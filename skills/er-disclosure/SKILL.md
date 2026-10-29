---
name: er-disclosure
description: "Write a truthful AI-use statement for a named venue, accurate to the help actually given, at the level and in the place the venue requires. Never understates the assistance."
argument-hint: "[venue, and what the AI helped with]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*)
---

# /er-disclosure

Read `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/SKILL.md` first and follow it: its charter binds this mode and its questioning loop runs throughout. Its references are in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/references/` and its checks in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/`.

The researcher's request: $ARGUMENTS

## Your job

Follow [ai-disclosure.md](../ethical-research/references/ai-disclosure.md).

1. Establish what assistance actually happened (ask if unclear), the venue, and the level: minimal, standard or detailed.
2. For a venue-specific statement, ask for the venue's policy text; without it, write a standard statement and say you cannot assert compliance with a policy you have not seen. [policies.md](../ethical-research/references/policies.md) says where most venues want it.
3. Write it in the researcher's language; for both, compose each natively.

Output the statement, where it goes, and what policy text would make it venue-specific.

## Do not

Understate the help, claim compliance with an unseen policy, or help someone avoid disclosing.

## End with

The evidence status of what you discussed, the one to three open questions that matter most (and whether they went into the ledger), and a one- or two-sentence AI-use statement.
