# Reclaim

Nature takes a brick wall back.

A photographed brick wall is edge-traced to its mortar outlines. On the music, a crack
spreads from a seed point, the brick darkens and breaks open, an L-System plant pushes
through the gap, grows, blooms, and bees arrive at the flowers. Every cycle wakes
another plant, so the wall fills into a garden.

Build with:

```python
code = open('scenes/reclaim/build.py', encoding='utf-8').read()
g = dict(globals()); exec(code, g)
```

The script is idempotent — it destroys and recreates `/project1/reclaim` and its
project-level `reclaim_out` Out TOP, and touches nothing else.

Needs `media/brick-wall.png`. The path list at the top of `build.py`
(`WALL_CANDIDATES`) is tried in order; the first that exists wins.

## The cycle

One `timerCHOP` free-runs and cycles forever; everything else is derived from its
phase in the `director` Script CHOP. Within a cycle:

| phase | what happens |
|---|---|
| 0.00 – 0.24 | the crack spreads and the brick breaks open |
| 0.14 – 0.60 | the stem grows (L-System `generations` 0 → 6) |
| 0.50 – 0.80 | flowers open, each on its own delay |
| 0.66 – 1.00 | bees fly in from off-frame and orbit the flowers |

Plant *i* is born on cycle *i*. From cycle *i+1* on it simply stays grown while later
cycles keep adding flowers to it (`dens0..2`), so the garden accumulates rather than
resetting. `Restart` zeroes it back to a bare wall.

## Custom parameters

On the `reclaim` COMP, page **Reclaim**:

| parameter | what it does |
|---|---|
| `Audiosrc` | Audio Device In (performance) or TD's bundled track (testing) |
| `Reactivity` | overall audio gain into the band chain |
| `Devgain` | extra gain applied to device input only — a mic sits far below a decoded file |
| `Cyclelen` | seconds per cycle (default 20) |
| `Photomix` | how much of the brick photograph shows under the traced outlines |
| `Linebright` | brightness of the traced mortar grid |
| `Crackamt` | crack strength |
| `Flowersize` | flower head size |
| `Beecount` / `Beespeed` | how many bees and how fast they orbit |
| `Glow` | bloom pass strength |
| `Vignette` | corner falloff |
| `Restart` | reset to a bare wall (cycle 0) |

## Audio mapping

Canonical two-band chain from `patterns.md` (lowpass 700 Hz / highpass 3 kHz, each
enveloped, **resampled to 60 Hz**, then filtered) plus a slow overall energy envelope.

- **bass** → growth surge, brightness of the light bleeding through the fracture
- **high** → bee speed and orbit radius
- **energy** → stem colour warmth, flower lift, glow strength, plant sway

## Structure

```
wall_src → wall_fit ─┬─ wall_base (dim warm photo) ─┐
                     └─ wall_mono → wall_soft → wall_edge → wall_lines ─┴→ wall_mix
                                                                             │
cycle_timer ─┐                                                          wall_crack (GLSL)
null_audio  ─┴→ director ──────────────────────────────────────────┐         │
                                                                   │         │
plant{0,1,2}_lsys (tube, generations from director) → plant*_geo ───┤         │
plant{0,1,2}_full (static skeleton) → flower_sites ─┬→ flower_inst ─┤         │
                                                    └→ bee_inst  ───┤         │
                                          flowers / bees (instanced)┴→ render_garden
                                                                             │
                                              comp_scene ← render over wall ─┘
                                              → glow (cut → blur → add) → grade
                                              → final_out → out1 → /project1/reclaim_out
```

## Performance

Measured at **60.0 fps** on the M5 (see `MACHINE.md`), whole project clean.

- The only per-frame CPU of consequence is the L-System of the plant currently
  growing: `type='tube'`, Gens 6, ~23k points, ~1 ms.
- `wall_crack` is one full-res GLSL pass (~0.9–2.9 ms GPU) that does the crack *and*
  the wall's final grade, rather than four separate TOPs.
- The three Script CHOPs (`director`, `flower_inst`, `bee_inst`) replace roughly forty
  CHOPs of envelope maths and run numpy over fewer than 200 samples per frame.
- If it ever needs headroom: all three L-Systems re-cook every frame even once fully
  grown (~3 ms total). Freezing a finished plant into a static copy would recover most
  of that.

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
