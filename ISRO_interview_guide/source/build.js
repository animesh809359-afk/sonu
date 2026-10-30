const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, PageBreak, Footer, Header, PageNumber,
  TableOfContents, LevelFormat, PageOrientation, LineRuleType, TabStopType, LeaderType,
} = require("docx");

const FIG = path.join(__dirname, "figs");
const W = 9026; // A4 text width in DXA with 1" margins
let figNo = 0, tabNo = 0;

// inline **bold** and *italic* parser
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "9CA3AF" };
const borders = { top: border, bottom: border, left: border, right: border };

function cell(text, width, opts = {}) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: String(text).split("|").map(t => new Paragraph({ spacing: { after: 0, line: 252 },
      children: runs(t, { size: 19, bold: !!opts.bold, color: opts.color }) })),
  });
}

function table(b) {
  const n = b.head.length;
  const widths = b.widths ? b.widths.map(x => Math.round(x * W / b.widths.reduce((a, c) => a + c, 0))) : Array(n).fill(Math.floor(W / n));
  const diff = W - widths.reduce((a, c) => a + c, 0); widths[n - 1] += diff;
  const rows = [new TableRow({ tableHeader: true, children: b.head.map((h, i) => cell(h, widths[i], { fill: "1E3A8A", bold: true, color: "FFFFFF" })) })];
  b.rows.forEach((r, k) => rows.push(new TableRow({ children: r.map((c, i) => cell(c, widths[i], { fill: k % 2 ? "F3F4F6" : "FFFFFF", bold: i === 0 && b.boldFirst !== false })) })));
  const out = [];
  if (b.cap) { tabNo++; out.push(new Paragraph({ style: "Caption", keepNext: true, children: runs(`Table ${tabNo}. ${b.cap}`) })); }
  out.push(new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths, rows }));
  out.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
  return out;
}

function figure(b) {
  const file = path.join(FIG, b.fig + ".png");
  const buf = fs.readFileSync(file);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  const maxW = (b.w || 6.2) * 96, maxH = 8.2 * 96;
  let dw = maxW, dh = maxW * h / w;
  if (dh > maxH) { dh = maxH; dw = maxH * w / h; }
  figNo++;
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60, line: 240, lineRule: LineRuleType.AUTO },
      children: [new ImageRun({ type: "png", data: buf, transformation: { width: Math.round(dw), height: Math.round(dh) },
        altText: { title: b.fig, description: b.cap, name: b.fig } })] }),
    new Paragraph({ style: "Caption", alignment: AlignmentType.CENTER, children: runs(`Figure ${figNo}. ${b.cap}`) }),
  ];
}

function list(items, ref, level = 0, inst = 0) {
  const out = [];
  for (const it of items) {
    if (Array.isArray(it)) {
      out.push(new Paragraph({ numbering: { reference: ref, level, instance: inst }, spacing: { after: 60 }, children: runs(it[0]) }));
      out.push(...list(it[1], ref === "num" ? "bul" : ref, level + 1, inst));
    } else out.push(new Paragraph({ numbering: { reference: ref, level, instance: inst }, spacing: { after: 60 }, children: runs(it) }));
  }
  return out;
}

let numInst = 0; const headings = [];
function render(blocks) {
  const out = [];
  for (const b of blocks) {
    if (b.h1) headings.push([1, b.h1]); if (b.h2) headings.push([2, b.h2]);
    if (b.h1) out.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun(b.h1)] }));
    else if (b.h2) out.push(new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, children: [new TextRun(b.h2)] }));
    else if (b.h3) out.push(new Paragraph({ heading: HeadingLevel.HEADING_3, keepNext: true, children: [new TextRun(b.h3)] }));
    else if (b.p) out.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, children: runs(b.p) }));
    else if (b.ul) out.push(...list(b.ul, "bul"));
    else if (b.ol) { numInst++; out.push(...list(b.ol, "num", 0, numInst)); }
    else if (b.table) out.push(...table(b.table));
    else if (b.fig) out.push(...figure(b));
    else if (b.eq) out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 120 },
      shading: { fill: "F8FAFC", type: ShadingType.CLEAR, color: "auto" },
      children: [new TextRun({ text: b.eq, font: "Cambria Math", size: 22 })] }));
    else if (b.key) out.push(new Paragraph({ spacing: { before: 120, after: 160 },
      shading: { fill: b.tone === "warn" ? "FEF3C7" : "E0F2FE", type: ShadingType.CLEAR, color: "auto" },
      border: { left: { style: BorderStyle.SINGLE, size: 24, color: b.tone === "warn" ? "D97706" : "0284C7", space: 8 } },
      indent: { left: 200, right: 200 },
      children: [new TextRun({ text: (b.label || "Key point") + ": ", bold: true }), ...runs(b.key)] }));
    else if (b.qa) for (const [q, a] of b.qa) {
      out.push(new Paragraph({ keepNext: true, spacing: { before: 120, after: 40 }, children: [new TextRun({ text: "Q. ", bold: true, color: "1E3A8A" }), ...runs(q, { bold: true })] }));
      out.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { left: 360 }, children: [new TextRun({ text: "A. ", bold: true, color: "15803D" }), ...runs(a)] }));
    }
    else if (b.pb) out.push(new Paragraph({ children: [new PageBreak()] }));
  }
  return out;
}

const chapters = fs.readdirSync(path.join(__dirname, "content")).filter(f => f.endsWith(".js")).sort();
let body = [];
for (const c of chapters) body = body.concat(require(path.join(__dirname, "content", c)));

const cover = [
  new Paragraph({ spacing: { before: 2400 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "ISRO INTERVIEW PREPARATION", size: 28, bold: true, color: "64748B" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 300, after: 200 }, children: [new TextRun({ text: "Space Technology for Agriculture", size: 56, bold: true, color: "1E3A8A" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 }, children: [new TextRun({ text: "A complete, point-wise study guide with diagrams, equations, research basis and model answers", size: 26, italics: true, color: "334155" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "SIF & FLEX  •  NISAR  •  Evapotranspiration (SEBAL / METRIC / ALEXI)  •  Eddy covariance", size: 21 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Crop & soil parameter retrieval  •  Meteorology & El Niño  •  Statistics & ML  •  Digital twins", size: 21 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Crop-residue burning  •  Conservation & regenerative agriculture  •  Carbon credits & MRV", size: 21 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Precision agriculture & VRT  •  FASAL, YES-TECH & PMFBY  •  IARI Agricultural Physics  •  IAIRO", size: 21 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1600 }, children: [new TextRun({ text: "Prepared: October 2026", size: 22, color: "64748B" })] }),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Contents")] }),
];
const pmap = fs.existsSync(path.join(__dirname, "tocpages.json")) ? JSON.parse(fs.readFileSync(path.join(__dirname, "tocpages.json"))) : {};
function tocParas() {
  return headings.map(([lvl, t]) => new Paragraph({ spacing: { after: lvl === 1 ? 40 : 0, before: lvl === 1 ? 100 : 0 }, indent: { left: lvl === 1 ? 0 : 360 },
    children: [new TextRun({ text: t, bold: lvl === 1, size: lvl === 1 ? 21 : 19 }),
      new TextRun({ text: "\t" + String(pmap[t] || "000"), size: lvl === 1 ? 21 : 19, bold: lvl === 1 })],
    tabStops: [{ type: TabStopType.RIGHT, position: W, leader: LeaderType.DOT }] }));
}

const doc = new Document({
  creator: "Interview preparation notes", title: "Space Technology for Agriculture — ISRO interview guide",
  styles: {
    default: { document: { run: { font: "Calibri", size: 23 }, paragraph: { spacing: { after: 120, line: 276, lineRule: LineRuleType.AUTO } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 34, bold: true, color: "1E3A8A" }, paragraph: { spacing: { before: 240, after: 200 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: "1E3A8A", space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 27, bold: true, color: "0F766E" }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, color: "374151" }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
      { id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal",
        run: { size: 18, italics: true, color: "475569" }, paragraph: { spacing: { before: 40, after: 200 } } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [0, 1, 2].map(l => ({ level: l, format: LevelFormat.BULLET, text: ["•", "◦", "▪"][l], alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540 + l * 360, hanging: 270 } } } })) },
    { reference: "num", levels: [0, 1].map(l => ({ level: l, format: l ? LevelFormat.LOWER_LETTER : LevelFormat.DECIMAL, text: l ? "%2)" : "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540 + l * 360, hanging: 300 } } } })) },
  ] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1300, left: 1440, right: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "Space Technology for Agriculture — ISRO interview guide", size: 16, color: "94A3B8" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "64748B" })] })] }) },
    children: (() => { const b = render(body); fs.writeFileSync(path.join(__dirname, "headings.json"), JSON.stringify(headings)); return [...cover, ...tocParas(), ...b]; })(),
  }],
});

const out = process.argv[2] || path.join(__dirname, "out.docx");
Packer.toBuffer(doc).then(b => { fs.writeFileSync(out, b); console.log("wrote", out, figNo, "figures", tabNo, "tables"); });
