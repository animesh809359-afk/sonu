"""Feature statistics used by Tier 1 and K1-K4: Welch t + BH-FDR, Hedges g,
direction-free AUC, Youden threshold classifier, mixed model and ICC."""
from __future__ import annotations

import warnings

import numpy as np
from scipy import stats as st


def welch(X, y):
    """Column-wise Welch t-test, positive t = class 1 (diseased) > class 0."""
    X0, X1 = X[y == 0], X[y == 1]
    n0, n1 = len(X0), len(X1)
    m0, m1 = X0.mean(0), X1.mean(0)
    v0, v1 = X0.var(0, ddof=1), X1.var(0, ddof=1)
    a, b = v0 / n0, v1 / n1
    se = np.sqrt(a + b)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (m1 - m0) / se
        df = (a + b) ** 2 / (a ** 2 / (n0 - 1) + b ** 2 / (n1 - 1))
    p = 2 * st.t.sf(np.abs(t), df)
    p = np.where(np.isfinite(p), p, 1.0)
    sp = np.sqrt(((n0 - 1) * v0 + (n1 - 1) * v1) / (n0 + n1 - 2))
    with np.errstate(divide="ignore", invalid="ignore"):
        g = (m1 - m0) / sp * (1 - 3 / (4 * (n0 + n1) - 9))
    return {"mean0": m0, "mean1": m1, "sd0": np.sqrt(v0), "sd1": np.sqrt(v1),
            "t": t, "df": df, "p": p, "g": g, "n0": n0, "n1": n1}


def bh(p):
    p = np.asarray(p, float)
    n = len(p)
    o = np.argsort(p)
    q = p[o] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(n)
    out[o] = np.minimum(q, 1.0)
    return out


def auc(X, y):
    """AUC of each column for 'class 1 has larger values' (Mann-Whitney)."""
    X = np.asarray(X, float)
    if X.ndim == 1:
        X = X[:, None]
    r = st.rankdata(X, axis=0)
    n1 = (y == 1).sum()
    n0 = len(y) - n1
    u = r[y == 1].sum(0) - n1 * (n1 + 1) / 2
    return u / (n0 * n1)


def auc_free(X, y):
    a = auc(X, y)
    return np.maximum(a, 1 - a), np.where(a >= 0.5, 1, -1)


def balanced_accuracy(y, pred):
    y, pred = np.asarray(y), np.asarray(pred)
    tpr = (pred[y == 1] == 1).mean() if (y == 1).any() else np.nan
    tnr = (pred[y == 0] == 0).mean() if (y == 0).any() else np.nan
    return 0.5 * (tpr + tnr)


def youden_fit(X, y, direction=None):
    """Best threshold per column (Youden J). Returns thr, direction (+1 means
    'class 1 if x > thr')."""
    X = np.asarray(X, float)
    if X.ndim == 1:
        X = X[:, None]
    if direction is None:
        _, direction = auc_free(X, y)
    Xs = X * direction
    n, p = Xs.shape
    n1 = (y == 1).sum()
    n0 = n - n1
    o = np.argsort(-Xs, axis=0, kind="mergesort")       # descending
    xs = np.take_along_axis(Xs, o, 0)
    ys = y[o]
    tp = np.cumsum(ys, 0)
    fp = np.cumsum(1 - ys, 0)
    J = tp / n1 - fp / n0                                # first k+1 called positive
    valid = np.ones_like(J, bool)
    valid[:-1] = xs[:-1] > xs[1:]                        # cut only between distinct values
    valid[-1] = False
    J = np.where(valid, J, -np.inf)
    k = J.argmax(0)
    cols = np.arange(p)
    thr_s = 0.5 * (xs[k, cols] + xs[np.minimum(k + 1, n - 1), cols])
    return thr_s * direction, direction


def youden_predict(X, thr, direction):
    X = np.asarray(X, float)
    if X.ndim == 1:
        X = X[:, None]
    return ((X * direction) > (thr * direction)).astype(int)


def _mixed_one(x, y, g):
    import pandas as pd
    import statsmodels.formula.api as smf
    sd = x.std()
    if not np.isfinite(sd) or sd == 0:
        return np.nan, np.nan, np.nan, 0
    d = pd.DataFrame({"v": (x - x.mean()) / sd, "D": y, "g": g})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # statsmodels' default (L-)BFGS optimiser often collapses to a zero plot
        # variance with NaN standard errors; Powell / Nelder-Mead do not (checked
        # against R nlme::lme in the cross-checks)
        for meth in ("powell", "nm"):
            try:
                r = smf.mixedlm("v ~ D", d, groups=d["g"]).fit(reml=True, method=meth)
            except Exception:  # noqa: BLE001
                continue
            p = float(r.pvalues["D"])
            if np.isfinite(p):
                vg = max(float(r.cov_re.iloc[0, 0]), 0.0)
                icc = vg / (vg + r.scale) if vg + r.scale > 0 else np.nan
                return float(r.params["D"]) * sd, p, icc, int(vg < 1e-8)
        # boundary fit (plot variance estimated at 0): REML reduces to OLS
        o = smf.ols("v ~ D", d).fit()
        return float(o.params["D"]) * sd, float(o.pvalues["D"]), 0.0, 1


def mixed_models(X, y, groups, n_jobs=4):
    """Random-intercept model per feature (R nlme::lme, REML; t-test of the
    disease effect with the between-plot degrees of freedom). Columns are split
    over `n_jobs` parallel R processes."""
    import json
    import subprocess
    import tempfile
    from pathlib import Path
    X = np.asarray(X, float)
    p = X.shape[1]
    runner = Path(__file__).with_name("lme_runner.R")
    chunks = np.array_split(np.arange(p), max(1, min(n_jobs, p)))
    with tempfile.TemporaryDirectory(prefix="lme_") as td:
        procs = []
        for k, idx in enumerate(chunks):
            jd = Path(td) / str(k)
            jd.mkdir()
            X[:, idx].T.astype("<f8").tofile(jd / "X.bin")
            (jd / "meta.json").write_text(json.dumps({"n": int(X.shape[0]), "p": int(len(idx)),
                                                      "y": [int(v) for v in y], "g": [str(v) for v in groups]}))
            procs.append((idx, jd, subprocess.Popen(["Rscript", str(runner), str(jd)],
                                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)))
        res = np.full((p, 4), np.nan)
        for idx, jd, pr in procs:
            _, err = pr.communicate()
            if pr.returncode != 0:
                raise RuntimeError("nlme failed: " + err.decode()[-2000:])
            # nlme returns NA for a feature whose model does not converge -> NaN (not significant, counted in the checks)
            res[idx] = np.atleast_2d(np.genfromtxt(jd / "out.txt", missing_values="NA", filling_values=np.nan))
    eff, pv, icc, df = res.T
    q = np.full_like(pv, np.nan)
    ok = np.isfinite(pv)
    q[ok] = bh(pv[ok])
    return {"effect": eff, "p": pv, "q": q, "icc": icc, "df": df, "boundary": (icc < 1e-6).astype(int)}


def mixed_models_statsmodels(X, y, groups, n_jobs=4):
    """statsmodels MixedLM (Wald z) - used only as a cross-check of nlme."""
    from joblib import Parallel, delayed
    X = np.asarray(X, float)
    res = Parallel(n_jobs=n_jobs, batch_size=8)(
        delayed(_mixed_one)(X[:, j], y, groups) for j in range(X.shape[1]))
    eff, p, icc, bnd = (np.array(v, float) for v in zip(*res))
    return {"effect": eff, "p": p, "icc": icc}


def feature_table(X, y, alpha=0.05):
    w = welch(X, y)
    q = bh(w["p"])
    a, d = auc_free(X, y)
    return {**w, "q": q, "sig": q < alpha, "auc": a, "dir": d}
