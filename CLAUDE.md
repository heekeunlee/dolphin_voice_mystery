# book_publish — 초등 고학년 장편 동화 출간 프로젝트

> **새 세션은 먼저 `HANDOFF.md`(현재 상태·결정 이력·파일 지도·남은 일)를 읽는다.** 현재 6단계(조판) 교정쇄 204쪽, 그림은 사용자가 직접 그림.

**초등 고학년(5~6학년)** 독자를 위한, 재미 + 교육적 가치를 갖춘 **장편 시리즈 1권**을 기획·집필해
교보문고 POD 종이책, 국내 전자책, Google Play Books·Amazon KDP(영문)로 출간하는 것이 목표다.

- 벤치마크: 『시간 고양이』(박미연, 이지북) — 분석만 하고 설정·캐릭터·플롯은 차용하지 않는다.
- 출판 주체: 1인 출판사 **에르고스피어**, ISBN 직접 발급 경로 (`heekeunlee/book_publish_process` 참조).
- 서브에이전트: `heekeunlee/fairy_tale`(동화공방) 8인 크루를 가져와 장편용으로 운용한다.
  `.claude/agents/`의 정의는 단편 동화 기준이므로, 장편에서는 아래 단계 규칙을 우선한다.

## 단계 (각 단계 끝에서 사람이 승인해야 다음으로 진행)

| 단계 | 내용 | 담당 | 산출물 |
|---|---|---|---|
| 1 | 시장·독자 조사, 출판 경로 전략 | researcher | `research/`, `strategy/` |
| 2 | 콘셉트 3안 → 1안 선정 | planner + critic + advisor | `planning/*-concepts.md` |
| 3 | 시리즈 바이블(세계관·인물·톤) + 1권 장별 아웃라인 | planner | `planning/` |
| 4 | 장 단위 집필 → 심사 → 퇴고 반복 | writer ↔ critic, advisor | `drafts/`, `reviews/`, `advisory/` |
| 5 | 유사성·저작권 점검, 교정 | researcher, admin | `research/`, `admin/` |
| 6 | 조판(Quarto A5 POD/EPUB), 표지, ISBN·바코드 | designer + `quarto-korean-pod-book` 스킬 | `book/` |
| 7 | 유통 등록(교보 POD, 전자책, GPB, KDP), 영문판 | marketer + `korean-indie-publishing` 스킬 | `marketing/` |

## 파일 명명

- 조사: `research/{YYYY-MM-DD}-{주제}.md` / 전략: `strategy/{YYYY-MM-DD}-{주제}.md`
- 기획: `planning/{YYYY-MM-DD}-{슬러그}.md`
- 장편 초고: `drafts/{슬러그}/ch{NN}-v{버전}.md`, 심사: `reviews/{슬러그}/ch{NN}-v{버전}-review.md`

## 원칙

- 목표 독자: 초등 5~6학년이 혼자 읽고 이해·몰입하는 것이 1순위 기준이다(2026-10-03 변경, 성인 크로스오버 목표 폐기). 4학년은 도전 독자, 부모·교사는 함께 읽는 보조 독자.
- 각 장은 집필 → `tools/readability.py` 측정 → 이해도 점검(5학년 독자 시뮬) → 심사·고문 → 퇴고 → 확정 순서로 진행한다.

- 설교 대신 사건과 행동으로 메시지를 전달한다 (동화공방 톤 유지).
- 확인 못 한 사실은 지어내지 않는다. 출처를 남긴다.
- 원고 공개 저장소 push는 사용자 승인 후에만 한다.
