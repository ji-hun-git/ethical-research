# Outside benchmarks

Benchmarks built by other people, run as their authors describe, with their published results beside ours. The
results are in [benchmarks/README.md](../README.md#outside-benchmarks); this folder holds the runners and the raw
outputs, so every number can be checked or recomputed.

| Benchmark | What it tests here | Data | Runner | Raw output |
| --- | --- | --- | --- | --- |
| [HALLMARK](https://github.com/rpatrik96/hallmark) (Kim, Brendel & Reizinger, 2026) | `verify_refs.py` on 831 BibTeX entries, real or with one of 14 kinds of error | commit `c62d296`, `data/v1.2/test_public.jsonl` (MIT) | [hallmark.py](hallmark.py) | `results/hallmark-test_public.jsonl` |
| [Badalova & Mayr](https://doi.org/10.5281/zenodo.23236264) (2026) | `verify_refs.py` on the 104 references of three published documents, beside five other checkers | v1.1.0, corrected labels (CC BY 4.0) | [badalova_mayr.py](badalova_mayr.py) | `results/badalova-mayr.jsonl` |
| [SycoBench-600](https://github.com/debu-sinha/sycobench-600) (Sinha, 2026) | three models, with and without the skill, under doubt, authority and wrong suggestions | commit `3b2d368`, the 555 questions of the paper (data CC BY 4.0) | [sycobench.py](sycobench.py) | `results/sycobench-<model>-<arm>.jsonl` |

`summarise.py` collects them into `results/summary.json`, which the report reads.

```
git clone https://github.com/rpatrik96/hallmark && git -C hallmark checkout c62d296
python benchmarks/external/hallmark.py hallmark test_public benchmarks/external/results/hallmark-test_public.jsonl
python benchmarks/external/badalova_mayr.py manual_reference_verification_dataset.csv benchmarks/external/results/badalova-mayr.jsonl
python benchmarks/external/sycobench.py sycobench-600 --model anthropic:claude-opus-5-5 --arm with --out benchmarks/external/results/sycobench-claude-opus-5-5-with.jsonl
python benchmarks/external/summarise.py --hallmark hallmark --badalova manual_reference_verification_dataset.csv
python evals/run.py report
```

## How it was done, and what to keep in mind

- **No benchmark code is run.** The runners read each benchmark's data and reimplement its published scoring (HALLMARK's confusion matrix, its handling of abstentions and its NeurIPS 2026 fold; SycoBench's prompts, parser and metrics), so the numbers can be compared with the published ones.
- **Tuned on one split, reported on another.** The reference checker was improved on a 300-entry random sample of HALLMARK's `dev_public` split. `test_public` was run once, after those changes, and is what is reported.
- **The live indexes change.** The checker asks Crossref, DataCite, arXiv, OpenReview and OpenAlex at run time. OpenAlex allows a small number of requests a day without a key, and it ran out during these runs: the outputs say where it could not be reached, and those references were judged on the other indexes alone. A rerun on another day can differ by a little.
- **Tools that abstain.** Some published tools answer "uncertain" for part of the entries; HALLMARK scores them on what they answered and reports their coverage. `verify_refs.py` answers every entry unless a lookup fails.
- **One SycoBench wording per question.** The paper asks each question in three wordings; here each question uses one, in rotation, so all three are used equally. The published numbers are for the paper's models, which are older than the ones run here.
