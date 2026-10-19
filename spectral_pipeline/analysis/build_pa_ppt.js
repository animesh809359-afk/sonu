// Deck for the plot-average analysis (192 plot-average spectra, all dates combined): four tiers on raw reflectance
// (CART and Random Forest), disease-sensitive features from raw reflectance, four tiers on the combined feature pool.
// usage: node build_pa_ppt.js <work dir with results.json and figures/> <out.pptx>
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const WORK = process.argv[2];
const OUT = process.argv[3];
const J = JSON.parse(fs.readFileSync(path.join(WORK, "results.json"), "utf8"));
const FIG = path.join(WORK, "figures");

const THEME = {
  name: "White rust mustard",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: { dk1: "1B1B1A", lt1: "FFFFFF", dk2: "1F3D2B", lt2: "EEF3EF", accent1: "2A78D6", accent2: "EB6834",
            accent3: "1BAF7A", accent4: "D9A21B", accent5: "2A5A3C", accent6: "52514E", hlink: "2A78D6", folHlink: "52514E" },
};
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "White rust of mustard — plot-average four-tier analysis";
pres.author = "Animesh Panda";
const C = pres.SchemeColor;
const W = 13.33, H = 7.5, M = 0.55;

pres.defineSlideMaster({
  title: "TITLE", background: { color: THEME.colors.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.0, w: W - 2 * M, h: 1.9, fontFace: THEME.headFontFace, fontSize: 38, bold: true, color: "FFFFFF", valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.05, w: W - 2 * M, h: 2.2, fontFace: THEME.bodyFontFace, fontSize: 18, color: "CFE3D5", valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION", background: { color: THEME.colors.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.6, w: W - 2 * M, h: 1.2, fontFace: THEME.headFontFace, fontSize: 36, bold: true, color: "FFFFFF", valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 3.95, w: W - 2 * M, h: 1.6, fontFace: THEME.bodyFontFace, fontSize: 18, color: "CFE3D5", valign: "top" }, text: "" } },
  ],
  slideNumber: { x: W - 1.0, y: H - 0.45, fontFace: THEME.bodyFontFace, fontSize: 10, color: "CFE3D5" },
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.3, w: W - 2 * M, h: 0.85, fontFace: THEME.headFontFace, fontSize: 28, bold: true, color: THEME.colors.dk2, valign: "middle" }, text: "" } },
    { text: { text: "White rust of mustard · plot-average spectra, all dates combined", options: { x: M, y: H - 0.42, w: 8, h: 0.3, fontFace: THEME.bodyFontFace, fontSize: 10, color: "52514E" } } },
  ],
  slideNumber: { x: W - 1.0, y: H - 0.42, fontFace: THEME.bodyFontFace, fontSize: 10, color: "52514E" },
});

// ---------------------------------------------------------------- helpers
function pngSize(f) { const b = fs.readFileSync(f); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }
function img(slide, name, x, y, w, h, alt) {
  const f = path.join(FIG, name);
  if (!fs.existsSync(f)) { console.warn("missing figure", name); return; }
  const d = pngSize(f);
  let ww = w, hh = w * d.h / d.w;
  if (hh > h) { hh = h; ww = h * d.w / d.h; }
  slide.addImage({ path: f, x: x + (w - ww) / 2, y: y + (h - hh) / 2, w: ww, h: hh, altText: alt || name, objectName: name });
}
function cap(slide, text, x, y, w, h = 0.35) {
  slide.addText(text, { x, y, w, h, fontSize: 11, italic: true, color: "52514E", isTextBox: true, margin: 0, valign: "top" });
}
function para(slide, text, x, y, w, h, size = 15) {
  const runs = Array.isArray(text) ? text : [text];
  slide.addText(runs.map((t, i) => ({ text: t, options: { breakLine: i < runs.length - 1, paraSpaceAfter: 6 } })),
    { x, y, w, h, fontSize: size, color: "1B1B1A", isTextBox: true, valign: "top", margin: 0.05 });
}
function bullets(slide, items, x, y, w, h, size = 15) {
  slide.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } })),
    { x, y, w, h, fontSize: size, color: "1B1B1A", isTextBox: true, valign: "top", margin: 0.05 });
}
function table(slide, rows, x, y, w, opts = {}) {
  const fsz = opts.fontSize || 12;
  const body = rows.map((r, i) => r.map((c) => ({
    text: String(c),
    options: i === 0
      ? { bold: true, color: "FFFFFF", fill: { color: THEME.colors.dk2 }, fontSize: fsz, valign: "middle" }
      : { color: "1B1B1A", fill: { color: i % 2 ? "FFFFFF" : "EEF3EF" }, fontSize: fsz, valign: "middle",
          bold: opts.boldRows && opts.boldRows.includes(i) },
  })));
  slide.addTable(body, { x, y, w, colW: opts.colW, border: { type: "solid", pt: 0.5, color: "C9C8C1" }, margin: 0.04,
    rowH: opts.rowH || 0.3, autoPage: false });
}
function stat(slide, big, small, x, y, w, col) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.55, fill: { color: "EEF3EF" }, line: { color: "EEF3EF" }, rectRadius: 0.08, objectName: "stat card" });
  slide.addText(big, { x, y: y + 0.12, w, h: 0.85, fontSize: 40, bold: true, color: col || THEME.colors.dk2, align: "center", isTextBox: true, fontFace: THEME.headFontFace });
  slide.addText(small, { x: x + 0.1, y: y + 0.95, w: w - 0.2, h: 0.5, fontSize: 13, color: "52514E", align: "center", isTextBox: true });
}
let section = "";
function sectionSlide(title, sub) {
  section = title;
  pres.addSection({ title });
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: title });
  s.addText(title, { placeholder: "title" });
  s.addText(sub, { placeholder: "body" });
  return s;
}
function content(title) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
}
const VN = { V1: "Spectrum-level 10-fold cross-validation (protocol of Das et al.)", V2: "Plot-grouped cross-validation",
             V3: "Nested plot-grouped cross-validation", V4: "30 % plot hold-out validation", V5: "Leave-one-date-out validation on new plots" };
const VS = { V1: "Spectrum-level 10-fold", V3: "Nested plot-grouped", V4: "30 % plot hold-out", V5: "Leave-one-date-out" };
const pct = (v) => (v == null ? "–" : (100 * v).toFixed(1) + " %");
const PIPES = ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"];
const PN = { "CART classifier": "CART classifier", "RF classifier": "Random Forest classifier", "QDA on CART features": "QDA on CART bands", "QDA on RF features": "QDA on Random Forest bands" };
const valRows = (blk) => [["Pipeline", VS.V1, VS.V3, VS.V4, VS.V5],
  ...PIPES.map((p) => [PN[p], ...["V1", "V3", "V4", "V5"].map((s) => pct(blk.v[`${p}|${s}`].BA))])];
const em = (m) => [["Classified \\ Reference", "Healthy", "Diseased", "User's accuracy"],
  ["Healthy", m.HH, m.DH, pct(m.HH / (m.HH + m.DH))], ["Diseased", m.HD, m.DD, pct(m.DD / (m.HD + m.DD))],
  ["Producer's accuracy", pct(m.PA_H), pct(m.PA_D), `BA ${pct(m.BA)} · κ ${(+m.kappa).toFixed(3)}`]].map((r) => r.map(String));
const A = J.A, K = J.K, CC = J.C, X = J.X, PA = J.PA, T = J.txt || {};
const DN = { D1: "first derivative", D2: "second derivative", D3: "third derivative" };
const featName = (n) => { const m = /^(D[123])_(\d+)$/.exec(n.trim()); if (m) return `${DN[m[1]]} ${m[2]} nm`; const r = /^R(\d+)$/.exec(n.trim()); return r ? `reflectance ${r[1]} nm` : n.trim(); };
const featList = (str) => str.split(",").map(featName).join("; ");
const jmA = (s) => (+A.jm[s]).toFixed(3), jmC = (s) => (+CC.jm[s]).toFixed(3);

// ================================================================ title
pres.addSection({ title: "Introduction" });
section = "Introduction";
let s = pres.addSlide({ masterName: "TITLE", sectionTitle: section });
s.addText("Discrimination of healthy and white-rust-diseased mustard from plot-average leaf spectra", { placeholder: "title" });
s.addText([
  { text: "Four-tier hierarchical analysis (Das et al., 2020) with imbalance correction · CART vs Random Forest · disease-sensitive features from raw reflectance", options: { breakLine: true } },
  { text: `${J.n} plot-average spectra (${J.nH} healthy, ${J.nD} diseased) · 48 plots × 4 dates · ASD FieldSpec contact probe, 400–2500 nm`, options: { breakLine: true } },
  { text: "Animesh Panda · Division of Agricultural Physics, ICAR-IARI, New Delhi" },
], { placeholder: "body" });

s = content("The study at a glance");
stat(s, String(J.n), "plot-average spectra (48 plots × 4 dates)", M, 1.45, 2.85);
stat(s, `${J.nH} : ${J.nD}`, "healthy : diseased (1 : " + J.ratio.toFixed(1) + ")", M + 3.05, 1.45, 2.85, C.accent2);
stat(s, String(PA ? PA.n_leaf : "–"), "leaf spectra averaged", M + 6.1, 1.45, 2.85);
stat(s, String(CC.n_features), "features in the combined pool", M + 9.15, 1.45, 2.85, C.accent4);
bullets(s, [
  "Question: which bands and which disease-sensitive features separate healthy from white-rust-diseased mustard when all dates, growth stages and varieties are combined — at the plot level?",
  "Step 1 · Four tiers of Das et al. (2020) on raw reflectance: statistical screening → CART (and Random Forest) band selection → Jeffries–Matusita separability → QDA classification.",
  "Step 2 · Disease-sensitive features from the raw reflectance (continuum removal, vegetation indices, first/second/third derivatives, red-edge parameters).",
  "Step 3 · The same four tiers on the combined pool (reflectance + all features) → disease-specific features.",
  "Every step corrected for the 1 : 3 class imbalance and validated on new plots and new dates.",
], M, 3.3, W - 2 * M, 3.6, 15);

s = content("Data: leaf spectra averaged to one spectrum per plot and date");
if (PA) table(s, PA.leaf_tab, M, 1.35, 7.0, { colW: [1.4, 1.1, 1.1, 1.1, 1.15, 1.15], fontSize: 11, rowH: 0.28 });
bullets(s, [
  `Four ASD export workbooks (11-02, 24-02, 03-03 and 13-03-2026); exact duplicate spectra removed (75 block-2 copies, 4 unnamed copies) → ${PA ? PA.n_leaf : ""} unique leaf spectra.`,
  `Plot average = mean of all leaf spectra of a plot on a date, at every band: ${J.n} spectra (${J.nH} healthy, ${J.nD} diseased).`,
  `Cross-check: ${PA ? PA.n_ok : ""} of ${PA ? PA.n_cols : ""} plot-average (=AVERAGE) columns of the source workbooks are identical to these averages at all 2151 bands.`,
  "Water-absorption bands kept (contact probe, no atmospheric path); 350–399 nm detector edge removed (noise).",
  "The same plot appears on four dates → plot-grouped validation and a random plot effect.",
], 7.8, 1.35, W - 7.8 - M, 5.4, 14);

s = content("Workflow of the analysis");
img(s, "F01_workflow.png", M, 1.25, W - 2 * M, 5.75, "Workflow");

s = content("Corrections applied to the protocol of Das et al. (2020)");
table(s, [["Issue", "Correction", "Why"],
  [`Class imbalance (${J.nH} : ${J.nD} = 1 : ${J.ratio.toFixed(1)})`, "rpart prior = (0.5, 0.5); Balanced Random Forest; QDA with equal priors; balanced accuracy; 1000 balanced subsets in Tier 1", "otherwise every model favours 'diseased'"],
  ["Two classes only", "Welch t-test instead of ANOVA + Tukey (ANOVA reported)", "unequal variances; one pair"],
  ["2101 tests", "Benjamini–Hochberg false-discovery rate (q < 0.05)", "≈ 105 false positives at α = 0.05"],
  ["Same plot on 4 dates", "mixed model with random plot effect; plot-grouped folds", "the dates of a plot are not independent"],
  ["Selection bias", "Tier 1, selection and classifier refitted in every training set", "selecting and testing on the same spectra is optimistic"],
  ["Detector joins", "guard zones (990–1010, 1795–1835 nm) excluded from the feature sets; no smoothing (features from raw reflectance)", "instrument steps must not be read as disease"],
], M, 1.35, W - 2 * M, { colW: [2.9, 6.1, 3.23], fontSize: 13, rowH: 0.62 });

s = content("Validation design — identical folds in every step");
table(s, [["Scheme", "How", "What it estimates"],
  [VN.V1, "features chosen once on all spectra; random 10 folds", "the protocol of the paper (optimistic: same plot on other dates in training)"],
  [VN.V3, "10 plot-grouped folds × 5 repeats; Tier 1, selection and classifier refitted inside each training set", "the honest accuracy for new plots"],
  [VN.V4, "4 healthy + 11 diseased plots held out × 10 splits; everything refitted", "independent test plots"],
  [VN.V5, "train on three dates (training plots), test the fourth date (test plots); 40 units", "transfer to an unseen date and unseen plots"],
], M, 1.35, W - 2 * M, { colW: [3.6, 5.3, 3.33], fontSize: 13, rowH: 0.75 });
para(s, "Balanced accuracy (BA) = ½ (recall healthy + recall diseased) is the headline metric; overall accuracy alone would be inflated by the 3 : 1 majority of diseased spectra.", M, 5.4, W - 2 * M, 1.0, 14);

// ================================================================ A: four tiers on raw reflectance
sectionSlide("Step 1 · Four tiers on raw reflectance", "Welch t-test + FDR → CART (rpart, equal priors) and Balanced Random Forest → Jeffries–Matusita distance → QDA with equal priors");

s = content("Mean plot-average spectra of healthy and diseased plots");
img(s, "F02_mean_spectra.png", M, 1.2, W - 2 * M, 3.3, "Mean spectra");
img(s, "F02b_mean_spectra_by_date.png", M, 4.55, W - 2 * M, 2.45, "Mean spectra by date");

s = content("Tier 1 · statistical screening of 2101 bands");
img(s, "F05_minus_log10_p.png", M, 1.25, 7.9, 5.6, "-log10 p against wavelength");
table(s, A.tests, 8.6, 1.35, W - 8.6 - M, { colW: [3.0, 1.18], fontSize: 11, rowH: 0.42 });
cap(s, "−log₁₀(p) of every band against wavelength (Welch, FDR-adjusted and mixed-model q). Dashed line: p = 0.05.", M, 6.75, 7.9);

s = content("Tier 1 · where the significant bands are");
table(s, A.regions, M, 1.35, 7.3, { colW: [2.3, 0.8, 1.2, 1.2, 0.9, 0.9], fontSize: 11, rowH: 0.36 });
img(s, "F03_tier1_significant_regions.png", 8.0, 1.25, W - 8.0 - M, 5.6, "Significant regions");

s = content(`Tier 2 · CART selects ${A.set_sizes[A.cart_name]} bands (rpart, prior 0.5 / 0.5)`);
img(s, "F06_cart_tree.png", M, 1.25, 8.1, 5.65, "CART tree");
para(s, [`CART bands (order of use): ${A.sets[A.cart_name]} nm.`, "Equal priors give the 48 healthy spectra the same weight as the 144 diseased ones.",
         "The bands used as split variables form the CART set passed to Tiers 3 and 4."], 8.85, 1.4, W - 8.85 - M, 5.4, 14);

s = content("Tier 2 · how stable are the CART bands?");
table(s, A.cart_table.slice(0, 14).map((r) => [r[0], r[1], r[2], r[4], r[5]]), M, 1.3, 7.4, { colW: [1.1, 2.1, 1.2, 1.5, 1.5], fontSize: 11, rowH: 0.36 });
img(s, "F08_cart_reselection.png", 8.1, 1.25, W - 8.1 - M, 5.6, "CART re-selection");

s = content(`Tier 2 · Random Forest importance: the ${A.rf_name} bands`);
img(s, "F12_A1_rf_importance.png", M, 1.25, 8.4, 5.65, "Random Forest importance");
para(s, [`${A.rf_name} (highest importance peaks ≥ 10 nm apart): ${A.sets[A.rf_name]} nm.`,
         "Balanced Random Forest: 1000 trees, each grown on a bootstrap sample with equal numbers of healthy and diseased spectra; importance = mean decrease in Gini impurity."],
     9.1, 1.4, W - 9.1 - M, 5.4, 14);

s = content("Tier 3 · Jeffries–Matusita separability");
table(s, A.tier3, M, 1.35, 5.6, { colW: [2.8, 1.2, 1.6], fontSize: 13, rowH: 0.42 });
img(s, "F09_tier3_tier4_incremental.png", 6.4, 1.25, W - 6.4 - M, 5.6, "J-M and accuracy by number of bands");
para(s, `J–M (0–2) on the CART bands = ${jmA(A.cart_name)}, on the ${A.rf_name} bands = ${jmA(A.rf_name)}; the classes count as separable at ≥ 1.90 (Das et al. used 1.94).`, M, 4.6, 5.6, 2.0, 14);

s = content("Tier 4 · QDA with equal priors");
s.addText(`CART bands (${A.cart_name})`, { x: M, y: 1.3, w: 5.9, h: 0.4, fontSize: 16, bold: true, color: THEME.colors.dk2, isTextBox: true, margin: 0 });
table(s, em(A.errmat[A.cart_name]), M, 1.75, 5.9, { colW: [2.0, 1.1, 1.1, 1.7], fontSize: 13, rowH: 0.45 });
s.addText(`Random Forest bands (${A.rf_name})`, { x: 6.9, y: 1.3, w: 5.9, h: 0.4, fontSize: 16, bold: true, color: THEME.colors.dk2, isTextBox: true, margin: 0 });
table(s, em(A.errmat[A.rf_name]), 6.9, 1.75, W - 6.9 - M, { colW: [2.0, 1.1, 1.1, 1.68], fontSize: 13, rowH: 0.45 });
para(s, "Spectrum-level 10-fold cross-validation (protocol of Das et al.). Error matrix layout of Das et al. (2020, Table 2): rows = classified, columns = reference. Producer's accuracy = recall of a class; user's accuracy = precision. Balanced accuracy and κ correct for the class imbalance.", M, 4.4, W - 2 * M, 1.2, 14);

s = content("Validation of the raw-reflectance pipelines");
table(s, valRows(A), M, 1.3, 7.2, { colW: [2.4, 1.2, 1.2, 1.2, 1.2], fontSize: 12, rowH: 0.42 });
para(s, "Balanced accuracy. Spectrum-level 10-fold reproduces the paper; nested plot-grouped and 30 % plot hold-out are honest estimates for new plots; leave-one-date-out tests transfer to an unseen date.", 7.95, 1.3, W - 7.95 - M, 2.2, 14);
img(s, "F11_validation_qda_cart.png", M, 3.6, W - 2 * M, 3.4, "Validation of QDA on CART bands");

s = content("CART versus Random Forest on raw reflectance");
img(s, "F13_A3_pipelines.png", M, 1.2, W - 2 * M, 3.2, "CART vs RF pipelines");
table(s, [["Comparison", "Validation", "Mean difference", "Wilcoxon p"], ...A.wilcoxon.slice(1, 7).map((r) => [r[0], r[1], r[2], r[5]])], M, 4.5, W - 2 * M, { colW: [4.6, 4.4, 1.6, 1.63], fontSize: 11, rowH: 0.3 });

s = content("Stability of the selected bands");
img(s, "F14_A4_stability.png", M, 1.25, 7.4, 5.6, "Stability");
table(s, A.stability.map((r) => [r[0], r[1], r[2], r[5]]), 8.1, 1.35, W - 8.1 - M, { colW: [1.4, 1.2, 1.3, 1.23], fontSize: 11, rowH: 0.55 });

// ================================================================ K: features from raw reflectance
sectionSlide("Step 2 · Disease-sensitive features from raw reflectance", "Band reflectance · continuum-removal parameters · vegetation indices · optimised two-band index · first/second/third derivatives · red-edge parameters · correlation spectra");

s = content("Detector joins and noise (information only)");
img(s, "F15_K0_detector_joins.png", M, 1.25, 8.2, 5.6, "Detector joins");
bullets(s, ["All features are computed from the raw plot-average reflectance, as requested: no splice correction, no smoothing.",
            "Derivatives: central finite differences on the 1-nm grid (first, second and third order).",
            "Bands beside the detector joins (990–1010 and 1795–1835 nm) carry an instrument step and are excluded from the reflectance and derivative feature sets."],
        8.95, 1.4, W - 8.95 - M, 5.4, 14);

s = content("Band reflectance and derivatives: AUC of every band");
img(s, "F16_K1_K4_band_auc.png", M, 1.25, 7.9, 5.65, "AUC spectra");
table(s, K.k1_regions.map((r) => [r[0], r[1], r[2], r[3]]), 8.6, 1.35, W - 8.6 - M, { colW: [1.3, 1.0, 0.9, 0.98], fontSize: 11, rowH: 0.42 });

s = content("Continuum-removal parameters");
img(s, "F17_K2_continuum.png", M, 1.25, 7.0, 5.65, "Continuum removal");
table(s, K.k2.map((r) => [r[0], r[3], r[4], r[5]]), 7.7, 1.35, W - 7.7 - M, { colW: [2.4, 0.8, 0.9, 1.0], fontSize: 11, rowH: 0.45 });

s = content(`Vegetation indices — ${J.vi_table.length - 1} indices`);
img(s, "F18_K3_indices.png", M, 1.25, 6.6, 5.65, "Vegetation indices");
table(s, K.k3.map((r) => [r[0], r[3], r[4], r[5]]), 7.3, 1.35, W - 7.3 - M, { colW: [1.8, 0.9, 0.9, 1.3], fontSize: 11, rowH: 0.42 });
cap(s, "31 indices of the flowering-stage workbook (Activity 1.4 table) + further pigment, red-edge, water and disease indices; AUC is direction-free (0.5 = no separation).", 7.3, 6.0, W - 7.3 - M, 0.7);

s = content("Optimised two-band index");
img(s, "F19_K3b_ndsi_heatmap.png", M, 1.25, 7.4, 5.65, "Optimised index");
table(s, K.k3b_jf_refined.map((r) => [r[0], r[3], r[5]]), 8.1, 1.35, W - 8.1 - M, { colW: [2.3, 0.9, 1.53], fontSize: 12, rowH: 0.45 });
para(s, `Every band pair searched (5-nm grid, refined at 1 nm), pairs straddling a detector join excluded. Honest balanced accuracy with the pair searched inside training plots only: ${pct(K.k3b_jf_honest.NDSI ? K.k3b_jf_honest.NDSI["BA CV"] : null)} (cross-validation).`, 8.1, 3.0, W - 8.1 - M, 3.5, 14);

s = content("First-, second- and third-derivative spectra");
img(s, "F20_K4_first_derivative.png", M, 1.25, 7.2, 5.65, "Derivatives");
table(s, K.k4_summary.map((r) => [r[0], r[1], r[2], r[3]]), 7.9, 1.35, W - 7.9 - M, { colW: [2.4, 0.9, 0.9, 0.68], fontSize: 11, rowH: 0.55 });

s = content("Red-edge parameters and the red-edge inflection point");
img(s, "F21_K4_REIP.png", M, 1.25, 7.2, 5.65, "Red-edge inflection point");
table(s, J.edge_all.slice(0, 13).map((r) => [r[0], r[3], r[4]]), 7.9, 1.35, W - 7.9 - M, { colW: [3.2, 0.8, 0.88], fontSize: 11, rowH: 0.36 });

s = content("Correlation spectra with disease status");
img(s, "F22_K6_correlation.png", M, 1.25, 8.0, 5.65, "Correlation spectra");
table(s, K.corr_regions.slice(0, 10).map((r) => [r[0], r[1], r[2], r[3]]), 8.7, 1.35, W - 8.7 - M, { colW: [1.2, 1.2, 0.9, 0.78], fontSize: 11, rowH: 0.42 });

s = content("CART versus Random Forest on each feature group");
img(s, "F23_K5_cart_vs_rf.png", M, 1.25, 6.6, 5.65, "Feature groups");
table(s, K.k5.map((r) => [r[0], r[1], r[2], r[3]]), 7.3, 1.35, W - 7.3 - M, { colW: [2.6, 0.9, 1.0, 1.0], fontSize: 11, rowH: 0.45 });

// ================================================================ C: combined pool
sectionSlide("Step 3 · Four tiers on the combined feature pool", `Raw reflectance + continuum removal + vegetation indices + derivatives + red-edge parameters (${CC.n_features} features) → disease-specific features`);

s = content("The combined feature pool");
table(s, CC.composition, M, 1.3, 7.6, { colW: [2.6, 0.85, 0.95, 0.65, 0.75, 0.6, 0.6, 0.6], fontSize: 10, rowH: 0.3 });
para(s, [`${CC.pool_raw} features from the raw plot-average reflectance; ${CC.n_features} after removing exact duplicates; Tier 1 (Welch + FDR): ${CC.n_sig} significant.`,
         "Columns 4–8: number of features of each type in the CART and Random Forest sets."], 8.4, 1.3, W - 8.4 - M, 2.4, 14);
img(s, "F24_C_composition.png", M, 4.5, W - 2 * M, 2.5, "Pool composition");

s = content(`Tier 2 · CART (${CC.cart_name}) and Random Forest (${CC.rf_name}) features`);
img(s, "F26_C_cart_tree.png", M, 1.25, 6.6, 5.65, "CART tree of the pool");
para(s, [`CART (${CC.cart_name}): ${featList(CC.sets[CC.cart_name])}.`, `Random Forest (${CC.rf_name}): ${featList(CC.sets[CC.rf_name])}.`], 7.3, 1.4, W - 7.3 - M, 5.4, 14);

s = content("Tier 2 · Random Forest importance in the combined pool");
img(s, "F25_C_top_importance.png", M, 1.25, W - 2 * M, 5.65, "Top importance");

s = content("Tiers 3 and 4 · separability and QDA on the selected features");
table(s, CC.tier3, M, 1.35, 5.6, { colW: [2.8, 1.2, 1.6], fontSize: 13, rowH: 0.42 });
s.addText(`QDA on ${CC.rf_name} features (spectrum-level 10-fold)`, { x: 6.6, y: 1.3, w: 6.2, h: 0.4, fontSize: 15, bold: true, color: THEME.colors.dk2, isTextBox: true, margin: 0 });
table(s, em(CC.errmat[CC.rf_name]), 6.6, 1.75, W - 6.6 - M, { colW: [2.0, 1.1, 1.1, 1.98], fontSize: 13, rowH: 0.45 });
img(s, "F27_C_incremental.png", 6.6, 3.85, W - 6.6 - M, 3.0, "Incremental");
para(s, `J–M on the CART features = ${jmC(CC.cart_name)}, on the ${CC.rf_name} features = ${jmC(CC.rf_name)}.`, M, 4.6, 5.6, 1.5, 14);

s = content("Validation of the combined-pool pipelines");
table(s, valRows(CC), M, 1.3, 7.2, { colW: [2.4, 1.2, 1.2, 1.2, 1.2], fontSize: 12, rowH: 0.42 });
para(s, `Nested plot-grouped cross-validation: raw reflectance, QDA on CART bands ${pct(A.v["QDA on CART features|V3"].BA)} → combined pool, QDA on ${CC.rf_name} features ${pct(CC.v["QDA on RF features|V3"].BA)}; Random Forest classifier ${pct(A.v["RF classifier|V3"].BA)} → ${pct(CC.v["RF classifier|V3"].BA)}.`, 7.95, 1.3, W - 7.95 - M, 2.2, 14);
img(s, "F28_C_pipelines.png", M, 3.6, W - 2 * M, 3.4, "Pool pipelines");

s = content("Stability of the selected pool features");
img(s, "F28b_C_stability.png", M, 1.25, 7.4, 5.65, "Pool stability");
table(s, CC.stability.map((r) => [r[0], r[1], r[2], r[4]]), 8.1, 1.35, W - 8.1 - M, { colW: [1.4, 1.2, 1.3, 1.23], fontSize: 11, rowH: 0.55 });
table(s, CC.fold_comp.slice(0, 11).map((r) => [r[0], r[1], r[3]]), 8.1, 3.2, W - 8.1 - M, { colW: [1.3, 2.5, 1.33], fontSize: 10, rowH: 0.3 });

// disease-specific features slide (filled from J.DS)
s = content("Disease-specific features: diseased vs healthy plots");
if (J.DS) {
  table(s, J.DS.rows, M, 1.2, W - 2 * M, { colW: J.DS.colW, fontSize: 10, rowH: 0.245 });
  cap(s, J.DS.note, M, 6.5, W - 2 * M, 0.55);
}

// ================================================================ synthesis
sectionSlide("Synthesis", "All approaches side by side · transfer to an unseen date · conclusions");

s = content("All approaches on new plots");
img(s, "F29_synthesis.png", M, 1.2, W - 2 * M, 5.8, "Synthesis");
s = content("All approaches · balanced accuracy table");
table(s, [["Approach", "Nested plot-grouped", "30 % plot hold-out", "Leave-one-date-out"], ...X.synthesis.slice(1, 15)], M, 1.3, W - 2 * M,
      { colW: [7.4, 1.6, 1.6, 1.63], fontSize: 11, rowH: 0.36 });

s = content("Transfer to an unseen date");
table(s, X.lodo, M, 1.25, 7.4, { colW: [3.0, 1.1, 1.1, 1.1, 1.1], fontSize: 10, rowH: 0.27 });
para(s, "Balanced accuracy on each held-out date: trained on the other three dates (training plots of a hold-out split), tested on the held-out date (test plots of the split). the last date, 13-03-2026, is predicted at chance level by every pipeline.", 8.2, 1.3, W - 8.2 - M, 2.6, 14);
img(s, "F30_V5_leave_one_date_out.png", M, 4.1, W - 2 * M, 2.9, "Leave-one-date-out");

s = content("Conclusions");
bullets(s, (T.conclusions || []).slice(1, 9), M, 1.3, W - 2 * M, 5.7, 14);

s = content("Recommendations and cross-checks");
bullets(s, (T.recommendations || []).slice(0, 5), M, 1.3, 7.6, 5.7, 14);
stat(s, String(J.checks.pass), "checks passed", 8.5, 1.4, 2.0, C.accent3);
stat(s, String(J.checks.flag), "flagged (limitations, reported)", 10.75, 1.4, 2.0, C.accent4);
stat(s, String(J.checks.fail), "failed", 8.5, 3.2, 2.0, C.accent2);
para(s, "Every step was verified by an independent implementation or recomputation (SciPy, statsmodels, R rpart/MASS/nlme/randomForest, Excel formulas); see the 33_Cross_Checks sheet of the workbook.", 10.75, 3.2, 2.05, 3.0, 11);

const KEY = ["Das B", "Breiman L", "Chen C", "Benjamini", "Welch", "Swain", "Richards", "Bhattacharyya", "Clark, R.N.", "Clark RN", "Kokaly",
             "Gong", "Dawson", "Cho", "Guyot", "Horler", "Tsai", "Mahlein", "Brodersen", "Varma", "Hurlbert", "Therneau", "Venables", "Lemaître",
             "Pinheiro", "Haboudane, D., Miller, J.R., Tremblay", "Gitelson, A.A., Merzlyak, M.N., 1996", "Saharan", "Thenkabail", "Ambroise"];
const keyRefs = (J.refs || []).filter((r) => KEY.some((k) => r.startsWith(k)));
for (let i = 0; i < keyRefs.length; i += 14) {
  s = content(i === 0 ? "Key references" : "Key references (continued)");
  bullets(s, keyRefs.slice(i, i + 14), M, 1.3, W - 2 * M, 5.7, 11);
}
cap(s, `Full list (${(J.refs || []).length} references, including the source of every vegetation index) in the Word report.`, M, 6.65, W - 2 * M, 0.4);

pres.writeFile({ fileName: OUT }).then(async () => { await applyTheme(OUT, THEME); console.log("saved", OUT); });
