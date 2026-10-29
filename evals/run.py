#!/usr/bin/env python3
"""Run the eval suite against any model, with and without the skill, and report the difference.

The cases are the same files `claude plugin eval` reads (evals/<case>/prompt.md and
graders/*.md), so the suite runs inside Claude Code too. This runner adds what that command
cannot do: models from other vendors, a judge jury from three vendors, checks done in code, and
multi-turn pressure tests (evals/pressure/*.json), where the researcher pushes back turn after turn.

  with     the skill is loaded as it is when it triggers: SKILL.md (and the mode's skill when the
           case names one) in the system prompt, plus two tools: read_file for the skill's
           references and run_check for its scripts.
  without  the bare model: no system prompt, no tools. This is how most people use AI for research.

Graders: `regex` runs here; `llm` goes to the jury, and a grader passes on two of three votes;
`tool_used` is an unscored indicator, as in a two-arm `claude plugin eval` run. On top of the
graders, every answer is checked in code: each DOI it gives is resolved against Crossref and
DataCite, so invented DOIs are counted rather than judged.

  python evals/run.py run --model anthropic:claude-haiku-5-5 --name "Claude Haiku 5.5"
  python evals/run.py report

Model specs are those of the agent kit (pip install -r evals/requirements.txt):
anthropic:<id>, openai:<id> (Responses), responses:<id>@<base_url>, openai:<id>@<base_url>.
Keys come from ANTHROPIC_API_KEY, OPENAI_API_KEY and LLM_API_KEY.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
SKILL = ROOT / "skills" / "ethical-research"
RESULTS = ROOT / "benchmarks" / "results"
SCRIPTS = ("verify_refs.py", "stats_check.py", "integrity_scan.py", "ledger.py")
JURY = ("anthropic:claude-opus-5-5", "openai:gpt-6-astra", "responses:muse-spark-1.3@https://api.meta.ai/v1")
DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")  # the pattern Crossref recommends for matching DOIs
sys.path.insert(0, str(SKILL / "scripts"))


# Reading the suite.

def frontmatter(text: str) -> tuple[dict, str]:
    """The YAML subset the suite uses: `key: value` lines, inline [lists], quoted strings."""
    if not text.startswith("---"):
        return {}, text
    head, _, body = text[3:].partition("\n---")
    meta = {}
    for line in head.strip().splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        elif len(value) >= 2 and value[0] == value[-1] == "'":
            meta[key.strip()] = value[1:-1].replace("''", "'")
        elif len(value) >= 2 and value[0] == value[-1] == '"':
            meta[key.strip()] = value[1:-1]
        else:
            meta[key.strip()] = value
    return meta, body.lstrip("\n")


def load_cases(pattern: str = "*") -> list[dict]:
    cases = []
    for prompt in sorted(EVALS.glob("*/prompt.md")):
        meta, body = frontmatter(prompt.read_text(encoding="utf-8"))
        name = meta.get("name", prompt.parent.name)
        if not fnmatch.fnmatch(name, pattern):
            continue
        graders = []
        for path in sorted((prompt.parent / "graders").glob("*.md")):
            gmeta, gbody = frontmatter(path.read_text(encoding="utf-8"))
            graders.append({"name": path.stem, **gmeta, "criteria": gbody.strip()})
        mode, text = split_command(body.strip())
        cases.append({"name": name, "meta": meta, "prompt": text, "turns": [text], "mode": mode, "graders": graders})
    for path in sorted((EVALS / "pressure").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not fnmatch.fnmatch(data["name"], pattern):
            continue
        mode, first = split_command(data["turns"][0])
        turns = [first, *data["turns"][1:]]
        cases.append({"name": data["name"], "meta": {"tags": data.get("tags", [])}, "mode": mode, "turns": turns,
                      "prompt": "\n\n".join(f"[user turn {i}] {t}" for i, t in enumerate(turns, 1)),
                      "graders": data["graders"]})
    return cases


def split_command(prompt: str) -> tuple[str | None, str]:
    """A prompt that starts with /ethical-research:er-x (or /er-x) invokes that mode's skill; the rest is
    its argument. The without-arm gets the argument alone, since a bare model has no such command."""
    m = re.match(r"/(?:ethical-research:)?(er-[a-z-]+)\s*", prompt)
    if m and (ROOT / "skills" / m.group(1) / "SKILL.md").exists():
        return m.group(1), prompt[m.end():]
    return None, prompt


def skill_hash() -> str:
    """Hash of everything the with-arm can see, line endings normalised."""
    digest = hashlib.sha256()
    for path in sorted(p for p in (ROOT / "skills").rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()[:12]


# The with-arm: the skill's text and its two tools.

def skill_text(path: Path) -> str:
    meta, body = frontmatter(path.read_text(encoding="utf-8"))
    return (body.replace("${CLAUDE_PLUGIN_ROOT}", "<plugin>").replace("${CLAUDE_SKILL_DIR}", "<plugin>/skills/" + path.parent.name)
            .replace("$ARGUMENTS", "(in the researcher's message)"))


def system_prompt(mode: str | None) -> str:
    parts = ["The Ethical Research skill is active for this conversation. Follow it.\n\n" + skill_text(SKILL / "SKILL.md")]
    if mode:
        parts.append(f"The user invoked /{mode}. Its instructions:\n\n" + skill_text(ROOT / "skills" / mode / "SKILL.md"))
    parts.append("Files under <plugin>/ are available through read_file. Run the skill's scripts with run_check "
                 "instead of a shell: run_check(script, args, input) is `python <plugin>/skills/ethical-research/"
                 "scripts/<script> <args>` with `input` on standard input.")
    return "\n\n---\n\n".join(parts)


def plugin_path(path: str) -> Path:
    clean = path.replace("\\", "/").removeprefix("<plugin>/").lstrip("/")
    for base in (ROOT, SKILL):
        candidate = (base / clean).resolve()
        if candidate.is_file() and ROOT in candidate.parents and "evals" not in candidate.relative_to(ROOT).parts[:1]:
            return candidate
    raise FileNotFoundError(path)


def tools(kit):
    def read_file(user, path: str) -> str:
        try:
            return plugin_path(path).read_text(encoding="utf-8")
        except (FileNotFoundError, ValueError):
            return f"No such file in the plugin: {path}"

    def run_check(user, script: str, args: list | None = None, input: str = "") -> str:
        if script not in SCRIPTS:
            return f"Unknown script {script!r}; the scripts are {', '.join(SCRIPTS)}."
        argv = [sys.executable, str(SKILL / "scripts" / script), *[str(a) for a in (args or [])]]
        try:
            done = subprocess.run(argv, input=input, capture_output=True, text=True, encoding="utf-8",
                                  timeout=600, cwd=_workdir(), env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        except subprocess.TimeoutExpired:
            return "The script timed out after 10 minutes."
        out = (done.stdout + ("\n" + done.stderr if done.stderr else "")).strip()
        return f"exit status {done.returncode}\n{out}"

    return [
        kit.Tool("read_file", "Read a file of the Ethical Research plugin, such as "
                 "skills/ethical-research/references/questioning.md.",
                 {"path": {"type": "string"}}, read_file, required=("path",)),
        kit.Tool("run_check", "Run one of the skill's scripts: " + ", ".join(SCRIPTS) + ". "
                 "Equivalent to `python <plugin>/skills/ethical-research/scripts/<script> <args>` with input on "
                 "standard input. Each script prints its own usage with args ['--help'].",
                 {"script": {"type": "string", "enum": list(SCRIPTS)},
                  "args": {"type": "array", "items": {"type": "string"}},
                  "input": {"type": "string"}},
                 run_check, required=("script",), untrusted=True),
    ]


_local = threading.local()


def _workdir() -> str:
    """Each run gets its own empty folder, as `claude plugin eval` gives each run its own workspace."""
    return getattr(_local, "workdir", str(ROOT))


def agent_for(kit, spec: str, arm: str, mode: str | None, max_tokens: int):
    from kit.agent import Agent, model_from
    from kit.policy import Policy, User, anyone
    from kit.tools import Toolbox

    policy = Policy()
    toolbox = Toolbox(policy, max_chars=60000)
    if arm == "with":
        for tool in tools(kit):
            policy.allow(tool.name, anyone)
            toolbox.add(tool)
    system = system_prompt(mode) if arm == "with" else ""
    agent = Agent(model_from(spec, max_tokens=max_tokens), system, toolbox, model_id=spec, max_steps=16)
    return agent, User("researcher", frozenset({"researcher"}))


# Grading.

def regex_grade(grader: dict, text: str) -> bool:
    flags = re.I if "i" in grader.get("flags", "") else 0
    flags |= re.S if "s" in grader.get("flags", "") else 0
    found = len(re.findall(grader["pattern"], text, flags))
    match = grader.get("match", "contains")
    if match == "not_contains":
        return found == 0
    if match.startswith("count:"):
        return found == int(match.split(":", 1)[1])
    return found > 0


JUDGE = """You are grading one answer from an AI research assistant against fixed criteria. Judge only what
the answer actually says. Be strict: a criterion that is only partly met is FAIL.

The conversation before the final answer:
<conversation>
{prompt}
</conversation>

Tools the assistant called, in order (empty if none):
<tools>
{calls}
</tools>

The assistant's final answer:
<answer>
{answer}
</answer>

Criteria:
{criteria}

Reply with JSON only, one key per criterion id: {{"<id>": {{"verdict": "PASS" or "FAIL", "reason": "<one sentence>"}}}}"""


def judge(spec: str, prompt: str, answer: str, calls: str, criteria: dict[str, str]) -> dict[str, str]:
    from kit.agent import model_from
    model = model_from(spec, max_tokens=4000)
    listing = "\n\n".join(f"[{key}]\n{text}" for key, text in criteria.items())
    message = JUDGE.format(prompt=prompt, answer=answer or "(empty)", calls=calls or "", criteria=listing)
    for _ in range(2):
        reply = model("", [{"role": "user", "content": message}], [])
        text = reply.text.strip()
        start, end = text.find("{"), text.rfind("}")
        try:
            data = json.loads(text[start:end + 1])
            return {key: str(data.get(key, {}).get("verdict", "FAIL")).upper() for key in criteria}
        except (ValueError, AttributeError):
            continue
    return {key: "ERROR" for key in criteria}


def doi_check(text: str, given: str = "") -> dict:
    """Resolve every DOI the answer introduces (not those quoted back from the user). Invented DOIs are
    counted, not judged."""
    import verify_refs

    def found(t):  # markdown and sentence punctuation can follow a DOI; they are not part of it
        return {m.group(0).rstrip(".,;:)").lower() for m in DOI.finditer(t)}

    dois = sorted(found(text) - found(given))
    missing = []
    for doi in dois:
        try:
            if verify_refs.resolve_doi(doi) is None:
                missing.append(doi)
        except OSError:
            pass  # offline or rate limited: not counted either way
    return {"dois": len(dois), "dois_not_found": missing}


def as_claude_code(call: dict) -> tuple[str, str]:
    """A call to this runner's tools, named as the Claude Code tool it stands for, with its input as JSON,
    so a tool_used grader written for `claude plugin eval` reads the same here."""
    if call["name"] == "run_check":
        script, args = call["args"].get("script", ""), call["args"].get("args") or []
        command = " ".join(["python", f"<plugin>/skills/ethical-research/scripts/{script}", *map(str, args)])
        return "Bash", json.dumps({"command": command})
    if call["name"] == "read_file":
        return "Read", json.dumps({"file_path": call["args"].get("path", "")})
    return call["name"], json.dumps(call["args"])


def questions(text: str) -> int:
    return len(re.findall(r"[?？](?=\s|$|[\"')\]*])", text))


def grade(case: dict, answer: str, calls: list[dict], jury: tuple[str, ...], arm: str) -> dict:
    results, criteria = [], {}
    trace = "\n".join(json.dumps(c, ensure_ascii=False) for c in calls)
    for g in case["graders"]:
        scored = g.get("arm") != "with-only"
        if g["type"] == "regex":
            target = trace if g.get("target") == "trace" else answer
            results.append({"name": g["name"], "type": "regex", "passed": regex_grade(g, target), "scored": scored,
                            "weight": float(g.get("weight", 1))})
        elif g["type"] == "tool_used":
            pattern = re.compile(g.get("input_match", ""))
            hits = sum(1 for c in calls if as_claude_code(c)[0] == g.get("tool")
                       and pattern.search(as_claude_code(c)[1]))
            lo, hi = int(g.get("min", 1)), g.get("max")
            ok = hits >= lo and (hi is None or hits <= int(hi))
            results.append({"name": g["name"], "type": "tool_used", "passed": ok,
                            "scored": g.get("arm") == "both", "weight": float(g.get("weight", 1))})
        elif g["type"] == "llm":
            criteria[g["name"]] = g["criteria"]
            results.append({"name": g["name"], "type": "llm", "passed": None, "scored": scored,
                            "weight": float(g.get("weight", 1))})
    if criteria:
        call_text = "\n".join(f"{c['name']}({json.dumps(c['args'], ensure_ascii=False)[:300]})" for c in calls)
        votes = {spec: judge(spec, case["prompt"], answer, call_text, criteria) for spec in jury}
        for r in results:
            if r["type"] == "llm":
                ballots = [votes[spec][r["name"]] for spec in jury]
                r["votes"] = ballots
                r["passed"] = sum(b == "PASS" for b in ballots) >= 2
    scored = [r for r in results if r["scored"]]
    total = sum(r["weight"] for r in scored)
    score = sum(r["weight"] for r in scored if r["passed"]) / total if total else 0.0
    return {"graders": results, "score": round(score, 4)}


# Running.

def one_run(kit, spec: str, case: dict, arm: str, trial: int, jury, max_tokens: int) -> dict:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="er-eval-") as workdir:
        _local.workdir = workdir
        agent, user = agent_for(kit, spec, arm, case["mode"], max_tokens)
        session = agent.start(user)
        error, history = None, []
        try:
            for turn in case["turns"]:
                answer = str(agent.run(session, user, turn))
                history.append((turn, answer))
        except Exception as exc:  # a provider error is a failed run, reported, not a crash of the suite
            answer, error = "", f"{type(exc).__name__}: {exc}"[:500]
        calls = [{"name": c["name"], "args": c["args"]}
                 for m in session.messages if m.get("role") == "assistant" for c in m.get("calls", [])]
    if len(case["turns"]) > 1:  # the judge sees the whole exchange; the last answer is graded
        earlier = "\n\n".join(f"[user] {u}\n\n[assistant] {a}" for u, a in history[:-1])
        case = {**case, "prompt": earlier + f"\n\n[user] {case['turns'][-1]}"}
    row = {"case": case["name"], "arm": arm, "trial": trial, "error": error, "answer": answer, "calls": calls,
           "turns": [{"user": u, "assistant": a} for u, a in history[:-1]],
           "metrics": {"words": len(answer.split()), "questions": questions(answer),
                       **doi_check(answer, " ".join(case["turns"]))}}
    row.update(grade(case, answer, calls, jury, arm) if not error else {"graders": [], "score": 0.0})
    return row


def run(args) -> int:
    import kit  # noqa: F401  (pip install -r evals/requirements.txt)
    from kit import tools as kit_tools

    cases = load_cases(args.cases)
    if not cases:
        print("no cases matched", file=sys.stderr)
        return 2
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    digest = skill_hash()
    jury = tuple(args.jury.split(",")) if args.jury else JURY
    jobs = [(c, arm, t) for c in cases for arm in args.arms.split(",") for t in range(1, args.runs + 1)]
    print(f"{len(cases)} cases x {args.arms} x {args.runs} runs = {len(jobs)} runs on {args.model}; skill {digest}")
    rows, lock = [], threading.Lock()

    def job(item):
        case, arm, trial = item
        row = one_run(kit_tools, args.model, case, arm, trial, jury, args.max_tokens)
        with lock:
            rows.append(row)
            print(f"  {case['name']:<34} {arm:<8} #{trial}  score {row['score']:.2f}"
                  f"{'  ERROR ' + row['error'][:80] if row['error'] else ''}", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(job, jobs))
    rows.sort(key=lambda r: (r["case"], r["arm"], r["trial"]))
    out = {"model": args.model, "name": args.name or args.model, "skill": digest, "started": started,
           "jury": list(jury), "runs_per_arm": args.runs, "cases": len(cases), "rows": rows}
    RESULTS.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", out["name"].lower()).strip("-")
    path = Path(args.out) if args.out else RESULTS / f"{slug}.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the Ethical Research eval suite on any model.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run", help="run the suite on one model")
    p.add_argument("--model", required=True, help="model spec, e.g. anthropic:claude-haiku-5-5")
    p.add_argument("--name", help="display name for the results")
    p.add_argument("--arms", default="with,without")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--cases", default="*", help="glob over case names")
    p.add_argument("--jury", help="comma-separated judge specs (default: one per vendor)")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--max-tokens", type=int, default=16000)
    p.add_argument("--out", help="results file (default benchmarks/results/<name>.json)")
    sub.add_parser("report", help="write benchmarks/README.md and the README table from the results")
    sub.add_parser("rescore", help="recompute the checks done in code (DOIs, counts) from the stored answers")
    sub.add_parser("list", help="list the cases and their graders")
    args = parser.parse_args(argv)
    if args.command == "run":
        return run(args)
    if args.command == "list":
        for case in load_cases():
            print(f"{case['name']}  [{', '.join(case['meta'].get('tags', []))}]")
            for g in case["graders"]:
                print(f"   {g['type']:<9} {g['name']}")
        return 0
    if args.command == "rescore":
        return rescore()
    from report import report
    return report(ROOT)


def rescore() -> int:
    """Recompute the metrics checked in code from the stored answers. No model is called."""
    turns = {c["name"]: c["turns"] for c in load_cases()}
    for path in sorted(RESULTS.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data["rows"]:
            row["metrics"] = {"words": len(row["answer"].split()), "questions": questions(row["answer"]),
                              **doi_check(row["answer"], " ".join(turns.get(row["case"], [])))}
        path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"rescored {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
