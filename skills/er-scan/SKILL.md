---
name: er-scan
description: "Scan a manuscript (txt, md, tex, docx or pdf) for hidden instructions to AI reviewers, invisible characters, chatbot leftovers, tortured phrases, placeholders and strong claims. Never judges whether text was written by AI."
argument-hint: "[a manuscript file or pasted text]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/*)
---

# /er-scan

Read `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/SKILL.md` first and follow it: its charter binds this mode and its questioning loop runs throughout. Its references are in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/references/` and its checks in `${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/`.

The researcher's request: $ARGUMENTS

## Your job

1. Run `python ${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/scripts/integrity_scan.py <file>` (or `-` with pasted text). If the PDF has text the scanner could not decode, suggest scanning the `pdftotext` output as well.
2. Report errors first: hidden instructions (quote them), invisible tag characters (quote the decoded message), a paper-mill signature. Then warnings and questions.
3. For each, say what to do: remove hidden text, replace tortured phrases with the standard terms and find where they came from, fill or delete placeholders, check the AI-use statement for chatbot leftovers.

Read [integrity-scan.md](../ethical-research/references/integrity-scan.md) for what the scan does not do.

## Do not

Estimate whether text is AI-written, suggest edits that would make text pass a detector, or present a clean scan as a certificate.

## End with

The evidence status of what you discussed, the one to three open questions that matter most (and whether they went into the ledger), and a one- or two-sentence AI-use statement.
