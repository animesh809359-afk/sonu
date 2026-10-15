"""Publication-style figures (PNG, 300 dpi) for the thesis; heat maps are also used in the slides."""
import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
from common import *

T = lambda n: pd.read_csv(os.path.join(TAB, n))
H, D, C3, C4 = '#2E7D32', '#D08A00', '#2A6FB0', '#B03A2E'
DATEC = [C3, H, D, C4]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': '#E6E6E6', 'grid.linewidth': 0.6, 'axes.edgecolor': '#888888',
                     'legend.frameon': False, 'savefig.dpi': 300, 'savefig.bbox': 'tight'})
REGIONS = [(400, 700, 'VIS'), (700, 750, 'RE'), (750, 1300, 'NIR'), (1300, 1900, 'SWIR-1'), (1900, 2400, 'SWIR-2')]


def save(fig, name):
    fig.savefig(os.path.join(FIG, name)); plt.close(fig)


def shade(ax):
    for a, b, lab in REGIONS:
        ax.axvspan(a, b, color='#000000', alpha=0.03 if REGIONS.index((a, b, lab)) % 2 else 0.0, lw=0)


# Fig 1 mean spectra
S = T('spectra_mean_class.csv'); w = S['Wavelength_nm']
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
for lab, c in [('Healthy', H), ('Diseased', D)]:
    ax[0].plot(w, S[f'{lab}_mean'], color=c, lw=1.6, label=lab)
    ax[0].fill_between(w, S[f'{lab}_mean'] - S[f'{lab}_SD'], S[f'{lab}_mean'] + S[f'{lab}_SD'], color=c, alpha=0.15, lw=0)
ax[0].set(xlabel='Wavelength (nm)', ylabel='Reflectance', title='(a) Mean reflectance ± SD'); ax[0].legend()
ax[1].plot(w, S['Difference_D-H'], color='#333333', lw=1.4); ax[1].axhline(0, color='#999999', lw=0.8)
ax[1].set(xlabel='Wavelength (nm)', ylabel='Diseased − Healthy', title='(b) Difference spectrum')
ax[2].plot(w, S['Ratio_D/H'], color='#333333', lw=1.4); ax[2].axhline(1, color='#999999', lw=0.8)
ax[2].set(xlabel='Wavelength (nm)', ylabel='Diseased / Healthy', title='(c) Ratio spectrum')
for a in ax: shade(a)
save(fig, 'Fig01_mean_spectra.png')

# Fig 2 by date
S = T('spectra_mean_by_date.csv')
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
for k, dt in enumerate(DATE_ORDER):
    nm = DATE_LABEL[dt]
    ax[0].plot(S['Wavelength_nm'], S[f'{nm}_H'], color=DATEC[k], lw=1.3, label=f'{nm} H')
    ax[0].plot(S['Wavelength_nm'], S[f'{nm}_D'], color=DATEC[k], lw=1.3, ls='--', label=f'{nm} D')
    ax[1].plot(S['Wavelength_nm'], S[f'{nm}_Diff'], color=DATEC[k], lw=1.4, label=nm)
ax[0].set(xlabel='Wavelength (nm)', ylabel='Reflectance', title='(a) Healthy (solid) and diseased (dashed) by date'); ax[0].legend(ncol=2, fontsize=7)
ax[1].axhline(0, color='#999999', lw=0.8); ax[1].set(xlabel='Wavelength (nm)', ylabel='Diseased − Healthy', title='(b) Difference spectra by date'); ax[1].legend()
save(fig, 'Fig02_spectra_by_date.png')

# Fig 3 derivatives
S = T('spectra_mean_class.csv')
fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
for lab, c in [('Healthy', H), ('Diseased', D)]:
    ax[0].plot(S['Wavelength_nm'], S[f'FD_{lab}'], color=c, lw=1.4, label=lab)
    ax[1].plot(S['Wavelength_nm'], S[f'SD2_{lab}'], color=c, lw=1.4, label=lab)
ax[0].set(xlabel='Wavelength (nm)', ylabel='dR/dλ', title='(a) First-derivative spectra'); ax[0].legend()
ax[1].set(xlabel='Wavelength (nm)', ylabel='d²R/dλ²', title='(b) Second-derivative spectra')
ax[0].set_xlim(400, 1400); ax[1].set_xlim(400, 1400)
save(fig, 'Fig03_derivative_spectra.png')

# Fig 4 band-wise statistics
B = T('bandwise_statistics.csv')
fig, ax = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
ax[0].plot(B['Wavelength_nm'], B['Cohen_d'], color='#333333', lw=1.4); ax[0].axhline(0, color='#999999', lw=0.8)
sig = B['q_FDR'] < 0.05
ax[0].fill_between(B['Wavelength_nm'], 0, B['Cohen_d'], where=sig, color=D, alpha=0.35, lw=0, label='FDR q < 0.05')
ax[0].set(ylabel="Cohen's d (D − H)", title="(a) Effect size per band (plot-date means, n = 192)"); ax[0].legend()
ax[1].plot(B['Wavelength_nm'], B['Point_biserial_r_spectrum'], color=C3, lw=1.4, label='spectrum level')
ax[1].plot(B['Wavelength_nm'], B['Point_biserial_r_plotdate'], color=C4, lw=1.4, label='plot-date level')
ax[1].axhline(0, color='#999999', lw=0.8); ax[1].set(ylabel='Point-biserial r', title='(b) Correlation spectrum'); ax[1].legend()
ax[2].plot(B['Wavelength_nm'], B['JM_distance'], color=H, lw=1.4, label='Reflectance')
ax[2].plot(B['Wavelength_nm'], B['FD_JM'], color=D, lw=1.4, label='First derivative')
ax[2].set(xlabel='Wavelength (nm)', ylabel='J-M distance (0-2)', title='(c) Jeffries-Matusita separability'); ax[2].legend()
save(fig, 'Fig04_bandwise_statistics.png')

# Fig 5 PCA / t-SNE
P = T('pca_tsne_scores.csv'); V = T('pca_variance.csv')
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
for lab, c in [('Healthy', H), ('Diseased', D)]:
    m = P['label'] == lab
    ax[0].scatter(P.loc[m, 'PC1'], P.loc[m, 'PC2'], s=6, color=c, alpha=0.5, label=lab, lw=0)
    ax[2].scatter(P.loc[m, 'tSNE1'], P.loc[m, 'tSNE2'], s=6, color=c, alpha=0.5, label=lab, lw=0)
for k, dt in enumerate(DATE_ORDER):
    m = P['date'] == dt
    ax[1].scatter(P.loc[m, 'PC1'], P.loc[m, 'PC2'], s=6, color=DATEC[k], alpha=0.5, label=DATE_LABEL[dt], lw=0)
v1, v2 = V['Explained_variance_pct'][:2]
for a, t in zip(ax[:2], ['(a) PCA coloured by class', '(b) PCA coloured by date']):
    a.set(xlabel=f'PC1 ({v1:.1f}%)', ylabel=f'PC2 ({v2:.1f}%)', title=t); a.legend(markerscale=3)
ax[2].set(xlabel='t-SNE 1', ylabel='t-SNE 2', title='(c) t-SNE coloured by class'); ax[2].legend(markerscale=3)
save(fig, 'Fig05_PCA_tSNE.png')

# Fig 6 PERMANOVA
PM = T('permanova.csv')
fig, ax = plt.subplots(figsize=(6, 3.2))
ax.barh(PM['Term'][::-1], PM['R2_partial_pct'][::-1], color=[H if t == 'Disease' else '#7A7A7A' for t in PM['Term'][::-1]])
for i, (r2, p) in enumerate(zip(PM['R2_partial_pct'][::-1], PM['p_perm'][::-1])):
    ax.text(r2 + 0.3, i, f'{r2:.1f}%' + ('' if pd.isna(p) else f'  (p = {p:.3f})'), va='center', fontsize=8)
ax.set(xlabel='Marginal variance explained (%)', title='PERMANOVA on SNV spectra (plot-date means)')
save(fig, 'Fig06_PERMANOVA.png')

# Fig 7 VI ranking
VR = T('vi_ranking.csv').head(20)
fig, ax = plt.subplots(figsize=(6.5, 5))
ax.barh(VR['Index'][::-1], VR['AUC'][::-1], color=[H if s else '#9E9E9E' for s in VR['Sign_consistent_all_dates'][::-1]])
ax.axvline(0.5, color='#999999', lw=0.8); ax.set_xlim(0.45, max(0.8, VR['AUC'].max() + 0.03))
ax.set(xlabel='AUC (healthy vs diseased)', title='Top-20 published indices (green = same direction on all dates)')
save(fig, 'Fig07_VI_ranking.png')

# Fig 8 NDSI map
mat = np.load(os.path.join(CACHE, 'ndsi_matrix.npy'))
top = T('ndsi_top_pairs.csv').iloc[0]
fig, ax = plt.subplots(figsize=(6.2, 5.2))
im = ax.imshow(np.triu(mat), origin='lower', extent=[400, 2400, 400, 2400], cmap='YlGn', vmin=0)
ax.plot(top['Band_j_nm'], top['Band_i_nm'], marker='o', mfc='none', mec=C4, ms=10, mew=1.6)
ax.annotate(f"best: ND(R{int(top['Band_i_nm'])}, R{int(top['Band_j_nm'])})", (top['Band_j_nm'], top['Band_i_nm']),
            xytext=(900, 2150), fontsize=8, arrowprops=dict(arrowstyle='->', color=C4))
ax.set(xlabel='Band j (nm)', ylabel='Band i (nm)', title='Normalised-difference index search\n(mean |Cohen d| across dates, sign-consistent)')
fig.colorbar(im, ax=ax, shrink=0.8, label='|d|')
save(fig, 'Fig08_NDSI_map.png')

# Fig 9 CWT scalogram
CW = T('cwt_abs_d_scalogram.csv').set_index(T('cwt_abs_d_scalogram.csv').columns[0])
fig, ax = plt.subplots(figsize=(9, 3.2))
im = ax.imshow(CW.to_numpy().T, aspect='auto', origin='lower', extent=[400, 2400, 0.5, 8.5], cmap='YlGn')
ax.set(xlabel='Wavelength (nm)', ylabel='Wavelet scale (2^k)', title="CWT sensitivity: |Cohen d| of wavelet coefficients (Mexican hat)")
fig.colorbar(im, ax=ax, label='|d|')
save(fig, 'Fig09_CWT_scalogram.png')


def summ(df, by, metric='BA'):
    g = df.groupby(by)[metric]
    return g.mean().rename('mean').to_frame().join(g.std().rename('sd')).reset_index()


# Fig 10 preprocessing
if os.path.exists(os.path.join(TAB, 'E1_preprocessing_reps.csv')):
    E1 = summ(T('E1_preprocessing_reps.csv'), ['variant', 'clf'])
    vs = ['Reflectance (SG)', 'SNV', 'MSC', 'First derivative (SG)', 'Date normalisation', 'Date normalisation + SNV']
    clfs = ['LDA', 'PLS-DA', 'LR', 'SVM']
    fig, ax = plt.subplots(figsize=(10, 3.6)); x = np.arange(len(vs))
    for k, c in enumerate(clfs):
        sub = E1[E1['clf'] == c].set_index('variant').loc[vs]
        ax.bar(x + (k - 1.5) * 0.2, sub['mean'], 0.18, yerr=sub['sd'], color=[C3, H, D, C4][k], label=c, capsize=2)
    ax.set_xticks(x, vs, fontsize=8); ax.set_ylim(0.5, 1); ax.set(ylabel='Balanced accuracy', title='E1: preprocessing comparison (full spectrum, 10 × 4-fold plot-grouped CV)'); ax.legend(ncol=4)
    save(fig, 'Fig10_preprocessing.png')

# Fig 11 BA matrix
if os.path.exists(os.path.join(TAB, 'cv_ba_matrix.csv')):
    BM = T('cv_ba_matrix.csv').set_index(T('cv_ba_matrix.csv').columns[0])
    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(BM.to_numpy(), cmap='YlGn', vmin=0.5, vmax=1)
    ax.set_xticks(range(BM.shape[1]), BM.columns, rotation=0); ax.set_yticks(range(BM.shape[0]), BM.index, fontsize=8)
    for i in range(BM.shape[0]):
        for j in range(BM.shape[1]):
            ax.text(j, i, f'{BM.iat[i, j]:.3f}', ha='center', va='center', fontsize=7, color='white' if BM.iat[i, j] > 0.85 else '#222222')
    ax.grid(False); ax.set_title('Balanced accuracy, 25 × 4-fold nested plot-grouped CV (mean of 25 repeats)')
    fig.colorbar(im, ax=ax, shrink=0.8)
    save(fig, 'Fig11_BA_matrix.png')
    BP = T('cv_best_per_scenario.csv')
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.bar(BP['scenario'], BP['BA_mean'], yerr=BP['BA_SD'], color=H, capsize=3)
    for i, (b, c) in enumerate(zip(BP['BA_mean'], BP['clf'])):
        ax.text(i, b + 0.02, f'{b:.3f}\n{c}', ha='center', fontsize=7)
    ax.set_ylim(0.5, 1.05); ax.set(ylabel='Balanced accuracy (mean ± SD)', title='Best classifier per feature scenario')
    save(fig, 'Fig12_best_per_scenario.png')
    CM = T('confusion_matrices.csv')
    fig, axs = plt.subplots(1, 4, figsize=(13, 3))
    for a, (_, r) in zip(axs, CM.iterrows()):
        m = np.array([[r['TN'], r['FP']], [r['FN'], r['TP']]])
        a.imshow(m, cmap='Greens'); a.grid(False)
        for i in range(2):
            for j in range(2):
                a.text(j, i, int(m[i, j]), ha='center', va='center', fontsize=11, color='white' if m[i, j] > m.max() / 2 else '#222')
        a.set_xticks([0, 1], ['Pred H', 'Pred D']); a.set_yticks([0, 1], ['True H', 'True D'])
        a.set_title(f"{r['Role']}\n{r['Level']}", fontsize=8)
    save(fig, 'Fig13_confusion_matrices.png')
    ROC = T('roc_curves.csv')
    fig, ax = plt.subplots(figsize=(4.2, 4))
    for col, c in zip([c for c in ROC.columns if c.startswith('TPR')], [H, D]):
        ax.plot(ROC['FPR'], ROC[col], color=c, lw=1.8, label=col.replace('TPR_', ''))
    ax.plot([0, 1], [0, 1], color='#999999', lw=0.8, ls='--'); ax.set(xlabel='False-positive rate', ylabel='True-positive rate', title='ROC (representative repeat)'); ax.legend()
    save(fig, 'Fig14_ROC.png')
    FI = T('final_features.csv')
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.barh(FI['Feature'][::-1], FI['Permutation_importance_BA'][::-1], xerr=FI['Permutation_importance_SD'][::-1], color=H, capsize=2)
    ax.set(xlabel='Drop in balanced accuracy when permuted', title='Final robust feature set: permutation importance (SVM)')
    save(fig, 'Fig15_final_feature_importance.png')
    LC = T('lr_coefficients.csv')
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(LC['Wavelength_nm'], LC['LR_std_coefficient'], color='#333333', lw=1.3); ax.axhline(0, color='#999', lw=0.8)
    ax.set(xlabel='Wavelength (nm)', ylabel='Standardised coefficient', title='Full-spectrum logistic regression coefficients (SNV spectra)')
    save(fig, 'Fig16_LR_coefficients.png')
    SG = T('subgroup_performance.csv')
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.2), sharey=True)
    for a, fac in zip(axs, ['Date', 'Variety', 'Stage']):
        sub = SG[SG['Factor'] == fac]
        roles = sub['Role'].unique(); levs = sub['Level'].unique(); x = np.arange(len(levs))
        for k, rl in enumerate(roles):
            s2 = sub[sub['Role'] == rl].set_index('Level').loc[levs]
            a.bar(x + (k - 0.5) * 0.38, s2['BA'], 0.36, color=[H, D][k], label=rl)
        a.set_xticks(x, levs); a.set_title(f'By {fac.lower()}'); a.set_ylim(0.5, 1)
    axs[0].set_ylabel('Balanced accuracy'); axs[0].legend(fontsize=7)
    save(fig, 'Fig17_subgroup_performance.png')

if os.path.exists(os.path.join(TAB, 'E2_transfer_reps.csv')):
    E2 = T('E2_transfer_reps.csv'); E2['pipe'] = E2['scenario'] + '-' + E2['clf']
    s = E2.groupby(['kind', 'level', 'pipe'])['BA'].mean().reset_index()
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.2), sharey=True)
    for a, kind in zip(axs, ['Date', 'Variety', 'Stage']):
        sub = s[s['kind'] == kind]; levs = sub['level'].unique(); pipes = sub['pipe'].unique(); x = np.arange(len(levs))
        for k, p in enumerate(pipes):
            v = sub[sub['pipe'] == p].set_index('level').loc[levs]['BA']
            a.bar(x + (k - 1) * 0.27, v, 0.25, color=[C3, H, D][k], label=p)
        a.set_xticks(x, [DATE_LABEL.get(l, l) for l in levs], fontsize=8); a.set_title(f'Leave-one-{kind.lower()}-out'); a.set_ylim(0.4, 1)
    axs[0].set_ylabel('Balanced accuracy'); axs[0].legend(fontsize=7)
    save(fig, 'Fig18_transfer.png')
if os.path.exists(os.path.join(TAB, 'E4_learning_curve_reps.csv')):
    E4 = T('E4_learning_curve_reps.csv'); E4['pipe'] = E4['scenario'] + '-' + E4['clf']
    s = E4.groupby(['pipe', 'n_train_plots'])['BA'].agg(['mean', 'std']).reset_index()
    fig, ax = plt.subplots(figsize=(5, 3.4))
    for k, p in enumerate(s['pipe'].unique()):
        sub = s[s['pipe'] == p]
        ax.errorbar(sub['n_train_plots'], sub['mean'], yerr=sub['std'], color=[H, D][k], marker='o', lw=1.6, capsize=3, label=p)
    ax.set(xlabel='Number of training plots', ylabel='Balanced accuracy', title='E4: learning curve'); ax.legend()
    save(fig, 'Fig19_learning_curve.png')
if os.path.exists(os.path.join(TAB, 'E5_sensor_reps.csv')):
    E5 = summ(T('E5_sensor_reps.csv'), ['sensor', 'clf'])
    fig, ax = plt.subplots(figsize=(6, 3.2)); sens = E5['sensor'].unique(); x = np.arange(len(sens))
    for k, c in enumerate(['LR', 'SVM', 'RF']):
        sub = E5[E5['clf'] == c].set_index('sensor').loc[sens]
        ax.bar(x + (k - 1) * 0.27, sub['mean'], 0.25, yerr=sub['sd'], color=[C3, H, D][k], label=c, capsize=2)
    ax.set_xticks(x, sens, fontsize=8); ax.set_ylim(0.4, 1); ax.set(ylabel='Balanced accuracy', title='E5: simulated multispectral sensors'); ax.legend()
    save(fig, 'Fig20_sensors.png')
print('figures written to', FIG)

if os.path.exists(os.path.join(TAB, 'E7_ofc_reps.csv')):
    E7 = T('E7_ofc_reps.csv').groupby(['feature_set', 'clf'])['BA'].agg(['mean', 'std']).reset_index()
    sets = ['OFC-LDA', 'OFC-kNN', 'OFC-SVM', 'All DSFs', 'Full spectrum (SNV)']; x = np.arange(len(sets))
    fig, ax = plt.subplots(figsize=(8, 3.4))
    for k, c in enumerate(['LDA', 'kNN', 'SVM']):
        sub = E7[E7.clf == c].set_index('feature_set').loc[sets]
        ax.bar(x + (k - 1) * 0.27, sub['mean'], 0.25, yerr=sub['std'], color=[C3, H, D][k], label=c, capsize=2)
    ax.set_xticks(x, sets, fontsize=8); ax.set_ylim(0.6, 1); ax.set(ylabel='Balanced accuracy', title='E7: optimal feature combinations (Tian et al., 2021)'); ax.legend(ncol=3)
    save(fig, 'Fig21_OFC_E7.png')
if os.path.exists(os.path.join(TAB, 'E8_fs_reps.csv')):
    E8 = T('E8_fs_reps.csv'); E8['k'] = E8['k'].astype(str)
    ms = ['SVM-RFE', 'LASSO', 'CARS', 'ReliefF', 'SFFS (QDA)', 'Consensus (Borda)', 'Robust selection + SFFS-LDA (S8)', 'OFC-SVM (Tian et al., 2021)']
    lab = ['SVM-RFE', 'LASSO', 'CARS', 'ReliefF', 'SFFS-QDA', 'Borda', 'Robust S8', 'OFC-SVM']
    A8 = E8[(E8.variant == 'all features') & E8.k.isin(['10', 'native'])].groupby(['method', 'clf'])['BA'].mean()
    fig, ax = plt.subplots(figsize=(9, 3.4)); x = np.arange(len(ms))
    for k, c in enumerate(['QDA', 'SVM', 'RF']):
        ax.bar(x + (k - 1) * 0.27, [A8.get((m, c), np.nan) for m in ms], 0.25, color=[C3, H, D][k], label=c)
    ax.set_xticks(x, lab, fontsize=8); ax.set_ylim(0.6, 1); ax.set(ylabel='Balanced accuracy', title='E8: published selectors vs this study (10 features or native size)'); ax.legend(ncol=3)
    save(fig, 'Fig22_selectors_E8.png')
    J = E8[E8.k.isin(['10', 'native']) & (E8.clf == 'SVM') & E8.method.isin(['SVM-RFE', 'SFFS (QDA)', 'Robust selection + SFFS-LDA (S8)'])].groupby(['method', 'variant'])['BA'].mean().unstack()
    fig, ax = plt.subplots(figsize=(5.5, 3.2)); x = np.arange(len(J))
    ax.bar(x - 0.2, J['all features'], 0.38, color=H, label='All features'); ax.bar(x + 0.2, J['join bands excluded'], 0.38, color='#7A7A7A', label='Join bands excluded')
    ax.set_xticks(x, [i.replace('Robust selection + SFFS-LDA (S8)', 'Robust S8') for i in J.index]); ax.set_ylim(0.6, 1); ax.set(ylabel='Balanced accuracy (SVM)', title='E8: detector-join check'); ax.legend()
    save(fig, 'Fig23_detector_join_check.png')
print('extra figures done')
