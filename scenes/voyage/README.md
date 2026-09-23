# Voyage

The man from `homestead` takes his bamboo raft off the river one night. He flies out
past the Moon, a ringed giant, a comet, a nebula and a spiral galaxy, and comes home
through the dawn clouds to land on the river by his house.

**The camera is behind him.** We see the back of his head: the faded red cloth knotted
at his nape, with its tails fluttering down his back. We also see the path forward.
Everything he flies toward sits at one vanishing point just above his head. It grows as
he approaches, then slides past to the side, and the stars and space dust stream
outward past him. The audience travels with him rather than watching him travel.

Build:

```python
code = open('scenes/voyage/build.py', encoding='utf-8').read()
g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
```

The builder is idempotent. It destroys and recreates `/project1/voyage` and
`/project1/voyage_out`, and touches nothing else. It needs no media files.

**`build.py` is generated.** It is `voyage_template.py` with verbatim blocks of
`scenes/homestead/build.py` spliced in (marked `BEGIN/END HOMESTEAD`): the helpers, the
audio front end, the tempo detector, the director, the cel primitives, his house and
tree, the render setup, and the painted sky/hills/jungle shader library. After editing
either file, regenerate with `python3 scenes/voyage/gen_voyage.py`. A fix that belongs
to both scenes goes in homestead, and then you regenerate.

## Chapters and keys

| key | chapter | what happens |
|---|---|---|
| 1 | Lift Off | night on the river, the house's window and bulb lit on the left bank; he waves goodbye as the raft rises |
| 2 | Through the Clouds | the land falls away, moonlit cloud banks, the sky dissolves into space, and the Earth's glowing limb curves below |
| 3 | Sunrise Over the Earth | he sits on the deck and watches a pastel sun come up over the limb |
| 4 | The Moon | the Moon grows ahead and slides past on the right; he waves |
| 5 | The Ringed Giant | a banded planet with rings passes on the left; he has a cup of tea |
| 6 | A Comet | it crosses the sky with an ion tail and a curved dust tail; he points at it with whichever arm is on its side |
| 7 | Where Stars Are Born | he flies into a pastel nebula, with young stars inside it |
| 8 | The Spiral | a galaxy grows ahead; he just sits |
| 9 | Home | the blue marble grows from a dot; he braces through re-entry, then descends through dawn clouds and lands on the river, sailing into the sunrise toward his house |
| 0 | restart | |
| s | **SHOOTING STAR** over the top of the frame | |
| n | **RESEED** new grass and trees on the bank | |

A chapter jump is a **seek**. The story **loops** through black (about 3 s out, 3 s in)
when `Loop the Story` is on, which is the default.

## Same style as homestead

- **The character is homestead's man, turned round**, drawn as the same flat cel
  primitive: a patched shirt with a torn hem, the grey dhoti, thin limbs, and the red
  head-cloth. From behind, the head-cloth is the whole portrait.
- **Poses ease into each other** (hip height and both arm angles are interpolated), so a
  change of pose is a movement, not a cut.
- **The raft is drawn in perspective.** Seven bamboo poles run toward the vanishing
  point, with lashings, the cut pole ends facing us, and his bundle tied down. A short
  mast carries a patched pennant and the lantern, which is the bulb from his house in a
  little cage.
- **The painted world is homestead's shader**, verbatim, seen looking up-river. The
  river's water is homestead's water, turned to face away from us.
- **Space is painted in the same register, dim and pastel.** The Earth is a lit sphere
  with continents, clouds and an atmosphere rim, and a few warm town lights on its night
  side. The Moon has maria and craters that catch the light. The ringed giant has bands,
  and its ring passes behind and in front of the planet. The comet, the nebula with its
  dust lanes and the spiral galaxy are all procedural.
- **The lantern is always the warmest thing in the frame.** It lights him from its side
  in every chapter.

## Audio

| signal | drives |
|---|---|
| tempo | musical time is the story clock |
| energy | how fast he flies: how fast the stars stream and stretch, and how much space dust passes (integrated, so the speed changes and nothing jerks) |
| kick | a gentle breath of glow in the lantern, the sun and the moon; his head nods when he is sitting |
| bass | his head-cloth tails and the pennant flutter, and the raft bobs |
| highs | star twinkle, glitter on the river |
| drop | a shooting star |

## Built to run all night

- **Phases reset at the loop seam.** The flight phase (star streaming, river flow,
  cloud drift) and every particle list go back to zero inside the black.
- **The shader's clock is story time**, so it also returns to zero each loop.
- **Lists are hard-capped**: space dust at 70, shooting stars at 3, re-entry plasma at 60.
- **Channels are published with `copyNumpyArray`**, so no Python lists are built per
  frame.
- **Script CHOP channels are built once, then only written.** Rebuilding them every
  frame with `clear()` + `appendChan()` leaks native memory inside TouchDesigner: about
  2 MB a minute, ~760 MB over a six-hour night. Python's object count and GPU memory
  both stay flat, so only the process's memory shows it. This applies to the engine,
  the director and the tempo detector (details in the skill's `debugging.md`). With the
  fix, TouchDesigner's memory was flat over 4 quiet minutes: **0.02 MB/min**.

Soak test (story set to 45 s, 2 minutes, 5 loops): Python objects flat at ~68.4k, GPU
memory flat at 64.8 MB, dust at its cap, and the flight phase back to 0 at every seam.
That soak missed the real leak, which only showed in the process's own memory
measured over a longer quiet window. It is now fixed (see above).

## Performance

- **60 fps locked in perform mode**: median frame period 16.66 ms, p90 16.74 ms.
- The engine costs **1.3 ms** per cook in space and **1.6 ms** over the river (timed
  with 60 forced cooks).
- The world shader costs 3.4 ms on the GPU.
- 58 operators, zero errors, zero warnings.

## What went wrong on the way

- **The painted sky sank with the ground.** Homestead's sky function was written for a
  fixed camera, so when the whole painting scrolled down with altitude, the moon went
  down with the land. The sky's sun, moon and stars are now pinned to the altitude, so
  only the land falls away.
- **Stars in a zooming field grow into snowflakes.** A cell-based star's size scales
  with its cell, and near cells are big. The star's size is now measured in world units,
  so a near star gets brighter but not bigger.
- **Homestead's house brought its garden with it.** The house generator includes the
  wheel frame, pole and garden rows placed for homestead's camera. Only stages 1–3 (the
  house itself) are used here.
- **Tails tied at the crown read as an X across his head from behind.** The knot is now
  at the nape, so the tails fall down his back.
