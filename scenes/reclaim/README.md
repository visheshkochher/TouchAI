# Reclaim

Nature takes a brick wall back.

One continuous story, about four minutes long: a photographed brick wall is edge-traced
to its mortar outlines, a crack opens, an L-System plant pushes through it, grows,
blooms and draws bees — then a second plant cracks its own brick and does the same,
then the next, and the next — eight in all, their scenes overlapping — until the wall
is a garden, and the garden stays.

Build with:

```python
code = open('scenes/reclaim/build.py', encoding='utf-8').read()
g = dict(globals()); exec(code, g)
```

The script is idempotent — it destroys and recreates `/project1/reclaim` and its
project-level `reclaim_out` Out TOP, and touches nothing else.

Needs `media/brick-wall.png`. The path list at the top of `build.py`
(`WALL_CANDIDATES`) is tried in order; the first that exists wins.

## The story

There is no stage machine and nothing loops. The show is a single playhead, `show`,
in story-seconds since the wall was bare:

```
show = clamp(musical time − Timeoffset, 0, storyend)
storyend = Scenelen × ((plants−1)×STAGGER + 1 + 0.3)   # 60 × 4.8 = 288s by default
```

**The ending persists.** `show` is clamped, not wrapped: once the fourth plant has
bloomed the full garden simply stays on screen (`done` goes to 1) until someone seeks
back to an earlier checkpoint, from which it grows forward again.

**Story time is musical time, not wall time.** A beat detector estimates the tempo and
the story advances at `bpm / Refbpm`, so a 140bpm track pushes the plants up noticeably
faster than a 90bpm one, and `Scenelen` is "seconds per plant *at the reference
tempo*". `Beatdrive` blends between constant speed (0) and full tempo-following (1).
See Tempo below.

Plant *i*'s scene opens `STAGGER` (0.5) scene-lengths after plant *i−1*, so growth
overlaps and the wall is continuously in motion rather than taking eight full minutes
to fill. Each plant holds its finished state afterwards. Within its own 60 seconds:

| fraction | seconds | what happens |
|---|---|---|
| 0.02 – 0.22 | 1 – 13 | the crack spreads and the brick breaks open |
| 0.12 – 0.62 | 7 – 37 | the stem grows (L-System `generations` 0 → 5) |
| 0.52 – 0.80 | 31 – 48 | flowers open, each on its own delay |
| 0.68 – 0.95 | 41 – 57 | bees fly in from off-frame and orbit the flowers |

The trailing `0.3 × Scenelen` is the held full-garden ending.
Every later scene also keeps adding flowers to the plants already standing (`dens0..3`),
so the wall keeps thickening rather than just accumulating stems.

## Checkpoints — keys 1-9

Checkpoints are **seeks, not freeze-frames**. Pressing a key moves the playhead and the
story carries on playing from there, so key `2` shows the crack actually *forming* over
the following twelve seconds rather than a static cracked wall.

| key | pulse | lands on | seconds |
|---|---|---|---|
| `1` | `Gostart` | bare traced wall | 0 |
| `2` | `Gocrack` | first crack begins to open | 1.2 |
| `3` | `Gogrow` | first sprout pushes through | 8.4 |
| `4` | `Gobloom` | first plant grown, about to flower | 30 |
| `5` | `Gobees` | flowers open, bees on their way | 39.6 |
| `6` | `Gospread` | garden spreading, 2 of 8 up | 60 |
| `7` | `Gohalf` | half the wall, 4 of 8 up | 120 |
| `8` | `Golast` | last plants breaking through, 6 of 8 | 180 |
| `9` | `Gogarden` | full garden, all eight, into the held ending | 279 |
| `0` | `Restart` | back to the bare wall, playing | 0 |

Because the ending holds rather than looping, the keys are also how you get *out* of the
finished garden: press `7` and the first two plants stay standing while the third
cracks its brick and grows again from there.

Seconds shown are at the default `Scenelen` of 60; they scale with it. `Nextcp` and
`Prevcp` step through the list — those are the ones to bind to a footswitch or MIDI pad.

Seeking is a subtraction on `Timeoffset`, not a transport command: nothing is ever
paused, which is exactly why playback resumes by itself. Checkpoints are measured in
*musical* time, so a given checkpoint means the same place in the story at any tempo.
Bee orbits and plant sway run off the wall clock instead, so they stay smooth and
physical across a jump and are not disturbed if the tempo estimate wobbles.

`Showtime` on the COMP is a read-only mirror of the playhead, handy while performing.

## Custom parameters

On the `reclaim` COMP, page **Reclaim**:

| parameter | what it does |
|---|---|
| `Audiosrc` | Audio Device In (performance) or TD's bundled track (testing) |
| `Reactivity` | overall audio gain into the band chain |
| `Devgain` | extra gain applied to device input only — a mic sits far below a decoded file |
| `Scenelen` | seconds for one plant's full arc at the reference tempo (default 60) |
| `Refbpm` | tempo at which `Scenelen` is literal (default 120) |
| `Beatdrive` | 0 = constant speed, 1 = fully tempo-driven |
| `Bpm` | read-only detected tempo (0 when the beat is lost) |
| `Photomix` | how much of the brick photograph shows under the traced outlines |
| `Linebright` | brightness of the traced mortar grid |
| `Crackamt` | crack strength |
| `Moss` | how far green creeps over the brick as the garden fills |
| `Flowersize` | flower head size |
| `Leafsize` | leaf size (0 removes the foliage entirely) |
| `Beecount` / `Beespeed` | how many bees, and the shared orbital rate |
| `Glow` | bloom pass strength |
| `Vignette` | corner falloff |
| `Timeoffset` | the playhead; checkpoints write it |
| `Showtime` | read-only story time in seconds |
| `Gostart` … `Gogarden` | seek to a checkpoint |
| `Nextcp` / `Prevcp` | step between checkpoints |
| `Restart` | back to the bare wall |

## Tempo

`tempo` is a Script CHOP doing onset detection on a **dedicated kick band** — a
lowpass at 140Hz that feeds nothing else. The main 700Hz "bass" band is too wide to
count beats with: it carries the bassline and the body of the snare too, and detection
off it read 175bpm on a ~125bpm track.

Two choices in there are worth keeping:

- **Positive flux, not a level ratio.** Comparing the slice peak against an EMA of the
  slice peak does not work — the envelope is already smooth, so the baseline sits at
  roughly the same height as the signal (measured: baseline 0.77 against a signal
  maxing at 0.54) and the ratio never clears a threshold. The *rise* is what marks an
  onset, and it is naturally independent of how loud the track is.
- **Median of recent intervals, not an EMA.** One spurious onset halves an EMA and
  drags the whole story speed with it; the median just ignores it. On the bundled test
  track the collected intervals run
  `[0.35, 0.37, 0.37, 0.37, 0.38, 0.40, 0.43, 0.48, 0.48, 0.48, 0.48, 0.50, 0.58, 0.67, 0.70]`
  — the median picks 0.483s = **124.1 bpm**, which is right, while the mean would not be.

Before the first beat is ever heard the factor sits at 1.0 rather than the silence
floor, so the show does not crawl for the first few seconds after a build. After ~2.5s
with no beats it eases down to 0.25× rather than stopping. `Bpm` on the COMP shows the
current estimate (0 when it has lost the beat).

## Audio mapping

Canonical two-band chain from `patterns.md` (lowpass 700 Hz / highpass 3 kHz, each
enveloped, **resampled to 60 Hz**, then filtered) plus a slow overall energy envelope.

- **bass** → growth surge, brightness of the light bleeding through the fracture, and
  the bees' orbit radius breathing in and out
- **high** → deliberately not routed to the bees (see below)
- **energy** → stem colour warmth, flower lift, glow strength, plant sway

### Bees are rhythmic, not frantic

Three things were making the swarm read as jitter, and all three are fixed:

- Per-bee orbital rates were spread over **2.55×**, and a treble transient multiplied
  speed on top, so the fastest bee could run **5.6×** the slowest. Every bee now shares
  one rate with a ±6% spread (**1.13×**), and the treble band no longer touches speed.
- The beat now breathes the orbit **radius** (±18%) instead of the speed, so bees pulse
  toward and away from their flower on the music instead of sprinting.
- The wobble was at non-integer harmonics (1.3 / 2.7 / 3.1 ×) which never resolved
  against the orbit. It now sits on exact **2×** and **0.5×** harmonics, so it repeats
  with the orbit and reads as a hover.

## Plant detail

Each plant is four instanced layers over one L-System, not just stems:

- **Stems** — lit tapered tubes. The rule carries a `/(137)` roll, the golden angle
  real phyllotaxis uses; without it every branch stays in one plane and the crown is a
  flat cut-out (measured depth, z extent over height: **0.11 flat vs 0.54** with the
  roll, and it bunches the tips slightly better too).
- **Leaves** — pointed blades instanced up the stems, unfurling as growth passes their
  height, older ones lower down and larger. They are distributed by **height band**
  rather than evenly through the candidate list: branching multiplies segments toward
  the crown, so sampling the list evenly piles every leaf into the flower head and
  leaves the stems bare. Candidates are also sampled *along* each segment, because the
  bare lower stem is only four long segments and vertex-only sampling leaves the low
  bands empty.
- **Buds** — a bud is just an unopened flower: once the stem carrying it has grown it
  shows small and green, then swells and takes on its colour as it opens. Cheaper than
  a separate instancer, and it means the crown is never bare while the plant waits for
  its bloom window.
- **Flowers** — five-petal blooms with a warm centre, sitting on the **true branch
  tips** and pushed a little way out along their own branch so the bloom crowns the
  stem end rather than straddling it.

Foliage and blossom scale with **their own plant**: at a fixed world size the short
plants read as stacked green chevrons rather than leaves.

**Layer order is done with three render passes, not with depth.** Inside a single
render TOP the blossom kept losing to the stems no matter what: flowers parked at
z=3.0 — right against the camera, an order of magnitude in front of stems at z ≤ 0.2 —
*still* drew behind them, and neither `orderind` nor `sortedblending` changed it.
Compositing separate passes in 2D is unconditional: `render_plants` (stems + leaves),
then `render_bloom`, then `render_bees`, each composited strictly over the last. What
is in front is simply what is composited last. The per-layer z values are kept as a
sane secondary ordering, but they are not what decides it.

**Moss** creeps out of every crack as `fullness` rises — patchy, broken up by its own
noise, and settling into the mortar first, so it reads as growth on brick rather than a
green wash.

Everything rotates about its own plant's base by the **same** `sway` angle, published
once by the director. Flowers used to carry an unrelated horizontal wiggle of their own
and visibly slid off the stems as the plant leaned.

## Structure

```
wall_src → wall_fit ─┬─ wall_base (dim warm photo) ─┐
                     └─ wall_mono → wall_soft → wall_edge → wall_lines ─┴→ wall_mix
                                                                             │
clock (free-run) ─┐                                                     wall_crack (GLSL)
null_audio       ─┴→ director ─────────────────────────────────────┐         │
                                                                   │         │
plant{0..3}_lsys  (tube, generations from director) ─┐             │         │
plant{0..3}_grown (tube, static, full growth) ───────┴→ *_switch → plant*_geo │
plant{0..3}_full  (skeleton, static) → flower_sites ─┬→ flower_inst ┤         │
                                                     └→ bee_inst  ──┤         │
                                          flowers / bees (instanced)┴→ render_garden
                                                                             │
                                              comp_scene ← render over wall ─┘
                                              → glow (cut → blur → add) → grade
                                              → final_out → out1 → /project1/reclaim_out
```

## Performance

Measured at **60.0 fps** on the M5 (see `MACHINE.md`) with all four plants grown, whole
project clean.

- **Only the plant currently growing costs anything.** A finished plant's
  `generations` expression reads the director, which cooks every frame, so its SOP was
  being dirtied every frame even though the value had stopped moving — with four plants
  that was ~4 ms of L-System per frame for no reason. A **Switch SOP only cooks its
  selected input**, so once `grow >= 0.999` it selects a static full-growth copy and the
  animated L-System is not evaluated at all. Verified: `cookFrame` on all four animated
  L-Systems stays frozen across thousands of frames at the garden checkpoint.
- `wall_crack` is one full-res GLSL pass (~0.8–1.1 ms GPU) that does all four cracks
  *and* the wall's final grade, rather than a stack of TOPs.
- The Script CHOPs (`director`, `tempo`, `flower_inst`, `bee_inst`) replace roughly
  forty CHOPs of envelope maths and run numpy over fewer than 250 samples per frame.
- `frame_exec` cooks the director once per frame. **TD only cooks what something is
  pulling on**, and with the scene's output not on screen nothing pulls the director,
  so the story clock and the beat detector simply stop — measured, `cookFrame` stuck at
  246 while the project was on frame 374990. This keeps musical time and tempo
  detection running whatever is being displayed, for the price of one CHOP cook.

## Things worth knowing if you edit this

- **A branch tip is a node with exactly one segment touching it** — *not* "the last
  vertex of a prim". Measured on one plant: 82 real tips (degree 1, at heights
  0.71–1.00 of the plant) against 41 prim end-points, of which exactly **one** was a
  real tip; the rest were interior junctions at heights 0.55–0.88. Placing flowers on
  prim ends buried them in the middle of the crown and left the outer stems bare.
  Build adjacency over every segment and take the degree-1 nodes (dropping the root,
  which is also degree 1).
- **Sprite quads must come from a `gridSOP`** (`rows=2, cols=2, texture='rowcol'`).
  `rectangleSOP`'s own `texture` toggle produces no uv attribute at all on this build,
  and a `textureSOP` in `rowcol` mode on a single four-vertex polygon produces garbage:
  measured uv `(1.0,0.5) (1.333,0.5) (0.667,0.5) (1.0,0.5)` — `v` pinned at 0.5 and `u`
  running outside 0..1, so every sprite drew one horizontal *slice* of its texture
  stretched across the quad. It is easy to miss because the result still looks like a
  soft coloured blob. gridSOP gives the expected `(0,0) (1,0) (0,1) (1,1)`.
- A Script SOP's `scriptOp.vertexAttribs.create(...)` **aborts the callback** on this
  build — no exception, no error, the geometry just stops being built at that line.
- The **Rules DAT wants no space after the delimiter**. `premise:FX` and `X=F-...`
  work; `premise: FX` silently produces zero geometry and no error.
- The textbook `F=FF` bush grows a long bare stick before it branches at all (measured:
  zero horizontal spread over the bottom 30% of the plant). Rule C —
  `premise:A`, `A=F[+A]F[-A]A` — branches from the base up, which is what a plant
  bursting out of a wall needs.
- `thickinit` on a tube L-System is scaled by the **step size**, not by plant height.
  Rendered silhouette coverage for one plant at Gens 6: `0.02` → 0.7 % (sub-pixel
  hairlines), `0.06` → 4.6 % (what's used), `0.30` → 16 % (a solid green blob).
- Flower **sites** come off `plant*_full`, a *skeleton* copy held at full growth. Tube
  mode would turn every branch tip into a ring of duplicate points, and a static input
  means the Script CHOP cooks once instead of every frame.
- Plant bases sit well inside the frame. Centred on the bottom edge, a crack loses half
  its disc off-screen and stops reading as a break in the wall.
- `Timeoffset` is a 32-bit float par, so seeking to exactly 0 rounds to a tiny negative
  and `(negative mod storylen)` wraps to the very *end* of the story — the bare wall
  came back as the full garden. `_seek` lands 20 ms past the target to stay clear of it.
- `switchSOP`'s parameter is `input`, not `index`.
- TD delivers at most one pulse per parameter per frame, so firing several checkpoint
  pulses inside a single script only applies the first. One key press per frame — real
  use — is fine.
- To inspect a specific moment without MCP round-trip latency moving the story on you,
  set `clock.par.play = False`, seek, observe, then set it back to `True`.
