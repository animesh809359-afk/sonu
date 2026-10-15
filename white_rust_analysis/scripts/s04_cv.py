"""Step 5-7: nested, plot-grouped, stratified, repeated 4-fold CV of 10 feature scenarios x 10 classifiers.
Usage: python s04_cv.py <n_repeats> <tag> [scenario,...] [classifier,...]"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import sys, time, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from models import *
from joblib import Parallel, delayed


def load_all():
    d = np.load(os.path.join(CACHE, 'clean.npz'))
    M = pd.read_csv(os.path.join(CACHE, 'meta_clean.csv'))
    fam = {'F1': pd.read_pickle(os.path.join(CACHE, 'F1_bands.pkl')),
           'F2': pd.read_pickle(os.path.join(CACHE, 'F2_VI.pkl')),
           'F4': pd.read_pickle(os.path.join(CACHE, 'F4_deriv.pkl')),
           'F5': pd.read_pickle(os.path.join(CACHE, 'F5_CR.pkl')),
           'F6': pd.read_pickle(os.path.join(CACHE, 'F6_CWT.pkl'))}
    return d['B10'], M, fam


SCENARIOS = {
    'S1': 'Full spectrum (SNV, 201 bands)',
    'S2': 'F1 Bands + robust selection',
    'S3': 'F2 Vegetation indices + robust selection',
    'S4': 'F3 Novel NDSI (in-fold top-3)',
    'S5': 'F4 Derivative features + robust selection',
    'S6': 'F5 Continuum removal + robust selection',
    'S7': 'F6 Wavelet (CWT) + robust selection',
    'S8': 'Combined F1-F6 + robust selection',
    'S9': 'SPA bands (SNV)',
    'S10': 'GA-PLS bands (SNV)',
}


def inner_splits(Mtr, k=3, seed=0):
    pt = plot_table(Mtr)
    a = plot_folds(pt, k, seed)
    f = Mtr['plot'].map(a).to_numpy()
    return [(np.where(f != j)[0], np.where(f == j)[0]) for j in range(k)]


def ndsi_top(B, y, dates, n=3):
    I, J, s_mean, s_min = ndsi_scores(B, y, dates)
    order = np.argsort(-s_mean)
    used, out = set(), []
    for k in order:
        i, j = I[k], J[k]
        if i in used or j in used:
            continue
        out.append((i, j)); used |= {i, j}
        if len(out) == n:
            break
    return out


def nd_feats(B, pairs):
    return np.column_stack([(B[:, i] - B[:, j]) / (B[:, i] + B[:, j]) for i, j in pairs])


def scenario_matrix(sc, tr, te, B10, M, fam, inner, y, dates, seed):
    """Return Xtr, Xte, feature names, info for one scenario fitted on the training indices."""
    info = {}
    if sc == 'S1':
        S = snv(B10)
        return S[tr], S[te], [f'R{w}' for w in WL10], info
    if sc in ('S9', 'S10'):
        S = snv(B10)
        if sc == 'S9':
            cols, crit = spa(S[tr], y[tr].astype(float), inner)
        else:
            cols, crit = ga_pls(S[tr], y[tr], inner, seed=seed)
        info['crit'] = crit
        return S[tr][:, cols], S[te][:, cols], [f'R{WL10[c]}' for c in cols], info
    if sc == 'S4':
        pairs = ndsi_top(B10[tr], y[tr], dates[tr])
        N = nd_feats(B10, pairs)
        return N[tr], N[te], [f'ND({WL10[i]},{WL10[j]})' for i, j in pairs], info
    if sc == 'S8':
        pairs = ndsi_top(B10[tr], y[tr], dates[tr])
        N = pd.DataFrame(nd_feats(B10, pairs), columns=[f'ND({WL10[i]},{WL10[j]})' for i, j in pairs])
        F = pd.concat([fam['F1'], fam['F2'], N, fam['F4'], fam['F5'], fam['F6']], axis=1)
    else:
        F = fam[{'S2': 'F1', 'S3': 'F2', 'S5': 'F4', 'S6': 'F5', 'S7': 'F6'}[sc]]
    A = F.to_numpy(float)
    sel, info = robust_select(A[tr], y[tr], dates[tr], inner, seed=seed)
    return A[tr][:, sel], A[te][:, sel], list(F.columns[sel]), info


def run_job(rep, fold, assign, B10, M, fam, scen, clfs, seed):
    y = M['y'].to_numpy(); dates = M['date'].to_numpy()
    f = M['plot'].map(assign).to_numpy()
    tr, te = np.where(f != fold)[0], np.where(f == fold)[0]
    inner_rel = inner_splits(M.iloc[tr].reset_index(drop=True), 3, seed)
    out = []
    for sc in scen:
        t0 = time.time()
        Xtr, Xte, names, info = scenario_matrix(sc, tr, te, B10, M, fam, inner_rel, y, dates, seed)
        tsel = time.time() - t0
        for c in clfs:
            t1 = time.time()
            p, s_in = tune(c, Xtr, y[tr], inner_rel, seed)
            score, pred = fit_predict(c, p, Xtr, y[tr], Xte, seed)
            out.append(dict(rep=rep, fold=fold, scenario=sc, clf=c, te=te, score=score, pred=pred, params=p,
                            inner_BA=s_in, features=names, sel_info=info, t_sel=tsel, t_clf=time.time() - t1))
    return out


if __name__ == '__main__':
    R = int(sys.argv[1]); tag = sys.argv[2]
    scen = sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] != 'all' else list(SCENARIOS)
    clfs = sys.argv[4].split(',') if len(sys.argv) > 4 and sys.argv[4] != 'all' else CLF_NAMES
    njobs = int(os.environ.get('NJOBS', 4))
    B10, M, fam = load_all()
    pt = plot_table(M)
    jobs = []
    for rep in range(R):
        assign = plot_folds(pt, 4, 1000 + rep)
        for fold in range(4):
            jobs.append((rep, fold, assign))
    t = time.time()
    res = Parallel(n_jobs=njobs, verbose=5)(delayed(run_job)(r, f, a, B10, M, fam, scen, clfs, 1000 + r)
                                            for r, f, a in jobs)
    res = [x for r in res for x in r]
    with open(os.path.join(CACHE, f'cv_{tag}.pkl'), 'wb') as fh:
        pickle.dump(res, fh)
    print('done', tag, len(res), 'rows', round(time.time() - t, 1), 's')
