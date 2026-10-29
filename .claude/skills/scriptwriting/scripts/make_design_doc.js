/**
 * make_design_doc.js
 * 한비즈 유튜브 대본 → 디자인용 워드(.docx) 생성 (인터뷰어/PD용)
 *
 * 사용법:
 *   node make_design_doc.js <script.json> <output.docx>
 *
 * script.json 구조:
 * {
 *   "format": "interview" | "monologue",
 *   "company": "한국중소기업 비즈니스센터" | "HANBIZ MARKETING",
 *   "footer": "한국중소기업 비즈니스센터  ·  누적 승인 5,657건  ·  승인률 97.2%  ·  수임료 0원 성공보수제",
 *   "title": "제목",
 *   "subtitle": "부제",
 *   "shooting": ["촬영 구성 줄1", "줄2", ...],
 *   "highlights": ["핵심 강조점 줄1", "줄2", ...],
 *   "blocks": [
 *     // 공통
 *     { "type": "section", "text": "1. 섹션 제목" },
 *     { "type": "callout", "lines": ["핵심 강조 멘트", ...] },
 *     { "type": "cta", "label": "[ CTA #1 — 공론화 ]", "lines": [...] },
 *     { "type": "direction", "text": "도장 찍는 제스처" },
 *     { "type": "phones", "items": [ {"name":"신용회복위원회","value":"1600-5500"}, ... ] },
 *
 *     // 독백 전용
 *     { "type": "ment", "lines": ["대표 멘트 줄1", ...] },
 *     { "type": "viewer", "text": "시청자 속마음 한 줄" },
 *
 *     // 인터뷰 전용
 *     { "type": "rep", "lines": ["대표 대사", ...] },   // 대표(베이지)
 *     { "type": "interviewer", "lines": ["A 대사", ...] } // 인터뷰어 A(흰 배경)
 *   ]
 * }
 */

const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, BorderStyle, WidthType, ShadingType,
  VerticalAlign
} = require('docx');

// ===== 색상 팔레트 =====
const NAVY = "1A2332";
const GOLD = "C9A961";
const GOLD_BG = "F2E9D0";
const BEIGE = "F5F3EE";
const GRAY = "8A8A8A";
const DARKTEXT = "222222";
const WHITE = "FFFFFF";
const REDLINE = "B03A2E";

const CONTENT_WIDTH = 9360;

function spacer(h = 120) {
  return new Paragraph({ spacing: { after: h }, children: [new TextRun({ text: "" })] });
}

// 단일 셀 박스 (좌측 컬러 바)
function barBox(lines, opts) {
  const { fill, barColor, textColor, bold } = opts;
  const paras = lines.map((ln, i) =>
    new Paragraph({
      spacing: { after: i === lines.length - 1 ? 0 : 60 },
      children: [new TextRun({ text: ln, font: "Arial", size: 24, color: textColor, bold: !!bold })]
    })
  );
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 1, color: fill },
      bottom: { style: BorderStyle.SINGLE, size: 1, color: fill },
      left: { style: BorderStyle.SINGLE, size: 18, color: barColor },
      right: { style: BorderStyle.SINGLE, size: 1, color: fill },
      insideHorizontal: { style: BorderStyle.NONE },
      insideVertical: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: CONTENT_WIDTH, type: WidthType.DXA },
        shading: { fill: fill, type: ShadingType.CLEAR },
        margins: { top: 160, bottom: 160, left: 240, right: 200 },
        children: paras
      })]
    })]
  });
}

// 대표 멘트(독백) / 대표 대사(인터뷰) — 베이지
function mentBlock(lines) {
  return barBox(lines, { fill: BEIGE, barColor: GOLD, textColor: DARKTEXT, bold: false });
}

// 인터뷰어 A 대사 — 흰 배경 + 회색 바 + 라벨
function interviewerBlock(lines) {
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 1, color: "DDDDDD" },
      bottom: { style: BorderStyle.SINGLE, size: 1, color: "DDDDDD" },
      left: { style: BorderStyle.SINGLE, size: 18, color: GRAY },
      right: { style: BorderStyle.SINGLE, size: 1, color: "DDDDDD" },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: CONTENT_WIDTH, type: WidthType.DXA },
        shading: { fill: WHITE, type: ShadingType.CLEAR },
        margins: { top: 140, bottom: 140, left: 240, right: 200 },
        children: [
          new Paragraph({ children: [new TextRun({ text: "A (인터뷰어)", font: "Arial", size: 18, color: GRAY, bold: true })] }),
          ...lines.map((ln, i) => new Paragraph({
            spacing: { before: i === 0 ? 40 : 0, after: i === lines.length - 1 ? 0 : 60 },
            children: [new TextRun({ text: ln, font: "Arial", size: 24, color: DARKTEXT })]
          }))
        ]
      })]
    })]
  });
}

// 시청자 속마음(독백) — 흰 배경 + 빨강 바 + 빨강 텍스트
function viewerBlock(line) {
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 1, color: "DDDDDD" },
      bottom: { style: BorderStyle.SINGLE, size: 1, color: "DDDDDD" },
      left: { style: BorderStyle.SINGLE, size: 18, color: REDLINE },
      right: { style: BorderStyle.SINGLE, size: 1, color: "DDDDDD" },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: CONTENT_WIDTH, type: WidthType.DXA },
        shading: { fill: WHITE, type: ShadingType.CLEAR },
        margins: { top: 140, bottom: 140, left: 240, right: 200 },
        children: [
          new Paragraph({ children: [new TextRun({ text: "시청자 속마음", font: "Arial", size: 18, color: GRAY, bold: true })] }),
          new Paragraph({ spacing: { before: 40 }, children: [new TextRun({ text: line, font: "Arial", size: 26, color: REDLINE, bold: true, italics: true })] })
        ]
      })]
    })]
  });
}

function direction(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 80 },
    children: [new TextRun({ text: `( ${text} )`, font: "Arial", size: 20, color: GRAY, italics: true })]
  });
}

function sectionBar(text) {
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    borders: {
      top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: CONTENT_WIDTH, type: WidthType.DXA },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 240, right: 200 },
        verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({ children: [new TextRun({ text: text, font: "Arial", size: 26, color: WHITE, bold: true })] })]
      })]
    })]
  });
}

function ctaBlock(label, lines) {
  const paras = [
    new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: label, font: "Arial", size: 20, color: NAVY, bold: true })] }),
    ...lines.map((ln, i) => new Paragraph({
      spacing: { after: i === lines.length - 1 ? 0 : 60 },
      children: [new TextRun({ text: ln, font: "Arial", size: 24, color: NAVY, bold: true })]
    }))
  ];
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 8, color: GOLD },
      bottom: { style: BorderStyle.SINGLE, size: 8, color: GOLD },
      left: { style: BorderStyle.SINGLE, size: 8, color: GOLD },
      right: { style: BorderStyle.SINGLE, size: 8, color: GOLD },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: CONTENT_WIDTH, type: WidthType.DXA },
        shading: { fill: GOLD_BG, type: ShadingType.CLEAR },
        margins: { top: 160, bottom: 160, left: 240, right: 200 },
        children: paras
      })]
    })]
  });
}

function calloutBlock(lines) {
  const paras = lines.map((ln, i) => new Paragraph({
    spacing: { after: i === lines.length - 1 ? 0 : 60 },
    children: [new TextRun({ text: ln, font: "Arial", size: 24, color: NAVY, bold: true })]
  }));
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 12, color: NAVY },
      bottom: { style: BorderStyle.SINGLE, size: 12, color: NAVY },
      left: { style: BorderStyle.SINGLE, size: 12, color: NAVY },
      right: { style: BorderStyle.SINGLE, size: 12, color: NAVY },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: CONTENT_WIDTH, type: WidthType.DXA },
        shading: { fill: WHITE, type: ShadingType.CLEAR },
        margins: { top: 160, bottom: 160, left: 240, right: 200 },
        children: paras
      })]
    })]
  });
}

// 전화번호 N개 강조 테이블
function phonesBlock(items) {
  const n = items.length;
  const colW = Math.floor(CONTENT_WIDTH / n);
  const widths = Array(n).fill(colW);
  widths[n - 1] = CONTENT_WIDTH - colW * (n - 1);
  const border = { style: BorderStyle.SINGLE, size: 4, color: GOLD };
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    borders: { top: border, bottom: border, left: border, right: border, insideHorizontal: border, insideVertical: border },
    rows: [
      new TableRow({ children: items.map((it, i) => new TableCell({
        width: { size: widths[i], type: WidthType.DXA },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: it.name, font: "Arial", size: 22, color: WHITE, bold: true })] })]
      })) }),
      new TableRow({ children: items.map((it, i) => new TableCell({
        width: { size: widths[i], type: WidthType.DXA },
        shading: { fill: BEIGE, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 120, left: 100, right: 100 },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: it.value, font: "Arial", size: 24, color: NAVY, bold: true })] })]
      })) }),
    ]
  });
}

// 2단 박스 (촬영 구성 / 핵심 강조점)
function twoColBox(shooting, highlights) {
  const half = 4680;
  const navyBorder = { style: BorderStyle.SINGLE, size: 4, color: NAVY };
  const mkLines = (arr) => arr.map((ln, i) => new Paragraph({
    spacing: { after: i === arr.length - 1 ? 0 : 50 },
    children: [new TextRun({ text: ln, font: "Arial", size: 20, color: DARKTEXT })]
  }));
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [half, half],
    borders: { top: navyBorder, bottom: navyBorder, left: navyBorder, right: navyBorder, insideHorizontal: navyBorder, insideVertical: navyBorder },
    rows: [
      new TableRow({ children: [
        new TableCell({ width: { size: half, type: WidthType.DXA }, shading: { fill: NAVY, type: ShadingType.CLEAR }, margins: { top: 100, bottom: 100, left: 180, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: "촬영 구성", font: "Arial", size: 22, color: WHITE, bold: true })] })] }),
        new TableCell({ width: { size: half, type: WidthType.DXA }, shading: { fill: GOLD, type: ShadingType.CLEAR }, margins: { top: 100, bottom: 100, left: 180, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: "핵심 강조점", font: "Arial", size: 22, color: NAVY, bold: true })] })] }),
      ]}),
      new TableRow({ children: [
        new TableCell({ width: { size: half, type: WidthType.DXA }, shading: { fill: BEIGE, type: ShadingType.CLEAR }, margins: { top: 120, bottom: 120, left: 180, right: 120 }, children: mkLines(shooting) }),
        new TableCell({ width: { size: half, type: WidthType.DXA }, shading: { fill: BEIGE, type: ShadingType.CLEAR }, margins: { top: 120, bottom: 120, left: 180, right: 120 }, children: mkLines(highlights) }),
      ]}),
    ]
  });
}

// ===== 블록 디스패처 =====
function renderBlock(b) {
  switch (b.type) {
    case "section":     return [sectionBar(b.text), spacer(120)];
    case "ment":        return [mentBlock(b.lines), spacer(120)];
    case "rep":         return [mentBlock(b.lines), spacer(120)];
    case "interviewer": return [interviewerBlock(b.lines), spacer(120)];
    case "viewer":      return [viewerBlock(b.text), spacer(120)];
    case "callout":     return [calloutBlock(b.lines), spacer(120)];
    case "cta":         return [ctaBlock(b.label, b.lines), spacer(160)];
    case "direction":   return [direction(b.text)];
    case "phones":      return [phonesBlock(b.items), spacer(120)];
    case "spacer":      return [spacer(b.h || 120)];
    default:            return [];
  }
}

// ===== 메인 =====
function build(data) {
  const children = [];

  // 타이틀
  children.push(new Paragraph({
    spacing: { after: 60 },
    children: [new TextRun({ text: data.title, font: "Arial", size: 36, bold: true, color: NAVY })]
  }));
  if (data.subtitle) {
    children.push(new Paragraph({
      spacing: { after: 200 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 18, color: GOLD, space: 6 } },
      children: [new TextRun({ text: data.subtitle, font: "Arial", size: 26, bold: true, color: GOLD })]
    }));
  }

  // 2단 박스
  if (data.shooting && data.highlights) {
    children.push(twoColBox(data.shooting, data.highlights));
    children.push(spacer(200));
  }

  // 본문 블록
  for (const b of data.blocks) {
    for (const el of renderBlock(b)) children.push(el);
  }

  const formatLabel = data.format === "monologue" ? "독백 대본" : "인터뷰 대본";
  return new Document({
    styles: { default: { document: { run: { font: "Arial", size: 24 } } } },
    sections: [{
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      headers: { default: new Header({ children: [new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: GOLD, space: 4 } },
        children: [
          new TextRun({ text: data.company || "한국중소기업 비즈니스센터", font: "Arial", size: 18, color: NAVY, bold: true }),
          new TextRun({ text: `   |   성제관 유튜브 ${formatLabel} (디자인)`, font: "Arial", size: 18, color: GRAY }),
        ]
      })] }) },
      footers: { default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        border: { top: { style: BorderStyle.SINGLE, size: 6, color: GOLD, space: 4 } },
        children: [new TextRun({ text: data.footer || "", font: "Arial", size: 16, color: GRAY })]
      })] }) },
      children
    }]
  });
}

// ===== CLI =====
const [,, inPath, outPath] = process.argv;
if (!inPath || !outPath) {
  console.error("사용법: node make_design_doc.js <script.json> <output.docx>");
  process.exit(1);
}
const data = JSON.parse(fs.readFileSync(inPath, "utf8"));
Packer.toBuffer(build(data)).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log("디자인 워드 생성 완료:", outPath);
});
