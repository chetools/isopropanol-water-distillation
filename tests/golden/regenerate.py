"""Regenerate tests/golden/reference.npz from the current implementation.

Run deliberately and review the resulting diff: these values are the
contract that protects the physics during refactoring.
"""
import sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import src.thermo as th, src.column as col

T = np.linspace(300.0, 400.0, 21)
X = np.linspace(0.0, 1.0, 21)
TT, XX = np.meshgrid(T, X, indexing="ij")

g1 = np.empty_like(TT); g2 = np.empty_like(TT); he = np.empty_like(TT)
for i in range(TT.shape[0]):
    for j in range(TT.shape[1]):
        a, b = th.nrtl_gamma(XX[i, j], TT[i, j])
        g1[i, j], g2[i, j] = a, b
        he[i, j] = th.excess_enthalpy(XX[i, j], TT[i, j])

out = {"T_grid": T, "x_grid": X, "gamma1": g1, "gamma2": g2, "h_excess": he}

for P in (101325.0, 50000.0, 300000.0):
    tag = f"{int(P)}"
    vle = th.get_vle_curves(P, n_points=61)
    for k in ("x", "T_bubble_K", "y", "h_L", "H_V"):
        out[f"vle_{tag}_{k}"] = np.asarray(vle[k])
    out[f"azeo_{tag}"] = np.array([vle["x_azeo"], vle["T_azeo_K"]])
    ys = np.linspace(0.02, 0.98, 25)
    out[f"dew_{tag}"] = np.array([th.dew_point(y, P) for y in ys])
    out[f"dew_{tag}_y"] = ys

feed = th.calculate_feed_state(0.20, 101325.0, q=1.0)
r = col.solve_design_column(100.0, 0.20, 101325.0, 0.60, 0.02, 3.0, feed)
scalars = ["D","B","Q_C","Q_R","Q_prime_D","Q_prime_B","R_min","h_F","h_D","h_B","T_D_C","T_B_C"]
out["col_scalars"] = np.array([r[k] for k in scalars])
out["col_ints"] = np.array([r["total_stages"], r["N_min"], r["feed_stage"], r["tray_count"]])
out["col_stage_x"] = np.array([s["x"] for s in r["stages"]])
out["col_stage_y"] = np.array([s["y"] for s in r["stages"]])
out["col_stage_L"] = np.array([s["L"] for s in r["stages"]])
out["col_stage_V"] = np.array([s["V"] for s in r["stages"]])
out["col_stair_x"] = np.array(r["mccabe_lines"]["staircase_x"])
out["col_stair_y"] = np.array(r["mccabe_lines"]["staircase_y"])

np.savez_compressed(Path(__file__).with_name("reference.npz"), **out)
print("scalars:", dict(zip(scalars, out["col_scalars"])))
print("ints:", out["col_ints"], " stages:", len(out["col_stage_x"]))
print("saved", len(out), "arrays")
