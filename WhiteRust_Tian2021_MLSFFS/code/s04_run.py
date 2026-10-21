"""A: paper-faithful ML-SFFS (OA criterion, 4-fold CV x N repetitions);
B: corrected nested CV (whole DSSF pipeline inside the outer folds, BA criterion, balanced classifiers);
C: permutation null of procedure A (labels of the plots permuted, whole pipeline repeated)."""
import sys, pickle, time, numpy as np, pandas as pd
from joblib import Parallel, delayed
sys.path.insert(0, '.')
from mlsffs import *

feats, y, _ = pickle.load(open(sys.argv[1], 'rb'))
P = pickle.load(open(sys.argv[2], 'rb'))
OUT = sys.argv[3]
mode = sys.argv[4]
NREP = int(sys.argv[5])
CLFS = ['LDA', 'kNN', 'SVM']
import warnings; warnings.filterwarnings('ignore')
PERM_CLFS = sys.argv[7].split(',') if len(sys.argv) > 7 else CLFS
plots = np.array(feats[DATES[0]]['R'].index)


def faithful_rep(d, clf, rep, pool, yd):
    X = date_matrix(feats, d, pool).values
    folds = [strat_folds(yd, 4, rep)]
    r = sffs(X, yd, folds, clf, 'OA', False, 8)
    allm = evaluate_subset(X, yd, folds, clf, 'OA', False)
    return dict(date=d, clf=clf, rep=rep, ofc=tuple(pool[i] for i in r['subset']), k=len(r['subset']),
                OA=r['metrics']['OA'], BA=r['metrics']['BA'], kappa=r['metrics']['kappa'],
                sens=r['metrics']['sens'], spec=r['metrics']['spec'], params=r['params'],
                all_OA=allm[2]['OA'], all_BA=allm[2]['BA'], all_kappa=allm[2]['kappa'], all_params=allm[1],
                path={k: (v[0], tuple(pool[i] for i in v[1])) for k, v in r['path'].items()})


def nested_fold(rep, fold, tr_idx, te_idx):
    tr, te = plots[tr_idx], plots[te_idx]
    Pf = build_pool(feats, y, plots=list(tr))
    pool = Pf['pool']
    res = []
    for d in DATES:
        yd = y[d]
        Xtr = date_matrix(feats, d, pool, list(tr)).values
        Xte = date_matrix(feats, d, pool, list(te)).values
        ytr, yte = yd[tr_idx], yd[te_idx]
        inner = [strat_folds(ytr, 4, 100 * rep + 10 * fold + s) for s in range(3)]
        for clf in CLFS:
            r = sffs(Xtr, ytr, inner, clf, 'BA', True, 8)
            sub = r['subset']
            C, g = r['params']
            a, b = (lambda m, s: ((Xtr[:, sub] - m) / s, (Xte[:, sub] - m) / s))(Xtr[:, sub].mean(0), np.where(Xtr[:, sub].std(0) == 0, 1, Xtr[:, sub].std(0)))
            pred = make_clf(clf, True, C, g, len(sub)).fit(a, ytr).predict(b)
            ra = evaluate_subset(Xtr, ytr, inner, clf, 'BA', True)
            C2, g2 = ra[1]
            a2, b2 = (Xtr - Xtr.mean(0)) / Xtr.std(0), (Xte - Xtr.mean(0)) / Xtr.std(0)
            pred_all = make_clf(clf, True, C2, g2, Xtr.shape[1]).fit(a2, ytr).predict(b2)
            res.append(dict(rep=rep, fold=fold, date=d, clf=clf, plots=list(te), y=list(yte), pred=list(pred),
                            pred_all=list(pred_all), ofc=tuple(pool[i] for i in sub), inner_BA=r['score'],
                            params=r['params'], pool=tuple(pool)))
    return res


def perm_run(p):
    rng = np.random.default_rng(5000 + p)
    perm = rng.permutation(len(plots))
    yp = {d: y[d][perm] for d in DATES}
    Pp = build_pool(feats, yp)
    out = []
    for d in DATES:
        for clf in PERM_CLFS:
            for rep in range(NREP):
                X = date_matrix(feats, d, Pp['pool']).values
                r = sffs(X, yp[d], [strat_folds(yp[d], 4, rep)], clf, 'OA', False, 8)
                out.append(dict(perm=p, date=d, clf=clf, rep=rep, OA=r['metrics']['OA'], BA=r['metrics']['BA'],
                                k=len(r['subset']), pool_size=len(Pp['pool'])))
    return out


t = time.time()
if mode == 'faithful':
    tasks = [(d, clf, rep) for d in DATES for clf in CLFS for rep in range(NREP)]
    tasks.sort(key=lambda x: x[1] != 'SVM')          # long SVM tasks first
    res = Parallel(n_jobs=4, verbose=0)(delayed(faithful_rep)(d, c, r, P['pool'], y[d]) for d, c, r in tasks)
elif mode == 'nested':
    yp = y[DATES[0]]
    tasks = [(r, k, tr, te) for r in range(NREP) for k, (tr, te) in enumerate(strat_folds(yp, 4, 1000 + r))]
    res = sum(Parallel(n_jobs=4, verbose=0)(delayed(nested_fold)(*t_) for t_ in tasks), [])
elif mode == 'perm':
    NPERM = int(sys.argv[6])
    P0 = int(sys.argv[8]) if len(sys.argv) > 8 else 0
    res = sum(Parallel(n_jobs=4, verbose=0)(delayed(perm_run)(p) for p in range(P0, P0 + NPERM)), [])
pickle.dump(res, open(OUT, 'wb'))
print(mode, 'done', round(time.time() - t), 's', len(res))
