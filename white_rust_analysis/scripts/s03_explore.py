"""Step 3: spectral characterisation, band-wise statistics, red-edge parameters, separability,
PCA / t-SNE, PERMANOVA variance partitioning, mixed models, NDSI map, CWT sensitivity."""
import numpy as np, pandas as pd, os, sys, warnings
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from scipy import stats
from statsmodels.stats.multitest import multipletests
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import statsmodels.formula.api as smf
warnings.filterwarnings('ignore')

d = np.load(os.path.join(CACHE, 'clean.npz')); X1, wl1, B10 = d['X1'], d['wl1'], d['B10']
M = pd.read_csv(os.path.join(CACHE, 'meta_clean.csv'))
y = M['y'].to_numpy(); dates = M['date'].to_numpy()
FD10 = resample10(sg(X1, 11, 2, deriv=1), wl1)
SD10 = resample10(sg(X1, 15, 3, deriv=2), wl1)

# ---- mean spectra (spectrum level) overall / per date / variety / stage
rows = {'Wavelength_nm': WL10}
for lab, v in [('Healthy', 0), ('Diseased', 1)]:
    rows[f'{lab}_mean'] = B10[y == v].mean(0); rows[f'{lab}_SD'] = B10[y == v].std(0)
rows['Difference_D-H'] = rows['Diseased_mean'] - rows['Healthy_mean']
rows['Ratio_D/H'] = rows['Diseased_mean'] / rows['Healthy_mean']
for lab, v in [('Healthy', 0), ('Diseased', 1)]:
    rows[f'FD_{lab}'] = FD10[y == v].mean(0)
    rows[f'SD2_{lab}'] = SD10[y == v].mean(0)
pd.DataFrame(rows).to_csv(os.path.join(TAB, 'spectra_mean_class.csv'), index=False)
for fac, order in [('date', DATE_ORDER), ('variety', VARIETIES), ('stage', STAGE_ORDER)]:
    out = {'Wavelength_nm': WL10}
    for lev in order:
        for lab, v in [('H', 0), ('D', 1)]:
            m = (M[fac] == lev).to_numpy() & (y == v)
            name = DATE_LABEL.get(lev, lev)
            out[f'{name}_{lab}'] = B10[m].mean(0)
        out[f'{name}_Diff'] = out[f'{name}_D'] - out[f'{name}_H']
    pd.DataFrame(out).to_csv(os.path.join(TAB, f'spectra_mean_by_{fac}.csv'), index=False)

# ---- band-wise statistics on plot-date means (independent-ish units, n = 192)
grp = M.groupby('plot_date').indices
keys = list(grp)
PDm = np.vstack([B10[grp[k]].mean(0) for k in keys])
PDfd = np.vstack([FD10[grp[k]].mean(0) for k in keys])
PDmeta = M.groupby('plot_date').first().loc[keys].reset_index()
ypd = PDmeta['y'].to_numpy()
def bandstats(A, yy):
    a, b = A[yy == 1], A[yy == 0]
    t, p = stats.ttest_ind(a, b, equal_var=False)
    u, pu = stats.mannwhitneyu(a, b, axis=0)
    sp = np.sqrt((a.var(0, ddof=1) * (len(a) - 1) + b.var(0, ddof=1) * (len(b) - 1)) / (len(a) + len(b) - 2))
    dco = (a.mean(0) - b.mean(0)) / sp
    q = multipletests(p, method='fdr_bh')[1]
    r = np.array([stats.pointbiserialr(yy, A[:, j])[0] for j in range(A.shape[1])])
    return t, p, q, pu, dco, r
t, p, q, pu, dco, r = bandstats(PDm, ypd)
tf, pf, qf, puf, dcof, rf = bandstats(PDfd, ypd)
# spectrum-level correlation (as in Mandal et al., 2022) for comparison
r_spec = np.array([stats.pointbiserialr(y, B10[:, j])[0] for j in range(B10.shape[1])])
# univariate Jeffries-Matusita distance per band (spectrum level, Gaussian)
def jm1(a, b):
    m1, m2, v1, v2 = a.mean(0), b.mean(0), a.var(0), b.var(0)
    B = 0.125 * (m1 - m2) ** 2 * 2 / (v1 + v2) + 0.5 * np.log(((v1 + v2) / 2) / np.sqrt(v1 * v2))
    return 2 * (1 - np.exp(-B))
jm = jm1(B10[y == 1], B10[y == 0]); jmf = jm1(FD10[y == 1], FD10[y == 0])
BS = pd.DataFrame({'Wavelength_nm': WL10, 'Welch_t': t, 'p_value': p, 'q_FDR': q, 'MannWhitney_p': pu,
                   'Cohen_d': dco, 'Point_biserial_r_plotdate': r, 'Point_biserial_r_spectrum': r_spec,
                   'JM_distance': jm, 'FD_Cohen_d': dcof, 'FD_q_FDR': qf, 'FD_r_plotdate': rf, 'FD_JM': jmf,
                   'neglog10_q': -np.log10(q), 'Significant_FDR_0.05': q < 0.05})
BS.to_csv(os.path.join(TAB, 'bandwise_statistics.csv'), index=False)
# band-wise effect size per date (stability)
eff = {'Wavelength_nm': WL10}
for dt in DATE_ORDER:
    m = (PDmeta['date'] == dt).to_numpy()
    eff[DATE_LABEL[dt]] = bandstats(PDm[m], ypd[m])[4]
pd.DataFrame(eff).to_csv(os.path.join(TAB, 'bandwise_cohen_d_by_date.csv'), index=False)

# sensitive regions table
sig = BS['q_FDR'] < 0.05
regions = []
cur = None
for w, s, dd in zip(WL10, sig, dco):
    sgn = np.sign(dd)
    if s and cur and cur['sign'] == sgn and w - cur['end'] == 10:
        cur['end'] = w; cur['d'].append(dd)
    else:
        if cur: regions.append(cur)
        cur = dict(start=w, end=w, sign=sgn, d=[dd]) if s else None
if cur: regions.append(cur)
RG = pd.DataFrame([dict(Region_nm=f"{g['start']}-{g['end']}", Width_nm=g['end'] - g['start'] + 10,
                        Direction='Diseased > Healthy' if g['sign'] > 0 else 'Diseased < Healthy',
                        Max_abs_Cohen_d=np.max(np.abs(g['d'])),
                        Peak_wavelength_nm=g['start'] + 10 * int(np.argmax(np.abs(g['d'])))) for g in regions])
RG.to_csv(os.path.join(TAB, 'sensitive_regions.csv'), index=False)

# ---- red-edge and edge parameters by class x date (plot-date means), Welch tests
VI = pd.read_pickle(os.path.join(CACHE, 'F2_VI.pkl')); DER = pd.read_pickle(os.path.join(CACHE, 'F4_deriv.pkl'))
edge = pd.concat([VI[['REP_LI', 'REP_FD', 'REV']], DER[['Sum_Dr2_680-780', 'Db', 'lambda_b', 'SDb', 'Dy', 'lambda_y', 'SDy', 'Dr', 'lambda_r', 'SDr']]], axis=1)
edge['plot_date'] = M['plot_date']; edge_pd = edge.groupby('plot_date').mean().loc[keys]
er = []
for col in edge_pd.columns:
    for dt in ['All'] + DATE_ORDER:
        m = np.ones(len(keys), bool) if dt == 'All' else (PDmeta['date'] == dt).to_numpy()
        a, b = edge_pd[col].to_numpy()[m & (ypd == 1)], edge_pd[col].to_numpy()[m & (ypd == 0)]
        er.append(dict(Parameter=col, Date=DATE_LABEL.get(dt, dt), Healthy_mean=b.mean(), Healthy_SD=b.std(ddof=1),
                       Diseased_mean=a.mean(), Diseased_SD=a.std(ddof=1), Welch_p=stats.ttest_ind(a, b, equal_var=False)[1]))
pd.DataFrame(er).to_csv(os.path.join(TAB, 'red_edge_parameters.csv'), index=False)

# ---- PCA (SNV 10-nm) and t-SNE
S10 = snv(B10)
pca = PCA(10).fit(S10); T = pca.transform(S10)
pd.DataFrame({'PC': [f'PC{i+1}' for i in range(10)], 'Explained_variance_pct': 100 * pca.explained_variance_ratio_,
              'Cumulative_pct': 100 * np.cumsum(pca.explained_variance_ratio_)}).to_csv(os.path.join(TAB, 'pca_variance.csv'), index=False)
pd.DataFrame({'Wavelength_nm': WL10, **{f'PC{i+1}_loading': pca.components_[i] for i in range(4)}}).to_csv(os.path.join(TAB, 'pca_loadings.csv'), index=False)
sc = M[['spec_uid', 'date', 'plot', 'variety', 'stage', 'label', 'plot_date']].copy()
for i in range(4): sc[f'PC{i+1}'] = T[:, i]
ts = TSNE(2, perplexity=40, random_state=7, init='pca').fit_transform(S10)
sc['tSNE1'], sc['tSNE2'] = ts[:, 0], ts[:, 1]
sc.to_csv(os.path.join(TAB, 'pca_tsne_scores.csv'), index=False)
# PC scores vs factors (eta^2) for first 5 PCs
eta = []
for i in range(5):
    for fac in ['label', 'date', 'variety', 'stage', 'plot']:
        g = pd.Series(T[:, i]).groupby(M[fac].to_numpy())
        ssb = (g.size() * (g.mean() - T[:, i].mean()) ** 2).sum(); sst = ((T[:, i] - T[:, i].mean()) ** 2).sum()
        eta.append(dict(PC=f'PC{i+1}', Factor=fac, Eta_squared=ssb / sst))
pd.DataFrame(eta).pivot(index='PC', columns='Factor', values='Eta_squared').reset_index().to_csv(os.path.join(TAB, 'pca_eta2.csv'), index=False)

# ---- PERMANOVA (Euclidean, SNV spectra, plot-date means) with marginal (Type II) SS
Y = snv(PDm); Y = Y - Y.mean(0)
D = PDmeta.copy(); D['Disease'] = D['label']; D['Date'] = D['date']; D['Variety'] = D['variety']; D['Stage'] = D['stage']
def design(terms):
    cols = [np.ones(len(D))]
    for tname in terms:
        if ':' in tname:
            a_, b_ = tname.split(':')
            A_ = pd.get_dummies(D[a_], drop_first=True).to_numpy(float); B_ = pd.get_dummies(D[b_], drop_first=True).to_numpy(float)
            cols.append(np.einsum('ij,ik->ijk', A_, B_).reshape(len(D), -1))
        else:
            cols.append(pd.get_dummies(D[tname], drop_first=True).to_numpy(float))
    return np.column_stack(cols)
def rss(Xd, Yv):
    beta, *_ = np.linalg.lstsq(Xd, Yv, rcond=None); e = Yv - Xd @ beta
    return (e ** 2).sum(), np.linalg.matrix_rank(Xd)
mains = ['Disease', 'Date', 'Variety', 'Stage']
inters = ['Disease:Date', 'Disease:Variety']
terms = mains + inters
SST = (Y ** 2).sum()
rss_full, rk_full = rss(design(terms), Y)
rng = np.random.default_rng(11)
perm_rows = []
def term_F(Dcur, tname):
    base = mains if tname in mains else terms
    red = [x for x in base if x != tname]
    rf_, kf = rss(design_on(Dcur, base), Y); rr_, kr = rss(design_on(Dcur, red), Y)
    df1 = kf - kr; df2 = len(Dcur) - rk_full
    return ((rr_ - rf_) / df1) / (rss_full / df2), rr_ - rf_, df1
def design_on(Dcur, tl):
    global D
    keep = D; D = Dcur
    out = design(tl); D = keep
    return out
NPERM = 999
for tname in terms:
    F, SSt, df1 = term_F(D, tname)
    cnt = 0
    for _ in range(NPERM):
        Dp = D.copy()
        col = 'Disease' if tname.startswith('Disease') else tname
        if col in ('Disease', 'Variety'):
            pl = D.groupby('plot')[col].first(); perm = pd.Series(rng.permutation(pl.to_numpy()), index=pl.index)
            Dp[col] = D['plot'].map(perm)
        else:
            Dp[col] = D.groupby('plot')[col].transform(lambda s: rng.permutation(s.to_numpy()))
        cnt += term_F(Dp, tname)[0] >= F
    perm_rows.append(dict(Term=tname, df=df1, SS=SSt, Pseudo_F=F, R2_partial_pct=100 * SSt / SST, p_perm=(cnt + 1) / (NPERM + 1)))
PM = pd.DataFrame(perm_rows)
PM = pd.concat([PM, pd.DataFrame([dict(Term='Residual', df=len(D) - rk_full, SS=rss_full, Pseudo_F=np.nan,
                                       R2_partial_pct=100 * rss_full / SST, p_perm=np.nan)])])
PM.to_csv(os.path.join(TAB, 'permanova.csv'), index=False)
print(PM)

# ---- linear mixed models for key features: feature ~ disease + date + variety + (1|plot)
key = pd.concat([VI, DER[['Datt3_D754/D704', 'D2_D705/D722', 'SDr', 'Db']]], axis=1)
lm = []
for col in key.columns:
    dfm = M[['plot', 'date', 'variety', 'stage', 'y']].copy(); dfm['v'] = (key[col] - key[col].mean()) / key[col].std()
    try:
        fit = smf.mixedlm('v ~ y + C(date) + C(variety)', dfm, groups=dfm['plot']).fit(reml=True)
        inter = smf.mixedlm('v ~ y * C(date) + C(variety)', dfm, groups=dfm['plot']).fit(reml=False)
        base = smf.mixedlm('v ~ y + C(date) + C(variety)', dfm, groups=dfm['plot']).fit(reml=False)
        lr = 2 * (inter.llf - base.llf); p_int = stats.chi2.sf(lr, 3)
        lm.append(dict(Feature=col, Disease_effect_SDunits=fit.params['y'], SE=fit.bse['y'], p_disease=fit.pvalues['y'],
                       p_disease_x_date=p_int, Plot_var=float(fit.cov_re.iloc[0, 0]), Residual_var=fit.scale))
    except Exception as e:
        print('lmm fail', col, e)
LM = pd.DataFrame(lm)
LM['q_disease'] = multipletests(LM['p_disease'], method='fdr_bh')[1]
LM.sort_values('p_disease').to_csv(os.path.join(TAB, 'mixed_models_features.csv'), index=False)

# ---- VI ranking: AUC, Cohen d per date, JM (spectrum level) + plot-date Welch
from sklearn.metrics import roc_auc_score
vr = []
VIpd = VI.assign(plot_date=M['plot_date']).groupby('plot_date').mean().loc[keys]
cite = pd.read_csv(os.path.join(TAB, 'vi_definitions.csv')).set_index('Index')
for col in VI.columns:
    v = VI[col].to_numpy()
    auc = roc_auc_score(y, v); d_by = []
    for dt in DATE_ORDER:
        m = (PDmeta['date'] == dt).to_numpy(); a, b = VIpd[col].to_numpy()[m & (ypd == 1)], VIpd[col].to_numpy()[m & (ypd == 0)]
        d_by.append((a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2))
    a, b = VIpd[col].to_numpy()[ypd == 1], VIpd[col].to_numpy()[ypd == 0]
    vr.append(dict(Index=col, Trait=cite.loc[col, 'Trait'], Reference=cite.loc[col, 'Reference'],
                   Healthy_mean=v[y == 0].mean(), Diseased_mean=v[y == 1].mean(), AUC=max(auc, 1 - auc),
                   Direction='D > H' if auc > 0.5 else 'D < H', JM=jm1(v[y == 1][:, None], v[y == 0][:, None])[0],
                   Cohen_d_pooled=(a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2),
                   **{f'd_{DATE_LABEL[dt]}': x for dt, x in zip(DATE_ORDER, d_by)},
                   Sign_consistent_all_dates=bool(np.all(np.sign(d_by) == np.sign(d_by[0]))),
                   Welch_p_plotdate=stats.ttest_ind(a, b, equal_var=False)[1]))
VR = pd.DataFrame(vr)
VR['q_FDR'] = multipletests(VR['Welch_p_plotdate'], method='fdr_bh')[1]
VR = VR.sort_values('AUC', ascending=False)
VR.to_csv(os.path.join(TAB, 'vi_ranking.csv'), index=False)

# ---- exhaustive NDSI / RSI search (whole data, descriptive map; in-fold search used for modelling)
I, J, score_mean, score_min = ndsi_scores(B10, y, dates)
mat = np.zeros((len(WL10), len(WL10))); mat[I, J] = score_mean; mat[J, I] = score_mean
np.save(os.path.join(CACHE, 'ndsi_matrix.npy'), mat)
order = np.argsort(-score_mean)[:15]
top = []
for k in order:
    i, j = I[k], J[k]
    nd = (B10[:, i] - B10[:, j]) / (B10[:, i] + B10[:, j])
    auc = roc_auc_score(y, nd)
    top.append(dict(Band_i_nm=WL10[i], Band_j_nm=WL10[j], Formula=f'(R{WL10[i]} - R{WL10[j]})/(R{WL10[i]} + R{WL10[j]})',
                    Mean_abs_d_across_dates=score_mean[k], Min_abs_d_across_dates=score_min[k], AUC=max(auc, 1 - auc)))
pd.DataFrame(top).to_csv(os.path.join(TAB, 'ndsi_top_pairs.csv'), index=False)
# coarse matrix (every 20 nm) for an editable Excel heat map
step = 2
pd.DataFrame(mat[::step, ::step], index=WL10[::step], columns=WL10[::step]).to_csv(os.path.join(TAB, 'ndsi_matrix_20nm.csv'))

# ---- CWT sensitivity (|Cohen d| per wavelength x scale on plot-date means)
CW = pd.read_pickle(os.path.join(CACHE, 'F6_CWT.pkl'))
CWpd = CW.assign(plot_date=M['plot_date']).groupby('plot_date').mean().loc[keys].to_numpy()
a, b = CWpd[ypd == 1], CWpd[ypd == 0]
dcw = (a.mean(0) - b.mean(0)) / np.sqrt((a.var(0, ddof=1) + b.var(0, ddof=1)) / 2)
cwm = np.abs(dcw).reshape(len(CWT_SCALES), len(WL10))
pd.DataFrame(cwm.T, index=WL10, columns=[f'Scale_{k}' for k in range(1, 9)]).to_csv(os.path.join(TAB, 'cwt_abs_d_scalogram.csv'))

# ---- class-mean similarity per date (Selvaprakash et al., 2026)
sim = []
for dt in DATE_ORDER:
    m = dates == dt; h, dd_ = B10[m & (y == 0)].mean(0), B10[m & (y == 1)].mean(0)
    cos = h @ dd_ / (np.linalg.norm(h) * np.linalg.norm(dd_))
    sim.append(dict(Date=DATE_LABEL[dt], Cosine_similarity=cos, Spectral_angle_deg=np.degrees(np.arccos(cos)),
                    Euclidean_distance=np.linalg.norm(h - dd_)))
pd.DataFrame(sim).to_csv(os.path.join(TAB, 'class_similarity_by_date.csv'), index=False)
print('done explore')
