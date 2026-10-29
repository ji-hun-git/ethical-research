# Acknowledgments and origin

Ethical Research is an independent work, written from scratch. A project about research integrity should hold itself to the citation standard it asks of researchers, so this file records what it owes.

## Methods it implements

The checks are implementations of published methods. The credit for the methods belongs to their authors; any errors in the implementations are ours.

- **Recomputed p-values** follow the approach of statcheck (Nuijten, Hartgerink, van Assen, Epskamp & Wicherts, 2016, *Behavior Research Methods*), including its rule for rounding.
- **GRIM** is the test of Brown & Heathers (2017, *Social Psychological and Personality Science*).
- **Tortured phrases** come from Table 1 of Cabanac, Labbé & Magazinov (2021, arXiv:2107.06751), and the threshold of five from their Problematic Paper Screener.
- **Chatbot phrases** are the most specific of those documented by Glynn (Academ-AI, arXiv:2411.15218).
- **Reference records** come from Crossref, including the Retraction Watch data Crossref has carried in its API since January 2025, and from DataCite, which also resolves arXiv DOIs. When neither has a work, the checker asks arXiv, OpenReview (which also serves the DBLP index of computer-science venues) and OpenAlex. All are open infrastructure run for the research community.
- **The questioning loop** draws on research on sycophancy, cognitive offloading and AI that challenges its users; [the questioning reference](skills/ethical-research/references/questioning.md) cites each source.

## Prior art

Ethical Research belongs to the broader category of academic research assistants built as agent skills, which help a researcher across the arc from question to publication while keeping a person in control. One notable example is **Academic Research Skills (ARS)** by Cheng-I Wu, distributed under CC BY-NC 4.0 (DOI: 10.5281/zenodo.20696614).

From that line of work it reuses ideas: treating fabricated citations as a hard failure, verifying references against bibliographic indexes, Socratic planning, venue-specific AI-use disclosure and mandatory human checkpoints. Ideas, methods and workflows belong to no one, and building on good ones is how research works.

It does not reuse expression. No text, code, prompt wording, file structure, mode names or taxonomy phrasing was copied or translated from it, which is why Ethical Research carries its own license (MIT) rather than CC BY-NC 4.0.

## Benchmarks and skills it is measured against

The head-to-head evals load two other research skills as they are published, without changing them, and only read their files: **Academic Research Skills** (Cheng-I Wu, CC BY-NC 4.0) and **K-Dense Scientific Agent Skills** (K-Dense Inc., MIT). How each case is routed to them is in [evals/rivals](evals/rivals/). Neither is redistributed here.

The outside benchmarks are other people's work, used under their licenses and run as their authors describe:

- **HALLMARK** (Kim, Brendel & Reizinger, 2026, arXiv:2607.18360; MIT), its data, its scoring rules and the published results of the tools it compares.
- **The reference set of Badalova & Mayr** (2026, arXiv:2607.22693; data CC BY 4.0, doi:10.5281/zenodo.23236264), with the outputs of the five tools they tested.
- **SycoBench-600** (Sinha, 2026, Findings of ACL; code MIT, data CC BY 4.0), its questions, prompts, parser and metrics.

## Where it differs on purpose

- It **keeps questioning**: a structured loop with evidence labels, a rule that positions change only for evidence, and a ledger of open questions in the researcher's project that returns each session.
- It **checks in code**: references against the registries, statistics against their own numbers, manuscripts for hidden text, instead of relying on the model's reading.
- It is **measured**: the same cases run with and without the skill on models from three vendors, graded by a jury from three vendors and by checks in code.
- It **refuses AI-text detection** in both directions: it neither scores text nor helps anyone pass a detector.
- It has **no full-draft mode**, and an AI-use statement comes with every substantive deliverable.
- It works **in Korean and English**, composed natively, and is grounded in the Korean research-ethics framework as well as international venue rules.

## If you maintain a related tool

If this acknowledgment is inaccurate or incomplete, please open an issue and it will be corrected. Getting attribution right is the point.
