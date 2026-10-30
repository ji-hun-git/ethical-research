#!/usr/bin/env python3
"""The skill's checks as an MCP server, for any host that speaks the Model Context Protocol. Standard library only.

    python mcp_server.py                    # MCP on standard input and output, for a host that starts it
    python mcp_server.py --http 8765        # MCP over HTTP at http://127.0.0.1:8765/mcp, for a host that connects

Tools: check_references, find_sources, check_statistics, grim_test, scan_manuscript and ledger, each running the
script of the same job in this folder. Prompts: the skill itself and each of its modes, so a host without skills
support can still load the instructions. Resources: the skill's reference files. The ledger is kept in the folder
the host starts the server in, as .ethical-research/ledger.json.

It speaks both eras of the protocol: the current one (2026-07-28: no handshake, the version in each request's
_meta, server/discover) and the earlier ones that open with initialize (2025-11-25 back to 2024-11-05).

Over HTTP the two tools that touch local files (scan_manuscript with a path, and ledger) are off unless
--allow-files is given, since anyone who can reach the address can call them. It listens on 127.0.0.1 unless
--host says otherwise; put it behind HTTPS before exposing it beyond this machine.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
MODERN = ("2026-07-28",)  # revisions with the version in each request's _meta and no handshake
VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")  # revisions that open with initialize, newest first
META_VERSION = "io.modelcontextprotocol/protocolVersion"
FILE_TOOLS_OFF = "This server was started without --allow-files, so it does not read or write local files."
_allow_files = True  # False when serving HTTP without --allow-files
TIMEOUT = 600
LEDGER_COMMANDS = ("init", "claim", "evidence", "mark", "ask", "answer", "withdraw", "accept", "status", "export",
                   "session-start")
HOST_NOTE = ("In this host the skill's scripts are MCP tools: use check_references, find_sources, check_statistics, "
             "grim_test, scan_manuscript and ledger wherever the instructions below say to run a script. The reference "
             "files they mention are MCP resources (ethical-research://references/<file>).")


def frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    head, _, body = text[3:].partition("\n---")
    meta = {}
    for line in head.splitlines():
        key, sep, value = line.strip().partition(":")
        if sep and value.strip():
            meta[key.strip()] = value.strip().strip('"')
    return meta, body.lstrip("\n")


def version() -> str:
    match = re.search(r'^\s+version:\s*"?([\d.]+)"?', (SKILL / "SKILL.md").read_text(encoding="utf-8"), re.M)
    return match.group(1) if match else "0"


# Tools.

def text_arg(name: str, description: str) -> dict:
    return {name: {"type": "string", "description": description}}


TOOLS = [
    {"name": "check_references",
     "description": "Check references against Crossref, DataCite, arXiv, OpenReview and OpenAlex: for each one, record "
                    "found, metadata mismatch, retracted, concern, not found, page found or unchecked. A found record "
                    "shows the work exists, not that it supports a claim.",
     "inputSchema": {"type": "object", "properties": text_arg(
         "references", "BibTeX entries, or one reference per line (a DOI, an arXiv identifier or a formatted citation)"),
         "required": ["references"]}},
    {"name": "find_sources",
     "description": "List works on a topic from Crossref's index, retractions marked, so candidate sources come from "
                    "an index, never from memory. None has been read.",
     "inputSchema": {"type": "object", "properties": {
         **text_arg("topic", "what to search for"),
         "rows": {"type": "integer", "description": "how many works (default 10)", "minimum": 1, "maximum": 25},
         "since": {"type": "integer", "description": "only works published from this year on"}},
         "required": ["topic"]}},
    {"name": "check_statistics",
     "description": "Recompute the p-values of APA-style t, F, chi-square, r and z results in a text and report each "
                    "as consistent, inconsistent, a decision error or one to check by hand.",
     "inputSchema": {"type": "object", "properties": text_arg("text", "the results text"), "required": ["text"]}},
    {"name": "grim_test",
     "description": "GRIM test: whether a mean reported to its decimals is possible for n integer responses.",
     "inputSchema": {"type": "object", "properties": {
         **text_arg("mean", "the mean as reported, keeping its decimals, e.g. \"3.47\""),
         "n": {"type": "integer", "minimum": 1},
         "items": {"type": "integer", "minimum": 1, "description": "number of items averaged (default 1)"}},
         "required": ["mean", "n"]}},
    {"name": "scan_manuscript",
     "description": "Scan a manuscript for instructions hidden from readers (white, tiny, invisible or off-page text, "
                    "metadata, LaTeX comments, Word hidden runs, Unicode tags), chatbot leftovers, tortured phrases, "
                    "placeholders and strong claims. It does not judge whether text was written by AI.",
     "inputSchema": {"type": "object", "properties": {
         **text_arg("path", "a local .txt, .md, .tex, .docx or .pdf file"),
         **text_arg("text", "or the text itself")}}},
    {"name": "ledger",
     "description": "The research ledger in the current project: claims, evidence and open questions that come back "
                    "until answered. Commands: " + ", ".join(LEDGER_COMMANDS) + ". Arguments are as for ledger.py, "
                    "e.g. [\"Social media use predicts anxiety\", \"--where\", \"abstract\"] for claim.",
     "inputSchema": {"type": "object", "properties": {
         "command": {"type": "string", "enum": list(LEDGER_COMMANDS)},
         "args": {"type": "array", "items": {"type": "string"}}},
         "required": ["command"]}},
]


def run_script(script: str, args: list[str], stdin: str = "") -> tuple[str, bool]:
    """The script's output, and whether it failed to run. Exit status 1 means "problems found", which is a result."""
    try:
        done = subprocess.run([sys.executable, str(HERE / script), *args], input=stdin, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    except subprocess.TimeoutExpired:
        return f"{script} did not finish within {TIMEOUT} seconds.", True
    output = (done.stdout + ("\n" + done.stderr if done.stderr.strip() else "")).strip()
    return output or f"{script} printed nothing (exit status {done.returncode}).", done.returncode not in (0, 1)


def call_tool(name: str, args: dict) -> tuple[str, bool]:
    if name == "check_references":
        return run_script("verify_refs.py", ["-"], str(args.get("references", "")))
    if name == "find_sources":
        extra = ["--rows", str(int(args.get("rows", 10)))] + (["--since", str(int(args["since"]))] if args.get("since") else [])
        return run_script("verify_refs.py", ["--find", str(args.get("topic", "")), *extra])
    if name == "check_statistics":
        return run_script("stats_check.py", ["-"], str(args.get("text", "")))
    if name == "grim_test":
        values = [str(args.get("mean", "")), str(int(args.get("n", 0)))] + ([str(int(args["items"]))] if args.get("items") else [])
        return run_script("stats_check.py", ["--grim", *values])
    if name == "scan_manuscript":
        if args.get("path"):
            if not _allow_files:
                return FILE_TOOLS_OFF + " Pass the text instead.", True
            return run_script("integrity_scan.py", [str(Path(args["path"]).expanduser())])
        return run_script("integrity_scan.py", ["-"], str(args.get("text", "")))
    if name == "ledger":
        if not _allow_files:
            return FILE_TOOLS_OFF, True
        command = str(args.get("command", ""))
        if command not in LEDGER_COMMANDS:
            return f"Unknown ledger command {command!r}; the commands are {', '.join(LEDGER_COMMANDS)}.", True
        return run_script("ledger.py", [command, *[str(a) for a in args.get("args") or []]])
    return f"Unknown tool {name!r}.", True


# Prompts and resources.

def mode_files() -> dict[str, Path]:
    """The modes: modes/<mode>.md in the zip for the Claude apps, ../<mode>/SKILL.md beside this folder in the plugin."""
    found = {p.stem: p for p in sorted((SKILL / "modes").glob("er-*.md"))}
    found.update({p.parent.name: p for p in sorted(SKILL.parent.glob("er-*/SKILL.md"))})
    return found


def prompts() -> list[dict]:
    meta, _ = frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
    out = [{"name": "ethical-research", "description": meta.get("description", "")[:300],
            "arguments": [{"name": "request", "description": "what the researcher asks", "required": False}]}]
    for name, path in mode_files().items():
        meta, _ = frontmatter(path.read_text(encoding="utf-8"))
        out.append({"name": name, "description": meta.get("description", name)[:300],
                    "arguments": [{"name": "request", "description": "what the researcher asks", "required": False}]})
    return out


def prompt_text(name: str, request: str) -> str | None:
    _, skill = frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
    parts = [HOST_NOTE, skill]
    if name != "ethical-research":
        path = mode_files().get(name)
        if path is None:
            return None
        _, body = frontmatter(path.read_text(encoding="utf-8"))
        body = re.sub(r"`?\$\{CLAUDE_PLUGIN_ROOT\}/skills/ethical-research/SKILL\.md`?", "the skill above", body)
        body = body.replace("${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/", "")
        parts.append(f"The researcher chose the mode /{name}. Its instructions:\n\n" + body)
    text = "\n\n---\n\n".join(parts)
    if "$ARGUMENTS" in text:  # a mode says where the request goes
        return text.replace("$ARGUMENTS", request or "(in the researcher's next message)")
    return text + (f"\n\n---\n\nThe researcher's request: {request}" if request else "")


def resources() -> list[dict]:
    return [{"uri": f"ethical-research://references/{p.name}", "name": p.stem, "mimeType": "text/markdown",
             "description": f"Ethical Research reference: {p.stem}"} for p in sorted((SKILL / "references").glob("*.md"))]


def read_resource(uri: str) -> str | None:
    name = uri.removeprefix("ethical-research://references/")
    path = (SKILL / "references" / name).resolve()
    if path.parent != (SKILL / "references").resolve() or not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


# The protocol: JSON-RPC 2.0, one message per line.

class RpcError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


CAPABILITIES = {"tools": {}, "prompts": {}, "resources": {}}
INSTRUCTIONS = ("Checks for research integrity done in code, and the Ethical Research skill as prompts. Load the prompt "
                "ethical-research to work as the skill describes.")


def server_info() -> dict:
    return {"name": "ethical-research", "title": "Ethical Research", "version": version()}


def handle(method: str, params: dict) -> dict:
    if method == "initialize":  # the earlier protocol's handshake
        asked = str(params.get("protocolVersion", ""))
        return {"protocolVersion": asked if asked in VERSIONS else VERSIONS[0], "capabilities": CAPABILITIES,
                "serverInfo": server_info(), "instructions": INSTRUCTIONS}
    if method == "server/discover":  # the current protocol's: what this server speaks, and who it is
        return {"supportedVersions": [*MODERN, *VERSIONS], "capabilities": CAPABILITIES,
                "_meta": {"io.modelcontextprotocol/serverInfo": server_info()}, "instructions": INSTRUCTIONS}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name = str(params.get("name", ""))
        if name not in {t["name"] for t in TOOLS}:
            raise RpcError(-32602, f"Unknown tool: {name}")
        text, failed = call_tool(name, params.get("arguments") or {})
        return {"content": [{"type": "text", "text": text}], "isError": failed}
    if method == "prompts/list":
        return {"prompts": prompts()}
    if method == "prompts/get":
        name = str(params.get("name", ""))
        text = prompt_text(name, str((params.get("arguments") or {}).get("request", "")))
        if text is None:
            raise RpcError(-32602, f"Unknown prompt: {name}")
        return {"description": f"Ethical Research: {name}", "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}
    if method == "resources/list":
        return {"resources": resources()}
    if method == "resources/read":
        uri = str(params.get("uri", ""))
        text = read_resource(uri)
        if text is None:
            raise RpcError(-32002, f"Resource not found: {uri}")
        return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]}
    raise RpcError(-32601, f"Method not found: {method}")


def respond(message: dict) -> dict | None:
    """The reply to one message, or None for a notification."""
    if "id" not in message:  # notifications (initialized, cancelled) need no reply
        return None
    params = message.get("params") or {}
    asked = (params.get("_meta") or {}).get(META_VERSION) if isinstance(params, dict) else None
    try:
        if not isinstance(message.get("method"), str):
            raise RpcError(-32600, "Invalid request")
        if asked is not None and asked not in MODERN:  # a request in the current era, for a version not spoken here
            return {"jsonrpc": "2.0", "id": message["id"], "error": {
                "code": -32022, "message": "Unsupported protocol version",
                "data": {"supported": [*MODERN, *VERSIONS], "requested": asked}}}
        result = handle(message["method"], params)
        if asked is not None or message["method"] == "server/discover":
            result = {"resultType": "complete", **result}  # the current era marks every result
        return {"jsonrpc": "2.0", "id": message["id"], "result": result}
    except RpcError as err:
        return {"jsonrpc": "2.0", "id": message["id"], "error": {"code": err.code, "message": str(err)}}
    except Exception as err:  # a fault here must not end the session
        return {"jsonrpc": "2.0", "id": message["id"], "error": {"code": -32603, "message": f"{type(err).__name__}: {err}"}}


def reply_to(body: str) -> dict | None:
    try:
        message = json.loads(body)
    except json.JSONDecodeError:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
    if not isinstance(message, dict):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}}
    return respond(message)


def serve_http(host: str, port: int) -> int:
    """Streamable HTTP without streams: each POST to /mcp gets its JSON-RPC reply as application/json."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    local = ("http://localhost", "https://localhost", "http://127.0.0.1", "https://127.0.0.1")

    class Handler(BaseHTTPRequestHandler):
        def send(self, status: int, body: bytes = b"", kind: str = "application/json") -> None:
            self.send_response(status)
            if body:
                self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):  # noqa: N802 (the name http.server calls)
            origin = self.headers.get("Origin")
            if origin and not origin.startswith(local):  # a web page elsewhere must not drive local tools
                return self.send(403, b'{"error": "origin not allowed"}')
            if self.path.split("?")[0] != "/mcp":
                return self.send(404)
            body = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode("utf-8", "replace")
            reply = reply_to(body)
            if reply is None:
                return self.send(202)
            return self.send(200, json.dumps(reply, ensure_ascii=False).encode("utf-8"))

        def do_GET(self):  # noqa: N802
            self.send(405)

        def log_message(self, *args):  # to stderr, as the protocol wants, and quietly
            pass

    print(f"Ethical Research MCP server on http://{host}:{port}/mcp", file=sys.stderr, flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
    return 0


def main() -> int:
    global _allow_files
    stdin = open(sys.stdin.fileno(), encoding="utf-8", errors="replace", newline="\n", closefd=False)
    stdout = open(sys.stdout.fileno(), "w", encoding="utf-8", newline="\n", closefd=False)
    argv = sys.argv[1:]
    if "--help" in argv or "-h" in argv:
        stdout.write("usage: mcp_server.py [--http PORT [--host HOST] [--allow-files]]\n\n" + __doc__ + "\n")
        return 0
    if "--http" in argv:
        _allow_files = "--allow-files" in argv
        host = argv[argv.index("--host") + 1] if "--host" in argv else "127.0.0.1"
        return serve_http(host, int(argv[argv.index("--http") + 1]))
    for line in stdin:  # ends when the host closes the stream
        if not line.strip():
            continue
        reply = reply_to(line)
        if reply is not None:
            stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
