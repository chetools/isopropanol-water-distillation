"""Streamlit presentation for preliminary equipment sizing and economics."""

import pandas as pd
import streamlit as st

from src.sizing import SizingBasis, calculate_sizing


def _money(value: float) -> str:
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value / 1_000:.0f}k"


def render_sizing_dashboard(column: dict) -> None:
    st.subheader("🏗 Automated preliminary sizing & economics")
    st.caption(
        "Calculated from the current maximum internal vapor load, actual tray count, and condenser/reboiler duties. "
        "Class-4 screening estimate only (typically ±30–50%); vendor hydraulics and code design govern."
    )

    with st.expander("Sizing basis and cost assumptions — inspect or change every input", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            flood = st.slider("Design / flood velocity", 0.50, 0.90, 0.80, 0.05)
            cap = st.number_input("Capacity factor C (m/s)", 0.04, 0.20, 0.107, 0.005)
            downcomer = st.slider("Downcomer area fraction", 0.08, 0.30, 0.15, 0.01)
            spacing = st.number_input("Tray spacing (m)", 0.35, 0.90, 0.55, 0.05)
        with c2:
            p_design = st.number_input("Design pressure (bar abs)", 1.2, 15.0, 3.0, 0.2)
            material = st.selectbox("Material factor", ["Carbon steel · 1.00", "304 SS · 1.70", "316 SS · 2.00"])
            project_index = st.number_input("Project cost index", 400.0, 1500.0, 820.0, 10.0)
            base_index = st.number_input("Correlation base index", 400.0, 1500.0, 800.0, 10.0)
        with c3:
            uc = st.number_input("Condenser U (kW/m²/K)", 0.10, 2.0, 0.85, 0.05)
            dtc = st.number_input("Condenser LMTD (K)", 3.0, 50.0, 15.0, 1.0)
            ur = st.number_input("Reboiler U (kW/m²/K)", 0.10, 2.0, 0.75, 0.05)
            dtr = st.number_input("Reboiler LMTD (K)", 3.0, 80.0, 20.0, 1.0)
        with c4:
            hours = st.number_input("Operating hours/year", 1000.0, 8760.0, 8000.0, 250.0)
            steam = st.number_input("Steam price ($/GJ)", 0.0, 100.0, 12.0, 0.5)
            cooling = st.number_input("Cooling price ($/GJ)", 0.0, 20.0, 0.60, 0.10)
            discount = st.slider("Discount rate", 0.0, 0.30, 0.10, 0.01)

    material_factor = {"Carbon steel · 1.00": 1.0, "304 SS · 1.70": 1.7, "316 SS · 2.00": 2.0}[material]
    basis = SizingBasis(
        flood_fraction=flood, capacity_factor_m_s=cap, downcomer_fraction=downcomer,
        tray_spacing_m=spacing, design_pressure_bar_abs=p_design, material_factor=material_factor,
        project_cost_index=project_index, base_cost_index=base_index,
        condenser_u_kw_m2_k=uc, condenser_lmtd_k=dtc,
        reboiler_u_kw_m2_k=ur, reboiler_lmtd_k=dtr,
        operating_hours_y=hours, steam_usd_gj=steam, cooling_usd_gj=cooling,
        discount_rate=discount,
    )
    result = calculate_sizing(column, basis)

    dims = st.columns(6)
    labels = [
        ("Diameter", f"{result['diameter_m']:.2f} m", f"stage {result['governing_stage']} governs"),
        ("Tangent height", f"{result['tangent_height_m']:.1f} m", f"{column['tray_count']} trays"),
        ("Shell thickness", f"{result['shell_thickness_mm']:.1f} mm", "preliminary pressure shell"),
        ("Condenser area", f"{result['condenser_area_m2']:.0f} m²", "Q/(U·LMTD)"),
        ("Reboiler area", f"{result['reboiler_area_m2']:.0f} m²", "Q/(U·LMTD)"),
        ("Fixed capital", _money(result["fixed_capital_usd"]), "screening estimate"),
    ]
    for slot, (label, value, help_text) in zip(dims, labels):
        slot.metric(label, value, help=help_text)

    cost_cols = st.columns(4)
    cost_cols[0].metric("Annual steam", _money(result["steam_cost_usd_y"]) + "/y")
    cost_cols[1].metric("Annual cooling", _money(result["cooling_cost_usd_y"]) + "/y")
    cost_cols[2].metric("Annual OPEX", _money(result["annual_opex_usd_y"]) + "/y")
    cost_cols[3].metric("Total annualized cost", _money(result["tac_usd_y"]) + "/y")

    with st.expander("Calculation audit trail — values used by the sizing equations", expanded=False):
        audit = pd.DataFrame(
            [
                ("Maximum vapor molar flow", result["vapor_mol_s"], "mol/s"),
                ("Maximum vapor volume", result["vapor_volume_m3_s"], "m³/s"),
                ("Vapor density", result["rho_v_kg_m3"], "kg/m³"),
                ("Liquid density", result["rho_l_kg_m3"], "kg/m³"),
                ("Flood velocity", result["u_flood_m_s"], "m/s"),
                ("Design velocity", result["u_design_m_s"], "m/s"),
                ("Active area", result["active_area_m2"], "m²"),
                ("Total cross-sectional area", result["total_area_m2"], "m²"),
                ("Estimated shell mass", result["shell_mass_kg"], "kg"),
                ("Capital recovery factor", result["crf"], "1/y"),
            ], columns=["Quantity", "Value", "Unit"]
        )
        st.dataframe(audit, hide_index=True, width="stretch")
        st.download_button(
            "Download sizing/cost audit CSV",
            audit.to_csv(index=False).encode("utf-8"),
            "column_sizing_cost_audit.csv",
            "text/csv",
        )
