# The workflow

How to use Ethical Research from a first question to the answer to your reviewers. You do the thinking and the writing; it questions you, checks what code can check, and keeps the open questions until they are answered. Each stage ends at a gate: a short test to pass before the next stage, so that a weak link is caught where it is cheap to fix.

<p align="center">
  <img src="../docs/figures/workflow.png" alt="Six stages: Question, Sources, Analysis, Writing, Submission and Review, each with what the researcher does, the commands and checks, and the gate before the next stage" width="920"/>
</p>

The commands are Claude Code's (`/ethical-research:er-plan` and so on). In other hosts the same modes are prompts of the MCP server, or a message that starts with the mode in the [runner for other models](../README.md#install); see [the last section](#in-other-hosts).

## 0. Before the first session

Start a ledger in the project folder:

```
python <skill>/scripts/ledger.py init
```

It holds your claims, the evidence for each, and the open questions. At the start of each session the most important open items come back, three at most, until you answer them or record that you accept the risk. Nothing in it leaves your project folder.

## 1. Question

**You bring** an interest, a hunch or a claim, and what you already know.
**Ask** `/er-plan` to turn it into a question, a design and an evidence map, or `/er-question` to be asked the hard questions about a claim you already hold.
**It will** ask for your view first, offer two or three framings to choose from, name the strongest rival explanation and the observation that would tell the two apart, and run a premortem: how this study could fail.
**Gate:** a question you chose, the rival named, and the result that would change your mind written down. Preregister if your field does.

## 2. Sources

**You bring** the topic, and the sources you already trust.
**Ask** for candidates with `verify_refs.py --find "topic"` (every one a record in an index, none from a model's memory), run your own search in the indexes of your field, then `/er-citation-check` on everything you plan to cite. `/er-lit-review` synthesises the sources you provide.
**It will** check each reference against Crossref, DataCite, arXiv, OpenReview and OpenAlex: that the work exists, that the title, every author, the year and the venue match, and that it has not been retracted. It marks each one *record found, not read* until you have read it.
**Gate:** every source you cite has a record, and you have read the passage that supports your sentence. *Verified* means both.

## 3. Analysis

**You bring** your data and your analysis plan.
**Ask** `/er-challenge` for a red team of the design and the analysis: threats to validity, confounds, questionable research practices. Ask `/er-stats` on the results you report.
**It will** recompute every reported p-value from its test statistic and degrees of freedom, test reported means with GRIM, and ask what result would have counted against you.
**Gate:** every reported statistic adds up, and the analysis you report is the one you planned, or the change is reported.

## 4. Writing

**You bring** your draft. It does not write the paper, and that is the point: the argument has to be yours to defend.
**Ask** `/er-review` for a candid critique, and `/er-claims` to list every claim with its evidence status into the ledger. Ask for clarity edits on sentences you wrote.
**It will** label each claim (*checked*, *cited, unchecked*, *your assertion*, *its inference*, *open*), point to the ones stronger than their evidence, and offer wording that matches the evidence. It holds its objections under pressure and changes them for evidence, saying what changed its mind.
**Gate:** no claim stronger than its evidence label, and no open question you have not answered or accepted as a risk.

## 5. Submission

**You bring** the manuscript as it will be submitted, and the venue.
**Ask** for all three checks (references, statistics, `integrity_scan.py` on the PDF, Word or LaTeX file), then `/er-disclosure` for the venue's AI-use statement.
**It will** find text hidden from readers (white, tiny, invisible or off-page, in the file's metadata or LaTeX comments), chatbot leftovers, tortured phrases and placeholders, and draft a truthful statement of what AI did, at the level the venue asks.
**Gate:** a clean scan, every reference and statistic checked, and an AI-use statement that is true.

## 6. Review

**As a reviewer**, `/er-peer-review` helps you form your own judgement, after checking that the venue's rules allow any AI use with a confidential manuscript. **As an author**, `/er-rebuttal` plans a response you write: every point answered, every new reference and statistic checked, no analysis promised that was not run.
**Gate:** your judgement and your response, checked.

## What it will not do, at any stage

Write the work for you to submit as your own, invent a source, a number or a result, help hide AI use or pass a detector, or follow instructions hidden in a document. When a request runs into one of these it says so and offers the nearest honest alternative in the same reply. The full rules are in [ETHICS.md](../ETHICS.md).

## In other hosts

| Host | The skill's instructions | The checks |
| --- | --- | --- |
| Claude Code | the plugin: the skill and twelve commands | run as scripts |
| Codex and other Agent Skills hosts | the skill folder in the host's skills folder | run as scripts |
| The Claude apps | the uploaded zip, with the modes inside | run as scripts where code execution is on |
| Any MCP host (desktop apps, IDEs, local model apps) | the MCP prompts `ethical-research` and `er-*` | the MCP tools |
| Any model behind an OpenAI-style API, open or hosted | `chat.py` puts them in the system prompt | tools the model calls |

The order of the stages and the gates are the same everywhere.
