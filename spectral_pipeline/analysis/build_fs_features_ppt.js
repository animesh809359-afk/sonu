// Presentation: disease-specific features across the feature-selection methods
// usage: PPTX_SKILL=<pptx skill dir> node build_fs_features_ppt.js <work dir> <out.pptx>
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const WORK = process.argv[2];
const OUT = process.argv[3];
const J = JSON.parse(fs.readFileSync(path.join(WORK, "fsfeat.json"), "utf8"));
const FIG = (n) => (n.startsWith("FS") ? path.join(J.fig_fs, n + ".png") : path.join(J.fig, n + ".png"));
const sizeOf = (f) => { const b = fs.readFileSync(f); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; };
const THEME = { name: "Disease-specific features", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1B1B1A", lt1: "FFFFFF", dk2: "1F3D2B", lt2: "F0EFEC", accent1: "1C5CAB", accent2: "EB6834", accent3: "1BAF7A",
            accent4: "EDA100", accent5: "6250D6", accent6: "52514E", hlink: "2A78D6", folHlink: "6250D6" } };
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Disease-specific spectral features of white rust in mustard leaves";
pres.author = "Animesh Panda";
const W = 13.333, H = 7.5, M = 0.5;
pres.defineSlideMaster({ title: "TITLE", background: { color: "1F3D2B" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 1.7, w: W - 2 * M, h: 1.9, fontFace: "Cambria", fontSize: 38, bold: true, color: "FFFFFF", valign: "bottom" }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: M, y: 3.8, w: W - 2 * M, h: 2.4, fontSize: 18, color: "E3F4EC", valign: "top" }, text: "" } }] });
pres.defineSlideMaster({ title: "SECTION", background: { color: "1F3D2B" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 2.6, w: W - 2 * M, h: 1.2, fontFace: "Cambria", fontSize: 34, bold: true, color: "FFFFFF", valign: "bottom" }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: M, y: 3.9, w: W - 2 * M, h: 1.8, fontSize: 18, color: "E3F4EC", valign: "top" }, text: "" } }],
  slideNumber: { x: W - 0.9, y: H - 0.45, fontSize: 10, color: "B5D6C3" } });
pres.defineSlideMaster({ title: "CONTENT", background: { color: "FFFFFF" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 0.3, w: W - 2 * M, h: 0.8, fontFace: "Cambria", fontSize: 25, bold: true, color: "1F3D2B", valign: "middle" }, text: "" } },
            { text: { text: "White rust · mustard leaves · disease-specific features across 23 feature-selection methods",
                      options: { x: M, y: H - 0.42, w: 10, h: 0.3, fontSize: 9, color: "8A8981" } } }],
  slideNumber: { x: W - 0.9, y: H - 0.42, fontSize: 10, color: "8A8981" } });

let section = "Introduction";
const sec = (t, body) => { section = t; pres.addSection({ title: t }); const s = pres.addSlide({ masterName: "SECTION", sectionTitle: t }); s.addText(t, { placeholder: "title" }); if (body) s.addText(body, { placeholder: "body" }); };
const content = (title) => { const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section }); s.addText(title, { placeholder: "title" }); return s; };
function img(s, name, x, y, w, h) {
  const f = FIG(name);
  if (!fs.existsSync(f)) return;
  const d = sizeOf(f), r = Math.min(w / d.w, h / d.h);
  s.addImage({ path: f, x: x + (w - d.w * r) / 2, y: y + (h - d.h * r) / 2, w: d.w * r, h: d.h * r, altText: name });
}
function table(s, rows, x, y, w, o = {}) {
  const f = o.fontSize || 11, hl = o.highlight || [];
  s.addTable(rows.map((r, i) => r.map((c) => ({ text: String(c), options: i === 0 ? { bold: true, color: "FFFFFF", fill: { color: "1F3D2B" }, fontSize: f, valign: "middle" }
    : { fontSize: f, color: "1B1B1A", fill: { color: hl.includes(i) ? "E3F4EC" : (i % 2 ? "FFFFFF" : "F7F7F5") } } }))),
  { x, y, w, colW: o.colW, border: { type: "solid", pt: 0.5, color: "D9D8D2" }, margin: 0.04, rowH: o.rowH || 0.26, autoPage: false });
}
function bullets(s, items, x, y, w, h, fontSize = 14) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
            { x, y, w, h, fontSize, color: "1B1B1A", valign: "top", paraSpaceAfter: 6, isTextBox: true });
}
function refnote(s, t) { s.addText(t, { x: M, y: H - 0.8, w: W - 2 * M, h: 0.35, fontSize: 10, italic: true, color: "52514E", isTextBox: true, margin: 0 }); }
function stat(s, value, label, x, y, w, color) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.5, fill: { color: "F0EFEC" }, line: { color: "F0EFEC" }, rectRadius: 0.08 });
  s.addText(value, { x: x + 0.15, y: y + 0.08, w: w - 0.3, h: 0.75, fontFace: "Cambria", fontSize: 30, bold: true, color, isTextBox: true, margin: 0 });
  s.addText(label, { x: x + 0.15, y: y + 0.82, w: w - 0.3, h: 0.65, fontSize: 12, color: "52514E", isTextBox: true, margin: 0, valign: "top" });
}
function card(s, x, y, w, h, color, title, lines, fs_ = 12) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: "FFFFFF" }, line: { color, width: 1.5 } });
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.48, fill: { color }, line: { color } });
  s.addText(title, { x: x + 0.12, y, w: w - 0.24, h: 0.48, fontSize: 14, bold: true, color: "FFFFFF", valign: "middle", isTextBox: true, margin: 0 });
  bullets(s, lines, x + 0.08, y + 0.56, w - 0.16, h - 0.62, fs_);
}
const pct = (v) => (100 * v).toFixed(1) + " %";
const fx = Object.fromEntries(J.fixed.slice(1).map((r) => [r[0], r]));

// ================================================================ title
pres.addSection({ title: "Introduction" });
let s = pres.addSlide({ masterName: "TITLE", sectionTitle: section });
s.addText("Disease-specific spectral features of white rust in mustard leaves: what 23 feature-selection methods agree on", { placeholder: "title" });
s.addText([{ text: "Features chosen by filter, wrapper and embedded methods · features stable across methods, dates, growth stages and varieties · a feature set to discriminate healthy and diseased leaves", options: { breakLine: true } },
           { text: "2264 leaf spectra (378 healthy, 1886 diseased) · ASD contact probe, 1-nm · K1–K4 pool of 4150 features · 20 plot-grouped training sets", options: { breakLine: true, fontSize: 14, color: "B5D6C3" } },
           { text: "Animesh Panda · Division of Agricultural Physics, ICAR-IARI, New Delhi", options: { fontSize: 14, color: "B5D6C3" } }], { placeholder: "body" });

s = content("Key messages");
stat(s, "3", "core water features chosen by 10–17 of the 21 methods", M, 1.25, 3.0, "0D366B");
stat(s, "5", "stable spectral regions (selected by ≥ 11 of 21 methods)", M + 3.1, 1.25, 3.0, "1C5CAB");
stat(s, "7 / 7", "stable features keep the same direction on every date, stage and variety", M + 6.2, 1.25, 3.0, "1BAF7A");
stat(s, fx["Stable + complementary set (11)"][4], "RF balanced accuracy on new plots with the 11-feature recommended set", M + 9.3, 1.25, 3.0, "C98500");
bullets(s, ["The most stable disease-specific signal is LEAF WATER: the width of the 970-nm water band (narrower in diseased leaves) and the position and symmetry of the 1940-nm water band (shifted and more asymmetric) — chosen by 17, 13 and 10 of 21 methods.",
            "Derivative bands on the 1940-nm water-band wing (1915, 1934 nm) and across the NIR plateau (848–911 nm; leaf structure) are the next most stable features.",
            "All seven stable features change in the same direction on all 4 dates, 3 growth stages and 3 varieties.",
            "Stable features alone are not the most accurate: weak but complementary features (anthocyanin index ARI, C–H bands 1724 / 2223 / 2306 nm) raise QDA accuracy from 70.8 % to 80.2 % and RF to 85.6 %."],
        M, 2.95, W - 2 * M, 3.8, 14);

s = content("How 'disease-specific' and 'stable' were judged");
bullets(s, ["23 methods (11 filter, 6 wrapper, 6 embedded + Borda consensus) selected features from the same K1–K4 pool (4150 features) inside 20 plot-grouped training sets — never using the test plots.",
            "For each method, the redundancy-controlled top-10 features (|r| < 0.95 between chosen features) of each training set were recorded.",
            "Selection frequency = share of the 20 training sets in which a feature (± 10 nm, same spectral series) was in the top-10.",
            "STABLE across methods = selected in ≥ 50 % of training sets by many methods (core ≥ 10 of 21; supporting 5–9; complementary 3–4). Pearson r and Fisher score count once (identical to ANOVA F).",
            "STABLE across conditions = same direction of change and useful AUC within every date, growth stage and variety.",
            "INFORMATIVE = balanced accuracy on held-out plots, AUC and effect size (Hedges g).",
            "Features within 10 nm of an ASD detector join (≈ 1000, 1800 nm) are flagged as possible artefacts."],
        M, 1.25, 7.3, 5.4, 14);
card(s, 8.1, 1.3, 4.7, 1.6, "2A78D6", "Filter (11)", ["Pearson r · ANOVA F · Fisher · χ² · MI · ReliefF · J–M · mRMR · SPA · MC-UVE · CWT"], 12);
card(s, 8.1, 3.05, 4.7, 1.45, "C98500", "Wrapper (6)", ["SVM-RFE · RF-RFE · CARS · SFFS (QDA) · SFFS (J–M) · GA"], 12);
card(s, 8.1, 4.65, 4.7, 1.6, "14895F", "Embedded (6) + consensus", ["RF · CART · Boruta · PLS-VIP · LASSO · gradient boosting · Borda"], 12);

// ================================================================ regions
sec("Where are the disease-specific features?", "Spectral regions selected by the different feature-selection methods");
s = content("Five spectral regions are selected by most methods");
img(s, "FD01_regions_on_spectrum", M, 1.05, 8.6, 4.2);
table(s, J.regions.slice(0, 7).map((r) => [r[0], r[1], r[2]]), M, 5.3, 8.6, { colW: [3.6, 3.8, 1.2], fontSize: 9.5, rowH: 0.22 });
bullets(s, ["Liquid water: continuum-removed 970-nm and 1940-nm water bands (18 of 21 methods each) and the 1940-nm band wing in the first derivative (11 methods).",
            "Leaf structure: first-derivative slope across the NIR plateau 760–930 nm (16 methods).",
            "Dry matter: C–H absorption near 1730 nm (12 methods) and 2200–2300 nm (6 methods) — complementary information.",
            "Pigments (red edge, visible) are chosen by few methods: white rust changes water and structure more consistently than chlorophyll."],
        9.3, 1.2, 3.5, 5.6, 12);

s = content("Which regions does each method select?");
img(s, "FD02_region_map", M, 1.05, 8.9, 5.85);
bullets(s, ["Cells = share of the 20 training sets in which the method's top-10 contains ≥ 1 feature of the region; brackets = number of methods with ≥ 50 %.",
            "Almost every method takes the 970-nm and 1940-nm water features and the NIR-plateau slope.",
            "Linear and PLS-based selectors (SVM-RFE, CARS, LASSO, PLS-VIP) add the 1730 and 2300 nm C–H regions and the 970-nm shoulder.",
            "SPA and SFFS (J–M) differ most: they favour uncorrelated or variance-based features (pigment CR bands, edge parameters)."],
        9.55, 1.2, 3.3, 5.6, 12);

// ================================================================ per method
sec("Disease-specific features chosen by each method", "Top-10 features on all leaves (redundancy-controlled) and the regions they belong to");
const famSlides = [["Filter", "Filter methods: features and regions"], ["Wrapper", "Wrapper methods: features and regions"], ["Embedded", "Embedded methods and consensus: features and regions"]];
famSlides.forEach(([fam, title]) => {
  s = content(title);
  const rows = J.per_method[fam];
  const fsz = rows.length > 9 ? 8.5 : 10;
  table(s, rows, M, 1.15, W - 2 * M, { colW: [1.6, 6.3, 4.4], fontSize: fsz, rowH: rows.length > 9 ? 0.48 : 0.62 });
});

s = content("Which exact features do the methods agree on?");
img(s, "FS08_selection_frequency", M, 1.05, W - 2 * M, 5.85);

// ================================================================ stable features
sec("Features stable across most methods", "Agreement between methods, consistency across dates, stages and varieties, and difference between healthy and diseased leaves");
s = content("How many methods agree on each feature?");
img(s, "FD03_feature_agreement", M, 1.05, 7.3, 5.85);
bullets(s, ["Core (≥ 10 of 21 methods): CR3 970-nm width (17), CR6 1940-nm position (13), CR6 1940-nm symmetry (10).",
            "Supporting (5–9): D1_1934 (9), D1_898 (8), D1_1724 (8), D1_1915 (6), D1_848 (6), D1_2306 (5), D1_1792 (5, next to the 1800-nm join).",
            "Complementary (3–4): D1_872, D1_911, D1_832, D1_861 (same NIR-slope region as D1_848/898), D1_1945, D1_2223, D1_2209, ARI, D1_1744, SDr/SDb, D1_981 (next to the 1000-nm join).",
            "Neighbouring 1-nm bands are interchangeable: the NIR-slope REGION (832–911 nm) is stable even though the exact band varies between methods."],
        8.0, 1.2, 4.8, 5.6, 12.5);

s = content("The stable features: tier, AUC and change from healthy to diseased");
table(s, J.tiers, M, 1.15, W - 2 * M, { colW: [2.4, 1.6, 1.2, 0.8, 4.6, 1.7], fontSize: 10, rowH: 0.3, highlight: [1, 2, 3] });
refnote(s, "Derivative values ×10⁻³ nm⁻¹; CR width and position in nm. AUC is direction-free (0.5 = no discrimination).");

s = content("Which methods select the core and supporting features?");
table(s, J.which, M, 1.15, W - 2 * M, { colW: [2.3, 10.0], fontSize: 9.5, rowH: 0.42 });
bullets(s, ["The water-band continuum features are chosen by all three families — filters, wrappers and embedded methods — which is why they are the most trustworthy disease markers.",
            "Derivative features are chosen mainly by filters and tree-based methods; wrappers replace some of them by complementary features."], M, 5.65, W - 2 * M, 1.1, 12.5);

s = content("Stable across dates, growth stages and varieties?");
img(s, "FD04_consistency_strata", M, 1.05, 8.4, 5.85);
bullets(s, ["All seven stable features (3 water CR features, D1_1934, D1_1915, D1_848, D1_898) change in the SAME direction on all 4 dates, in all 3 growth stages and all 3 varieties.",
            "Water-band position / symmetry and D1_1915 are strongest early in the season and at the vegetative stage (AUC 0.86–0.93), the 970-nm width at flowering and pod formation (0.79–0.87).",
            "NIR-slope derivatives (D1_832–911) are the most even (AUC 0.69–0.90 in every stratum).",
            "D1_1724 is NOT consistent on its own (direction differs on 2 of 4 dates) — it only helps in combination."],
        9.1, 1.2, 3.7, 5.6, 12);

s = content("Healthy vs diseased leaves for the stable features");
img(s, "FD05_class_distributions", M, 1.05, W - 2 * M, 5.8);

s = content("What the stable features mean physiologically");
table(s, [["Feature", "Change in diseased leaves", "Interpretation"],
          ["CR3 970-nm water band width", "narrower (64.2 → 60.9 nm)", "Lower / redistributed leaf water: pustules rupture the epidermis and increase water loss"],
          ["CR6 1940-nm water band position", "shifted to longer wavelength (1912 → 1917 nm)", "Change in the water absorption shape (free vs bound water)"],
          ["CR6 1940-nm water band symmetry", "more asymmetric (0.238 → 0.250)", "Same water signal, shape of the band"],
          ["D1 1915 / 1934 nm", "steeper wing of the 1940-nm band", "Water-band depth and slope change"],
          ["D1 832–911 nm (848, 898)", "slope turns from negative to slightly positive", "Altered mesophyll scattering (hyphae, pustules, cell damage) on the NIR plateau"],
          ["ARI (anthocyanin index)", "higher (−1.00 → −0.59)", "Anthocyanin accumulation in stressed tissue"],
          ["D1 1724, 2223, 2306 nm", "small shifts (weak alone)", "C–H / N–H absorption of cellulose, lignin, proteins — dry-matter changes"]],
      M, 1.2, W - 2 * M, { colW: [3.0, 3.6, 5.7], fontSize: 11.5, rowH: 0.55 });
refnote(s, "Absorption-feature assignments as summarised by Thomas et al. (2018) and Mahlein et al. (2013).");

// ================================================================ discrimination
sec("Using the stable features to discriminate healthy and diseased leaves");
s = content("How well do the stable features discriminate?");
img(s, "FD06_performance", M, 1.05, 7.0, 5.0);
table(s, J.fixed, 7.7, 1.2, 5.1, { colW: [1.75, 0.35, 0.65, 0.65, 0.65, 0.55, 0.5], fontSize: 8.5, rowH: 0.42 });
bullets(s, [`Water features alone (3): RF ${fx["Core water features (3)"][4]}. Adding the stable derivatives (7): RF ${fx["Stable disease-specific set (7)"][4]}.`,
            `Adding 4 complementary features (11): QDA ${fx["Stable + complementary set (11)"][2]}, RF ${fx["Stable + complementary set (11)"][4]}, AUC ${fx["Stable + complementary set (11)"][5]} — close to the four-tier RF-17 set (84.5 %).`,
            `A selector re-run on each training set (SVM-RFE) remains best (QDA ${pct(J.svm)}, RF ${pct(J.svm_rf)}).`],
        7.7, 4.0, 5.1, 2.8, 11.5);
refnote(s, "Fixed sets were defined from selection frequencies over the same 20 training sets, so their accuracies are slightly optimistic; the Borda consensus re-selected inside each training set gives the honest consensus estimate.");

s = content("Recommended disease-specific features for healthy vs diseased mustard leaves");
card(s, M, 1.2, 4.0, 5.3, "0D366B", "1 · Core (always use)", ["CR3 970-nm water band WIDTH — narrower in diseased", "CR6 1940-nm water band POSITION — shifted to longer λ", "CR6 1940-nm water band SYMMETRY — more asymmetric", "chosen by 10–17 of 21 methods; same direction on every date, stage and variety"], 13);
card(s, 4.65, 1.2, 4.0, 5.3, "1C5CAB", "2 · Stable supporting", ["D1 1934 nm — higher in diseased", "D1 1915 nm — lower in diseased", "D1 848 nm (NIR slope 832–872)", "D1 898 nm (NIR slope 883–911)", "chosen by 6–9 methods; consistent in all strata; any band within ±10 nm works"], 13);
card(s, 8.8, 1.2, 4.0, 5.3, "C98500", "3 · Complementary (in models)", ["ARI — anthocyanin index", "D1 2223 nm — 2200-nm dry-matter band", "D1 1724 nm — C–H 1730 nm", "D1 2306 nm — C–H/N–H 2300 nm", "weak alone, but raise RF to 85.6 % and AUC to 0.91", "flag: D1_981, D1_1792 (detector joins)"], 13);
refnote(s, "Recommended discriminating set = 1 + 2 + 3 (11 features): QDA 80.2 %, LDA 81.4 %, RF 85.6 %, AUC 0.91 on new plots.");

s = content("Cautions");
bullets(s, ["Stable ≠ maximally accurate: the most reproducible features describe one signal (water + structure); a wrapper (SVM-RFE, SFFS) that adds complementary features per training set is ≈ 2–7 points more accurate.",
            "The exact 1-nm band within a stable region varies between methods (ASD data are interpolated from ≈ 3–10 nm resolution): report regions, or any band within ±10 nm.",
            "D1_981 and D1_1792 lie within 10 nm of the ASD detector joins (1000, 1800 nm) — they may carry splice residuals and should not be used for a sensor without checking.",
            "D1_1724 changes direction between dates; use it only inside a multivariate model.",
            "Results come from pooled data (4 dates, 3 stages, 3 varieties); transfer to an unseen date was weaker in the main analysis — calibrate with all growth stages."],
        M, 1.2, W - 2 * M, 5.4, 14);

s = content("Conclusions");
bullets(s, ["Across 21 distinct feature-selection methods, the white-rust signal in mustard leaves is dominated by LEAF WATER: the 970-nm water-band width and the 1940-nm water-band position and symmetry are selected by 10–17 methods and are the most stable disease-specific features.",
            "First-derivative features on the 1940-nm water-band wing (1915, 1934 nm) and the NIR-plateau slope (832–911 nm) are stable across methods and across all dates, growth stages and varieties.",
            "Dry-matter (C–H 1724, 2223, 2306 nm) and pigment-stress (ARI) features are complementary: weak alone, they add the information that turns the stable features into an accurate classifier.",
            `Recommended set for discriminating healthy and diseased leaves: 3 core + 4 supporting + 4 complementary features (RF ${fx["Stable + complementary set (11)"][4]}, AUC ${fx["Stable + complementary set (11)"][5]} on new plots); for maximum accuracy, re-select with SVM-RFE (87 %).`],
        M, 1.2, W - 2 * M, 5.5, 15);

// ================================================================ references
const keys = ["Abdulridha 2023", "Ambroise 2002", "Araújo 2001", "Breiman 2001", "Centner 1996", "Cheng 2010", "Das 2020", "Demšar 2006", "Guyon 2002",
              "Kononenko 1994", "Kuncheva 2007", "Kursa 2010", "Li 2009", "Liu 2024", "Mahlein 2013", "Mustafa 2022", "Mustafa 2023", "Nogueira 2018",
              "Peng 2005", "Pudil 1994", "Saeys 2008", "Thomas 2018", "Tibshirani 1996", "Wei 2021", "Wold 2001", "Zhu 2017"];
const refs = keys.map((k) => J.refs[k]).filter(Boolean).sort();
const per = Math.ceil(refs.length / 2);
for (let k = 0; k < 2; k++) {
  s = content(`References (${k + 1}/2)`);
  bullets(s, refs.slice(k * per, (k + 1) * per), M, 1.1, W - 2 * M, 5.9, 10.5);
}
pres.writeFile({ fileName: OUT }).then(async () => { await applyTheme(OUT, THEME); console.log("deck written", OUT); });
