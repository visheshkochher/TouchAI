# Homestead

A poor man walks out of the forest with everything he owns tied in a cloth on a stick,
and by the next morning there is a house on the riverbank that feeds and lights itself.

One fixed camera looks across a river at a wild far bank, and one day passes over the
story. He arrives at dawn while two deer drink on the far bank and bolt. He clears the
ground in the morning and raises bamboo stilts against the flood. At noon he walls the
house in bamboo and mud, and he gets the thatch on just before an afternoon shower. He
builds a water wheel on the bank and plants seeds in the golden hour. At dusk he throws a
switch and the wheel lights a bulb under his eave. Then the owl, the fireflies and a fox
come to the edge of the light. The last chapter is the next dawn: smoke from the chimney,
tomatoes ripe, and the deer come back to drink, this time with a fawn.

Build:

```python
code = open('scenes/homestead/build.py', encoding='utf-8').read()
g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
```

The builder is idempotent. It destroys and recreates `/project1/homestead` and
`/project1/homestead_out`, and touches nothing else. It needs no media files: the test
track is the one TouchDesigner ships.

## Chapters and keys

| key | chapter | time of day |
|---|---|---|
| 1 | Nothing But the River | dawn: he walks in, the deer leave |
| 2 | Clearing the Ground | morning: machete, the plot spreads, a log pile |
| 3 | Stilts Against the Flood | posts, bracing, floor, ladder |
| 4 | Bamboo and Mud | noon: slats left to right, mud plaster, window, door curtain |
| 5 | Thatch Before the Rain | on the platform, five courses of thatch; the shower; a heron |
| 6 | The Water Wheel | afternoon: frame, spokes, rim, paddles, generator, pole, wire |
| 7 | Seeds | golden hour: fence, rows, 21 plants that keep growing |
| 8 | First Light | dusk: he throws the switch; bulb, window glow, owl, fox, fireflies |
| 9 | Home | the next dawn: cup of tea, smoke, harvest, the deer return |
| 0 | restart | |
| g | **GUST**: wind through the grass, and the birds go up out of the tree | |
| f | **FISH**: one jumps | |
| n | **RESEED**: a new wilderness around the same house | |

A chapter jump is a **seek**, not a freeze-frame, so the story plays on from wherever it
lands. `Story Length` (default 300 s) can be changed live: everything is driven by the
story *fraction*, so changing it never makes anything jump.

**It loops, for all-night runs.** With `Loop the Story` on (the default), the finished
homestead fades through black (about 3 s out, 3 s in) back to the empty riverbank, and
`Loops Completed` counts the cycles. With it off, the story clamps at the end and holds
on the last morning.

## Built to run for hours

Nothing in the scene can grow past one story length:

- **Phases reset at the seam.** The river's flow phase, the cloud drift and the wheel
  angle are integrated, so they would otherwise grow for as long as the scene runs.
  The shader samples noise at them in 32-bit float, and after hours the ripples and
  clouds would go visibly blocky. All three return to zero inside the black at every
  loop seam, and the wheel angle is also kept modulo 2π.
- **The shader's clock is story time**, not raw time, so it also returns to zero each
  loop.
- **Every list is hard-capped** (particles, smoke, rings, fish, birds), and the tempo
  detector's histories are fixed-length.
- **Channels are published with `copyNumpyArray`**, so no Python lists are built per
  frame.
- **Script CHOP channels are built once, then only written.** Rebuilding them every
  frame with `clear()` + `appendChan()` leaks native memory inside TouchDesigner: about
  2 MB a minute, ~760 MB over a six-hour night. Python's object count and GPU memory
  both stay flat, so only the process's memory shows it. This applies to the engine,
  the director and the tempo detector (details in the skill's `debugging.md`). With the
  fix (measured on this scene, running with the story looping every 45 s), memory
  grew by only **0.14 MB/min** over 7 quiet minutes, ~50 MB over a six-hour night.
  Rebuilding the channels every frame had leaked ~2 MB/min.

Soak test (story set to 45 s so it loops quickly, 2 minutes, 3 loops): Python objects
held flat at ~69k, the scene's GPU memory held at 64.8 MB, every list stayed small, and
every phase went back to ~0 at each loop.

## Light: dim days, a pastel sun, a moon that breathes

- **Daylight is kept dim and slightly warm.** The frame is never bright. What says
  "day" is the sun's position: it rises out of the dawn mist on the left, peaks just
  under the top of the frame at noon, and sets on the right at dusk.
- **The sun is a soft pastel disc**, peach at dawn and pale apricot at noon. It sits
  below full brightness and has a soft painted edge. It **glows to the beat, gently**:
  the kick lifts its halo and the disc by a few percent, never to a flash.
- **The moon glows to the beat at night**, a cool halo that breathes with the kick.
- **The stars are only in the top half of the frame**, fading in toward the top, so
  none sits over the hills, the jungle or the land. The green points that blink low
  over the grass at night are fireflies.
- **The camera is zoomed in** (1.6 world units across instead of 2.0) and framed low,
  and he is drawn 20% larger, so he stands about 200 px tall in a 720p frame instead
  of 138.

## Cartoon and realism, split by what things are

- **Painted realistically** in one GLSL shader (`world`), with a real day/night cycle:
  - the sky, the sun and its haze, and clouds lit from the sun's side;
  - two mountain ranges in aerial perspective, lit on their slopes that face the sun;
  - the far jungle's treeline, with mist lying on it at dawn, at dusk and after rain;
  - the river, with perspective ripples, reflections of everything above it, sun
    glitter, moon glitter and shoreline foam;
  - the near bank, with grass and a dirt clearing that grows with the story;
  - stars, the moon and the rain.
- **Drawn as flat cartoon cels** (one instanced quad primitive, as in `monsoon`):
  everything that lives or is built. That means the man, the house, the wheel, the
  garden, the animals, the grass and reeds, and the big tree.
- **Tied together by light.** The cels are multiplied by the same ambient colour the
  shader uses at that sun height. Each cel's lit edge is on whichever side the sun is.
  They throw contact shadows onto the painted ground by day, and at night the bulb's
  warm falloff lights both layers.
- **Water is one rule.** Every cel row can carry its own waterline. Anything above it is
  mirrored into the river with a shimmer, and anything below it is dimmed and tinted.
  This is how the wheel, the heron, the reeds, the deer and the jumping fish get
  reflections without any of their drawing code knowing about water.

## Audio: in the pace, not the brightness

| signal | drives |
|---|---|
| tempo | musical time is the story clock, phase-locked to the beat |
| energy | how fast the **water wheel** turns, the **river** flows and the **clouds** drift (integrated, so these change speed and never jump) |
| kick | his **hammer / machete / seed** lands on the beat (wood chips, cut grass, soil), and smoke puffs from the chimney |
| kick while sitting | his head nods to the beat |
| kick (sky) | the sun's halo swells gently; at night the moon's halo does |
| accented kick | now and then a fish jumps (at most once every 7 s), and the heron strikes (at most once every 5 s) |
| bass | grass, reeds, tree canopy and garden sway |
| highs | how fast fireflies blink, sun glitter on the water, star twinkle, wingbeat rate |
| drop | a gust through the grass, and a flock goes up out of the tree |

The wet afternoon also runs the river faster for a while after the rain, and the wheel
speeds up with it.

Measured live on the test track: 124.1 BPM detected, story time advancing 1:1 with the
clock, about 2.4 kicks per second, and wheel speed tracking energy from 1.26 to
2.09 rad/s.

## Performance

- Measured before the camera zoom: **60 fps locked in perform mode**: median frame period 16.67 ms (p90 17.9 ms). With
  the network editor open it is 17.1 ms.
- The engine costs **2.4 ms** per cook (timed with 60 forced cooks) and the world
  shader 2.2 ms on the GPU. The scene has 58 operators, with zero errors and zero
  warnings.
- 6–9.5k instances are live out of a fixed pool of 12,000.
- The tree and the framing leaves are built once at fine slab resolution and only swayed
  per frame. Filling round shapes in Python every frame used to cost 5 ms and still
  stair-stepped.
- The channels are published with `copyNumpyArray`, not by building Python lists.
- The label text TOP costs ~8 ms, but only on the one frame when the chapter changes.

## What went wrong on the way

- **A bare `../` in `instanceop` rendered one giant grey quad.** The geometry COMP
  resolves `instanceop` and `material` from its own parent, so the bare name is right
  (as in bayou); `'../engine'` silently failed to instance and drew the unit quad at
  full size.
- **Depth came from where he stands, which hid him while he thatched.** Standing on the
  platform puts his feet *behind* the wall in depth, so the wall drew over him. While
  he is up there, his depth is overridden to sit just in front of the house.
- **A per-channel tonemap turned the midday sun salmon.** A shoulder applied to R, G and
  B separately compresses each by a different amount. The shoulder now works on
  luminance, and the sun has a white-hot core.
- **Parts at the very end of a stage never finished appearing.** Progress stops at 1.0,
  so a part with a threshold of 0.995 stayed at 14% alpha forever (the rain barrel, the
  downspout). Once a stage completes, every part in it is fully in.
- **"Accented" is most kicks on this track** (107 of 136), so anything triggered by
  accents needs its own rate limit.
