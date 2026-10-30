# Run it anywhere

Ethical Research is two things that travel separately: **the skill** (instructions: `skills/ethical-research/`, an [Agent Skill](https://agentskills.io)) and **the checks** (four scripts, served to any host by the MCP server `skills/ethical-research/scripts/mcp_server.py`, or called by the runner `chat.py`). A host needs the first to behave as the skill describes and the second to check in code. Both need Python 3.10 or newer and nothing else.

Hosts change fast. What follows was checked against each vendor's documentation on **2026-10-30**; the links are where to look if a step has moved.

| Host | The skill | The checks | How |
| --- | --- | --- | --- |
| Claude Code | plugin | scripts | [below](#claude) |
| Claude apps | uploaded zip | code execution, where on | [below](#claude) |
| Codex, ChatGPT desktop app | `~/.agents/skills` or the plugin | MCP (local) | [below](#openai-chatgpt-and-codex) |
| ChatGPT on the web and phone | plugin | MCP (remote, HTTPS) | [below](#openai-chatgpt-and-codex) |
| Grok Build CLI | reads the Claude plugin and `~/.agents/skills` | MCP (local) | [below](#xai-grok) |
| grok.com | uploaded zip | MCP connector (remote, HTTPS) | [below](#xai-grok) |
| Muse Code | `~/.agents/skills` | MCP (local) | [below](#meta-muse) |
| Gemini app | uploaded zip | not available (see below) | [below](#google-gemini) |
| Gemini CLI, Antigravity CLI | extension or plugin | MCP (local) | [below](#google-gemini) |
| GitHub Copilot and VS Code, Cursor, OpenCode, Goose, Kimi Code | `~/.agents/skills` | MCP (local) | [below](#other-agent-hosts) |
| Any model behind an API: OpenAI, xAI, Meta, Ollama, LM Studio, vLLM, llama.cpp | system prompt, by `chat.py` | tools, by `chat.py` | [below](#models-behind-an-api-open-or-hosted) |
| LM Studio, Open WebUI | system prompt | MCP | [below](#local-model-apps) |

Below, `<skill>` is the path of `skills/ethical-research` in your copy of this repository, and `python3` is `python` on Windows.

## The MCP server

```
python3 <skill>/scripts/mcp_server.py               # for a host that starts it (stdio)
python3 <skill>/scripts/mcp_server.py --http 8765   # for a host that connects: http://127.0.0.1:8765/mcp
```

It offers six tools (`check_references`, `find_sources`, `check_statistics`, `grim_test`, `scan_manuscript`, `ledger`), the skill and its twelve modes as prompts (for a host that supports MCP but not skills), and the skill's references as resources. It speaks the current protocol (2026-07-28) and the earlier ones that open with a handshake, so old and new hosts both work. Over HTTP it does not touch local files (no manuscript by path, no ledger) unless started with `--allow-files`; it listens only on this machine unless `--host` says otherwise, and needs HTTPS in front of it before anything outside can reach it.

Most hosts take a local server as a command and its arguments; the generic entry is:

```json
{ "mcpServers": { "ethical-research": { "command": "python3", "args": ["<skill>/scripts/mcp_server.py"] } } }
```

## Claude

- **Claude Code**: `/plugin marketplace add ji-hun-git/ethical-research`, then `/plugin install ethical-research@ethical-research`. The checks run as scripts; no MCP needed.
- **Claude apps** (web, desktop, mobile): `python scripts/build_skill_zip.py`, then upload `dist/ethical-research.zip` as a custom skill. The checks run where code execution is on.
- **Claude Desktop**, for the checks as tools in any chat: add the generic entry above to `claude_desktop_config.json`.

## OpenAI: ChatGPT and Codex

- **Codex** (CLI, IDE, and the ChatGPT desktop app, which share skills and MCP settings): copy the skill and register the server.
  ```
  cp -r <skill> ~/.agents/skills/
  codex mcp add ethical-research -- python3 <skill>/scripts/mcp_server.py
  ```
  This repository is also a plugin in OpenAI's portable format (`plugin.json` and `mcp.json` at the root, skills under `skills/`). [Skills](https://learn.chatgpt.com/docs/build-skills), [MCP in Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), [plugins](https://developers.openai.com/plugins/build/plugins.md).
- **ChatGPT on the web and phone** uses skills through plugins, and reaches MCP servers only over HTTPS. Run the server with `--http` behind an HTTPS address you control, then add it at chatgpt.com/plugins as a custom MCP server. Which plans allow custom servers, and with what access, depends on the workspace ([custom MCP servers](https://developers.openai.com/api/docs/guides/custom-mcp-server.md)).
- **Custom GPTs** are being retired in favour of plugins, so this repository does not ship one.

## xAI: Grok

- **Grok Build CLI** reads Claude Code plugins and `~/.agents/skills` without setup ([skills and plugins](https://docs.x.ai/build/features/skills-plugins-marketplaces)). Add the checks with `grok mcp add ethical-research -- python3 <skill>/scripts/mcp_server.py` ([MCP](https://docs.x.ai/build/features/mcp-servers)).
- **grok.com**: upload `dist/ethical-research.zip` as a skill, on plans that offer skills ([Grok skills](https://x.ai/news/grok-skills)). The checks need a custom connector, which takes a public HTTPS address: the server with `--http`, behind HTTPS ([connectors](https://docs.x.ai/grok/connector-management)).
- **The xAI API**: `chat.py` (below) with `--base-url https://api.x.ai/v1 --api responses --key-env XAI_API_KEY` and a current Grok model name.

## Meta: Muse

- **Muse Code** reads `~/.agents/skills` (and `~/.claude/skills`, `~/.codex/skills`): copy the skill there, and register the server as a stdio MCP server in its `mcp_servers` settings ([extending Muse Code](https://dev.meta.ai/docs/muse-code/extending.md)).
- **The Meta API** serves Muse models in both the Chat Completions and the Responses shape at `https://api.meta.ai/v1` ([docs](https://dev.meta.ai/docs/tool-calling.md)). Both worked with `chat.py` on 2026-10-30, with the model calling the checks itself:
  ```
  python3 <skill>/scripts/chat.py --base-url https://api.meta.ai/v1 --model muse-spark-1.3 --key-env META_API_KEY
  ```
- **The Muse app** has no documented way to add a skill or local tools.

## Google: Gemini

- **Gemini app**: Customize, Skills, Create, Upload, then `dist/ethical-research.zip` (web and Mac). Skills there cannot run scripts that need the internet, so the reference checks are not available; the skill says which check it could not run and goes on ([Gemini skills](https://support.google.com/gemini/answer/17094296)). Gems are moving to skills, so this repository does not ship a Gem.
- **Gemini CLI**: `gemini extensions install https://github.com/ji-hun-git/ethical-research` installs the skills and the MCP server together (`gemini-extension.json`; [extensions](https://geminicli.com/docs/extensions/reference/)).
- **Antigravity CLI**: with the plugin installed in Claude Code, `agy plugin import claude` brings it over ([plugins](https://antigravity.google/docs/plugins?tab=cli)). Its skills folder `.agents/skills` also takes a copy of the skill.

## Other agent hosts

GitHub Copilot (CLI, VS Code, Visual Studio, JetBrains), Cursor, OpenCode, Goose and Kimi Code all read skills from `~/.agents/skills` (and from `.agents/skills` in a project): `cp -r <skill> ~/.agents/skills/`. Register the server in each host's MCP settings with the generic entry above ([VS Code](https://code.visualstudio.com/docs/copilot/customization/agent-skills), [Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), [Cursor](https://cursor.com/docs/context/skills), [OpenCode](https://opencode.ai/docs/skills/), [Goose](https://goose-docs.ai/docs/guides/context-engineering/using-skills), [Kimi Code](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html)).

## Models behind an API, open or hosted

`chat.py` runs the skill on any model behind an OpenAI-style API: the skill's instructions become the system prompt and the checks become tools the model calls. Start a message with a mode (`/er-plan ...`) to use it.

```
python3 <skill>/scripts/chat.py --base-url http://localhost:11434 --api ollama --model <model>   # Ollama
python3 <skill>/scripts/chat.py --base-url http://localhost:1234/v1 --model <model>              # LM Studio
python3 <skill>/scripts/chat.py --base-url http://localhost:8000/v1 --model <model>              # vLLM, llama.cpp
python3 <skill>/scripts/chat.py --base-url https://api.openai.com/v1 --api responses --model <model> --key-env OPENAI_API_KEY
```

- **Ollama**: use `--api ollama`. Its OpenAI-style endpoint uses the server's default context size, 4,096 tokens in many installs, and the skill's instructions alone take about 3,700; `--api ollama` asks for 16,384 (`--ctx` to change).
- **vLLM** needs tool calling switched on (`--enable-auto-tool-choice --tool-call-parser <parser>`), and **llama.cpp's** server needs `--jinja` ([vLLM](https://docs.vllm.ai/en/latest/features/tool_calling.html), [llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md)).
- **A model without tool calling** runs with `--no-tools`: it is told which checks it cannot run.
- **Which model**: one with tool calling and a context of 16,000 tokens or more. A 2-billion-parameter model on Ollama called the statistics check and caught the error in our test, then wrote a false AI-use statement: small models follow the skill loosely, so check what they say.
- The key is read from the environment variable `--key-env` names and is sent only to `--base-url`.

## Local model apps

- **LM Studio** reads MCP servers from its `mcp.json` (Program, Install, Edit mcp.json), in the generic format above; paste the skill's instructions into the system prompt, or use the MCP prompt `ethical-research` ([LM Studio MCP](https://lmstudio.ai/docs/app/mcp)).
- **Open WebUI** connects to MCP servers over HTTP only: run the server with `--http 8765`, then add a connection of type MCP (Streamable HTTP) at `http://localhost:8765/mcp` in the admin settings ([Open WebUI MCP](https://docs.openwebui.com/features/extensibility/mcp)).
