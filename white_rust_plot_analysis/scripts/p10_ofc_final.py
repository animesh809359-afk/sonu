"""E7 final sets: disease-sensitive features (DSFs) and optimal feature combinations (OFCs) fitted on all
192 plot-dates (Tian et al., 2021), with per-feature statistics and the CV accuracy of each set."""
import os, sys, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcommon import *
from p03_cv import load_all, combined, inner_splits
from models import dsf_pool, sffs_wrapper, relieff
from sklearn.metrics import roc_auc_score

M, fam = load_all('raw'); y = M['y'].to_numpy(); dates = M['date'].to_numpy()
F = combined(fam, np.arange(len(y)), y, dates, fam['REF'].to_numpy(float))
names = np.array(F.columns); A = F.to_numpy(float)
Z = (A - A.mean(0)) / np.where(A.std(0) > 0, A.std(0), 1)
pool, n_stable = dsf_pool(A, y, dates, seed=77)
inner = inner_splits(M, 4, 77)
sets = {'DSFs (all)': list(range(len(pool)))}
for w in ('LDA', 'kNN', 'SVM'):
    s, crit = sffs_wrapper(Z[:, pool], y, inner, w, seed=77)
    sets[f'OFC-{w}'] = s
W = np.zeros(A.shape[1])
for d in DATE_ORDER:
    m = dates == d; W += relieff(A[m], y[m], seed=77) / 4
rows = []
for j, p in enumerate(pool):
    v = A[:, p]; a, b = v[y == 1], v[y == 0]
    r = dict(Feature=names[p], ReliefF_weight=W[p], Healthy_mean=b.mean(), Diseased_mean=a.mean(), Direction='D > H' if a.mean() > b.mean() else 'D < H',
             Hedges_g=(a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2))
    for d in DATE_ORDER:
        m = dates == d; au = roc_auc_score(y[m], v[m]); r[f'AUC {DATE_LABEL[d]}'] = max(au, 1 - au)
    for k, s in sets.items():
        r[k] = 'yes' if j in s else ''
    rows.append(r)
T = pd.DataFrame(rows)
C = np.corrcoef(Z[:, pool].T); T['VIF'] = np.diag(np.linalg.pinv(C)) if len(pool) > 1 else 1.0
T.to_csv(os.path.join(TAB, 'E7_ofc_final_sets.csv'), index=False)
cv = pd.read_csv(os.path.join(TAB, 'E7_ofc_reps.csv')).groupby(['feature_set', 'clf'])[['BA', 'MCC', 'ROC_AUC', 'Sensitivity', 'Specificity']].mean().reset_index()
cv['feature_set'] = cv['feature_set'].replace({'All DSFs': 'DSFs (all)'})
summ = pd.DataFrame([dict(Set=k, Features=', '.join(names[pool][s]), n=len(s)) for k, s in sets.items()])
best = cv.loc[cv.groupby('feature_set')['BA'].idxmax()].rename(columns={'feature_set': 'Set', 'clf': 'Best classifier (CV)'})
summ = summ.merge(best, on='Set')
summ.to_csv(os.path.join(TAB, 'E7_ofc_final_summary.csv'), index=False)
R = pickle.load(open(os.path.join(CACHE, 'E7_ofc.pkl'), 'rb'))
fr = []
for fs in ['All DSFs', 'OFC-LDA', 'OFC-kNN', 'OFC-SVM']:
    rr = [r for r in R if r['feature_set'] == fs and r['clf'] == 'LDA']
    c = pd.Series([f for r in rr for f in r['features']]).value_counts()
    for f, n in c.items():
        fr.append(dict(Set=fs.replace('All DSFs', 'DSFs (all)'), Feature=f, Selected_pct=100 * n / len(rr)))
pd.DataFrame(fr).to_csv(os.path.join(TAB, 'E7_ofc_feature_frequency.csv'), index=False)
print('stable candidates', n_stable, 'pool', len(pool))
print(T.round(3).to_string()); print(summ.round(3).to_string())
