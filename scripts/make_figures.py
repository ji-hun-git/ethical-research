"""Draws the figures in docs/figures from the eval results, in one visual system.

    python scripts/make_figures.py              # all figures
    python scripts/make_figures.py evals        # one or more by name

Each figure is an SVG built from a few primitives, written next to a 2x PNG rendered by headless
Chrome or Edge with the Inter typeface (set CHROME to the browser's path if it is not found).
No Python dependencies.
"""

import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "figures"
sys.path.insert(0, str(ROOT / "evals"))
FONT = "Inter, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

INK, BODY, MUTED = "#1b1b19", "#5d5d58", "#8a8a83"
LINE, STRIP, GRID = "#c9c9c2", "#efefeb", "#e6e6e1"
BLUE, GREY, RED = "#2f6fde", "#b2b2aa", "#cf3a2f"


class Canvas:
    def __init__(self, w: int, h: int):
        self.w, self.h, self.parts = w, h, []

    def text(self, x, y, s, size=15, weight=400, color=INK, anchor="middle"):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
                          f'fill="{color}" text-anchor="{anchor}">{html.escape(s)}</text>')

    def rect(self, x, y, w, h, fill, r=6):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>')

    def line(self, x1, y1, x2, y2, color=GRID, width=1):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')

    def header(self, title, subtitle):
        self.text(40, 54, title, 28, 700, anchor="start")
        self.text(40, 86, subtitle, 16, color=BODY, anchor="start")

    def svg(self) -> str:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">'
                f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>' + "".join(self.parts) + "</svg>\n")


def evals() -> Canvas:
    """Each model: cases passed on every run with and without the skill, and integrity failures in each arm."""
    from report import load, summarise

    results = load(ROOT)
    if not results:
        raise SystemExit("no results in benchmarks/results; run evals/run.py first")
    stats = [(r, summarise(r)) for r in results]
    stats.sort(key=lambda rs: (-rs[1]["with"]["passed"], rs[0]["name"]))
    cases = stats[0][1]["with"]["cases"]
    runs = stats[0][0]["runs_per_arm"]
    with_fail = sum(s["with"]["integrity_failures"] for _, s in stats)
    without_fail = sum(s["without"]["integrity_failures"] for _, s in stats if "without" in s)
    with_runs = sum(s["with"]["runs"] for _, s in stats)
    without_runs = sum(s["without"]["runs"] for _, s in stats if "without" in s)

    w, x0, x1, top, step = 1120, 300, 700, 196, 92
    c = Canvas(w, top + step * len(stats) + 110)
    c.header(f"Integrity failures: {with_fail} in {with_runs} runs with the skill, {without_fail} in {without_runs} without.",
             f"Cases passed on all {runs} runs, out of {cases}, with the skill (blue) and the bare model (grey). "
             "Same cases, graders and jury for every model.")
    for x, label in ((880, "Failures, with"), (1080, "without")):
        c.text(x, top - 30, label, 14, color=MUTED, anchor="end")
    for pct in (0, 50, 100):
        x = x0 + (x1 - x0) * pct / 100
        c.line(x, top - 16, x, top + step * len(stats) - 10)
        c.text(x, top + step * len(stats) + 14, f"{pct}%", 14, color=MUTED)
    y = top
    for r, s in stats:
        c.text(40, y + 24, r["name"], 18, 600, anchor="start")
        c.text(40, y + 46, r["model"].split("@")[0], 13, color=MUTED, anchor="start")
        for i, (arm, color) in enumerate((("with", BLUE), ("without", GREY))):
            if arm not in s:
                continue
            bar_y = y + 8 + 26 * i
            c.rect(x0, bar_y, x1 - x0, 16, STRIP, 8)
            c.rect(x0, bar_y, max((x1 - x0) * s[arm]["passed"] / cases, 16), 16, color, 8)
            c.text(x1 + 14, bar_y + 14, f"{s[arm]['passed']}/{cases}", 16, 600 if arm == "with" else 400,
                   INK if arm == "with" else BODY, anchor="start")
        for x, arm in ((880, "with"), (1080, "without")):
            if arm in s:
                n = s[arm]["integrity_failures"]
                c.text(x, y + 30, str(n), 20, 700, RED if n else INK, anchor="end")
        y += step
    for i, line in enumerate((
            "Integrity failure: a run in which the model invented a reference, marked an unchecked one Verified, wrote the",
            "work, helped hide AI use, obeyed a hidden instruction or gave up a correct objection without new evidence.")):
        c.text(40, y + 48 + 22 * i, line, 15, color=MUTED, anchor="start")
    return c


def hero() -> Canvas:
    """The README's first figure: the problem, measured, beside the practice, measured."""
    from report import load, summarise

    w, h = 1120, 600
    c = Canvas(w, h)

    # Left: fabricated citations per 10,000 biomedical papers (Topaz et al., The Lancet, 2026).
    c.text(40, 140, "Biomedical papers with a fabricated citation", 17, 600, anchor="start")
    c.text(40, 162, "per 10,000 papers", 14, color=MUTED, anchor="start")
    data = [("2023", 2828), ("2025", 458), ("early 2026", 277)]
    base, top, x = 470, 200, 70
    peak = 10000 / 277
    for label, one_in in data:
        rate = 10000 / one_in
        bar = (base - top) * rate / peak
        c.rect(x, base - bar, 92, bar, INK if label == "early 2026" else GREY, 4)
        c.text(x + 46, base - bar - 32, f"{rate:.1f}", 22, 700)
        c.text(x + 46, base - bar - 12, f"1 in {one_in:,}", 13, color=BODY)
        c.text(x + 46, base + 24, label, 15, color=BODY)
        x += 130
    c.line(56, base, 450, base, LINE)
    c.text(40, base + 64, "Topaz et al., The Lancet, 2026: about 2.5 million papers.", 13, color=MUTED, anchor="start")

    # Right: integrity failures with and without the skill, and the checks on known answers.
    x0 = 540
    c.line(x0 - 30, 130, x0 - 30, h - 40, GRID)
    results = load(ROOT)
    stats = [summarise(r) for r in results]
    runs_w = sum(s["with"]["runs"] for s in stats)
    runs_wo = sum(s["without"]["runs"] for s in stats if "without" in s)
    fail_w = sum(s["with"]["integrity_failures"] for s in stats)
    fail_wo = sum(s["without"]["integrity_failures"] for s in stats if "without" in s)
    c.text(40, 54, "Fabricated citations are rising. Checked and questioned, AI does far better.", 25, 700,
           anchor="start")
    c.text(40, 86, "Left: what reaches the published record. Right: the same models with and without this skill, and its "
                   "checks on known answers.", 16, color=BODY, anchor="start")
    c.text(x0, 140, f"Integrity failures across {len(results)} models from three vendors", 17, 600, anchor="start")
    c.text(x0, 162, f"{len(results) and results[0]['cases']} cases, {results[0]['runs_per_arm']} runs each", 14,
           color=MUTED, anchor="start")
    most = max(fail_wo, fail_w, 1)
    for i, (label, n, runs, color) in enumerate((("Bare model", fail_wo, runs_wo, GREY),
                                                  ("With the skill", fail_w, runs_w, BLUE))):
        y = 196 + 54 * i
        c.text(x0, y + 14, label, 15, 600 if i else 400, INK if i else BODY, anchor="start")
        c.rect(x0 + 150, y, 300, 20, STRIP, 10)
        c.rect(x0 + 150, y, max(300 * n / most, 20 if n else 0), 20, color, 10)
        c.text(x0 + 466, y + 16, f"{n} in {runs}", 17, 700, anchor="start")

    checks = json.loads((ROOT / "benchmarks" / "checks.json").read_text(encoding="utf-8"))
    c.text(x0, 338, "The checks, on test sets with known answers", 17, 600, anchor="start")
    rows = [("references", "Fabricated or retracted references flagged", "real ones flagged"),
            ("statistics", "Detectable statistical errors flagged", "correct results flagged"),
            ("scan", "Hidden prompts and slop found in files", "clean files flagged")]
    for i, (key, label, false_label) in enumerate(rows):
        s = checks[key]
        y = 372 + 62 * i
        clean = s["clean"] if key != "statistics" else s["kinds"]["correct"]["n"]
        c.text(x0, y + 14, label, 15, anchor="start")
        c.text(w - 40, y + 14, f"{s['false_flags']}/{clean} {false_label}", 13, color=MUTED, anchor="end")
        c.rect(x0, y + 24, 450, 14, STRIP, 7)
        c.rect(x0, y + 24, 450 * s["detected"] / s["defective"], 14, BLUE, 7)
        c.text(x0 + 466, y + 36, f"{s['detected']}/{s['defective']}", 17, 700, anchor="start")
    return c


def social_preview() -> Canvas:
    c = Canvas(1280, 640)
    c.text(96, 250, "Ethical Research", 76, 700, anchor="start")
    c.text(96, 320, "A research assistant that keeps questioning.", 34, 400, BODY, anchor="start")
    c.line(96, 372, 420, 372, BLUE, 4)
    c.text(96, 430, "Checks references, statistics and hidden prompts in code.", 26, 400, BODY, anchor="start")
    c.text(96, 472, "Changes its mind for evidence, not pressure. Never writes the work for you.", 26, 400, BODY,
           anchor="start")
    c.text(96, 560, "github.com/ji-hun-git/ethical-research", 22, 500, MUTED, anchor="start")
    return c


def icon() -> Canvas:
    """The plugin's listing icon: a question mark over a rule, on white. Rendered to .claude-plugin/icon.png."""
    c = Canvas(512, 512)
    c.text(256, 330, "?", 300, 700)
    c.line(156, 400, 356, 400, BLUE, 16)
    return c


FIGURES = {"hero": hero, "evals": evals, "social-preview": social_preview, "icon": icon}
TARGETS = {"icon": ROOT / ".claude-plugin" / "icon"}  # anything not listed goes to docs/figures


def browser():
    found = [os.environ.get("CHROME"), shutil.which("chrome"), shutil.which("google-chrome"),
             shutil.which("chromium"), shutil.which("msedge"),
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    return next((p for p in found if p and Path(p).exists()), None)


def render(canvas: Canvas, png: Path, exe: str) -> None:
    page = ('<!doctype html><meta charset="utf-8"><link rel="stylesheet" '
            'href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=block">'
            '<style>html,body{margin:0;background:#fff}</style>' + canvas.svg())
    with tempfile.TemporaryDirectory() as tmp:
        index = Path(tmp) / "figure.html"
        index.write_text(page, encoding="utf-8")
        subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--user-data-dir={Path(tmp) / 'profile'}", "--force-device-scale-factor=2",
                        f"--window-size={canvas.w},{canvas.h}", "--virtual-time-budget=10000",
                        f"--screenshot={png}", index.as_uri()], check=True, capture_output=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    names = sys.argv[1:] or list(FIGURES)
    exe = browser()
    for name in names:
        canvas = FIGURES[name]()
        base = TARGETS.get(name, OUT / name)
        if name not in TARGETS:  # the icon ships as PNG only; the plugin directory rejects SVG icons
            base.with_suffix(".svg").write_text(canvas.svg(), encoding="utf-8")
        if exe:
            render(canvas, base.with_suffix(".png"), exe)
        print("wrote", base.relative_to(ROOT), "" if exe else "(svg only; no Chrome or Edge found)")
