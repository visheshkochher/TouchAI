# Bayou — an alligator walks out of a swamp and into a lake, and keeps stopping
# because the world will not stop being interesting.
#
# One continuous side-on journey, left to right, for the whole set. He never turns
# round and there is never a cut: the camera is locked to him and the swamp scrolls
# past. Seven times on the way he finds something — a fern, a dragonfly, a turtle, a
# heron, the lilies, a shoal, and finally the lake itself — and each time he STOPS,
# turns his head, and his eye opens. The stopping is the piece. A creature that
# walks the whole way is a screensaver; a creature that keeps being stopped by what
# it finds is a character.
#
# EVERYTHING IS A STRAIGHT LINE, and every form is built out of a repeated angular
# motif: the back is a row of triangles, a reed is a shaft with a chevron ladder, a
# turtle is a hex lattice, a lily is a nest of concentric hexagons, wonder is a
# stack of rotating n-gons. Nothing in the scene is drawn with a curve. That is the
# aesthetic and it is also why it runs: the whole frame is one instanced unit
# segment with a per-instance transform, exactly as in `as_above`.
#
# THE WATERLINE IS ONE RULE, NOT A FEATURE. A single horizontal world y. Anything
# emitted below it is dimmed, shifted cyan, and horizontally sheared by the local
# surface displacement; anything above it is mirrored through it at low alpha with a
# moving shimmer. One rule, applied at emit time to every segment in the scene, is
# what makes wading work: as the bank falls away his legs go quiet, then his belly,
# and by the lake only the scute ridge and one eye are still bright. Nothing had to
# be written to make him "enter the water".
#
# AUDIO. Musical time carries the journey (the walk is in beats, not seconds, so he
# steps on the track). Kicks drop ripple rings into the water from under his feet
# and beat the wonder n-gons outward. Bass sways the reeds and swells the mist.
# Highs are the fine stuff — motes, wing beats, surface glints. A bass DROP is what
# actually reveals each discovery: the schedule only arms the window.
#
# Idempotent: destroys and recreates /project1/bayou and its project-level Out TOP.
# No media files needed.
#     code = open('scenes/bayou/build.py', encoding='utf-8').read()
#     g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)

import math
import os

SCENE = 'bayou'
OUTW, OUTH = 1280, 720
ASPECT = OUTW / OUTH
ORTHOW = 2.0
ORTHOH = ORTHOW / ASPECT
CLOCKLEN = 60.0

STORYDEF = 330.0
MAXSEG = 5000            # instance pool; fixed, never resized. Measured peak
                         # over a full dry-run pass is 2890, so this is ~1.7x headroom.
TOTALX = 24.0            # world units walked from the first reed to the open lake
WATERY = -0.090          # the one waterline, in world y
GATORX = -0.30           # where on screen he sits. Left of centre: we watch what is
                         # ahead of him, which is the whole point of the piece.
GSCALE = 0.70            # body length, world units

# The seven things he finds. `f` is where in the story he stops, `dwell` is how much
# of the story he spends stopped. The speed profile is derived from these and nothing
# else, so moving a discovery moves the walk with it and the two can never disagree.
DISCOVERIES = [
    dict(key='fern',   name='A FERN',      kind='fern',   f=0.115, dwell=0.055,
         col=(0.42, 1.00, 0.62), y=-0.048, sc=1.15, ahead=0.46),
    dict(key='dragon', name='A DRAGONFLY', kind='dragon', f=0.245, dwell=0.050,
         col=(0.52, 0.92, 1.00), y=0.265, sc=0.95, ahead=0.42),
    dict(key='turtle', name='A TURTLE',    kind='turtle', f=0.370, dwell=0.055,
         col=(1.00, 0.78, 0.38), y=0.045, sc=1.00, ahead=0.50),
    dict(key='heron',  name='A HERON',     kind='heron',  f=0.495, dwell=0.060,
         col=(0.72, 0.87, 1.00), y=0.075, sc=0.95, ahead=0.56),
    dict(key='lilies', name='THE LILIES',  kind='lilies', f=0.620, dwell=0.055,
         col=(1.00, 0.62, 0.86), y=-0.076, sc=1.10, ahead=0.50),
    dict(key='shoal',  name='A SHOAL',     kind='shoal',  f=0.745, dwell=0.055,
         col=(0.74, 0.92, 1.00), y=-0.178, sc=1.05, ahead=0.40),
    dict(key='moon',   name='THE LAKE',    kind='moon',   f=0.880, dwell=0.075,
         col=(1.00, 0.95, 0.80), y=0.330, sc=1.05, ahead=0.28, hold=True),
]

CHECKPOINTS = [
    ('swamp',  ' 1 - Into the Swamp',   0.000),
    ('fern',   ' 2 - The Fern',         0.086),
    ('dragon', ' 3 - The Dragonfly',    0.216),
    ('turtle', ' 4 - The Turtle',       0.341),
    ('heron',  ' 5 - The Heron',        0.466),
    ('lilies', ' 6 - The Lilies',       0.591),
    ('shoal',  ' 7 - The Shoal',        0.716),
    ('lake',   ' 8 - Into the Lake',    0.851),
    ('still',  ' 9 - Stillness',        0.958),
]

proj = op('/project1')
for stale in (SCENE, SCENE + '_out'):
    o = proj.op(stale)
    if o:
        o.destroy()

s = proj.create(containerCOMP, SCENE)
s.nodeX, s.nodeY = 0, -1100
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


def hdr(**kw):
    return ''.join('%s = %r\n' % (k, v) for k, v in sorted(kw.items())) + '\n'


# ---------------------------------------------------------------------------
# PERFORMANCE SURFACE
# ---------------------------------------------------------------------------
pg = s.appendCustomPage('Bayou')
pg.appendMenu('Audiosrc', label='Audio Source')
s.par.Audiosrc.menuNames = ['device', 'file']
s.par.Audiosrc.menuLabels = ['Audio Device In', 'Audio File In (test)']
s.par.Audiosrc = 'file'

for nm, label, val, lo, hi in [
    ('Reactivity', 'Reactivity',          1.0, 0.0, 3.0),
    ('Devgain',    'Device In Gain',      6.0, 1.0, 30.0),
    ('Storylen',   'Journey Length (s)', STORYDEF, 90.0, 2400.0),
    ('Refbpm',     'Reference BPM',     124.0, 60.0, 200.0),
    ('Beatdrive',  'Beat Drive',          1.0, 0.0, 1.0),
    ('Timeoffset', 'Time Offset (s)',     0.0, -600.0, 3000.0),
    ('Wonder',     'Amazement',           1.0, 0.0, 2.0),
    ('Ripple',     'Water Response',      1.0, 0.0, 3.0),
    ('Sway',       'Reed Sway',           1.0, 0.0, 3.0),
    ('Density',    'Swamp Density',       1.0, 0.3, 1.6),
    ('Linewidth',  'Line Width (px)',     1.40, 0.6, 5.0),
    ('Ink',        'Line Brightness',     1.10, 0.0, 3.0),
    ('Reflect',    'Reflections',         1.0, 0.0, 2.0),
    ('Mist',       'Mist',                1.0, 0.0, 2.0),
    ('Glow',       'Glow',                1.0, 0.0, 3.0),
    ('Shockamt',   'Drop Shock',          0.55, 0.0, 3.0),
    ('Label',      'Chapter Readout',     1.0, 0.0, 2.0),
    ('Vignette',   'Vignette',            0.80, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

pg.appendToggle('Dropfire', label='Drops Reveal the Discovery')
s.par.Dropfire.default = True
s.par.Dropfire.val = True

for _mn, _ml, _lo, _hi in (('Bpm', 'Detected BPM', 0.0, 200.0),
                           ('Showt', 'Story Time (s)', 0.0, 2400.0),
                           ('Walkx', 'Distance Walked', 0.0, TOTALX),
                           ('Chapter', 'Chapter', 0.0, float(len(CHECKPOINTS))),
                           ('Wonderm', 'Amazement Level', 0.0, 1.0),
                           ('Segs', 'Lines Drawn', 0.0, float(MAXSEG)),
                           ('Labelfade', 'Readout Fade', 0.0, 1.0),
                           ('Shock', 'Shock', 0.0, 1.0),
                           ('Bassm', 'Bass Level', 0.0, 1.0),
                           ('Highm', 'High Level', 0.0, 1.0),
                           ('Energym', 'Energy Level', 0.0, 1.0)):
    pg.appendFloat(_mn, label=_ml)
    _p = getattr(s.par, _mn)
    _p.normMin, _p.normMax = _lo, _hi
    _p.readOnly = True

pg.appendStr('Scaletxt', label='Chapter Text')
s.par.Scaletxt.readOnly = True
s.par.Scaletxt.val = ''

pg.appendPulse('Look', label='L - LOOK (make him notice, anywhere)')
pg.appendPulse('Startle', label='G - STARTLE (gust: everything bends)')
pg.appendPulse('Reseed', label='N - RESEED (new swamp, same journey)')
pg.appendPulse('Restart', label='0 - RESTART')
pg.appendPulse('Nextcp', label='next chapter')
pg.appendPulse('Prevcp', label='previous chapter')

for cp, label, _f in CHECKPOINTS:
    pg.appendPulse('Go' + cp, label=label)
# ---------------------------------------------------------------------------
# AUDIO FRONT END — verbatim from scenes/dispersal/build.py. SEVENTH copy, and the
# debt is now large enough to be worth naming again: seven scenes carry the same 270
# lines, so a fix to the drop detector is seven edits. It should be one shared .tox
# that every scene references; this scene was not the moment to stop and do it.
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
# TEMPO + DROP
# ---------------------------------------------------------------------------
TEMPO_BODY = '''# Beat detector, tempo estimator and drop detector.
import numpy as np
#
# A BEAT is a transient: positive flux (the RISE of a dedicated kick band) against an
# EMA of that flux. A DROP is the opposite, it is SUSTAIN: the wide bass band sitting
# well above its own recent median for several frames running. Comparing level against
# an EMA of level does not find either, because the envelope is already smooth and its
# baseline sits at roughly the height of the signal.

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

    # TEMPO: autocorrelation of the onset envelope, not clustering of intervals.
    # Clustering is too fragile — one missed beat contributes a double-length interval
    # and one spurious onset a half-length one, both inside the accepted range, and the
    # estimate jumps between them. Autocorrelating ~7s uses every onset at once, and
    # the harmonic sum (a lag scored with its 2x and 3x lags) picks the fundamental.
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

    # OCTAVE FOLD, so a double-time lock does not run the ladder at 2x.
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

    scriptOp.clear()
    names = ('factor', 'bpm', 'beat', 'beatstr', 'drop', 'bassmed')
    chans = [scriptOp.appendChan(n) for n in names]
    scriptOp.numSamples = 1
    vals = (factor, bpm if (st['seen'] and not quiet) else 0.0, beat, beatstr,
            drop, med)
    for c, v in zip(chans, vals):
        c[0] = v
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
tempo.par.callbacks = tempo_src.path
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
DIRECTOR_BODY = '''# Musical time is monotonic and never seeks. The PLAYHEAD is a subtraction from it
# (show = musical - Timeoffset), so a checkpoint jump is one parameter write and the
# story carries on playing from wherever it lands — nothing is ever paused, and there
# is no second clock that can drift out of agreement with the first.
#
# Discrete events are MONOTONIC COUNTERS, never one-frame flags. A flag is lost if
# the engine cooks twice in a frame or not at all; a counter read as a delta is not.
import math

_clock = {'last_raw': None, 'musical': 0.0}
_st = {'peak': {'bass': PEAKFLOOR, 'high': PEAKFLOOR, 'energy': PEAKFLOOR},
       'kickenv': 0.0, 'kickslow': 0.0, 'dropenv': 0.0,
       'look': 0, 'gust': 0, 'reseed': 0,
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
        st['kickenv'] *= 0.5 ** (dt / 0.15)
        st['kickslow'] *= 0.5 ** (dt / 0.55)
        st['dropenv'] *= 0.5 ** (dt / 0.95)
    # Counters, not flags. Every visual that must happen exactly once per beat —
    # a ripple dropped in the water, an n-gon of amazement leaving a creature —
    # reads a counter delta, so it survives a frame the engine did not cook.
    if kick > 0.5:
        st['kickenv'] = 1.0
        st['kickslow'] = 1.0
        st['kicks'] += 1
        if beatstr >= ACCENT:
            st['accents'] += 1
    if drop > 0.5:
        st['dropenv'] = 1.0
        st['drops'] += 1

    # Phase-lock, never snap. A snap visibly jerks every envelope in the scene at
    # once the moment the detector hiccups; a fractional pull is invisible.
    if kick > 0.5 and float(par.Beatdrive.eval()) > 0.01:
        period = 60.0 / max(1.0, float(par.Refbpm.eval()))
        phase = _clock['musical'] % period
        err = phase if phase < period * 0.5 else phase - period
        _clock['musical'] -= err * BEATLOCK * float(par.Beatdrive.eval())
        musical = _clock['musical']

    # The playhead is CLAMPED, not wrapped: the lake at the end stays until someone
    # seeks back to the swamp. A journey that silently restarts is not a journey.
    slen = max(1.0, float(par.Storylen.eval()))
    show = min(slen, max(0.0, musical - float(par.Timeoffset.eval())))

    pending = comp.fetch('pending', None)
    if pending:
        comp.store('pending', [])
        for what in pending:
            if what == 'look':
                st['look'] += 1
            elif what == 'gust':
                st['gust'] += 1
                st['dropenv'] = 1.0
            elif what == 'reseed':
                st['reseed'] += 1

    out = {
        'rawtime': raw, 'musical': musical, 'show': show, 'tempofactor': factor,
        'bass': bass, 'high': high, 'energy': energy,
        'kick': kick, 'kickenv': st['kickenv'], 'kickslow': st['kickslow'],
        'beatstr': beatstr, 'drop': drop, 'dropenv': st['dropenv'],
        'accent': 1.0 if (kick > 0.5 and beatstr >= ACCENT) else 0.0,
        'lookcnt': float(st['look']), 'gustcnt': float(st['gust']),
        'reseedcnt': float(st['reseed']), 'kickcnt': float(st['kicks']),
        'accentcnt': float(st['accents']), 'dropcnt': float(st['drops']),
        'storylen': slen,
    }

    scriptOp.clear()
    keys = sorted(out.keys())
    chans = [scriptOp.appendChan(k) for k in keys]
    scriptOp.numSamples = 1
    for c, k in zip(chans, keys):
        c[0] = out[k]

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
director.par.callbacks = dir_src.path
W(timer, director, 0)
W(null_audio, director, 1)
W(tempo, director, 2)


def D(ch):
    return "(op('director')['%s'] or 0)" % ch


# ---------------------------------------------------------------------------
# THE ENGINE — the swamp, the animal, and the one waterline rule
# ---------------------------------------------------------------------------
ENGINE_BODY = r'''# Everything you see is emitted from here as line segments in world coordinates and
# handed to one instanced unit segment. Three kinds of geometry, and they are kept
# apart on purpose:
#
#   STATIC   the swamp itself — reeds, cypress, vines, bank, logs, lilies. Built ONCE
#            into numpy arrays at reseed, then per frame only translated by the
#            camera, culled by a binary search, swayed, and emitted. This is what
#            makes a 24-world-unit swamp free.
#   ANIMAL   the alligator, ~150 segments rebuilt in Python every frame. Small enough
#            that Python is the right tool and the legibility is worth it.
#   MOMENT   the discovery on screen, the n-gons of amazement, ripples, motes, mist.
#
# THE ONE RULE. At the very end, every segment whose midpoint is below WATERY is
# dimmed, pushed cyan, and sheared sideways by the local surface displacement; every
# reflectable segment above it is mirrored through it. That is all "he walks into the
# lake" is. Nothing in the animal code knows about water.
import math
import random
import numpy as np

_S = {'S': None}
CG = np.array(CGATOR, dtype=np.float64)
CG2 = np.array(CGATOR2, dtype=np.float64)
CW = np.array(CWONDER, dtype=np.float64)


def _ss(a, b, x):
    t = (x - a) / (b - a if b != a else 1e-9)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return t * t * (3.0 - 2.0 * t)


def _sv(a, b, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a if b != a else 1e-9),
                0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# --- the terrain ----------------------------------------------------------------
# One closed-form function, used by the bank geometry, by the animal's feet, and by
# the water mask. There is no terrain array anywhere, so they cannot disagree.
def ground(wx):
    wx = np.asarray(wx, dtype=np.float64)
    p = np.clip(wx / TOTALX, -0.2, 1.4)
    base = WATERY - 0.462 * _sv(0.40, 0.96, p)
    damp = np.clip(1.0 - 0.58 * p, 0.22, 1.0)
    u = (0.036 * np.sin(wx * 1.73 + 0.4) + 0.022 * np.sin(wx * 3.91 + 2.1)
         + 0.013 * np.sin(wx * 7.30 + 1.0)) * damp
    return base + u


def groundf(wx):
    return float(ground(np.array([wx]))[0])


# --- the walk -------------------------------------------------------------------
# Distance is a function of story FRACTION, not of seconds, so Journey Length can be
# swept live without the animal teleporting. The speed profile is derived from the
# discovery schedule and nothing else: he is stopped where and only where there is
# something to look at.
def _plateau(f, c, d):
    h, sh = d * 0.5, d * 0.45
    return _sv(c - h - sh, c - h, f) * (1.0 - _sv(c + h, c + h + sh, f))


NS = 3001
FTAB = np.linspace(0.0, 1.0, NS)
_sp = np.ones(NS)
for _d in DISCOVERIES:
    _sp = _sp * (1.0 - 0.955 * _plateau(FTAB, _d['f'], _d['dwell']))
_sp *= 0.22 + 0.78 * _sv(0.0, 0.035, FTAB)        # he starts out of the dark
_sp *= 1.0 - 0.78 * _sv(0.930, 1.0, FTAB)          # and coasts to a stop on the lake
XTAB = np.concatenate([[0.0], np.cumsum((_sp[1:] + _sp[:-1]) * 0.5 / (NS - 1.0))])
XTAB *= TOTALX / max(XTAB[-1], 1e-9)
DPOS = [float(np.interp(d['f'], FTAB, XTAB)) + d['ahead'] for d in DISCOVERIES]


def walkx(f):
    return float(np.interp(f, FTAB, XTAB))


# --- prop generators ------------------------------------------------------------
# Each returns segments in local coordinates with the base at the origin, as
# (x0, y0, x1, y1, kind). kind 1 is detail and draws dimmer, which is the whole
# reason the fine work does not out-shout the shape it decorates.
def _reed(rs, h, lean):
    segs, n = [], 6
    pts = [(lean * h * (i / n) ** 1.7, h * (i / n)) for i in range(n + 1)]
    for i in range(n):
        segs.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 0))
    for i in range(1, n):
        x, y = pts[i]
        w = h * 0.085 * (1.0 - i / float(n)) + h * 0.022
        segs.append((x, y, x - w, y - w * 1.15, 1))
        segs.append((x, y, x + w * 0.85, y - w * 1.15, 1))
    return segs


def _cypress(rs, h):
    segs = []
    w0 = h * 0.045
    lean = rs.uniform(-0.09, 0.09)
    n = 5
    pts = [(lean * h * (i / n) ** 1.4, h * (i / n)) for i in range(n + 1)]
    for i in range(n):
        for sgn in (-1.0, 1.0):
            t0 = w0 * (1.0 - i / float(n + 1)) * sgn
            t1 = w0 * (1.0 - (i + 1) / float(n + 1)) * sgn
            segs.append((pts[i][0] + t0, pts[i][1], pts[i + 1][0] + t1,
                         pts[i + 1][1], 0))
    # a rigid symmetric fractal: branch pairs, shorter and flatter as they climb
    for i in range(1, n + 1):
        u = i / float(n)
        L = h * 0.30 * (1.0 - u * 0.58)
        ang = 0.95 - 0.42 * u
        for sgn in (-1.0, 1.0):
            bx, by = pts[i]
            ex = bx + sgn * L * math.cos(ang)
            ey = by + L * math.sin(ang)
            segs.append((bx, by, ex, ey, 0))
            for k in (0.42, 0.72):
                mx, my = bx + (ex - bx) * k, by + (ey - by) * k
                segs.append((mx, my, mx + sgn * L * 0.26,
                             my + L * 0.34, 1))
    # buttress roots — the V's that say cypress and nothing else
    for sgn in (-1.0, 1.0):
        for k in (0.5, 1.0):
            segs.append((0.0, h * 0.10 * k, sgn * h * 0.11 * k, 0.0, 1))
    return segs


def _vine(rs, L):
    segs, n = [], 7
    x = 0.0
    pts = [(0.0, 0.0)]
    for i in range(n):
        x += rs.uniform(-0.018, 0.018)
        pts.append((x, -L * (i + 1) / n))
    for i in range(n):
        segs.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 0))
    for i in range(1, n + 1):
        x, y = pts[i]
        w = L * 0.055
        segs.append((x - w, y + w * 0.4, x + w, y - w * 0.4, 1))
    return segs


def _tuft(rs, h):
    segs = []
    for i in range(6):
        a = math.radians(rs.uniform(52.0, 128.0))
        L = h * rs.uniform(0.55, 1.0)
        segs.append((0.0, 0.0, L * math.cos(a), L * math.sin(a), 0))
    return segs


def _log(rs, L):
    t = L * 0.085
    segs = [(0.0, t, L, t * 0.72, 0), (0.0, -t, L, -t * 0.72, 0),
            (0.0, t, 0.0, -t, 0), (L, t * 0.72, L, -t * 0.72, 0)]
    for k in (0.25, 0.5, 0.75):
        segs.append((L * k, t * (1 - 0.28 * k), L * k, -t * (1 - 0.28 * k), 1))
    return segs


def _rock(rs, r):
    n = 5
    a0 = rs.uniform(0.0, 1.2)
    pts = [(r * math.cos(a0 + i * 2 * math.pi / n) * rs.uniform(0.75, 1.15),
            r * 0.62 * math.sin(a0 + i * 2 * math.pi / n) * rs.uniform(0.75, 1.15)
            + r * 0.45) for i in range(n)]
    segs = [(pts[i][0], pts[i][1], pts[(i + 1) % n][0], pts[(i + 1) % n][1], 0)
            for i in range(n)]
    segs.append((pts[0][0], pts[0][1], pts[2][0], pts[2][1], 1))
    return segs


def _pad(rs, r):
    # A lily pad is concentric hexagons with spokes and one notch. Flat, at water
    # level, so it also reads as a ring on the surface.
    segs, n = [], 6
    a0 = rs.uniform(0.0, 1.0)
    for k, rr in ((0, 1.0), (1, 0.62), (1, 0.30)):
        for i in range(n):
            a1 = a0 + i * 2 * math.pi / n
            a2 = a0 + (i + 1) * 2 * math.pi / n
            if i == 0 and rr > 0.9:
                continue                      # the notch
            segs.append((r * rr * math.cos(a1), r * rr * 0.30 * math.sin(a1),
                         r * rr * math.cos(a2), r * rr * 0.30 * math.sin(a2), k))
    for i in range(1, n):
        a1 = a0 + i * 2 * math.pi / n
        segs.append((0.0, 0.0, r * math.cos(a1), r * 0.30 * math.sin(a1), 1))
    return segs


def _stump(rs, h):
    w = h * 0.34
    segs = [(-w, 0.0, -w * 0.78, h, 0), (w, 0.0, w * 0.78, h, 0),
            (-w * 0.78, h, w * 0.78, h, 0)]
    for k in (0.3, 0.55, 0.8):
        segs.append((-w * (1 - 0.22 * k), h * k, w * (1 - 0.22 * k) * 0.6,
                     h * k * rs.uniform(0.9, 1.1), 1))
    return segs


# --- building the swamp ---------------------------------------------------------
def _pack(items):
    """items: list of (segs, ox, oy, scale, swaymode, h, col, alpha, refl)"""
    X0, Y0, X1, Y1, S0, S1, R, G, B, A, ZZ, RF = ([] for _ in range(12))
    for segs, ox, oy, sc, mode, h, col, al, refl, zz in items:
        for (x0, y0, x1, y1, kind) in segs:
            ax0, ay0 = ox + x0 * sc, oy + y0 * sc
            ax1, ay1 = ox + x1 * sc, oy + y1 * sc
            hh = max(h * sc, 1e-4)
            if mode > 0:      # rooted at the bottom: the tip moves, the base does not
                s0 = min(1.0, max(0.0, (ay0 - oy) / hh)) ** 1.35
                s1 = min(1.0, max(0.0, (ay1 - oy) / hh)) ** 1.35
            elif mode < 0:    # hanging: the far end swings
                s0 = min(1.0, max(0.0, (oy - ay0) / hh)) ** 1.15
                s1 = min(1.0, max(0.0, (oy - ay1) / hh)) ** 1.15
            else:
                s0 = s1 = 0.0
            a = al * (DETAILDIM if kind else 1.0)
            X0.append(ax0); Y0.append(ay0); X1.append(ax1); Y1.append(ay1)
            S0.append(s0); S1.append(s1)
            R.append(col[0]); G.append(col[1]); B.append(col[2])
            A.append(a); ZZ.append(zz); RF.append(refl)
    n = len(X0)
    if not n:
        return None
    k = np.argsort(np.minimum(np.array(X0), np.array(X1)))
    f = lambda L: np.array(L, dtype=np.float64)[k]
    return dict(x0=f(X0), y0=f(Y0), x1=f(X1), y1=f(Y1), s0=f(S0), s1=f(S1),
                r=f(R), g=f(G), b=f(B), a=f(A), z=f(ZZ), refl=f(RF),
                key=np.minimum(f(X0), f(X1)))


def _layer_far(rs):
    items, x, p = [], -2.0, PFAR
    span = TOTALX * p + 3.0
    while x < span:
        prog = min(1.3, (x / p) / TOTALX)
        # the far bank thins out as the lake opens, but never empties: a horizon
        # with nothing on it stops reading as distance and starts reading as void
        keep = 1.0 - 0.72 * _ss(0.40, 0.92, prog)
        if rs.random() < keep:
            h = rs.uniform(0.34, 0.62)
            items.append((_cypress(rs, 1.0), x, WATERY + rs.uniform(-0.01, 0.03),
                          h, 1, 1.0, CFAR, 0.26, 0.0, -0.45))
        x += rs.uniform(0.36, 0.62)
    x = -2.0
    while x < span:
        prog = min(1.3, (x / p) / TOTALX)
        if rs.random() < 1.0 - 0.80 * _ss(0.35, 0.88, prog):
            h = rs.uniform(0.09, 0.19)
            items.append((_reed(rs, 1.0, rs.uniform(-0.2, 0.2)), x,
                          WATERY + rs.uniform(-0.015, 0.02), h, 1, 1.0,
                          CFAR, 0.20, 0.0, -0.44))
        x += rs.uniform(0.058, 0.125)
    return _pack(items)


def _layer_mid(rs):
    items, x, p = [], -2.0, PMID
    span = TOTALX * p + 3.0
    while x < span:
        prog = min(1.3, (x / p) / TOTALX)
        open_ = _ss(0.38, 0.90, prog)
        if rs.random() < 1.0 - 0.86 * open_:
            for _ in range(rs.randint(2, 4)):
                h = rs.uniform(0.14, 0.40)
                items.append((_reed(rs, 1.0, rs.uniform(-0.28, 0.28)),
                              x + rs.uniform(-0.05, 0.05),
                              WATERY + rs.uniform(-0.03, 0.04), h, 1, 1.0,
                              CMID, 0.48, 1.0, -0.25))
        if rs.random() < 0.20 * (1.0 - open_):
            items.append((_vine(rs, 1.0), x + rs.uniform(-0.1, 0.1),
                          rs.uniform(0.36, 0.56), rs.uniform(0.14, 0.34),
                          -1, 1.0, CMID, 0.32, 0.0, -0.24))
        x += rs.uniform(0.21, 0.40)
    return _pack(items)


def _layer_near(rs):
    items, x = [], -1.5
    span = TOTALX + 3.0
    while x < span:
        prog = min(1.3, x / TOTALX)
        open_ = _ss(0.36, 0.88, prog)
        gy = groundf(x)
        dry = gy > WATERY - 0.004
        if dry and rs.random() < 1.0 - 0.90 * open_:
            for _ in range(rs.randint(1, 3)):
                # biased short: a reed as tall as he is reads as camouflage, and
                # the one thing the frame must never lose is the animal
                h = 0.065 + 0.245 * rs.random() ** 1.9
                hue = rs.uniform(-0.09, 0.09)
                cc = (CREED[0] + hue * 0.5, CREED[1] - abs(hue) * 0.25,
                      CREED[2] - hue)
                items.append((_reed(rs, 1.0, rs.uniform(-0.34, 0.34)),
                              x + rs.uniform(-0.06, 0.06), gy, h, 1, 1.0,
                              cc, 0.86, 1.0, 0.0))
        if dry and rs.random() < 0.34 * (1.0 - open_):
            items.append((_tuft(rs, 1.0), x + rs.uniform(-0.08, 0.08), gy,
                          rs.uniform(0.045, 0.10), 1, 1.0, CREED, 0.62, 1.0, 0.01))
        if dry and rs.random() < 0.10:
            items.append((_rock(rs, 1.0), x, gy, rs.uniform(0.035, 0.075), 0,
                          1.0, CGROUND, 0.55, 1.0, 0.01))
        if rs.random() < 0.055 and prog < 0.86:
            items.append((_log(rs, 1.0), x, max(gy, WATERY) + 0.012,
                          rs.uniform(0.22, 0.44), 0, 1.0, CGROUND, 0.66, 1.0, 0.02))
        if dry and rs.random() < 0.05 and prog < 0.8:
            items.append((_stump(rs, 1.0), x, gy, rs.uniform(0.10, 0.20), 1,
                          1.0, CGROUND, 0.60, 1.0, 0.01))
        # lilies arrive with the open water and stay for the rest of the journey
        if (not dry) and rs.random() < 0.30 * _ss(0.45, 0.70, prog):
            items.append((_pad(rs, 1.0), x + rs.uniform(-0.15, 0.15),
                          WATERY + 0.002, rs.uniform(0.045, 0.095), 0, 1.0,
                          CPAD, 0.50, 0.0, 0.03))
        x += rs.uniform(0.19, 0.34)
    return _pack(items)


def _layer_fore(rs):
    items, x, p = [], -2.0, PFORE
    span = TOTALX * p + 3.0
    while x < span:
        prog = min(1.3, (x / p) / TOTALX)
        if rs.random() < 1.0 - 0.72 * _ss(0.40, 0.92, prog):
            h = rs.uniform(0.34, 0.82)
            items.append((_reed(rs, 1.0, rs.uniform(-0.30, 0.30)), x,
                          WATERY - rs.uniform(0.02, 0.10), h, 1, 1.0,
                          CFORE, 0.42, 0.0, 0.40))
        x += rs.uniform(0.34, 0.85)
    return _pack(items)


def _layer_bank(rs):
    """The bank itself: a faceted ground line, hatching under it, and two dashed
    strata below that. Flat colour, parallax 1, and it is the only thing in the
    scene the animal's feet are allowed to touch."""
    items = []
    step = 0.082
    xs = np.arange(-1.6, TOTALX + 3.0, step)
    gs = ground(xs)
    segs = [(float(xs[i]), float(gs[i]), float(xs[i + 1]), float(gs[i + 1]), 0)
            for i in range(len(xs) - 1)]
    items.append((segs, 0.0, 0.0, 1.0, 0, 1.0, CGROUND, 0.70, 1.0, 0.05))
    hatch = []
    for i in range(0, len(xs) - 1, 2):
        x, y = float(xs[i]), float(gs[i])
        L = rs.uniform(0.028, 0.085)
        hatch.append((x, y, x - L * 0.42, y - L, 1))
    items.append((hatch, 0.0, 0.0, 1.0, 0, 1.0, CGROUND, 0.52, 0.0, 0.05))
    # roots: three-segment zigzags dropped off the bank, so the earth has a grain
    roots = []
    for i in range(0, len(xs) - 1, 7):
        x, y = float(xs[i]), float(gs[i])
        px, py = x, y
        for k in range(3):
            nx = px + rs.uniform(-0.030, 0.030)
            ny = py - rs.uniform(0.030, 0.075)
            roots.append((px, py, nx, ny, 1))
            px, py = nx, ny
    items.append((roots, 0.0, 0.0, 1.0, 0, 1.0, CGROUND, 0.40, 0.0, 0.055))
    # strata: dashed rules that flatten as they go down, because what is under the
    # swamp is the same claim the rest of the piece makes — repeated angular motif
    for k, (depth, dash, al) in enumerate(((0.048, 4, 0.60), (0.098, 5, 0.52),
                                           (0.158, 6, 0.44), (0.228, 7, 0.36),
                                           (0.308, 8, 0.28), (0.398, 9, 0.22))):
        st = []
        flat = 1.0 - 0.15 * k
        for i in range(0, len(xs) - 1, dash):
            j = min(len(xs) - 2, i + min(4, max(2, dash - 2)))
            y0 = (float(gs[i]) - WATERY) * flat + WATERY - depth
            y1 = (float(gs[j]) - WATERY) * flat + WATERY - depth
            st.append((float(xs[i]), y0, float(xs[j]), y1, 1 if k > 1 else 0))
        items.append((st, 0.0, 0.0, 1.0, 0, 1.0, CGROUND, al, 0.0, 0.06))
    return _pack(items)


# --- drawing primitives for the per-frame geometry --------------------------------
# A segment is (x0, y0, x1, y1, r, g, b, a, z, exempt). `exempt` means "the waterline
# rule has already been applied to me" — only reflections ever set it.
def _L(out, x0, y0, x1, y1, col, a, z=0.0, fl=0.0):
    out.append((x0, y0, x1, y1, col[0], col[1], col[2], a, z, fl))


def _P(out, pts, col, a, z=0.0, fl=0.0):
    for i in range(len(pts) - 1):
        out.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                    col[0], col[1], col[2], a, z, fl))


def _NG(out, cx, cy, r, n, rot, col, a, z=0.0, fl=0.0, ry=None):
    ry = r if ry is None else ry
    pts = [(cx + r * math.cos(rot + i * 2.0 * math.pi / n),
            cy + ry * math.sin(rot + i * 2.0 * math.pi / n)) for i in range(n + 1)]
    _P(out, pts, col, a, z, fl)


def _mix(c1, c2, k):
    return (c1[0] + (c2[0] - c1[0]) * k, c1[1] + (c2[1] - c1[1]) * k,
            c1[2] + (c2[2] - c1[2]) * k)


def _ik(out, hx, hy, fx, fy, l1, l2, sgn, col, a, z):
    # Two links and a knee. The foot is pulled back inside reach rather than left
    # where it was asked for: a leg drawn to an unreachable target is a leg that
    # visibly stretches, and one stretched leg reads as a broken rig.
    dx, dy = fx - hx, fy - hy
    raw = max(math.hypot(dx, dy), 1e-6)
    ux, uy = dx / raw, dy / raw
    d = min(max(raw, 0.012), l1 + l2 - 0.002)
    fx, fy = hx + ux * d, hy + uy * d
    aa = (l1 * l1 - l2 * l2 + d * d) / (2.0 * d)
    hh = math.sqrt(max(0.0, l1 * l1 - aa * aa))
    kx = hx + ux * aa - uy * hh * sgn
    ky = hy + uy * aa + ux * hh * sgn
    _L(out, hx, hy, kx, ky, col, a, z)
    _L(out, kx, ky, fx, fy, col, a, z)
    return fx, fy


# --- the alligator --------------------------------------------------------------
NB = 15
_UU = [i / float(NB - 1) for i in range(NB)]
_HKU = [0.00, 0.10, 0.22, 0.36, 0.52, 0.66, 0.76, 0.88, 1.00]
_HKH = [0.005, 0.036, 0.072, 0.102, 0.116, 0.106, 0.086, 0.066, 0.052]


def _gator(out, bx, by, pitch, gp, swim, wonder, gaze, kickenv, high, t, ink,
           feet_out):
    ca, sa = math.cos(pitch), math.sin(pitch)

    def T(x, y):
        x *= GSCALE
        y *= GSCALE
        return (bx + x * ca - y * sa, by + x * sa + y * ca)

    taA = 0.030 + 0.105 * swim + 0.022 * kickenv
    bob = 0.013 * math.sin(4.0 * math.pi * gp) * (1.0 - 0.7 * swim)
    swimph = t * (1.1 + 0.5 * swim)

    def yc(u):
        w = taA * (max(0.0, (0.44 - u) / 0.44) ** 1.7)
        ph = (2.0 * math.pi * gp) if swim < 0.5 else (2.0 * math.pi * swimph)
        return bob + w * math.sin(ph - 5.0 * u)

    xs = [-0.62 + 0.92 * u for u in _UU]
    ys = [yc(u) for u in _UU]
    hs = [float(np.interp(u, _HKU, _HKH)) for u in _UU]

    back = [T(xs[i], ys[i] + hs[i]) for i in range(NB)]
    belly = [T(xs[i], ys[i] - hs[i]) for i in range(NB)]
    _P(out, back, CGATOR, ink)
    _P(out, belly[:NB - 1], CGATOR, ink * 0.95)
    for i in range(1, NB - 1, 2):
        _L(out, back[i][0], back[i][1], belly[i][0], belly[i][1],
           CGATOR, ink * 0.34 * DETAILDIM)

    # THE RIDGE. A row of triangles standing on the spine, and the one place the
    # amazement is allowed to change his colour: a warm crest runs head-to-tail
    # while he is looking at something.
    for i in range(1, NB - 1):
        u = _UU[i]
        sh = (0.020 + 0.038 * hs[i] / 0.098) * (1.0 + 0.40 * kickenv
                                                + 0.25 * wonder)
        mx = (xs[i] + xs[i + 1]) * 0.5
        my = (ys[i] + ys[i + 1]) * 0.5 + (hs[i] + hs[i + 1]) * 0.5
        apex = T(mx, my + sh)
        warm = wonder * max(0.0, math.sin(2.0 * math.pi * (u * 0.85 - t * 0.42)))
        col = _mix(CGATOR, CGATOR2, min(1.0, warm))
        _L(out, back[i][0], back[i][1], apex[0], apex[1], col,
           ink * (0.80 + 0.5 * warm))
        _L(out, apex[0], apex[1], back[i + 1][0], back[i + 1][1], col,
           ink * (0.80 + 0.5 * warm))

    # --- legs, solved in world space so the feet actually meet the bank ----------
    stride = 0.148
    duty = 0.62
    tuck = swim
    for (uh, off, near, sgn) in ((0.848, 0.00, 1.0, -1.0), (0.848, 0.50, 0.0, -1.0),
                                 (0.391, 0.25, 0.0, 1.0), (0.391, 0.75, 1.0, 1.0)):
        i = uh * (NB - 1)
        i0, fr = int(i), i - int(i)
        lx = xs[i0] + (xs[min(NB - 1, i0 + 1)] - xs[i0]) * fr
        ly = ys[i0] + (ys[min(NB - 1, i0 + 1)] - ys[i0]) * fr
        lh = hs[i0] + (hs[min(NB - 1, i0 + 1)] - hs[i0]) * fr
        hpx, hpy = T(lx + (0.02 if near < 0.5 else 0.0), ly - lh * 0.90)
        if near < 0.5:
            hpy += 0.013
        ph = (gp + off) % 1.0
        if ph < duty:
            k = ph / duty
            fx = hpx + LEGA - 2.0 * LEGA * k
            fy = groundf(fx)
        else:
            k = (ph - duty) / (1.0 - duty)
            fx = hpx - LEGA + 2.0 * LEGA * k
            fy = groundf(fx) + LEGLIFT * math.sin(math.pi * k)
        if tuck > 0.01:
            tx = hpx - 0.045 + 0.018 * math.sin(swimph * 2.4 + off * 6.2)
            ty = hpy - 0.055 + 0.016 * math.cos(swimph * 2.4 + off * 6.2)
            fx += (tx - fx) * tuck
            fy += (ty - fy) * tuck
        al = ink * (1.0 if near > 0.5 else 0.44)
        fx, fy = _ik(out, hpx, hpy, fx, fy, LEG1, LEG2, sgn, CGATOR, al, 0.0)
        for ta in (-0.55, -0.15, 0.25):
            _L(out, fx, fy, fx + 0.030 * math.cos(ta), fy + 0.030 * math.sin(ta),
               CGATOR, al * 0.7 * DETAILDIM)
        if near > 0.5 and ph < duty:
            feet_out.append((fx, fy))

    # --- the head: one rigid wedge, hinged at the neck, and it is what looks -----
    nx, ny = xs[NB - 1], ys[NB - 1]
    cg, sg = math.cos(gaze), math.sin(gaze)

    def HT(hx, hy):
        return T(nx + hx * cg - hy * sg, ny + hx * sg + hy * cg)

    gape = wonder * 0.14
    cj, sj = math.cos(-gape), math.sin(-gape)

    def JT(hx, hy):
        x, y = hx - 0.0, hy + 0.040
        return HT(x * cj - y * sj + 0.0, x * sj + y * cj - 0.040)

    upper = [HT(0.0, 0.050), HT(0.118, 0.038), HT(0.232, 0.014)]
    lower = [JT(0.0, -0.040), JT(0.124, -0.028), JT(0.232, 0.002)]
    _P(out, upper, CGATOR, ink)
    _P(out, lower, CGATOR, ink)
    _L(out, upper[0][0], upper[0][1], lower[0][0], lower[0][1], CGATOR, ink * 0.8)
    _L(out, upper[2][0], upper[2][1], lower[2][0], lower[2][1], CGATOR, ink)
    for tx, up in ((0.072, 1), (0.118, 1), (0.166, 1),
                   (0.096, 0), (0.142, 0), (0.192, 0)):
        if up:
            k = tx / 0.232
            y0 = 0.050 + (0.014 - 0.050) * k
            p0 = HT(tx, y0)
            p1 = HT(tx + 0.012, y0 - 0.016)
            p2 = HT(tx + 0.024, y0)
        else:
            k = tx / 0.232
            y0 = -0.040 + (0.002 + 0.040) * k
            p0 = JT(tx, y0)
            p1 = JT(tx + 0.012, y0 + 0.015)
            p2 = JT(tx + 0.024, y0)
        _P(out, [p0, p1, p2], CGATOR, ink * 0.75 * DETAILDIM)
    _P(out, [HT(0.020, 0.052), HT(0.052, 0.082), HT(0.088, 0.055)],
       CGATOR, ink * 0.9)
    for cx in (0.120, 0.162, 0.204):
        k = cx / 0.232
        y0 = 0.050 + (0.014 - 0.050) * k
        _P(out, [HT(cx - 0.014, y0 + 0.011), HT(cx, y0 + 0.002),
                 HT(cx + 0.014, y0 + 0.011)], CGATOR, ink * 0.6 * DETAILDIM)
    for i in range(4):
        a1 = i * math.pi / 2.0 + 0.78
        a2 = (i + 1) * math.pi / 2.0 + 0.78
        p1 = HT(0.212 + 0.010 * math.cos(a1), 0.022 + 0.010 * math.sin(a1))
        p2 = HT(0.212 + 0.010 * math.cos(a2), 0.022 + 0.010 * math.sin(a2))
        _L(out, p1[0], p1[1], p2[0], p2[1], CGATOR, ink * 0.7 * DETAILDIM)

    # THE EYE. Everything in the piece is aimed at this: a diamond that opens into
    # concentric rings when he is amazed, with the same n-gons the discovery is
    # throwing off, reflected in it at one tenth the size.
    ex, ey = 0.058, 0.054
    re = 0.0115 * (1.0 + 1.35 * wonder)
    epts = [HT(ex + re * math.cos(i * math.pi / 2.0 + 0.78),
               ey + re * 0.86 * math.sin(i * math.pi / 2.0 + 0.78))
            for i in range(5)]
    _P(out, epts, CGATOR2, ink * (0.9 + 0.6 * wonder))
    _L(out, HT(ex - re * 0.3, ey)[0], HT(ex - re * 0.3, ey)[1],
       HT(ex + re * 0.3, ey)[0], HT(ex + re * 0.3, ey)[1],
       CGATOR2, ink * (1.0 + 0.8 * wonder))
    if wonder > 0.04:
        for k, rr in ((0, 2.2), (1, 3.5)):
            n = 6
            rot = t * (0.6 + 0.5 * k) * (1 if k == 0 else -1)
            pts = [HT(ex + re * rr * math.cos(rot + i * 2 * math.pi / n),
                      ey + re * rr * 0.9 * math.sin(rot + i * 2 * math.pi / n))
                   for i in range(n + 1)]
            _P(out, pts, CWONDER, ink * wonder * (0.55 - 0.2 * k))
    return


# --- the seven things he finds ---------------------------------------------------
# Each is a motif repeated: a fern is a triangle repeated down a rachis, a turtle is
# a hexagon repeated inside a hexagon, the lilies are hexagons repeated outward, the
# moon is an n-gon repeated inward. They are siblings, and that is what keeps seven
# different creatures reading as one world.
def _d_fern(out, cx, cy, sc, w, high, t, col, ink):
    for fi, (ang, L, ph) in enumerate(((1.42, 1.00, 0.0), (1.12, 0.78, 1.9),
                                       (1.76, 0.70, 3.4))):
        n = 8
        grow = min(1.0, 0.25 + 0.95 * w)
        nv = max(2, int(round(n * grow)))
        pts, angs, x, y, a = [(0.0, 0.0)], [ang], 0.0, 0.0, ang
        for i in range(n):
            step = L * sc * 0.052
            x += step * math.cos(a)
            y += step * math.sin(a)
            a -= 0.085 + 0.02 * math.sin(t * 0.5 + ph)
            pts.append((x, y))
            angs.append(a)
        _P(out, [(cx + p[0], cy + p[1]) for p in pts[:nv + 1]], col, ink * 0.95)
        for i in range(1, nv):
            px, py = pts[i]
            u = i / float(n)
            pl = L * sc * 0.095 * (1.0 - 0.70 * u) * min(1.0, w * 1.6)
            base = angs[i] + 1.1
            for sgn in (-1.0, 1.0):
                aa = base + sgn * 1.05
                ex, ey = px + pl * math.cos(aa) * sgn, py + pl * abs(math.sin(aa))
                _L(out, cx + px, cy + py, cx + ex, cy + ey, col, ink * 0.8)
                for k in (0.40, 0.70, 0.94):      # the leaflets: the same triangle
                    mx, my = px + (ex - px) * k, py + (ey - py) * k
                    _L(out, cx + mx, cy + my, cx + mx + sgn * pl * 0.22,
                       cy + my + pl * 0.30, col, ink * 0.55 * DETAILDIM)
        # the crozier: five straight chords that unwind as it opens
        cxp, cyp = pts[nv]
        r0 = L * sc * 0.030 * (1.0 - w * 0.85)
        if r0 > 1e-4:
            pp = []
            for i in range(6):
                aa = angs[nv] + 2.4 + i * 1.05
                rr = r0 * (1.0 - i * 0.14)
                pp.append((cx + cxp + rr * math.cos(aa), cy + cyp + rr * math.sin(aa)))
            _P(out, pp, col, ink * 0.9)
    return


def _d_dragon(out, cx, cy, sc, w, high, t, kickenv, col, ink):
    beat = t * (7.0 + 16.0 * high) * (0.25 + 0.75 * w)
    hover = 0.012 * math.sin(t * 1.7) + 0.006 * math.sin(t * 3.1)
    cy = cy + hover * sc
    S = 0.155 * sc
    # abdomen: five diamonds, tapering
    for i in range(5):
        u = i / 5.0
        ax = cx - S * (0.12 + u * 0.78)
        rr = S * 0.055 * (1.0 - u * 0.62)
        _NG(out, ax, cy, rr * 1.5, 4, 0.0, col, ink * (0.9 - 0.25 * u), ry=rr)
    _L(out, cx - S * 0.95, cy, cx + S * 0.10, cy, col, ink * 0.55 * DETAILDIM)
    _NG(out, cx + S * 0.20, cy, S * 0.085, 6, 0.0, col, ink)
    for sgn in (-1.0, 1.0):
        _NG(out, cx + S * 0.25, cy + sgn * S * 0.045, S * 0.035, 3, 0.4, col,
            ink * 0.9)
    # four lattice wings, front and hind pair in antiphase
    for wi, (rx, sgn, phase) in enumerate(((0.06, 1.0, 0.0), (0.06, -1.0, 0.0),
                                           (-0.10, 1.0, math.pi),
                                           (-0.10, -1.0, math.pi))):
        fl = math.sin(beat * 2.0 * math.pi + phase)
        aw = sgn * (0.30 + 0.55 * fl * (0.3 + 0.7 * w))
        bx, by = cx + S * rx, cy
        L, W = S * 0.85, S * 0.115
        cA, sA = math.cos(aw), math.sin(aw)

        def WT(u, v):
            return (bx + (u * L) * cA - (v * W) * sA, by + (u * L) * sA + (v * W) * cA)
        hexp = [WT(0.0, 0.0), WT(0.22, 1.0), WT(0.68, 0.95), WT(1.0, 0.25),
                WT(0.72, -0.55), WT(0.26, -0.75), WT(0.0, 0.0)]
        _P(out, hexp, col, ink * (0.80 + 0.3 * abs(fl)))
        for k in (0.30, 0.52, 0.74):
            p1 = WT(k, 0.98 - 0.7 * k)
            p2 = WT(k + 0.06, -0.75 + 0.9 * k)
            _L(out, p1[0], p1[1], p2[0], p2[1], col, ink * 0.5 * DETAILDIM)
    return


def _d_turtle(out, cx, cy, sc, w, high, t, col, ink):
    S = 0.175 * sc
    lg = _log(None, 1.0)
    for (x0, y0, x1, y1, kind) in lg:
        _L(out, cx - S * 1.15 + x0 * S * 2.3, cy - S * 0.44 + y0 * S * 2.3,
           cx - S * 1.15 + x1 * S * 2.3, cy - S * 0.44 + y1 * S * 2.3,
           CGROUND, ink * (0.55 if kind else 0.75))
    # the shell: a hexagon of hexagons
    _NG(out, cx, cy, S, 6, 0.0, col, ink, ry=S * 0.66)
    _NG(out, cx, cy, S * 0.56, 6, 0.0, col, ink * 0.85, ry=S * 0.37)
    for i in range(6):
        a1 = i * math.pi / 3.0
        _L(out, cx + S * 0.56 * math.cos(a1), cy + S * 0.37 * math.sin(a1),
           cx + S * math.cos(a1), cy + S * 0.66 * math.sin(a1), col,
           ink * 0.6 * DETAILDIM)
        a2 = a1 + math.pi / 6.0
        _NG(out, cx + S * 0.78 * math.cos(a2), cy + S * 0.50 * math.sin(a2),
            S * 0.15, 6, 0.3, col, ink * 0.45 * DETAILDIM, ry=S * 0.10)
    _L(out, cx - S, cy - S * 0.06, cx + S, cy - S * 0.06, col, ink * 0.5)
    for fx in (-0.66, 0.60):
        _P(out, [(cx + S * fx, cy - S * 0.30), (cx + S * (fx + 0.22),
                 cy - S * 0.62), (cx + S * (fx + 0.44), cy - S * 0.50)],
           col, ink * 0.8)
    # he pokes his head out at you, and that is the whole performance
    nk = S * (0.08 + 0.26 * w)
    hx, hy = cx + S * 0.92 + nk, cy + S * 0.14 + nk * 0.45
    _L(out, cx + S * 0.80, cy + S * 0.06, hx, hy, col, ink * 0.9)
    _L(out, cx + S * 0.86, cy - S * 0.02, hx + S * 0.03, hy - S * 0.07,
       col, ink * 0.7)
    _NG(out, hx + S * 0.09, hy + S * 0.02, S * 0.135, 5, 0.2, col, ink,
        ry=S * 0.098)
    _NG(out, hx + S * 0.10, hy + S * 0.06, S * 0.030, 4, 0.0, CGATOR2,
        ink * (0.8 + 0.7 * w))
    return


def _d_heron(out, cx, cy, sc, w, high, t, lift, col, ink):
    S = 0.30 * sc
    cy = cy + lift * 0.55
    for sgn in (-1.0, 1.0):
        lx = cx + sgn * S * 0.07
        ky = cy - S * 0.52
        fy = cy - S * 1.00 + lift * 1.2
        _P(out, [(lx, cy - S * 0.16), (lx + sgn * S * 0.05, ky),
                 (lx - sgn * S * 0.03, fy)], col, ink * max(0.15, 0.85 - 1.2 * lift))
        for ta in (-0.2, 0.25, 0.7):
            _L(out, lx - sgn * S * 0.03, fy,
               lx - sgn * S * 0.03 + S * 0.11 * math.cos(ta),
               fy + S * 0.11 * math.sin(ta), col, ink * 0.55 * DETAILDIM)
    body = [(cx - S * 0.34, cy - S * 0.06), (cx - S * 0.12, cy + S * 0.14),
            (cx + S * 0.20, cy + S * 0.12), (cx + S * 0.30, cy - S * 0.08),
            (cx + S * 0.06, cy - S * 0.22), (cx - S * 0.26, cy - S * 0.20),
            (cx - S * 0.34, cy - S * 0.06)]
    _P(out, body, col, ink)
    # the neck straightens as he notices it, and the head comes up
    k = w
    neck = [(cx + S * 0.22, cy + S * 0.08),
            (cx + S * (0.34 - 0.06 * k), cy + S * (0.30 + 0.16 * k)),
            (cx + S * (0.20 + 0.16 * k), cy + S * (0.44 + 0.30 * k)),
            (cx + S * (0.34 + 0.10 * k), cy + S * (0.55 + 0.26 * k))]
    _P(out, neck, col, ink)
    hx, hy = neck[-1]
    _NG(out, hx, hy + S * 0.04, S * 0.075, 5, 0.5, col, ink, ry=S * 0.055)
    _P(out, [(hx + S * 0.05, hy + S * 0.07), (hx + S * 0.44, hy + S * 0.015),
             (hx + S * 0.05, hy + S * 0.00)], col, ink)
    _NG(out, hx + S * 0.02, hy + S * 0.055, S * 0.024, 4, 0.0, CGATOR2, ink)
    # the wing is a fan of straight rays, folded until he goes
    opened = min(1.0, max(0.0, lift * 4.5))
    for i in range(7):
        u = i / 6.0
        # folded, the rays lie nearly parallel along the back; opened, they fan.
        # A folded wing drawn as a fan reads as a starburst stuck to a bird.
        a0 = (math.radians(202.0 - 16.0 * u)
              + opened * math.radians(66.0 - 40.0 * u))
        L = S * (0.34 + 0.46 * math.sin(math.pi * (0.25 + 0.7 * u))) * \
            (0.62 + 0.78 * opened)
        bx, by = cx + S * 0.02, cy + S * 0.04
        _L(out, bx, by, bx + L * math.cos(a0), by + L * math.sin(a0), col,
           ink * (0.55 + 0.45 * opened))
    return


def _d_lilies(out, cx, cy, sc, w, high, t, col, ink):
    S = 0.185 * sc
    pads = ((-1.75, 0.95), (-0.45, 1.25), (0.85, 0.88), (2.00, 0.62))
    for pi, (px, pr) in enumerate(pads):
        r = S * pr
        bx = cx + S * px * 1.55
        by = cy + 0.004 * math.sin(t * 0.9 + pi * 1.7)
        for k, rr in ((0, 1.0), (1, 0.60), (1, 0.28)):
            n = 6
            for i in range(n):
                if i == 1 and rr > 0.9:
                    continue
                a1, a2 = i * math.pi / 3.0 + 0.2, (i + 1) * math.pi / 3.0 + 0.2
                _L(out, bx + r * rr * math.cos(a1), by + r * rr * 0.30 * math.sin(a1),
                   bx + r * rr * math.cos(a2), by + r * rr * 0.30 * math.sin(a2),
                   col, ink * (DETAILDIM if k else 0.9))
        for i in range(1, 6):
            a1 = i * math.pi / 3.0 + 0.2
            _L(out, bx, by, bx + r * math.cos(a1), by + r * 0.30 * math.sin(a1),
               col, ink * 0.45 * DETAILDIM)
        if pi in (0, 2):
            fh = S * (0.20 + 0.45 * w)
            _L(out, bx, by, bx, by + fh, col, ink * 0.8)
            for j in range(8):
                aa = j * math.pi / 4.0 + t * 0.15
                pl = S * 0.30 * (0.35 + 0.65 * w)
                _P(out, [(bx, by + fh),
                         (bx + pl * math.cos(aa) * 0.55,
                          by + fh + pl * abs(math.sin(aa)) * 0.5 + pl * 0.25),
                         (bx + pl * math.cos(aa), by + fh + pl * 0.10)],
                   CGATOR2, ink * (0.5 + 0.6 * w))
    # the frog, on the middle pad, and he is the punchline
    fx = cx + S * pads[1][0] * 1.55
    fy = cy + S * 0.05
    hop = max(0.0, math.sin(t * 0.8)) ** 6.0 * w * S * 0.55
    fy += hop
    _P(out, [(fx - S * 0.20, fy), (fx - S * 0.12, fy + S * 0.16),
             (fx + S * 0.12, fy + S * 0.16), (fx + S * 0.20, fy),
             (fx - S * 0.20, fy)], CFROG, ink)
    for sgn in (-1.0, 1.0):
        _P(out, [(fx + sgn * S * 0.14, fy + S * 0.05),
                 (fx + sgn * S * 0.30, fy + S * 0.13),
                 (fx + sgn * S * 0.24, fy - S * 0.02),
                 (fx + sgn * S * 0.34, fy - S * 0.02)], CFROG, ink * 0.8)
        _NG(out, fx + sgn * S * 0.08, fy + S * 0.21, S * 0.055, 3, 1.05, CFROG,
            ink * (0.9 + 0.5 * w))
    return


def _d_shoal(out, cx, cy, sc, w, high, t, col, ink, phases, rads):
    S = 0.30 * sc
    spin = t * (0.30 + 0.55 * high) + w * 0.7
    n = len(phases)
    ang = phases + spin
    rx = rads * S * (1.0 + 0.30 * math.sin(t * 0.4))
    ry = rads * S * 0.34
    px = cx + rx * np.cos(ang)
    py = cy + ry * np.sin(ang)
    hx = -rx * np.sin(ang)
    hy = ry * np.cos(ang)
    hl = np.maximum(np.hypot(hx, hy), 1e-6)
    hx, hy = hx / hl, hy / hl
    nx, ny = -hy, hx
    bl = S * 0.088 * (0.7 + 0.5 * rads)
    bw = bl * 0.34
    a = ink
    for i in range(n):
        x, y = px[i], py[i]
        ux, uy = hx[i], hy[i]
        vx, vy = nx[i], ny[i]
        L, Wd = bl[i], bw[i]
        nose = (x + ux * L, y + uy * L)
        tail = (x - ux * L * 0.95, y - uy * L * 0.95)
        up = (x + vx * Wd, y + vy * Wd)
        dn = (x - vx * Wd, y - vy * Wd)
        _P(out, [nose, up, tail, dn, nose], col, a)
        _P(out, [tail, (tail[0] - ux * L * 0.45 + vx * Wd * 1.5,
                        tail[1] - uy * L * 0.45 + vy * Wd * 1.5),
                 (tail[0] - ux * L * 0.45 - vx * Wd * 1.5,
                  tail[1] - uy * L * 0.45 - vy * Wd * 1.5), tail], col, a * 0.8)
    return


def _d_moon(out, cx, cy, sc, w, high, t, kickenv, col, ink):
    R = 0.118 * sc
    _NG(out, cx, cy, R, 14, t * 0.04, col, ink * (0.80 + 0.45 * w))
    for k, rr in ((0, 0.72), (1, 0.46), (2, 0.22)):
        _NG(out, cx, cy, R * rr, 14 - k * 3, -t * 0.05 * (k + 1) + k,
            col, ink * (0.60 - 0.10 * k) * (0.55 + 0.55 * w))
    for i in range(12):
        aa = i * math.pi / 6.0 + t * 0.02
        L = R * (0.22 + 0.30 * kickenv + 0.18 * w)
        _L(out, cx + R * 1.10 * math.cos(aa), cy + R * 1.10 * math.sin(aa),
           cx + (R * 1.10 + L) * math.cos(aa), cy + (R * 1.10 + L) * math.sin(aa),
           col, ink * 0.50 * (0.20 + 0.80 * w))
    # THE LIGHT ON THE WATER. Emitted below the waterline like anything else, so the
    # refraction shear picks it up for free and the column wobbles with the surface
    # the animal is swimming in. This is the last image of the piece.
    for i in range(18):
        u = i / 17.0
        yy = WATERY - 0.014 - u * 0.38
        hw = R * (0.14 + 1.05 * u * u)
        _L(out, cx - hw, yy, cx + hw, yy, col,
           ink * (0.18 + 0.95 * w) * (0.85 - 0.55 * u)
           * (1.0 if i % 2 == 0 else 0.45))
    return


# --- state ----------------------------------------------------------------------
def _new(seed):
    rs = random.Random(seed)
    layers = [(_layer_far(rs), PFAR, False), (_layer_mid(rs), PMID, True),
              (_layer_near(rs), 1.0, True), (_layer_bank(rs), 1.0, False),
              (_layer_fore(rs), PFORE, False)]
    layers = [(L, p, rf) for (L, p, rf) in layers if L is not None]
    nseg = sum(len(L['x0']) for L, _, _ in layers)
    sh_n = 26
    return {
        'seed': seed, 'layers': layers, 'nstatic': nseg,
        'shph': np.array([rs.uniform(0, 6.283) for _ in range(sh_n)]),
        'shrad': np.array([rs.uniform(0.35, 1.0) ** 0.7 for _ in range(sh_n)]),
        'mx': np.array([rs.uniform(-1.3, 1.3) for _ in range(MOTEN)]),
        'my': np.array([rs.uniform(-0.12, 0.52) for _ in range(MOTEN)]),
        'mph': np.array([rs.uniform(0, 6.283) for _ in range(MOTEN)]),
        'mrt': np.array([rs.uniform(0.7, 2.6) for _ in range(MOTEN)]),
        'seen': {}, 'rings': [], 'rays': [], 'rip': [], 'flock': [],
        'reveal': [None] * len(DISCOVERIES), 'lookenv': 0.0,
        'lastt': None, 'labelt': -99.0, 'lastcp': -1, 'census': '',
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


def _tri(x):
    q = x / (2.0 * math.pi)
    return 2.0 * np.abs(2.0 * (q - np.floor(q + 0.5))) - 1.0


def onCook(scriptOp):
    d = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    comp = scriptOp.parent()
    par = comp.par
    first = _S['S'] is None
    if first:
        _S['S'] = _new(SEED0)
    S = _S['S']

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
    dt = min(0.25, max(0.0, t - S['lastt']))
    S['lastt'] = t

    bass = ch('bass'); high = ch('high'); energy = ch('energy')
    kickenv = ch('kickenv'); kickslow = ch('kickslow'); dropenv = ch('dropenv')

    # PRIME. The director is force-cooked by the builder, so on frame one its
    # counters are already non-zero: read as deltas that is a drop, a look and a
    # reseed all at once, and the scene opens mid-event.
    if first and d is not None:
        for nm in ('kickcnt', 'accentcnt', 'dropcnt', 'lookcnt', 'gustcnt',
                   'reseedcnt'):
            try:
                S['seen'][nm] = float(d[nm][0])
            except Exception:
                pass

    if _delta(S, d, 'reseedcnt'):
        keep = dict(S['seen'])
        S.update(_new((S['seed'] * 1103515245 + 12345) % 2147483647))
        S['seen'] = keep

    slen = max(1.0, ch('storylen', 330.0))
    show = ch('show', 0.0)
    f = min(1.0, max(0.0, show / slen))
    walk = walkx(f)
    camX = walk - GATORX
    ink = float(par.Ink.eval()) * (1.0 + 0.16 * kickenv + 0.30 * dropenv
                                  + 0.18 * bass)
    swaypar = float(par.Sway.eval())
    rippar = float(par.Ripple.eval())
    wpar = float(par.Wonder.eval())
    reflpar = float(par.Reflect.eval())
    mistpar = float(par.Mist.eval())
    dens = float(par.Density.eval())

    gust = _delta(S, d, 'gustcnt')
    nkick = _delta(S, d, 'kickcnt')
    naccent = _delta(S, d, 'accentcnt')
    ndrop = _delta(S, d, 'dropcnt')
    nlook = _delta(S, d, 'lookcnt')
    if nlook:
        S['lookenv'] = 1.0
    S['lookenv'] *= 0.5 ** (dt / 2.4)
    if gust:
        for _ in range(gust):
            S['flock'].append([t, 0.30 + 0.5 * (len(S['flock']) % 3) * 0.2])
    gustenv = dropenv

    # --- the discoveries: the schedule ARMS, the bass FIRES ----------------------
    W = [0.0] * len(DISCOVERIES)
    EX = [0.0] * len(DISCOVERIES)
    for i, D in enumerate(DISCOVERIES):
        f0, dw = D['f'], D['dwell']
        rise = _ss(f0 - dw * 0.62, f0 - dw * 0.16, f)
        fall = 1.0 if D.get('hold') else (1.0 - _ss(f0 + dw * 0.28, f0 + dw * 0.85, f))
        base = rise * fall
        if f < f0 - dw * 0.80:
            S['reveal'][i] = None
        w0, w1 = f0 - dw * 0.45, f0 + dw * 0.28
        if S['reveal'][i] is None and f >= w0:
            fire = (ndrop > 0 and bool(par.Dropfire.eval())) or f >= w1
            if fire:
                S['reveal'][i] = t
                plx = D.get('plx', 1.0)
                S['rays'].append([t, DPOS[i], D['y'], plx])
                for k in range(3):
                    S['rings'].append([t + k * 0.10, 1.0, DPOS[i], D['y'],
                                       6 + (i + k) % 4, k * 0.7, plx])
        gate = 0.0 if S['reveal'][i] is None else _ss(0.0, 0.55, t - S['reveal'][i])
        W[i] = base * gate * wpar
        EX[i] = _ss(f0 + dw * 0.22, f0 + dw * 0.85, f)

    wonder = min(1.6, max(max(W), S['lookenv'] * wpar))
    # an accented kick throws another n-gon off whatever he is looking at
    if naccent and wonder > 0.22 and t - S.get('lastring', -9.0) > 0.42:
        S['lastring'] = t
        if max(W) > 0.02:
            _j = int(np.argmax(W))
            rx, ry0, rp = DPOS[_j], DISCOVERIES[_j]['y'], DISCOVERIES[_j].get('plx', 1.0)
        else:
            rx, ry0, rp = walkx(f), WATERY + 0.14, 1.0
        S['rings'].append([t, 0.55 + 0.45 * ch('beatstr'), rx, ry0,
                           6 + (nkick % 4), t * 0.8, rp])
    del S['rings'][:-RINGMAX]
    del S['rays'][:-4]

    # --- body: it follows the SMOOTHED bank, and floats when the bank is gone ----
    gsm = float(np.mean(ground(np.array([walk - 0.24, walk - 0.10, walk,
                                         walk + 0.12, walk + 0.26]))))
    yg = gsm + BODYUP
    # A swimming alligator shows a ridge and an eye. Floating him high enough to
    # see the whole animal is the tell that the water is a backdrop and not a
    # medium; this number is what makes the last chapter mean anything.
    yw = WATERY - 0.040
    swim = _ss(-0.015, 0.075, yw - yg)
    by = yg + (yw - yg) * swim
    gfront = groundf(walk + 0.22)
    gback = groundf(walk - 0.22)
    # he rears at what he finds: the body pitches up with the amazement, which is
    # the one gesture that reads from across a room. A head turn alone does not.
    pitch = math.atan2(gfront - gback, 0.44) * 0.75 * (1.0 - swim)
    gp = walk / STRIDE

    blocks = []

    def push(rows, reflect=False):
        if not len(rows):
            return
        a = np.asarray(rows, dtype=np.float64)
        if a.ndim == 1:
            a = a.reshape(1, -1)
        blocks.append((a, reflect))

    # --- the animal ------------------------------------------------------------
    gsx = GATORX
    feet = []
    gseg = []
    # who is he looking at, and where is that from his eye
    j = int(np.argmax(W)) if max(W) > 0.02 else -1
    gaze = 0.0
    if j >= 0:
        plx = DISCOVERIES[j].get('plx', 1.0)
        tsx = (DPOS[j] - camX) * plx
        tsy = DISCOVERIES[j]['y']
        hbx = gsx + 0.30 * GSCALE
        hby = by + 0.05 * GSCALE
        gaze = math.atan2(tsy - hby, max(0.04, tsx - hbx))
        gaze = min(0.80, max(-0.55, gaze)) * min(1.0, W[j])
    gaze += 0.20 * min(1.0, wonder) + S['lookenv'] * 0.25 * math.sin(t * 0.7)
    pitch += 0.11 * min(1.0, wonder)
    _gator(gseg, gsx, by, pitch, gp, swim, min(1.0, wonder), gaze, kickenv,
           high, t, ink, feet)
    push(gseg, reflect=True)

    # --- the discovery on screen ------------------------------------------------
    cseg = []
    for i, D in enumerate(DISCOVERIES):
        plx = D.get('plx', 1.0)
        sx = (DPOS[i] - camX) * plx
        if abs(sx) > 1.55:
            continue
        vis = 1.0 - _ss(1.05, 1.45, abs(sx))
        if vis <= 0.01:
            continue
        w = min(1.0, W[i])
        ci = ink * vis * (0.32 + 0.85 * w)
        sy = D['y']
        k = D['kind']
        ex = EX[i]
        if k == 'fern':
            _d_fern(cseg, sx, sy, D['sc'], w, high, t, D['col'], ci)
        elif k == 'dragon':
            sx += ex * ex * 1.30
            sy += ex * ex * 0.42
            _d_dragon(cseg, sx, sy, D['sc'], w, high, t, kickenv, D['col'], ci)
        elif k == 'turtle':
            _d_turtle(cseg, sx, sy, D['sc'], w, high, t, D['col'], ci)
        elif k == 'heron':
            _d_heron(cseg, sx, sy, D['sc'], w, high, t, ex, D['col'], ci)
        elif k == 'lilies':
            _d_lilies(cseg, sx, sy, D['sc'], w, high, t, D['col'], ci)
        elif k == 'shoal':
            _d_shoal(cseg, sx, sy, D['sc'], w, high, t, D['col'], ci,
                     S['shph'], S['shrad'])
        elif k == 'moon':
            _d_moon(cseg, sx, sy, D['sc'], w, high, t, kickenv, D['col'], ci)
    push(cseg, reflect=True)

    # --- amazement: rotating n-gons leaving the thing he is looking at ----------
    rseg = []
    for rg in S['rings']:
        age = t - rg[0]
        if age < 0.0 or age > RINGLIFE:
            continue
        r = RINGV * age
        al = rg[1] * ink * math.exp(-age / (RINGLIFE * 0.30)) * 0.95
        if al < 0.006:
            continue
        cx = (rg[2] - camX) * rg[6]
        _NG(rseg, cx, rg[3], r, int(rg[4]), rg[5] + age * 1.3, CWONDER, al,
            ry=r * 0.80)
    for ry_ in S['rays']:
        age = t - ry_[0]
        if age > 1.4:
            continue
        al = ink * 0.8 * (1.0 - age / 1.4) ** 2
        cx = (ry_[1] - camX) * ry_[3]
        for i in range(14):
            aa = i * math.pi / 7.0 + age * 0.4
            r0 = 0.045 + age * 0.30
            r1 = r0 + 0.055 * (1.0 - age / 1.4)
            _L(rseg, cx + r0 * math.cos(aa), ry_[2] + r0 * 0.8 * math.sin(aa),
               cx + r1 * math.cos(aa), ry_[2] + r1 * 0.8 * math.sin(aa),
               CWONDER, al)
    push(rseg)


    # --- the surface -----------------------------------------------------------
    # One sampled polyline across the frame, masked off wherever the bank is above
    # the waterline. Its displacement array is then the single source of truth for
    # the refraction shear, the reflection shear and the glints, so the surface and
    # everything it acts on can never disagree about where the water is.
    WSX = np.linspace(-1.22, 1.22, NWATER)
    WWX = WSX + camX
    gw = ground(WWX)
    wet = gw < (WATERY - 0.004)
    openn = _sv(0.34, 0.90, WWX / TOTALX)
    amp = (0.0038 + 0.0105 * bass + 0.004 * dropenv) * rippar * (0.45 + 0.95 * openn)
    disp = amp * (0.55 * np.sin(WWX * 11.0 - t * 1.30)
                  + 0.30 * _tri(WWX * 23.0 + t * 0.85)
                  + 0.18 * np.sin(WWX * 41.0 - t * 2.10))

    # every kick drops a ring in the water under his feet
    if nkick:
        fx = feet[0][0] if feet else GATORX
        fw = fx + camX
        amp0 = 1.0 if (groundf(fw) < WATERY + 0.02 or swim > 0.3) else 0.45
        S['rip'].append([t, fw, amp0 * (0.6 + 0.6 * ch('beatstr'))])
    if ndrop:
        S['rip'].append([t, walk, 2.2])
    del S['rip'][:-RIPMAX]
    for rp in S['rip']:
        age = t - rp[0]
        if age > RIPLIFE:
            continue
        r = RIPV * age
        dd = np.abs(WWX - rp[1])
        env = np.exp(-((dd - r) ** 2) / (2.0 * RIPW * RIPW))
        disp = disp + (env * rp[2] * 0.016 * rippar * math.exp(-age / RIPDECAY)
                       * np.cos((dd - r) * RIPK))

    wy = WATERY + disp
    wseg = []
    ok = wet[:-1] & wet[1:]
    idxw = np.nonzero(ok)[0]
    if len(idxw):
        a0 = ink * 0.80
        for i in idxw:
            wseg.append((WSX[i], wy[i], WSX[i + 1], wy[i + 1],
                         CWATER[0], CWATER[1], CWATER[2], a0, 0.04, 1.0))
            wseg.append((WSX[i], wy[i] - 0.011, WSX[i + 1], wy[i + 1] - 0.011,
                         CWATER[0], CWATER[1], CWATER[2], a0 * 0.30, 0.041, 1.0))
        # glints: the surface only sparkles where it is actually steep
        slope = np.abs(np.diff(wy)) / (WSX[1] - WSX[0])
        thr = float(np.percentile(slope[idxw], 82)) if len(idxw) > 6 else 1e9
        gl = ink * (0.25 + 1.5 * high)
        for i in idxw[::2]:
            if slope[i] > thr:
                wseg.append((WSX[i], wy[i], WSX[i], wy[i] + 0.016,
                             1.0, 0.98, 0.90, gl, 0.042, 1.0))
        # DEPTH. Dashed rules parallel to the surface, only where the bank is
        # actually that far down. A lake has to have a body you can feel, or the
        # bottom of the frame is void and the animal is standing on a line.
        for k in range(1, 7):
            yy = WATERY - 0.062 * k
            al = ink * 0.46 * math.exp(-k * 0.30)
            if al < 0.006:
                break
            step = 3 + k
            for i in idxw[::step]:
                j2 = i + step - 1
                if j2 >= NWATER - 1 or gw[i] > yy or gw[j2] > yy:
                    continue
                sq = 1.0 - 0.11 * k
                wseg.append((WSX[i], yy + disp[i] * sq, WSX[j2], yy + disp[j2] * sq,
                             CWATER[0], CWATER[1], CWATER[2], al, 0.03, 0.0))
    push(wseg)

    # --- the swamp: static, culled by binary search, swayed on the bass ---------
    swayA = (0.0035 + 0.013 * bass + 0.016 * gustenv) * swaypar
    for (L, p, dorefl) in S['layers']:
        cx = camX * p
        lo = np.searchsorted(L['key'], cx - 1.9)
        hi = np.searchsorted(L['key'], cx + 1.9)
        if hi <= lo:
            continue
        sl = slice(lo, hi)
        x0 = L['x0'][sl] - cx
        x1 = L['x1'][sl] - cx
        y0 = L['y0'][sl].copy()
        y1 = L['y1'][sl].copy()
        ph = (L['x0'][sl] * 2.1 + t * (0.55 + 0.9 * p))
        sw = np.sin(ph) * 0.65 + np.sin(ph * 2.37 + 1.7) * 0.35
        x0 = x0 + L['s0'][sl] * swayA * sw / max(p, 0.2)
        x1 = x1 + L['s1'][sl] * swayA * sw / max(p, 0.2)
        # while he is amazed the swamp steps back, so the warm thing is the only
        # thing in the frame that got brighter
        aa = L['a'][sl] * ink * dens * (1.0 - 0.30 * min(1.0, wonder))
        arr = np.stack([x0, y0, x1, y1, L['r'][sl], L['g'][sl], L['b'][sl],
                        aa, L['z'][sl], np.zeros(hi - lo)], axis=1)
        blocks.append((arr, dorefl))

    # --- motes and mist --------------------------------------------------------
    mtw = 2.6
    mx = np.mod(S['mx'] - camX * 0.55 + 1.3, mtw) - 1.3
    my = S['my'] + 0.022 * np.sin(t * S['mrt'] * 0.5 + S['mph'])
    tw = 0.5 + 0.5 * np.sin(t * S['mrt'] + S['mph'])
    ma = ink * (0.22 + 0.85 * high) * (0.25 + 0.75 * tw) * 0.85
    ms = 0.0045 + 0.0035 * tw
    z = np.full(MOTEN, -0.05)
    zz = np.zeros(MOTEN)
    m1 = np.stack([mx - ms, my - ms, mx + ms, my + ms,
                   np.full(MOTEN, CMOTE[0]), np.full(MOTEN, CMOTE[1]),
                   np.full(MOTEN, CMOTE[2]), ma, z, zz], axis=1)
    m2 = np.stack([mx - ms, my + ms, mx + ms, my - ms,
                   np.full(MOTEN, CMOTE[0]), np.full(MOTEN, CMOTE[1]),
                   np.full(MOTEN, CMOTE[2]), ma, z, zz], axis=1)
    blocks.append((m1, False))
    blocks.append((m2, False))

    mseg = []
    for bi, (my0, mv, ma0) in enumerate(MISTBANDS):
        yy = my0 + 0.014 * math.sin(t * 0.27 + bi * 1.7)
        off = (-t * mv - camX * 0.30) % 0.34
        al = ink * ma0 * mistpar * (0.30 + 0.60 * bass + 0.4 * dropenv) * 0.60
        if al < 0.004:
            continue
        for k in range(20):
            x = -1.30 + k * 0.145 + off
            L = 0.030 + 0.070 * (((k * 7 + bi * 13) % 5) / 4.0)
            wob = 0.005 * math.sin(k * 2.1 + bi * 1.3)
            aa = al * (0.35 + 0.65 * (((k * 11 + bi * 5) % 7) / 6.0))
            mseg.append((x, yy + wob, x + L, yy + wob * 0.4,
                         CMIST[0], CMIST[1], CMIST[2], aa, -0.30, 1.0))
    push(mseg)

    # --- a flock, when the low end takes the room ------------------------------
    fseg = []
    for fl in S['flock']:
        age = t - fl[0]
        if age > 4.2:
            continue
        al = ink * 0.55 * (1.0 - age / 4.2) ** 1.5
        for k in range(7):
            u = k / 6.0
            bx = -0.7 + u * 0.55 + age * (0.20 + 0.06 * k)
            byb = fl[1] + u * 0.10 + age * (0.085 + 0.02 * k)
            wgs = 0.030 * (1.0 + 0.5 * math.sin(age * (7.0 + k) + k))
            _L(fseg, bx - wgs, byb + wgs * 0.55 * math.sin(age * 8.0 + k),
               bx, byb, CFAR, al)
            _L(fseg, bx, byb, bx + wgs,
               byb + wgs * 0.55 * math.sin(age * 8.0 + k), CFAR, al)
    push(fseg)

    # --- THE ONE RULE ----------------------------------------------------------
    # Mirror everything reflectable, then dim and shear everything under water.
    # Nothing above this line knows the waterline exists.
    refl = []
    if reflpar > 0.01:
        for (arr, dorefl) in blocks:
            if not dorefl or not len(arr):
                continue
            src = arr
            if len(src) > 220:
                src = src[::2]
            above = np.maximum(src[:, 1], src[:, 3]) > WATERY + 0.004
            k = np.nonzero(above)[0]
            if not len(k):
                continue
            m = src[k].copy()
            m[:, 1] = 2.0 * WATERY - src[k, 1]
            m[:, 3] = 2.0 * WATERY - src[k, 3]
            ymid = (m[:, 1] + m[:, 3]) * 0.5
            dep = np.clip(WATERY - ymid, 0.0, 0.7)
            d0 = np.interp(m[:, 0], WSX, disp)
            d1 = np.interp(m[:, 2], WSX, disp)
            sc = 2.0 + 14.0 * dep
            m[:, 0] = m[:, 0] + d0 * sc
            m[:, 2] = m[:, 2] + d1 * sc
            haswater = np.interp(m[:, 0], WSX, wet.astype(np.float64))
            shim = 0.40 + 0.60 * (0.5 + 0.5 * np.sin(ymid * 105.0 + t * 2.3))
            m[:, 7] = (m[:, 7] * 0.28 * reflpar * shim * haswater
                       * np.exp(-dep * 2.6))
            m[:, 4] *= 0.55
            m[:, 5] *= 0.92
            m[:, 6] = np.minimum(1.3, m[:, 6] * 1.15)
            m[:, 8] = 0.10
            m[:, 9] = 1.0
            refl.append(m)
    for m in refl:
        blocks.append((m, False))

    parts = [b for (b, _) in blocks if len(b)]
    if parts:
        A = np.concatenate(parts, axis=0)
    else:
        A = np.zeros((0, 10))

    x0, y0, x1, y1 = A[:, 0], A[:, 1], A[:, 2], A[:, 3]
    r, g, b, al = A[:, 4].copy(), A[:, 5].copy(), A[:, 6].copy(), A[:, 7].copy()
    ymid = (y0 + y1) * 0.5
    # BELOW THE LINE IS NOT THE SAME AS IN THE WATER. Everything under the bank is
    # earth seen in section, and dimming it cyan drowned the whole lower third of
    # the frame in the first pass. Submerged means below the waterline AND above
    # the bank; below the bank is simply ground, and is left alone.
    gmid = ground((x0 + x1) * 0.5 + camX)
    sub = (ymid < WATERY) & (ymid > gmid - 0.006) & (A[:, 9] < 0.5)
    if sub.any():
        dep = np.clip(WATERY - ymid, 0.0, 0.7)
        sc = (2.2 + 8.0 * dep) * rippar
        d0 = np.interp(x0, WSX, disp)
        d1 = np.interp(x1, WSX, disp)
        x0 = np.where(sub, x0 + d0 * sc, x0)
        x1 = np.where(sub, x1 + d1 * sc, x1)
        fade = SUBDIM * np.exp(-dep * 1.4)
        al = np.where(sub, al * fade, al)
        r = np.where(sub, r * 0.48, r)
        g = np.where(sub, g * 0.88, g)
        b = np.where(sub, np.minimum(1.35, b * 1.20), b)

    dx, dy = x1 - x0, y1 - y0
    ln = np.hypot(dx, dy)
    keep = ((np.minimum(x0, x1) < CULLX) & (np.maximum(x0, x1) > -CULLX)
            & (np.minimum(y0, y1) < CULLY) & (np.maximum(y0, y1) > -CULLY)
            & (ln > MINLEN) & (al > 0.005))
    idx = np.nonzero(keep)[0]
    # Priority is emission order and emission order is the story: the animal and
    # what he is looking at go in first, so if the pool ever ran dry it would be
    # the far bank that vanished, never him.
    if len(idx) > MAXSEG:
        idx = idx[:MAXSEG]
    n = len(idx)

    out = np.zeros((11, MAXSEG), dtype=np.float64)
    out[4] = 1.0
    out[6] = 1.0
    if n:
        out[0, :n] = (x0[idx] + x1[idx]) * 0.5
        out[1, :n] = (y0[idx] + y1[idx]) * 0.5
        out[2, :n] = A[idx, 8]
        out[3, :n] = np.degrees(np.arctan2(-dx[idx], dy[idx]))
        out[5, :n] = np.maximum(ln[idx], 1e-5)
        out[7, :n] = np.clip(r[idx], 0.0, 4.0)
        out[8, :n] = np.clip(g[idx], 0.0, 4.0)
        out[9, :n] = np.clip(b[idx], 0.0, 4.0)
        out[10, :n] = np.clip(al[idx], 0.0, 1.0)

    scriptOp.clear()
    chans = [scriptOp.appendChan(nm) for nm in CH]
    scriptOp.numSamples = MAXSEG
    for ii, c in enumerate(chans):
        c.vals = out[ii].tolist()

    cp = 0
    for i, c in enumerate(CHECKPOINTS):
        if c[2] <= f + 1e-6:
            cp = i
    if cp != S['lastcp']:
        S['lastcp'] = cp
        S['labelt'] = t
    lf = math.exp(-max(0.0, t - S['labelt']) / 3.0)
    nm = CHECKPOINTS[cp][1].strip()
    if j >= 0 and W[j] > 0.25:
        nm = nm + '\n' + DISCOVERIES[j]['name']
        lf = max(lf, min(1.0, W[j]))

    try:
        par.Walkx.val = walk
        par.Chapter.val = float(cp)
        par.Wonderm.val = min(1.0, wonder)
        par.Segs.val = float(n)
        par.Labelfade.val = lf
        par.Shock.val = dropenv ** 4
        if par.Scaletxt.eval() != nm:
            par.Scaletxt.val = nm
    except Exception:
        pass

    S['census'] = ('f %.3f | x %.2f/%.1f | swim %.2f | wonder %.2f | lines %d/%d '
                   '| static %d | rings %d' % (f, walk, TOTALX, swim, wonder, n,
                                               MAXSEG, S['nstatic'],
                                               len(S['rings'])))
    return
'''


eng_src = C(textDAT, 'engine_src', 1780, 980)
eng_src.text = hdr(
    DISCOVERIES=DISCOVERIES, CHECKPOINTS=CHECKPOINTS,
    TOTALX=TOTALX, WATERY=WATERY, GATORX=GATORX, GSCALE=GSCALE, MAXSEG=MAXSEG,
    SEED0=20260917,
    CH=('tx', 'ty', 'tz', 'rz', 'sx', 'sy', 'sz', 'r', 'g', 'b', 'a'),
    # palette: the swamp is cold and the amazement is warm, and that is the
    # whole colour idea. Nothing warm happens except where he is looking.
    CGATOR=(0.40, 0.94, 0.80), CGATOR2=(1.00, 0.86, 0.50),
    CREED=(0.26, 0.74, 0.60), CFAR=(0.20, 0.42, 0.55), CMID=(0.24, 0.60, 0.60),
    CFORE=(0.13, 0.32, 0.36), CGROUND=(0.32, 0.55, 0.54),
    CWATER=(0.50, 0.87, 1.00), CWONDER=(1.00, 0.97, 0.89),
    CMOTE=(0.86, 1.00, 0.92), CPAD=(0.34, 0.80, 0.70),
    CFROG=(0.70, 1.00, 0.55), CMIST=(0.42, 0.66, 0.78),
    # parallax. 1.0 is the plane the animal walks on and the only one his feet
    # are allowed to touch.
    PFAR=0.22, PMID=0.55, PFORE=1.42,
    DETAILDIM=0.55,
    # the rig, in world units. Reach (0.138) must beat hip-to-bank (0.095) plus
    # half a stride (0.072) or the legs visibly stretch at the end of stance.
    LEG1=0.074, LEG2=0.080, LEGA=0.074, LEGLIFT=0.048, BODYUP=0.148,
    STRIDE=0.148,
    NWATER=176, RIPV=0.46, RIPW=0.058, RIPK=32.0, RIPLIFE=3.4, RIPDECAY=1.5,
    RIPMAX=16,
    RINGV=0.30, RINGLIFE=2.2, RINGMAX=16,
    MOTEN=44,
    MISTBANDS=((-0.020, 0.016, 0.45), (0.100, 0.010, 0.34),
               (0.235, 0.022, 0.26), (0.375, 0.007, 0.18)),
    SUBDIM=0.42,
    # a touch wider than the ortho frame (half-extents 1.0 x 0.5625)
    CULLX=1.30, CULLY=0.72, MINLEN=0.0018,
) + ENGINE_BODY

engine = C(scriptCHOP, 'engine', 1940, 980)
engine.par.callbacks = eng_src.path
W(director, engine, 0)


# ---------------------------------------------------------------------------
# GEOMETRY AND RENDER
# ---------------------------------------------------------------------------
SHAPE_BODY = '''# One unit segment along +y, centred. Everything else is instance transform.


def onCook(scriptOp):
    scriptOp.clear()
    a = scriptOp.appendPoint(); a.x, a.y, a.z = 0.0, -0.5, 0.0
    b = scriptOp.appendPoint(); b.x, b.y, b.z = 0.0, 0.5, 0.0
    ln = scriptOp.appendPoly(2, closed=False, addPoints=False)
    ln[0].point = scriptOp.points[0]
    ln[1].point = scriptOp.points[1]
    return
'''
shape_src = C(textDAT, 'shape_src', 1300, 200)
shape_src.text = SHAPE_BODY
unit_line = C(scriptSOP, 'unit_line', 1440, 200)
unit_line.par.callbacks = shape_src.path

mat_line = C(lineMAT, 'mat_line', 1600, 200)
soft(mat_line, widthnear=1.40, widthfar=1.40, widthaffectedbyfov=False,
     linenearalpha=1.0, blending=True, depthtest=False, depthwriting=False)
mat_line.par.widthnear.expr = ("max(0.8, parent().par.Linewidth * (1.0 + 0.40 * %s "
                               "+ 0.14 * %s))" % (D('dropenv'), D('kickenv')))
mat_line.par.widthfar.expr = mat_line.par.widthnear.expr

g_lines = C(geometryCOMP, 'geo_lines', 1780, 200)
_stale = g_lines.op('torus1')
if _stale:
    _stale.destroy()
_sel = g_lines.create(selectSOP, 'shape')
_sel.par.sop = unit_line.path
_sel.render = True
_sel.display = True
g_lines.par.material = mat_line.path
g_lines.par.instancing = True
g_lines.par.instanceop = engine.path
for _p, _v in (('instancetx', 'tx'), ('instancety', 'ty'), ('instancetz', 'tz'),
               ('instancerz', 'rz'), ('instancesx', 'sx'), ('instancesy', 'sy'),
               ('instancesz', 'sz')):
    soft(g_lines, **{_p: _v})
soft(g_lines, instancecolormode='replace')
for _p, _v in (('instancer', 'r'), ('instanceg', 'g'), ('instanceb', 'b'),
               ('instancea', 'a')):
    soft(g_lines, **{_p: _v})

cam = C(cameraCOMP, 'cam', 1620, 330, projection='ortho', tz=4.0)
soft(cam, orthowidth=ORTHOW, near=0.1, far=20.0)

render_lines = C(renderTOP, 'render_lines', 1940, 200)
res(render_lines)
render_lines.par.camera = cam.path
render_lines.par.geometry = g_lines.path
render_lines.par.bgcolora = 0.0
soft(render_lines, antialias='msaa4x', transparency='sortedblending')

# --- the air -------------------------------------------------------------------
void = C(glslTOP, 'void', 1780, 440)
res(void)
void_pix = C(textDAT, 'void_pixel', 1780, 370)
void_pix.text = '''// The air the whole journey is drawn in. Near-black, cold, with a band of haze
// sitting exactly on the waterline — the horizon everything converges toward — and
// a triangular lattice that only surfaces when the low end takes the room, so the
// geometry of the piece is stated by the background too and not only by the lines.
uniform vec4 uP;   // x energy, y kickenv, z vignette, w time
uniform vec4 uQ;   // x dropenv, y progress, z bass, w mist
out vec4 fragColor;

float hash(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453); }

float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
               mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

float fbm(vec2 p) {
    float s = 0.0, a = 0.5;
    for (int i = 0; i < 4; i++) { s += a * vnoise(p); p = p * 2.03 + 7.3; a *= 0.5; }
    return s;
}

// one set of parallel lines at angle a, thin and cheap
float rule(vec2 uv, float a, float n, float w) {
    vec2 dir = vec2(cos(a), sin(a));
    float v = abs(fract(dot(uv, dir) * n) - 0.5);
    return smoothstep(w, 0.0, v);
}

void main() {
    vec2 uv = vUV.st;
    vec2 d = (uv - 0.5) * vec2(1.777, 1.0);
    // the waterline in uv: world y -0.145 over an ortho height of 1.125
    float wl = 0.5 - 0.090 / 1.125;
    float dy = uv.y - wl;

    // the swamp is green-black and the lake is blue-black: one lerp, on progress
    vec3 swamp = vec3(0.013, 0.026, 0.022);
    vec3 lake  = vec3(0.012, 0.019, 0.036);
    vec3 col = mix(swamp, lake, clamp(uQ.y, 0.0, 1.0));
    // under the surface is darker and colder than the air above it
    col *= mix(0.62, 1.0, smoothstep(-0.10, 0.02, dy));

    float grain = fbm(uv * vec2(5.0, 3.0) + vec2(uP.w * 0.007, 0.0));
    col *= 0.68 + 0.72 * grain;

    // haze on the horizon, and it breathes on the bass
    float haze = exp(-dy * dy * 210.0) * (0.55 + 0.75 * uQ.z + 0.9 * uQ.x);
    col += vec3(0.030, 0.062, 0.078) * haze * uQ.w;
    col += vec3(0.020, 0.040, 0.062) * exp(-dy * dy * 16.0) * (0.25 + 0.6 * uP.x)
           * uQ.w;

    // the lattice: three rules at 60 degrees, only on the drop
    float lat = uQ.x * 0.55 + uP.y * 0.10;
    if (lat > 0.004) {
        float g = rule(uv, 1.5708, 26.0, 0.030)
                + rule(uv, 0.5236, 26.0, 0.030)
                + rule(uv, 2.6180, 26.0, 0.030);
        col += vec3(0.055, 0.105, 0.130) * g * lat * (0.35 + 0.65 * grain);
    }

    col += (hash(uv * vec2(1920.0, 1080.0) + fract(uP.w)) - 0.5) * 0.006;
    col *= 1.0 - uP.z * 0.85 * dot(d, d);
    fragColor = TDOutputSwizzle(vec4(max(col, vec3(0.0)), 1.0));
}
'''
void.par.pixeldat = void_pix.path
void.par.vec = 2
void.par.vec0name = 'uP'
void.par.vec0valuex.expr = D('energy')
void.par.vec0valuey.expr = D('kickenv')
void.par.vec0valuez.expr = 'parent().par.Vignette'
void.par.vec0valuew.expr = D('rawtime')
void.par.vec1name = 'uQ'
void.par.vec1valuex.expr = D('dropenv')
void.par.vec1valuey.expr = 'parent().par.Walkx / %f' % float(TOTALX)
void.par.vec1valuez.expr = D('bass')
void.par.vec1valuew.expr = 'parent().par.Mist'

comp = C(compositeTOP, 'comp_scene', 2100, 440, operand='over')
res(comp)
W(render_lines, comp, 0)
W(void, comp, 1)

glow_cut = C(levelTOP, 'glow_cut', 2100, 320)
soft(glow_cut, blacklevel=0.28, gamma1=1.20)
W(comp, glow_cut)
glow_blur = C(blurTOP, 'glow_blur', 2260, 320, size=13.0)
res(glow_blur, OUTW // 2, OUTH // 2)
glow_blur.par.size.expr = "13.0 + 24.0 * %s" % D('dropenv')
W(glow_cut, glow_blur)
glow_lvl = C(levelTOP, 'glow_lvl', 2420, 320)
glow_lvl.par.opacity.expr = (
    "0.46 * parent().par.Glow * (0.42 + 0.28 * %s + 0.40 * %s + 0.70 * %s "
    "+ 0.35 * parent().par.Wonderm)"
    % (D('energy'), D('kickenv'), D('dropenv')))
W(glow_blur, glow_lvl)

comp_glow = C(compositeTOP, 'comp_glow', 2260, 440, operand='add')
res(comp_glow)
W(comp, comp_glow, 0)
W(glow_lvl, comp_glow, 1)

shock = C(glslTOP, 'shock', 2420, 440)
res(shock)
shock_pix = C(textDAT, 'shock_pixel', 2420, 370)
shock_pix.text = '''// Radial chromatic shear, only while a drop is decaying. Proportional to radius so
// the middle of the frame — where he is — stays clean and only the swamp tears.
// At uS.x = 0 this is an exact passthrough, which is how it spends most of its life.
// sTD2DInputs is declared by TD itself - redeclaring it is a compile error.
uniform vec4 uS;   // x shock, y aberration scale, z unused, w unused
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec2 d = uv - 0.5;
    float k = uS.x * uS.y;
    if (k < 0.0005) {
        fragColor = TDOutputSwizzle(texture(sTD2DInputs[0], uv));
        return;
    }
    float rr = dot(d, d);
    vec2 off = d * k * (0.30 + 2.4 * rr);
    float r = texture(sTD2DInputs[0], uv + off).r;
    vec4 g = texture(sTD2DInputs[0], uv);
    float b = texture(sTD2DInputs[0], uv - off).b;
    fragColor = TDOutputSwizzle(vec4(r, g.g, b, g.a));
}
'''
shock.par.pixeldat = shock_pix.path
shock.par.vec = 1
shock.par.vec0name = 'uS'
shock.par.vec0valuex.expr = 'parent().par.Shock'
shock.par.vec0valuey.expr = 'parent().par.Shockamt * 0.010'
W(comp_glow, shock)

label = C(textTOP, 'label', 2100, 620)
res(label, OUTW, OUTH, 'rgba8fixed')
soft(label, alignx='left', aligny='bottom', fontsizex=22, font='Courier New',
     bgalpha=0.0, fontcolorr=0.80, fontcolorg=0.96, fontcolorb=0.92,
     fontcolora=1.0, wordwrap=False, trackingx=0.15,
     positionx=0.052, positiony=0.070, positionunit='fraction')
label.par.text.expr = 'parent().par.Scaletxt.eval()'

label_lvl = C(levelTOP, 'label_lvl', 2260, 620)
label_lvl.par.opacity.expr = (
    "parent().par.Label * (0.16 + 0.84 * parent().par.Labelfade)")
W(label, label_lvl)

comp_label = C(compositeTOP, 'comp_label', 2580, 440, operand='over')
res(comp_label)
W(label_lvl, comp_label, 0)
W(shock, comp_label, 1)

grade = C(levelTOP, 'grade', 2740, 440)
soft(grade, gamma1=0.95, contrast=1.05, blacklevel=0.0, brightness1=1.0)
# contrast pivots on 0.5 and pushes darks below zero; clamp the floor only, and it
# is clamphigh2 that governs the ceiling, not clamphigh
soft(grade, clamp=True, clamplow2=0.0, clamphigh2=4.0)
W(comp_label, grade)

final_out = C(nullTOP, 'final_out', 2900, 440)
W(grade, final_out)
out1 = C(outTOP, 'out1', 3060, 440)
W(final_out, out1)

pout = proj.create(outTOP, SCENE + '_out')
pout.nodeX, pout.nodeY = 400, -1100
s.outputConnectors[0].connect(pout.inputConnectors[0])


# ---------------------------------------------------------------------------
# PADS AND KEYS — 1-9 chapters, 0 restart, L look, G startle, N reseed
# ---------------------------------------------------------------------------
PEXEC_BODY = '''# A chapter is a SEEK, not a freeze-frame: show = monotonic musical clock minus
# Timeoffset, so jumping to T is Timeoffset = musical_now - T and the journey simply
# carries on from where it lands. Nothing is ever paused.
#
# The three performance pads do not seek. They push a verb into the director's queue,
# so they work at any point in the story and leave the playhead alone — which is what
# you want when the track does something the schedule did not expect.


def _seek(comp, seconds):
    d = comp.op('director')
    mus = float(d['musical'][0]) if d is not None and d.numChans else 0.0
    comp.par.Timeoffset = mus - max(0.02, seconds)


def _index(comp):
    return int(round(float(comp.par.Chapter.eval())))


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

    if n == 'Look':
        _push(comp, 'look')
    elif n == 'Startle':
        _push(comp, 'gust')
    elif n == 'Reseed':
        _push(comp, 'reseed')
    elif n == 'Restart':
        _seek(comp, 0.0)
    elif n == 'Nextcp':
        _seek(comp, CHECKPOINTS[(_index(comp) + 1) % len(CHECKPOINTS)][2] * slen)
    elif n == 'Prevcp':
        _seek(comp, CHECKPOINTS[(_index(comp) - 1) % len(CHECKPOINTS)][2] * slen)
    elif n.startswith('Go'):
        want = n[2:].lower()
        if want in names:
            _seek(comp, CHECKPOINTS[names.index(want)][2] * slen)
    return
'''

pexec = C(parameterexecuteDAT, 'checkpoint_exec', 2100, 1000)
pexec.text = hdr(CHECKPOINTS=CHECKPOINTS) + PEXEC_BODY
pexec.par.op = s.path
soft(pexec, pars='Look Startle Reseed Restart Nextcp Prevcp '
     + ' '.join('Go' + cp[0] for cp in CHECKPOINTS),
     valuechange=False, onpulse=True)

KEY_BODY = '''# 1-9 walk him to a chapter and let the journey keep playing; 0 starts again.
#   l  LOOK    — make him notice, wherever he is. Hold it under a breakdown.
#   g  STARTLE — a gust: everything bends, and something goes up off the far bank.
#   n  RESEED  — a new swamp. Same journey, nothing repeats.


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
    elif k == 'l':
        comp.par.Look.pulse()
    elif k == 'g':
        comp.par.Startle.pulse()
    elif k == 'n':
        comp.par.Reseed.pulse()
    return


def onShortcut(dat, shortcutName, time):
    return
'''

keyin = C(keyboardinDAT, 'key_pad', 1780, 700)
keyin.par.keys = '1 2 3 4 5 6 7 8 9 0 l g n'
kcb = keyin.par.callbacks.eval()
if kcb is None:
    kcb = C(textDAT, 'key_pad_callbacks', 1780, 620)
    keyin.par.callbacks = kcb.path
kcb.nodeX, kcb.nodeY = 1780, 620
kcb.text = hdr(CHECKPOINTS=CHECKPOINTS) + KEY_BODY

frame_exec = C(executeDAT, 'frame_exec', 2260, 1000)
frame_exec.text = '''# TD only cooks what something is pulling on. The director holds musical time and
# the event counters; the engine holds the walk. Neither may stop when the scene is
# off screen, or the journey pauses and then jumps when it comes back.
#
# Order matters: the director publishes the counters the engine reads in the same
# frame.


def onFrameStart(frame):
    d = op('director')
    if d is not None:
        d.cook()
    e = op('engine')
    if e is not None:
        e.cook()
    return
'''
soft(frame_exec, framestart=True)

s.par.display = True
s.par.opviewer = final_out.path
s.store('pending', [])

timer.par.initialize.pulse()
timer.par.start.pulse()
director.cook(force=True)
engine.cook(force=True)

# Menu values are accepted silently and land on the first entry when wrong, so the
# ones that would quietly ruin the scene are asserted rather than trusted.
for _got, _want, _what in (
        (cam.par.projection.eval(), 'ortho', 'camera projection'),
        (g_lines.par.instancecolormode.eval(), 'replace', 'instance colour mode'),
        (comp.par.operand.eval(), 'over', 'scene composite operand'),
        (comp_glow.par.operand.eval(), 'add', 'glow composite operand')):
    if _got != _want:
        print('  [CHECK FAILED] %s is %r, expected %r' % (_what, _got, _want))

print('built %s' % s.path)
print('  journey: %s' % ' -> '.join(d['name'] for d in DISCOVERIES))
print('  %.1f world units | waterline %.3f | pool %d' % (TOTALX, WATERY, MAXSEG))
print('  %s' % eng_src.module._S['S']['census'])
print('  keys: 1-9 chapters | 0 restart | l look | g startle | n reseed')
