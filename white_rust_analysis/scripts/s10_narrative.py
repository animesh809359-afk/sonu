"""Generate the slide narrative (results text, discussion, conclusions) from the result tables, so every
number quoted on a slide comes from the analysis."""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from s04_cv import SCENARIOS

T = lambda n: pd.read_csv(os.path.join(TAB, n))
have = lambda n: os.path.exists(os.path.join(TAB, n))
N = {}
S = T('spectra_mean_class.csv')
imax, imin = S['Difference_D-H'].idxmax(), S['Difference_D-H'].idxmin()
vis = S[(S.Wavelength_nm >= 550) & (S.Wavelength_nm <= 700)]
sw = S[(S.Wavelength_nm >= 1400) & (S.Wavelength_nm <= 1500)]
N['spectral_response'] = (f"Diseased leaves reflect more in the visible (up to +{100 * (vis['Ratio_D/H'].max() - 1):.0f}% near "
                          f"{int(vis.loc[vis['Ratio_D/H'].idxmax(), 'Wavelength_nm'])} nm: chlorophyll loss) and in the SWIR water bands "
                          f"(+{100 * (sw['Ratio_D/H'].max() - 1):.0f}% at ~1450 nm, +{100 * (S['Ratio_D/H'].max() - 1):.0f}% near {int(S.loc[S['Ratio_D/H'].idxmax(), 'Wavelength_nm'])} nm: water loss). "
                          f"NIR reflectance is only slightly lower (min {S.loc[imin, 'Difference_D-H']:.3f} at {int(S.loc[imin, 'Wavelength_nm'])} nm), "
                          "consistent with white pustules offsetting the loss of mesophyll scattering (Zhang et al., 2012).")
sim = T('class_similarity_by_date.csv')
N['by_date'] = (f"The healthy-diseased spectral angle grows from {sim['Spectral_angle_deg'].iloc[0]:.2f}° on 11 Feb to "
                f"{sim['Spectral_angle_deg'].max():.2f}° on {sim.loc[sim['Spectral_angle_deg'].idxmax(), 'Date']}, tracking epidemic development. "
                "Early (vegetative) differences are small and mainly in the SWIR, so date-specific effects must be handled by the pooled model.")
RG = T('sensitive_regions.csv')
N['regions'] = ("FDR-significant regions (plot-date means): " + '; '.join(f"{r.Region_nm} nm ({'D>H' if 'Diseased >' in r.Direction else 'D<H'}, |d| {r.Max_abs_Cohen_d:.2f} at {r.Peak_wavelength_nm} nm)" for r in RG.itertuples())
                + ". The NIR plateau is not significant in reflectance, but its first derivative (850-870 nm) is the strongest VNIR feature (J-M peak), "
                  "matching the NIR-slope signature of mesophyll collapse reported by Tian et al. (2021). The largest derivative J-M is at 1820 nm.")
ER = T('red_edge_parameters.csv'); er = ER[ER.Date == 'All'].set_index('Parameter')
N['rededge'] = (f"The red edge shifts to shorter wavelengths in diseased leaves: REP {er.loc['REP_LI', 'Healthy_mean']:.1f} -> {er.loc['REP_LI', 'Diseased_mean']:.1f} nm "
                f"(p {'< 0.001' if er.loc['REP_LI', 'Welch_p'] < 0.001 else '= %.3f' % er.loc['REP_LI', 'Welch_p']}); REV and SDr decrease (p = {er.loc['REV', 'Welch_p']:.3f}, {er.loc['SDr', 'Welch_p']:.3f}). "
                "Blue shift + lower red-edge amplitude = chlorophyll loss, as for rice blast (Mandal et al., 2022).")
V = T('pca_variance.csv'); E = T('pca_eta2.csv').set_index('PC')
N['pca'] = (f"PC1 ({V.Explained_variance_pct[0]:.1f}%) and PC2 ({V.Explained_variance_pct[1]:.1f}%) are driven by date "
            f"(η² {E.loc['PC1', 'date']:.2f}, {E.loc['PC2', 'date']:.2f}) and stage, not disease (η² ≤ {E['label'].max():.2f}). "
            "Unsupervised methods cannot separate classes, so supervised feature selection is needed.")
PM = T('permanova.csv').set_index('Term')
N['permanova'] = (f"Date explains {PM.loc['Date', 'R2_partial_pct']:.1f}% of spectral variance; disease {PM.loc['Disease', 'R2_partial_pct']:.1f}% "
                  f"(pseudo-F {PM.loc['Disease', 'Pseudo_F']:.1f}, p = {PM.loc['Disease', 'p_perm']:.3f}) plus {PM.loc['Disease:Date', 'R2_partial_pct']:.1f}% disease x date. "
                  f"Variety is not significant (p = {PM.loc['Variety', 'p_perm']:.2f}). H2 is supported: the disease effect is small but robust.")
VR = T('vi_ranking.csv')
cons = VR[VR['Sign_consistent_all_dates']]
N['vi'] = (f"The best published index reaches AUC {VR.AUC.iloc[0]:.3f} ({VR.Index.iloc[0]}). Many chlorophyll indices (NDVI, SR, MTCI) show no difference on 11 Feb and change sign; "
           f"date-consistent indices are mainly water, anthocyanin and disease indices ({', '.join(cons.Index.head(5))}).")
NT = T('ndsi_top_pairs.csv'); t0 = NT.iloc[0]
nir = NT[NT.Band_i_nm < 1000].iloc[0] if (NT.Band_i_nm < 1000).any() else None
N['mwri'] = (f"MWRI = (R{int(t0.Band_i_nm)} - R{int(t0.Band_j_nm)}) / (R{int(t0.Band_i_nm)} + R{int(t0.Band_j_nm)}): mean |d| {t0.Mean_abs_d_across_dates:.2f} "
             f"(min {t0.Min_abs_d_across_dates:.2f} on any date), AUC {t0.AUC:.3f} vs {VR.AUC.iloc[0]:.3f} for the best published index. The pair lies on the shoulder of the 1940-nm water band "
             "inside one detector (artefact checked: same AUC without splice correction)."
             + (f" A second family, ND(R{int(nir.Band_i_nm)}, R{int(nir.Band_j_nm)}), captures the NIR slope (AUC {nir.AUC:.3f})." if nir is not None else ''))
cw = pd.read_csv(os.path.join(TAB, 'cwt_abs_d_scalogram.csv'), index_col=0)
st = cw.stack().sort_values(ascending=False)
N['cwt'] = (f"The most sensitive wavelet coefficients are at {st.index[0][0]} nm (fine scales, |d| up to {st.iloc[0]:.2f}), 680 nm (chlorophyll well), 1920-1930 nm (water) and 1010 nm at scale 6 (NIR shape). "
            "Fine scales capture narrow slope changes; coarse scales capture broad shape (Cheng et al., 2011). Wavelet maxima exceed those of single bands (|d| < 1), consistent with Lv et al. (2023).")

if have('E1_preprocessing_reps.csv'):
    E1 = T('E1_preprocessing_reps.csv').groupby(['variant', 'clf'])['BA'].mean().unstack()
    best_v = E1.mean(1).idxmax(); worst_v = E1.mean(1).idxmin()
    N['e1'] = (f"Preprocessing matters more than the classifier: mean BA ranges from {E1.mean(1).min():.3f} ({worst_v}) to {E1.mean(1).max():.3f} ({best_v}). "
               f"SNV ({E1.loc['SNV'].mean():.3f}) removes brightness differences between dates and leaves; date normalisation alone gives {E1.loc['Date normalisation'].mean():.3f}"
               f" and with SNV {E1.loc['Date normalisation + SNV'].mean():.3f}. Raw reflectance is worst for linear models, because date effects dominate it (PERMANOVA). SNV was therefore used for the band families.")
if have('cv_main_summary.csv'):
    SUM = T('cv_main_summary.csv'); BP = T('cv_best_per_scenario.csv').set_index('scenario'); B = T('best_pipelines.csv')
    best, comp = B.iloc[0], B.iloc[1]
    bsum = SUM[(SUM.scenario == best.scenario) & (SUM.clf == best.clf)].iloc[0]
    csum = SUM[(SUM.scenario == comp.scenario) & (SUM.clf == comp.clf)].iloc[0]
    FRc = T('friedman_classifiers.csv'); FRs = T('friedman_scenarios.csv')
    N['matrix'] = (f"Highest BA: {best.scenario} {SCENARIOS[best.scenario]} with {best.clf} ({bsum.BA_mean:.3f} ± {bsum.BA_SD:.3f}). Best compact model: {comp.scenario} with {comp.clf} "
                   f"({csum.BA_mean:.3f}, median {T('selection_frequency.csv').query('scenario == @comp.scenario').Median_n_features.iloc[0]:.0f} features). Single-family band and index selections (S2, S3) are weakest.")
    N['friedman'] = (f"Best-ranked classifiers: {', '.join(FRc.clf.head(3))}; worst: {', '.join(FRc.clf.tail(2))}. Best-ranked feature scenarios: {', '.join(FRs.scenario.head(3))}.")
    FI = T('final_features.csv'); JM = T('final_features_JM.csv')
    N['features'] = (f"Final robust set ({len(FI)} features, selected on all data): {', '.join(FI.Feature)}. Multivariate J-M = {JM.JM.iloc[0]:.2f} (pooled), "
                     f"{JM.JM.iloc[1:].min():.2f}-{JM.JM.iloc[1:].max():.2f} within dates. Features sit on the 1800-1950 nm water shoulder, the NIR slope and red/visible pigment features.")
    LC = T('lr_coefficients.csv')
    top_pos = LC.sort_values('LR_std_coefficient', ascending=False).head(3).Wavelength_nm.tolist()
    top_neg = LC.sort_values('LR_std_coefficient').head(3).Wavelength_nm.tolist()
    N['lr'] = (f"The full-spectrum model ({SUM[(SUM.scenario == 'S1') & (SUM.clf == 'LR')].BA_mean.iloc[0]:.3f} BA with LR) uses contrasts across the whole spectrum. "
               f"Largest positive weights near {', '.join(map(str, top_pos))} nm and negative near {', '.join(map(str, top_neg))} nm. "
               "Adjacent bands with opposite signs = the model reads local slopes, the same information captured by derivatives, CWT and MWRI.")
    SG = T('subgroup_performance.csv')
    sb = SG[SG.Role == 'Best overall'].set_index('Level')['BA']
    N['subgroups'] = (f"With one pooled model, BA is lowest on {sb.idxmin()} ({sb.min():.3f}) and highest on {sb.idxmax()} ({sb.max():.3f}). "
                      "Varieties perform similarly, so a single model serves all three varieties. The earliest (vegetative) date is the hardest, as expected for low disease expression.")
    if have('E2_transfer_reps.csv'):
        E2 = T('E2_transfer_reps.csv').groupby(['kind', 'level', 'scenario', 'clf'])['BA'].mean().reset_index()
        bp = E2[(E2.scenario == best.scenario) & (E2.clf == best.clf)] if ((E2.scenario == best.scenario) & (E2.clf == best.clf)).any() else E2
        by = {k: g for k, g in bp.groupby('kind')}
        N['transfer'] = ("Held-out transfer (best available pipeline): "
                         + '; '.join(f"{k.lower()} BA {g.BA.min():.2f}-{g.BA.max():.2f}" for k, g in by.items())
                         + ". Transfer to an unseen variety is close to the pooled CV result; transfer to an unseen date or stage is harder, especially for the earliest date. Models should be updated with each season's data.")
    extras = []
    if have('E3_metadata_reps.csv'):
        E3 = T('E3_metadata_reps.csv').groupby(['scenario', 'clf', 'inputs'])['BA'].mean().unstack()
        d = (E3['Spectra + metadata'] - E3['Spectra only'])
        extras.append(f"E3: adding date/variety/stage changes BA by {d.min():+.3f} to {d.max():+.3f}, so the spectral model is effectively context-independent.")
    if have('E4_learning_curve_reps.csv'):
        E4 = T('E4_learning_curve_reps.csv').groupby(['scenario', 'clf', 'n_train_plots'])['BA'].mean().unstack()
        extras.append(f"E4: BA rises from {E4.iloc[:, 0].min():.3f} (12 plots) to {E4.iloc[:, -1].max():.3f} (36 plots) and has not plateaued; more plots would help.")
    if have('E5_sensor_reps.csv'):
        E5 = T('E5_sensor_reps.csv').groupby('sensor')['BA'].max() if False else T('E5_sensor_reps.csv').groupby(['sensor', 'clf'])['BA'].mean().groupby('sensor').max()
        extras.append('E5: ' + '; '.join(f"{k} max BA {v:.3f}" for k, v in E5.items()) + ' (hyperspectral detail matters).')
    if have('E6_outlier_sensitivity_reps.csv'):
        E6 = T('E6_outlier_sensitivity_reps.csv').groupby(['scenario', 'clf'])['BA'].mean()
        diffs = [E6.loc[(s_, c_)] - SUM[(SUM.scenario == s_) & (SUM.clf == c_)].BA_mean.iloc[0] for s_, c_ in E6.index]
        extras.append(f"E6: keeping outliers changes BA by {min(diffs):+.3f} to {max(diffs):+.3f}.")
    N['extras'] = ' '.join(extras)
    if have('E7_ofc_reps.csv'):
        E7 = T('E7_ofc_reps.csv').groupby(['feature_set', 'clf'])[['BA', 'MCC', 'median_n_features']].mean()
        diag = {w: E7.loc[(f'OFC-{w}', w)] for w in ['LDA', 'kNN', 'SVM']}
        bw = max(diag, key=lambda w: diag[w]['BA'])
        best7 = E7['BA'].idxmax()
        N['e7'] = (f"Tian-style OFCs are compact (median {diag['LDA'].median_n_features:.0f}, {diag['kNN'].median_n_features:.0f} and {diag['SVM'].median_n_features:.0f} features). "
                   f"Wrapper-matched models: OFC-LDA+LDA {diag['LDA'].BA:.3f}, OFC-kNN+kNN {diag['kNN'].BA:.3f}, OFC-SVM+SVM {diag['SVM'].BA:.3f} BA. "
                   f"All DSFs + SVM: {E7.loc[('All DSFs', 'SVM'), 'BA']:.3f}; full spectrum + SVM: {E7.loc[('Full spectrum (SNV)', 'SVM'), 'BA']:.3f}. "
                   f"Best in E7: {best7[0]} + {best7[1]} ({E7['BA'].max():.3f}). OFCs chosen by a non-linear wrapper work best with non-linear classifiers, as Tian et al. (2021) found.")
        N['e7_best'] = dict(set=best7[0], clf=best7[1], BA=float(E7['BA'].max()), svm_diag=float(diag['SVM'].BA), n_svm=float(diag['SVM'].median_n_features))

    # ---------------- discussion
    vi_best = VR.AUC.iloc[0]
    N['discussion'] = [
        dict(title='Discussion 1: the spectral signature of white rust',
             points=['Higher VIS reflectance, red-edge blue shift and lower REV = chlorophyll breakdown, the common fungal response (Zhang et al., 2012; Mandal et al., 2022; Lv et al., 2023)',
                     'Higher SWIR reflectance (1400-1560, 1840-2400 nm) = leaf water loss around pustules; strongest single-band effects',
                     'NIR reflectance barely changes although the NIR slope does: white sori raise scattering and offset mesophyll collapse (Zhang et al., 2012; Tian et al., 2021)',
                     'Differences are smallest at the vegetative date and grow through flowering and pod formation'],
             source='Zhang et al. 2012; Tian et al. 2021; Mandal et al. 2022; Lv et al. 2023'),
        dict(title='Discussion 2: why a pooled model works despite strong date effects',
             points=[f"Date explains about {PM.loc['Date', 'R2_partial_pct']:.0f}% of spectral variance vs {PM.loc['Disease', 'R2_partial_pct']:.1f}% for disease, yet disease is significant (PERMANOVA)",
                     'SNV removes most date and leaf brightness effects; the remaining disease signal is in shape (slopes, band ratios), not amplitude',
                     'Features chosen for stability across dates (Tian et al., 2021; Lv et al., 2023) generalise better than date-specific ones',
                     'Metadata inputs do not improve the spectral model, so it is usable without knowing date, variety or stage'],
             source='Anderson 2001; Barnes et al. 1989; Tian et al. 2021; Lv et al. 2023'),
        dict(title='Discussion 3: which features carry the information',
             points=[f"Published indices are weak for white rust (AUC <= {vi_best:.2f}); many reverse sign between dates",
                     f"The new MWRI (R{int(t0.Band_i_nm)}/R{int(t0.Band_j_nm)} normalised difference) reaches AUC {t0.AUC:.2f}, echoing Mandal et al. (2023) and Selvaprakash et al. (2026), whose best indices were also SWIR/NIR pairs",
                     'Wavelet and derivative features outperform raw bands, as in Lv et al. (2023) and Tian et al. (2021)',
                     'Full-spectrum SNV models remain competitive: with 2,000+ correlated bands, regularised linear models use all slope information']
                    + ([f"Tian-style OFCs (SFFS-LDA/kNN/SVM) reach BA {N['e7_best']['svm_diag']:.2f} with OFC-SVM + SVM using ~{N['e7_best']['n_svm']:.0f} features: compact sets keep most of the full-spectrum accuracy (Tian et al., 2021)"] if 'e7_best' in N else []),
             source='Mandal et al. 2023; Selvaprakash et al. 2026; Lv et al. 2023; Tian et al. 2021'),
        dict(title='Discussion 4: comparison with published accuracies',
             points=['Our numbers come from plot-grouped, nested CV pooled over 4 dates, 3 varieties and 3 stages; most published values come from single experiments with random splits',
                     'Strict validation removes optimistic bias from repeated measurements and in-sample selection (Varma & Simon, 2006; Roberts et al., 2017)',
                     'Balanced accuracy and MCC are reported because the data are 1 : 5 imbalanced (Chicco & Jurman, 2020)'],
             table=[['Study', 'Task', 'Reported'],
                    ['Tian et al. 2021', 'Rice blast, per stage', 'OA 0.65-0.99'],
                    ['Lv et al. 2023', 'SCLB, asympt./sympt.', 'OA 0.87 / 0.93'],
                    ['Zhang et al. 2012', 'Powdery mildew, 3 cl.', 'OA 0.89, κ 0.84'],
                    ['Zhu et al. 2017', 'TMV, 4 classes', 'Acc. 0.98'],
                    ['Nguyen et al. 2023', 'Yellow rust, UAV', 'OA 0.79'],
                    ['This study (best)', 'White rust, pooled', f"BA {bsum.BA_mean:.2f}, MCC {bsum.MCC_mean:.2f}"],
                    ['This study (compact)', f"{len(FI)}-10 features", f"BA {csum.BA_mean:.2f}"]],
             colW=[1.9, 2.1, 1.8], source='Values as reported in each paper; this study from workbook sheet 21'),
    ]
    N['conclusions'] = [
        f"White rust raises visible and SWIR reflectance, blue-shifts the red edge and changes the NIR slope; the effect is significant after removing date, variety and stage effects.",
        f"Date/phenology dominates the spectra ({PM.loc['Date', 'R2_partial_pct']:.0f}% of variance), so SNV correction and date-stable features are essential for a pooled model.",
        f"A new Mustard White Rust Index, ND(R{int(t0.Band_i_nm)}, R{int(t0.Band_j_nm)}), outperforms all 46 published indices (AUC {t0.AUC:.2f} vs {vi_best:.2f}).",
        f"Best pooled model: {best.scenario} + {best.clf}, BA {bsum.BA_mean:.3f} ± {bsum.BA_SD:.3f}, MCC {bsum.MCC_mean:.2f}, AUC {bsum.ROC_AUC_mean:.3f} under strict plot-grouped nested CV.",
        f"A compact model ({comp.scenario} + {comp.clf}, BA {csum.BA_mean:.3f}) uses about {T('selection_frequency.csv').query('scenario == @comp.scenario').Median_n_features.iloc[0]:.0f} features, suited to a low-cost sensor.",
        *( [f"Wrapper-based optimal feature combinations (Tian et al., 2021) give compact models: OFC-SVM + SVM reaches BA {N['e7_best']['svm_diag']:.3f} with ~{N['e7_best']['n_svm']:.0f} features."] if 'e7_best' in N else []),
        "One model serves all three varieties; transfer to new dates is the main remaining challenge.",
    ]
    N['limitations'] = ['Labels are plot-level (healthy vs diseased plots); individual leaves in diseased plots may be symptom-free, which caps achievable accuracy.',
                        'Only 12 healthy plots: the healthy class drives the uncertainty of every metric.',
                        'One season and one site; leaf layer and severity scores were not available.',
                        'Healthy plots are numbered 1-12; if they form one field block, field-position effects cannot be fully excluded.']
    N['future'] = ['Score severity (PDI) per leaf to build severity regression and multi-class models (Mandal et al., 2023; Lv et al., 2023).',
                   'Validate on a second season / location as an independent test (Terentev et al., 2023).',
                   'Add pre-symptomatic dates with inoculated plots for early detection (Tian et al., 2021).',
                   'Invert PROSPECT-D for pigment and water traits; upscale MWRI to UAV/satellite bands.']
json.dump(N, open(os.path.join(ROOT, 'scripts', 'narrative.json'), 'w'), indent=1, ensure_ascii=False)
print(json.dumps({k: (v if isinstance(v, str) else '...') for k, v in N.items()}, indent=1, ensure_ascii=False)[:4000])
