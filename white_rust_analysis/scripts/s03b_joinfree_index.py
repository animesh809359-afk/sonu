"""Join-free alternative to the MWRI: best normalised-difference pair with both bands >= 30 nm from the
ASD detector joins (1000, 1800 nm), as a robustness check of the index (cf. detector-join check in the
researcher's feature-selection workbook)."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from sklearn.metrics import roc_auc_score
d = np.load(os.path.join(CACHE, 'clean.npz')); B10 = d['B10']
M = pd.read_csv(os.path.join(CACHE, 'meta_clean.csv')); y = M['y'].to_numpy()
mat = np.load(os.path.join(CACHE, 'ndsi_matrix.npy'))
ok = np.array([all(abs(w - j) >= 30 for j in (1000, 1800)) for w in WL10])
I, J = np.triu_indices(len(WL10), 1)
sc = mat[I, J] * ok[I] * ok[J]
rows = []
for k in np.argsort(-sc)[:10]:
    i, j = I[k], J[k]
    nd = (B10[:, i] - B10[:, j]) / (B10[:, i] + B10[:, j])
    auc = roc_auc_score(y, nd)
    rows.append(dict(Band_i_nm=WL10[i], Band_j_nm=WL10[j], Formula=f'(R{WL10[i]} - R{WL10[j]})/(R{WL10[i]} + R{WL10[j]})',
                     Mean_abs_d_across_dates=sc[k], AUC=max(auc, 1 - auc)))
pd.DataFrame(rows).to_csv(os.path.join(TAB, 'ndsi_top_pairs_joinfree.csv'), index=False)
print(pd.DataFrame(rows).round(3).to_string())
