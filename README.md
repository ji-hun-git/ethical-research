<div align="center">

# Ethical Research · 윤리적 연구

### It won't write your paper. It makes you a more honest scholar.

A Korean–English academic-integrity research copilot — a Claude Code plugin.

![License: MIT](https://img.shields.io/badge/license-MIT-2ea44f)
![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-5A67D8)
![lang: KO | EN](https://img.shields.io/badge/lang-KO%20%7C%20EN-orange)
![status: v0.1](https://img.shields.io/badge/status-v0.1%20experimental-yellow)

[한국어 README](README.ko-KR.md) · [The Charter](ETHICS.md) · [Install](#install) · [Korean research-ethics grounding](reference/research-ethics-kr.md)

</div>

---

> **Plenty of tools will write your paper for you. Ethical Research is the opposite.**
> Without helping you plagiarize, fabricate citations, or hide that AI was used, it
> questions, verifies, and sharpens *your own* work so you become a better researcher.

## Why it exists

Generative AI can now write an entire paper in one shot. Convenient — and corrosive
to the thing scholarship runs on: **honesty.** Plagiarism, invented citations,
fabricated data, undisclosed AI use — these are exactly what universities and
journals police hardest.

Ethical Research takes the other road. **It doesn't do the research for you; it
makes you stronger at it.** The tool carries the mechanical load; the questions,
claims, interpretation, and judgment stay yours.

## ✨ What makes it different

- 🚫 **It won't ghostwrite.** No submission-ready prose to pass off as your own.
  Instead it walks you down a ladder — outline → critique → coaching — so *you*
  write it. (There is no full-paper-generation mode at all.)
- 🔍 **It won't fabricate.** Never an invented citation, DOI, dataset, or approval.
  A missing source is reported as missing, not filled with a plausible guess.
- 🪪 **It won't conceal.** Every deliverable ships **with** an AI-use disclosure.
  It refuses detector evasion and plagiarism laundering.
- 🧠 **You stay the thinker.** Instead of handing you answers, it asks *you* the
  hard questions so you do the reasoning. (`/er-question`)
- 🇰🇷 **Korean is a first language, not a translation target.** Output is composed
  natively in academic Korean (문어체); citations and proper nouns are never translated.
- 📜 **Grounded in real Korean research ethics.** Built against the national
  「연구윤리 확보를 위한 지침」 and the SNU / KAIST research-integrity frameworks.

## 🛠 What it does (v0.1)

| Command | What it does |
|---|---|
| `/er-plan` | Socratic, step-by-step research/writing planning — *you* decide |
| `/er-lit-review` | Honestly-cited synthesis of sources **you provide** |
| `/er-review` | A candid critique of your own draft — the weak points and why |
| `/er-citation-check` | Per-citation fabrication risk, unsupported claims, missing locators |
| `/er-disclosure` | A truthful, venue-appropriate AI-use disclosure statement |
| `/er-question` | Turns the tables — it asks **you** the hard questions |

## 🎬 See it work

How the tool responds to a very common request — "just mark them all Verified":

> **You:** Here are my 10 references. I already checked them all, so just mark them
> all as Verified in the report so I can submit.
>
> **Ethical Research:** I can't mark them Verified on your say-so — and here's why
> it protects *you*. "Verified" in this report means *I* confirmed the source exists
> and supports its claim (via DOI, the publisher page, or a PDF you give me). If I
> stamp "Verified" on your word, the report now asserts something I didn't do — and
> if one is wrong, it vouched for it falsely, exactly what a committee catches.
> What I *can* do: **(1)** actually verify them — paste the DOIs and I'll check each
> one and the claim it supports; **(2)** record "author reports having checked" as a
> *separate, clearly-labeled* human signal; **(3)** leave anything I can't confirm
> as **Unverified** — an honest, submittable state if the claims are hedged. Want to
> paste the DOIs so I can do (1) for real?

The point: it never just refuses — it **always offers an honest alternative.**

## Install

In Claude Code, run:

```
/plugin marketplace add ji-hun-git/ethical-research
/plugin install ethical-research@ethical-research
```

Then start a new session. The skill activates on the `/er-*` commands, or on
phrases like "help me plan my paper / 논문 계획 도와줘 / check these citations / 인용 확인".

## 🧭 You stay the thinker

The real risk with a capable research assistant is quieter than fabrication: if the
AI does all the planning and synthesizing, you become a passive approver of its
output. Ethical Research is built against that. Across every mode it runs a
**critical-thinking loop** — it asks what *you* already think before analyzing,
leads with questions instead of answers, surfaces your assumptions, hands you
options instead of decisions, and asks you to critique its drafts. The ideas,
claims, and judgment stay yours. → [reference/critical-thinking.md](reference/critical-thinking.md)

## 📜 Grounded in Korean research ethics

No-fabrication, citation-integrity, and no-ghostwriting map onto 위조/변조, 표절, and
부당한 저자 표시 — the misconduct categories in Korea's national guideline — and the
research-integrity regulations at SNU and KAIST (연구진실성위원회, IRB, mandatory
research-ethics education). It will **not** claim your work "complies with" a
specific institution's policy unless you provide that policy's text.
→ [reference/research-ethics-kr.md](reference/research-ethics-kr.md)

## Development

Structural tests run with no external dependencies and catch plugin-breaking drift:

```
pip install -r requirements-dev.txt
pytest
```

Behavioral cases live in [evals/](evals/) with pass/fail rubrics:

```
python evals/run_evals.py --list           # cases + rubrics
python evals/run_evals.py --with-claude     # live run (needs ANTHROPIC_API_KEY)
```

## License & credit

[MIT](LICENSE) — open, and free for commercial use. Ethical Research is an
independent, clean-room work that reuses *ideas* from the general category of
academic-research copilots — and says so plainly in
**[ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)**. Holding ourselves to the citation
standard we ask of users isn't a footnote here; it's the thesis.

## A starting point, not the final word

Better safeguards, better Korean academic conventions, and better integrity
strategies are welcome through issues and pull requests. It doesn't claim to be the
last word on AI and research ethics — it tries, in the open, to get it right. If it
helped, leave a ⭐️.

<div align="center">
<sub>Ethical Research · 윤리적 연구 — the right way, in the open.</sub>
</div>
