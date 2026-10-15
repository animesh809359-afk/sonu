"""Supplementary experiments E1-E6 (all plot-grouped, all learning steps inside training data).
E1 preprocessing comparison | E2 transfer to unseen date / variety / stage | E3 spectra vs spectra+metadata
E4 learning curve | E5 simulated multispectral sensors | E6 outlier-removal sensitivity"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
import sys, time, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from models import *
from s04_cv import load_all, scenario_matrix, inner_splits
from joblib import Parallel, delayed

B10, M, fam = load_all()
d = np.load(os.path.join(CACHE, 'clean.npz')); X1, wl1 = d['X1'], d['wl1']
y = M['y'].to_numpy(); dates = M['date'].to_numpy(); pt = plot_table(M)
FD10 = resample10(sg(X1, 11, 2, deriv=1), wl1)
NJ = int(os.environ.get('NJOBS', 4))
EXP = sys.argv[1].split(',') if len(sys.argv) > 1 else ['E1', 'E2', 'E3', 'E4', 'E5', 'E6']
BEST = [('S1', 'LR'), ('S7', 'SVM'), ('S8', 'SVM')]   # pipelines carried into transfer experiments


def evaluate(tr, te, sc, c, seed, Mloc=M, B=B10, famloc=fam, extra=None):
    yl = Mloc['y'].to_numpy(); dl = Mloc['date'].to_numpy()
    inner = inner_splits(Mloc.iloc[tr].reset_index(drop=True), 3, seed)
    Xtr, Xte, names, info = scenario_matrix(sc, tr, te, B, Mloc, famloc, inner, yl, dl, seed)
    if extra is not None:
        Xtr, Xte = np.c_[Xtr, extra[tr]], np.c_[Xte, extra[te]]
    p, _ = tune(c, Xtr, yl[tr], inner, seed)
    s, pr = fit_predict(c, p, Xtr, yl[tr], Xte, seed)
    return s, pr, names


# ---------------------------------------------------------------- E1 preprocessing
def e1_job(rep, fold, assign, variant, c):
    f = M['plot'].map(assign).to_numpy(); tr, te = np.where(f != fold)[0], np.where(f == fold)[0]
    if variant == 'Reflectance (SG)':
        A = B10
    elif variant == 'SNV':
        A = snv(B10)
    elif variant == 'MSC':
        m = MSC().fit(B10[tr]); A = m.transform(B10)
    elif variant == 'First derivative (SG)':
        A = FD10
    elif variant == 'Date normalisation':
        A = DateNorm().fit(B10[tr], dates[tr], y[tr]).transform(B10, dates)
    elif variant == 'Date normalisation + SNV':
        A = snv(DateNorm().fit(B10[tr], dates[tr], y[tr]).transform(B10, dates))
    inner = inner_splits(M.iloc[tr].reset_index(drop=True), 3, 1000 + rep)
    p, _ = tune(c, A[tr], y[tr], inner, 1000 + rep)
    s, pr = fit_predict(c, p, A[tr], y[tr], A[te], 1000 + rep)
    return dict(rep=rep, variant=variant, clf=c, te=te, score=s, pred=pr)


VARIANTS = ['Reflectance (SG)', 'SNV', 'MSC', 'First derivative (SG)', 'Date normalisation', 'Date normalisation + SNV']
if 'E1' in EXP:
    t = time.time(); jobs = []
    for rep in range(10):
        a = plot_folds(pt, 4, 1000 + rep)
        for fold in range(4):
            for v in VARIANTS:
                for c in ['LDA', 'PLS-DA', 'LR', 'SVM']:
                    jobs.append((rep, fold, a, v, c))
    res = Parallel(n_jobs=NJ)(delayed(e1_job)(*j) for j in jobs)
    rows = []
    for (v, c, rep), g in pd.DataFrame(res).groupby(['variant', 'clf', 'rep']):
        te = np.concatenate(g['te'].to_list()); pr = np.concatenate(g['pred'].to_list()); s = np.concatenate(g['score'].to_list())
        rows.append(dict(variant=v, clf=c, rep=rep, **metrics(y[te], pr, s)))
    pd.DataFrame(rows).to_csv(os.path.join(TAB, 'E1_preprocessing_reps.csv'), index=False)
    print('E1', time.time() - t)


# ---------------------------------------------------------------- E2 transfer
def e2_job(kind, level, rep, fold, assign, sc, c):
    f = M['plot'].map(assign).to_numpy() if assign is not None else None
    col = {'Date': 'date', 'Stage': 'stage', 'Variety': 'variety'}[kind]
    lev = M[col].to_numpy() == level
    if kind == 'Variety':
        tr, te = np.where(~lev)[0], np.where(lev)[0]
    else:
        tr = np.where((~lev) & (f != fold))[0]; te = np.where(lev & (f == fold))[0]
    s, pr, names = evaluate(tr, te, sc, c, 2000 + rep)
    return dict(kind=kind, level=level, rep=rep, fold=fold, scenario=sc, clf=c, te=te, score=s, pred=pr)


if 'E2' in EXP:
    t = time.time(); jobs = []
    for sc, c in BEST:
        for rep in range(3):
            a = plot_folds(pt, 4, 2000 + rep)
            for fold in range(4):
                for dt in DATE_ORDER:
                    jobs.append(('Date', dt, rep, fold, a, sc, c))
                for st in STAGE_ORDER:
                    jobs.append(('Stage', st, rep, fold, a, sc, c))
        for v in VARIETIES:
            jobs.append(('Variety', v, 0, 0, None, sc, c))
    res = Parallel(n_jobs=NJ)(delayed(e2_job)(*j) for j in jobs)
    rows = []
    for (k, lv, sc, c, rep), g in pd.DataFrame(res).groupby(['kind', 'level', 'scenario', 'clf', 'rep']):
        te = np.concatenate(g['te'].to_list()); pr = np.concatenate(g['pred'].to_list()); s = np.concatenate(g['score'].to_list())
        rows.append(dict(kind=k, level=lv, scenario=sc, clf=c, rep=rep, n_test=len(te), **metrics(y[te], pr, s)))
    pd.DataFrame(rows).to_csv(os.path.join(TAB, 'E2_transfer_reps.csv'), index=False)
    print('E2', time.time() - t)


# ---------------------------------------------------------------- E3 metadata
META = pd.get_dummies(M[['date', 'variety', 'stage']].astype(str)).to_numpy(float)
def e3_job(rep, fold, assign, sc, c, use_meta):
    f = M['plot'].map(assign).to_numpy(); tr, te = np.where(f != fold)[0], np.where(f == fold)[0]
    s, pr, _ = evaluate(tr, te, sc, c, 3000 + rep, extra=META if use_meta else None)
    return dict(rep=rep, scenario=sc, clf=c, meta=use_meta, te=te, score=s, pred=pr)


if 'E3' in EXP:
    t = time.time(); jobs = []
    for rep in range(5):
        a = plot_folds(pt, 4, 3000 + rep)
        for fold in range(4):
            for sc, c in BEST:
                for um in (False, True):
                    jobs.append((rep, fold, a, sc, c, um))
    res = Parallel(n_jobs=NJ)(delayed(e3_job)(*j) for j in jobs)
    rows = []
    for (sc, c, um, rep), g in pd.DataFrame(res).groupby(['scenario', 'clf', 'meta', 'rep']):
        te = np.concatenate(g['te'].to_list()); pr = np.concatenate(g['pred'].to_list()); s = np.concatenate(g['score'].to_list())
        rows.append(dict(scenario=sc, clf=c, inputs='Spectra + metadata' if um else 'Spectra only', rep=rep, **metrics(y[te], pr, s)))
    pd.DataFrame(rows).to_csv(os.path.join(TAB, 'E3_metadata_reps.csv'), index=False)
    print('E3', time.time() - t)


# ---------------------------------------------------------------- E4 learning curve
def e4_job(rep, fold, assign, sc, c, n_h):
    f = M['plot'].map(assign).to_numpy()
    rng = np.random.default_rng(4000 + rep * 10 + fold)
    trp = pt[pt['plot'].map(assign) != fold]
    keep = []
    for (v, yy), g in trp.groupby(['variety', 'y']):
        k = n_h if yy == 0 else 3 * n_h
        keep += list(rng.choice(g['plot'].to_numpy(), k, replace=False))
    tr = np.where(M['plot'].isin(keep).to_numpy())[0]; te = np.where(f == fold)[0]
    s, pr, _ = evaluate(tr, te, sc, c, 4000 + rep)
    return dict(rep=rep, scenario=sc, clf=c, n_train_plots=4 * n_h * 3, te=te, score=s, pred=pr)


if 'E4' in EXP:
    t = time.time(); jobs = []
    for rep in range(5):
        a = plot_folds(pt, 4, 4000 + rep)
        for fold in range(4):
            for sc, c in [('S1', 'LR'), ('S8', 'SVM')]:
                for n_h in (1, 2, 3):
                    jobs.append((rep, fold, a, sc, c, n_h))
    res = Parallel(n_jobs=NJ)(delayed(e4_job)(*j) for j in jobs)
    rows = []
    for (sc, c, n, rep), g in pd.DataFrame(res).groupby(['scenario', 'clf', 'n_train_plots', 'rep']):
        te = np.concatenate(g['te'].to_list()); pr = np.concatenate(g['pred'].to_list()); s = np.concatenate(g['score'].to_list())
        rows.append(dict(scenario=sc, clf=c, n_train_plots=n, rep=rep, **metrics(y[te], pr, s)))
    pd.DataFrame(rows).to_csv(os.path.join(TAB, 'E4_learning_curve_reps.csv'), index=False)
    print('E4', time.time() - t)


# ---------------------------------------------------------------- E5 simulated sensors
SENSORS = {
    'Sentinel-2 MSI (10 bands)': {'B2': (458, 523), 'B3': (543, 578), 'B4': (650, 680), 'B5': (698, 713), 'B6': (733, 748),
                                  'B7': (773, 793), 'B8': (785, 900), 'B8A': (855, 875), 'B11': (1565, 1655), 'B12': (2100, 2280)},
    'UAV multispectral (5 bands)': {'Blue': (434, 466), 'Green': (544, 576), 'Red': (634, 666), 'RedEdge': (714, 746), 'NIR': (814, 866)},
}
def sensor_matrix(name):
    bands = SENSORS[name]
    Bk = {k: X1[:, (wl1 >= a) & (wl1 <= b)].mean(1) for k, (a, b) in bands.items()}
    df = pd.DataFrame(Bk)
    if 'NIR' in Bk:
        nir, red, re, gr = Bk['NIR'], Bk['Red'], Bk['RedEdge'], Bk['Green']
    else:
        nir, red, re, gr = Bk['B8'], Bk['B4'], Bk['B5'], Bk['B3']
    df['NDVI'] = (nir - red) / (nir + red); df['NDRE'] = (nir - re) / (nir + re); df['GNDVI'] = (nir - gr) / (nir + gr)
    if 'B11' in Bk:
        df['NDII'] = (Bk['B8A'] - Bk['B11']) / (Bk['B8A'] + Bk['B11'])
    return df.to_numpy(float)


def e5_job(rep, fold, assign, sname, c):
    f = M['plot'].map(assign).to_numpy(); tr, te = np.where(f != fold)[0], np.where(f == fold)[0]
    A = sensor_matrix(sname)
    inner = inner_splits(M.iloc[tr].reset_index(drop=True), 3, 5000 + rep)
    p, _ = tune(c, A[tr], y[tr], inner, 5000 + rep)
    s, pr = fit_predict(c, p, A[tr], y[tr], A[te], 5000 + rep)
    return dict(rep=rep, sensor=sname, clf=c, te=te, score=s, pred=pr)


if 'E5' in EXP:
    t = time.time(); jobs = []
    for rep in range(10):
        a = plot_folds(pt, 4, 5000 + rep)
        for fold in range(4):
            for sname in SENSORS:
                for c in ['LR', 'SVM', 'RF']:
                    jobs.append((rep, fold, a, sname, c))
    res = Parallel(n_jobs=NJ)(delayed(e5_job)(*j) for j in jobs)
    rows = []
    for (sn, c, rep), g in pd.DataFrame(res).groupby(['sensor', 'clf', 'rep']):
        te = np.concatenate(g['te'].to_list()); pr = np.concatenate(g['pred'].to_list()); s = np.concatenate(g['score'].to_list())
        rows.append(dict(sensor=sn, clf=c, rep=rep, **metrics(y[te], pr, s)))
    pd.DataFrame(rows).to_csv(os.path.join(TAB, 'E5_sensor_reps.csv'), index=False)
    print('E5', time.time() - t)


# ---------------------------------------------------------------- E6 outlier-removal sensitivity (all 2339 spectra)
if 'E6' in EXP:
    t = time.time()
    Xr, wl, Mall = load_raw()
    Xt, wlt = trim(splice_correct(Xr, wl), wl)
    X1a = sg(Xt); B10a = resample10(X1a, wlt)
    VIa, _ = vegetation_indices(X1a, wlt)
    fam_a = {'F1': pd.DataFrame(snv(B10a), columns=[f'R{w}' for w in WL10]), 'F2': VIa,
             'F4': derivative_features(X1a, wlt), 'F5': continuum_features(X1a, wlt), 'F6': cwt_features(X1a, wlt)}
    pta = plot_table(Mall); ya = Mall['y'].to_numpy()
    def e6_job(rep, fold, assign, sc, c):
        f = Mall['plot'].map(assign).to_numpy(); tr, te = np.where(f != fold)[0], np.where(f == fold)[0]
        s, pr, _ = evaluate(tr, te, sc, c, 6000 + rep, Mloc=Mall, B=B10a, famloc=fam_a)
        return dict(rep=rep, scenario=sc, clf=c, te=te, score=s, pred=pr)
    jobs = []
    for rep in range(5):
        a = plot_folds(pta, 4, 6000 + rep)
        for fold in range(4):
            for sc, c in BEST:
                jobs.append((rep, fold, a, sc, c))
    res = Parallel(n_jobs=NJ)(delayed(e6_job)(*j) for j in jobs)
    rows = []
    for (sc, c, rep), g in pd.DataFrame(res).groupby(['scenario', 'clf', 'rep']):
        te = np.concatenate(g['te'].to_list()); pr = np.concatenate(g['pred'].to_list()); s = np.concatenate(g['score'].to_list())
        rows.append(dict(scenario=sc, clf=c, data='All spectra (no outlier removal)', rep=rep, **metrics(ya[te], pr, s)))
    pd.DataFrame(rows).to_csv(os.path.join(TAB, 'E6_outlier_sensitivity_reps.csv'), index=False)
    print('E6', time.time() - t)
