"""Multicollinearity diagnostics of the final selected feature sets: Pearson correlation matrix, variance
inflation factor (VIF = diagonal of the inverse correlation matrix) and condition number, plus the effect of the
redundancy + VIF < 10 filter on the candidate pool of the robust selection (all spectra, seed as in s06)."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from models import relieff, vif_filter
from s04_cv import load_all, ndsi_top, nd_feats

B10, M, fam = load_all()
y = M['y'].to_numpy(); dates = M['date'].to_numpy()
pairs = ndsi_top(B10, y, dates)
N = pd.DataFrame(nd_feats(B10, pairs), columns=[f'ND({WL10[i]},{WL10[j]})' for i, j in pairs])
F = pd.concat([fam['F1'], fam['F2'], N, fam['F4'], fam['F5'], fam['F6']], axis=1)


def diag(cols):
    X = F[cols].to_numpy(float)
    R = np.corrcoef(X.T)
    vif = np.diag(np.linalg.pinv(R))
    ev = np.linalg.eigvalsh(R)
    return R, vif, float(np.sqrt(ev.max() / max(ev.min(), 1e-12)))


sets = {}
sets['Robust S8 (final)'] = pd.read_csv(os.path.join(TAB, 'final_features.csv'))['Feature'].tolist()
O = pd.read_csv(os.path.join(TAB, 'E7_ofc_final_sets.csv'))
for s in ['OFC-SVM', 'OFC-kNN', 'OFC-LDA']:
    sets[s] = O[O['Set'] == s]['Feature'].tolist()
E = pd.read_csv(os.path.join(TAB, 'E8_fs_final_sets.csv'))
for m in ['SVM-RFE', 'ReliefF', 'LASSO', 'CARS', 'SFFS (QDA)', 'Consensus (Borda)']:
    sets[m + ' (top-10)'] = E[E['method'] == m].sort_values('rank')['Feature'].tolist()

summ, vif_rows = [], []
for name, cols in sets.items():
    cols = [c for c in cols if c in F.columns]
    R, vif, cn = diag(cols)
    off = np.abs(R[np.triu_indices(len(cols), 1)])
    summ.append(dict(Feature_set=name, n_features=len(cols), Max_abs_r=off.max(), Mean_abs_r=off.mean(),
                     Pairs_abs_r_ge_0_8=int((off >= 0.8).sum()), Max_VIF=vif.max(), Mean_VIF=vif.mean(),
                     n_VIF_gt_10=int((vif > 10).sum()), Condition_number=cn))
    for c, v in zip(cols, vif):
        vif_rows.append(dict(Feature_set=name, Feature=c, VIF=v, Tolerance=1 / v))
    if name == 'Robust S8 (final)':
        pd.DataFrame(R, index=cols, columns=cols).to_csv(os.path.join(TAB, 'collinearity_corr_S8.csv'))
    if name == 'SVM-RFE (top-10)':
        pd.DataFrame(R, index=cols, columns=cols).to_csv(os.path.join(TAB, 'collinearity_corr_SVMRFE.csv'))
pd.DataFrame(summ).to_csv(os.path.join(TAB, 'collinearity_summary.csv'), index=False)
pd.DataFrame(vif_rows).to_csv(os.path.join(TAB, 'collinearity_vif.csv'), index=False)

# ---- effect of the filter: candidate pool before / after redundancy + VIF (robust selection, all spectra)
A = F.to_numpy(float); nf = A.shape[1]; ntop = max(10, int(round(0.10 * nf)))
W_all, hits = np.zeros(nf), np.zeros(nf)
for d in np.unique(dates):
    m = dates == d; w = relieff(A[m], y[m], seed=77); W_all += w; hits[np.argsort(-w)[:ntop]] += 1
cand = np.where(hits >= 3)[0]; cand = cand[np.argsort(-W_all[cand])]
Z = (A - A.mean(0)) / np.where(A.std(0) > 0, A.std(0), 1)
stage = []
def stats_of(idx, label):
    R = np.corrcoef(Z[:, idx].T); v = np.diag(np.linalg.pinv(R)); off = np.abs(R[np.triu_indices(len(idx), 1)])
    ev = np.linalg.eigvalsh(R)
    stage.append(dict(Stage=label, n_features=len(idx), Max_abs_r=off.max(), Mean_abs_r=off.mean(), Max_VIF=v.max(),
                      Median_VIF=np.median(v), n_VIF_gt_10=int((v > 10).sum()), Condition_number=float(np.sqrt(ev.max() / max(ev.min(), 1e-12)))))
stats_of(list(cand[:40]), '1. Date-stable ReliefF candidates (top 40)')
pool = []
for c in cand:
    if all(abs(np.corrcoef(Z[:, c], Z[:, p])[0, 1]) < 0.98 for p in pool):
        pool.append(c)
    if len(pool) >= 40:
        break
stats_of(pool, '2. After redundancy filter (|r| < 0.98)')
keep = vif_filter(Z[:, pool]); post = [pool[i] for i in keep]
stats_of(post, '3. After VIF < 10')
stats_of([F.columns.get_loc(c) for c in sets['Robust S8 (final)']], '4. Final set after SFFS-LDA')
pd.DataFrame(stage).to_csv(os.path.join(TAB, 'collinearity_filter_stages.csv'), index=False)
print(pd.DataFrame(summ).round(2).to_string()); print(pd.DataFrame(stage).round(2).to_string())
