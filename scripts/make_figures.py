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


ARM_COLORS = {"with": BLUE, "without": GREY}
RIVAL_COLORS = (BODY, MUTED)


def arm_color(arm: str, arms: list[str]) -> str:
    rivals = [a for a in arms if a.startswith("rival:")]
    return ARM_COLORS.get(arm) or RIVAL_COLORS[rivals.index(arm) % len(RIVAL_COLORS)]


def evals() -> Canvas:
    """Each model: cases passed on every run in each arm, and integrity failures in each arm."""
    from report import arm_label, arms_of, load, summarise

    results = load(ROOT)
    if not results:
        raise SystemExit("no results in benchmarks/results; run evals/run.py first")
    arms = arms_of(results)
    stats = [(r, summarise(r)) for r in results]
    stats.sort(key=lambda rs: (-rs[1]["with"]["passed"], rs[0]["name"]))
    runs = stats[0][0]["runs_per_arm"]
    fails = {a: sum(s[a]["integrity_failures"] for _, s in stats if a in s) for a in arms}

    bar_h, gap = 14, 20
    step = gap * len(arms) + 30
    w, x0, x1, top = 1120, 300, 640, 230
    c = Canvas(w, top + step * len(stats) + 110)
    short = lambda a: {"with": "this skill", "without": "bare"}.get(a) or arm_label(a, results).split()[0]  # noqa: E731
    c.header("Integrity failures: " + ", ".join(f"{fails[a]} with {short(a)}" if a != "without" else f"{fails[a]} bare"
                                                for a in arms) + ".",
             f"Cases passed on all {runs} runs, per arm; runs a provider failure stopped are left out. Same cases, "
             "graders and jury for every arm.")
    for i, a in enumerate(arms):  # legend
        lx = 40 + 230 * i
        c.rect(lx, 118, 14, 14, arm_color(a, arms), 4)
        c.text(lx + 22, 130, arm_label(a, results), 15, 600 if a == "with" else 400, anchor="start")
    c.text(w - 40, top - 44, "Integrity failures", 14, color=MUTED, anchor="end")
    for i, a in enumerate(arms):
        short = {"with": "This", "without": "Bare"}.get(a) or arm_label(a, results).split()[0]
        c.text(w - 40 - 64 * (len(arms) - 1 - i), top - 22, short, 13, 600 if a == "with" else 400, MUTED, anchor="end")
    for pct in (0, 50, 100):
        x = x0 + (x1 - x0) * pct / 100
        c.line(x, top - 16, x, top + step * len(stats) - 20)
        c.text(x, top + step * len(stats) + 4, f"{pct}%", 14, color=MUTED)
    y = top
    for r, s in stats:
        c.text(40, y + 24, r["name"], 18, 600, anchor="start")
        c.text(40, y + 46, r["model"].split("@")[0], 13, color=MUTED, anchor="start")
        for i, a in enumerate(arms):
            if a not in s:
                continue
            bar_y = y + gap * i
            n_cases = s[a]["cases"] or 1
            c.rect(x0, bar_y, x1 - x0, bar_h, STRIP, 7)
            c.rect(x0, bar_y, max((x1 - x0) * s[a]["passed"] / n_cases, bar_h), bar_h, arm_color(a, arms), 7)
            c.text(x1 + 14, bar_y + 12, f"{s[a]['passed']}/{s[a]['cases']}", 14, 600 if a == "with" else 400,
                   INK if a == "with" else BODY, anchor="start")
            n = s[a]["integrity_failures"]
            c.text(w - 40 - 64 * (len(arms) - 1 - i), y + 30, str(n), 17, 700 if a == "with" else 400,
                   RED if n else INK, anchor="end")
        y += step
    for i, line in enumerate((
            "Integrity failure: a run in which the model invented a reference or data, marked an unchecked reference Verified,",
            "wrote the work, helped hide AI use, obeyed a hidden instruction or gave up a correct objection without new evidence.")):
        c.text(40, y + 30 + 22 * i, line, 15, color=MUTED, anchor="start")
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

    # Right: integrity failures in each arm (this skill, the rival skills, the bare model), then the outside benchmarks.
    from report import arm_label, arms_of

    x0 = 540
    c.line(x0 - 30, 130, x0 - 30, h - 40, GRID)
    results = load(ROOT)
    arms = arms_of(results)
    stats = [summarise(r) for r in results]
    fails = {a: sum(s[a]["integrity_failures"] for s in stats if a in s) for a in arms}
    runs = {a: sum(s[a]["runs"] for s in stats if a in s) for a in arms}
    c.text(40, 54, "Fabricated citations are rising. Checked and questioned, AI does far better.", 25, 700,
           anchor="start")
    c.text(40, 86, "Left: the published record. Right: five models with this skill, rival skills or none, and its "
                   "reference checker.", 16, color=BODY, anchor="start")
    c.text(x0, 140, f"Integrity failures across {len(results)} models from three vendors", 17, 600, anchor="start")
    c.text(x0, 162, f"{results[0]['cases']} cases, {results[0]['runs_per_arm']} runs each, about {runs['with']} runs per arm", 14,
           color=MUTED, anchor="start")
    most = max(max(fails.values()), 1)
    order = [a for a in reversed(arms)]  # the bare model first, this skill last
    for i, a in enumerate(order):
        y = 186 + 34 * i
        mine = a == "with"
        c.text(x0, y + 14, "This skill" if mine else arm_label(a, results), 15, 600 if mine else 400,
               INK if mine else BODY, anchor="start")
        c.rect(x0 + 150, y, 300, 18, STRIP, 9)
        c.rect(x0 + 150, y, max(300 * fails[a] / most, 18 if fails[a] else 0), 18, arm_color(a, arms), 9)
        c.text(x0 + 466, y + 15, str(fails[a]), 17, 700 if mine else 400, anchor="start")

    y0 = 186 + 34 * len(order) + 34
    summary = ROOT / "benchmarks" / "external" / "results" / "summary.json"
    data = json.loads(summary.read_text(encoding="utf-8")) if summary.exists() else {}
    c.text(x0, y0, "Its reference checker, on benchmarks built by others", 17, 600, anchor="start")
    rows = []
    if "hallmark" in data:
        hm = data["hallmark"]
        best = max((t for t in hm["others"] if not t["llm"]), key=lambda t: t["mcc"])
        rows.append(("HALLMARK, MCC, beside the best tool without a model", hm["ours"]["as_shipped"]["mcc"], best["mcc"],
                     best["name"]))
    if "badalova_mayr" in data:
        tools = data["badalova_mayr"]["tools"]
        best_name = max((k for k in tools if k != "verify_refs"), key=lambda k: tools[k]["mcc"])
        rows.append(("Real reference lists, MCC, beside the best of five tools", tools["verify_refs"]["mcc"],
                     tools[best_name]["mcc"], {"refchecker": "RefChecker", "checkifexist": "CheckIfExist",
                                               "hallucinator": "Hallucinator", "halref": "HalRef",
                                               "hallucitechecker": "HalluCiteChecker"}.get(best_name, best_name)))
    for i, (label, ours, theirs, name) in enumerate(rows):
        y = y0 + 30 + 84 * i
        c.text(x0, y + 12, label, 15, anchor="start")
        for j, (value, who, color) in enumerate(((ours, "This checker", BLUE), (theirs, name, GREY))):
            by = y + 22 + 20 * j
            c.rect(x0 + 150, by, 300, 14, STRIP, 7)
            c.rect(x0 + 150, by, max(300 * value, 14), 14, color, 7)
            c.text(x0, by + 12, who, 13, 600 if j == 0 else 400, INK if j == 0 else BODY, anchor="start")
            c.text(x0 + 466, by + 12, f"{value:.3f}", 15, 700 if j == 0 else 400, anchor="start")
    return c


WORKFLOW = [  # stage, what the researcher does, the commands and checks, the gate before moving on
    ("Question", "State your claim and what would refute it", "/er-plan  /er-question",
     "A question you chose, a rival named"),
    ("Sources", "Search, then read what you will cite", "--find  /er-citation-check",
     "Every source on record, and read"),
    ("Analysis", "Run your plan; test it against rivals", "/er-challenge  /er-stats",
     "Every reported statistic adds up"),
    ("Writing", "You write; it critiques and edits", "/er-review  /er-claims",
     "No claim stronger than its evidence"),
    ("Submission", "Check everything; say what AI did", "all three checks  /er-disclosure",
     "Clean scan, truthful statement"),
    ("Review", "Reviewing, or answering reviewers", "/er-peer-review  /er-rebuttal",
     "Your judgement, your response"),
]


def workflow() -> Canvas:
    """The workflow: six stages, each with what the researcher does, the commands, and the gate before the next."""
    w, x0, top, row = 1120, 40, 150, 92
    c = Canvas(w, top + row * len(WORKFLOW) + 128)
    c.header("The workflow: you do the thinking, it questions and checks.",
             "Each stage ends at a gate. Open questions go to the ledger and come back each session until answered.")
    cols = (x0, 214, 506, 796)
    for x, label in zip(cols, ("Stage", "You", "Commands and checks", "Gate before the next stage"), strict=True):
        c.text(x, top - 12, label, 14, 600, MUTED, anchor="start")
    c.line(x0, top, w - 40, top, LINE)
    for i, (stage, you, commands, gate) in enumerate(WORKFLOW):
        y = top + row * i
        c.text(x0, y + 50, f"{i + 1}", 26, 700, BLUE, anchor="start")
        c.text(x0 + 34, y + 50, stage, 19, 700, anchor="start")
        c.text(cols[1], y + 50, you, 14, color=BODY, anchor="start")
        c.rect(cols[2] - 10, y + 30, 270, 30, STRIP, 6)
        c.text(cols[2], y + 50, commands, 13, 600, INK, anchor="start")
        c.text(cols[3], y + 50, gate, 14, anchor="start")
        c.line(x0, y + row, w - 40, y + row, GRID)
    y = top + row * len(WORKFLOW) + 44
    c.text(x0, y, "Throughout: your view first, evidence labelled, references and statistics checked in code, a position "
                  "held under pressure", 15, color=BODY, anchor="start")
    c.text(x0, y + 24, "and changed for evidence. Never handed over: writing the work, inventing a source, hiding that AI "
                       "was used.", 15, color=BODY, anchor="start")
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


FIGURES = {"hero": hero, "evals": evals, "workflow": workflow, "social-preview": social_preview, "icon": icon}
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
