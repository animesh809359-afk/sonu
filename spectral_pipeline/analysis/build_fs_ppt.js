// Presentation for Part FS (feature-selection methods) from work/fs_results.json and work/figures_fs/*.png
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const WORK = process.argv[2];
const OUT = process.argv[3];
const J = JSON.parse(fs.readFileSync(path.join(WORK, "fs_results.json"), "utf8"));
const T = J.txt || {};
const FIG = (n) => path.join(J.fig, n + ".png");
const sizeOf = (f) => { const b = fs.readFileSync(f); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; };
const THEME = {
  name: "Feature selection", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1B1B1A", lt1: "FFFFFF", dk2: "1F3D2B", lt2: "F0EFEC", accent1: "2A78D6", accent2: "EDA100",
            accent3: "1BAF7A", accent4: "6250D6", accent5: "EB6834", accent6: "52514E", hlink: "2A78D6", folHlink: "6250D6" },
};
const FAM = { Filter: "2A78D6", Wrapper: "C98500", Embedded: "14895F", Ensemble: "6250D6" };
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Feature selection for white-rust detection in mustard leaves";
pres.author = "Animesh Panda";
const W = 13.333, H = 7.5, M = 0.5;
pres.defineSlideMaster({ title: "TITLE", background: { color: "1F3D2B" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 1.8, w: W - 2 * M, h: 1.8, fontFace: "Cambria", fontSize: 38, bold: true, color: "FFFFFF", valign: "bottom" }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: M, y: 3.8, w: W - 2 * M, h: 2.4, fontSize: 18, color: "E3F4EC", valign: "top" }, text: "" } }] });
pres.defineSlideMaster({ title: "SECTION", background: { color: "1F3D2B" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 2.6, w: W - 2 * M, h: 1.2, fontFace: "Cambria", fontSize: 36, bold: true, color: "FFFFFF", valign: "bottom" }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: M, y: 3.9, w: W - 2 * M, h: 1.8, fontSize: 18, color: "E3F4EC", valign: "top" }, text: "" } }],
  slideNumber: { x: W - 0.9, y: H - 0.45, fontSize: 10, color: "B5D6C3" } });
pres.defineSlideMaster({ title: "CONTENT", background: { color: "FFFFFF" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 0.3, w: W - 2 * M, h: 0.8, fontFace: "Cambria", fontSize: 25, bold: true, color: "1F3D2B", valign: "middle" }, text: "" } },
            { text: { text: "White rust · mustard leaves · K1–K4 feature pool · filter, wrapper and embedded feature selection",
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
function bullets(s, items, x, y, w, h, fontSize = 15) {
  if (!items || !items.length) return;
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
            { x, y, w, h, fontSize, color: "1B1B1A", valign: "top", paraSpaceAfter: 6, isTextBox: true });
}
function refnote(s, text) { s.addText("References: " + text, { x: M, y: H - 0.8, w: W - 2 * M, h: 0.35, fontSize: 10, italic: true, color: "52514E", isTextBox: true, margin: 0 }); }
function stat(s, value, label, x, y, w, color) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.45, fill: { color: "F0EFEC" }, line: { color: "F0EFEC" }, rectRadius: 0.08 });
  s.addText(value, { x: x + 0.15, y: y + 0.08, w: w - 0.3, h: 0.75, fontFace: "Cambria", fontSize: 30, bold: true, color, isTextBox: true, margin: 0 });
  s.addText(label, { x: x + 0.15, y: y + 0.8, w: w - 0.3, h: 0.6, fontSize: 12, color: "52514E", isTextBox: true, margin: 0, valign: "top" });
}
function famCard(s, fam, x, y, w, h, title, lines) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: "FFFFFF" }, line: { color: FAM[fam], width: 1.5 } });
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.5, fill: { color: FAM[fam] }, line: { color: FAM[fam] } });
  s.addText(title, { x: x + 0.12, y, w: w - 0.24, h: 0.5, fontSize: 15, bold: true, color: "FFFFFF", valign: "middle", isTextBox: true, margin: 0 });
  bullets(s, lines, x + 0.08, y + 0.6, w - 0.16, h - 0.7, 12);
}
const pct = (v) => (v == null ? "–" : (100 * v).toFixed(1) + " %");
const A = J.acc;
const best = J.best[0];
const methodsOf = (fam) => J.methods.filter((m) => m[1] === fam);

// ================================================================ title
pres.addSection({ title: "Introduction" });
let s = pres.addSlide({ masterName: "TITLE", sectionTitle: section });
s.addText("Which features detect white rust? Filter, wrapper and embedded feature selection on the K1–K4 spectral feature pool", { placeholder: "title" });
s.addText([{ text: "23 methods from crop-disease research compared under one honest protocol · stable and informative disease-specific features", options: { breakLine: true } },
           { text: `${J.n} leaf spectra (${J.nH} healthy, ${J.nD} white-rust diseased) · 4 dates · 3 growth stages · 3 varieties · ${J.p} features`, options: { breakLine: true, fontSize: 14, color: "B5D6C3" } },
           { text: "Animesh Panda · Division of Agricultural Physics, ICAR-IARI, New Delhi", options: { fontSize: 14, color: "B5D6C3" } }], { placeholder: "body" });

// ================================================================ key results
s = content("Key results at a glance");
stat(s, best, "best method overall (composite ranking)", M, 1.25, 3.0, "1F3D2B");
stat(s, pct(A[best].qda), `QDA balanced accuracy on new plots with its 10 features`, M + 3.1, 1.25, 3.0, "2A78D6");
stat(s, (A[best].jac == null ? "–" : A[best].jac.toFixed(2)), "stability: Jaccard of the 20 training-set selections (±10 nm)", M + 6.2, 1.25, 3.0, "C98500");
stat(s, pct(J.fourtier["Four-tier RF-17 (Part C)"]), "four-tier RF-17 set of Part C on the same plots (reference)", M + 9.3, 1.25, 3.0, "52514E");
bullets(s, (T.key_messages || []).slice(0, 5), M, 2.95, W - 2 * M, 3.8, 14);

// ================================================================ why
s = content(`Why feature selection? ${J.p} correlated features, ${J.n} leaves`);
bullets(s, ["Hyperspectral data are high-dimensional and strongly collinear: neighbouring bands carry almost the same information (Thomas et al. 2018).",
            "Too many features → over-fitting, unstable covariance matrices (QDA needs fewer features than leaves per class), costly sensors.",
            "Feature selection keeps a few original, interpretable features — unlike PCA, the selected wavelengths can guide a multispectral disease sensor (Wei et al. 2021).",
            "Different selectors answer different questions: which feature is individually discriminating (filter), which subset classifies best (wrapper), which features a model relies on (embedded).",
            "Goal here: features that are (1) informative — separate healthy and diseased leaves on new plots, (2) stable — chosen again when the data change, (3) disease-specific — physiologically interpretable."],
        M, 1.25, 7.4, 5.4, 15);
famCard(s, "Filter", 8.2, 1.3, 4.6, 1.65, "Filter", ["score each feature by a statistic, independent of a classifier", "fast; ignores interactions; redundant top lists"]);
famCard(s, "Wrapper", 8.2, 3.1, 4.6, 1.65, "Wrapper", ["search subsets, scored by a classifier or a separability criterion", "finds complementary features; slow; can over-fit"]);
famCard(s, "Embedded", 8.2, 4.9, 4.6, 1.65, "Embedded", ["selection is part of model fitting (trees, penalties, PLS)", "middle ground in cost; model-specific"]);
refnote(s, "Guyon & Elisseeff 2003; Saeys et al. 2007; Kohavi & John 1997; Thomas et al. 2018; Wei et al. 2021");

// ================================================================ methods overview
s = content("The 23 methods compared (as used in crop-disease studies)");
const fam3 = [["Filter", 0.5], ["Wrapper", 4.65], ["Embedded", 8.8]];
fam3.forEach(([f, x]) => {
  const ms = methodsOf(f).concat(f === "Embedded" ? methodsOf("Ensemble") : []);
  famCard(s, f, x, 1.2, 4.0, 5.4, `${f} (${ms.length})`, ms.map((m) => `${m[0]} — ${m[3]}`));
});

s = content("Study design: one protocol for every method");
img(s, "FS01_workflow", M, 1.1, W - 2 * M, 4.4);
bullets(s, ["Selection runs only inside the training leaves of each of 20 units (10 plot-grouped folds + 10 hold-outs of 30 % of plots) — no selection bias (Ambroise & McLachlan 2002).",
            "Same leaves, same pool, same units, same classifiers (QDA equal priors = Tier 4 of Das et al. 2020; LDA; Balanced RF) → differences come from the selector only.",
            "Top-k with k = 5–20; 'redundancy-controlled' = skip a feature correlated |r| ≥ 0.95 with one already chosen (cf. Wei et al. 2021, 20-nm minimum distance)."],
        M, 5.45, W - 2 * M, 1.4, 12.5);

// ================================================================ filter
sec("Filter methods", "Pearson r · ANOVA F · Fisher score · chi-square · mutual information · ReliefF · univariate J–M · mRMR · SPA · MC-UVE · CWT separability scalogram");
s = content("Univariate filters: where does each statistic find information?");
img(s, "FS02_score_spectra", M, 1.05, 8.3, 5.75);
bullets(s, ["Pearson r, ANOVA F and Fisher score are algebraically equivalent for two classes (r² = F/(F + n − 2)) → identical rankings (verified: Spearman ρ = 1).",
            "Chi-square (Abdulridha et al. 2023) bins each feature into quantiles; mutual information (Kraskov et al. 2004) also captures non-linear dependence.",
            "All univariate filters peak on the same few regions — first-derivative bands near 850–875 nm and 1910–1950 nm and the continuum-removed water features — so their top-10 lists are made of neighbouring bands."],
        9.0, 1.2, 3.8, 5.4, 12.5);
refnote(s, "Pearson 1895; Duda et al. 2001; Abdulridha et al. 2023; Kraskov et al. 2004; Das et al. 2020");

s = content("Multivariate filters: ReliefF, mRMR, SPA and MC-UVE");
const mf = ["ReliefF", "mRMR", "SPA", "MC-UVE"];
table(s, [["Method", "Principle", "Top-5 (all leaves)"]].concat(mf.map((m) => [m, J.methods.find((x) => x[0] === m)[2], (J.top[m] || []).slice(0, 5).join(", ")])),
      M, 1.2, W - 2 * M, { colW: [1.4, 5.0, 5.9], fontSize: 11, rowH: 0.55 });
bullets(s, [`ReliefF (Kononenko 1994; used by Mahlein et al. 2013 to build disease indices): nearest hit / nearest miss differences; class-balanced instances.`,
            `SPA (Araújo et al. 2001; Zhu et al. 2017): picks the least collinear chain; ${J.native_n["SPA"]} variables chosen by inner CV — minimal collinearity, but not necessarily the most discriminating features.`,
            `MC-UVE (Centner et al. 1996): ${J.native_n["MC-UVE"]} of ${J.p} features have PLS coefficients more stable than every artificial noise variable — UVE removes noise, it does not pick a short list.`,
            `mRMR (Peng et al. 2005): relevance (F) divided by redundancy (mean |r|) — built-in redundancy control.`], M, 4.15, W - 2 * M, 2.5, 13);
refnote(s, "Kira & Rendell 1992; Kononenko 1994; Mahlein et al. 2013; Peng et al. 2005; Araújo et al. 2001; Zhu et al. 2017; Centner et al. 1996; Cai et al. 2008");

s = content("Continuous wavelet analysis: separability scalogram (Cheng et al. 2010)");
img(s, "FS03_cwt_scalogram", M, 1.1, W - 2 * M, 3.5);
bullets(s, [`Each spectrum is decomposed with the Mexican-hat wavelet at 8 dyadic scales (2–256 nm): ${J.n_cwt} wavelet features; the J–M of every coefficient forms the scalogram.`,
            `Top features (all leaves): ${(J.top["CWT scalogram"] || []).slice(0, 6).join(", ")}.`,
            `Small scales behave like derivatives (absorption-feature shape), large scales like continuum-removed band depths — wavelet features combine K2 and K4 information.`],
        M, 4.7, W - 2 * M, 1.9, 13);
refnote(s, "Cheng et al. 2010; Das et al. 2020 (J–M)");

// ================================================================ wrapper
sec("Wrapper methods", "SVM-RFE · RF-RFE · CARS · SFFS (QDA criterion) · SFFS (J–M criterion) · genetic algorithm");
s = content("Recursive feature elimination and CARS");
table(s, [["Method", "Principle", "Top-6 (all leaves)"]].concat(["SVM-RFE", "RF-RFE", "CARS"].map((m) => [m, J.methods.find((x) => x[0] === m)[2], (J.top[m] || []).slice(0, 6).join(", ")])),
      M, 1.2, 8.0, { colW: [1.2, 3.0, 3.8], fontSize: 10.5, rowH: 0.6 });
img(s, "FS13_cars", 8.7, 1.1, 4.1, 2.6);
bullets(s, [`RFE removes the least important features step by step and re-fits the model each time (Guyon et al. 2002); Wei et al. (2021) found RFE better than chi-square for peanut stem rot.`,
            `CARS (Li et al. 2009) keeps an exponentially shrinking set by PLS-coefficient weights and adaptive reweighted sampling: best run ${J.info["CARS"] ? J.info["CARS"]["best run"] : "–"} with ${J.native_n["CARS"]} variables.`],
        M, 4.0, W - 2 * M, 2.4, 13);
refnote(s, "Guyon et al. 2002; Wei et al. 2021; Liu et al. 2024 (as cited); Li et al. 2009; Zhu et al. 2017");

s = content("Sequential floating forward selection and the genetic algorithm");
img(s, "FS12_wrapper_search", M, 1.05, W - 2 * M, 3.3);
bullets(s, [`SFFS (Pudil et al. 1994; used by Mustafa et al. 2023): add the best feature, drop features while that helps. Criterion = inner-CV QDA balanced accuracy (ML-based) or J–M (Das Tier 3).`,
            `SFFS (QDA), 10 features: ${(J.top["SFFS (QDA)"] || []).slice(0, 10).join(", ")}.`,
            `GA (Leardi et al. 1992; Nagasubramanian et al. 2018 for charcoal rot): 50 chromosomes × 40 generations, fitness = QDA BA − size penalty; best chromosome ${J.native_n["Genetic algorithm"]} features.`,
            `Candidates for SFFS/GA: the 100 most significant, mutually non-redundant (|r| < 0.95) features of each training set.`],
        M, 4.45, W - 2 * M, 2.3, 12.5);
refnote(s, "Pudil et al. 1994; Mustafa et al. 2023; Leardi et al. 1992; Nagasubramanian et al. 2018; Das et al. 2020");

// ================================================================ embedded
sec("Embedded methods", "Random Forest importance · CART importance · Boruta · PLS-VIP · LASSO · gradient boosting · consensus (Borda)");
s = content("Tree-based importance, PLS-VIP and LASSO");
const em = ["RF importance", "CART importance", "Gradient boosting", "PLS-VIP", "LASSO"];
table(s, [["Method", "Principle", "Top-5 (all leaves)"]].concat(em.map((m) => [m, J.methods.find((x) => x[0] === m)[2], (J.top[m] || []).slice(0, 5).join(", ")])),
      M, 1.2, W - 2 * M, { colW: [1.6, 4.6, 6.1], fontSize: 10.5, rowH: 0.5 });
bullets(s, [`PLS-VIP: ${J.info["PLS-VIP"] ? J.info["PLS-VIP"].components : "–"} components; ${J.native_n["PLS-VIP"]} features with VIP > 1 (Wold et al. 2001; Chong & Jun 2005).`,
            `LASSO: ${J.info["LASSO"] ? J.info["LASSO"]["nonzero at C"] : "–"} non-zero coefficients at the cross-validated penalty (Tibshirani 1996).`,
            `CART uses only ${J.native_n["CART importance"]} features in its pruned tree — the same mechanism as Tier 2 of Das et al. (2020).`],
        M, 4.45, W - 2 * M, 2.0, 13);
refnote(s, "Breiman 2001; Breiman et al. 1984; Friedman 2001; Chen & Guestrin 2016; Wold et al. 2001; Chong & Jun 2005; Tibshirani 1996");

s = content("Boruta: all-relevant selection with shadow features");
const bi = J.info["Boruta"] || {};
stat(s, String(bi.confirmed ?? "–"), "features confirmed (all leaves)", M, 1.25, 2.9, "14895F");
stat(s, String(bi.tentative ?? "–"), "tentative", M + 3.05, 1.25, 2.9, "C98500");
stat(s, String(bi.rejected ?? "–"), "rejected", M + 6.1, 1.25, 2.9, "52514E");
bullets(s, ["Every real feature competes with a shuffled copy of itself (a 'shadow'); a feature that beats the best shadow significantly often (binomial test, Bonferroni) is confirmed (Kursa & Rudnicki 2010).",
            "Boruta finds ALL features carrying disease information (all-relevant), so its confirmed set is large: it is a screening tool, not a minimal set; for top-k the ranking by mean importance is used.",
            `Top features by mean importance: ${(J.top["Boruta"] || []).slice(0, 8).join(", ")}.`,
            "Mustafa et al. (2022, 2023) used Boruta to pick fusarium-head-blight-sensitive features before a final SFFS step — the same two-stage idea as Boruta → SFFS here."],
        M, 2.9, W - 2 * M, 3.7, 14);
refnote(s, "Kursa & Rudnicki 2010; Mustafa et al. 2022, 2023");

// ================================================================ comparison
sec("Which method works best?", "Accuracy on new plots · redundancy · stability · statistical tests · composite ranking");
s = content("What each method picks (10 features, all leaves, redundancy-controlled)");
img(s, "FS14_selected_positions", M, 1.05, W - 2 * M, 5.85);

s = content("Accuracy of 10 selected features on leaves of new plots");
img(s, "FS05_accuracy_k10", M, 1.05, 6.6, 5.8);
bullets(s, (T.accuracy || []), 7.3, 1.2, 5.5, 5.4, 13);

s = content("How many features are needed?");
img(s, "FS04_ba_vs_k", M, 1.05, W - 2 * M, 4.3);
bullets(s, (T.k || []), M, 5.45, W - 2 * M, 1.3, 13);

s = content("Redundancy control: skip near-duplicate features");
img(s, "FS15_redundancy_control", M, 1.05, 6.0, 5.6);
bullets(s, (T.redundancy || []), 6.8, 1.2, 6.0, 5.4, 13);
refnote(s, "Wei et al. 2021 (minimum distance between selected wavelengths)");

s = content("Stable and informative: stability against accuracy");
img(s, "FS06_stability_vs_accuracy", M, 1.05, 7.4, 5.0);
table(s, J.stability.slice(0, 13), 8.1, 1.2, 4.7, { colW: [1.9, 0.9, 0.95, 0.95], fontSize: 9.5, rowH: 0.27 });
bullets(s, (T.stability || []), M, 6.05, W - 2 * M, 0.7, 12);
refnote(s, "Kuncheva 2007; Nogueira et al. 2018");

s = content("Are the differences between methods significant?");
img(s, "FS07_cd_diagram", M, 1.05, W - 2 * M, 3.6);
table(s, J.wilcoxon.slice(0, 8), M, 4.7, 7.6, { colW: [2.4, 1.6, 1.2, 1.3, 0.8], fontSize: 8.5, rowH: 0.19 });
bullets(s, (T.tests || []), 8.3, 4.75, 4.5, 2.0, 12);
refnote(s, "Friedman 1937 via Demšar 2006 (Friedman–Nemenyi); Holm-corrected Wilcoxon tests");

s = content("Composite ranking: accuracy, stability and separability together");
img(s, "FS10_composite_ranking", M, 1.05, 5.6, 5.8);
table(s, J.composite.slice(0, 13), 6.3, 1.2, 6.5, { colW: [0.35, 1.8, 0.85, 0.75, 0.75, 0.7, 0.6, 0.7], fontSize: 9.5, rowH: 0.3, highlight: [1, 2, 3] });

s = content("Best selectors vs the four-tier sets (Das et al. 2020 approach, Part C)");
table(s, J.vs4, M, 1.2, W - 2 * M, { colW: [2.8, 2.6, 1.3, 1.4, 1.3, 1.1, 1.0], fontSize: 11, rowH: 0.32 });
bullets(s, (T.vs4 || []), M, 5.1, W - 2 * M, 1.6, 13);

s = content("Computing cost");
img(s, "FS11_runtime", M, 1.05, 6.6, 5.6);
bullets(s, (T.runtime || []), 7.4, 1.2, 5.4, 5.0, 13);

// ================================================================ consensus
sec("Stable, informative, disease-specific features", "Features chosen by many methods in many training sets");
s = content("Where the methods agree");
img(s, "FS08_selection_frequency", M, 1.05, W - 2 * M, 5.8);

s = content("Consensus disease-specific features");
table(s, J.consensus, M, 1.2, 7.4, { colW: [2.2, 1.4, 1.0, 1.1, 0.8, 0.9], fontSize: 10, rowH: 0.3 });
bullets(s, (T.consensus || []), 8.1, 1.2, 4.7, 5.5, 12.5);

s = content("Consensus features on the healthy and diseased spectra");
img(s, "FS09_consensus_on_spectrum", M, 1.05, 8.4, 5.7);
bullets(s, (T.interpretation || []), 9.1, 1.2, 3.7, 5.5, 12);

// ================================================================ conclusions
sec("Conclusions");
s = content("Conclusions");
bullets(s, (T.conclusions || []), M, 1.2, W - 2 * M, 5.6, 14);
s = content("Recommendations: which method to use");
bullets(s, (T.recommendations || []), M, 1.2, W - 2 * M, 5.6, 14);

s = content("Quality control: implementation checks");
table(s, J.checks.map((r) => [r[0].slice(0, 95), r[1].slice(0, 55), r[2]]), M, 1.2, W - 2 * M, { colW: [7.0, 4.4, 0.9], fontSize: 10, rowH: 0.36 });

// ================================================================ references
const order = Object.keys(J.refs).sort((a, b) => J.refs[a].localeCompare(J.refs[b]));
const refs = order.map((k) => J.refs[k]);
const per = Math.ceil(refs.length / 4);
for (let k = 0; k < 4; k++) {
  s = content(`References (${k + 1}/4)`);
  bullets(s, refs.slice(k * per, (k + 1) * per), M, 1.1, W - 2 * M, 5.9, 10.5);
}
pres.writeFile({ fileName: OUT }).then(async () => { await applyTheme(OUT, THEME); console.log("deck written", OUT); });
