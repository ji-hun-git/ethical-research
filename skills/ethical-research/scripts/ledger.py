#!/usr/bin/env python3
"""The research ledger: the claims in a piece of work, the evidence for each, and the questions
still open about them. Standard library only.

The ledger is what makes the assistant keep questioning instead of agreeing. It lives in the
researcher's project (.ethical-research/ledger.json), so open questions survive the session and
come back at the start of the next one. Some questions are owed by the state of the work itself
and are derived on every read, so they cannot be forgotten: a claim asserted without evidence,
evidence nobody has checked, a claim the assistant suggested that the author never endorsed.

Questions come back sparingly, because repeated reminders get overridden: the session reminder shows
at most three items, the most important first, and anything the author has accepted as a known risk
stays quiet until it is reopened.

Usage:
  python ledger.py init
  python ledger.py claim "Generative AI lowers critical-thinking scores" --where "abstract" --origin author
  python ledger.py evidence C1 "doi:10.1234/abcd" --status unverified
  python ledger.py ask "What would you expect to see if the effect were caused by prior ability?" --kind alternative --about C1
  python ledger.py answer Q1 "The author's own answer, in their words"
  python ledger.py withdraw Q2 --reason "out of scope for this paper"
  python ledger.py accept Q3 --reason "single-site sample; stated as a limitation"
  python ledger.py accept C2 --reason "kept as a hypothesis for future work"
  python ledger.py status                  open questions, owed questions, weak claims
  python ledger.py export                  the whole ledger as Markdown
  python ledger.py session-start           short reminder for the start of a session; silent without a ledger

Options: --file PATH (default .ethical-research/ledger.json in the current folder), --json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

DEFAULT = Path(".ethical-research") / "ledger.json"
KINDS = ("clarification", "assumption", "evidence", "alternative", "implication", "method", "question")
ORIGINS = ("author", "assistant")
STRENGTHS = ("asserts", "hedged", "speculative")
EVIDENCE = ("none", "unverified", "exists", "supports", "partial", "contradicts")
CLAIM_STATES = ("open", "supported", "revised", "dropped")
SESSION_ITEMS = 3     # questions put back at the start of a session
SESSION_LIMIT = 1800  # characters printed at session start


class LedgerError(Exception):
    pass


def today() -> str:
    return dt.date.today().isoformat()


def load(path: Path) -> dict:
    if not path.exists():
        raise LedgerError(f"no ledger at {path}; run `ledger.py init` in the project folder first")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1:
        raise LedgerError(f"{path} is not a version 1 ledger")
    return data


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _next_id(items: list[dict], prefix: str) -> str:
    numbers = [int(i["id"][1:]) for i in items if i["id"][1:].isdigit()]
    return f"{prefix}{max(numbers, default=0) + 1}"


def _find(items: list[dict], ident: str, what: str) -> dict:
    for item in items:
        if item["id"].lower() == ident.lower():
            return item
    raise LedgerError(f"no {what} {ident}")


def add_claim(data: dict, text: str, where: str = "", origin: str = "author", strength: str = "asserts") -> dict:
    if not text.strip():
        raise LedgerError("a claim needs its text")
    claim = {"id": _next_id(data["claims"], "C"), "text": text.strip(), "where": where, "origin": origin,
             "strength": strength, "evidence": [], "status": "open", "added": today()}
    data["claims"].append(claim)
    return claim


def add_evidence(data: dict, claim_id: str, source: str, status: str) -> dict:
    claim = _find(data["claims"], claim_id, "claim")
    if not source.strip():
        raise LedgerError("evidence needs a source: a DOI, a citation, a dataset or a table")
    claim["evidence"].append({"source": source.strip(), "status": status, "checked": today()})
    return claim


def set_claim(data: dict, claim_id: str, status: str, endorsed: bool = False) -> dict:
    claim = _find(data["claims"], claim_id, "claim")
    if status == "supported" and not any(e["status"] == "supports" for e in claim["evidence"]):
        raise LedgerError(f"{claim['id']} has no evidence marked 'supports'; check a source before calling it supported")
    claim["status"] = status
    if endorsed:
        claim["endorsed"] = today()
    return claim


def ask(data: dict, text: str, kind: str = "question", about: str = "", priority: int = 2) -> dict:
    if not text.strip():
        raise LedgerError("a question needs its text")
    if about:
        _find(data["claims"], about, "claim")
    question = {"id": _next_id(data["questions"], "Q"), "text": text.strip(), "kind": kind, "about": about,
                "priority": priority, "status": "open", "raised": today()}
    data["questions"].append(question)
    return question


def answer(data: dict, question_id: str, text: str) -> dict:
    question = _find(data["questions"], question_id, "question")
    if not text.strip():
        raise LedgerError("record the author's answer in their own words; an empty answer does not close a question")
    question.update(status="answered", answer=text.strip(), answered=today())
    return question


def withdraw(data: dict, question_id: str, reason: str) -> dict:
    question = _find(data["questions"], question_id, "question")
    if not reason.strip():
        raise LedgerError("say why the question no longer matters")
    question.update(status="withdrawn", reason=reason.strip(), withdrawn=today())
    return question


def accept(data: dict, ident: str, reason: str) -> dict:
    """The author accepts an open question or a weak claim as a known risk, with a reason; it stops
    coming back until reopened."""
    if not reason.strip():
        raise LedgerError("say why the risk is acceptable, for example where the paper states it as a limitation")
    items = data["questions"] if ident.upper().startswith("Q") else data["claims"]
    item = _find(items, ident, "question" if items is data["questions"] else "claim")
    if items is data["questions"]:
        item.update(status="accepted", reason=reason.strip(), accepted=today())
    else:
        item["risk_accepted"] = {"reason": reason.strip(), "date": today()}
    return item


def owed(data: dict) -> list[dict]:
    """Questions the state of the work demands, derived fresh on every read."""
    out = []
    for claim in data["claims"]:
        if claim["status"] in ("dropped", "revised") or claim.get("risk_accepted"):
            continue
        statuses = {e["status"] for e in claim["evidence"]}
        if claim["origin"] == "assistant" and "endorsed" not in claim:
            out.append({"about": claim["id"], "kind": "assumption",
                        "text": f"{claim['id']} came from the assistant. Do you hold it yourself, and on what grounds?"})
        if "contradicts" in statuses:
            out.append({"about": claim["id"], "kind": "evidence",
                        "text": f"A source cited for {claim['id']} contradicts it. Revise the claim, or explain the conflict."})
        elif claim["strength"] == "asserts" and not statuses & {"supports"}:
            state = "has no evidence" if not statuses or statuses == {"none"} else "has evidence nobody has checked against the claim"
            out.append({"about": claim["id"], "kind": "evidence",
                        "text": f"{claim['id']} is stated as fact but {state}. What supports it, or should it be hedged?"})
    return out


def status(data: dict) -> dict:
    open_qs = sorted((q for q in data["questions"] if q["status"] == "open"), key=lambda q: (q["priority"], q["id"]))
    return {
        "open_questions": open_qs,
        "owed_questions": owed(data),
        "claims": len(data["claims"]),
        "supported": sum(c["status"] == "supported" for c in data["claims"]),
        "answered": sum(q["status"] == "answered" for q in data["questions"]),
        "accepted": sum(q["status"] == "accepted" for q in data["questions"])
                    + sum(bool(c.get("risk_accepted")) for c in data["claims"]),
    }


def count(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def render_status(s: dict) -> str:
    lines = [f"{count(s['claims'], 'claim')} ({s['supported']} supported), "
             f"{count(len(s['open_questions']), 'open question')}, "
             f"{len(s['owed_questions'])} owed by the evidence, {s['answered']} answered, "
             f"{s['accepted']} accepted as known risks."]
    if s["open_questions"]:
        lines.append("\nOpen questions:")
        lines += [f"- {q['id']} [{q['kind']}, priority {q['priority']}{', about ' + q['about'] if q['about'] else ''}] {q['text']}"
                  for q in s["open_questions"]]
    if s["owed_questions"]:
        lines.append("\nOwed by the evidence:")
        lines += [f"- [{q['kind']}, about {q['about']}] {q['text']}" for q in s["owed_questions"]]
    return "\n".join(lines)


def session_start(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        s = status(load(path))
    except (LedgerError, ValueError, KeyError):
        return "Ethical Research: the research ledger at .ethical-research/ledger.json could not be read."
    if not s["open_questions"] and not s["owed_questions"]:
        return ""
    head = ("Ethical Research ledger for this project: "
            f"{count(len(s['open_questions']), 'open question')} and {len(s['owed_questions'])} owed by the evidence. "
            "Before new work, put the most important of these back to the researcher; do not answer them yourself.")
    lines = [head]
    items = [q for q in s["open_questions"] if q["priority"] == 1] + s["owed_questions"] + \
            [q for q in s["open_questions"] if q["priority"] > 1]
    for q in items[:SESSION_ITEMS]:
        line = f"- {q.get('id', 'owed')}: {q['text']}"
        if sum(len(x) + 1 for x in lines) + len(line) > SESSION_LIMIT:
            break
        lines.append(line)
    rest = len(items) - (len(lines) - 1)
    if rest > 0:
        lines.append(f"- {rest} more in `ledger.py status`; raise them only when the work reaches them.")
    return "\n".join(lines)


def export(data: dict) -> str:
    out = ["# Research ledger", ""]
    out.append("## Claims")
    for c in data["claims"]:
        out.append(f"\n**{c['id']}** ({c['strength']}, from the {c['origin']}, {c['status']})"
                   f"{' at ' + c['where'] if c['where'] else ''}: {c['text']}")
        for e in c["evidence"]:
            out.append(f"- evidence: {e['source']} ({e['status']}, {e['checked']})")
        if c.get("risk_accepted"):
            out.append(f"- accepted as a known risk {c['risk_accepted']['date']}: {c['risk_accepted']['reason']}")
    out.append("\n## Questions")
    for q in data["questions"]:
        out.append(f"\n**{q['id']}** [{q['kind']}{', about ' + q['about'] if q['about'] else ''}] {q['text']}")
        if q["status"] == "answered":
            out.append(f"- answered {q['answered']}: {q['answer']}")
        elif q["status"] == "withdrawn":
            out.append(f"- withdrawn {q['withdrawn']}: {q['reason']}")
        elif q["status"] == "accepted":
            out.append(f"- accepted as a known risk {q['accepted']}: {q['reason']}")
        else:
            out.append("- open")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The research ledger: claims, evidence and open questions.")
    parser.add_argument("--file", type=Path, default=DEFAULT, help="ledger path (default %(default)s)")
    parser.add_argument("--json", action="store_true", help="print JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    p = sub.add_parser("claim")
    p.add_argument("text")
    p.add_argument("--where", default="")
    p.add_argument("--origin", choices=ORIGINS, default="author")
    p.add_argument("--strength", choices=STRENGTHS, default="asserts")
    p = sub.add_parser("evidence")
    p.add_argument("claim")
    p.add_argument("source")
    p.add_argument("--status", choices=EVIDENCE, default="unverified")
    p = sub.add_parser("mark")
    p.add_argument("claim")
    p.add_argument("status", choices=CLAIM_STATES)
    p.add_argument("--endorsed", action="store_true", help="the author has said they hold this claim")
    p = sub.add_parser("ask")
    p.add_argument("text")
    p.add_argument("--kind", choices=KINDS, default="question")
    p.add_argument("--about", default="")
    p.add_argument("--priority", type=int, choices=(1, 2, 3), default=2)
    p = sub.add_parser("answer")
    p.add_argument("question")
    p.add_argument("text")
    p = sub.add_parser("withdraw")
    p.add_argument("question")
    p.add_argument("--reason", required=True)
    p = sub.add_parser("accept", help="accept an open question or a weak claim as a known risk")
    p.add_argument("item", help="a question (Q3) or a claim (C2)")
    p.add_argument("--reason", required=True)
    sub.add_parser("status")
    sub.add_parser("export")
    sub.add_parser("session-start")
    args = parser.parse_args(argv)

    if args.command == "session-start":
        text = session_start(args.file)
        if text:
            print(text)
        return 0
    try:
        if args.command == "init":
            if args.file.exists():
                raise LedgerError(f"{args.file} already exists")
            save(args.file, {"version": 1, "created": today(), "claims": [], "questions": []})
            print(f"created {args.file}")
            return 0
        data = load(args.file)
        if args.command == "status":
            s = status(data)
            print(json.dumps(s, indent=2, ensure_ascii=False) if args.json else render_status(s))
            return 0
        if args.command == "export":
            print(json.dumps(data, indent=2, ensure_ascii=False) if args.json else export(data), end="")
            return 0
        actions = {
            "claim": lambda: add_claim(data, args.text, args.where, args.origin, args.strength),
            "evidence": lambda: add_evidence(data, args.claim, args.source, args.status),
            "mark": lambda: set_claim(data, args.claim, args.status, args.endorsed),
            "ask": lambda: ask(data, args.text, args.kind, args.about, args.priority),
            "answer": lambda: answer(data, args.question, args.text),
            "withdraw": lambda: withdraw(data, args.question, args.reason),
            "accept": lambda: accept(data, args.item, args.reason),
        }
        item = actions[args.command]()
        save(args.file, data)
        print(json.dumps(item, ensure_ascii=False) if args.json else f"{item['id']}: {args.command} recorded")
        return 0
    except LedgerError as err:
        print(f"ledger: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
