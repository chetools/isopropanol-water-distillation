"""Engineering-unit conversions for UI display; solver storage remains canonical SI."""

from dataclasses import dataclass


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
        "mol/s": Conversion(1.0), "kmol/h": Conversion(3.6), "lbmol/h": Conversion(7.93664144),
    },
    "pressure": {
        "kPa(a)": Conversion(1e-3), "bar(a)": Conversion(1e-5), "Pa(a)": Conversion(1.0),
        "atm(a)": Conversion(1 / 101325.0), "psia": Conversion(1 / 6894.757293),
    },
    "stress": {"MPa": Conversion(1e-6), "bar": Conversion(1e-5), "ksi": Conversion(1 / 6_894_757.293)},
    "duty": {
        "kW": Conversion(1.0), "MW": Conversion(1e-3), "kBtu/h": Conversion(3.412141633),
        "MMBtu/h": Conversion(0.003412141633),
    },
    "temperature": {
        "°C": Conversion(1.0), "K": Conversion(1.0, 273.15), "°F": Conversion(1.8, 32.0),
    },
    "delta_temperature": {
        "K": Conversion(1.0), "°C difference": Conversion(1.0), "°F difference": Conversion(1.8),
    },
    "length": {
        "m": Conversion(1.0), "mm": Conversion(1000.0), "ft": Conversion(3.280839895), "in": Conversion(39.37007874),
    },
    "area": {"m²": Conversion(1.0), "ft²": Conversion(10.76391042)},
    "velocity": {"m/s": Conversion(1.0), "ft/s": Conversion(3.280839895), "ft/min": Conversion(196.8503937)},
    "density": {"kg/m³": Conversion(1.0), "lb/ft³": Conversion(0.0624279606)},
    "mass": {"kg": Conversion(1.0), "metric tonne": Conversion(1e-3), "lb": Conversion(2.204622622)},
    "enthalpy": {"kJ/mol": Conversion(1.0), "kJ/kmol": Conversion(1000.0), "Btu/lbmol": Conversion(429.922614)},
    "heat_transfer_coefficient": {
        "kW/m²/K": Conversion(1.0), "W/m²/K": Conversion(1000.0), "Btu/h/ft²/°F": Conversion(176.1101838),
    },
    "energy": {"GJ/y": Conversion(1.0), "MMBtu/y": Conversion(0.947817121)},
    "energy_price": {"USD/GJ": Conversion(1.0), "USD/MMBtu": Conversion(1.055055853)},
    "money": {"MUSD": Conversion(1e-6), "kUSD": Conversion(1e-3), "USD": Conversion(1.0)},
    "money_rate": {"MUSD/y": Conversion(1e-6), "kUSD/y": Conversion(1e-3), "USD/y": Conversion(1.0)},
    "hours_year": {"h/y": Conversion(1.0), "operating days/y": Conversion(1 / 24.0)},
    "years": {"years": Conversion(1.0)},
    "fraction": {"fraction": Conversion(1.0), "%": Conversion(100.0)},
    "composition": {"mole fraction": Conversion(1.0), "mol%": Conversion(100.0)},
    "dimensionless": {"dimensionless": Conversion(1.0)},
    "ratio": {"mol/mol": Conversion(1.0)},
    "count_stage": {"equilibrium stages": Conversion(1.0)},
    "count_tray": {"trays": Conversion(1.0)},
    "cost_index": {"index points": Conversion(1.0)},
}


def unit_options(quantity: str) -> list[str]:
    return list(UNITS[quantity])


def from_canonical(value: float, quantity: str, unit: str) -> float:
    return UNITS[quantity][unit].from_canonical(float(value))


def to_canonical(value: float, quantity: str, unit: str) -> float:
    return UNITS[quantity][unit].to_canonical(float(value))


def default_unit(quantity: str) -> str:
    return unit_options(quantity)[0]
