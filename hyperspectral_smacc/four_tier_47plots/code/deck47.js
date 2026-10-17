const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
const { applyTheme } = require(process.env.SKILL + "/scripts/apply_theme.js");

const RES = process.env.RES;                         // results folder of the 47-plot analysis
const OUT = process.argv[2];
const D = JSON.parse(fs.readFileSync(path.join(RES, process.env.DJSON || "deck47.json"), "utf8"));
const IMG = (f) => path.join(RES, f);
const pct = (v, d = 1) => (v === null || v === undefined ? "—" : (100 * v).toFixed(d) + "%");
const f2 = (v, d = 2) => (v === null || v === undefined ? "—" : Number(v).toFixed(d));
const pm = (a, d = 3) => `${f2(a[0], d)} ± ${f2(a[1], d)}`;
const ci = (a, d = 1, mul = 100) => `${(a[0] * mul).toFixed(d)}–${(a[1] * mul).toFixed(d)}`;
const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;

const THEME = {
  name: "Canopy", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1B1F1D", lt1: "FFFFFF", dk2: "1F3A2E", lt2: "EEF3EF", accent1: "1BAF7A", accent2: "EB6834", accent3: "2A78D6", accent4: "EDA100", accent5: "6250D6", accent6: "52514E", hlink: "2A78D6", folHlink: "6250D6" },
};
const HX = THEME.colors;
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Four-tier analysis of 47-plot SMACC endmembers";
const C = pres.SchemeColor;
const W = 13.333, MX = 0.6, CW = W - 2 * MX;

pres.defineSlideMaster({ title: "TITLE", background: { color: HX.dk2 }, objects: [
  { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.6, w: 11.7, h: 2.3, fontFace: THEME.headFontFace, fontSize: 38, bold: true, color: C.background1, valign: "bottom", margin: 0 }, text: "" } },
  { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 2.0, fontFace: THEME.bodyFontFace, fontSize: 17, color: "CADDD2", valign: "top", margin: 0 }, text: "" } }] });
pres.defineSlideMaster({ title: "SECTION", background: { color: HX.dk2 }, objects: [
  { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.6, w: 11.7, h: 1.2, fontFace: THEME.headFontFace, fontSize: 40, bold: true, color: C.background1, valign: "bottom", margin: 0 }, text: "" } },
  { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.95, w: 11.7, h: 1.2, fontFace: THEME.bodyFontFace, fontSize: 18, color: "CADDD2", valign: "top", margin: 0 }, text: "" } }],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, color: "CADDD2", fontSize: 10, fontFace: THEME.bodyFontFace, align: "right" } });
pres.defineSlideMaster({ title: "CLOSING", background: { color: HX.dk2 }, objects: [
  { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.45, w: CW, h: 0.9, fontFace: THEME.headFontFace, fontSize: 36, bold: true, color: C.background1, valign: "middle", margin: 0 }, text: "" } }],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, color: "CADDD2", fontSize: 10, fontFace: THEME.bodyFontFace, align: "right" } });
pres.defineSlideMaster({ title: "CONTENT", background: { color: HX.lt1 }, margin: [0.5, 0.6, 0.7, 0.6], objects: [
  { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.35, w: CW, h: 0.85, fontFace: THEME.headFontFace, fontSize: 29, bold: true, color: C.text2, valign: "middle", margin: 0 }, text: "" } },
  { text: { text: "47 plots · healthy vs diseased · four-tier method (Das et al. 2020) with CART and Random Forest in Tier 2", options: { x: MX, y: 7.0, w: 10, h: 0.3, fontSize: 10, color: HX.accent6, fontFace: THEME.bodyFontFace, margin: 0 } } }],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, color: HX.accent6, fontSize: 10, fontFace: THEME.bodyFontFace, align: "right" } });

let section = "";
function slide(master, title, sub) { const s = pres.addSlide({ masterName: master, sectionTitle: section }); s.addText(title, { placeholder: "title" }); if (sub) s.addText(sub, { placeholder: "body" }); return s; }
function newSection(t) { section = t; pres.addSection({ title: t }); }
function notes(s, lines) { s.addNotes(lines.join("\n\n")); }
const sizes = {};
for (const f of fs.readdirSync(RES).filter((f) => f.endsWith(".png"))) { const b = fs.readFileSync(IMG(f)); sizes[f] = [b.readUInt32BE(16), b.readUInt32BE(20)]; }
function img(s, file, x, y, maxW, maxH, name) {
  const [pw, ph] = sizes[file]; const ar = pw / ph; let w = maxW, h = maxW / ar; if (h > maxH) { h = maxH; w = maxH * ar; }
  s.addImage({ path: IMG(file), x: x + (maxW - w) / 2, y: y + (maxH - h) / 2, w, h, objectName: name || file, altText: name || file });
}
function body(s, items, x, y, w, h, size = 15, opts = {}) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } })), { x, y, w, h, fontSize: size, color: C.text1, valign: "top", margin: 0, isTextBox: true, ...opts });
}
function card(s, x, y, w, h, title, lines, fill = HX.lt2, size = 14) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08, objectName: "card " + title });
  s.addText(title, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.4, fontSize: 16, bold: true, color: C.text2, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
  s.addText(lines.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < lines.length - 1, paraSpaceAfter: 4 } })), { x: x + 0.2, y: y + 0.6, w: w - 0.4, h: h - 0.72, fontSize: size, color: C.text1, valign: "top", margin: 0, isTextBox: true });
}
function stat(s, x, y, w, value, label, color = C.text2, vsize = 34) {
  s.addText(value, { x, y, w, h: 0.7, fontSize: vsize, bold: true, color, margin: 0, isTextBox: true, fontFace: THEME.headFontFace, valign: "bottom" });
  s.addText(label, { x, y: y + 0.72, w, h: 0.55, fontSize: 12, color: HX.accent6, margin: 0, isTextBox: true, valign: "top" });
}
function table(s, rows, x, y, w, colW, opts = {}) {
  const fs_ = opts.fontSize || 12;
  const out = rows.map((r, i) => r.map((c) => {
    const cell = typeof c === "object" && c !== null && c.text !== undefined ? c : { text: String(c) };
    const base = i === 0 ? { bold: true, color: HX.lt1, fill: { color: HX.dk2 }, fontSize: fs_, valign: "middle" } : { color: HX.dk1, fill: { color: i % 2 === 0 ? HX.lt2 : HX.lt1 }, fontSize: fs_, valign: "middle" };
    return { text: cell.text, options: { ...base, ...(cell.options || {}) } };
  }));
  s.addTable(out, { x, y, w, colW, border: { type: "solid", pt: 0.5, color: "C9D3CC" }, margin: opts.margin || [3, 6, 3, 6], fontFace: THEME.bodyFontFace, autoPage: false, rowH: opts.rowH, objectName: opts.name || "table" });
}
function caption(s, text, x, y, w, h = 0.35) { s.addText(text, { x, y, w, h, fontSize: 11, italic: true, color: HX.accent6, margin: 0, isTextBox: true, valign: "top" }); }
function boxes(s, items, x0, y0, cols, w, h, gx, gy, tsize = 15, dsize = 12.5) {
  items.forEach(([t, d], i) => {
    const x = x0 + (i % cols) * (w + gx), y = y0 + Math.floor(i / cols) * (h + gy);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: HX.lt2 }, line: { color: HX.lt2 }, rectRadius: 0.08, objectName: "box " + t });
    s.addText(t, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.4, fontSize: tsize, bold: true, color: C.text2, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(d, { x: x + 0.2, y: y + 0.55, w: w - 0.4, h: h - 0.62, fontSize: dsize, color: C.text1, margin: 0, isTextBox: true, valign: "top" });
  });
}
function errMatrix(s, x, y, a, title, w = 5.95) {
  const m = a.cm;
  s.addText(title, { x, y, w, h: 0.35, fontSize: 14.5, bold: true, color: C.text2, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
  table(s, [
    ["Reference \\ Predicted", "Healthy", "Diseased", "Total", "Producer's acc."],
    ["Healthy", m[0][0], m[0][1], m[0][0] + m[0][1], pct(a.PA_H)],
    ["Diseased", m[1][0], m[1][1], m[1][0] + m[1][1], pct(a.PA_D)],
    ["Total", m[0][0] + m[1][0], m[0][1] + m[1][1], a.n, ""],
    ["User's acc.", pct(a.UA_H), pct(a.UA_D), "", { text: `OA ${pct(a.OA)}`, options: { bold: true } }],
  ], x, y + 0.4, w, [1.6, 1.0, 1.0, 0.85, 1.5], { fontSize: 11.5, rowH: 0.34 });
}

const CV = D.cv, F = D.full, T2 = ["CART", "RF"], t1 = D.tier1;
const KEYS = ["CV1", "CV2", "CV3", "CV4", "CV5", "CV6"];
const KN = { CV1: "Das et al.: random 10-fold", CV2: "Plot-grouped nested (main)", CV3: "Leave-one-plot-out", CV4: "Leave-one-treatment-out", CV5: "Leave-one-variety-out", CV6: "Leave-one-date-out" };
const best = (k) => (CV.CART[k].BA[0] >= CV.RF[k].BA[0] ? "CART" : "RF");
const nc = (p) => D.nc.find((r) => r.pair === p);
const ncCtrl = D.nc.filter((r) => r.pair.startsWith("C ")), ncNeg = D.nc.filter((r) => !r.pair.startsWith("C "));
const ncMean = (arr, t2) => mean(arr.map((r) => r[t2].BA[0]));
const designBA = T2.flatMap((t) => ["CV4", "CV5", "CV6"].map((k) => CV[t][k].BA[0]));
const realBA = T2.flatMap((t) => ["CV2", "CV3", "CV4", "CV5", "CV6"].map((k) => CV[t][k].acc.spectra.BA));
const nEdge = (t) => F[t].bands.filter((b) => b < 420 || b > 2350).length;

// ================================================================== TITLE
newSection("Introduction");
{
  const s = slide("TITLE", "Discriminating healthy and diseased plots from SMACC endmembers: four-tier analysis with CART and Random Forest",
    `Method of Das et al. (2020): Tier 1 ANOVA → Tier 2 CART (or Random Forest) → Tier 3 Jeffries–Matusita distance → Tier 4 QDA\n47 plots (plot 4 excluded) · ${D.N} endmember spectra kept separately (${D.nH} healthy = 11 × 98; ${D.nD} diseased = 36 × 30) · ${D.P} reflectance bands`);
  notes(s, [
    "This presentation applies the four-tier hierarchical method of Das et al. (2020, Geocarto International 35:64–77) to separate healthy from diseased plots in one hyperspectral image.",
    `Input: SMACC endmembers extracted plot by plot — 98 endmembers from each of the 11 healthy plots (1–3, 5–12; plot 4 was excluded) and 30 from each of the 36 diseased plots (13–48). Every endmember is analysed as a separate sample; nothing is averaged. That gives ${D.nH} healthy and ${D.nD} diseased spectra over ${D.P} reflectance bands (399–2398 nm).`,
    "Tier 2 is run twice: with CART, as in the paper, and with Random Forest instead of CART, for comparison. Everything else is identical, so differences come from the band-selection step only.",
    "Every step is also done in the accompanying Excel workbook (Four_Tier_47plots.xlsx), mostly with live formulas, and cross-checked against Python.",
  ]);
}
// ================================================================== ABBREVIATIONS
{
  const per = 26, nsl = Math.ceil(D.abbr.length / per);
  for (let k = 0; k < nsl; k++) {
    const s = slide("CONTENT", `Abbreviations (${k + 1}/${nsl})`);
    const part = D.abbr.slice(k * per, (k + 1) * per);
    [part.slice(0, 13), part.slice(13)].forEach((col, j) => {
      if (col.length) table(s, [["Abbreviation", "Meaning"], ...col.map((r) => [{ text: r[0], options: { bold: true } }, r[1]])], MX + j * 6.13, 1.3, 5.95, [1.45, 4.5], { fontSize: 9.5, rowH: 0.36 });
    });
    if (k === 0) caption(s, "V1–V3 are varieties; validation schemes are CV1–CV6. 'D' alone = diseased, D1–D4 = inoculation dates; 'R' + wavelength = reflectance, R1–R3 = inoculated blocks.", MX, 6.55, CW, 0.35);
    notes(s, ["All abbreviations used on the slides and in the workbook (sheet 'Abbreviations').",
      "Two pairs look alike: V1–V3 are the three varieties from the treatment sheet, whereas CV1–CV6 are the six validation schemes. 'D' alone means diseased, while D1–D4 are the four inoculation dates (days after sowing). 'R2380' means reflectance at 2380 nm, while R1, R2 and R3 are the inoculated replication blocks."]);
  }
}
// ================================================================== WORKFLOW
{
  const s = slide("CONTENT", "Workflow at a glance");
  const blocks = [
    ["A", "Data", ["SMACC endmembers per plot", `${D.N} spectra, kept separate`, `All ${D.P} bands, reflectance only`, "Treatment design + plot map", "Data check"], HX.accent6],
    ["B", "Four-tier analysis", ["Tier 1: ANOVA + Tukey HSD", "Tier 2: CART  |  RF instead", "Tier 3: J–M distance per band and per set", "Tier 4: QDA"], HX.dk2],
    ["C", "Validation", ["CV1: as Das et al. (10-fold)", "CV2: plot-grouped nested", "CV3: leave-one-plot-out", "CV4–6: by treatment level", "Permutation tests"], HX.accent4],
    ["D", "Checks & controls", ["Error matrices + 95% CIs", "Block-vs-block negative control", "Band-removal sensitivity", "Python ↔ Excel checks"], HX.accent3],
  ];
  const bw = 2.85, gap = 0.243;
  blocks.forEach(([k, t, items, col], i) => {
    const x = MX + i * (bw + gap), y = 1.5;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: bw, h: 4.1, fill: { color: HX.lt2 }, line: { color: HX.lt2 }, rectRadius: 0.08, objectName: "stage " + k });
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.22, w: 0.62, h: 0.62, fill: { color: col }, line: { color: col }, objectName: "badge " + k });
    s.addText(k, { x: x + 0.2, y: y + 0.22, w: 0.62, h: 0.62, align: "center", valign: "middle", fontSize: 22, bold: true, color: HX.lt1, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(t, { x: x + 0.95, y: y + 0.22, w: bw - 1.1, h: 0.62, fontSize: 17, bold: true, color: C.text2, valign: "middle", margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(items.map((it, j) => ({ text: it, options: { bullet: { type: "number" }, breakLine: j < items.length - 1, paraSpaceAfter: 8 } })), { x: x + 0.2, y: y + 1.1, w: bw - 0.35, h: 2.85, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
    if (i < 3) s.addText("›", { x: x + bw - 0.02, y: y + 1.7, w: gap + 0.04, h: 0.6, fontSize: 30, color: HX.accent6, align: "center", margin: 0, isTextBox: true });
  });
  s.addText("Two analysis configurations: CART + QDA (the paper) and RF + QDA (comparison). Band selection is repeated inside every training fold in CV2–CV6. Seed 42 for all random steps.", { x: MX, y: 5.85, w: CW, h: 0.8, fontSize: 15, color: C.text1, margin: 0, isTextBox: true, valign: "middle" });
  notes(s, [
    "A – Data: the endmember spectra are read exactly as supplied, labelled by plot and class, and linked to the treatment sheet (block, variety, inoculation date) and to the plot polygons (EXCEPTPLOT4.xml).",
    "B – The four tiers of Das et al. (2020). Tier 1 keeps bands whose class means differ (one-way ANOVA, p < 0.05, Tukey HSD). Tier 2 reduces them to a small set with CART — or, for comparison, with Random Forest. Tier 3 measures how separable the classes are on those bands with the Jeffries–Matusita distance. Tier 4 classifies with quadratic discriminant analysis.",
    "C – Validation. CV1 is exactly the validation of the paper (10-fold cross-validation of QDA). Because spectra from the same plot are not independent, the main result is CV2, which holds out whole plots and repeats the band selection inside each fold. CV3–CV6 and the permutation tests check the result from other angles.",
    "D – Controls: complete accuracy assessment with confidence intervals, a negative control for the location effect, a sensitivity analysis with the band removal of the paper, and live Excel recomputation of every key number.",
  ]);
}

// ================================================================== A DATA
newSection("A. Data");
{ const s = slide("SECTION", "A · Data", "SMACC endmembers from 47 plots, the treatment design and a check of the spectra");
  notes(s, ["Part A describes the input data and checks it before any statistics are run. Problems found here (out-of-range values, unequal sampling) affect how later results must be read."]); }
{
  const s = slide("CONTENT", "47 plots and the analysis data set");
  img(s, "f01_plotmap.png", MX, 1.3, 6.1, 5.55, "Plot map");
  stat(s, 7.0, 1.45, 2.7, String(D.N), "endmember spectra analysed");
  stat(s, 9.9, 1.45, 2.8, `${D.nH} / ${D.nD}`, "healthy / diseased spectra");
  stat(s, 7.0, 2.85, 2.7, String(D.P), `reflectance bands (${D.wl_min.toFixed(0)}–${D.wl_max.toFixed(0)} nm)`);
  stat(s, 9.9, 2.85, 2.8, "11 / 36", "healthy / diseased plots", HX.accent2);
  body(s, [
    "Healthy: plots 1–3 and 5–12, 98 SMACC endmembers each; plot 4 excluded",
    "Diseased: plots 13–48, 30 SMACC endmembers each",
    "Endmembers are not averaged: each is one sample labelled with its plot's class",
    "Spectra are balanced (1 : 1.002) by design; plots are not (11 : 36)",
  ], 7.0, 4.3, 5.73, 2.5, 13.5);
  notes(s, [
    "The map shows the 47 plot polygons from EXCEPTPLOT4.xml (WGS-84 converted to local metres). Green = healthy plots, orange = diseased plots. Plot 4 is absent from the ROI file and from the spectra.",
    `Sampling: 98 endmembers per healthy plot × 11 plots = ${D.nH}; 30 per diseased plot × 36 plots = ${D.nD}. The two classes therefore have almost the same number of spectra, so no re-sampling or class weighting is needed for the main analysis.`,
    "The plots, however, are not balanced (11 vs 36). Each healthy plot contributes 98 spectra and each diseased plot 30, so a healthy plot weighs about three times more than a diseased plot. This is why the accuracy is also reported at plot level and why balanced accuracy is reported next to overall accuracy.",
    "Endmembers are analysed individually as requested. Note that SMACC endmembers are the most extreme spectra of a plot (the 'corners' of the data cloud), not random pixels, which increases within-class variability.",
  ]);
}
{
  const s = slide("CONTENT", "Treatment design (treatment_detail.xlsx)");
  img(s, "f13_design.png", MX, 1.3, 6.6, 5.55, "Treatment design map");
  table(s, [["Block", "Plots", "Treatment", "Class"], ["C", "1–3, 5–12", "Control (not inoculated)", "Healthy"], ["R3", "13–24", "Inoculated, replication 3", "Diseased"],
    ["R2", "25–36", "Inoculated, replication 2", "Diseased"], ["R1", "37–48", "Inoculated, replication 1", "Diseased"]], 7.4, 1.45, 5.33, [0.8, 1.05, 2.38, 1.1], { fontSize: 12, rowH: 0.36 });
  body(s, [
    `Each block: ${D.design.varieties.length} varieties (${D.design.varieties.join(", ")}) × ${D.design.dates.length} inoculation dates (${D.design.dates.join(", ")}, days after sowing); plot 4 (C, V1·D3) is missing`,
    "Blocks run west → east (C, R3, R2, R1), centres ≈ 13 m apart",
    "All healthy plots form one block, so class and location are confounded (Hurlbert 1984); CV4–CV6 and the negative control use this design",
  ], 7.4, 3.45, 5.33, 3.4, 13.5);
  notes(s, [
    "The treatment sheet shows a blocked layout. Block C holds the uninoculated control plots (healthy); blocks R3, R2 and R1 hold the inoculated plots (diseased). Every block contains the same 12 treatment combinations: 3 varieties × 4 inoculation dates.",
    "Why this matters for validation: plots, not endmembers, are the experimental units. Moreover, all healthy plots lie together at the west end of the field. Any west–east gradient (soil, moisture, illumination, sowing order) is therefore mixed with the healthy–diseased difference. Hurlbert (1984) calls this spatially segregated treatments; it is the main limitation of the data, and later slides measure it.",
    "The design also allows validation by treatment level: leaving out one variety, one inoculation date, or one variety × date combination at a time (CV4–CV6).",
  ]);
}
{
  const s = slide("CONTENT", "Endmember spectra per plot");
  img(s, "f02_counts.png", MX, 1.35, CW, 3.9, "Endmembers per plot");
  body(s, [`Healthy plots contribute 98 spectra each (${D.nH}), diseased plots 30 each (${D.nD}): equal class totals, unequal plot weights`,
    "Spectra of one plot share soil, illumination and treatment; they are not independent replicates, which is why validation must hold out whole plots"], MX, 5.4, CW, 1.4, 15);
  notes(s, ["The bar chart confirms the extraction design: 98 endmembers in every healthy plot and 30 in every diseased plot (checked automatically and with COUNTIF in sheet 2_Data_Summary).",
    "Because a plot's endmembers come from the same small area, they are correlated. Treating them as independent replicates inflates the apparent evidence (pseudo-replication; Hurlbert 1984). This is handled by (i) reporting the ANOVA also on plot means and (ii) validating with whole plots held out."]);
}
{
  const s = slide("CONTENT", "All endmember spectra");
  img(s, "f03_spectra.png", MX, 1.35, CW, 4.8, "All endmember spectra");
  caption(s, `Thin lines: individual endmembers (${D.nH} healthy, ${D.nD} diseased); black: class mean. Gaps are water-absorption bands missing from the image. SMACC selects extreme spectra, hence the wide spread.`, MX, 6.25, CW, 0.6);
  notes(s, ["Every endmember spectrum is drawn as a thin line; the black line is the class mean. Both classes show the typical vegetation shape: low visible reflectance with a green peak, a steep red edge near 700–750 nm, a high near-infrared plateau and water-absorption features in the SWIR.",
    "The spread within each class is large compared with the difference between the class means. This already suggests that the classes overlap strongly — confirmed by the J–M distances in Tier 3.",
    "The gaps (≈1330–1460 nm and ≈1780–1970 nm) are bands absent from the image because of atmospheric water vapour."]);
}
{
  const s = slide("CONTENT", "Class means and variability");
  img(s, "f04_mean_sd.png", MX, 1.35, CW, 4.7, "Mean ± SD spectra");
  caption(s, "Mean ± 1 SD per class. The two bands overlap almost everywhere: the class difference is small relative to the spread within each class.", MX, 6.2, CW, 0.6);
  notes(s, ["Class means with ±1 standard deviation. The healthy mean is slightly higher in the near-infrared plateau and the diseased mean slightly lower in parts of the visible and SWIR, but the shaded bands overlap almost completely.",
    "Interpretation: disease effects in these data are subtle relative to the natural variability among endmembers. Statistical tests with thousands of spectra can still detect such small differences (Tier 1), but classification of individual spectra will be difficult (Tier 4)."]);
}
{
  const s = slide("CONTENT", "Data check: everything is analysed");
  stat(s, MX, 1.45, 2.8, String(D.N), "spectra analysed: none removed");
  stat(s, MX + 3.0, 1.45, 2.8, String(D.P), "bands analysed: none removed");
  body(s, [
    `Reflectance < 0 (physically impossible) in ${D.neg.healthy} healthy and ${D.neg.diseased} diseased spectra, mostly at the SWIR-2 edge`,
    `Reflectance > 1 in ${D.neg.gt1_healthy} healthy and ${D.neg.gt1_diseased} diseased spectra (specular or saturated pixels)`,
    "Values are kept unchanged (reflectance only, no editing); the sensitivity analysis repeats everything without the bands ≥ 2350 nm, as Das et al. removed them",
    "Checked: 2158 × 483 values, no missing values, no duplicates, 98/30 endmembers per plot, plot 4 absent",
  ], 6.4, 1.4, 6.33, 2.9, 13);
  img(s, "f05_quality.png", MX, 4.35, CW, 2.5, "Out-of-range reflectance");
  notes(s, ["Before analysis the data were checked automatically (sheet 18_Cross_Checks) and by formulas in Excel (sheet 2_Data_Summary).",
    "Reflectance must lie between 0 and 1. Negative values occur mainly in the SWIR-2 region above ≈2000 nm, where the sensor signal is weak and atmospheric correction is uncertain; they are far more frequent in diseased spectra. A few spectra exceed 1 (specular reflection or saturation).",
    "Following the request to analyse reflectance values only, nothing was edited or removed. Instead, the sensitivity analysis (Step 14) repeats Tiers 1–4 without the bands ≥ 2350 nm, which Das et al. (2020) removed as noisy. If conclusions hold without these bands, the noisy edge is not driving them."]);
}

// ================================================================== B METHODS
newSection("B. Methods and why");
{ const s = slide("SECTION", "B · Methods and why they are used", "The four tiers, the validation schemes and the accuracy measures, each with its reference");
  notes(s, ["Part B explains each method before the results: what is done, why it is done, and which publication it comes from. All references were checked against the journal, publisher or repository record."]); }
{
  const s = slide("CONTENT", "Four-tier method: what each tier does and why");
  table(s, [
    ["Tier", "What is done here", "Why", "Reference"],
    ["1 · ANOVA", "One-way ANOVA per band, p < 0.05; Tukey HSD; FDR, Bonferroni, Welch, Levene, Cohen's d and plot-mean ANOVA as checks", "Keeps bands whose class means differ; removes uninformative bands before selection", "Das et al. 2020; Tukey 1949; Benjamini & Hochberg 1995; Welch 1947; Levene 1960; Cohen 1988; Hurlbert 1984"],
    ["2 · CART", "rpart-equivalent tree (Gini, minsplit 20, minbucket 7, maxdepth 30, cp 0.01) on the significant bands; bands used in splits are kept", "A small set of complementary bands; same tool and settings as the paper", "Breiman et al. 1984; Therneau & Atkinson (rpart)"],
    ["2 · RF", "Random Forest (500 trees, mtry = √p) importance ranking; top bands with |r| < 0.95; same number as CART", "Requested comparison: ensemble ranking, less dependent on one tree", "Breiman 2001; Strobl et al. 2008"],
    ["3 · J–M", "Jeffries–Matusita distance JM = 2(1 − e^−B) for each selected band and for the set; threshold 1.94", "How separable the classes are on the chosen bands (0 = none, 2 = complete)", "Bhattacharyya 1943; Richards 2013; Das et al. 2020"],
    ["4 · QDA", "Quadratic discriminant analysis on the selected bands; 10-fold CV as in the paper, plus plot-based validation", "The classifier of the paper; allows a different covariance matrix per class", "Das et al. 2020"],
  ], MX, 1.35, CW, [1.15, 4.4, 3.55, 3.03], { fontSize: 11.5, rowH: [0.4, 1.0, 0.8, 0.75, 0.75, 0.75] });
  caption(s, "Das et al. (2020) used 14 rice genotypes (91 pairs); here there are 2 classes (1 pair), so Tukey HSD gives exactly the ANOVA decision (checked at all 483 bands).", MX, 6.35, CW, 0.5);
  notes(s, [
    "Tier 1 – one-way ANOVA tests at each band H0: mean reflectance(healthy) = mean reflectance(diseased). Das et al. used p < 0.05 and then Tukey HSD for all genotype pairs. With two classes there is only one pair, so the Tukey decision equals the ANOVA decision. Extra checks are added because 483 tests are run (FDR and Bonferroni corrections), variances may differ (Welch and Levene tests), significance says nothing about size (Cohen's d), and spectra of a plot are not independent (ANOVA on plot means).",
    "Tier 2 – CART (classification and regression tree) recursively splits the spectra with the band and threshold that best separates the classes (Gini impurity), then prunes the tree with the complexity parameter cp = 0.01, exactly as R's rpart used by Das et al. The bands that appear in the pruned tree form the selected subset. As requested, Tier 2 is also run with Random Forest: 500 trees each grown on bootstrap samples and random subsets of bands; bands are ranked by their mean decrease in Gini impurity. Highly correlated neighbours (|r| ≥ 0.95) are skipped, because RF importance spreads over correlated bands (Strobl et al. 2008), and the same number of bands as CART is kept so the comparison is fair.",
    "Tier 3 – the J–M distance is based on the Bhattacharyya distance B, which uses both class means and class covariance matrices. JM = 2(1 − e^−B) ranges from 0 (identical distributions) to 2 (no overlap). Das et al. used 1.94 as the threshold for 'separable'.",
    "Tier 4 – QDA assigns each spectrum to the class with the highest posterior probability under a multivariate normal model with a separate covariance matrix for each class.",
  ]);
}
{
  const s = slide("CONTENT", "Class balance: spectra balanced, plots not");
  card(s, MX, 1.5, 5.9, 5.1, "What the design gives", [
    `${D.nH} healthy vs ${D.nD} diseased spectra: ratio 1 : 1.002 → no re-sampling or class weighting needed for training`,
    "11 healthy vs 36 diseased plots: each healthy plot weighs ≈ 3.3 diseased plots",
    "Overall accuracy (OA) is therefore reported together with balanced accuracy (BA), producer's and user's accuracy per class and MCC",
    "Class weights are used only in the block-vs-block negative control, where blocks have 98 vs 30 spectra per plot",
  ], HX.lt2, 14.5);
  card(s, 6.73, 1.5, 6.0, 5.1, "References", [
    "He & Garcia (2009): accuracy is misleading when classes are unequal",
    "Brodersen et al. (2010): balanced accuracy, 0.5 = chance",
    "Chicco & Jurman (2020): MCC for binary problems",
    "Breiman et al. (1984); Chen, Liaw & Breiman (2004): class weights / priors in CART and RF",
  ], "FDF3E7", 14.5);
  notes(s, ["In the previous data set the classes were imbalanced and re-sampling was needed. Here the extraction design (98 endmembers per healthy plot, 30 per diseased plot) makes the two classes almost equal at spectrum level, so classifiers are trained on the data as they are. This follows Das et al., who did not re-balance.",
    "At plot level there remain 11 healthy and 36 diseased plots. Plot-level results (majority vote of a plot's spectra) are therefore summarised with balanced accuracy, which averages the accuracy of the two classes and is not inflated by the larger class.",
    "In the negative-control analysis, block C (98 spectra per plot) is compared with single inoculated blocks (30 per plot); there, class weights make each class count equally."]);
}
{
  const s = slide("CONTENT", "Validation design (1/2): the paper's CV and plot-based CV");
  boxes(s, [
    ["CV1 · Das et al. (2020): QDA with 10-fold CV", "Exactly as in the paper: Tier-2 bands chosen on all spectra, then QDA cross-validated with 10 random folds of spectra (repeated 10× here; repetition 1 = the paper's single run). Reported as error matrix, OA, PA, UA. Optimistic: spectra of the same plot fall in training and test, and the bands were chosen with the test spectra."],
    ["CV2 · Plot-grouped nested 4-fold (× 10) — main result", "Whole plots are held out (≈3 healthy + 9 diseased per fold). Tier 1, Tier 2 and QDA are all refitted on the training plots only. Repeated 10 times with different plot splits."],
    ["CV3 · Leave-one-plot-out (47 folds)", "Each plot predicted by a model built on the other 46; a plot is called diseased if > 50% of its spectra are. Shows which plots fail."],
    ["Permutation test (100 ×)", "Plot labels shuffled (11 healthy / 36 diseased kept) and CV2 re-run: is the observed balanced accuracy better than chance?"],
  ], MX, 1.4, 2, 5.98, 2.45, 0.17, 0.17, 14.5, 12.5);
  caption(s, "References: Das et al. 2020 (CV1); Hurlbert 1984 (pseudo-replication); Roberts et al. 2017 (grouped CV); Ambroise & McLachlan 2002 (selection inside the folds); Ojala & Garriga 2010 (permutation test).", MX, 6.55, CW, 0.4);
  notes(s, ["CV1 reproduces the validation of the paper so the results can be compared directly with the 98% of Das et al. In the paper, field spectra of genotype plots were cross-validated in 10 folds using the CART bands; the same is done here.",
    "Two weaknesses of CV1 for these data: (1) random folds put endmembers of the same plot in both the training and the test set, so the model is tested on near-copies of training spectra; (2) the bands were selected using all spectra, including those later used for testing — selection bias (Ambroise & McLachlan 2002). Both make CV1 optimistic.",
    "CV2 removes both problems: entire plots are held out and every tier is refitted on the training plots only (nested validation). It is the honest estimate of how well a new plot would be classified, and is therefore the main result (Roberts et al. 2017).",
    "CV3 (leave-one-plot-out) gives a prediction for every plot, which can be mapped and checked in the field. The permutation test answers whether the CV2 accuracy could have arisen by chance: plot labels are shuffled 100 times and the whole pipeline re-run (Ojala & Garriga 2010)."]);
}
{
  const s = slide("CONTENT", "Validation design (2/2): using the treatment design");
  boxes(s, [
    ["CV4 · Leave-one-treatment-combination-out (12 folds)", "Hold out the plots sharing one variety × inoculation date (1 control + 3 inoculated; the V1×D3 fold has no control because plot 4 is missing). Tests transfer to unseen treatment combinations (Meyer et al. 2018)."],
    ["CV5 · Leave-one-variety-out (3 folds)", "Train on two varieties, test on the third. Disease detection should not depend on the variety."],
    ["CV6 · Leave-one-inoculation-date-out (4 folds)", "Train on three inoculation dates, test on the fourth."],
    ["Negative control: block vs block", "Classify two INOCULATED blocks (e.g. R3 vs R1). They cannot differ by disease, so their accuracy measures the block/location effect (Lipsitch et al. 2010)."],
    ["Restricted permutation (4 labellings)", "Treatments were applied to whole blocks, so blocks are the exchangeable units: each block in turn is called 'healthy' (Anderson & ter Braak 2003). Smallest possible p = 1/4."],
    ["Sensitivity: band removal of Das et al.", "Tiers 1–4 repeated without bands ≥ 2350 nm, which the paper removed as noisy; the other removed ranges are already absent from the image."],
  ], MX, 1.4, 2, 5.98, 1.62, 0.17, 0.12, 14.5, 12);
  caption(s, "All schemes are nested: Tier 1, Tier 2 and QDA are refitted without the test plots.", MX, 6.6, CW, 0.35);
  notes(s, ["These analyses use the treatment sheet. CV4–CV6 are leave-group-out validations: a whole treatment level is withheld from training, which is stricter than random plot splits because the model must generalise to a combination, variety or inoculation date it has never seen.",
    "The negative control and the restricted permutation address the main weakness of the design: all healthy plots are in block C. If two inoculated blocks — which received the same treatment — can be told apart about as well as control vs inoculated, the separation reflects location rather than disease.",
    "In the restricted permutation, the 'healthy' label is given in turn to each of the four blocks and the whole CV2 pipeline is re-run. With only four possible labellings the smallest attainable p-value is 0.25: this is a property of the design, not of the analysis.",
    "The sensitivity analysis follows the paper's band removal (1350–1430, 1800–1950 and 2350–2500 nm). The first two ranges are not in the image; removing bands ≥ 2350 nm tests whether the noisy detector edge drives the results."]);
}
{
  const s = slide("CONTENT", "Accuracy measures: how they are calculated");
  table(s, [
    ["Measure", "Formula (error matrix: rows = reference, columns = predicted)", "Why", "Reference"],
    ["Error (confusion) matrix", "Counts of reference × predicted classes", "Basis of all measures; reported by Das et al.", "Congalton 1991"],
    ["Overall accuracy (OA)", "(correct healthy + correct diseased) / all", "Measure used in the paper (98%)", "Congalton 1991; Das et al. 2020"],
    ["Producer's accuracy (PA)", "correct of a class / reference total of that class (= 1 − omission error)", "How well each class is found", "Story & Congalton 1986"],
    ["User's accuracy (UA)", "correct of a class / predicted total of that class (= 1 − commission error)", "How reliable a predicted label is", "Story & Congalton 1986"],
    ["Balanced accuracy (BA)", "(PA healthy + PA diseased) / 2; 0.5 = chance", "Not inflated by the larger class (plots 11 : 36)", "Brodersen et al. 2010"],
    ["Kappa", "(OA − chance agreement) / (1 − chance agreement)", "Common in remote sensing; its use is debated", "Cohen 1960; Pontius & Millones 2011"],
    ["F1, MCC", "F1 = 2·PA·UA/(PA+UA); MCC = correlation of reference and prediction", "Single-number summaries robust to class size", "Chicco & Jurman 2020"],
    ["Quantity / allocation disagreement", "Wrong class totals / wrong placement; sum = 1 − OA", "Explains where the error comes from", "Pontius & Millones 2011"],
    ["95% confidence interval", "Plots resampled with replacement within each class, 2000×", "Spectra of a plot are not independent", "Field & Welsh 2007; Olofsson et al. 2014"],
  ], MX, 1.3, CW, [2.45, 4.35, 3.35, 1.98], { fontSize: 10.5, rowH: 0.47 });
  notes(s, ["All accuracy measures are computed from the error matrix, exactly as in remote-sensing practice (Congalton 1991; Story & Congalton 1986). Das et al. reported the error matrix with overall, producer's and user's accuracy; these are given for every validation scheme, together with the additional measures in the table.",
    "Why so many measures: overall accuracy can look good if one class dominates; producer's accuracy shows how many diseased (or healthy) samples are found; user's accuracy shows how trustworthy a 'diseased' label is in a map; balanced accuracy averages the two producer's accuracies and is the main summary here.",
    "Confidence intervals: because spectra of the same plot are correlated, resampling individual spectra would give intervals that are too narrow. Instead whole plots are resampled (cluster bootstrap), separately within the healthy and diseased plots (11 and 36), 2000 times; the 2.5th and 97.5th percentiles form the 95% interval (Field & Welsh 2007; Olofsson et al. 2014).",
    "Every measure in the error-matrix blocks of the workbook (sheet 13_Accuracy) is recomputed by Excel formulas and matches Python to < 1e-9."]);
}

// ================================================================== C RESULTS
newSection("C. Results");
{ const s = slide("SECTION", "C · Results, tier by tier", "Tier 1 → Tier 2 (CART and RF) → Tier 3 → Tier 4 and validation");
  notes(s, ["Part C presents the results in the order of the method. For Tier 2 and Tier 3 both CART and Random Forest are shown side by side."]); }
{
  const s = slide("CONTENT", `Tier 1 · ${t1.sig} of ${D.P} bands differ at p < 0.05`);
  img(s, "f06_tier1.png", MX, 1.3, 7.6, 5.6, "Tier 1 ANOVA results");
  card(s, 8.4, 1.45, 4.33, 5.3, "What Tier 1 shows", [
    `${t1.sig} bands significant with spectra as replicates (${t1.fdr} after FDR, ${t1.bonf} after Bonferroni); Tukey HSD gives the same ${t1.sig}`,
    `Diseased lower at ${t1.lower_D} and higher at ${t1.higher_D} of the significant bands`,
    `Effects are small: largest |d| = ${f2(t1.dmax)} (${t1.wl_dmax.toFixed(0)} nm); ${t1.n_d_medium} bands reach |d| ≥ 0.5`,
    `With the 47 plot means as replicates only ${t1.plotmean} bands are significant: spectrum-level p-values are inflated by pseudo-replication`,
  ], HX.lt2, 13);
  notes(s, [`Top panel: class means; grey shading marks the ${D.P - t1.sig} bands that are not significant (p ≥ 0.05). Middle: −log10(p) for the test with spectra as replicates (blue) and with plot means as replicates (purple, dashed); the dotted line is p = 0.05. Bottom: Cohen's d, the mean difference in units of the pooled standard deviation (0.2 small, 0.5 medium, 0.8 large; Cohen 1988).`,
    `Following Das et al., the ${t1.sig} bands with p < 0.05 are passed to Tier 2. They lie mainly in ${Object.entries(t1.regions).filter(([k, v]) => v[1] > 0).map(([k, v]) => `${k} (${v[1]} of ${v[0]})`).join(", ")}.`,
    `Caution: with ${D.N} spectra even tiny differences become 'significant'. Effect sizes are small (max |d| = ${f2(t1.dmax)}). When each plot is reduced to its mean (n = 47), almost no band remains significant (${t1.plotmean}). The spectrum-level test treats correlated endmembers of one plot as independent and overstates the evidence (Hurlbert 1984). The band list is still used for Tier 2, as in the paper, but the validation must be done at plot level.`]);
}
{
  const s = slide("CONTENT", "Tier 1 · how robust is the band list?");
  table(s, [["Test", "Replicates", "Bands significant (of 483)", "Use"],
    ["One-way ANOVA, p < 0.05", `${D.N} spectra`, String(t1.sig), "Passed to Tier 2 (as in Das et al.)"],
    ["Tukey HSD, p < 0.05", `${D.N} spectra`, String(t1.sig), "Identical decision (one pair)"],
    ["ANOVA + FDR (Benjamini–Hochberg)", `${D.N} spectra`, String(t1.fdr), "Controls false discoveries over 483 tests"],
    ["ANOVA + Bonferroni", `${D.N} spectra`, String(t1.bonf), "Strictest control"],
    ["Welch test (unequal variances)", `${D.N} spectra`, String(t1.welch), `Levene: variances differ at ${t1.levene} bands`],
    ["ANOVA on plot means", "47 plots", String(t1.plotmean), "Pseudo-replication check (Hurlbert 1984)"]], MX, 1.45, CW, [3.6, 1.9, 2.6, 4.03], { fontSize: 13.5, rowH: 0.5 });
  table(s, [["Region", ...Object.keys(t1.regions)], ["Bands", ...Object.values(t1.regions).map((v) => v[0])], ["p < 0.05 (spectra)", ...Object.values(t1.regions).map((v) => v[1])], ["p < 0.05 (plot means)", ...Object.values(t1.regions).map((v) => v[2])]],
    MX, 5.15, CW, [2.6, 1.9, 1.9, 1.9, 1.9, 1.93], { fontSize: 12, rowH: 0.38 });
  notes(s, ["The table compares the paper's criterion with stricter alternatives. FDR keeps the expected share of false discoveries below 5% across the 483 tests (Benjamini & Hochberg 1995); Bonferroni controls the chance of even one false discovery. The Welch test does not assume equal variances; Levene's test shows that the variances do differ at many bands, which also justifies QDA (separate covariance per class) rather than LDA.",
    "The decisive line is the last one: when the 47 plots — the true experimental units — are the replicates, very few bands differ. The healthy–diseased difference is real at spectrum level but weak relative to the variation among plots.",
    "All these counts are recomputed live in sheet 4_Tier1_ANOVA (F, p, sums of squares, Cohen's d and single-band J–M are Excel formulas on the raw data)."]);
}
{
  const s = slide("CONTENT", "Tier 2 · the CART tree");
  img(s, "f07_tree.png", MX, 1.25, CW, 5.2, "CART tree");
  const r = F.CART.root;
  caption(s, `Tree grown on all ${D.N} spectra and pruned at cp = 0.01: ${F.CART.nodes} splits using ${F.CART.bands.length} bands; resubstitution accuracy ${pct(F.CART.train_acc)}. Boxes: split rule (R = reflectance at that wavelength, left = true); leaves: predicted class and healthy | diseased spectra. Root split R${r.band.toFixed(0)} ≤ ${r.thr.toFixed(4)}.`, MX, 6.5, CW, 0.5);
  notes(s, [`This is the Tier-2 CART model of Das et al. (rpart: Gini splitting, minimum 20 spectra to split, 7 per leaf, maximum depth 30, pruned with complexity parameter cp = 0.01). Each box is a rule 'reflectance at band ≤ threshold'; spectra satisfying it go left. Leaves show the predicted class and how many healthy | diseased spectra reach them.`,
    `The first (root) split uses ${r.band.toFixed(0)} nm with threshold ${r.thr.toFixed(4)}: the left branch holds ${r.left[0]} healthy and ${r.left[1]} diseased spectra. ${r.band > 2350 ? "This band lies in the noisy SWIR-2 edge where reflectance is near zero or negative, so the tree partly exploits sensor noise — one reason for the sensitivity analysis." : ""}`,
    `The ${F.CART.bands.length} bands used anywhere in the pruned tree are the selected wavebands passed to Tiers 3 and 4. The resubstitution accuracy (${pct(F.CART.train_acc)}) is measured on the training spectra themselves and is not a validation result.`]);
}
{
  const s = slide("CONTENT", "Tier 2 · bands selected by CART and by Random Forest");
  img(s, "f10_rf_importance.png", MX, 1.25, CW, 2.75, "RF importance");
  table(s, [["#", ...F.CART.bands.map((_, i) => String(i + 1))], ["CART (nm)", ...F.CART.bands.map((b) => b.toFixed(0))], ["RF (nm)", ...F.RF.bands.map((b) => b.toFixed(0))]],
    MX, 4.15, CW, [1.2, ...F.CART.bands.map(() => (CW - 1.2) / F.CART.bands.length)], { fontSize: 11, rowH: 0.42 });
  body(s, [`CART: bands in order of first use in the tree (root first); RF: highest importance first, neighbours with |r| ≥ 0.95 skipped, ${F.RF.bands.length} bands kept (= CART)`,
    `Shared regions: ${["VIS (< 700 nm)", "red-edge/NIR (700–1350)", "SWIR-1 (1350–1800)", "SWIR-2 (> 1800)"].filter((_, i) => [F.CART.bands, F.RF.bands].every((L) => L.some((b) => [b < 700, b >= 700 && b < 1350, b >= 1350 && b < 1800, b >= 1800][i]))).join(", ")}; edge bands (< 420 or > 2350 nm): CART ${nEdge("CART")}, RF ${nEdge("RF")}`],
    MX, 5.55, CW, 1.3, 13.5);
  notes(s, ["Top: Random Forest importance (mean decrease in Gini impurity) of every ANOVA-significant band, with the kept bands marked. RF importance forms broad peaks because neighbouring bands are highly correlated; the |r| < 0.95 filter keeps one band per peak (Strobl et al. 2008).",
    "Table: the bands selected on all spectra by each method. CART bands are listed in order of first use in the tree (the root split first); RF bands in order of importance. The number of RF bands was set equal to the number of CART bands, so Tier 3 and Tier 4 compare equally sized band sets.",
    "Both methods pick bands from several spectral regions, but the exact wavelengths differ. Inside the validation folds the selected bands also change from fold to fold (see 'Are the same bands chosen in every fold?'), so individual wavelengths should not be over-interpreted."]);
}
{
  const s = slide("CONTENT", "Tier 3 · J–M distance of each band selected in Tier 2");
  const n = Math.max(F.CART.bands.length, F.RF.bands.length);
  const rows = [["#", "CART band (nm)", "J–M of this band", "J–M of first k bands", "RF band (nm)", "J–M of this band", "J–M of first k bands"]];
  for (let i = 0; i < n; i++) rows.push([String(i + 1), F.CART.bands[i] ? F.CART.bands[i].toFixed(1) : "", F.CART.bands[i] ? f2(F.CART.jm_single[i], 4) : "", F.CART.bands[i] ? f2(F.CART.cum[i], 3) : "",
    F.RF.bands[i] ? F.RF.bands[i].toFixed(1) : "", F.RF.bands[i] ? f2(F.RF.jm_single[i], 4) : "", F.RF.bands[i] ? f2(F.RF.cum[i], 3) : ""]);
  rows.push([{ text: "Set", options: { bold: true } }, "", { text: `max ${f2(Math.max(...F.CART.jm_single), 4)}`, options: { bold: true } }, { text: f2(F.CART.JM, 3), options: { bold: true } }, "",
    { text: `max ${f2(Math.max(...F.RF.jm_single), 4)}`, options: { bold: true } }, { text: f2(F.RF.JM, 3), options: { bold: true } }]);
  table(s, rows, MX, 1.3, 8.2, [0.45, 1.25, 1.3, 1.35, 1.25, 1.3, 1.3], { fontSize: 10.5, rowH: 0.33, margin: [1, 4, 1, 4] });
  card(s, 9.0, 1.3, 3.73, 5.4, "Reading the table", [
    `Every single band has J–M ≤ ${f2(Math.max(...F.CART.jm_single, ...F.RF.jm_single), 3)} on the 0–2 scale: alone, no band separates the classes`,
    `All ${F.CART.bands.length} bands together: CART ${f2(F.CART.JM, 3)}, RF ${f2(F.RF.JM, 3)}`,
    "Threshold of Das et al.: 1.94 — not reached",
    `Best band anywhere in the spectrum: ${f2(D.jm_band_max, 3)} at ${D.wl_jm_max.toFixed(0)} nm`,
  ], HX.lt2, 13);
  notes(s, ["This table gives the Jeffries–Matusita distance of every individual band selected in Tier 2, for CART and for Random Forest, plus the cumulative J–M of the first k bands and of the whole set (last row).",
    "Single-band J–M: JM = 2(1 − e^−B), with the one-dimensional Bhattacharyya distance B = (μD − μH)² / (4(σH² + σD²)) + ½ ln((σH² + σD²) / (2σHσD)). It uses the class means and variances of that one band. The same value is computed by an Excel formula for all 483 bands in sheet 4_Tier1_ANOVA (column R) and linked into sheets 5–7.",
    `Interpretation: on the 0–2 scale, individual bands reach at most ${f2(Math.max(...F.CART.jm_single, ...F.RF.jm_single), 3)}. Combining bands raises the distance (multivariate J–M uses the covariance between bands), but even the full set stays far below the 1.94 threshold that Das et al. used for 'separable'. Healthy and diseased endmembers overlap strongly.`,
    "For CART the cumulative column follows the order of first use in the tree; for RF the order of importance."]);
}
{
  const s = slide("CONTENT", "Tier 3 · separability on the spectrum and with more bands");
  img(s, "f08_bands_jm.png", MX, 1.3, 7.3, 3.1, "Single-band JM with selected bands");
  img(s, "f09_jm_cumulative.png", MX, 4.45, 7.3, 2.45, "Cumulative JM");
  card(s, 8.1, 1.3, 4.63, 5.5, "What the figures show", [
    "Top: J–M of every single band (grey) with the CART and RF bands marked; the highest values are in the SWIR",
    `Bottom: J–M grows as bands are added but levels off near ${f2(Math.max(F.CART.JM, F.RF.JM), 2)}, far below 1.94`,
    `CART bands reach a ${F.CART.JM >= F.RF.JM ? "higher" : "lower"} set J–M than RF bands (${f2(F.CART.JM, 3)} vs ${f2(F.RF.JM, 3)})`,
    "Conclusion of Tier 3: the classes are statistically different but not separable in the sense of Das et al.",
  ], HX.lt2, 13.5);
  notes(s, ["Top figure: the grey line is the J–M distance of each band on its own; markers show where the CART (orange) and RF (blue) bands lie on this curve. Both methods choose some bands with relatively high single-band J–M, but also bands with low individual J–M that add information in combination with others.",
    "Bottom figure: J–M of the first k selected bands. Adding bands helps at first and then flattens out. The dashed line is the 1.94 threshold of Das et al.; neither set comes close. In the paper all genotype pairs exceeded 1.94 with 17 CART bands, which explains their 98% accuracy; here the much lower J–M predicts modest accuracy, which Tier 4 confirms."]);
}
{
  const s = slide("CONTENT", "Tier 4 · QDA validated as in Das et al. (CV1)");
  errMatrix(s, MX, 1.35, CV.CART.CV1.rep1, `CART bands + QDA (repetition 1)`);
  errMatrix(s, MX + 6.13, 1.35, CV.RF.CV1.rep1, `RF bands + QDA (repetition 1)`);
  table(s, [["10-fold CV, mean of 10 repetitions", "OA", "BA", "Kappa", "AUC"],
    ...T2.map((t) => [`${t} + QDA`, pm(CV[t].CV1.OA, 3), pm(CV[t].CV1.BA, 3), pm(CV[t].CV1.kappa, 3), pm(CV[t].CV1.AUC, 3)])], MX, 4.3, CW, [3.3, 2.2, 2.2, 2.2, 2.23], { fontSize: 12.5, rowH: 0.4 });
  caption(s, "Bands chosen on all spectra, QDA with 10 random folds of spectra, as in Das et al. (2020: OA 98% for 14 genotypes). Optimistic for these data: endmembers of one plot fall in training and test, and the bands were chosen using the test spectra.", MX, 5.75, CW, 0.7);
  notes(s, ["This slide reproduces Tier 4 of the paper. The error matrix of the first repetition corresponds to the single run reported by Das et al.; the table shows the mean ± SD over 10 repetitions with different random folds.",
    `Result: overall accuracy ${pct(CV.CART.CV1.OA[0])} with the CART bands and ${pct(CV.RF.CV1.OA[0])} with the RF bands, compared with 98% in the paper. Producer's accuracy shows how many healthy and diseased spectra are found; user's accuracy how often a predicted label is correct.`,
    "Why this is not the final answer: in random 10-fold CV the training set always contains endmembers from the same plots as the test endmembers, and the CART/RF bands were chosen with all spectra. Both inflate accuracy. The following slides therefore validate with whole plots held out (CV2–CV6)."]);
}
{
  const s = slide("CONTENT", "Main result · balanced accuracy under every validation scheme");
  const labels = KEYS.map((k) => `${k}`);
  s.addChart(pres.charts.BAR, [
    { name: "CART + QDA", labels, values: KEYS.map((k) => +CV.CART[k].acc.spectra.BA.toFixed(3)) },
    { name: "RF + QDA", labels, values: KEYS.map((k) => +CV.RF[k].acc.spectra.BA.toFixed(3)) },
  ], { x: MX, y: 1.3, w: 7.9, h: 5.4, barDir: "col", barGrouping: "clustered", chartColors: [HX.accent2, HX.accent3], valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.25,
       valAxisLabelFormatCode: "0.00", valAxisTitle: "Balanced accuracy (spectra)", showValAxisTitle: true, valAxisTitleFontSize: 11, catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
       showLegend: true, legendPos: "b", legendFontSize: 11, showValue: true, dataLabelFontSize: 9, dataLabelFormatCode: "0.00", valGridLine: { color: "E4E3DF", size: 0.5 }, catGridLine: { style: "none" }, objectName: "BA chart" });
  card(s, 8.75, 1.3, 3.98, 5.4, "Reading the chart", [
    "0.5 = chance; 1.0 = perfect",
    `CV1 (paper's method): ${f2(CV.CART.CV1.acc.spectra.BA)} / ${f2(CV.RF.CV1.acc.spectra.BA)}`,
    `Plot-based schemes CV2–CV6: ${f2(Math.min(...realBA))}–${f2(Math.max(...realBA))}`,
    `CV2 (main): CART ${f2(CV.CART.CV2.acc.spectra.BA, 3)}, RF ${f2(CV.RF.CV2.acc.spectra.BA, 3)}`,
    "CART and RF differ by only a few points under every scheme",
  ], HX.lt2, 13);
  notes(s, ["Each bar is the balanced accuracy of all spectrum predictions of one scheme (for CV1 and CV2 pooled over 10 repetitions). CV1 = validation of Das et al.; CV2 = plot-grouped nested CV (main); CV3 = leave-one-plot-out; CV4 = leave-one-treatment-combination-out; CV5 = leave-one-variety-out; CV6 = leave-one-inoculation-date-out.",
    `Key message: under every scheme the accuracy is clearly above chance but moderate (about ${f2(Math.min(...realBA), 2)}–${f2(Math.max(...realBA), 2)} with whole plots held out). The difference between CV1 and CV2 is the optimism of random spectrum-level cross-validation for these data.`,
    "CART and Random Forest in Tier 2 lead to very similar QDA accuracy; neither band-selection method is clearly better here."]);
}
{
  const s = slide("CONTENT", "Accuracy assessment · error matrices of the main validation (CV2)");
  errMatrix(s, MX, 1.3, CV.CART.CV2.acc.spectra, `CART + QDA (${CV.CART.CV2.acc.spectra.n} predictions)`);
  errMatrix(s, MX + 6.13, 1.3, CV.RF.CV2.acc.spectra, `RF + QDA (${CV.RF.CV2.acc.spectra.n} predictions)`);
  const rows = [["Measure (95% CI by plot bootstrap)", "CART + QDA", "RF + QDA"]];
  const A = (t) => CV[t].CV2.acc.spectra;
  rows.push(["Overall accuracy", ...T2.map((t) => `${pct(A(t).OA)} (${ci(A(t).ci.OA)}%)`)]);
  rows.push(["Balanced accuracy", ...T2.map((t) => `${pct(A(t).BA)} (${ci(A(t).ci.BA)}%)`)]);
  rows.push(["Kappa", ...T2.map((t) => `${f2(A(t).kappa, 3)} (${ci(A(t).ci.kappa, 3, 1)})`)]);
  rows.push(["PA healthy / PA diseased", ...T2.map((t) => `${pct(A(t).PA_H)} / ${pct(A(t).PA_D)}`)]);
  rows.push(["UA healthy / UA diseased", ...T2.map((t) => `${pct(A(t).UA_H)} / ${pct(A(t).UA_D)}`)]);
  rows.push(["MCC · F1 healthy · F1 diseased", ...T2.map((t) => `${f2(A(t).MCC, 3)} · ${f2(A(t).F1_H, 2)} · ${f2(A(t).F1_D, 2)}`)]);
  rows.push(["Quantity / allocation disagreement", ...T2.map((t) => `${pct(A(t).QD)} / ${pct(A(t).AD)}`)]);
  table(s, rows, MX, 3.75, CW, [4.13, 4.0, 4.0], { fontSize: 11.5, rowH: 0.34 });
  notes(s, ["Error matrices of the main validation (CV2), summed over 10 repetitions: every spectrum is predicted 10 times, always by a model trained without its plot. Rows are the true classes, columns the predictions.",
    "Producer's accuracy (PA) of diseased = share of diseased spectra recognised as diseased (sensitivity); PA of healthy = share of healthy spectra recognised as healthy (specificity). User's accuracy (UA) = share of predicted labels that are correct.",
    "Confidence intervals come from resampling whole plots (cluster bootstrap), so they reflect the plot-to-plot variability, which is the relevant uncertainty for new plots.",
    "Quantity disagreement shows whether one class is predicted too often; allocation disagreement shows errors that cancel in the totals. Their sum equals 1 − OA (Pontius & Millones 2011). All values are recomputed by Excel formulas in sheet 13_Accuracy.",
    `Why healthy is found far more often than diseased (PA ${pct(CV.CART.CV2.acc.spectra.PA_H, 0)} vs ${pct(CV.CART.CV2.acc.spectra.PA_D, 0)}): the two class means are almost equal, but diseased endmembers are more variable (mean SD ${f2(D.disp.sd_D, 3)} vs ${f2(D.disp.sd_H, 3)}; log-determinant of the covariance on the CART bands ${f2(D.disp.logdet.CART[1], 1)} vs ${f2(D.disp.logdet.CART[0], 1)}). QDA then assigns spectra near the common mean to the tighter (healthy) class and calls a spectrum diseased only when it lies in the wider tails of the diseased distribution. The large quantity disagreement reflects this: too many spectra are labelled healthy. Disease therefore appears mainly as increased spectral variability rather than as a shift of the mean.`]);
}
{
  const s = slide("CONTENT", "Accuracy of every validation scheme (spectrum level)");
  const rows = [["Tier 2", "Validation", "OA", "BA (95% CI)", "Kappa", "PA H", "UA H", "PA D", "UA D", "MCC", "QD / AD"]];
  for (const t of T2) for (const k of KEYS) {
    const a = CV[t][k].acc.spectra;
    rows.push([k === "CV1" ? { text: t, options: { bold: true } } : "", `${k} ${KN[k]}`, pct(a.OA), a.ci ? `${pct(a.BA)} (${ci(a.ci.BA, 0)}%)` : `${pct(a.BA)}`, f2(a.kappa, 2), pct(a.PA_H, 0), pct(a.UA_H, 0), pct(a.PA_D, 0), pct(a.UA_D, 0), f2(a.MCC, 2), `${pct(a.QD, 0)} / ${pct(a.AD, 0)}`]);
  }
  table(s, rows, MX, 1.3, CW, [0.75, 2.95, 0.85, 1.65, 0.8, 0.8, 0.8, 0.8, 0.8, 0.75, 1.18], { fontSize: 10, rowH: 0.36 });
  caption(s, "H = healthy, D = diseased. CV1 has no CI because its folds split the spectra of each plot between training and test. Plot-level matrices: sheet 13_Accuracy and slide on leave-one-plot-out.", MX, 6.15, CW, 0.5);
  notes(s, ["This table brings together the full accuracy assessment for both Tier-2 methods and all six validation schemes. It is the complete version of the bar chart.",
    "Points to note: (1) accuracy under CV1 (the paper's method) is higher than under the plot-based schemes; (2) the plot-based schemes agree with each other, so the estimate is stable; (3) look at PA and UA of each class to see whether errors are balanced or one class is systematically missed."]);
}
{
  const s = slide("CONTENT", "Are the same bands chosen in every training fold?");
  const sc = CV.CART.CV2.stable, sr = CV.RF.CV2.stable;
  table(s, [["CART band (nm)", "Share of 40 folds", "RF band (nm)", "Share of 40 folds"], ...sc.map((b, i) => [f2(b[0], 1), pct(b[1], 0), sr[i] ? f2(sr[i][0], 1) : "", sr[i] ? pct(sr[i][1], 0) : ""])],
    MX, 1.4, 7.2, [1.8, 1.8, 1.8, 1.8], { fontSize: 13, rowH: 0.42 });
  card(s, 8.1, 1.4, 4.63, 5.0, "Stability of band selection", [
    "In CV2, Tier 1 and Tier 2 are repeated in each of the 40 training folds (4 folds × 10 repetitions)",
    `Bands per fold: CART ${f2(CV.CART.CV2.kfold, 1)}, RF ${f2(CV.RF.CV2.kfold, 1)} on average`,
    "Even the most frequent bands are chosen in only part of the folds: the band set depends on which plots are in the training set",
    "Report spectral regions rather than single wavelengths",
  ], HX.lt2, 13.5);
  notes(s, ["Because band selection is part of the model, it is repeated inside every training fold (nested validation). This table counts how often each wavelength was selected over the 40 training folds of CV2.",
    "A band chosen in 100% of the folds would be a robust marker. Here selection varies considerably, which is expected when classes overlap strongly: many bands carry similar weak information, and small changes in the training plots change which one wins. Interpretation should therefore focus on regions (e.g. visible, red-edge, SWIR) rather than on exact wavelengths."]);
}
{
  const s = slide("CONTENT", "Leave-one-plot-out (CV3): which plots are misclassified?");
  img(s, "f11_lopo_CART.png", MX, 1.25, 4.6, 4.2, "LOPO CART map");
  img(s, "f11_lopo_RF.png", 5.3, 1.25, 4.6, 4.2, "LOPO RF map");
  card(s, 10.1, 1.3, 2.63, 4.15, "Plot level", T2.map((t) => `${t}: ${CV[t].CV3.correct}/47 plots correct, plot BA ${f2(CV[t].CV3.acc.plots.BA, 2)}`), HX.lt2, 12.5);
  table(s, [["Tier 2", "Spectrum BA", "Plot BA", "Healthy plots wrong", "Diseased plots wrong"],
    ...T2.map((t) => [t, f2(CV[t].CV3.acc.spectra.BA, 3), f2(CV[t].CV3.acc.plots.BA, 3), CV[t].CV3.wrongH.join(", ") || "none", CV[t].CV3.wrongD.length > 10 ? `${CV[t].CV3.wrongD.length} plots` : (CV[t].CV3.wrongD.join(", ") || "none")])],
    MX, 5.55, CW, [1.4, 1.6, 1.4, 3.6, 4.13], { fontSize: 11.5, rowH: 0.38 });
  notes(s, ["Each plot was predicted by a model built from the other 46 plots (all tiers refitted). The colour shows the share of the plot's endmembers predicted diseased; a plot is called diseased if more than 50% are. Black outlines mark plots whose majority call is wrong.",
    "The maps show whether errors are spatially clustered. Errors concentrated in one part of the field would point to a location effect rather than to disease."]);
}
{
  const s = slide("CONTENT", "Validation using the treatment design (CV4–CV6)");
  const rows = [["Tier 2", "Scheme", "BA (95% CI)", "OA", "Kappa", "Plot BA", "Plots correct"]];
  for (const t of T2) for (const k of ["CV2", "CV4", "CV5", "CV6"]) {
    const a = CV[t][k].acc;
    rows.push([k === "CV2" ? { text: t, options: { bold: true } } : "", `${k} ${KN[k]}`, `${f2(a.spectra.BA, 3)} (${ci(a.spectra.ci.BA, 0)}%)`, pct(a.spectra.OA), f2(a.spectra.kappa, 2), f2(a.plots.BA, 2), k === "CV2" ? "—" : `${CV[t][k].correct}/47`]);
  }
  table(s, rows, MX, 1.35, 8.5, [0.8, 2.6, 1.7, 0.8, 0.8, 0.85, 0.95], { fontSize: 11, rowH: 0.42 });
  card(s, 9.3, 1.35, 3.43, 5.3, "What it shows", [
    `Holding out a whole variety, inoculation date or treatment combination gives BA ${f2(Math.min(...designBA), 2)}–${f2(Math.max(...designBA), 2)}, close to CV2`,
    "The weak discrimination is not tied to one variety or date: the model transfers, but stays weak",
    "The CV4 fold V1×D3 contains no control plot (plot 4 missing); pooled predictions are still valid",
  ], HX.lt2, 12.5);
  notes(s, ["CV4–CV6 withhold an entire treatment level from training (Meyer et al. 2018 call this target-oriented validation). If the model relied on something specific to one variety or one inoculation date, accuracy would drop for that level.",
    "Accuracy stays at the same level as CV2, so the result is consistent across varieties and inoculation dates. Per-fold accuracies are listed in sheet 11_CV4-6_Design.",
    "These schemes keep the spatial layout intact (block C is always west of the inoculated blocks), so they cannot remove the block/location confound — that is the purpose of the next two slides."]);
}
{
  const s = slide("CONTENT", "Permutation test: better than chance?");
  img(s, "f12_permutation.png", MX, 1.3, 7.3, 3.6, "Permutation null distributions");
  table(s, [["Tier 2", "Observed BA", "Null mean", "Null 95%", "Null max", "p"], ...T2.map((t) => { const p = D.perm[t]; return [t, f2(p.observed, 3), f2(p.null_mean, 3), f2(p.q95, 3), f2(p.null_max, 3), f2(p.p, 3)]; })],
    8.1, 1.4, 4.63, [0.8, 0.85, 0.75, 0.75, 0.75, 0.73], { fontSize: 11, rowH: 0.45 });
  body(s, [`Plot labels shuffled ${D.perm.CART.n} times (11 healthy / 36 diseased kept) and the CV2 pipeline (one repetition) re-run each time`,
    `Shuffled labels give BA ≈ ${f2(D.perm.CART.null_mean, 2)}; the true labels give ${f2(D.perm.CART.observed, 3)} (CART) and ${f2(D.perm.RF.observed, 3)} (RF): p = ${f2(D.perm.CART.p, 3)} and ${f2(D.perm.RF.p, 3)} (smallest possible ${f2(1 / (D.perm.CART.n + 1), 3)})`,
    "Because whole plots are permuted, this tests the plot-level class difference (Ojala & Garriga 2010) — but not whether that difference is disease or location (next slides)"], MX, 5.05, CW, 1.8, 13.5);
  notes(s, ["The permutation test asks: if the healthy/diseased labels were assigned to plots at random, how high would the accuracy be? The labels of whole plots are shuffled (keeping 11 healthy and 36 diseased), and the full nested pipeline is re-run each time. The grey histogram is this null distribution; the orange line is the accuracy with the true labels.",
    `The true accuracy exceeds ${Math.round((1 - D.perm.CART.p) * (D.perm.CART.n + 1)) - 1} of ${D.perm.CART.n} shuffled accuracies for CART (p = ${f2(D.perm.CART.p, 3)}) and ${Math.round((1 - D.perm.RF.p) * (D.perm.RF.n + 1)) - 1} of ${D.perm.RF.n} for RF (p = ${f2(D.perm.RF.p, 3)}), so the plots labelled healthy and diseased differ spectrally beyond chance at the 5% level.`,
    "Limitation: plots of block C share a location. A plot-label permutation cannot distinguish disease from location; the block-level analyses that follow address this."]);
}
{
  const s = slide("CONTENT", "Negative control: block vs block");
  img(s, "f14_negative_control.png", MX, 1.25, CW, 3.95, "Negative control");
  body(s, [
    `Control vs inoculated: mean BA ${f2(ncMean(ncCtrl, "CART"), 2)} (CART) / ${f2(ncMean(ncCtrl, "RF"), 2)} (RF); inoculated vs inoculated: ${f2(ncMean(ncNeg, "CART"), 2)} / ${f2(ncMean(ncNeg, "RF"), 2)}`,
    `Same distance (≈ 27 m): C vs R2 ${f2(nc("C vs R2").CART.BA[0], 2)} / ${f2(nc("C vs R2").RF.BA[0], 2)} against R3 vs R1 ${f2(nc("R3 vs R1").CART.BA[0], 2)} / ${f2(nc("R3 vs R1").RF.BA[0], 2)}`,
    `But inoculated blocks also differ in Tier 1 (R3 vs R1: ${nc("R3 vs R1").sig} bands; plot means ${nc("R3 vs R1").sig_plot}), and C vs R accuracy rises with distance (C vs R3 ${f2(nc("C vs R3").CART.BA[0], 2)} → C vs R1 ${f2(nc("C vs R1").CART.BA[0], 2)})`,
  ], MX, 5.3, CW, 1.6, 12.5);
  notes(s, ["A negative control is a comparison where the effect of interest cannot exist (Lipsitch et al. 2010). Two inoculated blocks received the same treatment, so any accuracy above 0.5 between them reflects block or location differences, not disease.",
    "Orange bars: the control block against each inoculated block; grey bars: inoculated blocks against each other. Same pipeline, plot-grouped CV with 5 repetitions, class weights because block C has 98 endmembers per plot versus 30.",
    "If the grey bars were as high as the orange ones, the healthy–diseased separation could be entirely location. Higher orange bars, especially at equal distance (C vs R2 against R3 vs R1, both ≈ 27 m apart), indicate a difference specific to the control block — consistent with a disease effect, though a difference unique to block C (e.g. its management or position) cannot be excluded."]);
}
{
  const s = slide("CONTENT", "Detection by block, variety and inoculation date");
  img(s, "f15_detection_block.png", MX, 1.25, 8.3, 3.2, "Detection by block");
  const rp = (t) => ["C", "R3", "R2", "R1"].map((b) => f2(D.rp[t].ba[b], 3));
  table(s, [["Block called healthy", "C (true)", "R3", "R2", "R1", "p"], ...T2.map((t) => [t, ...rp(t), f2(D.rp[t].p, 2)])], 9.1, 1.35, 3.63, [1.0, 0.6, 0.5, 0.5, 0.5, 0.53], { fontSize: 10, rowH: 0.42 });
  caption(s, "Restricted permutation: CV2 balanced accuracy (class weights, 5 reps) when each block in turn is called healthy; smallest possible p = 0.25.", 9.1, 2.75, 3.63, 0.9);
  const kw = (t, k) => f2(D.det[t].kw[k][1], 2);
  body(s, [
    `Share of spectra predicted diseased by block (CART, CV2): C ${pct(D.det.CART.by_block.C, 0)}, R3 ${pct(D.det.CART.by_block.R3, 0)}, R2 ${pct(D.det.CART.by_block.R2, 0)}, R1 ${pct(D.det.CART.by_block.R1, 0)} (RF ${pct(D.det.RF.by_block.C, 0)} → ${pct(D.det.RF.by_block.R1, 0)})`,
    `Among inoculated plots detection does not differ by inoculation date (Kruskal–Wallis p = ${kw("CART", "date|diseased")} CART, ${kw("RF", "date|diseased")} RF) or variety (p = ${kw("CART", "variety|diseased")}, ${kw("RF", "variety|diseased")}); between inoculated blocks p = ${f2(D.det.CART.kw_block[1], 2)} / ${f2(D.det.RF.kw_block[1], 2)}`,
    `The true labelling ranks ${D.rp.CART.rank === 1 ? "first" : D.rp.CART.rank} of 4 (CART) and ${D.rp.RF.rank === 1 ? "first" : D.rp.RF.rank} of 4 (RF), p = ${f2(D.rp.CART.p, 2)} / ${f2(D.rp.RF.p, 2)}: with one control block, disease and block cannot be separated statistically`,
  ], MX, 4.6, CW, 2.25, 12.5);
  notes(s, ["Box plots: for each plot, the share of its endmembers predicted diseased in CV2, grouped by block from west to east. A clear increase from R3 to R1 would mean the classifier responds to position along the field as well as to treatment.",
    "Kruskal–Wallis tests (Kruskal & Wallis 1952) compare these shares among inoculation dates and varieties within the diseased plots. If disease severity increased with earlier inoculation, a difference among dates would be expected; none is found.",
    "Restricted permutation: since the treatment was applied block-wise, the honest permutation exchanges whole blocks. There are only four ways to choose the 'healthy' block, so the p-value cannot be smaller than 0.25 even if the true labelling gives the best accuracy. This is a limit of the field design, not of the analysis; it can only be removed by replicating control plots in every block in future trials."]);
}
{
  const s = slide("CONTENT", "Sensitivity analysis: band removal of Das et al.");
  const S_ = D.sens;
  table(s, [["Tier 2", "Bands", "Selected bands", "J–M set", "CV1 OA", "CV2 BA", "CV2 plot BA"],
    ...T2.flatMap((t) => [[{ text: `${t}, all ${D.P} bands`, options: { bold: true } }, D.P, F[t].bands.length, f2(F[t].JM, 3), pct(CV[t].CV1.OA[0]), pct(CV[t].CV2.BA[0]), pct(CV[t].CV2.plotBA[0])],
      [`${t}, bands < 2350 nm`, S_.bands_used, S_[t].bands.length, f2(S_[t].JM, 3), pct(S_[t].CV1_OA), pct(S_[t].CV2_BA[0]), pct(S_[t].CV2_plotBA)]])], MX, 1.4, CW, [2.9, 1.0, 1.6, 1.4, 1.6, 1.6, 2.03], { fontSize: 12.5, rowH: 0.45 });
  body(s, [
    `Das et al. removed 1350–1430, 1800–1950 and 2350–2500 nm; the first two ranges are not in the image, so ${D.P - S_.bands_used} bands ≥ 2350 nm were removed and all tiers repeated`,
    `Without them the set J–M changes to ${f2(S_.CART.JM, 3)} (CART) and ${f2(S_.RF.JM, 3)} (RF); plot-grouped BA becomes ${f2(S_.CART.CV2_BA[0], 3)} and ${f2(S_.RF.CV2_BA[0], 3)}`,
    `CART bands without the edge: ${S_.CART.bands.map((b) => b.toFixed(0)).join(", ")} nm`,
  ], MX, 4.35, CW, 2.4, 14);
  notes(s, ["The sensitivity analysis applies the band removal used by Das et al. The noisy edge above 2350 nm contains most of the negative reflectance values and was used by CART for its first split. Repeating the whole analysis without it tests whether the results depend on sensor noise.",
    "Read the table by comparing each pair of rows: if accuracy stays similar without the edge bands, the conclusions do not depend on them; a clear drop would mean the noisy region was carrying part of the separation."]);
}
{
  const s = slide("CONTENT", "Comparison: CART vs Random Forest in Tier 2");
  const rows = [["Measure", "CART", "RF"]];
  rows.push(["Bands selected", F.CART.bands.length, F.RF.bands.length]);
  rows.push(["J–M of the set (Tier 3)", f2(F.CART.JM, 3), f2(F.RF.JM, 3)]);
  rows.push(["Largest single-band J–M", f2(Math.max(...F.CART.jm_single), 3), f2(Math.max(...F.RF.jm_single), 3)]);
  for (const k of KEYS) rows.push([`${k} BA — ${KN[k]}`, f2(CV.CART[k].acc.spectra.BA, 3), f2(CV.RF[k].acc.spectra.BA, 3)]);
  rows.push(["CV1 overall accuracy (paper's measure)", pct(CV.CART.CV1.OA[0]), pct(CV.RF.CV1.OA[0])]);
  rows.push(["CV2 plot-level BA", f2(CV.CART.CV2.acc.plots.BA, 3), f2(CV.RF.CV2.acc.plots.BA, 3)]);
  rows.push(["Permutation p / block permutation p", `${f2(D.perm.CART.p, 3)} / ${f2(D.rp.CART.p, 2)}`, `${f2(D.perm.RF.p, 3)} / ${f2(D.rp.RF.p, 2)}`]);
  table(s, rows, MX, 1.3, 7.9, [4.5, 1.7, 1.7], { fontSize: 11.5, rowH: 0.37 });
  const wins = KEYS.filter((k) => best(k) === "CART").length;
  card(s, 8.8, 1.3, 3.93, 5.4, "What the comparison shows", [
    `CART gives ${F.CART.JM >= F.RF.JM ? "the higher" : "a lower"} set J–M; RF ranks bands with less dependence on a single tree`,
    `Balanced accuracy is higher with CART in ${wins} of 6 schemes and with RF in ${6 - wins}; differences are small compared with the CIs`,
    "Both reach the same conclusion: statistically different but weakly separable classes",
    "Choice of Tier-2 method matters less than the validation scheme",
  ], HX.lt2, 13);
  notes(s, ["This slide answers the comparison asked for: CART (as in Das et al.) versus Random Forest in Tier 2, with all other tiers identical.",
    "The two methods select different wavelengths but lead to similar separability and similar QDA accuracy under every validation scheme. The width of the confidence intervals (about ±3–5 percentage points) is larger than most CART–RF differences, so neither method is clearly superior for these data.",
    "Practical recommendation: keep CART for comparability with the paper, report RF as a robustness check, and interpret spectral regions rather than individual bands."]);
}
{
  const s = slide("CONTENT", "Every step was cross-checked");
  const groups = {}; for (const r of D.checks.rows) (groups[r[0]] = groups[r[0]] || []).push(r);
  const ex = { Data: "2158 × 483; 98/30 endmembers per plot; plot 4 absent; no missing or duplicate spectra", Design: "47 ROIs; block C = healthy plots; R1–R3 = diseased plots",
    "Tier 1": "manual F = scipy; Tukey = ANOVA decision at all bands", "Tier 2": "bands ⊂ significant set; RF = CART band count; custom pruned tree = sklearn",
    "Tier 3": "1-D closed-form J–M = matrix form; cumulative = set J–M", Validation: "no plot in training and test; every spectrum tested once; permutation nulls ≈ 0.5",
    "Tier 4": "hand-coded QDA = sklearn; BA = (sens + spec)/2", Accuracy: "matrix totals; OA = 1 − QD − AD; kappa = sklearn; OA = accuracy" };
  const rows = [["Step", "Checks", "What was checked", "Result"]];
  for (const [k, v] of Object.entries(groups)) rows.push([k, v.length, ex[k] || "", { text: v.every((c) => c[3] === "PASS") ? "PASS" : "FAIL", options: { bold: true, color: v.every((c) => c[3] === "PASS") ? "008000" : "C00000" } }]);
  rows.push(["Excel ↔ Python", "live", "ANOVA F and p, single-band and set J–M, error-matrix accuracies, LOPO plot BA, permutation p recomputed by Excel formulas", { text: "PASS", options: { bold: true, color: "008000" } }]);
  table(s, rows, MX, 1.35, CW, [1.9, 1.0, 8.03, 1.2], { fontSize: 12, rowH: 0.43 });
  caption(s, `${D.checks.passed} of ${D.checks.n} Python checks pass; live Excel checks in sheet 18_Cross_Checks of Four_Tier_47plots.xlsx. QDA needed the ridge fallback in ${D.fallbacks} fits.`, MX, 6.5, CW);
  notes(s, ["Each step was checked in two independent ways. Python checks run during the analysis (for example: the hand-written ANOVA equals scipy, Tukey equals the ANOVA decision, the re-implemented rpart pruning reproduces scikit-learn, a hand-coded QDA equals scikit-learn, no plot appears in both training and test, every spectrum is tested exactly once).",
    "In the workbook, key numbers are recomputed with Excel formulas directly from the raw spectra (ANOVA F and p for all 483 bands, single-band J–M, the J–M of the whole CART and RF sets with matrix formulas, every accuracy measure of every error matrix, the plot-level accuracy of leave-one-plot-out and the permutation p-values). Sheet 18 compares them with Python and shows ALL PASS."]);
}

// ================================================================== D DISCUSSION
newSection("D. Discussion and conclusion");
{ const s = slide("SECTION", "D · Discussion, summary and conclusion", "What the results mean, their limits and what to do next");
  notes(s, ["Part D interprets the results, lists their limitations and gives the conclusion."]); }
{
  const s = slide("CONTENT", "Discussion");
  boxes(s, [
    ["Statistically different, weakly separable", `${t1.sig} bands differ (Tier 1) but effect sizes are small and the set J–M is ${f2(F.CART.JM, 2)} / ${f2(F.RF.JM, 2)}, far below 1.94. Das et al. separated genotypes with averaged field spectra; here single SMACC endmembers mix leaves, lesions, soil and shadow.`],
    ["Validation decides the accuracy", `The paper's 10-fold CV gives OA ${pct(CV.CART.CV1.OA[0], 0)} / ${pct(CV.RF.CV1.OA[0], 0)}; holding out whole plots gives BA ${f2(Math.min(...realBA), 2)}–${f2(Math.max(...realBA), 2)}. Spectra of one plot are not independent (Hurlbert 1984), so plot-based validation is the honest estimate.`],
    ["Why diseased spectra are missed", `PA healthy ${pct(CV.CART.CV2.acc.spectra.PA_H, 0)} vs PA diseased ${pct(CV.CART.CV2.acc.spectra.PA_D, 0)}. Class means are nearly equal but diseased endmembers vary more (SD ${f2(D.disp.sd_D, 3)} vs ${f2(D.disp.sd_H, 3)}), so QDA calls only the outlying diseased spectra 'diseased': disease shows as variability, not a mean shift.`],
    ["Location confound", `All healthy plots form block C at the west end. Control vs inoculated (BA ${f2(ncMean(ncCtrl, "CART"), 2)}) exceeds inoculated vs inoculated (${f2(ncMean(ncNeg, "CART"), 2)}), suggesting a real control–inoculated difference, but with one control block the restricted permutation cannot go below p = 0.25.`],
    ["CART vs RF; treatment levels", `CART and RF select different wavelengths but give similar accuracy (CV2 BA ${f2(CV.CART.CV2.acc.spectra.BA, 3)} vs ${f2(CV.RF.CV2.acc.spectra.BA, 3)}). Holding out a variety, date or combination gives BA ${f2(Math.min(...designBA), 2)}–${f2(Math.max(...designBA), 2)}; detection does not differ by date or variety.`],
    ["Data quality", `${D.neg.diseased} diseased and ${D.neg.healthy} healthy spectra contain negative reflectance (mainly SWIR-2). CART's root split uses ${F.CART.root.band.toFixed(0)} nm; the sensitivity analysis without bands ≥ 2350 nm gives CV2 BA ${f2(D.sens.CART.CV2_BA[0], 3)} / ${f2(D.sens.RF.CV2_BA[0], 3)}.`],
  ], MX, 1.35, 2, 5.98, 1.7, 0.17, 0.12, 14.5, 11.5);
  notes(s, ["1. The four tiers of Das et al. work as intended, but the data are much harder than in the paper. Das et al. separated 14 rice genotypes with field spectroradiometer measurements of uniform plots; here healthy and diseased canopies are compared through individual SMACC endmembers, which are extreme pixels mixing leaves, lesions, soil and shadow. The class difference is small relative to within-class variation (Tier 3).",
    "2. The validation scheme changes the answer more than any other choice. Random 10-fold CV of spectra (the paper's method) overstates accuracy because near-identical endmembers from one plot are both trained and tested. Plot-based validation is the appropriate estimate for classifying new plots.",
    "3. The error matrices are asymmetric: most healthy spectra are recognised, most diseased spectra are not. Diseased endmembers are more variable than healthy ones while the class means are almost the same, so QDA assigns the bulk of the spectra to the tighter healthy class. For practical use this means the method flags only the most strongly affected spectra; it is not a reliable detector of every diseased plot.",
    "4. CART and RF lead to the same conclusion, and results are consistent across varieties and inoculation dates.",
    "5. The main limitation is the design: the control plots form one contiguous block. The negative control suggests a genuine difference between control and inoculated plots beyond distance, but statistical proof of a disease effect is impossible with one control block.",
    "6. Out-of-range reflectance in the SWIR-2 region is a data-quality issue; the sensitivity analysis shows how much the results depend on it."]);
}
{
  const s = slide("CONTENT", "Summary");
  const items = [
    [String(D.N), `endmember spectra (${D.nH} healthy from 11 plots, ${D.nD} diseased from 36 plots) × ${D.P} bands, analysed individually`],
    [String(t1.sig), `bands significant in Tier 1 (only ${t1.plotmean} with plot means as replicates)`],
    [`${F.CART.bands.length} + ${F.RF.bands.length}`, "bands selected in Tier 2 by CART and by Random Forest"],
    [`${f2(F.CART.JM, 2)} / ${f2(F.RF.JM, 2)}`, `J–M of the CART / RF band sets (Tier 3); single bands ≤ ${f2(Math.max(...F.CART.jm_single, ...F.RF.jm_single), 3)}; threshold 1.94`],
    [`${pct(CV.CART.CV1.OA[0], 0)} / ${pct(CV.RF.CV1.OA[0], 0)}`, "overall accuracy with the validation of Das et al. (CV1, optimistic)"],
    [`${f2(CV.CART.CV2.acc.spectra.BA, 2)} / ${f2(CV.RF.CV2.acc.spectra.BA, 2)}`, `balanced accuracy with whole plots held out (CV2, main); permutation p = ${f2(D.perm.CART.p, 3)}`],
  ];
  items.forEach(([v, l], i) => {
    const x = MX + (i % 3) * 4.1, y = 1.45 + Math.floor(i / 3) * 2.7;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 3.9, h: 2.45, fill: { color: HX.lt2 }, line: { color: HX.lt2 }, rectRadius: 0.08, objectName: "summary " + (i + 1) });
    s.addText(v, { x: x + 0.25, y: y + 0.2, w: 3.4, h: 0.85, fontSize: 34, bold: true, color: C.text2, margin: 0, isTextBox: true, fontFace: THEME.headFontFace, valign: "bottom" });
    s.addText(l, { x: x + 0.25, y: y + 1.15, w: 3.45, h: 1.2, fontSize: 13.5, color: C.text1, margin: 0, isTextBox: true, valign: "top" });
  });
  notes(s, ["Summary of the main numbers. The first value in each pair refers to CART in Tier 2, the second to Random Forest.",
    "The most important contrast is between the two accuracy boxes: the paper's validation (CV1) and plot-based validation (CV2). The second is the realistic accuracy for new plots."]);
}
{
  const s = slide("CLOSING", "Conclusion");
  const pts = [
    `The four-tier method of Das et al. (2020) was applied step by step to all ${D.N} SMACC endmembers of 47 plots, with Random Forest replacing CART in Tier 2 for comparison; every step is reproduced in Excel and cross-checked.`,
    `Healthy and diseased spectra differ statistically, but separability is low: J–M ${f2(F.CART.JM, 2)} (CART) and ${f2(F.RF.JM, 2)} (RF), no single band above ${f2(Math.max(...F.CART.jm_single, ...F.RF.jm_single), 2)}, all far below 1.94.`,
    `With the paper's validation QDA reaches ${pct(CV.CART.CV1.OA[0], 0)} / ${pct(CV.RF.CV1.OA[0], 0)} overall accuracy; with whole plots held out the balanced accuracy is ${f2(Math.min(...realBA), 2)}–${f2(Math.max(...realBA), 2)}, with healthy spectra recognised far more often than diseased (PA ${pct(CV.CART.CV2.acc.spectra.PA_H, 0)} vs ${pct(CV.CART.CV2.acc.spectra.PA_D, 0)}). CART and RF perform similarly.`,
    "Because all control plots form one block, part of the separation may be location. Next trials should replicate control plots in every block, record plot-level disease scores and add an independent date.",
  ];
  s.addText(pts.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < pts.length - 1, paraSpaceAfter: 12 } })), { x: MX, y: 1.5, w: CW, h: 5.3, fontSize: 17.5, color: HX.lt1, margin: 0, isTextBox: true, valign: "middle" });
  notes(s, ["Conclusion in four points: (1) the method was applied completely and transparently; (2) the classes differ but overlap strongly; (3) accuracy depends on how it is validated, and plot-based validation gives the realistic, moderate value, with CART and RF equivalent; (4) the experimental design limits causal interpretation.",
    "Recommendations: randomise control plots within each replication, measure disease severity per plot for a continuous response, keep atmospheric correction under control in the SWIR-2, and validate on an image from another date."]);
}
{
  const per = Math.ceil(D.refs.length / 3);
  [0, 1, 2].map((k) => D.refs.slice(k * per, (k + 1) * per)).forEach((part, k) => {
    const s = slide("CONTENT", `References (${k + 1}/3)`);
    s.addText(part.map((r, i) => ({ text: r[1], options: { bullet: true, breakLine: i < part.length - 1, paraSpaceAfter: 5 } })), { x: MX, y: 1.35, w: CW, h: 5.5, fontSize: 12, color: C.text1, margin: 0, isTextBox: true, valign: "top" });
    notes(s, ["References cited in this presentation. Each was checked against the journal, publisher, repository or library record; sheet 17_References of the workbook lists what each reference is used for and the record it was checked against."]);
  });
}

pres.writeFile({ fileName: OUT }).then(async () => { await applyTheme(OUT, THEME); console.log("wrote", OUT); });
