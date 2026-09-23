# Homestead — a poor man walks out of the forest with everything he owns on a stick,
# and by the next morning there is a house on the riverbank that feeds and lights
# itself.
#
# One fixed camera looking across a river at a wild far bank. A day passes over the
# story: he arrives at dawn, clears the ground in the morning, raises bamboo stilts
# against the flood, walls it in bamboo and mud at noon, gets the thatch on just
# before an afternoon shower, builds a water wheel on the bank, plants seeds in the
# golden hour, and at dusk throws a switch and the wheel lights a bulb under his eave.
# The last chapter is the next dawn: smoke from the chimney, the garden grown, and
# the deer that bolted when he arrived come back to drink.
#
# CARTOON AND REALISM ARE SPLIT BY WHAT THEY ARE, NOT MIXED BY A FILTER. The WORLD —
# sky, sun, clouds, mountains, the far jungle, the river and the land — is painted
# in one shader with a real day/night cycle, aerial perspective, reflections and sun
# glitter. Everything that LIVES or is BUILT — the man, the house, the wheel, the
# animals, the grass — is a flat cel with a hard shadow side and a bold outline. The
# two are tied together by light: the cels are lit by the same sky the shader
# paints, their lit side follows the sun across the day, they throw contact shadows
# onto the painted ground, and at night the bulb warms both.
#
# THE BUILD IS A FUNCTION OF THE STORY, NOT STATE. Every part of the house has a
# stage and a threshold, and whether it exists is decided from the playhead alone,
# so a chapter jump lands on exactly the right half-built house. Only things that
# are genuinely continuous — where he is standing, the angle of the wheel, the river's
# phase, particles — carry state.
#
# AUDIO IS IN THE PACE, NOT THE BRIGHTNESS. Tempo is the story clock. Energy is how
# fast the wheel turns, the river runs and the clouds drift — all integrated, so the
# music changes their SPEED and never makes anything jump. His hammer lands on the
# kick. Bass sways the grass; highs are fireflies, glitter and stars; a drop is a
# gust through the grass that puts the birds up out of the tree.
#
# Idempotent: destroys and recreates /project1/homestead and its project-level Out
# TOP, and touches nothing else. No media files.
#     code = open('scenes/homestead/build.py', encoding='utf-8').read()
#     g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)

import math
import os

SCENE = 'homestead'
OUTW, OUTH = 1280, 720
ASPECT = OUTW / OUTH
# The camera is zoomed in (2.0 -> 1.6 world units across) and framed low and to the
# left, so the man and his house fill more of the frame; the tree is cut by the left
# edge and the sky is what is left over the jungle.
ORTHOW = 1.60
ORTHOH = ORTHOW / ASPECT
CAMX, CAMY = -0.080, -0.070
CLOCKLEN = 60.0

STORYDEF = 300.0
MAXSEG = 12000           # instance pool; fixed, never resized

# --- the geography, shared by the shader and the engine so they cannot disagree ---
FARY = 0.020             # the far bank: where the water meets the jungle
SHOREY = -0.125          # the back edge of the near bank
SHOREX = 0.160           # where the near bank turns and falls into the river
BANKK = 0.600            # how far right the bank reaches at the bottom of frame
BANKH = 0.440
GYH = -0.265             # where the house stands
FLOORY = -0.195          # its raised floor
WALLTOP = 0.012
HX0, HX1 = -0.640, -0.205
MANGY = -0.330           # where he normally stands
MANSC = 0.255            # how tall he is
WX, WY, WR = 0.530, -0.205, 0.092     # the water wheel, out past the bank edge
WWL = -0.270             # the wheel's own waterline
BULB = (-0.188, -0.030)  # the bulb under the eave

# Nine chapters. A chapter is a SEEK: jump to it and the story plays on from there.
CHECKPOINTS = [
    ('arrive', ' 1 - Nothing But the River',   0.000),
    ('clear',  ' 2 - Clearing the Ground',     0.100),
    ('stilts', ' 3 - Stilts Against the Flood', 0.205),
    ('walls',  ' 4 - Bamboo and Mud',          0.325),
    ('roof',   ' 5 - Thatch Before the Rain',  0.445),
    ('wheel',  ' 6 - The Water Wheel',         0.565),
    ('seeds',  ' 7 - Seeds',                   0.675),
    ('light',  ' 8 - First Light',             0.790),
    ('home',   ' 9 - Home',                    0.905),
]

# The six building stages, as story fractions. Each stage's progress is
# (f - f0) / (f1 - f0), clamped, and every part knows which stage it belongs to.
STAGES = (
    ('clear',  0.110, 0.195),
    ('stilts', 0.215, 0.315),
    ('walls',  0.335, 0.435),
    ('roof',   0.455, 0.545),
    ('wheel',  0.575, 0.665),
    ('seeds',  0.685, 0.775),
)

# THE DAY. Sun height (-1 deep night .. 1 overhead) and sun x across the story. He
# arrives at dawn; it is noon while the walls go up; the golden hour is the garden;
# dusk is the switch; the last chapter is the next dawn. The sun goes back east
# while it is below the horizon, where nobody can see it travel.
SUN_F = (0.00, 0.05, 0.10, 0.20, 0.33, 0.45, 0.52, 0.57, 0.66, 0.74, 0.79, 0.83,
         0.87, 0.905, 0.95, 0.98, 1.00)
SUN_H = (0.00, 0.10, 0.25, 0.55, 0.90, 0.80, 0.60, 0.55, 0.35, 0.16, 0.04, -0.15,
         -0.45, -0.60, -0.25, 0.02, 0.10)
SUNX_F = (0.00, 0.81, 0.86, 0.87, 1.00)
SUNX_X = (-0.42, 0.66, 1.00, -1.00, -0.42)
# One afternoon shower, arriving just as the last of the thatch goes on.
RAIN_F = (0.00, 0.500, 0.525, 0.545, 0.565, 0.585, 0.605, 1.00)
RAIN_A = (0.00, 0.000, 0.550, 0.900, 0.700, 0.250, 0.000, 0.00)

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
    DEER=(0.560, 0.360, 0.200), DEERLT=(0.720, 0.500, 0.300),
    HERON=(0.580, 0.620, 0.690), HERONLT=(0.800, 0.830, 0.880),
    FOX=(0.820, 0.400, 0.130), FOXLT=(0.950, 0.560, 0.240),
    WARM=(1.000, 0.640, 0.300),
    FIREFLY=(0.820, 1.000, 0.420),
    WATER=(0.300, 0.420, 0.460),
)

proj = op('/project1')
for stale in (SCENE, SCENE + '_out'):
    o = proj.op(stale)
    if o:
        o.destroy()

s = proj.create(containerCOMP, SCENE)
s.nodeX, s.nodeY = 0, -2000
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


# ---------------------------------------------------------------------------
# PERFORMANCE SURFACE
# ---------------------------------------------------------------------------
pg = s.appendCustomPage('Homestead')
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
    ('Paceaudio',  'Energy Drives Pace',  1.0, 0.0, 3.0),
    ('Sway',       'Grass Sway',          1.0, 0.0, 3.0),
    ('Rain',       'Rain',                1.0, 0.0, 2.0),
    ('Brightness', 'Brightness',          1.0, 0.2, 2.0),
    ('Ink',        'Brightness of Art',   1.0, 0.0, 2.0),
    ('Glow',       'Glow',                1.0, 0.0, 3.0),
    ('Label',      'Chapter Readout',     1.0, 0.0, 2.0),
    ('Vignette',   'Vignette',            0.65, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

for _mn, _ml, _lo, _hi in (('Bpm', 'Detected BPM', 0.0, 200.0),
                           ('Showt', 'Story Time (s)', 0.0, 2400.0),
                           ('Chapter', 'Chapter', 0.0, float(len(CHECKPOINTS))),
                           ('Sunh', 'Sun Height', -1.0, 1.0),
                           ('Sunx', 'Sun X', -1.5, 1.5),
                           ('Rainnow', 'Rain Level', 0.0, 1.0),
                           ('Flowph', 'River Phase', 0.0, 1e6),
                           ('Cloudph', 'Cloud Phase', 0.0, 1e6),
                           ('Wheelspd', 'Wheel Speed (rad/s)', 0.0, 6.0),
                           ('Bulb', 'Bulb', 0.0, 1.0),
                           ('Clearp', 'Ground Cleared', 0.0, 1.0),
                           ('Gustnow', 'Gust', 0.0, 1.0),
                           ('Fade', 'Loop Fade', 0.0, 1.0),
                           ('Loops', 'Loops Completed', 0.0, 1e6),
                           ('Rejects', 'Bad Quads Dropped', 0.0, 1e6),
                           ('Segs', 'Quads Drawn', 0.0, float(MAXSEG)),
                           ('Labelfade', 'Readout Fade', 0.0, 1.0),
                           ('Bassm', 'Bass Level', 0.0, 1.0),
                           ('Highm', 'High Level', 0.0, 1.0),
                           ('Energym', 'Energy Level', 0.0, 1.0)):
    pg.appendFloat(_mn, label=_ml)
    _p = getattr(s.par, _mn)
    _p.normMin, _p.normMax = _lo, _hi
    _p.readOnly = True
s.par.Sunh.val = 0.0
s.par.Sunx.val = -0.9

pg.appendToggle('Loop', label='Loop the Story')
s.par.Loop.default = True
s.par.Loop.val = True
pg.appendStr('Scaletxt', label='Chapter Text')
s.par.Scaletxt.readOnly = True
s.par.Scaletxt.val = ''

pg.appendPulse('Gust', label='G - GUST (wind, and the birds go up)')
pg.appendPulse('Fish', label='F - FISH (one jumps)')
pg.appendPulse('Reseed', label='N - RESEED (new wilderness)')
pg.appendPulse('Restart', label='0 - RESTART')
pg.appendPulse('Nextcp', label='next chapter')
pg.appendPulse('Prevcp', label='previous chapter')
for cp, label, _f in CHECKPOINTS:
    pg.appendPulse('Go' + cp, label=label)

# ---------------------------------------------------------------------------
# AUDIO FRONT END — the same chain every scene in this repo carries (see monsoon).
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


# ---------------------------------------------------------------------------
# DIRECTOR — musical time, the seekable playhead, envelopes, event counters
# ---------------------------------------------------------------------------
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


def D(ch):
    return "(op('director')['%s'] or 0)" % ch


# ---------------------------------------------------------------------------
# THE ENGINE — the man, the house, the wheel, the garden, and the wild
# ---------------------------------------------------------------------------
ENGINE_BODY = r'''# Everything that lives or is built is emitted from here as ONE primitive: a
# rotated, filled quad, instanced from a unit square with a per-instance width (see
# monsoon). An outline is a quad 3 px wide; a limb is one fat quad; a flat shape is
# a stack of horizontal slabs; a grass blade is a thin quad.
#
# Each emitted row is (x0, y0, x1, y1, r, g, b, a, z, fl, w, wl):
#   fl  1 = emissive (the bulb, the window, fireflies, eyes) — not lit by the sky
#   wl  the row's own waterline, or 99 for none. Anything above its waterline is
#       mirrored into the river; anything below it is dimmed and tinted — one rule,
#       applied at the end to every row, and nothing that draws the heron or the
#       wheel needs to know that water exists.
#
# The painted world is lit in the shader; the cels are lit HERE, by the same sky, at
# the end of the frame: every non-emissive row is multiplied by the ambient colour of
# the current time of day, plus the bulb's warm falloff at night.
import math
import random
import numpy as np

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


# --- the man --------------------------------------------------------------------
# Thin, barefoot, a patched shirt with a torn hem, a dhoti gone grey with washing, a
# faded red cloth tied round his head, a beard nobody has trimmed. Proportions in
# units of his own height; `face` mirrors him. He is lit from the sun's side, so his
# lit edge swaps over as the day goes past.
def _man(out, x, gy, sc, face, pose, ph, walk, strike, t, sun, tool, nod, sip,
         seat=0.27, reach=0.0, zover=None):
    def P(u, v):
        return (x + u * sc * face, gy + v * sc)

    # on the platform he stands IN FRONT of the wall he is thatching over, although
    # by his feet he is further back than it — depth from feet alone hid him
    z0 = _zd(gy) if zover is None else zover
    lean = {'hammer': 0.10, 'swing': 0.34, 'plant': 0.58, 'sit': 0.04,
            'look': -0.04, 'carry': 0.08, 'switch': 0.18}.get(pose, 0.05)
    lean += 0.05 * walk

    # --- legs ------------------------------------------------------------------
    if pose == 'sit':
        hip = (0.0, seat)
        feet = [(0.21, 0.0), (0.28, 0.0)]
    else:
        crouch = 0.55 if pose == 'plant' else 0.0
        bob = 0.014 * abs(math.sin(TAU * ph)) * walk
        hip = (0.0, 0.47 - 0.17 * crouch + bob)
        feet = []
        for i in (0, 1):
            p = ph + 0.5 * i
            stand = (0.06 if i == 0 else -0.05) + crouch * (0.12 if i == 0 else -0.10)
            fu = 0.15 * math.sin(TAU * p) * walk + stand * (1.0 - walk)
            fv = 0.045 * max(0.0, math.cos(TAU * p)) * walk
            feet.append((fu, fv))
    for i in (1, 0):                      # back leg first, then the front one
        dark = 0.78 if i == 1 else 1.0
        zz = z0 + (0.0 if i == 0 else -0.006)
        fu, fv = feet[i]
        ku, kv, fu, fv = _knee(hip[0], hip[1], fu, fv + 0.035, 0.235, 0.215, 1.0)
        H, K, F = P(*hip), P(ku, kv), P(fu, fv)
        _limb(out, K[0], K[1], F[0], F[1], 0.058 * sc, _mul(SKIN, dark),
              _mul(SKINLT, dark), 1.0, zz, sun)
        toe = P(fu + 0.075, fv - 0.030)
        _limb(out, F[0], F[1], toe[0], toe[1], 0.036 * sc, _mul(SKIN, dark), None,
              1.0, zz + 0.0002, sun)
        _limb(out, H[0], H[1], K[0], K[1], 0.118 * sc, _mul(DHOTI, dark),
              _mul(DHOTILT, dark), 1.0, zz + 0.0006, sun)
        _joint(out, K[0], K[1], 0.036 * sc, _mul(DHOTI, dark), 1.0, zz + 0.0007)

    # --- torso -----------------------------------------------------------------
    au, av = math.sin(lean), math.cos(lean)
    nu, nv = av, -au
    shl = (hip[0] + au * 0.29, hip[1] + av * 0.29)
    tor = [P(hip[0] - nu * 0.074, hip[1] - nv * 0.074),
           P(hip[0] + nu * 0.080, hip[1] + nv * 0.080),
           P(shl[0] + nu * 0.078, shl[1] + nv * 0.078),
           P(shl[0] - nu * 0.084, shl[1] - nv * 0.084)]
    zt = z0 + 0.002
    _shape(out, tor, SHIRT, 1.0, zt, SHIRTLT, sun)
    # a torn hem: three rags hanging off the bottom of the shirt
    for k, du in enumerate((-0.045, 0.0, 0.045)):
        hu, hv = hip[0] + nu * du, hip[1] + nv * du
        _fill(out, [P(hu - nu * 0.022, hv - nv * 0.022),
                    P(hu + nu * 0.022, hv + nv * 0.022),
                    P(hu + au * -0.045 + nu * (0.004 * k), hv + av * -0.045)],
              SHIRT, 1.0, zt + 0.0003, 2)
    # patches, sewn on in whatever cloth there was
    pu, pv = hip[0] + au * 0.17 + nu * 0.010, hip[1] + av * 0.17 + nv * 0.010
    _shape(out, [P(pu - 0.030, pv - 0.028), P(pu + 0.028, pv - 0.030),
                 P(pu + 0.030, pv + 0.026), P(pu - 0.026, pv + 0.030)],
           PATCH, 1.0, zt + 0.0006, None, sun, lw=LWO * 0.6)
    qu, qv = hip[0] + au * 0.06 - nu * 0.035, hip[1] + av * 0.06 - nv * 0.035
    _shape(out, [P(qu - 0.018, qv - 0.020), P(qu + 0.020, qv - 0.018),
                 P(qu + 0.018, qv + 0.018)], PATCH2, 1.0, zt + 0.0006, None, sun,
           lw=LWO * 0.6)
    # the waist-knot of the dhoti
    _shape(out, _ell(P(*hip)[0], P(*hip)[1], 0.070 * sc, 0.040 * sc, 10),
           DHOTI, 1.0, zt + 0.0008, DHOTILT, sun)

    # --- head ------------------------------------------------------------------
    hc = (shl[0] + au * 0.115 + nu * 0.022, shl[1] + av * 0.115 + nv * 0.022 - nod)

    def Q(du, dv):
        return P(hc[0] + du * HS, hc[1] + dv * HS)

    N0, N1 = P(shl[0] + au * 0.01, shl[1] + av * 0.01), P(*hc)
    zh = z0 + 0.004
    _limb(out, N0[0], N0[1], N1[0], N1[1], 0.050 * sc, SKIN, None, 1.0, zh - 0.0015,
          sun)
    HC = P(*hc)
    _shape(out, _ell(HC[0], HC[1], 0.064 * HS * sc, 0.071 * HS * sc, 14), SKIN, 1.0, zh,
           SKINLT, sun)
    _fill(out, [Q(+0.070, +0.004), Q(+0.088, -0.018),
                Q(+0.062, -0.022)], SKIN, 1.0, zh + 0.0005, 2)
    # scruffy beard, jaw to chin
    _shape(out, [Q(-0.012, -0.012), Q(+0.068, -0.030),
                 Q(+0.050, -0.090), Q(+0.004, -0.098),
                 Q(-0.034, -0.052)], BEARD, 1.0, zh + 0.0010, None,
           sun, lw=LWO * 0.5)
    # the eye, and a brow that has seen weather
    e = Q(+0.036, +0.014)
    _rect(out, e[0], e[1], 0.014 * sc, 0.020 * sc, INK, 1.0, zh + 0.0016)
    b0, b1 = Q(+0.020, +0.036), Q(+0.058, +0.030)
    _seg(out, b0[0], b0[1], b1[0], b1[1], INK, 1.0, zh + 0.0016, 0.009 * sc)
    # the head-cloth, knotted at the back with a tail
    _shape(out, [Q(-0.074, +0.004), Q(-0.060, +0.058),
                 Q(+0.004, +0.086), Q(+0.058, +0.064),
                 Q(+0.070, +0.030), Q(+0.002, +0.034)],
           CLOTHR, 1.0, zh + 0.0012, CLOTHRLT, sun)
    k0 = Q(-0.068, +0.030)
    wig = 0.012 * math.sin(t * 3.1)
    _shape(out, [k0, P(hc[0] - 0.128, hc[1] - 0.010 + wig),
                 P(hc[0] - 0.100, hc[1] - 0.034 + wig)], CLOTHR, 1.0, zh + 0.0011,
           None, sun, lw=LWO * 0.7)

    # --- arms ------------------------------------------------------------------
    sw = math.sin(TAU * ph) * walk
    if pose == 'hammer':
        F = (2.75 - 1.85 * strike + reach, 0.55 - 0.40 * strike)
        B = (1.05 + reach * 0.5, 0.55)
    elif pose == 'swing':
        F = (2.20 - 1.95 * strike, 0.25)
        B = (0.55, 1.05)
    elif pose == 'plant':
        F = (0.10 + 0.35 * strike, 0.30)
        B = (0.05, 1.35)
    elif pose == 'sit':
        F = (0.95 + 0.40 * sip, 1.55 + 0.45 * sip)
        B = (0.40, 1.00)
    elif pose == 'look':
        F = (1.90, 2.00)
        B = (-0.10, 0.20)
    elif pose == 'carry':
        F = (0.50, 2.40)
        B = (-0.40 * sw, 0.30)
    elif pose == 'switch':
        F = (1.45, 0.10)
        B = (-0.10, 0.20)
    else:
        F = (0.12 + 0.45 * sw, 0.25 + 0.10 * walk)
        B = (-0.12 - 0.45 * sw, 0.25 + 0.10 * walk)
    hands = []
    for i, (sa, ea) in ((1, B), (0, F)):
        dark = 0.78 if i == 1 else 1.0
        zz = z0 + (0.006 if i == 0 else -0.007)
        S0 = (shl[0] - au * 0.025, shl[1] - av * 0.025)
        d1 = (math.sin(sa + lean), -math.cos(sa + lean))
        el = (S0[0] + d1[0] * 0.165, S0[1] + d1[1] * 0.165)
        d2 = (math.sin(sa + ea + lean), -math.cos(sa + ea + lean))
        hd = (el[0] + d2[0] * 0.155, el[1] + d2[1] * 0.155)
        A0, A1, A2 = P(*S0), P(*el), P(*hd)
        _limb(out, A1[0], A1[1], A2[0], A2[1], 0.052 * sc, _mul(SKIN, dark),
              _mul(SKINLT, dark), 1.0, zz, sun)
        _joint(out, A2[0], A2[1], 0.032 * sc, _mul(SKIN, dark), 1.0, zz + 0.0002)
        # the upper arm: a ragged short sleeve over thin skin
        mid = ((A0[0] + A1[0]) * 0.5, (A0[1] + A1[1]) * 0.5)
        _limb(out, mid[0], mid[1], A1[0], A1[1], 0.054 * sc, _mul(SKIN, dark), None,
              1.0, zz, sun)
        _limb(out, A0[0], A0[1], mid[0], mid[1], 0.074 * sc, _mul(SHIRT, dark),
              _mul(SHIRTLT, dark), 1.0, zz + 0.0003, sun)
        _joint(out, A1[0], A1[1], 0.024 * sc, _mul(SKIN, dark), 1.0, zz + 0.0001)
        hands.append((A2, d2, zz))

    # --- what he is holding ------------------------------------------------------
    (hx, hy), d2, zz = hands[1]
    dx, dy = d2[0] * face, d2[1]
    tip = None
    if tool == 'hammer':
        hx1, hy1 = hx + dx * 0.15 * sc, hy + dy * 0.15 * sc
        _limb(out, hx - dx * 0.02 * sc, hy - dy * 0.02 * sc, hx1, hy1, 0.018 * sc,
              WOOD, WOODLT, 1.0, zz + 0.001, sun)
        px, py = -dy, dx
        _limb(out, hx1 - px * 0.040 * sc, hy1 - py * 0.040 * sc,
              hx1 + px * 0.045 * sc, hy1 + py * 0.045 * sc, 0.034 * sc, IRON, IRONLT,
              1.0, zz + 0.0015, sun)
        tip = (hx1 + px * 0.045 * sc, hy1 + py * 0.045 * sc)
    elif tool == 'machete':
        hx1, hy1 = hx + dx * 0.05 * sc, hy + dy * 0.05 * sc
        _limb(out, hx, hy, hx1, hy1, 0.022 * sc, WOOD, None, 1.0, zz + 0.001, sun)
        hx2, hy2 = hx1 + dx * 0.20 * sc, hy1 + dy * 0.20 * sc
        _limb(out, hx1, hy1, hx2, hy2, 0.030 * sc, IRON, IRONLT, 1.0, zz + 0.0012,
              sun)
        tip = (hx2, hy2)
    elif tool == 'cup':
        _shape(out, [(hx - 0.018 * sc, hy - 0.004), (hx + 0.020 * sc, hy - 0.004),
                     (hx + 0.022 * sc, hy + 0.040 * sc),
                     (hx - 0.020 * sc, hy + 0.040 * sc)], CLAY, 1.0, zz + 0.001,
               CLAYLT, sun, lw=LWO * 0.7)
        tip = (hx, hy + 0.045 * sc)
    elif tool == 'bundle':
        # a stick over his shoulder with everything he owns tied in a cloth
        bx, by = hx - face * 0.42 * sc, hy + 0.05 * sc
        _limb(out, hx + face * 0.06 * sc, hy - 0.01 * sc, bx, by, 0.018 * sc, WOOD,
              None, 1.0, zz - 0.012, sun)
        swing = 0.010 * math.sin(TAU * ph * 2.0) * walk
        bc = (bx + swing, by - 0.075 * sc)
        _shape(out, _ell(bc[0], bc[1], 0.075 * sc, 0.068 * sc, 10), PATCH2, 1.0,
               zz - 0.011, _mix(PATCH2, DHOTILT, 0.35), sun)
        _shape(out, [(bx - 0.018 * sc, by + 0.004), (bx + 0.018 * sc, by + 0.004),
                     (bc[0], bc[1] + 0.04 * sc)], PATCH2, 1.0, zz - 0.0105, None,
               sun, lw=LWO * 0.6)
        _shape(out, _ell(bc[0] - 0.02 * sc, bc[1] - 0.01 * sc, 0.024 * sc,
                         0.022 * sc, 8), PATCH, 1.0, zz - 0.0100, None, sun,
               lw=LWO * 0.5)
    return tip


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


# --- the wild: grass, reeds, wildflowers — generated once, swayed per frame -------
def _gen_grass(rs):
    rows, clr, ph, hgt = [], [], [], []
    tones = ((0.430, 0.470, 0.195), (0.310, 0.400, 0.150), (0.560, 0.540, 0.270),
             (0.250, 0.340, 0.130), (0.470, 0.520, 0.230))
    flw = ((0.95, 0.92, 0.80), (0.98, 0.80, 0.25), (0.72, 0.52, 0.85))
    for k in range(NTUFT):
        by = rs.uniform(-0.555, SHOREY - 0.012)
        xmax = land_edge(by) - 0.018
        bx = rs.uniform(-1.12, xmax)
        if bx > xmax:
            continue
        depth = 0.75 + (SHOREY - by) * 1.35
        # the clearing: everything inside the plot falls, left to right
        inside = (CLR0 - 0.02 < bx < CLR1 + 0.02) and by > -0.56
        u = (bx - CLR0) / (CLR1 - CLR0) if inside else 9.0
        nb = rs.randint(4, 7)
        tone = tones[rs.randint(0, len(tones) - 1)]
        z = _zd(by) + 0.003
        p = rs.uniform(0.0, TAU)
        for j in range(nb):
            h = rs.uniform(0.030, 0.078) * depth * (1.3 if not inside else 1.0)
            ang = rs.uniform(-0.45, 0.45)
            x0 = bx + rs.uniform(-0.010, 0.010) * depth
            col = _mix(tone, tones[(j + k) % len(tones)], 0.3)
            col = _mul(col, rs.uniform(0.82, 1.12))
            rows.append((x0, by, x0 + math.sin(ang) * h, by + math.cos(ang) * h,
                         col[0], col[1], col[2], 1.0, z + j * 1e-5, 0.0,
                         0.0048 * depth, 99.0))
            clr.append(u)
            ph.append(p + j * 0.3)
            hgt.append(h)
        if rs.random() < 0.22:
            fc = flw[rs.randint(0, 2)]
            h = rs.uniform(0.05, 0.085) * depth
            x0 = bx + rs.uniform(-0.006, 0.006)
            rows.append((x0, by, x0 + rs.uniform(-0.01, 0.01), by + h,
                         0.30, 0.42, 0.16, 1.0, z + 0.0002, 0.0, 0.0030 * depth, 99.0))
            clr.append(u)
            ph.append(p)
            hgt.append(h)
            rows.append((x0, by + h, x0, by + h + 0.0001, fc[0], fc[1], fc[2], 1.0,
                         z + 0.0003, 0.0, 0.0120 * depth, 99.0))
            clr.append(u + 100.0)       # marks a flower head: follows the stalk tip
            ph.append(p)
            hgt.append(h)
    return dict(A=np.array(rows, dtype=np.float64), u=np.array(clr),
                ph=np.array(ph), h=np.array(hgt))


def _gen_reeds(rs):
    reeds = []
    # along the back shore, in front of the river
    for k in range(34):
        x = rs.uniform(-1.12, SHOREX + 0.02)
        reeds.append((x, shore_top(x) - 0.004, rs.uniform(0.05, 0.13), rs.random(),
                      99.0))
    # down the bank face, and a few standing in the shallows with their own
    # waterline, so the river reflects them
    for k in range(26):
        y = rs.uniform(-0.54, SHOREY - 0.02)
        x = land_edge(y) + rs.uniform(-0.03, 0.05)
        wet = x > land_edge(y) + 0.004
        reeds.append((x, y, rs.uniform(0.07, 0.16) * (0.9 + (SHOREY - y)), rs.random(),
                      (y + 0.010) if wet else 99.0))
    return reeds


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


def _gen_fireflies(rs):
    ff = []
    for k in range(NFLY):
        y = rs.uniform(-0.50, 0.00)
        x = rs.uniform(-1.05, 0.95)
        ff.append((x, y, rs.uniform(0.0, TAU), rs.uniform(0.6, 1.6),
                   rs.uniform(0.0, 100.0)))
    return ff


def _new(seed):
    rs = random.Random(seed)
    return {
        'seed': seed, 'rng': rs,
        'house': _gen_house(),
        'grass': _gen_grass(rs),
        'reeds': _gen_reeds(rs),
        'flies': _gen_fireflies(rs),
        'canopy': [(TREEX + rs.uniform(-0.20, 0.26), rs.uniform(0.18, 0.52),
                    rs.uniform(0.07, 0.13), rs.random()) for _ in range(16)],
        'plants': [(GARDEN[0] + 0.030 + (GARDEN[1] - GARDEN[0] - 0.06) * c / 6.0
                    + rs.uniform(-0.006, 0.006), ROWS[r], (r + c) % 3,
                    (r * 7 + c) / 20.0, rs.random())
                   for r in range(3) for c in range(7)],
        'tree': None,
        'mx': None, 'mgy': MANGY, 'mface': 1.0, 'mph': 0.0, 'walk': 0.0,
        'wang': 0.0, 'flow': 0.0, 'cloud': 0.0, 'lastf': None,
        'chips': [], 'smoke': [], 'rings': [], 'fish': [], 'birds': [],
        'bird_t': -99.0, 'fish_t': -99.0, 'smoke_t': -99.0, 'gust': 0.0,
        'seen': {}, 'rejects': 0, 'errs': 0, 'lastout': None, 'lastt': None,
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


# --- the plan: where he is and what he is doing, from the story alone -----------
def _stagep(f):
    return [_cl((f - a) / (b - a)) for (_n, a, b) in STAGES]


def _front(H, st, p):
    """x of the part currently being built in stage `st` at progress p."""
    m = H['st'] == st
    if not m.any():
        return None
    us = H['u'][m]
    xs = (H['A'][m, 0] + H['A'][m, 2]) * 0.5
    k = np.nonzero(us <= p + 1e-6)[0]
    if len(k) == 0:
        return float(xs[np.argmin(us)])
    return float(xs[k[np.argmax(us[k])]])


def _plan(f, sp, H, P5):
    """(target x, target gy, pose, facing, tool, reach)"""
    if f < 0.075:
        q = f / 0.075
        return (-1.28 + 1.20 * q, MANGY, 'carry', 1.0, 'bundle', 0.0)
    if f < STAGES[0][1]:
        return (-0.08, MANGY, 'look' if f < 0.092 else 'stand', 1.0, None, 0.0)
    if f < STAGES[0][2] + 0.008:
        front = CLR0 + (CLR1 - CLR0) * sp[0]
        return (front - 0.070, MANGY - 0.020, 'swing', 1.0, 'machete', 0.0)
    for si in (1, 2, 3):
        a, b = STAGES[si][1], STAGES[si][2]
        if f < b + 0.015:
            if f < a:
                x = _front(H, si, 0.0)
                return (x + 0.075, MANGY, 'stand', -1.0, 'hammer', 0.0)
            x = _front(H, si, sp[si])
            x = min(max(x, HX0 - 0.02), HX1 + 0.04)
            if si == 3:
                return (x + 0.060, FLOORY + 0.006, 'hammer', -1.0, 'hammer', 0.25)
            return (x + 0.075, MANGY, 'hammer', -1.0, 'hammer',
                    0.25 if si == 2 else 0.0)
    if f < STAGES[4][2] + 0.010:
        return (WX - 0.170, MANGY + 0.005, 'hammer' if f >= STAGES[4][1] else 'stand',
                1.0, 'hammer', 0.15)
    if f < STAGES[5][2] + 0.004:
        if f < STAGES[5][1]:
            return (P5[0][0] - 0.05, ROWS[0] + 0.012, 'stand', 1.0, None, 0.0)
        j = min(len(P5) - 1, int(sp[5] * len(P5)))
        px, py = P5[j][0], P5[j][1]
        return (px - 0.045, py + 0.010, 'plant', 1.0, None, 0.0)
    if f < 0.800:
        return (GARDEN[0] - 0.06, ROWS[0] + 0.012, 'look', -1.0, None, 0.0)
    if f < 0.818:
        return (0.305, MANGY + 0.004, 'switch' if f > 0.806 else 'stand', 1.0, None,
                0.0)
    return (HX1 + 0.090, MANGY + 0.010, 'sit', 1.0,
            'cup' if f > 0.905 else None, 0.0)


# --- the wild things -------------------------------------------------------------
def _deer(out, x, gy, sc, face, drink, walk, ph, sun, z, fawn=False):
    def P(u, v):
        return (x + u * sc * face, gy + v * sc)

    col = DEER if not fawn else _mix(DEER, (0.70, 0.50, 0.32), 0.3)
    lit = DEERLT
    legs = ((0.25, 0.0), (0.19, 0.5), (-0.24, 0.5), (-0.30, 0.0))
    for i, (hu, po) in enumerate(legs):
        back = i in (1, 2)
        sw = 0.10 * math.sin(TAU * (ph + po)) * walk
        top, foot = P(hu, 0.58), P(hu + sw, 0.0)
        _limb(out, top[0], top[1], foot[0], foot[1], 0.050 * sc,
              _mul(col, 0.78 if back else 1.0), None, 1.0,
              z + (-0.0012 if back else 0.0012), sun, LWT)
    body = _ell(P(0.0, 0.64)[0], P(0.0, 0.64)[1], 0.36 * sc, 0.155 * sc, 12)
    _shape(out, body, col, 1.0, z, lit, sun, LWT)
    head = _l2((0.52, 1.00), (0.64, 0.24), drink)
    n0, h = P(0.25, 0.72), P(*head)
    _limb(out, n0[0], n0[1], h[0], h[1], 0.110 * sc, col, lit, 1.0, z + 0.0005, sun,
          LWT)
    rot = math.atan2(-0.6 * drink + 0.25 * (1.0 - drink), 1.0) * face
    _shape(out, _ell(h[0] + 0.05 * sc * face, h[1], 0.105 * sc, 0.060 * sc, 10, rot),
           col, 1.0, z + 0.0008, lit, sun, LWT)
    for eo in (-0.04, 0.03):
        e0 = P(head[0] + eo, head[1] + 0.05)
        _limb(out, e0[0], e0[1], e0[0] - 0.05 * sc * face, e0[1] + 0.09 * sc,
              0.030 * sc, col, None, 1.0, z + 0.0006, sun, LWT)
    ey = P(head[0] + 0.06, head[1] + 0.015)
    _rect(out, ey[0], ey[1], 0.018 * sc, 0.018 * sc, INK, 1.0, z + 0.0012)
    tl = P(-0.37, 0.70)
    _shape(out, _ell(tl[0], tl[1], 0.040 * sc, 0.060 * sc, 8), (0.95, 0.93, 0.88),
           1.0, z + 0.0004, None, sun, LWT)
    if fawn:
        for k in range(5):
            sp = P(-0.20 + 0.10 * k, 0.66 + 0.04 * ((k % 2) - 0.5))
            _rect(out, sp[0], sp[1], 0.028 * sc, 0.022 * sc, (0.95, 0.92, 0.85), 1.0,
                  z + 0.0006)


def _heron(out, x, gy, sc, face, strike, sun, z, t):
    def P(u, v):
        return (x + u * sc * face, gy + v * sc)

    for fo in (-0.03, 0.04):
        a, b = P(fo * 0.3, 0.55), P(fo, 0.0)
        _limb(out, a[0], a[1], b[0], b[1], 0.018 * sc, (0.55, 0.50, 0.35), None, 1.0,
              z - 0.001, sun, LWT)
    bc = P(0.0, 0.64)
    _shape(out, _ell(bc[0], bc[1], 0.22 * sc, 0.095 * sc, 12, -0.35 * face), HERON,
           1.0, z, HERONLT, sun, LWT)
    _fill(out, [P(-0.18, 0.66), P(0.06, 0.62), P(-0.34, 0.54)], (0.38, 0.41, 0.49),
          1.0, z + 0.0005, 3)
    hd = _l2((0.16, 0.99), (0.44, 0.38), strike)
    mid = _l2((0.25, 0.82), (0.36, 0.62), strike)
    pts = [P(0.15, 0.68), P(*mid), P(0.12, 0.90) if strike < 0.5 else P(*mid),
           P(*hd)]
    for i in range(3):
        _limb(out, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 0.050 * sc,
              HERONLT, None, 1.0, z + 0.0008, sun, LWT)
    H = P(*hd)
    _shape(out, _ell(H[0], H[1], 0.050 * sc, 0.038 * sc, 8), HERONLT, 1.0, z + 0.001,
           None, sun, LWT)
    ang = -0.25 - 0.9 * strike
    bk = (H[0] + math.cos(ang) * 0.17 * sc * face, H[1] + math.sin(ang) * 0.17 * sc)
    _limb(out, H[0], H[1], bk[0], bk[1], 0.020 * sc, (0.92, 0.72, 0.25), None, 1.0,
          z + 0.0012, sun, LWT)
    cr = P(hd[0] - 0.13, hd[1] + 0.02 + 0.01 * math.sin(t * 2.0))
    _seg(out, H[0], H[1] + 0.01 * sc, cr[0], cr[1], INK, 1.0, z + 0.0011, 0.010 * sc)


def _fox(out, x, gy, sc, face, walk, ph, sit, sun, z, eyes):
    def P(u, v):
        return (x + u * sc * face, gy + v * sc)

    if sit > 0.5:
        body = [P(-0.16, 0.02), P(0.12, 0.02), P(0.16, 0.42), P(-0.02, 0.52),
                P(-0.18, 0.28)]
        _shape(out, body, FOX, 1.0, z, FOXLT, sun, LWT)
        _fill(out, [P(0.06, 0.20), P(0.15, 0.40), P(0.02, 0.46)], (0.95, 0.92, 0.86),
              1.0, z + 0.0005, 3)
        tl = [P(-0.14, 0.04), P(-0.40, 0.04), P(-0.46, 0.14), P(-0.20, 0.14)]
        _shape(out, tl, FOX, 1.0, z - 0.001, FOXLT, sun, LWT)
        _fill(out, [P(-0.40, 0.05), P(-0.47, 0.14), P(-0.42, 0.13)],
              (0.95, 0.92, 0.86), 1.0, z - 0.0005, 2)
        hc = P(0.06, 0.60)
    else:
        for i, (hu, po) in enumerate(((0.20, 0.0), (0.15, 0.5), (-0.16, 0.5),
                                      (-0.22, 0.0))):
            sw = 0.08 * math.sin(TAU * (ph + po)) * walk
            a, b = P(hu, 0.26), P(hu + sw, 0.0)
            _limb(out, a[0], a[1], b[0], b[1], 0.050 * sc,
                  _mul(FOX, 0.75) if i in (1, 2) else (0.20, 0.13, 0.10), None, 1.0,
                  z + (-0.001 if i in (1, 2) else 0.001), sun, LWT)
        _shape(out, _ell(P(0, 0.32)[0], P(0, 0.32)[1], 0.26 * sc, 0.10 * sc, 10),
               FOX, 1.0, z, FOXLT, sun, LWT)
        _shape(out, [P(-0.22, 0.34), P(-0.52, 0.30), P(-0.56, 0.36), P(-0.24, 0.40)],
               FOX, 1.0, z - 0.001, FOXLT, sun, LWT)
        hc = P(0.30, 0.40)
    _shape(out, _ell(hc[0], hc[1], 0.085 * sc, 0.070 * sc, 10), FOX, 1.0, z + 0.001,
           FOXLT, sun, LWT)
    _fill(out, [(hc[0] + 0.05 * sc * face, hc[1] + 0.01 * sc),
                (hc[0] + 0.15 * sc * face, hc[1] - 0.03 * sc),
                (hc[0] + 0.05 * sc * face, hc[1] - 0.05 * sc)], FOX, 1.0,
          z + 0.0012, 2)
    for eo in (-0.04, 0.03):
        e = (hc[0] + eo * sc * face, hc[1] + 0.06 * sc)
        _fill(out, [(e[0] - 0.03 * sc, e[1]), (e[0] + 0.03 * sc, e[1]),
                    (e[0], e[1] + 0.08 * sc)], FOX, 1.0, z + 0.0011, 2)
    CUR['fl'] = 1.0 if eyes > 0.05 else 0.0
    ey = (hc[0] + 0.04 * sc * face, hc[1] + 0.015 * sc)
    ec = _mix(INK, (1.0, 0.85, 0.45), eyes)
    _rect(out, ey[0], ey[1], 0.022 * sc, 0.020 * sc, ec, 1.0, z + 0.0015)
    CUR['fl'] = 0.0


def _bird(out, x, y, s, flap, a, z):
    w = 0.020 * s
    lift = 0.012 * s * flap
    _seg(out, x, y, x - w, y + lift, INK, a, z, 0.0030 * s)
    _seg(out, x, y, x + w, y + lift, INK, a, z, 0.0030 * s)


# --- one frame -------------------------------------------------------------------
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
        for nm in ('kickcnt', 'accentcnt', 'dropcnt', 'gustcnt', 'fishcnt',
                   'reseedcnt'):
            try:
                S['seen'][nm] = float(d[nm][0])
            except Exception:
                pass

    if _delta(S, d, 'reseedcnt'):
        keep = dict(S['seen'])
        S.update(_new((S['seed'] * 1103515245 + 12345) % 2147483647))
        S['seen'] = keep
    rs = S['rng']

    nkick = _delta(S, d, 'kickcnt')
    naccent = _delta(S, d, 'accentcnt')
    ndrop = _delta(S, d, 'dropcnt')
    ngust = _delta(S, d, 'gustcnt')
    nfish = _delta(S, d, 'fishcnt')

    slen = _sane(ch('storylen', STORYDEF), STORYDEF, 1.0, 1.0e5)
    f = _sane(ch('show', 0.0) / slen, 0.0, 0.0, 1.0)
    seek = S['lastf'] is not None and abs(f - S['lastf']) > 0.012
    # THE LOOP SEAM. Everything that integrates — the river's phase, the clouds,
    # the wheel — goes back to zero here, inside the black, so that no quantity in
    # this scene can grow past one story length however long it runs. (The shader
    # samples noise at these phases in 32-bit float; left to grow for six hours
    # they would reach thousands and the ripples and clouds would go blocky.)
    if S['lastf'] is not None and f < S['lastf'] - 0.5:
        S['flow'] = S['cloud'] = S['wang'] = 0.0
        S['loops'] = S.get('loops', 0) + 1
    S['lastf'] = f
    sp = _stagep(f)
    H = S['house']

    # --- the day --------------------------------------------------------------
    sunh = float(np.interp(f, SUN_F, SUN_H))
    sunx = float(np.interp(f, SUNX_F, SUNX_X))
    day = _ss(-0.06, 0.22, sunh)
    night = _ss(0.02, -0.35, sunh)
    rain = float(np.interp(f, RAIN_F, RAIN_A)) * float(par.Rain.eval())
    bulb = _ss(0.812, 0.822, f) * (1.0 - _ss(0.968, 0.990, f))
    amb = np.array([np.interp(sunh, AMB_H, AMB_R), np.interp(sunh, AMB_H, AMB_G),
                    np.interp(sunh, AMB_H, AMB_B)]) * (1.0 - 0.22 * rain)
    sway = float(par.Sway.eval())
    # through black at the loop seam: ~3 s out at the end, ~3 s in at the start
    fade = (_ss(0.0, 0.010, f) * (1.0 - _ss(0.990, 1.0, f))
            if par.Loop.eval() else 1.0)
    pace = float(par.Paceaudio.eval())

    # --- PACE: energy drives how fast things MOVE, integrated so nothing jumps ---
    # the river runs a little faster after the rain, and a lot faster when the
    # track is full; the wheel turns with the river; the clouds go with the wind
    flowspd = 0.030 * (0.70 + 0.55 * energy * pace) * (1.0 + 0.8 * _ss(0.53, 0.60, f)
                                                      * (1.0 - _ss(0.66, 0.80, f)))
    S['flow'] += dt * flowspd
    S['cloud'] += dt * 0.0045 * (0.6 + 0.8 * energy * pace)
    wheeldone = _ss(0.86, 1.0, sp[4])
    wspd = wheeldone * (0.55 + 1.35 * energy * pace) * (0.8 + 8.0 * flowspd)
    S['wang'] = (S['wang'] - dt * wspd) % TAU
    if ngust or ndrop:
        S['gust'] = 1.0
    S['gust'] *= 0.5 ** (dt / 0.9)
    gust = S['gust']

    # --- the man --------------------------------------------------------------
    P5 = S['plants']
    tx, tgy, pose, face, tool, reach = _plan(f, sp, H, P5)
    if S['mx'] is None or seek:
        S['mx'], S['mgy'] = tx, tgy
        S['chips'], S['smoke'], S['fish'], S['rings'] = [], [], [], []
    dxm = tx - S['mx']
    step = max(-MSPEED * dt, min(MSPEED * dt, dxm))
    S['mx'] += step
    moving = abs(dxm) > 0.006
    S['walk'] += ((1.0 if moving else 0.0) - S['walk']) * min(1.0, dt * 7.0)
    if moving:
        S['mface'] = 1.0 if dxm > 0 else -1.0
        S['mph'] = (S['mph'] + abs(step) / (0.36 * MANSC)) % 1.0
    else:
        S['mface'] = face
    dgy = tgy - S['mgy']
    S['mgy'] += max(-0.10 * dt, min(0.10 * dt, dgy))
    walkamt = S['walk']
    if moving and pose not in ('carry',):
        pose, tool = 'walk', (tool if tool in ('hammer', 'machete') else None)
    strike = kickenv ** 0.6 if not moving else 0.0
    sip = _ss(0.55, 0.85, 0.5 + 0.5 * math.sin(t * 0.55)) if pose == 'sit' else 0.0
    nod = 0.010 * kickenv if pose in ('sit', 'stand', 'look') else 0.0

    out = []
    CUR['wl'], CUR['fl'] = 99.0, 0.0
    msun = 1.0 if sunx > S['mx'] else -1.0
    mgy = S['mgy']
    tip = _man(out, S['mx'], mgy, MANSC, S['mface'], pose, S['mph'], walkamt,
               strike, t, msun, tool, nod, sip, reach=reach,
               zover=(_zd(GYH) + 0.030) if mgy > GYH + 0.02 else None)
    # his shadow on the ground (only by day, and only where there is ground)
    if day > 0.02 and pose != 'sit' and mgy < -0.25:
        shx = -(sunx - S['mx']) * 0.05
        _fill(out, _ell(S['mx'] + shx, mgy - 0.006, 0.070 + 0.03 * (1.0 - sunh),
                        0.012, 10), (0.0, 0.0, 0.0), 0.30 * day, _zd(mgy) - 0.012, 2)

    # work sparks: chips on the hammer, grass on the machete, soil on the seed
    if nkick and tip is not None and not moving:
        if pose == 'hammer':
            col = (0.80, 0.68, 0.45)
            for _ in range(4):
                S['chips'].append([t, tip[0], tip[1], rs.uniform(-0.25, 0.25),
                                   rs.uniform(0.10, 0.35), col, 0.006])
        elif pose == 'swing':
            for _ in range(5):
                S['chips'].append([t, tip[0], tip[1], rs.uniform(0.0, 0.35),
                                   rs.uniform(0.05, 0.30), (0.42, 0.56, 0.20),
                                   0.007])
        elif pose == 'plant':
            for _ in range(3):
                S['chips'].append([t, tip[0], tip[1] - 0.005,
                                   rs.uniform(-0.12, 0.12), rs.uniform(0.05, 0.18),
                                   (0.36, 0.26, 0.17), 0.006])
    del S['chips'][:-40]
    alive = []
    for c in S['chips']:
        a = t - c[0]
        if a > 0.65:
            continue
        alive.append(c)
        x = c[1] + c[3] * a
        y = c[2] + c[4] * a - 1.1 * a * a
        _rect(out, x, y, c[6], c[6], c[5], 1.0 - a / 0.65, _zd(mgy) + 0.02)
    S['chips'] = alive

    # --- the bundle he put down, and the log pile he cut ------------------------
    if f > 0.090:
        bxp, byp = 0.135, MANGY + 0.012
        _shape(out, _ell(bxp, byp + 0.020, 0.030, 0.024, 10), PATCH2, 1.0,
               _zd(byp), _mix(PATCH2, DHOTILT, 0.35), -1.0)
        _shape(out, _ell(bxp + 0.020, byp + 0.012, 0.016, 0.014, 8), PATCH, 1.0,
               _zd(byp) + 0.001, None, -1.0, LWO * 0.6)
    logs = int(round(9 * sp[0])) - int(round(9 * (0.45 * sp[1] + 0.30 * sp[2]
                                                  + 0.25 * sp[3])))
    logs = max(0, logs)
    LX, LY = -0.040, -0.300
    lz = _zd(LY)
    k = 0
    for row in range(3):
        for c in range(4 - row):
            if k >= logs:
                break
            cx = LX + c * 0.030 + row * 0.015
            cy = LY + 0.012 + row * 0.024
            _limb(out, cx - 0.045, cy + 0.012, cx, cy, 0.022, WOOD, WOODLT, 1.0,
                  lz - 0.002 + row * 0.001, -1.0)
            _shape(out, _ell(cx, cy, 0.012, 0.012, 8), WOODEND, 1.0,
                   lz + row * 0.001, None, -1.0, LWO * 0.7)
            k += 1

    # --- the house: parts whose stage has reached them, dropping into place ------
    stp = np.array(sp, dtype=np.float64)
    kk = np.clip((stp[H['st']] - H['u']) / POPW, 0.0, 1.0)
    kk = np.where(stp[H['st']] >= 1.0, 1.0, kk)
    vis = kk > 0.0
    HA = H['A'][vis].copy()
    kv = kk[vis]
    drop = (1.0 - kv) ** 2 * 0.030
    HA[:, 1] += drop
    HA[:, 3] += drop
    HA[:, 7] *= np.minimum(1.0, kv * 1.6)
    # a contact shadow under the platform once there are walls to throw one
    if day > 0.02 and sp[2] > 0.05:
        shl = 0.035 + 0.05 * (1.0 - _cl(sunh))
        sx = -(sunx - (HX0 + HX1) * 0.5) * 0.10
        _fill(out, [(HX0 - 0.02, GYH - 0.004), (HX1 + 0.03, GYH - 0.004),
                    (HX1 + 0.03 + sx, GYH - shl), (HX0 - 0.02 + sx, GYH - shl)],
              (0.0, 0.0, 0.0), 0.26 * day * _ss(0.05, 0.9, sp[2]), _zd(GYH) - 0.045,
              3)

    # the window lights up at night, and the bulb burns under the eave
    if sp[2] > 0.95:
        CUR['fl'] = 1.0
        wglow = max(bulb * 0.95, 0.55 * night * _ss(0.60, 0.70, f))
        if wglow > 0.01:
            flick = 0.92 + 0.08 * math.sin(t * 7.3) * math.sin(t * 3.1)
            # between the dark interior (zw - 0.002) and the slats (zw)
            _rect(out, -0.490, -0.073, 0.086, 0.068, _mul(WARM, 0.95 * flick),
                  wglow, _zd(GYH) - 0.0112)
            _rect(out, -0.2985, -0.111, 0.070, 0.158, _mul(WARM, 0.70 * flick),
                  wglow * 0.85, _zd(GYH) - 0.0112)
        CUR['fl'] = 0.0
    if bulb > 0.0 and sp[3] >= 1.0:
        CUR['fl'] = 1.0
        bf = bulb * (0.90 + 0.10 * min(1.0, wspd / 1.2))
        _fill(out, _ell(BULB[0], BULB[1], 0.011, 0.014, 10), (1.0, 0.92, 0.70),
              bf, _zd(GYH) + 0.020, 2)
        _fill(out, _ell(BULB[0], BULB[1], 0.030, 0.030, 16), WARM, 0.45 * bf,
              _zd(GYH) + 0.019, 8)
        CUR['fl'] = 0.0

    # --- the water wheel ---------------------------------------------------------
    p4 = sp[4]
    if p4 > 0.22:
        CUR['wl'] = WWL
        zwh = _zd(WWL) + 0.010
        ang = S['wang']
        nsp = 8
        shown = int(round(_cl((p4 - 0.26) / 0.30) * nsp))
        for i in range(shown):
            th = ang + i * TAU / nsp
            ex, ey = WX + math.cos(th) * WR * 0.90, WY + math.sin(th) * WR * 0.90
            _limb(out, WX, WY, ex, ey, 0.008, WOOD, None, 1.0, zwh, -1.0, LWO * 0.6)
        if p4 > 0.58:
            for r in (WR, WR * 0.84):
                pts = [(WX + math.cos(ang + i * TAU / 20) * r,
                        WY + math.sin(ang + i * TAU / 20) * r) for i in range(20)]
                _path(out, pts, INK, 1.0, zwh + 0.0003, 0.012, close=True)
                _path(out, pts, WOODLT if r == WR else WOOD, 1.0, zwh + 0.0006, 0.006,
                      close=True)
        npd = int(round(_cl((p4 - 0.62) / 0.20) * nsp))
        for i in range(npd):
            th = ang + (i + 0.5) * TAU / nsp
            cx, cy = math.cos(th), math.sin(th)
            a0 = (WX + cx * WR * 0.80, WY + cy * WR * 0.80)
            a1 = (WX + cx * WR * 1.16, WY + cy * WR * 1.16)
            _limb(out, a0[0], a0[1], a1[0], a1[1], 0.028, WOOD, WOODLT, 1.0,
                  zwh + 0.001, -1.0, LWO * 0.7)
        _shape(out, _ell(WX, WY, 0.016, 0.016, 10), IRON, 1.0, zwh + 0.002, IRONLT,
               -1.0)
        CUR['wl'] = 99.0
        # water thrown off the bottom paddles as it turns
        if wspd > 0.2 and rs.random() < 0.45 * min(1.0, wspd):
            S['chips'].append([t, WX + rs.uniform(0.02, 0.09), WWL + 0.004,
                               rs.uniform(0.02, 0.25), rs.uniform(0.10, 0.30),
                               (0.82, 0.90, 0.95), 0.005])

    # --- the garden -------------------------------------------------------------
    f50, f51 = STAGES[5][1], STAGES[5][2]
    for (px, py, kind, u, var) in P5:
        fp = f50 + (f51 - f50) * (u + 0.03)
        if f < fp:
            continue
        g = _cl((f - fp) / 0.13) ** 0.8
        g = 0.20 + 0.80 * g if f < 0.90 else 1.0
        zp = _zd(py) + 0.002
        swy = (0.004 + 0.006 * bass * sway + 0.02 * gust) * math.sin(t * 1.9 + px * 9.0)
        hmax = (0.050, 0.100, 0.070)[kind]
        h = hmax * g
        tipx, tipy = px + swy * g, py + h
        _limb(out, px, py, tipx, tipy, 0.005, LEAFDK, None, 1.0, zp, -1.0, LWO * 0.5)
        nl = 1 + int(4 * g)
        for j in range(nl):
            q = (j + 1.0) / (nl + 1.0)
            lx, ly = px + (tipx - px) * q, py + h * q
            side = 1.0 if j % 2 == 0 else -1.0
            ll = (0.018 + 0.010 * g) * (1.2 - 0.5 * q) * (1.3 if kind == 0 else 1.0)
            _shape(out, _ell(lx + side * ll * 0.55, ly + ll * 0.25, ll * 0.60,
                             ll * 0.24, 8, side * 0.45), LEAF, 1.0, zp + 0.0003,
                   LEAFLT, -1.0, LWO * 0.5)
        if kind == 1 and g > 0.7:
            _shape(out, _ell(tipx, tipy + 0.012, 0.007, 0.018, 8), (0.80, 0.66, 0.30),
                   1.0, zp + 0.0006, None, -1.0, LWO * 0.5)
        if kind == 2 and f > 0.905:
            ripe = _ss(0.905, 0.960, f)
            for j in range(2):
                fx = px + (0.012 if j else -0.010)
                fy = py + h * (0.45 + 0.2 * j)
                _shape(out, _ell(fx, fy, 0.008, 0.008, 8),
                       _mix((0.40, 0.60, 0.20), (0.85, 0.18, 0.12), ripe), 1.0,
                       zp + 0.0008, None, -1.0, LWO * 0.5)

    # --- smoke from the chimney once there is a hearth under the thatch -----------
    if f > 0.600 and sp[3] >= 1.0:
        want = (nkick > 0 and t - S['smoke_t'] > 0.35) or t - S['smoke_t'] > 1.4
        if want:
            S['smoke_t'] = t
            S['smoke'].append([t, -0.326, 0.190, rs.random()])
        del S['smoke'][:-14]
        for pf in S['smoke']:
            a = t - pf[0]
            if a > 5.0:
                continue
            x = pf[1] + a * 0.018 * (1.0 + 2.0 * gust) + 0.010 * math.sin(a * 1.3 + pf[3] * 6)
            y = pf[2] + a * 0.030
            r = 0.012 + 0.016 * a
            sfade = (1.0 - a / 5.0) * _ss(0.0, 0.4, a)
            CUR['fl'] = 0.0
            _fill(out, _ell(x, y, r, r * 0.85, 14), (0.90, 0.89, 0.87),
                  0.42 * sfade * (1.0 - 0.45 * night), _zd(GYH) + 0.020, 8)

    # --- the big wild tree (static rows, swayed below) --------------------------
    tz = _zd(-0.300) - 0.030
    tsun = 1.0 if sunx > TREEX else -1.0

    # the owl on the low branch, only at night
    owl = night * _ss(0.83, 0.86, f) * (1.0 - _ss(0.965, 0.985, f))
    if owl > 0.02:
        ox, oy = TREEX + 0.150, 0.262
        _shape(out, _ell(ox, oy, 0.024, 0.036, 10), (0.36, 0.28, 0.20), owl,
               tz + 0.010, (0.50, 0.40, 0.28), tsun)
        _fill(out, [(ox - 0.020, oy + 0.028), (ox - 0.012, oy + 0.050),
                    (ox - 0.004, oy + 0.030)], (0.36, 0.28, 0.20), owl, tz + 0.011, 2)
        _fill(out, [(ox + 0.020, oy + 0.028), (ox + 0.012, oy + 0.050),
                    (ox + 0.004, oy + 0.030)], (0.36, 0.28, 0.20), owl, tz + 0.011, 2)
        blink = 0.0 if (t % 5.3) < 0.14 else 1.0
        CUR['fl'] = 1.0
        for eo in (-0.009, 0.009):
            _rect(out, ox + eo, oy + 0.014, 0.008, 0.008 * blink + 0.001,
                  (1.0, 0.80, 0.30), owl, tz + 0.012)
        CUR['fl'] = 0.0

    # --- reeds ----------------------------------------------------------------
    for (rx, ry, rh, v, wl) in S['reeds']:
        CUR['wl'] = wl
        o = (0.004 + 0.008 * bass * sway + 0.025 * gust) * math.sin(t * 1.5 + v * 9.0)
        zr = _zd(ry) + 0.001
        tipx, tipy = rx + o * rh * 12.0, ry + rh
        _seg(out, rx, ry, tipx, tipy, (0.33, 0.40, 0.18), 1.0, zr, 0.0042)
        _seg(out, rx + 0.004, ry, rx + 0.016 + o * 8.0, ry + rh * 0.62,
             (0.40, 0.48, 0.20), 1.0, zr + 0.0002, 0.0034)
        if v > 0.55:
            hy0 = tipy - 0.030 * rh / 0.1
            _limb(out, rx + (tipx - rx) * 0.8, hy0, tipx, tipy - 0.004, 0.009,
                  (0.38, 0.24, 0.13), None, 1.0, zr + 0.0003, -1.0, LWO * 0.5)
    CUR['wl'] = 99.0

    # --- the deer: at the far bank when he arrives, and back again at dawn ---------
    if f < 0.105:
        leave = _ss(0.055, 0.100, f)
        for i, (dx0, sc) in enumerate(((0.52, 0.058), (0.64, 0.052))):
            x = dx0 + leave * 0.55
            if x > 1.15:
                continue
            CUR['wl'] = FARY - 0.002
            drink = 0.0 if leave > 0.0 else _ss(0.3, 0.7, 0.5 + 0.5 * math.sin(
                t * 0.35 + i * 2.0))
            _deer(out, x, FARY + 0.002, sc, 1.0, drink, 1.0 if leave > 0.01 else 0.0,
                  t * 1.6 + i * 0.3, 1.0 if sunx > x else -1.0, 0.060 + 0.001 * i)
    if f > 0.915:
        come = _ss(0.915, 0.955, f)
        for i, (dx0, sc, fawn) in enumerate(((0.44, 0.060, False),
                                             (0.60, 0.055, False),
                                             (0.53, 0.038, True))):
            x = dx0 + (1.0 - come) * 0.60
            CUR['wl'] = FARY - 0.002
            drink = come * _ss(0.3, 0.7, 0.5 + 0.5 * math.sin(t * 0.3 + i * 1.7))
            _deer(out, x, FARY + 0.002, sc, -1.0, drink,
                  1.0 if come < 0.99 else 0.0, t * 1.6 + i * 0.3,
                  1.0 if sunx > x else -1.0, 0.060 + 0.001 * i, fawn)
    CUR['wl'] = 99.0

    # --- the heron fishes the shallows through the afternoon ---------------------
    her = _ss(0.520, 0.540, f) * (1.0 - _ss(0.770, 0.790, f))
    if her > 0.02:
        hx, hy = 0.655, -0.040
        # she strikes on an accented beat, but patiently: most of them she lets go
        if naccent and t - S.get('heron_t', -99.0) > 5.0 and rs.random() < 0.30:
            S['heron_t'] = t
        sa = t - S.get('heron_t', -99.0)
        strike_h = math.exp(-((sa - 0.25) / 0.14) ** 2) if 0.0 < sa < 0.8 else 0.0
        CUR['wl'] = hy + 0.018
        tmp = []
        _heron(tmp, hx, hy, 0.14, -1.0, strike_h,
               1.0 if sunx > hx else -1.0, _zd(hy), t)
        out.extend([r[:7] + (r[7] * her,) + r[8:] for r in tmp])
        CUR['wl'] = 99.0
        if 0.20 < sa < 0.24 and dt > 0:
            S['rings'].append([t, hx - 0.05, hy + 0.008, 0.45])

    # --- the fox comes to the edge of the light and sits -------------------------
    fx_in = _ss(0.838, 0.862, f)
    fx_out = _ss(0.925, 0.945, f)
    if 0.838 < f < 0.945:
        walking = (fx_in < 0.999) or (fx_out > 0.001)
        x = -1.20 + 0.52 * fx_in - 0.60 * fx_out
        facef = 1.0 if fx_out < 0.001 else -1.0
        _fox(out, x, -0.415, 0.16, facef, 1.0 if walking else 0.0, t * 2.2,
             0.0 if walking else 1.0, 1.0, _zd(-0.415), night)

    # --- fish jump on accented beats, and the rings they leave --------------------
    if (naccent and t - S['fish_t'] > FISHGAP and 0.02 < f and rs.random() < 0.55) \
            or nfish:
        for _ in range(10):
            fy = rs.uniform(-0.50, FARY - 0.04)
            fx = rs.uniform(-0.2, 0.70)
            if is_water(fx, fy) and is_water(fx + 0.08, fy):
                S['fish'].append([t, fx, fy, rs.choice((-1.0, 1.0)),
                                  0.6 + (FARY - fy) * 1.6])
                S['fish_t'] = t
                break
    live = []
    for fh in S['fish']:
        a = (t - fh[0]) / 0.75
        if a > 1.0:
            S['rings'].append([t, fh[1] + fh[3] * 0.06 * fh[4], fh[2], fh[4]])
            continue
        live.append(fh)
        sz = fh[4]
        x = fh[1] + fh[3] * 0.06 * sz * a
        y = fh[2] + 0.055 * sz * 4.0 * a * (1.0 - a)
        rot = math.atan2(0.055 * sz * 4.0 * (1.0 - 2.0 * a), fh[3] * 0.06 * sz)
        CUR['wl'] = fh[2]
        _shape(out, _ell(x, y, 0.016 * sz, 0.006 * sz, 8, rot), (0.72, 0.78, 0.82),
               1.0, _zd(fh[2]) + 0.002, (0.92, 0.95, 0.98), 1.0, LWO * 0.5)
        CUR['wl'] = 99.0
    S['fish'] = live
    # the shower patters on the open water
    if rain > 0.05:
        for _ in range(int(rain * 3.0 + rs.random())):
            ry = rs.uniform(-0.55, FARY - 0.02)
            rx = rs.uniform(-0.2, 0.75)
            if is_water(rx, ry):
                S['rings'].append([t, rx, ry, 0.25 + (FARY - ry) * 0.9])
    del S['rings'][:-RINGMAX]
    del S['fish'][:-6]
    live = []
    for rg in S['rings']:
        a = (t - rg[0]) / 1.3
        if a > 1.0:
            continue
        live.append(rg)
        r = (0.006 + 0.040 * a) * rg[3]
        pts = _ell(rg[1], rg[2], r, r * 0.22, 14)
        _path(out, pts, (0.80, 0.88, 0.92), 0.45 * (1.0 - a), _zd(rg[2]) - 0.003,
              0.0022, close=True)
    S['rings'] = live

    # --- birds: a flock crosses now and then, and a gust puts them up out of the tree
    if (ngust or ndrop) and day > 0.15:
        n = rs.randint(5, 9)
        S['birds'].append([t, TREEX + 0.05, 0.24, 1.0, n, rs.random(), 1.0, 0.14])
    elif day > 0.3 and t - S['bird_t'] > 22.0 and rs.random() < 0.01:
        S['bird_t'] = t
        dirb = rs.choice((-1.0, 1.0))
        S['birds'].append([t, -1.15 * dirb, rs.uniform(0.17, 0.32), dirb,
                           rs.randint(3, 7), rs.random(), rs.uniform(0.55, 0.9), 0.0])
    del S['birds'][:-6]
    live = []
    for bd in S['birds']:
        a = t - bd[0]
        x0 = bd[1] + bd[3] * a * 0.11
        y0 = bd[2] + bd[7] * a * 0.6 * math.exp(-a * 0.6)
        if abs(x0) > 1.35 or a > 30.0:
            continue
        live.append(bd)
        for j in range(int(bd[4])):
            ox = -bd[3] * (0.035 * ((j + 1) // 2)) + 0.004 * math.sin(a + j)
            oy = (0.018 * ((j + 1) // 2)) * (1 if j % 2 else -1) * 0.6
            flap = math.sin(t * 9.0 * (0.8 + 0.5 * high) + j * 1.3 + bd[5] * 6.0)
            _bird(out, x0 + ox, y0 + oy, bd[6], flap, 0.85 * (0.4 + 0.6 * day),
                  0.030)
    S['birds'] = live

    # --- fireflies over the grass at night; the highs are how often they blink ----
    if night > 0.05:
        CUR['fl'] = 1.0
        for (fxb, fyb, ph, rate, sd) in S['flies']:
            x = fxb + 0.030 * math.sin(t * 0.31 * rate + sd)
            y = fyb + 0.020 * math.sin(t * 0.43 * rate + sd * 1.7)
            bl = max(0.0, math.sin(t * rate * (1.2 + 1.6 * high) + ph)) ** 6
            if bl < 0.02:
                continue
            _rect(out, x, y, 0.0048, 0.0048, FIREFLY, night * bl, 0.95)
            _rect(out, x, y, 0.014, 0.014, FIREFLY, night * bl * 0.22, 0.949)
        CUR['fl'] = 0.0

    # --- assemble: dynamic rows, the house, the grass ------------------------------
    A = np.array(out, dtype=np.float64) if out else np.zeros((0, 12))
    G = S['grass']
    GA = G['A'].copy()
    isfl = G['u'] >= 99.0
    uu = np.where(isfl, G['u'] - 100.0, G['u'])
    cut = sp[0] >= uu
    base_x, base_y = GA[:, 0], GA[:, 1]
    amp = (0.006 + 0.010 * bass * sway) * (1.0 + 3.5 * gust)
    swayv = amp * np.sin(t * 1.6 + G['ph'] + base_x * 2.5) * (G['h'] / 0.06)
    swayv += 0.012 * gust * (G['h'] / 0.06)
    GA[:, 2] += swayv
    # cut grass: stubble, a little browner
    k = np.where(cut, 0.20, 1.0)
    GA[:, 2] = base_x + (GA[:, 2] - base_x) * k
    GA[:, 3] = base_y + (GA[:, 3] - base_y) * k
    brown = np.where(cut, 0.45, 0.0)
    GA[:, 4] = GA[:, 4] * (1 - brown) + 0.46 * brown
    GA[:, 5] = GA[:, 5] * (1 - brown) + 0.38 * brown
    GA[:, 6] = GA[:, 6] * (1 - brown) + 0.20 * brown
    # a flower head rides the tip of the stalk just before it in the list
    fi = np.nonzero(isfl)[0]
    if len(fi):
        GA[fi, 0] = GA[fi - 1, 2]
        GA[fi, 1] = GA[fi - 1, 3]
        GA[fi, 2] = GA[fi - 1, 2]
        GA[fi, 3] = GA[fi - 1, 3] + 0.0001
        GA[fi, 7] = np.where(cut[fi], 0.0, 1.0)
    # anything growing under the house or the garden is gone once it is built on
    T = S['tree']
    TA = T['A'].copy()
    tsw = (0.004 + 0.006 * bass * sway + 0.020 * gust)
    osc = np.sin(t * 1.2 + T['ph'][T['g']])
    off = np.where(T['w'] > 0.0, tsw * T['w'] * osc, 0.0)
    off = np.where(T['w'] < 0.0, (0.010 + 0.012 * bass * sway + 0.03 * gust)
                   * np.sin(t * 0.9 + T['ph'][T['g']]), off)
    TA[:, 0] += off
    TA[:, 2] += off
    parts = [A, HA, TA, GA]
    A = np.concatenate([p for p in parts if len(p)], axis=0)

    # --- the waterline rule --------------------------------------------------------
    wl = A[:, 11]
    my = (A[:, 1] + A[:, 3]) * 0.5
    has = wl < 50.0
    sub = has & (my < wl)
    wc = np.array(WATER)
    if sub.any():
        A[sub, 7] *= 0.40
        A[np.ix_(sub, [4, 5, 6])] = A[np.ix_(sub, [4, 5, 6])] * 0.5 + wc * 0.5
    ref = has & (my >= wl)
    R = A[ref].copy()
    if len(R):
        rwl = R[:, 11]
        R[:, 1] = 2.0 * rwl - R[:, 1]
        R[:, 3] = 2.0 * rwl - R[:, 3]
        shim = 0.004 * np.sin(R[:, 1] * 160.0 + t * 2.6)
        R[:, 0] += shim
        R[:, 2] += shim
        depth = rwl - (R[:, 1] + R[:, 3]) * 0.5
        R[:, 7] *= 0.34 * np.clip(1.0 - depth / 0.35, 0.0, 1.0)
        R[:, 4:7] = R[:, 4:7] * 0.62 + wc * 0.22
        R[:, 8] = -0.80 + R[:, 8] * 0.01
        R[:, 11] = 99.0

    # --- light the cels by the painted sky ---------------------------------------
    lit = A[:, 9] < 0.5
    ink = float(par.Ink.eval())
    L = np.tile(amb, (len(A), 1))
    if bulb > 0.0:
        mx = (A[:, 0] + A[:, 2]) * 0.5
        dd = (mx - BULB[0]) ** 2 + ((my - BULB[1]) * 1.4) ** 2
        warm = bulb * 0.95 / (1.0 + dd * 70.0)
        L += np.outer(warm, np.array(WARM))
    A[lit, 4:7] = A[lit, 4:7] * L[lit] * ink
    if len(R):
        rl = R[:, 9] < 0.5
        R[rl, 4:7] = R[rl, 4:7] * amb * ink
        A = np.concatenate([A, R], axis=0)

    # --- cull, order, publish -------------------------------------------------------
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

    # THE BLACKOUT GUARD (see monsoon): a non-finite or runaway instance is a quad
    # across the whole frame. Validate, remove, count, carry on.
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

    try:
        par.Chapter.val = float(cp)
        par.Segs.val = float(n)
        par.Sunh.val = _sane(sunh, 0.0, -1.0, 1.0)
        par.Sunx.val = _sane(sunx, 0.0, -1.5, 1.5)
        par.Rainnow.val = _sane(rain, 0.0, 0.0, 1.0)
        par.Flowph.val = _sane(S['flow'], 0.0, 0.0, 1e6)
        par.Cloudph.val = _sane(S['cloud'], 0.0, 0.0, 1e6)
        par.Wheelspd.val = _sane(wspd, 0.0, 0.0, 6.0)
        par.Bulb.val = _sane(bulb, 0.0, 0.0, 1.0)
        par.Clearp.val = _sane(sp[0], 0.0, 0.0, 1.0)
        par.Gustnow.val = _sane(gust, 0.0, 0.0, 1.0)
        par.Fade.val = _sane(fade, 1.0, 0.0, 1.0)
        par.Loops.val = float(S.get('loops', 0))
        par.Labelfade.val = _sane(lf, 0.0, 0.0, 1.0)
        par.Rejects.val = float(S.get('rejects', 0))
        txt = CHECKPOINTS[cp][1].strip()
        if par.Scaletxt.eval() != txt:
            par.Scaletxt.val = txt
    except Exception:
        pass

    S['census'] = ('f %.3f | sun %.2f | stages %s | quads %d/%d | man %.2f %s | '
                   'wheel %.2f rad/s | rejects %d'
                   % (f, sunh, ' '.join('%.2f' % v for v in sp), n, MAXSEG,
                      S['mx'], pose, wspd, S.get('rejects', 0)))
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
                print('[homestead engine] frame failed:\n' + S['lasterr'])
            prev = S.get('lastout')
        else:
            prev = None
        if prev is None:
            raise
        _publish(scriptOp, prev)
    return
'''

GARDEN = (-0.115, 0.235, -0.505, -0.365)     # x0, x1, y front, y back
ROWS = (-0.385, -0.430, -0.475)
AMB = dict(  # ambient light on the cels by sun height: night, dusk, sunset, gold, day
    # KEPT DIM ON PURPOSE. The day is told by where the sun is, not by how bright
    # the frame is — so the sun is the brightest thing on screen and it pulses on
    # the beat. These must match ambient() in the world shader.
    H=(-0.60, -0.20, 0.00, 0.15, 0.40, 0.90),
    R=(0.130, 0.260, 0.600, 0.700, 0.700, 0.690),
    G=(0.160, 0.260, 0.440, 0.560, 0.640, 0.650),
    B=(0.300, 0.440, 0.420, 0.440, 0.540, 0.560),
)

eng_src = C(textDAT, 'engine_src', 1780, 980)
_eng_consts = dict(
    CHECKPOINTS=CHECKPOINTS, STAGES=STAGES, MAXSEG=MAXSEG, SEED0=20260923,
    CH=('tx', 'ty', 'tz', 'rz', 'sx', 'sy', 'sz', 'r', 'g', 'b', 'a'),
    FARY=FARY, SHOREY=SHOREY, SHOREX=SHOREX, BANKK=BANKK, BANKH=BANKH,
    GYH=GYH, FLOORY=FLOORY, WALLTOP=WALLTOP, HX0=HX0, HX1=HX1,
    MANGY=MANGY, MANSC=MANSC, WX=WX, WY=WY, WR=WR, WWL=WWL, BULB=BULB,
    GARDEN=GARDEN, ROWS=ROWS,
    SUN_F=SUN_F, SUN_H=SUN_H, SUNX_F=SUNX_F, SUNX_X=SUNX_X,
    RAIN_F=RAIN_F, RAIN_A=RAIN_A,
    AMB_H=AMB['H'], AMB_R=AMB['R'], AMB_G=AMB['G'], AMB_B=AMB['B'],
    STORYDEF=STORYDEF,
    # 1280 px across 2.0 world units: 640 px per unit, so 0.0042 is a 2.7 px line
    LWO=0.0042, LWT=0.0030, HS=1.30,
    CLR0=-0.760, CLR1=0.300, NTUFT=190, NFLY=46, TREEX=-0.905,
    MSPEED=0.200, POPW=0.035, FISHGAP=7.0, RINGMAX=36,
    CULLX=1.30, CULLY=0.70, MINLEN=0.0004, MAXW=0.60, MAXL=2.80,
)
for _k in ('INK', 'SKIN', 'SKINLT', 'SHIRT', 'SHIRTLT', 'PATCH', 'PATCH2', 'DHOTI',
           'DHOTILT', 'CLOTHR', 'CLOTHRLT', 'BEARD', 'BAMB', 'BAMBLT', 'BAMBDK',
           'MUD', 'MUDLT', 'THATCH', 'THATCHLT', 'THATCHDK', 'DARKIN', 'CLAY',
           'CLAYLT', 'WOOD', 'WOODLT', 'WOODEND', 'IRON', 'IRONLT', 'LEAF', 'LEAFLT',
           'LEAFDK', 'TRUNK', 'TRUNKLT', 'DEER', 'DEERLT', 'HERON', 'HERONLT', 'FOX',
           'FOXLT', 'WARM', 'FIREFLY', 'WATER'):
    _eng_consts[_k] = PAL[_k]
eng_src.text = hdr(**_eng_consts) + ENGINE_BODY

engine = C(scriptCHOP, 'engine', 1940, 980)
engine.par.callbacks = eng_src.name
W(director, engine, 0)


# ---------------------------------------------------------------------------
# GEOMETRY AND RENDER
# ---------------------------------------------------------------------------
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


def _g3(c):
    return 'vec3(%.4f, %.4f, %.4f)' % c


# --- ONE SHADER: the painted world, the composite, and the grade --------------
world = C(glslTOP, 'world', 2260, 200)
res(world)
world_pix = C(textDAT, 'world_pixel', 2260, 120)
world_pix.text = ('''// THE PAINTED WORLD. Everything here is the "realism" half of the piece: a sky
// with a real day and night, the sun and its haze, clouds lit from the sun's side,
// two ranges of mountains fading into aerial perspective, the far jungle and the
// mist lying on it, the river with perspective ripples, reflections and glitter,
// and the textured bank. Then the cels are composited over it, glowed, graded.
//
// uD.w is the loop fade: the whole frame goes through black at the story's seam.
//
// Every scalar arrives on the Vectors page (the Constants page is broken on this
// build — see MACHINE.md), and goes through san() before it is used.
uniform vec4 uA;   // x time, y sun height, z sun x (world), w rain
uniform vec4 uB;   // x river phase, y cloud phase, z bass, w high
uniform vec4 uC;   // x vignette, y brightness, z glow, w label fade
uniform vec4 uD;   // x kick env, y bulb, z ground cleared, w loop fade
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
const vec2 BULB = vec2(''' + repr(BULB[0]) + ''', ''' + repr(BULB[1]) + ''');
const vec3 WARM = ''' + _g3(PAL['WARM']) + ''';
// the sun's path: it clears the hills a little after dawn and peaks just under the
// top of the frame, so where it is in the sky tells you the time of day
const float SUNY0 = 0.085;
const float SUNYK = 0.27;
const vec2 MOONP = vec2(0.46, 0.30);

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

    vec2 sp = vec2(sunx, FARY + SUNY0 + sunh * SUNYK);
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
    float topfrac = (w.y - CAMY) / (OH * 0.5);
    if (night > 0.01 && !refl && topfrac > 0.0) {
        vec2 g = floor(w * 150.0);
        float hs = hash21(g);
        float tw = 0.55 + 0.45 * sin(t * (1.5 + 3.0 * hs) * (0.7 + 0.8 * high) + hs * 40.0);
        float star = step(0.9955, hs) * tw * smoothstep(0.0, 0.35, topfrac);
        col += vec3(0.85, 0.90, 1.0) * star * night * 0.9;
    }
    // THE MOON GLOWS TO THE BEAT too, a cool halo that breathes with the kick
    vec2 mp = MOONP;
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

float sheet(vec2 uv, float sc, float speed, float slant, float thin, float t) {
    vec2 p = uv * vec2(sc, sc * 0.30);
    p.x += p.y * slant;
    p.y -= t * speed;
    vec2 id = floor(p);
    vec2 f = fract(p);
    float h = hash21(id);
    float on = step(0.62, h);
    float x = abs(f.x - 0.5 - (h - 0.5) * 0.6);
    float streak = smoothstep(0.5, 0.0, x * thin);
    float tail = smoothstep(0.0, 0.55, f.y) * smoothstep(1.0, 0.75, f.y);
    return streak * tail * on * (0.45 + 0.55 * h);
}

void main() {
    vec2 uv = vUV.st;
    vec2 w = vec2((uv.x - 0.5) * OW + CAMX, (uv.y - 0.5) * OH + CAMY);
    float t     = san(uA.x, 0.0, 1.0e7, 0.0);
    float sunh  = san(uA.y, -1.0, 1.0, 0.3);
    float sunx  = san(uA.z, -1.5, 1.5, 0.0);
    float rain  = san(uA.w, 0.0, 2.0, 0.0);
    float flow  = san(uB.x, 0.0, 1.0e6, 0.0);
    float cph   = san(uB.y, 0.0, 1.0e6, 0.0);
    float bass  = san(uB.z, 0.0, 2.0, 0.0);
    float high  = san(uB.w, 0.0, 2.0, 0.0);
    float vign  = san(uC.x, 0.0, 2.0, 0.65);
    float brite = san(uC.y, 0.2, 4.0, 1.0);
    float glowa = san(uC.z, 0.0, 4.0, 0.3);
    float labf  = san(uC.w, 0.0, 1.0, 0.0);
    float bulb  = san(uD.y, 0.0, 1.0, 0.0);
    float clr   = san(uD.z, 0.0, 1.0, 0.0);
    float kick  = pow(san(uD.x, 0.0, 1.0, 0.0), 0.7);
    float fade  = san(uD.w, 0.0, 1.0, 1.0);

    vec3 amb = ambient(sunh);
    vec3 sc = sunColor(sunh);
    vec3 hor = skyHor(sunh);
    float night = smoothstep(0.02, -0.35, sunh);
    float sunvis = smoothstep(-0.10, 0.03, sunh);

    vec3 col;
    bool land = (w.y < shoreTop(w.x)) && (w.x < landEdge(w.y));
    if (w.y >= FARY - 0.004) {
        col = above(w, sunh, sunx, cph, t, high, rain, false, kick);
    } else if (!land) {
        // --- the river ---------------------------------------------------------
        float dz = FARY - w.y;
        float s = 0.10 + dz * 2.6;
        vec2 q = vec2(w.x / s, 1.0 / s);
        float n1 = fbm3(vec2(q.x * 2.0 - flow * 2.0, q.y * 3.0));
        float n2 = fbm3(vec2(q.x * 5.0 - flow * 5.0 + 3.1, q.y * 7.0 + 1.7 + t * 0.05));
        float rip = (n1 - 0.5) + 0.6 * (n2 - 0.5);
        vec2 rw = vec2(w.x + rip * 0.020 * s, FARY + dz * 0.92 + rip * 0.030 * s);
        vec3 refl = above(rw, sunh, sunx, cph, t, high, rain, true, kick);
        vec3 deep = vec3(0.050, 0.115, 0.105) * amb;
        float fres = mix(0.90, 0.50, smoothstep(0.0, 0.50, dz));
        col = mix(deep, refl * 0.90, fres);
        // flow lines drawn out along the current
        float st = smoothstep(0.64, 0.86, fbm3(vec2(q.x * 0.9 - flow * 1.0, q.y * 16.0)));
        col += (hor * 0.35 + 0.03) * st * 0.22 * (1.0 - 0.7 * night);
        // sun glitter under the sun, busier when the highs are
        float g = pow(clamp((n2 - 0.52) / 0.30, 0.0, 1.0), 5.0);
        g *= exp(-abs(w.x - sunx) * (3.0 + 4.0 * dz)) * sunvis * (1.0 - rain * 0.85);
        col += sc * g * (0.9 + 1.2 * high);
        // moon glitter at night
        float mg = pow(clamp((n2 - 0.55) / 0.3, 0.0, 1.0), 6.0) * exp(-abs(w.x - MOONP.x) * 5.0) * night;
        col += vec3(0.55, 0.60, 0.75) * mg * 0.8;
        // foam and shadow where the water meets the near bank
        float de = 1.0;
        if (w.y < SHOREY + 0.01) de = min(de, abs(w.x - landEdge(w.y)));
        if (w.x < SHOREX + 0.02) de = min(de, abs(w.y - shoreTop(w.x)));
        col *= 1.0 - 0.45 * exp(-de * 45.0);
        col += vec3(0.75, 0.80, 0.82) * amb * exp(-de * 380.0) * (0.25 + 0.2 * sin(t * 2.0 + w.x * 60.0));
        // the bulb on the water
        col += WARM * bulb * 0.10 * exp(-length((w - vec2(BULB.x + 0.3, -0.20)) * vec2(1.5, 5.0)) * 3.0);
    } else {
        // --- the near bank ------------------------------------------------------
        float e1 = shoreTop(w.x) - w.y;
        float e2 = landEdge(w.y) - w.x;
        float e = min(e1, e2);
        float n = fbm(w * vec2(12.0, 26.0));
        vec3 grass = mix(vec3(0.20, 0.26, 0.10), vec3(0.36, 0.40, 0.17), n);
        grass *= 0.85 + 0.25 * vnoise(vec2(w.x * 260.0, w.y * 60.0));
        grass *= 0.80 + 0.25 * smoothstep(-0.56, SHOREY, w.y);
        // the plot he clears: dirt spreading out from the house toward the river
        vec2 cc = vec2(-0.22, -0.34);
        vec2 rr = vec2(0.56, 0.20) * (0.25 + 0.75 * clr) * step(0.001, clr);
        float cd = length((w - cc) / max(rr, vec2(1e-3)));
        float edge = 0.90 + 0.22 * (fbm3(w * 14.0) - 0.5);
        float dirt = smoothstep(edge + 0.10, edge - 0.10, cd);
        vec3 soil = vec3(0.40, 0.31, 0.20) * (0.78 + 0.35 * fbm3(w * vec2(40.0, 60.0)));
        vec3 alb = mix(grass, soil, dirt);
        // the bank lip: earth showing where it falls to the water
        float lip = smoothstep(0.022, 0.004, e);
        alb = mix(alb, vec3(0.30, 0.21, 0.13) * (0.8 + 0.3 * fbm3(w * 80.0)), lip);
        alb *= 1.0 - 0.18 * rain;
        col = alb * amb * (0.92 + 0.12 * sunvis);
        // the bulb's pool of light on the ground
        vec2 pd = (w - vec2(BULB.x - 0.02, -0.30)) * vec2(1.0, 2.2);
        col += alb * WARM * bulb * 1.2 / (1.0 + dot(pd, pd) * 55.0);
    }

    // the bulb warms the air around it
    col += WARM * bulb * 0.06 * exp(-length(w - BULB) * 10.0);
    // haze toward the sun (the light the camera sees through the air)
    col += sc * (0.015 + 0.015 * kick) * exp(-length(w - vec2(sunx, FARY + SUNY0 + sunh * SUNYK)) * 1.8) * sunvis;

    // --- the shower ------------------------------------------------------------
    if (rain > 0.01) {
        float r = 0.0;
        r += sheet(uv, 26.0, 0.55, 0.18, 30.0, t) * 0.16;
        r += sheet(uv, 15.0, 0.95, 0.22, 22.0, t) * 0.22;
        r += sheet(uv,  8.5, 1.60, 0.26, 15.0, t) * 0.26;
        col += vec3(0.70, 0.75, 0.82) * r * rain * (0.25 + 0.75 * amb.g);
        col = mix(col, vec3(dot(col, vec3(0.33))), rain * 0.25);
    }

    // --- the cels, and their glow ------------------------------------------------
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

    // --- grade: soft shoulder, cool shadows / warm highlights, vignette, grain -----
    col *= brite;
    float lum = dot(col, vec3(0.2126, 0.7152, 0.0722));
    col += (vec3(-0.010, 0.000, 0.018) * (1.0 - smoothstep(0.0, 0.35, lum))
            + vec3(0.012, 0.004, -0.010) * smoothstep(0.45, 1.0, lum));
    // shoulder on LUMINANCE, so a bright thing gets brighter without changing hue
    float l2 = max(dot(col, vec3(0.2126, 0.7152, 0.0722)), 1e-4);
    float lm = mix(l2, 1.0 - exp(-l2 * 1.3), smoothstep(0.55, 1.3, l2));
    col = col * (lm / l2);
    col = mix(col, vec3(lm), smoothstep(1.0, 1.8, l2) * 0.35);
    col += (hash21(uv * vec2(1920.0, 1080.0) + fract(t)) - 0.5) * 0.012;
    vec2 dd = (uv - 0.5) * vec2(1.777, 1.0);
    col *= 1.0 - vign * 0.55 * dot(dd, dd);
    col *= fade;
    vec3 outc = max(col, vec3(0.0));
    vec3 fallback = mix(skyHor(sunh), skyTop(sunh), uv.y) * 0.8 * fade;
    if (!(outc.r >= 0.0) || !(outc.g >= 0.0) || !(outc.b >= 0.0)) {
        outc = fallback;
    }
    fragColor = TDOutputSwizzle(vec4(outc, 1.0));
}
''')
world.par.pixeldat = world_pix.name
W(render_cels, world, 0)
W(glow_blur, world, 1)
world.par.vec = 4
world.par.vec0name = 'uA'
# the shader's clock is STORY time, which returns to zero every loop: raw time would
# reach 21600 s in six hours and 32-bit float maths on it gets coarse
world.par.vec0valuex.expr = 'parent().par.Showt'
world.par.vec0valuey.expr = 'parent().par.Sunh'
world.par.vec0valuez.expr = 'parent().par.Sunx'
world.par.vec0valuew.expr = 'parent().par.Rainnow'
world.par.vec1name = 'uB'
world.par.vec1valuex.expr = 'parent().par.Flowph'
world.par.vec1valuey.expr = 'parent().par.Cloudph'
world.par.vec1valuez.expr = D('bass')
world.par.vec1valuew.expr = D('high')
world.par.vec2name = 'uC'
world.par.vec2valuex.expr = 'parent().par.Vignette'
world.par.vec2valuey.expr = 'parent().par.Brightness'
# the glow is for what EMITS — the bulb, the window, fireflies — so it is mostly a
# night thing; by day it would only haze the cels
world.par.vec2valuez.expr = ("parent().par.Glow * (0.10 + 0.75 * max(0.0, min(1.0, "
                             "(0.02 - parent().par.Sunh) / 0.37)))")
world.par.vec2valuew.expr = ("parent().par.Label * (0.18 + 0.82 * "
                             "parent().par.Labelfade)")
world.par.vec3name = 'uD'
world.par.vec3valuex.expr = D('kickenv')
world.par.vec3valuey.expr = 'parent().par.Bulb'
world.par.vec3valuez.expr = 'parent().par.Clearp'
world.par.vec3valuew.expr = 'parent().par.Fade'

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
pout.nodeX, pout.nodeY = 400, -2000
s.outputConnectors[0].connect(pout.inputConnectors[0])


# ---------------------------------------------------------------------------
# PADS AND KEYS
# ---------------------------------------------------------------------------
PEXEC_BODY = '''# A chapter is a SEEK: show = musical clock - Timeoffset, so jumping is one
# parameter write and the story plays on from where it lands. The pads do not seek;
# they push a verb into the director's queue.


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
    if n == 'Gust':
        _push(comp, 'gust')
    elif n == 'Fish':
        _push(comp, 'fish')
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
soft(pexec, pars='Gust Fish Reseed Restart Nextcp Prevcp '
     + ' '.join('Go' + cp[0] for cp in CHECKPOINTS),
     valuechange=False, onpulse=True)

KEY_BODY = '''# 1-9 walk the story to a chapter; 0 starts it again.
#   g  GUST   — wind through the grass, and the birds go up out of the tree
#   f  FISH   — one jumps
#   n  RESEED — a new wilderness around the same house


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
    elif k == 'g':
        comp.par.Gust.pulse()
    elif k == 'f':
        comp.par.Fish.pulse()
    elif k == 'n':
        comp.par.Reseed.pulse()
    return


def onShortcut(dat, shortcutName, time):
    return
'''

keyin = C(keyboardinDAT, 'key_pad', 1780, 700)
keyin.par.keys = '1 2 3 4 5 6 7 8 9 0 g f n'
kcb = keyin.par.callbacks.eval()
if kcb is None:
    kcb = C(textDAT, 'key_pad_callbacks', 1780, 620)
    keyin.par.callbacks = kcb.name
kcb.nodeX, kcb.nodeY = 1780, 620
kcb.text = hdr(CHECKPOINTS=CHECKPOINTS) + KEY_BODY

# NO executeDAT KEEP-ALIVE (see bayou/monsoon): pull-based, so unselected on a switch
# this scene costs one Audio Device In tick.

s.par.display = True
s.par.opviewer = final_out.name
s.store('pending', [])

timer.par.initialize.pulse()
timer.par.start.pulse()
director.cook(force=True)
engine.cook(force=True)

for _got, _want, _what in (
        (cam.par.projection.eval(), 'ortho', 'camera projection'),
        (g_cels.par.instancecolormode.eval(), 'replace', 'instance colour mode')):
    if _got != _want:
        print('  [CHECK FAILED] %s is %r, expected %r' % (_what, _got, _want))
if world.warnings():
    print('  [SHADER] %s' % world.warnings())

print('built %s' % s.path)
print('  antialias -> %r | blend %r over %r' % (AA, SRCB, DSTB))
print('  %s' % eng_src.module._S['S']['census'])
print('  keys: 1-9 chapters | 0 restart | g gust | f fish | n reseed')
