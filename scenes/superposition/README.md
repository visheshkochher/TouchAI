# Superposition

Schrödinger's cat sits in its box. Most of the time the box is closed, and the cat
inside is both alive and dead: two faint ghosts, one sitting and one keeled over,
flickering over each other while the box rattles on the kick. Then a bass drop lifts
the lid, the wavefunction collapses in a burst of kaleidoscope, and we see which cat
it is this time. It might be alive or dead. It might still be superposed, or be a
wave. It might be entangled with a twin, tunnelling through the wall, branching into
many worlds, or decohering into dust. Or we are the cat, looking up out of the box at
the giant eye of whoever opened it.

The drawing style is `bayou`'s: everything is a straight line, and every form repeats
one motif. The whole frame is a single instanced unit segment.

Build:

```python
code = open('scenes/superposition/build.py', encoding='utf-8').read()
g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
```

The builder is idempotent. It destroys and recreates `/project1/superposition` and
`/project1/superposition_out`, and touches nothing else. It needs no media files.

**`build.py` is generated**, as fathom's is. It is `superposition_template.py` plus
three verbatim blocks of `scenes/homestead/build.py` (the helpers, the audio front
end with tempo and drop detection, and the director), assembled by
`gen_superposition.py`. After editing the template, regenerate with
`python3 scenes/superposition/gen_superposition.py`.

## Keys

| key | does |
|---|---|
| 1-9 | jump to a quantum state (a seek, so the story plays on from there) |
| 0 | restart |
| o | **OBSERVE**: opens the box now. Once it's open, a second press collapses the state: the superposed cats snap to alive or dead for a few seconds, with a kaleidoscope flash |
| v | **POV**: the cat's point of view, in whatever state it is in (toggle) |
| k | **TRIP**: a kaleidoscopic hallucination, now |
| m | **HOLD**: keep the kaleidoscope turning (toggle) |
| n | **RESEED**: new worlds, new scatter |

## The nine states

Each state lasts `Storylen / 9` (40 s at the default 360 s), and the story loops. The
box starts closed. The first drop after 8% of the state opens the lid; if no drop
comes, it opens at 24%. It closes again at 93%.

| # | state | when the lid is up |
|---|---|---|
| 1 | ALIVE | the cat sits up out of the box. It blinks on the kick, twitches an ear on the accent, sways its tail on the bass, and its pupils open on the drop. A faint echo of it pulses outward on each kick |
| 2 | DEAD | a moment of superposed fuzz, then it keels over: X eyes, a tongue, the hammer down and the flask in shards. Its ghost rises out of the box, over and over |
| 3 | SUPERPOSITION | both cats at once, each doubled, trading brightness in a Rabi oscillation (one cycle every 8 beats). `o` collapses it |
| 4 | WAVEFUNCTION | both cats bent through a travelling wave field (bass is the amplitude), with the wave packet drawn over its head |
| 5 | ENTANGLEMENT | two cats, always opposite, joined by braided strands. An accent kick swaps them, at most once every 4 beats |
| 6 | TUNNELLING | the cat walks through the box wall. What crosses the wall is shredded, what gets through is faint, and a ghost of it bounces back |
| 7 | MANY WORLDS | every 4 kicks the tree splits again, up to 16 worlds, each cat alive or dead. The camera pulls back as it grows |
| 8 | DECOHERENCE | the superposed cat leaks into its environment and flies apart, while stray photons cross the box and the interference fringes fade. A drop snaps it back together |
| 9 | THE CAT'S EYE VIEW | inside the box: a lattice room, the Geiger counter, the flask and the atom. The cat looks around, and when the lid opens it looks up at the observer's eye. Its paws tap on the kick |

## The quantum states are operators on line drawings

Every state is a numpy function that takes an array of segments and returns a new
one. None of them is a feature of the cat:

- `_double` puts every segment in two places at once.
- `_wave` bends segments through one continuous wave field, so joints stay joined.
- `_tunnel` shreds whatever crosses the wall and mirrors a faint ghost back.
- `_scatter` sends each segment off on its own path.

Because they act on arrays, **the same operator applies to the cat's point of view.**
Press `v` in any state and you see the inside of the box *through* that state:

- superposition is double vision
- the wave wobbles the room
- entanglement mirrors it
- tunnelling shreds a band of the view
- many worlds puts several eyes in the opening
- decoherence scatters the whole room
- the dead cat's view is cold, dim and rolled onto its side

## Three coordinate spaces

- **LOCAL**: the cat's drawing plane. The base of the cat is at (0, 0) and a sitting
  cat is 1.0 tall. The operators act here.
- **BOX**: 3D, with the box as the cube [-0.5, 0.5]³. The box, the props and the eye
  live here. The cat's plane is billboarded into it, facing the camera.
- **SCREEN**: one numpy perspective projection, with near-plane clipping, takes
  everything to the ortho frame. The TD render is a flat 2D camera, and all the 3D is
  done in Python.

## The hallucination

A kaleidoscope pass (`kaleido`) folds the frame into N mirrored wedges **around the
cat's face**. The engine projects the face's position every frame, and in POV the
fold centre moves to the observer's eye. On top of the fold it adds:

- a swirl and a ripple that run outward from the fold centre
- a chromatic split along the radius
- a hue turn

The result is crossfaded over the plain frame. The fold count (3-8) and the hue jump
on every drop.

| signal | drives |
|---|---|
| tempo | the story clock, the Rabi oscillation, the tunnelling walk |
| kick | a short kaleidoscope (`Kickkal`); the closed box rattles; the cat blinks; the Geiger needle jumps and clicks; the atom throws off a decay; the POV paws tap; the many-worlds tree grows |
| accent | the ear twitch, and the entangled twins swap |
| drop | opens the lid (the schedule only arms it); a full kaleidoscope with a new fold count and hue; long trails; pupils dilate; decoherence snaps back |
| bass | the wave amplitude, the probability cloud behind the box, the strands |
| highs | the interference fringes, the whiskers, the fuzz on the ghosts |

A feedback trail (`trail`) takes the max of the new lines and the previous frame,
slightly zoomed and turned. It is short normally and long while a drop's kaleidoscope
decays. Because it uses max rather than add, it can never wash out to white.

## Performance

- **60.0 fps, with the engine cooking 60 times a second** (counted with
  `totalCooks`, not assumed). Measured in the editor, in the heaviest state: many
  worlds at 16 leaves (31 cats, 3483 lines) with the kaleidoscope held on.
- Engine: 2.2 ms per cook in the light states and 5.8 ms in many worlds.
- GPU: under 0.6 ms for every operator.
- `render_lines` shows 13 ms of CPU cook time in that state, without dropping frames.
  If a weaker machine drops frames, look there first.
- 74 operators, zero errors, zero warnings.
- The line pool is 12000 and never resized.

## Built to run all night

- **Script CHOP channels are built once**, then only written. That covers the
  engine, plus the director and tempo detector inherited verbatim from homestead.
- **Every list is hard-capped** and aged out: 12 atom decays, and 16 queued verbs.
  The environment photons and the ghosts follow fixed paths, so no list grows for
  them.
- **Every phase wraps**: the kaleidoscope turn, the Rabi phase, the walk and the
  eye's rotation. Shaders get story time, never `absTime`.
- **The story loops.**

**Long-run memory audit**, run as the final iteration once the look was approved, the
way `debugging.md` prescribes:

- The story was shortened to 45 s so it looped through all nine states and the seam.
- 3 minutes of warm-up, then TouchDesigner's RSS was read from outside once a minute
  for 7 minutes, with no bridge calls.
- Result: **1319.7 → 1320.4 MB, 0.10 MB/min**, flat. That is about 36 MB over a
  six-hour night.
- The run was real: over the whole window the engine cooked 35,579 times in 36,728
  frames, the story looped 15 times, and the engine logged zero errors.

## What went wrong on the way

- **A measured "59.9 fps" was an idle project.** The container's node viewer shows
  its *panel*, not `final_out`, so nothing pulled the chain: `totalCooks` did not
  move over 306 frames. The builder now sets the COMP's background TOP (`par.top`) to
  `final_out`, and fps was re-measured with a viewer open and the engine counted
  cooking at 60/s.
- **The first kaleidoscope folded around the frame centre**, so it turned the box
  edges into concentric rings and never repeated the cat. Folding around the
  projected face makes the mandala out of the cat.
- **`_xf(A, sx=-1)` flipped the entangled twin upside down**, because `sy` defaults
  to `sx`. Mirrors now pass `sy=1.0` explicitly.
- **On a Text TOP with `aligny='top'`, the position is an offset from the top
  edge**, so `positiony=0.935` put the readout off-screen. It is now `-0.065`.
- **The readout's text changes every frame** (the live amplitudes), and each change
  re-renders the Text TOP at about 6 ms. It now updates at most five times a
  second.
- **Keyboard In DAT rejects `.` and `,`** as key names, and warns. Next and previous
  state are pads on the custom page instead.
