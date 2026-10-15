"""Part FS evaluation: accuracy of the selected features on held-out plots, stability across the 20
training sets, separability (J-M) of the all-leaf selections, statistical comparison of methods
(Friedman + Nemenyi, Wilcoxon-Holm), composite ranking, consensus disease-specific features."""
from __future__ import annotations

import pickle
import warnings
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, rankdata, spearmanr, studentized_range, wilcoxon

from common import WORK, cfg, load, save
from sp import fs_methods as fm
from sp import models
from stage_FS import OUT, build_pool, units

C = cfg()
KS = (5, 10, 15, 20)
METHODS = [  # name, family, short principle, reference key
    ("Pearson r", "Filter", "|point-biserial correlation| with disease status", "Pearson"),
    ("ANOVA F", "Filter", "one-way ANOVA F-value (between / within class variance)", "Abdulridha 2023"),
    ("Fisher score", "Filter", "between-class / within-class scatter", "Duda 2001"),
    ("Chi-square", "Filter", "χ² of class × quantile-bin (10) contingency table", "Abdulridha 2023"),
    ("Mutual information", "Filter", "k-NN estimate of I(feature; class)", "Kraskov 2004"),
    ("ReliefF", "Filter", "nearest hit / nearest miss differences (k = 10, L1)", "Kononenko 1994; Mahlein 2013"),
    ("J–M (univariate)", "Filter", "Jeffries–Matusita distance of each feature", "Das 2020"),
    ("mRMR", "Filter", "max relevance (F) / min redundancy (|r|) quotient", "Peng 2005"),
    ("SPA", "Filter", "successive projections: least collinear chain; length by inner CV", "Araújo 2001; Zhu 2017"),
    ("MC-UVE", "Filter", "stability of PLS coefficients vs artificial noise variables", "Centner 1996; Cai 2008"),
    ("CWT scalogram", "Filter", "J–M separability scalogram of Mexican-hat wavelet features", "Cheng 2010"),
    ("SVM-RFE", "Wrapper", "recursive elimination by |w| of a linear SVM", "Guyon 2002; Wei 2021; Liu 2024"),
    ("RF-RFE", "Wrapper", "recursive elimination by Balanced-RF importance", "Wei 2021; Liu 2024"),
    ("CARS", "Wrapper", "Monte-Carlo PLS, exponential decay + adaptive reweighted sampling", "Li 2009; Zhu 2017"),
    ("SFFS (QDA)", "Wrapper", "floating forward search, criterion = inner-CV QDA balanced accuracy", "Pudil 1994; Mustafa 2023"),
    ("SFFS (J–M)", "Wrapper", "floating forward search, criterion = multivariate J–M distance", "Pudil 1994; Das 2020"),
    ("Genetic algorithm", "Wrapper", "binary GA, fitness = inner-CV QDA balanced accuracy − size penalty", "Leardi 1992; Nagasubramanian 2018"),
    ("RF importance", "Embedded", "Balanced Random Forest mean decrease in Gini", "Breiman 2001; Chen 2004"),
    ("CART importance", "Embedded", "Gini importance of a pruned CART tree (equal priors)", "Breiman 1984; Das 2020"),
    ("Boruta", "Embedded", "all-relevant: real vs shuffled shadow features, binomial test", "Kursa 2010; Mustafa 2023"),
    ("PLS-VIP", "Embedded", "variable importance in projection of PLS-DA", "Wold 2001; Chong 2005"),
    ("LASSO", "Embedded", "L1-penalised logistic regression (order of entry)", "Tibshirani 1996"),
    ("Gradient boosting", "Embedded", "gradient-boosted trees split-gain importance (XGBoost family)", "Friedman 2001; Chen 2016"),
    ("Consensus (Borda)", "Ensemble", "rank aggregation of all methods inside each training set", "Saeys 2008"),
]
NAMES = [m[0] for m in METHODS]
FAMILY = {m[0]: m[1] for m in METHODS}
EQUIV = ["Pearson r", "Fisher score"]          # identical rankings to ANOVA F for two classes (checked)
UNIQUE = [m for m in NAMES if m not in EQUIV]


def load_units():
    R = {}
    for f in sorted(OUT.glob("*.pkl")):
        with open(f, "rb") as fh:
            R[f.stem] = pickle.load(fh)
    return R


def series_pos(meta):
    s = meta["series"].to_numpy()
    p = meta["position"].to_numpy(float)
    return s, p


def tol_match(a, b, ser, pos, tol=10):
    """Number of features of a with a partner in b (same feature, or same spectral series within tol nm)."""
    n = 0
    for i in a:
        if i in b:
            n += 1
            continue
        if np.isfinite(pos[i]) and any(ser[j] == ser[i] and np.isfinite(pos[j]) and abs(pos[j] - pos[i]) <= tol for j in b):
            n += 1
    return n


def borda(Ru, Xz, methods, depth=20):
    pts = {}
    for m in methods:
        r = Ru.get(m, {})
        if "rank" not in r or r.get("space") == "cwt":
            continue
        top = r["sets"][depth] if "sets" in r and depth in r["sets"] else fm.guard_topk(r["rank"], Xz, depth)
        for pos_, j in enumerate(top):
            pts[j] = pts.get(j, 0) + (depth - pos_)
    return np.array(sorted(pts, key=lambda j: -pts[j])), pts


def main():
    D, P, cw = build_pool()
    y, F = D["y"], D["folds"]
    X = P.X
    meta = P.meta
    ser, pos = series_pos(meta)
    U = load_units()
    test_units = [u for u in U if u != "ALL"]
    import os
    if not os.environ.get("FS_PARTIAL"):
        assert len(test_units) == 20, test_units
    out = {"methods": pd.DataFrame(METHODS, columns=["Method", "Family", "Principle", "Reference"])}

    # ------------------------------------------------ consensus (Borda) inside each unit
    for u, Ru in U.items():
        Xz = fm.zs(X[Ru["train"]])
        o, pts = borda(Ru, Xz, [m for m in UNIQUE if m != "Consensus (Borda)"])
        Ru["Consensus (Borda)"] = {"rank": o, "score": pts}

    # ------------------------------------------------ selections
    def select(Ru, m, k, guard, Xz, Wz):
        r = Ru[m]
        if "rank" not in r:
            return None
        if "sets" in r and k in r["sets"]:
            return list(r["sets"][k])
        Z = Wz if r.get("space") == "cwt" else Xz
        return fm.guard_topk(r["rank"], Z, k) if guard else list(r["rank"][:k])

    rows, sels = [], {}
    brf = models.brf(C, 300)
    brf.set_params(n_jobs=4)
    for u in test_units:
        Ru = U[u]
        tr, te = Ru["train"], Ru["test"]
        Xz = fm.zs(X[tr])
        Wz = fm.zs(cw["X"][tr])
        for m in NAMES:
            if "error" in Ru.get(m, {}):
                continue
            space = Ru[m].get("space")
            M = cw["X"] if space == "cwt" else X
            for guard in (False, True):
                for k in KS:
                    S = select(Ru, m, k, guard, Xz, Wz)
                    if not S:
                        continue
                    sels[(m, guard, k, u)] = S
                    rec = {"Unit": u, "Scheme": u[:2], "Method": m, "Family": FAMILY[m], "Guard": "yes" if guard else "no",
                           "k": k, "Size": len(S)}
                    for cname, mk in (("QDA", models.qda), ("LDA", models.lda)):
                        pr, sc = models.fit_predict(mk("equal"), M[tr][:, S], y[tr], M[te][:, S])
                        rec[f"BA {cname}"] = fm.ba(y[te], pr)
                        if cname == "QDA":
                            from sklearn.metrics import roc_auc_score
                            rec["AUC QDA"] = roc_auc_score(y[te], sc)
                    if k == 10:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            brf.fit(M[tr][:, S], y[tr])
                        rec["BA RF"] = fm.ba(y[te], brf.predict(M[te][:, S]))
                    rows.append(rec)
            # native subset
            nat = Ru[m].get("native")
            if nat is not None and len(nat) > 0:
                nat = list(nat)
                rec = {"Unit": u, "Scheme": u[:2], "Method": m, "Family": FAMILY[m], "Guard": "native", "k": len(nat), "Size": len(nat)}
                if len(nat) <= 30:
                    pr, _ = models.fit_predict(models.qda("equal"), M[tr][:, nat], y[tr], M[te][:, nat])
                    rec["BA QDA"] = fm.ba(y[te], pr)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    brf.fit(M[tr][:, nat], y[tr])
                rec["BA RF"] = fm.ba(y[te], brf.predict(M[te][:, nat]))
                rows.append(rec)
        print("evaluated", u, flush=True)
    ev = pd.DataFrame(rows)
    out["eval"] = ev

    # ------------------------------------------------ four-tier reference (Part C) on the same units
    Cc = load("partC")
    fb = Cc["fold_ba"]
    v3idx = [i for i, f in enumerate(F["V3"]) if f["rep"] == 0]
    ref = []
    for pipe, lab, size in (("QDA on CART features", "Four-tier CART-13 (Part C)", 13), ("QDA on RF features", "Four-tier RF-17 (Part C)", 17)):
        for u in test_units:
            sch, i = u.split("_")
            unit = v3idx[int(i)] if sch == "V3" else int(i)
            q = fb[(fb.Pipeline == pipe) & (fb.Scheme == sch) & (fb.Unit == unit)]
            ref.append({"Unit": u, "Method": lab, "BA QDA": float(q["BA"].iloc[0]), "Size": size})
    out["fourtier_ref"] = pd.DataFrame(ref)

    # ------------------------------------------------ summary tables
    g = ev[ev.Guard != "native"].groupby(["Method", "Family", "Guard", "k"])
    summ = g.agg(**{"Mean size": ("Size", "mean"), "BA QDA": ("BA QDA", "mean"), "SD QDA": ("BA QDA", "std"),
                    "BA LDA": ("BA LDA", "mean"), "AUC QDA": ("AUC QDA", "mean"), "BA RF": ("BA RF", "mean"),
                    "SD RF": ("BA RF", "std")}).reset_index()
    out["summary"] = summ
    nat = ev[ev.Guard == "native"].groupby(["Method", "Family"]).agg(**{"Mean size": ("Size", "mean"), "Min size": ("Size", "min"),
                                                                      "Max size": ("Size", "max"), "BA QDA": ("BA QDA", "mean"),
                                                                      "BA RF": ("BA RF", "mean")}).reset_index()
    out["native"] = nat

    # ------------------------------------------------ stability (k = 10)
    p_all = X.shape[1]
    st = []
    for m in NAMES:
        for guard in (False, True):
            L = [sels.get((m, guard, 10, u)) for u in test_units]
            L = [l for l in L if l]
            if len(L) < 2:
                continue
            cw_space = U[test_units[0]][m].get("space") == "cwt"
            ki, je, jt = [], [], []
            for a, b in combinations(L, 2):
                k_ = len(a)
                r_ = len(set(a) & set(b))
                pp = len(cw["names"]) if cw_space else p_all
                if len(a) == len(b) and 0 < k_ < pp:
                    ki.append((r_ * pp - k_ * k_) / (k_ * (pp - k_)))
                je.append(r_ / len(set(a) | set(b)))
                if cw_space:
                    jt.append(je[-1])
                else:
                    mt = (tol_match(a, set(b), ser, pos) + tol_match(b, set(a), ser, pos)) / 2
                    jt.append(mt / (len(a) + len(b) - mt))
            st.append({"Method": m, "Family": FAMILY[m], "Guard": "yes" if guard else "no", "Lists": len(L),
                       "Kuncheva index": np.mean(ki) if ki else np.nan, "Jaccard (exact)": np.mean(je),
                       "Jaccard (±10 nm)": np.mean(jt), "SD Jaccard (±10 nm)": np.std(jt, ddof=1)})
    out["stability"] = pd.DataFrame(st)

    # ------------------------------------------------ full-data selections (all leaves)
    RA = U["ALL"]
    XzA = fm.zs(X)
    WzA = fm.zs(cw["X"])
    from sklearn.model_selection import StratifiedKFold
    v1 = [(f["train"], f["test"]) for f in F["V1"]]
    full = []
    for m in NAMES:
        if "rank" not in RA.get(m, {}):
            continue
        cwt = RA[m].get("space") == "cwt"
        M, Z, nm = (cw["X"], WzA, cw["names"]) if cwt else (X, XzA, meta["name"].to_numpy())
        S = select(RA, m, 10, True, XzA, WzA)
        jmv = fm.jm_multi(Z[:, S], y)
        pred = np.zeros(len(y), int)
        for tr, te in v1:
            pred[te], _ = models.fit_predict(models.qda("equal"), M[tr][:, S], y[tr], M[te][:, S])
        rr = np.abs(np.corrcoef(Z[:, S], rowvar=False))
        auc = fm.univariate(M[:, S], y)
        from sp.stats import auc_free
        a, _ = auc_free(M[:, S], y)
        full.append({"Method": m, "Family": FAMILY[m], "Selected (top-10, redundancy-controlled)": ", ".join(nm[S]),
                     "Native subset size": (len(RA[m]["native"]) if RA[m].get("native") is not None else np.nan),
                     "J–M": jmv, "QDA BA (V1, leaf 10-fold)": fm.ba(y, pred),
                     "Mean |r| within set": (rr.sum() - len(S)) / (len(S) * (len(S) - 1)), "Mean AUC": float(np.mean(a)),
                     "Runtime all leaves (s)": RA[m].get("sec", np.nan), "idx": S, "space": "cwt" if cwt else "pool"})
    out["full"] = pd.DataFrame(full)
    out["full_rank"] = {m: (RA[m]["rank"][:50] if "rank" in RA.get(m, {}) else None) for m in NAMES}
    out["full_score"] = {m: RA[m].get("score") for m in NAMES if m in RA}
    out["full_info"] = {m: RA[m].get("info") for m in NAMES if m in RA}
    out["full_native"] = {m: RA[m].get("native") for m in NAMES if m in RA}
    out["full_sffs"] = {m: (RA[m].get("sets"), RA[m].get("crit")) for m in ("SFFS (QDA)", "SFFS (J–M)")}
    out["ga_hist"] = RA["Genetic algorithm"].get("info", {}).get("history")
    out["cars_sizes"] = RA["CARS"].get("info", {}).get("subset sizes")
    out["univariate_all"] = RA["univariate"]

    # ------------------------------------------------ statistical comparison: QDA BA, k = 10, redundancy-controlled
    q = ev[(ev.Guard == "yes") & (ev.k == 10)].pivot_table(index="Unit", columns="Method", values="BA QDA")
    q = q[[m for m in UNIQUE if m in q.columns]]
    fr = friedmanchisquare(*[q[c].values for c in q.columns])
    ranks = q.rank(axis=1, ascending=False)
    mr = ranks.mean().sort_values()
    kk, N = q.shape[1], q.shape[0]
    qa = studentized_range.ppf(0.95, kk, np.inf) / np.sqrt(2)
    cd = qa * np.sqrt(kk * (kk + 1) / (6 * N))
    best = q.mean().idxmax()
    wr = []
    for c in q.columns:
        if c == best:
            continue
        d = q[best] - q[c]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = wilcoxon(d).pvalue if (d != 0).any() else 1.0
        wr.append({"Best": best, "Other": c, "Mean difference": d.mean(), "Best better": int((d > 0).sum()),
                   "Other better": int((d < 0).sum()), "p": p})
    wr = pd.DataFrame(wr).sort_values("p")
    m_ = len(wr)
    wr["Holm p"] = np.minimum(1, np.maximum.accumulate((m_ - np.arange(m_)) * wr["p"].values))
    wr["Significant (Holm 0.05)"] = np.where(wr["Holm p"] < 0.05, "yes", "no")
    out["friedman"] = {"chi2": fr.statistic, "p": fr.pvalue, "k": kk, "N": N, "q_alpha": qa, "CD": cd, "best": best}
    out["mean_ranks"] = mr.rename("Mean rank").reset_index().rename(columns={"index": "Method"})
    out["wilcoxon"] = wr
    out["ba_matrix"] = q

    # ------------------------------------------------ composite ranking
    s10 = summ[(summ.Guard == "yes") & (summ.k == 10)].set_index("Method")
    stb = out["stability"][out["stability"].Guard == "yes"].set_index("Method")
    fu = out["full"].set_index("Method")
    comp = pd.DataFrame({"BA QDA (k=10)": s10["BA QDA"], "BA RF (k=10)": s10["BA RF"],
                         "Stability Jaccard (±10 nm)": stb["Jaccard (±10 nm)"], "J–M (all leaves)": fu["J–M"]}).loc[UNIQUE]
    for c in comp.columns:
        comp[f"Rank {c}"] = rankdata(-comp[c].values, method="average")
    comp["Mean rank"] = comp[[c for c in comp.columns if c.startswith("Rank")]].mean(axis=1)
    comp["Overall rank"] = rankdata(comp["Mean rank"], method="min").astype(int)
    comp.insert(0, "Family", [FAMILY[m] for m in comp.index])
    out["composite"] = comp.sort_values("Overall rank").reset_index().rename(columns={"index": "Method"})

    # ------------------------------------------------ best methods vs the four-tier sets of Part C (same 20 units)
    fr4 = out["fourtier_ref"].pivot_table(index="Unit", columns="Method", values="BA QDA")
    vs = []
    for m in list(out["composite"]["Method"].head(6)) + ["Consensus (Borda)"]:
        if m not in q.columns:
            continue
        for ref_ in fr4.columns:
            d = (q[m] - fr4[ref_]).dropna()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                p = wilcoxon(d).pvalue if (d != 0).any() else 1.0
            vs.append({"Method (top-10)": m, "Four-tier set": ref_, "Method BA": q[m].mean(), "Four-tier BA": fr4[ref_].mean(),
                       "Mean difference": d.mean(), "Method better": int((d > 0).sum()), "Four-tier better": int((d < 0).sum()),
                       "Wilcoxon p": p})
    out["vs_fourtier"] = pd.DataFrame(vs).drop_duplicates(["Method (top-10)", "Four-tier set"])

    # ------------------------------------------------ consensus disease-specific features
    freq = {}
    for m in UNIQUE:
        if m == "CWT scalogram":
            continue
        L = [sels.get((m, True, 10, u)) for u in test_units]
        L = [l for l in L if l]
        cand = sorted(set(j for l in L for j in l))
        for j in cand:
            f_ = np.mean([tol_match([j], set(l), ser, pos) > 0 for l in L])
            freq.setdefault(j, {})[m] = f_
    F_ = pd.DataFrame(freq).T.fillna(0.0)
    F_ = F_[[m for m in UNIQUE if m in F_.columns]]
    F_["Consensus score"] = F_.mean(axis=1)
    F_["Methods ≥ 50 %"] = (F_[[c for c in F_.columns if c != "Consensus score"]] >= 0.5).sum(axis=1)
    F_ = F_.sort_values("Consensus score", ascending=False)
    # non-maximum suppression: one representative per series within ±10 nm
    reps = []
    for j in F_.index:
        if any((j == r) or (np.isfinite(pos[j]) and ser[r] == ser[j] and np.isfinite(pos[r]) and abs(pos[r] - pos[j]) <= 10) for r in reps):
            continue
        reps.append(j)
    t1 = Cc["tier1"].set_index("name")
    cons = []
    for j in reps[:25]:
        nm = meta["name"].iloc[j]
        r = t1.loc[nm]
        cons.append({"Feature": nm, "Type": meta["type"].iloc[j], "Wavelength (nm)": pos[j],
                     "Consensus score": F_.loc[j, "Consensus score"], "Methods ≥ 50 % of training sets": int(F_.loc[j, "Methods ≥ 50 %"]),
                     "AUC": r["auc"], "Direction in diseased": "higher" if r["mean1"] > r["mean0"] else "lower",
                     "Hedges g": r["g"], "Mixed-model q": r["mm_q"], "idx": j})
    cons = pd.DataFrame(cons)
    out["consensus"] = cons
    out["consensus_freq"] = F_.loc[cons["idx"].values].assign(Feature=cons["Feature"].values)
    S = fm.guard_topk(cons["idx"].values, XzA, 10)
    pred = np.zeros(len(y), int)
    for tr, te in v1:
        pred[te], _ = models.fit_predict(models.qda("equal"), X[tr][:, S], y[tr], X[te][:, S])
    out["consensus_set"] = {"idx": S, "names": meta["name"].to_numpy()[S].tolist(), "J–M": fm.jm_multi(XzA[:, S], y),
                            "QDA BA V1": fm.ba(y, pred)}

    # ------------------------------------------------ redundancy-control effect, runtime, checks
    gq = summ[summ.k == 10].pivot_table(index="Method", columns="Guard", values="BA QDA")
    out["guard_effect"] = gq.rename(columns={"no": "Plain top-10", "yes": "Redundancy-controlled top-10"}).assign(
        Difference=lambda d: d["Redundancy-controlled top-10"] - d["Plain top-10"]).reset_index()
    rt = []
    for m in NAMES:
        secs = [U[u][m].get("sec", np.nan) for u in U if m in U[u] and isinstance(U[u][m], dict)]
        rt.append({"Method": m, "Family": FAMILY[m], "Mean seconds per training set": np.nanmean(secs) if secs else np.nan,
                   "All leaves (s)": U["ALL"].get(m, {}).get("sec", np.nan)})
    out["runtime"] = pd.DataFrame(rt)
    out["errors"] = {(u, m): U[u][m]["error"] for u in U for m in NAMES if isinstance(U[u].get(m), dict) and "error" in U[u][m]}
    out["checks"] = checks(U, X, y, cw, F, test_units)
    out["pool_meta"] = meta
    out["cwt"] = {"names": cw["names"], "shape": cw["shape"], "wl": cw["wl"], "scales": cw["scales"], "valid": cw["valid"]}
    out["test_units"] = test_units
    save(out, "partFS_partial" if os.environ.get("FS_PARTIAL") else "partFS")
    pd.set_option("display.width", 250)
    print(out["composite"].round(3).to_string())
    print(out["friedman"])
    print(cons.head(15).to_string())
    print("errors:", list(out["errors"]))


def checks(U, X, y, cw, F, test_units):
    from scipy.stats import chi2_contingency
    rows = []
    A = U["ALL"]
    u = A["univariate"]
    rho = min(spearmanr(u["abs_r"], u["F"]).statistic, spearmanr(u["fisher"], u["F"]).statistic)
    rows.append(("Filter", "Pearson |r|, ANOVA F and Fisher score rank features identically (two classes: r² = F/(F+n−2), Fisher ∝ F)",
                 "Spearman correlation of the three score vectors (all leaves)", f"min ρ = {rho:.6f}", "PASS" if rho > 0.999999 else "FLAG"))
    from sklearn.feature_selection import f_classif
    Fs, _ = f_classif(X, y)
    d = np.max(np.abs(Fs - u["F"]) / Fs)
    rows.append(("Filter", "ANOVA F implementation", "own formula vs scikit-learn f_classif", f"max relative Δ = {d:.1e} (floating-point level)", "PASS" if d < 1e-5 else "FAIL"))
    j = int(np.argmax(u["F"]))
    chi_own = fm.chi2_binned(X[:, [j]], y)[0]
    ranks = X[:, j].argsort().argsort()
    b = np.minimum(ranks * 10 // len(y), 9)
    tab = np.array([[((b == k) & (y == c)).sum() for k in range(10)] for c in (0, 1)])
    chi_ref = chi2_contingency(tab, correction=False)[0]
    rows.append(("Filter", "Chi-square implementation", "own vectorised χ² vs scipy chi2_contingency (best feature)",
                 f"{chi_own:.4f} vs {chi_ref:.4f}", "PASS" if abs(chi_own - chi_ref) < 1e-6 * chi_ref else "FAIL"))
    S = A["SFFS (J–M)"]["sets"][5]
    Z = fm.zs(X)
    j1 = fm.jm_multi(Z[:, S], y)
    a = models.bhattacharyya_explicit(X[:, S], y)
    j2 = 2 * (1 - np.exp(-a))
    rows.append(("Tier-3 criterion", "J–M used by SFFS (J–M) and the evaluation", "Cholesky on standardised vs explicit inverse on raw features",
                 f"|Δ| = {abs(j1 - j2):.1e}", "PASS" if abs(j1 - j2) < 1e-8 else "FAIL"))
    tr, te = F["V4"][0]["train"], F["V4"][0]["test"]
    S10 = A["SFFS (QDA)"]["sets"][10]
    p1 = fm.qda_fast(fm.zs(X[tr][:, S10]), y[tr], (X[te][:, S10] - X[tr][:, S10].mean(0)) / X[tr][:, S10].std(0))
    p2, _ = models.fit_predict(models.qda("equal"), X[tr][:, S10], y[tr], X[te][:, S10])
    agree = (p1 == p2).mean()
    rows.append(("Wrapper", "Fast QDA used inside SFFS / GA", "own QDA vs scikit-learn QDA (equal priors), V4 split 1",
                 f"{100 * agree:.2f} % identical predictions", "PASS" if agree > 0.995 else "FLAG"))
    v = A["PLS-VIP"]["score"]
    ms = float(np.mean(v ** 2))
    rows.append(("Embedded", "PLS-VIP normalisation", "mean of VIP² must equal 1", f"{ms:.6f}", "PASS" if abs(ms - 1) < 1e-6 else "FAIL"))
    ch = fm.spa_chain(fm.zs(X), int(A["SPA"]["rank"][0]), 5)
    rows.append(("Filter", "SPA chain", "chain recomputed from the reported start variable equals the reported chain",
                 "identical" if list(ch) == list(A["SPA"]["rank"][:5]) else "different", "PASS" if list(ch) == list(A["SPA"]["rank"][:5]) else "FAIL"))
    leak = 0
    for uu in test_units:
        f = U[uu]
        g = load("data")["groups"]
        leak += len(set(g[f["train"]]) & set(g[f["test"]]))
    rows.append(("Design", "No plot in both training and test leaves", "intersection of plot sets over the 20 units", f"{leak} shared plots", "PASS" if leak == 0 else "FAIL"))
    t = np.arange(-200, 201, dtype=float)
    sig = np.exp(-t ** 2 / (2 * 8 ** 2))
    W = fm.cwt_mexh(sig[None, :], t, [2, 4, 8, 16, 32])[0, :, 200]
    rows.append(("Filter", "CWT implementation", "Mexican-hat response to a Gaussian peak (σ = 8 nm) is largest at the scale ≈ σ",
                 f"best scale {[2, 4, 8, 16, 32][int(np.argmax(W))]} nm", "PASS" if [2, 4, 8, 16, 32][int(np.argmax(W))] in (8, 16) else "FLAG"))
    bor = A["Boruta"]["info"]
    rows.append(("Embedded", "Boruta convergence", "confirmed / tentative / rejected after the last run (all leaves)",
                 f"{bor['confirmed']} / {bor['tentative']} / {bor['rejected']} after {bor['runs']} runs", "PASS" if bor["tentative"] < 0.2 * X.shape[1] else "FLAG"))
    return pd.DataFrame(rows, columns=["Step", "What was checked", "Method", "Result", "Status"])


if __name__ == "__main__":
    main()
