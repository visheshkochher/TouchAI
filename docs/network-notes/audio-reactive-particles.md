# Audio-reactive GPU particles — network notes

*Source project: `AudioParticles.toe` (private, gitignored).*

Audio-reactive GPU particle system (TD palette `particlesGpu` COMP) layered over
webcam motion-detect feedback trails. 60,000 particles, "Sand" preset.

## Audio front end (the canonical two-band chain)

```
audiodevin1 → null4 ─┬→ audiofilter1 (lowpass, 700 Hz)  → envelope1 (w=0.15) → resample1 → math1 (add, →0..0.7)   → filter1 (w=0.1) → null2   # BASS
                     └→ audiofilter2 (highpass, 3 kHz)  → envelope2 (w=0.15) → resample2 → math2 (0..0.5→0.2..1)  → filter2 (w=0.5) → null3   # HIGHS
```

Bass gets a fast filter (0.1s) for punch; highs get a slow one (0.5s) for smooth shimmer.

## particlesGpu custom pars (audio-mapped)

| Par | Value / expression |
|---|---|
| `Particles` | 60000 |
| `Drag` | `op('null2')['chan1']*1.2` — bass tightens drag |
| `Turbtransx` | `op('null3')['chan1']` (y/z ×0.2) — highs push turbulence field |
| `Turbuperiod` | `op('null5')['tP']*2` — noiseCHOP (period 7, amp .5, off .5) slowly varies turbulence scale |
| `Reset` | `op('mousein1')['lbutton']` — mouse click reseeds |
| Turbulence x/y/z | 3 / 2.5 / 10; `Turbulencemag` 0.5 |
| Size | 0.005–0.015; `Compositing` coverage, `Texture` square |

## Particle post chain

`particlesGpu/out1 → transform1 (black bg, comp over) → lookup1 (ramp1 = palette colorize)
→ lumablur1 (ramp2 control, blackvalue .011, whitewidth 35 = glow on bright) → level1 → null1`

**lookup TOP + ramp = palette colorize; lumablur + ramp = luminance-driven glow.**

## Webcam motion-detect + feedback trail layer

```
videodevin1 → cache1 (11 frames) → comp1 (difference vs cacheselect1 index −1)   # frame-difference motion mask
→ level2 → chroma1 (valmin .68 keys out noise) → edge1 (strength 10) → blur1
→ level3 (brightness 60, contrast 5, gamma .86)                                   # extreme boost: faint diffs → solid shapes
feedback1 (in: level3, target: comp2) → transform2 (rotate .01, sx/sy 1.02) → level4
comp2 = level4 ⊕ level3  → trails
comp3 = comp2 atop noise3 (bg texture); comp4 = null1 (particles) over comp3 → out1
```

## Reusable ideas

- Frame-difference motion detection: cacheTOP + cacheselectTOP(index −1..−2) + compositeTOP `difference`.
- Boost-then-key: level(brightness ~60, contrast ~5) after chroma-key turns whisper-faint camera diffs into graphic shapes.
- Scale-up feedback (sx/sy 1.02 + rotate .01) = outward-spiraling trails.
- Slow noiseCHOP as a "wander" LFO on a particle par keeps stills interesting between beats.
