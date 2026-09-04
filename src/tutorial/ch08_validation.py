"""Chapter 8 - validation criteria, numerical acceptance, and references."""

from src.tutorial.layout import Chapter

OBJECTIVES = (
    "Apply numerical acceptance criteria that a smooth-looking plot cannot satisfy.",
    "Know which residuals are checked in this app and to what tolerance.",
    "Locate the primary sources for every model and parameter used here.",
)

REFERENCES = [
    ("[Renon & Prausnitz (1968), *Local compositions in thermodynamic excess "
      "functions for liquid mixtures*](https://doi.org/10.1002/aic.690140124)",
     "The original NRTL paper. Chapter 2's excess Gibbs energy and the "
     "non-randomness parameter come from here."),
    ("[Seader, Henley & Roper, *Separation Process Principles*]"
     "(https://www.wiley.com/en-us/Separation+Process+Principles%3A+Chemical+and+Biochemical+Operations%2C+4th+Edition-p-9781119327881)",
     "Flash calculations, equilibrium stages, McCabe-Thiele and Ponchon-Savarit "
     "at the level of chapters 3 to 5."),
    ("[ChemSep distillation text](https://chemsep.org/book/docs/book2.pdf)",
     "Operating lines, pinch behaviour and graphical stepping; useful for "
     "cross-checking chapter 4."),
    ("[University of Oran distillation notes](https://www.univ-usto.dz/images/coursenligne/op_nl.pdf)",
     "Ponchon-Savarit tie lines, difference points and construction — an "
     "alternative presentation of chapter 5."),
    ("[NIST Chemistry WebBook: isopropyl alcohol]"
     "(https://webbook.nist.gov/cgi/cbook.cgi?ID=C67630&Mask=4) and "
     "[water](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=4)",
     "Independent property data for cross-checking vapour pressures and latent "
     "heats."),
    ("[CHEMCAD 7 User Guide](https://www.chemstations.com/content/documents/CHEMCAD_7_User_Guide.pdf)",
     "Basis for offering per-quantity engineering units while keeping one "
     "canonical solver basis."),
    ("[AIChE CCPS resources](https://www.aiche.org/ccps)",
     "Process-safety management and layers of protection, underpinning chapter 7."),
    ("[OSHA flammable-liquid standard 1910.106]"
     "(https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.106)",
     "Regulatory context for handling isopropanol."),
]


def render(state) -> None:
    ch = Chapter(8, "Validation and references", OBJECTIVES)
    ch.open()

    # ==================================================================
    ch.heading("8A · Numerical acceptance criteria")
    ch.prose(
        "A visually smooth curve is not validation. These are the checks that "
        "distinguish a converged solution from a plausible-looking one, and the app "
        "reports each of them in the **Audit** tab."
    )

    ch.prose("**Global closure.** Both residuals should sit at solver tolerance:")
    ch.eq(r"\frac{|F-D-B|}{F}\;\to\;0,\qquad "
          r"\frac{|F z_F-D x_D-B x_B|}{F z_F}\;\to\;0", "globalres")
    ch.prose("**Energy closure** on the common reference of chapter 2:")
    ch.eq(r"r_H=F h_F+Q_R-D h_D-B h_B-Q_C\;\to\;0", "energyres")

    ch.caution(
        "<b>Global closure can hide equal-and-opposite stage errors.</b> Two stages "
        "wrong in opposite directions sum to zero overall. Every stage must "
        "therefore satisfy total, component and energy residuals <i>on its own "
        "envelope</i> — which is why the Audit tab exposes the full stage table "
        "rather than only the summary."
    )

    ch.prose(
        "**Per-state sanity.** $\\sum_i x_i = \\sum_i y_i = 1$; all compositions and "
        "phase fractions inside $[0,1]$; bubble and dew roots bracketed inside a "
        "physically valid temperature interval; stage temperatures monotonic from "
        "top to bottom."
    )
    ch.prose(
        "**Collinearity.** $\\Delta_D$, $F$ and $\\Delta_B$ must lie on one line "
        "(Result 5.3). This is the most sensitive single check available, because "
        "it fails whenever any enthalpy reference or duty sign is inconsistent."
    )
    ch.prose(
        "**Independent confirmation.** Recompute selected states with a different "
        "property package, or against measured IPA/water VLE data. Agreement of a "
        "model with itself is not evidence."
    )
    ch.prose(
        "**Off-design behaviour.** Hydraulics must be checked at normal, turndown, "
        "maximum throughput, start-up and upset conditions — not only at the design "
        "point."
    )
    ch.prose(
        "**Economic statement.** Any cost figure must carry its currency, cost-index "
        "date, location, installation scope and uncertainty class, or it cannot be "
        "compared with anything."
    )

    # ==================================================================
    ch.heading("8B · How this build protects the physics")
    ch.prose(
        "The calculation modules were rewritten into array form so the code would "
        "match the equations in chapters 2 to 6. That refactoring is only "
        "trustworthy because it was done against a golden-reference test: NRTL "
        "activity coefficients, excess enthalpy, the full phase envelope at three "
        "pressures, the dew-point branch, and every column scalar and stage profile "
        "are pinned to values produced by the previous implementation, at "
        "tolerances between $10^{-8}$ and $10^{-12}$."
    )
    ch.key_result(
        "<b>Why this matters to a reader.</b> The equation-and-code panels "
        "throughout this tutorial claim the code implements the printed equation. "
        "The characterisation tests are what make that claim checkable: "
        "<code>uv run pytest tests/test_characterization.py</code> re-verifies it "
        "in a few seconds, and <code>tests/golden/regenerate.py</code> is the only "
        "way the reference values can change."
    )

    if state.column is not None:
        c = state.column
        total_res = c['F'] - c['D'] - c['B']
        ipa_res = c['F'] * c['z_F'] - c['D'] * c['x_D'] - c['B'] * c['x_B']
        energy_res = (c['F'] * c['h_F'] + c['Q_R'] - c['D'] * c['h_D']
                      - c['B'] * c['h_B'] - c['Q_C'])
        ch.worked_example(
            "closure residuals for the current run",
            [
                ("total, " + ch.ref("globalres"),
                 f"{c['F']:.10g} - {c['D']:.10g} - {c['B']:.10g}",
                 f"{total_res:.3e} mol/s"),
                ("IPA component",
                 f"{c['F']:.6g}x{c['z_F']:.6g} - {c['D']:.6g}x{c['x_D']:.6g} - {c['B']:.6g}x{c['x_B']:.6g}",
                 f"{ipa_res:.3e} mol/s"),
                ("energy, " + ch.ref("energyres"),
                 "F h_F + Q_R - D h_D - B h_B - Q_C",
                 f"{energy_res:.3e} kW"),
            ],
        )

    # ==================================================================
    ch.heading("8C · References")
    ch.prose(
        "Each source below is tied to the chapter that uses it, so a claim in this "
        "tutorial can be traced to something outside it."
    )
    for citation, why in REFERENCES:
        ch.prose(f"- {citation}\n  <br/>*{why}*")

    ch.prose(
        "The NRTL constants and pure-component correlations used by this app are "
        "documented in `data/` and `src/thermo.py`. **Retain those source files "
        "with any published result** — a VLE curve without its parameter provenance "
        "cannot be reproduced or defended."
    )

    ch.heading("Implementation")
    ch.source("process KPI equation and substitution ledger", "src/process_audit.py", "build_process_ledger")
    ch.source("canonical-to-selected unit conversion", "src/units.py", "from_canonical")
    ch.source("selected-to-canonical unit conversion", "src/units.py", "to_canonical")
