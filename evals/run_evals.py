#!/usr/bin/env python3
"""Tiny eval harness for Ethical Research.

Behavioral cases live in cases.json. Because these test an assistant's *behavior*,
scoring is a judgment call, so the harness keeps it explicit and offline — no
network, no third-party dependencies:

    python run_evals.py --list                # print every case with its pass/fail rubric
    python run_evals.py --template > r.json    # emit a results template to fill in
    python run_evals.py --check r.json         # score a filled results file (CI gate; exits 1 on fail)

A reviewer runs each prompt against the skill, then marks the case pass/fail
against its rubric in the results file. The `--check` step turns that into a
gate. (If you want to automate scoring, wire a model-backed judge into the check
step yourself; the harness deliberately ships without one.)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CASES_PATH = Path(__file__).resolve().parent / "cases.json"


def load_cases():
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def cmd_list(cases) -> int:
    for c in cases:
        print(f"\n=== {c['id']}  [{c['kind']} · {c['mode']} · {c['language']}] ===")
        print(f"PROMPT: {c['prompt']}")
        print("MUST:")
        for m in c["expect"]["must"]:
            print(f"  + {m}")
        print("MUST NOT:")
        for m in c["expect"]["must_not"]:
            print(f"  - {m}")
    print(f"\n{len(cases)} cases. Fill a template with --template, then score with --check.")
    return 0


def cmd_template(cases) -> int:
    out = [{"id": c["id"], "pass": None, "notes": ""} for c in cases]
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_check(cases, results_path: str) -> int:
    results = {r["id"]: r for r in json.loads(Path(results_path).read_text(encoding="utf-8"))}
    failed, unreviewed = [], []
    for c in cases:
        r = results.get(c["id"])
        if r is None or r.get("pass") is None:
            unreviewed.append(c["id"])
        elif not r["pass"]:
            failed.append(c["id"])
    total = len(cases)
    passed = total - len(failed) - len(unreviewed)
    print(f"passed {passed}/{total}  |  failed {len(failed)}  |  unreviewed {len(unreviewed)}")
    for cid in failed:
        print(f"  FAIL  {cid}: {results[cid].get('notes', '')}")
    for cid in unreviewed:
        print(f"  ????  {cid}: not reviewed")
    return 0 if not failed and not unreviewed else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Ethical Research eval harness")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--list", action="store_true", help="print cases and rubrics (default)")
    g.add_argument("--template", action="store_true", help="emit a results template to stdout")
    g.add_argument("--check", metavar="RESULTS.json", help="score a filled results file (CI gate)")
    args = p.parse_args(argv)

    cases = load_cases()
    if args.template:
        return cmd_template(cases)
    if args.check:
        return cmd_check(cases, args.check)
    return cmd_list(cases)


if __name__ == "__main__":
    raise SystemExit(main())
