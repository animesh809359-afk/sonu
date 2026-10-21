"""Publication-style figures (PNG, 300 dpi) of the plot-level analysis; line and bar charts are also rebuilt as
native, editable charts in the workbook and the slides."""
import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcommon import *

T = lambda n: pd.read_csv(os.path.join(TAB, n))
have = lambda n: os.path.exists(os.path.join(TAB, n))
H, D, C3, C4 = '#2E7D32', '#D08A00', '#2A6FB0', '#B03A2E'
DATEC = [C3, H, D, C4]
DL = [DATE_LABEL[d] for d in DATE_ORDER]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': '#E6E6E6', 'grid.linewidth': 0.6, 'axes.edgecolor': '#888888',
                     'legend.frameon': False, 'savefig.dpi': 300, 'savefig.bbox': 'tight'})
REGIONS = [(400, 700), (700, 750), (750, 1300), (1300, 1900), (1900, 2400)]


def save(fig, name):
    fig.savefig(os.path.join(FIG, name)); plt.close(fig); print('fig', name)


def shade(ax):
    for k, (a, b) in enumerate(REGIONS):
        if k % 2:
            ax.axvspan(a, b, color='#000000', alpha=0.035, lw=0)
    for j in JOINS:
        ax.axvline(j, color='#999999', lw=0.6, ls=':')


M = load_meta()

# Fig01 field layout of the treatments
Lay = T('design_layout.csv')
fig, ax = plt.subplots(figsize=(10, 2.8))
blocks = ['C', 'R3', 'R2', 'R1']
for i, b in enumerate(blocks):
    for j, (_, r) in enumerate(Lay.iterrows()):
        pl = r[f'Plot_{b}']
        col = H if b == 'C' else D
        ax.add_patch(plt.Rectangle((j, -i), 0.94, 0.9, color=col, alpha=0.85 if b == 'C' else 0.55 + 0.1 * i))
        ax.text(j + 0.47, -i + 0.58, f'P{pl}', ha='center', va='center', fontsize=8, color='white', weight='bold')
        ax.text(j + 0.47, -i + 0.25, f"{r['Variety']}-{r['Inoculation']}", ha='center', va='center', fontsize=6.5, color='white')
ax.set_xlim(0, 12); ax.set_ylim(-3.2, 1)
ax.set_yticks([0.45, -0.55, -1.55, -2.55]); ax.set_yticklabels(['Control (healthy)', 'Inoculated R3', 'Inoculated R2', 'Inoculated R1'])
ax.set_xticks([]); ax.grid(False)
for s in ax.spines.values(): s.set_visible(False)
ax.set_title('Treatment layout: 3 varieties x 4 inoculation timings (D1-D4); one control and three inoculated plots per cell', fontsize=9)
save(fig, 'Fig01_treatment_layout.png')

# Fig02 mean spectra by date
S = T('spectra_mean_by_date_class.csv'); w = S['Wavelength_nm']
fig, axs = plt.subplots(2, 2, figsize=(11, 6.2), sharex=True, sharey=True)
for k, dl in enumerate(DL):
    ax = axs.flat[k]
    for lab, c, nm in (('H', H, 'Healthy plots (12)'), ('D', D, 'Diseased plots (36)')):
        m, s = S[f'raw_{dl}_{lab}_mean'], S[f'raw_{dl}_{lab}_sd']
        ax.plot(w, m, color=c, lw=1.4, label=nm); ax.fill_between(w, m - s, m + s, color=c, alpha=0.15, lw=0)
    shade(ax); ax.set_title(f'({chr(97 + k)}) {dl} 2026', loc='left')
    if k >= 2: ax.set_xlabel('Wavelength (nm)')
    if k % 2 == 0: ax.set_ylabel('Plot-average reflectance')
axs.flat[0].legend(loc='upper right')
save(fig, 'Fig02_mean_spectra_by_date.png')

# Fig03 difference / ratio spectra and first derivative
BW = T('bandwise_by_date.csv'); BWr = BW[BW.branch == 'raw']
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
for k, dl in enumerate(DL):
    s = BWr[(BWr.family == 'REF') & (BWr.date == dl)]
    ax[0].plot(s.wl, s['diff'], color=DATEC[k], lw=1.3, label=dl); ax[1].plot(s.wl, s['ratio'], color=DATEC[k], lw=1.3, label=dl)
    f1 = BWr[(BWr.family == 'FD1') & (BWr.date == dl)]
    ax[2].plot(f1.wl, f1['diff'], color=DATEC[k], lw=1.2, label=dl)
ax[0].axhline(0, color='#888', lw=0.8); ax[1].axhline(1, color='#888', lw=0.8); ax[2].axhline(0, color='#888', lw=0.8)
ax[0].set(title='(a) Difference spectrum (D - H)', xlabel='Wavelength (nm)', ylabel='Reflectance difference')
ax[1].set(title='(b) Ratio spectrum (D / H)', xlabel='Wavelength (nm)', ylabel='Ratio')
ax[2].set(title='(c) First-derivative difference (D - H)', xlabel='Wavelength (nm)', ylabel='dR/dλ difference')
for a in ax: shade(a)
ax[0].legend()
save(fig, 'Fig03_difference_ratio_spectra.png')

# Fig04 band-wise statistics heat strips
fig, axs = plt.subplots(4, 1, figsize=(11, 6.6), sharex=True)
for i, (fam, met, lab, cmap, vmax) in enumerate([('REF', 'g', "Hedges' g (reflectance)", 'RdBu_r', 2.5), ('FD1', 'g', "Hedges' g (first derivative)", 'RdBu_r', 2.5),
                                                 ('REF', 'AUC', 'AUC (reflectance)', 'viridis', 1.0), ('FD1', 'AUC', 'AUC (first derivative)', 'viridis', 1.0)]):
    P = BWr[(BWr.family == fam) & (BWr.date.isin(DL))].pivot(index='date', columns='wl', values=met).loc[DL]
    vmin = -vmax if met == 'g' else 0.5
    im = axs[i].imshow(P.to_numpy(), aspect='auto', cmap=cmap, vmin=vmin, vmax=vmax, extent=[395, 2405, 3.5, -0.5], interpolation='nearest')
    axs[i].set_yticks(range(4)); axs[i].set_yticklabels(DL); axs[i].grid(False); axs[i].set_title(lab, loc='left', fontsize=9)
    plt.colorbar(im, ax=axs[i], pad=0.01, fraction=0.03)
axs[-1].set_xlabel('Wavelength (nm)')
save(fig, 'Fig04_bandwise_effects.png')

# Fig05 PCA
P = T('pca_scores.csv'); V = T('pca_variance.csv')
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
mk = dict(zip(DATE_ORDER, ['o', 's', '^', 'D']))
for dt in DATE_ORDER:
    for lab, c in (('Healthy', H), ('Diseased', D)):
        s = P[(P.date == dt) & (P.label == lab)]
        ax[0].scatter(s.PC1, s.PC2, c=c, marker=mk[dt], s=22, alpha=0.8, edgecolor='white', lw=0.4, label=f'{lab}, {DATE_LABEL[dt]}')
        ax[1].scatter(s.dcPC1, s.dcPC2, c=c, marker=mk[dt], s=22, alpha=0.8, edgecolor='white', lw=0.4)
ax[0].set(xlabel=f"PC1 ({V.Explained_pct[0]:.1f} %)", ylabel=f"PC2 ({V.Explained_pct[1]:.1f} %)", title='(a) PCA, SNV reflectance (date effect dominates)')
ax[1].set(xlabel=f"PC1 ({V.DateCentred_Explained_pct[0]:.1f} %)", ylabel=f"PC2 ({V.DateCentred_Explained_pct[1]:.1f} %)", title='(b) PCA after removing the date means')
ax[0].legend(fontsize=6.5, ncol=2)
save(fig, 'Fig05_PCA.png')

# Fig06 PERMANOVA
PM = T('permanova.csv')
fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
for k, (rname, g) in enumerate(PM.groupby('Response', sort=False)):
    g = g[g.Term != 'Residual']
    cols = [C4 if t.startswith('Disease') else '#7F7F7F' for t in g.Term]
    ax[k].barh(g.Term, g.R2_pct, color=cols); ax[k].invert_yaxis()
    for i, (r2, p) in enumerate(zip(g.R2_pct, g.p_perm)):
        ax[k].text(r2 + 0.3, i, f'p = {p:.3f}', va='center', fontsize=7)
    ax[k].set(xlabel='Share of total variation (%)', title=f'({chr(97 + k)}) {rname}')
save(fig, 'Fig06_PERMANOVA.png')

# Fig07 feature screening top features per family
TP = T('feature_screening_top10.csv')
fams = ['REF', 'FD1', 'FD2', 'FD3', 'CR', 'VI', 'RE', 'CWT']
fig, axs = plt.subplots(2, 4, figsize=(14, 6.4))
for k, fm in enumerate(fams):
    ax = axs.flat[k]; g = TP[TP.family == fm].head(8).iloc[::-1]
    lab = [f[:26] for f in g.feature]
    ax.barh(lab, g.mean_AUC, color=[C4 if d == 'D > H' else C3 for d in g.direction]); ax.set_xlim(0.5, 1.0)
    ax.set_title(FAMILY_LABEL[fm], fontsize=9, loc='left'); ax.tick_params(axis='y', labelsize=6.5)
    ax.set_xlabel('Mean AUC over 4 dates')
save(fig, 'Fig07_feature_screening.png')

# Fig08 optimised-index map (raw): lower triangle NDSI, upper SR
Mat = np.load(os.path.join(CACHE, 'ndsi_sr_matrix_raw.npy'))
fig, ax = plt.subplots(figsize=(6.2, 5.4))
im = ax.imshow(Mat, origin='lower', extent=[395, 2405, 395, 2405], cmap='magma', vmin=0, vmax=max(0.5, Mat.max()))
ax.plot([400, 2400], [400, 2400], color='white', lw=0.6)
IDX = T('optimised_index_top_pairs.csv'); IDX = IDX[(IDX.branch == 'raw') & (~IDX.join_free)]
for kind, mkr in (('NDSI', 'o'), ('SR', 's')):
    b = IDX[IDX['index'] == kind].iloc[0]
    xx, yy = (b.band_i, b.band_j) if kind == 'NDSI' else (b.band_j, b.band_i)
    ax.scatter([yy], [xx], s=60, facecolor='none', edgecolor='cyan', marker=mkr, lw=1.5)
ax.set(xlabel='Band λ1 (nm)', ylabel='Band λ2 (nm)', title='Mean r² with disease status over dates\n(lower-right: NDSI, upper-left: SR; sign-consistent)')
ax.grid(False); plt.colorbar(im, ax=ax, label='Mean r²')
save(fig, 'Fig08_optimised_index_map.png')

# Fig09 CWT scalogram of mean AUC
SC = T('feature_screening_all.csv'); cw = SC[(SC.branch == 'raw') & (SC.family == 'CWT')].copy()
cw['wl'] = cw.feature.str.extract(r'WF(\d+)_').astype(int); cw['s'] = cw.feature.str.extract(r'_s(\d)').astype(int)
Pm = cw.pivot(index='s', columns='wl', values='score')
fig, ax = plt.subplots(figsize=(11, 2.8))
im = ax.imshow(Pm.to_numpy(), aspect='auto', cmap='viridis', vmin=0.5, vmax=1, extent=[395, 2405, 8.5, 0.5])
ax.set(xlabel='Wavelength (nm)', ylabel='Scale 2^k', title='CWT (Mexican hat) coefficients: mean AUC over dates (0 = sign not consistent)')
ax.set_yticks(range(1, 9)); ax.grid(False); plt.colorbar(im, ax=ax, pad=0.01)
save(fig, 'Fig09_CWT_scalogram.png')

# Fig10 design controls on the features
BC = T('block_control.csv'); MC = T('matched_control_effects.csv')
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
order = ['REF', 'FD1', 'FD2', 'FD3', 'CR', 'VI', 'RE', 'CWT']
dat1 = [BC[BC.family == f].abs_d_control_vs_inoculated.dropna() for f in order]
dat2 = [BC[BC.family == f].max_abs_d_between_blocks.dropna() for f in order]
pos = np.arange(len(order))
b1 = ax[0].boxplot(dat1, positions=pos - 0.18, widths=0.32, patch_artist=True, showfliers=False)
b2 = ax[0].boxplot(dat2, positions=pos + 0.18, widths=0.32, patch_artist=True, showfliers=False)
for b, c in ((b1, C4), (b2, '#9E9E9E')):
    for p_ in b['boxes']: p_.set_facecolor(c); p_.set_alpha(0.7)
ax[0].set_xticks(pos); ax[0].set_xticklabels(order); ax[0].set_ylabel('|effect size d|')
ax[0].set_title('(a) Control vs inoculated (red) vs largest block-to-block contrast (grey)', fontsize=8.5)
mc = MC.groupby(['family', 'date']).apply(lambda g: (g.p < 0.05).mean() * 100).unstack().reindex(order)[DL]
mc.plot.bar(ax=ax[1], color=DATEC, width=0.8); ax[1].set_ylabel('% of features with matched-control p < 0.05')
ax[1].set_title('(b) Matched-control test, top-ranked features (inoculated minus own control)', fontsize=8.5); ax[1].set_xlabel('')
ax[1].legend(ncol=4, fontsize=7, loc='upper center', bbox_to_anchor=(0.5, -0.08)); ax[1].set_ylim(0, 105)
ax[1].tick_params(axis='x', rotation=0)
save(fig, 'Fig10_design_controls_features.png')

# Fig25 noise and leaf number
QC = T('qc_plot_noise.csv'); QC = QC[QC.branch == 'raw']
fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
for lab, c in (('Healthy', H), ('Diseased', D)):
    s = QC[QC.label == lab]
    ax[0].scatter(s.n_leaves + np.random.default_rng(0).uniform(-0.25, 0.25, len(s)), s.noise_sd * 1e4, c=c, s=14, alpha=0.7, label=lab)
nn = np.arange(3, 16); k0 = (QC.noise_sd * np.sqrt(QC.n_leaves)).median() * 1e4
ax[0].plot(nn, k0 / np.sqrt(nn), color='#555', lw=1, ls='--', label='1/√n expectation')
ax[0].set(xlabel='Leaves averaged per plot', ylabel='High-frequency noise SD (x10⁻⁴)', title='(a) Noise of the raw plot averages'); ax[0].legend(fontsize=7)
NS = T('qc_noise_summary.csv'); NS = NS[NS.Branch == 'raw']
x = np.arange(4); ax[1].bar(x - 0.2, NS.Noise_ratio_D_over_H, 0.4, color=C4, label='Observed D/H noise ratio')
ax[1].bar(x + 0.2, NS.Expected_ratio_sqrt_n, 0.4, color='#9E9E9E', label='Expected from leaf numbers')
ax[1].set_xticks(x); ax[1].set_xticklabels(NS.Date); ax[1].axhline(1, color='#888', lw=0.8); ax[1].set_ylim(0.6, 1.1)
ax[1].set_title('(b) Diseased / healthy noise ratio'); ax[1].legend(fontsize=7)
save(fig, 'Fig25_noise_leaf_number.png')

# ------------------------------------------------------------------ results figures (after the CV)
if have('cv_main_summary.csv'):
    from p03_cv import SCENARIOS
    from models import CLF_NAMES
    SUM = T('cv_main_summary.csv')
    BA = SUM.pivot(index='scenario', columns='clf', values='BA_mean').loc[list(SCENARIOS), CLF_NAMES]
    fig, ax = plt.subplots(figsize=(10, 5.4))
    im = ax.imshow(BA.to_numpy(), cmap='YlGn', vmin=max(0.5, BA.min().min() - 0.02), vmax=1)
    for i in range(BA.shape[0]):
        for j in range(BA.shape[1]):
            ax.text(j, i, f'{BA.iat[i, j]:.3f}', ha='center', va='center', fontsize=7, color='white' if BA.iat[i, j] > 0.93 else 'black')
    ax.set_xticks(range(len(CLF_NAMES))); ax.set_xticklabels(CLF_NAMES, rotation=30, ha='right')
    ax.set_yticks(range(len(SCENARIOS))); ax.set_yticklabels([f'{k} {v}' for k, v in SCENARIOS.items()], fontsize=7.5); ax.grid(False)
    plt.colorbar(im, ax=ax, label='Balanced accuracy (mean of 20 x 4-fold)')
    save(fig, 'Fig11_BA_matrix.png')

    CM = T('confusion_matrices.csv')
    fig, axs = plt.subplots(1, len(CM), figsize=(4 * len(CM), 3.4))
    for ax, (_, r) in zip(np.atleast_1d(axs), CM.iterrows()):
        mat = np.array([[r.TN, r.FP], [r.FN, r.TP]])
        ax.imshow(mat / mat.sum(1, keepdims=True), cmap='Greens', vmin=0, vmax=1); ax.grid(False)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f'{int(mat[i, j])}\n({100 * mat[i, j] / mat[i].sum():.1f} %)', ha='center', va='center', fontsize=9)
        ax.set_xticks([0, 1]); ax.set_xticklabels(['Healthy', 'Diseased']); ax.set_yticks([0, 1]); ax.set_yticklabels(['Healthy', 'Diseased'])
        ax.set_xlabel('Predicted'); ax.set_ylabel('Observed'); ax.set_title(f'{r.Role}\n{r.Pipeline[:48]}', fontsize=8)
    save(fig, 'Fig13_confusion_matrices.png')

    RC = T('roc_curves.csv')
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    for k, c in zip([c for c in RC.columns if c.startswith('TPR_')], [C4, C3, H]):
        role = k[4:]
        ax.plot(RC.FPR, RC[k], color=c, lw=1.6, label=role)
        ax.fill_between(RC.FPR, RC[k] - RC['SD_' + role], np.minimum(1, RC[k] + RC['SD_' + role]), color=c, alpha=0.12, lw=0)
    ax.plot([0, 1], [0, 1], color='#999', ls='--', lw=0.8); ax.set(xlabel='False-positive rate', ylabel='True-positive rate', title='ROC (mean ± SD over repeats)')
    ax.legend(fontsize=7)
    save(fig, 'Fig14_ROC.png')

    OP = T('oof_predictions.csv')
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
    for k, dt in enumerate(DATE_ORDER):
        for lab, c, off in (('Healthy', H, -0.15), ('Diseased', D, 0.15)):
            s = OP[(OP.date == dt) & (OP.label == lab)]['Best overall_score']
            ax[0].scatter(np.full(len(s), k + off) + np.random.default_rng(k).uniform(-0.07, 0.07, len(s)), s, c=c, s=12, alpha=0.7, label=lab if k == 0 else None)
    ax[0].axhline(0, color='#888', lw=0.8); ax[0].set_xticks(range(4)); ax[0].set_xticklabels(DL)
    ax[0].set(ylabel='Out-of-fold decision score', title='(a) Plot scores by date (best pipeline)'); ax[0].legend(fontsize=7)
    PG = T('oof_vote_by_date_inoc.csv'); dd = PG[PG.label == 'Diseased']
    for k, inoc in enumerate(['D1', 'D2', 'D3', 'D4']):
        ax[1].plot(range(4), dd[inoc], marker='o', color=[C4, D, C3, H][k], label=f'Inoculation {inoc}')
    hh = PG[PG.label == 'Healthy'][['D1', 'D2', 'D3', 'D4']].mean(1)
    ax[1].plot(range(4), hh, color='#555', ls='--', marker='x', label='Controls (all)')
    ax[1].set_xticks(range(4)); ax[1].set_xticklabels(DL); ax[1].set_ylim(-0.02, 1.02)
    ax[1].set(ylabel='Share of plots classified diseased', title='(b) Disease call by date and inoculation timing'); ax[1].legend(fontsize=7)
    save(fig, 'Fig16_oof_progression.png')

    FIN = T('final_features.csv'); C = T('final_features_corr.csv').set_index('Unnamed: 0')
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw=dict(width_ratios=[1, 1.1]))
    g = FIN.iloc[::-1]
    ax[0].barh([f[:30] for f in g.Feature], g.Perm_importance_BA, xerr=g.Perm_importance_SD, color=C4, alpha=0.85)
    ax[0].set(xlabel='Permutation importance (drop in BA)', title='(a) Final feature set (S10, all data)'); ax[0].tick_params(axis='y', labelsize=7)
    im = ax[1].imshow(C.to_numpy(), cmap='RdBu_r', vmin=-1, vmax=1); ax[1].grid(False)
    n = len(C)
    for i in range(n):
        for j in range(n):
            ax[1].text(j, i, f'{C.iat[i, j]:.2f}', ha='center', va='center', fontsize=6.5)
    ax[1].set_xticks(range(n)); ax[1].set_xticklabels([c[:14] for c in C.columns], rotation=45, ha='right', fontsize=6.5)
    ax[1].set_yticks(range(n)); ax[1].set_yticklabels([c[:14] for c in C.columns], fontsize=6.5)
    ax[1].set_title('(b) Pearson correlation of the final features'); plt.colorbar(im, ax=ax[1], fraction=0.04)
    save(fig, 'Fig17_final_features.png')

if have('E5_permutation.csv'):
    E5 = T('E5_permutation.csv')
    fig, axs = plt.subplots(1, E5.groupby(['scenario', 'clf']).ngroups, figsize=(12, 3.2))
    for ax, ((sc, c), g) in zip(np.atleast_1d(axs), E5.groupby(['scenario', 'clf'])):
        ax.hist(g[g.perm > 0].BA, bins=20, color='#9E9E9E'); ax.axvline(g[g.perm == 0].BA.iloc[0], color=C4, lw=2)
        ax.set(title=f'{sc} + {c}', xlabel='Balanced accuracy'); ax.set_xlim(0.2, 1.0)
    np.atleast_1d(axs)[0].set_ylabel('Permutations')
    save(fig, 'Fig19_permutation_test.png')
print('figures done')
