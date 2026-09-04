"""Isopropanol / water rigorous distillation simulator.

Ponchon-Savarit, McCabe-Thiele, T-x-y and non-CMO internal flow profiles,
with preliminary sizing, economics, a full calculation audit, and a
step-by-step engineering tutorial.

Layout: a persistent KPI strip above five tabs, so the headline results stay
visible while the reader moves between design, diagrams, sizing, audit and
the tutorial.
"""

import hashlib
import importlib
import sys

import numpy as np
import pandas as pd
import streamlit as st

# --- Streamlit Community Cloud stale-module guard ---------------------------
# After a redeploy the Cloud runner can keep already-imported ``src.*`` modules
# from the previous revision while serving the new ``app.py``.  The mismatch is
# silent until a caller uses something the old module cannot do -- e.g. the new
# array-aware ``units.from_canonical`` being served by a copy that still does
# ``float(value)``, which raises TypeError on an array.
#
# Reloading in dependency order matters: a module that did
# ``from src.units import from_canonical`` keeps its old binding until it is
# itself reloaded, so every dependency must be refreshed before its dependents.
_MODULE_RELOAD_ORDER = (
    "src.units", "src.theme", "src.source_links",
    "src.thermo", "src.flash", "src.column", "src.sizing",
    "src.plotting", "src.ui", "src.dof_manager",
    "src.engineering_diagrams", "src.process_audit", "src.sizing_dashboard",
    "src.tutorial.layout",
    "src.tutorial.ch00_nomenclature", "src.tutorial.ch01_overview",
    "src.tutorial.ch02_equilibrium", "src.tutorial.ch03_flash",
    "src.tutorial.ch04_mccabe", "src.tutorial.ch05_ponchon",
    "src.tutorial.ch06_equipment", "src.tutorial.ch07_safety",
    "src.tutorial.ch08_validation", "src.tutorial",
)


@st.cache_resource
def _refresh_source_modules() -> int:
    """Reload ``src.*`` once per process, before this module binds names from them.

    ``st.cache_resource`` makes this process-global, so it runs once per boot
    -- which is precisely when staleness can exist -- rather than on every
    script rerun.  On a cold start the modules are not yet imported and the
    loop is a no-op.
    """
    reloaded = 0
    for name in _MODULE_RELOAD_ORDER:
        module = sys.modules.get(name)
        if module is None:
            continue
        try:
            importlib.reload(module)
            reloaded += 1
        except Exception:
            # A refresh failure must not take the app down; the normal import
            # below still yields a working (if possibly stale) module.
            pass
    return reloaded


_refresh_source_modules()

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

PLOTLY_CONFIG = {
    "scrollZoom": True,
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
}

#: Which quantity each locked specification is measured in.
SPEC_QUANTITY = {
    "x_D": "composition", "x_B": "composition", "D": "flow", "B": "flow",
    "R": "ratio", "Q_C": "duty", "Q_R": "duty",
    "Rec_LK": "fraction", "Rec_HK": "fraction",
}


@st.cache_data(show_spinner=False)
def _cached_vle_curves(pressure: float, n_points: int) -> dict:
    return th.get_vle_curves(pressure, n_points=n_points)


@st.cache_data(show_spinner="Solving Ponchon-Savarit stages and MESH energy balances…")
def _cached_column_solve(
    mode_is_rating: bool,
    F: float,
    z_F: float,
    P: float,
    q: float,
    x_D: float,
    x_B: float,
    R: float,
    D: float,
    N_spec: int,
    N_feed: int,
    subcooling_dT: float,
    murphree_eff: float,
    feed_stage_spec: int,
) -> dict:
    """Physics-only cache. Every solver input is a primitive so a change in
    q, N, reflux, feed stage, etc. cannot reuse a previous column.
    Display-unit changes do not appear here and so do not re-solve.
    """
    feed = th.calculate_feed_state(z_F, P, q=q)
    locked_feed = None if feed_stage_spec <= 0 else feed_stage_spec
    if mode_is_rating:
        return col.solve_rating_column(
            F, z_F, P, feed, N_spec, N_feed, R, D, subcooling_dT, murphree_eff,
            feed_stage_spec=locked_feed,
        )
    return col.solve_design_column(
        F, z_F, P, x_D, x_B, R, feed, subcooling_dT, murphree_eff,
        feed_stage_spec=locked_feed,
    )


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

    feed_placement = st.radio(
        "Feed location",
        ["Optimal (feed-line crossing)", "Specified tray"],
        help="Optimal switches from the rectifying to the stripping difference "
             "point where the construction crosses the feed composition — the "
             "nozzle that minimises stages for this split (tutorial §5D). "
             "Specified locks the switch at a tray, as in an existing column.",
    )

    N_spec = 0
    N_feed_spec = 0
    feed_stage_spec = None
    if "Rating" in mode:
        st.subheader("Rating specification")
        st.session_state.setdefault("rating_stages", 10)
        N_spec = int(st.number_input(
            "Total stages N", min_value=3, max_value=50, step=1,
            key="rating_stages",
            help="Equilibrium stages including the partial reboiler.",
        ))

    if "Specified" in feed_placement:
        n_feed_max = N_spec if "Rating" in mode else 50
        # The feed stage cannot exceed the stage count, and Streamlit retains a
        # widget's previous value across reruns.  Lowering N below the retained
        # feed stage therefore raises StreamlitValueAboveMaxError unless the
        # stored value is clamped *before* the widget is rendered.
        st.session_state.setdefault("specified_feed_stage", 5)
        st.session_state.specified_feed_stage = min(
            max(1, int(st.session_state.get("specified_feed_stage", 5))),
            n_feed_max,
        )
        feed_stage_spec = int(st.number_input(
            "Feed stage from top", min_value=1, max_value=n_feed_max, step=1,
            key="specified_feed_stage",
            help="First stripping stage, counted from the top. "
                 "The total condenser is not a stage.",
        ))
        N_feed_spec = feed_stage_spec


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

vle_data = _cached_vle_curves(float(P), 240)
result = _cached_column_solve(
    "Rating" in mode,
    float(F), float(z_F), float(P), float(q_value),
    float(x_D), float(x_B), float(R), float(D),
    int(N_spec), int(N_feed_spec),
    float(subcooling_dT), float(murphree_eff),
    0 if feed_stage_spec is None else int(feed_stage_spec),
)


def _figure_key(name: str) -> str:
    """Remount Plotly figures when any physics input changes.

    Streamlit can keep a previous Plotly trace set if the chart widget is
    identified only by position.  Hashing the solver arguments into the
    widget key forces a redraw when q, N, R, feed stage, etc. change.
    """
    payload = (
        name, mode, float(F), float(z_F), float(P), float(q_value),
        float(x_D), float(x_B), float(R), float(D),
        int(N_spec), int(N_feed_spec), float(subcooling_dT),
        float(murphree_eff),
        0 if feed_stage_spec is None else int(feed_stage_spec),
        int(result["total_stages"]), int(result["feed_stage"]),
    )
    digest = hashlib.sha1(repr(payload).encode("utf-8")).hexdigest()[:16]
    return f"{name}_{digest}"


# ---------------------------------------------------------------------------
# Persistent KPI strip
# ---------------------------------------------------------------------------

kpis = st.columns(6)
ui.kpi_card(kpis[0], "Total stages", f"{result['total_stages']}", "",
            f"{result['tray_count']} trays + partial reboiler")
_used_feed = result["feed_stage"]
_opt_feed = result.get("optimal_feed_stage", _used_feed)
if result.get("feed_stage_spec") is None:
    _feed_sub = "feed-line crossing (tutorial §5D)"
elif _used_feed == _opt_feed:
    _feed_sub = "specified, and it is the crossing"
else:
    _feed_sub = f"specified · crossing would be {_opt_feed}"
ui.kpi_card(kpis[1], "Feed stage", f"{_used_feed}", "", _feed_sub)
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

# In rating mode the requested hardware is not always attainable at the given
# reflux ratio and distillate rate.  Say so plainly rather than quietly
# returning a different column than the one that was asked for.
rating = result.get("rating")
if rating and rating["message"]:
    st.warning(
        f"**Rating specification not met.** You asked for "
        f"{rating['requested_stages']} stages; this column delivers "
        f"{result['total_stages']}. {rating['message']}"
    )
elif rating and rating.get("requested_feed_stage") is not None and not rating["feed_stage_met"]:
    st.warning(
        f"Specified feed stage {rating['requested_feed_stage']} is below the "
        f"last stage of this column ({result['total_stages']}). The construction "
        f"never switches to stripping."
    )
elif (
    result.get("feed_stage_spec") is not None
    and result["feed_stage"] != result.get("optimal_feed_stage", result["feed_stage"])
):
    _off = result["feed_stage"] - result["optimal_feed_stage"]
    _side = "below" if _off > 0 else "above"
    st.info(
        f"Feed is on stage {result['feed_stage']}, {_side} the feed-line "
        f"crossing at stage {result['optimal_feed_stage']}. Off-optimal feed "
        f"uses the wrong difference point on some stages, so the split is worse "
        f"than the same reflux at the crossing (tutorial §5D)."
    )


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
    if result.get("mccabe_lines", {}).get("pinched"):
        st.info(
            "The McCabe–Thiele (CMO) staircase pinches before it reaches $x_B$. "
            "That is the constant-molal-overflow construction at this $R$ and split; "
            f"$R/R_{{\\min}}$ = {R / max(0.01, result['R_min']):.3g}. "
            "Ponchon–Savarit still closes because it does not assume CMO."
        )
    row1 = st.columns(2)
    with row1[0]:
        st.plotly_chart(
            plots.plot_xy(vle_data, result, z_F, ui.unit_for("composition")),
            width="stretch", config=PLOTLY_CONFIG, key=_figure_key("xy"),
        )
    with row1[1]:
        st.plotly_chart(
            plots.plot_txy(vle_data, result, z_F, P,
                           ui.unit_for("composition"), ui.unit_for("temperature")),
            width="stretch", config=PLOTLY_CONFIG, key=_figure_key("txy"),
        )
    row2 = st.columns(2)
    with row2[0]:
        st.plotly_chart(
            plots.plot_ponchon_savarit(vle_data, result, z_F, feed_state["h_F"],
                                       ui.unit_for("composition"), ui.unit_for("enthalpy")),
            width="stretch", config=PLOTLY_CONFIG, key=_figure_key("ponchon"),
        )
    with row2[1]:
        st.plotly_chart(
            plots.plot_flow_profiles(result, ui.unit_for("flow")),
            width="stretch", config=PLOTLY_CONFIG, key=_figure_key("flows"),
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
