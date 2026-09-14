# TouchDesigner Reference

Sources: [Par Class](https://docs.derivative.ca/Par_Class), [Connector Class](https://docs.derivative.ca/Connector_Class), [Working with OPs in Python](https://docs.derivative.ca/Working_with_OPs_in_Python), [GLSL TOP](https://docs.derivative.ca/GLSL_TOP), [Introduction to Python Tutorial](https://docs.derivative.ca/Introduction_to_Python_Tutorial)

## Python API Essentials

### Operator References
```python
op('/project1/my_op')       # absolute path (always works from MCP)
root.op('child_name')       # relative to a container
root.children               # list all children
root.create(glslTOP, 'name') # create operator (returns reference)
my_op.destroy()              # delete operator
```

Always check existence before accessing: `if op('/project1/foo'):` — `op()` returns `None` for missing paths.

### Connecting Operators ([Connector Class](https://docs.derivative.ca/Connector_Class))

Connections go through `.inputConnectors` and `.outputConnectors`:

```python
# Connect output of noise1 to input 0 of lag1
op('noise1').outputConnectors[0].connect(op('lag1'))

# Connect to a specific input (e.g. 2nd input of composite)
op('src').outputConnectors[0].connect(op('comp').inputConnectors[1])

# Shorthand: connect input to a source op (replaces existing connection)
op('comp').inputConnectors[0].connect(op('src'))

# Disconnect
op('lag1').inputConnectors[0].disconnect()
```

**Input connectors replace** the existing connection. **Output connectors append** to the target.

**COMPs must be wired connector-to-connector**: with a COMP on either side, use
`a.outputConnectors[0].connect(b.inputConnectors[0])` — passing the COMP op itself
raises `tdError`. Wiring across different parents **silently no-ops**.

### Parameter Access ([Par Class](https://docs.derivative.ca/Par_Class))

| Access | Does | Use When |
|---|---|---|
| `par.x = 5` | Sets constant value | Static values |
| `par.x.expr = "..."` | Sets expression (auto-enters expression mode) | Dynamic/animated values |
| `par.x.val` | Get/set constant mode value only | You know it's constant mode |
| `par.x.eval()` | Get current value in any mode | Reading values safely |

Menu params accept names or indices: `par.operand = 'screen'` or `par.operand = 28`.

**Verified gotchas:**

- Assigning `.val` (or a bare constant) to a par in expression mode **silently kills the
  expression** — save and restore `.expr` around temporary overrides.
- A custom **menu** par referenced bare in an expression coerces to its menu *index*, and
  the target menu maps that index to the wrong entry (e.g. custom `'maximum'` →
  compositeTOP `'brightest'`). Write `parent().par.X.eval()` in menu-par expressions.
- In a parameter expression, relative `op('name')` resolves among the owner op's
  *siblings* — for a COMP's custom par, that means siblings of the COMP itself.

### Custom Parameters

`page.appendFloat(...)` returns a **ParGroup**, not a Par — set defaults/ranges on the
member: `p[0].default`, `p[0].normMin`, `p[0].normMax`, `p[0].val`.

### Resolution Management

TOPs inherit resolution from their first input. Problems happen at **chain roots** (TOPs with no input) and **feedbackTOPs** that haven't resolved yet. Set resolution explicitly on these:

```python
top.par.outputresolution = 'custom'   # override inheritance
top.par.resmult = False               # ignore global resolution multiplier
top.par.resolutionw = 1920
top.par.resolutionh = 1080
```

**Which TOPs need this:** feedbackTOP (defaults to 128x128), noiseTOP, constantTOP, glslTOP, renderTOP — any TOP at the start of a chain with no input. Mid-chain TOPs inherit correctly if wired after the source has its resolution set. If resolution is wrong after setting params, destroy and recreate the operator.

### Operator Paths
- Always absolute from MCP: `/project1/my_op`
- `me` refers to the script's owner operator (inside TD)
- `me.parent()` goes up one level
- `me.time.seconds` and `me.time.frame` for time values in expressions

### Walking the network — `findChildren`
- `findChildren()` — every descendant, any depth.
- `findChildren(maxDepth=N)` — down to N levels. **This is the one you usually want.**
- `findChildren(depth=N)` — operators at *exactly* depth N. A near-universal trap:
  `depth=5` on a normal shallow project returns an **empty list**, so a sweep built on
  it silently reports nothing wrong rather than failing loudly.
- Filter with `type=`/`name=` (e.g. `findChildren(type=glslTOP)`).

### Errors vs. warnings
`errors()` and `warnings()` are separate strings, and **which one a failure lands in is
not intuitive**: on 2025.x builds a GLSL shader that fails to compile populates only
`warnings()` and leaves `errors()` empty. Any health/verification sweep must check
both, or it will call a visibly broken scene clean.

## Commonly Used Operator Types

Type constants are Python globals in TD, not strings. Always verify with `docs(type='list_types', family=...)`.

### TOPs (Texture Operators)

| Type Constant | What It Does | Key Params |
|---|---|---|
| `glslTOP` | Custom shaders. Auto-creates `_pixel` DAT | `resolutionw/h`, `vec0name`, `vec0valuex/y/z/w` |
| `compositeTOP` | Blend two inputs | `operand` (menu: `screen`, `add`, `multiply`, `over`, etc.) |
| `feedbackTOP` | Feedback loop node | `top` = **loop end** (this is what feeds back — verified; the wired input is only the reset image), `resetpulse` |
| `transformTOP` | Translate/rotate/scale | `tx/ty`, `rotate`, `sx/sy`, `extend` |
| `levelTOP` | Brightness/gamma/contrast | `brightness1`, `gamma1`, `contrast`, `invert` |
| `hsvadjustTOP` | Hue/saturation/value | `hueoffset`, `saturationmult`, `valuemult` |
| `blurTOP` | Blur filter | `size` (filter size), `type` |
| `noiseTOP` | Procedural noise texture | `type`, `rough`, `exp` (exponent), `period`, `amp`, `offset`, `tx/ty/tz` (animate!) — for dark-background looks, drop `offset` negative (e.g. −0.25) so only noise peaks survive |
| `nullTOP` | Pass-through / output reference | (no special params) |
| `constantTOP` | Solid color | `colorr/g/b`, `alpha` |
| `renderTOP` | 3D render | `camera`, `geometry`, `lights`, `resolutionw/h` |
| `moviefileinTOP` | Load image/video | `file`; scrubbing: `playmode='specifyindex'` + drive `index` (see patterns.md CHOP idioms) |
| `depthTOP` | Depth image from a renderTOP | `top` (the render), depth space `camera` + far-distance tuned to scene → lumablur input 2 = pseudo-DOF |
| `reorderTOP` | Reassemble channels from 2 inputs | e.g. output alpha from input 2's luminance (attach alpha to a lookup color) |
| `rgbkeyTOP` | Key by color; default = solid black bg behind transparent renders | — |
| `fitTOP` | Fit/letterbox to a target resolution | `fit` (inside/outside) — square-fit dataset images before POP/particle use |
| `texture3dTOP` + `timemachineTOP` | Rolling N-frame cache + time-displaced readback | crossfade/melt between changing images for free (patterns.md recipe C) |
| `switchTOP` | Switch between inputs | `index` |
| `textTOP` | Render text | `text`, `fontsizex` |
| `cropTOP` | Crop region | `cropleft/right/top/bottom` |
| `rampTOP` | Color ramp/gradient | (various ramp params) |
| `displaceTOP` | Warp input 1 by vectors from input 2 | `displaceweightx/y`, `uvweight` |
| `lookupTOP` | Map input luminance through input-2 palette | (input 2 = rampTOP) |
| `lumablurTOP` | Blur amount driven by input-2 luminance (= glow) | `blackvalue`, `whitewidth` |
| `bloomTOP` | Physically-styled lens bloom (threshold+spread+rolloff in one op) | `intensity`, `threshold`-style pars — check `docs`, build-dependent |
| `thresholdTOP` | Binary cut by brightness | `threshold`, `comparator` (polarity is backwards-feeling — see debugging.md) |
| `edgeTOP` / `embossTOP` | Edge extract / relief map | `strength` / (emboss is neutral-gray on flat input — self-gating for composites) |
| `convolveTOP` | Custom kernel (sharpen/Laplacian) | kernel table, `scale` (decay knob in RD loops) |
| `cacheTOP` + `cacheselectTOP` | Frame history / delayed frame taps | `cachesize`; select `index` −1..−N |
| `analyzeTOP` | Reduce image to 1×1 stat (avg/min/max) | `op`, `analyzechannel` (use `rgbaverage`, see patterns.md) |
| `slopeTOP` | Per-pixel derivative (edge/motion energy) | — |
| `cornerpinTOP` | 4-point projection-region warp | corner pars |
| `resolutionTOP` | Explicit resize point in a chain | `resolutionw/h` — cheap place to downres before expensive ops |

### CHOPs (Channel Operators)

| Type Constant | What It Does | Key Params |
|---|---|---|
| `lfoCHOP` | Oscillator | `wavetype` (menu: `sin`, `tri`, `ramp`, `square`), `frequency`, `amp` |
| `noiseCHOP` | Procedural noise | `rough`, `period`, `amp`, `channelname` |
| `mathCHOP` | Range mapping / math | `gain`, `preoff`, `postoff`, `fromrange1/2`, `torange1/2` |
| `mergeCHOP` | Combine channels | (connect multiple inputs) |
| `constantCHOP` | Static values | `name0`, `value0` |
| `filterCHOP` | Smooth/lag values | `filter`, `width` |
| `selectCHOP` | Reference another CHOP | `chop` |
| `audiofilterCHOP` | Band filter for audio | `cutofflog` is **log10(Hz)**, range 0–4.5 (kick ≈ 2.2, highs ≈ 3.6) |
| `lagCHOP` | Asymmetric smoothing | `lag1` (attack) / `lag2` (release) — quick-to-rise, slow-to-forget signals |
| `limitCHOP` | Hard clamp | `min`, `max` — mathCHOP range-mapping does NOT clamp; put this after it |
| `resampleCHOP` | Rate conversion | timeslice on, rate 60 — **mandatory** after envelope on audio chains (patterns.md) |
| `envelopeCHOP` | Audio amplitude follower | `width` — output stays at audio rate until resampled |
| `speedCHOP` | Integrate a value over time | turns a level into an ever-advancing phase (smooth audio-driven rotation) |
| `triggerCHOP` | ADSR envelope from a gate | attack/decay/sustain/release — turns beat pulses into shaped envelopes |
| `beatCHOP` | Tempo-locked ramps/pulses | tap or lock to a BPM; steadier than raw kick detection for strobes |
| `timerCHOP` | Cue/sequence engine | `length`, `cyclelimit`, callbacks — the right tool for timed scene phases |
| `trailCHOP` | Rolling history plot | pair with performCHOP (`Frame time`/`GPU frame time`) for a live perf graph |
| `hogCHOP` | Deliberately burn CPU ms | the CPU-vs-GPU bottleneck test (debugging.md) |
| `logicCHOP` | Boolean shaping | channel pre-op `toggle` (flip state per pulse), "on when value changes" (count → pulse) |
| `countCHOP` | Count pulses | + limit `loop` 0..N = beat-driven switch index (patterns.md CHOP idioms) |
| `audiospectrumCHOP` | FFT of audio | → `choptoTOP` for spectrum-as-texture |
| `soptoCHOP` | SOP points → channels | Custom attribute scope (e.g. `life`) exposes per-particle data beyond P/N/V |
| `envelopeCHOP` ÷ trick | Self-normalizing signal | mathCHOP divide by own envelope (width ~10) → true 0..1 (patterns.md) |

### SOPs, MATs, COMPs

| Type Constant | What It Does |
|---|---|
| `gridSOP`, `sphereSOP`, `boxSOP`, `torusSOP` | Primitive geometry |
| `noiseSOP` | Deform geometry with noise |
| `pbrMAT`, `phongMAT`, `constantMAT` | Materials for 3D rendering |
| `geometryCOMP` | Contains SOPs for rendering |
| `cameraCOMP` | Camera for renderTOP |
| `lightCOMP` | Light for renderTOP |

## Pixel Formats (quality ↔ bandwidth lever)

Per [Pixel Formats](https://docs.derivative.ca/Pixel_Formats). Set via each TOP's Common page (`format` par). Format is inherited down a chain like resolution, so one explicit choice early usually covers the chain.

| Format | Bits/px | Use for |
|---|---|---|
| 8-bit fixed (default) | 32 | Final display output; most compositing. Values clamp 0..1, 256 steps |
| 16-bit float | 64 | Feedback loops that accumulate (avoids banding/quantize death), soft gradients, HDR-ish glow, signed data (optical flow) |
| 32-bit float | 128 | Data textures only: positions/velocities for GPU particles, timestamp textures. **No texture filtering** — forced nearest everywhere it's sampled |
| Mono / RG variants | 8–64 | Masks, motion maps, presence fields — a luminance mask does not need 4 channels; quarter the bandwidth |

Rules of thumb:
- Banding in a gradient or a feedback loop that "dies" to flat gray → bump that chain to 16-bit float, not 32.
- 32-bit only when values must survive exactly (a second-count, a particle position). Remember nearest-filtering: never put it mid-look-chain.
- Bandwidth cost is linear in bits × pixels — a 32f full-res texture costs 4× the default; combine with the resolution lever before blaming the GPU.

## CHOP Time Slicing

A *time slice* is the span since the last cooked frame ([Time Slicing](https://docs.derivative.ca/Time_Slicing)). Time-sliced CHOPs (flag on the Common page; audio/device CHOPs default on) cook every frame but process **all** samples since the last cook — so dropped frames don't lose audio energy or smoothing history. Consequences:

- Audio chains stay time-sliced end-to-end (the resampleCHOP in patterns.md has *timeslice on* for exactly this reason).
- A non-time-sliced CHOP mid-chain (e.g. a plain constant/merge arrangement) breaks the guarantee — values jump when frames drop.
- Time-sliced CHOPs recook every frame by design. Keep the chains short and low-channel-count; put a `nullCHOP` (cook type *Selective* on its Common page) at the end so unchanged data doesn't cook everything downstream.

## POPs — GPU geometry (builds ≥ 2025.30k)

The 2025 release added **POPs (Point Operators)**: a GPU-resident replacement for most SOP workflows — millions of points in real time, no CPU→GPU transfer per frame ([POP docs](https://docs.derivative.ca/POP), [Learning About POPs](https://docs.derivative.ca/Learning_About_POPs)). **Check availability first**: `run` → `app.build`, or `docs(type='list_types', family='POP')`. If present, prefer POPs over SOPs for anything with many points (particles, point clouds, instancing data). SOP knowledge still applies to old project files.

Core model: every POP is a list of **points with attributes** — `P` (position, float3), `N`, `Color` (float4), `Tex`, `PointScale`, plus custom ones (`Velocity`, `LineWidth`, …). Operators transform attributes; attributes are the currency.

Key operators (verify names via `docs` — the installed build may differ):

- **Generate:** `pointgeneratorPOP`, `gridPOP`, `spherePOP`/`boxPOP`/`torusPOP`, `pointfileinPOP` (point clouds), `randomPOP` (combine `set` + custom attr name = mint new random attributes, e.g. a `vel` float3)
- **Transform/math:** `transformPOP` (per-point via Map page), `mathPOP`, `noisePOP`, `normalizePOP`, `rerangePOP`, `limitPOP` (clamp = keep a sim inside a box), `mathmixPOP` (attribute algebra: `A+B` integrates vel into P, `mix A B C` blends two states by a third attribute, `length` builds a distance attr), `twistPOP`
- **Simulate:** `particlePOP` + `feedbackPOP` (force → velocity → position integration loop; set feedbackPOP's **memory limit** on merge-based loops or they grow unbounded), `glslPOP` (compute shader on attributes)
- **Structure:** `copyPOP` (instance geometry per point; Template Attributes page maps point attrs → `PointScale`, rotate-to, color), `linePOP`, `trailPOP` (per-point motion trails), `deletePOP` (by attribute compare, e.g. `len > 3` distance-cull; also random thinning), `sortPOP`, `groupPOP`, `mergePOP`
- **Interop:** `soptoPOP`, `choptoPOP`, `toptoPOP` (image → point cloud, no 4-channel limit), `lookuptexturePOP` (attribute → UV → Color), `poptoDAT`
- Built-in read-only attributes for free math: `_PointI`/`_PointU` (index / normalized 0–1), `_PrimI`, `_StepSeconds` — never allocated, always available.

Rendering: POPs go inside a `geometryCOMP` → MAT → `renderTOP`, same as SOPs. Points need Point primitives (generator `connectivity='point'`) to draw; `lineMAT` reads `LineWidth`, point sprites read `PointScale`, surface MATs read `Color`/`Tex` via the MAT's Attributes page.

Gotchas (from Derivative's docs):
- Middle-click info popups and `op.points('P')` **stall the GPU** (synchronous readback). In Python use `numPoints(delayed=True)` — 1 frame late but no stall.
- Feedback loops can over-allocate memory — set the feedbackPOP's allocation limit toggle.
- Attributes are referenced, not copied, downstream (`(r)` in info) — memory is cheaper than it looks; deleting attributes mid-chain rarely saves anything.

## L-Systems (lsystemSOP) — procedural plants

**Rules come from a DAT, not from parameters.** On 2025.33230 the SOP has no
`premise`/`rule1..N` params at all — only a `rules` param pointing at a DAT. The DAT is
a list of lines:

```
premise:FX
X=F-[[X]+X]+F[+FX]-X
F=FF
```

**There must be no space after `:` or `=`.** `premise: FX` produces zero geometry,
zero points, and an empty `errors()` — it fails completely silently. Optional
`context_ignore:` line for context-sensitive rules; rule syntax is
`[lc<]pred[>rc][:cond]=succ[:prob]`.

Turtle operators worth remembering: `F` forward drawing, `f` forward without drawing,
`+`/`-` turn, `&`/`^` pitch, `\`/`/` roll, `[`/`]` push/pop (branch), `~(n)` random
turn, `"`/`!` multiply length/thickness, `J K M` stamp the geometry wired into inputs
2/3/4 at the turtle. Full table in the offline help at
`/Applications/TouchDesigner.app/Contents/Resources/tfs/Samples/Learn/OfflineHelp/https.docs.derivative.ca/LSystem_SOP.htm`.

### Growing a plant on the music

`generations` is a **float**, so animating it grows the plant smoothly (with
`contangl`/`contlength` on, new segments extend from zero). Topology jumps at half
steps; the interpolation between them is what reads as growth.

Cost scales brutally with generations — measure before committing. Rule
`A=F[+A]F[-A]A` at `type='tube'`, rows 3 cols 5:

| Gens | points | cook |
|---|---|---|
| 4 | 2.5k | 0.6 ms |
| 5 | 7.7k | 0.9 ms |
| 6 | 23k | ~1.1 ms |
| 7 (rule D, 4-way) | 39k | 209 ms |

A plant whose `generations` stops changing stops re-cooking, so only the plant
currently growing costs anything.

### Shape gotchas

- The textbook bush `premise:FX / X=F-[[X]+X]+F[+FX]-X / F=FF` grows a **long bare
  stick** before it branches — measured zero horizontal spread across the bottom 30%
  of the plant. `F=FF` doubles the trunk every generation. For anything that should
  look like a plant rather than a tree, drop the `F=FF` rule:
  `premise:A / A=F[+A]F[-A]A` branches from the base up.
- `type='tube'` (lit, tapered stems) beats `type='skel'` for organic work — flat
  constant-width lines read as a wire mesh no matter what colour they are. Tubes need
  a lit MAT (phongMAT) plus a lightCOMP; a constantMAT throws the shading away.
- **`thickinit` is scaled by the step size, not by plant height.** Calibrate it by
  rendered silhouette coverage, not by eye on the parameter. For one plant filling
  ~⅓ of a 1280×720 frame at Gens 6: `0.02` → 0.7 % coverage (sub-pixel hairlines that
  rasterize to speckles), `0.06` → 4.6 %, `0.30` → 16 % (a solid blob).
- To read branch **tips** (to place flowers, fruit, instances), take the last vertex of
  each prim of a **skeleton** L-System: `prim[len(prim)-1].point.P`. Tube mode makes
  every tip a ring of duplicate points. Keep a second, static full-growth copy for
  this — a constant `generations` means the Script OP reading it cooks once instead of
  every frame.

## Python performance hierarchy (per [Derivative Optimize](https://docs.derivative.ca/Optimize))

Fastest to slowest ways to compute a per-frame value — always prefer the highest tier
that can express it:

1. **Optimized expressions** — parameter expressions marked "(Optimized)" in the docs
   (simple `op(...)['chan']`, `me.time.seconds`, arithmetic) are pre-compiled.
2. **A small CHOP/DAT network** — often **an order of magnitude faster** than the
   equivalent Python; this is why the recipes here shape signals in CHOPs and export,
   rather than computing in expressions.
3. **Unoptimized Python expressions** — any expression with function calls, conditionals,
   or attribute chains re-runs the interpreter every cook.
4. **Python in DATs every frame** (execute DATs on Frame Start) — the most expensive;
   profile with `time.perf_counter()` and cache anything reusable.

Related CPU rules: transforms belong at **object (COMP) level, not SOP level** — a
transformSOP moves every point on CPU, the geometryCOMP transform is free on GPU. Keep
op output *shapes* stable between cooks (tweaking values is fast; adding/removing
channels/rows/points re-allocates). `audioplayCHOP` loads whole files into RAM — use
`audiofileinCHOP` for long tracks.

## Script OPs (numpy in the network)

`scriptTOP` / `scriptCHOP` / `scriptDAT` run a callback DAT with a `onCook(scriptOp)`
hook — the bridge for OpenCV / numpy work inside the cook chain:

- `scriptOp.copyNumpyArray(arr)` — TOP wants HxWx3/4 (uint8 or float32); CHOP wants
  shape `(numChannels, numSamples)` float32.
- Any TOP → `top.numpyArray()`, any CHOP → `chop.numpyArray()` to read.
- A scriptTOP cooks on CPU every frame it's asked for — keep it off the per-frame
  chain unless it earns its cost (see Python hierarchy above); for pure-GPU math use a
  glslTOP instead.

### Instanced sprite gotchas (verified 2025.33230)

- Per-instance colour params are **`instancer` / `instanceg` / `instanceb` /
  `instancea`** — *not* `instancecolorr/g/b`. `instancecolormode` is
  `replace | multiply | add | subtract`, and it defaults to **`replace`**, which throws
  the texture away and paints flat quads. Use `multiply` to tint a sprite texture, and
  keep the texture near-neutral so the instance colour actually sets the hue.
- **rectangleSOP's `texture` toggle does not create a `uv` attribute** on this build.
  Without UVs the sprite renders untextured and the render TOP warns
  *"A MAT is using texture coordinates, but the POP/SOP ... does not have texture
  attributes."* Add a `textureSOP` with `type='rowcol'` after the rectangle.
- **constantMAT blends premultiplied by default** (`srcblend='one'`,
  `destblend='omsa'`). A sprite shader emitting straight alpha — `vec4(col, a)` —
  paints an opaque rectangle wherever alpha is 0. Emit `vec4(col * a, a)`.

## Engine COMP (process isolation, builds ≥2020)

`engineCOMP` runs a `.tox` in a **separate process** (TouchEngine) — a crash or a
100ms stall inside it cannot stutter the main render loop. Use for: heavy web/API work
(e.g. calls to image-generation APIs), expensive simulations, third-party components
you don't trust. Only TOP/CHOP/DAT inputs and outputs cross the boundary. Monitor via
its docked info CHOP (`Info Type = TouchEngine Status` → loading/running/error, or
`TouchEngine Perform` → its private fps). Costs: one extra process's RAM + a frame of
latency at the boundary.

## Perform mode

`ui.performMode = True` from `run` switches TD to perform mode (the network editor UI
stops rendering — it is itself a GPU/CPU cost); `False` returns to the editor. The MCP
bridge (WebServer DAT) keeps working either way. Final fps numbers quoted to the user
should be measured in perform mode — editor-mode fps understates real performance,
sometimes by a lot. Don't leave perform mode on during building (observe of
intermediate ops still works, but the user loses the editor).

## Video Codecs (moviefilein playback)

For image sequences/loops played back as textures: **HAP Q** decodes almost free (GPU-native layout, minimal CPU), at the cost of big files and 8-bit banding on soft gradients; **NotchLC** is higher quality (ProRes-4444-class, 10/12-bit) with moderate GPU cost; H.264/H.265 are small but seek badly and decode on CPU unless hw-accelerated ([codec guide](https://interactiveimmersive.io/blog/touchdesigner-lessons/codecs-for-touchdesigner-explained/)). On non-commercial licenses GPU H.264/HEVC *encode* is blocked (check `MACHINE.md` for this machine's license — record recipe in debugging.md); HAP encode via moviefileoutTOP works regardless and is the right target format for loops that will be played back in TD.

## Recipes

### GLSL Shader Pipeline

```python
root = op('/project1')
glsl = root.create(glslTOP, 'my_glsl')
glsl.par.resolutionw = 1920
glsl.par.resolutionh = 1080

out = root.create(nullTOP, 'out')
out.inputConnectors[0].connect(glsl)

# Write shader to auto-created pixel DAT
pixel_dat = root.op('my_glsl_pixel')
pixel_dat.text = """uniform vec4 uTime;
out vec4 fragColor;
void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = gl_FragCoord.xy / res;
    fragColor = vec4(uv, 0.5 + 0.5 * sin(uTime.x), 1.0);
}"""

# Wire time uniform manually
glsl.par.vec0name = 'uTime'
glsl.par.vec0valuex.expr = "me.time.seconds"
```

### Feedback Loop

**Semantics (verified live):** the feedbackTOP's `top` parameter (Target TOP) is what
gets grabbed at end-of-frame and fed back next frame; the **wired input is only the
image used on reset**. Wiring the loop end into the input with `top` unset produces a
dead loop — output frozen at the reset state, no errors reported. Every working
feedback network closes its loop this way.

```python
root = op('/project1')

# Seed content
seed = root.create(noiseTOP, 'fb_seed')
seed.par.resolutionw = 960
seed.par.resolutionh = 540

# Feedback — create early; INPUT = reset/initial image
feedback = root.create(feedbackTOP, 'fb_feedback')
feedback.inputConnectors[0].connect(seed)

# Processing chain off feedback output
transform = root.create(transformTOP, 'fb_transform')
transform.par.rotate.expr = "me.time.seconds * 2"
transform.par.sx = 0.99
transform.par.sy = 0.99
transform.inputConnectors[0].connect(feedback)

# Composite seed + feedback — 'over' decays; add/screen needs a decay stage
# (levelTOP opacity <1) in the loop or it washes to white
comp = root.create(compositeTOP, 'fb_comp')
comp.par.operand = 'over'
comp.inputConnectors[0].connect(seed)
comp.inputConnectors[1].connect(transform)

# Output
out = root.create(nullTOP, 'fb_out')
out.inputConnectors[0].connect(comp)

# Close the loop LAST — via Target TOP, then reset so it starts from the seed
feedback.par.top = comp.path
feedback.par.resetpulse.pulse()
```

### 3D Render Pipeline

```python
root = op('/project1')

geo = root.create(geometryCOMP, 'geo1')
torus = geo.create(torusSOP, 'torus1')
out_sop = geo.create(outSOP, 'out1')
out_sop.inputConnectors[0].connect(torus)

cam = root.create(cameraCOMP, 'cam1')
cam.par.tz = 5

light = root.create(lightCOMP, 'light1')

mat = root.create(pbrMAT, 'mat1')
geo.par.material = 'mat1'

render = root.create(renderTOP, 'render1')
render.par.camera = 'cam1'
render.par.geometry = 'geo1'
render.par.lights = 'light1'
render.par.outputresolution = 'custom'
render.par.resmult = False
render.par.resolutionw = 1920
render.par.resolutionh = 1080
```

**Key 3D param names** (use `docs` to verify):

| Operator | Params |
|---|---|
| renderTOP | `camera`, `geometry`, `lights`, `antialias`, `bgcolorr/g/b`, `cullface` |
| cameraCOMP | `tx/ty/tz`, `rx/ry/rz`, `fov`, `near`, `far` |
| lightCOMP | `tx/ty/tz`, `lighttype` (menu), `dimmer`, `lightcolorr/g/b` |

### Instanced 3D Scene

Use TD's native instancing on `geometryCOMP` for efficiently rendering many copies of the same geometry with different transforms/colors:

```python
root = op('/project1')

# Instance data — CHOP with channels named tx, ty, tz, sx, sy, sz, etc.
inst_data = root.create(constantCHOP, 'inst_data')
inst_data.par.name0 = 'tx'
inst_data.par.value0 = 0
inst_data.par.name1 = 'ty'
inst_data.par.value1 = 0
inst_data.par.name2 = 'tz'
inst_data.par.value2 = 0

# Geometry with instancing enabled
geo = root.create(geometryCOMP, 'geo_inst')
box = geo.create(boxSOP, 'box1')
out_sop = geo.create(outSOP, 'out1')
out_sop.inputConnectors[0].connect(box)

# Instance page params (on geometryCOMP, NOT renderTOP)
geo.par.instanceop = 'inst_data'
geo.par.instancetx = 'tx'
geo.par.instancety = 'ty'
geo.par.instancetz = 'tz'
# Optional: per-instance rotation and scale
# geo.par.instancerx = 'rx'
# geo.par.instancesx = 'sx'

# Optional: per-instance color
# geo.par.instancecolormode = 'instancecolor'
# geo.par.instancecolorr = 'cr'
# geo.par.instancecolorg = 'cg'
# geo.par.instancecolorb = 'cb'

mat = root.create(pbrMAT, 'mat_inst')
geo.par.material = 'mat_inst'

cam = root.create(cameraCOMP, 'cam_inst')
cam.par.tz = 10

light = root.create(lightCOMP, 'light_inst')

render = root.create(renderTOP, 'render_inst')
render.par.camera = 'cam_inst'
render.par.geometry = 'geo_inst'
render.par.lights = 'light_inst'
render.par.outputresolution = 'custom'
render.par.resmult = False
render.par.resolutionw = 1920
render.par.resolutionh = 1080
```

**Instance page params** are on `geometryCOMP` — use `docs(type='geometryCOMP', filter='instance')` to see them all. The CHOP must have one sample per instance with channel names matching what you set in `instancetx`, `instancety`, etc.

## GLSL in TouchDesigner

Per the [GLSL TOP docs](https://docs.derivative.ca/GLSL_TOP):

### How the GLSL TOP Works

- Creating a `glslTOP` named `my_glsl` auto-creates `my_glsl_pixel` (pixel shader DAT) and `my_glsl_compute` (compute shader DAT)
- Write your shader to the `_pixel` DAT's `.text` property
- Color output: declare `out vec4 fragColor;` (or any name with `layout(location = 0)`)
- TD prepends its own uniform/function declarations before your code — so `#extension` directives must go in the Preprocess Directives param (`predat`), not in the main shader

### Built-in Uniforms (always available)

- `uTDOutputInfo.res.zw` — output resolution (width, height)
- `gl_FragCoord.xy` — pixel coordinates
- `TDSimplexNoise()` — built-in noise function (Performance or Quality mode via `simplexnoise` param)

### Standard UV Patterns

```glsl
vec2 res = uTDOutputInfo.res.zw;
vec2 uv = gl_FragCoord.xy / res;                                    // 0..1
vec2 centered = (gl_FragCoord.xy - 0.5 * res) / min(res.x, res.y); // centered, aspect-correct
```

### Custom Uniforms — Wiring

Uniform types map to GLSL TOP parameter pages:

| GLSL Type | Param Page | Param Pattern |
|---|---|---|
| `uniform vec4 uFoo;` | Vectors | `vec0name='uFoo'`, `vec0valuex/y/z/w` |
| `uniform float uBar[N];` | Arrays | `array0name='uBar'`, `array0chop` (CHOP source) |
| `uniform mat4 uMat;` | Matrices | `matrix0name='uMat'`, `matrix0value` (CHOP) |
| `uniform vec4 uColor;` | Colors | `color0name='uColor'`, `color0rgbr/g/b`, `color0alpha` |

**Do not use the Constants page** (`const0name`/`const0value`) for scalar floats — broken
on some builds (see MACHINE.md): the shader silently fails to compile (checkerboard
fallback) with empty `.errors()`. Pack scalars into `vec4` groups on the Vectors page
(safe on every build); `glsl.par.vec = N` extends the number of vector groups.

Common wiring patterns:
```python
# Time
glsl.par.vec0name = 'uTime'
glsl.par.vec0valuex.expr = "me.time.seconds"

# CHOP channels
glsl.par.vec0name = 'uAudio'
glsl.par.vec0valuex.expr = "op('my_chop')['chan1']"

# Input textures: connect TOPs to GLSL inputs
# Access in shader as sTD2DInputs[0], or use sampler uniforms
```

### Debugging Shaders

- Use an **Info DAT** with its Operator param pointing at the GLSL TOP to see compile errors
- "Compiled Successfully" / "Linked Successfully" = no errors
- Unused uniforms are stripped by the compiler and won't appear in Load Uniform Names

### GPU Particle State (texture-as-memory)

The idiom behind particlesGpu and every custom GPU particle system: a shader invocation
sees only its own pixel/point — no neighbors, no previous frame. All state must arrive as
textures ([Intro to TD, GPU Particle Systems](https://nvoid.gitbooks.io/introduction-to-touchdesigner/content/GLSL/12-7-GPU-Particle-Systems.html)):

- Store positions in a TOP (one pixel = one particle, RGB = XYZ). **32-bit float format**, resolution = fixed max particle count — shaders cannot create points, so allocate the max up front.
- Persist across frames with the standard feedbackTOP loop (TD's replacement for ping-pong buffers): feedback → glslTOP (integrate velocity) → back into feedback.
- The GLSL TOP's **# of Color Buffers** param gives one shader multiple outputs (position buffer + velocity buffer + color buffer): `layout(location = 1) out vec4 velOut;` etc., pick them apart downstream with `renderselectTOP`.
- `normalize(vec3(0.))` is undefined — guard any normalize of a computed vector: `safeNorm(v) = length(v) > 0.0001 ? normalize(v) : vec3(0)`.
- Read the position texture on the render side via vertex-shader texture fetch or instancing (`instanceop` pointing at a `toptoCHOP`, or POPs' `toptoPOP` on 2025+ builds — the POP route skips the CPU hop entirely).

## Tool Cheat Sheet

| Goal | Tool |
|---|---|
| See what exists + positions | `map` (shows `@(x,y)` on every node) |
| Render MP4 video | `render` with `output` + `duration` (both required), optional `fps` and `audio_chop` for audio capture |
| Look up param names | `docs` with type constant |
| Find type constants | `docs` with `type='list_types'` |
| Create/wire operators | `create` (single op, requires `nodeX`/`nodeY`) or `run` (multi-op scripts) |
| Set params (validated) | `set` with `params` and/or `exprs` |
| Quick value check | `run` (expressions return values directly) |
| Read shader/script | `read` |
| Write shader/script | `write` |
| Tweak shader/script | `edit` |
| See visual output | `observe` (pass explicit `top` path; check `stats.verdict` — black/flat/transparent/static = dead chain) |
| Whole-project error sweep + hotspots + real fps | `health` (call twice ≥1s apart for fps) |
| Check operator state | `inspect` |
