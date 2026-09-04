"""Chapter 6 - equipment sizing and economics, with Souders-Brown and CRF derived."""

from src.engineering_diagrams import (
    column_geometry_svg,
    sizing_workflow_svg,
    tray_hydraulics_svg,
)
from src.tutorial.layout import Chapter

OBJECTIVES = (
    "Derive the Souders-Brown velocity from a droplet force balance.",
    "Assemble column diameter and height from the governing vapour load.",
    "Derive the capital recovery factor from the annuity series and build a TAC.",
)


def render(state) -> None:
    ch = Chapter(6, "Equipment and economics", OBJECTIVES)
    ch.open()

    ch.prose(
        "Stage count alone does not determine geometry. A 20-stage column can be "
        "0.5 m or 5 m in diameter depending entirely on throughput. The bridge from "
        "process results to equipment is the **vapour load**, and everything in this "
        "chapter follows from it."
    )
    ch.figure(
        sizing_workflow_svg(),
        "The calculation chain. Each box corresponds to a row in the downloadable "
        "ledger in the Sizing tab, so every number can be traced to its inputs.",
    )

    # ==================================================================
    ch.heading("6A · The governing vapour load")
    ch.derivation("volumetric vapour rate and required area")
    ch.step(
        1, "Find the governing stage, do not assume it",
        "Because $L$ and $V$ vary from stage to stage (chapter 5), the largest "
        "vapour rate is not necessarily at the top. Inspect **every** calculated "
        "stage and take the maximum molar vapour rate together with that stage's own "
        "$T$, $P$ and vapour molecular weight.",
    )
    ch.step(2, "Convert to actual volumetric rate", "By the real-gas law at that stage's conditions:")
    ch.eq(r"\dot V_{vol}=\frac{\dot n_V\,Z R T}{P}", "vvol")
    ch.step(
        3, "Divide by a design velocity",
        "Area is volumetric flow over velocity. The question is what velocity is "
        "allowable — which is the next derivation:",
    )
    ch.eq(r"A_{active}=\frac{\dot V_{vol}}{u_{design}},\qquad "
          r"A_{total}=\frac{A_{active}}{1-f_{dc}},\qquad "
          r"D_c=\sqrt{\frac{4A_{total}}{\pi}}", "diameter")

    # ==================================================================
    ch.heading("6B · Souders-Brown, derived from a droplet force balance")
    ch.prose(
        "The capacity factor $C$ is usually quoted without explanation, which makes "
        "it look like a fudge factor. It is not — it falls out of asking when a "
        "liquid droplet stops falling."
    )
    ch.derivation("the Souders-Brown flooding velocity")
    ch.step(
        1, "Consider one droplet in the rising vapour",
        "A droplet of diameter $d$ and liquid density $\\rho_L$ is suspended in "
        "vapour of density $\\rho_V$ moving upward at velocity $u$. Three forces "
        "act: gravity down, buoyancy up, and drag up.",
    )
    ch.step(
        2, "Write the force balance at the entrainment threshold",
        "Entrainment begins when drag plus buoyancy exactly balances weight, so the "
        "droplet is carried rather than falling. With droplet volume "
        "$\\tfrac{\\pi}{6}d^3$ and projected area $\\tfrac{\\pi}{4}d^2$:",
    )
    ch.eq(r"\underbrace{C_D\,\frac{\pi d^2}{4}\,\frac{\rho_V u^2}{2}}_{\text{drag}}"
          r"=\underbrace{\frac{\pi d^3}{6}\,(\rho_L-\rho_V)\,g}"
          r"_{\text{weight}-\text{buoyancy}}", "force")
    ch.step(
        3, "Solve for the velocity",
        "Cancel $\\pi d^2$ from both sides of " + ch.ref("force") + " and rearrange "
        "for $u$:",
    )
    ch.eq(r"u=\sqrt{\frac{4\,g\,d}{3\,C_D}}\;"
          r"\sqrt{\frac{\rho_L-\rho_V}{\rho_V}}", "sb_full")
    ch.step(
        4, "Recognise the capacity factor",
        "The first square root in " + ch.ref("sb_full") + " contains only the "
        "droplet size and drag coefficient — properties of the *tray geometry and "
        "the froth*, not of the throughput. Lumping them into a single empirical "
        "constant $C$ gives the familiar form:",
    )
    ch.eq(r"u_{flood}=C\,\sqrt{\frac{\rho_L-\rho_V}{\rho_V}},\qquad "
          r"u_{design}=f_{flood}\,u_{flood}", "souders")
    ch.key_result(
        "<b>Result 6.1.</b> $C$ is not arbitrary — it encapsulates droplet size and "
        "drag, which is exactly why it depends on <i>tray spacing, surface tension, "
        "foaming tendency and liquid load</i>, and why vendor correlations present "
        "it as a chart rather than a number. The density-ratio group is the part "
        "that is genuinely universal."
    )
    ch.caution(
        "A generic $C$ applied without checking entrainment, weeping, downcomer "
        "backup and allowable pressure drop is a guess wearing an equation. "
        "70&ndash;85% of flooding is a <i>starting point for iteration</i>, not a "
        "design."
    )
    ch.figure(
        tray_hydraulics_svg(),
        "The tray area split and the operating window. Too much vapour floods; too "
        "little lets liquid weep through the perforations instead of bubbling "
        "through the froth. Both bounds destroy efficiency.",
    )

    # ==================================================================
    ch.heading("6C · Height and shell")
    ch.derivation("tangent-to-tangent height")
    ch.step(
        1, "Convert equilibrium stages to actual trays",
        "Equilibrium stages are a thermodynamic result; trays are hardware. "
        "$N_{actual} \\approx N_{equilibrium}/E_{overall}$. Do this **before** "
        "applying tray spacing — multiplying equilibrium stages by spacing "
        "understates the column by whatever the efficiency is.",
    )
    ch.step(2, "Stack the allowances", "Each term is separately justified, not a lumped factor:")
    ch.eq(r"H_{shell}\approx N_{actual}\,s_{tray}+H_{top}+H_{feed}+H_{bottom}"
          r"+H_{allowance}", "height")
    ch.figure(
        column_geometry_svg(),
        "Height stack-up. Top disengagement prevents entrainment into the overhead "
        "line; the bottom sump provides reboiler circulation and holdup time.",
    )
    ch.step(
        3, "Screen the shell thickness",
        "A thin-wall cylindrical shell under internal pressure needs, before "
        "corrosion allowance:",
    )
    ch.eq(r"t_p=\frac{P_D D}{2SE-1.2P_D},\qquad t=\max\left(t_{min},\;t_p+c_A\right)",
          "thickness")
    ch.caution(
        "This is a <b>screen only</b>. Heads, wind and seismic loading, vacuum "
        "conditions, nozzle reinforcement, support skirts, fatigue and code minimum "
        "thicknesses are all excluded. A pressure vessel is designed to a code by a "
        "qualified engineer, not by this equation."
    )

    # ==================================================================
    ch.heading("6D · Heat exchangers")
    ch.prose(
        "The duties come from the column solution, but the *areas* depend on choices "
        "the simulation cannot make for you, which is why $U$ and $\\Delta T_{lm}$ "
        "are exposed as inputs rather than assumed:"
    )
    ch.eq(r"A_C=\frac{|Q_C|}{U_C\,\Delta T_{lm,C}},\qquad "
          r"A_R=\frac{|Q_R|}{U_R\,\Delta T_{lm,R}}", "areas")
    ch.prose(
        "Fouling, phase regime (condensing versus subcooling, nucleate versus film "
        "boiling), and utility temperature levels dominate $U$. A factor-of-two "
        "error in $U$ is a factor-of-two error in area and therefore in exchanger "
        "cost."
    )

    # ==================================================================
    ch.heading("6E · Economics: annualise before comparing")
    ch.prose(
        "Comparing purchased shell costs across designs is meaningless, because a "
        "cheaper column usually needs more reflux and therefore more steam forever. "
        "The correct comparison is **total annualised cost**, which needs capital "
        "and operating costs on the same yearly basis."
    )

    ch.derivation("the capital recovery factor")
    ch.step(
        1, "State the problem",
        "Convert a lump-sum capital cost $P$ today into an equivalent uniform "
        "annual payment $A$ over $n$ years at discount rate $i$ — the same "
        "calculation as a mortgage payment.",
    )
    ch.step(
        2, "Write the present value of the annuity",
        "Each payment $A$ made at the end of year $k$ is worth $A(1+i)^{-k}$ today. "
        "Summing over $n$ years:",
    )
    ch.eq(r"P=\sum_{k=1}^{n}\frac{A}{(1+i)^{k}}"
          r"=A\sum_{k=1}^{n}v^{k},\qquad v\equiv\frac{1}{1+i}", "annuity")
    ch.step(
        3, "Sum the geometric series",
        "The sum in " + ch.ref("annuity") + " is geometric with ratio $v$, first "
        "term $v$, and $n$ terms, so "
        "$\\sum_{k=1}^{n}v^{k}=v\\dfrac{1-v^{n}}{1-v}$. Substituting "
        "$v = 1/(1+i)$ gives $1-v = i/(1+i)$, hence "
        "$\\sum = \\dfrac{1-(1+i)^{-n}}{i}$:",
    )
    ch.eq(r"P=A\,\frac{1-(1+i)^{-n}}{i}", "pv")
    ch.step(
        4, "Invert for the annual payment",
        "Solve " + ch.ref("pv") + " for $A/P$ and multiply numerator and denominator "
        "by $(1+i)^n$:",
    )
    ch.eq(r"CRF\;\equiv\;\frac{A}{P}=\frac{i\,(1+i)^{n}}{(1+i)^{n}-1}", "crf")
    ch.prose(
        "Two sanity checks on " + ch.ref("crf") + ". As $i \\to 0$ it tends to "
        "$1/n$ — with no discounting you simply divide the capital across the years. "
        "As $n \\to \\infty$ it tends to $i$ — a perpetual loan costs only its "
        "interest. Both limits are what they should be."
    )

    ch.step(
        5, "Build the total annualised cost",
        "Annualised capital plus the annual operating costs:",
    )
    ch.eq(r"TAC=CRF\cdot\left(C_{col}+C_{cond}+C_{reb}+C_{ctrl}\right)"
          r"+C_{steam}+C_{cool}+C_{elec}+C_{maint}", "tac")
    ch.eq(r"C_{utility}=|Q|\;t_{op}\;\left(0.0036\;\mathrm{GJ/kWh}\right)\;p_{utility}",
          "utility")

    ch.heading("The cost sequence used here")
    ch.prose(
        "1. Scale shell, trays and exchangers with sub-linear capacity exponents "
        "(the six-tenths rule and its relatives).\n"
        "2. Multiply by material factor and by the project/base cost-index ratio.\n"
        "3. Apply the displayed installation factor.\n"
        "4. Add controls and contingency.\n"
        "5. Compute annual steam, cooling and maintenance from " + ch.ref("utility") + ".\n"
        "6. Annualise the capital with " + ch.ref("crf") + ".\n"
        "7. Sum to " + ch.ref("tac") + "."
    )
    ch.caution(
        "This is a <b>Class-4 screening estimate</b>, expected accuracy roughly "
        "&plusmn;30&ndash;50%. Before any capital decision, replace the defaults "
        "with current vendor quotes, a traceable cost index with a stated date, "
        "local utility tariffs, the actual metallurgy and pressure class, and site "
        "factors. Every correlation here is location-, material-, pressure-, "
        "index-year- and capacity-range-dependent."
    )

    ch.key_result(
        "<b>Result 6.2 — the design trade-off.</b> Raising $R$ <i>reduces</i> stage "
        "count (shorter column) but <i>raises</i> vapour load, and therefore "
        "diameter, condenser duty and reboiler duty — capital in one direction, "
        "operating cost in the other. Sweep $R$ just above $R_{min}$ and pick the "
        "minimum " + ch.ref("tac") + ", then check that the result is controllable "
        "and can be turned down."
    )

    if state.sizing_hint:
        ch.prose(state.sizing_hint)

    ch.self_check(
        "Why convert equilibrium stages to actual trays before applying spacing?",
        "Because tray spacing is the distance between *physical* trays. With "
        "$E_{overall} = 0.6$, ten equilibrium stages need about seventeen real "
        "trays; multiplying ten by the spacing understates the column height by "
        "40%, and consequently understates shell mass, cost and the pump head "
        "needed to reflux it."
    )
    ch.self_check(
        "$CRF$ with $i = 0.10$ and $n = 15$ — estimate it, then check.",
        "$(1.1)^{15} \\approx 4.177$, so "
        "$CRF = 0.1 \\times 4.177 / 3.177 \\approx 0.131$. So each dollar of "
        "capital costs about 13 cents per year — noticeably more than the 6.7 cents "
        "($1/15$) that ignoring the time value of money would suggest."
    )

    ch.heading("Implementation")
    ch.source("all sizing and economic calculation steps", "src/sizing.py", "calculate_sizing")
    ch.source("unit-aware sizing dashboard and ledger", "src/sizing_dashboard.py", "render_sizing_dashboard")
