# Monsoon — a harmonium on a street corner, the rain that arrives halfway through,
# and everyone who walks past without stopping.
#
# A fixed camera on one corner. The first third is dry: he is already playing, the
# evening crowd is already going home, and the wind gets up. Then it starts, and by
# the time the sky opens he has been out in it for two chapters and has not moved.
#
# DRAWN FLAT, NOT DRAWN AS WIREFRAME. Everything is a filled shape with a hard
# shadow side and a bold outline, in the register of an animated series cel: flat
# colour blocked in, no gradients inside a shape, one light source, strong
# silhouettes. Every filled shape and every outline in the scene is the SAME
# primitive — one instanced unit quad with a per-instance width — so a hairline
# outline and a solid slab of colour cost exactly the same and come out of the same
# pool. A convex shape is filled by horizontal slabs; a limb is a single fat quad.
#
# THE COLOUR IS THE STORY. The world is blue, the air is purple, and the only red in
# the frame is him. Anyone who passes close enough picks up his lamp on the side
# facing him and loses it again on the way out.
#
# BUILT FOR A SWITCH. This is one tox among sixteen, so the cost of NOT being on
# screen mattered more than the cost of being on it: fixed camera so there is no
# world to store, six TOPs none of which is a pass-through, the volume of the rain
# procedural in the shader rather than in the instance pool, and no executeDAT
# keep-alive — TD is pull-based, and unselected this costs one timer CHOP.
#
# Idempotent: destroys and recreates /project1/monsoon and its project-level Out TOP.
# No media files needed.
#     code = open('scenes/monsoon/build.py', encoding='utf-8').read()
#     g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)

import math
import os

SCENE = 'monsoon'
OUTW, OUTH = 1280, 720
ASPECT = OUTW / OUTH
ORTHOW = 2.0
ORTHOH = ORTHOW / ASPECT
CLOCKLEN = 60.0

STORYDEF = 240.0
MAXSEG = 3000            # instance pool; fixed, never resized
GROUNDY = -0.260         # the wet street, in world y
MUSX = -0.245            # where he sits
MSCALE = 0.440
# 1280 px across an ortho width of 2.0 is 640 px per world unit, so an outline of
# 0.0052 is a 3.3 px line. Bold enough to read as drawn rather than as wireframe.
LWCHAR = 0.0052          # character outlines
LWBG = 0.0034            # background outlines

# Flat, desaturated, limited — blocked in rather than lit. Each surface gets a
# SHADOW value and a LIT value and nothing in between, which is what makes a flat
# cel read as form instead of as a sticker.
PAL = dict(
    SKYTOP=(0.098, 0.108, 0.208),
    SKYLOW=(0.290, 0.180, 0.330),
    BLDGFAR=(0.115, 0.108, 0.198),
    BLDGDK=(0.078, 0.074, 0.150),
    BLDGLT=(0.158, 0.140, 0.252),
    WINDOW=(0.880, 0.430, 0.560),
    ROAD=(0.150, 0.130, 0.230),
    KERB=(0.245, 0.205, 0.340),
    FOREDK=(0.052, 0.048, 0.105),
    PERSONDK=(0.150, 0.170, 0.305),
    PERSONLT=(0.355, 0.415, 0.660),
    PERSONED=(0.585, 0.665, 0.930),
    MUSDK=(0.430, 0.115, 0.180),
    MUSLT=(0.840, 0.245, 0.265),
    MUSED=(1.000, 0.440, 0.390),
    HARMDK=(0.310, 0.125, 0.205),
    HARMLT=(0.615, 0.230, 0.300),
    LAMP=(1.000, 0.490, 0.360),
    LAMPCORE=(1.000, 0.790, 0.570),
    RAIN=(0.620, 0.720, 1.000),
    RAINFAR=(0.380, 0.450, 0.760),
    PURPLE=(0.720, 0.390, 0.960),
    FLASH=(0.780, 0.730, 1.000),
)

# Eight chapters, and the weather is now a real arc rather than a level: three dry
# chapters with a rising wind, rain from 4, and the sky only opens at 6. Everything
# before that is a man playing to people who are walking home.
CHECKPOINTS = [
    ('street',  ' 1 - The Street',        0.000),
    ('evening', ' 2 - Evening Crowd',     0.135),
    ('wind',    ' 3 - The Wind Gets Up',  0.270),
    ('first',   ' 4 - It Starts to Rain', 0.400),
    ('steady',  ' 5 - Steady Rain',       0.530),
    ('thunder', ' 6 - Thunder',           0.660),
    ('listen',  ' 7 - Someone Stops',     0.800),
    ('easing',  ' 8 - It Eases',          0.910),
]

proj = op('/project1')
for stale in (SCENE, SCENE + '_out'):
    o = proj.op(stale)
    if o:
        o.destroy()

s = proj.create(containerCOMP, SCENE)
s.nodeX, s.nodeY = 0, -1500
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

    TD accepts an invalid menu value SILENTLY and lands on entry zero — which is
    how `bayou` shipped with antialias='msaa4x' quietly meaning 'no antialiasing'
    for its entire life. Never assign a menu value you have not seen in the list.
    """
    names = list(par.menuNames or [])
    for wname in wanted:
        if wname in names:
            par.val = wname
            return wname
    print('  [menu] %s: none of %s in %s' % (par.name, wanted, names))
    return par.eval()


def hdr(**kw):
    return ''.join('%s = %r\n' % (k, v) for k, v in sorted(kw.items())) + '\n'


# ---------------------------------------------------------------------------
# PERFORMANCE SURFACE
# ---------------------------------------------------------------------------
pg = s.appendCustomPage('Monsoon')
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
    ('Brightness', 'Brightness',          1.0, 0.2, 2.0),
    ('Rain',       'Rain',                1.0, 0.0, 2.0),
    ('Rainaudio',  'Rain rides Audio',    1.0, 0.0, 3.0),
    ('Wind',       'Wind',                1.0, -2.0, 3.0),
    ('Crowd',      'Crowd',               1.0, 0.0, 2.0),
    ('Thunder',    'Thunder',             1.0, 0.0, 2.0),
    ('Drone',      'Harmonium Drone',     1.0, 0.0, 2.0),
    ('Lamp',       'His Lamp',            1.0, 0.0, 2.0),
    ('Reflect',    'Wet Street',          1.0, 0.0, 2.0),
    ('Linewidth',  'Outline Weight',      1.0, 0.2, 3.0),
    ('Ink',        'Brightness of Art',   1.05, 0.0, 3.0),
    ('Glow',       'Glow',                1.0, 0.0, 3.0),
    ('Label',      'Chapter Readout',     1.0, 0.0, 2.0),
    ('Vignette',   'Vignette',            0.70, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

for _mn, _ml, _lo, _hi in (('Bpm', 'Detected BPM', 0.0, 200.0),
                           ('Showt', 'Story Time (s)', 0.0, 2400.0),
                           ('Chapter', 'Chapter', 0.0, float(len(CHECKPOINTS))),
                           ('Flash', 'Lightning', 0.0, 1.0),
                           ('Afterglow', 'Afterglow', 0.0, 1.0),
                           ('Rainnow', 'Rain Level', 0.0, 1.0),
                           ('Windnow', 'Wind Level', 0.0, 2.0),
                           ('Walkers', 'People On Screen', 0.0, 16.0),
                           ('Segs', 'Quads Drawn', 0.0, float(MAXSEG)),
                           ('Labelfade', 'Readout Fade', 0.0, 1.0),
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

pg.appendPulse('Bolt', label='T - THUNDER (open the sky)')
pg.appendPulse('Passer', label='P - PASSER-BY (send someone across)')
pg.appendPulse('Stopper', label='S - SOMEONE STOPS (and listens)')
pg.appendPulse('Reseed', label='N - RESEED (new street, new crowd)')
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
DIRECTOR_BODY = '''# Musical time is monotonic and never seeks; the playhead is a subtraction from it
# (show = musical - Timeoffset), so a chapter jump is one parameter write and the
# story carries on from where it lands.
#
# Discrete events are MONOTONIC COUNTERS, never one-frame flags. A flag is lost if
# the engine cooks twice in a frame or not at all — and in a switch rig, where this
# scene is skipped for minutes at a time and then cuts back in, that is not a corner
# case, it is the normal path.
import math

_clock = {'last_raw': None, 'musical': 0.0}
_st = {'peak': {'bass': PEAKFLOOR, 'high': PEAKFLOOR, 'energy': PEAKFLOOR},
       'kickenv': 0.0, 'dropenv': 0.0, 'flash': 0.0, 'after': 0.0,
       'bolt': 0, 'passer': 0, 'stopper': 0, 'reseed': 0,
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
        st['dropenv'] *= 0.5 ** (dt / 0.90)
        # THE FLASH AND THE AFTERGLOW ARE TWO DIFFERENT CLOCKS, and getting that
        # wrong is what makes stage lightning look like a dimmer. The strike is
        # gone in a tenth of a second; the purple it leaves in the air takes two
        # seconds to go. One envelope cannot be both.
        st['flash'] *= 0.5 ** (dt / 0.055)
        st['after'] *= 0.5 ** (dt / 1.40)

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

    # The playhead WRAPS here, unlike the journey scenes. There is no destination on
    # this street corner — it is the same rain at minute forty as at minute four —
    # so a clamp would just mean the arc dies and the scene goes static mid-set.
    slen = max(1.0, float(par.Storylen.eval()))
    show = (musical - float(par.Timeoffset.eval())) % slen

    pending = comp.fetch('pending', None)
    if pending:
        comp.store('pending', [])
        for what in pending:
            if what == 'bolt':
                st['bolt'] += 1
            elif what == 'passer':
                st['passer'] += 1
            elif what == 'stopper':
                st['stopper'] += 1
            elif what == 'reseed':
                st['reseed'] += 1

    out = {
        'rawtime': raw, 'musical': musical, 'show': show, 'tempofactor': factor,
        'bass': bass, 'high': high, 'energy': energy,
        'kick': kick, 'kickenv': st['kickenv'], 'beatstr': beatstr,
        'drop': drop, 'dropenv': st['dropenv'],
        'kickcnt': float(st['kicks']), 'accentcnt': float(st['accents']),
        'dropcnt': float(st['drops']), 'boltcnt': float(st['bolt']),
        'passercnt': float(st['passer']), 'stoppercnt': float(st['stopper']),
        'reseedcnt': float(st['reseed']),
        'storylen': slen,
    }

    # The engine owns when lightning strikes (it needs the story arc to decide);
    # the director owns the two envelopes it leaves behind, because the shader
    # reads them by expression and must never wait a frame for them.
    fire = comp.fetch('strike', 0.0)
    if fire > 0.5:
        comp.store('strike', 0.0)
        st['flash'] = 1.0
        st['after'] = 1.0
    out['flash'] = st['flash']
    out['after'] = st['after']

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
        par.Flash.val = st['flash']
        par.Afterglow.val = st['after']
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

# ---------------------------------------------------------------------------
# THE ENGINE — the street, the drizzle, and the man playing through it
# ---------------------------------------------------------------------------
ENGINE_BODY = r'''# One fixed camera on one corner, so there is no world to store and no camera to
# track. Everything is emitted per frame as ONE primitive: a rotated, filled quad,
# instanced from a unit square with a per-instance width.
#
# THAT SINGLE PRIMITIVE IS THE WHOLE DRAWING SYSTEM, and it is why the flat style
# costs nothing extra over the wireframe it replaced:
#   an OUTLINE  is a quad 3 px wide along the edge
#   a LIMB      is one fat quad from joint to joint
#   a FILL      is a stack of horizontal quads scanned across a convex outline
#   a WINDOW    is one quad
# A hairline and a solid block of colour are the same instance out of the same pool,
# so blocking in flat colour did not cost a second render pass, a second material,
# or a triangulator.
#
# WHAT IS GEOMETRY AND WHAT IS NOT. The volume of the rain — the sheets, the haze,
# the wet sheen on the road — is in the shader, where a million drops cost what one
# costs. Geometry is only the near streaks that must fall IN FRONT of people and the
# splashes that land on the actual street line. It is a drizzle for most of the
# piece, so there are 150 of them and not thousands.
import math
import random
import numpy as np

_S = {'S': None}


def _ss(a, b, x):
    t = (x - a) / (b - a if b != a else 1e-9)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return t * t * (3.0 - 2.0 * t)


# --- the one primitive, and the three things built out of it ---------------------
def _seg(out, x0, y0, x1, y1, col, a, z=0.0, w=LWCHAR, fl=0.0):
    out.append((x0, y0, x1, y1, col[0], col[1], col[2], a, z, fl, w))


def _path(out, pts, col, a, z=0.0, w=LWCHAR, fl=0.0, close=False):
    n = len(pts)
    rng = range(n) if close else range(n - 1)
    for i in rng:
        p, q = pts[i], pts[(i + 1) % n]
        out.append((p[0], p[1], q[0], q[1], col[0], col[1], col[2], a, z, fl, w))


def _rect(out, cx, cy, w, h, col, a, z=0.0, fl=0.0):
    """An axis-aligned filled rectangle: one instance, no scanning needed."""
    out.append((cx, cy - h * 0.5, cx, cy + h * 0.5,
                col[0], col[1], col[2], a, z, fl, w))


def _fill(out, pts, col, a, z=0.0, fl=0.0, slabs=0):
    """Fill a CONVEX polygon with horizontal slabs.

    Each slab is one quad lying on its side, so an arbitrary flat shape costs a
    handful of instances and needs no triangulation. Slabs overlap by 6% because
    at a slab height of two pixels a seam is a visible stripe through the shape.
    """
    ys = [p[1] for p in pts]
    lo, hi = min(ys), max(ys)
    hgt = hi - lo
    if hgt < 1e-5:
        return
    n = slabs if slabs else max(3, min(16, int(hgt / 0.014) + 2))
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
        out.append((xa, yc, xb, yc, col[0], col[1], col[2], a, z, fl, dh * 1.06))


def _ngon(out, cx, cy, r, n, rot, col, a, z=0.0, w=LWCHAR, fl=0.0, ry=None):
    ry = r if ry is None else ry
    pts = [(cx + r * math.cos(rot + i * 2.0 * math.pi / n),
            cy + ry * math.sin(rot + i * 2.0 * math.pi / n)) for i in range(n)]
    _path(out, pts, col, a, z, w, fl, close=True)
    return pts


def _mix(c1, c2, k):
    k = 0.0 if k < 0.0 else (1.0 if k > 1.0 else k)
    return (c1[0] + (c2[0] - c1[0]) * k, c1[1] + (c2[1] - c1[1]) * k,
            c1[2] + (c2[2] - c1[2]) * k)


def _knee(hx, hy, fx, fy, l1, l2, sgn):
    dx, dy = fx - hx, fy - hy
    raw = max(math.hypot(dx, dy), 1e-6)
    ux, uy = dx / raw, dy / raw
    d = min(max(raw, 0.010), l1 + l2 - 0.002)
    fx, fy = hx + ux * d, hy + uy * d
    aa = (l1 * l1 - l2 * l2 + d * d) / (2.0 * d)
    hh = math.sqrt(max(0.0, l1 * l1 - aa * aa))
    return (hx + ux * aa - uy * hh * sgn, hy + uy * aa + ux * hh * sgn, fx, fy)


def _rh(i):
    x = math.sin(i * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


# --- the city, blocked in flat ---------------------------------------------------
# A building is ONE filled quad plus its windows. Static, generated once per seed:
# 12 blocks and their windows come to under 40 KB, which is the whole argument for
# algorithmic scenery — this backdrop costs a two-hundredth of one 1280x720 texture.
def _gen_static(rs):
    rows = []      # x0,y0,x1,y1,r,g,b,a,z,w,kind   kind 1 = window (flickers)
    def block(x0, y0, x1, y1, col, al, z, kind=0):
        rows.append((x0, (y0 + y1) * 0.5, x1, (y0 + y1) * 0.5,
                     col[0], col[1], col[2], al, z, abs(y1 - y0), kind))

    # three receding ranks, darkest at the back so the skyline reads as depth
    for rank, (base, tone, zz, hmul) in enumerate((
            (SKYBASE + 0.050, BLDGFAR, -0.62, 1.00),
            (SKYBASE + 0.012, BLDGDK, -0.56, 0.86),
            (SKYBASE - 0.010, BLDGLT, -0.50, 0.66))):
        x = -1.34 - rs.uniform(0.0, 0.14)
        while x < 1.34:
            w = rs.uniform(0.13, 0.32)
            h = rs.uniform(0.16, 0.46) * hmul
            block(x, base, x + w, base + h, tone, 1.0, zz)
            if rank == 2 and rs.random() < 0.40:           # a tank or a stack
                ax = x + w * rs.uniform(0.2, 0.7)
                block(ax, base + h, ax + 0.035, base + h + rs.uniform(0.03, 0.08),
                      tone, 1.0, zz)
            if rank >= 1:
                cols = max(1, int(w / 0.062))
                rws = max(1, int(h / 0.072))
                for ci in range(cols):
                    for ri in range(rws):
                        if rs.random() > (0.30 if rank == 2 else 0.18):
                            continue
                        wx = x + 0.020 + ci * 0.062
                        wy = base + 0.030 + ri * 0.072
                        if wx + 0.024 > x + w - 0.012 or wy + 0.032 > base + h - 0.016:
                            continue
                        block(wx, wy, wx + 0.024, wy + 0.032, WINDOW,
                              rs.uniform(0.55, 1.0), zz + 0.01, kind=1)
            x += w + rs.uniform(0.004, 0.030)

    # the far pavement and the kerb: two flat bands, and the only edge the figures
    # are allowed to stand on
    block(-1.34, GROUNDY + 0.082, 1.34, GROUNDY + 0.155, BLDGDK, 1.0, -0.44)
    block(-1.34, GROUNDY + 0.074, 1.34, GROUNDY + 0.092, KERB, 0.85, -0.42)
    block(-1.34, GROUNDY - 0.004, 1.34, GROUNDY + 0.006, KERB, 0.55, -0.24)

    X0, Y0, X1, Y1, R, G, B, A, Z, WD, K = ([] for _ in range(11))
    for (a0, b0, a1, b1, r_, g_, b2, al, z, wd, kind) in rows:
        X0.append(a0); Y0.append(b0); X1.append(a1); Y1.append(b1)
        R.append(r_); G.append(g_); B.append(b2)
        A.append(al); Z.append(z); WD.append(wd); K.append(kind)
    f = lambda L: np.array(L, dtype=np.float64)
    return dict(x0=f(X0), y0=f(Y0), x1=f(X1), y1=f(Y1), r=f(R), g=f(G), b=f(B),
                a=f(A), z=f(Z), w=f(WD), kind=f(K), n=len(X0),
                fph=f([rs.uniform(0.0, 6.283) for _ in X0]))


# --- the two lampposts that frame the shot ---------------------------------------
def _posts(out, ink, flash):
    col = _mix(FOREDK, FLASH, 0.35 * flash)
    for px, sc in ((-1.02, 1.0), (1.06, 0.92)):
        _seg(out, px, GROUNDY - 0.02, px, GROUNDY + 0.60 * sc, col, ink,
             0.42, 0.020)
        _seg(out, px, GROUNDY + 0.60 * sc, px + 0.10, GROUNDY + 0.625 * sc,
             col, ink, 0.42, 0.014)
        _fill(out, [(px + 0.075, GROUNDY + 0.612 * sc),
                    (px + 0.145, GROUNDY + 0.640 * sc),
                    (px + 0.165, GROUNDY + 0.596 * sc),
                    (px + 0.090, GROUNDY + 0.574 * sc)], col, ink, 0.42)


# --- the man, blocked in flat ----------------------------------------------------
# One light source: his own lamp, on his right. So every shape gets a LIT value on
# the lamp side and a SHADOW value on the other, with a hard edge between them and
# nothing in between. That hard edge is the whole difference between a flat cel and
# a coloured-in wireframe.
def _musician(out, ox, oy, sc, pump, press, ink, lamp, kickenv, high, t, flash):
    def T(x, y):
        return (ox + x * sc, oy + y * sc)

    LWC = LWCHAR * LINEW
    lt, dk, ed = MUSLT, MUSDK, MUSED
    hlt, hdk = HARMLT, HARMDK
    z = 0.06

    # --- the harmonium: a front face, a top face, and a keyboard ----------------
    fl_, fr_, fb_, ft_ = 0.10, 0.52, 0.02, 0.20
    dx_, dy_ = 0.072, 0.052
    _fill(out, [T(fl_, fb_), T(fr_, fb_), T(fr_, ft_), T(fl_, ft_)], hdk, ink, z)
    _fill(out, [T(fl_, ft_), T(fl_ + dx_, ft_ + dy_), T(fr_ + dx_, ft_ + dy_),
                T(fr_, ft_)], hlt, ink, z + 0.004)
    _path(out, [T(fl_, fb_), T(fr_, fb_), T(fr_, ft_), T(fl_, ft_)], ed,
          ink * 0.85, z + 0.02, LWC, close=True)
    _path(out, [T(fl_, ft_), T(fl_ + dx_, ft_ + dy_), T(fr_ + dx_, ft_ + dy_),
                T(fr_, ft_)], ed, ink * 0.85, z + 0.02, LWC, close=True)

    NK = 11
    for i in range(NK):
        u = i / float(NK)
        kx = fl_ + 0.022 + u * (fr_ - fl_ - 0.044)
        dn = 0.010 if i == press else 0.0
        kc = LAMPCORE if i == press else _mix(hlt, (1.0, 1.0, 1.0), 0.45)
        _fill(out, [T(kx, ft_ - dn), T(kx + 0.020, ft_ - dn),
                    T(kx + 0.020 + dx_ * 0.62, ft_ + dy_ * 0.62 - dn),
                    T(kx + dx_ * 0.62, ft_ + dy_ * 0.62 - dn)],
              kc, ink * (1.15 if i == press else 0.80), z + 0.008, slabs=3)

    # --- the bellows: a hinged flap, and the pleats really compress -------------
    hx_, hy_ = fr_ + dx_ * 0.55, ft_ + dy_ * 0.72
    ang = 0.24 + 0.46 * pump
    tipx, tipy = hx_ + 0.108 * math.cos(ang), hy_ + 0.108 * math.sin(ang)
    bx0, by0 = fr_ - 0.03, ft_ + dy_ * 0.34
    bx1e = fr_ + dx_ * 0.92
    _fill(out, [T(hx_, hy_), T(tipx, tipy), T(tipx - 0.030, tipy - 0.062),
                T(bx1e, by0), T(bx0, by0)], hlt, ink, z + 0.002)
    for i in range(1, 5):
        u = i / 5.0
        ax_ = hx_ + (tipx - hx_) * u
        ay_ = hy_ + (tipy - hy_) * u
        bxx = bx0 + (bx1e - bx0) * u
        bulge = 0.026 * (1.0 - 0.70 * pump) * math.sin(math.pi * u)
        _path(out, [T(ax_, ay_),
                    T((ax_ + bxx) * 0.5 + bulge, (ay_ + by0) * 0.5 - bulge * 0.4),
                    T(bxx, by0)], ed, ink * 0.55, z + 0.02, LWC * 0.8)
    _path(out, [T(hx_, hy_), T(tipx, tipy), T(tipx - 0.030, tipy - 0.062),
                T(bx1e, by0)], ed, ink * 0.9, z + 0.02, LWC)

    # --- the open case --------------------------------------------------------
    _fill(out, [T(-0.46, 0.02), T(-0.21, 0.02), T(-0.21, 0.085), T(-0.46, 0.085)],
          hdk, ink, z)
    _path(out, [T(-0.46, 0.02), T(-0.21, 0.02), T(-0.21, 0.085), T(-0.46, 0.085)],
          ed, ink * 0.8, z + 0.02, LWC, close=True)
    _path(out, [T(-0.46, 0.085), T(-0.52, 0.155)], ed, ink * 0.7, z + 0.02, LWC)

    # --- the player -----------------------------------------------------------
    rock = (pump - 0.5) * 0.055 + kickenv * 0.008
    hipx, hipy = -0.10, 0.17
    shx, shy = 0.02 + rock, 0.51 - abs(rock) * 0.5
    legs = [T(-0.36, 0.02), T(0.11, 0.02), T(-0.09, 0.195)]
    _fill(out, legs, dk, ink, z + 0.03)
    _path(out, legs, ed, ink * 0.9, z + 0.05, LWC, close=True)
    torso = [T(hipx - 0.105, hipy), T(hipx + 0.105, hipy),
             T(shx + 0.095, shy), T(shx - 0.095, shy)]
    _fill(out, torso, dk, ink, z + 0.03)
    # the lamp side, hard-edged: the right third of the torso only
    _fill(out, [T(hipx + 0.020, hipy), T(hipx + 0.105, hipy),
                T(shx + 0.095, shy), T(shx + 0.018, shy)], lt, ink, z + 0.035)
    _path(out, torso, ed, ink * 0.95, z + 0.05, LWC, close=True)

    hdx, hdy = shx + 0.030, shy + 0.115
    head = [T(hdx + 0.106 * math.cos(a), hdy + 0.118 * math.sin(a))
            for a in [i * 2.0 * math.pi / 7.0 for i in range(7)]]
    _fill(out, head, dk, ink, z + 0.03)
    _fill(out, [T(hdx + 0.012, hdy - 0.114), T(hdx + 0.106, hdy - 0.046),
                T(hdx + 0.100, hdy + 0.072), T(hdx + 0.024, hdy + 0.114)],
          lt, ink, z + 0.035)
    _path(out, head, ed, ink, z + 0.05, LWC, close=True)
    _seg(out, *(T(shx, shy) + T(hdx - 0.020, hdy - 0.085)), dk, ink, z + 0.02,
         0.052 * sc)

    # arms: one fat quad per bone, which is what a flat cel limb is
    kpx = fl_ + 0.022 + (press / float(NK)) * (fr_ - fl_ - 0.044) + dx_ * 0.45
    for (sx0, sy0, tx0, ty0, cc, aa) in (
            (shx + 0.075, shy - 0.030, kpx, ft_ + dy_ * 0.55, lt, 1.0),
            (shx + 0.020, shy - 0.020, hx_ - 0.010, hy_ + 0.030, dk, 0.62)):
        ekx, eky, fxx, fyy = _knee(sx0, sy0, tx0, ty0, 0.22, 0.21, -1.0)
        wmul = 1.0 if aa > 0.8 else 0.72
        _seg(out, *(T(sx0, sy0) + T(ekx, eky)), cc, ink * aa, z + 0.04,
             0.056 * sc * wmul)
        _seg(out, *(T(ekx, eky) + T(fxx, fyy)), cc, ink * aa, z + 0.04,
             0.046 * sc * wmul)

    # --- the lamp: the only light source in the scene --------------------------
    lx_, ly_ = 0.80, 0.14
    la = ink * lamp * (0.88 + 0.22 * math.sin(t * 5.3) + 0.24 * kickenv)
    _fill(out, [T(lx_ - 0.05, 0.02), T(lx_ + 0.05, 0.02), T(lx_ + 0.02, ly_ - 0.05),
                T(lx_ - 0.02, ly_ - 0.05)], hdk, ink, z)
    lamp_pts = [(T(lx_ + 0.062 * math.cos(a), ly_ + 0.062 * math.sin(a)))
                for a in [i * math.pi / 3.0 + 0.26 for i in range(6)]]
    _fill(out, lamp_pts, LAMP, la, z + 0.03)
    _fill(out, [T(lx_ + 0.026 * math.cos(a), ly_ + 0.026 * math.sin(a))
                for a in [i * math.pi / 2.0 for i in range(4)]],
          LAMPCORE, la * 1.25, z + 0.04, slabs=4)
    _path(out, lamp_pts, ed, ink * 0.9, z + 0.05, LWC, close=True)
    _seg(out, *(T(lx_, ly_ + 0.062) + T(lx_, ly_ + 0.125)), ed, ink * 0.7,
         z + 0.02, LWC)
    for i in range(6):
        a = i * math.pi / 3.0 + t * 0.22
        r0, r1 = 0.088, 0.088 + 0.052 * (0.5 + 0.5 * math.sin(t * 2.1 + i))
        _seg(out, *(T(lx_ + r0 * math.cos(a), ly_ + r0 * math.sin(a))
                    + T(lx_ + r1 * math.cos(a), ly_ + r1 * math.sin(a))),
             LAMP, la * 0.45, z + 0.01, LWC * 0.8)
    return T(0.36, ft_ + dy_), T(lx_, ly_)


# --- someone walking past --------------------------------------------------------
# Built once in local coordinates facing +x and mirrored through T. Doing the mirror
# in the transform rather than in the pose is what keeps the knee bending forwards in
# both directions — solve the pose in world space with a mirrored frame and every
# figure walking left has its legs on backwards.
def _person(out, px, gy, sc, ph, umb, al, redk, facing, lean, ink, t, stopped,
            rain, flash):
    def T(lx, ly):
        return (px + facing * lx * sc, gy + ly * sc)

    LWC = LWCHAR * LINEW
    a = al * ink
    dk = _mix(PERSONDK, LAMP, redk * 0.55)
    lt = _mix(PERSONLT, LAMP, redk)
    ed = _mix(PERSONED, LAMPCORE, redk)
    if flash > 0.02:            # the strike silhouettes everyone against the sky
        dk = _mix(dk, FOREDK, flash * 0.70)
        lt = _mix(lt, FOREDK, flash * 0.55)
    z = 0.0 + sc * 0.10

    hipy = 0.47
    for li, off in ((1, 0.5), (0, 0.0)):
        A, lift, duty = 0.155, 0.10, 0.60
        p = (ph + off) % 1.0
        if stopped:
            fx, fy = (0.085 if li else -0.070), 0.0
        elif p < duty:
            fx, fy = A - 2.0 * A * (p / duty), 0.0
        else:
            k = (p - duty) / (1.0 - duty)
            fx, fy = -A + 2.0 * A * k, lift * math.sin(math.pi * k)
        kx, ky, fx, fy = _knee(0.0, hipy, fx, fy, 0.26, 0.25, 1.0)
        cc = dk if li else lt
        la = a * (0.80 if li else 1.0)
        _seg(out, *(T(0.0, hipy) + T(kx, ky)), cc, la, z + 0.01, 0.085 * sc)
        _seg(out, *(T(kx, ky) + T(fx, fy)), cc, la, z + 0.01, 0.072 * sc)
        _seg(out, *(T(fx, fy) + T(fx + 0.062, fy)), cc, la, z + 0.012, 0.038 * sc)

    shy = 0.82
    coat = [T(-0.086, hipy - 0.10), T(0.086, hipy - 0.10),
            T(0.092 + lean, shy), T(-0.092 + lean, shy)]
    _fill(out, coat, dk, a, z + 0.02)
    _fill(out, [T(0.016, hipy - 0.10), T(0.086, hipy - 0.10),
                T(0.092 + lean, shy), T(0.020 + lean, shy)], lt, a, z + 0.025)
    _path(out, coat, ed, a * 0.95, z + 0.05, LWC, close=True)

    hdx, hdy = lean * 1.15 + 0.012, 0.930
    head = [T(hdx + 0.092 * math.cos(ang), hdy + 0.104 * math.sin(ang))
            for ang in [i * math.pi / 3.0 + 0.30 for i in range(6)]]
    _fill(out, head, dk, a, z + 0.02)
    _fill(out, [T(hdx + 0.006, hdy - 0.100), T(hdx + 0.092, hdy - 0.034),
                T(hdx + 0.082, hdy + 0.072), T(hdx + 0.012, hdy + 0.100)],
          lt, a, z + 0.025)
    _path(out, head, ed, a, z + 0.05, LWC, close=True)

    if stopped:
        hxk, hyk = 0.045, 0.50
    else:
        hxk = 0.115 * math.cos(2.0 * math.pi * (ph + 0.5))
        hyk = 0.52 + 0.035 * math.sin(2.0 * math.pi * (ph + 0.5))
    ekx, eky, hxk, hyk = _knee(0.070 + lean, shy - 0.030, hxk, hyk, 0.20, 0.19, -1.0)
    _seg(out, *(T(0.070 + lean, shy - 0.030) + T(ekx, eky)), lt, a, z + 0.04,
         0.062 * sc)
    _seg(out, *(T(ekx, eky) + T(hxk, hyk)), lt, a, z + 0.04, 0.052 * sc)

    # The umbrella only goes up once it is actually raining. Six people holding
    # umbrellas open on a dry evening is the single fastest way to tell an audience
    # the weather is a parameter and not a story.
    up = _ss(0.10, 0.30, rain) if umb else 0.0
    if up > 0.02:
        ucx, ucy = lean * 1.30, 1.100
        R = 0.310 * (0.40 + 0.60 * up)
        rim = [T(ucx + R * math.cos(math.pi * (1.0 - i / 7.0)),
                 ucy + R * 0.34 * math.sin(math.pi * (1.0 - i / 7.0)))
               for i in range(8)]
        _fill(out, rim, dk, a, z + 0.06)
        _fill(out, [T(ucx, ucy)] + rim[4:], lt, a, z + 0.065)
        _path(out, rim, ed, a, z + 0.08, LWC, close=True)
        _seg(out, *(T(ucx, ucy) + T(0.055 + lean, 0.79)), ed, a * 0.9, z + 0.055,
             0.016 * sc)
        for i in (0, 4, 7):
            dl = 0.05 + 0.07 * ((t * 2.3 + i * 0.37) % 1.0)
            _seg(out, rim[i][0], rim[i][1], rim[i][0], rim[i][1] - dl * sc,
                 RAIN, a * 0.45 * rain, z + 0.05, LWC * 0.7)
    return


def _bolt(out, bx, age, ink, seed):
    k = 1.0 - age / BOLTLIFE
    flick = 1.0 if (age * 46.0) % 2.0 < 1.35 else 0.28
    a = ink * 1.60 * k * flick
    if a < 0.01:
        return
    n = 11
    y0, y1 = 0.640, GROUNDY + 0.115
    pts, x = [(bx, y0)], bx
    for i in range(n):
        x += (_rh(seed * 13.0 + i * 3.7) - 0.5) * 0.115 + 0.010
        pts.append((x, y0 + (y1 - y0) * (i + 1) / float(n)))
    _path(out, pts, FLASH, a, 0.52, 0.012)
    _path(out, pts, (1.0, 1.0, 1.0), a * 0.9, 0.53, 0.004)
    for bi, si in ((0, 3), (1, 6)):
        bxx, byy = pts[si]
        d = 1.0 if _rh(seed * 5.0 + bi) > 0.5 else -1.0
        for j in range(4):
            nx = bxx + d * (0.045 + 0.030 * _rh(seed + bi * 9.0 + j))
            ny = byy - 0.055
            _seg(out, bxx, byy, nx, ny, FLASH, a * 0.62, 0.52, 0.007)
            bxx, byy = nx, ny


def _drone(out, cx, cy, amt, energy, t, ink):
    # A harmonium is a drone instrument: the sound does not pulse, it sits and
    # widens. Bands rise and spread and never repeat a beat, which is what keeps
    # them from reading as another audio meter.
    for i in range(NBAND):
        ri = (t * 0.195 + i / float(NBAND)) % 1.0
        a = ink * amt * 0.62 * ((1.0 - ri) ** 1.6) * (0.22 + 0.80 * energy)
        if a < 0.007:
            continue
        yy = cy + ri * 0.21
        hw = 0.090 + ri * 0.20
        pts = []
        for k in range(11):
            u = -1.0 + 2.0 * k / 10.0
            pts.append((cx + u * hw,
                        yy - 0.020 * u * u
                        + 0.008 * math.sin(u * 6.5 + t * 2.6 + i * 1.7)))
        _path(out, pts, PURPLE, a, -0.05, 0.0038)


# --- state ----------------------------------------------------------------------
def _new(seed):
    rs = random.Random(seed)
    u = lambda a, b, n: np.array([rs.uniform(a, b) for _ in range(n)])
    lay = np.arange(NRAIN) % 3
    return {
        'seed': seed,
        'static': _gen_static(rs),
        'rx': u(-1.50, 1.50, NRAIN), 'rph': u(0.0, 1.0, NRAIN),
        'rv': np.choose(lay, [0.30, 0.44, 0.62]) * u(0.88, 1.14, NRAIN),
        'rl': np.choose(lay, [0.040, 0.066, 0.104]) * u(0.80, 1.25, NRAIN),
        'ra': np.choose(lay, [0.22, 0.40, 0.72]),
        'rlay': lay,
        'sx': u(-1.32, 1.32, NSPL), 'sph': u(0.0, 1.0, NSPL),
        'srate': u(0.65, 2.10, NSPL),
        'sy': np.choose(np.arange(NSPL) % 3,
                        [GROUNDY, GROUNDY + 0.030, GROUNDY + 0.074]),
        'people': [], 'bolts': [], 'coins': [], 'rings': [], 'seen': {},
        'spawn_t': -9.0, 'strike_t': -9.0, 'press': 7, 'press_t': -9.0,
        'lastt': None, 'labelt': -99.0, 'lastcp': -1, 'rng': rs, 'census': '',
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


def _spawn(S, rs, crowd, t, forced=False):
    lane = 0 if rs.random() < 0.18 else (1 if rs.random() < 0.46 else 2)
    gy, sc, al = LANES[lane]
    d = 1.0 if rs.random() < 0.5 else -1.0
    S['people'].append(dict(
        x=(-1.45 if d > 0 else 1.45), gy=gy, sc=sc, al=al, dir=d,
        spd=(0.155 + 0.155 * rs.random()) * sc / 0.38 * (0.85 + 0.45 * crowd),
        umb=rs.random() < 0.78, ph=rs.random(), lane=lane,
        lean=(0.045 + 0.055 * rs.random()) * (1.0 if not forced else 0.5),
        willstop=False, stopped=False, stopuntil=0.0, gave=False))
    S['spawn_t'] = t
    return S['people'][-1]


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
    dt = min(0.20, max(0.0, t - S['lastt']))
    S['lastt'] = t

    bass = ch('bass'); high = ch('high'); energy = ch('energy')
    kickenv = ch('kickenv'); dropenv = ch('dropenv'); flash = ch('flash')

    if first and d is not None:
        for nm in ('kickcnt', 'accentcnt', 'dropcnt', 'boltcnt', 'passercnt',
                   'stoppercnt', 'reseedcnt'):
            try:
                S['seen'][nm] = float(d[nm][0])
            except Exception:
                pass

    if _delta(S, d, 'reseedcnt'):
        keep = dict(S['seen'])
        S.update(_new((S['seed'] * 1103515245 + 12345) % 2147483647))
        S['seen'] = keep
    rs = S['rng']

    slen = max(1.0, ch('storylen', 240.0))
    f = min(1.0, max(0.0, ch('show', 0.0) / slen))
    ink = float(par.Ink.eval()) * (1.0 + 0.08 * kickenv + 0.12 * dropenv
                                  + 0.30 * flash)
    rainpar = float(par.Rain.eval())
    raudio = float(par.Rainaudio.eval())
    windpar = float(par.Wind.eval())
    crowdpar = float(par.Crowd.eval())
    thunpar = float(par.Thunder.eval())
    dronepar = float(par.Drone.eval())
    lamppar = float(par.Lamp.eval())
    reflpar = float(par.Reflect.eval())

    # --- the arc. Endpoints match, so the loop has no seam ----------------------
    # THE WEATHER IS THE STORY AND THE MUSIC IS NOT. Rain used to swing +-28% with
    # the energy of the track, which made the downpour pump on the beat like a
    # compressor and left nothing else in the frame doing anything. It rides the
    # audio by 6% now, and what the music actually drives is everything that is
    # ALIVE: the bellows, the lamp, the drone, the rings on the puddles, the
    # windows. Weather moves on weather time.
    rain = float(np.interp(f, ARC_F, ARC_RAIN)) * rainpar
    crowd = float(np.interp(f, ARC_F, ARC_CROWD))
    thun = float(np.interp(f, ARC_F, ARC_THUN)) * thunpar
    wind = float(np.interp(f, ARC_F, ARC_WIND)) * windpar
    rain = rain * (1.0 + (0.06 * energy - 0.02) * raudio)
    wind = wind * (1.0 + (0.08 * bass - 0.03) * raudio)

    nbolt = _delta(S, d, 'boltcnt')
    npass = _delta(S, d, 'passercnt')
    nstop = _delta(S, d, 'stoppercnt')
    ndrop = _delta(S, d, 'dropcnt')
    nkick = _delta(S, d, 'kickcnt')
    naccent = _delta(S, d, 'accentcnt')

    # --- thunder: nothing before chapter 6, because thun is 0 there -------------
    strike = nbolt > 0
    if thun > 0.03:
        if ndrop and rs.random() < 0.25 + 0.65 * thun:
            strike = True
        gap = 2.4 + 14.0 * (1.0 - min(1.0, thun))
        if t - S['strike_t'] > gap and rs.random() < 0.025 * thun:
            strike = True
    if strike:
        S['strike_t'] = t
        S['bolts'].append([t, rs.uniform(-0.95, 0.95), rs.uniform(1.0, 900.0)])
        comp.store('strike', 1.0)
    del S['bolts'][:-3]

    # rings on the wet road, one per accented kick. Small, low, and the reason the
    # street reads as reactive without the rain having to pump.
    if naccent and rain > 0.12:
        S['rings'].append([t, rs.uniform(-1.05, 1.05),
                           GROUNDY - rs.uniform(0.02, 0.20)])
    del S['rings'][:-7]

    # --- the crowd --------------------------------------------------------------
    target = int(round(1.1 + 6.4 * crowd * crowdpar))
    if npass:
        for _ in range(npass):
            _spawn(S, rs, crowd, t, forced=True)
    if (len(S['people']) < target
            and t - S['spawn_t'] > 0.22 + 1.5 * (1.0 - crowd)):
        _spawn(S, rs, crowd, t)

    if nstop or (LISTEN0 <= f <= LISTEN1 and rs.random() < 0.004):
        best, bd = None, 9.0
        for p in S['people']:
            if p['willstop'] or p['stopped'] or p['gave']:
                continue
            ahead = (MUSX - p['x']) * p['dir']
            if ahead <= 0.15:
                continue
            score = ahead + (0.0 if p['lane'] == 2 else
                             (0.35 if p['lane'] == 1 else 1.60))
            if score < bd:
                best, bd = p, score
        if best is not None:
            best['willstop'] = True

    dead = []
    for p in S['people']:
        if p['stopped']:
            if t >= p['stopuntil']:
                p['stopped'] = False
                p['gave'] = True
                S['coins'].append([t, p['x'], p['gy'] + 0.36 * p['sc']])
        else:
            stopx = MUSX + 0.30 * p['dir']
            if (p['willstop'] and not p['gave']
                    and (stopx - p['x']) * p['dir'] <= 0.0):
                p['stopped'] = True
                p['willstop'] = False
                p['stopuntil'] = t + STOPDWELL
            else:
                step = p['dir'] * p['spd'] * dt
                p['x'] += step
                p['ph'] = (p['ph'] + abs(step) / (0.34 * p['sc'])) % 1.0
        if p['x'] < -1.60 or p['x'] > 1.60:
            dead.append(p)
    for p in dead:
        S['people'].remove(p)
    del S['coins'][:-4]

    blocks = []

    def push(rows, reflect=False):
        if not len(rows):
            return
        a = np.asarray(rows, dtype=np.float64)
        if a.ndim == 1:
            a = a.reshape(1, -1)
        blocks.append((a, reflect))


    # --- the man ----------------------------------------------------------------
    period = 60.0 / max(1.0, float(par.Refbpm.eval()))
    pump = 0.5 - 0.5 * math.cos(2.0 * math.pi * (ch('musical', 0.0)
                                                 / (period * 2.0)))
    if t - S['press_t'] > 0.35 + 0.9 * rs.random():
        S['press_t'] = t
        S['press'] = rs.randrange(11)
    mseg = []
    dcx, dcy = _musician(mseg, MUSX, GROUNDY, MSCALE, pump, S['press'], ink,
                         lamppar, kickenv, high, t, flash)
    push(mseg, reflect=True)

    dseg = []
    _drone(dseg, dcx[0], dcx[1] + 0.115, dronepar, energy, t, ink)
    push(dseg)

    # --- the people, far lane first so the near lane draws over them ------------
    for lane in (0, 1, 2):
        pseg = []
        for p in S['people']:
            if p['lane'] != lane:
                continue
            # HIS LAMP LANDS ON THEM. The whole colour idea in one expression: the
            # closer you pass him the more of his red you carry, and you lose it
            # again on the way out. A figure that stops keeps it.
            dist = abs(p['x'] - MUSX)
            redk = math.exp(-(dist / 0.62) ** 2) * 0.72 * lamppar
            if p['stopped']:
                redk = min(0.85, redk + 0.22)
            face = -p['dir'] if p['stopped'] else p['dir']
            lean = 0.0 if p['stopped'] else p['lean'] * (0.6 + 0.9 * wind * 0.3)
            _person(pseg, p['x'], p['gy'], p['sc'], p['ph'], p['umb'],
                    p['al'], redk, face, lean, ink, t, p['stopped'], rain, flash)
        push(pseg, reflect=True)

    fseg = []
    _posts(fseg, ink, flash)
    push(fseg)

    # --- coins ------------------------------------------------------------------
    cseg = []
    for c in S['coins']:
        age = t - c[0]
        if age > 1.7:
            continue
        casex, casey = MUSX - 0.335 * MSCALE, GROUNDY + 0.045
        k = min(1.0, age / 0.52)
        cx_ = c[1] + (casex - c[1]) * k
        cy_ = c[2] + (casey - c[2]) * k - 0.13 * math.sin(math.pi * k)
        if k < 1.0:
            _fill(cseg, [(cx_ - 0.012, cy_), (cx_, cy_ + 0.014),
                         (cx_ + 0.012, cy_), (cx_, cy_ - 0.014)],
                  LAMPCORE, ink * 1.1, 0.30, slabs=3)
        else:
            rr = 0.02 + 0.16 * (age - 0.52) / 1.18
            _ngon(cseg, casex, casey, rr, 8, age * 1.4, LAMPCORE,
                  ink * 0.85 * max(0.0, 1.0 - (age - 0.52) / 1.18), 0.30,
                  0.0040, ry=rr * 0.34)
    push(cseg)

    # --- rings on the puddles, one per accented kick ---------------------------
    gseg = []
    for rg in S['rings']:
        age = t - rg[0]
        if age > RINGLIFE:
            continue
        rr = 0.035 + 0.30 * (age / RINGLIFE)
        a = ink * 0.55 * ((1.0 - age / RINGLIFE) ** 2) * min(1.0, rain * 1.6)
        if a < 0.01:
            continue
        _ngon(gseg, rg[1], rg[2], rr, 9, 0.0, RAIN, a, -0.10, 0.0030,
              ry=rr * 0.24)
    push(gseg)

    bseg = []
    for b in S['bolts']:
        age = t - b[0]
        if 0.0 <= age <= BOLTLIFE:
            _bolt(bseg, b[1], age, ink, b[2])
    push(bseg)

    # --- the rain that is geometry. A drizzle is 150 streaks, not thousands -----
    ph = np.mod(S['rph'] + t * S['rv'] * (0.80 + 0.30 * rain), 1.0)
    ry0 = 0.680 - ph * 1.360
    rx0 = S['rx'] + wind * (0.680 - ry0) * 0.300
    sl = wind * 0.44
    nrm = 1.0 / math.sqrt(1.0 + sl * sl)
    rlen = S['rl'] * (0.55 + 0.75 * min(1.2, rain))
    rx1 = rx0 + sl * nrm * rlen
    ry1 = ry0 - nrm * rlen
    live = (ry1 > GROUNDY - 0.010) & (rain > 0.015)
    ra = S['ra'] * ink * (0.15 + 1.05 * rain) * (1.0 + 2.2 * flash) \
        * live.astype(np.float64)
    rcol = np.where(S['rlay'][:, None] > 0.5,
                    np.array(RAIN)[None, :], np.array(RAINFAR)[None, :])
    rz = np.choose(S['rlay'], [-0.10, 0.10, 0.34])
    rw = np.choose(S['rlay'], [0.0016, 0.0022, 0.0032])
    blocks.append((np.stack([rx0, ry0, rx1, ry1, rcol[:, 0], rcol[:, 1],
                             rcol[:, 2], ra, rz, np.ones(NRAIN), rw], axis=1),
                   False))

    # --- splashes, on the actual street line ------------------------------------
    su = np.mod(t * S['srate'] * (0.45 + 0.95 * rain) + S['sph'], 1.0)
    sage = np.clip(su / 0.30, 0.0, 1.0)
    sact = (su < 0.30).astype(np.float64) * (1.0 if rain > 0.04 else 0.0)
    sr = 0.012 + 0.038 * sage
    sa = ((1.0 - sage) ** 1.7) * sact * ink * (0.15 + 1.0 * rain) * 0.95
    zs = np.full(NSPL, 0.05)
    one = np.ones(NSPL)
    ww = np.full(NSPL, 0.0024)
    for ox, oy, am in ((-1.0, 0.85, 1.0), (0.9, 0.75, 1.0)):
        blocks.append((np.stack([S['sx'], S['sy'], S['sx'] + ox * sr,
                                 S['sy'] + oy * sr,
                                 one * RAIN[0], one * RAIN[1], one * RAIN[2],
                                 sa * am, zs, one, ww], axis=1), False))

    # --- the city, static; the windows are the quietest reactive thing here -----
    st = S['static']
    n = st['n']
    flick = np.where(st['kind'] > 0.5,
                     0.72 + 0.20 * np.sin(st['fph'] + t * 0.55) + 0.30 * high,
                     1.0)
    sa2 = st['a'] * ink * flick * (1.0 + 1.6 * flash * (st['kind'] < 0.5))
    blocks.append((np.stack([st['x0'], st['y0'], st['x1'], st['y1'],
                             st['r'], st['g'], st['b'], sa2, st['z'],
                             np.zeros(n), st['w']], axis=1), False))


    # --- the wet street ---------------------------------------------------------
    # Mirror everything that stands on the ground. The shimmer is a horizontal
    # banding on the mirrored y, not a displacement: on a street the water is a
    # film, not a body, so what breaks the reflection is the surface rippling, and
    # a flat shape should smear along its own length rather than wander sideways.
    if reflpar > 0.01:
        refl = []
        for (arr, dorefl) in blocks:
            if not dorefl or not len(arr):
                continue
            above = np.maximum(arr[:, 1], arr[:, 3]) > GROUNDY + 0.004
            k = np.nonzero(above)[0]
            if not len(k):
                continue
            m = arr[k].copy()
            m[:, 1] = 2.0 * GROUNDY - arr[k, 1]
            m[:, 3] = 2.0 * GROUNDY - arr[k, 3]
            ymid = (m[:, 1] + m[:, 3]) * 0.5
            dep = np.clip(GROUNDY - ymid, 0.0, 0.8)
            wob = 0.009 * (0.5 + 1.1 * rain) * np.sin(ymid * 62.0 - t * 3.1)
            m[:, 0] += wob
            m[:, 2] += wob
            shim = 0.36 + 0.64 * (0.5 + 0.5 * np.sin(ymid * 118.0 + t * 2.4))
            m[:, 7] = m[:, 7] * 0.34 * reflpar * shim * np.exp(-dep * 2.2)
            m[:, 4] *= 0.86
            m[:, 5] *= 0.72
            m[:, 6] = np.minimum(1.4, m[:, 6] * 1.18)
            m[:, 8] = -0.18
            m[:, 9] = 1.0
            refl.append(m)
        for m in refl:
            blocks.append((m, False))

    parts = [b for (b, _) in blocks if len(b)]
    A = np.concatenate(parts, axis=0) if parts else np.zeros((0, 11))

    x0, y0, x1, y1 = A[:, 0], A[:, 1], A[:, 2], A[:, 3]
    dx, dy = x1 - x0, y1 - y0
    ln = np.hypot(dx, dy)
    al = A[:, 7]
    wd = A[:, 10]
    keep = ((np.minimum(x0, x1) - wd < CULLX) & (np.maximum(x0, x1) + wd > -CULLX)
            & (np.minimum(y0, y1) - wd < CULLY)
            & (np.maximum(y0, y1) + wd > -CULLY)
            & (ln > MINLEN) & (al > 0.005) & (wd > 1e-5))
    idx = np.nonzero(keep)[0]
    # Emission order is priority: the man, then the drone, then whoever is walking
    # past, then the weather. If the pool ever ran dry it would be the far drizzle
    # that thinned, never him.
    if len(idx) > MAXSEG:
        idx = idx[:MAXSEG]
    # Two different orderings, and they are both needed. Truncation uses EMISSION
    # order, so a full pool drops far drizzle and never the man. Drawing uses
    # DEPTH order, because one instanced geometry is one object to the sorter and
    # nothing else will put the background behind the foreground.
    idx = idx[np.argsort(A[idx, 8], kind='stable')]
    n = len(idx)

    out = np.zeros((11, MAXSEG), dtype=np.float64)
    out[6] = 1.0
    if n:
        out[0, :n] = (x0[idx] + x1[idx]) * 0.5
        out[1, :n] = (y0[idx] + y1[idx]) * 0.5
        out[2, :n] = A[idx, 8]
        out[3, :n] = np.degrees(np.arctan2(-dx[idx], dy[idx]))
        # sx is the WIDTH of the quad and sy its LENGTH. That one extra channel is
        # the whole difference between a wireframe and a flat cel.
        out[4, :n] = np.maximum(wd[idx], 1e-5)
        out[5, :n] = np.maximum(ln[idx], 1e-5)
        out[7, :n] = np.clip(A[idx, 4], 0.0, 4.0)
        out[8, :n] = np.clip(A[idx, 5], 0.0, 4.0)
        out[9, :n] = np.clip(A[idx, 6], 0.0, 4.0)
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
    lf = math.exp(-max(0.0, t - S['labelt']) / 3.2)

    try:
        par.Chapter.val = float(cp)
        par.Segs.val = float(n)
        par.Rainnow.val = min(1.0, max(0.0, rain))
        par.Windnow.val = wind
        par.Walkers.val = float(len(S['people']))
        par.Labelfade.val = lf
        txt = CHECKPOINTS[cp][1].strip()
        if par.Scaletxt.eval() != txt:
            par.Scaletxt.val = txt
    except Exception:
        pass

    S['census'] = ('f %.3f | rain %.2f wind %.2f thun %.2f | people %d '
                   '| quads %d/%d | bolts %d | static %d'
                   % (f, rain, wind, thun, len(S['people']), n, MAXSEG,
                      len(S['bolts']), st['n']))
    return
'''
eng_src = C(textDAT, 'engine_src', 1780, 980)


def _g3(c):
    return 'vec3(%.4f, %.4f, %.4f)' % c


eng_src.text = hdr(
    CHECKPOINTS=CHECKPOINTS, MAXSEG=MAXSEG, GROUNDY=GROUNDY, MUSX=MUSX,
    MSCALE=MSCALE, SEED0=20260918,
    CH=('tx', 'ty', 'tz', 'rz', 'sx', 'sy', 'sz', 'r', 'g', 'b', 'a'),
    SKYBASE=GROUNDY + 0.150,
    LWCHAR=LWCHAR, LWBG=LWBG,
    RAIN=PAL['RAIN'], RAINFAR=PAL['RAINFAR'], ROAD=PAL['ROAD'],
    KERB=PAL['KERB'], FOREDK=PAL['FOREDK'], WINDOW=PAL['WINDOW'],
    BLDGFAR=PAL['BLDGFAR'], BLDGDK=PAL['BLDGDK'], BLDGLT=PAL['BLDGLT'],
    PERSONDK=PAL['PERSONDK'], PERSONLT=PAL['PERSONLT'],
    PERSONED=PAL['PERSONED'],
    MUSDK=PAL['MUSDK'], MUSLT=PAL['MUSLT'], MUSED=PAL['MUSED'],
    HARMDK=PAL['HARMDK'], HARMLT=PAL['HARMLT'],
    LAMP=PAL['LAMP'], LAMPCORE=PAL['LAMPCORE'],
    PURPLE=PAL['PURPLE'], FLASH=PAL['FLASH'],
    # a DRIZZLE. 150 near streaks, not thousands: the volume of the rain is in
    # the shader, and these are only the ones that must fall in front of people.
    NRAIN=150, NSPL=44, NBAND=6, RINGLIFE=1.6,
    # gy, scale, alpha — further away is higher on screen, smaller, and dimmer
    LANES=((GROUNDY + 0.082, 0.265, 0.62), (GROUNDY + 0.030, 0.360, 0.86),
           (GROUNDY - 0.074, 0.505, 1.00)),
    BOLTLIFE=0.24, STOPDWELL=7.5, LISTEN0=0.79, LISTEN1=0.90,
    # THE WEATHER IS AN ARC, NOT A LEVEL. Three dry chapters with a rising wind,
    # the first drops at chapter 4, and the sky does not open until chapter 6 —
    # thunder is exactly zero before then, so it cannot leak early. Endpoints
    # match so the wrap has no seam.
    ARC_F=(0.00, 0.135, 0.270, 0.400, 0.470, 0.530, 0.660, 0.800, 0.910, 1.00),
    ARC_RAIN=(0.00, 0.00, 0.020, 0.105, 0.280, 0.420, 0.620, 0.480, 0.190, 0.00),
    ARC_CROWD=(0.55, 0.95, 0.850, 0.700, 0.600, 0.480, 0.400, 0.330, 0.470, 0.55),
    ARC_THUN=(0.00, 0.00, 0.000, 0.000, 0.000, 0.050, 1.000, 0.420, 0.100, 0.00),
    ARC_WIND=(0.18, 0.26, 0.720, 0.620, 0.580, 0.620, 0.900, 0.540, 0.300, 0.18),
    LINEW=1.0, CULLX=1.34, CULLY=0.74, MINLEN=0.0012,
) + ENGINE_BODY

engine = C(scriptCHOP, 'engine', 1940, 980)
engine.par.callbacks = eng_src.path
W(director, engine, 0)


# ---------------------------------------------------------------------------
# GEOMETRY AND RENDER — six TOPs, none of them a pass-through
# ---------------------------------------------------------------------------
SHAPE_BODY = '''# ONE UNIT QUAD, 1x1, centred, and it is the entire drawing system.
# sx scales its width and sy its length, so the same instance is a 3 px outline, a
# limb, or a slab of flat colour depending only on two numbers. Replacing the unit
# LINE with a unit QUAD is what let this scene go from wireframe to blocked-in flat
# colour without a second render pass, a second material, or a triangulator.


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
unit_line = C(scriptSOP, 'unit_quad', 1440, 200)
unit_line.par.callbacks = shape_src.path

mat_line = C(constantMAT, 'mat_flat', 1600, 200)
soft(mat_line, blending=True, depthtest=False, depthwriting=False, alpha=1.0)
SRCB = menu_pick(mat_line.par.srcblend, 'sa', 'srcalpha')
DSTB = menu_pick(mat_line.par.destblend, 'omsa', 'oneminussrcalpha')

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
soft(render_lines, transparency='sortedblending')
# NEVER ASSIGN A MENU VALUE YOU HAVE NOT SEEN IN THE LIST. `bayou` shipped with
# antialias='msaa4x', which is not a valid name, so it silently took entry zero and
# rendered with no multisampling for its entire life.
AA = menu_pick(render_lines.par.antialias, 'aa4', 'msaa4x', '4xmsaa', 'aa2')

glow_blur = C(blurTOP, 'glow_blur', 2100, 300, size=9.0)
res(glow_blur, OUTW // 4, OUTH // 4)
glow_blur.par.size.expr = "9.0 + 16.0 * %s + 22.0 * %s" % (D('dropenv'), D('flash'))
W(render_lines, glow_blur)

# --- ONE SHADER: sky, rain volume, wet street, lightning, composite, grade -------
post = C(glslTOP, 'post', 2260, 200)
res(post)
post_pix = C(textDAT, 'post_pixel', 2260, 120)
post_pix.text = ('''// Everything that is not a line lives here, and so does everything that would
// otherwise be its own pass-through TOP. This one shader is the sky gradient, the
// three sheets of rain, the wet street and its haze, the lamp's pool on the road,
// the lightning flash, the composite of the rendered lines, the glow add, the
// grade and the vignette.
//
// It is written this way because this scene is one of sixteen on a switch. Fifteen
// TOPs at 1280x720 is 88 MB of VRAM whether or not anyone is looking; six is 29.
// The rain is here rather than in the instance pool for the same reason: a sheet
// of rain drawn as geometry costs thousands of instances and still looks thin,
// and drawn as a shader it costs one texture fetch and has no upper limit.
//
// sTD2DInputs is declared by TD itself - redeclaring it is a compile error.
uniform vec4 uA;   // x flash, y afterglow, z rain, w time
uniform vec4 uB;   // x bass, y energy, z vignette, w brightness
uniform vec4 uC;   // x lamp uv.x, y lamp uv.y, z lamp amount, w wind
uniform vec4 uD;   // x glow amount, y horizon uv.y, z kickenv, w label fade
out vec4 fragColor;

const vec3 SKYTOP = ''' + _g3(PAL['SKYTOP']) + ''';
const vec3 SKYLOW = ''' + _g3(PAL['SKYLOW']) + ''';
const vec3 CRAIN  = ''' + _g3(PAL['RAIN']) + ''';
const vec3 CSTREET= ''' + _g3(PAL['ROAD']) + ''';
const vec3 CRED   = ''' + _g3(PAL['LAMP']) + ''';
const vec3 CFLASH = ''' + _g3(PAL['FLASH']) + ''';

float hash21(vec2 p) {
    p = fract(p * vec2(233.34, 851.73));
    p += dot(p, p + 23.45);
    return fract(p.x * p.y);
}

// One sheet of rain. Cells are tall and narrow; each holds at most one streak, and
// the streak's own hash decides whether it exists, so density is a threshold and
// costs nothing.
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
    float hz = uD.y;
    float t = uA.w;
    float rain = uA.z;
    float flash = uA.x;
    float after = uA.y;

    // --- the air -------------------------------------------------------------
    float above = clamp((uv.y - hz) / max(1.0 - hz, 0.001), 0.0, 1.0);
    vec3 col = mix(SKYLOW, SKYTOP, pow(above, 0.72));
    // the purple the lightning leaves in the air takes two seconds to go
    col += vec3(0.115, 0.045, 0.165) * after * (0.35 + 0.75 * (1.0 - above));
    col = mix(col, CFLASH * 0.58, flash * 0.46);

    // --- the street: a film, so it mirrors the air and shimmers --------------
    float below = clamp((hz - uv.y) / max(hz, 0.001), 0.0, 1.0);
    if (uv.y < hz) {
        float my = hz + (hz - uv.y) * 0.85;
        float ab2 = clamp((my - hz) / max(1.0 - hz, 0.001), 0.0, 1.0);
        vec3 mirror = mix(SKYLOW, SKYTOP, pow(ab2, 0.72));
        float shim = 0.72 + 0.28 * sin(uv.y * 210.0 - t * 2.2 + sin(uv.x * 9.0) * 2.0);
        col = mix(CSTREET * 0.34, mirror * shim, exp(-below * 2.1) * 0.75);
        col += vec3(0.040, 0.022, 0.068) * after * exp(-below * 1.6);
        col = mix(col, CFLASH * 0.40, flash * 0.36);
    }

    // --- his lamp, pooled on the wet road ------------------------------------
    vec2 lp = vec2(uv.x - uC.x, (uv.y - uC.y) * 1.30);
    float lr = length(lp * vec2(1.0, 1.0));
    float lamp = exp(-lr * lr * 62.0) * (0.85 + 0.35 * uD.z);
    vec2 sp = vec2(uv.x - uC.x, (uv.y - (2.0 * hz - uC.y)) * 2.6);
    float smear = exp(-dot(sp, sp) * 16.0) * step(uv.y, hz);
    col += CRED * uC.z * (lamp * 0.30 + smear * 0.20);

    // --- three sheets, far to near -------------------------------------------
    float w = uC.w;
    float r = 0.0;
    r += sheet(uv, 26.0, 0.55, w * 0.22, 30.0, t) * 0.17;
    r += sheet(uv, 15.0, 0.95, w * 0.26, 22.0, t) * 0.22;
    r += sheet(uv,  8.5, 1.60, w * 0.30, 15.0, t) * 0.26;
    r *= 0.06 + 0.94 * rain;
    // the strike is what makes the whole volume of it visible at once
    r *= 1.0 + 3.4 * flash;
    col += CRAIN * r * (0.30 + 0.06 * uB.y);
    // haze, heaviest just above the road
    col += mix(CRAIN, SKYLOW, 0.55) * rain * 0.085
           * exp(-abs(uv.y - hz) * 3.2) * (0.85 + 0.15 * uB.x);

    // --- the lines, and their glow -------------------------------------------
    vec4 li = texture(sTD2DInputs[0], uv);
    vec4 gl = texture(sTD2DInputs[1], uv);
    col = col * (1.0 - clamp(li.a, 0.0, 1.0)) + li.rgb;
    col += gl.rgb * uD.x;
    vec4 lb = texture(sTD2DInputs[2], uv);
    col = mix(col, lb.rgb, clamp(lb.a, 0.0, 1.0) * uD.w);

    // --- grade ---------------------------------------------------------------
    col *= uB.w;
    col += (hash21(uv * vec2(1920.0, 1080.0) + fract(t)) - 0.5) * 0.010;
    vec2 d = (uv - 0.5) * vec2(1.777, 1.0);
    col *= 1.0 - uB.z * 0.80 * dot(d, d);
    fragColor = TDOutputSwizzle(vec4(max(col, vec3(0.0)), 1.0));
}
''')
post.par.pixeldat = post_pix.path
W(render_lines, post, 0)
W(glow_blur, post, 1)
post.par.vec = 4
post.par.vec0name = 'uA'
post.par.vec0valuex.expr = D('flash')
post.par.vec0valuey.expr = D('after')
post.par.vec0valuez.expr = 'parent().par.Rainnow'
post.par.vec0valuew.expr = D('rawtime')
post.par.vec1name = 'uB'
post.par.vec1valuex.expr = D('bass')
post.par.vec1valuey.expr = D('energy')
post.par.vec1valuez.expr = 'parent().par.Vignette'
post.par.vec1valuew.expr = 'parent().par.Brightness'
post.par.vec2name = 'uC'
# his lamp, in uv. world x/ORTHOW + 0.5, world y/ORTHOH + 0.5
post.par.vec2valuex = MUSX / ORTHOW + 0.80 * MSCALE / ORTHOW + 0.5
post.par.vec2valuey = (GROUNDY + 0.14 * MSCALE) / ORTHOH + 0.5
post.par.vec2valuez.expr = 'parent().par.Lamp'
post.par.vec2valuew.expr = 'parent().par.Wind'
post.par.vec3name = 'uD'
post.par.vec3valuex.expr = ("0.55 * parent().par.Glow * (0.45 + 0.35 * %s "
                            "+ 0.60 * %s)" % (D('energy'), D('dropenv')))
post.par.vec3valuey = GROUNDY / ORTHOH + 0.5
post.par.vec3valuez.expr = D('kickenv')
post.par.vec3valuew.expr = ("parent().par.Label * (0.16 + 0.84 * "
                            "parent().par.Labelfade)")

label = C(textTOP, 'label', 2260, 420)
res(label, OUTW, OUTH, 'rgba8fixed')
soft(label, alignx='left', aligny='bottom', fontsizex=22, font='Courier New',
     bgalpha=0.0, fontcolorr=0.92, fontcolorg=0.80, fontcolorb=1.0,
     fontcolora=1.0, wordwrap=False, trackingx=0.15,
     positionx=0.048, positiony=0.070, positionunit='fraction')
label.par.text.expr = 'parent().par.Scaletxt.eval()'

W(label, post, 2)

final_out = C(nullTOP, 'final_out', 2580, 200)
W(post, final_out)
out1 = C(outTOP, 'out1', 2740, 200)
W(final_out, out1)

pout = proj.create(outTOP, SCENE + '_out')
pout.nodeX, pout.nodeY = 400, -1500
s.outputConnectors[0].connect(pout.inputConnectors[0])


# ---------------------------------------------------------------------------
# PADS AND KEYS
# ---------------------------------------------------------------------------
PEXEC_BODY = '''# A chapter is a SEEK: show = musical clock - Timeoffset, so jumping is one
# parameter write and the street carries on raining from where it lands.
#
# The four performance pads do not seek. They push a verb into the director's queue,
# so they work at any point and leave the playhead alone.


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
    if n == 'Bolt':
        _push(comp, 'bolt')
    elif n == 'Passer':
        _push(comp, 'passer')
    elif n == 'Stopper':
        _push(comp, 'stopper')
    elif n == 'Reseed':
        _push(comp, 'reseed')
    elif n == 'Restart':
        _seek(comp, 0.0)
    elif n == 'Nextcp':
        i = int(round(float(comp.par.Chapter.eval())))
        _seek(comp, CHECKPOINTS[(i + 1) % len(CHECKPOINTS)][2] * slen)
    elif n == 'Prevcp':
        i = int(round(float(comp.par.Chapter.eval())))
        _seek(comp, CHECKPOINTS[(i - 1) % len(CHECKPOINTS)][2] * slen)
    elif n.startswith('Go'):
        want = n[2:].lower()
        if want in names:
            _seek(comp, CHECKPOINTS[names.index(want)][2] * slen)
    return
'''

pexec = C(parameterexecuteDAT, 'checkpoint_exec', 2100, 1000)
pexec.text = hdr(CHECKPOINTS=CHECKPOINTS) + PEXEC_BODY
pexec.par.op = s.path
soft(pexec, pars='Bolt Passer Stopper Reseed Restart Nextcp Prevcp '
     + ' '.join('Go' + cp[0] for cp in CHECKPOINTS),
     valuechange=False, onpulse=True)

KEY_BODY = '''# 1-8 walk the story to a chapter; 0 starts it again.
#   t  THUNDER   — open the sky. The best single pad in the scene.
#   p  PASSER-BY — send someone across now.
#   s  STOPS     — the next person to reach him stops and listens, then gives.
#   n  RESEED    — a new street and a new crowd.


def onKey(dat, keyInfo):
    if not keyInfo.state:
        return
    comp = dat.parent()
    k = keyInfo.key
    if k in '12345678':
        i = int(k) - 1
        if i < len(CHECKPOINTS):
            getattr(comp.par, 'Go' + CHECKPOINTS[i][0]).pulse()
    elif k == '0':
        comp.par.Restart.pulse()
    elif k == 't':
        comp.par.Bolt.pulse()
    elif k == 'p':
        comp.par.Passer.pulse()
    elif k == 's':
        comp.par.Stopper.pulse()
    elif k == 'n':
        comp.par.Reseed.pulse()
    return


def onShortcut(dat, shortcutName, time):
    return
'''

keyin = C(keyboardinDAT, 'key_pad', 1780, 700)
keyin.par.keys = '1 2 3 4 5 6 7 8 0 t p s n'
kcb = keyin.par.callbacks.eval()
if kcb is None:
    kcb = C(textDAT, 'key_pad_callbacks', 1780, 620)
    keyin.par.callbacks = kcb.path
kcb.nodeX, kcb.nodeY = 1780, 620
kcb.text = hdr(CHECKPOINTS=CHECKPOINTS) + KEY_BODY

# NO executeDAT KEEP-ALIVE, and that is deliberate. TD is pull-based: unselected on
# a Switch TOP this scene costs one Audio Device In tick per frame and nothing else.
# A framestart callback that force-cooks the engine would make sixteen of these cost
# sixteen engines per frame whether or not anyone can see them.

s.par.display = True
s.par.opviewer = final_out.path
s.store('pending', [])
s.store('strike', 0.0)

timer.par.initialize.pulse()
timer.par.start.pulse()
director.cook(force=True)
engine.cook(force=True)

for _got, _want, _what in (
        (cam.par.projection.eval(), 'ortho', 'camera projection'),
        (g_lines.par.instancecolormode.eval(), 'replace', 'instance colour mode'),
        (post.par.pixeldat.eval(), post_pix, 'post shader source')):
    if _got != _want:
        print('  [CHECK FAILED] %s is %r, expected %r' % (_what, _got, _want))
if post.warnings():
    print('  [SHADER] %s' % post.warnings())

print('built %s' % s.path)
print('  antialias -> %r | blend %r over %r' % (AA, SRCB, DSTB))
print('  %s' % eng_src.module._S['S']['census'])
print('  chapters: dry 1-3 | rain from 4 | lightning from 6')
print('  keys: 1-8 chapters | 0 restart | t thunder | p passer-by | s stops | n reseed')
