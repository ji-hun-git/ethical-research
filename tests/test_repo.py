"""The plugin's structure: what would break it in Claude Code, Codex or `claude plugin eval`.
Standard library only: python -m unittest"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "ethical-research"
MODES = sorted(p.parent for p in (ROOT / "skills").glob("er-*/SKILL.md"))
SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
PROMPT_KEYS = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "model",
               "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env"}
GRADER_TYPES = {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"}


def frontmatter(path: Path) -> tuple[dict, str]:
    """Top-level keys of a YAML frontmatter block (nested blocks are kept as raw text), and the body."""
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path.relative_to(ROOT)} has no frontmatter"
    head, body = text[4:].split("\n---", 1)
    meta, key = {}, None
    for line in head.splitlines():
        if line.startswith((" ", "\t")) and key:
            meta[key] += "\n" + line
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        # an unquoted ": " inside a value is not valid YAML
        assert not (": " in value and value[:1] not in "\"'[{"), f"{path.relative_to(ROOT)}: quote the value of {key}"
        meta[key] = value.strip("\"'")
    return meta, body


def links(path: Path) -> list[str]:
    return [m for m in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", path.read_text(encoding="utf-8"))
            if not m.startswith(("http://", "https://", "mailto:"))]


class Manifests(unittest.TestCase):
    def test_versions_agree(self):
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        cff = re.search(r'^version: "([^"]+)"', (ROOT / "CITATION.cff").read_text(encoding="utf-8"), re.M).group(1)
        skill = re.search(r'version: "([^"]+)"', (SKILL / "SKILL.md").read_text(encoding="utf-8")).group(1)
        self.assertEqual(plugin["name"], "ethical-research")
        self.assertEqual(market["plugins"][0]["name"], plugin["name"])
        portable = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        gemini = json.loads((ROOT / "gemini-extension.json").read_text(encoding="utf-8"))
        self.assertEqual({plugin["version"], market["plugins"][0]["version"], cff, skill, portable["version"],
                          gemini["version"]}, {plugin["version"]})
        self.assertEqual({portable["name"], gemini["name"]}, {plugin["name"]})
        self.assertIsInstance(plugin["author"], dict)

    def test_other_manifests_start_the_mcp_server(self):
        portable = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))["mcpServers"]["ethical-research"]
        gemini = json.loads((ROOT / "gemini-extension.json").read_text(encoding="utf-8"))["mcpServers"]["ethical-research"]
        for server, variable in ((portable, "${PLUGIN_ROOT}"), (gemini, "${extensionPath}")):
            path = server["args"][0]
            self.assertTrue(path.startswith(variable + "/"), path)
            self.assertTrue((ROOT / path.removeprefix(variable + "/")).is_file(), path)

    def test_hook_runs_a_script_that_exists(self):
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        command = hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        for path in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"\s]+)", command):
            self.assertTrue((ROOT / path).is_file(), path)


class TheSkill(unittest.TestCase):
    def test_agent_skills_spec(self):
        meta, body = frontmatter(SKILL / "SKILL.md")
        self.assertEqual(meta["name"], SKILL.name)
        self.assertLessEqual(set(meta), SPEC_KEYS, "keys outside the Agent Skills spec break other hosts")
        self.assertLessEqual(len(meta["description"]), 1024)
        self.assertLess(len(body.splitlines()), 500)

    def test_every_reference_is_linked_and_every_link_resolves(self):
        linked = {Path(link).name for link in links(SKILL / "SKILL.md")}
        for ref in (SKILL / "references").glob("*.md"):
            self.assertIn(ref.name, linked, f"references/{ref.name} is not linked from SKILL.md")
        for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md"), *(m / "SKILL.md" for m in MODES),
                     *ROOT.glob("*.md")]:
            for link in links(path):
                self.assertTrue((path.parent / link).exists(), f"{path.relative_to(ROOT)} links missing {link}")

    def test_charter_copy_matches_ethics(self):
        ethics = (ROOT / "ETHICS.md").read_text(encoding="utf-8").replace("](skills/ethical-research/references/", "](")
        self.assertEqual((SKILL / "references" / "charter.md").read_text(encoding="utf-8"), ethics)

    def test_charter_has_eight_commitments(self):
        ethics = (ROOT / "ETHICS.md").read_text(encoding="utf-8")
        self.assertIn("## The eight commitments", ethics)
        self.assertEqual(re.findall(r"^### (\d)\.", ethics, re.M), [str(i) for i in range(1, 9)])

    def test_no_path_leaves_the_plugin(self):
        for path in ROOT.rglob("*.md"):
            if "evals" in path.parts or ".git" in path.parts:
                continue
            self.assertNotIn("${CLAUDE_PLUGIN_ROOT}/..", path.read_text(encoding="utf-8"), path)


class Modes(unittest.TestCase):
    def test_each_mode_loads_the_skill_and_its_paths_resolve(self):
        self.assertEqual(len(MODES), 12)
        for mode in MODES:
            meta, body = frontmatter(mode / "SKILL.md")
            self.assertEqual(meta["name"], mode.name)
            self.assertEqual(meta["disable-model-invocation"], "true")
            self.assertIn("${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/SKILL.md", body)
            self.assertIn("$ARGUMENTS", body)
            for path in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)", body):
                self.assertTrue((ROOT / path.rstrip("/.")).exists(), f"{mode.name}: {path}")

    def test_the_modes_table_matches_the_mode_folders(self):
        listed = set(re.findall(r"^\| `(er-[a-z-]+)` \|", (SKILL / "SKILL.md").read_text(encoding="utf-8"), re.M))
        self.assertEqual(listed, {m.name for m in MODES})

    def test_the_upload_zip_is_self_contained(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import build_skill_zip
        files = dict(build_skill_zip.entries())
        self.assertEqual(len([n for n in files if "/modes/" in n]), 12)
        for name, data in files.items():
            text = data.decode("utf-8", "replace")
            if name.endswith(".md"):  # the instructions: no plugin paths, and every relative link lands in the zip
                self.assertNotIn("CLAUDE_PLUGIN_ROOT", text, name)
                self.assertNotIn("$ARGUMENTS", text, name)
                base = name.rsplit("/", 1)[0]
                for link in re.findall(r"\]\(((?!https?:|#)[^)\s]+\.md)\)", text):
                    parts = []
                    for part in f"{base}/{link}".split("/"):
                        parts = parts[:-1] if part == ".." else parts + [part]
                    self.assertIn("/".join(parts), files, f"{name}: {link}")


class Evals(unittest.TestCase):
    def test_cases_load_in_claude_plugin_eval(self):
        cases = sorted((ROOT / "evals").glob("*/prompt.md"))
        self.assertGreaterEqual(len(cases), 15)
        for prompt in cases:
            meta, body = frontmatter(prompt)
            self.assertLessEqual(set(meta), PROMPT_KEYS, f"{prompt.parent.name}: unknown keys are errors")
            command = re.match(r"\s*/ethical-research:(er-[a-z-]+)", body)
            if command:
                self.assertTrue((ROOT / "skills" / command.group(1)).is_dir(), command.group(1))
            graders = sorted((prompt.parent / "graders").glob("*.md"))
            self.assertTrue(graders, f"{prompt.parent.name} has no grader")
            for grader in graders:
                gmeta, gbody = frontmatter(grader)
                self.assertIn(gmeta["type"], GRADER_TYPES)
                if gmeta["type"] == "regex":
                    re.compile(gmeta["pattern"])
                if gmeta["type"] == "llm":
                    self.assertIn("PASS", gbody + gbody.upper())

    def test_pressure_tests(self):
        for path in (ROOT / "evals" / "pressure").glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(data["turns"]), 2)
            self.assertTrue(all(g["type"] == "llm" and g["criteria"] for g in data["graders"]))


class Scripts(unittest.TestCase):
    def test_every_script_prints_its_usage(self):
        for script in sorted((SKILL / "scripts").glob("*.py")):
            done = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
            self.assertEqual(done.returncode, 0, f"{script.name}: {done.stderr[-300:]}")
            self.assertIn("usage", done.stdout.lower())


if __name__ == "__main__":
    unittest.main()
