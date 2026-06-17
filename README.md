<div align="center">

<img src="assets/banner-en.svg" alt="Ethical Research" width="100%">

<br>

![License: MIT](https://img.shields.io/badge/license-MIT-2ea44f?style=flat-square)
![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-5A67D8?style=flat-square)
![status: v0.1](https://img.shields.io/badge/status-v0.1%20experimental-d9a441?style=flat-square)

**[Read in Korean &#8594;](README.ko-KR.md)**  ·  [The Charter](ETHICS.md)  ·  [Install](#install)

</div>

---

> **Plenty of tools will write your paper for you. This one refuses.**
> It questions, verifies, and sharpens *your own* work — without helping you
> plagiarize, fabricate citations, or hide that AI was involved.

## Why it exists

Generative AI can write a whole paper in one shot. Convenient — and corrosive to
the thing scholarship runs on: **honesty.** Invented citations, fabricated data,
quiet AI use, plagiarism dressed up to dodge detectors — these are exactly what
universities and journals police hardest.

Ethical Research takes the other road. It doesn't do the work for you; it makes you
better at it. The tool carries the mechanical load — the questions, claims, and
judgment stay yours.

## Most AI tools vs. Ethical Research

|  | A typical AI writing tool | **Ethical Research** |
|---|:---|:---|
| **Produces a ready-to-submit paper** | Yes — that's the selling point | **No — it coaches you to write it** |
| **Citations** | May invent plausible ones | **Verifies them, or labels "unverified"** |
| **AI-use disclosure** | Hidden or optional | **Ships with every output** |
| **Your role** | Approve what it generated | **Do the thinking and own the work** |
| **Korean** | Machine-translated | **Composed natively** |

## What it does

| Command | What it does |
|---|---|
| `/er-plan` | Socratic, step-by-step research and writing planning — *you* decide |
| `/er-lit-review` | An honestly-cited synthesis of sources **you provide** |
| `/er-review` | A candid critique of your own draft — the weak points, and why |
| `/er-citation-check` | Per-citation fabrication risk, unsupported claims, missing locators |
| `/er-disclosure` | A truthful, venue-appropriate AI-use disclosure statement |
| `/er-question` | Turns the tables — it asks **you** the hard questions |

Every substantive output ships **with** an AI-use disclosure. You can't get the
help without the honesty.

## See it work

What happens when you ask it to cut a corner:

> **You** — Here are my 10 references. I already checked them all, so just mark them
> all as Verified in the report so I can submit.
>
> **Ethical Research** — I can't mark them Verified on your say-so, and here's why
> it protects *you*. "Verified" means *I* confirmed the source exists and supports
> its claim — via a DOI, the publisher page, or a PDF you give me. If I stamp it on
> your word, the report now asserts something I didn't do, and if one is wrong it
> vouched for it falsely — exactly what a committee catches.
> What I can do instead: **(1)** actually verify them — paste the DOIs and I'll check
> each one and the claim it supports; **(2)** record "author reports having checked"
> as a *separate, clearly-labeled* human signal; **(3)** leave anything I can't
> confirm as **Unverified** — an honest, submittable state if the claims are hedged.
> Want to paste the DOIs so I can do (1) for real?

It never just refuses — it **always offers an honest alternative.**

## Install

In Claude Code, run:

```
/plugin marketplace add ji-hun-git/ethical-research
/plugin install ethical-research@ethical-research
```

Then start a new session. The skill activates on the `/er-*` commands, or on
phrases like "help me plan my paper" or "check these citations."

## You stay the thinker

The real risk with a capable assistant is quieter than fabrication: if the AI does
all the planning and synthesizing, you become a passive approver of its output.
Ethical Research is built against that. Across every mode it runs a
**critical-thinking loop** — it asks what *you* already think before analyzing,
leads with questions instead of answers, surfaces your assumptions, hands you
options instead of decisions, and asks you to critique its drafts. The ideas,
claims, and judgment stay yours.
→ [reference/critical-thinking.md](reference/critical-thinking.md)

## Grounded in real research ethics

Its rules map onto the misconduct categories in Korea's national research-ethics
guideline — fabrication, falsification, plagiarism, and improper authorship — and
the research-integrity frameworks at Seoul National University and KAIST
(integrity committees, IRB review, mandatory research-ethics education). It will
**not** claim your work "complies with" a specific institution's policy unless you
provide that policy's text.
→ [reference/research-ethics-kr.md](reference/research-ethics-kr.md)

## Development

Structural tests run with no external dependencies and catch plugin-breaking drift:

```
pip install -r requirements-dev.txt
pytest
```

Behavioral cases live in [evals/](evals/) with pass/fail rubrics:

```
python evals/run_evals.py --list           # cases and rubrics
python evals/run_evals.py --with-claude     # live run (needs ANTHROPIC_API_KEY)
```

## License and credit

[MIT](LICENSE) — open, and free for commercial use. Ethical Research is an
independent, clean-room work that reuses *ideas* from the general category of
academic-research copilots, and says so plainly in
**[ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)**. Holding ourselves to the citation
standard we ask of users isn't a footnote here; it's the thesis.

## A starting point, not the final word

Better safeguards, better academic conventions, and better integrity strategies
are welcome through issues and pull requests. It doesn't claim to be the last word
on AI and research ethics — it tries, in the open, to get it right. If it helped,
leave a star.

<div align="center">
<br>
<sub>Ethical Research — the right way, in the open.</sub>
</div>
