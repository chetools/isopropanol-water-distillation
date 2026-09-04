"""Chapter 5 - Ponchon-Savarit, with the difference point and collinearity proved."""

import src.plotting as plots
from src.engineering_diagrams import mesh_stage_svg, ponchon_construction_svg
from src.tutorial.layout import Chapter

OBJECTIVES = (
    "Derive the difference point as an invariant of the section balances.",
    "Prove that the difference point, the stage points and the feed are collinear.",
    "Step a stage, and use the lever rule to recover the internal flows.",
)

RMIN_CODE = '''x = np.linspace(max(0.01, x_B), min(x_azeo - 0.002, x_D - 0.005), 150)
T_b, y = th.bubble_point_curve(x, P)          # one solve, every sample
h_L = th.h_liquid_mix(x, T_b)
H_V = th.h_vapor_mix(y, T_b)

tie_slope = np.where(np.abs(y - x) < 1e-5, np.nan, y - x)
Q_int = h_L + ((H_V - h_L) / tie_slope) * (x_D - x)     # the equation
Q_prime_D_min = float(np.nanmax(Q_int))'''


def render(state) -> None:
    ch = Chapter(5, "Ponchon-Savarit", OBJECTIVES)
    ch.open()

    ch.prose(
        "Ponchon–Savarit keeps the same equilibrium tie lines as McCabe–Thiele but "
        "adds the axis McCabe–Thiele threw away: **molar enthalpy**. Because energy "
        "is now carried explicitly rather than assumed away, unequal latent heats, "
        "heat of mixing, feed enthalpy, subcooled reflux and section-wise varying "
        "$L/V$ all appear naturally instead of being hidden inside CMO."
    )
    ch.figure(
        mesh_stage_svg(),
        "One equilibrium stage and its four MESH closures. Ponchon–Savarit satisfies "
        "the H equation graphically, which is exactly the equation CMO replaces with "
        "an assumption.",
    )

    # ==================================================================
    ch.heading("5A · Building the diagram")
    ch.derivation("thermodynamically paired enthalpy curves")
    ch.step(
        1, "Solve equilibrium at every composition",
        "For each liquid composition $x$, find the bubble temperature and the "
        "equilibrium vapour $y$ — the chapter 2 calculation, evaluated across the "
        "whole composition range at once.",
    )
    ch.step(
        2, "Evaluate both enthalpies on one reference",
        "Compute $h_L(x, T_{bub})$ and $H_V(y, T_{bub})$ using the *same* reference "
        "state. Plotting $h_L$ against $x$ and $H_V$ against $y$ gives the two "
        "curves; joining each equilibrium pair gives a **tie line**.",
    )
    ch.caution(
        "The two curves must be plotted against <i>different</i> composition "
        "variables — $h_L$ against $x$, $H_V$ against $y$ — but the tie line joins "
        "points computed at the <i>same</i> temperature. Plotting both against $x$ "
        "is a common and silent error that makes every subsequent construction "
        "wrong."
    )

    # ==================================================================
    ch.heading("5B · The rectifying difference point")
    ch.prose(
        "This is the central idea of the method, and it is worth deriving carefully "
        "because everything else follows from it mechanically."
    )
    ch.derivation("the rectifying difference point")
    ch.step(
        1, "Envelope the top, as before",
        "Cut between stages $n$ and $n+1$; take the condenser and everything above. "
        "Vapour $V_{n+1}$ enters the envelope from below, liquid $L_n$ leaves "
        "downward, distillate $D$ leaves, and $Q_C$ leaves.",
    )
    ch.step(2, "Write all three balances", "")
    ch.eq(r"V_{n+1}-L_n = D", "vminusl")
    ch.eq(r"V_{n+1}y_{n+1}-L_n x_n = D x_D", "compdiff")
    ch.eq(r"V_{n+1}H_{n+1}-L_n h_n = D h_D + Q_C", "enerdiff")
    ch.step(
        3, "Notice what is invariant",
        "The left sides of " + ch.ref("vminusl") + ", " + ch.ref("compdiff") + " and "
        + ch.ref("enerdiff") + " are all *differences* between the two "
        "counter-current internal streams. Their right sides contain only "
        "distillate-side quantities — which do not depend on $n$. So the difference "
        "$V_{n+1} - L_n$ is the **same fictitious stream at every cut in the "
        "section**, with flow $D$, composition $x_D$, and an enthalpy we can now "
        "extract.",
    )
    ch.step(
        4, "Extract its enthalpy coordinate",
        "Divide " + ch.ref("enerdiff") + " by " + ch.ref("vminusl") + ". The left "
        "side is the enthalpy of the difference stream by definition; the right "
        "side is $(Dh_D + Q_C)/D$:",
    )
    ch.eq(r"Q'_D \;\equiv\; \frac{V_{n+1}H_{n+1}-L_n h_n}{V_{n+1}-L_n}"
          r"\;=\;h_D+\frac{Q_C}{D}", "QD")
    ch.key_result(
        "<b>Result 5.1.</b> The rectifying difference point is "
        "$\\Delta_D = (x_D,\\; h_D + Q_C/D)$. It is a <i>net flow</i>, not a real "
        "stream: it has the composition of the distillate but an enthalpy raised by "
        "the condenser duty per mole of product. Because it lies above the "
        "saturated-vapour curve, it plots off the top of the physical region — "
        "which is correct, not a plotting error."
    )

    ch.step(
        5, "Prove the collinearity",
        "Rearranging " + ch.ref("vminusl") + " gives $V_{n+1} = L_n + D$. Substituting "
        "into " + ch.ref("compdiff") + " and " + ch.ref("enerdiff") + " shows that the "
        "point $\\Delta_D$ is the *external division point* of the segment joining "
        "$(x_n, h_n)$ and $(y_{n+1}, H_{n+1})$ in the ratio $L_n : V_{n+1}$. Three "
        "points related by such a division are collinear. So the liquid state, the "
        "vapour state and $\\Delta_D$ **always lie on one straight line** — and that "
        "line is the graphical statement of both the component and the energy "
        "balance simultaneously.",
    )
    ch.key_result(
        "<b>Result 5.2 (the lever rule).</b> Because the three points are collinear "
        "with external division ratio $L_n : V_{n+1}$, measuring the two segment "
        "lengths returns the internal flows directly: "
        "$\\dfrac{L_n}{V_{n+1}} = \\dfrac{\\overline{\\Delta_D\\,y_{n+1}}}"
        "{\\overline{\\Delta_D\\,x_n}}$. This is how the method delivers "
        "<b>non-constant</b> $L$ and $V$ without ever assuming CMO."
    )

    # ==================================================================
    ch.heading("5C · The stripping difference point, and the feed line")
    ch.derivation("the stripping difference point")
    ch.step(
        1, "Envelope the bottom",
        "By the identical argument on the lower section, the invariant difference is "
        "$L_m - V_{m+1} = B$, and its enthalpy coordinate is:",
    )
    ch.eq(r"Q'_B \;\equiv\; \frac{L_m h_m - V_{m+1}H_{m+1}}{L_m-V_{m+1}}"
          r"\;=\;h_B-\frac{Q_R}{B}", "QB")
    ch.prose(
        "The minus sign is not a slip: reboiler heat *enters*, so it lowers the net "
        "enthalpy of the downward net stream. $\\Delta_B$ therefore plots **below** "
        "the saturated-liquid curve, mirroring $\\Delta_D$ above the vapour curve."
    )
    ch.step(
        2, "Connect the two through the feed",
        "The whole-column balances say the feed is the sum of the two net streams: "
        "$F = D + B$, $Fz_F = Dx_D + Bx_B$, and, using " + ch.ref("QD") + " and "
        + ch.ref("QB") + ", $Fh_F = DQ'_D + BQ'_B$. That last relation is exactly "
        "the statement that $(z_F, h_F)$ is the *internal* division point of the "
        "segment $\\Delta_D\\Delta_B$ in ratio $B : D$:",
    )
    ch.eq(r"Q'_B=\frac{F h_F - D\,Q'_D}{B}", "QBfromF")
    ch.key_result(
        "<b>Result 5.3.</b> $\\Delta_D$, the feed point $F$, and $\\Delta_B$ are "
        "<b>collinear</b>. This is the single most useful check in the whole method: "
        "if those three points do not lie on a line, the energy balance has not "
        "closed. The app asserts this in its test suite to a slope tolerance of "
        "$10^{-6}$."
    )

    # ==================================================================
    ch.heading("5D · Stepping a stage")
    ch.derivation("one stage of the construction")
    ch.step(
        1, "Start at the product",
        "Begin at the distillate composition on the appropriate curve. The vapour "
        "leaving stage 1 has $y_1 = x_D$ for a total condenser.",
    )
    ch.step(
        2, "Follow the tie line — this is thermodynamics",
        "From the current vapour point, the tie line leads to the liquid in "
        "equilibrium with it. This step uses only the equilibrium calculation of "
        "chapter 2; no balance is involved.",
    )
    ch.step(
        3, "Draw the ray through the difference point — this is the balance",
        "From that liquid point, draw a straight line through $\\Delta_D$ and "
        "extend it to the saturated-vapour curve. By Result 5.2 the intersection is "
        "the vapour rising from the stage below. This step uses only the balances; "
        "no equilibrium is involved.",
    )
    ch.step(
        4, "Alternate, and switch difference points at the feed",
        "Repeat steps 2 and 3. Once the construction crosses the feed line, switch "
        "from $\\Delta_D$ to $\\Delta_B$ — that switch *is* the feed stage, and "
        "switching at the crossing is what makes it the optimal feed location.",
    )
    ch.step(
        5, "Stop and interpolate",
        "Continue until $x_n \\le x_B$. The last step is generally fractional; "
        "interpolating it rather than rounding up is the difference between a stage "
        "count and a stage estimate.",
    )
    ch.prose(
        "The alternation of steps 2 and 3 — equilibrium, then balance, then "
        "equilibrium — is the structure of *every* stage-by-stage method. "
        "McCabe–Thiele does the same thing; it just uses a straight operating line "
        "in place of the ray because CMO has already fixed $L/V$."
    )
    ch.figure(
        ponchon_construction_svg(),
        "One stage of the construction. Tie line (equilibrium) then ray through "
        "$\\Delta_D$ (balance); the intersection with $H_V$ locates the next stage.",
    )

    # ==================================================================
    ch.heading("5E · Minimum reflux, as an array expression")
    ch.prose(
        "At minimum reflux some tie line, extended, passes through $\\Delta_D$. "
        "Extending the tie line through $(x, h_L)$ and $(y, H_V)$ out to the "
        "distillate composition gives the intercept"
    )
    ch.eq(r"Q'_{int}(x)=h_L(x)+\frac{H_V(y)-h_L(x)}{y-x}\,\left(x_D-x\right)", "pinch")
    ch.prose(
        "and the **largest** such intercept is the limiting one, since a lower "
        "$\\Delta_D$ would place some tie line on the wrong side of the operating "
        "line. Because " + ch.ref("pinch") + " is evaluated independently at each "
        "sampled composition, the whole search is one array expression followed by "
        "a maximum — and the code can be read straight against the equation:"
    )
    ch.code(
        equation=r"Q'_{D,min}=\max_x\left[h_L+\frac{H_V-h_L}{y-x}(x_D-x)\right],"
                 r"\qquad R_{min}=\frac{Q'_D-H_{V1}}{H_{V1}-h_{reflux}}",
        snippet=RMIN_CODE,
        path="src/column.py",
        symbol="calc_min_reflux",
        note="Tie lines too close to the azeotrope are excluded with NaN rather "
             "than by an if-statement inside a loop.",
    )

    if state.vle is not None:
        c = state.column
        ch.chart(
            plots.plot_ponchon_savarit(state.vle, c, state.z_F, state.feed['h_F']),
            f"The Ponchon–Savarit construction for the current run. "
            f"$\\Delta_D = ({c['x_D']:.4g},\\, {c['Q_prime_D']:.4g})$ and "
            f"$\\Delta_B = ({c['x_B']:.4g},\\, {c['Q_prime_B']:.4g})$; the dashed "
            f"line through the feed point demonstrates Result 5.3.",
            key="tutorial_ponchon",
        )
        slope_DF = (c['Q_prime_D'] - c['h_F']) / (c['x_D'] - state.z_F)
        slope_FB = (c['h_F'] - c['Q_prime_B']) / (state.z_F - c['x_B'])
        ch.worked_example(
            "difference points and the collinearity check",
            [
                ("$Q'_D = h_D + Q_C/D$",
                 f"{c['h_D']:.6g} + {c['Q_C']:.6g} / {c['D']:.6g}",
                 f"{c['Q_prime_D']:.6g} kJ/mol"),
                ("$Q'_B = (F h_F - D Q'_D)/B$",
                 f"({c['F']:.6g} x {c['h_F']:.6g} - {c['D']:.6g} x {c['Q_prime_D']:.6g}) / {c['B']:.6g}",
                 f"{c['Q_prime_B']:.6g} kJ/mol"),
                ("$Q_R = B(h_B - Q'_B)$",
                 f"{c['B']:.6g} x ({c['h_B']:.6g} - {c['Q_prime_B']:.6g})",
                 f"{c['Q_R']:.6g} kW"),
                ("slope $\\Delta_D \\to F$",
                 f"({c['Q_prime_D']:.6g} - {c['h_F']:.6g}) / ({c['x_D']:.6g} - {state.z_F:.6g})",
                 f"{slope_DF:.8g}"),
                ("slope $F \\to \\Delta_B$",
                 f"({c['h_F']:.6g} - {c['Q_prime_B']:.6g}) / ({state.z_F:.6g} - {c['x_B']:.6g})",
                 f"{slope_FB:.8g}"),
                ("collinearity residual", f"|{slope_DF:.8g} - {slope_FB:.8g}|",
                 f"{abs(slope_DF - slope_FB):.3e} ✓"),
            ],
        )

    ch.caution(
        "Ponchon–Savarit removes the CMO assumption, but <b>not</b> the equilibrium-"
        "stage assumption and <b>not</b> the fixed-pressure assumption. Tray "
        "efficiency, pressure profile, entrainment and rate-based mass transfer all "
        "still require additional models."
    )

    ch.self_check(
        "Why does $\\Delta_D$ plot above the saturated-vapour curve?",
        "Because " + ch.ref("QD") + " adds $Q_C/D$ to the distillate enthalpy, and "
        "$Q_C$ is positive. $\\Delta_D$ is a *net* stream, not a real one, so it is "
        "under no obligation to lie in the physically attainable region. Its "
        "distance above the vapour curve is a direct visual measure of the "
        "condenser duty per mole of distillate — which is why increasing $R$ visibly "
        "pushes it upward."
    )
    ch.self_check(
        "The three points $\\Delta_D$, $F$, $\\Delta_B$ do not line up. What is wrong?",
        "The energy balance has not closed. In practice the causes are: enthalpies "
        "computed on two different reference states; $h^E$ included in one curve "
        "but not the other; a sign error on $Q_C$ or $Q_R$; or a feed enthalpy "
        "evaluated at the wrong temperature. It is essentially never a plotting "
        "problem — collinearity is an algebraic consequence of "
        + ch.ref("QBfromF") + ", so a visible gap means the numbers themselves "
        "disagree."
    )

    ch.heading("Implementation")
    ch.source("difference points, rays, roots and lever rules", "src/column.py", "solve_design_column")
    ch.source("minimum reflux pinch search", "src/column.py", "calc_min_reflux")
    ch.source("saturated liquid mixture enthalpy", "src/thermo.py", "h_liquid_mix")
    ch.source("saturated vapour mixture enthalpy", "src/thermo.py", "h_vapor_mix")
