// Builds the presentation from work/results.json and work/figures/*.png
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const WORK = process.argv[2];
const OUT = process.argv[3];
const J = JSON.parse(fs.readFileSync(path.join(WORK, "results.json"), "utf8"));
const FIG = (n) => path.join(J.fig, n + ".png");
const sizeOf = (file) => { // PNG width/height from the IHDR chunk
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
};

const THEME = {
  name: "White rust spectral", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1B1B1A", lt1: "FFFFFF", dk2: "1F3D2B", lt2: "F0EFEC", accent1: "1BAF7A", accent2: "EB6834",
            accent3: "2A78D6", accent4: "EDA100", accent5: "6250D6", accent6: "52514E", hlink: "2A78D6", folHlink: "6250D6" },
};
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "White rust in mustard: four-tier spectral analysis";
pres.author = "Animesh Panda";
const C = pres.SchemeColor;
const W = 13.333, H = 7.5, M = 0.5;

pres.defineSlideMaster({
  title: "TITLE", background: { color: "1F3D2B" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 2.0, w: W - 2 * M, h: 1.6, fontFace: "Cambria", fontSize: 40, bold: true, color: "FFFFFF", valign: "bottom" }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: M, y: 3.8, w: W - 2 * M, h: 2.2, fontSize: 18, color: "E3F4EC", valign: "top" }, text: "" } }],
});
pres.defineSlideMaster({
  title: "SECTION", background: { color: "1F3D2B" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 2.6, w: W - 2 * M, h: 1.2, fontFace: "Cambria", fontSize: 36, bold: true, color: "FFFFFF", valign: "bottom" }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: M, y: 3.9, w: W - 2 * M, h: 1.6, fontSize: 18, color: "E3F4EC", valign: "top" }, text: "" } }],
  slideNumber: { x: W - 0.9, y: H - 0.45, fontSize: 10, color: "B5D6C3" },
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 0.3, w: W - 2 * M, h: 0.8, fontFace: "Cambria", fontSize: 26, bold: true, color: "1F3D2B", valign: "middle" }, text: "" } },
            { text: { text: "White rust · mustard leaves · all dates combined · four-tier analysis (Das et al. 2020) + CART vs RF + K + combined pool",
                      options: { x: M, y: H - 0.42, w: 10, h: 0.3, fontSize: 9, color: "8A8981" } } }],
  slideNumber: { x: W - 0.9, y: H - 0.42, fontSize: 10, color: "8A8981" },
});

let section = "Introduction";
const sec = (t) => { section = t; pres.addSection({ title: t }); };
const content = (title) => { const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section }); s.addText(title, { placeholder: "title" }); return s; };

function img(s, name, x, y, w, h) {
  const f = FIG(name);
  if (!fs.existsSync(f)) return;
  const d = sizeOf(f);
  const r = Math.min(w / d.w, h / d.h);
  const iw = d.w * r, ih = d.h * r;
  s.addImage({ path: f, x: x + (w - iw) / 2, y: y + (h - ih) / 2, w: iw, h: ih, altText: name });
}
function table(s, rows, x, y, w, opts = {}) {
  const fs_ = opts.fontSize || 11;
  const hl = opts.highlight || [];
  const data = rows.map((r, i) => r.map((c) => ({
    text: String(c),
    options: i === 0 ? { bold: true, color: "FFFFFF", fill: { color: "1F3D2B" }, fontSize: fs_, valign: "middle" }
                     : { fontSize: fs_, color: "1B1B1A", fill: { color: hl.includes(i) ? "E3F4EC" : (i % 2 ? "FFFFFF" : "F7F7F5") } },
  })));
  s.addTable(data, { x, y, w, colW: opts.colW, border: { type: "solid", pt: 0.5, color: "D9D8D2" }, margin: 0.04,
                     rowH: opts.rowH || 0.26, autoPage: false });
}
function bullets(s, items, x, y, w, h, fontSize = 15) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
            { x, y, w, h, fontSize, color: "1B1B1A", valign: "top", paraSpaceAfter: 6, isTextBox: true });
}
function stat(s, value, label, x, y, w, color) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.55, fill: { color: "F0EFEC" }, line: { color: "F0EFEC" }, rectRadius: 0.08 });
  s.addText(value, { x: x + 0.15, y: y + 0.1, w: w - 0.3, h: 0.8, fontFace: "Cambria", fontSize: 34, bold: true, color, isTextBox: true, margin: 0 });
  s.addText(label, { x: x + 0.15, y: y + 0.88, w: w - 0.3, h: 0.6, fontSize: 12, color: "52514E", isTextBox: true, margin: 0, valign: "top" });
}
function note(s, text, y = H - 0.85) {
  s.addText(text, { x: M, y, w: W - 2 * M, h: 0.4, fontSize: 11, italic: true, color: "52514E", isTextBox: true, margin: 0 });
}
const pct = (v) => (v == null ? "–" : (100 * v).toFixed(1) + " %");
const A = J.A, K = J.K, CC = J.C, X = J.X;
const vA = (p, s) => A.v[p + "|" + s].BA, vC = (p, s) => CC.v[p + "|" + s].BA;

// ----------------------------------------------------------------- 1 title
sec("Introduction");
let s = pres.addSlide({ masterName: "TITLE", sectionTitle: section });
s.addText("Discriminating healthy and white-rust-diseased mustard leaves with field spectroradiometry", { placeholder: "title" });
s.addText([{ text: "Four-tier hierarchical analysis (Das et al., 2020) with imbalance correction · CART vs Random Forest · disease-sensitive features (K) · four tiers on the combined feature pool", options: { breakLine: true } },
           { text: `${J.n} leaf spectra (${J.nH} healthy, ${J.nD} diseased) · 4 dates · 3 growth stages · 3 varieties · ASD contact probe, 400–2500 nm`, options: { breakLine: true, fontSize: 14, color: "B5D6C3" } },
           { text: "Animesh Panda · Division of Agricultural Physics, ICAR-IARI, New Delhi", options: { fontSize: 14, color: "B5D6C3" } }],
          { placeholder: "body" });

// ----------------------------------------------------------------- 2 key results
s = content("Key results at a glance");
const jmC = A.jm[A.cart_name], jmR = A.jm[A.rf_name];
stat(s, `${A.n_sig}/${J.n_bands}`, "bands differ significantly (Tier 1, Welch + FDR)", M, 1.3, 2.9, "1F3D2B");
stat(s, jmC.toFixed(2), `J–M on ${A.cart_name} bands (threshold 1.90)`, M + 3.1, 1.3, 2.9, "2A78D6");
stat(s, pct(vA("QDA on CART features", "V3")), "QDA on CART bands, honest nested CV (V3)", M + 6.2, 1.3, 2.9, "2A78D6");
stat(s, pct(vC("QDA on RF features", "V3")), "QDA on RF-selected features of the combined pool (V3)", M + 9.3, 1.3, 2.9, "C98500");
bullets(s, (J.txt.key_messages || []).slice(0, 5), M, 3.15, W - 2 * M, 3.6, 15);

// ----------------------------------------------------------------- 3 data
s = content("Data: 2264 unique leaf spectra pooled over dates, stages and varieties");
table(s, J.by_date, M, 1.3, 5.2, { colW: [1.7, 1.15, 1.2, 1.15] });
table(s, J.by_stage, M, 3.0, 5.2, { colW: [2.0, 1.6, 1.6] });
table(s, J.by_variety, M, 4.4, 5.2, { colW: [2.0, 1.6, 1.6] });
bullets(s, [`Four ASD export files, one column per leaf; plot-average columns ignored (leaf level only).`,
            `79 exact copies removed: 75 in the second block of 13-03-2026, 4 unnamed spectra of plot 27 (11-02-2026).`,
            `48 plots: 12 healthy controls (plots 1–12), 36 inoculated; every plot measured on all four dates.`,
            `Diseased : healthy = ${J.ratio.toFixed(2)} : 1 → equal priors, balanced sampling and balanced accuracy throughout.`,
            `Leaf level and disease score not used — healthy vs diseased only.`], 6.2, 1.3, 6.6, 4.5, 14);

s = content("Workflow: Das et al. (2020) four tiers, extended and validated");
img(s, "F01_workflow", M, 1.15, W - 2 * M, 5.8);

s = content("Corrections to the published protocol and how validation was made honest");
table(s, [["Issue", "Correction"], ["Class imbalance 1 : 5", "equal priors (QDA, rpart), balanced RF, balanced accuracy, 1000 balanced subsets"],
          ["Two classes, unequal variances", "Welch t-test (ANOVA reported for comparison)"], ["2101 tests", "Benjamini–Hochberg FDR"],
          ["Leaves nested in plots, plots on 4 dates", "mixed model; all honest folds grouped by plot across dates"],
          ["Selection bias", "Tier 1 + selection + classifier refitted in every training set (V3, V4, V5)"],
          ["Water bands", "kept — contact probe (Das et al. removed them for canopy data)"],
          ["Detector joins (1000, 1800 nm)", "splice correction + guard zones in Part K"]], M, 1.3, 7.2, { colW: [2.6, 4.6], fontSize: 12, rowH: 0.42 });
table(s, [["Scheme", "Test leaves", "Refitted"], ["V1", "leaf-level 10-fold (paper)", "classifier only"], ["V2", "plot-grouped 10-fold", "classifier only"],
          ["V3", "plot-grouped 10-fold × 5, nested", "everything"], ["V4", "30 % of plots × 10", "everything"],
          ["V5 (extra)", "new date + new plots", "everything"]], 8.0, 1.3, 4.8, { colW: [1.1, 2.3, 1.4], fontSize: 12, rowH: 0.42 });

// ----------------------------------------------------------------- Part A
sec("Part A · Four-tier analysis (CART)");
s = pres.addSlide({ masterName: "SECTION", sectionTitle: section });
s.addText("Part A · The four-tier method of Das et al. (2020)", { placeholder: "title" });
s.addText("Step 0–1 data and band set → Tier 1 statistical screening → Tier 2 CART band selection → Tier 3 J–M separability → Tier 4 QDA → validation", { placeholder: "body" });

s = content("Step 0–1 · Data audit and band set: 350–399 nm removed, water bands kept");
table(s, J.checks0.map((r) => [r[0], r[1].slice(0, 60), r[2]]), M, 1.2, 7.8, { colW: [3.2, 3.8, 0.8], fontSize: 10, rowH: 0.3 });
table(s, J.noise, 8.6, 1.2, 4.2, { colW: [1.5, 1.4, 1.3], fontSize: 11 });
note(s, "Noise = SD of the Savitzky–Golay residual; the 350–399 nm detector edge is ~116 × noisier than 500–699 nm and was removed.");

s = content("Mean spectra: diseased leaves brighter in VIS and SWIR, darker in NIR");
img(s, "F02_mean_spectra", M, 1.1, 7.6, 4.0);
img(s, "F02b_mean_spectra_by_date", M, 5.0, W - 2 * M, 2.0);
bullets(s, (J.txt.spectra || []), 8.3, 1.2, 4.5, 3.8, 14);

s = content(`Tier 1 · ${A.n_sig} of ${J.n_bands} bands differ significantly (Welch + FDR)`);
table(s, A.tests, M, 1.2, 6.0, { colW: [4.7, 1.3], fontSize: 11, rowH: 0.34 });
img(s, "F03_tier1_significant_regions", 6.7, 1.1, 6.1, 3.3);
table(s, A.ranges.slice(0, 9), M, 4.0, 6.0, { colW: [2.4, 1.2, 2.4], fontSize: 11 });
note(s, `Mixed model with a random plot effect: ${A.mixed_sig} bands remain significant (pseudo-replication check).`);

s = content("Tier 1 · Significance frequency over 1000 balanced subsets (Das et al. Fig. 5)");
img(s, "F04_tier1_frequency", M, 1.1, 8.0, 5.3);
bullets(s, [`378 healthy vs 378 randomly drawn diseased leaves, 1000 times.`, `Median ${A.balanced.median} significant bands per subset (min ${A.balanced.min}, max ${A.balanced.max}).`,
            `${A.balanced.ge95} bands significant in ≥ 95 % of subsets; ${A.balanced.all} in all.`,
            `The imbalance inflates significance only slightly: the significant regions are the same.`], 8.8, 1.3, 4.0, 4.5, 14);

s = content("Tier 1 · −log₁₀(p) against wavelength");
img(s, "F05_minus_log10_p", M, 1.1, 7.9, 4.3);
bullets(s, (J.txt.log10p || []), M, 5.5, 7.9, 1.4, 12);
table(s, A.regions.map((r) => [r[0], r[1], r[2], r[3]]), 8.6, 1.2, 4.2, { colW: [1.8, 0.6, 0.9, 0.9], fontSize: 9.5, rowH: 0.3 });

s = content(`Tier 2 · CART (rpart, prior 0.5/0.5) selects ${A.set_sizes[A.cart_name]} bands`);
img(s, "F06_cart_tree", M, 1.1, W - 2 * M, 5.2);
note(s, `${A.cart_name}: ${A.sets[A.cart_name]} nm`);

s = content("Tier 2 · The CART bands, their regions and how often they are re-selected");
table(s, A.cart_table, M, 1.15, 8.3, { colW: [0.9, 1.4, 1.1, 0.9, 1.5, 1.5, 1.0], fontSize: 10, rowH: 0.24 });
img(s, "F08_cart_reselection", 8.9, 1.15, 3.9, 3.0);
img(s, "F07_cart_cp", 8.9, 4.2, 3.9, 2.5);

s = content(`Tier 3 · J–M = ${jmC.toFixed(2)} on the CART bands: ${jmC >= 1.9 ? "separable" : "not separable at 1.90"}`);
table(s, A.tier3, M, 1.2, 5.2, { colW: [2.8, 1.1, 1.3], fontSize: 12, rowH: 0.34 });
img(s, "F09_tier3_tier4_incremental", 5.9, 1.2, 6.9, 2.6);
bullets(s, (J.txt.jm || []), 5.9, 4.0, 6.9, 2.6, 14);

const em = (m) => [["Classified \\ Reference", "Healthy", "Diseased", "Row total", "User's acc."],
  ["Healthy", m.HH, m.DH, m.HH + m.DH, pct(m.HH / (m.HH + m.DH))], ["Diseased", m.HD, m.DD, m.HD + m.DD, pct(m.DD / (m.HD + m.DD))],
  ["Column total", m.HH + m.HD, m.DH + m.DD, m.N, ""], ["Producer's acc.", pct(m.PA_H), pct(m.PA_D), "", ""]].map((r) => r.map(String));
s = content("Tier 4 · QDA with equal priors on the CART bands (Das et al. Table 2)");
const e1 = A.errmat[A.cart_name];
table(s, em(e1), M, 1.3, 6.4, { colW: [1.9, 1.1, 1.1, 1.1, 1.2], fontSize: 13, rowH: 0.42 });
stat(s, pct(e1.OA), "overall accuracy", M, 3.8, 2.0, "1F3D2B");
stat(s, pct(e1.BA), "balanced accuracy", M + 2.2, 3.8, 2.0, "2A78D6");
stat(s, e1.kappa.toFixed(3), "Cohen's κ", M + 4.4, 3.8, 2.0, "52514E");
table(s, A.tier4.filter((r, i) => i === 0 || r[0].startsWith("CART")).map((r) => r.slice(0, 7)), 7.2, 1.3, 5.6, { colW: [1.1, 1.3, 0.62, 0.62, 0.66, 0.66, 0.64], fontSize: 10, rowH: 0.3 });
note(s, "Equal priors correct the 1 : 5 imbalance: the minority (healthy) class is recognised far better than with sample priors.");

s = content(`Validation · honest estimates for new plots: ${pct(vA("QDA on CART features", "V3"))} (V3) and ${pct(vA("QDA on CART features", "V4"))} (V4)`);
table(s, A.val_qda, M, 1.2, 7.2, { colW: [2.6, 1.3, 0.6, 0.6, 0.6, 0.5, 0.5, 0.5], fontSize: 9, rowH: 0.24 });
img(s, "F11_validation_qda_cart", 7.9, 1.2, 4.9, 2.6);
table(s, A.sens_range, 7.9, 4.2, 4.9, { colW: [2.0, 0.6, 0.75, 0.8, 0.75], fontSize: 9.5 });

// ----------------------------------------------------------------- CART vs RF
sec("Part A · CART vs Random Forest");
s = pres.addSlide({ masterName: "SECTION", sectionTitle: section });
s.addText("Random Forest instead of CART", { placeholder: "title" });
s.addText("A1 RF importance as the Tier-2 selector · A2 Tiers 3–4 on each band set · A3 CART and RF as classifiers · A4 band stability", { placeholder: "body" });

s = content("A1 · Where the Random Forest finds the disease signal");
img(s, "F12_A1_rf_importance", M, 1.1, 8.2, 3.8);
table(s, Object.entries(A.sets).map(([k, v]) => [k, v]).slice(0, 5).reduce((a, r) => (a.push(r), a), [["Band set", "Wavelengths (nm)"]]),
      M, 5.0, W - 2 * M, { colW: [2.4, 9.9], fontSize: 10, rowH: 0.27 });
table(s, A.rf_checks.map((r) => [r[0].slice(0, 46), r[1], r[2]]), 8.9, 1.2, 3.9, { colW: [2.4, 0.9, 0.6], fontSize: 8.5, rowH: 0.3 });

s = content(`A2 · J–M ${jmR.toFixed(2)} (RF) vs ${jmC.toFixed(2)} (CART); QDA BA ${pct(A.errmat[A.rf_name].BA)} vs ${pct(A.errmat[A.cart_name].BA)}`);
table(s, A.tier3, M, 1.2, 4.6, { colW: [2.4, 1.0, 1.2], fontSize: 12, rowH: 0.34 });
table(s, em(A.errmat[A.cart_name]), M, 3.5, 4.6, { colW: [1.4, 0.8, 0.8, 0.8, 0.8], fontSize: 10, rowH: 0.3 });
table(s, em(A.errmat[A.rf_name]), M, 5.3, 4.6, { colW: [1.4, 0.8, 0.8, 0.8, 0.8], fontSize: 10, rowH: 0.3 });
s.addText(`${A.cart_name}`, { x: M, y: 3.22, w: 3, h: 0.28, fontSize: 11, bold: true, color: "2A78D6", isTextBox: true, margin: 0 });
s.addText(`${A.rf_name}`, { x: M, y: 5.02, w: 3, h: 0.28, fontSize: 11, bold: true, color: "C98500", isTextBox: true, margin: 0 });
img(s, "F09_tier3_tier4_incremental", 5.4, 1.2, 7.4, 2.8);
bullets(s, (J.txt.a2 || []), 5.4, 4.2, 7.4, 2.4, 14);

s = content("A3 · CART and RF as classifiers and as band selectors (identical folds)");
img(s, "F13_A3_pipelines", M, 1.1, 8.3, 3.4);
table(s, A.wilcoxon, M, 4.6, W - 2 * M, { colW: [4.6, 2.2, 1.6, 1.2, 1.3, 1.4], fontSize: 10, rowH: 0.23 });
bullets(s, (J.txt.a3 || []), 9.0, 1.2, 3.8, 3.3, 13);

s = content("A4 · How stable are the selected bands across 50 training sets?");
img(s, "F14_A4_stability", M, 1.1, W - 2 * M, 3.6);
table(s, A.stability, M, 4.9, W - 2 * M, { colW: [1.2, 1.6, 2.2, 2.6, 2.3, 2.4], fontSize: 11 });

// ----------------------------------------------------------------- Part K
sec("Part K · Disease-sensitive features");
s = pres.addSlide({ masterName: "SECTION", sectionTitle: section });
s.addText("Part K · Disease-sensitive feature extraction", { placeholder: "title" });
s.addText("K0 denoising → K1 band reflectance · K2 continuum removal · K3 spectral indices (+ K3b optimised index) · K4 first derivative and REIP · K6 correlation spectra → K5 CART vs RF on every feature group", { placeholder: "body" });

s = content("K0 · Splice correction, smoothing and the detector artefact at 1800 nm");
img(s, "F15_K0_detector_joins", M, 1.1, 8.4, 3.0);
table(s, [["Join", "Offset healthy", "Offset diseased"]].concat(K.k0.offsets), M, 4.4, 5.0, { colW: [1.8, 1.6, 1.6], fontSize: 12 });
bullets(s, [`Savitzky–Golay: SG(11,2) smoothing, SG(15,2) first and SG(21,2) second derivative.`,
            `Signal preserved: r ≥ ${K.k0.corr.toFixed(5)}; Tier-1 bands ${K.k0.sig_raw} (raw) vs ${K.k0.sig_s} (smoothed).`,
            `Start-up bump after 1801 nm ${K.k0.bump ? "detected" : "not detected"} → guard zones 990–1010 and 1795–1835 nm (wider for derivatives) excluded from rankings.`],
        9.1, 1.2, 3.7, 5.0, 13);

s = content(`K1 · Band reflectance: best single band ${K.k1.best_wl.toFixed(0)} nm (AUC ${K.k1.best_auc.toFixed(3)})`);
img(s, "F16_K1_K4_band_auc", M, 1.1, 7.0, 3.1);
table(s, K.k1_regions, M, 4.3, W - 2 * M, { colW: [1.8, 1.4, 1.0, 1.1, 1.0, 1.8, 1.6], fontSize: 10, rowH: 0.21 });
bullets(s, [`${K.k1.sig_smoothed} of ${K.k1.tested} smoothed bands significant; ${K.k1.auc70} bands reach AUC ≥ 0.70.`,
            `Threshold chosen on training plots and tested on new plots (CV and hold-out columns).`], 7.8, 1.2, 5.0, 2.8, 13);

s = content("K2 · Continuum-removed absorption features");
img(s, "F17_K2_continuum", M, 1.1, 6.6, 3.6);
table(s, K.k2, 7.3, 1.2, 5.5, { colW: [1.8, 0.65, 0.65, 0.5, 0.6, 0.65, 0.65], fontSize: 9, rowH: 0.26 });
note(s, "Depth, position, area, width (FWHM) and symmetry of six absorption windows (30 parameters); ranked by AUC.", 5.0);

s = content("K3 · Disease-sensitive spectral indices (31 indices)");
img(s, "F18_K3_indices", M, 1.1, 4.6, 5.8);
table(s, K.k3, 5.4, 1.2, 7.4, { colW: [1.3, 1.1, 1.1, 0.8, 0.9, 1.1, 1.1], fontSize: 10.5, rowH: 0.3 });
s.addText("mCARI1 and MTVI1 are algebraically identical; SR761 and NDVI761 rank leaves identically (same AUC). Ranking: AUC on all leaves; BA columns: threshold chosen on training plots, tested on new plots.",
          { x: 5.4, y: 4.6, w: 7.4, h: 0.8, fontSize: 11, italic: true, color: "52514E", isTextBox: true, margin: 0 });

s = content(`K3b · Optimised two-band index: ${K.k3b_npairs.toLocaleString("en")} band pairs searched`);
img(s, "F19_K3b_ndsi_heatmap", M, 1.1, 5.2, 4.6);
table(s, K.k3b_top, 6.0, 1.2, 3.4, { colW: [2.3, 1.1], fontSize: 11 });
table(s, K.k3b_refined, 6.0, 3.1, 6.8, { colW: [1.4, 1.0, 1.0, 0.7, 0.8, 1.0, 0.9], fontSize: 10 });
table(s, [["Honest (search inside training sets)", "BA CV", "BA hold-out"],
          ["NDSI, all pairs (straddles 1800 nm join)", pct(K.k3b_honest.NDSI["BA CV"]), pct(K.k3b_honest.NDSI["BA hold-out"])],
          ["NDSI, join-free pairs", pct(K.k3b_jf_honest.NDSI["BA CV"]), pct(K.k3b_jf_honest.NDSI["BA hold-out"])],
          ["DI, join-free pairs", pct(K.k3b_jf_honest.DI["BA CV"]), pct(K.k3b_jf_honest.DI["BA hold-out"])]], 6.0, 4.3, 6.8, { colW: [3.6, 1.6, 1.6], fontSize: 11 });
table(s, K.k3b_jf_refined.map((r) => r.slice(0, 7)), 6.0, 5.75, 6.8, { colW: [1.4, 1.0, 1.0, 0.7, 0.8, 1.0, 0.9], fontSize: 9.5, rowH: 0.22 });

s = content("K4 · First-derivative spectra and edge parameters");
img(s, "F20_K4_first_derivative", M, 1.1, 8.0, 2.9);
table(s, K.k4_summary, M, 4.15, 8.0, { colW: [2.4, 1.3, 1.5, 0.9, 1.9], fontSize: 10 });
table(s, K.k4_edge.map((r) => [r[0].slice(0, 30), r[3], r[4], r[5], r[6]]), 8.7, 1.2, 4.1, { colW: [1.9, 0.5, 0.6, 0.55, 0.55], fontSize: 9, rowH: 0.28 });

s = content("K4b · Red-edge inflection point (REIP): four methods agree on a blue shift");
img(s, "F21_K4_REIP", M, 1.1, 8.4, 3.2);
table(s, K.reip.map((r) => [r[0].replace("REIP – ", ""), r[1], r[2], r[3], r[5], r[6]]), M, 4.5, 8.4, { colW: [2.9, 1.1, 1.1, 0.8, 1.3, 1.2], fontSize: 10.5 });
bullets(s, (J.txt.reip || []), 9.1, 1.2, 3.7, 5.0, 13);

s = content("K6 · Correlation spectra: r between band value and disease status");
img(s, "F22_K6_correlation", M, 1.1, 7.2, 4.8);
table(s, K.corr_regions, 7.9, 1.2, 4.9, { colW: [1.2, 1.0, 0.9, 0.7, 1.1], fontSize: 9, rowH: 0.23 });
note(s, "Severity scores were not used (healthy vs diseased only), so the point-biserial correlation with the 0/1 status is shown.");

s = content("K5 · CART vs Random Forest on each feature group");
img(s, "F23_K5_cart_vs_rf", M, 1.1, 7.6, 2.8);
table(s, K.k5, M, 4.05, 7.6, { colW: [3.3, 0.8, 0.9, 0.9, 0.85, 0.85], fontSize: 9.5, rowH: 0.24 });
table(s, K.k5_share, 8.3, 1.2, 4.5, { colW: [1.6, 0.8, 1.0, 1.1], fontSize: 9.5 });
bullets(s, (J.txt.k5 || []), 8.3, 3.4, 4.5, 3.2, 13);

// ----------------------------------------------------------------- Part C
sec("Part C · Four tiers on the combined pool");
s = pres.addSlide({ masterName: "SECTION", sectionTitle: section });
s.addText("Part C · The four-tier method on all extracted features", { placeholder: "title" });
s.addText(`K1 reflectance + K2 continuum removal + K3 indices + K4 derivative bands and edge parameters = ${CC.pool_raw} features → Tier 1 → CART / RF selection → J–M → QDA → nested validation`, { placeholder: "body" });

s = content(`C0–C1 · Pool of ${CC.n_features} features; ${CC.n_sig} pass Tier 1`);
table(s, CC.composition, M, 1.2, W - 2 * M, { fontSize: 11, rowH: 0.34 });
bullets(s, [`Duplicates removed before Tier 1: ${CC.dups.map((d) => d[1] + " (= " + d[0] + ")").join("; ") || "none"}.`,
            `RF peaks picked within each spectral series (bands ≥ 10 nm apart); every scalar feature is its own candidate.`,
            `Same settings, seeds and folds as Part A; Tier 1 + selection refitted inside every training set in V3–V5.`], M, 3.9, W - 2 * M, 2.4, 14);

s = content(`C2 · CART on the combined pool selects ${CC.set_sizes[CC.cart_name]} features`);
img(s, "F26_C_cart_tree", M, 1.1, W - 2 * M, 4.6);
note(s, `${CC.cart_name}: ${CC.sets[CC.cart_name]}`, 5.9);

s = content("C2 · Which feature families CART and RF pick from the pool");
img(s, "F25_C_top_importance", M, 1.1, 5.3, 5.8);
img(s, "F24_C_composition", 6.0, 1.1, 6.8, 3.0);
s.addText(`${CC.rf_name}: ${CC.sets[CC.rf_name]}`, { x: 6.0, y: 4.3, w: 6.8, h: 2.4, fontSize: 12, color: "1B1B1A", isTextBox: true, valign: "top" });

s = content(`C3–C4 · J–M and QDA on the selected features of the combined pool`);
table(s, CC.tier3, M, 1.2, 4.8, { colW: [2.6, 1.0, 1.2], fontSize: 12, rowH: 0.34 });
table(s, CC.tier4.filter((r, i) => i === 0 || r[1].startsWith("QDA equal")), M, 3.4, 7.6, { colW: [2.2, 1.6, 0.6, 0.6, 0.65, 0.65, 0.65, 0.65], fontSize: 10.5 });
table(s, em(CC.errmat[CC.rf_name]), 8.3, 1.2, 4.5, { colW: [1.4, 0.8, 0.8, 0.75, 0.75], fontSize: 10, rowH: 0.3 });
s.addText(`Error matrix · QDA on ${CC.rf_name} (V1)`, { x: 8.3, y: 0.95, w: 4.5, h: 0.25, fontSize: 11, bold: true, color: "C98500", isTextBox: true, margin: 0 });
img(s, "F27_C_incremental", 8.3, 3.3, 4.5, 2.0);

s = content("C5 · Honest validation of the combined-pool pipeline");
img(s, "F28_C_pipelines", M, 1.1, 8.0, 3.3);
table(s, CC.wilcoxon, M, 4.6, W - 2 * M, { colW: [4.6, 2.2, 1.6, 1.2, 1.3, 1.4], fontSize: 10, rowH: 0.23 });
bullets(s, (J.txt.c5 || []), 8.7, 1.2, 4.1, 3.3, 13);

s = content("C6 · Stability and the families chosen across 50 training sets");
img(s, "F28b_C_stability", M, 1.1, 8.2, 3.3);
table(s, CC.stability, M, 4.6, 8.2, { colW: [1.2, 1.4, 1.9, 1.8, 1.9], fontSize: 11 });
table(s, CC.fold_comp, 8.9, 1.2, 3.9, { colW: [0.8, 1.7, 0.8, 0.6], fontSize: 9.5 });

s = content("C7 · Combined pool vs reflectance only vs K5 (paired tests, same folds)");
const cx = [["First", "Second", "V3 Δ BA", "V3 wins", "V3 p", "V4 Δ BA", "V4 wins", "V4 p"]];
for (let i = 1; i < X.cross.length; i += 2) {
  const a = X.cross[i], b = X.cross[i + 1];
  cx.push([a[0], a[1], a[3], a[4] + "/" + (+a[4] + +a[5]), a[6], b[3], b[4] + "/" + (+b[4] + +b[5]), b[6]]);
}
table(s, cx, M, 1.2, W - 2 * M, { colW: [3.4, 3.4, 0.95, 0.85, 0.85, 0.95, 0.85, 1.08], fontSize: 10, rowH: 0.36 });
bullets(s, (J.txt.c7 || []), M, 5.2, W - 2 * M, 1.3, 13);

// ----------------------------------------------------------------- Part C′
const CR = J.CR, XR = J.XR;
sec("Part C′ · Four tiers on raw + K2 + K3 + K4");
s = pres.addSlide({ masterName: "SECTION", sectionTitle: section });
s.addText("Part C′ · The four-tier method on raw reflectance + K2 + K3 + K4", { placeholder: "title" });
s.addText(`Variant of Part C: the reflectance part of the pool is the RAW reflectance (2101 bands, as in Part A and Das et al. 2020) instead of K1. Pool = ${CR.pool_raw} features; same settings, seeds and folds.`, { placeholder: "body" });

s = content(`C′0–C′1 · Pool of ${CR.n_features} features; ${CR.n_sig} pass Tier 1`);
table(s, CR.composition, M, 1.2, W - 2 * M, { fontSize: 11, rowH: 0.34 });
bullets(s, [`Raw reflectance: all 2101 bands 400–2500 nm exactly as measured — no splice correction, no smoothing, no guard zones (names "R λ (raw)").`,
            `Duplicates removed before Tier 1: ${CR.dups.map((d) => d[1] + " (= " + d[0] + ")").join("; ") || "none"}.`,
            `K2, K3, K4 identical to Part C, so any difference between C′ and C comes only from raw vs K1 reflectance.`], M, 3.9, W - 2 * M, 2.4, 14);

s = content(`C′2 · CART on raw + K2–K4 selects ${CR.set_sizes[CR.cart_name]} features`);
img(s, "F32_CR_cart_tree", M, 1.1, W - 2 * M, 4.6);
note(s, `${CR.cart_name}: ${CR.sets[CR.cart_name]}`, 5.9);

s = content("C′2 · Which feature families CART and RF pick from raw + K2–K4");
img(s, "F33_CR_top_importance", M, 1.1, 5.3, 5.8);
img(s, "F34_CR_composition", 6.0, 1.1, 6.8, 3.0);
s.addText(`${CR.rf_name}: ${CR.sets[CR.rf_name]}`, { x: 6.0, y: 4.3, w: 6.8, h: 2.4, fontSize: 12, color: "1B1B1A", isTextBox: true, valign: "top" });

s = content("C′3–C′4 · J–M and QDA on the selected features");
table(s, CR.tier3, M, 1.2, 4.8, { colW: [2.6, 1.0, 1.2], fontSize: 12, rowH: 0.34 });
table(s, CR.tier4.filter((r, i) => i === 0 || r[1].startsWith("QDA equal")), M, 3.4, 7.6, { colW: [2.2, 1.6, 0.6, 0.6, 0.65, 0.65, 0.65, 0.65], fontSize: 10.5 });
table(s, em(CR.errmat[CR.rf_name]), 8.3, 1.2, 4.5, { colW: [1.4, 0.8, 0.8, 0.75, 0.75], fontSize: 10, rowH: 0.3 });
s.addText(`Error matrix · QDA on ${CR.rf_name} (V1)`, { x: 8.3, y: 0.95, w: 4.5, h: 0.25, fontSize: 11, bold: true, color: "C98500", isTextBox: true, margin: 0 });
img(s, "F35_CR_incremental", 8.3, 3.3, 4.5, 2.0);

s = content("C′5–C′6 · Validation and stability of the raw + K2–K4 pipeline");
img(s, "F36_CR_pipelines", M, 1.1, 7.0, 2.9);
img(s, "F37_CR_stability", M, 4.1, 7.0, 2.4);
table(s, CR.stability, 7.7, 1.2, 5.1, { colW: [0.7, 0.8, 1.1, 1.2, 1.3], fontSize: 9 });
table(s, CR.fold_comp, 7.7, 3.4, 5.1, { colW: [0.8, 2.4, 1.1, 0.8], fontSize: 9, rowH: 0.24 });

s = content("C′ vs C · Same folds: raw or K1 reflectance in the combined pool?");
img(s, "F38_A_CR_C_comparison", M, 1.0, W - 2 * M, 2.95);
table(s, XR.val, M, 4.05, 8.0, { colW: [2.0, 0.7, 1.35, 1.35, 1.35, 1.25], fontSize: 8.5, rowH: 0.19 });
const vCR = (p, sc) => CR.v[p + "|" + sc].BA;
const pmin = Math.min(...XR.wilcoxon.slice(1).filter((r) => r[1].startsWith("Part C (")).map((r) => parseFloat(r[6])));
bullets(s, [`Same CART set (${CR.cart_name}); J–M ${CR.jm[CR.cart_name].toFixed(3)} vs ${CC.jm[CC.cart_name].toFixed(3)}.`,
            `QDA on RF features: V3 ${pct(vCR("QDA on RF features", "V3"))} vs ${pct(vC("QDA on RF features", "V3"))}; V4 ${pct(vCR("QDA on RF features", "V4"))} vs ${pct(vC("QDA on RF features", "V4"))}.`,
            `RF classifier: V3 ${pct(vCR("RF classifier", "V3"))} vs ${pct(vC("RF classifier", "V3"))}.`,
            `No C′ vs C difference is significant (smallest paired p = ${pmin.toFixed(3)}).`,
            `C′ beats raw reflectance alone (Part A) by 6–16 points in every pipeline.`], 8.7, 4.05, 4.1, 2.5, 12);

s = content("C′ vs C · Reading the comparison");
bullets(s, (J.txt.cr || []).slice(0, 3), M, 1.2, W - 2 * M, 5.4, 15);

s = content("C′ vs C and C′ vs A · Paired Wilcoxon tests on identical folds");
const cr = [["First", "Second", "V3 Δ BA", "V3 wins", "V3 p", "V4 Δ BA", "V4 wins", "V4 p"]];
for (let i = 1; i < XR.wilcoxon.length; i += 2) {
  const a = XR.wilcoxon[i], b = XR.wilcoxon[i + 1];
  cr.push([a[0], a[1], a[3], a[4] + "/" + (+a[4] + +a[5]), a[6], b[3], b[4] + "/" + (+b[4] + +b[5]), b[6]]);
}
table(s, cr, M, 1.2, W - 2 * M, { colW: [3.4, 3.4, 0.95, 0.85, 0.85, 0.95, 0.85, 1.08], fontSize: 10, rowH: 0.34 });
bullets(s, (J.txt.cr || []).slice(3, 5), M, 4.6, W - 2 * M, 2.0, 13);

s = content("C′ vs C · What the selectors take: raw bands vs K1 bands, overlap");
table(s, XR.comp, M, 1.2, 6.2, { colW: [0.8, 2.6, 0.7, 0.7, 0.7, 0.7], fontSize: 9.5, rowH: 0.26 });
table(s, XR.raw_bands, M, 4.25, 6.2, { colW: [0.7, 0.9, 1.0, 0.9, 0.9, 1.0, 0.8], fontSize: 8, rowH: 0.3 });
table(s, XR.overlap.map((r) => [r[0], r[3], r[4], r[5], r[6]]), 6.9, 1.2, 5.9, { colW: [1.0, 1.5, 0.7, 1.4, 1.3], fontSize: 8.5 });
bullets(s, (J.txt.cr || []).slice(5), 6.9, 4.25, 5.9, 2.5, 11.5);

// ----------------------------------------------------------------- additional
sec("Additional checks and synthesis");
s = content("Additional step · V5: an unseen date in unseen plots");
img(s, "F30_V5_leave_one_date_out", M, 1.1, 7.6, 3.6);
table(s, X.lodo, M, 4.8, W - 2 * M, { colW: [4.3, 2.0, 2.0, 2.0, 2.0], fontSize: 10, rowH: 0.22 });
bullets(s, (J.txt.v5 || []), 8.3, 1.2, 4.5, 3.4, 13);

s = content("Additional step · Does the signal hold within each date, stage and variety?");
table(s, X.strata_range, M, 1.2, W - 2 * M, { colW: [4.4, 1.6, 2.1, 2.1, 2.1], fontSize: 11, rowH: 0.34 });
bullets(s, (J.txt.strata || []), M, 4.6, W - 2 * M, 2.0, 14);

s = content("Synthesis · All approaches on new plots");
img(s, "F29_synthesis", M, 1.1, 6.6, 5.6);
table(s, X.synthesis.slice(0, 13).map((r) => [r[0].slice(0, 52), r[1], r[2], r[3]]), 7.3, 1.2, 5.5, { colW: [3.1, 0.8, 0.8, 0.8], fontSize: 8.5, rowH: 0.27 });

s = content("Conclusions");
bullets(s, (J.txt.conclusions || []).slice(0, 7), M, 1.15, W - 2 * M, 5.8, 14);
s = content("Recommendations");
bullets(s, (J.txt.recommendations || []), M, 1.2, W - 2 * M, 5.6, 15);

s = content(`Appendix · Every step was cross-checked (${J.checks.pass} PASS, ${J.checks.flag} FLAG, ${J.checks.fail} FAIL)`);
const ck = J.checks.table;
const half = Math.ceil((ck.length - 1) / 2);
table(s, [ck[0].slice(1, 5)].concat(ck.slice(1, 1 + Math.min(half, 22)).map((r) => [r[1], r[2].slice(0, 36), r[3].slice(0, 48), r[4]])), M, 1.15, 6.1,
      { colW: [0.9, 2.0, 2.6, 0.6], fontSize: 7.5, rowH: 0.22 });
table(s, [ck[0].slice(1, 5)].concat(ck.slice(1 + Math.min(half, 22), 45).map((r) => [r[1], r[2].slice(0, 36), r[3].slice(0, 48), r[4]])), 6.75, 1.15, 6.1,
      { colW: [0.9, 2.0, 2.6, 0.6], fontSize: 7.5, rowH: 0.22 });
note(s, "Full register with methods: workbook sheet 33_CrossChecks.");

const refs = J.txt.references || [];
const per = Math.ceil(refs.length / 3);
for (let k = 0; k < 3; k++) {
  s = content(`References (${k + 1}/3)`);
  bullets(s, refs.slice(k * per, (k + 1) * per), M, 1.1, W - 2 * M, 5.9, 11);
}

pres.writeFile({ fileName: OUT }).then(async () => { await applyTheme(OUT, THEME); console.log("deck written", OUT); });
