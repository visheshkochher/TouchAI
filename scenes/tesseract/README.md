# Tesseract

A camera travelling through the inside of a four-dimensional lattice, for a long
techno set. It is Amon Tobin's *ISAM* by way of the tesseract in *Interstellar*, and
everything in it is a line.

Build:

```python
code = open('scenes/tesseract/build.py', encoding='utf-8').read()
g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
```

The builder is idempotent. It destroys and recreates `/project1/tesseract` and
`/project1/tesseract_out`, and touches nothing else. It needs no media files.

**`build.py` is generated.** It is `tesseract_template.py` plus three verbatim blocks
of `scenes/homestead/build.py` (the helpers, the audio front end with tempo and drop
detection, and the director), assembled by `gen_tesseract.py`. After editing the
template, regenerate with `python3 scenes/tesseract/gen_tesseract.py`.

## Research: what was taken from where

**Amon Tobin, *ISAM* (2011–12).** V Squared Labs and Leviathan built the show in
TouchDesigner, projection-mapped onto a 14-foot stack of Tetris-like cubes. It
included:

- wireframes and procedural structures, Tron grids, M.C. Escher and kaleidoscopes
- the structure glowing "as if each square is being lit from the inside" (*Lost &
  Found*)
- a circuit board and a futuristic skyscraper
- a spaceship interior and an engine-room emergency
- high-end renders deliberately "ripped to shreds" with glitch

**Taken here:** the lit cell faces (amber panels and circuit traces), the stacked
channel, the Tron and red-alert palettes, and glitch on the drop.

**The *Interstellar* tesseract** (Double Negative, Paul Franklin, with Kip Thorne):

- an open lattice of rooms extended infinitely, where "the rooms are snapshots in
  time"
- time made physical as world lines, threads extruded from every object with
  information streaming along them
- slit-scan photography, and Gerhard Richter's scraped paint trails
- hypercube rotation transforms

**Taken here:**

- the lattice is the world
- threads run along the travel axis, with light packets running down them
- the big hypercube's vertices trail their own past orientations (its timelines,
  extruded)
- a feedback trail that either pulls outward from the vanishing point (slit-scan) or
  drags sideways (Richter's scrape)
- the bookshelf program: the Interstellar shelf texture, in sepia

**The math:** a tesseract's 16 vertices are (±1, ±1, ±1, ±1), with 32 edges. It is
rotated in the xw, yw, zw and xy planes, and projected to 3D by `d / (d − w)`.

**The repo's `audio-reactive-particles` notes:**

- fast bass and slow highs
- a slow noise "wander" on parameters so it never sits still between beats
- outward-spiralling scale-up feedback trails (here, the slit-scan)

Everything is a line, not a particle.

## Six programs, one world

A program is a set of parameters, not a scene. Every parameter morphs over two beats,
so a change transforms the one lattice rather than cutting away from it.

| # | program | what it is |
|---|---|---|
| 1 | CORRIDOR | a lattice all around, amber panels and circuits on the walls, threads through it |
| 2 | HYPERCUBE | a big tesseract turning in 4D around the camera, small ones in the cells, slow travel |
| 3 | STACK | ISAM: a channel walled with lit panels and circuit traces, stacked and broken like Tetris |
| 4 | STARGATE | fast. The cross-lines fade, the long lines and threads stream out of the vanishing point, long slit-scan trails |
| 5 | BOOKSHELF | Interstellar: shelves of books on every wall, threads woven across, the scrape trail, sepia |
| 6 | FOLD | the whole lattice folding through the fourth dimension, with tesseracts in the cells |

Each program picks a palette at random from the ones it allows: AMBER, SEPIA, TRON,
ALERT, BONE or CIRCUIT. Each palette sets the lattice, panel, thread, tesseract,
highlight and background colours.

## Built for a long set: what keeps changing

- **Phrases.** On each phrase boundary (default 32 beats) the program is re-chosen
  with the probability set by `Program Change Chance` (default 0.55). Its palette is
  re-chosen with it. In a breakdown, the choice is biased toward the quiet programs.
- **Every 8 beats**, small things may flip: which plane the lattice folds in, the
  direction of the roll, and the angle of the scrape.
- **Every 2 beats**, the lit faces re-choose themselves, so the Tetris lighting
  keeps shifting.
- **Drops.** A drop:
  - folds the lattice through w, in a random plane and direction
  - tears the frame with glitch and fires a white flash
  - surges the travel speed
  - sends a big shockwave
  - reseeds the lattice, which is masked by the glitch
  - three times in four, switches program
- **Breakdowns are detected.** If short-term energy stays under half its 10-second
  level for 2.5 s:
  - travel slows to a quarter
  - the hypercube surfaces
  - every face glows dimly (*Lost & Found*)
  - the trails lengthen

  When the kick returns, it all eases back.
- **Stochastic by construction.** Lattice gaps, lit faces, patterns, tesseract cells
  and thread positions are all hashed from cell indices and a seed. The corridor
  never repeats, and a reseed makes a new one.

## Audio

| signal | drives |
|---|---|
| tempo | travel speed (cells per beat), the phrase and 8-beat clocks, the fold's slow swing |
| kick | a shockwave that runs down the lattice lighting every line it passes; the threads are plucked; the small tesseracts tick forward in 4D; the lit faces flicker; the field of view punches; the line width pulses |
| accent | occasionally (15%, scaled by `Glitch`) a short glitch |
| drop | fold, glitch, flash, surge, big shockwave, reseed, program change |
| bass | the 4D spin, the thread vibration, the roll speed, the fold's w bulge, the line width |
| highs | how many light packets run down the threads, and their brightness; thread shimmer; panel shimmer |
| energy | travel speed, glow, the vanishing-point light |

## Keys

| key | does |
|---|---|
| 1-6 | force a program. It is held for 64 beats, then the automatic changes resume |
| 0 | release it now |
| f | **FOLD**: rotate the whole lattice through the fourth dimension |
| g | **GLITCH**: tear the frame |
| p | **PULSE**: a shockwave down the lattice |
| c | **PALETTE**: the next palette |
| n | **NEW**: a random program and a new lattice |
| h | **HOLD**: stop the automatic program changes (toggle) |
| r | **REVERSE**: fly the other way (toggle) |

The performance page also has:

- Travel Speed, Program Change Chance and Phrase Length
- Line Width, Brightness of Lines, Glow, Trails
- Glitch and Fold (4D) amounts
- the Program Readout and the Vignette

## The pipeline

One numpy engine builds only the window of the world around the camera each frame.
The window is 8 × 6 cells across and 18 deep.

- **Lattice lines** go at every half-integer x and y and every integer z. Gaps come
  from an occupancy hash. A hollow channel for the camera is cleared by `hol`.
- **Faces** are the channel's walls, floor and ceiling. Lit ones get one of five
  patterns (panel, three circuits, books), stamped by broadcasting.
- **Threads** are 40 world lines along z, with packets. The bookshelf also weaves
  threads along x.
- **Small tesseracts** sit in hashed cells. The big one sits ahead of the camera,
  with 7 extruded timeline steps.

All of it goes through one pipeline:

1. camera-relative position, then yaw, pitch and roll
2. **the fold**: embed in 4D with a small w bulge, rotate through w in one of three
   planes, project back with a w-perspective
3. near-plane clip
4. perspective
5. band-tear and red/cyan echo glitch

It publishes into a fixed pool of 14000 instanced unit segments.

The post chain is:

1. feedback trail (slit-scan zoom or scrape, max-blended)
2. over a nebula void with a vanishing-point glow
3. glow
4. a glitch shader: torn bands, displaced blocks, colour split, scan lines
5. the readout
6. the grade

## Performance

- **60 fps with the engine verified cooking at 59.8 cooks/s** (counted with
  `totalCooks`), in the editor with a viewer open.
- Engine: 5 ms per cook. Other CPU cooks: 2.5 ms or less each.
- GPU: 1.1 ms or less per operator.
- Line count: 3–7k in most programs, 11.6k at a breakdown with every face lit.
- 74 operators, zero errors, zero warnings.

## Built to run all night

- **Script CHOP channels are built once**, then only written: the engine, plus the
  director and tempo detector inherited verbatim from homestead.
- **Every list is hard-capped** and aged out: 8 shockwaves, and 16 queued verbs.
  Everything else is recomputed from the window each frame.
- **Every phase wraps.** The camera position is an integer cell counter modulo 2^20
  plus a fraction; hashes use the counter modulo 4096. The roll, the 4D angles and
  the sway and fold phases wrap too, and the shaders get a clock modulo 1000 s.
- **Nothing tells a story that could end.** The piece is a state machine over
  programs.

**Long-run memory audit: pending.** Per the repo rule, the RSS soak is the final
iteration and runs only after the visual style is approved.

## What went wrong on the way

- **The first pass was a moiré.** Far lattice lines barely faded, so thousands of
  them converged into a bright knot at the vanishing point, and the full bookshelf
  lattice hit 11k lines of noise. Every program's fog was roughly halved, and the
  bookshelf got a wider channel and sparser occupancy.
- **A colour fringe with glitch at zero.** The glitch shader's resting colour split
  (0.001 of the width, plus the kick) was a visible fringe on 1-pixel lines. It is
  now 0.0003.
- **The bookshelf blew out into an X.** With the camera in a one-cell corridor, both
  adjacent walls were full of lit books and smeared by the scrape trail. Moving the
  walls out a cell (`hol` 1) and trimming the scrape fixed it.
- **The "[breakdown]" readout never showed**, because the label only refreshed on a
  program change. Entering or leaving a breakdown now also flashes the readout.
- **The test track is not a techno set.** TD's sample file fires the drop detector
  every few seconds, so drops, folds and glitches come far more often here than they
  will on a real set. `Glitch` and `Fold (4D)` scale them if they do.
