"""Steps 2-4 - quality control, spectral characterisation and univariate / multivariate screening of
every feature family at plot level (48 plots x 4 dates)."""
import os, sys
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import savgol_filter
from statsmodels.stats.multitest import multipletests
import statsmodels.formula.api as smf
import warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcommon import *
import common as LC

M = load_meta()
y = M['y'].to_numpy()
dates = M['date'].to_numpy()

# ---------------------------------------------------------------- CWT family (Lv et al., 2023; Tian et al., 2021)
for b in BRANCHES:
    p = os.path.join(CACHE, f'{b}_CWT.pkl')
    if not os.path.exists(p):
        R1, wl = load_spectra(b)
        k = (wl >= 400) & (wl <= 2400)
        LC.cwt_features(R1[:, k], wl[k]).to_pickle(p)
FAMS = ['REF', 'FD1', 'FD2', 'FD3', 'CR', 'VI', 'RE', 'CWT']
F = {b: {f: load_family(b, f) for f in FAMS} for b in BRANCHES}

# ---------------------------------------------------------------- Step 1 design tables
design = M.pivot_table(index='date', columns='label', values='plot', aggfunc='count')[['Healthy', 'Diseased']]
leaves = M.pivot_table(index='date', columns='label', values='n_leaves', aggfunc=['min', 'median', 'max', 'sum'])
leaves.columns = [f'{a}_{b}' for a, b in leaves.columns]
D1 = design.join(leaves).reset_index()
D1['Date'] = D1['date'].map(DATE_LABEL)
D1.to_csv(os.path.join(TAB, 'design_by_date.csv'), index=False)
st = M.pivot_table(index=['date', 'stage'], columns='label', values='plot', aggfunc='count').fillna(0).reset_index()
st.to_csv(os.path.join(TAB, 'design_stage.csv'), index=False)
T = pd.read_csv(os.path.join(CACHE, 'treatment.csv'))
lay = T.pivot_table(index=['variety_t', 'inoc'], columns='block', values='plot', aggfunc='first').reset_index()
lay.columns = ['Variety', 'Inoculation'] + [f'Plot_{c}' for c in lay.columns[2:]]
lay.to_csv(os.path.join(TAB, 'design_layout.csv'), index=False)

# ---------------------------------------------------------------- Step 2 QC: noise, joins, leaf-number confound, outliers
qc = []
for b in BRANCHES:
    R1, wl = load_spectra(b)
    sm = savgol_filter(R1, 11, 2, axis=1)
    m = ((wl >= 450) & (wl <= 900)) | ((wl >= 1050) & (wl <= 1300))
    noise = (R1 - sm)[:, m].std(1)
    i1000, i1001, i1800, i1801 = [int(np.where(wl == w)[0][0]) for w in (1000, 1001, 1800, 1801)]
    step1 = R1[:, i1001] - R1[:, i1000] - (R1[:, i1000] - R1[:, i1000 - 1])
    step2 = R1[:, i1801] - R1[:, i1800] - (R1[:, i1800] - R1[:, i1800 - 1])
    for i in range(len(M)):
        qc.append(dict(branch=b, pd=M['pd'][i], plot=M['plot'][i], date=M['date'][i], label=M['label'][i],
                       n_leaves=M['n_leaves'][i], noise_sd=noise[i], join1000_step=step1[i], join1800_step=step2[i]))
QC = pd.DataFrame(qc)
QC.to_csv(os.path.join(TAB, 'qc_plot_noise.csv'), index=False)
qsum = []
for b in BRANCHES:
    q = QC[QC.branch == b]
    for dt in DATE_ORDER:
        qq = q[q.date == dt]
        h, d = qq[qq.label == 'Healthy'], qq[qq.label == 'Diseased']
        rho, prho = stats.spearmanr(qq['n_leaves'], qq['noise_sd'])
        qsum.append(dict(Branch=b, Date=DATE_LABEL[dt], Leaves_H=h['n_leaves'].median(), Leaves_D=d['n_leaves'].median(),
                         Noise_H=h['noise_sd'].mean(), Noise_D=d['noise_sd'].mean(),
                         Noise_ratio_D_over_H=d['noise_sd'].mean() / h['noise_sd'].mean(),
                         Expected_ratio_sqrt_n=np.sqrt(h['n_leaves'].mean() / d['n_leaves'].mean()),
                         p_MWU_noise=stats.mannwhitneyu(h['noise_sd'], d['noise_sd'])[1],
                         Spearman_leaves_noise=rho, p_spearman=prho,
                         Join1000_abs_H=h['join1000_step'].abs().mean(), Join1000_abs_D=d['join1000_step'].abs().mean(),
                         Join1800_abs_H=h['join1800_step'].abs().mean(), Join1800_abs_D=d['join1800_step'].abs().mean()))
pd.DataFrame(qsum).to_csv(os.path.join(TAB, 'qc_noise_summary.csv'), index=False)

R10 = F['raw']['REF'].to_numpy()
out = []
for dt in DATE_ORDER:
    mm = dates == dt
    Z = (R10[mm] - R10[mm].mean(0)) / R10[mm].std(0)
    U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    k = 5
    Tsc = U[:, :k] * S[:k]
    lam = S[:k] ** 2 / (mm.sum() - 1)
    T2 = ((Tsc ** 2) / lam).sum(1)
    E = Z - Tsc @ Vt[:k]
    Q = (E ** 2).sum(1)
    n = mm.sum()
    T2lim = k * (n - 1) * (n + 1) / (n * (n - k)) * stats.f.ppf(0.99, k, n - k)
    g = Q.var() / (2 * Q.mean()); h = 2 * Q.mean() ** 2 / Q.var()
    Qlim = g * stats.chi2.ppf(0.99, h)
    for j, i in enumerate(np.where(mm)[0]):
        out.append(dict(date=dt, plot=M['plot'][i], label=M['label'][i], T2=T2[j], T2_limit99=T2lim, Q=Q[j], Q_limit99=Qlim,
                        flag=bool(T2[j] > T2lim or Q[j] > Qlim)))
OUT = pd.DataFrame(out)
OUT.to_csv(os.path.join(TAB, 'qc_outliers_plot.csv'), index=False)
print('outlier flags', OUT.groupby(['date', 'label'])['flag'].sum().to_dict())


# ---------------------------------------------------------------- Step 3 statistics helpers
def jm1(a, b):
    m1, m2, v1, v2 = a.mean(0), b.mean(0), a.var(0, ddof=1), b.var(0, ddof=1)
    v1 = np.maximum(v1, 1e-30); v2 = np.maximum(v2, 1e-30)
    B = 0.125 * (m1 - m2) ** 2 * 2 / (v1 + v2) + 0.5 * np.log(((v1 + v2) / 2) / np.sqrt(v1 * v2))
    return 2 * (1 - np.exp(-B))


def auc_vec(A, yy):
    r = stats.rankdata(A, axis=0)
    n1, n0 = (yy == 1).sum(), (yy == 0).sum()
    return (r[yy == 1].sum(0) - n1 * (n1 + 1) / 2) / (n1 * n0)


def fstats(A, yy):
    a, b = A[yy == 1], A[yy == 0]
    with np.errstate(all='ignore'):
        t, p = stats.ttest_ind(a, b, equal_var=False)
        sp = np.sqrt((a.var(0, ddof=1) * (len(a) - 1) + b.var(0, ddof=1) * (len(b) - 1)) / (len(a) + len(b) - 2))
        d = (a.mean(0) - b.mean(0)) / sp
        d = d * (1 - 3 / (4 * (len(a) + len(b)) - 9))  # Hedges correction
    p = np.where(np.isfinite(p), p, 1.0)
    auc = auc_vec(A, yy)
    return dict(mean_H=b.mean(0), mean_D=a.mean(0), t=t, p=p, g=np.nan_to_num(d), AUC_signed=auc,
                AUC=np.maximum(auc, 1 - auc), JM=jm1(a, b), r_pb=np.nan_to_num(np.array([np.corrcoef(yy, A[:, j])[0, 1] if A[:, j].std() > 0 else 0 for j in range(A.shape[1])])))


# ---------------------------------------------------------------- Step 3a band-wise spectra statistics (raw branch)
spec = {'Wavelength_nm': WL10}
for b in BRANCHES:
    X = F[b]['REF'].to_numpy()
    for dt in DATE_ORDER:
        mm = dates == dt
        for lab, yy in (('H', 0), ('D', 1)):
            spec[f'{b}_{DATE_LABEL[dt]}_{lab}_mean'] = X[mm & (y == yy)].mean(0)
            spec[f'{b}_{DATE_LABEL[dt]}_{lab}_sd'] = X[mm & (y == yy)].std(0, ddof=1)
    for lab, yy in (('H', 0), ('D', 1)):
        spec[f'{b}_All_{lab}_mean'] = X[y == yy].mean(0)
        spec[f'{b}_All_{lab}_sd'] = X[y == yy].std(0, ddof=1)
SP = pd.DataFrame(spec)
SP.to_csv(os.path.join(TAB, 'spectra_mean_by_date_class.csv'), index=False)

bw = []
for b in BRANCHES:
    for fam in ['REF', 'FD1', 'FD2', 'FD3']:
        X = F[b][fam].to_numpy()
        for dt in DATE_ORDER + ['All']:
            mm = np.ones(len(y), bool) if dt == 'All' else dates == dt
            s = fstats(X[mm], y[mm])
            q = multipletests(s['p'], method='fdr_bh')[1]
            for j, w in enumerate(WL10):
                bw.append(dict(branch=b, family=fam, date=DATE_LABEL.get(dt, 'All'), wl=w, mean_H=s['mean_H'][j], mean_D=s['mean_D'][j],
                               diff=s['mean_D'][j] - s['mean_H'][j], ratio=s['mean_D'][j] / s['mean_H'][j] if s['mean_H'][j] != 0 else np.nan,
                               t=s['t'][j], p=s['p'][j], q=q[j], g=s['g'][j], AUC=s['AUC'][j], JM=s['JM'][j], r_pb=s['r_pb'][j]))
BW = pd.DataFrame(bw)
BW.to_csv(os.path.join(TAB, 'bandwise_by_date.csv'), index=False)

# sensitive regions: contiguous 10-nm bands with q < 0.05 on >= 3 of 4 dates and a consistent sign
reg = []
for b in BRANCHES:
    for fam in ['REF', 'FD1']:
        S = BW[(BW.branch == b) & (BW.family == fam) & (BW.date != 'All')]
        sig = S.assign(s=(S.q < 0.05) * np.sign(S.g)).pivot(index='wl', columns='date', values='s')
        ndates = (sig > 0).sum(1).where((sig > 0).sum(1) >= (sig < 0).sum(1), -(sig < 0).sum(1))
        ok = ndates.abs() >= 3
        run = []
        for w in WL10:
            if ok[w]:
                run.append(w)
            if (not ok[w] or w == WL10[-1]) and run:
                if len(run) >= 2:
                    sub = S[S.wl.isin(run)]
                    reg.append(dict(branch=b, family=fam, start_nm=run[0], end_nm=run[-1] + 9, n_bands=len(run),
                                    direction='D > H' if sub.g.mean() > 0 else 'D < H', mean_abs_g=sub.g.abs().mean(),
                                    mean_AUC=sub.AUC.mean(), min_q=sub.q.min()))
                run = []
REG = pd.DataFrame(reg)
REG.to_csv(os.path.join(TAB, 'sensitive_regions.csv'), index=False)
print(REG[REG.branch == 'raw'].to_string())

# ---------------------------------------------------------------- Step 3b screening of every feature (all families)
rows = []
for b in BRANCHES:
    for fam in FAMS:
        Fm = F[b][fam]
        X = Fm.to_numpy(float)
        per = {}
        for dt in DATE_ORDER:
            mm = dates == dt
            s = fstats(X[mm], y[mm]); s['q'] = multipletests(s['p'], method='fdr_bh')[1]
            per[dt] = s
        sall = fstats(X, y)
        g = np.array([per[dt]['g'] for dt in DATE_ORDER])
        q = np.array([per[dt]['q'] for dt in DATE_ORDER])
        A = np.array([per[dt]['AUC'] for dt in DATE_ORDER])
        cons = np.abs(np.sign(g).sum(0)) == 4
        for j, c in enumerate(Fm.columns):
            r = dict(branch=b, family=fam, feature=c, mean_H=sall['mean_H'][j], mean_D=sall['mean_D'][j],
                     direction='D > H' if np.mean(g[:, j]) > 0 else 'D < H', sign_consistent=bool(cons[j]),
                     n_dates_q05=int((q[:, j] < 0.05).sum()), mean_abs_g=np.abs(g[:, j]).mean(), mean_AUC=A[:, j].mean(),
                     min_AUC=A[:, j].min(), pooled_AUC=sall['AUC'][j], pooled_JM=sall['JM'][j])
            for k, dt in enumerate(DATE_ORDER):
                r[f'AUC_{DATE_LABEL[dt]}'] = A[k, j]; r[f'g_{DATE_LABEL[dt]}'] = g[k, j]; r[f'q_{DATE_LABEL[dt]}'] = q[k, j]
            rows.append(r)
SCR = pd.DataFrame(rows)
SCR['score'] = SCR['mean_AUC'] * SCR['sign_consistent']
SCR.to_csv(os.path.join(TAB, 'feature_screening_all.csv'), index=False)
top = SCR[SCR.branch == 'raw'].sort_values('score', ascending=False).groupby('family').head(10)
top.to_csv(os.path.join(TAB, 'feature_screening_top10.csv'), index=False)
fsum = SCR.groupby(['branch', 'family']).agg(n_features=('feature', 'size'), n_sig_3dates=('n_dates_q05', lambda s: int((s >= 3).sum())),
                                              n_sig_4dates=('n_dates_q05', lambda s: int((s >= 4).sum())),
                                              best_mean_AUC=('score', 'max'), median_mean_AUC=('mean_AUC', 'median')).reset_index()
fsum.to_csv(os.path.join(TAB, 'feature_screening_family_summary.csv'), index=False)
print(fsum.to_string())

# ---------------------------------------------------------------- Step 3c raw vs smoothed separability
rv = SCR.pivot_table(index=['family', 'feature'], columns='branch', values='mean_AUC').reset_index()
rv['delta'] = rv['smooth'] - rv['raw']
rvs = rv.groupby('family').agg(mean_AUC_raw=('raw', 'mean'), mean_AUC_smooth=('smooth', 'mean'), mean_delta=('delta', 'mean'),
                               max_AUC_raw=('raw', 'max'), max_AUC_smooth=('smooth', 'max'),
                               r_raw_smooth=('raw', lambda s: np.corrcoef(s, rv.loc[s.index, 'smooth'])[0, 1])).reset_index()
rvs.to_csv(os.path.join(TAB, 'raw_vs_smooth_separability.csv'), index=False)

# ---------------------------------------------------------------- Step 3d mixed models (repeated measures over dates)
lm = []
sc = pd.concat([F['raw']['VI'], F['raw']['CR'], F['raw']['RE']], axis=1)
fam_of = {c: 'VI' for c in F['raw']['VI'].columns} | {c: 'CR' for c in F['raw']['CR'].columns} | {c: 'RE' for c in F['raw']['RE'].columns}
topb = SCR[(SCR.branch == 'raw') & SCR.family.isin(['REF', 'FD1', 'FD2', 'FD3', 'CWT'])].sort_values('score', ascending=False).groupby('family').head(5)
for _, r in topb.iterrows():
    sc[r['feature']] = F['raw'][r['family']][r['feature']].to_numpy(); fam_of[r['feature']] = r['family']
for col in sc.columns:
    v = sc[col].to_numpy(float)
    if v.std() == 0:
        continue
    dfm = M[['plot', 'date', 'variety', 'y']].copy(); dfm['v'] = (v - v.mean()) / v.std()
    try:
        fit = smf.mixedlm('v ~ y + C(date) + C(variety)', dfm, groups=dfm['plot']).fit(reml=True)
        inter = smf.mixedlm('v ~ y * C(date) + C(variety)', dfm, groups=dfm['plot']).fit(reml=False)
        base = smf.mixedlm('v ~ y + C(date) + C(variety)', dfm, groups=dfm['plot']).fit(reml=False)
        p_int = stats.chi2.sf(2 * (inter.llf - base.llf), 3)
        pv = float(fit.cov_re.iloc[0, 0])
        lm.append(dict(Family=fam_of[col], Feature=col, Disease_effect_SD=fit.params['y'], SE=fit.bse['y'], z=fit.tvalues['y'],
                       p_disease=fit.pvalues['y'], p_disease_x_date=p_int, ICC_plot=pv / (pv + fit.scale)))
    except Exception as e:
        print('lmm fail', col, e)
LM = pd.DataFrame(lm)
LM['q_disease'] = multipletests(LM['p_disease'], method='fdr_bh')[1]
LM['q_interaction'] = multipletests(LM['p_disease_x_date'], method='fdr_bh')[1]
LM.sort_values('p_disease').to_csv(os.path.join(TAB, 'mixed_models.csv'), index=False)
print('LMM sig', (LM.q_disease < 0.05).sum(), 'of', len(LM))

# ---------------------------------------------------------------- Step 3e treatment design: matched control, block control, inoculation timing
mc, bc, it = [], [], []
cand = SCR[SCR.branch == 'raw'].sort_values('score', ascending=False)
cand = pd.concat([cand[cand.family.isin(['VI', 'CR', 'RE'])], cand[~cand.family.isin(['VI', 'CR', 'RE'])].groupby('family').head(20)])
inoc_order = {'D1': 1, 'D2': 2, 'D3': 3, 'D4': 4}
for _, r in cand.iterrows():
    v = F['raw'][r['family']][r['feature']].to_numpy(float)
    for dt in DATE_ORDER:
        mm = dates == dt
        sub = M[mm].assign(v=v[mm])
        h, d = sub[sub.y == 0], sub[sub.y == 1]
        sp = np.sqrt(((h.v.var() * (len(h) - 1)) + d.v.var() * (len(d) - 1)) / (len(sub) - 2))
        if sp == 0:
            continue
        ctrl = h.set_index('cell')['v']
        dd = d.assign(delta=(d.v - d.cell.map(ctrl)) / sp)
        cellm = dd.groupby('cell')['delta'].mean()
        t, p = stats.ttest_1samp(cellm, 0)
        mc.append(dict(family=r['family'], feature=r['feature'], date=DATE_LABEL[dt], mean_delta_SD=cellm.mean(), t=t, p=p,
                       cells_same_sign=float((np.sign(cellm) == np.sign(cellm.mean())).mean())))
        gb = [d[d.block == k].v.to_numpy() for k in ('R1', 'R2', 'R3')]
        dcr = (d.v.mean() - h.v.mean()) / sp
        dblk = max(abs(a.mean() - c.mean()) / np.sqrt((a.var(ddof=1) + c.var(ddof=1)) / 2) for a, c in [(gb[0], gb[1]), (gb[0], gb[2]), (gb[1], gb[2])])
        dhr = [abs(g_.mean() - h.v.mean()) / np.sqrt((g_.var(ddof=1) + h.v.var(ddof=1)) / 2) for g_ in gb]
        bc.append(dict(family=r['family'], feature=r['feature'], date=DATE_LABEL[dt], abs_d_control_vs_inoculated=abs(dcr),
                       max_abs_d_between_blocks=dblk, ratio=abs(dcr) / dblk if dblk > 0 else np.nan,
                       min_abs_d_control_vs_block=min(dhr), p_KW_blocks=stats.kruskal(*gb)[1]))
        grp = [dd[dd.inoc == k]['delta'].to_numpy() for k in ('D1', 'D2', 'D3', 'D4')]
        rho, prho = stats.spearmanr(dd.inoc.map(inoc_order), dd['delta'])
        it.append(dict(family=r['family'], feature=r['feature'], date=DATE_LABEL[dt], **{f'delta_{k}': g_.mean() for k, g_ in zip(('D1', 'D2', 'D3', 'D4'), grp)},
                       p_KW_inoc=stats.kruskal(*grp)[1], spearman_inoc=rho, p_spearman=prho))
pd.DataFrame(mc).to_csv(os.path.join(TAB, 'matched_control_effects.csv'), index=False)
BC = pd.DataFrame(bc); BC.to_csv(os.path.join(TAB, 'block_control.csv'), index=False)
pd.DataFrame(it).to_csv(os.path.join(TAB, 'inoculation_timing.csv'), index=False)
print(BC.groupby('family')[['abs_d_control_vs_inoculated', 'max_abs_d_between_blocks', 'ratio']].median())

# ---------------------------------------------------------------- Step 3f red-edge parameter table (Mandal et al., 2022)
re_rows = []
REm = F['raw']['RE']
for c in REm.columns:
    v = REm[c].to_numpy(float)
    for dt in DATE_ORDER:
        mm = dates == dt
        h, d = v[mm & (y == 0)], v[mm & (y == 1)]
        re_rows.append(dict(Parameter=c, Date=DATE_LABEL[dt], Healthy_mean=h.mean(), Healthy_sd=h.std(ddof=1), Diseased_mean=d.mean(),
                            Diseased_sd=d.std(ddof=1), Diff=d.mean() - h.mean(), p_Welch=stats.ttest_ind(d, h, equal_var=False)[1]))
pd.DataFrame(re_rows).to_csv(os.path.join(TAB, 'red_edge_by_date.csv'), index=False)

# ---------------------------------------------------------------- Step 4a PCA (SNV raw reflectance) and eta-squared
Xs = LC.snv(R10)
Zc = Xs - Xs.mean(0)
U, S, Vt = np.linalg.svd(Zc, full_matrices=False)
Tsc = U * S
ev = S ** 2 / (S ** 2).sum()
Xd = Xs.copy()
for dt in DATE_ORDER:
    mm = dates == dt; Xd[mm] -= Xd[mm].mean(0)
U2, S2, Vt2 = np.linalg.svd(Xd, full_matrices=False)
T2s = U2 * S2; ev2 = S2 ** 2 / (S2 ** 2).sum()
sc_df = M[['pd', 'plot', 'date', 'label', 'variety', 'inoc', 'block', 'stage']].copy()
for i in range(3):
    sc_df[f'PC{i+1}'] = Tsc[:, i]; sc_df[f'dcPC{i+1}'] = T2s[:, i]
sc_df.to_csv(os.path.join(TAB, 'pca_scores.csv'), index=False)
pd.DataFrame({'PC': [f'PC{i+1}' for i in range(10)], 'Explained_pct': 100 * ev[:10], 'Cumulative_pct': 100 * np.cumsum(ev[:10]),
              'DateCentred_Explained_pct': 100 * ev2[:10]}).to_csv(os.path.join(TAB, 'pca_variance.csv'), index=False)
pd.DataFrame({'Wavelength_nm': WL10, **{f'PC{i+1}': Vt[i] for i in range(3)}, **{f'dcPC{i+1}': Vt2[i] for i in range(3)}}).to_csv(os.path.join(TAB, 'pca_loadings.csv'), index=False)
eta = []
for nm, TT in (('PCA', Tsc), ('Date-centred PCA', T2s)):
    for i in range(5):
        for fac in ['label', 'date', 'variety', 'stage', 'inoc', 'block', 'plot']:
            g = pd.Series(TT[:, i]).groupby(M[fac].to_numpy())
            ssb = (g.size() * (g.mean() - TT[:, i].mean()) ** 2).sum(); sst = ((TT[:, i] - TT[:, i].mean()) ** 2).sum()
            eta.append(dict(Analysis=nm, PC=f'PC{i+1}', Factor=fac, Eta_squared=ssb / sst))
pd.DataFrame(eta).pivot_table(index=['Analysis', 'PC'], columns='Factor', values='Eta_squared').reset_index().to_csv(os.path.join(TAB, 'pca_eta2.csv'), index=False)

# ---------------------------------------------------------------- Step 4b PERMANOVA with design-restricted permutations
D = M.copy(); D['Disease'] = D['label']; D['Date'] = D['date']; D['Variety'] = D['variety']; D['Stage'] = D['stage']; D['Inoculation'] = D['inoc']


def design_mat(Dc, terms):
    cols = [np.ones(len(Dc))]
    for tname in terms:
        if ':' in tname:
            a_, b_ = tname.split(':')
            A_ = pd.get_dummies(Dc[a_], drop_first=True).to_numpy(float); B_ = pd.get_dummies(Dc[b_], drop_first=True).to_numpy(float)
            cols.append(np.einsum('ij,ik->ijk', A_, B_).reshape(len(Dc), -1))
        else:
            cols.append(pd.get_dummies(Dc[tname], drop_first=True).to_numpy(float))
    return np.column_stack(cols)


def rss(Xd_, Yv):
    beta, *_ = np.linalg.lstsq(Xd_, Yv, rcond=None); e = Yv - Xd_ @ beta
    return (e ** 2).sum(), np.linalg.matrix_rank(Xd_)


mains = ['Disease', 'Date', 'Variety', 'Inoculation', 'Stage']
inters = ['Disease:Date', 'Disease:Variety']
terms = mains + inters
rng = np.random.default_rng(11)
NPERM = 999
PMs = []
resp = {'SNV reflectance (201 bands)': Xs,
        'All scalar features (VI + CR + RE, z-scored)': pd.concat([F['raw']['VI'], F['raw']['CR'], F['raw']['RE']], axis=1).pipe(lambda d: ((d - d.mean()) / d.std().replace(0, 1)).fillna(0)).to_numpy()}
for rname, Yr in resp.items():
    Y = Yr - Yr.mean(0)
    SST = (Y ** 2).sum()
    rss_full, rk_full = rss(design_mat(D, terms), Y)

    def term_F(Dc, tname):
        base = mains if tname in mains else terms
        red = [x for x in base if x != tname]
        rf_, kf = rss(design_mat(Dc, base), Y); rr_, kr = rss(design_mat(Dc, red), Y)
        return ((rr_ - rf_) / (kf - kr)) / (rss_full / (len(Dc) - rk_full)), rr_ - rf_, kf - kr

    for tname in terms:
        Fv, SSt, df1 = term_F(D, tname)
        cnt = 0
        for _ in range(NPERM):
            Dp = D.copy()
            col = 'Disease' if tname.startswith('Disease') else tname
            if col == 'Disease':      # whole plots permuted within variety x inoculation cells
                pl = D.groupby('plot')[['Disease', 'cell']].first()
                perm = pl.groupby('cell')['Disease'].transform(lambda s: rng.permutation(s.to_numpy()))
                Dp[col] = D['plot'].map(perm)
            elif col in ('Variety', 'Inoculation'):
                pl = D.groupby('plot')[col].first(); perm = pd.Series(rng.permutation(pl.to_numpy()), index=pl.index)
                Dp[col] = D['plot'].map(perm)
            else:
                Dp[col] = D.groupby('plot')[col].transform(lambda s: rng.permutation(s.to_numpy()))
            cnt += term_F(Dp, tname)[0] >= Fv
        PMs.append(dict(Response=rname, Term=tname, df=df1, SS=SSt, Pseudo_F=Fv, R2_pct=100 * SSt / SST, p_perm=(cnt + 1) / (NPERM + 1)))
    PMs.append(dict(Response=rname, Term='Residual', df=len(D) - rk_full, SS=rss_full, Pseudo_F=np.nan, R2_pct=100 * rss_full / SST, p_perm=np.nan))
PM = pd.DataFrame(PMs)
PM.to_csv(os.path.join(TAB, 'permanova.csv'), index=False)
print(PM.to_string())

# ---------------------------------------------------------------- Step 4c exhaustive two-band index search (NDSI, SR, DI) on 10-nm bands
I, J = np.triu_indices(len(WL10), 1)
near = lambda w: (abs(w - 1000) <= 10) | (abs(w - 1800) <= 10)
joinfree = ~(near(WL10[I]) | near(WL10[J]))
res = {}
idx_rows = []
for b in BRANCHES:
    X = F[b]['REF'].to_numpy()
    for kind in ('NDSI', 'SR', 'DI'):
        r2d, sgn = [], []
        for dt in DATE_ORDER:
            mm = dates == dt
            A, B = X[mm][:, I], X[mm][:, J]
            V = (A - B) / (A + B) if kind == 'NDSI' else (A / B if kind == 'SR' else A - B)
            yy = y[mm] - y[mm].mean()
            Vc = V - V.mean(0)
            r = (yy @ Vc) / np.sqrt((yy ** 2).sum() * (Vc ** 2).sum(0))
            r2d.append(r ** 2); sgn.append(np.sign(r))
        r2d = np.array(r2d); cons = np.abs(np.array(sgn).sum(0)) == 4
        score = r2d.mean(0) * cons
        res[(b, kind)] = score
        for jf in (False, True):
            sc_ = np.where(joinfree, score, 0) if jf else score
            for k in np.argsort(-sc_)[:10]:
                idx_rows.append(dict(branch=b, index=kind, join_free=jf, band_i=WL10[I[k]], band_j=WL10[J[k]], mean_r2=r2d[:, k].mean(),
                                     min_r2=r2d[:, k].min(), **{f'r2_{DATE_LABEL[dt]}': r2d[q, k] for q, dt in enumerate(DATE_ORDER)}))
IDX = pd.DataFrame(idx_rows)
IDX.to_csv(os.path.join(TAB, 'optimised_index_top_pairs.csv'), index=False)
print(IDX[(IDX.branch == 'raw')].groupby(['index', 'join_free']).head(2).to_string())
Mat = np.zeros((len(WL10), len(WL10)))
Mat[I, J] = res[('raw', 'NDSI')]; Mat[J, I] = res[('raw', 'SR')]
np.save(os.path.join(CACHE, 'ndsi_sr_matrix_raw.npy'), Mat)
sub = np.arange(0, len(WL10), 2)
pd.DataFrame(Mat[np.ix_(sub, sub)], index=WL10[sub], columns=WL10[sub]).to_csv(os.path.join(TAB, 'ndsi_sr_r2_matrix_20nm.csv'))

# workbook's own optimised indices (selected on all plots of a date -> descriptive only)
wb = []
OPT = load_family('raw', 'OPT')
for dt in DATE_ORDER:
    mm = dates == dt
    sub_ = OPT[mm].dropna(axis=1, how='all')
    for c in sub_.columns:
        v = sub_[c].to_numpy(float)
        a = auc_vec(v[:, None], y[mm])[0]
        wb.append(dict(Date=DATE_LABEL[dt], Index=c, AUC=max(a, 1 - a)))
pd.DataFrame(wb).to_csv(os.path.join(TAB, 'workbook_optimised_indices.csv'), index=False)
print('done')
