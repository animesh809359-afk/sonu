"""Feature-selection methods of the researcher's filter / wrapper / embedded comparison (Panda, 2026),
taken unchanged from the leaf-level pipeline (white_rust_analysis/scripts/s12_fs_methods.py)."""
import numpy as np
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.cross_decomposition import PLSRegression
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.metrics import balanced_accuracy_score
from pcommon import *
from models import relieff


def rank_svm_rfe(Z, yy):
    """SVM-RFE (Guyon et al., 2002): linear SVM, balanced weights; 10 % removed per step to 100, then one at a time."""
    alive = list(range(Z.shape[1])); elim = []
    while len(alive) > 1:
        m = LinearSVC(C=0.01, class_weight='balanced', dual=False, max_iter=5000).fit(Z[:, alive], yy)
        w = np.abs(m.coef_[0])
        n_drop = max(1, int(0.1 * len(alive))) if len(alive) > 100 else 1
        order = np.argsort(w)[:n_drop]
        drop = [alive[i] for i in order]
        elim += drop
        alive = [a for a in alive if a not in set(drop)]
    return (alive + elim[::-1])


def rank_lasso(Z, yy):
    """L1-logistic regression (Tibshirani, 1996): features ordered by entry along the regularisation path."""
    Cs = np.logspace(-3, 0, 25)
    entry = np.full(Z.shape[1], np.inf); last = None
    for k, C in enumerate(Cs):
        m = LogisticRegression(penalty='l1', solver='liblinear', C=C, class_weight='balanced', max_iter=2000).fit(Z, yy)
        nz = np.abs(m.coef_[0]) > 1e-10
        entry[nz & ~np.isfinite(entry)] = k
        last = np.abs(m.coef_[0])
    r = np.abs([np.corrcoef(Z[:, j], yy)[0, 1] for j in range(Z.shape[1])])
    return list(np.lexsort((-last, -np.nan_to_num(r), entry)))


def rank_cars(Z, yy, inner, n_runs=50, ncomp=5, seed=0):
    """CARS (Li et al., 2009): Monte-Carlo PLS-DA, exponentially decreasing retained fraction + adaptive reweighted sampling."""
    rng = np.random.default_rng(seed)
    p = Z.shape[1]; a = (p / 2) ** (1 / (n_runs - 1)); k = np.log(p / 2) / (n_runs - 1)
    keep = np.arange(p); elim_run = np.full(p, n_runs); best = (np.inf, None)
    i0, i1 = np.where(yy == 0)[0], np.where(yy == 1)[0]
    for run in range(1, n_runs + 1):
        sub = np.r_[rng.choice(i0, int(0.8 * len(i0)), replace=False), rng.choice(i1, int(0.8 * len(i0)), replace=False)]
        pls = PLSRegression(min(ncomp, len(keep)), scale=False).fit(Z[sub][:, keep], 2 * yy[sub] - 1.0)
        w = np.abs(pls.coef_.ravel()); w = w / w.sum()
        r_frac = a * np.exp(-k * run)
        n_keep = max(2, int(round(r_frac * p)))
        top = keep[np.argsort(-w)[:n_keep]]
        wt = w[np.argsort(-w)[:n_keep]]; wt = wt / wt.sum()
        ars = np.unique(rng.choice(top, n_keep, replace=True, p=wt))
        dropped = np.setdiff1d(keep, ars)
        elim_run[dropped] = run
        keep = ars
        err = []
        for a_, b_ in inner:
            m = PLSRegression(min(ncomp, len(keep)), scale=False).fit(Z[a_][:, keep], 2 * yy[a_] - 1.0)
            err.append(np.mean((m.predict(Z[b_][:, keep]).ravel() - (2 * yy[b_] - 1.0)) ** 2))
        if np.mean(err) < best[0]:
            best = (np.mean(err), keep.copy())
    r = np.abs([np.corrcoef(Z[:, j], yy)[0, 1] for j in range(p)])
    order = list(np.lexsort((-np.nan_to_num(r), -elim_run)))
    return order, list(best[1])


def rank_relieff(Z, yy, seed=0):
    """ReliefF (Kononenko, 1994; Mahlein et al., 2013) on all healthy + an equal number of diseased spectra."""
    rng = np.random.default_rng(seed)
    i0, i1 = np.where(yy == 0)[0], np.where(yy == 1)[0]
    sub = np.r_[i0, rng.choice(i1, len(i0), replace=False)]
    w = relieff(Z[sub], yy[sub], m=300, seed=seed)
    return list(np.argsort(-w))


class QDAeq:
    def __init__(self): self.m = QuadraticDiscriminantAnalysis(priors=[0.5, 0.5], reg_param=0.01)
    def fit(self, X, yy): self.m.fit(X, yy); return self
    def predict(self, X): return self.m.predict(X)


def qda_cv(Z, yy, inner, cols):
    return np.mean([balanced_accuracy_score(yy[b], QDAeq().fit(Z[a][:, cols], yy[a]).predict(Z[b][:, cols])) for a, b in inner])


def sffs_qda(Z, yy, inner, k_max=15, n_cand=100):
    """SFFS (Pudil et al., 1994) with an inner-CV QDA balanced-accuracy criterion (Mustafa et al., 2023);
    candidates = the 100 most correlated, mutually non-redundant (|r| < 0.95) features."""
    r = np.nan_to_num(np.abs([np.corrcoef(Z[:, j], yy)[0, 1] for j in range(Z.shape[1])]))
    cand = []
    for j in np.argsort(-r):
        if all(abs(np.corrcoef(Z[:, j], Z[:, c])[0, 1]) < 0.95 for c in cand):
            cand.append(j)
        if len(cand) >= n_cand:
            break
    sel, best_by_k, rest = [], {}, list(cand)
    while len(sel) < k_max and rest:
        sc = [qda_cv(Z, yy, inner, sel + [f]) for f in rest]
        f = rest[int(np.argmax(sc))]; sel.append(f); rest.remove(f)
        if len(sel) not in best_by_k or max(sc) > best_by_k[len(sel)][0]:
            best_by_k[len(sel)] = (max(sc), list(sel))
        while len(sel) > 2:
            sb = [qda_cv(Z, yy, inner, [s for s in sel if s != f2]) for f2 in sel]
            j = int(np.argmax(sb))
            if sb[j] > best_by_k[len(sel) - 1][0] + 1e-9:
                rest.append(sel.pop(j)); best_by_k[len(sel)] = (sb[j], list(sel))
            else:
                break
    return {k: v[1] for k, v in best_by_k.items()}


def redundancy_topk(order, Z, k, thr=0.95):
    out = []
    for j in order:
        if all(abs(np.corrcoef(Z[:, j], Z[:, c])[0, 1]) < thr for c in out):
            out.append(j)
        if len(out) == k:
            break
    return out


def borda(lists, n=20):
    score = {}
    for L in lists:
        for r, f in enumerate(L[:n]):
            score[f] = score.get(f, 0) + (n - r)
    return [f for f, _ in sorted(score.items(), key=lambda t: -t[1])]



def kuncheva(sets, p):
    k = int(np.median([len(s) for s in sets])); vals = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            a, b = set(sets[i][:k]), set(sets[j][:k]); r = len(a & b)
            vals.append((r * p - k * k) / (k * (p - k)))
    return np.mean(vals)


def jaccard(sets):
    v = [len(set(a) & set(b)) / len(set(a) | set(b)) for i, a in enumerate(sets) for b in sets[i + 1:]]
    return np.mean(v)


