"""Shared Streamlit presentation helpers: one units preference, one card style.

The interface used to carry a unit dropdown beside every displayed quantity --
29 of them on the main page alone, so the KPI strip was roughly half selector
by area.  Units are a *display preference*, not a per-widget decision, so they
now live in one panel and every display site reads the chosen unit from
:func:`unit_for`.
"""

import streamlit as st

import src.theme as theme
from src.units import default_unit, from_canonical, unit_options

#: Quantities the reader can choose a display unit for, grouped for the panel.
UNIT_GROUPS = {
    "Process": [
        ("flow", "Molar flow", "kgmol/h"),
        ("composition", "Composition", "mole fraction"),
        ("temperature", "Temperature", "°C"),
        ("pressure", "Pressure", "kPa(a)"),
        ("enthalpy", "Molar enthalpy", "kJ/mol"),
        ("duty", "Heat duty", "kW"),
    ],
    "Equipment": [
        ("length", "Length", "m"),
        ("area", "Area", "m²"),
        ("velocity", "Velocity", "m/s"),
        ("stress", "Stress", "MPa"),
        ("heat_transfer_coefficient", "Heat-transfer coefficient", "kW/m²/K"),
        ("delta_temperature", "Temperature difference", "K"),
    ],
    "Economics": [
        ("money", "Capital cost", "MUSD"),
        ("money_rate", "Annual cost", "kUSD/y"),
        ("energy_price", "Utility price", "USD/GJ"),
    ],
}

_ALL_QUANTITIES = [q for group in UNIT_GROUPS.values() for q, _, _ in group]


def _defaults() -> dict[str, str]:
    out = {}
    for group in UNIT_GROUPS.values():
        for quantity, _, preferred in group:
            options = unit_options(quantity)
            out[quantity] = preferred if preferred in options else default_unit(quantity)
    return out


def init_units() -> None:
    """Seed the session's unit preferences once."""
    if "units" not in st.session_state:
        st.session_state.units = _defaults()


def unit_for(quantity: str) -> str:
    """The reader's chosen display unit for a quantity."""
    init_units()
    if quantity not in st.session_state.units:
        st.session_state.units[quantity] = default_unit(quantity)
    return st.session_state.units[quantity]


def show(value, quantity: str, digits: int = 4) -> str:
    """Format a canonical value in the reader's chosen unit, with the unit."""
    unit = unit_for(quantity)
    return f"{from_canonical(value, quantity, unit):.{digits}g} {unit}"


def render_unit_panel(container=st) -> None:
    """One panel that sets every display unit in the application."""
    init_units()
    with container.expander("⚙ Display units", expanded=False):
        st.caption(
            "Display only. The solver always works in mol/s, Pa, K, kJ/mol and "
            "metres, so changing a unit here can never change a result."
        )
        for group_name, entries in UNIT_GROUPS.items():
            st.markdown(f"**{group_name}**")
            columns = st.columns(3)
            for index, (quantity, label, _) in enumerate(entries):
                options = unit_options(quantity)
                current = unit_for(quantity)
                st.session_state.units[quantity] = columns[index % 3].selectbox(
                    label, options,
                    index=options.index(current) if current in options else 0,
                    key=f"unit_pref_{quantity}",
                )
        if st.button("Reset to defaults", width="stretch"):
            for quantity, unit in _defaults().items():
                st.session_state[f"unit_pref_{quantity}"] = unit
            st.session_state.units = _defaults()
            st.rerun()


def kpi_card(container, title: str, value: str, unit: str = "", sub: str = "") -> None:
    """One KPI card.  Replaces six near-identical inline HTML blocks."""
    unit_markup = f'<span class="metric-unit">{unit}</span>' if unit else ""
    sub_markup = f'<div class="metric-sub">{sub}</div>' if sub else ""
    container.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-title">{title}</div>'
        f'<div class="metric-value">{value} {unit_markup}</div>'
        f'{sub_markup}</div>',
        unsafe_allow_html=True,
    )


def section(title: str, caption: str = "") -> None:
    """A consistent section heading."""
    st.markdown(
        f'<div style="font-size:{theme.FONT_SECTION}px;font-weight:700;'
        f'color:{theme.TEXT};margin:0.2rem 0 0.1rem 0;">{title}</div>',
        unsafe_allow_html=True,
    )
    if caption:
        st.caption(caption)
