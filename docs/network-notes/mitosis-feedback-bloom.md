# Mitosis feedback bloom — network notes

*Source project: `Mitosis.toe` (private, gitignored).*

Audio-reactive "cell division": three colored circles get pushed apart by bass while a
zooming, luma-adaptive-blur feedback loop grows glowing organic trails between them.
All in `/project1`.

## Source layer

Three 720p Circle TOPs (blue `0,.18,1`, red `1,0,.32`, green `0,.59,.10`), each through
its own Transform, `add`-composited with a near-black constant (`0.078` gray):

```
constant2 + transform1(circle1) + transform3(circle2) + transform4(circle3)
→ comp1 (operand add, 1280×720)
```

Audio drive (`null2`): `audiodevin1 → math2 (±0.1 → -0.3..0.2) → lag2 (0.1 up / 0.5 down)`.

- `transform1.ty = op('null2')['chan1']`, `transform3.ty = op('null2')['chan1']*-1` —
  the two circles split **in opposite directions** on the beat; that's the mitosis read.
- `transform4.sx/sy = op('null2')['chan1']+.7` — third cell breathes instead of moving.
- A parallel `noise1 → math1 → lag1` chain exists but nothing consumes it (dead).

## Feedback bloom loop

```
comp1 → feedback1 (top: comp2) → transform2 (sx/sy 1.1)
→ lumalevel1 (blacklevel .2, brightness .82, gamma 1.93, contrast .74)
→ lumablur1 (width from red channel: black width 18, white width 14, blackvalue .157)
→ blur1 (preshrink 2, size 20, extend repeat)
→ level1 (gamma .75, opacity .7)
comp2 = level1 add comp1  → out1
```

Key trick: **the Feedback TOP's `top` points at `comp2`, the post-composite** — so the
loop re-ingests the finished frame (trails + fresh circles), while `comp1` (circles
only) is what feedback1 passes through on reset. The 1.1× transform makes trails bloom
*outward*; lumalevel kills dim history (so trails decay) before the luma-driven +
regular blur smear what survives into soft plasma.

## Reusable ideas

- Outward-zoom feedback (`sx/sy > 1`) = expanding halo trails; contrast/blacklevel
  inside the loop is the decay knob (same family as the [reaction-diffusion](reaction-diffusion-feedback.md) loop, but
  bloom-flavored: no sharpen, heavy blur).
- Luma Blur width mapped black-vs-white = bright cores stay crisp, dark trails smear.
- Mirrored `±level` exports on two transforms for a split/divide gesture.
- Slow-attack/slower-release Lag (0.1/0.5) on raw `audiodevin` instead of a band chain —
  crude but effective when the track is beat-heavy.
