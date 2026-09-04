"""Chapter 3 - flash calculations, with Rachford-Rice derived and bounded."""

from src.engineering_diagrams import (
    flash_algorithm_svg,
    flash_balance_svg,
    rachford_rice_svg,
)
from src.tutorial.layout import Chapter

OBJECTIVES = (
    "Derive the Rachford-Rice equation from the component balance, not recall it.",
    "Prove it is monotonic, and use the phase test before attempting a root.",
    "Set up all five flash specifications and identify the unknown in each.",
)

RR_CODE = '''def rachford_rice(z, k_values):
    """sum_i z_i (K_i - 1) / (1 + beta (K_i - 1)) = 0"""
    def residual(beta):
        return float(np.sum(z * (k - 1.0) / (1.0 + beta * (k - 1.0))))

    g0, g1 = residual(0.0), residual(1.0)
    if g0 <= 0.0:   return 0.0      # all liquid
    if g1 >= 0.0:   return 1.0      # all vapour
    return float(brentq(residual, 0.0, 1.0, xtol=1e-12))'''


def render(state) -> None:
    ch = Chapter(3, "Flash calculations", OBJECTIVES)
    ch.open()

    ch.prose(
        "A flash is a single equilibrium contact — one stage, standing alone. Every "
        "stage in the column is a flash with extra streams attached, so getting "
        "this right once pays for the rest of the tutorial."
    )
    ch.figure(
        flash_balance_svg(),
        "The flash envelope. One feed enters; two phases in mutual equilibrium "
        "leave. $\\beta = V/F$ is the vapour fraction, physically restricted to "
        "$[0, 1]$.",
    )

    # ==================================================================
    ch.heading("3A · Deriving Rachford-Rice")
    ch.derivation("the Rachford-Rice equation")
    ch.step(
        1, "Write the component balance",
        "For each component, what enters leaves in one phase or the other:",
    )
    ch.eq(r"F z_i = L x_i + V y_i", "cbal")
    ch.step(
        2, "Divide by the feed and substitute the vapour fraction",
        "With $\\beta = V/F$ and therefore $L/F = 1-\\beta$, "
        + ch.ref("cbal") + " becomes $z_i = (1-\\beta)x_i + \\beta y_i$. Now use "
        "the equilibrium relation $y_i = K_i x_i$:",
    )
    ch.eq(r"z_i=(1-\beta)x_i+\beta K_i x_i = x_i\left[1+\beta(K_i-1)\right]", "zi")
    ch.step(
        3, "Isolate each composition",
        "Both phase compositions now follow from $\\beta$ and the $K$-values alone:",
    )
    ch.eq(r"x_i=\frac{z_i}{1+\beta(K_i-1)},\qquad "
          r"y_i=\frac{z_i K_i}{1+\beta(K_i-1)}", "xy")
    ch.step(
        4, "Impose both summation constraints",
        "Each of $\\sum_i x_i = 1$ and $\\sum_i y_i = 1$ is a valid equation, but "
        "each alone is numerically poor — both have poles and neither is monotonic. "
        "**Subtract** them instead. The difference $\\sum_i y_i - \\sum_i x_i = 0$ "
        "gives, using " + ch.ref("xy") + ":",
    )
    ch.eq(r"g(\beta)\;\equiv\;\sum_i\frac{z_i\,(K_i-1)}{1+\beta(K_i-1)}\;=\;0",
          "rr")
    ch.step(
        5, "Show it is monotonic",
        "Differentiate " + ch.ref("rr") + " term by term:",
    )
    ch.eq(r"g'(\beta)=-\sum_i\frac{z_i\,(K_i-1)^2}{\left[1+\beta(K_i-1)\right]^2}"
          r"\;\le\;0", "rrprime")
    ch.prose(
        "Every term of " + ch.ref("rrprime") + " is a non-negative quantity with a "
        "minus sign in front, because $z_i \\ge 0$ and both the squared factors are "
        "non-negative. So $g$ is **non-increasing everywhere between its poles**. "
        "That is the whole reason this form is used instead of "
        "$\\sum x_i = 1$: a monotonic function with a sign change has exactly one "
        "root, and a bracketed solver cannot miss it or land on the wrong branch."
    )

    ch.key_result(
        "<b>Result 3.1.</b> Subtracting the two summation constraints is not a "
        "trick — it converts two badly behaved equations into one monotonic "
        "equation with a unique bracketed root. The same idea (difference the "
        "constraints, then bracket) recurs throughout equilibrium computation."
    )

    # ==================================================================
    ch.heading("3B · Test the phase before solving for it")
    ch.prose(
        "A root of " + ch.ref("rr") + " in $[0,1]$ exists only if the feed is "
        "genuinely two-phase. Evaluating the residual at the two endpoints settles "
        "it before any iteration:"
    )
    ch.eq(r"g(0)=\sum_i z_i(K_i-1),\qquad "
          r"g(1)=\sum_i \frac{z_i(K_i-1)}{K_i}", "phasetest")
    ch.prose(
        "If $g(0) \\le 0$ the mixture is subcooled liquid and $\\beta = 0$. "
        "If $g(1) \\ge 0$ it is superheated vapour and $\\beta = 1$. Only opposite "
        "signs indicate a two-phase root. Skipping this test is the usual cause of "
        "a flash routine returning $\\beta$ outside $[0,1]$ and then producing "
        "negative compositions from " + ch.ref("xy") + "."
    )
    ch.figure(
        rachford_rice_svg(),
        "The shape of $g(\\beta)$. Monotonic decrease between poles means the "
        "bracketed root is unique; the endpoint values are the phase test.",
    )
    ch.code(
        equation=r"g(\beta)=\sum_i\frac{z_i(K_i-1)}{1+\beta(K_i-1)}=0",
        snippet=RR_CODE,
        path="src/flash.py",
        symbol="rachford_rice",
        note="The summation is a NumPy expression over the component axis, so the "
             "code is the equation with a solver wrapped around it.",
    )

    # ==================================================================
    ch.heading("3C · The five specifications")
    ch.prose(
        "Which variables are known determines which equation you solve. All five "
        "cases below use the same " + ch.ref("rr") + " at their core; they differ "
        "only in what the outer loop varies."
    )
    ch.assumptions([
        ("**Ideal TP flash** — given $T, P, z$",
         "$K_i = P_i^{sat}(T)/P$ needs no composition, so one pass suffices",
         "Wrong whenever $\\gamma \\ne 1$; for IPA/water it misses the azeotrope"),
        ("**Non-ideal TP flash** — given $T, P, z$",
         "$K_i = \\gamma_i P_i^{sat}/(\\phi_i P)$ depends on $x$, so alternate the "
         "Rachford-Rice solve and the NRTL update to convergence",
         "Undamped iteration oscillates near the azeotrope, where $\\partial\\gamma/\\partial x$ is large"),
        ("**Bubble T** — given $P, x$, set $\\beta = 0$",
         "Collapses to the single scalar bubble-point root of chapter 2",
         "Needs a bracket that extends below both pure boiling points"),
        ("**Dew T** — given $P, y$, set $\\beta = 1$",
         "Same idea from the vapour side",
         "Harder: $\\gamma$ depends on the *unknown* liquid $x$, so it needs an "
         "inner composition loop even at fixed $T$"),
        ("**Adiabatic PH flash** — given $P, z, h_F$",
         "$T$ becomes an unknown; the outer loop roots the enthalpy residual",
         "The outer residual must include heat of mixing and latent heat on one "
         "common reference, or it converges to the wrong temperature"),
    ])
    ch.heading("The adiabatic flash, in detail")
    ch.derivation("the adiabatic (PH) flash")
    ch.step(
        1, "Add the energy balance",
        "An adiabatic flash has $Q = 0$, so the outlet enthalpy equals the inlet "
        "enthalpy:",
    )
    ch.eq(r"h_F=(1-\beta)\,h_L(T,\mathbf{x})+\beta\,H_V(T,\mathbf{y})", "ph")
    ch.step(
        2, "Recognise the nesting",
        "In " + ch.ref("ph") + " the unknowns are $T$, $\\beta$, $\\mathbf{x}$ and "
        "$\\mathbf{y}$ — but given $T$, the previous section already determines the "
        "other three. So the problem is *one* scalar unknown with an expensive "
        "residual, not four simultaneous unknowns.",
    )
    ch.step(
        3, "Bracket the outer variable, iterate the inner one",
        "For each trial $T$: run the complete non-ideal TP flash to convergence, "
        "evaluate $h_{out}=(1-\\beta)h_L+\\beta H_V$, and return the residual "
        "$h_F - h_{out}$. Update the temperature **bracket** — never a raw "
        "fixed-point step — and repeat.",
    )
    ch.caution(
        "Never update $T$, $P$, $\\beta$ and $\\gamma$ together in one unguarded "
        "simultaneous fixed-point iteration near an azeotrope. The activity "
        "derivative is steep there and the iteration diverges or, worse, converges "
        "to the wrong branch. <b>Bracket the outer scalar; damp the inner activity "
        "update.</b>"
    )
    ch.figure(
        flash_algorithm_svg(),
        "The nesting. The inner loop must be converged before the outer enthalpy "
        "residual means anything — an outer step taken on a half-converged inner "
        "solve is chasing noise.",
    )

    ch.prose(
        "A **constant-$T$, variable-$P$** flash swaps the roles: pressure becomes "
        "the outer unknown while the inner composition loop closes equilibrium. The "
        "structure is identical; only the bracketed variable changes."
    )

    ch.self_check(
        "Why subtract the summation constraints rather than use $\\sum x_i = 1$?",
        "$\\sum_i x_i(\\beta) - 1 = 0$ is a valid equation but is not monotonic and "
        "has poles inside the physical interval, so a solver can jump branches. The "
        "difference " + ch.ref("rr") + " is provably non-increasing by "
        + ch.ref("rrprime") + ", so sign change implies a unique root. Robustness, "
        "not elegance, is the reason."
    )
    ch.self_check(
        "The phase test gives $g(0) = -0.4$ and $g(1) = -0.9$. What is the answer?",
        "Both negative, so there is no root in $[0,1]$ and the stable state is "
        "**all liquid**, $\\beta = 0$. Returning the bracket endpoint is the "
        "correct answer here, not a solver failure — which is why the test is done "
        "before, not after, attempting the root."
    )

    ch.heading("Implementation")
    ch.source("Rachford-Rice root with phase tests", "src/flash.py", "rachford_rice")
    ch.source("ideal TP flash", "src/flash.py", "ideal_tp_flash")
    ch.source("non-ideal NRTL TP flash", "src/flash.py", "nonideal_tp_flash")
    ch.source("fixed-P bubble-temperature flash", "src/flash.py", "bubble_t_fixed_p")
    ch.source("fixed-P dew-temperature flash", "src/flash.py", "dew_t_fixed_p")
    ch.source("fixed-T specified-vapour-fraction pressure flash", "src/flash.py", "tvf_flash")
    ch.source("adiabatic PH flash", "src/flash.py", "adiabatic_ph_flash")
