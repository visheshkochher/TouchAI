# Monsoon

It is raining hard, someone is playing a harmonium in it, and everyone walks past.

A fixed camera on one street corner. The rain does not let up and he does not stop
playing; what changes is how many people are crossing, how hard it is coming down,
and how often the sky opens. Once in a while somebody stops.

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
| 1-8 | walk the story to a chapter and let it keep raining |
| 0 | restart |
| t | **THUNDER** — open the sky. The best single pad in the scene. |
| p | **PASSER-BY** — send someone across now |
| s | **SOMEONE STOPS** — the next person to reach him stops, listens, and gives |
| n | **RESEED** — a new street and a new crowd |

## The colour is the story

**The world is blue, the air is purple, and the only red in the frame is him.**

Everyone who passes picks up his lamp on the side facing him and loses it again on
the way out — `redk = exp(-(dist/0.62)^2) * 0.72`, one expression, and it is the
entire point of the piece. Someone who *stops* keeps it. On a thunderclap the city
behind goes dark against a lit sky while he stays warm, because his light is the only
one in the scene that is not the weather.

Brightness is deliberately mid — the background alone sits near 0.13 luminance and a
typical frame measures **0.18–0.21 mean**, where `bayou` sat at 0.02–0.04. A scene
that is mostly black reads as cheap on a large screen and vanishes next to fifteen
others on a switch.

## Built for a switch, and measured

This is one tox among sixteen, so what it costs when **nobody is looking** mattered
more than what it costs when they are.

| | `bayou` | `monsoon` |
|---|---|---|
| TOP textures | **87.9 MB** / 15 TOPs | **39.1 MB** / 7 TOPs |
| ×16 scenes resident | 1.37 GB | **0.61 GB** |
| CPU (all numpy) | 1.1 MB | **0.24 MB** |
| Engine, headless mean | 1.33 ms | **0.50 ms** |
| Live fps, rendering | 60.0 | **60.0** |
| Off-screen, viewers off | 0 ops cooking | **1 op** (the timer) |

Three decisions got the 56%:

**One shader does everything that is not a line.** The sky gradient, three sheets of
rain, the wet street and its haze, the lamp's pool on the road, the lightning flash,
the composite of the rendered lines, the glow add, the chapter label, the grade and
the vignette are a single GLSL TOP. `bayou` spent eleven full-res `rgba16float` TOPs
on the same work, several of them pure pass-through.

**The rain is in two places on purpose.** The *volume* of it is procedural in the
shader, where a million drops cost what one costs. Geometry is only the near streaks
that must pass in front of people and the splashes that must land on the actual
street line — 330 streaks and 44 splash sites. Drawing the whole downpour as
instances is how you spend an eight-thousand instance pool on drizzle and still have
it look thin.

**A fixed camera means there is no world to store.** No static terrain array, no
parallax layers, no culling structure. The entire persistent state is a 267-segment
city, four small rain arrays, and a list of at most eight people: 37 KB.

### There is no `executeDAT` keep-alive, and that is the point

`bayou` has a frame-start callback whose comment claims it keeps the scene running
off-screen. It does not — `.cook()` without `force=True` on a chain nothing is
pulling is a no-op — and it is just as well, because sixteen scenes each force-cooking
an engine every frame is how a switch rig loses 60 fps to scenes nobody can see. This
scene does not pretend: TD is pull-based, unselected it costs one timer CHOP, and its
clock resumes where it left off when you cut back to it.

**Operational note for the rig:** with the network editor displaying the tox's
internals, TD pulls the node thumbnails and **30 of the 54 ops cook at about 5 Hz**
even unselected. Measured. Keep the editor out of the tox, or run in Perform mode, or
sixteen scenes will each idle at that rate while you are patching.

## How the story works

Eight chapters on a wrapping clock (default 240 s). **None of them is an empty
stage** — a switch can land on this scene at any moment of a set, so every chapter is
already raining and he is already playing. The arc moves how hard, how many, and how
often, never whether.

| # | chapter | what changes |
|---|---|---|
| 1 | First Drops | light rain, a few people |
| 2 | It Sets In | it builds |
| 3 | The Crowd | the pavement is busy and quick |
| 4 | Thunder | heavy rain, the sky opens often |
| 5 | The Downpour | the peak of it |
| 6 | Someone Stops | the odds of a listener rise sharply |
| 7 | Alone, Playing | the street empties; he does not stop |
| 8 | It Eases | rain falls off, purple afterlight |

The playhead **wraps** rather than clamping, unlike the journey scenes: there is no
destination on this corner — it is the same rain at minute forty as at minute four —
so a clamp would just mean the arc dies mid-set.

## Audio

Same proven front end as `as_above` and `dispersal` (adaptive band normalisation,
autocorrelation tempo with harmonic sum and octave fold, sustain-based drop
detection).

| signal | drives |
|---|---|
| tempo | musical time, and **the bellows**: he pumps once every two beats, phase-locked |
| bass **drop** | opens the sky — a fork of lightning, a 55 ms flash, and a 1.4 s purple afterglow |
| bass | rain density, wind, how far the figures lean into it, haze on the road |
| energy | the drone bands rising off the harmonium, glow |
| highs | rain landing on his head and shoulders, splash brightness |
| kick | line width, lamp flicker, the red on his shoulders |

**The flash and the afterglow are two different clocks**, and getting that wrong is
what makes stage lightning look like a dimmer. The strike is gone in a tenth of a
second; the violet it leaves in the air takes a second and a half. One envelope
cannot be both.

Thunder does not *only* follow the music: away from a drop the storm still fires on
its own timer at a rate set by the chapter, so a quiet passage is not a calm sky.

## What went wrong, and what it cost

**Seven people were on the street and none of them could be seen.** The figures are
built at local height 1.0 and the lane scale *is* their height in world units — but
the frame is only 1.125 tall, and the near lane was set to 1.16. Every passer-by was
a pair of legs the size of the whole screen, reading as more rain. Lanes are
0.22/0.30/0.42 now.

**Then the rain drowned them anyway.** Three shader sheets were adding ~0.4 of
luminance across the entire frame — more than the figures themselves contributed.
The sharp near streaks are geometry and composite *over* the sheets, so the shader
only has to carry the volume of the rain; it does not have to be the brightest thing
on screen. Halved.

**Both of those were invisible in the preview and obvious at full resolution.**
`observe` returns 480×270 regardless of the real output, a 2.67× downscale, and a
far-lane figure 50 px tall becomes 19 px of noise. Three passes were spent tuning
things that were already correct. Saving the TOP to a file and reading that back is
what found it — and it is also the only way to capture a 55 ms lightning flash, which
has decayed to nothing by the time a second tool call arrives.

**`bayou` shipped with `antialias='msaa4x'`, which is not a valid menu name.** TD
accepts an invalid menu value silently and lands on entry zero, so that scene has
rendered with *no* multisampling for its entire life; the real names on this build
are `aa1 … aa32`. This scene asserts the value against `menuNames` and prints what it
actually got.

**A pad cannot drive a 55 ms envelope.** The performance pulses queue through a
`parameterexecuteDAT` and land on the *next* frame, so pulsing `Bolt` and cooking in
the same call captures a flash that has not happened yet. For capture, drive the
state directly.

**The bellows fanned backwards into the box** and read as sound rather than as a
bellows. Pleats are now shallow Vs spanning the gap between the lifted flap and the
box top, bulging when it is up and flattening when it comes down.

## Known debt

- The audio front end is inlined here for the **ninth** time. Nine scenes carry the
  same 270 lines. On a sixteen-tox rig the right answer is one shared analysis COMP
  at project level that every scene reads by path — it would also drop the per-scene
  Audio Device In, which is the only thing besides the timer that ticks off-screen.
  This scene did not stop to do it either.
- `final_out` / `out1` / `monsoon_out` are three full-res pass-throughs, 21 MB of the
  39. They are the repo's output-rig convention and the other fifteen scenes follow
  it, so they stayed. Dropping the null and pointing `out1` straight at `post` saves
  7 MB per scene, 112 MB across the rig.
- Not yet done: an uninterrupted full-length pass at the default 240 s with a real
  set playing, and a soak with all sixteen scenes loaded. Verified instead as a
  900-frame headless pass over the whole arc plus **60.0 fps measured live** (1051
  frames over 17.52 s of wall clock with the scene rendering, 7 people on screen,
  1170 lines, 124.1 BPM detected).
