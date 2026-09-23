# Voyage — the man from `homestead` takes his bamboo raft off the river one night,
# flies out past the Moon, a ringed giant, a comet, a nebula and a spiral galaxy,
# and comes home through the dawn clouds to land on the river by his house.
#
# THE CAMERA IS BEHIND HIM. We see the back of his head — the faded red cloth
# knotted at the back, its tails streaming — and the path forward: everything he
# flies toward sits at one vanishing point ahead of him and GROWS as he approaches,
# then slides past to the side. Stars stream outward past him. The vantage point is
# his, so the audience travels with him rather than watching him travel.
#
# SAME STYLE AS HOMESTEAD, and much of the same code. The world is painted in one
# shader (the sky, hills, jungle and river are homestead's own functions, verbatim);
# everything that lives or is built is a flat cel with a hard shadow side and a bold
# outline (homestead's primitive and his house and tree, verbatim). The universe is
# kept dim and pastel, so the lantern on his raft is always the warmest thing in it.
#
# AUDIO IS IN THE PACE. Tempo is the story clock. Energy is how fast he flies: how
# fast the stars and space dust stream past, integrated, so the music changes his
# speed and never jerks the frame. The kick is a gentle breath of glow in the lantern,
# the sun and the moon. Bass flutters his head-cloth and the pennant; highs twinkle
# the stars; a drop sends a shooting star over the top of the frame.
#
# BUILT TO RUN ALL NIGHT. The story loops through black; every integrated phase
# returns to zero inside the black; every list is hard-capped (see homestead).
#
# Idempotent: destroys and recreates /project1/voyage and its project-level Out TOP,
# and touches nothing else. No media files.
#     code = open('scenes/voyage/build.py', encoding='utf-8').read()
#     g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
#
# GENERATED: this file is assembled from a template plus verbatim blocks of
# scenes/homestead/build.py (marked BEGIN/END HOMESTEAD). Edit homestead's copy of a
# shared block if the fix belongs to both scenes.

import math
import os

SCENE = 'voyage'
OUTW, OUTH = 1280, 720
ASPECT = OUTW / OUTH
ORTHOW = 1.80
ORTHOH = ORTHOW / ASPECT
CAMX, CAMY = 0.0, 0.0
CLOCKLEN = 60.0

STORYDEF = 330.0
MAXSEG = 12000

# the vanishing point: where the path forward goes, just above his head
VPX, VPY = 0.05, 0.125
# the horizon of the painted world (homestead's FARY, raised for a forward view)
FARY = 0.105
# where he stands, from behind, and how big he is
MANX, MANGY, MANSC = -0.090, -0.405, 0.370
RAFTX, RAFTY = -0.050, -0.465          # centre of the raft's near edge

# homestead's geography, needed by its verbatim house and tree generators
SHOREY, SHOREX, BANKK, BANKH = -0.125, 0.160, 0.600, 0.440
GYH, FLOORY, WALLTOP = -0.265, -0.195, 0.012
HX0, HX1 = -0.640, -0.205
WX, WY, WR, WWL = 0.530, -0.205, 0.092, -0.270
BULB = (-0.188, -0.030)
GARDEN = (-0.115, 0.235, -0.505, -0.365)
ROWS = (-0.385, -0.430, -0.475)
TREEX = -0.905
# his house sits on the left bank, seen from the river, scaled into the distance
HOUSEK, HOUSEX, HOUSEY = 0.52, -0.600, 0.020

CHECKPOINTS = [
    ('liftoff', ' 1 - Lift Off',               0.000),
    ('clouds',  ' 2 - Through the Clouds',     0.100),
    ('earth',   ' 3 - Sunrise Over the Earth', 0.190),
    ('moon',    ' 4 - The Moon',               0.300),
    ('rings',   ' 5 - The Ringed Giant',       0.415),
    ('comet',   ' 6 - A Comet',                0.530),
    ('nebula',  ' 7 - Where Stars Are Born',   0.640),
    ('galaxy',  ' 8 - The Spiral',             0.750),
    ('home',    ' 9 - Home',                   0.860),
]

# --- the journey, as tables against the story fraction f ---------------------------
# altitude: 0 on the river, clouds at ~1, space from ~2.4; up, and back down at dawn
ALT_F = (0.000, 0.035, 0.100, 0.150, 0.190, 0.905, 0.940, 0.965, 0.985, 1.000)
ALT_A = (0.000, 0.000, 0.900, 2.100, 3.600, 3.600, 2.100, 0.900, 0.000, 0.000)
# the painted ground's sun: night when he leaves, dawn when he lands
GSUN_F = (0.00, 0.50, 0.93, 1.00)
GSUN_H = (-0.55, -0.55, 0.00, 0.12)
# ambient light on the cels, chapter by chapter — dim and pastel throughout
AMB_F = (0.00, 0.10, 0.20, 0.31, 0.43, 0.54, 0.65, 0.76, 0.87, 0.92, 0.96, 1.00)
AMB_R = (0.30, 0.32, 0.58, 0.52, 0.64, 0.46, 0.60, 0.48, 0.52, 0.74, 0.62, 0.62)
AMB_G = (0.30, 0.33, 0.56, 0.52, 0.55, 0.50, 0.46, 0.45, 0.56, 0.52, 0.52, 0.54)
AMB_B = (0.44, 0.48, 0.64, 0.60, 0.45, 0.62, 0.60, 0.62, 0.68, 0.42, 0.50, 0.48)
# which side the key light is on (for the lit edge of every cel): +1 right, -1 left
KEY_F = (0.00, 0.30, 0.42, 0.53, 0.65, 0.76, 0.87, 1.00)
KEY_X = (1.00, 1.00, -1.00, 1.00, -1.00, 1.00, 1.00, 1.00)
# departure: the Earth's limb below the horizon, sinking away (y of the disc's top)
EDEP_F = (0.130, 0.190, 0.260, 0.315)
EDEP_T = (0.090, -0.060, -0.280, -0.760)
# celestial objects ahead: offset from the vanishing point (x, y), true radius R, and
# depth z(f). Screen centre = VP + offset / z, screen radius = R / z. As z falls the
# object grows and slides outward; each has a long near plateau so he can look.
MOON = dict(O=(0.62, 0.20), R=0.36, F=(0.290, 0.340, 0.395, 0.435), Z=(30.0, 2.6, 1.55, 0.42))
SAT = dict(O=(-0.66, 0.14), R=0.30, F=(0.400, 0.455, 0.505, 0.548), Z=(30.0, 3.0, 1.85, 0.45))
GAL = dict(O=(0.10, 0.06), R=1.60, F=(0.735, 0.790, 0.860), Z=(16.0, 5.0, 3.0))
EHOME = dict(O=(0.00, -0.05), R=0.90, F=(0.855, 0.890, 0.905, 0.930), Z=(45.0, 5.0, 1.60, 0.95))

PAL = dict(
    INK=(0.090, 0.062, 0.050),
    SKIN=(0.500, 0.315, 0.205), SKINLT=(0.660, 0.445, 0.305),
    SHIRT=(0.585, 0.520, 0.380), SHIRTLT=(0.735, 0.670, 0.505),
    PATCH=(0.360, 0.420, 0.500), PATCH2=(0.560, 0.300, 0.240),
    DHOTI=(0.705, 0.670, 0.575), DHOTILT=(0.845, 0.815, 0.730),
    CLOTHR=(0.600, 0.215, 0.175), CLOTHRLT=(0.760, 0.330, 0.255),
    BEARD=(0.200, 0.165, 0.145),
    BAMB=(0.600, 0.525, 0.300), BAMBLT=(0.790, 0.710, 0.440),
    BAMBDK=(0.420, 0.350, 0.180),
    MUD=(0.560, 0.420, 0.285), MUDLT=(0.680, 0.540, 0.380),
    THATCH=(0.660, 0.545, 0.300), THATCHLT=(0.840, 0.740, 0.470),
    THATCHDK=(0.470, 0.375, 0.190),
    DARKIN=(0.075, 0.055, 0.045),
    CLAY=(0.620, 0.330, 0.210), CLAYLT=(0.780, 0.450, 0.300),
    WOOD=(0.420, 0.290, 0.180), WOODLT=(0.580, 0.420, 0.270),
    WOODEND=(0.720, 0.590, 0.400),
    IRON=(0.330, 0.340, 0.360), IRONLT=(0.560, 0.580, 0.600),
    LEAF=(0.235, 0.400, 0.150), LEAFLT=(0.400, 0.600, 0.220),
    LEAFDK=(0.130, 0.240, 0.100),
    TRUNK=(0.300, 0.225, 0.165), TRUNKLT=(0.450, 0.345, 0.250),
    ROPE=(0.560, 0.470, 0.320),
    WARM=(1.000, 0.680, 0.380),
    DUST=(0.880, 0.860, 1.000),
    PLASMA=(1.000, 0.560, 0.280),
    WATER=(0.300, 0.420, 0.460),
)

proj = op('/project1')
for stale in (SCENE, SCENE + '_out'):
    o = proj.op(stale)
    if o:
        o.destroy()

s = proj.create(containerCOMP, SCENE)
s.nodeX, s.nodeY = 0, -2600
s.par.w, s.par.h = OUTW, OUTH


# ---- BEGIN HOMESTEAD (verbatim) ----
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
    missed = []
    for k, v in params.items():
        if hasattr(o.par, k):
            setattr(o.par, k, v)
        else:
            missed.append(k)
    if missed:
        print('  [soft] %s: no such params %s' % (o.name, missed))
    return o


def menu_pick(par, *wanted):
    """Set a menu parameter to the first of `wanted` that actually exists.

    TD accepts an invalid menu value SILENTLY and lands on entry zero. Never assign
    a menu value you have not seen in the list.
    """
    names = list(par.menuNames or [])
    for wname in wanted:
        if wname in names:
            par.val = wname
            return wname
    print('  [menu] %s: none of %s in %s' % (par.name, wanted, names))
    return par.eval()


# EVERY INTERNAL REFERENCE IS RELATIVE (see bayou): an absolute path makes a copy
# of this COMP, or a second .tox of it, silently drive the ORIGINAL's DATs.


def hdr(**kw):
    return ''.join('%s = %r\n' % (k, v) for k, v in sorted(kw.items())) + '\n'
# ---- END HOMESTEAD ----


# ---------------------------------------------------------------------------
# PERFORMANCE SURFACE
# ---------------------------------------------------------------------------
pg = s.appendCustomPage('Voyage')
pg.appendMenu('Audiosrc', label='Audio Source')
s.par.Audiosrc.menuNames = ['device', 'file']
s.par.Audiosrc.menuLabels = ['Audio Device In', 'Audio File In (test)']
s.par.Audiosrc = 'file'

for nm, label, val, lo, hi in [
    ('Reactivity', 'Reactivity',          1.0, 0.0, 3.0),
    ('Devgain',    'Device In Gain',      6.0, 1.0, 30.0),
    ('Storylen',   'Story Length (s)', STORYDEF, 60.0, 2400.0),
    ('Refbpm',     'Reference BPM',     124.0, 60.0, 200.0),
    ('Beatdrive',  'Beat Drive',          1.0, 0.0, 1.0),
    ('Timeoffset', 'Time Offset (s)',     0.0, -600.0, 3000.0),
    ('Paceaudio',  'Energy Drives Speed', 1.0, 0.0, 3.0),
    ('Brightness', 'Brightness',          1.0, 0.2, 2.0),
    ('Ink',        'Brightness of Art',   1.0, 0.0, 2.0),
    ('Glow',       'Glow',                1.0, 0.0, 3.0),
    ('Label',      'Chapter Readout',     1.0, 0.0, 2.0),
    ('Vignette',   'Vignette',            0.70, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

# Read-only readouts. Most of them are also the world shader's uniforms: the engine
# works the journey out once per frame and the shader reads it from here.
_RO = [('Bpm', 0, 200), ('Showt', 0, 2400), ('Chapter', 0, len(CHECKPOINTS)),
       ('Alt', 0, 5), ('Sf', 0, 1), ('Travel', 0, 1e6), ('Gsun', -1, 1),
       ('Bulb', 0, 1), ('Reentry', 0, 1), ('Fade', 0, 1), ('Loops', 0, 1e6),
       ('Warp', 0, 3),
       ('Ex', -9, 9), ('Ey', -9, 9), ('Er', 0, 9), ('Ea', 0, 1), ('Erot', 0, 1e6),
       ('Mx', -9, 9), ('My', -9, 9), ('Mr', 0, 9), ('Ma', 0, 1),
       ('Sx', -9, 9), ('Sy', -9, 9), ('Sr', 0, 9), ('Sa', 0, 1),
       ('Kx', -9, 9), ('Ky', -9, 9), ('Ka', 0, 1),
       ('Gx', -9, 9), ('Gy', -9, 9), ('Gr', 0, 9), ('Ga', 0, 1), ('Grot', 0, 1e6),
       ('Na', 0, 1), ('Nz', 0, 9),
       ('Px', -9, 9), ('Py', -9, 9), ('Pa', 0, 1),
       ('Lx', -1, 1), ('Ly', -1, 1), ('Lz', -1, 1),
       ('Rejects', 0, 1e6), ('Segs', 0, MAXSEG), ('Labelfade', 0, 1),
       ('Bassm', 0, 1), ('Highm', 0, 1), ('Energym', 0, 1)]
for _mn, _lo, _hi in _RO:
    pg.appendFloat(_mn, label=_mn)
    _p = getattr(s.par, _mn)
    _p.normMin, _p.normMax = _lo, _hi
    _p.readOnly = True
s.par.Fade.val = 1.0

pg.appendToggle('Loop', label='Loop the Story')
s.par.Loop.default = True
s.par.Loop.val = True
pg.appendStr('Scaletxt', label='Chapter Text')
s.par.Scaletxt.readOnly = True
s.par.Scaletxt.val = ''

pg.appendPulse('Star', label='S - SHOOTING STAR')
pg.appendPulse('Reseed', label='N - RESEED')
pg.appendPulse('Restart', label='0 - RESTART')
pg.appendPulse('Nextcp', label='next chapter')
pg.appendPulse('Prevcp', label='previous chapter')
for cp, label, _f in CHECKPOINTS:
    pg.appendPulse('Go' + cp, label=label)

# ---------------------------------------------------------------------------
# AUDIO FRONT END, CLOCK, TEMPO — verbatim from homestead
# ---------------------------------------------------------------------------
# ---- BEGIN HOMESTEAD (verbatim) ----
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

gain = C(mathCHOP, 'audio_gain', 500, 1260)
gain.par.gain.expr = ("parent().par.Reactivity * (parent().par.Devgain.eval() "
                      "if parent().par.Audiosrc.menuIndex == 0 else 1.0)")
W(mono, gain)

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

env_all = C(envelopeCHOP, 'env_energy', 820, 1460, width=0.35)
W(gain, env_all)
rs_all = C(resampleCHOP, 'rs_energy', 980, 1460, method='rate', rate=60,
           timeslice=True)
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
# MASTER CLOCK — one free-running timerCHOP, never seeked.
# ---------------------------------------------------------------------------
timer = C(timerCHOP, 'clock', 0, 1000, lengthunits='seconds', length=CLOCKLEN,
          cycle=True, cyclelimit=False, play=True,
          outfraction=True, outcycle=True, outcycleplusfraction=True)

# ---------------------------------------------------------------------------
# TEMPO + DROP — verbatim from monsoon.
# ---------------------------------------------------------------------------
TEMPO_BODY = '''# Beat detector, tempo estimator and drop detector.
import numpy as np
#
# A BEAT is a transient: positive flux (the RISE of a dedicated kick band) against an
# EMA of that flux. A DROP is SUSTAIN: the wide bass band sitting well above its own
# recent median for several frames running.

_state = {'prev': 0.0, 'fluxavg': 0.0, 'last_t': 0.0, 'last_beat': -99.0,
          'factor': 1.0, 'seen': False, 'period': 0.5, 'rate': 60.0,
          'beatstr': 0.0, 'fluxpeak': 1e-4,
          'flux_hist': [], 'acc': 0,
          'bhist': [], 'hot': 0, 'last_drop': -99.0}


def onCook(scriptOp):
    src = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    clk = scriptOp.inputs[1] if len(scriptOp.inputs) > 1 else None
    aud = scriptOp.inputs[2] if len(scriptOp.inputs) > 2 else None
    par = scriptOp.parent().par
    st = _state

    level = 0.0
    try:
        level = max(abs(v) for v in src.chan(0).vals)
    except Exception:
        pass
    try:
        now = float(clk['cycles_plus_fraction'][0]) * CLOCKLEN
    except Exception:
        now = st['last_t']

    dt = max(0.0, now - st['last_t'])
    st['last_t'] = now

    flux = max(0.0, level - st['prev'])
    st['prev'] = level
    a = min(1.0, dt / 0.6) if dt > 0 else 0.0
    st['fluxavg'] += (flux - st['fluxavg']) * a

    beat = 0.0
    beatstr = st['beatstr']
    if flux > max(st['fluxavg'] * 1.9, 0.004):
        if now - st['last_beat'] > REFRACTORY:
            st['last_beat'] = now
            st['seen'] = True
            beat = 1.0
            st['fluxpeak'] = max(flux, st['fluxpeak'] * FLUXPEAKDECAY, 1e-4)
            beatstr = min(1.0, flux / st['fluxpeak'])
            st['beatstr'] = beatstr

    # TEMPO: autocorrelation of the onset envelope, with a harmonic sum so the
    # fundamental wins over half-tempo.
    st['rate'] += (1.0 / max(dt, 1e-3) - st['rate']) * 0.02 if dt > 0 else 0.0
    st['flux_hist'].append(flux)
    del st['flux_hist'][:-TEMPOHIST]
    st['acc'] += 1
    if st['acc'] >= 15 and len(st['flux_hist']) >= TEMPOHIST * 0.6:
        st['acc'] = 0
        x = np.array(st['flux_hist'], dtype=np.float64)
        x -= x.mean()
        if float(x.std()) > 1e-7:
            ac = np.correlate(x, x, 'full')[len(x) - 1:]
            rate = max(20.0, min(200.0, st['rate']))
            lo = max(2, int(round(60.0 / 200.0 * rate)))
            hi = min(len(ac) - 1, int(round(60.0 / 55.0 * rate)))
            if hi > lo + 2:
                best, bestscore = -1, -1e18
                for lag in range(lo, hi + 1):
                    sc = float(ac[lag])
                    if lag * 2 < len(ac):
                        sc += 0.6 * float(ac[lag * 2])
                    if lag * 3 < len(ac):
                        sc += 0.3 * float(ac[lag * 3])
                    if sc > bestscore:
                        bestscore, best = sc, lag
                if best > 0:
                    st['period'] = best / rate
    period = st['period']
    bpm = min(200.0, max(50.0, 60.0 / max(period, 1e-3)))

    ref = max(1.0, float(par.Refbpm.eval()))
    for _ in range(3):
        if bpm > ref * 1.45:
            bpm *= 0.5
        elif bpm < ref * 0.72:
            bpm *= 2.0
        else:
            break

    quiet = st['seen'] and now - st['last_beat'] > SILENCE
    if not st['seen']:
        target = 1.0
    else:
        target = REF_FLOOR if quiet else bpm / max(1.0, float(par.Refbpm.eval()))
    target = min(REF_CEIL, max(REF_FLOOR, target))
    st['factor'] += (target - st['factor']) * min(1.0, dt * 0.6)

    drive = float(par.Beatdrive.eval())
    factor = 1.0 + (st['factor'] - 1.0) * drive

    bass = 0.0
    try:
        bass = float(aud['bass'][0])
    except Exception:
        pass
    st['bhist'].append(bass)
    del st['bhist'][:-DROPHIST]
    hist = sorted(st['bhist'])
    med = hist[len(hist) // 2] if hist else 0.0
    drop = 0.0
    if bass > max(med * DROPRATIO, DROPFLOOR):
        st['hot'] += 1
        if st['hot'] >= DROPFRAMES and now - st['last_drop'] > DROPHOLD:
            st['last_drop'] = now
            drop = 1.0
    else:
        st['hot'] = 0

    # NEVER clear() AND RE-APPEND CHANNELS EVERY FRAME. On 2025.33230 a Script
    # CHOP that does leaks native memory inside TouchDesigner — measured 2-5 MB a
    # minute on a 12k-sample publish, ~0.6 MB a minute even on a few 1-sample
    # channels. Build the channels once; after that only write values.
    # (numChans cannot be read from inside a cook, so whether they exist is
    # tracked here; if a write ever fails they are rebuilt and the write retried.)
    names = ('factor', 'bpm', 'beat', 'beatstr', 'drop', 'bassmed')
    vals = (factor, bpm if (st['seen'] and not quiet) else 0.0, beat, beatstr,
            drop, med)
    for attempt in (0, 1):
        try:
            if not st.get('built'):
                scriptOp.clear()
                for n in names:
                    scriptOp.appendChan(n)
                scriptOp.numSamples = 1
                st['built'] = True
            for i, v in enumerate(vals):
                scriptOp[i][0] = v
            break
        except Exception:
            st['built'] = False
    try:
        par.Bpm.val = bpm if (st['seen'] and not quiet) else 0.0
    except Exception:
        pass
    return
'''

tempo_src = C(textDAT, 'tempo_src', 1780, 1240)
tempo_src.text = hdr(
    CLOCKLEN=CLOCKLEN, REF_FLOOR=0.25, REF_CEIL=2.50, REFRACTORY=0.30, SILENCE=2.5,
    DROPHIST=240, DROPRATIO=1.55, DROPFLOOR=0.045, DROPFRAMES=3, DROPHOLD=6.0,
    TEMPOHIST=420, FLUXPEAKDECAY=0.9990,
) + TEMPO_BODY

tempo = C(scriptCHOP, 'tempo', 1940, 1240)
tempo.par.callbacks = tempo_src.name
af_kick = C(audiofilterCHOP, 'af_kick', 660, 1020, filter='lowpass')
soft(af_kick, cutofflog=math.log10(140.0), cutofffrequency=140.0)
W(gain, af_kick)
env_kick = C(envelopeCHOP, 'env_kick', 820, 1020, width=0.025)
W(af_kick, env_kick)
rs_kick = C(resampleCHOP, 'rs_kick', 980, 1020, method='rate', rate=120,
            timeslice=True)
W(env_kick, rs_kick)
W(rs_kick, tempo, 0)
W(timer, tempo, 1)
W(null_audio, tempo, 2)
# ---- END HOMESTEAD ----

# ---------------------------------------------------------------------------
# DIRECTOR — verbatim from homestead (its 'gust' verb is our shooting star)
# ---------------------------------------------------------------------------
# ---- BEGIN HOMESTEAD (verbatim) ----
DIRECTOR_BODY = '''# Musical time is monotonic and never seeks; the playhead is a subtraction from it
# (show = musical - Timeoffset), so a chapter jump is one parameter write.
#
# The playhead is CLAMPED at the end, not wrapped: the finished house stays on the
# bank until someone seeks back. And because `musical` is module state that resets
# on every reload while Timeoffset is a parameter that survives, the offset is
# re-derived from Showt on the first cook after a reload (see bayou) — otherwise the
# story freezes at the first frame for however long the stale offset is.
#
# Discrete events are MONOTONIC COUNTERS, never one-frame flags.
import math

_clock = {'last_raw': None, 'musical': 0.0, 'primed': False}
_st = {'peak': {'bass': PEAKFLOOR, 'high': PEAKFLOOR, 'energy': PEAKFLOOR},
       'kickenv': 0.0, 'dropenv': 0.0,
       'gust': 0, 'fish': 0, 'reseed': 0,
       'kicks': 0, 'accents': 0, 'drops': 0}


def _norm(st, key, v):
    pk = max(v, st['peak'][key] * PEAKDECAY, PEAKFLOOR)
    st['peak'][key] = pk
    return min(1.0, v / pk)


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
    mus = scriptOp.inputs[2] if len(scriptOp.inputs) > 2 else None
    comp = scriptOp.parent()
    par = comp.par
    st = _st

    raw = chan(tmr, 'cycles_plus_fraction', 0.0) * CLOCKLEN
    factor = chan(mus, 'factor', 1.0)
    if _clock['last_raw'] is None:
        _clock['last_raw'] = raw
    dt = max(0.0, raw - _clock['last_raw'])
    _clock['last_raw'] = raw
    _clock['musical'] += dt * factor
    musical = _clock['musical']

    bass = _norm(st, 'bass', chan(aud, 'bass', 0.0))
    high = _norm(st, 'high', chan(aud, 'high', 0.0))
    energy = _norm(st, 'energy', chan(aud, 'energy', 0.0))
    kick = chan(mus, 'beat', 0.0)
    beatstr = chan(mus, 'beatstr', 0.0)
    drop = chan(mus, 'drop', 0.0)

    if dt > 0.0:
        st['kickenv'] *= 0.5 ** (dt / 0.14)
        st['dropenv'] *= 0.5 ** (dt / 1.10)

    if kick > 0.5:
        st['kickenv'] = 1.0
        st['kicks'] += 1
        if beatstr >= ACCENT:
            st['accents'] += 1
    if drop > 0.5:
        st['dropenv'] = 1.0
        st['drops'] += 1

    if kick > 0.5 and float(par.Beatdrive.eval()) > 0.01:
        period = 60.0 / max(1.0, float(par.Refbpm.eval()))
        phase = _clock['musical'] % period
        err = phase if phase < period * 0.5 else phase - period
        _clock['musical'] -= err * BEATLOCK * float(par.Beatdrive.eval())
        musical = _clock['musical']

    slen = max(1.0, float(par.Storylen.eval()))
    off = float(par.Timeoffset.eval())
    if not _clock['primed']:
        _clock['primed'] = True
        try:
            was = min(slen, max(0.0, float(par.Showt.eval())))
        except Exception:
            was = 0.0
        off = musical - was
        par.Timeoffset = off
    elif musical - off < -0.5:
        try:
            was = min(slen, max(0.0, float(par.Showt.eval())))
        except Exception:
            was = 0.0
        off = musical - was
        par.Timeoffset = off
    # For an all-night run the story LOOPS: the finished homestead fades through
    # black into the empty riverbank again. With Loop off it clamps and holds.
    if par.Loop.eval():
        show = (musical - off) % slen
    else:
        show = min(slen, max(0.0, musical - off))

    pending = comp.fetch('pending', None)
    if pending:
        comp.store('pending', [])
        for what in pending:
            if what == 'gust':
                st['gust'] += 1
                st['dropenv'] = 1.0
            elif what == 'fish':
                st['fish'] += 1
            elif what == 'reseed':
                st['reseed'] += 1

    out = {
        'rawtime': raw, 'musical': musical, 'show': show, 'tempofactor': factor,
        'bass': bass, 'high': high, 'energy': energy,
        'kick': kick, 'kickenv': st['kickenv'], 'beatstr': beatstr,
        'drop': drop, 'dropenv': st['dropenv'],
        'kickcnt': float(st['kicks']), 'accentcnt': float(st['accents']),
        'dropcnt': float(st['drops']), 'gustcnt': float(st['gust']),
        'fishcnt': float(st['fish']), 'reseedcnt': float(st['reseed']),
        'storylen': slen,
    }

    # NEVER clear() AND RE-APPEND CHANNELS EVERY FRAME. On 2025.33230 a Script
    # CHOP that does leaks native memory inside TouchDesigner — measured 2-5 MB a
    # minute on a 12k-sample publish, ~0.6 MB a minute even on a few 1-sample
    # channels. Build the channels once; after that only write values.
    # (numChans cannot be read from inside a cook, so whether they exist is
    # tracked here; if a write ever fails they are rebuilt and the write retried.)
    keys = sorted(out.keys())
    for attempt in (0, 1):
        try:
            if not st.get('built'):
                scriptOp.clear()
                for k in keys:
                    scriptOp.appendChan(k)
                scriptOp.numSamples = 1
                st['built'] = True
            for i, k in enumerate(keys):
                scriptOp[i][0] = out[k]
            break
        except Exception:
            st['built'] = False

    try:
        par.Bassm.val = bass
        par.Highm.val = high
        par.Energym.val = energy
        par.Showt.val = show
    except Exception:
        pass
    return
'''

dir_src = C(textDAT, 'director_src', 1780, 1120)
dir_src.text = hdr(CLOCKLEN=CLOCKLEN, PEAKDECAY=0.9988, PEAKFLOOR=0.05,
                   BEATLOCK=0.22, ACCENT=0.32) + DIRECTOR_BODY

director = C(scriptCHOP, 'director', 1940, 1120)
director.par.callbacks = dir_src.name
W(timer, director, 0)
W(null_audio, director, 1)
W(tempo, director, 2)
# ---- END HOMESTEAD ----


def D(ch):
    return "(op('director')['%s'] or 0)" % ch


# ---------------------------------------------------------------------------
# THE ENGINE
# ---------------------------------------------------------------------------
ENGINE_BODY = r'''# Everything that lives or is built is emitted from here as ONE primitive: a
# rotated, filled quad instanced from a unit square with a per-instance width (see
# homestead / monsoon). Rows are (x0, y0, x1, y1, r, g, b, a, z, fl, w, wl).
#
# The first half of this module is homestead's engine, verbatim: its drawing
# primitives, and the generators for his house and the big tree on the bank. The
# second half is the voyage: the man seen from BEHIND, his raft in perspective, the
# space dust streaming past, and the schedule of the whole flight.
import math
import random
import numpy as np

# ---- BEGIN HOMESTEAD (verbatim) ----
_S = {'S': None}
CUR = {'wl': 99.0, 'fl': 0.0}
TAU = 6.283185307


def _ss(a, b, x):
    t = (x - a) / (b - a if b != a else 1e-9)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return t * t * (3.0 - 2.0 * t)


def _cl(x, lo=0.0, hi=1.0):
    return lo if x < lo else (hi if x > hi else x)


def _mix(c1, c2, k):
    k = 0.0 if k < 0.0 else (1.0 if k > 1.0 else k)
    return (c1[0] + (c2[0] - c1[0]) * k, c1[1] + (c2[1] - c1[1]) * k,
            c1[2] + (c2[2] - c1[2]) * k)


def _l2(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


def _mul(c, k):
    return (c[0] * k, c[1] * k, c[2] * k)


def _rh(i):
    x = math.sin(i * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


def _sane(v, dv=0.0, lo=-1.0e6, hi=1.0e6):
    """min/max PROPAGATE NaN; everything that leaves this engine goes through here."""
    try:
        v = float(v)
    except Exception:
        return dv
    if v != v or v in (float('inf'), float('-inf')):
        return dv
    return lo if v < lo else (hi if v > hi else v)


def _zd(gy):
    # depth from where a thing stands: lower on screen = nearer = drawn later
    return 0.20 + (0.0 - gy) * 0.60


def land_edge(y):
    return SHOREX + BANKK * (max(SHOREY - y, 0.0) / BANKH) ** 0.85


def shore_top(x):
    return SHOREY + 0.006 * math.sin(x * 11.0) + 0.004 * math.sin(x * 27.0 + 1.3)


def is_land(x, y):
    return y < shore_top(x) and x < land_edge(y)


def is_water(x, y):
    return y < FARY - 0.006 and not is_land(x, y)


# --- the one primitive ----------------------------------------------------------
def _seg(out, x0, y0, x1, y1, col, a, z=0.0, w=LWO):
    out.append((x0, y0, x1, y1, col[0], col[1], col[2], a, z, CUR['fl'], w,
                CUR['wl']))


def _rect(out, cx, cy, w, h, col, a, z=0.0):
    out.append((cx, cy - h * 0.5, cx, cy + h * 0.5, col[0], col[1], col[2], a, z,
                CUR['fl'], w, CUR['wl']))


def _fill(out, pts, col, a, z=0.0, slabs=0):
    """Fill a CONVEX polygon with horizontal slabs (6% overlap hides seams)."""
    ys = [p[1] for p in pts]
    lo, hi = min(ys), max(ys)
    hgt = hi - lo
    if hgt < 1e-5:
        return
    n = slabs if slabs else max(2, min(22, int(hgt / 0.0055) + 2))
    dh = hgt / n
    m = len(pts)
    for k in range(n):
        yc = lo + dh * (k + 0.5)
        xa, xb = 1e9, -1e9
        for i in range(m):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % m]
            if (ay <= yc < by) or (by <= yc < ay):
                xx = ax + (bx - ax) * (yc - ay) / (by - ay)
                if xx < xa:
                    xa = xx
                if xx > xb:
                    xb = xx
        if xb - xa < 1e-5:
            continue
        out.append((xa, yc, xb, yc, col[0], col[1], col[2], a, z, CUR['fl'],
                    dh * 1.06, CUR['wl']))


def _path(out, pts, col, a, z=0.0, w=LWO, close=False):
    n = len(pts)
    for i in (range(n) if close else range(n - 1)):
        p, q = pts[i], pts[(i + 1) % n]
        _seg(out, p[0], p[1], q[0], q[1], col, a, z, w)


def _cen(pts):
    n = float(len(pts))
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)


def _grow(pts, d):
    cx, cy = _cen(pts)
    res = []
    for (px, py) in pts:
        dx, dy = px - cx, py - cy
        ln = math.hypot(dx, dy) or 1e-9
        res.append((px + dx / ln * d, py + dy / ln * d))
    return res


def _shape(out, pts, col, a, z, lit=None, sun=0.0, lw=None, slabs=0):
    """A flat cel: an ink silhouette, the colour, and a lit crescent on the sun side."""
    lw = LWO if lw is None else lw
    if lw > 0:
        _fill(out, _grow(pts, lw), INK, a, z - 0.0008, slabs)
    _fill(out, pts, col, a, z, slabs)
    if lit is not None:
        cx, cy = _cen(pts)
        xs = [p[0] for p in pts]
        span = max(xs) - min(xs)
        ox = span * 0.16 * (1.0 if sun >= 0.0 else -1.0)
        inner = [(cx + (px - cx) * 0.74 + ox, cy + (py - cy) * 0.80 + span * 0.05)
                 for (px, py) in pts]
        _fill(out, inner, lit, a, z + 0.0004, slabs)


def _ell(cx, cy, rx, ry, n=12, rot=0.0):
    cr, sr = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(n):
        th = i * TAU / n
        x, y = rx * math.cos(th), ry * math.sin(th)
        pts.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return pts


def _limb(out, x0, y0, x1, y1, w, col, lit, a, z, sun, lw=None):
    lw = LWO if lw is None else lw
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    if ln < 1e-6:
        return
    ux, uy = dx / ln, dy / ln
    if lw > 0:
        _seg(out, x0 - ux * lw, y0 - uy * lw, x1 + ux * lw, y1 + uy * lw, INK, a,
             z - 0.0008, w + 2.0 * lw)
    _seg(out, x0, y0, x1, y1, col, a, z, w)
    if lit is not None:
        nx, ny = -uy, ux
        sgn = 1.0 if (nx * sun + ny * 0.7) > 0.0 else -1.0
        o = w * 0.24 * sgn
        _seg(out, x0 + nx * o, y0 + ny * o, x1 + nx * o, y1 + ny * o, lit, a,
             z + 0.0004, w * 0.40)


def _joint(out, x, y, r, col, a, z):
    _fill(out, _ell(x, y, r, r, 8), col, a, z, 2)


def _knee(hx, hy, fx, fy, l1, l2, sgn):
    dx, dy = fx - hx, fy - hy
    raw = max(math.hypot(dx, dy), 1e-6)
    ux, uy = dx / raw, dy / raw
    d = min(max(raw, 0.010), l1 + l2 - 0.002)
    fx, fy = hx + ux * d, hy + uy * d
    aa = (l1 * l1 - l2 * l2 + d * d) / (2.0 * d)
    hh = math.sqrt(max(0.0, l1 * l1 - aa * aa))
    return (hx + ux * aa - uy * hh * sgn, hy + uy * aa + ux * hh * sgn, fx, fy)
# ---- END HOMESTEAD ----
# ---- BEGIN HOMESTEAD (verbatim) ----
# --- the house ------------------------------------------------------------------
# Generated once, as rows tagged (stage, threshold). A part exists when its stage's
# progress passes its threshold, and it drops the last few centimetres into place.
def _gen_house():
    rows, stg, thr = [], [], []

    def tag(st, u, fn, *args, **kw):
        tmp = []
        fn(tmp, *args, **kw)
        for r in tmp:
            rows.append(r)
            stg.append(st)
            thr.append(u)

    zb = _zd(GYH)
    sun = -1.0

    # -- stage 1: stilts, bracing, the floor, the ladder --------------------------
    stx = [HX0 + 0.020, -0.530, -0.425, -0.320, HX1 - 0.015]
    for i, sx in enumerate(stx):
        u = 0.04 + 0.13 * i
        tag(1, u, _limb, sx, GYH - 0.010, sx, FLOORY + 0.012, 0.017, BAMB, BAMBLT,
            1.0, zb - 0.020, sun)
        for ny in (GYH + 0.022, GYH + 0.050):
            tag(1, u, _seg, sx - 0.010, ny, sx + 0.010, ny, BAMBDK, 1.0, zb - 0.019,
                0.004)
    for i in range(4):
        u = 0.70 + 0.03 * i
        a, b = stx[i], stx[i + 1]
        tag(1, u, _limb, a, GYH + 0.004, b, FLOORY - 0.006, 0.007, BAMBDK, None, 1.0,
            zb - 0.022, sun, LWO * 0.6)
    tag(1, 0.84, _limb, HX0 - 0.025, FLOORY, HX1 + 0.025, FLOORY, 0.020, BAMB,
        BAMBLT, 1.0, zb - 0.017, sun)
    for k in range(22):
        xx = HX0 - 0.015 + k * (HX1 - HX0 + 0.03) / 21.0
        tag(1, 0.88, _seg, xx, FLOORY - 0.009, xx, FLOORY + 0.009, BAMBDK, 1.0,
            zb - 0.016, 0.0025)
    lx0, lx1 = HX1 + 0.075, HX1 + 0.030
    for off in (0.0, 0.034):
        tag(1, 0.93, _limb, lx0 + off, MANGY + 0.012, lx1 + off, FLOORY + 0.004,
            0.009, BAMB, None, 1.0, _zd(MANGY + 0.02) - 0.03, sun, LWO * 0.7)
    for k in range(4):
        q = (k + 0.6) / 4.6
        yy = MANGY + 0.012 + (FLOORY - MANGY) * q
        xx = lx0 + (lx1 - lx0) * q
        tag(1, 0.96, _seg, xx - 0.004, yy, xx + 0.038, yy, BAMBDK, 1.0,
            _zd(MANGY + 0.02) - 0.029, 0.007)

    # -- stage 2: walls — slats left to right, then mud, then the window and door --
    zw = zb - 0.010
    DOOR = (-0.335, -0.262)
    WIN = (-0.535, -0.445, -0.108, -0.038)
    tag(2, 0.0, _fill, [(DOOR[0], FLOORY + 0.01), (DOOR[1], FLOORY + 0.01),
                        (DOOR[1], -0.030), (DOOR[0], -0.030)], DARKIN, 1.0, zw - 0.002)
    tag(2, 0.30, _fill, [(WIN[0], WIN[2]), (WIN[1], WIN[2]), (WIN[1], WIN[3]),
                         (WIN[0], WIN[3])], DARKIN, 1.0, zw - 0.002)
    ns = 22
    for k in range(ns):
        x0 = HX0 + 0.012 + k * (HX1 - HX0 - 0.024) / ns
        xc = x0 + (HX1 - HX0 - 0.024) / ns * 0.5
        u = 0.02 + 0.58 * k / (ns - 1.0)
        spans = [(FLOORY + 0.010, WALLTOP)]
        if DOOR[0] - 0.004 < xc < DOOR[1] + 0.004:
            spans = [(-0.030, WALLTOP)]
        elif WIN[0] - 0.004 < xc < WIN[1] + 0.004:
            spans = [(FLOORY + 0.010, WIN[2]), (WIN[3], WALLTOP)]
        tone = _mix(BAMB, BAMBDK, 0.25 * _rh(k * 3.1))
        for (ya, yb) in spans:
            tag(2, u, _limb, xc, ya, xc, yb, 0.0175, tone, BAMBLT, 1.0, zw, sun,
                LWO * 0.55)
    # mud plaster over the lower half, laid on in lumps
    for k in range(9):
        xa = HX0 + 0.010 + k * 0.047
        xb = min(HX1 - 0.010, xa + 0.052)
        if xa > DOOR[0] - 0.02 and xa < DOOR[1]:
            continue
        top = -0.118 + 0.020 * _rh(k * 7.7)
        if WIN[0] - 0.04 < xa < WIN[1]:
            top = min(top, WIN[2] - 0.004)
        u = 0.64 + 0.26 * k / 8.0
        tag(2, u, _shape, [(xa, FLOORY + 0.012), (xb, FLOORY + 0.012),
                           (xb - 0.004, top + 0.010 * _rh(k)),
                           (xa + 0.006, top)], MUD, 1.0, zw + 0.002, MUDLT, sun,
            LWO * 0.55)
    tag(2, 0.62, _limb, HX0 - 0.005, WALLTOP, HX1 + 0.005, WALLTOP, 0.014, BAMB,
        BAMBLT, 1.0, zw + 0.003, sun)
    for (xa, ya, xb, yb) in ((WIN[0], WIN[2], WIN[1], WIN[2]),
                             (WIN[0], WIN[3], WIN[1], WIN[3]),
                             (WIN[0], WIN[2], WIN[0], WIN[3]),
                             (WIN[1], WIN[2], WIN[1], WIN[3]),
                             ((WIN[0] + WIN[1]) * 0.5, WIN[2],
                              (WIN[0] + WIN[1]) * 0.5, WIN[3])):
        tag(2, 0.93, _limb, xa, ya, xb, yb, 0.008, BAMB, None, 1.0, zw + 0.004, sun,
            LWO * 0.6)
    # a curtain across the door, patched like his shirt
    tag(2, 0.97, _shape, [(DOOR[0] + 0.002, -0.032), (DOOR[0] + 0.040, -0.032),
                          (DOOR[0] + 0.030, FLOORY + 0.012),
                          (DOOR[0] + 0.002, FLOORY + 0.012)], PATCH, 1.0, zw + 0.004,
        _mix(PATCH, DHOTILT, 0.3), sun, LWO * 0.6)

    # -- stage 3: rafters, five courses of thatch from the eave up, ridge, chimney --
    zr = zb - 0.004
    RE, RR = WALLTOP - 0.006, 0.138
    EL, ER = HX0 - 0.070, HX1 + 0.070
    RL, RRr = -0.575, -0.270

    def rx(y, left):
        q = (y - RE) / (RR - RE)
        return (EL + (RL - EL) * q) if left else (ER + (RRr - ER) * q)

    for k in range(7):
        q = k / 6.0
        xe = EL + (ER - EL) * q
        xr = RL + (RRr - RL) * q
        tag(3, 0.02 + 0.025 * k, _limb, xe, RE, xr, RR, 0.009, BAMBDK, None, 1.0,
            zr - 0.003, sun, LWO * 0.6)
    ncourse = 5
    for L in range(ncourse):
        y0 = RE + (RR - RE) * L / ncourse - (0.010 if L == 0 else 0.0)
        y1 = RE + (RR - RE) * (L + 1) / ncourse + 0.006
        u = 0.22 + 0.14 * L
        tone = THATCH if L % 2 == 0 else _mix(THATCH, THATCHDK, 0.25)
        tag(3, u, _shape, [(rx(y0, True) - 0.006, y0), (rx(y0, False) + 0.006, y0),
                           (rx(y1, False), y1), (rx(y1, True), y1)], tone, 1.0,
            zr + 0.001 * L, THATCHLT, -1.0, LWO * 0.8)
        # the straw fringe along the bottom of each course
        xa, xb = rx(y0, True), rx(y0, False)
        nf = int((xb - xa) / 0.0105)
        for j in range(nf):
            xx = xa + (j + 0.5) * (xb - xa) / nf
            ln = 0.014 + 0.012 * _rh(j * 1.7 + L * 9.1)
            col = THATCHDK if j % 3 == 0 else (THATCHLT if j % 3 == 1 else THATCH)
            tag(3, u + 0.02, _seg, xx, y0 + 0.004, xx - 0.004, y0 - ln, col, 1.0,
                zr + 0.001 * L + 0.0005, 0.0034)
    tag(3, 0.94, _limb, RL - 0.012, RR, RRr + 0.012, RR, 0.020, THATCHDK, THATCH,
        1.0, zr + 0.008, sun)
    tag(3, 0.97, _shape, [(-0.340, 0.080), (-0.312, 0.080), (-0.314, 0.182),
                          (-0.338, 0.182)], CLAY, 1.0, zr + 0.009, CLAYLT, -1.0,
        LWO * 0.8)
    tag(3, 0.975, _limb, -0.346, 0.184, -0.306, 0.184, 0.010, CLAYLT, None, 1.0,
        zr + 0.0095, sun, LWO * 0.6)
    # the gutter off the left eave, and a barrel to catch it
    tag(3, 0.985, _limb, EL - 0.004, RE - 0.012, HX0 + 0.05, RE - 0.012, 0.009,
        BAMB, None, 1.0, zr + 0.009, sun, LWO * 0.6)
    tag(3, 0.99, _limb, EL + 0.004, RE - 0.012, EL + 0.004, GYH + 0.080, 0.008,
        BAMB, None, 1.0, _zd(GYH - 0.02) + 0.002, sun, LWO * 0.6)
    bx = EL + 0.006
    tag(3, 0.995, _shape, [(bx - 0.034, GYH - 0.022), (bx + 0.034, GYH - 0.022),
                           (bx + 0.038, GYH + 0.072), (bx - 0.038, GYH + 0.072)],
        WOOD, 1.0, _zd(GYH - 0.02) + 0.003, WOODLT, -1.0)
    for yy in (GYH + 0.002, GYH + 0.046):
        tag(3, 0.996, _seg, bx - 0.037, yy, bx + 0.037, yy, IRON, 1.0,
            _zd(GYH - 0.02) + 0.004, 0.006)
    # the bulb socket under the right eave
    tag(3, 1.0, _seg, BULB[0], RE - 0.010, BULB[0], BULB[1] + 0.012, INK, 1.0,
        zr + 0.010, 0.004)

    # -- stage 4 (static): the wheel's bank frame, generator, pole and wire -------
    zwh = _zd(WWL) + 0.010
    PX = WX - 0.090
    tag(4, 0.02, _limb, PX - 0.030, WWL + 0.004, PX, WY + 0.012, 0.014, WOOD, WOODLT,
        1.0, zwh - 0.010, sun)
    tag(4, 0.08, _limb, PX + 0.026, WWL + 0.004, PX, WY + 0.012, 0.014, WOOD, WOODLT,
        1.0, zwh - 0.011, sun)
    tag(4, 0.14, _limb, PX - 0.020, WWL + 0.030, PX + 0.018, WWL + 0.030, 0.008,
        WOOD, None, 1.0, zwh - 0.0095, sun, LWO * 0.6)
    tag(4, 0.20, _limb, PX - 0.004, WY, WX + 0.004, WY, 0.012, IRON, IRONLT, 1.0,
        zwh - 0.008, sun)
    GX, GY = 0.345, -0.300
    tag(4, 0.82, _shape, [(GX - 0.030, GY), (GX + 0.030, GY), (GX + 0.030, GY + 0.040),
                          (GX - 0.030, GY + 0.040)], IRON, 1.0, _zd(GY) - 0.004,
        IRONLT, -1.0)
    tag(4, 0.83, _shape, _ell(GX + 0.030, GY + 0.020, 0.012, 0.012, 8), IRONLT, 1.0,
        _zd(GY) - 0.003, None, -1.0, LWO * 0.7)
    tag(4, 0.86, _seg, GX + 0.030, GY + 0.032, PX, WY + 0.010, INK, 1.0,
        _zd(GY) - 0.0035, 0.0030)
    tag(4, 0.86, _seg, GX + 0.030, GY + 0.008, PX, WY - 0.010, INK, 1.0,
        _zd(GY) - 0.0035, 0.0030)
    PLX, PLY0, PLY1 = 0.070, -0.305, 0.050
    tag(4, 0.89, _limb, PLX, PLY0, PLX, PLY1, 0.012, BAMB, BAMBLT, 1.0,
        _zd(PLY0) - 0.02, sun, LWO * 0.8)
    tag(4, 0.91, _limb, PLX - 0.026, PLY1 - 0.010, PLX + 0.026, PLY1 - 0.010, 0.007,
        BAMBDK, None, 1.0, _zd(PLY0) - 0.019, sun, LWO * 0.6)

    def sag(ax, ay, bx_, by_, dip, n=10):
        return [(ax + (bx_ - ax) * i / n,
                 ay + (by_ - ay) * i / n - dip * 4.0 * (i / n) * (1.0 - i / n))
                for i in range(n + 1)]

    wz = _zd(PLY0) - 0.018
    tag(4, 0.95, _path, sag(GX - 0.028, GY + 0.036, PLX + 0.024, PLY1 - 0.010, 0.030),
        INK, 1.0, wz, 0.0028)
    tag(4, 0.98, _path, sag(PLX - 0.024, PLY1 - 0.010, BULB[0] + 0.004, RE - 0.012,
                            0.022), INK, 1.0, wz, 0.0028)

    # -- stage 5 (static): the fence and the rows --------------------------------
    FX0, FX1, FY0, FY1 = GARDEN
    posts = [(FX0 + (FX1 - FX0) * i / 6.0, FY1) for i in range(7)] + \
            [(FX0 + (FX1 - FX0) * i / 6.0, FY0) for i in range(7)]
    for i, (px, py) in enumerate(posts):
        tag(5, 0.02 + 0.010 * i, _limb, px, py - 0.004, px + 0.002 * (i % 2),
            py + 0.042, 0.007, WOOD, None, 1.0, _zd(py) - 0.001, sun, LWO * 0.6)
    for (yy, u) in ((FY1 + 0.020, 0.17), (FY1 + 0.034, 0.18),
                    (FY0 + 0.020, 0.19), (FY0 + 0.034, 0.20)):
        tag(5, u, _limb, FX0, yy, FX1, yy + 0.003, 0.005, WOOD, None, 1.0,
            _zd(yy - 0.02) - 0.0005, sun, LWO * 0.5)
    for r, ry in enumerate(ROWS):
        tag(5, 0.22 + 0.05 * r, _shape, [(FX0 + 0.012, ry - 0.008),
                                         (FX1 - 0.012, ry - 0.008),
                                         (FX1 - 0.022, ry + 0.010),
                                         (FX0 + 0.022, ry + 0.010)],
            (0.300, 0.210, 0.140), 1.0, _zd(ry) - 0.004, (0.400, 0.290, 0.200),
            -1.0, LWO * 0.5)

    A = np.array(rows, dtype=np.float64)
    return dict(A=A, st=np.array(stg, dtype=np.int64), u=np.array(thr),
                n=len(rows))
# ---- END HOMESTEAD ----
# ---- BEGIN HOMESTEAD (verbatim) ----
def _slabs(ry):
    return max(6, min(90, int(2.0 * ry / 0.0032)))


def _gen_tree(rs, canopy):
    """The big tree and the framing leaves, built ONCE at fine slab resolution.

    Round shapes filled with slabs stair-step unless the slabs are ~2 px tall, and
    at that density doing it in Python every frame cost more than everything else
    in the engine together. Built once, they are numpy rows; per frame each clump
    only gets a sideways sway offset, vectorised.
    """
    rows, grp, wgt = [], [], []

    def add(tmp, g, wt):
        rows.extend(tmp)
        grp.extend([g] * len(tmp))
        wgt.extend([wt] * len(tmp))

    tz = _zd(-0.300) - 0.030
    tsun = 1.0
    tmp = []
    _shape(tmp, [(TREEX - 0.060, -0.310), (TREEX + 0.060, -0.310),
                 (TREEX + 0.030, 0.100), (TREEX + 0.045, 0.300),
                 (TREEX - 0.010, 0.300), (TREEX - 0.030, 0.100)], TRUNK, 1.0, tz,
           TRUNKLT, tsun, slabs=90)
    # bark: a few darker vertical strokes
    for k in range(9):
        bx = TREEX - 0.040 + 0.010 * k + rs.uniform(-0.004, 0.004)
        by = rs.uniform(-0.28, 0.05)
        _seg(tmp, bx, by, bx + rs.uniform(-0.004, 0.004), by + rs.uniform(0.04, 0.10),
             _mul(TRUNK, 0.72), 1.0, tz + 0.0006, 0.004)
    for (bx0, by0, bx1, by1, bw) in ((TREEX + 0.01, 0.05, TREEX + 0.20, 0.25, 0.030),
                                     (TREEX, 0.12, TREEX - 0.14, 0.34, 0.026),
                                     (TREEX + 0.02, 0.22, TREEX + 0.10, 0.44, 0.022),
                                     (TREEX + 0.05, 0.20, TREEX + 0.16, 0.235,
                                      0.014)):
        _limb(tmp, bx0, by0, bx1, by1, bw, TRUNK, TRUNKLT, 1.0, tz + 0.001, tsun)
    add(tmp, 0, 0.0)
    for i, (cx, cy, r, v) in enumerate(canopy):
        tmp = []
        ry = r * 0.78
        tone = _mix(LEAFDK, LEAF, 0.25 + 0.5 * v)
        zc = tz + 0.004 + 0.0004 * i
        _shape(tmp, _ell(cx, cy, r, ry, 28, v), tone, 1.0, zc,
               _mix(LEAF, LEAFLT, 0.5 * v), tsun, slabs=_slabs(ry))
        # leaf texture: little dark and light tufts inside the clump
        for k in range(10):
            a = rs.uniform(0.0, TAU)
            rr = r * rs.uniform(0.15, 0.75)
            lx, ly = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.7
            c2 = _mul(tone, 0.72) if (lx < cx) else _mix(LEAF, LEAFLT, 0.6)
            _fill(tmp, _ell(lx, ly, r * 0.16, r * 0.10, 10, rs.uniform(0, 3)), c2,
                  1.0, zc + 0.0006, 6)
        add(tmp, i + 1, 1.0 + cy * 2.0)
    base = len(canopy) + 1
    for i, (lx, ly, ll, rot) in enumerate(((-1.00, -0.54, 0.16, 0.8),
                                           (-0.92, -0.57, 0.13, 1.25),
                                           (-1.04, -0.46, 0.12, 0.45),
                                           (0.74, -0.53, 0.14, 2.3),
                                           (0.79, -0.46, 0.11, 2.7))):
        tmp = []
        cx, cy = lx + math.cos(rot) * ll * 0.5, ly + math.sin(rot) * ll * 0.5
        pts = _ell(cx, cy, ll * 0.55, ll * 0.17, 24, rot)
        _shape(tmp, pts, _mul(LEAFDK, 0.75), 1.0, 0.97 + 0.001 * i,
               _mul(LEAF, 0.7), 1.0 if lx < 0 else -1.0, slabs=40)
        _seg(tmp, cx - math.cos(rot) * ll * 0.5, cy - math.sin(rot) * ll * 0.5,
             cx + math.cos(rot) * ll * 0.45, cy + math.sin(rot) * ll * 0.45,
             _mul(LEAF, 0.55), 1.0, 0.97 + 0.001 * i + 0.0006, 0.004)
        add(tmp, base + i, -1.0)
    return dict(A=np.array(rows, dtype=np.float64), g=np.array(grp),
                w=np.array(wgt), ph=np.array([rs.uniform(0, TAU)
                                              for _ in range(base + 5)]))
# ---- END HOMESTEAD ----


# ===================================================================================
# THE VOYAGE
# ===================================================================================
def _lerp(a, b, k):
    return a + (b - a) * k


def _tab(f, F, V):
    return float(np.interp(f, F, V))


def _persp(f, obj):
    """Screen centre and radius of an object ahead, from its depth table."""
    z = max(1e-3, _tab(f, obj['F'], obj['Z']))
    ox, oy = obj['O']
    return VPX + ox / z, VPY + oy / z, obj['R'] / z


# --- the man, from behind ---------------------------------------------------------
# The same man as homestead — thin, barefoot, a patched shirt with a torn hem, a
# dhoti gone grey with washing, the faded red cloth round his head — turned round.
# From behind the head-cloth is the whole portrait: its knot sits at the back of his
# skull and its two tails stream in the wind of the flight. Units are his height.
# `pz` is a dict of eased pose parameters, so a change of pose is a movement, not a
# cut: hip height, and (upper, fore) arm angles for each side, measured from hanging
# straight down, positive = out to that side.
POSES = {
    #          hip    L-arm           R-arm          foreshorten R
    'stand':  (0.50, (0.14, 0.06),  (0.14, 0.06),  1.00),
    'steer':  (0.50, (0.14, 0.06),  (1.25, 0.35),  1.00),
    'waveL':  (0.50, (2.55, 0.55),  (0.14, 0.06),  1.00),
    'wave':   (0.50, (0.14, 0.06),  (2.55, 0.55),  1.00),
    'look':   (0.50, (0.20, 0.10),  (2.25, 2.05),  1.00),
    'point':  (0.50, (0.16, 0.08),  (2.05, 0.10),  1.00),
    'pointL': (0.50, (2.05, 0.10),  (0.16, 0.08),  1.00),
    'sit':    (0.14, (0.28, -0.20), (0.28, -0.20), 1.00),
    'cup':    (0.14, (0.28, -0.20), (0.45, 2.30),  1.00),
    'brace':  (0.40, (1.35, -0.45), (1.35, -0.45), 1.00),
}


def _man_back(out, x, gy, sc, pz, t, sun, nod, wind, sip, z0, tool):
    def P(u, v):
        return (x + u * sc, gy + v * sc)

    hip = pz['hip']
    sitting = hip < 0.30
    zl = z0
    # --- legs and dhoti ------------------------------------------------------
    if not sitting:
        crouch = _cl((0.50 - hip) / 0.12)
        for sgn in (-1.0, 1.0):
            fx = sgn * (0.080 + 0.05 * crouch)
            k = P(fx * 0.9, 0.25 * (hip / 0.5))
            f0 = P(fx, 0.035)
            _limb(out, k[0], k[1], f0[0], f0[1], 0.062 * sc, SKIN, SKINLT, 1.0, zl,
                  sun)
            # a heel and the sole of a bare foot
            _shape(out, _ell(f0[0], f0[1] - 0.012 * sc, 0.040 * sc, 0.026 * sc, 10),
                   SKIN, 1.0, zl + 0.0003, None, sun, LWO * 0.8)
        top, bot = hip + 0.02, 0.24 * (hip / 0.5)
        dh = [P(-0.125, top), P(0.125, top), P(0.170, bot + 0.02),
              P(0.030, bot), P(-0.030, bot), P(-0.170, bot + 0.02)]
        _shape(out, dh, DHOTI, 1.0, zl + 0.001, DHOTILT, sun)
        a, b = P(0.0, bot + 0.01), P(0.004, bot + 0.13)
        _seg(out, a[0], a[1], b[0], b[1], _mul(DHOTI, 0.62), 1.0, zl + 0.0016,
             0.012 * sc)
    else:
        # sitting cross-legged on the deck: from behind, a broad fold of dhoti,
        # and one foot peeking out at each side
        dc = P(0, 0.065)
        _shape(out, _ell(dc[0], dc[1], 0.205 * sc, 0.062 * sc, 18),
               _mul(DHOTI, 0.86), 1.0, zl + 0.001, DHOTI, sun)
        for sgn in (-1.0, 1.0):             # the folds over each knee
            a, b = P(sgn * 0.05, 0.10), P(sgn * 0.16, 0.05)
            _seg(out, a[0], a[1], b[0], b[1], _mul(DHOTI, 0.55), 1.0, zl + 0.0016,
                 0.010 * sc)
        for sgn in (-1.0, 1.0):
            fp = P(sgn * 0.255, 0.035)
            _shape(out, _ell(fp[0], fp[1], 0.040 * sc, 0.024 * sc, 10), SKIN, 1.0,
                   zl + 0.0005, None, sun, LWO * 0.8)

    # --- torso: the back of the patched shirt ---------------------------------
    w0, w1 = hip + 0.02, hip + 0.33
    tor = [P(-0.120, w0), P(0.120, w0), P(0.172, w1 - 0.035), P(0.130, w1),
           P(-0.130, w1), P(-0.172, w1 - 0.035)]
    zt = zl + 0.004
    _shape(out, tor, SHIRT, 1.0, zt, SHIRTLT, sun)
    for k, du in enumerate((-0.085, -0.03, 0.03, 0.085)):
        _fill(out, [P(du - 0.030, w0 + 0.004), P(du + 0.030, w0 + 0.004),
                    P(du + 0.004 * (k - 1.5), w0 - 0.050 - 0.012 * (k % 2))],
              SHIRT, 1.0, zt + 0.0002, 2)
    _shape(out, [P(-0.095, w0 + 0.10), P(-0.020, w0 + 0.095), P(-0.018, w0 + 0.175),
                 P(-0.092, w0 + 0.180)], PATCH, 1.0, zt + 0.0006, None, sun,
           LWO * 0.6)
    _shape(out, [P(0.040, w0 + 0.035), P(0.100, w0 + 0.040), P(0.096, w0 + 0.090),
                 P(0.042, w0 + 0.088)], PATCH2, 1.0, zt + 0.0006, None, sun,
           LWO * 0.6)
    for k in range(4):                      # a line of stitches up the patch
        a = P(-0.100 + 0.003 * k, w0 + 0.11 + 0.018 * k)
        _seg(out, a[0], a[1], a[0] + 0.008 * sc, a[1], INK, 1.0, zt + 0.0008,
             0.004 * sc)
    sp0, sp1 = P(0.004, w0 + 0.04), P(0.0, w1 - 0.03)
    _seg(out, sp0[0], sp0[1], sp1[0], sp1[1], _mul(SHIRT, 0.78), 1.0, zt + 0.0004,
         0.008 * sc)

    # --- arms ------------------------------------------------------------------
    hands = {}
    for side, key in ((-1.0, 'L'), (1.0, 'R')):
        a1, a2 = pz[key]
        fs = pz['fs'] if side > 0 else 1.0
        S0 = (side * 0.150, w1 - 0.030)
        d1 = (side * math.sin(a1), -math.cos(a1))
        el = (S0[0] + d1[0] * 0.170 * fs, S0[1] + d1[1] * 0.170 * fs)
        d2 = (side * math.sin(a1 + a2), -math.cos(a1 + a2))
        hd = (el[0] + d2[0] * 0.160 * fs, el[1] + d2[1] * 0.160 * fs)
        A0, A1, A2 = P(*S0), P(*el), P(*hd)
        za = zt + 0.002
        mid = ((A0[0] + A1[0]) * 0.5, (A0[1] + A1[1]) * 0.5)
        _limb(out, A1[0], A1[1], A2[0], A2[1], 0.052 * sc, SKIN, SKINLT, 1.0, za, sun)
        _joint(out, A2[0], A2[1], 0.034 * sc, SKIN, 1.0, za + 0.0002)
        _limb(out, mid[0], mid[1], A1[0], A1[1], 0.056 * sc, SKIN, None, 1.0, za, sun)
        _joint(out, A1[0], A1[1], 0.026 * sc, SKIN, 1.0, za + 0.0001)
        _limb(out, A0[0], A0[1], mid[0], mid[1], 0.078 * sc, SHIRT, SHIRTLT, 1.0,
              za + 0.0003, sun)
        hands[key] = (A2, za)

    # --- head, from behind ---------------------------------------------------------
    hc = (0.004 + 0.010 * math.sin(t * 0.4), w1 + 0.105 - nod)
    n0, n1 = P(0.0, w1 - 0.01), P(*hc)
    zh = zt + 0.003
    _limb(out, n0[0], n0[1], n1[0], n1[1], 0.070 * sc, SKIN, None, 1.0, zh - 0.0015,
          sun)
    HC = P(*hc)
    R = 0.098
    for sgn in (-1.0, 1.0):                 # ears
        e = P(hc[0] + sgn * R * 0.98, hc[1] - 0.010)
        _shape(out, _ell(e[0], e[1], 0.020 * sc, 0.030 * sc, 10), SKIN, 1.0,
               zh - 0.0005, None, sun, LWO * 0.7)
    _shape(out, _ell(HC[0], HC[1], R * sc, R * 1.06 * sc, 16), SKIN, 1.0, zh,
           SKINLT, sun)
    # his hair at the nape, under the cloth
    _shape(out, [P(hc[0] - R * 0.92, hc[1] + 0.010), P(hc[0] + R * 0.92, hc[1] + 0.010),
                 P(hc[0] + R * 0.70, hc[1] - R * 0.70), P(hc[0], hc[1] - R * 0.98),
                 P(hc[0] - R * 0.70, hc[1] - R * 0.70)], BEARD, 1.0, zh + 0.0005,
           None, sun, LWO * 0.5)
    # the head-cloth: a cap over the crown, a band round it, the knot at the back
    _shape(out, [P(hc[0] + R * 1.03, hc[1] - 0.006)] +
           [P(hc[0] + R * 1.03 * math.cos(a), hc[1] + R * 1.09 * math.sin(a))
            for a in [i * math.pi / 12.0 for i in range(13)]] +
           [P(hc[0] - R * 1.03, hc[1] - 0.006)], CLOTHR, 1.0, zh + 0.0010,
           CLOTHRLT, sun)
    b0, b1 = P(hc[0] - R * 1.04, hc[1] + 0.004), P(hc[0] + R * 1.04, hc[1] + 0.004)
    _limb(out, b0[0], b0[1], b1[0], b1[1], 0.030 * sc, _mul(CLOTHR, 0.82), None, 1.0,
          zh + 0.0012, sun, LWO * 0.7)
    # the knot sits low at the back of the skull, at the nape, so the tails fall
    # from it onto his back instead of across his head
    kn = P(hc[0] + 0.012, hc[1] - 0.052)
    # the two tails stream in the wind of the flight and flutter on the bass
    for i, sgn in enumerate((-1.0, 1.0)):
        ph = t * (5.0 + 1.5 * i) + i * 1.7
        wob = math.sin(ph) * (0.018 + 0.030 * wind)
        # in still air they hang down his back; in the wind of the flight they
        # stream out to the side and flutter
        m = P(hc[0] + sgn * 0.022 + wob * 0.5, hc[1] - 0.125 + 0.015 * wind)
        e = P(hc[0] + sgn * (0.040 + 0.030 * wind) + wob * 1.6,
              hc[1] - 0.215 + 0.045 * wind)
        _limb(out, kn[0], kn[1], m[0], m[1], 0.034 * sc, CLOTHR, CLOTHRLT, 1.0,
              zh + 0.0013 + 0.0001 * i, sun, LWO * 0.7)
        _limb(out, m[0], m[1], e[0], e[1], 0.028 * sc, CLOTHR, None, 1.0,
              zh + 0.0014 + 0.0001 * i, sun, LWO * 0.7)
    _shape(out, _ell(kn[0], kn[1], 0.030 * sc, 0.026 * sc, 10), _mul(CLOTHR, 0.85),
           1.0, zh + 0.0016, CLOTHRLT, sun, LWO * 0.7)

    # --- what he holds -------------------------------------------------------------
    if tool == 'cup' and 'R' in hands:
        (hx, hy), za = hands['R']
        _shape(out, [(hx - 0.020 * sc, hy - 0.004), (hx + 0.020 * sc, hy - 0.004),
                     (hx + 0.022 * sc, hy + 0.045 * sc), (hx - 0.022 * sc, hy + 0.045 * sc)],
               CLAY, 1.0, za + 0.004, CLAYLT, sun, LWO * 0.7)
    return hands


# --- the raft, in perspective ------------------------------------------------------
# Seen from behind: seven bamboo poles running away from us toward the vanishing
# point, lashed across, the cut ends of the poles along the near edge, a short mast
# at the far right corner with a patched pennant, and the lantern — the bulb from
# his house, in a little cage — hanging off it.
def _raft(out, cx, cy, t, sun, lamp, wind, z0):
    NW, FW, D = 0.380, 0.215, 0.150        # near half-width, far half-width, depth
    yf = cy + D
    fx0 = cx + (VPX - cx) * 0.35           # the far edge is drawn toward the VP
    poles = 7
    for i in range(poles):
        u0 = -1.0 + 2.0 * i / poles
        u1 = -1.0 + 2.0 * (i + 1) / poles
        pts = [(cx + u0 * NW + 0.004, cy), (cx + u1 * NW - 0.004, cy),
               (fx0 + u1 * FW - 0.002, yf), (fx0 + u0 * FW + 0.002, yf)]
        tone = _mix(BAMB, BAMBDK, 0.20 * _rh(i * 3.3))
        _shape(out, pts, tone, 1.0, z0, None, sun, LWO * 0.7)
        um = (u0 + u1) * 0.5
        a, b = (cx + um * NW + 0.012, cy + 0.004), (fx0 + um * FW + 0.006, yf - 0.004)
        _seg(out, a[0], a[1], b[0], b[1], BAMBLT, 1.0, z0 + 0.0004, 0.010)
        # node rings across each pole
        for q in (0.35, 0.72):
            ya = cy + D * q
            xa = _lerp(cx + u0 * NW, fx0 + u0 * FW, q)
            xb = _lerp(cx + u1 * NW, fx0 + u1 * FW, q)
            _seg(out, xa + 0.004, ya, xb - 0.004, ya, BAMBDK, 1.0, z0 + 0.0005, 0.005)
        # the cut end of the pole, facing us
        ex = cx + um * NW
        _shape(out, _ell(ex, cy - 0.016, NW / poles * 0.92, 0.024, 12), WOODEND, 1.0,
               z0 + 0.001, None, sun, LWO * 0.8)
        _fill(out, _ell(ex, cy - 0.016, NW / poles * 0.40, 0.010, 10),
              _mul(WOODEND, 0.72), 1.0, z0 + 0.0012, 3)
    # lashings across the deck
    for q in (0.22, 0.80):
        ya = cy + D * q
        xa, xb = _lerp(cx - NW, fx0 - FW, q), _lerp(cx + NW, fx0 + FW, q)
        _limb(out, xa, ya, xb, ya, 0.007, ROPE, None, 1.0, z0 + 0.0008, sun, LWO * 0.4)
    # his bundle, tied to the deck
    bx, by = cx - 0.20, cy + 0.075
    _shape(out, _ell(bx, by + 0.03, 0.050, 0.042, 12), PATCH2, 1.0, z0 + 0.002,
           _mix(PATCH2, DHOTILT, 0.35), sun)
    _shape(out, _ell(bx + 0.028, by + 0.018, 0.022, 0.020, 10), PATCH, 1.0,
           z0 + 0.0022, None, sun, LWO * 0.6)
    # the mast, at the far right corner
    mx, my = fx0 + FW * 0.80, yf - 0.010
    top = my + 0.36
    _limb(out, mx, my, mx, top, 0.016, BAMB, BAMBLT, 1.0, z0 - 0.004, sun)
    for q in (0.3, 0.6):
        _seg(out, mx - 0.009, my + (top - my) * q, mx + 0.009, my + (top - my) * q,
             BAMBDK, 1.0, z0 - 0.0035, 0.004)
    arm = (mx + 0.075, top - 0.030)
    _limb(out, mx, top - 0.020, arm[0], arm[1], 0.009, BAMB, None, 1.0, z0 - 0.0038,
          sun, LWO * 0.6)
    # the pennant: a patched cloth that flies back toward us in the wind
    fl = math.sin(t * 6.0) * (0.010 + 0.020 * wind)
    pen = [(mx, top), (mx - 0.110, top - 0.020 + fl), (mx - 0.090, top - 0.048 + fl * 0.7),
           (mx, top - 0.060)]
    _shape(out, pen, PATCH, 1.0, z0 - 0.0042, _mix(PATCH, DHOTILT, 0.35), sun,
           LWO * 0.6)
    # the lantern
    lx, ly = arm[0], arm[1] - 0.060
    _seg(out, arm[0], arm[1], lx, ly + 0.030, INK, 1.0, z0 - 0.0036, 0.003)
    CUR['fl'] = 1.0
    _fill(out, _ell(lx, ly, 0.046, 0.046, 18), _mul(WARM, 1.25), 0.40 * lamp,
          z0 - 0.0034, 10)
    _fill(out, _ell(lx, ly, 0.028, 0.030, 16), _mul(WARM, 1.45), 0.65 * lamp,
          z0 - 0.0032, 8)
    _fill(out, _ell(lx, ly, 0.015, 0.019, 12), (1.25, 1.10, 0.85), lamp, z0 - 0.0030, 6)
    CUR['fl'] = 0.0
    _path(out, [(lx - 0.020, ly - 0.028), (lx + 0.020, ly - 0.028),
                (lx + 0.020, ly + 0.028), (lx - 0.020, ly + 0.028)], INK, 1.0,
          z0 - 0.0028, 0.0035, close=True)
    _seg(out, lx, ly - 0.028, lx, ly + 0.028, INK, 1.0, z0 - 0.0028, 0.0028)
    return (lx, ly)


# --- the ground he leaves from and lands on ----------------------------------------
def river_hw(y):
    d = max(FARY - y, 0.0)
    return 0.045 + d * 1.15


def river_cx(y):
    d = max(FARY - y, 0.0)
    return VPX + 0.06 * math.sin(d * 6.0) * d


def _gen_ground(rs):
    """His house on the left bank, the tree, and grass and reeds on both banks.

    Built once. The house and tree are homestead's own generators, scaled into place
    on the bank; the grass is new, laid out in perspective (bigger and sparser near,
    smaller and denser far)."""
    H = _gen_house()
    # stages 1-3 only (the house itself): the wheel, pole and garden rows were
    # placed for homestead's camera and would float loose in this one
    A = H['A'][H['st'] <= 3].copy()
    # every stage finished: this is the house after the story, not during it
    k, ax, ay = HOUSEK, (HX0 + HX1) * 0.5, GYH
    for cx_, cy_ in ((0, 1), (2, 3)):
        A[:, cx_] = HOUSEX + (A[:, cx_] - ax) * k
        A[:, cy_] = HOUSEY + (A[:, cy_] - ay) * k
    A[:, 10] *= k
    A[:, 8] = 0.30 + (A[:, 8] - 0.30) * 0.2
    A[:, 11] = 99.0
    rows = [A]
    G = []
    tones = ((0.430, 0.470, 0.195), (0.310, 0.400, 0.150), (0.560, 0.540, 0.270),
             (0.250, 0.340, 0.130), (0.470, 0.520, 0.230))
    for k2 in range(NTUFT):
        y = FARY - 0.012 - (rs.random() ** 1.6) * (FARY + 0.62)
        side = -1.0 if rs.random() < 0.5 else 1.0
        edge = river_cx(y) + side * river_hw(y)
        x = edge + side * rs.uniform(0.01, 0.95)
        if abs(x) > 1.0:
            continue
        dep = 0.25 + (FARY - y) * 1.35
        z = 0.20 + (FARY - y) * 0.40
        tone = tones[rs.randint(0, len(tones) - 1)]
        for j in range(rs.randint(3, 6)):
            h = rs.uniform(0.028, 0.070) * dep
            ang = rs.uniform(-0.45, 0.45)
            x0 = x + rs.uniform(-0.01, 0.01) * dep
            col = _mul(_mix(tone, tones[(j + k2) % 5], 0.3), rs.uniform(0.82, 1.12))
            G.append((x0, y, x0 + math.sin(ang) * h, y + math.cos(ang) * h,
                      col[0], col[1], col[2], 1.0, z + j * 1e-5, 0.0, 0.0048 * dep,
                      99.0))
    # reeds along both shorelines, standing in the shallows with their waterline
    for k2 in range(46):
        y = FARY - 0.010 - (rs.random() ** 1.4) * (FARY + 0.60)
        side = -1.0 if rs.random() < 0.5 else 1.0
        x = river_cx(y) + side * (river_hw(y) + rs.uniform(-0.04, 0.02))
        dep = 0.25 + (FARY - y) * 1.35
        h = rs.uniform(0.08, 0.16) * dep
        z = 0.20 + (FARY - y) * 0.40
        lean = rs.uniform(-0.2, 0.2)
        G.append((x, y, x + lean * h, y + h, 0.33, 0.40, 0.18, 1.0, z, 0.0,
                  0.0045 * dep, y + 0.006))
        if rs.random() < 0.55:
            G.append((x + lean * h * 0.80, y + h * 0.78, x + lean * h, y + h * 0.97,
                      0.38, 0.24, 0.13, 1.0, z + 0.0003, 0.0, 0.0110 * dep, y + 0.006))
    rows.append(np.array(G, dtype=np.float64))
    return np.concatenate(rows, axis=0)


# --- state -------------------------------------------------------------------------
def _new(seed):
    rs = random.Random(seed)
    canopy = [(TREEX + rs.uniform(-0.20, 0.26), rs.uniform(0.18, 0.52),
               rs.uniform(0.07, 0.13), rs.random()) for _ in range(16)]
    return {
        'seed': seed, 'rng': rs, 'canopy': canopy, 'tree': None, 'ground': None,
        'travel': 0.0, 'lastf': None, 'lastt': None, 'loops': 0,
        'pz': None, 'dust': [], 'stars': [], 'plasma': [],
        'seen': {}, 'rejects': 0, 'errs': 0, 'lastout': None,
        'labelt': -99.0, 'lastcp': -1, 'census': '',
    }


def _delta(S, inp, name):
    try:
        v = float(inp[name][0])
    except Exception:
        return 0
    p = S['seen'].get(name)
    S['seen'][name] = v
    if p is None:
        return 0
    return int(max(0.0, v - p))


def _plan(f, moon_near, comet_on, comet_left=False):
    """(pose, tool) from the story alone."""
    if f < 0.035:
        return 'steer', None
    if f < 0.100:
        return 'waveL', None                  # goodbye to the house on the left bank
    if f < 0.190:
        return 'look', None                   # looking down through the clouds
    if f < 0.300:
        return 'sit', None                    # watching the sun come up over the Earth
    if f < 0.415:
        return ('wave' if moon_near else 'stand'), None
    if f < 0.530:
        return 'cup', 'cup'                   # tea with the ringed giant
    if f < 0.640:
        # he points at it with whichever arm is on its side
        return (('pointL' if comet_left else 'point') if comet_on else 'stand'), None
    if f < 0.750:
        return 'look', None
    if f < 0.860:
        return 'sit', None                    # the spiral: he just sits
    if f < 0.905:
        return 'stand', None
    if f < 0.945:
        return 'brace', None                  # re-entry
    if f < 0.990:
        return 'look', None                   # looking for home
    return 'stand', None


def _frame(scriptOp):
    d = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    comp = scriptOp.parent()
    par = comp.par
    first = _S['S'] is None
    if first:
        _S['S'] = _new(SEED0)
    S = _S['S']
    if S['tree'] is None:
        S['tree'] = _gen_tree(S['rng'], S['canopy'])
        S['ground'] = _gen_ground(S['rng'])

    def ch(n, dv=0.0):
        if d is None:
            return dv
        try:
            return float(d[n][0])
        except Exception:
            return dv

    t = ch('rawtime', 0.0)
    if S['lastt'] is None:
        S['lastt'] = t
    dt = min(0.20, max(0.0, t - S['lastt']))
    S['lastt'] = t
    bass = ch('bass'); high = ch('high'); energy = ch('energy')
    kickenv = ch('kickenv'); dropenv = ch('dropenv')
    if first and d is not None:
        for nm in ('kickcnt', 'dropcnt', 'gustcnt', 'reseedcnt'):
            try:
                S['seen'][nm] = float(d[nm][0])
            except Exception:
                pass
    if _delta(S, d, 'reseedcnt'):
        keep = dict(S['seen'])
        S.update(_new((S['seed'] * 1103515245 + 12345) % 2147483647))
        S['seen'] = keep
        S['tree'] = _gen_tree(S['rng'], S['canopy'])
        S['ground'] = _gen_ground(S['rng'])
    rs = S['rng']
    ndrop = _delta(S, d, 'dropcnt')
    nstar = _delta(S, d, 'gustcnt')

    slen = _sane(ch('storylen', STORYDEF), STORYDEF, 1.0, 1.0e5)
    f = _sane(ch('show', 0.0) / slen, 0.0, 0.0, 1.0)
    # THE LOOP SEAM: every integrated phase and every particle list goes back to
    # empty inside the black, so nothing in the scene can grow past one story
    if S['lastf'] is not None and (f < S['lastf'] - 0.5 or abs(f - S['lastf']) > 0.02):
        S['travel'] = 0.0
        S['dust'], S['stars'], S['plasma'] = [], [], []
        if f < S['lastf'] - 0.5:
            S['loops'] += 1
    S['lastf'] = f
    loop = bool(par.Loop.eval())
    fade = (_ss(0.0, 0.010, f) * (1.0 - _ss(0.990, 1.0, f))) if loop else 1.0

    # --- the journey ------------------------------------------------------------
    alt = _tab(f, ALT_F, ALT_A)
    sf = _ss(0.55, 2.40, alt)
    gsun = _tab(f, GSUN_F, GSUN_H)
    amb = np.array([_tab(f, AMB_F, AMB_R), _tab(f, AMB_F, AMB_G),
                    _tab(f, AMB_F, AMB_B)])
    key = _tab(f, KEY_F, KEY_X)
    sun = 1.0 if key >= 0.0 else -1.0
    bulb = 1.0 - _ss(0.45, 0.55, f)
    reentry = _ss(0.895, 0.908, f) * (1.0 - _ss(0.935, 0.950, f))
    pace = float(par.Paceaudio.eval())
    # SPEED is where the music goes: energy sets how fast he flies, so the stars and
    # dust stream past faster when the track is full. Integrated; resets at the seam.
    speed = sf * (0.10 + 0.22 * energy * pace) + 0.8 * reentry
    S['travel'] += dt * speed
    wind = _cl(0.25 + 0.65 * sf + 0.25 * bass + reentry)

    # the Earth: its limb below as he leaves, a blue dot growing ahead as he returns
    if f < 0.5:
        etop = _tab(f, EDEP_F, EDEP_T)
        er = 2.40
        ex, ey = VPX, etop - er
        ea = _ss(0.5, 1.6, alt) if f < 0.31 else 0.0
    else:
        ex, ey, er = _persp(f, EHOME)
        ea = _ss(0.852, 0.862, f)
    mx, my, mr = _persp(f, MOON)
    ma = 1.0 if 0.285 < f < 0.44 else 0.0
    sx_, sy_, sr_ = _persp(f, SAT)
    sa = 1.0 if 0.395 < f < 0.552 else 0.0
    kq = _cl((f - 0.552) / (0.632 - 0.552))
    kx, ky = _lerp(1.25, -1.25, kq), _lerp(0.44, 0.27, kq)
    ka = 1.0 if 0.550 < f < 0.636 else 0.0
    gx, gy, gr = _persp(f, GAL)
    ga = _ss(0.735, 0.770, f) * (1.0 - _ss(0.850, 0.875, f))
    na = _ss(0.625, 0.670, f) * (1.0 - _ss(0.745, 0.780, f))
    nz = _tab(f, (0.625, 0.780), (3.2, 0.35))
    # the sun comes up over the Earth's limb, straight ahead
    pa = _ss(0.195, 0.215, f) * (1.0 - _ss(0.290, 0.312, f))
    px_, py_ = VPX - 0.46, max(etop if f < 0.5 else -2.0, -1.0) + _tab(
        f, (0.195, 0.300), (0.02, 0.19))
    lx, ly, lz = (0.70 * sun, 0.40, 0.60)
    comet_on = 0.565 < f < 0.625
    moon_near = 0.345 < f < 0.405

    # --- him, and his raft --------------------------------------------------------
    pose, tool = _plan(f, moon_near, comet_on, kx < MANX)
    tgt = POSES[pose]
    if S['pz'] is None or dt == 0.0:
        S['pz'] = {'hip': tgt[0], 'L': tgt[1], 'R': tgt[2], 'fs': tgt[3]}
    pz = S['pz']
    kk = min(1.0, dt * 4.5)
    pz['hip'] += (tgt[0] - pz['hip']) * kk
    pz['fs'] += (tgt[3] - pz['fs']) * kk
    for key2, i in (('L', 1), ('R', 2)):
        a, b = pz[key2]
        # the waving arm really waves
        wa = 0.28 * math.sin(t * 7.0) if (pose in ('wave', 'waveL') and
                                          ((pose == 'wave') == (key2 == 'R'))) else 0.0
        sipa = 0.35 * _ss(0.55, 0.85, 0.5 + 0.5 * math.sin(t * 0.55)) \
            if (pose == 'cup' and key2 == 'R') else 0.0
        pz[key2] = (a + (tgt[i][0] + wa - a) * kk, b + (tgt[i][1] + sipa + wa - b) * kk)
    nod = 0.012 * kickenv if pose in ('sit', 'cup', 'stand') else 0.0
    bob = 0.008 * math.sin(t * 1.1) + 0.003 * bass
    shake = reentry * 0.006 * math.sin(t * 37.0)
    roll = 0.018 * math.sin(t * 0.7) + 0.6 * shake
    lamp = 0.82 + 0.10 * kickenv + 0.08 * math.sin(t * 5.3) * math.sin(t * 2.1)

    rr = []
    CUR['wl'], CUR['fl'] = 99.0, 0.0
    lpos = _raft(rr, RAFTX, RAFTY + bob, t, sun, lamp, wind, 0.60)
    gyb = RAFTY + bob + (0.068 if pz['hip'] > 0.3 else 0.060)
    _man_back(rr, MANX, gyb, MANSC, pz, t, sun, nod, wind, 0.0, 0.62, tool)
    R = np.array(rr, dtype=np.float64)
    ca, sa2 = math.cos(roll), math.sin(roll)
    ox, oy = RAFTX, RAFTY
    for c0, c1 in ((0, 1), (2, 3)):
        X, Y = R[:, c0] - ox, R[:, c1] - oy
        R[:, c0] = ox + X * ca - Y * sa2 + shake
        R[:, c1] = oy + X * sa2 + Y * ca
    lpx = ox + (lpos[0] - ox) * ca - (lpos[1] - oy) * sa2
    lpy = oy + (lpos[0] - ox) * sa2 + (lpos[1] - oy) * ca

    out = []
    # --- space dust: motes that stream outward past him from the path ahead -------
    if sf > 0.05 and len(S['dust']) < NDUST and rs.random() < min(1.0, 3.0 * speed):
        a = rs.uniform(0.0, TAU)
        S['dust'].append([rs.uniform(0.02, 0.10), a, rs.uniform(0.6, 1.4), rs.random()])
    live = []
    for m_ in S['dust']:
        # radius from the vanishing point grows geometrically: perspective
        m_[0] *= 1.0 + dt * (0.9 + 5.0 * speed) * m_[2]
        if m_[0] > 1.6:
            continue
        live.append(m_)
        x = VPX + math.cos(m_[1]) * m_[0] * 1.3
        y = VPY + math.sin(m_[1]) * m_[0] * 0.8
        ln = 0.004 + 0.030 * m_[0] * speed
        CUR['fl'] = 1.0
        _seg(out, x, y, x + math.cos(m_[1]) * ln * 1.3, y + math.sin(m_[1]) * ln * 0.8,
             DUST, sf * _cl(m_[0] * 4.0) * (0.35 + 0.35 * m_[3]), 0.90,
             0.002 + 0.004 * m_[0])
        CUR['fl'] = 0.0
    S['dust'] = live

    # --- a shooting star on a drop (or the pad), over the top of the frame --------
    if (ndrop or nstar) and len(S['stars']) < 3:
        S['stars'].append([t, rs.uniform(-0.8, 0.2), rs.uniform(0.33, 0.46),
                           rs.uniform(0.9, 1.4)])
    live = []
    for st in S['stars']:
        a = (t - st[0]) / 0.9
        if a > 1.0:
            continue
        live.append(st)
        hx = st[1] + a * 0.9 * st[3]
        hy = st[2] - a * 0.18
        CUR['fl'] = 1.0
        _seg(out, hx - 0.16, hy + 0.032, hx, hy, (1.0, 0.95, 0.88),
             0.65 * math.sin(a * math.pi), 0.91, 0.0035)
        CUR['fl'] = 0.0
    S['stars'] = live

    # --- re-entry: plasma streaming back past the raft ------------------------------
    if reentry > 0.02:
        for _ in range(3):
            if len(S['plasma']) < NPLASMA:
                a = rs.uniform(-0.9, 0.9) + (math.pi if rs.random() < 0.5 else 0.0)
                S['plasma'].append([t, a, rs.uniform(0.18, 0.32)])
    live = []
    for pl in S['plasma']:
        a = (t - pl[0]) / 0.45
        if a > 1.0:
            continue
        live.append(pl)
        r0 = pl[2] * (1.0 + 2.2 * a)
        x0 = VPX + math.cos(pl[1]) * r0 * 1.2
        y0 = VPY + math.sin(pl[1]) * r0 * 0.7 - 0.10
        x1 = VPX + math.cos(pl[1]) * r0 * 1.2 * 1.35
        y1 = VPY + math.sin(pl[1]) * r0 * 0.7 * 1.35 - 0.10
        CUR['fl'] = 1.0
        _seg(out, x0, y0, x1, y1, _mix(PLASMA, (1.0, 0.9, 0.7), 0.5 * (1 - a)),
             reentry * 0.55 * (1.0 - a), 0.905, 0.006 + 0.010 * a)
        CUR['fl'] = 0.0
    S['plasma'] = live

    # --- the ground, scrolled down by the altitude ----------------------------------
    parts = [R]
    if out:
        parts.append(np.array(out, dtype=np.float64))
    if alt < 1.25:
        GA = S['ground'].copy()
        tsw = 0.004 + 0.008 * bass
        GA[:, 2] += tsw * np.sin(t * 1.5 + GA[:, 0] * 7.0) * (GA[:, 3] - GA[:, 1]) * 8.0
        T = S['tree']
        TA = T['A'].copy()
        osc = np.sin(t * 1.2 + T['ph'][T['g']])
        off = np.where(T['w'] > 0.0, (0.004 + 0.006 * bass) * T['w'] * osc, 0.0)
        TA[:, 0] += off
        TA[:, 2] += off
        TA = TA[T['w'] >= 0.0]              # no framing leaves in this view
        gw = [GA, TA]
        # the house at night: his window, and the bulb under the eave, still lit
        if bulb > 0.01:
            gl = []
            CUR['fl'] = 1.0
            wx_ = HOUSEX + (-0.490 - (HX0 + HX1) * 0.5) * HOUSEK
            wy_ = HOUSEY + (-0.073 - GYH) * HOUSEK
            _rect(gl, wx_, wy_, 0.086 * HOUSEK, 0.068 * HOUSEK, WARM, bulb * 0.9, 0.35)
            bx_ = HOUSEX + (BULB[0] - (HX0 + HX1) * 0.5) * HOUSEK
            by_ = HOUSEY + (BULB[1] - GYH) * HOUSEK
            _fill(gl, _ell(bx_, by_, 0.010, 0.012, 10), (1.0, 0.92, 0.7), bulb, 0.36, 3)
            CUR['fl'] = 0.0
            gw.append(np.array(gl, dtype=np.float64))
        G = np.concatenate(gw, axis=0)
        G[:, 1] -= alt
        G[:, 3] -= alt
        G[:, 11] = np.where(G[:, 11] < 50.0, G[:, 11] - alt, G[:, 11])
        parts.append(G)
    A = np.concatenate(parts, axis=0)

    # --- the waterline rule (see homestead) -----------------------------------------
    wl = A[:, 11]
    my_ = (A[:, 1] + A[:, 3]) * 0.5
    has = wl < 50.0
    wc = np.array(WATER)
    sub = has & (my_ < wl)
    if sub.any():
        A[sub, 7] *= 0.40
        A[np.ix_(sub, [4, 5, 6])] = A[np.ix_(sub, [4, 5, 6])] * 0.5 + wc * 0.5
    ref = has & (my_ >= wl)
    Rf = A[ref].copy()
    if len(Rf):
        rwl = Rf[:, 11]
        Rf[:, 1] = 2.0 * rwl - Rf[:, 1]
        Rf[:, 3] = 2.0 * rwl - Rf[:, 3]
        shim = 0.003 * np.sin(Rf[:, 1] * 160.0 + t * 2.6)
        Rf[:, 0] += shim
        Rf[:, 2] += shim
        Rf[:, 7] *= 0.30
        Rf[:, 4:7] = Rf[:, 4:7] * 0.62 + wc * 0.22
        Rf[:, 8] = 0.05 + Rf[:, 8] * 0.01
        Rf[:, 11] = 99.0

    # --- light the cels: the scene's ambient, and his lantern ----------------------
    lit = A[:, 9] < 0.5
    ink = float(par.Ink.eval())
    L = np.tile(amb, (len(A), 1))
    mxc = (A[:, 0] + A[:, 2]) * 0.5
    dd = (mxc - lpx) ** 2 + ((my_ - lpy) * 1.2) ** 2
    L += np.outer(lamp * 0.70 / (1.0 + dd * 18.0), np.array(WARM))
    if reentry > 0.0:
        L += np.outer(np.full(len(A), reentry * 0.22), np.array(PLASMA))
    A[lit, 4:7] = A[lit, 4:7] * L[lit] * ink
    if len(Rf):
        rl = Rf[:, 9] < 0.5
        Rf[rl, 4:7] = Rf[rl, 4:7] * amb * ink
        A = np.concatenate([A, Rf], axis=0)

    # --- cull, order, publish (see homestead) ----------------------------------------
    x0, y0, x1, y1 = A[:, 0], A[:, 1], A[:, 2], A[:, 3]
    dx, dy = x1 - x0, y1 - y0
    ln = np.hypot(dx, dy)
    al = A[:, 7]
    wd = A[:, 10]
    keep = ((np.minimum(x0, x1) - wd < CULLX) & (np.maximum(x0, x1) + wd > -CULLX)
            & (np.minimum(y0, y1) - wd < CULLY) & (np.maximum(y0, y1) + wd > -CULLY)
            & (ln > MINLEN) & (al > 0.004) & (wd > 1e-5))
    idx = np.nonzero(keep)[0]
    if len(idx) > MAXSEG:
        idx = idx[:MAXSEG]
    idx = idx[np.argsort(A[idx, 8], kind='stable')]
    n = len(idx)
    outc = np.zeros((11, MAXSEG), dtype=np.float64)
    outc[6] = 1.0
    if n:
        outc[0, :n] = (x0[idx] + x1[idx]) * 0.5
        outc[1, :n] = (y0[idx] + y1[idx]) * 0.5
        outc[2, :n] = A[idx, 8]
        outc[3, :n] = np.degrees(np.arctan2(-dx[idx], dy[idx]))
        outc[4, :n] = np.maximum(wd[idx], 1e-5)
        outc[5, :n] = np.maximum(ln[idx], 1e-5)
        outc[7, :n] = np.clip(A[idx, 4], 0.0, 4.0)
        outc[8, :n] = np.clip(A[idx, 5], 0.0, 4.0)
        outc[9, :n] = np.clip(A[idx, 6], 0.0, 4.0)
        outc[10, :n] = np.clip(al[idx], 0.0, 1.0)
    colbad = ~np.isfinite(outc)
    if colbad.any():
        outc = np.where(colbad, 0.0, outc)
    kill = (colbad.any(axis=0) | (outc[4] > MAXW) | (outc[5] > MAXL))
    nkill = int(kill.sum())
    if nkill:
        outc[4] = np.where(kill, 0.0, outc[4])
        outc[5] = np.where(kill, 0.0, outc[5])
        outc[10] = np.where(kill, 0.0, outc[10])
    S['rejects'] = S.get('rejects', 0) + nkill
    S['lastout'] = outc
    _publish(scriptOp, outc)

    cp = 0
    for i, c in enumerate(CHECKPOINTS):
        if c[2] <= f + 1e-6:
            cp = i
    if cp != S['lastcp']:
        S['lastcp'] = cp
        S['labelt'] = t
    lf = math.exp(-max(0.0, t - S['labelt']) / 3.2)

    showt = ch('show', 0.0)
    vals = dict(Chapter=cp, Segs=n, Alt=alt, Sf=sf, Travel=S['travel'], Gsun=gsun,
                Bulb=bulb, Reentry=reentry, Fade=fade, Loops=S['loops'], Warp=speed,
                Ex=ex, Ey=ey, Er=er, Ea=ea, Erot=showt * 0.012,
                Mx=mx, My=my, Mr=mr, Ma=ma, Sx=sx_, Sy=sy_, Sr=sr_, Sa=sa,
                Kx=kx, Ky=ky, Ka=ka, Gx=gx, Gy=gy, Gr=gr, Ga=ga, Grot=showt * 0.010,
                Na=na, Nz=nz, Px=px_, Py=py_, Pa=pa, Lx=lx, Ly=ly, Lz=lz,
                Rejects=S.get('rejects', 0), Labelfade=lf)
    try:
        for k3, v in vals.items():
            getattr(par, k3).val = _sane(v, 0.0)
        txt = CHECKPOINTS[cp][1].strip()
        if par.Scaletxt.eval() != txt:
            par.Scaletxt.val = txt
    except Exception:
        pass
    S['census'] = ('f %.3f | alt %.2f sf %.2f | pose %s | quads %d/%d | dust %d | '
                   'loops %d | rejects %d' % (f, alt, sf, pose, n, MAXSEG,
                                              len(S['dust']), S['loops'],
                                              S.get('rejects', 0)))
    return


def _publish(scriptOp, outc):
    # copyNumpyArray is a memcpy; `.vals = list` built 66k Python floats a frame.
    # NEVER clear() AND RE-APPEND CHANNELS EVERY FRAME. On 2025.33230 a Script
    # CHOP that does leaks native memory inside TouchDesigner — measured 2-5 MB a
    # minute on a 12k-sample publish, ~0.6 MB a minute even on a few 1-sample
    # channels. Build the channels once; after that only write values.
    # (numChans cannot be read from inside a cook, so whether they exist is
    # tracked here; if a write ever fails they are rebuilt and the write retried.)
    f32 = outc.astype(np.float32)
    for attempt in (0, 1):
        try:
            if not _PUB['built']:
                scriptOp.clear()
                for nm in CH:
                    scriptOp.appendChan(nm)
                scriptOp.numSamples = MAXSEG
                _PUB['built'] = True
            for ii in range(len(CH)):
                scriptOp[ii].copyNumpyArray(f32[ii])
            return
        except Exception:
            _PUB['built'] = False
    raise RuntimeError('could not publish the instance channels')


_PUB = {'built': False}


def onCook(scriptOp):
    """Publish a frame, and NEVER publish a broken one (see monsoon)."""
    try:
        _frame(scriptOp)
        return
    except Exception:
        import traceback
        S = _S['S']
        if isinstance(S, dict):
            S['errs'] = S.get('errs', 0) + 1
            S['lasterr'] = traceback.format_exc()
            if S['errs'] <= 3:
                print('[voyage engine] frame failed:\n' + S['lasterr'])
            prev = S.get('lastout')
        else:
            prev = None
        if prev is None:
            raise
        _publish(scriptOp, prev)
    return
'''

eng_src = C(textDAT, 'engine_src', 1780, 980)
_eng_consts = dict(
    CHECKPOINTS=CHECKPOINTS, MAXSEG=MAXSEG, SEED0=20260924,
    CH=('tx', 'ty', 'tz', 'rz', 'sx', 'sy', 'sz', 'r', 'g', 'b', 'a'),
    FARY=FARY, SHOREY=SHOREY, SHOREX=SHOREX, BANKK=BANKK, BANKH=BANKH,
    GYH=GYH, FLOORY=FLOORY, WALLTOP=WALLTOP, HX0=HX0, HX1=HX1,
    MANGY=MANGY, MANX=MANX, MANSC=MANSC, RAFTX=RAFTX, RAFTY=RAFTY,
    WX=WX, WY=WY, WR=WR, WWL=WWL, BULB=BULB, GARDEN=GARDEN, ROWS=ROWS,
    HOUSEK=HOUSEK, HOUSEX=HOUSEX, HOUSEY=HOUSEY, VPX=VPX, VPY=VPY,
    ALT_F=ALT_F, ALT_A=ALT_A, GSUN_F=GSUN_F, GSUN_H=GSUN_H,
    AMB_F=AMB_F, AMB_R=AMB_R, AMB_G=AMB_G, AMB_B=AMB_B, KEY_F=KEY_F, KEY_X=KEY_X,
    EDEP_F=EDEP_F, EDEP_T=EDEP_T, MOON=MOON, SAT=SAT, GAL=GAL, EHOME=EHOME,
    STORYDEF=STORYDEF,
    LWO=0.0048, LWT=0.0034, HS=1.30,
    CLR0=-0.760, CLR1=0.300, NTUFT=230, TREEX=TREEX,
    NDUST=70, NPLASMA=60,
    CULLX=1.20, CULLY=0.70, MINLEN=0.0004, MAXW=0.60, MAXL=2.80,
)
for _k, _v in PAL.items():
    _eng_consts[_k] = _v
eng_src.text = hdr(**_eng_consts) + ENGINE_BODY

engine = C(scriptCHOP, 'engine', 1940, 980)
engine.par.callbacks = eng_src.name
W(director, engine, 0)


# ---------------------------------------------------------------------------
# GEOMETRY AND RENDER — verbatim from homestead
# ---------------------------------------------------------------------------
# ---- BEGIN HOMESTEAD (verbatim) ----
SHAPE_BODY = '''# ONE UNIT QUAD, 1x1, centred, and it is the entire drawing system.


def onCook(scriptOp):
    scriptOp.clear()
    pts = ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))
    for (px, py) in pts:
        pt = scriptOp.appendPoint()
        pt.x, pt.y, pt.z = px, py, 0.0
    poly = scriptOp.appendPoly(4, closed=True, addPoints=False)
    for i in range(4):
        poly[i].point = scriptOp.points[i]
    return
'''
shape_src = C(textDAT, 'shape_src', 1300, 200)
shape_src.text = SHAPE_BODY
unit_quad = C(scriptSOP, 'unit_quad', 1440, 200)
unit_quad.par.callbacks = shape_src.name

mat_flat = C(constantMAT, 'mat_flat', 1600, 200)
soft(mat_flat, blending=True, depthtest=False, depthwriting=False, alpha=1.0)
SRCB = menu_pick(mat_flat.par.srcblend, 'sa', 'srcalpha')
DSTB = menu_pick(mat_flat.par.destblend, 'omsa', 'oneminussrcalpha')

g_cels = C(geometryCOMP, 'geo_cels', 1780, 200)
for _stale in list(g_cels.children):
    _stale.destroy()
_sel = g_cels.create(selectSOP, 'shape')
_sel.par.sop = '../' + unit_quad.name
_sel.render = True
_sel.display = True
g_cels.par.material = mat_flat.name
g_cels.par.instancing = True
g_cels.par.instanceop = engine.name
for _p, _v in (('instancetx', 'tx'), ('instancety', 'ty'), ('instancetz', 'tz'),
               ('instancerz', 'rz'), ('instancesx', 'sx'), ('instancesy', 'sy'),
               ('instancesz', 'sz')):
    soft(g_cels, **{_p: _v})
soft(g_cels, instancecolormode='replace')
for _p, _v in (('instancer', 'r'), ('instanceg', 'g'), ('instanceb', 'b'),
               ('instancea', 'a')):
    soft(g_cels, **{_p: _v})

cam = C(cameraCOMP, 'cam', 1620, 330, projection='ortho', tz=4.0, tx=CAMX, ty=CAMY)
soft(cam, orthowidth=ORTHOW, near=0.1, far=20.0)

render_cels = C(renderTOP, 'render_cels', 1940, 200)
res(render_cels)
render_cels.par.camera = cam.name
render_cels.par.geometry = g_cels.name
render_cels.par.bgcolora = 0.0
AA = menu_pick(render_cels.par.antialias, 'aa4', 'aa2')

glow_blur = C(blurTOP, 'glow_blur', 2100, 300, size=10.0)
res(glow_blur, OUTW // 4, OUTH // 4)
W(render_cels, glow_blur)
# ---- END HOMESTEAD ----


def _g3(c):
    return 'vec3(%.4f, %.4f, %.4f)' % c


world = C(glslTOP, 'world', 2260, 200)
res(world)
world_pix = C(textDAT, 'world_pixel', 2260, 120)
world_pix.text = ('''// THE PAINTED UNIVERSE. The river he leaves from and lands on (homestead's sky,
// hills and jungle, verbatim, seen up-river), the cloud sea, and then space: a star
// field streaming outward from the vanishing point ahead, and the Earth, the Moon, a
// ringed giant, a comet, a nebula and a spiral galaxy — every one kept dim and
// pastel, and placed by the engine in perspective.
//
// Every scalar arrives on the Vectors page (the Constants page is broken on this
// build — see MACHINE.md) and goes through san() before it is used.
uniform vec4 uA;   // x story time, y altitude, z space fade, w travel
uniform vec4 uB;   // x bass, y high, z kick, w loop fade
uniform vec4 uC;   // x vignette, y brightness, z glow, w label fade
uniform vec4 uD;   // x ground sun, y bulb, z re-entry, w speed
uniform vec4 uE;   // earth x, y, r, a
uniform vec4 uF;   // x earth spin, y galaxy spin, z nebula a, w nebula zoom
uniform vec4 uM;   // moon x, y, r, a
uniform vec4 uS;   // ringed giant x, y, r, a
uniform vec4 uK;   // comet x, y, a
uniform vec4 uG;   // galaxy x, y, r, a
uniform vec4 uP;   // sun x, y, a
uniform vec4 uL;   // key light direction
out vec4 fragColor;

const float OW = ''' + repr(ORTHOW) + ''';
const float OH = ''' + repr(ORTHOH) + ''';
const float FARY = ''' + repr(FARY) + ''';
const float CAMX = ''' + repr(CAMX) + ''';
const float CAMY = ''' + repr(CAMY) + ''';
const float SHOREY = ''' + repr(SHOREY) + ''';
const float SHOREX = ''' + repr(SHOREX) + ''';
const float BANKK = ''' + repr(BANKK) + ''';
const float BANKH = ''' + repr(BANKH) + ''';
const vec2 VP = vec2(''' + repr(VPX) + ''', ''' + repr(VPY) + ''');
const vec2 BULB = vec2(''' + repr(HOUSEX) + ''', ''' + repr(HOUSEY) + ''');
const vec3 WARM = ''' + _g3(PAL['WARM']) + ''';
const float SUNY0 = 0.085;
const float SUNYK = 0.27;
const vec2 MOONP = vec2(0.46, 0.36);

// the space colour and how far the sky has gone to it: set in main() before the
// homestead sky is painted, so its sky can dissolve into space as he climbs
vec3 gSpace = vec3(0.0);
float gSF = 0.0;
// and the altitude: the painted sky's sun, moon and stars are pinned to it, so as
// he climbs the land falls away beneath them while they stay where they are
float gAlt = 0.0;

// ---- BEGIN HOMESTEAD (verbatim) ----
float san(float v, float lo, float hi, float dv) {
    return (v == v) ? clamp(v, lo, hi) : dv;
}

float hash21(vec2 p) {
    p = fract(p * vec2(233.34, 851.73));
    p += dot(p, p + 23.45);
    return fract(p.x * p.y);
}

float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    float a = hash21(i), b = hash21(i + vec2(1.0, 0.0));
    float c = hash21(i + vec2(0.0, 1.0)), d = hash21(i + vec2(1.0, 1.0));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p) {
    float s = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) {
        s += a * vnoise(p);
        p = p * 2.03 + vec2(17.1, 9.2);
        a *= 0.5;
    }
    return s;
}

float fbm3(vec2 p) {
    float s = 0.0, a = 0.5;
    for (int i = 0; i < 3; i++) {
        s += a * vnoise(p);
        p = p * 2.07 + vec2(5.3, 1.9);
        a *= 0.5;
    }
    return s / 0.875;
}

float landEdge(float y) { return SHOREX + BANKK * pow(max(SHOREY - y, 0.0) / BANKH, 0.85); }
float shoreTop(float x) { return SHOREY + 0.006 * sin(x * 11.0) + 0.004 * sin(x * 27.0 + 1.3); }

// --- light, by sun height --------------------------------------------------
vec3 skyTop(float h) {
    vec3 night = vec3(0.010, 0.016, 0.045), dusk = vec3(0.110, 0.120, 0.300);
    vec3 day = vec3(0.150, 0.240, 0.380);
    return mix(mix(dusk, day, smoothstep(-0.05, 0.35, h)), night, smoothstep(-0.12, -0.45, h));
}
vec3 skyHor(float h) {
    vec3 night = vec3(0.035, 0.050, 0.100), dusk = vec3(0.600, 0.300, 0.240);
    vec3 gold = vec3(0.720, 0.480, 0.300), day = vec3(0.560, 0.520, 0.440);
    vec3 c = mix(dusk, gold, smoothstep(-0.02, 0.10, h));
    c = mix(c, day, smoothstep(0.12, 0.42, h));
    return mix(c, night, smoothstep(-0.12, -0.45, h));
}
vec3 ambient(float h) {
    vec3 night = vec3(0.130, 0.160, 0.300), dusk = vec3(0.260, 0.260, 0.440);
    vec3 sset = vec3(0.600, 0.440, 0.420), gold = vec3(0.700, 0.560, 0.440);
    vec3 day = vec3(0.700, 0.640, 0.540), noon = vec3(0.690, 0.650, 0.560);
    vec3 c = mix(night, dusk, smoothstep(-0.60, -0.20, h));
    c = mix(c, sset, smoothstep(-0.20, 0.00, h));
    c = mix(c, gold, smoothstep(0.00, 0.15, h));
    c = mix(c, day, smoothstep(0.15, 0.40, h));
    return mix(c, noon, smoothstep(0.40, 0.90, h));
}
vec3 sunColor(float h) {
    // golden even at noon, so the sun can never be mistaken for the moon
    return mix(vec3(1.00, 0.42, 0.16), vec3(1.00, 0.80, 0.52), smoothstep(0.0, 0.45, h));
}

float treeline(float x) {
    float base = FARY + 0.020 + 0.022 * fbm3(vec2(x * 3.5, 7.0));
    float s = 0.0;
    // broad canopies
    float fx = x * 30.0;
    float i0 = floor(fx);
    for (int j = -1; j <= 1; j++) {
        float ii = i0 + float(j);
        float hh = 0.010 + 0.028 * hash21(vec2(ii, 3.0));
        float cx = ii + 0.5 + (hash21(vec2(ii, 5.0)) - 0.5) * 0.7;
        float r = 0.75 + 0.5 * hash21(vec2(ii, 9.0));
        float dd = abs(fx - cx) / r;
        s = max(s, hh * sqrt(max(0.0, 1.0 - dd * dd)));
    }
    // and a few tall ones standing out of it
    float gx = x * 11.0;
    float g0 = floor(gx);
    for (int j = -1; j <= 1; j++) {
        float ii = g0 + float(j);
        float on = step(0.62, hash21(vec2(ii, 13.0)));
        float hh = (0.030 + 0.030 * hash21(vec2(ii, 17.0))) * on;
        float cx = ii + 0.5 + (hash21(vec2(ii, 19.0)) - 0.5) * 0.6;
        float dd = abs(gx - cx) / 0.28;
        s = max(s, hh * sqrt(max(0.0, 1.0 - dd * dd)));
    }
    return base + s;
}

// Everything above the water, as a function, so the river can reflect it.
vec3 above(vec2 w, float sunh, float sunx, float cph, float t, float high,
           float rain, bool refl, float kick) {
    float topy = OH * 0.5;
    float h = clamp((w.y - FARY) / (topy - FARY), 0.0, 1.0);
    vec3 hor = skyHor(sunh);
    vec3 amb = ambient(sunh);
    vec3 sc = sunColor(sunh);
    float night = smoothstep(0.02, -0.35, sunh);
    float sunvis = smoothstep(-0.10, 0.03, sunh);
    vec3 col = mix(hor, skyTop(sunh), pow(h, 0.55));
    col = mix(col, vec3(0.42, 0.44, 0.48) * (0.3 + 0.7 * amb), rain * 0.55);

    vec2 sp = vec2(sunx, FARY + SUNY0 + sunh * SUNYK + gAlt);   // (voyage) pinned to the altitude
    vec2 dv = (w - sp);
    float d = length(dv);
    // THE SUN IS PASTEL, AND IT BREATHES WITH THE BEAT — GENTLY. A soft peach
    // disc that never reaches full white, with a low halo; the kick lifts the halo
    // and the disc by a few percent, never to a flash. Its position in the sky, not
    // its brightness, is what says it is day.
    float clear = 1.0 - smoothstep(0.05, 0.45, rain);
    vec3 pastel = mix(vec3(0.96, 0.66, 0.56), vec3(0.97, 0.84, 0.70), smoothstep(0.05, 0.45, sunh));
    col += pastel * (exp(-d * 3.6) * (0.05 + 0.05 * kick) + exp(-d * 16.0) * (0.10 + 0.12 * kick))
           * sunvis * (0.3 + 0.7 * clear);
    vec3 core = pastel * (0.80 + 0.07 * kick);
    float rs = 0.026 * (1.0 + 0.04 * kick);
    // a soft edge, painted rather than burned in
    col = mix(col, core, smoothstep(rs + 0.006, rs - 0.004, d) * sunvis * clear * 0.95);

    // stars — only in the top half of the frame, and fading in toward the top, so
    // none of them ever sits over the hills, the jungle or the land
    float topfrac = (w.y - gAlt - CAMY) / (OH * 0.5);   // (voyage) pinned to the altitude
    if (night > 0.01 && !refl && topfrac > 0.0) {
        vec2 g = floor(w * 150.0);
        float hs = hash21(g);
        float tw = 0.55 + 0.45 * sin(t * (1.5 + 3.0 * hs) * (0.7 + 0.8 * high) + hs * 40.0);
        float star = step(0.9955, hs) * tw * smoothstep(0.0, 0.35, topfrac);
        col += vec3(0.85, 0.90, 1.0) * star * night * 0.9;
    }
    // THE MOON GLOWS TO THE BEAT too, a cool halo that breathes with the kick
    vec2 mp = MOONP + vec2(0.0, gAlt);   // (voyage) pinned to the altitude
    float md = length(w - mp);
    float moon = smoothstep(0.034, 0.030, md) * night * (refl ? 0.30 : 1.0);
    col = mix(col, vec3(0.86, 0.88, 0.95) * (0.80 + 0.15 * fbm3((w - mp) * 60.0) + 0.30 * kick), moon);
    col += vec3(0.30, 0.34, 0.50) * (exp(-md * 9.0) * (0.12 + 0.22 * kick)
                                     + exp(-md * 30.0) * (0.10 + 0.45 * kick)) * night;

    // clouds, lit on the sun's side
    vec2 cp = vec2(w.x * 1.3 + cph, w.y * 4.2);
    float c = fbm(cp);
    float c2 = fbm(cp + vec2(0.06 * sign(sunx - w.x + 1e-4), -0.10));
    float cover = 0.60 - 0.18 * rain;
    float cm = smoothstep(cover, cover + 0.20, c) * smoothstep(FARY + 0.05, FARY + 0.18, w.y);
    vec3 clit = mix(sc, vec3(0.8), 0.45) * (0.55 * amb.g + 0.25) * (0.35 + 0.65 * (1.0 - night));
    vec3 cshade = mix(hor, skyTop(sunh), 0.5) * 0.75 + vec3(0.04);
    vec3 ccol = mix(clit, cshade, smoothstep(-0.02, 0.10, c2 - c) * 0.9 + 0.1);
    ccol = mix(ccol, vec3(0.50, 0.52, 0.56) * (0.25 + 0.75 * amb), rain * 0.6);
    col = mix(col, ccol, cm * (0.85 - 0.35 * night));

    // (voyage) the sky dissolves into space as he climbs
    col = mix(col, gSpace, gSF);
    // far range, deep in aerial perspective
    float m1 = FARY + 0.075 + 0.075 * fbm(vec2(w.x * 1.1 + 3.0, 2.0));
    if (w.y < m1) {
        float sl = 0.75 * (fbm(vec2((w.x + 0.02) * 1.1 + 3.0, 2.0)) - fbm(vec2((w.x - 0.02) * 1.1 + 3.0, 2.0)));
        float lit = 0.80 + 2.2 * sl * sign(sunx - w.x) * sunvis;
        vec3 mc = vec3(0.30, 0.36, 0.46) * amb * clamp(lit, 0.55, 1.25);
        mc *= 0.90 + 0.18 * fbm3(w * vec2(10.0, 22.0));
        col = mix(mc, hor, 0.58 + 0.12 * smoothstep(m1 - 0.08, m1, w.y) - 0.2 * rain);
    }
    // near range, greener, less haze
    float m2 = FARY + 0.045 + 0.050 * fbm(vec2(w.x * 2.0 + 11.0, 5.0));
    if (w.y < m2) {
        float sl = fbm(vec2((w.x + 0.015) * 2.0 + 11.0, 5.0)) - fbm(vec2((w.x - 0.015) * 2.0 + 11.0, 5.0));
        float lit = 0.80 + 2.4 * sl * sign(sunx - w.x) * sunvis;
        vec3 mc = vec3(0.17, 0.26, 0.18) * amb * clamp(lit, 0.5, 1.3);
        mc *= 0.82 + 0.30 * fbm3(w * vec2(18.0, 36.0));
        col = mix(mc, hor, 0.34 - 0.1 * rain);
    }
    // the far jungle
    float ft = treeline(w.x);
    if (w.y < ft) {
        float tex = 0.72 + 0.45 * vnoise(vec2(w.x * 150.0, w.y * 90.0)) * vnoise(vec2(w.x * 40.0, w.y * 70.0 + 3.0));
        float crown = smoothstep(ft - 0.025, ft, w.y);
        float side = 0.5 + 0.5 * sign(sunx - w.x);
        vec3 fc = vec3(0.070, 0.150, 0.075) * tex * (0.9 + 0.5 * crown * sunvis * (0.6 + 0.4 * side));
        fc *= amb;
        col = mix(fc, hor, 0.14);
    }
    // the far bank itself: a strip of mud and roots
    if (w.y < FARY + 0.004) {
        col = vec3(0.16, 0.12, 0.08) * amb * (0.8 + 0.3 * vnoise(vec2(w.x * 200.0, 1.0)));
    }
    // mist lying on the jungle at dawn and dusk, and after the rain
    float mist = 0.55 * (1.0 - smoothstep(0.05, 0.40, sunh)) * (1.0 - night * 0.6) + 0.35 * rain;
    float mh = exp(-max(w.y - FARY, 0.0) * 26.0) * (0.75 + 0.25 * fbm3(vec2(w.x * 4.0 - t * 0.01, 1.0)));
    col = mix(col, mix(hor, vec3(0.8), 0.25) * (0.35 + 0.65 * amb), clamp(mist * mh, 0.0, 0.85));
    return col;
}
// ---- END HOMESTEAD ----

// ================================================================================
// SPACE
// ================================================================================
float hash31(vec3 p) {
    p = fract(p * vec3(443.897, 441.423, 437.195));
    p += dot(p, p.yzx + 19.19);
    return fract((p.x + p.y) * p.z);
}
float vnoise3(vec3 p) {
    vec3 i = floor(p), f = fract(p);
    vec3 u = f * f * (3.0 - 2.0 * f);
    float a = mix(mix(hash31(i), hash31(i + vec3(1, 0, 0)), u.x),
                  mix(hash31(i + vec3(0, 1, 0)), hash31(i + vec3(1, 1, 0)), u.x), u.y);
    float b = mix(mix(hash31(i + vec3(0, 0, 1)), hash31(i + vec3(1, 0, 1)), u.x),
                  mix(hash31(i + vec3(0, 1, 1)), hash31(i + vec3(1, 1, 1)), u.x), u.y);
    return mix(a, b, u.z);
}
float fbm3d(vec3 p) {
    float s = 0.0, a = 0.5;
    for (int i = 0; i < 4; i++) {
        s += a * vnoise3(p);
        p = p * 2.04 + vec3(3.1, 7.7, 1.3);
        a *= 0.5;
    }
    return s / 0.9375;
}

// Stars streaming OUTWARD from the vanishing point: four layers of the same cell
// field, each zooming from far to near and recycling, so it reads as flying forward.
vec3 starfield(vec2 w, float tr, float high, float t, float speed) {
    vec3 s = vec3(0.0);
    vec2 q = w - VP;
    float rq = length(q);
    vec2 rad = q / max(rq, 1e-4);
    for (int i = 0; i < 4; i++) {
        float ph = fract(tr * 0.22 + float(i) / 4.0);
        float z = mix(5.0, 0.55, ph);
        vec2 p = q * z * 9.0 + float(i) * 17.3;
        vec2 id = floor(p);
        vec2 f = fract(p) - 0.5;
        float h = hash21(id + float(i) * 7.1);
        if (h > 0.915) {
            vec2 o = (vec2(hash21(id + 3.1), hash21(id + 9.7)) - 0.5) * 0.6;
            // the offset in WORLD units, so a near star is brighter but not bigger
            vec2 d = (f - o) / (z * 9.0);
            float al = dot(d, rad), pe = dot(d, vec2(-rad.y, rad.x));
            // a little stretch along the direction of flight, more when faster
            float st = 1.0 + 3.0 * speed * ph;
            float sz = 0.0017 + 0.0010 * ph;
            float r2 = ((al * al) / (st * st) + pe * pe) / (sz * sz) * 0.0035;
            float life = smoothstep(0.0, 0.25, ph) * smoothstep(1.0, 0.85, ph);
            float tw = 0.75 + 0.25 * sin(t * (1.0 + 3.0 * h) * (0.7 + 0.8 * high) + h * 60.0);
            float br = exp(-r2 / 0.0035) * life * tw * (0.35 + 0.65 * (h - 0.915) / 0.085);
            vec3 c = mix(vec3(0.85, 0.82, 1.0), vec3(1.0, 0.88, 0.78), hash21(id + 5.5));
            s += c * br * 0.85;
        }
    }
    return s;
}

// A lit sphere helper: normal from a disc, and a soft anti-aliased edge.
vec3 sphN(vec2 w, vec2 c, float r, out float q) {
    vec2 d = (w - c) / max(r, 1e-4);
    q = dot(d, d);
    return vec3(d, sqrt(max(0.0, 1.0 - q)));
}

vec3 spaceColour(vec2 w, float t, float tr, float high, float kick, float speed) {
    vec3 L = normalize(vec3(san(uL.x, -1.0, 1.0, 0.7), san(uL.y, -1.0, 1.0, 0.4),
                            san(uL.z, 0.05, 1.0, 0.6)));
    // deep, faintly violet night; a little lighter toward the path ahead
    vec3 col = mix(vec3(0.018, 0.020, 0.042), vec3(0.040, 0.036, 0.070),
                   exp(-length(w - VP) * 1.4));
    // the Milky Way: a faint band leaning across the frame, drifting with the flight
    vec2 mw = w - VP;
    float band = dot(mw, normalize(vec2(-0.40, 1.0)));
    float mwv = exp(-band * band * 7.0) * fbm(w * 2.4 + vec2(tr * 0.05, 0.0));
    col += vec3(0.090, 0.080, 0.120) * mwv;

    // the spiral galaxy, ahead
    float ga = san(uG.w, 0.0, 1.0, 0.0);
    if (ga > 0.001) {
        vec2 p = w - uG.xy;
        float gr = max(uG.z, 1e-3);
        float gro = uF.y;
        p = mat2(cos(gro), -sin(gro), sin(gro), cos(gro)) * p;
        p.y /= 0.52;
        float r = length(p) / gr;
        float th = atan(p.y, p.x);
        float arm = 0.5 + 0.5 * cos(2.0 * (th - log(r + 0.04) * 2.6));
        arm = pow(arm, 3.0) * exp(-r * 2.3) * (0.55 + 0.7 * fbm(p / gr * 7.0));
        float core = exp(-r * 10.0) * 1.1 + exp(-r * 3.2) * 0.25;
        float hii = step(0.985, hash21(floor(p / gr * 60.0))) * arm * 3.0;
        vec3 gc = vec3(0.95, 0.86, 0.74) * core + vec3(0.62, 0.66, 0.92) * arm
                  + vec3(0.95, 0.60, 0.75) * hii;
        col += gc * ga * 0.60 * smoothstep(1.3, 0.8, r);
    }
    // the nebula: pastel gas he flies into, zooming as he goes
    float na = san(uF.z, 0.0, 1.0, 0.0);
    if (na > 0.001) {
        float nz = san(uF.w, 0.2, 5.0, 1.0);
        vec2 p = (w - VP) * nz + vec2(3.0, 1.0);
        float n1 = fbm(p * 1.3);
        float n2 = fbm(p * 2.6 + 5.0);
        float dust = fbm(p * 3.4 + 9.0);
        float cl = smoothstep(0.38, 0.86, n1);
        vec3 nc = mix(vec3(0.82, 0.52, 0.70), vec3(0.44, 0.72, 0.76), smoothstep(0.3, 0.7, n2));
        nc = mix(nc, vec3(0.70, 0.62, 0.90), smoothstep(0.55, 0.8, n1) * 0.5);
        nc *= 1.0 - 0.75 * smoothstep(0.52, 0.72, dust);
        col += nc * cl * na * 0.55;
        // young stars glowing inside it
        vec2 sp = p * 6.0;
        vec2 f = fract(sp) - 0.5;
        float h = hash21(floor(sp) + 41.0);
        col += vec3(0.85, 0.90, 1.0) * step(0.965, h) * exp(-dot(f, f) / 0.004) * na * cl * 1.4;
    }
    col += starfield(w, tr, high, t, speed);

    // the sun, coming up over the Earth's limb: pastel, and a gentle breath on the kick
    float pa = san(uP.z, 0.0, 1.0, 0.0);
    if (pa > 0.001) {
        float d = length(w - uP.xy);
        vec3 pc = vec3(0.97, 0.80, 0.64);
        col += pc * (exp(-d * 3.2) * (0.08 + 0.05 * kick) + exp(-d * 14.0) * (0.14 + 0.10 * kick)) * pa;
        col = mix(col, pc * (0.82 + 0.06 * kick), smoothstep(0.036, 0.028, d) * pa);
    }

    // the ringed giant: the far half of the ring, the planet, then the near half
    float sa = san(uS.w, 0.0, 1.0, 0.0);
    if (sa > 0.001) {
        vec2 c = uS.xy;
        float r = max(uS.z, 1e-3);
        vec2 p = w - c;
        float rt = -0.32;
        vec2 rp = mat2(cos(rt), -sin(rt), sin(rt), cos(rt)) * p;
        float er = length(vec2(rp.x, rp.y / 0.26)) / r;
        float ring = smoothstep(1.35, 1.40, er) * smoothstep(2.35, 2.28, er);
        ring *= 0.55 + 0.45 * sin(er * 34.0) * sin(er * 11.0 + 1.0);
        ring *= 1.0 - 0.85 * smoothstep(0.03, 0.0, abs(er - 1.92));
        vec3 rc = vec3(0.86, 0.78, 0.62);
        if (rp.y > 0.0) col = mix(col, rc * 0.80, ring * 0.75 * sa);
        float q;
        vec3 n = sphN(w, c, r, q);
        if (q < 1.0) {
            float v = n.y * 7.0 + 0.6 * fbm3d(n * 3.0);
            vec3 bc = mix(vec3(0.84, 0.72, 0.52), vec3(0.93, 0.86, 0.68), 0.5 + 0.5 * sin(v * 3.1));
            bc = mix(bc, vec3(0.70, 0.56, 0.42), smoothstep(0.6, 1.0, sin(v * 1.3)) * 0.4);
            float lam = max(dot(n, L), 0.0);
            vec3 pcol = bc * (0.12 + 0.80 * lam);
            col = mix(col, pcol, smoothstep(1.0, 0.985, q) * sa);
        }
        if (rp.y <= 0.0) col = mix(col, rc * 0.92, ring * 0.80 * sa);
    }

    // the Moon, passing on the right; it breathes a little with the beat
    float ma = san(uM.w, 0.0, 1.0, 0.0);
    if (ma > 0.001) {
        float q;
        vec3 n = sphN(w, uM.xy, max(uM.z, 1e-3), q);
        float halo = exp(-max(sqrt(q) - 1.0, 0.0) * max(uM.z, 1e-3) * 18.0);
        col += vec3(0.55, 0.58, 0.70) * halo * (0.05 + 0.06 * kick) * ma;
        if (q < 1.0) {
            float mar = smoothstep(0.45, 0.62, fbm3d(n * 1.7 + 2.0));
            vec3 mc = mix(vec3(0.74, 0.72, 0.70), vec3(0.50, 0.50, 0.52), mar);
            mc *= 0.86 + 0.28 * fbm3d(n * 9.0);
            // craters: rims catch the light, floors fall in shadow
            vec2 cp = n.xy * 5.0;
            vec2 ci = floor(cp);
            vec2 cf = fract(cp) - 0.5;
            float ch = hash21(ci + 13.0);
            float cr = 0.18 + 0.20 * ch;
            float cd = length(cf - (vec2(hash21(ci + 2.0), hash21(ci + 5.0)) - 0.5) * 0.4);
            float crater = step(0.55, ch) * smoothstep(cr, cr - 0.04, cd);
            float rim = step(0.55, ch) * smoothstep(0.05, 0.0, abs(cd - cr));
            mc *= 1.0 - 0.18 * crater;
            mc += 0.10 * rim * max(dot(normalize(vec2(L.xy)), normalize(cf + 1e-4)), 0.0);
            float lam = max(dot(n, L), 0.0);
            vec3 mcol = mc * (0.06 + 0.84 * lam) * (0.92 + 0.08 * kick);
            col = mix(col, mcol, smoothstep(1.0, 0.985, q) * ma);
        }
    }

    // the comet crossing: coma, a straight blue ion tail and a curved dust tail
    float ka = san(uK.z, 0.0, 1.0, 0.0);
    if (ka > 0.001) {
        vec2 rel = w - uK.xy;
        vec2 td = normalize(vec2(0.92, 0.26));
        float al = dot(rel, td);
        float pe = dot(rel, vec2(-td.y, td.x));
        if (al > -0.05) {
            float wi = 0.006 + max(al, 0.0) * 0.09;
            float ion = exp(-pe * pe / (wi * wi)) * exp(-max(al, 0.0) * 1.6)
                        * (0.65 + 0.35 * fbm(vec2(al * 9.0 - t * 0.6, pe / wi * 2.0)));
            float pe2 = pe + al * al * 0.35;
            float wi2 = 0.010 + max(al, 0.0) * 0.16;
            float dst = exp(-pe2 * pe2 / (wi2 * wi2)) * exp(-max(al, 0.0) * 2.2);
            col += (vec3(0.62, 0.82, 0.95) * ion * 0.55 + vec3(0.95, 0.84, 0.66) * dst * 0.35)
                   * step(0.0, al) * ka;
        }
        float dh = length(rel);
        col += vec3(0.90, 0.95, 1.0) * (exp(-dh * 55.0) * 0.8 + exp(-dh * 16.0) * 0.18) * ka;
    }

    // the Earth: its limb below as he leaves, the blue marble growing as he returns
    float ea = san(uE.w, 0.0, 1.0, 0.0);
    if (ea > 0.001) {
        float r = max(uE.z, 1e-3);
        float q;
        vec3 n = sphN(w, uE.xy, r, q);
        float dist = (sqrt(q) - 1.0) * r;
        vec3 atmo = vec3(0.55, 0.72, 0.95);
        col += atmo * exp(-max(dist, 0.0) * (22.0 / max(r, 0.3))) * 0.30 * ea
               * smoothstep(-0.2, 0.4, dot(normalize(w - uE.xy), L.xy));
        if (q < 1.0) {
            float er = uF.x;
            vec3 m = vec3(cos(er) * n.x + sin(er) * n.z, n.y, -sin(er) * n.x + cos(er) * n.z);
            // seen close, the Earth is a big sphere and only a sliver of it is on
            // screen, so its detail has to scale up with its size
            float fq = 2.3 * clamp(r * 1.2, 1.0, 3.5);
            float ld = fbm3d(m * fq + 4.0);
            vec3 surf = mix(vec3(0.22, 0.36, 0.52), vec3(0.36, 0.46, 0.30), smoothstep(0.50, 0.53, ld));
            surf = mix(surf, vec3(0.56, 0.50, 0.38), smoothstep(0.60, 0.72, ld));
            float cl = smoothstep(0.52, 0.74, fbm3d(m * fq * 1.6 + vec3(t * 0.01, 0.0, 0.0) + 11.0));
            surf = mix(surf, vec3(0.90, 0.91, 0.94), cl * 0.85);
            surf = mix(surf, vec3(0.90, 0.93, 0.97), smoothstep(0.84, 0.92, abs(m.y)));
            float lam = dot(n, L);
            float day = smoothstep(-0.10, 0.25, lam);
            vec3 ecol = surf * (0.08 + 0.80 * max(lam, 0.0));
            // the lights of towns on the night side: a few, warm, sparse
            float city = step(0.53, ld) * step(0.988, hash31(floor(m * 80.0))) * (1.0 - day) * (1.0 - cl);
            ecol += vec3(1.0, 0.76, 0.42) * city * 0.55;
            ecol = mix(ecol, atmo * (0.2 + 0.6 * day), pow(1.0 - n.z, 3.0) * 0.55);
            col = mix(col, ecol, smoothstep(1.0, 0.994, q) * ea);
        }
    }
    return col;
}

// the river seen from behind him: it runs away from us to the vanishing point
float riverHW(float y) { return 0.045 + max(FARY - y, 0.0) * 1.15; }
float riverCX(float y) { float d = max(FARY - y, 0.0); return VP.x + 0.06 * sin(d * 6.0) * d; }

void main() {
    vec2 uv = vUV.st;
    vec2 w = vec2((uv.x - 0.5) * OW + CAMX, (uv.y - 0.5) * OH + CAMY);
    float t     = san(uA.x, 0.0, 1.0e6, 0.0);
    float alt   = san(uA.y, 0.0, 10.0, 0.0);
    float sf    = san(uA.z, 0.0, 1.0, 0.0);
    float tr    = san(uA.w, 0.0, 1.0e5, 0.0);
    float bass  = san(uB.x, 0.0, 2.0, 0.0);
    float high  = san(uB.y, 0.0, 2.0, 0.0);
    float kick  = pow(san(uB.z, 0.0, 1.0, 0.0), 0.7);
    float fade  = san(uB.w, 0.0, 1.0, 1.0);
    float vign  = san(uC.x, 0.0, 2.0, 0.70);
    float brite = san(uC.y, 0.2, 4.0, 1.0);
    float glowa = san(uC.z, 0.0, 4.0, 0.4);
    float labf  = san(uC.w, 0.0, 1.0, 0.0);
    float gsun  = san(uD.x, -1.0, 1.0, -0.5);
    float bulb  = san(uD.y, 0.0, 1.0, 0.0);
    float reent = san(uD.z, 0.0, 1.0, 0.0);
    float speed = san(uD.w, 0.0, 3.0, 0.0);
    float gsunx = VP.x + 0.25;

    vec3 spc = spaceColour(w, t, tr, high, kick, speed);
    gSpace = spc;
    gSF = sf;
    gAlt = alt;

    // --- the world below, scrolled down by the altitude ---------------------------
    vec3 col;
    vec2 wg = w + vec2(0.0, alt);
    vec3 amb = ambient(gsun);
    if (sf >= 0.999) {
        col = spc;
    } else if (wg.y >= FARY - 0.004) {
        col = above(wg, gsun, gsunx, t * 0.004, t, high, 0.0, false, kick);
    } else {
        float hw = riverHW(wg.y);
        float cx = riverCX(wg.y);
        float e = abs(wg.x - cx) - hw;
        if (e < 0.0) {
            // --- the river (homestead's water, turned to face up-river) -----------
            float dz = FARY - wg.y;
            float s = 0.10 + dz * 2.6;
            vec2 q = vec2((wg.x - cx) / s, 1.0 / s);
            float n1 = fbm3(vec2(q.x * 2.0, q.y * 3.0 - tr * 2.0 - t * 0.04));
            float n2 = fbm3(vec2(q.x * 5.0 + 3.1, q.y * 7.0 + 1.7 - t * 0.08));
            float rip = (n1 - 0.5) + 0.6 * (n2 - 0.5);
            vec2 rw = vec2(wg.x + rip * 0.020 * s, FARY + dz * 0.92 + rip * 0.030 * s);
            vec3 refl = above(rw, gsun, gsunx, t * 0.004, t, high, 0.0, true, kick);
            vec3 deep = vec3(0.050, 0.115, 0.105) * amb;
            float fres = mix(0.90, 0.50, smoothstep(0.0, 0.50, dz));
            col = mix(deep, refl * 0.90, fres);
            float g = pow(clamp((n2 - 0.52) / 0.30, 0.0, 1.0), 5.0);
            float sunvis = smoothstep(-0.10, 0.03, gsun);
            col += sunColor(gsun) * g * exp(-abs(wg.x - gsunx) * (3.0 + 4.0 * dz)) * sunvis * (0.5 + 0.6 * high);
            float mg = pow(clamp((n2 - 0.55) / 0.3, 0.0, 1.0), 6.0) * exp(-abs(wg.x - MOONP.x) * 5.0)
                       * smoothstep(0.02, -0.35, gsun);
            col += vec3(0.55, 0.60, 0.75) * mg * 0.8;
            col *= 1.0 - 0.45 * exp(e * 40.0);
            col += vec3(0.75, 0.80, 0.82) * amb * exp(e * 300.0) * 0.25;
            // the house's bulb, on the water
            col += WARM * bulb * 0.10 * exp(-length((wg - vec2(BULB.x + 0.25, BULB.y - 0.12)) * vec2(1.4, 4.0)) * 3.0);
        } else {
            // --- the banks ---------------------------------------------------------
            float dz = FARY - wg.y;
            float s = 0.10 + dz * 2.6;
            vec2 q = vec2(wg.x / s, 1.0 / s);
            float n = fbm(q * vec2(3.0, 4.0));
            vec3 grass = mix(vec3(0.20, 0.26, 0.10), vec3(0.36, 0.40, 0.17), n);
            grass *= 0.85 + 0.25 * vnoise(vec2(q.x * 60.0, q.y * 30.0));
            float lip = smoothstep(0.022 * s * 3.0, 0.0, e);
            vec3 alb = mix(grass, vec3(0.30, 0.21, 0.13) * (0.8 + 0.3 * fbm3(q * 20.0)), lip);
            col = alb * amb;
            vec2 pd = (wg - vec2(BULB.x, BULB.y - 0.03)) * vec2(1.0, 2.6);
            col += alb * WARM * bulb * 0.9 / (1.0 + dot(pd, pd) * 70.0);
        }
    }

    // --- the cloud sea: overhead as he leaves, a floor beneath him, and back ------
    if (alt > 0.10 && alt < 3.2) {
        float drift = tr * 0.6 + t * 0.004;
        float top = 1.00 + 0.07 * fbm(vec2(wg.x * 1.1 + drift, 1.3)) + 0.03 * fbm(vec2(wg.x * 4.0 - drift, 7.0));
        float below = top - wg.y;
        if (below > -0.04 && below < 0.75) {
            float dens = smoothstep(-0.04, 0.05, below) * smoothstep(0.75, 0.40, below);
            float tex = fbm(vec2(wg.x * 3.0 + drift * 1.5, wg.y * 7.0));
            float holes = fbm(vec2(wg.x * 1.8 - drift, wg.y * 3.5 + 2.0));
            dens *= smoothstep(0.34, 0.56, holes + 0.25 * smoothstep(0.25, 0.0, below));
            float dawn = smoothstep(-0.30, 0.05, gsun);
            vec3 ctop = mix(vec3(0.40, 0.44, 0.60), vec3(0.95, 0.78, 0.72), dawn) * 0.78;
            vec3 cbot = mix(vec3(0.12, 0.13, 0.22), vec3(0.42, 0.36, 0.48), dawn);
            vec3 cc = mix(cbot, ctop, smoothstep(0.28, 0.0, below) * 0.75 + 0.25 * tex);
            col = mix(col, cc, dens * (0.75 + 0.25 * tex));
        }
    }

    // --- re-entry: the frame warms and burns at the edges ------------------------
    if (reent > 0.001) {
        vec2 dd = (uv - 0.5) * vec2(1.777, 1.0);
        float edge = dot(dd, dd);
        col += vec3(1.0, 0.50, 0.22) * reent * (0.06 + 0.40 * edge) * (0.85 + 0.15 * sin(t * 30.0));
    }

    // --- the cels, and their glow ---------------------------------------------------
    vec4 li = texture(sTD2DInputs[0], uv);
    vec4 gl = texture(sTD2DInputs[1], uv);
    li = vec4(san(li.r, 0.0, 8.0, 0.0), san(li.g, 0.0, 8.0, 0.0),
              san(li.b, 0.0, 8.0, 0.0), san(li.a, 0.0, 1.0, 0.0));
    gl = vec4(san(gl.r, 0.0, 8.0, 0.0), san(gl.g, 0.0, 8.0, 0.0),
              san(gl.b, 0.0, 8.0, 0.0), 1.0);
    col = col * (1.0 - li.a) + li.rgb;
    col += gl.rgb * glowa;
    vec4 lb = texture(sTD2DInputs[2], uv);
    col = mix(col, lb.rgb, clamp(lb.a, 0.0, 1.0) * labf);

    // --- grade (homestead's): luminance shoulder, split-tone, vignette, grain ------
    col *= brite;
    float lum = dot(col, vec3(0.2126, 0.7152, 0.0722));
    col += (vec3(-0.010, 0.000, 0.018) * (1.0 - smoothstep(0.0, 0.35, lum))
            + vec3(0.012, 0.004, -0.010) * smoothstep(0.45, 1.0, lum));
    float l2 = max(dot(col, vec3(0.2126, 0.7152, 0.0722)), 1e-4);
    float lm = mix(l2, 1.0 - exp(-l2 * 1.3), smoothstep(0.55, 1.3, l2));
    col = col * (lm / l2);
    col = mix(col, vec3(lm), smoothstep(1.0, 1.8, l2) * 0.35);
    col += (hash21(uv * vec2(1920.0, 1080.0) + fract(t)) - 0.5) * 0.012;
    vec2 dv = (uv - 0.5) * vec2(1.777, 1.0);
    col *= 1.0 - vign * 0.55 * dot(dv, dv);
    col *= fade;
    vec3 outc = max(col, vec3(0.0));
    if (!(outc.r >= 0.0) || !(outc.g >= 0.0) || !(outc.b >= 0.0)) {
        outc = vec3(0.02, 0.02, 0.04) * fade;
    }
    fragColor = TDOutputSwizzle(vec4(outc, 1.0));
}
''')
world.par.pixeldat = world_pix.name
W(render_cels, world, 0)
W(glow_blur, world, 1)

_U = [('uA', ('Showt', 'Alt', 'Sf', 'Travel')),
      ('uB', (D('bass'), D('high'), D('kickenv'), 'Fade')),
      ('uC', ('Vignette', 'Brightness', None, 'Labelfade')),
      ('uD', ('Gsun', 'Bulb', 'Reentry', 'Warp')),
      ('uE', ('Ex', 'Ey', 'Er', 'Ea')),
      ('uF', ('Erot', 'Grot', 'Na', 'Nz')),
      ('uM', ('Mx', 'My', 'Mr', 'Ma')),
      ('uS', ('Sx', 'Sy', 'Sr', 'Sa')),
      ('uK', ('Kx', 'Ky', 'Ka', None)),
      ('uG', ('Gx', 'Gy', 'Gr', 'Ga')),
      ('uP', ('Px', 'Py', 'Pa', None)),
      ('uL', ('Lx', 'Ly', 'Lz', None))]
world.par.vec = len(_U)
for i, (nm, comps) in enumerate(_U):
    setattr(world.par, 'vec%dname' % i, nm)
    for c, src in zip('xyzw', comps):
        p = getattr(world.par, 'vec%dvalue%s' % (i, c))
        if src is None:
            p.val = 0.0
        elif src.startswith('('):
            p.expr = src
        else:
            p.expr = 'parent().par.%s' % src
# glow is what EMITS: the lantern, the dust, the stars, the plasma
world.par.vec2valuez.expr = 'parent().par.Glow * 0.55'

label = C(textTOP, 'label', 2260, 420)
res(label, OUTW, OUTH, 'rgba8fixed')
soft(label, alignx='left', aligny='bottom', fontsizex=22, font='Georgia',
     bgalpha=0.0, fontcolorr=0.98, fontcolorg=0.94, fontcolorb=0.84,
     fontcolora=1.0, wordwrap=False, trackingx=0.10,
     positionx=0.048, positiony=0.070, positionunit='fraction')
label.par.text.expr = 'parent().par.Scaletxt.eval()'
W(label, world, 2)

final_out = C(nullTOP, 'final_out', 2580, 200)
W(world, final_out)
out1 = C(outTOP, 'out1', 2740, 200)
W(final_out, out1)

pout = proj.create(outTOP, SCENE + '_out')
pout.nodeX, pout.nodeY = 400, -2600
s.outputConnectors[0].connect(pout.inputConnectors[0])


# ---------------------------------------------------------------------------
# PADS AND KEYS
# ---------------------------------------------------------------------------
PEXEC_BODY = '''# A chapter is a SEEK; the pads push a verb into the director's queue.


def _seek(comp, seconds):
    d = comp.op('director')
    mus = float(d['musical'][0]) if d is not None and d.numChans else 0.0
    comp.par.Timeoffset = mus - max(0.02, seconds)


def _push(comp, what):
    q = comp.fetch('pending', None)
    if not isinstance(q, list):
        q = []
    q.append(what)
    comp.store('pending', q)


def onPulse(par):
    comp = par.owner
    n = par.name
    slen = max(1.0, float(comp.par.Storylen.eval()))
    names = [c[0] for c in CHECKPOINTS]
    if n == 'Star':
        _push(comp, 'gust')
    elif n == 'Reseed':
        _push(comp, 'reseed')
    elif n == 'Restart':
        _seek(comp, 0.0)
    elif n == 'Nextcp':
        i = int(round(float(comp.par.Chapter.eval())))
        _seek(comp, CHECKPOINTS[min(i + 1, len(CHECKPOINTS) - 1)][2] * slen)
    elif n == 'Prevcp':
        i = int(round(float(comp.par.Chapter.eval())))
        _seek(comp, CHECKPOINTS[max(i - 1, 0)][2] * slen)
    elif n.startswith('Go'):
        want = n[2:].lower()
        if want in names:
            _seek(comp, CHECKPOINTS[names.index(want)][2] * slen)
    return
'''

pexec = C(parameterexecuteDAT, 'checkpoint_exec', 2100, 1000)
pexec.text = hdr(CHECKPOINTS=CHECKPOINTS) + PEXEC_BODY
pexec.par.op = '..'
soft(pexec, pars='Star Reseed Restart Nextcp Prevcp '
     + ' '.join('Go' + cp[0] for cp in CHECKPOINTS),
     valuechange=False, onpulse=True)

KEY_BODY = '''# 1-9 walk the voyage to a chapter; 0 starts it again.
#   s  SHOOTING STAR
#   n  RESEED — new grass and trees on the bank


def onKey(dat, keyInfo):
    if not keyInfo.state:
        return
    comp = dat.parent()
    k = keyInfo.key
    if k in '123456789':
        i = int(k) - 1
        if i < len(CHECKPOINTS):
            getattr(comp.par, 'Go' + CHECKPOINTS[i][0]).pulse()
    elif k == '0':
        comp.par.Restart.pulse()
    elif k == 's':
        comp.par.Star.pulse()
    elif k == 'n':
        comp.par.Reseed.pulse()
    return


def onShortcut(dat, shortcutName, time):
    return
'''

keyin = C(keyboardinDAT, 'key_pad', 1780, 700)
keyin.par.keys = '1 2 3 4 5 6 7 8 9 0 s n'
kcb = keyin.par.callbacks.eval()
if kcb is None:
    kcb = C(textDAT, 'key_pad_callbacks', 1780, 620)
    keyin.par.callbacks = kcb.name
kcb.nodeX, kcb.nodeY = 1780, 620
kcb.text = hdr(CHECKPOINTS=CHECKPOINTS) + KEY_BODY

s.par.display = True
s.par.opviewer = final_out.name
s.store('pending', [])

timer.par.initialize.pulse()
timer.par.start.pulse()
director.cook(force=True)
engine.cook(force=True)

if world.warnings():
    print('  [SHADER] %s' % world.warnings())
print('built %s' % s.path)
print('  antialias -> %r | blend %r over %r' % (AA, SRCB, DSTB))
print('  %s' % eng_src.module._S['S']['census'])
print('  keys: 1-9 chapters | 0 restart | s shooting star | n reseed')
