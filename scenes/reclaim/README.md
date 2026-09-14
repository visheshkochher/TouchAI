# Reclaim

Nature takes a brick wall back.

One continuous story, about four minutes long: a photographed brick wall is edge-traced
to its mortar outlines, a crack opens, an L-System plant pushes through it, grows,
blooms and draws bees — then a second plant cracks its own brick and does the same,
then a third, then a fourth, until the wall is a garden. Then it loops.

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

There is no stage machine and nothing loops except the whole arc. The show is a single
playhead, `show`, in seconds since the wall was bare:

```
show = (monotonic clock − Timeoffset) mod storylen
storylen = Scenelen × (plants + 0.3)      # 60 × 4.3 = 258s by default
```

Plant *i* owns the window `[i·Scenelen, (i+1)·Scenelen]` and holds its finished state
afterwards. Within its own 60 seconds:

| fraction | seconds | what happens |
|---|---|---|
| 0.02 – 0.22 | 1 – 13 | the crack spreads and the brick breaks open |
| 0.12 – 0.62 | 7 – 37 | the stem grows (L-System `generations` 0 → 6) |
| 0.52 – 0.80 | 31 – 48 | flowers open, each on its own delay |
| 0.68 – 0.95 | 41 – 57 | bees fly in from off-frame and orbit the flowers |

The trailing `0.3 × Scenelen` is a held full-garden tail before the story restarts.
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
| `6` | `Gosecond` | second plant starts cracking | 60 |
| `7` | `Gothird` | third plant starts cracking | 120 |
| `8` | `Gofourth` | fourth plant starts cracking | 180 |
| `9` | `Gogarden` | full garden, all four plants | 235.2 |
| `0` | `Restart` | back to the bare wall, playing | 0 |

Seconds shown are at the default `Scenelen` of 60; they scale with it. `Nextcp` and
`Prevcp` step through the list — those are the ones to bind to a footswitch or MIDI pad.

Seeking is a subtraction on `Timeoffset`, not a transport command: nothing is ever
paused, which is exactly why playback resumes by itself. The master clock free-runs and
is never seeked, so bee orbits and plant sway stay continuous across a jump.

`Showtime` on the COMP is a read-only mirror of the playhead, handy while performing.

## Custom parameters

On the `reclaim` COMP, page **Reclaim**:

| parameter | what it does |
|---|---|
| `Audiosrc` | Audio Device In (performance) or TD's bundled track (testing) |
| `Reactivity` | overall audio gain into the band chain |
| `Devgain` | extra gain applied to device input only — a mic sits far below a decoded file |
| `Scenelen` | seconds for one plant's full arc (default 60) |
| `Photomix` | how much of the brick photograph shows under the traced outlines |
| `Linebright` | brightness of the traced mortar grid |
| `Crackamt` | crack strength |
| `Flowersize` | flower head size |
| `Beecount` / `Beespeed` | how many bees, and the shared orbital rate |
| `Glow` | bloom pass strength |
| `Vignette` | corner falloff |
| `Timeoffset` | the playhead; checkpoints write it |
| `Showtime` | read-only story time in seconds |
| `Gostart` … `Gogarden` | seek to a checkpoint |
| `Nextcp` / `Prevcp` | step between checkpoints |
| `Restart` | back to the bare wall |

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
- The three Script CHOPs (`director`, `flower_inst`, `bee_inst`) replace roughly forty
  CHOPs of envelope maths and run numpy over fewer than 250 samples per frame.

## Things worth knowing if you edit this

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
