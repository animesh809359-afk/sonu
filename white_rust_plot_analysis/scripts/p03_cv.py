"""Steps 5-7 - nested, cell-grouped, repeated 4-fold cross-validation of 12 feature scenarios x 10 classifiers
for healthy vs diseased PLOT discrimination (all 4 dates pooled, 192 plot-date samples, 48 plots).

Outer folds hold out whole variety x inoculation cells (1 control + 3 inoculated plots, all 4 dates), one cell per
variety, so a test fold always has 3 healthy and 9 diseased plots that the model has never seen on any date.
Everything that learns from labels (index search, feature selection, tuning) sees training plots only.
Usage: python p03_cv.py <n_repeats> <tag> [scenarios|all] [classifiers|all] [branch]"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import sys, time, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcommon import *
from models import CLF_NAMES, tune, fit_predict, robust_select, spa, ga_pls
from joblib import Parallel, delayed

SCENARIOS = {
    'S1': 'Reflectance, full spectrum (201 bands)',
    'S2': 'First derivative, full (201)',
    'S3': 'Second derivative, full (201)',
    'S4': 'Third derivative, full (201)',
    'S5': 'Continuum-removal parameters (48)',
    'S6': 'Vegetation indices (87)',
    'S7': 'Red-edge parameters (23)',
    'S8': 'Optimised two-band indices (in-fold NDSI/SR/DI)',
    'S9': 'CWT coefficients + robust selection',
    'S10': 'All families combined + robust selection',
    'S11': 'SPA bands (reflectance)',
    'S12': 'GA-PLS bands (reflectance)',
}
FULL = {'S1': 'REF', 'S2': 'FD1', 'S3': 'FD2', 'S4': 'FD3', 'S5': 'CR', 'S6': 'VI', 'S7': 'RE'}
FAMS = ['REF', 'FD1', 'FD2', 'FD3', 'CR', 'VI', 'RE', 'CWT']

_I, _J = np.triu_indices(len(WL10), 1)


def load_all(branch='raw'):
    M = load_meta()
    fam = {f: load_family(branch, f) for f in FAMS}
    return M, fam


def index_top(B, y, dates, n=3):
    """Exhaustive two-band search (Mandal et al., 2023; Tian et al., 2021; Zhu et al., 2017) on the training plots:
    NDSI, SR and DI of every 10-nm pair scored by mean r2 with disease status over dates (sign-consistent);
    the n best pairs with no band shared are kept for every index type."""
    out = []
    for kind in ('NDSI', 'SR', 'DI'):
        r2s, sg = [], []
        for d in np.unique(dates):
            m = dates == d
            A, C = B[m][:, _I], B[m][:, _J]
            V = (A - C) / (A + C) if kind == 'NDSI' else (A / C if kind == 'SR' else A - C)
            yy = y[m] - y[m].mean(); Vc = V - V.mean(0)
            r = (yy @ Vc) / np.sqrt((yy ** 2).sum() * (Vc ** 2).sum(0) + 1e-30)
            r2s.append(r ** 2); sg.append(np.sign(r))
        score = np.mean(r2s, 0) * (np.abs(np.sum(sg, 0)) == len(sg))
        used = set()
        for k in np.argsort(-score):
            i, j = _I[k], _J[k]
            if i in used or j in used:
                continue
            out.append((kind, i, j)); used |= {i, j}
            if len(used) == 2 * n:
                break
    return out


def index_feats(B, trip):
    cols, names = [], []
    for kind, i, j in trip:
        a, c = B[:, i], B[:, j]
        cols.append((a - c) / (a + c) if kind == 'NDSI' else (a / c if kind == 'SR' else a - c))
        names.append(f'{kind}({WL10[i]},{WL10[j]})')
    return pd.DataFrame(np.column_stack(cols), columns=names)


def inner_splits(Mtr, k=3, seed=0):
    a = cell_folds(plot_table(Mtr), k, seed)
    f = Mtr['plot'].map(a).to_numpy()
    return [(np.where(f != j)[0], np.where(f == j)[0]) for j in range(k)]


def combined(fam, tr, y, dates, B):
    N = index_feats(B, index_top(B[tr], y[tr], dates[tr]))
    return pd.concat([fam[f] for f in FAMS] + [N], axis=1)


def scenario_matrix(sc, tr, te, M, fam, inner, y, dates, seed):
    info = {}
    B = fam['REF'].to_numpy(float)
    if sc in FULL:
        F = fam[FULL[sc]]
        A = F.to_numpy(float)
        return A[tr], A[te], list(F.columns), info
    if sc == 'S8':
        N = index_feats(B, index_top(B[tr], y[tr], dates[tr])).to_numpy()
        names = list(index_feats(B[:2], index_top(B[tr], y[tr], dates[tr])).columns)
        return N[tr], N[te], names, info
    if sc in ('S11', 'S12'):
        if sc == 'S11':
            Z = (B - B[tr].mean(0)) / B[tr].std(0)
            cols, crit = spa(Z[tr], y[tr].astype(float), inner)
        else:
            cols, crit = ga_pls(B[tr], y[tr], inner, seed=seed)
        info['crit'] = crit
        return B[tr][:, cols], B[te][:, cols], [f'R{WL10[c]}' for c in cols], info
    F = fam['CWT'] if sc == 'S9' else combined(fam, tr, y, dates, B)
    A = F.to_numpy(float)
    sel, info = robust_select(A[tr], y[tr], dates[tr], inner, seed=seed)
    return A[tr][:, sel], A[te][:, sel], list(F.columns[sel]), info


def date_norm(Xtr, Xte, dtr, dte):
    """Per-date standardisation (Lv et al., 2023): every date is centred and scaled with all of its plots
    (labels not used), removing the date/growth-stage shift before the classifier."""
    A, B = Xtr.copy(), Xte.copy()
    for d in np.unique(np.r_[dtr, dte]):
        allv = np.vstack([Xtr[dtr == d], Xte[dte == d]])
        mu, sd = allv.mean(0), allv.std(0); sd[sd == 0] = 1
        A[dtr == d] = (Xtr[dtr == d] - mu) / sd; B[dte == d] = (Xte[dte == d] - mu) / sd
    return A, B


def run_job(rep, fold, assign, M, fam, scen, clfs, seed, dnorm=False):
    y = M['y'].to_numpy(); dates = M['date'].to_numpy()
    f = M['plot'].map(assign).to_numpy()
    tr, te = np.where(f != fold)[0], np.where(f == fold)[0]
    inner = inner_splits(M.iloc[tr].reset_index(drop=True), 3, seed)
    out = []
    for sc in scen:
        t0 = time.time()
        Xtr, Xte, names, info = scenario_matrix(sc, tr, te, M, fam, inner, y, dates, seed)
        if dnorm:
            Xtr, Xte = date_norm(Xtr, Xte, dates[tr], dates[te])
        tsel = time.time() - t0
        for c in clfs:
            p, s_in = tune(c, Xtr, y[tr], inner, seed)
            score, pred = fit_predict(c, p, Xtr, y[tr], Xte, seed)
            out.append(dict(rep=rep, fold=fold, scenario=sc, clf=c, te=te, score=score, pred=pred, params=p,
                            inner_BA=s_in, features=names, sel_info=info, t_sel=tsel))
    return out


def run(R, scen, clfs, branch='raw', dnorm=False, seed0=1000, njobs=4, M=None, fam=None):
    if M is None:
        M, fam = load_all(branch)
    P = plot_table(M)
    jobs = []
    for rep in range(R):
        a = cell_folds(P, 4, seed0 + rep)
        for fold in range(4):
            jobs.append((rep, fold, a))
    res = Parallel(n_jobs=njobs, verbose=2)(delayed(run_job)(r, f, a, M, fam, scen, clfs, seed0 + r, dnorm) for r, f, a in jobs)
    return [x for r in res for x in r]


if __name__ == '__main__':
    R = int(sys.argv[1]); tag = sys.argv[2]
    scen = sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] != 'all' else list(SCENARIOS)
    clfs = sys.argv[4].split(',') if len(sys.argv) > 4 and sys.argv[4] != 'all' else CLF_NAMES
    branch = sys.argv[5] if len(sys.argv) > 5 else 'raw'
    t = time.time()
    res = run(R, scen, clfs, branch, njobs=int(os.environ.get('NJOBS', 4)))
    pickle.dump(res, open(os.path.join(CACHE, f'cv_{tag}.pkl'), 'wb'))
    print('done', tag, len(res), 'rows', round(time.time() - t, 1), 's')
