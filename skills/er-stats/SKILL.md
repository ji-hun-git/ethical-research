---
name: er-stats
description: "Check reported statistics for internal consistency: recompute p-values for APA-style t, F, chi-square, r and z results and test reported means with GRIM, then raise each inconsistency as a question for the author."
argument-hint: "[a results section or the statistics to check]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*)
---

# /er-stats

Read `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/SKILL.md` first and follow it: its charter binds this mode and its questioning loop runs throughout. Its references are in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/references/` and its checks in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/`.

The researcher's request: $ARGUMENTS

## Your job

1. Save the text and run `python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/stats_check.py results.txt`. For means of integer data, also run `--grim <mean> <n> [items]`, after asking what the measure is.
2. Report each inconsistency as "inconsistent at the reported precision" with the recomputed value, and each decision error first. "Check by hand" means a correction is mentioned that the recomputation ignores.
3. Ask the researcher to check their analysis output; suggest the likely causes (typo, a different test, a one-tailed or corrected p).

Read [statistics.md](../ethical-research/references/statistics.md) for what the checks can and cannot show.

## Do not

Correct a number yourself, accuse anyone, or call results sound because the numbers are consistent: consistency is not validity.

## End with

The evidence status of what you discussed, the one to three open questions that matter most (and whether they went into the ledger), and a one- or two-sentence AI-use statement.
