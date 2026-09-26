# Eridian

*Project Hail Mary*, seen the way Rocky sees: by sound. It is built for a club LED
wall, so it is dark by design, with its brightness held down by a limiter.

Build:

```python
code = open('scenes/eridian/build.py', encoding='utf-8').read()
g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
```

The builder is idempotent. It destroys and recreates `/project1/eridian` and
`/project1/eridian_out`, and touches nothing else. It needs no media files.

**`build.py` is generated.** It is `eridian_template.py` plus three verbatim blocks of
`scenes/homestead/build.py` (the helpers, the audio front end with tempo and drop
detection, and the director), assembled by `gen_eridian.py`. After editing the
template, regenerate with `python3 scenes/eridian/gen_eridian.py`.

## What it takes from the book and the film

**Rocky** is an Eridian engineer. He is eyeless and spider-like: five legs from a
rough rock carapace, three fingers to each hand. He navigates by echolocation and
speaks in musical chords.

**The Blip-A**, his ship, is built almost entirely of xenonite.

- In the film, its interior is strung with "long strings and prism-like plates" that
  are its musical instruments.
- It has reflective surfaces, and carvings that tell Eridian history.

The rest of the world:

- **Astrophage** lives on starlight and glows in the infrared, drawing the Petrova
  line.
- **Tau Ceti** and its planet **Adrian**, home of the taumoeba that eat Astrophage.
- The **xenonite tunnel** between the two ships, with the clear wall Rocky and Grace
  talk through.

So:

- **The world is dark until sound reveals it.** Every kick is a sonar ping from Rocky.
  A shell expands through the line-drawn structure and lights it (in teal) only as it
  passes. Between pings the world is a faint ghost, and some things, like the
  carvings on the walls, exist *only* in the sonar.
- **The music is played on the ship.** Each of the Blip-A's strings is tuned to one
  of 16 spectrum bands, as a standing wave with its own harmonic. A chord in the
  track is a chord on the strings.
- **Rocky answers in chords.** Glyphs rise from his carapace, one arc per note. The
  notes are the spectrum's three loudest bands at that moment.

## Five views

| # | view | what it is |
|---|---|---|
| 1 | THE STRINGS | inside the Blip-A: a long hexagonal xenonite hall, a harp of strings along it, prisms turning on the strings, carvings on the walls. Rocky walks the floor ahead |
| 2 | ROCKY | him: a faceted rock carapace with vent slits that breathe on the bass, five arched legs, three-fingered hands. Around him are pentagonal floor rings and a ring of pillars strung overhead |
| 3 | BLIP-A | outside: a hexagonal truss spine, three rings on stays, a geodesic xenonite hull forward, and the Astrophage drive bell with a dim infrared exhaust. The Hail Mary is docked off to the side by the tunnel. Stars |
| 4 | THE TUNNEL | the octagonal xenonite tube, and the clear wall. Rocky is on the far side with one hand on it; his taps ripple across it. *Fist my bump.* |
| 5 | THE PETROVA LINE | Tau Ceti, a river of 700 Astrophage flowing to Adrian, and taumoeba that arrive on a drop and eat what they touch |

The views crossfade over four beats. Each phrase (32 beats by default) has a 50%
chance of a new view. A drop picks a new one 60% of the time.

## Audio

| signal | drives |
|---|---|
| kick | a sonar ping from Rocky; he lifts the next leg (a five-point star-step, every other leg); in the tunnel, he taps the wall and it ripples |
| spectrum (16 bands) | the strings: each band's level is its string's amplitude and brightness, with its own harmonic |
| three loudest bands | the notes of Rocky's chord glyphs (35% of downbeats, 40% of accents, every drop) |
| bass | the vent slits opening, the thick bass strings across the hall, the drive exhaust, Tau Ceti's rays, the orbit speed |
| highs | the Astrophage shimmer, the stars |
| drop | three pings, Rocky jumps, a chord, taumoeba, "amaze amaze amaze", and often a new view (in the tunnel: the fist bump) |
| breakdown | detected when energy stays under half its 10-second level for 2.5 s. The pings stop, Rocky curls up, travel slows, and the readout says *you sleep. i watch.* |

## Keys

| key | does |
|---|---|
| 1-5 | a view (held for 64 beats, then the automatic changes resume) |
| 0 | automatic again |
| s | **SONAR**: three pings |
| a | **AMAZE** |
| f | **FIST MY BUMP**: goes to the tunnel |
| c | Rocky speaks a **CHORD** |
| h | **HOLD** the view (toggle) |
| n | **RESEED** |

## For a club LED wall

- **The look itself is dim.** The world is near-black, and its lines sit at a
  ghost's brightness until a ping passes.
- **An average-brightness limiter.** An Analyze TOP measures the frame's mean
  luminance, a Lag CHOP smooths it (0.15 s up, 1.2 s down), and a gain holds it
  under `Average Brightness Cap` (default 0.055, about 5.5% of full white).
  Measured running: 0.033.
- **A soft peak ceiling.** `c' = M(1 − e^(−c/M))` is linear in the dark and never
  exceeds `Peak Ceiling` (default 0.75).
- **No white flashes anywhere.** Drops are more pings, a jump and a chord, not light.
- The knobs are `Master Brightness`, `Average Brightness Cap`, `Peak Ceiling` and
  `Unlit World`. Tune them on the actual wall. LED walls vary enormously.

## Performance

- **60 fps with the engine verified cooking at 60 cooks/s** (counted with
  `totalCooks`), in the editor with a viewer open.
- Engine: 3–6 ms per cook. GPU: under 1 ms for every operator.
- The limiter's TOP→CHOP readback (`apl_chop`) costs about 2.7 ms of CPU, because it
  waits on the GPU. If a slower machine drops frames, halve the Analyze input
  resolution first.
- Line count: 0.4k–3k depending on the view, against a fixed pool of 14000.
- 78 operators, zero errors, zero warnings.

## Built to run all night

- **Script CHOP channels are built once**, then only written: the engine, plus the
  director and tempo detector inherited verbatim from homestead.
- **Every list is hard-capped** and aged out: 10 pings, 6 glyphs, and 16 queued
  verbs.
- **Every phase wraps.** The hall position is an integer module counter modulo 2^20
  plus a fraction; the gait, orbit and roll wrap; the shaders get a clock modulo
  1000 s.
- **No story that could end.**

**Long-run memory audit: passed.** It was run as the final iteration, once the look
was approved:

- The phrase was set to 8 beats with change chance 1.0, so the view changed every
  few seconds: 2,587 beats of views, drops, chords and breakdowns in the window.
- After warm-up, TouchDesigner's physical footprint (not RSS; see `debugging.md`)
  was sampled once a minute over two 8-minute windows:
  - **The second window read 1953 → 1953 MB: 0 MB/min.**
  - The first held at 1933–1934 MB, then stepped once by 19 MB in the same minute
    macOS compressed TouchDesigner. RSS fell from 1543 to 833 MB that minute. It
    was flat again after the step.
- The engine cooked 60 times a second throughout, with zero errors.

## What went wrong on the way

- **The spectrum CHOP ignored its output length.** Set to 16, it delivered 128
  samples, and reading the first 16 would have tuned every string to the bass. The
  engine now averages whatever arrives into 16 equal runs. The CHOP's samples are
  already log-spaced, so equal runs are log bands.
- **The Analyze TOP's "luminance" came back as r, g and b separately.** The limiter
  computes Rec.709 luminance from them itself.
- **The sonar didn't read as a wavefront.** The reveal is computed per segment
  midpoint, so long floor lines lit up all at once as the shell crossed their
  centre. Sonar-lit geometry is now cut into pieces no longer than the ping's width,
  and revealed lines get more teal and more alpha, so the shell draws as a
  travelling ring.
- **The first Rocky was a daddy-long-legs.** The carapace was too small and the
  legs too thin and too flat. He now has a bigger, taller dome, doubled legs arching
  up at the knee, and knuckle rings at hip and knee.
- **The Blip-A was a speck.** The camera orbited at 17 units, and the hall's
  distance fog, applied to space, erased the ship and the stars. Fog is now a
  per-view setting (none in space), the camera is at 10.5, and the hull keeps more of
  its ghost between pings.
