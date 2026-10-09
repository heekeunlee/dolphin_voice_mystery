#!/usr/bin/env python3
"""조판 순서(_quarto.yml chapters)대로 완성 원고를 마크다운 한 파일로 묶는다."""
import re, pathlib
B = pathlib.Path(__file__).resolve().parents[1]
cfg = (B / "_quarto.yml").read_text(encoding="utf-8")
files = re.findall(r"^\s*-\s+((?:src/)?[\w\-./]+\.qmd)\s*$", cfg, flags=re.M)
out = ["# 곰새코지 돌고래 목소리 사건", "",
       "> 완성 원고(조판 교정쇄 기준). 그림 자리와 `[[ ]]` 표시는 인쇄 전에 채울 항목.", ""]
for f in files:
    t = (B / f).read_text(encoding="utf-8")
    t = re.sub(r"^(#+ .*?)\s*\{[^}]*\}\s*$", r"\1", t, flags=re.M)        # qmd 속성 제거
    t = t.replace("::: {.art-slot}\n지도 그림이 들어갈 자리\n:::", "*[지도 그림이 들어갈 자리]*")
    out += ["\n---\n", t.strip(), ""]
dst = B / "_output" / "dolphin-said-manuscript.md"
dst.write_text("\n".join(out) + "\n", encoding="utf-8")
print(dst, len(files), "files")
