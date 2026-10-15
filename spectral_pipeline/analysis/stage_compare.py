"""Cross-part comparisons and additional checks:
* Part C (combined pool) vs Part A (reflectance) vs K5 - paired Wilcoxon on identical folds
* V5 leave-one-date-out on new plots, by held-out date
* stratified checks (date, growth stage, variety): feature AUC and classifier BA
* synthesis table of all approaches."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from common import cfg, load, save
from sp import stats

C = cfg()
D = load("data")
A, K, Cc = load("partA"), load("partK"), load("partC")
y, meta, F = D["y"], D["meta"], D["folds"]
out = {}


def fb(R, pipe, sch):
    f = R["fold_ba"]
    return f[(f.Pipeline == pipe) & (f.Scheme == sch)].set_index(["Repeat", "Unit"])["BA"]


def k5b(group, clf, sch):
    f = K["k5_folds"]
    return f[(f.Group == group) & (f.Classifier == clf) & (f.Scheme == sch)].set_index(["Repeat", "Unit"])["BA"]


pairs = [
    ("Combined pool: QDA on CART features", lambda s: fb(Cc, "QDA on CART features", s),
     "Reflectance: QDA on CART bands", lambda s: fb(A, "QDA on CART features", s)),
    ("Combined pool: QDA on RF features", lambda s: fb(Cc, "QDA on RF features", s),
     "Reflectance: QDA on RF bands", lambda s: fb(A, "QDA on RF features", s)),
    ("Combined pool: RF classifier (Tier-1 features)", lambda s: fb(Cc, "RF classifier", s),
     "Reflectance: RF classifier (Tier-1 bands)", lambda s: fb(A, "RF classifier", s)),
    ("Combined pool: CART classifier (Tier-1 features)", lambda s: fb(Cc, "CART classifier", s),
     "Reflectance: CART classifier (Tier-1 bands)", lambda s: fb(A, "CART classifier", s)),
    ("Combined pool: QDA on RF features", lambda s: fb(Cc, "QDA on RF features", s),
     "Combined pool: QDA on CART features", lambda s: fb(Cc, "QDA on CART features", s)),
    ("Combined pool: QDA on RF features", lambda s: fb(Cc, "QDA on RF features", s),
     "K5: RF classifier on all 4151 features", lambda s: k5b("G5", "RF", s)),
    ("Combined pool: QDA on RF features", lambda s: fb(Cc, "QDA on RF features", s),
     "K5: QDA on 15 features chosen by AUC", lambda s: k5b("GS", "QDA", s)),
    ("Combined pool: RF classifier (Tier-1 features)", lambda s: fb(Cc, "RF classifier", s),
     "K5: RF classifier on all 4151 features", lambda s: k5b("G5", "RF", s)),
]
rows = []
for an, af, bn, bf in pairs:
    for sch, lab in (("V3", "V3 nested (50 folds)"), ("V4", "V4 hold-out (10 splits)")):
        d = (af(sch) - bf(sch)).dropna()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = wilcoxon(d).pvalue if (d != 0).any() else 1.0
        rows.append({"First": an, "Second": bn, "Units": lab, "n": len(d), "Mean difference (BA)": d.mean(),
                     "SD": d.std(ddof=1), "First better": int((d > 0).sum()), "Second better": int((d < 0).sum()),
                     "Wilcoxon p": p})
out["cross_wilcoxon"] = pd.DataFrame(rows)

# ---------------------------------------------------------------- V5 by date
dates = F["V5_dates"]
lodo = []
for lab, R in (("Reflectance (Part A)", A), ("Combined pool (Part C)", Cc)):
    for p in ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"]:
        for d in dates:
            bas, n_te = [], []
            for te, pp, ss, rep, i in R["preds"][(p, "V5")]:
                if F["V5"][i]["date"] != d:
                    continue
                bas.append(stats.balanced_accuracy(y[te], pp))
                n_te.append(len(te))
            lodo.append({"Feature set": lab, "Pipeline": p, "Held-out date": d, "Splits": len(bas),
                         "Mean test leaves": float(np.mean(n_te)), "BA mean": float(np.mean(bas)),
                         "BA SD": float(np.std(bas, ddof=1))})
out["lodo"] = pd.DataFrame(lodo)

# ---------------------------------------------------------------- stratified checks
FE = K["features"]
pool = FE["groups"]["G5"][1]
pick = {}
for lab, tab, src in (("Best K1 band", K["k1_top15"].iloc[0], "R"), ):
    pick[f"K1 reflectance R{int(tab['Wavelength (nm)'])}"] = FE["K1"].X[:, list(FE["K1"].names).index(f"R{int(tab['Wavelength (nm)'])}")]
d1 = K["d1_all"][~K["d1_all"]["Guard"]].nlargest(1, "AUC").iloc[0]
pick[f"K4 first derivative D1_{int(d1['Wavelength (nm)'])}"] = FE["K4d1"].X[:, list(FE["K4d1"].names).index(f"D1_{int(d1['Wavelength (nm)'])}")]
for tab, fs, lab in ((K["k2"], FE["K2"], "K2"), (K["k3"], FE["K3"], "K3"), (K["k4_edge"], FE["K4edge"], "K4 edge")):
    nm = tab.iloc[0]["name"]
    pick[f"{lab} {nm}"] = fs.X[:, list(fs.names).index(nm)]
pick["REIP (Lagrangian)"] = K["reip_X"][:, 2]
strata = []
for nm, v in pick.items():
    a_all, d_all = stats.auc_free(v[:, None], y)
    strata.append({"Feature": nm, "Stratum": "All leaves", "Level": "all", "n healthy": int((y == 0).sum()),
                   "n diseased": int((y == 1).sum()), "AUC": a_all[0], "Same direction as all leaves": "—"})
    for by in ("Date", "Growth stage", "Variety"):
        for lev, g in meta.groupby(by):
            idx = g.index.to_numpy()
            if len(np.unique(y[idx])) < 2:
                continue
            a = stats.auc(v[idx][:, None], y[idx])[0]
            strata.append({"Feature": nm, "Stratum": by, "Level": lev, "n healthy": int((y[idx] == 0).sum()),
                           "n diseased": int((y[idx] == 1).sum()), "AUC": max(a, 1 - a),
                           "Same direction as all leaves": "yes" if (a >= 0.5) == (d_all[0] > 0) else "no"})
out["strata_auc"] = pd.DataFrame(strata)
# classifier BA within strata (V3 out-of-fold predictions, mean over the 5 repeats)
cls_rows = []
for lab, R in (("Reflectance (Part A)", A), ("Combined pool (Part C)", Cc)):
    for p in ["RF classifier", "QDA on CART features", "QDA on RF features"]:
        per_rep = {}
        for te, pp, ss, rep, i in R["preds"][(p, "V3")]:
            arr = per_rep.setdefault(rep, np.full(len(y), -1))
            arr[te] = pp
        for by in ("Date", "Growth stage", "Variety"):
            for lev, g in meta.groupby(by):
                idx = g.index.to_numpy()
                bas = [stats.balanced_accuracy(y[idx], arr[idx]) for arr in per_rep.values()]
                cls_rows.append({"Feature set": lab, "Pipeline": p, "Stratum": by, "Level": lev,
                                 "Leaves": len(idx), "BA (V3, mean of 5 repeats)": float(np.mean(bas))})
out["strata_ba"] = pd.DataFrame(cls_rows)

# ---------------------------------------------------------------- synthesis
syn = []
for lab, R in (("Part A · reflectance four-tier", A), ("Part C · combined-pool four-tier", Cc)):
    v = R["validation"].set_index(["Pipeline", "Scheme"])
    for p, nm in (("QDA on CART features", f"QDA on {R['cart_name']} (CART-selected)"),
                  ("QDA on RF features", f"QDA on {R['rf_name']} (RF-selected)"),
                  ("CART classifier", "CART classifier (rpart)"), ("RF classifier", "RF classifier (Balanced RF)")):
        syn.append({"Approach": f"{lab}: {nm}", "BA V1 (leaf 10-fold)": v.loc[(p, "V1"), "BA"],
                    "BA V3 (nested CV)": v.loc[(p, "V3"), "BA"], "SD V3": v.loc[(p, "V3"), "BA_SD"],
                    "BA V4 (hold-out plots)": v.loc[(p, "V4"), "BA"], "SD V4": v.loc[(p, "V4"), "BA_SD"],
                    "BA V5 (new date + plots)": v.loc[(p, "V5"), "BA"], "AUC V3": v.loc[(p, "V3"), "AUC"],
                    "κ V3": v.loc[(p, "V3"), "kappa"]})
t = K["k5"]
gn = {"G0": "full raw spectrum", "G1": "K1 reflectance", "G2": "K2 continuum removal", "G3": "K3 vegetation indices",
      "G4": "K4 derivatives + edge", "G5": "K1–K4 combined", "G6": "K4 incl. guard bands (artefact)", "GS": "K-selected 15"}
for g in gn:
    for clf in ("CART", "RF", "QDA"):
        a = t[(t.Group == g) & (t.Classifier == clf) & (t.Scheme == "CV")]
        b = t[(t.Group == g) & (t.Classifier == clf) & (t.Scheme == "Hold-out")]
        if len(a):
            syn.append({"Approach": f"K5 · {gn[g]}: {clf}", "BA V1 (leaf 10-fold)": np.nan,
                        "BA V3 (nested CV)": a.iloc[0]["BA"], "SD V3": a.iloc[0]["BA_SD"],
                        "BA V4 (hold-out plots)": b.iloc[0]["BA"], "SD V4": b.iloc[0]["BA_SD"],
                        "BA V5 (new date + plots)": np.nan, "AUC V3": a.iloc[0]["AUC"], "κ V3": a.iloc[0]["kappa"]})
for nm, tab in (("K2 best single parameter", K["k2"]), ("K3 best single index", K["k3"]),
                ("K4 best edge parameter", K["k4_edge"]), ("REIP best method", K["reip"])):
    r = tab.iloc[0]
    syn.append({"Approach": f"Single feature · {nm}: {r['name']} (threshold)", "BA V1 (leaf 10-fold)": r["BA all leaves"],
                "BA V3 (nested CV)": r["BA plot-grouped CV"], "SD V3": np.nan, "BA V4 (hold-out plots)": r["BA hold-out"],
                "SD V4": np.nan, "BA V5 (new date + plots)": np.nan, "AUC V3": r["AUC"], "κ V3": np.nan})
for lab, h in (("K3b optimised NDSI, all pairs — brackets the 1800 nm join (search nested)", K["k3b_honest"]["NDSI"]),
               ("K3b optimised NDSI, join-free pairs (search nested)", K["k3b_jf"]["honest"]["NDSI"])):
    syn.append({"Approach": f"Single feature · {lab}", "BA V1 (leaf 10-fold)": np.nan,
                "BA V3 (nested CV)": h["BA CV"], "SD V3": np.nan, "BA V4 (hold-out plots)": h["BA hold-out"], "SD V4": h["SD"],
                "BA V5 (new date + plots)": np.nan, "AUC V3": np.nan, "κ V3": np.nan})
out["synthesis"] = pd.DataFrame(syn).sort_values("BA V3 (nested CV)", ascending=False).reset_index(drop=True)
# ---------------------------------------------------------------- guard-edge proximity (artefact leakage?)
guards = {"R": C["spectra"]["guard"]["R"], "D1": C["spectra"]["guard"]["D1"]}


def near_guard(name, tol=5):
    for pre, key in (("D1_", "D1"), ("R", "R")):
        if name.startswith(pre) and name[len(pre):].isdigit():
            w = float(name[len(pre):])
            return any((a - tol) <= w < a or b < w <= (b + tol) for a, b in guards[key])
    return False


ge_rows = []
for meth in ("CART", "RF"):
    allset = Cc["sets"][Cc["cart_name"] if meth == "CART" else Cc["rf_name"]]
    lists = Cc["fold_selections"][meth]
    tot = sum(len(l) for l in lists)
    near = sum(near_guard(v) for l in lists for v in l)
    ge_rows.append({"Selector": meth, "All-leaf set": ", ".join(v for v in allset if near_guard(v)) or "none",
                    "Selections within 5 nm of a guard zone (50 training sets)": near, "Of": tot, "Share": near / tot})
out["guard_edge"] = pd.DataFrame(ge_rows)
save(out, "compare")
pd.set_option("display.width", 250)
print(out["cross_wilcoxon"])
print(out["lodo"].pivot_table(index=["Feature set", "Pipeline"], columns="Held-out date", values="BA mean"))
print(out["synthesis"].head(15)[["Approach", "BA V3 (nested CV)", "BA V4 (hold-out plots)"]])
print(out["strata_auc"].groupby("Feature")["AUC"].agg(["min", "max"]))
