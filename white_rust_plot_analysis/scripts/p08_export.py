"""Collect every table needed by the slide builder into cache/ppt_data.json."""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcommon import *
from p03_cv import SCENARIOS

T = lambda n: pd.read_csv(os.path.join(TAB, n))
have = lambda n: os.path.exists(os.path.join(TAB, n))
DL = [DATE_LABEL[d] for d in DATE_ORDER]
METS = ['BA', 'OA', 'Sensitivity', 'Specificity', 'MacroF1', 'Kappa', 'MCC', 'ROC_AUC']
D = {}


def rec(df, nd=4):
    return json.loads(df.round(nd).to_json(orient='records'))


def summ(df, keys, extra=()):
    g = df.groupby(keys, sort=False)
    s = g[METS].mean(); s['BA_SD'] = g['BA'].std()
    for e in extra:
        s[e] = g[e].median()
    return s.reset_index()


M = load_meta()
D['scenarios'] = SCENARIOS
D['family_label'] = FAMILY_LABEL
D['design'] = rec(T('design_by_date.csv'))
D['layout'] = rec(T('design_layout.csv'))
D['stage'] = rec(T('design_stage.csv').assign(Date=lambda d: d['date'].map(DATE_LABEL)))
NS = T('qc_noise_summary.csv'); D['noise'] = rec(NS[NS.Branch == 'raw'], 5)
OU = T('qc_outliers_plot.csv'); D['n_outlier_flags'] = int(OU.flag.sum())
S = T('spectra_mean_by_date_class.csv')
D['spec'] = {'wl': S['Wavelength_nm'].tolist(), **{f'{d}_{c}': S[f'raw_{d}_{c}_mean'].round(5).tolist() for d in DL for c in ('H', 'D')}}
BW = T('bandwise_by_date.csv'); BW = BW[BW.branch == 'raw']
D['diff'] = {d: BW[(BW.family == 'REF') & (BW.date == d)]['diff'].round(5).tolist() for d in DL}
D['fd1_mean'] = {c: BW[(BW.family == 'FD1') & (BW.date == 'All')][c].round(6).tolist() for c in ('mean_H', 'mean_D')}
D['auc_ref'] = {d: BW[(BW.family == 'REF') & (BW.date == d)]['AUC'].round(3).tolist() for d in DL}
D['auc_fd1'] = {d: BW[(BW.family == 'FD1') & (BW.date == d)]['AUC'].round(3).tolist() for d in DL}
RG = T('sensitive_regions.csv'); D['regions'] = rec(RG[RG.branch == 'raw'], 3)
D['pca_var'] = rec(T('pca_variance.csv'), 2); D['eta'] = rec(T('pca_eta2.csv'), 3)
D['permanova'] = rec(T('permanova.csv'), 4)
FS = T('feature_screening_family_summary.csv'); D['fam_summary'] = rec(FS, 3)
TP = T('feature_screening_top10.csv'); D['top'] = rec(TP[['family', 'feature', 'direction', 'n_dates_q05', 'mean_AUC', 'min_AUC'] + [f'AUC_{d}' for d in DL]], 3)
SC = T('feature_screening_all.csv'); SC = SC[SC.branch == 'raw']
VD = pd.read_csv(os.path.join(CACHE, 'vi_definitions.csv')); VD.columns = ['Index', 'Full name', 'Equation', 'Reference', 'Group', 'Source']
vi = SC[SC.family == 'VI'].sort_values('score', ascending=False).head(15).merge(VD, left_on='feature', right_on='Index', how='left')
D['vi_top'] = rec(vi[['feature', 'direction', 'n_dates_q05', 'mean_AUC', 'min_AUC', 'Equation', 'Reference', 'Group'] + [f'AUC_{d}' for d in DL]], 3)
RE = T('red_edge_by_date.csv'); D['re'] = rec(RE, 4)
D['cr_top'] = rec(SC[SC.family == 'CR'].sort_values('score', ascending=False).head(8)[['feature', 'direction', 'n_dates_q05', 'mean_AUC', 'min_AUC']], 3)
IX = T('optimised_index_top_pairs.csv'); D['idx'] = rec(IX[IX.branch == 'raw'], 3)
LM = T('mixed_models.csv'); D['lmm'] = rec(LM.head(12), 4)
D['lmm_n'] = dict(tested=len(LM), sig=int((LM.q_disease < 0.05).sum()), inter=int((LM.q_interaction < 0.05).sum()))
D['lmm_fam'] = rec(LM.groupby('Family').agg(n=('Feature', 'size'), sig=('q_disease', lambda s: int((s < 0.05).sum())), inter=('q_interaction', lambda s: int((s < 0.05).sum())), median_ICC=('ICC_plot', 'median')).reset_index(), 3)
BC = T('block_control.csv')
D['block'] = rec(BC.groupby('family').agg(d_ctrl=('abs_d_control_vs_inoculated', 'median'), d_block=('max_abs_d_between_blocks', 'median'), ratio=('ratio', 'median')).reset_index(), 3)
MC = T('matched_control_effects.csv')
D['matched'] = rec(MC.groupby(['family', 'date']).apply(lambda g: (g.p < 0.05).mean()).unstack()[DL].reset_index(), 3)
IT = T('inoculation_timing.csv')
D['inoc'] = rec(IT.groupby('date').apply(lambda g: pd.Series(dict(share_KW=(g.p_KW_inoc < 0.05).mean(), median_rho=g.spearman_inoc.median()))).reindex(DL).reset_index(), 3)
D['raw_smooth'] = rec(T('raw_vs_smooth_separability.csv'), 3)

if have('cv_main_summary.csv'):
    SUM = T('cv_main_summary.csv')
    D['summary'] = rec(SUM[['scenario', 'clf'] + [f'{m}_mean' for m in METS] + ['BA_SD', 'BA_CI95_low', 'BA_CI95_high']], 4)
    D['best'] = rec(T('best_pipelines.csv'), 4)
    D['best_sc'] = rec(T('cv_best_per_scenario.csv')[['scenario', 'clf', 'BA_mean', 'BA_SD', 'BA_CI95_low', 'BA_CI95_high', 'Sensitivity_mean', 'Specificity_mean', 'Kappa_mean', 'MCC_mean', 'ROC_AUC_mean']], 4)
    D['best_clf'] = rec(T('cv_best_per_classifier.csv')[['clf', 'scenario', 'BA_mean']], 4)
    D['friedman_c'] = rec(T('friedman_classifiers.csv'), 3); D['friedman_s'] = rec(T('friedman_scenarios.csv'), 3)
    D['friedman'] = rec(T('friedman_tests.csv'), 6); D['pairwise'] = rec(T('pairwise_tests.csv'), 5)
    D['cm'] = rec(T('confusion_matrices.csv'), 3); D['roc'] = rec(T('roc_curves.csv'), 3)
    D['subgroups'] = rec(T('subgroup_performance.csv'), 3)
    PG = T('oof_vote_by_date_inoc.csv'); D['progress'] = rec(PG[['label', 'Date', 'D1', 'D2', 'D3', 'D4']], 3)
    D['prog_tests'] = rec(T('oof_progression_tests.csv'), 4); D['plot_decision'] = rec(T('plot_level_decision.csv'), 3)
    D['final'] = rec(T('final_features.csv'), 4); D['final_jm'] = rec(T('final_features_JM.csv'), 3)
    C = T('final_features_corr.csv').set_index('Unnamed: 0'); D['final_corr'] = dict(names=list(C.columns), values=C.round(2).values.tolist())
    D['s10_share'] = rec(T('S10_family_share.csv'), 1)
    FR = T('selection_frequency.csv'); D['selfreq'] = rec(FR[FR.scenario == 'S10'].head(12), 1)
    D['hyper'] = rec(T('hyperparameters.csv'), 2)
    if have('leaf_vs_plot_comparison.csv'):
        D['E10'] = rec(T('leaf_vs_plot_comparison.csv'), 4)
    MR = T('cv_main_reps.csv')
if have('E1_branch_reps.csv'):
    E1 = summ(T('E1_branch_reps.csv'), ['scenario', 'clf']); base = summ(MR[MR.rep < 10], ['scenario', 'clf'])
    m = base[['scenario', 'clf', 'BA']].rename(columns={'BA': 'raw'}).merge(E1[['scenario', 'clf', 'BA']].rename(columns={'BA': 'smooth'}), on=['scenario', 'clf'])
    D['E1'] = rec(m.loc[m.groupby('scenario')['raw'].idxmax()], 4)
    D['E1_all'] = rec(m, 4)
if have('E2_single_date_reps.csv'):
    E2 = summ(T('E2_single_date_reps.csv'), ['date', 'scenario', 'clf'])
    D['E2'] = rec(E2.loc[E2.groupby(['date', 'scenario'])['BA'].idxmax()], 4)
if have('E3_transfer.csv'):
    E3 = T('E3_transfer.csv')
    D['E3'] = rec(E3.loc[E3.groupby(['kind', 'held_out', 'date_norm', 'scenario'])['BA'].idxmax()][['kind', 'held_out', 'date_norm', 'scenario', 'clf', 'BA', 'Sensitivity', 'Specificity', 'MCC']], 4)
if have('E4_datenorm_reps.csv'):
    E4 = summ(T('E4_datenorm_reps.csv'), ['scenario', 'clf']); base = summ(MR[MR.rep < 10], ['scenario', 'clf'])
    m = base[['scenario', 'clf', 'BA']].rename(columns={'BA': 'without'}).merge(E4[['scenario', 'clf', 'BA']].rename(columns={'BA': 'with'}), on=['scenario', 'clf'])
    D['E4'] = rec(m, 4)
if have('E5_permutation_summary.csv'):
    D['E5'] = rec(T('E5_permutation_summary.csv'), 4)
if have('E6_design_controls_reps.csv'):
    E6 = summ(T('E6_design_controls_reps.csv'), ['contrast', 'type', 'scenario', 'clf'])
    D['E6'] = rec(E6.loc[E6.groupby(['contrast', 'scenario'])['BA'].idxmax()], 4)
if have('E7_ofc_reps.csv'):
    D['E7'] = rec(summ(T('E7_ofc_reps.csv'), ['feature_set', 'clf'], extra=('features',)), 4)
    if have('E7_ofc_final_sets.csv'):
        D['E7_final'] = rec(T('E7_ofc_final_sets.csv'), 3); D['E7_summary'] = rec(T('E7_ofc_final_summary.csv'), 3)
        fq = T('E7_ofc_feature_frequency.csv'); D['E7_freq'] = rec(fq[fq.Set == 'DSFs (all)'].head(8), 0)
if have('E8_fs_reps.csv'):
    D['E8'] = rec(summ(T('E8_fs_reps.csv'), ['method', 'k', 'clf']), 4)
if have('E9_equal_leaves_reps.csv'):
    E9 = T('E9_equal_leaves_reps.csv')
    s9 = summ(E9, ['averaging', 'scenario', 'clf'])
    D['E9'] = rec(s9.loc[s9.groupby(['averaging', 'scenario'])['BA'].idxmax()], 4)
    D['E9_check'] = float(E9['check_max_abs_diff'].iloc[0])
D['refs'] = rec(pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'references.csv')))
json.dump(D, open(os.path.join(CACHE, 'ppt_data.json'), 'w'))
print('exported', len(D), 'keys')
