# Isopropanol / Water Rigorous Distillation Simulator

A standalone, production-grade Streamlit web application for the rigorous design and simulation of an Isopropanol / Water distillation column.

[![Deploy with Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=chetools/isopropanol-water-distillation&branch=main&mainModule=app.py)

## ⚡️ Key Features

1. **Ponchon-Savarit (H-x-y) Diagram**:
   - Saturated liquid $h_L(x)$ and saturated vapor $H_V(y)$ curves.
   - Difference poles $\Delta_D = (x_D, Q'_D)$ and $\Delta_B = (x_B, Q'_B)$.
   - Exact collinear operating line ($\Delta_D - F - \Delta_B$).
   - Stage tie lines and construction rays.

2. **Constant P VLE (T-x-y) Diagram**:
   - Bubble point and dew point curves.
   - Minimum-boiling azeotrope displayed at $x_{\text{azeo}} = 0.6697$ ($80.25^\circ\text{C}$ at 1 atm).

3. **McCabe-Thiele (x-y) Diagram**:
   - VLE equilibrium curve, $y = x$ diagonal, and stepped stages.

4. **Non-CMO Internal Flow Profiles ($L_n$, $V_n$)**:
   - Stage-by-stage liquid and vapor flows solved via the Ponchon-Savarit lever rule.
   - Clearly illustrates flow variations and the feed stage jump.

5. **Dynamic Degree-of-Freedom (DOF) Budget Locker**:
   - Exactly $N_{\text{dof}} = 2$. Prevents over-specification across all 7 variables ($x_D, x_B, D, B, R, Q_C, Q_R$).
   - Automatic azeotrope barrier and feasibility clamping with detailed explanations.

6. **Dual Modes**:
   - **Design Mode**: Ponchon-Savarit stage stepping, $R_{\text{min}}$, $N_{\text{min}}$, and optimal feed stage $N_F$.
   - **Rating Mode**: Fixed tray count MESH simulation.

## 🔬 Thermodynamic Data Source
All parameters come strictly from `chetools/chetools/data`:
- Isopropanol (ID 145): `data/IsopropanolProps.txt`
- Water (ID 62): `data/WaterProps.txt`
- NRTL Binary Interaction Parameters: `data/BinaryNRTL.txt` (30 Water, 36 IPA: $B_{12} = 20.06\,\mathrm{K}$, $B_{21} = 832.98\,\mathrm{K}$, $\alpha = 0.326$)
- Reference State: Pure saturated liquid at $25^\circ\text{C}$ ($298.15\,\mathrm{K}$) where $h_{L,i}(298.15) = 0$.
- Excess Enthalpy: Analytical $H^E(x, T)$ derived from NRTL temperature dependence.

## 🚀 Running Locally

Using `uv`:
```bash
uv run streamlit run app.py
```

Run tests:
```bash
uv run pytest
```

## ☁️ Deploying to Streamlit Community Cloud
1. Push this repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io).
3. Click **New App** and select your repository.
4. Set Main file path to `app.py`.
5. Click **Deploy**! (Streamlit Cloud automatically installs from `requirements.txt`).
