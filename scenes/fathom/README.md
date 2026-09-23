# Fathom

The man from `homestead` puts a glass jar over his head, ties his lantern to his waist,
and dives off his own riverbank. He goes down through the sunlit shallows, a kelp
forest, a coral garden, and the twilight zone where the jellyfish drift. He passes a
whale, goes into the abyss and reaches the hot vents on the sea floor. Then a burst of
bubbles carries him home, and he surfaces by his house at golden hour and climbs out.

**The view is a cross-section**, side-on like homestead. The water surface is one line
and the bank drops away beneath it. The camera follows him down while the world scrolls
past (as in bayou). Everything he meets is a flat cel with a hard shadow side and a
bold outline: the same primitive, and the same man, as homestead.

Build:

```python
code = open('scenes/fathom/build.py', encoding='utf-8').read()
g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
```

The builder is idempotent. It destroys and recreates `/project1/fathom` and
`/project1/fathom_out`, and touches nothing else. It needs no media files.

**`build.py` is generated**, as voyage's is. It is `fathom_template.py` plus verbatim
blocks of `scenes/homestead/build.py` (marked `BEGIN/END HOMESTEAD`), assembled by
`gen_fathom.py`:

- The blocks are: the helpers, the audio front end, the tempo detector, the director,
  the cel primitives, **the side-view man himself**, his house and tree, the render
  setup, and the painted sky shader.
- The generator also adds three poses to homestead's man in place: `swim` (a stroke on
  the kick), `dive` and `tread`.
- After editing either file, regenerate with `python3 scenes/fathom/gen_fathom.py`.

## Chapters and keys

| key | chapter | what happens |
|---|---|---|
| 1 | The Edge of the Water | a dim morning on his bank: the house, the tree, the reeds. He looks out over the river, puts the jar on his head, and dives |
| 2 | Into the River | sunlit shallows: sea grass, pebbles, light shafts, caustics on the bed, a school of minnows |
| 3 | The Kelp Forest | tall kelp swaying from the root (some in front of him), with a sardine school swirling through it |
| 4 | The Coral Garden | fan, brain, tube and staghorn corals, anemones with a pair of clownfish, reef fish, a sea turtle gliding over |
| 5 | The Twilight Zone | the shelf drops away into open water; glowing jellyfish **pulse on the kick** |
| 6 | The Whale | a humpback passes slowly behind him |
| 7 | The Abyss | black water, bioluminescent sparks, an anglerfish with a flickering lure, rainbow comb jellies, glowing sea pens |
| 8 | The Deep Vents | smoking chimneys with hot cracks, red tube worms that **snap into their tubes on the kick**, crabs, a dumbo octopus |
| 9 | Back to the Light | he rises; a curtain of bubbles carries him home; he surfaces by his bank at golden hour, swims to the edge and climbs out |
| 0 | restart | |
| b | **BUBBLES**: a burst from his helmet | |
| n | **RESEED**: a new sea | |

A chapter jump is a **seek**. The story **loops** through black when `Loop the Story`
is on, which is the default.

## The realism is in the water

- **Water eats colour with depth.** Every cel is lit by the surface light attenuated
  per channel by its own depth: red goes first, then green. Shallows are teal, the
  coral garden is already muted, and the abyss is black.
- **His lantern is the only warm light down there, and it gives back the true colours**
  of whatever it falls on. Tube worms, his shirt and the whale's belly regain their
  colour as he passes.
- **The water column is painted.** The shader draws a depth gradient to black, the
  bright underside of the surface, slanting light shafts, caustics dancing on a shallow
  bed, marine snow drifting in the current, hazy rock silhouettes at half parallax,
  bioluminescent sparks in the abyss, and warm light scattering around his lantern.
- **The sea bed is one table** (`FLOOR_X/FLOOR_Y`), interpolated identically by the
  shader and the engine, so every plant is rooted exactly on the painted floor. The
  shelf edge after the reef is where the floor falls away into open water.
- **Above the surface is homestead's painting**: his bank, the river running to the far
  jungle, and the pastel sun, which glows on the beat.

## Audio

| signal | drives |
|---|---|
| tempo | musical time is the story clock |
| kick | his **swim stroke**; the jellyfish bells pulse; the tube worms snap back; a puff of bubbles from his jar; his nod on the bank |
| energy | the **current**: how fast the schools circle, the marine snow drifts and the plants sway (integrated, reset at the seam) |
| bass | how far the kelp, sea grass, anemones and whips sway |
| highs | the bioluminescent sparks, the anglerfish's lure, the comb jellies' rainbow |
| drop | a flash of fish darting past him |

## Built to run all night

It follows the long-run rules in the skill's `debugging.md`:

- **Script CHOP channels are built once**, then only written: the engine here, and the
  director and tempo detector inherited from homestead.
- **Every list is hard-capped** and aged out: bubbles 260, splash drops 40, vent smoke
  30, fish darts 2.
- **The current resets at the loop seam**; the swim phase wraps.
- **The shader's clock is story time.**

**Long-run memory audit**, run the way `debugging.md` prescribes: story shortened to 45 s
so it loops, 3 minutes of warm-up, then TouchDesigner's process memory read from outside
once a minute for 7 minutes, with no bridge calls. The result was 1545.4 → 1545.9 MB,
**0.07 MB/min**: about 30 MB over a six-hour night, and flat.

## Performance

- **60 fps locked in perform mode** (median frame period 16.66 ms, p90 16.71 ms,
  measured in the reef and the abyss).
- The engine costs **1.2–2.6 ms** per cook in every chapter (timed with 60 forced cooks
  after the chapter has been running).
- 58 operators, zero errors, zero warnings.

Two optimisations did most of that:

- **Small fish are one fat stroke plus a two-slab tail**, not a filled polygon. A school
  of thirty filled polygons had cost ~5 ms a frame.
- **The sea bed is sorted by x once**, so each frame takes its slice near the camera
  with a binary search. Tube-worm plumes are plain strokes rather than outlined limbs.

## What went wrong on the way

- **The turtle, anglerfish and octopus came out enormous and on top of him.** Creature
  scales are now set against his height, and their positions are ahead of him in his
  path.
- **The whale was placed in world space and only a fin tip crossed the frame.** It is
  now placed against the camera, so it always crosses the frame behind him.
- **Jellyfish lit like everything else vanish at depth.** They are bioluminescent, so
  their bells and tentacles emit instead of reflecting.
