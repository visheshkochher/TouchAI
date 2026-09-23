---
name: touchdesigner-building
description: Building TouchDesigner projects via MCP tools. Use when creating operators, writing shaders, wiring networks, setting parameters, or debugging TD projects. Covers correct parameter names, GLSL workflow, feedback loops, and the iterative observe loop.
---

# Building in TouchDesigner via MCP

## The Build Loop

Every TD task follows this cycle:

1. **Orient** — `map` to see what exists and where (shows `@(x,y)` coordinates on every node)
2. **Look up** — `docs` for every operator type BEFORE creating it
3. **Build** — `create` for operators (requires `nodeX`/`nodeY` — read positions from `map` and place nearby), or `run` for complex multi-op scripts
4. **Verify** — `health` (whole-project error sweep + hotspots + real fps), then
   `observe` with explicit `top` path: check its `stats.verdict`
   (black/flat/transparent/static = dead chain, see debugging.md "Automated
   verification") AND judge the image
5. **Refine** — `edit` for shader tweaks, `set` for param changes (validates names, handles expressions)
6. Repeat 4-5 until it looks right; before declaring done, measure real fps (perform
   mode for headline numbers) and run the motion check on anything that should animate
7. **Long-run audit** — no per-frame growth anywhere (see "Nothing may grow per frame"
   below), then a quiet RSS slope over 7+ minutes with the story looping. Record the
   number in the README.

## Hard Rules

### Always call `docs` before creating operators

TD parameter names are abbreviated and non-obvious. Guessing causes silent failures.

**Examples of wrong guesses:**

| You'd guess | Actual name | Operator |
|---|---|---|
| `roughness` | `rough` | noiseCHOP/TOP |
| `type` (for waveform) | `wavetype` | lfoCHOP |
| `saturation` | `saturationmult` | hsvadjustTOP |
| `hue` | `hueoffset` | hsvadjustTOP |
| `mode` / `blend` | `operand` | compositeTOP |
| `brightness` | `brightness1` | levelTOP |
| `radius` / `filtersize` | `size` | blurTOP |
| `harmonics` | `harmon` | noiseCHOP/TOP |
| `multiply` | `gain` | mathCHOP |
| `rotation` | `rotate` (transformTOP) but `r` (compositeTOP) | varies |

Use `docs(type='list_types', family='TOP')` to find type constants before `root.create()`.

### Parameters: `.val` vs `.eval()` vs `.expr`

TD's Par class has three distinct access modes ([Par Class docs](https://docs.derivative.ca/Par_Class)):

- `.val` — get/set the **constant mode** value only (ignores expressions/exports)
- `.eval()` — returns the **current working value** regardless of mode (always safe to read)
- `.expr` — get/set the expression string; setting this puts the param into expression mode

```python
# Static value → assign directly (sets constant mode)
op.par.frequency = 0.5

# Dynamic/time-based → use .expr (switches to expression mode)
op.par.rotate.expr = "me.time.seconds * 1.5"

# WRONG — string to numeric par → ERROR
op.par.rotate = "me.time.seconds * 1.5"

# Reading values: .eval() is always correct
current = op('/project1/my_op').par.rotate.eval()  # works in any mode
```

**Gotcha:** `par.x` returns a parameter *object*, not a number. When passing to Python functions that need actual numbers, use `.eval()`:
```python
round(op('geo1').par.tx.eval(), 2)  # correct
round(op('geo1').par.tx, 2)         # may error in some contexts
```

### GLSL uniform wiring

Per the [GLSL TOP docs](https://docs.derivative.ca/GLSL_TOP), the "Load Uniform Names" button pre-fills uniform params from shader declarations — but the compiler strips unused uniforms, and pulsing from scripts is unreliable. Wire uniforms manually via the Vectors page:

```python
glsl.par.vec0name = 'uTime'
glsl.par.vec0valuex.expr = "me.time.seconds"
```

For multi-value uniforms from CHOPs:
```python
glsl.par.vec0name = 'uParams'
glsl.par.vec0valuex.expr = "op('my_chop')['chan1']"
glsl.par.vec0valuey.expr = "op('my_chop')['chan2']"
```

**Gotcha (build-dependent — see MACHINE.md):** the **Constants** sequence page (`const0name`/`const0value`) for scalar float uniforms is broken on some builds — the shader silently fails to compile (checkerboard fallback pattern) while `.errors()` stays empty. Pack scalar uniforms into `vec4` groups on the Vectors page instead (`glsl.par.vec = N` adds more groups) — safe everywhere.

**Gotcha:** The uniform name in `vec0name` must exactly match the GLSL `uniform` declaration. GLSL types map to pages: `vec4` → Vectors, `float[N]` → Arrays, `mat4` → Matrices. Use `#extension` directives via the Preprocess Directives param (`predat`), not inline in the pixel shader — TD prepends its own declarations before your code.

### Bridge tool call signatures (verified against the vendored bridge)

- `create` takes `parent` + `name` (not `path`).
- `wire` needs explicit `to_input` for fan-ins — omit it and input indices auto-increment, which mis-wires multi-input ops.
- `observe` takes `top` (not `path`). Each snapshot advances the timeline.
- `set` validates menu values and returns the valid list on error — trust it
  (e.g. analyzeCHOP `function='rmspower'`, mathCHOP `chopop='avg'`).

### Always pass explicit `top` path to `observe`

Auto-detection only finds ops named `out`, `out1`, `render`, `comp`, `null1`. Real projects use custom names — always specify the path.

### `run` rules

- `run` executes on TD's **main thread** — `time.sleep` inside it freezes cooking.
  For realtime waits (e.g. recording), return from `run`, wait in the shell, then call `run` again.
- Executing a script file's source via `run`: plain `exec(code)` breaks any function
  the script defines (exec locals scoping). Always `g = dict(globals()); exec(code, g)`.

### Clean up before re-running

The `create` tool handles this automatically (destroy-before-create). But when using `run` for multi-op scripts, add cleanup to prevent duplicates (`glsl_main1`, `glsl_main2`):

```python
for name in ['my_glsl', 'my_glsl_pixel', 'my_out']:
    o = root.op(name)
    if o: o.destroy()
```

### Recording video — check MACHINE.md before using `render`

On some build/license combinations (see `MACHINE.md`) the bridge's `render` tool
crashes and/or GPU H.264/H.265 encoding is license-blocked. Where either applies,
record manually with a `moviefileoutTOP`: `videocodec='mpeg4'` (CPU, works),
`audiocodec='mp3'`, set `audiochop`, pulse the audio's `cue`, toggle `record` on →
wait realtime **in the shell** (not `time.sleep` in `run`) → toggle off. Verify audio
with `ffprobe`.
Full recipe in [debugging.md](debugging.md). **Destroy the moviefileoutTOP when done** —
left in the network it costs ~100s of ms per frame even after recording.

### Resolution management

TOPs inherit resolution from their first input. Problems happen when a TOP has no input or its input hasn't resolved yet:

- **feedbackTOP** defaults to 128x128 when created without an input — always set `outputresolution='custom'`, `resmult=False`, and explicit `resolutionw/h` on it
- **Chain roots** (any TOP with no input: noiseTOP, constantTOP, glslTOP, renderTOP) should have explicit resolution set
- **Mid-chain TOPs** generally inherit correctly if wired after the source has its resolution set
- If resolution is wrong after setting params, destroy and recreate the operator

### 3D instancing basics

Instance params live on `geometryCOMP`, not `renderTOP`:

- Use `docs(type='geometryCOMP', filter='instance')` to look up Instance page params
- Instance data comes from a CHOP with channels named `tx`, `ty`, `tz`, `rx`, `ry`, `rz`, `sx`, `sy`, `sz`, etc.
- Set `instanceop` on the geometryCOMP to point at the CHOP path
- Per-instance color via `instancecolormode`, `instancecolorr/g/b`
- See [reference.md](reference.md) for the full instancing recipe

### Feedback loop wiring (verified — the input does NOT close the loop)

feedbackTOP semantics: the **Target TOP parameter (`top`)** is what gets grabbed at
end-of-frame and fed back; the **wired input is only the reset/initial image**. Wiring
the loop end into the input with `top` unset leaves the loop dead — output stuck at its
reset state forever, with no errors (this made an entire scene motion-blind once).

1. Create the feedback TOP early; wire its **input to the seed/reset image**
2. Wire its OUTPUT into the processing chain
3. Close the loop LAST by setting **`fb.par.top = <loop-end op>.path`**
4. Pulse `resetpulse` after (re)wiring so it starts from the seed
5. A pure-additive loop (add/screen composites, sharpen-add) needs a decay element
   (levelTOP opacity <1, e.g. 0.9965) or it washes to white — steady state is
   stamp/(1−decay) (see patterns.md)

### Performance budget

At 60fps the whole frame — cook + render — has **16.6ms**. Before optimizing anything,
measure real fps (`absTime.frame` delta over wall clock) and rank hotspots by
`cookTime`/`gpuCookTime`. Then follow the triage order in [debugging.md](debugging.md)
(resolution-halving test for GPU-bound, hogCHOP test for CPU-bound) and the
"quality per unit of compute" ladder in [patterns.md](patterns.md) — motion smoothness
beats pixel count; simulate at half res and upscale near `final_out`.

### Pixel format is a real parameter

Feedback loops and gradients band/die at the default 8-bit — use `format='rgba16float'`
on those chains. 32-bit float **disables texture filtering**; reserve it for data
textures (particle positions, timestamps). Details in [reference.md](reference.md).

### POPs (2025+ builds)

If `app.build` ≥ 2025.30k, the GPU **POP** operator family exists — prefer it over SOPs
for particles, point clouds, and anything with many points. Check with
`docs(type='list_types', family='POP')`; overview + gotchas in [reference.md](reference.md).

### Nothing may grow per frame (scenes run for hours)

Assume every scene will run unattended all night. Every per-frame code path must be
bounded:

- **Script OPs: build channels, rows or points once, then only write values.**
  `scriptOp.clear()` + `appendChan()` in every `onCook` leaks native memory inside
  TouchDesigner. It was measured at ~2 MB/min (~760 MB over six hours) while Python's
  object count and `gpuMemory` both stayed flat. Track "built" in Python state, because
  `numChans` cannot be read inside a cook. The pattern is in
  [debugging.md](debugging.md).
- **Every list that gains entries** (particles, events, history) gets a hard length cap
  **and** an age expiry.
- **Every integrated phase** (flow, travel, spin, a shader clock) is wrapped or reset
  at a loop seam. Feed shaders story time, never raw `absTime`.
- **An unattended story loops** through a fade, rather than clamping on its last frame.

Before calling a scene done, and when auditing an existing one, run the **long-run
memory audit** in [debugging.md](debugging.md): a grep for appends, then a quiet RSS
slope measured from outside TouchDesigner, then a bisection if it grows. Python's
object count alone cannot see the worst leak.

### Prefer CHOP networks over per-frame Python

Derivative's own ranking (reference.md "Python performance hierarchy"): optimized
expressions > a small CHOP network (often **10× faster** than Python) > unoptimized
expressions > per-frame scripts. Shape signals in CHOPs, export/reference the result;
keep expressions to simple `op(...)['chan']` arithmetic. Transforms go at COMP level,
not transformSOP.

## Reference

- Common operator types, pixel formats, time slicing, POPs, Python performance
  hierarchy, Script OPs (numpy), engine COMP, perform mode, GLSL patterns, codecs:
  [reference.md](reference.md)
- Debugging common failures, **automated verification** (error sweep, image sanity
  verdicts, motion check) + the performance triage workflow: [debugging.md](debugging.md)
- **Proven visual recipes from real projects and studied tutorials** (audio
  chains, CHOP idiom toolbox, reaction-diffusion feedback, motion detection, optical
  flow, particlesGpu, three Anadol particle recipes — particleSOP / POP / image-POP —
  TOP-only curl noise, GLSL compute particles) plus aesthetic defaults,
  quality-per-compute doctrine, flow-field and strobe/tunnel vocabulary:
  [patterns.md](patterns.md) — check here first when asked for audio-reactive or
  camera-reactive visuals, and before declaring any visual "done"
