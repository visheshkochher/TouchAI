# Debugging TouchDesigner Projects

## Quick Diagnosis

| Symptom | Likely Cause | Fix |
|---|---|---|
| Black screen | Shader compile error, missing connection, wrong resolution | `inspect` on the output chain — look for `errors` |
| Operator not found | Relative path used instead of absolute | Use `/project1/my_op`, not `my_op` |
| Param didn't take | Wrong parameter name | `inspect` to see current values, `docs` to get correct name |
| Expression error | String assigned to numeric par | Use `.expr = "..."` for expressions, not direct assignment |
| Uniform not working | Name mismatch or missing wiring | Check `vec0name` matches GLSL `uniform` declaration exactly |
| Feedback loop frozen / stuck at its seed image, no errors | `top` (Target TOP) not set — the wired input is only the reset image, it does NOT feed back | Set `fb.par.top = <loop-end>.path`, pulse `resetpulse` (see SKILL.md wiring order) |
| Feedback output evolves but ignores all processing in the loop | `top` points at the wrong op (e.g. the seed instead of the loop end) | Point `top` at the last op of the loop chain |
| Duplicate operators | Re-ran script without cleanup | Use `create` tool (auto-replaces), or add destroy loop in `run` scripts |
| Observe shows wrong output | Auto-detection grabbed wrong TOP | Pass explicit `top` path to `observe` |
| TOP stuck at 128x128 | Missing `outputresolution='custom'` or `resmult=False` | Set both + explicit `resolutionw/h`; destroy+recreate if stuck |
| Resolution smaller than expected | Global res multiplier active | Set `resmult=False` on the affected TOP |
| Instances not showing | Wrong `instanceop` path or missing channels | `inspect` geometryCOMP Instance page; verify CHOP has `tx`, `ty`, `tz` channels |
| Checkerboard output, `.errors()` empty | Scalar uniform on GLSL Constants page (broken on some builds — see MACHINE.md) | Move uniforms to the Vectors page as `vec4` groups (safe on every build) |
| `thresholdTOP` output looks inverted (dark where the source is bright) | `comparator` evaluates `threshold [op] value`, not `value [op] threshold` | Use `'less'`/`'lessorequal'` for "true where input is brighter than threshold", not `'greater'`/`'greaterorequal'` — verify visually with `observe`, the polarity is easy to get backwards |
| `op.sample()` returns stale/zero values right after a param or wiring change in the same `run` script | Same pull-based cooking as feedback trails (below) — `.sample()` doesn't force a fresh cook | Don't trust `.sample()` for "did this just take effect" checks; use `observe` on the actual TOP instead, in a separate call |
| Project at ~1fps, one op cooking 100s of ms | Full-rate audio CHOP chain, or a leftover moviefileoutTOP | Insert resampleCHOP (timeslice on, rate 60) after envelopeCHOP; destroy moviefileoutTOPs after recording |
| Feedback trails look like discrete ghost copies in `observe` | Pull-based cooking — only the observed chain cooks between snapshots | Normal; fine in live playback. See "Pull-based cooking" below |
| Feedback washes to flat white | Additive operand (`add`/`screen`) with a never-black source | Steady-state gain is 1/(1−opacity); use `over` for a true decaying trail, or opacity ≤ ~0.8 |
| Feedback loop's decay does nothing — brightness never falls even with `levelTOP.opacity < 1` | In an `ADD`-composited loop, `opacity` scales alpha, which `add` ignores entirely — RGB stays full strength forever | Decay ADD loops with `brightness2` (RGB multiplier), not `opacity`. Reserve `opacity` for `over`-composited loops |
| A near-black-but-opaque "fresh stamp" composited `over` a feedback loop erases existing detail everywhere, not just where the stamp is bright | `over` blends the stamp's *uniform* alpha across the whole frame regardless of its RGB content — a mostly-black stamp with alpha=1 still overwrites bright feedback pixels with near-black | Composite fresh per-frame content with `add` instead (only contributes where actually bright), or explicitly key the stamp's alpha to its own luminance before using `over` |
| Feedback zoom loop develops an expanding black (or single-color) hole at the transform's pivot, no errors | Continuous `scale > 1` on a feedback loop repeatedly re-samples an ever-shrinking crop around the pivot; whatever was there originally (often dark) self-reinforces forever since fresh content rarely reaches that few-pixel region | Periodically reseed: `fb.par.reset.expr = "absTime.seconds % N < 0.1"` (self-healing cycle) rather than trying to tune the zoom to never collapse |
| `lumablurTOP` throws "Not enough sources specified", no visual symptom otherwise | It needs **2 wired inputs** despite `widthchan` naming a channel of input1 — input2 isn't optional | Wire the same source into both inputs (`widthchan` then reads that channel from input2) |
| MCP timeouts, TD ~80% CPU, health endpoint dead | Bridge/TD main thread wedged (seen after rapid set+observe bursts) | Only recovery: user force-quits TD. Keep scenes rebuildable from scripts (network-as-code) |
| "Vulkan Device has returned a fatal error" dialog when *opening* a `.toe` (low-spec/below-spec GPUs — budgets in `MACHINE.md`) | **GPU watchdog timeout** — terminal launch shows `VK_TIMEOUT … kIOAccelCommandBufferCallbackErrorTimeout` then `VK_ERROR_DEVICE_LOST`: the load-time first cook (all ops at once + shader compiles) exceeds the OS's ~2s command-buffer watchdog. Heavy per-pixel shader loops and wide blurTOPs (size 100+) are the usual overload. (A crash-log SIGILL in libVIDEO is downstream fallout of the lost device, NOT the cause — verified by a webcam-bypassed copy crashing identically) | Scenes must fit the GPU *at load*, not just steady-state: keep shader loops small (search radius 1–2, not 3), blur sizes modest (use Pre-Shrink), sim res within the MACHINE.md budget. To rescue an existing `.toe`: `toeexpand` → edit the `_pixel.text` shader bounds / `.parm` blur sizes (binary-ish text; patch bytes) → `toecollapse` to a new file. Diagnose by launching TD from a terminal — the mvk-error lines name the real failure the crash dialog hides |
| Banding rings in gradients; feedback loop fades to a stuck flat gray | 8-bit quantization — small per-frame deltas round to zero | Set `format='rgba16float'` on the feedback/gradient chain (reference.md Pixel Formats) |
| Texture samples look blocky/pixelated only when a chain is 32-bit float | 32f disables texture filtering (forced nearest) everywhere it's sampled | Use 16-bit float for look chains; keep 32f for data textures only |
| Value jumps/steps in smoothed CHOP data when fps dips | Non-time-sliced CHOP in an audio/control chain drops samples | Turn on the Time Slice flag (Common page); keep audio chains time-sliced end-to-end |
| Instances twitch/glitch when combining rotate-to with per-instance scale | Instance rotate order | Set instance rotate order to `prerot` (Instance 2 page) |
| GPU-particle init loses ~3/4 of its volume (one quadrant only) | Init noise texture left at 8-bit — negative positions clipped to 0 | 32-bit float on the init texture (and amp 1 / offset 0 for signed range) |
| All GPU/POP particles die and respawn in sync (whole system blinks) | Constant birth alpha — every particle's life started equal | Seed the init texture's alpha with random noise so births de-sync |
| POP feedback loop's point count (and GPU memory) grows every frame | merge loop with no cap | Set the feedbackPOP's memory/point limit; add a distance- or age-based deletePOP in the loop |
| Whole net looks right but output fps quoted is low | Measuring in editor mode — network UI costs GPU/CPU | `ui.performMode = True`, re-measure, then back to `False` (reference.md) |

## Automated verification (cheap checks to run every build pass)

Codified from how mature TD-automation projects test networks — run these instead of
eyeballing only. **The bridge's `health` tool does #1 and #5 in one call** (error/warning
sweep + hotspot ranking + real fps between successive calls) and `observe` returns the
#2/#3 stats as `stats.verdict` automatically — the manual `run` versions below are the
fallback when driving an older bridge:

1. **Whole-project error sweep** (one `run` call, catches everything `inspect`-one-op
   misses — including ops you didn't touch that your change broke):
   ```python
   [(c.path, c.errors()) for c in op('/project1').findChildren() if c.errors()]
   ```
   Warnings too: `c.warnings()`. Empty list = clean. Run after every build/rewire pass.
2. **Image sanity check before trusting `observe`** — read the output's statistics and
   verdict it (an all-black, flat-gray, or fully-transparent frame means a dead chain
   even when nothing errors — feedback loops especially fail silently this way):
   ```python
   a = op('/project1/final_out').numpyArray()   # float32 HxWx4
   dict(mean=float(a.mean()), std=float(a.std()),
        amax=float(a[...,3].max()),
        verdict=('black' if a[...,:3].max()<0.02 else
                 'flat' if a[...,:3].std()<0.005 else
                 'transparent' if a[...,3].max()<0.02 else 'ok'))
   ```
   A 'flat'/'black' verdict + no errors = look for an unclosed feedback (`top` unset),
   a dead uniform, or an all-zero source. Then still `observe` — stats can't judge
   composition.
3. **Motion check** — two snapshots of the same numpyArray a second apart; if
   `abs(a2-a1).max() < 0.01` the scene is static (stuck timeline, dead expression, or
   frozen loop). Cheaper and more objective than comparing two observe images by eye.
4. **A `errorDAT`** in the project collects Python runtime errors network-wide
   (callbacks, expressions) — read it after exercising interactive logic; exceptions in
   callbacks otherwise vanish silently.
5. **Real fps + hotspot ranking** (see Profiling below) — always numbers, never vibes.
   Measure headline numbers with `ui.performMode = True` (reference.md): editor UI
   rendering understates real fps.

## Diagnosis Steps

### 1. Check for errors
```
inspect: path="/project1/my_op"
```
Look for `errors` and `warnings` fields in the response.

### 2. Verify connections
```
map: path="/project1"
```
Check that edges (connections) match your intended signal flow.

### 3. Check param values
```
run: code="op('/project1/my_op').par.rotate.val"
```
Verify the parameter actually has the value you set.

### 4. Check if expression is valid
```
run: code="op('/project1/my_op').par.rotate.expr"
```
Returns the expression string, or empty if none set.

### 5. Isolate shader errors
If a GLSL TOP has errors, read the pixel DAT to check the shader source:
```
read: path="/project1/my_glsl_pixel"
```
Then check the GLSL TOP for compile errors:
```
inspect: path="/project1/my_glsl"
```

## Common `run` Errors

- **`NameError: name 'glslTOP' is not defined`** — You're using a type constant that doesn't exist. Use `docs(type='list_types')` to find the correct name.
- **`TypeError: 'NoneType' object...`** — An `op()` call returned None. The operator doesn't exist at that path.
- **`AttributeError: ... has no attribute 'par'`** — You're calling `.par` on None. Check that the operator exists first.
- **`td.error: Can't set ... to string`** — You assigned a string to a numeric parameter. Use `.expr` instead.

## Recording Video (fallback when `render` is unavailable)

Check `MACHINE.md` first: on some build/license combinations the bridge's `render` tool
crashes (e.g. missing `leadingzerosdigits` param) and non-commercial licenses block GPU
H.264/H.265 encoding. Where either applies, record manually:

1. Create a `moviefileoutTOP`, wire the TOP to record into it.
2. Set `videocodec='mpeg4'` (CPU, works), `audiocodec='mp3'`, `audiochop=<path>`, `file=<output>.mp4`.
3. Pulse the audio CHOP's `cue` so the track starts from the top.
4. Set `record=True`, **return from `run` and wait realtime in the shell** (`time.sleep`
   inside `run` freezes cooking), then call `run` again to set `record=False`.
5. Verify audio with `ffprobe` (installed).
6. **Destroy the moviefileoutTOP** — left in the network it costs ~100s of ms per frame
   even when not recording.

## Observe Side Effects & Pull-Based Cooking

`observe` advances `me.time.frame` by several frames per captured frame. This is normally fine for visual work, but be aware if timeline position matters for your project logic.

Cooking is **pull-based**: while `observe` runs, only the observed TOP's chain cooks.
Trail/feedback CHOPs elsewhere hold stale data — feedback trails look like discrete ghost
copies in snapshots but are smooth in live playback. To verify a CHOP over time, hang a
`choptoTOP` off it and `observe` that; to verify trail pixels, read `top.numpyArray()`.

## Profiling

- Measure real fps via `absTime.frame` delta over wall-clock time — don't trust the
  timeline setting. Feedback dynamics are per-cook, so constants tuned at degraded fps
  are 10–60× too aggressive once the project actually runs at 60 (see patterns.md).
- `op.cookTime` is already in **milliseconds** — don't multiply by 1000. The first read
  after a rebuild can show a huge one-off spike from the initial cook; re-read a moment
  later for the steady-state number. Walk children's cookTime to find hotspots.
- Also available per-op from `run`: `op.gpuCookTime` (GPU ms), `op.cpuMemory` /
  `op.gpuMemory` (bytes). Sort children by these to rank hotspots in one pass:
  ```python
  sorted(((c.cookTime, c.gpuCookTime, c.path) for c in op('/project1').findChildren(depth=3)), reverse=True)[:10]
  ```

## Performance Triage (do this in order)

Budget: at 60fps everything — cook + render — must fit in **16.6ms**; at 30fps, 33ms.
Full background: [Derivative Optimize](https://docs.derivative.ca/Optimize).

1. **Measure real fps** (`absTime.frame` delta over wall clock, above). If it's at
   target, stop optimizing.
2. **CPU or GPU?** Two cheap experiments:
   - Halve the main chain's resolution (quarter the pixels). fps jumps → **GPU-bound**,
     almost always pixel-shader cost (blur sizes, feedback chains, resolution).
   - Or create a `hogCHOP` (burns CPU ms): fps drops further → **CPU-bound** (cooking,
     Python, audio chains, SOPs). fps unchanged → GPU-bound.
3. **GPU-bound fixes**, in order of payoff:
   - Drop resolution of the *processing* chain, not the output: run feedback/simulation
     at 640×360–960×540, upscale near `final_out` (a `resolutionTOP` + final sharpen
     reads nearly identical in motion — see "quality per watt" in patterns.md).
   - blurTOP cost scales with `size` — use **Pre-Shrink** (downres before blurring,
     ~5× cheaper for wide blurs) or `lumablurTOP` at reduced res.
   - Check pixel formats: a stray 32-bit-float chain quadruples bandwidth (reference.md).
   - renderTOP: fewer lights (cone > point in cost), turn off rim/advanced MAT features,
     back-face culling on, reduce antialias level.
4. **CPU-bound fixes**, in order of payoff:
   - Find per-frame Python: parameter expressions with function calls, executeDATs on
     Frame Start. Replace with CHOP references or expressions marked "(Optimized)" in
     the docs. A CHOP network is often 10× faster than the equivalent script.
   - Audio chains cooking at 44.1kHz (missing resampleCHOP — patterns.md).
   - SOPs deforming per frame = CPU. Move transforms to the geometryCOMP (object level,
     GPU) or instancing; on 2025+ builds convert the whole thing to POPs.
   - Anything cooking that doesn't change: put a **selective-cook nullCHOP** after it,
     move static branches upstream of animated ones, lock (`op.lock=True`) truly static
     generators (locking stores the data and stops upstream cooking).
5. **Verify the fix with numbers** — re-measure fps and re-read cookTime. Never trust
   "feels smoother" through the MCP bridge; pull-based cooking lies (below).

In the TD UI (tell the user if driving manually): Performance Monitor (alt+Y) shows one
frame's full cook list with ms per op; palette **Probe** overlays live CPU/GPU cost per
node over time. Both exist only interactively — from the bridge, use the cookTime/
gpuCookTime walk instead.
