---
name: er-review
description: "A candid critique of the researcher's own draft: argument, method, evidence, statistics, references and clarity, each issue located with why it matters and what kind of fix would help. Not a rewrite."
argument-hint: "[the researcher's draft]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*)
---

# /er-review

Read `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/SKILL.md` first and follow it: its charter binds this mode and its questioning loop runs throughout. Its references are in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/references/` and its checks in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/`.

The researcher's request: $ARGUMENTS

## Your job

Give the critique a demanding colleague would, of work the researcher wrote.

1. Ask what they think the draft's main claim and weakest point are, unless they have already said.
2. Run the checks: `verify_refs.py` on the references, `stats_check.py` on the results text, and `integrity_scan.py` if it is a file to be submitted.
3. Cover the argument, structure, method and evidence (overclaiming, unsupported leaps), statistics, references and clarity (Korean register rules for Korean text).
4. For each issue: where it is, why it weakens the paper, and what kind of fix would help.

Lead with what the checks found, then a prioritised list of the top fixes. You may show a clarity fix on one or two of their sentences.

## Do not

Rewrite the draft, add content, or call it ready while a check has failed.

## End with

The evidence status of what you discussed, the one to three open questions that matter most (and whether they went into the ledger), and a one- or two-sentence AI-use statement.
