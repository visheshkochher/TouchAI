# LEARN-MCP — Model Context Protocol, explained with this repo

This repo contains a complete, working MCP server: `mcp/td_mcp_server.py`, ~2250 lines
of plain Python running *inside* TouchDesigner, which is how Claude builds visuals here.
That makes it a perfect dissection specimen — small enough to read in one sitting, real
enough to show every concept that matters. This document teaches MCP from zero, pointing
at the actual lines in this repo the whole way.

---

## 1. The problem MCP solves

An LLM is a text-in, text-out function. It cannot touch TouchDesigner, your filesystem,
or a database. Before MCP, every AI app invented its own plugin format, so a
"TouchDesigner integration" written for one chat app was useless in every other one.

**MCP (Model Context Protocol)** is an open standard (published by Anthropic, late 2024)
that fixes the *plug shape*. Think USB-C: a server that speaks MCP works unchanged with
Claude Code, Claude Desktop, an Agent SDK script, or any other MCP-capable client. This
repo proves the point — the same `.tox` serves Claude Code today and could serve
Claude Desktop, Cursor, or a custom Agent SDK app with zero changes.

## 2. The three roles

```
┌────────────────────────┐        ┌──────────────────────────┐
│ HOST (Claude Code)     │        │ SERVER (td_mcp_server.py │
│  the AI app the human  │        │  inside TouchDesigner)   │
│  talks to              │        │                          │
│  ┌──────────────────┐  │  MCP   │  exposes 14 tools:       │
│  │ CLIENT           │──┼────────┼─ create, wire, set, run, │
│  │ one per server;  │  │ HTTP   │  observe, inspect, map,  │
│  │ speaks protocol  │  │ :9988  │  docs, read/write/edit,  │
│  └──────────────────┘  │        │  list, render, health    │
└────────────────────────┘        └──────────────────────────┘
```

- **Host** — the application with the LLM in it. It decides *when* to call a tool
  (actually, the model decides; the host executes).
- **Client** — the protocol plumbing the host spins up, one per configured server.
- **Server** — any process that exposes capabilities. It knows nothing about the model;
  it just answers structured requests. Ours happens to live inside a running TD project,
  which is what gives Claude hands.

A server can offer three kinds of capability. Ours implements only the first:

| Capability | What it is | In this repo |
|---|---|---|
| **Tools** | Functions the *model* chooses to call (side effects allowed) | all 14 |
| **Resources** | Read-only data the *host/user* attaches as context (like files) | not implemented |
| **Prompts** | Reusable prompt templates the *user* invokes | not implemented |

That's a deliberate design choice: for "drive TD," everything is an action, so tools
suffice. See §8 for what adding the other two would look like.

## 3. The wire format: JSON-RPC 2.0

Everything on the wire is [JSON-RPC 2.0](https://www.jsonrpc.org/specification) — a
20-year-old, dead-simple envelope:

```json
{"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {...}}   ← request
{"jsonrpc": "2.0", "id": 7, "result": {...}}                            ← response
{"jsonrpc": "2.0", "method": "notifications/initialized"}               ← notification (no id → no reply)
```

In our server that's literally three helper functions —
`_jsonrpc_response`, `_jsonrpc_error` (`mcp/td_mcp_server.py:2084-2093`), and the
dispatcher `_handle_one` (`:2096`), which is just an if/elif on `method`. There is no
framework. MCP is small enough to implement with `json.loads` and a dict.

Two error channels, and the distinction matters:

- **Protocol errors** → JSON-RPC `error` object (e.g. unknown tool → code `-32601`,
  `:2124`). "You spoke wrong."
- **Tool failures** → a *successful* JSON-RPC response whose result has `"isError": true`
  (`:2163-2172`). "You spoke fine; the thing you asked for failed." The model gets to
  read the traceback and try again — this is why a typo'd param name comes back to
  Claude as feedback instead of killing the session.

## 4. Transports: how the JSON moves

MCP defines two standard transports:

- **stdio** — host launches the server as a subprocess, JSON flows over stdin/stdout.
  Right for local CLI-style servers. Doesn't fit TD, because the server must live
  inside an already-running GUI app.
- **Streamable HTTP** — server is an independent process with one HTTP endpoint
  (`POST /mcp`). Right for long-running or remote servers. That's ours.

Look at `onHTTPRequest` (`:2212`) — the entire transport is one callback on a
TouchDesigner **Web Server DAT** listening on port 9988:

- `POST /mcp` with a JSON-RPC body → parse, dispatch, respond (`:2251-2262`)
- `GET /mcp` → 405: the optional server-push SSE stream is *not implemented*, and
  doesn't need to be — the spec lets simple servers answer plain JSON per POST (`:2247`)
- `GET /health` → liveness check outside MCP proper (`:2239`) — this is what tells you
  the TD main thread has wedged (see CLAUDE.md's constraints)
- `Mcp-Session-Id` header issued on initialize (`:2261`) — the spec's lightweight
  session mechanism; ours is a single UUID since TD has exactly one client at a time
- CORS headers (`:2225-2229`) so a browser-based host could connect too

**A subtle, TD-specific consequence:** the Web Server DAT callback runs on TD's main
thread. Every tool call briefly blocks cooking, and `time.sleep` inside `run` freezes
the whole engine — a transport decision (in-process HTTP) leaking into usage rules
(CLAUDE.md's "wait in the shell, not in `run`").

## 5. The lifecycle: what happens when Claude Code starts

1. Claude Code reads **`.mcp.json`** at the repo root:
   ```json
   { "mcpServers": { "touchdesigner": { "type": "http", "url": "http://127.0.0.1:9988/mcp" } } }
   ```
   This file is the entire client-side configuration. Change the URL to a LAN IP and
   the same setup drives a remote GPU rig (`mcp/README.md`).

2. Client sends **`initialize`** → server replies with its `protocolVersion`
   (`"2025-03-26"`, `:19`), `serverInfo` (name/version), and `capabilities`
   (`{"tools": {}}` = "I have tools, nothing else", `:24-26`, handled at `:2105`).
   Version and capability negotiation happen here — a client that needs resources
   knows immediately not to ask.

3. Client sends **`notifications/initialized`** (fire-and-forget, `:2112`).

4. Client sends **`tools/list`** → server returns the `TOOLS` array (`:31`). Each tool
   is a name + natural-language `description` + **`inputSchema`** (JSON Schema for its
   arguments). The host folds these into the model's context — *this is the only thing
   the model ever "knows" about the server*. Read the `run` tool's description
   (`:34`): it embeds usage warnings ("use docs first — TD names are abbreviated",
   "use par.expr for expressions"). Tool descriptions are prompts. Writing them well
   is prompt engineering, and it's why this server steers even a smaller model away
   from known failure modes.

5. From then on, the model emits tool calls; the host turns each into
   **`tools/call`** with `{"name": ..., "arguments": {...}}`; the server looks up the
   handler in a plain dict (`TOOL_HANDLERS`, dispatch at `:2118-2124`) and returns
   **content blocks**.

## 6. Content blocks: how results (and images) come back

A tool result is a list of typed blocks, not a bare string (`:2129-2162`):

```json
{ "content": [
    {"type": "text",  "text": "{ \"cook_ms\": 4.2 }"},
    {"type": "image", "data": "<base64 PNG>", "mimeType": "image/png"}
]}
```

The `observe` handler (`:593`) captures a TOP, encodes PNG/GIF *with hand-rolled PNG
chunk writing* (`_encode_single_png`, `:450` — remember, this Python runs inside TD
with no pip), and returns it as an `image` block. The host feeds that image straight
into the model's vision input.

**This is the single most important design idea in the repo:** the CLAUDE.md iteration
loop ("never declare a visual done without having seen it") is only possible because
MCP results are multimodal. A tool that returned "observe succeeded" as text would be
useless; returning *the pixels* closes the feedback loop between the model and the
canvas.

## 7. Tool design lessons (why these 14, shaped this way)

Compare the tool list against the raw capability — `run` alone can do everything, since
it executes arbitrary Python inside TD. So why 12 more tools?

- **Structured beats general.** `create`/`wire`/`set` cover 90% of network edits with
  validation, destroy-before-create idempotency, and typed errors. `run` is the escape
  hatch, and CLAUDE.md explicitly ranks it last. Rule: *make the correct path the easy
  path, keep the powerful path available.*
- **Validate inside the tool, return the fix.** `set` checks parameter names and, for
  menu params, returns the list of valid values on error. The model's next call is
  right. An unvalidated server would silently no-op (TD's own behavior) and the model
  would never know. Rule: *a tool's error message is model feedback — spend effort on it.*
- **Make the server self-describing.** `docs` serves operator/param documentation from
  inside TD itself. The model doesn't need TD's wiki in its context; it asks. Rule:
  *ship the reference material as a tool, not as prompt bulk.*
- **Perception tools, not just action tools.** `inspect` (errors, channels, params),
  `map` (network topology with coordinates), `observe` (pixels). A model that can act
  but not perceive loops blindly. Roughly half this server exists for perception.
- **Granularity = one model intention per tool.** Not `td_api(method, args...)` (too
  coarse to describe, schema tells the model nothing) and not one tool per TD parameter
  (thousands of tools). "Create an operator", "see the output" — verbs at the level the
  model thinks.
- **Failure containment.** Every handler is wrapped so a Python exception inside TD
  becomes an `isError` payload with traceback (`:2163`), never a dead bridge.

The division of labor that emerges in this repo:

| Layer | Holds |
|---|---|
| MCP server (`mcp/`) | *mechanism* — generic verbs, validation, perception |
| Skill (`.claude/skills/touchdesigner-building/`) | *knowledge* — param quirks, recipes, debugging |
| CLAUDE.md | *policy* — safety rules, iteration loop, taste |
| your repo (builder scripts, saved `.tox` components) | *artifacts* — reusable results, network-as-code |

The server stays dumb and stable; intelligence lives in text files the model reads.
That's what keeps the whole system workable even with smaller/cheaper models.

## 8. What this server does NOT implement (and when you'd want it)

- **Resources** — e.g. `td://project1/network.json` as attachable read-only context, or
  a README per reusable component. Useful when a *human* should pick what context to attach;
  here Claude pulls what it needs via `map`/`docs`, so tools cover it.
- **Prompts** — canned templates like "build an audio-reactive scene from {tox}". This
  repo keeps those as skills and scripts instead, which are host-side and versioned in git.
- **Server-push (SSE) / progress notifications** — for long renders, the spec allows
  streaming progress. Ours instead returns fast and lets the model poll — simpler, and
  the TD main-thread constraint makes true streaming impossible anyway.
- **Sampling** — the wildest MCP feature: a server can ask the *client's model* to
  generate text mid-tool-call (server borrows the LLM). E.g. `docs` could summarize a
  wiki page before returning it. Adds latency and complexity; skipped.
- **Auth** — the HTTP endpoint is unauthenticated, which is why `mcp/README.md` says
  LAN-only. Production remote MCP servers use OAuth per the spec's authorization
  extension.

## 9. Exercise: add your own tool in ~20 lines

Say you want `fps` — returns the project's real cook rate. In `td_mcp_server.py`:

1. **Describe it** — append to `TOOLS` (`:31`):
   ```python
   {
       "name": "fps",
       "description": "Measure the project's actual frames-per-second over a short window "
                      "(realtime flag, cook rate, and timeline rate for comparison).",
       "inputSchema": {"type": "object", "properties": {}},
   }
   ```
2. **Implement it** — a handler taking an args dict, returning a JSON-able dict:
   ```python
   def handle_fps(args):
       return {
           "timeline_rate": me.time.rate,
           "realtime": project.realTime,
           "cook_rate": project.cookRate,
       }
   ```
3. **Register it** — add `"fps": handle_fps` to `TOOL_HANDLERS`.
4. Re-save the DAT inside TD (or re-drop the `.tox`), restart the Claude Code session
   so `tools/list` runs again, and the model can now call it.

That's the whole extension surface: *describe, implement, register.* No SDK required —
though for new servers outside TD you'd normally use the official
[Python/TypeScript MCP SDKs](https://modelcontextprotocol.io), which reduce steps 3–4
to a decorator and give you stdio/HTTP transports for free.

## 10. Vocabulary cheat sheet

| Term | Meaning | Here |
|---|---|---|
| Host | AI app the human uses | Claude Code |
| Client | Protocol plumbing, one per server | inside Claude Code, configured by `.mcp.json` |
| Server | Process exposing capabilities | `td_mcp_server.py` in a Web Server DAT |
| Transport | How bytes move | Streamable HTTP, port 9988 |
| JSON-RPC | Message envelope | `_jsonrpc_*` helpers |
| initialize | Handshake + version/capability negotiation | `:2105` |
| Tool | Model-invoked function with JSON Schema args | the 14 |
| Content block | Typed result chunk (text / image / …) | `observe`'s PNG |
| isError | Tool-level failure (model-visible, recoverable) | `:2163` |
| Resource / Prompt / Sampling | Other capability types | not implemented (§8) |

Further reading: [modelcontextprotocol.io](https://modelcontextprotocol.io) (spec +
SDKs), [johnsabath/touchdesigner-mcp](https://github.com/johnsabath/touchdesigner-mcp)
(upstream of this bridge), `mcp/UPSTREAM_README.md` (tool list), `mcp/README.md`
(session checklist).
