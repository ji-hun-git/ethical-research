"""Run verify_refs.py on the Badalova & Mayr (2026) reference set and score it beside the five tools they tested.

  python benchmarks/external/badalova_mayr.py <data.csv> <out.jsonl>

Labels are the dataset's corrected manual labels (v1.1.0: 69 verified, 35 problematic). As in the paper, a tool
"flags" a reference when it marks it suspicious, mismatched, unresolved or not found; for verify_refs that is
any status but "record found" or "page found" ("unchecked" included, since it asks for verification). Resumable.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills" / "ethical-research" / "scripts"))
import verify_refs  # noqa: E402

TOOLS = ["checkifexist", "hallucitechecker", "hallucinator", "halref", "refchecker"]
FOUND = ("record found", "page found")  # anything else asks for verification, so it counts as flagged


def main() -> int:
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
    out = Path(sys.argv[2])
    done = {}
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done[r["id"]] = r
    with out.open("a", encoding="utf-8") as sink:
        for row in rows:
            rid = f"{row['document_id']}-{row['reference_number']}"
            if rid in done:
                continue
            refs = verify_refs.parse(row["reference"])
            result = verify_refs.check(refs[0]) if refs else {"status": "unchecked", "detail": "not parsed"}
            r = {"id": rid, "status": result["status"], "detail": result["detail"][:300]}
            sink.write(json.dumps(r, ensure_ascii=False) + "\n")
            sink.flush()
            done[rid] = r
    table = {}
    for tool in TOOLS + ["verify_refs"]:
        tp = fp = fn = tn = 0
        for row in rows:
            rid = f"{row['document_id']}-{row['reference_number']}"
            flagged = (done[rid]["status"] not in FOUND) if tool == "verify_refs" else row[tool] == "flagged"
            bad = row["manual_label"] == "problematic"
            tp, fp, fn, tn = tp + (bad and flagged), fp + (not bad and flagged), fn + (bad and not flagged), tn + (not bad and not flagged)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        denom = ((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) ** 0.5
        table[tool] = {"caught": f"{tp}/{tp + fn}", "false_flags": f"{fp}/{fp + tn}", "precision": round(prec, 3),
                       "recall": round(rec, 3), "f1": round(2 * prec * rec / (prec + rec), 3) if prec + rec else 0.0,
                       "mcc": round((tp * tn - fp * fn) / denom, 3) if denom else 0.0}
    print(json.dumps(table, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
