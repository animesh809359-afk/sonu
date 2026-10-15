"""E8: best feature-selection methods from the researcher's filter/wrapper/embedded comparison
(composite ranking: SVM-RFE, LASSO, CARS, Borda consensus, ReliefF; most accurate: SFFS with a QDA criterion),
re-implemented on the F1-F6 pool of this analysis and compared - on the same plot-grouped outer folds - with the
robust selection of Tian et al. (2021) / Lv et al. (2023) (S8), the OFC-SVM of E7 and the full SNV spectrum.
Includes a detector-join check (features within the ASD 1000/1800 nm joins excluded).
Usage: python s12_fs_methods.py <n_repeats>"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
import sys, re, time, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from models import *
from s04_cv import load_all, inner_splits, ndsi_top, nd_feats
from sklearn.svm import LinearSVC
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.metrics import balanced_accuracy_score
from joblib import Parallel, delayed

B10, M, fam = load_all()
y = M['y'].to_numpy(); dates = M['date'].to_numpy(); pt = plot_table(M)
JOINS = (1000, 1800)
KS = (5, 10, 15)
METHODS = ['SVM-RFE', 'LASSO', 'CARS', 'ReliefF', 'SFFS (QDA)', 'Consensus (Borda)']


def feature_wl(name):
    """Wavelengths (and half-width) a feature depends on, for the detector-join check."""
    m = re.match(r'^(R|FD)(\d+)$', name)
    if m: return [int(m.group(2))], 20
    m = re.match(r'^WF(\d+)_s(\d+)$', name)
    if m: return [int(m.group(1))], max(20, 2 ** int(m.group(2)))
    m = re.match(r'^ND\((\d+),(\d+)\)$', name)
    if m: return [int(m.group(1)), int(m.group(2))], 20
    m = re.match(r'^CR(\d+)-(\d+)_', name)
    if m: a, b = int(m.group(1)), int(m.group(2)); return list(range(a, b + 1, 10)), 20
    if name == 'LWVI1': return [983, 1094], 20
    return [], 0


def near_join(name):
    wls, tol = feature_wl(name)
    return any(abs(w - j) <= tol for w in wls for j in JOINS)


def combined(tr_idx):
    pairs = ndsi_top(B10[tr_idx], y[tr_idx], dates[tr_idx])
    N = pd.DataFrame(nd_feats(B10, pairs), columns=[f'ND({WL10[i]},{WL10[j]})' for i, j in pairs])
    return pd.concat([fam['F1'], fam['F2'], N, fam['F4'], fam['F5'], fam['F6']], axis=1)


# ------------------------------------------------------------------ selectors (return a full ranking)
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


def evaluate(cols, Ztr, Zte, ytr, inner, clfs, seed):
    out = {}
    for c in clfs:
        if c == 'QDA':
            s = QDAeq().m.fit(Ztr[:, cols], ytr).predict_proba(Zte[:, cols])[:, 1] - 0.5
            out[c] = (s, (s > 0).astype(int))
        elif c == 'RF':
            m = RandomForestClassifier(n_estimators=200, class_weight='balanced_subsample', n_jobs=1, random_state=seed).fit(Ztr[:, cols], ytr)
            s = m.predict_proba(Zte[:, cols])[:, 1] - 0.5; out[c] = (s, (s > 0).astype(int))
        else:
            p, _ = tune(c, Ztr[:, cols], ytr, inner, seed)
            out[c] = fit_predict(c, p, Ztr[:, cols], ytr, Zte[:, cols], seed)
    return out


def job(rep, fold, assign):
    seed = 8000 + rep
    f = M['plot'].map(assign).to_numpy(); tr, te = np.where(f != fold)[0], np.where(f == fold)[0]
    inner = inner_splits(M.iloc[tr].reset_index(drop=True), 3, seed)
    F = combined(tr); names = np.array(F.columns); A = F.to_numpy(float)
    mu, sd = A[tr].mean(0), np.where(A[tr].std(0) > 0, A[tr].std(0), 1)
    Z = (A - mu) / sd; Ztr, Zte, ytr = Z[tr], Z[te], y[tr]
    t0 = time.time(); ranks, native, times = {}, {}, {}
    t = time.time(); ranks['SVM-RFE'] = rank_svm_rfe(Ztr, ytr); times['SVM-RFE'] = time.time() - t
    t = time.time(); ranks['LASSO'] = rank_lasso(Ztr, ytr); times['LASSO'] = time.time() - t
    t = time.time(); ranks['CARS'], native['CARS'] = rank_cars(Ztr, ytr, inner, seed=seed); times['CARS'] = time.time() - t
    t = time.time(); ranks['ReliefF'] = rank_relieff(Ztr, ytr, seed=seed); times['ReliefF'] = time.time() - t
    t = time.time(); sffs_sets = sffs_qda(Ztr, ytr, inner); times['SFFS (QDA)'] = time.time() - t
    ranks['SFFS (QDA)'] = sffs_sets[max(sffs_sets)]
    rc = {m: redundancy_topk(ranks[m], Ztr, 20) for m in ['SVM-RFE', 'LASSO', 'CARS', 'ReliefF']}
    rc['SFFS (QDA)'] = sffs_sets[max(sffs_sets)]
    ranks['Consensus (Borda)'] = borda([rc[m] for m in rc])
    out = []
    def add(method, k, cols, clfs, variant='all features'):
        res = evaluate(cols, Ztr, Zte, ytr, inner, clfs, seed)
        for c, (s, pr) in res.items():
            out.append(dict(rep=rep, fold=fold, method=method, variant=variant, k=k, clf=c, te=te, score=s, pred=pr,
                            features=list(names[cols]), near_join_share=float(np.mean([near_join(n) for n in names[cols]]))))
    for m in METHODS:
        for k in KS:
            cols = sffs_sets[min(k, max(sffs_sets))] if m == 'SFFS (QDA)' else redundancy_topk(ranks[m], Ztr, k)
            add(m, k, cols, ['QDA', 'RF', 'SVM', 'LDA'] if k == 10 else ['QDA', 'RF'])
    # comparators on the same fold
    sel, _ = robust_select(A[tr], ytr, dates[tr], inner, seed=seed)
    add('Robust selection + SFFS-LDA (S8)', len(sel), sel, ['QDA', 'RF', 'SVM', 'LDA'])
    pool, _ = dsf_pool(A[tr], ytr, dates[tr], seed=seed)
    o_sel, _ = sffs_wrapper(Ztr[:, pool], ytr, inner, 'SVM', seed=seed)
    add('OFC-SVM (Tian et al., 2021)', len(o_sel), [pool[i] for i in o_sel], ['QDA', 'RF', 'SVM', 'LDA'])
    S = snv(B10); fs = evaluate(list(range(S.shape[1])), S[tr], S[te], ytr, inner, ['SVM', 'LDA', 'LR'], seed)
    for c, (s, pr) in fs.items():
        out.append(dict(rep=rep, fold=fold, method='Full spectrum (SNV)', variant='all features', k=201, clf=c, te=te, score=s, pred=pr, features=[], near_join_share=np.nan))
    # detector-join check: drop every feature within the ASD joins and repeat the best selectors
    ok = np.array([not near_join(n) for n in names])
    idx_ok = np.where(ok)[0]
    r_svm = rank_svm_rfe(Ztr[:, idx_ok], ytr)
    add('SVM-RFE', 10, [idx_ok[i] for i in redundancy_topk(r_svm, Ztr[:, idx_ok], 10)], ['QDA', 'RF', 'SVM'], 'join bands excluded')
    s_sets = sffs_qda(Ztr[:, idx_ok], ytr, inner, k_max=10)
    add('SFFS (QDA)', 10, [idx_ok[i] for i in s_sets[max(s_sets)]], ['QDA', 'RF', 'SVM'], 'join bands excluded')
    sel_ok, _ = robust_select(A[tr][:, idx_ok], ytr, dates[tr], inner, seed=seed)
    add('Robust selection + SFFS-LDA (S8)', len(sel_ok), [idx_ok[i] for i in sel_ok], ['QDA', 'RF', 'SVM'], 'join bands excluded')
    for r_ in out:
        r_['t_select'] = times
    return out


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


if __name__ == '__main__':
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    t = time.time(); jobs = []
    for rep in range(R):
        a = plot_folds(pt, 4, 8000 + rep)
        for fold in range(4):
            jobs.append((rep, fold, a))
    res = Parallel(n_jobs=int(os.environ.get('NJOBS', 4)), verbose=5)(delayed(job)(*j) for j in jobs)
    res = [x for r in res for x in r]
    pickle.dump(res, open(os.path.join(CACHE, 'fsm.pkl'), 'wb'))
    D = pd.DataFrame(res)
    rows = []
    for (m, v, k, c, rep), g in D.groupby(['method', 'variant', 'k', 'clf', 'rep'], sort=False):
        te = np.concatenate(g['te'].to_list()); pr = np.concatenate(g['pred'].to_list()); s = np.concatenate(g['score'].to_list())
        rows.append(dict(method=m, variant=v, k=k if m not in ('Robust selection + SFFS-LDA (S8)', 'OFC-SVM (Tian et al., 2021)') else 'native',
                         clf=c, rep=rep, near_join_share=g['near_join_share'].mean(), **metrics(y[te], pr, s)))
    REP = pd.DataFrame(rows); REP.to_csv(os.path.join(TAB, 'E8_fs_reps.csv'), index=False)
    fold_rows = [dict(method=r['method'], variant=r['variant'], k=r['k'] if r['method'] not in ('Robust selection + SFFS-LDA (S8)', 'OFC-SVM (Tian et al., 2021)') else 'native',
                      clf=r['clf'], rep=r['rep'], fold=r['fold'], BA=balanced_accuracy_score(y[r['te']], r['pred'])) for r in res]
    FO = pd.DataFrame(fold_rows); FO.to_csv(os.path.join(TAB, 'E8_fs_folds.csv'), index=False)
    # stability (top-10 sets over the outer training folds) and feature frequency
    p_pool = 201 + 46 + 3 + 221 + 24 + 1608
    st, fr = [], []
    for (m, v), g in D[(D['clf'] == 'QDA') & ((D['k'] == 10) | D['method'].str.contains('S8|OFC'))].groupby(['method', 'variant'], sort=False):
        g = g.drop_duplicates(['rep', 'fold'])
        sets = g['features'].to_list()
        st.append(dict(method=m, variant=v, mean_size=np.mean([len(s) for s in sets]), Jaccard=jaccard(sets), Kuncheva=kuncheva(sets, p_pool),
                       near_join_share=g['near_join_share'].mean()))
        cnt = pd.Series([f for s in sets for f in s]).value_counts()
        for feat, n in cnt.head(15).items():
            fr.append(dict(method=m, variant=v, Feature=feat, Frequency_pct=100 * n / len(sets), Near_join=near_join(feat)))
    pd.DataFrame(st).to_csv(os.path.join(TAB, 'E8_fs_stability.csv'), index=False)
    pd.DataFrame(fr).to_csv(os.path.join(TAB, 'E8_fs_feature_frequency.csv'), index=False)
    # paired Wilcoxon tests vs the reference (robust selection S8 with SVM) and composite ranking
    from scipy.stats import wilcoxon, friedmanchisquare
    k10 = FO[(FO['variant'] == 'all features') & ((FO['k'] == 10) | (FO['k'] == 'native') | (FO['k'] == 201))]
    W = k10[k10['clf'] == 'SVM'].pivot_table(index=['rep', 'fold'], columns='method', values='BA')
    ref = 'Robust selection + SFFS-LDA (S8)'
    tests = []
    for m in W.columns:
        if m == ref: continue
        d = (W[m] - W[ref]).dropna()
        p = wilcoxon(d).pvalue if (d != 0).any() else 1.0
        tests.append(dict(Comparison=f'{m} vs {ref} (SVM, k = 10 / native)', Mean_BA_difference=d.mean(), Wins=int((d > 0).sum()), Losses=int((d < 0).sum()), Wilcoxon_p=p))
    T = pd.DataFrame(tests)
    if len(T):
        from statsmodels.stats.multitest import multipletests
        T['Holm_p'] = multipletests(T['Wilcoxon_p'], method='holm')[1]
    T.to_csv(os.path.join(TAB, 'E8_fs_tests.csv'), index=False)
    fchi, fp = friedmanchisquare(*[W[c].to_numpy() for c in W.columns])
    S_ = REP[(REP['variant'] == 'all features') & (REP['k'].isin([10, 'native']))].groupby(['method', 'clf'])['BA'].mean().unstack()
    ST = pd.DataFrame(st).query("variant == 'all features'").set_index('method')
    comp = pd.DataFrame({'BA_QDA': S_['QDA'], 'BA_RF': S_['RF'], 'BA_SVM': S_['SVM'], 'BA_LDA': S_['LDA'], 'Jaccard': ST['Jaccard'], 'Kuncheva': ST['Kuncheva'],
                         'Near_join_share': ST['near_join_share']}).dropna(subset=['BA_QDA'])
    for c in ['BA_QDA', 'BA_RF', 'BA_SVM', 'Jaccard']:
        comp['rank_' + c] = comp[c].rank(ascending=False)
    comp['Mean_rank'] = comp[[c for c in comp.columns if c.startswith('rank_')]].mean(1)
    comp = comp.sort_values('Mean_rank'); comp['Overall_rank'] = np.arange(1, len(comp) + 1)
    comp.reset_index().rename(columns={'index': 'method'}).to_csv(os.path.join(TAB, 'E8_fs_composite_ranking.csv'), index=False)
    pd.DataFrame([dict(Test='Friedman over methods (SVM, k = 10 / native, 20 outer folds)', chi2=fchi, p=fp)]).to_csv(os.path.join(TAB, 'E8_fs_friedman.csv'), index=False)
    # final top-10 sets on all data
    allidx = np.arange(len(M)); inner_all = inner_splits(M, 4, 77)
    F = combined(allidx); names = np.array(F.columns); A = F.to_numpy(float); Z = (A - A.mean(0)) / np.where(A.std(0) > 0, A.std(0), 1)
    fin = []
    rk = {'SVM-RFE': rank_svm_rfe(Z, y), 'LASSO': rank_lasso(Z, y), 'CARS': rank_cars(Z, y, inner_all, seed=77)[0], 'ReliefF': rank_relieff(Z, y, seed=77)}
    ss = sffs_qda(Z, y, inner_all)
    sets = {m: redundancy_topk(rk[m], Z, 10) for m in rk}
    sets['SFFS (QDA)'] = ss[min(10, max(ss))]
    sets['Consensus (Borda)'] = redundancy_topk(borda([redundancy_topk(rk[m], Z, 20) for m in rk] + [ss[max(ss)]]), Z, 10)
    for m, cols in sets.items():
        for i, c in enumerate(cols):
            fin.append(dict(method=m, rank=i + 1, Feature=names[c], Near_join=near_join(names[c])))
    pd.DataFrame(fin).to_csv(os.path.join(TAB, 'E8_fs_final_sets.csv'), index=False)
    print('E8 done', round(time.time() - t), 's')
