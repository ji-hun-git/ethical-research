---
name: er-claims
description: "List every substantive claim in a draft with the evidence it has, label each claim's evidence status, flag wording stronger than the design allows, and record it all in the research ledger."
argument-hint: "[a draft or section]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*)
---

# /er-claims

Read `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/SKILL.md` first and follow it: its charter binds this mode and its questioning loop runs throughout. Its references are in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/references/` and its checks in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/`.

The researcher's request: $ARGUMENTS

## Your job

Make the draft's claims and their evidence visible.

1. Extract each substantive claim with its location: findings, causal and novelty claims, generalisations, policy recommendations.
2. For each: the evidence offered, its status (checked, cited but unchecked, the researcher's assertion, your inference, none), and whether the wording fits the design (association against causation, sample against population).
3. Run `python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/verify_refs.py` on the cited references.
4. Ask before creating the ledger the first time, then record each claim (`ledger.py claim`) and its evidence (`ledger.py evidence`), marking claims you suggested as `--origin assistant`.

Show a table: claim, location, evidence, status, wording fits the design. Then `ledger.py status` for what the evidence still owes.

## Do not

Mark a claim supported because the citation exists, or rewrite the claims for them; suggest the honest range of wording and let them choose.

## End with

The evidence status of what you discussed, the one to three open questions that matter most (and whether they went into the ledger), and a one- or two-sentence AI-use statement.
