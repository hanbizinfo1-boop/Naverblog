"""블로그 이미지 자동 수집 — Pexels 1순위 / Unsplash 2순위

API 키도 계정도 필요 없다.
검색 페이지는 브라우저(Claude in Chrome)로 열어 이미지 주소만 뽑고,
실제 다운로드는 이 스크립트가 CDN 에서 직접 받는다. CDN 에는 봇 차단이 없다.

## 흐름

1) 브라우저로 검색 페이지를 열고 아래 JS 로 주소를 긁는다.

   Pexels   https://www.pexels.com/search/<검색어>/
            [...document.querySelectorAll('img')].map(i=>i.src)
              .filter(s=>s&&s.includes('images.pexels.com/photos/'))

   Unsplash https://unsplash.com/s/photos/<검색어>
            [...document.querySelectorAll('img')].map(i=>i.src)
              .filter(s=>s&&s.includes('images.unsplash.com/photo-'))

2) 긁은 주소를 후보 파일에 넣는다.  출력/<폴더>/후보.json
   {
     "사진1": {"urls": ["https://images.pexels.com/photos/...", ...],
               "portrait": false}
   }

3) 이 스크립트를 돌린다.

   python scripts/이미지수집.py 출력/0921-1
   python scripts/이미지수집.py --all

   후보를 위에서부터 받아 1200x800 이상인 첫 장을 채택하고,
   1536x1024(세로형은 1024x1536)로 중앙 크롭해 저장한다.
   같은 폴더 안에서 같은 사진이 두 번 쓰이지 않게 막는다.

## 라이선스

Pexels / Unsplash 모두 상업적 이용 무료이고 출처 표기 의무가 없다.
그래도 출력/이미지출처.json 에 전부 기록해 나중에 추적할 수 있게 한다.
"""
import io
import json
import pathlib
import sys
import urllib.request

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
LAND = (1536, 1024)
PORT = (1024, 1536)
MIN_W, MIN_H = 1200, 800
UA = {"User-Agent": "Mozilla/5.0"}

# 제공처 우선순위. 후보 목록을 이 순서로 정렬해 앞쪽부터 시도한다.
PRIORITY = ["images.pexels.com", "images.unsplash.com"]


def provider_of(url):
    if "images.pexels.com" in url:
        return "pexels"
    if "images.unsplash.com" in url:
        return "unsplash"
    return "기타"


def rank(url):
    for i, host in enumerate(PRIORITY):
        if host in url:
            return i
    return len(PRIORITY)


def sized(url, w=1920):
    """CDN 에 큰 사이즈를 요청한다."""
    base = url.split("?")[0]
    if "images.pexels.com" in base:
        return f"{base}?auto=compress&cs=tinysrgb&w={w}"
    if "images.unsplash.com" in base:
        return f"{base}?w={w}&fm=jpg&q=90"
    return base


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def crop_to(im, tw, th):
    im = im.convert("RGB")
    sw, sh = im.size
    tr = tw / th
    if sw / sh > tr:
        nw = int(sh * tr)
        im = im.crop(((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh))
    else:
        nh = int(sw / tr)
        im = im.crop((0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh))
    return im.resize((tw, th), Image.LANCZOS)


def fill_slot(dest, urls, portrait, used):
    tw, th = PORT if portrait else LAND
    for url in sorted(urls, key=rank):
        base = url.split("?")[0]
        if base in used:
            continue
        try:
            im = Image.open(io.BytesIO(fetch(sized(url))))
            if im.width < MIN_W or im.height < MIN_H:
                continue
            crop_to(im, tw, th).save(dest, "JPEG", quality=88,
                                     optimize=True, progressive=True)
            used.add(base)
            return {"provider": provider_of(url), "url": base,
                    "orig": f"{im.width}x{im.height}"}
        except Exception:
            continue
    return None


def run_folder(folder):
    folder = pathlib.Path(folder)
    cand_f = folder / "후보.json"
    if not cand_f.exists():
        print(f"  건너뜀 — {cand_f} 가 없습니다 (브라우저로 주소를 먼저 긁어주세요)")
        return [], []

    img_dir = folder / "이미지"
    img_dir.mkdir(exist_ok=True)
    spec = json.loads(cand_f.read_text(encoding="utf-8"))

    done, fail, used = [], [], set()
    for slot, cfg in spec.items():
        urls = cfg["urls"] if isinstance(cfg, dict) else list(cfg)
        portrait = bool(cfg.get("portrait")) if isinstance(cfg, dict) else False
        got = fill_slot(img_dir / f"{slot}.jpg", urls, portrait, used)
        if got:
            got.update({"folder": folder.name, "slot": slot})
            done.append(got)
            print(f"  OK   {slot}  [{got['provider']}]  {got['orig']}")
        else:
            fail.append(f"{folder.name}/{slot}")
            print(f"  FAIL {slot}  (후보 {len(urls)}개 모두 실패)")
    return done, fail


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    targets = (sorted(p for p in (ROOT / "출력").iterdir()
                      if p.is_dir() and not p.name.startswith("_"))
               if args[0] == "--all" else [pathlib.Path(a) for a in args])

    all_done, all_fail = [], []
    for t in targets:
        print(f"[{t.name}]")
        d, f = run_folder(t)
        all_done += d
        all_fail += f

    man = ROOT / "출력" / "이미지출처.json"
    prev = json.loads(man.read_text(encoding="utf-8")) if man.exists() else []
    keys = {(d["folder"], d["slot"]) for d in all_done}
    merged = [p for p in prev if (p.get("folder"), p.get("slot")) not in keys] + all_done
    man.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n성공 {len(all_done)} / 실패 {len(all_fail)}")
    if all_fail:
        print("실패:", ", ".join(all_fail))
    print(f"출처 기록: {man}")


if __name__ == "__main__":
    main()
