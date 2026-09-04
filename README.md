# Isopropanol / Water Rigorous Distillation Simulator

A standalone Streamlit application for the rigorous design and simulation of an
isopropanol / water distillation column — with a full step-by-step engineering
tutorial built into the app.

**Public app:** [IPA/Water Rigorous Distillation Simulator](https://chetools-isopropanol-water-distillation-app-ofszvm.streamlit.app/)

[![Deploy with Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=chetools/isopropanol-water-distillation&branch=main&mainModule=app.py)

---

## What it does

The interface is a persistent KPI strip above five tabs:

| Tab | Contents |
|---|---|
| **⚗ Design** | Stage-by-stage solution table, product states, CSV export |
| **📊 Diagrams** | McCabe–Thiele, T-x-y, Ponchon–Savarit, non-CMO internal flows |
| **🏗 Sizing & economics** | Diameter, height, shell, exchanger areas, capital and TAC |
| **🔍 Audit** | 19-step KPI ledger, unrounded stage states, links to source lines |
| **📖 Learn** | Nine-chapter tutorial with numbered equations and derivations |

Display units are chosen **once** in the sidebar's *Display units* panel and
apply everywhere. The solver never sees them: everything inside `src/` is
mol/s, Pa, K, kJ/mol and metres.

### Engineering features

1. **Ponchon–Savarit (H-x-y)** — saturated liquid $h_L(x)$ and vapour $H_V(y)$
   curves, difference points $\Delta_D$ and $\Delta_B$, the exact collinear
   $\Delta_D$–$F$–$\Delta_B$ line, tie lines and construction rays.
2. **Constant-P VLE (T-x-y)** — bubble and dew curves with the minimum-boiling
   azeotrope located by root-find rather than hardcoded.
3. **McCabe–Thiele (x-y)** — equilibrium curve, operating lines, q-line and an
   independent CMO staircase (deliberately *not* reusing the Ponchon–Savarit
   stage coordinates).
4. **Non-CMO internal flow profiles** — $L_n$ and $V_n$ from the Ponchon–Savarit
   lever rule, showing the feed-stage jump.
5. **Specification locker** — exactly two degrees of freedom across
   $x_D, x_B, D, B, R, Q_C, Q_R$ and the two key recoveries, with azeotrope and
   feasibility clamping.
6. **Design and Rating modes** — stage stepping to a purity target, or a fixed
   tray count.
7. **Preliminary sizing and economics** — Souders–Brown diameter, height
   stack-up, shell thickness screen, exchanger areas, installed capital and
   total annualised cost, with a downloadable calculation ledger.
8. **Nine-chapter tutorial** — see below.

---

## The tutorial

`src/tutorial/` is one module per chapter, so each is reviewable in a diff and
equation numbering stays local to its chapter.

| Chapter | Covers |
|---|---|
| 0 | Nomenclature, sign conventions, how to read the code as mathematics |
| 1 | The outer envelope, three balances, and why the DOF budget is exactly two |
| 2 | Fugacity → modified Raoult; NRTL derived by differentiating $g^E$; $h^E$ from Gibbs–Helmholtz |
| 3 | Rachford–Rice derived and proved monotonic; the five flash specifications |
| 4 | Both operating lines; the q-line elimination in full; $R_{min}$ and $N_{min}$ |
| 5 | The difference point as an invariant; the collinearity proof; the lever rule |
| 6 | Souders–Brown from a droplet force balance; CRF from the annuity series |
| 7 | Safeguards derived from the unsteady energy balance; the relief envelope |
| 8 | Numerical acceptance criteria and referenced sources |

Each chapter carries learning objectives, a step-by-step derivation, numbered
and cross-referenced equations, captioned vector figures, an
assumption/consequence/failure-mode table, self-check questions with hidden
answers, and — where the equation has just been derived — a **worked example
substituting the current run's own numbers**.

Fifteen SVG diagrams are generated in `src/engineering_diagrams.py`; a test
asserts none is orphaned.

---

## Reading the code as mathematics

The calculation modules are written so that a reader arriving from an equation
recognises the code. Three conventions:

1. **The component index is the last array axis.** A composition is `x[..., i]`,
   an interaction matrix `tau[..., i, j]`. Leading axes are grid axes, so one
   call evaluates a model across a whole sweep.
2. **Summations are contractions.** `np.einsum` subscripts are the summation
   indices of the printed equation:

   $$\ln\gamma_i=\frac{C_i}{S_i}+\sum_j \frac{x_j G_{ij}}{S_j}\left(\tau_{ij}-\frac{C_j}{S_j}\right)$$

   ```python
   S = np.einsum("...k,...ki->...i", x, G)          # S_i = sum_k x_k G_ki
   C = np.einsum("...m,...mj->...j", x, tau * G)    # C_j = sum_m x_m tau_mj G_mj
   r = C / S
   return r + np.einsum("...ij,...j->...i", G * (tau - r[..., None, :]), x / S)
   ```

3. **The only surviving loops are iteration schemes** — interval halving,
   fixed-point updates. Loops that merely walked over grid points are gone.

**The deliberate exception is physics, not style.** Stage-to-stage construction
is a *recurrence*: stage $n+1$ cannot be computed before stage $n$. The
Ponchon–Savarit stepping, the McCabe–Thiele staircase and the minimum-stage
count therefore remain sequential; the array operations live inside each step.

Solver choice follows the same logic. `bubble_point_curve` solves the whole
composition grid by simultaneous interval halving (every iteration does useful
work at every point); the scalar `bubble_point` used inside the recurrences uses
Brent's method, which reaches machine precision in far fewer residual
evaluations for a single root.

`excess_enthalpy` takes $\partial\ln\gamma_i/\partial T$ by **complex-step
differentiation**, so the code states Gibbs–Helmholtz directly. This requires
the NRTL chain to stay analytic in $T$ — no `abs`, `clip` or comparison may
touch the complex temperature.

---

## Thermodynamic data source

All parameters come strictly from `chetools/chetools/data`:

- Isopropanol (ID 145): `data/IsopropanolProps.txt`
- Water (ID 62): `data/WaterProps.txt`
- NRTL binary interaction parameters: `data/BinaryNRTL.txt`
  (30 water, 36 IPA: $B_{12} = 20.06\,\mathrm{K}$, $B_{21} = 832.98\,\mathrm{K}$,
  $\alpha = 0.326$; component 1 = IPA — ordering must match the source)
- Reference state: pure saturated liquid at $25\,^\circ\mathrm{C}$
  ($298.15\,\mathrm{K}$), where $h_{L,i} = 0$
- Excess enthalpy: analytical $h^E(x,T)$ from the NRTL temperature dependence

---

## Running locally

```bash
uv run streamlit run app.py
```

```bash
uv run pytest
```

### Test layout

| File | Protects |
|---|---|
| `tests/test_characterization.py` | Golden-reference physics: NRTL, $h^E$, the phase envelope at three pressures, dew-point branch, column scalars and stage profiles |
| `tests/test_distillation.py` | Collinearity, non-CMO flow variation, DOF closure, Murphree effect, app smoke test |
| `tests/test_presentation.py` | Diagram well-formedness, no orphaned figures, array-aware units, tutorial structure |
| `tests/test_flash.py`, `test_sizing.py`, `test_units.py` | Flash routines, sizing chain, unit round-trips |

`tests/golden/reference.npz` pins the physics at $10^{-8}$–$10^{-12}$ so the
array-form rewrites could be verified to reproduce the original scalar results
rather than merely look plausible. Regenerate it **deliberately**, and review
the diff:

```bash
uv run python tests/golden/regenerate.py
```

---

## Deploying to Streamlit Community Cloud

1. Push this repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io).
3. Click **New App** and select the repository.
4. Set the main file path to `app.py`.
5. Deploy — Streamlit Cloud installs from `requirements.txt`.

---

## Scope and limits

This is an **educational screening tool**. It is not a substitute for a
validated property package, relief-system design, HAZOP/LOPA, licensed
pressure-vessel design, or a process-safety review. Cost output is a Class-4
estimate (roughly ±30–50%). The application deliberately does not calculate
relief-orifice size, SIL, hazardous-area classification, or safe operating
limits.
