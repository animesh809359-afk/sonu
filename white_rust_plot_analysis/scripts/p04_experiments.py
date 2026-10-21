"""Step 8 - supporting experiments at plot level.
E1 raw vs smoothed branch      E2 single-date models          E3 temporal / variety transfer (LODO, LOVO)
E4 date normalisation          E5 label-permutation test      E6 design controls (block vs block, control vs block)
E7 OFC-SFFS (Tian et al. 2021) E8 feature-selection methods (Panda 2026)
E9 equal leaf-number check (plot means re-built from the leaf spectra with 3 leaves per plot)
Usage: python p04_experiments.py E1 [E2 ...]"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import sys, time, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcommon import *
from p03_cv import load_all, run, run_job, scenario_matrix, inner_splits, combined, date_norm, FAMS
from models import tune, fit_predict, dsf_pool, sffs_wrapper, wrapper_cv
from common import metrics
import pfs
from sklearn.ensemble import RandomForestClassifier
from joblib import Parallel, delayed

NJ = int(os.environ.get('NJOBS', 4))
CL5 = ['LDA', 'PLS-DA', 'LR', 'SVM', 'RF']


def save(df, name):
    df.to_csv(os.path.join(TAB, name), index=False)
    print('saved', name, len(df))


def subset(M, fam, mask):
    idx = np.where(mask)[0]
    return M.iloc[idx].reset_index(drop=True), {k: v.iloc[idx].reset_index(drop=True) for k, v in fam.items()}


def metric_rows(res, y, keys):
    return rep_metrics(res, keys, y, extra=('features',))


# ---------------------------------------------------------------- E1 branch
def E1():
    M, fam = load_all('smooth')
    res = run(10, ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S10'], CL5, 'smooth', M=M, fam=fam, njobs=NJ)
    df = metric_rows(res, M['y'].to_numpy(), ['scenario', 'clf']); df.insert(0, 'branch', 'smoothed')
    save(df, 'E1_branch_reps.csv')


# ---------------------------------------------------------------- E2 single date
def E2():
    M0, fam0 = load_all('raw')
    out = []
    for dt in DATE_ORDER:
        M, fam = subset(M0, fam0, (M0['date'] == dt).to_numpy())
        res = run(10, ['S1', 'S2', 'S5', 'S6', 'S7', 'S8', 'S10'], CL5, M=M, fam=fam, njobs=NJ, seed0=2000)
        df = metric_rows(res, M['y'].to_numpy(), ['scenario', 'clf']); df.insert(0, 'date', DATE_LABEL[dt])
        out.append(df)
    save(pd.concat(out), 'E2_single_date_reps.csv')


# ---------------------------------------------------------------- E3 transfer
def _transfer_job(kind, hold, M, fam, scen, clfs, dn):
    y = M['y'].to_numpy(); dates = M['date'].to_numpy()
    col = 'date' if kind == 'LODO' else 'variety'
    te = np.where(M[col] == hold)[0]; tr = np.where(M[col] != hold)[0]
    inner = inner_splits(M.iloc[tr].reset_index(drop=True), 3, 7)
    out = []
    for sc in scen:
        Xtr, Xte, names, _ = scenario_matrix(sc, tr, te, M, fam, inner, y, dates, 7)
        if dn:
            Xtr, Xte = date_norm(Xtr, Xte, dates[tr], dates[te])
        for c in clfs:
            p, _ = tune(c, Xtr, y[tr], inner, 7)
            s, pr = fit_predict(c, p, Xtr, y[tr], Xte, 7)
            r = dict(kind=kind, held_out=DATE_LABEL.get(hold, hold), date_norm=dn, scenario=sc, clf=c, n_features=len(names))
            r.update(metrics(y[te], pr, s)); out.append(r)
    return out


def E3():
    M, fam = load_all('raw')
    jobs = [('LODO', d, dn) for d in DATE_ORDER for dn in (False, True)] + [('LOVO', v, False) for v in ['V1', 'V2', 'V3']]
    res = Parallel(n_jobs=NJ, verbose=2)(delayed(_transfer_job)(k, h, M, fam, ['S1', 'S2', 'S6', 'S8', 'S10'], CL5, dn) for k, h, dn in jobs)
    save(pd.DataFrame([x for r in res for x in r]), 'E3_transfer.csv')


# ---------------------------------------------------------------- E4 date normalisation inside the main CV
def E4():
    M, fam = load_all('raw')
    res = run(10, ['S1', 'S2', 'S6', 'S10'], ['LDA', 'LR', 'SVM', 'RF'], M=M, fam=fam, njobs=NJ, dnorm=True)
    df = metric_rows(res, M['y'].to_numpy(), ['scenario', 'clf']); df.insert(0, 'date_norm', True)
    save(df, 'E4_datenorm_reps.csv')


# ---------------------------------------------------------------- E5 permutation test (Ojala & Garriga, 2010)
def _perm_job(k, M, fam, pipes):
    rng = np.random.default_rng(5000 + k)
    Mp = M.copy()
    if k > 0:  # whole plots permuted within variety x inoculation cells (design-restricted)
        P = plot_table(M)
        perm = P.groupby('cell')['y'].transform(lambda s: rng.permutation(s.to_numpy()))
        Mp['y'] = M['plot'].map(pd.Series(perm.to_numpy(), index=P['plot'])).to_numpy()
    out = []
    for sc, c in pipes:
        rows = []
        a = cell_folds(plot_table(Mp), 4, 1000)
        for fold in range(4):
            rows += run_job(0, fold, a, Mp, fam, [sc], [c], 1000)
        te = np.concatenate([r['te'] for r in rows]); pr = np.concatenate([r['pred'] for r in rows]); s = np.concatenate([r['score'] for r in rows])
        m = metrics(Mp['y'].to_numpy()[te], pr, s)
        out.append(dict(perm=k, scenario=sc, clf=c, BA=m['BA'], MCC=m['MCC'], ROC_AUC=m['ROC_AUC']))
    return out


def E5(n_perm=200):
    M, fam = load_all('raw')
    pipes = [('S2', 'LR'), ('S6', 'LR'), ('S1', 'PLS-DA')]
    res = Parallel(n_jobs=NJ, verbose=2)(delayed(_perm_job)(k, M, fam, pipes) for k in range(n_perm + 1))
    df = pd.DataFrame([x for r in res for x in r])
    save(df, 'E5_permutation.csv')
    obs = df[df.perm == 0].set_index(['scenario', 'clf'])
    rows = []
    for (sc, c), g in df[df.perm > 0].groupby(['scenario', 'clf']):
        o = obs.loc[(sc, c)]
        rows.append(dict(scenario=sc, clf=c, BA_observed=o['BA'], BA_null_mean=g.BA.mean(), BA_null_sd=g.BA.std(), BA_null_95=g.BA.quantile(0.95),
                         p_value=(1 + (g.BA >= o['BA']).sum()) / (1 + len(g)), n_perm=len(g)))
    save(pd.DataFrame(rows), 'E5_permutation_summary.csv')


# ---------------------------------------------------------------- E6 design controls
def E6():
    M0, fam0 = load_all('raw')
    out = []
    contrasts = [('C', 'R1'), ('C', 'R2'), ('C', 'R3'), ('R1', 'R2'), ('R1', 'R3'), ('R2', 'R3')]
    for a, b in contrasts:
        M, fam = subset(M0, fam0, M0['block'].isin([a, b]).to_numpy())
        M['y'] = (M['block'] == b).astype(int)
        res = run(10, ['S2', 'S6', 'S10'], ['LR', 'SVM', 'RF'], M=M, fam=fam, njobs=NJ, seed0=3000)
        df = metric_rows(res, M['y'].to_numpy(), ['scenario', 'clf'])
        df.insert(0, 'contrast', f'{a} vs {b}'); df.insert(1, 'type', 'control vs inoculated block' if a == 'C' else 'inoculated block vs block')
        out.append(df)
    save(pd.concat(out), 'E6_design_controls_reps.csv')


# ---------------------------------------------------------------- E7 OFC (Tian et al., 2021)
def _ofc_job(rep, fold, a, M, fam):
    y = M['y'].to_numpy(); dates = M['date'].to_numpy(); seed = 6000 + rep
    f = M['plot'].map(a).to_numpy(); tr, te = np.where(f != fold)[0], np.where(f == fold)[0]
    inner = inner_splits(M.iloc[tr].reset_index(drop=True), 3, seed)
    F = combined(fam, tr, y, dates, fam['REF'].to_numpy(float)); names = np.array(F.columns); A = F.to_numpy(float)
    mu, sd = A[tr].mean(0), np.where(A[tr].std(0) > 0, A[tr].std(0), 1); Z = (A - mu) / sd
    pool, n_stable = dsf_pool(A[tr], y[tr], dates[tr], seed=seed)
    sets = {'All DSFs': list(range(len(pool)))}
    for w in ('LDA', 'kNN', 'SVM'):
        s_, _ = sffs_wrapper(Z[tr][:, pool], y[tr], inner, w, seed=seed); sets[f'OFC-{w}'] = s_
    out = []
    for nm, cols in sets.items():
        cc = [pool[i] for i in cols]
        for c in ['LDA', 'kNN', 'SVM', 'LR', 'RF']:
            p, _ = tune(c, Z[tr][:, cc], y[tr], inner, seed)
            s, pr = fit_predict(c, p, Z[tr][:, cc], y[tr], Z[te][:, cc], seed)
            out.append(dict(rep=rep, fold=fold, feature_set=nm, clf=c, te=te, score=s, pred=pr, features=list(names[cc]), n_pool=len(pool)))
    return out


def E7(R=10):
    M, fam = load_all('raw'); P = plot_table(M)
    jobs = [(r, f, cell_folds(P, 4, 1000 + r)) for r in range(R) for f in range(4)]
    res = Parallel(n_jobs=NJ, verbose=2)(delayed(_ofc_job)(r, f, a, M, fam) for r, f, a in jobs)
    res = [x for r in res for x in r]
    pickle.dump(res, open(os.path.join(CACHE, 'E7_ofc.pkl'), 'wb'))
    save(metric_rows(res, M['y'].to_numpy(), ['feature_set', 'clf']), 'E7_ofc_reps.csv')


# ---------------------------------------------------------------- E8 feature-selection methods (Panda, 2026)
KS = (5, 10, 15)
FSM = ['SVM-RFE', 'LASSO', 'CARS', 'ReliefF', 'SFFS (QDA)', 'Consensus (Borda)']


def _evaluate(cols, Ztr, Zte, ytr, inner, clfs, seed):
    out = {}
    for c in clfs:
        if c == 'QDA':
            s = pfs.QDAeq().m.fit(Ztr[:, cols], ytr).predict_proba(Zte[:, cols])[:, 1] - 0.5
        elif c == 'RF':
            s = RandomForestClassifier(n_estimators=200, class_weight='balanced_subsample', n_jobs=1, random_state=seed).fit(Ztr[:, cols], ytr).predict_proba(Zte[:, cols])[:, 1] - 0.5
        else:
            p, _ = tune(c, Ztr[:, cols], ytr, inner, seed)
            s, _ = fit_predict(c, p, Ztr[:, cols], ytr, Zte[:, cols], seed)
        out[c] = (s, (s > 0).astype(int))
    return out


def _fs_job(rep, fold, a, M, fam):
    y = M['y'].to_numpy(); seed = 8000 + rep; dates = M['date'].to_numpy()
    f = M['plot'].map(a).to_numpy(); tr, te = np.where(f != fold)[0], np.where(f == fold)[0]
    inner = inner_splits(M.iloc[tr].reset_index(drop=True), 3, seed)
    F = combined(fam, tr, y, dates, fam['REF'].to_numpy(float)); names = np.array(F.columns); A = F.to_numpy(float)
    mu, sd = A[tr].mean(0), np.where(A[tr].std(0) > 0, A[tr].std(0), 1); Z = (A - mu) / sd
    Ztr, Zte, ytr = Z[tr], Z[te], y[tr]
    ranks = {'SVM-RFE': pfs.rank_svm_rfe(Ztr, ytr), 'LASSO': pfs.rank_lasso(Ztr, ytr)}
    ranks['CARS'], _ = pfs.rank_cars(Ztr, ytr, inner, seed=seed)
    ranks['ReliefF'] = pfs.rank_relieff(Ztr, ytr, seed=seed)
    sffs_sets = pfs.sffs_qda(Ztr, ytr, inner)
    rc = {m: pfs.redundancy_topk(ranks[m], Ztr, 20) for m in ['SVM-RFE', 'LASSO', 'CARS', 'ReliefF']}
    rc['SFFS (QDA)'] = sffs_sets[max(sffs_sets)]
    ranks['Consensus (Borda)'] = pfs.borda([rc[m] for m in rc])
    out = []
    for m in FSM:
        for k in KS:
            cols = sffs_sets[min(k, max(sffs_sets))] if m == 'SFFS (QDA)' else pfs.redundancy_topk(ranks[m], Ztr, k)
            for c, (s, pr) in _evaluate(cols, Ztr, Zte, ytr, inner, ['QDA', 'RF', 'SVM', 'LDA', 'LR'] if k == 10 else ['QDA', 'RF', 'LR'], seed).items():
                out.append(dict(rep=rep, fold=fold, method=m, k=k, clf=c, te=te, score=s, pred=pr, features=list(names[cols]),
                                family_share={fm: float(np.mean([n.startswith(fm) for n in names[cols]])) for fm in ('R', 'D1_', 'D2_', 'D3_', 'WF', 'CR')}))
    return out


def E8(R=10):
    M, fam = load_all('raw'); P = plot_table(M)
    jobs = [(r, f, cell_folds(P, 4, 1000 + r)) for r in range(R) for f in range(4)]
    res = Parallel(n_jobs=NJ, verbose=2)(delayed(_fs_job)(r, f, a, M, fam) for r, f, a in jobs)
    res = [x for r in res for x in r]
    pickle.dump(res, open(os.path.join(CACHE, 'E8_fs.pkl'), 'wb'))
    save(metric_rows(res, M['y'].to_numpy(), ['method', 'k', 'clf']), 'E8_fs_reps.csv')


# ---------------------------------------------------------------- E9 equal leaf-number check
def rebuild_from_leaves(n_leaf=None, seed=0):
    """Plot means of the leaf spectra (exact duplicate spectra dropped); n_leaf=None uses every leaf,
    otherwise n_leaf leaves drawn at random per plot and date. Features are computed identically for both."""
    import common as LC
    d = np.load(os.path.join(LEAF, 'cache', 'raw.npz')); X, wl = d['X'], d['wl']
    L = pd.read_csv(os.path.join(LEAF, 'cache', 'meta.csv'))
    M = load_meta()
    rng = np.random.default_rng(seed)
    R1 = np.zeros((len(M), X.shape[1])); used = np.zeros(len(M), int)
    grp = L.groupby(['date', 'plot']).indices
    for i, (dt, pl) in enumerate(zip(M['date'], M['plot'])):
        idx = grp[(dt, pl)]
        _, first = np.unique(X[idx].round(10), axis=0, return_index=True)
        idx = idx[np.sort(first)]
        if n_leaf is not None:
            idx = rng.choice(idx, min(n_leaf, len(idx)), replace=False)
        R1[i] = X[idx].mean(0); used[i] = len(idx)
    k = (wl >= 400) & (wl <= 2400)
    D1 = np.gradient(R1, axis=1); D2 = np.gradient(D1, axis=1); D3 = np.gradient(D2, axis=1)
    fam = {'REF': pd.DataFrame(bin10(R1[:, k], wl[k]), columns=[f'R{w}' for w in WL10]),
           'FD1': pd.DataFrame(bin10(D1[:, k], wl[k]), columns=[f'D1_{w}' for w in WL10]),
           'FD2': pd.DataFrame(bin10(D2[:, k], wl[k]), columns=[f'D2_{w}' for w in WL10]),
           'FD3': pd.DataFrame(bin10(D3[:, k], wl[k]), columns=[f'D3_{w}' for w in WL10]),
           'VI': LC.vegetation_indices(R1[:, k], wl[k])[0]}
    return R1, wl, used, fam


def E9(n_draw=5):
    M = load_meta(); y = M['y'].to_numpy()
    R_all, wl, used_all, fam_all = rebuild_from_leaves(None)
    W = load_spectra('raw')[0]
    chk = dict(max_abs_diff_vs_workbook=float(np.abs(R_all - W).max()), leaves_match=bool((used_all == M['n_leaves']).all()))
    print('rebuild check', chk)
    out = []
    for draw in range(-1, n_draw):
        if draw < 0:
            fam, used, lab = fam_all, used_all, 'all leaves (re-built)'
        else:
            _, _, used, fam = rebuild_from_leaves(3, seed=100 + draw); lab = '3 random leaves per plot'
        sc_map = {'S1': 'REF', 'S2': 'FD1', 'S3': 'FD2', 'S4': 'FD3', 'S6': 'VI'}
        res = run(5 if draw < 0 else 2, list(sc_map), ['LDA', 'LR', 'SVM'], M=M, fam=fam, njobs=NJ, seed0=1000)
        df = metric_rows(res, y, ['scenario', 'clf']); df.insert(0, 'averaging', lab); df.insert(1, 'draw', draw)
        out.append(df)
    E = pd.concat(out); E['check_max_abs_diff'] = chk['max_abs_diff_vs_workbook']; E['check_leaves_match'] = chk['leaves_match']
    save(E, 'E9_equal_leaves_reps.csv')


if __name__ == '__main__':
    for e in sys.argv[1:]:
        t = time.time(); globals()[e](); print(e, 'finished in', round(time.time() - t), 's', flush=True)
