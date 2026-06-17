#!/usr/bin/env python3
"""Tiny eval harness for Ethical Research.

Behavioral cases live in cases.json. Because these test an assistant's *behavior*,
scoring is a judgment call — so this harness supports both a human-review path
(no dependencies) and an optional live path that runs the prompts through Claude
and an LLM judge.

    python run_evals.py --list               # print every case with its pass/fail rubric
    python run_evals.py --template > r.json   # emit a results template to fill in by hand
    python run_evals.py --check r.json        # score a filled results file (CI gate; exits 1 on fail)
    python run_evals.py --with-claude         # live: run prompts + judge them
                                              #   needs ANTHROPIC_API_KEY and `pip install anthropic`

The live path sends each prompt to a model whose system prompt is this repo's
SKILL.md, then asks a judge model to check the output against the case rubric.
It is opt-in on purpose: the default paths run anywhere, offline, with no key.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = Path(__file__).resolve().parent / "cases.json"
SKILL_PATH = ROOT / "skills" / "ethical-research" / "SKILL.md"


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


def cmd_with_claude(cases, model: str) -> int:
    try:
        import anthropic  # type: ignore
    except ImportError:
        print("--with-claude needs the anthropic package: pip install anthropic", file=sys.stderr)
        return 2
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("--with-claude needs ANTHROPIC_API_KEY in the environment", file=sys.stderr)
        return 2

    client = anthropic.Anthropic()
    system = SKILL_PATH.read_text(encoding="utf-8")
    results = []
    for c in cases:
        answer = client.messages.create(
            model=model,
            max_tokens=1200,
            system=system,
            messages=[{"role": "user", "content": c["prompt"]}],
        ).content[0].text

        rubric = json.dumps(c["expect"], ensure_ascii=False, indent=2)
        judge_prompt = (
            "You are grading whether an assistant's reply meets a rubric. "
            "Reply with ONLY a JSON object: {\"pass\": true|false, \"reason\": \"...\"}.\n\n"
            f"RUBRIC (every MUST satisfied, no MUST NOT violated):\n{rubric}\n\n"
            f"ASSISTANT REPLY:\n{answer}"
        )
        verdict_raw = client.messages.create(
            model=model,
            max_tokens=400,
            messages=[{"role": "user", "content": judge_prompt}],
        ).content[0].text
        try:
            verdict = json.loads(verdict_raw[verdict_raw.find("{"): verdict_raw.rfind("}") + 1])
        except (ValueError, json.JSONDecodeError):
            verdict = {"pass": False, "reason": f"could not parse judge output: {verdict_raw[:200]}"}
        results.append({"id": c["id"], "pass": bool(verdict.get("pass")), "notes": verdict.get("reason", "")})
        mark = "PASS" if verdict.get("pass") else "FAIL"
        print(f"  {mark}  {c['id']}: {verdict.get('reason', '')[:140]}")

    out_path = Path(__file__).resolve().parent / "results.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {out_path}")
    return 0 if all(r["pass"] for r in results) else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Ethical Research eval harness")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--list", action="store_true", help="print cases and rubrics (default)")
    g.add_argument("--template", action="store_true", help="emit a results template to stdout")
    g.add_argument("--check", metavar="RESULTS.json", help="score a filled results file (CI gate)")
    g.add_argument("--with-claude", action="store_true", help="live run via Claude + LLM judge")
    p.add_argument("--model", default="claude-sonnet-4-6", help="model id for --with-claude")
    args = p.parse_args(argv)

    cases = load_cases()
    if args.template:
        return cmd_template(cases)
    if args.check:
        return cmd_check(cases, args.check)
    if args.with_claude:
        return cmd_with_claude(cases, args.model)
    return cmd_list(cases)


if __name__ == "__main__":
    raise SystemExit(main())
