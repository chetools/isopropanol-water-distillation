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
        st.markdown(r"""
**Step 1 — choose a basis and draw the outer envelope.** Take one second as the
basis because the UI uses mol/s. Streams crossing the envelope are feed
$F,z_F,h_F$, distillate $D,x_D,h_D$, bottoms $B,x_B,h_B$, condenser heat
$Q_C$ leaving, and reboiler heat $Q_R$ entering.
""")
        _diagram("Whole-column balance envelope", """                         Q_C out
                            ↑
             D, x_D, h_D ← [ CONDENSER ]
                              │ reflux
F, z_F, h_F ───────────────> [  COLUMN  ]
                              │
             B, x_B, h_B ← [ REBOILER  ]
                            ↑
                         Q_R in""")
        st.markdown("**Step 2 — close independent balances before solving stages.**")
        _eq(r"F=D+B")
        _eq(r"Fz_F=Dx_D+Bx_B")
        _eq(r"Fh_F+Q_R=Dh_D+Bh_B+Q_C")
        st.markdown(r"""
The first two equations give $D=F(z_F-x_B)/(x_D-x_B)$ and $B=F-D$. The energy
balance supplies one relation between the two duties; the specified reflux or
a condenser/reboiler model supplies the other. A degree-of-freedom audit must
precede numerical solution: each independent specification removes one degree
of freedom, while redundant product-rate specifications can contradict the
component balance.

**Step 3 — move inward.** Each equilibrium stage contributes two component
balances, one energy balance, two summation constraints, and phase-equilibrium
relations. Temperatures, compositions and internal flows are therefore solved
together; a plotted staircase alone is not a complete MESH solution.
""")

    with st.expander("2 · Equilibrium relationship and NRTL derivation", expanded=False):
        st.markdown("At vapor–liquid equilibrium, each component has equal fugacity in both phases.")
        _eq(r"f_i^L=f_i^V\quad\Rightarrow\quad x_i\gamma_i P_i^{sat}(T)=y_i\phi_iP")
        st.markdown("With φᵢ≈1 and a negligible Poynting correction, this becomes the modified Raoult law used for bubble-point calculations.")
        _eq(r"y_i=\frac{x_i\gamma_iP_i^{sat}(T)}{P},\qquad \sum_i x_i\gamma_iP_i^{sat}(T)=P")
        st.markdown("**Why NRTL?** IPA/water is strongly non-ideal because hydrogen bonding makes unlike molecular neighborhoods energetically different. NRTL represents local composition rather than assuming random mixing.")
        _eq(r"\tau_{ij}=B_{ij}/T,\qquad G_{ij}=\exp(-\alpha_{ij}\tau_{ij})")
        _eq(r"\ln\gamma_i=\sum_j\frac{x_j\tau_{ji}G_{ji}}{\sum_kx_kG_{ki}}+\sum_j\frac{x_jG_{ij}}{\sum_kx_kG_{kj}}\left(\tau_{ij}-\frac{\sum_mx_m\tau_{mj}G_{mj}}{\sum_kx_kG_{kj}}\right)")
        st.markdown(r"""
**Derivation, one thermodynamic layer at a time**

1. Chemical equilibrium requires $\mu_i^L=\mu_i^V$. Because
$\mu_i=\mu_i^\circ+RT\ln f_i$, equality of chemical potential is equality of
fugacity.
2. Write vapor fugacity as $f_i^V=y_i\phi_iP$. Write liquid fugacity relative
to pure saturated liquid as
$f_i^L=x_i\gamma_iP_i^{sat}\exp[\int_{P_i^{sat}}^P v_i^L dP/(RT)]$.
3. Near atmospheric pressure the Poynting exponential is nearly one and the
vapor fugacity coefficient is nearly one. Cancelling the reference states
produces modified Raoult's law—not ordinary Raoult's law, because $\gamma_i$
remains.
4. NRTL begins with a molar excess Gibbs-energy expression. Differentiate
$n g^E/(RT)$ with respect to component mole number at fixed $T,P,n_{j\ne i}$;
the result is $\ln\gamma_i$. Thus activity coefficients are thermodynamic
derivatives, not curve-fitting multipliers attached after the balance.
""")
        _eq(r"\frac{g^E}{RT}=\sum_i x_i\frac{\sum_jx_j\tau_{ji}G_{ji}}{\sum_kx_kG_{ki}},\qquad \ln\gamma_i=\left[\frac{\partial(n g^E/RT)}{\partial n_i}\right]_{T,P,n_j}")
        st.markdown(r"""
For the binary form, insert $x_2=1-x_1$, evaluate $\tau_{12},\tau_{21}$ and
$G_{12},G_{21}$, then calculate both $\gamma$ values. At a trial temperature
form the bubble residual
$r(T)=x_1\gamma_1P_1^{sat}+x_2\gamma_2P_2^{sat}-P$. Bracket the two pure boiling
points, solve $r(T)=0$, and finally calculate $y_i$. Verify $\sum y_i=1$ and
repeat across $x_1\in[0,1]$. The azeotrope is a second root problem,
$y_1(x_1)-x_1=0$.

**Energy consistency.** If $\tau_{ij}$ depends on temperature, NRTL also
contributes excess enthalpy. Gibbs–Helmholtz gives
""")
        _eq(r"h^E=-RT^2\left[\frac{\partial(g^E/RT)}{\partial T}\right]_{P,\mathbf{x}}=-RT^2\sum_i x_i\frac{\partial\ln\gamma_i}{\partial T}")
        st.markdown("That term belongs in the saturated-liquid enthalpy curve used by Ponchon–Savarit; omitting it makes the VLE and energy model internally inconsistent.")
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
        _diagram("Flash balance envelope", """                   Q (zero for adiabatic)
                   ↓
F, z_i, h_F ---> [ FLASH ] ---> V=beta F, y_i, H
                    │
                    └----------> L=(1-beta)F, x_i, h""")
        st.markdown(r"""
**Deriving Rachford–Rice rather than quoting it.** Start with
$Fz_i=Lx_i+Vy_i$. Divide by $F$, substitute $L/F=1-\beta$ and $y_i=K_ix_i$:
$z_i=x_i[1+\beta(K_i-1)]$. Isolate $x_i$. Then impose both phase summations.
Subtracting $\sum x_i=1$ from $\sum y_i=1$ produces the scalar equation shown
above. Its derivative is always non-positive between singularities, so a
bracketed root is robust.

**Phase test before solving.** Evaluate $g(0)=\sum z_i(K_i-1)$ and
$g(1)=\sum z_i(K_i-1)/K_i$. If both are negative the stable result is liquid;
if both are positive it is vapor; opposite signs indicate a two-phase root.
""")
        st.markdown("The last equation is Rachford–Rice. Solve it on 0≤β≤1; if no root exists, the feed is a single phase.")
        st.markdown("**Ideal isothermal–isobaric flash.** Use Kᵢ=Pᵢˢᵃᵗ(T)/P, solve Rachford–Rice, then recover x and y.\n\n**Non-ideal isothermal–isobaric flash.** Iterate Kᵢ←γᵢ(x,T)Pᵢˢᵃᵗ(T)/(φᵢP), re-solve Rachford–Rice, and converge both K and composition. Damping prevents oscillation near azeotropes.\n\n**Constant-T flash.** T and P are known; unknowns are β, x, y. Use the two equations above.\n\n**Constant-P bubble/dew calculation.** Bubble point solves ΣxᵢγᵢPᵢˢᵃᵗ(T)=P. Dew point solves ΣyᵢP/(γᵢPᵢˢᵃᵗ(T))=1 while updating x and γ.\n\n**Adiabatic flash.** Add the enthalpy balance Q=0:")
        _eq(r"Fh_F=V H(T,\mathbf y)+L h(T,\mathbf x)")
        st.markdown("Now T is unknown. An outer root solver varies T; at each trial T, the inner non-ideal flash supplies β, x, y, h and H. This is the same energy-balance logic that makes Ponchon–Savarit more general than constant-molar-overflow stepping.")
        _diagram("Robust non-ideal adiabatic flash algorithm", """guess T -> calculate K_i(T,x) -> solve Rachford-Rice for beta
   ^                                      │
   │                                      v
root on residual Fh_F - [V H + L h] <- update x,y,gamma
stop only when material, equilibrium, and energy residuals all converge""")
        st.markdown(r"""
**Five flash specifications and their unknowns**

1. **Ideal TP flash:** $T,P,z$ known. Calculate ideal $K_i$, phase-test, solve
$\beta$, then $x,y$.
2. **Non-ideal TP flash:** $T,P,z$ known. Initialize $\gamma=1$; alternate the
Rachford–Rice solve and NRTL update until both composition and $K$ stop moving.
3. **Bubble T at fixed P,x:** set $\beta=0$ and root the bubble residual in T.
4. **Dew T at fixed P,y:** set $\beta=1$; iterate liquid composition because
$\gamma$ depends on the unknown $x$, while rooting the dew residual in T.
5. **Adiabatic PH flash:** $P,z,h_F$ known. For each outer trial T, perform the
complete non-ideal TP flash, calculate $h_{out}=(1-\beta)h+\beta H$, and root
$h_F-h_{out}=0$. The outer residual must include heat of mixing and latent
heat on the same reference state.

For a **constant-T, variable-P** flash, pressure is an unknown instead: outer-root
P while the inner composition loop closes equilibrium. Never update T, P,
$\beta$, and $\gamma$ with an unguarded simultaneous fixed-point iteration near
an azeotrope; bracket the outer scalar variable and damp the inner activity update.
""")

    with st.expander("4 · McCabe–Thiele: derivation, stepping, and limitations", expanded=False):
        st.markdown("McCabe–Thiele is a graphical binary-stage method. It replaces the full energy treatment with **constant molar overflow (CMO)**: comparable latent heats, negligible heat loss, negligible pressure drop, and nearly constant L and V within each section.")
        st.markdown("For a total condenser and reflux ratio R=L₀/D, the rectifying-section total/component balances give")
        _diagram("Rectifying-section envelope", """       V_(n+1), y_(n+1) enters from below
                     ↑
                [ trays 1..n ] ---> D, x_D
                     ↓
          L_n, x_n leaves downward
Envelope balance: V y_(n+1) = L x_n + D x_D""")
        _eq(r"V=L+D,\quad L=RD,\quad y_{n+1}=\frac{R}{R+1}x_n+\frac{x_D}{R+1}")
        st.markdown(r"""
The derivation is direct: total balance gives $V=L+D$; component balance gives
$Vy_{n+1}=Lx_n+Dx_D$. Divide by V, substitute $L=RD$ and $V=(R+1)D$, then
cancel D. The slope is therefore $R/(R+1)$ and the intercept is $x_D/(R+1)$.
Both follow from the envelope; neither is a fitted line.
""")
        st.markdown("For the stripping section, a balance below tray m yields")
        _eq(r"y_{m+1}=\frac{\bar L}{\bar V}x_m-\frac{B}{\bar V}x_B")
        _diagram("Stripping-section envelope", """          Lbar_m, x_m enters from above
                     ↓
                [ trays m..N ]
                     ↑
       Vbar_(m+1), y_(m+1) leaves upward ---> B, x_B leaves bottom
Envelope balance: Lbar x_m = Vbar y_(m+1) + B x_B""")
        st.markdown("Solve the displayed component balance for vapor composition to obtain the stripping line. It must pass through (x_B,x_B) for a partial reboiler counted as an equilibrium stage.")
        st.markdown("The feed condition is encoded by q, the liquid fraction after an isenthalpic flash at column pressure. Combining feed and section balances gives the q-line:")
        _eq(r"y=\frac{q}{q-1}x-\frac{z_F}{q-1}")
        st.markdown(r"""
Across the feed tray, $\bar L=L+qF$ and $\bar V=V-(1-q)F$. Combine those
relations with $Fz_F=\bar Lx-Lx+Vy-\bar Vy$ and eliminate the internal flows;
the locus of admissible feed-tray intersections is the q-line. Limiting cases:
$q=1$ vertical saturated-liquid line, $q=0$ horizontal saturated-vapor line,
$0<q<1$ two-phase feed, $q>1$ subcooled liquid, and $q<0$ superheated vapor.
""")
        _diagram("One ideal-stage construction", """equilibrium curve y*=f(x)
       horizontal: operating line -> equilibrium curve (vapor leaving tray)
       vertical:   equilibrium curve -> operating line (liquid leaving tray)
repeat from x_D down to x_B; switch at q-line intersection""")
        st.markdown("At total reflux R→∞, operating lines approach y=x and the staircase gives N_min. At minimum reflux, the operating line pinches the equilibrium curve and N→∞. Practical R is selected between these limits after economics. **Do not use CMO blindly** for strongly non-ideal systems, large temperature spans, subcooled reflux, non-saturated feeds, or appreciable pressure drop; this app shows non-CMO flow profiles for that reason.")

    with st.expander("5 · Ponchon–Savarit: enthalpy-composition construction", expanded=False):
        st.markdown("Ponchon–Savarit retains the same equilibrium tie-lines but also carries molar enthalpy. Plot saturated-liquid h(x) and saturated-vapor H(y) at the operating pressure. Each tie-line joins the paired equilibrium liquid and vapor states.")
        _eq(r"Fh_F+D h_D+B h_B=Q_C+Q_R")
        _diagram("Single equilibrium-stage MESH envelope", """L_(n-1), x_(n-1), h_(n-1) ↓     ↑ V_n, y_n, H_n
                               [ STAGE n ]
L_n, x_n, h_n ↓                         ↑ V_(n+1), y_(n+1), H_(n+1)

total:    L_(n-1)+V_(n+1)=L_n+V_n
component:L_(n-1)x_(n-1)+V_(n+1)y_(n+1)=L_n x_n+V_n y_n
energy:   L_(n-1)h_(n-1)+V_(n+1)H_(n+1)=L_n h_n+V_n H_n""")
        st.markdown(r"""
**Step 1 — construct thermodynamically paired curves.** For each liquid $x$,
solve its bubble temperature and equilibrium vapor $y$. Evaluate $h(x,T)$ and
$H(y,T)$ on the same reference state. Join each paired point with a tie-line.

**Step 2 — derive the rectifying difference point.** A balance around the
condenser and all trays above stage n can be rearranged by subtracting the
distillate stream from the two counter-current internal streams. The invariant
difference is $V_{n+1}-L_n=D$ and its enthalpy coordinate is
""")
        _eq(r"h_{\Delta D}=\frac{V_{n+1}H_{n+1}-L_nh_n}{V_{n+1}-L_n}=h_D+\frac{Q_C}{D}")
        st.markdown(r"""
Every rectifying operating line must therefore pass through $\Delta_D$ and the
two stage points. Collinearity is the graphical statement of both component
and energy balance; the lever rule on the line returns L and V.

**Step 3 — derive the stripping difference point.** The lower envelope gives
$L_m-V_{m+1}=B$ and
""")
        _eq(r"h_{\Delta B}=\frac{L_mh_m-V_{m+1}H_{m+1}}{L_m-V_{m+1}}=h_B-\frac{Q_R}{B}")
        st.markdown(r"""
**Step 4 — step stages.** Start at distillate composition. (a) Follow the
equilibrium tie-line between saturated vapor and liquid curves. (b) Draw a
line from that point through the appropriate difference point. (c) Its
intersection with the opposite enthalpy curve locates the next stage. Switch
from $\Delta_D$ to $\Delta_B$ when the construction crosses the feed line.
(d) Repeat until $x_B$; interpolate the final step for a fractional stage.

The feed line passes through the feed point $(z_F,h_F)$ and both difference
points. Failure of those three points to align is an energy-balance closure
error. Unlike McCabe–Thiele, changing latent heat, heat of mixing, subcooling,
and changing L/V appear explicitly rather than being buried in CMO.
""")
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
        _diagram("Automated sizing chain used on this dashboard", """maximum stage V,T,y + P ---> vapor density and volume flow
                                    |
                                    v
capacity factor + densities ---> flood velocity ---> design velocity
                                    |
                                    v
active area + downcomer allowance ---> diameter

actual trays + spacing + end allowances ---> tangent height
Q_C,Q_R + U + LMTD ---------------------> exchanger areas
shell mass + trays + exchangers --------> purchased and installed cost
duties + hours + utility tariffs -------> OPEX and TAC""")
        st.markdown("**Step 1 — governing vapor load.** Inspect every calculated stage rather than assuming the top tray governs. Convert the largest molar vapor rate to actual volumetric rate at that stage’s T, P and vapor molecular weight.")
        _eq(r"\dot V_{vol}=\frac{\dot n_V ZRT}{P},\qquad A_{active}=\frac{\dot V_{vol}}{u_{design}},\qquad D_c=\sqrt{\frac{4A_{total}}{\pi}}")
        st.markdown("**Step 2 — flood velocity and diameter.** Estimate densities, obtain an appropriate tray capacity factor C, calculate Souders–Brown flood velocity, multiply by the selected flood fraction, divide vapor volume by design velocity for active area, and divide by (1−downcomer fraction) for total area.")
        st.markdown(r"For trays, obtain u_design from a vendor correlation or a fair-diameter method (e.g., Souders–Brown) after accounting for liquid density, vapor density, foaming, surface tension, tray spacing and downcomer area. A common preliminary form is u_flood=C\sqrt{(ρ_L-ρ_V)/ρ_V}; use 70–85% of flooding only after checking entrainment, weeping, downcomer backup and allowable pressure drop. Do not apply a generic C blindly.")
        _eq(r"H_{shell}\approx N_{actual}\,s_{tray}+H_{top}+H_{bottom}+H_{allowance}")
        st.markdown("**Step 3 — height and shell.** Convert equilibrium stages to actual trays with efficiency before applying tray spacing. Add top disengagement, bottom liquid inventory, feed-zone allowance and access. The dashboard’s thin-wall pressure calculation is only a preliminary thickness screen; heads, wind/seismic loads, vacuum, nozzles, supports, fatigue and code minimums require a mechanical design.")
        _eq(r"t_p=\frac{P_DD}{2SE-1.2P_D},\qquad t=\max(t_{minimum},t_p+c_A)")
        st.markdown("**Step 4 — heat exchangers.** Use the simulator duties, but require the user to state U and LMTD. Each assumption is exposed because fouling, phase regime and utility temperatures dominate area.")
        _eq(r"A_C=\frac{|Q_C|}{U_C\Delta T_{lm,C}},\qquad A_R=\frac{|Q_R|}{U_R\Delta T_{lm,R}}")
        st.markdown("Typical preliminary tray spacing is 0.45–0.61 m, but final spacing follows access, fouling, maintenance and hydraulic design. For packing, calculate required transfer units (NTU) and height of a transfer unit (HTU): Z=HTU×NTU; check distributor quality, liquid turndown and packing pressure drop.")
        st.markdown("**Economics.** Annualized cost is the correct comparison, not purchased shell cost alone:")
        _eq(r"TAC=CRF(C_{column}+C_{condenser}+C_{reboiler}+C_{controls})+C_{steam}+C_{cooling}+C_{electricity}+C_{maintenance}")
        _eq(r"CRF=\frac{i(1+i)^n}{(1+i)^n-1},\qquad C_{utility}=|Q|\,t_{op}\,(0.0036\;\mathrm{GJ/kWh})\,p_{utility}")
        st.markdown(r"""
**Step 5 — transparent cost sequence used here.** (a) scale shell, trays and
exchangers with sub-linear capacity exponents; (b) multiply by material factor
and project/base cost-index ratio; (c) apply the displayed installation factor;
(d) add controls/contingency; (e) calculate annual steam, cooling and
maintenance; (f) annualize capital with CRF; (g) add annual OPEX to obtain TAC.
This is a class-4 screening estimate, expected uncertainty roughly ±30–50%.
Replace defaults with current vendor quotes, a traceable cost index, local
utility tariffs, metallurgy, pressure class and site factors before making a
capital decision.
""")
        st.markdown("Increasing R lowers stage count but raises diameter, condenser duty and reboiler duty. Evaluate a small R sweep above R_min and select the minimum TAC subject to controllability and operability. Obtain current vendor quotes and utility rates; all cost correlations are location, material, pressure, index year, and capacity-range dependent.")

    with st.expander("7 · Safe operation, safeguards, and what this model does not certify", expanded=False):
        st.markdown("IPA is a **highly flammable liquid/vapor**; IPA/water vapor can create a flammable atmosphere. Treat this app’s calculated T, P, compositions and duties as inputs to a formal design review—not operating limits.")
        _diagram("Layered protection concept", """basic control: reflux, reboiler heat, pressure, level
        -> alarms + trained response
        -> interlocks / shutdown: high P, low reflux, low bottoms level, high reboiler temperature
        -> relief to a properly designed disposal system
        -> containment, ventilation, ignition control, emergency response""")
        _diagram("Normal control structure and upset propagation", """pressure controller ---> condenser duty / vent system
reflux-drum level -------> distillate flow
column base level -------> bottoms flow
temperature/composition -> reboiler duty or reflux ratio

loss of cooling -> pressure rises -> alarm -> cut heat -> shutdown -> relief (last resort)
loss of reflux  -> top temperature rises, separation lost -> alarm/interlock
low base level  -> reboiler dry-out risk -> low-low trip removes heat""")
        st.markdown(r"""
**Safeguard derivation starts with inventory and energy, not a checklist.** For
each deviation, identify (1) initiating cause, (2) how mass or energy
accumulates, (3) the measurable consequence, (4) independent prevention, and
(5) independent mitigation. Example: cooling loss removes $Q_C$ while $Q_R$
continues, so vapor inventory and pressure rise. Pressure control may demand
more cooling but cannot restore a failed utility; a high-pressure alarm prompts
response, an independent trip removes reboiler heat, and a relief device sized
for the credible residual generation rate protects containment.

**Relief envelope:** blocked outlets require vapor-generation and thermal
expansion checks; external fire requires wetted-area heat input; tube rupture
requires upstream pressure/area analysis; condensation or steam-out can create
vacuum. Determine required relief rate from the governing mass/energy balance,
then design inlet/outlet pressure losses and disposal—not just valve orifice.
""")
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
        st.markdown(r"""
**Numerical acceptance criteria for an auditable run**

- Overall balance residual $|F-D-B|/F$ and IPA residual
$|Fz_F-Dx_D-Bx_B|/(Fz_F)$ should be reported near solver tolerance.
- Every stage must satisfy total, component and energy residuals on its own
envelope; global closure can hide equal-and-opposite stage errors.
- $\sum x_i=\sum y_i=1$, phase fractions stay in [0,1], and bubble/dew roots
must be bracketed in a physically valid temperature interval.
- Recalculate selected states with an independent property package or measured
VLE. A visually smooth curve is not validation.
- Hydraulic design must be checked at normal, turndown, maximum throughput,
start-up and upset conditions. Economics must state currency, cost-index date,
location, installation scope and uncertainty class.
""")
