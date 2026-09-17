# MACHINE.md — profile of the machine TD runs on

This file holds everything that is true of **one specific machine, TD build, and
license** — not of TouchDesigner in general. The agent reads it at session start
alongside CLAUDE.md and treats its budgets as hard constraints.

**This copy is both a working example and the template.** The values below were
re-verified live against a running TD instance on a second machine (2026-09-14) after
a fresh clone. They replace the original author's below-spec Intel MacBook profile
(see `git log` for that version — it is the more constrained worst case, and worth
reading if you ever move this repo to weaker hardware). On *your* machine: keep the
section headings, re-verify every claim, and rewrite the values — the easiest way is
to ask the agent to "re-verify MACHINE.md on this machine and rewrite it". If this
file is missing, assume the defaults noted per section.

## Hardware / OS (verified 2026-09-14)

- MacBook Pro (Mac17,2) with **Apple M5** (10-core: 4P+6E), **24 GB** unified memory,
  Metal 4, native arm64 (TD binary confirmed arm64, no Rosetta). macOS **26.5**
  (build 25F71).
- This is **officially supported** spec (Apple Silicon, no discrete-GPU or Rosetta
  caveats). *Default per the skill: use the generic 16.6ms/60fps doctrine — no
  below-spec budgets apply here.*

### GPU watchdog budget

Not stress-tested (no heavy feedback/blur scene pushed to failure this session — only
light verification ops). No Vulkan/Metal fatal-error dialogs occurred. On
officially-supported Apple Silicon the macOS GPU watchdog is far less likely to be the
binding constraint than it was on the old Intel Iris Plus machine; treat the old
machine's per-pixel/blur/feedback-resolution ceilings as **not applicable here** rather
than carrying them forward. If a scene ever produces a "Vulkan/Metal Device has
returned a fatal error" dialog on this machine, re-derive real budgets using the
skill's `debugging.md` recipe and record them here.

## TouchDesigner build

- **2025.33230** (`/Applications/TouchDesigner.app`), native arm64. Confirmed live via
  `app.build` and the bridge's `health` tool.
- POPs: **confirmed available** (`POP`, `boxPOP`, `circlePOP`, etc. all resolve) —
  unlike the old machine, no need to check `app.build` before reaching for them.
- `render` tool: **works correctly** on this build — tested end-to-end (glslTOP →
  MovieFileOut TOP, 30 frames captured cleanly at 30fps). The old build's
  `leadingzerosdigits` crash does **not** reproduce here.
  **Gotcha found on this machine**: since ffmpeg isn't installed yet (see Tools
  below), the final MP4 mux step fails and — because the code's cleanup only runs on
  the ffmpeg-success path — it **leaves stray `_mcp_movieout`/`_mcp_audioout`
  operators** in the project needing manual `.destroy()`. Re-test end-to-end once
  ffmpeg is installed and update this note.
- **Shader failures report as warnings, not errors, on this build.** A GLSL TOP that
  fails to compile leaves `errors()` empty and puts *"The GLSL Shader has compile
  errors (Use Info DAT to see details)"* in `warnings()`. Any verification sweep that
  only reads `errors()` will call a broken scene clean — this silently defeated the
  `run` tool's post-execution error detection until it was fixed (see below).
- GLSL TOP **Constants page is still broken on this build** — confirmed live: a plain
  `uniform float` wired via `const0name`/`const0value` produces solid black output.
  Unlike the old machine's report of a *silent* failure, this build does surface a
  `warnings()` message (`"Uniform 'X' is not assigned. Please assign it on the Colors
  or Vectors page."`) — but `.errors()` stays empty and the output is still dead, so
  the practical rule is unchanged: **never use the Constants page for scalar
  uniforms.** The Vectors-page workaround (`vec0name`/`vec0valuex..w`) was verified
  working (uniform float via `.x` component, correct pixel value observed).

## License

- **Non-commercial**: confirmed via user — same restriction as the old machine, GPU
  H.264/H.265 *encoding* is blocked (playback fine). Record with
  `videocodec='mpeg4'` + `audiocodec='mp3'`, or HAP for loops that play back in TD.
  Not yet directly re-tested end-to-end (blocked on ffmpeg being installed — see
  Tools below); re-verify the exact failure mode once ffmpeg is in place.

## Stability quirks (observed here)

- **Never restart the Web Server DAT from inside a request it is serving.** Calling
  `webserver.par.restart.pulse()` inside a `run` **killed TouchDesigner outright**
  here (`EXC_BREAKPOINT`/`SIGTRAP`, faulting thread in `libPocoNet` → `operator new`
  → `libsystem_malloc`): `.pulse()` fires synchronously and tears down the HTTP
  worker thread that is still executing the handler and building the response.
  Setting the parameter instead — the `set` tool with `{"restart": true}` — is safe,
  because a pulse par set to True is applied at the next frame boundary, after the
  response has been sent. Deploy handler source and restart as **two separate
  calls**, never one.
- **Main-thread wedge: now confirmed on this machine (2026-09-14).** After a long
  build session, a `run` that pulsed a custom parameter and then called
  `project.save()` in the same call never returned. The save itself *succeeded* (the
  `.toe` was written, correct size, correct timestamp) but no response came back, and
  every subsequent request timed out.
  Diagnosis afterwards: the TD process was **alive and healthy** — `STAT R`, 33-72%
  CPU, no new `.ips` crash log, and port 9988 still `LISTEN`ing — so this is the Web
  Server DAT's handler thread wedging, not a crash and not a deadlock of the whole
  app. `curl` against the raw endpoint hung identically (`HTTP 000`), which rules out
  the MCP client.
  Precautions that follow from it: **never combine `project.save()` with anything else
  in one `run`**, and save sparingly — the save is the one call here that reliably
  blocks the main thread for a long time. Nothing was lost because the `.toe` had been
  written; recovery is to restart TD and reopen the saved file.
  Still unconfirmed whether rapid `set`/`observe` bursts alone can cause it.
- **The wedge can be TRANSIENT — try again before restarting (observed 2026-09-18).**
  Building the `monsoon` scene, turning a container's node viewer on and then calling
  `health` (a project-wide sweep with profiling) produced the exact signature above:
  two MCP calls timed out, `curl` against the raw endpoint returned `HTTP 000` after a
  20 s timeout, and the process sat at **99.4% CPU**, `STAT R`, port 9988 still
  `LISTEN`ing, no `.ips` crash log. **It recovered on its own after roughly a minute**
  — the next `curl` answered `HTTP 200 in 0.012 s` and CPU fell to 59% — with no
  restart and no state lost. So the earlier entry's recovery advice ("restart TD and
  reopen the saved file") is the *last* resort, not the first: wait a minute and
  re-probe with `curl` first. Nothing here was saved to a `.toe` and nothing needed to
  be, because the scene rebuilds from its builder script in one call — which is the
  practical argument for the repo's "scenes must be rebuildable from code" rule.
- **Node viewers are not free.** With the network editor displaying a scene COMP's
  internals, TD pulls the node thumbnails and cooks the chain even when nothing else
  is: measured 30 of 54 ops cooking at ~5 Hz on a scene that was otherwise idle, versus
  1 op (a time-sliced timer CHOP) with viewers off. On a multi-scene switch rig, patch
  with the editor out of the tox or in Perform mode.
- Claude Code's MCP client connects to the bridge at session start. If TD wasn't up
  then, the tools stay missing for a while; the raw endpoint is still drivable with
  `curl` against `http://127.0.0.1:9988/mcp` (plain JSON-RPC) as a workaround, and the
  client did pick the tools up later in-session here.
- Crash logs land in `~/Library/Logs/DiagnosticReports/TouchDesigner-*.ips`. Parse the
  JSON body for `exception` + the faulting thread's frames — that named the POCO
  networking teardown above precisely. For GPU crashes, launch TD from a terminal to
  see native error lines the crash dialog hides.

## Tools present

- `toeexpand` / `toecollapse` present at
  `/Applications/TouchDesigner.app/Contents/MacOS/`.
- `ffmpeg`: **not installed**, and neither is Homebrew (confirmed absent from PATH,
  `/opt/homebrew`, and `/usr/local`). The bridge's `render` MP4 mux, GIF observe mode,
  and `ffprobe`-based recording verification all need it — `render` was confirmed to
  fail cleanly at just the mux step (see TouchDesigner build section above) with
  everything upstream of it working. Install with:
  `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && brew install ffmpeg`
  (run this yourself in a terminal — the Homebrew installer needs an interactive sudo
  password prompt, which an agent can't supply). Update this line once installed, and
  re-test `render` + the license codec fallback end-to-end.
