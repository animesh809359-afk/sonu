// To-scale field layout with a 30 m buffer between inoculated and healthy plots.
// Usage: NODE_PATH=<dir with pptxgenjs> node build_layout.js out.pptx <pptx-skill>/scripts/apply_theme.js
const pptxgen = require("pptxgenjs");
const [, , outPath, themeScript] = process.argv;
const { applyTheme } = require(themeScript);

const THEME = {
  name: "Field Layout",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F2A24", lt1: "FFFFFF", dk2: "1F4D2B", lt2: "EEF2EC",
    accent1: "D9D9D6", accent2: "F6EBC0", accent3: "D7E8CF", accent4: "F2C9A8",
    accent5: "2E6DA4", accent6: "6B7A70", hlink: "2E6DA4", folHlink: "6B7A70",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Field layout with 30 m buffer";
const C = pres.SchemeColor;

// ---------------------------------------------------------------- field geometry (metres)
const PLOT_W = 3.5, PLOT_H = 5, BUND = 0.5, CHANNEL = 2, BUFFER = 30;
const BLOCK_W = 3 * PLOT_W + 2 * BUND;          // 11.5 m
const INOC_W = 3 * BLOCK_W + 2 * BUND;          // 35.5 m (R1-R3)
const FIELD_W = INOC_W + BUFFER + BLOCK_W;      // 77 m
const FIELD_H = 4 * PLOT_H + 2 * CHANNEL;       // 24 m

// Plot grid from the field map: rows top to bottom, columns R1 | R2 | R3 | Healthy
const GRID = [
  [[48, "D3V3"], [41, "D1V1"], [40, "D2V3"], [33, "D4V3"], [32, "D3V2"], [25, "D1V3"], [24, "D1V1"], [17, "D3V2"], [16, "D2V3"], [9, "D2V1"], [8, "D2V3"], [1, "D4V2"]],
  [[47, "D4V1"], [42, "D1V2"], [39, "D2V2"], [34, "D1V1"], [31, "D2V1"], [26, "D4V2"], [23, "D1V3"], [18, "D4V2"], [15, "D3V1"], [10, "D3V3"], [7, "D1V1"], [2, "D2V2"]],
  [[46, "D4V3"], [43, "D2V1"], [38, "D1V3"], [35, "D2V2"], [30, "D1V2"], [27, "D2V3"], [22, "D2V1"], [19, "D2V2"], [14, "D4V1"], [11, "D3V2"], [6, "D4V3"], [3, "D1V3"]],
  [[45, "D4V2"], [44, "D3V2"], [37, "D3V1"], [36, "D3V1"], [29, "D3V3"], [28, "D4V1"], [21, "D3V3"], [20, "D4V3"], [13, "D1V2"], [12, "D4V1"], [5, "D1V2"], [4, "D3V1"]],
];
const BLOCKS = [
  { name: "R1", fill: C.accent1 }, { name: "R2", fill: C.accent2 },
  { name: "R3", fill: C.accent3 }, { name: "HEALTHY", fill: C.accent4 },
];

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.25, w: 12.33, h: 0.75, fontFace: THEME.headFontFace, fontSize: 28, bold: true, color: C.text2, valign: "middle", align: "left" }, text: "" } },
    { text: { text: "White rust of mustard | ICAR-IARI New Delhi, rabi 2025-26", options: { x: 0.5, y: 7.05, w: 8, h: 0.3, fontFace: THEME.bodyFontFace, fontSize: 10, color: "6B7A70" } } },
  ],
  slideNumber: { x: 12.3, y: 7.05, w: 0.6, h: 0.3, fontFace: THEME.bodyFontFace, fontSize: 10, color: "6B7A70", align: "right" },
});
const T = (slide, text, o) => slide.addText(text, { isTextBox: true, fontFace: THEME.bodyFontFace, color: C.text1, margin: 0, ...o });
const line = (slide, x, y, w, h, o = {}) => slide.addShape(pres.shapes.LINE, { x, y, w, h, line: { color: "4A5A50", width: 1, ...o } });

// ---------------------------------------------------------------- slide 1: to-scale layout
// Positions are worked out in the original orientation (metres), then rotated 180 degrees so
// that the healthy block and Amrit Sarovar sit on the left and R1 on the far right.
const S = 0.14;                 // inches per metre
const X0 = 1.75, Y0 = 2.05;     // top-left corner of the field on the slide
let s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Field layout with 30 m buffer, Amrit Sarovar on the left", { placeholder: "title" });

const colM = (c) => {
  const b = Math.floor(c / 3), i = c % 3;
  const blockStart = b < 3 ? b * (BLOCK_W + BUND) : INOC_W + BUFFER;
  return blockStart + i * (PLOT_W + BUND);
};
const rowM = (r) => r * PLOT_H + (r >= 1 ? CHANNEL : 0) + (r >= 3 ? CHANNEL : 0);
// rotate a box given in original metres by 180 degrees and convert to slide inches
const box = (xm, ym, wm, hm) => ({ x: X0 + (FIELD_W - xm - wm) * S, y: Y0 + (FIELD_H - ym - hm) * S, w: wm * S, h: hm * S });
const bottom = Y0 + FIELD_H * S;

// field boundary
s.addShape(pres.shapes.RECTANGLE, { ...box(0, 0, FIELD_W, FIELD_H), fill: { color: "FAFBF9" }, line: { color: "4A5A50", width: 1 }, objectName: "field boundary" });
// buffer zone
s.addShape(pres.shapes.RECTANGLE, { ...box(INOC_W, 0, BUFFER, FIELD_H), fill: { color: C.background2 }, line: { color: "6B7A70", width: 1.25, dashType: "dash" }, objectName: "buffer zone" });
// channels
[1, 3].forEach((r) => {
  const ym = rowM(r) - CHANNEL;
  s.addShape(pres.shapes.RECTANGLE, { ...box(0, ym, FIELD_W, CHANNEL), fill: { color: "DCE8F2" }, line: { color: "DCE8F2", width: 0.5 }, objectName: `channel ${r}` });
  T(s, "CHANNEL", { ...box(0, ym, INOC_W, CHANNEL), align: "center", valign: "middle", fontSize: 10, bold: true, color: C.accent5, charSpacing: 3 });
  T(s, "CHANNEL", { ...box(INOC_W + BUFFER, ym, BLOCK_W, CHANNEL), align: "center", valign: "middle", fontSize: 10, bold: true, color: C.accent5 });
});
// buffer label (on the middle strip, between channels)
const mid = box(INOC_W, rowM(1), BUFFER, rowM(3) - CHANNEL - rowM(1));
T(s, [
  { text: "30 m BUFFER ZONE", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
  { text: "No mustard or other crucifer.", options: { fontSize: 12, breakLine: true } },
  { text: "Keep fallow or sow a non-host crop;", options: { fontSize: 12, breakLine: true } },
  { text: "remove cruciferous weeds.", options: { fontSize: 12 } },
], { x: mid.x + 0.1, y: mid.y, w: mid.w - 0.2, h: mid.h, align: "center", valign: "middle" });

// plots
GRID.forEach((row, r) => row.forEach(([p, t], c) => {
  const b = BLOCKS[Math.floor(c / 3)];
  const bx = box(colM(c), rowM(r), PLOT_W, PLOT_H);
  s.addShape(pres.shapes.RECTANGLE, { ...bx, fill: { color: b.fill }, line: { color: "4A5A50", width: 0.75 }, objectName: `plot ${p}` });
  T(s, [{ text: t, options: { bold: true, fontSize: 10, breakLine: true } }, { text: `(${p})`, options: { fontSize: 10 } }],
    { ...bx, align: "center", valign: "middle" });
}));

// block labels under the field
BLOCKS.forEach((b, i) => {
  const { x, w } = box(i < 3 ? i * (BLOCK_W + BUND) : INOC_W + BUFFER, 0, BLOCK_W, 0);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: bottom + 0.12, w, h: 0.32, fill: { color: C.accent5 }, line: { color: C.accent5 }, rectRadius: 0.05, objectName: `${b.name} label` });
  T(s, b.name, { x, y: bottom + 0.12, w, h: 0.32, align: "center", valign: "middle", fontSize: 13, bold: true, color: C.background1 });
});
const inoc = box(0, 0, INOC_W, 0), heal = box(INOC_W + BUFFER, 0, BLOCK_W, 0), buf = box(INOC_W, 0, BUFFER, 0);
T(s, "Inoculated (05/02/2026)", { x: inoc.x, y: bottom + 0.5, w: inoc.w, h: 0.3, align: "center", fontSize: 12, italic: true, color: "4A5A50" });
T(s, "Uninoculated control", { x: heal.x - 0.3, y: bottom + 0.5, w: heal.w + 0.6, h: 0.3, align: "center", fontSize: 12, italic: true, color: "4A5A50" });
// facing-field arrow: after rotation the viewing side is at the bottom
s.addShape(pres.shapes.UP_ARROW, { x: buf.x + buf.w / 2 - 0.85, y: bottom + 0.2, w: 0.3, h: 0.4, fill: { color: C.accent5 }, line: { color: C.accent5 }, objectName: "facing field arrow" });
T(s, "Facing field", { x: buf.x + buf.w / 2 - 0.45, y: bottom + 0.2, w: 1.4, h: 0.4, fontSize: 12, italic: true, color: "4A5A50", valign: "middle" });

// dimension lines above the field
const dimY = Y0 - 0.32;
const dim = (m0, m1, label) => {
  const { x, w } = box(m0, 0, m1 - m0, 0);
  line(s, x, dimY, w, 0, { beginArrowType: "triangle", endArrowType: "triangle" });
  T(s, label, { x, y: dimY - 0.3, w, h: 0.26, align: "center", fontSize: 12, bold: true, color: C.text2 });
};
dim(0, INOC_W, "35.5 m");
dim(INOC_W, INOC_W + BUFFER, "30 m buffer");
dim(INOC_W + BUFFER, FIELD_W, "11.5 m");
T(s, `Total ${FIELD_W} m × ${FIELD_H} m`, { x: X0, y: dimY - 0.62, w: FIELD_W * S, h: 0.28, align: "center", fontSize: 13, bold: true, color: C.text1 });

// vertical dimension on the left, between Amrit Sarovar and the field
const vx = X0 - 0.2;
line(s, vx, Y0, 0, FIELD_H * S, { beginArrowType: "triangle", endArrowType: "triangle" });
T(s, "24 m", { x: vx - 0.6, y: Y0 + 0.25, w: 0.52, h: 0.3, align: "right", fontSize: 12, bold: true, color: C.text2 });

// Amrit Sarovar on the left
const sv = { y: Y0 + (FIELD_H / 2) * S - 0.55 };  // centred on the field height
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.35, y: sv.y, w: 0.95, h: 1.1, fill: { color: C.accent5 }, line: { color: C.accent5 }, rectRadius: 0.12, objectName: "Amrit Sarovar" });
T(s, "Amrit Sarovar", { x: 0.35, y: sv.y, w: 0.95, h: 1.1, align: "center", valign: "middle", fontSize: 12, bold: true, color: C.background1 });

// key facts strip
T(s, [
  { text: "Plot 5 m × 3.5 m, 0.5 m bunds, 2 m channels. ", options: {} },
  { text: "Field grows from 48 m to 77 m wide (1,848 m²). ", options: { bold: true } },
  { text: "Afternoon winds at IARI blew from NW, W or N on 86 of 102 days (9 Dec-20 Mar, your weather file): place the healthy block on the north-west / west (upwind) side.", options: {} },
], { x: 0.5, y: 6.4, w: 12.33, h: 0.6, fontSize: 12, valign: "top" });
s.addNotes("Drawn to scale (0.14 inch per metre). Plot numbers and treatments are unchanged from the original layout; the layout is rotated 180 degrees (viewed from the opposite side) so Amrit Sarovar is on the left, and a 30 m buffer strip separates R3 from the healthy block. The 0.5 m bund width is inferred from the original 48 m field width (12 plots x 3.5 m = 42 m plus 11 bunds).");

// ---------------------------------------------------------------- slide 2: dimensions
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Dimensions and area of the revised layout", { placeholder: "title" });
const H = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 } } });
const rows = [
  [H("Component"), H("Width (m)"), H("Length (m)"), H("Area (m²)"), H("Contents")],
  ["Plot", "3.5", "5", "17.5", "One treatment (sowing date × variety)"],
  ["Inoculated block (R1-R3)", "35.5", "24", "852", "36 plots, 3 replications × 12 treatments"],
  ["Buffer zone", "30", "24", "720", "Fallow or non-host crop; no crucifers"],
  ["Healthy block", "11.5", "24", "276", "12 uninoculated control plots (1-12)"],
  ["Whole field", "77", "24", "1,848", "48 plots + buffer"],
].map((r, i) => (i === 0 ? r : r.map((t, j) => ({ text: t, options: { bold: j === 0 || i === 5, fill: i === 5 ? { color: C.background2 } : undefined } }))));
s.addTable(rows, { x: 0.5, y: 1.35, w: 12.33, colW: [3.0, 1.4, 1.4, 1.4, 5.13], fontFace: THEME.bodyFontFace, fontSize: 14, color: C.text1, border: { type: "solid", pt: 0.5, color: "C9D3CC" }, rowH: 0.45, valign: "middle", align: "center" });

const cards = [
  ["Why a buffer", "Albugo candida sporangia spread by wind and rain splash. A 30 m strip reduces spore drift from inoculated plots onto the healthy control, so the control stays a clean reference for the spectra and physiology."],
  ["Which side", "Afternoon winds at IARI came from NW, W or N on 86 of 102 days this season. Keep the healthy block upwind (north-west or west of the inoculated plots) where the site allows."],
  ["Inside the buffer", "Leave fallow or sow a non-crucifer (e.g. wheat). Remove cruciferous weeds such as shepherd's purse, which also host white rust."],
];
cards.forEach(([h, t], i) => {
  const x = 0.5 + i * 4.18, y = 4.35, w = 3.97;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 2.45, fill: { color: C.background2 }, line: { color: C.background2 }, rectRadius: 0.1, objectName: `${h} card` });
  s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: y + 0.25, w: 0.4, h: 0.4, fill: { color: C.text2 }, line: { color: C.text2 }, objectName: `${h} marker` });
  T(s, String(i + 1), { x: x + 0.25, y: y + 0.25, w: 0.4, h: 0.4, align: "center", valign: "middle", fontSize: 15, bold: true, color: C.background1 });
  T(s, h, { x: x + 0.8, y: y + 0.22, w: w - 1, h: 0.46, fontSize: 17, bold: true, color: C.text2, valign: "middle" });
  T(s, t, { x: x + 0.25, y: y + 0.82, w: w - 0.5, h: 1.5, fontSize: 14, valign: "top" });
});
s.addNotes("Bund width 0.5 m is inferred from the original 48 m field width; adjust if your bunds differ.");

(async () => {
  await pres.writeFile({ fileName: outPath });
  await applyTheme(outPath, THEME);
  console.log("wrote", outPath);
})();
