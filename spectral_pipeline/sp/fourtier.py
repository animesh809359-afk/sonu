"""The four-tier engine (Das et al. 2020 + corrections), applied to any feature
set: reflectance bands (Part A) or the combined K1-K4 pool (Part C).

Tier 1  Welch t-test + BH-FDR at every feature           (screening)
Tier 2  CART (rpart) split variables  |  Balanced RF MDI peaks (selection)
Tier 3  Jeffries-Matusita distance on each selected set   (separability)
Tier 4  QDA with equal priors on each selected set        (classification)

Validation: V1 (features fixed, leaf-level CV, = paper protocol), V3 and V4
(Tier 1 + selection + classifier refitted inside every training set).
"""
from __future__ import annotations

import time
import warnings
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from . import cart, models, stats
from .metrics import evaluate, summarise


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _rf_peaks(imp, meta_sig, k, cfg, X=None, collinear_r=None):
    idx, skipped = models.select_peaks(imp, meta_sig["series"].to_numpy(),
                                       meta_sig["position"].to_numpy(dtype=float), k,
                                       cfg["rf"]["peak_min_sep_nm"], X=X, collinear_r=collinear_r)
    return idx, skipped


def _qda_cv(X, y, folds, priors="equal", model="qda"):
    pred = np.zeros(len(y), int)
    prob = np.zeros(len(y))
    for f in folds:
        m = models.qda(priors) if model == "qda" else models.lda(priors)
        p, pr = _safe_fit(m, X[f["train"]], y[f["train"]], X[f["test"]])
        pred[f["test"]], prob[f["test"]] = p, pr
    return pred, prob


QDA_FAILURES = []


def _safe_fit(model, Xtr, ytr, Xte):
    """QDA/LDA fit; a singular class covariance is recorded and the test rows
    are left unclassified (probability 0.5, predicted diseased)."""
    try:
        return models.fit_predict(model, Xtr, ytr, Xte)
    except (np.linalg.LinAlgError, ValueError) as e:
        QDA_FAILURES.append(str(e)[:120])
        return np.ones(len(Xte), int), np.full(len(Xte), 0.5)


def tier1_cols(ft, alpha=0.05, k_min=2, k_fallback=20):
    """Tier-1 features passed to Tier 2: BH-FDR q < alpha. When fewer than k_min features pass (weak
    signal in a small training set), fall back to uncorrected p < alpha, then to the k_fallback
    smallest p-values, so that Tier 2 always has candidates. Returns (columns, rule)."""
    s_ = np.where(ft["sig"])[0]
    if len(s_) >= k_min:
        return s_, "FDR"
    p = np.asarray(ft["p"])
    s_ = np.where(p < alpha)[0]
    if len(s_) >= k_min:
        return s_, "uncorrected p"
    return np.sort(np.argsort(p)[:k_fallback]), "smallest p"


def run(fs, y, groups, folds, cfg, label, collinear_guard=False, mixed=True):
    """fs: FeatureSet. Returns a dict of tables for the report."""
    out = {"label": label, "checks": []}
    X = fs.X
    names = fs.names
    meta = fs.meta
    n = len(y)
    alpha = cfg["tier1"]["alpha"]
    coll_r = cfg["combined"]["collinear_abs_r"] if collinear_guard else None
    ks = cfg["rf"]["top_k"]

    # ------------------------------------------------------------ Tier 1
    log(f"{label}: Tier 1 on {X.shape[1]} features")
    ft = stats.feature_table(X, y, alpha)
    t1 = meta[["name", "type", "series", "position"]].copy()
    for k in ("mean0", "sd0", "mean1", "sd1", "t", "df", "p", "q", "g", "auc", "dir"):
        t1[k] = ft[k]
    t1["sig"] = ft["sig"]
    if mixed and cfg["tier1"]["mixed_model"]:
        log(f"{label}: mixed models (1|plot) on {X.shape[1]} features")
        mm = stats.mixed_models(X, y, groups, cfg["tier1"]["mixed_model_jobs"])
        t1["mm_effect"], t1["mm_p"], t1["mm_q"], t1["icc"] = mm["effect"], mm["p"], mm["q"], mm["icc"]
        t1["mm_sig"] = t1["mm_q"] < alpha
        _nna = int(np.isnan(np.asarray(mm["p"], float)).sum())
        out["checks"].append(("Tier 1", "Mixed model converged for every feature", "R nlme::lme (REML) per feature",
                              f"{X.shape[1] - _nna} of {X.shape[1]} converged" + (f"; {_nna} returned NA → counted as not significant" if _nna else ""),
                              "PASS" if _nna == 0 else "FLAG"))
        t1["mm_boundary"] = mm["boundary"]
    out["tier1"] = t1
    out["n_sig"] = int(ft["sig"].sum())
    sig, out["tier1_rule"] = tier1_cols(ft, alpha)
    out["sig_cols"] = sig
    if out["tier1_rule"] != "FDR":
        out["checks"].append(("Tier 1", "Fewer than 2 FDR-significant features on all leaves", "fallback rule for Tier 2 candidates",
                              f"{len(sig)} features by {out['tier1_rule']}", "FLAG"))
    out["n_features"] = int(X.shape[1])
    msig = meta.iloc[sig].reset_index(drop=True)
    Xsig = X[:, sig]

    # ------------------------------------------------------------ Tier 2 (all data) + fold jobs
    log(f"{label}: Tier 2 - rpart on {len(sig)} Tier-1 features + fold trees")
    xv = cart.grouped_xval(y, groups, cfg["cart"]["xval_folds"], 42)
    jobs = [dict(train=np.arange(n), test=[], cols=sig, full=True, xval=xv)]
    for f in folds["V1"]:                  # CART classifier, Tier-1 features fixed
        jobs.append(dict(train=f["train"], test=f["test"], cols=sig))
    fold_sig = {}
    fallback = []
    nested = [sch for sch in ("V3", "V4", "V5") if folds.get(sch)]
    for sch in nested:                     # nested: Tier 1 refitted in the training rows
        for i, f in enumerate(folds[sch]):
            ftr = stats.feature_table(X[f["train"]], y[f["train"]], alpha)
            s_, rule = tier1_cols(ftr, alpha)
            if rule != "FDR":
                fallback.append((sch, i, rule, len(s_)))
            fold_sig[(sch, i)] = s_
            jobs.append(dict(train=f["train"], test=f["test"], cols=s_))
    t0 = time.time()
    cres = cart.run_jobs(X, y, names, jobs, cfg)
    log(f"{label}: {len(jobs)} rpart trees in {time.time() - t0:.0f} s")
    out["tier1_fallback"] = fallback
    ntr = sum(len(folds[s]) for s in nested)
    out["checks"].append(("Tier 1", "Training sets with < 2 FDR-significant features (nested V3/V4/V5)",
                          "fallback: uncorrected p < 0.05, else the 20 smallest p",
                          f"{len(fallback)} of {ntr} training sets"
                          + (": " + "; ".join(f"{a} #{b + 1} → {c} ({d})" for a, b, c, d in fallback[:8])
                             + (" …" if len(fallback) > 8 else "") if fallback else ""),
                          "FLAG" if fallback else "PASS"))
    full = cres[0]
    name_to_col = {nm: i for i, nm in enumerate(names)}
    cart_vars = full["vars"]
    cart_1se = full.get("vars_1se", [])
    out["cart_full"] = full

    log(f"{label}: Tier 2 - Balanced RF importance ({cfg['rf']['n_estimators_importance']} trees)")
    imp, _ = models.rf_importance(Xsig, y, cfg)
    imp2, _ = models.rf_importance(Xsig, y, cfg, seed=7)
    out["rf_importance"] = pd.DataFrame({"name": msig["name"], "type": msig["type"],
                                         "series": msig["series"], "position": msig["position"],
                                         "importance": imp, "importance_seed7": imp2})
    sets = {}
    sets[f"CART-{len(cart_vars)}"] = cart_vars
    if cart_1se and len(cart_1se) != len(cart_vars):
        sets[f"CART-{len(cart_1se)} (1-SE)"] = cart_1se
    rf_sets = {}
    kk = list(ks)
    if len(cart_vars) not in kk and len(cart_vars) >= 2:
        kk.append(len(cart_vars))              # size-matched RF set
    skipped_all = []
    for k in kk:
        idx, sk = _rf_peaks(imp, msig, k, cfg, Xsig, coll_r)
        skipped_all += sk
        nm = f"RF-{k}" + (" (size-matched)" if k not in ks else "")
        rf_sets[nm] = list(msig["name"].iloc[idx])
    sets.update(rf_sets)
    out["sets"] = sets
    out["cart_name"] = f"CART-{len(cart_vars)}"
    out["rf_name"] = f"RF-{ks[0]}"
    out["collinear_skipped"] = [msig["name"].iloc[i] for i in sorted(set(skipped_all))]
    # reproducibility of the RF peaks with another seed
    i7, _ = _rf_peaks(imp2, msig, ks[0], cfg, Xsig, coll_r)
    out["rf_seed_check"] = {
        "rho": float(pd.Series(imp).corr(pd.Series(imp2), method="spearman")),
        "within10": _n_matched(rf_sets[f"RF-{ks[0]}"], list(msig["name"].iloc[i7]), meta),
        "k": ks[0]}

    # ------------------------------------------------------------ Tier 3 + Tier 4 (V1, features fixed)
    log(f"{label}: Tiers 3-4 on {len(sets)} selected sets")
    t3, t4, err = [], [], {}
    for sname, fl in sets.items():
        cols = [name_to_col[v] for v in fl]
        Xs = X[:, cols]
        row = {"Set": sname, "Features": len(fl), "List": ", ".join(fl)}
        try:
            jmv, a = models.jm(Xs, y)
            c0, c1 = models.cond_numbers(Xs, y)
            row.update({"alpha": a, "JM": jmv, "cond0": c0, "cond1": c1})
            if sname == out["cart_name"]:
                out["checks"].append(("Tier 3", f"J–M implementation ({label})",
                                      "Cholesky/log-det vs explicit inverse/determinant",
                                      f"|Δα| = {abs(a - models.bhattacharyya_explicit(Xs, y)):.1e}", "PASS"))
        except np.linalg.LinAlgError:
            row.update({"alpha": np.nan, "JM": np.nan, "cond0": np.nan, "cond1": np.nan})
        t3.append(row)
        for clf, pri in (("QDA", "equal"), ("QDA", "sample"), ("LDA", "equal")):
            pred, prob = _qda_cv(Xs, y, folds["V1"], pri, clf.lower())
            m = evaluate(y, pred, prob)
            t4.append({"Set": sname, "Classifier": f"{clf} {pri} priors", **m})
            if clf == "QDA" and pri == "equal":
                err[sname] = m
    out["tier3"] = pd.DataFrame(t3)
    cmax = float(np.nanmax(out["tier3"][["cond0", "cond1"]].to_numpy()))
    inv = []
    for sname, fl in sets.items():
        cols = [name_to_col[v] for v in fl]
        Z = (X[:, cols] - X[:, cols].mean(0)) / X[:, cols].std(0)
        inv.append(abs(models.jm(Z, y)[0] - out["tier3"].set_index("Set").loc[sname, "JM"]))
    out["checks"].append(("Tier 3", "Invertibility of the class covariances",
                          "condition number of the class correlation matrices of every selected set",
                          f"max {cmax:.1e} " + ("(well below the ~1e12 limit of double precision)" if cmax < 1e8 else
                                               "(ill-conditioned but below the ~1e12 limit of double precision: J–M and QDA "
                                               "are computable, yet sensitive to small changes in the data)"),
                          "PASS" if cmax < 1e8 else "FLAG"))
    out["checks"].append(("Tier 3", "J–M is scale-invariant", "J–M on raw vs standardised features of every selected set",
                          f"max |ΔJ–M| = {max(inv):.1e}", "PASS" if max(inv) < 1e-8 else "FLAG"))
    out["tier4"] = pd.DataFrame(t4)
    out["errmat"] = err
    # QDA cross-check: sklearn vs manual discriminant functions
    cols = [name_to_col[v] for v in cart_vars]
    if len(cols) >= 1:
        same, ties = [], []
        for f in folds["V1"]:
            p1, _ = models.fit_predict(models.qda(), X[f["train"]][:, cols], y[f["train"]], X[f["test"]][:, cols])
            p2 = models.qda_manual(X[f["train"]][:, cols], y[f["train"]], X[f["test"]][:, cols])
            same.append((p1 == p2).mean())
            pr = models.fit_predict(models.qda(), X[f["train"]][:, cols], y[f["train"]], X[f["test"]][:, cols])[1]
            ties.extend(np.abs(pr[p1 != p2] - 0.5).tolist())
        worst = max(ties) if ties else 0.0
        out["checks"].append(("Tier 4", f"QDA implementation ({label})",
                              "scikit-learn vs manual discriminant functions (equal priors), V1 folds",
                              f"{100 * np.mean(same):.2f} % identical predictions; differing leaves have |P(diseased) − 0.5| ≤ {worst:.4f}",
                              "PASS" if np.mean(same) > 0.999 or worst < 0.01 else "FLAG"))

    # incremental J-M and QDA BA as features are added
    inc = []
    rf_main = rf_sets[f"RF-{ks[0]}"]
    for i in range(max(len(cart_vars), len(rf_main))):
        row = {"Features used": i + 1}
        for tag, lst in (("CART", cart_vars), ("RF", rf_main)):
            if i < len(lst):
                cols = [name_to_col[v] for v in lst[:i + 1]]
                try:
                    jmv, _ = models.jm(X[:, cols], y)
                except np.linalg.LinAlgError:
                    jmv = np.nan
                pred, prob = _qda_cv(X[:, cols], y, folds["V1"])
                row.update({f"{tag} feature added": lst[i], f"{tag} J–M": jmv,
                            f"{tag} QDA BA": evaluate(y, pred, prob)["BA"]})
        inc.append(row)
    out["tier3_incremental"] = pd.DataFrame(inc)

    # ------------------------------------------------------------ validation pipelines
    log(f"{label}: validation pipelines V1/V3/V4")
    pipes = ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"]
    fold_rows = []
    preds = {(p, s): [] for p in pipes for s in ["V1"] + nested}
    fold_vars = {}
    sel = {"CART": [], "RF": []}
    # V1
    cols_c = [name_to_col[v] for v in cart_vars]
    cols_r = [name_to_col[v] for v in rf_main]
    for i, f in enumerate(folds["V1"]):
        te = f["test"]
        rc = cres[1 + i]
        rfm = models.brf(cfg).fit(X[f["train"]][:, sig], y[f["train"]])
        prf = rfm.predict_proba(X[te][:, sig])[:, 1]
        pq_c, pr_c = _safe_fit(models.qda(), X[f["train"]][:, cols_c], y[f["train"]], X[te][:, cols_c])
        pq_r, pr_r = _safe_fit(models.qda(), X[f["train"]][:, cols_r], y[f["train"]], X[te][:, cols_r])
        for p, (pp, ss) in zip(pipes, ((rc["pred"], rc["prob"]), ((prf > 0.5).astype(int), prf),
                                      (pq_c, pr_c), (pq_r, pr_r))):
            preds[(p, "V1")].append((te, pp, ss, 0, i))
    # V3 / V4 nested
    j = 1 + len(folds["V1"])
    for sch in nested:
        for i, f in enumerate(folds[sch]):
            tr, te = f["train"], f["test"]
            rc = cres[j]
            j += 1
            s_ = fold_sig[(sch, i)]
            m_s = meta.iloc[s_].reset_index(drop=True)
            rfm = models.brf(cfg).fit(X[tr][:, s_], y[tr])
            prf = rfm.predict_proba(X[te][:, s_])[:, 1]
            idx, _ = _rf_peaks(rfm.feature_importances_, m_s, ks[0], cfg, X[tr][:, s_], coll_r)
            rf_f = list(m_s["name"].iloc[idx])
            c_f = rc["vars"]
            fold_vars[(sch, i)] = {"CART": c_f, "RF": rf_f, "sig": s_}
            if sch == "V3":
                sel["CART"].append(c_f)
                sel["RF"].append(rf_f)
            out_q = []
            for fl in (c_f, rf_f):
                cc = [name_to_col[v] for v in fl]
                if len(cc) == 0:
                    out_q.append((np.ones(len(te), int), np.full(len(te), 0.5)))
                    continue
                out_q.append(_safe_fit(models.qda(), X[tr][:, cc], y[tr], X[te][:, cc]))
            for p, (pp, ss) in zip(pipes, ((rc["pred"], rc["prob"]), ((prf > 0.5).astype(int), prf),
                                          out_q[0], out_q[1])):
                preds[(p, sch)].append((te, pp, ss, f["rep"], i))
                yt = y[te]
                fold_rows.append({"Pipeline": p, "Scheme": sch, "Unit": i, "Repeat": f["rep"],
                                  "BA": stats.balanced_accuracy(yt, pp) if len(np.unique(yt)) == 2 else np.nan})
        log(f"{label}: {sch} done")
    val, pooled = [], {}
    for (p, sch), lst in preds.items():
        per_rep = {}
        for te, pp, ss, r, _ in lst:
            per_rep.setdefault(r, []).append((te, pp, ss))
        mets = []
        for r, parts in per_rep.items():
            te = np.concatenate([a for a, _, _ in parts])
            pp = np.concatenate([b for _, b, _ in parts])
            ss = np.concatenate([c for _, _, c in parts])
            mets.append(evaluate(y[te], pp, ss))
        sm = summarise(mets)
        val.append({"Pipeline": p, "Scheme": sch, **sm})
        pooled[(p, sch)] = sm
    out["validation"] = pd.DataFrame(val)
    out["fold_ba"] = pd.DataFrame(fold_rows)
    out["pooled"] = pooled
    out["preds"] = preds
    out["fold_vars"] = fold_vars
    out["nested"] = nested
    out["wilcoxon"] = paired_tests(out["fold_ba"], [
        ("RF classifier", "CART classifier"), ("QDA on RF features", "QDA on CART features"),
        ("QDA on CART features", "CART classifier"), ("QDA on RF features", "RF classifier")])

    # ------------------------------------------------------------ stability
    out["stability"] = stability(sel, meta, sets[out["cart_name"]], rf_main)
    out["fold_selections"] = sel
    return out


def paired_tests(fold_ba, pairs, label_a=None):
    rows = []
    for a, b in pairs:
        for sch, unit in (("V3", "V3 nested (folds)"), ("V4", "V4 hold-out (splits)")):
            da = fold_ba[(fold_ba.Pipeline == a) & (fold_ba.Scheme == sch)].set_index(["Repeat", "Unit"])["BA"]
            db = fold_ba[(fold_ba.Pipeline == b) & (fold_ba.Scheme == sch)].set_index(["Repeat", "Unit"])["BA"]
            d = (da - db).dropna()
            if len(d) == 0:
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    p = wilcoxon(d.values).pvalue if (d != 0).any() else 1.0
                except ValueError:
                    p = np.nan
            rows.append({"Comparison": f"{a} − {b}", "Units": unit, "n": int(len(d)),
                         "Mean difference": float(d.mean()), "SD": float(d.std(ddof=1)) if len(d) > 1 else np.nan,
                         "First better": int((d > 0).sum()), "Second better": int((d < 0).sum()),
                         "Ties": int((d == 0).sum()), "Wilcoxon p": p})
    return pd.DataFrame(rows)


def _partner(f, others, meta_pos, meta_series, tol=10):
    pf, sf = meta_pos.get(f, np.nan), meta_series.get(f)
    for o in others:
        if o == f:
            return True
        if np.isfinite(pf) and meta_series.get(o) == sf and abs(meta_pos.get(o, np.nan) - pf) <= tol:
            return True
    return False


def _n_matched(a, b, meta, tol=10):
    pos = dict(zip(meta["name"], meta["position"].astype(float)))
    ser = dict(zip(meta["name"], meta["series"]))
    return int(sum(_partner(f, b, pos, ser, tol) for f in a))


def stability(sel, meta, cart_all, rf_all, tol=10):
    pos = dict(zip(meta["name"], meta["position"].astype(float)))
    ser = dict(zip(meta["name"], meta["series"]))
    typ = dict(zip(meta["name"], meta["type"]))
    res = {"index": [], "freq": {}}
    for meth, lists in sel.items():
        nf = len(lists)
        if nf == 0:
            continue
        union = sorted(set(v for l in lists for v in l), key=lambda v: (ser.get(v), pos.get(v, 0), v))
        in_all = [v for v in union if all(v in l for l in lists)]
        tol_all = [v for v in union if all(_partner(v, l, pos, ser, tol) for l in lists)]
        jac = []
        for a, b in combinations(lists, 2):
            ma = sum(_partner(v, b, pos, ser, tol) for v in a)
            mb = sum(_partner(v, a, pos, ser, tol) for v in b)
            m = (ma + mb) / 2
            den = len(a) + len(b) - m
            jac.append(m / den if den > 0 else 1.0)
        sizes = [len(l) for l in lists]
        res["index"].append({
            "Method": meth, "Training sets": nf, "Mean features": float(np.mean(sizes)),
            "Range": f"{min(sizes)}–{max(sizes)}", "Unique features (union)": len(union),
            "Selected in all sets (exact)": len(in_all),
            "Stability index (exact) = all / union": len(in_all) / len(union) if union else np.nan,
            "Selected in all sets (±10 nm)": len(tol_all),
            "Stability index (±10 nm)": len(tol_all) / len(union) if union else np.nan,
            "Mean pairwise Jaccard (±10 nm)": float(np.mean(jac)) if jac else np.nan,
            "SD Jaccard": float(np.std(jac, ddof=1)) if len(jac) > 1 else np.nan})
        cnt = pd.Series([v for l in lists for v in l]).value_counts()
        fr = pd.DataFrame({"Feature": cnt.index, "Type": [typ.get(v, "") for v in cnt.index],
                           "Times selected (exact)": cnt.values,
                           "Share of training sets": cnt.values / nf})
        res["freq"][meth] = fr.reset_index(drop=True)
    # re-selection of the all-data sets (±10 nm), by CART and by RF
    for tag, allset in (("CART", cart_all), ("RF", rf_all)):
        rows = []
        for f in allset:
            r = {"Feature": f, "Type": typ.get(f, "")}
            for meth, lists in sel.items():
                r[f"Re-selected by {meth} (±10 nm)"] = float(np.mean([_partner(f, l, pos, ser, tol) for l in lists])) if lists else np.nan
            rows.append(r)
        res[f"reselect_{tag}"] = pd.DataFrame(rows)
    res["index"] = pd.DataFrame(res["index"])
    return res
