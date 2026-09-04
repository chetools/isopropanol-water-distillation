from src.column import solve_design_column
from src.sizing import SizingBasis, build_sizing_reproduction_script, calculate_sizing
from src.thermo import calculate_feed_state


def test_preliminary_sizing_is_positive_and_cost_closes():
    p = 101325.0
    feed = calculate_feed_state(0.20, p, q=1.0)
    column = solve_design_column(100.0, 0.20, p, 0.60, 0.02, 3.0, feed)
    result = calculate_sizing(column, SizingBasis())
    assert result["diameter_m"] > 0
    assert result["tangent_height_m"] > 0
    assert result["condenser_area_m2"] > 0
    assert result["reboiler_area_m2"] > 0
    assert result["tac_usd_y"] == result["annualized_capital_usd_y"] + result["annual_opex_usd_y"]


def test_lower_allowable_flood_fraction_requires_larger_diameter():
    p = 101325.0
    feed = calculate_feed_state(0.20, p, q=1.0)
    column = solve_design_column(100.0, 0.20, p, 0.60, 0.02, 3.0, feed)
    d80 = calculate_sizing(column, SizingBasis(flood_fraction=0.80))["diameter_m"]
    d60 = calculate_sizing(column, SizingBasis(flood_fraction=0.60))["diameter_m"]
    assert d60 > d80


def test_downloaded_python_reproduces_dashboard_results():
    p = 101325.0
    feed = calculate_feed_state(0.20, p, q=1.0)
    column = solve_design_column(100.0, 0.20, p, 0.60, 0.02, 3.0, feed)
    basis = SizingBasis()
    expected = calculate_sizing(column, basis)
    namespace = {}
    exec(build_sizing_reproduction_script(column, basis), namespace)
    actual = namespace["results"]
    assert actual["diameter_m"] == expected["diameter_m"]
    assert actual["fixed_capital_usd"] == expected["fixed_capital_usd"]
    assert actual["tac_usd_y"] == expected["tac_usd_y"]
    assert len(expected["calculation_steps"]) == 37
