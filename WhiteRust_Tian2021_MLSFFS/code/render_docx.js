// Generic renderer: JSON block list -> .docx (docx-js). Usage: node render_docx.js spec.json out.docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, PageBreak, TableOfContents, Footer, PageNumber,
  LevelFormat, VerticalAlign,
} = require("docx");

const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const FONT = "Times New Roman";
const PAGE_W = 11906, PAGE_H = 16838, MARGIN = 1247;          // A4, 2.2 cm margins
const CONTENT_W = PAGE_W - 2 * MARGIN;
const BORDER = { style: BorderStyle.SINGLE, size: 4, color: "8C8B86" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };

function runs(text, base = {}) {
  // supports **bold**, *italic*, ^sup^ and ~sub~ markup
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|\^[^^]+\^|~[^~]+~)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, font: FONT, ...base }));
    else if (t.startsWith("*")) out.push(new TextRun({ text: t.slice(1, -1), italics: true, font: FONT, ...base }));
    else if (t.startsWith("^")) out.push(new TextRun({ text: t.slice(1, -1), superScript: true, font: FONT, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), subScript: true, font: FONT, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, ...base }));
  return out;
}

function table(b) {
  const ncol = b.header.length;
  const total = b.widths ? b.widths.reduce((a, c) => a + c, 0) : ncol;
  const widths = (b.widths || Array(ncol).fill(1)).map(w => Math.floor(CONTENT_W * w / total));
  const tw = widths.reduce((a, c) => a + c, 0);
  const fs_ = b.fontSize || 17;
  const mk = (txt, i, head) => new TableCell({
    borders: BORDERS, width: { size: widths[i], type: WidthType.DXA },
    shading: head ? { fill: "DCE8F7", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 70, right: 70 }, verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ spacing: { before: 0, after: 0 }, children: runs(String(txt ?? ""), { size: fs_, bold: !!head }) })],
  });
  const rows = [new TableRow({ tableHeader: true, children: b.header.map((h, i) => mk(h, i, true)) })];
  for (const r of b.rows) rows.push(new TableRow({ children: r.map((c, i) => mk(c, i, false)) }));
  return new Table({ width: { size: tw, type: WidthType.DXA }, columnWidths: widths, rows });
}

const children = [];
let fig = 0;
for (const b of spec.blocks) {
  switch (b.type) {
    case "title":
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 400 }, children: runs(b.text, { size: 36, bold: true, color: "0D366B" }) }));
      break;
    case "subtitle":
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: runs(b.text, { size: 24, color: "333333" }) }));
      break;
    case "h1": children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: !!b.pageBreak, children: runs(b.text) })); break;
    case "h2": children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(b.text) })); break;
    case "h3": children.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: runs(b.text) })); break;
    case "p":
      children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 120, line: 300 }, children: runs(b.text) }));
      break;
    case "note":
      children.push(new Paragraph({ spacing: { after: 120 }, children: runs(b.text, { size: 19, italics: true, color: "52514E" }) }));
      break;
    case "eq":
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 120 }, children: runs(b.text, { italics: false, size: 22 }) }));
      break;
    case "bullets":
      for (const it of b.items) children.push(new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 280 }, alignment: AlignmentType.JUSTIFIED, children: runs(it) }));
      break;
    case "numbered":
      for (const it of b.items) children.push(new Paragraph({ numbering: { reference: b.ref || "num", level: 0 }, spacing: { after: 60, line: 280 }, alignment: AlignmentType.JUSTIFIED, children: runs(it) }));
      break;
    case "table":
      if (b.caption) children.push(new Paragraph({ keepNext: true, spacing: { before: 200, after: 80 }, children: runs(b.caption, { size: 20 }) }));
      children.push(table(b));
      if (b.note) children.push(new Paragraph({ spacing: { before: 40, after: 200 }, children: runs(b.note, { size: 17, italics: true, color: "52514E" }) }));
      else children.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
      break;
    case "figure": {
      const data = fs.readFileSync(b.path);
      const w = data.readUInt32BE(16), h = data.readUInt32BE(20);      // PNG header
      const maxw = (b.widthCm || 16) * 37.8;
      const sc = maxw / w;
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160 },
        children: [new ImageRun({ type: "png", data, transformation: { width: Math.round(w * sc), height: Math.round(h * sc) },
          altText: { title: b.caption.slice(0, 60), description: b.caption, name: path.basename(b.path) } })] }));
      children.push(new Paragraph({ spacing: { after: 240 }, children: runs(b.caption, { size: 19 }) }));
      break;
    }
    case "toc":
      children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs("Contents") }));
      children.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-3" }));
      children.push(new Paragraph({ children: runs("(Right-click the table of contents and choose 'Update field' if page numbers are missing.)", { size: 18, italics: true, color: "777777" }) }));
      break;
    case "pagebreak": children.push(new Paragraph({ children: [new PageBreak()] })); break;
    case "ref":
      children.push(new Paragraph({ spacing: { after: 80 }, indent: { left: 360, hanging: 360 }, alignment: AlignmentType.LEFT, children: runs(b.text, { size: 21 }) }));
      break;
    default: throw new Error("unknown block " + b.type);
  }
}

const doc = new Document({
  features: { updateFields: true },
  creator: "ML-SFFS analysis", title: spec.title, description: spec.title,
  styles: {
    default: { document: { run: { font: FONT, size: 23 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: FONT, color: "0D366B" }, paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: "1C5CAB" }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, italics: true, font: FONT, color: "1C5CAB" }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 280 } } } }] },
    ...["num", "num2", "num3", "num4", "num5", "num6", "num7", "num8"].map(r => ({ reference: r, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 320 } } } }] })),
  ] },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: PAGE_H }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(process.argv[3], buf); console.log("written", process.argv[3]); });
