# Camera motion-detect trails — network notes

*Source project: `CameraMotionDetect.toe` (private, gitignored).*

Pure webcam motion-detection visual: frame-difference mask → psychedelic
difference-operand feedback trails over animated perlin noise. No audio.
(This is the precursor of the motion layer inside [audio-reactive-particles](audio-reactive-particles.md).)

## Chain

```
videodevin1 → cache1 (cachesize 11) → comp1 (operand=difference, in2 = cacheselect1 index −2)
→ level1 (brightness 2) → chroma1 (valmin .65 — keys out sensor noise)
→ edge1 (strength 10) → blur1 (size 120!) → level2 (brightness 60, gamma .86, contrast 5)

feedback1 (in: level2, target: comp2) → transform1 (rotate .01, sx/sy 1.02) → level3 (opacity .42, gamma2 1.09)
comp2 = level3 DIFFERENCE level2            # difference-operand feedback = inverting, non-blowout trails
comp3 = comp2 over noise1 (perlin3d TOP, animated tx/ty, exp .41, amp 1.31, offset .99 ≈ near-white bg)
→ out1
```

## Reusable ideas

- **Frame difference across N frames:** `cacheselect1.index = -2` compares against 2 frames
  ago — larger |index| = more motion sensitivity for slow movement.
- **Difference-operand feedback** (comp2 operand=difference) self-cancels where trails
  overlap → oscillating inverted patterns instead of white blowout. Opacity .42 on the
  fed-back branch sets trail persistence.
- Huge blur (120) before the boost stage turns edge fragments into soft blobs the
  feedback can smear.
