"""Chapter 1 - the problem, the envelope, and the modelling assumptions."""

from src.engineering_diagrams import model_map_svg, whole_column_balance_svg
from src.tutorial.layout import Chapter

OBJECTIVES = (
    "Draw the outer control volume and write its three independent balances.",
    "Explain why the degree-of-freedom count is exactly two once the feed is fixed.",
    "State which physical effects this model captures and which it silently omits.",
)


def render(state) -> None:
    ch = Chapter(1, "Map of the problem", OBJECTIVES)
    ch.open()

    ch.prose(
        "A distillation column couples six problems that are usually taught "
        "separately: **phase equilibrium**, **component balances**, **energy "
        "balances**, **hydraulics**, **heat transfer**, and **mechanical design**. "
        "They cannot be solved in isolation, because each one supplies a constraint "
        "the next one needs. The order in this tutorial is the order in which the "
        "constraints become available."
    )
    ch.figure(
        model_map_svg(),
        "Information flow from specifications to a buildable column. Everything "
        "left of the process/equipment boundary is thermodynamics and balances; "
        "everything right of it needs a vendor, a code, or a safety review.",
    )

    # -- Step 1 ------------------------------------------------------------
    ch.derivation("the outer envelope and its three balances")
    ch.step(
        1, "Choose a basis and draw the envelope",
        "The solver's canonical basis is one second and mol/s. Every interface "
        "selector converts to and from that basis without touching the balance. "
        "Streams crossing the envelope are the feed $F, z_F, h_F$; the distillate "
        "$D, x_D, h_D$; the bottoms $B, x_B, h_B$; condenser heat $Q_C$ leaving; and "
        "reboiler heat $Q_R$ entering.",
    )
    ch.figure(
        whole_column_balance_svg(),
        "The outer control volume. Arrow directions define the sign convention: "
        "both duties are stored as positive magnitudes, so the direction is carried "
        "by which side of the energy balance they appear on.",
    )

    ch.step(
        2, "Write the total material balance",
        "Nothing accumulates, reacts, or leaks, so what enters must leave:",
    )
    ch.eq(r"F = D + B", "total")

    ch.step(
        3, "Write the component balance on the light key",
        "The same statement applied to isopropanol alone. Water is not an "
        "independent equation — for a binary, $\\sum x_i = 1$ makes the second "
        "component balance a linear combination of the first two:",
    )
    ch.eq(r"F z_F = D x_D + B x_B", "component")

    ch.step(
        4, "Solve the two together",
        "Substitute $B = F - D$ from " + ch.ref("total") + " into "
        + ch.ref("component") + ": $F z_F = D x_D + (F - D) x_B$. Collect the $D$ "
        "terms, $F z_F - F x_B = D(x_D - x_B)$, and divide:",
    )
    ch.eq(r"D = F\,\frac{z_F - x_B}{x_D - x_B}, \qquad B = F - D", "split")
    ch.prose(
        "This is the lever rule on the composition axis, and it already carries a "
        "hard feasibility condition: $x_B < z_F < x_D$. If a specification pair "
        "violates it, $D$ goes negative or exceeds $F$ — which is why the "
        "specification locker in the **Design** tab clamps rather than letting the "
        "solver return a physically meaningless answer."
    )

    ch.step(
        5, "Write the energy balance",
        "On one common enthalpy reference, with no heat loss:",
    )
    ch.eq(r"F h_F + Q_R = D h_D + B h_B + Q_C", "energy")
    ch.prose(
        "Three equations " + ch.ref("total") + ", " + ch.ref("component") + " and "
        + ch.ref("energy") + " relate seven unknowns once the feed is fixed: "
        "$x_D, x_B, D, B, R, Q_C, Q_R$. Two of the three equations are material and "
        "consume two unknowns; the energy balance links the two duties but "
        "introduces no new independent variable. **Exactly two specifications remain "
        "free** — which is precisely the budget the locker enforces."
    )

    ch.key_result(
        "<b>Result 1.1.</b> With the feed fully specified, a binary column at fixed "
        "pressure has <b>two</b> remaining degrees of freedom. Any two of "
        "$x_D, x_B, D, B, R, Q_C, Q_R$ may be set — with the single exception of "
        "$\\{D, B\\}$ together, which is redundant because "
        + ch.ref("total") + " already relates them."
    )

    ch.step(
        6, "Only then move inward",
        "Each equilibrium stage adds two component balances, one energy balance, "
        "two summation constraints, and the equilibrium relations. Temperatures, "
        "compositions and internal flows are solved together. A drawn staircase is "
        "a *visualisation* of that solution, not a substitute for it.",
    )

    # -- Assumptions -------------------------------------------------------
    ch.heading("Assumptions, and how each one fails")
    ch.assumptions([
        ("Equilibrium stages",
         "Vapour and liquid leaving a stage share $T$, $P$ and chemical potential, "
         "so one equilibrium calculation defines the stage",
         "Real trays approach but never reach it; apply Murphree efficiency, or "
         "HETP / rate-based modelling for packing"),
        ("Binary, non-reacting",
         "Two components, one independent composition variable, so the whole "
         "problem is drawable in two dimensions",
         "Dissolved gases, side draws, reaction or entrainment all break the "
         "balance structure, not merely its accuracy"),
        ("Ideal vapour, $\\phi_i \\approx 1$",
         "Removes the vapour-phase equation of state entirely",
         "Degrades as pressure rises; near or above a few bar use a $\\gamma$–$\\phi$ "
         "or $\\phi$–$\\phi$ model"),
        ("Negligible pressure drop",
         "One pressure for the whole column, so one T-x-y diagram serves every stage",
         "A real 40-tray column may drop 0.1–0.3 bar, shifting bottom temperatures "
         "and reboiler duty"),
        ("No heat loss",
         "The energy balance closes with only $Q_C$ and $Q_R$",
         "Lagging quality changes internal reflux; a cold column self-refluxes"),
        ("Constant pressure azeotrope",
         "One fixed composition barrier at $x_{azeo}$",
         "The azeotrope *moves* with pressure — which is the basis of "
         "pressure-swing distillation"),
    ])

    ch.caution(
        "<b>The azeotrope is a hard barrier, not a numerical difficulty.</b> "
        "IPA/water forms a minimum-boiling azeotrope near $x = 0.67$ at 1 atm. "
        "Ordinary distillation at fixed pressure <i>cannot</i> produce a distillate "
        "richer than that, no matter how many stages or how much reflux. Reaching "
        "anhydrous IPA requires changing the problem: pressure swing, an entrainer, "
        "or a membrane. This app clamps $x_D$ below the azeotrope for that reason."
    )

    ch.self_check(
        "Why can you not specify $D$ and $B$ as your two degrees of freedom?",
        "Because " + ch.ref("total") + " already fixes $B$ once $D$ is chosen. "
        "Specifying both either restates that equation (harmless but wasteful, "
        "leaving the column actually under-specified by one) or contradicts it "
        "(no solution). The locker therefore refuses the $\\{D, B\\}$ pair "
        "explicitly rather than letting the solver fail."
    )
    ch.self_check(
        "A colleague specifies $x_D$, $x_B$ **and** $R$. What have they done?",
        "Over-specified the column by one. With $x_D$ and $x_B$ fixed, "
        + ch.ref("split") + " already determines $D$ and $B$, and the stage "
        "calculation then determines the reflux needed to hit those purities in the "
        "available stages. Fixing $R$ as well generally makes the system "
        "inconsistent — the usual symptom is a solver that 'converges' to a "
        "composition profile that does not close the component balance."
    )

    ch.heading("Implementation")
    ch.source("degree-of-freedom specification closure", "src/dof_manager.py", "recompute")
    ch.source("outer column material and energy solution", "src/column.py", "solve_design_column")
