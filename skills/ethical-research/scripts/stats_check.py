#!/usr/bin/env python3
"""Check reported statistics for internal consistency. Standard library only.

Two published, deterministic checks:

  p-values   Recomputes the p-value of each APA-style t, F, chi-square, r and z result from
             its test statistic and degrees of freedom, as statcheck does (Nuijten et al.,
             2016). A result is inconsistent when no statistic that rounds to the reported one
             gives the reported p-value, and a decision error when the recomputed p-value
             falls on the other side of .05.
  GRIM       Tests whether a mean reported to d decimals can come from n integer responses
             (Brown & Heathers, 2017).

Usage:
  python stats_check.py paper.txt            scan a text file for APA-style results
  python stats_check.py -                    scan standard input
  python stats_check.py --grim 3.48 25       mean, sample size
  python stats_check.py --grim 3.48 25 4     mean, sample size, items per scale
  add --json for machine-readable output

Exit status: 0 when everything checked is consistent, 1 when anything is not.
An inconsistency is a question for the author, not proof of misconduct: typos, one-tailed tests
and corrected p-values all produce them. Results in a sentence that mentions a correction
(Bonferroni, Holm, Greenhouse-Geisser, Welch, adjusted p) are marked "check by hand" instead of
flagged, and one-tailed tests are recognised from the words one-tailed, one-sided or directional.
statcheck itself has documented misses and false flags (Schmidt, 2017; Boschen, 2024), so this
check reads only complete APA-style results.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from decimal import ROUND_HALF_UP, Decimal

ALPHA = 0.05


# Distributions, from the regularized incomplete beta and gamma functions
# (Press et al., Numerical Recipes, 3rd ed., sections 6.2 and 6.4).

def _betacf(a: float, b: float, x: float) -> float:
    tiny, eps = 1e-300, 3e-16
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 1000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        step = d * c
        h *= step
        if abs(step - 1.0) < eps:
            break
    return h


def betai(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def gammq(a: float, x: float) -> float:
    """Upper regularized incomplete gamma function Q(a, x)."""
    if x <= 0.0:
        return 1.0
    if x < a + 1.0:
        term = total = 1.0 / a
        ap = a
        for _ in range(10000):
            ap += 1.0
            term *= x / ap
            total += term
            if abs(term) < abs(total) * 3e-16:
                break
        return 1.0 - total * math.exp(-x + a * math.log(x) - math.lgamma(a))
    tiny = 1e-300
    b = x + 1.0 - a
    c, d = 1.0 / tiny, 1.0 / b
    h = d
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = b + an / c
        c = c if abs(c) > tiny else tiny
        step = d * c
        h *= step
        if abs(step - 1.0) < 3e-16:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def p_value(test: str, stat: float, df1: float | None = None, df2: float | None = None) -> float:
    """Two-tailed p for t, r and z; upper tail for F and chi-square."""
    if test == "t":
        return betai(df1 / 2.0, 0.5, df1 / (df1 + stat * stat))
    if test == "r":
        if abs(stat) >= 1.0:
            return 0.0
        t = stat * math.sqrt(df1 / (1.0 - stat * stat))
        return p_value("t", t, df1)
    if test == "z":
        return math.erfc(abs(stat) / math.sqrt(2.0))
    if test == "F":
        if stat <= 0.0:
            return 1.0
        return betai(df2 / 2.0, df1 / 2.0, df2 / (df2 + df1 * stat))
    if test == "chi2":
        return gammq(df1 / 2.0, stat / 2.0)
    raise ValueError(f"unknown test {test!r}")


# Parsing APA-style results.

MINUS = "−–—"
NUM = rf"[-{MINUS}]?\s?(?:\d+\.?\d*|\.\d+)"
DF = r"\d+(?:\.\d+)?"
P = r"(?P<pcmp><=|>=|[=<>≤≥])\s*(?P<p>(?:0?\.\d+|1(?:\.0+)?|0))"
TESTS = {
    "t": rf"\bt\s*\(\s*(?P<df1>{DF})\s*\)\s*=\s*(?P<stat>{NUM})",
    "F": rf"\bF\s*\(\s*(?P<df1>{DF})\s*,\s*(?P<df2>{DF})\s*\)\s*=\s*(?P<stat>{NUM})",
    "chi2": rf"(?:χ\s*2|χ²|χ2|\bchi2|\bchi-square|\bX2)\s*\(\s*(?P<df1>{DF})\s*(?:,\s*[Nn]\s*=\s*\d[\d,]*)?\s*\)\s*=\s*(?P<stat>{NUM})",
    "r": rf"\br\s*\(\s*(?P<df1>{DF})\s*\)\s*=\s*(?P<stat>{NUM})",
    "z": rf"\b[zZ]\s*=\s*(?P<stat>{NUM})",
}
PATTERNS = {name: re.compile(body + rf"\s*,\s*(?:ns\b|p\s*{P})") for name, body in TESTS.items()}
ONE_TAILED = re.compile(r"one[- ](?:tailed|sided)|directional", re.I)
CORRECTED = re.compile(r"bonferroni|holm|greenhouse|geisser|huynh|welch|adjust|correct(?:ed|ion) for|"
                       r"false discovery|\bfdr\b|sid[a\u00e1]k|tukey", re.I)


def _number(text: str) -> float:
    text = text.replace(" ", "")
    for ch in MINUS:
        text = text.replace(ch, "-")
    return float(text)


def _decimals(text: str) -> int:
    text = text.strip().lstrip("-" + MINUS).strip()
    return len(text.split(".", 1)[1]) if "." in text else 0


def check_result(test: str, stat_text: str, df1: float | None, df2: float | None,
                 pcmp: str | None, p_text: str | None, one_tailed: bool = False) -> dict:
    stat = _number(stat_text)
    half = 0.5 * 10 ** -_decimals(stat_text)
    if test in ("F", "chi2"):
        lo, hi = max(stat - half, 0.0), stat + half
    else:
        lo, hi = max(abs(stat) - half, 0.0), abs(stat) + half
    p_lo, p_hi = p_value(test, hi, df1, df2), p_value(test, lo, df1, df2)
    exact = p_value(test, stat, df1, df2)
    if one_tailed and test in ("t", "r", "z"):
        p_lo, p_hi, exact = p_lo / 2, p_hi / 2, exact / 2
    row = {"test": test, "statistic": stat, "df1": df1, "df2": df2, "reported": None,
           "recomputed": exact, "one_tailed": one_tailed, "status": "consistent"}
    if pcmp is None:  # reported as "ns"
        row["reported"] = "ns"
        if p_hi < ALPHA:
            row["status"] = "decision error"
        return row
    cmp = {"≤": "<=", "≥": ">="}.get(pcmp, pcmp)
    p_rep = float(p_text)
    row["reported"] = f"p {cmp} {p_text}"
    if cmp == "=":
        half_p = 0.5 * 10 ** -_decimals(p_text)
        ok = p_lo <= p_rep + half_p and p_hi >= p_rep - half_p
        claims_sig = p_rep < ALPHA
        claims_ns = p_rep > ALPHA
    elif cmp in ("<", "<="):
        ok = p_lo < p_rep or (cmp == "<=" and p_lo <= p_rep)
        claims_sig, claims_ns = p_rep <= ALPHA, False
    else:
        ok = p_hi > p_rep or (cmp == ">=" and p_hi >= p_rep)
        claims_sig, claims_ns = False, p_rep >= ALPHA
    if not ok:
        decision = (claims_sig and p_lo >= ALPHA) or (claims_ns and p_hi < ALPHA)
        row["status"] = "decision error" if decision else "inconsistent"
    return row


def scan(text: str) -> list[dict]:
    rows = []
    for test, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            df1 = float(m.group("df1")) if "df1" in pattern.groupindex and m.group("df1") else None
            df2 = float(m.group("df2")) if "df2" in pattern.groupindex and m.group("df2") else None
            start = text.rfind(".", 0, m.start()) + 1
            end = text.find(".", m.end())
            sentence = text[start:end if end != -1 else len(text)]
            row = check_result(test, m.group("stat"), df1, df2, m.group("pcmp"), m.group("p"),
                               bool(ONE_TAILED.search(sentence)))
            if row["status"] != "consistent" and CORRECTED.search(sentence):
                row["status"] = "check by hand"  # the recomputed p ignores the correction the text mentions
            row["text"] = " ".join(m.group(0).split())
            row["offset"] = m.start()
            rows.append(row)
    rows.sort(key=lambda r: r["offset"])
    return rows


def grim(mean_text: str, n: int, items: int = 1) -> dict:
    """GRIM: can a mean with this many decimals come from n * items integer responses?"""
    decimals = _decimals(mean_text)
    total = n * items
    row = {"mean": mean_text, "n": n, "items": items, "status": "consistent"}
    if total >= 10 ** decimals:
        row["status"] = "not testable"  # every mean at this precision is possible
        return row
    target = Decimal(mean_text)
    quantum = Decimal(1).scaleb(-decimals)
    centre = int(target * total)
    for s in range(centre - 2, centre + 3):
        if (Decimal(s) / Decimal(total)).quantize(quantum, rounding=ROUND_HALF_UP) == target:
            return row
    row["status"] = "inconsistent"
    return row


def _table(rows: list[dict]) -> str:
    if not rows:
        return "No APA-style t, F, chi-square, r or z results found."
    lines = ["| # | Result | Recomputed p | Status |", "| ---: | --- | ---: | --- |"]
    for i, r in enumerate(rows, 1):
        tail = ", one-tailed" if r["one_tailed"] else ""
        lines.append(f"| {i} | {r['text']} | {r['recomputed']:.4f}{tail} | {r['status']} |")
    bad = sum(r["status"] in ("inconsistent", "decision error") for r in rows)
    lines.append("")
    lines.append(f"{len(rows)} results, {bad} not consistent.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source", nargs="?", help="text file to scan, or - for standard input")
    parser.add_argument("--grim", nargs="+", metavar="VALUE", help="mean n [items]")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)
    if args.grim:
        if len(args.grim) not in (2, 3):
            parser.error("--grim takes a mean, a sample size and optionally items per scale")
        row = grim(args.grim[0], int(args.grim[1]), int(args.grim[2]) if len(args.grim) == 3 else 1)
        print(json.dumps(row) if args.json else f"GRIM {row['mean']} with n = {row['n']}"
              f"{', ' + str(row['items']) + ' items' if row['items'] > 1 else ''}: {row['status']}")
        return 1 if row["status"] == "inconsistent" else 0
    if not args.source:
        parser.error("give a file, - for standard input, or --grim")
    if args.source == "-":
        text = sys.stdin.read()
    else:
        with open(args.source, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    rows = scan(text)
    print(json.dumps(rows, indent=2) if args.json else _table(rows))
    return 1 if any(r["status"] in ("inconsistent", "decision error") for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
