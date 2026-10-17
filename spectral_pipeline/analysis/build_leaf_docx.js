// Detailed Word report of the three leaf-level analyses (L3, L5, LL; all dates, growth stages and varieties combined).
// Full names throughout (no V1-V5 / K1-K4 codes). Input: work_subsets/report_leaf/subsets.json and figures (export_leaf_report.py).
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
const GN = { G0: "Full raw spectrum", G1: "Band reflectance", G2: "Continuum-removal features", G3: "Vegetation indices",
             G4: "Derivatives + edge parameters", G5: "All disease-sensitive features combined", G6: "Derivatives incl. guard bands (artefact test)", GS: "15 selected features" };
const VN = { V1: "Leaf-level 10-fold cross-validation", V2: "Plot-grouped cross-validation", V3: "Nested plot-grouped cross-validation",
             V4: "30 % plot hold-out validation", V5: "Leave-one-date-out validation on new plots" };
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

// ============================================================ derived facts
const L = Object.fromEntries(S.map((s) => [s.level, s]));
const LV = S.map((s) => s.level);
const rng = (arr) => `${p1(Math.min(...arr))}–${p1(Math.max(...arr))} %`;
const best = (s, part) => PIPES.map((p) => [p, (part === "A" ? vA : vC)(s, p, "V3").BA]).sort((a, b) => b[1] - a[1])[0];
const bestK = (s) => ["G1", "G2", "G3", "G4", "G5"].map((g) => [g, k5(s, g, "RF")]).sort((a, b) => b[1] - a[1])[0];
const wil = (s, cmp) => s.wil_A.find((r) => r.Comparison.startsWith(cmp) && r.Units.startsWith("Nested"));
const gainC = S.map((s) => vC(s, "QDA on RF features", "V3").BA - vA(s, "QDA on CART features", "V3").BA);
const lvlist = (f, d = 1) => S.map((s) => `${s.level} ${typeof f(s) === "number" ? (d === "pct" ? p1(f(s)) + " %" : num(f(s), d)) : f(s)}`).join(", ");
const reipL = (s) => s.reip.find((r) => r[0].startsWith("Lagrangian"));
const VALCOLS = ["Leaf-level 10-fold CV", "Nested plot-grouped CV (± SD)", "30 % plot hold-out (± SD)", "Leave-one-date-out (new date and plots)"];
const vrowTab = (s, f, cap) => table([["Pipeline", "Leaf-level 10-fold cross-validation", "Nested plot-grouped cross-validation (± SD)", "30 % plot hold-out validation (± SD)", "Leave-one-date-out validation on new plots", "AUC (nested)", "κ (nested)"],
  ...PIPES.map((p) => [p, pct(f(s, p, "V1").BA), `${pct(f(s, p, "V3").BA)} ± ${p1(f(s, p, "V3").SD)}`, `${pct(f(s, p, "V4").BA)} ± ${p1(f(s, p, "V4").SD)}`,
    pct(f(s, p, "V5").BA), num(f(s, p, "V3").AUC), num(f(s, p, "V3").kappa)])], cap, [2, 1.3, 1.6, 1.6, 1.5, 0.9, 0.8], 15);

// ============================================================ title page
body.push(new Paragraph({ spacing: { before: 2200, after: 240 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Discrimination of healthy and white-rust-diseased mustard leaves at three leaf levels (L3, L5 and LL)", bold: true, size: 40, color: "1F3D2B" })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "Four-tier hierarchical analysis (Das et al., 2020) with imbalance correction on raw reflectance and on the combined disease-sensitive features, CART versus Random Forest, honest validation on new plots and new dates — all dates, growth stages and varieties combined", size: 26, italics: true })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: `Leaf level · ASD FieldSpec contact probe · ${S.map((s) => `${s.level}: ${s.n} leaves (${s.nH} healthy, ${s.nD} diseased)`).join(" · ")}`, size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: "Animesh Panda · Division of Agricultural Physics, ICAR-Indian Agricultural Research Institute, New Delhi", size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Methods, results and interpretation · companion to the three Excel workbooks (WhiteRust_LeafLevels)", size: 20, color: "52514E" })] }));
pageBreak();
body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Contents")] }));
body.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }));
body.push(new Paragraph({ children: [new TextRun({ text: "(Right-click → Update field in Word to refresh the page numbers.)", italics: true, size: 18, color: "52514E" })] }));
pageBreak();

// ============================================================ summary
H1("Summary");
P(`Leaf reflectance spectra (350–2500 nm, 1 nm) of healthy and white-rust (_Albugo candida_) diseased mustard leaves were analysed separately for three leaf levels — L3, L5 and LL — with all four measurement dates, the three growth stages and the three varieties combined in each analysis (${S.map((s) => `${s.level}: ${s.nH} healthy and ${s.nD} diseased leaves`).join("; ")}; 12 healthy and 36 diseased plots each). The leaf levels were taken from the leaf-level workbooks supplied for this analysis; plot, variety and growth stage were attached by exact spectral matching to the labelled ASD workbooks, so that every validation could keep the leaves of one plot together.`);
P(`At each leaf level the four-tier hierarchical method of Das et al. (2020) was applied twice: first on raw reflectance (2101 bands, 400–2500 nm) and then on the combined pool of disease-sensitive features (band reflectance + continuum-removal features + vegetation indices + derivative and edge features, ${S[0].C_nfeat} features). Tier 1 used Welch's t-test with the Benjamini–Hochberg false-discovery rate, Tier 2 CART (rpart) band selection with equal priors — repeated with a Balanced Random Forest as the alternative selector — Tier 3 the Jeffries–Matusita (J–M) distance and Tier 4 quadratic discriminant analysis (QDA) with equal priors. The 1 : 5 imbalance between healthy and diseased leaves was corrected throughout (equal priors, balanced bootstrap samples, balanced accuracy as the headline metric), and every result was validated by leaf-level 10-fold cross-validation (the protocol of Das et al.), nested plot-grouped cross-validation, a 30 % plot hold-out and leave-one-date-out validation on new plots.`);
P(`On raw reflectance, ${lvlist((s) => s.n_sig, 0)} of 2101 bands differed significantly between healthy and diseased leaves. CART selected ${lvlist((s) => s.cart_bands.length, 0)} bands; J–M on the CART bands was ${lvlist((s) => s.jm_c, 2)} and on the 17 Random Forest importance peaks ${lvlist((s) => s.jm_r, 2)}. QDA with equal priors on the CART bands classified new plots (nested plot-grouped cross-validation) with a balanced accuracy of ${lvlist((s) => vA(s, "QDA on CART features", "V3").BA, "pct")}. On the combined feature pool QDA on the 17 Random Forest-selected features reached ${lvlist((s) => vC(s, "QDA on RF features", "V3").BA, "pct")}, and the best pipeline ${lvlist((s) => best(s, "C")[1], "pct")}; the selected features were mainly first-derivative bands and continuum-removed water-absorption parameters. Transfer to an unseen date in unseen plots was much weaker (Random Forest classifier on the combined pool: ${lvlist((s) => vC(s, "RF classifier", "V5").BA, "pct")}).`);

// ============================================================ 1 introduction
H1("1. Introduction");
P("White rust (_Albugo candida_) produces white pustules and chlorosis on mustard leaves, changing leaf pigments, structure and water content and hence the leaf reflectance spectrum. Leaves at different positions on the plant differ in age and exposure, so the spectral signature of the disease may differ between leaf levels. Earlier analyses pooled all leaves (2264 spectra) or analysed each date, growth stage and variety separately. This report analyses each leaf level separately, with all dates, growth stages and varieties combined, to answer:");
B(["Which wavelengths and disease-sensitive features discriminate healthy and diseased leaves at leaf levels L3, L5 and LL?",
   "How separable are the classes (J–M distance) and how accurately can they be classified (QDA, CART, Random Forest) at each leaf level, on new plots and on new dates?",
   "Is Random Forest a better band selector and classifier than CART, and does the combined pool of disease-sensitive features improve on raw reflectance?",
   "Which leaf level is best suited for detecting white rust?"]);
P("Each leaf level has its own Excel workbook (40 sheets, including a glossary) with every table, figure and cross-check; this report collects the results, explains the methods and compares the three leaf levels. Validation schemes and feature steps are written out in full in both.");

// ============================================================ 2 methods
pageBreak();
H1("2. Materials and methods");
H2("2.1 Data: leaf-level workbooks and plot information");
P(`Three workbooks with leaf-level spectra were supplied: 2_date.xlsx (11-02-2026 and 24-02-2026, healthy and diseased sheets), 2_more_date.xlsx (03-03-2026 healthy and diseased, 13-03-2026 healthy) and lased_date_diseased.xlsx (13-03-2026 diseased). Each sheet holds one column per leaf spectrum (350–2500 nm, 1 nm) whose header is the leaf level L3, L5 or LL; ${S[0].leaf_n || 2267} spectra in all. Plot-average columns were not used (leaf level only), and disease score was not used: the response is healthy vs diseased.`);
P("The sheets carry no plot numbers. Because leaves of one plot share the plot environment, an honest validation must keep them together, so every spectrum was matched exactly (all 2151 bands identical) to the labelled ASD export workbooks of the four dates, which give plot, variety and growth stage. All spectra matched, and the healthy/diseased label and the date of every sheet agreed with the labelled files. Four spectra of plot 27 on 11-02-2026 (Mustard00215–00218) occur twice in the leaf-level sheet (two L3 and two L5 pairs of identical columns); one copy of each was kept, as in the earlier analyses. One labelled spectrum (Mustard00574, plot 44, 03-03-2026, diseased) is not in the leaf-level workbooks and was not used.");
table([["Leaf level", "Leaves (healthy / diseased)", "Ratio diseased : healthy", "Plots (healthy / diseased)", "Leaves per plot and date", "Growth stages"],
  ...S.map((s) => [s.level, `${s.n} (${s.nH} / ${s.nD})`, (s.nD / s.nH).toFixed(1), `${s.pH} / ${s.pD}`, "3 (healthy), 5 (diseased)", s.stages.join(", ")])],
  "The three leaf-level data sets (all four dates and three varieties in each).", [1, 1.8, 1.2, 1.4, 1.5, 2.2]);
table([["Leaf level", "Date", "Healthy", "Diseased"], ...S.flatMap((s) => s.by_date.map((r) => [s.level, r.Date, r.Healthy, r.Diseased]))],
  "Leaf spectra by leaf level, date and class.", [1, 1.5, 1, 1]);
P("LL leaves are scarce on the first dates (on 11-02-2026 only 9 healthy and 45 diseased LL leaves), so the LL data set is dominated by the flowering and pod-formation dates, whereas L3 and L5 are balanced over the four dates.");
H2("2.2 Pre-processing");
P("The contact probe illuminates the leaf with its own lamp at a few millimetres, so there is no atmospheric path; the water-absorption bands (1350–1430, 1800–1950, 2350–2500 nm), which Das et al. (2020) removed for canopy data, were kept because they carry leaf-water information. The noisy 350–399 nm detector edge was removed. The four tiers on raw reflectance used the reflectance of 400–2500 nm (2101 bands) without smoothing, as in Das et al. The disease-sensitive features used splice-corrected (detector joins at 1000/1001 and 1800/1801 nm) and Savitzky–Golay-smoothed spectra (window 11, order 2), with guard zones next to the joins excluded from the rankings.");
H2("2.3 The four-tier method with imbalance correction");
P("**Tier 1 — statistical screening.** With two classes the one-way ANOVA of Das et al. reduces to a two-sample test; Welch's unequal-variance t-test was applied at every band and the p-values adjusted with the Benjamini–Hochberg false-discovery rate (q < 0.05):");
EQ("t = (x̄_D − x̄_H) / √(s²_D/n_D + s²_H/n_H),     q₍ᵢ₎ = min_{k ≥ i} p₍ₖ₎ · m / k");
P("Checks: one-way ANOVA (rule of Das et al.), 1000 balanced random subsets with equal numbers of healthy and diseased leaves, and a linear mixed model with a random plot intercept (leaves nested in plots). The −log₁₀(p) of every band was plotted against wavelength.");
P("**Tier 2 — CART band selection** (R rpart; Gini splitting, minsplit 20, minbucket 7, cp 0.01) with **prior = c(0.5, 0.5)** so that the minority healthy class weighs as much as the diseased class. The bands used as split variables form the CART set. **Random Forest as the alternative selector:** a Balanced Random Forest (each tree on a bootstrap sample with equal numbers of healthy and diseased leaves; 1000 trees, √p candidate bands per split); importance = mean decrease in Gini impurity; the 17 highest importance peaks at least 10 nm apart form the Random Forest band set (RF-17).");
P("**Tier 3 — Jeffries–Matusita distance** on the selected bands (class means μ, covariance matrices Σ):");
EQ("α = ⅛ (μ_H − μ_D)ᵀ [(Σ_H + Σ_D)/2]⁻¹ (μ_H − μ_D) + ½ ln{ |(Σ_H + Σ_D)/2| / √(|Σ_H| |Σ_D|) },     J–M = 2 (1 − e^(−α))");
P("J–M ranges from 0 to 2; the classes are called separable at J–M ≥ 1.90 (Das et al. used 1.94).");
P("**Tier 4 — quadratic discriminant analysis** with **equal prior probabilities** (π_H = π_D = 0.5; sample priors would favour 'diseased'), summarised in an error matrix (rows = classified, columns = reference) with producer's and user's accuracy, overall accuracy, Cohen's κ and the **balanced accuracy** = ½ (recall of healthy + recall of diseased), the headline metric because overall accuracy is dominated by the large diseased class.");
H2("2.4 Validation");
B(["**Leaf-level 10-fold cross-validation** — bands chosen once on all leaves, leaves split at random into 10 folds (the protocol of Das et al.). Optimistic: leaves of one plot are in training and test, and selection and evaluation use the same leaves.",
   "**Plot-grouped cross-validation** — bands fixed, folds formed from whole plots (removes plot leakage).",
   "**Nested plot-grouped cross-validation** — Tier 1, band selection and classifier refitted inside every training set; 10 plot-grouped folds × 5 repeats (50 training sets), folds grouped by plot across all dates and every test fold containing both classes. The honest estimate for new plots.",
   "**30 % plot hold-out validation** — 30 % of the plots of each class (4 healthy + 11 diseased) held out, everything refitted on the rest; 10 random splits.",
   "**Leave-one-date-out validation on new plots** — train on three dates (training plots of a hold-out split), test on the fourth date (test plots of the split); 10 splits × 4 dates. No leaf, plot or date of the test set is seen in training.",
   "**Nested plot-grouped cross-validation with random under-sampling** — as nested cross-validation but diseased leaves randomly under-sampled to the number of healthy leaves, as an alternative imbalance correction."]);
P("Paired Wilcoxon signed-rank tests compare pipelines on identical folds. When a training set has fewer than two FDR-significant bands, Tier 2 receives the bands with uncorrected p < 0.05 (flagged in the cross-checks).");
H2("2.5 Disease-sensitive feature extraction");
B(["**Smoothing and detector-join correction** — splice correction, Savitzky–Golay smoothing and derivatives, guard zones.",
   "**Band reflectance** — smoothed reflectance at every band: Welch t + FDR, Hedges' g, AUC and a threshold classifier validated on plots.",
   "**Continuum-removal features** — depth, position, area, width and symmetry of six absorption features (495, 675, 970, 1200, 1450, 1940 nm) after division by the upper convex hull (Clark and Roush, 1984; Kokaly and Clark, 1999).",
   "**Vegetation indices** — the 31 indices of the flowering-stage workbook, plus the optimised two-band normalised-difference index searched over all band pairs (pairs straddling a detector join excluded; search repeated inside training plots).",
   "**Derivative and edge features** — first-derivative bands, 20 edge parameters and the red-edge inflection point by four methods (maximum first derivative; linear four-point, Guyot and Baret, 1988; Lagrangian, Dawson and Curran, 1998; linear extrapolation, Cho and Skidmore, 2006).",
   "**Correlation spectra** and **CART vs Random Forest on each feature group** — point-biserial correlation with disease status; CART and Balanced Random Forest fitted to each feature family on identical plot-grouped folds."]);
H2("2.6 Four tiers on the combined feature pool");
P(`All band-reflectance, continuum-removal, vegetation-index, first-derivative and edge features were pooled (${S[0].C_nfeat} features after removing exact duplicates), and the same four tiers, settings and validation folds were applied: Welch + FDR, CART and Random Forest selection, J–M and QDA with equal priors.`);
H2("2.7 Cross-checks and software");
P("Each step was cross-checked by an independent implementation or recomputation (Welch t vs SciPy; FDR vs statsmodels; ANOVA F = t²; mixed model R nlme vs statsmodels; rpart vs scikit-learn trees; QDA vs manual discriminant functions and R MASS::qda; J–M by Cholesky vs explicit inverse; Random Forest importance vs a second seed, R randomForest and permutation importance; continuum removal, indices and red-edge position recomputed by Excel formulas; assertions that no plot, and in leave-one-date-out no date, is in training and test). Software: Python 3.13 (NumPy, SciPy, pandas, statsmodels, scikit-learn, imbalanced-learn, matplotlib, openpyxl) and R 4.3.3 (rpart, MASS, nlme, randomForest).");
figure("workflow.png", "Workflow of each leaf-level analysis.", 600);

// ============================================================ 3 overview across leaf levels
pageBreak();
H1("3. Results: comparison of the three leaf levels");
H2("3.1 Spectra of healthy and diseased leaves");
figure("X10_mean_spectra_grid.png", "Mean reflectance of healthy (aqua) and diseased (orange) leaves at each leaf level (n = healthy / diseased).", 620);
figure("X4_difference_spectra.png", "Difference spectra (mean diseased − mean healthy reflectance, %) at the three leaf levels.", 600);
P(DIFFTXT);
H2("3.2 Tier 1 — how many bands differ");
table([["Leaf level", "Welch t-test + FDR (of 2101)", "Mixed model (plot effect) + FDR", "Significant in ≥ 95 % of balanced subsets", "Most sensitive band (nm)", "AUC", "Bands with AUC ≥ 0.70"],
  ...S.map((s) => [s.level, s.n_sig, s.n_mm, s.tier1_tests.find((t) => t[0].startsWith("Balanced"))[1], num(s.k1_best[0], 0), num(s.k1_best[1]), s.k1_best[2]])],
  "Tier 1 results by leaf level (raw reflectance, 400–2500 nm).", [1, 1.3, 1.4, 1.5, 1.2, 0.7, 1]);
figure("X3_significance_spectra.png", "Significance spectra: −log₁₀ q of the Welch t-test (Benjamini–Hochberg) against wavelength at the three leaf levels (dashed line q = 0.05; symmetric-log scale).", 620);
P(T1TXT);
H2("3.3 Tier 2 — bands selected by CART and by Random Forest");
figure("X6_selected_bands.png", "Bands selected by CART (blue triangles) and the 17 Random Forest importance peaks (orange dots) at each leaf level (raw reflectance).", 620);
table([["Leaf level", "CART set", "Root band (nm)", "CART bands (nm, order of use)", "Random Forest peaks RF-17 (nm, by importance)"],
  ...S.map((s) => [s.level, s.cart_name, s.root, s.cart_bands.join(", "), s.rf_bands.join(", ")])], "Tier 2 band sets by leaf level.", [0.8, 0.9, 0.8, 3.2, 3.6], 15);
H2("3.4 Tier 3 — separability (Jeffries–Matusita distance)");
figure("X7_jm_by_subset.png", "J–M distance on the CART and RF-17 sets, raw reflectance and combined feature pool, by leaf level (dashed 1.90, dotted 1.94).", 600);
table([["Leaf level", "Raw reflectance: CART bands", "Raw reflectance: RF-17", "Combined pool: CART features", "Combined pool: RF-17"],
  ...S.map((s) => [s.level, `${num(s.jm_c)} (${s.cart_name})`, num(s.jm_r), `${num(s.C_jm_c)} (${s.C_cart_name})`, num(s.C_jm_r)])], "J–M distance (0–2) by leaf level.", [1, 1.8, 1.4, 1.8, 1.4]);
P(JMTXT);
H2("3.5 Tier 4 and validation — accuracy on new plots");
table([["Leaf level", ...PIPES.map((p) => `Raw reflectance: ${p}`), ...PIPES.map((p) => `Combined pool: ${p}`)],
  ...S.map((s) => [s.level, ...PIPES.map((p) => p1(vA(s, p, "V3").BA)), ...PIPES.map((p) => p1(vC(s, p, "V3").BA))]),
  ["All leaves pooled (earlier analysis)", ...PIPES.map((p) => p1(REF.vA[`${p}|V3`].BA)), ...PIPES.map((p) => p1(REF.vC[`${p}|V3`].BA))]],
  "Balanced accuracy (%) of the four pipelines under nested plot-grouped cross-validation (new plots), raw reflectance and combined feature pool.", [1.6, 1, 1, 1.1, 1, 1, 1, 1.1, 1], 15);
figure("X1_pipelines_by_subset.png", "Balanced accuracy on new plots (nested plot-grouped cross-validation) of the four pipelines, raw reflectance (top) and combined feature pool (bottom). Dashed line: all leaves pooled.", 620);
figure("X2_validation_schemes.png", "Combined feature pool: balanced accuracy of QDA on Random Forest features and of the Random Forest classifier under the four validation schemes.", 620);
P(VALTXT);
H2("3.6 CART versus Random Forest");
table([["Leaf level", "Random Forest − CART classifier", "Random Forest better (folds)", "p", "QDA: Random Forest − CART bands", "p", "Stability (Jaccard) Random Forest / CART"],
  ...S.map((s) => { const a = wil(s, "RF classifier"), b = wil(s, "QDA on RF");
                    return [s.level, `${(100 * a["Mean difference"]).toFixed(1)} points`, `${a["First better"]} / ${a.n}`, pv(a["Wilcoxon p"]),
                            `${(100 * b["Mean difference"]).toFixed(1)} points`, pv(b["Wilcoxon p"]), `${num(s.stab_A.RF.jacc, 2)} / ${num(s.stab_A.CART.jacc, 2)}`]; })],
  "CART versus Random Forest on raw reflectance: paired Wilcoxon tests over the 50 nested cross-validation folds (positive = Random Forest better) and stability of the selected bands (mean pairwise Jaccard index, ± 10 nm).", [1, 1.5, 1.2, 0.8, 1.5, 0.8, 1.5]);
P(CRTXT);
H2("3.7 Disease-sensitive features");
figure("X5_k5_heatmap.png", "Balanced accuracy of a Balanced Random Forest on each feature group, by leaf level (nested plot-grouped cross-validation).", 600);
table([["Leaf level", "Best feature group (Random Forest)", "Best first-derivative band (AUC)", "Best continuum-removal parameter (AUC)", "Best vegetation index (AUC)", "Best edge parameter (AUC)"],
  ...S.map((s) => { const b = bestK(s); return [s.level, `${GN[b[0]]} ${p1(b[1])} %`, `${s.d1_top[0][0]} nm (${num(s.d1_top[0][1], 2)})`,
                   `${s.k2_top[0][0]} (${num(s.k2_top[0][1], 2)})`, `${s.k3_top[0][0]} (${num(s.k3_top[0][1], 2)})`, `${s.k4e_top[0][0]} (${num(s.k4e_top[0][1], 2)})`]; })],
  "Most informative feature group and most sensitive single features, by leaf level (AUC is direction-free: 0.5 = no separation).", [0.8, 1.9, 1.3, 2.1, 1.3, 2.1], 15);
P(KTXT);
H2("3.8 Red-edge shift and transfer to new dates");
figure("X9_reip_transfer.png", "Left: red-edge inflection point shift (diseased − healthy, Lagrangian method). Right: Random Forest classifier on the combined pool, nested plot-grouped cross-validation vs leave-one-date-out validation on new plots.", 600);
P(REIPTXT);
H2("3.9 What the selectors chose from the combined pool");
figure("X8_partC_types.png", "Feature types chosen by CART and by Random Forest (RF-17) from the combined pool, by leaf level.", 600);
P(POOLTXT);

// ============================================================ 4 per leaf level
function levelChapter(s, idx) {
  pageBreak();
  H1(`4.${idx} Leaf level ${s.level}`);
  const T = s.txt || {};
  H2(`4.${idx}.1 Data and validation design`);
  P(`${s.n} leaf spectra (${s.nH} healthy, ${s.nD} diseased; ratio 1 : ${(s.nD / s.nH).toFixed(1)}) from ${s.pH} healthy and ${s.pD} diseased plots, measured on ${s.dates.join(", ")}; growth stages ${s.stages.join(", ")}; varieties ${s.varieties.join(", ")}. Nested plot-grouped cross-validation used ${s.k3} plot-grouped folds × 5 repeats (${s.nV3} training sets); the 30 % plot hold-out held out ${s.v4[0]} healthy + ${s.v4[1]} diseased plots × 10; leave-one-date-out validation on new plots had ${s.nV5} units${s.v5_dropped ? ` (${s.v5_dropped} skipped)` : ""}.`);
  table([["Date", "Growth stage", "Healthy", "Diseased"], ...s.by_stage.map((r) => [r.Date, r["Growth stage"], r.Healthy, r.Diseased])],
    `Leaf level ${s.level}: leaf spectra by date and growth stage.`, [2, 2, 1, 1]);
  figure(s.figs.mean, `Leaf level ${s.level}: mean reflectance of healthy and diseased leaves (± 1 SD).`, 520);
  figure(s.figs.bydate, `Leaf level ${s.level}: mean spectra of healthy and diseased leaves on each date.`, 600);
  H2(`4.${idx}.2 Tier 1 — statistical screening on raw reflectance`);
  table([["Test", "Significant bands (of 2101)"], ...s.tier1_tests.map((t) => [t[0], t[1]])], `Leaf level ${s.level}: number of significant bands by test.`, [5, 1.5]);
  if (s.ranges.length) table([["Contiguous significant range (nm)", "Bands"], ...s.ranges.map((r) => [r["Range (nm)"], r.Bands])], `Leaf level ${s.level}: largest contiguous ranges of significant bands.`, [3, 1]);
  table([["Band (nm)", "Mean healthy", "Mean diseased", "Welch t", "q (FDR)", "Hedges g", "AUC"], ...s.top_bands.map((r) => [r[0], num(r[1], 4), num(r[2], 4), num(r[3], 2), r[4] == null ? "–" : Number(r[4]).toExponential(2), num(r[5], 2), num(r[6], 3)])],
    `Leaf level ${s.level}: ten bands with the largest |t|.`, [1, 1, 1, 1, 1.2, 1, 0.8]);
  figure(s.figs.logp, `Leaf level ${s.level}: −log₁₀(p) against wavelength (Welch p, FDR q and mixed-model q; dashed p or q = 0.05).`, 560);
  H2(`4.${idx}.3 Tier 2 — CART and Random Forest band selection`);
  table([["Band (nm)", "Region", "First used at node", "Bootstrap re-selection", "Nested cross-validation re-selection"],
    ...s.cart_table.map((r) => [r[0], r[1], r[2], pct(r[3]), pct(r[4])])], `Leaf level ${s.level}: the ${s.cart_name} bands selected by rpart (prior 0.5/0.5) and how often a band within ± 10 nm is re-selected.`, [1, 2, 1, 1.3, 1.5]);
  figure(s.figs.tree, `Leaf level ${s.level}: CART tree on the Tier-1 bands (${s.cart_name}).`, 600);
  P(`Random Forest importance peaks (RF-17): ${s.rf_bands.join(", ")} nm.`);
  figure(s.figs.rfimp, `Leaf level ${s.level}: Balanced Random Forest importance spectrum with the RF-17 peaks and the CART bands.`, 560);
  H2(`4.${idx}.4 Tier 3 and Tier 4 — separability and classification`);
  table([["Band set", "Bands", "α (Bhattacharyya)", "J–M (0–2)", "√J–M", "Separability"], ...s.tier3.map((r) => [r[0], r[1], num(r[2]), num(r[3]), num(r[4]), sepWord(r[3])])],
    `Leaf level ${s.level}: Jeffries–Matusita distance of healthy and diseased leaves.`, [2, 0.8, 1.2, 1, 0.9, 2]);
  table(em(s.em_cart), `Leaf level ${s.level}: error matrix of QDA (equal priors) on the ${s.cart_name} bands, leaf-level 10-fold cross-validation (as Table 2 of Das et al.).`, [2, 1, 1, 1, 1.2]);
  table(em(s.em_rf), `Leaf level ${s.level}: error matrix of QDA (equal priors) on the ${s.rf_name} bands, leaf-level 10-fold cross-validation.`, [2, 1, 1, 1, 1.2]);
  table([["Band set", "Classifier", "Overall accuracy", "Balanced accuracy", "Recall healthy", "Recall diseased", "κ"], ...s.tier4.map((r) => [r[0], r[1], pct(r[2]), pct(r[3]), pct(r[4]), pct(r[5]), num(r[6])])],
    `Leaf level ${s.level}: Tier 4 on all band sets (leaf-level 10-fold cross-validation), equal and sample priors and LDA.`, [1.8, 2, 1, 1, 1, 1, 0.8]);
  H2(`4.${idx}.5 Validation and CART versus Random Forest (raw reflectance)`);
  vrowTab(s, vA, `Leaf level ${s.level}: balanced accuracy of the four pipelines on raw reflectance under each validation scheme.`);
  table([["Validation scheme", "Priors", "Balanced accuracy", "SD", "Overall accuracy", "Recall healthy", "Recall diseased"], ...s.val_qda.map((r) => [r[0], r[1], pct(r[2]), r[3] == null ? "–" : p1(r[3]), pct(r[4]), pct(r[5]), pct(r[6])])],
    `Leaf level ${s.level}: validation of QDA on CART bands — equal priors (imbalance correction) vs sample priors, and random under-sampling.`, [2.8, 1.5, 0.9, 0.6, 0.9, 0.9, 0.9], 15);
  figure(s.figs.pipesA, `Leaf level ${s.level}: CART and Random Forest as classifiers and as band selectors for QDA (raw reflectance).`, 580);
  table([["Comparison", "Validation", "n", "Mean difference", "First better", "Wilcoxon p"],
    ...s.wil_A.map((r) => [r.Comparison, r.Units, r.n, `${(100 * r["Mean difference"]).toFixed(1)} points`, r["First better"], pv(r["Wilcoxon p"])])],
    `Leaf level ${s.level}: paired comparisons on identical folds (positive = first pipeline better).`, [3, 2, 0.5, 1, 0.9, 1], 15);
  figure(s.figs.stabA, `Leaf level ${s.level}: re-selection of the CART and Random Forest bands in the nested training sets.`, 580);
  H2(`4.${idx}.6 Disease-sensitive features`);
  table([["Family", "Feature", "AUC", "Direction", "Balanced accuracy, plot-grouped", "Balanced accuracy, hold-out"],
    ...s.k2_top.slice(0, 3).map((r) => ["Continuum removal", r[0], num(r[1]), r[2], pct(r[4]), pct(r[5])]),
    ...s.k3_top.slice(0, 3).map((r) => ["Vegetation index", r[0], num(r[1]), r[2], pct(r[4]), pct(r[5])]),
    ...s.k4e_top.slice(0, 2).map((r) => ["Edge parameter", r[0], num(r[1]), r[2], pct(r[4]), pct(r[5])]),
    ...s.d1_top.slice(0, 3).map((r) => ["First derivative", `${r[0]} nm`, num(r[1]), r[2], "–", "–"]),
    ...[...s.k1_regions].sort((a, b) => b[2] - a[2]).slice(0, 2).map((r) => ["Band reflectance", `${r[0]} nm (${r[1]})`, num(r[2]), r[3], pct(r[4]), "–"]),
    ...s.k3b.map((r) => ["Optimised two-band index", r[0], num(r[1]), "", pct(r[2]), "–"])],
    `Leaf level ${s.level}: most sensitive single features of each family (threshold classifier validated on plots).`, [1.6, 2.4, 0.7, 0.8, 1.2, 1.1]);
  table([["Feature group", "CART (nested)", "Random Forest (nested)", "CART (hold-out)", "Random Forest (hold-out)"],
    ...["G0", "G1", "G2", "G3", "G4", "G5", "G6", "GS"].filter((g) => k5(s, g, "RF") != null).map((g) => [GN[g], pct(k5(s, g, "CART")), pct(k5(s, g, "RF")), pct(k5(s, g, "CART", "Hold-out")), pct(k5(s, g, "RF", "Hold-out"))])],
    `Leaf level ${s.level}: CART vs Balanced Random Forest on each feature group (balanced accuracy).`, [3, 1, 1.2, 1, 1.2]);
  figure(s.figs.k5, `Leaf level ${s.level}: CART vs Random Forest on each disease-sensitive feature group.`, 560);
  figure(s.figs.k1auc, `Leaf level ${s.level}: AUC of every band, band reflectance and first derivative.`, 560);
  table([["Red-edge inflection point method", "Healthy (nm)", "Diseased (nm)", "Shift (nm)", "AUC", "Balanced accuracy, plot-grouped"], ...s.reip.map((r) => [r[0], num(r[1], 1), num(r[2], 1), num(r[3], 2), num(r[4]), pct(r[5])])],
    `Leaf level ${s.level}: red-edge inflection point by four methods.`, [2.4, 1, 1, 0.9, 0.8, 1.3]);
  figure(s.figs.reip, `Leaf level ${s.level}: red-edge inflection point by method and by date.`, 560);
  H2(`4.${idx}.7 Four tiers on the combined feature pool`);
  P(`Tier 1: ${s.C_nsig} of ${s.C_nfeat} features significant. Tier 2: CART selected ${s.C_cart.length} features (${s.C_cart.map(featName).join(", ")}); Random Forest RF-17: ${s.C_rf.map(featName).join(", ")}. Tier 3: J–M ${num(s.C_jm_c)} (CART set) and ${num(s.C_jm_r)} (RF-17), ${sepWord(s.C_jm_r)} for RF-17.`);
  table([["Feature type", "Features", "Tier-1 significant", s.C_cart_name, s.C_rf_name], ...s.C_comp.map((r) => [r[0], r[1], r[2], r[3], r[4]])],
    `Leaf level ${s.level}: composition of the combined pool and of the selected sets.`, [2.4, 1, 1.2, 1, 1]);
  table(em(s.C_em_rf), `Leaf level ${s.level}: error matrix of QDA (equal priors) on the RF-17 features of the combined pool, leaf-level 10-fold cross-validation.`, [2, 1, 1, 1, 1.2]);
  vrowTab(s, vC, `Leaf level ${s.level}: balanced accuracy of the four pipelines on the combined pool under each validation scheme.`);
  figure(s.figs.pipesC, `Leaf level ${s.level}: four pipelines on the combined pool under the four validation schemes.`, 580);
  figure(s.figs.ctop, `Leaf level ${s.level}: the 30 most important features of the combined pool (Balanced Random Forest).`, 520);
  const cw = s.cross.filter((r) => r[2].startsWith("Nested"));
  table([["First", "Second", "Mean difference", "First better / n", "Wilcoxon p"], ...cw.map((r) => [r[0], r[1], `${(100 * r[3]).toFixed(1)} points`, `${r[4]} / ${r[5]}`, pv(r[6])])],
    `Leaf level ${s.level}: combined pool vs raw reflectance vs single feature groups (paired over the nested cross-validation folds).`, [2.6, 2.6, 0.9, 1, 0.9], 15);
  H2(`4.${idx}.8 Transfer to an unseen date (leave-one-date-out validation on new plots)`);
  const lv = [...new Set(s.lodo.map((r) => r[2]))];
  table([["Feature set · pipeline", ...lv.map((d) => `Held-out ${d}`)],
    ...[...new Set(s.lodo.map((r) => `${r[0]} · ${r[1]}`))].map((k) => [k, ...lv.map((l) => { const r = s.lodo.find((q) => `${q[0]} · ${q[1]}` === k && q[2] === l); return r ? pct(r[4]) : "–"; })])],
    `Leaf level ${s.level}: balanced accuracy on each held-out date (trained on the other three dates, tested on new plots of the held-out date).`, [3, ...lv.map(() => 1)]);
  figure(s.figs.v5, `Leaf level ${s.level}: leave-one-date-out validation on new plots, by held-out date.`, 540);
  H2(`4.${idx}.9 Interpretation`);
  (T.conclusions || []).slice(1).forEach((t) => P(t));
  if (T.recommendations) { H3(`Recommendations for leaf level ${s.level}`); B(T.recommendations); }
  H3("Cross-checks");
  P(`${s.checks.PASS} checks passed, ${s.checks.FLAG} were flagged and ${s.checks.FAIL} failed. Flagged items are limitations reported in the workbook, not errors: ${s.flags.map((f) => f[1]).join("; ")}.`);
}
pageBreak();
H1("4. Results for each leaf level");
P("Each section follows the steps of the workbook of that leaf level: data and validation design; Tiers 1–4 on raw reflectance with CART and Random Forest; validation; disease-sensitive features; the four tiers on the combined feature pool; transfer to an unseen date; interpretation and cross-checks.");
S.forEach((s, i) => levelChapter(s, i + 1));

// ============================================================ 5 discussion, 6 conclusions
pageBreak();
H1("5. Discussion");
DISC.forEach(([h, ps]) => { H2(h); ps.forEach((t) => (Array.isArray(t) ? B(t) : P(t))); });
H1("6. Conclusions and recommendations");
B(CONCL);
H2("Recommendations");
B(RECS);
H1("References");
REFS.forEach((r) => body.push(new Paragraph({ children: runs(r, { size: 20 }), spacing: { after: 80 }, indent: { left: 360, hanging: 360 } })));
pageBreak();
H1("Appendix A. Cross-check summary by leaf level");
table([["Leaf level", "PASS", "FLAG", "FAIL", "Flagged items (limitations reported in the workbook)"],
  ...S.map((s) => [s.level, s.checks.PASS, s.checks.FLAG, s.checks.FAIL, s.flags.map((f) => f[1]).join("; ")])],
  "Cross-checks of each leaf-level analysis (all workbooks recalculated in LibreOffice with 0 formula errors).", [0.8, 0.6, 0.6, 0.6, 5.6], 15);
H1("Appendix B. The three workbooks");
table([["Workbook", "Leaf level"], ...S.map((s, i) => [`${i + 1}_WhiteRust_Mustard_LeafLevel_${s.level}_FourTier_CART_RF_K_Combined.xlsx`, s.label])],
  "Excel workbooks (40 sheets each: README, glossary, summary, design, data audit, pre-processing, Tiers 1–4, validation, Random Forest steps, disease-sensitive feature steps, four tiers on the combined pool, transfer to new dates, within-strata checks, cross-checks, band-by-band and feature tables, folds, chart data).", [5, 2.4]);

const doc = new Document({
  creator: "Animesh Panda", title: "White rust in mustard — leaf levels L3, L5, LL", description: "Four-tier analysis by leaf level",
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
