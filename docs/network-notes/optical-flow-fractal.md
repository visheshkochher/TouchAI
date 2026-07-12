# Optical-flow reactive fractal — network notes

*Source project: `GenerativeAVReactiveFractal.toe` (private, gitignored).*

Evolution of the [reaction-diffusion feedback](reaction-diffusion-feedback.md) engine: the displacement field is **webcam optical
flow** instead of noise, so viewer movement literally stirs the fractal. Audio still
drives growth/zoom.

## Top level

```
videodevin2 → (feeds) webcamOpticalFlow → RD1.in1 (displace source)
RD1/out1 → out1
```

## RD1 (vs the original RD engine)

```
feedback1 (init: noise1 perlin3d, resetpulse = mouse lbutton)
→ transform1 (sx/sy = 1.005**op('null2')['chan1'], growshrinky = 1.05**op('null2'))   # gentler exponent
→ displace1 (in2 = in1 ← optical flow; weight .001; offsetweight = "1 - me.par.uvweight.eval()")
→ blur1 (extend=mirror) → sharpen1 (same Laplacian convolve) → null1 → out1
```

- noise1 seed: `tz = (absTime.seconds*0.05) - (100**op('null3')['chan1'])` — highs scrub the seed field.
- Base 1.005/1.05 instead of 100 — subtler growth, RD survives longer between reseeds.

## webcamOpticalFlow COMP

```
in1 → flip1 → fit1 (fitoutside, 600×600) → blur4 (10)
→ opticalFlow (GLSL, ofxFlowTools port)
   inputs: current frame + cacheTOP previous frame; out = flow vec2 in RG, rgba32float
→ blur3 (9) → fbk (flow trail: feedback → blur → math (decay) → comp add with live) → out1
```

Uniforms: uForce=1, uOffset=3, uLambda=0.1, uThreshold=0 (format rgba32float — flow
needs signed float pixels!).

## Reusable ideas

- Optical flow → displaceTOP source: camera motion as a force field for any feedback/RD loop.
- Pre-chain for flow quality: fit to small square (600²) + blur ~10 before, blur ~9 after.
- Flow trails: run flow through its own mini feedback (blur + gain-decay + add) so
  forces persist a moment after movement stops.
- Downscale + blur webcam before analysis — flow at full res is noise, not motion.
