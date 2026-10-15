"""Step 8-10: summarise the main CV, statistical comparison of models, sub-group performance,
feature-selection stability, final model and interpretation."""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
import sys, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from models import *
from s04_cv import load_all, SCENARIOS, inner_splits, ndsi_top, nd_feats
from scipy import stats
from sklearn.metrics import roc_curve, balanced_accuracy_score
from sklearn.inspection import permutation_importance

B10, M, fam = load_all()
y = M['y'].to_numpy(); dates = M['date'].to_numpy()
res = pickle.load(open(os.path.join(CACHE, 'cv_main.pkl'), 'rb'))
R = 1 + max(r['rep'] for r in res)
KEYM = ['OA', 'BA', 'Sensitivity', 'Specificity', 'Precision', 'F1_Diseased', 'F1_Healthy', 'MacroF1', 'Kappa', 'MCC', 'ROC_AUC', 'PR_AUC_Healthy']

# ---- pooled predictions per (scenario, clf, rep)
pool = {}
for r in res:
    k = (r['scenario'], r['clf'], r['rep'])
    pool.setdefault(k, []).append(r)
rep_rows, pd_rows, fold_rows = [], [], []
pred_store = {}
for (sc, c, rep), rr in pool.items():
    te = np.concatenate([r['te'] for r in rr]); pr = np.concatenate([r['pred'] for r in rr]); s = np.concatenate([r['score'] for r in rr])
    pred_store[(sc, c, rep)] = (te, pr, s)
    rep_rows.append(dict(scenario=sc, clf=c, rep=rep, **metrics(y[te], pr, s)))
    # plot-date majority vote
    dfp = pd.DataFrame({'pd': M['plot_date'].to_numpy()[te], 'y': y[te], 'p': pr, 's': s}).groupby('pd').agg(y=('y', 'first'), p=('p', 'mean'), s=('s', 'mean'))
    pd_rows.append(dict(scenario=sc, clf=c, rep=rep, **metrics(dfp['y'].to_numpy(), (dfp['p'] > 0.5).astype(int).to_numpy(), dfp['s'].to_numpy())))
    for r in rr:
        fold_rows.append(dict(scenario=sc, clf=c, rep=rep, fold=r['fold'], BA=balanced_accuracy_score(y[r['te']], r['pred']),
                              n_test=len(r['te'])))
REP = pd.DataFrame(rep_rows); PDL = pd.DataFrame(pd_rows); FOLD = pd.DataFrame(fold_rows)
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
SUMPD = summarise(PDL, ['scenario', 'clf']); SUMPD.to_csv(os.path.join(TAB, 'cv_main_summary_plotdate.csv'), index=False)
BA_MAT = SUM.pivot(index='scenario', columns='clf', values='BA_mean').loc[list(SCENARIOS), CLF_NAMES]
BA_MAT.index = [f'{k}: {SCENARIOS[k]}' for k in BA_MAT.index]
BA_MAT.to_csv(os.path.join(TAB, 'cv_ba_matrix.csv'))
MCC_MAT = SUM.pivot(index='scenario', columns='clf', values='MCC_mean').loc[list(SCENARIOS), CLF_NAMES]
MCC_MAT.index = BA_MAT.index; MCC_MAT.to_csv(os.path.join(TAB, 'cv_mcc_matrix.csv'))
best_per_sc = SUM.loc[SUM.groupby('scenario')['BA_mean'].idxmax()].set_index('scenario').loc[list(SCENARIOS)].reset_index()
best_per_sc.to_csv(os.path.join(TAB, 'cv_best_per_scenario.csv'), index=False)
best_per_clf = SUM.loc[SUM.groupby('clf')['BA_mean'].idxmax()].set_index('clf').loc[CLF_NAMES].reset_index()
best_per_clf.to_csv(os.path.join(TAB, 'cv_best_per_classifier.csv'), index=False)
TOP = SUM.sort_values('BA_mean', ascending=False).iloc[0]
best_key = (TOP['scenario'], TOP['clf'])
print('best pipeline', best_key, TOP['BA_mean'])
# compact pipeline (best among selected-feature scenarios with <= 10 features)
SEL = SUM[SUM['scenario'].isin(['S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8'])].sort_values('BA_mean', ascending=False).iloc[0]
compact_key = (SEL['scenario'], SEL['clf'])
print('best compact pipeline', compact_key, SEL['BA_mean'])
pd.DataFrame([dict(Role='Best overall', scenario=best_key[0], clf=best_key[1], BA=TOP['BA_mean']),
              dict(Role='Best compact (feature-selected)', scenario=compact_key[0], clf=compact_key[1], BA=SEL['BA_mean'])]).to_csv(
    os.path.join(TAB, 'best_pipelines.csv'), index=False)

# ---- Friedman / Nemenyi: classifiers (blocks = scenario x rep) and scenarios (blocks = clf x rep)
def friedman(D, treat, block):
    W = D.pivot_table(index=block, columns=treat, values='BA')
    ranks = W.rank(axis=1, ascending=False)
    chi, p = stats.friedmanchisquare(*[W[c] for c in W.columns])
    k, N = W.shape[1], W.shape[0]
    q = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102, 10: 3.164}[k]
    cd = q * np.sqrt(k * (k + 1) / (6 * N))
    out = pd.DataFrame({'Average_rank': ranks.mean(), 'Mean_BA': W.mean()}).sort_values('Average_rank').reset_index()
    out.columns = [treat, 'Average_rank', 'Mean_BA']
    return out, dict(chi2=chi, p=p, k=k, N=N, CD_Nemenyi_0_05=cd)
REP['block_s'] = REP['scenario'] + '_' + REP['rep'].astype(str)
REP['block_c'] = REP['clf'] + '_' + REP['rep'].astype(str)
fr_c, frc_info = friedman(REP, 'clf', 'block_s')
fr_s, frs_info = friedman(REP, 'scenario', 'block_c')
fr_s['Scenario_name'] = fr_s['scenario'].map(SCENARIOS)
fr_c.to_csv(os.path.join(TAB, 'friedman_classifiers.csv'), index=False)
fr_s.to_csv(os.path.join(TAB, 'friedman_scenarios.csv'), index=False)
pd.DataFrame([dict(Comparison='Classifiers (blocks = scenario x repeat)', **frc_info),
              dict(Comparison='Feature scenarios (blocks = classifier x repeat)', **frs_info)]).to_csv(os.path.join(TAB, 'friedman_tests.csv'), index=False)

# ---- Nadeau-Bengio corrected resampled t-test: best pipeline vs best of every other scenario
def corrected_t(a, b, ratio=1 / 3):
    d = a - b; n = len(d)
    v = d.var(ddof=1)
    t = d.mean() / np.sqrt((1 / n + ratio) * v) if v > 0 else np.inf
    return d.mean(), t, 2 * stats.t.sf(abs(t), n - 1)
FB = FOLD.set_index(['scenario', 'clf', 'rep', 'fold'])['BA']
base = FB.loc[best_key[0], best_key[1]].sort_index()
ct = []
for _, rw in best_per_sc.iterrows():
    other = FB.loc[rw['scenario'], rw['clf']].sort_index()
    md, t, p = corrected_t(base.to_numpy(), other.to_numpy())
    ct.append(dict(Comparison=f"{best_key[0]}-{best_key[1]} vs {rw['scenario']}-{rw['clf']}", Mean_BA_difference=md, t_corrected=t, p_value=p))
pd.DataFrame(ct).to_csv(os.path.join(TAB, 'corrected_ttests.csv'), index=False)

# ---- confusion matrices: representative repeat (median BA) for best + compact pipelines
cms, rocs, subg = [], {}, []
for role, key in [('Best overall', best_key), ('Best compact', compact_key)]:
    rr = REP[(REP['scenario'] == key[0]) & (REP['clf'] == key[1])]
    rep_med = int(rr.iloc[(rr['BA'] - rr['BA'].median()).abs().argsort().iloc[0]]['rep'])
    te, pr, s = pred_store[(key[0], key[1], rep_med)]
    m = metrics(y[te], pr, s)
    cms.append(dict(Role=role, Pipeline=f'{key[0]} {SCENARIOS[key[0]]} + {key[1]}', Repeat=rep_med, Level='Spectrum',
                    TN=m['TN'], FP=m['FP'], FN=m['FN'], TP=m['TP']))
    dfp = pd.DataFrame({'pd': M['plot_date'].to_numpy()[te], 'y': y[te], 'p': pr}).groupby('pd').agg(y=('y', 'first'), p=('p', 'mean'))
    mp = metrics(dfp['y'].to_numpy(), (dfp['p'] > 0.5).astype(int).to_numpy())
    cms.append(dict(Role=role, Pipeline=f'{key[0]} {SCENARIOS[key[0]]} + {key[1]}', Repeat=rep_med, Level='Plot-date (majority vote)',
                    TN=mp['TN'], FP=mp['FP'], FN=mp['FN'], TP=mp['TP']))
    fpr, tpr, _ = roc_curve(y[te], s)
    grid_f = np.linspace(0, 1, 51)
    rocs[role] = np.interp(grid_f, fpr, tpr)
    # sub-group metrics averaged over repeats
    for rep in range(R):
        te, pr, s = pred_store[(key[0], key[1], rep)]
        for fac, order in [('date', DATE_ORDER), ('variety', VARIETIES), ('stage', STAGE_ORDER)]:
            lv = M[fac].to_numpy()[te]
            for L in order:
                mm = lv == L
                subg.append(dict(Role=role, Factor=fac.capitalize(), Level=DATE_LABEL.get(L, L), rep=rep, **metrics(y[te][mm], pr[mm], s[mm])))
pd.DataFrame(cms).to_csv(os.path.join(TAB, 'confusion_matrices.csv'), index=False)
roc = pd.DataFrame({'FPR': np.linspace(0, 1, 51), **{f'TPR_{k}': v for k, v in rocs.items()}})
roc.to_csv(os.path.join(TAB, 'roc_curves.csv'), index=False)
SG = pd.DataFrame(subg)
SGS = SG.groupby(['Role', 'Factor', 'Level'], sort=False)[['OA', 'BA', 'Sensitivity', 'Specificity', 'MacroF1', 'Kappa', 'MCC', 'ROC_AUC']].mean().reset_index()
SGS.to_csv(os.path.join(TAB, 'subgroup_performance.csv'), index=False)

# ---- feature-selection stability (100 outer folds)
freq_rows = []
for sc in ['S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10']:
    rr = [r for r in res if r['scenario'] == sc and r['clf'] == 'LDA']
    nfold = len(rr)
    cnt = pd.Series([f for r in rr for f in r['features']]).value_counts()
    nsel = [len(r['features']) for r in rr]
    for f, n in cnt.items():
        freq_rows.append(dict(scenario=sc, Scenario_name=SCENARIOS[sc], Feature=f, Selected_in_folds=n, Frequency_pct=100 * n / nfold,
                              Median_n_features=np.median(nsel)))
FR = pd.DataFrame(freq_rows).sort_values(['scenario', 'Selected_in_folds'], ascending=[True, False])
FR.to_csv(os.path.join(TAB, 'selection_frequency.csv'), index=False)
# band-level selection frequency for SPA / GA-PLS
bf = {'Wavelength_nm': WL10}
for sc in ['S9', 'S10']:
    sub = FR[FR['scenario'] == sc].set_index('Feature')['Frequency_pct']
    bf[sc] = [sub.get(f'R{w}', 0.0) for w in WL10]
pd.DataFrame(bf).to_csv(os.path.join(TAB, 'band_selection_frequency.csv'), index=False)
hp = []
for (sc, c), g in pd.DataFrame([dict(scenario=r['scenario'], clf=r['clf'], params=str(r['params']), nfeat=len(r['features'])) for r in res]).groupby(['scenario', 'clf']):
    hp.append(dict(scenario=sc, clf=c, Most_frequent_params=g['params'].mode().iloc[0], Median_n_features=g['nfeat'].median()))
pd.DataFrame(hp).to_csv(os.path.join(TAB, 'hyperparameters.csv'), index=False)

# ---- final model on all data (S8 combined robust selection) + interpretation
pairs = ndsi_top(B10, y, dates)
N = pd.DataFrame(nd_feats(B10, pairs), columns=[f'ND({WL10[i]},{WL10[j]})' for i, j in pairs])
F = pd.concat([fam['F1'], fam['F2'], N, fam['F4'], fam['F5'], fam['F6']], axis=1)
A = F.to_numpy(float)
inner_all = inner_splits(M, 4, 77)
sel, info = robust_select(A, y, dates, inner_all, seed=77)
final_names = list(F.columns[sel])
print('final features', final_names, info)
Z = A[:, sel]
# grouped-CV permutation importance with the fixed final feature set (SVM)
pt = plot_table(M); a = plot_folds(pt, 4, 99); f = M['plot'].map(a).to_numpy()
imp = np.zeros((len(sel), 4))
for k in range(4):
    tr, te = np.where(f != k)[0], np.where(f == k)[0]
    inner = inner_splits(M.iloc[tr].reset_index(drop=True), 3, 99)
    p, _ = tune('SVM', Z[tr], y[tr], inner, 99)
    sc_ = StandardScaler().fit(Z[tr]); m = make('SVM', p, Z.shape[1]).fit(sc_.transform(Z[tr]), y[tr])
    pi = permutation_importance(m, sc_.transform(Z[te]), y[te], scoring='balanced_accuracy', n_repeats=20, random_state=k)
    imp[:, k] = pi.importances_mean
# TreeSHAP of XGBoost on the final features
from xgboost import XGBClassifier, DMatrix
xg = XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
                   scale_pos_weight=(y == 0).sum() / (y == 1).sum(), n_jobs=4, verbosity=0).fit(Z, y)
shap = xg.get_booster().predict(DMatrix(Z), pred_contribs=True)[:, :-1]
# univariate stats of final features
fin = []
for j, nm in enumerate(final_names):
    v = Z[:, j]
    a_, b_ = v[y == 1], v[y == 0]
    dco = (a_.mean() - b_.mean()) / np.sqrt((a_.var(ddof=1) + b_.var(ddof=1)) / 2)
    from sklearn.metrics import roc_auc_score
    auc = roc_auc_score(y, v)
    fin.append(dict(Feature=nm, Healthy_mean=b_.mean(), Diseased_mean=a_.mean(), Cohen_d=dco, AUC=max(auc, 1 - auc),
                    Permutation_importance_BA=imp[j].mean(), Permutation_importance_SD=imp[j].std(),
                    Mean_abs_SHAP=np.abs(shap[:, j]).mean()))
FIN = pd.DataFrame(fin).sort_values('Permutation_importance_BA', ascending=False)
FIN.to_csv(os.path.join(TAB, 'final_features.csv'), index=False)
# multivariate Jeffries-Matusita distance of the final feature set (overall and per date)
def jm_multi(a, b):
    m1, m2 = a.mean(0), b.mean(0); c1, c2 = np.cov(a.T), np.cov(b.T); c = (c1 + c2) / 2
    dm = (m1 - m2)[:, None]
    Bh = 0.125 * float(dm.T @ np.linalg.pinv(c) @ dm) + 0.5 * np.log(np.linalg.det(c) / np.sqrt(np.linalg.det(c1) * np.linalg.det(c2)))
    return 2 * (1 - np.exp(-Bh))
Zs = (Z - Z.mean(0)) / Z.std(0)
jmr = [dict(Subset='All dates', JM=jm_multi(Zs[y == 1], Zs[y == 0]))]
for dt in DATE_ORDER:
    m = dates == dt
    jmr.append(dict(Subset=DATE_LABEL[dt], JM=jm_multi(Zs[m & (y == 1)], Zs[m & (y == 0)])))
pd.DataFrame(jmr).to_csv(os.path.join(TAB, 'final_features_JM.csv'), index=False)
# LR full-spectrum standardised coefficients (interpretation of the full-spectrum model)
S = snv(B10); sc_ = StandardScaler().fit(S)
p_lr = SUM[(SUM['scenario'] == 'S1') & (SUM['clf'] == 'LR')]
lr = LogisticRegression(C=0.1, class_weight='balanced', max_iter=5000).fit(sc_.transform(S), y)
pd.DataFrame({'Wavelength_nm': WL10, 'LR_std_coefficient': lr.coef_[0]}).to_csv(os.path.join(TAB, 'lr_coefficients.csv'), index=False)
print('summarise done')
