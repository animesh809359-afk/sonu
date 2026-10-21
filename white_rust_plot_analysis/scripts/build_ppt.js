// PhD seminar deck: plot-level discrimination of healthy and white-rust-diseased mustard plots.
// Native (editable) charts and tables are built from cache/ppt_data.json; heat maps / maps are figures.
const path = require('path');
const pptxgen = require('pptxgenjs');
const SKILL = '/root/.claude/skills/synced/4f45d97b-0a27-4cd4-81ca-4f53ae4b645e_3447a982-a016-432c-b6ed-4390ec73d1e4/pptx';
const { applyTheme } = require(path.join(SKILL, 'scripts/apply_theme.js'));
const ROOT = path.join(__dirname, '..');
const D = require(path.join(ROOT, 'cache/ppt_data.json'));
const NARR = require(path.join(ROOT, 'cache/narrative.json'));
const FIG = (n) => path.join(ROOT, 'outputs/figures', n);
const OUT = path.join(ROOT, 'outputs/WhiteRust_Mustard_PlotLevel_PhD_Seminar.pptx');

const THEME = {
  name: 'Mustard White Rust', headFontFace: 'Cambria', bodyFontFace: 'Calibri',
  colors: { dk1: '1A1A1A', lt1: 'FFFFFF', dk2: '1F3D2B', lt2: 'EEF3EC', accent1: '2E7D32', accent2: 'D08A00',
            accent3: '2A6FB0', accent4: 'B03A2E', accent5: '6B8E23', accent6: '6E6E6E', hlink: '2A6FB0', folHlink: '7A4E9C' },
};
const HX = { H: '2E7D32', D: 'D08A00', B: '2A6FB0', R: 'B03A2E', G: '6E6E6E', DK: '1F3D2B', LT: 'EEF3EC', INK: '1A1A1A', GRID: 'E3E3E3' };
const DATEC = [HX.B, HX.H, HX.D, HX.R];
const DL = ['11 Feb', '24 Feb', '03 Mar', '13 Mar'];

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = 'Plot-level hyperspectral discrimination of white rust in Indian mustard';
pres.author = 'PhD research seminar';
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: 'TITLE', background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.8, y: 1.5, w: 11.7, h: 2.4, fontSize: 36, bold: true, color: C.background1, valign: 'bottom', fontFace: THEME.headFontFace }, text: '' } },
    { placeholder: { options: { name: 'body', type: 'body', x: 0.8, y: 4.15, w: 11.7, h: 2.4, fontSize: 18, color: C.background2, valign: 'top' }, text: '' } },
  ],
});
pres.defineSlideMaster({
  title: 'SECTION', background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.8, y: 2.6, w: 11.7, h: 1.3, fontSize: 40, bold: true, color: C.background1, fontFace: THEME.headFontFace }, text: '' } },
    { placeholder: { options: { name: 'body', type: 'body', x: 0.8, y: 3.95, w: 11.7, h: 1.2, fontSize: 18, color: C.background2 }, text: '' } },
  ],
});
pres.defineSlideMaster({
  title: 'CONTENT', background: { color: C.background1 },
  margin: [0.5, 0.5, 0.6, 0.5],
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.5, y: 0.28, w: 12.3, h: 0.8, fontSize: 26, bold: true, color: C.text2, fontFace: THEME.headFontFace, valign: 'middle' }, text: '' } },
    { text: { text: 'Plot-level detection of white rust in Indian mustard  |  PhD research seminar', options: { x: 0.5, y: 7.08, w: 7.5, h: 0.3, fontSize: 9, color: C.accent6 } } },
  ],
  slideNumber: { x: 12.3, y: 7.08, w: 0.6, h: 0.3, fontSize: 9, color: '6E6E6E', align: 'right' },
});

// ------------------------------------------------------------------ helpers
let section = '';
function newSection(title, sub) {
  pres.addSection({ title }); section = title;
  const s = pres.addSlide({ masterName: 'SECTION', sectionTitle: section });
  s.addText(title, { placeholder: 'title' });
  if (sub) s.addText(sub, { placeholder: 'body' });
  return s;
}
function content(title, notes) {
  const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: section });
  s.addText(title, { placeholder: 'title' });
  if (notes) s.addNotes(notes);
  return s;
}
function source(s, txt) {
  s.addText('Source: ' + txt, { x: 0.5, y: 6.74, w: 12.3, h: 0.3, fontSize: 10, italic: true, color: C.accent6, isTextBox: true, margin: 0 });
}
function bullets(s, items, opt) {
  const runs = items.map((it, i) => {
    const o = { bullet: it.sub ? { indent: 18 } : true, indentLevel: it.sub ? 1 : 0, breakLine: i < items.length - 1, paraSpaceAfter: 6 };
    if (typeof it === 'string') return { text: it, options: o };
    return { text: it.t, options: Object.assign(o, it.b ? { bold: true } : {}) };
  });
  s.addText(runs, Object.assign({ x: 0.5, y: 1.25, w: 6, h: 5.3, fontSize: 15, color: C.text1, valign: 'top', isTextBox: true }, opt));
}
function card(s, x, y, w, h, head, body, color, fs) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 } });
  s.addShape(pres.shapes.OVAL, { x: x + 0.18, y: y + 0.2, w: 0.42, h: 0.42, fill: { color: color || C.accent1 }, line: { color: color || C.accent1 } });
  s.addText(head, { x: x + 0.72, y: y + 0.13, w: w - 0.85, h: 0.56, fontSize: 15, bold: true, color: C.text2, valign: 'middle', isTextBox: true, margin: 0 });
  s.addText(body, { x: x + 0.2, y: y + 0.78, w: w - 0.4, h: h - 0.9, fontSize: fs || 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
}
function stat(s, x, y, w, big, small, color) {
  s.addText(big, { x, y, w, h: 0.85, fontSize: 38, bold: true, color: color || C.accent1, fontFace: THEME.headFontFace, align: 'left', isTextBox: true, margin: 0 });
  s.addText(small, { x, y: y + 0.85, w, h: 0.5, fontSize: 13, color: C.accent6, isTextBox: true, margin: 0 });
}
const HDR = (t) => ({ text: t, options: { bold: true, color: 'FFFFFF', fill: { color: HX.DK }, align: 'center', valign: 'middle' } });
function table(s, header, rows, opt) {
  const data = [header.map(HDR)].concat(rows.map((r, i) => r.map((v) => {
    if (v && typeof v === 'object' && v.text !== undefined) return v;
    return { text: String(v), options: { fill: { color: i % 2 ? 'F6F8F5' : 'FFFFFF' } } };
  })));
  s.addTable(data, Object.assign({ x: 0.5, y: 1.25, w: 6, fontSize: 11, color: HX.INK, border: { type: 'solid', pt: 0.5, color: 'D5D5D5' }, valign: 'middle', margin: 0.04 }, opt));
}
function heatCell(v, lo, hi, fmt) {
  if (v === null || v === undefined || isNaN(v)) return { text: '-', options: { align: 'center' } };
  const t = Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
  const a = [255, 255, 229], b = [120, 198, 121], c = [0, 69, 41];
  const mix = (p, q, u) => p.map((x, i) => Math.round(x + (q[i] - x) * u));
  const rgb = t < 0.5 ? mix(a, b, t * 2) : mix(b, c, (t - 0.5) * 2);
  const hex = rgb.map((x) => x.toString(16).padStart(2, '0')).join('').toUpperCase();
  return { text: fmt(v), options: { fill: { color: hex }, color: t > 0.62 ? 'FFFFFF' : HX.INK, align: 'center' } };
}
const AX = () => ({
  catAxisLabelFontFace: '+mn-lt', valAxisLabelFontFace: '+mn-lt', catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
  catAxisLabelColor: '555555', valAxisLabelColor: '555555', valGridLine: { color: HX.GRID, size: 0.5 }, catGridLine: { style: 'none' },
  legendFontFace: '+mn-lt', legendFontSize: 10, legendColor: '333333', showLegend: true, legendPos: 'b',
  showTitle: true, titleFontFace: '+mj-lt', titleFontSize: 13, titleColor: HX.DK,
  catAxisTitleFontSize: 10, valAxisTitleFontSize: 10, catAxisTitleColor: '555555', valAxisTitleColor: '555555',
  catAxisTitleFontFace: '+mn-lt', valAxisTitleFontFace: '+mn-lt', dataLabelFontFace: '+mn-lt', dataLabelFontSize: 9, dataLabelColor: '333333',
  catAxisMajorTickMark: 'none', catAxisLabelPos: 'low', valAxisLabelPos: 'low',
});
function lineChart(s, labels, series, colors, o) {
  s.addChart(pres.charts.LINE, series.map(([name, values]) => ({ name, labels, values })), Object.assign(AX(), {
    x: 0.5, y: 1.25, w: 6.2, h: 4.4, chartColors: colors, lineSize: 2, lineDataSymbol: 'none', catAxisLabelFrequency: 20,
    showCatAxisTitle: true, catAxisTitle: 'Wavelength (nm)', showValAxisTitle: true,
  }, o));
}
function barChart(s, labels, series, colors, o) {
  s.addChart(pres.charts.BAR, series.map(([name, values]) => ({ name, labels, values })), Object.assign(AX(), {
    x: 0.5, y: 1.25, w: 6.2, h: 4.4, barDir: 'col', chartColors: colors, showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0.00',
    valGridLine: { color: HX.GRID, size: 0.5 }, showLegend: series.length > 1,
  }, o));
}
const f3 = (v) => (v === null || v === undefined || isNaN(v) ? '-' : Number(v).toFixed(3));
const f2 = (v) => (v === null || v === undefined || isNaN(v) ? '-' : Number(v).toFixed(2));
const f1 = (v) => (v === null || v === undefined || isNaN(v) ? '-' : Number(v).toFixed(1));
const pfmt = (p) => (p < 0.001 ? '< 0.001' : Number(p).toFixed(3));
const SCN = D.scenarios;
const CLFS = ['LDA', 'PLS-DA', 'LR', 'kNN', 'SVM', 'LS-SVM', 'RF', 'XGBoost', 'ELM', 'MLP'];
const SUMK = {}; (D.summary || []).forEach((r) => { SUMK[r.scenario + '|' + r.clf] = r; });
const BEST = D.best[0], COMPACT = D.best[1], VIB = D.best[2];
const BS = SUMK[BEST.scenario + '|' + BEST.clf], CS = SUMK[COMPACT.scenario + '|' + COMPACT.clf];
const pipe = (sc, clf) => `${sc} ${SCN[sc]} + ${clf}`;

function box(s, x, y, w, h, title, sub, fill, dark) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: fill || HX.LT }, line: { color: dark ? fill : 'C9D3C6', width: 0.75 } });
  const runs = [{ text: title, options: { bold: true, fontSize: 12, color: dark ? 'FFFFFF' : HX.DK, breakLine: !!sub } }];
  if (sub) runs.push({ text: sub, options: { fontSize: 10, color: dark ? 'F2F2F2' : '333333' } });
  s.addText(runs, { x: x + 0.06, y, w: w - 0.12, h, align: 'center', valign: 'middle', isTextBox: true, margin: 0.02 });
}
function arrow(s, x1, y1, x2, y2, color) {
  let x = x1, y = y1, w = x2 - x1, h = y2 - y1, flipH = false, flipV = false;
  if (w < 0) { x = x2; w = -w; flipH = true; }
  if (h < 0) { y = y2; h = -h; flipV = true; }
  s.addShape(pres.shapes.LINE, { x, y, w, h, flipH, flipV, line: { color: color || '7A7A7A', width: 1.5, endArrowType: 'triangle' } });
}
const WHAT = NARR.what || {};
function explain(s, key, o) {
  const runs = [{ text: 'What it shows: ', options: { bold: true, color: HX.DK } }, { text: WHAT[key] || '', options: { color: '444444', breakLine: true } },
    { text: ' ', options: { fontSize: 5, breakLine: true } },
    { text: 'Finding: ', options: { bold: true, color: HX.R } }, { text: NARR[key] || '', options: { color: HX.INK } }];
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: o.x - 0.08, y: o.y - 0.06, w: o.w + 0.16, h: o.h + 0.1, rectRadius: 0.05, fill: { color: 'F6F8F5' }, line: { color: 'F6F8F5' } });
  s.addText(runs, { x: o.x, y: o.y, w: o.w, h: o.h, fontSize: o.fontSize || 12.5, valign: 'top', isTextBox: true, margin: 0.02 });
}
const pick = (arr, f) => (arr || []).filter(f);

// ================================================================== OPENING
{
  pres.addSection({ title: 'Opening' }); section = 'Opening';
  const s = pres.addSlide({ masterName: 'TITLE', sectionTitle: section });
  s.addText('Plot-level hyperspectral discrimination of healthy and white-rust (Albugo candida) diseased mustard plots', { placeholder: 'title' });
  s.addText([
    { text: 'Plot-average ASD contact-probe spectra, derived spectral features and machine-learning classification across four dates', options: { breakLine: true } },
    { text: ' ', options: { breakLine: true, fontSize: 10 } },
    { text: 'Animesh Panda  |  Division of Agricultural Physics, ICAR-IARI, New Delhi', options: { fontSize: 15, breakLine: true } },
    { text: 'PhD research seminar  |  Methodology - Results - Discussion', options: { fontSize: 13 } },
  ], { placeholder: 'body' });
}
{
  const s = content('Outline of the seminar');
  const items = [['1', 'Introduction', 'Why discriminate plots, not leaves'], ['2', 'Review of literature', 'Ten studies and what each contributed'],
    ['3', 'Objectives', 'Five objectives and hypotheses'], ['4', 'Materials and methods', 'Design, features, screening, selection, classifiers, validation'],
    ['5', 'Results', 'Spectral response, features, models, controls and experiments'], ['6', 'Discussion and conclusions', 'Meaning, comparison, caveats, recommendations']];
  items.forEach((it, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.2, y = 1.45 + row * 1.7;
    s.addShape(pres.shapes.OVAL, { x, y, w: 0.8, h: 0.8, fill: { color: C.accent1 }, line: { color: C.accent1 } });
    s.addText(it[0], { x, y, w: 0.8, h: 0.8, fontSize: 22, bold: true, color: C.background1, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    s.addText(it[1], { x: x + 1.0, y: y - 0.02, w: 4.9, h: 0.45, fontSize: 20, bold: true, color: C.text2, isTextBox: true, margin: 0 });
    s.addText(it[2], { x: x + 1.0, y: y + 0.43, w: 4.9, h: 0.45, fontSize: 14, color: C.accent6, isTextBox: true, margin: 0 });
  });
}

// ================================================================== INTRODUCTION
newSection('1. Introduction', 'From leaf spectra to a plot-level decision');
{
  const s = content('Why a plot-level model?');
  bullets(s, [
    { t: 'The plot (field unit) is where scouting and fungicide decisions are made', b: true },
    'Leaf spectra vary with leaf position, pustule cover and probe placement; averaging the leaves of a plot gives a stable plot signature',
    'Plot averages approach what canopy, UAV and satellite sensors record',
    'The previous chapter modelled single leaves; this chapter asks whether the plot average alone separates healthy from diseased plots',
    { t: 'Inputs: 48 plots x 4 dates of plot-average raw reflectance and the features derived from it', b: true },
  ], { w: 6.4 });
  card(s, 7.2, 1.3, 5.6, 1.6, 'Pigments (400-750 nm)', 'Chlorophyll loss and anthocyanin / carotenoid change: visible reflectance, red edge, VIs.', HX.H);
  card(s, 7.2, 3.05, 5.6, 1.6, 'Structure (750-1300 nm)', 'Haustoria and pustules alter mesophyll scattering: NIR level and slope.', HX.B);
  card(s, 7.2, 4.8, 5.6, 1.6, 'Water and dry matter (1300-2400 nm)', 'Water status and leaf constituents: 1450 / 1940 nm absorption, derivatives, continuum removal.', HX.D);
  source(s, 'Saharan et al. 2014; Zhang et al. 2012; Tian et al. 2021; Lv et al. 2023; Panda 2026 (R2)');
}
{
  const s = content('Research gaps for plot-level disease discrimination');
  const gaps = [
    ['Few plots, many features', 'n = 48 plots per date against > 2 000 candidate features: selection and validation must avoid optimistic bias (Ambroise & McLachlan 2002; Varma & Simon 2006).'],
    ['Repeated measurements', 'The same plots are measured on four dates; ignoring this inflates tests and CV accuracy (Roberts et al. 2017).'],
    ['Design confounding', 'Healthy controls often sit in a separate block; field position and leaf sampling can mimic a disease effect (Hurlbert 1984).'],
    ['Feature families not compared', 'Reflectance, derivatives, continuum removal, VIs, red-edge, wavelets and optimised indices are rarely compared under one plot-level design.'],
  ];
  gaps.forEach((g, i) => card(s, 0.5 + (i % 2) * 6.2, 1.3 + Math.floor(i / 2) * 2.65, 6.0, 2.45, g[0], g[1], [HX.R, HX.D, HX.B, HX.H][i]));
  source(s, 'Synthesis of the reviewed studies and methods literature');
}

// ================================================================== LITERATURE
newSection('2. Review of literature', 'Ten studies on spectral disease detection used to build the methodology');
{
  const s = content('Reviewed studies: designs, methods and best reported accuracy');
  const rows = [
    ['Mandal et al. 2022, 2023', 'Rice blast', 'ASD canopy', 'SG, 10-nm bands, red-edge, VIs, NDSI map, J-M, GA-PLS, PLS/RF/SVM', 'SVM R² 0.94'],
    ['Selvaprakash et al. 2026', 'Rice blast', 'ASD leaf', 'Derivatives, PCA, outlier screening, RF, new blast index', 'F1 0.95'],
    ['Tian et al. 2021', 'Rice leaf blast', 'ASD leaf clip', 'Bands + VIs + CWT, temporal stability, VIF, SFFS-OFC', 'OA 65-98.7 %'],
    ['Lv et al. 2023', 'Maize SCLB', 'Leaf clip', 'Date normalisation, FD + CWT + indices, ReliefF, SFFS-SVM', 'OA 87.1 %'],
    ['Terentev et al. 2023', 'Wheat leaf rust', 'HSI', 'Band means, VIs, cross-experiment linear SVM', 'Acc. 98 %'],
    ['Zhang et al. 2012', 'Wheat powdery mildew', 'ASD', 'Derivative edges, continuum removal, VIs, FLDA', 'OA 0.89'],
    ['Zhu et al. 2017', 'Tobacco TMV', 'HSI', 'SPA, PLS-DA, LS-SVM, ELM, BPNN', 'Acc. 98.3 %'],
    ['Huang et al. 2020', 'Wheat FHB', 'HSI', 'SPA, image features, PSO-SVM', 'Acc. 92 %'],
    ['Nguyen et al. 2023', 'Wheat yellow rust', 'UAV 5-band', 'VIs, class imbalance, SVM/RF/MLP/3D-CNN', 'OA 79 %'],
    ['Panda 2026 (R1, R2)', 'Mustard white rust', 'ASD contact probe', '23 selectors; leaf-level pooled models', 'Leaf BA 0.92-0.95'],
  ];
  table(s, ['Study', 'Crop / disease', 'Sensor', 'Key methods', 'Best result'], rows, { x: 0.5, y: 1.25, w: 12.3, colW: [2.3, 1.9, 1.6, 4.6, 1.9], fontSize: 11.5, rowH: 0.45 });
  source(s, 'Papers provided by the researcher; Panda 2026 = researcher\'s own feature-selection study and leaf-level chapter');
}
{
  const s = content('What each study contributed to the plot-level methodology');
  const rows = [
    ['Spectral characterisation', 'Mean, difference and ratio spectra; correlation spectrum; red-edge parameters; J-M distance', 'Zhang 2012; Mandal 2022, 2023'],
    ['Feature families', '10-nm bands, 1st-3rd derivatives, continuum removal, 87 VIs, red-edge, CWT, optimised NDSI/SR/DI', 'Mandal 2023; Zhang 2012; Lv 2023; Tian 2021'],
    ['Temporal stability', 'Features retained only when separable on >= 3 of 4 dates; per-date standardisation', 'Tian 2021; Lv 2023'],
    ['Feature selection', 'ReliefF + VIF + SFFS; OFC with LDA/kNN/SVM; SPA; GA-PLS; SVM-RFE, LASSO, CARS, Borda', 'Tian 2021; Zhu 2017; Huang 2020; Mandal 2023; Panda 2026'],
    ['Classifiers', 'LDA, PLS-DA, LR, kNN, SVM, LS-SVM, RF, XGBoost, ELM, MLP', 'Zhu 2017; Nguyen 2023; Tian 2021; Mandal 2023'],
    ['Validation', 'Repeated k-fold, transfer to unseen dates (cross-experiment), class-balanced metrics', 'Tian 2021; Terentev 2023; Nguyen 2023'],
    ['Not applicable', 'Image texture, 3D-CNN, severity regression (no images, no severity scores)', 'Huang 2020; Nguyen 2023; Mandal 2022'],
  ];
  table(s, ['Step', 'Method adopted', 'From'], rows, { x: 0.5, y: 1.25, w: 12.3, colW: [2.3, 6.4, 3.6], fontSize: 12, rowH: 0.62 });
  source(s, 'Synthesis by the author');
}

// ================================================================== OBJECTIVES
newSection('3. Objectives', 'Plot-level discrimination of healthy and diseased plots');
{
  const s = content('Objectives and hypotheses');
  const rows = [
    ['O1', 'Characterise the plot-level spectral response to white rust on four dates', 'H1: diseased plots differ in pigment, red-edge and water regions on every date'],
    ['O2', 'Rank seven feature families and identify date-stable disease features', 'H2: derivative / wavelet and water-region features separate plots best'],
    ['O3', 'Compare 12 feature scenarios x 10 classifiers under plot-grouped validation', 'H3: a compact selected set matches the full-spectrum models'],
    ['O4', 'Test robustness: single dates, unseen dates/varieties, permutation, design and leaf-number controls', 'H4: the separation is a disease effect, not a design artefact'],
    ['O5', 'Compare plot-average models with the leaf-level models', 'H5: plot averaging is at least as accurate as leaf-level prediction'],
  ];
  table(s, ['#', 'Objective', 'Hypothesis'], rows, { x: 0.5, y: 1.3, w: 12.3, colW: [0.6, 6.0, 5.7], fontSize: 13, rowH: 0.85 });
}

// ================================================================== METHODS
newSection('4. Materials and methods', 'Design, features, screening, selection, classifiers and validation');
{
  const s = content('Experimental design and plot-average dataset');
  stat(s, 0.6, 1.3, 2.8, '48', 'plots (12 control, 36 inoculated)', HX.H);
  stat(s, 3.5, 1.3, 2.8, '4', 'dates (11 Feb - 13 Mar 2026)', HX.B);
  stat(s, 0.6, 2.75, 2.8, '192', 'plot-average spectra', HX.D);
  stat(s, 3.5, 2.75, 2.8, '3 x 4', 'varieties x inoculation timings', HX.R);
  const rows = D.design.map((r) => [r.Date, r.Healthy, r.Diseased, f1(r.median_Healthy), f1(r.median_Diseased)]);
  table(s, ['Date', 'Healthy plots', 'Diseased plots', 'Leaves / H plot', 'Leaves / D plot'], rows, { x: 0.5, y: 4.3, w: 6.2, colW: [1.2, 1.25, 1.25, 1.25, 1.25], fontSize: 12, rowH: 0.38 });
  s.addImage({ path: FIG('Fig01_treatment_layout.png'), x: 6.9, y: 1.35, w: 5.95, h: 1.66 });
  bullets(s, [
    'Plot average = mean of all leaf spectra of a plot on a date (ASD contact probe, 350-2500 nm, 1 nm)',
    'Each cell (variety x inoculation timing D1-D4) holds 1 control + 3 inoculated plots',
    'Controls are all in one block (C); inoculated plots in blocks R1-R3',
    'Diseased plots averaged more leaves (5-15) than controls (3-9) - tested in E9',
  ], { x: 6.9, y: 3.2, w: 5.95, h: 3.3, fontSize: 13 });
  source(s, 'Treatment layout file; PlotAverage_Features workbooks (sheets 01-03)');
}
{
  const s = content('Feature families derived from the raw plot-average reflectance');
  const fs = pick(D.fam_summary, (r) => r.branch === 'raw');
  const nf = {}; fs.forEach((r) => { nf[r.family] = r.n_features; });
  const rows = [
    ['Reflectance (REF)', nf.REF, '10-nm means of raw 400-2400 nm reflectance', 'Mandal et al. 2023'],
    ['1st / 2nd / 3rd derivative', `${nf.FD1} each`, 'Central differences (1 nm), averaged to 10 nm', 'Tsai & Philpot 1998; Zhang 2012'],
    ['Continuum removal (CR)', nf.CR, '6 absorption windows x depth, position, width, area, asymmetry...', 'Clark & Roush 1984; Kokaly & Clark 1999'],
    ['Vegetation indices (VI)', nf.VI, 'Pigment, red-edge, water and disease indices (e.g. HI, PMI, LRDSI)', 'Mahlein 2013; Ashourloo 2014; see refs'],
    ['Red-edge parameters (RE)', nf.RE, 'REIP by 4 methods; blue/yellow/red edge amplitude, position, area', 'Horler 1983; Guyot & Baret 1988; Gong 2002'],
    ['Wavelet (CWT)', nf.CWT, 'Mexican-hat coefficients, scales 2^1-2^8, every 10 nm', 'Cheng 2011; Tian 2021; Lv 2023'],
    ['Optimised two-band indices', '3 x 20 100 pairs', 'NDSI, SR, DI of every 10-nm pair; best pairs found inside each training fold', 'Mandal 2023; Tian 2021; Zhu 2017'],
  ];
  table(s, ['Family', 'Features', 'Definition', 'References'], rows, { x: 0.5, y: 1.25, w: 12.3, colW: [2.6, 1.5, 5.0, 3.2], fontSize: 12, rowH: 0.58 });
  s.addText('Smoothed branch (detector-join correction + Savitzky-Golay 11/2) was built identically and compared in E1. The workbook\'s own optimised indices were chosen on all plots of a date, so they are reported descriptively only.',
    { x: 0.5, y: 5.95, w: 12.3, h: 0.6, fontSize: 12, italic: true, color: C.accent6, isTextBox: true, margin: 0 });
  source(s, 'PlotAverage_Features workbooks (sheets 02-12); this analysis (CWT, 10-nm binning, in-fold index search)');
}
{
  const s = content('Methodological flowchart: step by step');
  const X = [0.55, 3.7, 6.85, 10.0], W = 2.75, H = 1.2, Y = [1.3, 3.1, 4.9];
  const r1 = [['Step 1. Data assembly', '4 workbooks + treatment layout: 192 plot-dates'], ['Step 2. Quality control', 'noise, joins, leaf number, T²/Q flags'],
    ['Step 3. Characterisation', 'mean / difference spectra, band-wise tests, J-M'], ['Step 4. Feature families', 'REF, FD1-3, CR, VI, RE, CWT, NDSI/SR/DI']];
  const r2 = [['Step 5. Screening', 'AUC, Hedges g, FDR per date; LMM; PCA, PERMANOVA'], ['Step 6. Design checks', 'matched control, block contrast, inoculation timing'],
    ['Step 7. Selection', 'robust ReliefF+VIF+SFFS, SPA, GA-PLS, OFC, 6 selectors'], ['Step 8. Classification', '12 scenarios x 10 classifiers, nested cell-grouped CV']];
  const r3 = [['Step 9. Statistics', 'Friedman-Nemenyi, corrected t, Wilcoxon-Holm'], ['Step 10. Experiments', 'E1-E10: branch, dates, transfer, permutation, controls'],
    ['Step 11. Interpretation', 'final features, VIF, importance, progression'], ['Outcome', 'validated plot-level classifier and diagnostic features']];
  r1.forEach((b, i) => box(s, X[i], Y[0], W, H, b[0], b[1], 'F7F1E1'));
  r2.forEach((b, i) => box(s, X[3 - i], Y[1], W, H, b[0], b[1], 'E6EFE3'));
  r3.forEach((b, i) => box(s, X[i], Y[2], W, H, b[0], b[1], i === 3 ? HX.DK : 'E3ECF5', i === 3));
  for (let i = 0; i < 3; i++) { arrow(s, X[i] + W, Y[0] + H / 2, X[i + 1], Y[0] + H / 2); arrow(s, X[3 - i], Y[1] + H / 2, X[2 - i] + W, Y[1] + H / 2); arrow(s, X[i] + W, Y[2] + H / 2, X[i + 1], Y[2] + H / 2); }
  arrow(s, X[3] + W / 2, Y[0] + H, X[3] + W / 2, Y[1]); arrow(s, X[0] + W / 2, Y[1] + H, X[0] + W / 2, Y[2]);
  s.addText('Tan = data; green = features and models; blue = evaluation. Every step that uses labels (index search, selection, tuning) runs inside the training plots of each fold.',
    { x: 0.55, y: 6.3, w: 12.2, h: 0.35, fontSize: 11, italic: true, color: C.accent6, isTextBox: true, margin: 0 });
}
{
  const s = content('Steps 2-6 flowchart: characterisation and screening');
  box(s, 0.5, 1.3, 2.7, 0.9, '192 plot-average spectra', 'raw branch (main)', 'F7F1E1'); arrow(s, 3.2, 1.75, 3.6, 1.75);
  box(s, 3.6, 1.3, 2.9, 0.9, 'Seven feature families', '+ in-fold NDSI / SR / DI', 'F7F1E1');
  const br = [['Per-date tests', 'Welch t, FDR, Hedges g, AUC'], ['Stability', 'q < 0.05 and same sign on >= 3 dates'], ['Separability', 'J-M, sensitive regions'],
    ['Mixed models', 'z ~ disease + date + variety + (1|plot)'], ['Multivariate', 'PCA, eta², PERMANOVA'], ['Design checks', 'matched control, blocks, timing']];
  br.forEach((b, i) => { const x = 0.5 + i * 2.07; box(s, x, 2.9, 1.9, 1.1, b[0], b[1], 'E6EFE3'); arrow(s, 5.05, 2.2, x + 0.95, 2.9); });
  const outs = [['Where white rust acts', 'sensitive regions, family ranking (R3-R8)'], ['How large vs nuisance', 'date, variety, block effects (R9-R11)'], ['Candidate features', 'date-stable, non-redundant pools (Step 7)']];
  outs.forEach((o, i) => box(s, 0.9 + i * 4.1, 4.75, 3.6, 1.0, o[0], o[1], HX.DK, true));
  for (let i = 0; i < 6; i++) arrow(s, 0.5 + i * 2.07 + 0.95, 4.0, 0.9 + Math.min(2, Math.floor(i / 2)) * 4.1 + 1.8, 4.75);
  s.addText('Plots are the experimental units: statistics are computed on the 48 plots of each date (no leaf-level pseudo-replication); repeated dates are handled by the mixed model and by plot-level permutations.',
    { x: 0.5, y: 5.95, w: 12.3, h: 0.6, fontSize: 12, italic: true, color: C.accent6, isTextBox: true, margin: 0 });
  source(s, 'Benjamini & Hochberg 1995; Hedges 1981; Richards & Jia 2006; Bates et al. 2015; Anderson 2001; Hurlbert 1984');
}
{
  const s = content('Step 8 flowchart: nested, cell-grouped cross-validation');
  box(s, 0.5, 1.35, 3.0, 1.0, '12 cells = variety x inoculation', 'each: 1 control + 3 inoculated plots', 'F7F1E1');
  arrow(s, 3.5, 1.85, 4.0, 1.85);
  box(s, 4.0, 1.35, 3.6, 1.0, 'Outer split: 4 folds of 3 cells', 'one cell per variety; all 4 dates of a plot together', 'F7F1E1');
  arrow(s, 7.6, 1.85, 8.1, 1.85);
  box(s, 8.1, 1.35, 4.7, 1.0, 'Test fold: 3 healthy + 9 diseased plots', '48 plot-dates never seen in training', HX.R, true);
  arrow(s, 5.8, 2.35, 5.8, 2.8);
  box(s, 3.2, 2.8, 5.2, 1.0, 'Training: 9 cells (36 plots, 144 plot-dates)', 'inner 3-fold cell CV inside', 'E6EFE3');
  const inner = [['Index search', 'NDSI/SR/DI best pairs'], ['Feature selection', 'robust / SPA / GA-PLS'], ['Scaling', 'z-score on training'], ['Tuning', 'grid, inner BA']];
  inner.forEach((b, i) => { const x = 0.7 + i * 3.05; box(s, x, 4.2, 2.8, 0.9, b[0], b[1], 'E3ECF5'); arrow(s, 5.8, 3.8, x + 1.4, 4.2); });
  box(s, 3.2, 5.45, 5.2, 0.85, 'Predict the test fold -> metrics', 'repeat with 20 random cell assignments', HX.DK, true);
  for (let i = 0; i < 4; i++) arrow(s, 0.7 + i * 3.05 + 1.4, 5.1, 5.8, 5.45);
  s.addText('BA = (sensitivity + specificity) / 2; MCC, kappa, macro-F1, ROC-AUC and PR-AUC also reported (12 : 36 class ratio).', { x: 8.6, y: 5.5, w: 4.2, h: 0.8, fontSize: 11, italic: true, color: C.accent6, isTextBox: true, margin: 0 });
  source(s, 'Varma & Simon 2006; Roberts et al. 2017; Ambroise & McLachlan 2002; Chicco & Jurman 2020');
}
{
  const s = content('Feature scenarios and classifiers compared');
  const refs = { S1: 'Zhang 2012; Terentev 2023', S2: 'Mandal 2022; Lv 2023', S3: 'Tsai & Philpot 1998', S4: 'Tsai & Philpot 1998', S5: 'Zhang 2012', S6: 'Mandal 2023; Mahlein 2013',
    S7: 'Mandal 2022; Gong 2002', S8: 'Mandal 2023; Tian 2021', S9: 'Lv 2023; Cheng 2011', S10: 'Tian 2021; Lv 2023', S11: 'Huang 2020; Zhu 2017', S12: 'Mandal 2023' };
  table(s, ['', 'Feature scenario', 'Source'], Object.keys(SCN).map((k) => [k, SCN[k], refs[k]]), { x: 0.5, y: 1.2, w: 7.4, colW: [0.6, 4.3, 2.5], fontSize: 11, rowH: 0.36 });
  table(s, ['Classifier', 'Setting'], [['LDA', 'shrinkage, equal priors'], ['PLS-DA', '1-16 latent variables'], ['LR', 'L2, class-balanced'], ['kNN', 'k = 5/15/35, oversampled'],
    ['SVM', 'RBF, class-balanced'], ['LS-SVM', 'kernel ridge form'], ['RF', '200 trees'], ['XGBoost', '300 trees'], ['ELM', 'random tanh layer'], ['MLP', '1-2 hidden layers']],
  { x: 8.2, y: 1.25, w: 4.6, colW: [1.4, 3.2], fontSize: 11, rowH: 0.4 });
  s.addText('Robust selection (S9, S10): ReliefF top 10 % on >= 3 of 4 dates -> |r| < 0.98 -> VIF < 10 -> SFFS-LDA (Tian 2021; Lv 2023).', { x: 0.5, y: 6.3, w: 12.3, h: 0.4, fontSize: 12, italic: true, color: C.accent6, isTextBox: true, margin: 0 });
  source(s, 'Classifier references: Cortes & Vapnik 1995; Suykens & Vandewalle 1999; Breiman 2001; Chen & Guestrin 2016; Huang et al. 2006');
}
{
  const s = content('Supporting experiments: what each one tests');
  const rows = [
    ['E1', 'Raw vs smoothed branch', 'Does SG smoothing / join correction help plot averages?', 'Mandal 2023'],
    ['E2', 'Single-date models', 'Can one date alone separate the plots? How early?', 'Tian 2021'],
    ['E3', 'Leave-one-date / variety-out', 'Transfer to an unseen date or variety (+/- date normalisation)', 'Terentev 2023; Lv 2023'],
    ['E4', 'Date normalisation in CV', 'Does removing the date shift help the pooled model?', 'Lv 2023'],
    ['E5', 'Label-permutation test', 'Is the accuracy above what random labels give?', 'Ojala & Garriga 2010'],
    ['E6', 'Block controls', 'Control vs each block, and block vs block (both diseased)', 'Hurlbert 1984'],
    ['E7', 'OFC from SFFS-LDA/kNN/SVM', 'Optimal feature combinations of disease-sensitive features', 'Tian 2021'],
    ['E8', 'Six published selectors', 'SVM-RFE, LASSO, CARS, ReliefF, SFFS-QDA, Borda', 'Panda 2026 (R1)'],
    ['E9', 'Equal leaf numbers', 'Plot means rebuilt from 3 random leaves per plot', 'This study'],
    ['E10', 'Leaf vs plot level', 'Plot averages vs leaf models of the previous chapter', 'Panda 2026 (R2)'],
  ];
  table(s, ['', 'Experiment', 'Question', 'Basis'], rows, { x: 0.5, y: 1.25, w: 12.3, colW: [0.6, 3.2, 5.9, 2.6], fontSize: 12, rowH: 0.47 });
}

// ================================================================== RESULTS
newSection('5. Results', 'Spectral response, features, classification and robustness checks');
{
  const s = content('R1. Quality control: noise and the leaf-number difference');
  const n = D.noise;
  barChart(s, n.map((r) => r.Date), [['Observed D/H noise ratio', n.map((r) => r.Noise_ratio_D_over_H)], ['Expected from leaf numbers', n.map((r) => r.Expected_ratio_sqrt_n)]], [HX.R, '9E9E9E'],
    { x: 0.5, y: 1.25, w: 6.3, h: 4.2, title: 'Diseased / healthy noise of raw plot averages', valAxisMinVal: 0.6, valAxisMaxVal: 1.1, dataLabelFormatCode: '0.00' });
  table(s, ['Date', 'Leaves H', 'Leaves D', 'p (noise H vs D)'], n.map((r) => [r.Date, f1(r.Leaves_H), f1(r.Leaves_D), pfmt(r.p_MWU_noise)]), { x: 7.1, y: 1.3, w: 5.7, colW: [1.5, 1.2, 1.2, 1.8], fontSize: 12, rowH: 0.38 });
  explain(s, 'qc', { x: 7.1, y: 3.5, w: 5.7, h: 2.9 });
  source(s, 'Sheets 03_QC; Fig25');
}
{
  const s = content('R2. Mean plot-average spectra of healthy and diseased plots');
  const wl = D.spec.wl.map(String);
  DL.forEach((d, k) => {
    const x = 0.5 + (k % 2) * 3.65, y = 1.2 + Math.floor(k / 2) * 2.7;
    lineChart(s, wl, [['Healthy', D.spec[d + '_H']], ['Diseased', D.spec[d + '_D']]], [HX.H, HX.D],
      { x, y, w: 3.55, h: 2.65, title: d, showLegend: k === 0, legendPos: 't', showCatAxisTitle: false, showValAxisTitle: false, titleFontSize: 11, catAxisLabelFontSize: 8, valAxisLabelFontSize: 8 });
  });
  explain(s, 'spectra', { x: 8.0, y: 1.3, w: 4.8, h: 5.2 });
  source(s, '04_Mean_Spectra; Fig02');
}
{
  const s = content('R3. Difference spectra (diseased - healthy) by date');
  const wl = D.spec.wl.map(String);
  lineChart(s, wl, DL.map((d) => [d, D.diff[d]]), DATEC, { x: 0.5, y: 1.25, w: 7.6, h: 5.3, title: 'Reflectance difference D - H', valAxisTitle: 'Reflectance difference', valAxisLabelFormatCode: '0.00' });
  explain(s, 'diff', { x: 8.4, y: 1.3, w: 4.4, h: 5.2 });
  source(s, '04_Mean_Spectra; Zhang et al. 2012; Mandal et al. 2022');
}
{
  const s = content('R4. Band-wise effect sizes and sensitive regions');
  s.addImage({ path: FIG('Fig04_bandwise_effects.png'), x: 0.5, y: 1.2, w: 7.4, h: 4.43 });
  const rg = pick(D.regions, (r) => r.family === 'REF' || r.family === 'FD1').slice(0, 11);
  table(s, ['Family', 'Region (nm)', 'Direction', 'Mean AUC'], rg.map((r) => [r.family, `${r.start_nm}-${r.end_nm}`, r.direction, f3(r.mean_AUC)]),
    { x: 8.15, y: 1.25, w: 4.65, colW: [0.9, 1.45, 1.1, 1.2], fontSize: 10.5, rowH: 0.3 });
  explain(s, 'regions', { x: 0.5, y: 5.75, w: 12.3, h: 0.9, fontSize: 12 });
}
{
  const s = content('R5. Separability of the seven feature families');
  const fs = pick(D.fam_summary, (r) => r.branch === 'raw');
  barChart(s, fs.map((r) => r.family), [['Best stable feature', fs.map((r) => r.best_mean_AUC)], ['Median feature', fs.map((r) => r.median_mean_AUC)]], [HX.R, '9E9E9E'],
    { x: 0.5, y: 1.25, w: 6.4, h: 4.3, title: 'Mean AUC over 4 dates', valAxisMinVal: 0.5, valAxisMaxVal: 1.0 });
  table(s, ['Family', 'Features', 'Sig. >= 3 dates', 'Sig. 4 dates'], fs.map((r) => [D.family_label[r.family], r.n_features, r.n_sig_3dates, r.n_sig_4dates]),
    { x: 7.2, y: 1.25, w: 5.6, colW: [2.6, 0.9, 1.1, 1.0], fontSize: 11, rowH: 0.33 });
  explain(s, 'families', { x: 7.2, y: 4.35, w: 5.6, h: 2.25, fontSize: 12 });
}
{
  const s = content('R6. Most discriminating features of each family');
  const fams = ['REF', 'FD1', 'FD2', 'FD3', 'CR', 'VI', 'RE', 'CWT'];
  const rows = [];
  fams.forEach((f) => pick(D.top, (r) => r.family === f).slice(0, 2).forEach((r) => rows.push([f, r.feature.slice(0, 40), r.direction, r.n_dates_q05,
    heatCell(r.mean_AUC, 0.5, 1, f3), ...DL.map((d) => heatCell(r['AUC_' + d], 0.5, 1, f2))])));
  table(s, ['Family', 'Feature', 'Direction', 'Dates q<0.05', 'Mean AUC', ...DL], rows, { x: 0.5, y: 1.2, w: 12.3, colW: [0.8, 4.0, 1.0, 1.1, 1.0, 1.1, 1.1, 1.1, 1.1], fontSize: 10.5, rowH: 0.31 });
  explain(s, 'topfeat', { x: 0.5, y: 6.25, w: 12.3, h: 0.42, fontSize: 11.5 });
}
{
  const s = content('R7. Vegetation indices: the 15 best of 87');
  const v = D.vi_top;
  barChart(s, v.map((r) => r.feature), [['Mean AUC', v.map((r) => r.mean_AUC)]], [HX.B],
    { x: 0.5, y: 1.25, w: 5.2, h: 5.35, barDir: 'bar', title: 'Mean AUC over 4 dates', valAxisMinVal: 0.5, valAxisMaxVal: 1.0, catAxisLabelFontSize: 9, catAxisOrientation: 'maxMin' });
  table(s, ['Index', 'Equation', 'Reference', 'Min AUC'], v.slice(0, 9).map((r) => [r.feature, (r.Equation || '').slice(0, 44), (r.Reference || '').slice(0, 26), f2(r.min_AUC)]),
    { x: 5.95, y: 1.25, w: 6.85, colW: [1.0, 3.2, 1.9, 0.75], fontSize: 9.5, rowH: 0.33 });
  explain(s, 'vi', { x: 5.95, y: 4.75, w: 6.85, h: 1.85, fontSize: 11.5 });
}
{
  const s = content('R8. Red-edge and continuum-removal parameters');
  const keep = ['REIP, Lagrangian interpolation (nm)', 'Red-edge amplitude Dr (1/nm)', 'Red-edge area SDr', 'Yellow-edge area SDy', 'Red-edge slope (R750 − R700)/50 (1/nm)'];
  const rows = [];
  keep.forEach((p) => pick(D.re, (r) => r.Parameter === p).forEach((r) => rows.push([p.split(' (')[0].slice(0, 30), r.Date, Number(r.Healthy_mean).toPrecision(4), Number(r.Diseased_mean).toPrecision(4), pfmt(r.p_Welch)])));
  table(s, ['Parameter', 'Date', 'Healthy', 'Diseased', 'p'], rows, { x: 0.5, y: 1.2, w: 6.9, colW: [2.6, 0.9, 1.15, 1.15, 1.1], fontSize: 9.5, rowH: 0.24 });
  table(s, ['CR parameter', 'Dir.', 'Mean AUC'], D.cr_top.map((r) => [r.feature.slice(0, 40), r.direction, f3(r.mean_AUC)]), { x: 7.65, y: 1.2, w: 5.15, colW: [3.35, 0.8, 1.0], fontSize: 10, rowH: 0.3 });
  explain(s, 'rededge', { x: 7.65, y: 4.2, w: 5.15, h: 2.4, fontSize: 11.5 });
  source(s, '08_CR_RedEdge_Deriv; Mandal et al. 2022; Gong et al. 2002; Kokaly & Clark 1999');
}
{
  const s = content('R9. Optimised two-band indices and wavelet scalogram');
  s.addImage({ path: FIG('Fig08_optimised_index_map.png'), x: 0.5, y: 1.2, w: 4.35, h: 3.79 });
  s.addImage({ path: FIG('Fig09_CWT_scalogram.png'), x: 5.0, y: 1.2, w: 7.8, h: 2.0 });
  const ix = pick(D.idx, (r) => !r.join_free).filter((r, i, a) => a.findIndex((q) => q.index === r.index) === i || a.filter((q) => q.index === r.index).indexOf(r) < 2);
  table(s, ['Index', 'Bands (nm)', 'Mean r²', 'Min r²'], ix.slice(0, 6).map((r) => [r.index, `${r.band_i}, ${r.band_j}`, f3(r.mean_r2), f3(r.min_r2)]), { x: 5.0, y: 3.4, w: 4.0, colW: [0.8, 1.2, 1.0, 1.0], fontSize: 10.5, rowH: 0.3 });
  explain(s, 'index', { x: 9.25, y: 3.4, w: 3.55, h: 3.2, fontSize: 11 });
  explain(s, 'cwt', { x: 0.5, y: 5.2, w: 8.5, h: 1.4, fontSize: 11 });
}
{
  const s = content('R10. Repeated-measures mixed models');
  const lf = D.lmm_fam;
  barChart(s, lf.map((r) => r.Family), [['Features tested', lf.map((r) => r.n)], ['Disease q < 0.05', lf.map((r) => r.sig)], ['Disease x date q < 0.05', lf.map((r) => r.inter)]], ['9E9E9E', HX.R, HX.B],
    { x: 0.5, y: 1.25, w: 5.8, h: 4.0, title: 'Features with a significant disease effect', dataLabelFormatCode: '0' });
  table(s, ['Feature', 'Effect (SD)', 'q', 'ICC'], D.lmm.slice(0, 10).map((r) => [r.Feature.slice(0, 34), f2(r.Disease_effect_SD), pfmt(r.q_disease), f2(r.ICC_plot)]),
    { x: 6.6, y: 1.25, w: 6.2, colW: [3.4, 1.0, 0.9, 0.9], fontSize: 10.5, rowH: 0.31 });
  explain(s, 'lmm', { x: 0.5, y: 5.45, w: 12.3, h: 1.15, fontSize: 12 });
  source(s, '10_Mixed_Models; Bates et al. 2015');
}
{
  const s = content('R11. PCA and PERMANOVA: date dominates, disease is significant');
  s.addImage({ path: FIG('Fig05_PCA.png'), x: 0.5, y: 1.2, w: 7.2, h: 2.75 });
  const pm = pick(D.permanova, (r) => r.Response.startsWith('SNV') && r.Term !== 'Residual');
  barChart(s, pm.map((r) => r.Term), [['R² (%)', pm.map((r) => r.R2_pct)]], [HX.R], { x: 0.5, y: 4.05, w: 7.2, h: 2.6, barDir: 'bar', title: 'PERMANOVA, SNV reflectance: R² (%)', dataLabelFormatCode: '0.0', catAxisOrientation: 'maxMin' });
  const pm2 = pick(D.permanova, (r) => r.Term !== 'Residual');
  table(s, ['Response', 'Term', 'R² %', 'p'], pm2.map((r) => [r.Response.startsWith('SNV') ? 'Reflectance' : 'Scalar features', r.Term, f1(r.R2_pct), pfmt(r.p_perm)]),
    { x: 7.95, y: 1.2, w: 4.85, colW: [1.45, 1.6, 0.8, 1.0], fontSize: 9.5, rowH: 0.24 });
  explain(s, 'permanova', { x: 7.95, y: 4.85, w: 4.85, h: 1.75, fontSize: 11 });
}
{
  const s = content('R12. Design checks on the features: disease effect vs field position');
  const b = D.block;
  barChart(s, b.map((r) => r.family), [['Control vs inoculated', b.map((r) => r.d_ctrl)], ['Largest block vs block', b.map((r) => r.d_block)]], [HX.R, '9E9E9E'],
    { x: 0.5, y: 1.25, w: 6.4, h: 4.3, title: 'Median |effect size| of top-ranked features' });
  const mt = D.matched;
  table(s, ['Family', ...DL], mt.map((r) => [r.family, ...DL.map((d) => heatCell(r[d], 0, 1, (v) => (100 * v).toFixed(0) + ' %'))]), { x: 7.2, y: 1.3, w: 5.6, colW: [1.2, 1.1, 1.1, 1.1, 1.1], fontSize: 11, rowH: 0.32 });
  s.addText('% of features with a significant matched-control effect (inoculated minus its own control)', { x: 7.2, y: 4.25, w: 5.6, h: 0.4, fontSize: 10, italic: true, color: C.accent6, isTextBox: true, margin: 0 });
  explain(s, 'design', { x: 0.5, y: 5.75, w: 12.3, h: 0.9, fontSize: 11.5 });
}
// ---- classification
{
  const s = content('R13. Main CV: balanced accuracy of 12 feature scenarios x 10 classifiers');
  const rows = Object.keys(SCN).map((k) => [k + ' ' + SCN[k].slice(0, 34), ...CLFS.map((c) => heatCell((SUMK[k + '|' + c] || {}).BA_mean, 0.6, 1.0, f3))]);
  table(s, ['Feature scenario', ...CLFS], rows, { x: 0.5, y: 1.2, w: 12.3, colW: [3.5, ...CLFS.map(() => 0.88)], fontSize: 9.5, rowH: 0.33 });
  explain(s, 'matrix', { x: 0.5, y: 5.65, w: 12.3, h: 1.0, fontSize: 12 });
}
{
  const s = content('R14. Best classifier of every feature scenario');
  const b = D.best_sc;
  barChart(s, b.map((r) => r.scenario), [['Balanced accuracy', b.map((r) => r.BA_mean)], ['MCC', b.map((r) => r.MCC_mean)]], [HX.R, HX.B],
    { x: 0.5, y: 1.25, w: 6.6, h: 5.3, title: 'Best pipeline per scenario (mean of 20 repeats)', valAxisMinVal: 0.4, valAxisMaxVal: 1.0, dataLabelFontSize: 8 });
  table(s, ['Scenario', 'Best clf', 'BA (95 % CI)', 'AUC'], b.map((r) => [r.scenario + ' ' + SCN[r.scenario].slice(0, 20), r.clf, `${f3(r.BA_mean)} (${f3(r.BA_CI95_low)}-${f3(r.BA_CI95_high)})`, f3(r.ROC_AUC_mean)]),
    { x: 7.35, y: 1.25, w: 5.45, colW: [2.15, 0.95, 1.65, 0.7], fontSize: 9.5, rowH: 0.3 });
  explain(s, 'bestsc', { x: 7.35, y: 5.25, w: 5.45, h: 1.35, fontSize: 11 });
}
{
  const s = content('R15. Statistical comparison of classifiers and feature sets');
  const fc = D.friedman_c, fsn = D.friedman_s;
  barChart(s, fc.map((r) => r.clf), [['Average rank', fc.map((r) => r.Average_rank)]], [HX.B], { x: 0.5, y: 1.25, w: 4.0, h: 4.0, barDir: 'bar', title: 'Classifiers: Friedman rank', dataLabelFormatCode: '0.0', catAxisOrientation: 'maxMin' });
  barChart(s, fsn.map((r) => r.scenario), [['Average rank', fsn.map((r) => r.Average_rank)]], [HX.R], { x: 4.6, y: 1.25, w: 4.0, h: 4.0, barDir: 'bar', title: 'Feature sets: Friedman rank', dataLabelFormatCode: '0.0', catAxisOrientation: 'maxMin' });
  const ft = D.friedman;
  table(s, ['Comparison', 'chi²', 'p', 'CD'], ft.map((r) => [r.Comparison.split(' (')[0], f1(r.chi2), pfmt(r.p), f2(r.CD_Nemenyi_0_05)]), { x: 8.85, y: 1.25, w: 3.95, colW: [1.6, 0.8, 0.8, 0.75], fontSize: 10.5, rowH: 0.35 });
  const pw = D.pairwise.slice().sort((a, b) => a.Mean_BA_difference - b.Mean_BA_difference).slice(0, 5);
  table(s, ['Best vs', 'ΔBA', 'p (Holm)'], pw.map((r) => [r.Comparison.split(' vs ')[1], f3(r.Mean_BA_difference), pfmt(r.p_Wilcoxon_Holm)]), { x: 8.85, y: 2.6, w: 3.95, colW: [1.9, 0.9, 1.15], fontSize: 10.5, rowH: 0.3 });
  explain(s, 'friedman', { x: 0.5, y: 5.45, w: 12.3, h: 1.15, fontSize: 12 });
  source(s, 'Demsar 2006; Nadeau & Bengio 2003; Holm 1979');
}
{
  const s = content('R16. Best pipelines: confusion matrices and ROC curves');
  D.cm.forEach((r, i) => {
    const x = 0.5 + i * 2.95;
    s.addText(`${r.Role}: ${r.Pipeline.split(' + ')[0].split(' ')[0]} + ${r.Pipeline.split(' + ')[1]}`, { x, y: 1.2, w: 2.85, h: 0.45, fontSize: 11, bold: true, color: HX.DK, isTextBox: true, margin: 0 });
    const tot0 = r.TN + r.FP, tot1 = r.FN + r.TP;
    table(s, ['Obs \\ Pred', 'H', 'D'], [['Healthy', heatCell(r.TN / tot0, 0, 1, () => `${r.TN}`), heatCell(r.FP / tot0, 0, 1, () => `${r.FP}`)],
      ['Diseased', heatCell(r.FN / tot1, 0, 1, () => `${r.FN}`), heatCell(r.TP / tot1, 0, 1, () => `${r.TP}`)]], { x, y: 1.7, w: 2.75, colW: [1.05, 0.85, 0.85], fontSize: 12, rowH: 0.42 });
    s.addText(`BA ${f3(r.BA)} | MCC ${f3(r.MCC)} | κ ${f3(r.Kappa)}`, { x, y: 3.05, w: 2.85, h: 0.35, fontSize: 10.5, color: HX.INK, isTextBox: true, margin: 0 });
  });
  const rc = D.roc;
  const keys = Object.keys(rc[0]).filter((k) => k.startsWith('TPR_'));
  s.addChart(pres.charts.SCATTER, [{ name: 'FPR', values: rc.map((r) => r.FPR) }].concat(keys.map((k) => ({ name: k.slice(4), values: rc.map((r) => r[k]) }))),
    Object.assign(AX(), { x: 9.3, y: 1.15, w: 3.5, h: 3.4, chartColors: [HX.R, HX.B, HX.H], lineSize: 2, lineDataSymbol: 'none', title: 'Mean ROC', valAxisMaxVal: 1, catAxisMaxVal: 1,
      showCatAxisTitle: true, catAxisTitle: 'False-positive rate', showValAxisTitle: true, valAxisTitle: 'True-positive rate', legendFontSize: 8 }));
  explain(s, 'cm', { x: 0.5, y: 3.6, w: 8.55, h: 3.0, fontSize: 12 });
}
{
  const s = content('R17. Best pipeline by date, variety and inoculation timing');
  const sg = pick(D.subgroups, (r) => r.Role === 'Best overall');
  const byF = (f) => pick(sg, (r) => r.Factor === f);
  const dd = byF('Date'), vv = byF('Variety'), ii = byF('Inoculation');
  barChart(s, dd.map((r) => r.Level), [['BA', dd.map((r) => r.BA)], ['Sensitivity', dd.map((r) => r.Sensitivity)], ['Specificity', dd.map((r) => r.Specificity)]], [HX.R, HX.D, HX.H],
    { x: 0.5, y: 1.25, w: 6.1, h: 3.9, title: 'By date', valAxisMinVal: 0.5, valAxisMaxVal: 1.0, dataLabelFontSize: 8 });
  barChart(s, vv.concat(ii).map((r) => r.Level), [['BA', vv.concat(ii).map((r) => r.BA)]], [HX.B], { x: 6.8, y: 1.25, w: 6.0, h: 3.9, title: 'By variety and inoculation timing', valAxisMinVal: 0.5, valAxisMaxVal: 1.0 });
  explain(s, 'subgroups', { x: 0.5, y: 5.35, w: 12.3, h: 1.25, fontSize: 12 });
}
{
  const s = content('R18. Disease call through the season and by inoculation timing');
  const pg = pick(D.progress, (r) => r.label === 'Diseased');
  const ph = pick(D.progress, (r) => r.label === 'Healthy');
  s.addChart(pres.charts.LINE, ['D1', 'D2', 'D3', 'D4'].map((k) => ({ name: 'Inoculated ' + k, labels: pg.map((r) => r.Date), values: pg.map((r) => r[k]) }))
    .concat([{ name: 'Controls', labels: ph.map((r) => r.Date), values: ph.map((r) => (r.D1 + r.D2 + r.D3 + r.D4) / 4) }]),
  Object.assign(AX(), { x: 0.5, y: 1.25, w: 6.8, h: 4.6, chartColors: [HX.R, HX.D, HX.B, HX.H, '555555'], lineSize: 2, lineDataSymbolSize: 7, title: 'Share of plot-dates called diseased (best pipeline)', valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: '0.0' }));
  const pt = D.prog_tests;
  table(s, ['Date', 'Score H', 'Score D', 'ρ timing', 'p'], pt.map((r) => [r.Date, f2(r.mean_score_H), f2(r.mean_score_D), f2(r.Spearman_inoc_vs_score_diseased), pfmt(r.p_spearman)]),
    { x: 7.6, y: 1.25, w: 5.2, colW: [1.1, 1.0, 1.0, 1.0, 1.1], fontSize: 11, rowH: 0.36 });
  const pdx = D.plot_decision[0];
  s.addText(`Plot decision over 4 dates (mean vote): BA ${f3(pdx.BA)}, sensitivity ${f3(pdx.Sensitivity)}, specificity ${f3(pdx.Specificity)}`, { x: 7.6, y: 3.25, w: 5.2, h: 0.6, fontSize: 12, bold: true, color: HX.DK, isTextBox: true, margin: 0 });
  explain(s, 'progress', { x: 7.6, y: 4.0, w: 5.2, h: 2.6, fontSize: 11.5 });
}
// ---- experiments
if (D.E1) {
  const s = content('R19. E1 - raw vs smoothed plot averages, and E4 - date normalisation');
  const e = D.E1;
  barChart(s, e.map((r) => r.scenario), [['Raw', e.map((r) => r.raw)], ['Smoothed', e.map((r) => r.smooth)]], [HX.R, HX.B], { x: 0.5, y: 1.25, w: 6.1, h: 4.1, title: 'E1: best BA per scenario (same 10 x 4 folds)', valAxisMinVal: 0.5, valAxisMaxVal: 1.0, dataLabelFontSize: 8 });
  if (D.E4) {
    const e4 = D.E4;
    barChart(s, e4.map((r) => r.scenario + ' ' + r.clf), [['Without', e4.map((r) => r.without)], ['With date normalisation', e4.map((r) => r['with'])]], ['9E9E9E', HX.H],
      { x: 6.8, y: 1.25, w: 6.0, h: 4.1, title: 'E4: per-date standardisation', valAxisMinVal: 0.5, valAxisMaxVal: 1.0, dataLabelFontSize: 7, catAxisLabelFontSize: 8 });
  }
  explain(s, 'e1', { x: 0.5, y: 5.55, w: 12.3, h: 1.05, fontSize: 12 });
}
if (D.E2) {
  const s = content('R20. E2 - single-date models (48 plots each)');
  const sc = ['S1', 'S2', 'S5', 'S6', 'S7', 'S8', 'S10'];
  barChart(s, sc.map((k) => k + ' ' + SCN[k].split(' (')[0].slice(0, 18)), DL.map((d) => [d, sc.map((k) => (pick(D.E2, (r) => r.date === d && r.scenario === k)[0] || {}).BA)]), DATEC,
    { x: 0.5, y: 1.25, w: 8.4, h: 5.3, title: 'Best BA per feature set and date', valAxisMinVal: 0.4, valAxisMaxVal: 1.0, showValue: false, catAxisLabelFontSize: 9 });
  explain(s, 'e2', { x: 9.15, y: 1.3, w: 3.65, h: 5.25, fontSize: 12 });
}
if (D.E3) {
  const s = content('R21. E3 - transfer to an unseen date or variety');
  const sc = ['S1', 'S2', 'S6', 'S8', 'S10'];
  const lodo = (dn) => DL.map((d) => Math.max(...pick(D.E3, (r) => r.kind === 'LODO' && r.held_out === d && r.date_norm === dn).map((r) => r.BA)));
  barChart(s, DL, [['Without date normalisation', lodo(false)], ['With date normalisation', lodo(true)]], ['9E9E9E', HX.H], { x: 0.5, y: 1.25, w: 6.1, h: 4.1, title: 'LODO: best BA for the held-out date', valAxisMinVal: 0.3, valAxisMaxVal: 1.0 });
  const vs = ['V1', 'V2', 'V3'];
  barChart(s, vs, sc.map((k) => [k, vs.map((v) => (pick(D.E3, (r) => r.kind === 'LOVO' && r.held_out === v && r.scenario === k)[0] || {}).BA)]), [HX.R, HX.D, HX.B, HX.H, '7A4E9C'],
    { x: 6.8, y: 1.25, w: 6.0, h: 4.1, title: 'LOVO: BA for the held-out variety', valAxisMinVal: 0.3, valAxisMaxVal: 1.0, showValue: false });
  explain(s, 'e3', { x: 0.5, y: 5.55, w: 12.3, h: 1.05, fontSize: 12 });
}
if (D.E5) {
  const s = content('R22. E5 - label-permutation test');
  s.addImage({ path: FIG('Fig19_permutation_test.png'), x: 0.5, y: 1.3, w: 12.3, h: 3.29 });
  table(s, ['Pipeline', 'Observed BA', 'Null mean (SD)', 'Null 95th pct', 'p', 'Permutations'], D.E5.map((r) => [`${r.scenario} ${SCN[r.scenario].split(',')[0]} + ${r.clf}`, f3(r.BA_observed), `${f3(r.BA_null_mean)} (${f3(r.BA_null_sd)})`, f3(r.BA_null_95), pfmt(r.p_value), r.n_perm]),
    { x: 0.5, y: 4.75, w: 7.6, colW: [2.6, 1.0, 1.3, 1.0, 0.8, 0.9], fontSize: 10.5, rowH: 0.36 });
  explain(s, 'e5', { x: 8.35, y: 4.75, w: 4.45, h: 1.85, fontSize: 11.5 });
}
if (D.E6) {
  const s = content('R23. E6 - field-design controls');
  const cons = ['C vs R1', 'C vs R2', 'C vs R3', 'R1 vs R2', 'R1 vs R3', 'R2 vs R3'];
  const sc = ['S2', 'S6', 'S10'];
  barChart(s, cons, sc.map((k) => [k + ' ' + SCN[k].split(',')[0].split(' (')[0], cons.map((c) => (pick(D.E6, (r) => r.contrast === c && r.scenario === k)[0] || {}).BA)]), [HX.R, HX.B, HX.H],
    { x: 0.5, y: 1.25, w: 8.0, h: 5.3, title: 'Balanced accuracy of each contrast (best classifier)', valAxisMinVal: 0.3, valAxisMaxVal: 1.0, dataLabelFontSize: 8 });
  explain(s, 'e6', { x: 8.75, y: 1.3, w: 4.05, h: 5.25, fontSize: 12 });
}
if (D.E7) {
  const s = content('R24. E7 - optimal feature combinations (Tian et al. 2021)');
  const sets = ['All DSFs', 'OFC-LDA', 'OFC-kNN', 'OFC-SVM'], cl = ['LDA', 'kNN', 'SVM', 'LR', 'RF'];
  barChart(s, sets, cl.map((c) => [c, sets.map((f) => (pick(D.E7, (r) => r.feature_set === f && r.clf === c)[0] || {}).BA)]), [HX.B, HX.D, HX.R, HX.H, '7A4E9C'],
    { x: 0.5, y: 1.25, w: 7.6, h: 5.3, title: 'OFC balanced accuracy by classifier', valAxisMinVal: 0.5, valAxisMaxVal: 1.0, showValue: false });
  table(s, ['Set', 'Median size', 'Best BA'], sets.map((f) => { const g = pick(D.E7, (r) => r.feature_set === f); const b = g.reduce((a, r) => (r.BA > a.BA ? r : a), g[0]); return [f, f1(b.features), `${f3(b.BA)} (${b.clf})`]; }),
    { x: 8.35, y: 1.3, w: 4.45, colW: [1.4, 1.2, 1.85], fontSize: 11, rowH: 0.36 });
  explain(s, 'e7', { x: 8.35, y: 3.4, w: 4.45, h: 3.2, fontSize: 11.5 });
}
if (D.E8) {
  const s = content('R25. E8 - six published feature-selection methods (Panda 2026)');
  const ms = ['SVM-RFE', 'LASSO', 'CARS', 'ReliefF', 'SFFS (QDA)', 'Consensus (Borda)'], ks = [5, 10, 15];
  const best = (m, k) => Math.max(...pick(D.E8, (r) => r.method === m && Number(r.k) === k).map((r) => r.BA));
  barChart(s, ms, ks.map((k) => ['k = ' + k, ms.map((m) => best(m, k))]), [HX.B, HX.R, HX.H], { x: 0.5, y: 1.25, w: 7.6, h: 5.3, title: 'Best BA by selector and subset size', valAxisMinVal: 0.5, valAxisMaxVal: 1.0, showValue: false });
  explain(s, 'e8', { x: 8.35, y: 1.3, w: 4.45, h: 5.25, fontSize: 12 });
}
if (D.E9) {
  const s = content('R26. E9 - equal leaf numbers: is the separation a leaf-count artefact?');
  const sc = ['S1', 'S2', 'S3', 'S4', 'S6'];
  const g = (a, k) => (pick(D.E9, (r) => r.averaging === a && r.scenario === k)[0] || {}).BA;
  const lab = sc.map((k) => k === 'S6' ? 'S6 Vegetation indices (46)' : k + ' ' + SCN[k].split(',')[0].split(' (')[0]);
  barChart(s, lab, [['All leaves (as in the workbooks)', sc.map((k) => g('all leaves (re-built)', k))], ['3 random leaves per plot', sc.map((k) => g('3 random leaves per plot', k))]], [HX.R, HX.B],
    { x: 0.5, y: 1.25, w: 7.6, h: 5.3, title: 'Balanced accuracy (best of LDA / LR / SVM)', valAxisMinVal: 0.4, valAxisMaxVal: 1.0 });
  explain(s, 'e9', { x: 8.35, y: 1.3, w: 4.45, h: 5.25, fontSize: 12 });
}
if (D.E10) {
  const s = content('R27. E10 - plot-average models vs leaf-level models');
  const e = D.E10;
  barChart(s, e.map((r) => r.Approach.replace(' (this analysis)', '').replace('Leaf models, majority vote per plot-date', 'Leaf models, plot-date vote')),
    [['Balanced accuracy', e.map((r) => r.BA)], ['MCC', e.map((r) => r.MCC)]], [HX.R, HX.B], { x: 0.5, y: 1.25, w: 7.6, h: 5.3, title: 'Leaf level vs plot level', valAxisMinVal: 0.4, valAxisMaxVal: 1.0, catAxisLabelFontSize: 9 });
  table(s, ['Approach', 'Pipeline', 'BA'], e.map((r) => [r.Unit, r.Pipeline.slice(0, 32), f3(r.BA)]), { x: 8.35, y: 1.3, w: 4.45, colW: [1.1, 2.55, 0.8], fontSize: 10, rowH: 0.38 });
  explain(s, 'e10', { x: 8.35, y: 3.4, w: 4.45, h: 3.2, fontSize: 11.5 });
}
{
  const s = content('R28. Final feature set: importance, correlation and VIF');
  const f = D.final;
  barChart(s, f.map((r) => r.Feature.slice(0, 26)), [['Permutation importance', f.map((r) => r.Perm_importance_BA)]], [HX.R],
    { x: 0.5, y: 1.25, w: 5.0, h: 4.2, barDir: 'bar', title: 'Drop in BA when permuted', dataLabelFormatCode: '0.000', catAxisLabelFontSize: 9, catAxisOrientation: 'maxMin' });
  const cn = D.final_corr.names;
  const rows = cn.map((n, i) => [n.slice(0, 18), ...D.final_corr.values[i].map((v) => heatCell(Math.abs(v), 0, 1, () => f2(v)))]);
  table(s, ['', ...cn.map((n) => n.slice(0, 9))], rows, { x: 5.7, y: 1.25, w: 7.1, colW: [1.6, ...cn.map(() => 5.5 / cn.length)], fontSize: 8.5, rowH: 0.3 });
  table(s, ['Feature', 'Family', 'AUC', 'g', 'VIF'], f.map((r) => [r.Feature.slice(0, 30), r.Family.split(' ')[0], f3(r.AUC), f2(r.Hedges_g), f2(r.VIF)]),
    { x: 5.7, y: 1.4 + 0.3 * (cn.length + 1), w: 7.1, colW: [3.2, 1.3, 0.85, 0.85, 0.9], fontSize: 9.5, rowH: 0.27 });
  explain(s, 'final', { x: 0.5, y: 5.6, w: 5.0, h: 1.0, fontSize: 11 });
}
{
  const s = content('Summary of results');
  const rows = (NARR.summary_rows || []).map((r) => [r[0], r[1]]);
  table(s, ['Question', 'Answer from the analysis'], rows, { x: 0.5, y: 1.25, w: 12.3, colW: [3.4, 8.9], fontSize: 12, rowH: 0.5 });
}

// ================================================================== DISCUSSION
newSection('6. Discussion and conclusions', 'What the plot-level results mean');
{
  const s = content('Discussion 1: what white rust does to the plot-average spectrum');
  card(s, 0.5, 1.3, 6.0, 5.25, 'Spectral mechanism', (NARR.disc_mech || []).join('\n\n'), HX.H, 12.5);
  card(s, 6.8, 1.3, 6.0, 5.25, 'Why derivatives and wavelets win', (NARR.disc_feat || []).join('\n\n'), HX.B, 12.5);
}
{
  const s = content('Discussion 2: comparison with the reviewed studies');
  table(s, ['Study', 'Their finding', 'This study (plot level)'], NARR.compare || [], { x: 0.5, y: 1.25, w: 12.3, colW: [2.3, 4.8, 5.2], fontSize: 11, rowH: 0.52 });
}
{
  const s = content('Discussion 3: is the separation really disease? Evidence and caveats');
  card(s, 0.5, 1.3, 6.0, 5.25, 'Evidence for a disease effect', (NARR.disc_evidence || []).join('\n\n'), HX.H, 12);
  card(s, 6.8, 1.3, 6.0, 5.25, 'Caveats', (NARR.disc_caveats || []).join('\n\n'), HX.R, 12);
}
{
  const s = content('Recommended plot-level protocol');
  const steps = NARR.protocol || [];
  steps.forEach((st, i) => {
    const y = 1.3 + i * 0.76;
    s.addShape(pres.shapes.OVAL, { x: 0.6, y, w: 0.6, h: 0.6, fill: { color: C.accent1 }, line: { color: C.accent1 } });
    s.addText(String(i + 1), { x: 0.6, y, w: 0.6, h: 0.6, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    s.addText([{ text: st[0] + ': ', options: { bold: true, color: HX.DK } }, { text: st[1], options: { color: HX.INK } }], { x: 1.4, y: y - 0.05, w: 11.4, h: 0.7, fontSize: 14, valign: 'middle', isTextBox: true, margin: 0 });
  });
}
{
  const s = content('Conclusions');
  bullets(s, NARR.conclusions || [], { x: 0.5, y: 1.25, w: 12.3, h: 5.4, fontSize: 15 });
}
{
  const s = content('Limitations and future work');
  card(s, 0.5, 1.3, 6.0, 5.25, 'Limitations', (NARR.limitations || []).join('\n\n'), HX.R, 12.5);
  card(s, 6.8, 1.3, 6.0, 5.25, 'Future work', (NARR.future || []).join('\n\n'), HX.H, 12.5);
}

// ================================================================== REFERENCES
pres.addSection({ title: 'References' }); section = 'References';
const refs = D.refs;
const groups = [['Papers reviewed (provided by the researcher)', refs.filter((r) => r.ID.startsWith('P') || r.ID.startsWith('R'))],
  ['Methods', refs.filter((r) => r.ID.startsWith('M'))], ['Feature-selection methods', refs.filter((r) => r.ID.startsWith('F'))],
  ['Vegetation index and red-edge sources', refs.filter((r) => r.ID.startsWith('I'))]];
groups.forEach(([gname, list]) => {
  const per = 16;
  for (let i = 0; i < list.length; i += per) {
    const s = content('References: ' + gname.split(' (')[0].toLowerCase() + (i ? ' (cont.)' : ''));
    const chunk = list.slice(i, i + per);
    s.addText(chunk.map((r, k) => ({ text: r.Reference.replace('[P] ', '').replace('[R] ', ''), options: { breakLine: k < chunk.length - 1, paraSpaceAfter: 4 } })),
      { x: 0.5, y: 1.2, w: 12.3, h: 5.75, fontSize: 10.5, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  }
});
{
  const s = pres.addSlide({ masterName: 'SECTION', sectionTitle: section });
  s.addText('Thank you', { placeholder: 'title' });
  s.addText('Questions and suggestions are welcome', { placeholder: 'body' });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log('wrote', OUT);
})();
