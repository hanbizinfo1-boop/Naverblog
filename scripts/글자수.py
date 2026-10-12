"""본문 글자 수 (공백 제외) — v7 기준 1,200~1,600자

    python scripts/글자수.py 출력/1006-1 출력/1006-2 ...

글.md 머리(--- 위)와 표시 문법({빨}·[사진 N]·[구분선]·## ·> )은 빼고 센다.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def count(md: str) -> int:
    s = md.split("---\n", 1)[1].split("## 찾아오시는 길")[0]
    s = re.sub(r"\{.\}|\{/\}", "", s)
    s = re.sub(r"\[사진 \d+\]|\[구분선\]", "", s)
    s = re.sub(r"^(## |>> |> )", "", s, flags=re.M)
    return len(re.sub(r"\s", "", s))


for arg in sys.argv[1:]:
    p = Path(arg)
    f = p / "글.md" if p.is_dir() else p
    n = count(f.read_text(encoding="utf-8"))
    mark = "" if 1200 <= n <= 1600 else "  ⚠ 1,200~1,600 밖"
    print(f"{p.name}\t{n:,}자{mark}")
