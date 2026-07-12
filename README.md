# TouchDesigner MCP

**Drive TouchDesigner with any LLM** — an MCP server that lives inside your TD project
as a single `.tox`, plus the knowledge layer that makes the LLM actually good at TD.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![TouchDesigner](https://img.shields.io/badge/TouchDesigner-2023.12600%2B-blue)](https://derivative.ca/download)
[![MCP](https://img.shields.io/badge/MCP-compatible-green)](https://modelcontextprotocol.io)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#contributing)

<!-- DEMO GIF: hero — 20-30s screen recording: split screen of Claude Code
     (or Claude Desktop) on the left and TouchDesigner on the right; prompt
     "build an audio-reactive feedback scene", watch operators appear, wire
     themselves, and the output render live. Export ~800px wide GIF or MP4,
     place in docs/media/hero.gif -->
![Demo: building a TD network from a prompt](docs/media/hero.gif)

## What it does

- **Builds and wires networks from prompts** — the agent creates operators, connects
  them, and sets parameters (with validation that returns the correct names/menu
  values on error) via structured tools: `create`, `wire`, `set`.
- **Sees its own output** — `observe` returns an actual PNG/GIF of any TOP *plus* a
  pixel-stats verdict (`black` / `flat` / `transparent` / `static` / `ok`), so dead
  chains are caught objectively even when nothing errors.
- **Verifies the whole project in one call** — `health` sweeps every operator for
  errors/warnings, ranks cook-time hotspots (CPU+GPU ms), and measures real fps.
- **Renders MP4s** — `render` records a TOP (with synchronized audio from a CHOP) to
  video via TD-native recording + ffmpeg.
- **Runs arbitrary Python inside TD** — `run` executes in TD's embedded Python with
  full network access; anything doable by hand is doable from a prompt.
- **Works with any MCP client** — Claude Code, Claude Desktop, Cursor, Windsurf, or
  anything else that speaks MCP Streamable HTTP.

## Not just a server — a knowledge layer

An MCP server gives a model hands; it doesn't make the model *good at TouchDesigner*.
TD is full of traps for an LLM — abbreviated parameter names, feedback loops that fail
silently, audio chains that quietly cook at 44.1kHz and drop the project to 1fps. This
repo ships the accumulated, machine-verified knowledge that closes that gap:

- **[The `touchdesigner-building` skill](.claude/skills/touchdesigner-building/SKILL.md)**
  — the build loop, verified tool-call signatures, correct-vs-guessed parameter names,
  GLSL uniform wiring, feedback-loop semantics, resolution management.
  With three deep-dive companions:
  [reference.md](.claude/skills/touchdesigner-building/reference.md) (pixel formats,
  time slicing, POPs, Python performance hierarchy, codecs),
  [debugging.md](.claude/skills/touchdesigner-building/debugging.md) (symptom → fix
  tables, automated verification, the performance-triage workflow), and
  [patterns.md](.claude/skills/touchdesigner-building/patterns.md) (proven recipes:
  audio analysis chains, reaction-diffusion feedback, particle systems, optical flow).
- **Opinionated aesthetic defaults** — [patterns.md](.claude/skills/touchdesigner-building/patterns.md)
  has taste, on purpose: dark-canvas idle states, multiplicative audio mappings that
  rest at identity, 2–3-hue palette discipline, and a visual vocabulary inspired by
  Refik Anadol and Max Cooper. If your aesthetic differs, edit the "Aesthetic
  defaults" section of that file — everything else in it is aesthetic-neutral.
- **[MACHINE.md](MACHINE.md)** — a regenerable per-machine profile: GPU budgets, TD
  build quirks, license limits, known instabilities. The shipped copy is a worked
  example (a below-spec Intel MacBook — a usefully extreme worst case) *and* the
  template: ask the agent to re-verify it on your machine.
- **[docs/network-notes/](docs/network-notes/)** — distilled write-ups of real-world
  TD networks (reaction-diffusion feedback, projection-mapping rigs, beat-gated video,
  audio-reactive particles…), so the agent composes from studied patterns instead of
  inventing node soup.
- **[LEARN-MCP.md](LEARN-MCP.md)** — a from-zero MCP tutorial that uses this server
  as the dissection specimen, ending with how to add your own tool in ~20 lines.

## How it works

```
MCP client (Claude Code / Desktop / Cursor / …)
        │
        │  MCP Streamable HTTP — JSON-RPC over POST, localhost:9988
        ▼
Web Server DAT  ←  mcp/td_mcp_server.tox (dropped into your project)
        │
        ▼
TouchDesigner — embedded Python with full network access
```

There is no separate process and nothing to install: the server **is** a `.tox` inside
your project, answering MCP requests from a Web Server DAT callback. TD's embedded
Python has full access to the network (`op()`, `.create()`, `.par`, connectors), so
the bridge can do anything you could do by hand. Details: [mcp/README.md](mcp/README.md).

## Requirements

- **TouchDesigner** — developed and verified on build **2023.12600**; the upstream
  project targets 2024+. Any build with a Web Server DAT and Python 3 should work.
  All license tiers work (non-commercial included — see [MACHINE.md](MACHINE.md) for
  license-specific codec limits).
- **OS** — developed and tested on macOS (Metal). Windows is expected to work — the
  bridge is pure Python on a cross-platform DAT with no OS-specific code — but is
  untested here.
- **ffmpeg** on your PATH — required by the `render` tool's final MP4 encode and the
  animated `observe` mode. Everything else has zero dependencies.
- **MCP client** — tested with Claude Code and Claude Desktop; any Streamable-HTTP MCP
  client should work.

## Installation

1. **Clone the repo:**

   ```sh
   git clone https://github.com/visheshkochher/TouchAI.git
   cd TouchAI
   ```

2. **Open your TouchDesigner project** (or a new empty one).

3. **Drag `mcp/td_mcp_server.tox` into the network.** The server starts immediately on
   port **9988** — no configuration. Verify from a terminal:

   ```sh
   curl http://127.0.0.1:9988/health
   # → {"status": "ok", "server": "touchdesigner"}
   ```

   The `.tox` saves with your `.toe`, so this is one-time per project.

4. **Connect a client:**

   **Claude Code** — the repo already contains `.mcp.json`, which auto-loads when you
   start `claude` from the repo root:

   ```json
   {
     "mcpServers": {
       "touchdesigner": {
         "type": "http",
         "url": "http://127.0.0.1:9988/mcp"
       }
     }
   }
   ```

   Or register it from anywhere with one command:

   ```sh
   claude mcp add --transport http touchdesigner http://127.0.0.1:9988/mcp
   ```

   **Claude Desktop** — add to `claude_desktop_config.json` (Settings → Developer →
   Edit Config):

   ```json
   {
     "mcpServers": {
       "touchdesigner": {
         "type": "http",
         "url": "http://127.0.0.1:9988/mcp"
       }
     }
   }
   ```

   **Any other MCP client** — point it at `http://127.0.0.1:9988/mcp`, transport type
   *Streamable HTTP*.

5. **Smoke test** — first prompt:

   > List the operators in /project1 and observe the current output.

   Success looks like: the agent lists the operators, then shows a captured image of
   your project's output with pixel stats. The loop is live.

6. **First-run advice** — the shipped [MACHINE.md](MACHINE.md) describes the
   *author's* machine. Regenerate it for yours with one prompt:

   > Re-verify MACHINE.md on this machine and rewrite it.

<!-- DEMO GIF: install — 10-15s: dragging the .tox into a TD network and the
     smoke-test prompt succeeding in Claude Code. docs/media/install.gif -->

## Tool reference

All 14 tools, from [`mcp/td_mcp_server.py`](mcp/td_mcp_server.py):

| Tool | Description | Example arguments |
|---|---|---|
| `run` | Execute Python inside TD — expressions return values, multi-line code captures stdout; errors return full tracebacks | `{"code": "op('/project1/noise1').par.period.eval()"}` |
| `inspect` | Detailed operator info: type, channels with values, params, errors, connections | `{"path": "/project1/audio_bands"}` |
| `set` | Set params with name validation; constants and/or expressions | `{"path": "/project1/blur1", "params": {"size": 20}, "exprs": {"rotate": "me.time.seconds*10"}}` |
| `create` | Create an operator — type resolution, destroy-before-create, params, wiring, and placement in one call | `{"type": "noiseTOP", "name": "flow_field", "nodeX": 0, "nodeY": 200, "params": {"period": 4}}` |
| `wire` | Batch-wire connections and parameter-expression links, auto-incrementing input indices | `{"connections": [{"from": "/project1/noise1", "to": "/project1/comp1", "to_input": 1}]}` |
| `observe` | Capture a TOP as PNG (snapshot) or GIF (animated) + pixel `stats` with a verdict: black/flat/transparent/static/ok | `{"top": "/project1/final_out", "mode": "animated", "duration": 2}` |
| `health` | Project-wide error/warning sweep + cook-time hotspot ranking + real fps since the previous call | `{"path": "/project1"}` |
| `read` | Read a DAT's text (optional offset/limit) | `{"path": "/project1/my_glsl_pixel"}` |
| `write` | Overwrite a DAT's text (creates a TextDAT if missing) | `{"path": "/project1/shader_code", "content": "out vec4 fragColor; …"}` |
| `edit` | Exact find/replace inside a DAT | `{"path": "/project1/my_glsl_pixel", "old_string": "0.5", "new_string": "0.8"}` |
| `list` | List operators under a container, filterable by family and name pattern | `{"path": "/project1", "family": "TOP", "pattern": "fb_*"}` |
| `docs` | Parameter docs (pages, defaults, menu options) + connectors for any op type; `list_types` enumerates type constants | `{"type": "feedbackTOP", "filter": "reset"}` |
| `map` | Text map of the network: operators, connections, positions, non-default params | `{"path": "/project1", "family": "TOP"}` |
| `render` | Record a TOP to MP4 (TD-native image sequence + optional audio CHOP, ffmpeg encode) | `{"top": "/project1/final_out", "output": "renders/take1.mp4", "duration": 10, "audio_chop": "/project1/audio_in"}` |

## Usage patterns

The recommended iteration loop (the skill enforces this):

1. **Build** — `create`/`wire`/`set`, or `run` for multi-op scripts.
2. **Health-check** — `health` catches errors in ops you didn't touch.
3. **Observe and actually look** — capture the output TOP, judge the image, and trust
   the stats verdict: `black`/`flat`/`transparent`/`static` means a dead chain even
   with zero errors. **Never declare a visual done unseen.**
4. **Adjust and re-observe** until it matches the request.

> **⚠️ About `run`:** it executes arbitrary Python on TD's **main thread**.
> `time.sleep` inside it freezes cooking entirely — return, wait in your shell, then
> call `run` again. And since it can rewire or delete anything, keep backups of
> projects you care about (work on copies).

Example prompts showing the range:

> Build an audio-reactive feedback scene in /project1 driven by the default audio
> file — dark background, glowing structures, kick-driven zoom. Show me an animated
> capture.

> The output is black. Diagnose why and fix it.

> Render 10 seconds of /project1/final_out with audio to renders/demo.mp4.

<!-- DEMO GIF: iteration loop — 20s: agent observes a black output, diagnoses
     via health/inspect, fixes the parameter, re-observes a working visual.
     docs/media/debug-loop.gif -->

## Troubleshooting

| Symptom | Fix |
|---|---|
| Port 9988 not responding / client can't connect | TD isn't running, or the `.tox` isn't in the open project. Re-drag it; check the Web Server DAT is Active. `curl http://127.0.0.1:9988/health` to confirm. |
| `touchdesigner` tools missing in the client | Restart the client — MCP configs are read at startup. In Claude Code, `/mcp` shows connection status. |
| `observe` returns black/transparent | Usually the network, not the bridge — that's exactly what the stats verdict is for. Common causes: unclosed feedback loop (`top` param unset), dead GLSL uniform, all-zero source. See [debugging.md](.claude/skills/touchdesigner-building/debugging.md). |
| TD frozen during a long `run` | `run` blocks TD's main thread; a `time.sleep` or heavy loop inside it freezes cooking until it returns. Wait it out, then restructure: return early and wait in the shell between calls. |
| MCP timeouts, TD at high CPU, `/health` dead | The TD main thread can wedge after rapid set+observe bursts (see [MACHINE.md](MACHINE.md)). Only recovery: force-quit TD. Keep scenes rebuildable from scripts. |
| `render` fails or produces no file | Check ffmpeg is on PATH. On some build/license combos GPU H.264 encode is blocked — the manual Movie File Out recipe is in [debugging.md](.claude/skills/touchdesigner-building/debugging.md). |

## How it differs from upstream

Forked from [johnsabath/touchdesigner-mcp](https://github.com/johnsabath/touchdesigner-mcp)
(MIT) — the excellent single-`.tox` Web Server DAT design, the 13 core tools, and the
original skill are all upstream's work ([upstream README](mcp/UPSTREAM_README.md)).
This repo adds:

- **`health` tool** — one-call project verification: full error/warning sweep,
  cook-time hotspot ranking, and real-fps measurement.
- **`observe` pixel-stats verdicts** — every capture now includes mean/std/alpha
  stats and a `black`/`flat`/`transparent`/`static`/`ok` verdict computed from the
  full-res frame, so the agent catches dead chains it would misread from a thumbnail.
- **The knowledge layer** — a heavily extended skill (verified parameter names,
  feedback semantics, performance triage, proven visual recipes with aesthetic
  defaults), the regenerable [MACHINE.md](MACHINE.md) machine profile,
  [docs/network-notes/](docs/network-notes/) studies of real networks, and the
  [LEARN-MCP.md](LEARN-MCP.md) tutorial.

## Contributing

PRs welcome — especially verified TD quirks for the skill files and new network notes.

## License

[MIT](LICENSE) — retains upstream's copyright.
