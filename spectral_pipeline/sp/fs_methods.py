"""Feature-selection methods for two-class spectral data (healthy vs diseased).

Every method takes the training data of one validation unit (X, y, plot groups)
and returns a dict with
    rank   : feature indices, most important first (may be shorter than p)
    sets   : optional {k: [indices]} when the method produces its own subset for
             each size k (SFFS, GA); otherwise top-k of `rank` is used
    native : optional subset chosen by the method's own stopping rule
    score  : optional per-feature score (length p)
    info   : dict with method-specific details
Class imbalance is handled in the same spirit as the four-tier analysis:
equal priors / balanced class weights / class-balanced sub-sampling.

Methods
  filter   : Pearson r, ANOVA F, Fisher score (identical rankings for two classes),
             chi-square (quantile bins), mutual information, ReliefF, univariate J-M,
             mRMR (F-test correlation quotient), SPA, MC-UVE, CWT separability scalogram
  wrapper  : SVM-RFE, RF-RFE, CARS, SFFS (QDA balanced accuracy), SFFS (J-M), GA (QDA)
  embedded : Balanced-RF importance (MDI), CART importance, Boruta, PLS-VIP,
             LASSO (L1-logistic), gradient-boosting importance
"""
from __future__ import annotations

import warnings

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import binom
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import StratifiedGroupKFold

INNER_SEED = 7


# =============================================================== helpers
def zfit(X):
    mu = X.mean(0)
    sd = X.std(0)
    sd[sd == 0] = 1.0
    return mu, sd


def zs(X):
    mu, sd = zfit(X)
    return (X - mu) / sd


def ba(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    return 0.5 * ((p[y == 1] == 1).mean() + (p[y == 0] == 0).mean())


def inner_folds(y, groups, k=5, seed=INNER_SEED):
    sgk = StratifiedGroupKFold(k, shuffle=True, random_state=seed)
    return list(sgk.split(np.zeros(len(y)), y, groups))


def balanced_sample(y, frac, rng):
    i0, i1 = np.where(y == 0)[0], np.where(y == 1)[0]
    m = int(round(frac * min(len(i0), len(i1))))
    return np.concatenate([rng.choice(i0, m, replace=False), rng.choice(i1, m, replace=False)])


def qda_fast(Xtr, ytr, Xte, reg=1e-9):
    """QDA with equal priors (discriminant functions); returns predictions or None if singular."""
    sc = []
    for c in (0, 1):
        Xc = Xtr[ytr == c]
        m = Xc.mean(0)
        C = np.atleast_2d(np.cov(Xc, rowvar=False))
        C = C + reg * np.trace(C) / len(C) * np.eye(len(C))
        try:
            L = np.linalg.cholesky(C)
        except np.linalg.LinAlgError:
            return None
        z = np.linalg.solve(L, (Xte - m).T)
        sc.append(-np.log(np.diag(L)).sum() - 0.5 * (z * z).sum(0))
    return (sc[1] > sc[0]).astype(int)


def lda_fast(Xtr, ytr, Xte):
    m0, m1 = Xtr[ytr == 0].mean(0), Xtr[ytr == 1].mean(0)
    C = (np.atleast_2d(np.cov(Xtr[ytr == 0], rowvar=False)) + np.atleast_2d(np.cov(Xtr[ytr == 1], rowvar=False))) / 2
    C = C + 1e-9 * np.trace(C) / len(C) * np.eye(len(C))
    w = np.linalg.solve(C, m1 - m0)
    return ((Xte - (m0 + m1) / 2) @ w > 0).astype(int)


def cv_score(X, y, folds, clf=qda_fast):
    out = []
    for tr, te in folds:
        p = clf(X[tr], y[tr], X[te])
        out.append(0.5 if p is None else ba(y[te], p))
    return float(np.mean(out))


def guard_topk(order, Xz, k, r_max=0.95):
    """Greedy top-k from a ranking, skipping a feature correlated |r| >= r_max with one already
    chosen (redundancy control, cf. the minimum-distance rule of Wei et al. 2021). Xz standardised."""
    chosen = []
    n = len(Xz)
    for j in order:
        if len(chosen) >= k:
            break
        if chosen:
            r = np.abs(Xz[:, chosen].T @ Xz[:, j]) / n
            if (r >= r_max).any():
                continue
        chosen.append(int(j))
    return chosen


def jm_1d(X, y):
    """Univariate Jeffries-Matusita distance (Gaussian classes) for every column."""
    a, b = X[y == 0], X[y == 1]
    m0, m1 = a.mean(0), b.mean(0)
    v0, v1 = a.var(0, ddof=1), b.var(0, ddof=1)
    v0 = np.maximum(v0, 1e-300)
    v1 = np.maximum(v1, 1e-300)
    B = (m0 - m1) ** 2 / (4 * (v0 + v1)) + 0.5 * np.log((v0 + v1) / (2 * np.sqrt(v0 * v1)))
    return 2 * (1 - np.exp(-B))


def jm_multi(X, y):
    X0, X1 = X[y == 0], X[y == 1]
    m0, m1 = X0.mean(0), X1.mean(0)
    C0 = np.atleast_2d(np.cov(X0, rowvar=False))
    C1 = np.atleast_2d(np.cov(X1, rowvar=False))
    C = (C0 + C1) / 2
    try:
        L = np.linalg.cholesky(C)
        z = np.linalg.solve(L, (m0 - m1)[:, None])
        ld = lambda M: np.linalg.slogdet(M)[1]  # noqa: E731
        B = float((z.T @ z).item()) / 8 + 0.5 * (ld(C) - 0.5 * (ld(C0) + ld(C1)))
    except np.linalg.LinAlgError:
        return np.nan
    return 2 * (1 - np.exp(-B))


# =============================================================== filters
def univariate(X, y):
    """Pearson r (point-biserial), ANOVA F, Fisher score, univariate J-M, AUC."""
    n = len(y)
    n0, n1 = (y == 0).sum(), (y == 1).sum()
    Xz = zs(X)
    yz = (y - y.mean()) / y.std()
    r = Xz.T @ yz / n
    m, m0, m1 = X.mean(0), X[y == 0].mean(0), X[y == 1].mean(0)
    v0, v1 = X[y == 0].var(0), X[y == 1].var(0)
    ssb = n0 * (m0 - m) ** 2 + n1 * (m1 - m) ** 2
    ssw = n0 * v0 + n1 * v1
    F = (ssb / 1) / (ssw / (n - 2))
    fisher = ssb / ssw
    return {"r": r, "abs_r": np.abs(r), "F": F, "fisher": fisher, "jm": jm_1d(X, y)}


def chi2_binned(X, y, bins=10):
    """Chi-square statistic of the class x quantile-bin contingency table of every feature."""
    n = len(y)
    ranks = X.argsort(0).argsort(0)
    B = np.minimum((ranks * bins) // n, bins - 1)
    chi = np.zeros(X.shape[1])
    tot = np.array([(B == b).sum(0) for b in range(bins)], float)          # bins x p
    for c in (0, 1):
        pc = (y == c).mean()
        Oc = np.array([(B[y == c] == b).sum(0) for b in range(bins)], float)
        E = tot * pc
        chi += ((Oc - E) ** 2 / np.where(E > 0, E, 1)).sum(0)
    return chi


def mutual_info(X, y, seed=0):
    from sklearn.feature_selection import mutual_info_classif
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return mutual_info_classif(zs(X), y, n_neighbors=3, random_state=seed)


def relieff(X, y, k=10, rng=None, chunk=64):
    """ReliefF (Kononenko 1994) with Manhattan distance on min-max scaled features. Instances:
    all training leaves of the minority class and an equal random number of the majority class;
    the weight is the mean of the two class-wise updates (equal priors)."""
    rng = rng or np.random.default_rng(0)
    lo, hi = X.min(0), X.max(0)
    S = (X - lo) / np.where(hi > lo, hi - lo, 1)
    i0, i1 = np.where(y == 0)[0], np.where(y == 1)[0]
    m = min(len(i0), len(i1))
    W = np.zeros(X.shape[1])
    for c, idx in ((0, i0), (1, i1)):
        R = idx if len(idx) == m else rng.choice(idx, m, replace=False)
        Wc = np.zeros(X.shape[1])
        for s in range(0, len(R), chunk):
            rr = R[s:s + chunk]
            Dm = cdist(S[rr], S, "cityblock")
            Dm[np.arange(len(rr)), rr] = np.inf
            same = (y == c)
            Dh = np.where(same[None, :], Dm, np.inf)
            Dmi = np.where(~same[None, :], Dm, np.inf)
            H = np.argpartition(Dh, k, axis=1)[:, :k]
            M = np.argpartition(Dmi, k, axis=1)[:, :k]
            for a, r_ in enumerate(rr):
                Wc -= np.abs(S[H[a]] - S[r_]).sum(0) / k
                Wc += np.abs(S[M[a]] - S[r_]).sum(0) / k
        W += 0.5 * Wc / len(R)
    return W


def mrmr_fcq(X, y, F, k=30):
    """mRMR, F-test correlation quotient (Ding & Peng 2005): relevance F, redundancy mean |r|."""
    Xz = zs(X)
    n = len(y)
    sel = [int(np.argmax(F))]
    red = np.abs(Xz.T @ Xz[:, sel[0]]) / n
    while len(sel) < k:
        score = F / np.maximum(red / len(sel), 1e-6)
        score[sel] = -np.inf
        j = int(np.argmax(score))
        sel.append(j)
        red += np.abs(Xz.T @ Xz[:, j]) / n
    return sel


def spa_chain(Xz, start, k):
    """Successive projections algorithm (Araujo et al. 2001) from a start column."""
    P = Xz.copy()
    sel = [start]
    for _ in range(k - 1):
        x = P[:, sel[-1]].copy()
        P -= np.outer(x, x @ P) / (x @ x)
        nrm = (P * P).sum(0)
        nrm[sel] = -1
        sel.append(int(np.argmax(nrm)))
    return sel


def spa(X, y, groups, F, k_max=20, n_starts=10):
    """SPA chains from the n_starts most significant features (ANOVA F); chain and length are
    chosen by plot-grouped inner CV of LDA (the MLR validation of the original SPA)."""
    Xz = zs(X)
    folds = inner_folds(y, groups)
    best = (-1, None, None)
    for s in np.argsort(-F)[:n_starts]:
        ch = spa_chain(Xz, int(s), k_max)
        for kk in range(2, k_max + 1):
            sc = cv_score(Xz[:, ch[:kk]], y, folds, lda_fast)
            if sc > best[0]:
                best = (sc, ch, kk)
    return best[1], best[1][:best[2]], {"inner BA": best[0], "start": best[1][0]}


def _pls(X, y, A):
    m = PLSRegression(n_components=A, scale=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m.fit(X, y)
    return m


def _plsda_ba(X, y, folds, A):
    out = []
    for tr, te in folds:
        A_ = min(A, X.shape[1], len(tr) - 1)
        m = _pls(X[tr], y[tr], A_)
        f = m.predict(X[tr]).ravel()
        thr = (f[y[tr] == 0].mean() + f[y[tr] == 1].mean()) / 2
        out.append(ba(y[te], (m.predict(X[te]).ravel() > thr).astype(int)))
    return float(np.mean(out))


def mc_uve(X, y, A=10, n_runs=100, rng=None):
    """Monte-Carlo UVE (Centner et al. 1996; Cai et al. 2008): reliability mean(b)/sd(b) of the
    PLS-DA coefficients over class-balanced sub-samples; artificial noise variables give the cut-off."""
    rng = rng or np.random.default_rng(0)
    Xz = zs(X)
    n, p = Xz.shape
    N = rng.uniform(size=(n, p)) * 1e-10
    XN = np.hstack([Xz, N])
    B = np.zeros((n_runs, 2 * p))
    for i in range(n_runs):
        s = balanced_sample(y, 0.8, rng)
        B[i] = _pls(XN[s], y[s].astype(float), A).coef_.ravel()
    c = B.mean(0) / B.std(0, ddof=1)
    cut = np.abs(c[p:]).max()
    rel = np.abs(c[:p])
    return rel, np.where(rel > cut)[0], {"cutoff |c|": float(cut)}


def cars(X, y, groups, A=10, n_runs=50, rng=None):
    """Competitive adaptive reweighted sampling (Li et al. 2009) with PLS-DA on class-balanced
    Monte-Carlo sub-samples; the subset with the best plot-grouped CV balanced accuracy is kept.
    Ranking: last sampling run survived (descending), then final |b|."""
    rng = rng or np.random.default_rng(0)
    Xz = zs(X)
    p = Xz.shape[1]
    a = (p / 2) ** (1 / (n_runs - 1))
    kk = np.log(p / 2) / (n_runs - 1)
    keep = np.arange(p)
    survived = np.zeros(p, int)
    lastw = np.zeros(p)
    subsets = []
    for i in range(1, n_runs + 1):
        s = balanced_sample(y, 0.8, rng)
        m = _pls(Xz[s][:, keep], y[s].astype(float), min(A, len(keep)))
        w = np.abs(m.coef_.ravel())
        w = w / w.sum()
        lastw[keep] = w
        nk = max(2, int(round(a * np.exp(-kk * i) * p)))
        o = np.argsort(-w)[:nk]
        pick = rng.choice(len(o), nk, replace=True, p=w[o] / w[o].sum())
        keep = np.unique(keep[o[pick]])
        survived[keep] = i
        subsets.append(keep.copy())
    folds = inner_folds(y, groups)
    scores = [(_plsda_ba(Xz[:, S], y, folds, A), S) for S in subsets]
    best = max(range(len(scores)), key=lambda j: (scores[j][0], -len(scores[j][1])))
    order = np.lexsort((-lastw, -survived))
    return order, list(scores[best][1]), {"best run": best + 1, "inner BA": scores[best][0],
                                          "subset sizes": [len(s) for s in subsets]}


def pls_vip(X, y, groups, A_max=15):
    """PLS-DA variable importance in projection (Wold et al. 2001); components by plot-grouped
    inner CV (balanced accuracy); VIP > 1 is the native subset (Chong & Jun 2005)."""
    Xz = zs(X)
    folds = inner_folds(y, groups)
    sc = [_plsda_ba(Xz, y, folds, A) for A in range(1, A_max + 1)]
    A = int(np.argmax(sc)) + 1
    m = _pls(Xz, y.astype(float), A)
    W, T, Q = m.x_weights_, m.x_scores_, m.y_loadings_
    ss = (Q[0] ** 2) * (T ** 2).sum(0)
    Wn = W / np.linalg.norm(W, axis=0)
    vip = np.sqrt(Xz.shape[1] * (Wn ** 2 @ ss) / ss.sum())
    return vip, np.where(vip > 1)[0], {"components": A, "inner BA": sc[A - 1]}


def cwt_mexh(R, wl, scales):
    """Continuous wavelet transform (Mexican hat) of every spectrum at the given dyadic scales."""
    from scipy.signal import fftconvolve
    out = []
    for a in scales:
        t = np.arange(-5 * a, 5 * a + 1) / a
        psi = 2 / (np.sqrt(3) * np.pi ** 0.25) * (1 - t ** 2) * np.exp(-t ** 2 / 2) / np.sqrt(a)
        out.append(fftconvolve(R, psi[None, ::-1], mode="same", axes=1))
    return np.stack(out, 1)       # n x scales x wl


def scalogram_peaks(S, valid):
    """Local maxima of a separability scalogram (scales x wavelengths)."""
    pk = np.zeros_like(S, bool)
    ns, nw = S.shape
    for i in range(ns):
        for j in range(nw):
            if not valid[i, j]:
                continue
            v = S[i, j]
            nb = S[max(0, i - 1):i + 2, max(0, j - 1):j + 2]
            vb = valid[max(0, i - 1):i + 2, max(0, j - 1):j + 2]
            if v >= nb[vb].max():
                pk[i, j] = True
    return pk


# =============================================================== wrappers
def svm_rfe(X, y, C=0.01, frac=0.1, tail=100):
    """SVM-RFE (Guyon et al. 2002): linear SVM with balanced class weights; 10 % of the remaining
    features removed per step down to `tail`, then one at a time."""
    from sklearn.svm import LinearSVC
    Xz = zs(X)
    alive = list(range(Xz.shape[1]))
    elim = []
    while len(alive) > 1:
        m = LinearSVC(C=C, class_weight="balanced", dual=False, max_iter=5000)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m.fit(Xz[:, alive], y)
        w = np.abs(m.coef_.ravel())
        nrem = max(1, int(frac * len(alive))) if len(alive) > tail else 1
        o = np.argsort(w)[:nrem]
        rem = [alive[i] for i in o]
        elim.extend(rem)
        alive = [a for a in alive if a not in set(rem)]
    elim.extend(alive)
    return np.array(elim[::-1])


def rf_rfe(X, y, cfg, frac=0.2, n_trees=150, seed=0):
    """RF-RFE: Balanced-RF MDI importance, 20 % removed per step down to 100, then 5 at a time
    down to 30, then one at a time."""
    from .models import brf
    alive = np.arange(X.shape[1])
    elim = []
    while len(alive) > 1:
        m = brf(cfg, n_trees, seed)
        m.set_params(n_jobs=1)
        m.fit(X[:, alive], y)
        w = m.feature_importances_
        nrem = int(frac * len(alive)) if len(alive) > 100 else (5 if len(alive) > 30 else 1)
        nrem = max(1, min(nrem, len(alive) - 1))
        o = np.argsort(w)[:nrem]
        elim.extend(alive[o].tolist())
        alive = np.delete(alive, o)
    elim.extend(alive.tolist())
    return np.array(elim[::-1])


class _Crit:
    """Memoised subset criterion."""

    def __init__(self, f):
        self.f, self.memo, self.calls = f, {}, 0

    def __call__(self, S):
        key = frozenset(S)
        if key not in self.memo:
            self.calls += 1
            self.memo[key] = self.f(sorted(S))
        return self.memo[key]


def sffs(cands, crit, k_max=20):
    """Sequential floating forward selection (Pudil et al. 1994). Returns the best set per size."""
    S, best = [], {}
    while len(S) < k_max:
        rest = [c for c in cands if c not in S]
        if not rest:
            break
        j = max(rest, key=lambda c: crit(S + [c]))
        S = S + [j]
        v = crit(S)
        if len(S) not in best or v > best[len(S)][0]:
            best[len(S)] = (v, list(S))
        while len(S) > 2:
            worst = max(S, key=lambda s: crit([t for t in S if t != s]))
            S2 = [t for t in S if t != worst]
            v2 = crit(S2)
            if v2 > best[len(S2)][0] + 1e-12:
                S = S2
                best[len(S2)] = (v2, list(S2))
            else:
                break
    return {k: v[1] for k, v in best.items()}, {k: v[0] for k, v in best.items()}


def ga_select(cands, crit, rng, pop=50, gens=40, p_cross=0.8, pen=0.002, k_max=25):
    """Genetic algorithm (Leardi et al. 1992): binary chromosomes over the candidate pool, fitness =
    criterion - pen * size, tournament selection, uniform crossover, bit-flip mutation, elitism."""
    m = len(cands)
    P = np.zeros((pop, m), bool)
    for i in range(pop):
        P[i, rng.choice(m, int(rng.integers(3, 13)), replace=False)] = True

    def fit(ch):
        s = [cands[j] for j in np.where(ch)[0]]
        if not 2 <= len(s) <= k_max:
            return 0.0
        return crit(s) - pen * len(s)
    hist = []
    for g in range(gens):
        f = np.array([fit(ch) for ch in P])
        hist.append(float(f.max()))
        elite = P[np.argsort(-f)[:2]].copy()
        new = [elite[0], elite[1]]
        while len(new) < pop:
            a, b = [P[max(rng.choice(pop, 3, replace=False), key=lambda i: f[i])] for _ in range(2)]
            child = np.where(rng.random(m) < 0.5, a, b) if rng.random() < p_cross else a.copy()
            flip = rng.random(m) < 1.0 / m
            child = child ^ flip
            new.append(child)
        P = np.array(new)
    f = np.array([fit(ch) for ch in P])
    bestc = P[int(np.argmax(f))]
    freq = P.mean(0)
    order = [cands[j] for j in np.lexsort((-np.array([crit([c]) for c in cands]), -freq))]
    return order, [cands[j] for j in np.where(bestc)[0]], {"best fitness": float(f.max()), "history": hist}


# =============================================================== embedded
def rf_mdi(X, y, cfg, n_trees=500, seed=0):
    from .models import brf
    m = brf(cfg, n_trees, seed)
    m.set_params(n_jobs=1)
    m.fit(X, y)
    return m.feature_importances_


def cart_importance(X, y, groups):
    """CART (Gini, balanced class weights = equal priors, minsplit 20 / minbucket 7 as rpart),
    pruned by cost complexity chosen with plot-grouped inner CV; Gini importance."""
    from sklearn.tree import DecisionTreeClassifier
    base = dict(class_weight="balanced", min_samples_split=20, min_samples_leaf=7, random_state=0)
    path = DecisionTreeClassifier(**base).cost_complexity_pruning_path(X, y)
    alphas = np.unique(path.ccp_alphas)
    alphas = alphas[np.linspace(0, len(alphas) - 1, min(25, len(alphas))).astype(int)]
    folds = inner_folds(y, groups)
    sc = []
    for a in alphas:
        v = []
        for tr, te in folds:
            t = DecisionTreeClassifier(**base, ccp_alpha=a).fit(X[tr], y[tr])
            v.append(ba(y[te], t.predict(X[te])))
        sc.append(np.mean(v))
    a = alphas[int(np.argmax(sc))]
    t = DecisionTreeClassifier(**base, ccp_alpha=a).fit(X, y)
    imp = t.feature_importances_
    return imp, {"ccp_alpha": float(a), "leaves": int(t.get_n_leaves()), "inner BA": float(max(sc))}


def boruta(X, y, cfg, max_runs=60, n_trees=200, alpha=0.01, rng=None):
    """Boruta (Kursa & Rudnicki 2010) with Balanced-RF MDI importance: shuffled shadow copies of the
    undecided features, a hit when a feature beats the best shadow, two-sided binomial tests with
    Bonferroni correction; rejected features are dropped from later runs."""
    from .models import brf
    rng = rng or np.random.default_rng(0)
    p = X.shape[1]
    status = np.zeros(p, int)          # 0 tentative, 1 confirmed, -1 rejected
    hits = np.zeros(p)
    runs = np.zeros(p)
    imp_sum = np.zeros(p)
    rej_run = np.zeros(p)
    for it in range(1, max_runs + 1):
        act = np.where(status >= 0)[0]
        und = np.where(status == 0)[0]
        if len(und) == 0:
            break
        Sh = X[:, act].copy()
        for j in range(Sh.shape[1]):
            Sh[:, j] = Sh[rng.permutation(len(y)), j]
        m = brf(cfg, n_trees, int(rng.integers(1e9)))
        m.set_params(n_jobs=1)
        m.fit(np.hstack([X[:, act], Sh]), y)
        imp = m.feature_importances_
        real, shadow = imp[:len(act)], imp[len(act):]
        smax = shadow.max()
        hits[act] += real > smax
        runs[act] += 1
        imp_sum[act] += real
        n_und = len(und)
        pu = binom.sf(hits[und] - 1, runs[und], 0.5)
        pl = binom.cdf(hits[und], runs[und], 0.5)
        status[und[pu < alpha / n_und]] = 1
        newly = und[pl < alpha / n_und]
        status[newly] = -1
        rej_run[newly] = it
    mean_imp = imp_sum / np.maximum(runs, 1)
    order = np.lexsort((-mean_imp, -rej_run, -(status + 1)))
    return order, np.where(status == 1)[0], {"confirmed": int((status == 1).sum()), "tentative": int((status == 0).sum()),
                                             "rejected": int((status == -1).sum()), "runs": it, "mean_imp": mean_imp}


def lasso_path(X, y, groups, Cs=None):
    """L1-penalised logistic regression (Tibshirani 1996) with balanced class weights; C chosen by
    plot-grouped inner CV; ranking = order of entry along the regularisation path."""
    from sklearn.linear_model import LogisticRegression
    Cs = np.logspace(-3, -0.5, 9) if Cs is None else Cs
    Xz = zs(X)

    def model(C):
        return LogisticRegression(l1_ratio=1.0, solver="liblinear", C=C, class_weight="balanced", max_iter=400) \
            if _new_lr() else LogisticRegression(penalty="l1", solver="liblinear", C=C, class_weight="balanced", max_iter=400)
    entry = np.full(Xz.shape[1], np.inf)
    coefs = {}
    for i, C in enumerate(Cs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = model(C).fit(Xz, y)
        w = m.coef_.ravel()
        coefs[C] = w
        newly = (w != 0) & ~np.isfinite(entry)
        entry[newly] = i
    folds = inner_folds(y, groups, 3)
    sc = []
    for C in Cs:
        v = []
        for tr, te in folds:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                v.append(ba(y[te], model(C).fit(Xz[tr], y[tr]).predict(Xz[te])))
        sc.append(np.mean(v))
    Cb = Cs[int(np.argmax(sc))]
    last = np.abs(coefs[Cs[-1]])
    order = np.lexsort((-last, entry))
    order = order[np.isfinite(entry[order])]
    return order, np.where(coefs[Cb] != 0)[0], {"C": float(Cb), "inner BA": float(max(sc)), "nonzero at C": int((coefs[Cb] != 0).sum())}


def _new_lr():
    import sklearn
    v = tuple(int(x) for x in sklearn.__version__.split(".")[:2])
    return v >= (1, 8)


def gbm_importance(X, y, seed=0):
    """Gradient-boosted trees (Friedman 2001; the XGBoost family) with balanced sample weights;
    split-gain importance."""
    from sklearn.ensemble import GradientBoostingClassifier
    w = np.where(y == 1, 0.5 / (y == 1).mean(), 0.5 / (y == 0).mean())
    m = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.1, subsample=0.8,
                                   max_features="sqrt", random_state=seed)
    m.fit(X, y, sample_weight=w)
    return m.feature_importances_
