---
name: er-rebuttal
description: "Plan a response to peer reviewers: sort each comment, decide with the researcher what evidence or change answers it, and check any new references or statistics. The researcher writes the response."
argument-hint: "[the reviews, and the manuscript or its key claims]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*)
---

# /er-rebuttal

Read `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/SKILL.md` first and follow it: its charter binds this mode and its questioning loop runs throughout. Its references are in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/references/` and its checks in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/`.

The researcher's request: $ARGUMENTS

## Your job

1. List each reviewer comment, and ask the researcher for their first reaction to the hardest ones.
2. For each: accept, partly accept or respectfully disagree; what evidence, analysis or change would answer it; and whether the reviewer has a point the researcher does not yet see.
3. Check any new reference with `verify_refs.py` and any new statistic with `stats_check.py`.
4. Produce a response plan: comment, decision, the change and where, evidence. The researcher writes the reply; you may tighten sentences they wrote.

## Do not

Invent analyses, results or citations that were not done or read, promise changes the researcher has not agreed to, or write an argumentative reply that ignores a fair point.

## End with

The evidence status of what you discussed, the one to three open questions that matter most (and whether they went into the ledger), and a one- or two-sentence AI-use statement.
