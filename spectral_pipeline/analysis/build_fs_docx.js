// Thesis-style Word report on the feature-selection comparison (Part FS)
// usage: DOCX_MODULE=<docx> node build_fs_docx.js <work dir> <out.docx>
const fs = require("fs");
const path = require("path");
const docx = require(process.env.DOCX_MODULE || "docx");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType, ImageRun,
        AlignmentType, LevelFormat, PageBreak, TableOfContents, Footer, PageNumber, BorderStyle } = docx;

const WORK = process.argv[2];
const OUT = process.argv[3];
const J = JSON.parse(fs.readFileSync(path.join(WORK, "fs_results.json"), "utf8"));
const MT = JSON.parse(fs.readFileSync(path.join(__dirname, "fs_method_text.json"), "utf8"));
const T = J.txt || {};
const FIG = (n) => path.join(J.fig, n + ".png");
const CW = 9638;
const pct = (v) => (v == null ? "–" : (100 * v).toFixed(1) + " %");
const body = [];
let figNo = 0, tabNo = 0;

function runs(text, opts = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*)/g;   // bold only: feature names contain underscores (D1_848)
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), size: opts.size || 22 }));
    const t = m[0];
    out.push(t.startsWith("**") ? new TextRun({ text: t.slice(2, -2), bold: true, size: opts.size || 22 })
                                : new TextRun({ text: t.slice(1, -1), italics: true, size: opts.size || 22 }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), size: opts.size || 22 }));
  return out;
}
const P = (text, o = {}) => body.push(new Paragraph({ children: runs(text, o), spacing: { after: 120, line: 300 }, alignment: o.align || AlignmentType.JUSTIFIED }));
const H1 = (t) => body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] }));
const H2 = (t) => body.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] }));
const H3 = (t) => body.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] }));
const B = (items) => (items || []).forEach((t) => body.push(new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(t), spacing: { after: 60 } })));
const EQ = (t) => body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 120 }, children: [new TextRun({ text: t, font: "Cambria Math", size: 22 })] }));
const KV = (label, text) => body.push(new Paragraph({ spacing: { after: 80, line: 290 }, alignment: AlignmentType.JUSTIFIED,
  children: [new TextRun({ text: label + ": ", bold: true, size: 22 })].concat(runs(text)) }));
const pageBreak = () => body.push(new Paragraph({ children: [new PageBreak()] }));
function pngSize(f) { const b = fs.readFileSync(f); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }
function figure(name, caption, widthPx = 610) {
  const f = FIG(name);
  if (!fs.existsSync(f)) return;
  const d = pngSize(f);
  const w = Math.min(widthPx, 620), h = Math.round(d.h * w / d.w);
  figNo += 1;
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, keepNext: true,
    children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width: w, height: h }, altText: { title: name, description: caption, name } })] }));
  body.push(new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: `Figure ${figNo}. `, bold: true, size: 20 }), new TextRun({ text: caption, size: 20, italics: true })] }));
}
function table(rows, caption, widths, fontSize = 18) {
  tabNo += 1;
  body.push(new Paragraph({ spacing: { before: 160, after: 80 }, keepNext: true,
    children: [new TextRun({ text: `Table ${tabNo}. `, bold: true, size: 20 }), new TextRun({ text: caption, size: 20 })] }));
  const n = rows[0].length;
  const ws = widths && widths.length === n ? widths : Array(n).fill(1);
  const tot = ws.reduce((a, b) => a + b, 0);
  const cw = ws.map((w) => Math.floor(w * CW / tot));
  const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBEB7" };
  body.push(new Table({
    width: { size: cw.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: cw,
    rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, cantSplit: true, children: r.map((c, j) => new TableCell({
      width: { size: cw[j], type: WidthType.DXA }, borders: { top: border, bottom: border, left: border, right: border },
      shading: i === 0 ? { type: ShadingType.CLEAR, color: "auto", fill: "1F3D2B" } : (i % 2 ? undefined : { type: ShadingType.CLEAR, color: "auto", fill: "F4F4F1" }),
      margins: { top: 40, bottom: 40, left: 70, right: 70 },
      children: [new Paragraph({ children: [new TextRun({ text: String(c), size: fontSize, bold: i === 0, color: i === 0 ? "FFFFFF" : "1B1B1A" })] })] })) })),
  }));
  body.push(new Paragraph({ spacing: { after: 160 }, children: [] }));
}

const FAMILIES = [["Filter", "filter"], ["Wrapper", "wrapper"], ["Embedded", "embedded"], ["Ensemble", "ensemble"]];
const methodsOf = (fam) => J.methods.filter((m) => m[1] === fam).map((m) => m[0]);
const D = J.detail;
const best = J.best[0];

// ===================================================================== title
body.push(new Paragraph({ spacing: { before: 2200, after: 240 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Selection of stable and informative disease-specific spectral features for white rust detection in mustard leaves", bold: true, size: 40, color: "1F3D2B" })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "A systematic comparison of filter, wrapper and embedded feature-selection methods on the combined K1–K4 feature pool", size: 26, italics: true })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: `${J.n} leaf spectra (${J.nH} healthy, ${J.nD} white-rust diseased) · ASD FieldSpec contact probe, 1-nm interval · four dates, three growth stages, three varieties pooled · ${J.p} spectral features`, size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: "Animesh Panda · Division of Agricultural Physics, ICAR-Indian Agricultural Research Institute, New Delhi", size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Methodology, results and interpretation for thesis use · companion to the feature-selection Excel workbook and presentation", size: 20, color: "52514E" })] }));
pageBreak();
body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Contents")] }));
body.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-3" }));
body.push(new Paragraph({ children: [new TextRun({ text: "(Right-click → Update field in Word to show page numbers.)", italics: true, size: 18, color: "52514E" })] }));
pageBreak();

// ===================================================================== summary
H1("Summary");
(T.summary || []).forEach((t) => P(t));
P(`The best method overall was **${best}**. The most stable method was ReliefF. The most universal disease-specific feature was the width of the 970-nm water absorption feature, chosen by 17 of 21 methods.`);
H2("Key findings");
B(T.key_messages);

// ===================================================================== 1 introduction
pageBreak();
H1("1. Introduction");
P("Hyperspectral leaf reflectance contains thousands of narrow, strongly correlated bands. When the bands are converted into disease-sensitive features — reflectance (K1), continuum-removed absorption parameters (K2), vegetation indices (K3), first-derivative bands and red-edge parameters (K4) — the number of candidate features (4150 here) far exceeds what a classifier needs. Too many features cause over-fitting, unstable covariance estimates in discriminant analysis, poor interpretability and expensive sensors (Guyon & Elisseeff 2003; Thomas et al. 2018).");
P("Feature selection keeps a small subset of the ORIGINAL features, so the result can be interpreted physiologically and used to design a multispectral sensor (Wei et al. 2021). Feature-selection methods fall into three families (Kohavi & John 1997; Saeys et al. 2007):");
B(["**Filter** methods score every feature with a statistic computed from the data alone, independent of any classifier (e.g. Pearson correlation, ANOVA F, chi-square, ReliefF, SPA, UVE). They are fast but judge features individually (or by simple redundancy rules).",
   "**Wrapper** methods search over feature subsets and score each subset with a classifier or a separability criterion (e.g. RFE, CARS, sequential floating forward selection, genetic algorithms). They find complementary features but are slower and can over-fit.",
   "**Embedded** methods select features as part of fitting a model (e.g. Random Forest and CART importance, Boruta, PLS-VIP, LASSO, gradient boosting). They are a compromise between the two."]);
P("Crop-disease studies have used many of these methods — chi-square and ANOVA-F (Abdulridha et al. 2023), RFE (Wei et al. 2021; Liu et al. 2024), RELIEF-F (Mahlein et al. 2013), SPA and CARS (Zhu et al. 2017; Li et al. 2009), continuous-wavelet separability scalograms (Cheng et al. 2010), Boruta with SFFS (Mustafa et al. 2022, 2023), genetic algorithms (Nagasubramanian et al. 2018) and the J–M-based four-tier approach (Das et al. 2020) — but usually one or two at a time, on different data and with different validation. Which method works best for a given dataset therefore remains an open question.");
H2("1.1 Objectives");
B(["Apply filter, wrapper and embedded feature-selection methods used in crop-disease research to the same K1–K4 feature pool of healthy and white-rust-diseased mustard leaves.",
   "Evaluate every method under one honest protocol: selection inside training plots only, accuracy on new plots, stability across training sets and separability (J–M).",
   "Identify which feature-selection method works best for this dataset, with statistical tests.",
   "Identify stable and informative disease-specific features on which the methods agree, and interpret them physiologically."]);

// ===================================================================== 2 methods
pageBreak();
H1("2. Materials and methods");
H2("2.1 Spectral data");
P(`Leaf reflectance was measured with an ASD FieldSpec spectroradiometer and contact probe at 1-nm intervals (350–2500 nm) on four dates (11-02, 24-02, 03-03 and 13-03-2026), covering vegetative, flowering and pod-formation stages and three varieties. After removing exact duplicate spectra, ${J.n} unique leaf spectra remained (${J.nH} healthy from 12 control plots, ${J.nD} diseased from 36 inoculated plots). The 400–2500 nm range (2101 bands at 1 nm) was analysed; the detector-edge noise below 400 nm was removed. The ASD's native resolution (≈ 3 nm VNIR, ≈ 8–10 nm SWIR) is interpolated to 1 nm, so adjacent 1-nm bands are strongly correlated.`);
H2("2.2 The K1–K4 feature pool");
P(`The pool was identical to the combined pool of the four-tier analysis (Part C): K1 band reflectance (2039 bands, Savitzky–Golay smoothed (11 points = 11 nm, 2nd order) after additive splice correction at the 1000/1001 and 1800/1801 nm detector joins, with guard zones 990–1010 and 1795–1835 nm removed); K2 continuum-removed absorption parameters (30: depth, position, area, width and symmetry of six absorption features: blue, red, 970, 1200, 1450 and 1940 nm); K3 vegetation indices (30 after removing MTVI1, which equals mCARI1); K4 first-derivative bands (2031, Savitzky–Golay 15 points, guard zones 988–1012 and 1793–1837 nm removed) and 20 red-edge and derivative edge parameters. Total ${J.p} features. For the wavelet method an additional feature space of ${J.n_cwt} continuous-wavelet coefficients was derived from the K1 spectrum (Section 2.5.11).`);
H2("2.3 Study design and validation");
figure("FS01_workflow", "Workflow of the feature-selection comparison.", 620);
B(["**Training/test units.** 20 units: the 10 plot-grouped folds of the first repeat of the nested cross-validation used throughout the thesis (StratifiedGroupKFold, seed 101) and 10 hold-out splits in which 30 % of the plots (4 healthy + 11 diseased) form the test set. No plot ever contributes leaves to both training and test sets.",
   "**Selection inside the training set only.** Every method was run on the training leaves of each unit; the test leaves were used only to measure accuracy. This avoids the selection bias that arises when features are chosen on all samples and then cross-validated (Ambroise & McLachlan 2002). Each method was also run once on all leaves to report the selected features.",
   "**Feature budget.** From each method's ranking the top k = 5, 10, 15 and 20 features were taken; k = 10 is used for the headline comparison. SFFS returns its own best set for each size.",
   "**Redundancy control.** Two variants were evaluated: the plain top-k (as most methods are published) and a redundancy-controlled top-k in which a candidate correlated |r| ≥ 0.95 (on the training leaves) with an already chosen feature is skipped — the correlation analogue of the minimum spectral distance of Wei et al. (2021).",
   "**Classifiers.** QDA with equal priors (Tier 4 of Das et al. 2020), LDA with equal priors and a Balanced Random Forest (300 trees; k = 10) were trained on the training leaves using the selected features and applied to the test leaves.",
   "**Class imbalance (1 : 5).** Equal priors (QDA, LDA), balanced class weights (CART, SVM, LASSO, gradient boosting), class-balanced bootstrap samples (Balanced RF, RF-RFE, Boruta), class-balanced Monte-Carlo sub-samples (CARS, MC-UVE) and class-balanced instance sampling (ReliefF); all accuracies are balanced accuracies.",
   "**Inner validation.** Methods that tune themselves (SPA chain length, CARS subset, PLS components, CART pruning, LASSO penalty, SFFS and GA criterion) used plot-grouped 3- or 5-fold cross-validation inside the training set."]);
H2("2.4 Notation");
P("n = number of training leaves, n₀/n₁ = healthy/diseased leaves, x̄_c and σ_c² = class mean and variance of a feature, p = number of features, S = selected subset, k = |S|.");

const famTitle = { Filter: "2.5 Filter methods", Wrapper: "2.6 Wrapper methods", Embedded: "2.7 Embedded methods", Ensemble: "2.8 Ensemble: consensus feature selection" };
const famIntro = {
  Filter: "Filter methods score features from the data alone. Eleven filters were applied; for each the principle, equation, settings, the way the ranking was formed and its use in crop-disease research are given.",
  Wrapper: "Wrapper methods evaluate feature subsets with a learning algorithm or a separability criterion and search the subset space. Six wrappers were applied. To keep the floating search and the genetic algorithm tractable, they searched a candidate pool of the 100 most significant, mutually non-redundant features of each training set (filter–wrapper hybrid).",
  Embedded: "Embedded methods obtain feature importance as a by-product of fitting a model. Six embedded methods were applied.",
  Ensemble: "Ensemble selection aggregates the rankings of several methods to obtain a more robust selection.",
};
let secN = { Filter: 5, Wrapper: 6, Embedded: 7, Ensemble: 8 };
FAMILIES.forEach(([fam]) => {
  H2(famTitle[fam]);
  P(famIntro[fam]);
  methodsOf(fam).forEach((m, i) => {
    const t = MT[m];
    H3(`2.${secN[fam]}.${i + 1} ${t.code} · ${m}`);
    KV("Principle", t.principle);
    if (t.equation) EQ(t.equation);
    KV("Settings", t.settings);
    KV("Output used", t.ranking);
    KV("Use in crop-disease studies", t.use);
  });
});

H2("2.9 Evaluation criteria");
H3("2.9.1 Accuracy on new plots");
P("Balanced accuracy (BA) — the mean of the recall of healthy and of diseased leaves — is insensitive to the 1 : 5 class imbalance. The area under the ROC curve of QDA's posterior probability was also recorded. Each value is the mean over the 20 test sets.");
EQ("BA = ½ [ TP/(TP + FN) + TN/(TN + FP) ]");
H3("2.9.2 Stability");
P("The 20 top-10 lists of a method were compared pair-wise (190 pairs). The Kuncheva (2007) consistency index corrects the overlap for chance; the Jaccard index is the share of shared features. Because neighbouring 1-nm bands carry the same information, a tolerant Jaccard index counted a feature of the same spectral series within ±10 nm as the same feature (headline stability measure).");
EQ("KI(A, B) = (r p − k²) / [k (p − k)],   Jaccard(A, B) = |A ∩ B| / |A ∪ B|");
H3("2.9.3 Separability");
P("The multivariate Jeffries–Matusita distance (0–2) of the top-10 set chosen on all leaves (Tier 3 of Das et al. 2020) was computed with the Gaussian Bhattacharyya distance; J–M ≥ 1.90 is the usual separability threshold. The QDA balanced accuracy of the same set in leaf-level 10-fold cross-validation (the protocol of Das et al.; optimistic because the set was chosen on all leaves) is also reported.");
EQ("B = ⅛ (μ₀ − μ₁)ᵀ Σ⁻¹ (μ₀ − μ₁) + ½ ln[ |Σ| / √(|Σ₀||Σ₁|) ],  Σ = (Σ₀ + Σ₁)/2,  J–M = 2(1 − e^(−B))");
H3("2.9.4 Statistical comparison of methods");
P("The QDA balanced accuracies of the 22 distinct methods (k = 10, redundancy-controlled) in the 20 units were compared with the Friedman test, followed by the Nemenyi critical difference of mean ranks (Demšar 2006). The best method was compared with every other method by paired Wilcoxon signed-rank tests with Holm correction.");
EQ("CD = q_α √[ K(K + 1) / (6N) ],  K = 22 methods, N = 20 units");
H3("2.9.5 Composite ranking");
P("Methods were ranked by four criteria — QDA balanced accuracy and RF balanced accuracy (k = 10, redundancy-controlled), stability (tolerant Jaccard) and J–M of the all-leaf set — and the mean of the four ranks gave the overall rank.");
H3("2.9.6 Consensus disease-specific features");
P("For each distinct method and each feature, the share of the 20 training sets in which the feature (±10 nm) was in the method's redundancy-controlled top-10 was computed. The consensus score is the mean of these shares over the 21 distinct methods (CWT excluded, as it uses another feature space); one representative was kept per ±10-nm region. A feature selected in ≥ 50 % of the training sets by many methods is both stable and informative.");
H3("2.9.7 Detector-join check");
P("The ASD detectors join at 1000/1001 and 1800/1801 nm. For each method, the share of top-10 selections within 10 nm of a guard zone was counted, and the accuracy was recomputed after excluding such bands from the ranking, to test whether a method exploits residual splice effects.");
H2("2.10 Software and quality control");
P("Python 3.13 with NumPy, SciPy, pandas, scikit-learn 1.9 (Pedregosa et al. 2011) and imbalanced-learn (Lemaître et al. 2017); ReliefF, SPA, MC-UVE, CARS, SFFS, the genetic algorithm, Boruta, PLS-VIP, the CWT and all evaluation statistics were implemented in a reusable module (sp/fs_methods.py). Implementation checks are listed in Section 6.");

// ===================================================================== 3 results
pageBreak();
H1("3. Results");
H2("3.1 Overview of all methods");
table(J.summary_table, "QDA balanced accuracy on new plots for 5–20 redundancy-controlled features, RF accuracy (k = 10), stability, J–M and overall rank of every method (mean of 20 held-out sets).",
      [2.4, 1.1, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.7, 0.9], 15);
figure("FS02_score_spectra", "Feature scores of the ranking methods along the wavelength (all leaves, scaled to each method's maximum). Grey bars: detector-join guard zones.", 600);
P("All univariate and importance-based scores peak in the same three regions: first-derivative bands across the NIR plateau (≈ 800–920 nm), first-derivative bands on the 1940-nm water band (≈ 1900–1950 nm) and, for the trees, 2200–2230 nm; among the scalar features the 970-nm water-band width and the 1940-nm water-band position and symmetry score highest. MC-UVE and PLS-VIP spread their weight more evenly and highlight the 1725–1750 and 2300 nm regions.");
figure("FS14_selected_positions", "Top-10 features selected by each method on all leaves (redundancy-controlled). Circles: K1 reflectance; triangles: K4 first derivative; squares: CWT features; scalar features (K2, K3, K4 edge) are listed on the right.", 620);

const famRes = { Filter: "3.2 Results of the filter methods", Wrapper: "3.3 Results of the wrapper methods", Embedded: "3.4 Results of the embedded methods", Ensemble: "3.5 Result of the consensus (ensemble) method" };
const resN = { Filter: 2, Wrapper: 3, Embedded: 4, Ensemble: 5 };
FAMILIES.forEach(([fam]) => {
  H2(famRes[fam]);
  methodsOf(fam).forEach((m, i) => {
    const d = D[m], t = MT[m];
    H3(`3.${resN[fam]}.${i + 1} ${t.code} · ${m}`);
    (t.result || []).forEach((x) => P(x));
    if (m === "Pearson r" || m === "Fisher score") return;
    const extra = [`J–M of the all-leaf top-10: ${d.jm == null ? "–" : d.jm.toFixed(3)}`,
                   `QDA (Das protocol, leaf 10-fold): ${pct(d.v1)}`,
                   `RF on top-10 (new plots): ${pct(d.rf10)}`,
                   `stability (Jaccard ±10 nm): ${d.jac == null ? "–" : d.jac.toFixed(2)}${d.ki == null ? "" : `; Kuncheva ${d.ki.toFixed(2)}`}`];
    if (d.native) extra.push(`own subset: ${d.native.mean.toFixed(0)} features (${d.native.min}–${d.native.max}); RF ${pct(d.native.rf)}${d.native.qda == null ? "" : `; QDA ${pct(d.native.qda)}`}`);
    if (d.edge) extra.push(`selections within 10 nm of a detector join: ${pct(d.edge.share)} (accuracy without them ${pct(d.edge.excl)})`);
    if (d.sec != null) extra.push(`computing time: ${d.sec.toFixed(1)} s per training set`);
    if (d.overall) extra.push(`overall rank: ${d.overall} of 22`);
    B(extra);
    table(d.k_rows, `${m}: accuracy on new plots for k = 5–20 redundancy-controlled features (mean of 20 held-out sets).`, [1.4, 1, 1, 1, 1], 17);
    if (d.top15 && d.top15.length > 1) table(d.top15, `${m}: top-ranked features on all leaves (before redundancy control).`, [0.6, 2.6, 2.2, 1.2], 16);
    if (m === "CWT scalogram") figure("FS03_cwt_scalogram", "Separability scalogram: J–M of every Mexican-hat wavelet coefficient (scale × wavelength); circles = top-10 selected on all leaves.", 600);
    if (m === "CARS") figure("FS13_cars", "CARS: number of variables retained in the 50 sampling runs (all leaves); dashed line = selected run.", 380);
    if (m === "SFFS (J–M)") figure("FS12_wrapper_search", "Wrapper searches on all leaves: SFFS criterion by subset size (QDA balanced accuracy; J–M) and best fitness of the genetic algorithm by generation.", 610);
  });
});

H2("3.6 Comparison of accuracy");
figure("FS05_accuracy_k10", "Balanced accuracy on new plots with 10 features per method: QDA with redundancy-controlled (coloured) and plain (open) top-10, and RF (diamonds). Dashed line: four-tier RF-17 set of Part C.", 520);
B(T.accuracy);
H2("3.7 Number of features");
figure("FS04_ba_vs_k", "QDA balanced accuracy against the number of features (redundancy-controlled); the three best methods of each family are coloured.", 620);
B(T.k);
H2("3.8 Effect of redundancy control");
figure("FS15_redundancy_control", "QDA balanced accuracy of the plain and the redundancy-controlled top-10 of each method.", 480);
table(J.guard, "Plain vs redundancy-controlled top-10 (QDA balanced accuracy, mean of 20 held-out sets).", [3, 1.5, 1.8, 1.3], 17);
B(T.redundancy);
H2("3.9 Stability of the selections");
figure("FS06_stability_vs_accuracy", "Stability (tolerant Jaccard of the 20 top-10 lists) against QDA balanced accuracy.", 560);
table(J.stability, "Stability of the top-10 selections over the 20 training sets.", [3, 1.3, 1.3, 1.3], 17);
B(T.stability);
H2("3.10 Statistical comparison");
figure("FS07_cd_diagram", "Critical-difference diagram: mean rank of the QDA balanced accuracy over the 20 held-out sets (1 = best); horizontal bars join methods whose difference is smaller than the Nemenyi critical difference.", 620);
table(J.mean_ranks, "Mean Friedman rank of the 22 distinct methods (QDA, k = 10, redundancy-controlled).", [3, 1.5], 17);
table(J.wilcoxon, `Paired Wilcoxon tests of the best method (${J.friedman.best}) against every other method, Holm-corrected.`, [2.6, 1.6, 1.1, 1.1, 0.7], 16);
B(T.tests);
H2("3.11 Composite ranking: which method works best?");
figure("FS10_composite_ranking", "Composite ranking: mean of the ranks for QDA accuracy, RF accuracy, stability and J–M (lower = better).", 520);
table(J.composite, "Composite ranking of the 22 distinct methods.", [0.4, 2.4, 1.1, 1, 1, 0.9, 0.7, 0.9], 16);
P(`SVM-RFE ranks first because it is among the three most accurate methods with QDA, the most accurate with RF and LDA, and moderately stable. SFFS (QDA) is the most accurate single method but ranks 11th because its selections change from one training set to the next (Jaccard 0.24).`);
H2("3.12 Comparison with the four-tier feature sets");
table(J.vs4, "Best feature-selection methods (top-10, QDA) against the four-tier CART-13 and RF-17 sets of Part C on the same 20 held-out sets (paired Wilcoxon tests).", [2.3, 1.6, 1.1, 1.1, 1, 0.8, 0.8], 16);
B(T.vs4);
H2("3.13 Detector-join check");
table(J.edge, "Share of top-10 selections within 10 nm of an ASD detector join and QDA accuracy without such bands (methods with at least one such selection).", [2.4, 1.3, 1.1, 1.4, 1, 0.8], 16);
B(T.edge);
H2("3.14 Subsets chosen by the methods' own rules");
table(J.native_tab, "Size and accuracy of the subsets chosen by each method's own stopping rule (mean over 20 training sets; QDA only when every subset has ≤ 30 features).", [2.4, 1.1, 1.2, 1.6, 1.1], 17);
P("Boruta, MC-UVE, PLS-VIP (VIP > 1) and LASSO keep about 100–1400 features: they identify relevant features but do not reduce the pool to a compact, interpretable set. SFFS and the GA end at about 16 features with 88.0 % and 88.5 % QDA balanced accuracy.");
H2("3.15 Computing cost");
figure("FS11_runtime", "Computing time per training set (≈ 2000 leaves × 4150 features, one CPU core; log scale).", 480);
table(J.runtime_tab, "Computing time of each method.", [2.6, 1.3, 1.6, 1.4], 17);
B(T.runtime);
H2("3.16 Stable and informative disease-specific features");
figure("FS08_selection_frequency", "Selection frequency of the 20 consensus features by method: share of the 20 training sets in which the feature (±10 nm) was in the method's top-10.", 620);
table(J.consensus_full, "Consensus disease-specific features (one per ±10-nm region), with their univariate AUC, effect size (Hedges g) and direction in diseased leaves.", [1.9, 1.7, 0.9, 0.9, 0.7, 0.8, 0.8, 2.4], 14);
B(T.consensus);
figure("FS09_consensus_on_spectrum", "Consensus features on the mean reflectance and first-derivative spectra of healthy and diseased leaves.", 600);
H3("Physiological interpretation");
B(T.interpretation);

// ===================================================================== 4 discussion
pageBreak();
H1("4. Discussion");
H2("4.1 Why wrapper methods performed best");
P("The white-rust signal is spread over several complementary regions — leaf water (970 and 1940 nm), internal leaf structure (NIR-plateau slope) and dry matter (C–H bands near 1730 and 2300 nm) — and within each region over many collinear 1-nm features. Univariate filters and importance rankings repeatedly pick the single strongest region (the NIR-plateau derivative), so even after redundancy control their ten features carry overlapping information (78–81 %). Wrappers (SFFS, SVM-RFE, CARS) and LASSO judge a feature by what it adds to the features already chosen, and therefore combine the water features with weakly discriminating but complementary bands (e.g. D1_1724, D1_2305, D1_454). This is why they reached 85–88 % with the same number of features, in line with Wei et al. (2021), who found RFE superior to chi-square for peanut stem rot.");
H2("4.2 Accuracy versus stability");
P("Accuracy and stability did not coincide. The search-based wrappers (SFFS, GA, CARS) produced different subsets in different training sets (Jaccard 0.22–0.34), whereas ReliefF, LASSO, RF importance and the univariate filters were more reproducible (0.60–0.84). In collinear spectra many subsets are almost equally good, so a wrapper's exact choice is partly arbitrary. For a thesis, the accurate wrapper sets should therefore be reported together with selection frequencies, and the physiological interpretation should rest on features that are both stable and informative (the consensus features), following the recommendation to report stability alongside accuracy (Kuncheva 2007; Nogueira et al. 2018).");
H2("4.3 J–M is a description, not a selection criterion");
P("The sets with the highest J–M distance — SFFS with a J–M criterion (1.80) and the univariate J–M filter (1.75) — were among the least accurate on new plots (70–73 %). The Bhattacharyya distance contains a covariance term that rewards differences in class spread; in pooled field data such differences arise partly from plots, dates and growth stages and do not transfer to new plots. J–M remains useful to describe the separability of a chosen set (Tier 3 of Das et al. 2020), but it should not be the objective of the selection for this dataset.");
H2("4.4 Redundancy in 1-nm data");
P("The ASD records 1-nm values interpolated from a native resolution of about 3–10 nm, so adjacent bands are nearly identical. Without a redundancy rule the top-10 of a univariate ranking contains several copies of the same signal; skipping features correlated |r| ≥ 0.95 raised the accuracy of chi-square, ReliefF, MC-UVE, ANOVA F, mutual information and RF importance by 2.9–6.1 points. Methods with built-in redundancy handling (SFFS, GA, SPA, CARS, LASSO) did not need it, while mRMR's quotient criterion over-penalised redundancy and replaced strong features by weak ones.");
H2("4.5 Screening versus selection");
P("Boruta, MC-UVE and PLS-VIP answer a different question from the other methods: which features carry ANY disease information (all-relevant). They confirmed 120–1400 features, and a Random Forest on these large subsets reached 84–86 %, but their top-10 lists were weak. They are best used as a first screening step followed by a wrapper for the final compact set — the two-stage Boruta → SFFS strategy of Mustafa et al. (2023).");
H2("4.6 Detector-join artefacts");
P("Linear selectors (SVM-RFE, LASSO, CARS) and ReliefF often selected first-derivative bands just outside the guard zones of the ASD detector joins (≈ 981 and 1791 nm). Removing them cost CARS 4.6 and LASSO 3.2 points but SVM-RFE only 1.5 and SFFS 1.1 points (not significant). Some of this information may be real — 981 nm lies on the shoulder of the 970-nm water band, which is the strongest disease feature — but residual splice effects cannot be excluded. Bands within 10 nm of a join should therefore be flagged or excluded when a sensor is designed.");
H2("4.7 Comparison with the four-tier method");
P("The best feature-selection methods improved on the CART-13 set of the four-tier analysis by 8.5–9.6 points and on its RF-17 set by 2.3–3.4 points on the same held-out plots (15 of 20 sets, p ≤ 0.019). The four-tier approach remains useful as an interpretable baseline, but the choice of Tier-2 selector matters: a wrapper that selects complementary features (SVM-RFE or SFFS) is a better Tier-2 than CART for this disease.");
H2("4.8 Limitations");
B(["One disease, one crop and one season; the ranking of methods may differ for other datasets — the pipeline can be rerun unchanged.",
   "Twenty training/test units (10 plot-grouped folds and 10 plot hold-outs); transfer to an unseen date, which was poor in the main analysis, was not repeated for every selector.",
   "SFFS and the GA searched a pre-filtered pool of 100 candidates; the LASSO penalty and the number of PLS components on all leaves ended at the limits of their search grids.",
   "XGBoost was represented by scikit-learn gradient boosting, and Boruta by an implementation with Balanced Random Forest importance; the CWT used a 5-nm grid of wavelet coefficients computed from the 1-nm spectrum.",
   "The reference cited as Liu et al. (2024) for RFE could not be verified and must be completed by the author."]);

// ===================================================================== 5 summary and conclusions
pageBreak();
H1("5. Summary and conclusions");
H2("5.1 Summary");
(T.summary || []).forEach((t) => P(t));
H2("5.2 Conclusions");
(T.conclusions || []).forEach((t, i) => P(`${i + 1}. ${t}`));
H2("5.3 Recommendations");
B(T.recommendations);
H2("5.4 Recommended feature-selection workflow for new datasets");
B(["Build the disease-sensitive feature pool (K1–K4) from 1-nm spectra with splice correction and guard zones.",
   "Use plot-grouped training/test splits; select features only inside training data.",
   "Screen with a stable filter or Boruta/MC-UVE (optional), then select a compact set with SVM-RFE (main method) and SFFS (QDA) or CARS (alternatives), always with redundancy control (|r| < 0.95) and join-adjacent bands flagged.",
   "Report balanced accuracy on new plots, stability (Jaccard ±10 nm or Kuncheva), J–M as a descriptor, and a Friedman–Nemenyi comparison.",
   "Interpret only features that are stable across training sets and agreed by several methods (consensus features)."]);

// ===================================================================== 6 QC
H1("6. Quality control");
table(J.checks, "Implementation checks.", [5, 3, 0.8], 16);

// ===================================================================== references
H1("References");
Object.keys(J.refs).map((k) => J.refs[k]).sort((a, b) => a.localeCompare(b))
  .forEach((r) => body.push(new Paragraph({ children: runs(r, { size: 20 }), spacing: { after: 80 }, indent: { left: 400, hanging: 400 } })));

const doc = new Document({
  creator: "Animesh Panda", title: "Feature selection for white rust detection — methods and results",
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, font: "Cambria", color: "1F3D2B" }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, font: "Cambria", color: "1F3D2B" }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, italics: true, font: "Cambria", color: "1F3D2B" }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
               footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "8A8981" })] })] }) },
               children: body }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log("docx written", OUT, figNo, "figures", tabNo, "tables"); });
