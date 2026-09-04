"""Transparent preliminary tray-column sizing and class-4 cost estimate.

The correlations are intentionally exposed through ``SizingBasis``. Results are
screening estimates, not mechanical design or vendor guarantees.
"""

from dataclasses import dataclass, asdict
from math import pi, sqrt


R_GAS = 8.314462618  # Pa m3 / (mol K)
MW_IPA = 60.096  # kg/kmol
MW_WATER = 18.015


@dataclass(frozen=True)
class SizingBasis:
    flood_fraction: float = 0.80
    capacity_factor_m_s: float = 0.107
    downcomer_fraction: float = 0.15
    tray_spacing_m: float = 0.55
    top_disengagement_m: float = 2.5
    bottom_sump_m: float = 3.0
    shell_allowance_m: float = 1.0
    design_pressure_bar_abs: float = 3.0
    allowable_stress_mpa: float = 115.0
    weld_efficiency: float = 0.85
    corrosion_allowance_mm: float = 3.0
    condenser_u_kw_m2_k: float = 0.85
    condenser_lmtd_k: float = 15.0
    reboiler_u_kw_m2_k: float = 0.75
    reboiler_lmtd_k: float = 20.0
    material_factor: float = 1.0
    project_cost_index: float = 820.0
    base_cost_index: float = 800.0
    operating_hours_y: float = 8000.0
    steam_usd_gj: float = 12.0
    cooling_usd_gj: float = 0.60
    discount_rate: float = 0.10
    project_life_y: int = 15


def _liquid_density(x_ipa: float) -> float:
    """Additive-liquid-volume estimate at near-ambient conditions, kg/m3."""
    mw_mix = x_ipa * MW_IPA + (1.0 - x_ipa) * MW_WATER
    molar_volume = x_ipa * MW_IPA / 785.0 + (1.0 - x_ipa) * MW_WATER / 997.0
    return mw_mix / molar_volume


def _step(order, symbol, quantity, formula, substitution, value, unit, provenance):
    """Create one machine-readable row in the calculation ledger."""
    return {
        "Step": order,
        "Symbol": symbol,
        "Quantity": quantity,
        "Formula": formula,
        "Numerical substitution": substitution,
        "Value": float(value),
        "Unit": unit,
        "Basis / provenance": provenance,
    }


def calculate_sizing(column: dict, basis: SizingBasis) -> dict:
    stages = column["stages"]
    governing = max(stages, key=lambda row: row["V"])
    vapor_mol_s = max(float(governing["V"]), 1e-9)
    y_ipa = float(governing["y"])
    t_k = float(governing["T_C"]) + 273.15
    pressure_pa = float(column["P"])

    mw_vapor_kg_mol = (y_ipa * MW_IPA + (1.0 - y_ipa) * MW_WATER) / 1000.0
    rho_v = pressure_pa * mw_vapor_kg_mol / (R_GAS * t_k)
    rho_l = _liquid_density(float(governing["x"]))
    vapor_volume_m3_s = vapor_mol_s * R_GAS * t_k / pressure_pa

    u_flood = basis.capacity_factor_m_s * sqrt(max((rho_l - rho_v) / rho_v, 0.0))
    u_design = basis.flood_fraction * u_flood
    active_area = vapor_volume_m3_s / max(u_design, 1e-9)
    total_area = active_area / (1.0 - basis.downcomer_fraction)
    diameter = sqrt(4.0 * total_area / pi)

    tray_count = int(column["tray_count"])
    tangent_height = (
        max(tray_count - 1, 0) * basis.tray_spacing_m
        + basis.top_disengagement_m
        + basis.bottom_sump_m
        + basis.shell_allowance_m
    )
    p_design_pa = basis.design_pressure_bar_abs * 1e5
    stress_pa = basis.allowable_stress_mpa * 1e6
    pressure_thickness = p_design_pa * diameter / max(
        2.0 * stress_pa * basis.weld_efficiency - 1.2 * p_design_pa, 1.0
    )
    shell_thickness = max(0.006, pressure_thickness + basis.corrosion_allowance_mm / 1000.0)
    tray_stack_height = max(tray_count - 1, 0) * basis.tray_spacing_m
    shell_steel_volume = pi * diameter * tangent_height * shell_thickness
    shell_mass = shell_steel_volume * 7850.0 * 1.20

    condenser_area = abs(float(column["Q_C"])) / (
        basis.condenser_u_kw_m2_k * basis.condenser_lmtd_k
    )
    reboiler_area = abs(float(column["Q_R"])) / (
        basis.reboiler_u_kw_m2_k * basis.reboiler_lmtd_k
    )

    index_ratio = basis.project_cost_index / basis.base_cost_index
    shell_cost = 120_000.0 * (max(shell_mass, 1000.0) / 10_000.0) ** 0.62
    trays_cost = 7_500.0 * max(tray_count, 1) * max(diameter, 0.6) ** 1.55
    condenser_cost = 65_000.0 * (max(condenser_area, 10.0) / 100.0) ** 0.65
    reboiler_cost = 75_000.0 * (max(reboiler_area, 10.0) / 100.0) ** 0.65
    purchased = basis.material_factor * index_ratio * (
        shell_cost + trays_cost + condenser_cost + reboiler_cost
    )
    installed = 2.75 * purchased
    controls_and_contingency = 0.25 * installed
    fixed_capital = installed + controls_and_contingency

    steam_gj_y = abs(float(column["Q_R"])) * basis.operating_hours_y * 0.0036
    cooling_gj_y = abs(float(column["Q_C"])) * basis.operating_hours_y * 0.0036
    steam_cost = steam_gj_y * basis.steam_usd_gj
    cooling_cost = cooling_gj_y * basis.cooling_usd_gj
    maintenance = 0.03 * fixed_capital
    annual_opex = steam_cost + cooling_cost + maintenance
    i = basis.discount_rate
    n = basis.project_life_y
    crf = i * (1.0 + i) ** n / ((1.0 + i) ** n - 1.0) if i else 1.0 / n
    annualized_capital = crf * fixed_capital

    calculation_steps = [
        _step(1, "V_max", "Governing stage vapor rate", "max(V_n)",
              f"max of {len(stages)} stage vapor rates; stage {int(governing['stage'])}", vapor_mol_s, "mol/s", "Column stage solution"),
        _step(2, "T_g", "Governing absolute temperature", "T_C + 273.15",
              f"{float(governing['T_C']):.8g} + 273.15", t_k, "K", "Column stage solution"),
        _step(3, "MW_v", "Vapor-mixture molecular weight", "y_IPA MW_IPA + (1-y_IPA) MW_water",
              f"{y_ipa:.8g}×{MW_IPA} + (1-{y_ipa:.8g})×{MW_WATER}", mw_vapor_kg_mol * 1000.0, "kg/kmol", "Ideal mixture molecular weight"),
        _step(4, "rho_v", "Vapor density", "P MW_v/(R T)",
              f"{pressure_pa:.8g}×{mw_vapor_kg_mol:.8g}/({R_GAS:.10g}×{t_k:.8g})", rho_v, "kg/m³", "Ideal-gas equation; Z=1"),
        _step(5, "rho_L", "Liquid density", "MW_mix / sum(x_i MW_i/rho_i)",
              f"({float(governing['x']):.8g}×{MW_IPA} + (1-{float(governing['x']):.8g})×{MW_WATER}) / "
              f"({float(governing['x']):.8g}×{MW_IPA}/785 + (1-{float(governing['x']):.8g})×{MW_WATER}/997)", rho_l, "kg/m³", "Additive liquid volumes; pure densities 785 and 997 kg/m³"),
        _step(6, "Vdot", "Actual vapor volumetric rate", "n_dot R T/P",
              f"{vapor_mol_s:.8g}×{R_GAS:.10g}×{t_k:.8g}/{pressure_pa:.8g}", vapor_volume_m3_s, "m³/s", "Ideal-gas equation; Z=1"),
        _step(7, "u_flood", "Souders–Brown flood velocity", "C sqrt((rho_L-rho_v)/rho_v)",
              f"{basis.capacity_factor_m_s:.8g}×sqrt(({rho_l:.8g}-{rho_v:.8g})/{rho_v:.8g})", u_flood, "m/s", "User capacity factor; vendor hydraulic check required"),
        _step(8, "u_design", "Design superficial velocity", "f_flood u_flood",
              f"{basis.flood_fraction:.8g}×{u_flood:.8g}", u_design, "m/s", "User-selected fraction of flood"),
        _step(9, "A_active", "Required active bubbling area", "Vdot/u_design",
              f"{vapor_volume_m3_s:.8g}/{u_design:.8g}", active_area, "m²", "Continuity"),
        _step(10, "A_total", "Total tower cross-section", "A_active/(1-f_downcomer)",
              f"{active_area:.8g}/(1-{basis.downcomer_fraction:.8g})", total_area, "m²", "User downcomer-area fraction"),
        _step(11, "D_c", "Inside column diameter", "sqrt(4 A_total/pi)",
              f"sqrt(4×{total_area:.8g}/pi)", diameter, "m", "Circular cross-section"),
        _step(12, "H_trays", "Tray-stack height", "max(N_tray-1,0) s",
              f"max({tray_count}-1,0)×{basis.tray_spacing_m:.8g}", tray_stack_height, "m", "User tray spacing; reboiler excluded"),
        _step(13, "H_TT", "Tangent-to-tangent shell height", "H_trays+H_top+H_bottom+H_allow",
              f"{tray_stack_height:.8g}+{basis.top_disengagement_m:.8g}+{basis.bottom_sump_m:.8g}+{basis.shell_allowance_m:.8g}", tangent_height, "m", "Explicit geometric allowances"),
        _step(14, "t_p", "Pressure-only shell thickness", "P_D D/(2 S E-1.2 P_D)",
              f"{p_design_pa:.8g}×{diameter:.8g}/(2×{stress_pa:.8g}×{basis.weld_efficiency:.8g}-1.2×{p_design_pa:.8g})", pressure_thickness * 1000.0, "mm", "Preliminary thin-wall screen; not an ASME design"),
        _step(15, "t", "Selected nominal shell thickness", "max(6 mm, t_p+c_A)",
              f"max(6, {pressure_thickness * 1000.0:.8g}+{basis.corrosion_allowance_mm:.8g})", shell_thickness * 1000.0, "mm", "App minimum plus corrosion allowance"),
        _step(16, "V_steel", "Cylindrical shell steel volume", "pi D H t",
              f"pi×{diameter:.8g}×{tangent_height:.8g}×{shell_thickness:.8g}", shell_steel_volume, "m³", "Cylindrical shell only"),
        _step(17, "m_shell", "Estimated fabricated shell mass", "V_steel rho_steel f_allow",
              f"{shell_steel_volume:.8g}×7850×1.20", shell_mass, "kg", "20% allowance for heads, nozzles, attachments"),
        _step(18, "A_C", "Condenser heat-transfer area", "|Q_C|/(U_C LMTD_C)",
              f"{abs(float(column['Q_C'])):.8g}/({basis.condenser_u_kw_m2_k:.8g}×{basis.condenser_lmtd_k:.8g})", condenser_area, "m²", "User U and LMTD"),
        _step(19, "A_R", "Reboiler heat-transfer area", "|Q_R|/(U_R LMTD_R)",
              f"{abs(float(column['Q_R'])):.8g}/({basis.reboiler_u_kw_m2_k:.8g}×{basis.reboiler_lmtd_k:.8g})", reboiler_area, "m²", "User U and LMTD"),
        _step(20, "I/I_0", "Cost-index ratio", "I_project/I_base",
              f"{basis.project_cost_index:.8g}/{basis.base_cost_index:.8g}", index_ratio, "–", "User-entered indices; same index series required"),
        _step(21, "C_shell,0", "Base shell purchased cost", "120000[max(m,1000)/10000]^0.62",
              f"120000×[max({shell_mass:.8g},1000)/10000]^0.62", shell_cost, "USD at base index", "Illustrative app screening correlation"),
        _step(22, "C_tray,0", "Base tray purchased cost", "7500 N_tray max(D,0.6)^1.55",
              f"7500×{max(tray_count, 1)}×max({diameter:.8g},0.6)^1.55", trays_cost, "USD at base index", "Illustrative app screening correlation"),
        _step(23, "C_C,0", "Base condenser purchased cost", "65000[max(A_C,10)/100]^0.65",
              f"65000×[max({condenser_area:.8g},10)/100]^0.65", condenser_cost, "USD at base index", "Illustrative app screening correlation"),
        _step(24, "C_R,0", "Base reboiler purchased cost", "75000[max(A_R,10)/100]^0.65",
              f"75000×[max({reboiler_area:.8g},10)/100]^0.65", reboiler_cost, "USD at base index", "Illustrative app screening correlation"),
        _step(25, "C_p", "Escalated purchased equipment", "F_M(I/I_0) sum(C_k,0)",
              f"{basis.material_factor:.8g}×{index_ratio:.8g}×({shell_cost:.8g}+{trays_cost:.8g}+{condenser_cost:.8g}+{reboiler_cost:.8g})", purchased, "USD", "Material and cost-index factors"),
        _step(26, "C_inst", "Installed equipment cost", "2.75 C_p",
              f"2.75×{purchased:.8g}", installed, "USD", "Explicit illustrative installation factor"),
        _step(27, "C_scope", "Controls and contingency", "0.25 C_inst",
              f"0.25×{installed:.8g}", controls_and_contingency, "USD", "Explicit illustrative scope allowance"),
        _step(28, "FCI", "Fixed capital investment", "C_inst+C_scope",
              f"{installed:.8g}+{controls_and_contingency:.8g}", fixed_capital, "USD", "Screening total"),
        _step(29, "E_steam", "Annual reboiler energy", "|Q_R| h_op 0.0036",
              f"{abs(float(column['Q_R'])):.8g}×{basis.operating_hours_y:.8g}×0.0036", steam_gj_y, "GJ/y", "1 kWh = 0.0036 GJ"),
        _step(30, "E_cw", "Annual condenser heat removal", "|Q_C| h_op 0.0036",
              f"{abs(float(column['Q_C'])):.8g}×{basis.operating_hours_y:.8g}×0.0036", cooling_gj_y, "GJ/y", "1 kWh = 0.0036 GJ"),
        _step(31, "C_steam", "Annual steam cost", "E_steam p_steam",
              f"{steam_gj_y:.8g}×{basis.steam_usd_gj:.8g}", steam_cost, "USD/y", "User utility tariff"),
        _step(32, "C_cw", "Annual cooling cost", "E_cw p_cw",
              f"{cooling_gj_y:.8g}×{basis.cooling_usd_gj:.8g}", cooling_cost, "USD/y", "User utility tariff"),
        _step(33, "C_maint", "Annual maintenance allowance", "0.03 FCI",
              f"0.03×{fixed_capital:.8g}", maintenance, "USD/y", "Explicit illustrative factor"),
        _step(34, "OPEX", "Total annual operating cost", "C_steam+C_cw+C_maint",
              f"{steam_cost:.8g}+{cooling_cost:.8g}+{maintenance:.8g}", annual_opex, "USD/y", "Excludes labor, feed, waste, electricity, taxes"),
        _step(35, "CRF", "Capital recovery factor", "i(1+i)^n/[(1+i)^n-1]",
              f"{i:.8g}×(1+{i:.8g})^{n}/[(1+{i:.8g})^{n}-1]", crf, "1/y", "User discount rate and project life"),
        _step(36, "C_cap,ann", "Annualized capital", "CRF FCI",
              f"{crf:.8g}×{fixed_capital:.8g}", annualized_capital, "USD/y", "Uniform annual equivalent"),
        _step(37, "TAC", "Total annualized cost", "C_cap,ann+OPEX",
              f"{annualized_capital:.8g}+{annual_opex:.8g}", annualized_capital + annual_opex, "USD/y", "Screening economic objective"),
    ]

    return {
        "basis": asdict(basis),
        "governing_stage": int(governing["stage"]),
        "vapor_mol_s": vapor_mol_s,
        "vapor_volume_m3_s": vapor_volume_m3_s,
        "rho_v_kg_m3": rho_v,
        "rho_l_kg_m3": rho_l,
        "mw_vapor_kg_kmol": mw_vapor_kg_mol * 1000.0,
        "u_flood_m_s": u_flood,
        "u_design_m_s": u_design,
        "active_area_m2": active_area,
        "total_area_m2": total_area,
        "diameter_m": diameter,
        "tangent_height_m": tangent_height,
        "tray_stack_height_m": tray_stack_height,
        "pressure_thickness_mm": pressure_thickness * 1000.0,
        "shell_thickness_mm": shell_thickness * 1000.0,
        "shell_steel_volume_m3": shell_steel_volume,
        "shell_mass_kg": shell_mass,
        "condenser_area_m2": condenser_area,
        "reboiler_area_m2": reboiler_area,
        "purchased_cost_usd": purchased,
        "shell_base_cost_usd": shell_cost,
        "trays_base_cost_usd": trays_cost,
        "condenser_base_cost_usd": condenser_cost,
        "reboiler_base_cost_usd": reboiler_cost,
        "cost_index_ratio": index_ratio,
        "installed_cost_usd": installed,
        "controls_contingency_usd": controls_and_contingency,
        "fixed_capital_usd": fixed_capital,
        "steam_energy_gj_y": steam_gj_y,
        "cooling_energy_gj_y": cooling_gj_y,
        "steam_cost_usd_y": steam_cost,
        "cooling_cost_usd_y": cooling_cost,
        "maintenance_usd_y": maintenance,
        "annual_opex_usd_y": annual_opex,
        "annualized_capital_usd_y": annualized_capital,
        "tac_usd_y": annualized_capital + annual_opex,
        "crf": crf,
        "calculation_steps": calculation_steps,
    }


def build_sizing_reproduction_script(column: dict, basis: SizingBasis) -> str:
    """Return dependency-free Python that reproduces the displayed estimate.

    All stage loads and all user assumptions are embedded as ordinary literals;
    the downloaded file neither imports this application nor hides a correlation.
    """
    stage_rows = [
        {
            "stage": int(s["stage"]),
            "V_mol_s": float(s["V"]),
            "y_IPA": float(s["y"]),
            "x_IPA": float(s["x"]),
            "T_C": float(s["T_C"]),
        }
        for s in column["stages"]
    ]
    return f'''"""Independent reproduction of the Streamlit preliminary sizing/cost estimate.

Generated from one dashboard state.  Standard-library Python only.
This is a transparent Class-4 educational estimate, not vendor hydraulic,
ASME pressure-vessel, exchanger, or definitive cost design.
"""
from math import pi, sqrt

# ---- Simulator outputs passed into equipment sizing ----
STAGES = {stage_rows!r}
P_PA = {float(column['P'])!r}
TRAY_COUNT = {int(column['tray_count'])!r}
Q_C_KW = {float(column['Q_C'])!r}
Q_R_KW = {float(column['Q_R'])!r}

# ---- Molecular/physical constants ----
R = {R_GAS!r}                 # Pa m3 mol-1 K-1
MW_IPA = {MW_IPA!r}           # kg kmol-1
MW_WATER = {MW_WATER!r}       # kg kmol-1
RHO_IPA = 785.0               # kg m-3; preliminary near-ambient value
RHO_WATER = 997.0             # kg m-3; preliminary near-ambient value
RHO_STEEL = 7850.0            # kg m-3

# ---- User-visible sizing and economic assumptions ----
FLOOD_FRACTION = {basis.flood_fraction!r}
CAPACITY_FACTOR_M_S = {basis.capacity_factor_m_s!r}
DOWNCOMER_FRACTION = {basis.downcomer_fraction!r}
TRAY_SPACING_M = {basis.tray_spacing_m!r}
TOP_DISENGAGEMENT_M = {basis.top_disengagement_m!r}
BOTTOM_SUMP_M = {basis.bottom_sump_m!r}
SHELL_ALLOWANCE_M = {basis.shell_allowance_m!r}
DESIGN_PRESSURE_BAR_ABS = {basis.design_pressure_bar_abs!r}
ALLOWABLE_STRESS_MPA = {basis.allowable_stress_mpa!r}
WELD_EFFICIENCY = {basis.weld_efficiency!r}
CORROSION_ALLOWANCE_MM = {basis.corrosion_allowance_mm!r}
CONDENSER_U_KW_M2_K = {basis.condenser_u_kw_m2_k!r}
CONDENSER_LMTD_K = {basis.condenser_lmtd_k!r}
REBOILER_U_KW_M2_K = {basis.reboiler_u_kw_m2_k!r}
REBOILER_LMTD_K = {basis.reboiler_lmtd_k!r}
MATERIAL_FACTOR = {basis.material_factor!r}
PROJECT_COST_INDEX = {basis.project_cost_index!r}
BASE_COST_INDEX = {basis.base_cost_index!r}
OPERATING_HOURS_Y = {basis.operating_hours_y!r}
STEAM_USD_GJ = {basis.steam_usd_gj!r}
COOLING_USD_GJ = {basis.cooling_usd_gj!r}
DISCOUNT_RATE = {basis.discount_rate!r}
PROJECT_LIFE_Y = {basis.project_life_y!r}

# 1. Find the stage with the largest molar vapor load.
g = max(STAGES, key=lambda row: row["V_mol_s"])
n_v = max(g["V_mol_s"], 1e-9)
y = g["y_IPA"]
x = g["x_IPA"]
T = g["T_C"] + 273.15

# 2. Convert molar load to actual volume and calculate phase densities.
mw_v_kg_mol = (y*MW_IPA + (1-y)*MW_WATER)/1000
rho_v = P_PA*mw_v_kg_mol/(R*T)                       # ideal gas, Z=1
mw_l_kg_kmol = x*MW_IPA + (1-x)*MW_WATER
v_l_m3_kmol = x*MW_IPA/RHO_IPA + (1-x)*MW_WATER/RHO_WATER
rho_l = mw_l_kg_kmol/v_l_m3_kmol                     # additive volumes
vapor_volume = n_v*R*T/P_PA

# 3. Preliminary Souders-Brown tray capacity and diameter.
u_flood = CAPACITY_FACTOR_M_S*sqrt((rho_l-rho_v)/rho_v)
u_design = FLOOD_FRACTION*u_flood
active_area = vapor_volume/u_design
total_area = active_area/(1-DOWNCOMER_FRACTION)
diameter = sqrt(4*total_area/pi)

# 4. Height, thin-wall pressure screen, and estimated fabricated shell mass.
tray_stack = max(TRAY_COUNT-1, 0)*TRAY_SPACING_M
tangent_height = tray_stack + TOP_DISENGAGEMENT_M + BOTTOM_SUMP_M + SHELL_ALLOWANCE_M
P_design = DESIGN_PRESSURE_BAR_ABS*1e5
S = ALLOWABLE_STRESS_MPA*1e6
t_pressure = P_design*diameter/(2*S*WELD_EFFICIENCY - 1.2*P_design)
t_shell = max(0.006, t_pressure + CORROSION_ALLOWANCE_MM/1000)
steel_volume = pi*diameter*tangent_height*t_shell
shell_mass = steel_volume*RHO_STEEL*1.20               # heads/nozzles allowance

# 5. Heat-transfer areas. Duties are kW and U is kW m-2 K-1.
condenser_area = abs(Q_C_KW)/(CONDENSER_U_KW_M2_K*CONDENSER_LMTD_K)
reboiler_area = abs(Q_R_KW)/(REBOILER_U_KW_M2_K*REBOILER_LMTD_K)

# 6. Explicit illustrative bare-equipment correlations at the base index.
index_ratio = PROJECT_COST_INDEX/BASE_COST_INDEX
shell_cost_0 = 120_000*(max(shell_mass, 1000)/10_000)**0.62
trays_cost_0 = 7_500*max(TRAY_COUNT, 1)*max(diameter, 0.6)**1.55
condenser_cost_0 = 65_000*(max(condenser_area, 10)/100)**0.65
reboiler_cost_0 = 75_000*(max(reboiler_area, 10)/100)**0.65
purchased = MATERIAL_FACTOR*index_ratio*(
    shell_cost_0 + trays_cost_0 + condenser_cost_0 + reboiler_cost_0
)
installed = 2.75*purchased
controls_contingency = 0.25*installed
fixed_capital = installed + controls_contingency

# 7. Annual utilities, maintenance allowance, and annualized capital.
steam_gj_y = abs(Q_R_KW)*OPERATING_HOURS_Y*0.0036
cooling_gj_y = abs(Q_C_KW)*OPERATING_HOURS_Y*0.0036
steam_cost = steam_gj_y*STEAM_USD_GJ
cooling_cost = cooling_gj_y*COOLING_USD_GJ
maintenance = 0.03*fixed_capital
opex = steam_cost + cooling_cost + maintenance
i, n = DISCOUNT_RATE, PROJECT_LIFE_Y
crf = i*(1+i)**n/((1+i)**n-1) if i else 1/n
annualized_capital = crf*fixed_capital
tac = annualized_capital + opex

results = {{
    "governing_stage": g["stage"], "vapor_mol_s": n_v,
    "vapor_MW_kg_kmol": 1000*mw_v_kg_mol, "rho_v_kg_m3": rho_v,
    "rho_l_kg_m3": rho_l, "vapor_volume_m3_s": vapor_volume,
    "u_flood_m_s": u_flood, "u_design_m_s": u_design,
    "active_area_m2": active_area, "total_area_m2": total_area,
    "diameter_m": diameter, "tray_stack_m": tray_stack,
    "tangent_height_m": tangent_height, "pressure_thickness_mm": 1000*t_pressure,
    "selected_thickness_mm": 1000*t_shell, "shell_mass_kg": shell_mass,
    "condenser_area_m2": condenser_area, "reboiler_area_m2": reboiler_area,
    "shell_base_cost_usd": shell_cost_0, "trays_base_cost_usd": trays_cost_0,
    "condenser_base_cost_usd": condenser_cost_0,
    "reboiler_base_cost_usd": reboiler_cost_0, "purchased_cost_usd": purchased,
    "installed_cost_usd": installed, "controls_contingency_usd": controls_contingency,
    "fixed_capital_usd": fixed_capital, "steam_energy_gj_y": steam_gj_y,
    "cooling_energy_gj_y": cooling_gj_y, "steam_cost_usd_y": steam_cost,
    "cooling_cost_usd_y": cooling_cost, "maintenance_usd_y": maintenance,
    "opex_usd_y": opex, "crf_1_y": crf,
    "annualized_capital_usd_y": annualized_capital, "tac_usd_y": tac,
}}
for name, value in results.items():
    print(f"{{name:34s}} = {{value:.10g}}" if isinstance(value, float) else f"{{name:34s}} = {{value}}")
'''
