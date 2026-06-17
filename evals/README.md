# Evals

Two layers of regression testing.

## 1. Structural tests (no dependencies, run today)

`tests/` checks the repo's invariants — that every command binds the charter and
is listed in the router, that reference links resolve, that the manifests are
valid and consistent, that the charter still has its six commitments, and that no
stale brand tokens crept back in.

```
pip install -r requirements-dev.txt
pytest
```

## 2. Behavioral cases

`cases.json` holds the behavioral cases — including the three from the smoke test
(`plan-safe`, `citation-verify-trap`, `question-critical-ko`) — each with a
pass/fail rubric (`must` / `must_not`). Because these test an assistant's
*behavior*, scoring is a judgment call, so the harness offers both a no-setup
path and a live path.

```
python evals/run_evals.py --list             # print every case with its rubric
python evals/run_evals.py --template > r.json # emit a results template to fill by hand
python evals/run_evals.py --check r.json      # score a filled file (exits 1 on any fail)
python evals/run_evals.py --with-claude       # live: run prompts through Claude + an LLM judge
```

The live path (`--with-claude`) is opt-in: it needs `ANTHROPIC_API_KEY` and
`pip install anthropic`. It sends each prompt to a model whose system prompt is
this repo's `skills/ethical-research/SKILL.md`, then asks a judge model whether
the reply meets the rubric. The default paths run offline with no key.

The narrative specs in `safe-cases.md` and `unsafe-cases.md` are the
human-readable companion to `cases.json`.
