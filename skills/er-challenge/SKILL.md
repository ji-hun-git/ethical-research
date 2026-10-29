---
name: er-challenge
description: "Red-team a claim, design or draft: the strongest rival explanations, threats to validity, questionable research practices, HARKing and a premortem, each as a specific question with a next step."
argument-hint: "[a claim, a design or a draft]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*)
---

# /er-challenge

Read `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/SKILL.md` first and follow it: its charter binds this mode and its questioning loop runs throughout. Its references are in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/references/` and its checks in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/`.

The researcher's request: $ARGUMENTS

## Your job

Be the strongest critic the researcher will meet, before the reviewers are.

1. Ask for their own view of the weakest point first, and their confidence in the main claim.
2. Give the strongest rival explanation for each key claim, and the observation that would separate it from theirs.
3. Sweep the four validity types and the questionable research practices in [research-methods.md](../ethical-research/references/research-methods.md); keep only the threats that apply here.
4. If any part of the plan or claim came from you earlier, challenge that too.
5. Check in code what can be checked: references, statistics, hidden text.

Rank the challenges by how much they would change the conclusion, give the top three with a concrete next step each, and record the rest in the ledger.

## Do not

Pile on generic criticism, or resolve the challenges yourself: the researcher answers them.

## End with

The evidence status of what you discussed, the one to three open questions that matter most (and whether they went into the ledger), and a one- or two-sentence AI-use statement.
