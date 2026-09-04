"""Distillation Column Algorithms: Design (Ponchon-Savarit) and Rating (MESH).
Implements exact Ponchon-Savarit graphical stage stepping, minimum reflux,
minimum stages, non-equimolar internal flow calculations, subcooling,
Murphree stage efficiency, and McCabe-Thiele operating lines.
"""

import numpy as np
from scipy.optimize import brentq
import src.thermo as th

#: Composition samples used to locate the limiting (pinching) tie line.
_PINCH_SAMPLES = 150


def calc_min_reflux(x_D, x_B, z_F, P, h_F, subcooling_dT=0.0):
    r"""Minimum reflux ratio from the limiting tie line, as one array expression.

    At minimum reflux some tie line, extended, passes through the rectifying
    difference point.  Extending the tie line through :math:`(x, h_L)` and
    :math:`(y, H_V)` to the distillate composition gives the intercept

    .. math:: Q'_{int}(x)=h_L+\frac{H_V-h_L}{y-x}\,(x_D-x)

    and the *highest* such intercept is the limiting one, because any lower
    difference point would put a tie line on the wrong side of the operating
    line.  The reflux ratio then follows from the definition of the difference
    point, :math:`R=(Q'_D-H_{V1})/(H_{V1}-h_{reflux})`.

    Sampling every candidate composition at once turns the search into the
    formula above evaluated on an array, followed by one maximum.
    """
    T_D, _ = th.bubble_point(x_D, P)
    h_D = th.h_liquid_mix(x_D, T_D)
    h_reflux = th.h_liquid_mix(x_D, T_D - subcooling_dT)
    T_V1, _ = th.dew_point(x_D, P)
    H_V1 = th.h_vapor_mix(x_D, T_V1)

    x_azeo, _ = th.find_azeotrope(P)
    x = np.linspace(max(0.01, x_B), min(x_azeo - 0.002, x_D - 0.005), _PINCH_SAMPLES)
    T_b, y = th.bubble_point_curve(x, P)                     # one solve, every sample
    h_L = th.h_liquid_mix(x, T_b)
    H_V = th.h_vapor_mix(y, T_b)

    tie_slope = np.where(np.abs(y - x) < 1e-5, np.nan, y - x)
    Q_int = h_L + ((H_V - h_L) / tie_slope) * (x_D - x)      # the equation above
    Q_prime_D_min = float(np.nanmax(Q_int)) if np.any(np.isfinite(Q_int)) else float(H_V1 + 10.0)

    denom = H_V1 - h_reflux
    if denom <= 0:
        denom = H_V1 - h_D
    return float(max(0.05, (Q_prime_D_min - H_V1) / denom)), Q_prime_D_min

def calc_min_stages(x_D, x_B, P):
    x_curr = x_D
    stages = 0
    while x_curr > x_B and stages < 100:
        _, x_next = th.dew_point(x_curr, P)
        stages += 1
        x_curr = x_next
    return stages


def _dew_state(y, P, approx):
    """Dew temperature, incipient liquid composition, and vapour enthalpy."""
    if approx:
        return th.dew_envelope(y, P)
    T, x = th.dew_point(y, P)
    return T, x, float(th.h_vapor_mix(y, T))


def _bubble_state(x, P, approx):
    """Bubble temperature and liquid enthalpy."""
    if approx:
        T, _y, h = th.bubble_envelope(x, P)
        return T, h
    T, _ = th.bubble_point(x, P)
    return T, float(th.h_liquid_mix(x, T))


def _should_switch_to_stripping(section, n, x_n, z_F, feed_stage_spec):
    """Whether stage ``n`` is the first stripping (feed) stage.

    ``feed_stage_spec is None`` is the textbook construction: switch where the
    liquid composition crosses the feed line.  An integer locks the switch at
    that tray, which is the existing-nozzle (off-optimal) case.
    """
    if section != 'Rectifying':
        return False
    if feed_stage_spec is None:
        return x_n <= z_F or (n >= 2 and x_n < (z_F + 0.02))
    return n == int(feed_stage_spec)


def _ponchon_stage_loop(
    z_F, x_D, x_B, D, B, Q_prime_D, Q_prime_B, V_top, L_reflux,
    murphree_eff, P, approx_vle, record_construction, feed_stage_spec=None,
):
    """Stage-to-stage Ponchon–Savarit recurrence.

    The loop itself cannot be vectorised: each stage's liquid is the previous
    stage's operating-ray root.  ``approx_vle`` only swaps the thermo inside
    each step (interpolated envelope vs scalar root-find).
    """
    stages = []
    construction_lines = []
    y_curr = x_D
    x_prev = x_D
    section = 'Rectifying'
    feed_stage = int(feed_stage_spec) if feed_stage_spec is not None else 1

    for n in range(1, 101):
        T_dew_n, x_eq, H_Vn = _dew_state(y_curr, P, approx_vle)

        # Apply Murphree stage efficiency
        x_n = float(np.clip(x_prev - murphree_eff * (x_prev - x_eq), 1e-5, 0.999))

        _T_bubble_n, h_Ln = _bubble_state(x_n, P, approx_vle)

        if _should_switch_to_stripping(section, n, x_n, z_F, feed_stage_spec):
            section = 'Stripping'
            feed_stage = n

        if section == 'Rectifying':
            def ray_H(y, h_Ln=h_Ln, x_n=x_n):
                return h_Ln + ((Q_prime_D - h_Ln) / (x_D - x_n)) * (y - x_n)

            def diff_y(y, h_Ln=h_Ln, x_n=x_n):
                return _dew_state(y, P, approx_vle)[2] - ray_H(y)

            try:
                y_next = brentq(diff_y, x_n, x_D - 1e-5)
                ray_converged = True
            except Exception:
                y_next = max(x_B + 1e-4, x_n - 0.05)
                ray_converged = False

            _Td_next, _x_next, HV_next = _dew_state(y_next, P, approx_vle)

            denom = HV_next - h_Ln
            if abs(denom) > 1e-4:
                L_stage = D * (Q_prime_D - HV_next) / denom
            else:
                L_stage = L_reflux
            V_stage = L_stage + D

            if record_construction and ray_converged and x_n > x_B:
                construction_lines.append({
                    'type': 'rectifying',
                    'x0': x_D, 'y0': Q_prime_D,
                    'x1': x_n, 'y1': h_Ln,
                    'x2': float(y_next), 'y2': float(HV_next),
                })
        else:
            def ray_H(y, h_Ln=h_Ln, x_n=x_n):
                return h_Ln + ((Q_prime_B - h_Ln) / (x_B - x_n)) * (y - x_n)

            def diff_y(y, h_Ln=h_Ln, x_n=x_n):
                return _dew_state(y, P, approx_vle)[2] - ray_H(y)

            try:
                y_next = brentq(diff_y, x_B + 1e-5, min(0.66, x_n + 0.15))
                ray_converged = True
            except Exception:
                y_next = max(x_B + 1e-4, x_n * 0.8)
                ray_converged = False

            _Td_next, _x_next, HV_next = _dew_state(y_next, P, approx_vle)

            denom = HV_next - h_Ln
            if abs(denom) > 1e-4:
                V_next = B * (h_Ln - Q_prime_B) / denom
            else:
                V_next = V_top
            L_stage = V_next + B
            V_stage = V_next

            if record_construction and ray_converged and x_n > x_B:
                construction_lines.append({
                    'type': 'stripping',
                    'x0': x_B, 'y0': Q_prime_B,
                    'x1': x_n, 'y1': h_Ln,
                    'x2': float(y_next), 'y2': float(HV_next),
                })

        stages.append({
            'stage': n,
            'section': section,
            'x': float(x_n),
            'y': float(y_curr),
            'T_C': float(T_dew_n - 273.15),
            'h_L': float(h_Ln),
            'H_V': float(H_Vn),
            'L': float(max(0.0, L_stage)),
            'V': float(max(0.0, V_stage))
        })

        if x_n <= x_B or n >= 60:
            break

        y_curr = y_next
        x_prev = x_n

    return stages, construction_lines, feed_stage


def solve_design_column(F, z_F, P, x_D, x_B, R, feed_state, subcooling_dT=0.0,
                        murphree_eff=1.0, *, diagnostics=True, approx_vle=False,
                        feed_stage_spec=None):
    h_F = feed_state['h_F']
    q_feed = feed_state.get('q', 1.0)

    D = F * (z_F - x_B) / (x_D - x_B)
    B = F - D

    T_D, h_D = _bubble_state(x_D, P, approx_vle)
    if subcooling_dT:
        h_reflux = float(th.h_liquid_mix(x_D, T_D - subcooling_dT))
    else:
        h_reflux = h_D

    T_V1, _x_eq_top, H_V1 = _dew_state(x_D, P, approx_vle)

    if diagnostics:
        R_min, Q_prime_D_min = calc_min_reflux(x_D, x_B, z_F, P, h_F, subcooling_dT)
        N_min = calc_min_stages(x_D, x_B, P)
    else:
        R_min, N_min = 0.0, 0

    QC = D * ((R + 1.0) * H_V1 - R * h_reflux - h_D)
    Q_prime_D = h_D + QC / D

    T_B, h_B = _bubble_state(x_B, P, approx_vle)

    Q_prime_B = (F * h_F - D * Q_prime_D) / B
    QR = B * (h_B - Q_prime_B)

    V_top = (R + 1.0) * D
    L_reflux = R * D

    stages, construction_lines, feed_stage = _ponchon_stage_loop(
        z_F, x_D, x_B, D, B, Q_prime_D, Q_prime_B, V_top, L_reflux,
        murphree_eff, P, approx_vle, record_construction=diagnostics,
        feed_stage_spec=feed_stage_spec,
    )

    total_stages = len(stages)
    tray_count = max(0, total_stages - 1)

    mccabe_lines = {
        'rectifying_x': [x_D, x_D],
        'rectifying_y': [x_D, x_D],
        'stripping_x': [x_B, x_B],
        'stripping_y': [x_B, x_B],
        'q_line_x': [z_F, z_F],
        'q_line_y': [z_F, z_F],
        'staircase_x': [x_D],
        'staircase_y': [x_D],
        'stage_count': 0,
        'pinched': False,
    }

    if diagnostics:
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

        # Independent CMO McCabe–Thiele construction.  Do not reuse the
        # Ponchon–Savarit stage coordinates: those include variable internal flows
        # and therefore need not lie exactly on the CMO operating lines.
        staircase_x = [x_D]
        staircase_y = [x_D]
        m_S = (y_I - x_B) / max(x_I - x_B, 1e-12)
        b_S = x_B * (1.0 - m_S)
        y_step = x_D
        mccabe_stage_count = 0
        pinched = False
        prev_x_eq = x_D
        for _ in range(100):
            _, x_eq = th.dew_point(y_step, P)
            x_eq = float(np.clip(x_eq, 0.0, 1.0))
            staircase_x.append(x_eq)
            staircase_y.append(y_step)  # horizontal: equilibrium tie at fixed y
            mccabe_stage_count += 1
            if x_eq <= x_B:
                break
            # CMO pinches when a step no longer moves toward x_B — typically
            # R < R_min.  Do not keep drawing dummy stages up to the loop cap.
            if mccabe_stage_count > 1 and x_eq >= prev_x_eq - 1e-10:
                pinched = True
                break
            prev_x_eq = x_eq
            if feed_stage_spec is None:
                on_rectifying = x_eq >= x_I
            else:
                on_rectifying = mccabe_stage_count < int(feed_stage_spec)
            if on_rectifying:
                y_next = m_R * x_eq + b_R
            else:
                y_next = m_S * x_eq + b_S
            y_next = float(np.clip(y_next, 0.0, 1.0))
            staircase_x.append(x_eq)
            staircase_y.append(y_next)  # vertical: component-balance operating line
            if y_next <= x_B:
                break
            if y_next >= y_step - 1e-12:
                pinched = True
                break
            y_step = y_next

        mccabe_lines = {
            'rectifying_x': [x_D, x_I],
            'rectifying_y': [x_D, y_I],
            'stripping_x': [x_B, x_I],
            'stripping_y': [x_B, y_I],
            'q_line_x': [z_F, x_I],
            'q_line_y': [z_F, y_I],
            'staircase_x': staircase_x,
            'staircase_y': staircase_y,
            'stage_count': mccabe_stage_count,
            'pinched': pinched,
        }

    if feed_stage_spec is None:
        optimal_feed_stage = int(feed_stage)
    elif diagnostics:
        crossing = solve_design_column(
            F, z_F, P, x_D, x_B, R, feed_state, subcooling_dT, murphree_eff,
            diagnostics=False, approx_vle=True, feed_stage_spec=None,
        )
        optimal_feed_stage = int(crossing["feed_stage"])
    else:
        optimal_feed_stage = int(feed_stage)

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
        'feed_stage_spec': None if feed_stage_spec is None else int(feed_stage_spec),
        'optimal_feed_stage': int(optimal_feed_stage),
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

#: Smallest bottoms composition treated as physically meaningful.
_XB_FLOOR = 1e-3

#: Bisection budget for inverting the monotone N(x_D) in a rating case.
#: N is an integer step function, so the search only has to land inside the
#: right step: it stops as soon as the bracket is narrower than the tolerance.
_RATING_BISECTIONS = 16
_RATING_TOLERANCE = 2e-4


def rating_feasible_window(F, z_F, P, D):
    r"""The range of distillate compositions a rating case may actually use.

    Three constraints bound it, and the previous implementation respected none
    of them properly -- it stopped at ``min(0.66, 2.5 z_F + 0.1)``, a heuristic
    that silently excluded the high-purity end where the larger stage counts
    live.

    1. The component balance fixes :math:`x_B=(F z_F-D x_D)/B`, so :math:`x_D`
       may not rise so far that :math:`x_B` goes negative.
    2. :math:`x_B` must stay below :math:`z_F` for the split to make sense.
    3. :math:`x_D` cannot reach the azeotrope at this pressure.

    Returns ``(low, high)``; ``high <= low`` means no feasible split exists for
    this distillate rate.
    """
    B = F - D
    if B <= 0.0 or D <= 0.0:
        return 1.0, 0.0
    x_azeo, _ = th.find_azeotrope(P)
    low = max(z_F + 0.01, (F * z_F - (z_F - 0.005) * B) / D)
    high = min(x_azeo - 0.005, (F * z_F - _XB_FLOOR * B) / D)
    return float(low), float(high)


def solve_rating_column(F, z_F, P, feed_state, N_stages, N_feed, R, D_spec,
                        subcooling_dT=0.0, murphree_eff=1.0, feed_stage_spec=None):
    """Fixed-hardware case: find the split a column of ``N_stages`` delivers.

    With the feed and the distillate rate fixed, the component balance leaves a
    one-parameter family of splits indexed by :math:`x_D`, and the stage count
    rises monotonically along it.  Rating therefore means inverting
    :math:`N(x_D)` -- sampling the *whole* feasible window from
    :func:`rating_feasible_window`, then refining around the best sample.

    Each bisection probe interpolates the cached saturation envelope so the
    search is milliseconds; one exact :func:`solve_design_column` at the
    selected split produces the plot-ready column.  The requested stage count
    is not always attainable: at a given reflux ratio and distillate rate there
    is a maximum separation, and asking for more stages than that has no
    solution.  Rather than silently returning something else, the result
    carries ``rating`` diagnostics recording what was asked for, what the
    hardware can actually deliver, and whether the two agree.
    """
    D = float(D_spec)
    low, high = rating_feasible_window(F, z_F, P, D)

    def attempt(x_D, *, full):
        x_B = (F * z_F - D * x_D) / (F - D)
        if not (_XB_FLOOR <= x_B < z_F):
            return None
        try:
            return solve_design_column(
                F, z_F, P, x_D, x_B, R, feed_state, subcooling_dT, murphree_eff,
                diagnostics=full, approx_vle=not full,
                feed_stage_spec=feed_stage_spec,
            )
        except Exception:
            return None

    def present(x_D, lean_result):
        """Exact column at ``x_D``, falling back to the lean probe if needed."""
        return attempt(x_D, full=True) or lean_result

    # N(x_D) is monotonically non-decreasing across the feasible window -- a
    # purer distillate always needs at least as many stages -- so the request
    # is inverted by bisection rather than by scanning.  Probes interpolate
    # the envelope; only the winning split is solved exactly.
    solutions = []
    if high > low:
        endpoints = [(x, attempt(x, full=False)) for x in (low, high)]
        solutions = [s for _, s in endpoints if s is not None]

    polish_lo, polish_hi = low, high
    if solutions and len(solutions) == 2:
        (x_low, low_solution), (x_high, high_solution) = endpoints
        reachable_low = low_solution["total_stages"]
        reachable_high = high_solution["total_stages"]

        if N_stages <= reachable_low:
            best_bisect = low_solution
            polish_lo = polish_hi = x_low
        elif N_stages >= reachable_high:
            best_bisect = high_solution
            polish_lo = polish_hi = x_high
        else:
            # Smallest x_D whose stage count reaches the request.
            lo_x, hi_x, best_bisect = x_low, x_high, high_solution
            for _ in range(_RATING_BISECTIONS):
                if hi_x - lo_x < _RATING_TOLERANCE:
                    break
                mid_x = 0.5 * (lo_x + hi_x)
                probe = attempt(mid_x, full=False)
                if probe is None:
                    hi_x = mid_x
                    continue
                if probe["total_stages"] >= N_stages:
                    hi_x, best_bisect = mid_x, probe
                else:
                    lo_x = mid_x
            polish_lo, polish_hi = lo_x, hi_x
        solutions = [low_solution, high_solution, best_bisect]

    if not solutions:
        # No feasible split at this distillate rate; fall back to a nominal one
        # so the interface still has something coherent to display.
        fallback_x = min(0.62, z_F * 2.0)
        fallback = attempt(fallback_x, full=True) or solve_design_column(
            F, z_F, P, fallback_x,
            max(0.01, (F * z_F - D * fallback_x) / (F - D)),
            R, feed_state, subcooling_dT, murphree_eff,
            feed_stage_spec=feed_stage_spec,
        )
        fallback["rating"] = {
            "requested_stages": int(N_stages),
            "requested_feed_stage": None if feed_stage_spec is None else int(N_feed),
            "achievable_stages": None, "stages_met": False, "feed_stage_met": False,
            "message": ("No feasible split exists at this distillate rate: the "
                        "component balance drives the bottoms composition out of "
                        "range. Change D, or the product purities."),
        }
        return fallback

    counts = [s["total_stages"] for s in solutions]
    reachable = (min(counts), max(counts))   # endpoints bound the monotone range

    # Closest stage count, with the feed stage as a tie-break.
    best = min(solutions, key=lambda s: (abs(s["total_stages"] - N_stages),
                                         abs(s["feed_stage"] - N_feed)))

    presented = present(best["x_D"], best)
    # If interpolation landed on the wrong side of an N step, polish with a
    # few exact solves inside the lean bracket.  This is the rare path.
    if (presented["total_stages"] != int(N_stages)
            and reachable[0] <= N_stages <= reachable[1]
            and polish_hi > polish_lo):
        lo_x, hi_x = polish_lo, polish_hi
        for _ in range(8):
            if presented["total_stages"] == int(N_stages):
                break
            mid_x = 0.5 * (lo_x + hi_x)
            probe = attempt(mid_x, full=True)
            if probe is None:
                hi_x = mid_x
                continue
            if probe["total_stages"] >= N_stages:
                hi_x, presented = mid_x, probe
            else:
                lo_x = mid_x

    stages_met = presented["total_stages"] == int(N_stages)
    message = ""
    if not stages_met:
        if N_stages > reachable[1]:
            message = (
                f"{int(N_stages)} stages cannot be reached at R = {R:.3g} with "
                f"D fixed: the most this column can use is {reachable[1]} before "
                f"the bottoms composition runs out. Lower the reflux ratio "
                f"(towards R_min) or reduce D to need more stages."
            )
        elif N_stages < reachable[0]:
            message = (
                f"{int(N_stages)} stages is fewer than the {reachable[0]} this "
                f"separation needs at R = {R:.3g}. Raise the reflux ratio to do "
                f"the job in fewer stages."
            )
        else:
            message = (
                f"No split in the feasible window lands on exactly "
                f"{int(N_stages)} stages; the closest is "
                f"{presented['total_stages']}."
            )

    if feed_stage_spec is None:
        feed_stage_met = True
    else:
        feed_stage_met = (
            presented["feed_stage"] == int(feed_stage_spec)
            and presented["total_stages"] >= int(feed_stage_spec)
        )

    presented["rating"] = {
        "requested_stages": int(N_stages),
        "requested_feed_stage": None if feed_stage_spec is None else int(feed_stage_spec),
        "achievable_stages": reachable,
        "stages_met": stages_met,
        "feed_stage_met": feed_stage_met,
        "message": message,
    }
    return presented
