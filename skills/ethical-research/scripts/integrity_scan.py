#!/usr/bin/env python3
"""Scan a manuscript for integrity defects that can be found in code. Standard library only.

What it finds, and how sure each finding is:

  error     hidden instructions aimed at AI reviewers or assistants (also when drawn in white,
            at a tiny size, as invisible text, or in LaTeX comments); invisible Unicode tag
            characters, which can carry a hidden message
  warn      chatbot text left in the manuscript (possible undisclosed AI use: check the AI-use
            statement); tortured phrases (synonym-swapped technical terms, a paper-mill signature,
            meaningful in numbers rather than one at a time); unfilled placeholders such as
            [citation needed]; zero-width and bidirectional control characters
  question  claims stated more strongly than most evidence allows ("proves", "for the first time");
            these are questions for the author, not errors

What it does not do: it does not guess whether text was written by AI. Style-based AI detectors
are unreliable and flag non-native writers far more often, and this tool will not help anyone tune
text to pass one. A clean scan says these defects were not found; it does not certify a paper.

Formats: .txt .md .tex .docx .pdf (PDF text is read from uncompressed and Flate-compressed content
streams; fonts with custom encodings cannot be decoded without a PDF library, so the scan says how
many text runs it could not read, and you can scan pdftotext output as well).

  python integrity_scan.py paper.pdf
  python integrity_scan.py draft.docx --json
  cat abstract.txt | python integrity_scan.py -

Exit status 1 when any error-level finding is present, otherwise 0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import zipfile
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path

# Instructions addressed to an AI model, of the kind found hidden in submitted papers.
INJECTION = [
    r"ignore (?:all |any )?(?:the )?(?:previous|prior|above|preceding|earlier) (?:instructions|prompts|directions)",
    r"disregard (?:all |any )?(?:the )?(?:previous|prior|above) (?:instructions|prompts)",
    r"give (?:this paper |this manuscript |it )?(?:a |only )?(?:positive|favou?rable|glowing) (?:review|evaluation|assessment)",
    r"(?:do not|don't) (?:highlight|mention|point out|list) (?:any )?(?:negatives|weaknesses|limitations|flaws)",
    r"(?:recommend|suggest) (?:its |the paper'?s? |this paper'?s? )?accept(?:ance|ing)?(?: of this (?:paper|manuscript))?",
    r"for (?:llm|ai|language model) reviewers",
    r"(?:as|you are) an? (?:llm|ai|language model)[^.\n]{0,40}(?:review|rate|score|evaluate)",
    r"rate this (?:paper|manuscript|submission) (?:highly|as (?:excellent|strong|outstanding))",
    r"new instructions?:",
    r"system prompt:",
    r"\uc774\uc804\s*\uc9c0\uc2dc(?:\ub97c|\uc0ac\ud56d\uc744)?\s*\ubb34\uc2dc",  # Korean: ignore the previous instructions
    r"\uae0d\uc815\uc801(?:\uc778)?\s*(?:\ub9ac\ubdf0|\ud3c9\uac00|\uc2ec\uc0ac)",  # Korean: positive review/evaluation
]

# Text that chatbots produce, kept to strings specific enough to flag on their own (Glynn, "Academ-AI",
# arXiv:2411.15218, Table 1, and the cases reported by Cabanac and colleagues).
CHAT_ARTIFACTS = [
    r"as an ai language model", r"as a large language model", r"regenerate response",
    r"as of my (?:last )?knowledge (?:update|cutoff)", r"my knowledge cutoff",
    r"i (?:do not|don't) have access to real-time", r"certainly[!,.]? here (?:is|are)",
    r"here is (?:a|an|the) (?:revised|rewritten|improved|polished) version", r"i cannot provide (?:you with )?(?:a|an|the|specific)",
]

PLACEHOLDERS = [
    r"\[(?:citation needed|insert (?:citation|reference|ref|source|figure|table|name|date)[^\]]*|"
    r"reference|ref|cite|your name|author name|journal name|year|doi|source)\]",
    r"\((?:author|authors),? (?:year|20xx|19xx)\)", r"et al\.,? (?:20xx|19xx|n\.d\.\?)",
    r"\bxx\.xx%|\bp\s*[<=]\s*0?\.0x\b", r"lorem ipsum",
]

# Synonym-swapped technical terms (tortured phrases), from Table 1 of Cabanac, Labbe & Magazinov,
# "Tortured phrases: A dubious writing style emerging in science" (2021, arXiv:2107.06751).
# Some have legitimate uses; the Problematic Paper Screener flags a paper at five or more.
TORTURED = {
    r"profound neural organi[sz]ation": "deep neural network",
    r"(?:fake|counterfeit) neural organi[sz]ation": "artificial neural network",
    r"versatile organi[sz]ation": "mobile network",
    r"organi[sz]ation (?:ambush|assault)": "network attack",
    r"(?:enormous|huge|immense|colossal) information": "big data",
    r"information (?:stockroom|distribution center)": "data warehouse",
    r"(?:counterfeit|human-made|man-made) consciousness": "artificial intelligence",
    r"elite figuring": "high performance computing",
    r"haze figuring": "fog or cloud computing",
    r"designs preparing unit": "graphics processing unit",
    r"focal preparing unit": "central processing unit",
    r"facial acknowledg(?:e)?ment": "face recognition",
    r"discourse acknowledg(?:e)?ment": "voice recognition",
    r"mean square (?:mistake|blunder)": "mean square error",
    r"mean (?:outright|supreme) (?:mistake|blunder)": "mean absolute error",
    r"(?:flag|motion|sign|indicator) to (?:clamor|commotion)": "signal to noise",
    r"(?:arbitrary|irregular) (?:backwoods|timberland|lush territory|woodland)": "random forest",
    r"(?:arbitrary|irregular) get right of passage to": "random access",
    r"subterranean insect (?:state|province|area|region|settlement)": "ant colony",
    r"leftover vitality": "remaining energy",
    r"motor vitality": "kinetic energy",
    r"(?:credulous|innocent|gullible) bayes": "naive Bayes",
    r"individual computeri[sz]ed collaborator": "personal digital assistant",
    r"profound learning": "deep learning",
}
TORTURED_THRESHOLD = 5

OVERCLAIM = [
    r"\bprove[sd]?\b", r"\bproof that\b", r"\bclearly (?:demonstrates?|shows?|proves?)\b",
    r"\bfor the first time\b", r"\bundoubtedly\b", r"\bunequivocally\b", r"\bdefinitively\b",
    r"\bgroundbreaking\b", r"\brevolutioni[sz]e[sd]?\b", r"\bparadigm shift\b",
    r"\bit is (?:well|widely) known that\b", r"\beveryone (?:knows|agrees)\b",
    r"\b(?:causes|caused|leads to|results in)\b(?=[^.]{0,80}\b(?:survey|correlat|associat|cross-sectional)\b)",
]

ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0xFEFF}
BIDI = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))


@dataclass
class Finding:
    level: str      # error, warn, question
    kind: str
    line: int
    excerpt: str
    note: str = ""


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _visible(text: str) -> str:
    """Invisible characters shown as code points, so an excerpt never hides what it reports."""
    return "".join(f"<U+{ord(ch):04X}>" if (0xE0000 <= ord(ch) <= 0xE007F or ord(ch) in ZERO_WIDTH or ord(ch) in BIDI)
                   else ch for ch in text)


def _excerpt(text: str, start: int, end: int, pad: int = 40) -> str:
    left, right = max(0, start - pad), min(len(text), end + pad)
    return " ".join(_visible(text[left:right]).split())


def scan_text(text: str, hidden: list[tuple[str, str]] | None = None) -> list[Finding]:
    """Scan plain text. `hidden` holds (how it was hidden, text) runs found by the format readers."""
    findings: list[Finding] = []
    folded = unicodedata.normalize("NFKC", text)

    tags = [ch for ch in text if 0xE0000 <= ord(ch) <= 0xE007F]
    if tags:
        message = "".join(chr(ord(ch) - 0xE0000) for ch in tags if 0x20 <= ord(ch) - 0xE0000 < 0x7F)
        pos = next(i for i, ch in enumerate(text) if 0xE0000 <= ord(ch) <= 0xE007F)
        findings.append(Finding("error", "invisible tag characters", _line(text, pos), message[:200],
                                f"{len(tags)} Unicode tag characters; they render as nothing and can carry instructions"))
    zw = [i for i, ch in enumerate(text) if ord(ch) in ZERO_WIDTH and not (i == 0 and ord(ch) == 0xFEFF)]
    if zw:
        findings.append(Finding("warn", "zero-width characters", _line(text, zw[0]), _excerpt(text, zw[0], zw[0] + 1),
                                f"{len(zw)} zero-width characters"))
    bidi = [i for i, ch in enumerate(text) if ord(ch) in BIDI]
    if bidi:
        findings.append(Finding("warn", "bidirectional controls", _line(text, bidi[0]),
                                _excerpt(text, bidi[0], bidi[0] + 1), f"{len(bidi)} bidirectional control characters"))

    for level, kind, patterns, note in (
        ("error", "instruction to an AI", INJECTION, "text addressed to an AI reviewer or assistant"),
        ("warn", "chatbot text", CHAT_ARTIFACTS, "possible undisclosed AI text: check the AI-use statement"),
        ("warn", "placeholder", PLACEHOLDERS, "unfilled placeholder"),
        ("question", "strong claim", OVERCLAIM, "is the evidence as strong as the wording?"),
    ):
        for pattern in patterns:
            for m in re.finditer(pattern, folded, re.I):
                findings.append(Finding(level, kind, _line(folded, m.start()), _excerpt(folded, m.start(), m.end()), note))
    tortured = []
    for pattern, meaning in TORTURED.items():
        for m in re.finditer(r"\b" + pattern + r"\b", folded, re.I):
            tortured.append(Finding("warn", "tortured phrase", _line(folded, m.start()),
                                    _excerpt(folded, m.start(), m.end()), f"the standard term is '{meaning}'"))
    if len(tortured) >= TORTURED_THRESHOLD:
        findings.append(Finding("error", "paper-mill signature", tortured[0].line, f"{len(tortured)} tortured phrases",
                                f"{TORTURED_THRESHOLD} or more is the Problematic Paper Screener's threshold"))
    findings += tortured
    for how, run in hidden or []:
        if run.strip():
            injected = any(re.search(p, run, re.I) for p in INJECTION)
            findings.append(Finding("error" if injected else "warn", f"hidden text ({how})", 0, run.strip()[:200],
                                    "instructions to an AI, hidden from human readers" if injected
                                    else "text a human reader cannot see"))
    findings.sort(key=lambda f: ({"error": 0, "warn": 1, "question": 2}[f.level], f.line))
    return _dedupe(findings)


def _dedupe(findings: list[Finding]) -> list[Finding]:
    seen, out = set(), []
    for f in findings:
        # one finding per kind per line, except distinct tortured phrases and hidden runs
        key = (f.kind, f.line, f.note if f.kind == "tortured phrase" else f.excerpt if f.kind.startswith("hidden") else "")
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


# Format readers. Each returns (visible text, hidden runs, notes).

def read_tex(source: str) -> tuple[str, list[tuple[str, str]], list[str]]:
    hidden = []
    for m in re.finditer(r"(?<!\\)%(.*)", source):
        if any(re.search(p, m.group(1), re.I) for p in INJECTION):
            hidden.append(("LaTeX comment", m.group(1)))
    for m in re.finditer(r"\\(?:textcolor|color)\s*\{\s*white\s*\}\s*\{?([^}\n]{3,})", source, re.I):
        hidden.append(("white text", m.group(1)))
    for m in re.finditer(r"\\fontsize\s*\{\s*0?\.\d+\s*(?:pt)?\s*\}[^\n]*?\\selectfont\s*([^}\n]{3,})", source):
        hidden.append(("tiny font", m.group(1)))
    return source, hidden, []


def read_docx(path: Path) -> tuple[str, list[tuple[str, str]], list[str]]:
    with zipfile.ZipFile(path) as z:
        xml = "".join(z.read(n).decode("utf-8", "replace") for n in z.namelist()
                      if n.startswith("word/") and n.endswith(".xml") and ("document" in n or "footnotes" in n
                                                                             or "header" in n or "footer" in n))
    visible, hidden = [], []
    for para in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        texts = []
        for run in re.findall(r"<w:r[ >].*?</w:r>", para, re.S):
            text = "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", run))
            if not text:
                continue
            props = (re.search(r"<w:rPr>(.*?)</w:rPr>", run, re.S) or [None, ""])[1]
            size = re.search(r'<w:sz w:val="(\d+)"', props)
            if "<w:vanish" in props:
                hidden.append(("hidden text", text))
            elif re.search(r'<w:color w:val="(?:FFFFFF|ffffff)"', props):
                hidden.append(("white text", text))
            elif size and int(size.group(1)) <= 4:  # half-points: 2pt or smaller
                hidden.append(("tiny font", text))
            texts.append(text)
        visible.append("".join(texts))
    return _unescape("\n".join(visible)), [(h, _unescape(t)) for h, t in hidden], []


def _unescape(text: str) -> str:
    return (text.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
            .replace("&apos;", "'").replace("&amp;", "&"))


PDF_STREAM = re.compile(rb"<<(.*?)>>\s*stream\r?\n(.*?)\r?\n?endstream", re.S)
PDF_TOKEN = re.compile(rb"\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]*>|\[|\]|/[^\s/\[\]()<>]+|[-+]?\d*\.?\d+|[A-Za-z'\"*]+")


def _pdf_string(token: bytes) -> str | None:
    if token.startswith(b"("):
        body = token[1:-1]
        body = re.sub(rb"\\([nrtbf()\\])", lambda m: {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"", b"f": b"",
                                                       b"(": b"(", b")": b")", b"\\": b"\\"}[m.group(1)], body)
        body = re.sub(rb"\\([0-7]{1,3})", lambda m: bytes([int(m.group(1), 8) & 255]), body)
        return body.decode("latin-1")
    return None  # hex strings are glyph ids in most modern PDFs; not decodable without the font


PDF_META = re.compile(rb"/(Title|Subject|Keywords|Author|Creator)\s*(\((?:\\.|[^\\)])*\))")
XMP_TEXT = re.compile(r"<(dc:description|dc:title|dc:subject|pdf:Keywords)[^>]*>(.*?)</\1>", re.S)
NUMBER = re.compile(rb"[-+]?\d*\.?\d+")


def _metadata(data: bytes) -> list[tuple[str, str]]:
    """Instructions placed in the document's metadata, where a reader never looks but a tool may."""
    found = [(m.group(1).decode(), _pdf_string(m.group(2)) or "") for m in PDF_META.finditer(data)]
    for m in PDF_STREAM.finditer(data):
        if b"/Metadata" in m.group(1) or b"/XML" in m.group(1):
            xml = m.group(2).decode("utf-8", "replace")
            found += [(tag, re.sub(r"<[^>]+>", " ", body)) for tag, body in XMP_TEXT.findall(xml)]
    return [("PDF metadata", f"{field}: {text.strip()}") for field, text in found
            if any(re.search(p, text, re.I) for p in INJECTION)]


def read_pdf(path: Path) -> tuple[str, list[tuple[str, str]], list[str]]:
    data = path.read_bytes()
    visible, hidden, undecoded = [], [], 0
    box = re.search(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", data)
    x0, y0, x1, y1 = (float(v) for v in box.groups()) if box else (0.0, 0.0, 612.0, 792.0)
    hidden += _metadata(data)
    for m in PDF_STREAM.finditer(data):
        head, body = m.group(1), m.group(2)
        if b"/FlateDecode" in head:
            try:
                body = zlib.decompress(body)
            except zlib.error:
                continue
        elif b"/Filter" in head:
            continue
        if b"Tj" not in body and b"TJ" not in body:
            continue
        fill_white, size, render, buf = False, 10.0, 0, []
        stack: list[bytes] = []
        ctm, saved, tx, ty = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0), [], 0.0, 0.0  # page transform; text position
        for tok in PDF_TOKEN.findall(body):
            nums = [float(t) for t in stack if NUMBER.fullmatch(t)]
            if tok == b"q":
                saved.append(ctm)
            elif tok == b"Q":
                ctm = saved.pop() if saved else ctm
            elif tok == b"cm" and len(nums) >= 6:
                a, b, c, d, e, f = nums[-6:]
                A, B, C, D, E, F = ctm
                ctm = (a * A + b * C, a * B + b * D, c * A + d * C, c * B + d * D, e * A + f * C + E, e * B + f * D + F)
            elif tok == b"Tm" and len(nums) >= 6:
                tx, ty = nums[-2], nums[-1]
            elif tok in (b"Td", b"TD") and len(nums) >= 2:
                tx, ty = tx + nums[-2], ty + nums[-1]
            if tok in (b"q", b"Q", b"cm", b"Tm", b"Td", b"TD"):
                stack = []
                continue
            if tok in (b"rg", b"g", b"k", b"sc", b"scn"):
                nums = [float(t) for t in stack if re.fullmatch(rb"[-+]?\d*\.?\d+", t)]
                fill_white = (tok == b"k" and nums[-4:] == [0, 0, 0, 0]) or (
                    tok != b"k" and bool(nums) and all(n >= 0.97 for n in nums[-3:]))
                stack = []
            elif tok == b"Tf":
                nums = [t for t in stack if re.fullmatch(rb"[-+]?\d*\.?\d+", t)]
                size = abs(float(nums[-1])) if nums else size
                stack = []
            elif tok == b"Tr":
                nums = [t for t in stack if re.fullmatch(rb"[-+]?\d*\.?\d+", t)]
                render = int(float(nums[-1])) if nums else render
                stack = []
            elif tok in (b"Tj", b"TJ", b"'", b'"'):
                strings = [_pdf_string(t) for t in stack if t.startswith((b"(", b"<"))]
                undecoded += sum(s is None for s in strings)
                text = "".join(s for s in strings if s)
                stack = []
                if not text:
                    continue
                px = ctm[0] * tx + ctm[2] * ty + ctm[4]
                py = ctm[1] * tx + ctm[3] * ty + ctm[5]
                off_page = not (x0 - 20 <= px <= x1 + 20 and y0 - 20 <= py <= y1 + 20)
                how = ("invisible render mode" if render == 3 else "white text" if fill_white
                       else "tiny font" if size < 2 else "off the page" if off_page else None)
                if how:
                    hidden.append((how, text))
                else:
                    buf.append(text)
            elif tok in (b"ET", b"BT"):
                if buf:
                    visible.append("".join(buf))
                    buf = []
                stack, tx, ty = [], 0.0, 0.0
            else:
                stack.append(tok)
        if buf:
            visible.append("".join(buf))
    notes = []
    if undecoded:
        notes.append(f"{undecoded} text runs use font encodings this scanner cannot decode; "
                     "also scan the output of `pdftotext` for full coverage")
    hidden = _merge_runs(hidden)
    return "\n".join(visible), hidden, notes


def _merge_runs(runs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    merged: list[tuple[str, str]] = []
    for how, text in runs:
        if merged and merged[-1][0] == how:
            merged[-1] = (how, merged[-1][1] + text)
        else:
            merged.append((how, text))
    return merged


def scan_path(source: str) -> dict:
    notes: list[str] = []
    hidden: list[tuple[str, str]] = []
    if source == "-":
        text = sys.stdin.read()
    else:
        path = Path(source)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            text, hidden, notes = read_pdf(path)
        elif suffix == ".docx":
            text, hidden, notes = read_docx(path)
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
            if suffix == ".tex":
                text, hidden, notes = read_tex(text)
    findings = scan_text(text, hidden)
    return {"source": source, "characters": len(text), "notes": notes,
            "counts": {lvl: sum(f.level == lvl for f in findings) for lvl in ("error", "warn", "question")},
            "findings": [asdict(f) for f in findings]}


def render(report: dict) -> str:
    c = report["counts"]
    lines = [f"{report['source']}: {c['error']} errors, {c['warn']} warnings, {c['question']} questions "
             f"({report['characters']} characters read)"]
    for note in report["notes"]:
        lines.append(f"note: {note}")
    if report["findings"]:
        lines += ["", "| Level | Kind | Line | Excerpt | Note |", "| --- | --- | ---: | --- | --- |"]
        for f in report["findings"]:
            excerpt = f["excerpt"].replace("|", "\\|")
            lines.append(f"| {f['level']} | {f['kind']} | {f['line'] or ''} | {excerpt} | {f['note']} |")
    else:
        lines.append("No defects of the kinds this scan looks for. That is not a certificate of integrity.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan a manuscript for integrity defects that code can find.")
    parser.add_argument("source", help="a .txt, .md, .tex, .docx or .pdf file, or - for standard input")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")  # legacy consoles cannot print every character
    report = scan_path(args.source)
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else render(report))
    return 1 if report["counts"]["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
