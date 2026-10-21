"""Steps 9-10 - summary of the main plot-level CV, statistical comparison of pipelines, per-date / variety /
inoculation performance, disease-probability progression, selection stability, final model and interpretation."""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
import sys, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcommon import *
from p03_cv import load_all, SCENARIOS, inner_splits, combined
from models import CLF_NAMES, tune, fit_predict, make, robust_select, vif_filter
from common import metrics
from scipy import stats
from sklearn.metrics import roc_curve, balanced_accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression

M, fam = load_all('raw')
y = M['y'].to_numpy(); dates = M['date'].to_numpy()
res = pickle.load(open(os.path.join(CACHE, 'cv_main.pkl'), 'rb'))
R = 1 + max(r['rep'] for r in res)
KEYM = ['OA', 'BA', 'Sensitivity', 'Specificity', 'Precision', 'F1_Diseased', 'F1_Healthy', 'MacroF1', 'Kappa', 'MCC', 'ROC_AUC', 'PR_AUC_Healthy']

pool = {}
for r in res:
    pool.setdefault((r['scenario'], r['clf'], r['rep']), []).append(r)
rep_rows, fold_rows, pred_store = [], [], {}
for (sc, c, rep), rr in pool.items():
    te = np.concatenate([r['te'] for r in rr]); pr = np.concatenate([r['pred'] for r in rr]); s = np.concatenate([r['score'] for r in rr])
    pred_store[(sc, c, rep)] = (te, pr, s)
    rep_rows.append(dict(scenario=sc, clf=c, rep=rep, **metrics(y[te], pr, s)))
    for r in rr:
        fold_rows.append(dict(scenario=sc, clf=c, rep=rep, fold=r['fold'], BA=balanced_accuracy_score(y[r['te']], r['pred'])))
REP = pd.DataFrame(rep_rows); FOLD = pd.DataFrame(fold_rows)
REP.to_csv(os.path.join(TAB, 'cv_main_reps.csv'), index=False)


def summarise(D, by):
    g = D.groupby(by)
    out = g[KEYM].mean().add_suffix('_mean').join(g[KEYM].std().add_suffix('_SD'))
    n = g.size()
    out['BA_CI95_low'] = out['BA_mean'] - stats.t.ppf(0.975, n - 1) * out['BA_SD'] / np.sqrt(n)
    out['BA_CI95_high'] = out['BA_mean'] + stats.t.ppf(0.975, n - 1) * out['BA_SD'] / np.sqrt(n)
    out['n_repeats'] = n
    return out.reset_index()


SUM = summarise(REP, ['scenario', 'clf'])
SUM['Scenario_name'] = SUM['scenario'].map(SCENARIOS)
SUM.to_csv(os.path.join(TAB, 'cv_main_summary.csv'), index=False)
for met in ('BA', 'MCC', 'ROC_AUC'):
    MAT = SUM.pivot(index='scenario', columns='clf', values=f'{met}_mean').loc[list(SCENARIOS), CLF_NAMES]
    MAT.index = [f'{k}: {SCENARIOS[k]}' for k in MAT.index]
    MAT.to_csv(os.path.join(TAB, f'cv_{met.lower()}_matrix.csv'))
best_sc = SUM.loc[SUM.groupby('scenario')['BA_mean'].idxmax()].set_index('scenario').loc[list(SCENARIOS)].reset_index()
best_sc.to_csv(os.path.join(TAB, 'cv_best_per_scenario.csv'), index=False)
best_clf = SUM.loc[SUM.groupby('clf')['BA_mean'].idxmax()].set_index('clf').loc[CLF_NAMES].reset_index()
best_clf.to_csv(os.path.join(TAB, 'cv_best_per_classifier.csv'), index=False)
TOP = SUM.sort_values(['BA_mean', 'MCC_mean'], ascending=False).iloc[0]
best_key = (TOP['scenario'], TOP['clf'])
SEL = SUM[SUM['scenario'].isin(['S8', 'S9', 'S10', 'S11'])].sort_values(['BA_mean', 'MCC_mean'], ascending=False).iloc[0]
compact_key = (SEL['scenario'], SEL['clf'])
VIb = SUM[SUM['scenario'] == 'S6'].sort_values('BA_mean', ascending=False).iloc[0]
vi_key = ('S6', VIb['clf'])
nfeat = {sc: np.median([len(r['features']) for r in res if r['scenario'] == sc and r['clf'] == 'LDA']) for sc in SCENARIOS}
BEST = pd.DataFrame([dict(Role='Best overall', scenario=best_key[0], clf=best_key[1], BA=TOP['BA_mean'], MCC=TOP['MCC_mean'], AUC=TOP['ROC_AUC_mean'], n_features=nfeat[best_key[0]]),
                     dict(Role='Best compact (feature-selected)', scenario=compact_key[0], clf=compact_key[1], BA=SEL['BA_mean'], MCC=SEL['MCC_mean'], AUC=SEL['ROC_AUC_mean'], n_features=nfeat[compact_key[0]]),
                     dict(Role='Best vegetation-index model', scenario=vi_key[0], clf=vi_key[1], BA=VIb['BA_mean'], MCC=VIb['MCC_mean'], AUC=VIb['ROC_AUC_mean'], n_features=nfeat['S6'])])
BEST['Scenario_name'] = BEST['scenario'].map(SCENARIOS)
BEST.to_csv(os.path.join(TAB, 'best_pipelines.csv'), index=False)
print(BEST)


def friedman(D, treat, block):
    W = D.pivot_table(index=block, columns=treat, values='BA')
    ranks = W.rank(axis=1, ascending=False)
    chi, p = stats.friedmanchisquare(*[W[c] for c in W.columns])
    k, N = W.shape[1], W.shape[0]
    q = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102, 10: 3.164, 11: 3.219, 12: 3.268}[k]
    cd = q * np.sqrt(k * (k + 1) / (6 * N))
    out = pd.DataFrame({'Average_rank': ranks.mean(), 'Mean_BA': W.mean()}).sort_values('Average_rank').reset_index()
    out.columns = [treat, 'Average_rank', 'Mean_BA']
    return out, dict(chi2=chi, p=p, k=k, N=N, CD_Nemenyi_0_05=cd)


REP['block_s'] = REP['scenario'] + '_' + REP['rep'].astype(str)
REP['block_c'] = REP['clf'] + '_' + REP['rep'].astype(str)
fr_c, frc = friedman(REP, 'clf', 'block_s'); fr_s, frs = friedman(REP, 'scenario', 'block_c')
fr_s['Scenario_name'] = fr_s['scenario'].map(SCENARIOS)
fr_c.to_csv(os.path.join(TAB, 'friedman_classifiers.csv'), index=False)
fr_s.to_csv(os.path.join(TAB, 'friedman_scenarios.csv'), index=False)
pd.DataFrame([dict(Comparison='Classifiers (blocks = scenario x repeat)', **frc),
              dict(Comparison='Feature scenarios (blocks = classifier x repeat)', **frs)]).to_csv(os.path.join(TAB, 'friedman_tests.csv'), index=False)


def corrected_t(a, b, ratio=1 / 3):
    """Nadeau & Bengio (2003) corrected resampled t-test on the per-fold BA of repeated k-fold CV."""
    d = a - b; n = len(d); v = d.var(ddof=1)
    t = d.mean() / np.sqrt((1 / n + ratio) * v) if v > 0 else np.inf
    return d.mean(), t, 2 * stats.t.sf(abs(t), n - 1)


FB = FOLD.set_index(['scenario', 'clf', 'rep', 'fold'])['BA']
base = FB.loc[best_key[0], best_key[1]].sort_index()
ct = []
for _, rw in best_sc.iterrows():
    if (rw['scenario'], rw['clf']) == best_key:
        continue
    other = FB.loc[rw['scenario'], rw['clf']].sort_index()
    md, t, p = corrected_t(base.to_numpy(), other.to_numpy())
    w = stats.wilcoxon(REP[(REP.scenario == best_key[0]) & (REP.clf == best_key[1])].sort_values('rep')['BA'].to_numpy(),
                       REP[(REP.scenario == rw['scenario']) & (REP.clf == rw['clf'])].sort_values('rep')['BA'].to_numpy(), zero_method='zsplit')[1]
    ct.append(dict(Comparison=f"{best_key[0]}-{best_key[1]} vs {rw['scenario']}-{rw['clf']}", Other=SCENARIOS[rw['scenario']],
                   Mean_BA_difference=md, t_corrected=t, p_corrected_t=p, p_Wilcoxon=w))
CT = pd.DataFrame(ct)
o = np.argsort(CT['p_Wilcoxon'].to_numpy()); m_ = len(o); adj = np.zeros(m_); run_max = 0
for rnk, i in enumerate(o):
    run_max = max(run_max, min(1, (m_ - rnk) * CT['p_Wilcoxon'].iloc[i])); adj[i] = run_max
CT['p_Wilcoxon_Holm'] = adj
CT.to_csv(os.path.join(TAB, 'pairwise_tests.csv'), index=False)

# ---- confusion matrices, ROC, out-of-fold disease probability
cms, rocs, subg = [], {}, []
oof = M[['pd', 'plot', 'date', 'label', 'y', 'variety', 'inoc', 'block', 'stage', 'n_leaves']].copy()
for role, key in [('Best overall', best_key), ('Best compact', compact_key), ('Best VI model', vi_key)]:
    rr = REP[(REP['scenario'] == key[0]) & (REP['clf'] == key[1])]
    rep_med = int(rr.iloc[(rr['BA'] - rr['BA'].median()).abs().argsort().iloc[0]]['rep'])
    te, pr, s = pred_store[(key[0], key[1], rep_med)]
    m = metrics(y[te], pr, s)
    cms.append(dict(Role=role, Pipeline=f'{key[0]} {SCENARIOS[key[0]]} + {key[1]}', Repeat=rep_med, TN=m['TN'], FP=m['FP'], FN=m['FN'], TP=m['TP'],
                    BA=m['BA'], OA=m['OA'], Kappa=m['Kappa'], MCC=m['MCC']))
    allp, alls = np.zeros(len(y)), np.zeros(len(y))
    tprs = []
    for rep in range(R):
        te, pr, s = pred_store[(key[0], key[1], rep)]
        allp[te] += pr / R; alls[te] += s / R
        fpr, tpr, _ = roc_curve(y[te], s); tprs.append(np.interp(np.linspace(0, 1, 51), fpr, tpr))
        for fac, order in [('date', DATE_ORDER), ('variety', ['V1', 'V2', 'V3']), ('inoc', ['D1', 'D2', 'D3', 'D4']), ('stage', ['Vegetative', 'Flowering', 'Pod formation'])]:
            lv = M[fac].to_numpy()[te]
            for L in order:
                mm = lv == L
                if mm.sum() == 0:
                    continue
                r_ = dict(Role=role, Factor={'inoc': 'Inoculation'}.get(fac, fac.capitalize()), Level=DATE_LABEL.get(L, L), rep=rep, n=int(mm.sum()))
                r_.update(metrics(y[te][mm], pr[mm], s[mm] if len(np.unique(y[te][mm])) == 2 else None))
                subg.append(r_)
    rocs[role] = (np.mean(tprs, 0), np.std(tprs, 0))
    oof[f'{role}_vote'] = allp; oof[f'{role}_score'] = alls
pd.DataFrame(cms).to_csv(os.path.join(TAB, 'confusion_matrices.csv'), index=False)
pd.DataFrame({'FPR': np.linspace(0, 1, 51), **{f'TPR_{k}': v[0] for k, v in rocs.items()}, **{f'SD_{k}': v[1] for k, v in rocs.items()}}).to_csv(os.path.join(TAB, 'roc_curves.csv'), index=False)
SG = pd.DataFrame(subg)
SG.groupby(['Role', 'Factor', 'Level'], sort=False)[['n', 'OA', 'BA', 'Sensitivity', 'Specificity', 'MacroF1', 'Kappa', 'MCC', 'ROC_AUC']].mean().reset_index().to_csv(
    os.path.join(TAB, 'subgroup_performance.csv'), index=False)
oof.to_csv(os.path.join(TAB, 'oof_predictions.csv'), index=False)
# disease-vote progression: diseased-plot share by date x inoculation timing x class (best overall)
prog = oof.groupby(['label', 'date', 'inoc'])['Best overall_vote'].mean().unstack('inoc').reset_index()
prog['Date'] = prog['date'].map(DATE_LABEL)
prog.to_csv(os.path.join(TAB, 'oof_vote_by_date_inoc.csv'), index=False)
pr_rows = []
for dt in DATE_ORDER:
    d = oof[(oof.date == dt) & (oof.y == 1)]
    rho, p = stats.spearmanr(d['inoc'].str[1].astype(int), d['Best overall_score'])
    kw = stats.kruskal(*[g['Best overall_score'].to_numpy() for _, g in d.groupby('inoc')])[1]
    h = oof[(oof.date == dt) & (oof.y == 0)]
    pr_rows.append(dict(Date=DATE_LABEL[dt], Spearman_inoc_vs_score_diseased=rho, p_spearman=p, p_KW=kw,
                        mean_score_H=h['Best overall_score'].mean(), mean_score_D=d['Best overall_score'].mean(),
                        rho_leaves_score_within_D=stats.spearmanr(d['n_leaves'], d['Best overall_score'])[0] if d['n_leaves'].nunique() > 1 else np.nan,
                        rho_leaves_score_within_H=stats.spearmanr(h['n_leaves'], h['Best overall_score'])[0] if h['n_leaves'].nunique() > 1 else np.nan))
pd.DataFrame(pr_rows).to_csv(os.path.join(TAB, 'oof_progression_tests.csv'), index=False)
# plot-level decision across all four dates (mean vote of a plot over the dates)
plot_dec = oof.groupby('plot').agg(y=('y', 'first'), vote=('Best overall_vote', 'mean'), score=('Best overall_score', 'mean')).reset_index()
mp = metrics(plot_dec['y'].to_numpy(), (plot_dec['vote'] > 0.5).astype(int).to_numpy(), plot_dec['score'].to_numpy())
pd.DataFrame([dict(Level='Plot (4 dates combined)', **mp)]).to_csv(os.path.join(TAB, 'plot_level_decision.csv'), index=False)

# ---- selection stability and hyper-parameters
freq = []
for sc in ['S8', 'S9', 'S10', 'S11', 'S12']:
    rr = [r for r in res if r['scenario'] == sc and r['clf'] == 'LDA']
    cnt = pd.Series([f for r in rr for f in r['features']]).value_counts()
    for f, n in cnt.items():
        freq.append(dict(scenario=sc, Scenario_name=SCENARIOS[sc], Feature=f, Selected_in_folds=n, Frequency_pct=100 * n / len(rr),
                         Median_n_features=np.median([len(r['features']) for r in rr])))
FR = pd.DataFrame(freq).sort_values(['scenario', 'Selected_in_folds'], ascending=[True, False])
FR.to_csv(os.path.join(TAB, 'selection_frequency.csv'), index=False)


def fam_of(n):
    for p, f in (('D1_', 'FD1'), ('D2_', 'FD2'), ('D3_', 'FD3'), ('WF', 'CWT'), ('CR', 'CR'), ('NDSI(', 'NDSI'), ('SR(', 'NDSI'), ('DI(', 'NDSI')):
        if n.startswith(p):
            return f
    if n[0] == 'R' and n[1:].isdigit():
        return 'REF'
    if n in fam['RE'].columns:
        return 'RE'
    return 'VI'


s10 = [r for r in res if r['scenario'] == 'S10' and r['clf'] == 'LDA']
fs = pd.Series([fam_of(f) for r in s10 for f in r['features']]).value_counts(normalize=True).mul(100).rename('Share_pct').reset_index()
fs.columns = ['Family', 'Share_pct']; fs['Family_name'] = fs['Family'].map(FAMILY_LABEL)
fs.to_csv(os.path.join(TAB, 'S10_family_share.csv'), index=False)
bf = {'Wavelength_nm': WL10}
for sc in ['S11', 'S12']:
    sub = FR[FR['scenario'] == sc].set_index('Feature')['Frequency_pct']
    bf[sc] = [sub.get(f'R{w}', 0.0) for w in WL10]
pd.DataFrame(bf).to_csv(os.path.join(TAB, 'band_selection_frequency.csv'), index=False)
hp = []
for (sc, c), g in pd.DataFrame([dict(scenario=r['scenario'], clf=r['clf'], params=str(r['params']), nfeat=len(r['features'])) for r in res]).groupby(['scenario', 'clf']):
    hp.append(dict(scenario=sc, clf=c, Most_frequent_params=g['params'].mode().iloc[0], Median_n_features=g['nfeat'].median()))
pd.DataFrame(hp).to_csv(os.path.join(TAB, 'hyperparameters.csv'), index=False)

# ---- final model: S10 robust selection on all 192 plot-dates + interpretation
F = combined(fam, np.arange(len(y)), y, dates, fam['REF'].to_numpy(float))
A = F.to_numpy(float)
inner_all = inner_splits(M, 4, 77)
sel, info = robust_select(A, y, dates, inner_all, seed=77)
names = list(F.columns[sel]); Z = A[:, sel]
print('final features', names, info)
P = plot_table(M); a = cell_folds(P, 4, 99); f = M['plot'].map(a).to_numpy()
imp = np.zeros((len(sel), 4))
for k in range(4):
    tr, te = np.where(f != k)[0], np.where(f == k)[0]
    inner = inner_splits(M.iloc[tr].reset_index(drop=True), 3, 99)
    p, _ = tune('SVM', Z[tr], y[tr], inner, 99)
    sc_ = StandardScaler().fit(Z[tr]); mdl = make('SVM', p, Z.shape[1]).fit(sc_.transform(Z[tr]), y[tr])
    imp[:, k] = permutation_importance(mdl, sc_.transform(Z[te]), y[te], scoring='balanced_accuracy', n_repeats=30, random_state=k).importances_mean
Zs = (Z - Z.mean(0)) / Z.std(0)
lr = LogisticRegression(C=1.0, class_weight='balanced', max_iter=5000).fit(Zs, y)
C = np.corrcoef(Zs.T); vif = np.diag(np.linalg.pinv(C))
fin = []
for j, nm in enumerate(names):
    v = Z[:, j]; a_, b_ = v[y == 1], v[y == 0]
    auc = roc_auc_score(y, v)
    fin.append(dict(Feature=nm, Family=FAMILY_LABEL[fam_of(nm)], Healthy_mean=b_.mean(), Healthy_sd=b_.std(ddof=1), Diseased_mean=a_.mean(), Diseased_sd=a_.std(ddof=1),
                    Hedges_g=(a_.mean() - b_.mean()) / np.sqrt((a_.var(ddof=1) + b_.var(ddof=1)) / 2), AUC=max(auc, 1 - auc),
                    LR_std_coef=lr.coef_[0][j], VIF=vif[j], Perm_importance_BA=imp[j].mean(), Perm_importance_SD=imp[j].std()))
FIN = pd.DataFrame(fin).sort_values('Perm_importance_BA', ascending=False)
FIN.to_csv(os.path.join(TAB, 'final_features.csv'), index=False)
pd.DataFrame(C, index=names, columns=names).to_csv(os.path.join(TAB, 'final_features_corr.csv'))


def jm_multi(a, b):
    m1, m2 = a.mean(0), b.mean(0); c1, c2 = np.cov(a.T), np.cov(b.T); c = (c1 + c2) / 2
    dm = (m1 - m2)[:, None]
    Bh = 0.125 * (dm.T @ np.linalg.pinv(c) @ dm).item() + 0.5 * (np.linalg.slogdet(c)[1] - 0.5 * (np.linalg.slogdet(c1)[1] + np.linalg.slogdet(c2)[1]))
    return 2 * (1 - np.exp(-Bh))


jmr = [dict(Subset='All dates', JM=jm_multi(Zs[y == 1], Zs[y == 0]), n_features=len(names), max_VIF=vif.max(),
            max_abs_r=np.abs(C[np.triu_indices(len(names), 1)]).max() if len(names) > 1 else np.nan, condition_number=np.linalg.cond(C))]
for dt in DATE_ORDER:
    mm = dates == dt
    jmr.append(dict(Subset=DATE_LABEL[dt], JM=jm_multi(Zs[mm & (y == 1)], Zs[mm & (y == 0)]), n_features=len(names)))
pd.DataFrame(jmr).to_csv(os.path.join(TAB, 'final_features_JM.csv'), index=False)
# full-spectrum first-derivative LR coefficients (interpretation of S2)
D1 = fam['FD1'].to_numpy(); sc_ = StandardScaler().fit(D1)
lr2 = LogisticRegression(C=0.1, class_weight='balanced', max_iter=5000).fit(sc_.transform(D1), y)
pd.DataFrame({'Wavelength_nm': WL10, 'LR_std_coefficient_FD1': lr2.coef_[0]}).to_csv(os.path.join(TAB, 'lr_coefficients.csv'), index=False)

# ---- leaf-level vs plot-level comparison (previous leaf analysis of the same plots)
lt = os.path.join(LEAF, 'outputs', 'tables')
if os.path.exists(os.path.join(lt, 'cv_main_summary.csv')):
    LS = pd.read_csv(os.path.join(lt, 'cv_main_summary.csv')); LP = pd.read_csv(os.path.join(lt, 'cv_main_summary_plotdate.csv'))
    rows = []
    for nm, D, lev in (('Leaf spectra (leaf-level models)', LS, 'Leaf spectrum'), ('Leaf models, majority vote per plot-date', LP, 'Plot-date')):
        b = D.sort_values('BA_mean', ascending=False).iloc[0]
        rows.append(dict(Approach=nm, Unit=lev, Pipeline=f"{b['scenario']} + {b['clf']}", BA=b['BA_mean'], BA_SD=b['BA_SD'], MCC=b['MCC_mean'],
                         Sensitivity=b['Sensitivity_mean'], Specificity=b['Specificity_mean']))
    for role, key in [('Plot-average spectra (this analysis), best overall', best_key), ('Plot-average spectra (this analysis), best compact', compact_key)]:
        b = SUM[(SUM.scenario == key[0]) & (SUM.clf == key[1])].iloc[0]
        rows.append(dict(Approach=role, Unit='Plot-date', Pipeline=f'{key[0]} {SCENARIOS[key[0]]} + {key[1]}', BA=b['BA_mean'], BA_SD=b['BA_SD'], MCC=b['MCC_mean'],
                         Sensitivity=b['Sensitivity_mean'], Specificity=b['Specificity_mean']))
    pd.DataFrame(rows).to_csv(os.path.join(TAB, 'leaf_vs_plot_comparison.csv'), index=False)
print('summarise done')
