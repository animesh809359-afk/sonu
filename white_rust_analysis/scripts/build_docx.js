// Render cache/doc_blocks.json to the thesis Word report.
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType, ShadingType,
  ImageRun, PageBreak, TableOfContents, Footer, PageNumber, LevelFormat, BorderStyle, TabStopType,
} = require('docx');

const ROOT = path.join(__dirname, '..');
const B = JSON.parse(fs.readFileSync(path.join(ROOT, 'cache/doc_blocks.json'), 'utf8'));
const OUT = path.join(ROOT, 'outputs/WhiteRust_Mustard_Thesis_Analysis_Report.docx');
const FONT = 'Times New Roman';
const DK = '1F3D2B';
const TEXT_W = 9026; // A4 width 11906 - 2 x 1440 margins (DXA)
const BODY = { line: 360, after: 120 };

const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: 24, ...o });
const children = [];
const NUMS = [];

function para(t, o = {}) {
  return new Paragraph({ children: [run(t, o.run || {})], alignment: o.align || AlignmentType.JUSTIFIED, spacing: o.spacing || BODY, ...o.extra });
}

function table(b) {
  const n = b.headers.length;
  let w = b.widths && b.widths.length === n ? b.widths : Array(n).fill(1);
  const sum = w.reduce((a, c) => a + c, 0);
  let cols = w.map((x) => Math.floor((x / sum) * TEXT_W));
  cols[cols.length - 1] += TEXT_W - cols.reduce((a, c) => a + c, 0);
  const sz = b.small ? 17 : 19;
  const border = { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' };
  const borders = { top: border, bottom: border, left: border, right: border };
  const cell = (t, i, head, shade) => new TableCell({
    width: { size: cols[i], type: WidthType.DXA }, borders,
    shading: head ? { type: ShadingType.CLEAR, color: 'auto', fill: DK } : (shade ? { type: ShadingType.CLEAR, color: 'auto', fill: 'F2F5F0' } : undefined),
    margins: { top: 40, bottom: 40, left: 70, right: 70 },
    children: [new Paragraph({ spacing: { line: 240, after: 0 }, alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
      children: [run(t, { size: sz, bold: head, color: head ? 'FFFFFF' : '1A1A1A' })] })],
  });
  const rows = [new TableRow({ tableHeader: true, children: b.headers.map((h, i) => cell(h, i, true)) })]
    .concat(b.rows.map((r, k) => new TableRow({ cantSplit: true, children: r.map((v, i) => cell(v, i, false, k % 2 === 1)) })));
  children.push(new Paragraph({ keepNext: true, spacing: { before: 200, after: 80, line: 260 }, children: [run(b.caption, { bold: true, size: 21 })] }));
  children.push(new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: cols, rows }));
  if (b.note) children.push(para(b.note, { run: { size: 18, italics: true } }));
  children.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
}

function figure(b) {
  const maxW = Math.min(b.width || 6.3, 6.3) * 96;
  const [pw, ph] = b.px;
  let w = maxW, h = (ph / pw) * maxW;
  if (h > 8.2 * 96) { h = 8.2 * 96; w = (pw / ph) * h; }
  const ext = b.path.toLowerCase().endsWith('.png') ? 'png' : 'jpg';
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 60 },
    children: [new ImageRun({ type: ext, data: fs.readFileSync(b.path), transformation: { width: Math.round(w), height: Math.round(h) },
      altText: { title: b.caption, description: b.caption, name: path.basename(b.path) } })] }));
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200, line: 260 }, children: [run(b.caption, { italics: true, size: 21 })] }));
}

for (const b of B) {
  switch (b.type) {
    case 'title':
      children.push(new Paragraph({ spacing: { before: 2400, after: 400 }, alignment: AlignmentType.CENTER, children: [run(b.title, { bold: true, size: 36, color: DK })] }));
      children.push(new Paragraph({ spacing: { after: 1200 }, alignment: AlignmentType.CENTER, children: [run(b.subtitle, { size: 26, italics: true })] }));
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [run(b.author, { bold: true, size: 28 })] }));
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [run(b.affil, { size: 24 })] }));
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1200 }, children: [run(b.note, { size: 24, italics: true })] }));
      children.push(new Paragraph({ children: [new PageBreak()] }));
      children.push(new Paragraph({ spacing: { after: 200 }, children: [run('Contents', { bold: true, size: 32, color: DK })] }));
      children.push(new TableOfContents('Contents', { hyperlink: true, headingStyleRange: '1-2' }));
      children.push(new Paragraph({ spacing: { before: 120 }, children: [run('(If the contents list is empty, right-click it in Word and choose "Update Field".)', { size: 18, italics: true, color: '6E6E6E' })] }));
      children.push(new Paragraph({ children: [new PageBreak()] }));
      break;
    case 'h1': children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(b.text)] })); break;
    case 'h2': children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(b.text)] })); break;
    case 'h3': children.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(b.text)] })); break;
    case 'p': children.push(para(b.text)); break;
    case 'eq': children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 160, line: 276 }, children: [run(b.text, { italics: true, size: 22 })] })); break;
    case 'bullets': b.items.forEach((t) => children.push(new Paragraph({ numbering: { reference: 'bul', level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 320, after: 60 }, children: [run(t)] }))); break;
    case 'numbered': {
      const ref = 'num' + children.length;
      NUMS.push(ref);
      b.items.forEach((t) => children.push(new Paragraph({ numbering: { reference: ref, level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 320, after: 60 }, children: [run(t)] })));
      break;
    }
    case 'table': table(b); break;
    case 'fig': figure(b); break;
    case 'ref': children.push(new Paragraph({ alignment: AlignmentType.LEFT, indent: { left: 360, hanging: 360 }, spacing: { line: 260, after: 80 }, children: [run(b.text, { size: 21 })] })); break;
    case 'pagebreak': children.push(new Paragraph({ children: [new PageBreak()] })); break;
    default: break;
  }
}

const doc = new Document({
  creator: 'Animesh Panda', title: 'Hyperspectral detection of white rust in Indian mustard', features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 24 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 32, bold: true, color: DK }, paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 27, bold: true, color: DK }, paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1, keepNext: true } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 24, bold: true, italics: true, color: '333333' }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: { config: [{ reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] }]
    .concat(NUMS.map((r) => ({ reference: r, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] }))) },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log('wrote', OUT); });
