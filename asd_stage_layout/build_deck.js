// Stage-wise plot arrangement deck for the white rust ASD dataset (IARI 2025-26).
// Usage: NODE_PATH=<dir with pptxgenjs> node build_deck.js deck_data.json out.pptx <pptx-skill>/scripts/apply_theme.js
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const [, , dataPath, outPath, themeScript] = process.argv;
const D = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const { applyTheme } = require(themeScript);

const THEME = {
  name: "Mustard Field",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F2A24", lt1: "FFFFFF", dk2: "1F4D2B", lt2: "EEF2EC",
    accent1: "3A7D44", accent2: "C99A06", accent3: "9C4A2B",
    accent4: "2E6DA4", accent5: "7A4BA0", accent6: "1E9E8A",
    hlink: "2E6DA4", folHlink: "7A4BA0",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Stage-wise plot arrangement for white rust severity models";
const C = pres.SchemeColor;

// ---------------------------------------------------------------- data helpers
const DATES = ["110226", "240226", "030326", "130326"];
const DLAB = { "110226": "11/02", "240226": "24/02", "030326": "03/03", "130326": "13/03" };
const DAI = { "110226": 6, "240226": 19, "030326": 26, "130326": 36 };
const STAGES = ["Vegetative", "Flowering", "Pod formation"];
const SCOL = { Vegetative: C.accent1, Flowering: C.accent2, "Pod formation": C.accent3 };
const SHEX = { Vegetative: HEX.accent1, Flowering: HEX.accent2, "Pod formation": HEX.accent3 };
const STXT = { Vegetative: C.background1, Flowering: C.text1, "Pod formation": C.background1 };
const DHEX = { "110226": HEX.accent4, "240226": HEX.accent2, "030326": HEX.accent5, "130326": HEX.accent6 };
const TREATS = ["D1V1", "D1V2", "D1V3", "D2V1", "D2V2", "D2V3", "D3V1", "D3V2", "D3V3", "D4V1", "D4V2", "D4V3"];
const plot = (d, p) => D.plots[d][String(p)];
const plotsOf = (d) => Object.keys(D.plots[d]).map((p) => ({ p: +p, ...D.plots[d][p] }));

function tally(filter) {
  const o = { plotsH: 0, plotsD: 0, specH: 0, specD: 0 };
  DATES.forEach((d) => plotsOf(d).filter((x) => filter(d, x)).forEach((x) => {
    if (x.hd === "Healthy") { o.plotsH++; o.specH += x.n; } else { o.plotsD++; o.specD += x.n; }
  }));
  return o;
}
const TOTAL = tally(() => true);
const fmt = (n) => Number(n).toLocaleString("en-US");

// Field grid as seen in the field map: 4 rows x 12 columns, blocks R1 | R2 | R3 | Healthy
const GRID = [
  [48, 41, 40, 33, 32, 25, 24, 17, 16, 9, 8, 1],
  [47, 42, 39, 34, 31, 26, 23, 18, 15, 10, 7, 2],
  [46, 43, 38, 35, 30, 27, 22, 19, 14, 11, 6, 3],
  [45, 44, 37, 36, 29, 28, 21, 20, 13, 12, 5, 4],
];
const BLOCKS = ["R1", "R2", "R3", "Healthy control"];

// ---------------------------------------------------------------- layouts
const FOOT = "White rust ASD leaf spectra | ICAR-IARI New Delhi, rabi 2025-26";
pres.defineSlideMaster({
  title: "TITLE",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 1.9, fontFace: THEME.headFontFace, fontSize: 40, bold: true, color: C.background1, valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 1.4, fontFace: THEME.bodyFontFace, fontSize: 18, color: C.background2, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.5, 0.6, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 12.33, h: 0.9, fontFace: THEME.headFontFace, fontSize: 26, bold: true, color: C.text2, valign: "middle", align: "left" }, text: "" } },
    { text: { text: FOOT, options: { x: 0.5, y: 7.05, w: 8, h: 0.3, fontFace: THEME.bodyFontFace, fontSize: 10, color: "6B7A70" } } },
  ],
  slideNumber: { x: 12.3, y: 7.05, w: 0.6, h: 0.3, fontFace: THEME.bodyFontFace, fontSize: 10, color: "6B7A70", align: "right" },
});

const T = (slide, text, o) => slide.addText(text, { isTextBox: true, fontFace: THEME.bodyFontFace, color: C.text1, ...o });

// ---------------------------------------------------------------- shared drawing: field grid
function drawGrid(slide, x0, y0, cw, ch, cellFn, opts = {}) {
  const bgap = 0.14, chan = 0.3;
  const colX = (c) => x0 + c * cw + Math.floor(c / 3) * bgap;
  const rowY = (r) => y0 + r * ch + (r >= 1 ? chan : 0) + (r >= 3 ? chan : 0);
  GRID.forEach((row, r) => row.forEach((p, c) => {
    const s = cellFn(p);
    slide.addShape(pres.shapes.RECTANGLE, {
      x: colX(c) + 0.02, y: rowY(r) + 0.02, w: cw - 0.04, h: ch - 0.04,
      fill: { color: s.fill }, line: s.line || { color: C.background1, width: 0.5 },
      objectName: `plot ${p}`,
    });
    slide.addText([
      { text: String(p), options: { bold: true, fontSize: opts.pfs || 11, breakLine: true } },
      { text: s.label, options: { fontSize: opts.tfs || 10 } },
    ], { isTextBox: true, x: colX(c) + 0.02, y: rowY(r) + 0.02, w: cw - 0.04, h: ch - 0.04, margin: 0, align: "center", valign: "middle", fontFace: THEME.bodyFontFace, color: s.text });
  }));
  // channels
  [1, 3].forEach((r) => T(slide, "CHANNEL", { x: x0, y: rowY(r) - chan, w: colX(11) + cw - x0, h: chan, align: "center", valign: "middle", fontSize: 10, color: "6B7A70", charSpacing: 4, margin: 0 }));
  // block labels
  BLOCKS.forEach((b, i) => T(slide, b, { x: colX(i * 3), y: rowY(3) + ch + 0.05, w: 3 * cw, h: 0.3, align: "center", fontSize: 12, bold: true, color: C.text2, margin: 0 }));
  return { w: colX(11) + cw - x0, bottom: rowY(3) + ch + 0.35 };
}

// ---------------------------------------------------------------- slide 1: title
let s = pres.addSlide({ masterName: "TITLE" });
s.addText("Growth-stage-wise arrangement of plots for white rust severity prediction", { placeholder: "title" });
s.addText(`ASD leaf spectra of Indian mustard on 11/02, 24/02, 03/03 and 13/03/2026 | 48 plots, 4 sowing dates × 3 varieties | ${fmt(TOTAL.specH + TOTAL.specD)} unique spectra`, { placeholder: "body" });
s.addNotes("Purpose: arrange every plot-date by the growth stage it was in, so that a separate disease-severity model can be built for vegetative, flowering and pod-formation stages.");

// ---------------------------------------------------------------- slide 2: at a glance
s = pres.addSlide({ masterName: "CONTENT" });
s.addText(`${fmt(TOTAL.specH + TOTAL.specD)} unique leaf spectra from 192 plot-dates feed three stage models`, { placeholder: "title" });
const stats = [
  [fmt(TOTAL.specH + TOTAL.specD), "unique ASD leaf spectra (350-2500 nm)"],
  ["192", "plot-dates (48 plots × 4 dates)"],
  ["3", "growth stages: vegetative, flowering, pod formation"],
  ["75", "duplicated spectra removed (13/03, plots 13, 34, 38, 41, 42)"],
];
stats.forEach(([n, l], i) => {
  const x = 0.5 + i * 3.1;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.45, w: 2.85, h: 1.75, fill: { color: C.background2 }, line: { color: C.background2 }, rectRadius: 0.12, objectName: `stat ${i + 1}` });
  T(s, n, { x: x + 0.2, y: 1.55, w: 2.45, h: 0.9, fontSize: 44, bold: true, color: C.text2, fontFace: THEME.headFontFace, margin: 0, valign: "middle" });
  T(s, l, { x: x + 0.2, y: 2.45, w: 2.45, h: 0.65, fontSize: 14, color: C.text1, margin: 0, valign: "top" });
});
const rows2 = [["Date", "DAI", "Plots", "Spectra in file", "Unique spectra", "Vegetative", "Flowering", "Pod formation"].map((t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 } } }))];
const RAW = { "110226": 428, "240226": 540, "030326": 648, "130326": 723 };
DATES.forEach((d) => {
  const ps = plotsOf(d);
  const n = (st) => ps.filter((x) => x.stage === st).reduce((a, x) => a + x.n, 0);
  const np = (st) => ps.filter((x) => x.stage === st).length;
  const cell = (st) => (np(st) ? `${np(st)} plots / ${n(st)}` : "-");
  rows2.push([`${DLAB[d]}/2026`, String(DAI[d]), "48", String(RAW[d]), String(ps.reduce((a, x) => a + x.n, 0)), cell("Vegetative"), cell("Flowering"), cell("Pod formation")].map((t) => ({ text: t })));
});
s.addTable(rows2, { x: 0.5, y: 3.6, w: 12.33, colW: [1.45, 0.8, 0.9, 1.6, 1.6, 1.99, 1.99, 2.0], fontFace: THEME.bodyFontFace, fontSize: 14, color: C.text1, border: { type: "solid", pt: 0.5, color: "C9D3CC" }, rowH: 0.42, valign: "middle", align: "center" });
T(s, "Plot-date labels (plot no., variety, stage, healthy/diseased) in all four files were checked against your plot layout and stage table: all 192 agree.", { x: 0.5, y: 5.95, w: 12.33, h: 0.6, fontSize: 14, italic: true, color: C.text2, margin: 0 });
s.addNotes("Unique spectra = after removing 75 exact duplicates on 13/03. Healthy plots carry 9 spectra, diseased plots 15 (5 plants x 3 leaves); 11/02 has 3-15 spectra per plot.");

// ---------------------------------------------------------------- slide 3: layout
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Field layout: three inoculated replications and a healthy control block", { placeholder: "title" });
const g3 = drawGrid(s, 0.5, 1.4, 0.72, 1.0, (p) => {
  const L = D.layout[String(p)];
  return { fill: L.rep === "Healthy" ? C.background2 : "F7F8F6", text: C.text1, label: L.t, line: { color: "C9D3CC", width: 0.75 } };
}, { pfs: 12, tfs: 11 });
const px = 0.5 + g3.w + 0.4, pw = 13.33 - 0.5 - px;
T(s, [
  { text: "Design", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
  { text: "RBD, 48 plots of 5 × 3.5 m in a 48 × 24 m field", options: { bullet: true, breakLine: true } },
  { text: "D1 09/12, D2 18/12, D3 27/12/2025, D4 09/01/2026 sowings", options: { bullet: true, breakLine: true } },
  { text: "V1 Pusa Mustard 26, V2 Pusa Vijay, V3 Pusa Mustard 37", options: { bullet: true, breakLine: true } },
  { text: "Plots 1-12: uninoculated control; 13-48: inoculated 05/02/2026", options: { bullet: true, breakLine: true } },
  { text: "Source: your treatment_detail.xlsx and field map", options: { fontSize: 12, italic: true, color: "6B7A70" } },
], { x: px, y: 1.45, w: pw, h: 4.2, fontSize: 14, valign: "top", paraSpaceAfter: 6, margin: 0 });
s.addNotes("Cell = plot number and treatment (sowing date + variety). Orientation follows the field map (facing field, channel between rows 1-2 and 3-4).");

// ---------------------------------------------------------------- slide 4: stage calendar
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Each treatment moves through the stages at a different date", { placeholder: "title" });
const STL = { Vegetative: "V", Flowering: "F", "Pod formation": "P" };
const calRows = [["Treatment", ...DATES.map((d) => `${DLAB[d]} (${DAI[d]} DAI)`)].map((t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 } } }))];
TREATS.forEach((t) => {
  const p = Object.keys(D.layout).find((k) => D.layout[k].t === t && D.layout[k].rep !== "Healthy");
  calRows.push([{ text: t, options: { bold: true } }, ...DATES.map((d) => {
    const x = plot(d, p);
    return { text: `${STL[x.stage]}  ·  ${x.das} DAS`, options: { fill: { color: SCOL[x.stage] }, color: STXT[x.stage], bold: true } };
  })]);
});
s.addTable(calRows, { x: 0.5, y: 1.4, w: 8.6, colW: [1.6, 1.75, 1.75, 1.75, 1.75], fontFace: THEME.bodyFontFace, fontSize: 13, color: C.text1, border: { type: "solid", pt: 1, color: "FFFFFF" }, rowH: 0.4, valign: "middle", align: "center" });
const legend = (slide, x, y) => STAGES.forEach((st, i) => {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: y + i * 0.45, w: 0.35, h: 0.3, fill: { color: SCOL[st] }, line: { color: SCOL[st] }, rectRadius: 0.05, objectName: `legend ${st}` });
  T(slide, st, { x: x + 0.45, y: y + i * 0.45 - 0.02, w: 2.4, h: 0.34, fontSize: 14, margin: 0, valign: "middle" });
});
legend(s, 9.6, 1.5);
T(s, [
  { text: "Reading the calendar", options: { bold: true, color: C.text2, fontSize: 16, breakLine: true } },
  { text: "Vegetative data come only from 11/02 and from D3V2, D3V3 and D4 on 24/02", options: { bullet: true, breakLine: true } },
  { text: "Flowering is sampled on all four dates", options: { bullet: true, breakLine: true } },
  { text: "Pod formation: D1V1 on 03/03 and D1-D3 on 13/03", options: { bullet: true } },
], { x: 9.6, y: 3.0, w: 3.23, h: 3.4, fontSize: 14, valign: "top", paraSpaceAfter: 6, margin: 0 });
s.addNotes("Stage and DAS from your stage table; the same stage labels are written in every ASD file, and they agree plot by plot.");

// ---------------------------------------------------------------- slides 5-8: per-date stage maps
const DATE_MSG = {
  "110226": "11/02 (6 DAI): every plot is vegetative except D1V1, already flowering",
  "240226": "24/02 (19 DAI): early sowings flower; D3V2, D3V3 and D4 stay vegetative",
  "030326": "03/03 (26 DAI): all flowering except D1V1, now at pod formation",
  "130326": "13/03 (36 DAI): D1-D3 are at pod formation and D4 is still flowering",
};
DATES.forEach((d) => {
  s = pres.addSlide({ masterName: "CONTENT" });
  s.addText(DATE_MSG[d], { placeholder: "title" });
  const g = drawGrid(s, 0.5, 1.4, 0.7, 1.0, (p) => {
    const x = plot(d, p);
    return {
      fill: SCOL[x.stage], text: STXT[x.stage], label: x.t,
      line: x.hd === "Healthy" ? { color: C.text1, width: 2, dashType: "dash" } : { color: C.background1, width: 0.5 },
    };
  }, { pfs: 12, tfs: 11 });
  const sx = 0.5 + g.w + 0.4, sw = 13.33 - 0.5 - sx;
  legend(s, sx, 1.45);
  s.addShape(pres.shapes.RECTANGLE, { x: sx, y: 2.9, w: 0.35, h: 0.3, fill: { color: C.background1 }, line: { color: C.text1, width: 2, dashType: "dash" }, objectName: "legend healthy" });
  T(s, "Healthy (uninoculated) plot", { x: sx + 0.45, y: 2.88, w: sw - 0.45, h: 0.34, fontSize: 14, margin: 0, valign: "middle" });
  const ps = plotsOf(d);
  const tr = [["Stage", "Plots H/D", "Spectra H/D"].map((t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 } } }))];
  STAGES.forEach((st) => {
    const q = ps.filter((x) => x.stage === st);
    if (!q.length) return;
    const h = q.filter((x) => x.hd === "Healthy"), dz = q.filter((x) => x.hd !== "Healthy");
    const sum = (a) => a.reduce((z, x) => z + x.n, 0);
    tr.push([{ text: st, options: { bold: true } }, { text: `${h.length} / ${dz.length}` }, { text: `${sum(h)} / ${sum(dz)}` }]);
  });
  s.addTable(tr, { x: sx, y: 3.5, w: sw, colW: [sw * 0.4, sw * 0.27, sw * 0.33], fontFace: THEME.bodyFontFace, fontSize: 12, color: C.text1, border: { type: "solid", pt: 0.5, color: "C9D3CC" }, rowH: 0.4, valign: "middle", align: "center" });
  s.addNotes(`Map of plot growth stage on ${DLAB[d]}/2026 (${DAI[d]} days after inoculation). Cell = plot number and treatment; fill = stage; dashed outline = healthy control plot.`);
});

// ---------------------------------------------------------------- slide 9: stage datasets
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Pooling plot-dates by stage gives three modelling datasets", { placeholder: "title" });
STAGES.forEach((st, i) => {
  const x = 0.5 + i * 4.18, w = 3.97;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.4, w, h: 4.9, fill: { color: C.background2 }, line: { color: C.background2 }, rectRadius: 0.1, objectName: `${st} card` });
  s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: 1.6, w: 0.45, h: 0.45, fill: { color: SCOL[st] }, line: { color: SCOL[st] }, objectName: `${st} marker` });
  T(s, st, { x: x + 0.85, y: 1.57, w: w - 1, h: 0.5, fontSize: 20, bold: true, color: C.text2, fontFace: THEME.headFontFace, margin: 0, valign: "middle" });
  const t = tally((d, q) => q.stage === st);
  T(s, [
    { text: `${t.plotsH + t.plotsD} plot-dates`, options: { bold: true, breakLine: true } },
    { text: `${t.plotsH} healthy / ${t.plotsD} diseased`, options: { breakLine: true } },
    { text: `${fmt(t.specH + t.specD)} spectra`, options: { bold: true, breakLine: true } },
    { text: `${t.specH} healthy / ${t.specD} diseased` },
  ], { x: x + 0.25, y: 2.2, w: w - 0.5, h: 1.3, fontSize: 15, margin: 0, valign: "top" });
  const lines = [];
  DATES.forEach((d) => {
    const q = plotsOf(d).filter((x) => x.stage === st && x.hd !== "Healthy");
    if (!q.length) return;
    const tt = [...new Set(q.map((x) => x.t))].sort();
    lines.push({ text: `${DLAB[d]} (${DAI[d]} DAI): `, options: { bold: true } });
    lines.push({ text: tt.length === 11 ? "all treatments except D1V1" : tt.join(", "), options: { breakLine: true } });
  });
  lines[lines.length - 1].options.breakLine = false;
  T(s, lines, { x: x + 0.25, y: 3.65, w: w - 0.5, h: 3.0, fontSize: 14, margin: 0, valign: "top", paraSpaceAfter: 6 });
});
s.addNotes("Each stage dataset = all plot-dates observed at that stage; healthy control plots of the same treatment and date are its reference class.");

// ---------------------------------------------------------------- slide 10: counts chart
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Flowering holds half the spectra; vegetative and pod sets ~550 each", { placeholder: "title" });
const cnt = DATES.map((d) => ({
  name: `${DLAB[d]}/2026`,
  labels: STAGES,
  values: STAGES.map((st) => plotsOf(d).filter((x) => x.stage === st).reduce((a, x) => a + x.n, 0)),
}));
s.addChart(pres.charts.BAR, cnt, {
  x: 0.5, y: 1.4, w: 7.9, h: 5.4, barDir: "bar", barGrouping: "stacked", barGapWidthPct: 60,
  chartColors: DATES.map((d) => DHEX[d]), showValue: true, dataLabelPosition: "ctr", dataLabelColor: "FFFFFF", dataLabelFontSize: 12, dataLabelFormatCode: "#,##0;;", dataLabelFontFace: "+mn-lt",
  showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt",
  catAxisLabelColor: "4A5A50", valAxisLabelColor: "4A5A50", catAxisLabelFontSize: 13, valAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  valGridLine: { color: "E3E8E4", size: 0.5 }, catGridLine: { style: "none" }, catAxisOrientation: "maxMin",
  showTitle: true, title: "Unique spectra per stage, by assessment date", titleFontSize: 14, titleColor: "1F2A24", titleFontFace: "+mn-lt",
});
const kt = [["Stage", "Healthy", "Diseased", "Total"].map((t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 } } }))];
STAGES.forEach((st) => { const t = tally((d, q) => q.stage === st); kt.push([{ text: st, options: { bold: true } }, { text: fmt(t.specH) }, { text: fmt(t.specD) }, { text: fmt(t.specH + t.specD) }]); });
kt.push([{ text: "All", options: { bold: true } }, { text: fmt(TOTAL.specH) }, { text: fmt(TOTAL.specD) }, { text: fmt(TOTAL.specH + TOTAL.specD), options: { bold: true } }]);
s.addTable(kt, { x: 8.8, y: 1.6, w: 4.03, colW: [1.4, 0.85, 0.95, 0.83], fontFace: THEME.bodyFontFace, fontSize: 13, color: C.text1, border: { type: "solid", pt: 0.5, color: "C9D3CC" }, rowH: 0.42, valign: "middle", align: "center" });
T(s, "About 1 healthy spectrum per 5 diseased in every stage: use class weights or balanced sampling when training.", { x: 8.8, y: 4.0, w: 4.03, h: 1.4, fontSize: 14, italic: true, color: C.text2, margin: 0, valign: "top" });
s.addNotes("Counts after duplicate removal. Healthy = uninoculated control plots.");

// ---------------------------------------------------------------- slide 11: difference spectra
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("From 24/02, diseased leaves reflect more red and SWIR and less NIR", { placeholder: "title" });
const WL = D.wl.map(String);
STAGES.forEach((st, i) => {
  const series = DATES.filter((d) => D.diff[`${st}|${d}`]).map((d) => ({ name: DLAB[d], labels: WL, values: D.diff[`${st}|${d}`] }));
  s.addChart(pres.charts.LINE, series, {
    x: 0.5 + i * 4.18, y: 1.4, w: 3.97, h: 4.6,
    chartColors: DATES.filter((d) => D.diff[`${st}|${d}`]).map((d) => DHEX[d]), lineSize: 2, lineDataSymbol: "none",
    valAxisMinVal: -0.1, valAxisMaxVal: 0.15, valAxisMajorUnit: 0.05, valAxisLabelFormatCode: "+0.00;-0.00;0",
    catAxisLabelFrequency: "40", catAxisMajorTickMark: "none", catAxisLabelPos: "low", catAxisLabelColor: "4A5A50", valAxisLabelColor: "4A5A50", catAxisLabelFontSize: 11, valAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    valGridLine: { color: "E3E8E4", size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 11, legendFontFace: "+mn-lt",
    showTitle: true, title: `${st}: diseased − healthy`, titleFontSize: 13, titleColor: "1F2A24", titleFontFace: "+mn-lt",
    showCatAxisTitle: true, catAxisTitle: "Wavelength (nm)", catAxisTitleFontSize: 11, catAxisTitleColor: "4A5A50",
  });
});
T(s, "Mean diseased minus mean healthy reflectance within each date (removes the date-to-date offset). 11/02 shows almost no signal (6 DAI); the clearest separation is at pod formation on 03/03 (D1V1, 4 plots).", { x: 0.5, y: 6.15, w: 12.33, h: 0.7, fontSize: 14, color: C.text1, margin: 0, valign: "top" });
s.addNotes("Positive = diseased reflects more. Rise at 670-700 nm = chlorophyll loss; drop at 750-1100 nm = mesophyll damage; rise at 1650 and 2200 nm = lower leaf water.");

// ---------------------------------------------------------------- slide 12: date offset
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Raw reflectance shifts between dates: normalise before pooling dates", { placeholder: "title" });
s.addChart(pres.charts.LINE, DATES.map((d) => ({ name: `${DLAB[d]}/2026`, labels: WL, values: D.healthy[d] })), {
  x: 0.5, y: 1.4, w: 8.4, h: 5.4,
  chartColors: DATES.map((d) => DHEX[d]), lineSize: 2, lineDataSymbol: "none",
  valAxisMinVal: 0, valAxisMaxVal: 0.7, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0",
  catAxisLabelFrequency: "20", catAxisMajorTickMark: "none", catAxisLabelColor: "4A5A50", valAxisLabelColor: "4A5A50", catAxisLabelFontSize: 11, valAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  valGridLine: { color: "E3E8E4", size: 0.5 }, catGridLine: { style: "none" },
  showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt",
  showTitle: true, title: "Mean healthy-leaf reflectance by date", titleFontSize: 14, titleColor: "1F2A24", titleFontFace: "+mn-lt",
  showCatAxisTitle: true, catAxisTitle: "Wavelength (nm)", catAxisTitleFontSize: 11, catAxisTitleColor: "4A5A50",
});
const r400 = (d) => D.healthy[d][0].toFixed(2), r800 = (d) => D.healthy[d][D.wl.indexOf(800)].toFixed(2);
T(s, [
  { text: "What the healthy means show", options: { bold: true, color: C.text2, fontSize: 16, breakLine: true } },
  { text: `R400: ${DATES.map((d) => `${DLAB[d]} ${r400(d)}`).join(", ")}`, options: { bullet: true, breakLine: true } },
  { text: `R800: ${DATES.map((d) => `${DLAB[d]} ${r800(d)}`).join(", ")}`, options: { bullet: true, breakLine: true } },
  { text: "Blue reflectance near 0.3 on the first three dates is unusually high for green leaves; check white-reference and probe settings", options: { bullet: true, breakLine: true } },
  { text: "Within one date, compare diseased with that date's healthy plots, or apply SNV / first derivative before pooling dates", options: { bullet: true } },
], { x: 9.3, y: 1.5, w: 3.53, h: 5.2, fontSize: 14, valign: "top", paraSpaceAfter: 6, margin: 0 });
s.addNotes("This offset is the main risk for a model trained across dates within a stage (e.g. flowering spans all four dates).");

// ---------------------------------------------------------------- slide 13: modelling design
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Recommended workflow for stage-specific severity models", { placeholder: "title" });
const steps = [
  ["1", "Label", "Add a disease score to every spectrum (leaf grade 0-9) and DI to every plot-date; the score rows are empty in all four files"],
  ["2", "Split by stage", "Build the vegetative, flowering and pod-formation datasets shown on slide 9"],
  ["3", "Clean", "Drop duplicates; trim to 400-2400 nm; remove 1350-1450 and 1800-1950 nm water bands; Savitzky-Golay smoothing"],
  ["4", "Normalise", "SNV or first derivative so dates can share one stage model"],
  ["5", "Model", "PLSR / RF / SVR for DI or score; PLS-DA / RF for severity class"],
  ["6", "Validate", "Group k-fold by plot (no plot in both train and test) and leave-one-date-out within each stage"],
];
steps.forEach(([n, h, t], i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.5 + col * 6.25, y = 1.45 + row * 1.8;
  s.addShape(pres.shapes.OVAL, { x, y: y + 0.05, w: 0.6, h: 0.6, fill: { color: C.text2 }, line: { color: C.text2 }, objectName: `step ${n}` });
  T(s, n, { x, y: y + 0.05, w: 0.6, h: 0.6, align: "center", valign: "middle", fontSize: 18, bold: true, color: C.background1, margin: 0 });
  T(s, [{ text: h, options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } }, { text: t, options: { fontSize: 14 } }], { x: x + 0.8, y, w: 5.2, h: 1.6, margin: 0, valign: "top" });
});
s.addNotes("Group-wise validation matters: the 9-15 spectra of one plot are not independent, so random splits overstate accuracy.");

// ---------------------------------------------------------------- slide 14: data checks
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Fix these data issues before training", { placeholder: "title" });
const chk = [
  ["Disease scores missing", "The score row is empty for all spectra except healthy plots on 24/02 (score 0). Severity models need these labels."],
  ["Duplicated spectra on 13/03", "Plots 13, 34, 38, 41 and 42 (all D1) each hold the same 15 spectra twice, under file names restarting at Mustard00001. 75 copies removed here."],
  ["Uneven sampling on 11/02", "3 to 15 spectra per plot; healthy plots have 9, diseased 15 on later dates. Weight or aggregate by plot."],
  ["Small sub-sets", "Flowering on 11/02 and pod formation on 03/03 are D1V1 only (4 plots each). Keep them, but do not judge a date by them."],
  ["Leaf position", "L3 / L5 / LL labels exist for only 24 spectra (24/02). Fill them in, or drop the column."],
];
chk.forEach(([h, t], i) => {
  const y = 1.4 + i * 1.08;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 12.33, h: 0.95, fill: { color: C.background2 }, line: { color: C.background2 }, rectRadius: 0.08, objectName: `check ${i + 1}` });
  s.addShape(pres.shapes.OVAL, { x: 0.7, y: y + 0.3, w: 0.35, h: 0.35, fill: { color: i === 0 ? C.accent3 : C.accent2 }, line: { color: i === 0 ? C.accent3 : C.accent2 }, objectName: `check marker ${i + 1}` });
  T(s, h, { x: 1.25, y, w: 3.2, h: 0.95, fontSize: 15, bold: true, color: C.text2, margin: 0, valign: "middle" });
  T(s, t, { x: 4.5, y, w: 8.15, h: 0.95, fontSize: 14, margin: 0, valign: "middle" });
});
s.addNotes("Companion workbook Stage_wise_plot_index.xlsx lists every plot-date by stage with spectrum file ranges and blank DI columns to fill.");

(async () => {
  await pres.writeFile({ fileName: outPath });
  await applyTheme(outPath, THEME);
  console.log("wrote", outPath);
})();
