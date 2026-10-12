"""공고 PDF 원문에서 필요한 부분만 잘라 캡처 + 빨간 테두리 좌표 계산

    python scripts/공고PDF캡처.py <캡처.json>

캡처.json 예:
{
  "pdf": "assets/공고캡처/2026-10-12/공지-4분기금리.pdf",
  "out_dir": "assets/공고캡처/2026-10-12",
  "shots": [
    {"name": "4분기-공단대출", "page": 1,
     "from": "2026년 4분기 소상공인정책자금 금리 안내", "to": "긴급경영안정자금(‘26년거제·통영호우피해)",
     "boxes": ["혁신성장촉진자금", "연 4.52%"],     ← 이 글자가 있는 줄에 테두리 (같은 줄 전체)
     "pad": 20, "zoom": 3}
  ]
}

- from / to: 잘라낼 위·아래 경계가 되는 글자 (첫 번째로 나오는 것). to 는 그 줄의 아래끝까지 포함
- boxes: 글자 → 그 글자가 있는 «줄 띠» 전체 폭에 테두리 좌표. 결과 JSON 에 원본 픽셀 좌표로 적는다
- cell_rows: true (또는 글자 앞에 «칸:») 면 표 안의 글자는 «칸 전체»(위·아래 표 가로줄 사이)를 감싼다 — 두 줄짜리 칸용. 점선 칸 구분은 못 읽으니 한 줄 칸은 그냥 쓴다
- 결과: <out_dir>/<name>.png 와 <out_dir>/<name>.boxes.json (사진.json 의 "boxes" 에 그대로)

PDF 는 글자 위치가 정확히 나오므로 화면 캡처보다 테두리가 어긋나지 않는다.
"""
import json
import sys
from pathlib import Path

import pymupdf

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent


def find(page, text, after=None):
    hits = page.search_for(text)
    if after is not None:
        hits = [h for h in hits if h.y0 >= after - 1]
    if not hits:
        raise SystemExit(f"✗ p{page.number + 1} 에서 «{text}» 를 못 찾음")
    return hits[0]


def table_lines(page, clip):
    """표의 가로줄 (y, x0, x1) — 폭 100pt 넘는 수평 선분만"""
    out = []
    for dr in page.get_drawings():
        for it in dr["items"]:
            if it[0] == "l":
                p0, p1 = it[1], it[2]
                if abs(p0.y - p1.y) < 0.8 and abs(p1.x - p0.x) > 100:
                    out.append((p0.y, min(p0.x, p1.x), max(p0.x, p1.x)))
            elif it[0] == "re":
                r = it[1]
                if r.width > 100 and r.height < 1.5:
                    out.append((r.y0, r.x0, r.x1))
                elif r.width > 100:
                    out += [(r.y0, r.x0, r.x1), (r.y1, r.x0, r.x1)]
    return [h for h in out if clip.y0 - 2 <= h[0] <= clip.y1 + 2]


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    doc = pymupdf.open(ROOT / spec["pdf"])
    out_dir = ROOT / spec["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    for s in spec["shots"]:
        page = doc[s["page"] - 1]
        zoom, pad = s.get("zoom", 3), s.get("pad", 16)
        top = find(page, s["from"])
        bottom = find(page, s["to"], after=top.y0) if s.get("to") else page.rect
        x0 = s.get("x0", page.rect.x0 + 30)
        x1 = s.get("x1", page.rect.x1 - 30)
        clip = pymupdf.Rect(x0, top.y0 - pad, x1, bottom.y1 + pad)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
        png = out_dir / f"{s['name']}.png"
        pix.save(png)
        boxes = []
        all_lines = table_lines(page, clip)
        for t in s.get("boxes", []):
            cell = s.get("cell_rows") or t.startswith("칸:")
            t = t.removeprefix("칸:")
            r = find(page, t, after=clip.y0)
            hlines = all_lines if cell else []
            if hlines:  # 표 칸 전체: 글자 위·아래의 가장 가까운 표 가로줄 사이
                ups = [h for h in hlines if h[0] <= r.y0 + 1]
                downs = [h for h in hlines if h[0] >= r.y1 - 1]
                if ups and downs:
                    up, dn = max(ups, key=lambda h: h[0]), min(downs, key=lambda h: h[0])
                    lx0, lx1 = min(up[1], dn[1]), max(up[2], dn[2])
                    boxes.append([round((lx0 - clip.x0) * zoom), round((up[0] - clip.y0) * zoom),
                                  round((lx1 - clip.x0) * zoom), round((dn[0] - clip.y0) * zoom)])
                    continue
            # 같은 줄(세로 겹침) 의 모든 글자를 묶어 줄 띠 폭을 정한다
            words = [w for w in page.get_text("words") if w[1] < r.y1 - 1 and w[3] > r.y0 + 1 and clip.x0 <= w[0] <= clip.x1]
            lx0 = min([w[0] for w in words] + [r.x0]) - 6
            lx1 = max([w[2] for w in words] + [r.x1]) + 6
            ly0, ly1 = r.y0 - 5, r.y1 + 5
            boxes.append([round((lx0 - clip.x0) * zoom), round((ly0 - clip.y0) * zoom),
                          round((lx1 - clip.x0) * zoom), round((ly1 - clip.y0) * zoom)])
        (out_dir / f"{s['name']}.boxes.json").write_text(json.dumps(boxes), encoding="utf-8", newline="\n")
        print(f"만듦: {png.name}  {pix.width}×{pix.height}  boxes {boxes}")


if __name__ == "__main__":
    main()
