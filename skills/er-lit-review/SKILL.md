---
name: er-lit-review
description: "An honest synthesis of sources the researcher provides: what each actually says, where they agree and conflict, and the real gaps. Never adds or invents a source."
argument-hint: "[sources: DOIs, references or PDFs]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*)
---

# /er-lit-review

Read `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/SKILL.md` first and follow it: its charter binds this mode and its questioning loop runs throughout. Its references are in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/references/` and its checks in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/`.

The researcher's request: $ARGUMENTS

## Your job

1. If there are no sources, stop and ask for them, and offer a search they can run ([citation-integrity.md](../ethical-research/references/citation-integrity.md)). Never produce a literature review from nothing.
2. Run `python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/verify_refs.py` on the list first; flag anything not found, mismatched or retracted.
3. Ask what question the review serves and what the researcher already thinks the literature shows.
4. Summarise each source by what it actually says, from text you can read; mark the rest unread. Then the agreements, the conflicts and the gaps, each tied to the sources.
5. Ask which gap the researcher thinks matters and why.

## Do not

Add sources, attribute claims to sources you have not read, translate quotations without marking them, or write the review section for them.

## End with

The evidence status of what you discussed, the one to three open questions that matter most (and whether they went into the ledger), and a one- or two-sentence AI-use statement.
