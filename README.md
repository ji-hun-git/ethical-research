# Ethical Research · 윤리적 연구

*A Korean–English academic-integrity research copilot for Claude Code.*

> Help that makes you a more honest scholar — never a ghostwriter that covers its tracks.

Ethical Research is a Claude Code skill that helps Korean- and English-speaking
researchers and students **plan, review, verify, and improve** academic work —
while refusing to ghostwrite it, fabricate sources, hide AI use, or help anyone
defeat an integrity check.

It is built on a simple stance: a research tool should make *you* a better,
more honest scholar, not replace you and cover its tracks.

**Languages:** 한국어 · English · [한국어 README](README.ko-KR.md)
**Status:** v0.1 — experimental. Not legal, academic, or institutional advice.
**License:** [MIT](LICENSE) — open, and free for commercial use.

---

## What it does (v0.1)

Ethical Research deliberately ships a small, safe set of capabilities. There is **no
full-paper-generation mode** — that is the point.

| Command | What it does |
|---|---|
| `/er-plan` | Socratic, chapter-by-chapter research/writing planning. Helps you decide; never decides for you. |
| `/er-lit-review` | Annotated, honestly-cited synthesis of sources **you provide**. |
| `/er-review` | A candid critique of your own draft — finds the weak points and explains them. |
| `/er-citation-check` | Goes through your citations and flags fabrication risk, unsupported claims, and missing locators. |
| `/er-disclosure` | Drafts a truthful, venue-appropriate AI-use disclosure statement. |
| `/er-question` | Turns the tables — the assistant asks **you** the hard questions to sharpen your own thinking. |

Every substantive output ships **with** an AI-use disclosure statement. You can't
get the help without the honesty.

## You stay the thinker

The real risk with a capable research assistant is quieter than fabrication: if
the AI does all the planning and synthesizing, you become a passive approver of
its output. Ethical Research is built against that. Across every mode it runs a
**critical-thinking loop** — it asks what *you* already think before it analyzes,
leads with questions instead of answers, surfaces your assumptions, hands you
options instead of decisions, and asks you to critique its drafts. It does the
mechanical lifting; the ideas, claims, and judgment stay yours. The `/er-question`
mode exists purely for this. See
[reference/critical-thinking.md](reference/critical-thinking.md).

## What it will not do

Refuse ghostwriting · refuse fabricated citations/data/approvals · refuse
AI-detector evasion · refuse plagiarism laundering · refuse to claim it read
sources it didn't. See **[the Ethical Research Charter](ETHICS.md)** for the full set of
commitments and the "decline → useful alternative" table.

## Why Korean–English specifically

Most academic AI tooling treats Korean as a translation target — write in
English, machine-translate out. Ethical Research treats Korean as a **first language to
compose in.** Its output follows real academic Korean register (문어체 declarative
style, proper hedging and 논증 connectives), never translates citations or proper
nouns, and can produce side-by-side Korean/English when you ask. See
[reference/korean-academic-register.md](reference/korean-academic-register.md)
and [reference/korean-glossary.md](reference/korean-glossary.md).

## Grounded in Korean research ethics

Its rules are anchored in the frameworks Korean researchers actually answer to —
the national 「연구윤리 확보를 위한 지침」 and the research-integrity regulations at
SNU and KAIST (연구진실성위원회, IRB, mandatory research-ethics education). No
fabrication, citation integrity, and no ghostwriting map onto 위조/변조, 표절, and
부당한 저자 표시 respectively. It will not, however, claim your work "complies with"
a specific institution's policy unless you give it that policy's text. See
[reference/research-ethics-kr.md](reference/research-ethics-kr.md).

## Install (Claude Code)

In Claude Code, run:

```
/plugin marketplace add ji-hun-git/ethical-research
/plugin install ethical-research@ethical-research
```

Then start a new session. The skill activates on phrases like "help me plan my
paper / 논문 계획 도와줘 / check these citations / 인용 확인", or via the `/er-*`
commands above.

## Origin & credit

Ethical Research is an independent, clean-room work (MIT licensed). It reuses *ideas* from
the general category of academic-research copilots — and says so plainly. See
**[ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)**. Holding ourselves to the citation
standard we ask of users is not a footnote here; it's the thesis.

## Development

Structural tests run with no external dependencies and catch plugin-breaking
drift (broken reference links, commands missing from the router, a charter that
lost a commitment):

```
pip install -r requirements-dev.txt
pytest
```

Behavioral cases live in [evals/](evals/) with pass/fail rubrics:

```
python evals/run_evals.py --list           # cases + rubrics
python evals/run_evals.py --with-claude     # live run (needs ANTHROPIC_API_KEY)
```

## This is a starting point, not the final word

Ethical Research is an evolving project. Better safeguards, better Korean academic
conventions, and better integrity strategies are welcome through issues and pull
requests. It does not claim to be the last word on AI and research ethics — it
claims to try, in the open, to get it right.
