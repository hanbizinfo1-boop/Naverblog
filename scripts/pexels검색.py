"""Pexels 후보 검색 → 번호 붙은 미리보기 시트 (브라우저 확장 없이, 로컬 크롬 headless)

    python scripts/pexels검색.py <시트이름> "검색어1" "검색어2" …

- 검색어마다 결과 사진 ID·설명(alt)을 모아 `_tmp/pexels/<시트이름>.json` 에 저장
- 이미 쓴 사진(출력/이미지출처.json)은 뺀다 → 재사용 금지
- 미리보기 시트 `_tmp/pexels/<시트이름>.jpg` (사진마다 ID 표시) — 직접 열어 보고 고른다
- 후보만 다시 보기: python scripts/pexels검색.py --ids <시트이름> <id> <id> …
- 고른 사진 받기: python scripts/pexels검색.py --get <id> <저장경로>

라이선스: Pexels License — 상업 이용 가능, 출처 표기 불필요.
단, 사진 속 인물이 우리 서비스를 보증하는 것처럼 쓰지 않는다 (사례 «그 대표님» 으로 지목 ✗).
"""
import io
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_tmp/pexels"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"


def used_ids():
    p = ROOT / "출력/이미지출처.json"
    if not p.exists():
        return set()
    return {str(x["url"]).split("/photos/")[1].split("/")[0] for x in json.loads(p.read_text(encoding="utf-8"))
            if x.get("provider") == "pexels"}


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()


def search(queries):
    from playwright.sync_api import sync_playwright
    found = {}
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True, args=["--disable-blink-features=AutomationControlled"])
        pg = b.new_page(user_agent=UA, viewport={"width": 1400, "height": 2400})
        for q in queries:
            pg.goto(f"https://www.pexels.com/search/{urllib.parse.quote(q)}/", timeout=60000)
            pg.wait_for_timeout(4000)
            pg.mouse.wheel(0, 3000)
            pg.wait_for_timeout(1500)
            rows = pg.eval_on_selector_all(
                "img", "els=>els.filter(e=>e.src.includes('images.pexels.com/photos/'))"
                       ".map(e=>[e.src.split('/photos/')[1].split('/')[0], e.alt||''])")
            for i, alt in rows:
                if alt.startswith("Free "):
                    found.setdefault(i, {"id": i, "alt": alt, "q": q})
        b.close()
    return found


def sheet(name, items):
    cell, cols = 300, 6
    rows = (len(items) + cols - 1) // cols
    im = Image.new("RGB", (cols * cell, rows * (cell + 26)), "white")
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 18)
    for k, it in enumerate(items):
        try:
            t = Image.open(io.BytesIO(fetch(f"https://images.pexels.com/photos/{it['id']}/pexels-photo-{it['id']}.jpeg?auto=compress&cs=tinysrgb&w=400")))
            t.thumbnail((cell - 6, cell - 6))
        except Exception:
            continue
        x, y = (k % cols) * cell, (k // cols) * (cell + 26)
        im.paste(t, (x + 3, y + 3))
        d.text((x + 6, y + cell), f"{k + 1}. {it['id']}", font=f, fill="#c00")
    path = OUT / f"{name}.jpg"
    im.save(path, quality=80)
    return path


def main():
    a = sys.argv[1:]
    OUT.mkdir(parents=True, exist_ok=True)
    if a and a[0] == "--get":
        pid, dst = a[1], Path(a[2])
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(fetch(f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=1920"))
        print(f"받음: {dst}  {Image.open(dst).size}")
        return
    if a and a[0] == "--ids":  # 고른 후보만 다시 시트로: --ids <시트이름> <id> <id> …
        print("시트:", sheet(a[1], [{"id": i} for i in a[2:]]))
        return
    name, queries = a[0], a[1:]
    used = used_ids()
    found = [v for k, v in search(queries).items() if k not in used]
    (OUT / f"{name}.json").write_text(json.dumps(found, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for k, it in enumerate(found, 1):
        print(f"{k:3}. {it['id']:>9}  [{it['q']}] {it['alt'][5:95]}")
    print("시트:", sheet(name, found))


if __name__ == "__main__":
    main()
