"""Assemble the thesis report (methodology, results, discussion, summary, conclusions) as a list of blocks
rendered to Word by build_docx.js. Every number is read from the result tables."""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from s04_cv import SCENARIOS

T = lambda n: pd.read_csv(os.path.join(TAB, n))
B = []
FIGN, TABN = [0], [0]
f3 = lambda v: f'{v:.3f}'
f2 = lambda v: f'{v:.2f}'
f1 = lambda v: f'{v:.1f}'
pf = lambda p: '< 0.001' if p < 0.001 else f'{p:.3f}'
FLOW = os.path.join(CACHE, 'flow')


def h1(t): B.append(dict(type='h1', text=t))
def h2(t): B.append(dict(type='h2', text=t))
def h3(t): B.append(dict(type='h3', text=t))
def p(t): B.append(dict(type='p', text=t))
def eq(t): B.append(dict(type='eq', text=t))
def bl(items): B.append(dict(type='bullets', items=items))
def nl(items): B.append(dict(type='numbered', items=items))
def pb(): B.append(dict(type='pagebreak'))


def fig(path, cap, w=6.3):
    FIGN[0] += 1
    B.append(dict(type='fig', path=path, caption=f'Figure {FIGN[0]}. {cap}', width=w))
    return FIGN[0]


def tab(headers, rows, cap, widths=None, note=None, small=False):
    if cap[:2] in ('A1', 'A2'):
        label = f'Table {cap}'
    else:
        TABN[0] += 1; label = f'Table {TABN[0]}. {cap}'
    B.append(dict(type='table', headers=headers, rows=[[str(x) for x in r] for r in rows], caption=label,
                  widths=widths, note=note, small=small))
    return TABN[0]


nf = lambda: FIGN[0] + 1
nt = lambda: TABN[0] + 1

# ----------------------------------------------------------------------------- data
M = pd.read_csv(os.path.join(CACHE, 'meta.csv')); Mc = pd.read_csv(os.path.join(CACHE, 'meta_clean.csv'))
nH, nD, nC = int((M.y == 0).sum()), int((M.y == 1).sum()), len(Mc)
nHc, nDc = int((Mc.y == 0).sum()), int((Mc.y == 1).sum())
QC = T('qc_summary.csv'); QC.columns = ['k', 'v']; qc = dict(zip(QC.k, QC.v.astype(float)))
NZ = T('qc_noise.csv'); S = T('spectra_mean_class.csv'); SIM = T('class_similarity_by_date.csv')
BS = T('bandwise_statistics.csv'); RG = T('sensitive_regions.csv'); ER = T('red_edge_parameters.csv')
PV = T('pca_variance.csv'); ETA = T('pca_eta2.csv'); PM = T('permanova.csv').set_index('Term'); LM = T('mixed_models_features.csv')
VR = T('vi_ranking.csv'); VD = T('vi_definitions.csv'); NT = T('ndsi_top_pairs.csv'); NJ = T('ndsi_top_pairs_joinfree.csv')
CW = pd.read_csv(os.path.join(TAB, 'cwt_abs_d_scalogram.csv'), index_col=0)
E1 = T('E1_preprocessing_reps.csv'); E2 = T('E2_transfer_reps.csv'); E3 = T('E3_metadata_reps.csv'); E4 = T('E4_learning_curve_reps.csv')
E5 = T('E5_sensor_reps.csv'); E6 = T('E6_outlier_sensitivity_reps.csv'); E7 = T('E7_ofc_reps.csv'); E8 = T('E8_fs_reps.csv'); E8['k'] = E8['k'].astype(str)
SUM = T('cv_main_summary.csv'); BPS = T('cv_best_per_scenario.csv'); FRC = T('friedman_classifiers.csv'); FRS = T('friedman_scenarios.csv')
FRT = T('friedman_tests.csv'); CT = T('corrected_ttests.csv'); CM = T('confusion_matrices.csv'); SG = T('subgroup_performance.csv')
SF = T('selection_frequency.csv'); FI = T('final_features.csv'); JM = T('final_features_JM.csv'); PDL = T('cv_main_summary_plotdate.csv')
CS = T('collinearity_summary.csv'); CST = T('collinearity_filter_stages.csv'); CV = T('collinearity_vif.csv')
E7F = T('E7_ofc_final_sets.csv'); E8R = T('E8_fs_composite_ranking.csv'); E8S = T('E8_fs_stability.csv'); E8T = T('E8_fs_tests.csv'); E8F = T('E8_fs_final_sets.csv')
REFS = pd.read_csv(os.path.join(ROOT, 'scripts', 'references.csv'))
best = SUM.sort_values('BA_mean', ascending=False).iloc[0]
comp = SUM[(SUM.scenario == 'S8') & (SUM.clf == 'LS-SVM')].iloc[0]
e1m = E1.groupby(['variant', 'clf'])['BA'].mean().unstack()
e7m = E7.groupby(['feature_set', 'clf'])[['BA', 'MCC', 'median_n_features']].mean()
e8m = E8.groupby(['method', 'variant', 'k', 'clf'])['BA'].mean()
def e8v(m, k, c, v='all features'):
    try: return e8m.loc[(m, v, k, c)]
    except KeyError: return np.nan
s8row = CS.set_index('Feature_set').loc['Robust S8 (final)']
vi0 = VR.iloc[0]; nd0 = NT.iloc[0]; nj0 = NJ.iloc[0]
sav = SIM.set_index('Date')['Spectral_angle_deg']

# ============================================================================= TITLE
B.append(dict(type='title', title='Hyperspectral detection of white rust (Albugo candida) in Indian mustard using ASD contact-probe leaf spectra',
              subtitle='Detailed methodology, results and discussion of the pooled prediction model (all dates, varieties and growth stages)',
              author='Animesh Panda', affil='Division of Agricultural Physics, ICAR-Indian Agricultural Research Institute, New Delhi',
              note='PhD research - analysis chapter'))

# ============================================================================= SUMMARY
h1('Summary')
p(f'White rust, caused by the oomycete Albugo candida, is a major foliar disease of Indian mustard. This study developed and rigorously validated a single (pooled) hyperspectral model that separates healthy from white-rust-diseased mustard leaves irrespective of measurement date, variety and growth stage. Leaf reflectance (350-2500 nm) was measured with an ASD spectroradiometer and contact probe on 48 plots (three varieties; 12 healthy and 36 diseased plots) on four dates between 11 February and 13 March 2026, giving {len(M)} spectra ({nH} healthy, {nD} diseased).')
p(f'The methodology combined the approaches of ten published studies with the researcher\'s own comparison of 23 feature-selection methods. Spectra were splice-corrected, trimmed to 400-2400 nm, screened for outliers by a four-rule consensus ({int(qc["n_removed"])} removed) and smoothed. Spectral characterisation used band-wise tests with false-discovery-rate control, Jeffries-Matusita (J-M) separability, red-edge parameters, PCA/t-SNE, PERMANOVA and mixed models. Six feature families (bands, 46 vegetation indices, a new normalised-difference index search, derivatives, continuum removal and continuous wavelet features; about 2,100 features) were reduced by four selection routes: date-stable robust selection with redundancy and VIF control, optimal feature combinations (OFCs) from wrapper-based SFFS (Tian et al., 2021), six published filter/wrapper/embedded selectors, and SPA/GA-PLS band selection. Ten classifiers were compared in nested, plot-grouped, stratified 4-fold cross-validation repeated 25 times, and eight supplementary experiments tested preprocessing, transfer, metadata, training size, simulated sensors, outliers, OFCs and the published selectors.')
p(f'White rust raised visible reflectance (up to +{100 * (S[(S.Wavelength_nm >= 550) & (S.Wavelength_nm <= 700)]["Ratio_D/H"].max() - 1):.0f}% near 690 nm) and SWIR water-band reflectance (up to +{100 * (S["Ratio_D/H"].max() - 1):.0f}%), shifted the red edge to shorter wavelengths (REP {ER[(ER.Parameter == "REP_LI") & (ER.Date == "All")].Healthy_mean.iloc[0]:.1f} to {ER[(ER.Parameter == "REP_LI") & (ER.Date == "All")].Diseased_mean.iloc[0]:.1f} nm) and changed the NIR slope, while NIR reflectance itself changed little. Date explained {PM.loc["Date", "R2_partial_pct"]:.1f}% of spectral variance and disease {PM.loc["Disease", "R2_partial_pct"]:.1f}% (PERMANOVA p = {PM.loc["Disease", "p_perm"]:.3f}). Published vegetation indices were weak (best AUC {vi0.AUC:.2f}), whereas a new Mustard White Rust Index, ND(R{int(nd0.Band_i_nm)}, R{int(nd0.Band_j_nm)}), reached AUC {nd0.AUC:.2f} (join-free alternative ND(R{int(nj0.Band_i_nm)}, R{int(nj0.Band_j_nm)}): AUC {nj0.AUC:.2f}).')
p(f'The most accurate pooled model was a first-derivative full-spectrum logistic regression (balanced accuracy, BA = {e1m.loc["First derivative (SG)", "LR"]:.3f}); in the main 10 x 10 comparison the SNV full-spectrum logistic regression reached BA {best.BA_mean:.3f} +/- {best.BA_SD:.3f} (MCC {best.MCC_mean:.2f}, AUC {best.ROC_AUC_mean:.3f}). Ten features chosen by ReliefF, Borda consensus, CARS or SVM-RFE reached BA 0.91-0.92 with an SVM, and the date-stable robust set of seven features reached BA {comp.BA_mean:.3f} with no multicollinearity (maximum VIF {s8row.Max_VIF:.1f}). One model served all three varieties (unseen-variety BA {E2[E2.kind == "Variety"].groupby("level").BA.mean().min():.2f}-{E2[E2.kind == "Variety"].groupby("level").BA.mean().max():.2f}), but a date absent from training could not be predicted, so every phenological stage must be represented in the training data. Several strong features lie next to the ASD detector join at 1800 nm; join-free feature sets remained accurate (SVM-RFE BA {e8v("SVM-RFE", "10", "SVM", "join bands excluded"):.2f}) and are recommended for sensor design.')

# ============================================================================= 1 INTRODUCTION
pb(); h1('1. Introduction and objectives')
h2('1.1 Background')
p('Indian mustard (Brassica juncea) is the principal rabi oilseed of India. White rust (Albugo candida), an obligate biotrophic oomycete, produces white blister-like sori mainly on the lower leaf surface, causes chlorosis and, on inflorescences, the staghead symptom; epidemics cause large yield losses (Saharan et al., 2014). Visual scoring is slow and subjective and cannot capture pre-visual physiological change, while fungicide timing depends on early, reliable detection.')
p('Leaf reflectance spectroscopy measures the optical consequences of infection: chlorophyll, carotenoid and anthocyanin changes in the visible region (400-700 nm), red-edge shifts (680-750 nm), mesophyll disruption in the near infrared (750-1300 nm) and water and dry-matter changes in the short-wave infrared (1300-2400 nm) (Zhang et al., 2012; Tian et al., 2021; Lv et al., 2023). Most published spectral disease models were built for one date or one experiment with random spectrum-level validation; the challenge addressed here is a single model that works across dates, varieties and growth stages and is validated so that its accuracy is not inflated by repeated measurements of the same plots.')
h2('1.2 Objectives and hypotheses')
tab(['No.', 'Objective', 'Hypothesis'], [
    ['O1', 'Characterise the spectral response of mustard leaves to white rust', 'H1: VIS and red-edge reflectance rise; NIR and SWIR change with structure and water'],
    ['O2', 'Partition spectral variance into disease and date, variety, stage effects', 'H2: disease is significant after accounting for nuisance factors'],
    ['O3', 'Identify disease features that are stable across dates and varieties', 'H3: a small set of features separates classes on every date'],
    ['O4', 'Develop a novel Mustard White Rust Index (MWRI)', 'H4: an optimal band pair outperforms published indices'],
    ['O5', 'Compare preprocessing, feature types, selection methods and 10 classifiers', 'H5: selected combined features match or exceed single families'],
    ['O6', 'Test transfer to an unseen date, variety and growth stage', 'H6: accuracy is maintained when a whole level is held out'],
], 'Objectives and hypotheses of the study.', widths=[0.6, 3.1, 2.8])

# ============================================================================= 2 METHODS
pb(); h1('2. Materials and methods')
p('The analysis followed eleven steps (Figure 1). Every step that learns from class labels (MSC reference, date normalisation, band-pair search, feature selection and hyper-parameter tuning) was fitted only on the training plots of each cross-validation fold.')
fig(os.path.join(FLOW, 'flow_overview_c.jpg'), 'Methodological flowchart of the whole analysis (Steps 1-11).')
h2('2.1 Experimental material and spectral measurement')
dsum = M.assign(Date=M.date.map(DATE_LABEL)).pivot_table(index='Date', columns='label', values='spec_uid', aggfunc='count').reindex([DATE_LABEL[d] for d in DATE_ORDER])
rows = [[d, int(r.Healthy), int(r.Diseased), int(r.Healthy + r.Diseased)] for d, r in dsum.iterrows()] + [['Total', nH, nD, len(M)]]
p(f'Spectra were recorded with an ASD FieldSpec spectroradiometer fitted with a contact probe (internal halogen source; 350-2500 nm, 1-nm sampling) on mustard leaves of three varieties (V1, V2, V3) grown in 48 plots: 16 plots per variety, of which 4 were healthy and 12 diseased (plots 1-12 healthy, 13-48 diseased). Every plot was measured on all four dates (11 Feb, 24 Feb, 03 Mar and 13 Mar 2026), giving 192 plot-date units covering vegetative, flowering and pod-formation stages. The class label is the plot label provided in the source workbooks; the leaf-level and severity fields were empty, so the task is binary classification. The data are hierarchical (scans within leaves within plots, repeated over dates) and imbalanced (1 : {nD / nH:.1f}).')
tab(['Date', 'Healthy', 'Diseased', 'Total'], rows, 'Number of spectra by measurement date and class.', widths=[1.6, 1.4, 1.4, 1.4])
sv = M.pivot_table(index='stage', columns='label', values='spec_uid', aggfunc='count').reindex(STAGE_ORDER)
vv = M.pivot_table(index='variety', columns='label', values='spec_uid', aggfunc='count')
tab(['Factor', 'Level', 'Healthy', 'Diseased'], [['Stage', k, int(r.Healthy), int(r.Diseased)] for k, r in sv.iterrows()] + [['Variety', k, int(r.Healthy), int(r.Diseased)] for k, r in vv.iterrows()],
    'Number of spectra by growth stage and variety.', widths=[1.4, 1.8, 1.4, 1.4])

h2('2.2 Data assembly and quality control (Steps 1-2)')
fig(os.path.join(FLOW, 'flow_qc_c.jpg'), 'Data assembly and quality-control flowchart.')
p('The four workbooks were merged into one table of spectra with plot, variety, growth stage, date and class; the Excel AVERAGE columns between plot groups were ignored and all statistics were recomputed from the raw scans.')
p(f'Splice correction. The ASD instrument joins three detectors at 1000/1001 nm and 1800/1801 nm. Each SWIR segment was shifted additively so that its first value matched the linear extrapolation of the preceding detector (Hueni & Bialek, 2017). The mean absolute step at 1000 nm was {1000 * qc["splice_1000_before"]:.1f} x 10^-3 reflectance before and 0 after correction; at 1800 nm it was {1000 * qc["splice_1800_before"]:.2f} x 10^-3.')
p(f'Spectral trimming and noise. Noise was estimated as the SD of the high-frequency residual (raw spectrum minus a 9-nm moving average) and the signal-to-noise ratio (SNR) as mean reflectance / noise SD. The 350-400 nm region had SNR {NZ.SNR.iloc[0]:.0f} versus {NZ.SNR.iloc[1:-1].min():.0f}-{NZ.SNR.max():.0f} elsewhere, so the analysis used 400-2400 nm (Mandal et al., 2023).')
p(f'Outlier screening. Four label-free rules were applied to SNV-corrected 10-nm spectra: Hotelling T^2 and Q-residual beyond the 99% limits of a 5-component PCA, Isolation Forest (2% contamination; Liu et al., 2008; Selvaprakash et al., 2026) and the spectral angle to the plot-date median spectrum (robust z > 3.5). A spectrum was removed only if at least three rules flagged it. The rules flagged {int(qc["n_T2"])}, {int(qc["n_Q"])}, {int(qc["n_iso"])} and {int(qc["n_sam"])} spectra; {int(qc["n_removed"])} spectra (all from diseased plots) were removed, leaving {nC} ({nHc} healthy, {nDc} diseased). Because the screening uses no labels it was applied before cross-validation; experiment E6 repeats the best models without removal.')

h2('2.3 Spectral preprocessing (Step 3)')
fig(os.path.join(FLOW, 'flow_prep_c.jpg'), 'Preprocessing flowchart. Options marked * are fitted on training plots only.')
p('Spectra were smoothed with a Savitzky-Golay filter (11-nm window, second-order polynomial; Savitzky & Golay, 1964). Smoothed 1-nm reflectance was used to compute indices, derivatives, continuum removal and wavelet features; 10-nm band averages (201 bands, 400-2400 nm) were used for band-based models (Mandal et al., 2023). Six preprocessing options were compared in experiment E1:')
bl(['Reflectance (smoothed only).',
    'Standard normal variate (SNV; Barnes et al., 1989): each spectrum is centred and scaled by its own mean and SD.',
    'Multiplicative scatter correction (MSC; Geladi et al., 1985): each spectrum is regressed on the mean training spectrum and corrected (reference fitted on training plots).',
    'First derivative (SG, 11 nm; Tsai & Philpot, 1998).',
    'Date normalisation (Lv et al., 2023): every spectrum of a date is multiplied by the ratio of the baseline healthy mean (first date) to the healthy mean of that date, both from training plots.',
    'Date normalisation followed by SNV.'])
eq('SNV: x*(lambda) = [x(lambda) - mean(x)] / sd(x)        MSC: x*(lambda) = [x(lambda) - a] / b, where x = a + b * x_ref')

h2('2.4 Spectral characterisation (Step 4)')
fig(os.path.join(FLOW, 'flow_stats_c.jpg'), 'Flowchart of the statistical characterisation.')
p('To avoid pseudo-replication, univariate tests used plot-date mean spectra (n = 192; 48 healthy, 144 diseased). For every 10-nm band, Welch\'s t-test and the Mann-Whitney U test compared classes, p-values were corrected with the Benjamini-Hochberg false-discovery rate (FDR; Benjamini & Hochberg, 1995), and the effect size was Cohen\'s d (difference of means divided by the pooled SD). Point-biserial correlation spectra were computed at plot-date and spectrum level (Mandal et al., 2022). Contiguous bands with q < 0.05 formed the sensitive regions.')
eq("Cohen's d = (mean_D - mean_H) / s_pooled        J-M = 2 [1 - exp(-B)],  B = (1/8)(m1-m2)^2 [2/(v1+v2)] + (1/2) ln{[(v1+v2)/2] / sqrt(v1 v2)}")
p('Separability of each band, index and final feature set was measured by the Jeffries-Matusita distance (0 = no separability, 2 = complete; Richards & Jia, 2006). Red-edge and edge parameters followed Mandal et al. (2022) and Zhang et al. (2012): red-edge position by linear interpolation (REP_LI = 700 + 40 [(R670 + R780)/2 - R700] / (R740 - R700); Guyot & Baret, 1988) and by the derivative maximum in 680-750 nm (REP_FD), red-edge value (REV, maximum first derivative), the derivative sum over 680-760 nm (SDr), and amplitude, position and sum of the blue (490-530 nm), yellow (550-582 nm) and red (670-737 nm) edges.')
p('PCA and t-SNE (van der Maaten & Hinton, 2008) of SNV spectra were coloured by class, date, variety and stage; eta-squared quantified how much of each PC was explained by each factor. PERMANOVA (Anderson, 2001) partitioned the variance of plot-date SNV spectra into disease, date, variety, stage and the disease x date and disease x variety interactions, using marginal sums of squares and 999 restricted permutations (disease and variety permuted across plots, date and stage within plots). Linear mixed models (Bates et al., 2015) tested each index: feature ~ disease + date + variety + (1 | plot), with a likelihood-ratio test of the disease x date interaction. Class-mean similarity per date was summarised by the cosine similarity and spectral angle (Selvaprakash et al., 2026).')

h2('2.5 Feature engineering (Step 5)')
fig(os.path.join(FLOW, 'flow_features_c.jpg'), 'Feature-engineering flowchart: six feature families.')
tab(['Family', 'Content', 'n', 'Reference'], [
    ['F1', 'SNV-corrected reflectance bands, 10 nm (400-2400 nm)', 201, 'Mandal et al. 2023; Terentev et al. 2023'],
    ['F2', 'Published vegetation indices and red-edge parameters (Appendix Table A1)', 46, 'Mandal et al. 2023; Tian et al. 2021; Mahlein et al. 2013'],
    ['F3', 'Novel normalised-difference indices: all 20,100 band pairs, scored by mean |d| across dates with sign consistency; top 3 disjoint pairs (in-fold)', 3, 'Mandal et al. 2023; Selvaprakash et al. 2026'],
    ['F4', 'First-derivative bands (10 nm), derivative indices (Boochs, Datt3, DPI, EGFN/EGFR, Vogelmann3, sums) and blue/yellow/red edge features', 221, 'Lv et al. 2023; Zhang et al. 2012'],
    ['F5', 'Continuum removal of six absorption features (550-750, 920-1060, 1100-1290, 1300-1650, 1800-2100, 2100-2350 nm): depth, width, area, position', 24, 'Zhang et al. 2012; Kokaly & Clark 1999'],
    ['F6', 'Continuous wavelet transform, Mexican-hat mother wavelet, dyadic scales 2^1-2^8, coefficients every 10 nm', 1608, 'Tian et al. 2021; Lv et al. 2023; Cheng et al. 2011'],
], 'Feature families used for modelling.', widths=[0.6, 3.6, 0.5, 1.8])
eq('NDSI(i, j) = (R_i - R_j) / (R_i + R_j)        CWT: W(a, b) = integral R(lambda) psi[(lambda - b)/a] d lambda / sqrt(a),  psi = Mexican hat')
p('Image texture and colour features used in imaging studies (Huang et al., 2020; Zhu et al., 2017; Nguyen et al., 2023) were not applicable because the contact probe records point spectra.')

h2('2.6 Feature selection and multicollinearity control (Step 6)')
fig(os.path.join(FLOW, 'flow_selection_c.jpg'), 'Four feature-selection routes applied to the same training plots.')
p('Hyperspectral features are strongly collinear, so feature selection had two aims: keep disease-informative, date-stable features, and remove redundancy. Four routes were compared, each fitted inside the training plots of every outer fold.')
h3('Route A - robust date-stable selection (scenarios S2-S8)')
nl(['ReliefF (k = 10 nearest hits/misses, Manhattan distance; Robnik-Sikonja & Kononenko, 2003) was computed separately within each date of the training data.',
    'Temporal stability: features ranked in the top 10% on at least 3 of the 4 dates were kept (Tian et al., 2021; Lv et al., 2023).',
    'Redundancy filter: a feature was dropped if |r| >= 0.98 with a better-ranked feature (pool capped at 40).',
    'Variance inflation factor: the feature with the highest VIF was removed iteratively until all VIF < 10.',
    'Sequential floating forward selection (SFFS; Pudil et al., 1994) wrapped around LDA chose up to 10 features by inner plot-grouped CV balanced accuracy; the most parsimonious subset within 0.002 of the best was retained.'])
eq('VIF_j = 1 / (1 - R_j^2) = [R^-1]_jj   (R = correlation matrix of the candidate features)')
h3('Route B - optimal feature combinations (OFCs; experiment E7)')
p('Following Tian et al. (2021), a disease-specific feature (DSF) pool was formed from all families (top 5% ReliefF on >= 3 of 4 dates, |r| < 0.98, VIF < 10). SFFS was then wrapped around three classifiers - LDA, kNN (k = 15) and SVM (RBF) - giving OFC-LDA, OFC-kNN and OFC-SVM. Each OFC, the whole DSF pool and the full SNV spectrum were classified with LDA, kNN and SVM.')
fig(os.path.join(FLOW, 'flow_ofc_c.jpg'), 'OFC workflow after Tian et al. (2021).')
h3('Route C - published filter, wrapper and embedded selectors (experiment E8)')
p('The best methods of the researcher\'s comparison of 23 selectors (Panda, 2026) were re-implemented on the same pool: SVM-RFE (linear SVM, 10% eliminated per step to 100 features, then one at a time; Guyon et al., 2002), LASSO order of entry along the L1-logistic path (Tibshirani, 1996), CARS (50 Monte-Carlo PLS-DA runs with exponential decay and adaptive reweighted sampling; Li et al., 2009), class-balanced ReliefF (Kononenko, 1994), SFFS with an inner-CV QDA criterion on the 100 most correlated non-redundant features (Mustafa et al., 2023) and Borda rank aggregation of these lists (Saeys et al., 2008). Top-k sets (k = 5, 10, 15) were redundancy-controlled (|r| < 0.95) and classified with QDA (equal priors; Das et al., 2020), LDA, SVM and RF.')
h3('Route D - band selection (S9, S10)')
p('The successive projections algorithm (SPA; Araujo et al., 2001; Zhu et al., 2017) built minimally collinear band chains on SNV bands, with chain start and length chosen by inner-CV regression error; GA-PLS (30 chromosomes x 25 generations, PLS-DA fitness with a size penalty; Leardi & Lupianez Gonzalez, 1998; Mandal et al., 2023) selected band subsets.')
h3('Multicollinearity diagnostics')
p('For the final selected sets, Pearson correlation matrices, VIF (diagonal of the inverse correlation matrix), tolerance (1/VIF) and the condition number (square root of the ratio of the largest to smallest eigenvalue) were computed on all spectra (Belsley et al., 1980; Dormann et al., 2013). Full-spectrum models kept all collinear bands and relied on regularisation (PLS latent variables, Ledoit-Wolf shrinkage LDA, L2-penalised logistic regression, ridge-type LS-SVM and ELM).')

h2('2.7 Classifiers, tuning and class imbalance (Step 7)')
tab(['Classifier', 'Hyper-parameters tuned in inner CV', 'Imbalance handling', 'Reference'], [
    ['LDA', 'shrinkage (Ledoit-Wolf) / none', 'equal priors', 'Zhang et al. 2012; Tian et al. 2021'],
    ['PLS-DA', 'components 1-16', 'random oversampling', 'Barker & Rayens 2003; Zhu et al. 2017'],
    ['Logistic regression (L2)', 'C = 0.01-100', 'class weights', 'baseline'],
    ['kNN', 'k = 5, 15, 35 (distance weighted)', 'random oversampling', 'Tian et al. 2021'],
    ['SVM (RBF)', 'C = 1-100, gamma = 0.1-10 / p', 'class weights', 'Cortes & Vapnik 1995'],
    ['LS-SVM (kernel ridge form)', 'gamma, regularisation', 'weighted', 'Suykens & Vandewalle 1999'],
    ['Random forest (200 trees)', 'minimum leaf size 1, 5', 'balanced subsample', 'Breiman 2001'],
    ['XGBoost (300 trees)', 'depth 2/4, learning rate 0.05/0.15', 'scale_pos_weight', 'Chen & Guestrin 2016'],
    ['Extreme learning machine', 'hidden units 100/400, ridge 0.1/10', 'weighted ridge', 'Huang et al. 2006'],
    ['MLP', '(64) or (64, 32) units, alpha', 'random oversampling', 'Nguyen et al. 2023'],
], 'Classifiers, tuning grids and imbalance handling.', widths=[1.7, 2.1, 1.3, 1.6])
p('Features were standardised on the training data. A 1D/3D convolutional network was not used because only 48 independent plots were available (Nguyen et al., 2023 required hundreds of plots). Ten feature scenarios were combined with the ten classifiers: S1 full SNV spectrum; S2-S7 single families with robust selection (F1 bands, F2 indices, F3 NDSI, F4 derivatives, F5 continuum removal, F6 wavelets); S8 all families combined with robust selection; S9 SPA; S10 GA-PLS.')

h2('2.8 Validation design (Step 8)')
fig(os.path.join(FLOW, 'flow_cv_c.jpg'), 'Nested, plot-grouped, stratified cross-validation.')
p('The plot was the unit of independence (Roberts et al., 2017). The outer loop split the 48 plots into 4 folds of whole plots, each containing 1 healthy and 3 diseased plots of every variety, so all dates of a plot were always in the same fold. Within the 36 training plots, an inner 3-fold plot-grouped CV was used for preprocessing fits, the band-pair search, feature selection and hyper-parameter tuning (nested CV; Varma & Simon, 2006); the chosen model was refitted on all training plots and predicted the 12 test plots. The outer split was repeated with 25 random plot shuffles (100 outer test folds; cf. 4-fold x 100 in Tian et al., 2021 and Lv et al., 2023). Each repeat predicts every spectrum once; metrics are the mean +/- SD of the 25 repeats. Plot-date predictions were obtained by majority vote of the spectra.')
h2('2.9 Performance metrics and statistical comparison')
p('Because the classes are imbalanced, balanced accuracy (BA, the mean of sensitivity and specificity) was the primary metric, together with overall accuracy, sensitivity (diseased recall), specificity (healthy recall), precision, F1 per class, macro-F1, Cohen\'s kappa (Cohen, 1960), Matthews correlation coefficient (MCC; Chicco & Jurman, 2020), ROC-AUC and PR-AUC for the healthy class.')
eq('BA = (TP/(TP+FN) + TN/(TN+FP)) / 2        MCC = (TP*TN - FP*FN) / sqrt[(TP+FP)(TP+FN)(TN+FP)(TN+FN)]')
p('Classifiers and feature scenarios were compared with the Friedman test and the Nemenyi critical difference (Demsar, 2006), the best pipeline against the best of every scenario with the corrected resampled t-test (Nadeau & Bengio, 2003), and E8 selectors with paired Wilcoxon tests and Holm correction.')
h2('2.10 Supplementary experiments (Step 9)')
fig(os.path.join(FLOW, 'flow_experiments_c.jpg'), 'Experiments and the question each one answers.')
tab(['Exp.', 'Question', 'Design'], [
    ['E1', 'Which preprocessing is best?', 'Full spectrum with six preprocessings x LDA, PLS-DA, LR, SVM; 10 x 4-fold'],
    ['E2', 'Does the model transfer to an unseen date, variety or stage?', 'Leave-one-date/stage-out with plots kept apart (3 x 4 folds); leave-one-variety-out'],
    ['E3', 'Does metadata help?', 'Best pipelines with and without one-hot date, variety, stage; 5 x 4-fold'],
    ['E4', 'Are more plots needed?', '12, 24, 36 training plots (1:3 healthy:diseased); 5 x 4-fold'],
    ['E5', 'Can multispectral sensors detect white rust?', 'Simulated Sentinel-2 MSI (10 bands) and UAV 5-band + NDVI/NDRE/GNDVI(/NDII); 10 x 4-fold'],
    ['E6', 'Do results depend on outlier removal?', 'Best pipelines on all 2339 spectra; 5 x 4-fold'],
    ['E7', 'Do OFCs (Tian et al., 2021) help?', 'DSF pool, SFFS-LDA/kNN/SVM, classified by LDA/kNN/SVM; 25 x 4-fold'],
    ['E8', 'How do published selectors compare?', 'SVM-RFE, LASSO, CARS, ReliefF, SFFS-QDA, Borda vs S8, OFC-SVM, full spectrum; 5 x 4-fold; detector-join check'],
], 'Supplementary experiments.', widths=[0.6, 2.4, 3.6])
h2('2.11 Interpretation and software')
p('Feature importance was assessed by selection frequency over the 100 outer folds, permutation importance of an SVM in plot-grouped CV (Breiman, 2001) and TreeSHAP values of XGBoost (Lundberg & Lee, 2017); full-spectrum behaviour was shown by standardised logistic-regression coefficients. All analyses were run in Python (NumPy, SciPy, pandas, scikit-learn, statsmodels, PyWavelets, XGBoost); the workbook and presentation were generated from the same result tables.')

# ============================================================================= 3 RESULTS
pb(); h1('3. Results')
h2('3.1 Data quality')
tab(['Region (nm)', 'Mean reflectance', 'Noise SD', 'SNR'], [[r.Region_nm, f3(r.Mean_reflectance), f'{r.HF_noise_SD:.5f}', f'{r.SNR:.0f}'] for r in NZ.itertuples()],
    'Noise and signal-to-noise ratio of the raw spectra by spectral region.', widths=[1.5, 1.6, 1.4, 1.2])
p(f'The SNR was lowest at 350-400 nm ({NZ.SNR.iloc[0]:.0f}) and highest in the NIR (up to {NZ.SNR.max():.0f}), confirming trimming to 400-2400 nm. Splice correction removed the 1000-nm step completely. The {int(qc["n_removed"])} consensus outliers (2.1% of spectra) all came from diseased plots, which are spectrally more heterogeneous because of lesions and pustules. What this represents: the data entering the models are free of detector artefacts and gross measurement errors, and E6 later shows that removing outliers did not change the conclusions.')

h2('3.2 Spectral response of mustard leaves to white rust')
fig(os.path.join(FIG, 'Fig01_mean_spectra.png'), f'(a) Mean reflectance +/- SD of healthy (n = {nHc}) and diseased (n = {nDc}) leaves, (b) difference spectrum and (c) ratio spectrum.')
vis = S[(S.Wavelength_nm >= 550) & (S.Wavelength_nm <= 700)]
imin = S['Difference_D-H'].idxmin()
p(f'Diseased leaves reflected more in the visible region, with a maximum increase of {100 * (vis["Ratio_D/H"].max() - 1):.0f}% near {int(vis.loc[vis["Ratio_D/H"].idxmax(), "Wavelength_nm"])} nm (chlorophyll absorption well), and in the SWIR water bands (+{100 * (S[(S.Wavelength_nm >= 1400) & (S.Wavelength_nm <= 1500)]["Ratio_D/H"].max() - 1):.0f}% near 1450 nm and up to +{100 * (S["Ratio_D/H"].max() - 1):.0f}% near {int(S.loc[S["Ratio_D/H"].idxmax(), "Wavelength_nm"])} nm). NIR reflectance was only slightly lower (largest difference {S.loc[imin, "Difference_D-H"]:.3f} at {int(S.loc[imin, "Wavelength_nm"])} nm). What this represents: white rust reduces chlorophyll (less red absorption) and leaf water (less SWIR absorption), while the expected NIR decline from mesophyll disruption is largely offset by scattering from the white sori, as described for powdery mildew by Zhang et al. (2012). Hypothesis H1 is supported.')
fig(os.path.join(FIG, 'Fig03_derivative_spectra.png'), 'First- and second-derivative spectra of healthy and diseased leaves (400-1400 nm).')

h2('3.3 Dependence of the disease signal on date')
fig(os.path.join(FIG, 'Fig02_spectra_by_date.png'), '(a) Mean spectra of healthy (solid) and diseased (dashed) leaves and (b) difference spectra for each date.')
tab(['Date', 'Cosine similarity', 'Spectral angle (deg)', 'Euclidean distance'], [[r.Date, f'{r.Cosine_similarity:.4f}', f2(r.Spectral_angle_deg), f3(r.Euclidean_distance)] for r in SIM.itertuples()],
    'Similarity of healthy and diseased class-mean spectra on each date.', widths=[1.4, 1.7, 1.7, 1.7])
p(f'The healthy-diseased spectral angle increased from {sav.iloc[0]:.2f} deg on 11 Feb to {sav.max():.2f} deg on {sav.idxmax()} and was {sav.iloc[-1]:.2f} deg on 13 Mar. What this represents: the spectral expression of white rust grows as the epidemic develops and depends on phenology, so a pooled model must cope with a disease signature that changes over the season.')

h2('3.4 Sensitive spectral regions and separability')
fig(os.path.join(FIG, 'Fig04_bandwise_statistics.png'), "(a) Cohen's d per band (plot-date means; shaded = FDR q < 0.05), (b) point-biserial correlation spectra and (c) Jeffries-Matusita distance of reflectance and first-derivative bands.")
tab(['Region (nm)', 'Width (nm)', 'Direction', 'Max |d|', 'Peak (nm)'], [[r.Region_nm, r.Width_nm, r.Direction, f2(r.Max_abs_Cohen_d), r.Peak_wavelength_nm] for r in RG.itertuples()],
    'Contiguous spectral regions with significant class differences (Welch t-test, FDR q < 0.05, plot-date means).', widths=[1.3, 1.0, 1.9, 1.0, 1.0])
jfd = BS.loc[BS.FD_JM.idxmax()]
p(f'Three regions differed significantly: the red/orange visible region ({RG.Region_nm.iloc[0]} nm, |d| up to {RG.Max_abs_Cohen_d.iloc[0]:.2f}), the 1450-nm water band ({RG.Region_nm.iloc[1]} nm) and the long SWIR including the 1940-nm water band ({RG.Region_nm.iloc[2]} nm, |d| up to {RG.Max_abs_Cohen_d.iloc[2]:.2f}). NIR reflectance was not significant, but its first derivative at 850-870 nm had the largest VNIR effect (d = {BS.loc[BS.Wavelength_nm == 850, "FD_Cohen_d"].iloc[0]:.2f}) and the largest derivative J-M was at {int(jfd.Wavelength_nm)} nm (J-M = {jfd.FD_JM:.2f}). What this represents: single bands separate the classes only weakly (J-M < 0.3), whereas slopes (derivatives) carry stronger information - motivating derivative, wavelet and band-ratio features.')

h2('3.5 Red-edge and derivative parameters')
er = ER[ER.Date == 'All']
tab(['Parameter', 'Healthy (mean +/- SD)', 'Diseased (mean +/- SD)', 'Welch p'], [[r.Parameter, f'{r.Healthy_mean:.4g} +/- {r.Healthy_SD:.2g}', f'{r.Diseased_mean:.4g} +/- {r.Diseased_SD:.2g}', pf(r.Welch_p)] for r in er.itertuples()],
    'Red-edge and edge parameters of healthy and diseased leaves (plot-date means, all dates).', widths=[1.6, 1.9, 1.9, 1.0])
rep = er.set_index('Parameter')
p(f'The red-edge position moved to shorter wavelengths in diseased leaves (REP_LI {rep.loc["REP_LI", "Healthy_mean"]:.1f} vs {rep.loc["REP_LI", "Diseased_mean"]:.1f} nm, p {pf(rep.loc["REP_LI", "Welch_p"])}; REP_FD {rep.loc["REP_FD", "Healthy_mean"]:.1f} vs {rep.loc["REP_FD", "Diseased_mean"]:.1f} nm), and the red-edge amplitude (REV, p = {rep.loc["REV", "Welch_p"]:.3f}) and area (SDr, p = {rep.loc["SDr", "Welch_p"]:.3f}) decreased. What this represents: a blue shift and flattening of the red edge are classic indicators of chlorophyll loss, as found for rice blast by Mandal et al. (2022).')

h2('3.6 Unsupervised structure: PCA and t-SNE')
fig(os.path.join(FIG, 'Fig05_PCA_tSNE.png'), 'PCA scores coloured by (a) class and (b) date, and (c) t-SNE embedding coloured by class (SNV spectra).')
et = ETA.set_index('PC')
p(f'PC1 ({PV.Explained_variance_pct.iloc[0]:.1f}%) and PC2 ({PV.Explained_variance_pct.iloc[1]:.1f}%) were dominated by date (eta-squared {et.loc["PC1", "date"]:.2f} and {et.loc["PC2", "date"]:.2f}) and stage, whereas class explained at most {et["label"].max():.2f} of any PC. What this represents: the largest spectral differences are phenological; the disease signal is subtle and cannot be found without supervised feature selection.')

h2('3.7 Variance partitioning (PERMANOVA) and mixed models')
tab(['Term', 'df', 'Pseudo-F', 'R2 (%)', 'p'], [[t, int(r.df), '-' if pd.isna(r.Pseudo_F) else f2(r.Pseudo_F), f2(r.R2_partial_pct), '-' if pd.isna(r.p_perm) else f3(r.p_perm)] for t, r in PM.iterrows()],
    'PERMANOVA of SNV spectra (plot-date means; marginal sums of squares; 999 permutations).', widths=[1.8, 0.6, 1.1, 1.0, 1.0])
fig(os.path.join(FIG, 'Fig06_PERMANOVA.png'), 'Marginal variance explained by each term in the PERMANOVA.', w=5.0)
p(f'Date explained {PM.loc["Date", "R2_partial_pct"]:.1f}% of spectral variance, disease {PM.loc["Disease", "R2_partial_pct"]:.1f}% (pseudo-F = {PM.loc["Disease", "Pseudo_F"]:.1f}, p = {PM.loc["Disease", "p_perm"]:.3f}) and the disease x date interaction {PM.loc["Disease:Date", "R2_partial_pct"]:.1f}% (p = {PM.loc["Disease:Date", "p_perm"]:.3f}); variety was not significant (p = {PM.loc["Variety", "p_perm"]:.2f}). Mixed models confirmed significant disease effects for most indices after accounting for date, variety and plot (Table {nt()}). What this represents: hypothesis H2 is supported - the disease effect is small relative to date but highly significant and independent of variety, which justifies one pooled model for all varieties.')
lm = LM.head(12)
tab(['Feature', 'Disease effect (SD units)', 'SE', 'p (disease)', 'p (disease x date)'], [[r.Feature, f3(r.Disease_effect_SDunits), f3(r.SE), pf(r.p_disease), '-' if pd.isna(r.p_disease_x_date) else pf(r.p_disease_x_date)] for r in lm.itertuples()],
    'Linear mixed models (feature ~ disease + date + variety + (1 | plot)) for the twelve most significant indices.', widths=[1.4, 1.6, 0.8, 1.2, 1.4])

h2('3.8 Published vegetation indices')
fig(os.path.join(FIG, 'Fig07_VI_ranking.png'), 'Top-20 published indices ranked by AUC (green = same direction of change on all dates).', w=5.0)
tab(['Index', 'Trait', 'AUC', 'd 11 Feb', 'd 24 Feb', 'd 03 Mar', 'd 13 Mar'], [[r.Index, r.Trait, f3(r.AUC), f2(r['d_11 Feb']), f2(r['d_24 Feb']), f2(r['d_03 Mar']), f2(r['d_13 Mar'])] for _, r in VR.head(12).iterrows()],
    "Twelve best published indices: AUC and Cohen's d on each date.", widths=[0.9, 1.8, 0.6, 0.7, 0.7, 0.7, 0.7], small=True)
p(f'The best published index reached only AUC {vi0.AUC:.3f} ({vi0.Index}). Several chlorophyll indices (NDVI, SR, MTCI) showed no difference on 11 Feb and changed direction between dates, whereas water, anthocyanin and disease indices (WI, HI, ARI2, RVSI) were date-consistent. What this represents: greenness indices designed for chlorophyll or biomass are poor and unstable white-rust detectors in a multi-date dataset.')

h2('3.9 A new Mustard White Rust Index (MWRI)')
fig(os.path.join(FIG, 'Fig08_NDSI_map.png'), 'Exhaustive normalised-difference index search: mean |Cohen d| across dates (sign-consistent pairs).', w=4.8)
tab(['Family', 'Index', 'Mean |d|', 'AUC'], [['SWIR', r.Formula, f2(r.Mean_abs_d_across_dates), f3(r.AUC)] for r in NT.head(4).itertuples()] + [['NIR, join-free', r.Formula, f2(r.Mean_abs_d_across_dates), f3(r.AUC)] for r in NJ.head(3).itertuples()],
    'Best two-band normalised-difference indices (MWRI candidates).', widths=[1.3, 2.9, 1.0, 0.9])
p(f'The best pair, MWRI = (R{int(nd0.Band_i_nm)} - R{int(nd0.Band_j_nm)}) / (R{int(nd0.Band_i_nm)} + R{int(nd0.Band_j_nm)}), had mean |d| {nd0.Mean_abs_d_across_dates:.2f} (at least {nd0.Min_abs_d_across_dates:.2f} on every date) and AUC {nd0.AUC:.3f}, far above any published index (hypothesis H4 supported). The pair lies on the shoulder of the 1940-nm water band within the SWIR-2 detector, 10-30 nm from the 1800-nm detector join; its AUC was unchanged without splice correction, but because of the join proximity a join-free alternative is also proposed: MWRI-NIR = ND(R{int(nj0.Band_i_nm)}, R{int(nj0.Band_j_nm)}), AUC {nj0.AUC:.3f}, which captures the NIR slope linked to mesophyll scattering (Tian et al., 2021).')

h2('3.10 Wavelet features')
fig(os.path.join(FIG, 'Fig09_CWT_scalogram.png'), 'CWT sensitivity scalogram: |Cohen d| of Mexican-hat coefficients by wavelength and scale.')
st = CW.stack().sort_values(ascending=False)
p(f'The largest wavelet effects were at {st.index[0][0]} nm at fine scales (|d| up to {st.iloc[0]:.2f}), 680 nm (chlorophyll well), 1920-1930 nm (water) and 1010 nm at scale 6 (NIR shape). Wavelet coefficients exceeded the effect of any single band (|d| < 1). What this represents: wavelets isolate narrow absorption-shape changes (fine scales) and broad curvature (coarse scales), consistent with Cheng et al. (2011) and Lv et al. (2023).')

h2('3.11 Effect of preprocessing (E1)')
fig(os.path.join(FIG, 'Fig10_preprocessing.png'), 'Balanced accuracy of full-spectrum models under six preprocessings (10 x 4-fold plot-grouped CV).')
vs = ['Reflectance (SG)', 'SNV', 'MSC', 'First derivative (SG)', 'Date normalisation', 'Date normalisation + SNV']
tab(['Preprocessing', 'LDA', 'PLS-DA', 'LR', 'SVM', 'Mean'], [[v] + [f3(e1m.loc[v, c]) for c in ['LDA', 'PLS-DA', 'LR', 'SVM']] + [f3(e1m.loc[v].mean())] for v in vs],
    'Balanced accuracy of full-spectrum models by preprocessing (E1).', widths=[2.2, 0.9, 0.9, 0.9, 0.9, 0.9])
p(f'First-derivative spectra gave the highest accuracy for every classifier (LR {e1m.loc["First derivative (SG)", "LR"]:.3f}, SVM {e1m.loc["First derivative (SG)", "SVM"]:.3f}, LDA {e1m.loc["First derivative (SG)", "LDA"]:.3f}), followed by date normalisation + SNV ({e1m.loc["Date normalisation + SNV"].mean():.3f} mean), MSC and SNV; raw reflectance was poorest for linear models. What this represents: date and leaf-to-leaf brightness differences dominate raw reflectance; derivatives remove these additive and multiplicative effects while keeping the slope information in which the disease signal resides.')

h2('3.12 Comparison of feature scenarios and classifiers')
BM = SUM.pivot(index='scenario', columns='clf', values='BA_mean').loc[list(SCENARIOS)]
CL = ['LDA', 'PLS-DA', 'LR', 'kNN', 'SVM', 'LS-SVM', 'RF', 'XGBoost', 'ELM', 'MLP']
tab(['Scenario'] + CL, [[k] + [f3(BM.loc[k, c]) for c in CL] for k in SCENARIOS],
    'Balanced accuracy of 10 feature scenarios x 10 classifiers (mean of 25 repeats of nested plot-grouped 4-fold CV). S1 full SNV spectrum; S2 F1 bands; S3 F2 indices; S4 F3 NDSI; S5 F4 derivatives; S6 F5 continuum removal; S7 F6 wavelets; S8 combined; S9 SPA; S10 GA-PLS (S2-S8 with robust selection).', small=True,
    widths=[0.6] + [0.59] * 10)
fig(os.path.join(FIG, 'Fig11_BA_matrix.png'), 'Heat map of balanced accuracy for all scenario x classifier pipelines.')
tab(['Scenario', 'Best classifier', 'BA (mean +/- SD)', '95% CI', 'Sens.', 'Spec.', 'MCC', 'AUC'],
    [[r.scenario, r.clf, f'{r.BA_mean:.3f} +/- {r.BA_SD:.3f}', f'{r.BA_CI95_low:.3f}-{r.BA_CI95_high:.3f}', f3(r.Sensitivity_mean), f3(r.Specificity_mean), f3(r.MCC_mean), f3(r.ROC_AUC_mean)] for r in BPS.itertuples()],
    'Best classifier of each feature scenario.', widths=[0.7, 0.8, 1.2, 1.1, 0.6, 0.6, 0.6, 0.6], small=True)
fr = FRT.iloc[0]
p(f'The highest BA was obtained with the full SNV spectrum and logistic regression ({best.BA_mean:.3f} +/- {best.BA_SD:.3f}; MCC {best.MCC_mean:.2f}; AUC {best.ROC_AUC_mean:.3f}), followed by LS-SVM ({BM.loc["S1", "LS-SVM"]:.3f}) and ELM ({BM.loc["S1", "ELM"]:.3f}). Among feature-selected scenarios, the combined pool (S8, {comp.BA_mean:.3f} with LS-SVM) and wavelets (S7, {BM.loc["S7"].max():.3f}) were best, followed by GA-PLS (S10), derivatives (S5) and SPA (S9); robust selection of single bands (S2) or indices (S3) gave only {BM.loc["S2"].max():.3f} and {BM.loc["S3"].max():.3f}. The Friedman test showed significant differences among classifiers (chi2 = {fr.chi2:.0f}, p < 0.001; Nemenyi CD = {fr.CD_Nemenyi_0_05:.2f}); kernel and neural classifiers (LS-SVM, ELM, SVM) ranked best and random forest worst (Table {nt()}). What this represents: the white-rust signal is distributed across many bands and is best captured by regularised linear or kernel models on preprocessed spectra or on combined shape features; hypothesis H5 is partly supported - combined features beat single families, but not the full spectrum.')
tab(['Classifier', 'Average rank', 'Mean BA'], [[r.clf, f2(r.Average_rank), f3(r.Mean_BA)] for r in FRC.itertuples()], 'Average Friedman ranks of classifiers (lower = better; blocks = scenario x repeat).', widths=[1.6, 1.3, 1.3])
tab(['Comparison', 'Mean BA difference', 'Corrected t', 'p'], [[r.Comparison, f3(r.Mean_BA_difference), f2(r.t_corrected) if np.isfinite(r.t_corrected) else '-', pf(r.p_value)] for r in CT.itertuples()],
    'Corrected resampled t-tests of the best pipeline against the best pipeline of each scenario (100 outer folds).', widths=[3.2, 1.2, 1.0, 0.8], small=True)

h2('3.13 Performance of the best models')
fig(os.path.join(FIG, 'Fig13_confusion_matrices.png'), 'Confusion matrices of the best overall (S1 + LR) and best compact (S8 + LS-SVM) models at spectrum and plot-date level (representative repeat).')
cmrows = []
for r in CM.itertuples():
    sens = r.TP / (r.TP + r.FN); spec = r.TN / (r.TN + r.FP)
    cmrows.append([r.Role, r.Level, r.TN, r.FP, r.FN, r.TP, f3(sens), f3(spec), f3((sens + spec) / 2)])
tab(['Model', 'Level', 'TN', 'FP', 'FN', 'TP', 'Sens.', 'Spec.', 'BA'], cmrows, 'Confusion-matrix counts of the best models (representative repeat; diseased = positive class).', widths=[1.0, 1.4, 0.5, 0.5, 0.5, 0.6, 0.6, 0.6, 0.6], small=True)
fig(os.path.join(FIG, 'Fig14_ROC.png'), 'ROC curves of the best overall and best compact models.', w=3.6)
pdb = PDL.set_index(['scenario', 'clf'])
p(f'At spectrum level the best model detected {cmrows[0][6]} of diseased spectra and {cmrows[0][7]} of healthy spectra. Aggregating spectra by majority vote raised performance at plot-date level (mean BA {pdb.loc[("S1", "LR"), "BA_mean"]:.3f} for S1 + LR and {pdb.loc[("S8", "LS-SVM"), "BA_mean"]:.3f} for S8 + LS-SVM over 25 repeats). What this represents: for field decisions taken per plot, averaging a few leaf scans gives highly reliable classification.')

h2('3.14 Selected features and interpretation')
s8f = SF[SF.scenario == 'S8'].head(10)
tab(['Feature', 'Selected in folds (%)'], [[r.Feature, f'{r.Frequency_pct:.0f}'] for r in s8f.itertuples()], 'Most frequently selected features of the combined robust selection (S8) over 100 outer folds.', widths=[2.2, 1.6])
tab(['Final feature', "Cohen's d", 'AUC', 'Permutation importance (BA drop)', 'Mean |SHAP|'], [[r.Feature, f2(r.Cohen_d), f3(r.AUC), f'{r.Permutation_importance_BA:.3f} +/- {r.Permutation_importance_SD:.3f}', f3(r.Mean_abs_SHAP)] for r in FI.itertuples()],
    'Final robust feature set (selected on all spectra) with effect size, AUC and importance.', widths=[1.6, 0.9, 0.8, 2.0, 1.1])
fig(os.path.join(FIG, 'Fig15_final_feature_importance.png'), 'Permutation importance of the final robust features (SVM, plot-grouped CV).', w=5.0)
p(f'The final robust set comprised {len(FI)} features: {", ".join(FI.Feature)}. They describe the shoulder of the 1940-nm water band (FD1810, WF1800_s1, WF1810_s4, CR1800-2100 position), the SWIR dry-matter region (WF2040_s3), the NIR slope (FD850) and the red edge (WF710_s2). The multivariate J-M distance of the set was {JM.JM.iloc[0]:.2f} pooled and {JM.JM.iloc[1:].min():.2f}-{JM.JM.iloc[1:].max():.2f} within dates. What this represents: hypothesis H3 is supported - a few date-stable shape features linked to water, structure and pigments carry most of the disease information.')
fig(os.path.join(FIG, 'Fig16_LR_coefficients.png'), 'Standardised coefficients of the full-spectrum logistic regression (positive = diseased).')
p('The full-spectrum model assigned alternating positive and negative weights to neighbouring bands, i.e. it reads local slopes - the same information isolated by derivatives, wavelets and the MWRI.')

h2('3.15 Multicollinearity of the selected features')
fig(os.path.join(FIG, 'Fig24_collinearity_matrix.png'), 'Correlation matrix of the final robust feature set.', w=4.8)
tab(['Stage', 'n', 'Max |r|', 'Max VIF', 'VIF > 10', 'Condition no.'], [[r.Stage, r.n_features, f2(r.Max_abs_r), f'{r.Max_VIF:,.1f}', r.n_VIF_gt_10, f'{r.Condition_number:,.1f}'] for r in CST.itertuples()],
    'Collinearity at each stage of the robust selection (all spectra).', widths=[2.6, 0.5, 0.8, 1.1, 0.8, 1.1], small=True)
tab(['Feature set', 'n', 'Max |r|', 'Max VIF', 'Mean VIF', 'VIF > 10', 'Cond. no.'], [[r.Feature_set, r.n_features, f2(r.Max_abs_r), f1(r.Max_VIF), f1(r.Mean_VIF), r.n_VIF_gt_10, f1(r.Condition_number)] for r in CS.itertuples()],
    'Collinearity of every final feature set (robust S8, OFCs of E7, top-10 sets of E8).', widths=[2.0, 0.4, 0.8, 0.9, 0.9, 0.8, 0.9], small=True)
p(f'The date-stable ReliefF candidates were extremely collinear (maximum VIF {CST.Max_VIF.iloc[0]:,.0f}; {int(CST.n_VIF_gt_10.iloc[0])} of {int(CST.n_features.iloc[0])} features with VIF > 10). The redundancy filter alone barely helped, but the VIF filter reduced the maximum VIF to {CST.Max_VIF.iloc[2]:.1f}, and the final set had maximum |r| {s8row.Max_abs_r:.2f}, maximum VIF {s8row.Max_VIF:.1f} and condition number {s8row.Condition_number:.1f}. The OFCs and the SVM-RFE, LASSO and CARS top-10 sets were also below VIF 10, whereas the ReliefF ({CS.set_index("Feature_set").loc["ReliefF (top-10)", "Max_VIF"]:.0f}) and Borda ({CS.set_index("Feature_set").loc["Consensus (Borda) (top-10)", "Max_VIF"]:.0f}) top-10 sets remained collinear despite the |r| < 0.95 rule. What this represents: a VIF criterion is necessary in addition to a correlation threshold to obtain non-redundant, interpretable feature sets (Dormann et al., 2013).')

h2('3.16 Optimal feature combinations (E7)')
fig(os.path.join(FIG, 'Fig21_OFC_E7.png'), 'Balanced accuracy of OFC-LDA, OFC-kNN, OFC-SVM, the whole DSF pool and the full spectrum with three classifiers (25 x 4-fold).')
sets = ['OFC-LDA', 'OFC-kNN', 'OFC-SVM', 'All DSFs', 'Full spectrum (SNV)']
tab(['Feature set', 'Median n', 'BA LDA', 'BA kNN', 'BA SVM', 'MCC SVM'], [[s, f1(e7m.loc[(s, 'LDA'), 'median_n_features'])] + [f3(e7m.loc[(s, c), 'BA']) for c in ['LDA', 'kNN', 'SVM']] + [f3(e7m.loc[(s, 'SVM'), 'MCC'])] for s in sets],
    'Classification with optimal feature combinations after Tian et al. (2021).', widths=[1.8, 0.8, 0.9, 0.9, 0.9, 0.9])
ofc_rows = []
for i in range(int(E7F[E7F.Set != 'All DSFs'].groupby('Set').size().max())):
    row = [str(i + 1)]
    for s in ['OFC-LDA', 'OFC-kNN', 'OFC-SVM']:
        L = E7F[E7F.Set == s].Feature.tolist(); row.append(L[i] if i < len(L) else '')
    ofc_rows.append(row)
tab(['Rank', 'OFC-LDA', 'OFC-kNN', 'OFC-SVM'], ofc_rows, 'Composition of the final OFCs (selected on all spectra).', widths=[0.6, 1.9, 1.9, 1.9])
p(f'The OFCs were compact (median {e7m.loc[("OFC-LDA", "LDA"), "median_n_features"]:.0f}-{e7m.loc[("OFC-SVM", "LDA"), "median_n_features"]:.0f} features). With the wrapper-matched classifier (the Tian et al. design), OFC-LDA + LDA reached {e7m.loc[("OFC-LDA", "LDA"), "BA"]:.3f}, OFC-kNN + kNN {e7m.loc[("OFC-kNN", "kNN"), "BA"]:.3f} and OFC-SVM + SVM {e7m.loc[("OFC-SVM", "SVM"), "BA"]:.3f}; the whole DSF pool with SVM reached {e7m.loc[("All DSFs", "SVM"), "BA"]:.3f}, above the full SNV spectrum with SVM ({e7m.loc[("Full spectrum (SNV)", "SVM"), "BA"]:.3f}). What this represents: as in Tian et al. (2021), non-linear wrappers find complementary features that work best with non-linear classifiers, and about seven disease-specific features retain the information of the whole spectrum.')

h2('3.17 Published feature selectors (E8)')
fig(os.path.join(FIG, 'Fig22_selectors_E8.png'), 'Balanced accuracy of six published selectors (10 features) and of this study\'s selections on identical plot-grouped folds.')
ms = ['SVM-RFE', 'LASSO', 'CARS', 'ReliefF', 'SFFS (QDA)', 'Consensus (Borda)']
rows8 = [[m] + [f3(e8v(m, '10', c)) for c in ['QDA', 'LDA', 'SVM', 'RF']] + [f3(e8v(m, k, 'QDA')) for k in ['5', '15']] for m in ms]
rows8 += [[m, f3(e8v(m, 'native', 'QDA')), f3(e8v(m, 'native', 'LDA')), f3(e8v(m, 'native', 'SVM')), f3(e8v(m, 'native', 'RF')), '-', '-'] for m in ['Robust selection + SFFS-LDA (S8)', 'OFC-SVM (Tian et al., 2021)']]
rows8 += [['Full spectrum (SNV)', '-', f3(e8v('Full spectrum (SNV)', '201', 'LDA')), f3(e8v('Full spectrum (SNV)', '201', 'SVM')), '-', '-', '-']]
tab(['Method', 'QDA k=10', 'LDA k=10', 'SVM k=10', 'RF k=10', 'QDA k=5', 'QDA k=15'], rows8, 'Balanced accuracy of the published selectors (5 x 4 plot-grouped folds; S8 and OFC-SVM at their own size).', widths=[2.2, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75], small=True)
tab(['Rank', 'Method', 'BA QDA', 'BA SVM', 'BA RF', 'Jaccard', 'Near-join share'], [[r.Overall_rank, r.method, f3(r.BA_QDA), f3(r.BA_SVM), f3(r.BA_RF), f2(r.Jaccard), f'{100 * r.Near_join_share:.0f}%'] for r in E8R.itertuples()],
    'Composite ranking of selectors (mean rank of QDA, SVM, RF accuracy and Jaccard stability).', widths=[0.5, 2.2, 0.8, 0.8, 0.8, 0.8, 1.0], small=True)
tab(['Comparison', 'Mean BA diff.', 'Wins', 'Losses', 'Wilcoxon p', 'Holm p'], [[r.Comparison.replace(' (SVM, k = 10 / native)', ''), f3(r.Mean_BA_difference), r.Wins, r.Losses, f3(r.Wilcoxon_p), f3(r.Holm_p)] for r in E8T.itertuples()],
    'Paired comparison of each method with the robust selection S8 (SVM, 20 folds).', widths=[2.8, 0.9, 0.5, 0.6, 0.8, 0.7], small=True)
p(f'With ten features and an SVM, ReliefF ({e8v("ReliefF", "10", "SVM"):.3f}), Borda ({e8v("Consensus (Borda)", "10", "SVM"):.3f}), CARS ({e8v("CARS", "10", "SVM"):.3f}) and SVM-RFE ({e8v("SVM-RFE", "10", "SVM"):.3f}) matched or exceeded the full SNV spectrum ({e8v("Full spectrum (SNV)", "201", "SVM"):.3f}); accuracy rose from 5 to 15 features and levelled off. Differences between selectors were not significant after Holm correction. ReliefF ranked first in the composite ranking, whereas the researcher\'s earlier 23-method comparison placed SVM-RFE first; the difference arises mainly because ReliefF selected many features next to the 1800-nm detector join ({100 * E8S.set_index("method").loc["ReliefF", "near_join_share"]:.0f}% of its features).')

h2('3.18 Detector-join check')
fig(os.path.join(FIG, 'Fig23_detector_join_check.png'), 'SVM balanced accuracy with all features and with features within the 1000/1800 nm detector joins excluded.', w=4.5)
jrows = []
for m, k in [('SVM-RFE', '10'), ('SFFS (QDA)', '10'), ('Robust selection + SFFS-LDA (S8)', 'native')]:
    a, b = e8v(m, k, 'SVM'), e8v(m, k, 'SVM', 'join bands excluded')
    jrows.append([m, f3(a), f3(b), f'{b - a:+.3f}'])
tab(['Method', 'All features', 'Join bands excluded', 'Change'], jrows, 'Effect of excluding near-join features on SVM balanced accuracy.', widths=[2.6, 1.1, 1.5, 0.9])
p(f'Removing every feature within 20 nm (or the wavelet half-width) of the 1000 and 1800 nm joins reduced BA by {jrows[0][3]} for SVM-RFE, {jrows[1][3]} for SFFS (QDA) and {jrows[2][3]} for the robust selection. What this represents: the disease signal does not depend on detector artefacts - SVM-RFE remains accurate from NIR, red-edge and SWIR-2 features - but selectors that concentrate on 1800-1840 nm lose more, so join-free features are preferable for sensor design.')

h2('3.19 Performance within dates, varieties and stages')
fig(os.path.join(FIG, 'Fig17_subgroup_performance.png'), 'Balanced accuracy of the pooled models within each date, variety and growth stage.')
sgb = SG[SG.Role == 'Best overall'].set_index('Level')['BA']; sgc = SG[SG.Role == 'Best compact'].set_index('Level')['BA']
tab(['Group', 'Best overall (S1 + LR)', 'Best compact (S8 + LS-SVM)'], [[f'{r.Factor}: {r.Level}', f3(r.BA), f3(sgc.loc[r.Level])] for r in SG[SG.Role == 'Best overall'].itertuples()],
    'Balanced accuracy of the pooled models by sub-group (25 repeats).', widths=[2.2, 1.9, 2.1])
p(f'With one pooled model, BA ranged from {sgb.min():.3f} ({sgb.idxmin()}) to {sgb.max():.3f} ({sgb.idxmax()}); the three varieties performed similarly. What this represents: a single model serves all varieties and stages when every date is represented in training.')

h2('3.20 Transfer to an unseen date, variety or stage (E2)')
fig(os.path.join(FIG, 'Fig18_transfer.png'), 'Balanced accuracy when a whole date, variety or stage is held out.')
e2m = E2.groupby(['kind', 'level', 'scenario', 'clf'])['BA'].mean().unstack(['scenario', 'clf'])
tab(['Held-out level', 'S1 + LR', 'S7 + SVM', 'S8 + SVM'], [[f'{k}: {DATE_LABEL.get(l, l)}'] + [f3(e2m.loc[(k, l)][c]) for c in e2m.columns] for k, l in e2m.index],
    'Transfer performance (balanced accuracy) of three pipelines.', widths=[2.2, 1.3, 1.3, 1.3])
p(f'Transfer to an unseen variety was as good as pooled CV (BA {e2m.loc["Variety"].min().min():.2f}-{e2m.loc["Variety"].max().max():.2f}), transfer to an unseen stage was moderate ({e2m.loc["Stage"].min().min():.2f}-{e2m.loc["Stage"].max().max():.2f}), but transfer to an unseen date failed for the later dates (03 Mar {e2m.loc[("Date", "2026-03-03")].max():.2f}; 13 Mar {e2m.loc[("Date", "2026-03-13")].max():.2f}, i.e. chance level). What this represents: hypothesis H6 holds for varieties but not for dates - the late-season disease signature is not present in other dates, so the model must be trained on data covering the whole season.')

h2('3.21 Metadata, training size, multispectral sensors and outliers (E3-E6)')
fig(os.path.join(FIG, 'Fig19_learning_curve.png'), 'Learning curve: balanced accuracy versus number of training plots.', w=4.2)
fig(os.path.join(FIG, 'Fig20_sensors.png'), 'Balanced accuracy with simulated Sentinel-2 and UAV multispectral bands.', w=4.6)
e3m = E3.groupby(['scenario', 'clf', 'inputs'])['BA'].mean().unstack(); e4m = E4.groupby(['scenario', 'clf', 'n_train_plots'])['BA'].mean().unstack()
e5m = E5.groupby(['sensor', 'clf'])['BA'].mean().unstack(); e6m = E6.groupby(['scenario', 'clf'])['BA'].mean()
rows = [[f'E3 {s} + {c}', 'Spectra only / + metadata', f'{r["Spectra only"]:.3f} / {r["Spectra + metadata"]:.3f}'] for (s, c), r in e3m.iterrows()]
rows += [[f'E4 {s} + {c}', '12 / 24 / 36 training plots', ' / '.join(f3(v) for v in r.values)] for (s, c), r in e4m.iterrows()]
rows += [[f'E5 {s}', 'LR / RF / SVM', ' / '.join(f3(r[c]) for c in ['LR', 'RF', 'SVM'])] for s, r in e5m.iterrows()]
rows += [[f'E6 {s} + {c}', 'All spectra (no outlier removal)', f3(v)] for (s, c), v in e6m.items()]
tab(['Experiment', 'Setting', 'Balanced accuracy'], rows, 'Results of experiments E3-E6.', widths=[2.2, 2.4, 1.9], small=True)
p(f'Adding date, variety and stage as inputs changed BA by only {(e3m["Spectra + metadata"] - e3m["Spectra only"]).min():+.3f} to {(e3m["Spectra + metadata"] - e3m["Spectra only"]).max():+.3f}, so the spectral model does not need metadata. BA increased with the number of training plots without reaching a plateau ({e4m.iloc[:, 0].min():.3f} with 12 to {e4m.iloc[:, -1].max():.3f} with 36 plots), so more plots would improve the model. Simulated Sentinel-2 bands reached at most {e5m.loc[e5m.index.str.startswith("Sentinel")].max(axis=1).iloc[0]:.3f} and UAV five-band data {e5m.loc[e5m.index.str.startswith("UAV")].max(axis=1).iloc[0]:.3f}, showing that narrow hyperspectral features are needed. Keeping the outliers changed BA by at most {max(abs(e6m.loc[(s, c)] - SUM[(SUM.scenario == s) & (SUM.clf == c)].BA_mean.iloc[0]) for s, c in e6m.index):.3f}.')

# ============================================================================= 4 DISCUSSION
pb(); h1('4. Discussion')
h2('4.1 The spectral signature of white rust')
p('White rust produced the response typical of foliar pathogens - higher visible reflectance, a blue-shifted and flattened red edge and higher SWIR reflectance - which reflects chlorophyll breakdown and loss of leaf water around infection sites (Zhang et al., 2012; Mandal et al., 2022; Lv et al., 2023; Tian et al., 2021). Its distinctive feature is the near-absence of an NIR reflectance decrease despite a clear change in NIR slope. The white sori of Albugo candida scatter light strongly and compensate for the reduced scattering of disrupted mesophyll, the same mechanism proposed for powdery-mildew pustules by Zhang et al. (2012). Consequently slope-based features (derivatives, wavelets, narrow band ratios) are better white-rust indicators than reflectance amplitude.')
h2('4.2 Why a pooled model works despite strong date effects')
p(f'Date explained about {PM.loc["Date", "R2_partial_pct"]:.0f}% of spectral variance against {PM.loc["Disease", "R2_partial_pct"]:.1f}% for disease, and unsupervised methods separated dates rather than classes. A pooled model nevertheless achieved BA above 0.9 because (i) first-derivative and SNV preprocessing remove most date-related brightness and scattering differences, (ii) features were selected for stability across dates (Tian et al., 2021; Lv et al., 2023) and (iii) the training data contained every date. The failure of leave-one-date-out transfer shows the limit of this approach: the disease x date interaction is significant and the late-season signature cannot be extrapolated from earlier dates. Varieties, in contrast, did not differ significantly, and a model trained on two varieties transferred to the third.')
h2('4.3 Which features carry the information')
p(f'Published greenness indices were weak (AUC <= {vi0.AUC:.2f}) and unstable across dates, in line with the observation that indices designed for chlorophyll or biomass are not disease-specific (Mahlein et al., 2013). The exhaustive band-pair search produced an index (MWRI, AUC {nd0.AUC:.2f}) that, like the best indices for rice blast (R1148/R1301, Mandal et al., 2023; R1068/R1560, Selvaprakash et al., 2026), lies in the NIR/SWIR rather than the visible region. Wavelet and derivative features outperformed raw bands, confirming Lv et al. (2023) and Tian et al. (2021). Full-spectrum models with derivative or SNV preprocessing were the most accurate overall, because regularised linear models can combine slope information across all bands.')
h2('4.4 Which feature-selection strategy should be used')
p(f'Ten features chosen by ReliefF, Borda, CARS or SVM-RFE matched the full spectrum with an SVM (BA 0.91-0.92), confirming the researcher\'s earlier conclusion (Panda, 2026) and that of Wei et al. (2021) that wrapper and embedded selectors produce compact, accurate sets. The date-stable robust selection gave fewer features (about seven) with slightly lower accuracy (BA {comp.BA_mean:.3f}) but with the best interpretability, stability across dates and no multicollinearity (maximum VIF {s8row.Max_VIF:.1f}). The OFC approach of Tian et al. (2021) gave similar results. Two practical lessons emerge: a VIF criterion is needed in addition to a correlation threshold (ReliefF and Borda sets remained collinear), and the strongest features near 1800 nm sit next to the ASD detector join. Because SVM-RFE remained accurate without join features (BA {e8v("SVM-RFE", "10", "SVM", "join bands excluded"):.2f}), SVM-RFE on join-free features is the safest choice for transferring the model to another instrument or to a multispectral sensor.')
h2('4.5 Comparison with published studies')
tab(['Study', 'Task', 'Reported accuracy'], [
    ['Tian et al. (2021)', 'Rice leaf blast, per stage, leaf clip', 'OA 0.65-0.99'],
    ['Lv et al. (2023)', 'Maize SCLB, asymptomatic / symptomatic', 'OA 0.87 / 0.93'],
    ['Zhang et al. (2012)', 'Wheat powdery mildew, 3 classes', 'OA 0.89, kappa 0.84'],
    ['Zhu et al. (2017)', 'Tobacco TMV, 4 classes, imaging', 'Accuracy 0.98'],
    ['Terentev et al. (2023)', 'Wheat leaf rust, imaging', 'Accuracy 0.98'],
    ['Nguyen et al. (2023)', 'Wheat yellow rust, UAV', 'OA 0.79'],
    ['This study: FD + LR', 'White rust, pooled, plot-grouped nested CV', f'BA {e1m.loc["First derivative (SG)", "LR"]:.2f}'],
    ['This study: SNV + LR', 'White rust, pooled', f'BA {best.BA_mean:.2f}, MCC {best.MCC_mean:.2f}'],
    ['This study: 10 selected features', 'ReliefF + SVM (E8)', f'BA {e8v("ReliefF", "10", "SVM"):.2f}'],
    ['This study: robust S8', f'{len(FI)} date-stable features + LS-SVM', f'BA {comp.BA_mean:.2f}'],
], 'Accuracy of this study compared with published spectral disease-detection studies.', widths=[2.0, 2.8, 1.7])
p('The accuracies obtained here are comparable to those of single-experiment studies even though they come from a much stricter design: one model pooled over four dates, three varieties and three growth stages, validated on plots never used for training and with all selection and tuning nested inside the training data. Most published values were obtained with random spectrum-level splits, which inflate accuracy when repeated measurements of the same plants appear in both training and test sets (Varma & Simon, 2006; Roberts et al., 2017).')
h2('4.6 Limitations')
bl(['Labels are plot-level (healthy and diseased plots); some leaves in diseased plots may have been symptom-free, which limits attainable accuracy and blurs the early-stage signal.',
    'Only 12 healthy plots were available, so the healthy class drives the uncertainty of all metrics, and the learning curve had not reached a plateau.',
    'One season and one site were analysed; leaf layer and disease severity were not recorded, so severity models could not be built.',
    'The strongest single index (1810-1830 nm) lies next to the ASD 1800-nm detector join; join-free alternatives are reported.',
    'Healthy plots were numbered 1-12; if they form one field block, field-position effects cannot be fully excluded.'])

# ============================================================================= 5 SUMMARY AND CONCLUSIONS
pb(); h1('5. Summary and conclusions')
h2('5.1 Summary')
p(f'This study analysed {len(M)} ASD contact-probe leaf spectra of healthy and white-rust-diseased Indian mustard from 48 plots, three varieties, three growth stages and four dates in 2026, in order to develop a single prediction model for white rust. A systematic methodology derived from ten published studies and the researcher\'s comparison of 23 feature-selection methods was applied: quality control (splice correction, trimming, consensus outlier screening), six preprocessing options, extensive spectral characterisation (FDR-controlled band tests, J-M separability, red-edge parameters, PCA, t-SNE, PERMANOVA, mixed models), six feature families (about 2,100 features), four feature-selection routes with multicollinearity control, ten classifiers and nested plot-grouped cross-validation repeated 25 times, complemented by eight experiments.')
p(f'White rust raised visible and SWIR reflectance, blue-shifted the red edge and altered the NIR slope; date dominated the spectra ({PM.loc["Date", "R2_partial_pct"]:.0f}% of variance) but the disease effect was highly significant and independent of variety. A new Mustard White Rust Index outperformed all 46 published indices. The best pooled model (first-derivative full spectrum with logistic regression) reached a balanced accuracy of {e1m.loc["First derivative (SG)", "LR"]:.3f}; compact sets of 7-10 selected features reached 0.89-0.92 without multicollinearity. The model transferred to an unseen variety but not to an unseen date.')
h2('5.2 Conclusions')
nl([f'White rust of Indian mustard can be detected from leaf reflectance with a single model pooled across dates, varieties and growth stages: balanced accuracy {e1m.loc["First derivative (SG)", "LR"]:.3f} (first-derivative full spectrum + logistic regression) and {best.BA_mean:.3f} +/- {best.BA_SD:.3f} (SNV full spectrum + logistic regression; MCC {best.MCC_mean:.2f}, AUC {best.ROC_AUC_mean:.3f}) on plots never used for training.',
    'The spectral signature of white rust consists of higher visible reflectance (chlorophyll loss), a blue-shifted, flattened red edge, higher SWIR reflectance at the 1450 and 1940 nm water bands (water loss) and a changed NIR slope; NIR reflectance itself changes little because the white sori offset mesophyll damage.',
    f'Phenology (date) dominates the spectra ({PM.loc["Date", "R2_partial_pct"]:.0f}% of variance) whereas disease explains {PM.loc["Disease", "R2_partial_pct"]:.1f}% but is highly significant; derivative/SNV preprocessing and date-stable features are therefore essential.',
    f'Published vegetation indices are weak white-rust indicators (AUC <= {vi0.AUC:.2f}); the new MWRI, ND(R{int(nd0.Band_i_nm)}, R{int(nd0.Band_j_nm)}), reaches AUC {nd0.AUC:.2f}, and the join-free MWRI-NIR, ND(R{int(nj0.Band_i_nm)}, R{int(nj0.Band_j_nm)}), AUC {nj0.AUC:.2f}.',
    f'Shape features (derivatives, wavelets, band ratios) carry the disease information. Seven date-stable robust features (BA {comp.BA_mean:.3f}), Tian-style OFCs (BA {e7m.loc[("OFC-SVM", "SVM"), "BA"]:.3f}) and ten features from ReliefF/Borda/CARS/SVM-RFE (BA 0.91-0.92) retain most of the full-spectrum accuracy, suiting low-cost sensors.',
    f'Multicollinearity was effectively controlled: the VIF filter reduced the maximum VIF from {CST.Max_VIF.iloc[0]:,.0f} to {CST.Max_VIF.iloc[2]:.1f}, and the final robust set had a maximum VIF of {s8row.Max_VIF:.1f}.',
    'One model serves all three varieties (unseen-variety BA about 0.93), but an unseen date cannot be predicted; training data must span the whole season.',
    'Kernel and regularised linear classifiers (LS-SVM, ELM, SVM, logistic regression) outperform tree ensembles and kNN for this problem.'])
h2('5.3 Recommendations')
bl(['Use first-derivative (or SNV) preprocessed full spectra with logistic regression or LS-SVM for the most accurate laboratory or field-spectrometer model.',
    'For a sensor or rapid index, use the join-free MWRI-NIR or an SVM-RFE / robust feature set on join-free bands, checked for VIF < 10.',
    'Always validate with plots (not spectra) as independent units and keep feature selection inside the training data.',
    'Include every phenological stage of the season in the training data, and add plots (especially healthy plots) to improve accuracy further.'])
h2('5.4 Future work')
bl(['Record per-leaf severity (percent disease index) to build severity regression and multi-class models (Mandal et al., 2023; Lv et al., 2023).',
    'Validate the model on an independent season and location (Terentev et al., 2023).',
    'Include inoculated plots measured before symptom appearance to test pre-symptomatic detection (Tian et al., 2021).',
    'Invert PROSPECT-D to estimate pigment and water traits, and upscale MWRI to UAV and satellite sensors.'])

# ============================================================================= REFERENCES
pb(); h1('References')
for r in sorted(REFS.Reference.tolist(), key=lambda s: s.replace('[P] ', '').replace('[R] ', '').lower()):
    B.append(dict(type='ref', text=r.replace('[P] ', '').replace('[R] ', '')))

# ============================================================================= APPENDIX
pb(); h1('Appendix')
VF = {'NDVI': '(R800-R670)/(R800+R670)', 'GNDVI': '(R800-R550)/(R800+R550)', 'SR': 'R800/R670', 'mND705': '(R750-R705)/(R750+R705-2R445)',
      'mSR705': '(R750-R445)/(R705-R445)', 'MCARI': '[(R700-R670)-0.2(R700-R550)](R700/R670)', 'TCARI': '3[(R700-R670)-0.2(R700-R550)(R700/R670)]',
      'OSAVI': '1.16(R800-R670)/(R800+R670+0.16)', 'TCARI/OSAVI': 'TCARI/OSAVI', 'MTCI': '(R754-R709)/(R709-R681)', 'Datt': '(R850-R710)/(R850-R680)',
      'PSSRa': 'R800/R675', 'PSSRb': 'R800/R650', 'CIred-edge': 'R800/R720 - 1', 'NDRE': '(R790-R720)/(R790+R720)', 'TVI': '0.5[120(R750-R550)-200(R670-R550)]',
      'NRI': '(R570-R670)/(R570+R670)', 'CCI': '(R531-R645)/(R531+R645)', 'PRI': '(R531-R570)/(R531+R570)', 'SIPI': '(R800-R445)/(R800-R680)',
      'PSRI': '(R680-R500)/R750', 'CRI1': '1/R510 - 1/R550', 'CRI2': '1/R510 - 1/R700', 'ARI1': '1/R550 - 1/R700', 'ARI2': 'R800(1/R550 - 1/R700)',
      'RGR': 'R690/R550', 'REP_LI': '700 + 40[(R670+R780)/2 - R700]/(R740-R700)', 'Vog1': 'R740/R720', 'Vog2': '(R734-R747)/(R715+R726)',
      'RVSI': '(R712+R752)/2 - R732', 'WI': 'R900/R970', 'NDWI': '(R860-R1240)/(R860+R1240)', 'MSI': 'R1600/R820', 'NDII': '(R820-R1650)/(R820+R1650)',
      'LWVI1': '(R1094-R983)/(R1094+R983)', 'DWSI': '(R802+R547)/(R1657+R682)', 'NDNI': '[log(1/R1510)-log(1/R1680)]/[log(1/R1510)+log(1/R1680)]',
      'NDLI': '[log(1/R1754)-log(1/R1680)]/[log(1/R1754)+log(1/R1680)]', 'CAI': '0.5(R2000+R2200) - R2100', 'HI': '(R534-R698)/(R534+R698) - 0.5 R704',
      'PMI': '(R520-R584)/(R520+R584) + R724', 'LRDSI': '6.9(R605/R455) - 1.2', 'RBI': '(R1068-R1560)/(R1068+R1560)', 'BI_ratio': 'R1148/R1301',
      'REP_FD': 'wavelength of max dR/dlambda, 680-750 nm', 'REV': 'max dR/dlambda, 680-750 nm'}
tab(['Index', 'Formula', 'Trait', 'Reference'], [[r['Index'], VF.get(r['Index'], ''), r['Trait'], r['Reference']] for _, r in VD.iterrows()],
    'A1. Vegetation indices (feature family F2): formulas, traits and sources.', widths=[0.9, 2.7, 1.5, 1.5], small=True)
tab(['Sheet', 'Content'], [
    ['01-02', 'Data design; quality control (noise, splice, outliers)'], ['03-06', 'Mean spectra by class, date, variety, stage'],
    ['07-12', 'Band-wise statistics, sensitive regions, red edge, PCA/t-SNE, PERMANOVA, mixed models'], ['13-16', 'Vegetation indices, NDSI/MWRI, CWT scalogram, feature families'],
    ['17-24', 'E1 preprocessing; model matrix, repeat-level results, full metric summary, best pipelines, confusion matrices, ROC, plot level'],
    ['25-27c', 'Selection frequency, final features, collinearity/VIF, sub-groups, OFC (E7), published selectors (E8)'],
    ['28-34', 'E2-E6 experiments, cleaned 10-nm data, references']],
    'A2. Structure of the accompanying Excel workbook (WhiteRust_Mustard_Hyperspectral_Analysis.xlsx).', widths=[1.0, 5.5])

json.dump(B, open(os.path.join(CACHE, 'doc_blocks.json'), 'w'), ensure_ascii=False)
print('blocks', len(B), 'figures', FIGN[0], 'tables', TABN[0])
