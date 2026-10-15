"""Recompute the (scale-free) condition numbers and add the J-M invariance check."""
import numpy as np
from common import cfg, load, save
from sp import features, models

D = load("data")
y = D["y"]
A, Cc = load("partA"), load("partC")
XA = D["spec"].R_raw
nA = [f"WV{int(w)}" for w in D["spec"].wl]
pool = features.build_all(D["spec"], cfg())["groups"]["G5"][1]
nC = list(pool.names)
for R, X, names in ((A, XA, nA), (Cc, pool.X, nC)):
    rows = []
    for i, r in R["tier3"].iterrows():
        cols = [names.index(v) for v in R["sets"][r["Set"]]]
        c0, c1 = models.cond_numbers(X[:, cols], y)
        R["tier3"].at[i, "cond0"], R["tier3"].at[i, "cond1"] = c0, c1
        Z = (X[:, cols] - X[:, cols].mean(0)) / X[:, cols].std(0)
        rows.append(abs(models.jm(Z, y)[0] - r["JM"]))
    R["checks"] = [c for c in R["checks"] if c[1] != "Invertibility of the class covariances"]
    cmax = R["tier3"][["cond0", "cond1"]].to_numpy().max()
    R["checks"].append(("Tier 3", "Invertibility of the class covariances",
                        "condition number of the class correlation matrices of every selected set",
                        f"max {cmax:.1e} (well below the ~1e12 limit of double precision)", "PASS" if cmax < 1e8 else "FLAG"))
    R["checks"].append(("Tier 3", "J–M is scale-invariant", "J–M on raw vs standardised features of every selected set",
                        f"max |ΔJ–M| = {max(rows):.1e}", "PASS" if max(rows) < 1e-8 else "FLAG"))
save(A, "partA")
save(Cc, "partC")
print(A["tier3"][["Set", "JM", "cond0", "cond1"]])
print(Cc["tier3"][["Set", "JM", "cond0", "cond1"]])
