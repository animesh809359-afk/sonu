// Detailed Word report (thesis chapter) of the plot-average analysis: 192 plot-average spectra, all dates combined;
// four tiers on raw reflectance (CART and Random Forest), disease-sensitive features from raw reflectance, four tiers on the
// combined feature pool, disease-specific features. Input: results.json and figures/ of the work directory.
// usage: node build_pa_docx.js <work dir> <out.docx>
const fs = require("fs");
const path = require("path");
const docx = require(process.env.DOCX_MODULE || "docx");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType, ImageRun,
        AlignmentType, LevelFormat, PageBreak, TableOfContents, Footer, PageNumber, BorderStyle } = docx;

const WORK = process.argv[2];
const OUT = process.argv[3];
const J = JSON.parse(fs.readFileSync(path.join(WORK, "results.json"), "utf8"));
const FIGDIR = path.join(WORK, "figures");
const CW = 9638; // A4, 2 cm margins
const A = J.A, K = J.K, CC = J.C, X = J.X, PA = J.PA, T = J.txt || {};

const pct = (v) => (v == null ? "–" : (100 * v).toFixed(1) + " %");
const p1 = (v) => (v == null ? "–" : (100 * v).toFixed(1));
const num = (v, d = 3) => (v == null ? "–" : Number(v).toFixed(d));
const vA = (p, s) => A.v[`${p}|${s}`], vC = (p, s) => CC.v[`${p}|${s}`];
const DN = { D1: "first derivative", D2: "second derivative", D3: "third derivative" };
const featName = (n) => { const m = /^(D[123])_(\d+)$/.exec(n.trim()); if (m) return `${DN[m[1]]} at ${m[2]} nm`; const r = /^R(\d+)$/.exec(n.trim()); return r ? `reflectance at ${r[1]} nm` : n.trim(); };
const featList = (str) => str.split(",").map(featName).join(", ");
const PIPES = ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"];
const PN = { "CART classifier": "CART classifier", "RF classifier": "Random Forest classifier", "QDA on CART features": "QDA on CART-selected features", "QDA on RF features": "QDA on Random Forest-selected features" };
const SCH = [["V1", "Spectrum-level 10-fold cross-validation"], ["V3", "Nested plot-grouped cross-validation"], ["V4", "30 % plot hold-out validation"], ["V5", "Leave-one-date-out validation on new plots"]];

const body = [];
let figNo = 0, tabNo = 0;
function runs(text, opts = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|(?<![A-Za-z0-9])_[^_]+_(?![A-Za-z0-9]))/g;
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
const P = (text, opts = {}) => body.push(new Paragraph({ children: runs(text, opts), spacing: { after: 120, line: 300 }, alignment: opts.align || AlignmentType.JUSTIFIED }));
const NOTE = (text) => body.push(new Paragraph({ children: runs(text, { size: 18, italics: true }), spacing: { after: 140 } }));
const H1 = (t) => body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)], spacing: { before: 360, after: 160 } }));
const H2 = (t) => body.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)], spacing: { before: 240, after: 120 } }));
const H3 = (t) => body.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)], spacing: { before: 180, after: 80 } }));
const B = (items) => items.forEach((t) => body.push(new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(t), spacing: { after: 60 } })));
const EQ = (t) => body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 120 }, children: [new TextRun({ text: t, font: "Cambria Math", size: 22 })] }));
const pageBreak = () => body.push(new Paragraph({ children: [new PageBreak()] }));

function pngSize(file) { const b = fs.readFileSync(file); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }
function figure(file, caption, widthPx = 610) {
  const f = path.join(FIGDIR, file);
  if (!fs.existsSync(f)) { console.warn("missing", file); return null; }
  const d = pngSize(f);
  const w = Math.min(widthPx, 620);
  let h = Math.round(d.h * w / d.w);
  let ww = w;
  if (h > 760) { ww = Math.round(w * 760 / h); h = 760; }
  figNo += 1;
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, keepNext: true,
    children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width: ww, height: h }, altText: { title: file, description: caption, name: file } })] }));
  body.push(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 200 },
    children: [new TextRun({ text: `Figure ${figNo}. `, bold: true, size: 20 }), new TextRun({ text: caption, size: 20, italics: true })] }));
  return figNo;
}
function table(rows, caption, widths, fontSize = 17) {
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
      margins: { top: 30, bottom: 30, left: 60, right: 60 },
      children: [new Paragraph({ children: [new TextRun({ text: String(c), size: fontSize, bold: i === 0, color: i === 0 ? "FFFFFF" : "1B1B1A" })] })] })) })),
  }));
  body.push(new Paragraph({ spacing: { after: 160 }, children: [] }));
  return tabNo;
}
const em = (m) => [["Classified \\ Reference", "Healthy", "Diseased", "Row total", "User's accuracy"],
  ["Healthy", m.HH, m.DH, m.HH + m.DH, pct(m.HH / (m.HH + m.DH))], ["Diseased", m.HD, m.DD, m.HD + m.DD, pct(m.DD / (m.HD + m.DD))],
  ["Column total", m.HH + m.HD, m.DH + m.DD, m.N, ""], ["Producer's accuracy", pct(m.PA_H), pct(m.PA_D), "", ""],
  ["Overall accuracy", pct(m.OA), "Balanced accuracy", pct(m.BA), `κ = ${num(m.kappa)}`]].map((r) => r.map(String));
const valTab = (blk, f, cap) => table([["Pipeline", ...SCH.map((s) => s[1])],
  ...PIPES.map((p) => [PN[p], ...SCH.map((s) => pct(f(p, s[0]).BA) + (s[0] === "V3" || s[0] === "V4" ? (f(p, s[0]).SD != null ? ` ± ${p1(f(p, s[0]).SD)}` : "") : ""))])],
  cap, [2.6, 1.5, 1.6, 1.5, 1.6]);
const t1 = (name) => J.tier1_sig_by_test[Object.keys(J.tier1_sig_by_test).find((k) => k.startsWith(name))];
const jmA = (s) => num(A.jm[s]), jmC = (s) => num(CC.jm[s]);
const cartA = A.cart_name, rfA = A.rf_name, cartC = CC.cart_name, rfC = CC.rf_name;
const vq = (scheme, pri) => A.val_qda.find((r) => r[0].startsWith(scheme) && r[1].startsWith(pri));
const k5 = (g, col) => { const r = K.k5.find((q) => q[0].startsWith(g)); return r ? r[col] : "–"; };
const DS = J.DS.rows;

// ================================================================ title page
body.push(new Paragraph({ spacing: { before: 2000, after: 240 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Discrimination of healthy and white-rust-diseased mustard from plot-average leaf spectra", bold: true, size: 40, color: "1F3D2B" })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "Four-tier hierarchical analysis (Das et al., 2020) with imbalance correction on raw reflectance and on the combined pool of disease-sensitive features derived from raw reflectance; CART versus Random Forest; validation on new plots and new dates — all dates, growth stages and varieties combined", size: 26, italics: true })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: `${J.n} plot-average spectra (${J.nH} healthy, ${J.nD} diseased) = 48 plots × 4 dates · ${PA.n_leaf} leaf spectra · ASD FieldSpec contact probe, 400–2500 nm`, size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: "Animesh Panda · Division of Agricultural Physics, ICAR-Indian Agricultural Research Institute, New Delhi", size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Methods, results and interpretation · companion to the Excel workbook and the presentation (WhiteRust_PlotAverage_AllDates)", size: 20, color: "52514E" })] }));
pageBreak();
body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Contents")] }));
body.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }));
body.push(new Paragraph({ children: [new TextRun({ text: "(Right-click → Update field in Word to refresh the page numbers.)", italics: true, size: 18, color: "52514E" })] }));
pageBreak();

// ================================================================ abstract
H1("Abstract");
P(`White rust (_Albugo candida_) is a major disease of Indian mustard. To identify the wavelengths and spectral features that separate healthy from white-rust-diseased plants, leaf reflectance spectra (350–2500 nm, ASD FieldSpec contact probe) measured on four dates (11-02, 24-02, 03-03 and 13-03-2026) were averaged per plot and date, giving ${J.n} plot-average spectra (${J.nH} healthy, ${J.nD} diseased; 48 plots × 4 dates). The four-tier hierarchical method of Das et al. (2020) — statistical screening, CART band selection, Jeffries–Matusita (J–M) separability and quadratic discriminant analysis (QDA) — was applied first to the raw reflectance (2101 bands) and repeated with a Balanced Random Forest as the band selector. The 1 : 3 imbalance between healthy and diseased spectra was corrected throughout (equal priors in CART and QDA, balanced bootstrap samples, balanced subsets, balanced accuracy). Disease-sensitive features were then derived from the raw reflectance — continuum-removal parameters, ${J.vi_table.length - 1} vegetation indices, first-, second- and third-derivative spectra and red-edge parameters — and the four tiers were applied to the combined pool of ${CC.n_features} features.`);
P(`On raw reflectance, ${A.n_sig} of 2101 bands differed significantly (Welch's t-test with false-discovery-rate control); the strongest differences were in the red (600–679 nm), at the red edge and in the short-wave infrared beyond 1350 nm. CART selected ${A.set_sizes[cartA]} bands (root ${A.sets[cartA].split(",")[0]} nm) with J–M = ${jmA(cartA)}, whereas the 17 Random Forest importance peaks reached J–M = ${jmA(rfA)}, above the separability threshold of 1.94. QDA with equal priors classified new plots (nested plot-grouped cross-validation) with a balanced accuracy of ${pct(vA("QDA on CART features", "V3").BA)} on the CART bands and ${pct(vA("QDA on RF features", "V3").BA)} on the Random Forest bands. The combined feature pool was dominated by derivative features: the first derivative at 871 nm was the single most discriminating feature (AUC ${DS[1][6]}), and a Random Forest on the pool reached ${pct(vC("RF classifier", "V3").BA)} on new plots (${pct(vC("RF classifier", "V4").BA)} on a 30 % plot hold-out). Transfer to an unseen date was weak (${pct(vC("RF classifier", "V5").BA)}). The disease-specific features of white rust at plot level are the slope of the near-infrared shoulder (first derivative 820–895 nm), the curvature of the red edge (second and third derivative at 682 and 737–741 nm) and derivative features of the water-absorption regions (around 1240 and 1918 nm).`);
P("**Keywords:** white rust; _Albugo candida_; Indian mustard; hyperspectral reflectance; plot average; CART; Random Forest; Jeffries–Matusita distance; quadratic discriminant analysis; class imbalance; derivative spectra; continuum removal; red-edge position.");

// ================================================================ 1 introduction
pageBreak();
H1("1. Introduction");
P("White rust, caused by the oomycete _Albugo candida_, infects leaves, stems and inflorescences of rapeseed-mustard. On leaves it produces chlorotic spots on the upper surface and white to cream pustules (sori) on the lower surface; systemic infection deforms the inflorescence ('stag head'). Yield losses of 20–60 % have been reported in India (Saharan et al., 2014). Early, objective detection of infected plants is therefore of practical value for disease forecasting and plant protection.");
P("Leaf reflectance is shaped by pigments in the visible region (chlorophylls absorb near 430–450 and 640–680 nm, carotenoids near 450–500 nm), by leaf internal structure in the near infrared (multiple scattering at cell wall–air interfaces of the mesophyll gives the high NIR plateau) and by leaf water and dry matter in the short-wave infrared (absorption near 970, 1200, 1450 and 1940 nm). White rust alters all three: chlorosis lowers chlorophyll absorption and raises visible reflectance, pustules disrupt the epidermis and mesophyll and change NIR scattering, and infected tissue loses water. Hyperspectral reflectance should therefore contain a disease signal at several wavelengths (Mahlein et al., 2013; Mahlein, 2016).");
P("Das et al. (2020) proposed a four-tier hierarchical procedure to identify the most informative wavelengths for discriminating classes from field spectra: (1) statistical screening of every band, (2) band selection with classification and regression trees (CART), (3) separability of the classes on the selected bands with the Jeffries–Matusita distance and (4) classification with quadratic discriminant analysis. This study applies that procedure to healthy versus white-rust-diseased mustard with the following extensions:");
B(["The analysis unit is the **plot-average spectrum**: the leaf spectra of a plot on a date are averaged, so each plot contributes one spectrum per date. All four dates, three growth stages and three varieties are combined.",
   "The 1 : 3 **class imbalance** (48 healthy vs 144 diseased spectra) is corrected at every tier, following the correction used in the flowering-stage workbook.",
   "**Random Forest** is used as an alternative band selector and classifier in Tier 2 and compared with CART.",
   "Accuracy is **validated** on new plots (plot-grouped and nested cross-validation, plot hold-out) and on a new date, in addition to the leaf/spectrum-level cross-validation of the original protocol.",
   "**Disease-sensitive features** derived from the raw reflectance (continuum removal, vegetation indices, first- to third-order derivatives, red-edge parameters) are added, and the four tiers are applied to the combined pool to find the **disease-specific features**."]);
P("The objectives were (i) to identify the wavelengths that separate healthy and diseased plots, (ii) to quantify their separability and classification accuracy on new plots and dates, (iii) to compare CART and Random Forest, and (iv) to identify the disease-specific spectral features of white rust at plot level.");

// ================================================================ 2 methods
pageBreak();
H1("2. Materials and methods");
H2("2.1 Experiment and spectral measurements");
P("Mustard was grown in 48 plots: plots 1–12 healthy (protected) and plots 13–48 infected with white rust, three varieties (V1, V2, V3). Leaf reflectance was measured with an ASD FieldSpec spectroradiometer and contact probe (350–2500 nm, 1-nm output) on 11-02-2026 and 24-02-2026 (plots at the vegetative and flowering stages) and on 03-03-2026 and 13-03-2026 (plots at the flowering and pod-formation stages); on each date several leaves of each plot (leaf levels L3, L5 and the lowest leaf) were measured. The data were exported to four labelled workbooks, one per date, with one column per leaf spectrum and the plot number, variety, growth stage and healthy/diseased label in the header rows.");
H2("2.2 Data cleaning and plot averaging");
P(`Exact duplicate spectra were removed before averaging: a second data block on 13-03-2026 (75 columns) repeats spectra of plots 13, 34, 38, 41 and 42, and four unnamed columns of plot 27 on 11-02-2026 are copies of Mustard00215–00218. This left ${PA.n_leaf} unique leaf spectra. The spectra of each plot on each date were then averaged band by band:`);
EQ("R̄_plot,date(λ) = (1/n) Σᵢ Rᵢ(λ),   i = 1 … n leaf spectra of the plot on that date");
P(`This gives ${J.n} plot-average spectra (48 plots × 4 dates; ${J.nH} healthy, ${J.nD} diseased). Averaging reduces leaf-to-leaf variation and random instrument noise (by about √n) and makes the plot — the experimental unit to which the disease treatment applies — the unit of analysis. As a cross-check, the labelled workbooks contain their own plot-average (=AVERAGE) columns; ${PA.n_ok} of ${PA.n_cols} of them are identical to the averages computed here at all 2151 bands (Table 1).`);
table(PA.leaf_tab, "Leaf spectra averaged into each plot-average spectrum, by date and class.", [1.3, 1, 1.1, 1.1, 1.3, 1.3]);
H2("2.3 Spectral range and pre-processing");
P("The 350–399 nm detector edge was removed because its noise is about 100 times that of the 500–699 nm region; 2101 bands (400–2500 nm) were analysed. The water-absorption bands were kept: the contact probe illuminates the leaf with its own lamp at a few millimetres, so there is no atmospheric water vapour in the light path, and these bands carry leaf-water information (Das et al. removed them because they worked with canopy field spectra). As requested, all analyses use the **raw** plot-average reflectance — no smoothing and no detector-join (splice) correction. The ASD records with three detectors (350–1000, 1001–1800, 1801–2500 nm); the small steps at the detector joins are instrument artefacts, so the bands beside the joins (990–1010 and 1795–1835 nm, the 'guard zones') were excluded from the reflectance and derivative feature sets of the disease-sensitive feature step.");
H2("2.4 The four-tier method (Das et al., 2020) with corrections");
H3("Tier 1 — statistical screening");
P("With two classes the one-way ANOVA used by Das et al. reduces to a two-sample comparison. Because the class variances differed at many bands (Levene's test), Welch's unequal-variance t-test was used at every band:");
EQ("t = (x̄_D − x̄_H) / √(s²_D/n_D + s²_H/n_H)");
P("The 2101 p-values were adjusted with the Benjamini–Hochberg false-discovery rate (q < 0.05); without adjustment about 105 bands would be significant by chance. The one-way ANOVA of Das et al. is reported for comparison. Two corrections were added: (a) **pseudo-replication** — the same plot is measured on four dates, so a linear mixed model with a random plot intercept (R nlme) was fitted at every band; (b) **class imbalance** — the test was repeated on 1000 balanced random subsets of 48 healthy and 48 diseased spectra. The −log₁₀(p) of every band was plotted against wavelength.");
H3("Tier 2 — band selection by CART and by Random Forest");
P("CART (R rpart; Gini splitting, minsplit 20, minbucket 7, complexity parameter 0.01) was grown on the Tier-1 bands with **prior = (0.5, 0.5)**, so that the 48 healthy spectra weigh as much as the 144 diseased spectra. The bands used as split variables form the CART band set. The 1-SE tree (complexity parameter by plot-grouped cross-validation) is reported as a smaller alternative.");
P("**Random Forest** (Breiman, 2001) was used as the alternative selector: a Balanced Random Forest (Chen et al., 2004) in which every tree is grown on a bootstrap sample with equal numbers of healthy and diseased spectra (1000 trees, √p candidate bands per split). Band importance is the mean decrease in Gini impurity; the 17 highest importance peaks at least 10 nm apart form the Random Forest band set (RF-17).");
H3("Tier 3 — Jeffries–Matusita distance");
P("The separability of the classes on a band set is measured by the Jeffries–Matusita distance (Swain and Davis, 1978; Richards, 2013), computed from the class mean vectors μ and covariance matrices Σ of all selected bands together (one value per band set, not per band):");
EQ("α = ⅛ (μ_H − μ_D)ᵀ [(Σ_H + Σ_D)/2]⁻¹ (μ_H − μ_D) + ½ ln{ |(Σ_H + Σ_D)/2| / √(|Σ_H| |Σ_D|) },    J–M = 2 (1 − e^(−α))");
P("J–M ranges from 0 (identical distributions) to 2 (complete separation). Classes are considered separable at J–M ≥ 1.90; Das et al. used 1.94.");
H3("Tier 4 — quadratic discriminant analysis");
P("QDA assigns a spectrum to the class with the larger discriminant score δ_k(x) = −½ ln|Σ_k| − ½ (x − μ_k)ᵀ Σ_k⁻¹ (x − μ_k) + ln π_k. **Equal prior probabilities** (π_H = π_D = 0.5) were used, because the sample priors (0.25 / 0.75) push the decision towards 'diseased'. Results are reported as error matrices (rows = classified, columns = reference, as Table 2 of Das et al.) with producer's and user's accuracy, overall accuracy (OA), Cohen's κ and the **balanced accuracy**:");
EQ("BA = ½ (recall_healthy + recall_diseased)");
P("Balanced accuracy is the headline metric: with 75 % diseased spectra, a classifier that calls everything diseased has OA = 75 % but BA = 50 %.");
H2("2.5 Validation");
B(["**Spectrum-level 10-fold cross-validation** — features chosen once on all 192 spectra; spectra split at random into 10 folds (the protocol of Das et al.). Optimistic, because the same plot on other dates is in training and test, and features are chosen on the test spectra.",
   "**Plot-grouped cross-validation** — features fixed, folds formed from whole plots (all four dates of a plot in the same fold).",
   "**Nested plot-grouped cross-validation** — Tier 1, feature selection and classifier refitted inside every training set; 10 plot-grouped folds × 5 repeats = 50 training sets, every test fold containing both classes. The honest estimate of the accuracy on new plots (Varma and Simon, 2006).",
   "**30 % plot hold-out validation** — 4 healthy and 11 diseased plots (all their dates) held out, everything refitted on the remaining plots; 10 random splits.",
   "**Leave-one-date-out validation on new plots** — train on three dates (training plots of a hold-out split), test on the fourth date (test plots); 10 splits × 4 dates = 40 units. Nothing of the test set — spectrum, plot or date — is seen in training.",
   "**Random under-sampling** — as nested cross-validation, but the diseased spectra are randomly under-sampled to the number of healthy spectra in every training set, as an alternative imbalance correction."]);
P("Pipelines were compared on identical folds with paired Wilcoxon signed-rank tests. The stability of the selected bands across the 50 training sets was measured with the Jaccard index (bands within ± 10 nm counted as the same).");
H2("2.6 Disease-sensitive features derived from raw reflectance");
B(["**Band reflectance** — raw reflectance at each band (guard zones excluded): Welch t + FDR, Hedges' g, AUC and a threshold classifier validated on plots.",
   "**Continuum removal** (Clark and Roush, 1984; Kokaly and Clark, 1999) — in six absorption windows (blue 400–548, red 548–765, water 914–1069, 1069–1258, 1258–1721 and 1721–2304 nm) the reflectance is divided by its upper convex hull; from the band depth BD = 1 − R/R_hull eight parameters are taken: maximum depth, position, area, width (full width at half depth), symmetry, left area, right area and depth/area.",
   `**Vegetation indices** — ${J.vi_table.length - 1} indices: the 31 indices of the Activity 1.4 table (flowering-stage workbook) and further pigment, red-edge, water, dry-matter and disease indices (e.g. the Healthy Index, Cercospora, rust and powdery-mildew indices of Mahlein et al., 2013; the Disease–Water Stress Index of Apan et al., 2004), each with its reference (Appendix B). An optimised two-band index NDSI = (R_λ1 − R_λ2)/(R_λ1 + R_λ2) was searched over all band pairs (Thenkabail et al., 2000), with the search repeated inside training plots to measure its optimism.`,
   "**Derivative spectra** (Tsai and Philpot, 1998) — first, second and third derivatives of the raw reflectance by central finite differences on the 1-nm grid: D1(λ) = [R(λ+1) − R(λ−1)]/2; D2(λ) = R(λ+1) − 2R(λ) + R(λ−1); D3(λ) = [R(λ+2) − 2R(λ+1) + 2R(λ−1) − R(λ−2)]/2. Derivatives remove additive brightness offsets (D1) and linear trends (D2) and sharpen overlapping absorption features.",
   "**Red-edge parameters** — the red-edge inflection point (REIP) by four methods (maximum first derivative, Horler et al., 1983; linear four-point interpolation, Guyot and Baret, 1988; Lagrangian interpolation, Dawson and Curran, 1998; linear extrapolation, Cho and Skidmore, 2006), amplitudes, positions and areas of the blue, yellow and red edges, green peak and red well (Gong et al., 2002) and the red-edge slope (Filella and Peñuelas, 1994).",
   "**Correlation spectra** — point-biserial correlation of every band with disease status, on all spectra and on each date; and **CART versus Random Forest on each feature group** with identical plot-grouped folds."]);
H2("2.7 Four tiers on the combined feature pool");
P(`All band-reflectance, continuum-removal, vegetation-index, derivative (first, second, third) and red-edge features were pooled (${CC.pool_raw} features; ${CC.n_features} after removing exact duplicates), and the same four tiers, settings and validation folds were applied. The features chosen by CART and by Random Forest from this pool, with their statistics and re-selection rates, are the **disease-specific features**.`);
H2("2.8 Cross-checks and software");
P(`Every step was verified by an independent route (${J.checks.pass} checks passed, ${J.checks.flag} flagged as limitations, ${J.checks.fail} failed): Welch t vs SciPy; FDR vs statsmodels; ANOVA F = t²; mixed model R nlme vs Python statsmodels; rpart vs scikit-learn trees; QDA vs manual discriminant functions and R MASS::qda; J–M by Cholesky vs explicit inverse; Random Forest importance vs a second seed, R randomForest and permutation importance; indices, red-edge position and plot averages recomputed by Excel formulas; assertions that no plot, and in leave-one-date-out no date, is in training and test. Software: Python 3.13 (NumPy, SciPy, pandas, statsmodels, scikit-learn, imbalanced-learn, matplotlib, openpyxl) and R 4.3.3 (rpart, MASS, nlme, randomForest).`);
figure("F01_workflow.png", "Workflow of the analysis.", 600);

// ================================================================ 3 results: raw reflectance
pageBreak();
H1("3. Results — four tiers on raw reflectance");
H2("3.1 Plot-average spectra");
figure("F02_mean_spectra.png", "Mean plot-average reflectance of healthy and diseased plots (± 1 SD), all dates combined.", 610);
figure("F02b_mean_spectra_by_date.png", "Mean plot-average spectra of healthy and diseased plots on each date.", 620);
P("Diseased plots reflect more in the visible — most clearly in the red (600–680 nm), where chlorophyll absorbs — and in the short-wave infrared beyond 1350 nm, and slightly less on the near-infrared plateau. Higher visible reflectance indicates chlorosis (less chlorophyll), and higher SWIR reflectance indicates lower leaf water content. The difference changes with the date (Figure 3): on 11-02-2026 the classes hardly differ in the red (mean difference −0.3 % reflectance), whereas the red difference is +1.6 % on 24-02, +3.1 % on 03-03 and +1.7 % on 13-03-2026; in SWIR-2 (2000–2300 nm) it grows from +0.3–0.5 % on the first two dates to +3.7 % and +2.4 % on the last two. The NIR plateau (780–1000 nm) is lower in diseased plots on the first three dates (−0.9 to −3.3 %) but higher on 13-03-2026 (+1.2 %), which is why the NIR level is not significant when all dates are pooled.");
H2("3.2 Tier 1 — statistical screening");
table(A.tests, "Tier 1: number of significant bands (of 2101) by test.", [5, 1.4]);
P(`Welch's t-test with FDR control found ${A.n_sig} significant bands; ${t1("Mixed")} remain significant with a random plot effect, so the differences are not an artefact of repeated measurements of the same plots. In balanced subsets (48 vs 48) a median of ${Math.round(A.balanced.median)} bands were significant and ${A.balanced.ge95} bands in at least 95 % of the 1000 subsets — the imbalance does not create the result. The significant bands form contiguous ranges (Table 3, Figure 4): all 80 red bands (600–679 nm), most of the red edge, the water bands and the whole SWIR-2 region, but no band of the NIR plateau (760–1349 nm) and none in the blue.`);
table(A.regions, "Tier 1 by spectral region: significant bands (Welch + FDR and mixed model) and the band of maximum |t|.", [2.2, 0.8, 1.3, 1.3, 1.1, 0.8]);
figure("F05_minus_log10_p.png", "−log₁₀(p) of every band against wavelength (Welch p, FDR-adjusted q and mixed-model q). Dashed line: p or q = 0.05.", 600);
figure("F03_tier1_significant_regions.png", "Mean spectra with the Tier-1 significant bands shaded.", 560);
H2("3.3 Tier 2 — band selection by CART and Random Forest");
P(`CART (equal priors) selected ${A.set_sizes[cartA]} bands, in order of use: ${A.sets[cartA]} nm (Figure 6). The root split is at ${A.sets[cartA].split(",")[0]} nm (red edge), followed by red (655, 669 nm), green (510 nm), water-band (1384, 1884 nm) and SWIR-1 (1578 nm) bands. The bands at 699 and 700 nm were re-selected (± 10 nm) in 86 % of 200 plot-level bootstrap trees and in all 50 nested training sets (Table 4). The 1-SE tree uses a single band.`);
figure("F06_cart_tree.png", `CART tree on the Tier-1 bands (${cartA}), rpart with prior 0.5/0.5.`, 600);
table([["Band (nm)", "Region", "First used at node", "Welch t", "Bootstrap re-selection (±10 nm)", "Nested cross-validation re-selection (±10 nm)", "Mixed model significant"], ...A.cart_table.slice(1)],
      `The ${cartA} bands and how often a band within ± 10 nm is re-selected.`, [0.8, 1.6, 0.9, 0.7, 1.2, 1.4, 1]);
P(`The Balanced Random Forest importance spectrum (Figure 7) has its highest peaks in the red (602–688 nm) and at the red edge (699 nm) and further peaks in the 1887–1928 nm water band and at 1992–2031 nm: ${rfA} = ${A.sets[rfA]} nm. Ten of the 17 bands lie in the visible and red edge.`);
figure("F12_A1_rf_importance.png", `Balanced Random Forest importance spectrum with the ${rfA} peaks and the CART bands.`, 600);
H2("3.4 Tier 3 — Jeffries–Matusita separability");
table(A.tier3, "Tier 3: Jeffries–Matusita distance (0–2) between healthy and diseased plot-average spectra on each band set.", [3, 1, 1]);
P(`J–M on the CART bands is ${jmA(cartA)}, below the separability threshold; the RF-17 bands reach ${jmA(rfA)}, above 1.90 and the 1.94 of Das et al. With the same number of bands as CART (size-matched set) the Random Forest bands give ${jmA(A.tier3.find((r) => r[0].includes("size-matched"))[0])}: slightly better than CART at equal size, so most of the higher separability of RF-17 comes from its larger number of bands. J–M rises steadily as bands are added (Figure 8).`);
figure("F09_tier3_tier4_incremental.png", "J–M distance and QDA balanced accuracy as the CART and Random Forest bands are added one by one.", 600);
H2("3.5 Tier 4 — QDA classification");
table(em(A.errmat[cartA]), `Error matrix of QDA (equal priors) on the ${cartA} bands, spectrum-level 10-fold cross-validation (layout of Das et al., Table 2).`, [2, 1, 1, 1, 1.2]);
table(em(A.errmat[rfA]), `Error matrix of QDA (equal priors) on the ${rfA} bands, spectrum-level 10-fold cross-validation.`, [2, 1, 1, 1, 1.2]);
table(A.tier4, "Tier 4 on all band sets: QDA with equal and sample priors and LDA (spectrum-level 10-fold cross-validation).", [1.8, 1.6, 0.8, 0.8, 0.8, 0.8, 0.7, 0.7], 15);
P(`With the protocol of Das et al., QDA on the CART bands reaches a balanced accuracy of ${pct(A.errmat[cartA].BA)} (OA ${pct(A.errmat[cartA].OA)}, κ = ${num(A.errmat[cartA].kappa)}) and on the RF-17 bands ${pct(A.errmat[rfA].BA)} (OA ${pct(A.errmat[rfA].OA)}, κ = ${num(A.errmat[rfA].kappa)}). With equal priors the healthy recall (producer's accuracy) of the CART bands is ${pct(A.errmat[cartA].PA_H)}; with sample priors it would fall to 75.0 %.`);
H2("3.6 Validation on new plots and new dates");
valTab(A, vA, "Balanced accuracy of the four pipelines on raw reflectance under each validation scheme (± SD over repeats or splits).");
figure("F11_validation_qda_cart.png", "QDA on the CART bands under each validation scheme, equal (corrected) vs sample (uncorrected) priors.", 560);
P(`On new plots (nested plot-grouped cross-validation) QDA on the CART bands reaches ${pct(vA("QDA on CART features", "V3").BA)} and QDA on the Random Forest bands ${pct(vA("QDA on RF features", "V3").BA)}; the spectrum-level estimate of the paper's protocol is ${p1(vA("QDA on CART features", "V1").BA - vA("QDA on CART features", "V3").BA)} points optimistic for the CART bands. The 30 % plot hold-out gives lower values (${pct(vA("QDA on CART features", "V4").BA)} and ${pct(vA("QDA on RF features", "V4").BA)}) with a large spread between splits, because each split holds out only 4 healthy plots. On an unseen date accuracy drops to ${pct(vA("QDA on CART features", "V5").BA)} (CART bands).`);
P(`**Imbalance correction.** In nested cross-validation equal priors give a healthy recall of ${vq("Nested", "equal")[6]} against ${vq("Nested", "sample")[6]} with sample priors, at a similar balanced accuracy (${vq("Nested", "equal")[3]} vs ${vq("Nested", "sample")[3]}). Random under-sampling of the diseased spectra gave ${vq("Nested plot-grouped cross-validation with random", "equal")[3]} because it discards two thirds of the diseased spectra.`);
H2("3.7 CART versus Random Forest");
table(A.wilcoxon, "Paired comparisons on identical folds (positive = first pipeline better).", [2.6, 2.4, 1, 0.7, 0.7, 0.8], 15);
figure("F13_A3_pipelines.png", "CART and Random Forest as classifiers and as band selectors for QDA (raw reflectance).", 600);
table(A.stability.map((r) => [r[0], r[1], r[2], r[4], r[5]]), "Stability of the selected bands over the 50 nested training sets.", [1, 1, 1.2, 1.2, 1.4]);
figure("F14_A4_stability.png", "Re-selection of the CART and Random Forest bands in the 50 nested training sets (± 10 nm).", 560);
P(`Random Forest is better than CART in both roles: as a classifier by ${A.wilcoxon[1][2]} (Random Forest better in ${A.wilcoxon[1][3]} of 50 folds, p = ${A.wilcoxon[1][5]}) and as a band selector for QDA by ${A.wilcoxon[3][2]} (p = ${A.wilcoxon[3][5]}). Its band selection is also far more stable (mean pairwise Jaccard ${A.stability[2][5]} vs ${A.stability[1][5]} for CART). A single CART tree is unstable because small changes in the training plots change the split variables, whereas the forest averages 1000 trees.`);

// ================================================================ 4 results: features
pageBreak();
H1("4. Results — disease-sensitive features from raw reflectance");
H2("4.1 Band reflectance");
table(K.k1_regions, "Most sensitive raw reflectance band of each region (threshold classifier validated on plots).", [1.1, 1, 0.8, 0.9, 0.9, 1.3, 1.2]);
figure("F16_K1_K4_band_auc.png", "AUC of every band: raw reflectance and first derivative (grey: detector guard zones).", 600);
P(`The best single reflectance band is at 650 nm (AUC 0.785, diseased > healthy); ${K.k1.auc70} bands have AUC ≥ 0.70. A threshold on a single band classifies new plots with a balanced accuracy of at most about 71 % — the disease signal is spread over many bands.`);
H2("4.2 Continuum removal");
table([J.k2_all[0], ...J.k2_all.slice(1, 13)], "Continuum-removal parameters ranked by AUC.", [2.6, 1, 1, 0.7, 0.8, 1.2, 1]);
figure("F17_K2_continuum.png", "Mean continuum-removed absorption features of healthy and diseased plots.", 600);
P("The strongest continuum-removal parameter is the depth/area ratio of the 970-nm water feature (AUC 0.792; higher in diseased plots), followed by the width of the 970-nm feature (narrower in diseased plots), the position and symmetry of the 1940-nm feature and the area of the red (chlorophyll) feature (smaller in diseased plots). These describe a narrower 970-nm water absorption (higher depth-to-area ratio) and a weaker chlorophyll absorption (smaller red-feature area) in diseased plots.");
H2("4.3 Vegetation indices");
table([J.k3_all[0], ...J.k3_all.slice(1, 16)], `The 15 most sensitive of the ${J.vi_table.length - 1} vegetation indices.`, [1.4, 1, 1, 0.7, 0.8, 1.2, 1]);
figure("F18_K3_indices.png", "The 30 most sensitive vegetation indices ranked by AUC (orange: higher in diseased, aqua: lower in diseased).", 480);
P("No published index exceeds AUC 0.75: the best are the chlorophyll-b ratio RARSb, the red-edge stress index RVS2, the red-NIR ratios NDVI761/SR761, PRI515, the water index NWI2 and the pigment ratios PSSRb/PSNDb. Published indices use fixed wavelengths chosen for other purposes and capture only part of the white-rust signal.");
H2("4.4 Optimised two-band index");
table(K.k3b_jf_refined, "Optimised two-band indices (all band pairs searched; pairs straddling a detector join excluded).", [1.5, 1, 1, 0.7, 0.8, 1.3, 1.1]);
figure("F19_K3b_ndsi_heatmap.png", "AUC of the normalised-difference index for every band pair.", 520);
P(`The best pair is (870, 872) nm (AUC 0.916) — two adjacent bands on the near-infrared shoulder, i.e. a local slope, the same information as the first derivative at 871 nm. When the pair is searched inside the training plots only, the honest balanced accuracy is ${pct(K.k3b_jf_honest.NDSI["BA CV"])} (NDSI) and ${pct(K.k3b_jf_honest.DI["BA CV"])} (difference index); the pair (870, 875) nm was found in almost every training set, so the location is stable.`);
H2("4.5 First-, second- and third-derivative spectra");
table(K.k4_summary, "Band-wise derivative sensitivity (central differences of raw reflectance; guard zones excluded from the ranking).", [2.6, 0.9, 1, 0.7, 2]);
table(J.k4_regions, "Most sensitive derivative band of each region.", [0.8, 1.2, 0.9, 0.7, 0.8, 0.8], 15);
figure("F20_K4_first_derivative.png", "Mean first-derivative spectra of healthy and diseased plots and the red-edge region.", 600);
P("Derivatives are the most discriminating single features: the first derivative at 871 nm reaches AUC 0.916 (Hedges' g = 1.57), the second derivative at 741 nm 0.829 and the third derivative at 738 nm 0.832. In diseased plots the reflectance on the NIR shoulder (780–900 nm) still rises with wavelength, whereas in healthy plots it has already levelled off or falls slightly — a change in the shape of the NIR plateau that the reflectance itself (AUC ≤ 0.63 in this region) does not reveal, because it is masked by brightness differences between plots. The second and third derivatives at 737–741 nm describe a change in the curvature of the upper red edge.");
H2("4.6 Red-edge parameters");
table([J.edge_all[0], ...J.edge_all.slice(1, 14)], "Red-edge and edge parameters ranked by AUC.", [2.8, 1, 1, 0.7, 0.8, 1.2, 1]);
figure("F21_K4_REIP.png", "Red-edge inflection point by four methods (left) and by date (right).", 600);
P("The red well reflectance Ro (minimum reflectance 640–680 nm) is higher in diseased plots (AUC 0.75). The red-edge inflection point shifts to shorter wavelengths in diseased plots (Lagrangian: 707.5 → 704.6 nm, a 2.9-nm 'blue shift'; AUC 0.70), the classical sign of chlorophyll loss; the four REIP methods agree on the direction.");
H2("4.7 Correlation spectra");
table(K.corr_regions, "Band of maximum |r| (point-biserial correlation with disease status) per region, and whether its sign is the same on all four dates.", [1.3, 1.2, 1, 0.8, 1.3], 15);
figure("F22_K6_correlation.png", "Correlation of reflectance and first derivative with disease status, all spectra and each date.", 600);
P("The largest correlation is again for the first derivative at 871 nm (r = +0.57), and its sign is the same on all four dates. Correlations of reflectance in the SWIR are consistent across dates; those in the visible change sign between dates, i.e. the visible signal depends on the growth stage.");
H2("4.8 CART versus Random Forest on each feature group");
table(K.k5, "Balanced accuracy of CART and Balanced Random Forest on each feature group (nested plot-grouped cross-validation and 30 % plot hold-out).", [3, 0.8, 1, 1, 1, 1]);
figure("F23_K5_cart_vs_rf.png", "CART versus Random Forest on each feature group.", 600);
P(`Random Forest beats CART on every feature group (Wilcoxon p < 0.001 in cross-validation). The derivative-and-edge group (${k5("Derivatives + edge", 3)}) and the continuum-removal parameters (${k5("Continuum", 3)}) give by far the highest accuracy, against ${k5("Band reflectance", 3)} for band reflectance and ${k5("Vegetation indices", 3)} for the vegetation indices. Including the guard-zone bands beside the detector joins raises the derivative group further (${k5("Derivatives incl.", 3)}), but these bands carry an instrument artefact and were excluded.`);

// ================================================================ 5 results: combined pool
pageBreak();
H1("5. Results — four tiers on the combined feature pool");
H2("5.1 Pool and Tier 1");
table(CC.composition, "Composition of the combined pool, Tier-1 significant features and the features chosen by CART and Random Forest.", [2.6, 0.8, 1, 0.7, 0.8, 0.7, 0.7, 0.8], 15);
figure("F24_C_composition.png", "Feature types chosen by CART and Random Forest from the combined pool.", 560);
P(`The pool contains ${CC.n_features} features, of which ${CC.n_sig} passed Tier 1.`);
H2("5.2 Tier 2 — selected features");
P(`CART (${cartC}) chose ${featList(CC.sets[cartC])}. Random Forest (${rfC}) chose ${featList(CC.sets[rfC])}. Both selectors chose only derivative features; no reflectance band, vegetation index or continuum-removal parameter entered the RF-17 set.`);
figure("F26_C_cart_tree.png", `CART tree on the combined pool (${cartC}).`, 560);
figure("F25_C_top_importance.png", "The 30 most important features of the combined pool (Balanced Random Forest).", 520);
H2("5.3 Tiers 3 and 4");
table(CC.tier3, "Jeffries–Matusita distance on the feature sets of the combined pool.", [3, 1, 1]);
table(em(CC.errmat[rfC]), `Error matrix of QDA (equal priors) on the ${rfC} features of the combined pool, spectrum-level 10-fold cross-validation.`, [2, 1, 1, 1, 1.2]);
table(CC.tier4, "Tier 4 on all feature sets of the combined pool (spectrum-level 10-fold cross-validation).", [1.8, 1.6, 0.8, 0.8, 0.8, 0.8, 0.7, 0.7], 15);
P(`J–M is ${jmC(rfC)} on the RF-17 features (separable) and ${jmC(cartC)} on the 4 CART features. QDA on the RF-17 features reaches a balanced accuracy of ${pct(CC.errmat[rfC].BA)} (OA ${pct(CC.errmat[rfC].OA)}, κ = ${num(CC.errmat[rfC].kappa)}) in the protocol of Das et al.`);
figure("F27_C_incremental.png", "J–M and QDA balanced accuracy as the combined-pool features are added.", 560);
H2("5.4 Validation");
valTab(CC, vC, "Balanced accuracy of the four pipelines on the combined pool under each validation scheme.");
figure("F28_C_pipelines.png", "The four pipelines on the combined pool under the four validation schemes.", 600);
table(X.cross, "Combined pool vs raw reflectance (paired over identical folds; positive = first better).", [2.4, 2.4, 2.2, 0.9, 0.6, 0.6, 0.7], 14);
P(`The combined pool improves the tree-based classifiers strongly: the Random Forest classifier rises from ${pct(vA("RF classifier", "V3").BA)} on raw reflectance to ${pct(vC("RF classifier", "V3").BA)} on new plots (+17.3 points, p = 1.2e-09) and to ${pct(vC("RF classifier", "V4").BA)} on the 30 % plot hold-out; CART rises by 19.0 points. QDA on the CART features improves by 6.8 points, whereas QDA on the RF-17 features gains nothing over the raw RF-17 bands (${pct(vC("QDA on RF features", "V3").BA)} vs ${pct(vA("QDA on RF features", "V3").BA)}) and loses on the plot hold-out (${pct(vC("QDA on RF features", "V4").BA)}): 17 highly correlated derivative features and few healthy plots make the class covariance matrices of QDA unstable. On the combined pool the Random Forest itself is the best classifier.`);
H2("5.5 Stability of the selected features");
table(CC.stability, "Stability of the CART and Random Forest feature selections in the 50 nested training sets.", [1, 1, 1.2, 1.2, 1.4]);
table(CC.fold_comp, "Feature types selected in the 50 nested training sets.", [1, 2.4, 1.4, 0.8]);
figure("F28b_C_stability.png", "Re-selection of the CART and Random Forest features of the combined pool in the 50 nested training sets.", 560);
H2("5.6 Disease-specific features");
table(J.DS.rows, "Disease-specific features: the features chosen by CART and Random Forest from the combined pool, with class means, direction, AUC, FDR q and re-selection in the 50 nested training sets (CART / Random Forest).", [2.2, 1.4, 1.5, 0.9, 0.9, 0.7, 0.6, 0.7, 1.1], 14);
P("The disease-specific features of white rust at plot level fall into three groups:");
B(["**Slope of the near-infrared shoulder** — first derivative at 820–893 nm (871, 852, 893, 839, 820, 784 nm; AUC 0.81–0.92). Diseased plots have a positive slope where healthy plots are flat or slightly negative. The first derivative at 871 nm is the single best feature (AUC 0.916), chosen by both CART and Random Forest and re-selected in every training set.",
   "**Curvature of the red edge** — second derivative at 682 nm and second/third derivative at 737–741 nm (AUC 0.81–0.83): the lower and upper bends of the red edge, consistent with the blue shift of the red-edge position caused by chlorophyll loss.",
   "**Derivatives in the water-absorption regions** — second and third derivatives at 934, 1077, 1240–1244, 1720 and 1918 nm (AUC 0.65–0.82): changes in the shape of the 970-, 1200-, 1730- and 1940-nm absorption features, i.e. leaf water and dry matter."]);
P("These features are significant after FDR control (q ≤ 0.02), their direction is consistent, and Random Forest re-selects the RF-17 features (within ± 10 nm) in 14–100 % of the training sets — 15 of the 17 in at least 42 %, the first derivatives at 852–893 nm in all of them. They describe the shape of the spectrum rather than its level, which makes them less sensitive to brightness differences between plots and dates than single reflectance bands.");

// ================================================================ 6 synthesis
pageBreak();
H1("6. Synthesis and transfer to new dates");
figure("F29_synthesis.png", "Balanced accuracy of all approaches on new plots (nested plot-grouped cross-validation ± SD over repeats; 30 % plot hold-out ± SD over splits).", 620);
table([["Approach", "Nested plot-grouped cross-validation", "30 % plot hold-out validation", "Leave-one-date-out validation"], ...X.synthesis_all.slice(1, 21)],
      "All approaches ranked by the nested plot-grouped balanced accuracy.", [4.4, 1.3, 1.3, 1.3], 15);
table(X.lodo, "Leave-one-date-out validation on new plots: balanced accuracy on each held-out date.", [3, 1, 1, 1, 1]);
figure("F30_V5_leave_one_date_out.png", "Leave-one-date-out validation on new plots, by held-out date.", 560);
P("When a whole date is held out, all pipelines drop to 43–77 % and the last date (13-03-2026) is classified at chance level by every pipeline: a model trained on the earlier dates does not apply to the late-season spectra, in which, for example, the NIR difference between the classes has changed sign. The spectral expression of white rust changes with the growth stage (and the canopy and leaf age), so a classifier should be calibrated with plots of the target stage.");
table(X.strata_range, "AUC of the best feature of each family on all spectra and its range over dates, growth stages and varieties.", [2.6, 1, 1.2, 1.2, 1.1], 15);

// ================================================================ 7 discussion
pageBreak();
H1("7. Discussion");
H2("7.1 Which wavelengths separate healthy and diseased plots?");
P("Tier 1 identifies the red (600–680 nm), the red edge, the water bands around 1400 and 1900 nm and SWIR-2 as the regions where diseased plots differ from healthy plots, while the NIR plateau does not differ in level. CART and Random Forest concentrate on the red edge and red (699, 700, 689, 669, 655 nm; Random Forest 602–699 nm) with additional bands in the 1384–1928 nm water region. This matches the expected symptoms of white rust: chlorosis reduces chlorophyll absorption (higher red reflectance, blue-shifted red edge) and infected leaves lose water (higher SWIR reflectance, shallower water absorptions).");
H2("7.2 Plot averages versus single leaves");
P(`Averaging the leaves of a plot improves discrimination on new plots: compared with the leaf-level analysis of all 2264 leaf spectra (QDA on CART bands 72.0 %, combined pool 83.7 % in nested plot-grouped cross-validation), the plot averages give ${pct(vA("QDA on CART features", "V3").BA)} and ${pct(vC("QDA on RF features", "V3").BA)}, and the Random Forest on the combined pool ${pct(vC("RF classifier", "V3").BA)}. Averaging removes leaf-to-leaf variation (leaf position, age, angle, the presence or absence of a pustule under the probe) and random noise, so the derivative features — which amplify noise — become reliable even without smoothing. The price is fewer samples (192 instead of 2264) and a coarser unit: a plot average describes the plot, not an individual leaf.`);
H2("7.3 Correction for the imbalanced classes");
P("With 48 healthy and 144 diseased spectra an uncorrected classifier favours 'diseased': QDA with sample priors would recall only 72 % of the healthy plots on new plots. Equal priors in rpart and QDA and the balanced bootstrap of the Random Forest raise the healthy recall (QDA on CART bands: 80 % on new plots) at a similar balanced accuracy; balanced subsets confirm that the Tier-1 result does not depend on the imbalance. Random under-sampling was inferior because it discards most of the diseased spectra. Balanced accuracy, together with both recalls and κ, is therefore the appropriate summary.");
H2("7.4 CART versus Random Forest");
P("Random Forest is the better choice in both roles. As a classifier it is 10–12 points better than a single CART tree; as a band selector its bands give a higher J–M (1.96 vs 1.52 on raw reflectance) and a higher QDA accuracy, and its selection is about twice as stable. CART remains useful for interpretation — a tree with a handful of thresholds (e.g. the first derivative at 871 nm at the root of the combined-pool tree) shows how the decision is made — but its selection depends strongly on the particular training plots.");
H2("7.5 Disease-specific features");
P("The combined pool shows that the most discriminating information lies in the shape of the spectrum rather than in reflectance levels: all features selected from 8264 candidates were derivatives. The first derivative on the NIR shoulder (820–895 nm) is the single best feature; a change of this slope indicates altered internal leaf structure (disrupted mesophyll and epidermis around the sori) and possibly the white pustules, which scatter strongly. Curvature features at the lower (682 nm) and upper (737–741 nm) red edge reflect the chlorophyll loss that also shifts the red-edge position by about 3 nm. Derivative features of the 970-, 1200- and 1940-nm absorptions reflect the loss of leaf water. Continuum-removal parameters of the 970-nm water feature are almost as informative as a group (Random Forest 93 %), whereas published vegetation indices are clearly weaker (≤ 78 %).");
H2("7.6 Validation and limitations");
B(["The spectrum-level 10-fold cross-validation of Das et al. is optimistic (by 3–4 points for QDA on CART bands) because the same plot on other dates is in training and test; nested plot-grouped cross-validation and the plot hold-out are the honest estimates for new plots.",
   "Only 12 healthy plots exist; each plot hold-out tests 4 of them, so hold-out accuracies vary by ± 5–8 points between splits.",
   "Transfer to a new date is weak (43–77 %, chance level for the last date, 13-03-2026): the models are valid for the dates and growth stages they were trained on.",
   "Raw (unsmoothed) derivatives were used as requested; plot averaging keeps their noise low, but derivatives beside the detector joins are artefact-prone and were excluded (with them the derivative group would reach 95.6 %).",
   "The feature lists of Table 5.6 were selected on all 192 spectra; their accuracy on new plots is given by the nested validation, in which the selection was repeated inside every training set."]);

// ================================================================ 8 conclusions
H1("8. Conclusions");
B([`Healthy and white-rust-diseased mustard plots differ significantly at ${A.n_sig} of 2101 bands (plot-average spectra, all dates), mainly in the red, at the red edge, in the water bands and in SWIR-2; the result is robust to the plot effect and to the class imbalance.`,
   `The four tiers of Das et al. on raw reflectance select ${A.set_sizes[cartA]} CART bands (root 699 nm; J–M ${jmA(cartA)}) and 17 Random Forest bands (J–M ${jmA(rfA)}, separable); QDA with equal priors classifies new plots with ${pct(vA("QDA on CART features", "V3").BA)} (CART bands) and ${pct(vA("QDA on RF features", "V3").BA)} (Random Forest bands) balanced accuracy.`,
   `Random Forest is superior to CART as classifier (+${A.wilcoxon[1][2].replace(/[+ pts]/g, "")} points) and as band selector, and its selection is more stable.`,
   `Disease-sensitive features derived from raw reflectance — especially derivatives and continuum-removal parameters — separate the classes far better than reflectance bands or published vegetation indices; on the combined pool a Balanced Random Forest reaches ${pct(vC("RF classifier", "V3").BA)} on new plots.`,
   "The disease-specific features of white rust at plot level are the first derivative of the NIR shoulder (820–895 nm, best at 871 nm), the curvature of the red edge (682 and 737–741 nm) and derivative features of the water absorptions (≈ 970, 1240 and 1918 nm).",
   "Models trained on some dates transfer poorly to a new growth stage; calibration with plots of the target stage is needed."]);
H2("Recommendations");
B(["Use plot-average spectra and derivative features (first derivative 820–895 nm; second/third derivative at the red edge) for white-rust detection with the contact probe.",
   "Select features with Balanced Random Forest importance and classify with a Balanced Random Forest (or QDA on a small, decorrelated feature set); report balanced accuracy with both recalls.",
   "Validate on new plots (plot-grouped, nested) and on new dates; do not rely on spectrum-level cross-validation.",
   "Calibrate for each growth stage, or collect further seasons before applying a model to a new stage."]);

// ================================================================ references + appendices
pageBreak();
H1("References");
(J.refs || []).forEach((r) => body.push(new Paragraph({ children: runs(r, { size: 20 }), spacing: { after: 80 }, indent: { left: 360, hanging: 360 } })));
pageBreak();
H1("Appendix A. Cross-checks");
table(J.checks.table.map((r) => [r[0], r[1], r[2], r[3], r[4]]), `All cross-checks (${J.checks.pass} passed, ${J.checks.flag} flagged as limitations, ${J.checks.fail} failed).`, [0.4, 1.2, 2.6, 3.6, 0.7], 14);
H1("Appendix B. Vegetation indices");
table(J.vi_table, `The ${J.vi_table.length - 1} vegetation indices (R = reflectance at the given wavelength, nearest 1-nm band).`, [1, 2.6, 3, 2], 14);
H1("Appendix C. Files");
table([["File", "Content"],
  ["WhiteRust_Mustard_PlotAverage_AllDates_FourTier_CART_RF_K_Combined.xlsx", "Excel workbook, 40 sheets: every step, table and figure, cross-checks and data (plot-average spectra, features, folds)"],
  ["WhiteRust_Mustard_PlotAverage_AllDates_Presentation.pptx", "Presentation of the methodological steps and results"],
  ["WhiteRust_Mustard_PlotAverage_AllDates_Report.docx", "This report"]], "Deliverables of this analysis.", [4, 4]);

const doc = new Document({
  creator: "Animesh Panda", title: "White rust in mustard — plot-average four-tier analysis", description: "Four-tier analysis of plot-average spectra",
  styles: { default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, color: "1F3D2B" }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, color: "2A5A3C" }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, color: "3B3B38" }, paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } }] },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "52514E" })] })] }) },
    children: body }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log("saved", OUT, figNo, "figures", tabNo, "tables"); });
