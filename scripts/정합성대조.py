"""사진-본문 정합성 대조 시트

글 폴더의 올릴사진/ 과 글.md 를 읽어, 사진마다 바로 앞 문단과 바로 뒤 문단을
옆에 붙인 한 장짜리 시트를 만든다. 사진을 넣은 사람이 "이 사진 옆에서 무슨 말을 하는지"
한눈에 확인하는 용도다.

    python scripts/정합성대조.py 출력/1006-1          → 출력/1006-1/_정합성대조.jpg
"""
import json
import pathlib
import re
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = "C:/Windows/Fonts/malgun.ttf"
MARK = re.compile(r"\{[가-힣]\}|\{/\}|\*\*|^>>? |^## |^Q\. ")


def plain(s):
    return MARK.sub("", s)


def paragraphs(body):
    return [b.strip() for b in re.split(r"\n\s*\n", body.strip()) if b.strip()]


def main(folder):
    folder = pathlib.Path(folder)
    text = (folder / "글.md").read_text(encoding="utf-8")
    body = text.split("\n---\n", 1)[1]
    photos = json.loads((folder / "사진.json").read_text(encoding="utf-8"))
    paras = paragraphs(body)

    rows = []
    for i, p in enumerate(paras):
        m = re.fullmatch(r"\[사진 (\d+)\]", p)
        if not m:
            continue
        n = int(m[1])
        before = next((paras[j] for j in range(i - 1, -1, -1) if not paras[j].startswith("[사진")), "")
        after = next((paras[j] for j in range(i + 1, len(paras)) if not paras[j].startswith("[사진")), "")
        rows.append((n, photos[n - 1]["file"], before, after))

    f = ImageFont.truetype(FONT, 17)
    fb = ImageFont.truetype(FONT, 19)
    IW, TW, PAD = 520, 560, 14
    tiles = []
    for n, file, before, after in rows:
        im = Image.open(folder / "올릴사진" / file).convert("RGB")
        im.thumbnail((IW, 420))
        lines = ["▲ 앞 문단"] + [plain(l) for l in before.split("\n")] + [""] + \
                ["▼ 뒤 문단"] + [plain(l) for l in after.split("\n")]
        th = PAD * 2 + 30 + len(lines) * 26
        h = max(im.height + PAD * 2 + 30, th)
        t = Image.new("RGB", (IW + TW + PAD * 3, h), "white")
        d = ImageDraw.Draw(t)
        d.text((PAD, PAD), f"사진 {n}  {file}", font=fb, fill=(200, 30, 40))
        t.paste(im, (PAD, PAD + 30))
        y = PAD + 30
        for l in lines:
            color = (0, 120, 60) if l.startswith(("▲", "▼")) else (40, 40, 40)
            d.text((IW + PAD * 2, y), l, font=f, fill=color)
            y += 26
        d.line([(0, h - 1), (t.width, h - 1)], fill=(200, 200, 200), width=2)
        tiles.append(t)

    W = max(t.width for t in tiles)
    sheet = Image.new("RGB", (W, sum(t.height for t in tiles)), "white")
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.height
    out = folder / "_정합성대조.jpg"
    sheet.save(out, "JPEG", quality=85)
    print(out)


if __name__ == "__main__":
    for a in sys.argv[1:]:
        main(a)
