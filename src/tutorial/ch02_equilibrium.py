"""Chapter 2 - phase equilibrium and the NRTL model, derived rather than quoted."""

import src.plotting as plots
from src.engineering_diagrams import nrtl_local_composition_svg, txy_anatomy_svg
from src.tutorial.layout import Chapter

OBJECTIVES = (
    "Derive modified Raoult's law from equality of fugacity, and know what was dropped.",
    "Obtain the NRTL activity coefficient by differentiating the excess Gibbs energy.",
    "Derive the excess enthalpy from Gibbs-Helmholtz and say why it must appear in h_L.",
)

NRTL_CODE = '''def nrtl_ln_gamma(x, tau, G):
    S = np.einsum("...k,...ki->...i", x, G)        # S_i = sum_k x_k G_ki
    C = np.einsum("...m,...mj->...j", x, tau * G)  # C_j = sum_m x_m tau_mj G_mj
    r = C / S                                      # ratio common to both terms
    first  = r                                     # C_i / S_i
    second = np.einsum("...ij,...j->...i",
                       G * (tau - r[..., None, :]), x / S)
    return first + second'''

HE_CODE = '''def excess_enthalpy(x1, T, _step=1e-30):
    """h^E = -R T^2 sum_i x_i d(ln gamma_i)/dT"""
    tau, G = nrtl_matrices(T + 1j * _step)          # complex step in T
    dln_gamma_dT = nrtl_ln_gamma(x, tau, G).imag / _step
    return -R_GAS * T**2 * np.sum(x * dln_gamma_dT, axis=-1) / 1000.0'''


def render(state) -> None:
    ch = Chapter(2, "Equilibrium and NRTL", OBJECTIVES)
    ch.open()

    # ==================================================================
    ch.heading("2A · From equal fugacity to modified Raoult's law")
    ch.prose(
        "Everything downstream rests on one statement: at equilibrium a component "
        "has the same escaping tendency in both phases. The useful working form is "
        "not obvious from that statement, so it is worth deriving rather than "
        "quoting."
    )

    ch.derivation("modified Raoult's law")
    ch.step(
        1, "Start from chemical potential",
        "Equilibrium requires $\\mu_i^L = \\mu_i^V$. Because "
        "$\\mu_i = \\mu_i^\\circ + RT\\ln f_i$ at fixed $T$, and both phases share "
        "the same $\\mu_i^\\circ$ at that temperature, equality of chemical "
        "potential *is* equality of fugacity:",
    )
    ch.eq(r"f_i^{\,L} = f_i^{\,V}", "fugacity")

    ch.step(
        2, "Express the vapour fugacity",
        "Referenced to the ideal-gas state, the vapour fugacity is the partial "
        "pressure corrected by a fugacity coefficient:",
    )
    ch.eq(r"f_i^{\,V} = y_i\,\phi_i\,P", "fV")

    ch.step(
        3, "Express the liquid fugacity",
        "Referenced to the *pure saturated liquid* at the same temperature. Three "
        "factors appear: the composition, the departure from ideal-solution "
        "behaviour, and the pressure correction from $P_i^{sat}$ up to $P$:",
    )
    ch.eq(
        r"f_i^{\,L} = x_i\,\gamma_i\,P_i^{sat}(T)\,"
        r"\underbrace{\exp\!\left[\int_{P_i^{sat}}^{P}\frac{v_i^L}{RT}\,dP\right]}"
        r"_{\text{Poynting}}",
        "fL",
    )

    ch.step(
        4, "Estimate the two corrections near 1 atm",
        "The Poynting exponent is $v_i^L \\Delta P / RT$. For water, "
        "$v^L \\approx 1.8\\times10^{-5}\\,\\mathrm{m^3/mol}$; with "
        "$\\Delta P \\sim 10^4$ Pa and $RT \\approx 3000$ J/mol the exponent is "
        "about $6\\times10^{-5}$, so the factor is $1.00006$. The vapour fugacity "
        "coefficient at these conditions is likewise within a fraction of a percent "
        "of unity. Both are dropped — deliberately, and only because they were "
        "estimated first.",
    )

    ch.step(
        5, "Equate and rearrange",
        "Setting " + ch.ref("fV") + " equal to " + ch.ref("fL") + " with "
        "$\\phi_i \\approx 1$ and Poynting $\\approx 1$:",
    )
    # Note the trailing space: adjacent string literals are folded by the
    # parser, so "...\qquad" + "y_i = ..." would yield the bogus command
    # \qquady, which KaTeX renders as red error text.
    ch.eq(r"y_i P = x_i\,\gamma_i\,P_i^{sat}(T)"
          r"\qquad\Longrightarrow\qquad "
          r"y_i = \frac{x_i\,\gamma_i\,P_i^{sat}(T)}{P}", "raoult")

    ch.step(
        6, "Impose the summation constraint",
        "Summing " + ch.ref("raoult") + " over all components with "
        "$\\sum_i y_i = 1$ gives the bubble-point equation — a single scalar "
        "equation whose root in $T$ is the bubble temperature:",
    )
    ch.eq(r"\sum_i x_i\,\gamma_i(T,\mathbf{x})\,P_i^{sat}(T) = P", "bubble")

    ch.key_result(
        "<b>Result 2.1.</b> This is <i>modified</i> Raoult's law, not Raoult's law. "
        "The difference is $\\gamma_i$, and for IPA/water it is not a small "
        "correction: $\\gamma_{IPA}$ exceeds 2 in dilute aqueous solution. Setting "
        "$\\gamma_i = 1$ removes the azeotrope entirely and predicts a separation "
        "that does not exist."
    )

    # ==================================================================
    ch.heading("2B · Why NRTL, and where its equation comes from")
    ch.prose(
        "IPA and water both hydrogen-bond, but not equally with each other. A water "
        "molecule is more likely to find another water molecule beside it than a "
        "random draw from the bulk composition would suggest. NRTL — Non-Random "
        "Two-Liquid — puts exactly that idea into an equation."
    )
    ch.figure(
        nrtl_local_composition_svg(),
        "Local composition. In an ideal mixture every neighbour is drawn at random "
        "from the bulk; in a real one, energetically favoured pairs cluster. "
        "$\\tau_{ij}$ measures the energy difference and $\\alpha$ how strongly it "
        "biases the neighbourhood.",
    )

    ch.prose("The model postulates an excess Gibbs energy of this form:")
    ch.eq(r"\frac{g^E}{RT}=\sum_i x_i\,"
          r"\frac{\sum_j x_j\,\tau_{ji}G_{ji}}{\sum_k x_k G_{ki}},"
          r"\qquad \tau_{ij}=\frac{B_{ij}}{T},"
          r"\qquad G_{ij}=\exp(-\alpha_{ij}\tau_{ij})", "gE")

    ch.prose(
        "The activity coefficient is **not** a separate fitted quantity. It is the "
        "partial molar derivative of " + ch.ref("gE") + ", which is why activity "
        "coefficients automatically satisfy Gibbs–Duhem. Here is that "
        "differentiation, done rather than asserted."
    )

    ch.derivation("the NRTL activity coefficient")
    ch.step(
        1, "State the definition",
        "By definition of a partial molar excess property,",
    )
    ch.eq(r"\ln\gamma_i=\left[\frac{\partial\,(n\,g^E/RT)}{\partial n_i}\right]"
          r"_{T,P,\,n_{j\neq i}}", "defn")

    ch.step(
        2, "Convert mole fractions to mole numbers",
        "Differentiating with respect to $n_i$ requires the extensive form. Put "
        "$x_j = n_j/n$ with $n=\\sum_j n_j$. Every summation in " + ch.ref("gE") +
        " is homogeneous of degree zero in $\\mathbf{n}$ except the leading $x_i$, "
        "so the $n$'s cancel to leave",
    )
    ch.eq(r"\frac{n\,g^E}{RT}=\sum_i n_i\,\frac{\sum_j n_j\tau_{ji}G_{ji}}"
          r"{\sum_k n_k G_{ki}}", "extensive")
    ch.prose(
        "This expression is homogeneous of degree **one** in $\\mathbf{n}$, as any "
        "extensive property must be. That is a useful check: if it were not, "
        "Euler's theorem would fail and the resulting $\\gamma_i$ would not satisfy "
        "Gibbs–Duhem."
    )

    ch.step(
        3, "Name the two repeated sums",
        "Two groups recur throughout, so name them once. They are the *only* two "
        "arrays the final answer needs:",
    )
    ch.eq(r"S_i \equiv \sum_k x_k G_{ki},\qquad "
          r"C_j \equiv \sum_m x_m \tau_{mj} G_{mj},\qquad r_j\equiv \frac{C_j}{S_j}",
          "SC")

    ch.step(
        4, "Differentiate the $i$-th term",
        "In " + ch.ref("extensive") + " the term with the explicit factor $n_i$ "
        "contributes, by the product rule, its own bracket evaluated at composition "
        "$\\mathbf{x}$. That bracket is exactly $C_i/S_i = r_i$. This is the first "
        "term of the answer, and it is where the deceptively simple leading ratio "
        "comes from.",
    )

    ch.step(
        5, "Differentiate every other term by the quotient rule",
        "Each term $j$ in " + ch.ref("extensive") + " is a quotient "
        "$n_j C_j^{(n)} / S_j^{(n)}$. Differentiating with respect to $n_i$: the "
        "numerator contributes $\\partial C_j/\\partial n_i = \\tau_{ij}G_{ij}/n$ "
        "and the denominator contributes "
        "$-\\,(C_j/S_j)\\,\\partial S_j/\\partial n_i = -\\,r_j G_{ij}/n$. "
        "Collecting the two with the common factor $x_j G_{ij}/S_j$ gives the "
        "bracketed difference $(\\tau_{ij}-r_j)$ — which is why the second term of "
        "NRTL has that characteristic subtracted-ratio shape.",
    )

    ch.step(
        6, "Assemble",
        "Adding the results of Steps 4 and 5:",
    )
    ch.eq(r"\ln\gamma_i=\underbrace{\frac{C_i}{S_i}}_{\text{step 4}}"
          r"+\underbrace{\sum_j \frac{x_j G_{ij}}{S_j}\left(\tau_{ij}-r_j\right)}"
          r"_{\text{step 5}}", "lngamma")

    ch.step(
        7, "Check the limits",
        "As $x_i \\to 1$ the mixture becomes pure $i$: $S_i \\to G_{ii} = 1$, "
        "$C_i \\to \\tau_{ii}G_{ii} = 0$, and every cross term vanishes, so "
        "$\\ln\\gamma_i \\to 0$ and $\\gamma_i \\to 1$. Likewise $\\tau_{ij} \\to 0$ "
        "recovers the ideal solution. A model that failed either limit would be "
        "wrong regardless of how well it fitted data.",
    )

    ch.key_result(
        "<b>Result 2.2.</b> " + ch.ref("lngamma") + " needs only two contractions, "
        "$S$ and $C$, and the ratio $r=C/S$ built from them. That is why the "
        "implementation below is four lines and why it is valid for any number of "
        "components — the binary case is simply a 2&times;2 $\\tau$."
    )

    ch.code(
        equation=r"\ln\gamma_i=\frac{C_i}{S_i}"
                 r"+\sum_j \frac{x_j G_{ij}}{S_j}\left(\tau_{ij}-\frac{C_j}{S_j}\right)",
        snippet=NRTL_CODE,
        path="src/thermo.py",
        symbol="nrtl_ln_gamma",
        note="Component index is the last axis; each einsum subscript is a "
             "summation index of the equation.",
    )

    # ==================================================================
    ch.heading("2C · Excess enthalpy, and why the VLE model owes it to the energy model")
    ch.prose(
        "Because $\\tau_{ij}=B_{ij}/T$ depends on temperature, NRTL does not only "
        "predict activity coefficients — it *also* predicts a heat of mixing. "
        "Omitting that term while using NRTL for equilibrium makes the "
        "thermodynamic model internally inconsistent, and Ponchon–Savarit is built "
        "on enthalpies, so the inconsistency shows up directly in the duties."
    )

    ch.derivation("excess enthalpy from Gibbs-Helmholtz")
    ch.step(
        1, "Start from the Gibbs-Helmholtz relation",
        "For any excess property, $\\left[\\partial(g^E/RT)/\\partial T\\right]_{P,\\mathbf{x}} "
        "= -\\,h^E/(RT^2)$. Rearranged:",
    )
    ch.eq(r"h^E=-RT^2\left[\frac{\partial\,(g^E/RT)}{\partial T}\right]_{P,\mathbf{x}}",
          "gh")
    ch.step(
        2, "Express it through the activity coefficients",
        "Since $g^E/RT=\\sum_i x_i\\ln\\gamma_i$ and the $x_i$ are held constant "
        "during the differentiation, the derivative passes straight through the sum:",
    )
    ch.eq(r"h^E=-RT^2\sum_i x_i\left(\frac{\partial \ln\gamma_i}{\partial T}\right)"
          r"_{P,\mathbf{x}}", "he")
    ch.step(
        3, "Take the derivative without hand calculus",
        "$\\ln\\gamma_i$ is analytic in $T$, so the derivative can be taken by the "
        "**complex-step** method: evaluate at $T + ih$ with a tiny $h$, and the "
        "imaginary part divided by $h$ *is* the derivative — exactly, with no "
        "subtractive cancellation, because the Taylor expansion "
        "$f(T+ih)=f(T)+ihf'(T)-\\tfrac{h^2}{2}f''(T)+\\dots$ puts $f'$ alone in the "
        "imaginary part. The code can therefore state " + ch.ref("he") + " literally.",
    )
    ch.code(
        equation=r"h^E=-RT^2\sum_i x_i\frac{\partial \ln\gamma_i}{\partial T}",
        snippet=HE_CODE,
        path="src/thermo.py",
        symbol="excess_enthalpy",
        note="Verified against the hand-differentiated form to 7e-16 kJ/mol over a "
             "(T, x) grid.",
    )
    ch.caution(
        "Complex-step differentiation only works while the whole chain stays "
        "analytic. A single <code>abs</code>, <code>clip</code> or comparison "
        "applied to the complex temperature silently destroys the imaginary part "
        "and returns a derivative of zero — which looks like a converged answer. "
        "The composition is clipped <i>before</i> the complex step for exactly this "
        "reason."
    )

    ch.prose(
        "The enthalpy curves that Ponchon–Savarit needs then follow directly, both "
        "on the same reference state (pure saturated liquid at 25 °C):"
    )
    ch.eq(r"h_L(x,T)=\sum_i x_i\!\int_{T_{ref}}^{T}\!\! C_{p,L,i}\,dT + h^E(x,T)", "hL")
    ch.eq(r"H_V(y,T)=\sum_i y_i\left[\int_{T_{ref}}^{T}\!\! C_{p,L,i}\,dT "
          r"+ \Delta H_{vap,i}(T)\right]", "HV")

    # ==================================================================
    ch.heading("2D · Solving for the phase envelope")
    ch.derivation("the bubble-point root and the azeotrope")
    ch.step(
        1, "Form the residual",
        "At a trial temperature, $r(T)=\\sum_i x_i\\gamma_i(T,\\mathbf{x})P_i^{sat}(T)-P$ "
        "from " + ch.ref("bubble") + ". Both $\\gamma$ and $P^{sat}$ rise with $T$, "
        "so $r$ is monotonically increasing — which guarantees a bracketed root is "
        "unique.",
    )
    ch.step(
        2, "Bracket it physically",
        "The root lies between the two pure boiling points, *extended downward*: a "
        "minimum-boiling azeotrope boils below both pure components, so the lower "
        "bound must be $\\min(T_{b,1},T_{b,2}) - 15$ K rather than the pure minimum.",
    )
    ch.step(
        3, "Solve, then recover the vapour",
        "With $T$ known, " + ch.ref("raoult") + " gives $y_i$ directly. Verify "
        "$\\sum_i y_i = 1$ — it is a genuine check, not a formality, because it "
        "would fail if the root had not converged.",
    )
    ch.step(
        4, "Find the azeotrope as a second root problem",
        "The azeotrope is where the vapour and liquid compositions coincide, so it "
        "is the root of $y_1(x_1) - x_1 = 0$ — a root-find whose residual is itself "
        "a root-find. This app caches it per pressure for that reason.",
    )
    ch.eq(r"y_1(x_1)-x_1=0 \;\;\Longrightarrow\;\; x_{azeo}", "azeo")

    ch.figure(
        txy_anatomy_svg(),
        "How to read the phase envelope, and what the azeotrope forbids. A vertical "
        "cut below the bubble curve is all liquid, above the dew curve all vapour, "
        "and between them a two-phase mixture whose phases sit at the two curve "
        "intersections at that temperature.",
    )

    if state.vle is not None:
        ch.chart(
            plots.plot_txy(state.vle, state.column, state.z_F, state.P),
            f"The calculated IPA/water envelope for the current run at "
            f"{state.P/1000:.1f} kPa. The azeotrope is at "
            f"$x = {state.vle['x_azeo']:.4f}$, "
            f"$T = {state.vle['T_azeo_C']:.2f}\\,°C$.",
            key="tutorial_txy",
        )

        ch.worked_example(
            "bubble point at the current feed composition",
            [
                ("$z_F$", f"feed IPA mole fraction = {state.z_F:.4f}",
                 f"{state.z_F:.4f}"),
                ("$T_{bubble}$", f"root of sum(x_i g_i Psat_i) = {state.P:.6g} Pa",
                 f"{state.feed['T_bubble_K'] - 273.15:.3f} °C"),
                ("$h_{L,sat}$", f"h_L({state.z_F:.4f}, {state.feed['T_bubble_K']:.3f} K)",
                 f"{state.feed['h_L_sat']:.5f} kJ/mol"),
                ("$H_{V,sat}$", f"H_V({state.z_F:.4f}, {state.feed['T_bubble_K']:.3f} K)",
                 f"{state.feed['H_V_sat']:.5f} kJ/mol"),
                ("$\\Delta H_{vap}$ of the mixture",
                 f"{state.feed['H_V_sat']:.5f} - {state.feed['h_L_sat']:.5f}",
                 f"{state.feed['H_V_sat'] - state.feed['h_L_sat']:.5f} kJ/mol"),
            ],
        )

    ch.prose(
        "For this binary the parameters are $B_{12} = 20.06$ K, "
        "$B_{21} = 832.98$ K and $\\alpha = 0.326$, with component 1 = IPA. "
        "**Component ordering must match the parameter source**; swapping $B_{12}$ "
        "and $B_{21}$ produces a plausible-looking curve with the azeotrope in the "
        "wrong place."
    )
    ch.caution(
        "Before using NRTL parameters outside this app, check their provenance, the "
        "temperature range of the regression, the units of $B_{ij}$ (K here, but "
        "cal/mol and J/mol are both common), and whether they were fitted with the "
        "same $\\gamma$&ndash;$\\phi$ assumption. Parameters extrapolated outside "
        "their regression range are the single most common source of confidently "
        "wrong VLE."
    )

    ch.self_check(
        "Why does the azeotrope make $\\gamma_i$ impossible to ignore?",
        "At an azeotrope $y_i = x_i$, so " + ch.ref("raoult") + " requires "
        "$\\gamma_i P_i^{sat} = P$ for *both* components simultaneously. With "
        "$\\gamma_i = 1$ that would demand $P_1^{sat} = P_2^{sat} = P$, i.e. both "
        "components boiling at the same temperature — which for IPA and water is "
        "false at every pressure. An azeotrope is therefore *only* possible with "
        "non-ideal $\\gamma$, and its existence is direct evidence that the "
        "activity coefficients matter."
    )
    ch.self_check(
        "What breaks if $h^E$ is dropped from " + ch.ref("hL") + "?",
        "The VLE and the energy model stop describing the same fluid. The saturated "
        "liquid curve shifts, so the difference points $\\Delta_D$ and $\\Delta_B$ "
        "move, so the Ponchon–Savarit lever rule returns wrong internal flows and "
        "the reboiler duty is biased. Since $h^E$ for IPA/water is of the order of "
        "a few hundred J/mol against a latent heat of ~40 kJ/mol, the error is "
        "small but systematic — the worst kind, because nothing looks wrong."
    )

    ch.heading("Implementation")
    ch.source("general N-component NRTL activity coefficients", "src/thermo.py", "nrtl_ln_gamma")
    ch.source("binary wrapper over the general form", "src/thermo.py", "nrtl_gamma")
    ch.source("excess enthalpy by complex-step Gibbs-Helmholtz", "src/thermo.py", "excess_enthalpy")
    ch.source("bubble residual and vectorised phase envelope", "src/thermo.py", "bubble_point_curve")
    ch.source("scalar bubble point for stage recurrences", "src/thermo.py", "bubble_point")
    ch.source("dew-point branch inversion", "src/thermo.py", "dew_point")
    ch.source("cached azeotrope root", "src/thermo.py", "find_azeotrope")
