"""Packs the portable skill as a zip for hosts that take skills as uploads, such as the Claude apps.

    python scripts/build_skill_zip.py              # writes dist/ethical-research.zip

The zip holds one folder, ethical-research/, with SKILL.md, its references and its scripts as they are in
skills/ethical-research, and the twelve modes as modes/<mode>.md. The modes are Claude Code commands in the
plugin; here their paths are rewritten to point inside the folder, and SKILL.md points to them. Entries
carry a fixed date, so the same files give the same zip.
"""

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "ethical-research"
OUT = ROOT / "dist" / "ethical-research.zip"
STAMP = (2026, 1, 1, 0, 0, 0)
MODES_IN_PLUGIN = "`../<mode>/SKILL.md` beside this folder"
MODES_IN_ZIP = "`modes/<mode>.md` in this folder"


def mode_text(path: Path) -> str:
    """A mode's instructions with its frontmatter dropped and its paths made relative to the skill folder."""
    body = re.sub(r"\A---\n.*?\n---\n", "", path.read_text(encoding="utf-8").replace("\r\n", "\n"), flags=re.S)
    body = body.replace("`${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/SKILL.md`", "`SKILL.md`")
    body = body.replace("${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/", "")
    body = body.replace("The researcher's request: $ARGUMENTS", "The researcher's request is in their message.")
    return body.replace("../ethical-research/", "../")


def entries() -> list[tuple[str, bytes]]:
    out = []
    for path in sorted(p for p in SKILL.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        data = path.read_bytes().replace(b"\r\n", b"\n")
        if path == SKILL / "SKILL.md":
            text = data.decode("utf-8")
            if MODES_IN_PLUGIN not in text:
                raise SystemExit(f"SKILL.md no longer says {MODES_IN_PLUGIN!r}; update build_skill_zip.py")
            data = text.replace(MODES_IN_PLUGIN, MODES_IN_ZIP).encode("utf-8")
        out.append((f"ethical-research/{path.relative_to(SKILL).as_posix()}", data))
    for mode in sorted((ROOT / "skills").glob("er-*/SKILL.md")):
        out.append((f"ethical-research/modes/{mode.parent.name}.md", mode_text(mode).encode("utf-8")))
    return out


def main() -> int:
    files = entries()
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files:
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
