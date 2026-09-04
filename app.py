"""Isopropanol / water rigorous distillation simulator.

Ponchon-Savarit, McCabe-Thiele, T-x-y and non-CMO internal flow profiles,
with preliminary sizing, economics, a full calculation audit, and a
step-by-step engineering tutorial.

Layout: a persistent KPI strip above five tabs, so the headline results stay
visible while the reader moves between design, diagrams, sizing, audit and
the tutorial.
"""

import numpy as np
import pandas as pd
import streamlit as st

import src.column as col
import src.plotting as plots
import src.theme as theme
import src.thermo as th
import src.ui as ui
from src.dof_manager import ALL_SPECS, DOFManager, SPEC_LABELS
from src.process_audit import render_process_calculation_audit
from src.sizing_dashboard import render_sizing_dashboard
from src.tutorial import render_tutorial
from src.units import display_step, from_canonical, to_canonical

st.set_page_config(
    page_title="IPA/Water Distillation",
    page_icon="⚗",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(theme.app_css(), unsafe_allow_html=True)
ui.init_units()

PLOTLY_CONFIG = {"scrollZoom": True, "displayModeBar": True, "displaylogo": False}

#: Which quantity each locked specification is measured in.
SPEC_QUANTITY = {
    "x_D": "composition", "x_B": "composition", "D": "flow", "B": "flow",
    "R": "ratio", "Q_C": "duty", "Q_R": "duty",
    "Rec_LK": "fraction", "Rec_HK": "fraction",
}


# ---------------------------------------------------------------------------
# Sidebar: feed, hardware, and the single display-unit panel
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("⚗ Column configuration")

    mode = st.radio(
        "Operating mode",
        ["Design (Ponchon-Savarit)", "Rating (fixed stages)"],
        help="Design steps stages to hit the specified purities. "
             "Rating fixes the tray count and finds the compositions it delivers.",
    )

    ui.render_unit_panel(st)

    st.subheader("Feed")
    flow_unit = ui.unit_for("flow")
    F = to_canonical(
        st.number_input(
            f"Feed flow rate F [{flow_unit}]",
            min_value=from_canonical(1.0, "flow", flow_unit),
            max_value=from_canonical(10000.0, "flow", flow_unit),
            value=from_canonical(100.0, "flow", flow_unit),
            step=from_canonical(10.0, "flow", flow_unit),
            key=f"feed_flow_{flow_unit}",
        ),
        "flow", flow_unit,
    )

    comp_unit = ui.unit_for("composition")
    z_F = to_canonical(
        st.slider(
            f"Feed IPA composition z_F [{comp_unit}]",
            from_canonical(0.02, "composition", comp_unit),
            from_canonical(0.65, "composition", comp_unit),
            from_canonical(0.20, "composition", comp_unit),
            display_step(0.01, "composition", comp_unit, 0.20),
        ),
        "composition", comp_unit,
    )

    pressure_unit = ui.unit_for("pressure")
    P = to_canonical(
        st.number_input(
            f"Column pressure [{pressure_unit}]",
            min_value=from_canonical(20000.0, "pressure", pressure_unit),
            max_value=from_canonical(500000.0, "pressure", pressure_unit),
            value=from_canonical(101325.0, "pressure", pressure_unit),
            step=from_canonical(5000.0, "pressure", pressure_unit),
            key=f"column_pressure_{pressure_unit}",
        ),
        "pressure", pressure_unit,
    )

    q_option = st.selectbox(
        "Thermal condition of feed",
        ["Saturated liquid (q = 1)", "Subcooled liquid (q > 1)",
         "Saturated vapour (q = 0)", "Superheated vapour (q < 0)",
         "Two-phase mixture (0 < q < 1)"],
        help="q is the liquid fraction after an isenthalpic flash at column "
             "pressure. It sets the slope of the McCabe-Thiele q-line.",
    )
    if "Saturated liquid" in q_option:
        q_value = 1.0
    elif "Saturated vapour" in q_option:
        q_value = 0.0
    elif "Subcooled" in q_option:
        q_value = st.slider("Feed q-value", 1.05, 1.50, 1.15, 0.05)
    elif "Superheated" in q_option:
        q_value = st.slider("Feed q-value", -0.50, -0.05, -0.15, 0.05)
    else:
        q_value = st.slider("Feed q-value", 0.10, 0.90, 0.50, 0.05)
    feed_state = th.calculate_feed_state(z_F, P, q=q_value)

    st.subheader("Hardware and efficiency")
    subcooling_dT = 0.0
    if st.checkbox("Subcooled reflux", value=False):
        dt_unit = ui.unit_for("delta_temperature")
        subcooling_dT = to_canonical(
            st.slider(
                f"Subcooling ΔT [{dt_unit}]",
                from_canonical(1.0, "delta_temperature", dt_unit),
                from_canonical(30.0, "delta_temperature", dt_unit),
                from_canonical(10.0, "delta_temperature", dt_unit),
                from_canonical(1.0, "delta_temperature", dt_unit),
            ),
            "delta_temperature", dt_unit,
        )

    murphree_eff = st.slider(
        "Murphree tray efficiency E_MV", 0.20, 1.00, 1.00, 0.05,
        help="Fraction of the equilibrium composition change actually achieved "
             "on a real tray.",
    )

    if "Rating" in mode:
        st.subheader("Rating specification")
        N_spec = st.number_input("Total stages N", 3, 50, 10)
        N_feed_spec = st.number_input("Feed stage from top", 1, int(N_spec), 5)


# ---------------------------------------------------------------------------
# Specification locker
# ---------------------------------------------------------------------------

if ("dof" not in st.session_state
        or st.session_state.dof.F != F
        or st.session_state.dof.z_F != z_F
        or st.session_state.dof.P != P):
    st.session_state.dof = DOFManager(F=F, z_F=z_F, P=P)
    st.session_state.dof.recompute(feed_state, subcooling_dT)
dof = st.session_state.dof

st.title("⚗ Isopropanol / water rigorous distillation simulator")
st.caption(
    "Ponchon-Savarit (H-x-y), McCabe-Thiele (x-y), VLE (T-x-y) and non-CMO "
    "internal flow profiles. All physical properties from chetools."
)


def render_specification_locker() -> None:
    """Two locked specifications; the other seven follow from the balances."""
    st.markdown(
        "Lock **exactly two** specifications 🔒. The remaining variables are "
        "computed from the mass and enthalpy balances, so the column can never be "
        "over- or under-specified. See tutorial §1 for why the budget is two."
    )
    left, right = st.columns(2)
    spec1 = left.selectbox(
        "Locked specification #1", options=ALL_SPECS,
        format_func=lambda s: SPEC_LABELS[s],
        index=ALL_SPECS.index(dof.locked_specs[0]),
    )
    available = [s for s in ALL_SPECS if s != spec1 and {spec1, s} != {"D", "B"}]
    default_index = (available.index(dof.locked_specs[1])
                     if dof.locked_specs[1] in available else 0)
    spec2 = right.selectbox(
        "Locked specification #2", options=available,
        format_func=lambda s: SPEC_LABELS[s], index=default_index,
    )
    dof.set_locked_pair(spec1, spec2)

    x_azeo, _ = th.find_azeotrope(P)
    grid = st.columns(3) + st.columns(3) + st.columns(3)

    for slot, spec in zip(grid, ALL_SPECS):
        with slot:
            locked = spec in dof.locked_specs
            badge = ('<span class="locked-badge">&#128274; LOCKED</span>' if locked
                     else '<span class="unlocked-badge">&#128273; COMPUTED</span>')
            st.markdown(
                f'<span class="spec-name">{SPEC_LABELS[spec]}</span> {badge}',
                unsafe_allow_html=True,
            )

            quantity = SPEC_QUANTITY[spec]
            unit = ui.unit_for(quantity)
            value = float(dof.values[spec])
            shown = from_canonical(value, quantity, unit)

            if not locked:
                digits = 5 if spec in ("x_D", "x_B", "Rec_LK", "Rec_HK") else 4
                st.markdown(
                    f'<div class="computed-value">{shown:.{digits}g} '
                    f'<span class="metric-unit">{unit}</span></div>',
                    unsafe_allow_html=True,
                )
                continue

            if spec == "x_D":
                low, high = z_F + 0.01, x_azeo - 0.005
                new = st.slider(
                    "x_D", from_canonical(low, quantity, unit),
                    from_canonical(high, quantity, unit),
                    from_canonical(float(np.clip(value, low, high)), quantity, unit),
                    display_step(0.005, quantity, unit, value),
                    label_visibility="collapsed",
                )
            elif spec == "x_B":
                low, high = 0.001, z_F - 0.005
                new = st.slider(
                    "x_B", from_canonical(low, quantity, unit),
                    from_canonical(high, quantity, unit),
                    from_canonical(float(np.clip(value, low, high)), quantity, unit),
                    display_step(0.005, quantity, unit, value),
                    label_visibility="collapsed",
                )
            elif spec == "R":
                new = st.slider("R", 0.5, 15.0, float(max(0.5, shown)), 0.1,
                                label_visibility="collapsed")
            elif spec in ("Rec_LK", "Rec_HK"):
                new = st.slider(
                    spec, from_canonical(0.10, quantity, unit),
                    from_canonical(0.999, quantity, unit),
                    from_canonical(float(np.clip(value, 0.10, 0.999)), quantity, unit),
                    from_canonical(0.005, quantity, unit),
                    label_visibility="collapsed",
                )
            else:
                new = st.number_input(
                    f"{spec} [{unit}]", value=shown,
                    step=from_canonical(1.0, quantity, unit),
                    label_visibility="collapsed",
                    key=f"dof_input_{spec}_{unit}",
                )
            dof.values[spec] = to_canonical(new, quantity, unit)

    dof.recompute(feed_state, subcooling_dT)
    if dof.warning_msg:
        st.warning(dof.warning_msg)


with st.expander("🔐 Specification locker — exactly two degrees of freedom", expanded=True):
    render_specification_locker()


# ---------------------------------------------------------------------------
# Solve
# ---------------------------------------------------------------------------

x_D, x_B = dof.values["x_D"], dof.values["x_B"]
R, D = dof.values["R"], dof.values["D"]

with st.spinner("Solving Ponchon-Savarit stages and MESH energy balances…"):
    vle_data = th.get_vle_curves(P, n_points=240)
    if "Design" in mode:
        result = col.solve_design_column(
            F, z_F, P, x_D, x_B, R, feed_state, subcooling_dT, murphree_eff
        )
    else:
        result = col.solve_rating_column(
            F, z_F, P, feed_state, N_spec, N_feed_spec, R, D,
            subcooling_dT, murphree_eff,
        )


# ---------------------------------------------------------------------------
# Persistent KPI strip
# ---------------------------------------------------------------------------

kpis = st.columns(6)
ui.kpi_card(kpis[0], "Total stages", f"{result['total_stages']}", "",
            f"{result['tray_count']} trays + partial reboiler")
ui.kpi_card(kpis[1], "Feed stage", f"{result['feed_stage']}", "", "counted from top")
ui.kpi_card(kpis[2], "Min reflux R_min", f"{result['R_min']:.3g}", "mol/mol",
            f"R/R_min = {R / max(0.01, result['R_min']):.3g}")
ui.kpi_card(kpis[3], "Min stages N_min", f"{result['N_min']}", "",
            "total-reflux limit")
duty_unit = ui.unit_for("duty")
ui.kpi_card(kpis[4], "Condenser duty Q_C",
            f"{from_canonical(result['Q_C'], 'duty', duty_unit):.4g}", duty_unit,
            "total condenser")
ui.kpi_card(kpis[5], "Reboiler duty Q_R",
            f"{from_canonical(result['Q_R'], 'duty', duty_unit):.4g}", duty_unit,
            "partial reboiler")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_design, tab_diagrams, tab_sizing, tab_audit, tab_learn = st.tabs(
    ["⚗ Design", "📊 Diagrams", "🏗 Sizing & economics", "🔍 Audit", "📖 Learn"]
)


with tab_design:
    ui.section(
        "Stage-by-stage solution",
        "Every row is one equilibrium-stage iteration: compositions and temperature "
        "from the NRTL equilibrium root, enthalpies on the common reference, and "
        "L and V from the Ponchon-Savarit lever rule.",
    )

    summary = st.columns(4)
    ui.kpi_card(summary[0], "Distillate D", ui.show(result["D"], "flow"), "",
                f"x_D = {result['x_D']:.4g}")
    ui.kpi_card(summary[1], "Bottoms B", ui.show(result["B"], "flow"), "",
                f"x_B = {result['x_B']:.4g}")
    ui.kpi_card(summary[2], "Top temperature", ui.show(result["T_D_C"], "temperature"),
                "", "bubble point of the distillate")
    ui.kpi_card(summary[3], "Bottom temperature", ui.show(result["T_B_C"], "temperature"),
                "", "bubble point of the bottoms")

    stages = pd.DataFrame(result["stages"])
    c_unit, t_unit = ui.unit_for("composition"), ui.unit_for("temperature")
    h_unit, f_unit = ui.unit_for("enthalpy"), ui.unit_for("flow")
    for name in ("x", "y"):
        stages[name] = from_canonical(stages[name].to_numpy(), "composition", c_unit)
    stages["T_C"] = from_canonical(stages["T_C"].to_numpy(), "temperature", t_unit)
    for name in ("h_L", "H_V"):
        stages[name] = from_canonical(stages[name].to_numpy(), "enthalpy", h_unit)
    for name in ("L", "V"):
        stages[name] = from_canonical(stages[name].to_numpy(), "flow", f_unit)
    stages = stages.rename(columns={
        "stage": "Stage", "section": "Section",
        "x": f"x_IPA ({c_unit})", "y": f"y_IPA ({c_unit})",
        "T_C": f"T ({t_unit})", "h_L": f"h_L ({h_unit})", "H_V": f"H_V ({h_unit})",
        "L": f"L_n ({f_unit})", "V": f"V_n ({f_unit})",
    })
    st.dataframe(stages, width="stretch", hide_index=True)
    st.download_button(
        "⬇ Download stage profiles (CSV)",
        stages.to_csv(index=False).encode("utf-8"),
        "distillation_stages.csv", "text/csv",
    )


with tab_diagrams:
    ui.section(
        "Distillation visualisation dashboard",
        "Axis units follow the display-units panel in the sidebar.",
    )
    row1 = st.columns(2)
    with row1[0]:
        st.plotly_chart(
            plots.plot_xy(vle_data, result, z_F, ui.unit_for("composition")),
            width="stretch", config=PLOTLY_CONFIG,
        )
    with row1[1]:
        st.plotly_chart(
            plots.plot_txy(vle_data, result, z_F, P,
                           ui.unit_for("composition"), ui.unit_for("temperature")),
            width="stretch", config=PLOTLY_CONFIG,
        )
    row2 = st.columns(2)
    with row2[0]:
        st.plotly_chart(
            plots.plot_ponchon_savarit(vle_data, result, z_F, feed_state["h_F"],
                                       ui.unit_for("composition"), ui.unit_for("enthalpy")),
            width="stretch", config=PLOTLY_CONFIG,
        )
    with row2[1]:
        st.plotly_chart(
            plots.plot_flow_profiles(result, ui.unit_for("flow")),
            width="stretch", config=PLOTLY_CONFIG,
        )


with tab_sizing:
    render_sizing_dashboard(result)


with tab_audit:
    ui.section(
        "Calculation audit",
        "KPI cards are rounded for readability; these ledgers retain full "
        "calculation precision and link to the exact source lines.",
    )
    render_process_calculation_audit(result)

    with st.expander("Thermodynamic model summary", expanded=False):
        st.markdown(r"""
##### Pure-component correlations (from `chetools/data`)
- **Vapour pressure** (DIPPR 101): $\ln P^{vap} = A + B/T + C\ln T + D\,T^{E}$
- **Heat of vaporisation** (DIPPR 106): $\Delta H_{vap} = A(1-T_r)^{B + CT_r + DT_r^2 + ET_r^3}$
- **Liquid heat capacity** (DIPPR 100): $C_{p,L} = A + BT + CT^2 + DT^3 + ET^4$

##### Reference state and enthalpies
Pure saturated liquid at $25\,^\circ\mathrm{C}$ ($298.15$ K), where $h_i = 0$.

$$h_L(x,T)=\sum_i x_i\!\int_{298.15}^{T}\!\!C_{p,L,i}\,dT + h^E(x,T)$$
$$H_V(y,T)=\sum_i y_i\left[\int_{298.15}^{T}\!\!C_{p,L,i}\,dT+\Delta H_{vap,i}(T)\right]$$

##### NRTL
Parameters $B_{12}=20.06$ K, $B_{21}=832.98$ K, $\alpha=0.326$ (component 1 = IPA).
Excess enthalpy follows from Gibbs–Helmholtz,
$h^E=-RT^2\sum_i x_i\,\partial\ln\gamma_i/\partial T$,
evaluated by complex-step differentiation. Full derivation in **Learn → §2**.
""")


with tab_learn:
    render_tutorial(vle_data, result, z_F, feed_state, P)
