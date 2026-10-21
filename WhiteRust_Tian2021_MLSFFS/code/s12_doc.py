"""Thesis-style Word report: content spec (JSON) rendered by render_docx.js."""
import sys, re, json, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from mlsffs import *
from content import REFS, TIAN_REF_ERRORS, CORRECTIONS, PAPER_VS_STUDY

S = sys.argv[1]; OUT = sys.argv[2]; O = f"{S}/out"; FIG = f"{S}/figs"
T = pickle.load(open(f"{O}/tables.pkl", "rb"))
CK = pickle.load(open(f"{O}/crosschecks.pkl", "rb"))
CODE = T["code"]; POOL = T["pool"]; INV = {v: k for k, v in CODE.items()}
B = []
def h1(t, pb=True): B.append({"type": "h1", "text": t, "pageBreak": pb})
def h2(t): B.append({"type": "h2", "text": t})
def h3(t): B.append({"type": "h3", "text": t})
def p(t): B.append({"type": "p", "text": t})
def note(t): B.append({"type": "note", "text": t})
def eq(t): B.append({"type": "eq", "text": t})
def bullets(items): B.append({"type": "bullets", "items": items})
NUMREF = iter(["num", "num2", "num3", "num4", "num5", "num6", "num7", "num8"])
def numbered(items): B.append({"type": "numbered", "items": items, "ref": next(NUMREF)})
TAB = [0]; FIGN = [0]
LABELS = {}
def table(caption, df, widths=None, note_=None, fmt=None, fs=17, key=None):
    TAB[0] += 1
    if key: LABELS["T:" + key] = TAB[0]
    fmt = fmt or {}
    rows = []
    for r in df.itertuples(index=False):
        row = []
        for c_, v in zip(df.columns, r):
            if c_ in fmt and v is not None and not (isinstance(v, float) and np.isnan(v)):
                row.append(fmt[c_](v))
            elif isinstance(v, (float, np.floating)):
                row.append("" if np.isnan(v) else f"{v:.3f}")
            elif isinstance(v, (bool, np.bool_)):
                row.append("Yes" if v else "No")
            else:
                row.append(str(v))
        rows.append(row)
    B.append({"type": "table", "caption": f"**Table {TAB[0]}.** {caption}", "header": [str(c) for c in df.columns], "rows": rows,
              "widths": widths, "note": note_, "fontSize": fs})
    return TAB[0]
def figure(name, caption, w=16):
    FIGN[0] += 1
    LABELS["F:" + name] = FIGN[0]
    B.append({"type": "figure", "path": f"{FIG}/{name}.png", "caption": f"**Figure {FIGN[0]}.** {caption}", "widthCm": w})
    return FIGN[0]
pc = lambda v: f"{100 * v:.1f}"
NCAND = int(T["feature_counts"].iloc[0, 1:].sum())
fa, ne, op, pm = T["faithful"], T["nested"], T["optimism"], T.get("perm")
sa, sd, vd = T["stageA"], T["stage_detection"], T["variety_detection"]
dssf = T["dssf_final"]
ph = T["physio"]

# ------------------------------------------------------------------ title
B.append({"type": "title", "text": "Spectroscopic detection of white rust (*Albugo candida*) in mustard with integrated machine learning and sequential floating forward selection"})
B.append({"type": "subtitle", "text": "Step-by-step application and critical re-evaluation of the ML-SFFS methodology of Tian et al. (2021, *Remote Sensing of Environment* 257, 112350) on plot-average hyperspectral data"})
B.append({"type": "subtitle", "text": "Thesis chapter – methods, results, interpretation and verified references"})
B.append({"type": "subtitle", "text": "Data: 48 plots × 4 measurement dates (11 Feb – 13 Mar 2026), ASD FieldSpec contact-probe leaf spectra averaged per plot"})
B.append({"type": "pagebreak"})
B.append({"type": "toc"})

# ------------------------------------------------------------------ 1 introduction
h1("1. Introduction")
h2("1.1 Background")
p("White rust, caused by the oomycete *Albugo candida*, is one of the most damaging diseases of rapeseed-mustard; it produces chlorotic lesions and white pustules on leaves and, after systemic infection, malformed inflorescences ('stag heads') (Saharan et al., 2014). Because control depends on timely intervention, a non-destructive method that detects infection early – before symptoms are obvious to the eye – is of considerable practical value.")
p("Reflectance spectroscopy records how a leaf absorbs and scatters light from the visible (VIS, 400–700 nm) through the near-infrared (NIR, 700–1300 nm) to the short-wave infrared (SWIR, 1300–2500 nm). Pathogen attack changes leaf pigments (chlorophyll, carotenoids, anthocyanins), the internal cell structure and the water status, and each of these changes leaves a trace in a different part of the spectrum (Mahlein et al., 2013, 2018). The difficulty is that the early changes are small and spread over thousands of narrow, strongly correlated bands; a large number of candidate spectral features must therefore be reduced to a small, informative and interpretable set.")
h2("1.2 The methodology of Tian et al. (2021)")
p("Tian et al. (2021) proposed an integrated machine-learning and feature-selection methodology (ML-SFFS) to detect rice leaf blast from the asymptomatic to the mild stage. Their workflow has three modules (their Fig. 2): (i) **data preparation** – statistical analysis of leaf biochemistry and spectral processing (spectral indices, continuous wavelet transform); (ii) **feature selection** – assessment of the spectral separability of every reflectance band, spectral index (SI) and wavelet coefficient with a thresholding technique, retention of the top 5 % features per date, intersection across dates, one representative per spectral region, and collinearity reduction with the variance inflation factor (VIF < 10); and (iii) **classification** – sequential floating forward selection (SFFS; Pudil et al., 1994) wrapped around linear discriminant analysis (LDA), k-nearest neighbours (k-NN, k = 3) or a support vector machine (SVM), evaluated by 4-fold cross-validation repeated 100 times. The result is the optimal feature combination (OFC) and its overall accuracy (OA) for each day after inoculation (DAI). They reported OAs above 65 %, 80 % and 95 % for the asymptomatic, early and mild stages, with two to four features per OFC.")
h2("1.3 Objectives")
p("This chapter applies the ML-SFFS methodology, step by step, to the plot-average hyperspectral data of a white-rust experiment in mustard, using the raw plot-average reflectance and the features derived from it (continuum-removal parameters, vegetation indices, first- to third-order derivatives and red-edge parameters). The specific objectives are:")
numbered(["to reproduce every step of Tian et al. (2021) on these data and document each step with its concept, method, results and cross-checks;",
          "to identify the disease-specific spectral features (DSSFs) of white rust and interpret them physiologically;",
          "to determine the optimal feature combinations and classification accuracies for each measurement date and each infection stage (date × inoculation timing);",
          "to correct the procedure where the data or the method required it (class imbalance, instrument artefacts, multi-date consistency, selection bias) and to quantify how much the corrections change the conclusions."])

# ------------------------------------------------------------------ 2 materials
h1("2. Materials")
h2("2.1 Experimental design")
p("The experiment comprised 48 plots: three mustard varieties (V1, V2, V3) inoculated at four timings (D1–D4, inoculation on different days after sowing) in three replications (R1–R3), i.e. 36 inoculated plots, plus 12 uninoculated control plots – one for each variety × inoculation-timing combination – grouped in a separate block (C). The design is fully balanced (Table [[T:design]]). The same 48 plots were measured on four dates, here called T1 (11 Feb 2026), T2 (24 Feb), T3 (3 Mar) and T4 (13 Mar); the crops progressed from the vegetative stage through flowering to pod formation over this period.")
dz = T["design"].copy(); dz.columns = [f"{a} · {b}" for a, b in dz.columns]; dz = dz.reset_index().rename(columns={"Replication": "Block"})
table("Treatment design: number of plots per block, variety (V1–V3) and inoculation timing (D1–D4).", dz, fs=15, key="design")
note("D1–D4 denote inoculation timings (groups of days after sowing); the analysis assumes D1 is the earliest inoculation. The measurement dates are labelled T1–T4 throughout to avoid confusion with D1–D4.")
h2("2.2 Spectral measurements and plot averaging")
qc = T["qc"]
p(f"Leaf reflectance (350–2500 nm, 1-nm interval) was measured with an ASD FieldSpec spectroradiometer and contact probe, which illuminates the leaf with its own lamp, so the water-absorption regions near 1450 and 1940 nm carry leaf-water information rather than atmospheric noise. Between {int(qc['Leaf spectra'].min())} and {int(qc['Leaf spectra'].max())} leaf spectra were recorded per date; the spectra of each plot (3–15 leaves) were averaged to one plot spectrum. Averaging makes the plot the experimental unit, avoids pseudo-replication and reduces random leaf-to-leaf and instrument noise. The plot averages had been verified against the data owner's own averaging formulas (48 of 48 identical) in the source workbooks.")
h2("2.3 Candidate spectral features")
p("Six families of candidate features were derived from the raw (unsmoothed) plot-average reflectance (Table [[T:feat]]): the reflectance bands themselves; the first, second and third derivatives (central finite differences, Δλ = 1 nm; Tsai and Philpot, 1998); continuous wavelet coefficients (added in this study to follow Tian et al., 2021); 87 published vegetation indices (VIs); 48 continuum-removal (CR) parameters of six absorption windows (Clark and Roush, 1984; Kokaly and Clark, 1999); and 23 red-edge parameters (Horler et al., 1983; Gong et al., 2002).")
fc = T["feature_counts"].iloc[[0]].T.reset_index(); fc.columns = ["Feature family", "Number of candidates per date"]; fc = fc.iloc[1:]
table("Candidate features per date after restriction of the spectral range (Section 3.1).", fc, widths=[3, 2], key="feat")

# ------------------------------------------------------------------ 3 methods
h1("3. Methods")
p("The analysis follows the three modules of Tian et al. (2021) as Steps 1–6 (Figure [[F:fig01_workflow]]); Step 7 collects the cross-checks. Where the method had to be corrected, the paper-faithful result is reported beside the corrected one; the corrections are coded C1–C9 and summarised in Table [[T:corr]].")
figure("fig01_workflow", "Workflow of the analysis (analogue of Tian et al., 2021, Fig. 2). Steps 1–5 build the pool of disease-specific spectral features (DSSFs); Step 6 selects the optimal feature combination with ML-SFFS and evaluates it in four ways (A–D).", 13)
corr = sorted(CORRECTIONS, key=lambda x: int(x[0][1:]))
table("Corrections to the procedure of Tian et al. (2021) and their reasons.", pd.DataFrame([(c[0], c[1], c[3], c[4]) for c in corr], columns=["Code", "Issue", "Correction applied", "Reason"]), widths=[0.6, 1.7, 4.2, 3.2], fs=15, key="corr")

h2("3.1 Step 1 – Data preparation and quality control")
h3("Concept")
p("Before any feature is evaluated the data must be shown to be consistent (labels, plots, treatments) and free of instrument artefacts, because a feature-selection procedure will pick up any systematic difference between the classes – including differences that have nothing to do with the disease.")
h3("Procedure")
bullets(["**Consistency.** Class labels, varieties and the treatment file were compared plot by plot across the four workbooks.",
         "**Spectral range (C1).** Bands 350–399 nm and 2401–2500 nm (low signal-to-noise at the detector ends) and the guard zones 990–1010 nm and 1795–1835 nm around the joins of the three ASD detectors were excluded from the band, derivative and wavelet candidates. Exploratory analysis showed first derivatives at 1825–1830 nm separating the classes perfectly on single dates – a step artefact of the SWIR1/SWIR2 detector join, not leaf biology.",
         "**Continuous wavelet transform (CWT).** Following Cheng et al. (2010) and Tian et al. (2021), every plot spectrum was decomposed with the Mexican-hat (second derivative of a Gaussian) mother wavelet at dyadic scales 2^1^–2^8^; scales 3–8 were retained. Computations used PyWavelets (Lee et al., 2019).",
         "**Confounds (C9).** The measurement order and block structure were inspected."])
eq("W(a, λ) = ∫ R(x) · a^−1/2^ ψ((x − λ)/a) dx,   ψ(t) = (2/(√3 π^1/4^)) (1 − t²) e^−t²/2^")
note("R = reflectance, a = scale (2^j^ nm, j = 3…8), λ = wavelength; each W(a, λ) is one candidate wavelet feature (Torrence and Compo, 1998; Cheng et al., 2010).")

h2("3.2 Step 2 – Physiological interpretation")
h3("Concept")
p("Tian et al. (2021) first showed which leaf constituents change during infection, because this explains why particular spectral regions become disease-specific. Leaf biochemistry was not measured in this experiment, so published spectral proxies of the same four constituents were tested instead (C8): chlorophyll – CIrededge (Gitelson et al., 2003), MTCI (Dash and Curran, 2004) and the red-edge inflection point by linear four-point interpolation (Guyot and Baret, 1988); carotenoids – CRI1 (Gitelson et al., 2002); anthocyanins – ARI (Gitelson et al., 2001); xanthophyll-cycle activity – PRI (Gamon et al., 1992); water – WI (Peñuelas et al., 1997) and NDWI (Gao, 1996).")
h3("Procedure")
p("The decision rule of Tian et al. (2021) was applied to each proxy and date: values outside the median ± 3 MAD of each group were treated as outliers (Leys et al., 2013); if both groups were normal (Shapiro–Wilk; Shapiro and Wilk, 1965) and their variances equal (Levene, 1960), an independent Student t-test was used, otherwise the Mann–Whitney U test (Mann and Whitney, 1947). In addition (C7), the 32 p-values were adjusted with the Benjamini–Hochberg false-discovery rate (Benjamini and Hochberg, 1995). The effect size is Hedges' g (positive = higher in diseased plots).")

h2("3.3 Step 3 – Spectral separability by thresholding")
h3("Concept")
p("The separability of a single feature is the accuracy with which one threshold on that feature separates healthy from diseased plots (Mahlein et al., 2013; Tian et al., 2021, Fig. 3). It is a simple, model-free filter that can be computed for tens of thousands of features and displayed as a 'classification scalogram' along the wavelength axis.")
h3("Procedure")
p("For every feature and date the class means M~h~ (healthy) and M~i~ (infected) were computed and the interval between them divided into 100 equal steps; each step t~k~ = M~h~ + k(M~i~ − M~h~)/100 (k = 0…100) was used as a threshold, plots on the M~i~ side being called diseased. Because only 12 of the 48 plots are healthy, the best threshold was chosen by the balanced accuracy (C2):")
eq("BA = (Se + Sp)/2,   Se = TP/(TP + FN),   Sp = TN/(TN + FP),   OA = (TP + TN)/N")
note("A classifier that calls every plot 'diseased' has OA = 36/48 = 75 % but BA = 50 %; BA is therefore the appropriate criterion for imbalanced classes (Brodersen et al., 2010).")

h2("3.4 Step 4 – Extraction of disease-specific spectral features (DSSFs)")
p("The rules of Tian et al. (2021) were applied with an explicit consistency criterion (C3):")
numbered(["For the continuous families (reflectance, D1–D3, CWT) the features in the top 5 % of separability were marked on each date (ties included).",
          "A feature was 'common' if it was marked on at least k* of the four dates, where k* is the largest value (4, then 3, then 2) for which the family still has at least one common feature. Tian et al. intersected only the DAIs at which common features existed; with four dates spanning vegetative to pod-formation stages, the strict four-date intersection left almost nothing.",
          "Common features were grouped into contiguous wavelength regions (for the CWT, 8-connected regions in the scale × wavelength plane) and the feature with the highest mean balanced accuracy was kept as the region's representative.",
          "For the scalar families (VIs, CR and red-edge parameters) the top 10 % of each family on each date were retained and the union taken over the dates – the analogue of Tian et al.'s union of the yearly top-10 spectral indices.",
          "Exactly duplicated features (|r| > 0.9999) were removed."])

h2("3.5 Step 5 – Collinearity reduction (VIF)")
p("The candidate DSSFs were z-scored within each date and stacked over the four dates, and the variance inflation factor of feature j was computed as")
eq("VIF~j~ = 1/(1 − R~j~²)")
p("where R~j~² is the coefficient of determination of feature j regressed on all other features. Tian et al. (2021) retained features with VIF < 10 without stating the iteration rule. Here (C5) the VIFs were recomputed after every removal and, while any VIF was ≥ 10, the least separable of the features with VIF ≥ 10 was removed (relevance-aware rule); the commonly used 'drop the largest VIF' rule is reported for comparison. The threshold of 10 is a rule of thumb whose limits are discussed by O'Brien (2007).")

h2("3.6 Step 6 – ML-SFFS classification")
h3("Classifiers")
bullets(["**LDA** (Fisher, 1936) projects the features on the direction that maximises the ratio of between-class to within-class variance; it assumes normal classes with a common covariance.",
         "**k-NN** (Cover and Hart, 1967) assigns a plot to the majority class of its k = 3 nearest training plots (Euclidean = Minkowski p = 2 distance on z-scored features).",
         "**SVM** (Cortes and Vapnik, 1995; LIBSVM, Chang and Lin, 2011) with a radial basis function kernel K(x, x′) = exp(−γ‖x − x′‖²); C and γ were chosen by grid search, C ∈ {2^−1^, 2^1^, 2^3^, 2^5^, 2^7^}, γ ∈ {2^−5^, 2^−3^, 2^−1^, 2^1^}/p for p features (Hsu et al., 2003)."])
p("All features were z-scored with the mean and standard deviation of the training plots of each fold (C6). The classifiers were implemented with scikit-learn (Pedregosa et al., 2011).")
h3("Sequential floating forward selection")
p("SFFS (Pudil et al., 1994) is a wrapper method: the classifier's cross-validated accuracy is the criterion J of a feature subset. Starting from the empty set, it repeats:")
numbered(["**Inclusion:** add the feature that gives the largest J;",
          "**Conditional exclusion:** find the least significant feature of the current subset (the one whose removal gives the largest J); remove it if the reduced subset is better than the best subset of that size found so far, and repeat this step; otherwise return to inclusion.",
          "Stop when the subset reaches the maximum size (8 features) or J = 100 %; the OFC is the subset with the highest J (ties → fewer features)."])
p("The floating backward steps correct poor early decisions of plain forward selection, which is why SFFS approximates the exhaustive search closely at a fraction of its cost (Pudil et al., 1994; Saeys et al., 2007).")
h3("Evaluation")
bullets(["**A – paper-faithful (Tian et al., 2021).** For every date and classifier: stratified 4-fold CV partition, SFFS with J = OA, repeated 100 times with new partitions; reported OA = mean of the 100 optimal accuracies; OFC = the most frequent optimal combination. SVM-all = SVM with all DSSFs.",
         "**B – corrected nested CV (C4).** 10 repetitions × stratified 4-fold outer CV over plots (the same held-out plots on every date). Inside each outer training set the complete pipeline – separability, DSSF pool, VIF, SFFS (J = balanced accuracy, inner 4-fold CV × 3) and SVM grid search – was re-run, and the selected model classified the held-out plots. LDA used equal priors and the SVM class-balanced weights. This removes the selection bias of A (Ambroise and McLachlan, 2002; Varma and Simon, 2006; Cawley and Talbot, 2010).",
         "**C – permutation null.** The plot labels were shuffled (the same shuffle on all dates) and procedure A was re-run in full: 20 permutations × 5 repetitions for LDA and k-NN, 4 × 2 for the SVM (Ojala and Garriga, 2010).",
         "**D – infection stages.** (i) Paper-faithful ML-SFFS of the 12 controls against the 9 plots of each inoculation timing on each date (16 stages; fixed DSSF pool; 4-fold CV × 100); (ii) the unbiased per-group detection rate and per-variety accuracy from the nested-CV predictions of B."])
eq("κ = (OA − p~e~)/(1 − p~e~),   p~e~ = [(TP + FP)(TP + FN) + (FN + TN)(FP + TN)]/N²")
note("Cohen's kappa (Cohen, 1960) corrects OA for chance agreement; Se, Sp and BA as in Section 3.3.")
h2("3.7 Step 7 – Cross-checks and software")
p("Every step was verified by an independent route (Table [[T:ck]]): Excel formulas recompute class means, threshold accuracies and summary accuracies from the stored data; derivatives and wavelet coefficients were recomputed directly; the VIF was recomputed with statsmodels; SFFS was compared with an exhaustive search; the accuracy functions with scikit-learn; and the nested folds were checked for leakage. All references were checked against publisher or repository records. The analysis used Python 3 with NumPy, pandas, SciPy, statsmodels, scikit-learn 1.9 and PyWavelets 1.10.")

# ------------------------------------------------------------------ 4 results
h1("4. Results")
h2("4.1 Data quality and design")
cks = CK.set_index("Check")
p("Class labels and varieties were identical on all four dates and agreed with the treatment file; the design was balanced (Table [[T:design]]). Two properties of the data must be borne in mind when reading the results:")
dup = cks.loc["Identical vegetation indices in the source workbooks", "Result"]
bullets([f"**Measurement order and block (C9).** The 12 control plots form their own block and were measured first on every date (spectra 1–100). Disease is therefore partly confounded with field position and measurement time; this cannot be removed by any analysis of these data.",
         f"**Duplicated indices.** {dup}.",
         "**Detector joins.** The guard zones removed spurious 'perfect' features at the detector joins (Section 3.1)."])
table("Plots, leaves and growth stages per measurement date.", T["qc"][["Date", "Plots healthy", "Plots diseased", "Leaf spectra", "Growth stages", "Spectrum no. range healthy"]], widths=[1.2, 0.8, 0.8, 0.8, 3.2, 1.2], key="qc")
figure("fig02_mean_spectra", "Plot-average reflectance of healthy (blue) and diseased (orange) plots on the four dates (mean ± 1 SD). Grey: excluded detector edges and detector-join guard zones.")

h2("4.2 Physiological responses to white rust")
sig = ph[ph["significant (q<0.05)"]]
def ds(proxy):
    g = ph[ph.proxy == proxy]
    return ", ".join(f"{r.date_label.split(' ')[0]} (g = {r.hedges_g:+.2f}{'' if r['significant (q<0.05)'] else ', n.s.'})" for _, r in g.iterrows())
p(f"On T1 none of the pigment proxies differed between healthy and diseased plots, but both water indices were lower in the diseased plots (WI: q = {ph[(ph.proxy=='WI')&(ph.date=='11-02-2026')].q_BH.iloc[0]:.3f}; NDWI: q = {ph[(ph.proxy=='NDWI')&(ph.date=='11-02-2026')].q_BH.iloc[0]:.3f}). On T2 and T3 the chlorophyll proxies CIrededge and MTCI and the red-edge position were significantly lower in the diseased plots (on T4 only CIrededge remained significant); the carotenoid index CRI1 and PRI were lower and the anthocyanin index ARI strongly higher on T2–T4; the water indices were lower again on T3 and T4 but not on T2 (Table [[T:phys]], Figure [[F:fig06_physiology_boxplots]]). {len(sig)} of the 32 tests were significant after FDR correction.")
p("This is the same pattern that Tian et al. (2021) measured for rice blast – loss of chlorophyll and carotenoids, a contrary increase in anthocyanins and a later loss of water – except that the water signal appeared first here. An early water signal is consistent with the biology of white rust, whose pustules rupture the epidermis and increase transpiration losses, but the controls' separate block and measurement order (C9) could also contribute to an early difference and the finding should be confirmed in a randomised layout.")
pt = ph[["date_label", "proxy", "constituent", "test", "p", "q_BH", "hedges_g", "direction"]].copy()
pt.columns = ["Date", "Proxy", "Constituent", "Test", "p", "q (BH)", "Hedges g", "Direction"]
pt["Proxy"] = pt.Proxy.replace({"REIP, linear four-point interpolation (nm)": "REIP (4-point)"})
table("Healthy vs diseased plots for the physiological proxies (decision rule of Tian et al., 2021, plus BH-FDR).", pt, key="phys",
      fmt={"p": lambda v: f"{v:.1e}", "q (BH)": lambda v: f"{v:.1e}", "Hedges g": lambda v: f"{v:+.2f}"}, widths=[1.1, 1.3, 2.2, 1.4, 0.9, 0.9, 0.8, 1.4], fs=15)
figure("fig06_physiology_boxplots", "Physiological proxies of healthy (blue) and diseased (orange) plots on T1–T4 (analogue of Tian et al., 2021, Fig. 4). Stars: BH-adjusted q < 0.05 (∗), < 0.01 (∗∗), < 0.001 (∗∗∗); ns = not significant. Boxes show all plots; the tests exclude median ± 3 MAD outliers.")

h2("4.3 Spectral separability")
ss = T["selection_summary"]
p("Separability increased from T1 to T3 for most features (Figures [[F:fig04_scalogram_R]]–[[F:fig05_scalogram_CWT]]). On T1 the most separable regions were the visible bands (400–650 nm) and the NIR plateau slope (800–900 nm, first derivative); on T2 the red and red-edge region (580–720 nm) dominated; on T3 almost every region separated the classes (the 95th percentile of BA exceeded 0.9 for reflectance) and on T4 the SWIR regions (1400–2350 nm) were most separable. This shift with date mirrors the shift in Tian et al. (2021) from pigment-related VIS features early to water-related SWIR features late.")
figure("fig03_threshold_concept", "Thresholding separability (analogue of Tian et al., 2021, Fig. 3): PRI of the 48 plots on T3, class means Mh and Mi and the optimal threshold.", 12)
for f_, nm in [("R", "reflectance bands"), ("D1", "first derivatives")]:
    figure(f"fig04_scalogram_{f_}", f"Classification scalogram of the {nm} (analogue of Tian et al., 2021, Fig. 6). Shade = balanced accuracy; orange ticks = top 5 % on each date; bottom row = features common to k* dates; ▼ = region representatives.")
figure("fig04_scalogram_D2", "Classification scalogram of the second derivatives.")
figure("fig04_scalogram_D3", "Classification scalogram of the third derivatives.")
figure("fig05_scalogram_CWT", "Classification scalograms of the wavelet coefficients, scales 3–8 (analogue of Tian et al., 2021, Fig. 7).")

h2("4.4 Disease-specific spectral features and collinearity reduction")
lv = {r.Family: r["Consistency level k* used"] for _, r in ss.iterrows() if not pd.isna(r.get("Consistency level k* used", np.nan))}
SHORT = {"Reflectance band": "reflectance bands", "First derivative": "first derivatives", "Second derivative": "second derivatives", "Third derivative": "third derivatives", "Wavelet coefficient (CWT, Mexican hat)": "wavelet coefficients"}
p(f"The consistency level k* reached was {', '.join(f'{int(v)} dates for {SHORT[k]}' for k, v in lv.items())}. Together with the union of the per-date top-10 % scalar features this gave {len(T['dssf_candidates'])} candidate DSSFs; after removal of {int(T['dssf_candidates'].Duplicate_removed.sum())} exact duplicate and iterative VIF reduction, **{len(POOL)} DSSFs** remained, all with VIF < 10 (largest {dssf.VIF.max():.2f}; Table [[T:dssf]], Figure [[F:fig07_vif]]). The plain 'drop the largest VIF' rule would have kept {int(T['dssf_candidates'].In_plain_VIF_pool.sum())} features but would have discarded every reflectance band and the most separable indices (HI, ARI, Lic) while keeping weakly separable ones.")
dt = dssf[["Code", "Feature", "Family", "Region", "Dates_in_top", "Mean_BA", "VIF", "Meaning"]].copy()
dt["Feature"] = dt.Feature.str.replace(" water absorption", "").str.replace(" red absorption", "").str.replace(" blue absorption", "")
dt.columns = ["Code", "Feature", "Family", "Region", "Dates in top", "Mean BA", "VIF", "Physical meaning"]
table("The final pool of disease-specific spectral features (analogue of Tian et al., 2021, Table 2).", dt, key="dssf",
      fmt={"Mean BA": lambda v: f"{v:.3f}", "VIF": lambda v: f"{v:.2f}", "Dates in top": lambda v: str(int(v))}, widths=[0.7, 1.8, 1.3, 1.3, 0.6, 0.6, 0.5, 3.8], fs=14)
figure("fig07_vif", "Variance inflation factors of the final 16 DSSFs.", 13)
p("The pool contains features of every family and of every main absorption process: pigment absorption in the red (F1 R~641~, F8 wavelet at 634 nm, F11 Lic), the anthocyanin index ARI2 (F10), the NIR plateau slope (F2, first derivative at 852 nm), water absorptions at 970 nm (F13), 1350–1400 nm (F3) and 1940 nm (F6, F9, F12, F14), and C–H absorptions of dry matter near 1730–1750 nm and 2300 nm (F4, F5, F7). Two of these closely match the optimal wavelet features of Tian et al. (2021): the NIR slope near 850 nm (their WF~850,4~ and WF~866,5~) and the yellow–red edge near 610–640 nm (their WF~608,5~).")

h2("4.5 ML-SFFS classification – paper-faithful (procedure A)")
fbest = fa.loc[fa.groupby("Date", sort=False)["Mean OA"].idxmax()]
_t1 = T["sffs_vs_all"][T["sffs_vs_all"].Date.str.startswith("T1")]["Gain OA (pp)"]; G1, G2 = _t1.min(), _t1.max()
p(f"With the paper's procedure, one to four DSSFs (on average {fa['Mean no. of features'].min():.1f}–{fa['Mean no. of features'].max():.1f}) were enough to separate healthy from diseased plots almost perfectly on every date (Table [[T:faith]]). The mean OA ranged from {pc(fa['Mean OA'].min())} % (LDA, T1) to 100 %, and the SVM reached at least {pc(fa[fa.Classifier=='SVM']['Mean OA'].min())} % on every date, matching Tian et al.'s finding that SVM-SFFS was the best of the three classifiers. Feature selection improved on the use of all DSSFs most on T1 (gain {G1:.1f}–{G2:.1f} percentage points, Table [[T:sva]], Figure [[F:fig08_sffs_vs_all]]), as in Tian et al. (2021), whose SVM-SFFS exceeded SVM-all by about 10 % at the early stages.")
t7 = fa[["Date", "Classifier", "Most frequent OFC", "OFC frequency (%)", "Mean no. of features", "Mean OA", "SD OA", "Mean BA", "Mean kappa"]].copy()
table("Paper-faithful ML-SFFS: optimal feature combination and accuracy (4-fold CV × 100; analogue of Tian et al., 2021, Table 3).", t7, key="faith",
      fmt={"OFC frequency (%)": lambda v: f"{v:.0f}", "Mean no. of features": lambda v: f"{v:.2f}", "Mean OA": pc, "SD OA": pc, "Mean BA": pc}, widths=[1.1, 0.8, 1.6, 0.9, 0.9, 0.8, 0.7, 0.8, 0.8],
      note_="OA, SD OA and BA in %; OFC frequency = % of the 100 repetitions in which the most frequent OFC was selected. Codes F1–F16 as in Table [[T:dssf]].")
sv = T["sffs_vs_all"].copy()
table("SFFS-selected features vs all 16 DSSFs (procedure A; analogue of Tian et al., 2021, Fig. 8).", sv, key="sva",
      fmt={c_: pc for c_ in ["SFFS OA", "All-DSSF OA", "SFFS BA", "All-DSSF BA"]} | {"Gain OA (pp)": lambda v: f"{v:.1f}", "Gain BA (pp)": lambda v: f"{v:.1f}"})
figure("fig08_sffs_vs_all", "Overall accuracy with SFFS-selected features vs all DSSFs, for the paper-faithful (A, coloured) and nested (B, black) evaluation.")
fr = T["faithful_freq"]; codes_ = [CODE[n] for n in POOL]
topc = fr[codes_].mean().sort_values(ascending=False)
p(f"The OFCs differed between dates and classifiers, but a few features recurred (Figure [[F:fig10_selection_frequency]]): {', '.join(f'{c_} ({INV[c_]})' for c_ in topc.index[:4])} were selected most often over all dates and classifiers. On T2 the pair F2 + F8 (NIR slope at 852 nm + wavelet at 634 nm) was the OFC of all three classifiers.")
figure("fig10_selection_frequency", "Percentage of the 100 repetitions in which each DSSF was part of the optimal feature combination (procedure A).")
figure("fig13_top_dssf_boxplots", "The four most frequently selected DSSFs of healthy (blue) and diseased (orange) plots on T1–T4.")

h2("4.6 Corrected estimates – nested cross-validation (procedure B)")
p(f"When the test plots took no part in any selection step, the accuracies were lower (Table [[T:nested]], Figure [[F:fig09_faithful_vs_nested_vs_null]]): balanced accuracy {pc(ne.BA.min())}–{pc(ne.BA.max())} % (OA {pc(ne.OA.min())}–{pc(ne.OA.max())} %, κ {ne.kappa.min():.2f}–{ne.kappa.max():.2f}). The paper-faithful procedure overstated the balanced accuracy by {op['Optimism BA (pp)'].min():.1f}–{op['Optimism BA (pp)'].max():.1f} percentage points (Table [[T:opt]]), most on T1 ({op[op.Date.str.startswith('T1')]['Optimism BA (pp)'].min():.1f}–{op[op.Date.str.startswith('T1')]['Optimism BA (pp)'].max():.1f} pp). Detection nevertheless remained high from the first date: on T1 the best nested BA was {pc(ne[ne.Date.str.startswith('T1')].BA.max())} %, and from T2 onwards {pc(ne[~ne.Date.str.startswith('T1')].BA.min())}–{pc(ne[~ne.Date.str.startswith('T1')].BA.max())} %. Sensitivity (diseased plots recognised) was higher than specificity (controls recognised) in {int((ne.Sensitivity > ne.Specificity).sum())} of the 12 date × classifier combinations, the usual consequence of having three times more diseased plots.")
p(f"Under nested CV the SFFS subsets were no longer clearly better than all DSSFs: the all-DSSF classifiers reached BA {pc(ne['All-DSSF BA'].min())}–{pc(ne['All-DSSF BA'].max())} % and were at least as accurate as SFFS in {int((ne['All-DSSF BA'] >= ne.BA).sum())} of the 12 combinations. Part of the advantage of SFFS in procedure A is therefore the optimism of selecting the best of many subsets on the same plots.")
t9 = ne[["Date", "Classifier", "OA", "BA", "SD BA", "kappa", "Sensitivity", "Specificity", "All-DSSF BA", "Mean no. of features"]]
table("Nested cross-validation (procedure B): accuracy on held-out plots (10 × 4-fold).", t9, key="nested",
      fmt={c_: pc for c_ in ["OA", "BA", "SD BA", "Sensitivity", "Specificity", "All-DSSF BA"]} | {"kappa": lambda v: f"{v:.2f}", "Mean no. of features": lambda v: f"{v:.1f}"}, note_="Accuracies in %.")
table("Optimism of the paper-faithful estimate: procedure A minus procedure B.", op, key="opt",
      fmt={c_: pc for c_ in ["A: faithful OA", "A: faithful BA", "B: nested OA", "B: nested BA"]} | {"Optimism OA (pp)": lambda v: f"{v:.1f}", "Optimism BA (pp)": lambda v: f"{v:.1f}"})
figure("fig09_faithful_vs_nested_vs_null", "Balanced accuracy of the paper-faithful procedure (A, orange), of nested CV (B, blue, ± SD) and of procedure A with randomly permuted labels (C, grey band: mean–maximum).")
stab = T["nested_stability"].head(10)
p(f"The DSSF pool rebuilt inside the 40 outer folds was not identical to the full-data pool (median {T['nested_pool_size'].iloc[5, 0]:.0f} features), but its core was stable; the features entering it most often were " +
  ", ".join(f"{r['Feature']} ({r['In pool of outer folds (%)']:.0f} % of folds)" for _, r in stab.head(5).iterrows()) + ".")

h2("4.7 Permutation null (procedure C)")
if pm is not None:
    lk = pm[pm.Classifier.isin(["LDA", "kNN"])]
    p(f"With randomly shuffled labels – i.e. with no disease information at all – the paper-faithful procedure still reported a mean OA of {pc(pm['Null OA mean'].min())}–{pc(pm['Null OA mean'].max())} % and a mean BA of {pc(pm['Null BA mean'].min())}–{pc(pm['Null BA mean'].max())} %, with single permutations reaching OA {pc(pm['Null OA max'].max())} % (Table [[T:perm]], Figure [[F:fig11_permutation_null]]). These are the accuracies that the selection steps produce by chance on 48 plots and {NCAND:,} candidate features. The observed accuracies of LDA and k-NN were higher than every permuted value on every date (p = 0.048, the smallest p attainable with 20 permutations); the four SVM permutations are indicative only (smallest attainable p = 0.20).")
    t11 = pm[["Date", "Classifier", "Permutations", "Null OA mean", "Null OA max", "Null BA mean", "Observed OA (A)", "Observed BA (A)", "p (OA)"]]
    table("Permutation null of procedure A.", t11, fmt={c_: pc for c_ in ["Null OA mean", "Null OA max", "Null BA mean", "Observed OA (A)", "Observed BA (A)"]} | {"p (OA)": lambda v: f"{v:.3f}", "Permutations": lambda v: str(int(v))}, note_="Accuracies in %.", key="perm")
    NULLOA = f"{pc(pm['Null OA mean'].min())}–{pc(pm['Null OA mean'].max())}"
    figure("fig11_permutation_null", "Procedure A with shuffled labels (grey points: one per permutation) and with the true labels (diamonds).")

h2("4.8 Detection by infection stage (procedure D)")
piv = sa[sa.Classifier == "SVM"].pivot_table(index="Inoculation timing", columns="Date", values="Mean OA", observed=True)
_b = sa[(sa["Mean OA"] < 0.9995)]
_parts = []
for _d, _g in _b.groupby("Date", observed=True):
    _parts.append(f"{str(_d).split(' ')[0]}: {len(_g)} of 12 (lowest {100 * _g['Mean OA'].min():.1f} %)")
BELOW = ("; stage × classifier combinations with a mean OA below 100 % – " + ", ".join(_parts)) if len(_b) else "; every classifier reached 100 % at every stage"
det = sd[sd.Classifier == "SVM"].pivot_table(index="Group", columns="Date", values="Called diseased (%)", observed=True)
fa_rate = det.loc["Control"]
inoc = det.drop("Control")
low = inoc.stack().idxmin()
mins = {c_: list(inoc[c_][inoc[c_] == inoc[c_].min()].index) for c_ in inoc.columns}
late = [str(c_).split(" ")[0] for c_, g in mins.items() if set(g) <= {"D3", "D4"}]
STAGE_TXT = (" Differences between inoculation timings were small: the lowest detection rate on each date belonged to " +
             "; ".join(f"{'/'.join(g)} on {str(c_).split(' ')[0]}" for c_, g in mins.items()) +
             f". The later inoculations (D3/D4) were lowest on {', '.join(late)}, consistent with a shorter infection period, but with 9 plots per group one plot is 11 percentage points and none of these differences is statistically meaningful.")
p(f"Treated as separate infection stages (controls vs one inoculation timing on one date; Table [[T:stageA]]), the paper-faithful SVM-SFFS reached OA {pc(piv.values.min())}–{pc(piv.values.max())} % with on average {sa[sa.Classifier=="SVM"]["Mean no. of features"].min():.1f}–{sa[sa.Classifier=="SVM"]["Mean no. of features"].max():.1f} features{BELOW}. The unbiased nested-CV predictions (Table [[T:stageB]], Figure [[F:fig12_stage_wise]]) show that the SVM recognised {inoc.values.min():.0f}–{inoc.values.max():.0f} % of the inoculated plots of every timing on every date (lowest: {low[0]} on {low[1]}), while {fa_rate.min():.0f}–{fa_rate.max():.0f} % of the control plots were false alarms. " + STAGE_TXT)
t12 = sa[["Date", "Inoculation timing", "Classifier", "Mean OA", "Mean BA", "Mean no. of features", "Most frequent OFC", "OFC frequency (%)"]].copy(); t12["Date"] = t12.Date.astype(str)
t12 = t12[t12.Classifier == "SVM"]
table("Paper-faithful SVM-SFFS per infection stage: 12 controls vs the 9 plots of one inoculation timing (4-fold CV × 100).", t12, key="stageA",
      fmt={"Mean OA": pc, "Mean BA": pc, "Mean no. of features": lambda v: f"{v:.2f}", "OFC frequency (%)": lambda v: f"{v:.0f}"}, note_="LDA and k-NN results are given in the Excel workbook (sheet S20).")
t13 = sd[sd.Classifier == "SVM"].pivot_table(index="Group", columns="Date", values="Called diseased (%)", observed=True).reset_index()
t13.columns = ["Group"] + [str(c_) for c_ in t13.columns[1:]]
table("Plots called 'diseased' by the nested-CV SVM models (%). Controls: false-alarm rate; inoculated groups: detection rate.", t13, fmt={c_: lambda v: f"{v:.0f}" for c_ in t13.columns[1:]}, key="stageB")
figure("fig12_stage_wise", "Infection-stage analysis: (left) paper-faithful SVM-SFFS accuracy for controls vs each inoculation timing; (right) nested-CV detection rate of each group.")
vv = vd[vd.Classifier == "SVM"].pivot_table(index=["Variety", "Class"], columns="Date", values="Correct (%)", observed=True)
p(f"By variety (nested CV, SVM), inoculated plots were classified correctly in {vv.xs('Inoculated', level='Class').values.min():.0f}–{vv.xs('Inoculated', level='Class').values.max():.0f} % of cases for all three varieties, whereas the accuracy for control plots varied more ({vv.xs('Control', level='Class').values.min():.0f}–{vv.xs('Control', level='Class').values.max():.0f} %), mainly because each variety has only four control plots.")

h2("4.9 Cross-checks")
p(f"All {int((CK.Status == 'PASS').sum())} verification checks passed; {int((CK.Status == 'FLAG').sum())} items are flagged because they are properties of the data or of the original procedure that must be reported (Table [[T:ck]]). In the Excel workbook, live formulas reproduce the Python class means, the threshold balanced accuracies of all 16 DSSFs on all four dates and the summary accuracies of procedures A and B exactly (largest difference < 10^−15^).")
table("Cross-checks of every step.", CK, widths=[0.55, 2.6, 2.2, 3.5, 0.65], fs=14, key="ck")

# ------------------------------------------------------------------ 5 discussion
h1("5. Discussion")
h2("5.1 Physiological interpretation of the disease-specific features")
p("The selected DSSFs follow the physiological changes in Section 4.2. The **NIR plateau slope at 852 nm** (F2) was among the most frequently selected features (procedure A) and among the most stable members of the nested-CV pools. In the NIR, reflectance is governed by multiple scattering at the cell-wall/air interfaces of the mesophyll (Jacquemoud and Baret, 1990); white-rust pustules disrupt the epidermis and the intercellular structure. On every date the NIR reflectance of the controls declined from 800 to 900 nm (negative first derivative at 852 nm), whereas that of the diseased plots was flatter or rising. Tian et al. (2021) reached the same conclusion for rice blast, where wavelet features at 850–866 nm captured the collapse of the intercellular structure, and they noted that this region had been under-exploited in disease detection.")
p("The **yellow–red edge** (F8, wavelet at 634 nm; F1, R~641~; F11, R~440~/R~690~) and the **anthocyanin index ARI2** (F10) record pigment changes: loss of chlorophyll raises red reflectance (R~641~ was higher in diseased plots from T2) and lowers the blue/red ratio Lic, and shifts the red edge to shorter wavelengths, while anthocyanins accumulate in stressed tissue (Gitelson et al., 2001). The water features at 970 nm (F13), 1350 nm (F3) and 1940 nm (F6, F9, F12, F14) agree with the early decrease of the water indices, and the wavelet features at 1736, 1752 and 2318 nm (F4, F5, F7) lie in the C–H absorption regions of cellulose, lignin and protein (Kokaly and Clark, 1999), suggesting changes in leaf dry matter as tissue is colonised and pustules form. Because these interpretations rest on spectral proxies rather than measured biochemistry (C8), they should be presented as consistent with, not proof of, the underlying changes.")
h2("5.2 How optimistic is the paper-faithful accuracy?")
p(f"Procedure A reports the best of many cross-validated accuracies – over thousands of candidate features (Step 3), over the subsets visited by SFFS and over the SVM parameter grid – evaluated on the same plots. With 48 plots and {NCAND:,} candidate features some feature combination will separate the classes by chance, and the permutation test shows how large this effect is: {NULLOA} % OA without any disease information. The nested CV (B) removes this bias and should be reported as the accuracy of the method; procedure A remains useful for comparison with Tian et al. (2021) and for identifying the optimal feature combinations, which are the features consistently chosen across repetitions and folds. The same caution applies to the accuracies of Tian et al. (2021), which were obtained in the same way, and is a general lesson from other fields (Ambroise and McLachlan, 2002; Varma and Simon, 2006; Cawley and Talbot, 2010).")
h2("5.3 Comparison with Tian et al. (2021)")
bullets(["**Agreement.** A few DSSFs (one to four) suffice; SVM-SFFS is the most accurate criterion classifier in procedure A; feature selection helps most at the earliest date; pigment features dominate early and water/SWIR features late; NIR wavelet/derivative features near 850 nm are among the most robust indicators.",
         f"**Differences.** In this study the water signal appeared before the pigment signal; derivatives and continuum-removal parameters, which Tian et al. did not use, entered the pool; and the corrected (nested) balanced accuracies are {op['Optimism BA (pp)'].min():.0f}–{op['Optimism BA (pp)'].max():.0f} points lower than the paper-faithful ones.",
         "**Design.** The plot-average spectra of field plots are less noisy than single-leaf spectra but mix leaves at different stages of infection; the infection stage is defined here by the inoculation timing and the measurement date rather than by visual lesion scoring."])
h2("5.4 Limitations")
bullets(["**Confounded layout (C9).** All controls were in one block and measured first on every date, so part of the healthy–diseased difference may reflect field position or measurement time (e.g. leaf temperature, instrument drift). A randomised layout and a randomised measurement order are needed to rule this out.",
         "**Imbalance and sample size.** 12 vs 36 plots (9 per inoculation group) give wide uncertainty; one misclassified control changes specificity by 8 points.",
         "**No measured biochemistry (C8).** The physiological interpretation relies on spectral proxies.",
         "**Inoculation timings.** The days after sowing of D1–D4 and the sowing date were not available, so infection stage could not be expressed as days after inoculation as in the paper.",
         "**Computation.** The SVM permutation test used only 4 permutations; in procedure D(i) the DSSF pool was chosen on all plots (optimistic, like procedure A).",
         "**Single season and site.** Transfer to other seasons, sites or canopy-level sensors has not been tested."])
h2("5.5 Recommendations")
bullets(["Report the nested-CV accuracies (procedure B) as the performance of the method and the paper-faithful values (procedure A) only for comparison with Tian et al. (2021).",
         "Use the stable core of DSSFs – NIR slope near 850 nm, yellow-red edge near 635 nm, anthocyanin (ARI2), water absorptions at 970, 1350 and 1940 nm – as candidate indicators for an independent season.",
         "In future experiments, randomise the controls among the blocks and the measurement order, record the inoculation dates, and measure chlorophyll, anthocyanin and water content on a subset of leaves."])

# ------------------------------------------------------------------ 6 conclusions
h1("6. Conclusions")
numbered([f"The ML-SFFS methodology of Tian et al. (2021) could be applied step by step to plot-average spectra of white-rust-infected mustard. From {NCAND:,} candidate features, {len(POOL)} disease-specific spectral features covering pigment, NIR-structure, water and dry-matter absorptions were extracted.",
          "White rust lowered the water indices first (T1) and the chlorophyll and carotenoid indices from T2 onwards, while the anthocyanin index rose – the physiological basis of the selected features.",
          f"With the paper's procedure, one to four features gave {pc(fa['Mean OA'].min())}–100 % overall accuracy on every date, SVM-SFFS being the best classifier.",
          f"Corrected for selection bias by nested cross-validation, the balanced accuracy was {pc(ne.BA.min())}–{pc(ne.BA.max())} %; the paper-faithful values are optimistic by {op['Optimism BA (pp)'].min():.0f}–{op['Optimism BA (pp)'].max():.0f} percentage points, and the procedure reaches {NULLOA} % OA even with random labels.",
          "Detection rates were similar for all four inoculation timings and all three varieties; the confounding of controls with block and measurement order is the main limitation to be removed in future experiments."])

# ------------------------------------------------------------------ references
h1("References")
note("All references were checked against publisher, repository or indexing records (October 2026); the verification status of each is listed in the Excel workbook (sheet S24). References to the remaining vegetation indices are given in the source workbooks.")
for key, full, doi, status, use in sorted(REFS, key=lambda r: r[1]):
    B.append({"type": "ref", "text": full + (f" https://doi.org/{doi}" if doi.startswith("10.") else "")})
h2("Errors found in the reference list of Tian et al. (2021)")
table("Reference errors in Tian et al. (2021) detected during cross-checking.", pd.DataFrame(TIAN_REF_ERRORS, columns=["Reference", "As printed", "Correct"]), widths=[1.5, 3, 3.5], fs=15)

h1("Appendix A. Paper vs this study")
table("Design and method of Tian et al. (2021) and of this study.", pd.DataFrame(PAPER_VS_STUDY, columns=["Aspect", "Tian et al. (2021)", "This study"]), widths=[1.3, 3, 3.7], fs=15)
h1("Appendix B. Guide to the accompanying files", pb=False)
table("Files delivered with this chapter.", pd.DataFrame([
    ("WhiteRust_ML-SFFS_TianMethod_Analysis.xlsx", "25 sheets, one per step (S00 contents … S24 references); green cells are live Excel formulas that recompute key results"),
    ("WhiteRust_ML-SFFS_TianMethod_Slides.pptx", "Step-by-step slides of the workflow, results and corrections"),
    ("WhiteRust_ML-SFFS_TianMethod_Thesis_Chapter.docx", "This document"),
    ("code/ (Python, JavaScript)", "Scripts that reproduce every number: s01_load … s12_doc"),
], columns=["File", "Content"]), widths=[3, 5])

def resolve(t):
    def f(m):
        k = m.group(1)
        assert k in LABELS, k
        return str(LABELS[k])
    return re.sub(r"\[\[([TF]:[^\]]+)\]\]", f, t)
KSTAR = re.compile(r"(?<![*\w])k\*(?!\*)")
fixk = lambda t: KSTAR.sub("k^*^", t)
for b in B:
    for k_ in ("text", "caption", "note"):
        if isinstance(b.get(k_), str): b[k_] = fixk(resolve(b[k_]))
    if b.get("items"): b["items"] = [fixk(resolve(x)) for x in b["items"]]
    if b.get("rows"): b["rows"] = [[fixk(c_) for c_ in r_] for r_ in b["rows"]]
left = [b for b in B if re.search(r"\[\[[TF]:", json.dumps(b, ensure_ascii=False))]
assert not left, left[:1]
json.dump({"title": "White rust ML-SFFS (Tian et al. 2021 method)", "blocks": B}, open(OUT, "w"), ensure_ascii=False)
print("blocks", len(B), "tables", TAB[0], "figures", FIGN[0])
