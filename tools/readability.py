#!/usr/bin/env python3
"""한국어 원고 가독성 측정 (초등 5~6학년 기준 점검용).
usage: python3 tools/readability.py drafts/dolphin-said/ch01-v1.md
"""
import re, sys
from collections import Counter

text = open(sys.argv[1], encoding="utf-8").read()
# 코드블록(ASCII 로그)과 마크다운 헤더 제외
body = re.sub(r"```.*?```|<!--.*?-->", "", text, flags=re.S)
body = "\n".join(l for l in body.splitlines() if not l.startswith("#"))
paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
sents = [s.strip() for s in re.split(r"(?<=[.?!…])\s+|\n", body) if len(s.strip()) > 1]
lens = [len(re.sub(r"\s", "", s)) for s in sents]
dialog = [s for s in sents if s.startswith(("“", '"', "‘", "'"))]
chars = len(re.sub(r"\s", "", body))

print(f"본문 글자 수(공백 제외): {chars:,}")
print(f"문단 {len(paras)}개, 문장 {len(sents)}개")
print(f"평균 문장 길이: {sum(lens)/len(lens):.1f}자 (5~6학년 권장 20~30)")
long_ = [s for s, n in zip(sents, lens) if n > 50]
print(f"50자 초과 문장: {len(long_)}개 ({len(long_)/len(sents)*100:.1f}%)  (기준 10% 이하)")
print(f"대화 문장 비율: {len(dialog)/len(sents)*100:.1f}%")
plen = [len(re.sub(r'\s','',p)) for p in paras]
print(f"평균 문단 길이: {sum(plen)/len(plen):.0f}자, 최장 문단 {max(plen)}자")
latin = Counter(re.findall(r"[A-Za-z][A-Za-z0-9_.\-]+", body))
print("영문/약어:", ", ".join(f"{w}({c})" for w, c in latin.most_common(15)) or "없음")
print("\n[50자 초과 문장 상위 8개]")
for s in sorted(long_, key=len, reverse=True)[:8]:
    print(" -", s[:120])

# 짧은 '~다.' 서술문 4개 이상 연속 구간 (가독성 체크리스트 8번)
narr = [s for s in re.split(r"(?<=[.?!…])\s+|\n", body) if s.strip()]
run, runs = [], []
for s in narr:
    s2 = s.strip()
    if s2.endswith("다.") and not s2.startswith(("“", '"', "‘", "'", "`", ">", "[")) and len(re.sub(r"\s","",s2)) <= 18:
        run.append(s2)
    else:
        if len(run) >= 4: runs.append(run)
        run = []
if len(run) >= 4: runs.append(run)
print(f"\n[짧은 서술문(18자 이하) 4개 이상 연속: {len(runs)}곳]")
for r in runs[:8]:
    print(" -", " / ".join(r)[:160])
