# Projection-mapped feedback bar — network notes

*Source project: `HomeMapping.toe` (private, gitignored).*

First projection-mapping project: an audio-reactive feedback "light bar" mapped onto a
home wall with the stock **kantanMapper** palette component. The interesting parts are
the kantanMapper configuration and the export-table CHOP wiring. All in `/project1`.

## Audio drive

```
audiodevin1 → lag1 (0/0) → math1 (±0.1 → 0.3..0.5)
```

`math1` has **export on with an export table** (`math1_export` Table DAT docked to it:
row `transform1 py chan1`) — the third way to bind CHOPs to parameters besides
expressions and autoexport. The same `math1` also feeds ordinary expressions elsewhere.

## Content chain (feedback bar)

```
rectangle1 (10 × 0.02 bar, centery = 1-op('math1')['chan1']) + constant2 (black)
→ add1 → thresh1 (bypassed, threshold exported from math1) → edge1 (bypassed)
→ over1 (over constant1: black 720p rgba32float; sx/sy = 1-(math1*.1))
→ feedback1 (top: comp1) → transform1 (sx/sy .99, py = .9-math1, py also export-driven)
→ level1 (opacity .6, brightness 1.2) → comp1 = level1 over over1 → null1
```

A thin horizontal bar whose height tracks the audio level, trailing downward copies of
itself: the feedback shrinks 1% per frame around a pivot that itself moves with the
audio, so trails cascade with the beat. `constant1` being **rgba32float** keeps the
feedback accumulation from banding. `thresh1`/`edge1` left bypassed = kept experiments.

## Mapping output rig

```
kantanMapper (stock palette v2.13) → null2 → level2 (brightness 3) → out1
```

kantanMapper settings that matter: `Project = kantan.json` — **all quad/mask geometry
lives in a JSON sidecar file, not the network**; `sizefromwindow on`, 1280×720,
`display off`, `enable off` when not projecting; extension `Projecter`, parent shortcut
`mottoKantan`. Content TOPs are assigned to quads inside the kantan UI (stored in the
JSON), which is why nothing at network level wires `null1` into the mapper.
`level2` brightness 3 is projector-compensation gain.

Loose ends: `noise1 → chopto1` (CHOP-to-TOP) and `moviefilein1` (a photo of the wall,
for lining up quads) sit unwired — the photo-underlay trick is worth keeping.

## Reusable ideas

- kantanMapper recipe: content TOP(s) → kantanMapper (quads in `kantan.json`) → null →
  output level gain. Keep the `.json` with the project; the mapping *is* that file.
- Export-table binding (Math CHOP `exporttable`) when you want the binding visible and
  editable as data instead of buried in a parameter expression.
- Feedback pivot (`px`/`py`) as the audio-reactive element — moves the vanishing point
  of the trail instead of the image.
- A wall photo in a Movie File In as alignment underlay while drawing mapping quads.
