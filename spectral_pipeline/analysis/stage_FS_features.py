"""Disease-specific features across the feature-selection methods (Part FS, follow-up).

* spectral-region map: for every method, how often its redundancy-controlled top-10 (20 training sets)
  contains a feature of each spectral region / feature group
* stability tiers of the consensus features (number of methods selecting the feature in >= 50 % of the
  training sets)
* accuracy of fixed stable feature sets on the 20 held-out units (QDA, LDA, RF)
* consistency of the stable features across dates, growth stages and varieties (AUC and direction)
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from common import cfg, load, save
from sp import fs_methods as fm
from sp import models
from sp.stats import auc_free
from stage_FS import build_pool
from stage_FS_eval import EQUIV, FAMILY, NAMES, UNIQUE, borda, load_units

C = cfg()
GZ = {"R": C["spectra"]["guard"]["R"], "D1": C["spectra"]["guard"]["D1"]}
D1_REGIONS = [(400, 680, "D1 visible 400–680 nm"), (680, 760, "D1 red edge 680–760 nm"), (760, 930, "D1 NIR plateau 760–930 nm"),
              (930, 1000, "D1 970-nm water shoulder 930–1000 nm"), (1000, 1300, "D1 1200-nm water band 1000–1300 nm"),
              (1300, 1500, "D1 1450-nm water band 1300–1500 nm"), (1500, 1700, "D1 SWIR plateau 1500–1700 nm"),
              (1700, 1793, "D1 C–H band 1700–1792 nm"), (1837, 1990, "D1 1940-nm water band 1840–1990 nm"),
              (1990, 2150, "D1 2000–2150 nm"), (2150, 2260, "D1 2200-nm band 2150–2260 nm"),
              (2260, 2400, "D1 2300-nm C–H/N–H band 2260–2400 nm"), (2400, 2501, "D1 2400–2500 nm")]
CR_REGIONS = {"CR1": "CR blue / red pigment bands", "CR2": "CR blue / red pigment bands", "CR3": "CR 970-nm water band",
              "CR4": "CR 1200-nm water band", "CR5": "CR 1450-nm water band", "CR6": "CR 1940-nm water band"}
REGION_ORDER = ["CR 970-nm water band", "CR 1940-nm water band", "CR 1450-nm water band", "CR 1200-nm water band",
                "CR blue / red pigment bands"] + [r[2] for r in D1_REGIONS] + ["K1 reflectance VIS–NIR", "K1 reflectance SWIR",
                                                                              "K3 vegetation indices", "K4 edge parameters"]
PHYS = {
    "CR 970-nm water band": "liquid water (O–H, 970 nm)", "CR 1940-nm water band": "liquid water (O–H, 1940 nm)",
    "CR 1450-nm water band": "liquid water (1450 nm)", "CR 1200-nm water band": "liquid water (1200 nm)",
    "CR blue / red pigment bands": "chlorophyll / carotenoid absorption",
    "D1 visible 400–680 nm": "pigments", "D1 red edge 680–760 nm": "chlorophyll content / red edge",
    "D1 NIR plateau 760–930 nm": "mesophyll structure (NIR scattering)", "D1 970-nm water shoulder 930–1000 nm": "water (970 nm), near detector join",
    "D1 1200-nm water band 1000–1300 nm": "water (1200 nm)", "D1 1450-nm water band 1300–1500 nm": "water (1450 nm)",
    "D1 SWIR plateau 1500–1700 nm": "water / dry matter", "D1 C–H band 1700–1792 nm": "C–H: lignin, cellulose, waxes (1730 nm)",
    "D1 1940-nm water band 1840–1990 nm": "liquid water (1940 nm)", "D1 2000–2150 nm": "protein / N–H",
    "D1 2200-nm band 2150–2260 nm": "cellulose, protein (2100–2300 nm)", "D1 2300-nm C–H/N–H band 2260–2400 nm": "C–H / N–H: lignin, protein, starch",
    "D1 2400–2500 nm": "dry matter (noisy end)", "K1 reflectance VIS–NIR": "reflectance level", "K1 reflectance SWIR": "reflectance level (water)",
    "K3 vegetation indices": "pigment / stress indices", "K4 edge parameters": "red-edge shape",
}


def region_of(name, ser, pos, typ):
    if typ.startswith("K2"):
        return CR_REGIONS.get(name.split()[0], "CR other")
    if typ.startswith("K3"):
        return "K3 vegetation indices"
    if typ.startswith("K4 edge"):
        return "K4 edge parameters"
    if ser == "R":
        return "K1 reflectance VIS–NIR" if pos < 1300 else "K1 reflectance SWIR"
    for a, b, lab in D1_REGIONS:
        if a <= pos < b:
            return lab
    return "D1 other"


def near_join(ser, pos, tol=10):
    return ser in GZ and np.isfinite(pos) and any((a - tol) <= pos < a or b < pos <= (b + tol) for a, b in GZ[ser])


def main():
    D, P, cw = build_pool()
    X, y, meta = P.X, D["y"], P.meta
    ser, pos = meta["series"].to_numpy(), meta["position"].to_numpy(float)
    names = meta["name"].to_numpy()
    reg = np.array([region_of(n, s, p, t) for n, s, p, t in zip(names, ser, pos, meta["type"])])
    R = load("partFS")
    U = load_units()
    units = R["test_units"]
    for u in U:
        Xz = fm.zs(X[U[u]["train"]])
        o, pts = borda(U[u], Xz, [m for m in UNIQUE if m != "Consensus (Borda)"])
        U[u]["Consensus (Borda)"] = {"rank": o, "score": pts}
    methods = [m for m in NAMES if m not in EQUIV and m != "CWT scalogram"]
    sets = {}
    for u in units:
        Xz = fm.zs(X[U[u]["train"]])
        for m in methods:
            r = U[u][m]
            sets[(m, u)] = list(r["sets"][10]) if "sets" in r else fm.guard_topk(r["rank"], Xz, 10)
    # ---- region map
    rows = []
    for m in methods:
        rec = {"Method": m, "Family": FAMILY[m]}
        for g in REGION_ORDER:
            rec[g] = np.mean([any(reg[j] == g for j in sets[(m, u)]) for u in units])
        rows.append(rec)
    rmap = pd.DataFrame(rows)
    rcols = [g for g in REGION_ORDER if rmap[g].max() > 0]
    rmap = rmap[["Method", "Family"] + rcols]
    rsum = pd.DataFrame({"Region": rcols, "Physiological meaning": [PHYS.get(g, "") for g in rcols],
                         "Methods selecting it in ≥ 50 % of training sets": [(rmap[g] >= 0.5).sum() for g in rcols],
                         "Mean selection frequency": [rmap[g].mean() for g in rcols]}).sort_values(
        ["Methods selecting it in ≥ 50 % of training sets", "Mean selection frequency"], ascending=False).reset_index(drop=True)
    # ---- per-method all-leaf top-10 grouped by region
    full = R["full"].set_index("Method")
    per_method = []
    for m in methods + ["CWT scalogram"]:
        if m == "CWT scalogram":
            per_method.append({"Method": m, "Family": FAMILY[m], "Top-10 (all leaves)": full.loc[m, "Selected (top-10, redundancy-controlled)"],
                               "Regions": "wavelet features: SWIR 2185–2495 nm, red 655–680 nm, 1920 nm"})
            continue
        idx = full.loc[m, "idx"]
        regs = pd.Series([reg[j] for j in idx]).value_counts()
        per_method.append({"Method": m, "Family": FAMILY[m], "Top-10 (all leaves)": ", ".join(names[idx]),
                           "Regions": "; ".join(f"{g} ({c})" for g, c in regs.items())})
    per_method = pd.DataFrame(per_method)
    # ---- stability tiers of the consensus features
    cons = R["consensus"].copy()
    cons["Region"] = [reg[j] for j in cons["idx"]]
    cons["Physiology"] = cons["Region"].map(PHYS)
    nm_ = cons["Methods ≥ 50 % of training sets"]
    cons["Tier"] = np.where(nm_ >= 10, "Core (≥ 10 of 21 methods)", np.where(nm_ >= 5, "Supporting (5–9 methods)", np.where(nm_ >= 3, "Complementary (3–4 methods)", "Occasional")))
    cons["Near detector join"] = [near_join(ser[j], pos[j]) for j in cons["idx"]]
    which = []
    F_ = R["consensus_freq"]
    for _, r in cons.iterrows():
        f = F_[F_["Feature"] == r["Feature"]].drop(columns=["Feature", "Consensus score", "Methods ≥ 50 %"], errors="ignore").iloc[0]
        which.append(", ".join(k for k, v in f.items() if v >= 0.5))
    cons["Which methods (≥ 50 % of training sets)"] = which
    # class means and % difference
    t1 = load("partC")["tier1"].set_index("name")
    cons["Mean healthy"] = [t1.loc[n, "mean0"] for n in cons["Feature"]]
    cons["Mean diseased"] = [t1.loc[n, "mean1"] for n in cons["Feature"]]
    # ---- fixed stable sets on the 20 held-out units
    nm2idx = {n: i for i, n in enumerate(names)}
    S1 = ["CR3 water 970 width", "CR6 water 1940 position", "CR6 water 1940 symmetry"]
    S2 = S1 + ["D1_1934", "D1_1915", "D1_848", "D1_898"]
    S3 = S2 + ["ARI", "D1_1724", "D1_2306", "D1_2223"]
    S4 = list(cons[(cons.Tier != "Occasional") & ~cons["Near detector join"]]["Feature"])
    XzA = fm.zs(X)
    fixed = {}
    for lab, lst in (("Core water features (3)", S1), ("Stable disease-specific set (7)", S2),
                     ("Stable + complementary set (11)", S3), ("All consensus features (no join bands)", S4)):
        fixed[lab] = fm.guard_topk(np.array([nm2idx[n] for n in lst]), XzA, 30)
    brf = models.brf(C, 300)
    brf.set_params(n_jobs=4)
    ev = []
    for lab, S in fixed.items():
        for u in units:
            tr, te = U[u]["train"], U[u]["test"]
            pq, sq = models.fit_predict(models.qda("equal"), X[tr][:, S], y[tr], X[te][:, S])
            pl, _ = models.fit_predict(models.lda("equal"), X[tr][:, S], y[tr], X[te][:, S])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                brf.fit(X[tr][:, S], y[tr])
            from sklearn.metrics import roc_auc_score
            ev.append({"Set": lab, "Unit": u, "BA QDA": fm.ba(y[te], pq), "BA LDA": fm.ba(y[te], pl), "BA RF": fm.ba(y[te], brf.predict(X[te][:, S])),
                       "AUC QDA": roc_auc_score(y[te], sq)})
    ev = pd.DataFrame(ev)
    fixed_tab = ev.groupby("Set", sort=False).agg(**{"BA QDA": ("BA QDA", "mean"), "SD QDA": ("BA QDA", "std"), "BA LDA": ("BA LDA", "mean"),
                                                     "BA RF": ("BA RF", "mean"), "AUC QDA": ("AUC QDA", "mean")}).reset_index()
    fixed_tab.insert(1, "Features", [", ".join(names[fixed[s]]) for s in fixed_tab["Set"]])
    fixed_tab.insert(2, "k", [len(fixed[s]) for s in fixed_tab["Set"]])
    fixed_tab["J–M (all leaves)"] = [fm.jm_multi(XzA[:, fixed[s]], y) for s in fixed_tab["Set"]]
    # ---- consistency across dates / stages / varieties
    md = D["meta"]
    strata = []
    top = cons[cons.Tier != "Occasional"]
    for _, r in top.iterrows():
        v = X[:, r["idx"]]
        a_all, d_all = auc_free(v[:, None], y)
        rec = {"Feature": r["Feature"], "AUC all leaves": a_all[0]}
        for by in ("Date", "Growth stage", "Variety"):
            aucs, same = [], 0
            levels = list(md[by].unique())
            for lev in levels:
                ii = np.where(md[by].to_numpy() == lev)[0]
                if len(np.unique(y[ii])) < 2:
                    continue
                a, dd = auc_free(v[ii][:, None], y[ii])
                aucs.append(a[0])
                same += int(np.sign(dd[0]) == np.sign(d_all[0]))
                rec[f"{by}: {lev}"] = a[0]
            rec[f"Same direction ({by})"] = f"{same}/{len(aucs)}"
        strata.append(rec)
    strata = pd.DataFrame(strata)
    out = {"region_map": rmap, "region_summary": rsum, "per_method": per_method, "consensus": cons, "fixed": fixed_tab, "fixed_units": ev,
           "fixed_sets": {k: names[v].tolist() for k, v in fixed.items()}, "strata": strata, "region_cols": rcols,
           "borda_honest": float(R["summary"].query("Method == 'Consensus (Borda)' and Guard == 'yes' and k == 10")["BA QDA"].iloc[0])}
    save(out, "fsfeat")
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 120)
    print(rsum.round(2).to_string())
    print(cons[["Feature", "Tier", "Region", "Methods ≥ 50 % of training sets", "Near detector join"]].to_string())
    print(fixed_tab.round(3).to_string())
    print(strata.round(2).to_string())


if __name__ == "__main__":
    main()
