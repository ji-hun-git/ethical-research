#!/usr/bin/env python3
"""Check references against the scholarly record. Standard library only.

For each reference it looks up the record (Crossref for most DOIs, DataCite for datasets and
arXiv DOIs, OpenAlex when neither has the work, arXiv by identifier, and a search of Crossref, then
arXiv, OpenReview and OpenAlex when there is no DOI), compares the title, every cited author, the year
and the venue, and checks whether the work has been retracted. It reports what the
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
pool; Crossref rate-limits per address, so the tool ships with none. Set ER_OPENALEX_KEY to use your own
OpenAlex key; without one OpenAlex allows a limited number of requests a day.

  python verify_refs.py references.bib
  python verify_refs.py refs.txt --json
  echo "10.1016/j.patter.2023.100779" | python verify_refs.py -
  python verify_refs.py --find "generative AI critical thinking university students" --since 2022

Exit status 1 when any reference is not found, mismatched, retracted or under an expression of concern.
"""
from __future__ import annotations

import argparse
import difflib
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from xml.etree import ElementTree

TIMEOUT = 20
USER_AGENT = "ethical-research/2026.10.29 (https://github.com/ji-hun-git/ethical-research)"
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)")  # the pattern Crossref recommends
ARXIV_RE = re.compile(r"(?:arxiv[:./\s]*(?:abs/)?|^)(\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?\b", re.I)
YEAR_RE = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")
BIB_FIELD = re.compile(r"(\w+)\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|\"([^\"]*)\"|(\d+))")
SEARCH_ACCEPT = 0.80    # minimum similarity for a search hit to count as the same work
_last_call: dict[str, float] = {}
INTERVAL = 0.34         # seconds between requests: Crossref allows about 3 searches a second
ARXIV_HOST = "export.arxiv.org"
INTERVALS = {ARXIV_HOST: 3.0, "api2.openreview.net": 1.0}  # arXiv asks for one request every 3 seconds
FALLBACK_HOSTS = {ARXIV_HOST, "api2.openreview.net", "api.openalex.org"}  # asked only when Crossref has no match
_limited: set[str] = set()  # fallback sources that kept refusing for rate limits in this run
RETRACTION = {"retraction", "partial_retraction", "withdrawal", "removal"}
CORRECTION = {"correction", "erratum", "corrigendum", "addendum", "clarification"}
TYPO = {"retration": "retraction", "retracion": "retraction", "retraction_notice": "retraction"}
PARTICLES = {"van", "von", "de", "der", "den", "del", "della", "di", "da", "du", "la", "le", "dos", "das", "ter", "ten"}
STOPWORDS = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "via", "by", "from", "at", "as"}
PLACEHOLDER = re.compile(r"^(?:(?:john|jane|richard|j\.?)\s+(?:doe|roe)|(?:doe|roe),\s*(?:john|jane|richard|j\.?)|"
                         r"(?:first|firstname|author)\s+(?:last|lastname|name|surname)|a\.?\s+author|"
                         r"anonymous|author\s*\d*|unknown author|tbd)$", re.I)
GENERIC_VENUE = {"journal", "international", "conference", "proceedings", "transactions", "annual", "symposium",
                 "workshop", "review", "letters", "science", "sciences", "research", "society", "ieee", "acm",
                 "advances", "studies", "volume", "part", "papers", "long", "short", "findings", "meeting"}
VENUES = {  # the names a venue goes by, for venues usually cited by their acronym
    "neurips": ("nips", "neural information processing systems"), "icml": ("international conference on machine learning",),
    "iclr": ("learning representations",), "aaai": ("aaai",), "ijcai": ("international joint conference on artificial",),
    "acl": ("association for computational linguistics",), "naacl": ("north american chapter",),
    "emnlp": ("empirical methods in natural language",), "eacl": ("european chapter",), "coling": ("computational linguistics",),
    "tacl": ("transactions of the association for computational",), "cvpr": ("computer vision and pattern recognition",),
    "iccv": ("international conference on computer vision",), "eccv": ("european conference on computer vision",),
    "kdd": ("knowledge discovery and data mining",), "chi": ("human factors in computing systems",),
    "www": ("world wide web", "web conference"), "sigir": ("research and development in information retrieval",),
    "aistats": ("artificial intelligence and statistics",), "uai": ("uncertainty in artificial intelligence",),
    "colt": ("learning theory",), "icassp": ("acoustics speech and signal processing",), "corl": ("robot learning",),
    "icra": ("robotics and automation",), "iros": ("intelligent robots and systems",), "jmlr": ("machine learning research",),
    "tmlr": ("transactions on machine learning research",), "miccai": ("medical image computing",),
    "pnas": ("proceedings of the national academy of sciences",),
}


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
            ref["title"] = delatex(fields["title"])
        if fields.get("author"):
            names = [delatex(n).strip() for n in re.split(r"\s+and\s+", fields["author"]) if n.strip()]
            ref["names"] = [n for n in names if n.lower() not in ("others", "et al", "et al.")]
            ref["more_authors"] = len(ref["names"]) < len(names)
            ref["authors"] = [surname(n) for n in ref["names"]]
            if ref["authors"]:
                ref["author"] = ref["authors"][0]
        venue = fields.get("journal") or fields.get("booktitle")
        if venue:
            ref["venue"] = delatex(venue)
        year = YEAR_RE.search(fields.get("year", "") or fields.get("date", ""))
        if year:
            ref["year"] = int(year.group(1))
        refs.append(ref)
    return refs


def delatex(text: str) -> str:
    """BibTeX markup out: {Braces}, \\emph{...}, accents such as {\\"o}, and $math$ delimiters."""
    text = re.sub(r"\\[a-zA-Z]+\s*(?=\{)", "", text)          # \emph{x} -> {x}
    text = re.sub(r"\\[`'^\"~=.uvHtcdbk]\s*\{?(\w)\}?", r"\1", text)  # {\"o} -> o
    text = re.sub(r"\\([&%$#_])", r"\1", text)
    return " ".join(re.sub(r"[{}$]", "", text).split())


def surname(name: str) -> str:
    """'Vaswani, Ashish' and 'Ashish Vaswani' -> 'Vaswani'; particles stay ('van der Maaten')."""
    if "," in name:
        return name.split(",")[0].strip()
    parts = name.split()
    for i, part in enumerate(parts[:-1]):
        if part.lower() in PARTICLES:
            return " ".join(parts[i:])
    return parts[-1] if parts else name


# Comparing a reference with a record.

LETTERS = str.maketrans({"ł": "l", "Ł": "L", "ø": "o", "Ø": "O", "đ": "d", "Đ": "D", "ð": "d", "ß": "ss",
                         "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE", "ı": "i", "þ": "th"})  # letters NFKD keeps


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", html.unescape(text or "").translate(LETTERS))
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


def same_title(cited: str, recorded: str) -> bool:
    """The same title up to case, punctuation, spacing, word order, small words and spelling variants
    (modelling, modeling); a citation may also leave the subtitle out. One changed word is a different
    title: "Attention is all you want" is not "Attention is all you need"."""
    a, b = norm(cited), norm(recorded)
    if not a or not b:
        return False
    if a == b or a.replace(" ", "") == b.replace(" ", ""):
        return True
    shorter, longer = sorted((a, b), key=len)
    if len(shorter) >= 20 and longer.startswith(shorter + " "):
        return True
    only_a, only_b = sorted(set(a.split()) - set(b.split()) - STOPWORDS), sorted(set(b.split()) - set(a.split()) - STOPWORDS)
    if len(only_a) != len(only_b):
        return False

    def variant(x: str, y: str) -> bool:  # a spelling variant, not a different word or a plural
        short, long_ = sorted((x, y), key=len)
        if long_ in (short + "s", short + "es"):
            return False
        return x[0] == y[0] and difflib.SequenceMatcher(None, x, y).ratio() >= 0.8
    return all(any(variant(x, y) for y in only_b) for x in only_a)


def on_record(name: str, recorded: list[str], full_name: str = "") -> str | None:
    """The record's author whose name holds a cited surname, if any. Records give family names or full
    names; a cited particle ("Di Jin", "van der Maaten") is tried with and without it. When several
    authors share the surname, the one whose given name fits the cited full name is chosen."""
    wants = {norm(name), norm(name).split()[-1] if norm(name) else ""} - {""}
    hits = [r for r in recorded
            if any(want == norm(r) or want in norm(r).split() or f" {want}" in f" {norm(r)}" for want in wants)]
    if full_name:
        fitting = [r for r in hits if not given_differs(full_name, r)]
        hits = fitting or hits
    return hits[0] if hits else None


def given_differs(cited: str, recorded: str) -> bool:
    """Whether two names with the same surname have clearly different given names ("Aviral Sharma" for
    "Archit Sharma"). Initials, short forms ("Chris"), and family-name-first records are not a difference."""
    a, b = norm(cited).split(), norm(recorded).split()
    if len(a) < 2 or len(b) < 2 or "," in cited or "," in recorded:
        return False
    x, y = a[0], b[0]
    if len(x) < 3 or len(y) < 3 or x in b[1:] or y in a[1:] or x.startswith(y) or y.startswith(x):
        return False
    return x[0] != y[0] or difflib.SequenceMatcher(None, x, y).ratio() < 0.6


def venue_keys(venue: str) -> tuple[set[str], set[str]]:
    text = norm(venue)
    words = [w for w in text.split() if w not in STOPWORDS and not re.fullmatch(r"\d+(?:st|nd|rd|th)?", w)]
    keys = {key for key, names in VENUES.items() if key in text.split() or any(n in text for n in names)}
    keys |= {"".join(w[0] for w in words), "".join(w[0] for w in words if w not in GENERIC_VENUE)}
    return keys - {""}, set(words) - GENERIC_VENUE


def same_venue(cited: str, recorded: str) -> bool:
    (keys_a, words_a), (keys_b, words_b) = venue_keys(cited), venue_keys(recorded)
    return bool(keys_a & keys_b) or bool(words_a & words_b) or norm(cited) in norm(recorded)


def compare(ref: dict, record: dict) -> list[str]:
    problems = []
    titles = [t for t in (record.get("title"), record.get("main_title")) if t]  # cited with or without the subtitle
    if ref.get("title") and titles and not any(same_title(ref["title"], t) for t in titles):
        problems.append(f"title differs: the record says \"{record['title']}\"")
    recorded = [a for a in record.get("authors") or [] if a]
    listed = ref.get("authors") or ([ref["author"]] if ref.get("author") else [])
    if recorded and listed:
        names = ref.get("names") or []
        matched = [on_record(a, recorded, names[i] if i < len(names) else "") for i, a in enumerate(listed)]
        missing = [a for a, m in zip(listed, matched) if m is None]
        renamed = [f"{n} (the record has {m})" for n, m in zip(names, matched) if m and given_differs(n, m)]
        if len(listed) == 1 and missing:
            problems.append(f"first author differs: the record lists {', '.join(recorded[:3])}")
        elif missing:
            problems.append(f"{len(missing)} of the {len(listed)} cited authors are not on the record "
                            f"({', '.join(missing[:3])}); it lists {', '.join(recorded[:4])}"
                            + (" and others" if len(recorded) > 4 else ""))
        elif names and not ref.get("more_authors") and len(recorded) > len(listed):
            problems.append(f"the citation names {len(listed)} of the record's {len(recorded)} authors")
        if renamed:
            problems.append("given name differs: " + "; ".join(renamed[:3]))
    if ref.get("year") and record.get("year"):
        gap = ref["year"] - record["year"]  # a preprint can appear years before the version that is cited
        if not (-1 <= gap <= (3 if record.get("source", "").startswith("arXiv") else 1)):
            problems.append(f"year differs: the record says {record['year']}")
    cited, kept = ref.get("venue"), record.get("venue")
    if cited and kept and record.get("source", "").startswith("OpenReview") and UNPUBLISHED.search(kept):
        if same_venue(cited, UNPUBLISHED.sub("", kept)):
            problems.append(f"the record shows it as \"{kept}\", not a paper published there")
    elif cited and kept and record.get("source") in ("Crossref", "OpenReview (DBLP)") and not same_venue(cited, kept):
        problems.append(f"venue differs: the record says {kept}")
    return problems


# Looking records up.

def _get(url: str, raw: bool = False):
    """JSON (or, with raw, the text) from url; None on 404; OSError on any other failure. At most about 3
    requests a second, and one every 3 seconds to arXiv, as arXiv asks."""
    host = urllib.parse.urlsplit(url).netloc
    if host in _limited:  # it said "too many requests" and kept saying it: do not wait on it again this run
        raise OSError(f"HTTP 429 from {host} earlier in this run")
    wait = INTERVALS.get(host, INTERVAL) - (time.monotonic() - _last_call.get(host, 0.0))
    if wait > 0:
        time.sleep(wait)
    _last_call[host] = time.monotonic()
    accept = "application/atom+xml" if raw else "application/json"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                body = response.read().decode("utf-8")
                return body if raw else json.loads(body)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            if err.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(min(float(err.headers.get("Retry-After") or 2 ** attempt), 30))
                continue
            if err.code == 429 and host in FALLBACK_HOSTS:
                _limited.add(host)
            raise OSError(f"HTTP {err.code} from {host}") from err
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
        "authors": [" ".join(x for x in (a.get("given"), a.get("family")) if x) or a.get("name", "")
                    for a in item.get("author", [])],
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
    doi = re.sub(r"(?i)^(10\.48550/arxiv\.\d{4}\.\d{4,5})v\d+$", r"\1", doi.strip().rstrip("."))  # arXiv DOIs carry no version
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
            "authors": [" ".join(x for x in (c.get("givenName"), c.get("familyName")) if x) or c.get("name", "")
                        for c in attrs.get("creators", [])],
            "year": attrs.get("publicationYear"),
            "venue": attrs.get("publisher") if isinstance(attrs.get("publisher"), str) else "",
            "type": (attrs.get("types") or {}).get("resourceTypeGeneral"),
            "retracted": False,
            "concern": False,
            "corrected": False,
            "notices": [],
            "is_notice_for": [],
        }
    return openalex_doi(doi)


# OpenAlex covers works that Crossref and DataCite do not index well, among them many conference papers
# and journals outside the large publishers. It is asked only when those two have no record. Without
# a key it allows a limited number of requests a day; set ER_OPENALEX_KEY to use your own key.
OPENALEX = "https://api.openalex.org/works"
OPENALEX_FIELDS = "id,doi,title,publication_year,authorships,primary_location,type,is_retracted"
def _openalex(url: str) -> dict | None:
    key = os.environ.get("ER_OPENALEX_KEY", "").strip()
    try:
        return _get(url + (f"&api_key={urllib.parse.quote(key)}" if key else ""))
    except OSError as err:
        _unreached.append(f"OpenAlex: {err}")
        return None


def openalex_record(work: dict) -> dict:
    source = ((work.get("primary_location") or {}).get("source") or {})
    return {
        "source": "OpenAlex",
        "doi": (work.get("doi") or "").removeprefix("https://doi.org/") or None,
        "title": work.get("title") or "",
        "authors": [((a.get("author") or {}).get("display_name") or "") for a in work.get("authorships") or []],
        "year": work.get("publication_year"),
        "venue": source.get("display_name") or "",
        "type": work.get("type"),
        "retracted": bool(work.get("is_retracted")),
        "concern": False,
        "corrected": False,
        "notices": [],
        "is_notice_for": [],
    }


def openalex_doi(doi: str) -> dict | None:
    data = _openalex(f"{OPENALEX}/doi:{urllib.parse.quote(doi, safe='/:;()')}?select={OPENALEX_FIELDS}")
    return openalex_record(data) if data and data.get("id") else None


def openalex_search(ref: dict) -> dict | None:
    query = urllib.parse.quote((ref.get("title") or ref["raw"])[:300])
    data = _openalex(f"{OPENALEX}?search={query}&per-page=5&select={OPENALEX_FIELDS}")
    return best_match(ref, [openalex_record(w) for w in (data or {}).get("results", [])])


OPENREVIEW = "https://api2.openreview.net/notes/search"
UNPUBLISHED = re.compile(r"\b(?:submitted to|withdrawn|rejected|desk.rejected)\b", re.I)


def openreview_search(ref: dict) -> dict | None:
    """OpenReview holds ICLR, NeurIPS and TMLR papers and the DBLP index of computer-science venues, with
    each venue as DBLP records it ("ICML 2022") or as the conference decided ("Submitted to ICLR 2023")."""
    if not ref.get("title"):
        return None
    data = _get(f"{OPENREVIEW}?term={urllib.parse.quote(ref['title'][:300])}&type=terms&content=title&source=forum&limit=8")
    records = []
    for note in (data or {}).get("notes", []):
        content = note.get("content") or {}
        value = lambda key: (content.get(key) or {}).get("value") if isinstance(content.get(key), dict) else content.get(key)  # noqa: E731
        names = [a.get("fullname", "") if isinstance(a, dict) else str(a) for a in value("authors") or []]
        venue = str(value("venue") or "")
        year = YEAR_RE.search(venue)
        stamp = note.get("pdate") or note.get("cdate")
        records.append({
            "source": "OpenReview" + (" (DBLP)" if str(value("venueid") or "").startswith("dblp.org") else ""),
            "doi": None, "title": str(value("title") or ""), "authors": names,
            "year": int(year.group(1)) if year else (time.gmtime(stamp / 1000).tm_year if stamp else None),
            "venue": "" if venue.lower().startswith("corr") else venue, "type": "",
            "retracted": False, "concern": False, "corrected": False, "notices": [], "is_notice_for": [],
        })
    same = [r for r in records if same_title(ref["title"], r["title"])]
    if ref.get("venue") and same:  # DBLP keeps the preprint and the published paper apart: prefer the one cited
        same.sort(key=lambda r: not (r["venue"] and same_venue(ref["venue"], r["venue"])))
    return same[0] if same else best_match(ref, records)


ATOM = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}


def arxiv_search(ref: dict) -> dict | None:
    """arXiv holds most machine-learning papers, which Crossref often lacks (NeurIPS, ICLR and ICML papers
    have no Crossref DOI). Searched by the title's longest words."""
    if not ref.get("title"):
        return None
    words = sorted({w for w in norm(ref["title"]).split() if w not in STOPWORDS and len(w) > 2}, key=len, reverse=True)[:6]
    if not words:
        return None
    query = urllib.parse.quote(" AND ".join(f"ti:{w}" for w in words))
    feed = _get(f"https://{ARXIV_HOST}/api/query?search_query={query}&max_results=5", raw=True)
    records = []
    for entry in ElementTree.fromstring(feed).findall("a:entry", ATOM) if feed else []:
        published = entry.findtext("a:published", "", ATOM)
        records.append({
            "source": "arXiv", "doi": entry.findtext("x:doi", None, ATOM),
            "arxiv": entry.findtext("a:id", "", ATOM).rsplit("/abs/", 1)[-1],
            "title": " ".join(entry.findtext("a:title", "", ATOM).split()),
            "authors": [a.findtext("a:name", "", ATOM) for a in entry.findall("a:author", ATOM)],
            "year": int(published[:4]) if published[:4].isdigit() else None,
            "venue": entry.findtext("x:journal_ref", "", ATOM), "type": "preprint",
            "retracted": False, "concern": False, "corrected": False, "notices": [], "is_notice_for": [],
        })
    return best_match(ref, records)


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
    return best_match(ref, [crossref_record(item) for item in ((data or {}).get("message") or {}).get("items", [])])


def best_match(ref: dict, records: list[dict]) -> dict | None:
    best, best_score = None, 0.0
    for record in records:
        if not record["title"]:
            continue
        score = similarity(ref["title"], record["title"]) if ref.get("title") else within(ref["raw"], record["title"])
        if score > best_score:
            best, best_score = record, score
    if best and best_score >= SEARCH_ACCEPT:
        best["match"] = round(best_score, 3)
        return best
    return None


def check(ref: dict) -> dict:
    out = {"reference": ref["raw"][:300], "status": "unchecked", "detail": "", "record": None}
    _unreached.clear()
    placeholder = [n for n in ref.get("names", [ref.get("author") or ""]) if PLACEHOLDER.match(n.strip())]
    if placeholder:
        out.update(status="metadata mismatch", detail=f"placeholder author name: {placeholder[0]}")
        return out
    try:
        if ref.get("doi"):
            record = resolve_doi(ref["doi"])
            how = f"DOI {ref['doi']}"
            if record is None:
                out.update(status="not found", detail=f"{how} does not resolve in Crossref, DataCite or OpenAlex{_unreached_note()}")
                return out
        elif ref.get("arxiv"):
            record = resolve_arxiv(ref["arxiv"])
            how = f"arXiv {ref['arxiv']}"
            if record is None:
                out.update(status="not found", detail=f"{how} has no record")
                return out
        else:  # the first source with a record that agrees wins; else the first record found, to show the mismatch
            record, how = search(ref), "a Crossref bibliographic search"
            for name, fallback in (("arXiv", arxiv_search), ("OpenReview", openreview_search), ("OpenAlex", openalex_search)):
                if record is not None and not compare(ref, record):
                    break
                other = _try(name, fallback, ref)
                if other is not None and (record is None or not compare(ref, other)):
                    record, how = other, f"an {name} search"
            if record is None:
                out.update(status="not found", detail="no record in Crossref, arXiv, OpenReview or OpenAlex matches this citation"
                                                      f"{_unreached_note()}; it may still exist outside them (books, many "
                                                      "Korean journals, theses): find the source")
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


_unreached: list[str] = []  # fallback sources that could not be asked for this reference, and why


def _try(name: str, lookup, ref: dict) -> dict | None:
    try:
        return lookup(ref)
    except (OSError, ElementTree.ParseError) as err:
        _unreached.append(f"{name}: {err}")
        return None


def _unreached_note() -> str:
    return f" ({'; '.join(_unreached)} could not be reached)" if _unreached else ""


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


# Finding candidate sources in the record, never from memory.

FIND_TYPES = {"journal-article", "proceedings-article", "book-chapter", "book", "posted-content", "monograph", "report"}


def find(topic: str, rows: int = 10, since: int | None = None) -> list[dict]:
    """Works on a topic, from Crossref's index: each one a record, none recalled. Retracted works and
    retraction notices are kept and marked, so they are seen and not cited by accident."""
    params = f"query.bibliographic={urllib.parse.quote(topic[:300])}&rows={min(max(rows * 2, 10), 50)}"
    if since:
        params += f"&filter=from-pub-date:{since}"
    mail = _mailto()
    data = _get(f"https://api.crossref.org/works?{params}" + (f"&{mail}" if mail else ""))
    found = []
    for item in ((data or {}).get("message") or {}).get("items", []):
        record = crossref_record(item)
        if record["type"] in FIND_TYPES and record["title"] and record["authors"]:
            found.append(record)
        if len(found) == rows:
            break
    return found


def render_found(topic: str, records: list[dict]) -> str:
    lines = [f"Works in Crossref for: {topic}", "",
             "| # | Authors (year) | Title | Venue | DOI | Status |", "| ---: | --- | --- | --- | --- | --- |"]
    for i, r in enumerate(records, 1):
        names = ", ".join(r["authors"][:3]) + (" et al." if len(r["authors"]) > 3 else "")
        status = ("RETRACTED: do not cite" if r["retracted"] else "expression of concern" if r["concern"]
                  else "a retraction or other notice, not an article" if r["is_notice_for"]
                  else "record found, not read" + ("; corrected" if r["corrected"] else ""))
        cell = lambda text: (text or "").replace("|", "/")  # noqa: E731
        lines.append(f"| {i} | {cell(names)} ({r['year'] or 'n.d.'}) | {cell(r['title'])} | {cell(r['venue'])} | "
                     f"{r['doi'] or ''} | {status} |")
    lines += ["", "Each line is a record in the index, so the work exists. None has been read: whether it is relevant, "
              "sound and supports a claim needs the source itself. Search the field's own indexes too; one query in one "
              "index is not a literature search."]
    return chr(10).join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check references against Crossref, DataCite, OpenAlex and arXiv, "
                                                 "or find candidate works on a topic in Crossref.")
    parser.add_argument("source", nargs="?", help="a file of references (BibTeX or one per line), or - for standard input")
    parser.add_argument("--find", metavar="TOPIC", help="list works on a topic from Crossref instead of checking references")
    parser.add_argument("--rows", type=int, default=10, help="how many works --find lists (default 10)")
    parser.add_argument("--since", type=int, help="with --find, only works published from this year on")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    if args.find:
        try:
            records = find(args.find, args.rows, args.since)
        except OSError as err:
            print(f"Crossref could not be reached: {err}", file=sys.stderr)
            return 2
        print(json.dumps(records, indent=2, ensure_ascii=False) if args.json else render_found(args.find, records))
        return 0
    if not args.source:
        parser.error("give a file of references, - for standard input, or --find TOPIC")
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
