const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
const { applyTheme } = require(process.env.SKILL + "/scripts/apply_theme.js");

const RES = process.env.RES;                       // results folder of the 48-plot analysis
const OUT = process.argv[2];
const D = JSON.parse(fs.readFileSync(path.join(RES, "deck48.json"), "utf8"));
const IMG = (f) => path.join(RES, f);
const pct = (v, d = 1) => (100 * v).toFixed(d) + "%";
const f2 = (v, d = 2) => Number(v).toFixed(d);
const pm = (a, d = 3) => `${f2(a[0], d)} ± ${f2(a[1], d)}`;

const THEME = {
  name: "Canopy",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1F1D", lt1: "FFFFFF", dk2: "1F3A2E", lt2: "EEF3EF",
    accent1: "1BAF7A", accent2: "EB6834", accent3: "2A78D6", accent4: "EDA100", accent5: "6250D6", accent6: "52514E",
    hlink: "2A78D6", folHlink: "6250D6",
  },
};
const HX = THEME.colors;
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";        // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Four-tier analysis of 48-plot SMACC endmembers";
const C = pres.SchemeColor;
const W = 13.333, MX = 0.6, CW = W - 2 * MX;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "TITLE", background: { color: HX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.8, w: 11.7, h: 2.1, fontFace: THEME.headFontFace, fontSize: 40, bold: true, color: C.background1, valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 1.8, fontFace: THEME.bodyFontFace, fontSize: 18, color: "CADDD2", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION", background: { color: HX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.6, w: 11.7, h: 1.2, fontFace: THEME.headFontFace, fontSize: 40, bold: true, color: C.background1, valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.95, w: 11.7, h: 1.2, fontFace: THEME.bodyFontFace, fontSize: 18, color: "CADDD2", valign: "top", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, color: "CADDD2", fontSize: 10, fontFace: THEME.bodyFontFace, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSING", background: { color: HX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.45, w: CW, h: 0.9, fontFace: THEME.headFontFace, fontSize: 36, bold: true, color: C.background1, valign: "middle", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, color: "CADDD2", fontSize: 10, fontFace: THEME.bodyFontFace, align: "right" },
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: HX.lt1 },
  margin: [0.5, 0.6, 0.7, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.35, w: CW, h: 0.85, fontFace: THEME.headFontFace, fontSize: 30, bold: true, color: C.text2, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "48 plots · healthy vs diseased · four-tier analysis, RF comparison, imbalance handling", options: { x: MX, y: 7.0, w: 9, h: 0.3, fontSize: 10, color: HX.accent6, fontFace: THEME.bodyFontFace, margin: 0 } } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, color: HX.accent6, fontSize: 10, fontFace: THEME.bodyFontFace, align: "right" },
});

let section = "";
function slide(master, title, sub) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (sub) s.addText(sub, { placeholder: "body" });
  return s;
}
function newSection(t) { section = t; pres.addSection({ title: t }); }
const sizes = {};
for (const f of fs.readdirSync(RES).filter((f) => f.endsWith(".png"))) {
  const b = fs.readFileSync(IMG(f));
  sizes[f] = [b.readUInt32BE(16), b.readUInt32BE(20)];
}
function img(s, file, x, y, maxW, maxH, name) {
  const [pw, ph] = sizes[file];
  const ar = pw / ph;
  let w = maxW, h = maxW / ar;
  if (h > maxH) { h = maxH; w = maxH * ar; }
  s.addImage({ path: IMG(file), x: x + (maxW - w) / 2, y: y + (maxH - h) / 2, w, h, objectName: name || file, altText: name || file });
}
// each bullet is a single run (pptxgenjs writes an invalid mid-paragraph <a:pPr> for extra runs)
function body(s, items, x, y, w, h, size = 15, opts = {}) {
  const arr = items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } }));
  s.addText(arr, { x, y, w, h, fontSize: size, color: C.text1, valign: "top", margin: 0, isTextBox: true, ...opts });
}
function card(s, x, y, w, h, title, lines, fill = HX.lt2, size = 14) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08, objectName: "card " + title });
  s.addText(title, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.4, fontSize: 16, bold: true, color: C.text2, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
  const arr = lines.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < lines.length - 1, paraSpaceAfter: 4 } }));
  s.addText(arr, { x: x + 0.2, y: y + 0.6, w: w - 0.4, h: h - 0.72, fontSize: size, color: C.text1, valign: "top", margin: 0, isTextBox: true });
}
function stat(s, x, y, w, value, label, color = C.text2, vsize = 36) {
  s.addText(value, { x, y, w, h: 0.7, fontSize: vsize, bold: true, color, margin: 0, isTextBox: true, fontFace: THEME.headFontFace, valign: "bottom" });
  s.addText(label, { x, y: y + 0.72, w, h: 0.55, fontSize: 12, color: HX.accent6, margin: 0, isTextBox: true, valign: "top" });
}
function table(s, rows, x, y, w, colW, opts = {}) {
  const fs_ = opts.fontSize || 12;
  const out = rows.map((r, i) => r.map((c) => {
    const cell = typeof c === "object" && c !== null && c.text !== undefined ? c : { text: String(c) };
    const base = i === 0
      ? { bold: true, color: HX.lt1, fill: { color: HX.dk2 }, fontSize: fs_, valign: "middle" }
      : { color: HX.dk1, fill: { color: i % 2 === 0 ? HX.lt2 : HX.lt1 }, fontSize: fs_, valign: "middle" };
    return { text: cell.text, options: { ...base, ...(cell.options || {}) } };
  }));
  s.addTable(out, { x, y, w, colW, border: { type: "solid", pt: 0.5, color: "C9D3CC" }, margin: [3, 6, 3, 6], fontFace: THEME.bodyFontFace, autoPage: false, rowH: opts.rowH, objectName: opts.name || "table" });
}
function caption(s, text, x, y, w, h = 0.35) {
  s.addText(text, { x, y, w, h, fontSize: 11, italic: true, color: HX.accent6, margin: 0, isTextBox: true, valign: "top" });
}
function steps(s, items, x0, y0, cols, w, h, gx, gy, tsize = 16, dsize = 13) {
  items.forEach(([t, d], i) => {
    const col = i % cols, row = Math.floor(i / cols);
    const x = x0 + col * (w + gx), y = y0 + row * (h + gy);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: HX.lt2 }, line: { color: HX.lt2 }, rectRadius: 0.08, objectName: "box " + t });
    s.addText(t, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.4, fontSize: tsize, bold: true, color: C.text2, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(d, { x: x + 0.2, y: y + 0.55, w: w - 0.4, h: h - 0.62, fontSize: dsize, color: C.text1, margin: 0, isTextBox: true, valign: "top" });
  });
}

const cfg = D.cfg, S = ["S0", "S1", "S2", "S3"], T2 = ["CART", "RF"];
const K = (t, s) => cfg[`${t}-${s}`];
const SN = { S0: "S0 none", S1: "S1 class weights", S2: "S2 under-sampling", S3: "S3 SMOTE" };
const bestC = K("CART", D.best.CART), bestR = K("RF", D.best.RF);
const allCfg = T2.flatMap((t) => S.map((s) => K(t, s)));
const topV2 = allCfg.reduce((a, b) => (b.v2.BA[0] > a.v2.BA[0] ? b : a));
const topPlot = allCfg.reduce((a, b) => (b.v2plot.BA[0] > a.v2plot.BA[0] ? b : a));
const topV3 = allCfg.reduce((a, b) => (b.v3.plotBA > a.v3.plotBA ? b : a));
const t1 = D.tier1, pc = D.perm.CART, pr = D.perm.RF;
const v1max = Math.max(...allCfg.map((c) => c.v1.BA[0])), v1best = allCfg.find((c) => c.v1.BA[0] === v1max);
const jmMax = Math.max(...allCfg.map((c) => c.JM)), jmBest = allCfg.find((c) => c.JM === jmMax);
const edge = (b) => b < 420 || b > 2350;
const nEdge = (c) => c.bands.filter(edge).length;
const lab = (c) => `${c.t2}-${c.s}`;

// ================================================================== 1 TITLE
newSection("Introduction");
slide("TITLE", "Healthy vs diseased plots from SMACC endmembers: four-tier analysis with imbalance handling",
  `Four-tier method of Das et al. (2020): ANOVA → CART → J–M distance → QDA, with Random Forest in place of CART in Tier 2 for comparison\n48 plots (1–12 healthy, 13–48 diseased) · ${D.N} endmember spectra kept separately · all ${D.P} reflectance bands`);

// ================================================================== 2 WORKFLOW
{
  const s = slide("CONTENT", "Workflow at a glance");
  const blocks = [
    ["A", "Data", ["48 plot ROIs", "SMACC: 30 endmembers / plot", `${D.N} spectra kept separately`, `All ${D.P} bands, reflectance only`, "Data check"], HX.accent6],
    ["B", "Four-tier analysis", ["Tier 1: ANOVA + Tukey per band", "Tier 2: CART or RF band selection", "Tier 3: J–M distance", "Tier 4: QDA"], HX.dk2],
    ["C", "Class imbalance", [`Healthy : diseased = 1 : ${f2(D.nD / D.nH, 2)}`, "S0 no correction", "S1 class weighting", "S2 random under-sampling", "S3 SMOTE"], HX.accent4],
    ["D", "Validation & checks", ["Paper-style random 10-fold", "Plot-grouped nested CV (main)", "Leave-one-plot-out", "Permutation test", "Python ↔ Excel checks"], HX.accent3],
  ];
  const bw = 2.85, gap = 0.243;
  blocks.forEach(([k, t, items, col], i) => {
    const x = MX + i * (bw + gap), y = 1.5;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: bw, h: 4.1, fill: { color: HX.lt2 }, line: { color: HX.lt2 }, rectRadius: 0.08, objectName: "stage " + k });
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.22, w: 0.62, h: 0.62, fill: { color: col }, line: { color: col }, objectName: "stage badge " + k });
    s.addText(k, { x: x + 0.2, y: y + 0.22, w: 0.62, h: 0.62, align: "center", valign: "middle", fontSize: 22, bold: true, color: HX.lt1, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(t, { x: x + 0.95, y: y + 0.22, w: bw - 1.1, h: 0.62, fontSize: 17, bold: true, color: C.text2, valign: "middle", margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(items.map((it, j) => ({ text: it, options: { bullet: { type: "number" }, breakLine: j < items.length - 1, paraSpaceAfter: 8 } })),
      { x: x + 0.2, y: y + 1.1, w: bw - 0.35, h: 2.85, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
    if (i < 3) s.addText("›", { x: x + bw - 0.02, y: y + 1.7, w: gap + 0.04, h: 0.6, fontSize: 30, color: HX.accent6, align: "center", margin: 0, isTextBox: true });
  });
  s.addText("8 analysis configurations = 2 Tier-2 methods (CART, RF) × 4 imbalance strategies (S0–S3). Every re-sampling and every band selection is done on training data only. Seed 42 for all random steps.",
    { x: MX, y: 5.85, w: CW, h: 0.8, fontSize: 15, color: C.text1, margin: 0, isTextBox: true, valign: "middle" });
}

// ================================================================== PART A DATA
newSection("A. Data");
slide("SECTION", "A · Data", "48 plot ROIs, 30 SMACC endmembers per plot, every endmember kept as a separate spectrum");

{
  const s = slide("CONTENT", "48 plots and the analysis data set");
  img(s, "f01_plotmap.png", MX, 1.35, 6.0, 5.5, "Plot map");
  stat(s, 7.0, 1.45, 2.7, String(D.N), "endmember spectra analysed");
  stat(s, 9.9, 1.45, 2.8, `${D.nH} / ${D.nD}`, "healthy / diseased spectra", C.text2);
  stat(s, 7.0, 2.85, 2.7, String(D.P), `reflectance bands (${D.wl_min.toFixed(0)}–${D.wl_max.toFixed(0)} nm)`);
  stat(s, 9.9, 2.85, 2.8, `1 : ${f2(D.nD / D.nH, 2)}`, "class ratio (imbalanced)", HX.accent2);
  body(s, [
    "Plot polygons from 48_plot_roi_new.xml (ROI #1–#48, WGS-84), drawn in local metres",
    `30 SMACC endmembers per plot (Gruninger et al. 2004); ${D.removed} were removed before this analysis, so plots keep ${D.em_min}–${D.em_max}`,
    "Endmembers are not averaged: each is one sample, labelled by its plot's class",
    "Healthy plots 1–12 lie together at the west end of the field: class and position are partly confounded",
  ], 7.0, 4.3, 5.73, 2.5, 13.5);
}

{
  const s = slide("CONTENT", "Endmember spectra per plot");
  img(s, "f02_counts.png", MX, 1.35, CW, 3.9, "Endmembers per plot");
  body(s, [
    `Healthy plots: ${D.em_H[0]}–${D.em_H[1]} spectra each (${D.nH} in total); diseased plots: ${D.em_D[0]}–${D.em_D[1]} each (${D.nD} in total)`,
    "Spectra of one plot share soil, illumination and management: they are not independent samples. This is why validation is done by plot (Part D)",
  ], MX, 5.4, CW, 1.4, 15);
}

{
  const s = slide("CONTENT", "All endmember spectra");
  img(s, "f03_spectra.png", MX, 1.35, CW, 4.8, "All endmember spectra");
  caption(s, `Thin lines: individual endmembers (${D.nH} healthy, ${D.nD} diseased); black: class mean. Gaps are the water-absorption bands absent from the image. SMACC picks the most extreme spectra of each plot, hence the wide spread.`, MX, 6.25, CW, 0.6);
}

{
  const s = slide("CONTENT", "Class means and variability");
  img(s, "f04_mean_sd.png", MX, 1.35, CW, 4.7, "Mean ± SD spectra");
  caption(s, "Mean ± 1 SD per class over all 483 bands. The two bands overlap almost everywhere: the class difference is small compared with the spread within each class.", MX, 6.2, CW, 0.6);
}

{
  const s = slide("CONTENT", "Data check: everything is analysed");
  stat(s, MX, 1.5, 2.8, String(D.N), "spectra analysed: none removed in this step");
  stat(s, MX + 3.0, 1.5, 2.8, String(D.P), "bands analysed: none excluded");
  body(s, [
    "As requested, all uploaded endmembers and all wavelengths are used, including the detector edges (< 420 nm, > 2,350 nm)",
    `Negative reflectance (physically impossible) in ${D.neg.healthy} healthy and ${D.neg.diseased} diseased spectra, at ${D.neg_bands} bands, mainly the noisy ends of the range`,
    "These values are kept (no editing of data), but bands chosen there are flagged when the results are interpreted",
    "Checks passed: 1417 × 483 values, no missing values, plots 1–12 = healthy, 13–48 = diseased, each spectrum in exactly one plot",
  ], MX, 3.0, 6.2, 3.8, 14.5);
  img(s, "f05_negatives.png", 7.0, 1.45, 5.73, 4.5, "Negative reflectance by band");
}

// ================================================================== PART B METHODS AND WHY
newSection("B. Methods and why");
slide("SECTION", "B · Methods and why they are used", "Four-tier method, imbalance strategies, validation design and accuracy measures, each with its reference");

{
  const s = slide("CONTENT", "Four-tier method: what each tier does and why");
  table(s, [
    ["Tier", "What is done here", "Why", "Reference"],
    ["1 · ANOVA", "One-way ANOVA per band, p < 0.05; Tukey HSD; FDR and Bonferroni reported; plot-mean ANOVA as a check", "Keeps only bands where class means differ; removes uninformative bands before selection", "Das et al. 2020; Tukey 1949; Benjamini & Hochberg 1995; Hurlbert 1984"],
    ["2a · CART", "rpart-equivalent tree (Gini, minsplit 20, minbucket 7, cp 0.01) on the significant bands; bands used in splits are kept", "Picks a small set of complementary bands; same settings as the paper", "Breiman et al. 1984; Therneau & Atkinson (rpart)"],
    ["2b · RF", "Random Forest (500 trees, mtry = √p) importance ranking; top bands with |r| < 0.95; same number of bands as CART", "Comparison requested: a more stable, ensemble-based band ranking", "Breiman 2001; Strobl et al. 2008"],
    ["3 · J–M", "Jeffries–Matusita distance JM = 2(1 − e^−B) per band and for the selected set; 1.94 threshold", "Measures how separable the classes are on the chosen bands (0 = none, 2 = complete)", "Richards 2013; Das et al. 2020"],
    ["4 · QDA", "Quadratic discriminant analysis on the selected bands", "Classifier used in the paper; allows a different covariance per class", "Das et al. 2020"],
  ], MX, 1.45, CW, [1.35, 4.4, 3.6, 2.78], { fontSize: 12, rowH: [0.42, 0.95, 0.85, 0.85, 0.8, 0.6] });
  caption(s, "Das et al. (2020) used 14 rice genotypes; here there are 2 classes, so Tukey HSD tests one pair and gives the same decision as the ANOVA (checked at every band).", MX, 6.3, CW, 0.5);
}

{
  const s = slide("CONTENT", `Why class imbalance matters (1 : ${f2(D.nD / D.nH, 2)})`);
  card(s, MX, 1.5, 5.9, 5.1, "The problem", [
    `${D.nD} diseased vs ${D.nH} healthy spectra: a model that calls everything “diseased” already reaches ${pct(D.nD / D.N)} overall accuracy`,
    "Trees and QDA (with empirical priors) are pulled towards the majority class: healthy plots are under-detected",
    "Overall accuracy is therefore misleading; balanced accuracy, MCC, kappa and per-class F1 are reported instead",
    "Imbalance handling must be fitted on training folds only, or the test result is optimistic",
  ], HX.lt2, 14.5);
  card(s, 6.73, 1.5, 6.0, 5.1, "References", [
    "He & Garcia (2009) IEEE TKDE: review of imbalanced learning; why accuracy misleads",
    "Brodersen et al. (2010) ICPR: balanced accuracy",
    "Chicco & Jurman (2020) BMC Genomics: MCC for imbalanced binary problems",
    "Santos et al. (2018) IEEE CIM: re-sample inside the cross-validation, never before",
  ], "FDF3E7", 14.5);
}

{
  const s = slide("CONTENT", "Four imbalance strategies compared");
  table(s, [
    ["Strategy", "How it is applied (training folds only)", "Why", "Method reference", "Used for imbalance in"],
    ["S0 No correction", "Data as is; QDA with empirical priors", "Baseline, as in Das et al.", "Das et al. 2020", "—"],
    ["S1 Class weighting (cost-sensitive)", "Weight N/(2n_k) per class in CART (= rpart prior) and RF (class_weight = balanced); QDA equal priors", "Keeps every spectrum; no synthetic data", "Breiman et al. 1984; Chen, Liaw & Breiman 2004", "Chen et al. 2004 (weighted RF); He & Garcia 2009"],
    ["S2 Random under-sampling", "Diseased training spectra randomly reduced to the healthy count", "Simple; removes majority dominance", "He & Garcia 2009; Lemaître et al. 2017", "Chen et al. 2004 (balanced RF)"],
    ["S3 SMOTE", "Synthetic healthy spectra by interpolation between 5 nearest healthy neighbours", "Adds minority information without discarding data", "Chawla et al. 2002; Lemaître et al. 2017", "Cuenca-Romero et al. 2024 (wheat rust, hyperspectral); Douzas et al. 2019 (land cover)"],
  ], MX, 1.45, CW, [2.05, 3.65, 2.2, 2.0, 2.23], { fontSize: 11.5, rowH: [0.42, 0.55, 1.0, 0.8, 1.0] });
  caption(s, "S1 class weights: healthy 1417/(2·358) ≈ 1.98, diseased 1417/(2·1059) ≈ 0.67 (on the full data; recomputed in each training fold). The test spectra are never re-sampled.", MX, 5.45, CW, 0.5);
  body(s, [
    "Cuenca-Romero et al. (2024) used SMOTE on imbalanced hyperspectral data to detect yellow and brown rust in wheat: a direct plant-disease example",
    "Douzas et al. (2019) used SMOTE-type over-sampling for imbalanced land-cover classes in remote sensing",
  ], MX, 5.95, CW, 0.95, 13);
}

{
  const s = slide("CONTENT", "Validation design and why");
  steps(s, [
    ["V1 · Paper-style random 10-fold (× 5)", "As in Das et al.: bands chosen once on all data, then QDA cross-validated on randomly split spectra. Reported for comparison only: it is optimistic because spectra of the same plot fall in training and test, and the bands were chosen with the test spectra."],
    ["V2 · Plot-grouped nested 4-fold (× 10) — main result", "Whole plots are held out (3 healthy + 9 diseased per test fold). Tier 1, Tier 2, re-sampling and QDA are all redone inside each training fold. Repeated 10 times with different plot splits."],
    ["V3 · Leave-one-plot-out (48 folds)", "Each plot predicted by a model built on the other 47 plots; a plot is called diseased if > 50% of its spectra are. Shows which plots are misclassified."],
    ["Permutation test (100 ×)", "Plot labels shuffled (12 healthy / 36 diseased kept) and V2 repeated: tells whether the observed balanced accuracy is better than chance."],
  ], MX, 1.45, 2, 5.98, 2.45, 0.17, 0.17, 15, 13);
  caption(s, "References: Hurlbert 1984 (pseudo-replication); Roberts et al. 2017 (grouped/block CV); Ambroise & McLachlan 2002 (selection inside the folds); Santos et al. 2018 (re-sampling inside the folds); Ojala & Garriga 2010 (permutation test).", MX, 6.55, CW, 0.4);
}

{
  const s = slide("CONTENT", "Accuracy measures reported");
  table(s, [
    ["Measure", "Definition", "Why", "Reference"],
    ["Balanced accuracy (BA) — main", "(sensitivity + specificity) / 2", "Not inflated by the majority class; 0.5 = chance", "Brodersen et al. 2010"],
    ["Sensitivity / specificity", "Correct diseased / correct healthy", "Shows which class fails", "He & Garcia 2009"],
    ["MCC", "Correlation of observed and predicted classes", "Uses all four cells; robust to imbalance", "Chicco & Jurman 2020"],
    ["Kappa", "Agreement beyond chance", "Used in remote sensing and by Das et al.", "Cohen 1960"],
    ["F1 per class, ROC-AUC", "Precision–recall balance; ranking quality", "Complementary views", "He & Garcia 2009"],
    ["Plot-level BA", "Majority vote of a plot's spectra vs its true class", "Plots are the real units of interest", "Hurlbert 1984"],
    ["Overall accuracy (OA)", "Correct / total", "Reported only for comparison with the paper", "Das et al. 2020"],
  ], MX, 1.45, CW, [2.9, 3.6, 3.7, 1.93], { fontSize: 12.5, rowH: 0.56 });
}

// ================================================================== PART C RESULTS
newSection("C. Results");
slide("SECTION", "C · Results, tier by tier", "Tier 1 → Tier 2 (CART and RF) → Tier 3 → Tier 4, then validation");

{
  const s = slide("CONTENT", `Tier 1 · ${t1.sig} of ${D.P} bands differ at p < 0.05`);
  img(s, "f06_tier1.png", MX, 1.3, 7.6, 5.6, "Tier 1 ANOVA results");
  card(s, 8.4, 1.45, 4.33, 5.3, "What Tier 1 shows", [
    `${t1.sig} bands significant with all spectra as replicates; ${t1.fdr} after FDR and ${t1.bonf} after Bonferroni`,
    `Tukey HSD gives the same ${t1.sig} bands (one pair)`,
    `Effect sizes are small: largest |d| = ${f2(t1.dmax)} (${t1.wl_dmax.toFixed(0)} nm); ${t1.n_d_medium} bands |d| ≥ 0.5, ${t1.n_d_large} bands |d| ≥ 0.8`,
    `With the 48 plot means as replicates only ${t1.plotmean} bands are significant: the spectrum-level test is inflated by pseudo-replication`,
  ], HX.lt2, 13.5);
}

{
  const s = slide("CONTENT", "Tier 1 · how robust is the band list?");
  table(s, [
    ["Test", "Replicates", "Bands significant (of 483)", "Use"],
    ["One-way ANOVA, p < 0.05", `${D.N} spectra`, String(t1.sig), "Passed to Tier 2 (as in Das et al.)"],
    ["Tukey HSD, p < 0.05", `${D.N} spectra`, String(t1.sig), "Identical decision (one pair)"],
    ["ANOVA + FDR (Benjamini–Hochberg)", `${D.N} spectra`, String(t1.fdr), "Controls false discoveries over 483 tests"],
    ["ANOVA + Bonferroni", `${D.N} spectra`, String(t1.bonf), "Strictest control"],
    ["Welch t-test (unequal variances)", `${D.N} spectra`, String(t1.welch), `Levene: variances differ at ${t1.levene} bands`],
    ["ANOVA on plot means", "48 plots", String(t1.plotmean), "Pseudo-replication check (Hurlbert 1984)"],
  ], MX, 1.5, CW, [3.6, 1.9, 2.6, 4.03], { fontSize: 13.5, rowH: 0.52 });
  body(s, [
    "The band list is stable across tests that use spectra as replicates; with plots as replicates fewer bands remain, so p-values from spectra overstate the evidence",
    "Inside every validation fold Tier 1 is recomputed on the training spectra only",
  ], MX, 5.35, CW, 1.4, 14.5);
}

{
  const s = slide("CONTENT", "Tier 2a · CART tree (class-weighted, S1)");
  img(s, "f07_tree.png", MX, 1.3, CW, 5.2, "CART tree");
  caption(s, `Tree grown on all ${D.N} spectra with class weights (S1), pruned at cp = 0.01: ${K("CART", "S1").nodes} splits on ${K("CART", "S1").k} bands. Boxes: split rule (R = reflectance at that wavelength); leaves: predicted class and healthy | diseased spectra. The first split (R2380 ≤ 0.0001) isolates 241 spectra with zero or negative reflectance at 2,380 nm, 238 of them diseased: the tree exploits the noisy edge band.`, MX, 6.55, CW);
}

{
  const s = slide("CONTENT", "Tier 2a · CART bands for each imbalance strategy");
  table(s, [["Strategy", "Bands", "Selected wavelengths (nm)", "Edge bands*"],
    ...S.map((st) => { const c = K("CART", st); return [SN[st], c.k, c.bands.map((b) => b.toFixed(0)).join(", "), nEdge(c)]; })],
    MX, 1.45, CW, [2.3, 0.9, 7.6, 1.33], { fontSize: 12.5, rowH: [0.4, 0.8, 0.8, 0.8, 0.8] });
  body(s, [
    "The selected bands change with the imbalance strategy: individual bands should not be over-interpreted",
    "Recurring regions: blue/green (≈ 400–500 nm), red-edge/NIR (≈ 700–950 nm) and SWIR-2 (≈ 2,000–2,400 nm)",
    "* Edge bands < 420 or > 2,350 nm are kept as requested but are the noisiest part of the sensor",
  ], MX, 5.6, CW, 1.3, 14);
}

{
  const s = slide("CONTENT", "Tier 2b · Random Forest instead of CART");
  img(s, "f10_rf_importance.png", MX, 1.25, CW, 2.95, "RF importance");
  table(s, [["Strategy", "Bands", "RF-selected wavelengths (nm), in order of importance"],
    ...S.map((st) => { const c = K("RF", st); return [SN[st], c.k, c.bands.map((b) => b.toFixed(0)).join(", ")]; })],
    MX, 4.3, CW, [2.3, 0.9, 8.93], { fontSize: 11.5, rowH: 0.42 });
  caption(s, "RF ranks all ANOVA-significant bands; neighbours with |r| ≥ 0.95 to an already chosen band are skipped (Strobl et al. 2008) so that the same number of bands as CART is kept.", MX, 6.5, CW);
}

{
  const s = slide("CONTENT", "Which bands were selected? CART vs RF");
  img(s, "f08_bands.png", MX, 1.3, CW, 4.8, "Band selection matrix");
  caption(s, "Each row is one configuration (Tier-2 method × imbalance strategy); ticks are the selected wavelengths on the full data. Background: −log10 p of Tier 1.", MX, 6.25, CW, 0.5);
}

{
  const s = slide("CONTENT", "Tier 3 · Jeffries–Matusita distance");
  img(s, "f09_jm.png", MX, 1.3, 7.8, 3.6, "J-M distance");
  table(s, [["Configuration", "Bands", "JM (0–2)"],
    ...allCfg.map((c) => [lab(c), c.k, { text: f2(c.JM, 3), options: { bold: c === jmBest } }])],
    8.6, 1.4, 4.13, [2.0, 0.9, 1.23], { fontSize: 12, rowH: 0.4 });
  body(s, [
    `No configuration reaches the 1.94 threshold of Das et al.: the best is ${lab(jmBest)} with JM = ${f2(jmMax, 3)}`,
    `The best single band reaches only JM = ${f2(D.jm_band_max, 3)} (${D.wl_jm_max.toFixed(0)} nm)`,
    "Healthy and diseased endmembers overlap strongly in spectral space",
  ], MX, 5.1, 7.8, 1.75, 14);
}

{
  const s = slide("CONTENT", "Tier 4 · QDA with paper-style validation (V1)");
  table(s, [["Tier 2", ...S.map((st) => SN[st])],
    ...T2.map((t) => [t, ...S.map((st) => `${f2(K(t, st).v1.BA[0], 3)} (OA ${pct(K(t, st).v1.OA[0], 1)})`)])],
    MX, 1.5, CW, [1.6, 2.63, 2.63, 2.63, 2.64], { fontSize: 14, rowH: 0.55 });
  body(s, [
    `Balanced accuracy (overall accuracy in brackets); random stratified 10-fold × 5, bands chosen once on all spectra, as in Das et al. (2020)`,
    `Best: ${lab(v1best)}, BA ${f2(v1max, 3)}. This scheme is optimistic: spectra of one plot are in both training and test sets, and the bands were selected with the test spectra (Ambroise & McLachlan 2002)`,
    "The realistic estimate is the plot-grouped nested validation on the next slides",
  ], MX, 3.4, CW, 3.3, 15);
}

{
  const s = slide("CONTENT", "Main result · plot-grouped nested validation (V2)");
  const labels = allCfg.map(lab).concat(["RF all bands"]);
  s.addChart(pres.charts.BAR, [
    { name: "Spectrum-level BA", labels, values: allCfg.map((c) => +c.v2.BA[0].toFixed(3)).concat([+D.bench.BA[0].toFixed(3)]) },
    { name: "Plot-level BA", labels, values: allCfg.map((c) => +c.v2plot.BA[0].toFixed(3)).concat([+D.bench.plotBA[0].toFixed(3)]) },
  ], {
    x: MX, y: 1.35, w: 8.2, h: 5.4, barDir: "col", barGrouping: "clustered", chartColors: [HX.accent3, HX.accent4],
    valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.25, valAxisLabelFormatCode: "0.00", valAxisTitle: "Balanced accuracy", showValAxisTitle: true,
    valAxisTitleFontSize: 11, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, showLegend: true, legendPos: "b", legendFontSize: 11,
    showValue: true, dataLabelFontSize: 8, dataLabelFormatCode: "0.00", valGridLine: { color: "E4E3DF", size: 0.5 }, catGridLine: { style: "none" },
    objectName: "BA chart",
  });
  card(s, 9.0, 1.45, 3.73, 5.3, "Reading the chart", [
    "0.5 = chance for balanced accuracy",
    `Spectrum level: ${f2(Math.min(...allCfg.map((c) => c.v2.BA[0])), 2)}–${f2(Math.max(...allCfg.map((c) => c.v2.BA[0])), 2)}; best ${lab(topV2)}`,
    `Plot level (majority vote): best ${lab(topPlot)} at ${f2(topPlot.v2plot.BA[0], 2)}`,
    "Imbalance correction (S1–S3) clearly helps at plot level compared with S0",
    `RF on all ${D.P} bands as benchmark: ${f2(D.bench.BA[0], 2)} / ${f2(D.bench.plotBA[0], 2)}`,
  ], HX.lt2, 13);
}

{
  const s = slide("CONTENT", "V2 in detail (mean ± SD over 10 repetitions)");
  const rows = [["Config.", "BA", "Kappa", "MCC", "Sensitivity (D)", "Specificity (H)", "AUC", "Plot BA", "Bands/fold"]];
  for (const c of allCfg) rows.push([{ text: lab(c), options: { bold: c === topV2 } }, pm(c.v2.BA, 3), pm(c.v2.kappa, 2), pm(c.v2.MCC, 2), pm(c.v2.sens_D, 2), pm(c.v2.spec_H, 2), pm(c.v2.AUC, 2), pm(c.v2plot.BA, 2), f2(c.v2_kfold, 1)]);
  rows.push(["RF all bands", pm(D.bench.BA, 3), pm(D.bench.kappa, 2), pm(D.bench.MCC, 2), pm(D.bench.sens_D, 2), pm(D.bench.spec_H, 2), pm(D.bench.AUC, 2), pm(D.bench.plotBA, 2), String(D.P)]);
  table(s, rows, MX, 1.45, CW, [1.45, 1.4, 1.3, 1.3, 1.45, 1.45, 1.3, 1.35, 1.13], { fontSize: 11.5, rowH: 0.44 });
  caption(s, "Tier 1, Tier 2, re-sampling and QDA refitted in every training fold; test plots never seen. D = diseased, H = healthy. The RF benchmark is a class-weighted RF classifier on all bands (no Tier 1–3).", MX, 6.05, CW, 0.6);
}

{
  const s = slide("CONTENT", "Are the same bands chosen in every fold?");
  table(s, [["Band (nm)", `${lab(bestC)}: share of folds`, "Band (nm)", `${lab(bestR)}: share of folds`],
    ...bestC.v2_stable.map((b, i) => [f2(b[0], 1), pct(b[1], 0), bestR.v2_stable[i] ? f2(bestR.v2_stable[i][0], 1) : "", bestR.v2_stable[i] ? pct(bestR.v2_stable[i][1], 0) : ""])],
    MX, 1.5, 7.2, [1.6, 2.0, 1.6, 2.0], { fontSize: 13, rowH: 0.45 });
  card(s, 8.1, 1.5, 4.63, 4.9, "Stability of band selection", [
    "40 training folds (4 folds × 10 repetitions) per configuration",
    `${lab(bestC)} and ${lab(bestR)} are the best-performing strategies of each Tier-2 method in V2`,
    "Even the most frequent bands are chosen in only part of the folds: the band set depends on which plots are in the training set",
    "Report regions (blue, red-edge/NIR, SWIR-2) rather than single wavelengths",
  ], HX.lt2, 13.5);
}

{
  const s = slide("CONTENT", "Leave-one-plot-out (V3): which plots are misclassified?");
  img(s, "f11_lopo_CART.png", MX, 1.3, 4.6, 4.2, "LOPO CART map");
  img(s, "f11_lopo_RF.png", 5.3, 1.3, 4.6, 4.2, "LOPO RF map");
  const c3 = K("CART", D.best.CART).v3, r3 = K("RF", D.best.RF).v3;
  card(s, 10.1, 1.4, 2.63, 4.1, "Plot level", [
    `${lab(bestC)}: ${c3.correct}/48 plots, plot BA ${f2(c3.plotBA, 2)}`,
    `${lab(bestR)}: ${r3.correct}/48 plots, plot BA ${f2(r3.plotBA, 2)}`,
    `Best plot BA of 8: ${lab(topV3)} ${f2(topV3.v3.plotBA, 2)}`,
    `S0 looks good on plots correct (CART ${K("CART", "S0").v3.correct}/48) only because it calls nearly all plots diseased`,
  ], HX.lt2, 12);
  table(s, [["Configuration", "Spectrum BA", "Plot BA", "Healthy plots wrong", "Diseased plots wrong"],
    ...[bestC, bestR].map((c) => [lab(c), f2(c.v3.BA, 3), f2(c.v3.plotBA, 3), c.v3.wrongH.join(", ") || "none", c.v3.wrongD.length > 12 ? `${c.v3.wrongD.length} plots` : (c.v3.wrongD.join(", ") || "none")])],
    MX, 5.6, CW, [2.0, 1.5, 1.4, 3.3, 3.93], { fontSize: 11.5, rowH: 0.38 });
}

{
  const s = slide("CONTENT", "Permutation test: better than chance?");
  img(s, "f12_permutation.png", MX, 1.35, 7.2, 3.6, "Permutation null distributions");
  table(s, [["Tier 2", "Strategy", "Observed BA", "Null mean", "Null 95%", "p"],
    ...["CART", "RF"].map((t) => { const p = D.perm[t]; return [t, p.strategy, f2(p.observed, 3), f2(p.null_mean, 3), f2(p.q95, 3), f2(p.p, 3)]; })],
    8.0, 1.5, 4.73, [0.7, 0.8, 0.95, 0.8, 0.8, 0.68], { fontSize: 11.5, rowH: 0.5 });
  body(s, [
    `Plot labels were shuffled ${pc.n} times (12 healthy / 36 diseased kept) and the full nested pipeline rerun (one 4-fold repetition each)`,
    `Observed = balanced accuracy of V2 repetition 1 with the true labels. CART: p = ${f2(pc.p, 3)}; RF: p = ${f2(pr.p, 3)} (smallest possible p with ${pc.n} permutations = ${f2(1 / (pc.n + 1), 3)})`,
    `Because whole plots are permuted, this tests the plot-level class difference (Ojala & Garriga 2010). In ${D.no_bands_perm} of 800 permuted folds Tier 1 found no significant band; these folds predict by prior (BA 0.5), as the pipeline would`,
  ], MX, 5.1, CW, 1.7, 14);
}

{
  const s = slide("CONTENT", "Comparison: CART vs RF in Tier 2 and the imbalance strategies");
  const rows = [["Configuration", "Bands", "JM", "V1 BA (paper-style)", "V2 BA (plot-grouped)", "V2 plot BA", "V3 plot BA (plots correct)"]];
  for (const c of allCfg) rows.push([lab(c), c.k, f2(c.JM, 3), f2(c.v1.BA[0], 3), f2(c.v2.BA[0], 3), f2(c.v2plot.BA[0], 3), `${f2(c.v3.plotBA, 2)} (${c.v3.correct}/48)`]);
  table(s, rows, MX, 1.45, 8.0, [1.35, 0.75, 0.9, 1.25, 1.3, 1.2, 1.25], { fontSize: 12, rowH: 0.44 });
  const dV = allCfg.map((c) => c.v1.BA[0] - c.v2.BA[0]);
  card(s, 8.85, 1.45, 3.88, 5.3, "What the comparison shows", [
    `Paper-style CV is optimistic by up to ${f2(Math.max(...dV), 2)} BA compared with plot-grouped CV`,
    `CART vs RF in Tier 2: best V2 BA ${f2(bestC.v2.BA[0], 3)} (CART) vs ${f2(bestR.v2.BA[0], 3)} (RF): no clear winner`,
    "S0 (no correction) gives the weakest plot-level result: healthy plots are missed",
    "S1/S2/S3 perform similarly; S1 (class weights) needs no synthetic or discarded data",
    `RF classifier on all ${D.P} bands with class weights only: BA ${f2(D.bench.BA[0], 2)}, plot BA ${f2(D.bench.plotBA[0], 2)}: it still favours the majority class`,
  ], HX.lt2, 13);
}

{
  const s = slide("CONTENT", "Every step was cross-checked");
  const groups = {};
  for (const r of D.checks.rows) (groups[r[0]] = groups[r[0]] || []).push(r);
  const ex = {
    Data: "1417 × 483; plots 1–12 healthy; no missing values; unique spectra",
    "Tier 1": "manual F = scipy; Tukey = ANOVA decision at all bands",
    Imbalance: "under-sampling and SMOTE give equal class counts",
    "Tier 2": "class weights equalise the root; custom tree = sklearn; bands ⊂ significant set",
    "Tier 3": "1-D closed-form J–M = matrix form",
    Validation: "no plot in training and test; SMOTE on training only; permutation nulls ≈ 0.5",
    "Tier 4": "hand-coded QDA = sklearn; BA = (sens + spec)/2; confusion matrix total = N",
  };
  const rows = [["Step", "Checks", "What was checked", "Result"]];
  for (const [k, v] of Object.entries(groups)) rows.push([k, v.length, ex[k] || "", { text: v.every((c) => c[3] === "PASS") ? "PASS" : "FAIL", options: { bold: true, color: v.every((c) => c[3] === "PASS") ? "008000" : "C00000" } }]);
  rows.push(["Excel ↔ Python", "live", "ANOVA F and p, weights, J–M, confusion-matrix BA/kappa/MCC recomputed by Excel formulas", { text: "PASS", options: { bold: true, color: "008000" } }]);
  table(s, rows, MX, 1.45, CW, [2.0, 1.0, 7.93, 1.2], { fontSize: 12.5, rowH: 0.45 });
  caption(s, `${D.checks.passed} of ${D.checks.n} Python checks pass; live Excel checks in sheet 14_Cross_Checks of Four_Tier_48plots.xlsx. QDA needed the ridge fallback in ${D.fallbacks} fits.`, MX, 6.45, CW);
}

// ================================================================== DISCUSSION / SUMMARY / CONCLUSION
newSection("D. Discussion and conclusion");
slide("SECTION", "D · Discussion, summary and conclusion", "What the results mean, their limits, and what to do next");

{
  const s = slide("CONTENT", "Discussion");
  steps(s, [
    ["Weak to moderate separation", `JM ≤ ${f2(jmMax, 2)} (threshold 1.94) and plot-grouped BA ${f2(Math.min(...allCfg.map((c) => c.v2.BA[0])), 2)}–${f2(topV2.v2.BA[0], 2)}, far below the 98% of Das et al. Their samples were averaged field spectra of uniform plots; here single SMACC endmembers mix leaves, lesions, soil and shadow.`],
    ["Pseudo-replication", `${t1.sig} bands are significant with spectra as replicates but only ${t1.plotmean} with plot means. Spectra of one plot are not independent, so plot-grouped validation is the honest estimate (Hurlbert 1984; Roberts et al. 2017).`],
    ["Imbalance handling helps at plot level", `Without correction the minority (healthy) class is under-predicted. Class weighting, under-sampling and SMOTE all raise plot-level BA (best ${f2(topPlot.v2plot.BA[0], 2)}); applied inside folds only (Santos et al. 2018).`],
    ["CART vs RF in Tier 2", `Similar performance (V2 BA ${f2(bestC.v2.BA[0], 3)} vs ${f2(bestR.v2.BA[0], 3)}). RF ranking is more stable in principle; CART picks complementary bands. The bands change from fold to fold for both.`],
    ["Location confound", "All healthy plots are at the west end of the field. Part of any difference may be position (soil, illumination, sowing), not disease. Leave-one-plot-out errors should be inspected in the field."],
    ["All wavelengths kept", `Edge bands (< 420, > 2,350 nm) and negative reflectance are retained as requested; some selected bands lie there (${lab(K("CART", "S1"))}: ${nEdge(K("CART", "S1"))} edge bands). CART's first split uses near-zero/negative R2380. The ≈ 918–921 nm bands, chosen in most RF folds, sit just after the 899–916 nm gap where Tier 1 shows a narrow spike: check for a sensor artefact.`],
  ], MX, 1.4, 2, 5.98, 1.68, 0.17, 0.12, 14.5, 12);
}

{
  const s = slide("CONTENT", "Summary");
  const items = [
    [String(D.N), `endmember spectra (${D.nH} healthy, ${D.nD} diseased) × ${D.P} bands, all kept separately`],
    [String(t1.sig), `bands significant in Tier 1 (only ${t1.plotmean} with plot means)`],
    [`${K("CART", "S1").k} / ${K("CART", "S0").k}`, "CART bands with / without class weights; RF selects the same number"],
    [f2(jmMax, 2), `highest J–M distance (${lab(jmBest)}), below the 1.94 threshold`],
    [f2(topV2.v2.BA[0], 2), `best plot-grouped balanced accuracy (${lab(topV2)}); paper-style up to ${f2(v1max, 2)}`],
    [f2(topPlot.v2plot.BA[0], 2), `best plot-level balanced accuracy (${lab(topPlot)}); permutation p = ${f2(D.perm[topPlot.t2].p, 3)}`],
  ];
  items.forEach(([v, l], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = MX + col * 4.1, y = 1.5 + row * 2.65;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 3.9, h: 2.4, fill: { color: HX.lt2 }, line: { color: HX.lt2 }, rectRadius: 0.08, objectName: "summary " + (i + 1) });
    s.addText(v, { x: x + 0.25, y: y + 0.2, w: 3.4, h: 0.85, fontSize: 38, bold: true, color: C.text2, margin: 0, isTextBox: true, fontFace: THEME.headFontFace, valign: "bottom" });
    s.addText(l, { x: x + 0.25, y: y + 1.15, w: 3.45, h: 1.15, fontSize: 14, color: C.text1, margin: 0, isTextBox: true, valign: "top" });
  });
}

{
  const s = slide("CLOSING", "Conclusion");
  const pts = [
    `The four-tier method of Das et al. (2020) was applied to all ${D.N} endmembers of 48 plots and all ${D.P} bands, with Random Forest replacing CART in Tier 2 for comparison and four ways of handling the 1 : ${f2(D.nD / D.nH, 2)} imbalance.`,
    `Healthy and diseased spectra differ statistically, but separability is low (JM ≤ ${f2(jmMax, 2)}) and realistic plot-grouped balanced accuracy is ${f2(topV2.v2.BA[0], 2)} at best (plot level ${f2(topPlot.v2plot.BA[0], 2)}).`,
    "Imbalance correction is needed: class weighting (S1) is the simplest choice that keeps all data; CART and RF in Tier 2 perform similarly.",
    "Paper-style random cross-validation overstates accuracy; plots must be the validation unit. Next steps: plot-level ground truth, plots of both classes across the whole field, and an independent date.",
  ];
  s.addText(pts.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < pts.length - 1, paraSpaceAfter: 12 } })),
    { x: MX, y: 1.55, w: CW, h: 5.2, fontSize: 18, color: HX.lt1, margin: 0, isTextBox: true, valign: "middle" });
}

{
  const half = Math.ceil(D.refs.length / 2);
  [D.refs.slice(0, half), D.refs.slice(half)].forEach((part, k) => {
    const s = slide("CONTENT", `References (${k + 1}/2)`);
    s.addText(part.map((r, i) => ({ text: r[1], options: { bullet: true, breakLine: i < part.length - 1, paraSpaceAfter: 5 } })),
      { x: MX, y: 1.35, w: CW, h: 5.5, fontSize: 11.5, color: C.text1, margin: 0, isTextBox: true, valign: "top" });
  });
}

pres.writeFile({ fileName: OUT }).then(async () => {
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
});
