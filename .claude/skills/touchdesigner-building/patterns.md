# Proven Visual Recipes (from real projects + studied tutorials)

Extracted from the author's reference projects (full networks documented in
`docs/network-notes/`),
plus techniques distilled from studied tutorial transcripts (elekktronaut, Interactive
& Immersive HQ, Derivative community). These established aesthetics come first —
reach for them before inventing new ones.

## Canonical two-band audio chain

Used identically in every audio project. Build:

```
audio → audiofilterCHOP lowpass  cutoff 700 Hz → envelopeCHOP (width .15) → resampleCHOP → mathCHOP (map to 0..0.7)      → filterCHOP width 0.1 → null_bass
      → audiofilterCHOP highpass cutoff 3 kHz  → envelopeCHOP (width .15) → resampleCHOP → mathCHOP (0..0.5 → 0.2..1)    → filterCHOP width 0.5 → null_highs
```

Fast smoothing (0.1) on bass for punch; slow (0.5) on highs for shimmer. Reference in
expressions as `op('null_bass')['chan1']`.

- **The resampleCHOP is mandatory, not stylistic.** envelopeCHOP output stays at
  44.1kHz; a filterCHOP after it convolves half a second of full-rate audio
  (~800ms/frame → 1fps project). Resample to control rate first (timeslice on, rate 60).
- `analyzeCHOP` rms of a *lagged* band never returns to 0 on sustained-bass material —
  gate beats off the pre-lag RMS.
- For quick tests, TD ships a techno track (the audiofileinCHOP default):
  `Samples/Audio/JeremyCaulfield_www.dumb-unit.com.mp3`.

## Exponential audio mapping (the "RD zoom")

Map levels multiplicatively, not additively — silence gives exactly 1.0 (no drift):

```python
transform.par.sx.expr = "100**op('null_bass')['chan1']"    # dramatic (levels ~0..0.05)
transform.par.sx.expr = "1.005**op('null_bass')['chan1']"  # subtle, feedback-safe
noise.par.gain.expr   = "10**op('null_bass')['chan1']"
```

Pick the base by how hot the channel runs: level 0.7 with base 100 = ×25 — usually too much;
use big bases only on channels mapped to ~0..0.1.

## CHOP idiom toolbox (audio/control signal shaping)

Small moves that solve most "make X react to Y" requests (distilled from elekktronaut's
audio-reactivity teaching — [Make Anything Audio Reactive](https://derivative.ca/community-post/tutorial/make-anything-audio-reactive/64122)):

- **Envelope-divide normalization** — divide a signal by its own envelope to get a true
  0..1 signal regardless of source loudness: `signal → mathCHOP(divide)`, input 2 =
  `envelopeCHOP` (width ~10) of the same signal. Also the fix for lagged values that no
  longer reach 1: normalize *after* the lagCHOP the same way.
- **Level → beat gate**: `triggerCHOP` with threshold 0.7–0.9 on an analyzed level gives
  a clean on/off per kick (works on kick-heavy material; for anything else build
  per-band kick/snare/hat detectors from the two-band chain above). Alternative one-liner: `limitCHOP` with
  quantize=floor.
- **Gate → toggle**: `logicCHOP` (channel pre-op `toggle`) flips 0↔1 on each beat —
  bounce a position/state between two values per kick, add a lagCHOP for a smooth glide.
- **Gate → cycling index**: `countCHOP` on the gate + limit `loop` 0..N drives a
  `switchTOP.index` — advance to the next scene/source on every beat. logic/count need a
  hard 0/1 input, not a smoothed level.
- **Beat-locked pulse**: `beatCHOP` outputs ramps/counts, not pulses — `logicCHOP`
  "on when value changes" converts its count into a per-beat pulse.
- **Level → scrub**: `speedCHOP` on a level turns loudness into an ever-advancing phase.
  Classic uses: noise `translate`/`tz` drift that only moves with the music, and video
  scrubbing — `moviefileinTOP` with `playmode='specifyindex'`, `index` driven by the
  speed output (map generously, e.g. ×10–100; add a constant base rate so it never
  fully freezes). High-fps source footage scrubs smoother.
- **Camera orbit for free**: a `nullCOMP` as the camera's `constraint`/look-at target;
  drive the null's `ry` with `absTime.frame` (constant orbit) or a speedCHOP output
  (orbits on the music). No manual tx/ty/tz math.
- **Looping travel in 3D**: instance `ty`/`tz` from a rampTOP/pattern sampled with a
  moving *phase* (speed-driven) — particles/instances stream forever without leaving
  bounds. Same idea as scrubbing, applied to position.
- **Spectrum as texture**: `audiospectrumCHOP → choptoTOP` (fit to square), optionally
  res-matched to a noiseTOP via its resolution reference — drives per-instance scale or
  displaces as an image. Blur it to de-jitter.

## Pseudo reaction-diffusion feedback (organic growth)

Blur diffuses, Laplacian sharpen re-concentrates → coral/fractal growth from any seed:

```
feedbackTOP (init: perlin noiseTOP, amp ~1.3, offset ~1)
→ transformTOP (exponential audio zoom, see above)
→ displaceTOP (source: animated noiseTOP or optical flow; displaceweight ~0.0001–0.001)
→ blurTOP (size ~11, extend repeat/mirror)
→ convolveTOP 3×3 kernel [-1 -1 -1 / -1 8 -1 / -1 -1 -1] added back to input (sharpen)
→ levelTOP opacity ~0.9965 (decay — mandatory in an add-based loop, see below)
→ null → (close loop: `fb.par.top = <this null>.path` — NOT the feedback's input,
   which is only the reset image; see SKILL.md feedback wiring)
```

- Animate the displacement noise: `tz.expr = "(absTime.seconds*0.05) - 0.15*(100**op('null_highs')['chan1'])"`.
- RD loops die (all black/white). Always wire `feedback.par.resetpulse` to something
  (mouse, beat gate) and reseed when observing a dead loop.
- Verified in the manuscript-bloom project: convolveTOP with a 3×3 center-9 kernel IS the
  sharpen; its `scale` par is the decay knob. Continuously stamping a seed
  texture (composite add) makes the loop self-healing, and
  `fb.par.reset.expr = "absTime.seconds % 40 < 0.15"` gives a birth→bloom→dissolve
  life cycle. A quotes tableDAT + `ink_text.par.text.expr` indexed by
  `int(absTime.seconds//40) % numRows` rotates the seed each cycle for free.
- **Feedback dynamics scale with fps.** Every per-frame constant (zoom base,
  displace weight, stamp opacity, convolve decay) is applied once per cook — at
  60fps the loop evolves 10–60× faster than on a project accidentally cooking at
  a few fps. Verify the project's real fps (frame-delta over wall clock) BEFORE
  tuning, or all constants will be an order of magnitude too hot. Verified 60fps
  starting points: zoom `1.015**bass`, displaceweight
  ~0.0001–0.0004, stamp opacity 0.004–0.03, decay 0.9965 (grow) / 0.999 (sustain).
- **A per-cook multiplicative decay is hard to verify through the MCP bridge**
  (pull-based cooking, see debugging.md — a feedback loop's actual cook count
  between two `observe` calls doesn't reliably match wall-clock time elapsed,
  especially across a slow back-and-forth debugging session). For a trail/
  linger effect that needs to be *correct* regardless of cook frequency, use
  a timestamp texture instead of a decaying one: a `feedbackTOP` under `max`
  that only ever stores `absTime.seconds` at each pixel's last "hit" (no
  decay math in the loop — just monotonic max), then compute the visible
  fade elsewhere as a pure function of `(absTime.seconds - storedTime)` via
  `subtractTOP` + a `levelTOP` range remap (inlow=0→outlow=1,
  inhigh=LINGER_SECONDS→outhigh=0, Post Clamp 0..1). This is exact no matter
  how many times the loop actually cooked in between — verified in the
  curator-hand installation's `motion_trail` after a naive per-cook decay
  (`levelTOP.brightness2` each cook) produced inconsistent, sometimes
  instant-to-black results when tested this way. Needs `format='rgba32float'`
  on the timestamp texture/feedback (8-bit fixed clamps to 0..1 and can't
  hold a real second count).
- mathCHOP range mapping does NOT clamp: input above `fromrange2` maps above
  `torange2` (a 1.75 came out of a 0.2–1 mapping). Clamp at the consumer with
  `min(op('x')['chan1'], 1)` or keep from-ranges generous.
- The convolve-sharpen kernel above sums to zero (pure high-pass) — its raw
  output alone is near-black. It must be composited (`add`) back onto the
  *blurred* image it was computed from, not fed downstream by itself, or the
  RD loop reads as faint edge lines on black (verified:
  `rd_blur → convolveTOP(rd_sharpen)`, then `compositeTOP add(rd_blur, rd_sharpen)`
  is what actually continues the loop).

## Presence-gated displacement (aware, not reactive)

Gate an RD loop's zoom/displace strength off a smoothed scalar "presence"
level instead of driving it continuously — reads as the piece noticing the
room, not a screensaver. Built for a Tagore/Sher-Gil
"Camera Motion as a Curator's Hand" installation:

```
motion_map (frame-difference chain, see above)
  → analyzeTOP (op=average, analyzechannel=rgbaverage) → 1x1 px avg brightness
  → toptoCHOP → mathCHOP (gain) → lagCHOP (~0.5-0.6s) → limitCHOP (clamp 0..1) → null 'presence_level'

rd_zoom.par.sx/sy.expr   = "1.0 + 0.003 + 0.02*op('presence_level')['r']"
rd_displace.par.displaceweightx/y.expr = "0.0001 + 0.0015*op('presence_level')['r']"
```

- Two channel-naming gotchas that silently evaluate to 0 instead of erroring
  loudly — verify with `inspect` before trusting an expression against
  either: `toptoCHOP`'s default output channel is named `r` (from its
  `r`/`g`/`b`/`a` pars), **not** `chan1`; and `analyzeTOP`'s
  `analyzechannel='luminance'` writes somewhere other than a reliably-readable
  channel downstream — use `analyzechannel='rgbaverage'` instead.
- A viewer's silhouette covers only a small fraction of the frame, so the
  raw frame-average is tiny (~0.01–0.05) even with clear, solid motion — it
  needs a `mathCHOP` gain (start around ×15-20) before it's a usable 0..1
  presence signal. mathCHOP range-mapping does not clamp (see above), so
  clamp the boosted value with a `limitCHOP` afterward.
- Don't gate the motion map itself by presence a second time before feeding
  it into the displace map — it's already near-black at rest (presence is
  *measured from* it), so multiplying it by presence again squares the
  suppression on top of the already presence-gated displaceweight, and the
  loop reads as inert even with strong motion. Pass the motion map through
  at full strength; let displaceweight alone control how much it warps.
- Crossfade the RD displace source between idle noise and the live motion
  map using two `levelTOP.par.brightness1` expressions (`1-presence` and
  `presence` on the *noise* branch only — not the motion branch, see above)
  feeding a `compositeTOP(add)` — cheaper and more controllable than a
  shader mix, and keeps "dormant" and "aware" as literally different signal
  sources rather than one attenuated signal.
- Expose a single master "Intensity" custom par on the container COMP
  (`comp.appendCustomPage(...).appendFloat(...)`) and multiply it into
  *both* halves of the pipeline — motion-extraction sensitivity (edge
  strength, motion boost, presence gain) and RD diffusion strength (zoom
  rate, displaceweight, blur size) — so one knob controls how alive the
  whole piece feels, not just how far it moves once triggered.
- Beyond warping (displaceTOP), a silhouette can also be *carved into* the
  image: `embossTOP` on the silhouette produces a relief map that's
  naturally neutral gray when the input is flat/black, so composited with
  `operand='hardlight'` onto the current frame it's a no-op at rest and
  visible relief only where the silhouette's edge is — no extra presence
  gating needed, same self-gating logic as above. Pair it with a second
  read of the same silhouette (`edgeTOP` → `blurTOP`, larger size, e.g. 30)
  composited `add` at low opacity (~0.1-0.2) for a soft diffusing outline
  glow. Inject both into the feedback loop (not just onto the final output)
  so the RD loop's own blur+sharpen keeps softening/spreading them across
  subsequent frames instead of leaving a static decal.
- To render a texture (not raw camera feed) as a GLSL particle mosaic
  where motion only affects particles *near* the affected area — not one
  global scalar moving every particle — sample the force field (motion
  map) *per particle*, at that particle's own home UV, inside the same
  neighbor-cell search loop used for the particle color (the
  hash2/baseCell/bestD pattern). Each
  particle then gets its own local motion reading: `localMotion =
  texture(sTD2DInputs[1], homeUV).r` scatters and shrinks that one
  particle, while a particle a few cells away with near-zero local motion
  stays put. This needs the force-field texture at the same resolution/
  alignment as the color source (reuse the already-fitted motion map, no
  separate resize) since it's being sampled at literal pixel UVs, not
  averaged into a scalar.
- Shrinking particle radius by local force (`r = radius * (1 -
  0.5*localMotion)`) alongside scattering them reads as the mosaic
  dissolving/diffusing apart in the affected region — dark gaps show
  through between particles — rather than just sliding a solid clump of
  particles sideways.

## Webcam motion detection (frame difference)

```
videodevinTOP → cacheTOP (cachesize ~11) → compositeTOP operand='difference'
                 (input 2: cacheselectTOP, cachetop=cache, index −1..−2)
→ levelTOP (brightness 2) → chromaTOP (valmin ~0.65, keys out sensor noise)
→ edgeTOP (strength 10) → blurTOP (20–120) → levelTOP (brightness 60, contrast 5)
```

More negative cacheselect index = compares further back = catches slower motion.
The final extreme boost (brightness ~60) is what turns faint diffs into solid shapes.

## Feedback trail flavors

| Flavor | comp operand | fed-back branch | Look |
|---|---|---|---|
| Spiral-out | over/add | transform rotate .01, sx/sy 1.02 | trails fly outward |
| Psychedelic invert | **difference** | + level opacity ~0.42 | self-cancelling, never blows out |
| Decaying | over | level opacity <1 | classic fading trail |

Additive/screen feedback with a never-black source washes to flat white over time —
steady-state gain is 1/(1−opacity), so 0.93 blows out and ~0.8 is stable. For a genuine
decaying trail use `over`, not `screen`/`add`.

## Optical flow as a force field

Port the ofxFlowTools optical-flow shader into a glslTOP (network documented in
`docs/network-notes/optical-flow-fractal.md`). Camera motion → displaceTOP
source or particle force. Key gotchas: input 0 = previous frame; output format must
be rgba32float (signed); downscale to ~600² + blur before analysis.

## particlesGpu (TD palette) audio-reactive setup

Drop the palette `particlesGpu` COMP instead of hand-building GPU particles. Proven
mapping (from `docs/network-notes/audio-reactive-particles.md`, 60k particles, preset 'Sand'):

```python
p = op('/project1/particlesGpu').par
p.Particles = 60000
p.Drag.expr       = "op('null_bass')['chan1']*1.2"
p.Turbtransx.expr = "op('null_highs')['chan1']"     # y/z at *0.2
p.Turbuperiod.expr = "op('slow_noise')['tP']*2"     # slow noiseCHOP wander (period ~7)
p.Reset.expr      = "op('mousein1')['lbutton']"
```

It has an `inOpticalFlow` input — combine with the optical flow recipe.

## Colorize + glow finishing chain

```
src → lookupTOP (input 2: rampTOP palette)        # luminance → palette color
    → lumablurTOP (input 2: rampTOP; blackvalue .011, whitewidth 35)   # blur amount by luminance = glow
    → levelTOP → null final_out
```

Variants on the glow stage:
- **Classic bloom** (when lumablur reads muddy): `thresholdTOP` (isolate brights) →
  `blurTOP` (wide, use Pre-Shrink) → `compositeTOP add` back over the source. Same
  physics as a camera lens; keeps blacks black where lumablur lifts them.
- `bloomTOP` / palette `bloom` COMP does threshold+spread+rolloff in one op on newer
  builds — check `docs` before hand-building.
- Feed the pre-glow chain 16-bit float so the blur has >1.0 highlights to spread —
  bloom computed on clamped 8-bit reads flat.

## Quality per unit of compute (the doctrine)

The levers, in order of how much quality they buy per ms spent — spend the frame
budget top-down:

1. **Motion quality beats pixel count.** A 960×540 chain at a locked 60fps reads
   *better* than 1920×1080 stuttering at 40. Simulate/feedback at half or quarter res,
   upscale near `final_out`, and recover apparent detail with a mild sharpen
   (convolveTOP) or the glow stage — projection surfaces and haze hide upscaling
   completely.
2. **Bit depth where it matters only.** 16f on feedback/gradient chains kills banding;
   everything after the final colorize can drop to 8-bit. 32f only for data (reference.md).
3. **Blur is the usual GPU hog.** Pre-Shrink or half-res the blur stage before touching
   anything else — wide blurs at full res are where frames die.
4. **One expensive idea per scene.** An RD loop *or* a particle field *or* a 3D render —
   composite cheap layers (ramps, noise, trails) around one hero system instead of
   stacking two simulations that each eat 8ms.
5. **Static = free.** Anything that doesn't change per frame (masks, palettes, seed
   textures, text stamps) should cook once: selective-cook nulls, locked ops, or baked
   to a file. The cook chain should contain only what moves.

## Aesthetic defaults (what "good" looks like here)

Taste anchors: Refik Anadol (data-as-material, particle fluids, architectural
mapping) and Max Cooper (mathematical processes made emotional, strobe/tunnel/feedback
vocabulary). Working rules distilled from the reference projects (`docs/network-notes/`):

- **Darkness is the canvas.** Every strong scene here idles near-black (negative noise
  `offset`, thresholded sources, `over`-feedback decay). Brightness is *spent* on the
  moment the audio or a viewer earns it — a scene that idles at 50% gray has nowhere
  to go.
- **Motion hierarchy: one slow, one fast.** A slow evolution nobody consciously notices
  (noise `tz` drift, 0.01 rotate, palette walk over minutes) under one fast reactive
  element (kick zoom, strobe, scatter). All-fast reads as noise; all-slow reads as a
  screensaver.
- **React multiplicatively, rest at identity.** The `100**level` idiom generalizes:
  silence must produce *exactly* the idle state (×1.0, +0.0), so reactivity never
  drifts the composition. Additive mappings accumulate error; exponential/multiplicative
  ones don't.
- **Smooth the data, not the visual.** lag/filter CHOPs on the analysis side (asymmetric
  attack/release) read as intentional; blurring a jittery visual reads as mud.
- **Palette discipline: 2–3 hues via lookupTOP ramps**, never per-op RGB fiddling. A
  ramp from near-black → deep hue → desaturated highlight is the house default; full
  rainbow = default-look alarm. Hue *shifts* (hsvadjust cycling) are cheap drama, but
  keep saturation and value anchored so the piece stays one material.
- **Finish every scene**: colorize → glow → subtle vignette/level. Raw operator output
  (esp. raw noiseTOP or raw render) is the "default TouchDesigner look" — the finishing
  chain is what makes it read as authored. ([context](https://interactiveimmersive.io/blog/touchdesigner-lessons/quick-touchdesigner-effects/))
- **Break symmetry once.** Perfect radial/grid symmetry reads as a demo; one asymmetric
  element (off-center seed, per-tile phase offsets) makes it art.

## Particle flow field (Refik-style fluid mass)

The core Anadol look is a particle mass advected by a smooth vector field, with trails.
Cheapest-to-richest ladder — pick by frame budget:

1. **Fake it in 2D (cheap, often enough):** the existing RD/displace stack — noiseTOP
   (or optical flow) as `displaceTOP` source over a feedback trail already reads as
   flowing material at a fraction of the cost. Add `lookupTOP` palette + glow.
2. **particlesGpu palette COMP** (see recipe above): turbulence pars ARE a flow field;
   drive `Turbtransx/y/z` slowly (noiseCHOP, period ~7) and keep audio on `Drag`/force
   so the mass breathes instead of exploding. 60k particles verified in the
   audio-reactive-particles reference network — scale the count to the GPU budget in `MACHINE.md`.
3. **Custom GLSL / POPs** (2025+ builds: `particlePOP` + `noisePOP` force + `feedbackPOP`)
   when per-particle rules matter (per-particle color from a data texture, localized
   forces like the presence-gated mosaic above). Curl-noise velocity (sample noise gradient,
   rotate 90°) gives the divergence-free "smoke" drift; plain noise velocity looks like
   static jitter.

Trails carry the look as much as particles: render into a decaying feedback loop
(`over` operand, decay ~0.9) so the mass leaves fading silk — bare points never read
as fluid. ([Derivative's Anadol tutorial pair](https://derivative.ca/community-post/tutorial/refik-anadol-particles-touchdesigner-part-one-tutorial/67084))

### Anadol recipe A — particleSOP turbulent mass (built-in ops, CPU)

From the I&I HQ Anadol two-parter (studied via transcript). Good when POPs are
unavailable and particle count is modest (~5–10k):

- **Emitter**: big `sphereSOP` (polygon, frequency ~12) → `transformSOP` (scale ~5, so
  particles spawn off-screen) → `deleteSOP` (bounding-volume, cut the region behind the
  camera so boxes never fly through the lens) → `pointSOP` re-writing normals ×(−0.5)
  (invert = particles fly *inward*; smaller magnitude = gentler initial velocity) →
  `sortSOP` (point sort `random` — birth order is spatial otherwise and reads as a scan
  pattern) → `particleSOP`.
- **particleSOP**: birth ~300/s, life ~25s, `turb` ~2 for the organic wander, limit
  planes at ±5 so escapees die instead of costing CPU. Input 4 = **surface attractor**:
  a small sphereSOP whose transform tx/ty/tz is driven by a 3-channel time-sliced
  noiseCHOP (period ~10; map tz range so the attractor never crosses the camera). The
  mass then chases a wandering invisible ball — this is most of the "alive" look.
  Pulse `resetpulse` after retuning; stuck particles are normal while editing.
- **Instancing**: `soptoCHOP` on the particle output → instance translate from `P0/P1/P2`
  and **rotate-to vector from `V0/V1/V2`** (Instance 2 page) so boxes bank into their
  direction of travel.
- **Per-particle age**: soptoCHOP with Custom attribute scope `life` → age drives alpha
  fade-in (map 0..life to −0.2..5, so opacity saturates early and never pops) and
  scale-out (map to 1..0 — dying particles shrink instead of blinking off). Reference
  the particleSOP's own `par.life` in the mathCHOP from-range so retuning life doesn't
  break the mapping.
- **Depth color**: soptoCHOP `tz` → normalize → `choptoTOP` → `lookupTOP` with a
  rampTOP palette → `reorderTOP` merges the alpha channel → instance Color OP (RGBA).
  Color-by-depth is a cheap stand-in for color-by-velocity and reads very Anadol.
- **Pseudo depth-of-field**: `depthTOP` off the renderTOP (`pixelformat` mono 8-bit,
  depth space = camera, far distance tuned to the scene ~4) → `lumablurTOP` input 2 —
  near boxes blur, far ones stay crisp. Finish with a circular-ramp vignette
  (`compositeTOP under`, mid-stop alpha 0, ease-in/ease-out interpolation).

### Anadol recipe B — POP particle system (2025+ builds, GPU, preferred)

From a studied POPs tutorial transcript; the modern replacement for recipe A and for
most particlesGpu uses. Core loop:

```
audio (or any CHOP) → choptoPOP (connectivity='point')       # emitter: fresh points each frame
→ particlePOP (max ~5–500k, birthrate ~100)
→ randomPOP: combine='set', new attr 'vel' (float3, tiny min/max ~±0.01)
→ mergePOP ← feedbackPOP                                      # fresh source stays OUTSIDE the loop
→ mathmixPOP: P = P + vel                                     # integrate
→ (forces: noisePOP, twistPOP, attractors…)
→ deletePOP (see length-cull below)
→ nullPOP 'end_feedback' → feedbackPOP.target                 # close loop
→ geometryCOMP (+ pointspriteMAT) → renderTOP → rgbkeyTOP (black bg) → bloom
```

- **Feedback hygiene**: set the feedbackPOP's *use memory limit* (max points ×
  multiplier) — a runaway merge loop grows unbounded otherwise. Wire a reset (keyboard/
  beat gate) to `resetpulse`; reset after every retune.
- **Length-cull instead of age-cull**: build `len = length(P - origin)` via mathmixPOP
  (create a float3 `origin` attr = 0, subtract, then the `length` operation) and
  `deletePOP` where `len > 3` — keeps the mass inside a sphere and self-refreshing.
- **Audio-gated turbulence**: mix straight motion and noisePOP with mathmixPOP's
  `mix A B C` operation where `C = len × audio_level` (via a mathPOP multiply whose
  factor is exported from the audio chain's low band) — quiet = laminar flow, loud = the outer
  shell boils first. Far cleaner than scaling noise amplitude globally.
- **Perpetual base motion**: a `twistPOP` inside the loop (or slow noisePOP `translate`
  driven by a speedCHOP on overall level) keeps the mass alive between hits.

### Anadol recipe C — image → POP data sculpture

For "data painting" looks (an image dataset melting into particles), from a studied
transcript ([video](https://www.youtube.com/watch?v=UhUXprR6qPs)):

- **Dataset player**: `folderDAT` → `moviefileinTOP` with
  `file` expr `op('folder')[int(op('idx')['chan1']) % (op('folder').numRows-1) + 1, 'path']`
  (the `int()` and the modulo both matter) → `fitTOP` to square.
- **Crossfade between images for free**: `texture3dTOP` (cache ~100 frames) +
  `timemachineTOP` — new stills melt into the mass instead of hard-cutting.
- **The melt**: `toptoPOP` → feedbackPOP loop where fresh image is mixed in at only
  1–10% per frame (`mathmixPOP` mix `P/in1P` ~0.01–0.1, and a second mathmixPOP mixing
  `Color` the same way) + `noisePOP` (translate4d drifting via `absTime.seconds*0.01`).
  Low mix = pure abstract flow; higher mix = image stays legible under distortion.
- **Render mass**: `copyPOP` stamping a small box per point, template attributes:
  `PointScale` from color luminance (`color.x * 0.1` via mathmixPOP `A*B`), rotate-to
  from the noise vector. `limitPOP` (clamp ±0.5 box) keeps everything inside a frame —
  display it inside a boxPOP wireframe "case" (deletePOP one face) for the gallery-vitrine look.
- **Wisps**: branch the point stream → `deletePOP` (thin random, keep a few %) →
  `trailPOP` (frames mode) → own geometryCOMP with pointspriteMAT — sparse trailing
  particles over the dense mass. Wire the same reset to the trail.

## TOP-only curl noise (divergence-free flow, no GLSL)

Curl of a noise field by finite differences, entirely in TOPs (studied transcript,
[video](https://www.youtube.com/watch?v=vYP8XWV2BFo)) — the cheap way to get the
"smoke drift" displacement source when a shader isn't warranted:

```
noiseTOP (32f, monochrome)                     # the potential field
├─ transformTOP tx=+step (extend mirror) ─┐
│                                          ├ compositeTOP subtract → (this is ∂/∂x)
├─ transformTOP ty=+step (extend mirror) ─┤
│                                          ├ compositeTOP subtract → mathTOP ×(−1)   (−∂/∂y)
└──────────────────────────────────────────┘
→ reorderTOP: pack one derivative into R, the other into B (green = 0)
→ limitTOP (normalize 0..1)  →  use as displaceTOP source (weight ~0.005, extend mirror)
```

`step` ≈ 0.01 of UV (a shared constant driving both transform offsets). Swirls appear
when this displaces a feedback loop; animate the source noise `tz` for evolution. This
is the upgrade path from "plain noise displacement" (jittery) to "fluid" without
touching GLSL or POPs.

## GLSL compute particles with curl noise (the full custom build)

When per-particle rules matter and POPs can't express them (studied transcript,
[video](https://www.youtube.com/watch?v=DkSwEY-m9GA)). Extends the texture-as-memory
idiom in reference.md:

- glslTOP `mode='compute'`, GLSL 4.30+; resolution N×N = max particles (64²≈4k,
  256²≈65k). Keep N in a constantCHOP and reference it from resolution *and* dispatch
  size (`N/8` with local size 8×8) so scaling up is one edit.
- Inputs: input0 = position feedback (`feedbackTOP` targeting the pos buffer's
  renderselect), input1 = velocity feedback, input2 = init noiseTOP (32f, amp 1,
  offset 0 — 8-bit init silently clips 3/4 of the cube to one quadrant). Outputs:
  `# of color buffers = 2`, `imageStore` pos → buffer0, vel → buffer1, split with
  `renderselectTOP`s.
- Physics: `vel += curl(pos*freq + t) * uDelta * strength; vel *= 0.96; pos += vel`.
  Pass `absTime.stepSeconds` as `uDelta` — frame-rate-independent forces. The damping
  constant (~0.96) is what keeps the mass from exploding.
- Curl function: Cabbibo's `glsl-curl-noise` pasted into the shader, with its `snoise`
  replaced by the simplex implementation from TD's own GLSL TOP help (Built-In
  Functions → Perlin and Simplex noise) — no external dependency.
- **Life cycle in spare channels**: pos.a = life. Decrement by a `uLifeDamping`
  (~0.005/frame); on expiry reset pos to the init texture's value and life to 1. Seed
  the init texture's *alpha* with random noise so births de-sync (constant alpha = the
  whole system blinks at once). vel.a = render size: `parabola(1-life)` (grow → full →
  shrink) so particles never pop in/out.
- Render side: instance translate from pos buffer RGB, **rotate-to** from vel buffer
  RGB, scale from vel.a — and set instance rotate order to **pre-rot**, the
  rotate-to glitches otherwise. Color via rampTOP indexed by life or speed.

## Strobe / tunnel vocabulary (Max Cooper-style)

From the strobe-tunnel and spectral-tunnel projects, generalized:

- **Tunnel = feedback + inward scale.** sx/sy slightly <1 with `over` decay pulls
  trails toward the vanishing point; slight rotate makes it helix. Kick-stamped rings
  become rushing walls.
- **Strobe on the beat gate, not the level** — a `triggerCHOP` (fast attack, ~80ms
  release) on the beat gives a shaped flash; raw level flicker reads as broken.
  Hard-cut strobes (switchTOP between scene and white/invert for 1–2 frames) are the
  Cooper move — use sparingly, gate by section.
- **Beat-locked > beat-detected for rhythm.** `beatCHOP` tapped/locked to the track's
  BPM gives ramps and pulses that never miss; reserve live detection (a beat gate
  off the bass band) for material you don't control.
- A `timerCHOP` sequencing 20–40s phases (build → peak → release, different par sets
  via preset interpolation) is what separates a *set* from a looping patch.
