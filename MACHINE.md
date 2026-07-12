# MACHINE.md — profile of the machine TD runs on

This file holds everything that is true of **one specific machine, TD build, and
license** — not of TouchDesigner in general. The agent reads it at session start
alongside CLAUDE.md and treats its budgets as hard constraints.

**This copy is both a working example and the template.** The values below were
verified on the original author's machine (a below-spec Intel MacBook — a usefully
extreme worst case). On *your* machine: keep the section headings, re-verify every
claim, and rewrite the values — the easiest way is to ask the agent to
"re-verify MACHINE.md on this machine and rewrite it". If this file is missing,
assume the defaults noted per section.

## Hardware / OS (verified 2026-07-12)

- MacBook with **Intel Iris Plus integrated GPU** (deviceID 0x8a53), **1536 MB** GPU
  memory, Metal 3 via MoltenVK 1.2.7. macOS **26.5.1**.
- This GPU is **officially below TD's supported spec** (Derivative: Intel GPUs are not
  supported on macOS; Intel Macs need discrete AMD). It works, but with the budgets
  below. *Default on other machines: any Apple Silicon or discrete GPU — ignore this
  section's budgets and use the generic 16.6ms doctrine in the skill.*

### GPU watchdog budget (the hard constraint)

macOS kills any GPU command buffer that runs ≈2s (`kIOAccelCommandBufferCallbackErrorTimeout`
→ `VK_ERROR_DEVICE_LOST` → TD's "Vulkan Device has returned a fatal error" dialog and
exit). **Opening a `.toe` cooks everything at once + compiles all shaders**, so a scene
that runs fine when built incrementally can be un-openable from disk. Verified budgets
for scenes that must survive first cook here:

- Per-pixel shader loops: ≤ radius 2 neighborhoods (9–25 iterations), not 3+ (49).
- blurTOP sizes ≤ ~30 at sim res, always with Pre-Shrink for anything wider.
- Simulation/feedback resolution ≤ ~640 wide.
- One heavy GLSL op per scene.

Diagnosis + `.toe` rescue recipe (toeexpand → patch → toecollapse): skill's
`debugging.md`, "Vulkan fatal error" row.

## TouchDesigner build

- **2023.12600** (`/Applications/TouchDesigner.app`).
- The bridge's `render` tool **crashes on this build** (`leadingzerosdigits` param
  missing). Use the manual moviefileoutTOP recipe in the skill's `debugging.md`.
  *Default elsewhere: try `render` first; fall back to the manual recipe.*
- The GLSL TOP **Constants page is broken on this build** (scalar uniforms silently
  fail to compile, checkerboard output, empty `.errors()`) — pack scalars into vec4s
  on the Vectors page. *Unverified on other builds; the Vectors-page habit is safe
  everywhere.*
- POPs: not available (needs ≥ 2025.30k). Check `app.build` before reaching for them.

## License

- **Non-commercial**: GPU H.264/H.265 *encoding* is blocked (playback fine). Record
  with `videocodec='mpeg4'` + `audiocodec='mp3'`, or HAP for loops that play back in
  TD. *Default on licensed machines: H.264 encode works.*

## Stability quirks (observed here)

- The bridge/TD main thread can **wedge** (MCP timeouts, TD ~80% CPU, health endpoint
  dead) after rapid set-params + observe bursts. Only recovery: force-quit TD. Keep
  scenes rebuildable from scripts.
- Crash logs land in `~/Library/Logs/DiagnosticReports/TouchDesigner-*.ips`. For GPU
  crashes, launch TD from a terminal — the `[mvk-error]` lines name the real failure
  the crash dialog hides.

## Tools present

- `ffmpeg` installed (used by the bridge's GIF observe mode and for verifying
  recordings with `ffprobe`).
- `toeexpand` / `toecollapse` at `/Applications/TouchDesigner.app/Contents/MacOS/`.
