# Reaction-diffusion feedback engine — network notes

*Source project: `Govinderaver.toe` (private, gitignored).*

Audio-reactive pseudo-reaction-diffusion ("RD") feedback engine, composited under a
still image (moviefilein). All the action is in `/project1/RD`.

## The RD feedback core (the money recipe)

```
feedback1 (init: noise4 perlin3d, target: null1)
→ transform1 (sx = 100**op('null2')['chan1'], sy = 100**op('null3')['chan1'])   # EXPONENTIAL audio zoom
→ displace1 (source: noise2, weight .0001, offsetweight = 0.429 baseline + expr op('null3'))
→ blur1 (size 11, extend=repeat)
→ sharpen1 (convolve 3×3 Laplacian kernel: -1×8, center 8, i.e. unsharp)
→ null1  (closes loop)
out: comp1 = moviefilein1 over null1
```

**Blur → sharpen inside a feedback loop ≈ reaction-diffusion:** blur diffuses, the
Laplacian sharpen re-concentrates, and the balance grows organic coral/fractal
structure from any seed. Displace-by-noise makes it flow; transform zoom feeds it.

## Key expressions

- `sx = 100**op('null2')['chan1']` — **exponential audio mapping.** A 0..~0.05 bass level
  becomes a 1.0..~1.26 zoom; silence = exactly 1.0 (no drift). Far more dynamic than
  linear `1 + level`.
- noise2 (displacement field): `tz = (absTime.seconds*0.05) - 0.15*(100**op('null3')['chan1'])`
  — time scrub of the noise field accelerates with highs; `sx = 100**op('null3')`.
- noise1 (unused alt seed): `gain = 10**op('null2')['chan1']`.
- `feedback1.reset = op('mousein1')['lbutton']` — click to reseed. Essential: RD loops
  die (all-black/all-white) and need reseeding.

## Audio front end

Same canonical two-band chain as [audio-reactive-particles](audio-reactive-particles.md): lowpass 700 Hz → null2 (bass, filter
width .1), highpass 3 kHz → null3 (highs, filter width .5); envelopes width .15,
math1 → 0..0.7, math2 0..0.5 → 0.2..1.

## Reusable ideas

- Feedback + blur + Laplacian-sharpen + noise-displace = growing organic RD texture.
- `100**level` / `10**level` exponential mappings for zoom/gain (silence → identity).
- Seed feedback from a perlin noiseTOP (offset .99, amp 1.31) rather than black.
