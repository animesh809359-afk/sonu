// Detailed thesis-style report (Word) from work/results.json and figures
const fs = require("fs");
const path = require("path");
const docx = require(process.env.DOCX_MODULE || "docx");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType, ImageRun,
        AlignmentType, LevelFormat, PageBreak, TableOfContents, Footer, PageNumber, BorderStyle } = docx;

const WORK = process.argv[2];
const OUT = process.argv[3];
const J = JSON.parse(fs.readFileSync(path.join(WORK, "results.json"), "utf8"));
const T = J.txt || {};
const FIG = (n) => path.join(J.fig, n + ".png");
const A = J.A, K = J.K, CC = J.C, X = J.X;
const pct = (v) => (v == null ? "–" : (100 * v).toFixed(1) + " %");
const vA = (p, s) => A.v[p + "|" + s].BA, vC = (p, s) => CC.v[p + "|" + s].BA;
const CW = 9638; // content width (A4, 2 cm margins) in DXA

const body = [];
let figNo = 0, tabNo = 0;
const P = (text, opts = {}) => body.push(new Paragraph({ children: runs(text, opts), spacing: { after: 120, line: 300 }, alignment: opts.align || AlignmentType.JUSTIFIED }));
function runs(text, opts = {}) {
  // **bold** and _italic_ markup
  const out = [];
  const re = /(\*\*[^*]+\*\*|_[^_]+_)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), size: opts.size || 22, italics: opts.italics }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, size: opts.size || 22 }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, size: opts.size || 22 }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), size: opts.size || 22, italics: opts.italics }));
  return out;
}
const H1 = (t) => body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)], spacing: { before: 360, after: 160 } }));
const H2 = (t) => body.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)], spacing: { before: 240, after: 120 } }));
const H3 = (t) => body.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)], spacing: { before: 180, after: 80 } }));
const B = (items) => items.forEach((t) => body.push(new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(t), spacing: { after: 60 } })));
const EQ = (t) => body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 120 },
  children: [new TextRun({ text: t, font: "Cambria Math", size: 22, italics: false })] }));
const pageBreak = () => body.push(new Paragraph({ children: [new PageBreak()] }));

function pngSize(file) { const b = fs.readFileSync(file); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }
function figure(name, caption, widthPx = 610) {
  const f = FIG(name);
  if (!fs.existsSync(f)) return;
  const d = pngSize(f);
  const w = Math.min(widthPx, 620), h = Math.round(d.h * w / d.w);
  figNo += 1;
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width: w, height: h }, altText: { title: name, description: caption, name } })] }));
  body.push(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 200 },
    children: [new TextRun({ text: `Figure ${figNo}. `, bold: true, size: 20 }), new TextRun({ text: caption, size: 20, italics: true })] }));
  return figNo;
}
function table(rows, caption, widths, fontSize = 18) {
  tabNo += 1;
  body.push(new Paragraph({ spacing: { before: 160, after: 80 }, keepNext: true,
    children: [new TextRun({ text: `Table ${tabNo}. `, bold: true, size: 20 }), new TextRun({ text: caption, size: 20 })] }));
  const n = rows[0].length;
  const ws = widths && widths.length === n ? widths : Array(n).fill(Math.floor(CW / n));
  const tot = ws.reduce((a, b) => a + b, 0);
  const cw = ws.map((w) => Math.floor(w * CW / tot));
  const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBEB7" };
  body.push(new Table({
    width: { size: cw.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: cw,
    rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, children: r.map((c, j) => new TableCell({
      width: { size: cw[j], type: WidthType.DXA }, borders: { top: border, bottom: border, left: border, right: border },
      shading: i === 0 ? { type: ShadingType.CLEAR, color: "auto", fill: "1F3D2B" } : (i % 2 ? undefined : { type: ShadingType.CLEAR, color: "auto", fill: "F4F4F1" }),
      margins: { top: 40, bottom: 40, left: 70, right: 70 },
      children: [new Paragraph({ children: [new TextRun({ text: String(c), size: fontSize, bold: i === 0, color: i === 0 ? "FFFFFF" : "1B1B1A" })] })] })) })),
  }));
  body.push(new Paragraph({ spacing: { after: 160 }, children: [] }));
  return tabNo;
}
const em = (m) => [["Classified \\ Reference", "Healthy", "Diseased", "Row total", "User's accuracy"],
  ["Healthy", m.HH, m.DH, m.HH + m.DH, pct(m.HH / (m.HH + m.DH))], ["Diseased", m.HD, m.DD, m.HD + m.DD, pct(m.DD / (m.HD + m.DD))],
  ["Column total", m.HH + m.HD, m.DH + m.DD, m.N, ""], ["Producer's accuracy", pct(m.PA_H), pct(m.PA_D), "", ""],
  ["Overall accuracy", pct(m.OA), "Balanced accuracy", pct(m.BA), `κ = ${m.kappa.toFixed(3)}`]].map((r) => r.map(String));

// ============================================================ title page
body.push(new Paragraph({ spacing: { before: 2400, after: 240 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Discrimination of healthy and white-rust-diseased mustard leaves using field spectroradiometry", bold: true, size: 40, color: "1F3D2B" })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "A four-tier hierarchical analysis (Das et al., 2020) with imbalance correction, CART versus Random Forest band selection, disease-sensitive feature extraction and the four-tier analysis of the combined feature pool", size: 26, italics: true })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: `Leaf level · ${J.n} leaf spectra (${J.nH} healthy, ${J.nD} diseased) · four dates, three growth stages and three varieties combined`, size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: "Animesh Panda · Division of Agricultural Physics, ICAR-Indian Agricultural Research Institute, New Delhi", size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Methods, results and interpretation for thesis use · companion to the Excel workbook and the presentation", size: 20, color: "52514E" })] }));
pageBreak();
body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Contents")] }));
body.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }));
body.push(new Paragraph({ children: [new TextRun({ text: "(Right-click → Update field in Word to refresh the page numbers.)", italics: true, size: 18, color: "52514E" })] }));
pageBreak();

// ============================================================ summary
H1("Summary");
(T.abstract || []).forEach((t) => P(t));

// ============================================================ 1 introduction
H1("1. Introduction");
P("White rust, caused by the oomycete _Albugo candida_ (Pers.) Roussel ex Kuntze, is one of the most damaging foliar diseases of Indian mustard (_Brassica juncea_). Local infection produces white, raised sori (pustules) mainly on the abaxial leaf surface, with chlorosis of the surrounding tissue; systemic infection deforms inflorescences into 'stag heads' (Saharan et al., 2014). Because symptoms change leaf pigments, cell structure and water status, they alter the leaf reflectance spectrum, which can be measured rapidly and non-destructively with a field spectroradiometer (Mahlein, 2016).");
P("A hyperspectral spectrum contains about two thousand strongly correlated bands, many more than the number of samples needed to estimate a classifier reliably. Das et al. (2020) proposed a four-tier hierarchical method to reduce such data to a few discriminating wavelengths and to test whether these are sufficient: Tier 1 screens every band with one-way ANOVA; Tier 2 selects a small set of wavelengths with classification and regression trees (CART); Tier 3 quantifies the spectral separability of the classes with the Jeffries–Matusita (J–M) distance on the selected wavelengths; Tier 4 classifies the samples with quadratic discriminant analysis (QDA) under 10-fold cross-validation. They discriminated 14 rice genotypes from 336 canopy spectra with 98 % overall accuracy.");
P("This study applies the same hierarchy to a different problem — healthy versus white-rust-diseased mustard leaves measured with a contact probe on four dates, three growth stages and three varieties, all pooled — and adds what this problem requires: (i) corrections for the 1 : 5 class imbalance, for multiple testing and for the nesting of leaves in plots; (ii) honest validation in which every selection step is repeated inside the training data and test plots (and test dates) are never seen during training; (iii) a comparison of CART with Random Forest (RF) as the Tier-2 selector and as a classifier; (iv) extraction of disease-sensitive spectral features (band reflectance, continuum-removed absorption features, vegetation indices, first-derivative spectra and the red-edge inflection point); and (v) the four-tier analysis applied to the combined pool of all these features.");
H2("1.1 Objectives");
B(["Identify the wavelengths at which healthy and white-rust-diseased mustard leaves differ, irrespective of date, growth stage and variety (Tier 1).",
   "Select a minimal discriminating band set with CART as in Das et al. (2020), and with Random Forest as an alternative (Tier 2).",
   "Quantify the separability of the two classes on the selected bands (Tier 3) and the classification accuracy of QDA (Tier 4).",
   "Validate the complete pipeline on new plots and new dates, and test whether the differences between approaches are significant.",
   "Extract disease-sensitive spectral features (K1–K4) and evaluate CART and RF on each feature family and on the combined feature pool, including the full four-tier analysis of the combined pool."]);

// ============================================================ 2 methods
pageBreak();
H1("2. Materials and methods");
H2("2.1 Data");
P(`Leaf reflectance was recorded with an ASD FieldSpec spectroradiometer and contact probe (350–2500 nm, 1 nm) on 11-02-2026, 24-02-2026, 03-03-2026 and 13-03-2026 in 48 plots: 12 healthy control plots (plots 1–12) and 36 inoculated plots (13–48) of three varieties (V1–V3). Each date was exported as one workbook with one column per leaf spectrum and descriptor rows for plot, variety, growth stage (vegetative, flowering, pod formation) and the healthy/diseased label. Plot-average columns (=AVERAGE formulas) were not used: the analysis is at leaf level. Exact duplicates were removed: 75 spectra in a second data block of the 13-03-2026 file repeated plots 13, 34, 38, 41 and 42, and four unnamed spectra of plot 27 on 11-02-2026 were identical to Mustard00215–00218. ${J.n} unique leaf spectra remained (${J.nH} healthy, ${J.nD} diseased; ratio 1 : ${J.ratio.toFixed(2)}). Leaf position and disease score were not used; the response is healthy vs diseased.`);
table(J.by_date, "Leaf spectra by date and class.", [3, 2, 2, 2]);
table(J.by_stage, "Leaf spectra by growth stage (all dates).", [3, 2, 2]);
H2("2.2 Pre-processing and band set (Step 0–1)");
P("Das et al. (2020) removed 1350–1430, 1800–1950 and 2350–2500 nm because of atmospheric water vapour in canopy measurements. The contact probe illuminates the leaf with its own lamp at a few millimetres, so there is no atmospheric path and these bands carry leaf-water information; they were kept. The 350–399 nm detector edge was removed because its noise (standard deviation of the Savitzky–Golay residual) was about 116 times that of 500–699 nm. Tiers 1–4 used the raw reflectance of 400–2500 nm (2101 bands), as in the original method. Outliers were screened with the spectral angle to the class median spectrum and flagged, not removed.");
H2("2.3 Tier 1 — statistical screening");
P("With two classes the one-way ANOVA of Das et al. reduces to a two-sample test (F = t² of Student's t). Because the class variances differ at many bands (Levene's test) and the classes are unbalanced, Welch's unequal-variance t-test was used:");
EQ("t = (x̄_D − x̄_H) / √(s²_D/n_D + s²_H/n_H),   ν = (s²_D/n_D + s²_H/n_H)² / [ (s²_D/n_D)²/(n_D−1) + (s²_H/n_H)²/(n_H−1) ]");
P("Testing 2101 bands at α = 0.05 would yield about 105 false positives under the null hypothesis, so p-values were adjusted with the Benjamini–Hochberg false-discovery rate (FDR; Benjamini and Hochberg, 1995): q₍ᵢ₎ = min over k ≥ i of p₍ₖ₎·m/k. Bands with q < 0.05 passed to Tier 2. Three checks accompany the test: (a) one-way ANOVA, the rule of Das et al.; (b) 1000 balanced random subsets of 378 healthy and 378 diseased leaves, to show that significance is not an artefact of the large diseased class; (c) a linear mixed model y = β₀ + β₁·Disease + u_plot + ε with a random plot intercept (REML), because leaves of one plot share the plot environment (pseudo-replication; Hurlbert, 1984). The −log₁₀(p) of every band was plotted against wavelength (significance spectrum). Effect size is reported as Hedges' g (bias-corrected standardised mean difference).");
H2("2.4 Tier 2 — CART band selection");
P("Classification and regression trees (Breiman et al., 1984) split the data recursively; at each node the band and threshold are chosen that most reduce the Gini impurity G = 1 − Σ_k p_k², where p_k is the (prior-weighted) proportion of class k in the node. The bands used as split variables form the selected set. As in Das et al., the R package rpart was used (Therneau and Atkinson, 2023), with method = 'class', split = 'gini', minsplit = 20, minbucket = 7, cp = 0.01 and no competitor or surrogate splits. **Correction for imbalance:** prior = c(0.5, 0.5), so that each class carries equal weight in the impurity and in the class assigned to a terminal node. The complexity parameter was cross-validated with folds grouped by plot; the 1-SE rule gives a smaller tree. Stability was assessed by refitting rpart on 200 plot-level bootstrap samples and in the 50 nested training sets of V3; a band counts as re-selected when a band within ± 10 nm is chosen.");
H2("2.5 Random Forest as an alternative Tier-2 selector and classifier");
P("A Random Forest (Breiman, 2001) averages many trees grown on bootstrap samples with a random subset of √p candidate bands at each split, which makes it far more stable than a single tree. For imbalanced classes the Balanced Random Forest grows each tree on a bootstrap sample with equal numbers of both classes (Chen et al., 2004), implemented in imbalanced-learn (Lemaître et al., 2017): BalancedRandomForestClassifier with sampling_strategy = 'all', replacement = True, bootstrap = False, max_features = √p, 500 trees (1000 for importance), random_state = 42. Band importance is the mean decrease in Gini impurity (MDI). Because neighbouring bands are nearly identical, bands were picked as importance peaks: local maxima of the importance spectrum at least 10 nm apart; the 17 highest peaks give RF-17 (the size of the CART set of Das et al.) and the 10 highest RF-10. Checks: a second forest with another seed, the R package randomForest (Liaw and Wiener, 2002) with stratified balanced sampling, permutation importance (Strobl et al., 2007) and an ordinary class-weighted forest.");
H2("2.6 Tier 3 — Jeffries–Matusita distance");
P("The J–M distance measures the separability of two class distributions assumed multivariate normal (Swain and Davis, 1978; Richards, 2013). With class means μ and covariance matrices Σ of the selected bands, the Bhattacharyya distance is");
EQ("α = ⅛ (μ_H − μ_D)ᵀ [(Σ_H + Σ_D)/2]⁻¹ (μ_H − μ_D) + ½ ln{ |(Σ_H + Σ_D)/2| / √(|Σ_H| |Σ_D|) }");
EQ("J–M = 2 (1 − e^(−α))   (0 to 2);   √J–M ranges from 0 to √2");
P("Das et al. printed J–M = √[2(1 − e^(−α))] (Eq. 1) but applied thresholds of 1.90 and 1.94 (97 % of 2), which belong to the 0–2 scale; both scales are reported here and the thresholds are applied on the 0–2 scale. The distance was computed with a Cholesky factorisation and verified with explicit inverses and determinants; the J–M of a class with itself must be zero.");
H2("2.7 Tier 4 — quadratic discriminant analysis");
P("QDA assigns a leaf x to the class with the largest discriminant score");
EQ("δ_k(x) = −½ ln|Σ_k| − ½ (x − μ_k)ᵀ Σ_k⁻¹ (x − μ_k) + ln π_k");
P("with a separate covariance matrix for each class (Hastie et al., 2009). **Correction for imbalance:** equal prior probabilities π_H = π_D = 0.5 (the sample priors 0.17/0.83 would favour 'diseased'); sample priors and LDA are reported for comparison. As in Das et al., accuracy was estimated by 10-fold cross-validation and summarised in an error matrix (rows = classified, columns = reference) with producer's and user's accuracies (Congalton, 1991). QDA was cross-checked against MASS::qda in R (Venables and Ripley, 2002) and against manual discriminant functions.");
H2("2.8 Accuracy measures");
P("With unequal classes, overall accuracy (OA) is dominated by the diseased class. The headline metric is therefore the balanced accuracy BA = ½ (PA_H + PA_D), the mean of the producer's accuracies (recalls) of both classes (Brodersen et al., 2010). Cohen's κ (Cohen, 1960), the area under the ROC curve (AUC; Hanley and McNeil, 1982), user's accuracies and F1 are also reported.");
H2("2.9 Validation design");
P("Choosing bands on all leaves and then cross-validating on the same leaves is optimistic (selection bias; Ambroise and McLachlan, 2002; Varma and Simon, 2006), and leaves of one plot are more alike than leaves of different plots, so leaf-level folds leak plot information (Roberts et al., 2017). Five schemes were used, with identical folds in every step:");
table([["Scheme", "Test data", "Refitted on the training data", "Purpose"],
       ["V1", "leaf-level stratified 10-fold (seed 42)", "classifier only (bands fixed)", "reproduces Das et al.; optimistic"],
       ["V2", "10 folds grouped by plot (seed 42)", "classifier only", "removes plot leakage"],
       ["V3", "10 folds grouped by plot × 5 repeats (seeds 101–105)", "Tier 1 + selection + classifier (nested)", "honest estimate for new plots"],
       ["V4", "30 % of plots (4 healthy + 11 diseased) × 10 splits", "everything", "independent hold-out plots"],
       ["V5", "one held-out date in the V4 test plots (40 units)", "everything (other dates, training plots)", "unseen date and unseen plots"]],
      "Validation schemes. Plots are grouped across all dates, so no plot contributes to both training and test data.", [1, 3, 3, 3]);
P("Pipelines were compared with the paired Wilcoxon signed-rank test (Wilcoxon, 1945) over the 50 V3 folds and the 10 V4 splits, which share the same test leaves. The stability of band selection was summarised by the share of bands selected in every training set and by the mean pairwise Jaccard similarity of the selected sets (± 10 nm; Kuncheva, 2007).");
H2("2.10 Disease-sensitive feature extraction (Part K)");
H3("K0 — detector splice correction, smoothing and guard zones");
P("The ASD records 350–1000, 1001–1800 and 1801–2500 nm with three detectors; small steps occur at the joins. For each join a straight line was fitted to the 10 nm before it and the following detector was shifted additively to continue that line. Spectra were smoothed with a Savitzky–Golay filter (window 11, order 2; Savitzky and Golay, 1964); first and second derivatives used windows 15 and 21. A date-dependent start-up rise after 1801 nm was detected, so guard zones (990–1010 and 1795–1835 nm for reflectance; 988–1012 and 1793–1837 nm for the first derivative; 985–1015 and 1790–1840 nm for the second) were excluded from feature ranking; results with the guard bands are reported to show the size of the artefact.");
H3("K1 — band reflectance");
P("For every smoothed band: Welch's t-test with FDR, Hedges' g, the direction-free AUC (max(AUC, 1 − AUC)) and a single-band threshold classifier. The threshold maximises Youden's J = sensitivity + specificity − 1 (Youden, 1950); threshold and direction were chosen on the training plots and applied to the test plots (V3, V4).");
H3("K2 — continuum-removed absorption features");
P("In six windows (400–548, 548–765, 914–1069, 1069–1258, 1258–1721 and 1721–2304 nm) the reflectance was divided by its upper convex hull (continuum removal; Clark and Roush, 1984; Kokaly and Clark, 1999). From the continuum-removed curve CR(λ): depth = 1 − min CR, position = wavelength of the minimum, area = Σ (1 − CR), width = full width at half depth, symmetry = share of the area left of the position — 30 parameters.");
H3("K3 — disease-sensitive spectral (vegetation) indices");
P("The 31 indices of the flowering-stage analysis were computed (e.g. NDVI, GNDVI, PRI, MTVI2, TCARI, ARI, PSRI, NWI2, WI; formulas in workbook sheet 17). mCARI1 and MTVI1 are algebraically identical in the given form. An optimised two-band index (K3b) was searched exhaustively: NDSI(i, j) = (R_i − R_j)/(R_i + R_j) and DI(i, j) = R_i − R_j for all pairs on a 5 nm grid, refined at 1 nm; the search was repeated inside 20 training sets for an unbiased estimate.");
H3("K4 — first-derivative spectra, edge parameters and the red-edge inflection point (REIP)");
P("First-derivative bands were tested like K1. Twenty edge parameters were derived (Gong et al., 2002): amplitude, position and area (sum of the derivative) of the blue (490–530 nm), yellow (550–582 nm) and red (680–760 nm) edges, green-peak and red-well reflectance and position, the linear four-point red-edge position and six ratios. The REIP was estimated by four methods: maximum of the first derivative (Horler et al., 1983); linear four-point interpolation, REP = 700 + 40 [(R670 + R780)/2 − R700] / (R740 − R700) (Guyot and Baret, 1988); three-point Lagrangian interpolation of the derivative around its maximum (Dawson and Curran, 1998); and linear extrapolation of the far-red (680–694 nm) and NIR (724–760 nm) derivative lines (Cho and Skidmore, 2006).");
H3("K6 — correlation spectra");
P("Severity scores were not used, so the point-biserial correlation r between each band (reflectance and first derivative) and the binary disease status (healthy = 0, diseased = 1) was computed on all leaves and on each date; r is a monotone function of Student's t.");
H3("K5 — CART versus Random Forest on each feature group");
P("Each feature group — raw spectrum, K1, K2, K3, K4, the combined pool, and K4 including the guard bands (artefact test) — was classified by CART and by a Balanced RF in V3 and V4 without pre-screening; RF − CART was tested with the paired Wilcoxon test. A compact set of 15 non-redundant features (|r| < 0.9) with the highest AUC was also chosen inside every training set and classified by RF, CART and QDA.");
H2("2.11 Four-tier analysis of the combined feature pool (Part C)");
P(`The K1 bands, 30 K2 parameters, 31 K3 indices, K4 first-derivative bands and 20 edge parameters (guard zones excluded) form a pool of ${CC.pool_raw} features; exact duplicates (|r| ≥ 0.99999) were removed, leaving ${CC.n_features}. The four tiers were then applied exactly as in Part A: Welch t + FDR; CART (rpart, equal priors) and Balanced RF selection (peaks within each spectral series; every scalar feature its own candidate; candidates with |r| ≥ 0.999 to a chosen feature skipped to keep covariances invertible); J–M; QDA with equal priors; validation V1–V5 with identical folds; comparison with Part A and K5 by paired Wilcoxon tests.`);
H2("2.12 Additional checks");
B(["V5: transfer to an unseen date in unseen plots (Section 2.9).",
   "Stratified checks: the AUC of key features and the balanced accuracy of the classifiers within each date, growth stage and variety.",
   "Sensitivity analyses: band range (350–2500 and 450–2450 nm) and the four duplicate spectra kept.",
   "Cross-checks at every step (independent implementations, Excel recomputation, R versus Python) — workbook sheet 33."]);
H2("2.13 Software");
P("Python 3.13 with NumPy, SciPy, pandas, statsmodels (Seabold and Perktold, 2010), scikit-learn (Pedregosa et al., 2011), imbalanced-learn and matplotlib; R 4.3.3 (R Core Team, 2024) with rpart, MASS and randomForest. The code is organised as a reusable, configuration-driven pipeline.");

// ============================================================ 3 results
pageBreak();
H1("3. Results");
H2("3.1 Data audit and spectra (Step 0–1)");
P(`All quality checks passed (no missing values; reflectance ${J.checks0[2] ? J.checks0[2][1] : ""}; one class and one variety per plot). The mean spectra (Figure ${figNo + 1}) show the typical shape of green leaves.`);
figure("F02_mean_spectra", "Mean reflectance (± 1 SD) of healthy and diseased leaves, all dates combined (as Figure 3 of Das et al., 2020).");
(T.spectra || []).forEach((t) => P(t));
figure("F02b_mean_spectra_by_date", "Mean spectra of healthy and diseased leaves on each date.");
table(J.noise, "Noise by spectral region (SD of the Savitzky–Golay residual).", [3, 2, 2]);
H2("3.2 Tier 1 — significant wavelengths");
P(`${A.n_sig} of ${J.n_bands} bands differed significantly between healthy and diseased leaves (Welch + FDR, q < 0.05). In 1000 balanced subsets the median number of significant bands was ${A.balanced.median}; ${A.balanced.ge95} bands were significant in at least 95 % of subsets. With a random plot effect ${A.mixed_sig} bands remained significant.`);
table(A.tests, "Number of significant bands by test.", [6, 2]);
figure("F03_tier1_significant_regions", "Bands with a significant difference between healthy and diseased leaves (grey; Welch + FDR), with the class means (as Figure 4 of Das et al., 2020).");
figure("F04_tier1_frequency", "Share of 1000 balanced subsets (378 vs 378 leaves) in which each band differs significantly, and the mean spectrum (as Figure 5 of Das et al., 2020).");
figure("F05_minus_log10_p", "Significance spectrum: −log₁₀(p) of Welch's test, its FDR-adjusted q and the mixed-model q against wavelength; dashed line = 0.05.");
(T.log10p || []).forEach((t) => P(t));
table(A.regions, "Significance by spectral region.", [3, 1, 2, 2, 2, 1]);
H2("3.3 Tier 2 — CART band selection");
P(`CART selected ${A.set_sizes[A.cart_name]} bands: ${A.sets[A.cart_name]} nm. The 1-SE tree retained ${Object.keys(A.set_sizes).filter((k) => k.includes("1-SE")).map((k) => A.set_sizes[k] + " bands (" + A.sets[k] + " nm)").join("") || "the same bands"}.`);
figure("F06_cart_tree", "CART tree on the Tier-1 bands (rpart, prior 0.5/0.5; as Figure 6 of Das et al., 2020). Leaves: predicted class and numbers of healthy/diseased leaves.", 620);
table(A.cart_table, "Wavelengths selected by CART, with re-selection frequency in 200 plot-level bootstraps and 50 nested training sets.", [1, 2, 1, 1, 2, 2, 1.5], 16);
figure("F08_cart_reselection", "Re-selection frequency of each CART band (± 10 nm).");
(T.cart || []).forEach((t) => P(t));
H2("3.4 Tier 3 — J–M separability");
table(A.tier3, "J–M distance between healthy and diseased leaves for each band set (0–2 scale).", [4, 2, 2]);
(T.jm || []).forEach((t) => P(t));
figure("F09_tier3_tier4_incremental", "J–M distance and QDA balanced accuracy as the CART bands (blue) and the RF bands (yellow) are added in order of selection.");
H2("3.5 Tier 4 — QDA classification");
table(em(A.errmat[A.cart_name]), `Error matrix of QDA (equal priors, 10-fold CV) on the ${A.cart_name} bands (as Table 2 of Das et al., 2020).`, [3, 2, 2, 2, 2]);
table(A.tier4, "Tier 4 on each band set: QDA with equal and sample priors, and LDA (V1).", [2.4, 2.4, 1, 1, 1, 1, 1, 1], 16);
(T.qda || []).forEach((t) => P(t));
H2("3.6 Validation of the four-tier pipeline");
table(A.val_qda, "QDA on CART bands under the validation schemes (mean over repeats).", [3.4, 2, 1, 1, 1, 1, 1, 1], 16);
figure("F11_validation_qda_cart", "Balanced accuracy of QDA on the CART bands by validation scheme and prior.");
(T.validation || []).forEach((t) => P(t));
table(A.sens_range, "Sensitivity of the pipeline to the analysed band range.", [4, 1, 1.4, 1.4, 1.4]);
table(A.sens_dups, "Sensitivity to the four duplicate spectra of plot 27.", [4, 1, 1.4, 1.4, 1.4]);
H2("3.7 CART versus Random Forest (Part A1–A4)");
figure("F12_A1_rf_importance", "Balanced RF importance spectrum (MDI), the RF-17 peaks and the CART bands.");
table(Object.entries(A.sets).map(([k, v]) => [k, String(A.set_sizes[k]), v]).reduce((a, r) => (a.push(r), a), [["Band set", "Bands", "Wavelengths (nm)"]]), "Band sets selected by CART and RF.", [2, 1, 7]);
table(A.rf_checks, "Checks of the RF importance.", [5, 2, 1]);
(T.a2 || []).forEach((t) => P(t));
table(em(A.errmat[A.rf_name]), `Error matrix of QDA (equal priors, 10-fold CV) on the ${A.rf_name} bands.`, [3, 2, 2, 2, 2]);
figure("F13_A3_pipelines", "Balanced accuracy of CART and RF as classifiers and as band selectors for QDA, under V1, V3, V4 and V5.");
table(A.validation, "Validation of the four pipelines (mean over repeats).", [3, 1, 1, 1, 1, 1]);
table(A.wilcoxon, "Paired Wilcoxon tests on identical folds (positive = first pipeline better).", [4, 2, 1.5, 1, 1, 1.4], 16);
(T.a3 || []).forEach((t) => P(t));
figure("F14_A4_stability", "Re-selection of the CART and RF bands in the 50 nested training sets.");
table(A.stability, "Stability of band selection.", [1.2, 1.2, 1.6, 2, 1.6, 2]);
(T.a4 || []).forEach((t) => P(t));
H2("3.8 Disease-sensitive features (Part K)");
H3("K0 — denoising and detector joins");
figure("F15_K0_detector_joins", "(a) Step at the 1000/1001 nm detector join before and after splice correction; (b) the 1800/1801 nm join by date (grey = guard zone).");
P(`Smoothing preserved the signal (r ≥ ${K.k0.corr.toFixed(5)} between raw and smoothed class means; ${K.k0.sig_raw} vs ${K.k0.sig_s} significant bands). A start-up rise after 1801 nm was ${K.k0.bump ? "present and date-dependent, so the guard zones were applied" : "not detected; guard zones were applied as a precaution"}.`);
H3("K1 — band reflectance");
P(`${K.k1.auc70} bands reached AUC ≥ 0.70; the most sensitive band was ${K.k1.best_wl.toFixed(0)} nm (AUC ${K.k1.best_auc.toFixed(3)}).`);
figure("F16_K1_K4_band_auc", "AUC of every band for reflectance (K1) and the first derivative (K4); grey = guard zones.");
table(K.k1_regions, "Most sensitive band per region with its threshold-classifier accuracy on new plots.", [2, 1.2, 1, 1.2, 1, 1.5, 1.5]);
H3("K2 — continuum-removed absorption features");
figure("F17_K2_continuum", "Mean continuum-removed curves of healthy and diseased leaves in the six absorption windows.");
table(K.k2, "Continuum-removed parameters ranked by AUC (top 8).", [3, 1.2, 1.2, 1, 1, 1.4, 1.4]);
H3("K3 — spectral indices and the optimised index");
figure("F18_K3_indices", "The 31 vegetation indices ranked by AUC.", 430);
table(K.k3, "The ten most sensitive indices.", [2, 1.4, 1.4, 1, 1, 1.4, 1.4]);
figure("F19_K3b_ndsi_heatmap", "AUC of the normalised difference of every band pair (5 nm grid).", 450);
table(K.k3b_refined, "Refined best two-band indices (pair found on all leaves).", [2, 1.4, 1.4, 1, 1, 1.4, 1.4]);
P(`When the pair search was repeated inside the training sets, the honest balanced accuracy was ${pct(K.k3b_honest.NDSI["BA CV"])} (CV) and ${pct(K.k3b_honest.NDSI["BA hold-out"])} (hold-out) for NDSI and ${pct(K.k3b_honest.DI["BA CV"])} / ${pct(K.k3b_honest.DI["BA hold-out"])} for DI.`);
(T.k3b || []).forEach((t) => P(t));
table(K.k3b_jf_refined, "Refined best join-free two-band indices (pairs straddling a detector join excluded).", [2, 1.4, 1.4, 1, 1, 1.4, 1.4]);
P(`Join-free search repeated inside the training sets: NDSI ${pct(K.k3b_jf_honest.NDSI["BA CV"])} (CV) / ${pct(K.k3b_jf_honest.NDSI["BA hold-out"])} (hold-out); DI ${pct(K.k3b_jf_honest.DI["BA CV"])} / ${pct(K.k3b_jf_honest.DI["BA hold-out"])}.`);
H3("K4 — first-derivative spectra, edge parameters and REIP");
figure("F20_K4_first_derivative", "Mean first-derivative spectra of healthy and diseased leaves; right: the red edge.");
table(K.k4_summary, "Band-wise derivative sensitivity.", [3, 1.4, 1.4, 1, 2.4]);
table(K.k4_edge, "Edge parameters ranked by AUC (top 8).", [3, 1.2, 1.2, 1, 1, 1.4, 1.4]);
figure("F21_K4_REIP", "Red-edge inflection point by four methods (left) and by date (right).");
table(K.reip, "REIP of healthy and diseased leaves by four methods.", [3, 1.2, 1.2, 1, 1, 1.4, 1.4]);
(T.reip || []).forEach((t) => P(t));
H3("K6 — correlation spectra");
figure("F22_K6_correlation", "Point-biserial correlation between band value and disease status for reflectance and first derivative; thin lines: single dates.");
table(K.corr_regions, "Band of maximum |r| per region.", [1.5, 1.4, 1.3, 1, 1.4]);
H3("K5 — CART versus Random Forest on each feature group");
figure("F23_K5_cart_vs_rf", "Balanced accuracy of CART and RF on each feature group (V3 and V4).");
table(K.k5, "CART and RF on each feature group (balanced accuracy, mean over repeats).", [4, 1, 1, 1, 1, 1]);
table(K.k5_wilcoxon, "Paired comparison RF − CART on identical folds.", [4, 2, 1.4, 1, 1, 1.2], 16);
table(K.k5_share, "Share of RF importance by feature type (combined pool, all leaves).", [3, 1, 1.5, 2]);
(T.k5 || []).forEach((t) => P(t));
H2("3.9 Four-tier analysis of the combined feature pool (Part C)");
table(CC.composition, "Combined pool: features by type, Tier-1 significant and selected by CART and RF.", null, 16);
P(`Of ${CC.n_features} features, ${CC.n_sig} passed Tier 1. CART selected ${CC.set_sizes[CC.cart_name]} features (${CC.sets[CC.cart_name]}); RF-17 comprised ${CC.sets[CC.rf_name]}.`);
figure("F26_C_cart_tree", "CART tree on the combined feature pool.", 620);
figure("F25_C_top_importance", "The 30 most important features of the combined pool (Balanced RF), coloured by type.", 470);
table(CC.tier3, "J–M distance for the feature sets selected from the combined pool.", [4, 2, 2]);
table(em(CC.errmat[CC.rf_name]), `Error matrix of QDA (equal priors, 10-fold CV) on ${CC.rf_name} of the combined pool.`, [3, 2, 2, 2, 2]);
figure("F28_C_pipelines", "Four pipelines on the combined pool under V1, V3, V4 and V5.");
table(CC.validation, "Validation of the combined-pool pipelines.", [3, 1, 1, 1, 1, 1]);
table(X.cross, "Combined pool vs reflectance only vs K5: paired Wilcoxon tests on identical folds.", [3, 3, 1.6, 1.2, 0.9, 0.9, 1.1], 15);
(T.c5 || []).concat(T.c7 || []).forEach((t) => P(t));
H2("3.10 Additional checks");
figure("F30_V5_leave_one_date_out", "V5: balanced accuracy on each held-out date in held-out plots.");
table(X.lodo, "Balanced accuracy by held-out date (V5).", [4, 1.5, 1.5, 1.5, 1.5]);
(T.v5 || []).forEach((t) => P(t));
table(X.strata_range, "AUC of the key features on all leaves and its range within dates, growth stages and varieties.", [3.5, 1.3, 1.6, 1.6, 1.6]);
(T.strata || []).forEach((t) => P(t));
H2("3.11 Synthesis");
figure("F29_synthesis", "All approaches ranked by balanced accuracy on new plots (V3 and V4).");
table(X.synthesis, "All approaches side by side.", [5, 1.3, 1.3, 1.3], 15);

// ============================================================ 4 discussion, 5 conclusions
pageBreak();
H1("4. Discussion");
(T.discussion || []).forEach((d) => { if (d.h) H2(d.h); (d.p || []).forEach((t) => P(t)); });
H1("5. Conclusions");
(T.conclusions || []).forEach((t, i) => P(`${i + 1}. ${t}`));
H2("Recommendations");
B(T.recommendations || []);
H1("6. Quality control: cross-checks");
P(`${J.checks.n} cross-checks were run: ${J.checks.pass} PASS, ${J.checks.flag} FLAG (limitations that are reported and handled) and ${J.checks.fail} FAIL. The full register with methods is in workbook sheet 33_CrossChecks.`);
table(J.checks.table.map((r) => [r[0], r[1], r[2], r[3], r[4]]), "Cross-check register.", [0.5, 1.4, 3, 4, 0.9], 14);
H1("References");
(T.references || []).forEach((r) => body.push(new Paragraph({ children: runs(r, { size: 20 }), spacing: { after: 80 }, indent: { left: 400, hanging: 400 } })));

const doc = new Document({
  creator: "Animesh Panda", title: "White rust spectral discrimination — methods and results",
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, font: "Cambria", color: "1F3D2B" }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, font: "Cambria", color: "1F3D2B" }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, italics: true, font: "Cambria", color: "1F3D2B" }, paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
               footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "8A8981" })] })] }) },
               children: body }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log("docx written", OUT, figNo, "figures", tabNo, "tables"); });
