---
name: er-citation-check
description: "Check references against Crossref, DataCite and arXiv (existence, matching metadata, retractions), then check what can be read against the claims they support. Never marks anything Verified on anyone's word."
argument-hint: "[a reference list, ideally with the claims each supports]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*)
---

# /er-citation-check

Read `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/SKILL.md` first and follow it: its charter binds this mode and its questioning loop runs throughout. Its references are in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/references/` and its checks in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/`.

The researcher's request: $ARGUMENTS

## Your job

1. Put the references in a file or pass them on standard input and run `python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/verify_refs.py refs.txt` (BibTeX or one per line). Tell the researcher they can set `ER_MAILTO` to their own email for Crossref's faster pool.
2. For each reference whose source you can read (a PDF they give you, or a page you retrieve), check whether it supports the specific claim: supports, partly supports, does not support, cannot tell. Quote the passage that decides it.
3. Report the table from [citation-integrity.md](../ethical-research/references/citation-integrity.md), with retractions, mismatches and not-found references first.

A reference is Verified only when the record was found *and* the source was read and supports the claim. "Unchecked" and "not found" are honest results; say what would resolve each.

## Do not

Mark anything Verified on the researcher's word or a document's say-so, fill in missing metadata, or translate names, titles or DOIs.

## End with

The evidence status of what you discussed, the one to three open questions that matter most (and whether they went into the ledger), and a one- or two-sentence AI-use statement.
