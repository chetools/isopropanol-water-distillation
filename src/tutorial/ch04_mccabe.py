"""Chapter 4 - McCabe-Thiele, including the q-line elimination in full."""

import src.plotting as plots
from src.engineering_diagrams import mccabe_balance_svg, q_line_family_svg
from src.tutorial.layout import Chapter

OBJECTIVES = (
    "Derive both operating lines from section balances and the CMO assumption.",
    "Eliminate the internal flows to obtain the q-line, step by step.",
    "Identify the pinch that sets R_min and the total-reflux limit that sets N_min.",
)


def render(state) -> None:
    ch = Chapter(4, "McCabe-Thiele", OBJECTIVES)
    ch.open()

    ch.prose(
        "McCabe–Thiele replaces the full energy treatment with a single assumption: "
        "**constant molar overflow (CMO)**. If the two components have comparable "
        "molar latent heats, heat loss is negligible, pressure drop is negligible, "
        "and sensible-heat effects are small compared with latent heat, then "
        "condensing one mole of vapour evaporates one mole of liquid, and $L$ and "
        "$V$ are each constant within a section. That single assumption is what "
        "makes the method two-dimensional and drawable."
    )
    ch.figure(
        mccabe_balance_svg(),
        "The two section envelopes. Each operating line is nothing more than the "
        "component balance for its envelope, rearranged into $y = f(x)$.",
    )

    # ==================================================================
    ch.heading("4A · The rectifying operating line")
    ch.derivation("the rectifying operating line")
    ch.step(
        1, "Draw an envelope around the top of the column",
        "Cut between stage $n$ and stage $n+1$, and take everything above the cut "
        "plus the condenser. Two streams cross the cut — vapour $V$ rising with "
        "composition $y_{n+1}$, and liquid $L$ falling with composition $x_n$ — "
        "plus the distillate leaving.",
    )
    ch.step(2, "Total balance on that envelope", "What rises must leave as liquid reflux or product:")
    ch.eq(r"V = L + D", "vtot")
    ch.step(3, "Component balance on the same envelope", "")
    ch.eq(r"V\,y_{n+1} = L\,x_n + D\,x_D", "vcomp")
    ch.step(
        4, "Introduce the reflux ratio",
        "Define $R \\equiv L_0/D$. Under CMO, $L$ is constant in the section, so "
        "$L = RD$, and " + ch.ref("vtot") + " gives $V = RD + D = (R+1)D$.",
    )
    ch.step(
        5, "Substitute and cancel",
        "Divide " + ch.ref("vcomp") + " by $V$ and substitute both: "
        "$y_{n+1} = \\dfrac{RD}{(R+1)D}x_n + \\dfrac{D}{(R+1)D}x_D$. Every $D$ "
        "cancels:",
    )
    ch.eq(r"y_{n+1}=\frac{R}{R+1}\,x_n+\frac{x_D}{R+1}", "rect")
    ch.key_result(
        "<b>Result 4.1.</b> The slope $R/(R+1)$ and intercept $x_D/(R+1)$ are "
        "<i>consequences of the envelope</i>, not fitted parameters. Two "
        "consequences follow immediately: the line always passes through "
        "$(x_D, x_D)$ on the diagonal (set $x_n = x_D$), and as $R \\to \\infty$ "
        "the slope tends to 1, so the operating line collapses onto $y = x$."
    )

    # ==================================================================
    ch.heading("4B · The stripping operating line")
    ch.derivation("the stripping operating line")
    ch.step(
        1, "Envelope the bottom",
        "Cut below stage $m$ and take everything below it including the reboiler. "
        "Liquid $\\bar L$ descends with $x_m$; vapour $\\bar V$ rises with "
        "$y_{m+1}$; bottoms $B$ leaves.",
    )
    ch.step(2, "Balances", "Total $\\bar L = \\bar V + B$, and on the light key:")
    ch.eq(r"\bar L\,x_m = \bar V\,y_{m+1} + B\,x_B", "scomp")
    ch.step(3, "Rearrange for the vapour composition", "Solve " + ch.ref("scomp") + " for $y_{m+1}$:")
    ch.eq(r"y_{m+1}=\frac{\bar L}{\bar V}\,x_m-\frac{B}{\bar V}\,x_B", "strip")
    ch.prose(
        "Setting $x_m = x_B$ in " + ch.ref("strip") + " and using "
        "$\\bar L - \\bar V = B$ gives $y_{m+1} = x_B$, so the stripping line also "
        "meets the diagonal — at $(x_B, x_B)$. This holds when the partial reboiler "
        "is counted as an equilibrium stage, which is the convention used "
        "throughout this app."
    )

    # ==================================================================
    ch.heading("4C · The q-line, eliminated in full")
    ch.prose(
        "The feed stage is where the two sections meet, and the feed's thermal "
        "condition decides how much of it joins the liquid stream and how much "
        "joins the vapour stream. The locus of possible intersections is the "
        "q-line. This is the step most texts compress into 'eliminating the "
        "internal flows'; here it is done in full."
    )

    ch.derivation("the q-line")
    ch.step(
        1, "Define q operationally",
        "$q$ is the fraction of the feed that joins the **liquid** flowing down "
        "the column: $q = (\\bar L - L)/F$. Equivalently, it is the liquid fraction "
        "after an isenthalpic flash of the feed at column pressure. From that "
        "definition and a balance across the feed stage:",
    )
    ch.eq(r"\bar L = L + qF,\qquad \bar V = V-(1-q)F", "feedjump")
    ch.step(
        2, "Write both operating lines in unsubstituted form",
        "Before cancelling anything, the two component balances at the *same* "
        "intersection point $(x, y)$ are $Vy = Lx + Dx_D$ and "
        "$\\bar V y = \\bar L x - Bx_B$.",
    )
    ch.step(
        3, "Subtract them",
        "Subtracting the rectifying form from the stripping form eliminates the "
        "product terms into the feed:",
    )
    ch.eq(r"(\bar V - V)\,y = (\bar L - L)\,x - \left(Dx_D + Bx_B\right)", "sub")
    ch.step(
        4, "Substitute the feed jump and the overall balance",
        "From " + ch.ref("feedjump") + ", $\\bar V - V = -(1-q)F$ and "
        "$\\bar L - L = qF$. From the overall component balance of chapter 1, "
        "$Dx_D + Bx_B = Fz_F$. Putting all three into " + ch.ref("sub") + ":",
    )
    ch.eq(r"-(1-q)F\,y = qF\,x - F z_F", "sub2")
    ch.step(
        5, "Divide by F and solve for y",
        "The feed rate cancels entirely — the q-line does not depend on how much "
        "feed there is, only on its condition. Dividing " + ch.ref("sub2") + " by "
        "$F$ and rearranging, $(q-1)y = qx - z_F$, hence:",
    )
    ch.eq(r"y=\frac{q}{q-1}\,x-\frac{z_F}{q-1}", "qline")
    ch.step(
        6, "Check the diagonal",
        "Set $y = x$ in " + ch.ref("qline") + ": $x(q-1) = qx - z_F$, so "
        "$-x = -z_F$ and $x = z_F$. **Every** q-line passes through "
        "$(z_F, z_F)$ regardless of $q$ — which is why the family in the figure "
        "below is a pencil of lines through one point.",
    )

    ch.figure(
        q_line_family_svg(),
        "The q-line family. Slope $q/(q-1)$ rotates the line about $(z_F, z_F)$: "
        "vertical for saturated liquid, horizontal for saturated vapour, and "
        "through the other quadrants for subcooled, two-phase and superheated "
        "feeds.",
    )
    ch.assumptions([
        ("$q > 1$", "Subcooled liquid — condenses some rising vapour, so $\\bar L > L + F$",
         "Slope positive and steep; internal reflux exceeds what the condenser sends down"),
        ("$q = 1$", "Saturated liquid feed", "Vertical q-line"),
        ("$0 < q < 1$", "Two-phase feed", "Negative slope; the feed splits between both sections"),
        ("$q = 0$", "Saturated vapour feed", "Horizontal q-line"),
        ("$q < 0$", "Superheated vapour — vaporises some descending liquid",
         "Positive shallow slope; $\\bar L < L$"),
    ])

    # ==================================================================
    ch.heading("4D · The two limits")
    ch.prose(
        "The operating lines cannot be placed arbitrarily. Two limits bound every "
        "real design, and the economic optimum lies between them."
    )
    ch.derivation("minimum reflux and minimum stages")
    ch.step(
        1, "Total reflux gives N_min",
        "As $R \\to \\infty$, " + ch.ref("rect") + " has slope 1 and intercept 0, "
        "so both operating lines become $y = x$. The staircase steps directly "
        "between the equilibrium curve and the diagonal, which is the largest "
        "possible step per stage. No design can use fewer stages, so this defines "
        "$N_{min}$ — at the cost of infinite duty and zero product.",
    )
    ch.step(
        2, "Minimum reflux gives R_min",
        "Lowering $R$ rotates the rectifying line up about $(x_D, x_D)$. At some "
        "$R$ it first touches the equilibrium curve. At that **pinch** the driving "
        "force $y^* - y$ goes to zero, the steps become infinitesimal, and "
        "$N \\to \\infty$. Below it, the required separation is impossible at any "
        "stage count.",
    )
    ch.step(
        3, "Locate the pinch correctly",
        "For a well-behaved system the pinch is at the q-line intersection. For a "
        "system with a curved or inflected equilibrium line — which IPA/water has, "
        "approaching the azeotrope — the *tangent* pinch can occur elsewhere. This "
        "app therefore searches every candidate composition rather than assuming "
        "the feed intersection governs, which is the array expression shown in "
        "chapter 5.",
    )
    ch.key_result(
        "<b>Result 4.2.</b> $R_{min}$ and $N_{min}$ bracket every feasible design. "
        "Practical reflux is typically chosen at $1.1$–$1.5 \\times R_{min}$, but "
        "the defensible value is the one that minimises total annualised cost "
        "subject to controllability — which is what the <b>Sizing &amp; economics</b> "
        "tab is for."
    )

    if state.vle is not None:
        ch.chart(
            plots.plot_xy(state.vle, state.column, state.z_F),
            f"The CMO construction for the current run: "
            f"$R = {state.column['R']:.3g}$ against "
            f"$R_{{min}} = {state.column['R_min']:.3g}$ "
            f"(ratio {state.column['R'] / max(0.01, state.column['R_min']):.3g}), "
            f"reaching $x_B = {state.column['x_B']:.4g}$ in "
            f"{state.column['mccabe_lines'].get('stage_count', '—')} CMO stages.",
            key="tutorial_mccabe",
        )
        c = state.column
        ch.worked_example(
            "the rectifying operating line for this run",
            [
                ("slope $R/(R+1)$", f"{c['R']:.6g} / ({c['R']:.6g} + 1)",
                 f"{c['R'] / (c['R'] + 1):.6f}"),
                ("intercept $x_D/(R+1)$", f"{c['x_D']:.6g} / ({c['R']:.6g} + 1)",
                 f"{c['x_D'] / (c['R'] + 1):.6f}"),
                ("check at $x = x_D$",
                 f"{c['R'] / (c['R'] + 1):.6f} x {c['x_D']:.6g} + {c['x_D'] / (c['R'] + 1):.6f}",
                 f"{c['R'] / (c['R'] + 1) * c['x_D'] + c['x_D'] / (c['R'] + 1):.6f} = x_D ✓"),
                ("$R / R_{min}$", f"{c['R']:.6g} / {c['R_min']:.6g}",
                 f"{c['R'] / max(0.01, c['R_min']):.4f}"),
            ],
        )

    ch.caution(
        "<b>Do not use CMO blindly here.</b> IPA and water have latent heats "
        "differing by roughly a factor of two on a molar basis, so the assumption "
        "underpinning this whole chapter is genuinely violated for this system. "
        "The staircase above is a useful <i>picture</i>; the stage count that the "
        "app reports comes from Ponchon–Savarit, which carries the energy balance "
        "explicitly. Compare the two — the difference is the price of CMO."
    )

    ch.self_check(
        "Why does the q-line not depend on the feed rate $F$?",
        "Because $F$ cancels in step 5: both the composition and the flow terms in "
        + ch.ref("sub2") + " are proportional to $F$. Physically, $q$ is an "
        "intensive property of the feed stream — doubling the feed doubles both the "
        "liquid and vapour it contributes, leaving the *direction* of the feed "
        "locus unchanged."
    )
    ch.self_check(
        "At total reflux, what are $D$ and $B$?",
        "Both zero. All the overhead vapour is condensed and returned, all the "
        "bottoms liquid is reboiled and returned. That is why $N_{min}$ is a "
        "limiting case rather than an operating point: it separates perfectly and "
        "produces nothing, while consuming maximum duty."
    )

    ch.heading("Implementation")
    ch.source("minimum reflux pinch search (array form)", "src/column.py", "calc_min_reflux")
    ch.source("total-reflux minimum-stage recurrence", "src/column.py", "calc_min_stages")
    ch.source("operating lines and CMO staircase", "src/column.py", "solve_design_column")
