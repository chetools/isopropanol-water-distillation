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
    """Ideal volume-mixing estimate at near-ambient conditions, kg/m3."""
    return 1.0 / (x_ipa / 785.0 + (1.0 - x_ipa) / 997.0)


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
    shell_mass = pi * diameter * tangent_height * shell_thickness * 7850.0 * 1.20

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

    return {
        "basis": asdict(basis),
        "governing_stage": int(governing["stage"]),
        "vapor_mol_s": vapor_mol_s,
        "vapor_volume_m3_s": vapor_volume_m3_s,
        "rho_v_kg_m3": rho_v,
        "rho_l_kg_m3": rho_l,
        "u_flood_m_s": u_flood,
        "u_design_m_s": u_design,
        "active_area_m2": active_area,
        "total_area_m2": total_area,
        "diameter_m": diameter,
        "tangent_height_m": tangent_height,
        "shell_thickness_mm": shell_thickness * 1000.0,
        "shell_mass_kg": shell_mass,
        "condenser_area_m2": condenser_area,
        "reboiler_area_m2": reboiler_area,
        "purchased_cost_usd": purchased,
        "fixed_capital_usd": fixed_capital,
        "steam_cost_usd_y": steam_cost,
        "cooling_cost_usd_y": cooling_cost,
        "maintenance_usd_y": maintenance,
        "annual_opex_usd_y": annual_opex,
        "annualized_capital_usd_y": annualized_capital,
        "tac_usd_y": annualized_capital + annual_opex,
        "crf": crf,
    }
