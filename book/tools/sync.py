#!/usr/bin/env python3
"""확정 원고(drafts/dolphin-said)를 9장으로 묶어 조판 소스(book/src)로 옮긴다.

- 확정 원고의 17개 편집 단위를 유지하면서 출판본에서는 인접 장을 묶는다.
- HTML 주석(작가·심사 메모)은 빼고, 묶음 안의 기존 제목은 소제목으로 남긴다.
- 부속물은 인쇄용 부분만 남긴다(예: 「곰새코지 사람들」은 'A. 쪽 문안'만).
- 다시 실행하면 src/를 통째로 새로 만든다. src/ 파일은 직접 고치지 말 것.
"""
import re, pathlib, shutil, os

ROOT = pathlib.Path(__file__).resolve().parents[2]
DRAFT = ROOT / "drafts" / "dolphin-said"
MATTER = DRAFT / "matter"
SRC = ROOT / "book" / "src"

def curly_single(t: str) -> str:
    """'…' 짝을 ‘…’로. 코드 블록과 인라인 코드는 건드리지 않는다(pandoc smart는 '단어'를 의 ' 를 아포스트로피로 오인)."""
    parts = re.split(r"(```.*?```|`[^`\n]*`)", t, flags=re.S)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"'([^'\n]+?)'", "\u2018\\1\u2019", parts[i])
    return "".join(parts)

def strip_comments(t: str) -> str:
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"\n(?:\s*---\s*\n)+\s*$", "\n", t)   # 끝에 남은 구분선 제거
    t = curly_single(t)
    # 등장인물 이름 변경: 인쇄본·EPUB·부록에 일관되게 반영
    t = t.replace("하안", "다원")
    # 젊은 해녀의 이름을 한국식 이름으로 통일한다. ‘바위투성이라’처럼
    # 일반 단어 안의 글자는 건드리지 않고 인물명과 조사 결합만 바꾼다.
    # 조사 결합형은 문법에 맞게 교체한다(투가→미숙이, 투는→미숙은 등).
    for old, new in (("투였다", "미숙이었다"), ("투가", "미숙이"), ("투는", "미숙은"),
                     ("투의", "미숙의"), ("투를", "미숙을"), ("투 씨", "미숙 씨"),
                     ("투도", "미숙도"), ("투만", "미숙만")):
        t = t.replace(old, new)
    t = re.sub(r"(?<![가-힣])투(?=[.!?,]|\s|$)", "미숙", t)
    # 1장 메모는 일반 인용문 대신 어린이용 메모 카드로 조판한다.
    t = re.sub(
        r"> \*\*단우의 메모 #1\*\*\n> 라벨 = 소리 조각에 붙이는 이름표\.\n> 사진에 다는 해시태그 같은 것\.",
        r"\\memobox{단우의 메모 \\#1}{라벨 = 소리 조각에 붙이는 이름표.\\\\사진에 다는 해시태그 같은 것.}",
        t,
    )
    return t.rstrip() + "\n"

def write(name: str, text: str):
    (SRC / name).write_text(text, encoding="utf-8")

CHAPTER_GROUPS = [
    ("새벽 세 시, 내 아이디가 찍혔다", 1, [1, 2]),
    ("잘린 장면은 누구 편일까?", 3, [3, 4]),
    ("잠든 사이 라벨을 붙인 건 누구?", 5, [5, 6]),
    ("W-07은 누구의 휘슬일까?", 7, [7, 8]),
    ("원본 영상이 찾아낸 증거", 9, [9, 10]),
    ("정정문에 담긴 고백", 11, [11, 12]),
    ("엔진을 끄자, 소리가 들렸다", 13, [13, 14]),
    ("소등굴, 마지막 구조 신호", 15, [15, 16]),
    ("마지막 물질, 처음 듣는 휘슬", 17, [17]),
]

SOURCE_TO_BOOK_CHAPTER = {
    source_no: book_no
    for book_no, (_, _, source_numbers) in enumerate(CHAPTER_GROUPS, start=1)
    for source_no in source_numbers
}

def remap_chapter_references(text: str) -> str:
    """인쇄되는 권말의 장 참조를 새 9장 번호로 바꾼다."""
    pattern = re.compile(r"(?<!\d)(\d+(?:[·,–-]\d+)*)장")

    def replace(match):
        source_numbers = re.split(r"[·,–-]", match.group(1))
        book_numbers = []
        for number in source_numbers:
            mapped = SOURCE_TO_BOOK_CHAPTER.get(int(number))
            if mapped is not None and mapped not in book_numbers:
                book_numbers.append(mapped)
        if not book_numbers:
            return match.group(0)
        return "·".join(map(str, book_numbers)) + "장"

    return pattern.sub(replace, text)

def chapters():
    suffix = os.environ.get("CH_SUFFIX", "final")
    for output_no, (title, art_no, source_numbers) in enumerate(CHAPTER_GROUPS, start=1):
        parts = []
        for source_no in source_numbers:
            source = DRAFT / f"ch{source_no:02d}-{suffix}.md"
            t = strip_comments(source.read_text(encoding="utf-8"))
            lines = t.split("\n")
            match = re.match(r"^# \d+장\. (.+)$", lines[0]) if lines else None
            assert match, f"{source.name}: 첫 줄이 'n장. 제목' 형식이 아님"
            body = "\n".join(lines[1:]).strip()
            interlude = ""
            if source_no != source_numbers[0]:
                interlude = f'::: {{.chapter-interlude data-art="{source_no:02d}"}}\n:::\n\n'
            parts.append(interlude + f"## {match.group(1)}\n\n{body}")
        title_line = f'# {output_no}장. {title} {{.chapter-title data-art="{art_no:02d}"}}'
        write(f"ch{output_no:02d}.qmd", title_line + "\n\n" + "\n\n".join(parts) + "\n")

def section(text: str, start: str, end_pat: str = r"\n## ") -> str:
    i = text.index(start) + len(start)
    m = re.search(end_pat, text[i:])
    return text[i:i + m.start()] if m else text[i:]

def tables_to_lines(md: str) -> str:
    """좁은 A5 폭에서 3단 표가 깨지므로, 교정쇄에서는 한 사람 한 줄로 푼다(디자이너가 그림 쪽으로 다시 짠다)."""
    out = []
    for line in md.split("\n"):
        if re.match(r"^\|\s*-", line):
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells[0] in ("이름", "지느러미"):
                continue
            if len(cells) == 3 and cells[0].startswith("**"):      # 이름 | 한 줄 | 소품
                out.append(f"{cells[0]} — {cells[1]} *({cells[2]})*\n")
            elif len(cells) == 3:                                  # 그림 | 이름 | 한 줄
                out.append(f"{cells[1]} — {cells[2]}\n")
            elif len(cells) == 2:                                  # 이름 | 하는 일
                out.append(f"**{cells[0]}** — {cells[1]}\n")
            continue
        out.append(line)
    return "\n".join(out)

GROUPS = [
    ("아이들", ["고단우", "양채아", "다원"]),
    ("단우네 집", ["할머니", "엄마"]),
    ("물마루 AI 연구소", ["탁 박사", "봉 소장", "오삼촌"]),
    ("마을과 바다의 어른들", ["미숙", "채아 아빠(관광선 선장)", "해녀회장 김복자", "어촌계장 강덕수", "돌고래쉼표 활동가 윤나래"]),
    ("돌고래", ["불쑥이"]),
]

SPLIT = {
    "채아 아빠(관광선 선장)": ("채아 아빠", "관광선 선장"),
    "해녀회장 김복자": ("김복자", "해녀회장"),
    "어촌계장 강덕수": ("강덕수", "어촌계장"),
    "돌고래쉼표 활동가 윤나래": ("윤나래", "돌고래쉼표"),
}

def tex(s):
    return (s.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%")
             .replace("_", "\\_").replace("#", "\\#"))

def people_page(body):
    """등장인물 소개를 인물사진형 프로필 그리드로 만든다."""
    pdf = r"""\begin{profilepage}
\profileintro
\noindent\makebox[\linewidth][c]{\profilehero{images/portraits/danu.jpg}{고단우}{열두 살 · 6학년}{시민 라벨러 리더보드 1위. 코딩을 좋아한다.}\hspace{2mm}\profilehero{images/portraits/chaea.jpg}{양채아}{열두 살 · 6학년}{‘채아의 돌핀로그’를 하는 단우의 친구.}\hspace{2mm}\profilehero{images/portraits/haan.jpg}{다원}{열한 살 · 5학년}{틀린 데를 잘 찾아내는 미숙의 딸.}}\par\vspace{8mm}
\noindent\makebox[\linewidth][c]{\profilehero{images/portraits/grandma.jpg}{할머니}{해녀}{마지막 물질을 앞둔 해녀. 돌고래를 잘 알아본다.}\hspace{2mm}\profilehero{images/portraits/mom.jpg}{엄마}{간호사}{밤 근무가 많아 단우와 자꾸 엇갈린다.}\hspace{2mm}\profilehero{images/portraits/tak.jpg}{탁 박사}{과학자}{물마루 AI 연구소에서 돌고래 소리를 연구한다.}}
\clearpage
\thispagestyle{plain.scrheadings}
% 두 쪽 펼침에서 첫 인물 페이지와 같은 물리적 조판면을 쓴다.
% 짝수 쪽의 바깥 여백 차이(7mm)를 보정하고, 첫 사진 행 높이도 맞춘다.
\vspace*{-5.5mm}
\begin{center}{\sffamily\color{gray}곰새코지 사람들}\end{center}
\begin{center}{\sffamily\fontsize{8.5pt}{11pt}\selectfont\color{peopleGray}제주 바닷가에 있는 작은 마을, 곰새코지의 사람들입니다.}\end{center}
\vspace{3.5mm}
\noindent\hbox{\kern7mm\makebox[\linewidth][c]{\profilecompact{images/portraits/bong.jpg}{봉 소장}{연구소장}{AI 바당이의 첫 문장을 발표한 사람.}\hspace{2mm}\profilecompact{images/portraits/osamchon.jpg}{오삼촌}{배 조종}{연구소 배를 모는 아저씨. 성이 오씨다.}\hspace{2mm}\profilecompact{images/portraits/tu.jpg}{미숙}{해녀}{다원의 엄마. 곰새코지의 젊은 해녀.}}}\par
\noindent\hbox{\kern7mm\makebox[\linewidth][c]{\profilecompact{images/portraits/chaea-dad.jpg}{채아 아빠}{관광선 선장}{관광선 ‘곰새코지 3호’를 몬다.}\hspace{2mm}\profilecompact{images/portraits/bokja.jpg}{김복자}{해녀회장}{배가 작업장 가까이 오는 걸 싫어한다.}\hspace{2mm}\profilecompact{images/portraits/deoksu.jpg}{강덕수}{어촌계장}{마을 어민 모임의 대표. 항구 확장을 원한다.}}}\par
\noindent\hbox{\kern7mm\makebox[\linewidth][c]{\profilecompact{images/portraits/narae.jpg}{윤나래}{돌고래쉼표}{돌고래 보호 단체 활동가. 개인 방송을 한다.}\hspace{7mm}\profilecompact{images/portraits/bulssugi.jpg}{불쑥이}{돌고래}{카메라 앞에 불쑥 떠오른다.}}}
\end{profilepage}"""
    epub = """#### 아이들

**고단우** (열두 살 · 6학년)  
시민 라벨러 리더보드 1위. 코딩은 유튜브 두 배속으로 배웠다. — *노트북*

**양채아** (열두 살 · 6학년)  
단우네 반 친구. 유튜브 ‘채아의 돌핀로그’를 한다. 구독자 3만. — *휴대폰*

**다원** (열한 살 · 5학년)  
남의 글에서 틀린 데부터 찾아낸다. 미숙의 딸. — *단어 노트*

#### 단우네 집

**할머니**  
단우 할머니. 올해가 마지막 물질인 해녀. 돌고래를 지느러미만 보고 알아본다. — *주황 테왁*

**엄마**  
제주시 병원 간호사. 밤 근무가 많아 단우와 자꾸 엇갈린다. — *간호사 가방*

#### 물마루 AI 연구소

**탁 박사**  
물마루 AI 연구소 과학자. 커피를 ‘연료’라고 부른다. — *머그잔*

**봉 소장**  
물마루 AI 연구소 소장. AI 바당이의 첫 문장을 생중계로 발표했다. — *돌고래 넥타이*

**오삼촌**  
연구소 배를 모는 아저씨. 친척은 아니고, 성이 오씨라서 오삼촌. — *귤*

#### 마을과 바다의 어른들

**미숙**  
다원의 엄마. 곰새코지 해녀들 가운데 가장 젊다. — *고무옷*

**채아 아빠** (관광선 선장)  
돌고래 관광선 ‘곰새코지 3호’를 몬다.

**김복자** (해녀회장)  
해녀들의 회장. 배가 작업장 가까이 오는 걸 싫어한다.

**강덕수** (어촌계장)  
마을 어민 모임의 대표. 항구를 넓히자고 한다.

**윤나래** (돌고래쉼표)  
돌고래 보호 단체 활동가. 개인 방송을 한다.

#### 돌고래

**불쑥이**  
지느러미 끝이 뜯겼다. 카메라 앞에 불쑥 떠오른다.
"""
    return ("::: {.content-visible when-format=\"pdf\"}\n```{=latex}\n"
            + pdf + "\n```\n:::\n\n"
            "::: {.content-visible unless-format=\"pdf\"}\n" + epub + "\n:::\n")

def front():
    t = (MATTER / "front-01-곰새코지-사람들.md").read_text(encoding="utf-8")
    body = section(t, "## A. 쪽 문안 (이 글자만 인쇄한다)")
    body = strip_comments(body)
    body = re.sub(r"\n---\s*$", "", body.rstrip())
    body = re.sub(r"^### 쪽 제목\s*\n+\*\*곰새코지 사람들\*\*\s*\n", "", body.strip())
    body = re.sub(r"^### 1\).*\n", "", body, flags=re.M)              # 디자이너용 묶음 이름 삭제
    body = re.sub(r"^### 2\).*$", "#### 마을 어른들", body, flags=re.M)
    body = re.sub(r"^### 3\).*\n", "", body, flags=re.M)
    body = re.sub(r"^줄 머리: \*\*(.+?)\*\*\s*$", r"#### \1", body, flags=re.M)
    body = body.replace("| 그림 | 이름 | 한 줄 |", "| 지느러미 | 이름 | 한 줄 |")
    (ROOT / "book" / "index.qmd").write_text("# 곰새코지 사람들 {.unnumbered .helper}\n\n" + people_page(body) + "\n", encoding="utf-8")
    img = "images/map.png"
    map_body = ("![](../images/map.png){width=100% fig-alt='곰새코지 바다 지도'}\n" if (ROOT / "book" / img).exists()
                else "::: {.art-slot}\n지도 그림이 들어갈 자리\n:::\n")
    write("front-02-map.qmd", "# 곰새코지 바다 지도 {.unnumbered .helper}\n\n" + map_body)

BACK = [
    ("back-01-곰새코지-탐구-노트.md", "back-01-activities.qmd"),
    ("back-02-진짜-과학-노트.md", "back-02-science.qmd"),
    ("back-03-단우의-메모-용어.md", "back-03-glossary.qmd"),
    ("back-04-단우의-이름-사전.md", "back-04-namebook.qmd"),
    ("back-05-독서토론-질문.md", "back-05-questions.qmd"),
    ("back-06-작가의-말.md", "back-06-afterword.qmd"),
]

def back():
    for src, dst in BACK:
        t = strip_comments((MATTER / src).read_text(encoding="utf-8"))
        t = remap_chapter_references(t)
        lines = t.split("\n")
        assert lines[0].startswith("# ")
        lines[0] = lines[0] + " {.unnumbered .backmatter}"
        t = "\n".join(lines)
        t = re.sub(r"\n---\n", "\n", t)                 # 구분선은 조판에서 여백으로
        t = re.sub(r"\{\{([^}]*)\}\}", r"[[\1]]", t)     # 자리표시를 눈에 띄게(교정쇄 전용)
        write(dst, t)

def colophon():
    """판권면. 확정된 값만 적고, 미정 값은 [[ ]]로 드러낸다(교정쇄 전용 — 인쇄본에 [[ ]]가 남으면 안 됨)."""
    write("back-99-colophon.qmd", """# 판권 {.unnumbered .unlisted .colophon}

**곰새코지 돌고래 목소리 사건**

[[초판 1쇄 발행일]]

지은이 이희근\\
그린이 [[삽화가 이름]]\\
펴낸곳 에르고스피어\\
[[출판사 신고번호 · 주소 · 전자우편]]

ISBN [[종이책 ISBN — 발급 전]]\\
값 14,000원

[[AI 활용 고지 문구 — 결정 전]]

이 책에 나오는 사람, 기관, 마을, 바다 이름은 지어낸 것입니다.
""")

if __name__ == "__main__":
    if SRC.exists():
        shutil.rmtree(SRC)
    SRC.mkdir(parents=True)
    chapters(); front(); back(); colophon()
    print("synced:", sorted(p.name for p in SRC.iterdir()))
