"""Recompute the mixed-model columns with R nlme (the statsmodels L-BFGS fit
collapsed to a zero plot variance in most bands) and add the cross-check."""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy import stats as st

from common import load, save
from sp import stats

which = sys.argv[1:] or ["A", "K"]
D = load("data")
y, g = D["y"], D["groups"]
if "A" in which:
    A = load("partA")
    X = D["spec"].R_raw
    mm = stats.mixed_models(X, y, g, 4)
    t1 = A["tier1"]
    t1["mm_effect"], t1["mm_p"], t1["mm_q"], t1["icc"] = mm["effect"], mm["p"], mm["q"], mm["icc"]
    t1["mm_sig"] = t1["mm_q"] < 0.05
    t1["mm_boundary"] = mm["boundary"]
    tt = A["tier1_tests"]
    tt.loc[tt["Test"].str.startswith("Mixed model"), "Significant bands"] = int(t1["mm_sig"].sum())
    for i, r in A["tier1_regions"].iterrows():
        a, b = [float(v) for v in r["Region"].split("(")[1].rstrip(")").split("–")]
        m = (t1["position"] >= a) & (t1["position"] <= b)
        A["tier1_regions"].at[i, "Mixed-model significant"] = int(t1.loc[m, "mm_sig"].sum())
    ct = A["cart_table"]
    ct["Mixed model significant"] = ["yes" if t1.loc[t1["position"] == b, "mm_sig"].iloc[0] else "no" for b in ct["Band (nm)"]]
    # cross-check with statsmodels (Powell, Wald z) on every 50th band
    cols = list(range(0, X.shape[1], 50))
    sm = stats.mixed_models_statsmodels(X[:, cols], y, g, 4)
    rho = st.spearmanr(sm["p"], mm["p"][cols]).correlation
    icc_d = np.nanmax(np.abs(sm["icc"] - mm["icc"][cols]))
    A["checks"] = [c for c in A["checks"] if c[1] != "Pseudo-replication"]
    A["checks"].append(("Tier 1", "Pseudo-replication",
                        "linear mixed model v ~ Disease + (1|plot), REML, R nlme::lme (t-test, 46 df), BH-FDR",
                        f"{int(t1['mm_sig'].sum())} of {len(t1)} bands significant (Welch: {int(t1['sig'].sum())}); plot ICC median {np.nanmedian(mm['icc']):.3f}",
                        "PASS"))
    A["checks"].append(("Tier 1", "Mixed model implementation",
                        "R nlme::lme vs Python statsmodels MixedLM (Powell), every 50th band",
                        f"Spearman ρ of p-values {rho:.3f}; max |ΔICC| {icc_d:.3f} (statsmodels uses a Wald z-test, nlme a t-test with 46 df, so nlme p-values are larger)",
                        "PASS" if rho > 0.95 else "FLAG"))
    print("A:", int(t1["mm_sig"].sum()), "mixed-model significant; median ICC", np.nanmedian(mm["icc"]), "rho", rho)
    save(A, "partA")
if "K" in which:
    K = load("partK")
    FE = K["features"]
    sets = {"k2": FE["K2"], "k3": FE["K3"], "k4_edge": FE["K4edge"]}
    for key, fs in sets.items():
        mm = stats.mixed_models(fs.X, y, g, 4)
        m = pd.DataFrame({"name": fs.names, "Mixed-model q": mm["q"], "ICC plot": mm["icc"]}).set_index("name")
        K[key]["Mixed-model q"] = K[key]["name"].map(m["Mixed-model q"])
        K[key]["ICC plot"] = K[key]["name"].map(m["ICC plot"])
    mm = stats.mixed_models(K["reip_X"], y, g, 4)
    order = ["REIP – maximum first derivative", "REIP – linear 4-point interpolation", "REIP – Lagrangian interpolation", "REIP – linear extrapolation"]
    m = dict(zip(order, zip(mm["q"], mm["icc"])))
    K["reip"]["Mixed-model q"] = K["reip"]["name"].map(lambda n: m[n][0])
    K["reip"]["ICC plot"] = K["reip"]["name"].map(lambda n: m[n][1])
    # refined K3b indices: recompute from their definitions
    R = D["spec"].R
    wl = D["spec"].wl
    vals = []
    for nm in K["k3b_refined"]["name"]:
        a, b = [int(v) for v in nm[nm.index("(") + 1:-1].split(",")]
        ia, ib = int(np.argmin(np.abs(wl - a))), int(np.argmin(np.abs(wl - b)))
        vals.append((R[:, ia] - R[:, ib]) / (R[:, ia] + R[:, ib]) if nm.startswith("NDSI") else R[:, ia] - R[:, ib])
    mm = stats.mixed_models(np.column_stack(vals), y, g, 4)
    K["k3b_refined"]["Mixed-model q"], K["k3b_refined"]["ICC plot"] = mm["q"], mm["icc"]
    save(K, "partK")
    print("K patched")
