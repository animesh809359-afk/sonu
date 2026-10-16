// Detailed Word report of the nine subset analyses (4 dates, 2 growth stages, 3 varieties).
// Input: work_subsets/report/subsets.json and figures (export_subsets_report.py); references from the all-dates conclusions.
const fs = require("fs");
const path = require("path");
const docx = require(process.env.DOCX_MODULE || "docx");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType, ImageRun,
        AlignmentType, LevelFormat, PageBreak, TableOfContents, Footer, PageNumber, BorderStyle } = docx;

const REP = process.argv[2];
const OUT = process.argv[3];
const REFS = JSON.parse(fs.readFileSync(process.argv[4], "utf8")).references;
const J = JSON.parse(fs.readFileSync(path.join(REP, "subsets.json"), "utf8"));
const S = J.subsets, REF = J.ref;
const FIGDIR = J.fig;
const CW = 9638; // A4, 2 cm margins

const pct = (v) => (v == null ? "–" : (100 * v).toFixed(1) + " %");
const p1 = (v) => (v == null ? "–" : (100 * v).toFixed(1));
const num = (v, d = 3) => (v == null ? "–" : Number(v).toFixed(d));
const pv = (p) => (p == null ? "–" : p < 0.001 ? p.toExponential(1) : p.toFixed(3));
const vA = (s, p, sch) => s.vA[`${p}|${sch}`], vC = (s, p, sch) => s.vC[`${p}|${sch}`];
const k5 = (s, g, c, sch = "CV") => { const r = s.k5.find((r) => r[0] === g && r[3] === c && r[4] === sch); return r ? r[5] : null; };
const GN = { G0: "Full raw spectrum", G1: "K1 band reflectance", G2: "K2 continuum removal", G3: "K3 vegetation indices",
             G4: "K4 derivatives + edge parameters", G5: "K1–K4 combined pool", G6: "K4 incl. guard bands (artefact test)", GS: "K-selected 15" };
const PIPES = ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"];
const byGroup = (g) => S.filter((s) => s.group === g);

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
  if (!file) return null;
  const f = path.join(FIGDIR, file);
  if (!fs.existsSync(f)) return null;
  const d = pngSize(f);
  const w = Math.min(widthPx, 620), h = Math.round(d.h * w / d.w);
  figNo += 1;
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, keepNext: true,
    children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width: w, height: h }, altText: { title: file, description: caption, name: file } })] }));
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
const sepWord = (j) => (j >= 1.94 ? "separable (≥ 1.94, Das et al.)" : j >= 1.9 ? "separable (≥ 1.90)" : "below 1.90");
const featName = (n) => String(n).replace(/^D1_(\d+)$/, "D1 $1 nm").replace(/^R(\d+)$/, "R $1 nm");

// ============================================================ derived cross-subset facts
const dates = byGroup("Date"), stages = byGroup("Stage"), vars = byGroup("Variety");
const bestC = (s) => PIPES.map((p) => [p, vC(s, p, "V3").BA]).sort((a, b) => b[1] - a[1])[0];
const bestA = (s) => PIPES.map((p) => [p, vA(s, p, "V3").BA]).sort((a, b) => b[1] - a[1])[0];
const bestK = (s) => ["G1", "G2", "G3", "G4", "G5"].map((g) => [g, k5(s, g, "RF")]).sort((a, b) => b[1] - a[1])[0];
const rng = (arr) => `${p1(Math.min(...arr))}–${p1(Math.max(...arr))} %`;
const gainC = S.map((s) => vC(s, "QDA on RF features", "V3").BA - vA(s, "QDA on CART features", "V3").BA);
const bestOverall = S.map((s) => Math.max(...PIPES.map((p) => vC(s, p, "V3").BA)));
const rangeC = (s) => rng(PIPES.map((p) => vC(s, p, "V3").BA));
const SH = Object.fromEntries(S.map((s) => [s.short, s]));
const wil = (s, cmp) => s.wil_A.find((r) => r.Comparison.startsWith(cmp) && r.Units.startsWith("V3"));
const v5date = S.filter((s) => s.v5_by === "Date").map((s) => vC(s, "RF classifier", "V5").BA);
const v5var = S.filter((s) => s.v5_by !== "Date").map((s) => vC(s, "RF classifier", "V5").BA);

// ============================================================ title page
body.push(new Paragraph({ spacing: { before: 2200, after: 240 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Discrimination of healthy and white-rust-diseased mustard leaves by date, growth stage and variety", bold: true, size: 40, color: "1F3D2B" })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "Nine separate four-tier hierarchical analyses (Das et al., 2020) with imbalance correction, CART versus Random Forest, validation on new plots, disease-sensitive spectral features (K1–K4) and the four-tier analysis of the combined feature pool", size: 26, italics: true })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: "Leaf level · ASD FieldSpec contact probe · 4 dates (11-02, 24-02, 03-03, 13-03-2026) · vegetative and pod-formation stages · varieties V1, V2, V3", size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: "Animesh Panda · Division of Agricultural Physics, ICAR-Indian Agricultural Research Institute, New Delhi", size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Methods, results and interpretation · companion to the nine Excel workbooks (WhiteRust_Subsets)", size: 20, color: "52514E" })] }));
pageBreak();
body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Contents")] }));
body.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }));
body.push(new Paragraph({ children: [new TextRun({ text: "(Right-click → Update field in Word to refresh the page numbers.)", italics: true, size: 18, color: "52514E" })] }));
pageBreak();

// ============================================================ summary
H1("Summary");
P(`Leaf reflectance spectra (350–2500 nm, 1 nm) of healthy and white-rust (_Albugo candida_) diseased mustard leaves were analysed separately for nine subsets: each of the four measurement dates, the vegetative and the pod-formation growth stage (the flowering stage had been analysed before), and each of the three varieties. In every subset the four-tier hierarchical method of Das et al. (2020) was applied — Tier 1 Welch t-test with Benjamini–Hochberg false-discovery rate, Tier 2 CART band selection (rpart, equal priors), Tier 3 Jeffries–Matusita (J–M) separability and Tier 4 quadratic discriminant analysis (QDA, equal priors) — with corrections for the class imbalance (1 : 4.9 to 1 : 5.1 diseased to healthy), multiple testing and pseudo-replication, and repeated with Random Forest (RF) as the Tier-2 selector. Each analysis was validated on new plots (nested plot-grouped cross-validation V3 and 30 % plot hold-out V4) and on an unseen date or variety (V5). Disease-sensitive features (K1 band reflectance, K2 continuum-removed absorption features, K3 31 vegetation indices, K4 first-derivative bands, edge parameters and the red-edge inflection point) were extracted, and the four tiers were applied to their combined pool (Part C, ${S[0].C_nfeat} features).`);
P(`On raw reflectance (Part A) the number of significant bands rose from ${dates[0].n_sig} of 2101 on 11-02-2026 to ${dates[2].n_sig} on 03-03-2026 as symptoms developed, while no band reached significance in the pooled vegetative stage, where the disease effect in the visible changed sign between its two dates and the difference between the dates inflated the within-class variance. CART selected ${Math.min(...S.map((s) => s.cart_bands.length))}–${Math.max(...S.map((s) => s.cart_bands.length))} bands per subset, mainly in the red edge (690–760 nm), the green peak and the SWIR water bands near 1400 and 1880–2000 nm; J–M on CART bands was ${num(Math.min(...S.map((s) => s.jm_c)), 2)}–${num(Math.max(...S.map((s) => s.jm_c)), 2)} and on RF-17 bands ${num(Math.min(...S.map((s) => s.jm_r)), 2)}–${num(Math.max(...S.map((s) => s.jm_r)), 2)}, i.e. below the 1.90 separability threshold except for RF bands on 03-03-2026. QDA with equal priors on CART bands reached a balanced accuracy (BA) of ${rng(S.map((s) => vA(s, "QDA on CART features", "V3").BA))} on new plots (V3).`);
P(`The combined feature pool was clearly better in most subsets: QDA on the 17 RF-selected features reached ${rng(S.map((s) => vC(s, "QDA on RF features", "V3").BA))} (V3), on average ${p1(gainC.reduce((a, b) => a + b, 0) / gainC.length)} points above QDA on CART reflectance bands, and the best pipeline of each subset reached ${rng(bestOverall)}. The RF-selected features were almost all first-derivative bands and continuum-removed water-absorption parameters (970 and 1940 nm), and their J–M exceeded 1.90 in ${S.filter((s) => s.C_jm_r >= 1.9).length} of 9 subsets. Discrimination was best on single dates (24-02-2026: ${rangeC(SH["Date 24-02-2026"])}; 03-03-2026: ${rangeC(SH["Date 03-03-2026"])} across the four pipelines) and in the vegetative stage (${rangeC(SH["Vegetative"])}), and weakest at pod formation (${rangeC(SH["Pod formation"])}) and on 13-03-2026 (${rangeC(SH["Date 13-03-2026"])}), when senescence makes healthy leaves resemble diseased ones. Within a date, features chosen on two varieties transferred well to the third (V5 ${rng(v5var)} for the RF classifier on the combined pool), but models transferred poorly to an unseen date (V5 ${rng(v5date)}). White rust can therefore be detected reliably from leaf spectra within a date or growth stage with derivative and continuum-removed features, but a practical model needs calibration data from the date or stage to which it is applied.`);

// ============================================================ 1 introduction
H1("1. Introduction");
P("An earlier analysis pooled all four dates, three growth stages and three varieties (2264 leaves) and obtained balanced accuracies of 72 % with the four-tier method on reflectance and 84 % on the combined feature pool, but transfer to an unseen date was poor (53–62 %): the date and growth stage changed the spectra more than the disease did. Pooling therefore mixes the disease signal with phenological variation. This report repeats the complete analysis separately for each date, for the vegetative and the pod-formation growth stage and for each variety, to answer four questions:");
B(["Which wavelengths and features discriminate healthy and white-rust-diseased leaves on each date, in each growth stage and in each variety, and how does the disease signal develop over the season?",
   "How separable are the classes (J–M) and how accurately can they be classified (QDA, CART, RF) within each subset, on new plots?",
   "Is Random Forest a better band selector and classifier than CART in every subset, and do the disease-sensitive features (K1–K4) and their combined pool beat raw reflectance consistently?",
   "Do models transfer to an unseen variety (within a date) or to an unseen date (within a stage or variety)?"]);
P("Each subset has its own Excel workbook (39 sheets) with every table, figure and cross-check; this report collects the results, explains the methods and compares the nine subsets.");

// ============================================================ 2 methods
pageBreak();
H1("2. Materials and methods");
H2("2.1 Data and the nine subsets");
P("Leaf reflectance was recorded with an ASD FieldSpec spectroradiometer and contact probe (350–2500 nm, 1 nm interval) in 48 plots: 12 healthy control plots (plots 1–12) and 36 inoculated plots (13–48), 16 plots per variety (4 healthy, 12 inoculated). The four date files were cleaned once for all subsets: plot-average (=AVERAGE) columns were ignored (leaf level only); 75 spectra of a second data block on 13-03-2026 that repeated plots 13, 34, 38, 41 and 42 exactly, and four unnamed spectra of plot 27 on 11-02-2026 identical to Mustard00215–00218, were removed. Leaf position and disease score were not used: the response is healthy vs diseased. The subset filter was applied after this cleaning, so every subset contains only unique spectra.");
table([["Subset", "Leaves (H / D)", "Ratio D : H", "Plots (H / D)", "Dates", "Growth stages", "Varieties"],
  ...S.map((s) => [s.short, `${s.n} (${s.nH} / ${s.nD})`, `${(s.nD / s.nH).toFixed(1)}`, `${s.pH} / ${s.pD}`, s.dates.join(", "), s.stages.join(", "), s.varieties.join(", ")])],
  "The nine subsets (H = healthy, D = diseased). The flowering stage was analysed in an earlier workbook and is not repeated here.", [2.2, 1.6, 0.9, 1.1, 2.6, 1.8, 1.2]);
P("Single-date subsets contain all three varieties and, on 11-02 and 24-02-2026, a few flowering leaves besides the vegetative ones; on 03-03 and 13-03-2026 flowering and pod-formation leaves. The stage subsets combine two dates each (vegetative: 11-02 and 24-02-2026; pod formation: 03-03 and 13-03-2026) and the variety subsets all four dates. On 03-03-2026 only one healthy plot (9 leaves) was at pod formation, so the pod-formation subset is dominated by 13-03-2026.");
H2("2.2 Pre-processing");
P("The contact probe has its own light source at a few millimetres from the leaf, so there is no atmospheric path; the water-absorption bands (1350–1430, 1800–1950, 2350–2500 nm), which Das et al. (2020) removed for canopy data, were kept because they carry leaf-water information. The 350–399 nm detector edge was removed (its noise, the standard deviation of the Savitzky–Golay residual, was more than 100 times that of 500–699 nm). Tiers 1–4 of Part A used the raw reflectance of 400–2500 nm (2101 bands). Part K used splice-corrected and Savitzky–Golay-smoothed spectra with guard zones at the detector joins (section 2.7).");
H2("2.3 The four-tier method and the imbalance corrections");
P("**Tier 1 — statistical screening.** With two classes the one-way ANOVA of Das et al. reduces to a two-sample test. Welch's unequal-variance t-test was applied at every band and the p-values adjusted with the Benjamini–Hochberg false-discovery rate (q < 0.05):");
EQ("t = (x̄_D − x̄_H) / √(s²_D/n_D + s²_H/n_H),     q₍ᵢ₎ = min_{k ≥ i} p₍ₖ₎ · m / k");
P("Checks: one-way ANOVA (rule of Das et al.), 1000 balanced random subsets with equal numbers of healthy and diseased leaves (does significance survive without the large diseased class?), and a linear mixed model with a random plot intercept (leaves of one plot are not independent; Hurlbert, 1984). The −log₁₀(p) of every band was plotted against wavelength.");
P("**Tier 2 — CART band selection.** rpart (R) with method = 'class', Gini splitting, minsplit 20, minbucket 7, cp 0.01 and **prior = c(0.5, 0.5)**, so that both classes carry equal weight despite the imbalance. The bands used as split variables form the CART set. Stability: 200 plot-level bootstrap trees and the trees of the nested training sets; a band counts as re-selected when a band within ± 10 nm is chosen.");
P("**Random Forest as the alternative Tier-2 selector.** A Balanced Random Forest (imbalanced-learn; each tree on a bootstrap sample with equal numbers of both classes; 1000 trees, √p candidate bands per split) was fitted to the Tier-1 bands; importance = mean decrease in Gini impurity. Because neighbouring bands are almost identical, bands were picked as importance peaks at least 10 nm apart: the 17 highest form RF-17 (the size of the CART set of Das et al.), the 10 highest RF-10. Checks: second seed, R randomForest, permutation importance and an ordinary class-weighted forest.");
P("**Tier 3 — Jeffries–Matusita distance.** With class means μ and covariance matrices Σ of the selected bands:");
EQ("α = ⅛ (μ_H − μ_D)ᵀ [(Σ_H + Σ_D)/2]⁻¹ (μ_H − μ_D) + ½ ln{ |(Σ_H + Σ_D)/2| / √(|Σ_H| |Σ_D|) },     J–M = 2 (1 − e^(−α))");
P("J–M ranges from 0 to 2; classes are called separable at J–M ≥ 1.90, and Das et al. used 1.94 (97 % of 2).");
P("**Tier 4 — quadratic discriminant analysis** with **equal prior probabilities** (π_H = π_D = 0.5; the sample priors 0.17 / 0.83 would favour 'diseased'), leaf-level stratified 10-fold cross-validation as in Das et al., summarised in an error matrix (rows = classified, columns = reference) with producer's and user's accuracy, overall accuracy (OA), Cohen's κ and the **balanced accuracy** BA = ½ (recall healthy + recall diseased), the headline metric because OA is dominated by the large diseased class.");
H2("2.4 Validation designs");
P("The protocol of Das et al. (bands chosen on all leaves, then leaf-level 10-fold CV) is optimistic when leaves of one plot are both in training and test and when selection and evaluation use the same leaves (selection bias; Ambroise and McLachlan, 2002). Five schemes were therefore used, with identical folds in every step of a subset:");
B(["**V1** — leaf-level stratified 10-fold CV, bands fixed (the protocol of Das et al.).",
   "**V2** — plot-grouped k-fold CV, bands fixed (removes plot leakage, keeps selection bias).",
   "**V3** — nested plot-grouped k-fold CV × 5 repeats: Tier 1, band selection and classifier refitted inside every training set; folds grouped by plot across all dates, k = min(10, number of plots of the smaller class), so that every test fold contains both classes. This is the honest estimate for new plots.",
   "**V4** — 30 % of the plots of each class held out × 10 random splits; everything refitted on the remaining plots.",
   "**V5** — transfer: in subsets with several dates (stages, varieties) leave-one-date-out on the V4 test plots (train on the other dates' training plots, test on the held-out date's test plots); in single-date subsets leave-one-variety-out (train on two varieties, test on the third)."]);
table([["Subset", "V3 folds (k × 5)", "V3 fold assignment", "V4 held out (H + D plots)", "V5 type", "V5 units (skipped)"],
  ...S.map((s) => [s.short, `${s.k3} × 5 = ${s.nV3}`, s.v3_method, `${s.v4[0]} + ${s.v4[1]}`, s.v5_by === "Date" ? "leave-one-date-out" : "leave-one-variety-out",
    `${s.nV5}${s.v5_dropped ? ` (${s.v5_dropped})` : ""}`])],
  "Validation design of each subset. Variety subsets have only four healthy plots, so V3 uses 4 folds. Skipped V5 units: the held-out date had no leaves of the test plots, or the training set had fewer than 5 leaves of a class.", [2, 1.4, 2.3, 1.6, 1.8, 1.2]);
P("**Fallback when Tier 1 finds nothing.** In weak-signal subsets some training sets (and, in the vegetative stage, all leaves) had fewer than two FDR-significant bands. Tier 2 then received the bands with uncorrected p < 0.05 (or the 20 smallest p-values), so that the pipeline can still be evaluated; every such case is flagged in the cross-checks.");
H2("2.5 Disease-sensitive features (Part K)");
B(["**K0** — splice correction at the ASD detector joins (1000/1001 and 1800/1801 nm), Savitzky–Golay smoothing (window 11, order 2), first and second derivatives (windows 15 and 21), guard zones excluded from rankings (reflectance 990–1010 and 1795–1835 nm; derivative 988–1012 and 1793–1837 nm).",
   "**K1** — smoothed band reflectance at every band: Welch t + FDR, Hedges' g, AUC and a threshold classifier validated on plots.",
   "**K2** — continuum removal (upper convex hull) in six absorption windows (495, 675, 970, 1200, 1450, 1940 nm): depth, position, area, width and symmetry (30 parameters; Clark and Roush, 1984; Kokaly and Clark, 1999).",
   "**K3** — 31 vegetation indices of the flowering-stage workbook, plus K3b: the optimised two-band normalised difference (NDSI) and difference index searched over all band pairs, with pairs straddling a detector join excluded and the search repeated inside training plots (honest estimate).",
   "**K4** — first-derivative bands, 20 edge parameters (blue, yellow and red edge amplitude, position and area; green peak; red well) and **K4b** the red-edge inflection point (REIP) by four methods (maximum first derivative; linear four-point, Guyot and Baret, 1988; Lagrangian, Dawson and Curran, 1998; linear extrapolation, Cho and Skidmore, 2006).",
   "**K6** — point-biserial correlation spectra of reflectance and first derivative with disease status; **K5** — CART and Balanced RF on each feature group, with identical plot-grouped folds."]);
H2("2.6 Four tiers on the combined feature pool (Part C)");
P(`All K1 reflectance bands, the 30 K2 parameters, the 31 K3 indices, the first-derivative bands and the 20 edge parameters were pooled (${S[0].C_nfeat} features after removing exact duplicates), and the same four tiers, settings and folds as in Part A were applied: Welch + FDR, CART and RF-17 selection, J–M and QDA with equal priors, with V1–V5 validation. RF peaks were picked within each spectral series, and every scalar feature (index, CR parameter, edge parameter) was its own candidate.`);
H2("2.7 Cross-checks and software");
P("Every step was cross-checked by an independent implementation or recomputation: Welch t vs SciPy; BH q vs statsmodels; ANOVA F = t²; mixed model R nlme vs statsmodels; rpart vs scikit-learn trees; QDA vs manual discriminant functions and R MASS::qda; J–M by Cholesky vs explicit inverse; RF importance vs a second seed, R randomForest and permutation importance; continuum removal, indices and REP recomputed by Excel formulas; assertions that no plot (and in V5 no date or variety) occurs in both training and test. Software: Python 3.13 (NumPy, SciPy, pandas, statsmodels, scikit-learn 1.9, imbalanced-learn 0.14, matplotlib, openpyxl) and R 4.3.3 (rpart 4.1.23, MASS, nlme, randomForest 4.7).");
figure("workflow.png", "Workflow of each subset analysis (shown for date 11-02-2026; the validation design follows Table 3).", 600);

// ============================================================ 3 overview
pageBreak();
H1("3. Results across the nine subsets");
H2("3.1 Spectral differences between healthy and diseased leaves");
figure("X10_mean_spectra_grid.png", "Mean reflectance of healthy (aqua) and diseased (orange) leaves in each subset (n = healthy / diseased).", 620);
figure("X4_difference_spectra.png", "Difference spectra (mean diseased − mean healthy reflectance, in % reflectance) by date, growth stage and variety.", 620);
P(`The difference spectra show how the disease effect develops. On 11-02-2026 diseased leaves reflected slightly less than healthy leaves in the visible and NIR (differences < 1.2 %), whereas on 24-02 and 03-03-2026 they reflected more in the visible (chlorophyll loss, white pustules) and in the SWIR beyond 1400 nm (lower leaf water), and less on the NIR plateau at 750–1000 nm (mesophyll damage). The effect was largest on 03-03-2026 (up to +4 to +5 % in the visible and SWIR and −5 % in the NIR). On 13-03-2026 diseased leaves reflected more at all wavelengths, including the NIR (+0.3 to +2.5 %), as senescence of the late-season leaves overlays the disease effect. In the vegetative stage the visible difference has opposite signs on its two dates, so it cancels when the dates are pooled, and only a small NIR decrease remains; at pod formation the SWIR difference is large (+2 to +3 %) but the NIR difference is small. The three varieties show the same pattern with V1 strongest.`);
H2("3.2 Tier 1 — how many bands differ");
table([["Subset", "Welch + FDR", "Mixed model + FDR", "Balanced subsets ≥ 95 %", "Best K1 band (nm)", "AUC", "Bands AUC ≥ 0.70"],
  ...S.map((s) => [s.short, `${s.n_sig} of 2101`, s.n_mm, s.tier1_tests.find((t) => t[0].startsWith("Balanced"))[1], num(s.k1_best[0], 0), num(s.k1_best[1]), s.k1_best[2]])],
  "Tier 1 results by subset (raw reflectance, 400–2500 nm). Mixed model = random plot intercept (pseudo-replication); balanced subsets = significant in at least 95 % of 1000 subsets with equal class sizes.", [2, 1.2, 1.3, 1.3, 1.2, 0.8, 1.1]);
figure("X3_significance_spectra.png", "Significance spectra: −log₁₀ q of the Welch t-test (BH-FDR) against wavelength, by date, growth stage and variety (dashed line q = 0.05; symmetric-log scale).", 620);
P(`The disease signal grew over the season: ${dates.map((s) => `${s.dates[0]} ${s.n_sig}`).join(", ")} significant bands. On 11-02-2026 the significant bands are confined to the green (≈ 500–600 nm) and SWIR-2 (≈ 2260–2410 nm) and none survives the plot random effect, so symptoms were only beginning. On 03-03-2026, 2050 of 2101 bands are significant and 2010 remain so with the plot effect. The vegetative stage has no FDR-significant band at all, because the visible difference changes sign between its two dates and the date difference inflates the variance within each class, and V3 has no band significant with the mixed model although 1150 are significant by Welch: with only four healthy plots per variety the between-plot variation absorbs the class difference. These subsets warn that leaf-level significance can be produced by a few plots.`);
H2("3.3 Tier 2 — bands selected by CART and by Random Forest");
figure("X6_selected_bands.png", "Bands selected by CART (blue triangles) and the 17 RF importance peaks (orange dots) in each subset (Part A, raw reflectance).", 620);
table([["Subset", "CART set", "Root band (nm)", "CART bands (nm, order of use)", "RF-17 peaks (nm, by importance)"],
  ...S.map((s) => [s.short, s.cart_name, s.root, s.cart_bands.join(", "), s.rf_bands.join(", ")])],
  "Tier 2 band sets by subset.", [1.4, 0.9, 0.8, 3.2, 3.6], 15);
P("Both selectors return to the same regions in most subsets: the red edge (≈ 690–760 nm), the green peak (≈ 520–590 nm) and the SWIR water bands near 1400 nm and 1880–2020 nm. RF concentrates its 17 peaks in one or two regions (it ranks neighbouring, correlated bands), whereas CART picks complementary regions. On 11-02-2026 both selectors use only the green and the SWIR-2 end (2260–2410 nm), consistent with Tier 1.");
H2("3.4 Tier 3 — separability (J–M distance)");
figure("X7_jm_by_subset.png", "J–M distance of healthy and diseased leaves on the CART and RF-17 sets of Part A (raw reflectance) and Part C (combined pool). Dashed 1.90, dotted 1.94.", 620);
table([["Subset", "Part A CART", "Part A RF-17", "Part C CART", "Part C RF-17"],
  ...S.map((s) => [s.short, `${num(s.jm_c)} (${s.cart_name})`, num(s.jm_r), `${num(s.C_jm_c)} (${s.C_cart_name})`, num(s.C_jm_r)])],
  "J–M distance (0–2) by subset.", [2, 1.6, 1.2, 1.6, 1.2]);
P(`On raw reflectance no band set reaches 1.94; only RF-17 on 03-03-2026 (1.93) passes 1.90, and pod formation comes close (1.86). In the combined pool the 17 RF-selected features pass 1.90 in ${S.filter((s) => s.C_jm_r >= 1.9).length} of 9 subsets and 1.94 in ${S.filter((s) => s.C_jm_r >= 1.94).length} (${S.filter((s) => s.C_jm_r >= 1.94).map((s) => s.short).join(", ")}). The small CART sets of Part C (4–12 features) have lower J–M, because J–M grows with the number of features; their classification accuracy is nevertheless high (Table 8).`);
H2("3.5 Tier 4 and validation — accuracy on new plots");
table([["Subset", "A: CART clf", "A: RF clf", "A: QDA-CART", "A: QDA-RF", "C: CART clf", "C: RF clf", "C: QDA-CART", "C: QDA-RF"],
  ...S.map((s) => [s.short, ...PIPES.map((p) => p1(vA(s, p, "V3").BA)), ...PIPES.map((p) => p1(vC(s, p, "V3").BA))]),
  ["All dates pooled", ...PIPES.map((p) => p1(REF.vA[`${p}|V3`].BA)), ...PIPES.map((p) => p1(REF.vC[`${p}|V3`].BA))]],
  "Balanced accuracy (%) of the four pipelines on new plots (V3, nested plot-grouped CV, mean of 5 repeats), Part A (raw reflectance) and Part C (combined pool). clf = classifier; QDA-CART / QDA-RF = QDA with equal priors on the CART- or RF-selected features.", [1.8, 1, 1, 1.1, 1, 1, 1, 1.1, 1]);
figure("X1_pipelines_by_subset.png", "Balanced accuracy on new plots (V3) of the four pipelines in Part A and Part C, by subset. Dashed line: the same pipeline with all dates pooled.", 620);
P(`QDA with equal priors on the CART bands of Das et al. reached ${rng(S.map((s) => vA(s, "QDA on CART features", "V3").BA))} on new plots, above the pooled result (${p1(REF.vA["QDA on CART features|V3"].BA)} %) on all four dates and in V1, slightly below it in the vegetative stage, at pod formation and in V2 and V3, and up to ${p1(vA(SH["Date 03-03-2026"], "QDA on CART features", "V3").BA)} % on 03-03-2026. As classifiers on reflectance, CART and RF were weaker than QDA on the selected bands in every subset; in the weak-signal subsets (11-02-2026, vegetative) they stayed near chance (${p1(vA(SH["Vegetative"], "RF classifier", "V3").BA)}–${p1(vA(SH["Date 11-02-2026"], "RF classifier", "V3").BA)} % for RF), while QDA on the few CART bands still reached ${p1(vA(SH["Vegetative"], "QDA on CART features", "V3").BA)}–${p1(vA(SH["Date 11-02-2026"], "QDA on CART features", "V3").BA)} %. In the combined pool all pipelines improved: QDA on RF features gained ${p1(Math.min(...gainC))} to ${p1(Math.max(...gainC))} points over QDA on CART reflectance bands, and the best pipeline per subset reached ${rng(bestOverall)}. The exceptions are 13-03-2026 and pod formation, where the combined pool gained little.`);
figure("X2_validation_schemes.png", "Part C: balanced accuracy of QDA on RF features and of the RF classifier under the four validation schemes, by subset.", 620);
const dv1 = S.map((s) => vA(s, "QDA on CART features", "V1").BA - vA(s, "QDA on CART features", "V3").BA);
P(`For QDA on CART bands, the leaf-level estimate of Das et al. (V1) differed from the nested plot-grouped estimate (V3) by ${p1(Math.min(...dv1))} to +${p1(Math.max(...dv1))} points; it was clearly optimistic only in V2 (+${p1(dv1[7])}) and in the vegetative stage (+${p1(dv1[4])}), where selection on all leaves and plot effects matter most, and close to V3 elsewhere. In the combined pool (QDA on RF features) V1 − V3 ranged from ${p1(Math.min(...S.map((s) => vC(s, "QDA on RF features", "V1").BA - vC(s, "QDA on RF features", "V3").BA)))} to +${p1(Math.max(...S.map((s) => vC(s, "QDA on RF features", "V1").BA - vC(s, "QDA on RF features", "V3").BA)))} points. The plot hold-out (V4) agreed with V3 within a few points. Transfer (V5) is discussed in section 3.8.`);
H2("3.6 CART versus Random Forest");
table([["Subset", "RF − CART classifier (V3)", "RF better / folds", "p", "QDA: RF − CART bands", "p", "Jaccard RF / CART"],
  ...S.map((s) => { const a = s.wil_A.find((r) => r.Comparison.startsWith("RF classifier") && r.Units.startsWith("V3"));
                    const b = s.wil_A.find((r) => r.Comparison.startsWith("QDA on RF") && r.Units.startsWith("V3"));
                    return [s.short, `${(100 * a["Mean difference"]).toFixed(1)} pts`, `${a["First better"]} / ${a.n}`, pv(a["Wilcoxon p"]),
                            `${(100 * b["Mean difference"]).toFixed(1)} pts`, pv(b["Wilcoxon p"]), `${num(s.stab_A.RF.jacc, 2)} / ${num(s.stab_A.CART.jacc, 2)}`]; })],
  "CART versus RF in Part A: paired Wilcoxon signed-rank tests over the V3 folds (positive = RF better), and stability of the selected bands (mean pairwise Jaccard index, ± 10 nm, over the nested training sets).", [1.8, 1.4, 1.1, 0.9, 1.4, 0.9, 1.2]);
const rfw = S.map((s) => wil(s, "RF classifier")), qw = S.map((s) => wil(s, "QDA on RF"));
P(`As a classifier, RF beat CART in ${rfw.filter((r) => r["Mean difference"] > 0.01 && r["Wilcoxon p"] < 0.05).length} of 9 subsets (by ${p1(Math.min(...rfw.filter((r) => r["Wilcoxon p"] < 0.05).map((r) => r["Mean difference"])))}–${p1(Math.max(...rfw.map((r) => r["Mean difference"])))} points, Wilcoxon p < 0.01); in V2 the advantage (+${p1(rfw[7]["Mean difference"])} points) was not significant and in the vegetative stage the two performed alike. As band selectors for QDA the result was mixed: the RF bands were significantly better on 24-02-2026, on 13-03-2026 and at pod formation (+4 to +8 points), the CART bands in V3 (${p1(qw[8]["Mean difference"])} points), and the difference was not significant in the other five subsets. RF selected its bands more consistently than CART in eight subsets (mean pairwise Jaccard ${num(Math.min(...S.map((s) => s.stab_A.RF.jacc)), 2)}–${num(Math.max(...S.map((s) => s.stab_A.RF.jacc)), 2)} vs ${num(Math.min(...S.map((s) => s.stab_A.CART.jacc)), 2)}–${num(Math.max(...S.map((s) => s.stab_A.CART.jacc)), 2)}); only in the vegetative stage were both equally unstable (0.37 vs 0.39), consistent with the absence of a clear Tier-1 signal there.`);
H2("3.7 Disease-sensitive features (Part K)");
figure("X5_k5_heatmap.png", "K5: balanced accuracy of a Balanced RF on each feature group, by subset (plot-grouped CV, V3).", 620);
table([["Subset", "Best group (RF, V3)", "Best D1 band (AUC)", "Best K2 parameter (AUC)", "Best K3 index (AUC)", "Best edge parameter (AUC)"],
  ...S.map((s) => { const b = bestK(s); return [s.short, `${GN[b[0]]} ${p1(b[1])} %`, `${s.d1_top[0][0]} nm (${num(s.d1_top[0][1], 2)})`,
                   `${s.k2_top[0][0]} (${num(s.k2_top[0][1], 2)})`, `${s.k3_top[0][0]} (${num(s.k3_top[0][1], 2)})`, `${s.k4e_top[0][0]} (${num(s.k4e_top[0][1], 2)})`]; })],
  "Most informative feature group and the most sensitive single feature of each family, by subset (AUC is direction-free: 0.5 = no separation).", [1.5, 1.8, 1.3, 2.1, 1.3, 2.1], 15);
const kgap = S.map((s) => Math.max(k5(s, "G2", "RF"), k5(s, "G4", "RF")) - Math.max(k5(s, "G1", "RF"), k5(s, "G3", "RF")));
const kbig = S.filter((s, i) => kgap[i] > 0.05);
P(`In ${kbig.length} of 9 subsets the first-derivative (K4) and continuum-removed (K2) groups were far more informative than reflectance (K1) or the 31 indices (K3), by ${p1(Math.min(...kbig.map((s) => kgap[S.indexOf(s)])))}–${p1(Math.max(...kgap))} points of RF accuracy; on ${S.filter((s, i) => kgap[i] <= 0.05).map((s) => s.short).join(" and ")} the groups performed alike, because late-season senescence changes reflectance level and shape together. The most sensitive single features recur across subsets: the symmetry or area of the 1940 nm water absorption feature (CR6), the width of the 970 nm water feature (CR3), first-derivative bands on the NIR shoulder at 845–885 nm and near 1920 nm, and the water and anthocyanin indices NWI2 and ARI. The best single features reach AUC ${num(Math.min(...dates.slice(0, 3).map((s) => Math.max(s.k2_top[0][1], s.d1_top[0][1]))), 2)}–${num(Math.max(...dates.slice(0, 3).map((s) => Math.max(s.k2_top[0][1], s.d1_top[0][1]))), 2)} on the first three dates but only ${num(Math.min(...[SH["Pod formation"], ...vars].map((s) => Math.max(s.k2_top[0][1], s.d1_top[0][1]))), 2)}–${num(Math.max(...[SH["Pod formation"], ...vars].map((s) => Math.max(s.k2_top[0][1], s.d1_top[0][1]))), 2)} at pod formation and in the varieties.`);
H2("3.8 Red-edge shift and transfer to new dates and varieties");
figure("X9_reip_transfer.png", "Left: REIP shift (diseased − healthy, Lagrangian method). Right: Part C RF classifier, nested plot-grouped CV (V3) versus transfer to an unseen variety (dates) or an unseen date (stages, varieties) (V5).", 620);
P("The red-edge inflection point shifted to shorter wavelengths in diseased leaves in eight subsets (blue shift of chlorophyll loss): most on 03-03-2026 (−4.9 nm), on 24-02-2026 (−3.2 nm) and in V1 (−3.2 nm), little in the vegetative stage and at pod formation (−0.7 to −1.1 nm), and not at all on 11-02-2026 (+0.2 nm).");
P(`Transfer differed sharply between the two kinds of V5. Within a single date, features and classifiers chosen on two varieties worked on the third almost as well as on new plots of the same varieties (V5 ${rng(dates.map((s) => vC(s, "RF classifier", "V5").BA))} for the RF classifier on the combined pool). Across dates, accuracy fell to ${rng(S.filter((s) => s.v5_by === "Date").map((s) => vC(s, "RF classifier", "V5").BA))} in the stage and variety subsets: the spectral change between dates (phenology, leaf age, measurement conditions) is larger than the disease effect, and its direction is not the same on every date (Figure 2).`);
H2("3.9 What the combined-pool selectors chose (Part C)");
figure("X8_partC_types.png", "Feature types chosen by CART and by RF (RF-17) from the combined pool, by subset.", 620);
P("RF-17 consisted almost entirely of first-derivative bands, with two or three continuum-removed water parameters; edge parameters and indices entered mainly on 13-03-2026 and at pod formation, and reflectance bands almost never. CART chose fewer features (4–12) and a more varied mix, usually one continuum-removed water parameter at or near the root of the tree.");

// ============================================================ 4 per subset
function subsetChapter(s, idx) {
  pageBreak();
  H1(`4.${idx} ${s.short} — ${s.label}`);
  const T = s.txt || {};
  H2(`4.${idx}.1 Data and validation design`);
  P(`This subset contains ${s.n} leaf spectra (${s.nH} healthy, ${s.nD} diseased; ratio 1 : ${(s.nD / s.nH).toFixed(1)}) from ${s.pH} healthy and ${s.pD} diseased plots, measured on ${s.dates.join(", ")}; growth stages ${s.stages.join(", ")}; varieties ${s.varieties.join(", ")}. V3 used ${s.k3}-fold plot-grouped CV × 5 (${s.nV3} training sets), V4 held out ${s.v4[0]} healthy + ${s.v4[1]} diseased plots × 10, and V5 was ${s.v5_by === "Date" ? "leave-one-date-out on new plots" : "leave-one-variety-out"} (${s.nV5} units${s.v5_dropped ? `, ${s.v5_dropped} skipped` : ""}).`);
  if (s.by_stage.length > 1) table([["Date", "Growth stage", "Healthy", "Diseased"], ...s.by_stage.map((r) => [r.Date, r["Growth stage"], r.Healthy, r.Diseased])],
    `${s.short}: leaf spectra by date and growth stage.`, [2, 2, 1, 1]);
  figure(s.figs.mean, `${s.short}: mean reflectance of healthy and diseased leaves (± 1 SD).`, 520);
  H2(`4.${idx}.2 Tier 1 — statistical screening`);
  table([["Test", "Significant bands (of 2101)"], ...s.tier1_tests.map((t) => [t[0], t[1]])], `${s.short}: number of significant bands by test.`, [5, 1.5]);
  if (s.tier1_rule !== "FDR") P(`**Fallback applied:** only ${s.n_sig} band(s) passed the FDR correction on all leaves, so Tier 2 received the ${s.n_cand} bands with ${s.tier1_rule === "uncorrected p" ? "uncorrected p < 0.05" : "the smallest p-values"}.`);
  if (s.ranges.length) table([["Contiguous significant range (nm)", "Bands"], ...s.ranges.map((r) => [r["Range (nm)"], r.Bands])], `${s.short}: largest contiguous ranges of FDR-significant bands.`, [3, 1]);
  table([["Band (nm)", "Mean H", "Mean D", "Welch t", "q (BH)", "Hedges g", "AUC"], ...s.top_bands.map((r) => [r[0], num(r[1], 4), num(r[2], 4), num(r[3], 2), r[4] == null ? "–" : Number(r[4]).toExponential(2), num(r[5], 2), num(r[6], 3)])],
    `${s.short}: ten bands with the largest |t|.`, [1, 1, 1, 1, 1.2, 1, 0.8]);
  figure(s.figs.logp, `${s.short}: −log₁₀(p) against wavelength (Welch p, BH q and mixed-model q; dashed p or q = 0.05).`, 560);
  H2(`4.${idx}.3 Tier 2 — CART and Random Forest band selection`);
  table([["Band (nm)", "Region", "First used at node", "Bootstrap re-selection", "Nested-CV re-selection"],
    ...s.cart_table.map((r) => [r[0], r[1], r[2], pct(r[3]), pct(r[4])])], `${s.short}: the ${s.cart_name} bands selected by rpart (prior 0.5/0.5) and how often a band within ± 10 nm is re-selected.`, [1, 2, 1, 1.3, 1.3]);
  figure(s.figs.tree, `${s.short}: CART tree on the Tier-1 bands (${s.cart_name}).`, 600);
  P(`RF-17 importance peaks: ${s.rf_bands.join(", ")} nm.`);
  figure(s.figs.rfimp, `${s.short}: Balanced RF importance spectrum with the RF-17 peaks and the CART bands.`, 560);
  H2(`4.${idx}.4 Tier 3 and Tier 4 — separability and classification`);
  table([["Band set", "Bands", "α (Bhattacharyya)", "J–M (0–2)", "√J–M", "Separability"], ...s.tier3.map((r) => [r[0], r[1], num(r[2]), num(r[3]), num(r[4]), sepWord(r[3])])],
    `${s.short}: Jeffries–Matusita distance of healthy and diseased leaves.`, [2, 0.8, 1.2, 1, 0.9, 2]);
  table(em(s.em_cart), `${s.short}: error matrix of QDA (equal priors) on the ${s.cart_name} bands, leaf-level 10-fold CV (V1; as Table 2 of Das et al.).`, [2, 1, 1, 1, 1.2]);
  table([["Band set", "Classifier", "OA", "BA", "PA healthy", "PA diseased", "κ"], ...s.tier4.map((r) => [r[0], r[1], pct(r[2]), pct(r[3]), pct(r[4]), pct(r[5]), num(r[6])])],
    `${s.short}: Tier 4 on all band sets (V1), with equal and sample priors and LDA for comparison.`, [1.8, 2, 0.9, 0.9, 1, 1, 0.8]);
  H2(`4.${idx}.5 Validation and CART versus RF (Part A)`);
  table([["Pipeline", "V1", "V3 (± SD)", "V4 (± SD)", "V5", "AUC V3", "κ V3"],
    ...PIPES.map((p) => [p, pct(vA(s, p, "V1").BA), `${pct(vA(s, p, "V3").BA)} ± ${p1(vA(s, p, "V3").SD)}`, `${pct(vA(s, p, "V4").BA)} ± ${p1(vA(s, p, "V4").SD)}`,
      pct(vA(s, p, "V5").BA), num(vA(s, p, "V3").AUC), num(vA(s, p, "V3").kappa)])],
    `${s.short}: balanced accuracy of the four pipelines on raw reflectance under the validation schemes.`, [2.2, 1, 1.3, 1.3, 1, 1, 0.8]);
  table([["Scheme", "Priors", "BA", "SD", "OA", "PA healthy", "PA diseased"], ...s.val_qda.map((r) => [r[0], r[1], pct(r[2]), r[3] == null ? "–" : p1(r[3]), pct(r[4]), pct(r[5]), pct(r[6])])],
    `${s.short}: validation of QDA on CART bands — effect of the imbalance correction (equal vs sample priors) and of random under-sampling (V3-RUS).`, [2.8, 1.5, 0.8, 0.6, 0.8, 0.9, 0.9], 15);
  figure(s.figs.pipesA, `${s.short}: CART and RF as classifiers and as band selectors for QDA (Part A).`, 580);
  table([["Comparison", "Units", "n", "Mean Δ BA", "First better", "Wilcoxon p"],
    ...s.wil_A.map((r) => [r.Comparison, r.Units, r.n, `${(100 * r["Mean difference"]).toFixed(1)} pts`, r["First better"], pv(r["Wilcoxon p"])])],
    `${s.short}: paired comparisons on identical folds (positive = first pipeline better).`, [3, 1.6, 0.5, 1, 0.9, 1]);
  H2(`4.${idx}.6 Disease-sensitive features (Part K)`);
  table([["Family", "Feature", "AUC", "Direction", "BA plot-grouped CV", "BA hold-out"],
    ...s.k2_top.slice(0, 3).map((r) => ["K2 continuum removal", r[0], num(r[1]), r[2], pct(r[4]), pct(r[5])]),
    ...s.k3_top.slice(0, 3).map((r) => ["K3 index", r[0], num(r[1]), r[2], pct(r[4]), pct(r[5])]),
    ...s.k4e_top.slice(0, 2).map((r) => ["K4 edge parameter", r[0], num(r[1]), r[2], pct(r[4]), pct(r[5])]),
    ...s.d1_top.slice(0, 3).map((r) => ["K4 first derivative", `D1 ${r[0]} nm`, num(r[1]), r[2], "–", "–"]),
    ...s.k1_regions.sort((a, b) => b[2] - a[2]).slice(0, 2).map((r) => ["K1 reflectance", `R ${r[0]} nm (${r[1]})`, num(r[2]), r[3], pct(r[4]), "–"]),
    ...s.k3b.map((r) => ["K3b optimised index", r[0], num(r[1]), "", pct(r[2]), "–"])],
    `${s.short}: most sensitive single features of each family (threshold classifier validated on plots).`, [1.6, 2.4, 0.7, 0.8, 1.2, 1]);
  table([["Feature group", "CART (V3)", "RF (V3)", "CART (V4)", "RF (V4)"],
    ...["G0", "G1", "G2", "G3", "G4", "G5", "G6", "GS"].filter((g) => k5(s, g, "RF") != null).map((g) => [GN[g], pct(k5(s, g, "CART")), pct(k5(s, g, "RF")), pct(k5(s, g, "CART", "Hold-out")), pct(k5(s, g, "RF", "Hold-out"))])],
    `${s.short}: K5 — CART vs Balanced RF on each feature group (balanced accuracy).`, [3, 1, 1, 1, 1]);
  figure(s.figs.k5, `${s.short}: K5 — CART vs RF on each disease-sensitive feature group.`, 560);
  table([["REIP method", "Healthy (nm)", "Diseased (nm)", "Shift (nm)", "AUC", "BA plot-grouped CV"], ...s.reip.map((r) => [r[0], num(r[1], 1), num(r[2], 1), num(r[3], 2), num(r[4]), pct(r[5])])],
    `${s.short}: red-edge inflection point by four methods.`, [2.4, 1, 1, 0.9, 0.8, 1.2]);
  H2(`4.${idx}.7 Four tiers on the combined feature pool (Part C)`);
  P(`Tier 1: ${s.C_nsig} of ${s.C_nfeat} features significant. Tier 2: CART selected ${s.C_cart.length} features (${s.C_cart.map(featName).join(", ")}); RF-17: ${s.C_rf.map(featName).join(", ")}. Tier 3: J–M ${num(s.C_jm_c)} (CART set) and ${num(s.C_jm_r)} (RF-17), ${sepWord(s.C_jm_r)} for RF-17.`);
  table([["Feature type", "Features", "Tier-1 significant", s.C_cart_name, s.C_rf_name], ...s.C_comp.map((r) => [r[0], r[1], r[2], r[3], r[4]])],
    `${s.short}: composition of the combined pool and of the selected sets.`, [2.4, 1, 1.2, 1, 1]);
  table([["Pipeline", "V1", "V3 (± SD)", "V4 (± SD)", "V5", "AUC V3", "κ V3"],
    ...PIPES.map((p) => [p, pct(vC(s, p, "V1").BA), `${pct(vC(s, p, "V3").BA)} ± ${p1(vC(s, p, "V3").SD)}`, `${pct(vC(s, p, "V4").BA)} ± ${p1(vC(s, p, "V4").SD)}`,
      pct(vC(s, p, "V5").BA), num(vC(s, p, "V3").AUC), num(vC(s, p, "V3").kappa)])],
    `${s.short}: balanced accuracy of the four pipelines on the combined pool.`, [2.2, 1, 1.3, 1.3, 1, 1, 0.8]);
  figure(s.figs.pipesC, `${s.short}: four pipelines on the combined pool under V1, V3, V4 and V5.`, 580);
  figure(s.figs.ctop, `${s.short}: the 30 most important features of the combined pool (Balanced RF).`, 520);
  const cw = s.cross.filter((r) => r[2].startsWith("V3"));
  table([["First", "Second", "Mean Δ BA", "First better / n", "Wilcoxon p"], ...cw.map((r) => [r[0], r[1], `${(100 * r[3]).toFixed(1)} pts`, `${r[4]} / ${r[5]}`, pv(r[6])])],
    `${s.short}: combined pool vs reflectance vs K5 (paired over the V3 folds).`, [2.6, 2.6, 0.9, 1, 0.9], 15);
  H2(`4.${idx}.8 Transfer (V5)`);
  const lv = [...new Set(s.lodo.map((r) => r[2]))];
  table([["Feature set · pipeline", ...lv],
    ...[...new Set(s.lodo.map((r) => `${r[0]} · ${r[1]}`))].map((k) => [k, ...lv.map((l) => { const r = s.lodo.find((q) => `${q[0]} · ${q[1]}` === k && q[2] === l); return r ? pct(r[4]) : "–"; })])],
    `${s.short}: balanced accuracy by ${s.lodo_level.toLowerCase()} (${s.v5_by === "Date" ? "trained on the other dates, tested on new plots of the held-out date" : "trained on the other two varieties"}).`, [3, ...lv.map(() => 1)]);
  figure(s.figs.v5, `${s.short}: V5 transfer by held-out ${s.v5_by === "Date" ? "date" : "variety"}.`, 540);
  H2(`4.${idx}.9 Interpretation`);
  (T.conclusions || []).slice(1).forEach((t) => P(t));
  if (T.recommendations) { H3("Recommendations for this subset"); B(T.recommendations); }
  H3("Cross-checks");
  P(`${s.checks.PASS} checks passed, ${s.checks.FLAG} were flagged and ${s.checks.FAIL} failed. Flagged items are limitations reported in the workbook, not errors: ${s.flags.map((f) => f[1]).join("; ")}.`);
}
pageBreak();
H1("4. Results by subset");
P("Each section below follows the steps of the workbook of that subset: data and validation design, Tiers 1–4 on raw reflectance with CART and RF, validation, disease-sensitive features, the four tiers on the combined pool, transfer, interpretation and cross-checks. Sheet numbers in the workbooks: 03–09 (Steps 0–6), 10–13 (Part A1–A4), 14–22 (Part K), 23–30 (Part C), 31 (V5), 32 (strata), 33 (cross-checks).");
S.forEach((s, i) => subsetChapter(s, i + 1));

// ============================================================ 5 discussion
pageBreak();
H1("5. Discussion");
H2("5.1 Development of the disease signal over the season");
P(`The four dates trace the epidemic. On 11-02-2026 the plots had been inoculated recently and symptoms were developing: only ${dates[0].n_sig} bands differed (none with the plot effect), no single band reached AUC 0.70, the REIP did not shift, and diseased leaves were, if anything, slightly darker. Yet the derivative and continuum-removed features already separated the classes (RF ${p1(k5(dates[0], "G4", "RF"))} % on K4, best single feature ${dates[0].k2_top[0][0]} AUC ${num(dates[0].k2_top[0][1], 2)}), so changes in band shape — the NIR shoulder and the 1940 nm water feature — preceded visible changes in reflectance level. By 24-02 and 03-03-2026 white rust had produced the classical pattern of chlorophyll loss (higher visible reflectance, blue shift of the red edge up to ${num(Math.min(...dates.map((s) => s.reip.find((r) => r[0].startsWith("Lagrangian"))[3])), 1)} nm), mesophyll damage (lower NIR) and water loss (higher SWIR), and discrimination peaked (combined pool 93–94 %). On 13-03-2026, with most plants at pod formation and leaves senescing, healthy leaves also lost chlorophyll and water, the contrast narrowed and accuracy fell to ${p1(bestOverall[3])} %.`);
H2("5.2 Growth stage");
P(`The vegetative stage illustrates why pooling can hide a disease effect: neither of its two dates is uninformative, but the difference spectra have opposite signs in the visible and NIR on 11-02 and 24-02-2026, so no reflectance band is significant when they are pooled (Tier 1 fallback). Derivative and continuum-removed features, which describe band shape rather than level, separated the classes on both dates and gave ${p1(vC(stages[0], "QDA on RF features", "V3").BA)} % (QDA on RF features) on new plots — the largest gain of the combined pool over reflectance (${p1(gainC[4])} points). Pod formation was the most difficult subset (best ${p1(bestOverall[5])} %): senescence and pod development change the spectra of healthy leaves in the same direction as the disease, the healthy class is represented by few plots on 03-03-2026, and the combined pool gained nothing over reflectance. Detection at pod formation should therefore rely on earlier measurements.`);
H2("5.3 Varieties");
P(`The three varieties behaved alike: the same regions were selected (red edge, NIR shoulder, water bands), the difference spectra had the same shape with V1 strongest, and the combined pool reached ${rng(vars.map((s) => vC(s, "QDA on RF features", "V3").BA))} on new plots. With only four healthy plots per variety, between-plot variation is large relative to the class difference (V3: no band significant with the mixed model), plot-grouped folds contain one healthy plot each, and validation estimates varied more between folds (V3 SD up to ${p1(Math.max(...vars.map((s) => vC(s, "QDA on RF features", "V3").SD)))} points; V1 exceeded V3 by ${p1(dv1[7])} points in V2). Variety-specific models should therefore be built with more healthy plots per variety.`);
H2("5.4 CART versus Random Forest");
P(`Across subsets, RF was the better classifier and the more stable band selector, as in the pooled analysis. As a selector of bands for QDA (the Tier-2 role in Das et al.), neither method was consistently better on reflectance. In the combined pool the small CART sets (4–12 features) were about as accurate as RF-17 (within ± 5 points in eight subsets; CART better on 11-02-2026, 13-03-2026 and at pod formation, RF-17 clearly better in V3: ${p1(vC(SH["Variety V3"], "QDA on RF features", "V3").BA)} vs ${p1(vC(SH["Variety V3"], "QDA on CART features", "V3").BA)} %). CART remains useful for interpretation (its root split is usually a water or red-edge feature with a clear threshold), but RF importance gives the more reproducible feature ranking.`);
H2("5.5 Disease-sensitive features versus reflectance");
P("The most consistent result of the nine analyses is that first-derivative bands and continuum-removed water-absorption parameters discriminate white rust far better than reflectance bands or broad-band vegetation indices. Derivatives and continuum removal remove the brightness differences between leaves and dates and isolate band shape: the slope of the NIR shoulder (845–885 nm), the shape of the 970 nm and 1940 nm water absorptions and the red-edge slope. The four-tier analysis of the combined pool selects precisely these features and brings J–M above the 1.90 separability threshold in most subsets, which raw reflectance achieved only once (RF bands on 03-03-2026).");
H2("5.6 Transfer and practical use");
P(`Within a date the disease signal is consistent across varieties (V5 ${rng(v5var)}), so a model calibrated on some varieties can be applied to others measured on the same day. Across dates the signal is not stable: a model trained on one or three dates classified an unseen date with ${rng(v5date)} balanced accuracy (RF classifier on the combined pool; QDA on RF features ${rng(S.filter((s) => s.v5_by === "Date").map((s) => vC(s, "QDA on RF features", "V5").BA))}). Practical detection therefore requires date- or stage-specific calibration — for example a few reference healthy and diseased leaves measured at each survey — or features that are normalised against the healthy reference of the same date.`);
H2("5.7 Separate versus pooled analysis");
P(`Compared with the pooled analysis of all 2264 leaves (QDA on CART bands 72.0 %, combined pool 83.7 % on new plots, J–M 1.27 on CART bands), the separate analyses gave higher accuracy and separability on 11-02, 24-02 and 03-03-2026 and in the vegetative stage, similar or slightly lower accuracy in the varieties, and lower accuracy on 13-03-2026 and at pod formation. Separate analyses also reveal what pooling hides: the late onset of a reflectance signal, the sign change between the vegetative dates, and the senescence confound at pod formation.`);
H2("5.8 Limitations");
B(["Healthy vs diseased is a plot-level label; disease severity and leaf position were not used, so mildly infected leaves of inoculated plots are labelled diseased.",
   "Subsets are smaller than the pooled data (428–766 leaves; 4 healthy plots per variety), so validation SDs are larger and J–M and QDA covariances are less well estimated (condition numbers are reported in the cross-checks).",
   "Dates and growth stages are confounded (vegetative on 11-02 and 24-02, pod formation mainly on 13-03-2026).",
   "In the vegetative stage and on 11-02-2026 Tier 1 needed the fallback rule; the results of Tier 2 there rest on bands with uncorrected p < 0.05.",
   "All results refer to leaf-level contact-probe spectra; canopy or airborne data would require masking of the atmospheric water bands."]);

// ============================================================ 6 conclusions
H1("6. Conclusions and recommendations");
B([`White rust changes mustard leaf reflectance on every date, in both growth stages and in every variety, but the size and even the direction of the reflectance change depend on the date: from ${dates[0].n_sig} significant bands on 11-02-2026 to ${dates[2].n_sig} on 03-03-2026.`,
   `The four-tier method of Das et al. (2020) with imbalance correction works within each subset: CART selects ${Math.min(...S.map((s) => s.cart_bands.length))}–${Math.max(...S.map((s) => s.cart_bands.length))} bands in the red edge, green and water-band regions, and QDA with equal priors classifies new plots with ${rng(S.map((s) => vA(s, "QDA on CART features", "V3").BA))} balanced accuracy; J–M on reflectance bands stays below 1.90 except on 03-03-2026 (RF bands).`,
   "Random Forest is the better classifier (8 of 9 subsets) and the more stable selector; as a band selector for QDA neither RF nor CART is consistently better.",
   `First-derivative bands (NIR shoulder 845–885 nm, 1920 nm) and continuum-removed water features (970 nm width, 1940 nm symmetry/area) are the most disease-sensitive features in nearly all subsets; the four tiers on the combined pool reach ${rng(bestOverall)} on new plots and J–M ≥ 1.90 in ${S.filter((s) => s.C_jm_r >= 1.9).length} of 9 subsets.`,
   `Discrimination is best at mid-season (best pipeline ${p1(bestOverall[1])} % on 24-02-2026 and ${p1(bestOverall[2])} % on 03-03-2026) and in the vegetative stage (${p1(bestOverall[4])} %), and weakest at pod formation (${p1(bestOverall[5])} %) because of senescence.`,
   "Models transfer across varieties within a date but not across dates; calibrate per date or growth stage."]);
H2("Recommendations");
B(["For detection, use the combined pool reduced to RF-selected first-derivative and continuum-removed features, classified by QDA with equal priors or by a Balanced RF; report balanced accuracy and both class recalls.",
   "Measure at mid-season (flowering to early pod set) when the contrast is largest; at pod formation, include senescence-aware features or rely on earlier dates.",
   "Validate with folds grouped by plot and test on new dates; include healthy reference leaves from every date in the calibration.",
   "Use at least 8–10 healthy plots per variety for variety-specific models, and record a disease-severity score per leaf in future campaigns."]);

// ============================================================ references
H1("References");
REFS.forEach((r) => body.push(new Paragraph({ children: runs(r, { size: 20 }), spacing: { after: 80 }, indent: { left: 360, hanging: 360 } })));

// ============================================================ appendix
pageBreak();
H1("Appendix A. Cross-check summary by subset");
table([["Subset", "PASS", "FLAG", "FAIL", "Flagged items (limitations reported in the workbook)"],
  ...S.map((s) => [s.short, s.checks.PASS, s.checks.FLAG, s.checks.FAIL, s.flags.map((f) => f[1]).join("; ")])],
  "Cross-checks of each subset analysis (all workbooks recalculated in LibreOffice with 0 formula errors).", [1.4, 0.6, 0.6, 0.6, 5.2], 15);
H1("Appendix B. The nine workbooks");
table([["Workbook", "Subset"], ...S.map((s, i) => [`${String(i + 1).padStart(2, "0")}_WhiteRust_Mustard_Leaf_${s.key.slice(3)}_FourTier_CART_RF_K_Combined.xlsx`, s.label])],
  "Excel workbooks (39 sheets each: README, summary, design, Steps 0–6, Part A1–A4, Part K0–K6, Part C0–C7, V5, strata, cross-checks, band-by-band and feature tables, folds, chart data).", [5, 2]);

// ============================================================ document
const doc = new Document({
  creator: "Animesh Panda", title: "White rust in mustard — nine subset analyses", description: "Four-tier analysis by date, growth stage and variety",
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
