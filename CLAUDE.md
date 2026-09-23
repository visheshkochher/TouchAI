# TouchDesigner MCP — driving TD from Claude Code

This repo is an MCP bridge into a running TouchDesigner (TD) project plus the
knowledge layer that makes an LLM good at TD. Claude's job is to compose, modify, and
iterate on TD networks; the human directs aesthetics and judges the result.

## Architecture

```
Claude Code / Claude Desktop / any MCP client
        │  MCP over HTTP (localhost:9988)
TD bridge: mcp/td_mcp_server.tox  (WebServer DAT inside the running TD project)
        │
TouchDesigner
```

- MCP server: forked from johnsabath/touchdesigner-mcp (local source of truth:
  `mcp/td_mcp_server.py`) — a self-contained `.tox` dropped into the open TD project.
  Tools: `create`, `wire`, `set`, `run` (Python), `inspect`, `list`, `read`/`write`/`edit`
  DATs, `observe` (PNG/GIF snapshot + pixel-stats verdict), `health` (project-wide
  error sweep + hotspots + real fps), `render` (MP4), `map`, `docs`.
- TD embeds Python 3 with full network access (`op()`, `.create()`, `.par`, connectors).
  Anything doable by hand is doable from `run`.

## Iteration loop (always follow this)

1. Build or change the network (`create`/`wire`/`set`, or a Python script via `run`).
2. `health` for a project-wide error/warning sweep (catches ops your change broke that
   you didn't touch); `inspect` for detail on specific operators.
3. `observe` the output TOP and **look at the image** — and trust the returned `stats`
   verdict (`black`/`flat`/`transparent` = dead chain even with no errors). The
   exception is `static`: `observe` advances the timeline, not the wall clock, so
   `absTime`-driven animation reads as `static` while running fine (see
   `debugging.md`).
   Judge it against the request (motion, contrast, palette). Adjust and re-observe.
   Never declare a visual done without having seen it.
4. For audio-reactive work, `render` a few seconds of MP4 with audio to verify sync.
5. Before declaring a scene done, verify real fps (frame-delta over wall clock) fits the
   16.6ms/60fps budget — the triage workflow is in the skill's `debugging.md`, and the
   "quality per unit of compute" ladder in `patterns.md` decides where to spend it.
6. **Then audit it for long runs.** Scenes here run unattended for hours, so nothing
   may grow per frame:
   - Script OPs build their channels, rows or points **once** and then only write
     values. `clear()` + `appendChan()` every cook leaks ~2 MB/min of native memory.
   - Every list that gains entries is length-capped and aged out.
   - Every integrated phase wraps or resets at a loop seam.
   - The story loops rather than clamping.

   Then measure TD's process RSS from outside (no bridge calls during the window) over
   7+ minutes with the story looping. A flat Python object count proves nothing on its
   own. The procedure is "The long-run memory audit" in `debugging.md`. Record the
   measured slope in the scene's README.

## Safety rules

- **Never work on a project the user can't restore.** `run` executes arbitrary Python
  inside TD — it can delete or rewire anything. Work on copies (e.g. in a gitignored
  `work/` directory), not originals.
- Prefer the structured tools (`create`/`wire`/`set`) when they suffice; `run` is the
  escape hatch.
- **Audit existing projects for per-frame growth whenever you touch them.** When editing
  or studying any scene, `.tox` or reference `.toe`, grep its scripts for
  `append`/`appendChan`/`appendRow`/`appendPoint`/`clear()`/`store(` and unbounded `+=`
  phases, and fix what fails the long-run rules above. As of this writing every scene
  in `scenes/` except `homestead` and `voyage` still rebuilds its Script CHOP channels
  every frame.
- Anything worth keeping must exist as code or `.tox` in the repo, not only inside a
  `.toe`. Save reusable components with `.save()` as `.tox` files (give each a short
  README: what it does, custom parameters, inputs/outputs), and keep scenes
  rebuildable from idempotent Python builder scripts that destroy-and-recreate their
  own container and never touch anything outside it.

## Repo layout

- `mcp/` — the bridge `.tox`, its Python source, and setup notes (`mcp/README.md`).
- `.claude/skills/touchdesigner-building/` — the skill: SKILL.md, `reference.md`,
  `debugging.md`, `patterns.md`. All machine-independent TD knowledge lives here.
- `docs/network-notes/` — one notes file per studied reference `.toe` project,
  named for the technique it demonstrates (e.g. `reaction-diffusion-feedback.md`),
  summarizing its network + reusable tricks. Read these before inventing new patterns.
- `work/`, `renders/` — gitignored scratch space for working `.toe` copies and
  rendered output. Create them as needed.

## Reading .toe files

`.toe` is binary, but TD ships an expander:

```
/Applications/TouchDesigner.app/Contents/MacOS/toeexpand <file>.toe
```

(On Windows, `toeexpand.exe` sits next to the TouchDesigner executable.) This produces
a `<file>.dir/` tree of readable `.n`/`.parm` text files. Use it to study existing
projects instead of guessing at their contents; distill findings into
`docs/network-notes/<technique-name>.md` and delete the dump afterwards.

## Conventions

- TD operator families: TOP (textures), CHOP (channels/audio/control), SOP (3D geo),
  DAT (text/tables), MAT (materials), COMP (containers/UI). Audio-reactive = Audio
  Device In/File In CHOP → Audio Spectrum/Analyze → Math/Lag/Filter → parameter exports.
- Layout networks left-to-right: inputs → processing → output. Name operators
  descriptively (`audio_bands`, `feedback_loop`, `final_out`) — never leave `null5`.
- Output rig of every scene: `null` TOP `final_out` (display/render endpoint) → `out1`
  **Out TOP** inside the scene COMP, and the COMP wired to an Out TOP
  `/project1/<scene>_out` at project level. A COMP only gets an output connector if it
  contains an Out operator — never end a container at a bare null.
- Resolution: build at 1280x720 while iterating; final output resolution is set
  per-project.

## Machine profile — read `MACHINE.md`

Everything specific to the **current machine, TD build, and license** (GPU budgets and
the load-time watchdog, whether the `render` tool works, codec/license limits, known
instabilities) lives in **`MACHINE.md`** at the repo root — read it at session start
and treat its budgets as hard constraints. On a new machine, regenerate that file
(section headings are the template; re-verify each claim). If `MACHINE.md` is absent,
assume a supported GPU and a licensed build, and verify before relying on either.

One TD-universal rule that belongs here, not there: `run` blocks TD's main thread —
`time.sleep` inside it freezes cooking. For realtime waits, return, wait in the shell,
then call `run` again.

All other machine-verified quirks and researched TD knowledge (tool call signatures,
param/API gotchas, GLSL uniform pitfalls, audio-chain rates, feedback dynamics,
profiling/perf triage, pixel formats, time slicing, POPs, codecs, aesthetic defaults)
live in `.claude/skills/touchdesigner-building/` — SKILL.md, `reference.md`,
`debugging.md`, `patterns.md`. When a new quirk is verified, fold it into the matching
skill file (by topic, not by date) rather than appending it here.

To understand how the MCP bridge itself works (protocol, tool design, how to extend
it), read `LEARN-MCP.md` at the repo root — a tutorial on MCP concepts using this
repo as the worked example.
