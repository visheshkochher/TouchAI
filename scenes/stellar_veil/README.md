# Stellar Veil

Audio-reactive deep-space drift. Keywords: **stars, space, planets, ethereal**.

Three parallax layers of cell-hashed stars drift under a blurred nebula band
while a banded gas giant turns on its axis and a moon crosses in front of it
and back behind. A **maximum-operand feedback loop** (self-limiting — an
additive one would wash to white) leaves soft comet ghosts behind the stars.
Bass swells the field and the planet's disc, highs speed up the twinkle,
overall energy thickens the gas, and every kick punches the trail outward —
the "warp" moment. Finish: indigo→violet→starlight palette → threshold bloom
→ 1280x720 upres.

Every audio mapping **rests at exactly its idle value**, so the scene is a
complete, calm composition in silence and only spends brightness when the
music earns it.

## Rebuild

Run `build.py` via the MCP `run` tool (idempotent — destroys and recreates
`/project1/stellar_veil` + `/project1/stellar_veil_out`, touches nothing else):

```python
g = dict(globals())
exec(compile(open('<repo>/scenes/stellar_veil/build.py').read(), 'build.py', 'exec'), g)
```

## Custom parameters (the performance surface)

On the `stellar_veil` COMP, page **Veil**:

- **Audio Source** — `Audio Device In` (live) or `Audio File In (test)`.
  Defaults to file, using TD's bundled techno track. Switching is instant and
  the device path was verified clean.
- **Reactivity** (0–3, default 1) — one knob scaling every band at `spec_gain`.
- **Device In Gain** (1–30, default 5) — extra gain applied **only** in device
  mode, on top of Reactivity. A mic/line input sits far below a decoded file;
  5 lands a quiet room at a 0.05–0.23 idle with headroom to spare. Raise it for
  a quiet line input, lower it if ambient noise alone drives the scene.
- **Kick Warp** (0–3, default 0.5) — how far each kick punches the star trails
  outward. At 0 the trails just drift; past ~1.5 it becomes a hyperspace tunnel.
- **Beat Spin** (0–8, default 2.2) — angular velocity each kick adds to the
  planet. At 0 it turns at the idle rate; at the default the surface visibly
  surges on every hit.
- **Nebula Density** (0–2.5, default 1) — gas gain.
- **Star Twinkle** (0–2, default 1) — twinkle depth.

## Structure

- **Audio**: `audio_device` / `audio_file` → `audio_src` switchCHOP → mono →
  **one** `spectrum` (audiospectrumCHOP, 128 log bins) → `spec_gain`. Every
  scalar is then read back off those 128 samples — no per-sample work at 44.1kHz
  (the rings_of_saturn rule):
  `null_energy` (all bins, slow lag), `null_bass` (bins 0–24, fast),
  `null_highs` (bins 80–128), `null_beat` (envelope-divide kick: `anl_bass` ÷ its
  own 3s lag → triggerCHOP, so it fires at any input level).
- **Planet spin**: `null_beat` → `spin_rate` (mathCHOP: `Spinkick` × beat, plus
  the 0.035 idle rate) → `spin_phase` **speedCHOP** → `null_spin`, fed to the
  shader as `uOrb.x`. This is an *integrated phase*, not `time × rate`: scaling
  absTime by a beat-varying factor would snap the whole accumulated angle on
  every hit, whereas integrating a rate accelerates smoothly and never jumps.
- **Visual**: `src_nebula` noise → `neb_blur` (gas has no edges) → `starfield`
  glslTOP (uniforms `uStar` = time/energy/bass/highs, `uVeil` = knobs + beat)
  → maximum-feedback veil (`veil_fb` → `veil_xform` kick zoom → `veil_level`
  0.86 → `veil_comp` ← starfield; loop closed via `veil_fb.par.top = null_veil`).
- **Planets**: `src_bands` noise → `planets` glslTOP — two analytic lit spheres
  (normal from the disc, lat/lon banding, limb rim light, atmosphere halo),
  composited over the veil with an overTOP.
- **Finish**: `colorize` lookup (ramp from `palette_keys`) → threshold+blur bloom
  → `upres` (1280x720, 8-bit) → `final_out` → `out1`; project-level Out TOP
  `stellar_veil_out`.

## Inputs / outputs

- Input: audio device or file, selected by the **Audio Source** parameter.
- Output: `/project1/stellar_veil` COMP output connector /
  `/project1/stellar_veil_out`.

## Verified (2026-08-21, Intel MacBook profile in MACHINE.md)

- No operator errors/warnings in either audio mode.
- **60.0 fps real** (frame-delta over wall clock, 21s sample). Steady-state
  heaviest TOP is `glow_blur` at 0.21ms — the 40–50ms readings on the two GLSL
  TOPs right after a rebuild are one-off shader compiles, not per-frame cost.
- Sim res 640x360, blur size 16 with Pre-Shrink 3, and **no loop in either
  shader** — inside the watchdog budget.
- Band levels calibrated against measured levels. On the test track bass now
  sweeps ~0.29–1.09, using its full range and only brushing the `min(1.0, …)`
  clamp on the loudest hits. On device in, a quiet room idles at 0.05–0.23.
- Device-in bass is ~8× more sensitive than the first version (5× from
  `Device In Gain`, 1.67× from the hotter `math_bass` mapping). Verified that
  the spin phase accumulates and that beats drive it well above the idle rate.

## Tuning knobs

- `veil_level.opacity` (0.86) — trail length. Higher = longer comet ghosts.
- `veil_xform.sx/sy` (idle 1.0018) — constant outward drift of the trails.
- `kick_trig.threshup` (2.0) — kick sensitivity, on the *normalized* ratio.
  Because it gates a ratio rather than a level, it works unchanged at any input
  volume — the **Device In Gain** knob is about band *range*, not kick detection.
- The nebula's `min(…, 0.62)` clamp in `starfield_pixel` is what guarantees the
  gas can never out-shine a star or blow out through the bloom.
- `palette_keys` — the whole colour identity; the violet stop at 0.60 is where
  the nebula plateau lands.
