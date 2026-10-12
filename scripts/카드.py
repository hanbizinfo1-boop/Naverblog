"""정보 카드 이미지 — 카드 종류 4 × 디자인 3 × 내용 테마 (docs/구조틀_4종.md 8-0)

    python scripts/카드.py <카드.json> [<카드.json> …]

카드.json 하나에 카드 하나. 결과 PNG 는 "out" 경로(카드.json 기준 상대경로)에 저장된다.
글 폴더의 `원본/` 에 저장하고, 사진.json 의 src 로 그대로 쓴다.

## 자동으로 정해지는 두 가지 (카드.json 에 적으면 그 값을 쓴다)

1. "theme" — 카드에 적힌 글을 읽고 내용에 맞는 색 테마를 고른다 (THEMES · KEYWORDS)
2. "style" — 디자인 A·B·C 중, 같은 type 이 최근에 쓴 디자인을 피해서 고른다
3. "layout" — 글자 배치 1·2·3 중, 같은 type 이 최근에 쓴 배치를 피해서 고른다
   기록: 출력/카드기록.json (폴더 · type · style · layout · theme)

배치 (글자 위치·구조)
| type | 1 | 2 | 3 |
|---|---|---|---|
| 반전 | 왼쪽 위부터 쌓기 | 가운데 정렬·세로 가운데 | 위(통념)·아래(결론, 오른쪽 정렬) 나눔 |
| 요약 | 숫자 먼저 → 표 | 표 먼저 → 숫자가 결론 상자 | 숫자가 주인공(크게) → 표는 2~3열로 작게 |
| 타임라인 | A 왼쪽 줄 / B 꽉 찬 카드 / C 사진 머리 | A 지그재그 / B 좌우 엇갈림 / C 사진 왼쪽 띠 | A 큰 번호 열 / B 2열 격자 / C 둥근 사진 |
| 비교 | 좌우 칸·분할·카드 나란히 | 항목마다 위아래 / 위아래 색 분할 / 카드 위아래 | A 묶음→B 묶음 / 왼쪽 항목 띠 / 왼쪽 색 막대 |

| type | 틀 | A | B | C |
|---|---|---|---|---|
| 반전   | 1 | 짙은 바탕 · 취소선 · 테두리 도장 | 사진 배경(어둡게) · 가운데 · 빨간 알약 | 줄노트 종이 · 마커 취소선 · 기울어진 도장 |
| 요약   | 2 | 흰 바탕 · 색 머리 · 줄무늬 표 | 그라데이션 포스터 · 반투명 칩 2열 | 영수증 · 점선 · 톱니 가장자리 |
| 타임라인 | 3 | 종이 바탕 · 명조 · 세로 줄 | 연한 그라데이션 · 흰 카드 쌓기 · 번호 배지 | 사진 머리 + 다이어리 줄 |
| 비교   | 4 | 흰 바탕 · 두 칸 표 | 좌우 색 분할 · 가운데 VS | 떠 있는 카드 두 장 · «같은 점» 띠 |

"photo" 가 필요한 디자인(반전 B · 타임라인 C)은 카드.json 기준 상대경로로 사진을 준다.
그 글 본문에 따로 쓰지 않은 사진을 쓴다 (같은 사진 반복 방지). 없으면 그 디자인은 건너뛴다.

카드의 숫자·조건은 **공고 원문 그대로**만 쓴다. 사례 카드(타임라인)는 글 속 사례와 같은 내용만.
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
WIN = Path("C:/Windows/Fonts")
USER = Path.home() / "AppData/Local/Microsoft/Windows/Fonts"
BRAND = "한국중소기업비즈니스센터"
SYMBOL = ROOT / "assets/브랜드/한비즈-심볼.png"
LOG = ROOT / "출력/카드기록.json"

# ── 내용 테마 ───────────────────────────────────────────────────
# deep: 짙은 바탕 · g1→g2: 그라데이션 · accent: 강조 · ink: 글자 · paper: 밝은 바탕 · tint: 아주 연한 바탕
THEMES = {
    "금리": dict(deep="#14213d", g1="#1d4ed8", g2="#0b2a4a", accent="#ffd166", ink="#15328a", paper="#f5f8ff", tint="#e6eefc"),
    "가게": dict(deep="#3b1d12", g1="#c2410c", g2="#7c2d12", accent="#fbbf24", ink="#7c2d12", paper="#fbf3e6", tint="#fde7d3"),
    "제조": dict(deep="#2b2118", g1="#8a5a34", g2="#3e2c20", accent="#e0a458", ink="#5b3a22", paper="#f7f1e8", tint="#efe2cf"),
    "복지": dict(deep="#16352d", g1="#2f7d68", g2="#1f4d42", accent="#f2c14e", ink="#1f5a4a", paper="#f2f8f4", tint="#dcefe5"),
    "재기": dict(deep="#2a1145", g1="#f97316", g2="#7c3aed", accent="#fde68a", ink="#6d28d9", paper="#fff7ed", tint="#fde4cf"),
    "주의": dict(deep="#1d1d1f", g1="#7f1d1d", g2="#1d1d1f", accent="#f87171", ink="#991b1b", paper="#fbf8f1", tint="#fde2e2"),
    "기본": dict(deep="#0f2d2a", g1="#0f766e", g2="#0b2a4a", accent="#ffd166", ink="#0f5f58", paper="#f3faf8", tint="#dff2ee"),
}
KEYWORDS = [  # 앞에 있을수록 같은 점수일 때 우선
    ("재기", r"재도전|재창업|폐업|다시 연|다시 시작|재기"),
    ("복지", r"장애인|복지|국가유공자"),
    ("주의", r"제한|체납|연체|막히|못 받|안 된다|세 번|3회"),
    ("제조", r"제조|공방|설비|시설자금|소공인|기계"),
    ("가게", r"반찬|식당|국수|가게|마트|홈플러스|카페|미용실|백반"),
    ("금리", r"금리|이자|우대|분기"),
]
STYLE_ORDER = {"반전": "ABC", "요약": "ABC", "타임라인": "ABC", "비교": "ABC"}
PHOTO_STYLES = {("반전", "B"), ("타임라인", "C")}


def pick_theme(c):
    """제목(title·myth·a·b)을 먼저 읽는다. 표 속 숫자(%)가 테마를 가져가지 않게."""
    head = " ".join(str(c.get(k, "")) for k in ("title", "myth", "a", "b"))
    body = json.dumps(c, ensure_ascii=False)
    for text in (head, body):
        scores = [(len(re.findall(pat, text)), -i, name) for i, (name, pat) in enumerate(KEYWORDS)]
        best = max(scores)
        if best[0] > 0:
            return best[2]
    return "기본"


def load_log():
    try:
        return json.loads(LOG.read_text(encoding="utf-8"))
    except Exception:
        return []


def pick_style(c, folder, log):
    """같은 type 의 최근 기록 3개에 없는 디자인 → 사진이 필요한데 없으면 건너뜀"""
    recent = [r["style"] for r in log if r["type"] == c["type"] and r["folder"] != folder][-3:]
    for st in STYLE_ORDER[c["type"]]:
        if (c["type"], st) in PHOTO_STYLES and not c.get("photo"):
            continue
        if st not in recent:
            return st
    # 다 썼으면 가장 오래전에 쓴 것
    for st in recent:
        if not ((c["type"], st) in PHOTO_STYLES and not c.get("photo")):
            return st
    return "A"


# ── 글꼴 · 글자 ─────────────────────────────────────────────────
def font(name, size, weight=None):
    for d in (USER, WIN):
        p = d / name
        if p.exists():
            f = ImageFont.truetype(str(p), size)
            if weight is not None:
                try:
                    f.set_variation_by_axes([weight])
                except Exception:
                    pass
            return f
    return ImageFont.truetype(str(WIN / "malgun.ttf"), size)


def wrap(draw, text, f, width):
    """글자 단위 줄바꿈 (한국어). 명시적 줄바꿈 \\n 존중."""
    out = []
    for para in str(text).split("\n"):
        line = ""
        for ch in para:
            if draw.textlength(line + ch, font=f) <= width:
                line += ch
            else:
                cut = line.rfind(" ")
                if cut > 0:
                    out.append(line[:cut])
                    line = line[cut + 1:] + ch
                else:
                    out.append(line)
                    line = ch
        out.append(line)
    return out


def text_block(draw, xy, text, f, fill, width, gap=1.45):
    x, y = xy
    for ln in wrap(draw, text, f, width):
        draw.text((x, y), ln, font=f, fill=fill)
        y += int(f.size * gap)
    return y


def centered(d, y, text, f, fill, W):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill)
    return w


# ── 배경 · 판 ───────────────────────────────────────────────────
def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient(W, H, c1, c2, diagonal=True):
    a, b = hexrgb(c1), hexrgb(c2)
    small = Image.new("RGB", (64, 64))
    px = small.load()
    for y in range(64):
        for x in range(64):
            t = (x / 63 * 0.45 + y / 63 * 0.55) if diagonal else y / 63
            px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return small.resize((W, H), Image.BICUBIC)


def paper(W, H, base, grain=10):
    im = Image.new("RGB", (W, H), base)
    noise = Image.effect_noise((W, H), grain).convert("RGB")
    return Image.blend(im, noise, 0.05)


def photo_bg(path, W, H, blur=6, dark=0.5):
    ph = ImageOps.fit(Image.open(path).convert("RGB"), (W, H), Image.LANCZOS)
    ph = ph.filter(ImageFilter.GaussianBlur(blur))
    return Image.blend(ph, Image.new("RGB", (W, H), "#000000"), dark)


def panel(im, box, radius=28, fill=(255, 255, 255, 255), shadow=60):
    """그림자 진 둥근 판 (im 을 제자리에서 바꾼다)"""
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(lay).rounded_rectangle((x0, y0 + 14, x1, y1 + 14), radius=radius, fill=(0, 0, 0, shadow))
    lay = lay.filter(ImageFilter.GaussianBlur(18))
    ImageDraw.Draw(lay).rounded_rectangle(box, radius=radius, fill=fill)
    im.paste(Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB"))


def footer(im, color, dark=False, size=26, right=None, bottom=None):
    """오른쪽 아래 «심볼 + 상호». 심볼은 그림 부분만 잘라 글자 높이에 맞추고 세로 중심을 맞춘다."""
    d = ImageDraw.Draw(im)
    f = font("malgunbd.ttf", size)
    W, H = im.size
    bx = d.textbbox((0, 0), BRAND, font=f)
    tw, th = bx[2] - bx[0], bx[3] - bx[1]
    right = W - 56 if right is None else right
    bottom = H - 52 if bottom is None else bottom
    tx, ty = right - tw - bx[0], bottom - th - bx[1]
    cy = bottom - th / 2
    if SYMBOL.exists():
        s = Image.open(SYMBOL).convert("RGBA")
        px = s.load()
        for yy in range(s.height):
            for xx in range(s.width):
                r, g, b, a = px[xx, yy]
                if r > 235 and g > 235 and b > 235:
                    px[xx, yy] = (r, g, b, 0)
        s = s.crop(s.getbbox())
        sh = round(th * 1.25)
        s = s.resize((round(s.width * sh / s.height), sh), Image.LANCZOS)
        if dark:
            a = s.split()[3]
            s = Image.merge("RGBA", (a.point(lambda _: 255),) * 3 + (a,))
        gap = round(size * 0.45)
        im.paste(s, (round(right - tw - gap - s.width), round(cy - s.height / 2)), s)
    d.text((tx, ty), BRAND, font=f, fill=color)


# ── 배치 도우미 ─────────────────────────────────────────────────
def put_lines(d, lines, f, fill, x, y, width, align="left", gap=1.45):
    """줄 목록을 정렬해 쓴다. 다음 y 를 돌려준다."""
    h = int(f.size * gap)
    for ln in lines:
        w = d.textlength(ln, font=f)
        xx = x if align == "left" else (x + (width - w) / 2 if align == "center" else x + width - w)
        d.text((xx, y), ln, font=f, fill=fill)
        y += h
    return y


def line_h(f, gap=1.45):
    return int(f.size * gap)


def scratch():
    return ImageDraw.Draw(Image.new("RGB", (10, 10)))


def two_pass(render, W, min_h=1080, max_h=3000):
    """render(im, measure) → 내용 끝 y. 먼저 큰 판에 그려 높이를 재고, 맞는 크기로 다시 그린다."""
    end = render(Image.new("RGB", (W, max_h)), True)
    H = max(min_h, int(end))
    im = Image.new("RGB", (W, H))
    render(im, False)
    return im


# ══ 반전 (틀 1) ═════════════════════════════════════════════════
# 디자인: A 짙은 바탕 · B 사진 배경 · C 줄노트
# 배치: 1 왼쪽 위부터 쌓기 · 2 가운데 정렬 세로 가운데 · 3 위(통념)·아래(결론) 나눔, 결론은 오른쪽 정렬
def stamp_img(style, text):
    d = scratch()
    if style == "A":
        f = font("GmarketSansBold.otf", 116)
        w = int(d.textlength(text, font=f))
        st = Image.new("RGBA", (w + 64, 172), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        sd.rounded_rectangle((4, 4, w + 60, 168), radius=18, outline="#e3262e", width=8)
        sd.text((32, 16), text, font=f, fill="#e3262e")
        return st
    if style == "B":
        f = font("GmarketSansBold.otf", 96)
        w = int(d.textlength(text, font=f))
        st = Image.new("RGBA", (w + 140, 150), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        sd.rounded_rectangle((0, 0, w + 140, 150), radius=75, fill="#e3262e")
        sd.text((70, 18), text, font=f, fill="#ffffff")
        return st
    f = font("Hancom Gothic Bold.ttf", 104)
    w = int(d.textlength(text, font=f))
    st = Image.new("RGBA", (w + 120, 210), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    ink = (200, 16, 46, 225)
    sd.rounded_rectangle((6, 6, w + 114, 204), radius=26, outline=ink, width=9)
    sd.rounded_rectangle((22, 22, w + 98, 188), radius=18, outline=ink, width=3)
    sd.text((60, 38), text, font=f, fill=ink)
    return st.rotate(8, expand=True, resample=Image.BICUBIC)


def card_반전(c, base, T, style, L):
    W = H = 1080
    if style == "A":
        im = Image.new("RGB", (W, H), T["deep"])
        lf, lc = font("GmarketSansMedium.otf", 34), "#9a9aa0"
        mf, mc = font("GmarketSansBold.otf", 64), "#8d8d93"
        tf, tc = font("GmarketSansMedium.otf", 46), "#ffffff"
        M, fc, dark = 80, "#c9c9cf", True
    elif style == "B":
        im = photo_bg(base / c["photo"], W, H, blur=5, dark=0.58)
        lf, lc = font("GmarketSansMedium.otf", 32), T["accent"]
        mf, mc = font("GmarketSansBold.otf", 66), "#eeeeee"
        tf, tc = font("GmarketSansMedium.otf", 42), "#ffffff"
        M, fc, dark = 90, "#e6e6e6", True
    else:
        im = paper(W, H, T["paper"])
        g = ImageDraw.Draw(im)
        for y in range(150, H - 90, 74):
            g.line((0, y, W, y), fill=T["tint"], width=2)
        g.line((118, 0, 118, H), fill="#efb3b3", width=3)
        lf, lc = font("NotoSerifKR-VF.ttf", 34, weight=600), "#7a7f8a"
        mf, mc = font("NotoSerifKR-VF.ttf", 60, weight=800), "#3a3d44"
        tf, tc = font("NotoSansKR-VF.ttf", 42, weight=600), "#1f2329"
        M, fc, dark = 150, "#8a8f99", False
    d = ImageDraw.Draw(im)
    width = W - M - 80
    label = c.get("label", "많이들 이렇게 생각하세요")
    myth = wrap(d, c["myth"], mf, width)
    truth = wrap(d, c["truth"], tf, width - (40 if L == 3 else 0))
    st = stamp_img(style, c.get("stamp", "아닙니다"))
    mh = line_h(mf, 1.5 if style != "C" else 1.9)
    th = line_h(tf, 1.6)
    top_h = 60 + 30 + mh * len(myth)
    bot_h = st.height + 40 + th * len(truth)
    align = {1: "left", 2: "center", 3: "left"}[L]
    if L == 2:
        y0 = (H - (top_h + 50 + bot_h)) / 2 - 10
    else:
        y0 = 100
    strikes = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(strikes)
    # 라벨
    lw = d.textlength(label, font=lf)
    lx = M if align == "left" else (W - lw) / 2
    if style == "B":
        if align == "left":
            lx += 26
        d.rounded_rectangle((lx - 26, y0 - 12, lx + lw + 26, y0 + 52), radius=32, outline=lc, width=3)
    d.text((lx, y0), label, font=lf, fill=lc)
    # 통념 + 취소선
    y = y0 + 90
    for ln in myth:
        w = d.textlength(ln, font=mf)
        x = M if align == "left" else (W - w) / 2
        d.text((x, y), ln, font=mf, fill=mc)
        if style == "A":
            sd.line((x - 4, y + mf.size * 0.58, x + w + 4, y + mf.size * 0.58), fill=(209, 0, 0, 255), width=7)
        elif style == "B":
            sd.rectangle((x - 10, y + mf.size * 0.47, x + w + 10, y + mf.size * 0.7), fill=(226, 38, 46, 215))
        else:
            sd.line((x - 10, y + mf.size * 0.9, x + w + 10, y + mf.size * 0.5), fill=(214, 30, 40, 190), width=16)
        y += mh
    im.paste(Image.alpha_composite(im.convert("RGBA"), strikes).convert("RGB"))
    d = ImageDraw.Draw(im)
    # 도장 + 사실
    if L == 3:
        yb = H - 110 - bot_h
        d.line((M, yb - 40, W - 80, yb - 40), fill=(lc if style != "C" else "#c9ccd2"), width=2)
        im.paste(st, (int(W - 80 - st.width), int(yb)), st)
        d = ImageDraw.Draw(im)
        put_lines(d, truth, tf, tc, M, yb + st.height + 40, width, "right", 1.6)
    else:
        yb = y + 50
        sx = M if align == "left" else (W - st.width) / 2
        if style == "C" and align == "left":
            sx = W - st.width - 110
        im.paste(st, (int(sx), int(yb)), st)
        d = ImageDraw.Draw(im)
        put_lines(d, truth, tf, tc, M, yb + st.height + 40, width, align, 1.6)
    footer(im, fc, dark=dark)
    return im


# ══ 요약 (틀 2) ═════════════════════════════════════════════════
# 디자인: A 흰 바탕+색 머리 · B 그라데이션 포스터 · C 영수증
# 배치: 1 숫자 먼저→표 · 2 표 먼저→숫자가 결론 · 3 숫자가 주인공(크게 가운데)+표는 아래 작게
def card_요약(c, base, T, style, L):
    W = 1080
    rows = c["rows"]
    hi = set(c.get("hi", []))

    def render(im, measure, bg=True):
        H = im.height
        # 배경
        if not bg:
            pass
        elif style == "A":
            im.paste(Image.new("RGB", im.size, "#ffffff"))
        elif style == "B":
            im.paste(gradient(W, H, T["g1"], T["g2"]))
            g = ImageDraw.Draw(im, "RGBA")
            for r, a in ((520, 30), (380, 24)):
                g.ellipse((W - r - 40, -r // 2, W + r - 40, r + r // 2), outline=(255, 255, 255, a), width=3)
        else:
            im.paste(paper(W, H, T["tint"], grain=14))
        d = ImageDraw.Draw(im, "RGBA")
        ink = {"A": T["ink"], "B": "#ffffff", "C": "#111111"}[style]
        sub_c = {"A": "#666666", "B": "#e8eef8", "C": "#666666"}[style]
        M = 80 if style != "C" else 230
        RW = W - 2 * M
        y = 90 if style != "C" else 170

        def title_block(y, small=False):
            if small:
                f = font("Pretendard-Bold.otf", 34)
                t = c["title"].replace("\n", " · ")
                if style == "A":
                    d.rounded_rectangle((M, y, M + d.textlength(t, font=f) + 44, y + 64), radius=32, fill=T["ink"])
                    d.text((M + 22, y + 12), t, font=f, fill="#ffffff")
                else:
                    centered(d, y + 12, t, f, ink if style == "C" else T["accent"], W)
                return y + 100
            if style == "A":
                f = font("Pretendard-Bold.otf", 58)
                lines = c["title"].split("\n")
                band = 80 + len(lines) * 76 + (50 if c.get("sub") else 0)
                d.rectangle((0, 0, W, band), fill=T["ink"])
                yy = put_lines(d, lines, f, "#ffffff", M, 70, RW, "left", 1.3)
                if c.get("sub"):
                    d.text((M + 2, yy + 4), c["sub"], font=font("malgun.ttf", 32), fill="#dfe6f5")
                return band + 60
            if style == "B":
                f = font("GmarketSansBold.otf", 56)
                yy = put_lines(d, c["title"].split("\n"), f, "#ffffff", M, y, RW, "left", 1.3)
                if c.get("sub"):
                    d.text((M + 2, yy + 8), c["sub"], font=font("GmarketSansLight.otf", 32), fill=sub_c)
                    yy += 50
                return yy + 50
            f = font("NotoSansKR-VF.ttf", 50, weight=800)
            yy = put_lines(d, c["title"].split("\n"), f, ink, 0, y, W, "center", 1.3)
            if c.get("sub"):
                centered(d, yy + 4, c["sub"], font("NotoSansKR-VF.ttf", 28, weight=400), sub_c, W)
                yy += 46
            return yy + 30

        def hero_block(y, big=False, boxed=False):
            size = (104 if style == "C" else 150) if big else (78 if style == "C" else 108)
            f = font("NotoSansKR-VF.ttf", size, weight=900) if style == "C" else font("Pretendard-Bold.otf", size) if style == "A" else font("GmarketSansBold.otf", size)
            col = {"A": T["ink"], "B": "#ffffff", "C": T["ink"]}[style]
            if boxed:
                bh = size + 120
                if style == "A":
                    d.rounded_rectangle((M - 20, y, W - M + 20, y + bh), radius=28, fill=T["tint"])
                elif style == "B":
                    d.rounded_rectangle((M - 20, y, W - M + 20, y + bh), radius=28, fill=(255, 255, 255, 40))
                else:
                    d.rectangle((M, y, W - M, y + bh), outline="#111111", width=3)
                centered(d, y + 18, "그래서 결론은", font("Pretendard-Bold.otf", 30), sub_c if style != "B" else T["accent"], W)
                centered(d, y + 62, c["big"], f, col, W)
                y += bh + 20
            else:
                if style == "A" and not big:
                    d.text((M, y), c["big"], font=f, fill=col)
                else:
                    centered(d, y, c["big"], f, col, W)
                y += int(size * 1.25)
            if c.get("big_note"):
                nf = font("malgun.ttf", 32) if style == "A" else font("GmarketSansMedium.otf", 32) if style == "B" else font("NotoSansKR-VF.ttf", 28, weight=500)
                nc = {"A": "#555555", "B": T["accent"], "C": "#444444"}[style]
                if style == "A" and not big and not boxed:
                    d.text((M + 4, y - 6), c["big_note"], font=nf, fill=nc)
                else:
                    centered(d, y - 6, c["big_note"], nf, nc, W)
                y += 60
            return y + 30

        def rows_block(y, compact=False):
            if style == "A":
                nf, vf = font("malgunbd.ttf", 34 if compact else 38), font("Pretendard-Bold.otf", 38 if compact else 44)
                rh = 118 if compact else 104
                if compact:  # 2열 목록
                    cw = (RW - 30) // 2
                    for i, (k, v) in enumerate(rows):
                        x, yy = M + (i % 2) * (cw + 30), y + (i // 2) * rh
                        d.line((x, yy + rh - 8, x + cw, yy + rh - 8), fill="#e3e6ee", width=2)
                        d.text((x, yy + 8), k, font=font("malgun.ttf", 28), fill="#666666")
                        d.text((x, yy + 50), v, font=vf, fill="#d10000" if i in hi else T["ink"])
                    return y + ((len(rows) + 1) // 2) * rh + 30
                for i, (k, v) in enumerate(rows):
                    if i % 2 == 0:
                        d.rectangle((M - 30, y, W - M + 30, y + rh), fill=T["tint"])
                    d.text((M, y + (rh - 40) // 2), k, font=nf, fill="#222222")
                    vw = d.textlength(v, font=vf)
                    d.text((W - M - vw, y + (rh - 46) // 2), v, font=vf, fill="#d10000" if i in hi else T["ink"])
                    y += rh
                return y + 30
            if style == "B":
                kf, vf = font("GmarketSansMedium.otf", 28 if compact else 30), font("GmarketSansBold.otf", 42 if compact else 50)
                cols = 3 if compact and len(rows) > 4 else 2
                gx, gy = 24, 24
                cw = (RW - gx * (cols - 1)) // cols
                kl_max = max(len(wrap(d, k, kf, cw - 44)) for k, _ in rows)   # 항목명 줄 수만큼 칸을 키운다
                ch = 24 + 36 * kl_max + 14 + vf.size + 26
                for i, (k, v) in enumerate(rows):
                    x, yy = M + (i % cols) * (cw + gx), y + (i // cols) * (ch + gy)
                    d.rounded_rectangle((x, yy, x + cw, yy + ch), radius=24, fill=(255, 255, 255, 36), outline=(255, 255, 255, 80), width=2)
                    for j, kl in enumerate(wrap(d, k, kf, cw - 44)):
                        d.text((x + 22, yy + 20 + j * 36), kl, font=kf, fill="#eef3fb")
                    d.text((x + 22, yy + ch - vf.size - 26), v, font=vf, fill=T["accent"] if i in hi else "#ffffff")
                return y + ((len(rows) + cols - 1) // cols) * (ch + gy) + 20
            kf, vf = font("NotoSansKR-VF.ttf", 32, weight=500), font("NotoSansKR-VF.ttf", 34, weight=800)
            for x in range(M + 20, W - M - 20, 22):
                d.line((x, y, x + 11, y), fill="#9a9a9a", width=3)
            y += 34
            for i, (k, v) in enumerate(rows):
                kw, vw = d.textlength(k, font=kf), d.textlength(v, font=vf)
                d.text((M + 30, y), k, font=kf, fill="#222222")
                d.text((W - M - 30 - vw, y - 2), v, font=vf, fill="#c8102e" if i in hi else "#111111")
                for x in range(int(M + 40 + kw), int(W - M - 40 - vw), 14):
                    d.ellipse((x, y + 24, x + 4, y + 28), fill="#b0b0b0")
                y += 80
            for x in range(M + 20, W - M - 20, 22):
                d.line((x, y + 4, x + 11, y + 4), fill="#9a9a9a", width=3)
            return y + 40

        def note_block(y):
            if not c.get("note"):
                return y
            nf = font("malgun.ttf", 28) if style == "A" else font("GmarketSansLight.otf", 28) if style == "B" else font("NotoSansKR-VF.ttf", 26, weight=400)
            nc = {"A": "#777777", "B": "#e8eef8", "C": "#666666"}[style]
            return put_lines(d, wrap(d, c["note"], nf, RW), nf, nc, M, y, RW, "center" if style == "C" else "left", 1.5) + 20

        if L == 1:
            y = title_block(y); y = hero_block(y); y = rows_block(y); y = note_block(y)
        elif L == 2:
            y = title_block(y); y = rows_block(y); y = hero_block(y + 10, boxed=True); y = note_block(y)
        else:
            y = title_block(y, small=True); y = hero_block(y + 40, big=True); y = rows_block(y + 10, compact=True); y = note_block(y)
        end = y + (120 if style != "C" else 150)
        if not measure:
            footer(im, {"A": "#8a93ad", "B": "#eef3fb", "C": "#6f6a60"}[style], dark=style == "B")
        return end

    if style != "C":
        return two_pass(render, W)

    # 영수증: 내용 높이를 재고 → 종이를 깔고 → 내용을 다시 그린다
    end = render(Image.new("RGB", (W, 3000)), True)
    H = max(1350, int(end) + 40)
    py0, ph = 110, int(end) - 110 - 40
    im = paper(W, H, T["tint"], grain=14)
    pw, px0 = W - 2 * 200, 200
    rc = Image.new("RGBA", (pw, ph), (255, 255, 255, 255))
    md = Image.new("L", (pw, ph), 255)
    mdd = ImageDraw.Draw(md)
    for x in range(0, pw, 28):
        mdd.polygon([(x, 0), (x + 14, 14), (x + 28, 0)], fill=0)
        mdd.polygon([(x, ph), (x + 14, ph - 14), (x + 28, ph)], fill=0)
    rc.putalpha(md)
    if L == 3:  # 배치 3: 영수증을 살짝 기울인다
        rc = rc.rotate(-2.2, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 70), (px0 + 8, py0 + 18, px0 + pw + 8, py0 + ph + 18))
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    canvas = Image.alpha_composite(im.convert("RGBA"), sh)
    canvas.paste(rc, (px0 - (rc.width - pw) // 2, py0 - (rc.height - ph) // 2), rc)
    im = canvas.convert("RGB")
    render(im, True, bg=False)   # 종이 위에 내용만
    footer(im, "#6f6a60")
    return im


# ══ 타임라인 (틀 3) ═════════════════════════════════════════════
# 디자인: A 종이·명조 · B 흰 카드 · C 사진
# 배치 A: 1 왼쪽 세로줄 · 2 가운데 줄 지그재그 · 3 큰 번호 열
# 배치 B: 1 꽉 찬 카드 쌓기 · 2 좌우 엇갈림 · 3 2열 격자
# 배치 C: 1 사진 머리(제목 겹침) · 2 사진 왼쪽 띠 · 3 둥근 사진 + 가운데 제목
def card_타임라인(c, base, T, style, L):
    W = 1080
    steps = c["steps"]
    n = len(steps)

    if style == "A":
        def render(im, measure):
            im.paste(paper(W, im.height, T["paper"], grain=8))
            d = ImageDraw.Draw(im)
            tb = font("NotoSerifKR-VF.ttf", 54, weight=800)
            sf = font("NotoSerifKR-VF.ttf", 34, weight=400)
            wf = font("NotoSerifKR-VF.ttf", 31, weight=700)
            align = "center" if L == 2 else "left"
            y = put_lines(d, c["title"].split("\n"), tb, T["ink"], 90, 100, W - 180, align, 1.35)
            if L == 2:
                d.line((W / 2 - 80, y + 18, W / 2 + 80, y + 18), fill=T["g1"], width=4)
            else:
                d.line((90, y + 18, 250, y + 18), fill=T["g1"], width=4)
            y += 90
            if L == 1:
                xl = 150
                tops = []
                for when, what in steps:
                    tops.append(y)
                    y = max(y + 52 + line_h(sf, 1.5) * len(wrap(d, what, sf, W - xl - 140)), y + 140) + 40
                d.line((xl, tops[0] + 26, xl, tops[-1] + 26), fill=T["tint"], width=5)
                for i, ((when, what), ty) in enumerate(zip(steps, tops)):
                    last = i == n - 1
                    r = 24 if last else 18
                    d.ellipse((xl - r, ty + 26 - r, xl + r, ty + 26 + r), fill=T["g1"] if last else T["ink"])
                    d.text((xl + 50, ty), when, font=wf, fill=T["g1"] if last else "#8a6a4a")
                    put_lines(d, wrap(d, what, sf, W - xl - 140), sf, "#2b2118", xl + 50, ty + 52, W - xl - 140)
            elif L == 2:
                cx = W / 2
                tops = []
                for when, what in steps:
                    tops.append(y)
                    y = max(y + 52 + line_h(sf, 1.45) * len(wrap(d, what, sf, 380)), y + 150) + 30
                d.line((cx, tops[0] + 20, cx, tops[-1] + 20), fill=T["tint"], width=5)
                for i, ((when, what), ty) in enumerate(zip(steps, tops)):
                    last = i == n - 1
                    r = 22 if last else 16
                    d.ellipse((cx - r, ty + 20 - r, cx + r, ty + 20 + r), fill=T["g1"] if last else T["ink"])
                    left = i % 2 == 0
                    x = cx - 50 - 380 if left else cx + 50
                    al = "right" if left else "left"
                    put_lines(d, [when], wf, T["g1"] if last else "#8a6a4a", x, ty, 380, al)
                    put_lines(d, wrap(d, what, sf, 380), sf, "#2b2118", x, ty + 50, 380, al)
            else:
                nf = font("NotoSerifKR-VF.ttf", 120, weight=900)
                for i, (when, what) in enumerate(steps):
                    last = i == n - 1
                    num = f"{i + 1:02d}"
                    d.text((90, y - 20), num, font=nf, fill=T["tint"] if not last else T["g1"])
                    d.text((300, y + 6), when, font=wf, fill=T["g1"] if last else T["ink"])
                    yy = put_lines(d, wrap(d, what, sf, W - 400), sf, "#2b2118", 300, y + 56, W - 400)
                    y = max(yy, y + 150) + 30
                    if not last:
                        d.line((300, y - 18, W - 90, y - 18), fill="#e6dccf", width=2)
                tops = [y]
            end = max(y, (tops[-1] if tops else y) + 160) + 140
            if not measure:
                footer(im, "#9a8066")
            return end
        return two_pass(render, W, 1080)

    if style == "B":
        def render(im, measure):
            im.paste(gradient(W, im.height, T["paper"], T["tint"], diagonal=False))
            d = ImageDraw.Draw(im)
            tf, wf, bf = font("Pretendard-Bold.otf", 54), font("Pretendard-Bold.otf", 30), font("NotoSansKR-VF.ttf", 34, weight=500)
            y = put_lines(d, c["title"].split("\n"), tf, T["deep"], 90, 90, W - 180, "center" if L == 3 else "left", 1.3) + 50
            def card(x, y, w, i, when, what):
                last = i == n - 1
                lines = wrap(d, what, bf, w - 170)
                h = max(150, 80 + line_h(bf, 1.4) * len(lines))
                panel(im, (x, y, x + w, y + h), radius=30, fill=hexrgb(T["deep"]) + (255,) if last else (255, 255, 255, 255), shadow=40)
                dd = ImageDraw.Draw(im)
                cx, cy = x + 72, y + h / 2
                dd.ellipse((cx - 38, cy - 38, cx + 38, cy + 38), fill=T["accent"] if last else T["g1"])
                nf = font("Pretendard-Bold.otf", 38)
                nw = dd.textlength(str(i + 1), font=nf)
                dd.text((cx - nw / 2, cy - 24), str(i + 1), font=nf, fill=T["deep"] if last else "#ffffff")
                dd.text((x + 140, y + 30), when, font=wf, fill=T["accent"] if last else T["g1"])
                put_lines(dd, lines, bf, "#ffffff" if last else "#2b2b2b", x + 140, y + 78, w - 170, "left", 1.4)
                return h
            if L == 1:
                for i, (when, what) in enumerate(steps):
                    h = card(90, y, W - 180, i, when, what)
                    if i < n - 1:
                        ImageDraw.Draw(im).polygon([(W / 2 - 14, y + h + 8), (W / 2 + 14, y + h + 8), (W / 2, y + h + 28)], fill=T["g1"])
                    y += h + 36
            elif L == 2:
                for i, (when, what) in enumerate(steps):
                    x = 70 if i % 2 == 0 else 250
                    h = card(x, y, W - 320, i, when, what)
                    y += h + 28
            else:
                cw = (W - 180 - 30) // 2
                i = 0
                while i < n:
                    if i == n - 1:
                        h = card(90, y, W - 180, i, *steps[i])
                        y += h + 30
                        i += 1
                    else:
                        h1 = card(90, y, cw, i, *steps[i])
                        h2 = card(90 + cw + 30, y, cw, i + 1, *steps[i + 1]) if i + 1 < n - 1 or n % 2 == 0 else 0
                        if h2 == 0:
                            y += h1 + 30
                            i += 1
                            continue
                        y += max(h1, h2) + 30
                        i += 2
            end = y + 110
            if not measure:
                footer(im, T["ink"])
            return end
        return two_pass(render, W, 1080)

    # C · 사진
    def render(im, measure):
        im.paste(Image.new("RGB", im.size, "#ffffff"))
        d = ImageDraw.Draw(im)
        wf, bf = font("NotoSerifKR-VF.ttf", 32, weight=800), font("NotoSerifKR-VF.ttf", 34, weight=400)
        tf = font("NotoSerifKR-VF.ttf", 54, weight=900)
        ph_src = Image.open(base / c["photo"]).convert("RGB")
        if L == 1:
            top = 560
            ph = ImageOps.fit(ph_src, (W, top), Image.LANCZOS)
            fade = Image.new("L", (W, top), 0)
            fd = ImageDraw.Draw(fade)
            for yy in range(top):
                fd.line((0, yy, W, yy), fill=int(170 * max(0, (yy - top * 0.3) / (top * 0.7))))
            im.paste(Image.composite(Image.new("RGB", (W, top), T["deep"]), ph, fade), (0, 0))
            d = ImageDraw.Draw(im)
            lines = c["title"].split("\n")
            put_lines(d, lines, tf, "#ffffff", 80, top - 60 - 72 * len(lines), W - 160, "left", 1.33)
            d.rectangle((80, top - 40, 200, top - 34), fill=T["accent"])
            x0, wtxt, y = 90, W - 180, top + 50
        elif L == 2:
            sw = 360
            im.paste(ImageOps.fit(ph_src, (sw, 3000), Image.LANCZOS).crop((0, 0, sw, im.height)), (0, 0))
            d = ImageDraw.Draw(im)
            d.rectangle((sw, 0, sw + 10, im.height), fill=T["accent"])
            y = put_lines(d, wrap(d, c["title"], tf, W - sw - 140), tf, T["deep"], sw + 70, 100, W - sw - 140, "left", 1.33) + 40
            x0, wtxt = sw + 70, W - sw - 140
        else:
            r = 200
            circ = ImageOps.fit(ph_src, (2 * r, 2 * r), Image.LANCZOS)
            mk = Image.new("L", (2 * r, 2 * r), 0)
            ImageDraw.Draw(mk).ellipse((0, 0, 2 * r, 2 * r), fill=255)
            d.ellipse((W / 2 - r - 12, 80 - 12, W / 2 + r + 12, 80 + 2 * r + 12), fill=T["tint"])
            im.paste(circ, (int(W / 2 - r), 80), mk)
            d = ImageDraw.Draw(im)
            y = put_lines(d, c["title"].split("\n"), tf, T["deep"], 0, 80 + 2 * r + 50, W, "center", 1.33) + 40
            x0, wtxt = 110, W - 220
        for i, (when, what) in enumerate(steps):
            last = i == n - 1
            col_w = 230 if L != 2 else 0
            lines = wrap(d, what, bf, wtxt - col_w)
            h = max(110, (0 if L != 2 else 50) + 44 + line_h(bf, 1.5) * len(lines))
            if last:
                d.rectangle((x0 - 30, y - 10, x0 + wtxt + 30, y + h - 18), fill=T["tint"])
            if L == 2:
                d.text((x0, y + 4), when, font=wf, fill=T["ink"] if last else "#8a7a6a")
                put_lines(d, lines, bf, "#2b2118", x0, y + 54, wtxt, "left", 1.5)
            else:
                d.text((x0, y + 8), when, font=wf, fill=T["ink"] if last else "#8a7a6a")
                put_lines(d, lines, bf, "#2b2118", x0 + col_w, y + 4, wtxt - col_w, "left", 1.5)
            if not last:
                d.line((x0, y + h - 14, x0 + wtxt, y + h - 14), fill="#ebe5dc", width=2)
            y += h
        end = y + 130
        if not measure:
            footer(im, "#9a8a7a")
        return end
    return two_pass(render, W, 1080)


# ══ 비교 (틀 4) — A·B 색은 공고 캡처 테두리(청록·보라)와 짝이라 고정 ══
# 디자인: A 흰 바탕 · B 색 분할 · C 떠 있는 카드
# 배치 A: 1 좌우 칸 · 2 항목마다 위아래 · 3 A 묶음 → B 묶음
# 배치 B: 1 좌우 분할+VS · 2 위아래 분할+VS · 3 좌우 분할+왼쪽 항목 띠
# 배치 C: 1 카드 나란히 · 2 카드 위아래 · 3 나란히 + 왼쪽 색 막대 + «같은 점» 위
TEAL, PURPLE = "#13806e", "#5b3fa0"


def card_비교(c, base, T, style, L):
    W = 1440
    rows = c["rows"]
    same = c.get("same")

    def render(im, measure):
        H = im.height
        if style == "A":
            im.paste(Image.new("RGB", im.size, "#ffffff"))
        elif style == "B":
            im.paste(Image.new("RGB", im.size, PURPLE if L == 2 else TEAL))
        else:
            im.paste(Image.new("RGB", im.size, T["tint"]))
        d = ImageDraw.Draw(im)
        if style == "A":
            d.text((70, 60), c["title"], font=font("GmarketSansBold.otf", 52), fill="#222")
            kf, vf = font("GmarketSansMedium.otf", 34), font("malgunbd.ttf", 36)
            if L == 1:
                colA, colB, colW = 420, 930, 440
                for x, t, col in ((colA, c["a"], TEAL), (colB, c["b"], PURPLE)):
                    d.rounded_rectangle((x - 20, 160, x + colW, 250), radius=16, fill=col)
                    centered(d, 178, t, font("GmarketSansBold.otf", 44), "#ffffff", 2 * x - 20 + colW)
                y = 290
                for k, a, b in rows:
                    la, lb = wrap(d, a, vf, colW - 20), wrap(d, b, vf, colW - 20)
                    h = max(130, 30 + line_h(vf, 1.35) * max(len(la), len(lb)))
                    d.line((70, y - 18, W - 70, y - 18), fill="#e6e6e6", width=2)
                    d.text((70, y + 20), k, font=kf, fill="#777")
                    put_lines(d, la, vf, TEAL, colA, y + 10, colW, "left", 1.35)
                    put_lines(d, lb, vf, PURPLE, colB, y + 10, colW, "left", 1.35)
                    y += h
            elif L == 2:
                y = 170
                for k, a, b in rows:
                    d.text((70, y), k, font=font("GmarketSansBold.otf", 36), fill="#333")
                    y += 60
                    for name, v, col in ((c["a"], a, TEAL), (c["b"], b, PURPLE)):
                        tw = d.textlength(name, font=kf)
                        d.rounded_rectangle((70, y, 70 + tw + 40, y + 56), radius=28, fill=col)
                        d.text((90, y + 8), name, font=kf, fill="#ffffff")
                        put_lines(d, [v.replace("\n", " ")], vf, "#222222", 70 + tw + 70, y + 6, W - tw - 220)
                        y += 72
                    d.line((70, y + 10, W - 70, y + 10), fill="#e6e6e6", width=2)
                    y += 40
            else:
                y = 170
                for name, idx, col in ((c["a"], 1, TEAL), (c["b"], 2, PURPLE)):
                    d.rectangle((70, y, 82, y + 70 + 70 * len(rows)), fill=col)
                    d.text((110, y), name, font=font("GmarketSansBold.otf", 46), fill=col)
                    y += 80
                    for row in rows:
                        d.text((110, y), row[0], font=kf, fill="#777")
                        put_lines(d, [row[idx].replace("\n", " ")], vf, "#222222", 420, y - 2, W - 500)
                        y += 70
                    y += 50
            end = y + 90
        elif style == "B":
            vf, kf = font("GmarketSansMedium.otf", 38), font("GmarketSansMedium.otf", 30)
            nf = font("GmarketSansBold.otf", 56)
            if L == 2:  # 위아래 분할
                d.rectangle((0, 0, W, 130), fill="#ffffff")
                centered(d, 36, c["title"], font("GmarketSansBold.otf", 50), "#222222", W)
                y = 170
                ys = []
                for idx, (name, col) in enumerate(((c["a"], TEAL), (c["b"], PURPLE))):
                    top = y
                    d.rectangle((0, top, W, top + 90 + 66 * len(rows) + 40), fill=col)
                    d.text((90, top + 30), name, font=nf, fill="#ffffff")
                    yy = top + 120
                    for row in rows:
                        d.text((90, yy), row[0], font=kf, fill="#d9f0ea" if idx == 0 else "#e4dcf5")
                        put_lines(d, [row[idx + 1].replace("\n", " ")], vf, "#ffffff", 420, yy - 4, W - 520)
                        yy += 66
                    ys.append(top)
                    y = yy + 40
                d.ellipse((W - 220, ys[1] - 62, W - 96, ys[1] + 62), fill="#ffffff")
                centered(d, ys[1] - 30, "VS", font("GmarketSansBold.otf", 52), "#222222", 2 * W - 316)
                end = y + 90
            else:
                d.rectangle((W // 2, 0, W, H), fill=PURPLE)
                d.rectangle((0, 0, W, 130), fill="#ffffff")
                centered(d, 36, c["title"], font("GmarketSansBold.otf", 50), "#222222", W)
                keyw = 300 if L == 3 else 0
                if L == 3:
                    d.rectangle((0, 130, keyw, H), fill="#ffffff")
                mid = keyw + (W - keyw) / 2
                aw = d.textlength(c["a"], font=nf)
                d.text((mid - 110 - aw, 196), c["a"], font=nf, fill="#ffffff")
                d.text((mid + 110, 196), c["b"], font=nf, fill="#ffffff")
                d.ellipse((mid - 62, 172, mid + 62, 296), fill="#ffffff")
                centered(d, 204, "VS", font("GmarketSansBold.otf", 52), "#222222", 2 * mid)
                y = 340
                colw = (W - keyw) / 2 - 170
                for k, a, b in rows:
                    la, lb = wrap(d, a, vf, colw), wrap(d, b, vf, colw)
                    h = max(170, 60 + 54 * max(len(la), len(lb)))
                    if L == 3:
                        put_lines(d, wrap(d, k, kf, keyw - 60), kf, "#333333", 40, y + 24, keyw - 60, "left")
                    else:
                        kw = d.textlength(k, font=kf)
                        d.rounded_rectangle((mid - kw / 2 - 26, y + 34, mid + kw / 2 + 26, y + 86), radius=26, fill="#ffffff")
                        centered(d, y + 43, k, kf, "#333333", 2 * mid)
                    put_lines(d, la, vf, "#ffffff", mid - 130 - colw, y + 20, colw, "right", 1.42)
                    put_lines(d, lb, vf, "#ffffff", mid + 130, y + 20, colw, "left", 1.42)
                    y += h
                end = y + 110
        else:
            vf, kf = font("Pretendard-Bold.otf", 38), font("NotoSansKR-VF.ttf", 28, weight=500)
            d.text((90, 80), c["title"], font=font("Pretendard-Bold.otf", 54), fill="#1f2a37")
            y0 = 200
            if same and L == 3:
                d.rounded_rectangle((90, 190, W - 90, 280), radius=45, fill="#1f2a37")
                centered(d, 213, "같은 점  ·  " + same, font("Pretendard-Bold.otf", 36), "#ffd166", W)
                y0 = 330
            sides = (((c["a"], TEAL, 1)), ((c["b"], PURPLE, 2)))
            if L == 2:
                cw = W - 180
                y = y0
                for name, col, idx in sides:
                    hrows = [max(90, 40 + 50 * len(wrap(d, r[idx].replace("\n", " "), vf, cw - 420))) for r in rows]
                    ch = 110 + sum(hrows) + 20
                    panel(im, (90, y, 90 + cw, y + ch), radius=34, shadow=55)
                    d = ImageDraw.Draw(im)
                    d.rounded_rectangle((90, y, 90 + cw, y + 90), radius=34, fill=col)
                    d.rectangle((90, y + 50, 90 + cw, y + 90), fill=col)
                    d.text((130, y + 18), name, font=font("Pretendard-Bold.otf", 46), fill="#ffffff")
                    yy = y + 110
                    for r, h in zip(rows, hrows):
                        d.text((130, yy + 8), r[0], font=kf, fill="#8a94a3")
                        put_lines(d, wrap(d, r[idx].replace("\n", " "), vf, cw - 420), vf, "#1f2a37", 420, yy, cw - 420, "left", 1.3)
                        yy += h
                    y += ch + 40
                ybot = y
            else:
                cw = (W - 180 - 60) // 2
                rh = [max(120, 60 + 50 * max(len(wrap(d, a, vf, cw - 80)), len(wrap(d, b, vf, cw - 80)))) for _, a, b in rows]
                ch = 120 + sum(rh) + 30
                for k, (name, col, idx) in enumerate(sides):
                    x = 90 + k * (cw + 60)
                    panel(im, (x, y0, x + cw, y0 + ch), radius=34, shadow=55)
                    d = ImageDraw.Draw(im)
                    if L == 3:
                        d.rounded_rectangle((x, y0, x + 22, y0 + ch), radius=11, fill=col)
                        d.text((x + 50, y0 + 26), name, font=font("Pretendard-Bold.otf", 46), fill=col)
                    else:
                        d.rounded_rectangle((x, y0, x + cw, y0 + 100), radius=34, fill=col)
                        d.rectangle((x, y0 + 60, x + cw, y0 + 100), fill=col)
                        d.text((x + 40, y0 + 22), name, font=font("Pretendard-Bold.otf", 46), fill="#ffffff")
                    y = y0 + 130
                    for i, (r, h) in enumerate(zip(rows, rh)):
                        d.text((x + 50, y), r[0], font=kf, fill="#8a94a3")
                        put_lines(d, wrap(d, r[idx], vf, cw - 90), vf, "#1f2a37", x + 50, y + 40, cw - 90, "left", 1.3)
                        if i < len(rows) - 1:
                            d.line((x + 50, y + h - 16, x + cw - 40, y + h - 16), fill="#edf0f3", width=2)
                        y += h
                ybot = y0 + ch + 40
            if same and L != 3:
                d.rounded_rectangle((90, ybot + 10, W - 90, ybot + 110), radius=50, fill="#1f2a37")
                centered(d, ybot + 38, "같은 점  ·  " + same, font("Pretendard-Bold.otf", 38), "#ffd166", W)
                ybot += 140
            end = ybot + 90
        if not measure:
            footer(im, {"A": "#999999", "B": "#ece6f8", "C": "#5f6b7a"}[style], dark=style == "B")
        return end

    return two_pass(render, W, 700)


TYPES = {"반전": card_반전, "요약": card_요약, "타임라인": card_타임라인, "비교": card_비교}


def pick_layout(c, folder, log):
    """같은 type 의 최근 기록 3개에 없는 배치"""
    recent = [r.get("layout") for r in log if r["type"] == c["type"] and r["folder"] != folder][-3:]
    for L in (1, 2, 3):
        if L not in recent:
            return L
    return recent[0] or 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    log = load_log()
    for arg in sys.argv[1:]:
        spec_path = Path(arg).resolve()
        c = json.loads(spec_path.read_text(encoding="utf-8"))
        folder = next((p.name for p in spec_path.parents if re.fullmatch(r"\d{4}-\d+", p.name)), spec_path.parent.name)
        theme = c.get("theme") or pick_theme(c)
        style = c.get("style") or pick_style(c, folder, log)
        layout = int(c.get("layout") or pick_layout(c, folder, log))
        im = TYPES[c["type"]](c, spec_path.parent, THEMES[theme], style, layout)
        out = (spec_path.parent / c["out"]).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out)
        log = [r for r in log if not (r["folder"] == folder and r["out"] == c["out"])]
        log.append({"folder": folder, "type": c["type"], "style": style, "layout": layout, "theme": theme, "out": c["out"]})
        print(f"만듦: {folder}/{c['out']}  {c['type']}-{style}{layout} · 테마 {theme}  {im.size[0]}×{im.size[1]}")
    if LOG.parent.exists() and any(re.fullmatch(r"\d{4}-\d+", r["folder"]) for r in log):
        keep = sorted((r for r in log if re.fullmatch(r"\d{4}-\d+", r["folder"])),
                      key=lambda r: (r["folder"].split("-")[0], int(r["folder"].split("-")[1])))
        LOG.write_text(json.dumps(keep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
