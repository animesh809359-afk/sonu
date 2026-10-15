"""Classifiers, inner-CV tuning and feature-selection procedures (all fitted on training plots only)."""
import numpy as np
import pandas as pd
import itertools
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.cross_decomposition import PLSRegression
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.kernel_ridge import KernelRidge
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import balanced_accuracy_score
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')


def balance_idx(y, rng):
    """Random oversampling of the minority class (used for learners without class weights)."""
    i0, i1 = np.where(y == 0)[0], np.where(y == 1)[0]
    small, big = (i0, i1) if len(i0) < len(i1) else (i1, i0)
    extra = rng.choice(small, len(big) - len(small), replace=True)
    return np.r_[big, small, extra]


def class_weights(y):
    w = np.ones(len(y))
    for c in (0, 1):
        w[y == c] = len(y) / (2 * (y == c).sum())
    return w


class ELM:
    """Extreme learning machine (Huang et al., 2006): random tanh hidden layer + weighted ridge read-out."""
    def __init__(self, n_hidden=200, alpha=1.0, seed=0):
        self.n_hidden, self.alpha, self.seed = n_hidden, alpha, seed

    def fit(self, X, y):
        rng = np.random.default_rng(self.seed)
        self.W = rng.normal(0, 1 / np.sqrt(X.shape[1]), (X.shape[1], self.n_hidden)); self.b = rng.normal(0, 1, self.n_hidden)
        H = np.tanh(X @ self.W + self.b); t = 2 * y - 1.0; w = class_weights(y)
        Hw = H * w[:, None]
        self.beta = np.linalg.solve(H.T @ Hw + self.alpha * np.eye(self.n_hidden), Hw.T @ t)
        return self

    def decision_function(self, X):
        return np.tanh(X @ self.W + self.b) @ self.beta


class LSSVM:
    """LS-SVM classifier in its kernel-ridge form (Suykens & Vandewalle, 1999): +/-1 targets, RBF kernel, class weights."""
    def __init__(self, gamma=0.01, alpha=0.1):
        self.gamma, self.alpha = gamma, alpha

    def fit(self, X, y):
        self.m = KernelRidge(alpha=self.alpha, kernel='rbf', gamma=self.gamma).fit(X, 2 * y - 1.0, sample_weight=class_weights(y))
        return self

    def decision_function(self, X):
        return self.m.predict(X)


class PLSDA:
    def __init__(self, n_components=2):
        self.n_components = n_components

    def fit(self, X, y):
        self.m = PLSRegression(min(self.n_components, X.shape[1]), scale=False).fit(X, 2 * y - 1.0)
        return self

    def decision_function(self, X):
        return self.m.predict(X).ravel()


CLF_NAMES = ['LDA', 'PLS-DA', 'LR', 'kNN', 'SVM', 'LS-SVM', 'RF', 'XGBoost', 'ELM', 'MLP']
OVERSAMPLE = {'PLS-DA', 'kNN', 'MLP'}


def make(name, p, n_feat, seed=0):
    g = lambda f: f / n_feat  # gamma relative to feature count (scaled data -> 'scale' = 1/n_feat)
    if name == 'LDA':
        return LinearDiscriminantAnalysis(solver='lsqr', shrinkage=p['shrink'], priors=[0.5, 0.5])
    if name == 'PLS-DA':
        return PLSDA(p['nc'])
    if name == 'LR':
        return LogisticRegression(C=p['C'], class_weight='balanced', max_iter=3000)
    if name == 'kNN':
        return KNeighborsClassifier(n_neighbors=p['k'], weights='distance')
    if name == 'SVM':
        return SVC(C=p['C'], gamma=g(p['g']), class_weight='balanced')
    if name == 'LS-SVM':
        return LSSVM(gamma=g(p['g']), alpha=p['a'])
    if name == 'RF':
        return RandomForestClassifier(n_estimators=200, max_features=p['mf'], min_samples_leaf=p['leaf'],
                                      class_weight='balanced_subsample', n_jobs=1, random_state=seed)
    if name == 'XGBoost':
        return XGBClassifier(n_estimators=300, max_depth=p['d'], learning_rate=p['lr'], subsample=0.8,
                             colsample_bytree=0.8, n_jobs=1, random_state=seed, verbosity=0, tree_method='hist')
    if name == 'ELM':
        return ELM(p['h'], p['a'], seed)
    if name == 'MLP':
        return MLPClassifier(hidden_layer_sizes=p['hl'], alpha=p['a'], max_iter=600, early_stopping=True, random_state=seed)


def grid(name, n_feat):
    G = {'LDA': dict(shrink=[None, 'auto']) if n_feat <= 30 else dict(shrink=['auto']),
         'PLS-DA': dict(nc=[k for k in [1, 2, 3, 5, 8, 12, 16] if k <= max(1, n_feat)]),
         'LR': dict(C=[0.01, 0.1, 1, 10, 100]),
         'kNN': dict(k=[5, 15, 35]),
         'SVM': dict(C=[1, 10, 100], g=[0.1, 1, 10]),
         'LS-SVM': dict(g=[0.3, 3], a=[0.01, 0.1]),
         'RF': dict(mf=['sqrt'], leaf=[1, 5]),
         'XGBoost': dict(d=[2, 4], lr=[0.05, 0.15]),
         'ELM': dict(h=[100, 400], a=[0.1, 10]),
         'MLP': dict(hl=[(64,), (64, 32)], a=[1e-3, 1e-1])}[name]
    keys = list(G)
    return [dict(zip(keys, v)) for v in itertools.product(*[G[k] for k in keys])]


def fit_predict(name, p, Xtr, ytr, Xte, seed=0):
    sc = StandardScaler().fit(Xtr)
    A, B = sc.transform(Xtr), sc.transform(Xte)
    rng = np.random.default_rng(seed)
    if name in OVERSAMPLE:
        idx = balance_idx(ytr, rng); A, yy = A[idx], ytr[idx]
    else:
        yy = ytr
    m = make(name, p, A.shape[1], seed)
    if name == 'XGBoost':
        m.set_params(scale_pos_weight=(yy == 0).sum() / (yy == 1).sum())
    m.fit(A, yy)
    if name in ('LR', 'RF', 'XGBoost', 'kNN', 'MLP'):
        s = m.predict_proba(B)[:, 1] - 0.5
    elif name == 'LDA':
        s = m.decision_function(B)
    else:
        s = m.decision_function(B)
    return s, (s > 0).astype(int)


def tune(name, Xtr, ytr, inner, seed=0):
    """inner: list of (train_idx, val_idx) on the training set, grouped by plot."""
    best, best_s = None, -1
    for p in grid(name, Xtr.shape[1]):
        sc = []
        for a, b in inner:
            _, pr = fit_predict(name, p, Xtr[a], ytr[a], Xtr[b], seed)
            sc.append(balanced_accuracy_score(ytr[b], pr))
        if np.mean(sc) > best_s:
            best, best_s = p, np.mean(sc)
    return best, best_s


# ----------------------------------------------------------------------------- feature selection
def relieff(X, y, k=10, m=250, seed=0):
    """ReliefF for two classes (Robnik-Sikonja & Kononenko, 2003), Manhattan distance on min-max scaled data."""
    rng = np.random.default_rng(seed)
    mn, mx = X.min(0), X.max(0); rngx = np.where(mx - mn > 0, mx - mn, 1)
    Z = (X - mn) / rngx
    samp = rng.choice(len(Z), min(m, len(Z)), replace=False)
    W = np.zeros(Z.shape[1])
    for s0 in range(0, len(samp), 50):
        S = samp[s0:s0 + 50]
        D = cdist(Z[S], Z, 'cityblock')
        for r, i in enumerate(S):
            D[r, i] = np.inf
            same, other = np.where(y == y[i])[0], np.where(y != y[i])[0]
            h = same[np.argsort(D[r, same])[:k]]; mm = other[np.argsort(D[r, other])[:k]]
            W += np.abs(Z[mm] - Z[i]).mean(0) - np.abs(Z[h] - Z[i]).mean(0)
    return W / len(samp)


def vif_filter(X, thr=10.0):
    keep = list(range(X.shape[1]))
    while len(keep) > 1:
        Z = (X[:, keep] - X[:, keep].mean(0)) / X[:, keep].std(0)
        C = np.corrcoef(Z.T)
        try:
            vif = np.diag(np.linalg.pinv(C))
        except Exception:
            break
        j = int(np.argmax(vif))
        if vif[j] <= thr:
            break
        keep.pop(j)
    return keep


def lda_cv(X, y, inner, cols):
    sc = []
    for a, b in inner:
        m = LinearDiscriminantAnalysis(priors=[0.5, 0.5]).fit(X[a][:, cols], y[a])
        sc.append(balanced_accuracy_score(y[b], m.predict(X[b][:, cols])))
    return np.mean(sc)


def sffs(X, y, inner, k_max=10, tol=0.002):
    """Sequential floating forward selection (Pudil et al., 1994) wrapped around LDA (Tian et al., 2021)."""
    sel, best_by_k = [], {}
    rest = list(range(X.shape[1]))
    while len(sel) < k_max and rest:
        sc = [lda_cv(X, y, inner, sel + [f]) for f in rest]
        f = rest[int(np.argmax(sc))]; sel.append(f); rest.remove(f)
        cur = max(sc)
        if len(sel) not in best_by_k or cur > best_by_k[len(sel)][0]:
            best_by_k[len(sel)] = (cur, list(sel))
        # floating backward steps
        while len(sel) > 2:
            sc_b = [lda_cv(X, y, inner, [s for s in sel if s != f2]) for f2 in sel]
            j = int(np.argmax(sc_b))
            if sc_b[j] > best_by_k[len(sel) - 1][0] + 1e-9:
                rest.append(sel.pop(j)); best_by_k[len(sel)] = (sc_b[j], list(sel))
            else:
                break
    best = max(v[0] for v in best_by_k.values())
    for k in sorted(best_by_k):  # most parsimonious subset within tol of the best
        if best_by_k[k][0] >= best - tol:
            return best_by_k[k][1], best_by_k[k][0]


def robust_select(F, y, dates, inner, top_frac=0.10, min_dates=3, max_pool=40, r_max=0.98, seed=0, k_max=10):
    """Tian et al. (2021) / Lv et al. (2023) style: ReliefF ranking within each date, keep features in the
    top 10 % on >= 3 of 4 dates (temporal stability), redundancy filter, VIF < 10, then SFFS-LDA."""
    nf = F.shape[1]
    ntop = max(10, int(round(top_frac * nf)))
    W_all, hits = np.zeros(nf), np.zeros(nf)
    ud = np.unique(dates)
    for d in ud:
        m = dates == d
        w = relieff(F[m], y[m], seed=seed)
        W_all += w
        hits[np.argsort(-w)[:ntop]] += 1
    need = min(min_dates, len(ud))
    cand = np.where(hits >= need)[0]
    if len(cand) < 5:
        cand = np.argsort(-W_all)[:max(5, ntop)]
    cand = cand[np.argsort(-W_all[cand])]
    Z = (F - F.mean(0)) / np.where(F.std(0) > 0, F.std(0), 1)
    pool = []
    for c in cand:
        if all(abs(np.corrcoef(Z[:, c], Z[:, p])[0, 1]) < r_max for p in pool):
            pool.append(c)
        if len(pool) >= max_pool:
            break
    keep = vif_filter(Z[:, pool])
    pool = [pool[i] for i in keep]
    sel, crit = sffs(Z[:, pool], y, inner, k_max=k_max)
    return [pool[i] for i in sel], dict(n_stable=len(cand), n_pool=len(pool), crit=crit)


def spa(X, y, inner, n_max=15):
    """Successive projections algorithm (Araujo et al., 2001; Zhu et al., 2017); chain length and start band
    chosen by inner-CV RMSE of an MLR on the class codes."""
    Xc = X - X.mean(0)
    J = X.shape[1]
    best = (np.inf, None)
    for k0 in range(J):
        chain = [k0]
        P = Xc.copy()
        for _ in range(n_max - 1):
            xk = P[:, chain[-1]][:, None]
            P = P - xk @ (xk.T @ P) / (xk.T @ xk)
            norms = np.linalg.norm(P, axis=0); norms[chain] = -1
            chain.append(int(np.argmax(norms)))
        for n in range(1, n_max + 1):
            cols = chain[:n]; err = []
            for a, b in inner:
                A = np.c_[np.ones(len(a)), X[a][:, cols]]
                beta, *_ = np.linalg.lstsq(A, y[a], rcond=None)
                err.append(np.mean((np.c_[np.ones(len(b)), X[b][:, cols]] @ beta - y[b]) ** 2))
            e = np.sqrt(np.mean(err))
            if e < best[0] - 1e-6:
                best = (e, cols)
    return best[1], best[0]


def ga_pls(X, y, inner, pop=30, gens=25, p_init=0.08, seed=0):
    """Genetic-algorithm band selection with a PLS-DA fitness (Leardi & Lupianez Gonzalez, 1998; Mandal et al., 2023)."""
    rng = np.random.default_rng(seed)
    J = X.shape[1]
    Z = (X - X.mean(0)) / X.std(0)
    cache = {}
    def fit(ch):
        key = ch.tobytes()
        if key in cache:
            return cache[key]
        cols = np.where(ch)[0]
        if len(cols) == 0:
            return -1
        sc = []
        for a, b in inner:
            m = PLSRegression(min(5, len(cols)), scale=False).fit(Z[a][:, cols], 2 * y[a] - 1.0)
            sc.append(balanced_accuracy_score(y[b], (m.predict(Z[b][:, cols]).ravel() > 0).astype(int)))
        v = np.mean(sc) - 0.001 * len(cols)
        cache[key] = v
        return v
    P = rng.random((pop, J)) < p_init
    for _ in range(gens):
        fit_v = np.array([fit(c) for c in P])
        order = np.argsort(-fit_v)
        new = [P[order[0]].copy(), P[order[1]].copy()]
        while len(new) < pop:
            a, b = [P[max(rng.choice(pop, 3, replace=False), key=lambda i: fit_v[i])] for _ in range(2)]
            mask = rng.random(J) < 0.5
            child = np.where(mask, a, b)
            flip = rng.random(J) < 0.01
            child = np.where(flip, ~child, child)
            new.append(child)
        P = np.array(new)
    fit_v = np.array([fit(c) for c in P])
    best = P[int(np.argmax(fit_v))]
    return list(np.where(best)[0]), float(fit_v.max())


# ----------------------------------------------------------------------------- Tian et al. (2021) OFC workflow
def wrapper_cv(X, y, inner, cols, wrapper, seed=0):
    """Inner-CV balanced accuracy of a fixed-parameter wrapper classifier on feature subset `cols`."""
    sc = []
    rng = np.random.default_rng(seed)
    for a, b in inner:
        A, B_ = X[a][:, cols], X[b][:, cols]
        if wrapper == 'LDA':
            m = LinearDiscriminantAnalysis(priors=[0.5, 0.5]).fit(A, y[a])
        elif wrapper == 'kNN':
            idx = balance_idx(y[a], rng)
            m = KNeighborsClassifier(n_neighbors=15, weights='distance').fit(A[idx], y[a][idx])
        elif wrapper == 'SVM':
            m = SVC(C=10, gamma='scale', class_weight='balanced').fit(A, y[a])
        sc.append(balanced_accuracy_score(y[b], m.predict(B_)))
    return np.mean(sc)


def sffs_wrapper(X, y, inner, wrapper, k_max=8, tol=0.002, seed=0):
    """SFFS (Pudil et al., 1994) with an LDA, kNN or SVM wrapper -> optimal feature combination (OFC)."""
    sel, best_by_k = [], {}
    rest = list(range(X.shape[1]))
    while len(sel) < k_max and rest:
        sc = [wrapper_cv(X, y, inner, sel + [f], wrapper, seed) for f in rest]
        f = rest[int(np.argmax(sc))]; sel.append(f); rest.remove(f)
        if len(sel) not in best_by_k or max(sc) > best_by_k[len(sel)][0]:
            best_by_k[len(sel)] = (max(sc), list(sel))
        while len(sel) > 2:
            sc_b = [wrapper_cv(X, y, inner, [s for s in sel if s != f2], wrapper, seed) for f2 in sel]
            j = int(np.argmax(sc_b))
            if sc_b[j] > best_by_k[len(sel) - 1][0] + 1e-9:
                rest.append(sel.pop(j)); best_by_k[len(sel)] = (sc_b[j], list(sel))
            else:
                break
    best = max(v[0] for v in best_by_k.values())
    for k in sorted(best_by_k):
        if best_by_k[k][0] >= best - tol:
            return best_by_k[k][1], best_by_k[k][0]


def dsf_pool(F, y, dates, top_frac=0.05, min_dates=3, max_pool=30, r_max=0.98, seed=0):
    """Disease-specific feature (DSF) pool after Tian et al. (2021): features ranked in the top 5 % for
    separability (ReliefF) on >= 3 of 4 dates, redundancy-filtered and VIF < 10. Returns indices into F."""
    nf = F.shape[1]
    ntop = max(10, int(round(top_frac * nf)))
    W_all, hits = np.zeros(nf), np.zeros(nf)
    ud = np.unique(dates)
    for d in ud:
        m = dates == d
        w = relieff(F[m], y[m], seed=seed)
        W_all += w
        hits[np.argsort(-w)[:ntop]] += 1
    cand = np.where(hits >= min(min_dates, len(ud)))[0]
    if len(cand) < 5:
        cand = np.argsort(-W_all)[:max(5, ntop)]
    cand = cand[np.argsort(-W_all[cand])]
    Z = (F - F.mean(0)) / np.where(F.std(0) > 0, F.std(0), 1)
    pool = []
    for c in cand:
        if all(abs(np.corrcoef(Z[:, c], Z[:, p])[0, 1]) < r_max for p in pool):
            pool.append(c)
        if len(pool) >= max_pool:
            break
    keep = vif_filter(Z[:, pool])
    return [pool[i] for i in keep], len(cand)
