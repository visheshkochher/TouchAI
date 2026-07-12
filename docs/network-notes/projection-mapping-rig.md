# Projection-mapping performance rig — network notes

*Source project: `KantanMapping.toe` (private, gitignored).*

The full projection-mapping *performance rig*: four independent audio-reactive content
generators packaged as Base COMPs, all fed to the stock **kantanMapper** (quads in
`kantan.json`) which composes them onto mapped surfaces. This is the owner's pattern
for a multi-scene show file — each `base*` is a self-contained scene with its own
`out1` TOP; several are earlier projects imported wholesale.

```
base1 (beat movie player)      → null5 ┐
base2 (camera diff + particles)→ over1 (over black) → null3 ┐
base3 (RD feedback engine)     → null6 → edge1 (Chroma TOP) → null4 ├→ kantanMapper → null2 → out1
Wallpapergroups (p3m1) → null1 → displace2 (by Wolfram/out1) → null7 ┘
```

Content-to-quad assignment lives inside kantanMapper's `kantan.json` (same config as
the [mapped feedback bar](mapped-feedback-bar.md) project: v2.13, 1280×720, `Projecter` extension, shortcut `mottoKantan`), so the
nulls appear unwired at network level.

## The scene COMPs

- **base1 = the [beat-gated video jukebox](beat-gated-video.md) as a component**: folder-driven movie
  playlist (`~/Desktop/finalviz`, `*.m*`), keyboard keys 1–6 cycle files, bass gate
  plays the movie, highs rotate/zoom, cache-select exclude-comp frame echo. Has an
  `in1` CHOP for audio but it's unconnected — the COMP still uses gates fed from its
  internal chain.
- **base2 = camera motion-detect + particlesGpu** (ancestor of [camera-motion-detect](camera-motion-detect.md)):
  `videodevin1` (FaceTime cam, bypassed) → cache → `comp1 (difference)` with cache
  select → level (brightness 60, contrast 5!) → chroma key → edge → blur → level3 →
  `feedback1` + `transform2` (1.02 zoom, slight rotate) trails → difference/subtract
  composites with a perlin `noise3` layer. In parallel the stock **particlesGpu**
  palette COMP (150k particles, Sand preset, sphere SOP emitter via sort→noise SOP):
  two-band audio (`in1`→filters→envelopes→resample→math→filter) maps **bass → Drag
  (`*1.2`) and highs → Turbulence translate**, turbulence period wobbled by a noise
  CHOP, `Reset` on mouse click; particle image → lookup ramp palette → composited over
  the motion-detect layer. The particlesGpu parameter set here is the reference recipe
  in `patterns.md`.
- **base3 = the [reaction-diffusion feedback](reaction-diffusion-feedback.md) engine, verbatim**: feedback →
  transform (`sx/sy = 100**level` exponential audio zoom) → displace by animated
  perlin noise → blur 11 → `sharpen1` COMP → loop; seeded from a perlin noise TOP,
  mouse-click reset, canonical two-band chain (lowpass 700 Hz / highpass 3 kHz). Its
  output is then **Chroma-keyed at top level** (`edge1`, hue 30–374) to knock out a hue
  band before mapping.
- **Wallpapergroups** — stock palette COMP generating tiled wallpaper-symmetry-group
  patterns (all 17 groups as sub-COMPs; `Group = p3m1` selected), then `displace2`
  displaces the tiling with **Wolfram** (stock 1-D cellular automaton COMP, `Rule 122`)
  — CA texture as a displacement map.

## Loose ends (unwired experiments)

`moviefilein1 → displace1` (vertical displace by `chopto1` of a scrolling noise CHOP —
CHOP-to-TOP as displacement source) and `geo1` (box + phong with `colormap in1`,
face-projected texture SOP) reach no output; there is no Render TOP at this level.

## Reusable ideas

- **Show-file architecture:** one Base COMP per scene, each ending in `out1`, mapper
  as the only compositor/output. Import old projects as scenes instead of rebuilding.
- Cellular-automaton (Wolfram) or CHOP-to-TOP output as displacement maps.
- Chroma TOP hue-band keying to restyle a generator's output before mapping.
- particlesGpu two-band mapping: bass → Drag, highs → turbulence translate, noise-
  wobbled turbulence period, mouse reset.
