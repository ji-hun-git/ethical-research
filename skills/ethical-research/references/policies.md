# AI rules of journals, conferences, funders and agencies

Checked 2026-10-29. These rules change several times a year. Use this table to know what to ask about, never to tell a researcher that something complies: for that, ask for the venue's current text and read it. Entries marked *reported* were confirmed only through secondary sources because the primary page was not reachable.

## Authors

| Body | AI as author | What authors must disclose | Source |
| --- | --- | --- | --- |
| ICMJE (Jan 2026, new Section V) | No: AI cannot take responsibility | AI use, at submission, in the cover letter and the relevant section; AI output may not be cited as a primary source; non-disclosure may be treated as misconduct | https://www.icmje.org/news-and-editorials/updated_recommendations_jan2026.html |
| COPE (2023) | No | AI use, in the methods or a similar section (*reported*) | https://publicationethics.org/guidance/cope-position/authorship-and-ai-tools |
| Springer Nature (2026) | No | Tiered: language polishing encouraged to disclose; extensive writing help must be disclosed with oversight; give tool, version, dates and prompts; AI-generated images generally not allowed | https://www.nature.com/nature-portfolio/editorial-policies/ai |
| Elsevier (updated June 2026) | No | A separate AI declaration published with the article (spelling and grammar checks exempt); AI used in the research goes in the methods; AI may not create or alter research images | https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals |
| Science (AAAS) | No | Details not confirmed | https://www.science.org/content/page/science-journals-editorial-policies |
| IEEE (conferences) | Not stated on the page checked | AI-generated content (text, figures, code) in the acknowledgments, naming the system and sections; editing use recommended | https://conferences.ieeeauthorcenter.ieee.org/author-ethics/guidelines-and-policies/submission-policies/ |
| ACM | No | *Reported* 2026 change: writing assistance no longer needs disclosure; AI used in the research is described in the methods | https://www.acm.org/publications/policies/new-acm-policy-on-authorship |
| APA journals | Not confirmed | Disclose in the most relevant section; no identifiable participant data in open tools (*reported*) | https://www.apa.org/pubs/journals/resources/publishing-tips/policy-generative-ai |
| ACL | No, even when a model contributes ideas and text | Content-generating use in the acknowledgements; grammar checkers exempt; hidden prompts prohibited | https://aclweb.org/adminwiki/index.php/ACL_Policy_on_Publication_Ethics |
| NeurIPS 2025 | No | Important, original or non-standard LLM use in the method; authors are responsible for all text and references, and unverified LLM references are a stated violation | https://neurips.cc/Conferences/2025/LLM |
| ICLR 2026 / 2027 | Humans hold responsibility | 2026: any LLM use, in the paper and the form; hallucinated references lead to desk rejection. 2027: a mandatory AI disclosure section outside the page limit | https://blog.iclr.cc/?p=1046 ; https://iclr.cc/Conferences/2027/AIPolicyForAuthors |
| arXiv | No | Significant AI use reported; CS review and position papers need prior peer review (2025-10-31); a submission cap of two per month per submitter from 2026-10-01 | https://blog.arxiv.org/2026/10/01/updated-rate-limit-policy/ |
| NIH (NOT-OD-25-132, effective 2025-09-25) | n/a | Applications substantially developed by AI are not treated as the applicant's original work; six applications per PI per year; invented references may constitute fabrication (May 2026 reminder, *reported*) | https://grants.nih.gov/grants/guide/notice-files/NOT-OD-25-132.html |
| NSF | n/a | Proposers encouraged to disclose; proposers remain responsible for accuracy | https://www.nsf.gov/policies/ai/merit-review |

## Reviewers and editors

The common rule: do not put a confidential manuscript, application or review into an AI tool that does not guarantee confidentiality.

| Body | Rule for reviewers | Source |
| --- | --- | --- |
| NIH (NOT-OD-23-149, 2023) | No generative AI to analyse applications or write critiques | https://grants.nih.gov/grants/guide/notice-files/NOT-OD-23-149.html |
| NSF | No uploading proposal content to non-approved AI tools | https://www.nsf.gov/policies/ai/merit-review |
| ICMJE (Jan 2026) | Follow the journal's policy or ask; no upload where confidentiality cannot be assured; disclose AI use | https://www.icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-reviewers.html |
| Elsevier (June 2026) | Do not upload a manuscript or any part of it into an AI tool; supportive use through private tools only, disclosed in the review | https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals |
| Springer Nature | No upload to unsecured or public AI; approved secure tools allowed; disclose in the report | https://www.nature.com/nature-portfolio/editorial-policies/ai |
| ACL / ARR | No upload of the manuscript or the review to non-privacy-preserving tools; AI may not write the first draft of a review; paraphrasing help allowed | https://aclrollingreview.org/reviewerguidelines |
| NeurIPS 2025 | Do not share submissions with any LLM; LLMs may help with concepts and grammar without the submission | https://neurips.cc/Conferences/2025/LLM |
| ICLR 2026 | LLM use that breaks confidentiality violates the Code of Ethics; disclose LLM use; poor LLM-written reviews can get the reviewer's own papers desk-rejected | https://blog.iclr.cc/?p=1046 |
| ICML 2026 | Reviewers chose no LLMs or limited use (understanding and polishing, privacy-compliant tools only); hidden watermark instructions caught 506 reviewers who had pledged no LLM use, and 497 of their papers were desk-rejected | https://icml.cc/Conferences/2026/LLM-Policy ; https://blog.icml.cc/?p=1167 |
| Korea, MSIT national R&D guide (2026-09-20) | Evaluators may not enter material under evaluation into external AI (*reported*) | [research-ethics-kr.md](research-ethics-kr.md) |

## Hidden prompts in manuscripts

Text hidden in a manuscript to steer an AI reviewer (white text, tiny fonts, "give a positive review only") was found in 17 arXiv preprints from 14 institutions in 2025 (Nikkei Asia, 2025-07-01). It is now misconduct or collusion under ICML (2025), ICLR (2026), ACL, and Korea's MSIT guide (2026), which says it may be sanctioned as research misconduct. `scripts/integrity_scan.py` looks for it.

## Sources for the hidden-prompt section

- Nikkei Asia (2025, July 1). 'Positive review only': Researchers hide AI prompts in papers. https://asia.nikkei.com/Business/Technology/Artificial-intelligence/Positive-review-only-Researchers-hide-AI-prompts-in-papers
- ICML 2025 Publication Ethics. https://icml.cc/Conferences/2025/PublicationEthics
- Lin (2025). Hidden prompts in manuscripts exploit AI-assisted peer review. arXiv:2507.06185.
