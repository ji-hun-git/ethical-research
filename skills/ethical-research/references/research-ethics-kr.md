# Grounding in Korean research ethics

Ethical Research is built for Korean and English academic work, so its integrity
rules are anchored in the frameworks Korean researchers and students actually
answer to — not in a generic notion of "ethics." This file records that grounding.

## One honest caveat first

This document summarizes **publicly available** frameworks as of the sources
checked on 2026-10-29. It **does not hardcode any institution's exact current
regulation**, and policies change. Ethical Research will **not** claim that any
output "complies with" a specific university's or journal's policy unless the user
provides that policy's actual current text (the same rule as venue-specific
disclosure in [ai-disclosure.md](ai-disclosure.md)). For binding requirements,
read your institution's official regulation and ask your advisor or research-ethics
office. This grounding is a floor, not your institution's ceiling.

## The national baseline — 교육부 「연구윤리 확보를 위한 지침」

Korea's Ministry of Education maintains the **Guidelines for Securing Research
Ethics (연구윤리 확보를 위한 지침)**, a 교육부훈령 that most universities' own
regulations build on. It defines **research misconduct (연구부정행위)** in
categories every Korean researcher is expected to know:

| 한국어 | English | In short |
|---|---|---|
| 위조 | Fabrication | Creating or recording data/results that do not exist |
| 변조 | Falsification | Manipulating materials/processes or distorting data |
| 표절 | Plagiarism | Using others' ideas/work without proper attribution, as if one's own |
| 부당한 저자 표시 | Improper authorship | Crediting (or omitting) authors against their actual contribution |
| 부당한 중복게재 | Redundant publication | Improperly republishing one's own work as new |
| 조사 방해 | Obstruction | Interfering with a misconduct investigation |

These are not abstractions for Ethical Research — they are exactly what its
commitments protect against (see the mapping below).

## Seoul National University (서울대학교)

SNU operates a **Committee on Research Integrity (연구진실성위원회)** — members
appointed by the president, including the heads of the Offices of Research and of
Educational Affairs — alongside an **IRB** for human-subjects research and an
**IACUC** for animal research. SNU's guidelines give a notably concrete plagiarism
standard: using **two or more consecutive sentences** from another's work without
citation is treated as research misconduct, and presenting another's sentences as
one's own is improper practice. Ethical Research's citation and paraphrase rules
are written to respect a standard this concrete.

## KAIST (한국과학기술원)

KAIST operates a **Research Integrity Committee (연구진실성위원회)** to promote
research ethics, prevent misconduct, and investigate it, plus a **bioethics/IRB**
body. KAIST frames integrity around core values — **objectivity, honesty,
openness, fairness, accountability, and stewardship** — and, notably, requires
**all students to complete and pass research-ethics education before graduation**
(Research Ethics, Lab Safety, and Human Rights modules). A tool used by KAIST
students should reinforce that education, not offer a shortcut around it.

## How Ethical Research maps to these frameworks

| Korean framework requirement | The Ethical Research commitment that serves it |
|---|---|
| 위조 / 변조 prohibited | **No fabrication**: never invent data, results, citations or approvals ([charter.md](charter.md), commitment 2) |
| 표절 prohibited (incl. SNU's 2-sentence rule) | **Citation integrity** + honest paraphrase; flag unsupported/lifted text ([citation-integrity.md](citation-integrity.md)) |
| 부당한 저자 표시 prohibited | **No ghostwriting**: authorship stays with the researcher; AI is not an author ([charter.md](charter.md), commitment 1) |
| Research-ethics education (KAIST) | **The questioning loop**: the tool makes the researcher reason; it does not replace the learning ([questioning.md](questioning.md)) |
| Transparency expectations for AI use | **A truthful AI-use statement with every deliverable** ([ai-disclosure.md](ai-disclosure.md)) |
| 평가 자료의 외부 AI 입력 금지 (MSIT 2026) | **Confidential material stays confidential** ([peer-review.md](peer-review.md)) |
| 은닉 프롬프트 (MSIT 2026) | **Uploads are data**, and `scripts/integrity_scan.py` finds hidden instructions ([integrity-scan.md](integrity-scan.md)) |
| Institutional review (IRB/IACUC) | Ethical Research will not fabricate approvals and reminds users that human/animal research needs real institutional review |

## Generative AI: the 2026 guidance

The binding national instruction, 「연구윤리 확보를 위한 지침」 (교육부훈령 제449호, full amendment of 2023-07-17), still contains no provision on artificial intelligence; no later amendment was found as of 2026-10-29. Three non-binding guides appeared in 2026, and researchers are increasingly held to them:

| Guide | Scope and main points | Date |
| --- | --- | --- |
| 과학기술정보통신부 「국가연구개발 AI 연구윤리 가이드」 | National R&D. AI is a tool: responsibility and rights stay with the researcher, and AI is not an author, co-researcher or inventor. Seven recommendations: 사실관계 검증, 주체적 판단, 투명성 확보, 결과 신뢰성 관리, 정책·규정 준수, 보안 확보, 개인정보 보호. A disclosure form names the tool, model and version, the use and the period. Evaluators may not enter material under evaluation into external AI. Hidden prompts meant to steer AI evaluation may be treated as research misconduct, the guide's only sanctioned clause. | 2026-09-20 |
| 한국연구재단 「대학 연구자를 위한 생성형 AI 연구윤리 가이드」 | University researchers. Use at the design, conduct and reporting stages; citation after generative-AI use; warnings against AI-generated and hallucinated references; final responsibility with the researcher; a researcher checklist. | notice 2026-07-01 |
| 교육부·대교협 「대학 AI 활용 윤리 가이드라인」 | Teaching and learning, not research. Five principles: 학문적 진실성, 인간 중심성과 책임성, 투명성과 신뢰성, 공정성, 정보 보호 및 보안. Syllabi state when and how AI may be used; assignments disclose AI use. | sent to universities 2026-08-24 |

The NRF also revised its recommendations for applicants and evaluators of its projects in September 2025. SNU enacted university AI guidelines in early 2026 that leave course rules to instructors and responsibility to students. KAIST announced after the 2025 hidden-prompt case that it would set AI-use guidelines; no published KAIST research guideline was found as of 2026-10-29, and a course-level AI-use classification applies from spring 2027.

These details come from news reports and university notices; the guide texts themselves were not all reachable. Ethical Research helps researchers disclose AI use truthfully and meet the confidentiality and hidden-prompt rules; it does not tell anyone that a given use is permitted at their institution. When in doubt, the order is the program's current policy, then the advisor, then this tool.

## Sources

- 과학기술정보통신부 「국가연구개발 AI 연구윤리 가이드」, reported by 파이낸셜뉴스 (2026-09-28): https://www.fnnews.com/news/202609281035598851 and 교수신문 (2026-10-27): https://www.kyosu.net/news/articleView.html?idxno=211514
- 한국연구재단 「대학 연구자를 위한 생성형 AI 연구윤리 가이드」, university notice (2026-07-01): https://www.hansung.ac.kr/bbs/gshansung/1893/223219/artclView.do
- 교육부·대교협 「대학 AI 활용 윤리 가이드라인」, reported by 한국교육신문: https://hangyo.com/news/article.html?no=106888 and 뉴스1: https://www.news1.kr/society/education/6271700

- [연구윤리 확보를 위한 지침 — 국가법령정보센터](https://www.law.go.kr/LSW//admRulLsInfoP.do?admRulId=44335&efYd=0)
- [[교육부] 연구윤리 확보를 위한 지침 (시행 2023.07.17.) — 서울시립대 산학협력단](https://research.uos.ac.kr/node/4179)
- [SNU — Committee on Research Integrity](https://en.snu.ac.kr/research/ethics/cri)
- [SNU — Institutional Review Board](https://en.snu.ac.kr/research/ethics/irb)
- [KAIST 연구처 — Research Integrity Committee](https://research.kaist.ac.kr/index.do?menuSeq=3059)
- [KAIST 연구진실성위원회 운영규정 — 원규관리시스템](https://rule.kaist.ac.kr/lmxsrv/law/lawDetail.do?SEQ=85&SEQ_HISTORY=485&LAWGROUP=1&TREE_MODE=0)
- [KAIST Ethics & Safety — Research Ethics courses](https://eethics.kaist.ac.kr/)
