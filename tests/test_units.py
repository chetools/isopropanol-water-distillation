import pytest

from src.units import from_canonical, to_canonical, unit_options


@pytest.mark.parametrize("quantity", [
    "flow", "pressure", "duty", "temperature", "delta_temperature", "length",
    "area", "velocity", "density", "mass", "enthalpy", "heat_transfer_coefficient",
    "energy", "energy_price", "money", "money_rate", "hours_year", "fraction", "composition",
])
def test_every_engineering_unit_round_trips(quantity):
    canonical = 0.345 if quantity in {"composition", "fraction"} else 12.345
    for unit in unit_options(quantity):
        displayed = from_canonical(canonical, quantity, unit)
        assert to_canonical(displayed, quantity, unit) == pytest.approx(canonical)
