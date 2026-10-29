#!/usr/bin/env python3
"""Check references against the scholarly record. Standard library only.

For each reference it looks up the record (Crossref for most DOIs, DataCite for datasets and
arXiv DOIs, arXiv by identifier, and a Crossref bibliographic search when there is no DOI), compares
title, first author and year, and checks whether the work has been retracted. It reports what the
record shows; it never upgrades a reference to "Verified", because that also needs someone to read
the source and confirm it supports the claim it is cited for.

  record found          a record matches the reference (title, first author and year agree)
  metadata mismatch     a record exists, but the reference's title, author or year disagrees with it,
                        as when a real DOI is attached to the wrong paper
  retracted             the record has a retraction, withdrawal or removal notice
  concern               the record has an expression of concern
  not found             no record matches: treat as a fabrication risk until someone finds the source
  unchecked             the lookup failed (offline, rate limited); nothing is known either way

Input: a file or standard input with BibTeX entries, or one reference per line (a DOI, an arXiv
identifier, or a formatted citation). Set ER_MAILTO to your own email address to join Crossref's polite
pool; Crossref rate-limits per address, so the tool ships with none.

  python verify_refs.py references.bib
  python verify_refs.py refs.txt --json
  echo "10.1016/j.patter.2023.100779" | python verify_refs.py -

Exit status 1 when any reference is not found, mismatched, retracted or under an expression of concern.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 20
USER_AGENT = "ethical-research/2026.10.29 (https://github.com/ji-hun-git/ethical-research)"
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)")  # the pattern Crossref recommends
ARXIV_RE = re.compile(r"(?:arxiv[:./\s]*(?:abs/)?|^)(\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?\b", re.I)
YEAR_RE = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")
BIB_FIELD = re.compile(r"(\w+)\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|\"([^\"]*)\"|(\d+))")
TITLE_MATCH = 0.90      # normalised title similarity for "record found"
SEARCH_ACCEPT = 0.80    # minimum similarity for a search hit to count as the same work
_last_call = [0.0]
INTERVAL = 0.34         # seconds between requests: Crossref allows about 3 searches a second
RETRACTION = {"retraction", "partial_retraction", "withdrawal", "removal"}
CORRECTION = {"correction", "erratum", "corrigendum", "addendum", "clarification"}
TYPO = {"retration": "retraction", "retracion": "retraction", "retraction_notice": "retraction"}


# Parsing references.

def parse(text: str) -> list[dict]:
    if re.search(r"@\w+\s*\{", text):
        return parse_bibtex(text)
    refs = []
    for line in text.splitlines():
        line = re.sub(r"^\s*(?:[-*•]|\[\d+\]|\(\d+\)|\d+[.)])\s+", "", line).strip()  # list markers, not "10."
        if len(line) >= 8:
            refs.append(from_text(line))
    return refs


def from_text(line: str) -> dict:
    ref = {"raw": line}
    doi = DOI_RE.search(line)
    if doi:
        ref["doi"] = clean_doi(doi.group(1))
    arxiv = ARXIV_RE.search(line) if "arxiv" in line.lower() or re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", line) else None
    if arxiv:
        ref["arxiv"] = arxiv.group(1)
    year = YEAR_RE.search(line)
    if year:
        ref["year"] = int(year.group(1))
    title = apa_title(line) or quoted_title(line)
    if title:
        ref["title"] = title
    author = re.match(r"\s*([A-Z][\w'\-À-ɏ]+|[가-힣]{2,4})", line)
    if author:
        ref["author"] = author.group(1)
    return ref


def clean_doi(doi: str) -> str:
    """Drop what follows a DOI in prose: sentence punctuation, and a closing bracket that is not its own."""
    doi = doi.rstrip(".,;:")
    while doi.endswith(")") and doi.count(")") > doi.count("("):
        doi = doi[:-1].rstrip(".,;:")
    return doi


def apa_title(line: str) -> str | None:
    """APA and similar: '(Year). Title. Venue' - the title runs to the first full stop followed by a space,
    so a question mark inside it ("Who goes first? Influences of ...") does not cut it short."""
    m = re.search(r"\(\s*(?:1[89]|20)\d{2}[a-z]?[^)]{0,40}\)\.?\s*(.+?)(?:\.\s|\.$|$)", line)
    if not m:
        return None
    title = re.split(r"(?<=[?!])\s+(?=\*|arxiv|https?:|doi\b)", m.group(1), flags=re.I)[0]  # "...uncertainty? *ICLR*" ends at the "?"
    title = title.strip(" *").rstrip(".")
    return title if len(title) >= 10 else None


def quoted_title(line: str) -> str | None:
    """IEEE and Chicago: the title in quotation marks."""
    m = re.search(r"[\u201c\"]([^\u201d\"]{10,})[\u201d\"]", line)
    return m.group(1).strip().rstrip(",.") if m else None


def parse_bibtex(text: str) -> list[dict]:
    refs = []
    for entry in re.finditer(r"@(\w+)\s*\{\s*([^,]*),(.*?)\n\s*\}", text, re.S):
        fields = {m[0].lower(): (m[1] or m[2] or m[3]).strip() for m in BIB_FIELD.findall(entry.group(3))}
        ref = {"raw": f"@{entry.group(1)}{{{entry.group(2).strip()}}}", "key": entry.group(2).strip()}
        if fields.get("doi"):
            ref["doi"] = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", fields["doi"].strip())
        if fields.get("eprint") and "arxiv" in (fields.get("archiveprefix", "") + fields.get("eprinttype", "")).lower():
            ref["arxiv"] = fields["eprint"]
        if fields.get("title"):
            ref["title"] = re.sub(r"[{}]", "", fields["title"])
        if fields.get("author"):
            first = fields["author"].split(" and ")[0]
            ref["author"] = (first.split(",")[0] if "," in first else first.split()[-1]).strip("{} ")
        year = YEAR_RE.search(fields.get("year", "") or fields.get("date", ""))
        if year:
            ref["year"] = int(year.group(1))
        refs.append(ref)
    return refs


# Comparing a reference with a record.

def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = re.sub(r"<[^>]+>", " ", text)  # Crossref titles can carry JATS markup
    return " ".join(re.findall(r"[\w]+", text))


def similarity(a: str, b: str) -> float:
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    shorter, longer = sorted((a, b), key=len)
    if len(shorter) >= 20 and longer.startswith(shorter):  # a title without its subtitle
        ratio = max(ratio, 0.95)
    return ratio


def within(raw: str, title: str) -> float:
    """How well a record's title matches the best stretch of an unparsed citation."""
    raw, title = norm(raw), norm(title)
    if not title:
        return 0.0
    if title in raw:
        return 1.0
    size = len(title)
    return max(difflib.SequenceMatcher(None, raw[i:i + size], title).ratio()
               for i in range(0, max(1, len(raw) - size + 1), 3))


def compare(ref: dict, record: dict) -> list[str]:
    problems = []
    titles = [t for t in (record.get("title"), record.get("main_title")) if t]  # cited with or without the subtitle
    if ref.get("title") and titles and max(similarity(ref["title"], t) for t in titles) < TITLE_MATCH:
        problems.append(f"title differs: the record says \"{record['title']}\"")
    if ref.get("author") and record.get("authors"):
        surnames = {norm(a) for a in record["authors"]}
        if norm(ref["author"]) not in surnames and not any(norm(ref["author"]) in s for s in surnames):
            problems.append(f"first author differs: the record lists {', '.join(record['authors'][:3])}")
    if ref.get("year") and record.get("year") and abs(ref["year"] - record["year"]) > 1:
        problems.append(f"year differs: the record says {record['year']}")
    return problems


# Looking records up.

def _get(url: str) -> dict | None:
    """JSON from url; None on 404; OSError on any other failure. At most about 3 requests a second."""
    wait = INTERVAL - (time.monotonic() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.monotonic()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            if err.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(min(float(err.headers.get("Retry-After") or 2 ** attempt), 30))
                continue
            raise OSError(f"HTTP {err.code} from {urllib.parse.urlsplit(url).netloc}") from err
        except urllib.error.URLError as err:
            raise OSError(str(err.reason)) from err
    raise OSError("no answer")


def _mailto() -> str:
    mail = os.environ.get("ER_MAILTO", "").strip()
    return f"mailto={urllib.parse.quote(mail)}" if "@" in mail else ""


def crossref_record(item: dict) -> dict:
    year = None
    for key in ("published-print", "published-online", "issued", "created"):
        parts = (item.get(key) or {}).get("date-parts") or [[None]]
        if parts[0] and parts[0][0]:
            year = parts[0][0]
            break
    notices, seen = [], set()
    for update in item.get("updated-by") or []:  # the same event can come from the publisher and Retraction Watch
        kind = TYPO.get(norm_type(update.get("type")), norm_type(update.get("type")))
        key = ((update.get("DOI") or "").lower(), kind)
        if key not in seen:
            seen.add(key)
            notices.append({"type": kind, "doi": update.get("DOI")})
    kinds = {n["type"] for n in notices}
    title = " ".join(item.get("title") or [])
    subtitle = " ".join(item.get("subtitle") or [])
    if subtitle and norm(subtitle) not in norm(title):  # Crossref keeps subtitles in their own field
        title = f"{title}: {subtitle}"
    return {
        "source": "Crossref",
        "doi": item.get("DOI"),
        "title": title,
        "main_title": " ".join(item.get("title") or []),
        "authors": [a.get("family") or a.get("name", "") for a in item.get("author", [])],
        "year": year,
        "venue": " ".join(item.get("container-title") or []),
        "type": item.get("type"),
        "retracted": bool(kinds & RETRACTION) or norm(title).startswith("retracted"),
        "concern": "expression_of_concern" in kinds,
        "corrected": bool(kinds & CORRECTION),
        "notices": notices,
        "is_notice_for": sorted({u["DOI"].lower() for u in item.get("update-to") or [] if u.get("DOI")}),
    }


def norm_type(value) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(" ", "_")


def resolve_doi(doi: str) -> dict | None:
    """The record for a DOI from Crossref, else DataCite; None when neither has it."""
    doi = doi.strip().rstrip(".")
    quoted = urllib.parse.quote(doi, safe="/:;()")
    mail = _mailto()
    data = _get(f"https://api.crossref.org/works/{quoted}" + (f"?{mail}" if mail else ""))
    if data and data.get("message"):
        return crossref_record(data["message"])
    data = _get(f"https://api.datacite.org/dois/{urllib.parse.quote(doi, safe='')}")
    if data and data.get("data"):
        attrs = data["data"].get("attributes", {})
        return {
            "source": "DataCite",
            "doi": attrs.get("doi"),
            "title": " ".join(t.get("title", "") for t in attrs.get("titles", [])[:1]),
            "authors": [c.get("familyName") or c.get("name", "") for c in attrs.get("creators", [])],
            "year": attrs.get("publicationYear"),
            "venue": attrs.get("publisher") if isinstance(attrs.get("publisher"), str) else "",
            "type": (attrs.get("types") or {}).get("resourceTypeGeneral"),
            "retracted": False,
            "concern": False,
            "corrected": False,
            "notices": [],
            "is_notice_for": [],
        }
    return None


def resolve_arxiv(identifier: str) -> dict | None:
    """arXiv identifiers resolve through DataCite (arXiv mints DOIs 10.48550/arXiv.<id>)."""
    record = resolve_doi(f"10.48550/arXiv.{identifier}")
    if record:
        record["source"] = "arXiv (via DataCite)"
    return record


def search(ref: dict) -> dict | None:
    query = ref.get("title") or ref["raw"]
    params = f"query.bibliographic={urllib.parse.quote(query[:300])}&rows=5"
    if ref.get("author"):
        params += f"&query.author={urllib.parse.quote(ref['author'])}"
    mail = _mailto()
    data = _get(f"https://api.crossref.org/works?{params}" + (f"&{mail}" if mail else ""))
    best, best_score = None, 0.0
    for item in ((data or {}).get("message") or {}).get("items", []):
        record = crossref_record(item)
        score = similarity(ref["title"], record["title"]) if ref.get("title") else within(ref["raw"], record["title"])
        if score > best_score:
            best, best_score = record, score
    if best and best_score >= SEARCH_ACCEPT:
        best["match"] = round(best_score, 3)
        return best
    return None


def check(ref: dict) -> dict:
    out = {"reference": ref["raw"][:300], "status": "unchecked", "detail": "", "record": None}
    try:
        if ref.get("doi"):
            record = resolve_doi(ref["doi"])
            how = f"DOI {ref['doi']}"
            if record is None:
                out.update(status="not found", detail=f"{how} does not resolve in Crossref or DataCite")
                return out
        elif ref.get("arxiv"):
            record = resolve_arxiv(ref["arxiv"])
            how = f"arXiv {ref['arxiv']}"
            if record is None:
                out.update(status="not found", detail=f"{how} has no record")
                return out
        else:
            record = search(ref)
            how = "a Crossref bibliographic search"
            if record is None:
                out.update(status="not found", detail="no Crossref record matches this citation; it may still exist "
                                                      "outside Crossref (books, Korean journals, theses): find the source")
                return out
    except OSError as err:
        out["detail"] = f"lookup failed: {err}"
        return out
    out["record"] = record
    problems = compare(ref, record)
    notes = "".join(f" ({n['type'].replace('_', ' ')}: {n['doi']})" for n in record["notices"] if n.get("doi"))
    if record.get("retracted"):
        out.update(status="retracted", detail=f"{how} has a retraction notice{notes}")
    elif record.get("concern"):
        out.update(status="concern", detail=f"{how} has an expression of concern{notes}")
    elif record.get("is_notice_for"):
        out.update(status="metadata mismatch", detail=f"{how} is a notice about {', '.join(record['is_notice_for'])}, "
                                                      "not the article itself")
    elif problems:
        out.update(status="metadata mismatch", detail=f"{how}: " + "; ".join(problems))
    else:
        corrected = f"; corrected{notes}" if record.get("corrected") else ""
        out.update(status="record found", detail=f"matched by {how} ({record['source']}){corrected}")
    return out


def render(results: list[dict]) -> str:
    lines = ["| # | Reference | Status | What the record shows |", "| ---: | --- | --- | --- |"]
    for i, r in enumerate(results, 1):
        ref = r["reference"].replace("|", "\\|")
        ref = ref if len(ref) <= 90 else ref[:87] + "..."
        lines.append(f"| {i} | {ref} | {r['status']} | {r['detail'].replace('|', '/')} |")
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    lines.append("")
    lines.append(", ".join(f"{n} {status}" for status, n in counts.items()) + ". "
                 "A found record shows the work exists; whether it supports your claim needs the source itself.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check references against Crossref, DataCite and arXiv.")
    parser.add_argument("source", help="a file of references (BibTeX or one per line), or - for standard input")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    text = sys.stdin.read() if args.source == "-" else open(args.source, encoding="utf-8", errors="replace").read()
    refs = parse(text)
    if not refs:
        print("No references found in the input.", file=sys.stderr)
        return 2
    results = [check(ref) for ref in refs]
    print(json.dumps(results, indent=2, ensure_ascii=False) if args.json else render(results))
    return 1 if any(r["status"] in ("not found", "metadata mismatch", "retracted", "concern") for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
