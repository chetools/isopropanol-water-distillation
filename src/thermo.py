"""Thermodynamic models and physical properties for Isopropanol / Water system.
Parameters strictly from chetools/chetools/data:
- Isopropanol (ID 145): IsopropanolProps.txt
- Water (ID 62): WaterProps.txt
- NRTL BIPs: BinaryNRTL.txt (30 Water, 36 Isopropanol)
"""

import numpy as np
from scipy.optimize import brentq

R_GAS = 8.314462618
T_REF = 298.15

MW_IPA = 60.096
TC_IPA = 508.31
PC_IPA = 4764300.0
TBN_IPA = 355.41

PVAP_IPA = {'A': 92.935, 'B': -8177.1, 'C': -10.031, 'D': 3.9988e-6, 'E': 2.0}
HVAP_IPA = {'A': 5.6980e7, 'B': 0.0870, 'C': 0.3007, 'D': 0.0, 'E': 0.0}
CPL_IPA = {'A': 4.6640e5, 'B': -4108.6, 'C': 14.506, 'D': -0.014126, 'E': 0.0}

MW_WATER = 18.015
TC_WATER = 647.35
PC_WATER = 2.211823e7
TBN_WATER = 373.15

PVAP_WATER = {'A': 72.550, 'B': -7206.7, 'C': -7.1385, 'D': 4.0460e-6, 'E': 2.0}
HVAP_WATER = {'A': 5.2053e7, 'B': 0.3199, 'C': -0.2120, 'D': 0.2580, 'E': 0.0}
CPL_WATER = {'A': 2.7637e5, 'B': -2090.1, 'C': 8.1250, 'D': -0.014116, 'E': 9.3701e-6}

NRTL_B12 = 20.06
NRTL_B21 = 832.98
NRTL_ALPHA = 0.326

def pvap_ipa(T):
    T = np.asarray(T, dtype=float)
    return np.exp(PVAP_IPA['A'] + PVAP_IPA['B']/T + PVAP_IPA['C']*np.log(T) + PVAP_IPA['D']*(T**PVAP_IPA['E']))

def pvap_water(T):
    T = np.asarray(T, dtype=float)
    return np.exp(PVAP_WATER['A'] + PVAP_WATER['B']/T + PVAP_WATER['C']*np.log(T) + PVAP_WATER['D']*(T**PVAP_WATER['E']))

def t_boil_ipa(P=101325.0):
    return brentq(lambda T: pvap_ipa(T) - P, 280.0, 500.0)

def t_boil_water(P=101325.0):
    return brentq(lambda T: pvap_water(T) - P, 280.0, 500.0)

def hvap_ipa(T):
    T = np.asarray(T, dtype=float)
    Tr = T / TC_IPA
    return HVAP_IPA['A'] * (1.0 - Tr)**(HVAP_IPA['B'] + HVAP_IPA['C']*Tr + HVAP_IPA['D']*Tr**2 + HVAP_IPA['E']*Tr**3) / 1.0e6

def hvap_water(T):
    T = np.asarray(T, dtype=float)
    Tr = T / TC_WATER
    return HVAP_WATER['A'] * (1.0 - Tr)**(HVAP_WATER['B'] + HVAP_WATER['C']*Tr + HVAP_WATER['D']*Tr**2 + HVAP_WATER['E']*Tr**3) / 1.0e6

def _int_cpl(p_dict, T):
    A, B, C, D, E = p_dict['A'], p_dict['B'], p_dict['C'], p_dict['D'], p_dict['E']
    return A*T + (B/2.0)*T**2 + (C/3.0)*T**3 + (D/4.0)*T**4 + (E/5.0)*T**5

def h_liquid_pure_ipa(T):
    T = np.asarray(T, dtype=float)
    return (_int_cpl(CPL_IPA, T) - _int_cpl(CPL_IPA, T_REF)) / 1.0e6

def h_liquid_pure_water(T):
    T = np.asarray(T, dtype=float)
    return (_int_cpl(CPL_WATER, T) - _int_cpl(CPL_WATER, T_REF)) / 1.0e6

def nrtl_gamma(x1, T):
    x1 = np.clip(np.asarray(x1, dtype=float), 1e-15, 1.0 - 1e-15)
    x2 = 1.0 - x1
    T = np.asarray(T, dtype=float)
    tau12 = NRTL_B12 / T
    tau21 = NRTL_B21 / T
    G12 = np.exp(-NRTL_ALPHA * tau12)
    G21 = np.exp(-NRTL_ALPHA * tau21)
    term1 = tau21 * (G21 / (x1 + x2 * G21))**2
    term2 = tau12 * G12 / ((x2 + x1 * G12)**2)
    ln_g1 = (x2**2) * (term1 + term2)
    term3 = tau12 * (G12 / (x2 + x1 * G12))**2
    term4 = tau21 * G21 / ((x1 + x2 * G21)**2)
    ln_g2 = (x1**2) * (term3 + term4)
    return np.exp(ln_g1), np.exp(ln_g2)

def excess_enthalpy(x1, T):
    x1 = np.clip(np.asarray(x1, dtype=float), 0.0, 1.0)
    x2 = 1.0 - x1
    T = np.asarray(T, dtype=float)
    tau12 = NRTL_B12 / T
    tau21 = NRTL_B21 / T
    G12 = np.exp(-NRTL_ALPHA * tau12)
    G21 = np.exp(-NRTL_ALPHA * tau21)
    u1 = tau21 * G21
    v1 = x1 + x2 * G21
    u1_prime = (tau21 * G21 / T) * (NRTL_ALPHA * tau21 - 1.0)
    v1_prime = x2 * (NRTL_ALPHA * tau21 * G21 / T)
    dt1 = (u1_prime * v1 - u1 * v1_prime) / (v1**2)
    u2 = tau12 * G12
    v2 = x2 + x1 * G12
    u2_prime = (tau12 * G12 / T) * (NRTL_ALPHA * tau12 - 1.0)
    v2_prime = x1 * (NRTL_ALPHA * tau12 * G12 / T)
    dt2 = (u2_prime * v2 - u2 * v2_prime) / (v2**2)
    d_gE_dT = x1 * x2 * (dt1 + dt2)
    return -R_GAS * (T**2) * d_gE_dT / 1000.0

def h_liquid_mix(x1, T, include_heat_of_mixing=True):
    x1 = np.clip(np.asarray(x1, dtype=float), 0.0, 1.0)
    x2 = 1.0 - x1
    h_pure = x1 * h_liquid_pure_ipa(T) + x2 * h_liquid_pure_water(T)
    if include_heat_of_mixing:
        return h_pure + excess_enthalpy(x1, T)
    return h_pure

def h_vapor_mix(y1, T):
    y1 = np.clip(np.asarray(y1, dtype=float), 0.0, 1.0)
    y2 = 1.0 - y1
    h_v1 = h_liquid_pure_ipa(T) + hvap_ipa(T)
    h_v2 = h_liquid_pure_water(T) + hvap_water(T)
    return y1 * h_v1 + y2 * h_v2

def bubble_point(x1, P=101325.0):
    x1 = float(np.clip(x1, 0.0, 1.0))
    if x1 <= 1e-12:
        T_bp = t_boil_water(P)
        return T_bp, 0.0
    if x1 >= 1.0 - 1e-12:
        T_bp = t_boil_ipa(P)
        return T_bp, 1.0
    def f(T):
        g1, g2 = nrtl_gamma(x1, T)
        P_calc = x1 * g1 * pvap_ipa(T) + (1.0 - x1) * g2 * pvap_water(T)
        return P_calc - P
    T_bp1 = t_boil_ipa(P)
    T_bp2 = t_boil_water(P)
    t_low = min(T_bp1, T_bp2) - 15.0
    t_high = max(T_bp1, T_bp2) + 5.0
    T_bubble = brentq(f, t_low, t_high)
    g1, _ = nrtl_gamma(x1, T_bubble)
    y1 = float(np.clip(x1 * g1 * pvap_ipa(T_bubble) / P, 0.0, 1.0))
    return T_bubble, y1

def find_azeotrope(P=101325.0):
    def diff(x):
        T_b, y = bubble_point(x, P)
        return y - x
    x_azeo = brentq(diff, 0.45, 0.85)
    T_azeo, _ = bubble_point(x_azeo, P)
    return float(x_azeo), float(T_azeo)

def dew_point(y1, P=101325.0):
    y1 = float(np.clip(y1, 0.0, 1.0))
    if y1 <= 1e-9:
        return t_boil_water(P), 0.0
    if y1 >= 1.0 - 1e-9:
        return t_boil_ipa(P), 1.0
    x_az, T_az = find_azeotrope(P)
    if abs(y1 - x_az) < 1e-6:
        return T_az, x_az
    if y1 < x_az:
        def err(x):
            _, y_calc = bubble_point(x, P)
            return y_calc - y1
        x_sol = brentq(err, 0.0, x_az)
    else:
        def err(x):
            _, y_calc = bubble_point(x, P)
            return y_calc - y1
        x_sol = brentq(err, x_az, 1.0)
    T_sol, _ = bubble_point(x_sol, P)
    return T_sol, float(x_sol)

def get_vle_curves(P=101325.0, n_points=201):
    xs = np.linspace(0.0, 1.0, n_points)
    T_bubbles = np.zeros(n_points)
    ys = np.zeros(n_points)
    h_L = np.zeros(n_points)
    H_V = np.zeros(n_points)
    for i, x in enumerate(xs):
        T_b, y_val = bubble_point(x, P)
        T_bubbles[i] = T_b
        ys[i] = y_val
        h_L[i] = h_liquid_mix(x, T_b)
        H_V[i] = h_vapor_mix(y_val, T_b)
    x_az, T_az = find_azeotrope(P)
    return {
        'x': xs,
        'T_bubble_K': T_bubbles,
        'T_bubble_C': T_bubbles - 273.15,
        'y': ys,
        'h_L': h_L,
        'H_V': H_V,
        'x_azeo': x_az,
        'T_azeo_K': T_az,
        'T_azeo_C': T_az - 273.15
    }

def calculate_feed_state(z_F, P=101325.0, T_F=None, q=None):
    T_bubble_F, y_F_bubble = bubble_point(z_F, P)
    h_L_sat = h_liquid_mix(z_F, T_bubble_F)
    H_V_sat = h_vapor_mix(z_F, T_bubble_F)
    if q is not None:
        q_val = float(q)
        h_F = q_val * h_L_sat + (1.0 - q_val) * H_V_sat
        if q_val >= 1.0:
            dT = (h_F - h_L_sat) / (z_F * (CPL_IPA['A']/1e6) + (1.0 - z_F) * (CPL_WATER['A']/1e6))
            T_feed = T_bubble_F + dT
        else:
            T_feed = T_bubble_F
        return {
            'q': q_val,
            'h_F': h_F,
            'T_F_K': T_feed,
            'T_F_C': T_feed - 273.15,
            'T_bubble_K': T_bubble_F,
            'h_L_sat': h_L_sat,
            'H_V_sat': H_V_sat
        }
    elif T_F is not None:
        T_feed = float(T_F)
        if T_feed <= T_bubble_F:
            h_F = h_liquid_mix(z_F, T_feed)
            q_val = 1.0 + (h_L_sat - h_F) / (H_V_sat - h_L_sat)
        else:
            h_F = h_vapor_mix(z_F, T_feed)
            q_val = (H_V_sat - h_F) / (H_V_sat - h_L_sat)
        return {
            'q': float(q_val),
            'h_F': float(h_F),
            'T_F_K': T_feed,
            'T_F_C': T_feed - 273.15,
            'T_bubble_K': T_bubble_F,
            'h_L_sat': h_L_sat,
            'H_V_sat': H_V_sat
        }
    else:
        return calculate_feed_state(z_F, P, q=1.0)

generate_vle_curves = get_vle_curves
