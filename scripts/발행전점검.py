"""발행 전 점검 — 지난 사고가 다시 나지 않게 막는다 (길라잡이 3-13 · 8장)

    python scripts/발행전점검.py 출력/1019-1 출력/1019-2 …           ← 발행일은 업체설정 «발행 기록»의 «MM/DD 예정»
    python scripts/발행전점검.py 출력/1019-1 --발행일 2026-10-21      ← 직접 줄 때

읽는 설정: docs/블로그_업체설정.md
- «## 금리 기준» 의 «적용: YYYY-MM-DD ~ YYYY-MM-DD» 한 줄
- «## 사용 금지 자산» 의 `경로` 들
- «## 예산 소진형 자금» 의 낱말들

| 판정 | 무엇 | 막으려는 사고 |
|---|---|---|
| ✗ | 사용 금지 자산을 썼다 | 고객 얼굴·이름이 그대로 나감 (1006-4) · 언론사 사진 (1006-5·7) |
| ✗ | 글에 금리 숫자가 있는데 원고 머리 «금리기준:» 이 없다 · 발행일이 그 기간 밖 · 업체설정 현재 분기와 다르다 | 3분기 금리 글이 4분기에 나감 (1006-3·4·5·6·7) |
| ✗ | AI 생성 사진 (파일명에 AI·generated) | 대표님 09-21 «AI 말고» |
| ⚠ | 사례·스톡 사진에 얼굴이 보인다 (OpenCV) | 사진 속 인물이 우리 고객처럼 읽힘 |
| ⚠ | 제목에 변동금리 숫자가 있는데 «N분기»가 없다 | 분기가 바뀌면 제목이 틀림 |
| ⚠ | 예산 소진형 자금 | 발행 직전 접수 중인지 확인 |

✗ 가 있으면 종료코드 2.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / "docs/블로그_업체설정.md"


def section(text, title):
    m = re.search(r"^## " + re.escape(title) + r".*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def load_conf():
    t = CONF.read_text(encoding="utf-8")
    rate = re.search(r"적용:\s*(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})(.*)", section(t, "금리 기준"))
    deny = re.findall(r"^- `([^`]+)`(.*)$", section(t, "사용 금지 자산"), re.M)
    budget = re.findall(r"^- (.+)$", section(t, "예산 소진형 자금"), re.M)
    return t, rate, deny, [b.split("—")[0].strip() for b in budget]


def publish_date(conf_text, folder, given):
    if given:
        return dt.date.fromisoformat(given)
    row = next((l for l in conf_text.splitlines() if f"| {folder} |" in l), "")
    m = re.search(r"(\d{1,2})/(\d{1,2}) 예정", row)
    y = re.search(r"(\d{4})-\d{2}-\d{2}", row)
    if m and y:
        d = dt.date(int(y.group(1)), int(m.group(1)), int(m.group(2)))
        return d if d >= dt.date(int(y.group(1)), 1, 1) else d.replace(year=d.year + 1)
    return dt.date.today()


MODEL = ROOT / "scripts/models/face_detection_yunet_2023mar.onnx"   # OpenCV 공식 YuNet (opencv_zoo)


def ascii_model():
    """OpenCV 는 한글 경로를 못 연다 → 임시 폴더(영문 경로)에 복사해 쓴다"""
    import shutil
    import tempfile
    dst = Path(tempfile.gettempdir()) / MODEL.name
    if not dst.exists() or dst.stat().st_size != MODEL.stat().st_size:
        shutil.copy(MODEL, dst)
    return str(dst)


def faces(path):
    """얼굴 수. OpenCV·모델이 없으면 None. 한글 경로라 이미지는 Pillow 로 읽는다."""
    try:
        import cv2
        import numpy as np
        from PIL import Image
    except Exception:
        return None
    if not MODEL.exists():
        return None
    im = Image.open(path).convert("RGB")
    im.thumbnail((960, 960))
    img = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(ascii_model(), "", (w, h), 0.8)
    _, found = det.detect(img)
    if found is None:
        return 0
    side = min(w, h)
    return sum(1 for f in found if min(f[2], f[3]) >= side * 0.06)   # 너무 작은 얼굴(군중)은 뺀다


def check(folder, args, conf):
    text, rate, deny, budget = conf
    errs, warns = [], []
    md = (folder / "글.md").read_text(encoding="utf-8")
    head, body = md.split("---\n", 1)
    title = re.search(r"^제목:\s*(.+)$", head, re.M).group(1)
    photos = json.loads((folder / "사진.json").read_text(encoding="utf-8")) if (folder / "사진.json").exists() else []
    pub = publish_date(text, folder.name, args.발행일)

    # 1. 사용 금지 자산 — 경로가 아니라 파일 지문으로 (원본/ 에 복사해 써도 잡는다)
    deny_hash = {md5(ROOT / p): (p, why.strip(" —")) for p, why in deny if (ROOT / p).exists()}
    for ph in photos:
        src = (folder / ph["src"]).resolve()
        if src.exists() and md5(src) in deny_hash:
            p, why = deny_hash[md5(src)]
            errs.append(f"사용 금지 자산 {ph['file']} ← {Path(p).name} — {why}")
        if re.search(r"(^|[-_ ])(AI|ai|generated)([-_. ]|$)", src.name):
            errs.append(f"AI 생성 사진으로 보임 {ph['file']} ← {src.name}")

    # 2. 금리 기간 — 글이 어느 분기 금리로 쓰였는지(원고 머리 «금리기준:»)와 발행일·현재 분기를 맞춘다
    has_rate = re.search(r"\d+\.\d+%(?!p)", title + body)
    if has_rate:
        mine = re.search(r"^금리기준:\s*(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})", head, re.M)
        if not mine:
            errs.append("글에 금리 숫자가 있는데 원고 머리에 «금리기준: 시작 ~ 끝» 이 없다 — 어느 분기 숫자인지 적는다")
        else:
            ms, me = dt.date.fromisoformat(mine.group(1)), dt.date.fromisoformat(mine.group(2))
            if not (ms <= pub <= me):
                errs.append(f"발행일 {pub} 이 이 글의 금리기준({ms} ~ {me}) 밖 — 새 분기 금리로 숫자를 고친다")
            if rate and (mine.group(1), mine.group(2)) != (rate.group(1), rate.group(2)):
                errs.append(f"이 글은 {ms}~{me} 금리인데 업체설정 현재 금리는 {rate.group(1)}~{rate.group(2)} — 숫자를 새 분기로")
        if not rate:
            warns.append("업체설정 «## 금리 기준» 이 없다 — 현재 분기를 확인할 수 없음")

    # 3. 제목 변동금리 숫자
    t_rates = re.findall(r"\d+\.\d+%(?!p)", title)
    if t_rates and not re.search(r"분기|고정", title):
        warns.append(f"제목에 금리 숫자 {', '.join(t_rates)} — «N분기» 를 붙이거나 숫자를 본문으로 (분기가 바뀌면 제목이 틀린다)")

    # 4. 얼굴 — 자사 브랜드 자산(대표·상담사)은 파일 지문으로 알아보고 뺀다
    up = folder / "올릴사진"
    brand = {md5(f) for f in (ROOT / "assets/브랜드").glob("*") if f.is_file()} - set(deny_hash)
    for ph in photos:
        src = (folder / ph["src"]).resolve()
        if src.exists() and md5(src) in brand:
            continue
        if ph["file"].startswith(tuple(f"{i:02d}-카드" for i in range(1, 30))) or "공고" in ph["file"] or "카드" in ph["file"]:
            continue
        p = up / ph["file"]
        n = faces(p if p.exists() else src)
        if n:
            warns.append(f"얼굴 {n}개 {ph['file']} — 고객·사례 인물로 읽히면 ✗. 손·뒷모습·공간 사진으로 바꾸거나 가린다")
        elif n is None:
            warns.append("OpenCV 가 없어 얼굴 점검을 못 함 (pip install opencv-python)")
            break

    # 5. 예산 소진형
    hit = [b for b in budget if b and (b in title or body.count(b) >= 2)]
    if hit:
        warns.append(f"예산 소진형 자금 ({', '.join(hit)}) — 발행 직전 접수 중인지 공고 확인")

    return pub, errs, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--발행일")
    args = ap.parse_args()
    conf = load_conf()
    bad = 0
    for f in args.folders:
        folder = Path(f)
        pub, errs, warns = check(folder, args, conf)
        print(f"■ {folder.name}  발행 {pub}")
        for e in errs:
            print(f"  ✗ {e}")
        for w in warns:
            print(f"  ⚠ {w}")
        if not errs and not warns:
            print("  통과")
        bad += bool(errs)
    print(f"\n✗ 있는 글 {bad}편" if bad else "\n✗ 없음")
    sys.exit(2 if bad else 0)


if __name__ == "__main__":
    main()
