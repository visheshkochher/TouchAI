# Stellar Veil — a drifting starfield under a nebula band, with a gas giant and its
# moon turning slowly through it. Keywords: stars, space, planets, ethereal.
#
# Idempotent: destroys and recreates /project1/stellar_veil (and its project-level
# Out TOP) and touches nothing else. Run via the MCP `run` tool.
#
# BUILT LIGHT (MACHINE.md: Intel Iris, ~2s GPU watchdog). Sim res 640x360, upscaled
# to 1280x720 at the finish. Two GLSL TOPs, but neither contains a loop — the
# starfield is three cell-hashed layers and the planets are two analytic spheres.
# No per-sample audio work: one FFT (audiospectrumCHOP) and everything after it
# operates on 128 samples, per the rings_of_saturn note.

SCENE = 'stellar_veil'
SIMW, SIMH = 640, 360
OUTW, OUTH = 1280, 720
SPECBANDS = 128          # audiospectrumCHOP clamps outlength to a 128 minimum

proj = op('/project1')
for stale in (SCENE, SCENE + '_out'):
    o = proj.op(stale)
    if o:
        o.destroy()

s = proj.create(containerCOMP, SCENE)
s.nodeX, s.nodeY = 0, -400
s.par.w, s.par.h = OUTW, OUTH


def C(type_, name, x, y, **params):
    o = s.create(type_, name)
    o.nodeX, o.nodeY = x, y
    for k, v in params.items():
        setattr(o.par, k, v)
    return o


def W(src, dst, idx=0):
    src.outputConnectors[0].connect(dst.inputConnectors[idx])


def res(o, w=SIMW, h=SIMH, fmt='rgba16float'):
    o.par.outputresolution = 'custom'
    o.par.resmult = False
    o.par.resolutionw, o.par.resolutionh = w, h
    o.par.format = fmt
    return o


# ---------------------------------------------------------------------------
# CUSTOM PARAMETERS — the live-performance surface
# ---------------------------------------------------------------------------
pg = s.appendCustomPage('Veil')
pg.appendMenu('Audiosrc', label='Audio Source')
s.par.Audiosrc.menuNames = ['device', 'file']
s.par.Audiosrc.menuLabels = ['Audio Device In', 'Audio File In (test)']
s.par.Audiosrc = 'file'

for nm, label, val, lo, hi in [
    ('Reactivity', 'Reactivity',      1.0, 0.0, 3.0),
    ('Devgain',    'Device In Gain',  5.0, 1.0, 30.0),
    ('Warp',       'Kick Warp',       0.5, 0.0, 3.0),
    ('Spinkick',   'Beat Spin',       2.2, 0.0, 8.0),
    ('Nebula',     'Nebula Density',  1.0, 0.0, 2.5),
    ('Twinkle',    'Star Twinkle',    1.0, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

# ---------------------------------------------------------------------------
# AUDIO IN — device for performance, bundled file for testing
# ---------------------------------------------------------------------------
adev = C(audiodeviceinCHOP, 'audio_device', 0, 780)
adev.par.active.expr = "parent().par.Audiosrc.menuIndex == 0"

afile = C(audiofileinCHOP, 'audio_file', 0, 900, repeat=True, play=True)
# TD's bundled test track. 'Samples/...' resolves against the .toe folder, not the
# install, so search the known install layouts (macOS buries it under
# Contents/Resources/tfs). Only used when Audiosrc == file.
import os as _os
_rel = _os.path.join('Samples', 'Audio', 'JeremyCaulfield_www.dumb-unit.com.mp3')
for _base in ('', 'Contents/Resources/tfs', 'tfs', 'Contents/Resources'):
    _cand = _os.path.join(str(app.installFolder), _base, _rel)
    if _os.path.exists(_cand):
        afile.par.file = _cand
        break

audio = C(switchCHOP, 'audio_src', 170, 840)
audio.par.index.expr = "parent().par.Audiosrc.menuIndex"
W(adev, audio, 0)
W(afile, audio, 1)

mono = C(mathCHOP, 'audio_mono', 340, 840, chanop='avg')
W(audio, mono)

spec = C(audiospectrumCHOP, 'spectrum', 510, 840, frequencylog=True,
         fftsize='2048', outputmenu='setmanually', outlength=SPECBANDS)
W(mono, spec)
spec_gain = C(mathCHOP, 'spec_gain', 680, 840)
# A mic/line input sits far below a decoded file, so device mode gets its own
# gain stage on top of Reactivity. File mode is untouched (multiplier 1.0).
spec_gain.par.gain.expr = ("2.5 * parent().par.Reactivity * "
                           "(parent().par.Devgain.eval() "
                           "if parent().par.Audiosrc.menuIndex == 0 else 1.0)")
W(spec, spec_gain)
null_spec = C(nullCHOP, 'null_spec', 850, 840)
W(spec_gain, null_spec)

# overall energy → nebula density + planet atmosphere (slow: the "breath")
anl_energy = C(analyzeCHOP, 'anl_energy', 1020, 840, function='average')
W(null_spec, anl_energy)
# fromrange2 values below are calibrated against measured levels on the test track
# so each band lands in ~0..0.8 with headroom, instead of pinning at its clamp
math_energy = C(mathCHOP, 'math_energy', 1190, 840)
math_energy.par.fromrange2 = 1.2
math_energy.par.torange2 = 1.0
W(anl_energy, math_energy)
lag_energy = C(lagCHOP, 'lag_energy', 1360, 840, lag1=0.9, lag2=1.6)
W(math_energy, lag_energy)
null_energy = C(nullCHOP, 'null_energy', 1530, 840)
W(lag_energy, null_energy)

# bass = mean of the bottom fifth of the log-spaced spectrum → star breath (fast)
trim_bass = C(trimCHOP, 'trim_bass', 1020, 990,
              startunit='samples', start=0, endunit='samples', end=24)
W(null_spec, trim_bass)
anl_bass = C(analyzeCHOP, 'anl_bass', 1190, 990, function='average')
W(trim_bass, anl_bass)
math_bass = C(mathCHOP, 'math_bass', 1360, 990)
math_bass.par.fromrange2 = 0.6
math_bass.par.torange2 = 1.0
W(anl_bass, math_bass)
lag_bass = C(lagCHOP, 'lag_bass', 1530, 990, lag1=0.06, lag2=0.4)
W(math_bass, lag_bass)
null_bass = C(nullCHOP, 'null_bass', 1700, 990)
W(lag_bass, null_bass)

# highs = top third of the spectrum → star shimmer (slow smoothing, per patterns.md)
trim_highs = C(trimCHOP, 'trim_highs', 1020, 1140,
               startunit='samples', start=80, endunit='samples', end=SPECBANDS)
W(null_spec, trim_highs)
anl_highs = C(analyzeCHOP, 'anl_highs', 1190, 1140, function='average')
W(trim_highs, anl_highs)
math_highs = C(mathCHOP, 'math_highs', 1360, 1140)
math_highs.par.fromrange2 = 0.11
math_highs.par.torange2 = 1.0
W(anl_highs, math_highs)
lag_highs = C(lagCHOP, 'lag_highs', 1530, 1140, lag1=0.15, lag2=0.6)
W(math_highs, lag_highs)
null_highs = C(nullCHOP, 'null_highs', 1700, 1140)
W(lag_highs, null_highs)

# kick: fast bass gated against a slow lagged copy of itself (the envelope-divide
# idiom) so it triggers at any input level — device or file, quiet room or loud
lag_ref = C(lagCHOP, 'lag_ref', 1360, 1290, lag1=3.0, lag2=3.0)
W(anl_bass, lag_ref)
kick_norm = C(mathCHOP, 'kick_norm', 1530, 1290, chopop='div')
W(anl_bass, kick_norm, 0)
W(lag_ref, kick_norm, 1)
kick = C(triggerCHOP, 'kick_trig', 1700, 1290,
         threshup=2.0, threshdown=1.25, attack=0.005, decay=0.12,
         sustain=0.0, release=0.10, retrigger=0.20)
W(kick_norm, kick)
null_beat = C(nullCHOP, 'null_beat', 1870, 1290)
W(kick, null_beat)

# Planet spin: each kick ADDS angular velocity, which is why this is an
# integrated phase (speedCHOP) and not `time * rate`. Scaling absTime by a
# beat-varying factor would snap the whole accumulated angle on every hit;
# integrating a rate accelerates smoothly and never jumps. Rests at the idle
# rate 0.035 rad/s, exactly the constant it replaces.
spin_rate = C(mathCHOP, 'spin_rate', 2040, 1290, postoff=0.035)
spin_rate.par.gain.expr = "parent().par.Spinkick"
W(null_beat, spin_rate)
spin_phase = C(speedCHOP, 'spin_phase', 2210, 1290, timeslice=True)
W(spin_rate, spin_phase)
null_spin = C(nullCHOP, 'null_spin', 2380, 1290)
W(spin_phase, null_spin)

ENERGY = "min(1.0, op('null_energy')['chan1'])"
BASS = "min(1.0, op('null_bass')['chan1'])"
HIGHS = "min(1.0, op('null_highs')['chan1'])"
BEAT = "min(1.0, op('null_beat')['chan1'])"
SPIN = "op('null_spin')['chan1']"

# ---------------------------------------------------------------------------
# NEBULA SOURCE — one slow noise field, the only thing the starfield shader reads
# ---------------------------------------------------------------------------
neb = C(noiseTOP, 'src_nebula', 0, 0, period=4.2, harmon=3, amp=1.15,
        offset=-0.18, exp=1.5, mono=True)
res(neb)
neb.par.tz.expr = "absTime.seconds*0.012"        # slow drift nobody consciously sees
neb.par.tx.expr = "absTime.seconds*0.004"

# gas has no edges: blurring the source is what turns noise into a nebula
neb_blur = C(blurTOP, 'neb_blur', 0, -160, size=16, preshrink=3)
W(neb, neb_blur)

# ---------------------------------------------------------------------------
# STARFIELD + NEBULA VEIL (GLSL #1 — three hashed star layers, no loops)
# ---------------------------------------------------------------------------
stars = C(glslTOP, 'starfield', 200, 0)
res(stars)
W(neb_blur, stars)
stars.par.vec = 2
stars.par.vec0name = 'uStar'
stars.par.vec0valuex.expr = "absTime.seconds"
stars.par.vec0valuey.expr = ENERGY
stars.par.vec0valuez.expr = BASS
stars.par.vec0valuew.expr = HIGHS
stars.par.vec1name = 'uVeil'
stars.par.vec1valuex.expr = "parent().par.Nebula"
stars.par.vec1valuey.expr = "parent().par.Twinkle"
stars.par.vec1valuez.expr = BEAT

s.op('starfield_pixel').text = """uniform vec4 uStar;  // x time, y energy, z bass, w highs
uniform vec4 uVeil;  // x nebula knob, y twinkle knob, z beat
out vec4 fragColor;

float h21(vec2 p) {
    p = fract(p * vec2(127.31, 311.7));
    p += dot(p, p + 34.72);
    return fract(p.x * p.y);
}

// one cell-hashed star layer: hash each grid cell, keep the sparse minority
vec3 layer(vec2 uv, float scale, float density, float bright, float t, float tw) {
    vec2 g  = uv * scale;
    vec2 id = floor(g);
    float h = h21(id);
    if (h < density) return vec3(0.0);
    vec2 f = fract(g) - 0.5;
    vec2 o = (vec2(h21(id + 17.1), h21(id + 91.7)) - 0.5) * 0.66;
    float d = length(f - o) + 1e-4;
    float flick = max(mix(1.0, 0.5 + 0.5 * sin(t * (0.7 + 2.6 * h) + h * 47.0), tw), 0.0);
    float v = min(bright * flick * 0.035 / d, 2.5);
    v *= smoothstep(0.55, 0.06, d);                       // no cell seams
    vec3 tint = mix(vec3(0.72, 0.84, 1.0), vec3(1.0, 0.93, 0.80), h21(id + 5.3));
    return v * tint;
}

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv  = (gl_FragCoord.xy - 0.5 * res) / res.y;     // centred, aspect-correct
    float t  = uStar.x;

    // nebula: the input noise rotated into a diagonal band, gamma'd so only the
    // dense cores survive — darkness is the canvas
    vec2 nuv = uv * vec2(0.55, 1.0);
    float a  = 0.42;
    vec2 ruv = vec2(nuv.x * cos(a) - nuv.y * sin(a), nuv.x * sin(a) + nuv.y * cos(a));
    // two scales of the same field: the fine one breaks the coarse one into wisps
    float n1 = texture(sTD2DInputs[0], ruv * 0.8 + 0.5).r;
    float n2 = texture(sTD2DInputs[0], ruv * 2.1 + vec2(0.31, 0.67)).r;
    float n  = max(n1 * 0.80 + n2 * 0.30, 0.0);
    float band = exp(-pow(abs(ruv.y + 0.12) * 1.9, 2.0));   // band sits off-centre
    // low gamma = broad and dim rather than a few hot cores; the clamp guarantees
    // the gas can never out-shine a star or blow out through the bloom
    // ...and the clamp lands the gas in the violet plateau of the palette, where
    // "ethereal" lives — bright enough to read, never white
    float neb  = min(pow(n, 1.7) * band * 1.15 * uVeil.x
                     * (1.0 + 0.9 * uStar.y), 0.62);

    // three parallax layers, far to near. Highs speed up the twinkle and lift the
    // near layer, so hats/cymbals read as shimmer across the field.
    float tw = clamp(uVeil.y * (1.0 + 0.6 * uStar.w), 0.0, 1.0);
    float ts = t * (1.0 + 2.5 * uStar.w);                 // twinkle *rate* on highs
    float px = t * 0.006;
    vec3 col  = layer(uv + vec2(px * 0.35, 0.0),        26.0, 0.90, 0.55, ts, 0.85 * tw);
         col += layer(uv + vec2(px * 0.70, px * 0.12),  14.0, 0.86, 0.85, ts, 0.60 * tw);
         col += layer(uv + vec2(px * 1.30, px * 0.24),   7.0, 0.83, 1.25, ts, 0.35 * tw);
    // bass swells the field, the kick flashes it — both rest at exactly x1.0
    col *= 1.0 + 0.85 * uStar.z + 0.55 * uVeil.z;

    col += neb * vec3(0.62, 0.72, 1.0) * (1.0 + 0.5 * uVeil.z);
    col *= smoothstep(1.25, 0.28, length(uv));            // vignette
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}"""

# ---------------------------------------------------------------------------
# ETHEREAL VEIL — maximum-operand feedback: self-limiting, leaves soft ghosts
# that drift outward instead of blowing out (an additive loop would wash white)
# ---------------------------------------------------------------------------
fb = C(feedbackTOP, 'veil_fb', 380, -160)
res(fb)
W(stars, fb)                                     # input = reset image only

fb_xform = C(transformTOP, 'veil_xform', 550, -160, rotate=0.02, extend='zero')
# each kick punches the trail outward — the "warp through the stars" moment.
# Rests at exactly 1.0028 (the idle drift) when the room is silent.
_warp = "1.0018 + 0.006 * %s * parent().par.Warp" % BEAT
fb_xform.par.sx.expr = _warp
fb_xform.par.sy.expr = _warp
W(fb, fb_xform)
fb_level = C(levelTOP, 'veil_level', 720, -160, opacity=0.86)
fb_level.par.opacity.expr = "0.86 + 0.03 * %s" % BEAT   # trails linger on the beat
W(fb_xform, fb_level)

veil = C(compositeTOP, 'veil_comp', 890, 0, operand='maximum')
W(stars, veil, 0)
W(fb_level, veil, 1)
null_veil = C(nullTOP, 'null_veil', 1060, 0)
W(veil, null_veil)

fb.par.top = null_veil.path                      # close the loop LAST
fb.par.resetpulse.pulse()

# ---------------------------------------------------------------------------
# PALETTE — intensity → colour. Feeding slightly different r/g/b per star makes
# the lookup itself produce the hue variation (no per-op RGB fiddling).
# ---------------------------------------------------------------------------
pal_dat = C(tableDAT, 'palette_keys', 1060, 220)
pal_dat.clear()
pal_dat.appendRow(['pos', 'r', 'g', 'b', 'a'])
pal_dat.appendRow([0.00, 0.004, 0.006, 0.022, 1])   # void
pal_dat.appendRow([0.34, 0.045, 0.065, 0.210, 1])   # deep blue
pal_dat.appendRow([0.60, 0.205, 0.140, 0.445, 1])   # violet
pal_dat.appendRow([0.82, 0.360, 0.560, 0.820, 1])   # cool blue
pal_dat.appendRow([1.00, 0.940, 0.970, 1.000, 1])   # pale starlight

palette = C(rampTOP, 'palette', 1230, 220, dat='palette_keys')
res(palette, 256, 4, 'rgba16float')

colorize = C(lookupTOP, 'colorize', 1230, 0)
W(null_veil, colorize, 0)
W(palette, colorize, 1)

# ---------------------------------------------------------------------------
# PLANETS (GLSL #2 — two analytic spheres, no loops, no 3D render pass)
# ---------------------------------------------------------------------------
bands_src = C(noiseTOP, 'src_bands', 200, 420, period=1.6, harmon=4, amp=1.0,
              exp=1.2, mono=True)
res(bands_src, 256, 256, 'rgba16float')
bands_src.par.tz.expr = "absTime.seconds*0.02"

planets = C(glslTOP, 'planets', 380, 420)
res(planets)
W(bands_src, planets)
planets.par.vec0name = 'uPlanet'
planets.par.vec0valuex.expr = "absTime.seconds"
planets.par.vec0valuey.expr = ENERGY
planets.par.vec0valuez.expr = BASS
planets.par.vec0valuew.expr = BEAT
planets.par.vec = 2
planets.par.vec1name = 'uOrb'
planets.par.vec1valuex.expr = SPIN

s.op('planets_pixel').text = """uniform vec4 uPlanet;  // x time, y energy, z bass, w beat
uniform vec4 uOrb;     // x integrated spin phase (accelerates on each kick)
out vec4 fragColor;

vec4 over(vec4 f, vec4 b) { return f + b * (1.0 - f.a); }

// one lit sphere: analytic normal from the disc, lat/lon banding, limb rim, halo
vec4 body(vec2 uv, vec2 c, float R, float spin, vec3 L, vec3 tint,
          float bandScale, float atmo) {
    vec2 q = (uv - c) / R;
    float r2 = dot(q, q);
    float r  = sqrt(r2);
    vec4 res = vec4(0.0);

    float halo = exp(-max(r - 1.0, 0.0) * 9.0) * atmo;    // atmosphere glow
    res.rgb = halo * tint * 0.5;
    res.a   = halo * 0.35;

    if (r2 < 1.0) {
        vec3 n = vec3(q, sqrt(max(1.0 - r2, 0.0)));
        float lat = asin(clamp(n.y, -1.0, 1.0));
        float lon = atan(n.x, n.z) + spin;
        float tex = texture(sTD2DInputs[0],
                            vec2(fract(lon * 0.159154 * bandScale),
                                 lat * 0.3183 * 0.35 + 0.5)).r;
        // latitude dominates, noise only warps the band edges — reads as a gas
        // giant instead of marble
        float bands = 0.64 + 0.36 * sin(lat * 13.0 + tex * 1.7);
        bands *= 1.0 - 0.35 * pow(abs(sin(lat)), 3.0);                // dim poles
        float lam   = max(dot(n, L), 0.0);
        vec3 surf   = tint * bands * (0.03 + 0.70 * pow(lam, 0.9));
        surf += tint * pow(1.0 - n.z, 4.0) * pow(lam, 0.35) * 1.0;   // rim light
        float edge = smoothstep(1.0, 0.985, r);                       // AA the limb
        res.rgb = mix(res.rgb, surf, edge);
        res.a   = mix(res.a, 1.0, edge);
    }
    return res;
}

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv  = (gl_FragCoord.xy - 0.5 * res) / res.y;
    float t  = uPlanet.x;
    vec3 L   = normalize(vec3(-0.55, 0.42, 0.72));

    // gas giant, off-centre (break symmetry once) with a slow bob
    // the disc swells on bass, the atmosphere flares on the kick (both rest at idle)
    vec2 pc = vec2(0.30, -0.06 + 0.012 * sin(t * 0.07));
    vec4 p1 = body(uv, pc, 0.26 * (1.0 + 0.022 * uPlanet.z), uOrb.x, L,
                   vec3(0.55, 0.62, 0.95), 1.0,
                   0.9 + 0.5 * uPlanet.y + 0.8 * uPlanet.w);

    // moon on a slow ellipse — passes in front, then behind
    float a  = t * 0.055;
    vec2 mc  = pc + vec2(0.52 * cos(a), 0.17 * sin(a));
    vec4 p2  = body(uv, mc, 0.075, -uOrb.x * 0.57, L, vec3(0.68, 0.66, 0.62), 2.0, 0.30);

    vec4 c = (sin(a) < 0.0) ? over(p1, p2) : over(p2, p1);
    fragColor = TDOutputSwizzle(c);
}"""

# ---------------------------------------------------------------------------
# FINISH — planets over the veil, threshold bloom, upres, out rig
# ---------------------------------------------------------------------------
scene_comp = C(overTOP, 'comp_scene', 1400, 0)
W(planets, scene_comp, 0)                        # foreground
W(colorize, scene_comp, 1)                       # background

thresh = C(thresholdTOP, 'glow_thresh', 1570, -160, threshold=0.62)
W(scene_comp, thresh)
blur = C(blurTOP, 'glow_blur', 1740, -160, size=14, preshrink=2)
W(thresh, blur)
glow = C(compositeTOP, 'glow_add', 1910, 0, operand='add')
W(scene_comp, glow, 0)
W(blur, glow, 1)

upres = C(levelTOP, 'upres', 2080, 0, gamma1=0.95)
res(upres, OUTW, OUTH, 'rgba8fixed')
W(glow, upres)

final = C(nullTOP, 'final_out', 2250, 0)
W(upres, final)
out1 = C(outTOP, 'out1', 2420, 0)
W(final, out1)

scene_out = proj.create(outTOP, SCENE + '_out')
scene_out.nodeX, scene_out.nodeY = s.nodeX + 250, s.nodeY
s.outputConnectors[0].connect(scene_out.inputConnectors[0])

result = 'built ' + s.path
