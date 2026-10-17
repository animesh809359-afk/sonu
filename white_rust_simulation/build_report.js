// Builds the Word report from docdata.json (exported from the recalculated workbook).
// Usage: node build_report.js <docdata.json> <output.docx>
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, PageOrientation, BorderStyle, LevelFormat, PageBreak,
  TableOfContents, Footer, PageNumber,
} = require("docx");

const [, , inPath, outPath] = process.argv;
const D = JSON.parse(fs.readFileSync(inPath, "utf8"));

// ---------- layout ----------
const PAGE_W = 11906, PAGE_H = 16838, MARGIN = 900;
const CW = PAGE_H - 2 * MARGIN; // landscape content width
const FONT = "Arial";
const BORDER = { style: BorderStyle.SINGLE, size: 4, color: "A6A6A6" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };

const CLASSES = ["Healthy", "Very low", "Low", "Moderate", "High", "Very high"];
const DI = { "Healthy": "0", "Very low": "1-5", "Low": "6-10", "Moderate": "11-25", "High": "26-50", "Very high": ">50" };
const STAGE_NAME = { V: "Vegetative (3rd fully expanded leaf from top)", F: "Flowering (5th fully expanded leaf from top)", P: "Pod formation (5th fully expanded leaf from top)" };
const CLASS_FILL = { "Healthy": "E2EFDA", "Very low": "F2F7E8", "Low": "FFF8E1", "Moderate": "FFE9C7", "High": "FCD5C0", "Very high": "F4B6B6" };

const P = {}; D.params.forEach((p) => (P[p.Code] = p));
const PC = ["RWC", "MSI", "Pn", "gs", "E", "Ci", "LAI", "ChlA", "ChlB", "Car", "Anth", "Prot"];
const DEC = { RWC: 1, MSI: 1, Pn: 1, gs: 3, E: 2, Ci: 0, LAI: 2, ChlA: 3, ChlB: 3, Car: 3, Anth: 1, Prot: 2 };
const UNIT = {
  RWC: "%", MSI: "%", Pn: "µmol CO₂ m⁻² s⁻¹", gs: "mol H₂O m⁻² s⁻¹", E: "mmol H₂O m⁻² s⁻¹",
  Ci: "µmol mol⁻¹", LAI: "m² m⁻²", ChlA: "µg mg⁻¹ FW", ChlB: "µg mg⁻¹ FW", Car: "mg g⁻¹ FW",
  Anth: "µg g⁻¹ FW (C3G eq.)", Prot: "µg mg⁻¹ FW",
};
const NAME = {
  RWC: "Relative water content", MSI: "Membrane stability index", Pn: "Net photosynthesis (Pn)",
  gs: "Stomatal conductance (gs)", E: "Transpiration (E)", Ci: "Intercellular CO₂ (Ci)", LAI: "Leaf area index",
  ChlA: "Chlorophyll a", ChlB: "Chlorophyll b", Car: "Carotenoids", Anth: "Anthocyanin", Prot: "Total soluble protein",
};

const f = (v, d) => (v === null || v === undefined || Number.isNaN(v) ? "-" : Number(v).toFixed(d));
const pct = (v) => (v === null || v === undefined ? "-" : Math.abs(v) < 0.05 ? "0" : (v > 0 ? "+" : "") + Number(v).toFixed(1) + "%");

// ---------- primitives ----------
const run = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 20, bold: o.bold, italics: o.italics, color: o.color, superScript: o.sup, subScript: o.sub });
const para = (text, o = {}) => new Paragraph({
  children: Array.isArray(text) ? text : [run(text, o)],
  spacing: { after: o.after === undefined ? 100 : o.after, before: o.before || 0, line: o.line || 264 },
  alignment: o.align, keepNext: o.keepNext,
});
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t })], pageBreakBefore: true, spacing: { after: 160 } });
const h2 = (t, br) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t })], pageBreakBefore: !!br, spacing: { before: 200, after: 120 }, keepNext: true });
const h3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text: t })], spacing: { before: 160, after: 80 }, keepNext: true });
const bullet = (t, o = {}) => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: Array.isArray(t) ? t : [run(t, o)], spacing: { after: 60 } });
const num = (t) => new Paragraph({ numbering: { reference: "num", level: 0 }, children: Array.isArray(t) ? t : [run(t)], spacing: { after: 60 } });
const caption = (t) => para(t, { size: 17, italics: true, color: "404040", after: 160 });
const brk = () => new Paragraph({ children: [new PageBreak()] });

function cell(content, w, o = {}) {
  const lines = Array.isArray(content) ? content : [content];
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    borders: BORDERS,
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 70, right: 70 },
    verticalAlign: "center",
    children: lines.map((l, i) => new Paragraph({
      alignment: o.align || AlignmentType.LEFT,
      spacing: { after: 0 },
      children: [run(String(l), { size: i === 0 ? (o.size || 16) : (o.size2 || 14), bold: o.bold && i === 0, color: i > 0 ? "555555" : o.color, italics: i > 0 && o.it2 })],
    })),
  });
}
// rows: array of arrays of strings (or arrays of lines); opts: header rows count, fills, align
function table(widths, rows, o = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const hdr = o.header === undefined ? 1 : o.header;
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((r, ri) => new TableRow({
      tableHeader: ri < hdr,
      cantSplit: true,
      children: r.map((c, ci) => cell(c, widths[ci], {
        bold: ri < hdr || (o.boldFirstCol && ci === 0),
        fill: ri < hdr ? "1F4E79" : o.fillFn ? o.fillFn(ri, ci) : undefined,
        color: ri < hdr ? "FFFFFF" : undefined,
        align: ci === 0 && o.leftFirst !== false ? AlignmentType.LEFT : o.align || AlignmentType.CENTER,
        size: o.size, size2: o.size2, it2: o.it2,
      })),
    })),
  });
}
const scale = (fr) => { const s = fr.reduce((a, b) => a + b, 0); const w = fr.map((x) => Math.floor((x / s) * CW)); w[0] += CW - w.reduce((a, b) => a + b, 0); return w; };
const classFill = (rowsClass) => (ri, ci) => (ci === 0 ? CLASS_FILL[rowsClass[ri]] : undefined);
const colClassFill = (ri, ci) => (ci >= 1 && ci <= 6 ? CLASS_FILL[CLASSES[ci - 1]] : undefined);

// ---------- content ----------
const C = [];

// Title page
C.push(para("", { after: 1200 }));
C.push(para([run("SIMULATED (EXPECTED) PHYSIOLOGICAL, BIOCHEMICAL, THERMAL AND RGB-TEXTURE PARAMETERS OF INDIAN MUSTARD UNDER WHITE RUST (Albugo candida)", { size: 34, bold: true, color: "1F4E79" })], { align: AlignmentType.CENTER, after: 240 }));
C.push(para([run("Healthy vs six disease-index classes, for 4 sowing dates × 3 varieties × 4 assessment dates", { size: 24 })], { align: AlignmentType.CENTER, after: 120 }));
C.push(para([run("Field: ICAR-IARI, New Delhi | Rabi 2025-26 | Assessments 11/02, 24/02, 03/03 and 13/03/2026", { size: 22 })], { align: AlignmentType.CENTER, after: 120 }));
C.push(para([run("Thesis context: AI-based multimodal UAV sensing of white rust in mustard", { size: 22, italics: true })], { align: AlignmentType.CENTER, after: 600 }));
C.push(new Table({
  width: { size: CW, type: WidthType.DXA }, columnWidths: [CW],
  rows: [new TableRow({ children: [new TableCell({
    width: { size: CW, type: WidthType.DXA },
    borders: { top: { style: BorderStyle.SINGLE, size: 18, color: "C00000" }, bottom: { style: BorderStyle.SINGLE, size: 18, color: "C00000" }, left: { style: BorderStyle.SINGLE, size: 18, color: "C00000" }, right: { style: BorderStyle.SINGLE, size: 18, color: "C00000" } },
    shading: { fill: "FFF2F2", type: ShadingType.CLEAR, color: "auto" },
    margins: { top: 160, bottom: 160, left: 200, right: 200 },
    children: [
      para([run("STATUS OF ALL NUMBERS IN THIS REPORT: SIMULATED / EXPECTED VALUES, NOT MEASURED DATA", { bold: true, color: "C00000", size: 22 })], { align: AlignmentType.CENTER }),
      para("Every value is a model output. The model combines published baselines for healthy Brassica juncea, white-rust and analogous-disease effect sizes, the IARI 2025-26 daily weather, the DAS, GDD and phenology of each treatment, and the leaf you sample. Use the values as hypotheses, expected ranges, priors for checking your field data, synthetic data for testing analysis and machine-learning pipelines, and as the 'expected' column when you discuss your results. Do not present them as observations in the thesis, a paper or a report.", { size: 19, align: AlignmentType.JUSTIFIED }),
      para("The companion Excel workbook (White_Rust_Simulated_Parameters_IARI_2025-26.xlsx) holds the same model with live formulas. If you change any input (blue cells), every value recalculates.", { size: 19, after: 0 }),
    ],
  })] })],
}));
C.push(brk());
C.push(para([run("Contents", { bold: true, size: 28, color: "1F4E79" })]));
C.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }));
C.push(para("(Right-click and choose Update Field in Word to refresh page numbers.)", { size: 16, italics: true }));

// 1. Purpose
C.push(h1("1. Purpose and how to use this report"));
C.push(para("Your requirement is to compare, at each growth stage, the healthy plant with plants at different white-rust severities. This report gives the expected value and a plausible range of every measured parameter for each of the six disease-index (DI) classes. The values are given for each treatment (D1V1 … D4V3) at each of the four assessment dates. They are also pooled by growth stage (vegetative, flowering, pod formation), so healthy vs severity can be read directly.", { align: AlignmentType.JUSTIFIED }));
C.push(h3("Recommended uses"));
[
  "Hypotheses and expected direction/magnitude of each parameter when you write the objectives and discussion.",
  "Sanity-check ranges for your raw data. A measured value far outside the simulated 90% range for its class and stage should first be checked for assay or unit errors (e.g. FW vs DW basis, cuvette path length, IRGA chamber leaks).",
  "Synthetic training and test data for your multimodal machine-learning pipeline before the real dataset is complete. Draw from mean ± range and label the draws as synthetic.",
  "Priors for Bayesian or mixed-model analysis, and expected effect sizes for power calculations (number of plants or leaves per plot).",
  "Feature pre-selection for UAV models: which thermal and textural features should separate healthy from each class at each stage.",
].forEach((t) => C.push(bullet(t)));
C.push(h3("How the report is organised"));
[
  "Section 2: your experiment as the model sees it (DAS, DAI, GDD, stage, sampled leaf, weather and the expected DI of each treatment on each date).",
  "Section 3: model equations, parameter baselines and the evidence behind each response.",
  "Section 4 (main result): healthy vs each severity class at each growth stage, as absolute values with ranges and as % change.",
  "Section 5: the same comparison split by stage × assessment date.",
  "Sections 6 and 7: thermal and RGB textural/colour parameters: what to extract, formulas, expected values and changes.",
  "Section 8: which classes are realistically possible on each date. Section 9: limitations. Section 10: references.",
  "Appendix A: complete tables for all 48 treatment × date combinations (12 treatments × 4 dates), each with all 6 classes.",
].forEach((t) => C.push(bullet(t)));
C.push(h3("Reading the tables"));
C.push(para("Each cell shows the expected mean (top line) and, below it, the plausible range (low-high) with the % change vs healthy of the same treatment and date. The range combines two sources of spread: the DI span of the class (e.g. 11-25% for Moderate) and a ±1.645 × CV allowance for plant-to-plant and assay variability, giving roughly a 90% interval. Healthy means the uninoculated control replication of the same sowing date and variety.", { align: AlignmentType.JUSTIFIED }));

// 2. Experimental context
C.push(h1("2. Experimental and climatic context used by the model"));
C.push(h2("2.1 Design"));
C.push(table(scale([3, 7]), [
  ["Item", "Value used"],
  ["Location", "ICAR-IARI research farm, New Delhi (28.6° N, 77.2° E, ~228 m a.s.l.); semi-arid subtropical, cool dry winter with a rapid rise in temperature from late February"],
  ["Design", "RBD; 4 sowing dates × 3 varieties; 3 inoculated replications + 1 healthy (uninoculated) control replication; 48 plots of 5 × 3.5 m"],
  ["Sowing dates", "D1 09/12/2025, D2 18/12/2025, D3 27/12/2025, D4 09/01/2026"],
  ["Varieties", "V1 Pusa Mustard 26 (susceptible, PDI 44.4%), V2 Pusa Vijay (highly susceptible, PDI 55.6%) (Shrivastava et al. 2023); V3 Pusa Mustard 37 (reaction not reported in the papers you supplied; treated as moderately less susceptible, to be verified)"],
  ["Inoculation", "All plots on 05/02/2026 = 58, 49, 40 and 27 DAS for D1-D4 (planned 50/40/30/20 DAS)"],
  ["Assessments", "11/02/2026 (6 DAI), 24/02/2026 (19 DAI), 03/03/2026 (26 DAI), 13/03/2026 (36 DAI)"],
  ["Sampled leaf", "3rd fully expanded leaf from top at vegetative stage; 5th fully expanded leaf from top at flowering and pod formation"],
  ["Severity classes", "Healthy (0), Very low (1-5%), Low (6-10%), Moderate (11-25%), High (26-50%), Very high (>50%) DI, plot DI on the 0-9 scale"],
  ["Parameters", "RWC; MSI; Pn, E, gs (and Ci) by LI-6400; LAI by canopy analyser; Chl a and b (µg mg⁻¹ FW, DMSO); carotenoids (mg g⁻¹ FW); anthocyanin (µg g⁻¹ FW, pH differential); total protein (µg mg⁻¹ FW, Bradford); UAV thermal and RGB"],
], { boldFirstCol: true, align: AlignmentType.LEFT }));

C.push(h2("2.2 Weather at IARI, 9 December 2025 - 13 March 2026 (weekly means from your file)"));
const wxRows = [["Week", "Tmax (°C)", "Tmin (°C)", "RH I (%)", "RH II (%)", "Rain (mm)", "Sunshine (h)", "Leaf-WR favourable days*", "Staghead favourable days*"]];
D.wx.forEach((w) => wxRows.push([w.p, f(w.tmax, 1), f(w.tmin, 1), f(w.rh1, 0), f(w.rh2, 0), f(w.rf, 1), f(w.bss, 1), String(w.leaf), String(w.stag)]));
C.push(table(scale([2.2, 1, 1, 1, 1, 1, 1, 1.6, 1.6]), wxRows, {
  fillFn: (ri) => (ri > 0 && D.wx[ri - 1] && D.wx[ri - 1].tmax >= 27 ? "FCE4D6" : undefined),
}));
C.push(caption("* Criteria of Chattopadhyay et al. (2011). Leaf infection: Tmax 16-24 °C, RH I >97%, RH II >40%, mean RH >72%, mean T >10 °C. Staghead: Tmax 20-29 °C, Tmin >12 °C, RH I >97%, mean RH >72%. Shaded weeks have mean Tmax ≥27 °C, where the model's heat index h > 0."));
C.push(h3("What the weather implies for the simulation"));
[
  "All 17 leaf-favourable days fell between 18 December and 4 February, i.e. before your inoculation on 5 February. No favourable day occurred after inoculation, and no day met the staghead criteria. Natural infection before inoculation is therefore likely, especially in D1 and D2, and it explains any disease already visible on 11/02 (only 6 DAI).",
  "After inoculation the air was dry (RH II 29-46%) and warmed quickly. Mean weekly Tmax rose from 22 °C (early February) to 30-35 °C from 24 February. Leaf-to-air VPD at IRGA time rose from about 0.9 kPa (11/02) to 2-2.5 kPa (13/03). The model therefore lowers healthy gs (VPD response) and Pn and RWC (heat index h), and raises healthy canopy temperature and CWSI on the March dates.",
  "Dry, hot conditions after inoculation limit secondary spread. The model's expected DI is highest in V2 and D1/D2 and stays mostly in the Very low to Moderate classes; High and Very high are flagged as unlikely on most dates (Section 8). Values for every class are still given so all comparisons are possible.",
  "Cold nights (Tmin 3-6 °C in mid-January) raise anthocyanin in young leaves of late sowings (D3, D4). The model applies a cold-legacy factor on 11/02 (D2 ×1.05, D3 ×1.20, D4 ×1.40) and 24/02 (D3 ×1.05, D4 ×1.15).",
].forEach((t) => C.push(bullet(t)));

C.push(h2("2.3 Treatment × date context (inputs to the simulation)", true));
const ctxRows = [["Treatment", "Date", "DAS", "DAI", "GDD from emergence", "Stage", "Sampled leaf", "Tmax / Tmin wk (°C)", "RH I / II wk (%)", "Heat index h", "VPD at IRGA (kPa)", "Healthy LAI", "Expected DI (%)", "Expected class"]];
D.ctx.forEach((c) => ctxRows.push([c.Treatment, c["Date code"].slice(0, 5), String(c.DAS), String(c.DAI), f(c["GDD from emergence"], 0), c["Stage (obs.)"], c["Stage (obs.)"] === "V" ? "3rd" : "5th", `${f(c["Tmax wk"], 1)} / ${f(c["Tmin wk"], 1)}`, `${f(c["RH I wk"], 0)} / ${f(c["RH II wk"], 0)}`, f(c["Heat index h"], 2), f(c["VPD at IRGA (kPa)"], 2), f(c["Healthy LAI"], 2), f(c["Expected DI (%)"], 1), c["Expected class"]]));
C.push(table(scale([1.1, 0.9, 0.6, 0.6, 1.1, 0.7, 0.8, 1.3, 1.1, 0.8, 0.9, 0.9, 0.9, 1.1]), ctxRows, { size: 15, fillFn: (ri, ci) => (ci === 13 && ri > 0 ? CLASS_FILL[ctxRows[ri][13]] : undefined) }));
C.push(caption("GDD base 5 °C from your daily data; emergence assumed at 110 GDD from sowing. Stages are your field observations; they agree with the GDD thresholds of Rana et al. (2017). Expected DI is a scenario: reference DI for the date (3, 18, 28, 35%) × variety susceptibility (V1 0.8, V2 1.0, V3 0.5) × sowing-date exposure (D1 1.0, D2 0.9, D3 0.75, D4 0.6). Replace it with your measured DI."));

// 3. Model
C.push(h1("3. Simulation model, baselines and evidence"));
C.push(h2("3.1 Equations"));
[
  [run("Healthy value ", { bold: true }), run("H = Ref × stage factor (V/F/P, captures 3rd vs 5th leaf and leaf age) × (1 − heat sensitivity × h) × variety factor [× anthocyanin cold factor] [× (VPD/1 kPa)^−0.5 for gs]. Heat index h = max(0, (weekly mean Tmax − 27)/8).")],
  [run("LAI (healthy) ", { bold: true }), run("LAImax(sowing date) × variety factor × 1/(1 + e^−(GDDem − 330)/100) × exp(−[max(0, GDDem − 800)/300]²). LAImax D1 3.4, D2 3.2, D3 2.9, D4 2.5 (later sowing gives a smaller canopy).")],
  [run("Diseased value ", { bold: true }), run("X(s) = H × [1 + R(s) × variety tolerance × lesion-age factor]. s is DI as a fraction. Tolerance V1 1.00, V2 1.10, V3 0.85. The lesion-age factor on 11/02 (6 DAI) is 0.5 for tissue-damage parameters and 0.8 for gas exchange, because Pn falls from 8 DAI but chlorophyll only after 12 DAI (Chou et al. 2000). It is 1.0 on later dates.")],
  [run("Response curves R(s) ", { bold: true }), run("exp: sign × Rmax × (1 − e^−ks). logistic (threshold, for RWC and MSI, which change only after the epidermis ruptures): sign × Rmax × [L(s) − L(0)]/[1 − L(0)], L = 1/(1 + e^−(s − c)/sc). hump (carotenoids, which rise slightly at low severity then fall): exp decline + A(s/peak)e^(1 − s/peak).")],
  [run("Transpiration ", { bold: true }), run("E = gs × VPD_leaf-air / P × 1000 × (1 + 0.25 s). The (1 + 0.25 s) term is extra cuticular loss through ruptured pustules. VPD at IRGA time uses T = Tmin + 0.8(Tmax − Tmin) and RH = RH II + 0.3(RH I − RH II), from the 7 days before the assessment.")],
  [run("Range ", { bold: true }), run("min and max of X at the lower and upper DI of the class, widened by (1 ∓ 1.645 × CV), giving about a 90% interval.")],
  [run("Thermal ", { bold: true }), run("CWSI = 1 − (1 − CWSI_healthy) × E_diseased/E_healthy; Tc = Twet + CWSI(Tdry − Twet); Twet = Ta + 1.0 − 1.9 VPD; Tdry = Ta + 4 °C. Flight-time Ta and VPD use T = Tmin + 0.9(Tmax − Tmin), RH = RH II + 0.15(RH I − RH II). Healthy CWSI: V 0.12, F 0.20, P 0.30, + 0.05 h.")],
].forEach((r) => C.push(bullet(r)));

C.push(h2("3.2 Parameter baselines and severity-response coefficients"));
const prow = [["Parameter", "Unit / method", "Healthy ref. (range)", "CV", "Stage factor V/F/P", "Var. factor V1/V2/V3", "Response", "Rmax, k (c, sc)", "Evidence"]];
D.params.forEach((p) => prow.push([
  NAME[p.Code], [UNIT[p.Code], p.Method], p["Reference healthy value"] ? `${p["Reference healthy value"]} (${p["Ref range low"]}-${p["Ref range high"]})` : `derived (${p["Ref range low"]}-${p["Ref range high"]})`, f(p.CV, 2),
  `${p["Stage factor V (3rd leaf)"]} / ${p["Stage factor F (5th leaf)"]} / ${p["Stage factor P (5th leaf)"]}`,
  `${p["Variety factor V1"]} / ${p["Variety factor V2"]} / ${p["Variety factor V3"]}`,
  `${p["Response type"]} (${p.Sign > 0 ? "increase" : "decrease"})`,
  p["Response type"] === "logistic" ? `${p.Rmax}; c ${p["Logistic centre"]}, sc ${p["Logistic scale"]}` : p["Response type"] === "hump" ? `${p.Rmax}, ${p.k}; A ${p["Hump amplitude"]}, peak ${p["Hump peak s"]}` : `${p.Rmax}, ${p.k}`,
  p["Evidence level"],
]));
C.push(table(scale([1.6, 2.4, 1.3, 0.5, 1.1, 1.1, 1.1, 1.3, 1.1]), prow, { size: 15, size2: 13 }));
C.push(caption("Evidence levels: E1 direct white-rust data on B. juncea; E2 A. candida on another host (Arabidopsis); E3 other Brassica or foliar pathogen, including your similar-experiment slides; E4 mechanism or abiotic analogue only. µg mg⁻¹ FW is numerically identical to mg g⁻¹ FW."));

C.push(h2("3.3 Basis of each parameter"));
D.params.forEach((p) => C.push(bullet([run(NAME[p.Code] + ": ", { bold: true }), run(p["Basis / sources"])])));
C.push(h3("Key mechanistic anchors from the white-rust literature"));
[
  "Chou et al. (2000), A. candida on Arabidopsis: no change at 6 DAI. Pn declines from 8 DAI as sporulation begins on the abaxial surface, while transpiration is still unchanged at 8 DAI. Chlorophyll is stable to 12 DAI, then 40% of control at 14 DAI; whole-leaf photosynthesis is 30% of control at 14 DAI. Fv/Fm is unchanged and no defence genes are induced in the compatible interaction. This defines the lesion-age factor and the order of change: gas exchange first, pigments later, PSII efficiency barely.",
  "Mishra et al. (2009), B. juncea: total protein 4-10% lower in inoculated leaves, and susceptible genotypes have higher constitutive protein. Hence the protein decline is modest (Rmax 0.15), and V2 has a higher healthy protein factor (1.08) than V3 (1.00).",
  "Pandey et al. (2013): incubation 4-9 d, latent period 9-12 d; the Delhi isolate is the least virulent, with small pustules. This supports little visible disease from the 05/02 inoculation by 11/02.",
  "Rai et al. (2024): the resistant line keeps higher chlorophyll and carotenoids; carotenoids rise early in the susceptible line. This gives the carotenoid hump response.",
  "Your similar-experiment slides (HR/MR/MS/S classes) give magnitude anchors for Pn, gs, E, Ci and MSI. Their data-integrity issues (duplicated seasons, tables not matching the bars) mean they were used only for magnitudes, not as exact targets.",
].forEach((t) => C.push(bullet(t)));

C.push(h2("3.4 Severity classes"));
C.push(table(scale([2, 1.5, 1, 1, 1, 4]), [
  ["Class", "DI range (%)", "s low", "s mid (mean)", "s high", "Comment"],
  ["Healthy", "0", "0", "0", "0", "Uninoculated control replication, same sowing date and variety"],
  ["Very low", "1-5", "0.01", "0.03", "0.05", "Few pustules; physiological change mainly in gas exchange"],
  ["Low", "6-10", "0.06", "0.08", "0.10", ""],
  ["Moderate", "11-25", "0.11", "0.18", "0.25", "Thresholds of RWC/MSI decline begin (logistic centre ~0.28-0.35)"],
  ["High", "26-50", "0.26", "0.38", "0.50", "Epidermal rupture over large areas; chlorosis"],
  ["Very high", ">50", "0.51", "0.65", "0.85", "Upper limit capped at 85%: leaves beyond that are usually shed (Bal & Kumar 2014)"],
], { fillFn: (ri, ci) => (ci === 0 && ri > 0 ? CLASS_FILL[CLASSES[ri - 1]] : undefined) }));

// 4. Stage comparison
C.push(h1("4. Main result: healthy vs each severity class at each growth stage"));
C.push(para("The tables below pool all treatment × date combinations observed at the same stage, so each stage is compared on the leaf you actually sample (3rd leaf at V, 5th leaf at F and P). Values are means over the pooled combinations; ranges are the pooled minimum and maximum of the class range. Use Section 5 or Appendix A when you need a particular treatment and date.", { align: AlignmentType.JUSTIFIED }));
const stageCount = { V: 0, F: 0, P: 0 }; D.ctx.forEach((c) => stageCount[c["Stage (obs.)"]]++);
const stageNote = {
  V: "Vegetative records: 11/02 (all treatments except D1V1, which was already flowering) and 24/02 (D3 and D4 sowings). Disease is young (6 and 19 DAI): gas exchange changes first; pigment, RWC and MSI changes stay small except at High/Very high severities.",
  F: "Flowering records span all four dates. Healthy Pn, gs and RWC fall towards March because of heat and VPD, while E rises with VPD; the disease effect is measured against that moving healthy baseline.",
  P: "Pod-formation records (03/03 and 13/03, early sowings) come from the oldest 5th leaves, under the hottest and driest conditions. Healthy values are lowest here and leaf senescence adds to disease-driven chlorophyll and protein loss.",
};
["V", "F", "P"].forEach((st, si) => {
  const rows = D.stage[st];
  C.push(h2(`4.${si + 1} ${STAGE_NAME[st]}`, si > 0));
  C.push(para(`${stageCount[st]} treatment × date combinations at this stage. ${stageNote[st]}`, { size: 18 }));
  const hdr = ["Parameter (unit)"].concat(CLASSES.map((c) => `${c} (${DI[c]}%)`));
  const t = [hdr];
  PC.forEach((pc) => {
    const r = [[NAME[pc], UNIT[pc]]];
    rows.forEach((x) => r.push([f(x[pc], DEC[pc]), `${f(x[pc + "_lo"], DEC[pc])}-${f(x[pc + "_hi"], DEC[pc])}${x.class === "Healthy" ? "" : "  (" + pct(x[pc + "_pct"]) + ")"}`]));
    t.push(r);
  });
  // derived pigments
  const tot = rows.map((x) => x.ChlA + x.ChlB);
  t.push([["Total chlorophyll (a+b)", "µg mg⁻¹ FW"]].concat(rows.map((x, i) => [f(tot[i], 3), i === 0 ? "" : "(" + pct((tot[i] / tot[0] - 1) * 100) + ")"])));
  t.push([["Chl a/b ratio", "-"]].concat(rows.map((x) => [f(x.ChlA / x.ChlB, 2), ""])));
  t.push([["Carotenoid / total chl", "-"]].concat(rows.map((x, i) => [f(x.Car / tot[i], 3), ""])));
  t.push([["WUE = Pn/E", "µmol mmol⁻¹"]].concat(rows.map((x, i) => [f(x.Pn / x.E, 2), i === 0 ? "" : "(" + pct(((x.Pn / x.E) / (rows[0].Pn / rows[0].E) - 1) * 100) + ")"])));
  t.push([["Canopy temperature Tc", "°C"]].concat(rows.map((x) => [f(x["Tc (C)"], 2), x.class === "Healthy" ? "" : "ΔTc +" + f(x["dTc vs healthy (C)"], 2)])));
  t.push([["CTD = Tc − Ta", "°C"]].concat(rows.map((x) => [f(x["CTD = Tc - Ta (C)"], 2), ""])));
  t.push([["CWSI", "0-1"]].concat(rows.map((x) => [f(x.CWSI, 3), ""])));
  t.push([["Ig (stomatal index)", "-"]].concat(rows.map((x) => [f(x["IG = (Tdry-Tc)/(Tc-Twet)"], 2), ""])));
  t.push([["Within-plot Tc SD", "°C"]].concat(rows.map((x) => [f(x["Tc SD within plot (C)"], 2), ""])));
  C.push(table(scale([2.2, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3]), t, { size: 16, size2: 13, fillFn: colClassFill }));
  C.push(caption(`Top line: expected mean. Second line: plausible range (≈90%) and % change vs healthy at the same stage. Thermal values are pooled over the dates of this stage; see Section 6 for date-wise values.`));
  // % change summary
  C.push(h3(`Percentage change vs healthy at ${st === "V" ? "vegetative" : st === "F" ? "flowering" : "pod formation"} stage`));
  const t2 = [["Parameter"].concat(CLASSES.slice(1).map((c) => `${c} (${DI[c]}%)`))];
  PC.forEach((pc) => t2.push([NAME[pc]].concat(rows.slice(1).map((x) => pct(x[pc + "_pct"])))));
  C.push(table(scale([2.6, 1.3, 1.3, 1.3, 1.3, 1.3]), t2, { size: 16, fillFn: (ri, ci) => (ci >= 1 ? CLASS_FILL[CLASSES[ci]] : undefined) }));
});

C.push(h2("4.4 Interpretation: what separates healthy from each severity class", true));
const F_ = D.stage.F, V_ = D.stage.V, P_ = D.stage.P;
[
  `Very low and Low (1-10% DI): differences from healthy are mainly in gas exchange. At flowering Pn is ${pct(F_[1].Pn_pct)} and ${pct(F_[2].Pn_pct)}, gs ${pct(F_[1].gs_pct)} and ${pct(F_[2].gs_pct)}, and Ci rises (${pct(F_[1].Ci_pct)}, ${pct(F_[2].Ci_pct)}), which indicates non-stomatal limitation of photosynthesis. RWC and MSI change by less than about 5%, which is within assay error; do not expect significant differences in these two at low severity.`,
  `Moderate (11-25% DI): this is the first class where pigments separate clearly (Chl a at flowering ${pct(F_[3].ChlA_pct)}, total chlorophyll and carotenoids lower). The MSI decline begins (${pct(F_[3].MSI_pct)}). Canopy warming of about ${f(F_[3]["dTc vs healthy (C)"], 1)} °C over healthy at flowering is at the limit of reliable UAV thermal detection (±0.5 °C after calibration).`,
  `High (26-50% DI): RWC and MSI pass their thresholds (flowering RWC ${pct(F_[4].RWC_pct)}, MSI ${pct(F_[4].MSI_pct)}). Pn is roughly halved (${pct(F_[4].Pn_pct)}), anthocyanin rises (${pct(F_[4].Anth_pct)}) and LAI falls through leaf shedding (${pct(F_[4].LAI_pct)}). Canopy is ${f(F_[4]["dTc vs healthy (C)"], 1)} °C warmer than healthy, so thermal separation is reliable.`,
  `Very high (>50% DI): flowering RWC ${pct(F_[5].RWC_pct)}, MSI ${pct(F_[5].MSI_pct)}, Pn ${pct(F_[5].Pn_pct)}, gs ${pct(F_[5].gs_pct)}, E ${pct(F_[5].E_pct)}, Ci ${pct(F_[5].Ci_pct)}, LAI ${pct(F_[5].LAI_pct)}, Chl a ${pct(F_[5].ChlA_pct)}, Chl b ${pct(F_[5].ChlB_pct)}, carotenoids ${pct(F_[5].Car_pct)}, anthocyanin ${pct(F_[5].Anth_pct)}, protein ${pct(F_[5].Prot_pct)}. Chl a falls faster than Chl b, so the a/b ratio drops, and carotenoid/chlorophyll rises; both are good ratio-based indicators.`,
  `Stage effect: for the same DI, the % change is smaller at the vegetative stage (e.g. Very high Pn ${pct(V_[5].Pn_pct)} at V vs ${pct(F_[5].Pn_pct)} at F). V records are mainly from 11/02, only 6 DAI, when lesions are young (lesion-age factor). At pod formation (Pn ${pct(P_[5].Pn_pct)}) disease adds to senescence and heat, so absolute values are the lowest of the season even in healthy plants.`,
  "Variety effect: V2 (Pusa Vijay) has the largest response per unit DI (tolerance 1.10) and V3 the smallest (0.85). V2 also starts from slightly higher protein and chlorophyll, as expected from Mishra et al. (2009) for susceptible genotypes. The V3 reaction is an assumption until you confirm it.",
  "Sowing-date effect: later sowings (D3, D4) have smaller healthy LAI, more anthocyanin from cold legacy, and are still vegetative on 11/02. Early sowings (D1, D2) reach pod formation in March under heat, which lowers healthy Pn, gs and RWC. Always compare a diseased plot with the healthy plot of the same sowing date and variety (your control replication) rather than with a pooled healthy mean.",
  "Most robust discriminators of healthy vs diseased, in order of expected effect size: Pn, MSI (at Moderate and above), gs, Chl a and total chlorophyll, Ci (increase), canopy ΔTc/CWSI, LAI, RWC (only at High and above), anthocyanin, and protein (smallest change).",
].forEach((t) => C.push(bullet(t)));

// 5. Stage x date
C.push(h1("5. Healthy vs severity by stage and assessment date"));
C.push(para("Same comparison as Section 4, but separated by assessment date within each stage. This shows how the healthy baseline and the disease effect shift as the crop ages and the weather warms. Each cell gives the mean and, below it, the % change vs healthy.", { align: AlignmentType.JUSTIFIED }));
D.stage_date.forEach((b, bi) => {
  C.push(h2(`5.${bi + 1} ${STAGE_NAME[b.stage].split(" (")[0]} stage, ${b.date}`, bi > 0));
  C.push(para(`Treatments at this stage on this date: ${b.treatments.join(", ")} (n = ${b.treatments.length}).`, { size: 18 }));
  const t = [["Parameter (unit)"].concat(CLASSES.map((c) => `${c} (${DI[c]}%)`))];
  PC.forEach((pc) => t.push([[NAME[pc], UNIT[pc]]].concat(b.rows.map((x) => [f(x[pc], DEC[pc]), x.class === "Healthy" ? "" : pct(x[pc + "_pct"])]))));
  C.push(table(scale([2.2, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3]), t, { size: 16, size2: 13, fillFn: colClassFill }));
});

// 6. Thermal
C.push(h1("6. Thermal parameters"));
C.push(h2("6.1 Thermal parameters to extract (UAV FLIR Vue Pro R and handheld)"));
const thDefs = [
  ["Parameter", "Formula", "Unit", "Expected change with white rust", "Notes for IARI, Feb-Mar 2026"],
  ["Canopy temperature Tc", "Mean of canopy pixels after soil/shadow masking (K-means or NDVI mask)", "°C", "Increases (less transpirational cooling)", "Fly 11:00-14:00 under clear sky; log Ta and RH at flight time"],
  ["Canopy temperature depression CTD", "Tc − Ta (your ORW definition; many papers use Ta − Tc)", "°C", "Less negative / becomes positive", "State the sign convention explicitly in the thesis"],
  ["Canopy temperature ratio CTR", "Tc / Ta", "-", "Increases", "Use K if comparing dates with very different Ta"],
  ["Normalised relative canopy temperature NRCT", "(Tc − Tc,min) / (Tc,max − Tc,min) within a flight", "0-1", "Increases", "Computed across all 48 plots of one flight"],
  ["Crop water stress index CWSI", "(Tc − Twet) / (Tdry − Twet); Twet = Ta + a − b·VPD; Tdry = Ta + 3-5 °C", "0-1", "Increases", "Wet and dry reference surfaces improve it"],
  ["Stomatal conductance index Ig", "(Tdry − Tc) / (Tc − Twet)", "-", "Decreases (∝ gs)", "Validate against LI-6400 gs on the same plots"],
  ["Index I3", "(Tc − Twet) / (Tdry − Tc)", "-", "Increases (∝ 1/gs)", ""],
  ["Within-plot Tc SD", "SD of canopy pixels", "°C", "Increases (patchy lesions)", "Depends on pixel size (≈2 cm at 30 m)"],
  ["Maximum temperature difference MTD", "P95 − P5 (or max − min) of canopy pixels", "°C", "Increases", ""],
  ["Thermal percentiles", "P10, P50, P90 of canopy Tc", "°C", "Upper percentiles rise first", "Percentile features as in Liu et al. 2024"],
  ["Thermal GLCM texture", "Contrast, homogeneity, entropy, ASM, correlation, dissimilarity (0/45/90/135°, d = 1-5 px)", "-", "Contrast and entropy up; homogeneity and ASM down", "As in your ORW slide 21"],
  ["Tc − Tc(healthy) (ΔTc)", "Tc of diseased plot − Tc of healthy plot, same sowing × variety, same flight", "°C", "Increases with DI", "Best single thermal disease feature in your design"],
];
C.push(table(scale([2, 3, 0.6, 1.8, 2.6]), thDefs, { size: 15, align: AlignmentType.LEFT, boldFirstCol: true }));
C.push(h3("Caveats specific to white rust and your conditions"));
[
  "Pustules form on the lower (abaxial) leaf surface, while a nadir camera sees the upper surface. No thermal change is expected before 8-11 DAI (Chou et al. 2000: transpiration unchanged at 8 DAI while photosynthesis had already fallen).",
  "White pustules may change surface emissivity, and rupture can raise cuticular water loss and partly offset warming. The model includes the second effect through the (1 + 0.25 s) term in E.",
  "At flowering, yellow petals dominate the canopy view and are warmer than leaves. Mask flowers or compare only within a stage.",
  "Late-season heat (Tmax 30-35 °C from 28 February) and VPD of 2-3 kPa raise Tc of healthy plots as well. Always reference a diseased plot to the healthy plot of the same variety and sowing date in the same flight.",
].forEach((t) => C.push(bullet(t)));
C.push(h2("6.2 Simulated thermal values by assessment date and severity class (pooled over treatments)", true));
const th = [["Date", "Class", "Ta (°C)", "Twet (°C)", "Tdry (°C)", "Tc mean (°C)", "Tc range (°C)", "CTD = Tc−Ta (°C)", "ΔTc vs healthy (°C)", "CTR", "CWSI", "Ig", "Tc SD (°C)", "MTD proxy (°C)"]];
D.thermal.forEach((x) => th.push([x.date.slice(0, 5), x.class, f(x.Ta, 1), f(x.Twet, 1), f(x.Tdry, 1), f(x.Tc, 2), `${f(x.Tclo, 1)}-${f(x.Tchi, 1)}`, f(x.CTD, 2), f(x.dTc, 2), f(x.CTR, 3), f(x.CWSI, 3), f(x.IG, 2), f(x.SD, 2), f(x.MTD, 2)]));
C.push(table(scale([0.8, 1.1, 0.8, 0.8, 0.8, 0.9, 1.1, 1, 1, 0.8, 0.8, 0.8, 0.8, 0.9]), th, { size: 15, fillFn: (ri, ci) => (ci === 1 && ri > 0 ? CLASS_FILL[th[ri][1]] : undefined) }));
C.push(caption("Flight-time Ta and VPD were estimated from daily Tmax/Tmin/RH; replace them with your logged values. Tc SD = 0.6 + 2.0 s; the MTD proxy is 3.29 × SD (P95 − P5 of a normal distribution). Treatment-wise Tc, CTD, ΔTc and CWSI are in Appendix A and in the Simulation sheet of the workbook."));

// 7. Texture
C.push(h1("7. RGB textural (GLCM) and colour parameters"));
C.push(para("Absolute GLCM values depend on grey-level quantisation, window size, pixel offset and ground sampling distance, so only relative change vs healthy is given. Compute the features on the green or grey channel of the colour-calibrated image, inside a canopy mask, with the same settings on every date. Leaf-level values assume the abaxial (lower) surface photographed at fixed exposure with a colour card; canopy values assume a nadir UAV view of the upper surface.", { align: AlignmentType.JUSTIFIED }));
C.push(h2("7.1 Features, definitions and expected behaviour"));
const txDefs = [["Feature", "Group", "Definition", "Expected change", "Rmax leaf / canopy", "Rationale"],
  ["GLCM mean", "GLCM", "Σ i·P(i,j)", "Increase", "0.35 / 0.08", "White pustules brighten the abaxial surface; slight canopy yellowing"],
  ["GLCM variance", "GLCM", "Σ (i − μ)²·P(i,j)", "Increase", "1.20 / 0.25", "Bright pustules on green tissue"],
  ["GLCM contrast", "GLCM", "Σ (i − j)²·P(i,j)", "Increase", "2.50 / 0.30", "Local grey-level jumps at pustule edges"],
  ["GLCM dissimilarity", "GLCM", "Σ |i − j|·P(i,j)", "Increase", "1.20 / 0.18", "As contrast, linear weighting"],
  ["GLCM homogeneity", "GLCM", "Σ P(i,j)/(1 + (i − j)²)", "Decrease", "0.30 / 0.08", "Uniform healthy lamina becomes patchy"],
  ["GLCM entropy", "GLCM", "−Σ P(i,j)·log P(i,j)", "Increase", "0.22 / 0.06", "More grey-level randomness"],
  ["GLCM angular second moment (ASM)", "GLCM", "Σ P(i,j)²", "Decrease", "0.55 / 0.15", "Less uniformity"],
  ["GLCM correlation", "GLCM", "Σ (i − μi)(j − μj)P(i,j)/(σi σj)", "Decrease", "0.20 / 0.05", "Random pustule pattern breaks linear structure"],
  ["NGRDI", "Colour", "(G − R)/(G + R)", "Decrease", "0.60 / 0.45", "Chlorosis lowers green relative to red"],
  ["ExG", "Colour", "2g − r − b (chromatic coordinates)", "Decrease", "0.50 / 0.40", "Loss of greenness"],
  ["VARI", "Colour", "(G − R)/(G + R − B)", "Decrease", "0.60 / 0.50", "Loss of greenness"],
  ["GLI", "Colour", "(2G − R − B)/(2G + R + B)", "Decrease", "0.50 / 0.40", "Loss of greenness"],
  ["RGRI", "Colour", "R / G", "Increase", "0.40 / 0.25", "Yellowing"],
  ["Brightness / whiteness", "Colour", "(R + G + B)/3 or HSV value; white-pixel fraction", "Increase", "0.40 / 0.05", "Pustule area fraction: the best objective leaf-level severity proxy"],
];
C.push(table(scale([2, 0.8, 2.4, 1, 1.2, 3.2]), txDefs, { size: 15, align: AlignmentType.LEFT, boldFirstCol: true }));
C.push(caption("Change = sign × Rmax × (1 − e^−3s) × stage damping. Canopy damping V 1.0, F 0.6 (yellow petals mask leaves), P 0.8. Additional useful features: HSV/Lab channel statistics (a*, hue), local binary pattern (LBP) histograms, Gabor energy and the white-pustule area fraction from a threshold or segmentation model."));
D.texture.forEach((b, bi) => {
  C.push(h2(`7.${bi + 2} Expected % change vs healthy: ${b.title.charAt(0) + b.title.slice(1).toLowerCase().replace("uav", "UAV")}`, bi === 0));
  const short = ["Class", "Mean", "Var.", "Contr.", "Dissim.", "Homog.", "Entropy", "ASM", "Corr.", "NGRDI", "ExG", "VARI", "GLI", "RGRI", "Bright."];
  const t = [short];
  b.rows.forEach((r) => t.push([r[0]].concat(r.slice(1).map((v) => pct(v)))));
  C.push(table(scale([1.4].concat(Array(14).fill(1))), t, { size: 15, fillFn: (ri, ci) => (ci === 0 && ri > 0 ? CLASS_FILL[t[ri][0]] : undefined) }));
  C.push(caption("Mean, Var., Contr., Dissim., Homog., Entropy, ASM, Corr. = GLCM features; Bright. = brightness/whiteness. Confidence is LOW: no published white-rust GLCM values exist for mustard; magnitudes are scaled from pustule and chlorosis mechanisms and analogous foliar diseases."));
});

// 8. Plausibility
C.push(h1("8. Which severity classes are realistic on each date?"));
C.push(para("Values are given for every class at every date so the comparison is always possible. Under your 2025-26 weather and timing, however, some classes are unlikely. The table shows the expected DI scenario and the plausibility of the classes above Low. If your field data contain a class marked Unlikely, check whether it came from pre-inoculation natural infection (likely in D1 and D2) or from a rating-scale issue.", { align: AlignmentType.JUSTIFIED }));
const pl = [["Treatment", "11/02 (6 DAI)", "24/02 (19 DAI)", "03/03 (26 DAI)", "13/03 (36 DAI)"]];
const byT = {}; D.td.forEach((x) => { (byT[x.t] = byT[x.t] || {})[x.date] = x; });
Object.keys(byT).forEach((t) => {
  const r = [t];
  ["11/02/2026", "24/02/2026", "03/03/2026", "13/03/2026"].forEach((d) => {
    const x = byT[t][d];
    const ok = x.rows.filter((rr) => rr.class !== "Healthy" && /^Likely|^Possible|^Expected/.test(rr.plaus)).map((rr) => rr.class);
    r.push([`DI ${f(x.expDI, 1)}% (${x.expClass}), ${x.stage}`, ok.length ? "Plausible: " + ok.join(", ") : "Plausible: none"]);
  });
  pl.push(r);
});
C.push(table(scale([1, 2.2, 2.2, 2.2, 2.2]), pl, { size: 15, size2: 13 }));
const plausLabels = [...new Set(D.td.flatMap((x) => x.rows.map((r) => r.plaus)))];
C.push(caption("Plausibility labels used in the workbook: " + plausLabels.join("; ") + "."));

// 9. Limitations
C.push(h1("9. Limitations and correct use"));
[
  "These are simulated expectations, not data. Only chlorophyll, carotenoids and total protein have direct white-rust measurements in B. juncea. The RWC, MSI, Pn, E, gs, LAI and anthocyanin responses are built from mechanism, Arabidopsis-A. candida data, your similar-experiment slides and analogous Brassica foliar diseases (evidence levels in Section 3.2).",
  "Effect sizes assume the sampled leaf carries the plot-mean DI. In practice leaf-level severity of the 3rd or 5th leaf can differ from plot DI. Record leaf-level severity (% area with pustules) of the sampled leaf so you can regress parameters on leaf severity as well as plot DI.",
  "V3 (Pusa Mustard 37) resistance is unverified in the literature you supplied. Its tolerance (0.85) and lower expected DI should be updated after your 2025-26 data.",
  "On 11/02 (6 DAI), any visible disease almost certainly comes from natural infection during 18 December - 4 February, not from the 05/02 inoculation. Interpret that date as 'natural infection + very early inoculation response'.",
  "Fresh-weight basis: chlorophyll, carotenoid, anthocyanin and protein per unit FW are inflated when diseased leaves lose water. Report RWC alongside, or also express pigments per unit area or dry weight.",
  "The ±1.645 CV allowance assumes typical assay CVs (4-50%; anthocyanin highest). Your own replication CVs should replace them in Inputs/Parameters once available.",
  "Thermal and texture values depend on sensor calibration, flight time, altitude, flower masking and image processing; treat them as directions and relative magnitudes.",
  "Correct citation in the thesis: 'expected values were derived from a literature- and weather-based simulation (this study, Appendix X)'. Do not mix these numbers with measured data in tables or statistical tests.",
].forEach((t) => C.push(bullet(t)));
C.push(h3("Suggested analyses with your real data"));
[
  "Two-way comparisons at each stage: healthy control vs each DI class (Dunnett's test with healthy as control), or a mixed model: parameter ~ DI class × stage + variety + sowing date + (1|replication).",
  "Regression of each parameter on continuous DI (or leaf severity) within stage; compare the fitted slope with the simulated response curves in the Response_Table sheet.",
  "Add Ci, Chl a/b, carotenoid/chlorophyll, WUE and ΔTc as derived features. Lag weather by 7-14 days for epidemiological models; use AUDPC over the four dates.",
  "For machine learning: train on the healthy-vs-class contrasts within the same flight and stage, and use leave-one-sowing-date-out validation to avoid date leakage.",
].forEach((t) => C.push(bullet(t)));

// 10. References
C.push(h1("10. References and data sources"));
[
  "Chattopadhyay C. et al. (2011) Epidemiology and development of forecasting models for white rust of Brassica juncea in India. Archives of Phytopathology and Plant Protection 44(8): 751-763. https://doi.org/10.1080/03235400903458571",
  "Chou H.-M. et al. (2000) Infection of Arabidopsis thaliana leaves with Albugo candida (white blister rust) causes a reprogramming of host metabolism. Molecular Plant Pathology 1(2): 99-113. https://doi.org/10.1046/j.1364-3703.2000.00013.x",
  "Mishra K.K., Kolte S.J., Nashaat N.I., Awasthi R.P. (2009) Pathological and biochemical changes in Brassica juncea (mustard) infected with Albugo candida (white rust). Plant Pathology 58: 80-86. https://doi.org/10.1111/j.1365-3059.2008.01939.x",
  "Pandey P., Tewari A.K., Awasthi R.P. (2013) Morphological and pathogenic variability of Albugo candida isolates. The Bioscan 8(3): 835-838 (user-supplied PDF).",
  "Rai P. et al. (2024) Transcriptional, biochemical and histochemical response of resistant and susceptible Brassica juncea to Albugo candida. Frontiers in Plant Science 15: 1426302. https://doi.org/10.3389/fpls.2024.1426302",
  "Shrivastava A. et al. (2023) Screening of Indian mustard genotypes against white rust based on disease indexing. Biological Forum - An International Journal 15(4) (user-supplied PDF).",
  "Singh M. et al. (2024) Multivariate analysis of the effects of weather variables on white rust epidemics. Plant Pathology 73: 791-809. https://doi.org/10.1111/ppa.13851",
  "Rana R.S. et al. (2017) Forecasting phenology of mustard crop in North-western Himalayas. Journal of Applied and Natural Science 9(1): 230-236 (user-supplied PDF).",
  "Bal R.S., Kumar A. (2014) Studies on the epidemiology of white rust and Alternaria leaf blight and their effect on the yield of Indian mustard. African Journal of Agricultural Research 9(2): 302-306. https://doi.org/10.5897/AJAR2013.7352",
  "Ram L., Awasthi R.P. (2018) Comparative assessment of white rust disease in improved varieties of Indian mustard. International Journal of Current Microbiology and Applied Sciences 7(5): 1431-1438. https://doi.org/10.20546/ijcmas.2018.705.170",
  "Influence of sowing time, varieties and salicylic acid application on physiological parameters of Indian mustard (Jobner). https://www.microbiologyjournal.org/influence-of-sowing-time-varieties-and-salicylic-acid-application-on-different-physiological-parameters-of-indian-mustard-brassica-juncea-l/",
  "Potassium fertilizer effects on growth, physiology and water status of Brassica juncea cultivars. PLOS ONE (2021). https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0257023",
  "The photosynthetic characteristics of leaves in different-coloured Brassica juncea. Plants 14(20): 3197 (2025). https://doi.org/10.3390/plants14203197",
  "Chlorophyll content of B. juncea mutants. Journal of Pharmacognosy and Phytochemistry (2019). https://phytojournal.com/archives/2019/vol8issue3/PartAB/8-2-592-868.pdf",
  "Anthocyanins in purple vs green B. juncea leaves (PMC4992693, Table 1). https://pmc.ncbi.nlm.nih.gov/articles/PMC4992693/",
  "Tripathi S.K. et al. (2020) Canopy temperature depression in late-sown Indian mustard, Kanpur. IJCMAS 9(1). https://www.ijcmas.com/",
  "Remote sensing of physiological depression with thermal imagery. JARQ 25(1), JIRCAS. https://www.jircas.go.jp/en/publication/jarq/25/1/1",
  "Jain G., Sandhu S.K. Mustard under different dates of sowing (PAU). Journal of Pharmacognosy and Phytochemistry (2018). https://phytojournal.com/archives/2018/vol7issue3/PartAI/7-3-493-188.pdf",
  "Macioszek V.K. et al. (2021) Leaf-level physiological and biochemical responses of Brassica to Alternaria brassicicola. https://pmc.ncbi.nlm.nih.gov/articles/PMC8395102/",
  "Mahlein A.-K. (2016) Plant disease detection by imaging sensors. Plant Disease 100: 241-251; and Mahlein et al. (2019) https://pmc.ncbi.nlm.nih.gov/articles/PMC6567885/",
  "Abdulridha J. et al. (2023) UAV-based hyperspectral and thermal detection of plant disease. https://pmc.ncbi.nlm.nih.gov/articles/PMC10141366/",
  "Methods: Barrs H.D., Weatherley P.E. (1962) RWC; Sairam R.K. (1994) MSI; Wellburn A.R. (1994) DMSO pigment equations; Lee J., Durst R.W., Wrolstad R.E. (2005) pH-differential anthocyanin; Bradford M.M. (1976) protein; Haralick R.M. et al. (1973) GLCM; Idso S.B. et al. (1981) and Jackson R.D. et al. (1981) CWSI.",
  "IARI Agromet Observatory daily weather 31/10/2025-06/04/2026 (user-supplied file).",
  "Unpublished similar-experiment slides (HR/MR/MS/S classes, user-supplied): magnitude anchors only.",
].forEach((t) => C.push(num(t)));

// Appendix A
C.push(h1("Appendix A. Treatment × date tables (12 treatments × 4 dates × 6 classes)"));
C.push(para("Each table compares the healthy control of that treatment with all six severity classes on that date. Cell: expected mean (top) and plausible range with % change vs healthy (below). The thermal rows give expected mean values at flight time. The plausibility row repeats Section 8.", { align: AlignmentType.JUSTIFIED }));
D.td.forEach((x, i) => {
  C.push(h2(`A.${i + 1} ${x.t} - ${x.date}`, i > 0));
  C.push(para(`DAS ${x.das} | DAI ${x.dai} | GDD from emergence ${f(x.gdd, 0)} | Stage ${x.stage} | Sampled leaf: ${x.leaf} | Heat index h ${f(x.h, 2)} | VPD at IRGA ${f(x.vpd, 2)} kPa | Expected DI ${f(x.expDI, 1)}% (${x.expClass})`, { size: 17 }));
  const t = [["Parameter (unit)"].concat(CLASSES.map((c) => `${c} (${DI[c]}%)`))];
  PC.forEach((pc) => t.push([[NAME[pc], UNIT[pc]]].concat(x.rows.map((r) => {
    const v = r[pc];
    return [f(v[0], DEC[pc]), `${f(v[1], DEC[pc])}-${f(v[2], DEC[pc])}${r.class === "Healthy" ? "" : " (" + pct(v[3]) + ")"}`];
  }))));
  t.push([["Canopy temperature Tc", "°C"]].concat(x.rows.map((r) => [f(r["Tc (C)"], 2), r.class === "Healthy" ? "" : "ΔTc +" + f(r["dTc vs healthy (C)"], 2)])));
  t.push([["CTD = Tc − Ta", "°C"]].concat(x.rows.map((r) => [f(r["CTD = Tc - Ta (C)"], 2), ""])));
  t.push([["CWSI", "0-1"]].concat(x.rows.map((r) => [f(r.CWSI, 3), ""])));
  t.push(["Plausibility"].concat(x.rows.map((r) => r.class === "Healthy" ? "Control" : r.plaus.replace(" (only via pre-inoculation natural infection)", " (natural inf. only)"))));
  C.push(table(scale([2.1, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3]), t, { size: 15, size2: 12, fillFn: colClassFill }));
});

// ---------- document ----------
const doc = new Document({
  features: { updateFields: true },
  creator: "White rust simulation (IARI 2025-26)",
  title: "Simulated parameters of mustard under white rust",
  styles: {
    default: { document: { run: { font: FONT, size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, font: FONT, color: "1F4E79" }, paragraph: { spacing: { before: 120, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, font: FONT, color: "2E75B6" }, paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 21, bold: true, font: FONT, color: "404040" }, paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] },
      { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 500, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: PAGE_H, orientation: PageOrientation.LANDSCAPE }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "SIMULATED / EXPECTED VALUES - NOT MEASURED DATA | White rust of mustard, IARI New Delhi 2025-26 | Page ", font: FONT, size: 15, color: "808080" }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 15, color: "808080" }),
    ] })] }) },
    children: C,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(outPath, b); console.log("wrote", outPath, b.length); });
