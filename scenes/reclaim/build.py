# Reclaim — nature takes a brick wall back.
#
# A photographed brick wall is edge-traced to its mortar outlines. Audio drives a
# crack that spreads from a seed point, bricks darken and break, an L-System plant
# pushes through the gap, grows, blooms, and bees arrive at the flowers. Every cycle
# wakes another plant and thickens the garden.
#
# Idempotent: destroys and recreates /project1/reclaim (and its project-level Out TOP)
# and touches nothing else. Run via the MCP `run` tool:
#     code = open('scenes/reclaim/build.py').read()
#     g = dict(globals()); exec(code, g)
#
# Cost notes (M5, see MACHINE.md): the only per-frame CPU of consequence is the
# L-System of the plant currently growing (~1ms at Gens 5, 1521 points). Plants that
# have finished growing hold a constant `generations` and stop re-cooking. Three small
# numpy Script CHOPs (director / flower_inst / bee_inst) replace ~40 CHOPs of envelope
# math; together they run over <200 samples per frame.

import math
import os

SCENE = 'reclaim'
OUTW, OUTH = 1280, 720
ASPECT = OUTW / OUTH
ORTHOW = 2.0                      # camera ortho width -> world x in [-1, 1]
ORTHOH = ORTHOW / ASPECT          # world y in [-0.5625, 0.5625]
GENMAX = 6.0                      # L-System generations at full growth
MAXSITES = 96                     # hard cap on flower sites (all plants combined)
MAXBEES = 48

# Where the brick wall photo lives. First existing path wins.
WALL_CANDIDATES = [
    '/Users/visheshkochher/Projects/TouchAI/media/brick-wall.png',
    os.path.join(str(project.folder), 'media', 'brick-wall.png'),
    os.path.join(str(project.folder), '..', 'media', 'brick-wall.png'),
]

# Per-plant: base x, base y (world units), scale, lsystem random seed.
# Plant i is born on cycle i and stays for every cycle after.
# Per-plant: base x, base y, DESIRED on-screen height in world units, L-System seed.
# The actual geometry scale is measured from the grown plant at build time, so
# changing the rules never silently rescales the garden.
# Bases sit well inside the frame, not on the floor line: a crack centred at the
# bottom edge loses half its disc off-screen and stops reading as a break in the wall.
PLANTS = [
    (-0.56, -0.28, 0.72, 3),
    (0.06, -0.40, 0.60, 11),
    (0.62, -0.16, 0.48, 27),
]

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


def res(o, w=OUTW, h=OUTH, fmt='rgba16float'):
    o.par.outputresolution = 'custom'
    o.par.resmult = False
    o.par.resolutionw, o.par.resolutionh = w, h
    o.par.format = fmt
    return o


def soft(o, **params):
    """Set only the parameters this build actually has — some MAT/TOP param names
    differ between TD builds and a missing one should not abort the whole build."""
    missed = []
    for k, v in params.items():
        if hasattr(o.par, k):
            setattr(o.par, k, v)
        else:
            missed.append(k)
    if missed:
        print('  [soft] %s: no such params %s' % (o.name, missed))
    return o


# ---------------------------------------------------------------------------
# CUSTOM PARAMETERS — the live-performance surface
# ---------------------------------------------------------------------------
pg = s.appendCustomPage('Reclaim')
pg.appendMenu('Audiosrc', label='Audio Source')
s.par.Audiosrc.menuNames = ['device', 'file']
s.par.Audiosrc.menuLabels = ['Audio Device In', 'Audio File In (test)']
s.par.Audiosrc = 'file'

for nm, label, val, lo, hi in [
    ('Reactivity', 'Reactivity',        1.0, 0.0, 3.0),
    ('Devgain',    'Device In Gain',    6.0, 1.0, 30.0),
    ('Cyclelen',   'Cycle Length (s)', 20.0, 6.0, 60.0),
    ('Photomix',   'Wall Photo Mix',    0.62, 0.0, 1.0),
    ('Linebright', 'Brick Line Bright', 1.0, 0.0, 3.0),
    ('Crackamt',   'Crack Amount',      1.0, 0.0, 2.0),
    ('Flowersize', 'Flower Size',       1.0, 0.2, 3.0),
    ('Beecount',   'Bee Count',        24.0, 0.0, float(MAXBEES)),
    ('Beespeed',   'Bee Speed',         1.0, 0.0, 3.0),
    ('Glow',       'Glow',              1.0, 0.0, 3.0),
    ('Vignette',   'Vignette',          0.9, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

pg.appendPulse('Restart', label='Restart Cycle')

# ---------------------------------------------------------------------------
# AUDIO IN — device for performance, TD's bundled track for testing
# ---------------------------------------------------------------------------
adev = C(audiodeviceinCHOP, 'audio_device', 0, 1200)
adev.par.active.expr = "parent().par.Audiosrc.menuIndex == 0"

afile = C(audiofileinCHOP, 'audio_file', 0, 1320, repeat=True, play=True)
_rel = os.path.join('Samples', 'Audio', 'JeremyCaulfield_www.dumb-unit.com.mp3')
for _base in ('', 'Contents/Resources/tfs', 'tfs', 'Contents/Resources'):
    _cand = os.path.join(str(app.installFolder), _base, _rel)
    if os.path.exists(_cand):
        afile.par.file = _cand
        break

audio = C(switchCHOP, 'audio_src', 170, 1260)
audio.par.index.expr = "parent().par.Audiosrc.menuIndex"
W(adev, audio, 0)
W(afile, audio, 1)

mono = C(mathCHOP, 'audio_mono', 340, 1260, chanop='avg')
W(audio, mono)

# Device input sits far below a decoded file — give it its own gain stage.
gain = C(mathCHOP, 'audio_gain', 500, 1260)
gain.par.gain.expr = ("parent().par.Reactivity * (parent().par.Devgain.eval() "
                      "if parent().par.Audiosrc.menuIndex == 0 else 1.0)")
W(mono, gain)

# Canonical two-band chain (patterns.md). The resampleCHOP is mandatory: envelopeCHOP
# output stays at 44.1kHz and a filterCHOP on that convolves half a second of
# full-rate audio.
band_nulls = []
for nm, filt, cut, envw, fw, frm, to, ny in [
    ('bass', 'lowpass', 700.0, 0.15, 0.10, 0.7, 1.0, 1180),
    ('high', 'highpass', 3000.0, 0.15, 0.50, 0.5, 1.0, 1340),
]:
    af = C(audiofilterCHOP, 'af_' + nm, 660, ny, filter=filt)
    soft(af, cutofflog=math.log10(cut), cutofffrequency=cut)
    W(gain, af)
    en = C(envelopeCHOP, 'env_' + nm, 820, ny, width=envw)
    W(af, en)
    rs = C(resampleCHOP, 'rs_' + nm, 980, ny, method='rate', rate=60, timeslice=True)
    W(en, rs)
    mt = C(mathCHOP, 'math_' + nm, 1140, ny)
    mt.par.fromrange1, mt.par.fromrange2 = 0.0, frm
    mt.par.torange1, mt.par.torange2 = 0.0, to
    W(rs, mt)
    fl = C(filterCHOP, 'filt_' + nm, 1300, ny, type='gaussian')
    soft(fl, width=fw, widthunit='seconds')
    W(mt, fl)
    fl.par.renamefrom = '*'
    fl.par.renameto = nm
    band_nulls.append(fl)

# Overall energy — the slow "breath" of the track.
env_all = C(envelopeCHOP, 'env_energy', 820, 1460, width=0.35)
W(gain, env_all)
rs_all = C(resampleCHOP, 'rs_energy', 980, 1460, method='rate', rate=60, timeslice=True)
W(env_all, rs_all)
math_all = C(mathCHOP, 'math_energy', 1140, 1460)
math_all.par.fromrange1, math_all.par.fromrange2 = 0.0, 0.6
math_all.par.torange1, math_all.par.torange2 = 0.0, 1.0
W(rs_all, math_all)
filt_all = C(filterCHOP, 'filt_energy', 1300, 1460, type='gaussian')
soft(filt_all, width=0.8, widthunit='seconds')
W(math_all, filt_all)
filt_all.par.renamefrom = '*'
filt_all.par.renameto = 'energy'
band_nulls.append(filt_all)

bands = C(mergeCHOP, 'audio_bands', 1460, 1300)
for i, b in enumerate(band_nulls):
    W(b, bands, i)
null_audio = C(nullCHOP, 'null_audio', 1620, 1300)
W(bands, null_audio)

# ---------------------------------------------------------------------------
# CYCLE CLOCK — one timerCHOP, free-running, cycling forever.
# outcycleplusfraction is monotonic, so the director gets a continuous clock from it
# and never depends on the project timeline range.
# ---------------------------------------------------------------------------
timer = C(timerCHOP, 'cycle_timer', 0, 1000, lengthunits='seconds',
          cycle=True, cyclelimit=False, play=True,
          outfraction=True, outcycle=True, outcycleplusfraction=True)
timer.par.length.expr = "parent().par.Cyclelen"

# ---------------------------------------------------------------------------
# DIRECTOR — the whole show's state in one 1-sample CHOP.
# ---------------------------------------------------------------------------
dir_src = C(textDAT, 'director_src', 1780, 1120)
dir_src.text = '''# Director: turns the cycle timer + audio bands into every envelope the scene needs.
# Phase windows within a cycle:
#   crack 0.00-0.24   grow 0.14-0.60   bloom 0.50-0.80   bees 0.66-1.00
# Plant i is born on cycle i; from cycle i+1 on it simply stays grown.
NPLANTS = %d


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def env(p, a, b):
    if b <= a:
        return 1.0 if p >= b else 0.0
    return smooth((p - a) / (b - a))


def chan(inp, name, default=0.0):
    if inp is None:
        return default
    try:
        return float(inp[name][0])
    except Exception:
        return default


def onCook(scriptOp):
    tmr = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    aud = scriptOp.inputs[1] if len(scriptOp.inputs) > 1 else None
    par = scriptOp.parent().par

    frac = chan(tmr, 'timer_fraction', chan(tmr, 'fraction', 0.0))
    cyc = chan(tmr, 'cycles', chan(tmr, 'timer_cycles', 0.0))
    cyc_frac = chan(tmr, 'cycles_plus_fraction',
                    chan(tmr, 'timer_cycles_fraction', cyc + frac))

    cyclen = float(par.Cyclelen.eval())
    ctime = cyc_frac * cyclen

    bass = chan(aud, 'bass', 0.0)
    high = chan(aud, 'high', 0.0)
    energy = chan(aud, 'energy', 0.0)

    cyc_i = int(cyc)
    out = {'phase': frac, 'cycle': float(cyc_i), 'ctime': ctime,
           'bass': bass, 'high': high, 'energy': energy}

    # Bass makes the current growth surge; it never runs backwards.
    surge = 1.0 + 0.45 * bass

    for i in range(NPLANTS):
        born = cyc_i - i            # <0 not yet, 0 this cycle, >0 already grown
        if born < 0:
            crack = grow = bloom = bee = 0.0
        elif born == 0:
            crack = env(frac, 0.00, 0.24)
            grow = min(1.0, env(frac, 0.14, 0.60) * surge)
            bloom = env(frac, 0.50, 0.80)
            bee = env(frac, 0.66, 1.00)
        else:
            crack = 1.0
            grow = 1.0
            bloom = 1.0
            bee = 1.0
        out['crack%%d' %% i] = crack
        out['grow%%d' %% i] = grow
        out['bloom%%d' %% i] = bloom
        out['bee%%d' %% i] = bee
        # Later cycles keep adding flowers to plants that are already there.
        out['dens%%d' %% i] = min(1.0, 0.40 + 0.20 * max(0, born))

    # How full the garden is overall, 0..1 — drives bee count and glow.
    out['fullness'] = min(1.0, (cyc_i + frac) / float(NPLANTS + 1))

    scriptOp.clear()
    keys = sorted(out.keys())
    chans = [scriptOp.appendChan(k) for k in keys]
    scriptOp.numSamples = 1
    for c, k in zip(chans, keys):
        c[0] = out[k]
    return
''' % len(PLANTS)

director = C(scriptCHOP, 'director', 1940, 1120)
director.par.callbacks = dir_src.path
W(timer, director, 0)
W(null_audio, director, 1)


def D(ch):
    """Expression string reading a director channel, safe before it first cooks."""
    return "(op('director')['%s'] or 0)" % ch


# ---------------------------------------------------------------------------
# WALL — photo, edge-traced to its mortar outlines, then cracked open in GLSL
# ---------------------------------------------------------------------------
wall_path = ''
for cand in WALL_CANDIDATES:
    cand = os.path.abspath(cand)
    if os.path.exists(cand):
        wall_path = cand
        break
if not wall_path:
    print('  [warn] brick wall photo not found in %s' % WALL_CANDIDATES)

wall_src = C(moviefileinTOP, 'wall_src', 0, 500, file=wall_path)
wall_fit = C(fitTOP, 'wall_fit', 170, 500, fit='fitoutside')
res(wall_fit)
W(wall_src, wall_fit)

# The photo itself, pushed down to a dim warm base so the traced lines can sit on top.
wall_base = C(levelTOP, 'wall_base', 340, 420)
soft(wall_base, brightness1=0.72, contrast=1.05, blacklevel=0.0, gamma1=0.92)
wall_base.par.opacity.expr = "parent().par.Photomix"
W(wall_fit, wall_base)

# Outline trace: luminance edges of the brickwork = the mortar grid.
wall_mono = C(monochromeTOP, 'wall_mono', 340, 560)
W(wall_fit, wall_mono)
# Blur before the edge pass: straight off the photo, the brick grain reads as loud
# white speckle and swamps the mortar grid we actually want.
wall_soft = C(blurTOP, 'wall_soft', 500, 560, size=2.6)
W(wall_mono, wall_soft)
wall_edge = C(edgeTOP, 'wall_edge', 660, 560, strength=1.5)
soft(wall_edge, offset1=1.6, offset2=1.6, offset3=1.6,
     edgecolorr=1.0, edgecolorg=0.84, edgecolorb=0.62)   # warm ivory chalk
W(wall_soft, wall_edge)
wall_lines = C(levelTOP, 'wall_lines', 820, 560)
soft(wall_lines, gamma1=0.85, blacklevel=0.20, contrast=1.1)
wall_lines.par.opacity.expr = "0.75 * parent().par.Linebright"
W(wall_edge, wall_lines)

wall_mix = C(compositeTOP, 'wall_mix', 1300, 480, operand='add')
res(wall_mix)
W(wall_base, wall_mix, 0)
W(wall_lines, wall_mix, 1)

# --- crack shader: eats the wall away from each plant's seed point -----------
crack_src = C(glslmultiTOP, 'wall_crack', 1460, 480) if False else C(glslTOP, 'wall_crack', 1460, 480)
res(crack_src)
W(wall_mix, crack_src, 0)

crack_code = '''// Cracks radiating from each plant's seed point: a ridged-noise vein field masked by
// a growing disc. Also does the wall's final grade, so this is one pass, not four.
uniform vec4 uSeedA;    // xy seed in uv space, z growth radius, w active
uniform vec4 uSeedB;
uniform vec4 uSeedC;
uniform vec4 uParams;   // x time, y crack amount, z bass, w aspect
uniform vec4 uGrade;    // x vignette, y unused, z unused, w unused

out vec4 fragColor;

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float vnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash21(i);
    float b = hash21(i + vec2(1.0, 0.0));
    float c = hash21(i + vec2(0.0, 1.0));
    float d = hash21(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float s = 0.0;
    float a = 0.5;
    for (int i = 0; i < 5; i++) {
        s += a * vnoise(p);
        p = p * 2.07 + 11.3;
        a *= 0.5;
    }
    return s;
}

void main() {
    vec2 uv = vUV.st;
    vec4 wall = texture(sTD2DInputs[0], uv);
    vec2 p = vec2(uv.x * uParams.w, uv.y);

    vec4 seeds[3] = vec4[3](uSeedA, uSeedB, uSeedC);
    float crack = 0.0;   // thin fracture lines
    float rim = 0.0;     // dust glowing on the breaking edge
    float hole = 0.0;    // bricks actually gone

    for (int i = 0; i < 3; i++) {
        vec4 sd = seeds[i];
        if (sd.w < 0.01 || sd.z < 0.0005) continue;
        vec2 sp = vec2(sd.x * uParams.w, sd.y);
        vec2 pp = p + vec2(float(i) * 13.7, float(i) * 7.1);
        float R = sd.z;

        // A jagged break boundary: perturbing the radius is what stops the damage
        // reading as a soft circular smudge.
        float warp = fbm(pp * 6.0 + 77.0) - 0.5;
        float d = length(p - sp) * (1.0 + 0.55 * warp);
        if (d > R * 1.25) continue;

        // main fractures plus a finer web branching off them. The frequency is set
        // relative to the disc, not the frame, so a crack always reads as a crack.
        float v1 = 1.0 - abs(fbm(pp * 26.0) * 2.0 - 1.0);
        float v2 = 1.0 - abs(fbm(pp * 62.0 + 31.7) * 2.0 - 1.0);
        float web = clamp(smoothstep(0.86, 0.99, v1)
                        + 0.55 * smoothstep(0.90, 1.0, v2), 0.0, 1.0);

        float reach = 1.0 - smoothstep(R * 0.25, R * 1.05, d);
        float edge = smoothstep(R * 0.40, R * 0.85, d) *
                     (1.0 - smoothstep(R * 0.85, R * 1.20, d));

        crack = max(crack, web * reach * sd.w);
        rim = max(rim, web * edge * sd.w);
        hole = max(hole, (1.0 - smoothstep(R * 0.10, R * 0.40, d)) * sd.w);
    }

    float amt = uParams.y;
    crack = clamp(crack * amt, 0.0, 1.0);
    rim = clamp(rim * amt, 0.0, 1.0);
    hole = clamp(hole * amt, 0.0, 1.0);

    // Mostly a dark void where the brick has gone, with warm light bleeding along the
    // fracture edge. Weighted the other way it reads as lava rather than a broken wall.
    vec3 col = wall.rgb * (1.0 - 0.88 * crack);
    col = mix(col, vec3(0.010, 0.008, 0.010), max(crack * 0.78, hole * 0.94));
    col += vec3(1.00, 0.50, 0.18) * crack * (0.16 + 0.40 * uParams.z);
    col += vec3(1.00, 0.74, 0.40) * rim * (0.34 + 0.65 * uParams.z);

    vec2 q = uv - 0.5;
    col *= clamp(1.0 - uGrade.x * dot(q, q) * 1.6, 0.0, 1.0);

    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
'''
crack_dat = C(textDAT, 'wall_crack_pixel', 1460, 620)
crack_dat.text = crack_code
crack_src.par.pixeldat = crack_dat.path

# Uniforms via the Vectors page — the Constants page is broken on this build
# (MACHINE.md), and packing into vec4s is safe everywhere.
crack_src.par.vec = 5
for i, (px, py, _h, seed) in enumerate(PLANTS):
    nm = ['uSeedA', 'uSeedB', 'uSeedC'][i]
    setattr(crack_src.par, 'vec%dname' % i, nm)
    # world -> uv
    getattr(crack_src.par, 'vec%dvaluex' % i).val = 0.5 + px / ORTHOW
    getattr(crack_src.par, 'vec%dvaluey' % i).val = 0.5 + py / ORTHOH
    getattr(crack_src.par, 'vec%dvaluez' % i).expr = (
        "0.03 + 0.30 * %s" % D('crack%d' % i))
    getattr(crack_src.par, 'vec%dvaluew' % i).expr = (
        "1.0 if %s > 0.001 else 0.0" % D('crack%d' % i))

crack_src.par.vec3name = 'uParams'
crack_src.par.vec3valuex.expr = D('ctime')
crack_src.par.vec3valuey.expr = "parent().par.Crackamt"
crack_src.par.vec3valuez.expr = D('bass')
crack_src.par.vec3valuew.val = ASPECT

crack_src.par.vec4name = 'uGrade'
crack_src.par.vec4valuex.expr = "parent().par.Vignette"

# ---------------------------------------------------------------------------
# PLANTS — one L-System per plant, generations animated 0 -> GENMAX
# ---------------------------------------------------------------------------
rules = C(textDAT, 'plant_rules', 0, 100)
# Classic bushy plant (Prusinkiewicz & Lindenmayer, fig 1.24d). Note the Rules DAT
# wants NO space after ':' or '=' — with one it silently produces zero geometry.
# Rule C. The textbook `F=FF` bush grows a long bare stick before it branches at all
# (measured: zero spread over the bottom 30%); this one branches from the base up.
rules.text = "premise:A\nA=F[+A]F[-A]A\n"

# Tubes, not a wireframe skeleton: flat constant-width lines read as a wire mesh no
# matter what colour they are, while lit tapered tubes read as stems. 12k points at
# Gens 6 costs ~0.9ms to cook, so it is well inside budget.
stem_mat = C(phongMAT, 'mat_stem', 0, -60)
soft(stem_mat, diffr=0.26, diffg=0.40, diffb=0.20,
     ambr=0.09, ambg=0.13, ambb=0.07,
     specr=0.18, specg=0.21, specb=0.13, shininess=16.0)
# A small, clamped warm-up as the track gets loud - unclamped it drove the bush neon.
if hasattr(stem_mat.par, 'diffr'):
    stem_mat.par.diffr.expr = "0.24 + 0.08 * min(1.0, %s)" % D('energy')
    stem_mat.par.diffg.expr = "0.38 + 0.10 * min(1.0, %s)" % D('energy')

# Key light raking from the upper left, matching the photograph's own sunlight patch.
sun = C(lightCOMP, 'light_sun', 0, -160, lighttype='distant',
        cr=1.0, cg=0.92, cb=0.78, dimmer=1.15)
sun.par.tx, sun.par.ty, sun.par.tz = -2.0, 2.5, 3.0
sun.par.rx, sun.par.ry, sun.par.rz = -32.0, -28.0, 0.0
fill = C(lightCOMP, 'light_fill', 0, -230, lighttype='distant',
         cr=0.42, cg=0.52, cb=0.62, dimmer=0.55)
fill.par.rx, fill.par.ry, fill.par.rz = 18.0, 40.0, 0.0

plant_geos = []
plant_scales = []
for i, (px, py, height, seed) in enumerate(PLANTS):
    y = 100 - i * 170
    ls = C(lsystemSOP, 'plant%d_lsys' % i, 170, y, type='tube',
           angleinit=19.0, stepinit=0.1, stepscale=0.88, gravity=0.05,
           randscale=0.24, randseed=seed, contangl=True, contlength=True,
           # thickinit is scaled by the step size, not by plant height. Measured as
           # rendered silhouette coverage for one plant: 0.02 -> 0.7%, 0.06 -> 4.6%,
           # 0.30 -> 16% (a solid green blob). 0.06 keeps the branching legible.
           contwidth=True, thickinit=0.06, thickscale=0.80,
           rows=3, cols=5, smooth=0.35)
    ls.par.rules = rules.path
    ls.par.generations.expr = "%.2f * %s" % (GENMAX, D('grow%d' % i))

    # A second, static copy at full growth: flower sites are read off this, so they
    # stay put while the animated one grows. Constant params -> cooks once.
    lsf = C(lsystemSOP, 'plant%d_full' % i, 170, y - 80, type='skel',
            angleinit=19.0, stepinit=0.1, stepscale=0.88, gravity=0.05,
            randscale=0.24, randseed=seed, contangl=True, contlength=True,
            generations=GENMAX)
    lsf.par.rules = rules.path
    lsf.cook(force=True)
    ys_ = [pt.P[1] for pt in lsf.points] or [0.0, 1.0]
    span = max(1e-6, max(ys_) - min(ys_))
    scl = height / span

    geo = C(geometryCOMP, 'plant%d_geo' % i, 340, y, tx=px, ty=py, tz=0.0)
    geo.par.sx = geo.par.sy = geo.par.sz = scl
    geo.par.material = stem_mat.path
    # A slow sway that leans with the music.
    geo.par.rz.expr = ("2.6 * math.sin(%s * (0.31 + %0.3f) + %0.2f) * (0.5 + %s)"
                       % (D('ctime'), 0.04 * i, i * 2.1, D('energy')))
    ins = geo.op('torus1')
    if ins:
        ins.destroy()
    sel = geo.create(inSOP, 'in_stem') if False else None
    # Pull the L-System in with a Select SOP so the geometry lives outside the COMP.
    sel = geo.create(selectSOP, 'stem')
    sel.par.sop = ls.path
    sel.render = True
    sel.display = True
    sel.nodeX, sel.nodeY = 0, 0
    plant_geos.append(geo)
    plant_scales.append(scl)

# ---------------------------------------------------------------------------
# FLOWER SITES — branch tips of the fully-grown plants, in world space.
# Static input -> this cooks once, not per frame.
# ---------------------------------------------------------------------------
sites_src = C(textDAT, 'flower_sites_src', 500, 40)
sites_src.text = '''# Branch-end points of each fully grown L-System, transformed to world space and
# thinned to a manageable flower count. Depends only on the static *_full SOPs, so it
# cooks when the plant definition changes and then stops.
PLANTS = %r
MAXSITES = %d


def onCook(scriptOp):
    pts = []
    for pid, (px, py, scl, seed) in enumerate(PLANTS):
        sop = op('plant%%d_full' %% pid)
        if sop is None:
            continue
        ends = []
        for prim in sop.prims:
            if len(prim) < 2:
                continue
            P = prim[len(prim) - 1].point.P
            ends.append((P[0], P[1], P[2]))
        if not ends:
            continue
        # Prefer the highest tips, then thin evenly so flowers spread over the plant.
        ends.sort(key=lambda p: -p[1])
        budget = max(1, MAXSITES // max(1, len(PLANTS)))
        step = max(1, len(ends) // budget)
        for k in range(0, len(ends), step):
            if len([p for p in pts if p[4] == pid]) >= budget:
                break
            ex, ey, ez = ends[k]
            wx = px + ex * scl
            wy = py + ey * scl
            wz = ez * scl
            # stable per-flower randomness
            r = ((k * 2654435761) %% 10007) / 10007.0
            pts.append((wx, wy, wz, r, float(pid)))

    scriptOp.clear()
    names = ['tx', 'ty', 'tz', 'rnd', 'pid']
    chans = [scriptOp.appendChan(n) for n in names]
    scriptOp.numSamples = max(1, len(pts))
    if not pts:
        for c in chans:
            c[0] = 0.0
        return
    for j, p in enumerate(pts):
        for c, v in zip(chans, p):
            c[j] = v
    return
''' % ([(PLANTS[i][0], PLANTS[i][1], plant_scales[i], PLANTS[i][3])
         for i in range(len(PLANTS))], MAXSITES)

sites = C(scriptCHOP, 'flower_sites', 660, 40)
sites.par.callbacks = sites_src.path

# ---------------------------------------------------------------------------
# FLOWER INSTANCES — bloom timing, per-flower colour, audio breathing
# ---------------------------------------------------------------------------
finst_src = C(textDAT, 'flower_inst_src', 820, 40)
finst_src.text = '''# Per-flower transform + colour. ~90 samples of numpy per frame.
import numpy as np

NPLANTS = %d


def onCook(scriptOp):
    sites = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    d = scriptOp.inputs[1] if len(scriptOp.inputs) > 1 else None
    par = scriptOp.parent().par

    names = ['tx', 'ty', 'tz', 'sx', 'sy', 'sz', 'rz', 'cr', 'cg', 'cb']
    scriptOp.clear()
    chans = [scriptOp.appendChan(n) for n in names]

    if sites is None or d is None or sites.numSamples < 1:
        scriptOp.numSamples = 1
        for c in chans:
            c[0] = 0.0
        return

    n = sites.numSamples
    tx = np.array(sites['tx'].vals, dtype=np.float32)
    ty = np.array(sites['ty'].vals, dtype=np.float32)
    tz = np.array(sites['tz'].vals, dtype=np.float32)
    rnd = np.array(sites['rnd'].vals, dtype=np.float32)
    pid = np.array(sites['pid'].vals, dtype=np.float32).astype(np.int32)

    def dc(name, default=0.0):
        try:
            return float(d[name][0])
        except Exception:
            return default

    t = dc('ctime')
    bass = dc('bass')
    energy = dc('energy')
    size = float(par.Flowersize.eval())

    bloom = np.zeros(n, dtype=np.float32)
    dens = np.zeros(n, dtype=np.float32)
    for i in range(NPLANTS):
        m = (pid == i)
        if not m.any():
            continue
        bloom[m] = dc('bloom%%d' %% i)
        dens[m] = dc('dens%%d' %% i)

    # Each flower opens at its own moment inside the bloom window, and only the
    # fraction of sites allowed by this plant's density ever opens at all.
    delay = np.mod(rnd * 7.13, 1.0)
    local = np.clip((bloom - delay * 0.55) / 0.45, 0.0, 1.0)
    local = local * local * (3.0 - 2.0 * local)
    allowed = (rnd < dens).astype(np.float32)

    # overshoot then settle - flowers pop rather than fade in
    pop = 1.0 + 0.35 * np.sin(np.clip(local, 0.0, 1.0) * np.pi) * (1.0 - local)
    scale = local * allowed * pop * (0.026 + 0.020 * np.mod(rnd * 3.7, 1.0)) * size
    scale = scale * (1.0 + 0.16 * bass)

    sway = 0.012 * np.sin(t * 0.9 + rnd * 12.0) * local
    rot = np.mod(rnd * 360.0, 360.0) + 8.0 * np.sin(t * 0.7 + rnd * 5.0)

    # Cream / butter / coral / rose - warm hues that sit with the brick rather than
    # fighting it. Only the top of the range goes properly pink.
    h = np.mod(rnd * 2.7, 1.0)
    cr = 1.00 - 0.06 * h
    cg = 0.86 - 0.46 * h + 0.08 * energy
    cb = 0.58 - 0.16 * h + 0.12 * np.mod(rnd * 5.1, 1.0)
    lift = (0.90 + 0.25 * energy)

    scriptOp.numSamples = n
    data = [tx + sway, ty, tz + 0.02, scale, scale, scale, rot,
            cr * lift, cg * lift, cb * lift]
    for c, v in zip(chans, data):
        c.vals = np.asarray(v, dtype=np.float32).tolist()
    return
''' % len(PLANTS)

finst = C(scriptCHOP, 'flower_inst', 980, 40)
finst.par.callbacks = finst_src.path
W(sites, finst, 0)
W(director, finst, 1)

# ---------------------------------------------------------------------------
# BEE INSTANCES — arrive late in the cycle, orbit the flowers they picked
# ---------------------------------------------------------------------------
binst_src = C(textDAT, 'bee_inst_src', 820, -120)
binst_src.text = '''# Bees pick a flower each and orbit it, arriving from off-frame as the bee window
# opens. Highs make them jittery; the garden's fullness decides how many show up.
import numpy as np

NPLANTS = %d
MAXBEES = %d


def onCook(scriptOp):
    sites = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    d = scriptOp.inputs[1] if len(scriptOp.inputs) > 1 else None
    par = scriptOp.parent().par

    names = ['tx', 'ty', 'tz', 'sx', 'sy', 'sz', 'rz']
    scriptOp.clear()
    chans = [scriptOp.appendChan(n) for n in names]

    def dc(name, default=0.0):
        try:
            return float(d[name][0])
        except Exception:
            return default

    if sites is None or d is None or sites.numSamples < 1:
        scriptOp.numSamples = 1
        for c in chans:
            c[0] = 0.0
        return

    t = dc('ctime')
    high = dc('high')
    fullness = dc('fullness')

    # Only flowers on plants whose bee window has opened are worth visiting.
    pid = np.array(sites['pid'].vals, dtype=np.float32).astype(np.int32)
    beeenv = np.zeros(NPLANTS, dtype=np.float32)
    for i in range(NPLANTS):
        beeenv[i] = dc('bee%%d' %% i)
    live = np.where(beeenv[np.clip(pid, 0, NPLANTS - 1)] > 0.02)[0]
    nb = int(round(float(par.Beecount.eval()) * min(1.0, 0.35 + fullness)))
    nb = max(0, min(MAXBEES, nb))
    if len(live) == 0 or nb == 0:
        scriptOp.numSamples = 1
        for c in chans:
            c[0] = 0.0
        chans[3][0] = chans[4][0] = chans[5][0] = 0.0
        return

    ftx = np.array(sites['tx'].vals, dtype=np.float32)
    fty = np.array(sites['ty'].vals, dtype=np.float32)

    idx = np.arange(nb)
    pick = live[(idx * 7 + 3) %% len(live)]
    ax = ftx[pick]
    ay = fty[pick]
    apid = pid[pick]

    r1 = np.mod(np.sin(idx * 12.9898) * 43758.5453, 1.0)
    r2 = np.mod(np.sin(idx * 78.233) * 12345.6789, 1.0)
    r3 = np.mod(np.sin(idx * 39.425) * 24634.6345, 1.0)

    speed = float(par.Beespeed.eval()) * (0.9 + 1.4 * r1) * (1.0 + 1.2 * high)
    ang = t * speed + r2 * 6.2831
    rad = (0.075 + 0.075 * r3) * (1.0 + 0.5 * high)

    ox = np.cos(ang) * rad
    oy = np.sin(ang * 1.3 + r1 * 3.0) * rad * 0.8
    # a small figure-eight wobble so the orbit never reads as a perfect circle
    ox = ox + 0.018 * np.sin(ang * 2.7 + r3 * 4.0)
    oy = oy + 0.014 * np.cos(ang * 3.1 + r2 * 4.0)

    arrive = beeenv[np.clip(apid, 0, NPLANTS - 1)]
    arrive = np.clip((arrive - r1 * 0.35) / 0.65, 0.0, 1.0)
    arrive = arrive * arrive * (3.0 - 2.0 * arrive)

    # fly in from just off the sides
    entry_x = np.where(r2 > 0.5, 1.35, -1.35)
    entry_y = ay + (r3 - 0.5) * 0.5
    bx = entry_x + (ax + ox - entry_x) * arrive
    by = entry_y + (ay + oy - entry_y) * arrive

    sz = arrive * (0.034 + 0.018 * r3)
    # heading, so the bee tilts into its travel direction
    rz = np.degrees(np.arctan2(np.cos(ang * 1.3 + r1 * 3.0), -np.sin(ang))) - 90.0

    scriptOp.numSamples = nb
    data = [bx, by, np.full(nb, 0.06, dtype=np.float32), sz, sz, sz, rz]
    for c, v in zip(chans, data):
        c.vals = np.asarray(v, dtype=np.float32).tolist()
    return
''' % (len(PLANTS), MAXBEES)

binst = C(scriptCHOP, 'bee_inst', 980, -120)
binst.par.callbacks = binst_src.path
W(sites, binst, 0)
W(director, binst, 1)

# ---------------------------------------------------------------------------
# FLOWER + BEE SPRITES — tiny GLSL textures on camera-facing quads
# ---------------------------------------------------------------------------
flower_tex = C(glslTOP, 'flower_tex', 1140, 40)
res(flower_tex, 256, 256)
flower_dat = C(textDAT, 'flower_tex_pixel', 1140, -30)
flower_dat.text = '''// A five-petal bloom: polar rose curve for the silhouette, warm disc at the centre.
uniform vec4 uF;   // x petal count
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st * 2.0 - 1.0;
    float r = length(uv);
    float a = atan(uv.y, uv.x);
    float petals = max(3.0, uF.x);

    float shape = 0.50 + 0.32 * cos(petals * a);
    float m = 1.0 - smoothstep(shape - 0.12, shape, r);

    float lobe = 0.5 + 0.5 * cos(petals * a);
    // Kept close to neutral: the geometry COMP multiplies a per-flower colour over
    // this, and a strongly tinted texture would crush every flower to one hue.
    vec3 petal = mix(vec3(1.00, 0.97, 0.95), vec3(0.86, 0.72, 0.74),
                     smoothstep(0.05, 0.72, r));
    petal *= 0.72 + 0.40 * lobe;

    float core = 1.0 - smoothstep(0.09, 0.17, r);
    float ring = smoothstep(0.15, 0.11, r) * smoothstep(0.05, 0.10, r);
    vec3 col = mix(petal, vec3(1.00, 0.80, 0.22), core);
    col += vec3(0.30, 0.18, 0.04) * ring;

    // premultiplied - the MAT blends one / one-minus-src-alpha
    fragColor = TDOutputSwizzle(vec4(col * m, m));
}
'''
flower_tex.par.pixeldat = flower_dat.path
flower_tex.par.vec = 1
flower_tex.par.vec0name = 'uF'
flower_tex.par.vec0valuex.val = 5.0

bee_tex = C(glslTOP, 'bee_tex', 1140, -120)
res(bee_tex, 64, 64)
bee_dat = C(textDAT, 'bee_tex_pixel', 1140, -190)
bee_dat.text = '''// A bee at 10 screen pixels: striped amber body, two pale wings.
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st * 2.0 - 1.0;

    vec2 b = uv * vec2(1.7, 1.15);
    float body = 1.0 - smoothstep(0.78, 1.00, length(b));
    float stripe = smoothstep(0.0, 0.30, sin(uv.x * 11.0));
    vec3 bodycol = mix(vec3(1.00, 0.76, 0.16), vec3(0.10, 0.07, 0.04), stripe * 0.88);

    vec2 w1 = (uv - vec2(-0.18, 0.50)) * vec2(2.4, 3.4);
    vec2 w2 = (uv - vec2(0.26, 0.46)) * vec2(2.8, 3.8);
    float wing = (1.0 - smoothstep(0.60, 1.00, length(w1))) * 0.30
               + (1.0 - smoothstep(0.60, 1.00, length(w2))) * 0.22;

    float a = clamp(body + wing, 0.0, 1.0);
    vec3 col = mix(vec3(0.72, 0.78, 0.88), bodycol, body);

    fragColor = TDOutputSwizzle(vec4(col * a, a));
}
'''
bee_tex.par.pixeldat = bee_dat.path

# rectangleSOP's own `texture` toggle does not produce a uv attribute on this build —
# without a Texture SOP the sprites render untextured and the render TOP warns about it.
flower_rect = C(rectangleSOP, 'flower_rect', 1240, 40, sizex=1.0, sizey=1.0)
flower_quad = C(textureSOP, 'flower_quad', 1300, 40, type='rowcol')
W(flower_rect, flower_quad)
bee_rect = C(rectangleSOP, 'bee_rect', 1240, -120, sizex=1.0, sizey=0.62)
bee_quad = C(textureSOP, 'bee_quad', 1300, -120, type='rowcol')
W(bee_rect, bee_quad)

mat_flower = C(constantMAT, 'mat_flower', 1300, 110)
mat_flower.par.colormap = flower_tex.path
soft(mat_flower, alpha=1.0, blending=True, depthtest=False)

mat_bee = C(constantMAT, 'mat_bee', 1300, -50)
mat_bee.par.colormap = bee_tex.path
soft(mat_bee, alpha=1.0, blending=True, depthtest=False)

flowers = C(geometryCOMP, 'flowers', 1460, 40)
fq = flowers.op('torus1')
if fq:
    fq.destroy()
fsel = flowers.create(selectSOP, 'quad')
fsel.par.sop = flower_quad.path
fsel.render = True
fsel.display = True
flowers.par.material = mat_flower.path
flowers.par.instancing = True
flowers.par.instanceop = finst.path
for p, v in (('instancetx', 'tx'), ('instancety', 'ty'), ('instancetz', 'tz'),
             ('instancesx', 'sx'), ('instancesy', 'sy'), ('instancesz', 'sz'),
             ('instancerz', 'rz')):
    soft(flowers, **{p: v})
soft(flowers, instancecolormode='multiply', instancer='cr',
     instanceg='cg', instanceb='cb')

bees = C(geometryCOMP, 'bees', 1460, -120)
bq = bees.op('torus1')
if bq:
    bq.destroy()
bsel = bees.create(selectSOP, 'quad')
bsel.par.sop = bee_quad.path
bsel.render = True
bsel.display = True
bees.par.material = mat_bee.path
bees.par.instancing = True
bees.par.instanceop = binst.path
for p, v in (('instancetx', 'tx'), ('instancety', 'ty'), ('instancetz', 'tz'),
             ('instancesx', 'sx'), ('instancesy', 'sy'), ('instancesz', 'sz'),
             ('instancerz', 'rz')):
    soft(bees, **{p: v})

# ---------------------------------------------------------------------------
# RENDER + COMPOSITE
# ---------------------------------------------------------------------------
cam = C(cameraCOMP, 'cam', 1620, -60, projection='ortho', tz=4.0)
soft(cam, orthowidth=ORTHOW, near=0.1, far=20.0)

render = C(renderTOP, 'render_garden', 1780, -60)
res(render)
render.par.camera = cam.path
render.par.geometry = 'plant0_geo plant1_geo plant2_geo flowers bees'
render.par.lights = 'light_sun light_fill'
render.par.bgcolora = 0.0
soft(render, antialias='msaa4x', transparency=True)

comp = C(compositeTOP, 'comp_scene', 1940, 300, operand='over')
res(comp)
W(render, comp, 0)      # top layer first for compositeTOP 'over'
W(crack_src, comp, 1)

# Bloom: pull the bright bits, blur, add back. Cheap and it makes the flowers sing.
glow_cut = C(levelTOP, 'glow_cut', 1940, 460)
soft(glow_cut, blacklevel=0.55, gamma1=1.3)
W(comp, glow_cut)
glow_blur = C(blurTOP, 'glow_blur', 2100, 460, size=22.0)
res(glow_blur, OUTW // 2, OUTH // 2)
W(glow_cut, glow_blur)
glow_lvl = C(levelTOP, 'glow_lvl', 2260, 460)
glow_lvl.par.opacity.expr = "0.55 * parent().par.Glow * (0.6 + 0.7 * %s)" % D('energy')
W(glow_blur, glow_lvl)

comp_glow = C(compositeTOP, 'comp_glow', 2260, 300, operand='add')
res(comp_glow)
W(comp, comp_glow, 0)
W(glow_lvl, comp_glow, 1)

grade = C(levelTOP, 'grade', 2420, 300)
soft(grade, gamma1=0.88, contrast=1.04, blacklevel=0.0, brightness1=1.12)
W(comp_glow, grade)

final_out = C(nullTOP, 'final_out', 2580, 300)
W(grade, final_out)

out1 = C(outTOP, 'out1', 2740, 300)
W(final_out, out1)

# Project-level endpoint, per the repo's output-rig convention.
pout = proj.create(outTOP, SCENE + '_out')
pout.nodeX, pout.nodeY = 400, -400
s.outputConnectors[0].connect(pout.inputConnectors[0])

# ---------------------------------------------------------------------------
# Restart pulse -> re-cue the cycle timer.
# ---------------------------------------------------------------------------
pexec = C(parameterexecuteDAT, 'restart_exec', 1940, 1000)
pexec.text = '''def onPulse(par):
    if par.name == 'Restart':
        t = par.owner.op('cycle_timer')
        if t:
            # start alone resumes the timer but leaves the cycle counter where it
            # was, so the garden would come back already full. initialize zeroes it.
            t.par.initialize.pulse()
            t.par.start.pulse()
    return
'''
pexec.par.op = s.path
soft(pexec, pars='Restart', valuechange=False, onpulse=True)

s.par.display = True
s.par.opviewer = final_out.path

timer.par.initialize.pulse()
timer.par.start.pulse()

print('built %s' % s.path)
print('  wall photo: %s' % (wall_path or 'NOT FOUND'))
print('  timer chans: %s' % [c.name for c in timer.chans()])
print('  director chans: %s' % [c.name for c in director.chans()])
print('  flower sites: %d' % sites.numSamples)
