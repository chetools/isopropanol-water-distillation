"""Streamlit presentation for preliminary equipment sizing and economics."""

import pandas as pd
import streamlit as st

from src.sizing import SizingBasis, build_sizing_reproduction_script, calculate_sizing
from src.units import from_canonical, to_canonical, unit_options


def _input(container, label, quantity, key, minimum, maximum, value, step, slider=False, preferred=None):
    options = unit_options(quantity)
    index = options.index(preferred) if preferred in options else 0
    unit = container.selectbox(f"{label} unit", options, index=index, key=f"{key}_unit")
    values = [from_canonical(v, quantity, unit) for v in (minimum, maximum, value, step)]
    if slider:
        shown = container.slider(f"{label} [{unit}]", *values, key=f"{key}_{unit}")
    else:
        shown = container.number_input(
            f"{label} [{unit}]", min_value=values[0], max_value=values[1],
            value=values[2], step=values[3], key=f"{key}_{unit}",
        )
    return to_canonical(shown, quantity, unit)


def _metric(container, label, value, quantity, key, help_text, digits=4, preferred=None):
    options = unit_options(quantity)
    index = options.index(preferred) if preferred in options else 0
    unit = container.selectbox(f"{label} unit", options, index=index, key=f"{key}_unit")
    shown = from_canonical(value, quantity, unit)
    container.metric(label, f"{shown:.{digits}g} {unit}", help=help_text)


def render_sizing_dashboard(column: dict) -> None:
    st.subheader("🏗 Automated preliminary sizing & economics")
    st.caption(
        "Calculated from the current maximum internal vapor load, actual tray count, and condenser/reboiler duties. "
        "Class-4 screening estimate only (typically ±30–50%); vendor hydraulics and code design govern."
    )

    with st.expander("Sizing basis and cost assumptions — inspect or change every input", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            flood = _input(st, "Design/flood velocity fraction", "fraction", "flood", 0.50, 0.90, 0.80, 0.05, True)
            cap = _input(st, "Capacity factor C", "velocity", "capacity", 0.04, 0.20, 0.107, 0.005)
            downcomer = _input(st, "Downcomer area fraction", "fraction", "downcomer", 0.08, 0.30, 0.15, 0.01, True)
            spacing = _input(st, "Tray spacing", "length", "spacing", 0.35, 0.90, 0.55, 0.05)
            top_space = _input(st, "Top disengagement", "length", "top_space", 0.5, 6.0, 2.5, 0.25)
            bottom_space = _input(st, "Bottom sump allowance", "length", "bottom_space", 0.5, 8.0, 3.0, 0.25)
        with c2:
            shell_allow = _input(st, "Other shell allowance", "length", "shell_allow", 0.0, 5.0, 1.0, 0.25)
            p_design_pa = _input(st, "Design pressure (absolute)", "pressure", "p_design", 120000.0, 1_500_000.0, 300000.0, 20000.0, preferred="bar(a)")
            stress_pa = _input(st, "Allowable stress", "stress", "stress", 20e6, 250e6, 115e6, 5e6)
            weld = _input(st, "Weld-joint efficiency", "fraction", "weld", 0.5, 1.0, 0.85, 0.01, True)
            corrosion_m = _input(st, "Corrosion allowance", "length", "corrosion", 0.0, 0.012, 0.003, 0.0005, preferred="mm")
            material = st.selectbox("Material factor", ["Carbon steel · 1.00", "304 SS · 1.70", "316 SS · 2.00"])
        with c3:
            uc = _input(st, "Condenser U", "heat_transfer_coefficient", "uc", 0.10, 2.0, 0.85, 0.05)
            dtc = _input(st, "Condenser LMTD", "delta_temperature", "dtc", 3.0, 50.0, 15.0, 1.0)
            ur = _input(st, "Reboiler U", "heat_transfer_coefficient", "ur", 0.10, 2.0, 0.75, 0.05)
            dtr = _input(st, "Reboiler LMTD", "delta_temperature", "dtr", 3.0, 80.0, 20.0, 1.0)
            project_index = _input(st, "Project cost index", "cost_index", "project_index", 400.0, 1500.0, 820.0, 10.0)
            base_index = _input(st, "Correlation base index", "cost_index", "base_index", 400.0, 1500.0, 800.0, 10.0)
        with c4:
            hours = _input(st, "Operating time", "hours_year", "hours", 1000.0, 8760.0, 8000.0, 250.0)
            steam = _input(st, "Steam price", "energy_price", "steam", 0.0, 100.0, 12.0, 0.5)
            cooling = _input(st, "Cooling price", "energy_price", "cooling", 0.0, 20.0, 0.60, 0.10)
            discount = _input(st, "Discount rate", "fraction", "discount", 0.0, 0.30, 0.10, 0.01, True)
            life = _input(st, "Project life", "years", "life", 1.0, 50.0, 15.0, 1.0)

    material_factor = {"Carbon steel · 1.00": 1.0, "304 SS · 1.70": 1.7, "316 SS · 2.00": 2.0}[material]
    basis = SizingBasis(
        flood_fraction=flood, capacity_factor_m_s=cap, downcomer_fraction=downcomer,
        tray_spacing_m=spacing, top_disengagement_m=top_space, bottom_sump_m=bottom_space,
        shell_allowance_m=shell_allow, design_pressure_bar_abs=p_design_pa / 1e5,
        allowable_stress_mpa=stress_pa / 1e6, weld_efficiency=weld,
        corrosion_allowance_mm=corrosion_m * 1000.0, material_factor=material_factor,
        project_cost_index=project_index, base_cost_index=base_index,
        condenser_u_kw_m2_k=uc, condenser_lmtd_k=dtc,
        reboiler_u_kw_m2_k=ur, reboiler_lmtd_k=dtr,
        operating_hours_y=hours, steam_usd_gj=steam, cooling_usd_gj=cooling,
        discount_rate=discount, project_life_y=int(round(life)),
    )
    result = calculate_sizing(column, basis)

    dims = st.columns(6)
    labels = [
        ("Diameter", result['diameter_m'], "length", "diameter", f"stage {result['governing_stage']} governs", "m"),
        ("Tangent height", result['tangent_height_m'], "length", "height", f"{column['tray_count']} trays", "m"),
        ("Shell thickness", result['shell_thickness_mm'] / 1000.0, "length", "thickness", "preliminary pressure shell", "mm"),
        ("Condenser area", result['condenser_area_m2'], "area", "condenser_area", "Q/(U·LMTD)", "m²"),
        ("Reboiler area", result['reboiler_area_m2'], "area", "reboiler_area", "Q/(U·LMTD)", "m²"),
        ("Fixed capital", result["fixed_capital_usd"], "money", "fixed_capital", "screening estimate", "MUSD"),
    ]
    for slot, (label, value, quantity, key, help_text, preferred) in zip(dims, labels):
        _metric(slot, label, value, quantity, key, help_text, preferred=preferred)

    cost_cols = st.columns(4)
    _metric(cost_cols[0], "Annual steam", result["steam_cost_usd_y"], "money_rate", "steam_cost", "reboiler duty × operating time × tariff")
    _metric(cost_cols[1], "Annual cooling", result["cooling_cost_usd_y"], "money_rate", "cooling_cost", "condenser duty × operating time × tariff")
    _metric(cost_cols[2], "Annual OPEX", result["annual_opex_usd_y"], "money_rate", "opex", "steam + cooling + maintenance")
    _metric(cost_cols[3], "Total annualized cost", result["tac_usd_y"], "money_rate", "tac", "annualized capital + OPEX")

    with st.expander("Complete calculation ledger and independent Python reproduction", expanded=False):
        st.markdown(
            "The ledger exposes **every intermediate value used to produce the displayed sizing and cost outputs**. "
            "The substitution column uses more digits than the KPI cards so independent calculations do not inherit display-rounding error."
        )
        audit = pd.DataFrame(result["calculation_steps"])
        ledger_tab, python_tab = st.tabs(["37-step numerical ledger", "Dependency-free Python"])
        with ledger_tab:
            displayed = audit.copy()
            displayed["Value"] = displayed["Value"].map(lambda value: f"{value:.10g}")
            st.dataframe(
                displayed,
                hide_index=True,
                width="stretch",
                column_config={
                    "Step": st.column_config.NumberColumn(width="small", format="%d"),
                    "Symbol": st.column_config.TextColumn(width="small"),
                    "Quantity": st.column_config.TextColumn(width="medium"),
                    "Formula": st.column_config.TextColumn(width="large"),
                    "Numerical substitution": st.column_config.TextColumn(width="large"),
                    "Value": st.column_config.TextColumn(width="medium"),
                    "Unit": st.column_config.TextColumn(width="small"),
                    "Basis / provenance": st.column_config.TextColumn(width="large"),
                },
            )
            st.download_button(
                "Download complete calculation ledger (CSV)",
                audit.to_csv(index=False).encode("utf-8"),
                "column_sizing_cost_complete_ledger.csv",
                "text/csv",
            )
        with python_tab:
            script = build_sizing_reproduction_script(column, basis)
            st.markdown(
                "This generated script embeds the current stage loads and every dashboard assumption, uses only "
                "Python's standard library, and prints the unrounded intermediate and final results."
            )
            st.download_button(
                "Download exact hand-coded Python reproduction",
                script.encode("utf-8"),
                "reproduce_column_sizing_and_cost.py",
                "text/x-python",
            )
            st.code(script, language="python", line_numbers=True)
