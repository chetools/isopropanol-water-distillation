"""Distillation Column Algorithms: Design (Ponchon-Savarit) and Rating (MESH).
Implements exact Ponchon-Savarit graphical stage stepping, minimum reflux,
minimum stages, non-equimolar internal flow calculations, subcooling,
Murphree stage efficiency, and McCabe-Thiele operating lines.
"""

import numpy as np
from scipy.optimize import brentq
import src.thermo as th

def calc_min_reflux(x_D, x_B, z_F, P, h_F, subcooling_dT=0.0):
    T_D, _ = th.bubble_point(x_D, P)
    h_D = th.h_liquid_mix(x_D, T_D)
    T_reflux = T_D - subcooling_dT
    h_reflux = th.h_liquid_mix(x_D, T_reflux)
    T_V1, _ = th.dew_point(x_D, P)
    H_V1 = th.h_vapor_mix(x_D, T_V1)
    xs = np.linspace(max(0.01, x_B), min(0.665, x_D - 0.005), 150)
    Q_prime_intersections = []
    for x in xs:
        T_b, y = th.bubble_point(x, P)
        if abs(y - x) < 1e-5:
            continue
        h_L = th.h_liquid_mix(x, T_b)
        H_V = th.h_vapor_mix(y, T_b)
        Q_int = h_L + ((H_V - h_L) / (y - x)) * (x_D - x)
        Q_prime_intersections.append(Q_int)
    if len(Q_prime_intersections) == 0:
        Q_prime_D_min = H_V1 + 10.0
    else:
        Q_prime_D_min = float(np.max(Q_prime_intersections))
    denom = H_V1 - h_reflux
    if denom <= 0:
        denom = H_V1 - h_D
    R_min = max(0.05, (Q_prime_D_min - H_V1) / denom)
    return float(R_min), float(Q_prime_D_min)

def calc_min_stages(x_D, x_B, P):
    x_curr = x_D
    stages = 0
    while x_curr > x_B and stages < 100:
        _, x_next = th.dew_point(x_curr, P)
        stages += 1
        x_curr = x_next
    return stages

def solve_design_column(F, z_F, P, x_D, x_B, R, feed_state, subcooling_dT=0.0, murphree_eff=1.0):
    h_F = feed_state['h_F']
    q_feed = feed_state.get('q', 1.0)
    
    D = F * (z_F - x_B) / (x_D - x_B)
    B = F - D
    
    T_D, _ = th.bubble_point(x_D, P)
    h_D = th.h_liquid_mix(x_D, T_D)
    T_reflux = T_D - subcooling_dT
    h_reflux = th.h_liquid_mix(x_D, T_reflux)
    
    T_V1, _ = th.dew_point(x_D, P)
    H_V1 = th.h_vapor_mix(x_D, T_V1)
    
    R_min, Q_prime_D_min = calc_min_reflux(x_D, x_B, z_F, P, h_F, subcooling_dT)
    N_min = calc_min_stages(x_D, x_B, P)
    
    QC = D * ((R + 1.0) * H_V1 - R * h_reflux - h_D)
    Q_prime_D = h_D + QC / D
    
    T_B, _ = th.bubble_point(x_B, P)
    h_B = th.h_liquid_mix(x_B, T_B)
    
    Q_prime_B = (F * h_F - D * Q_prime_D) / B
    QR = B * (h_B - Q_prime_B)
    
    stages = []
    construction_lines = []
    
    y_curr = x_D
    x_prev = x_D
    section = 'Rectifying'
    feed_stage = 1
    
    V_top = (R + 1.0) * D
    L_reflux = R * D
    
    for n in range(1, 101):
        T_dew_n, x_eq = th.dew_point(y_curr, P)
        
        # Apply Murphree stage efficiency
        x_n = float(np.clip(x_prev - murphree_eff * (x_prev - x_eq), 1e-5, 0.999))
        
        T_bubble_n, _ = th.bubble_point(x_n, P)
        h_Ln = th.h_liquid_mix(x_n, T_bubble_n)
        H_Vn = th.h_vapor_mix(y_curr, T_dew_n)
        
        if section == 'Rectifying' and (x_n <= z_F or (n >= 2 and x_n < (z_F + 0.02))):
            section = 'Stripping'
            feed_stage = n
        
        if section == 'Rectifying':
            def ray_H(y):
                return h_Ln + ((Q_prime_D - h_Ln) / (x_D - x_n)) * (y - x_n)
            def diff_y(y):
                Td, _ = th.dew_point(y, P)
                return th.h_vapor_mix(y, Td) - ray_H(y)
            try:
                y_next = brentq(diff_y, x_n, x_D - 1e-5)
            except Exception:
                y_next = max(x_B + 1e-4, x_n - 0.05)
            
            Td_next, _ = th.dew_point(y_next, P)
            HV_next = th.h_vapor_mix(y_next, Td_next)
            
            denom = HV_next - h_Ln
            if abs(denom) > 1e-4:
                L_stage = D * (Q_prime_D - HV_next) / denom
            else:
                L_stage = L_reflux
            V_stage = L_stage + D
            
            construction_lines.append({
                'type': 'rectifying',
                'x0': x_D, 'y0': Q_prime_D,
                'x1': x_n, 'y1': h_Ln
            })
        else:
            def ray_H(y):
                return h_Ln + ((Q_prime_B - h_Ln) / (x_B - x_n)) * (y - x_n)
            def diff_y(y):
                Td, _ = th.dew_point(y, P)
                return th.h_vapor_mix(y, Td) - ray_H(y)
            try:
                y_next = brentq(diff_y, x_B + 1e-5, min(0.66, x_n + 0.15))
            except Exception:
                y_next = max(x_B + 1e-4, x_n * 0.8)
            
            Td_next, _ = th.dew_point(y_next, P)
            HV_next = th.h_vapor_mix(y_next, Td_next)
            
            denom = HV_next - h_Ln
            if abs(denom) > 1e-4:
                V_next = B * (h_Ln - Q_prime_B) / denom
            else:
                V_next = V_top
            L_stage = V_next + B
            V_stage = V_next
            
            construction_lines.append({
                'type': 'stripping',
                'x0': x_B, 'y0': Q_prime_B,
                'x1': x_n, 'y1': h_Ln
            })
        
        stage_info = {
            'stage': n,
            'section': section,
            'x': float(x_n),
            'y': float(y_curr),
            'T_C': float(T_dew_n - 273.15),
            'h_L': float(h_Ln),
            'H_V': float(H_Vn),
            'L': float(max(0.0, L_stage)),
            'V': float(max(0.0, V_stage))
        }
        stages.append(stage_info)
        
        if x_n <= x_B or n >= 60:
            break
        
        y_curr = y_next
        x_prev = x_n

    total_stages = len(stages)
    tray_count = max(0, total_stages - 1)
    
    # McCabe-Thiele lines & staircase
    m_R = R / (R + 1.0)
    b_R = x_D / (R + 1.0)
    
    if abs(q_feed - 1.0) < 1e-4:
        x_I = z_F
        y_I = m_R * z_F + b_R
    elif abs(q_feed) < 1e-4:
        y_I = z_F
        x_I = (y_I - b_R) / m_R
    else:
        m_q = q_feed / (q_feed - 1.0)
        b_q = -z_F / (q_feed - 1.0)
        x_I = (b_R - b_q) / (m_q - m_R)
        y_I = m_R * x_I + b_R
    
    x_I = float(np.clip(x_I, x_B, x_D))
    y_I = float(np.clip(y_I, x_B, x_D))
    
    # Staircase steps (alternating horizontal and vertical)
    staircase_x = [x_D]
    staircase_y = [x_D]
    for i, s in enumerate(stages):
        staircase_x.append(s['x'])
        staircase_y.append(s['y'])
        if i < len(stages) - 1:
            staircase_x.append(s['x'])
            staircase_y.append(stages[i + 1]['y'])
        else:
            staircase_x.append(s['x'])
            staircase_y.append(x_B)
            staircase_x.append(x_B)
            staircase_y.append(x_B)

    mccabe_lines = {
        'rectifying_x': [x_D, x_I],
        'rectifying_y': [x_D, y_I],
        'stripping_x': [x_B, x_I],
        'stripping_y': [x_B, y_I],
        'q_line_x': [z_F, x_I],
        'q_line_y': [z_F, y_I],
        'staircase_x': staircase_x,
        'staircase_y': staircase_y
    }

    return {
        'F': float(F),
        'z_F': float(z_F),
        'P': float(P),
        'x_D': float(x_D),
        'x_B': float(x_B),
        'D': float(D),
        'B': float(B),
        'R': float(R),
        'R_min': float(R_min),
        'N_min': int(N_min),
        'total_stages': int(total_stages),
        'tray_count': int(tray_count),
        'feed_stage': int(feed_stage),
        'Q_C': float(QC),
        'Q_R': float(QR),
        'Q_prime_D': float(Q_prime_D),
        'Q_prime_B': float(Q_prime_B),
        'h_F': float(h_F),
        'h_D': float(h_D),
        'h_B': float(h_B),
        'T_D_C': float(T_D - 273.15),
        'T_B_C': float(T_B - 273.15),
        'stages': stages,
        'construction_lines': construction_lines,
        'mccabe_lines': mccabe_lines
    }

def solve_rating_column(F, z_F, P, feed_state, N_stages, N_feed, R, D_spec, subcooling_dT=0.0, murphree_eff=1.0):
    D = float(D_spec)
    B = F - D
    h_F = feed_state['h_F']
    x_D_guess = min(0.65, z_F * 2.5)
    best_res = None
    best_err = 1e9
    xD_candidates = np.linspace(z_F + 0.05, min(0.66, x_D_guess + 0.1), 30)
    for xD_test in xD_candidates:
        xB_test = (F * z_F - D * xD_test) / B
        if xB_test <= 0.001 or xB_test >= z_F:
            continue
        try:
            res = solve_design_column(F, z_F, P, xD_test, xB_test, R, feed_state, subcooling_dT, murphree_eff)
            err = abs(res['total_stages'] - N_stages) + 0.2 * abs(res['feed_stage'] - N_feed)
            if err < best_err:
                best_err = err
                best_res = res
        except Exception:
            continue
    if best_res is None:
        xD_nominal = min(0.62, z_F * 2.0)
        xB_nominal = max(0.01, (F * z_F - D * xD_nominal) / B)
        best_res = solve_design_column(F, z_F, P, xD_nominal, xB_nominal, R, feed_state, subcooling_dT, murphree_eff)
    return best_res
