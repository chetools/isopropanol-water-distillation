"""Unit Tests for Isopropanol/Water Ponchon-Savarit Distillation System."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import numpy as np
import src.thermo as th
import src.column as col
from src.dof_manager import DOFManager

def test_pure_component_boiling_points():
    P = 101325.0
    T_ipa = th.t_boil_ipa(P)
    T_water = th.t_boil_water(P)
    assert abs(T_ipa - 355.62) < 0.5, f"IPA Tb {T_ipa} out of range"
    assert abs(T_water - 373.15) < 0.5, f"Water Tb {T_water} out of range"

def test_reference_state_enthalpy():
    # Pure saturated liquid at 25 °C (298.15 K) must have h == 0
    assert abs(th.h_liquid_pure_ipa(298.15)) < 1e-9
    assert abs(th.h_liquid_pure_water(298.15)) < 1e-9

def test_azeotrope_detection():
    x_az, T_az = th.find_azeotrope(101325.0)
    assert 0.65 < x_az < 0.69, f"Azeotrope composition {x_az} unexpected"
    assert 352.0 < T_az < 355.0, f"Azeotrope T {T_az} unexpected"
    # At azeotrope, y == x
    T_bub, y_az = th.bubble_point(x_az, 101325.0)
    assert abs(y_az - x_az) < 1e-4

def test_analytical_excess_enthalpy():
    T = 330.0
    x = 0.40
    h_analytic = th.excess_enthalpy(x, T)
    dT = 1e-5
    g1_p, g2_p = th.nrtl_gamma(x, T + dT)
    g1_m, g2_m = th.nrtl_gamma(x, T - dT)
    gE_p = x * np.log(g1_p) + (1 - x) * np.log(g2_p)
    gE_m = x * np.log(g1_m) + (1 - x) * np.log(g2_m)
    dgE_dT = (gE_p - gE_m) / (2 * dT)
    h_numeric = -th.R_GAS * (T**2) * dgE_dT / 1000.0
    assert abs(h_analytic - h_numeric) < 1e-4

def test_ponchon_savarit_collinearity():
    F = 100.0; z_F = 0.20; P = 101325.0; x_D = 0.60; x_B = 0.02; R = 3.0
    feed = th.calculate_feed_state(z_F, P, q=1.0)
    res = col.solve_design_column(F, z_F, P, x_D, x_B, R, feed)
    slope_DF = (res['Q_prime_D'] - res['h_F']) / (x_D - z_F)
    slope_FB = (res['h_F'] - res['Q_prime_B']) / (z_F - x_B)
    assert abs(slope_DF - slope_FB) < 1e-6, "Δ_D, F, Δ_B are not collinear!"


def test_ponchon_operating_rays_reach_equilibrium_vapor_curve():
    """Every displayed ray passes through liquid and next-vapor endpoints."""
    P = 101325.0
    feed = th.calculate_feed_state(0.20, P, q=1.0)
    res = col.solve_design_column(100.0, 0.20, P, 0.60, 0.02, 3.0, feed)
    assert res['construction_lines']
    for ray in res['construction_lines']:
        slope_01 = (ray['y1'] - ray['y0']) / (ray['x1'] - ray['x0'])
        slope_02 = (ray['y2'] - ray['y0']) / (ray['x2'] - ray['x0'])
        assert slope_01 == pytest.approx(slope_02, rel=1e-7, abs=1e-7)
        T_dew, _ = th.dew_point(ray['x2'], P)
        assert ray['y2'] == pytest.approx(th.h_vapor_mix(ray['x2'], T_dew), abs=1e-8)


def test_mccabe_staircase_alternates_equilibrium_and_operating_steps():
    """Horizontal endpoints are equilibrated; vertical endpoints lie on an operating line."""
    P = 101325.0
    x_D, x_B, z_F, R = 0.60, 0.02, 0.20, 3.0
    feed = th.calculate_feed_state(z_F, P, q=1.0)
    res = col.solve_design_column(100.0, z_F, P, x_D, x_B, R, feed)
    m = res['mccabe_lines']
    xs, ys = m['staircase_x'], m['staircase_y']
    x_i, y_i = m['rectifying_x'][-1], m['rectifying_y'][-1]
    m_r, b_r = R / (R + 1.0), x_D / (R + 1.0)
    m_s = (y_i - x_B) / (x_i - x_B)
    b_s = x_B * (1.0 - m_s)
    for i in range(1, len(xs), 2):
        assert ys[i] == pytest.approx(ys[i - 1])
        _, x_eq = th.dew_point(ys[i], P)
        assert xs[i] == pytest.approx(x_eq, abs=1e-8)
        if i + 1 < len(xs):
            assert xs[i + 1] == pytest.approx(xs[i])
            expected = m_r * xs[i] + b_r if xs[i] >= x_i else m_s * xs[i] + b_s
            assert ys[i + 1] == pytest.approx(expected, abs=1e-8)

def test_non_equimolar_overflow_variation():
    F = 100.0; z_F = 0.20; P = 101325.0; x_D = 0.60; x_B = 0.02; R = 3.0
    feed = th.calculate_feed_state(z_F, P, q=1.0)
    res = col.solve_design_column(F, z_F, P, x_D, x_B, R, feed)
    stages = res['stages']
    L_rect = stages[0]['L']
    L_strip = stages[-1]['L']
    assert L_strip > L_rect + 50.0, "Feed liquid flow jump not reflected"

def test_dof_manager_locker():
    dof = DOFManager(F=100.0, z_F=0.20, P=101325.0)
    feed = th.calculate_feed_state(0.20, 101325.0, q=1.0)
    dof.recompute(feed)
    assert len(dof.locked_specs) == 2
    assert abs(dof.values['D'] + dof.values['B'] - 100.0) < 1e-4

def test_key_recoveries_specification():
    dof = DOFManager(F=100.0, z_F=0.20, P=101325.0)
    feed = th.calculate_feed_state(0.20, 101325.0, q=1.0)
    dof.set_locked_pair('Rec_LK', 'Rec_HK')
    dof.values['Rec_LK'] = 0.80
    dof.values['Rec_HK'] = 0.85
    dof.recompute(feed)
    # Confirm mass balance consistency
    D = dof.values['D']
    B = dof.values['B']
    xD = dof.values['x_D']
    xB = dof.values['x_B']
    assert abs(D + B - 100.0) < 1e-4
    assert abs(D * xD + B * xB - 20.0) < 1e-3

def test_murphree_efficiency_effect():
    F = 100.0; z_F = 0.20; P = 101325.0; x_D = 0.60; x_B = 0.02; R = 3.0
    feed = th.calculate_feed_state(z_F, P, q=1.0)
    res_ideal = col.solve_design_column(F, z_F, P, x_D, x_B, R, feed, murphree_eff=1.0)
    res_actual = col.solve_design_column(F, z_F, P, x_D, x_B, R, feed, murphree_eff=0.70)
    assert res_actual['total_stages'] > res_ideal['total_stages'], "Murphree efficiency did not increase stage count!"

def test_streamlit_app_executes():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file('../app.py').run(timeout=30)
    assert len(at.exception) == 0, f"App raised exceptions: {[e.message for e in at.exception]}"
