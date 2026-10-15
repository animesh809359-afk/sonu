"""Collect every table needed by the slide builder into one JSON file."""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from s04_cv import SCENARIOS

T = lambda n: pd.read_csv(os.path.join(TAB, n))
have = lambda n: os.path.exists(os.path.join(TAB, n))
D = {}


def rec(df, nd=4):
    return json.loads(df.round(nd).to_json(orient='records'))


M = pd.read_csv(os.path.join(CACHE, 'meta.csv'))
Mc = pd.read_csv(os.path.join(CACHE, 'meta_clean.csv'))
D['design'] = rec(M.assign(Date=M['date'].map(DATE_LABEL)).pivot_table(index='Date', columns='label', values='spec_uid', aggfunc='count')
                  .reindex([DATE_LABEL[d] for d in DATE_ORDER])[['Healthy', 'Diseased']].reset_index())
D['design_stage'] = rec(M.pivot_table(index='stage', columns='label', values='spec_uid', aggfunc='count').reindex(STAGE_ORDER)[['Healthy', 'Diseased']].reset_index())
D['n_raw'] = int(len(M)); D['n_clean'] = int(len(Mc)); D['n_h'] = int((M['y'] == 0).sum()); D['n_d'] = int((M['y'] == 1).sum())
D['n_h_clean'] = int((Mc['y'] == 0).sum()); D['n_d_clean'] = int((Mc['y'] == 1).sum())
D['qc_noise'] = rec(T('qc_noise.csv'), 5)
qs = T('qc_summary.csv'); qs.columns = ['k', 'v']; D['qc'] = {k: float(v) for k, v in zip(qs['k'], qs['v'])}
S = T('spectra_mean_class.csv'); D['spec'] = {c: S[c].round(6).tolist() for c in S.columns}
for fac in ['date', 'variety', 'stage']:
    S = T(f'spectra_mean_by_{fac}.csv'); D[f'spec_{fac}'] = {c: S[c].round(6).tolist() for c in S.columns}
B = T('bandwise_statistics.csv'); D['bands'] = {c: B[c].round(5).tolist() for c in ['Wavelength_nm', 'Cohen_d', 'q_FDR', 'Point_biserial_r_spectrum', 'Point_biserial_r_plotdate', 'JM_distance', 'FD_JM', 'FD_Cohen_d']}
D['regions'] = rec(T('sensitive_regions.csv'), 3)
CDd = T('bandwise_cohen_d_by_date.csv'); D['d_by_date'] = {c: CDd[c].round(4).tolist() for c in CDd.columns}
ER = T('red_edge_parameters.csv'); D['rededge'] = rec(ER, 5)
D['pca_var'] = rec(T('pca_variance.csv'), 2); D['pca_eta'] = rec(T('pca_eta2.csv'), 3)
P = T('pca_tsne_scores.csv')
pdm = P.groupby('plot_date').agg(PC1=('PC1', 'mean'), PC2=('PC2', 'mean'), tSNE1=('tSNE1', 'mean'), tSNE2=('tSNE2', 'mean'), label=('label', 'first'), date=('date', 'first')).reset_index()
D['pca_pd'] = rec(pdm, 3)
rng = np.random.default_rng(0); sub = P.iloc[rng.choice(len(P), 900, replace=False)]
D['tsne'] = rec(sub[['tSNE1', 'tSNE2', 'label', 'date', 'PC1', 'PC2']], 3)
D['permanova'] = rec(T('permanova.csv'), 4)
D['lmm'] = rec(T('mixed_models_features.csv').head(12), 4)
D['vi'] = rec(T('vi_ranking.csv'), 4)
D['ndsi_top'] = rec(T('ndsi_top_pairs.csv'), 4)
D['similarity'] = rec(T('class_similarity_by_date.csv'), 4)
cw = pd.read_csv(os.path.join(TAB, 'cwt_abs_d_scalogram.csv'), index_col=0)
st = cw.stack().sort_values(ascending=False).head(8).reset_index(); st.columns = ['wl', 'scale', 'd']
D['cwt_top'] = rec(st, 3)
for fn, key in [('E1_preprocessing_reps.csv', 'E1'), ('E2_transfer_reps.csv', 'E2'), ('E3_metadata_reps.csv', 'E3'),
                ('E4_learning_curve_reps.csv', 'E4'), ('E5_sensor_reps.csv', 'E5'), ('E6_outlier_sensitivity_reps.csv', 'E6')]:
    if have(fn):
        E = T(fn)
        g = [c for c in ['kind', 'level', 'variant', 'scenario', 'clf', 'inputs', 'n_train_plots', 'sensor', 'data'] if c in E.columns]
        s = E.groupby(g, sort=False)[['BA', 'MCC', 'Kappa', 'MacroF1', 'ROC_AUC', 'Sensitivity', 'Specificity', 'OA']].mean()
        s['BA_SD'] = E.groupby(g, sort=False)['BA'].std()
        D[key] = rec(s.reset_index(), 4)
if have('cv_main_summary.csv'):
    SUM = T('cv_main_summary.csv')
    D['summary'] = rec(SUM[['scenario', 'clf', 'BA_mean', 'BA_SD', 'BA_CI95_low', 'BA_CI95_high', 'OA_mean', 'Sensitivity_mean', 'Specificity_mean',
                            'MacroF1_mean', 'Kappa_mean', 'MCC_mean', 'ROC_AUC_mean', 'PR_AUC_Healthy_mean']], 4)
    D['scenarios'] = SCENARIOS
    D['best_per_scenario'] = rec(T('cv_best_per_scenario.csv'), 4)
    D['best_per_clf'] = rec(T('cv_best_per_classifier.csv'), 4)
    D['best'] = rec(T('best_pipelines.csv'), 4)
    D['friedman_c'] = rec(T('friedman_classifiers.csv'), 3); D['friedman_s'] = rec(T('friedman_scenarios.csv'), 3)
    D['friedman'] = rec(T('friedman_tests.csv'), 5); D['ttests'] = rec(T('corrected_ttests.csv'), 5)
    D['cm'] = rec(T('confusion_matrices.csv'), 2); D['roc'] = rec(T('roc_curves.csv'), 4)
    D['plotlevel'] = rec(T('cv_main_summary_plotdate.csv')[['scenario', 'clf', 'BA_mean', 'BA_SD', 'MCC_mean', 'Sensitivity_mean', 'Specificity_mean', 'Kappa_mean']], 4)
    D['subgroups'] = rec(T('subgroup_performance.csv'), 4)
    FR = T('selection_frequency.csv'); D['selfreq'] = rec(FR.groupby('scenario').head(8), 2)
    D['median_nfeat'] = {k: float(v) for k, v in FR.groupby('scenario')['Median_n_features'].first().items()}
    BF = T('band_selection_frequency.csv'); D['bandfreq'] = {c: BF[c].round(2).tolist() for c in BF.columns}
    D['final'] = rec(T('final_features.csv'), 4); D['final_jm'] = rec(T('final_features_JM.csv'), 4)
    LC = T('lr_coefficients.csv'); D['lrcoef'] = {c: LC[c].round(4).tolist() for c in LC.columns}
    D['hyper'] = rec(T('hyperparameters.csv'), 3)
if have('E7_ofc_reps.csv'):
    E7 = T('E7_ofc_reps.csv')
    g = E7.groupby(['feature_set', 'clf'], sort=False)
    s7 = g[['BA', 'MCC', 'Kappa', 'MacroF1', 'ROC_AUC', 'Sensitivity', 'Specificity', 'median_n_features']].mean()
    s7['BA_SD'] = g['BA'].std()
    D['E7'] = rec(s7.reset_index(), 4)
    D['E7_final'] = rec(T('E7_ofc_final_sets.csv'), 4)
    D['E7_date'] = rec(T('E7_ofc_by_date.csv'), 4)
D['refs'] = rec(pd.read_csv(os.path.join(ROOT, 'scripts', 'references.csv')))
json.dump(D, open(os.path.join(ROOT, 'cache', 'ppt_data.json'), 'w'))
print('exported', len(D), 'keys')
