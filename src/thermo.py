"""Thermodynamic models and physical properties for the isopropanol/water system.

Reading this module as mathematics
----------------------------------
Every routine here is written so the code is recognisable as the equation it
implements.  Two conventions make that possible:

* **The component index is the last axis.**  A composition is ``x[..., i]`` and
  an interaction matrix is ``tau[..., i, j]``.  Any leading axes are grid axes
  (a temperature range, a composition sweep), so a single call evaluates the
  model at every point of a grid at once.
* **Summations are contractions.**  ``np.einsum`` subscripts are the summation
  indices of the printed equation, so ``sum_k x_k G_ki`` is written
  ``einsum("...k,...ki->...i", x, G)`` and can be checked term by term.

The only ``for`` loops that remain are *iteration schemes* (interval halving,
fixed-point updates) -- never bookkeeping over grid points.

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

#: Component order used by every array in this module: index 0 = IPA, 1 = water.
COMPONENTS = ("isopropanol", "water")


# ---------------------------------------------------------------------------
# Pure-component correlations (DIPPR forms; all naturally elementwise)
# ---------------------------------------------------------------------------

def pvap_ipa(T):
    """DIPPR-101 vapour pressure, ln P = A + B/T + C ln T + D T^E  [Pa]."""
    T = np.asarray(T)
    return np.exp(PVAP_IPA['A'] + PVAP_IPA['B'] / T + PVAP_IPA['C'] * np.log(T)
                  + PVAP_IPA['D'] * (T ** PVAP_IPA['E']))


def pvap_water(T):
    """DIPPR-101 vapour pressure, ln P = A + B/T + C ln T + D T^E  [Pa]."""
    T = np.asarray(T)
    return np.exp(PVAP_WATER['A'] + PVAP_WATER['B'] / T + PVAP_WATER['C'] * np.log(T)
                  + PVAP_WATER['D'] * (T ** PVAP_WATER['E']))


def t_boil_ipa(P=101325.0):
    """Pure-IPA boiling temperature at pressure ``P`` [K]."""
    return brentq(lambda T: pvap_ipa(T) - P, 280.0, 500.0)


def t_boil_water(P=101325.0):
    """Pure-water boiling temperature at pressure ``P`` [K]."""
    return brentq(lambda T: pvap_water(T) - P, 280.0, 500.0)


def hvap_ipa(T):
    """DIPPR-106 heat of vaporisation  [kJ/mol]."""
    T = np.asarray(T)
    Tr = T / TC_IPA
    exponent = HVAP_IPA['B'] + HVAP_IPA['C'] * Tr + HVAP_IPA['D'] * Tr**2 + HVAP_IPA['E'] * Tr**3
    return HVAP_IPA['A'] * (1.0 - Tr) ** exponent / 1.0e6


def hvap_water(T):
    """DIPPR-106 heat of vaporisation  [kJ/mol]."""
    T = np.asarray(T)
    Tr = T / TC_WATER
    exponent = HVAP_WATER['B'] + HVAP_WATER['C'] * Tr + HVAP_WATER['D'] * Tr**2 + HVAP_WATER['E'] * Tr**3
    return HVAP_WATER['A'] * (1.0 - Tr) ** exponent / 1.0e6


def _int_cpl(p_dict, T):
    """Antiderivative of the DIPPR-100 liquid heat-capacity polynomial."""
    A, B, C, D, E = p_dict['A'], p_dict['B'], p_dict['C'], p_dict['D'], p_dict['E']
    return A * T + (B / 2.0) * T**2 + (C / 3.0) * T**3 + (D / 4.0) * T**4 + (E / 5.0) * T**5


def h_liquid_pure_ipa(T):
    """Pure-IPA liquid enthalpy, integral of Cp,L from T_REF to T  [kJ/mol]."""
    T = np.asarray(T)
    return (_int_cpl(CPL_IPA, T) - _int_cpl(CPL_IPA, T_REF)) / 1.0e6


def h_liquid_pure_water(T):
    """Pure-water liquid enthalpy, integral of Cp,L from T_REF to T  [kJ/mol]."""
    T = np.asarray(T)
    return (_int_cpl(CPL_WATER, T) - _int_cpl(CPL_WATER, T_REF)) / 1.0e6


# ---------------------------------------------------------------------------
# NRTL activity coefficients, written as the general N-component equation
# ---------------------------------------------------------------------------

def nrtl_ln_gamma(x, tau, G):
    r"""General N-component NRTL activity coefficients.

    .. math::

        \ln\gamma_i=\underbrace{\frac{\sum_j x_j\tau_{ji}G_{ji}}
                                     {\sum_k x_k G_{ki}}}_{C_i/S_i}
        +\sum_j\frac{x_j G_{ij}}{\sum_k x_k G_{kj}}
         \left(\tau_{ij}-\frac{\sum_m x_m \tau_{mj}G_{mj}}{\sum_k x_k G_{kj}}\right)

    Both terms share the denominator ``S`` and the ratio ``r = C/S``, which is
    why the second term reuses exactly the same two arrays.  Each line below
    is one labelled group of the equation above.

    Parameters
    ----------
    x : array_like, shape (..., N)
        Mole fractions; component index last.
    tau, G : array_like, shape (..., N, N)
        NRTL interaction matrices, ``tau[..., i, j]`` = tau_ij.

    Returns
    -------
    ndarray, shape (..., N)
        Natural logarithm of every component's activity coefficient.
    """
    S = np.einsum("...k,...ki->...i", x, G)          # S_i = sum_k x_k G_ki
    C = np.einsum("...m,...mj->...j", x, tau * G)    # C_j = sum_m x_m tau_mj G_mj
    r = C / S                                        # the ratio common to both terms
    first = r                                        # C_i / S_i
    second = np.einsum("...ij,...j->...i", G * (tau - r[..., None, :]), x / S)
    return first + second


def nrtl_matrices(T):
    """Binary IPA(0)/water(1) NRTL matrices at temperature ``T``.

    ``tau_ij = B_ij / T`` and ``G_ij = exp(-alpha_ij tau_ij)``.  The diagonal
    is zero by definition, so ``G_ii = 1``.  ``T`` may be complex, which is
    what lets :func:`excess_enthalpy` take an exact temperature derivative.
    """
    T = np.asarray(T)
    tau = np.zeros(T.shape + (2, 2), dtype=T.dtype)
    tau[..., 0, 1] = NRTL_B12 / T
    tau[..., 1, 0] = NRTL_B21 / T
    return tau, np.exp(-NRTL_ALPHA * tau)


def _binary_composition(x1, shape):
    """Stack a binary IPA mole fraction into a ``(..., 2)`` composition array."""
    x1 = np.broadcast_to(np.asarray(x1, dtype=float), shape)
    return np.stack([x1, 1.0 - x1], axis=-1)


def nrtl_gamma(x1, T):
    """Binary activity coefficients ``(gamma_IPA, gamma_water)``.

    A thin wrapper over the general :func:`nrtl_ln_gamma`: the binary case is
    simply ``tau`` being 2x2, not a separate algebraic special case.
    """
    x1 = np.clip(np.asarray(x1, dtype=float), 1e-15, 1.0 - 1e-15)
    shape = np.broadcast_shapes(x1.shape, np.asarray(T).shape)
    tau, G = nrtl_matrices(np.broadcast_to(np.asarray(T, dtype=float), shape))
    gamma = np.exp(nrtl_ln_gamma(_binary_composition(x1, shape), tau, G))
    return gamma[..., 0], gamma[..., 1]


def excess_enthalpy(x1, T, _step=1e-30):
    r"""Excess enthalpy from the Gibbs-Helmholtz relation  [kJ/mol].

    .. math::

        h^E=-RT^2\sum_i x_i
            \left(\frac{\partial\ln\gamma_i}{\partial T}\right)_{P,\mathbf{x}}

    The derivative is taken by the *complex-step* method: evaluating
    :func:`nrtl_ln_gamma` at ``T + ih`` and dividing the imaginary part by
    ``h`` gives the exact derivative with no subtractive cancellation.  The
    code therefore states Gibbs-Helmholtz directly instead of a
    hand-differentiated rearrangement of it.

    This requires the NRTL chain to stay analytic in ``T``: no ``abs``,
    ``clip`` or comparison may touch the complex temperature.
    """
    x1 = np.clip(np.asarray(x1, dtype=float), 0.0, 1.0)
    T = np.asarray(T, dtype=float)
    shape = np.broadcast_shapes(x1.shape, T.shape)
    T = np.broadcast_to(T, shape)
    x = _binary_composition(x1, shape)

    tau, G = nrtl_matrices(T + 1j * _step)
    dln_gamma_dT = nrtl_ln_gamma(x, tau, G).imag / _step
    return -R_GAS * T**2 * np.sum(x * dln_gamma_dT, axis=-1) / 1000.0


# ---------------------------------------------------------------------------
# Mixture enthalpies on a common reference (pure saturated liquid at T_REF)
# ---------------------------------------------------------------------------

def h_liquid_mix(x1, T, include_heat_of_mixing=True):
    """Saturated-liquid molar enthalpy, ``h = sum_i x_i h_i(T) + h^E``  [kJ/mol]."""
    x1 = np.clip(np.asarray(x1, dtype=float), 0.0, 1.0)
    x2 = 1.0 - x1
    h_pure = x1 * h_liquid_pure_ipa(T) + x2 * h_liquid_pure_water(T)
    if include_heat_of_mixing:
        return h_pure + excess_enthalpy(x1, T)
    return h_pure


def h_vapor_mix(y1, T):
    """Saturated-vapour molar enthalpy, ``H = sum_i y_i [h_i(T) + Hvap_i(T)]``  [kJ/mol]."""
    y1 = np.clip(np.asarray(y1, dtype=float), 0.0, 1.0)
    y2 = 1.0 - y1
    h_v1 = h_liquid_pure_ipa(T) + hvap_ipa(T)
    h_v2 = h_liquid_pure_water(T) + hvap_water(T)
    return y1 * h_v1 + y2 * h_v2


# ---------------------------------------------------------------------------
# Phase equilibrium
# ---------------------------------------------------------------------------

def bubble_residual(x1, T, P):
    r"""Bubble-point residual.

    .. math:: r(T)=\sum_i x_i\gamma_i(T,\mathbf{x})P_i^{sat}(T)-P

    Modified Raoult's law with ideal vapour; the root in ``T`` is the bubble
    temperature.  ``r`` increases monotonically with ``T`` over the physical
    range, which is what makes bracketed halving safe.
    """
    g1, g2 = nrtl_gamma(x1, T)
    return x1 * g1 * pvap_ipa(T) + (1.0 - x1) * g2 * pvap_water(T) - P


def _temperature_bracket(P):
    """A bracket guaranteed to contain every binary bubble temperature at ``P``.

    The minimum-boiling azeotrope sits *below* both pure boiling points, hence
    the generous lower margin.
    """
    t_ipa, t_water = t_boil_ipa(P), t_boil_water(P)
    return min(t_ipa, t_water) - 15.0, max(t_ipa, t_water) + 5.0


#: 90 K / 2**60 is about 1e-16 K, i.e. exact to double precision.
_BUBBLE_HALVINGS = 60


def bubble_point_curve(x1, P=101325.0, halvings=_BUBBLE_HALVINGS):
    """Bubble temperature and equilibrium vapour for a whole array of ``x`` at once.

    The composition loop disappears; the loop that remains is interval
    halving, which *is* the numerical method.  Every iteration evaluates the
    residual at every composition simultaneously.

    Returns
    -------
    (T, y) : tuple of ndarray
        Bubble temperature [K] and equilibrium IPA vapour mole fraction.
    """
    x1 = np.clip(np.asarray(x1, dtype=float), 0.0, 1.0)
    low, high = _temperature_bracket(P)
    lo = np.full(x1.shape, low)
    hi = np.full(x1.shape, high)
    for _ in range(halvings):
        mid = 0.5 * (lo + hi)
        below = bubble_residual(x1, mid, P) < 0.0    # root lies above mid
        lo = np.where(below, mid, lo)
        hi = np.where(below, hi, mid)
    T = 0.5 * (lo + hi)
    g1, _ = nrtl_gamma(x1, T)
    y = np.clip(x1 * g1 * pvap_ipa(T) / P, 0.0, 1.0)
    return T, y


def bubble_point(x1, P=101325.0):
    """Scalar bubble point, used by the stage-to-stage recurrences.

    Solves the *same* residual as :func:`bubble_point_curve`, but with a
    scalar bracketing solver.  Interval halving is the right method when the
    whole composition grid is solved at once (every iteration does useful work
    at every point); Brent's method is the right method for a single root,
    where superlinear convergence reaches machine precision in far fewer
    residual evaluations.  Matching the solver to the shape of the problem is
    the reason both entry points exist.

    Returns ``(T_bubble_K, y_IPA)``.  Pure components are returned exactly
    rather than through the mixture root.
    """
    x1 = float(np.clip(x1, 0.0, 1.0))
    if x1 <= 1e-12:
        return t_boil_water(P), 0.0
    if x1 >= 1.0 - 1e-12:
        return t_boil_ipa(P), 1.0
    low, high = _temperature_bracket(P)
    T = brentq(lambda t: float(bubble_residual(x1, t, P)), low, high)
    g1, _ = nrtl_gamma(x1, T)
    return T, float(np.clip(x1 * g1 * pvap_ipa(T) / P, 0.0, 1.0))


_AZEOTROPE_CACHE: dict[float, tuple[float, float]] = {}


def find_azeotrope(P=101325.0):
    """Composition and temperature where ``y = x`` (minimum-boiling azeotrope).

    Cached per pressure.  This is a root-find over a root-find, and without
    the cache it is re-solved on every single dew-point evaluation.
    """
    key = float(P)
    if key not in _AZEOTROPE_CACHE:
        x_azeo = brentq(lambda x: bubble_point(x, key)[1] - x, 0.45, 0.85)
        T_azeo, _ = bubble_point(x_azeo, key)
        _AZEOTROPE_CACHE[key] = (float(x_azeo), float(T_azeo))
    return _AZEOTROPE_CACHE[key]


#: Resolution of the cached y(x) table used to bracket dew-point inversions.
_INVERSION_GRID = 512

_INVERSION_CACHE: dict[float, tuple[np.ndarray, np.ndarray]] = {}


def _inversion_table(P):
    """Cached ``y(x)`` table at pressure ``P``, built with one vectorised solve.

    Inverting ``y(x)`` is a scalar root-find, but a *good bracket* costs
    nothing once the whole curve is available as an array.  Bracketing each
    inversion to one grid interval roughly halves the iterations Brent's
    method needs, and the array solve that builds the table is cheaper than
    the scalar calls it saves.
    """
    key = float(P)
    if key not in _INVERSION_CACHE:
        x = np.linspace(0.0, 1.0, _INVERSION_GRID)
        _, y = bubble_point_curve(x, key)
        _INVERSION_CACHE[key] = (x, y)
    return _INVERSION_CACHE[key]


def _bracket_from_table(y1, P, low, high):
    """Narrow ``[low, high]`` to the tabulated interval containing ``y(x) = y1``."""
    x_tab, y_tab = _inversion_table(P)
    inside = (x_tab >= low) & (x_tab <= high)
    x_tab, y_tab = x_tab[inside], y_tab[inside]
    crossings = np.nonzero(np.diff(np.sign(y_tab - y1)))[0]
    if crossings.size == 0:
        return low, high
    i = crossings[0]
    return float(x_tab[i]), float(x_tab[i + 1])


def dew_point(y1, P=101325.0):
    """Dew temperature and incipient-liquid composition at fixed ``P``.

    Inverts ``y(x)``.  Because that curve is folded at the azeotrope the
    inversion is branch-dependent, so the azeotropic composition splits the
    search interval.  Returns ``(T_dew_K, x_IPA)``.
    """
    y1 = float(np.clip(y1, 0.0, 1.0))
    if y1 <= 1e-9:
        return t_boil_water(P), 0.0
    if y1 >= 1.0 - 1e-9:
        return t_boil_ipa(P), 1.0
    x_azeo, T_azeo = find_azeotrope(P)
    if abs(y1 - x_azeo) < 1e-6:
        return T_azeo, x_azeo
    low, high = (0.0, x_azeo) if y1 < x_azeo else (x_azeo, 1.0)
    low, high = _bracket_from_table(y1, P, low, high)
    x_sol = brentq(lambda x: bubble_point(x, P)[1] - y1, low, high)
    T_sol, _ = bubble_point(x_sol, P)
    return T_sol, float(x_sol)


def get_vle_curves(P=101325.0, n_points=201):
    """The complete constant-pressure phase envelope as parallel arrays.

    One vectorised bubble-point solve produces the whole diagram; the two
    enthalpy curves then follow as elementwise expressions.
    """
    x = np.linspace(0.0, 1.0, n_points)
    T_bubble, y = bubble_point_curve(x, P)
    x_azeo, T_azeo = find_azeotrope(P)
    return {
        'x': x,
        'T_bubble_K': T_bubble,
        'T_bubble_C': T_bubble - 273.15,
        'y': y,
        'h_L': h_liquid_mix(x, T_bubble),
        'H_V': h_vapor_mix(y, T_bubble),
        'x_azeo': x_azeo,
        'T_azeo_K': T_azeo,
        'T_azeo_C': T_azeo - 273.15,
    }


def calculate_feed_state(z_F, P=101325.0, T_F=None, q=None):
    """Feed enthalpy and thermal quality, specified either by ``q`` or by ``T_F``.

    ``q`` is the liquid fraction after an isenthalpic flash at column
    pressure, so ``h_F = q h_L,sat + (1-q) H_V,sat`` interpolates between the
    saturated states at the feed composition -- and extrapolates beyond them
    for subcooled (``q > 1``) or superheated (``q < 0``) feeds.
    """
    T_bubble_F, _ = bubble_point(z_F, P)
    h_L_sat = float(h_liquid_mix(z_F, T_bubble_F))
    H_V_sat = float(h_vapor_mix(z_F, T_bubble_F))

    if q is None and T_F is None:
        q = 1.0

    if q is not None:
        q_val = float(q)
        h_F = q_val * h_L_sat + (1.0 - q_val) * H_V_sat
        if q_val >= 1.0:
            # Subcooled: back out the sensible offset with a leading-order Cp.
            cp = z_F * (CPL_IPA['A'] / 1e6) + (1.0 - z_F) * (CPL_WATER['A'] / 1e6)
            T_feed = T_bubble_F + (h_F - h_L_sat) / cp
        else:
            T_feed = T_bubble_F
    else:
        T_feed = float(T_F)
        if T_feed <= T_bubble_F:
            h_F = float(h_liquid_mix(z_F, T_feed))
            q_val = 1.0 + (h_L_sat - h_F) / (H_V_sat - h_L_sat)
        else:
            h_F = float(h_vapor_mix(z_F, T_feed))
            q_val = (H_V_sat - h_F) / (H_V_sat - h_L_sat)

    return {
        'q': float(q_val),
        'h_F': float(h_F),
        'T_F_K': T_feed,
        'T_F_C': T_feed - 273.15,
        'T_bubble_K': T_bubble_F,
        'h_L_sat': h_L_sat,
        'H_V_sat': H_V_sat,
    }


generate_vle_curves = get_vle_curves
