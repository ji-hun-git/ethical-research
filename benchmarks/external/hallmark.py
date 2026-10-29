"""Run verify_refs.py on a HALLMARK split and score it the way HALLMARK does.

  python benchmarks/external/hallmark.py <hallmark checkout> <split> <out.jsonl> [--sample N]

Each entry becomes one BibTeX entry from its own fields (nothing is looked up to build it). Status ->
label: record found = VALID; not found, metadata mismatch, retracted, concern = HALLUCINATED;
unchecked = UNCERTAIN, which HALLMARK leaves out of the confusion matrix and counts against coverage.
Resumable: entries already in out.jsonl are not checked again.
"""
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills" / "ethical-research" / "scripts"))
import verify_refs  # noqa: E402

FLAG = {"not found", "metadata mismatch", "retracted", "concern"}


def bibtex(entry: dict) -> str:
    fields = "".join(f"  {k} = {{{v}}},\n" for k, v in entry["fields"].items() if v)
    return f"@{entry.get('bibtex_type') or 'misc'}{{{entry['bibtex_key']},\n{fields}}}\n"


def label(status: str) -> str:
    return "HALLUCINATED" if status in FLAG else "VALID" if status in ("record found", "page found") else "UNCERTAIN"


def main() -> int:
    root, split, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    entries = [json.loads(line) for line in (root / "data" / "v1.2" / f"{split}.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if "--sample" in sys.argv:
        n = int(sys.argv[sys.argv.index("--sample") + 1])
        entries = random.Random(20261029).sample(entries, n)
    done = {}
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            done[row["bibtex_key"]] = row
    with out.open("a", encoding="utf-8") as sink:
        for i, entry in enumerate(entries, 1):
            if entry["bibtex_key"] in done:
                continue
            started = time.monotonic()
            refs = verify_refs.parse(bibtex(entry))
            result = verify_refs.check(refs[0]) if refs else {"status": "unchecked", "detail": "no entry parsed"}
            row = {"bibtex_key": entry["bibtex_key"], "label": label(result["status"]), "confidence": 0.8,
                   "status": result["status"], "reason": result["detail"][:400],
                   "wall_clock_seconds": round(time.monotonic() - started, 2)}
            sink.write(json.dumps(row, ensure_ascii=False) + "\n")
            sink.flush()
            done[entry["bibtex_key"]] = row
            if i % 25 == 0:
                print(f"{i}/{len(entries)}", flush=True)
    print(json.dumps({"as_shipped": score(entries, done),
                      "neurips_2026": score([e for e in entries if e.get("hallucination_type") not in NEURIPS_2026], done)},
                     indent=1))
    return 0


# HALLMARK's own fold preset (scripts/ablate_taxonomy_fold.py): the modes the NeurIPS 2026 criteria leave outside
# "hallucinated". Folding drops those entries from the scored set; false positives are unchanged.
NEURIPS_2026 = {"wrong_venue", "preprint_as_published", "arxiv_version_mismatch", "near_miss_title",
                "partial_author_list", "fabricated_doi", "future_date"}


def score(entries: list[dict], preds: dict) -> dict:
    tp = fp = tn = fn = answered = 0
    w = {1: 1.0, 2: 2.0, 3: 3.0}
    wtp = wfn = wfp = 0.0
    by_type: dict[str, list[int]] = {}
    for e in entries:
        p = preds.get(e["bibtex_key"])
        if not p or p["label"] == "UNCERTAIN":
            continue
        answered += 1
        hit = p["label"] == "HALLUCINATED"
        kind = e.get("hallucination_type") or "valid"
        by_type.setdefault(kind, [0, 0])
        by_type[kind][0] += 1
        by_type[kind][1] += hit
        if e["label"] == "HALLUCINATED":
            tier = w.get(e.get("difficulty_tier") or 1, 1.0)
            if hit:
                tp, wtp = tp + 1, wtp + tier
            else:
                fn, wfn = fn + 1, wfn + tier
        elif hit:
            fp, wfp = fp + 1, wfp + 1.0
        else:
            tn += 1
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    denom = ((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) ** 0.5
    wp = wtp / (wtp + wfp) if wtp + wfp else 0.0
    wr = wtp / (wtp + wfn) if wtp + wfn else 0.0
    coverage = answered / len(entries) if entries else 0.0
    return {"entries": len(entries), "answered": answered, "coverage": round(coverage, 4), "tp": tp, "fp": fp, "tn": tn,
            "fn": fn, "detection_rate": round(rec, 4), "false_positive_rate": round(fp / (fp + tn), 4) if fp + tn else 0.0,
            "f1": round(f1, 4), "mcc": round((tp * tn - fp * fn) / denom, 4) if denom else 0.0,
            "tier_weighted_f1": round(2 * wp * wr / (wp + wr), 4) if wp + wr else 0.0,
            "coverage_adjusted_f1": round(f1 * coverage, 4),
            "by_type": {k: f"{v[1]}/{v[0]} flagged" for k, v in sorted(by_type.items())}}


if __name__ == "__main__":
    sys.exit(main())
