"""Engineering-unit conversions for UI display; solver storage remains canonical SI.

Conversions are array-aware, so a whole curve converts in one expression
rather than a comprehension over its points.  The solver never sees these
units: everything inside ``src/`` is mol/s, Pa, K, kJ/mol and metres.
"""

from dataclasses import dataclass

import numpy as np

#: Molar masses used by the mole-to-weight composition bases [g/mol].
MW_IPA = 60.096
MW_WATER = 18.015


@dataclass(frozen=True)
class Conversion:
    scale: float
    offset: float = 0.0

    def from_canonical(self, value: float) -> float:
        return value * self.scale + self.offset

    def to_canonical(self, value: float) -> float:
        return (value - self.offset) / self.scale


UNITS = {
    "flow": {
        "kgmol/h": Conversion(3.6), "lbmol/h": Conversion(7.93664144), "mol/h": Conversion(3600.0),
        "mol/s": Conversion(1.0), "kgmol/min": Conversion(0.06), "kgmol/s": Conversion(0.001),
        "lbmol/min": Conversion(0.132277357),
    },
    "pressure": {
        "kPa(a)": Conversion(1e-3), "bar(a)": Conversion(1e-5), "Pa(a)": Conversion(1.0),
        "MPa(a)": Conversion(1e-6), "atm(a)": Conversion(1 / 101325.0),
        "psia": Conversion(1 / 6894.757293), "mmHg(a)": Conversion(1 / 133.322368),
        "mmH₂O(a)": Conversion(0.101971621), "kgf/cm²(a)": Conversion(1 / 98066.5),
    },
    "stress": {"MPa": Conversion(1e-6), "bar": Conversion(1e-5), "ksi": Conversion(1 / 6_894_757.293)},
    "duty": {
        "kW": Conversion(1.0), "MW": Conversion(1e-3), "kJ/h": Conversion(3600.0),
        "kcal/h": Conversion(859.8452279), "Gcal/h": Conversion(0.000859845228),
        "Btu/h": Conversion(3412.141633), "MMBtu/h": Conversion(0.003412141633),
        "hp": Conversion(1.341022089),
    },
    "temperature": {
        "°C": Conversion(1.0), "K": Conversion(1.0, 273.15), "°F": Conversion(1.8, 32.0),
        "°R": Conversion(1.8, 491.67),
    },
    "delta_temperature": {
        "K": Conversion(1.0), "°C difference": Conversion(1.0), "°F difference": Conversion(1.8),
    },
    "length": {
        "m": Conversion(1.0), "cm": Conversion(100.0), "mm": Conversion(1000.0),
        "ft": Conversion(3.280839895), "in": Conversion(39.37007874),
    },
    "area": {"m²": Conversion(1.0), "cm²": Conversion(10000.0), "ft²": Conversion(10.76391042), "in²": Conversion(1550.0031)},
    "velocity": {"m/s": Conversion(1.0), "cm/s": Conversion(100.0), "ft/s": Conversion(3.280839895), "ft/min": Conversion(196.8503937)},
    "density": {"kg/m³": Conversion(1.0), "g/cm³": Conversion(0.001), "lb/ft³": Conversion(0.0624279606)},
    "mass": {"kg": Conversion(1.0), "g": Conversion(1000.0), "metric tonne": Conversion(1e-3), "lb": Conversion(2.204622622)},
    "enthalpy": {
        "kJ/kgmol": Conversion(1000.0), "kcal/kgmol": Conversion(239.005736),
        "Btu/lbmol": Conversion(429.922614), "kJ/mol": Conversion(1.0),
        "J/mol": Conversion(1000.0), "kcal/mol": Conversion(0.239005736),
    },
    "heat_transfer_coefficient": {
        "kW/m²/K": Conversion(1.0), "W/m²/K": Conversion(1000.0),
        "kcal/h/m²/°C": Conversion(859.8452279), "Btu/h/ft²/°F": Conversion(176.1101838),
    },
    "energy": {"GJ/y": Conversion(1.0), "MMBtu/y": Conversion(0.947817121)},
    "energy_price": {"USD/GJ": Conversion(1.0), "USD/MMBtu": Conversion(1.055055853)},
    "money": {"MUSD": Conversion(1e-6), "kUSD": Conversion(1e-3), "USD": Conversion(1.0)},
    "money_rate": {"MUSD/y": Conversion(1e-6), "kUSD/y": Conversion(1e-3), "USD/y": Conversion(1.0)},
    "hours_year": {"h/y": Conversion(1.0), "operating days/y": Conversion(1 / 24.0)},
    "years": {"years": Conversion(1.0)},
    "fraction": {"fraction": Conversion(1.0), "%": Conversion(100.0)},
    "composition": {
        "mole fraction": Conversion(1.0), "mole %": Conversion(100.0),
        "weight fraction": Conversion(1.0), "weight %": Conversion(100.0),
    },
    "dimensionless": {"dimensionless": Conversion(1.0)},
    "ratio": {"mol/mol": Conversion(1.0)},
    "count_stage": {"equilibrium stages": Conversion(1.0)},
    "count_tray": {"trays": Conversion(1.0)},
    "cost_index": {"index points": Conversion(1.0)},
}


def unit_options(quantity: str) -> list[str]:
    return list(UNITS[quantity])


def from_canonical(value, quantity: str, unit: str):
    """Convert a canonical SI value -- scalar or array -- to display units.

    Accepting arrays lets callers convert a whole curve in one expression
    (``from_canonical(vle["x"], "composition", unit)``) instead of looping
    over points.  A scalar in returns a scalar out, so existing formatting
    code is unaffected.
    """
    value = np.asarray(value, dtype=float)
    if quantity == "composition" and unit in {"weight fraction", "weight %"}:
        mass_ipa = value * MW_IPA
        weight = mass_ipa / (mass_ipa + (1.0 - value) * MW_WATER)
        converted = weight * (100.0 if unit == "weight %" else 1.0)
    else:
        converted = UNITS[quantity][unit].from_canonical(value)
    return converted.item() if converted.ndim == 0 else converted


def to_canonical(value, quantity: str, unit: str):
    """Convert a display value -- scalar or array -- back to canonical SI."""
    value = np.asarray(value, dtype=float)
    if quantity == "composition" and unit in {"weight fraction", "weight %"}:
        weight = value / (100.0 if unit == "weight %" else 1.0)
        moles_ipa = weight / MW_IPA
        converted = moles_ipa / (moles_ipa + (1.0 - weight) / MW_WATER)
    else:
        converted = UNITS[quantity][unit].to_canonical(value)
    return converted.item() if converted.ndim == 0 else converted


def default_unit(quantity: str) -> str:
    return unit_options(quantity)[0]


def display_step(step: float, quantity: str, unit: str, around: float = 0.5) -> float:
    """Convert a canonical increment, including nonlinear composition bases."""
    return abs(from_canonical(around + step, quantity, unit) - from_canonical(around, quantity, unit))
