# Evals

Each case is a realistic request with graders that decide pass or fail. Most are traps a research assistant meets every week: asked for references from nothing, asked to mark unchecked references Verified, asked to write the chapter and hide it, pushed to agree with a causal claim from a correlation. Some check that it still helps with legitimate requests and does not stall a student with questions.

## Layout

```
evals/
  <case>/prompt.md            the request, with run limits in frontmatter
  <case>/graders/*.md         one grader per file: regex, tool_used or llm (a PASS/FAIL rubric)
  pressure/*.json             multi-turn pressure tests: the researcher pushes back turn after turn
  run.py, report.py           the cross-vendor runner and the report it writes to benchmarks/
```

Graders whose names start with `never-` are integrity checks: failing one means the model did the thing this project exists to stop. The report counts those failures separately from ordinary misses.

## In Claude Code

The single-turn cases are in the layout `claude plugin eval` reads, so they run against the plugin in its real host, with and without the plugin:

```
claude plugin eval . --runs 3 --allow-tools "Bash(python3 *)"
```

Granting Bash runs commands under Claude Code's sandbox, which needs Linux, macOS or WSL2; without the grant the checks cannot run and the citation and statistics cases measure the instructions alone.

## On any model

`run.py` runs the same cases on models from any vendor, twice per run: **without** the skill (the bare model, no system prompt, no tools) and **with** it (the skill's instructions as if it had triggered, plus `read_file` for its references and `run_check` for its scripts). Answers are graded by a jury of three models from three vendors, majority of three, and every DOI in every answer is resolved against Crossref and DataCite in code.

```
pip install -r evals/requirements.txt
export ANTHROPIC_API_KEY=... OPENAI_API_KEY=... LLM_API_KEY=...   # one per vendor in the jury
python evals/run.py run --model anthropic:claude-haiku-5-5 --name "Claude Haiku 5.5"
python evals/run.py run --model openai:gpt-6-luna --name "GPT-6 Luna"
python evals/run.py report
```

Model specs are those of the [AI Agent Building Kit](https://github.com/ji-hun-git/ai-agent-building-kit): `anthropic:<id>`, `openai:<id>` (Responses API), `responses:<id>@<base_url>`, `openai:<id>@<base_url>` (Chat Completions, including a local Ollama). `--jury` swaps the judges, `--cases` filters by name, `--runs` sets runs per arm. Results go to `benchmarks/results/<name>.json` with the hash of the skill files they ran on, and `report` rewrites [benchmarks/README.md](../benchmarks/README.md) and the table in the README.

## What the numbers do and do not show

They show what the skill changes in a model's behaviour on these cases, under these graders. They do not show that researchers using it reason better: that needs a study with people, which has not been done. The with-arm loads the skill as if it had triggered; whether Claude Code triggers it on its own is what `claude plugin eval` measures.
