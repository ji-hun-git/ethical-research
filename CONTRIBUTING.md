# Contributing

Better checks, better questions and better grounding are all welcome. Keep the charter intact: a contribution that makes the assistant agree more, write more for the researcher or check less will not be merged.

- **Run what CI runs:** `python -m unittest` from the repository root. Standard library only.
- **Every fix comes with a test that fails without it.** Every check names the failure it catches.
- **Every fact carries its source.** In `skills/ethical-research/references/`, cite the primary source with a DOI or URL, give the date for anything that changes (policies, numbers from vendors), and mark second-hand reports as such. Before opening a pull request, run the reference list through `skills/ethical-research/scripts/verify_refs.py`: this repository holds itself to the standard it asks of researchers.
- **New tortured phrases or chatbot phrases** need a published source showing they occur in the literature, and must be specific enough to flag on their own.
- **The scripts stay dependency-free** so they run wherever the skill does, in Claude Code, Codex or a plain terminal.
- **Behaviour changes need an eval.** Add a case under `evals/` (the layout `claude plugin eval` reads) with PASS and FAIL conditions, and say in the pull request how it scored with and without your change.
- **No AI-text detection.** The tool reports integrity defects; it does not estimate whether text was written by AI, and it does not help anyone pass a detector.
- **Security issues** (a way to make the assistant follow hidden instructions, mark unchecked references verified, or leak confidential text) go by email, not issues: see [SECURITY.md](SECURITY.md).
