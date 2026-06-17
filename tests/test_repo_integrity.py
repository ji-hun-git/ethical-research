"""Structural regression tests for Ethical Research.

These run with no external dependencies (just pytest) and catch the drift that
breaks a Claude Code plugin: renamed reference files, commands missing from the
router, stale brand tokens, malformed manifests, a charter that lost a commitment.

    pip install -r requirements-dev.txt
    pytest
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Content files only — deliberately excludes tests/ and evals/ so the test's own
# literals (e.g. the brand tokens it searches for) don't match themselves.
CONTENT = (
    list(ROOT.glob("*.md"))
    + list(ROOT.glob(".claude-plugin/*.json"))
    + list(ROOT.glob("skills/**/*.md"))
    + list(ROOT.glob("commands/*.md"))
    + list(ROOT.glob("reference/*.md"))
)
COMMANDS = sorted(ROOT.glob("commands/*.md"))


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_manifests_valid_and_consistent():
    plugin = json.loads(_read(ROOT / ".claude-plugin" / "plugin.json"))
    market = json.loads(_read(ROOT / ".claude-plugin" / "marketplace.json"))
    assert plugin["name"] == "ethical-research"
    entry = market["plugins"][0]
    assert entry["name"] == "ethical-research"
    assert entry["version"] == plugin["version"]


def test_no_stale_brand_tokens():
    # The project was renamed from a working name; none of it may survive.
    for f in CONTENT:
        text = _read(f)
        for token in ("Jeongdo", "jeongdo", "jd-"):
            assert token not in text, f"stale token {token!r} in {f.relative_to(ROOT)}"


def test_every_command_binds_the_charter():
    assert COMMANDS, "no command files found"
    for f in COMMANDS:
        assert "ETHICS.md" in _read(f), f"{f.name} does not bind the charter (ETHICS.md)"


def test_reference_links_resolve():
    pattern = re.compile(r"reference/([a-z0-9\-]+)\.md")
    for f in CONTENT:
        for name in pattern.findall(_read(f)):
            target = ROOT / "reference" / f"{name}.md"
            assert target.exists(), f"{f.relative_to(ROOT)} links missing reference/{name}.md"


def test_router_lists_every_command():
    skill = _read(ROOT / "skills" / "ethical-research" / "SKILL.md")
    for f in COMMANDS:
        assert f"commands/{f.name}" in skill, f"{f.name} is not listed in SKILL.md router"


def test_charter_has_six_commitments():
    ethics = _read(ROOT / "ETHICS.md")
    assert "## The six commitments" in ethics
    for i in range(1, 7):
        assert f"### {i}." in ethics, f"commitment #{i} heading missing from ETHICS.md"


def test_eval_cases_well_formed():
    cases = json.loads(_read(ROOT / "evals" / "cases.json"))
    assert isinstance(cases, list) and cases
    ids = set()
    for c in cases:
        for key in ("id", "mode", "language", "kind", "prompt", "expect"):
            assert key in c, f"case missing {key}: {c.get('id', c)}"
        assert isinstance(c["expect"]["must"], list) and c["expect"]["must"]
        assert isinstance(c["expect"]["must_not"], list) and c["expect"]["must_not"]
        ids.add(c["id"])
    # the three behaviors from the smoke test must stay covered
    assert {"plan-safe", "citation-verify-trap", "question-critical-ko"} <= ids
