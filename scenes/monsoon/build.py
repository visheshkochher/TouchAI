# Monsoon — it is raining hard, someone is playing a harmonium in it, and everyone
# walks past.
#
# A fixed camera on one street corner. The rain does not let up and he does not stop
# playing; what changes is how many people are crossing, how hard it is coming down,
# and how often the sky goes white. Once in a while somebody stops. That is the whole
# story and it is told in colour: THE WORLD IS BLUE, THE AIR IS PURPLE, AND THE ONLY
# RED IN THE FRAME IS HIM. Every figure that passes close enough picks up a red edge
# on the side facing him and loses it again on the way out.
#
# BUILT FOR A SWITCH. This is one tox among sixteen, so the cost of NOT being on
# screen mattered more than the cost of being on it:
#   - fixed camera, so there is no world array — the scene is a few thousand line
#     segments per frame and nothing is stored between them
#   - six TOPs, none of them pass-through. The sky, the rain volume, the wet street,
#     the lightning flash, the glow add, the grade and the vignette are ONE shader.
#   - no executeDAT keep-alive. TD is pull-based; unselected, this costs one Audio
#     Device In tick per frame and nothing else.
# Measured against `bayou` (15 TOPs, 87.9 MB) at the bottom of the README.
#
# THE RAIN IS IN TWO PLACES ON PURPOSE. The volume of it — the sheets, the depth, the
# haze — is procedural in the shader, where a million drops cost the same as one. Only
# the near streaks that need to pass IN FRONT of people, and the splashes that have to
# land on the actual street line, are geometry. Drawing all of it as geometry is how
# you spend eight thousand instances on drizzle.
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
MAXSEG = 2400            # instance pool; fixed, never resized. Measured peak
                         # over a full dry-run pass is 1060, and Crowd tops out at 2x.
GROUNDY = -0.260         # the wet street, in world y
MUSX = -0.245            # where he sits
MSCALE = 0.360

# Red, blue, purple, and nothing else. Values are chosen for MEDIUM brightness: the
# sky alone sits near 0.13 luminance, where `bayou` sat near 0.02. A scene that is
# mostly black reads as cheap on a big screen and disappears next to fifteen others.
PAL = dict(
    SKYTOP=(0.055, 0.062, 0.158),
    SKYLOW=(0.190, 0.092, 0.268),
    RAIN=(0.600, 0.700, 1.000),
    RAINFAR=(0.360, 0.430, 0.780),
    STREET=(0.400, 0.360, 0.640),
    SKYLINE=(0.230, 0.200, 0.420),
    WINDOW=(0.780, 0.480, 0.980),
    PERSON=(0.660, 0.790, 1.000),
    RED=(1.000, 0.270, 0.320),
    RED2=(1.000, 0.600, 0.420),
    PURPLE=(0.760, 0.400, 1.000),
    FLASH=(0.780, 0.730, 1.000),
)

# Eight chapters. None of them is an empty stage: the switch can land on this scene
# at any moment of a set, so every chapter is already raining and he is already
# playing. The arc moves how hard, how many, and how often the sky opens.
CHECKPOINTS = [
    ('drizzle', ' 1 - First Drops',    0.000),
    ('settle',  ' 2 - It Sets In',     0.120),
    ('crowd',   ' 3 - The Crowd',      0.260),
    ('storm',   ' 4 - Thunder',        0.420),
    ('break',   ' 5 - The Downpour',   0.560),
    ('listen',  ' 6 - Someone Stops',  0.680),
    ('alone',   ' 7 - Alone, Playing', 0.800),
    ('easing',  ' 8 - It Eases',       0.920),
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
    ('Wind',       'Wind',                1.0, -2.0, 3.0),
    ('Crowd',      'Crowd',               1.0, 0.0, 2.0),
    ('Thunder',    'Thunder',             1.0, 0.0, 2.0),
    ('Drone',      'Harmonium Drone',     1.0, 0.0, 2.0),
    ('Lamp',       'His Lamp',            1.0, 0.0, 2.0),
    ('Reflect',    'Wet Street',          1.0, 0.0, 2.0),
    ('Linewidth',  'Line Width (px)',     1.45, 0.6, 5.0),
    ('Ink',        'Line Brightness',     1.15, 0.0, 3.0),
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
                           ('Walkers', 'People On Screen', 0.0, 16.0),
                           ('Segs', 'Lines Drawn', 0.0, float(MAXSEG)),
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
# THE ENGINE — the street, the rain that is geometry, and the man playing
# ---------------------------------------------------------------------------
ENGINE_BODY = r'''# One fixed camera on one corner, so there is no world to store and no camera to
# track. Everything here is emitted per frame as line segments in world coordinates
# and handed to a single instanced unit segment.
#
# WHAT IS GEOMETRY AND WHAT IS NOT. The volume of the rain — the sheets, the depth,
# the haze on the street — is in the shader, where a million drops cost what one
# costs. Geometry is only what has to interact: the near streaks that pass IN FRONT
# of people, and the splashes that must land on the actual street line. Drawing the
# whole downpour as instances is how you spend an eight-thousand instance pool on
# drizzle and still have it look thin.
#
# THE COLOUR IS THE STORY. Everything is blue; the air is purple; he is the only red
# thing in the frame. Anyone who passes close enough picks up his lamp on the side
# facing him, and loses it again on the way out. That is one line of code and it is
# the entire point of the piece.
import math
import random
import numpy as np

_S = {'S': None}


def _ss(a, b, x):
    t = (x - a) / (b - a if b != a else 1e-9)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return t * t * (3.0 - 2.0 * t)


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
    k = 0.0 if k < 0.0 else (1.0 if k > 1.0 else k)
    return (c1[0] + (c2[0] - c1[0]) * k, c1[1] + (c2[1] - c1[1]) * k,
            c1[2] + (c2[2] - c1[2]) * k)


def _ik(out, hx, hy, fx, fy, l1, l2, sgn, col, a, z=0.0):
    dx, dy = fx - hx, fy - hy
    raw = max(math.hypot(dx, dy), 1e-6)
    ux, uy = dx / raw, dy / raw
    d = min(max(raw, 0.010), l1 + l2 - 0.002)
    fx, fy = hx + ux * d, hy + uy * d
    aa = (l1 * l1 - l2 * l2 + d * d) / (2.0 * d)
    hh = math.sqrt(max(0.0, l1 * l1 - aa * aa))
    kx = hx + ux * aa - uy * hh * sgn
    ky = hy + uy * aa + ux * hh * sgn
    _L(out, hx, hy, kx, ky, col, a, z)
    _L(out, kx, ky, fx, fy, col, a, z)
    return fx, fy


def _rh(i):
    x = math.sin(i * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


# --- the city behind it all ------------------------------------------------------
# Static, generated once per seed into flat numpy arrays. About 250 segments and
# 25 KB, which is the whole argument for algorithmic scenery: this backdrop costs
# less than one four-hundredth of a single 1280x720 texture.
def _gen_static(rs):
    groups = []                      # (segs, colour, alpha, z, storm_lift)
    sky, lit = [], []
    x = -1.30
    while x < 1.32:
        w = rs.uniform(0.11, 0.29)
        h = rs.uniform(0.15, 0.44)
        b, top = SKYBASE, SKYBASE + h
        sky.append((x, b, x, top))
        sky.append((x, top, x + w, top))
        sky.append((x + w, top, x + w, b))
        if rs.random() < 0.35:                       # a water tank or an aerial
            ax = x + w * rs.uniform(0.25, 0.75)
            sky.append((ax, top, ax, top + rs.uniform(0.03, 0.09)))
        cols = max(1, int(w / 0.058))
        rows = max(1, int(h / 0.068))
        for ci in range(cols):
            for ri in range(rows):
                if rs.random() > 0.26:
                    continue
                wx = x + 0.020 + ci * 0.058
                wy = b + 0.030 + ri * 0.068
                ww, wh = 0.021, 0.031
                if wx + ww > x + w - 0.012 or wy + wh > top - 0.014:
                    continue
                lit.append((wx, wy, wx + ww, wy))
                lit.append((wx + ww, wy, wx + ww, wy + wh))
                lit.append((wx + ww, wy + wh, wx, wy + wh))
                lit.append((wx, wy + wh, wx, wy))
        x += w + rs.uniform(0.005, 0.045)
    groups.append((sky, SKYLINE, 0.62, -0.50, 2.6))
    groups.append((lit, WINDOW, 0.46, -0.49, 1.2))

    road, kerb = [], []
    for gy in (GROUNDY, GROUNDY + 0.030, GROUNDY + 0.085):
        road.append((-1.30, gy, 1.30, gy))
    road.append((-1.30, GROUNDY + 0.140, 1.30, GROUNDY + 0.140))
    for i in range(18):
        rx = -1.26 + i * 0.148
        kerb.append((rx, GROUNDY + 0.085, rx, GROUNDY + 0.148))
    for i in range(26):
        rx = -1.28 + i * 0.100
        kerb.append((rx, GROUNDY, rx - 0.030, GROUNDY - 0.026))
    groups.append((road, STREET, 0.78, -0.20, 1.5))
    groups.append((kerb, STREET, 0.42, -0.21, 1.5))

    posts = []
    for px in (-0.86, 0.94):
        posts.append((px, GROUNDY + 0.030, px, GROUNDY + 0.560))
        posts.append((px, GROUNDY + 0.560, px + 0.085, GROUNDY + 0.585))
        for i in range(5):
            a = math.radians(200.0 + i * 34.0)
            posts.append((px + 0.085, GROUNDY + 0.585,
                          px + 0.085 + 0.046 * math.cos(a),
                          GROUNDY + 0.585 + 0.046 * math.sin(a)))
    groups.append((posts, SKYLINE, 0.70, -0.30, 1.8))

    X0, Y0, X1, Y1, R, G, B, A, Z, LF = ([] for _ in range(10))
    for segs, col, al, z, lift in groups:
        for (a0, b0, a1, b1) in segs:
            X0.append(a0); Y0.append(b0); X1.append(a1); Y1.append(b1)
            R.append(col[0]); G.append(col[1]); B.append(col[2])
            A.append(al); Z.append(z); LF.append(lift)
    f = lambda L: np.array(L, dtype=np.float64)
    return dict(x0=f(X0), y0=f(Y0), x1=f(X1), y1=f(Y1), r=f(R), g=f(G), b=f(B),
                a=f(A), z=f(Z), lift=f(LF), n=len(X0))


# --- the man, and what he is playing --------------------------------------------
# A harmonium is a box you pump with one hand and play with the other, sitting on
# the ground. The pump is the animation: it is the only thing in the frame moving
# in musical time rather than in weather time, which is what makes him read as a
# person doing something rather than as scenery that happens to be person-shaped.
def _musician(out, ox, oy, sc, pump, press, ink, lamp, kickenv, high, t, flash):
    def T(x, y):
        return (ox + x * sc, oy + y * sc)

    RED_ = RED
    RED2_ = RED2
    body = _mix(RED_, RED2_, 0.25 + 0.35 * kickenv)
    box = _mix(RED_, RED2_, 0.55)

    # --- the harmonium: a front face and a top face, drawn as one solid -----------
    fl_, fr_, fb_, ft_ = 0.10, 0.52, 0.02, 0.20
    dx_, dy_ = 0.072, 0.052
    _P(out, [T(fl_, fb_), T(fr_, fb_), T(fr_, ft_), T(fl_, ft_), T(fl_, fb_)],
       box, ink)
    _P(out, [T(fl_, ft_), T(fl_ + dx_, ft_ + dy_), T(fr_ + dx_, ft_ + dy_),
             T(fr_, ft_)], box, ink)
    _L(out, *(T(fr_ + dx_, ft_ + dy_) + T(fr_ + dx_, fb_ + dy_ * 0.35)), box,
       ink * 0.55)
    for k in (0.33, 0.66):
        _L(out, *(T(fl_ + (fr_ - fl_) * k, fb_) + T(fl_ + (fr_ - fl_) * k, ft_)),
           box, ink * 0.30)

    # the keyboard, on the front edge of the top face. One key is down at a time.
    NK = 11
    for i in range(NK):
        u = i / float(NK)
        kx = fl_ + 0.022 + u * (fr_ - fl_ - 0.044)
        dn = 0.011 if i == press else 0.0
        _P(out, [T(kx, ft_ - dn), T(kx + dx_ * 0.62, ft_ + dy_ * 0.62 - dn)],
           box, ink * (1.25 if i == press else 0.62))
        if i % 7 in (1, 3, 5):
            _P(out, [T(kx + 0.008, ft_ + dy_ * 0.20),
                     T(kx + 0.008 + dx_ * 0.34, ft_ + dy_ * 0.54)],
               box, ink * 0.40)

    # --- the bellows. Hinged at the back, and the pleats really compress ---------
    hx_, hy_ = fr_ + dx_ * 0.55, ft_ + dy_ * 0.72
    ang = 0.24 + 0.46 * pump
    tipx, tipy = hx_ + 0.155 * math.cos(ang), hy_ + 0.155 * math.sin(ang)
    _P(out, [T(hx_, hy_), T(tipx, tipy)], box, ink)
    _P(out, [T(tipx, tipy), T(tipx - 0.035, tipy - 0.070), T(hx_ - 0.020, hy_)],
       box, ink * 0.85)
    bx0, by0 = fr_ - 0.03, ft_ + dy_ * 0.34
    bx1e = fr_ + dx_ * 0.92
    for i in range(1, 5):
        u = i / 5.0
        ax_ = hx_ + (tipx - hx_) * u
        ay_ = hy_ + (tipy - hy_) * u
        bx_ = bx0 + (bx1e - bx0) * u
        bulge = 0.026 * (1.0 - 0.70 * pump) * math.sin(math.pi * u)
        _P(out, [T(ax_, ay_),
                 T((ax_ + bx_) * 0.5 + bulge, (ay_ + by0) * 0.5 - bulge * 0.4),
                 T(bx_, by0)], box, ink * 0.50)
    _P(out, [T(bx0, by0), T(bx1e, by0)], box, ink * 0.55)

    # --- the open case in front of him ------------------------------------------
    _P(out, [T(-0.46, 0.02), T(-0.46, 0.085), T(-0.21, 0.085), T(-0.21, 0.02),
             T(-0.46, 0.02)], box, ink * 0.70)
    _P(out, [T(-0.46, 0.085), T(-0.52, 0.155)], box, ink * 0.50)

    # --- the lamp: the one red source, and the reason anyone is lit at all -------
    lx_, ly_ = 0.80, 0.14
    la = ink * lamp * (0.85 + 0.35 * math.sin(t * 5.3) * 0.3 + 0.30 * kickenv)
    _NG(out, *(T(lx_, ly_)), 0.062 * sc, 6, 0.26, RED_, la)
    _NG(out, *(T(lx_, ly_)), 0.026 * sc, 4, 0.0, RED2_, la * 1.5)
    _L(out, *(T(lx_, ly_ + 0.062) + T(lx_, ly_ + 0.125)), RED_, la * 0.6)
    _P(out, [T(lx_ - 0.05, 0.02), T(lx_, ly_ - 0.062), T(lx_ + 0.05, 0.02)],
       RED_, la * 0.5)
    for i in range(8):
        a = i * math.pi / 4.0 + t * 0.25
        r0, r1 = 0.085, 0.085 + 0.055 * (0.5 + 0.5 * math.sin(t * 2.1 + i))
        _L(out, *(T(lx_ + r0 * math.cos(a), ly_ + r0 * math.sin(a))
                  + T(lx_ + r1 * math.cos(a), ly_ + r1 * math.sin(a))),
           RED2_, la * 0.40)

    # --- the player -------------------------------------------------------------
    rock = (pump - 0.5) * 0.055
    hipx, hipy = -0.10, 0.17
    shx, shy = 0.02 + rock, 0.51 - abs(rock) * 0.5
    _P(out, [T(-0.36, 0.02), T(0.11, 0.02), T(-0.10, 0.19), T(-0.36, 0.02)],
       body, ink)
    _P(out, [T(-0.22, 0.02), T(-0.11, 0.12)], body, ink * 0.55)
    _P(out, [T(hipx - 0.105, hipy), T(shx - 0.095, shy), T(shx + 0.095, shy),
             T(hipx + 0.105, hipy)], body, ink)
    for k in (0.35, 0.68):
        _L(out, *(T(hipx - 0.105 + (shx - 0.095 - hipx + 0.105) * k,
                    hipy + (shy - hipy) * k)
                  + T(hipx + 0.105 + (shx + 0.095 - hipx - 0.105) * k,
                      hipy + (shy - hipy) * k)), body, ink * 0.28)
    hdx, hdy = shx + 0.030, shy + 0.115
    _NG(out, *(T(hdx, hdy)), 0.088 * sc, 7, 0.30, body, ink, ry=0.098 * sc)
    _P(out, [T(hdx - 0.075, hdy + 0.045), T(hdx + 0.010, hdy + 0.100),
             T(hdx + 0.080, hdy + 0.030)], body, ink * 0.75)
    _L(out, *(T(shx, shy) + T(hdx - 0.020, hdy - 0.085)), body, ink * 0.6)

    # right hand on the keys, left hand over the top on the bellows
    kpx = fl_ + 0.022 + (press / float(NK)) * (fr_ - fl_ - 0.044) + dx_ * 0.45
    _ik(out, *(T(shx + 0.075, shy - 0.030) + T(kpx, ft_ + dy_ * 0.55)),
        0.20 * sc, 0.19 * sc, -1.0, body, ink)
    _ik(out, *(T(shx + 0.020, shy - 0.020) + T(tipx - 0.025, tipy - 0.030)),
        0.24 * sc, 0.25 * sc, -1.0, body, ink * 0.55)

    # rain landing on him: four sites, blinking on their own phases
    for i in range(4):
        u = (t * (1.6 + 0.7 * i) + _rh(i * 7 + 3)) % 1.0
        if u > 0.28:
            continue
        age = u / 0.28
        sx_ = hdx - 0.10 + 0.075 * i
        sy_ = hdy + 0.075 - 0.055 * (i % 2)
        rr = 0.020 + 0.055 * age
        aa = ink * (1.0 - age) * (0.55 + 0.9 * high)
        _L(out, *(T(sx_ - rr, sy_ + rr * 0.6) + T(sx_, sy_)), RAIN, aa)
        _L(out, *(T(sx_, sy_) + T(sx_ + rr, sy_ + rr * 0.6)), RAIN, aa)
    return T(0.36, ft_ + dy_), T(lx_, ly_)


def _knee(hx, hy, fx, fy, l1, l2, sgn):
    dx, dy = fx - hx, fy - hy
    raw = max(math.hypot(dx, dy), 1e-6)
    ux, uy = dx / raw, dy / raw
    d = min(max(raw, 0.010), l1 + l2 - 0.002)
    fx, fy = hx + ux * d, hy + uy * d
    aa = (l1 * l1 - l2 * l2 + d * d) / (2.0 * d)
    hh = math.sqrt(max(0.0, l1 * l1 - aa * aa))
    return (hx + ux * aa - uy * hh * sgn, hy + uy * aa + ux * hh * sgn, fx, fy)


# --- someone walking past --------------------------------------------------------
# Built once in local coordinates facing +x, then mirrored through T. Doing the
# mirror in the transform rather than in the pose is what keeps the knee bending
# forwards in both directions — solve the IK in world space with a mirrored frame
# and every figure walking left has its legs on backwards.
def _person(out, px, gy, sc, ph, umb, al, redk, facing, lean, ink, t, stopped):
    def T(lx, ly):
        return (px + facing * lx * sc, gy + ly * sc)

    col = _mix(PERSON, RED2, redk)
    a = al * ink
    hipy = 0.47
    for li, off in ((0, 0.0), (1, 0.5)):
        A, lift, duty = 0.155, 0.10, 0.60
        p = (ph + off) % 1.0
        if stopped:
            fx, fy = (0.085 if li else -0.070), 0.0
        elif p < duty:
            fx, fy = A - 2.0 * A * (p / duty), 0.0
        else:
            k = (p - duty) / (1.0 - duty)
            fx, fy = -A + 2.0 * A * k, lift * math.sin(math.pi * k)
        kx, ky, fx, fy = _knee(0.0, hipy, fx, fy, 0.26, 0.25, -1.0)
        la = a * (1.0 if li == 0 else 0.62)
        _P(out, [T(0.0, hipy), T(kx, ky), T(fx, fy)], col, la)
        _L(out, *(T(fx, fy) + T(fx + 0.070, fy)), col, la * 0.8)

    shy = 0.82
    _P(out, [T(-0.078, hipy), T(-0.088 + lean, shy), T(0.088 + lean, shy),
             T(0.078, hipy), T(-0.078, hipy)], col, a)
    for k in (0.36, 0.70):
        _L(out, *(T(-0.078 + (lean - 0.010) * k, hipy + (shy - hipy) * k)
                  + T(0.078 + (lean + 0.010) * k, hipy + (shy - hipy) * k)),
           col, a * 0.30)
    hdx, hdy = lean * 1.15 + 0.012, 0.925
    _NG(out, *(T(hdx, hdy)), 0.072 * sc, 6, 0.32, col, a, ry=0.082 * sc)
    _L(out, *(T(hdx - 0.030, hdy - 0.082) + T(hdx + 0.030, hdy - 0.082)),
       col, a * 0.6)

    # the near arm swings against the near leg; stopped, it hangs
    if stopped:
        hxk, hyk = 0.045, 0.50
    else:
        hxk = 0.115 * math.cos(2.0 * math.pi * (ph + 0.5))
        hyk = 0.52 + 0.035 * math.sin(2.0 * math.pi * (ph + 0.5))
    ekx, eky, hxk, hyk = _knee(0.070 + lean, shy - 0.030, hxk, hyk, 0.20, 0.19, 1.0)
    _P(out, [T(0.070 + lean, shy - 0.030), T(ekx, eky), T(hxk, hyk)], col, a * 0.9)

    if umb:
        ucx, ucy, R = lean * 1.30, 1.145, 0.315
        pts = []
        for i in range(7):
            aa = math.pi * (0.14 + 0.72 * i / 6.0)
            pts.append(T(ucx + R * math.cos(aa), ucy + R * 0.46 * math.sin(aa)))
        _P(out, pts, col, a)
        for i in (0, 2, 4, 6):
            aa = math.pi * (0.14 + 0.72 * i / 6.0)
            _L(out, *(T(ucx, ucy) + T(ucx + R * math.cos(aa),
                                      ucy + R * 0.46 * math.sin(aa))),
               col, a * 0.40)
        _L(out, *(T(ucx, ucy) + T(0.055 + lean, 0.79)), col, a * 0.7)
        for i in (0, 3, 6):                       # the run-off at the rim
            aa = math.pi * (0.14 + 0.72 * i / 6.0)
            rx_ = ucx + R * math.cos(aa)
            ry_ = ucy + R * 0.46 * math.sin(aa)
            dl = 0.05 + 0.07 * ((t * 2.3 + i * 0.37) % 1.0)
            _L(out, *(T(rx_, ry_) + T(rx_, ry_ - dl)), RAIN, a * 0.55)
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
    _P(out, pts, FLASH, a)
    # a second pass a hair to the side: the strike has to out-read the sky it just
    # turned white, and one instanced line at 1.45 px cannot
    _P(out, [(q[0] + 0.006, q[1]) for q in pts], FLASH, a * 0.75)
    _P(out, [(q[0] - 0.006, q[1]) for q in pts], FLASH, a * 0.75)
    for bi, si in ((0, 3), (1, 6)):
        bxx, byy = pts[si]
        d = 1.0 if _rh(seed * 5.0 + bi) > 0.5 else -1.0
        for j in range(4):
            nx = bxx + d * (0.045 + 0.030 * _rh(seed + bi * 9.0 + j))
            ny = byy - 0.055
            _L(out, bxx, byy, nx, ny, FLASH, a * 0.62)
            bxx, byy = nx, ny
    return


def _drone(out, cx, cy, amt, energy, t, ink):
    # A harmonium is a drone instrument: the sound does not pulse, it sits and
    # widens. Bands rise and spread and never repeat a beat, which is what keeps
    # them from reading as another audio meter.
    for i in range(NBAND):
        ri = (t * 0.195 + i / float(NBAND)) % 1.0
        a = ink * amt * ((1.0 - ri) ** 1.45) * (0.26 + 0.85 * energy)
        if a < 0.007:
            continue
        yy = cy + ri * 0.46
        hw = 0.105 + ri * 0.44
        pts = []
        for k in range(11):
            u = -1.0 + 2.0 * k / 10.0
            pts.append((cx + u * hw,
                        yy - 0.036 * u * u
                        + 0.014 * math.sin(u * 6.5 + t * 2.6 + i * 1.7)))
        _P(out, pts, PURPLE, a)
    return


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
        'rl': np.choose(lay, [0.048, 0.080, 0.132]) * u(0.80, 1.25, NRAIN),
        'ra': np.choose(lay, [0.26, 0.48, 0.86]),
        'rlay': lay,
        'sx': u(-1.32, 1.32, NSPL), 'sph': u(0.0, 1.0, NSPL),
        'srate': u(0.65, 2.10, NSPL),
        'sy': np.choose(np.arange(NSPL) % 3,
                        [GROUNDY, GROUNDY + 0.030, GROUNDY + 0.085]),
        'people': [], 'bolts': [], 'coins': [], 'seen': {},
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
    # speed scales with size or the far lane looks like it is running
    d = 1.0 if rs.random() < 0.5 else -1.0
    S['people'].append(dict(
        x=(-1.45 if d > 0 else 1.45), gy=gy, sc=sc, al=al, dir=d,
        spd=(0.155 + 0.155 * rs.random()) * sc / 0.38 * (0.85 + 0.45 * crowd),
        umb=rs.random() < 0.62, ph=rs.random(), lane=lane,
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

    # PRIME: the builder force-cooks the director, so frame one already has non-zero
    # counters. Read as deltas that is a thunderclap, a passer-by and a reseed all
    # at once, and the scene opens mid-event.
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
    ink = float(par.Ink.eval()) * (1.0 + 0.14 * kickenv + 0.22 * dropenv
                                  + 0.30 * flash)
    rainpar = float(par.Rain.eval())
    windpar = float(par.Wind.eval())
    crowdpar = float(par.Crowd.eval())
    thunpar = float(par.Thunder.eval())
    dronepar = float(par.Drone.eval())
    lamppar = float(par.Lamp.eval())
    reflpar = float(par.Reflect.eval())

    # --- the arc. Endpoints match, so the loop has no seam ----------------------
    rain = float(np.interp(f, ARC_F, ARC_RAIN)) * rainpar
    crowd = float(np.interp(f, ARC_F, ARC_CROWD))
    thun = float(np.interp(f, ARC_F, ARC_THUN)) * thunpar
    wind = float(np.interp(f, ARC_F, ARC_WIND)) * windpar
    rain = rain * (0.86 + 0.28 * energy)
    wind = wind * (0.88 + 0.30 * bass)

    nbolt = _delta(S, d, 'boltcnt')
    npass = _delta(S, d, 'passercnt')
    nstop = _delta(S, d, 'stoppercnt')
    ndrop = _delta(S, d, 'dropcnt')
    nkick = _delta(S, d, 'kickcnt')

    # --- thunder. The bass opens the sky; failing that, the storm does it alone --
    strike = nbolt > 0
    if ndrop and rs.random() < 0.30 + 0.62 * thun:
        strike = True
    gap = 2.6 + 16.0 * (1.0 - min(1.0, thun))
    if t - S['strike_t'] > gap and rs.random() < 0.02 * (0.3 + thun):
        strike = True
    if strike:
        S['strike_t'] = t
        S['bolts'].append([t, rs.uniform(-0.95, 0.95), rs.uniform(1.0, 900.0)])
        comp.store('strike', 1.0)
    del S['bolts'][:-3]

    # --- the crowd --------------------------------------------------------------
    target = int(round(1.1 + 6.4 * crowd * crowdpar))
    if npass:
        for _ in range(npass):
            _spawn(S, rs, crowd, t, forced=True)
    if (len(S['people']) < target
            and t - S['spawn_t'] > 0.22 + 1.5 * (1.0 - crowd)):
        _spawn(S, rs, crowd, t)

    # Someone stopping is the rarest thing that happens here, so it is never left
    # to chance alone: chapter 6 raises the odds, and the pad forces it outright.
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
                    p['al'], redk, face, lean, ink, t, p['stopped'])
        push(pseg, reflect=True)

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
            _NG(cseg, cx_, cy_, 0.013, 4, age * 6.0, RED2, ink * 1.1)
        else:
            rr = 0.02 + 0.16 * (age - 0.52) / 1.18
            _NG(cseg, casex, casey, rr, 7, age * 1.4, RED2,
                ink * 0.85 * max(0.0, 1.0 - (age - 0.52) / 1.18))
    push(cseg)

    bseg = []
    for b in S['bolts']:
        age = t - b[0]
        if 0.0 <= age <= BOLTLIFE:
            _bolt(bseg, b[1], age, ink, b[2])
    push(bseg)

    # --- the rain that is geometry ----------------------------------------------
    ph = np.mod(S['rph'] + t * S['rv'] * (0.72 + 0.55 * rain), 1.0)
    ry0 = 0.680 - ph * 1.360
    rx0 = S['rx'] + wind * (0.680 - ry0) * 0.300
    sl = wind * 0.44
    nrm = 1.0 / math.sqrt(1.0 + sl * sl)
    rx1 = rx0 + sl * nrm * S['rl']
    ry1 = ry0 - nrm * S['rl']
    live = (ry1 > GROUNDY - 0.010)
    ra = (S['ra'] * ink * (0.30 + 0.95 * rain) * (1.0 + 2.2 * flash)
          * live.astype(np.float64))
    rcol = np.where(S['rlay'][:, None] > 0.5,
                    np.array(RAIN)[None, :], np.array(RAINFAR)[None, :])
    rz = np.choose(S['rlay'], [-0.10, 0.10, 0.34])
    rain_arr = np.stack([rx0, ry0, rx1, ry1, rcol[:, 0], rcol[:, 1], rcol[:, 2],
                         ra, rz, np.ones(NRAIN)], axis=1)
    blocks.append((rain_arr, False))

    # --- splashes, on the actual street line ------------------------------------
    su = np.mod(t * S['srate'] * (0.45 + 0.95 * rain) + S['sph'], 1.0)
    sage = np.clip(su / 0.30, 0.0, 1.0)
    sact = (su < 0.30).astype(np.float64)
    sr = 0.014 + 0.046 * sage
    sa = ((1.0 - sage) ** 1.7) * sact * ink * (0.25 + 0.95 * rain) * 0.95
    zs = np.full(NSPL, 0.05)
    one = np.ones(NSPL)
    sp1 = np.stack([S['sx'], S['sy'], S['sx'] - sr, S['sy'] + sr * 0.85,
                    one * RAIN[0], one * RAIN[1], one * RAIN[2], sa, zs, one],
                   axis=1)
    sp2 = np.stack([S['sx'], S['sy'], S['sx'] + sr * 0.9, S['sy'] + sr * 0.75,
                    one * RAIN[0], one * RAIN[1], one * RAIN[2], sa, zs, one],
                   axis=1)
    sp3 = np.stack([S['sx'] - sr * 1.3, S['sy'] + sr * 0.2,
                    S['sx'] + sr * 1.3, S['sy'] + sr * 0.2,
                    one * RAIN[0], one * RAIN[1], one * RAIN[2], sa * 0.5,
                    zs, one], axis=1)
    blocks.append((sp1, False))
    blocks.append((sp2, False))
    blocks.append((sp3, False))

    # --- the city, static, and it is the lightning that reveals it --------------
    st = S['static']
    n = st['n']
    sa2 = st['a'] * ink * (1.0 + st['lift'] * flash)
    st_arr = np.stack([st['x0'], st['y0'], st['x1'], st['y1'],
                       st['r'], st['g'], st['b'], sa2, st['z'],
                       np.zeros(n)], axis=1)
    blocks.append((st_arr, False))


    # --- the wet street ---------------------------------------------------------
    # Mirror everything that stands on the ground. The shimmer is a horizontal
    # banding on the mirrored y, not a displacement: on a street the water is a
    # film, not a body, so what breaks the reflection is the surface rippling, and
    # the figure should smear along its own length rather than wander sideways.
    if reflpar > 0.01:
        refl = []
        for (arr, dorefl) in blocks:
            if not dorefl or not len(arr):
                continue
            src = arr
            above = np.maximum(src[:, 1], src[:, 3]) > GROUNDY + 0.004
            k = np.nonzero(above)[0]
            if not len(k):
                continue
            m = src[k].copy()
            m[:, 1] = 2.0 * GROUNDY - src[k, 1]
            m[:, 3] = 2.0 * GROUNDY - src[k, 3]
            ymid = (m[:, 1] + m[:, 3]) * 0.5
            dep = np.clip(GROUNDY - ymid, 0.0, 0.8)
            wob = 0.010 * (0.4 + 1.4 * rain) * np.sin(ymid * 62.0 - t * 3.1)
            m[:, 0] = m[:, 0] + wob
            m[:, 2] = m[:, 2] + wob
            shim = 0.34 + 0.66 * (0.5 + 0.5 * np.sin(ymid * 118.0 + t * 2.4))
            m[:, 7] = m[:, 7] * 0.36 * reflpar * shim * np.exp(-dep * 2.2)
            m[:, 4] *= 0.86
            m[:, 5] *= 0.72
            m[:, 6] = np.minimum(1.4, m[:, 6] * 1.18)
            m[:, 8] = -0.18
            m[:, 9] = 1.0
            refl.append(m)
        for m in refl:
            blocks.append((m, False))

    parts = [b for (b, _) in blocks if len(b)]
    A = np.concatenate(parts, axis=0) if parts else np.zeros((0, 10))

    x0, y0, x1, y1 = A[:, 0], A[:, 1], A[:, 2], A[:, 3]
    dx, dy = x1 - x0, y1 - y0
    ln = np.hypot(dx, dy)
    al = A[:, 7]
    keep = ((np.minimum(x0, x1) < CULLX) & (np.maximum(x0, x1) > -CULLX)
            & (np.minimum(y0, y1) < CULLY) & (np.maximum(y0, y1) > -CULLY)
            & (ln > MINLEN) & (al > 0.005))
    idx = np.nonzero(keep)[0]
    # Emission order is priority: the man, then the drone, then whoever is walking
    # past, then the weather. If the pool ever ran dry it would be the far rain
    # that thinned, never him.
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
        par.Rainnow.val = min(1.0, rain)
        par.Walkers.val = float(len(S['people']))
        par.Labelfade.val = lf
        txt = CHECKPOINTS[cp][1].strip()
        if par.Scaletxt.eval() != txt:
            par.Scaletxt.val = txt
    except Exception:
        pass

    S['census'] = ('f %.3f | rain %.2f wind %.2f | people %d | lines %d/%d '
                   '| bolts %d | static %d'
                   % (f, rain, wind, len(S['people']), n, MAXSEG,
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
    SKYBASE=GROUNDY + 0.145,
    RAIN=PAL['RAIN'], RAINFAR=PAL['RAINFAR'], STREET=PAL['STREET'],
    SKYLINE=PAL['SKYLINE'], WINDOW=PAL['WINDOW'], PERSON=PAL['PERSON'],
    RED=PAL['RED'], RED2=PAL['RED2'], PURPLE=PAL['PURPLE'], FLASH=PAL['FLASH'],
    NRAIN=330, NSPL=44, NBAND=6,
    # gy, scale, alpha — further away is higher on screen, smaller, and dimmer
    LANES=((GROUNDY + 0.082, 0.222, 0.58), (GROUNDY + 0.030, 0.305, 0.84),
           (GROUNDY - 0.070, 0.425, 1.00)),
    BOLTLIFE=0.24, STOPDWELL=7.5, LISTEN0=0.66, LISTEN1=0.79,
    ARC_F=(0.00, 0.12, 0.26, 0.42, 0.56, 0.68, 0.80, 0.92, 1.00),
    ARC_RAIN=(0.42, 0.62, 0.74, 0.94, 1.00, 0.86, 0.70, 0.50, 0.42),
    ARC_CROWD=(0.42, 0.66, 1.00, 0.82, 0.52, 0.38, 0.14, 0.34, 0.42),
    ARC_THUN=(0.10, 0.24, 0.40, 1.00, 0.86, 0.38, 0.20, 0.12, 0.10),
    ARC_WIND=(0.30, 0.50, 0.56, 0.95, 1.00, 0.70, 0.44, 0.30, 0.30),
    CULLX=1.30, CULLY=0.70, MINLEN=0.0016,
) + ENGINE_BODY

engine = C(scriptCHOP, 'engine', 1940, 980)
engine.par.callbacks = eng_src.path
W(director, engine, 0)


# ---------------------------------------------------------------------------
# GEOMETRY AND RENDER — six TOPs, none of them a pass-through
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
soft(mat_line, widthnear=1.45, widthfar=1.45, widthaffectedbyfov=False,
     linenearalpha=1.0, blending=True, depthtest=False, depthwriting=False)
mat_line.par.widthnear.expr = ("max(0.8, parent().par.Linewidth * (1.0 + 0.12 * %s "
                               "+ 0.55 * %s))" % (D('kickenv'), D('flash')))
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
const vec3 CSTREET= ''' + _g3(PAL['STREET']) + ''';
const vec3 CRED   = ''' + _g3(PAL['RED']) + ''';
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
    r += sheet(uv, 26.0, 0.55, w * 0.22, 26.0, t) * 0.26;
    r += sheet(uv, 15.0, 0.95, w * 0.26, 18.0, t) * 0.34;
    r += sheet(uv,  8.5, 1.60, w * 0.30, 12.0, t) * 0.40;
    r *= 0.22 + 0.58 * rain;
    // the strike is what makes the whole volume of it visible at once
    r *= 1.0 + 3.4 * flash;
    col += CRAIN * r * (0.24 + 0.16 * uB.y);
    // haze, heaviest just above the road
    col += mix(CRAIN, SKYLOW, 0.55) * rain * 0.075
           * exp(-abs(uv.y - hz) * 3.2) * (0.6 + 0.5 * uB.x);

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
print('  antialias -> %r  (menu: %s)' % (AA, list(render_lines.par.antialias.menuNames)))
print('  %s' % eng_src.module._S['S']['census'])
print('  keys: 1-8 chapters | 0 restart | t thunder | p passer-by | s stops | n reseed')
