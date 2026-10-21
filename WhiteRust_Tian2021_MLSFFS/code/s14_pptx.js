// Slide deck: ML-SFFS (Tian et al., 2021) applied to white rust of mustard. Usage: node s14_pptx.js <scratch> <out.pptx> <skilldir>
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const [S, OUT, SKILL] = process.argv.slice(2);
const { applyTheme } = require(`${SKILL}/scripts/apply_theme.js`);
const D = JSON.parse(fs.readFileSync(`${S}/out/pptdata.json`, "utf8"));
const FIG = `${S}/figs`;

const THEME = {
  name: "Mustard Navy", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1B1B1B", lt1: "FFFFFF", dk2: "0D366B", lt2: "F3F6FA", accent1: "1C5CAB", accent2: "E3A21A",
            accent3: "1BAF7A", accent4: "EB6834", accent5: "6250D6", accent6: "52514E", hlink: "1C5CAB", folHlink: "6250D6" },
};
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";               // 13.33 x 7.5 in
pres.title = "White rust ML-SFFS (Tian et al. 2021 method)";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const W = 13.33, H = 7.5;

pres.defineSlideMaster({ title: "TITLE", background: { color: THEME.colors.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 1.9, fontFace: "Cambria", fontSize: 38, bold: true, color: "FFFFFF", valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 1.6, fontFace: "Calibri", fontSize: 18, color: "DCE8F7", valign: "top" }, text: "" } },
  ] });
pres.defineSlideMaster({ title: "SECTION", background: { color: THEME.colors.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.6, w: 11.7, h: 1.3, fontFace: "Cambria", fontSize: 36, bold: true, color: "FFFFFF" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.9, w: 11.7, h: 1.2, fontFace: "Calibri", fontSize: 18, color: "E3A21A" }, text: "" } },
  ], slideNumber: { x: 12.4, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: "DCE8F7" } });
pres.defineSlideMaster({ title: "CONTENT", background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 12.3, h: 0.8, fontFace: "Cambria", fontSize: 30, bold: true, color: "0D366B", valign: "middle" }, text: "" } },
    { text: { text: "White rust of mustard · ML-SFFS after Tian et al. (2021)", options: { x: 0.5, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: "8C8B86", fontFace: "Calibri" } } },
  ], slideNumber: { x: 12.4, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: "8C8B86" } });

let sec = "";
function slide(master, section) {
  if (section && section !== sec) { pres.addSection({ title: section }); sec = section; }
  return pres.addSlide({ masterName: master, sectionTitle: sec });
}
function img(s, file, x, y, w, h, name) {
  // keep aspect: read PNG size
  const b = fs.readFileSync(`${FIG}/${file}.png`); const iw = b.readUInt32BE(16), ih = b.readUInt32BE(20);
  let ww = w, hh = w * ih / iw;
  if (hh > h) { hh = h; ww = h * iw / ih; }
  s.addImage({ path: `${FIG}/${file}.png`, x: x + (w - ww) / 2, y, w: ww, h: hh, objectName: name || file });
}
function txt(s, text, o) { s.addText(text, { isTextBox: true, fontFace: "Calibri", fontSize: 15, color: "1B1B1B", valign: "top", margin: 0.05, ...o }); }
function bullets(s, items, o) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
    { isTextBox: true, fontFace: "Calibri", fontSize: 15, color: "1B1B1B", valign: "top", paraSpaceAfter: 6, margin: 0.05, ...o });
}
function card(s, x, y, w, h, head, body, color, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: "F3F6FA" }, line: { color: "DCE8F7", width: 1 }, rectRadius: 0.08, objectName: name + "-bg" });
  s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.22, w: 0.42, h: 0.42, fill: { color: color }, line: { color: color }, objectName: name + "-dot" });
  s.addText(head, { isTextBox: true, x: x + 0.75, y: y + 0.15, w: w - 0.9, h: 0.55, fontFace: "Cambria", fontSize: 17, bold: true, color: "0D366B", valign: "middle", margin: 0, objectName: name + "-head" });
  const content = Array.isArray(body) ? body.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < body.length - 1 } })) : body;
  s.addText(content, { isTextBox: true, x: x + 0.25, y: y + 0.8, w: w - 0.45, h: h - 0.95, fontFace: "Calibri", fontSize: 16, color: "1B1B1B", valign: "top", margin: 0, paraSpaceAfter: 6, objectName: name + "-body" });
}
function stat(s, x, y, w, big, small, color, name) {
  s.addText(big, { isTextBox: true, x, y, w, h: 0.9, fontFace: "Cambria", fontSize: 40, bold: true, color: color || "1C5CAB", align: "left", margin: 0, objectName: name + "-big" });
  s.addText(small, { isTextBox: true, x, y: y + 0.9, w, h: 0.7, fontFace: "Calibri", fontSize: 13, color: "52514E", align: "left", margin: 0, objectName: name + "-small" });
}
function table(s, header, rows, o) {
  const hdr = header.map(h => ({ text: h, options: { bold: true, color: "FFFFFF", fill: { color: "1C5CAB" }, fontSize: o.fs || 11 } }));
  const body = rows.map((r, i) => r.map(c => ({ text: String(c), options: { fontSize: o.fs || 11, fill: { color: i % 2 ? "FFFFFF" : "F3F6FA" } } })));
  s.addTable([hdr, ...body], { x: o.x, y: o.y, w: o.w, colW: o.colW, fontFace: "Calibri", color: "1B1B1B", border: { type: "solid", pt: 0.5, color: "D9D8D3" }, margin: 0.04, rowH: o.rowH || 0.26, autoPage: false, objectName: o.name || "table" });
}

// 1 title -----------------------------------------------------------------
let s = slide("TITLE", "Introduction");
s.addText("Spectroscopic detection of white rust in mustard with ML-SFFS", { placeholder: "title" });
s.addText("Step-by-step application and critical re-evaluation of Tian et al. (2021), Remote Sensing of Environment 257, 112350\nPlot-average hyperspectral data · 48 plots · 4 dates (11 Feb – 13 Mar 2026)", { placeholder: "body" });
s.addNotes("Title. The deck follows the workbook and the thesis chapter step by step (Steps 1–7).");

// 2 aim -------------------------------------------------------------------
s = slide("CONTENT");
s.addText("Aim: early detection with few interpretable features", { placeholder: "title" });
card(s, 0.5, 1.4, 4.0, 4.6, "The method", "Tian et al. (2021) detected rice leaf blast from the asymptomatic to the mild stage by (1) data preparation, (2) selecting disease-specific spectral features (DSSFs) by thresholding, consistency across dates and VIF, and (3) ML-SFFS: sequential floating forward selection wrapped around LDA, k-NN or SVM.", "1C5CAB", "c1");
card(s, 4.67, 1.4, 4.0, 4.6, "The data", "48 mustard plots: 3 varieties × 4 inoculation timings (D1–D4) × 3 replications + 12 uninoculated controls. Leaf spectra averaged per plot on 4 dates (T1–T4). Features: reflectance, 1st–3rd derivatives, continuum-removal, 87 vegetation indices, red-edge parameters (+ wavelets).", "E3A21A", "c2");
card(s, 8.84, 1.4, 4.0, 4.6, "The questions", "Which spectral features are disease-specific? How few are needed? How accurate is detection on each date and infection stage – and how much of the paper's accuracy survives an unbiased (nested) evaluation?", "1BAF7A", "c3");
s.addNotes("Three blocks: method, data, research questions.");

// 3 workflow ---------------------------------------------------------------
s = slide("CONTENT", "Method");
s.addText("Workflow: Tian et al. (2021) applied in seven steps", { placeholder: "title" });
img(s, "fig01_workflow", 0.5, 1.2, 5.2, 5.7, "workflow");
bullets(s, ["Steps 1–5 build the pool of DSSFs exactly as in the paper (with corrections C1–C9)",
            "Step 6 selects the optimal feature combination (OFC) with ML-SFFS",
            "A = paper-faithful (4-fold CV × 100), B = nested CV (unbiased), C = permutation null, D = infection stages",
            "Step 7 = cross-checks: Excel formulas, independent recomputation, reference verification"], { x: 6.1, y: 1.6, w: 6.7, h: 4.8, fontSize: 17 });
s.addNotes("The workflow mirrors Fig. 2 of Tian et al.; evaluation is reported in four ways.");

// 4 design ----------------------------------------------------------------
s = slide("CONTENT");
s.addText("Data and experimental design", { placeholder: "title" });
stat(s, 0.6, 1.4, 2.8, "48", "plots: 12 controls + 36 inoculated", "1C5CAB", "s1");
stat(s, 3.6, 1.4, 2.8, "4", "dates T1–T4, vegetative → pod formation", "1C5CAB", "s2");
stat(s, 6.6, 1.4, 3.0, D.ncand.toLocaleString("en-US"), "candidate features per date", "1C5CAB", "s3");
stat(s, 9.8, 1.4, 3.0, "12 : 36", "healthy : diseased – imbalanced", "EB6834", "s4");
table(s, ["Block", "V1 (D1–D4)", "V2 (D1–D4)", "V3 (D1–D4)", "Role"],
  [["C", "1 1 1 1", "1 1 1 1", "1 1 1 1", "uninoculated controls (healthy)"], ["R1", "1 1 1 1", "1 1 1 1", "1 1 1 1", "inoculated, replication 1"],
   ["R2", "1 1 1 1", "1 1 1 1", "1 1 1 1", "inoculated, replication 2"], ["R3", "1 1 1 1", "1 1 1 1", "1 1 1 1", "inoculated, replication 3"]],
  { x: 0.6, y: 3.4, w: 12.1, colW: [1.2, 2.2, 2.2, 2.2, 4.3], fs: 13, rowH: 0.36, name: "design" });
txt(s, "D1–D4 = inoculation timings (days after sowing). Controls were measured first on every date and form their own block – a confound reported as C9.", { x: 0.6, y: 5.5, w: 12.1, h: 0.8, fontSize: 14, color: "52514E", italic: true });
s.addNotes("Balanced factorial design; note the separate control block.");

// 5 corrections -------------------------------------------------------------
s = slide("CONTENT");
s.addText("Corrections to the paper's procedure (C1–C9)", { placeholder: "title" });
table(s, ["Code", "Issue", "Correction"], D.corr.map(r => [r[0], r[1], r[2]]), { x: 0.5, y: 1.25, w: 12.3, colW: [0.7, 3.0, 8.6], fs: 10.5, rowH: 0.58, name: "corrections" });
s.addNotes("Each correction is explained in the workbook (sheet S03) and the thesis chapter (Table 3).");

// 6 step 1 -----------------------------------------------------------------
s = slide("SECTION", "Steps 1–2");
s.addText("Steps 1–2 · Data preparation and physiology", { placeholder: "title" });
s.addText("Quality control, instrument artefacts, confounds, physiological proxies", { placeholder: "body" });
s = slide("CONTENT");
s.addText("Step 1 · Plot-average spectra and quality control", { placeholder: "title" });
img(s, "fig02_mean_spectra", 0.4, 1.2, 7.6, 5.6, "spectra");
bullets(s, ["Labels, varieties and treatment identical across all files (PASS)",
            "Detector edges and joins (grey) excluded: derivatives at 1825–1830 nm separated the classes 'perfectly' – an instrument step, not biology (C1)",
            "mCARI1 ≡ MTVI1 and RARSc ≡ GM2 in the source workbooks (duplicates)",
            "CWT (Mexican hat, scales 2³–2⁸) computed to follow the paper"], { x: 8.2, y: 1.4, w: 4.7, h: 5.3, fontSize: 15 });
s.addNotes("Spectra are means ± 1 SD. Diseased plots: higher red reflectance and a flatter NIR plateau.");

s = slide("CONTENT");
s.addText("Step 2 · Water first, then pigments: the physiological basis", { placeholder: "title" });
img(s, "fig06_physiology_boxplots", 0.4, 1.15, 9.1, 4.8, "physio");
bullets(s, ["T1: only the water indices (WI, NDWI) lower in diseased plots",
            "T2–T4: chlorophyll (CIrededge, MTCI, REIP), carotenoid (CRI1) and PRI lower; anthocyanin (ARI) higher",
            `${D.nsig} of 32 tests significant after BH-FDR`,
            "Same pattern as rice blast in Tian et al. (Fig. 4), but water before pigments"], { x: 9.7, y: 1.3, w: 3.3, h: 5.4, fontSize: 14 });
s.addNotes("Proxies replace the paper's measured biochemistry (C8). Test rule: median ± 3 MAD outliers, Shapiro–Wilk + Levene → t-test or Mann–Whitney, BH-FDR.");

// 7 separability -------------------------------------------------------------
s = slide("SECTION", "Steps 3–5");
s.addText("Steps 3–5 · Feature selection", { placeholder: "title" });
s.addText("Thresholding separability → DSSFs → VIF", { placeholder: "body" });
s = slide("CONTENT");
s.addText("Step 3 · Separability of a single feature by thresholding", { placeholder: "title" });
img(s, "fig03_threshold_concept", 0.4, 1.3, 7.2, 4.6, "threshold");
card(s, 8.0, 1.3, 4.8, 4.9, "How it works", "The interval between the class means Mh and Mi is divided into 100 steps; each step is tried as a threshold. Separability = balanced accuracy BA = (sensitivity + specificity)/2 at the best threshold (C2). With 12 vs 36 plots, calling every plot 'diseased' already gives OA = 75 % but BA = 50 %.", "E3A21A", "thr");
s.addNotes("Analogue of Fig. 3 in Tian et al.; BA replaces OA because the classes are imbalanced.");

s = slide("CONTENT");
s.addText("Step 3 · Classification scalograms", { placeholder: "title" });
img(s, "fig04_scalogram_R", 0.4, 1.15, 6.3, 2.6, "scR");
img(s, "fig04_scalogram_D1", 6.75, 1.15, 6.3, 2.6, "scD1");
img(s, "fig04_scalogram_D2", 0.4, 3.95, 6.3, 2.6, "scD2");
img(s, "fig04_scalogram_D3", 6.75, 3.95, 6.3, 2.6, "scD3");
s.addNotes("T1: visible bands and the NIR slope; T2: red / red edge; T3: nearly everything; T4: SWIR.");

s = slide("CONTENT");
s.addText("Step 3 · Wavelet scalograms (scales 3–8)", { placeholder: "title" });
img(s, "fig05_scalogram_CWT", 0.4, 1.1, 8.4, 5.8, "scCWT");
bullets(s, ["Top 5 % per date (orange)", "Common to ≥ k* dates (bottom), k* = largest of 4/3/2 with common features (C3)", "One representative per connected region (▼)"], { x: 9.0, y: 1.5, w: 4.0, h: 4.5, fontSize: 15 });
s.addNotes("Analogue of Fig. 7 of Tian et al.");

s = slide("CONTENT");
s.addText(`Steps 4–5 · ${D.ncand.toLocaleString("en-US")} candidates → ${D.npool} DSSFs`, { placeholder: "title" });
stat(s, 0.6, 1.4, 3.0, D.ncand.toLocaleString("en-US"), "candidate features per date", "1C5CAB", "f1");
stat(s, 0.6, 3.0, 3.0, String(D.ncandidates), "region representatives + top-10 % scalar features", "1C5CAB", "f2");
stat(s, 0.6, 4.6, 3.0, String(D.npool), "DSSFs with VIF < 10", "EB6834", "f3");
img(s, "fig07_vif", 4.0, 1.25, 8.8, 5.5, "vif");
s.addNotes("Relevance-aware VIF (C5): among features with VIF ≥ 10 the least separable is removed first.");

s = slide("CONTENT");
s.addText("Step 5 · The 16 disease-specific spectral features", { placeholder: "title" });
table(s, ["Code", "Feature", "Family", "Mean BA", "VIF"], D.dssf, { x: 0.5, y: 1.2, w: 7.6, colW: [0.7, 3.4, 2.1, 0.8, 0.6], fs: 10.5, rowH: 0.32, name: "dssf" });
card(s, 8.4, 1.2, 4.5, 5.3, "What they measure", ["Pigments: R641, wavelet 634 nm, Lic, ARI2", "NIR structure: slope at 852 nm", "Water: 970, 1350, 1875–1940 nm", "Dry matter (C–H): 1736, 1752, 2318 nm", "Blue-edge position", "NIR slope ≈ WF850/866 and yellow edge ≈ WF608 of Tian et al."], "1BAF7A", "meaning");
s.addNotes("Analogue of Table 2 of Tian et al.");

// 8 step 6 -----------------------------------------------------------------
s = slide("SECTION", "Step 6");
s.addText("Step 6 · ML-SFFS classification", { placeholder: "title" });
s.addText("A paper-faithful · B nested CV · C permutation null · D infection stages", { placeholder: "body" });

s = slide("CONTENT");
s.addText("6A · Paper-faithful: one to four features give 95–100 % OA", { placeholder: "title" });
table(s, ["Date", "Classifier", "Most frequent OFC", "OFC freq. %", "Mean OA %", "Mean BA %"], D.faithful, { x: 0.5, y: 1.2, w: 7.4, colW: [0.8, 1.1, 2.4, 1.0, 1.05, 1.05], fs: 11, rowH: 0.36, name: "faithful" });
bullets(s, ["4-fold CV × 100 repetitions, SFFS with OA criterion – exactly as Tian et al.",
            `Mean OA ${D.faOAmin}–100 %; SVM-SFFS best (as in the paper)`,
            "On T2 the pair F2 + F8 (NIR slope + yellow–red edge) is the OFC of all three classifiers",
            "Codes: see DSSF slide"], { x: 8.2, y: 1.3, w: 4.7, h: 5.3, fontSize: 15 });
s.addNotes("Analogue of Table 3 of Tian et al.");

s = slide("CONTENT");
s.addText("6A · SFFS vs all DSSFs, and which features are chosen", { placeholder: "title" });
img(s, "fig08_sffs_vs_all", 0.4, 1.15, 12.5, 2.9, "sva");
img(s, "fig10_selection_frequency", 1.6, 4.15, 10.0, 2.75, "selfreq");
s.addNotes("SFFS gains most on T1 (as SVM-SFFS vs SVM-all in Tian et al., Fig. 8). Under nested CV (black) the gain largely disappears.");

s = slide("CONTENT");
s.addText("6B · Nested CV: honest accuracy is lower but still high", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "A paper-faithful BA", labels: D.chart_labels, values: D.chart_A }, { name: "B nested-CV BA", labels: D.chart_labels, values: D.chart_B }],
  { x: 0.4, y: 1.2, w: 8.6, h: 5.6, barDir: "col", barGrouping: "clustered", chartColors: ["EB6834", "1C5CAB"],
    showLegend: true, legendPos: "t", legendFontSize: 12, legendFontFace: "+mn-lt",
    valAxisMinVal: 50, valAxisMaxVal: 100, valAxisLabelFontSize: 11, catAxisLabelFontSize: 10, catAxisLabelRotate: -45,
    valAxisLabelColor: "52514E", catAxisLabelColor: "52514E", valAxisLabelFontFace: "+mn-lt", catAxisLabelFontFace: "+mn-lt",
    valGridLine: { color: "E4E3DF", size: 0.5 }, catGridLine: { style: "none" },
    showValue: false, showTitle: true, title: "Balanced accuracy (%)", titleFontSize: 13, titleColor: "0D366B", titleFontFace: "+mn-lt", objectName: "chartAB" });
stat(s, 9.3, 1.4, 3.6, `${D.nestBAmin}–${D.nestBAmax} %`, "balanced accuracy on held-out plots (nested CV)", "1C5CAB", "n1");
stat(s, 9.3, 3.3, 3.6, `${D.optmin}–${D.optmax}`, "percentage points of optimism in the paper-faithful estimate", "EB6834", "n2");
txt(s, "Whole pipeline (separability, DSSF pool, VIF, SFFS, SVM tuning) re-run inside every outer fold (C4).", { x: 9.3, y: 5.2, w: 3.6, h: 1.4, fontSize: 13, color: "52514E" });
s.addNotes("Ambroise & McLachlan (2002), Varma & Simon (2006), Cawley & Talbot (2010).");

s = slide("CONTENT");
s.addText(`6C · Random labels still give ${D.nullOAmin}–${D.nullOAmax} % OA`, { placeholder: "title" });
img(s, "fig11_permutation_null", 0.4, 1.2, 12.5, 3.6, "perm");
stat(s, 0.8, 5.0, 3.8, `${D.nullOAmin}–${D.nullOAmax} %`, "mean OA with shuffled labels (procedure A)", "52514E", "p1");
stat(s, 4.9, 5.0, 3.8, `${D.nullBAmin}–${D.nullBAmax} %`, "mean BA with shuffled labels", "52514E", "p2");
stat(s, 9.0, 5.0, 3.8, "p = 0.048", "true labels beat every permutation (LDA, k-NN)", "1BAF7A", "p3");
s.addNotes("20 permutations × 5 repetitions for LDA and k-NN; 4 × 2 for SVM (indicative). Ojala & Garriga (2010).");

s = slide("CONTENT");
s.addText("6D · Infection stages: every inoculation timing is detected", { placeholder: "title" });
img(s, "fig12_stage_wise", 0.9, 1.15, 11.5, 3.9, "stage");
bullets(s, [`Nested CV (SVM): ${D.det_min}–${D.det_max} % of inoculated plots detected in every group and date`,
            `False alarms on controls: ${D.fa_min}–${D.fa_max} %`], { x: 0.6, y: 5.25, w: 6.0, h: 1.5, fontSize: 15 });
bullets(s, ["No consistent ordering by inoculation timing; 9 plots per group → 1 plot = 11 points",
            `Paper-faithful per-stage SVM-SFFS OA ${D.stageOAmin}–${D.stageOAmax} % (optimistic)`], { x: 6.8, y: 5.25, w: 6.0, h: 1.5, fontSize: 15 });
s.addNotes("Stage = date × inoculation timing; analogue of the per-DAI results of Tian et al.");

// 9 interpretation / checks / conclusion --------------------------------------
s = slide("SECTION", "Interpretation");
s.addText("Interpretation, cross-checks and conclusions", { placeholder: "title" });
s.addText("What the features mean, how robust the results are, what to report", { placeholder: "body" });

s = slide("CONTENT");
s.addText("Why these features: the physiology behind the DSSFs", { placeholder: "title" });
card(s, 0.5, 1.3, 3.0, 4.4, "NIR structure", "Slope at 852 nm: controls decline 800–900 nm, diseased plots flat or rising – pustules disrupt epidermis and mesophyll scattering (cf. WF850 of Tian et al.).", "1C5CAB", "i1");
card(s, 3.6, 1.3, 3.0, 4.4, "Pigments", "Red reflectance up, Lic down, ARI2 up: chlorophyll loss and anthocyanin accumulation; yellow–red edge wavelet at 634 nm (cf. WF608).", "EB6834", "i2");
card(s, 6.7, 1.3, 3.0, 4.4, "Water", "970, 1350 and 1875–1940 nm features; water indices lower already on T1.", "1BAF7A", "i3");
card(s, 9.8, 1.3, 3.0, 4.4, "Dry matter", "Wavelets at 1736, 1752, 2318 nm lie in C–H absorptions of cellulose, lignin and protein (Kokaly & Clark, 1999).", "E3A21A", "i4");
s.addNotes("Interpretations rest on spectral proxies (no measured biochemistry).");

s = slide("CONTENT");
s.addText(`Cross-checks: ${D.ck_pass} PASS, ${D.ck_flag} FLAG`, { placeholder: "title" });
table(s, ["Step", "Check", "Status"], D.ck, { x: 0.5, y: 1.2, w: 8.4, colW: [0.6, 6.9, 0.9], fs: 9.5, rowH: 0.26, name: "checks" });
card(s, 9.2, 1.2, 3.7, 5.3, "Also verified", ["Excel formulas reproduce class means, threshold BA of all 16 DSSFs × 4 dates and the summary accuracies exactly", "45 references checked; 5 errors found in the reference list of Tian et al. (2021)"], "1BAF7A", "ck2");
s.addNotes("FLAGs: control block measured first (confound), duplicate indices in source workbooks, optimism of procedure A.");

s = slide("CONTENT");
s.addText("Conclusions", { placeholder: "title" });
bullets(s, [`The ML-SFFS workflow runs step by step on plot-average spectra: ${D.ncand.toLocaleString("en-US")} candidates → ${D.npool} DSSFs covering pigments, NIR structure, water and dry matter`,
            "White rust lowers water indices first (T1), then chlorophyll and carotenoids; anthocyanins rise",
            `Paper-faithful ML-SFFS: 1–4 features, OA ${D.faOAmin}–100 %, SVM best – but optimistic`,
            `Nested CV (report this): BA ${D.nestBAmin}–${D.nestBAmax} %, best on T1 ${D.T1BAbest} %; optimism ${D.optmin}–${D.optmax} points`,
            "All inoculation timings and varieties detected similarly; the control-block confound must be removed in future trials"], { x: 0.6, y: 1.3, w: 12.1, h: 5.4, fontSize: 18 });
s.addNotes("Report procedure B as the accuracy of the method; A only for comparison with the paper.");

s = slide("CONTENT");
s.addText("Limitations and next steps", { placeholder: "title" });
card(s, 0.5, 1.3, 6.0, 4.6, "Limitations", ["Controls in one block and measured first (C9)", "12 vs 36 plots; 9 per inoculation group", "No measured biochemistry – proxies only (C8)", "Inoculation dates (DAS) not available → no DAI", "SVM permutation test small; stage-wise pool from all plots", "One season, one site"], "EB6834", "lim");
card(s, 6.8, 1.3, 6.0, 4.6, "Next steps", ["Randomise controls among blocks and measurement order", "Record inoculation dates; express stages as DAI", "Measure chlorophyll, anthocyanin and water on a subset of leaves", "Validate the stable DSSF core (852, 634, 970/1350/1940 nm, ARI2) on an independent season"], "1BAF7A", "next");
s.addNotes("These points are expanded in Section 5.4–5.5 of the chapter.");

s = slide("CONTENT");
s.addText("Reference cross-check: errors in Tian et al.'s reference list", { placeholder: "title" });
table(s, ["Reference", "Correct citation"], D.referr, { x: 0.5, y: 1.3, w: 12.3, colW: [3.0, 9.3], fs: 13, rowH: 0.55, name: "referr" });
txt(s, "Key references: Tian et al. (2021) RSE 257:112350 · Pudil et al. (1994) PRL 15:1119–1125 · Mahlein et al. (2013) RSE 128:21–30 · Cheng et al. (2010) RSE 114:899–910 · Ambroise & McLachlan (2002) PNAS 99:6562–6566 · Varma & Simon (2006) BMC Bioinf. 7:91 · Brodersen et al. (2010) ICPR · Ojala & Garriga (2010) JMLR 11:1833–1863. Full verified list: workbook sheet S24 and chapter references.",
    { x: 0.5, y: 5.0, w: 12.3, h: 1.6, fontSize: 13, color: "52514E" });
s.addNotes("All 45 references were checked against publisher/repository records.");

pres.writeFile({ fileName: OUT }).then(async () => { await applyTheme(OUT, THEME); console.log("written", OUT); });
