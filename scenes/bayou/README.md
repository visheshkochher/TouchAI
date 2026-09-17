# Bayou

An alligator walks out of a swamp and into a lake, and keeps stopping because the
world will not stop being interesting.

One continuous side-on journey, left to right, for the whole set. He never turns round
and there is never a cut: the camera is locked to him and the swamp scrolls past.
Seven times on the way he finds something, and each time he **stops**, turns his head,
rears, and his eye opens into rings.

```
SWAMP -> fern -> dragonfly -> turtle -> heron -> lilies -> shoal -> LAKE
```

The stopping is the piece. A creature that walks the whole way is a screensaver; a
creature that keeps being stopped by what it finds is a character.

Build:

```python
code = open('scenes/bayou/build.py', encoding='utf-8').read()
g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
```

Idempotent — destroys and recreates `/project1/bayou` and `/project1/bayou_out`, and
touches nothing else. No media files.

## Keys

| key | does |
|---|---|
| 1-9 | walk him to a chapter and let the journey keep playing |
| 0 | restart |
| l | **LOOK** — make him notice, wherever he is. Hold it under a breakdown. |
| g | **STARTLE** — a gust: everything bends, and a flock goes up off the far bank |
| n | **RESEED** — a new swamp. Same journey, nothing repeats. |

A chapter jump is a **seek**, not a freeze: `show = musical clock - Timeoffset`, so
jumping to T is one parameter write and the walk carries on from where it lands.

## Three ideas, and everything else follows

**Everything is a straight line, and every form is one angular motif repeated.** The
back is a row of triangles. A reed is a shaft with a chevron ladder. A cypress is a
rigid symmetric fractal. A turtle is a hexagon of hexagons. The lilies are hexagons
repeated outward; the moon is n-gons repeated inward; amazement is a rotating n-gon
leaving the thing he is looking at. Nothing in the frame is drawn with a curve. That
is the aesthetic and it is also why it runs at 60 fps: the whole scene is one
instanced unit segment with a per-instance transform.

That the seven creatures share a vocabulary is the point, not a shortcut — a fern, a
dragonfly's wing and a lily pad rhyme because they are all lattices, and a swamp that
rhymes with itself is a place rather than a set of props.

**The waterline is one rule, not a feature.** A single horizontal world y. At the very
end of the frame, every segment below it is dimmed, pushed cyan and sheared sideways
by the local surface displacement; every reflectable segment above it is mirrored
through it with a moving shimmer. One rule, applied to every segment in the scene, is
what makes wading work: as the bank falls away his legs go quiet, then his belly, and
by the lake only the ridge and one eye are still bright. **Nothing in the animal code
knows that water exists.**

**The swamp is static and the animal is not.** 6683 line segments of reeds, cypress,
vines, bank, strata and lilies are built once into numpy arrays covering 24 world
units, then per frame only translated by the camera, culled by a binary search over a
sorted key, swayed on the bass, and emitted. The alligator — about 150 segments — is
rebuilt in Python every frame, because he is small enough that Python is the right
tool and the legibility is worth it.

## The walk is derived from the schedule, and cannot disagree with it

There is no animation curve for his position. A speed profile is built from the
discovery table alone — 1.0 everywhere, dipping to 0.045 across each dwell — and
integrated once at load into a 3001-sample table of **distance against story
fraction**. Moving a discovery moves the walk with it.

Because distance is a function of *fraction* and not of seconds, `Journey Length` can
be swept live, from 90 s to 40 minutes, without the animal teleporting — and a
checkpoint seek lands him at exactly the right place on the bank every time. It is
also how this was iterated: set `Storylen` to 2400 and a dwell lasts two minutes of
wall clock, with the frame pixel-identical to the same moment at 330.

His body rides the bank **smoothed over his own length** (five samples across 0.5
world units) and pitches with its slope, so he goes over the mud ridges instead of
through them. The feet are solved in world space with two-link IK against the same
`ground()` function the bank geometry is drawn from — there is no terrain array
anywhere, so the feet and the bank cannot disagree.

## The music fires the discovery; the schedule only arms it

Each discovery arms a window around its dwell. The first detected **bass drop** inside
that window reveals it — the n-gons burst, the creature blooms out of a faint
geometric ghost, and he rears. If the track never drops, it fires at the end of the
window anyway, so the story cannot stall. `Drops Reveal the Discovery` turns this off.

| signal | drives |
|---|---|
| tempo | musical time; the whole journey runs on beats, phase-locked to the grid |
| kick | a ripple ring dropped in the water **under his stance foot**, ring amplitude on `beatstr` |
| accented kick | another n-gon of amazement thrown off whatever he is looking at (rate-limited to 0.42 s, or they sum into a constant glow) |
| bass | reed sway, surface chop, horizon haze, line width, ink |
| highs | motes, wing-beat rate, surface glints, the fine filigree |
| drop | reveals the discovery; gusts the reeds; the triangular lattice surfaces in the background; chromatic shear |
| `g` pad | the same gust plus a flock, at any point in the set |

Measured live on the test track: **124.1 BPM** detected against a 124 reference, story
time advancing at **0.990×** wall clock over a 20.7 s window, 50 kicks and 3 drops in
that window, line width swinging 1.40 → 1.53 px on the beat.

## Amazement has to read from the back of the room

The first pass had him turn his head, and it was invisible. What reads:

- **he rears** — the body pitches up 0.11 rad with the amazement. One gesture, whole
  silhouette.
- **the swamp steps back** — every static segment dims by 30%, so the warm thing is
  the only thing in frame that got *brighter*.
- **the ridge lights warm** — a crest travels head-to-tail along the scutes. It is the
  only place in the piece his colour changes.
- **the eye opens** — a diamond that grows 2.4× and gains two counter-rotating
  hexagons, the same n-gons the discovery is throwing off, at a tenth the size.
- **his jaw drops** — a 0.14 rad gape, hinged properly at the back of the skull.

The swamp is cold and the amazement is warm, and that is the entire colour idea.
Nothing warm happens except where he is looking.

## Performance

**60.0 fps measured**, 71 operators, zero errors and zero warnings. Engine 2.17 ms per
cook; void 0.8 ms GPU, scene composite 1.45 ms GPU. 1900–2332 line instances live out
of a fixed pool of 5000 — the pool is never resized, and unused instances get zero
length and zero alpha.

Emission order is the story: the animal goes in first, then what he is looking at,
then the amazement, then the water, then the swamp, then reflections and air. If the
pool ever ran dry it would be the far bank that vanished, never him.

Verified at full resolution rather than from the downscaled preview: 23.6% of pixels
lit, and the band *below* the waterline is 21.2% lit — the bottom of the frame is
water and earth, not void.

## What went wrong, and what it cost

**"Below the waterline" is not the same as "in the water".** The rule keyed on
absolute y, so the bank strata — earth, drawn in section under a mud bank that is
*above* the water — were dimmed cyan and faded to nothing, and the lower third of the
frame was a black band for three passes. Submerged is now `below the line AND above
the bank`, one extra `ground()` call on the midpoints.

**The chromatic shear was on almost all the time.** `Shock` was wired straight to
`dropenv`, which sits well above zero for most of a track. At a 4-pixel offset on a
3-pixel mote that is not an aberration, it is full colour separation: the drifting
motes rendered as red, green and blue crosses. `dropenv ** 4` and a 0.55 default.

**A creature dimmed by the wonder ramp twice, then by the water, is invisible.** Every
generator receives an ink that already carries the reveal envelope; the shoal
multiplied by it again and then sat below the waterline, so at full amazement it
rendered at alpha 0.044. It was not a bug that raised anything — the frame was simply
empty where a shoal was supposed to be.

**A reed as tall as he is reads as camouflage.** The first bank was uniform-random in
height and dense enough that the animal disappeared into his own scenery. Heights are
biased short (`0.065 + 0.245 * random() ** 1.9`) and the clumps thinned; the one thing
the frame must never lose is the animal.

**A folded wing drawn as a fan reads as a starburst stuck to a bird.** The heron's
nine rays at a 40° spread looked like an explosion on its shoulder. Folded they now
lie nearly parallel along the back and only fan when it goes.

**A leg drawn to an unreachable target visibly stretches**, and one stretched leg reads
as a broken rig. The IK pulls the foot back inside reach rather than leaving it where
the gait asked for it.

**Mist bands at even spacing and even length are rulers, not mist.** Four of them
across the frame read as scan lines. Dash length, wobble and alpha now vary per dash
off a cheap integer hash.

## Known debt

The audio front end is inlined here for the **eighth** time (dispersal, painter, maya,
residue, rhizome, tunnel_drive, as_above, bayou). Eight scenes carry the same 270
lines, so a fix to the drop detector is eight edits. `as_above` named this debt and
said the next scene should fix it; this scene did not either. It should be one shared
`.tox` every scene references.

Not yet done: an uninterrupted full-length pass at the default 330 s with a real set
playing. Verified instead as a 900-frame headless pass over the whole story (clean,
1.33 ms mean per engine cook) plus live inspection at every chapter at `Storylen`
2400.
