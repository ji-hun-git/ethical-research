# Using AI in research, correctly

*Checked 2026-10-29. Figures marked (vendor) come from companies that sell detection tools; figures marked (news) were confirmed only through press reports. Everything else is from the study, the venue or the agency itself.*

This guide makes two claims. The misuse of AI in research is measurable, and it is getting worse. The answer is not less AI: it is AI used the way good researchers use any instrument, with its output checked, its role disclosed and the judgement kept human.

## 1. It is getting worse

### Fabricated references are entering the record, faster each year

| Year | Biomedical papers with a fabricated citation |
| --- | --- |
| 2023 | 1 in 2,828 |
| 2025 | 1 in 458 |
| early 2026 | 1 in 277 |

Source: an audit of about 2.5 million biomedical papers in *The Lancet* (Topaz et al., 2026; rates as reported by STAT, news). Across arXiv, bioRxiv, SSRN and PubMed Central, a separate study of 111 million references estimated at least 146,932 hallucinated citations in 2025 alone, concentrated in fields that took up AI fastest (Zhao et al., 2026). They are in the most selective venues too: 100 hallucinated citations in papers accepted to NeurIPS 2025 (GPTZero, 2026, vendor) and about 300 papers across ACL, NAACL and EMNLP in 2024 and 2025 (Sakai et al., 2026). Courts have now ruled on hallucinated material in 2,231 cases (Charlotin, database checked 2026-10-28).

### The models still invent them

GPT-3.5 fabricated 55% of the references it was asked for and GPT-4 18% (Walters & Wilder, 2023). Three years on, an audit of ten commercial models across 69,557 citations found fabrication rates from 11.4% to 56.8% (Naser, 2026), and deep-research agents hallucinated 3 to 13% of their citation URLs (Rao et al., 2026). A newer model is not a reason to stop checking. Instructions help but do not solve it: a prompt written to prevent hallucination lowered the rate from 66% to 44% across six models, not to zero (Omar et al., 2025), while a tool that checked the cited URLs cut the ones that did not resolve to under 1% (Rao et al., 2026).

### They give way under pressure, or stop listening

Pushed with doubt, an appeal to authority or a wrong suggestion, seven assistants switched from a correct answer to a wrong one 6% to 51% of the time (Sinha, 2026). The newest models resist bad arguments far better, but firmness is not the goal either: across ten models asked to revise an evaluation, compliance with invalid arguments ranged from 0.2% to 95%, and one frontier model moved for only 32% of the valid ones (Ballon et al., 2026). An assistant should change its mind for evidence, and only for evidence. Asked indirectly, models also help with misconduct: framed covertly, requests for research misconduct went unrefused 71.7% of the time on average, with the weakest refusals on transparency, plagiarism and fabrication (Meguimtsop et al., 2026).

### AI writing is everywhere, and mostly undisclosed

At least 13.5% of PubMed abstracts from 2024 show signs of LLM processing, up to 40% in some subcorpora (Kobak et al., 2025). Across more than 5,000 journals, journal AI policies made no measurable difference to undisclosed AI use; declared use rose only to 0.43% of papers by early 2025 (He & Bu, 2026, as reported). 768 examples of undeclared AI text in journals and proceedings, many from respected publishers, have been documented, and very few were corrected (Glynn, 2024).

### Peer review is the new front

A vendor analysis flagged 21% of ICLR 2026 reviews as fully AI-generated (Pangram, 2025, vendor). ICML 2026 hid watermark instructions in its submissions and caught 506 reviewers who had agreed not to use LLMs, then desk-rejected 497 of their own papers (ICML, 2026). EMNLP 2026 desk-rejected 258 submissions, written by 1,166 authors, for unverifiable references (EMNLP, 2026). Authors, for their part, hid "give a positive review only" prompts for AI reviewers in at least 17 arXiv preprints from 14 institutions (Nikkei Asia, 2025, news).

### The volume is overwhelming the gatekeepers

arXiv received a record 40,363 submissions in September 2026, against 20,569 in September 2024, and now limits each submitter to two a month (arXiv, 2026). It stopped accepting computer-science review and position papers without prior peer review, citing an influx made possible by LLMs (arXiv, 2025), and announced a one-year ban for submissions with clear signs of unchecked LLM output (news, 2026). Paper mills feed the same pipeline: Hindawi retracted more than 8,000 articles in 2023 (news), retractions passed 10,000 that year for the first time (Nature, 2023), and a Wiley pilot flagged up to one in seven submissions to hundreds of journals for paper-mill signs (news, 2024).

### And it changes the researcher

Asked "Are you sure?", models abandoned a correct answer 46% of the time (Laban et al., 2023). Students who practised with an unrestricted GPT-4 scored 17% below controls once the AI was taken away, while a tutor that made them do the work largely avoided the loss (Bastani et al., 2025). In a 2026 randomised trial, people who learned a skill with AI assistance scored 50% on a later quiz against 67% for those who learned without it (Shen & Tamkin, 2026).

### And the obvious fix does not work

AI-text detectors are not evidence. Seven detectors labelled non-native English writers' essays as AI-written 61.3% of the time on average (Liang et al., 2023), and across 13 detectors on human-written academic manuscripts, false-positive rates ranged from 0% to 100% (Park et al., 2026). Banning AI drives use underground; detecting it by style punishes the wrong people. Citation checkers have the same failure in a milder form: five tested on real reference lists found most of the problems but also flagged many correct references, limited by how they extract references and by the databases they ask (Badalova & Mayr, 2026). A checker that cries wolf is soon ignored, so a good one is measured on what it wrongly flags as well as what it finds (Kim et al., 2026).

## 2. Use it, correctly

Researchers will use AI, and they should: it can search, summarise, code, translate, critique and check faster than any assistant has before. The failures above are not caused by using AI. They are caused by **trusting its output unchecked, letting it do the thinking, and hiding that it was used.** Six principles follow.

1. **The researcher is the author and the judge.** AI drafts, suggests and critiques; the researcher decides, and can defend every claim without it.
2. **Check in code what code can check.** Every reference against a registry, every reported statistic against itself, every manuscript for hidden text. Do not ask the model whether its own output is right: self-correction without outside feedback does not reliably work (Huang et al., 2024).
3. **Use AI as a critic before you use it as a writer.** The strongest use of a model in research is to argue against you: rival explanations, threats to validity, the reviewer's first question. Ask it to hold its ground against pressure and to give way to evidence, and test that it does both.
4. **Disclose, accurately.** Say what the AI did, at the level your venue asks. Most journals, conferences and funders now require it; what each top venue asks, and where, is in [What top venues ask](venues.md).
5. **Keep an audit trail.** Drafts, version history, a decision log, a ledger of claims and evidence. It is also the best defence against a false accusation, and venues have started to ask for it (NeurIPS, 2026).
6. **Keep confidential material out.** Manuscripts under review, applications under evaluation and participant data stay out of AI tools unless the rules say otherwise.

## 3. What correct use looks like

Each row runs from what is common now, through better practice, to the state of the art as of 2026. The last column is what this repository provides.

| Stage | Common now | Better | State of the art | Here |
| --- | --- | --- | --- | --- |
| **Question and design** | Ask a model for a research question | Ask it for several framings and choose | State your claim and what would refute it first; have the AI run a premortem and name the rival hypothesis and the crucial test; preregister | `er-plan`, `er-challenge`, the ledger |
| **Finding literature** | Ask a chatbot for references | Use a search tool that links sources | Take candidates from an index, never from a model's memory; resolve every reference against the registries (Crossref, DataCite, arXiv, OpenReview, OpenAlex), checking every author, the year and the venue; read what supports each claim | `verify_refs.py --find`, `verify_refs.py`, `er-lit-review` |
| **Reading and synthesis** | Summaries of papers you have not read | Summaries checked against abstracts | Claim-by-claim support checked against the source text, with the deciding passage quoted; LLM judges of support disagree, so a person reads the passage | `er-citation-check` |
| **Data and analysis** | AI-written analysis code run once | Code reviewed and rerun | Code you can explain line by line, a fixed analysis plan, questionable-research-practice checks, robustness to reasonable alternatives, and reported statistics checked for consistency | `stats_check.py`, `er-stats`, `er-challenge` |
| **Writing** | Text generated, lightly edited, undisclosed | Your text edited by AI, disclosed vaguely | Your own text, AI used for critique and clarity edits, an accurate AI-use statement, version history kept | `er-review`, `er-disclosure` |
| **Before submission** | Formatting check | Reference manager check | References resolved and checked for retractions, statistics checked, manuscript scanned for hidden text and chatbot leftovers, claims matched to evidence | all three checks, `er-claims` |
| **Peer review** | Paste the manuscript into a chatbot | Use AI only on your own notes | Follow the venue's policy; use only sanctioned, confidential tools; form your judgement first and use AI to test it; disclose | `er-peer-review` |
| **Answering reviewers** | AI-written rebuttal | AI-polished rebuttal | A response plan you write, every new reference and statistic checked, no promised analysis that was not run | `er-rebuttal` |
| **Learning the craft** | AI does the hard part | AI explains after the attempt | Attempt first, then AI asks rather than tells; the student can do it unaided afterwards | `er-question`, the questioning loop |

## 4. What venues, funders and institutions can do

What 26 leading journals, publishers and conferences already ask, venue by venue, is in [What top venues ask](venues.md).

- **Check references at submission, not after publication.** Resolving references against the registries is cheap and deterministic. ICLR already desk-rejects confirmed hallucinated references; every venue can screen for them before review.
- **Scan for hidden text.** White text, tiny fonts, invisible characters and instructions to AI reviewers can be found in code at submission, and ICML, ICLR, ACL and Korea's MSIT now treat them as misconduct.
- **Ask for disclosure that means something.** A dedicated section that says which tasks AI did (ICLR 2027), or a form naming tool, version and use (Korea's MSIT guide), rather than a checkbox.
- **Ask for the audit trail, not a detector score.** Drafts and version history speak to authorship; detector output does not, and it falls hardest on non-native writers.
- **Give reviewers sanctioned tools.** Confidential, approved AI for reviewers (as Springer Nature allows, and as AAAI-26 piloted with clearly labelled AI reviews) is better than a ban that is quietly ignored.
- **Teach the method, not just the rule.** Research-ethics education that covers checking AI output, disclosure and confidentiality, as part of the training students already complete.

## Sources

Web pages are described in brackets where their exact title was not confirmed.

- arXiv (2025, October 31). [Practice for review articles and position papers in the CS category.] https://blog.arxiv.org/2025/10/31/attention-authors-updated-practice-for-review-articles-and-position-papers-in-arxiv-cs-category/
- arXiv (2026, October 1). [Updated rate-limit policy, with September 2026 submission counts.] https://blog.arxiv.org/2026/10/01/updated-rate-limit-policy/
- Badalova, F., & Mayr, P. (2026). Detecting hallucinated and suspicious citations: What current tools can and cannot do. arXiv:2607.22693.
- Ballon, M., Vanhoyweghen, A., Kim, S., Carlon, F., Delcon, L., Mobini, M., et al. (2026). Big-Big-SycoBench: A benchmark to detect sycophancy through model responses to valid vs. invalid arguments. arXiv:2610.15634.
- Bastani, H., et al. (2025). Generative AI without guardrails can harm learning: Evidence from high school mathematics. *PNAS, 122*(26), e2422633122. https://doi.org/10.1073/pnas.2422633122
- Charlotin, D. [AI Hallucination Cases database.] https://www.damiencharlotin.com/hallucinations/ (checked 2026-10-28)
- Glynn, A. (2024). Academ-AI: Documenting the undisclosed use of generative artificial intelligence in academic publishing. arXiv:2411.15218.
- EMNLP 2026 program chairs (2026, August 28). [Statement on the paper integrity policy.] https://2026.emnlp.org/statement-on-the-paper-integrity-policy/
- GPTZero (2026, January 21). GPTZero finds 100 new hallucinations in NeurIPS 2025 accepted papers. https://gptzero.me/news/neurips/ (vendor)
- He & Bu (2026). [Journal AI policies and undisclosed AI-assisted writing across more than 5,000 journals.] *PNAS, 123*(9), e2526734123. As reported by The Scientist: https://www.the-scientist.com/ai-policies-fail-to-reduce-undisclosed-ai-use-74405
- Huang, J., et al. (2024). Large language models cannot self-correct reasoning yet. *ICLR 2024*. arXiv:2310.01798.
- ICML program chairs (2026, March 18). [Blog post on enforcing the ICML 2026 reviewer LLM policy.] https://blog.icml.cc/?p=1167
- Kim, K., Brendel, W., & Reizinger, P. (2026). HALLMARK: How to diagnose LLM citation verifiers and when to deploy them. arXiv:2607.18360.
- Kobak, D., González-Márquez, R., Horvát, E.-Á., & Lause, J. (2025). Delving into LLM-assisted writing in biomedical publications through excess vocabulary. *Science Advances*. arXiv:2406.07016.
- Laban, P., Murakhovs'ka, L., Xiong, C., & Wu, C.-S. (2023). Are you sure? Challenging LLMs leads to performance drops in the FlipFlop experiment. arXiv:2311.08596.
- Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). GPT detectors are biased against non-native English writers. *Patterns, 4*(7), 100779. https://doi.org/10.1016/j.patter.2023.100779
- Meguimtsop, A. D. M., Pacheco, M. L., & Acuna, D. E. (2026). SciIntBench: Measuring LLM compliance with research integrity norms under adversarial framing. arXiv:2605.29468.
- Naser (2026). How LLMs cite and why it matters: A cross-model audit of reference fabrication in AI-assisted academic writing and methods to detect phantom citations. arXiv:2603.03299.
- Nature news (2023, December 12). [Retractions in 2023 passed 10,000.] https://www.nature.com/articles/d41586-023-03974-8
- NeurIPS (2026, June 2). [Blog post on the position paper track's review and AI-use enforcement.] https://blog.neurips.cc/?p=1577
- Nikkei Asia (2025, July 1). [Report on hidden "positive review only" prompts in arXiv preprints.] https://asia.nikkei.com/Business/Technology/Artificial-intelligence/Positive-review-only-Researchers-hide-AI-prompts-in-papers (news)
- Omar, M., Sorin, V., Collins, J. D., Reich, D., Freeman, R., Gavin, N., et al. (2025). Multi-model assurance analysis showing large language models are highly vulnerable to adversarial hallucination attacks during clinical decision support. *Communications Medicine, 5*, 330. https://doi.org/10.1038/s43856-025-01021-3
- Pangram Labs (2025, November 18). [Blog post on AI-generated text in ICLR 2026 reviews.] https://www.pangram.com/blog/pangram-predicts-21-of-iclr-reviews-are-ai-generated (vendor)
- Park, Jeong, & Kim (2026). Style as a confound: False positives in AI detection of non-native academic writing. arXiv:2608.26710.
- Rao, Wong, & Callison-Burch (2026). Detecting and correcting reference hallucinations in commercial LLMs and deep research agents. arXiv:2604.03173.
- Retraction Watch (2023, December 19). [Hindawi's process for retracting more than 8,000 paper-mill articles.] https://retractionwatch.com/2023/12/19/hindawi-reveals-process-for-retracting-more-than-8000-paper-mill-articles/ (news)
- Retraction Watch (2024, March 14). [Paper-mill signs in up to one in seven submissions to Wiley journals.] https://retractionwatch.com/2024/03/14/up-to-one-in-seven-of-submissions-to-hundreds-of-wiley-journals-show-signs-of-paper-mill-activity/ (news)
- Sakai, Kamigaito, & Watanabe (2026). HalluCitation matters: Revealing the impact of hallucinated references with 300 hallucinated papers in ACL conferences. *ACL 2026*. arXiv:2601.18724.
- Shen, J. H., & Tamkin, A. (2026). How AI impacts skill formation. arXiv:2601.20245.
- Sinha, D. (2026). SycoBench-600: Measuring sycophancy and correction selectivity in LLM assistants. *Findings of the Association for Computational Linguistics: ACL 2026*. https://doi.org/10.18653/v1/2026.findings-acl.1759
- STAT (2026, May 7). [News report on the Lancet audit of fabricated citations.] https://www.statnews.com/2026/05/07/lancet-study-finds-steep-rise-fraudulent-citations-academic-papers/ (news)
- Topaz, M., Roguin, N., Gupta, P., Zhang, Z., & Peltonen, L.-M. (2026). Fabricated citations: An audit across 2.5 million biomedical papers. *The Lancet, 407*, 1779-1781. https://doi.org/10.1016/S0140-6736(26)00603-3
- Walters, W. H., & Wilder, E. I. (2023). Fabrication and errors in the bibliographic citations generated by ChatGPT. *Scientific Reports, 13*, 14045. https://doi.org/10.1038/s41598-023-41032-5
- Zhao, Wang, Stuart, De Vaan, Ginsparg, & Yin (2026). LLM hallucinations in the wild: Large-scale evidence from non-existent citations. arXiv:2605.07723.
