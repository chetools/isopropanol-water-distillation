"""Isopropanol / Water Rigorous Distillation Webapp
Ponchon-Savarit, McCabe-Thiele, T-x-y, and Internal Flow Profiles.
Unified Single-Panel Dashboard with Dark Theme & Large Fonts.
"""

import streamlit as st
import pandas as pd
import numpy as np

import importlib
import src.thermo as th
import src.column as col
import src.plotting as plt
import src.dof_manager as dof_mod
from src.tutorial import render_tutorial
from src.sizing_dashboard import render_sizing_dashboard
from src.process_audit import render_process_calculation_audit
from src.units import display_step, from_canonical, to_canonical, unit_options

importlib.reload(th)
importlib.reload(col)
importlib.reload(plt)
importlib.reload(dof_mod)
from src.dof_manager import DOFManager, SPEC_LABELS, ALL_SPECS

st.set_page_config(
    page_title="IPA/Water Distillation",
    page_icon="⚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Dark Theme Overrides */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        font-weight: 600;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color="#38bdf8";
        color: #38bdf8;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 12px;
        color: #64748b;
        margin-top: 2px;
    }
    .locked-badge {
        display: inline-block;
        background-color: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid #10b981;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
    }
    .unlocked-badge {
        display: inline-block;
        background-color: rgba(148, 163, 184, 0.15);
        color: #cbd5e1;
        border: 1px solid #475569;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
    }
    /* Center Plotly 1:1 charts in grid columns */
    .stPlotlyChart {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-left: auto;
        margin-right: auto;
    }
    .stPlotlyChart > div {
        margin-left: auto;
        margin-right: auto;
    }

    /* Constrain main block width on wide screens to accommodate side legends while preserving 1:1 plot proportions */
    .main .block-container,
    [data-testid="stMainBlockContainer"],
    .stMainBlockContainer {
        max-width: 1520px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-left: clamp(1.25rem, 3vw, 2.5rem) !important;
        padding-right: clamp(1.25rem, 3vw, 2.5rem) !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3.5rem !important;
    }

    @media (min-width: 1800px) {
        .main .block-container,
        [data-testid="stMainBlockContainer"],
        .stMainBlockContainer {
            max-width: 1580px !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
        }
    }

    @media (min-width: 2400px) {
        .main .block-container,
        [data-testid="stMainBlockContainer"],
        .stMainBlockContainer {
            max-width: 1640px !important;
            padding-left: 4rem !important;
            padding-right: 4rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)


def _unit_select(label, quantity, key, container=st):
    """A consistent engineering-unit selector for every numerical UI quantity."""
    options = unit_options(quantity)
    return container.selectbox(label, options, key=key)


def _display(value, quantity, unit, digits=4):
    converted = from_canonical(value, quantity, unit)
    return f"{converted:.{digits}g} {unit}"

# Sidebar Controls
with st.sidebar:
    st.title("⚗ Column Configuration")
    
    mode = st.radio("Operating Mode", ["Design Mode (Ponchon-Savarit)", "Rating Mode (Fixed Stages)"])
    
    st.subheader("Feed Specifications")
    F_unit = _unit_select("Feed-flow unit", "flow", "feed_flow_unit", st)
    F_display = st.number_input(
        f"Feed Flow Rate F [{F_unit}]",
        min_value=from_canonical(1.0, "flow", F_unit),
        max_value=from_canonical(10000.0, "flow", F_unit),
        value=from_canonical(100.0, "flow", F_unit),
        step=from_canonical(10.0, "flow", F_unit), key=f"feed_flow_{F_unit}",
    )
    F = to_canonical(F_display, "flow", F_unit)
    z_unit = _unit_select("Feed-composition unit", "composition", "feed_composition_unit", st)
    z_display = st.slider(
        f"Feed IPA Composition z_F [{z_unit}]",
        from_canonical(0.02, "composition", z_unit), from_canonical(0.65, "composition", z_unit),
        from_canonical(0.20, "composition", z_unit), display_step(0.01, "composition", z_unit, 0.20),
    )
    z_F = to_canonical(z_display, "composition", z_unit)
    P_unit = _unit_select("Column-pressure unit", "pressure", "column_pressure_unit", st)
    P_display = st.number_input(
        f"Column Pressure [{P_unit}]",
        min_value=from_canonical(20000.0, "pressure", P_unit),
        max_value=from_canonical(500000.0, "pressure", P_unit),
        value=from_canonical(101325.0, "pressure", P_unit),
        step=from_canonical(5000.0, "pressure", P_unit), key=f"column_pressure_{P_unit}",
    )
    P = to_canonical(P_display, "pressure", P_unit)
    
    q_option = st.selectbox("Thermal Condition of Feed", ["Saturated Liquid (q = 1.0)", "Subcooled Liquid (q > 1.0)", "Saturated Vapor (q = 0.0)", "Superheated Vapor (q < 0.0)", "Two-Phase Mixture (0 < q < 1)"])
    
    if "Saturated Liquid" in q_option:
        feed_state = th.calculate_feed_state(z_F, P, q=1.0)
    elif "Saturated Vapor" in q_option:
        feed_state = th.calculate_feed_state(z_F, P, q=0.0)
    elif "Subcooled" in q_option:
        _unit_select("Feed q-value unit", "dimensionless", "q_sub_unit", st)
        q_sub = st.slider("Feed q-value", 1.05, 1.50, 1.15, 0.05)
        feed_state = th.calculate_feed_state(z_F, P, q=q_sub)
    elif "Superheated" in q_option:
        _unit_select("Feed q-value unit", "dimensionless", "q_sup_unit", st)
        q_sup = st.slider("Feed q-value", -0.50, -0.05, -0.15, 0.05)
        feed_state = th.calculate_feed_state(z_F, P, q=q_sup)
    else:
        _unit_select("Feed q-value unit", "dimensionless", "q_two_unit", st)
        q_two = st.slider("Feed q-value", 0.10, 0.90, 0.50, 0.05)
        feed_state = th.calculate_feed_state(z_F, P, q=q_two)
    
    st.subheader("Hardware & Efficiency")
    allow_subcool = st.checkbox("Subcooled Reflux", value=False)
    subcooling_dT = 0.0
    if allow_subcool:
        subcool_unit = _unit_select("Subcooling-temperature unit", "delta_temperature", "subcool_unit", st)
        subcool_display = st.slider(
            f"Subcooling ΔT [{subcool_unit}]",
            from_canonical(1.0, "delta_temperature", subcool_unit),
            from_canonical(30.0, "delta_temperature", subcool_unit),
            from_canonical(10.0, "delta_temperature", subcool_unit),
            from_canonical(1.0, "delta_temperature", subcool_unit),
        )
        subcooling_dT = to_canonical(subcool_display, "delta_temperature", subcool_unit)
    
    eff_unit = _unit_select("Tray-efficiency unit", "fraction", "murphree_unit", st)
    eff_display = st.slider(
        f"Murphree Tray Efficiency E_MV [{eff_unit}]",
        from_canonical(0.20, "fraction", eff_unit), from_canonical(1.0, "fraction", eff_unit),
        from_canonical(1.0, "fraction", eff_unit), from_canonical(0.05, "fraction", eff_unit),
    )
    murphree_eff = to_canonical(eff_display, "fraction", eff_unit)

# Initialize DOF Manager in session state
if 'dof' not in st.session_state or st.session_state.dof.F != F or st.session_state.dof.z_F != z_F or st.session_state.dof.P != P:
    st.session_state.dof = DOFManager(F=F, z_F=z_F, P=P)
    st.session_state.dof.recompute(feed_state, subcooling_dT)

dof = st.session_state.dof

# Header
st.title("⚗ Isopropanol / Water Rigorous Distillation Simulator")
st.caption("Ponchon-Savarit (H-x-y), McCabe-Thiele (x-y), VLE (T-x-y), and Non-CMO Internal Flow Profiles — All Physical Properties from chetools")

# DOF Budget Locker Section
with st.expander("🔐 Degree-of-Freedom Budget Locker (Exactly 2 Specifications Locked)", expanded=True):
    st.markdown("""
    Select **exactly two** column specifications to lock 🔒. The remaining variables are rigorously computed via mass and enthalpy balances, guaranteeing that the column is never over- or under-specified.
    """)
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        spec1 = st.selectbox("Locked Specification #1", options=ALL_SPECS, format_func=lambda s: SPEC_LABELS[s], index=ALL_SPECS.index(dof.locked_specs[0]))
    with col_sel2:
        available_spec2 = [s for s in ALL_SPECS if s != spec1 and not ({spec1, s} == {'D', 'B'})]
        default_idx = available_spec2.index(dof.locked_specs[1]) if dof.locked_specs[1] in available_spec2 else 0
        spec2 = st.selectbox("Locked Specification #2", options=available_spec2, format_func=lambda s: SPEC_LABELS[s], index=default_idx)
    
    dof.set_locked_pair(spec1, spec2)
    
    # Display 9 variables in a 3x3 grid
    row1_cols = st.columns(3)
    row2_cols = st.columns(3)
    row3_cols = st.columns(3)
    all_cols = row1_cols + row2_cols + row3_cols
    
    x_azeo, _ = th.find_azeotrope(P)
    
    for idx, spec in enumerate(ALL_SPECS):
        with all_cols[idx]:
            is_locked = spec in dof.locked_specs
            badge = '<span class="locked-badge">&#128272; LOCKED SPEC</span>' if is_locked else '<span class="unlocked-badge">&#128273; COMPUTED</span>'
            st.markdown(f"<b>{SPEC_LABELS[spec]}</b> {badge}", unsafe_allow_html=True)
            
            curr_val = float(dof.values[spec])
            quantity = {
                'x_D': 'composition', 'x_B': 'composition', 'D': 'flow', 'B': 'flow',
                'R': 'ratio', 'Q_C': 'duty', 'Q_R': 'duty',
                'Rec_LK': 'fraction', 'Rec_HK': 'fraction',
            }[spec]
            unit = _unit_select(f"{spec} display unit", quantity, f"dof_unit_{spec}", st)
            curr_display = from_canonical(curr_val, quantity, unit)
            if is_locked:
                if spec == 'x_D':
                    new_display = st.slider("x_D value", from_canonical(float(z_F + 0.01), quantity, unit), from_canonical(float(x_azeo - 0.005), quantity, unit), from_canonical(float(np.clip(curr_val, z_F + 0.01, x_azeo - 0.005)), quantity, unit), display_step(0.005, quantity, unit, curr_val), label_visibility="collapsed")
                elif spec == 'x_B':
                    new_display = st.slider("x_B value", from_canonical(0.001, quantity, unit), from_canonical(float(z_F - 0.005), quantity, unit), from_canonical(float(np.clip(curr_val, 0.001, z_F - 0.005)), quantity, unit), display_step(0.005, quantity, unit, curr_val), label_visibility="collapsed")
                elif spec == 'R':
                    new_display = st.slider("R value", 0.5, 15.0, float(max(0.5, curr_display)), 0.1, label_visibility="collapsed")
                elif spec in ['Rec_LK', 'Rec_HK']:
                    new_display = st.slider(f"{spec} value", from_canonical(0.10, quantity, unit), from_canonical(0.999, quantity, unit), from_canonical(float(np.clip(curr_val, 0.10, 0.999)), quantity, unit), from_canonical(0.005, quantity, unit), label_visibility="collapsed")
                else:
                    new_display = st.number_input(f"{spec} value [{unit}]", value=curr_display, step=from_canonical(1.0, quantity, unit), label_visibility="collapsed", key=f"dof_input_{spec}_{unit}")
                dof.values[spec] = to_canonical(new_display, quantity, unit)
            else:
                digits = 5 if spec in ['x_D', 'x_B', 'Rec_LK', 'Rec_HK'] else 4
                st.markdown(f"<h3 style='color: #38bdf8; margin: 0;'>{curr_display:.{digits}g} <span style='font-size:13px'>{unit}</span></h3>", unsafe_allow_html=True)
    
    dof.recompute(feed_state, subcooling_dT)
    if dof.warning_msg:
        st.warning(dof.warning_msg)

x_D = dof.values['x_D']
x_B = dof.values['x_B']
R = dof.values['R']
D = dof.values['D']

# Solve Distillation Column
with st.spinner("Solving Ponchon-Savarit stages and MESH energy balances..."):
    vle_data = th.get_vle_curves(P, n_points=120)
    if "Design" in mode:
        col_result = col.solve_design_column(
            F, z_F, P, x_D, x_B, R, feed_state, subcooling_dT, murphree_eff
        )
    else:
        _unit_select("Total-stage count unit", "count_stage", "rating_stage_unit", st.sidebar)
        N_spec = st.sidebar.number_input("Total Stages N [equilibrium stages]", 3, 50, 10)
        _unit_select("Feed-stage count unit", "count_stage", "rating_feed_stage_unit", st.sidebar)
        N_feed_spec = st.sidebar.number_input("Feed Stage N_F [stage from top]", 1, N_spec, 5)
        col_result = col.solve_rating_column(
            F, z_F, P, feed_state, N_spec, N_feed_spec, R, D, subcooling_dT, murphree_eff
        )

# KPI Metric Cards
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
with kpi1:
    n_unit = _unit_select("Total-stage unit", "count_stage", "kpi_total_stage_unit", st)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Stages (N)</div>
        <div class="metric-value">{col_result['total_stages']} <span style="font-size:13px">{n_unit}</span></div>
        <div class="metric-sub">{col_result['tray_count']} trays + partial reboiler</div>
    </div>
    """, unsafe_allow_html=True)
with kpi2:
    nf_unit = _unit_select("Feed-stage unit", "count_stage", "kpi_feed_stage_unit", st)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Optimal Feed Stage</div>
        <div class="metric-value">{col_result['feed_stage']}</div>
        <div class="metric-sub">{nf_unit}; counted from top</div>
    </div>
    """, unsafe_allow_html=True)
with kpi3:
    rmin_unit = _unit_select("Minimum-reflux unit", "ratio", "kpi_rmin_unit", st)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Min Reflux (R_min)</div>
        <div class="metric-value">{col_result['R_min']:.3g} <span style="font-size:13px">{rmin_unit}</span></div>
        <div class="metric-sub">R/R_min = {R / max(0.01, col_result['R_min']):.3g} dimensionless</div>
    </div>
    """, unsafe_allow_html=True)
with kpi4:
    nmin_unit = _unit_select("Minimum-stage unit", "count_stage", "kpi_nmin_unit", st)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Min Stages (N_min)</div>
        <div class="metric-value">{col_result['N_min']} <span style="font-size:13px">{nmin_unit}</span></div>
        <div class="metric-sub">Total reflux limit</div>
    </div>
    """, unsafe_allow_html=True)
with kpi5:
    qc_unit = _unit_select("Condenser-duty unit", "duty", "kpi_qc_unit", st)
    qc_display = from_canonical(col_result['Q_C'], "duty", qc_unit)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Condenser Duty (Q_C)</div>
        <div class="metric-value">{qc_display:.4g} <span style="font-size:14px;">{qc_unit}</span></div>
        <div class="metric-sub">Total condenser</div>
    </div>
    """, unsafe_allow_html=True)
with kpi6:
    qr_unit = _unit_select("Reboiler-duty unit", "duty", "kpi_qr_unit", st)
    qr_display = from_canonical(col_result['Q_R'], "duty", qr_unit)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Reboiler Duty (Q_R)</div>
        <div class="metric-value">{qr_display:.4g} <span style="font-size:14px;">{qr_unit}</span></div>
        <div class="metric-sub">Partial reboiler</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

render_process_calculation_audit(col_result)

st.markdown("---")

render_sizing_dashboard(col_result)

st.markdown("---")

# Unified Single-Panel Grid (2x2 Layout)
st.subheader("📊 Distillation Visualization Dashboard")

PLOTLY_CONFIG = {
    'scrollZoom': True,
    'displayModeBar': True,
    'displaylogo': False
}

grid_row1_col1, grid_row1_col2 = st.columns(2)
with grid_row1_col1:
    st.markdown("<div style='text-align:center; font-size:18px; font-weight:700; color:#f8fafc; margin-bottom:4px;'>McCabe-Thiele Diagram (x-y)</div>", unsafe_allow_html=True)
    xy_comp_unit = _unit_select("McCabe composition axes", "composition", "plot_xy_comp_unit", st)
    fig_xy = plt.plot_xy(vle_data, col_result, z_F, xy_comp_unit)
    st.plotly_chart(fig_xy, width="content", config=PLOTLY_CONFIG)

with grid_row1_col2:
    p_heading = from_canonical(P, "pressure", P_unit)
    st.markdown(f"<div style='text-align:center; font-size:18px; font-weight:700; color:#f8fafc; margin-bottom:4px;'>Constant P VLE (T-x-y) at {p_heading:.4g} {P_unit}</div>", unsafe_allow_html=True)
    txy_units = st.columns(2)
    txy_comp_unit = _unit_select("VLE composition axis", "composition", "plot_txy_comp_unit", txy_units[0])
    txy_temp_unit = _unit_select("VLE temperature axis", "temperature", "plot_txy_temp_unit", txy_units[1])
    fig_txy = plt.plot_txy(vle_data, col_result, z_F, P, txy_comp_unit, txy_temp_unit)
    st.plotly_chart(fig_txy, width="content", config=PLOTLY_CONFIG)

grid_row2_col1, grid_row2_col2 = st.columns(2)
with grid_row2_col1:
    st.markdown("<div style='text-align:center; font-size:18px; font-weight:700; color:#f8fafc; margin-bottom:4px;'>Ponchon-Savarit Diagram (H-x-y)</div>", unsafe_allow_html=True)
    ps_units = st.columns(2)
    ps_comp_unit = _unit_select("Ponchon composition axis", "composition", "plot_ps_comp_unit", ps_units[0])
    ps_h_unit = _unit_select("Ponchon enthalpy axis", "enthalpy", "plot_ps_h_unit", ps_units[1])
    fig_ps = plt.plot_ponchon_savarit(vle_data, col_result, z_F, feed_state['h_F'], ps_comp_unit, ps_h_unit)
    st.plotly_chart(fig_ps, width="content", config=PLOTLY_CONFIG)

with grid_row2_col2:
    st.markdown("<div style='text-align:center; font-size:18px; font-weight:700; color:#f8fafc; margin-bottom:4px;'>Internal Vapor & Liquid Flows (Non-CMO)</div>", unsafe_allow_html=True)
    flow_units = st.columns(2)
    _unit_select("Stage-number axis", "count_stage", "plot_stage_unit", flow_units[0])
    plot_flow_unit = _unit_select("Internal-flow axis", "flow", "plot_flow_unit", flow_units[1])
    fig_flow = plt.plot_flow_profiles(col_result, plot_flow_unit)
    st.plotly_chart(fig_flow, width="content", config=PLOTLY_CONFIG)

st.markdown("---")

with st.expander("📋 Stage-by-Stage Data Table & CSV Download", expanded=False):
    df_stages = pd.DataFrame(col_result['stages'])
    unit_cols = st.columns(4)
    stage_comp_unit = _unit_select("Composition columns", "composition", "stage_table_comp_unit", unit_cols[0])
    stage_temp_unit = _unit_select("Temperature column", "temperature", "stage_table_temp_unit", unit_cols[1])
    stage_h_unit = _unit_select("Enthalpy columns", "enthalpy", "stage_table_h_unit", unit_cols[2])
    stage_flow_unit = _unit_select("Internal-flow columns", "flow", "stage_table_flow_unit", unit_cols[3])
    for name in ("x", "y"):
        df_stages[name] = df_stages[name].map(lambda v: from_canonical(v, "composition", stage_comp_unit))
    df_stages["T_C"] = df_stages["T_C"].map(lambda v: from_canonical(v, "temperature", stage_temp_unit))
    for name in ("h_L", "H_V"):
        df_stages[name] = df_stages[name].map(lambda v: from_canonical(v, "enthalpy", stage_h_unit))
    for name in ("L", "V"):
        df_stages[name] = df_stages[name].map(lambda v: from_canonical(v, "flow", stage_flow_unit))
    df_stages.rename(columns={
        'stage': 'Stage',
        'section': 'Section',
        'x': f'x_IPA ({stage_comp_unit})',
        'y': f'y_IPA ({stage_comp_unit})',
        'T_C': f'T ({stage_temp_unit})',
        'h_L': f'h_L ({stage_h_unit})',
        'H_V': f'H_V ({stage_h_unit})',
        'L': f'L_n ({stage_flow_unit})',
        'V': f'V_n ({stage_flow_unit})'
    }, inplace=True)
    st.dataframe(df_stages, width="stretch", hide_index=True)
    
    csv = df_stages.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Stage Profiles (CSV)", csv, "distillation_stages.csv", "text/csv")

# Thermodynamic Documentation
with st.expander("Thermodynamic Model", expanded=False):
    st.markdown(r"""
    ### 1. Pure Component Properties (From `chetools/data`)
    - **Vapor Pressure** (Equation 101):
      $$ \ln P^{\text{vap}} = A + \frac{B}{T} + C \ln T + D \cdot T^E $$
    - **Heat of Vaporization** (Equation 106):
      $$ H_{\text{vap}} = A (1 - T_r)^{B + C T_r + D T_r^2 + E T_r^3} $$
    - **Liquid Heat Capacity** (Equation 100):
      $$ C_{p,L} = A + B T + C T^2 + D T^3 + E T^4 $$

    ### 2. Reference State & Enthalpies
    - **Reference state**: Pure saturated liquid at $25^\circ\text{C}$ ($298.15\,\mathrm{K}$), $h_i(298.15) = 0$.
    - **Saturated liquid enthalpy**:
      $$ h_L(x, T) = \sum x_i \int_{298.15}^T C_{p,L,i}(T) dT + H^E(x, T) $$
    - **Saturated vapor enthalpy**:
      $$ H_V(y, T) = \sum y_i \left( \int_{298.15}^T C_{p,L,i} dT + H_{\text{vap,i}}(T) \right) $$

    ### 3. NRTL Activity Coefficients & Excess Enthalpy
    - **NRTL parameters**: $B_{12} = 20.06\,\mathrm{K}$, $B_{21} = 832.98\,\mathrm{K}$, $\alpha = 0.326$.
    - **Excess Enthalpy**: Derived analytically via the Gibbs-Helmholtz equation:
      $$ H^E(x, T) = -R T^2 \sum x_i \frac{\partial \ln \gamma_i}{\partial T} $$
    """)

st.markdown("---")
render_tutorial(vle_data, col_result, z_F, feed_state['h_F'], P)
