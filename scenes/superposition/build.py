# Superposition — Schrodinger's cat, in a box, revealed from time to time in a
# different quantum state each time the lid comes up.
#
# The box is closed most of the time, and while it is closed the cat is BOTH: two
# faint ghosts, one sitting and one keeled over, flickering over each other while
# the box rattles on the kick. Then a bass drop opens the lid, the wavefunction
# collapses in a burst of kaleidoscope, and we see which cat this time — alive,
# dead, still superposed, a wave, entangled with a twin, tunnelling through the
# wall, branching into many worlds, decohering into dust — or we are the cat,
# looking up out of the box at the giant eye of whoever opened it.
#
# EVERYTHING IS A STRAIGHT LINE (see bayou). The box is a wireframe with a lattice
# on its faces, the cat is a faceted head with nested-triangle ears, a chevron
# ladder down its chest and a tail of vertebra ticks; the observer's eye is n-gons
# inside n-gons. The whole frame is one instanced unit segment.
#
# THE QUANTUM STATES ARE OPERATORS ON LINE DRAWINGS. Superposition doubles every
# segment, the wavefunction bends them through a travelling wave field, tunnelling
# shreds whatever crosses the wall and reflects a ghost of it, decoherence scatters
# them. Because they are operators on arrays of segments, not features of the cat,
# the same operator applies to the cat's own point of view: press V in any state
# and see the box from inside, through that state.
#
# AUDIO. Tempo is the story clock. The kick rattles the closed box, blinks the cat,
# ticks the Geiger counter, decays the atom and throws a short kaleidoscopic
# hallucination; a DROP opens the lid (the schedule only arms it) and floods the
# frame with the kaleidoscope, a new fold count and a new hue. Bass is the wave
# amplitude and the probability cloud; highs are the interference fringes, the
# whiskers and the fuzz on the ghosts.
#
# BUILT TO RUN ALL NIGHT: Script CHOP channels are built once and then only written;
# every list is capped and aged; every phase wraps; the story loops.
#
# Idempotent: destroys and recreates /project1/superposition and its project-level
# Out TOP, and touches nothing else. No media files.
#     code = open('scenes/superposition/build.py', encoding='utf-8').read()
#     g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
#
# GENERATED: this file is superposition_template.py + verbatim blocks of
# scenes/homestead/build.py (BEGIN/END HOMESTEAD), assembled by
# gen_superposition.py.

import math
import os

SCENE = 'superposition'
OUTW, OUTH = 1280, 720
ASPECT = OUTW / OUTH
ORTHOW = 2.0
ORTHOH = ORTHOW / ASPECT
CLOCKLEN = 60.0

STORYDEF = 360.0
MAXSEG = 12000

CHECKPOINTS = [
    ('alive',    ' 1 - ALIVE',               0 / 9.0),
    ('dead',     ' 2 - DEAD',                1 / 9.0),
    ('super',    ' 3 - SUPERPOSITION',       2 / 9.0),
    ('wave',     ' 4 - WAVEFUNCTION',        3 / 9.0),
    ('entangle', ' 5 - ENTANGLEMENT',        4 / 9.0),
    ('tunnel',   ' 6 - TUNNELLING',          5 / 9.0),
    ('worlds',   ' 7 - MANY WORLDS',         6 / 9.0),
    ('decohere', ' 8 - DECOHERENCE',         7 / 9.0),
    ('pov',      " 9 - THE CAT'S EYE VIEW",  8 / 9.0),
]

proj = op('/project1')
for stale in (SCENE, SCENE + '_out'):
    o = proj.op(stale)
    if o:
        o.destroy()

s = proj.create(containerCOMP, SCENE)
s.nodeX, s.nodeY = 0, -4400
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
pg = s.appendCustomPage('Superposition')
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
    ('Kaleido',    'Kaleidoscope Amount', 1.0, 0.0, 2.0),
    ('Kickkal',    'Kaleidoscope on Kicks', 1.0, 0.0, 2.0),
    ('Trails',     'Trails',              1.0, 0.0, 1.5),
    ('Linewidth',  'Line Width (px)',     1.5, 0.5, 4.0),
    ('Ink',        'Brightness of Art',   1.0, 0.0, 2.0),
    ('Glow',       'Glow',                1.0, 0.0, 3.0),
    ('Fringes',    'Interference Fringes', 1.0, 0.0, 3.0),
    ('Label',      'Chapter Readout',     1.0, 0.0, 2.0),
    ('Vignette',   'Vignette',            0.75, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

_RO = [('Bpm', 0, 200), ('Showt', 0, 2400), ('Chapter', 0, len(CHECKPOINTS)),
       ('Kal', 0, 2), ('Kalseg', 2, 16), ('Kalrot', 0, 7), ('Warp', 0, 3),
       ('Hue', 0, 1), ('Kfx', -1.2, 1.2), ('Kfy', -0.8, 0.8), ('Trail', 0, 1), ('Fringe', 0, 1), ('Povm', 0, 1),
       ('Lid', 0, 1), ('Flash', 0, 1), ('Loops', 0, 1e6), ('Rejects', 0, 1e6),
       ('Segs', 0, MAXSEG), ('Labelfade', 0, 1),
       ('Bassm', 0, 1), ('Highm', 0, 1), ('Energym', 0, 1)]
for _mn, _lo, _hi in _RO:
    pg.appendFloat(_mn, label=_mn)
    _p = getattr(s.par, _mn)
    _p.normMin, _p.normMax = _lo, _hi
    _p.readOnly = True
s.par.Kalseg.val = 6.0

pg.appendToggle('Loop', label='Loop the Story')
s.par.Loop.default = True
s.par.Loop.val = True
pg.appendToggle('Pov', label="V - THE CAT'S POINT OF VIEW")
s.par.Pov.val = False
pg.appendToggle('Kaleidolock', label='M - HOLD THE KALEIDOSCOPE')
s.par.Kaleidolock.val = False
pg.appendStr('Scaletxt', label='Chapter Text')
s.par.Scaletxt.readOnly = True
s.par.Scaletxt.val = ''

pg.appendPulse('Observe', label='O - OBSERVE (open the box / collapse the state)')
pg.appendPulse('Trip', label='K - KALEIDOSCOPE (a hallucination, now)')
pg.appendPulse('Reseed', label='N - RESEED (new worlds)')
pg.appendPulse('Restart', label='0 - RESTART')
pg.appendPulse('Nextcp', label='next state')
pg.appendPulse('Prevcp', label='previous state')
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
# DIRECTOR — verbatim from homestead. Its verb queue ('pending') is unused here:
# this scene's verbs go to the engine through 'qverbs'.
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
# THE ENGINE — the box, the cat in all its states, and the cat's own view
# ---------------------------------------------------------------------------
ENGINE_BODY = r'''# Everything you see is emitted from here as line segments, and handed to one
# instanced unit segment (see bayou). Three coordinate spaces, kept apart:
#
#   LOCAL   the cat's own drawing plane: base of the cat at (0, 0), a sitting cat is
#           1.0 tall. The quantum operators act here, on arrays of segments.
#   BOX     3D, the box is the cube [-0.5, 0.5]^3. Box, props and the observer's eye
#           live here; the cat's local plane is billboarded into it facing the
#           camera; one numpy projection (with near-plane clipping) takes it to
#   SCREEN  the ortho frame, x in [-1, 1], y in [-0.5625, 0.5625].
#
# A 2D row is (x0, y0, x1, y1, r, g, b, a); a 3D row is (x0, y0, z0, x1, y1, z1, r,
# g, b, a). Rows are built in Python lists (the drawing code stays legible) and
# become numpy arrays as soon as they are whole shapes.
import math
import random
import numpy as np

_S = {'S': None}
_PUB = {'built': False}
TAU = 2.0 * math.pi
NCH = len(CHECKPOINTS)


def _ss(a, b, x):
    if a == b:
        return 1.0 if x >= b else 0.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def _cl(x, lo=0.0, hi=1.0):
    return min(hi, max(lo, x))


def _mix(c1, c2, k):
    return (c1[0] + (c2[0] - c1[0]) * k, c1[1] + (c2[1] - c1[1]) * k,
            c1[2] + (c2[2] - c1[2]) * k)


def _h(i):
    x = math.sin(i * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)


# --- 2D primitives ----------------------------------------------------------------
def _L(out, x0, y0, x1, y1, c, a):
    out.append((x0, y0, x1, y1, c[0], c[1], c[2], a))


def _P(out, pts, c, a, closed=False):
    n = len(pts)
    for i in range(n if closed else n - 1):
        p, q = pts[i], pts[(i + 1) % n]
        out.append((p[0], p[1], q[0], q[1], c[0], c[1], c[2], a))


def _NG(out, cx, cy, r, n, rot, c, a, ry=None):
    ry = r if ry is None else ry
    _P(out, [(cx + r * math.cos(rot + i * TAU / n), cy + ry * math.sin(rot + i * TAU / n))
             for i in range(n)], c, a, True)


def _A2(rows):
    return np.array(rows, dtype=np.float64).reshape(-1, 8)


# --- 3D primitives ----------------------------------------------------------------
def _L3(out, p, q, c, a):
    out.append((p[0], p[1], p[2], q[0], q[1], q[2], c[0], c[1], c[2], a))


def _P3(out, pts, c, a, closed=False):
    n = len(pts)
    for i in range(n if closed else n - 1):
        _L3(out, pts[i], pts[(i + 1) % n], c, a)


def _ring3(out, ctr, e1, e2, r, n, rot, c, a):
    pts = []
    for i in range(n):
        an = rot + i * TAU / n
        ca, sa = math.cos(an) * r, math.sin(an) * r
        pts.append((ctr[0] + e1[0] * ca + e2[0] * sa, ctr[1] + e1[1] * ca + e2[1] * sa,
                    ctr[2] + e1[2] * ca + e2[2] * sa))
    _P3(out, pts, c, a, True)


def _cube3(out, c0, c1, col, a):
    x0, y0, z0 = c0
    x1, y1, z1 = c1
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    for i, j in ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
                 (0, 4), (1, 5), (2, 6), (3, 7)):
        _L3(out, v[i], v[j], col, a)


def _A3(rows):
    return np.array(rows, dtype=np.float64).reshape(-1, 10)


# --- cameras and the one projection -----------------------------------------------
def _norm3(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _cam_look(P, F, f):
    F = _norm3(F)
    R = _norm3(_cross(F, (0.0, 1.0, 0.0)))
    U = _cross(R, F)
    return (np.array(P), np.array(R), np.array(U), np.array(F), f)


def _proj(A3, cam, fog=0.0):
    """3D rows -> screen 2D rows, clipped at the near plane."""
    if len(A3) == 0:
        return np.zeros((0, 8))
    P, R, U, F, f = cam
    p0 = A3[:, 0:3] - P
    p1 = A3[:, 3:6] - P
    x0, y0, z0 = p0 @ R, p0 @ U, p0 @ F
    x1, y1, z1 = p1 @ R, p1 @ U, p1 @ F
    keep = (z0 > NEAR) | (z1 > NEAR)
    x0, y0, z0, x1, y1, z1 = x0[keep], y0[keep], z0[keep], x1[keep], y1[keep], z1[keep]
    col = A3[keep, 6:10].copy()
    m = z0 < NEAR
    if m.any():
        t = (NEAR - z0[m]) / (z1[m] - z0[m])
        x0[m] += (x1[m] - x0[m]) * t
        y0[m] += (y1[m] - y0[m]) * t
        z0[m] = NEAR
    m = z1 < NEAR
    if m.any():
        t = (NEAR - z1[m]) / (z0[m] - z1[m])
        x1[m] += (x0[m] - x1[m]) * t
        y1[m] += (y0[m] - y1[m]) * t
        z1[m] = NEAR
    if fog > 0.0:
        col[:, 3] *= np.exp(-np.maximum(0.0, (z0 + z1) * 0.5 - 0.6) * fog)
    return np.column_stack([f * x0 / z0, f * y0 / z0, f * x1 / z1, f * y1 / z1, col])


def _bill(A2, base, R, U, s):
    """Local 2D rows -> 3D rows on a plane through `base` spanned by R and U."""
    out = np.empty((len(A2), 10))
    for k, (ix, iy) in enumerate(((0, 1), (2, 3))):
        for d in range(3):
            out[:, 3 * k + d] = base[d] + s * (A2[:, ix] * R[d] + A2[:, iy] * U[d])
    out[:, 6:10] = A2[:, 4:8]
    return out


# --- the quantum operators: arrays of segments in, arrays of segments out ----------
def _xf(A, sx=1.0, sy=None, tx=0.0, ty=0.0, rot=0.0, px=0.0, py=0.0, a=1.0):
    """Scale about (px, py), rotate, translate; multiply alpha."""
    sy = sx if sy is None else sy
    B = A.copy()
    c, s_ = math.cos(rot), math.sin(rot)
    for ix, iy in ((0, 1), (2, 3)):
        x = (A[:, ix] - px) * sx
        y = (A[:, iy] - py) * sy
        B[:, ix] = px + x * c - y * s_ + tx
        B[:, iy] = py + x * s_ + y * c + ty
    B[:, 7] *= a
    return B


def _tint(A, col, k):
    B = A.copy()
    for i in range(3):
        B[:, 4 + i] += (col[i] - B[:, 4 + i]) * k
    return B


def _subdiv(A, m):
    if m <= 1 or len(A) == 0:
        return A
    t0 = np.arange(m) / float(m)
    t1 = (np.arange(m) + 1.0) / m
    x0, y0 = A[:, 0:1], A[:, 1:2]
    dx, dy = A[:, 2:3] - x0, A[:, 3:4] - y0
    return np.column_stack([(x0 + dx * t0).ravel(), (y0 + dy * t0).ravel(),
                            (x0 + dx * t1).ravel(), (y0 + dy * t1).ravel(),
                            np.repeat(A[:, 4:8], m, axis=0)])


def _double(A, d, ang, a=0.6):
    """SUPERPOSITION: every segment is in two places at once."""
    dx, dy = d * math.cos(ang), d * math.sin(ang)
    return np.vstack([_xf(A, tx=dx, ty=dy, a=a), _xf(A, tx=-dx, ty=-dy, a=a)])


def _wave(A, amp, k, t, m=4):
    """WAVEFUNCTION: a travelling wave field bends every segment. One continuous
    field, so segments that met still meet."""
    if len(A) == 0 or amp <= 0.0:
        return A
    B = _subdiv(A, m)
    for ix, iy in ((0, 1), (2, 3)):
        x, y = B[:, ix].copy(), B[:, iy].copy()
        B[:, iy] = y + amp * np.sin(k * x - t * 3.1) * (0.6 + 0.4 * np.sin(k * 0.37 * y + t))
        B[:, ix] = x + amp * 0.55 * np.sin(k * 1.31 * y + t * 2.3)
    return B


def _scatter(A, amt, rnd, cx, cy):
    """DECOHERENCE: every segment leaks into the environment on its own path."""
    n = len(A)
    if n == 0 or amt <= 1e-4:
        return A
    R = rnd[np.arange(n) % len(rnd)]
    mx, my = (A[:, 0] + A[:, 2]) * 0.5, (A[:, 1] + A[:, 3]) * 0.5
    hx, hy = (A[:, 2] - A[:, 0]) * 0.5, (A[:, 3] - A[:, 1]) * 0.5
    an = R[:, 2] * amt * 2.6
    c, s_ = np.cos(an), np.sin(an)
    hx, hy = hx * c - hy * s_, hx * s_ + hy * c
    dist = amt * (0.20 + 0.85 * np.abs(R[:, 3])) * (1.0 + 1.6 * np.hypot(mx - cx, my - cy))
    mx = mx + R[:, 0] * dist
    my = my + R[:, 1] * dist
    B = A.copy()
    B[:, 0], B[:, 1], B[:, 2], B[:, 3] = mx - hx, my - hy, mx + hx, my + hy
    B[:, 7] *= 1.0 - 0.55 * amt
    return B


def _tunnel(A, wall, band, trans, refl, side):
    """TUNNELLING: what crosses the wall is shredded, what gets through is faint,
    and a ghost of it is reflected back."""
    if len(A) == 0:
        return A
    B = _subdiv(A, 3)
    if side < 0:
        B[:, 0] *= -1.0
        B[:, 2] *= -1.0
    mx = (B[:, 0] + B[:, 2]) * 0.5
    inb = np.abs(mx - wall) < band
    idx = np.arange(len(B))
    B = B[~(inb & (idx % 2 == 1))]
    mx = (B[:, 0] + B[:, 2]) * 0.5
    inb = np.abs(mx - wall) < band
    past = mx >= wall + band
    B[inb, 7] *= 0.55
    B[past, 7] *= trans * np.exp(-(mx[past] - wall) * 1.4)
    G = B[past].copy()
    G[:, 0] = 2.0 * wall - G[:, 0]
    G[:, 2] = 2.0 * wall - G[:, 2]
    G[:, 7] *= refl / max(trans, 1e-3)
    B = np.vstack([B, G])
    if side < 0:
        B[:, 0] *= -1.0
        B[:, 2] *= -1.0
    return B


# --- the cat ----------------------------------------------------------------------
# Front view, sitting. Every part is the same few motifs: a faceted polygon, a
# triangle nested in a triangle, a chevron ladder, n-gons for the eyes. `lie` tips
# him over onto his side and turns his eyes to crosses: the dead cat is the same
# drawing rotated, which is what lets the two states morph into each other.
HEAD = [(-0.21, 0.78), (-0.16, 0.63), (0.0, 0.575), (0.16, 0.63), (0.21, 0.78),
        (0.15, 0.88), (-0.15, 0.88)]
BODY = [(-0.13, 0.60), (-0.22, 0.46), (-0.28, 0.24), (-0.30, 0.06), (-0.25, 0.0),
        (0.25, 0.0), (0.30, 0.06), (0.28, 0.24), (0.22, 0.46), (0.13, 0.60)]


def _cat_rows(c, a, det, lie, blink, pupil, ear, tail, whisk, look):
    out = []
    dead = _ss(0.45, 0.85, lie)
    _P(out, HEAD, c, a, True)
    # ears: a triangle, and a triangle inside it
    for sg in (-1.0, 1.0):
        tw = ear * (0.6 if sg > 0 else 1.0)
        tip = (sg * (0.185 + 0.035 * tw), 1.0 - 0.035 * tw - 0.04 * dead)
        b0, b1 = (sg * 0.205, 0.80), (sg * 0.075, 0.88)
        _P(out, [b0, tip, b1], c, a)
        cx, cy = (b0[0] + tip[0] + b1[0]) / 3.0, (b0[1] + tip[1] + b1[1]) / 3.0
        _P(out, [(cx + (p[0] - cx) * 0.5, cy + (p[1] - cy) * 0.5) for p in (b0, tip, b1)],
           c, a * det, True)
    # the face lattice: nose to every facet of the head
    for p in HEAD:
        _L(out, 0.0, 0.672, p[0], p[1], c, a * det * 0.45)
    # eyes
    for sg in (-1.0, 1.0):
        ex, ey = sg * 0.085 + look * 0.008, 0.748
        if dead < 0.999:
            h = 0.034 * (1.0 - blink) + 0.003
            ea = a * (1.0 - dead)
            _P(out, [(ex - 0.05, ey), (ex, ey + h), (ex + 0.05, ey), (ex, ey - h)], c, ea, True)
            if blink < 0.75:
                px = ex + look * 0.016
                _L(out, px, ey - h * 0.85, px, ey + h * 0.85, c, ea)
                if pupil > 0.02:
                    _NG(out, px, ey, 0.006 + 0.017 * pupil, 6, 0.0, c, ea * pupil,
                        ry=min(0.006 + 0.017 * pupil, h * 0.9))
        if dead > 0.001:
            da = a * dead
            _L(out, ex - 0.028, ey - 0.022, ex + 0.028, ey + 0.022, c, da)
            _L(out, ex - 0.028, ey + 0.022, ex + 0.028, ey - 0.022, c, da)
    # nose, mouth, and a tongue when he is dead
    _P(out, [(-0.02, 0.683), (0.02, 0.683), (0.0, 0.663)], c, a, True)
    _L(out, 0.0, 0.663, -0.028, 0.646, c, a)
    _L(out, 0.0, 0.663, 0.028, 0.646, c, a)
    if dead > 0.01:
        _P(out, [(-0.012, 0.652), (0.0, 0.625), (0.012, 0.652)], c, a * dead)
    # whiskers
    for sg in (-1.0, 1.0):
        for k in range(3):
            sw = whisk * 0.012 * (k - 1) + 0.006 * math.sin(k * 2.1 + look)
            _L(out, sg * 0.05, 0.672 - k * 0.006, sg * 0.34, 0.725 - k * 0.05 + sw, c,
               a * (0.75 - 0.12 * k))
    # body, open at the neck where the head sits
    _P(out, BODY, c, a)
    for i in range(5):
        y = 0.53 - 0.075 * i
        w = 0.045 + 0.022 * i
        _P(out, [(-w, y), (0.0, y - 0.032), (w, y)], c, a * det * 0.8)
    for p in BODY[1:-1]:
        _L(out, 0.0, 0.30, p[0], p[1], c, a * det * 0.35)
    # front legs and paws
    for sg in (-1.0, 1.0):
        _L(out, sg * 0.035, 0.36, sg * 0.035, 0.018, c, a)
        _L(out, sg * 0.105, 0.33, sg * 0.105, 0.018, c, a)
        _P(out, [(sg * 0.02, 0.0), (sg * 0.07, 0.032), (sg * 0.12, 0.0)], c, a)
    # tail: a curling spine with a vertebra tick at every joint
    pts = []
    for i in range(11):
        u = i / 10.0
        an = u * (1.9 + 0.5 * tail)
        pts.append((0.28 + 0.27 * math.sin(an), 0.03 + 0.40 * (1.0 - math.cos(an)) +
                    0.05 * tail * u * u))
    _P(out, pts, c, a)
    for i in range(1, 10):
        (x0, y0), (x1, y1) = pts[i - 1], pts[i + 1]
        nx, ny = -(y1 - y0), (x1 - x0)
        nl = math.hypot(nx, ny) or 1.0
        k = 0.028 * (1.0 - i / 12.0) / nl
        x, y = pts[i]
        _L(out, x - nx * k, y - ny * k, x + nx * k, y + ny * k, c, a * det * 0.8)
    A = _A2(out)
    if lie > 0.001:
        e = lie * lie * (3.0 - 2.0 * lie)
        A = _xf(A, rot=-e * math.pi * 0.5, tx=-0.52 * e, ty=0.31 * e)
    return A


def _cat(c, a, det=0.6, lie=0.0, blink=0.0, pupil=0.2, ear=0.0, tail=0.0, whisk=0.0,
         look=0.0):
    return _cat_rows(c, a, det, lie, blink, pupil, ear, tail, whisk, look)


# --- the observer's eye -----------------------------------------------------------
def _eye(c, a, opn, rot, pupil, gx, gy):
    out = []
    n = 12
    up, lo = [], []
    for i in range(n + 1):
        x = -0.5 + i / float(n)
        k = max(0.0, 1.0 - (2.0 * x) ** 2) ** 0.8
        up.append((x, 0.25 * k * opn))
        lo.append((x, -0.19 * k * opn))
    _P(out, up, c, a)
    _P(out, lo, c, a)
    for i in range(1, n, 1):
        x, y = up[i]
        _L(out, x, y, x * 1.12, y + 0.07 + 0.03 * abs(x), c, a * 0.55)
    if opn > 0.08:
        for r, m, sgn in ((0.165, 12, 1.0), (0.125, 9, -1.0), (0.085, 6, 1.0)):
            _NG(out, gx, gy, r, m, rot * sgn, c, a * 0.8, ry=r * min(1.0, opn * 1.1))
        pr = 0.035 + 0.05 * pupil
        for k in range(3):
            _NG(out, gx, gy, pr * (1.0 - 0.3 * k), 6, rot * 0.5, c, a, ry=pr * (1.0 - 0.3 * k) * opn)
        for i in range(12):
            an = i * TAU / 12.0 + rot * 0.25
            _L(out, gx + math.cos(an) * pr * 1.1, gy + math.sin(an) * pr * 1.1 * opn,
               gx + math.cos(an) * 0.16, gy + math.sin(an) * 0.16 * opn, c, a * 0.35)
    return _A2(out)


# --- the box and what is in it ------------------------------------------------------
def _box(lid, col, a, det, trefoil):
    out = []
    h = 0.5
    v = [(-h, -h, -h), (h, -h, -h), (h, -h, h), (-h, -h, h),
         (-h, h, -h), (h, h, -h), (h, h, h), (-h, h, h)]
    for i, j in ((0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 5), (2, 6), (3, 7),
                 (4, 5), (5, 6), (6, 7), (7, 4)):
        _L3(out, v[i], v[j], col, a)
    # a lattice on each face: the motif repeated
    n = 4
    for k in range(1, n):
        s_ = -h + k / float(n)
        _L3(out, (s_, -h, h), (s_, h, h), col, a * det)          # front
        _L3(out, (-h, s_, h), (h, s_, h), col, a * det)
        _L3(out, (s_, -h, -h), (s_, h, -h), col, a * det)        # back
        _L3(out, (-h, s_, -h), (h, s_, -h), col, a * det)
        _L3(out, (-h, -h, s_), (-h, h, s_), col, a * det)        # sides
        _L3(out, (-h, s_, -h), (-h, s_, h), col, a * det)
        _L3(out, (h, -h, s_), (h, h, s_), col, a * det)
        _L3(out, (h, s_, -h), (h, s_, h), col, a * det)
        _L3(out, (s_, -h, -h), (s_, -h, h), col, a * det)        # floor
        _L3(out, (-h, -h, s_), (h, -h, s_), col, a * det)
    # the lid, hinged on the back top edge
    th = lid * 1.95
    cz, sy = math.cos(th), math.sin(th)

    def lp(x, d):   # d: 0 at the hinge .. 1 at the front edge
        return (x, h + sy * d, -h + cz * d)
    q = [lp(-h, 0.0), lp(h, 0.0), lp(h, 1.0), lp(-h, 1.0)]
    _P3(out, q, col, a * 1.1, True)
    for k in range(1, n):
        _L3(out, lp(-h + k / float(n), 0.0), lp(-h + k / float(n), 1.0), col, a * det)
        _L3(out, lp(-h, k / float(n)), lp(h, k / float(n)), col, a * det)
    # the trefoil on the front face
    if trefoil > 0.0:
        cx, cy, r0, r1 = 0.0, -0.18, 0.03, 0.11
        for k in range(3):
            a0 = math.pi * 0.5 + k * TAU / 3.0 - 0.5
            arc = [(cx + r1 * math.cos(a0 + i * 0.25), cy + r1 * math.sin(a0 + i * 0.25))
                   for i in range(5)]
            pts = [(cx + r0 * math.cos(a0), cy + r0 * math.sin(a0))] + arc + \
                  [(cx + r0 * math.cos(a0 + 1.0), cy + r0 * math.sin(a0 + 1.0))]
            _P3(out, [(p[0], p[1], h + 0.002) for p in pts], CPROP, trefoil, True)
        _ring3(out, (cx, cy, h + 0.002), (1, 0, 0), (0, 1, 0), 0.018, 6, 0.0, CPROP, trefoil)
    return out


def _props(out, t, kickenv, dead, decays, a):
    # the Geiger counter: a box, a dial, a needle that jumps on the kick
    g0 = (0.20, -0.5, -0.40)
    _cube3(out, g0, (0.40, -0.39, -0.28), CPROP, a * 0.8)
    dc = (0.30, -0.445, -0.279)
    arc = [(dc[0] + 0.045 * math.cos(math.pi * (0.15 + 0.7 * i / 6.0)),
            dc[1] - 0.02 + 0.045 * math.sin(math.pi * (0.15 + 0.7 * i / 6.0)), dc[2])
           for i in range(7)]
    _P3(out, arc, CPROP, a * 0.7)
    na = math.pi * (0.80 - 0.62 * kickenv)
    _L3(out, (dc[0], dc[1] - 0.02, dc[2]),
        (dc[0] + 0.05 * math.cos(na), dc[1] - 0.02 + 0.05 * math.sin(na), dc[2]), CPROP, a)
    if kickenv > 0.05:       # the click
        for k in range(6):
            an = k * TAU / 6.0 + t * 3.0
            r0, r1 = 0.09, 0.09 + 0.07 * kickenv
            _L3(out, (0.30 + r0 * math.cos(an), -0.44 + r0 * math.sin(an), -0.34),
                (0.30 + r1 * math.cos(an), -0.44 + r1 * math.sin(an), -0.34), CPROP,
                a * kickenv)
    # the flask of poison under its hammer: a hexagonal prism, a neck, a stopper —
    # and after the hammer falls, a ring of shards
    fc = (-0.30, -0.5, -0.30)
    rings = [(0.0, 0.055), (0.07, 0.055), (0.11, 0.02), (0.16, 0.02)]
    if dead < 0.5:
        prev = None
        for hy, r in rings:
            pts = [(fc[0] + r * math.cos(i * TAU / 6.0), fc[1] + hy,
                    fc[2] + r * math.sin(i * TAU / 6.0)) for i in range(6)]
            _P3(out, pts, CPROP, a * 0.85, True)
            if prev:
                for i in range(6):
                    _L3(out, prev[i], pts[i], CPROP, a * 0.5)
            prev = pts
        _cube3(out, (fc[0] - 0.012, fc[1] + 0.16, fc[2] - 0.012),
               (fc[0] + 0.012, fc[1] + 0.19, fc[2] + 0.012), CPROP, a * 0.8)
        ha = 0.55
    else:
        for i in range(9):
            an = i * TAU / 9.0 + 0.3
            r0 = 0.03 + 0.05 * _h(i)
            p = (fc[0] + r0 * math.cos(an), fc[1] + 0.002, fc[2] + r0 * math.sin(an))
            _L3(out, p, (p[0] + 0.03 * math.cos(an + 1.0), p[1] + 0.01 * _h(i + 9),
                         p[2] + 0.03 * math.sin(an + 1.0)), CPROP, a * 0.8)
        ha = -0.05
    # the hammer on its arm
    pv = (-0.30, -0.24, -0.45)
    hd = (-0.30, -0.24 - 0.09 * math.cos(ha), -0.45 + 0.15 * math.sin(ha) + 0.05)
    _L3(out, pv, hd, CPROP, a * 0.8)
    _cube3(out, (hd[0] - 0.03, hd[1] - 0.02, hd[2] - 0.02),
           (hd[0] + 0.03, hd[1] + 0.02, hd[2] + 0.02), CPROP, a * 0.8)
    _L3(out, pv, (pv[0], -0.5, pv[2]), CPROP, a * 0.6)
    # the atom: three tilted orbits and a nucleus, and what it throws off on the kick
    ac = (0.30, -0.22, -0.34)
    for k in range(3):
        an = k * math.pi / 3.0 + t * 0.4
        e1 = (math.cos(an), 0.0, math.sin(an))
        _ring3(out, ac, e1, (0.0, 1.0, 0.0), 0.06, 10, t * 1.6 + k, CATOM, a * 0.8)
        ea = t * (2.3 + k * 0.6) + k * 2.0
        ep = (ac[0] + 0.06 * (e1[0] * math.cos(ea)), ac[1] + 0.06 * math.sin(ea),
              ac[2] + 0.06 * (e1[2] * math.cos(ea)))
        _ring3(out, ep, (1, 0, 0), (0, 1, 0), 0.008, 4, 0.0, CATOM, a)
    _ring3(out, ac, (1, 0, 0), (0, 1, 0), 0.014, 6, t, CATOM, a)
    for (age, dx, dy, dz) in decays:
        k = age / DECAYLIFE
        r0, r1 = 0.02 + 0.6 * k, 0.02 + 0.6 * k + 0.08
        _L3(out, (ac[0] + dx * r0, ac[1] + dy * r0, ac[2] + dz * r0),
            (ac[0] + dx * r1, ac[1] + dy * r1, ac[2] + dz * r1), CATOM, a * (1.0 - k))


# --- state --------------------------------------------------------------------------
def _new(seed):
    return {
        'seed': seed, 'rs': random.Random(seed),
        'rnd': np.random.RandomState(seed % 2147483647).uniform(-1.0, 1.0, (4096, 4)),
        'last': {}, 'lastraw': None,
        'kalslow': 0.0, 'kalfast': 0.0, 'krot': 0.0, 'kseg': 6.0, 'hue': 0.0,
        'lid': 0.0, 'catup': 0.0, 'rev': False, 'cp': -1, 'u': 0.0, 'since': 0.0,
        'flash': 0.0, 'blink': 0.0, 'ear': 0.0, 'rabi': 0.0, 'tph': 0.0,
        'ent': 0.0, 'entlie': 0.0, 'entt': -99.0, 'entflash': 0.0, 'collapse': 0.0, 'cstate': 1.0,
        'nk': 0, 'wd': 1.0, 'dec': 0.6, 'povm': 0.0, 'paw': 0,
        'cam': [0.08, 3.3, 0.36, 0.5], 'decays': [], 'eyerot': 0.0,
        'errs': 0, 'lastout': None, 'lastcp': -1, 'labelt': 0.0, 'census': '',
        'loops': 0, 'lastshow': 0.0, 'face': [0.0, 0.0], 'labtxt': '', 'labtick': 0.0,
    }


def _delta(S, inp, name):
    try:
        v = float(inp[name][0])
    except Exception:
        return 0
    prev = S['last'].get(name)
    S['last'][name] = v
    if prev is None or v < prev:
        return 0
    return int(round(v - prev))


def _chan(inp, name, default=0.0):
    try:
        return float(inp[name][0])
    except Exception:
        return default


# --- the cat, per state, in its local plane ---------------------------------------
def _cat_scene(S, ch, t, E):
    """Everything drawn in the cat's local plane, for the observer's view."""
    up = S['catup']
    arrs = []
    kw = dict(blink=S['blink'], pupil=min(1.0, 0.15 + 0.8 * E['dropenv'] + S['flash']),
              ear=S['ear'], tail=math.sin(t * 2.1) * (0.4 + E['bass']),
              whisk=E['high'], look=math.sin(t * 0.7))
    # closed (and while opening): both cats at once, faint, in each other's place
    cl = 1.0 - up
    if cl > 0.01:
        fa = 0.34 * cl * (0.65 + 0.35 * E['high'])
        jit = 0.010 + 0.025 * E['kickenv']
        A = _cat(CALIVE, fa, det=0.25, **kw)
        Dd = _cat(CDEAD, fa, det=0.25, lie=1.0)
        arrs.append(_double(A, jit, t * 4.0, 0.7))
        arrs.append(_double(Dd, jit, -t * 3.3, 0.7))
    if up <= 0.01:
        return arrs
    w_col = None
    if ch == 0 or ch == 8:                                           # ALIVE
        A = _cat(CALIVE, up, **kw)
        arrs.append(A)
        if E['kickenv'] > 0.05:
            arrs.append(_xf(A, sx=1.0 + 0.35 * (1.0 - E['kickenv']), px=0.0, py=0.5,
                            a=0.30 * E['kickenv']))
    elif ch == 1:                                                    # DEAD
        lie = _ss(0.6, 2.2, S['since'])
        fz = 1.0 - lie
        if fz > 0.01:
            A = _cat(CSUPER, up * fz, det=0.3, **kw)
            arrs.append(_double(A, 0.02, t * 6.0, 0.6))
        Dd = _cat(CDEAD, up, lie=lie, blink=0.0, pupil=0.0, whisk=0.0)
        arrs.append(Dd)
        if lie > 0.9:
            gph = (S['since'] * 0.22) % 1.0
            G = _cat(CDEAD, 1.0, det=0.0, pupil=0.0)
            arrs.append(_xf(G, sx=1.0 + 0.25 * gph, px=0.0, py=0.0,
                            tx=0.05 * math.sin(t * 1.3), ty=0.10 + 0.9 * gph,
                            a=up * 0.40 * math.sin(math.pi * gph)))
    elif ch == 2:                                                    # SUPERPOSITION
        w = 0.5 + 0.5 * math.cos(S['rabi'])
        w += (S['cstate'] - w) * S['collapse']
        d = 0.008 + 0.035 * E['kickenv'] * (1.0 - S['collapse'])
        A = _cat(CALIVE, up * (0.15 + 0.85 * w), **kw)
        Dd = _cat(CDEAD, up * (0.15 + 0.85 * (1.0 - w)), lie=1.0 - 0.15 * (1.0 - w))
        arrs.append(_double(A, d, t * 5.0, 0.75))
        arrs.append(_double(Dd, d, -t * 4.1, 0.75))
        E['psi'] = (math.sqrt(max(0.0, w)), math.sqrt(max(0.0, 1.0 - w)))
    elif ch == 3:                                                    # WAVE
        w = 0.5 + 0.5 * math.cos(S['rabi'] * 0.5)
        amp = 0.012 + 0.045 * E['bass'] + 0.05 * E['dropenv'] + 0.02 * E['kickenv']
        A = _cat(_mix(CALIVE, CWAVE, 0.45), up * (0.25 + 0.75 * w), **kw)
        Dd = _cat(_mix(CDEAD, CWAVE, 0.45), up * (0.25 + 0.75 * (1.0 - w)), lie=1.0)
        arrs.append(_wave(A, amp, 9.0, t))
        arrs.append(_wave(Dd, amp, 9.0, t + 1.7))
        # the wave packet itself, over his head
        pk = []
        n = 90
        for i in range(n + 1):
            x = -1.35 + 2.7 * i / float(n)
            env = math.exp(-((x - 0.55 * math.sin(t * 0.37)) ** 2) / 0.22)
            pk.append((x, 1.30 + (0.12 + 0.10 * E['bass']) * env * math.cos(x * 13.0 - t * 4.0)))
        wr = []
        _P(wr, pk, CWAVE, up * 0.85)
        env_pts = [(p[0], 1.30 + (0.12 + 0.10 * E['bass']) *
                    math.exp(-((p[0] - 0.55 * math.sin(t * 0.37)) ** 2) / 0.22)) for p in pk]
        _P(wr, env_pts, CWAVE, up * 0.35)
        _P(wr, [(p[0], 2.60 - p[1]) for p in env_pts], CWAVE, up * 0.35)
        for i in range(0, n + 1, 6):
            _L(wr, pk[i][0], 1.30, pk[i][0], pk[i][1], CWAVE, up * 0.25)
        arrs.append(_A2(wr))
        E['psi'] = (math.sqrt(w), math.sqrt(1.0 - w))
    elif ch == 4:                                                    # ENTANGLED
        el = S['entlie']
        sc = 0.62
        kwb = dict(kw)
        A = _cat(_mix(CALIVE, CDEAD, el), up, lie=el, **kwb)
        B = _cat(_mix(CALIVE, CDEAD, 1.0 - el), up, lie=1.0 - el, **kwb)
        arrs.append(_xf(A, sx=sc, tx=-0.36))
        arrs.append(_xf(_xf(B, sx=-1.0, sy=1.0), sx=sc, tx=0.36))
        wr = []
        fl = S['entflash']
        for k in range(5):
            pts = []
            for i in range(33):
                u = i / 32.0
                x = -0.36 + 0.72 * u
                y = 0.32 + 0.05 * k * 0.3 + (0.07 + 0.05 * E['bass']) * math.sin(math.pi * u) * \
                    math.sin(t * 2.6 + k * 1.26 + u * 7.0)
                pts.append((x, y))
            _P(wr, pts, _mix(CSUPER, CEYE, fl), up * (0.45 + 0.5 * fl))
        arrs.append(_A2(wr))
    elif ch == 5:                                                    # TUNNELLING
        ph = S['tph']
        x = 0.98 * math.sin(ph)
        bob = 0.02 * abs(math.sin(t * 7.0))
        A = _cat(CALIVE, up, **kw)
        A = _xf(A, tx=x, ty=bob)
        side = 1.0 if x >= 0.0 else -1.0
        arrs.append(_tunnel(A, WALL, 0.035, 0.55, 0.32, side))
        E['psi'] = None
        E['tr'] = 0.55
    elif ch == 6:                                                    # MANY WORLDS
        arrs.extend(_worlds(S, t, E, up, kw))
    elif ch == 7:                                                    # DECOHERENCE
        amt = S['dec']
        w = 0.5 + 0.5 * math.cos(S['rabi'])
        A = _cat(_mix(CALIVE, CSUPER, 0.3), up * (0.3 + 0.7 * w), **kw)
        Dd = _cat(_mix(CDEAD, CSUPER, 0.3), up * (0.3 + 0.7 * (1.0 - w)), lie=1.0)
        arrs.append(_scatter(A, amt, S['rnd'], 0.0, 0.5))
        arrs.append(_scatter(Dd, amt, S['rnd'][1000:], 0.0, 0.3))
        # the environment: photons crossing the box from every side, on fixed paths
        wr = []
        R = S['rnd']
        for i in range(48):
            ox, oy, dx, dy = R[3000 + i]
            sp = 0.25 + 0.2 * abs(ox)
            ph = (t * sp + (oy + 1.0) * 0.5) % 1.0
            px, py = ox * 1.3 + dx * (ph - 0.5) * 2.4, 0.5 + oy * 0.6 + dy * (ph - 0.5) * 1.6
            _L(wr, px, py, px + dx * 0.05, py + dy * 0.05, CEYE,
               up * 0.5 * amt * math.sin(math.pi * ph))
        arrs.append(_A2(wr))
    return arrs


def _worlds(S, t, E, up, kw):
    """MANY WORLDS: every kick the tree splits again. Each copy is alive or dead,
    and the branch lines are the worlds parting."""
    A = _cat(CALIVE, 1.0, det=0.45, **kw)
    Dd = _cat(CDEAD, 1.0, det=0.45, lie=1.0)
    arrs = []
    br = []
    wd = S['wd']
    lv_y = (0.0, 1.10, 1.85, 2.38, 2.76)
    lv_w = (0.0, 1.25, 2.25, 3.05, 3.60)
    seed = S['seed']
    prev = [(0.0, 0.0, 1.0)]
    for l in range(0, 5):
        vis = _cl(wd - l + 1.0)
        if vis <= 0.001:
            break
        n = 2 ** l
        sc = 0.64 ** l
        cur = []
        for i in range(n):
            x = 0.0 if n == 1 else ((i + 0.5) / n - 0.5) * lv_w[l]
            x += 0.03 * l * math.sin(t * 0.9 + i * 1.7)
            y = lv_y[l]
            alive = _h(seed * 0.001 + l * 17.0 + i * 3.1) > 0.45
            base = A if alive else Dd
            arrs.append(_xf(base, sx=sc, tx=x, ty=y, a=up * vis * (1.0 - 0.1 * l)))
            if l > 0:
                px, py, psc = prev[i // 2]
                _L(br, px, py + 0.95 * psc, x, y, CSUPER, up * vis * 0.55)
                _L(br, px, py + 0.95 * psc, x, y - 0.02, CSUPER, up * vis * 0.2)
            cur.append((x, y, sc))
        if vis > 0.5:
            E['worlds'] = n
        prev = cur
    arrs.append(_A2(br))
    return arrs


# --- the cat's own view -------------------------------------------------------------
def _pov_frame(S, ch, t, E):
    lid = S['lid']
    look_up = _ss(0.15, 0.85, lid)
    yaw = (1.0 - 0.7 * look_up) * 0.55 * math.sin(TAU * t / 23.0) + 0.06 * math.sin(t * 0.7)
    pitch = (0.08 + 0.10 * math.sin(TAU * t / 31.0)) * (1.0 - look_up) + 0.92 * look_up
    pitch += 0.03 * E['kickenv']
    P = (0.02 * math.sin(t * 0.5), -0.30 + 0.01 * math.sin(t * 1.7), 0.40)
    F = (-math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch))
    cam = _cam_look(P, F, POVF)
    rows = []
    # the inside of the box: every wall a lattice
    h = 0.5
    n = 8
    wa = 0.32
    for k in range(n + 1):
        s_ = -h + k / float(n)
        wk = wa * (1.6 if k in (0, n) else 1.0)
        _L3(rows, (s_, -h, -h), (s_, h, -h), CBOX, wk)       # back
        _L3(rows, (-h, s_, -h), (h, s_, -h), CBOX, wk)
        _L3(rows, (-h, -h, s_), (-h, h, s_), CBOX, wk)       # left
        _L3(rows, (-h, s_, -h), (-h, s_, h), CBOX, wk)
        _L3(rows, (h, -h, s_), (h, h, s_), CBOX, wk)         # right
        _L3(rows, (h, s_, -h), (h, s_, h), CBOX, wk)
        _L3(rows, (s_, -h, -h), (s_, -h, h), CBOX, wk)       # floor
        _L3(rows, (-h, -h, s_), (h, -h, s_), CBOX, wk)
        _L3(rows, (s_, -h, h), (s_, h, h), CBOX, wk * 0.6)   # front, behind him
        _L3(rows, (-h, s_, h), (h, s_, h), CBOX, wk * 0.6)
    th = lid * 1.95
    cz, sy = math.cos(th), math.sin(th)
    for k in range(n + 1):
        s_ = -h + k / float(n)
        wk = wa * (1.6 if k in (0, n) else 1.0)
        _L3(rows, (s_, h, -h), (s_, h + sy, -h + cz), CBOX, wk)
        d = k / float(n)
        _L3(rows, (-h, h + sy * d, -h + cz * d), (h, h + sy * d, -h + cz * d), CBOX, wk)
    _props(rows, t, E['kickenv'], E['dead'], S['decays'], 1.0)
    # the observer: a giant eye over the opening
    eyes = []
    if lid > 0.05:
        n_eyes = 1 if ch != 6 else max(1, min(7, 1 + S['nk'] // 3))
        opn = max(0.0, 1.0 - S['blink']) * _ss(0.2, 0.9, lid)
        for e in range(n_eyes):
            ox = 0.0 if e == 0 else (0.55 * ((e + 1) // 2) * (1 if e % 2 else -1))
            oy = 0.0 if e == 0 else 0.18 * ((e + 1) // 2)
            ctr = (ox * 0.8, 1.02 + oy, -0.25 - 0.1 * abs(ox))
            gx = 0.05 * math.sin(t * 0.8) + 0.03 * math.sin(t * 2.9)
            gy = -0.03 + 0.02 * math.sin(t * 1.1)
            Ea = _eye(CEYE, _ss(0.1, 0.7, lid) * (1.0 if e == 0 else 0.6), opn,
                      S['eyerot'] + e, min(1.0, E['dropenv'] + S['flash'] * 0.6), gx, gy)
            R, U = cam[1], cam[2]
            eyes.append(_bill(Ea, ctr, R, U, 0.95 * (1.0 if e == 0 else 0.6)))
    A3 = _A3(rows)
    if eyes:
        A3 = np.vstack([A3] + eyes)
    A = _proj(A3, cam, fog=0.55)
    # his paws and whiskers, in screen space, at the bottom of his view
    ov = []
    pc = _mix(CALIVE, CDEAD, E['dead'])
    for sg in (-1.0, 1.0):
        tap = 0.035 * E['kickenv'] if ((S['paw'] % 2 == 0) == (sg < 0)) else 0.0
        cx, cy = sg * 0.30, -0.47 + tap
        _NG(ov, cx, cy, 0.095, 8, math.pi / 8.0, pc, 0.9, ry=0.07)
        for k in range(3):
            _NG(ov, cx + (k - 1) * 0.045, cy + 0.07 + (0.012 if k == 1 else 0.0), 0.018, 6,
                0.0, pc, 0.8)
        _NG(ov, cx, cy - 0.01, 0.035, 6, 0.0, pc, 0.8, ry=0.026)
        _L(ov, cx - 0.09, cy - 0.02, cx - 0.12, -0.60, pc, 0.8)
        _L(ov, cx + 0.09, cy - 0.02, cx + 0.12, -0.60, pc, 0.8)
        for k in range(3):
            sw = 0.02 * E['high'] * math.sin(t * 9.0 + k)
            _L(ov, sg * 1.05, -0.30 - 0.03 * k, sg * 0.66, -0.20 + 0.045 * (k - 1) + sw, pc,
               0.45 - 0.1 * k)
    A = np.vstack([A, _A2(ov)])
    # the state, applied to the whole of his view
    if ch == 2:
        A = _double(A, 0.008 + 0.03 * E['kickenv'], t * 5.0, 0.7)
    elif ch == 3:
        A = _wave(A, 0.012 + 0.035 * E['bass'] + 0.03 * E['dropenv'], 5.0, t, m=3)
    elif ch == 4:
        A = np.vstack([A, _tint(_xf(A, sx=-1.0, sy=1.0, a=0.5), CSUPER, 0.5)])
    elif ch == 5:
        A = _tunnel(A, 0.30 + 0.25 * math.sin(S['tph']), 0.03, 0.6, 0.3, 1.0)
    elif ch == 7:
        A = _scatter(A, S['dec'] * 0.5, S['rnd'], 0.0, 0.0)
    if E['dead'] > 0.01:
        A = _tint(A, CDEAD, 0.6 * E['dead'])
        A = _xf(A, rot=1.25 * E['dead'], ty=-0.1 * E['dead'], a=1.0 - 0.3 * E['dead'])
    return A


# --- one frame ----------------------------------------------------------------------
def _frame(scriptOp):
    d = scriptOp.inputs[0] if scriptOp.inputs else None
    comp = scriptOp.parent()
    par = comp.par
    S = _S['S']
    if S is None:
        S = _S['S'] = _new(SEED0)

    raw = _chan(d, 'rawtime')
    show = _chan(d, 'show')
    slen = max(1.0, _chan(d, 'storylen', STORYDEF))
    bass, high, energy = _chan(d, 'bass'), _chan(d, 'high'), _chan(d, 'energy')
    kickenv, dropenv = _chan(d, 'kickenv'), _chan(d, 'dropenv')
    beatstr = _chan(d, 'beatstr')
    kicks = _delta(S, d, 'kickcnt')
    accents = _delta(S, d, 'accentcnt')
    drops = _delta(S, d, 'dropcnt')
    if S['lastraw'] is None:
        S['lastraw'] = raw
    dt = min(0.1, max(0.0, raw - S['lastraw']))
    S['lastraw'] = raw
    t = show
    bpm = float(par.Bpm.eval()) or float(par.Refbpm.eval())
    bp = 60.0 / max(60.0, min(200.0, bpm))
    if show < S['lastshow'] - slen * 0.5:
        S['loops'] += 1
    S['lastshow'] = show

    # verbs from the keys and pads
    observe = trip = False
    q = comp.fetch('qverbs', None)
    if q:
        comp.store('qverbs', [])
        for v in q[:16]:
            if v == 'observe':
                observe = True
            elif v == 'trip':
                trip = True
            elif v == 'reseed':
                S['seed'] = S['rs'].randint(1, 10 ** 8)
                S['rnd'] = np.random.RandomState(S['seed']).uniform(-1.0, 1.0, (4096, 4))

    # the chapter, and the lid
    L = slen / NCH
    cp = min(NCH - 1, max(0, int(show / L)))
    u = (show - cp * L) / L
    if cp != S['cp'] or u < S['u'] - 0.3:
        S['cp'] = cp
        S['rev'] = False
        S['nk'] = 0
        S['collapse'] = 0.0
        S['since'] = 0.0
        S['entt'] = -99.0
        S['wd'] = 1.0
        S['dec'] = 0.6
    S['u'] = u
    reveal = False
    if not S['rev']:
        if (u >= REVU0 and drops > 0) or u >= REVU1 or observe:
            S['rev'] = True
            reveal = True
            S['since'] = 0.0
    elif observe:
        S['collapse'] = 1.0
        S['cstate'] = 1.0 if S['rs'].random() < 0.5 else 0.0
        S['flash'] = 1.0
        S['kalslow'] = max(S['kalslow'], 0.8)
    if S['rev']:
        S['since'] += dt
    closing = u >= CLOSEU
    target = 1.0 if (S['rev'] and not closing) else 0.0
    S['lid'] += (target - S['lid']) * min(1.0, dt * (3.2 if target > S['lid'] else 1.6))
    S['catup'] += (target - S['catup']) * min(1.0, dt * 1.8)

    # the envelopes
    S['kalslow'] *= 0.5 ** (dt / 0.9)
    S['kalfast'] *= 0.5 ** (dt / 0.16)
    S['flash'] *= 0.5 ** (dt / 0.35)
    S['blink'] *= 0.5 ** (dt / 0.09)
    S['ear'] *= 0.5 ** (dt / 0.25)
    S['entflash'] *= 0.5 ** (dt / 0.5)
    S['collapse'] *= 0.5 ** (dt / 4.0)
    if kicks:
        S['kalfast'] = max(S['kalfast'], (0.35 + 0.65 * beatstr) * float(par.Kickkal.eval()))
        S['blink'] = max(S['blink'], 0.55 + 0.45 * beatstr)
        S['paw'] = (S['paw'] + 1) % 2
        if S['rev']:
            S['nk'] += 1
        dec = S['decays']
        rs = S['rs']
        for _ in range(min(kicks, 2)):
            v = (rs.uniform(-1, 1), rs.uniform(-0.6, 1), rs.uniform(-1, 1))
            nv = math.sqrt(sum(x * x for x in v)) or 1.0
            dec.append([0.0, v[0] / nv, v[1] / nv, v[2] / nv])
        del dec[:-DECAYMAX]
    for dcy in S['decays']:
        dcy[0] += dt
    S['decays'] = [x for x in S['decays'] if x[0] < DECAYLIFE]
    if accents:
        S['ear'] = 1.0
        if cp == 4 and S['rev'] and S['since'] - S['entt'] > 4.0 * bp:
            S['entt'] = S['since']
            S['ent'] = 1.0 - S['ent']
            S['entflash'] = 1.0
    S['entlie'] += (S['ent'] - S['entlie']) * min(1.0, dt * 3.5)
    if drops or trip or reveal:
        S['kalslow'] = 1.0 if (drops or trip) else max(S['kalslow'], 0.8)
        S['kseg'] = float(S['rs'].choice((3, 4, 5, 6, 6, 8)))
        S['hue'] = (S['hue'] + S['rs'].uniform(0.15, 0.85)) % 1.0
        S['flash'] = 1.0
    if drops and cp == 7:
        S['dec'] = 0.0
    lock = 0.6 if par.Kaleidolock.eval() else 0.0
    kal = max(S['kalslow'], 0.45 * S['kalfast'], lock) * float(par.Kaleido.eval())
    warp = (0.45 * S['kalfast'] + 0.9 * S['kalslow'] + 0.5 * lock) * (0.6 + 0.8 * bass)
    S['krot'] = (S['krot'] + dt * (0.10 + 0.9 * S['kalslow'] + 0.4 * S['kalfast'] + 0.2 * lock)) % TAU
    S['rabi'] = (S['rabi'] + dt * TAU / (8.0 * bp)) % (2.0 * TAU)
    S['tph'] = (S['tph'] + dt * TAU / (16.0 * bp)) % TAU
    S['eyerot'] = (S['eyerot'] + dt * (0.3 + 1.2 * dropenv)) % TAU
    S['wd'] += (min(5.0, 1.0 + S['nk'] / 4.0) - S['wd']) * min(1.0, dt * 1.5)
    if cp == 7:
        tgt = 0.55 + 0.4 * math.sin(TAU * S['since'] / (16.0 * bp)) + 0.25 * kickenv
        S['dec'] += (max(0.0, tgt) - S['dec']) * min(1.0, dt * 0.8)
    povt = 1.0 if (cp == 8 or par.Pov.eval()) else 0.0
    S['povm'] += (povt - S['povm']) * min(1.0, dt * 2.2)
    povm = S['povm']

    E = {'bass': bass, 'high': high, 'energy': energy, 'kickenv': kickenv,
         'dropenv': dropenv, 'psi': (0.7071, 0.7071), 'bp': bp}
    E['dead'] = _ss(0.6, 2.2, S['since']) * S['catup'] if cp == 1 else 0.0
    if cp == 0:
        E['psi'] = (1.0, 0.0)
    elif cp == 1:
        lie = _ss(0.6, 2.2, S['since'])
        E['psi'] = (math.sqrt(1.0 - lie) * 0.7071, math.sqrt(0.5 + 0.5 * lie))
    parts = []
    face = (0.0, 0.0)

    # --- the observer's view --------------------------------------------------
    if povm < 0.999:
        ca = 1.0 - povm
        cam_t = list(CAMS.get(cp, CAMS[-1]))
        if cp == 6:
            wd1 = max(0.0, S['wd'] - 1.0)
            cam_t[0] += 0.24 * wd1
            cam_t[1] += 0.95 * wd1
        cam_t[1] *= 1.0 - DOLLY * S['catup']
        cam_t[0] += 0.12 * S['catup']
        cs = S['cam']
        for i in range(4):
            cs[i] += (cam_t[i] - cs[i]) * min(1.0, dt * 1.1)
        ty_, dist, pitch, yamp = cs
        yaw = yamp * (0.55 * math.sin(TAU * t / 53.0) + 0.18 * math.sin(TAU * t / 17.0)) \
            + 0.22 * dropenv * math.sin(t * 2.3)
        dist *= 1.0 - 0.04 * kickenv
        T = (0.0, ty_, 0.0)
        P = (T[0] + dist * math.sin(yaw) * math.cos(pitch), T[1] + dist * math.sin(pitch),
             T[2] + dist * math.cos(yaw) * math.cos(pitch))
        cam = _cam_look(P, (T[0] - P[0], T[1] - P[1], T[2] - P[2]), OBSF)
        R, U = cam[1], cam[2]
        Rh = np.array(_norm3((float(R[0]), 0.0, float(R[2]))))
        Uw = np.array((0.0, 1.0, 0.0))
        rise = 0.27 * S['catup']
        local = _cat_scene(S, cp, t, E)
        cat3 = [_bill(a_, (0.0, -0.5 + rise, 0.0), Rh, Uw, CATSC) for a_ in local if len(a_)]
        # a closed box rattles on the kick: someone is in there
        rows = _box(S['lid'], CBOX, 0.8, 0.14, 0.30)
        _props(rows, t, kickenv, E['dead'], S['decays'], 0.75)
        B3 = _A3(rows)
        rat = kickenv * (1.0 - S['lid']) * 0.05 * (1.0 if S['paw'] else -1.0)
        if abs(rat) > 1e-4:
            c_, s_ = math.cos(rat), math.sin(rat)
            for ix, iy in ((0, 1), (3, 4)):
                x, y = B3[:, ix].copy(), B3[:, iy].copy() + 0.5
                B3[:, ix] = x * c_ - y * s_
                B3[:, iy] = x * s_ + y * c_ - 0.5
        A = _proj(np.vstack(cat3 + [B3]) if cat3 else B3, cam)
        fl = [0.0, 0.72]
        if cp == 5:
            fl[0] = 0.98 * math.sin(S['tph'])
        elif cp == 6:
            fl[1] = 0.9
        elif cp == 4:
            fl[1] = 0.45
        fp = _bill(_A2([(fl[0], fl[1], fl[0], fl[1], 0, 0, 0, 1)]),
                   (0.0, -0.5 + rise, 0.0), Rh, Uw, CATSC)
        fp = _proj(fp, cam)
        if len(fp):
            face = (float(fp[0, 0]), float(fp[0, 1]))
        A[:, 7] *= ca
        parts.append(A)
    # --- the cat's view ----------------------------------------------------------
    if povm > 0.001:
        face = (face[0] * (1.0 - povm), face[1] * (1.0 - povm) + 0.30 * povm)
        A = _pov_frame(S, cp, t, E)
        A[:, 7] *= povm
        parts.append(A)

    A = np.vstack(parts) if parts else np.zeros((0, 8))
    # the reveal flash: everything brighter for a moment
    ink = float(par.Ink.eval()) * (1.0 + 0.6 * S['flash'] + 0.25 * kickenv)
    x0, y0, x1, y1 = A[:, 0], A[:, 1], A[:, 2], A[:, 3]
    dx, dy = x1 - x0, y1 - y0
    ln = np.hypot(dx, dy)
    ok = np.isfinite(ln) & (ln > MINLEN) & (ln < MAXL) & (A[:, 7] > 0.004) & \
        ~((np.minimum(x0, x1) > CULLX) | (np.maximum(x0, x1) < -CULLX) |
          (np.minimum(y0, y1) > CULLY) | (np.maximum(y0, y1) < -CULLY))
    idx = np.nonzero(ok)[0][:MAXSEG]
    n = len(idx)
    out = np.zeros((len(CH), MAXSEG), dtype=np.float64)
    out[4] = 1.0
    out[6] = 1.0
    if n:
        out[0, :n] = (x0[idx] + x1[idx]) * 0.5
        out[1, :n] = (y0[idx] + y1[idx]) * 0.5
        out[3, :n] = np.degrees(np.arctan2(-dx[idx], dy[idx]))
        out[5, :n] = ln[idx]
        out[7, :n] = np.clip(A[idx, 4], 0.0, 4.0)
        out[8, :n] = np.clip(A[idx, 5], 0.0, 4.0)
        out[9, :n] = np.clip(A[idx, 6], 0.0, 4.0)
        out[10, :n] = np.clip(A[idx, 7] * ink, 0.0, 1.0)
    S['lastout'] = out
    _publish(scriptOp, out)

    # the readout
    if cp != S['lastcp']:
        S['lastcp'] = cp
        S['labelt'] = t
    lf = math.exp(-max(0.0, t - S['labelt']) / 4.0)
    if S['rev'] and S['since'] < 4.0:
        lf = max(lf, 1.0 - S['since'] / 4.0)
    title = CHECKPOINTS[cp][1].strip()
    if not S['rev'] or S['lid'] < 0.3:
        sub = '|psi> = 0.71|alive> + 0.71|dead>     [the box is closed]'
    elif cp == 4:
        sub = '|psi> = ( |alive,dead> + |dead,alive> ) / sqrt 2'
    elif cp == 5:
        sub = 'T = 0.55   R = 0.32   the wall is not a wall'
    elif cp == 6:
        sub = 'worlds: %d' % E.get('worlds', 1)
    elif cp == 7:
        sub = 'coherence %.2f' % max(0.0, 1.0 - S['dec'])
    elif cp == 8:
        sub = 'the cat observes the observer'
    else:
        pa, pd = E['psi']
        sub = '|psi> = %.2f|alive> + %.2f|dead>' % (pa, pd)
    if par.Pov.eval() and cp != 8:
        sub += "     [cat's eye view]"
    txt = title + '\n' + sub
    try:
        par.Chapter.val = float(cp)
        par.Segs.val = float(n)
        par.Labelfade.val = lf
        par.Kal.val = kal
        S['face'][0] += (face[0] - S['face'][0]) * min(1.0, dt * 6.0)
        S['face'][1] += (face[1] - S['face'][1]) * min(1.0, dt * 6.0)
        par.Kfx.val = _cl(S['face'][0], -1.2, 1.2)
        par.Kfy.val = _cl(S['face'][1], -0.8, 0.8)
        par.Kalseg.val = S['kseg']
        par.Kalrot.val = S['krot']
        par.Warp.val = warp
        par.Hue.val = S['hue']
        par.Trail.val = min(0.92, 0.22 + 0.68 * S['kalslow'] + 0.08 * energy) * \
            float(par.Trails.eval())
        fr = 1.0 if cp in (2, 3) else (0.55 if cp != 7 else max(0.0, 0.8 - S['dec']))
        par.Fringe.val = fr * (0.4 + 0.6 * (1.0 - S['lid'] * 0.5))
        par.Povm.val = povm
        par.Lid.val = S['lid']
        par.Flash.val = S['flash']
        par.Loops.val = float(S['loops'])
        # a Text TOP re-renders on every change (~6 ms here), and the amplitudes
        # change every frame: redraw it at most five times a second
        if txt != S['labtxt'] and (txt.split('\n')[0] != S['labtxt'].split('\n')[0]
                                   or abs(raw - S['labtick']) > 0.2):
            S['labtxt'] = txt
            S['labtick'] = raw
            par.Scaletxt.val = txt
    except Exception:
        pass
    S['census'] = ('state %d u %.2f | lid %.2f | pov %.2f | kal %.2f | lines %d/%d'
                   % (cp, u, S['lid'], povm, kal, n, MAXSEG))
    return


def _publish(scriptOp, outc):
    # copyNumpyArray is a memcpy.
    # NEVER clear() AND RE-APPEND CHANNELS EVERY FRAME. On 2025.33230 a Script
    # CHOP that does leaks native memory inside TouchDesigner — measured 2-5 MB a
    # minute on a 12k-sample publish. Build the channels once; after that only
    # write values. (numChans cannot be read from inside a cook, so whether they
    # exist is tracked here; if a write ever fails they are rebuilt and retried.)
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
                print('[superposition engine] frame failed:\n' + S['lasterr'])
            prev = S.get('lastout')
        else:
            prev = None
        if prev is None:
            raise
        _publish(scriptOp, prev)
    return
'''

eng_src = C(textDAT, 'engine_src', 1780, 980)
eng_src.text = hdr(
    CHECKPOINTS=CHECKPOINTS, MAXSEG=MAXSEG, SEED0=20260926, STORYDEF=STORYDEF,
    CH=('tx', 'ty', 'tz', 'rz', 'sx', 'sy', 'sz', 'r', 'g', 'b', 'a'),
    # the palette: alive is warm, dead is cold, the superposition is the violet
    # between them, and the observer is white. The box and its machinery are bone
    # and a sick green.
    CALIVE=(1.00, 0.70, 0.32), CDEAD=(0.42, 0.74, 1.00), CSUPER=(0.92, 0.42, 1.00),
    CWAVE=(0.35, 1.00, 0.88), CEYE=(1.00, 0.96, 0.90), CBOX=(0.70, 0.72, 0.86),
    CPROP=(0.55, 0.95, 0.62), CATOM=(0.62, 1.00, 0.80),
    # cameras. Observer: per state (target y, distance, pitch, yaw amplitude).
    CAMS={-1: (0.08, 3.25, 0.36, 1.0), 4: (0.10, 3.45, 0.32, 0.8),
          5: (0.06, 3.70, 0.30, 0.25), 6: (0.25, 3.60, 0.22, 0.6),
          3: (0.30, 3.70, 0.30, 0.9)},
    OBSF=1.95, POVF=1.05, DOLLY=0.20, NEAR=0.03, CATSC=0.85,
    WALL=0.5 / 0.85,
    REVU0=0.08, REVU1=0.24, CLOSEU=0.93,
    DECAYLIFE=0.8, DECAYMAX=12,
    CULLX=1.35, CULLY=0.80, MINLEN=0.0006, MAXL=3.0,
) + ENGINE_BODY

engine = C(scriptCHOP, 'engine', 1940, 980)
engine.par.callbacks = eng_src.name
W(director, engine, 0)


# ---------------------------------------------------------------------------
# GEOMETRY AND RENDER
# ---------------------------------------------------------------------------
SHAPE_BODY = '''# One unit segment along +y, centred. Everything else is instance transform.
# Nothing it reads ever changes, so it cooks once at build and never again.


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
unit_line.par.callbacks = shape_src.name

mat_line = C(lineMAT, 'mat_line', 1600, 200)
soft(mat_line, widthnear=1.5, widthfar=1.5, widthaffectedbyfov=False,
     linenearalpha=1.0, blending=True, depthtest=False, depthwriting=False)
mat_line.par.widthnear.expr = ("max(0.6, parent().par.Linewidth * (1.0 + 0.35 * %s "
                               "+ 0.25 * %s + 0.5 * parent().par.Flash))"
                               % (D('dropenv'), D('kickenv')))
mat_line.par.widthfar.expr = mat_line.par.widthnear.expr

g_lines = C(geometryCOMP, 'geo_lines', 1780, 200)
for _stale in list(g_lines.children):
    _stale.destroy()
_sel = g_lines.create(selectSOP, 'shape')
_sel.par.sop = '../' + unit_line.name
_sel.render = True
_sel.display = True
g_lines.par.material = mat_line.name
g_lines.par.instancing = True
g_lines.par.instanceop = engine.name
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
render_lines.par.camera = cam.name
render_lines.par.geometry = g_lines.name
render_lines.par.bgcolora = 0.0
AA = menu_pick(render_lines.par.antialias, 'aa4', 'aa2')

# --- trails: the lines leave an after-image, long on a drop -------------------
trail_fb = C(feedbackTOP, 'trail_fb', 2100, 120)
res(trail_fb)
W(render_lines, trail_fb)
trail = C(glslTOP, 'trail', 2260, 200)
res(trail)
trail_pix = C(textDAT, 'trail_pixel', 2260, 130)
trail_pix.text = '''// After-images. The previous frame, turned and zoomed a touch, decayed, and
// max'ed under the new lines — max, not add, so it can never wash to white.
uniform vec4 uT;   // x decay, y zoom, z turn, w aspect
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec4 cur = texture(sTD2DInputs[0], uv);
    vec2 p = (uv - 0.5) * vec2(uT.w, 1.0);
    float c = cos(uT.z), s = sin(uT.z);
    p = mat2(c, -s, s, c) * p / uT.y;
    vec4 fb = texture(sTD2DInputs[1], p / vec2(uT.w, 1.0) + 0.5);
    fragColor = TDOutputSwizzle(max(cur, fb * uT.x));
}
'''
trail.par.pixeldat = trail_pix.name
W(render_lines, trail, 0)
W(trail_fb, trail, 1)
trail.par.vec = 1
trail.par.vec0name = 'uT'
trail.par.vec0valuex.expr = 'parent().par.Trail'
trail.par.vec0valuey.expr = '1.0 + 0.012 * parent().par.Kal'
trail.par.vec0valuez.expr = '0.006 * parent().par.Kal'
trail.par.vec0valuew = ASPECT
trail_fb.par.top = trail.name

# --- the void: interference fringes and a probability cloud -------------------
void = C(glslTOP, 'void', 1940, 440)
res(void)
void_pix = C(textDAT, 'void_pixel', 1940, 370)
void_pix.text = '''// The dark the box sits in. Deep violet-black, a probability cloud behind the box
// that breathes on the bass, and faint double-slit fringes across the whole frame
// — strongest while the state is still a superposition, gone when it decoheres.
uniform vec4 uP;   // x energy, y kickenv, z vignette, w story time
uniform vec4 uQ;   // x dropenv, y fringe, z bass, w pov
uniform vec4 uR;   // x high, y hue, z lid, w unused
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

void main() {
    vec2 uv = vUV.st;
    vec2 d = (uv - 0.5) * vec2(1.7778, 1.0);
    float t = uP.w;
    vec3 col = mix(vec3(0.008, 0.006, 0.020), vec3(0.018, 0.010, 0.034), uv.y);
    float g = fbm(d * 2.6 + vec2(t * 0.013, -t * 0.009));
    col *= 0.55 + 0.9 * g;

    // the probability cloud
    vec2 c = d - vec2(0.0, 0.02);
    float r2 = dot(c, c);
    col += vec3(0.060, 0.028, 0.090) * exp(-r2 * 7.0) * (0.35 + 0.7 * uQ.z + 0.6 * uQ.x)
           * (1.0 - 0.6 * uQ.w);

    // double-slit fringes: cos^2 under a sinc^2-ish envelope, drifting slowly
    float x = d.x;
    float envx = exp(-x * x * 2.2);
    float fr = pow(cos(x * 34.0 + sin(t * 0.21) * 2.0), 2.0) * envx;
    float fr2 = pow(cos(x * 11.0 - t * 0.1), 2.0);
    float band = 0.35 + 0.65 * smoothstep(0.60, 0.0, abs(d.y));
    col += vec3(0.070, 0.050, 0.120) * fr * fr2 * band * uQ.y * (0.45 + 0.9 * uR.x);

    // the cat's view is darker: he is in a box
    col *= mix(1.0, 0.45, uQ.w);

    col += (hash(uv * vec2(1920.0, 1080.0) + fract(t)) - 0.5) * 0.006;
    col *= 1.0 - uP.z * 0.85 * dot(d, d);
    fragColor = TDOutputSwizzle(vec4(max(col, vec3(0.0)), 1.0));
}
'''
void.par.pixeldat = void_pix.name
void.par.vec = 3
void.par.vec0name = 'uP'
void.par.vec0valuex.expr = D('energy')
void.par.vec0valuey.expr = D('kickenv')
void.par.vec0valuez.expr = 'parent().par.Vignette'
void.par.vec0valuew.expr = D('show')
void.par.vec1name = 'uQ'
void.par.vec1valuex.expr = D('dropenv')
void.par.vec1valuey.expr = 'parent().par.Fringe * parent().par.Fringes'
void.par.vec1valuez.expr = D('bass')
void.par.vec1valuew.expr = 'parent().par.Povm'
void.par.vec2name = 'uR'
void.par.vec2valuex.expr = D('high')
void.par.vec2valuey.expr = 'parent().par.Hue'
void.par.vec2valuez.expr = 'parent().par.Lid'

comp = C(compositeTOP, 'comp_scene', 2420, 440, operand='over')
res(comp)
W(trail, comp, 0)
W(void, comp, 1)

glow_cut = C(levelTOP, 'glow_cut', 2420, 320)
soft(glow_cut, blacklevel=0.22, gamma1=1.20)
W(comp, glow_cut)
glow_blur = C(blurTOP, 'glow_blur', 2580, 320, size=12.0)
res(glow_blur, OUTW // 2, OUTH // 2)
glow_blur.par.size.expr = "12.0 + 22.0 * %s" % D('dropenv')
W(glow_cut, glow_blur)
glow_lvl = C(levelTOP, 'glow_lvl', 2740, 320)
glow_lvl.par.opacity.expr = (
    "0.50 * parent().par.Glow * (0.45 + 0.25 * %s + 0.35 * %s + 0.6 * %s "
    "+ 0.5 * parent().par.Flash)" % (D('energy'), D('kickenv'), D('dropenv')))
W(glow_blur, glow_lvl)
comp_glow = C(compositeTOP, 'comp_glow', 2580, 440, operand='add')
res(comp_glow)
W(comp, comp_glow, 0)
W(glow_lvl, comp_glow, 1)

# --- the hallucination: kaleidoscope, swirl, ripple, hue -----------------------
kal = C(glslTOP, 'kaleido', 2740, 440)
res(kal)
kal_pix = C(textDAT, 'kaleido_pixel', 2740, 370)
kal_pix.text = '''// The hallucination. The frame is folded into N mirrored wedges around the
// cat's face (or the observer's eye), swirled by a ripple that runs outward, and hue-turned; that folded
// image is crossfaded over the plain one by uK.x. A kick throws a short one, a
// drop floods the frame with it, and the box opening is always one.
// At uK.x = 0 this is an exact passthrough, which is where it spends most of its life.
uniform vec4 uK;   // x amount, y wedges, z turn, w warp
uniform vec4 uH;   // x story time, y aspect, z hue, w chroma
uniform vec4 uC;   // xy the fold centre (the cat's face) in aspect units
out vec4 fragColor;

vec2 fold(vec2 p, float n, float turn) {
    float r = length(p);
    float a = atan(p.y, p.x) + turn;
    float w = 6.2831853 / n;
    a = mod(a, w);
    a = abs(a - 0.5 * w);
    return vec2(cos(a), sin(a)) * r;
}

vec2 touv(vec2 p) {
    vec2 uv = p / vec2(uH.y, 1.0) + 0.5;
    return 1.0 - abs(1.0 - mod(uv, 2.0));      // mirrored repeat
}

vec3 hue(vec3 c, float h) {
    const mat3 toYIQ = mat3(0.299, 0.596, 0.211, 0.587, -0.274, -0.523, 0.114, -0.322, 0.312);
    const mat3 toRGB = mat3(1.0, 1.0, 1.0, 0.956, -0.272, -1.106, 0.621, -0.647, 1.703);
    vec3 y = toYIQ * c;
    float a = h * 6.2831853;
    float cs = cos(a), sn = sin(a);
    y.yz = mat2(cs, sn, -sn, cs) * y.yz;
    return toRGB * y;
}

void main() {
    vec2 uv = vUV.st;
    vec4 base = texture(sTD2DInputs[0], uv);
    float amt = clamp(uK.x, 0.0, 1.5);
    if (amt < 0.002) {
        fragColor = TDOutputSwizzle(base);
        return;
    }
    float t = uH.x;
    vec2 p = (uv - 0.5) * vec2(uH.y, 1.0);
    float r = length(p - uC.xy);
    // swirl and ripple, both running outward from the middle
    float sw = uK.w * 0.55 * sin(r * 8.0 - t * 3.0);
    float c = cos(sw), s = sin(sw);
    p = uC.xy + mat2(c, -s, s, c) * (p - uC.xy) * (1.0 + 0.07 * uK.w * sin(r * 15.0 - t * 5.0));
    vec2 q = fold(p - uC.xy, uK.y, uK.z) * (0.92 - 0.10 * min(amt, 1.0)) + uC.xy;
    // chromatic split along the radius
    vec2 dq = normalize(q + 1e-5) * uH.w * min(amt, 1.0);
    vec3 k;
    k.r = texture(sTD2DInputs[0], touv(q + dq)).r;
    k.g = texture(sTD2DInputs[0], touv(q)).g;
    k.b = texture(sTD2DInputs[0], touv(q - dq)).b;
    k = max(hue(k, uH.z * min(amt, 1.0)), vec3(0.0));
    vec3 col = mix(base.rgb, max(k, base.rgb * 0.6), clamp(amt * 1.3, 0.0, 1.0));
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
'''
kal.par.pixeldat = kal_pix.name
W(comp_glow, kal)
kal.par.vec0name = 'uK'
kal.par.vec0valuex.expr = 'parent().par.Kal'
kal.par.vec0valuey.expr = 'parent().par.Kalseg'
kal.par.vec0valuez.expr = 'parent().par.Kalrot'
kal.par.vec0valuew.expr = 'parent().par.Warp'
kal.par.vec1name = 'uH'
kal.par.vec1valuex.expr = D('show')
kal.par.vec1valuey = ASPECT
kal.par.vec1valuez.expr = 'parent().par.Hue'
kal.par.vec1valuew.expr = '0.004 + 0.010 * %s' % D('dropenv')
kal.par.vec = 3
kal.par.vec2name = 'uC'
# screen world units -> the shader's aspect units: both axes divide by the ortho height
kal.par.vec2valuex.expr = 'parent().par.Kfx / %f' % ORTHOH
kal.par.vec2valuey.expr = 'parent().par.Kfy / %f' % (ORTHOH)

label = C(textTOP, 'label', 2420, 620)
res(label, OUTW, OUTH, 'rgba8fixed')
soft(label, alignx='left', aligny='top', fontsizex=20, font='Courier New',
     bgalpha=0.0, fontcolorr=0.92, fontcolorg=0.86, fontcolorb=1.0,
     fontcolora=1.0, wordwrap=False, trackingx=0.12,
     positionx=0.035, positiony=-0.065, positionunit='fraction')
label.par.text.expr = 'parent().par.Scaletxt.eval()'
label_lvl = C(levelTOP, 'label_lvl', 2580, 620)
label_lvl.par.opacity.expr = (
    "parent().par.Label * (0.22 + 0.78 * parent().par.Labelfade)")
W(label, label_lvl)
comp_label = C(compositeTOP, 'comp_label', 2900, 440, operand='over')
res(comp_label)
W(label_lvl, comp_label, 0)
W(kal, comp_label, 1)

grade = C(levelTOP, 'grade', 3060, 440)
soft(grade, gamma1=0.95, contrast=1.05, blacklevel=0.0, brightness1=1.0)
soft(grade, clamp=True, clamplow2=0.0, clamphigh2=4.0)
W(comp_label, grade)

final_out = C(nullTOP, 'final_out', 3220, 440)
W(grade, final_out)
out1 = C(outTOP, 'out1', 3380, 440)
W(final_out, out1)

pout = proj.create(outTOP, SCENE + '_out')
pout.nodeX, pout.nodeY = 400, -4400
s.outputConnectors[0].connect(pout.inputConnectors[0])


# ---------------------------------------------------------------------------
# PADS AND KEYS
# ---------------------------------------------------------------------------
PEXEC_BODY = '''# A state is a SEEK (see bayou): show = musical clock - Timeoffset, so jumping is
# one parameter write and the story plays on from there. The verbs do not seek:
# they go into the engine's queue and act wherever the story is.


def _seek(comp, seconds):
    d = comp.op('director')
    mus = float(d['musical'][0]) if d is not None and d.numChans else 0.0
    comp.par.Timeoffset = mus - max(0.02, seconds)


def _index(comp):
    return int(round(float(comp.par.Chapter.eval())))


def _push(comp, what):
    q = comp.fetch('qverbs', None)
    if not isinstance(q, list):
        q = []
    q.append(what)
    del q[:-16]
    comp.store('qverbs', q)


def onPulse(par):
    comp = par.owner
    n = par.name
    slen = max(1.0, float(comp.par.Storylen.eval()))
    names = [c[0] for c in CHECKPOINTS]
    if n == 'Observe':
        _push(comp, 'observe')
    elif n == 'Trip':
        _push(comp, 'trip')
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
pexec.par.op = '..'
soft(pexec, pars='Observe Trip Reseed Restart Nextcp Prevcp '
     + ' '.join('Go' + cp[0] for cp in CHECKPOINTS),
     valuechange=False, onpulse=True)

KEY_BODY = '''# 1-9 jump to a state; 0 starts again.
#   o  OBSERVE — open the box now; once open, collapse the state again
#   v  POV     — the cat's point of view, in whatever state it is in
#   k  TRIP    — a kaleidoscopic hallucination, now
#   m  HOLD    — keep the kaleidoscope turning
#   n  RESEED  — new worlds, new scatter


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
    elif k == 'o':
        comp.par.Observe.pulse()
    elif k == 'v':
        comp.par.Pov = not comp.par.Pov.eval()
    elif k == 'k':
        comp.par.Trip.pulse()
    elif k == 'm':
        comp.par.Kaleidolock = not comp.par.Kaleidolock.eval()
    elif k == 'n':
        comp.par.Reseed.pulse()
    return


def onShortcut(dat, shortcutName, time):
    return
'''
keyin = C(keyboardinDAT, 'key_pad', 1780, 700)
keyin.par.keys = '1 2 3 4 5 6 7 8 9 0 o v k m n'
kcb = keyin.par.callbacks.eval()
if kcb is None:
    kcb = C(textDAT, 'key_pad_callbacks', 1780, 620)
    keyin.par.callbacks = kcb.name
kcb.nodeX, kcb.nodeY = 1780, 620
kcb.text = hdr(CHECKPOINTS=CHECKPOINTS) + KEY_BODY

# NO executeDAT KEEP-ALIVE (see bayou): pull-based, so unselected on a switch it
# costs one Audio Device In tick and its clock resumes where it left off.

s.par.display = True
s.par.opviewer = final_out.name
# the panel shows the output, so the COMP's node viewer (and a panel/perform view of
# it) actually pulls the chain; with nothing pulling it, it does not cook at all
s.par.top = final_out.name
s.store('pending', [])
s.store('qverbs', [])

timer.par.initialize.pulse()
timer.par.start.pulse()
director.cook(force=True)
engine.cook(force=True)

for _got, _want, _what in (
        (cam.par.projection.eval(), 'ortho', 'camera projection'),
        (g_lines.par.instancecolormode.eval(), 'replace', 'instance colour mode'),
        (comp.par.operand.eval(), 'over', 'scene composite operand'),
        (comp_glow.par.operand.eval(), 'add', 'glow composite operand')):
    if _got != _want:
        print('  [CHECK FAILED] %s is %r, expected %r' % (_what, _got, _want))

print('built %s' % s.path)
print('  %s' % eng_src.module._S['S']['census'])
