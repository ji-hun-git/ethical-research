#!/usr/bin/env python3
"""Run Ethical Research on any model behind an OpenAI-style API: an open model on Ollama, LM Studio, vLLM or a
llama.cpp server, or a hosted one (OpenAI, xAI's Grok, Meta's Muse and others). Standard library only.

    python chat.py --base-url http://localhost:11434 --model qwen3:8b --api ollama
    python chat.py --base-url http://localhost:1234/v1 --model <model>          # LM Studio, vLLM, llama.cpp
    python chat.py --base-url https://api.x.ai/v1 --model <grok model> --key-env XAI_API_KEY
    python chat.py --base-url https://api.meta.ai/v1 --model <muse model> --api responses --key-env META_API_KEY
    python chat.py ... --once "Is this results paragraph ready? t(48) = 1.20, p < .01"

The skill's instructions are the system prompt and its checks are tools the model can call, the same tools as
mcp_server.py. Start a message with a mode (/er-plan, /er-question, ...) to use it; /modes lists them; /quit leaves.
A model without tool calling still works with --no-tools: it is told which checks it cannot run.
The key is read from the environment variable named by --key-env and is sent only to --base-url.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

import mcp_server as skill

MAX_STEPS = 12
NO_TOOLS = ("In this host no script can run. Where the instructions say to run a check, say in one line which check "
            "you could not run, then do the task without it.")


def system_prompt(tools: bool) -> str:
    _, body = skill.frontmatter((skill.SKILL / "SKILL.md").read_text(encoding="utf-8"))
    note = ("The skill's scripts are tools here: check_references, find_sources, check_statistics, grim_test, "
            "scan_manuscript and ledger. Use them wherever the instructions say to run a script." if tools else NO_TOOLS)
    return note + "\n\n---\n\n" + body


def user_turn(text: str) -> str:
    """A message that starts with a mode carries that mode's instructions with it."""
    match = re.match(r"\s*/(er-[a-z-]+)\b\s*(.*)", text, re.S)
    if not match or match.group(1) not in skill.mode_files():
        return text
    _, body = skill.frontmatter(skill.mode_files()[match.group(1)].read_text(encoding="utf-8"))
    body = re.sub(r"`?\$\{CLAUDE_PLUGIN_ROOT\}/skills/ethical-research/SKILL\.md`?", "the skill in your instructions", body)
    body = body.replace("${CLAUDE_PLUGIN_ROOT}/skills/ethical-research/", "")
    return f"I chose the mode /{match.group(1)}. Its instructions:\n\n" + body.replace("$ARGUMENTS", match.group(2).strip())


def post(url: str, payload: dict, key: str) -> dict:
    headers = {"Content-Type": "application/json", **({"Authorization": f"Bearer {key}"} if key else {})}
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        raise SystemExit(f"HTTP {err.code} from {url}: {err.read().decode('utf-8', 'replace')[:400]}") from err
    except urllib.error.URLError as err:
        raise SystemExit(f"Could not reach {url}: {err.reason}") from err


def visible(text: str) -> str:
    return re.sub(r"<think>.*?</think>\s*", "", text or "", flags=re.S).strip()  # reasoning some open models print


def run_tool(name: str, arguments: str | dict, show) -> str:
    try:
        args = json.loads(arguments) if isinstance(arguments, str) else dict(arguments or {})
    except json.JSONDecodeError:
        return f"The arguments were not valid JSON: {arguments!r}"
    show(f"[{name}]")
    text, _ = skill.call_tool(name, args)
    return text


class ChatCompletions:
    """POST {base}/chat/completions, as Ollama, LM Studio, vLLM, llama.cpp, OpenAI and xAI serve it."""

    def __init__(self, args, key: str):
        self.args, self.key = args, key
        self.messages = [{"role": "system", "content": system_prompt(not args.no_tools)}]
        self.tools = [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                        "parameters": t["inputSchema"]}} for t in skill.TOOLS]

    def ask(self, text: str, show) -> str:
        self.messages.append({"role": "user", "content": user_turn(text)})
        for _ in range(MAX_STEPS):
            payload = {"model": self.args.model, "messages": self.messages}
            if not self.args.no_tools:
                payload["tools"] = self.tools
            message = post(self.args.base_url.rstrip("/") + "/chat/completions", payload, self.key)["choices"][0]["message"]
            calls = message.get("tool_calls") or []
            self.messages.append({"role": "assistant", "content": message.get("content") or "",
                                  **({"tool_calls": calls} if calls else {})})
            if not calls:
                return visible(message.get("content"))
            for call in calls:
                output = run_tool(call["function"]["name"], call["function"].get("arguments") or "{}", show)
                self.messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": output})
        return "(stopped after too many tool calls)"


class Ollama(ChatCompletions):
    """POST {host}/api/chat, Ollama's own API, which takes the context size per request. Its OpenAI-style endpoint
    uses the server's default (4096 tokens in many installs), too small for the skill's instructions."""

    def ask(self, text: str, show) -> str:
        self.messages.append({"role": "user", "content": user_turn(text)})
        url = re.sub(r"/v1/?$", "", self.args.base_url.rstrip("/")) + "/api/chat"
        for _ in range(MAX_STEPS):
            payload = {"model": self.args.model, "messages": self.messages, "stream": False,
                       "options": {"num_ctx": self.args.ctx}}
            if not self.args.no_tools:
                payload["tools"] = self.tools
            message = post(url, payload, self.key)["message"]
            calls = message.get("tool_calls") or []
            self.messages.append({"role": "assistant", "content": message.get("content") or "",
                                  **({"tool_calls": calls} if calls else {})})
            if not calls:
                return visible(message.get("content"))
            for call in calls:
                output = run_tool(call["function"]["name"], call["function"].get("arguments") or {}, show)
                self.messages.append({"role": "tool", "tool_name": call["function"]["name"], "content": output})
        return "(stopped after too many tool calls)"


class Responses:
    """POST {base}/responses, the OpenAI Responses shape, as some hosted models serve it."""

    def __init__(self, args, key: str):
        self.args, self.key = args, key
        self.instructions = system_prompt(not args.no_tools)
        self.items: list[dict] = []
        self.tools = [{"type": "function", "name": t["name"], "description": t["description"],
                       "parameters": t["inputSchema"]} for t in skill.TOOLS]

    def ask(self, text: str, show) -> str:
        self.items.append({"role": "user", "content": user_turn(text)})
        for _ in range(MAX_STEPS):
            payload = {"model": self.args.model, "instructions": self.instructions, "input": self.items}
            if not self.args.no_tools:
                payload["tools"] = self.tools
            output = post(self.args.base_url.rstrip("/") + "/responses", payload, self.key).get("output") or []
            calls = [o for o in output if o.get("type") == "function_call"]
            self.items += [o for o in output if o.get("type") in ("message", "function_call")]
            if not calls:
                return visible("".join(c.get("text", "") for o in output if o.get("type") == "message"
                                       for c in o.get("content") or [] if c.get("type") == "output_text"))
            for call in calls:
                result = run_tool(call["name"], call.get("arguments") or "{}", show)
                self.items.append({"type": "function_call_output", "call_id": call["call_id"], "output": result})
        return "(stopped after too many tool calls)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ethical Research on any model behind an OpenAI-style API.")
    parser.add_argument("--base-url", required=True, help="e.g. http://localhost:11434/v1 for Ollama")
    parser.add_argument("--model", required=True)
    parser.add_argument("--api", choices=("chat", "responses", "ollama"), default="chat",
                        help="the API shape: chat (OpenAI Chat Completions, the default), responses, or ollama "
                             "(Ollama's own API, which lets --ctx set the context size)")
    parser.add_argument("--ctx", type=int, default=16384, help="with --api ollama, the context size (default 16384)")
    parser.add_argument("--key-env", help="name of the environment variable that holds the API key, if one is needed")
    parser.add_argument("--no-tools", action="store_true", help="for a model without tool calling")
    parser.add_argument("--once", metavar="MESSAGE", help="send one message, print the answer and exit")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    key = os.environ.get(args.key_env, "") if args.key_env else ""
    if args.key_env and not key:
        parser.error(f"the environment variable {args.key_env} is empty")
    session = {"responses": Responses, "ollama": Ollama}.get(args.api, ChatCompletions)(args, key)
    show = lambda line: print(line, file=sys.stderr, flush=True)  # noqa: E731
    if args.once:
        print(session.ask(args.once, show))
        return 0
    print(f"Ethical Research on {args.model}. Modes: /modes. Leave: /quit.", file=sys.stderr)
    while True:
        try:
            text = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if text in ("/quit", "/exit"):
            return 0
        if text == "/modes":
            print(", ".join("/" + m for m in skill.mode_files()) or "(no modes in this copy of the skill)")
            continue
        if text:
            print("\n" + session.ask(text, show))


if __name__ == "__main__":
    sys.exit(main())
