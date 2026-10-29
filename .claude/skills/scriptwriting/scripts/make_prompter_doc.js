/**
 * make_prompter_doc.js
 * 한비즈 유튜브 대본 → 프롬프터용 워드(.docx) 생성 (촬영용)
 *
 * 사용법:
 *   node make_prompter_doc.js <script.json> <output.docx>
 *
 * 디자인 일체 없음. 흰 배경, 검정 텍스트.
 * - 대표 대사: 18pt 큰 글씨, 한 호흡씩 줄바꿈, 같은 멘트 내 빈 줄 없음
 * - 인터뷰어 A 큐 / 시청자 속마음: 작은 회색 이탤릭
 * - CTA: 금색 굵은 글씨 구분선 + 위 공백
 * - 지문: 회색 이탤릭 가운데
 * - section: 굵은 구분(촬영 참고용, 작게)
 *
 * script.json 구조는 make_design_doc.js와 동일.
 */

const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle
} = require('docx');

const GOLD = "C9A961";
const GRAY = "8A8A8A";
const BLACK = "000000";
const NAVY = "1A2332";

// 대표 대사: 큰 글씨, 한 줄씩
function repLines(lines) {
  return lines
    .filter(l => l.trim() !== "")
    .map(ln => new Paragraph({
      spacing: { after: 40 },
      children: [new TextRun({ text: ln, font: "Arial", size: 36, color: BLACK })] // 18pt
    }));
}

// 인터뷰어 A 큐: 작은 회색 이탤릭
function interviewerCue(lines) {
  const out = [new Paragraph({ spacing: { before: 600, after: 0 }, children: [new TextRun({ text: "[A]", font: "Arial", size: 22, color: GRAY, bold: true, italics: true })] })];
  lines.filter(l => l.trim() !== "").forEach(ln => {
    out.push(new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: ln, font: "Arial", size: 22, color: GRAY, italics: true })] }));
  });
  out.push(new Paragraph({ spacing: { after: 480 }, children: [new TextRun({ text: "" })] }));
  return out;
}

// 시청자 속마음: 작은 회색 이탤릭 (독백)
function viewerCue(text) {
  return [
    new Paragraph({ spacing: { before: 360, after: 0 }, children: [new TextRun({ text: "[시청자 속마음]", font: "Arial", size: 22, color: GRAY, bold: true, italics: true })] }),
    new Paragraph({ spacing: { after: 360 }, children: [new TextRun({ text: text, font: "Arial", size: 22, color: GRAY, italics: true })] }),
  ];
}

// 지문
function direction(text) {
  return [new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 240, after: 240 },
    children: [new TextRun({ text: `( ${text} )`, font: "Arial", size: 22, color: GRAY, italics: true })]
  })];
}

// CTA: 금색 구분선 + 큰 글씨
function ctaLines(label, lines) {
  const out = [new Paragraph({
    spacing: { before: 480, after: 120 },
    border: { top: { style: BorderStyle.SINGLE, size: 12, color: GOLD, space: 6 } },
    children: [new TextRun({ text: label, font: "Arial", size: 24, color: GOLD, bold: true })]
  })];
  lines.filter(l => l.trim() !== "").forEach(ln => {
    out.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: ln, font: "Arial", size: 36, color: BLACK })] }));
  });
  out.push(new Paragraph({
    spacing: { before: 120, after: 240 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: GOLD, space: 6 } },
    children: [new TextRun({ text: "" })]
  }));
  return out;
}

// 섹션 구분 (촬영 참고용, 작게 회색)
function sectionCue(text) {
  return [new Paragraph({
    spacing: { before: 360, after: 120 },
    children: [new TextRun({ text: `— ${text} —`, font: "Arial", size: 20, color: NAVY, bold: true })]
  })];
}

// callout: 대표 대사와 동일하게 크게 (단 구분 위해 살짝 공백)
function calloutLines(lines) {
  const out = [new Paragraph({ spacing: { before: 200 }, children: [new TextRun({ text: "" })] })];
  lines.filter(l => l.trim() !== "").forEach(ln => {
    out.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: ln, font: "Arial", size: 36, color: BLACK, bold: true })] }));
  });
  out.push(new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "" })] }));
  return out;
}

// 전화번호: 큰 글씨로 또박또박
function phonesLines(items) {
  return items.map(it => new Paragraph({
    spacing: { after: 60 },
    children: [new TextRun({ text: `${it.name}  ${it.value}`, font: "Arial", size: 34, color: BLACK, bold: true })]
  }));
}

function renderBlock(b) {
  switch (b.type) {
    case "section":     return sectionCue(b.text);
    case "ment":        return repLines(b.lines);
    case "rep":         return repLines(b.lines);
    case "interviewer": return interviewerCue(b.lines);
    case "viewer":      return viewerCue(b.text);
    case "callout":     return calloutLines(b.lines);
    case "cta":         return ctaLines(b.label, b.lines);
    case "direction":   return direction(b.text);
    case "phones":      return phonesLines(b.items);
    case "spacer":      return [new Paragraph({ spacing: { after: b.h || 120 }, children: [new TextRun({ text: "" })] })];
    default:            return [];
  }
}

function build(data) {
  const children = [];
  // 제목 (프롬프터는 간결하게)
  children.push(new Paragraph({
    spacing: { after: 360 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: GRAY, space: 6 } },
    children: [new TextRun({ text: data.title, font: "Arial", size: 28, bold: true, color: BLACK })]
  }));
  for (const b of data.blocks) {
    for (const el of renderBlock(b)) children.push(el);
  }
  return new Document({
    styles: { default: { document: { run: { font: "Arial", size: 36 } } } },
    sections: [{
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      children
    }]
  });
}

const [,, inPath, outPath] = process.argv;
if (!inPath || !outPath) {
  console.error("사용법: node make_prompter_doc.js <script.json> <output.docx>");
  process.exit(1);
}
const data = JSON.parse(fs.readFileSync(inPath, "utf8"));
Packer.toBuffer(build(data)).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log("프롬프터 워드 생성 완료:", outPath);
});
