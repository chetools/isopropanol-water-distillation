"""Chapter 0 - nomenclature, sign conventions, and how to read the code."""

import streamlit as st

from src.tutorial.layout import nomenclature_table, sign_convention_box

SYMBOLS = [
    ("$F,\\;D,\\;B$", "Feed, distillate, bottoms molar flow", "mol/s", "§1"),
    ("$z_F,\\;x_D,\\;x_B$", "IPA mole fraction in feed, distillate, bottoms", "mole fraction", "§1"),
    ("$x_i,\\;y_i$", "Liquid and vapour mole fraction of component $i$", "mole fraction", "§2"),
    ("$L_n,\\;V_n$", "Internal liquid and vapour flow leaving stage $n$", "mol/s", "§5"),
    ("$R$", "External reflux ratio, $L_0/D$", "mol/mol", "§4"),
    ("$q$", "Feed liquid fraction after isenthalpic flash", "dimensionless", "§4"),
    ("$P,\\;P_i^{sat}$", "System pressure; pure-component vapour pressure", "Pa", "§2"),
    ("$T$", "Absolute temperature", "K", "§2"),
    ("$\\gamma_i$", "Activity coefficient of component $i$ in the liquid", "dimensionless", "§2"),
    ("$\\phi_i$", "Fugacity coefficient of component $i$ in the vapour", "dimensionless", "§2"),
    ("$K_i$", "Equilibrium ratio $y_i/x_i$", "dimensionless", "§3"),
    ("$\\beta$", "Vapour fraction $V/F$ of a flash", "dimensionless", "§3"),
    ("$\\tau_{ij},\\;G_{ij},\\;\\alpha$", "NRTL interaction, non-randomness matrices and parameter", "dimensionless", "§2"),
    ("$g^E,\\;h^E$", "Molar excess Gibbs energy and excess enthalpy", "kJ/mol", "§2"),
    ("$h_L(x,T)$", "Saturated-liquid molar enthalpy", "kJ/mol", "§2"),
    ("$H_V(y,T)$", "Saturated-vapour molar enthalpy", "kJ/mol", "§2"),
    ("$Q_C,\\;Q_R$", "Condenser and reboiler duty (positive magnitudes)", "kW", "§1"),
    ("$\\Delta_D,\\;\\Delta_B$", "Rectifying and stripping difference points", "—", "§5"),
    ("$Q'_D,\\;Q'_B$", "Enthalpy coordinates of $\\Delta_D$ and $\\Delta_B$", "kJ/mol", "§5"),
    ("$N,\\;N_{min},\\;N_F$", "Equilibrium stages, total-reflux minimum, feed stage", "stages", "§4"),
    ("$R_{min}$", "Minimum reflux ratio (pinched operating line)", "mol/mol", "§4"),
    ("$E_{MV}$", "Murphree vapour-phase stage efficiency", "fraction", "§6"),
    ("$u_{flood},\\;C$", "Souders-Brown flooding velocity and capacity factor", "m/s", "§6"),
    ("$D_c,\\;H_{shell},\\;t$", "Column diameter, tangent height, shell thickness", "m", "§6"),
    ("$U,\\;\\Delta T_{lm},\\;A$", "Overall coefficient, log-mean difference, area", "kW/m²K, K, m²", "§6"),
    ("$CRF,\\;TAC$", "Capital recovery factor; total annualised cost", "1/y, USD/y", "§6"),
]


def render(state=None) -> None:
    st.markdown(
        "Every symbol used in this tutorial, with the **canonical unit the solver "
        "actually stores**. The unit selectors in the interface convert only for "
        "display; nothing inside `src/` ever sees anything but the units below."
    )
    nomenclature_table(SYMBOLS)

    st.markdown("#### Sign and reference conventions")
    sign_convention_box()

    st.markdown("#### Reading the code as mathematics")
    st.markdown(
        "The calculation modules are written so that a reader arriving from an "
        "equation recognises the code, and vice versa. Three conventions make that "
        "possible, and they are worth knowing before opening any source link:"
    )
    st.markdown(
        "1. **The component index is the last array axis.** A composition is "
        "`x[..., i]`; an interaction matrix is `tau[..., i, j]`. Leading axes are "
        "grid axes, so one call evaluates a model at every point of a temperature "
        "or composition sweep simultaneously.\n"
        "2. **Summations are contractions.** `np.einsum` subscripts *are* the "
        "summation indices of the printed equation: $\\sum_k x_k G_{ki}$ is written "
        "`einsum(\"...k,...ki->...i\", x, G)` and can be checked term by term.\n"
        "3. **The only surviving loops are iteration schemes.** Interval halving and "
        "fixed-point updates stay as loops because they *are* the numerical method. "
        "Loops that merely walked over grid points have been removed."
    )
    st.markdown(
        "There is one important exception, and it is physics rather than style: "
        "**stage-to-stage construction is a recurrence.** Stage $n+1$ cannot be "
        "computed until stage $n$ is known, so the Ponchon–Savarit stepping, the "
        "McCabe–Thiele staircase and the minimum-stage count remain sequential "
        "loops. The array operations live *inside* each step, not across steps. "
        "Recognising which calculations are independent evaluations and which are "
        "recurrences is a genuinely useful habit — it is the same distinction that "
        "decides what can be parallelised in any simulation."
    )
