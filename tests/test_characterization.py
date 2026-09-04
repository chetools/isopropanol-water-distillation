"""Golden-reference tests pinning physics outputs across refactoring.

`tests/golden/reference.npz` was generated from the pre-vectorization
implementation.  These tests exist so the array-form rewrites of the NRTL,
enthalpy, and VLE routines can be verified to reproduce the original scalar
results to floating-point tolerance rather than merely "look right".

Regenerate deliberately (and review the diff) only when a physics model is
intentionally changed:  ``uv run python tests/golden/regenerate.py``
"""

import numpy as np
import pytest

import src.column as col
import src.thermo as th

GOLDEN = np.load("tests/golden/reference.npz")

PRESSURES = [101325.0, 50000.0, 300000.0]


def test_nrtl_activity_coefficients_match_reference_grid():
    """gamma_1, gamma_2 over a 21x21 (T, x) grid."""
    T, x = GOLDEN["T_grid"], GOLDEN["x_grid"]
    TT, XX = np.meshgrid(T, x, indexing="ij")
    g1, g2 = th.nrtl_gamma(XX, TT)
    assert np.allclose(g1, GOLDEN["gamma1"], rtol=1e-12, atol=1e-12)
    assert np.allclose(g2, GOLDEN["gamma2"], rtol=1e-12, atol=1e-12)


def test_excess_enthalpy_matches_reference_grid():
    T, x = GOLDEN["T_grid"], GOLDEN["x_grid"]
    TT, XX = np.meshgrid(T, x, indexing="ij")
    assert np.allclose(th.excess_enthalpy(XX, TT), GOLDEN["h_excess"], rtol=1e-11, atol=1e-13)


@pytest.mark.parametrize("P", PRESSURES)
def test_vle_curves_match_reference(P):
    tag = str(int(P))
    vle = th.get_vle_curves(P, n_points=61)
    assert np.allclose(vle["x"], GOLDEN[f"vle_{tag}_x"], atol=1e-14)
    assert np.allclose(vle["T_bubble_K"], GOLDEN[f"vle_{tag}_T_bubble_K"], atol=1e-8)
    assert np.allclose(vle["y"], GOLDEN[f"vle_{tag}_y"], atol=1e-10)
    assert np.allclose(vle["h_L"], GOLDEN[f"vle_{tag}_h_L"], atol=1e-10)
    assert np.allclose(vle["H_V"], GOLDEN[f"vle_{tag}_H_V"], atol=1e-10)


@pytest.mark.parametrize("P", PRESSURES)
def test_azeotrope_matches_reference(P):
    x_az, T_az = th.find_azeotrope(P)
    expected = GOLDEN[f"azeo_{int(P)}"]
    assert x_az == pytest.approx(expected[0], abs=1e-9)
    assert T_az == pytest.approx(expected[1], abs=1e-7)


@pytest.mark.parametrize("P", PRESSURES)
def test_dew_point_branch_matches_reference(P):
    tag = str(int(P))
    got = np.array([th.dew_point(y, P) for y in GOLDEN[f"dew_{tag}_y"]])
    assert np.allclose(got[:, 0], GOLDEN[f"dew_{tag}"][:, 0], atol=1e-7)
    assert np.allclose(got[:, 1], GOLDEN[f"dew_{tag}"][:, 1], atol=1e-9)


def _reference_column():
    feed = th.calculate_feed_state(0.20, 101325.0, q=1.0)
    return col.solve_design_column(100.0, 0.20, 101325.0, 0.60, 0.02, 3.0, feed)


def test_design_column_scalars_match_reference():
    r = _reference_column()
    names = ["D", "B", "Q_C", "Q_R", "Q_prime_D", "Q_prime_B", "R_min",
             "h_F", "h_D", "h_B", "T_D_C", "T_B_C"]
    got = np.array([r[n] for n in names])
    assert np.allclose(got, GOLDEN["col_scalars"], rtol=1e-9), dict(
        zip(names, zip(got, GOLDEN["col_scalars"]))
    )


def test_design_column_stage_counts_match_reference():
    r = _reference_column()
    got = np.array([r["total_stages"], r["N_min"], r["feed_stage"], r["tray_count"]])
    assert np.array_equal(got, GOLDEN["col_ints"])


def test_design_column_stage_profiles_match_reference():
    r = _reference_column()
    for key, field in (("col_stage_x", "x"), ("col_stage_y", "y"),
                       ("col_stage_L", "L"), ("col_stage_V", "V")):
        got = np.array([s[field] for s in r["stages"]])
        assert np.allclose(got, GOLDEN[key], rtol=1e-8, atol=1e-10), field


def test_mccabe_staircase_matches_reference():
    r = _reference_column()
    m = r["mccabe_lines"]
    assert np.allclose(m["staircase_x"], GOLDEN["col_stair_x"], atol=1e-9)
    assert np.allclose(m["staircase_y"], GOLDEN["col_stair_y"], atol=1e-9)
