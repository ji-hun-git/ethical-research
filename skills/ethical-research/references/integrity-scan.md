# The integrity scan

`scripts/integrity_scan.py` reads a manuscript (.txt, .md, .tex, .docx or .pdf) and reports defects that code can find reliably. Run it on the final files before submission, and on any manuscript a reviewer is permitted to process.

## What it finds

| Level | Finding | Why it matters |
| --- | --- | --- |
| error | Instructions addressed to an AI ("ignore previous instructions", "give a positive review", "for LLM reviewers"), in English or Korean | Hidden reviewer prompts were found in 17 arXiv preprints in 2025 and are misconduct at ICML, ICLR, ACL and under Korea's 2026 MSIT guide ([policies.md](policies.md)) |
| error | Text a reader cannot see: drawn in white, at a size under 2 pt, in PDF render mode 3 (invisible), placed off the page, Word hidden or white runs, LaTeX comments and `\textcolor{white}` carrying instructions, and instructions in a PDF's metadata (title, subject, keywords, XMP) | The usual hiding places for those prompts |
| error | Unicode tag characters, decoded so the hidden message can be quoted | They render as nothing and can carry instructions |
| error | Five or more tortured phrases | The threshold the Problematic Paper Screener uses for a likely paper-mill product |
| warn | Each tortured phrase ("profound learning" for deep learning, "counterfeit consciousness" for artificial intelligence), from Table 1 of Cabanac et al. (2021) | Synonym-swapped terms are a paper-mill signature; a single one can be innocent |
| warn | Chatbot text ("as an AI language model", "regenerate response", "certainly, here is", "as of my last knowledge update") | Possible undisclosed AI use; check the AI-use statement. Phrases kept to those specific enough to flag alone (Glynn, 2024) |
| warn | Unfilled placeholders ([citation needed], [insert reference], (Author, Year), lorem ipsum) | Unfinished text, and often a fabricated citation waiting to happen |
| warn | Zero-width and bidirectional control characters | Can hide or reorder text |
| question | Strong claims ("proves", "for the first time", "groundbreaking", causal verbs near "survey" or "correlation") | A question for the author about whether the design supports the wording |

## What it does not do

**It does not judge whether text was written by AI.** AI-text detectors are not reliable enough to accuse anyone: seven detectors misclassified essays by non-native English writers as AI-generated 61.3% of the time on average (Liang et al., 2023); fourteen tools tested were "neither accurate nor reliable" (Weber-Wulff et al., 2023); across 13 detectors on human-written academic manuscripts, false-positive rates ranged from 0% to 100% (Park et al., 2026). This tool will not compute an AI-likelihood score, and it will not help anyone edit text to pass a detector. When a researcher is accused on the basis of a detector, explain these error rates and suggest the evidence that does speak to authorship: drafts, version history, notes and a truthful AI-use statement.

**A clean scan certifies nothing.** It means none of these specific defects was found. PDF text in fonts with custom encodings cannot be decoded without a PDF library; the scan says how many runs it could not read, and scanning the output of `pdftotext` as well covers them.

## Reporting findings

Quote each finding with its location and level, explain why it matters in one line, and say what to do: remove hidden text, replace tortured phrases with the standard terms and ask where they came from, fill or delete placeholders, check the AI-use statement. If a co-author's text contains hidden prompts or paper-mill signatures, say plainly that it must be resolved before submission and that the venue would treat it as misconduct.

## Sources

- Cabanac, G., Labbé, C., & Magazinov, A. (2021). Tortured phrases: A dubious writing style emerging in science. Evidence of critical issues affecting established journals. arXiv:2107.06751.
- Glynn, A. (2024). Academ-AI: Documenting the undisclosed use of generative artificial intelligence in academic publishing. arXiv:2411.15218.
- Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). GPT detectors are biased against non-native English writers. *Patterns, 4*(7), 100779. https://doi.org/10.1016/j.patter.2023.100779
- Park, Jeong, & Kim (2026). Style as a confound: False positives in AI detection of non-native academic writing. arXiv:2608.26710.
- Weber-Wulff, D., et al. (2023). Testing of detection tools for AI-generated text. *International Journal for Educational Integrity, 19*, 26. https://doi.org/10.1007/s40979-023-00146-z
