# -*- coding: utf-8 -*-
"""
blogkit — 네이버 블로그 원고 검사 + «복사용 페이지» 만들기 (업종 무관판)

  python blogkit.py <글폴더>                       검사 → 통과하면 <글폴더>/복사용.html · <글폴더>/올릴사진/
  python blogkit.py <글폴더> --rules <업체설정.md>  업체 금지어·필수 문구까지 검사
  python blogkit.py <글폴더> --check               검사만(파일을 만들지 않음)

종료코드: 0 통과(⚠ 는 있을 수 있음) · 2 ✗ 가 있어 만들지 않음 · 1 사용법 오류

글폴더
  글.md        원고(머리 + --- + 본문). 문법은 references/서식_표시문법.md
  사진.json    (선택) [{"file":"01.jpg","src":"원본/IMG_1234.jpg","crop"?:[x0,y0,x1,y1],"center"?:true,
                        "blur"?:[[x0,y0,x1,y1]],"labels"?:[{"text":"손잡이 각인","at":[x,y],"to"?:[x,y]}]}]
                좌표는 원본 사진 기준. at = 글 상자 가운데, to = 화살표 끝. center 는 rembg 가 있으면 주인공 사물을 가운데로.
               (표시.json 이라는 이름도 읽는다)
  사진은 붙여넣지 않는다 — 붙여 넣은 외부 사진은 네이버에 올라가지 않고 링크로만 남는다. 페이지의 파란 «사진 자리»에 직접 올린다.
"""
import argparse, html, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")

# ── 표시 문법 → 인라인 스타일(네이버 편집기에 붙여 넣으면 색·굵게·크기·배경·테두리가 살아남는다) ──
COLORS = {
    "자": "color:#b0238f;font-weight:bold;",                     # 자주 — 첫 인사·용어 풀이 첫 줄
    "빨": "color:#d10000;font-weight:bold;",                     # 빨강 — 결론·주의 한 줄
    "초": "color:#1e8c2e;font-weight:bold;",                     # 초록 — 혜택·할인
    "분": "color:#e0287a;font-weight:bold;",                     # 분홍 — 혜택·할인
    "형": "background-color:#ffe3c8;font-weight:bold;",          # 주황 형광 — 절에서 가장 중요한 문장
    "노": "background-color:#fff3a8;font-weight:bold;",          # 노랑 형광
    "파": "color:#1f5fbf;font-weight:bold;",                     # 파랑 — 다시 나온 고유명사·용어
    "큰": "font-size:20px;font-weight:bold;color:#222;",         # 큰 글씨
    "이": "background-color:#fde3cf;border:1px solid #e8a77c;border-radius:3px;padding:0 3px;font-weight:bold;color:#333;",  # 사람 이름(처음)
    "고": "background-color:#e3eefb;border:1px solid #7fa6d9;border-radius:3px;padding:0 3px;font-weight:bold;color:#1f4f8f;",  # 기관·용어·작품(처음)
    "연": "color:#d2591a;font-weight:bold;",                     # 연도·숫자
    "지": "color:#13806e;font-weight:bold;",                     # 지명
}
MARK = "|".join(COLORS)
FF = "font-family:'나눔고딕',NanumGothic,'Nanum Gothic',sans-serif;"
P_C = FF + "text-align:center;font-size:16px;line-height:1.9;color:#333;margin:0;"
P_L = FF + "text-align:left;font-size:16px;line-height:1.9;color:#333;margin:0;"
LEFT_SECTIONS = ("찾아오시는", "오시는 길", "참고", "출처", "매장 안내", "위치")

# ── 공통 금지(모든 업종) ──
BAN = [
    (r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", "이모지 — 블로그 본문에 쓰지 않는다"),
    (r"초특가|득템|역대급|강추|놓치지 마세요|무조건|대박|파격", "호객 표현"),
]
SOFT = [  # 경고만 — 근거 없는 최상급·과장(표시광고법 위험 + AI티)
    (r"완벽한|완벽하게|최고의|최고 수준|폭발적|압도적|유일한|극도로|업계 최고|No\.?1|넘버원|1위", "과장·최상급 — 근거(연도·수치·방법)로 바꾸기"),
    (r"를 통해|을 통해|에 있어|에 의해|가지고 있다|결론적으로|시사하는 바", "번역투·AI티 — «~로», «~에서»로"),
    (r"트렌디|핫한|힙한", "유행어 — 구체 묘사로"),
    (r"심플한|깔끔한|예쁜|좋은", "빈약한 묘사 — 무엇이 어떻게 다른지로(자주 쓰면)"),
]


def plain(s):
    return re.sub(r"\{(?:%s)\}|\{/\}|\*\*|^>>? |^## |^Q\. " % MARK, "", s)


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"\{(%s)\}(.+?)\{/\}" % MARK, lambda m: f'<span style="{COLORS[m[1]]}">{m[2]}</span>', s)


def head_meta(text):
    head = text.split("\n---\n", 1)[0]
    return {k: v.strip() for k, v in re.findall(r"^([^\s:]+):\s*(.+)$", head, re.M)}


def blocks(body):
    """(소제목, 줄 목록) 묶음"""
    sec, out = "머리", []
    for b in re.split(r"\n\s*\n", body.strip()):
        lines = [l.rstrip() for l in b.strip().split("\n") if l.strip()]
        if not lines:
            continue
        if lines[0].startswith("## "):
            sec = plain(lines[0])
        out.append((sec, lines))
    return out


def width(s, story):
    t = plain(s)
    if story:  # 이야기 글은 괄호 속 원어·숫자 단위를 세지 않는다
        t = re.sub(r"\([A-Za-z0-9 .,'&/~%약-]+\)", "", t)
    return len(t)


def read_rules(path):
    """업체설정.md 의 «## 금지어» 표(| 낱말 | 이유 |)·«## 필수 문구» 목록을 읽는다"""
    if not path:
        return [], []
    t = open(path, encoding="utf-8").read()
    ban, must = [], []
    m = re.search(r"^## 금지어.*?$(.*?)(?=^## |\Z)", t, re.M | re.S)
    if m:
        for row in re.findall(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|", m[1], re.M):
            if row[0] and not set(row[0]) <= set("-: ") and row[0] not in ("낱말", "표현") and not row[0].startswith("("):
                words = [w.strip() for w in row[0].split(" / ") if w.strip()]  # 여러 낱말은 « / » 로 나눈다
                ban.append(("|".join(re.escape(w) for w in words), row[1] or "업체 금지어"))
    m = re.search(r"^## 필수 문구.*?$(.*?)(?=^## |\Z)", t, re.M | re.S)
    if m:  # «(예: …)» 처럼 괄호로 시작하는 줄은 안내문이라 건너뛴다
        must = [x.strip() for x in re.findall(r"^-\s+(.+)$", m[1], re.M) if not x.strip().startswith("(")]
    return ban, must


def lint(text, meta, photos, folder, rules):
    err, warn = [], []
    body = text.split("\n---\n", 1)[1] if "\n---\n" in text else ""
    kind = meta.get("종류", "설명")
    story = kind == "이야기"
    maxw = int(meta.get("줄", 24 if story else 20))
    maxp = 7 if story else 4
    if not meta.get("제목"):
        err.append("머리에 `제목:` 이 없다")
    if not body:
        err.append("머리 뒤 `---` 줄과 본문이 없다")
        return err, warn
    if not meta.get("태그"):
        warn.append("`태그:` 가 없다 — 검색어 5~10개(지역+업종+대상)")
    t = len(meta.get("제목", ""))
    if t and not 15 <= t <= 40:
        warn.append(f"제목 {t}자 — 15~40자가 검색 결과에서 잘리지 않는다")
    ban, must = read_rules(rules)
    for pat, why in BAN + ban:
        for m in re.finditer(pat, body):
            err.append(f"금지 «{m[0]}» — {why}")
    for pat, why in SOFT:
        hits = sorted(set(re.findall(pat, plain(body))))
        if hits and (why.startswith("빈약") is False or len(re.findall(pat, plain(body))) >= 3):
            warn.append(f"{'·'.join(hits)} — {why}")
    for w in must:
        if w not in body:
            err.append(f"필수 문구 없음: «{w}» (업체설정)")
    bs = blocks(body)
    heads = [s for s, ls in bs if ls[0].startswith("## ")]
    if len(heads) < 3:
        warn.append(f"소제목(##) {len(heads)}개 — 3개 이상이면 훑어 읽기 쉽다")
    if story and not any(h.startswith(("참고", "출처")) for h in heads):
        err.append("이야기 글인데 «## 참고» 절이 없다 — 연도·숫자·인용의 출처 URL 을 적는다")
    refs = [int(n) for n in re.findall(r"^\[사진 (\d+)\]$", body, re.M)]
    for n in refs:
        if n > len(photos):
            err.append(f"[사진 {n}] 인데 사진.json 에 {len(photos)}장뿐")
    for p in photos:
        if not os.path.exists(os.path.join(folder, p.get("src", p.get("file", "")))):
            err.append(f"사진 원본 없음: {p.get('src')}")
    if len(refs) < 3:
        warn.append(f"사진 {len(refs)}장 — 사진-글-사진 리듬에는 4장 이상")
    ai = [p for p in photos if re.search(r"(^|[_\-\s])AI", p.get("file", "") + p.get("src", ""))]
    if len(ai) > 1:
        warn.append(f"AI 사진 {len(ai)}장 — 실사진이 검색 점수에 유리, AI 는 1장까지(네이버 «AI 활용» 표시 켜기)")
    ends, bare, prev_end, run = [], 0, None, 0
    for sec, ls in bs:
        ls = [l for l in ls if not l.startswith("## ")]  # 소제목 바로 아래 줄은 본문으로 검사
        if not ls or ls[0].startswith((">> ", "> ", "|", "[사진", "[구분선")):
            continue
        listy = all(re.match(r"(\d+\.|[-·]|.+ : )", plain(l)) for l in ls)
        for l in ls:
            w = width(l, story)
            if w > maxw and not listy and not l.startswith("Q. ") and not sec.startswith(LEFT_SECTIONS):
                warn.append(f"줄 {w}자(>{maxw}) [{sec}] {plain(l)[:30]}")
        n = len(ls) - (1 if ls[0].startswith("Q. ") else 0)
        if n > maxp and not listy:
            warn.append(f"문단 {n}줄(>{maxp}) [{sec}] {plain(ls[0])[:20]}…")
        if not story and not listy and not ls[0].startswith("Q. ") and not sec.startswith(LEFT_SECTIONS) and not re.search(r"\{|\*\*|^> ", "\n".join(ls)):
            bare += 1
        last = plain(ls[-1]).rstrip(".!? ")
        end = "요" if last.endswith("요") else ("다" if last.endswith("다") else "")
        ends.append(end)
        run = run + 1 if end and end == prev_end else 1
        prev_end = end
        if run == 4 and not story:
            warn.append(f"같은 끝맺음 «~{end}» 4문단 연속 [{sec}] — «~요»·«~습니다» 섞기")
    if bare:
        warn.append(f"강조(색·굵게·상자) 없는 문단 {bare}개 — 문단마다 하나씩")
    if story and ends:
        yo = ends.count("요") / len(ends)
        if yo > 0.2:
            warn.append(f"«~요» 끝 {yo:.0%} — 이야기 글은 합쇼체(~습니다), «요»는 첫·끝 인사만")
    if re.search(r"!\s*$", body, re.M) and story:
        warn.append("느낌표 — 이야기 글은 차분한 해설")
    return err, warn


def render(text, photos):
    meta = head_meta(text)
    story = meta.get("종류") == "이야기"
    left_all = meta.get("정렬") == "왼쪽"
    body = text.split("\n---\n", 1)[1]
    parts = []
    for sec, ls in blocks(body):
        one = ls[0]
        left = left_all or sec.startswith(LEFT_SECTIONS)
        pst = P_L if left else P_C
        if one.startswith("## "):
            head = [l[3:] for l in ls if l.startswith("## ")]
            rest = [l for l in ls if not l.startswith("## ")]
            parts.append(f'<blockquote style="{FF}text-align:center;font-size:19px;color:#444;margin:0 auto;padding:16px 18px;border:3px solid #ddd;">'
                         + "<br>".join(inline(l) for l in head) + "</blockquote>")
            if rest:
                parts.append(f'<p style="{pst}">' + "<br>".join(inline(l) for l in rest) + "</p>")
        elif one.startswith(">> "):
            q = " ".join(l[3:] if l.startswith(">> ") else l for l in ls)
            parts.append(f'<blockquote style="{FF}text-align:center;font-size:19px;font-style:italic;line-height:1.9;color:#333;margin:0 auto;padding:18px 12px;border:0;">\u201c{inline(q)}\u201d</blockquote>')
        elif one.startswith("> "):
            parts.append(f'<blockquote style="{FF}text-align:center;font-size:17px;font-weight:bold;color:#333;margin:0 auto;padding:16px 18px;border:2px solid #b0238f;background:#fdf6fb;">'
                         + "<br>".join(inline(l[2:] if l.startswith("> ") else l) for l in ls) + "</blockquote>")
        elif all(l.startswith("|") for l in ls):
            rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in ls if not re.fullmatch(r"\|[\s:|-]+\|?", l)]
            td = "border:1px solid #ccc;padding:12px 14px;vertical-align:middle;" + FF + "font-size:15px;line-height:1.7;color:#333;text-align:left;"
            parts.append('<table style="border-collapse:collapse;width:100%;margin:0;">' + "".join(
                "<tr>" + "".join(f'<td style="{td}{"font-weight:bold;background:#f6f6f6;" if i == 0 else ""}">{inline(c)}</td>' for c in r) + "</tr>"
                for i, r in enumerate(rows)) + "</table>")
        elif one == "[구분선]":
            parts.append('<hr style="width:30%;margin:0 auto;border:0;border-top:1px solid #bbb;">')
        elif m := re.fullmatch(r"\[사진 (\d+)\]", one):
            n = int(m[1])
            f = photos[n - 1]["file"] if n <= len(photos) else "?"
            parts.append(f'<p style="text-align:center;font-size:14px;color:#2a6ebb;background:#eef4fb;padding:14px;margin:0;">▶ 사진 {n} 자리 — 올릴사진/{html.escape(f)}</p>')
        elif one.startswith("Q. "):
            parts.append(f'<p style="{pst}font-size:17px;font-weight:bold;color:#444;">{inline(one)}</p>')
            if len(ls) > 1:
                parts.append(f'<p style="{pst}">' + "<br>".join(inline(l) for l in ls[1:]) + "</p>")
        else:
            parts.append(f'<p style="{pst}">' + "<br>".join(inline(l) for l in ls) + "</p>")
    # 문단 사이 여백은 «빈 문단»으로 — 네이버는 margin 을 버리고 빈 문단만 남긴다. 큰 덩어리 앞뒤는 두 줄.
    gap = f'<p style="{P_C}">&nbsp;</p>'
    big = lambda x: x.startswith(("<blockquote", "<table", "<hr")) or "사진" in x[:200] and "자리 —" in x
    out = []
    for i, p in enumerate(parts):
        if i:
            out.append(gap * (2 if big(p) or big(parts[i - 1]) else 1))
        out.append(p)
    return meta, "\n".join(out)


def auto_center(im):
    """주인공 사물(배경 제거로 찾음)을 가운데 — 폭 85%, 16:9. rembg 가 없으면 None"""
    try:
        import numpy as np
        from rembg import remove
    except ImportError:
        return None
    W, H = im.size
    m = np.array(remove(im).getchannel("A")) > 128
    if not m.any():
        return None
    cols, rows = np.where(m.any(0))[0], np.where(m.any(1))[0]
    x0, x1, y0, y1 = int(cols.min()), int(cols.max()), int(rows.min()), int(rows.max())
    cx, cy, bw, bh = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    cw = max(bw / 0.85, bh / 0.8 * 16 / 9)
    ch = cw * 9 / 16
    k = min(1, 2 * min(cx, W - cx) / cw, 2 * min(cy, H - cy) / ch)
    cw, ch = cw * k, ch * k
    return [round(cx - cw / 2), round(cy - ch / 2), round(cx + cw / 2), round(cy + ch / 2)]


def make_photos(folder, photos):
    if not photos:
        return
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
    import math
    font_path = next((f for f in ("C:/Windows/Fonts/malgunbd.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                                  "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf") if os.path.exists(f)), None)
    dst = os.path.join(folder, "올릴사진")
    os.makedirs(dst, exist_ok=True)
    for ph in photos:
        im = ImageOps.exif_transpose(Image.open(os.path.join(folder, ph["src"]))).convert("RGB")
        for x0, y0, x1, y1 in ph.get("blur", []):  # 가격표·번호판·얼굴 가리기
            region = im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(28))
            mask = Image.new("L", region.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, region.width - 1, region.height - 1), fill=255)
            im.paste(region, (x0, y0), mask.filter(ImageFilter.GaussianBlur(max(1, min(region.size) // 6))))
        crop = ph.get("crop") or (auto_center(im) if ph.get("center") else None)
        if ph.get("center") and not crop:
            print(f"  ⚠ {ph['file']}: center 는 rembg 가 필요(pip install rembg) — 원본 그대로")
        cx, cy = (crop[0], crop[1]) if crop else (0, 0)
        if crop:
            im = im.crop(tuple(crop))
        scale = max(im.size) / 4000 * (4000 / max(im.size)) ** 0.5
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for lb in ph.get("labels", []):
            f = ImageFont.truetype(font_path, int(120 * scale)) if font_path else ImageFont.load_default()
            at = (lb["at"][0] - cx, lb["at"][1] - cy)
            to = (lb["to"][0] - cx, lb["to"][1] - cy) if lb.get("to") else None
            bx = d.textbbox((0, 0), lb["text"], font=f)
            w, h, pad = bx[2] - bx[0], bx[3] - bx[1], int(40 * scale)
            box = (at[0] - w / 2 - pad, at[1] - h / 2 - pad, at[0] + w / 2 + pad, at[1] + h / 2 + pad)
            red, lw = (230, 40, 50, 255), max(6, int(14 * scale))
            if to:
                sx, sy = min(max(to[0], box[0]), box[2]), min(max(to[1], box[1]), box[3])
                d.line([(sx, sy), to], fill=red, width=lw)
                ang = math.atan2(to[1] - sy, to[0] - sx)
                for a in (2.6, -2.6):
                    d.line([to, (to[0] + 60 * scale * math.cos(ang + a), to[1] + 60 * scale * math.sin(ang + a))], fill=red, width=lw)
            d.rectangle(box, fill=(255, 255, 255, 190), outline=red, width=lw)
            d.text((at[0] - w / 2 - bx[0], at[1] - h / 2 - bx[1]), lb["text"], font=f, fill=(40, 40, 40, 255))
        im = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
        im.thumbnail((2000, 2000))
        im.save(os.path.join(dst, ph["file"]), "JPEG", quality=90)


def page(meta, article, photos):
    e = lambda s: html.escape(s, quote=False)
    rows = "".join(f"<li>사진 {i} — 올릴사진/{e(p['file'])}</li>" for i, p in enumerate(photos, 1))
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow">
<title>{e(meta.get('제목', '블로그 원고'))}</title><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#f4f2ee;font-family:'Malgun Gothic',sans-serif;">
<div style="max-width:760px;margin:0 auto;padding:18px 16px 60px;">
<div style="background:#1c1a17;color:#fff;padding:16px 18px;font-size:15px;line-height:1.85;margin:0 0 18px;">
① 제목: <b id="t">{e(meta.get('제목', ''))}</b> <button data-copy="t">제목 복사</button><br>
② <button data-copy="post" style="font-weight:bold;padding:4px 12px;">본문 전체 복사</button> → 네이버 글쓰기 본문 클릭 → Ctrl+V<br>
③ 파란 «사진 자리» 줄 클릭 → 사진 버튼으로 그 번호 사진 올리기 → 파란 줄 지우기<br>
④ 소제목은 인용구로 붙습니다 — 인용구 클릭 → 도구막대 인용구 ▾ 에서 모양 고르기<br>
⑤ 글씨체가 나눔고딕이 아니면 본문 클릭 → Ctrl+A → 나눔고딕<br>
⑥ 태그: <span id="g">{e(meta.get('태그', ''))}</span> <button data-copy="g">태그 복사</button><br>
⑦ AI 로 만든 사진이 있으면 «AI 활용» 표시 켜기 · 발행은 직접(예약 발행 가능)
<ol style="margin:6px 0 0;">{rows}</ol></div>
<div id="post" style="background:#fff;padding:30px 24px;">
{article}
</div></div>
<script>
document.addEventListener('click', function (ev) {{
  var id = ev.target.getAttribute && ev.target.getAttribute('data-copy'); if (!id) return;
  var r = document.createRange(); r.selectNodeContents(document.getElementById(id));
  var s = getSelection(); s.removeAllRanges(); s.addRange(r);
  var ok = false; try {{ ok = document.execCommand('copy'); }} catch (x) {{}}
  ev.target.textContent = ok ? '복사됨' : 'Ctrl+C 누르기';
}});
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser(description="네이버 블로그 원고 검사 + 복사용 페이지")
    ap.add_argument("folder")
    ap.add_argument("--rules", help="업체설정.md (금지어·필수 문구)")
    ap.add_argument("--check", action="store_true", help="검사만")
    a = ap.parse_args()
    folder = a.folder
    src = os.path.join(folder, "글.md")
    if not os.path.exists(src):
        print(f"글.md 가 없다: {src}")
        return 1
    text = open(src, encoding="utf-8").read().replace("\r\n", "\n")
    pj = next((os.path.join(folder, n) for n in ("사진.json", "표시.json") if os.path.exists(os.path.join(folder, n))), None)
    photos = json.load(open(pj, encoding="utf-8")) if pj else []
    meta = head_meta(text)
    err, warn = lint(text, meta, photos, folder, a.rules)
    for w in warn:
        print("  ⚠ " + w)
    for x in err:
        print("  ✗ " + x)
    if err:
        print(f"→ ✗ {len(err)}개 — 고친 뒤 다시. 복사용 페이지를 만들지 않았다.")
        return 2
    if a.check:
        print(f"→ 검사 통과(⚠ {len(warn)})")
        return 0
    meta, article = render(text, photos)
    make_photos(folder, photos)
    out = os.path.join(folder, "복사용.html")
    open(out, "w", encoding="utf-8").write(page(meta, article, photos))
    print(f"→ 만듦: {out} (사진 {len(photos)}장, ⚠ {len(warn)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
