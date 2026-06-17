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
*behavior*, scoring is a judgment call, so the harness keeps it explicit and
offline (no network, no dependencies).

```
python evals/run_evals.py --list             # print every case with its rubric
python evals/run_evals.py --template > r.json # emit a results template to fill by hand
python evals/run_evals.py --check r.json      # score a filled file (exits 1 on any fail)
```

A reviewer runs each prompt against the skill, marks the case pass/fail in the
results file, and `--check` turns that into a gate. If you want to automate
scoring, wire your own model-backed judge into the check step.

The narrative specs in `safe-cases.md` and `unsafe-cases.md` are the
human-readable companion to `cases.json`.
