"""Step 2: QC (splice correction, trimming, noise, outliers) and preprocessing; Step 4: feature families."""
import numpy as np, pandas as pd, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from scipy import stats

X, wl, M = load_raw()
qc = {}
# splice steps before correction
i1000 = int(np.where(wl == 1000)[0][0]); i1800 = int(np.where(wl == 1800)[0][0])
step = lambda A, i: np.abs(A[:, i + 1] - (2 * A[:, i] - A[:, i - 1]))
qc['splice_1000_before'] = step(X, i1000).mean(); qc['splice_1800_before'] = step(X, i1800).mean()
Xs = splice_correct(X, wl)
qc['splice_1000_after'] = step(Xs, i1000).mean(); qc['splice_1800_after'] = step(Xs, i1800).mean()

# noise by region (high-frequency residual from a 9-nm moving average), raw data
resid = X - np.apply_along_axis(lambda s: np.convolve(s, np.ones(9) / 9, 'same'), 1, X)
noise = []
for lo, hi in [(350, 400), (400, 500), (500, 700), (700, 1000), (1000, 1350), (1350, 1450), (1450, 1800),
               (1800, 1950), (1950, 2350), (2350, 2400), (2400, 2500)]:
    m = (wl >= lo + 5) & (wl < hi - 5)
    mr = X[:, m].mean()
    noise.append(dict(Region_nm=f'{lo}-{hi}', Mean_reflectance=mr, HF_noise_SD=resid[:, m].std(),
                      SNR=mr / resid[:, m].std()))
noise = pd.DataFrame(noise)

Xt, wl1 = trim(Xs, wl)
X1 = sg(Xt)                                    # smoothed 1-nm reflectance 400-2400
B10 = resample10(X1, wl1)                      # 10-nm bands (201)
S10 = snv(B10)

# ---- outlier screening (label-free, consensus of 3 rules)
pca = PCA(5).fit(S10)
T = pca.transform(S10)
n, a = S10.shape[0], 5
T2 = ((T ** 2) / pca.explained_variance_).sum(1)
T2_lim = a * (n - 1) * (n + 1) / (n * (n - a)) * stats.f.ppf(0.99, a, n - a)
E = S10 - pca.inverse_transform(T)
Q = (E ** 2).sum(1)
ev = np.linalg.eigvalsh(np.cov(S10.T))[::-1][a:]
t1, t2, t3 = ev.sum(), (ev ** 2).sum(), (ev ** 3).sum()
h0 = 1 - 2 * t1 * t3 / (3 * t2 ** 2)
z = stats.norm.ppf(0.99)
Q_lim = t1 * (z * np.sqrt(2 * t2 * h0 ** 2) / t1 + 1 + t2 * h0 * (h0 - 1) / t1 ** 2) ** (1 / h0)
iso = IsolationForest(n_estimators=500, contamination=0.02, random_state=1).fit(S10)
iso_flag = iso.predict(S10) == -1
# spectral angle to plot-date median
sam = np.zeros(n)
for g, idx in M.groupby('plot_date').indices.items():
    med = np.median(B10[idx], 0)
    cos = (B10[idx] @ med) / (np.linalg.norm(B10[idx], axis=1) * np.linalg.norm(med))
    sam[idx] = np.degrees(np.arccos(np.clip(cos, -1, 1)))
sam_z = (sam - np.median(sam)) / (1.4826 * stats.median_abs_deviation(sam))
flags = np.c_[T2 > T2_lim, Q > Q_lim, iso_flag, sam_z > 3.5]
votes = flags.sum(1)
outlier = votes >= 3
OUT = M[['spec_uid', 'date', 'plot', 'variety', 'stage', 'label']].copy()
OUT['T2'] = T2; OUT['T2_flag'] = flags[:, 0]; OUT['Q'] = Q; OUT['Q_flag'] = flags[:, 1]
OUT['IsoForest_flag'] = flags[:, 2]; OUT['SAM_deg'] = sam; OUT['SAM_robust_z'] = sam_z; OUT['SAM_flag'] = flags[:, 3]
OUT['votes'] = votes; OUT['removed'] = outlier
qc.update(T2_limit=T2_lim, Q_limit=Q_lim, n_T2=int(flags[:, 0].sum()), n_Q=int(flags[:, 1].sum()),
          n_iso=int(flags[:, 2].sum()), n_sam=int(flags[:, 3].sum()), n_removed=int(outlier.sum()))
print(qc)
print(OUT.loc[outlier].groupby(['label']).size())

keep = ~outlier
M2 = M.loc[keep].reset_index(drop=True)
np.savez_compressed(os.path.join(CACHE, 'clean.npz'), X1=X1[keep], wl1=wl1, B10=B10[keep], X_raw_trim=Xt[keep])
M2.to_csv(os.path.join(CACHE, 'meta_clean.csv'), index=False)
OUT.to_csv(os.path.join(TAB, 'qc_outliers.csv'), index=False)
noise.to_csv(os.path.join(TAB, 'qc_noise.csv'), index=False)
pd.Series(qc).to_csv(os.path.join(TAB, 'qc_summary.csv'))

# ---- feature families
t = time.time()
VI, cite = vegetation_indices(X1[keep], wl1)
DER = derivative_features(X1[keep], wl1)
CR = continuum_features(X1[keep], wl1)
CW = cwt_features(X1[keep], wl1)
BANDS = pd.DataFrame(snv(B10[keep]), columns=[f'R{w}' for w in WL10])  # F1 = SNV-corrected 10-nm bands
print('features', VI.shape, DER.shape, CR.shape, CW.shape, time.time() - t)
for nm, df in [('F1_bands', BANDS), ('F2_VI', VI), ('F4_deriv', DER), ('F5_CR', CR), ('F6_CWT', CW)]:
    df.to_parquet(os.path.join(CACHE, nm + '.parquet')) if False else df.to_pickle(os.path.join(CACHE, nm + '.pkl'))
pd.DataFrame([(k, v[0], v[1]) for k, v in cite.items()], columns=['Index', 'Reference', 'Trait']).to_csv(
    os.path.join(TAB, 'vi_definitions.csv'), index=False)
print('nan/inf', {nm: int((~np.isfinite(df.to_numpy())).sum()) for nm, df in [('VI', VI), ('DER', DER), ('CR', CR), ('CW', CW)]})
