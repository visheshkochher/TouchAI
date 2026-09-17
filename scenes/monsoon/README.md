# Monsoon

A harmonium on a street corner, the rain that arrives halfway through, and everyone
who walks past without stopping.

A fixed camera on one corner. The first third is dry: he is already playing, the
evening crowd is already going home, and the wind gets up. Then it starts, and by the
time the sky opens he has been out in it for two chapters and has not moved.

**And one by one, people stop walking.** Each new listener peels off the pavement on
an accented kick and takes a place at his side, so the crowd that gathers is built by
the track rather than by a timer. By chapter 7 he is playing to a small silent group
in the rain; by chapter 8 they have gone.

Build:

```python
code = open('scenes/monsoon/build.py', encoding='utf-8').read()
g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
```

Idempotent — destroys and recreates `/project1/monsoon` and `/project1/monsoon_out`,
and touches nothing else. No media files.

## Keys

| key | does |
|---|---|
| 1-8 | walk the story to a chapter |
| 0 | restart |
| t | **THUNDER** — open the sky |
| p | **PASSER-BY** — send someone across now |
| s | **SOMEONE STOPS** — the next person to reach him stops, listens, and gives |
| n | **RESEED** — a new street and a new crowd |

## Drawn flat, and it is one primitive

Everything is a **filled shape with a hard shadow side and a bold outline** — flat
colour blocked in, no gradient inside a shape, one light source, strong silhouettes.

And every filled shape and every outline in the scene is the **same instance**: one
unit quad with a per-instance width.

```
an OUTLINE  a quad 3 px wide along the edge
a LIMB      one fat quad from joint to joint
a FILL      a stack of horizontal quads scanned across a convex outline
a WINDOW    one quad
a BUILDING  one quad
```

Swapping the unit *line* for a unit *quad* and adding one channel (`sx` = width) is
the entire change from wireframe to flat cel. It needed no second render pass, no
second material, no triangulator, and no extra memory — a hairline and a solid block
of colour cost exactly the same and come out of the same pool.

The one light source is his own lamp, so every shape gets a LIT value on the lamp
side and a SHADOW value on the other with a hard edge between them and nothing in
between. That hard edge is the whole difference between a flat cel and a coloured-in
wireframe.

**The colour is the story.** The world is blue, the air is purple, and the only red
in the frame is him. Anyone who passes close enough picks up his lamp on the side
facing him and loses it again on the way out — `exp(-(dist/0.62)²) * 0.72`, one
expression. Someone who *stops* keeps it. On a thunderclap the city goes dark against
a lit sky while he stays warm, because his light is the only one in the scene that is
not the weather.

## The weather is an arc, not a level

| # | chapter | weather | watching |
|---|---|---|---|
| 1 | The Street | **dry**, still, a few people | 0 |
| 2 | Evening Crowd | **dry**, the pavement is busy | 0 |
| 3 | The Wind Gets Up | **dry**, wind at 0.72 — the only warning | 0–1 |
| 4 | It Starts to Rain | first drops; umbrellas go up | 1–2 |
| 5 | Steady Rain | a drizzle that has settled in | 2–4 |
| 6 | **Thunder** | the sky opens; heaviest rain | 4 |
| 7 | Someone Stops | it eases | **5** |
| 8 | It Eases | last drops, purple afterlight | drains to 0 |

`ARC_THUN` is **exactly zero before chapter 6**, so lightning cannot leak early no
matter what the bass does. Rain is 0.00 for the first two chapters and 0.02 in the
third. Endpoints match, so the wrapping clock has no seam.

The umbrellas only go up once it is actually raining (`smoothstep(0.10, 0.30, rain)`).
Six people holding umbrellas open on a dry evening is the fastest possible way to
tell an audience that the weather is a parameter and not a story.

## Audio: the weather moves on weather time

Rain used to swing ±28% with the energy of the track, which made the downpour pump on
the beat like a compressor and left nothing else in the frame doing anything. **It
rides the audio by 6% now** (and `Rain rides Audio` turns even that down). What the
music drives instead is everything that is *alive*:

| signal | drives |
|---|---|
| tempo | **the bellows** — he pumps once every two beats, phase-locked to the grid |
| accented kick | **a new listener stops**; a ring on a puddle |
| kick | **the sky glows**; ~45% of the windows shine; the lamp, his shoulders |
| bass **drop** | **starts the rain** (chapter 4 window); fires the lightning (from 6) |
| energy | the drone bands rising off the harmonium |
| highs | **the lit windows** flicker; rain landing on his head and shoulders |
| bass | wind, and the haze on the road |

**The flash and the afterglow are two different clocks.** The strike is gone in a
tenth of a second; the violet it leaves in the air takes a second and a half. One
envelope cannot be both, and using one is what makes stage lightning look like a
dimmer.

### The story itself runs on the music

Decoration reacting to audio is not the same as a story reacting to audio, and the
first pass only had the former. Three of the piece's actual events are now the
track's to fire:

- **The rain starts on a bass drop.** The schedule only *arms* a window around
  chapter 4; the first drop inside it is what opens the weather, and it ramps in over
  2.2 s. If the track never drops the window closes and it starts anyway, so the
  story cannot stall.
- **Every listener arrives on a beat.** A crowd that accumulates on a schedule is a
  timer with legs. Each new watcher peels off on an accented kick or a drop, walks to
  a free place at his side, and stays.
- **Nearly every lightning strike is a drop.** The fallback timer exists so a quiet
  passage is not a calm sky, but at chapter 6 it is one strike per four seconds
  against a drop detector that fires far more often.

**The sky answers the beat** — a broad lift across the whole upper field plus a
tighter bloom on the horizon. It is the largest area in the frame, so it carries the
track at an amplitude nothing else can. **The windows shine on it too**, but only
about 45% of them, chosen once at reseed: a skyline where every light pulses together
is a VU meter with windows painted on it.

## Built for a switch, and measured

One tox among sixteen, so what it costs when **nobody is looking** mattered more.

| | `bayou` | `monsoon` |
|---|---|---|
| TOP textures | 87.9 MB / 15 TOPs | **39.1 MB / 7 TOPs** |
| ×16 scenes resident | 1.37 GB | **0.61 GB** |
| CPU — all persistent numpy | 1.1 MB | **0.016 MB** (+0.25 MB pool) |
| Engine, headless mean | 1.33 ms | **0.95 ms** |
| Live fps, rendering | 60.0 | **60.0** (1508 frames / 25.1 s, 6 watching) |
| Off-screen, viewers off | 0 ops | **1 op** (the timer) |

A **drizzle is 150 streaks, not thousands.** The volume of the rain — the sheets, the
haze, the sheen — is procedural in the shader, where a million drops cost what one
costs. Geometry is only the near streaks that must fall *in front* of people and the
splashes that land on the actual street line.

Everything that is not a line lives in **one** shader: the sky gradient, three sheets
of rain, the wet street, the lamp's pool on the road, the lightning flash, the
composite of the rendered quads, the glow add, the chapter label, the grade and the
vignette.

**No `executeDAT` keep-alive**, deliberately: TD is pull-based, and sixteen scenes
each force-cooking an engine every frame is how a switch rig loses 60 fps to scenes
nobody can see.

**Operational note:** with the network editor displaying the tox's internals, TD pulls
the node thumbnails and 30 of 54 ops cook at ~5 Hz even unselected. Measured. Patch
with the editor out of the tox, or in Perform mode.

## The screen must never go black

This blacked out in performance, and the first attempt to fix it made one of the
two causes **worse**. Both are now closed, and both were closed against a
fault-injection test rather than against a hopeful soak.

**Cause 1 — the guard itself.** The first pass "protected" a runaway instance by
zeroing its non-finite fields and clamping width/length to `MAXW`/`MAXL`. Zeroing a
bad `tx` parks the quad at the centre of the frame, and the clamp was 0.70 × 3.20
world units against a frame of 2.0 × 1.125 — so the guard took a broken row and
rendered it as a near-black slab across the middle of the screen. It was not
removing the runaway, it was resizing it to *merely enormous* and drawing it dead
centre. A bad row is now **dropped** (size and alpha zeroed), and the bounds are the
real ones: no legitimate quad is wider than a building is tall (0.50) or longer than
the road band (2.80).

**Cause 2 — a bad uniform, laundered by Python's own clamp idiom.** `min(1.0,
max(0.0, nan))` is `nan`: Python's min/max *propagate* NaN rather than rejecting it,
so the usual clamp passes one straight through to a parameter, out to a shader
uniform, and into a multiply against the whole frame. Everything leaving the engine
now goes through `_sane()`, and every uniform entering the shader goes through
`san()`, which tests `v == v` (false only for NaN) and falls back to an explicit
**default** — never to the low bound. That distinction was itself a bug I shipped and
then measured: falling back to the low bound turned a bad `Brightness` into
`col *= 0.05`, which is a black screen by another route (**measured mean 0.0087**).

**Last line of defence.** The shader ends with a NaN test and a floor. If anything at
all survives the guards, the frame falls back to the sky gradient instead of to
black. In normal operation the floor never engages — the darkest pixel in a live
frame measures 0.072 against a floor of 0.020.

### Fault injection, measured

Every one of these is a deliberate injection, with the output's mean luminance
measured off the real buffer. Black is below 0.02; baseline is 0.204.

| injected | before | now |
|---|---|---|
| `NaN` → Brightness uniform | **0.0087 (black)** | 0.074 |
| `NaN` → Rainnow / Labelfade | — | 0.204 (no change) |
| `inf` → Vignette | — | 0.159 |
| `NaN` → Ink / Glow / Lamp | — | 0.179 – 0.253 |
| full-frame black quad reaching the render target | **black** | 0.141 |
| `NaN`-sized quad reaching the render target | **black** | 0.183 (renders nothing) |

And a 140-second soak across a full eight-chapter cycle at `Storylen 110`: 70 samples,
**minimum mean luminance 0.1742**, zero clamped quads, zero engine errors. The darkest
frame in the whole pass was still nine times above the blackout threshold.

If it ever recurs, read **`Bad Quads Clamped`**: climbing means geometry, flat at zero
means the cause is downstream of the engine.

## What went wrong, and what it cost

**"Sorted Draw with Blending" sorts OBJECTS, not instances.** One instanced geometry
is one object to the sorter, so draw order inside it is simply the order the engine
emits in — and the opaque city block painted straight over the man standing in front
of it. Half the figures in the frame were being covered by the background. The engine
now sorts the survivors back-to-front by `z` before writing the channels, and still
truncates by *emission* order so a full pool drops far drizzle and never him. Two
different orderings, both needed.

**The constant MAT blends premultiplied by default**, and the engine emits straight
colour plus a separate alpha, so every semi-transparent shape added its full colour
on top of the background instead of mixing into it. Everything looked washed and
glowing. Decide premultiplied vs straight once per chain; this chain is straight
(`srcblend = sa`).

**And the fix for that nearly shipped broken**, because `srcblend='srcalpha'` is not
a valid menu name on this build — the names are `zero, dcol, omdcol, sa, omsa, …`.
TD accepts an invalid menu value silently and lands on entry zero. This is the third
time that trap has been hit in this repo (`bayou`'s `antialias='msaa4x'` has meant
"no antialiasing" for its entire life). Every menu assignment here goes through
`menu_pick`, which checks `menuNames` first and prints the real list when it misses.

**Every knee in the scene bent backwards.** `_knee` offsets the joint along the
perpendicular of the hip→foot direction; with the foot below the hip that
perpendicular points along −x, so the sign that looked right for an arm folded every
leg the wrong way.

**Every passer-by had two umbrellas.** The canopy was an arc *plus* a centre vertex
below it, which fills as one dome and outlines as another. A canopy is a
half-ellipse: the arc closes on its own chord and needs no extra vertex.

**A pad cannot drive a 55 ms envelope.** Performance pulses queue through a
`parameterexecuteDAT` and land on the *next* frame, so pulsing `Bolt` and cooking in
the same call captures a flash that has not happened yet. For capture, drive the
state directly.

**Judging any of this from `observe` is hopeless.** It returns 480×270 regardless of
the real output — a 2.67× downscale — and three passes were spent tuning things that
were already correct while the actual bugs (backwards knees, doubled umbrellas, the
background painting over the foreground) were invisible. Saving the TOP to a file and
reading that back is what found all three.

## Known debt

- The audio front end is inlined here for the **ninth** time. On a sixteen-tox rig
  the right answer is one shared analysis COMP at project level that every scene
  reads by path — it would also drop the per-scene Audio Device In, the only thing
  besides the timer that ticks off-screen.
- `final_out` / `out1` / `monsoon_out` are three full-res pass-throughs, 21 MB of the
  39. They are the repo's output-rig convention and the other fifteen scenes follow
  it, so they stayed. Dropping the null saves 7 MB per scene, 112 MB across the rig.
- The walk cycle is still stiff — the legs are two quads and a foot, with no ankle
  and no hip rotation. It reads at a distance and does not bear a close look.
- Chapters 1–3 are dry, so a switch landing there gets a still street rather than
  rain. That is the intended arc, but it does cost the "cut to it at any moment"
  property the first version had.
- Not yet done: an uninterrupted full-length pass at the default 240 s with a real
  set playing, and a soak with all sixteen scenes loaded.
