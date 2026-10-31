const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");
const { applyTheme } = require("/root/.claude/skills/synced/4f45d97b-0a27-4cd4-81ca-4f53ae4b645e_3447a982-a016-432c-b6ed-4390ec73d1e4/pptx/scripts/apply_theme.js");

const THEME = {
  name: "Thermal Infrared",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1F2A", lt1: "FFFFFF", dk2: "2B2D42", lt2: "F1F3F6",
    accent1: "D9480F", accent2: "F59F00", accent3: "1C7C8C", accent4: "5F3DC4",
    accent5: "2B8A3E", accent6: "C92A2A", hlink: "1C7C8C", folHlink: "5F3DC4",
  },
};
const HEX = THEME.colors;
const SHOT = (f) => path.join(__dirname, "shots", f);

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Satellite LST Retrieval Algorithms";
pres.author = "ISRO interview preparation";
const C = pres.SchemeColor;
const W = 13.333, H = 7.5;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "TITLE_DARK", background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.2, w: 11.7, h: 1.6, fontFace: THEME.headFontFace, fontSize: 44, bold: true, color: C.background1, valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.95, w: 11.7, h: 1.4, fontSize: 20, color: C.accent2, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION_DARK", background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.5, w: 11.7, h: 1.3, fontFace: THEME.headFontFace, fontSize: 40, bold: true, color: C.background1, valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.95, w: 11.7, h: 1.2, fontSize: 18, color: C.accent2, valign: "top" }, text: "" } },
  ],
  slideNumber: { x: 12.4, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: "BFC5CF" },
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 12.3, h: 0.8, fontFace: THEME.headFontFace, fontSize: 30, bold: true, color: C.text1, valign: "middle" }, text: "" } },
    { text: { text: "Based on Li et al. (2013), Remote Sensing of Environment 131: 14–37", options: { x: 0.5, y: 7.05, w: 8, h: 0.3, fontSize: 10, color: "8A93A3" } } },
  ],
  slideNumber: { x: 12.4, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: "8A93A3" },
});

// ---------- helpers ----------
let objN = 0;
const nm = (p) => `${p}-${++objN}`;
function box(s, x, y, w, h, text, o = {}) {
  s.addText(text, {
    shape: pres.ShapeType.roundRect, rectRadius: 0.08, x, y, w, h,
    fill: { color: o.fill || C.accent3, transparency: o.tr ?? 0 },
    line: { color: o.line || o.fill || C.accent3, width: o.lw ?? 1.25 },
    color: o.color || C.background1, fontSize: o.fs || 14, bold: !!o.bold, align: o.align || "center", valign: "middle",
    margin: o.margin ?? 0.08, isTextBox: true, objectName: nm("box"),
  });
}
function tbox(s, x, y, w, h, text, o = {}) { // tinted box with dark text
  box(s, x, y, w, h, text, { fill: o.fill || C.accent3, tr: o.tr ?? 85, line: o.fill || C.accent3, color: C.text1, fs: o.fs || 13, bold: o.bold, align: o.align || "center", margin: o.margin });
}
function arrow(s, x1, y1, x2, y2, o = {}) {
  s.addShape(pres.ShapeType.line, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: x2 < x1, flipV: y2 < y1,
    line: { color: o.color || "6B7280", width: o.w || 1.75, endArrowType: o.noHead ? undefined : "triangle", dashType: o.dash || "solid" },
    objectName: nm("arrow"),
  });
}
function txt(s, x, y, w, h, runs, o = {}) {
  s.addText(runs, { x, y, w, h, fontSize: o.fs || 15, color: o.color || C.text1, valign: o.valign || "top", align: o.align || "left", margin: o.margin ?? 0.05, isTextBox: true, objectName: nm("text"), paraSpaceAfter: o.psa ?? 6 });
}
function bullets(items, o = {}) {
  return items.map((it, i) => {
    const t = typeof it === "string" ? it : it.t;
    const lvl = typeof it === "string" ? 0 : (it.l || 0);
    const parts = t.split(/(\*\*[^*]+\*\*)/).filter(Boolean);
    return parts.map((p, k) => ({
      text: p.replace(/\*\*/g, ""),
      options: Object.assign({ bold: p.startsWith("**") }, { bullet: { indent: 16 }, indentLevel: lvl }, k === parts.length - 1 && i < items.length - 1 ? { breakLine: true } : {}, o.size ? { fontSize: o.size } : {}),
    }));
  }).flat();
}
function img(s, file, x, y, maxW, maxH, o = {}) {
  const buf = fs.readFileSync(SHOT(file));
  const w0 = buf.readUInt32BE(16), h0 = buf.readUInt32BE(20);
  let w = maxW, h = maxW * h0 / w0;
  if (h > maxH) { h = maxH; w = maxH * w0 / h0; }
  const xx = o.center ? x + (maxW - w) / 2 : x;
  s.addImage({ path: SHOT(file), x: xx, y, w, h, altText: o.alt || file, objectName: nm("img") });
  if (o.border) s.addShape(pres.ShapeType.rect, { x: xx, y, w, h, fill: { type: "none" }, line: { color: "C9CED6", width: 0.75 }, objectName: nm("frame") });
  return { x: xx, y, w, h };
}
function caption(s, x, y, w, t) { txt(s, x, y, w, 0.35, [{ text: t, options: { italic: true } }], { fs: 11, color: "6B7280" }); }
function content(title, section) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
}
function icon(s, x, y, d, label, fill) {
  s.addText(label, { shape: pres.ShapeType.ellipse, x, y, w: d, h: d, fill: { color: fill || C.accent1 }, line: { color: fill || C.accent1 }, color: C.background1, bold: true, fontSize: 16, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: nm("icon") });
}

// =============== SLIDES ===============
// 1 Title
pres.addSection({ title: "Introduction" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Introduction" });
s.addText("Land Surface Temperature from Space", { placeholder: "title" });
s.addText("Retrieval algorithms, concepts, methodology and validation\nBased on Li, Tang, Wu, Ren, Yan, Wan, Trigo & Sobrino (2013), Remote Sensing of Environment 131: 14–37", { placeholder: "body" });
s.addNotes("This deck explains how land surface temperature (LST) is retrieved from satellite thermal infrared data, following the review by Zhao-Liang Li and co-authors in Remote Sensing of Environment (2013). We go from the physics (Planck's law and the radiative transfer equation), through why the problem is ill-posed, to every family of algorithms: single-channel, split-window, multi-angle, emissivity methods (classification-based, NDVI-based, TISI), simultaneous temperature–emissivity separation (TTM, day/night, gray body, TES, ISSTES, LECTES), and full simultaneous retrieval with the atmosphere (ANN, two-step physical). We finish with validation and future directions.");

// 2 Why LST
s = content("Why land surface temperature matters", "Introduction");
txt(s, 0.5, 1.3, 6.6, 4.9, bullets([
  "LST is the **direct driving force** of long-wave radiation and turbulent heat exchange at the surface–atmosphere interface",
  "Key input for **evapotranspiration**, drought monitoring, climate change, hydrology, vegetation and urban heat studies",
  "Recognised as a **high-priority parameter** of the International Geosphere-Biosphere Programme (IGBP)",
  "LST varies strongly in space and time, so **only satellites** can map it over large areas with spatially averaged values",
  "Retrieval history dates back to the **1970s** (McMillin 1975)",
]), { fs: 17, psa: 10 });
const stats = [["1 K", "accuracy needed for LST"], ["< 10 %", "ET error target that needs it"], ["8–13 µm", "thermal atmospheric window"]];
stats.forEach(([v, l], i) => {
  const y = 1.35 + i * 1.75;
  s.addShape(pres.ShapeType.roundRect, { x: 7.7, y, w: 5.1, h: 1.5, rectRadius: 0.1, fill: { color: C.accent1, transparency: 88 }, line: { color: C.accent1, transparency: 60, width: 1 }, objectName: nm("card") });
  txt(s, 7.9, y + 0.12, 4.7, 0.8, [{ text: v, options: { bold: true, fontSize: 40, color: C.accent1, fontFace: THEME.headFontFace } }], { valign: "middle" });
  txt(s, 7.9, y + 0.9, 4.7, 0.5, [{ text: l }], { fs: 15, color: C.text2 });
});
s.addNotes("Why LST? It controls the exchange of long-wave radiation and turbulent (sensible and latent) heat between land and atmosphere. It is used in evapotranspiration models such as SEBAL, METRIC and ALEXI, in drought indices, climate studies and urban heat islands. To estimate ET with better than 10 % accuracy, LST must be retrieved to about 1 K or better (Kustas & Norman 1996; Wan & Dozier 1996). LST can change by more than 10 K over a few centimetres and by more than 1 K within a minute, so ground point measurements cannot represent large areas. Satellites are the only way to get spatially averaged values globally.");

// 3 Physics
s = content("Physical basis: Planck, Wien and emissivity", "Introduction");
tbox(s, 0.5, 1.35, 4, 1.55, "Planck's law\nBλ(T) = C1 / [λ⁵ (exp(C2/λT) − 1)]\nC1 = 1.191×10⁸ W µm⁴ sr⁻¹ m⁻²   C2 = 1.439×10⁴ µm K", { fill: C.accent1, fs: 13 });
tbox(s, 4.7, 1.35, 4, 1.55, "Wien's law\nλmax · T = 2897.9 µm K\n250–330 K → peak 11.6–8.8 µm\nWildfire ~800 K → ~3.6 µm (MIR)", { fill: C.accent2, fs: 13 });
tbox(s, 8.9, 1.35, 3.95, 1.55, "Emissivity ε\nratio of object radiance to a black body at the same T\nRadiance = ε · Bλ(T)", { fill: C.accent3, fs: 13 });
txt(s, 0.5, 3.2, 12.3, 3.6, bullets([
  "The Earth (~288 K) emits most strongly near **10 µm**, which falls inside the **8–13 µm atmospheric window**, the most transparent region for thermal radiation",
  "The **3–5 µm mid-infrared (MIR)** window is also clear: it is used for hot targets (fires) and in some LST algorithms",
  "If there were no atmosphere and ε were known, LST could be obtained simply by **inverting Planck's law**",
  "In reality the satellite also sees **atmospheric absorption, emission and reflection**, and natural surfaces are **not black bodies** (ε < 1). That is why we need retrieval algorithms",
  "Satellite channels have finite bandwidth, so all quantities are **channel-effective values** weighted by the spectral response function gi(λ)",
]), { fs: 16, psa: 8 });
s.addNotes("Every object above absolute zero emits radiation, described by Planck's law. Wien's law tells us where emission peaks: for land surfaces between 250 and 330 K the peak is between 11.6 and 8.8 µm, which conveniently sits in the 8–13 µm atmospheric window. Natural surfaces are not black bodies, so we multiply Planck radiance by emissivity. If the atmosphere had no effect, we could just invert Planck's law. In practice we must correct for the atmosphere and the emissivity, and those two corrections are what all LST algorithms are about.");

// 4 RTE
s = content("Radiative transfer equation in the thermal infrared", "Introduction");
img(s, "fig1_rte.png", 0.5, 1.25, 5.6, 5.3, { border: true, alt: "Fig. 1 of Li et al. 2013: radiative transfer paths" });
caption(s, 0.5, 6.62, 5.8, "Screenshot: Fig. 1 of Li et al. (2013), paths ① to ⑦");
img(s, "eq34_rte.png", 6.4, 1.3, 6.4, 1.2, { border: true });
img(s, "eq4b.png", 6.4, 2.6, 6.4, 2.0, { border: true });
caption(s, 6.4, 4.6, 6.4, "Screenshot: Eqs. (3) and (4) of Li et al. (2013)");
txt(s, 6.4, 5.0, 6.4, 1.9, bullets([
  "① surface radiance attenuated by the atmosphere (τ)   ② upward atmospheric emission",
  "④ surface emission ε·B(Ts)   ⑤ reflected downwelling atmospheric radiance (1−ε)·R↓",
  "③, ⑥, ⑦ solar terms: **negligible in 8–14 µm** (day and night) and in 3–5 µm at night",
]), { fs: 13, psa: 4 });
s.addNotes("This is the heart of LST retrieval. The radiance measured at the top of the atmosphere in channel i equals the radiance leaving the surface, attenuated by atmospheric transmittance τ, plus the upward atmospheric emission, plus scattered sunlight. The radiance leaving the surface itself is surface emission (emissivity times Planck at LST) plus reflection of the downward atmospheric radiance (1 minus emissivity times R-down), plus reflected sunlight. In the thermal window 8–14 µm the solar terms can be ignored, so the simplified equation is: I = [ε B(Ts) + (1−ε) R↓] τ + R↑. Radiances are usually expressed as brightness temperatures, the temperature a black body would need to give that radiance.");

// 5 Difficulties
s = content("Why LST retrieval is difficult: an ill-posed problem", "Introduction");
const diffs = [
  ["1", "Underdetermined", "N channels give N equations but N + 1 unknowns (N emissivities + 1 LST), even with a perfect atmosphere"],
  ["2", "Highly correlated channels", "TIR measurements are correlated, so noise and atmospheric errors strongly destabilise the solution"],
  ["3", "Coupling", "LST, emissivity and downward atmospheric radiance are coupled through ε; they cannot be separated physically from radiance alone"],
  ["4", "Atmospheric correction", "Needs accurate vertical profiles of temperature and water vapour, which are highly variable"],
  ["5", "Solar contamination in MIR", "By day, reflected sunlight at 3–5 µm is the same order as emission and needs surface BRDF"],
  ["6", "Physical meaning", "Satellite LST is a radiometric (skin) temperature of the top few mm; mixed pixels have no unique thermodynamic temperature"],
  ["7", "Validation", "LST can vary > 10 K over cm and > 1 K in under a minute, so ground truth rarely represents a pixel"],
];
diffs.forEach(([n, h, d], i) => {
  const col = i < 4 ? 0 : 1, row = i < 4 ? i : i - 4;
  const x = 0.5 + col * 6.35, y = 1.3 + row * 1.42;
  icon(s, x, y + 0.1, 0.6, n, C.accent1);
  txt(s, x + 0.75, y, 5.4, 0.4, [{ text: h, options: { bold: true } }], { fs: 16 });
  txt(s, x + 0.75, y + 0.38, 5.4, 0.95, [{ text: d }], { fs: 13, color: C.text2 });
});
s.addNotes("Li et al. list seven difficulties. The most fundamental is that the problem is underdetermined: with N channels you have N emissivities plus LST, so N plus 1 unknowns. Every algorithm must add information: either assume emissivity is known, add equations (more times, more angles) or add constraints on the shape of the emissivity spectrum. Second, thermal channels are highly correlated, which makes solutions unstable. Third, emissivity couples surface emission and reflected sky radiance. Fourth, atmospheric correction needs profiles of temperature and humidity. Fifth, MIR channels carry reflected sunlight by day. Sixth, the retrieved temperature is a radiometric skin temperature; over heterogeneous pixels its meaning is debated (Becker and Li 1995 definition recommended). Seventh, validation is hard because LST varies so quickly in space and time.");

// 6 Taxonomy
s = content("Taxonomy of LST retrieval algorithms", "Introduction");
box(s, 4.9, 1.2, 3.5, 0.6, "LST retrieval from TIR data", { fill: C.text1, bold: true, fs: 15 });
box(s, 1.2, 2.2, 3.6, 0.6, "Emissivity KNOWN", { fill: C.accent3, bold: true });
box(s, 8.4, 2.2, 3.9, 0.6, "Emissivity UNKNOWN", { fill: C.accent1, bold: true });
arrow(s, 6.0, 1.8, 3.0, 2.2); arrow(s, 7.3, 1.8, 10.35, 2.2);
["Single-channel", "Multi-channel (split-window)", "Multi-angle (dual-angle)"].forEach((t, i) => { tbox(s, 1.2, 3.1 + i * 0.85, 3.6, 0.65, t, { fill: C.accent3, fs: 14 }); });
arrow(s, 3.0, 2.8, 3.0, 3.1);
const unk = [
  ["Stepwise", "CBEM · NBEM (NDVI) · Day/night TISI", C.accent2],
  ["Simultaneous LST + LSE (atmosphere known)", "TTM · Physical day/night (MODIS) · GBE · TES · ISSTES · LECTES", C.accent1],
  ["Simultaneous LST + LSE + atmosphere", "ANN · Two-step physical retrieval (TSRM)", C.accent4],
];
unk.forEach(([h, d], i) => {
  const y = 3.1 + i * 1.18;
  tbox(s, 6.7, y, 6.2, 1.0, `${h}\n${d}`, { fill: unk[i][2], fs: 13 });
});
arrow(s, 10.35, 2.8, 10.35, 3.1);
txt(s, 0.5, 6.0, 5.8, 0.9, [{ text: "Every method adds information to make N + 1 unknowns solvable: known ε, extra channels, extra angles, extra times, or a constraint on the shape of the emissivity spectrum.", options: { italic: true } }], { fs: 13, color: C.text2 });
s.addNotes("The review organises algorithms by what is known about emissivity. If emissivity is known a priori, three families exist: single-channel, multi-channel (the split-window family) and multi-angle. If emissivity is unknown, there are three routes. Stepwise methods first estimate emissivity (from land-cover classes, NDVI or the TISI method) and then apply a known-emissivity algorithm. Simultaneous methods solve LST and emissivity together from atmospherically corrected radiance, using time (TTM, day/night) or spectral shape constraints (gray body, TES, ISSTES, LECTES). Finally, the most ambitious methods also retrieve the atmospheric profiles at the same time (neural networks, two-step physical retrieval), mostly from hyperspectral sounders.");

// ===== Section A: known emissivity
pres.addSection({ title: "Known emissivity" });
s = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Known emissivity" });
s.addText("Part A: algorithms with known emissivity", { placeholder: "title" });
s.addText("Single-channel · Split-window (linear, GSW, non-linear) · Multi-channel · Multi-angle", { placeholder: "body" });
s.addNotes("Part A covers methods that assume land surface emissivity is known for each pixel. They differ in how they deal with the atmosphere: by explicit radiative transfer (single-channel) or by exploiting differential absorption between channels (split-window) or between view angles (multi-angle).");

// 8 Single channel
s = content("Single-channel method (mono-window)", "Known emissivity");
const sc = ["TOA radiance in one TIR channel (≈10–11 µm)", "Atmospheric profile: radiosonde, sounder or NWP (NCEP, ECMWF)", "RTM (MODTRAN, 4A/OP) → τ, R↑, R↓", "Known emissivity ε of the pixel", "Invert RTE: B(Ts) = [(I − R↑)/τ − (1 − ε)R↓] / ε", "Invert Planck → LST"];
sc.forEach((t, i) => {
  const y = 1.25 + i * 0.88;
  box(s, 0.5, y, 5.2, 0.68, t, { fill: i === 5 ? C.accent1 : C.accent3, fs: 13, bold: i === 5 });
  if (i) arrow(s, 3.1, y - 0.2, 3.1, y);
});
txt(s, 6.1, 1.25, 6.7, 3.4, bullets([
  "Uses **one channel** in the window and corrects it with a radiative transfer model (also called the **model emissivity method**)",
  "RTM accuracy 0.5–2 % in the windows → **0.4–1.5 K** LST error",
  "**1 % emissivity error → 0.3 K** (hot, humid) to **0.7 K** (cold, dry); typical ε uncertainty gives **1–2 K**",
  "Radiosondes: ±0.5 K temperature, ±10 % water vapour; balloon drifts up to 60 km",
  "ECMWF humidity forecast errors usually add **< 0.5 K**",
]), { fs: 14, psa: 6 });
tbox(s, 6.1, 4.15, 6.7, 2.4, "Practical variants with fewer inputs\n– Qin et al. (2001) mono-window for Landsat TM6: needs near-surface air temperature and water vapour\n– Jiménez-Muñoz & Sobrino (2003, 2009) generalized single-channel: needs only ε and total water vapour; any ~1 µm wide channel\n– Empirical versions perform poorly at high water vapour", { fill: C.accent2, fs: 13, align: "left" });
s.addNotes("The single-channel method takes the radiance from one thermal channel and removes the atmosphere explicitly. You need an atmospheric profile at overpass time and a radiative transfer code such as MODTRAN to compute transmittance, upwelling and downwelling radiance. With a known emissivity you invert the equation to get the surface-emitted Planck radiance and then invert Planck's law. Accuracy depends on three things: the RTM (0.4–1.5 K), the profile (radiosondes are rarely coincident; NWP reanalysis is a practical alternative with under 0.5 K error from humidity), and emissivity (1 % error gives 0.3–0.7 K). For Landsat's single thermal band, Qin et al. 2001 and the Jiménez-Muñoz–Sobrino generalized single-channel algorithm replace profiles with water vapour and air temperature, but they degrade in very humid atmospheres, which matters for India in the monsoon.");

// 9 Split window
s = content("Split-window (SW) algorithm: the operational workhorse", "Known emissivity");
txt(s, 0.5, 1.25, 6.3, 2.6, bullets([
  "Two adjacent TIR channels near **11 µm and 12 µm** absorb water vapour differently",
  "The **difference Ti − Tj** is proportional to the atmospheric correction, so **no profile is needed**",
  "First proposed for **sea surface temperature** by McMillin (1975); extended to land from the late 1980s",
  "Coefficients come from **regressing MODTRAN-simulated** brightness temperatures over many atmospheres and surfaces",
]), { fs: 15, psa: 8 });
img(s, "eq7_sw.png", 0.5, 4.05, 6.3, 0.75, { border: true });
caption(s, 0.5, 4.85, 6.3, "Screenshot: linear SW, Eq. (7) of Li et al. (2013)");
tbox(s, 0.5, 5.3, 6.3, 1.5, "ak = f(gi, gj, εi, εj, WV, VZA)\nCoefficients depend on spectral response, the two emissivities, water vapour and view zenith angle", { fill: C.accent3, fs: 14 });
const swf = ["RT simulation database (profiles × ε × VZA)", "Simulate Ti, Tj at TOA", "Regress coefficients per WV / ε / VZA class → LUT", "Apply to image: Ti, Tj + ε (+ WV) → LST"];
swf.forEach((t, i) => { const y = 1.35 + i * 1.3; box(s, 7.4, y, 5.4, 0.9, t, { fill: i === 3 ? C.accent1 : C.accent3, fs: 14, bold: i === 3 }); if (i) arrow(s, 10.1, y - 0.4, 10.1, y); });
s.addNotes("The split-window idea: at 11 and 12 µm the atmosphere, mainly water vapour, absorbs differently. The stronger the absorption, the bigger the difference between the two brightness temperatures. So the brightness temperature difference itself tells you how much correction is needed. LST = a0 + a1 Ti + a2 (Ti − Tj). The coefficients are not universal; they depend on the sensor's spectral response, the two emissivities, the water vapour and the view angle. They are found by simulating a large database with MODTRAN and regressing, which is easier than collecting pixel-scale in situ LST. Coefficients can be parameterised in terms of emissivity only (valid for dry atmospheres, WV below 2.5 g/cm²), emissivity plus water vapour, or emissivity, water vapour and view angle (important beyond 50°).");

// 10 GSW & non-linear
s = content("Generalized split-window (MODIS) and non-linear SW", "Known emissivity");
img(s, "eq11_gsw.png", 0.5, 1.3, 6.3, 1.15, { border: true });
caption(s, 0.5, 2.5, 6.3, "Screenshot: GSW of Wan & Dozier (1996), Eq. (11) in Li et al. (2013)");
txt(s, 0.5, 2.95, 6.3, 3.9, bullets([
  "Uses MODIS **bands 31 and 32**, mean emissivity ε and difference Δε",
  "Coefficients b0–b6 stored in a **multi-dimensional LUT** by view angle, WV, ε and air temperature Ta",
  "WV sub-ranges up to **6.5 g/cm²** (0.5 overlap); ε classes **0.90–0.96** and **0.94–1.0**",
  "**Two-step**: approximate LST over Ta ± 16 K, then refine in the matching sub-range",
  "Accuracy **better than 1 K** for 263–322 K on several land covers",
  "Ignoring view angle: up to **1.6 K** error for 0.01 uncertainty in Δε/ε²",
]), { fs: 14, psa: 5 });
tbox(s, 7.2, 1.3, 5.6, 1.15, "Non-linear SW, Eq. (12)\nLST = c0 + c1 Ti + c2 (Ti − Tj) + c3 (Ti − Tj)²", { fill: C.accent1, fs: 16 });
txt(s, 7.2, 2.7, 5.6, 4.1, bullets([
  "Quadratic term corrects errors from **linearising the RTE**, important in **hot, humid** atmospheres",
  "Sobrino & Raissouni (2000) for AVHRR: c0 depends on ε, Δε and WV → **1.3 K** error vs Australian in situ data",
  "Sobrino & Romaguera (2004), Atitar & Sobrino (2009) for SEVIRI: coefficients depend on sec²(VZA) → **RMSE 1.3 K** for VZA < 50°",
  "Comparisons: most SW algorithms are statistically similar. Using **mean ε only** is recommended operationally (Yu et al. 2009)",
]), { fs: 14, psa: 5 });
s.addNotes("The MODIS generalized split-window of Wan and Dozier (1996) writes LST as a function of the mean and the difference of the two band emissivities, with seven coefficients. Rather than one set of coefficients, it uses look-up tables by view angle, water vapour sub-range, emissivity class and air temperature (or LST) sub-range, and retrieves in two steps: first approximate, then refined in the correct sub-range. Validation shows better than 1 K accuracy for several land covers in clear skies. The non-linear split-window adds a squared brightness-temperature-difference term to handle hot and humid atmospheres, where the linear approximation of transmittance with water vapour breaks down. Comparisons find most split-window formulations perform similarly; including emissivity difference can make results too sensitive to emissivity errors, so mean-emissivity forms are recommended operationally.");

// 11 Multi-channel & multi-angle
s = content("Multi-channel (3–4 channel) and multi-angle methods", "Known emissivity");
tbox(s, 0.5, 1.3, 6.0, 0.6, "Multi-channel: add MIR (3.9 µm) and 8.7 µm", { fill: C.accent2, fs: 16, bold: true });
txt(s, 0.5, 2.0, 6.0, 4.8, bullets([
  "Sun & Pinker (2003): **three-channel** night-time algorithm for GOES using 3.9 µm; RMSE **< 1 K**",
  "Sun & Pinker (2007): **four-channel** non-linear algorithm for SEVIRI with land-cover-dependent coefficients; adds a sec(VZA) term",
  "By day a **solar correction** term (d6·Ti1·cos θs) is needed for the MIR channel",
  "Cautions: MIR reflectance is high in arid regions; emissivity uncertainty is larger at 3.9 and 8.7 µm; extra channels add noise",
]), { fs: 14, psa: 6 });
tbox(s, 6.85, 1.3, 6.0, 0.6, "Multi-angle: same pixel, two path lengths", { fill: C.accent4, fs: 16, bold: true });
img(s, "eq17_da.png", 6.85, 2.05, 6.0, 0.45, { border: true });
caption(s, 6.85, 2.55, 6.0, "Screenshot: dual-angle algorithm, Eq. (17) of Li et al. (2013)");
txt(s, 6.85, 2.95, 6.0, 3.9, bullets([
  "Built for **ATSR** (ERS-1): nadir view 0–21.6° and forward view 52–55°, about **2 min apart**",
  "Longer slant path in the forward view means more absorption, so Tn − Tf gives the atmospheric correction",
  "Can beat split-window **if angular emissivity is known**",
  "Limitations: angular variation of ε and LST, pixel footprint differences, mis-registration, needs a horizontally uniform atmosphere",
  "Practical only over **homogeneous** surfaces (sea, dense forest)",
]), { fs: 14, psa: 5 });
s.addNotes("If more than two channels exist, LST can be a linear or non-linear combination of three or four brightness temperatures. Adding the 3.9 µm MIR channel helps atmospheric correction at night because it is less sensitive to water vapour, but by day it contains reflected sunlight which must be corrected. Multi-angle methods use the same idea as split-window, but instead of two wavelengths they use two view angles: the forward view travels through more atmosphere. ATSR and AATSR provided nadir and forward views. In theory dual-angle beats split-window, but the angular behaviour of emissivity and of temperature itself (sunlit versus shaded parts, 3-D structure), different footprints and co-registration errors limit it to homogeneous surfaces.");

// ===== Section B: unknown emissivity
pres.addSection({ title: "Unknown emissivity" });
s = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Unknown emissivity" });
s.addText("Part B: algorithms when emissivity is unknown", { placeholder: "title" });
s.addText("1 % emissivity error ≈ 0.5 K LST error, so emissivity must be estimated from space", { placeholder: "body" });
s.addNotes("Land emissivity differs from unity and varies with vegetation, soil moisture, roughness and view angle, so laboratory values cannot simply be used at pixel scale. Typically a 1 % emissivity uncertainty gives about 0.5 K LST error. To reach 1 K, emissivity itself must be estimated from space. Three routes: stepwise, simultaneous with known atmosphere, simultaneous with the atmosphere.");

// 13 Stepwise CBEM & NBEM
s = content("Stepwise methods: CBEM and NDVI-based emissivity", "Unknown emissivity");
tbox(s, 0.5, 1.3, 5.9, 0.6, "CBEM: classification-based emissivity", { fill: C.accent2, fs: 16, bold: true });
const cb = ["Land-cover classification (VNIR)", "Look-up table: emissivity per class (+ season, dynamic state)", "Known-ε LST algorithm (SW / single channel)"];
cb.forEach((t, i) => { const y = 2.05 + i * 0.9; box(s, 0.5, y, 5.9, 0.68, t, { fill: C.accent2, color: C.text1, fs: 13 }); if (i) arrow(s, 3.45, y - 0.22, 3.45, y); });
txt(s, 0.5, 4.8, 5.9, 2.1, bullets([
  "Snyder et al. (1998): ~**70 %** of land covers within **0.01** emissivity",
  "Simple; no atmospheric correction needed",
  "Problems: soil moisture, phenology, snow; VNIR responds to OH/Fe-oxides but TIR to Si–O; seams at class boundaries",
]), { fs: 13, psa: 4 });
tbox(s, 6.85, 1.3, 6.0, 0.6, "NBEM: NDVI threshold method (Sobrino & Raissouni 2000)", { fill: C.accent5, fs: 16, bold: true });
box(s, 6.85, 2.05, 6.0, 0.6, "Compute NDVI from red and NIR", { fill: C.accent5, fs: 13 });
arrow(s, 9.85, 2.65, 9.85, 2.85);
[["NDVI < NDVIs\nbare soil: ε from red reflectance", 6.85], ["NDVIs ≤ NDVI ≤ NDVIv\nmixed: ε = εv·Pv + εs·(1 − Pv) + dε", 8.9], ["NDVI > NDVIv\nfull vegetation: ε ≈ 0.99", 10.95]].forEach(([t, x]) => tbox(s, x, 2.85, 1.9, 1.35, t, { fill: C.accent5, fs: 11 }));
txt(s, 6.85, 4.35, 6.0, 0.5, [{ text: "Pv = [(NDVI − NDVIs)/(NDVIv − NDVIs)]²  (vegetation fraction; dε = cavity term)", options: { italic: true } }], { fs: 12, color: C.text2 });
txt(s, 6.85, 4.85, 6.0, 2.0, bullets([
  "Assumes pixel = **soil + vegetation**; ε varies linearly with vegetation fraction",
  "Needs NDVI thresholds and soil and vegetation emissivities; **soil ε is the main error source**",
  "Valid mainly in **10–12 µm**; not for water, snow, ice, rock or senescent vegetation; discontinuities between regimes",
]), { fs: 13, psa: 4 });
s.addNotes("Stepwise methods first get emissivity, then use any known-emissivity algorithm. The classification-based method assigns emissivity from land cover using a look-up table. Snyder and colleagues showed about 70 % of land covers can be assigned within 0.01. It fails where emissivity varies within a class, with moisture or snow, and for geology because visible classification is not related to thermal emissivity physics. The NDVI threshold method (widely used with Landsat) treats a pixel as a mixture of soil and vegetation: for bare soil emissivity comes from red reflectance, for full vegetation it is about 0.99, and in between it is a weighted mix by vegetation fraction from scaled NDVI, plus a cavity term. Note: the exact mixed-pixel formula shown is the standard Sobrino NDVI-THM formulation; the review describes the method and its assumptions. The weakest point is soil emissivity, and it is only valid around 10–12 µm.");

// 14 TISI
s = content("Day/night TISI method (Becker & Li; Li et al. 2000)", "Unknown emissivity");
const ti = ["Day and night MIR (3.9 µm) + TIR images, approximate atmospheric correction", "Assume TISI (temperature-independent spectral index) is the same day and night", "Day − night TISI difference isolates reflected sunlight → MIR bidirectional reflectivity", "Angular form factor or kernel BRDF model → hemispherical-directional reflectivity", "MIR emissivity = 1 − reflectivity", "TISI ratios → TIR emissivities", "Split-window LST with retrieved ε"];
ti.forEach((t, i) => { const y = 1.2 + i * 0.8; box(s, 0.5, y, 6.6, 0.62, t, { fill: i === 6 ? C.accent1 : C.accent4, fs: 12.5, bold: i === 6 }); if (i) arrow(s, 3.8, y - 0.18, 3.8, y); });
txt(s, 7.5, 1.25, 5.3, 5.6, bullets([
  "**Physically based**; needs no prior knowledge of the surface, so it works for surfaces with strong spectral contrast (bare soil, rocks)",
  "A standard atmosphere instead of the actual one gives only **≤ 3 %** emissivity and **0.5 K** LST error with SW",
  "Assumes emissivity is constant over a few days (unless rain or snow); **night dew** can break it",
  "Requires **co-registered** day and night images at **similar view angles**, plus concurrent MIR and TIR data",
]), { fs: 15, psa: 10 });
s.addNotes("TISI is a ratio of channel radiances arranged so that temperature cancels out, leaving an emissivity-related quantity. At night the MIR channel contains only emission; by day it also contains reflected sunlight. Assuming the TISI from emission is the same day and night, the day–night difference gives the MIR reflectivity. With a BRDF model you get hemispherical reflectivity, so MIR emissivity is one minus that, and the TISI ratios then give the thermal-band emissivities. Finally a split-window algorithm gives LST. It is physical and needs no land-cover knowledge, but requires approximate atmospheric correction, day/night co-registration and similar viewing angles.");

// 15 TTM and D/N
s = content("Two-temperature method and MODIS day/night physical method", "Unknown emissivity");
tbox(s, 0.5, 1.3, 6.0, 0.6, "Two-temperature method (Watson 1992)", { fill: C.accent3, fs: 16, bold: true });
box(s, 0.5, 2.05, 2.85, 1.1, "Time 1: N channels\nTime 2: N channels", { fill: C.accent3, fs: 13 });
box(s, 3.65, 2.05, 2.85, 1.1, "2N equations\nN emissivities + 2 LSTs = N + 2 unknowns", { fill: C.accent3, fs: 12 });
arrow(s, 3.35, 2.6, 3.65, 2.6);
txt(s, 0.5, 3.35, 6.0, 3.5, bullets([
  "Solvable if **N ≥ 2**; makes no assumption on spectral shape, only that **ε is time-invariant**",
  "Equations are highly correlated → **sensitive to noise** and atmospheric errors",
  "Needs a large temperature difference between times, accurate co-registration and the same view angle",
  "Best suited to **geostationary** data",
]), { fs: 14, psa: 6 });
tbox(s, 6.85, 1.3, 6.0, 0.6, "Physics-based day/night method (Wan & Li 1997, MODIS)", { fill: C.accent1, fs: 16, bold: true });
box(s, 6.85, 2.05, 2.85, 1.1, "Day + night MIR & TIR\n2N measurements", { fill: C.accent1, fs: 13 });
box(s, 10.0, 2.05, 2.85, 1.1, "N + 7 unknowns: N ε, 2 LST, 2 Ta, 2 WV, 1 form factor → N ≥ 7", { fill: C.accent1, fs: 12 });
arrow(s, 9.7, 2.6, 10.0, 2.6);
txt(s, 6.85, 3.35, 6.0, 3.5, bullets([
  "Reflected sun in MIR by day **reduces correlation** → more stable solution",
  "Ta and WV adjust the initial profile, so atmospheric correction can be approximate",
  "Works even if day and night LST are equal; images can be days apart",
  "Pixels aggregated to **5–6 km** against mis-registration; 16 VZA sub-ranges; combines Terra and Aqua",
]), { fs: 14, psa: 6 });
s.addNotes("Multi-temporal methods add equations by observing the same pixel at two times while assuming emissivity does not change. In the two-temperature method, N channels at two times give 2N equations for N emissivities and two temperatures. It is elegant but unstable because thermal channels are correlated. The MODIS day/night algorithm (MOD11B) improves on it: it uses seven bands in MIR and TIR, day and night, and also solves for air temperature, water vapour and an angular form factor, giving N plus 7 unknowns, so it needs N of at least 7. Reflected sunlight in MIR by day breaks the correlation and stabilises the solution.");

// 16 TES
s = content("Temperature–emissivity separation (TES) for ASTER", "Unknown emissivity");
const tes = [["NEM", "Normalized emissivity method: assume εmax ≈ 0.99 → initial LST and normalized emissivities"], ["SR", "Spectral ratio: βi = εi / mean(ε) → shape of the emissivity spectrum"], ["MMD", "Max–min difference of βi = spectral contrast"], ["Empirical law", "εmin = f(MMD) from laboratory spectra (power law; linear in Sabol et al. 2009)"], ["Output", "εi = βi · εmin / min(β) → refined LST"]];
tes.forEach(([h, d], i) => {
  const x = 0.5 + i * 2.55;
  box(s, x, 1.4, 2.25, 0.7, h, { fill: i === 4 ? C.accent1 : C.accent4, bold: true, fs: 16 });
  tbox(s, x, 2.2, 2.25, 1.75, d, { fill: i === 4 ? C.accent1 : C.accent4, fs: 12 });
  if (i) arrow(s, x - 0.3, 1.75, x, 1.75);
});
txt(s, 0.5, 4.2, 6.1, 2.7, bullets([
  "Gillespie et al. (1996, 1998); input: **atmospherically corrected** ASTER TIR (5 bands)",
  "Accuracy about **±1.5 K** in LST and **±0.015** in emissivity",
  "Works for any natural surface, best for **high spectral contrast** (rocks, soils)",
]), { fs: 14, psa: 6 });
txt(s, 6.85, 4.2, 6.0, 2.7, bullets([
  "Problems for **gray bodies** (water, snow, vegetation) and in hot, wet atmospheres",
  "Atmospheric errors can give **2–4 K** over bare soil; WVS correction (Tonooka 2005) helps",
  "Needs **≥ 3 TIR bands**; step discontinuities at gray-body edges",
  "Adapted to MODIS bands 29, 31, 32 (Hulley & Hook 2011)",
]), { fs: 14, psa: 6 });
s.addNotes("TES solves the N plus 1 problem by adding one empirical equation: the minimum emissivity in the spectrum is related to the spectral contrast (max minus min). It combines three modules. NEM assumes a maximum emissivity to get a first temperature and normalized emissivities. The spectral ratio module divides each emissivity by the mean, giving the spectrum's shape which is insensitive to the temperature guess. MMD measures contrast, the empirical law gives minimum emissivity, which scales the spectrum to absolute values, and temperature is recomputed. It reaches about 1.5 K and 0.015 emissivity, but struggles where contrast is low (water, vegetation) because noise and atmospheric errors look like spectral contrast.");

// 17 GBE / ISSTES / LECTES
s = content("Spectral-constraint methods: gray body, ISSTES and LECTES", "Unknown emissivity");
const sm = [
  ["Gray body emissivity (GBE)", "Barducci & Pippi (1996)", "Emissivity is flat (same) in at least two channels beyond 10 µm", "Sensitive to noise and atmospheric errors; hard with multispectral data; better for hyperspectral", C.accent3],
  ["ISSTES", "Borel (1997, 1998, 2008)", "True emissivity spectrum is smooth; a wrong LST leaves atmospheric 'saw-teeth' → choose LST maximizing smoothness", "Hyperspectral only; needs high SNR; sensitive to wavelength shifts and singular points", C.accent4],
  ["LECTES", "Wang et al. (2011)", "Emissivity linear within M segments (~10 cm⁻¹); unknowns 2M + 1 ≤ N channels", "Hyperspectral only; robust to noise, better in warm and wet atmospheres", C.accent1],
];
sm.forEach(([h, ref, a, l, col], i) => {
  const x = 0.5 + i * 4.2;
  box(s, x, 1.35, 3.95, 0.75, h, { fill: col, bold: true, fs: 17 });
  txt(s, x, 2.2, 3.95, 0.4, [{ text: ref, options: { italic: true } }], { fs: 12, color: C.text2 });
  tbox(s, x, 2.65, 3.95, 1.85, "Constraint: " + a, { fill: col, fs: 13, align: "left" });
  tbox(s, x, 4.65, 3.95, 1.6, "Limits: " + l, { fill: C.text2, tr: 90, fs: 13, align: "left" });
});
txt(s, 0.5, 6.35, 12.3, 0.6, [{ text: "Common need: accurate atmospheric correction. All three exploit the fact that emissivity spectra are smoother than atmospheric absorption features.", options: { italic: true } }], { fs: 13, color: C.text2 });
s.addNotes("These methods constrain the shape of the emissivity spectrum instead of using time. Gray-body assumes at least two channels share the same emissivity; easier to find in hyperspectral data. ISSTES uses the observation that real emissivity spectra are smooth: if the assumed temperature is wrong, the retrieved emissivity spectrum picks up the sharp atmospheric lines as saw-teeth, so you iterate temperature until the spectrum is smoothest. LECTES approximates emissivity as piecewise linear segments of about 10 wavenumbers, so unknowns are 2M plus 1, solvable when the number of hyperspectral channels exceeds that; it is more noise-resistant than ISSTES.");

// 18 ANN & TSRM
s = content("Simultaneous retrieval of LST, emissivity and atmosphere", "Unknown emissivity");
tbox(s, 0.5, 1.3, 5.9, 0.6, "Artificial neural network (ANN)", { fill: C.accent5, fs: 16, bold: true });
box(s, 0.5, 2.05, 1.75, 1.1, "Hyperspectral TOA radiances", { fill: C.accent5, fs: 12 });
box(s, 2.55, 2.05, 1.75, 1.1, "Trained network (1–2 hidden layers)", { fill: C.accent5, fs: 12 });
box(s, 4.6, 2.05, 1.8, 1.1, "LST + ε + T/WV profiles", { fill: C.accent1, fs: 12 });
arrow(s, 2.25, 2.6, 2.55, 2.6); arrow(s, 4.3, 2.6, 4.6, 2.6);
txt(s, 0.5, 3.35, 5.9, 3.5, bullets([
  "Wang et al. (2013): RMSE LST **≈ 1.6 K**, temperature profile **≈ 2 K**, WV **≈ 0.3 g/cm²**, emissivity **< 0.01** (10–14 µm)",
  "Learns complex non-linear patterns; tolerant to noise",
  "Black box: depends on architecture and training data; hard to interpret",
  "Best used to give **initial guesses** for physical methods",
]), { fs: 14, psa: 6 });
tbox(s, 6.85, 1.3, 6.0, 0.6, "Two-step physical retrieval (TSRM, Ma et al. 2000, 2002)", { fill: C.accent4, fs: 16, bold: true });
const ts = ["Initial guess: profiles, LST, ε", "Step 1: tangent-linearize RTE; PCA (5 T + 3 WV eigenvectors for 40 levels) + Tikhonov regularization", "Step 2: Newton iteration → maximum-likelihood solution", "LST, ε and T/WV profiles together (MODIS)"];
ts.forEach((t, i) => { const y = 2.05 + i * 1.12; box(s, 6.85, y, 6.0, 0.85, t, { fill: i === 3 ? C.accent1 : C.accent4, fs: 13 }); if (i) arrow(s, 9.85, y - 0.27, 9.85, y); });
txt(s, 6.85, 6.55, 6.0, 0.4, [{ text: "Needs no prior atmospheric correction, but depends strongly on the initial guess and is slow", options: { italic: true } }], { fs: 12, color: C.text2 });
s.addNotes("The ultimate solution is to retrieve the surface and the atmosphere together, which hyperspectral sounders such as AIRS and IASI make possible. ANNs map radiances directly to LST, emissivity and profiles. Wang et al. reported about 1.6 K for LST. They are fast but opaque. The two-step physical method linearises the radiative transfer equation around a first guess, reduces unknowns with principal components (five temperature and three humidity eigenvectors capture 40 levels) and stabilises the inversion with Tikhonov regularisation, then iterates with Newton's method. It needs a good first guess, which an ANN can supply.");

// 19 Comparison table
s = content("Comparison of algorithm families", "Unknown emissivity");
const hdr = ["Method", "Key assumption", "Main advantage", "Main limitation"].map(t => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk1 } } }));
const rows = [
  ["Single-channel", "ε and profile known", "Works with one TIR band (Landsat)", "Needs accurate profile + RTM"],
  ["Split-window", "Differential absorption 11/12 µm", "Simple, no profile; operational", "Degrades at high WV, large VZA"],
  ["Multi-angle", "LST independent of VZA", "Insensitive to absorber optics", "Homogeneous surfaces only"],
  ["CBEM / NBEM", "ε from class or NDVI", "Simple, no atm. correction", "Soil ε, seasonal change, rocks/water"],
  ["Day/night TISI", "TISI same day and night", "Physical, any surface", "Co-registration, same view angle"],
  ["TTM / MODIS D/N", "ε time-invariant", "Simultaneous LST + ε", "Multi-temporal data, registration"],
  ["TES", "εmin–MMD relation", "Any surface, high contrast", "Gray bodies, ≥ 3 bands, atm. errors"],
  ["ISSTES / LECTES", "Smooth / piecewise-linear ε", "Accurate with hyperspectral", "Hyperspectral only"],
  ["ANN / TSRM", "None / linearizable RTE", "Retrieves atmosphere too", "Training data / initial guess, slow"],
].map((r, i) => r.map(c => ({ text: c, options: { fill: { color: i % 2 ? HEX.lt2 : HEX.lt1 }, color: HEX.dk1 } })));
s.addTable([hdr, ...rows], { x: 0.5, y: 1.25, w: 12.3, colW: [2.2, 3.2, 3.4, 3.5], fontSize: 12.5, fontFace: THEME.bodyFontFace, border: { type: "solid", pt: 0.5, color: "C9CED6" }, rowH: 0.5, valign: "middle", objectName: nm("table") });
s.addNotes("This slide summarises Table 1 of the review. There is no universal best method: each relies on different assumptions. The practical choice depends on the sensor (number of channels, angles, revisit), whether emissivity and atmospheric profiles are available, required accuracy and computing time.");

// 20-21 Screenshot of Table 1
s = content("Table 1 of Li et al. (2013): screenshot (part 1)", "Unknown emissivity");
img(s, "table1a.png", 0.5, 1.2, 12.3, 5.7, { center: true, border: true, alt: "Table 1 part 1" });
s.addNotes("Screenshot of the first page of Table 1 from Li et al. (2013), comparing the methods with known emissivity and the stepwise and two-temperature methods: assumptions, advantages, limitations and references.");
s = content("Table 1 of Li et al. (2013): screenshot (part 2)", "Unknown emissivity");
img(s, "table1b.png", 0.5, 1.2, 12.3, 5.7, { center: true, border: true, alt: "Table 1 part 2" });
s.addNotes("Second page of Table 1: the day/night physical method, gray body, TES, ISSTES, LECTES, ANN and two-step physical retrieval.");

// 22 Decision flowchart
s = content("Choosing an algorithm: decision flowchart", "Unknown emissivity");
box(s, 4.9, 1.2, 3.5, 0.65, "Sensor & data available?", { fill: C.text1, bold: true });
const q = [["Hyperspectral TIR (sounder)?", 0.5], ["≥ 3 TIR bands (ASTER-like)?", 3.65], ["2 TIR bands (11 & 12 µm)?", 6.8], ["1 TIR band (Landsat)?", 9.95]];
q.forEach(([t, x]) => { tbox(s, x, 2.35, 2.9, 0.75, t, { fill: C.accent2, fs: 13, bold: true }); arrow(s, 6.65, 1.85, x + 1.45, 2.35); });
const a = [
  ["ISSTES / LECTES; ANN or TSRM to also get profiles", 0.5, C.accent4],
  ["TES (atm. correction needed) or day/night methods with MIR", 3.65, C.accent4],
  ["Split-window (GSW / non-linear) with ε from NDVI, class or TISI", 6.8, C.accent1],
  ["Single-channel with NWP profile + NDVI emissivity", 9.95, C.accent3],
];
a.forEach(([t, x, col]) => { box(s, x, 3.6, 2.9, 1.25, t, { fill: col, fs: 13 }); arrow(s, x + 1.45, 3.1, x + 1.45, 3.6); });
tbox(s, 0.5, 5.25, 12.35, 1.5, "Also ask: Is emissivity available (class map, NDVI, ASTER GED)? Are profiles available (NWP reanalysis)? Do you have day + night or geostationary time series (TTM, D/N)? Is the surface homogeneous (multi-angle)? What accuracy and processing time are needed?", { fill: C.text2, tr: 90, fs: 14, align: "left" });
s.addNotes("A practical decision path built from the review's conclusion that the optimal method depends on the sensor's characteristics, availability of emissivity and atmospheric information, and method complexity. Hyperspectral sounders allow spectral-smoothness methods and simultaneous atmospheric retrieval. Multispectral instruments with three or more TIR bands (ASTER) use TES. Two-band sensors (MODIS, AVHRR, INSAT-3D) use split-window with emissivity from NDVI or classification. Single-band sensors (Landsat 5–7 and often Landsat 8 band 10 alone) use single-channel algorithms with NWP water vapour.");

// ===== Section C: validation & future
pres.addSection({ title: "Validation and outlook" });
s = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Validation and outlook" });
s.addText("Part C: validation and future directions", { placeholder: "title" });
s.addText("Temperature-based · Radiance-based · Cross-validation · Hyperspectral, geostationary and all-weather LST", { placeholder: "body" });
s.addNotes("Without validation no product can be trusted. Then we look at where the field is heading.");

// 24 Validation
s = content("Three ways to validate satellite LST", "Validation and outlook");
const v = [
  ["T-based", "Temperature-based", "Compare with in situ radiometer LST at overpass over homogeneous sites (lakes, playas, dense grass, crops)", "Direct test of sensor + algorithm", "Scale mismatch (m² vs km²); mostly night and homogeneous sites; short campaigns", C.accent3],
  ["R-based", "Radiance-based", "Use in situ profile + emissivity in an RTM; adjust LST until simulated TOA radiance matches the satellite; LST difference = error", "No ground LST needed; day and night; non-isothermal surfaces", "Needs pixel-scale ε, cloud-free check and representative profiles", C.accent1],
  ["Cross", "Cross-validation", "Compare with a well-validated LST product from another satellite after space, time and view-angle matching", "Global, no ground data", "Sensitive to time and geometry mismatches; use near-identical VZA", C.accent4],
];
v.forEach(([ic, h, how, pro, con, col], i) => {
  const x = 0.5 + i * 4.2;
  box(s, x, 1.3, 3.95, 0.75, h, { fill: col, bold: true, fs: 18 });
  tbox(s, x, 2.15, 3.95, 1.9, how, { fill: col, fs: 13, align: "left" });
  txt(s, x, 4.15, 3.95, 1.25, [{ text: "+ ", options: { bold: true, color: C.accent5 } }, { text: pro }], { fs: 13 });
  txt(s, x, 4.95, 3.95, 1.5, [{ text: "− ", options: { bold: true, color: C.accent6 } }, { text: con }], { fs: 13 });
});
s.addNotes("Temperature-based validation compares satellite LST with radiometer measurements on the ground at overpass time. It is direct but only works over thermally homogeneous sites, often at night, because daytime LST can vary 10 K over a few metres. Radiance-based validation avoids ground LST: with an in situ atmospheric profile and known emissivity, you simulate the top-of-atmosphere radiance and tune LST until it matches the measured radiance; the difference from the product LST is the error. Cross-validation compares against a trusted product such as MODIS, carefully matching location, time and view angle. The three are complementary.");

// 25 Future
s = content("Future directions identified by the review", "Validation and outlook");
const fut = [
  ["Hyperspectral TIR", "Simultaneously retrieve LST, ε and atmospheric profiles; faster RTMs; combine ANN and physics"],
  ["Geostationary multi-temporal", "Use hourly SEVIRI, GOES, FY-2 data at fixed angles to separate LST and ε"],
  ["Aerosol and cirrus", "Correct heavy aerosol loads; retrieve LST through thin cirrus instead of masking"],
  ["Component temperatures", "Separate soil and canopy temperatures in mixed pixels (multi-angle, hyperspectral)"],
  ["Passive microwave fusion", "All-weather LST: combine microwave (penetrates clouds) with high-resolution TIR"],
  ["Angular and temporal normalization", "Make LST comparable across days, angles and satellites; physical meaning and validation"],
];
fut.forEach(([h, d], i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.5 + col * 6.35, y = 1.3 + row * 1.85;
  s.addShape(pres.ShapeType.roundRect, { x, y, w: 6.0, h: 1.6, rectRadius: 0.08, fill: { color: C.accent2, transparency: 88 }, line: { color: C.accent2, transparency: 50, width: 1 }, objectName: nm("card") });
  icon(s, x + 0.2, y + 0.45, 0.65, String(i + 1), C.accent1);
  txt(s, x + 1.05, y + 0.12, 4.8, 0.45, [{ text: h, options: { bold: true } }], { fs: 16 });
  txt(s, x + 1.05, y + 0.6, 4.8, 0.95, [{ text: d }], { fs: 13, color: C.text2 });
});
s.addNotes("The authors argue that multispectral methods have matured; real progress needs new data. Hyperspectral thermal sensors offer thousands of channels to retrieve the atmosphere and emissivity spectrum together. Geostationary satellites give hourly data at fixed angles, ideal for multi-temporal separation. Aerosols (thermal transmittance around 0.95–0.98) and cirrus need explicit handling. Component temperatures of soil and canopy matter for two-source energy balance models like TSEB and ALEXI. Microwave LST can fill cloudy gaps. And because polar-orbiter LST is taken at different local times and view angles, angular and temporal normalization is needed for consistent long-term records.");

// 26 India context
s = content("Relevance for ISRO and Indian agriculture (beyond the paper)", "Validation and outlook");
const ind = [
  ["INSAT-3D / 3DR / 3DS", "Geostationary imager with split-window TIR channels (~10.8 and 12 µm) → half-hourly LST; ideal for multi-temporal methods and ALEXI-type ET"],
  ["TRISHNA (ISRO–CNES)", "Upcoming high-resolution thermal mission (~57 m, multiple TIR bands, frequent revisit): field-scale ET and crop water stress, TES-type emissivity separation"],
  ["Landsat 8/9 TIRS", "Used with single-channel or split-window and NDVI emissivity for SEBAL / METRIC field-scale ET in India"],
  ["Applications", "Crop water stress (CWSI), drought (VHI = VCI + TCI), irrigation scheduling, heat-wave impact on wheat, FLEX–Sentinel-3 SLSTR LST to interpret SIF"],
];
ind.forEach(([h, d], i) => {
  const y = 1.3 + i * 1.35;
  icon(s, 0.5, y + 0.2, 0.7, ["G", "T", "L", "A"][i], [C.accent3, C.accent1, C.accent4, C.accent5][i]);
  txt(s, 1.4, y, 11.4, 0.45, [{ text: h, options: { bold: true } }], { fs: 17 });
  txt(s, 1.4, y + 0.45, 11.4, 0.85, [{ text: d }], { fs: 14, color: C.text2 });
});
txt(s, 0.5, 6.55, 12.3, 0.4, [{ text: "This slide adds Indian context for the interview and is not part of Li et al. (2013). Check mission specifications before quoting.", options: { italic: true } }], { fs: 11, color: "8A93A3" });
s.addNotes("This slide connects the review to Indian programmes. INSAT-3D series imagers carry split-window thermal channels, so LST is retrieved with a split-window approach every half hour, which suits multi-temporal methods and ALEXI-style energy balance. TRISHNA, a joint ISRO–CNES thermal mission, will provide high-resolution multi-band thermal data for field-scale evapotranspiration, where temperature–emissivity separation methods apply. Landsat thermal data with NDVI-based emissivity drive SEBAL and METRIC. LST feeds crop water stress indices, the temperature condition index used in drought monitoring, and interpretation of fluorescence from FLEX together with Sentinel-3 SLSTR land surface temperature.");

// 27 Takeaways
s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Validation and outlook" });
s.addText("Key takeaways", { placeholder: "title" });
txt(s, 0.8, 4.05, 11.7, 3.0, bullets([
  "LST retrieval is ill-posed: N channels give N + 1 unknowns, plus the atmosphere",
  "Known ε: single-channel (needs profiles), split-window (operational), multi-angle (homogeneous surfaces only)",
  "Unknown ε: stepwise (class, NDVI, TISI), simultaneous (TTM, MODIS D/N, TES, ISSTES, LECTES), or with the atmosphere (ANN, TSRM)",
  "Validate with T-based, R-based and cross-validation together; target accuracy ≈ 1 K",
]), { fs: 17, color: C.background1, psa: 8 });
s.addNotes("Interview one-liner: LST retrieval from thermal infrared is ill-posed because each channel adds an unknown emissivity, and the atmosphere must be corrected too. With known emissivity we use single-channel (with an atmospheric profile and RTM), split-window (differential absorption at 11 and 12 µm, as in MODIS GSW) or dual-angle methods. With unknown emissivity we estimate it stepwise from land cover, NDVI or TISI, or solve it simultaneously using time (two-temperature, MODIS day/night) or spectral constraints (TES for ASTER, ISSTES and LECTES for hyperspectral), or retrieve the atmosphere too with ANN or two-step physical methods. Products are validated by temperature-based, radiance-based and cross-validation, aiming at about 1 K.");

(async () => {
  const out = path.join(__dirname, "..", "LST_Retrieval_Algorithms.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
