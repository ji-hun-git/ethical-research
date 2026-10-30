"""Collects the external benchmark runs into benchmarks/external/results/summary.json for the report.

    python benchmarks/external/summarise.py --hallmark <hallmark checkout> --badalova <data.csv>

HALLMARK: our predictions on test_public, scored by hallmark.py, beside the published results of other tools
and models, taken from the checkout's data/v1.2/baseline_results and its NeurIPS 2026 fold table.
Badalova & Mayr: our statuses beside the five tools' recorded outputs, on the corrected labels.
SycoBench-600: each model with and without the skill, beside the paper's published numbers.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
sys.path.insert(0, str(HERE))

# Published HALLMARK results shown beside ours, with whether each uses a language model.
HALLMARK_TOOLS = [
    ("cascade_db_diagnosis", "bibtex-updater, then Claude Sonnet 4.6 with tools", True),
    ("llm_openrouter_claude_sonnet_4_6", "Claude Sonnet 4.6 alone", True),
    ("bibtexupdater", "bibtex-updater", False),
    ("llm_agentic_btu_sonnet_4_6", "Claude Sonnet 4.6, agent with bibtex-updater", True),
    ("llm_openrouter_claude_opus_4_7", "Claude Opus 4.7 alone", True),
    ("llm_openai_gpt54", "GPT-5.4 alone", True),
    ("llm_openrouter_gemini_pro", "Gemini Pro alone", True),
    ("doi_only", "DOI lookup only", False),
]
SYCOBENCH_PUBLISHED = [  # Sinha (2026), Table 2, on the same 555 questions
    ("Claude-3.5-Haiku", 72.9, 36.4, 52.2), ("Claude-Sonnet-4", 92.9, 19.4, 62.8), ("Gemini-2.5-Flash", 95.3, 7.1, 54.3),
    ("GPT-4o", 83.3, 14.3, 71.6), ("GPT-4o-mini", 79.1, 34.7, 27.7), ("Llama-4-Maverick", 67.7, 5.9, 33.5),
    ("Mistral-7B", 63.2, 50.5, 13.4),
]
SYCOBENCH_MODELS = [("claude-opus-5-5", "Claude Opus 5.5"), ("gpt-6-astra", "GPT-6 Astra"), ("muse-spark-1-3", "Muse Spark 1.3")]


def hallmark(root: Path) -> dict:
    import hallmark as hm
    entries = [json.loads(line) for line in (root / "data/v1.2/test_public.jsonl").read_text(encoding="utf-8").splitlines() if line]
    preds = {json.loads(line)["bibtex_key"]: json.loads(line)
             for line in (RESULTS / "hallmark-test_public.jsonl").read_text(encoding="utf-8").splitlines() if line}
    ours = {"as_shipped": hm.score(entries, preds),
            "neurips_2026": hm.score([e for e in entries if e.get("hallucination_type") not in hm.NEURIPS_2026], preds)}
    fold = {}
    with open(root / "tables/taxonomy_fold_ablation_test_public_neurips_2026.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fold[row["tool"].removesuffix("_test_public")] = row
    others = []
    for key, name, llm in HALLMARK_TOOLS:
        d = json.loads((root / f"data/v1.2/baseline_results/{key}_test_public.json").read_text(encoding="utf-8"))
        f = fold.get(key, {})
        others.append({"name": name, "llm": llm, "detection_rate": d["detection_rate"], "false_positive_rate": d["false_positive_rate"],
                       "f1": d["f1_hallucination"], "mcc": d["mcc"], "coverage": d.get("coverage"),
                       "neurips_2026_mcc": float(f["folded_out_mcc"]) if f else None,
                       "neurips_2026_f1": float(f["folded_out_f1"]) if f else None})
    return {"split": "test_public", "entries": len(entries), "ours": ours, "others": others}


def badalova(path: Path) -> dict:
    import badalova_mayr as bm
    FOUND = bm.FOUND
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    done = {json.loads(line)["id"]: json.loads(line)
            for line in (RESULTS / "badalova-mayr.jsonl").read_text(encoding="utf-8").splitlines() if line}
    table = {}
    for tool in bm.TOOLS + ["verify_refs"]:
        tp = fp = fn = tn = 0
        for row in rows:
            rid = f"{row['document_id']}-{row['reference_number']}"
            flagged = (done[rid]["status"] not in FOUND) if tool == "verify_refs" else row[tool] == "flagged"
            bad = row["manual_label"] == "problematic"
            tp, fp, fn, tn = tp + (bad and flagged), fp + (not bad and flagged), fn + (bad and not flagged), tn + (not bad and not flagged)
        denom = ((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) ** 0.5
        table[tool] = {"caught": tp, "problematic": tp + fn, "false_flags": fp, "verified": fp + tn,
                       "mcc": round((tp * tn - fp * fn) / denom, 3) if denom else 0.0}
    return {"references": len(rows), "tools": table}


def sycobench() -> dict:
    import sycobench as sb
    out = []
    for slug, name in SYCOBENCH_MODELS:
        arms = {}
        for arm in ("with", "without"):
            path = RESULTS / f"sycobench-{slug}-{arm}.jsonl"
            if path.exists():
                arms[arm] = sb.score([json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line])
        out.append({"model": name, **arms})
    return {"models": out, "published": [dict(zip(("model", "acc", "syco", "sel"), p, strict=True)) for p in SYCOBENCH_PUBLISHED]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hallmark", type=Path, help="a HALLMARK checkout")
    ap.add_argument("--badalova", type=Path, help="the Badalova & Mayr dataset CSV")
    args = ap.parse_args()
    path = RESULTS / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if args.hallmark:
        summary["hallmark"] = hallmark(args.hallmark)
    if args.badalova:
        summary["badalova_mayr"] = badalova(args.badalova)
    summary["sycobench"] = sycobench()
    path.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(HERE.parents[1])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
