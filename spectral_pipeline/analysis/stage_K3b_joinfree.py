"""K3b (additional): optimised two-band index excluding band pairs that straddle a
detector join (one band ≤ join, the other > join, both within 100 nm of it).
Such pairs measure the splice step / start-up bump at 1000/1001 or 1800/1801 nm."""
from __future__ import annotations

import re

import time

import numpy as np
import pandas as pd

from common import cfg, load, present_dates, save
from sp import features, fourtier, stats
from sp.features import FeatureSet

T0 = time.time()
C = cfg()
D = load("data")
K = load("partK")
spec, y, F, dates, groups = D["spec"], D["y"], D["folds"], D["dates"], D["groups"]
wl, R = spec.wl, spec.R
JOINS, NEAR = C["spectra"]["joins"], 100
grid = np.arange(400, 2501, C["k3b"]["grid_nm"])
gidx = np.array([int(np.argmin(np.abs(wl - g))) for g in grid])
gidx = gidx[~spec.guard["R"][gidx]]
ii, jj = np.triu_indices(len(gidx), 1)
wi, wj = wl[gidx[ii]], wl[gidx[jj]]


def straddles(a, b):
    return any(min(a, b) <= j < max(a, b) and abs(a - j) <= NEAR and abs(b - j) <= NEAR for j in JOINS)


keep = np.array([not straddles(a, b) for a, b in zip(wi, wj)])
ii, jj = ii[keep], jj[keep]
fourtier.log(f"K3b join-free: {keep.sum()} of {len(keep)} pairs kept")


def search(rows):
    Rg = R[np.ix_(rows, gidx)]
    yy = y[rows]
    n1 = int(yy.sum())
    n0 = len(yy) - n1
    res = {}
    for form in ("NDSI", "DI"):
        aucs = np.empty(len(ii))
        for s0 in range(0, len(ii), 4000):
            a, b = ii[s0:s0 + 4000], jj[s0:s0 + 4000]
            M = (Rg[:, a] - Rg[:, b]) / (Rg[:, a] + Rg[:, b]) if form == "NDSI" else Rg[:, a] - Rg[:, b]
            r = np.argsort(np.argsort(M, axis=0, kind="stable"), axis=0, kind="stable") + 1
            aucs[s0:s0 + 4000] = (r[yy == 1].sum(0) - n1 * (n1 + 1) / 2) / (n0 * n1)
        res[form] = np.maximum(aucs, 1 - aucs)
    return res


S = search(np.arange(len(y)))
top = []
for form in ("NDSI", "DI"):
    for k in np.argsort(-S[form])[:10]:
        top.append({"Index": f"{form}({wl[gidx[ii[k]]]:.0f}, {wl[gidx[jj[k]]]:.0f})", "Band i (nm)": wl[gidx[ii[k]]],
                    "Band j (nm)": wl[gidx[jj[k]]], "AUC": S[form][k], "Form": form})
top = pd.DataFrame(top)
# refine at 1 nm (same rule)
refined = {}
for form in ("NDSI", "DI"):
    b = top[top.Form == form].iloc[0]
    best = (0, None)
    for a in range(int(b["Band i (nm)"]) - 5, int(b["Band i (nm)"]) + 6):
        for c in range(int(b["Band j (nm)"]) - 5, int(b["Band j (nm)"]) + 6):
            if a >= c or a < 400 or c > 2500 or straddles(a, c):
                continue
            ia, ic = int(np.argmin(np.abs(wl - a))), int(np.argmin(np.abs(wl - c)))
            if spec.guard["R"][ia] or spec.guard["R"][ic]:
                continue
            v = (R[:, ia] - R[:, ic]) / (R[:, ia] + R[:, ic]) if form == "NDSI" else R[:, ia] - R[:, ic]
            au = stats.auc_free(v[:, None], y)[0][0]
            if au > best[0]:
                best = (au, (a, c, v))
    refined[form] = best[1]
fs_ref = FeatureSet(np.column_stack([refined[f][2] for f in ("NDSI", "DI")]),
                    features._meta([f"{f}({refined[f][0]},{refined[f][1]})" for f in ("NDSI", "DI")], "K3b", ["n", "d"], np.nan))
# statistics as in K (threshold CV / hold-out, mixed model)
ft = stats.feature_table(fs_ref.X, y)
thr, d = stats.youden_fit(fs_ref.X, y)


def threshold_cv(X, scheme):
    acc = {}
    for f in F[scheme]:
        t, dd = stats.youden_fit(X[f["train"]], y[f["train"]])
        pr = stats.youden_predict(X[f["test"]], t, dd)
        yt = y[f["test"]][:, None]
        a = acc.setdefault(f["rep"], np.zeros((4, X.shape[1])))
        a[0] += ((pr == 1) & (yt == 1)).sum(0)
        a[1] += (yt == 1).sum()
        a[2] += ((pr == 0) & (yt == 0)).sum(0)
        a[3] += (yt == 0).sum()
    return np.mean([0.5 * (a[0] / a[1] + a[2] / a[3]) for a in acc.values()], 0)


mm = stats.mixed_models(fs_ref.X, y, groups, 2)
ref_tab = pd.DataFrame({"name": fs_ref.names, "Mean healthy": ft["mean0"], "Mean diseased": ft["mean1"], "Welch t": ft["t"],
                        "q (BH)": ft["q"], "Hedges g": ft["g"], "AUC": ft["auc"], "Direction": np.where(ft["dir"] > 0, "D > H", "D < H"),
                        "Threshold": thr, "Rule": np.where(d > 0, "diseased if > thr", "diseased if < thr"),
                        "BA all leaves": [stats.balanced_accuracy(y, stats.youden_predict(fs_ref.X[:, j], thr[j], d[j])[:, 0]) for j in range(2)],
                        "BA plot-grouped CV": threshold_cv(fs_ref.X, "V3"), "BA hold-out": threshold_cv(fs_ref.X, "V4"),
                        "Mixed-model q": mm["q"], "ICC plot": mm["icc"]})
# honest nested search
units = [("V3", f) for f in F["V3"] if f["rep"] == 0] + [("V4", f) for f in F["V4"]]
res = {f: {"V3": [], "V4": []} for f in ("NDSI", "DI")}
chosen = {"NDSI": [], "DI": []}
for sch, f in units:
    Sx = search(f["train"])
    for form in ("NDSI", "DI"):
        k = int(np.argmax(Sx[form]))
        a, c = gidx[ii[k]], gidx[jj[k]]
        chosen[form].append((int(wl[a]), int(wl[c])))
        v = (R[:, a] - R[:, c]) / (R[:, a] + R[:, c]) if form == "NDSI" else R[:, a] - R[:, c]
        t, dd = stats.youden_fit(v[f["train"]][:, None], y[f["train"]])
        res[form][sch].append((f["test"], stats.youden_predict(v[f["test"]][:, None], t, dd)[:, 0]))
honest = {}
for form in ("NDSI", "DI"):
    te = np.concatenate([a for a, _ in res[form]["V3"]])
    bas = [stats.balanced_accuracy(y[a], b) for a, b in res[form]["V4"]]
    cnt = pd.Series([f"({a}, {c})" for a, c in chosen[form]]).value_counts()
    honest[form] = {"BA CV": stats.balanced_accuracy(y[te], np.concatenate([b for _, b in res[form]["V3"]])),
                    "BA hold-out": float(np.mean(bas)), "SD": float(np.std(bas, ddof=1)),
                    "pairs": "; ".join(f"{k} × {v}" for k, v in cnt.items()), "n_sets": len(units)}
# by date
rows = []
for form in ("NDSI", "DI"):
    a, c, v = refined[form]
    r = {"Pair": f"{form}({a}, {c})", "AUC all leaves": stats.auc_free(v[:, None], y)[0][0]}
    dirs = []
    for dte in present_dates(D):
        m = dates == dte
        au = stats.auc(v[m][:, None], y[m])[0]
        r[f"AUC {dte}"] = max(au, 1 - au)
        dirs.append(au >= 0.5)
    r["Direction by date"] = "same on all dates" if len(set(dirs)) == 1 else "changes between dates"
    rows.append(r)
K["k3b_jf"] = {"top": top, "refined": ref_tab, "honest": honest, "bydate": pd.DataFrame(rows),
               "npairs": int(keep.sum()), "excluded": int((~keep).sum()), "near_nm": NEAR}
_best = K["k3b_refined"].iloc[0]["name"]
_ab = [int(v) for v in re.findall(r"\d+", _best)[:2]]
_str = len(_ab) == 2 and straddles(*_ab)
K["k3b_jf"]["allpair_straddles"] = bool(_str)
K["k3b_jf"]["allpair_best"] = _best
K["checks"].append(("K3b", "Best pair straddles a detector join?",
                    "pairs with one band on each side of the 1000/1001 or 1800/1801 nm join (within 100 nm) excluded and the search repeated",
                    (f"all-pair best {_best} brackets a detector join → treated as artefact-prone; " if _str else
                     f"all-pair best {_best} does not straddle a join (same as the join-free search); ")
                    + f"join-free best {ref_tab.iloc[0]['name']} (AUC {ref_tab.iloc[0]['AUC']:.3f}; honest BA {100 * honest['NDSI']['BA CV']:.1f} % CV)",
                    "FLAG" if _str else "PASS"))
save(K, "partK")
fourtier.log(f"K3b join-free done in {(time.time() - T0) / 60:.1f} min")
print(top.groupby("Form").head(3))
print(ref_tab[["name", "AUC", "BA all leaves", "BA plot-grouped CV", "BA hold-out", "Mixed-model q"]])
print(honest)
print(pd.DataFrame(rows))
