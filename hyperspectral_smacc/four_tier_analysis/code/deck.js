const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
const { applyTheme } = require(process.env.SKILL + "/scripts/apply_theme.js");

const RES = process.env.RES;                       // results folder
const OUT = process.argv[2];
const D = JSON.parse(fs.readFileSync(path.join(RES, "deck_data.json"), "utf8"));
const IMG = (f) => path.join(RES, f);
const pct = (v, d = 1) => (100 * v).toFixed(d) + "%";
const f2 = (v, d = 2) => Number(v).toFixed(d);

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
const HX = THEME.colors;   // hex values for hex-only options
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";        // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Four-tier analysis of SMACC endmembers";
const C = pres.SchemeColor;
const W = 13.333, H = 7.5, MX = 0.6, CW = W - 2 * MX, TOP = 1.4, BOT = 6.85;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "TITLE", background: { color: HX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 1.9, fontFace: THEME.headFontFace, fontSize: 40, bold: true, color: C.background1, valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 1.6, fontFace: THEME.bodyFontFace, fontSize: 18, color: "CADDD2", valign: "top", margin: 0 }, text: "" } },
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
    { text: { text: "Healthy vs diseased · four-tier analysis + Random Forest", options: { x: MX, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: HX.accent6, fontFace: THEME.bodyFontFace, margin: 0 } } },
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
function img(s, file, x, y, maxW, maxH, name) {
  const [pw, ph] = sizes[file];
  const ar = pw / ph;
  let w = maxW, h = maxW / ar;
  if (h > maxH) { h = maxH; w = maxH * ar; }
  s.addImage({ path: IMG(file), x: x + (maxW - w) / 2, y: y + (maxH - h) / 2, w, h, objectName: name || file, altText: name || file });
}
function body(s, items, x, y, w, h, size = 15, opts = {}) {
  const arr = items.map((t, i) => {
    const o = { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 };
    // pptxgenjs writes an invalid mid-paragraph <a:pPr> for extra runs, so each bullet is one run
    if (Array.isArray(t)) return [{ text: t.map((r) => r.text).join(""), options: o }];
    return [{ text: t, options: o }];
  }).flat();
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
function caption(s, text, x, y, w) {
  s.addText(text, { x, y, w, h: 0.35, fontSize: 11, italic: true, color: HX.accent6, margin: 0, isTextBox: true });
}
const sizes = {};
for (const f of fs.readdirSync(RES).filter((f) => f.endsWith(".png"))) {
  const b = fs.readFileSync(IMG(f));
  sizes[f] = [b.readUInt32BE(16), b.readUInt32BE(20)];
}
const q = D.qda, rfC = D.rf["CART bands (tiers 2-3)"], rfS = D.rf["All ANOVA-significant bands"], rfA = D.rf["All 463 bands"];
const t1 = D.tier1, t3 = D.tier3, cart = D.cart;
const selTxt = cart.bandsA.map((b) => b.toFixed(1)).join(", ");

// ================================================================== 1 TITLE
newSection("Introduction");
slide("TITLE", "Discriminating healthy and diseased canopy from SMACC endmembers",
  "Four-tier hierarchical analysis (ANOVA → CART → J–M distance → QDA) after Das et al. (2020), with Random Forest comparison and cross-validation checks\nImage subset_200526 · 24 Feb 2026 · 300 + 300 SMACC endmembers · reflectance only");

// ================================================================== 2 WORKFLOW
{
  const s = slide("CONTENT", "Workflow at a glance");
  const blocks = [
    ["A", "Before the analysis", ["Hyperspectral image (483 bands)", "ROIs: healthy & diseased", "Pixel extraction + NDVI filter", "SMACC: 300 endmembers / class", "Quality screening"], HX.accent6],
    ["B", "Four-tier analysis", ["Tier 1: one-way ANOVA per band", "Tier 2: CART band selection", "Tier 3: J–M distance", "Tier 4: QDA, 10-fold CV"], HX.dk2],
    ["C", "Comparison", ["Random Forest, 500 trees", "Three band sets", "Same folds as QDA", "Band importance"], HX.accent4],
    ["D", "Cross-checks", ["Nested & spatial-block CV", "Permutation test", "Location-only control", "Sensitivity analyses", "Excel ↔ Python checks"], HX.accent3],
  ];
  const bw = 2.85, gap = 0.243;
  blocks.forEach(([k, t, items, col], i) => {
    const x = MX + i * (bw + gap), y = 1.55;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: bw, h: 4.0, fill: { color: HX.lt2 }, line: { color: HX.lt2 }, rectRadius: 0.08, objectName: "stage " + k });
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.22, w: 0.62, h: 0.62, fill: { color: col }, line: { color: col }, objectName: "stage badge " + k });
    s.addText(k, { x: x + 0.2, y: y + 0.22, w: 0.62, h: 0.62, align: "center", valign: "middle", fontSize: 22, bold: true, color: HX.lt1, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(t, { x: x + 0.95, y: y + 0.22, w: bw - 1.1, h: 0.62, fontSize: 17, bold: true, color: C.text2, valign: "middle", margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(items.map((it, j) => ({ text: it, options: { bullet: { type: "number" }, breakLine: j < items.length - 1, paraSpaceAfter: 8 } })),
      { x: x + 0.2, y: y + 1.1, w: bw - 0.35, h: 2.75, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
    if (i < 3) s.addText("›", { x: x + bw - 0.02, y: y + 1.7, w: gap + 0.04, h: 0.6, fontSize: 30, color: HX.accent6, align: "center", margin: 0, isTextBox: true });
  });
  s.addText(`Input: 600 SMACC endmembers (300 healthy, 300 diseased) × 483 bands → ${D.analysis.N} spectra × ${D.analysis.P} bands analysed. Reflectance values only; seed 42 for every random step.`, { x: MX, y: 5.85, w: CW, h: 0.7, fontSize: 15, color: C.text1, margin: 0, isTextBox: true, valign: "middle" });
}

// ================================================================== PART A
newSection("A. Before the analysis");
slide("SECTION", "A · Steps before the analysis", "From the hyperspectral image to 300 healthy and 300 diseased SMACC endmembers, and the quality screening of those spectra");

{
  const s = slide("CONTENT", "Input hyperspectral image");
  table(s, [
    ["Property", "Value (from the ENVI header)"],
    ["File", "subset_200526 (+ .hdr), acquired 24-02-2026"],
    ["Format", "ENVI, band-interleaved-by-line, 32-bit float"],
    ["Size", "2,355 columns × 2,142 rows × 483 bands"],
    ["Spectral range", "399.4–2,397.6 nm (≈1.76 nm VNIR, ≈6 nm SWIR)"],
    ["Bands already absent", "≈899–916, 1,330–1,460, 1,780–1,970 nm (water vapour)"],
    ["Coordinates", "Geographic WGS-84"],
    ["Pixel size", "≈2.25 × 2.22 cm on the ground"],
    ["Pre-processing in header", "Mask applied (masked pixels = 0); smoothed spectra (band names '…_rd_smt')"],
  ], MX, 1.5, 7.9, [2.6, 5.3], { fontSize: 13, rowH: 0.5 });
  stat(s, 9.1, 1.55, 3.6, "483", "spectral bands in the image");
  stat(s, 9.1, 3.0, 3.6, "≈ 2.2 cm", "ground pixel size: single leaves, soil gaps and shadow are resolved");
  stat(s, 9.1, 4.45, 3.6, "400–2400 nm", "VNIR + SWIR coverage, water bands removed");
}

{
  const s = slide("CONTENT", "Regions of interest and endmember positions");
  table(s, [
    ["ROI file", "Polygons", "Pixels inside", "Area"],
    ["healthy.xml", "1 (7 vertices)", "≈ 601,000", "≈ 300 m²"],
    ["diseased.xml", "1 (5 vertices)", "≈ 1,940,000", "≈ 966 m²"],
  ], MX, 1.55, 6.3, [1.7, 1.55, 1.6, 1.45], { fontSize: 13, rowH: 0.45 });
  body(s, [
    "ROIs digitised in ENVI over a healthy area and a diseased area, irrespective of plot, and exported as XML in WGS-84",
    "The two polygons share one boundary: healthy and diseased samples come from two neighbouring blocks of the field",
    "Every endmember keeps its pixel row/column and lon/lat, which allows spatial checks later (Part D)",
  ], MX, 3.15, 6.3, 3.4, 15);
  img(s, "fig01_locations.png", 7.2, 1.45, 5.5, 5.4, "Map of endmember positions");
}

{
  const s = slide("CONTENT", "How the 300 endmembers per class were extracted");
  const steps = [
    ["ROI → pixels", "Polygon vertices converted from lon/lat to image pixels; a pixel belongs to the ROI if its centre lies inside"],
    ["Remove no-data", "All-zero (masked) and NaN spectra discarded"],
    ["Vegetation filter", "NDVI = (R800 − R670)/(R800 + R670) ≥ 0.30 removes soil, water and shadow (minimum NDVI in the file: 0.31)"],
    ["Random subset", "Up to 100,000 pixels per class drawn at random (memory; neighbouring 2 cm pixels are near-identical)"],
    ["SMACC", "Run separately per class on 463 bands (420–2,350 nm), positivity + convex-cone constraints, 300 iterations"],
    ["Save", "All 483 bands of each selected pixel + row/col + lon/lat → CSV and ENVI spectral libraries"],
  ];
  steps.forEach(([t, d], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = MX + col * 6.13, y = 1.5 + row * 1.75, w = 5.95, h = 1.55;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: HX.lt2 }, line: { color: HX.lt2 }, rectRadius: 0.08, objectName: "extraction step " + (i + 1) });
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.22, w: 0.55, h: 0.55, fill: { color: HX.dk2 }, line: { color: HX.dk2 } });
    s.addText(String(i + 1), { x: x + 0.2, y: y + 0.22, w: 0.55, h: 0.55, align: "center", valign: "middle", fontSize: 18, bold: true, color: HX.lt1, margin: 0, isTextBox: true });
    s.addText(t, { x: x + 0.95, y: y + 0.18, w: w - 1.1, h: 0.45, fontSize: 17, bold: true, color: C.text2, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(d, { x: x + 0.95, y: y + 0.62, w: w - 1.15, h: 0.85, fontSize: 13.5, color: C.text1, margin: 0, isTextBox: true, valign: "top" });
  });
  caption(s, "Settings as in smacc_endmember_extraction.ipynb (defaults). The NDVI filter is confirmed by the data: no endmember has NDVI < 0.30 at 670/800 nm.", MX, 6.55, CW);
}

{
  const s = slide("CONTENT", "SMACC — sequential maximum angle convex cone");
  const steps = [
    "Start: residual R = all pixel spectra H (N pixels × 463 bands)",
    "Pick the pixel with the largest residual norm ‖rᵢ‖; store its original spectrum as the next endmember",
    "Project every residual on that pixel's residual w: Oᵢ = (rᵢ·w)/(w·w)",
    "Positivity: coefficients ≤ 0 set to 0. Convex cone: limit αᵢ so no earlier abundance turns negative",
    "Update residuals rᵢ ← rᵢ − αᵢw and abundances",
    "Repeat until 300 endmembers per class",
  ];
  s.addText(steps.map((t, i) => ({ text: t, options: { bullet: { type: "number" }, breakLine: i < steps.length - 1, paraSpaceAfter: 10 } })),
    { x: MX, y: 1.55, w: 7.4, h: 4.6, fontSize: 16, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.4, y: 1.55, w: 4.33, h: 2.0, fill: { color: HX.lt2 }, line: { color: HX.lt2 }, rectRadius: 0.08 });
  s.addText([{ text: "Model", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
    { text: "h = Σ fₖ·sₖ + r,   fₖ ≥ 0", options: { fontSize: 20, fontFace: "Cambria", italic: true, color: C.text1 } }],
    { x: 8.6, y: 1.7, w: 3.95, h: 1.7, margin: 0, isTextBox: true, valign: "top" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.4, y: 3.8, w: 4.33, h: 2.6, fill: { color: "FDEBE3" }, line: { color: "FDEBE3" }, rectRadius: 0.08 });
  s.addText([{ text: "Key property", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
    { text: "SMACC returns the most extreme (purest, most distinct) spectra of each ROI, not typical ones. This matters when they are used as samples for statistics (see Discussion).", options: { fontSize: 14, color: C.text1 } }],
    { x: 8.6, y: 3.95, w: 3.95, h: 2.35, margin: 0, isTextBox: true, valign: "top" });
  caption(s, "Gruninger, Ratkowski & Hoke (2004), Proc. SPIE 5425.", MX, 6.45, 7);
}

{
  const s = slide("CONTENT", "The 600 extracted endmember spectra");
  img(s, "fig02_spectra.png", MX, 1.4, CW, 4.6, "All endmember spectra by class");
  caption(s, "Thin lines: individual endmembers (n = 300 per class); black: class mean. Gaps are the water-vapour bands removed before extraction.", MX, 6.2, CW);
}

{
  const s = slide("CONTENT", "Quality screening of the endmembers");
  table(s, [
    ["Class", "EM no.", "NDVI", "R800/R670", "NDWI", "Reason removed"],
    ...D.removed.map((r) => [r.class, r.endmember_no, f2(r.NDVI, 3), f2(r.SR_800_670, 2), f2(r.NDWI, 3), r.remove_reason]),
  ], MX, 1.55, 6.6, [1.0, 0.8, 0.75, 1.05, 0.8, 2.2], { fontSize: 12, rowH: 0.42 });
  body(s, [
    "Rules: NDVI < 0.30, R800/R670 < 2, NDWI > 0, R800 < 0.10 → not vegetation → removed (3 of 600)",
    "Noisy detector edges (< 420 nm, > 2,350 nm) excluded: 20 of 483 bands",
    [{ text: `Negative (impossible) reflectance in ${D.neg_spectra.diseased} diseased vs ${D.neg_spectra.healthy} healthy spectra`, options: { bold: true } },
     { text: ", almost all in SWIR-2 (1,970–2,400 nm): a radiometric-quality warning for that region" }],
  ], MX, 3.5, 6.6, 3.2, 15);
  img(s, "fig04_negatives.png", 7.45, 1.5, 5.28, 2.95, "Negative reflectance by band");
  stat(s, 7.6, 4.85, 2.4, String(D.neg_spectra.diseased), "diseased spectra with values < 0", HX.accent2);
  stat(s, 10.2, 4.85, 2.4, String(D.neg_spectra.healthy), "healthy spectra with values < 0", HX.accent1);
}

{
  const s = slide("CONTENT", "Analysis data set: reflectance only");
  stat(s, MX, 1.5, 2.8, String(D.analysis.N), "endmember spectra analysed");
  stat(s, MX + 3.05, 1.5, 2.8, `${D.analysis.nH} / ${D.analysis.nD}`, "healthy / diseased");
  stat(s, MX + 6.1, 1.5, 2.8, String(D.analysis.P), "reflectance bands (420–2,350 nm)");
  stat(s, MX + 9.15, 1.5, 2.95, "0", "transformations (no indices, derivatives or normalisation)");
  img(s, "fig03_mean_sd.png", MX, 2.95, CW, 3.55, "Class mean spectra with SD");
  caption(s, "Mean ± SD. Diseased is lower in VIS, SWIR-1 and SWIR-2; slightly higher around 950–1,100 nm.", MX, 6.55, CW);
}

// ================================================================== PART B
newSection("B. Four-tier analysis");
slide("SECTION", "B · Four-tier hierarchical analysis", "Tier 1 ANOVA → Tier 2 CART → Tier 3 Jeffries–Matusita distance → Tier 4 QDA, as in Das et al. (2020)");

{
  const s = slide("CONTENT", "The four tiers, adapted from 14 genotypes to 2 classes");
  table(s, [
    ["Tier", "Das et al. (2020)", "This study"],
    ["Data", "336 field spectra, 14 rice genotypes (91 pairs)", `${D.analysis.N} image endmembers, 2 classes (1 pair)`],
    ["1 · ANOVA", "One-way ANOVA per band, p < 0.05; Tukey HSD; count of significant pairs per band", "One-way ANOVA per band, p < 0.05; Tukey HSD (same as ANOVA with 1 pair); FDR, Bonferroni and Cohen's d added"],
    ["2 · CART", "rpart on reflectance → 17 bands", "rpart-equivalent tree on the significant bands (Gini, minsplit 20, minbucket 7, cp 0.01)"],
    ["3 · J–M", "J–M per genotype pair on CART bands; threshold 1.94 (of 2)", "J–M healthy vs diseased on CART bands; threshold 1.94 (0–2 scale)"],
    ["4 · QDA", "QDA, 10-fold CV; confusion matrix, OA, PA, UA → 98%", "QDA, 10-fold CV (+ 10× repeated); plus nested and spatial-block CV"],
  ], MX, 1.5, CW, [1.6, 4.9, 5.63], { fontSize: 13, rowH: [0.45, 0.55, 0.85, 0.7, 0.7, 0.7] });
  caption(s, "J–M is reported on the 0–2 scale, JM = 2(1 − e^(−B)); the paper prints the √ form but uses the 0–2 threshold.", MX, 6.2, CW);
}

{
  const s = slide("CONTENT", `Tier 1 · ${t1.sig} of ${t1.n} bands differ significantly`);
  img(s, "fig05_tier1.png", MX, 1.35, 7.4, 5.5, "Tier 1 ANOVA results");
  card(s, 8.25, 1.5, 4.48, 5.2, "What the test shows", [
    `${t1.sig} bands significant at p < 0.05 (${t1.fdr} after FDR, ${t1.bonf} after Bonferroni)`,
    "All VIS, SWIR-1 and SWIR-2 bands significant; most NIR bands not",
    `Strongest band ${t1.maxF_wl.toFixed(1)} nm (F = ${t1.maxF.toFixed(1)}), at the noisy end of SWIR-2`,
    `Effects are small to moderate: largest |d| = ${t1.max_abs_d.toFixed(2)}; only ${t1.large_d} bands reach |d| ≥ 0.8`,
  ], HX.lt2, 14);
}

{
  const s = slide("CONTENT", "Tier 1 by spectral region");
  table(s, [
    ["Region", "Bands", "p < 0.05", "FDR q < 0.05", "Bonferroni", "Max-F band (nm)", "Max F", "Direction"],
    ...D.tier1_regions.map((r) => [r.region, r.bands, r.significant_p05, r.significant_FDR, r.significant_Bonferroni, r.max_F_band_nm, r.max_F, r.direction]),
    [{ text: "Total", options: { bold: true } }, t1.n, t1.sig, t1.fdr, t1.bonf, "", "", ""],
  ], MX, 1.55, CW, [2.4, 1.0, 1.15, 1.45, 1.35, 1.75, 1.2, 1.83], { fontSize: 13, rowH: 0.46 });
  body(s, [
    "With two classes Tukey HSD tests one pair, so it gives exactly the same decision as the ANOVA at every band (checked)",
    "Diseased is lower in VIS, red-edge, SWIR-1 and SWIR-2; only a NIR shoulder (1,047–1,101 nm) is slightly higher. A darker visible signal is opposite to the usual chlorosis response",
    "Many tests (463): the FDR column is the safer list of differing bands",
  ], MX, 5.0, CW, 1.8, 15);
}

{
  const s = slide("CONTENT", "Tier 2 · CART settings and tree size");
  card(s, MX, 1.5, 5.0, 5.2, "Settings (R rpart defaults)", [
    `Input: ${cart.n_input_bands} ANOVA-significant bands`,
    "Gini splitting; minsplit 20; minbucket 7",
    "Cost-complexity pruning on misclassification, cp = 0.01 (as rpart)",
    "10-fold cross-validation of every subtree (printcp)",
    `cp = 0.01 tree: ${cart.nsplitA} splits, ${cart.bandsA.length} bands, resubstitution accuracy ${pct(cart.train_acc_A)}`,
    `1-SE tree: ${cart.nsplitB} splits, ${cart.bandsB.length} bands (${cart.bandsB.map((b) => b.toFixed(0)).join(", ")} nm)`,
  ], HX.lt2, 14);
  img(s, "fig06_cp.png", 5.9, 1.45, 6.83, 4.9, "CART complexity plot");
  caption(s, `CV error is flat from 3 to 12 splits; the cp = 0.01 tree (used, as in the paper) is within about 1 SE of the minimum.`, 5.9, 6.4, 6.83);
}

{
  const s = slide("CONTENT", "Tier 2 · The CART tree");
  img(s, "fig07_tree.png", MX, 1.3, CW, 5.4, "CART tree diagram");
  caption(s, `First split R2350 ≤ 0.015 sends 149 spectra (138 diseased) left; CV accuracy of the tree itself as a classifier: ${pct(cart.cv_acc_cart_A)}.`, MX, 6.62, CW);
}

{
  const s = slide("CONTENT", `Tier 2 · ${cart.bandsA.length} bands selected by CART`);
  img(s, "fig08_selected_bands.png", MX, 1.4, 7.6, 3.6, "Selected bands on the mean spectra");
  table(s, [["Band (nm)", "Importance"], ...D.cart_imp.map((r) => [r.wavelength_nm, r.importance_pct.toFixed(1) + "%"])],
    8.5, 1.45, 4.23, [2.1, 2.13], { fontSize: 12, rowH: 0.33 });
  body(s, [
    "7 of 11 bands lie in SWIR-2; 2,349.5 nm alone carries 48% of the tree's importance",
    "One band each in blue (480), red (675), NIR (1,059) and SWIR-1 (1,629)",
  ], MX, 5.25, 7.6, 1.5, 15);
}

{
  const s = slide("CONTENT", `Tier 3 · J–M distance ${f2(t3.JM_0to2, 3)}: below the 1.94 threshold`);
  table(s, [
    ["Quantity (11 CART bands)", "Value"],
    ["Mahalanobis term ⅛ dᵀC⁻¹d", f2(t3.mahalanobis_term, 4)],
    ["Covariance term ½ ln(|C| / √|CH||CD|)", f2(t3.covariance_term, 4)],
    ["Bhattacharyya distance B", f2(t3.B, 4)],
    [{ text: "JM = 2(1 − e^(−B)), 0–2 scale", options: { bold: true } }, { text: f2(t3.JM_0to2, 4), options: { bold: true } }],
    ["√ form (0–1.414)", f2(t3.JM_sqrt, 4)],
    ["Separable (≥ 1.94)?", { text: "No", options: { bold: true, color: HX.accent2 } }],
  ], MX, 1.5, 5.6, [3.9, 1.7], { fontSize: 13, rowH: 0.42 });
  body(s, [
    `With all ${t3.n_sig} significant bands the covariance matrix has rank ${t3.cov_rank_all_sig} (< ${t3.n_sig}), so J–M cannot be computed — the reason the paper uses CART bands`,
    "Most of the distance comes from different covariance, not different means",
  ], MX, 4.65, 5.6, 2.1, 14);
  img(s, "fig09_jm.png", 6.45, 1.4, 6.28, 5.05, "J-M distance plots");
  caption(s, `Best single band: ${D.jm_band_max.wl.toFixed(1)} nm (JM ${f2(D.jm_band_max.jm, 3)}). Separability rises with each band but stays far below 1.94.`, 6.45, 6.5, 6.28);
}

{
  const s = slide("CONTENT", `Tier 4 · QDA, 10-fold cross-validation: ${pct(q.OA)}`);
  const cm = q.cm;
  table(s, [
    ["Reference ↓ / Predicted →", "Healthy", "Diseased", "Total", "Producer's acc."],
    [{ text: "Healthy", options: { bold: true } }, cm[0][0], cm[0][1], cm[0][0] + cm[0][1], pct(q.PA_H)],
    [{ text: "Diseased", options: { bold: true } }, cm[1][0], cm[1][1], cm[1][0] + cm[1][1], pct(q.PA_D)],
    [{ text: "Total", options: { bold: true } }, cm[0][0] + cm[1][0], cm[0][1] + cm[1][1], cm[0][0] + cm[0][1] + cm[1][0] + cm[1][1], ""],
    [{ text: "User's acc.", options: { bold: true } }, pct(q.UA_H), pct(q.UA_D), "", ""],
  ], MX, 1.55, 7.2, [2.3, 1.2, 1.2, 1.0, 1.5], { fontSize: 14, rowH: 0.5 });
  body(s, [
    `Bands: the ${cart.bandsA.length} CART bands; equal priors; stratified folds`,
    `Diseased spectra are often called healthy (${cm[1][0]} of ${cm[1][0] + cm[1][1]}); healthy are recognised better`,
    "Paper-style validation: bands were chosen on all data before CV (see Part D)",
  ], MX, 4.4, 7.2, 2.3, 15);
  stat(s, 8.4, 1.55, 4.3, pct(q.OA), "overall accuracy (10-fold CV)", C.text2, 40);
  stat(s, 8.4, 3.0, 4.3, f2(q.kappa, 2), "Cohen's kappa", C.text2, 40);
  stat(s, 8.4, 4.45, 4.3, `${pct(q.rep_mean)} ± ${pct(q.rep_sd)}`, "mean ± SD over 10 repeated 10-fold CVs", C.text2, 30);
}

// ================================================================== PART C
newSection("C. Random Forest comparison");
slide("SECTION", "C · Random Forest comparison", "Same data, same 10 folds; 500 trees, mtry = √(number of bands), three band sets");

{
  const s = slide("CONTENT", "Random Forest on three band sets");
  const row = (name, r) => [name, r.n_bands, pct(r.OA), f2(r.kappa, 2), pct(r.oob), pct(r.PA_H), pct(r.PA_D)];
  table(s, [
    ["Model / bands", "Bands", "CV OA", "Kappa", "OOB OA", "PA healthy", "PA diseased"],
    ["QDA · CART bands (four-tier)", cart.bandsA.length, pct(q.OA), f2(q.kappa, 2), "–", pct(q.PA_H), pct(q.PA_D)],
    row("RF · CART bands", rfC), row("RF · all ANOVA-significant bands", rfS),
    [{ text: "RF · all 463 bands", options: { bold: true } }, rfA.n_bands, { text: pct(rfA.OA), options: { bold: true } }, f2(rfA.kappa, 2), pct(rfA.oob), pct(rfA.PA_H), pct(rfA.PA_D)],
  ], MX, 1.55, CW, [3.9, 1.0, 1.25, 1.1, 1.3, 1.75, 1.83], { fontSize: 14, rowH: 0.5 });
  card(s, MX, 4.35, 5.9, 2.35, "Settings", ["500 trees, Gini, bootstrap samples", "mtry = √p (3, 17 or 21 bands per split)", "Same stratified folds as QDA; seed 42"], HX.lt2, 14);
  card(s, 6.83, 4.35, 5.9, 2.35, "Reading the table", ["On the same 11 bands RF ≈ QDA", "RF on all bands is best and needs no band selection", "OOB agrees with CV within 1.5 points"], HX.lt2, 14);
}

{
  const s = slide("CONTENT", "Where Random Forest finds the information");
  img(s, "fig10_rf_importance.png", MX, 1.4, CW, 4.5, "Random Forest importance");
  body(s, [
    `Top RF bands: ${D.rf_top.slice(0, 5).map((r) => r.wavelength_nm.toFixed(0)).join(", ")} nm — the same SWIR-2 region that dominates CART and ANOVA`,
    "Two independent methods agree on where the difference is; whether that difference is physiological or radiometric is discussed in Part D",
  ], MX, 5.95, CW, 0.9, 14);
}

{
  const s = slide("CONTENT", "QDA vs Random Forest (paper-style validation)");
  s.addChart(pres.charts.BAR, [{ name: "Overall accuracy", labels: ["QDA · CART bands", "RF · CART bands", "RF · significant bands", "RF · all bands"],
    values: [q.OA, rfC.OA, rfS.OA, rfA.OA] }], {
    x: MX, y: 1.45, w: 7.6, h: 5.2, barDir: "col", chartColors: [HX.accent3, HX.accent4, HX.accent4, HX.accent4],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0%", dataLabelFontSize: 13, dataLabelColor: HX.dk1, dataLabelFontFace: "+mn-lt",
    valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0%", valAxisLabelColor: HX.accent6, catAxisLabelColor: HX.dk1,
    valAxisLabelFontFace: "+mn-lt", catAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
    valGridLine: { color: "E4E3DF", size: 0.75 }, catGridLine: { style: "none" }, showLegend: false,
    showTitle: true, title: "Overall accuracy, 10-fold CV (same folds)", titleFontSize: 14, titleColor: HX.dk1, titleFontFace: "+mn-lt", barGapWidthPct: 60,
  });
  card(s, 8.5, 1.5, 4.23, 5.15, "Comparison", [
    `QDA ${pct(q.OA)} and RF ${pct(rfC.OA)} on the same 11 bands: no real difference`,
    `RF on all 463 bands: ${pct(rfA.OA)} (kappa ${f2(rfA.kappa, 2)}) — the best result`,
    "All four are moderate: about one spectrum in four is misclassified",
    "Blue = four-tier QDA, yellow = Random Forest",
  ], HX.lt2, 14);
}

// ================================================================== PART D
newSection("D. Cross-checks and validation");
slide("SECTION", "D · Cross-checks and validation", "Is the accuracy real, and does it come from disease? Nested CV, spatial blocks, permutation test, location control, sensitivity and step-by-step checks");

{
  const s = slide("CONTENT", "Accuracy under stricter validation");
  const lab = ["Paper-style 10-fold", "Nested 10-fold", "Spatial blocks (nested)"];
  s.addChart(pres.charts.BAR, [
    { name: "QDA · CART bands", labels: lab, values: [q.OA, D.nested.qda.OA, D.spatial.qda.OA] },
    { name: "RF · CART bands", labels: lab, values: [rfC.OA, D.nested.rf_sel.OA, D.spatial.rf_sel.OA] },
    { name: "RF · all bands", labels: lab, values: [rfA.OA, D.nested.rf_all.OA, D.spatial.rf_all.OA] },
  ], {
    x: MX, y: 1.45, w: 7.9, h: 5.25, barDir: "col", barGrouping: "clustered", chartColors: [HX.accent3, HX.accent4, HX.accent5],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0%", dataLabelFontSize: 11, dataLabelColor: HX.dk1, dataLabelFontFace: "+mn-lt",
    valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0%", valAxisLabelColor: HX.accent6, catAxisLabelColor: HX.dk1,
    valAxisLabelFontFace: "+mn-lt", catAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
    valGridLine: { color: "E4E3DF", size: 0.75 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: HX.dk1,
    showTitle: true, title: "Overall accuracy by validation scheme", titleFontSize: 14, titleColor: HX.dk1, titleFontFace: "+mn-lt", barGapWidthPct: 50,
  });
  card(s, 8.75, 1.5, 3.98, 5.15, "What changes", [
    "Nested: ANOVA + CART redone inside each training fold — no information from test spectra",
    "Spatial: whole spatial blocks held out (next slide)",
    `QDA falls from ${pct(q.OA)} to ${pct(D.nested.qda.OA)} (nested) and ${pct(D.spatial.qda.OA)} (spatial)`,
    `RF on all bands holds best: ${pct(D.spatial.rf_all.OA)} spatial`,
  ], HX.lt2, 14);
}

{
  const s = slide("CONTENT", "Spatial-block cross-validation");
  img(s, "fig12_blocks.png", MX, 1.4, 5.3, 5.3, "Spatial blocks map");
  table(s, [["Fold", "Test spectra", "QDA", "RF (CART)", "RF (all)"],
    ...D.spatial_folds.map((f) => [f.fold, f.n_test, pct(f.qda), pct(f.rf_sel), pct(f.rf_all)]),
    [{ text: "Pooled", options: { bold: true } }, D.analysis.N, pct(D.spatial.qda.OA), pct(D.spatial.rf_sel.OA), pct(D.spatial.rf_all.OA)]],
    6.2, 1.5, 6.53, [0.9, 1.4, 1.35, 1.4, 1.48], { fontSize: 13, rowH: 0.42 });
  body(s, [
    "Five k-means blocks per class on pixel position; each fold holds out one healthy and one diseased block",
    "Band selection (ANOVA + CART) repeated inside every fold",
    "Accuracy varies by block: the signal is not uniform across the field",
  ], 6.2, 4.65, 6.53, 2.1, 14);
}

{
  const s = slide("CONTENT", "Permutation test and location-only control");
  img(s, "fig11_permutation.png", MX, 1.4, 5.9, 3.5, "Permutation test histogram");
  body(s, [
    `${D.perm.n} label shuffles through the full nested pipeline: null mean ${pct(D.perm.null_mean)}, maximum ${pct(D.perm.null_max)}`,
    `Observed ${pct(D.perm.observed)}: p = ${f2(D.perm.p, 3)} (the smallest possible with ${D.perm.n} shuffles) — the signal is real`,
  ], MX, 5.05, 5.9, 1.7, 14);
  table(s, [["Control: two halves of the same class", "n", "QDA paper-style", "QDA nested"],
    ...D.location.map((r) => [r.control, r.n, pct(r.paper_style_QDA_OA), pct(r.nested_QDA_OA)])],
    6.8, 1.5, 5.93, [2.75, 1.05, 1.1, 1.03], { fontSize: 12, rowH: 0.5 });
  card(s, 6.8, 3.35, 5.93, 3.3, "Interpretation", [
    "Two halves of the healthy region separate at ≈ 63–64% although both are healthy: part of the spectral difference is position in the field",
    "The diseased halves are near chance (≈ 52%)",
    "Healthy vs diseased (72–76%) exceeds the healthy-halves control, so disease adds signal, but location effects are not small",
  ], HX.lt2, 13.5);
}

{
  const s = slide("CONTENT", "Sensitivity analyses");
  table(s, [["Case", "Significant bands", "CART bands", "JM (0–2)", "QDA OA", "RF OA (all bands)"],
    ...D.sens.map((r) => [r.case, r.n_sig, r.n_sel, f2(r.JM, 3), pct(r.QDA_OA), pct(r.RF_all_OA)])],
    MX, 1.5, CW, [5.3, 1.45, 1.2, 1.15, 1.35, 1.68], { fontSize: 13, rowH: 0.5 });
  body(s, [
    [{ text: "Removing SWIR-2 ", options: { bold: true } }, { text: `lowers QDA to ${pct(D.sens[2].QDA_OA)} and RF to ${pct(D.sens[2].RF_all_OA)}; VNIR alone gives ≈ 60–62%. The discrimination leans on the noisiest region.` }],
    [{ text: "Keeping the 3 non-vegetation spectra ", options: { bold: true } }, { text: `inflates JM to ${f2(D.sens[1].JM, 2)} and QDA to ${pct(D.sens[1].QDA_OA)}: screening matters.` }],
    "The selected CART bands change with every data variant, so individual bands should not be over-interpreted",
  ], MX, 4.75, CW, 2.0, 14.5);
}

{
  const s = slide("CONTENT", "Every step was cross-checked");
  const groups = {};
  for (const c of D.checks) { const k = c.step.replace(/^0 /, "").replace(/^1 /, ""); (groups[k] = groups[k] || []).push(c); }
  const rows = [["Step", "Checks", "Examples", "Result"]];
  const ex = {
    "Data": "600 × 489, 300/300, no missing values, no duplicate pixels",
    "Screening": "597 spectra × 463 bands after screening",
    "Tier 1": "manual F = scipy; t² = F; Tukey = ANOVA at all bands",
    "Tier 2": "custom pruning reproduces sklearn tree; rel error = 1 − accuracy",
    "Tier 3": "log-det = direct det; 1-D closed form; covariance full rank",
    "Tier 4": "hand-coded QDA = sklearn; OA and N consistent",
    "RF": "seed reproducibility; OOB ≈ CV",
    "Validation": "permutation null centred at 50%",
  };
  for (const [k, v] of Object.entries(groups)) rows.push([k, v.length, ex[k] || "", { text: v.every((c) => c.result === "PASS") ? "PASS" : "FAIL", options: { bold: true, color: "008000" } }]);
  rows.push(["Excel ↔ Python", 10, "F, p, JM, B, OA, kappa recomputed by live Excel formulas", { text: "PASS", options: { bold: true, color: "008000" } }]);
  table(s, rows, MX, 1.5, CW, [2.2, 1.0, 7.73, 1.2], { fontSize: 13, rowH: 0.44 });
  caption(s, `${D.checks.length} Python checks + 10 live Excel checks, all PASS. Details: sheet 11_Cross_Checks of Four_Tier_Analysis.xlsx.`, MX, 6.45, CW);
}

// ================================================================== DISCUSSION / SUMMARY / CONCLUSION
newSection("Discussion and conclusion");
{
  const s = slide("CONTENT", "Discussion");
  const pts = [
    ["Moderate, not near-perfect, separation", `JM ${f2(t3.JM_0to2, 2)} (threshold 1.94) and 72–76% accuracy vs 98% in Das et al. Their samples were 50-scan field spectra of uniform plots; here they are 2 cm image pixels with mixed leaves, lesions and shadow.`],
    ["SWIR-2 drives the result — with a caveat", `The strongest bands (≈2,330–2,350 nm) sit in the noisiest region; ${D.neg_spectra.diseased} diseased spectra have negative reflectance there. Without SWIR-2 accuracy drops by 5–8 points.`],
    ["Unexpected visible signal", "Diseased canopy is darker in the visible, not brighter as chlorosis would cause; canopy structure, illumination or region effects are plausible and should be checked in the field."],
    ["Location and validation", "Halves of the healthy region separate at ≈ 64%; spatial-block CV lowers QDA to 65%. Paper-style CV overstates accuracy."],
    ["QDA vs Random Forest", "On the same bands they are equal; RF on all bands is the most accurate and most robust, needing no band selection."],
    ["SMACC endmembers as samples", "SMACC picks extreme spectra; statistics from them describe the extremes, not the typical canopy."],
  ];
  pts.forEach(([t, d], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = MX + col * 6.13, y = 1.45 + row * 1.8, w = 5.95, h = 1.65;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: HX.lt2 }, line: { color: HX.lt2 }, rectRadius: 0.08, objectName: "discussion " + (i + 1) });
    s.addText(t, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.4, fontSize: 15, bold: true, color: C.text2, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(d, { x: x + 0.2, y: y + 0.55, w: w - 0.4, h: h - 0.62, fontSize: 12.5, color: C.text1, margin: 0, isTextBox: true, valign: "top" });
  });
}

{
  const s = slide("CONTENT", "Summary");
  const items = [
    ["597", "endmembers analysed (298 H / 299 D) on 463 reflectance bands after screening"],
    [`${t1.sig}`, "bands differ significantly (Tier 1); all VIS, SWIR-1 and SWIR-2"],
    [`${cart.bandsA.length}`, "bands kept by CART (Tier 2); 7 in SWIR-2, 2,349.5 nm most important"],
    [f2(t3.JM_0to2, 2), "J–M distance (Tier 3), below the 1.94 separability threshold"],
    [pct(q.OA), `QDA accuracy (Tier 4), kappa ${f2(q.kappa, 2)}; ${pct(D.nested.qda.OA)} nested, ${pct(D.spatial.qda.OA)} spatial`],
    [pct(rfA.OA), `Random Forest on all bands; ${pct(D.spatial.rf_all.OA)} under spatial-block CV`],
  ];
  items.forEach(([v, l], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = MX + col * 4.1, y = 1.55 + row * 2.6;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 3.9, h: 2.35, fill: { color: HX.lt2 }, line: { color: HX.lt2 }, rectRadius: 0.08, objectName: "summary " + (i + 1) });
    s.addText(v, { x: x + 0.25, y: y + 0.2, w: 3.4, h: 0.85, fontSize: 38, bold: true, color: C.text2, margin: 0, isTextBox: true, fontFace: THEME.headFontFace, valign: "bottom" });
    s.addText(l, { x: x + 0.25, y: y + 1.15, w: 3.45, h: 1.1, fontSize: 14, color: C.text1, margin: 0, isTextBox: true, valign: "top" });
  });
}

{
  const s = slide("CLOSING", "Conclusion");
  s.addText([
    { text: "The four-tier method of Das et al. (2020) was applied step by step to the SMACC endmembers and every step was cross-checked.", options: { bullet: true, breakLine: true, paraSpaceAfter: 10 } },
    { text: `Healthy and diseased spectra differ significantly (permutation p = ${f2(D.perm.p, 3)}), but separation is moderate: JM ${f2(t3.JM_0to2, 2)} < 1.94 and realistic accuracy 65–76%.`, options: { bullet: true, breakLine: true, paraSpaceAfter: 10 } },
    { text: "Random Forest on all bands matches or beats the four-tier QDA under every validation scheme.", options: { bullet: true, breakLine: true, paraSpaceAfter: 10 } },
    { text: "Before relying on the SWIR-2 bands: verify radiometric calibration, sample random pixels or plot means instead of SMACC extremes, add plot-level ground truth and an independent date.", options: { bullet: true } },
  ], { x: MX, y: 1.6, w: CW, h: 5.0, fontSize: 20, color: HX.lt1, margin: 0, isTextBox: true, valign: "middle" });
}

pres.writeFile({ fileName: OUT }).then(async () => {
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
});
