"""글끼리 얼마나 닮았나 — 양산형(저품질) 판정 예방

    python scripts/유사도검사.py 출력/1013-1                 ← 이 글을 최근 글 전부와 비교
    python scripts/유사도검사.py 출력/1006-1 … 출력/1006-7   ← 서로 비교

세 가지를 잰다.
1. 구조 유사도 — 문단 종류의 순서(사진·소제목·인용·구분선·번호·짧은 강조·일반)를 비교
2. 같은 문장 — 표시 문법을 뺀 6자 이상 줄이 다른 글에도 그대로 있는지 (고정 마무리는 제외)
3. 틀 — 원고 머리 `틀:` 이 비교 대상과 같은지
4. 같은 사진 — `올릴사진/` 파일이 다른 글과 똑같은지 (브랜드 자산은 3편 안에서만 ⚠, 나머지는 언제든 ⚠)

비교 대상: 인자로 준 폴더들 + 출력/ 아래 MMDD-N 폴더 중 최근 14개.
"""
import difflib
import hashlib
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
STRUCT_WARN = 0.75      # 구조 유사도 이 이상이면 ⚠
SAME_LINE_WARN = 3      # 고정 문구 빼고 같은 줄이 이 이상이면 ⚠

# 대표님이 고정한 마무리 — 모든 글에 같아야 하므로 비교에서 뺀다
FIXED = {
    "저희 한국중소기업비즈니스센터는", "정책자금과 정부 지원금은 물론", "함께 풀어드립니다.",
    "혼자 하기 어려우시면", "아래 네이버폼 남겨주세요.", "저 박관장이 꼼꼼히 보고", "연락드리겠습니다.",
    "한번 같이 봐요.",
}


def strip(line: str) -> str:
    line = re.sub(r"\{.\}|\{/\}", "", line)
    return re.sub(r"^(##|>>|>)\s*", "", line).strip()


def load(folder: Path):
    text = (folder / "글.md").read_text(encoding="utf-8")
    head, body = text.split("---\n", 1)
    frame = re.search(r"^틀:\s*(\S+)", head, re.M)
    blocks = [b.strip("\n") for b in re.split(r"\n\s*\n", body) if b.strip()]
    sig = []
    for b in blocks:
        first = b.split("\n")[0]
        if first.startswith("[사진"):
            sig.append("S")
        elif first.startswith("[구분선"):
            sig.append("D")
        elif first.startswith("## "):
            sig.append("H")
        elif first.startswith(">"):
            sig.append("Q")
        elif re.match(r"\{.\}\d+\.", first) or re.match(r"\d+\.", first):
            sig.append("N")
        elif first.startswith("http"):
            sig.append("U")
        elif len(b.split("\n")) == 1:
            sig.append("1")
        else:
            sig.append("P")
    lines = {strip(l) for l in body.split("\n")}
    lines = {l for l in lines if len(l) >= 6 and not l.startswith(("[사진", "[구분선", "http")) and l not in FIXED}
    photos = {}
    up = folder / "올릴사진"
    if up.exists():
        for f in up.iterdir():
            if f.is_file():
                photos[hashlib.md5(f.read_bytes()).hexdigest()] = f.name
    brand = set()
    pj = folder / "사진.json"
    if pj.exists():
        import json
        for x in json.loads(pj.read_text(encoding="utf-8")):
            if "assets/브랜드" in x.get("src", "").replace("\\", "/"):
                brand.add(x["file"])
    return {"name": folder.name, "frame": frame[1] if frame else "-", "sig": "".join(sig), "lines": lines,
            "photos": photos, "brand": brand}


def order(name):
    d, n = name.split("-")
    return int(d) * 100 + int(n)


def recent(limit=14):
    out = sorted((p for p in (ROOT / "출력").iterdir() if re.fullmatch(r"\d{4}-\d+", p.name) and (p / "글.md").exists()),
                 key=lambda p: (p.name.split("-")[0], int(p.name.split("-")[1])))
    return out[-limit:]


def main():
    targets = [Path(a) for a in sys.argv[1:]]
    if not targets:
        print(__doc__)
        return
    pool = {p.resolve(): p for p in recent()}
    for t in targets:
        pool.setdefault(t.resolve(), t)
    data = {k: load(v) for k, v in pool.items()}
    worst = 0
    for t in targets:
        a = data[t.resolve()]
        print(f"\n■ {a['name']}  (틀 {a['frame']})  구조 {a['sig']}")
        rows = []
        for k, b in data.items():
            if k == t.resolve():
                continue
            r = difflib.SequenceMatcher(None, a["sig"], b["sig"]).ratio()
            same = sorted(a["lines"] & b["lines"])
            pics = []
            dist = abs(order(a["name"]) - order(b["name"])) if "-" in a["name"] and "-" in b["name"] else 0
            for h in a["photos"].keys() & b["photos"].keys():
                f = a["photos"][h]
                if f in a["brand"] and dist > 3:
                    continue  # 브랜드 자산은 3편 넘게 떨어지면 허용
                pics.append(f)
            rows.append((r, b, same, sorted(pics)))
        rows.sort(key=lambda x: (-x[0], -len(x[2])))
        for r, b, same, pics in rows:
            flags = []
            if r >= STRUCT_WARN:
                flags.append(f"⚠ 구조 {r:.2f}")
            if len(same) >= SAME_LINE_WARN:
                flags.append(f"⚠ 같은 문장 {len(same)}")
            if pics:
                flags.append(f"⚠ 같은 사진 {len(pics)}")
            if a["frame"] != "-" and a["frame"] == b["frame"]:
                flags.append("같은 틀")
            if flags:
                worst += 1
                print(f"  vs {b['name']:8} 구조 {r:.2f} · 같은 문장 {len(same):2}  {' · '.join(flags)}")
                for s in same[:6]:
                    print(f"      «{s}»")
                for f in pics:
                    print(f"      사진 {f}")
        if not any(r >= STRUCT_WARN or len(s) >= SAME_LINE_WARN or p for r, _, s, p in rows):
            print("  통과 — 구조·문장이 겹치는 글 없음")
    print(f"\n⚠ 짝 {worst}개" if worst else "\n전부 통과")


if __name__ == "__main__":
    main()
