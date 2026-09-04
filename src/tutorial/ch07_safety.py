"""Chapter 7 - safe operation, derived from inventory and energy rather than a checklist."""

from src.engineering_diagrams import safety_layers_svg
from src.tutorial.layout import Chapter

OBJECTIVES = (
    "Derive a safeguard from the dynamic energy balance, not from a checklist.",
    "Identify the relief scenarios that a distillation column can credibly present.",
    "State clearly what this model does and does not certify.",
)


def render(state) -> None:
    ch = Chapter(7, "Safe operation", OBJECTIVES)
    ch.open()

    ch.caution(
        "<b>Isopropanol is a highly flammable liquid, and IPA/water vapour can form "
        "a flammable atmosphere.</b> Treat every temperature, pressure, composition "
        "and duty this app calculates as an <i>input to a formal design review</i> "
        "— never as an operating limit."
    )

    # ==================================================================
    ch.heading("7A · Safeguards follow from the balance, not from a list")
    ch.prose(
        "A checklist tells you *what* people usually protect against. The dynamic "
        "balance tells you *why*, and therefore what to do when your column is not "
        "the usual one. Start from accumulation."
    )
    ch.derivation("a safeguard, from the unsteady energy balance")
    ch.step(
        1, "Write the balance without the steady-state assumption",
        "Chapter 1 set the accumulation term to zero. Remove that assumption and "
        "the column's internal energy becomes a state variable:",
    )
    ch.eq(r"\frac{dU}{dt}=F h_F+Q_R-D h_D-B h_B-Q_C", "dudt")
    ch.step(
        2, "Impose the deviation",
        "Total loss of cooling water sets $Q_C \\to 0$ while $Q_R$ continues "
        "unchanged. Every other term in " + ch.ref("dudt") + " is small by "
        "comparison, so $dU/dt \\approx Q_R > 0$.",
    )
    ch.step(
        3, "Translate accumulation into a measurable consequence",
        "Energy accumulating in a fixed volume of boiling liquid raises vapour "
        "inventory, and therefore pressure. The *rate* matters: $Q_R$ divided by the "
        "latent heat gives the vapour generation rate, which is the quantity a "
        "relief device must handle.",
    )
    ch.step(
        4, "Identify prevention that is genuinely independent",
        "Pressure control may call for more cooling — but cooling has failed, so "
        "the basic control system <b>cannot</b> act. A high-pressure alarm prompts "
        "an operator (a layer, but one with human response time). An independent "
        "high-high trip that removes reboiler heat attacks the term that is actually "
        "driving " + ch.ref("dudt") + ", and is independent of the failed utility.",
    )
    ch.step(
        5, "Size mitigation for the residual",
        "A relief device sized for the credible residual generation rate protects "
        "containment if prevention fails. Note the order: relief is the *last* "
        "layer, not the first. <b>A relief valve is not a substitute for controlling "
        "heat input.</b>",
    )
    ch.figure(
        safety_layers_svg(),
        "Independent protection layers for one scenario. Each layer must be shown "
        "independent of the initiating cause and of the other layers — a trip "
        "sharing a sensor with the control loop is not a second layer.",
    )
    ch.key_result(
        "<b>Result 7.1 — the method, not the answer.</b> For each deviation, "
        "identify: (1) the initiating cause; (2) how mass or energy accumulates; "
        "(3) the measurable consequence; (4) independent prevention; (5) independent "
        "mitigation. That sequence generalises to deviations no checklist "
        "anticipated."
    )

    # ==================================================================
    ch.heading("7B · The relief envelope")
    ch.prose(
        "Different scenarios govern different parts of the relief design, and the "
        "governing case is rarely obvious in advance. Each needs its own mass and "
        "energy balance:"
    )
    ch.assumptions([
        ("Blocked outlet", "Vapour generation continues with no product route",
         "Required rate from $Q_R$ / latent heat, plus thermal expansion for "
         "liquid-full lines"),
        ("External fire", "Heat input through the wetted area",
         "Required rate from the standard wetted-area correlation, not from $Q_R$"),
        ("Tube rupture", "High-pressure utility enters the low-pressure side",
         "Governed by upstream pressure and hole area; can dwarf all other cases"),
        ("Loss of cooling", "Reboiler heat with no condensation",
         "Derived above from " + ch.ref("dudt")),
        ("Condensation / steam-out", "Vapour collapses and creates vacuum",
         "Needs *vacuum* protection; a pressure relief valve does nothing here"),
    ])
    ch.caution(
        "Determining the required relief <i>rate</i> is only the first half. Inlet "
        "and outlet pressure losses, reaction forces, and safe disposal of a "
        "flammable release are equally part of the design — an adequately sized "
        "orifice on an inadequate inlet line will chatter and destroy itself."
    )

    # ==================================================================
    ch.heading("7C · Minimum engineering checks before operation")
    ch.prose(
        "**Hazard study.** Perform a HAZOP and, where risk warrants, a LOPA. Include "
        "at minimum: loss of cooling, loss of reflux, loss of utilities, blocked "
        "outlet, external fire, control-valve failure in each direction, and "
        "vacuum/condensation."
    )
    ch.prose(
        "**Ignition control.** Suitable hazardous-area electrical classification, "
        "bonding and grounding, ventilation, leak detection, compatible seals and "
        "gaskets, and control of all ignition sources."
    )
    ch.prose(
        "**Equipment protection.** Protect reboilers from low liquid level and dry "
        "firing; protect condensers against cooling loss; verify reflux pump NPSH "
        "and minimum-flow protection."
    )
    ch.prose(
        "**Operating envelope and its indicators.** Establish limits for pressure, "
        "differential pressure, reflux ratio, temperatures, levels and compositions. "
        "Trends are diagnostic: rising $\\Delta P$ with falling separation indicates "
        "flooding or entrainment; falling $\\Delta P$ with lost efficiency indicates "
        "weeping; erratic level with poor separation suggests foaming."
    )
    ch.prose(
        "**Procedures.** Start-up, shutdown, sampling, maintenance, line-breaking, "
        "confined-space entry and emergency response. Use the current safety data "
        "sheet and the regulations that apply at the site."
    )

    ch.key_result(
        "<b>What this application deliberately does not calculate.</b> Relief "
        "orifice area, SIL determination, hazardous-area classification, and safe "
        "operating limits. These require scenario-specific data, site context and "
        "formal review, so there is <b>no line of code here presented as a safety "
        "certification algorithm</b> — an absence that is intentional and should "
        "stay that way."
    )

    ch.self_check(
        "Why is 'increase cooling' not a valid safeguard against loss of cooling?",
        "Because it is not independent of the initiating cause. The control system "
        "would indeed call for more cooling, but the utility that provides it has "
        "failed — the layer and the failure share a common cause. An independent "
        "layer must act on a *different* term of " + ch.ref("dudt") + ", which is "
        "why the trip removes $Q_R$ rather than trying to restore $Q_C$."
    )
    ch.self_check(
        "A column is separating well but $\\Delta P$ has been climbing for an hour. "
        "What should you suspect?",
        "Approach to flooding. Rising pressure drop at constant throughput means the "
        "trays are holding more liquid — entrainment is recycling liquid upward, "
        "and downcomers may be backing up. Separation often stays good or even "
        "improves briefly before it collapses, so good product quality is *not* "
        "reassurance here. Reduce boil-up and investigate before efficiency falls "
        "off."
    )
