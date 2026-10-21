"""Data-driven 'What it shows' / 'Finding' texts, summary table and discussion for the slides (cache/narrative.json)."""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcommon import *

D = json.load(open(os.path.join(CACHE, 'ppt_data.json')))
SCN = D['scenarios']; FL = D['family_label']
DL = [DATE_LABEL[d] for d in DATE_ORDER]
f3 = lambda v: f'{v:.3f}'
f2 = lambda v: f'{v:.2f}'
pf = lambda p: '< 0.001' if p < 0.001 else f'= {p:.3f}'
N = {}
W = {
    'qc': 'Noise of each raw plot average (SD of the high-frequency residual). Fewer averaged leaves give noisier averages; the grey bars show the ratio expected from the leaf numbers alone.',
    'spectra': 'Mean raw reflectance of the 12 control and 36 inoculated plots on each date (10-nm bands).',
    'diff': 'Diseased minus healthy reflectance; positive = diseased plots reflect more.',
    'regions': "Heat strips: Hedges' g (red = diseased higher) and AUC of every 10-nm band per date; the table lists contiguous regions significant (FDR q < 0.05) with the same sign on >= 3 of 4 dates.",
    'families': 'AUC of the best date-stable feature of each family and of its median feature (0.5 = chance, 1 = perfect separation of the 48 plots on a date).',
    'topfeat': 'Two best date-stable features of every family with their AUC on each date.',
    'vi': 'The 15 indices with the highest mean AUC whose direction is the same on all four dates.',
    'rededge': 'Class means of key red-edge parameters by date (Welch p) and the best continuum-removal parameters.',
    'index': 'r² of every NDSI/SR pair with disease status, averaged over dates.',
    'cwt': 'Mean AUC of every Mexican-hat wavelet coefficient (scale 2^1-2^8) - small scales capture narrow slope features.',
    'lmm': 'Mixed model per feature with plot as random effect: tests disease after date and variety, using all 192 plot-dates without pseudo-replication.',
    'permanova': 'Share of multivariate spectral variation explained by each factor; disease permuted as whole plots within cells.',
    'design': 'Disease contrast (control vs inoculated) compared with the largest contrast between the three inoculated blocks, which estimates field-position effects.',
    'matrix': 'Balanced accuracy on held-out cells (plots never seen in training on any date), mean of 20 x 4-fold; darker = better.',
    'bestsc': 'Best classifier of each feature scenario with the 95 % CI over repeats.',
    'friedman': 'Average rank of classifiers (blocks = scenario x repeat) and of feature sets (blocks = classifier x repeat); lower = better.',
    'cm': 'Counts of the repeat with the median BA (192 plot-dates); ROC curves averaged over the 20 repeats.',
    'subgroups': 'The pooled model evaluated separately within each date, variety and inoculation timing.',
    'progress': 'Fraction of the 20 repeats in which a plot-date was called diseased, by date and inoculation timing.',
    'e1': 'Same folds, same classifiers: raw vs Savitzky-Golay smoothed plot averages (E1); and with per-date standardisation (E4).',
    'e2': 'Models trained and tested within one date (48 plots, 4 cell-folds x 10).',
    'e3': 'Training without one date (LODO) or one variety (LOVO) and predicting it.',
    'e5': 'The whole CV repeated with labels shuffled between plots of the same cell; grey = null distribution, red = observed.',
    'e6': 'Control vs each inoculated block (true disease contrast) and block vs block (both inoculated: field-position only).',
    'e7': 'Disease-sensitive features (top 5 % ReliefF on >= 3 dates, VIF < 10) reduced by SFFS with LDA, kNN or SVM as wrapper.',
    'e8': 'Six selectors from the researcher\'s filter/wrapper/embedded comparison applied to the combined plot-level pool.',
    'e9': 'Plot means rebuilt from the leaf spectra with all leaves and with only 3 random leaves per plot (equal for both classes).',
    'e10': 'Best leaf-level models of the previous chapter vs the plot-average models of this chapter.',
    'final': 'Final robust feature set fitted on all data: permutation importance, correlation and VIF.',
}
N['what'] = W

# ---------------------------------------------------------------- characterisation
ns = D['noise']
N['qc'] = (f"Diseased-plot averages were {100 * (1 - np.mean([r['Noise_ratio_D_over_H'] for r in ns])):.0f} % less noisy on average (ratio {min(r['Noise_ratio_D_over_H'] for r in ns):.2f}-{max(r['Noise_ratio_D_over_H'] for r in ns):.2f}), "
           f"less than the {100 * (1 - np.mean([r['Expected_ratio_sqrt_n'] for r in ns])):.0f} % expected from leaf numbers. The difference is small but could favour noise-sensitive features (3rd derivative), so E9 rebuilt every plot from 3 leaves. "
           f"PCA T²/Q flagged {D['n_outlier_flags']} of 192 plot-dates; none removed.")
dd = {d: np.array(D['diff'][d]) for d in DL}; wl = np.array(D['spec']['wl'])
vis = (wl >= 500) & (wl <= 700); nir = (wl >= 760) & (wl <= 1300); sw = (wl >= 1400) & (wl <= 2400)
desc = []
for d in DL:
    desc.append(f"{d}: VIS {np.mean(dd[d][vis]):+.3f}, NIR {np.mean(dd[d][nir]):+.3f}, SWIR {np.mean(dd[d][sw]):+.3f}")
N['spectra'] = ('Healthy and diseased plot spectra share the typical leaf shape; their difference is small relative to the date-to-date change (see PERMANOVA). '
                'Mean D - H by region - ' + '; '.join(desc) + '.')
N['diff'] = ('The difference spectra change sign and size between dates, so a single reflectance band cannot separate the plots on every date. '
             'The most consistent differences are in the visible / red-edge region and around the 1400-1950 nm water bands; these regions dominate the derivative and wavelet features.')
rg = [r for r in D['regions'] if r['family'] in ('REF', 'FD1')]
best_rg = sorted(rg, key=lambda r: -r['mean_AUC'])[:3]
N['regions'] = (f"{len([r for r in rg if r['family'] == 'FD1'])} first-derivative and {len([r for r in rg if r['family'] == 'REF'])} reflectance regions were stable on >= 3 dates. Strongest: "
                + '; '.join(f"{r['family']} {r['start_nm']}-{r['end_nm']} nm ({r['direction']}, AUC {r['mean_AUC']:.2f})" for r in best_rg) + '.')
fs = sorted([r for r in D['fam_summary'] if r['branch'] == 'raw'], key=lambda r: -r['best_mean_AUC'])
N['families'] = (f"Best families: {', '.join(FL[r['family']] + ' (' + f2(r['best_mean_AUC']) + ')' for r in fs[:3])}. "
                 f"Reflectance itself is weakest ({f2([r for r in fs if r['family'] == 'REF'][0]['best_mean_AUC'])}; no band significant on all 4 dates); slopes and band shapes are more date-stable than band levels.")
tp = D['top']
N['topfeat'] = ('Columns 6-9: AUC per date (green = higher). Top-ranked features sit at ' + ', '.join(sorted({t['feature'] for t in tp if t['mean_AUC'] > 0.93})[:6]) + ' - mostly the 1900-1950 nm water-absorption shoulder and the NIR plateau slope.')
vi = D['vi_top']
N['vi'] = (f"Best indices: {', '.join(r['feature'] + ' (' + f2(r['mean_AUC']) + ')' for r in vi[:5])}. Anthocyanin / carotenoid and red-edge stress indices lead; "
           f"but their minimum AUC across dates ({f2(min(r['min_AUC'] for r in vi[:5]))}-{f2(max(r['min_AUC'] for r in vi[:5]))}) shows weaker date stability than derivative features.")
cr = D['cr_top']
N['rededge'] = (f"Red-edge parameters separate the plots moderately (best stable AUC {f2([r for r in fs if r['family'] == 'RE'][0]['best_mean_AUC'])}); diseased plots have a lower red-edge slope and amplitude (chlorophyll loss) on most dates. "
                f"The best CR parameter is {cr[0]['feature']} (AUC {f2(cr[0]['mean_AUC'])}), i.e. the shape of the 1721-2304 nm water / dry-matter absorption.")
ix = [r for r in D['idx'] if not r['join_free']]
b = {k: [r for r in ix if r['index'] == k][0] for k in ('NDSI', 'SR', 'DI')}
N['index'] = (f"Best pairs: NDSI({b['NDSI']['band_i']},{b['NDSI']['band_j']}) mean r² {f2(b['NDSI']['mean_r2'])}, SR({b['SR']['band_i']},{b['SR']['band_j']}) {f2(b['SR']['mean_r2'])}, DI({b['DI']['band_i']},{b['DI']['band_j']}) {f2(b['DI']['mean_r2'])}. "
              'The green-red pair is a pigment index; it is weakest on 11 Feb and strongest on 13 Mar, as disease advanced.')
N['cwt'] = 'High mean AUC (> 0.93) concentrates at small scales (2^1-2^3) around 1810-1950 nm and in the NIR shoulder; large scales (broad shape) separate less - disease changes narrow absorption features.'
ln = D['lmm_n']
N['lmm'] = (f"{ln['sig']} of {ln['tested']} features (VIs, CR, red-edge and the top bands/derivatives) had a significant disease effect after date and variety (FDR q < 0.05); "
            f"{ln['inter']} also changed with date (disease x date). Between-plot ICC was moderate, so repeated dates are not independent - supporting plot-grouped validation.")
pm = {(r['Response'][:3], r['Term']): r for r in D['permanova']}
N['permanova'] = (f"Reflectance: date {pm[('SNV', 'Date')]['R2_pct']:.1f} %, disease {pm[('SNV', 'Disease')]['R2_pct']:.1f} % (p {pf(pm[('SNV', 'Disease')]['p_perm'])}), disease x date {pm[('SNV', 'Disease:Date')]['R2_pct']:.1f} %. "
                  f"Scalar features: disease {pm[('All', 'Disease')]['R2_pct']:.1f} %. Disease is a small but highly significant part of the variation; inoculation timing is also significant.")
bl = D['block']
N['design'] = (f"For every family the control-vs-inoculated effect exceeds the largest block-to-block effect among inoculated plots (median ratio {min(r['ratio'] for r in bl):.1f}-{max(r['ratio'] for r in bl):.1f}); "
               'matched-control tests (inoculated vs its own control in the same cell) are significant for most derivative / wavelet features on every date. Field position alone does not explain the disease contrast, but cannot be fully excluded (controls share one block).')

# ---------------------------------------------------------------- classification
S = {(r['scenario'], r['clf']): r for r in D['summary']}
B = D['best']
b0, b1, b2 = B[0], B[1], B[2]
bsc = sorted(D['best_sc'], key=lambda r: -r['BA_mean'])
N['matrix'] = (f"Best overall: {b0['scenario']} {SCN[b0['scenario']]} + {b0['clf']} (BA {f3(b0['BA'])}, MCC {f3(b0['MCC'])}, AUC {f3(b0['AUC'])}). "
               f"Derivative and wavelet scenarios are best for almost every classifier; reflectance, VIs and red-edge parameters are lower. Linear models (LR, LDA, PLS-DA, SVM) match or beat tree ensembles at n = 144 training plot-dates.")
N['bestsc'] = ('Ranking of best pipelines: ' + ', '.join(f"{r['scenario']} {f2(r['BA_mean'])}" for r in bsc[:6]) + f". Compact selected sets: {b1['scenario']} + {b1['clf']} BA {f3(b1['BA'])} with a median of {b1['n_features']:.0f} features.")
fc = D['friedman_c']; fsn = D['friedman_s']; ft = D['friedman']
N['friedman'] = (f"Classifiers differ (Friedman p {pf(ft[0]['p'])}); best average ranks: {', '.join(r['clf'] for r in fc[:3])}. Feature sets differ (p {pf(ft[1]['p'])}); best: {', '.join(r['scenario'] for r in fsn[:3])}. "
                 'Pairwise tests show which scenarios are statistically indistinguishable from the best pipeline (corrected t and Wilcoxon-Holm in 17_Model_Comparison).')
cm = D['cm']
N['cm'] = (f"Best pipeline ({b0['scenario']} + {b0['clf']}): {cm[0]['FP']} of {cm[0]['TN'] + cm[0]['FP']} healthy and {cm[0]['FN']} of {cm[0]['FN'] + cm[0]['TP']} diseased plot-dates misclassified in the median repeat. "
           f"Compact ({b1['scenario']} + {b1['clf']}) and VI model ({b2['clf']}) err more often on the minority healthy class. Mean ROC-AUC {f3(b0['AUC'])}.")
sg = [r for r in D['subgroups'] if r['Role'] == 'Best overall']
sd = {r['Level']: r for r in sg if r['Factor'] == 'Date'}
N['subgroups'] = ('BA by date: ' + ', '.join(f"{d} {f2(sd[d]['BA'])}" for d in DL if d in sd) + '. ' +
                  'By variety: ' + ', '.join(f"{r['Level']} {f2(r['BA'])}" for r in sg if r['Factor'] == 'Variety') + '; by inoculation timing: ' + ', '.join(f"{r['Level']} {f2(r['BA'])}" for r in sg if r['Factor'] == 'Inoculation') + '.')
pt = D['prog_tests']; pdx = D['plot_decision'][0]
sig = [r['Date'] for r in pt if r['p_spearman'] < 0.05]
N['progress'] = (f"Inoculated plots are called diseased on almost every date (lowest on 11 Feb, the earliest stage); controls are almost never called diseased, except some on 13 Mar (pod formation). "
                 f"Combining the 4 dates per plot gives BA {f3(pdx['BA'])}. Within diseased plots, earlier inoculation tends to give higher scores (Spearman rho {min(r['Spearman_inoc_vs_score_diseased'] for r in pt):.2f} to {max(r['Spearman_inoc_vs_score_diseased'] for r in pt):.2f}), "
                 + (f"significant only on {', '.join(sig)}." if sig else 'not significant on any date.'))

if 'E1' in D:
    e1a = pd.DataFrame(D['E1_all']); e1a['gain'] = e1a['smooth'] - e1a['raw']
    gs = e1a.groupby('scenario')['gain'].mean().sort_values()
    N['e1'] = (f"Smoothing helped the noise-sensitive higher derivatives most ({', '.join(f'{k} {v:+.3f}' for k, v in gs.sort_values(ascending=False).head(2).items())} mean BA change over classifiers) "
               f"and changed reflectance / index scenarios little ({', '.join(f'{k} {v:+.3f}' for k, v in gs.head(2).items())}); best raw and smoothed pipelines are within {abs(e1a.raw.max() - e1a.smooth.max()):.3f} BA. ")
    if 'E4' in D:
        N['e1'] += f"Per-date standardisation inside the pooled CV changed BA by {np.mean([r['with'] - r['without'] for r in D['E4']]):+.3f} on average."
if 'E2' in D:
    e2 = pd.DataFrame(D['E2'])
    bd = e2.groupby('date')['BA'].max().reindex(DL)
    N['e2'] = ('Best single-date BA: ' + ', '.join(f"{d} {f2(v)}" for d, v in bd.items()) + '. Separation is already possible on the first date and is highest when symptoms are fully developed; '
               'pooling dates (main CV) gives a model that works on all dates at once.')
if 'E3' in D:
    e3 = pd.DataFrame(D['E3'])
    lo = e3[e3.kind == 'LODO'].groupby(['held_out', 'date_norm'])['BA'].max().unstack()
    lv = e3[e3.kind == 'LOVO'].groupby('held_out')['BA'].max()
    gain = (lo[True] - lo[False])
    N['e3'] = ('LODO best BA (without / with date normalisation): ' + ', '.join(f"{d} {f2(lo.loc[d, False])}/{f2(lo.loc[d, True])}" for d in DL if d in lo.index) +
               f". Without normalisation accuracy on an unseen date can drop sharply (best pipeline on {gain.idxmax()}: {f2(lo.loc[gain.idxmax(), False])}); per-date standardisation of the features restores it ({f2(lo.loc[gain.idxmax(), True])}). "
               'LOVO: ' + ', '.join(f"{v} {f2(x)}" for v, x in lv.items()) + ' - varieties transfer well.')
if 'E5' in D:
    e5 = D['E5']
    N['e5'] = ('Observed BA lies far outside the permutation null in every pipeline (' + ', '.join(f"{r['scenario']}+{r['clf']}: {f3(r['BA_observed'])} vs null {f2(r['BA_null_mean'])}, p {pf(r['p_value'])}" for r in e5) + '). The classifiers learn a real class signal.')
if 'E6' in D:
    e6 = pd.DataFrame(D['E6'])
    cr_ = e6[e6.contrast.str.startswith('C')].groupby('contrast')['BA'].max(); rr_ = e6[~e6.contrast.str.startswith('C')].groupby('contrast')['BA'].max()
    N['e6'] = (f"Control vs each block: BA {f2(cr_.min())}-{f2(cr_.max())}. Block vs block (both inoculated): BA {f2(rr_.min())}-{f2(rr_.max())}. "
               f"The disease contrast is larger by about {f2(cr_.mean() - rr_.mean())} BA, but inoculated blocks are themselves separable: field position and / or different disease development between blocks carries spectral signal, "
               'so part of the healthy-vs-diseased accuracy may reflect block rather than disease.')
if 'E7' in D:
    e7 = pd.DataFrame(D['E7']); bb = e7.loc[e7.BA.idxmax()]
    N['e7'] = (f"Best OFC result: {bb['feature_set']} + {bb['clf']} BA {f3(bb['BA'])} with a median of {bb['features']:.0f} features. "
               f"DSF / OFC sets of only {e7.features.min():.0f}-{e7.features.max():.0f} features reach BA {e7.groupby('feature_set').BA.max().min():.2f}-{bb['BA']:.2f}, i.e. most of the accuracy of the full derivative spectrum ({f3(b0['BA'])}), as Tian et al. (2021) reported for blast.")
if 'E7_final' in D:
    W['e7final'] = 'Selections made inside each training fold vary because the 12 control plots are few; the table on the left is the single set fitted on all data.'
    N['e7final'] = 'The second derivative (curvature) at 1810 nm (D2_1810) enters every set; SR(1820,1830), D1_1940 and WF1820_s1 (water shoulder) and ARI2 (anthocyanin) complete the pool.'
    W['e7sets'] = 'DSFs = top 5 % ReliefF features on >= 3 of 4 dates, |r| < 0.98, VIF < 10; OFC = subset chosen by SFFS with that wrapper. BA = 10 x 4-fold cell-grouped CV.'
    sm = pd.DataFrame(D['E7_summary'])
    N['e7sets'] = 'Best: ' + '; '.join(f"{r.Set} + {r['Best classifier (CV)']} BA {r.BA:.3f}" for _, r in sm.sort_values('BA', ascending=False).iterrows()) + '.'
if 'E8' in D:
    e8 = pd.DataFrame(D['E8']); b8 = e8.loc[e8.BA.idxmax()]
    rk = e8.groupby('method')['BA'].max().sort_values(ascending=False)
    N['e8'] = (f"Best selector: {b8['method']} (k = {b8['k']}) + {b8['clf']}, BA {f3(b8['BA'])}. Order: " + ', '.join(f"{m} {f2(v)}" for m, v in rk.items()) +
               '. All selectors favour small-scale CWT and 2nd / 3rd-derivative features at the red-edge / NIR shoulder (780-850 nm), the 950 and 1230 nm water bands and 2170 nm; SVM-RFE was also the top selector at leaf level (Panda 2026).')
if 'E9' in D:
    e9 = pd.DataFrame(D['E9'])
    p = e9.pivot_table(index='scenario', columns='averaging', values='BA')
    N['e9'] = ('BA all leaves -> 3 leaves: ' + ', '.join(f"{s} {f2(p.loc[s, 'all leaves (re-built)'])}->{f2(p.loc[s, '3 random leaves per plot'])}" for s in p.index) +
               f". Rebuilt all-leaf means equal the workbook values (max |diff| {D['E9_check']:.0e}). " +
               ('Accuracy stays high with equal leaf numbers, so the separation is not an artefact of averaging more leaves in diseased plots; the drop (largest for the noise-sensitive third derivative) reflects noisier 3-leaf means, i.e. averaging more leaves per plot improves detection.' if p['3 random leaves per plot'].max() > 0.85 else
                'Accuracy drops with 3 leaves, part of the separation depends on the number of leaves averaged.'))
if 'E10' in D:
    e10 = D['E10']
    N['e10'] = ('; '.join(f"{r['Approach']}: BA {f3(r['BA'])}" for r in e10) + '. Plot averages reach the accuracy of aggregated leaf models with one spectrum per plot.')
fin = D['final']; jm = D['final_jm'][0]
N['final'] = (f"{len(fin)} features, max VIF {jm['max_VIF']:.1f}, max |r| {jm['max_abs_r']:.2f}, multivariate J-M {jm['JM']:.2f} (of 2). Most important: {fin[0]['Feature']}.")

# ---------------------------------------------------------------- summary table and discussion
N['summary_rows'] = [
    ['Do plot spectra differ?', f"Yes - PERMANOVA disease p {pf(pm[('SNV', 'Disease')]['p_perm'])}; {ln['sig']} of {ln['tested']} features significant in mixed models; date effect much larger."],
    ['Which features?', f"{FL[fs[0]['family']]} and {FL[fs[1]['family']]} (AUC up to {f2(fs[0]['best_mean_AUC'])}); 1810-1950 nm water shoulder and red-edge / NIR slope."],
    ['Best plot-level model', f"{b0['scenario']} {SCN[b0['scenario']]} + {b0['clf']}: BA {f3(b0['BA'])}, MCC {f3(b0['MCC'])}, AUC {f3(b0['AUC'])}."],
    ['Compact model', f"{b1['scenario']} + {b1['clf']}: BA {f3(b1['BA'])} with ~{b1['n_features']:.0f} features."],
    *([['Best compact selection (E8)', f"SVM-RFE, 15 features + LR: BA {f3(pd.DataFrame(D['E8']).query('method == \"SVM-RFE\"').BA.max())} (10 x 4-fold)."]] if 'E8' in D else []),
    ['Best published-index model', f"VIs (S6) + {b2['clf']}: BA {f3(b2['BA'])}."],
]
if 'E3' in D:
    N['summary_rows'].append(['Transfer', f"Unseen date BA {f2(lo[True].min())}-{f2(lo[True].max())} with per-date normalisation ({f2(lo[False].min())}-{f2(lo[False].max())} without); unseen variety {f2(lv.min())}-{f2(lv.max())}."])
if 'E5' in D and 'E9' in D:
    N['summary_rows'].append(['Artefact checks', f"Permutation p {pf(max(r['p_value'] for r in D['E5']))} (null BA 0.50); 3-leaf plot means BA {f2(p['3 random leaves per plot'].max())}; caveat: inoculated blocks separable from each other (BA {f2(rr_.min())}-{f2(rr_.max())})."])

N['disc_mech'] = [
    'Inoculated plots show changes in the visible / red-edge region (pigment loss, anthocyanin and carotenoid indices rise, red-edge slope falls), as reported for blast, rusts and mildew (Zhang 2012; Mandal 2022; Ashourloo 2014).',
    'The largest and most date-stable changes are in the shape of the water-absorption features (1400-1950 nm) and of the NIR plateau: white rust pustules and haustoria disturb mesophyll structure and leaf water.',
    'The disease signal is small against the seasonal (date / growth-stage) change, so features that describe local shape (slopes, curvature, wavelet coefficients) are more robust than absolute reflectance.',
]
N['disc_feat'] = [
    'Derivatives and small-scale CWT coefficients remove the brightness level that varies with date, leaf angle and probe contact and keep the band shape (Tsai & Philpot 1998; Lv 2023; Tian 2021).',
    'Averaging 3-15 leaves suppresses random noise, so even second / third derivatives of raw plot averages are usable; Savitzky-Golay smoothing helps mainly the third derivative (E1).',
    'Exhaustively optimised two-band indices recover a pigment ratio (green / red) but explain less variance than derivative features, consistent with Mandal et al. (2023).',
]
N['compare'] = [
    ['Zhang et al. 2012', 'Derivative and CR features beat VIs for powdery mildew (OA 0.89)', 'Same pattern: derivative / CWT > CR > VIs at plot level'],
    ['Mandal et al. 2022, 2023', 'Red-edge shift and optimised NDSI track blast severity', 'Red-edge slope lower in diseased plots; best NDSI is a green-red pigment pair'],
    ['Tian et al. 2021', 'Date-stable OFCs from SFFS give 65-98.7 % OA', 'OFCs with few features keep most of the accuracy (E7)'],
    ['Lv et al. 2023', 'FD + CWT best; date normalisation helps asymptomatic stages', 'FD / CWT best; per-date standardisation +0.02 BA pooled (E4) and essential for unseen dates (E3)'],
    ['Terentev et al. 2023', 'Cross-experiment validation needed for honest accuracy', 'Unseen-date (LODO) accuracy lower than pooled CV (E3)'],
    ['Zhu 2017; Huang 2020', 'SPA selects few informative bands', 'SPA reflectance bands are weaker than derivative features'],
    ['Panda 2026 (leaf level)', 'Leaf pooled models BA 0.92-0.95', 'Plot averages give comparable or higher BA with one spectrum per plot (E10)'],
]
N['disc_evidence'] = ['Matched-control tests: inoculated plots differ from their own control in the same variety x inoculation cell on every date.',
                      'Control-vs-inoculated effects exceed block-to-block effects (R12, E6).',
                      'Label permutation within cells destroys the accuracy (E5).',
                      'Accuracy holds when every plot mean is rebuilt from 3 leaves (E9) and for unseen varieties (E3).']
N['disc_caveats'] = ['All controls are in one block (plots 1-12): disease and field position cannot be separated completely (Hurlbert 1984); inoculated blocks are also separable from each other (E6).',
                     'Controls averaged fewer leaves; E9 tested this directly.',
                     'Only 12 healthy plots: the minority class drives the uncertainty (wide CIs on specificity).',
                     'No severity score per plot: the model is binary and its probability is not a severity estimate.',
                     'One season and site; transfer to other years and to canopy / UAV sensors is untested.']
N['protocol'] = [['Sample', 'measure >= 9 leaves per plot with the contact probe and average them'], ['Pre-process', 'trim 400-2400 nm; use raw averages (smoothing optional)'],
                 ['Features', 'first / second derivative or CWT (small scales) of the plot average'], ['Model', f"{b0['clf']} on the {SCN[b0['scenario']].split(',')[0].lower()}, or LR on ~15 SVM-RFE-selected derivative / wavelet features"],
                 ['Normalise', 'standardise features within each date (all plots of the date, no labels) before applying the model to a new date'], ['Validate', 'cell- or plot-grouped CV; report BA, MCC; test unseen dates'], ['Decide', 'combine the calls of successive dates per plot for the final plot decision']]
N['conclusions'] = [
    f"Plot-average spectra separate healthy and white-rust diseased mustard plots on every date; disease explains a small but highly significant share of spectral variation (PERMANOVA p {pf(pm[('SNV', 'Disease')]['p_perm'])}).",
    f"Derivative and wavelet features of the raw plot average are the most discriminating and date-stable; the best pipeline ({b0['scenario']} + {b0['clf']}) reached BA {f3(b0['BA'])} on held-out plots.",
    (f"Compact sets work as well: SVM-RFE with 15 features + LR reached BA {pd.DataFrame(D['E8']).query('method == \"SVM-RFE\"').BA.max():.3f} (E8) and optimised two-band indices + {b1['clf']} {f3(b1['BA'])}; the best published vegetation indices reached BA {f3(b2['BA'])}." if 'E8' in D else ''),
    'Design controls (matched controls, block contrasts, permutations, equal leaf numbers) support a genuine disease effect, but the single control block remains a limitation.',
    (f"Standardising the features within each date (Lv et al. 2023) raised the first-derivative LDA model to BA {max(r['with'] for r in D['E4']):.3f} in the pooled CV (E4); " if 'E4' in D else '') + 'for a date not seen in training, per-date standardisation is essential (E3); varieties transfer without it.',
    'Plot averaging gives accuracy comparable to leaf-level models with far fewer spectra to process, and is the natural input for canopy-scale sensors.',
]
N['limitations'] = N['disc_caveats']
N['future'] = ['Randomise controls across blocks and equalise leaves per plot in the next season.', 'Record visual severity per plot to model severity, not only presence.',
               'Validate on an independent season / site and simulate canopy, UAV and satellite bands.', 'Test the derivative / CWT features on canopy spectra and multispectral sensors.']
json.dump(N, open(os.path.join(CACHE, 'narrative.json'), 'w'), indent=1)
print('narrative written', len(N))
