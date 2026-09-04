"""Transparent binary IPA/water flash calculations used by the tutorial.

All functions use mole fractions, kelvin, pascal, mol/s, and kJ/mol.  The
algorithms favor bracketed scalar roots and explicit residual checks so they
can be reproduced directly in Python.
"""

import numpy as np
from scipy.optimize import brentq

import src.thermo as th


def rachford_rice(z, k_values):
    """Return vapor fraction for fixed K-values, including single-phase tests."""
    z = np.asarray(z, dtype=float)
    k = np.asarray(k_values, dtype=float)
    if z.shape != k.shape or np.any(z < 0) or not np.isclose(z.sum(), 1.0):
        raise ValueError("z and K must have equal shape and z must sum to one")

    def residual(beta):
        return float(np.sum(z * (k - 1.0) / (1.0 + beta * (k - 1.0))))

    g0, g1 = residual(0.0), residual(1.0)
    if g0 <= 0.0:
        return 0.0
    if g1 >= 0.0:
        return 1.0
    return float(brentq(residual, 0.0, 1.0, xtol=1e-12))


def _phase_compositions(z, k_values, beta):
    """Back-calculate normalized liquid and vapor compositions."""
    z = np.asarray(z, dtype=float)
    k = np.asarray(k_values, dtype=float)
    x = z / (1.0 + beta * (k - 1.0))
    y = k * x
    x /= x.sum()
    y /= y.sum()
    return x, y


def ideal_tp_flash(T, P, z_ipa):
    """Ideal-vapor/ideal-liquid TP flash using Raoult-law K-values."""
    z = np.array([z_ipa, 1.0 - z_ipa], dtype=float)
    k = np.array([th.pvap_ipa(T) / P, th.pvap_water(T) / P], dtype=float)
    beta = rachford_rice(z, k)
    x, y = _phase_compositions(z, k, beta)
    return {"T_K": float(T), "P_Pa": float(P), "beta": beta, "x": x, "y": y, "K": k}


def nonideal_tp_flash(T, P, z_ipa, tolerance=1e-9, max_iterations=300, damping=1.0):
    """NRTL TP flash with a damped activity/composition fixed-point loop."""
    z = np.array([z_ipa, 1.0 - z_ipa], dtype=float)
    x = z.copy()
    beta = 0.0
    for iteration in range(1, max_iterations + 1):
        gamma = np.asarray(th.nrtl_gamma(x[0], T), dtype=float)
        k = gamma * np.array([th.pvap_ipa(T), th.pvap_water(T)]) / P
        beta_new = rachford_rice(z, k)
        x_new, y_new = _phase_compositions(z, k, beta_new)
        error = max(abs(beta_new - beta), float(np.max(abs(x_new - x))))
        beta = beta_new
        x = damping * x_new + (1.0 - damping) * x
        if error < tolerance:
            x, y = _phase_compositions(z, k, beta_new)
            return {
                "T_K": float(T), "P_Pa": float(P), "beta": float(beta_new),
                "x": x, "y": y, "K": k, "gamma": gamma,
                "iterations": iteration, "closure_error": error,
            }
    raise RuntimeError("non-ideal TP flash did not converge")


def bubble_t_fixed_p(x_ipa, P):
    """Bubble temperature and incipient-vapor composition at fixed P and x."""
    T, y_ipa = th.bubble_point(x_ipa, P)
    return {"T_K": float(T), "x_ipa": float(x_ipa), "y_ipa": float(y_ipa), "P_Pa": float(P)}


def dew_t_fixed_p(y_ipa, P):
    """Dew temperature and incipient-liquid composition at fixed P and y."""
    T, x_ipa = th.dew_point(y_ipa, P)
    return {"T_K": float(T), "x_ipa": float(x_ipa), "y_ipa": float(y_ipa), "P_Pa": float(P)}


def tvf_flash(T, z_ipa, beta_spec, pressure_bounds=(1_000.0, 5_000_000.0)):
    """Constant-T flash with specified vapor fraction; solve pressure."""
    if not 0.0 <= beta_spec <= 1.0:
        raise ValueError("beta_spec must be between zero and one")

    def residual(log_pressure):
        pressure = float(np.exp(log_pressure))
        return nonideal_tp_flash(T, pressure, z_ipa)["beta"] - beta_spec

    lo, hi = np.log(pressure_bounds[0]), np.log(pressure_bounds[1])
    grid = np.linspace(lo, hi, 120)
    values = [residual(p) for p in grid]
    bracket = next(
        ((a, b) for a, b, fa, fb in zip(grid[:-1], grid[1:], values[:-1], values[1:]) if fa * fb <= 0),
        None,
    )
    if bracket is None:
        raise ValueError("specified vapor fraction is not bracketed by pressure bounds")
    P = float(np.exp(brentq(residual, *bracket, xtol=1e-11)))
    return nonideal_tp_flash(T, P, z_ipa)


def adiabatic_ph_flash(P, z_ipa, h_feed, temperature_bounds=(270.0, 450.0)):
    """Adiabatic constant-P flash: outer enthalpy root around an NRTL TP flash."""
    def residual(T):
        state = nonideal_tp_flash(T, P, z_ipa)
        beta, x, y = state["beta"], state["x"], state["y"]
        h_liquid = float(th.h_liquid_mix(x[0], T))
        h_vapor = float(th.h_vapor_mix(y[0], T))
        return h_feed - ((1.0 - beta) * h_liquid + beta * h_vapor)

    T = float(brentq(residual, *temperature_bounds, xtol=1e-9))
    state = nonideal_tp_flash(T, P, z_ipa)
    state["h_feed_kJ_mol"] = float(h_feed)
    state["energy_residual_kJ_mol"] = float(residual(T))
    return state
