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

# Sidebar Controls
with st.sidebar:
    st.title("⚗ Column Configuration")
    
    mode = st.radio("Operating Mode", ["Design Mode (Ponchon-Savarit)", "Rating Mode (Fixed Stages)"])
    
    st.subheader("Feed Specifications")
    F = st.number_input("Feed Flow Rate F (mol/s)", min_value=1.0, max_value=10000.0, value=100.0, step=10.0)
    z_F = st.slider("Feed IPA Mole Fraction (z_F)", 0.02, 0.65, 0.20, 0.01)
    P_kPa = st.number_input("Column Pressure (kPa)", min_value=20.0, max_value=500.0, value=101.325, step=5.0)
    P = P_kPa * 1000.0
    
    q_option = st.selectbox("Thermal Condition of Feed", ["Saturated Liquid (q = 1.0)", "Subcooled Liquid (q > 1.0)", "Saturated Vapor (q = 0.0)", "Superheated Vapor (q < 0.0)", "Two-Phase Mixture (0 < q < 1)"])
    
    if "Saturated Liquid" in q_option:
        feed_state = th.calculate_feed_state(z_F, P, q=1.0)
    elif "Saturated Vapor" in q_option:
        feed_state = th.calculate_feed_state(z_F, P, q=0.0)
    elif "Subcooled" in q_option:
        q_sub = st.slider("Feed q-value", 1.05, 1.50, 1.15, 0.05)
        feed_state = th.calculate_feed_state(z_F, P, q=q_sub)
    elif "Superheated" in q_option:
        q_sup = st.slider("Feed q-value", -0.50, -0.05, -0.15, 0.05)
        feed_state = th.calculate_feed_state(z_F, P, q=q_sup)
    else:
        q_two = st.slider("Feed q-value", 0.10, 0.90, 0.50, 0.05)
        feed_state = th.calculate_feed_state(z_F, P, q=q_two)
    
    st.subheader("Hardware & Efficiency")
    allow_subcool = st.checkbox("Subcooled Reflux", value=False)
    subcooling_dT = 0.0
    if allow_subcool:
        subcooling_dT = st.slider("Subcooling ΔT (°C)", 1.0, 30.0, 10.0, 1.0)
    
    murphree_eff = st.slider("Murphree Tray Efficiency (E_MV)", 0.20, 1.00, 1.00, 0.05)

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
            if is_locked:
                if spec == 'x_D':
                    new_v = st.slider("x_D value", float(z_F + 0.01), float(x_azeo - 0.005), float(np.clip(curr_val, z_F + 0.01, x_azeo - 0.005)), 0.005, label_visibility="collapsed")
                elif spec == 'x_B':
                    new_v = st.slider("x_B value", 0.001, float(z_F - 0.005), float(np.clip(curr_val, 0.001, z_F - 0.005)), 0.005, label_visibility="collapsed")
                elif spec == 'R':
                    new_v = st.slider("R value", 0.5, 15.0, float(max(0.5, curr_val)), 0.1, label_visibility="collapsed")
                elif spec in ['Rec_LK', 'Rec_HK']:
                    new_v = st.slider(f"{spec} value", 0.10, 0.999, float(np.clip(curr_val, 0.10, 0.999)), 0.005, label_visibility="collapsed")
                else:
                    new_v = st.number_input(f"{spec} value", value=curr_val, step=1.0, label_visibility="collapsed")
                dof.values[spec] = new_v
            else:
                if spec in ['x_D', 'x_B', 'Rec_LK', 'Rec_HK']:
                    st.markdown(f"<h3 style='color: #38bdf8; margin: 0;'>{curr_val:.4f}</h3>", unsafe_allow_html=True)
                elif spec == 'R':
                    st.markdown(f"<h3 style='color: #38bdf8; margin: 0;'>{curr_val:.2f}</h3>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<h3 style='color: #38bdf8; margin: 0;'>{curr_val:.1f}</h3>", unsafe_allow_html=True)
    
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
        N_spec = st.sidebar.number_input("Total Stages (N)", 3, 50, 10)
        N_feed_spec = st.sidebar.number_input("Feed Stage (N_F)", 1, N_spec, 5)
        col_result = col.solve_rating_column(
            F, z_F, P, feed_state, N_spec, N_feed_spec, R, D, subcooling_dT, murphree_eff
        )

# KPI Metric Cards
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
with kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Stages (N)</div>
        <div class="metric-value">{col_result['total_stages']}</div>
        <div class="metric-sub">{col_result['tray_count']} trays + reboiler</div>
    </div>
    """, unsafe_allow_html=True)
with kpi2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Optimal Feed Stage</div>
        <div class="metric-value">{col_result['feed_stage']}</div>
        <div class="metric-sub">Stage from top</div>
    </div>
    """, unsafe_allow_html=True)
with kpi3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Min Reflux (R_min)</div>
        <div class="metric-value">{col_result['R_min']:.2f}</div>
        <div class="metric-sub">R / R_min = {R / max(0.01, col_result['R_min']):.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with kpi4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Min Stages (N_min)</div>
        <div class="metric-value">{col_result['N_min']}</div>
        <div class="metric-sub">Total reflux limit</div>
    </div>
    """, unsafe_allow_html=True)
with kpi5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Condenser Duty (Q_C)</div>
        <div class="metric-value">{col_result['Q_C']:.0f} <span style="font-size:14px;">kW</span></div>
        <div class="metric-sub">Total condenser</div>
    </div>
    """, unsafe_allow_html=True)
with kpi6:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Reboiler Duty (Q_R)</div>
        <div class="metric-value">{col_result['Q_R']:.0f} <span style="font-size:14px;">kW</span></div>
        <div class="metric-sub">Partial reboiler</div>
    </div>
    """, unsafe_allow_html=True)

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
    fig_xy = plt.plot_xy(vle_data, col_result, z_F)
    st.plotly_chart(fig_xy, width="content", config=PLOTLY_CONFIG)

with grid_row1_col2:
    st.markdown(f"<div style='text-align:center; font-size:18px; font-weight:700; color:#f8fafc; margin-bottom:4px;'>Constant P VLE (T-x-y) at {P/1e3:.1f} kPa</div>", unsafe_allow_html=True)
    fig_txy = plt.plot_txy(vle_data, col_result, z_F, P)
    st.plotly_chart(fig_txy, width="content", config=PLOTLY_CONFIG)

grid_row2_col1, grid_row2_col2 = st.columns(2)
with grid_row2_col1:
    st.markdown("<div style='text-align:center; font-size:18px; font-weight:700; color:#f8fafc; margin-bottom:4px;'>Ponchon-Savarit Diagram (H-x-y)</div>", unsafe_allow_html=True)
    fig_ps = plt.plot_ponchon_savarit(vle_data, col_result, z_F, feed_state['h_F'])
    st.plotly_chart(fig_ps, width="content", config=PLOTLY_CONFIG)

with grid_row2_col2:
    st.markdown("<div style='text-align:center; font-size:18px; font-weight:700; color:#f8fafc; margin-bottom:4px;'>Internal Vapor & Liquid Flows (Non-CMO)</div>", unsafe_allow_html=True)
    fig_flow = plt.plot_flow_profiles(col_result)
    st.plotly_chart(fig_flow, width="content", config=PLOTLY_CONFIG)

st.markdown("---")

with st.expander("📋 Stage-by-Stage Data Table & CSV Download", expanded=False):
    df_stages = pd.DataFrame(col_result['stages'])
    df_stages.rename(columns={
        'stage': 'Stage',
        'section': 'Section',
        'x': 'x_IPA',
        'y': 'y_IPA',
        'T_C': 'T (°C)',
        'h_L': 'h_L (kJ/mol)',
        'H_V': 'H_V (kJ/mol)',
        'L': 'L_n (mol/s)',
        'V': 'V_n (mol/s)'
    }, inplace=True)
    st.dataframe(df_stages.style.format({
        'x_IPA': '{:.4f}',
        'y_IPA': '{:.4f}',
        'T (°C)': '{:.2f}',
        'h_L (kJ/mol)': '{:.2f}',
        'H_V (kJ/mol)': '{:.2f}',
        'L_n (mol/s)': '{:.2f}',
        'V_n (mol/s)': '{:.2f}'
    }), width="stretch")
    
    csv = df_stages.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Stage Profiles (CSV)", csv, "distillation_stages.csv", "text/csv")

# Thermodynamic Documentation
with st.expander("📚 Thermodynamic Model & CHECHEM Equations", expanded=False):
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
render_tutorial()
