"""줄바꿈 점검 (대표님 10-26 «하고계세요만 밑으로 내려놓지를 않나 마침표 뒤에 글을 더 쓰질 않나»)

    python scripts/줄바꿈점검.py 출력/<폴더>/글.md …

- 문장 이어짐: 한 줄 안에서 문장이 끝나고 다음 문장이 바로 이어지는 줄 → 문장 끝마다 줄을 바꾼다
- 짧은 조각: 문장이 안 끝났는데 6자 이하만 남은 줄 («계세요.»처럼 서술어만 다음 줄로) → 앞줄과 합치거나 문장을 줄인다
- 강조 없는 문단 수 (고정 마무리 제외)
- 사진 연속: 사진 두 장 사이에 글 문단이 없음 (대표님 10-26) → 사이에 문단을 둔다
reflow 같은 자동 줄바꿈은 쓰지 않는다. 문장을 짧게 고쳐 쓴다.
"""
import re,sys
sys.stdout.reconfigure(encoding="utf-8")
TAG=re.compile(r"\{[^}]*\}")
for p in sys.argv[1:]:
    t=open(p,encoding="utf-8").read().split("---\n",1)[1]
    t=t.split("{노}저희 한국중소기업")[0]
    bad=0
    seq=[x.strip() for x in t.split("\n\n") if x.strip() and x.strip()!="[구분선]"]
    for a,b in zip(seq,seq[1:]):
        if re.fullmatch(r"\[사진 \d+\]",a) and re.fullmatch(r"\[사진 \d+\]",b):
            print(f"  사진 연속 | {a} {b}"); bad+=1
    paras=[x for x in t.split("\n\n") if x.strip() and not x.startswith(("[","##","http"))]
    plain_paras=0
    for para in paras:
        if not TAG.search(para) and not para.startswith(">"): plain_paras+=1
        for l in para.split("\n"):
            v=TAG.sub("",l).lstrip("> ").strip()
            if re.search(r"[가-힣a-z)][.?!]\s+\S",v):
                print(f"  문장 이어짐 | {v}"); bad+=1
            if len(v)<=6 and not re.search(r"[.?!]$",v) and v:
                print(f"  짧은 조각 | {v}"); bad+=1
    print(f"{p}: 문제 {bad}줄 · 강조 없는 문단 {plain_paras}/{len(paras)}")
