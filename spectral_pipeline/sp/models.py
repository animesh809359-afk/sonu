"""Balanced Random Forest (Tier-2 alternative and classifier), MDI peak
selection, Jeffries-Matusita distance (Tier 3) and QDA (Tier 4)."""
from __future__ import annotations

import numpy as np
from sklearn.discriminant_analysis import (LinearDiscriminantAnalysis,
                                           QuadraticDiscriminantAnalysis)


# ---------------------------------------------------------------- Random Forest
def brf(cfg, n_estimators=None, seed=None):
    from imblearn.ensemble import BalancedRandomForestClassifier
    r = cfg["rf"]
    return BalancedRandomForestClassifier(
        n_estimators=n_estimators or r["n_estimators"], max_features=r["max_features"],
        sampling_strategy=r["sampling_strategy"], replacement=r["replacement"],
        bootstrap=r["bootstrap"], random_state=r["random_state"] if seed is None else seed,
        n_jobs=r["n_jobs"])


def rf_importance(X, y, cfg, n_estimators=None, seed=None):
    m = brf(cfg, n_estimators or cfg["rf"]["n_estimators_importance"], seed)
    m.fit(X, y)
    return m.feature_importances_, m


def select_peaks(importance, series, position, k, min_sep=10.0, X=None, collinear_r=None):
    """Pick importance peaks.

    importance : MDI of every candidate feature
    series     : series id per feature (e.g. 'R', 'D1'; scalar features get their
                 own id so they are always a candidate)
    position   : wavelength per feature (nan for scalar features)
    A spectral feature is a candidate only if it is a local maximum of the
    importance curve of its series; a candidate is accepted if it is at least
    `min_sep` nm from every accepted feature of the same series. Optionally a
    candidate nearly collinear (|r| >= collinear_r) with an accepted feature is
    skipped (numerical guard for J-M/QDA; reported).
    """
    importance = np.asarray(importance, float)
    series = np.asarray(series)
    position = np.asarray(position, float)
    cand = np.zeros(len(importance), bool)
    for s in np.unique(series):
        idx = np.where(series == s)[0]
        if np.isnan(position[idx]).all() or len(idx) == 1:
            cand[idx] = True
            continue
        idx = idx[np.argsort(position[idx])]
        v = importance[idx]
        pos = position[idx]
        for a, i in enumerate(idx):
            left = v[a - 1] if a > 0 and pos[a] - pos[a - 1] <= 1.5 else -np.inf
            right = v[a + 1] if a + 1 < len(idx) and pos[a + 1] - pos[a] <= 1.5 else -np.inf
            cand[i] = v[a] >= left and v[a] >= right and v[a] > 0
    order = [i for i in np.argsort(-importance) if cand[i]]
    chosen, skipped = [], []
    for i in order:
        if len(chosen) >= k:
            break
        ok = all(not (series[j] == series[i] and np.isfinite(position[i])
                      and abs(position[j] - position[i]) < min_sep) for j in chosen)
        if ok and collinear_r is not None and X is not None and chosen:
            r = np.abs([np.corrcoef(X[:, i], X[:, j])[0, 1] for j in chosen])
            if (r >= collinear_r).any():
                skipped.append(int(i))
                ok = False
        if ok:
            chosen.append(int(i))
    return chosen, skipped


# ---------------------------------------------------------------- J-M distance
def bhattacharyya(X, y):
    X0, X1 = X[y == 0], X[y == 1]
    m0, m1 = X0.mean(0), X1.mean(0)
    C0 = np.atleast_2d(np.cov(X0, rowvar=False))
    C1 = np.atleast_2d(np.cov(X1, rowvar=False))
    C = (C0 + C1) / 2
    d = (m0 - m1)[:, None]
    L = np.linalg.cholesky(C)
    z = np.linalg.solve(L, d)
    term1 = float((z.T @ z).item()) / 8
    ld = lambda M: np.linalg.slogdet(M)[1]   # noqa: E731
    term2 = 0.5 * (ld(C) - 0.5 * (ld(C0) + ld(C1)))
    return term1 + term2


def bhattacharyya_explicit(X, y):
    """Independent implementation (explicit inverse and determinants)."""
    X0, X1 = X[y == 0], X[y == 1]
    m0, m1 = X0.mean(0), X1.mean(0)
    C0 = np.atleast_2d(np.cov(X0, rowvar=False))
    C1 = np.atleast_2d(np.cov(X1, rowvar=False))
    C = (C0 + C1) / 2
    d = m0 - m1
    return float(d @ np.linalg.inv(C) @ d / 8 +
                 0.5 * np.log(np.linalg.det(C) / np.sqrt(np.linalg.det(C0) * np.linalg.det(C1))))


def jm(X, y):
    a = bhattacharyya(X, y)
    return 2 * (1 - np.exp(-a)), a


def cond_numbers(X, y):
    return (float(np.linalg.cond(np.atleast_2d(np.cov(X[y == 0], rowvar=False)))),
            float(np.linalg.cond(np.atleast_2d(np.cov(X[y == 1], rowvar=False)))))


# ---------------------------------------------------------------- QDA / LDA
def qda(priors="equal"):
    """QDA (no regularisation). Features are standardised with the training-set
    mean/SD first: QDA is affine-invariant, so predictions are unchanged, but
    scikit-learn's rank check uses an absolute tolerance that misfires on raw
    reflectance and derivative values (variances ~1e-5 to 1e-9)."""
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return make_pipeline(StandardScaler(), QuadraticDiscriminantAnalysis(
        priors=[0.5, 0.5] if priors == "equal" else None, reg_param=0.0, tol=1e-12))


def lda(priors="equal"):
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return make_pipeline(StandardScaler(), LinearDiscriminantAnalysis(
        priors=[0.5, 0.5] if priors == "equal" else None))


def fit_predict(model, Xtr, ytr, Xte):
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(Xtr, ytr)
        prob = model.predict_proba(Xte)[:, 1]
    return (prob > 0.5).astype(int), prob


def qda_manual(Xtr, ytr, Xte):
    """Independent QDA (discriminant functions, equal priors) for cross-checks."""
    sc = []
    for c in (0, 1):
        Xc = Xtr[ytr == c]
        m = Xc.mean(0)
        C = np.cov(Xc, rowvar=False)
        Ci = np.linalg.inv(C)
        d = Xte - m
        sc.append(-0.5 * np.linalg.slogdet(C)[1] - 0.5 * np.einsum("ij,jk,ik->i", d, Ci, d))
    return (sc[1] > sc[0]).astype(int)
