"""Expandable, engineering-oriented tutorial content for the Streamlit UI."""

import streamlit as st


def _eq(text: str) -> None:
    st.latex(text)


def _diagram(title: str, body: str) -> None:
    st.markdown(f"**{title}**")
    st.code(body, language=None)


def render_tutorial() -> None:
    """Render a self-contained tutorial; it intentionally does not alter calculations."""
    st.header("📖 Engineering tutorial: from phase equilibrium to a safe column")
    st.info(
        "This is an educational design guide, not a replacement for validated property packages, "
        "relief-system design, HAZOP/LOPA, a licensed pressure-vessel design, or a process-safety review."
    )

    with st.expander("1 · Map of the problem and modelling assumptions", expanded=False):
        st.markdown(
            "A distillation column couples **phase equilibrium**, component balances, energy balances, "
            "hydraulics, heat transfer, and mechanical design. The simulator uses a binary IPA (1)/water (2) "
            "model at low-to-moderate pressure. It computes γ–φ equilibrium with liquid non-ideality from NRTL, "
            "ideal vapor behavior, and negligible pressure drop."
        )
        _diagram("Information flow", """Feed: F, z_F, P, h_F
        │
        ├── VLE: gamma_i(NRTL,T,x) · P_i^sat(T) ──> y_i, T_bubble
        ├── Enthalpy: h(x,T), H(y,T)              ──> q and tie-line energy
        └── Specifications: x_D, x_B, R           ──> stages, duties, internal flows
                                                        │
                                                        └── hydraulics / diameter / height / cost / safeguards""")
        st.markdown("**Core assumptions and their consequences**")
        st.markdown(
            "- Equilibrium stages: vapor and liquid leaving each ideal stage are at the same T, P and chemical potential. "
            "Real trays require Murphree efficiency; packing requires HETP/rate-based modelling.\n"
            "- Binary, nonreacting system: no dissolved gases, side draws, reaction, or entrainment in the balance model.\n"
            "- Ideal vapor (φᵢ≈1): usually reasonable near 1 atm; use an EOS/γ–φ or φ–φ model at elevated pressure.\n"
            "- Azeotrope: IPA/water has a minimum-boiling azeotrope, so ordinary distillation cannot cross the azeotropic composition at fixed pressure."
        )

    with st.expander("2 · Equilibrium relationship and NRTL derivation", expanded=False):
        st.markdown("At vapor–liquid equilibrium, each component has equal fugacity in both phases.")
        _eq(r"f_i^L=f_i^V\quad\Rightarrow\quad x_i\gamma_i P_i^{sat}(T)=y_i\phi_iP")
        st.markdown("With φᵢ≈1 and a negligible Poynting correction, this becomes the modified Raoult law used for bubble-point calculations.")
        _eq(r"y_i=\frac{x_i\gamma_iP_i^{sat}(T)}{P},\qquad \sum_i x_i\gamma_iP_i^{sat}(T)=P")
        st.markdown("**Why NRTL?** IPA/water is strongly non-ideal because hydrogen bonding makes unlike molecular neighborhoods energetically different. NRTL represents local composition rather than assuming random mixing.")
        _eq(r"\tau_{ij}=B_{ij}/T,\qquad G_{ij}=\exp(-\alpha_{ij}\tau_{ij})")
        _eq(r"\ln\gamma_i=\sum_j\frac{x_j\tau_{ji}G_{ji}}{\sum_kx_kG_{ki}}+\sum_j\frac{x_jG_{ij}}{\sum_kx_kG_{kj}}\left(\tau_{ij}-\frac{\sum_mx_m\tau_{mj}G_{mj}}{\sum_kx_kG_{kj}}\right)")
        st.markdown("For this binary, the model uses B₁₂=20.06 K, B₂₁=832.98 K and α=0.326 (component ordering must remain consistent with the parameter source). The code evaluates γ(T,x) at every equilibrium point; therefore y(x) is curved and an azeotrope can occur where y=x.")
        _diagram("Azeotrope diagnostic", """relative volatility alpha_12 = (y_1/x_1) / (y_2/x_2)
alpha_12 > 1  : IPA enriches in vapor
alpha_12 = 1  : y_1 = x_1  -> azeotrope / no composition driving force
alpha_12 < 1  : water enriches in vapor""")
        st.markdown("Check parameter provenance, temperature range, units, and whether parameters were fitted to γ–φ data before using them outside their regression range.")

    with st.expander("3 · Flash calculations: ideal, non-ideal, isothermal, isobaric, and adiabatic", expanded=False):
        st.markdown("A flash is one equilibrium contact. Let feed F split into L and V, with β=V/F. Component balances give")
        _eq(r"z_i=(1-\beta)x_i+\beta y_i,\qquad y_i=K_ix_i")
        _eq(r"x_i=\frac{z_i}{1+\beta(K_i-1)},\qquad \sum_i\frac{z_i(K_i-1)}{1+\beta(K_i-1)}=0")
        st.markdown("The last equation is Rachford–Rice. Solve it on 0≤β≤1; if no root exists, the feed is a single phase.")
        st.markdown("**Ideal isothermal–isobaric flash.** Use Kᵢ=Pᵢˢᵃᵗ(T)/P, solve Rachford–Rice, then recover x and y.\n\n**Non-ideal isothermal–isobaric flash.** Iterate Kᵢ←γᵢ(x,T)Pᵢˢᵃᵗ(T)/(φᵢP), re-solve Rachford–Rice, and converge both K and composition. Damping prevents oscillation near azeotropes.\n\n**Constant-T flash.** T and P are known; unknowns are β, x, y. Use the two equations above.\n\n**Constant-P bubble/dew calculation.** Bubble point solves ΣxᵢγᵢPᵢˢᵃᵗ(T)=P. Dew point solves ΣyᵢP/(γᵢPᵢˢᵃᵗ(T))=1 while updating x and γ.\n\n**Adiabatic flash.** Add the enthalpy balance Q=0:")
        _eq(r"Fh_F=V H(T,\mathbf y)+L h(T,\mathbf x)")
        st.markdown("Now T is unknown. An outer root solver varies T; at each trial T, the inner non-ideal flash supplies β, x, y, h and H. This is the same energy-balance logic that makes Ponchon–Savarit more general than constant-molar-overflow stepping.")
        _diagram("Robust non-ideal adiabatic flash algorithm", """guess T -> calculate K_i(T,x) -> solve Rachford-Rice for beta
   ^                                      │
   │                                      v
root on residual Fh_F - [V H + L h] <- update x,y,gamma
stop only when material, equilibrium, and energy residuals all converge""")

    with st.expander("4 · McCabe–Thiele: derivation, stepping, and limitations", expanded=False):
        st.markdown("McCabe–Thiele is a graphical binary-stage method. It replaces the full energy treatment with **constant molar overflow (CMO)**: comparable latent heats, negligible heat loss, negligible pressure drop, and nearly constant L and V within each section.")
        st.markdown("For a total condenser and reflux ratio R=L₀/D, the rectifying-section total/component balances give")
        _eq(r"V=L+D,\quad L=RD,\quad y_{n+1}=\frac{R}{R+1}x_n+\frac{x_D}{R+1}")
        st.markdown("For the stripping section, a balance below tray m yields")
        _eq(r"y_{m+1}=\frac{\bar L}{\bar V}x_m-\frac{B}{\bar V}x_B")
        st.markdown("The feed condition is encoded by q, the liquid fraction after an isenthalpic flash at column pressure. Combining feed and section balances gives the q-line:")
        _eq(r"y=\frac{q}{q-1}x-\frac{z_F}{q-1}")
        _diagram("One ideal-stage construction", """equilibrium curve y*=f(x)
       horizontal: operating line -> equilibrium curve (vapor leaving tray)
       vertical:   equilibrium curve -> operating line (liquid leaving tray)
repeat from x_D down to x_B; switch at q-line intersection""")
        st.markdown("At total reflux R→∞, operating lines approach y=x and the staircase gives N_min. At minimum reflux, the operating line pinches the equilibrium curve and N→∞. Practical R is selected between these limits after economics. **Do not use CMO blindly** for strongly non-ideal systems, large temperature spans, subcooled reflux, non-saturated feeds, or appreciable pressure drop; this app shows non-CMO flow profiles for that reason.")

    with st.expander("5 · Ponchon–Savarit: enthalpy-composition construction", expanded=False):
        st.markdown("Ponchon–Savarit retains the same equilibrium tie-lines but also carries molar enthalpy. Plot saturated-liquid h(x) and saturated-vapor H(y) at the operating pressure. Each tie-line joins the paired equilibrium liquid and vapor states.")
        _eq(r"Fh_F+D h_D+B h_B=Q_C+Q_R")
        st.markdown("Define the rectifying difference point Δ_D as the intersection implied by condenser/reflux balances and the stripping difference point Δ_B from reboiler/bottoms balances. A line from Δ_D through the vapor point on a tie-line locates the liquid point for a rectifying stage; the analogous line through Δ_B handles stripping stages.")
        _diagram("Ponchon–Savarit stage walk", r"""H (enthalpy)
^   saturated vapor curve H(y)      ΔD o
|      / tie-line ---------------------\
|     /                                 \  rectifying operating line
|  h(x) saturated liquid curve            o liquid stage point
|                              ΔB o
+------------------------------------------------> IPA mole fraction
Move tie-line <-> difference-point line until the feed tie-line is reached.""")
        st.markdown("This method naturally handles different latent heats, heat of mixing, feed enthalpy, subcooled reflux, and section-wise changing L/V. It still assumes equilibrium stages and a specified pressure; pressure profiles and tray efficiencies require additional models.")

    with st.expander("6 · From calculated stages to column diameter, height, utilities, and economics", expanded=False):
        st.markdown("**First scale the process.** Convert the simulator feed basis to kmol/h, calculate top and bottom vapor/liquid loads, and use the maximum vapor volumetric rate for diameter. Geometry is not determined by stage count alone.")
        _eq(r"\dot V_{vol}=\frac{\dot n_V ZRT}{P},\qquad A_{active}=\frac{\dot V_{vol}}{u_{design}},\qquad D_c=\sqrt{\frac{4A_{total}}{\pi}}")
        st.markdown(r"For trays, obtain u_design from a vendor correlation or a fair-diameter method (e.g., Souders–Brown) after accounting for liquid density, vapor density, foaming, surface tension, tray spacing and downcomer area. A common preliminary form is u_flood=C\sqrt{(ρ_L-ρ_V)/ρ_V}; use 70–85% of flooding only after checking entrainment, weeping, downcomer backup and allowable pressure drop. Do not apply a generic C blindly.")
        _eq(r"H_{shell}\approx N_{actual}\,s_{tray}+H_{top}+H_{bottom}+H_{allowance}")
        st.markdown("Typical preliminary tray spacing is 0.45–0.61 m, but final spacing follows access, fouling, maintenance and hydraulic design. For packing, calculate required transfer units (NTU) and height of a transfer unit (HTU): Z=HTU×NTU; check distributor quality, liquid turndown and packing pressure drop.")
        st.markdown("**Economics.** Annualized cost is the correct comparison, not purchased shell cost alone:")
        _eq(r"TAC=CRF(C_{column}+C_{condenser}+C_{reboiler}+C_{controls})+C_{steam}+C_{cooling}+C_{electricity}+C_{maintenance}")
        st.markdown("Increasing R lowers stage count but raises diameter, condenser duty and reboiler duty. Evaluate a small R sweep above R_min and select the minimum TAC subject to controllability and operability. Obtain current vendor quotes and utility rates; all cost correlations are location, material, pressure, index year, and capacity-range dependent.")

    with st.expander("7 · Safe operation, safeguards, and what this model does not certify", expanded=False):
        st.markdown("IPA is a **highly flammable liquid/vapor**; IPA/water vapor can create a flammable atmosphere. Treat this app’s calculated T, P, compositions and duties as inputs to a formal design review—not operating limits.")
        _diagram("Layered protection concept", """basic control: reflux, reboiler heat, pressure, level
        -> alarms + trained response
        -> interlocks / shutdown: high P, low reflux, low bottoms level, high reboiler temperature
        -> relief to a properly designed disposal system
        -> containment, ventilation, ignition control, emergency response""")
        st.markdown(
            "**Minimum engineering checks before operation**\n"
            "- Perform a HAZOP and, where appropriate, LOPA; include loss of cooling, loss of reflux, loss of utilities, blocked outlet, fire exposure, control-valve failure, and vacuum/condensation scenarios.\n"
            "- Size pressure/vacuum relief using the governing credible scenario; route flammable relief safely. A relief valve is not a substitute for controlling heat input.\n"
            "- Use suitable hazardous-area electrical classification, bonding/grounding, ventilation, leak detection, compatible seals/gaskets, and ignition-source control.\n"
            "- Protect reboilers from low liquid level and dry firing; protect condensers against cooling-water loss; verify reflux pump NPSH and minimum flow.\n"
            "- Establish operating envelopes for pressure, differential pressure, reflux ratio, temperatures, level, and composition. Trends help identify flooding (rising ΔP/entrainment), weeping (lost efficiency), foaming, or a developing heat-balance upset.\n"
            "- Write start-up, shutdown, sampling, maintenance, line-breaking, confined-space, and emergency procedures. Use the current safety data sheet and local regulations."
        )

    with st.expander("8 · Assumptions, validation checklist, and references", expanded=False):
        st.markdown(
            "**Validate before relying on results:** reconcile overall/component/energy balances; check 0≤x,y≤1; verify stage monotonicity; compare VLE against measured IPA/water data; assess NRTL parameter range; benchmark an independent property package; and sensitivity-test feed condition, pressure, efficiency, heat loss, and reflux ratio.\n\n"
            "**References**\n"
            "- [NIST Chemistry WebBook: isopropyl alcohol](https://webbook.nist.gov/cgi/cbook.cgi?ID=C67630&Mask=4) and [water](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=4) — property-data cross-checks.\n"
            "- [Renon & Prausnitz (1968), NRTL original paper](https://doi.org/10.1002/aic.690140124).\n"
            "- [Seader, Henley & Roper, Separation Process Principles](https://www.wiley.com/en-us/Separation+Process+Principles%3A+Chemical+and+Biochemical+Operations%2C+4th+Edition-p-9781119327881) — flash, stages, McCabe–Thiele and Ponchon–Savarit.\n"
            "- [AIChE CCPS resources](https://www.aiche.org/ccps) — process-safety management and layers of protection.\n"
            "- [OSHA flammable-liquid standard](https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.106).\n\n"
            "The NRTL constants and pure-component correlations used by this app are documented in `data/` and `src/thermo.py`; retain their source files with any published result."
        )
