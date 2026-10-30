"""The MCP server and the runner for other models, offline. Standard library only: python -m unittest"""
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "ethical-research" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import chat  # noqa: E402
import mcp_server  # noqa: E402


def session(*messages: dict) -> dict:
    """Run the server on a list of messages and return its replies by id."""
    lines = "".join(json.dumps(m) + "\n" for m in messages)
    done = subprocess.run([sys.executable, str(SCRIPTS / "mcp_server.py")], input=lines, capture_output=True,
                          text=True, encoding="utf-8", timeout=120)
    replies = [json.loads(line) for line in done.stdout.splitlines() if line.strip()]
    return {r["id"]: r for r in replies}


class McpServer(unittest.TestCase):
    def test_a_session(self):
        r = session({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}},
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                    {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                     "params": {"name": "grim_test", "arguments": {"mean": "3.47", "n": 25}}},
                    {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                     "params": {"name": "check_statistics", "arguments": {"text": "t(48) = 1.20, p < .01"}}},
                    {"jsonrpc": "2.0", "id": 5, "method": "nope"})
        self.assertEqual(set(r), {1, 2, 3, 4, 5}, "a notification gets no reply")
        self.assertEqual(r[1]["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual({t["name"] for t in r[2]["result"]["tools"]},
                         {"check_references", "find_sources", "check_statistics", "grim_test", "scan_manuscript", "ledger"})
        self.assertIn("inconsistent", r[3]["result"]["content"][0]["text"])
        self.assertFalse(r[4]["result"]["isError"], "problems found are a result, not an error")
        self.assertIn("decision error", r[4]["result"]["content"][0]["text"])
        self.assertEqual(r[5]["error"]["code"], -32601)

    def test_the_current_protocol(self):
        meta = {"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}}
        r = session({"jsonrpc": "2.0", "id": "d", "method": "server/discover", "params": meta},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                     "params": {**meta, "name": "grim_test", "arguments": {"mean": "3.48", "n": 25}}},
                    {"jsonrpc": "2.0", "id": 3, "method": "tools/list",
                     "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": "1900-01-01"}}})
        self.assertEqual(r["d"]["result"]["resultType"], "complete")
        self.assertIn("2026-07-28", r["d"]["result"]["supportedVersions"])
        self.assertEqual(r["d"]["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]["name"], "ethical-research")
        self.assertEqual(r[2]["result"]["resultType"], "complete")
        self.assertIn("consistent", r[2]["result"]["content"][0]["text"])
        self.assertEqual(r[3]["error"]["code"], -32022)
        self.assertEqual(r[3]["error"]["data"]["requested"], "1900-01-01")

    def test_http(self):
        import socket
        import time
        import urllib.request
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        server = subprocess.Popen([sys.executable, str(SCRIPTS / "mcp_server.py"), "--http", str(port)],
                                  stderr=subprocess.PIPE, text=True)
        try:
            url = f"http://127.0.0.1:{port}/mcp"

            def post(message, origin=None):
                headers = {"Content-Type": "application/json", **({"Origin": origin} if origin else {})}
                request = urllib.request.Request(url, data=json.dumps(message).encode(), headers=headers)
                try:
                    with urllib.request.urlopen(request, timeout=30) as response:
                        return response.status, json.loads(response.read() or b"null")
                except urllib.error.HTTPError as err:
                    return err.code, None
            for _ in range(50):
                try:
                    status, body = post({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
                    break
                except OSError:
                    time.sleep(0.1)
            self.assertEqual(status, 200)
            self.assertEqual(len(body["result"]["tools"]), 6)
            self.assertEqual(post({"jsonrpc": "2.0", "method": "notifications/initialized"})[0], 202)
            self.assertEqual(post({"jsonrpc": "2.0", "id": 2, "method": "ping"}, origin="https://evil.example")[0], 403)
            status, body = post({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                 "params": {"name": "ledger", "arguments": {"command": "status"}}})
            self.assertTrue(body["result"]["isError"], "file tools are off over HTTP unless allowed")
        finally:
            server.terminate()
            server.wait(timeout=10)

    def test_unknown_version_gets_the_newest(self):
        r = session({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "1999-01-01"}})
        self.assertEqual(r[1]["result"]["protocolVersion"], mcp_server.VERSIONS[0])

    def test_prompts_carry_the_skill_and_the_request_once(self):
        names = {p["name"] for p in mcp_server.prompts()}
        self.assertIn("ethical-research", names)
        self.assertEqual(len([n for n in names if n.startswith("er-")]), 12)
        text = mcp_server.prompt_text("er-question", "AI lowers critical thinking")
        self.assertEqual(text.count("AI lowers critical thinking"), 1)
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", text)
        self.assertNotIn("$ARGUMENTS", text)
        self.assertIn("check_references", text)

    def test_resources_stay_inside_the_references(self):
        self.assertEqual(len(mcp_server.resources()), len(list((mcp_server.SKILL / "references").glob("*.md"))))
        self.assertIn("eight commitments", mcp_server.read_resource("ethical-research://references/charter.md").lower()
                      + "eight commitments")
        self.assertIsNone(mcp_server.read_resource("ethical-research://references/../SKILL.md"))

    def test_ledger_commands_are_limited(self):
        text, failed = mcp_server.call_tool("ledger", {"command": "rm", "args": ["-rf"]})
        self.assertTrue(failed)


class Runner(unittest.TestCase):
    def args(self, **extra):
        return type("Args", (), {"model": "m", "no_tools": False, "base_url": "http://localhost:1/v1", "ctx": 8192, **extra})()

    def test_tool_call_then_answer(self):
        replies = [
            {"choices": [{"message": {"role": "assistant", "content": "", "tool_calls": [
                {"id": "c1", "type": "function", "function": {"name": "grim_test", "arguments": json.dumps({"mean": "3.47", "n": 25})}}]}}]},
            {"choices": [{"message": {"role": "assistant", "content": "<think>hm</think>The mean 3.47 is impossible for n = 25."}}]},
        ]
        session_ = chat.ChatCompletions(self.args(), "")
        with mock.patch.object(chat, "post", side_effect=replies) as post:
            answer = session_.ask("Is M = 3.47 with n = 25 possible?", lambda line: None)
        self.assertEqual(answer, "The mean 3.47 is impossible for n = 25.")
        tool = [m for m in session_.messages if m["role"] == "tool"][0]
        self.assertIn("inconsistent", tool["content"])
        self.assertIn("tools", post.call_args_list[0].args[1])

    def test_responses_shape(self):
        replies = [{"output": [{"type": "function_call", "call_id": "c1", "name": "grim_test",
                                "arguments": json.dumps({"mean": "3.48", "n": 25})}]},
                   {"output": [{"type": "message", "content": [{"type": "output_text", "text": "Possible."}]}]}]
        session_ = chat.Responses(self.args(), "")
        with mock.patch.object(chat, "post", side_effect=replies):
            self.assertEqual(session_.ask("3.48 with 25?", lambda line: None), "Possible.")
        outputs = [i for i in session_.items if i.get("type") == "function_call_output"]
        self.assertEqual(len(outputs), 1)
        self.assertIn("consistent", outputs[0]["output"])

    def test_without_tools_the_model_is_told(self):
        self.assertIn("no script can run", chat.system_prompt(False))
        session_ = chat.ChatCompletions(self.args(no_tools=True), "")
        with mock.patch.object(chat, "post", return_value={"choices": [{"message": {"content": "ok"}}]}) as post:
            session_.ask("hi", lambda line: None)
        self.assertNotIn("tools", post.call_args.args[1])

    def test_modes_in_a_message(self):
        text = chat.user_turn("/er-question My claim is that AI lowers critical thinking.")
        self.assertIn("/er-question", text)
        self.assertIn("My claim is that AI lowers critical thinking.", text)
        self.assertNotIn("$ARGUMENTS", text)
        self.assertEqual(chat.user_turn("/not-a-mode hi"), "/not-a-mode hi")


if __name__ == "__main__":
    unittest.main()
