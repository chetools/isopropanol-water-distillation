"""User-facing audit trail for the thermodynamic and stage calculations."""

import pandas as pd
import streamlit as st

from src.source_links import github_symbol_link
from src.units import from_canonical, unit_options


def _row(step, symbol, quantity, formula, substitution, value, unit, explanation):
    return {
        "Step": step,
        "Symbol": symbol,
        "Quantity": quantity,
        "Formula / algorithm": formula,
        "Numerical substitution": substitution,
        "Value": value,
        "Unit": unit,
        "How obtained": explanation,
    }


def build_process_ledger(c: dict) -> pd.DataFrame:
    """Describe each headline process result without display rounding."""
    F, z, D, B = c["F"], c["z_F"], c["D"], c["B"]
    xD, xB, R = c["x_D"], c["x_B"], c["R"]
    qpd, qpb = c["Q_prime_D"], c["Q_prime_B"]
    rec_lk = D * xD / (F * z)
    rec_hk = B * (1 - xB) / (F * (1 - z))
    total_residual = F - D - B
    ipa_residual = F * z - D * xD - B * xB
    energy_residual = F * c["h_F"] + c["Q_R"] - D * c["h_D"] - B * c["h_B"] - c["Q_C"]
    rows = [
        _row(1, "D", "Distillate molar rate", "F(z_F-x_B)/(x_D-x_B)",
             f"{F:.12g}({z:.12g}-{xB:.12g})/({xD:.12g}-{xB:.12g})", D, "mol/s", "Overall and IPA balances solved simultaneously."),
        _row(2, "B", "Bottoms molar rate", "F-D", f"{F:.12g}-{D:.12g}", B, "mol/s", "Overall steady-state balance."),
        _row(3, "h_F", "Feed molar enthalpy", "q h_L,sat +(1-q)H_V,sat", f"property calculation at z_F={z:.12g}, P={c['P']:.12g} Pa", c["h_F"], "kJ/mol", "NRTL bubble state plus pure sensible, latent, and excess enthalpy terms."),
        _row(4, "h_D", "Distillate molar enthalpy", "h_L(x_D,T_bubble)", f"h_L({xD:.12g}, {c['T_D_C'] + 273.15:.12g} K)", c["h_D"], "kJ/mol", "Total-condenser saturated-liquid product state."),
        _row(5, "h_B", "Bottoms molar enthalpy", "h_L(x_B,T_bubble)", f"h_L({xB:.12g}, {c['T_B_C'] + 273.15:.12g} K)", c["h_B"], "kJ/mol", "Partial-reboiler liquid product state."),
        _row(6, "Q'_D", "Rectifying difference-point enthalpy", "h_D+Q_C/D",
             f"{c['h_D']:.12g}+{c['Q_C']:.12g}/{D:.12g}", qpd, "kJ/mol", "Invariant upper-section material/energy difference point."),
        _row(7, "Q_C", "Condenser duty magnitude", "D(Q'_D-h_D)",
             f"{D:.12g}({qpd:.12g}-{c['h_D']:.12g})", c["Q_C"], "kW", "Because (mol/s)(kJ/mol)=kJ/s=kW."),
        _row(8, "Q'_B", "Stripping difference-point enthalpy", "(Fh_F-DQ'_D)/B",
             f"({F:.12g}×{c['h_F']:.12g}-{D:.12g}×{qpd:.12g})/{B:.12g}", qpb, "kJ/mol", "Collinearity of feed and both difference points."),
        _row(9, "Q_R", "Reboiler duty", "B(h_B-Q'_B)",
             f"{B:.12g}({c['h_B']:.12g}-{qpb:.12g})", c["Q_R"], "kW", "Whole-column energy balance using the common enthalpy reference."),
        _row(10, "R_min", "Minimum reflux ratio", "max_x(Q'_intersection-H_V1)/(H_V1-h_reflux)",
             "150 composition trials; maximum feasible pinch intercept", c["R_min"], "mol/mol", "The exact loop and root brackets are shown in column.py below."),
        _row(11, "N_min", "Minimum equilibrium stages", "repeat x_next=dew_point(y_current) at total reflux", f"step x_D={xD:.12g} until x≤x_B={xB:.12g}", c["N_min"], "stages", "Integer count of equilibrium contacts at the total-reflux limit."),
        _row(12, "N", "Calculated equilibrium stages", "Ponchon–Savarit tie-line/ray stepping", f"iterate from x_D={xD:.12g} until x≤x_B={xB:.12g}", c["total_stages"], "stages", "Each loop performs a dew root, equilibrium correction, enthalpy ray root, and lever-rule flow calculation."),
        _row(13, "N_tray", "Physical trays represented", "max(N-1,0)", f"max({c['total_stages']}-1,0)", c["tray_count"], "trays", "Partial reboiler is an equilibrium stage; total condenser is not."),
        _row(14, "N_F", "Feed stage from top", "first stage switching from rectifying to stripping construction", f"first x_n≤z_F={z:.12g} with implemented near-feed guard", c["feed_stage"], "stage", "Exact switching condition appears in column.py."),
        _row(15, "Rec_LK", "IPA recovery in distillate", "Dx_D/(Fz_F)", f"{D:.12g}×{xD:.12g}/({F:.12g}×{z:.12g})", rec_lk, "fraction", "Light-key component recovery."),
        _row(16, "Rec_HK", "Water recovery in bottoms", "B(1-x_B)/[F(1-z_F)]", f"{B:.12g}(1-{xB:.12g})/[{F:.12g}(1-{z:.12g})]", rec_hk, "fraction", "Heavy-key component recovery."),
        _row(17, "r_total", "Overall balance residual", "F-D-B", f"{F:.12g}-{D:.12g}-{B:.12g}", total_residual, "mol/s", "Should be near floating-point zero."),
        _row(18, "r_IPA", "IPA balance residual", "Fz_F-Dx_D-Bx_B", f"{F:.12g}×{z:.12g}-{D:.12g}×{xD:.12g}-{B:.12g}×{xB:.12g}", ipa_residual, "mol/s", "Should be near floating-point zero."),
        _row(19, "r_H", "Whole-column energy residual", "Fh_F+Q_R-Dh_D-Bh_B-Q_C", "all displayed unrounded enthalpy and duty values", energy_residual, "kW", "Should be near floating-point zero."),
    ]
    return pd.DataFrame(rows)


def render_process_calculation_audit(column: dict) -> None:
    """Render equations, substitutions, stage states, and source links."""
    with st.expander("How every process KPI is calculated — equations, substitutions, and source links", expanded=False):
        st.caption(
            "KPI cards are rounded for readability. The ledger retains calculation precision, and the final tab links to the exact Python source lines."
        )
        ledger_tab, stage_tab, code_tab = st.tabs(
            ["19-step KPI ledger", "Every calculated stage state", "Python code links"]
        )
        with ledger_tab:
            ledger = build_process_ledger(column)
            shown = ledger.copy()
            shown["Value"] = shown["Value"].map(lambda v: f"{float(v):.12g}")
            st.dataframe(shown, hide_index=True, width="stretch")
            st.download_button(
                "Download process KPI ledger (CSV)", ledger.to_csv(index=False).encode("utf-8"),
                "distillation_process_kpi_ledger.csv", "text/csv",
            )
        with stage_tab:
            stages = pd.DataFrame(column["stages"])
            st.markdown(
                "Each row is generated by one equilibrium-stage iteration. Compositions and temperatures come from "
                "the NRTL equilibrium root; enthalpies from the common-reference property model; L and V from the "
                "Ponchon–Savarit lever rule. The complete algorithm is linked in the next tab."
            )
            selectors = st.columns(4)
            comp_unit = selectors[0].selectbox("Composition unit", unit_options("composition"), key="audit_stage_comp_unit")
            temp_unit = selectors[1].selectbox("Temperature unit", unit_options("temperature"), key="audit_stage_temp_unit")
            h_unit = selectors[2].selectbox("Enthalpy unit", unit_options("enthalpy"), key="audit_stage_h_unit")
            flow_unit = selectors[3].selectbox("Flow unit", unit_options("flow"), key="audit_stage_flow_unit")
            stages["x"] = stages["x"].map(lambda v: from_canonical(v, "composition", comp_unit))
            stages["y"] = stages["y"].map(lambda v: from_canonical(v, "composition", comp_unit))
            stages["T_C"] = stages["T_C"].map(lambda v: from_canonical(v, "temperature", temp_unit))
            stages["h_L"] = stages["h_L"].map(lambda v: from_canonical(v, "enthalpy", h_unit))
            stages["H_V"] = stages["H_V"].map(lambda v: from_canonical(v, "enthalpy", h_unit))
            stages["L"] = stages["L"].map(lambda v: from_canonical(v, "flow", flow_unit))
            stages["V"] = stages["V"].map(lambda v: from_canonical(v, "flow", flow_unit))
            stages = stages.rename(columns={
                "x": f"x_IPA [{comp_unit}]", "y": f"y_IPA [{comp_unit}]",
                "T_C": f"temperature [{temp_unit}]", "h_L": f"h_L [{h_unit}]",
                "H_V": f"H_V [{h_unit}]", "L": f"L [{flow_unit}]", "V": f"V [{flow_unit}]",
            })
            st.dataframe(stages, hide_index=True, width="stretch")
            st.download_button(
                "Download unrounded stage calculation table (CSV)", stages.to_csv(index=False).encode("utf-8"),
                "distillation_unrounded_stage_calculations.csv", "text/csv",
            )
        with code_tab:
            choices = {
                "Thermodynamics: NRTL activity coefficients": ("src/thermo.py", "nrtl_gamma"),
                "Thermodynamics: bubble-point equilibrium root": ("src/thermo.py", "bubble_point"),
                "Column: balances, stage stepping, and duties": ("src/column.py", "solve_design_column"),
                "Specification solver: every allowed DOF pair": ("src/dof_manager.py", "recompute"),
            }
            selected = st.selectbox("Calculation module", list(choices), key="process_source_module")
            relative, symbol = choices[selected]
            st.markdown(github_symbol_link(selected, relative, symbol))
