import pytest

from src.units import from_canonical, to_canonical, unit_options


@pytest.mark.parametrize("quantity", [
    "flow", "pressure", "duty", "temperature", "delta_temperature", "length",
    "area", "velocity", "density", "mass", "enthalpy", "heat_transfer_coefficient",
    "energy", "energy_price", "money", "money_rate", "hours_year", "fraction", "composition",
])
def test_every_engineering_unit_round_trips(quantity):
    for unit in unit_options(quantity):
        displayed = from_canonical(12.345, quantity, unit)
        assert to_canonical(displayed, quantity, unit) == pytest.approx(12.345)

