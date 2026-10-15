// PhD seminar deck: hyperspectral detection of white rust in Indian mustard.
// Native (editable) charts and tables are built from cache/ppt_data.json; heat maps are figures.
const path = require('path');
const pptxgen = require('pptxgenjs');
const SKILL = '/root/.claude/skills/synced/4f45d97b-0a27-4cd4-81ca-4f53ae4b645e_3447a982-a016-432c-b6ed-4390ec73d1e4/pptx';
const { applyTheme } = require(path.join(SKILL, 'scripts/apply_theme.js'));
const ROOT = path.join(__dirname, '..');
const D = require(path.join(ROOT, 'cache/ppt_data.json'));
const NARR = require(path.join(ROOT, 'scripts/narrative.json'));
const FIG = (n) => path.join(ROOT, 'outputs/figures', n);
const OUT = path.join(ROOT, 'outputs/WhiteRust_Mustard_PhD_Seminar.pptx');

const THEME = {
  name: 'Mustard White Rust', headFontFace: 'Cambria', bodyFontFace: 'Calibri',
  colors: { dk1: '1A1A1A', lt1: 'FFFFFF', dk2: '1F3D2B', lt2: 'EEF3EC', accent1: '2E7D32', accent2: 'D08A00',
            accent3: '2A6FB0', accent4: 'B03A2E', accent5: '6B8E23', accent6: '6E6E6E', hlink: '2A6FB0', folHlink: '7A4E9C' },
};
const HX = { H: '2E7D32', D: 'D08A00', B: '2A6FB0', R: 'B03A2E', G: '6E6E6E', DK: '1F3D2B', LT: 'EEF3EC', INK: '1A1A1A', GRID: 'E3E3E3' };
const DATEC = [HX.B, HX.H, HX.D, HX.R];

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE'; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = 'Hyperspectral detection of white rust in Indian mustard';
pres.author = 'PhD research seminar';
const C = pres.SchemeColor;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: 'TITLE', background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.8, y: 1.7, w: 11.7, h: 2.2, fontSize: 38, bold: true, color: C.background1, valign: 'bottom', fontFace: THEME.headFontFace }, text: '' } },
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
    { placeholder: { options: { name: 'title', type: 'title', x: 0.5, y: 0.28, w: 12.3, h: 0.8, fontSize: 28, bold: true, color: C.text2, fontFace: THEME.headFontFace, valign: 'middle' }, text: '' } },
    { text: { text: 'White rust detection in Indian mustard  |  PhD research seminar', options: { x: 0.5, y: 7.08, w: 7, h: 0.3, fontSize: 9, color: C.accent6 } } },
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
  s.addText('Source: ' + txt, { x: 0.5, y: 6.72, w: 12.3, h: 0.32, fontSize: 10, italic: true, color: C.accent6, isTextBox: true, margin: 0 });
}
function bullets(s, items, opt) {
  const runs = items.map((it, i) => {
    const o = { bullet: it.sub ? { indent: 18 } : true, indentLevel: it.sub ? 1 : 0, breakLine: i < items.length - 1, paraSpaceAfter: 6 };
    if (typeof it === 'string') return { text: it, options: o };
    return { text: it.t, options: Object.assign(o, it.b ? { bold: true } : {}) };
  });
  s.addText(runs, Object.assign({ x: 0.5, y: 1.25, w: 6, h: 5.3, fontSize: 15, color: C.text1, valign: 'top', isTextBox: true }, opt));
}
function card(s, x, y, w, h, head, body, color) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 } });
  s.addShape(pres.shapes.OVAL, { x: x + 0.18, y: y + 0.2, w: 0.42, h: 0.42, fill: { color: color || C.accent1 }, line: { color: color || C.accent1 } });
  s.addText(head, { x: x + 0.72, y: y + 0.13, w: w - 0.85, h: 0.56, fontSize: 15, bold: true, color: C.text2, valign: 'middle', isTextBox: true, margin: 0 });
  s.addText(body, { x: x + 0.2, y: y + 0.78, w: w - 0.4, h: h - 0.9, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
}
function stat(s, x, y, w, big, small, color) {
  s.addText(big, { x, y, w, h: 0.85, fontSize: 40, bold: true, color: color || C.accent1, fontFace: THEME.headFontFace, align: 'left', isTextBox: true, margin: 0 });
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
function spectraChart(s, series, colors, o) {
  const wl = D.spec.Wavelength_nm.map(String);
  const data = series.map(([name, vals]) => ({ name, labels: wl, values: vals }));
  s.addChart(pres.charts.LINE, data, Object.assign(AX(), {
    x: 0.5, y: 1.25, w: 6.2, h: 4.4, chartColors: colors, lineSize: 2, lineDataSymbol: 'none',
    catAxisLabelFrequency: 20, showCatAxisTitle: true, catAxisTitle: 'Wavelength (nm)', showValAxisTitle: true,
  }, o));
}
const f3 = (v) => (v === null || v === undefined || isNaN(v) ? '-' : Number(v).toFixed(3));
const f2 = (v) => (v === null || v === undefined || isNaN(v) ? '-' : Number(v).toFixed(2));
const f1 = (v) => (v === null || v === undefined || isNaN(v) ? '-' : Number(v).toFixed(1));
const pct = (v) => (100 * v).toFixed(1) + '%';
const pfmt = (p) => (p < 0.001 ? '< 0.001' : Number(p).toFixed(3));
const SCN = D.scenarios || {};
const CLFS = ['LDA', 'PLS-DA', 'LR', 'kNN', 'SVM', 'LS-SVM', 'RF', 'XGBoost', 'ELM', 'MLP'];
const SUMK = {}; (D.summary || []).forEach((r) => { SUMK[r.scenario + '|' + r.clf] = r; });
const BEST = (D.best || [])[0] || {}; const COMPACT = (D.best || [])[1] || {};
const BS = SUMK[BEST.scenario + '|' + BEST.clf] || {}; const CS = SUMK[COMPACT.scenario + '|' + COMPACT.clf] || {};
const pipeName = (r) => `${r.scenario} ${SCN[r.scenario] || ''} + ${r.clf}`;

// ================================================================== TITLE
{
  pres.addSection({ title: 'Opening' }); section = 'Opening';
  const s = pres.addSlide({ masterName: 'TITLE', sectionTitle: section });
  s.addText('Hyperspectral detection of white rust (Albugo candida) in Indian mustard', { placeholder: 'title' });
  s.addText([
    { text: 'Development of a pooled prediction model from ASD contact-probe spectra across dates, varieties and growth stages', options: { breakLine: true } },
    { text: ' ', options: { breakLine: true, fontSize: 10 } },
    { text: 'PhD research seminar  |  Methodology - Results - Discussion', options: { fontSize: 15 } },
  ], { placeholder: 'body' });
  s.addNotes('Opening: the talk covers the study design, a literature-derived methodology, the full analysis and the discussion of results.');
}
{
  const s = content('Outline of the seminar');
  const items = [['1', 'Introduction', 'White rust, why spectra can detect it, research gaps'], ['2', 'Review of literature', 'Ten studies that shaped the methodology'],
    ['3', 'Objectives', 'Six objectives and hypotheses'], ['4', 'Materials and methods', 'Data, QC, features, selection, classifiers, validation'],
    ['5', 'Results', 'Spectral response, separability, features, models, transfer tests'], ['6', 'Discussion and conclusions', 'Comparison with literature, limitations, future work']];
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
newSection('1. Introduction', 'White rust of Indian mustard and the case for hyperspectral detection');
{
  const s = content('White rust is a major foliar disease of Indian mustard');
  bullets(s, [
    { t: 'Pathogen: Albugo candida (oomycete), an obligate biotroph of crucifers', b: true },
    'Symptoms: white, blister-like sori (pustules), mainly on the lower leaf surface; chlorosis; staghead on inflorescences',
    'Yield losses are large in epidemic years; fungicide timing depends on early detection',
    'Visual scoring is slow, subjective and cannot see pre-visual physiology',
    { t: 'Leaf spectroscopy measures pigment, structure and water changes caused by infection', b: true },
    'Question: can one model detect white rust whatever the date, variety or growth stage?',
  ], { w: 6.3 });
  card(s, 7.1, 1.3, 5.7, 1.6, 'Pigments (400-700 nm)', 'Chlorophyll, carotenoid and anthocyanin losses raise visible reflectance and shift the red edge.', HX.H);
  card(s, 7.1, 3.05, 5.7, 1.6, 'Structure (700-1300 nm)', 'Mesophyll disruption by haustoria changes NIR scattering; white pustules can raise reflectance.', HX.B);
  card(s, 7.1, 4.8, 5.7, 1.6, 'Water and dry matter (1300-2400 nm)', 'Water loss raises SWIR reflectance around 1450 and 1940 nm; cellulose/protein near 2100 nm.', HX.D);
  source(s, 'Saharan et al. (2014); Zhang et al. (2012); Tian et al. (2021); Lv et al. (2023)');
}
{
  const s = content('Research gaps identified from the literature');
  const gaps = [
    ['Single-date models', 'Most studies fit one date or one experiment; pooled models across dates, varieties and stages are rare (Tian et al., 2021; Lv et al., 2023).'],
    ['Leakage in validation', 'Random spectrum-level splits mix repeated measurements of the same plot into train and test; feature selection on all data inflates accuracy (Varma & Simon, 2006).'],
    ['Few comparisons of feature types', 'Bands, indices, derivatives, continuum removal and wavelets are seldom compared under one validation design (Lv et al., 2023).'],
    ['No white-rust spectral index', 'Disease-specific indices exist for blast, rusts and mildew (Mahlein et al., 2013; Mandal et al., 2023) but not for Albugo candida on mustard.'],
  ];
  gaps.forEach((g, i) => card(s, 0.5 + (i % 2) * 6.2, 1.3 + Math.floor(i / 2) * 2.65, 6.0, 2.45, g[0], g[1], [HX.R, HX.D, HX.B, HX.H][i]));
  source(s, 'Synthesis of the ten reviewed studies; Roberts et al. (2017)');
}

// ================================================================== LITERATURE
newSection('2. Review of literature', 'Ten studies on spectral disease detection used to build the methodology');
{
  const s = content('Reviewed studies: designs, methods and best reported accuracy');
  const rows = [
    ['Mandal et al. 2022, 2023', 'Rice blast', 'ASD canopy', 'SG, GA-PLS, J-M, VIs, NDSI map, PLS/RF/SVM', 'SVM R² 0.94; 10-class acc. 0.61'],
    ['Selvaprakash et al. 2026', 'Rice blast', 'ASD leaf', 'SNV/MSC, derivatives, PCA/t-SNE, Isolation Forest, RF', 'RBI F1 0.95'],
    ['Tian et al. 2021', 'Rice leaf blast', 'ASD leaf clip', 'Bands+VIs+CWT, stability, VIF, SFFS', 'OA 65-98.7% (stage)'],
    ['Lv et al. 2023', 'Maize SCLB', 'PSR leaf clip', 'Date norm., FSD+CWT+SB/SI, RELIEF-F, SFFS-SVM', 'OA 87.1% (asympt.)'],
    ['Terentev et al. 2023', 'Wheat leaf rust', 'HSI 450-850 nm', 'Band means, VIs, texture, cross-experiment SVM', 'Acc. 98%'],
    ['Zhang et al. 2012', 'Wheat powdery mildew', 'ASD + sphere', 'Derivative, CR, VIs, PLSR, FLDA', 'OA 0.89, κ 0.84'],
    ['Zhu et al. 2017', 'Tobacco TMV', 'HSI 380-1023 nm', 'SPA, texture, PLS-DA/LS-SVM/ELM/BPNN', 'Acc. 98.3%'],
    ['Huang et al. 2020', 'Wheat FHB', 'HSI 400-1000 nm', 'SPA, colour/texture, PSO-SVM', 'Acc. 92%'],
    ['Nguyen et al. 2023', 'Wheat yellow rust', 'UAV 5-band', 'VIs, GLCM, PCA, SVM/RF/MLP/3D-CNN', 'OA 79%'],
  ];
  table(s, ['Study', 'Crop / disease', 'Sensor', 'Key methods', 'Best result'], rows, { x: 0.5, y: 1.25, w: 12.3, colW: [2.3, 1.9, 1.7, 4.3, 2.1], fontSize: 12, rowH: 0.48 });
  source(s, 'Papers provided by the researcher (see references)');
}
{
  const s = content('What each study contributed to this methodology');
  const rows = [
    ['Data quality', 'Splice correction, edge trimming, SG smoothing, Isolation Forest outliers', 'Selvaprakash 2026; Mandal 2023; Hueni & Bialek 2017'],
    ['Preprocessing', 'SNV / MSC, first derivative, date normalisation to a healthy baseline', 'Selvaprakash 2026; Lv 2023; Zhang 2012'],
    ['Spectral characterisation', 'Mean/difference/ratio spectra, correlation spectrum, red-edge parameters, J-M', 'Zhang 2012; Mandal 2022, 2023'],
    ['Feature families', 'Bands, 46 VIs, NDSI search, derivatives, continuum removal, CWT', 'Mandal 2023; Lv 2023; Tian 2021; Zhang 2012'],
    ['Feature selection', 'RELIEF-F, temporal stability, VIF < 10, SFFS; OFCs (SFFS-LDA/kNN/SVM); SPA; GA-PLS', 'Tian 2021; Lv 2023; Zhu 2017; Huang 2020; Mandal 2023'],
    ['Classifiers', 'LDA, PLS-DA, LR, kNN, SVM, LS-SVM, RF, XGBoost, ELM, MLP', 'Zhu 2017; Nguyen 2023; Tian 2021; Mandal 2023'],
    ['Validation', '4-fold CV x repeats; cross-experiment / cross-date transfer; macro-F1, κ', 'Tian 2021; Lv 2023; Terentev 2023; Nguyen 2023'],
    ['Not applicable', 'Image texture/colour, 3D-CNN, severity regression (no images, no scores)', 'Huang 2020; Zhu 2017; Nguyen 2023; Mandal 2023'],
  ];
  table(s, ['Step', 'Method adopted', 'From'], rows, { x: 0.5, y: 1.25, w: 12.3, colW: [2.3, 6.2, 3.8], fontSize: 12, rowH: 0.56 });
  source(s, 'Synthesis by the author');
}

// ================================================================== OBJECTIVES
newSection('3. Objectives', 'Six objectives and testable hypotheses');
{
  const s = content('Objectives and hypotheses');
  const rows = [
    ['O1', 'Characterise the spectral response of mustard leaves to white rust', 'H1: VIS/red-edge reflectance rises; NIR and SWIR change with structure and water'],
    ['O2', 'Partition spectral variance into disease vs date, variety and stage', 'H2: disease is significant after accounting for nuisance factors'],
    ['O3', 'Identify disease features stable across dates and varieties', 'H3: a few bands/indices/derivatives/wavelets separate classes on every date'],
    ['O4', 'Develop a novel Mustard White Rust Index (MWRI)', 'H4: an optimal band pair beats published indices'],
    ['O5', 'Compare feature types, selection methods and 10 classifiers', 'H5: combined, selected features match or beat single families'],
    ['O6', 'Test transfer to unseen dates, varieties and stages', 'H6: accuracy holds when a whole date/variety/stage is held out'],
  ];
  table(s, ['#', 'Objective', 'Hypothesis'], rows, { x: 0.5, y: 1.3, w: 12.3, colW: [0.6, 5.9, 5.8], fontSize: 13, rowH: 0.75 });
}

// ================================================================== METHODS
newSection('4. Materials and methods', 'Data, quality control, features, selection, classifiers and validation');
{
  const s = content('Experimental material and dataset');
  stat(s, 0.6, 1.35, 2.8, '48', 'plots (3 varieties x 16)', HX.H);
  stat(s, 3.5, 1.35, 2.8, '4', 'measurement dates', HX.B);
  stat(s, 0.6, 2.9, 2.8, String(D.n_raw), 'contact-probe spectra', HX.D);
  stat(s, 3.5, 2.9, 2.8, '1 : ' + (D.n_d / D.n_h).toFixed(1), 'healthy : diseased', HX.R);
  bullets(s, [
    'ASD FieldSpec with contact probe, 350-2500 nm at 1 nm',
    'Plots 1-12 healthy, 13-48 diseased (4 + 12 per variety)',
    'Each plot measured on every date: 192 plot-date units',
    'Stages: vegetative, flowering, pod formation',
    'Severity and leaf-layer fields were empty: binary task',
  ], { x: 0.5, y: 4.45, w: 6.0, h: 2.2, fontSize: 14 });
  const rows = D.design.map((r) => [r.Date, r.Healthy, r.Diseased, r.Healthy + r.Diseased]);
  rows.push(['Total', D.n_h, D.n_d, D.n_raw]);
  table(s, ['Date', 'Healthy', 'Diseased', 'Total'], rows, { x: 7.0, y: 1.3, w: 5.8, colW: [1.6, 1.4, 1.4, 1.4], fontSize: 13, rowH: 0.4 });
  s.addChart(pres.charts.BAR, [{ name: 'Healthy', labels: D.design_stage.map((r) => r.stage), values: D.design_stage.map((r) => r.Healthy) },
    { name: 'Diseased', labels: D.design_stage.map((r) => r.stage), values: D.design_stage.map((r) => r.Diseased) }],
  Object.assign(AX(), { x: 7.0, y: 3.95, w: 5.8, h: 2.7, barDir: 'col', chartColors: [HX.H, HX.D], title: 'Spectra by growth stage', showValue: true, dataLabelPosition: 'outEnd', valAxisHidden: true, valGridLine: { style: 'none' } }));
}
{
  const s = content('Analysis workflow');
  const steps = [
    ['1', 'Data assembly', '4 workbooks -> 2339 spectra + metadata'],
    ['2', 'Quality control', 'Splice fix, trim 400-2400 nm, consensus outliers'],
    ['3', 'Preprocessing', 'SG smoothing, 10-nm, SNV / MSC / derivative / date-norm'],
    ['4', 'Characterisation', 'Spectra, FDR tests, J-M, PCA, PERMANOVA, LMM'],
    ['5', 'Features F1-F6', 'Bands, VIs, NDSI, derivatives, CR, CWT'],
    ['6', 'Selection', 'ReliefF + stability + VIF + SFFS; SPA; GA-PLS'],
    ['7', 'Classification', '10 classifiers, inner-CV tuning, class weights'],
    ['8', 'Validation', '25 x 4-fold nested plot-grouped CV'],
    ['9', 'Transfer & extras', 'Unseen date/variety/stage, sensors, learning curve'],
    ['10', 'Interpretation', 'Importance, SHAP, selection stability'],
  ];
  steps.forEach((st, i) => {
    const col = i % 5, row = Math.floor(i / 5);
    const x = 0.5 + col * 2.5, y = 1.45 + row * 2.6;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.25, h: 2.2, rectRadius: 0.08, fill: { color: row ? C.background2 : 'F7F1E1' }, line: { color: row ? C.background2 : 'F7F1E1' } });
    s.addShape(pres.shapes.OVAL, { x: x + 0.15, y: y + 0.15, w: 0.5, h: 0.5, fill: { color: row ? C.accent1 : C.accent2 }, line: { color: row ? C.accent1 : C.accent2 } });
    s.addText(st[0], { x: x + 0.15, y: y + 0.15, w: 0.5, h: 0.5, fontSize: 14, bold: true, color: C.background1, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    s.addText(st[1], { x: x + 0.15, y: y + 0.75, w: 1.95, h: 0.45, fontSize: 15, bold: true, color: C.text2, isTextBox: true, margin: 0 });
    s.addText(st[2], { x: x + 0.15, y: y + 1.2, w: 1.95, h: 0.9, fontSize: 12, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
    if (col < 4) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.27, y: y + 0.95, w: 0.2, h: 0.3, fill: { color: 'BDBDBD' }, line: { color: 'BDBDBD' } });
  });
  s.addText('Leakage rule: every step that learns from labels (MSC, date normalisation, NDSI search, feature selection, tuning) is fitted on training plots only.',
    { x: 0.5, y: 6.65, w: 12.3, h: 0.35, fontSize: 13, italic: true, color: C.accent4, isTextBox: true, margin: 0 });
}
{
  const s = content('Quality control and preprocessing');
  const rows = [
    ['Splice correction', 'Additive offset at 1000/1001 and 1800/1801 nm detector joins', 'Hueni & Bialek 2017'],
    ['Edge trimming', 'Keep 400-2400 nm (noisy 350-400 nm removed)', 'Mandal et al. 2023'],
    ['Outlier screening', 'Hotelling T², Q residual, Isolation Forest, SAM to plot median; removed if >= 3 of 4', 'Selvaprakash et al. 2026; Liu et al. 2008'],
    ['Smoothing', 'Savitzky-Golay, 11 nm window, 2nd-order polynomial', 'Savitzky & Golay 1964'],
    ['Resampling', '10-nm band averages (201 bands)', 'Mandal et al. 2023'],
    ['Scatter correction', 'SNV; MSC (reference from training folds)', 'Barnes et al. 1989; Geladi et al. 1985'],
    ['Derivatives', 'SG first and second derivatives', 'Tsai & Philpot 1998'],
    ['Date normalisation', 'Ratio of training healthy mean per date to baseline date', 'Lv et al. 2023'],
  ];
  table(s, ['Step', 'Implementation', 'Reference'], rows, { x: 0.5, y: 1.25, w: 12.3, colW: [2.4, 6.6, 3.3], fontSize: 12, rowH: 0.55 });
  source(s, 'Methods adapted from the reviewed papers; parameters fixed before modelling');
}
{
  const s = content('Statistical characterisation of the spectra');
  card(s, 0.5, 1.3, 4.0, 2.55, 'Band-wise tests', 'Welch t and Mann-Whitney on plot-date means (n = 192) to avoid pseudo-replication; Benjamini-Hochberg FDR; Cohen d; point-biserial r.', HX.H);
  card(s, 4.65, 1.3, 4.0, 2.55, 'Separability', 'Jeffries-Matusita distance per band, per index and for the final feature set (0 = none, 2 = complete).', HX.B);
  card(s, 8.8, 1.3, 4.0, 2.55, 'Red-edge parameters', 'REP (linear interpolation and derivative maximum), REV, edge amplitudes/positions/sums for blue, yellow and red edges.', HX.D);
  card(s, 0.5, 4.0, 4.0, 2.55, 'Unsupervised views', 'PCA and t-SNE on SNV spectra coloured by class, date, variety and stage; eta² of PC scores per factor.', HX.R);
  card(s, 4.65, 4.0, 4.0, 2.55, 'PERMANOVA', 'Variance partitioning of SNV spectra: disease, date, variety, stage and interactions; restricted permutations (999).', HX.H);
  card(s, 8.8, 4.0, 4.0, 2.55, 'Mixed models', 'feature ~ disease + date + variety + (1 | plot); LRT for disease x date interaction.', HX.B);
  source(s, 'Benjamini & Hochberg 1995; Richards & Jia 2006; Mandal et al. 2022, 2023; Zhang et al. 2012; Anderson 2001; Bates et al. 2015; van der Maaten & Hinton 2008');
}
{
  const s = content('Feature families (F1-F6)');
  const rows = [
    ['F1', 'Reflectance bands (SNV, 10 nm)', '201', 'Mandal 2023; Terentev 2023'],
    ['F2', 'Published vegetation indices + red-edge parameters', '46', 'Mandal 2023; Tian 2021; Mahlein 2013'],
    ['F3', 'Novel NDSI from exhaustive band-pair search (in-fold)', '3', 'Mandal 2023; Selvaprakash 2026'],
    ['F4', 'First-derivative bands, derivative indices, edge features', '221', 'Lv 2023; Zhang 2012'],
    ['F5', 'Continuum removal: depth, width, area, position (6 features)', '24', 'Zhang 2012; Kokaly & Clark 1999'],
    ['F6', 'CWT, Mexican hat, scales 2^1-2^8, every 10 nm', '1608', 'Tian 2021; Lv 2023; Cheng et al. 2011'],
  ];
  table(s, ['', 'Feature family', 'n', 'Reference'], rows, { x: 0.5, y: 1.3, w: 8.0, colW: [0.5, 4.4, 0.7, 2.4], fontSize: 12, rowH: 0.62 });
  card(s, 8.8, 1.3, 4.0, 2.4, 'Index groups (F2)', 'Chlorophyll (NDVI, MCARI, MTCI...), carotenoid/anthocyanin (PRI, CRI, ARI, PSRI), red edge (REP, Vog), water (WI, NDWI, MSI, DWSI), dry matter (CAI, NDLI) and disease indices (HI, PMI, LRDSI, RBI).', HX.H);
  card(s, 8.8, 3.85, 4.0, 2.7, 'Not used', 'Image texture and colour features (GLCM, colour moments) need images; the contact probe gives point spectra. PROSPECT inversion left for future work.', HX.G);
  source(s, 'Feature definitions in workbook sheets 13 and 16');
}
{
  const s = content('Robust feature selection (inside every training fold)');
  const st = [['ReliefF per date', 'Rank all features separately within each date (k = 10 neighbours)'], ['Temporal stability', 'Keep features in the top 10% on >= 3 of 4 dates'],
    ['Redundancy', 'Drop features with |r| >= 0.98 to a better-ranked feature'], ['VIF < 10', 'Iteratively remove collinear features'], ['SFFS-LDA', 'Floating forward search, inner plot-grouped CV, <= 10 features']];
  st.forEach((x, i) => {
    const y = 1.35 + i * 1.02;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 6.2, h: 0.85, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 } });
    s.addText(String(i + 1), { x: 0.65, y: y + 0.17, w: 0.5, h: 0.5, fontSize: 14, bold: true, color: C.background1, align: 'center', valign: 'middle', shape: pres.shapes.OVAL, fill: { color: C.accent1 }, isTextBox: true, margin: 0 });
    s.addText([{ text: x[0] + ':  ', options: { bold: true, color: HX.DK } }, { text: x[1] }], { x: 1.3, y, w: 5.3, h: 0.85, fontSize: 13, valign: 'middle', isTextBox: true, margin: 0 });
  });
  card(s, 7.1, 1.35, 5.7, 1.55, 'SPA (S9)', 'Successive projections on SNV bands; chain length and start chosen by inner-CV MLR error (Zhu et al. 2017; Araujo et al. 2001).', HX.B);
  card(s, 7.1, 3.05, 5.7, 1.55, 'GA-PLS (S10)', 'Genetic algorithm, 30 chromosomes x 25 generations, PLS-DA fitness with size penalty (Mandal et al. 2023; Leardi 1998).', HX.D);
  card(s, 7.1, 4.75, 5.7, 1.75, 'In-fold NDSI (S4)', 'All 20,100 band pairs scored by mean |d| across dates, sign-consistent; top 3 disjoint pairs (Mandal et al. 2023).', HX.R);
  source(s, 'Tian et al. 2021; Lv et al. 2023; Robnik-Sikonja & Kononenko 2003; Pudil et al. 1994');
}
{
  const s = content('Optimal feature combinations (OFCs) after Tian et al. (2021)');
  const st = [['All features', 'F1-F6 + in-fold NDSI (~2,100)', HX.G], ['DSF screening', 'ReliefF top 5% on >= 3 of 4 dates', HX.B], ['Redundancy + VIF', '|r| < 0.98, VIF < 10', HX.B],
    ['DSF pool', 'disease-specific features (~10)', HX.H]];
  st.forEach((x, i) => {
    const xx = 0.5 + i * 3.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: xx, y: 1.35, w: 2.8, h: 1.3, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 } });
    s.addText([{ text: x[0], options: { bold: true, color: HX.DK, breakLine: true, fontSize: 15 } }, { text: x[1], options: { fontSize: 12 } }], { x: xx + 0.15, y: 1.4, w: 2.5, h: 1.2, valign: 'middle', isTextBox: true, margin: 0 });
    if (i < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: xx + 2.83, y: 1.85, w: 0.24, h: 0.3, fill: { color: 'BDBDBD' }, line: { color: 'BDBDBD' } });
  });
  ['LDA', 'kNN', 'SVM'].forEach((w, i) => {
    const y = 3.0 + i * 1.12;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 3.6, h: 0.9, rectRadius: 0.08, fill: { color: [HX.B, HX.H, HX.D][i] }, line: { color: [HX.B, HX.H, HX.D][i] } });
    s.addText('SFFS wrapped around ' + w, { x: 0.6, y, w: 3.4, h: 0.9, fontSize: 15, bold: true, color: C.background1, valign: 'middle', isTextBox: true, margin: 0 });
    s.addShape(pres.shapes.RIGHT_ARROW, { x: 4.2, y: y + 0.3, w: 0.4, h: 0.3, fill: { color: 'BDBDBD' }, line: { color: 'BDBDBD' } });
    s.addText('OFC-' + w, { x: 4.7, y, w: 1.8, h: 0.9, fontSize: 16, bold: true, color: C.text2, valign: 'middle', isTextBox: true, margin: 0 });
  });
  card(s, 6.8, 3.0, 6.0, 3.25, 'Comparison design (E7)', 'Each OFC, the whole DSF pool and the full SNV spectrum is classified with LDA, kNN and SVM (tuned in inner CV), inside the same 25 x 4-fold nested plot-grouped CV. The diagonal (OFC-LDA + LDA, OFC-kNN + kNN, OFC-SVM + SVM) reproduces the Tian et al. (2021) design; the off-diagonal tests whether an OFC transfers to other classifiers.', HX.H);
  source(s, 'Tian et al. 2021; Pudil et al. 1994; Robnik-Sikonja & Kononenko 2003');
}
{
  const s = content('Classifiers, tuning and class imbalance');
  const rows = [
    ['LDA', 'Shrinkage / none', 'Equal priors', 'Zhang 2012; Tian 2021'], ['PLS-DA', 'Components 1-16', 'Oversampling', 'Zhu 2017'],
    ['Logistic regression', 'C = 0.01-100', 'Class weights', 'Baseline'], ['kNN', 'k = 5, 15, 35', 'Oversampling', 'Tian 2021'],
    ['SVM (RBF)', 'C x gamma grid', 'Class weights', 'Cortes & Vapnik 1995'], ['LS-SVM', 'gamma x regularisation', 'Weighted', 'Suykens 1999; Zhu 2017'],
    ['Random forest', 'Leaf size', 'Balanced subsample', 'Breiman 2001'], ['XGBoost', 'Depth x learning rate', 'scale_pos_weight', 'Chen & Guestrin 2016'],
    ['ELM', 'Hidden units x ridge', 'Weighted', 'Huang 2006; Zhu 2017'], ['MLP', 'Layers x alpha', 'Oversampling', 'Nguyen 2023'],
  ];
  table(s, ['Classifier', 'Tuned (inner CV)', 'Imbalance', 'Reference'], rows, { x: 0.5, y: 1.25, w: 8.2, colW: [2.0, 2.3, 1.8, 2.1], fontSize: 12, rowH: 0.47 });
  card(s, 9.0, 1.3, 3.8, 2.5, 'Deep learning', '1D/3D-CNN not used: only 48 independent plots, so a CNN would overfit (Nguyen et al. 2023 needed hundreds of plots).', HX.G);
  card(s, 9.0, 3.95, 3.8, 2.6, 'Ten feature scenarios', 'S1 full spectrum; S2-S7 single families with robust selection; S8 combined; S9 SPA; S10 GA-PLS.', HX.H);
}
{
  const s = content('Validation design: nested, plot-grouped, stratified, repeated CV');
  for (let k = 0; k < 4; k++) {
    for (let j = 0; j < 4; j++) {
      const x = 0.7 + j * 1.45, y = 1.55 + k * 0.62;
      const test = j === k;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 1.35, h: 0.5, rectRadius: 0.05, fill: { color: test ? C.accent2 : C.background2 }, line: { color: test ? C.accent2 : C.background2 } });
      s.addText(test ? 'Test' : 'Train', { x, y, w: 1.35, h: 0.5, fontSize: 12, bold: test, color: test ? C.background1 : C.text2, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    }
    s.addText('Fold ' + (k + 1), { x: 6.55, y: 1.55 + k * 0.62, w: 1, h: 0.5, fontSize: 12, color: C.accent6, valign: 'middle', isTextBox: true, margin: 0 });
  }
  bullets(s, [
    'Outer: 4 folds of whole plots; each test fold = 1 healthy + 3 diseased plots per variety',
    'Inner: 3-fold plot-grouped CV for selection and tuning',
    '25 repeats -> 100 outer test folds (cf. 4-fold x 100 in Tian 2021; Lv 2023)',
    'Plot-date predictions by majority vote of spectra',
  ], { x: 0.5, y: 4.15, w: 7.2, h: 2.4, fontSize: 14 });
  card(s, 8.0, 1.3, 4.8, 2.35, 'Transfer tests (E2)', 'Leave-one-date-out and leave-one-stage-out with plots kept apart; leave-one-variety-out (train 2 varieties, test the third).', HX.B);
  card(s, 8.0, 3.8, 4.8, 2.75, 'Metrics', 'OA, balanced accuracy (BA), sensitivity, specificity, macro-F1, Cohen κ, MCC, ROC-AUC, PR-AUC; Friedman-Nemenyi and corrected resampled t-tests.', HX.H);
  source(s, 'Roberts et al. 2017; Varma & Simon 2006; Demsar 2006; Nadeau & Bengio 2003; Chicco & Jurman 2020');
}

// ================================================================== RESULTS
newSection('5. Results', 'From spectral response to validated prediction models');
{
  const s = content('R1. Quality control: noise, splice steps and outliers');
  const nz = D.qc_noise;
  s.addChart(pres.charts.BAR, [{ name: 'SNR', labels: nz.map((r) => r.Region_nm), values: nz.map((r) => Math.round(r.SNR)) }],
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 7.0, h: 4.6, barDir: 'col', chartColors: [HX.H], title: 'Signal-to-noise ratio by region (raw spectra)', showLegend: false,
      showValue: true, dataLabelPosition: 'outEnd', catAxisLabelFontSize: 9, showValAxisTitle: true, valAxisTitle: 'Mean reflectance / noise SD' }));
  stat(s, 8.0, 1.35, 4.8, (D.qc.splice_1000_before * 1000).toFixed(1) + ' x10⁻³', 'mean step at 1000 nm before correction (0 after)', HX.B);
  stat(s, 8.0, 2.85, 4.8, String(D.qc.n_removed), `outliers removed (>= 3 of 4 rules); ${D.n_clean} spectra kept`, HX.D);
  bullets(s, [`350-400 nm has the lowest SNR; trimmed to 400-2400 nm`, `All ${D.qc.n_removed} removed spectra came from diseased plots`, 'Sensitivity of results to removal tested in E6'],
    { x: 8.0, y: 4.45, w: 4.8, h: 2.0, fontSize: 14 });
  source(s, 'Workbook sheet 02_QC');
}
{
  const s = content('R2. Spectral response of mustard leaves to white rust');
  spectraChart(s, [['Healthy', D.spec.Healthy_mean], ['Diseased', D.spec.Diseased_mean]], [HX.H, HX.D],
    { title: 'Mean reflectance (n = ' + D.n_h_clean + ' healthy, ' + D.n_d_clean + ' diseased)', valAxisTitle: 'Reflectance', x: 0.5, w: 6.2 });
  spectraChart(s, [['Diseased - Healthy', D.spec['Difference_D-H']]], [HX.R],
    { title: 'Difference spectrum (D - H)', valAxisTitle: 'Reflectance difference', x: 6.8, w: 6.0, h: 3.0, showLegend: false });
  s.addText(NARR.spectral_response, { x: 6.9, y: 4.35, w: 5.9, h: 2.3, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Workbook sheet 03_Spectra_Class; Fig01');
}
{
  const s = content('R3. The disease signal changes with date and growth stage');
  const sd = D.spec_date;
  const names = ['11 Feb', '24 Feb', '03 Mar', '13 Mar'];
  spectraChart(s, names.map((n) => [n, sd[n + '_Diff']]), DATEC, { title: 'Difference spectra (D - H) by date', valAxisTitle: 'Reflectance difference', w: 7.4, h: 5.2 });
  const sim = D.similarity.map((r) => [r.Date, f3(r.Cosine_similarity * 1), f2(r.Spectral_angle_deg), f3(r.Euclidean_distance)]);
  table(s, ['Date', 'Cosine', 'SAM (°)', 'Euclid.'], sim, { x: 8.2, y: 1.35, w: 4.6, colW: [1.2, 1.1, 1.1, 1.2], fontSize: 12, rowH: 0.4 });
  s.addText(NARR.by_date, { x: 8.2, y: 3.6, w: 4.6, h: 3.0, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Workbook sheets 04_Spectra_Date and 08; class-mean similarity after Selvaprakash et al. 2026');
}
{
  const s = content('R4. Sensitive regions: effect size, correlation and separability');
  const b = D.bands; const wl = b.Wavelength_nm.map(String);
  s.addChart(pres.charts.LINE, [{ name: "Cohen's d (D - H)", labels: wl, values: b.Cohen_d }],
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 6.2, h: 2.65, chartColors: ['333333'], lineSize: 2, lineDataSymbol: 'none', catAxisLabelFrequency: 20, title: "Effect size per band (plot-date means, n = 192)", showLegend: false }));
  s.addChart(pres.charts.LINE, [{ name: 'Reflectance', labels: wl, values: b.JM_distance }, { name: 'First derivative', labels: wl, values: b.FD_JM }],
    Object.assign(AX(), { x: 0.5, y: 3.95, w: 6.2, h: 2.7, chartColors: [HX.H, HX.D], lineSize: 2, lineDataSymbol: 'none', catAxisLabelFrequency: 20, title: 'Jeffries-Matusita distance per band' }));
  const rows = D.regions.map((r) => [r.Region_nm, r.Direction, f2(r.Max_abs_Cohen_d), r.Peak_wavelength_nm]);
  table(s, ['Region (nm)', 'Direction', 'max |d|', 'Peak (nm)'], rows, { x: 7.0, y: 1.3, w: 5.8, colW: [1.4, 2.2, 1.0, 1.2], fontSize: 12, rowH: 0.42 });
  s.addText(NARR.regions, { x: 7.0, y: 3.4, w: 5.8, h: 3.2, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Welch t-test with Benjamini-Hochberg FDR; workbook sheets 07-08; Mandal et al. 2022; Richards & Jia 2006');
}
{
  const s = content('R5. Red-edge and derivative parameters');
  const sd = D.spec;
  const wl = sd.Wavelength_nm.map(String).slice(0, 101);
  s.addChart(pres.charts.LINE, [{ name: 'Healthy', labels: wl, values: sd.FD_Healthy.slice(0, 101) }, { name: 'Diseased', labels: wl, values: sd.FD_Diseased.slice(0, 101) }],
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 6.0, h: 5.3, chartColors: [HX.H, HX.D], lineSize: 2, lineDataSymbol: 'none', catAxisLabelFrequency: 10, title: 'First-derivative spectra (400-1400 nm)', showCatAxisTitle: true, catAxisTitle: 'Wavelength (nm)', valAxisLabelFormatCode: '0.000' }));
  const pick = ['REP_LI', 'REP_FD', 'REV', 'SDr', 'lambda_b', 'lambda_y', 'Dy'];
  const rows = D.rededge.filter((r) => r.Date === 'All' && pick.includes(r.Parameter)).map((r) => [r.Parameter, `${(+r.Healthy_mean).toPrecision(5)} ± ${(+r.Healthy_SD).toPrecision(2)}`, `${(+r.Diseased_mean).toPrecision(5)} ± ${(+r.Diseased_SD).toPrecision(2)}`, pfmt(r.Welch_p)]);
  table(s, ['Parameter', 'Healthy', 'Diseased', 'p'], rows, { x: 6.8, y: 1.3, w: 6.0, colW: [1.4, 1.9, 1.9, 0.8], fontSize: 12, rowH: 0.4 });
  s.addText(NARR.rededge, { x: 6.8, y: 4.75, w: 6.0, h: 1.9, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'REP: Guyot & Baret 1988; REV/SDr: Mandal et al. 2022; edges: Zhang et al. 2012; workbook sheet 09');
}
{
  const s = content('R6. PCA and t-SNE: date dominates, disease is a subtle signal');
  const P = D.pca_pd;
  const xs = P.map((r) => r.PC1);
  const ser = (cond) => P.map((r) => (cond(r) ? r.PC2 : null));
  const v = D.pca_var;
  s.addChart(pres.charts.SCATTER, [{ name: 'PC1', values: xs }, { name: 'Healthy', values: ser((r) => r.label === 'Healthy') }, { name: 'Diseased', values: ser((r) => r.label === 'Diseased') }],
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 4.1, h: 4.2, chartColors: [HX.H, HX.D], lineSize: 0, lineDataSymbolSize: 6, title: 'PCA by class (plot-date means)',
      showCatAxisTitle: true, catAxisTitle: `PC1 (${f1(v[0].Explained_variance_pct)}%)`, showValAxisTitle: true, valAxisTitle: `PC2 (${f1(v[1].Explained_variance_pct)}%)` }));
  const dates = ['2026-02-11', '2026-02-24', '2026-03-03', '2026-03-13'], dl = ['11 Feb', '24 Feb', '03 Mar', '13 Mar'];
  s.addChart(pres.charts.SCATTER, [{ name: 'PC1', values: xs }].concat(dates.map((d, i) => ({ name: dl[i], values: ser((r) => r.date === d) }))),
    Object.assign(AX(), { x: 4.7, y: 1.25, w: 4.1, h: 4.2, chartColors: DATEC, lineSize: 0, lineDataSymbolSize: 6, title: 'PCA by date (plot-date means)',
      showCatAxisTitle: true, catAxisTitle: `PC1 (${f1(v[0].Explained_variance_pct)}%)` }));
  const eta = D.pca_eta.slice(0, 4).map((r) => [r.PC, f2(r.label), f2(r.date), f2(r.stage), f2(r.variety), f2(r.plot)]);
  table(s, ['PC', 'Class', 'Date', 'Stage', 'Var.', 'Plot'], eta, { x: 9.0, y: 1.3, w: 3.8, colW: [0.6, 0.65, 0.65, 0.65, 0.6, 0.65], fontSize: 11, rowH: 0.36 });
  s.addText('η² = share of PC-score variance explained by each factor', { x: 9.0, y: 3.2, w: 3.8, h: 0.4, fontSize: 10, italic: true, color: C.accent6, isTextBox: true, margin: 0 });
  s.addText(NARR.pca, { x: 9.0, y: 3.65, w: 3.8, h: 2.9, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  s.addText('t-SNE embedding in workbook sheet 10 and Fig05', { x: 0.5, y: 5.55, w: 8.3, h: 0.35, fontSize: 11, italic: true, color: C.accent6, isTextBox: true, margin: 0 });
  source(s, 'SNV spectra; van der Maaten & Hinton 2008; Selvaprakash et al. 2026');
}
{
  const s = content('R7. PERMANOVA: how much variance is disease?');
  const pm = D.permanova;
  s.addChart(pres.charts.BAR, [{ name: 'Marginal R² (%)', labels: pm.map((r) => r.Term), values: pm.map((r) => +(+r.R2_partial_pct).toFixed(2)) }],
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 6.4, h: 5.2, barDir: 'bar', chartColors: [HX.H], title: 'Variance explained (% of total SS)', showLegend: false, showValue: true, dataLabelPosition: 'outEnd', catAxisOrientation: 'maxMin', dataLabelFormatCode: '0.0' }));
  const rows = pm.map((r) => [r.Term, r.df, r.Pseudo_F === null ? '-' : f2(r.Pseudo_F), f2(r.R2_partial_pct), r.p_perm === null ? '-' : pfmt(r.p_perm)]);
  table(s, ['Term', 'df', 'Pseudo-F', 'R² %', 'p'], rows, { x: 7.2, y: 1.3, w: 5.6, colW: [1.8, 0.6, 1.1, 1.0, 1.1], fontSize: 12, rowH: 0.4 });
  s.addText(NARR.permanova, { x: 7.2, y: 4.7, w: 5.6, h: 1.9, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Anderson 2001; plot-date mean SNV spectra; disease/variety permuted across plots, date/stage within plots');
}
{
  const s = content('R8. Published vegetation indices are weak and date-dependent');
  const v = D.vi.slice(0, 15).reverse();
  s.addChart(pres.charts.BAR, [{ name: 'AUC', labels: v.map((r) => r.Index), values: v.map((r) => +(+r.AUC).toFixed(3)) }],
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 5.4, h: 5.35, barDir: 'bar', chartColors: [HX.H], title: 'Top-15 indices by AUC', showLegend: false, showValue: true, dataLabelPosition: 'outEnd', valAxisMinVal: 0.5, valAxisMaxVal: 0.75, catAxisLabelFontSize: 10, dataLabelFormatCode: '0.000' }));
  const t = D.vi.slice(0, 8).map((r) => [r.Index, r.Trait, f3(r.AUC), f2(r['d_11 Feb']), f2(r['d_24 Feb']), f2(r['d_03 Mar']), f2(r['d_13 Mar'])]);
  table(s, ['Index', 'Trait', 'AUC', 'd 11F', 'd 24F', 'd 03M', 'd 13M'], t, { x: 6.2, y: 1.3, w: 6.6, colW: [1.0, 2.2, 0.7, 0.68, 0.68, 0.68, 0.66], fontSize: 10.5, rowH: 0.38 });
  s.addText(NARR.vi, { x: 6.2, y: 4.95, w: 6.6, h: 1.7, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Index sources in workbook sheet 13; ranking approach after Mandal et al. 2023');
}
{
  const s = content('R9. A new Mustard White Rust Index (MWRI) from band-pair search');
  s.addImage({ path: FIG('Fig08_NDSI_map.png'), x: 0.5, y: 1.2, w: 5.7, h: 4.78 });
  const rows = D.ndsi_top.slice(0, 7).map((r) => [r.Formula, f2(r.Mean_abs_d_across_dates), f2(r.Min_abs_d_across_dates), f3(r.AUC)]);
  table(s, ['Index', 'mean |d|', 'min |d|', 'AUC'], rows, { x: 6.5, y: 1.3, w: 6.3, colW: [3.3, 1.0, 1.0, 1.0], fontSize: 11.5, rowH: 0.38 });
  s.addText(NARR.mwri, { x: 6.5, y: 4.55, w: 6.3, h: 2.1, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Exhaustive NDSI search after Mandal et al. 2023 and Selvaprakash et al. 2026; score = mean |Cohen d| across dates, sign-consistent');
}
{
  const s = content('R10. Wavelet (CWT) features capture shape changes');
  s.addImage({ path: FIG('Fig09_CWT_scalogram.png'), x: 0.5, y: 1.2, w: 8.2, h: 2.92 });
  const rows = D.cwt_top.slice(0, 8).map((r) => [String(r.wl) + ' nm', r.scale.replace('Scale_', 'scale '), f2(r.d)]);
  table(s, ['Wavelength', 'Scale', '|d|'], rows, { x: 9.0, y: 1.3, w: 3.8, colW: [1.4, 1.3, 1.1], fontSize: 12, rowH: 0.36 });
  s.addText(NARR.cwt, { x: 0.5, y: 4.35, w: 8.2, h: 2.25, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Mexican-hat CWT, Torrence & Compo 1998; Cheng et al. 2011; Tian et al. 2021; Lv et al. 2023; workbook sheet 15');
}
if (D.E1) {
  const s = content('R11. Preprocessing comparison (E1)');
  const vs = ['Reflectance (SG)', 'SNV', 'MSC', 'First derivative (SG)', 'Date normalisation', 'Date normalisation + SNV'];
  const cl = ['LDA', 'PLS-DA', 'LR', 'SVM'];
  const get = (v, c) => (D.E1.find((r) => r.variant === v && r.clf === c) || {}).BA;
  s.addChart(pres.charts.BAR, cl.map((c) => ({ name: c, labels: ['Reflectance', 'SNV', 'MSC', '1st deriv.', 'Date norm.', 'Date norm.+SNV'], values: vs.map((v) => +(+get(v, c)).toFixed(3)) })),
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 7.6, h: 5.3, barDir: 'col', chartColors: [HX.B, HX.H, HX.D, HX.R], title: 'Balanced accuracy, full spectrum (10 x 4-fold plot-grouped CV)', valAxisMinVal: 0.5, valAxisMaxVal: 1.0, valAxisLabelFormatCode: '0.00' }));
  s.addText(NARR.e1, { x: 8.4, y: 1.35, w: 4.4, h: 5.2, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Barnes et al. 1989; Geladi et al. 1985; Lv et al. 2023; workbook sheet 17');
}
if (D.summary) {
  const s = content('R12. Model comparison: 10 feature scenarios x 10 classifiers');
  const sc = Object.keys(SCN);
  const rows = sc.map((k) => [{ text: k + ' ' + SCN[k], options: { align: 'left', fontSize: 10 } }].concat(CLFS.map((c) => heatCell((SUMK[k + '|' + c] || {}).BA_mean, 0.55, 0.95, f3))));
  table(s, ['Scenario'].concat(CLFS), rows, { x: 0.5, y: 1.2, w: 12.3, colW: [3.5].concat(CLFS.map(() => 0.88)), fontSize: 10.5, rowH: 0.43 });
  s.addText(NARR.matrix, { x: 0.5, y: 6.0, w: 12.3, h: 0.65, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Mean balanced accuracy over 25 repeats of nested plot-grouped 4-fold CV; workbook sheets 18-20');
}
if (D.summary) {
  const s = content('R13. Best pipeline per feature scenario and Friedman ranking');
  const bp = D.best_per_scenario;
  s.addChart(pres.charts.BAR, [{ name: 'Balanced accuracy', labels: bp.map((r) => r.scenario + ' ' + r.clf), values: bp.map((r) => +(+r.BA_mean).toFixed(3)) }],
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 7.4, h: 5.35, barDir: 'col', chartColors: [HX.H], title: 'Best classifier per scenario (mean of 25 repeats)', showLegend: false, showValue: true, dataLabelPosition: 'outEnd', valAxisMinVal: 0.5, valAxisMaxVal: 1.0, valAxisLabelFormatCode: '0.00', catAxisLabelFontSize: 9, dataLabelFormatCode: '0.000' }));
  const fr = D.friedman_c.map((r) => [r.clf, f2(r.Average_rank), f3(r.Mean_BA)]);
  table(s, ['Classifier', 'Mean rank', 'Mean BA'], fr, { x: 8.2, y: 1.3, w: 4.6, colW: [1.8, 1.4, 1.4], fontSize: 11, rowH: 0.33 });
  const fc = D.friedman[0];
  s.addText(`Friedman χ² = ${f1(fc.chi2)}, p ${fc.p < 0.001 ? '< 0.001' : '= ' + f3(fc.p)}; Nemenyi CD = ${f2(fc.CD_Nemenyi_0_05)} ranks`, { x: 8.2, y: 5.0, w: 4.6, h: 0.5, fontSize: 12, bold: true, color: C.text2, isTextBox: true, margin: 0 });
  s.addText(NARR.friedman, { x: 8.2, y: 5.5, w: 4.6, h: 1.15, fontSize: 12, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Demsar 2006; workbook sheet 21');
}
if (D.summary) {
  const s = content('R14. Best models in detail: confusion matrices and metrics');
  const cms = D.cm;
  cms.forEach((r, i) => {
    const x = 0.5 + (i % 2) * 3.15, y = 1.3 + Math.floor(i / 2) * 2.7;
    s.addText(`${r.Role} - ${r.Level}`, { x, y, w: 3.0, h: 0.5, fontSize: 11, bold: true, color: C.text2, isTextBox: true, margin: 0 });
    const tot = r.TN + r.FP + r.FN + r.TP;
    table(s, ['', 'Pred H', 'Pred D'], [[{ text: 'True H', options: { bold: true } }, heatCell(r.TN / (r.TN + r.FP), 0, 1, () => String(Math.round(r.TN))), heatCell(r.FP / (r.TN + r.FP), 0, 1, () => String(Math.round(r.FP)))],
      [{ text: 'True D', options: { bold: true } }, heatCell(r.FN / (r.FN + r.TP), 0, 1, () => String(Math.round(r.FN))), heatCell(r.TP / (r.FN + r.TP), 0, 1, () => String(Math.round(r.TP)))]],
    { x, y: y + 0.5, w: 3.0, colW: [0.9, 1.05, 1.05], fontSize: 12, rowH: 0.5 });
  });
  const mrow = (lab, S) => [lab, f3(S.BA_mean) + ' ± ' + f3(S.BA_SD), f3(S.Sensitivity_mean), f3(S.Specificity_mean), f3(S.MacroF1_mean), f3(S.Kappa_mean), f3(S.MCC_mean), f3(S.ROC_AUC_mean)];
  table(s, ['Pipeline', 'BA', 'Sens.', 'Spec.', 'Macro-F1', 'κ', 'MCC', 'AUC'], [mrow('Best: ' + BEST.scenario + ' ' + BEST.clf, BS), mrow('Compact: ' + COMPACT.scenario + ' ' + COMPACT.clf, CS)],
    { x: 6.9, y: 1.3, w: 5.9, colW: [1.55, 1.05, 0.55, 0.55, 0.65, 0.5, 0.5, 0.55], fontSize: 10, rowH: 0.45 });
  const roc = D.roc; const keys = Object.keys(roc[0]).filter((k) => k.startsWith('TPR'));
  s.addChart(pres.charts.SCATTER, [{ name: 'FPR', values: roc.map((r) => r.FPR) }].concat(keys.map((k) => ({ name: k.replace('TPR_', ''), values: roc.map((r) => r[k]) }))),
    Object.assign(AX(), { x: 6.9, y: 2.85, w: 5.9, h: 3.75, chartColors: [HX.H, HX.D], lineSize: 2, lineDataSymbol: 'none', title: 'ROC curves (representative repeat)', valAxisMaxVal: 1, catAxisMaxVal: 1 }));
  source(s, 'Representative repeat (median BA); metrics mean ± SD over 25 repeats; workbook sheets 20-23');
}
if (D.summary) {
  const s = content('R15. Which features were selected, and why they matter');
  const s8 = D.selfreq.filter((r) => r.scenario === 'S8').slice(0, 8).reverse();
  s.addChart(pres.charts.BAR, [{ name: '% of folds', labels: s8.map((r) => r.Feature), values: s8.map((r) => +(+r.Frequency_pct).toFixed(0)) }],
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 5.0, h: 5.35, barDir: 'bar', chartColors: [HX.B], title: 'S8: selection frequency over 100 folds (%)', showLegend: false, showValue: true, dataLabelPosition: 'outEnd', catAxisLabelFontSize: 10, dataLabelFormatCode: '0' }));
  const rows = D.final.map((r) => [r.Feature, f2(r.Cohen_d), f3(r.AUC), f3(r.Permutation_importance_BA), f3(r.Mean_abs_SHAP)]);
  table(s, ['Final feature', 'd', 'AUC', 'Perm. imp.', '|SHAP|'], rows, { x: 5.8, y: 1.3, w: 7.0, colW: [2.4, 1.0, 1.0, 1.3, 1.3], fontSize: 11, rowH: 0.36 });
  s.addText(NARR.features, { x: 5.8, y: 4.75, w: 7.0, h: 1.9, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Permutation importance: Breiman 2001; TreeSHAP: Lundberg & Lee 2017; workbook sheets 25-26');
}
if (D.E7) {
  const s = content('R15b. OFCs from wrapper-based SFFS (Tian et al., 2021)');
  const sets = ['OFC-LDA', 'OFC-kNN', 'OFC-SVM', 'All DSFs', 'Full spectrum (SNV)'];
  const get = (fs, c) => D.E7.find((r) => r.feature_set === fs && r.clf === c) || {};
  s.addChart(pres.charts.BAR, ['LDA', 'kNN', 'SVM'].map((c) => ({ name: c, labels: sets.map((x) => x.replace(' (SNV)', '')), values: sets.map((fs) => +(+get(fs, c).BA).toFixed(3)) })),
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 7.2, h: 5.35, barDir: 'col', chartColors: [HX.B, HX.H, HX.D], title: 'Balanced accuracy by feature set and classifier (25 x 4-fold CV)', valAxisMinVal: 0.6, valAxisMaxVal: 1.0, valAxisLabelFormatCode: '0.00' }));
  const rows = sets.map((fs) => [fs, f1(get(fs, 'LDA').median_n_features)].concat(['LDA', 'kNN', 'SVM'].map((c) => heatCell(get(fs, c).BA, 0.7, 0.95, f3))));
  table(s, ['Feature set', 'n', 'LDA', 'kNN', 'SVM'], rows, { x: 8.0, y: 1.3, w: 4.8, colW: [1.75, 0.55, 0.83, 0.83, 0.84], fontSize: 11, rowH: 0.4 });
  s.addText(NARR.e7 || '', { x: 8.0, y: 3.95, w: 4.8, h: 2.7, fontSize: 12.5, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Tian et al. 2021; workbook sheet 27b_OFC_Tian2021');
}
if (D.E7) {
  const s = content('R15c. Composition of the final OFCs and accuracy by date');
  const fin = D.E7_final.filter((r) => r.Set !== 'All DSFs');
  const sets = ['OFC-LDA', 'OFC-kNN', 'OFC-SVM'];
  const maxn = Math.max(...sets.map((st) => fin.filter((r) => r.Set === st).length));
  const rows = []; for (let i = 0; i < maxn; i++) rows.push([String(i + 1)].concat(sets.map((st) => { const r = fin.filter((x) => x.Set === st)[i]; return r ? r.Feature : ''; })));
  table(s, ['#'].concat(sets), rows, { x: 0.5, y: 1.3, w: 6.6, colW: [0.4, 2.07, 2.07, 2.06], fontSize: 11.5, rowH: 0.36 });
  const pool = D.E7_final.filter((r) => r.Set === 'All DSFs').map((r) => r.Feature);
  s.addText('DSF pool (all data, ' + pool.length + '): ' + pool.join(', '), { x: 0.5, y: 5.2, w: 6.6, h: 1.4, fontSize: 11, color: C.accent6, valign: 'top', isTextBox: true, margin: 0 });
  const dts = ['11 Feb', '24 Feb', '03 Mar', '13 Mar'];
  const diag = [['OFC-LDA', 'LDA'], ['OFC-kNN', 'kNN'], ['OFC-SVM', 'SVM'], ['Full spectrum (SNV)', 'SVM']];
  s.addChart(pres.charts.LINE, diag.map(([fs, c]) => ({ name: fs.replace(' (SNV)', '') + ' + ' + c, labels: dts, values: dts.map((d) => { const r = D.E7_date.find((x) => x.feature_set === fs && x.clf === c && x.Date === d); return r ? +(+r.BA).toFixed(3) : null; }) })),
    Object.assign(AX(), { x: 7.4, y: 1.25, w: 5.4, h: 5.35, chartColors: [HX.B, HX.H, HX.D, HX.G], lineSize: 2, lineDataSymbol: 'circle', lineDataSymbolSize: 7, title: 'Balanced accuracy within each date', valAxisMinVal: 0.5, valAxisMaxVal: 1.0, valAxisLabelFormatCode: '0.00' }));
  source(s, 'Final OFCs re-selected on all data for interpretation; per-date accuracy from the CV predictions; Tian et al. 2021');
}
if (D.summary) {
  const s = content('R16. Full-spectrum model: where the logistic regression looks');
  const wl = D.lrcoef.Wavelength_nm.map(String);
  s.addChart(pres.charts.LINE, [{ name: 'Standardised coefficient', labels: wl, values: D.lrcoef.LR_std_coefficient }],
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 8.2, h: 5.3, chartColors: ['333333'], lineSize: 2, lineDataSymbol: 'none', catAxisLabelFrequency: 20, title: 'Logistic regression coefficients on SNV spectra (positive = diseased)', showLegend: false, showCatAxisTitle: true, catAxisTitle: 'Wavelength (nm)' }));
  s.addText(NARR.lr, { x: 9.0, y: 1.35, w: 3.8, h: 5.2, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Workbook sheet 26 (coefficients fitted on all data, C = 0.1)');
}
if (D.subgroups) {
  const s = content('R17. Performance within each date, variety and growth stage');
  const sg = D.subgroups; const roles = [...new Set(sg.map((r) => r.Role))];
  const levels = sg.filter((r) => r.Role === roles[0]).map((r) => r.Level);
  s.addChart(pres.charts.BAR, roles.map((ro) => ({ name: ro, labels: levels, values: sg.filter((r) => r.Role === ro).map((r) => +(+r.BA).toFixed(3)) })),
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 8.4, h: 5.35, barDir: 'col', chartColors: [HX.H, HX.D], title: 'Balanced accuracy by sub-group (pooled model, 25 repeats)', valAxisMinVal: 0.5, valAxisMaxVal: 1.0, valAxisLabelFormatCode: '0.00' }));
  s.addText(NARR.subgroups, { x: 9.2, y: 1.35, w: 3.6, h: 5.2, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Workbook sheet 27');
}
if (D.E2) {
  const s = content('R18. Transfer to an unseen date, variety or stage (E2)');
  const e = D.E2; const pipes = [...new Set(e.map((r) => r.scenario + ' ' + r.clf))];
  const order = [['Date', '2026-02-11', '11 Feb'], ['Date', '2026-02-24', '24 Feb'], ['Date', '2026-03-03', '03 Mar'], ['Date', '2026-03-13', '13 Mar'],
    ['Variety', 'V1', 'V1'], ['Variety', 'V2', 'V2'], ['Variety', 'V3', 'V3'], ['Stage', 'Vegetative', 'Veg.'], ['Stage', 'Flowering', 'Flow.'], ['Stage', 'Pod formation', 'Pod']];
  s.addChart(pres.charts.BAR, pipes.map((p) => ({ name: p, labels: order.map((o) => o[2]), values: order.map((o) => { const r = e.find((x) => x.kind === o[0] && x.level === o[1] && x.scenario + ' ' + x.clf === p); return r ? +(+r.BA).toFixed(3) : null; }) })),
    Object.assign(AX(), { x: 0.5, y: 1.25, w: 8.6, h: 5.35, barDir: 'col', chartColors: [HX.B, HX.H, HX.D], title: 'Held-out level: balanced accuracy (dates | varieties | stages)', valAxisMinVal: 0.4, valAxisMaxVal: 1.0, valAxisLabelFormatCode: '0.00' }));
  s.addText(NARR.transfer, { x: 9.4, y: 1.35, w: 3.4, h: 5.2, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Roberts et al. 2017; Terentev et al. 2023; Lv et al. 2023; workbook sheet 28');
}
if (D.E3 || D.E4 || D.E5) {
  const s = content('R19. Metadata, training-set size, multispectral sensors and outliers');
  if (D.E4) {
    const e = D.E4; const pipes = [...new Set(e.map((r) => r.scenario + ' ' + r.clf))]; const ns = [...new Set(e.map((r) => r.n_train_plots))];
    s.addChart(pres.charts.LINE, pipes.map((p) => ({ name: p, labels: ns.map(String), values: ns.map((n) => +(+e.find((r) => r.scenario + ' ' + r.clf === p && r.n_train_plots === n).BA).toFixed(3)) })),
      Object.assign(AX(), { x: 0.5, y: 1.25, w: 4.1, h: 3.4, chartColors: [HX.H, HX.D], lineSize: 2, lineDataSymbol: 'circle', lineDataSymbolSize: 7, title: 'E4: learning curve', showCatAxisTitle: true, catAxisTitle: 'Training plots', valAxisMinVal: 0.6, valAxisMaxVal: 1.0, valAxisLabelFormatCode: '0.00' }));
  }
  if (D.E5) {
    const e = D.E5; const sens = [...new Set(e.map((r) => r.sensor))];
    s.addChart(pres.charts.BAR, ['LR', 'SVM', 'RF'].map((c) => ({ name: c, labels: sens.map((x) => x.split(' (')[0]), values: sens.map((x) => +(+e.find((r) => r.sensor === x && r.clf === c).BA).toFixed(3)) })),
      Object.assign(AX(), { x: 4.7, y: 1.25, w: 4.1, h: 3.4, barDir: 'col', chartColors: [HX.B, HX.H, HX.D], title: 'E5: simulated sensors', valAxisMinVal: 0.4, valAxisMaxVal: 1.0, valAxisLabelFormatCode: '0.00' }));
  }
  const rows = [];
  if (D.E3) D.E3.forEach((r) => rows.push(['E3 ' + r.scenario + ' ' + r.clf, r.inputs, f3(r.BA), f3(r.MCC)]));
  if (D.E6) D.E6.forEach((r) => rows.push(['E6 ' + r.scenario + ' ' + r.clf, 'No outlier removal', f3(r.BA), f3(r.MCC)]));
  table(s, ['Experiment', 'Inputs / data', 'BA', 'MCC'], rows, { x: 9.0, y: 1.3, w: 3.8, colW: [1.25, 1.45, 0.55, 0.55], fontSize: 9.5, rowH: 0.3 });
  s.addText(NARR.extras, { x: 0.5, y: 4.85, w: 8.3, h: 1.8, fontSize: 13, color: C.text1, valign: 'top', isTextBox: true, margin: 0 });
  source(s, 'Workbook sheets 29-32; sensor bands: Sentinel-2 MSI and DJI-type UAV 5-band (Nguyen et al. 2023)');
}

// ================================================================== DISCUSSION
newSection('6. Discussion and conclusions', 'Interpreting the results against the literature');
(NARR.discussion || []).forEach((d) => {
  const s = content(d.title);
  bullets(s, d.points, { x: 0.5, y: 1.3, w: d.table ? 6.3 : 12.3, h: 5.3, fontSize: 15 });
  if (d.table) table(s, d.table[0], d.table.slice(1), { x: 7.0, y: 1.3, w: 5.8, fontSize: 11.5, rowH: 0.42, colW: d.colW });
  if (d.source) source(s, d.source);
});
{
  const s = content('Conclusions');
  (NARR.conclusions || []).forEach((c, i) => {
    const y = 1.25 + i * 0.77;
    s.addShape(pres.shapes.OVAL, { x: 0.5, y: y + 0.1, w: 0.46, h: 0.46, fill: { color: C.accent1 }, line: { color: C.accent1 } });
    s.addText(String(i + 1), { x: 0.5, y: y + 0.1, w: 0.46, h: 0.46, fontSize: 14, bold: true, color: C.background1, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    s.addText(c, { x: 1.15, y, w: 11.65, h: 0.68, fontSize: 14.5, color: C.text1, valign: 'middle', isTextBox: true, margin: 0 });
  });
}
{
  const s = content('Limitations and future work');
  card(s, 0.5, 1.3, 6.0, 5.25, 'Limitations', (NARR.limitations || []).join('\n\n'), HX.R);
  card(s, 6.8, 1.3, 6.0, 5.25, 'Future work', (NARR.future || []).join('\n\n'), HX.H);
}

// ================================================================== REFERENCES
pres.addSection({ title: 'References' }); section = 'References';
const refs = D.refs;
const groups = [['Papers reviewed (provided by the researcher)', refs.filter((r) => r.ID.startsWith('P'))],
  ['Methods', refs.filter((r) => r.ID.startsWith('M'))], ['Vegetation index sources', refs.filter((r) => r.ID.startsWith('I'))]];
groups.forEach(([gname, list]) => {
  const per = 17;
  for (let i = 0; i < list.length; i += per) {
    const s = content('References: ' + gname.split(' (')[0].toLowerCase() + (i ? ' (cont.)' : ''));
    const chunk = list.slice(i, i + per);
    s.addText(chunk.map((r, k) => ({ text: r.Reference.replace('[P] ', ''), options: { breakLine: k < chunk.length - 1, paraSpaceAfter: 4 } })),
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
