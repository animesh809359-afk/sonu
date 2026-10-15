"""E7: Optimal feature combinations (OFCs) after Tian et al. (2021).
Disease-specific feature pool (top-5 % ReliefF on >= 3 of 4 dates, redundancy, VIF < 10) from all feature
families, then SFFS with three wrappers (LDA, kNN, SVM) -> OFC-LDA, OFC-kNN, OFC-SVM. Each OFC (and the
whole DSF pool, and the full spectrum) is classified with LDA, kNN and SVM inside nested plot-grouped CV."""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
import sys, time, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from models import *
from s04_cv import load_all, inner_splits, ndsi_top, nd_feats
from joblib import Parallel, delayed

B10, M, fam = load_all()
y = M['y'].to_numpy(); dates = M['date'].to_numpy(); pt = plot_table(M)
WRAPPERS = ['LDA', 'kNN', 'SVM']


def combined(tr_idx):
    pairs = ndsi_top(B10[tr_idx], y[tr_idx], dates[tr_idx])
    N = pd.DataFrame(nd_feats(B10, pairs), columns=[f'ND({WL10[i]},{WL10[j]})' for i, j in pairs])
    return pd.concat([fam['F1'], fam['F2'], N, fam['F4'], fam['F5'], fam['F6']], axis=1)


def job(rep, fold, assign):
    seed = 7000 + rep
    f = M['plot'].map(assign).to_numpy(); tr, te = np.where(f != fold)[0], np.where(f == fold)[0]
    inner = inner_splits(M.iloc[tr].reset_index(drop=True), 3, seed)
    F = combined(tr); A = F.to_numpy(float)
    pool, n_stable = dsf_pool(A[tr], y[tr], dates[tr], seed=seed)
    mu, sd = A[tr].mean(0), np.where(A[tr].std(0) > 0, A[tr].std(0), 1)
    Z = (A - mu) / sd
    sets = {'All DSFs': pool}
    info = {'n_stable': n_stable, 'n_pool': len(pool)}
    for w in WRAPPERS:
        sel, crit = sffs_wrapper(Z[tr][:, pool], y[tr], inner, w, seed=seed)
        sets[f'OFC-{w}'] = [pool[i] for i in sel]; info[f'crit_{w}'] = crit
    S = snv(B10)
    out = []
    for setname, cols in list(sets.items()) + [('Full spectrum (SNV)', None)]:
        Xtr, Xte = (S[tr], S[te]) if cols is None else (A[tr][:, cols], A[te][:, cols])
        for c in WRAPPERS:
            p, _ = tune(c, Xtr, y[tr], inner, seed)
            s, pr = fit_predict(c, p, Xtr, y[tr], Xte, seed)
            out.append(dict(rep=rep, fold=fold, feature_set=setname, clf=c, te=te, score=s, pred=pr,
                            features=[] if cols is None else list(F.columns[cols]), n_features=201 if cols is None else len(cols), info=info))
    return out


if __name__ == '__main__':
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    t = time.time()
    jobs = []
    for rep in range(R):
        a = plot_folds(pt, 4, 7000 + rep)
        for fold in range(4):
            jobs.append((rep, fold, a))
    res = Parallel(n_jobs=int(os.environ.get('NJOBS', 4)), verbose=5)(delayed(job)(*j) for j in jobs)
    res = [x for r in res for x in r]
    pickle.dump(res, open(os.path.join(CACHE, 'ofc.pkl'), 'wb'))
    # ---- summaries
    rows, sub = [], []
    for (fs, c, rep), g in pd.DataFrame(res).groupby(['feature_set', 'clf', 'rep'], sort=False):
        te = np.concatenate(g['te'].to_list()); pr = np.concatenate(g['pred'].to_list()); s = np.concatenate(g['score'].to_list())
        rows.append(dict(feature_set=fs, clf=c, rep=rep, median_n_features=float(np.median(g['n_features'])), **metrics(y[te], pr, s)))
        for dt in DATE_ORDER:
            m = dates[te] == dt
            sub.append(dict(feature_set=fs, clf=c, rep=rep, Date=DATE_LABEL[dt], **metrics(y[te][m], pr[m], s[m])))
    REP = pd.DataFrame(rows); REP.to_csv(os.path.join(TAB, 'E7_ofc_reps.csv'), index=False)
    pd.DataFrame(sub).groupby(['feature_set', 'clf', 'Date'], sort=False)[['BA', 'OA', 'MCC', 'Kappa']].mean().reset_index().to_csv(
        os.path.join(TAB, 'E7_ofc_by_date.csv'), index=False)
    # feature frequency per OFC
    fr = []
    for fs in ['All DSFs'] + [f'OFC-{w}' for w in WRAPPERS]:
        rr = [r for r in res if r['feature_set'] == fs and r['clf'] == 'LDA']
        cnt = pd.Series([x for r in rr for x in r['features']]).value_counts()
        for feat, n in cnt.items():
            fr.append(dict(feature_set=fs, Feature=feat, Frequency_pct=100 * n / len(rr)))
    pd.DataFrame(fr).to_csv(os.path.join(TAB, 'E7_ofc_feature_frequency.csv'), index=False)
    # ---- final OFCs on all data (feature tables as in Tian et al., 2021, Table 4)
    allidx = np.arange(len(M))
    inner_all = inner_splits(M, 4, 77)
    F = combined(allidx); A = F.to_numpy(float)
    pool, n_stable = dsf_pool(A, y, dates, seed=77)
    Z = (A - A.mean(0)) / np.where(A.std(0) > 0, A.std(0), 1)
    fin = [dict(Set='All DSFs', Rank=i + 1, Feature=F.columns[c]) for i, c in enumerate(pool)]
    for w in WRAPPERS:
        sel, crit = sffs_wrapper(Z[:, pool], y, inner_all, w, seed=77)
        fin += [dict(Set=f'OFC-{w}', Rank=i + 1, Feature=F.columns[pool[c]], Inner_CV_BA=crit) for i, c in enumerate(sel)]
    pd.DataFrame(fin).to_csv(os.path.join(TAB, 'E7_ofc_final_sets.csv'), index=False)
    print('E7 done', round(time.time() - t), 's')
