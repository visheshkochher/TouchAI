# audio_reactive_feedback

Audio-reactive feedback tunnel: a two-band audio analysis chain drives an
exponential zoom + rotate + noise-displace feedback loop, with the live audio
spectrum stamped in each frame as fresh content. Colorized via a 3-stop
lookup ramp (black → deep blue → desaturated lavender) and finished with a
luma-driven glow blur.

Build with `scenes/audio_reactive_feedback/build.py` (paste into the MCP
`run` tool, or a Text DAT and execute). Idempotent — destroys and rebuilds
its own `/project1/audio_feedback` container and the project-level
`/project1/audio_feedback_out` Out TOP; touches nothing else.

## What it does

- **Audio**: `audio_in` (audiofileinCHOP, defaults to TD's bundled
  JeremyCaulfield track) → the canonical two-band bass/highs chain →
  `null_bass` / `null_highs`. Also feeds `spectrum1` (audiospectrumCHOP) →
  `spectrum_top` (choptoTOP) as a per-frame texture stamp.
- **Feedback loop**: `noise_seed` → `fb_loop` (feedbackTOP) → `fb_zoom`
  (transformTOP, exponential scale on bass + slow constant rotate) →
  `fb_displace` (noise-driven, animated by highs) → `fb_blur` → `fb_faded`
  (RGB decay) → `composite_loop` (ADD with the spectrum stamp) → `loop_null`
  → closes back into `fb_loop.par.top`.
- **Finish**: `loop_null` → `lookup1` (palette from `palette_dat`/`palette_ramp`)
  → `glow_blur` (lumablurTOP) → `level_final` → `final_out` → `out1`.

Runs at a measured 60fps on the below-spec Intel Iris Plus machine profiled
in `MACHINE.md` (640×360 feedback resolution, blur sizes ≤6, one lumablur —
well inside its GPU watchdog budgets).

## Gotchas discovered building this (already folded into
`.claude/skills/touchdesigner-building/patterns.md` and `SKILL.md` where
generic; scene-specific ones noted here)

- **lumablurTOP needs 2 wired inputs**, not 1 — `docs` lists `inputs: 2` but
  it's easy to assume input2 is optional since `widthchan` names channels of
  input1. Leaving it unwired throws "Not enough sources specified" (no
  visual symptom otherwise). Wire the same source into both.
- **A sustained scale>1 zoom feedback loop collapses to a black hole at
  center.** Each frame samples an ever-smaller crop of the previous frame
  around the pivot; if that pixel started dark (or ever goes dark), it
  self-reinforces into an expanding black circle with no error. Fixed here
  with a periodic self-reseed (`fb.par.reset.expr = "absTime.seconds % 14 <
  0.1"`) rather than trying to tune the zoom to never collapse.
- **`OVER` with a mostly-black-but-fully-opaque stamp washes the whole frame
  toward black every frame**, not just where the stamp is bright — `opacity`
  on a levelTOP scales alpha uniformly across the frame regardless of RGB
  content, so compositing 'over' blends that uniform alpha over the *entire*
  previous frame. Switched the loop's fresh-content composite to `ADD`,
  which only contributes where the stamp is actually bright.
- **Decay in an ADD-composited loop must reduce RGB (`brightness2`), not
  alpha (`opacity`)** — ADD ignores alpha entirely, so an opacity-only decay
  left brightness accumulating forever and blew the loop out to solid white
  in well under a second at 60fps.
- **Raw audiospectrumCHOP magnitudes are tiny (~1e-3)** — needs real gain
  (`brightness1` ~4 here) to read as visible bars once turned into a
  texture via choptoTOP. But in an ADD feedback loop, too much gain
  saturates almost instantly (verified at `brightness1=30`) — tune gain and
  decay together, not independently.
