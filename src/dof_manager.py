"""Degree-of-Freedom Budget and Specification Locker.
Manages 9 operational specifications: x_D, x_B, D, B, R, Q_C, Q_R, Rec_LK, Rec_HK.
Enforces N_dof == 2, prevents over-specification, and performs feasibility clamping.
"""

import numpy as np
import src.thermo as th

ALL_SPECS = ['x_D', 'x_B', 'D', 'B', 'R', 'Q_C', 'Q_R', 'Rec_LK', 'Rec_HK']
SPEC_LABELS = {
    'x_D': 'Distillate IPA Mole Fraction (x_D)',
    'x_B': 'Bottoms IPA Mole Fraction (x_B)',
    'D': 'Distillate Flow Rate (D, mol/s or kmol/h)',
    'B': 'Bottoms Flow Rate (B, mol/s or kmol/h)',
    'R': 'Reflux Ratio (R = L_0 / D)',
    'Q_C': 'Condenser Heat Duty (Q_C, kW)',
    'Q_R': 'Reboiler Heat Duty (Q_R, kW)',
    'Rec_LK': 'Light Key (IPA) Recovery in Distillate (Rec_LK)',
    'Rec_HK': 'Heavy Key (Water) Recovery in Bottoms (Rec_HK)'
}

class DOFManager:
    def __init__(self, F=100.0, z_F=0.20, P=101325.0):
        self.F = float(F)
        self.z_F = float(z_F)
        self.P = float(P)
        
        self.locked_specs = ['x_D', 'R']
        
        self.values = {
            'x_D': 0.60,
            'x_B': 0.02,
            'D': 31.03,
            'B': 68.97,
            'R': 3.0,
            'Q_C': 5000.0,
            'Q_R': 5000.0,
            'Rec_LK': 0.931,
            'Rec_HK': 0.845
        }
        self.warning_msg = None

    def lock_spec(self, spec_name):
        if spec_name not in self.locked_specs:
            self.locked_specs.pop(0)
            self.locked_specs.append(spec_name)

    def set_locked_pair(self, spec1, spec2):
        if spec1 == spec2:
            return
        if {spec1, spec2} == {'D', 'B'}:
            return
        self.locked_specs = [spec1, spec2]

    def update_value(self, spec_name, new_val, feed_state, subcooling_dT=0.0):
        self.lock_spec(spec_name)
        self.values[spec_name] = float(new_val)
        self.recompute(feed_state, subcooling_dT)

    def clamp_feasibility(self, x_azeo):
        warnings = []
        if self.z_F < x_azeo:
            max_xD = x_azeo - 0.005
            min_xD = self.z_F + 0.01
            if self.values['x_D'] > max_xD:
                self.values['x_D'] = max_xD
                warnings.append(f"x_D clamped to {max_xD:.4f}: Cannot exceed the minimum-boiling azeotrope ({x_azeo:.4f}).")
            elif self.values['x_D'] < min_xD:
                self.values['x_D'] = min_xD
                warnings.append(f"x_D clamped to {min_xD:.4f}: Distillate must be richer than feed.")
            
            max_xB = self.z_F - 0.005
            min_xB = 0.001
            if self.values['x_B'] > max_xB:
                self.values['x_B'] = max_xB
                warnings.append(f"x_B clamped to {max_xB:.4f}: Bottoms must be leaner than feed.")
            elif self.values['x_B'] < min_xB:
                self.values['x_B'] = min_xB
                warnings.append(f"x_B clamped to {min_xB:.4f}: Bottoms purity limit.")
        
        if self.values['D'] >= self.F:
            self.values['D'] = self.F * 0.95
        elif self.values['D'] <= 0:
            self.values['D'] = self.F * 0.05
        
        if self.values['R'] < 0.05:
            self.values['R'] = 0.05
            warnings.append("Reflux ratio clamped to minimum positive value (0.05).")
        
        self.values['Rec_LK'] = float(np.clip(self.values['Rec_LK'], 0.01, 0.999))
        self.values['Rec_HK'] = float(np.clip(self.values['Rec_HK'], 0.01, 0.999))
        
        self.warning_msg = " ".join(warnings) if warnings else None

    def recompute(self, feed_state, subcooling_dT=0.0):
        x_azeo, _ = th.find_azeotrope(self.P)
        self.clamp_feasibility(x_azeo)
        s1, s2 = self.locked_specs
        F, z_F, P = self.F, self.z_F, self.P
        h_F = feed_state['h_F']
        
        # Handle key recovery specifications
        if {'Rec_LK', 'Rec_HK'}.issubset({s1, s2}):
            r_lk = self.values['Rec_LK']
            r_hk = self.values['Rec_HK']
            D_ipa = F * z_F * r_lk
            D_water = F * (1.0 - z_F) * (1.0 - r_hk)
            D = max(0.1, D_ipa + D_water)
            xD = D_ipa / D if D > 0 else z_F
            B = max(0.1, F - D)
            self.values['D'] = float(D)
            self.values['B'] = float(B)
            clamped_xD = float(np.clip(xD, z_F + 0.001, x_azeo - 0.005))
            self.values['x_D'] = clamped_xD
            xB = (F * z_F - D * clamped_xD) / B
            self.values['x_B'] = float(np.clip(xB, 0.001, z_F - 0.001))
        elif 'Rec_LK' in {s1, s2}:
            r_lk = self.values['Rec_LK']
            D_ipa = F * z_F * r_lk
            if 'x_D' in {s1, s2}:
                xD = self.values['x_D']
                D = D_ipa / xD
                B = F - D
                xB = (F * z_F - D_ipa) / B if B > 0 else 0.01
                self.values['D'] = float(D)
                self.values['B'] = float(B)
                self.values['x_B'] = float(np.clip(xB, 0.001, z_F - 0.001))
            elif 'x_B' in {s1, s2}:
                xB = self.values['x_B']
                B_ipa = F * z_F * (1.0 - r_lk)
                B = B_ipa / xB
                D = F - B
                xD = D_ipa / D if D > 0 else z_F
                self.values['D'] = float(D)
                self.values['B'] = float(B)
                self.values['x_D'] = float(np.clip(xD, z_F + 0.001, x_azeo - 0.005))
            else:
                xD = self.values['x_D']
                D = D_ipa / xD
                B = F - D
                xB = (F * z_F - D_ipa) / B if B > 0 else 0.01
                self.values['D'] = float(D)
                self.values['B'] = float(B)
                self.values['x_B'] = float(np.clip(xB, 0.001, z_F - 0.001))
        elif 'Rec_HK' in {s1, s2}:
            r_hk = self.values['Rec_HK']
            B_water = F * (1.0 - z_F) * r_hk
            if 'x_B' in {s1, s2}:
                xB = self.values['x_B']
                B = B_water / (1.0 - xB) if xB < 0.99 else F * 0.5
                D = F - B
                xD = (F * z_F - B * xB) / D if D > 0 else z_F
                self.values['D'] = float(D)
                self.values['B'] = float(B)
                self.values['x_D'] = float(np.clip(xD, z_F + 0.001, x_azeo - 0.005))
            elif 'x_D' in {s1, s2}:
                xD = self.values['x_D']
                D_water = F * (1.0 - z_F) * (1.0 - r_hk)
                D = D_water / (1.0 - xD) if xD < 0.99 else F * 0.5
                B = F - D
                xB = (F * z_F - D * xD) / B if B > 0 else 0.01
                self.values['D'] = float(D)
                self.values['B'] = float(B)
                self.values['x_B'] = float(np.clip(xB, 0.001, z_F - 0.001))
            else:
                xB = self.values['x_B']
                B = B_water / (1.0 - xB) if xB < 0.99 else F * 0.5
                D = F - B
                xD = (F * z_F - B * xB) / D if D > 0 else z_F
                self.values['D'] = float(D)
                self.values['B'] = float(B)
                self.values['x_D'] = float(np.clip(xD, z_F + 0.001, x_azeo - 0.005))
        elif {'x_D', 'x_B'}.issubset({s1, s2}):
            xD = self.values['x_D']
            xB = self.values['x_B']
            D = F * (z_F - xB) / (xD - xB)
            B = F - D
            self.values['D'] = float(D)
            self.values['B'] = float(B)
        elif 'D' in {s1, s2}:
            D = self.values['D']
            B = F - D
            self.values['B'] = float(B)
            if 'x_D' in {s1, s2}:
                xD = self.values['x_D']
                xB = (F * z_F - D * xD) / B
                self.values['x_B'] = float(np.clip(xB, 0.001, z_F - 0.001))
            elif 'x_B' in {s1, s2}:
                xB = self.values['x_B']
                xD = (F * z_F - B * xB) / D
                self.values['x_D'] = float(np.clip(xD, z_F + 0.001, x_azeo - 0.001))
        elif 'B' in {s1, s2}:
            B = self.values['B']
            D = F - B
            self.values['D'] = float(D)
            if 'x_D' in {s1, s2}:
                xD = self.values['x_D']
                xB = (F * z_F - D * xD) / B
                self.values['x_B'] = float(np.clip(xB, 0.001, z_F - 0.001))
            elif 'x_B' in {s1, s2}:
                xB = self.values['x_B']
                xD = (F * z_F - B * xB) / D
                self.values['x_D'] = float(np.clip(xD, z_F + 0.001, x_azeo - 0.001))
        else:
            D = self.values['D']
            B = F - D
            self.values['B'] = float(B)

        xD = self.values['x_D']
        xB = self.values['x_B']
        D = self.values['D']
        B = self.values['B']
        
        # Update recoveries
        self.values['Rec_LK'] = float((D * xD) / (F * z_F))
        self.values['Rec_HK'] = float((B * (1.0 - xB)) / (F * (1.0 - z_F)))
        
        T_D, _ = th.bubble_point(xD, P)
        h_D = th.h_liquid_mix(xD, T_D)
        T_reflux = T_D - subcooling_dT
        h_reflux = th.h_liquid_mix(xD, T_reflux)
        T_V1, _ = th.dew_point(xD, P)
        H_V1 = th.h_vapor_mix(xD, T_V1)
        T_B, _ = th.bubble_point(xB, P)
        h_B = th.h_liquid_mix(xB, T_B)
        
        if 'Q_C' in {s1, s2}:
            QC = self.values['Q_C']
            denom = H_V1 - h_reflux
            R = (QC / D + h_D - H_V1) / denom if denom > 0 else 2.0
            self.values['R'] = float(max(0.1, R))
        elif 'Q_R' in {s1, s2}:
            QR = self.values['Q_R']
            QC = QR + F * h_F - D * h_D - B * h_B
            denom = H_V1 - h_reflux
            R = (QC / D + h_D - H_V1) / denom if denom > 0 else 2.0
            self.values['R'] = float(max(0.1, R))
            self.values['Q_C'] = float(QC)
        else:
            R = self.values['R']
            QC = D * ((R + 1.0) * H_V1 - R * h_reflux - h_D)
            self.values['Q_C'] = float(QC)

        QC = self.values['Q_C']
        QR = QC + D * h_D + B * h_B - F * h_F
        self.values['Q_R'] = float(QR)
