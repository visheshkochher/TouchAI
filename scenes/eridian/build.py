# Eridian — Project Hail Mary, seen the way Rocky sees: by sound.
#
# Rocky is an Eridian engineer: eyeless, five-legged, a carapace like rough rock, three
# fingers to each hand. He navigates by echolocation and speaks in musical chords, and
# his ship, the Blip-A, is built of xenonite; in the film its interior is strung with
# long strings and prism-like plates that are its musical instruments.
#
# SO THE WORLD IS DARK UNTIL SOUND REVEALS IT. Every kick is a sonar ping from Rocky: a
# wavefront expands through the line-drawn structure and lights it only as it passes,
# then the dark closes behind it. Between pings the world is a faint ghost. That is the
# look, and it is also what keeps the frame dim enough for a club's LED wall — on top
# of which an automatic limiter holds the frame's average brightness under a cap, and a
# soft ceiling takes the peaks. There are no white flashes anywhere.
#
# THE MUSIC IS PLAYED ON THE SHIP. The strings of the Blip-A are each tuned to a band of
# the spectrum: a chord in the track is a chord on the strings. Rocky answers in
# chords too — glyphs built from the spectrum's loudest bands rise from his carapace.
#
# FIVE VIEWS, one set: the Strings (inside the Blip-A), Rocky, the Blip-A from outside,
# the Tunnel (the xenonite wall between the two ships), and the Petrova Line
# (Astrophage flowing from Tau Ceti). They crossfade over four beats and are re-chosen
# at random on phrase boundaries and on drops; a breakdown is detected and the pings
# stop while he keeps watch.
#
# EVERYTHING IS A LINE: one instanced unit segment, fed by one numpy engine that does
# its own 3D and projection.
#
# BUILT TO RUN ALL NIGHT: Script CHOP channels are built once and then only written;
# every list is capped and aged; every phase wraps; shaders get a wrapped clock.
#
# Idempotent: destroys and recreates /project1/eridian and its project-level Out TOP,
# and touches nothing else. No media files.
#     code = open('scenes/eridian/build.py', encoding='utf-8').read()
#     g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
#
# GENERATED: this file is eridian_template.py + verbatim blocks of
# scenes/homestead/build.py (BEGIN/END HOMESTEAD), assembled by gen_eridian.py.

import math
import os

SCENE = 'eridian'
OUTW, OUTH = 1280, 720
ASPECT = OUTW / OUTH
ORTHOW = 2.0
ORTHOH = ORTHOW / ASPECT
CLOCKLEN = 60.0
STORYDEF = 600.0          # the director needs a clock length; this piece has no story
MAXSEG = 14000
NBANDS = 16

VIEWS = ('STRINGS', 'ROCKY', 'BLIP-A', 'TUNNEL', 'PETROVA')
VIEWTITLES = ('the strings', 'rocky', 'blip-a', 'the tunnel', 'the petrova line')

proj = op('/project1')
for stale in (SCENE, SCENE + '_out'):
    o = proj.op(stale)
    if o:
        o.destroy()

s = proj.create(containerCOMP, SCENE)
s.nodeX, s.nodeY = 0, -5600
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
pg = s.appendCustomPage('Eridian')
pg.appendMenu('Audiosrc', label='Audio Source')
s.par.Audiosrc.menuNames = ['device', 'file']
s.par.Audiosrc.menuLabels = ['Audio Device In', 'Audio File In (test)']
s.par.Audiosrc = 'file'

for nm, label, val, lo, hi in [
    ('Reactivity', 'Reactivity',          1.0, 0.0, 3.0),
    ('Devgain',    'Device In Gain',      6.0, 1.0, 30.0),
    ('Storylen',   'Clock Length (s)', STORYDEF, 60.0, 2400.0),
    ('Refbpm',     'Reference BPM',     126.0, 60.0, 200.0),
    ('Beatdrive',  'Beat Drive',          1.0, 0.0, 1.0),
    ('Timeoffset', 'Time Offset (s)',     0.0, -600.0, 3000.0),
    ('Changeprob', 'View Change Chance per Phrase', 0.5, 0.0, 1.0),
    ('Phrase',     'Phrase Length (beats)', 32.0, 8.0, 128.0),
    ('Brightness', 'Master Brightness',   0.80, 0.1, 1.5),
    ('Aplmax',     'Average Brightness Cap', 0.055, 0.01, 0.3),
    ('Ceiling',    'Peak Ceiling',        0.75, 0.2, 1.0),
    ('Ghost',      'Unlit World (between pings)', 0.20, 0.0, 0.6),
    ('Linewidth',  'Line Width (px)',     1.25, 0.5, 4.0),
    ('Glow',       'Glow',                0.7, 0.0, 2.0),
    ('Trails',     'Trails',              1.0, 0.0, 1.3),
    ('Label',      'Readout',             0.55, 0.0, 1.0),
    ('Vignette',   'Vignette',            0.9, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

_RO = [('Bpm', 0, 200), ('Showt', 0, 2400), ('View', 0, len(VIEWS)), ('Beat', 0, 1e9),
       ('Segs', 0, MAXSEG), ('Trail', 0, 1), ('Brk', 0, 1), ('Tclk', 0, 1000),
       ('Labelfade', 0, 1), ('Ping', 0, 1), ('Bgr', 0, 1), ('Bgg', 0, 1), ('Bgb', 0, 1),
       ('Bassm', 0, 1), ('Highm', 0, 1), ('Energym', 0, 1)]
for _mn, _lo, _hi in _RO:
    pg.appendFloat(_mn, label=_mn)
    _p = getattr(s.par, _mn)
    _p.normMin, _p.normMax = _lo, _hi
    _p.readOnly = True

pg.appendToggle('Loop', label='Loop the Clock')
s.par.Loop.default = True
s.par.Loop.val = True
pg.appendToggle('Hold', label='H - HOLD THE VIEW (no automatic changes)')
s.par.Hold.val = False
pg.appendStr('Scaletxt', label='Readout')
s.par.Scaletxt.readOnly = True
s.par.Scaletxt.val = ''

for i, nm in enumerate(VIEWS):
    pg.appendPulse('View%d' % (i + 1), label='%d - %s' % (i + 1, nm))
pg.appendPulse('Auto', label='0 - AUTOMATIC')
pg.appendPulse('Ping3', label='S - SONAR (three pings)')
pg.appendPulse('Amaze', label='A - AMAZE')
pg.appendPulse('Bump', label='F - FIST MY BUMP (the tunnel)')
pg.appendPulse('Chord', label='C - ROCKY SPEAKS (a chord)')
pg.appendPulse('Reseed', label='N - RESEED')

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

# the spectrum, for the strings and for Rocky's chords: NBANDS log-spaced bands,
# smoothed in the engine (a lag CHOP would smooth along frequency, not time)
spec = C(audiospectrumCHOP, 'audio_spectrum', 660, 1580)
menu_pick(spec.par.fftsize, '2048', '1024')
soft(spec, frequencylog=1.0, highfreqboost=0.9)
menu_pick(spec.par.outputmenu, 'setmanually')
spec.par.outlength = NBANDS
W(gain, spec)
null_spec = C(nullCHOP, 'spectrum', 820, 1580)
W(spec, null_spec)

# ---------------------------------------------------------------------------
# DIRECTOR — verbatim from homestead: the envelopes and the event counters. Its
# playhead and its verb queue are unused here (verbs go through 'qverbs').
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
ENGINE_BODY = r'''# Everything is a line segment in 3D, carrying a colour class, an alpha, and a SONAR
# WEIGHT: how much it depends on being pinged to be seen. Each view builds its world
# and its camera; then one pipeline lights it:
#
#   alpha = a * ((1 - sw) + sw * (ghost + (1 - ghost) * reveal))
#   reveal = sum over live pings of exp(-((|mid - origin| - v * age) / w)^2) * fade(age)
#
# so a ping is a shell expanding from Rocky through the world, and anything with sw = 1
# exists only while a shell passes over it. Then camera, near clip, perspective.
import math
import random
import numpy as np

_S = {'S': None}
_PUB = {'built': False}
TAU = 2.0 * math.pi
NV = len(VIEWS)


def _hs(a):
    x = np.sin(a * 12.9898 + 78.233) * 43758.5453
    return x - np.floor(x)


def _h1(a):
    x = math.sin(a * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


def _cl(x, lo=0.0, hi=1.0):
    return min(hi, max(lo, x))


def _chan(inp, name, default=0.0):
    try:
        return float(inp[name][0])
    except Exception:
        return default


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


# --- the bag: rows of (x0, y0, z0, x1, y1, z1, cls, a, sw) ----------------------------
class Bag(object):
    def __init__(self):
        self.rows = []
        self.chunks = []

    def L(self, p, q, cls, a, sw):
        self.rows.append((p[0], p[1], p[2], q[0], q[1], q[2], cls, a, sw))

    def P(self, pts, cls, a, sw, closed=False):
        n = len(pts)
        for i in range(n if closed else n - 1):
            self.L(pts[i], pts[(i + 1) % n], cls, a, sw)

    def ring(self, c, e1, e2, r, n, rot, cls, a, sw, closed=True, span=TAU):
        pts = []
        m = n if closed else n + 1
        step = (TAU if closed else span) / n
        for i in range(m):
            an = rot + i * step
            ca, sa = math.cos(an) * r, math.sin(an) * r
            pts.append((c[0] + e1[0] * ca + e2[0] * sa, c[1] + e1[1] * ca + e2[1] * sa,
                        c[2] + e1[2] * ca + e2[2] * sa))
        self.P(pts, cls, a, sw, closed)

    def arr(self, A, cls, a, sw):
        n = len(A)
        if n:
            self.chunks.append(np.column_stack([A, np.broadcast_to(cls, (n,)).astype(float),
                                                np.broadcast_to(a, (n,)).astype(float),
                                                np.broadcast_to(sw, (n,)).astype(float)]))

    def done(self):
        parts = list(self.chunks)
        if self.rows:
            parts.append(np.array(self.rows, dtype=np.float64))
        if not parts:
            return np.zeros((0, 9))
        return np.vstack(parts)


def _polyseg(X, Y, Z):
    """(n, m) point grids -> (n * (m - 1), 6) segments along the second axis."""
    return np.stack([X[:, :-1], Y[:, :-1], Z[:, :-1], X[:, 1:], Y[:, 1:], Z[:, 1:]],
                    axis=2).reshape(-1, 6)


# --- cameras ------------------------------------------------------------------------------
def _norm3(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _cam(P, T, f, roll=0.0):
    F = _norm3((T[0] - P[0], T[1] - P[1], T[2] - P[2]))
    R = _norm3(_cross(F, (0.0, 1.0, 0.0)))
    U = _cross(R, F)
    if roll:
        c, s_ = math.cos(roll), math.sin(roll)
        R, U = (tuple(R[i] * c + U[i] * s_ for i in range(3)),
                tuple(-R[i] * s_ + U[i] * c for i in range(3)))
    return (np.array(P), np.array(R), np.array(U), np.array(F), f)


# --- Rocky ----------------------------------------------------------------------------------
# A carapace of rough rock — a low five-sided dome of facets, a crack or two, three vent
# slits on top that breathe — and five legs, each two segments drawn double for mass,
# a knuckle ring at the knee, and a hand of three fingers.
def _rocky(bag, pos, yaw, s, t, lifts, E, S, sw=0.55, a=1.0, hand=None, curl=0.0):
    x0, y0, z0 = pos
    base = y0 + (0.30 - 0.14 * curl) * s + 0.05 * s * E['kickenv'] + 0.32 * s * S['jump']
    tw = 0.10 * math.sin(t * 0.9) + 0.08 * S['jump']
    ang = [yaw + tw + i * TAU / 5.0 for i in range(5)]
    jit = [1.0 + 0.12 * (_h1(i * 3.1 + 7.0) - 0.5) for i in range(5)]

    def ringp(r, y, off=0.0):
        return [(x0 + math.cos(an + off) * r * j, y, z0 + math.sin(an + off) * r * j)
                for an, j in zip(ang, jit)]
    bot = ringp(0.40 * s, base)
    rim = ringp(0.64 * s, base + 0.15 * s)
    top = ringp(0.44 * s, base + 0.34 * s, 0.25)
    peak = (x0, base + 0.44 * s, z0)
    bag.P(bot, 2, a * 0.7, sw, True)
    bag.P(rim, 2, a, sw, True)
    bag.P(top, 2, a, sw, True)
    for i in range(5):
        j = (i + 1) % 5
        bag.L(bot[i], rim[i], 2, a * 0.8, sw)
        bag.L(rim[i], top[i], 2, a * 0.9, sw)
        bag.L(rim[j], top[i], 2, a * 0.6, sw)
        bag.L(bot[i], rim[j], 2, a * 0.45, sw)
        bag.L(top[i], peak, 2, a * 0.55, sw)
        # a crack across the rim face
        m0 = [(rim[i][k] * 0.6 + top[i][k] * 0.4) for k in range(3)]
        m1 = [(rim[j][k] * 0.55 + bot[j][k] * 0.45) for k in range(3)]
        mid = [(m0[k] + m1[k]) * 0.5 + (0.03 * s if k == 1 else 0.0) for k in range(3)]
        bag.P([m0, mid, m1], 2, a * 0.35, sw)
    # the vents: three slits that open with the bass
    op_ = 0.012 * s + 0.035 * s * E['bass'] + 0.02 * s * S['voice']
    for k in range(3):
        an = yaw + k * TAU / 3.0 + 0.4
        cx, cz = x0 + math.cos(an) * 0.12 * s, z0 + math.sin(an) * 0.12 * s
        dx, dz = -math.sin(an) * 0.07 * s, math.cos(an) * 0.07 * s
        nx, nz = math.cos(an) * op_, math.sin(an) * op_
        yv = base + 0.40 * s
        bag.L((cx - dx + nx, yv, cz - dz + nz), (cx + dx + nx, yv, cz + dz + nz), 2, a, sw)
        bag.L((cx - dx - nx, yv, cz - dz - nz), (cx + dx - nx, yv, cz + dz - nz), 2, a, sw)
    # legs
    for i in range(5):
        an = ang[i]
        dx, dz = math.cos(an), math.sin(an)
        hip = rim[i]
        lift = lifts[i]
        reach = (1.00 - 0.40 * curl - 0.15 * lift + 0.2 * S['jump']) * s
        knee = (x0 + dx * (0.88 - 0.25 * curl) * s, base + (0.46 + 0.25 * lift - 0.3 * curl) * s,
                z0 + dz * (0.88 - 0.25 * curl) * s)
        foot = (x0 + dx * reach, y0 + 0.38 * s * lift + 0.05 * s * curl, z0 + dz * reach)
        if hand is not None and i == 0:
            foot = hand
        ox, oz = -dz * 0.055 * s, dx * 0.055 * s
        for sg in (-1.0, 1.0):
            bag.L((hip[0] + ox * sg, hip[1], hip[2] + oz * sg),
                  (knee[0] + ox * sg, knee[1], knee[2] + oz * sg), 2, a * 0.9, sw)
            bag.L((knee[0] + ox * sg * 0.8, knee[1], knee[2] + oz * sg * 0.8),
                  (foot[0] + ox * sg * 0.5, foot[1], foot[2] + oz * sg * 0.5), 2, a * 0.9, sw)
        bag.ring(knee, (1, 0, 0), (0, 0, 1), 0.075 * s, 5, an, 2, a * 0.8, sw)
        bag.ring(hip, (1, 0, 0), (0, 0, 1), 0.06 * s, 5, an, 2, a * 0.6, sw)
        # the hand: three fingers
        fx, fz = (foot[0] - knee[0]), (foot[2] - knee[2])
        fl = math.hypot(fx, fz) or 1.0
        fx, fz = fx / fl, fz / fl
        for fa in (-0.6, 0.0, 0.6):
            c_, s_ = math.cos(fa), math.sin(fa)
            ux, uz = fx * c_ - fz * s_, fx * s_ + fz * c_
            bag.L(foot, (foot[0] + ux * 0.17 * s, foot[1] - 0.02 * s, foot[2] + uz * 0.17 * s),
                  2, a * 0.8, sw)
    return peak


# --- his voice: chord glyphs, billboarded ------------------------------------------------
def _glyphs(bag, S, cam, s):
    R, U = cam[1], cam[2]
    for g in S['glyphs']:
        age, gx, gy, gz, notes = g
        k = age / GLIFE
        a = (1.0 - k) ** 1.3 * 0.85
        c = (gx + U[0] * age * 0.35 * s, gy + U[1] * age * 0.35 * s + 0.2 * s,
             gz + U[2] * age * 0.35 * s)
        for j, nt in enumerate(notes):
            r = (0.16 + 0.07 * j + 0.22 * k) * s
            span = 0.9 + 0.12 * nt
            rot = nt * 0.61 + j * 2.1
            bag.ring(c, tuple(R), tuple(U), r, 8, rot, 5, a, 0.0, closed=False, span=span)
            # a tick for each note's place in the octave
            for q in range(1 + nt % 4):
                an = rot + span + 0.12 * q
                p0 = [c[i] + (R[i] * math.cos(an) + U[i] * math.sin(an)) * r for i in range(3)]
                p1 = [c[i] + (R[i] * math.cos(an) + U[i] * math.sin(an)) * (r + 0.05 * s)
                      for i in range(3)]
                bag.L(p0, p1, 5, a, 0.0)


# --- a string between two points, vibrating ------------------------------------------------
def _strings(bag, P0, P1, lev, harm, t, cls, base_a, sw, npt=11, dirv=(0.0, 1.0, 0.0)):
    """P0, P1: (n, 3) end points; lev: (n,) 0..1; harm: (n,) ints. One standing wave each."""
    n = len(P0)
    if n == 0:
        return
    u = np.linspace(0.0, 1.0, npt)[None, :]
    amp = (0.010 + 0.085 * lev)[:, None]
    om = (17.0 + 2.3 * harm)[:, None]
    disp = amp * np.sin(np.pi * u * harm[:, None]) * np.cos(om * t + np.arange(n)[:, None])
    X = P0[:, 0:1] + (P1[:, 0:1] - P0[:, 0:1]) * u + dirv[0] * disp
    Y = P0[:, 1:2] + (P1[:, 1:2] - P0[:, 1:2]) * u + dirv[1] * disp
    Z = P0[:, 2:3] + (P1[:, 2:3] - P0[:, 2:3]) * u + dirv[2] * disp
    seg = _polyseg(X, Y, Z)
    bag.arr(seg, cls, np.repeat(base_a * (0.22 + 0.78 * lev), npt - 1), sw)


# --- carvings: Eridian pictographs, as unit line sets ------------------------------------
def _carve_set():
    C = []
    # a star with its planets
    g = []
    for k in range(8):
        an = k * TAU / 8
        g.append((0.0, 0.0, math.cos(an) * 0.25, math.sin(an) * 0.25))
    for r in (0.5, 0.8):
        for k in range(12):
            a0, a1 = k * TAU / 12, (k + 1) * TAU / 12
            g.append((math.cos(a0) * r, math.sin(a0) * r, math.cos(a1) * r, math.sin(a1) * r))
    C.append(g)
    # an Eridian: a pentagon with five legs
    g = []
    for k in range(5):
        a0, a1 = k * TAU / 5 + 0.3, (k + 1) * TAU / 5 + 0.3
        g.append((math.cos(a0) * 0.3, math.sin(a0) * 0.3, math.cos(a1) * 0.3, math.sin(a1) * 0.3))
        g.append((math.cos(a0) * 0.3, math.sin(a0) * 0.3, math.cos(a0 + 0.2) * 0.7,
                  math.sin(a0 + 0.2) * 0.7))
        g.append((math.cos(a0 + 0.2) * 0.7, math.sin(a0 + 0.2) * 0.7,
                  math.cos(a0 + 0.1) * 0.95, math.sin(a0 + 0.1) * 0.95 - 0.2))
    C.append(g)
    # a chord written as staves
    g = []
    for k in range(5):
        y = -0.6 + k * 0.3
        g.append((-0.9, y, 0.9, y))
    for k, (x, y) in enumerate(((-0.5, -0.3), (0.0, 0.3), (0.5, 0.0))):
        g.append((x, y, x + 0.12, y + 0.12))
        g.append((x + 0.12, y + 0.12, x, y + 0.24))
        g.append((x, y + 0.24, x - 0.12, y + 0.12))
        g.append((x - 0.12, y + 0.12, x, y))
    C.append(g)
    # the ship: a spine, rings and a bell
    g = [(-0.9, 0.0, 0.9, 0.0)]
    for x in (-0.3, 0.1, 0.5):
        g += [(x, -0.4, x, 0.4)]
    g += [(-0.9, 0.0, -0.6, 0.35), (-0.9, 0.0, -0.6, -0.35), (-0.6, 0.35, -0.6, -0.35)]
    C.append(g)
    # the numbers: base-6 tallies
    g = []
    for k in range(6):
        x = -0.75 + k * 0.3
        g.append((x, -0.5, x, 0.5))
        if k % 2:
            g.append((x - 0.12, -0.2, x + 0.12, 0.2))
    C.append(g)
    return [np.array(c) for c in C]


CARVE = _carve_set()


# --- state ----------------------------------------------------------------------------------
def _new(seed):
    rs = random.Random(seed)
    return {
        'rs': rs, 'seed': rs.random() * 100.0, 'last': {}, 'lastraw': None,
        'bph': 0.0, 'beat': 0, 'view': 1, 'prev': None, 'xf': 1.0, 'holdto': -1,
        'pings': [], 'glyphs': [], 'spec': np.zeros(NBANDS), 'specpk': np.full(NBANDS, 0.02),
        'lev': np.zeros(NBANDS),
        'legs': [0.0] * 5, 'legi': 0, 'jump': 0.0, 'voice': 0.0, 'bump': 0.0,
        'hz_i': 0, 'hz_f': 0.0, 'orb': 0.0, 'orb2': 0.0, 'gait': 0.0, 'roll': 0.0,
        'tau': 0.0, 'clk': 0.0, 'esh': 0.0, 'elo': 0.3, 'quiet': 0.0, 'brk': 0.0,
        'inbrk': False, 'labt': -99.0, 'labtxt': '', 'lastlab': '', 'phrase_txt': '',
        'pingenv': 0.0, 'errs': 0, 'lastout': None, 'census': '', 'stars': None,
        'ship': None,
    }


def _switch(S, n, raw, why=''):
    if n == S['view']:
        return
    S['prev'] = S['view']
    S['view'] = n
    S['xf'] = 0.0
    S['labt'] = raw
    S['phrase_txt'] = VIEWTITLES[n]


def _ping(S, count=1, strength=1.0):
    for k in range(count):
        S['pings'].append([-k * 0.22, strength])
    del S['pings'][:-PINGMAX]
    S['pingenv'] = 1.0


def _speak(S, origin):
    lev = S['lev']
    order = np.argsort(-lev)[:3]
    notes = [int(b) for b in sorted(order)]
    S['glyphs'].append([0.0, origin[0], origin[1], origin[2], notes])
    del S['glyphs'][:-GLYPHMAX]
    S['voice'] = 1.0


# --- the views -----------------------------------------------------------------------------
# Each returns (bag, camera, sonar origin, ping speed, ping width, where Rocky's voice
# comes from).

def _stars(S):
    if S['stars'] is None:
        rs = np.random.RandomState(11)
        v = rs.normal(size=(260, 3))
        v /= np.linalg.norm(v, axis=1)[:, None]
        v *= 60.0
        d = rs.normal(size=(260, 3)) * 0.12
        S['stars'] = (np.column_stack([v, v + d]), rs.uniform(0.2, 1.0, 260))
    return S['stars']


def _view_strings(S, E, t):
    bag = Bag()
    hf = S['hz_f']
    ks = np.arange(-1, NMOD + 1)
    zr = (ks - hf) * MODL
    kab = ((S['hz_i'] + ks) % 4096).astype(np.float64)
    # the hall's cross-section: a wide hexagon
    hexa = [(math.cos(k * TAU / 6.0) * 3.0, math.sin(k * TAU / 6.0) * 2.2) for k in range(6)]
    # ribs and the long edges
    for z, ka in zip(zr, kab):
        pts = [(x, y, z) for x, y in hexa]
        inn = [(x * 0.9, y * 0.9, z) for x, y in hexa]
        bag.P(pts, 0, 0.9, 0.8, True)
        bag.P(inn, 0, 0.5, 0.9, True)
        for p, q in zip(pts, inn):
            bag.L(p, q, 0, 0.6, 0.9)
    for (x, y) in hexa:
        Z = zr
        seg = np.column_stack([np.full(len(Z) - 1, x), np.full(len(Z) - 1, y), Z[:-1],
                               np.full(len(Z) - 1, x), np.full(len(Z) - 1, y), Z[1:]])
        bag.arr(seg, 0, 0.7, 0.9)
    # the strings, a harp around the hall, each tuned to a band
    n = NSTRH
    i = np.arange(n)
    an = (i + 0.5) / n * TAU
    sx, sy = np.cos(an) * 2.35, np.sin(an) * 1.55
    band = (i * 7) % NBANDS
    lev = S['lev'][band]
    harm = 1 + (band % 3)
    for z0, z1 in zip(zr[:-1], zr[1:]):
        P0 = np.column_stack([sx, sy, np.full(n, z0)])
        P1 = np.column_stack([sx, sy, np.full(n, z1)])
        _strings(bag, P0, P1, lev, harm.astype(float), t, 3, 0.9, 0.25, npt=10,
                 dirv=(0.0, 1.0, 0.0))
    # diagonal strings across each module: the bass
    P0, P1 = [], []
    for z0, z1, ka in zip(zr[:-1], zr[1:], kab[:-1]):
        sg = 1.0 if _h1(ka * 1.7 + S['seed']) > 0.5 else -1.0
        P0.append((-2.4 * sg, -1.6, z0))
        P1.append((2.4 * sg, 1.6, z1))
    P0, P1 = np.array(P0), np.array(P1)
    lb = np.full(len(P0), min(1.0, E['bass'] * 1.1))
    _strings(bag, P0, P1, lb, np.ones(len(P0)), t, 3, 0.6, 0.35, npt=14,
             dirv=(0.0, 0.7, 0.0))
    # prisms hanging from the strings, turning; they catch the sonar
    for z, ka in zip(zr[:-1], kab[:-1]):
        for q in range(2):
            h = _h1(ka * 3.3 + q * 7.1 + S['seed'])
            if h > 0.55:
                continue
            j = int(h * 100) % n
            cx, cy, cz = sx[j] * 0.8, sy[j] * 0.8 - 0.35, z + MODL * (0.3 + 0.4 * _h1(ka + q))
            rot = t * 0.4 + h * 9.0
            tri = [(cx + math.cos(rot + k * TAU / 3) * 0.22, cy + 0.25 * (k - 1) * 0.0 +
                    math.sin(k * TAU / 3) * 0.18, cz + math.sin(rot + k * TAU / 3) * 0.22)
                   for k in range(3)]
            tri2 = [(p[0], p[1] - 0.35, p[2]) for p in tri]
            cls = 8 + int(h * 60) % 6
            bag.P(tri, cls, 0.9, 1.0, True)
            bag.P(tri2, cls, 0.9, 1.0, True)
            for p, q2 in zip(tri, tri2):
                bag.L(p, q2, cls, 0.9, 1.0)
            bag.L((sx[j] * 0.95, sy[j] * 0.95, cz), tri[0], 0, 0.4, 1.0)
    # carvings on the four slanted walls, visible only in the sonar
    for z, ka in zip(zr[:-1], kab[:-1]):
        for w in (0, 2, 3, 5):
            h = _h1(ka * 5.9 + w * 1.3 + S['seed'])
            if h > 0.6:
                continue
            gi = int(h * 97) % len(CARVE)
            (xa, ya), (xb, yb) = hexa[w], hexa[(w + 1) % 6]
            cx, cy = (xa + xb) * 0.5 * 0.97, (ya + yb) * 0.5 * 0.97
            ux, uy = (xb - xa), (yb - ya)
            ul = math.hypot(ux, uy)
            ux, uy = ux / ul, uy / ul
            cz = z + MODL * 0.5
            G = CARVE[gi] * 0.55
            p0 = np.column_stack([cx + ux * G[:, 0], cy + uy * G[:, 0], cz + G[:, 1]])
            p1 = np.column_stack([cx + ux * G[:, 2], cy + uy * G[:, 2], cz + G[:, 3]])
            bag.arr(np.column_stack([p0, p1]), 1, 0.9, 1.0)
    # Rocky, walking the floor ahead
    rz = 3.6 + 0.4 * math.sin(t * 0.21)
    rx = 0.5 * math.sin(t * 0.13)
    g = S['gait']
    lifts = [max(0.0, math.sin(g + i * TAU * 2.0 / 5.0)) * 0.55 + S['legs'][i] * 0.5
             for i in range(5)]
    peak = _rocky(bag, (rx, -1.9, rz), -math.pi / 2.0 + 0.2 * math.sin(t * 0.3), 0.75, t,
                  lifts, E, S)
    P = (0.35 * math.sin(t * 0.17), -0.75 + 0.12 * math.sin(t * 0.23), 0.0)
    T = (0.25 * math.sin(t * 0.11) + rx * 0.3, -0.95, 6.0)
    cam = _cam(P, T, 1.05, 0.04 * math.sin(t * 0.19))
    return bag, cam, peak, 9.0, 0.55, peak, (FOGN, FOGD)


def _view_rocky(S, E, t):
    bag = Bag()
    # the floor: pentagons inside pentagons, and the ring of pillars that hold his web
    for r in np.arange(0.8, 4.6, 0.55):
        bag.ring((0.0, 0.0, 0.0), (1, 0, 0), (0, 0, 1), float(r), 5, 0.3, 0, 0.8, 1.0)
    for k in range(10):
        an = k * TAU / 10.0 + 0.3
        bag.L((math.cos(an) * 0.8, 0.0, math.sin(an) * 0.8),
              (math.cos(an) * 4.4, 0.0, math.sin(an) * 4.4), 0, 0.6, 1.0)
    tops = []
    for k in range(10):
        an = k * TAU / 10.0
        px, pz = math.cos(an) * 5.0, math.sin(an) * 5.0
        h = 3.0 + 0.4 * _h1(k * 2.3 + S['seed'])
        for sg in (-1.0, 1.0):
            ox, oz = -math.sin(an) * 0.12 * sg, math.cos(an) * 0.12 * sg
            bag.L((px + ox, 0.0, pz + oz), (px + ox, h, pz + oz), 0, 0.8, 0.9)
        bag.ring((px, h, pz), (1, 0, 0), (0, 0, 1), 0.2, 5, an, 0, 0.8, 0.9)
        for yy in (0.8, 1.9):
            bag.ring((px, yy, pz), (1, 0, 0), (0, 0, 1), 0.16, 5, an, 0, 0.5, 1.0)
        tops.append((px, h, pz))
    # overhead strings between the pillars, and down to the centre
    P0 = np.array(tops)
    P1 = np.array(tops[3:] + tops[:3])
    band = np.arange(10) * 3 % NBANDS
    _strings(bag, P0, P1, S['lev'][band], (1 + band % 3).astype(float), t, 3, 0.85, 0.3,
             npt=12)
    P1c = np.tile([0.0, 4.2, 0.0], (10, 1))
    band2 = (np.arange(10) * 5 + 2) % NBANDS
    _strings(bag, P0, P1c, S['lev'][band2], (1 + band2 % 2).astype(float), t, 3, 0.6, 0.3,
             npt=10)
    # him: every kick lifts the next leg
    lifts = [S['legs'][i] for i in range(5)]
    peak = _rocky(bag, (0.0, 0.0, 0.0), 0.3 * math.sin(t * 0.15), 1.0, t, lifts, E, S, sw=0.45,
                  curl=S['brk'] * 0.8)
    rad = 2.9 + 0.5 * math.sin(t * 0.07)
    orb = S['orb']
    P = (math.cos(orb) * rad, 1.05 + 0.35 * math.sin(t * 0.09), math.sin(orb) * rad)
    cam = _cam(P, (0.0, 0.42, 0.0), 1.15)
    return bag, cam, peak, 4.5, 0.35, peak, (FOGN, FOGD)


def _ship_model():
    bag = Bag()
    # the spine: a hexagonal truss
    xs = np.arange(-6.0, 4.01, 1.0)
    prev = None
    for x in xs:
        ring = [(x, math.cos(k * TAU / 6) * 0.45, math.sin(k * TAU / 6) * 0.45) for k in range(6)]
        bag.P(ring, 0, 0.8, 1.0, True)
        if prev:
            for k in range(6):
                bag.L(prev[k], ring[k], 0, 0.8, 1.0)
                bag.L(prev[k], ring[(k + 1) % 6], 0, 0.4, 1.0)
        prev = ring
    # three rings on stays
    for x, r in ((-2.5, 2.3), (-0.5, 2.7), (1.5, 2.1)):
        bag.ring((x, 0.0, 0.0), (0, 1, 0), (0, 0, 1), r, 24, 0.0, 0, 0.9, 1.0)
        bag.ring((x + 0.25, 0.0, 0.0), (0, 1, 0), (0, 0, 1), r * 0.94, 24, 0.13, 0, 0.5, 1.0)
        for k in range(8):
            an = k * TAU / 8
            bag.L((x, math.cos(an) * 0.45, math.sin(an) * 0.45),
                  (x, math.cos(an) * r, math.sin(an) * r), 0, 0.5, 1.0)
    # the forward hull: a faceted geodesic of xenonite plates
    cx, R = 5.4, 1.7
    lat = [(-0.5 + i / 7.0) * math.pi for i in range(8)]
    for i, la in enumerate(lat):
        pts = []
        for k in range(10):
            lo = k * TAU / 10 + (0.31 if i % 2 else 0.0)
            pts.append((cx + math.sin(la) * R, math.cos(la) * math.cos(lo) * R,
                        math.cos(la) * math.sin(lo) * R))
        if i > 0 and i < 7:
            bag.P(pts, 0, 0.7, 1.0, True)
        if i > 0:
            for k in range(10):
                bag.L(pp[k], pts[k], 0, 0.6, 1.0)
                bag.L(pp[k], pts[(k + 1) % 10] if i % 2 else pts[(k - 1) % 10], 0, 0.35, 1.0)
        pp = pts
    # the drive bell at the stern
    for j, (x, r) in enumerate(((-6.0, 0.6), (-6.6, 1.1), (-7.2, 1.6), (-7.6, 1.85))):
        bag.ring((x, 0.0, 0.0), (0, 1, 0), (0, 0, 1), r, 18, 0.0, 0, 0.8, 1.0)
    for k in range(18):
        an = k * TAU / 18
        bag.P([(x, math.cos(an) * r, math.sin(an) * r)
               for x, r in ((-6.0, 0.6), (-6.6, 1.1), (-7.2, 1.6), (-7.6, 1.85))], 0, 0.5, 1.0)
    # the Hail Mary, docked off to the side, and the xenonite tunnel between them
    hx, hy, hz = 2.0, -3.2, 3.2
    for k in range(6):
        bag.ring((hx - 1.2 + k * 0.5, hy, hz), (0, 1, 0), (0, 0, 1), 0.45, 8, 0.0, 6, 0.8, 1.0)
    for k in range(8):
        an = k * TAU / 8
        bag.L((hx - 1.2, hy + math.cos(an) * 0.45, hz + math.sin(an) * 0.45),
              (hx + 1.3, hy + math.cos(an) * 0.45, hz + math.sin(an) * 0.45), 6, 0.6, 1.0)
    for k in range(9):
        u = k / 8.0
        c = (hx + (0.5 - hx) * u, hy + (0.0 - hy) * u * 0.9, hz + (0.6 - hz) * u)
        bag.ring(c, (1, 0, 0), (0, 1, 0), 0.22, 8, 0.0, 0, 0.6, 1.0)
    return bag.done()


def _view_ship(S, E, t):
    bag = Bag()
    if S['ship'] is None:
        S['ship'] = _ship_model()
    M = S['ship'].copy()
    rl = S['roll']
    c_, s_ = math.cos(rl), math.sin(rl)
    for a0 in (0, 3):
        y, z = M[:, a0 + 1].copy(), M[:, a0 + 2].copy()
        M[:, a0 + 1] = y * c_ - z * s_
        M[:, a0 + 2] = y * s_ + z * c_
    M[:, 8] = 0.7
    bag.chunks.append(M)
    st, tw = _stars(S)
    bag.arr(st, 6, 0.30 * tw * (0.7 + 0.5 * E['high']), 0.0)
    # the drive's exhaust: Astrophage light, infrared, drawn as a dim red
    rs = S['rnd']
    n = 48
    an = rs[:n, 0] * TAU
    rr = 0.3 + 1.3 * np.abs(rs[:n, 1])
    L = (3.0 + 5.0 * np.abs(rs[:n, 2])) * (0.5 + 0.8 * E['bass'] + 0.4 * E['kickenv'])
    fl = (t * (2.0 + np.abs(rs[:n, 3]) * 3.0)) % 1.0
    x0 = -7.7 - fl * 2.0
    seg = np.column_stack([x0, np.cos(an) * rr, np.sin(an) * rr, x0 - L * 0.4,
                           np.cos(an) * rr * 1.2, np.sin(an) * rr * 1.2])
    bag.arr(seg, 4, 0.55 * (1.0 - fl), 0.0)
    orb = S['orb']
    rad = 10.5 + 1.5 * math.sin(t * 0.05)
    P = (math.cos(orb) * rad, 3.0 * math.sin(t * 0.06) + 1.5, math.sin(orb) * rad)
    cam = _cam(P, (-0.5 + 1.5 * math.sin(t * 0.04), 0.0, 0.0), 1.2)
    return bag, cam, (0.0, 0.0, 0.0), 12.0, 0.9, (5.4, 0.0, 0.0), (40.0, 1e6)


def _view_tunnel(S, E, t):
    bag = Bag()
    R = 1.25
    n = 8
    zs = np.arange(-1.2, WALLZ + 4.0, 0.6)
    oct_ = [(math.cos(k * TAU / n + TAU / 16) * R, math.sin(k * TAU / n + TAU / 16) * R)
            for k in range(n)]
    prev = None
    for j, z in enumerate(zs):
        ring = [(x, y, z) for x, y in oct_]
        bag.P(ring, 0, 0.8 if abs(z - WALLZ) > 0.3 else 1.0, 0.9, True)
        if prev:
            for k in range(n):
                bag.L(prev[k], ring[k], 0, 0.6, 0.95)
                kk = (k + (1 if j % 2 else -1)) % n
                bag.L(prev[k], ring[kk], 0, 0.3, 1.0)
        prev = ring
    # the wall: clear xenonite, a fine grid you only see in the ripples
    g = np.linspace(-R, R, 13)
    for v in g:
        w = math.sqrt(max(0.0, (R * 0.92) ** 2 - v * v))
        if w > 0.05:
            bag.L((-w, v, WALLZ), (w, v, WALLZ), 1, 0.7, 1.0)
            bag.L((v, -w, WALLZ), (v, w, WALLZ), 1, 0.7, 1.0)
    # Rocky on the far side, one hand on the wall
    bump = S['bump']
    hx = 0.12 * math.sin(t * 0.4) * (1.0 - bump)
    hy = 0.05 + 0.25 * bump
    tap = 0.18 * max(0.0, S['legs'][0] - 0.3)
    hand = (hx, hy, WALLZ + 0.04 + tap)
    lifts = [0.0] + [S['legs'][i] * 0.4 for i in range(1, 5)]
    peak = _rocky(bag, (0.0, -R * 0.92, WALLZ + 1.15), -math.pi / 2.0, 0.78, t, lifts, E, S,
                  sw=0.5, hand=hand)
    # the ripples on the wall, from his hand
    for p in S['pings']:
        age = p[0]
        if age <= 0.0:
            continue
        rr = age * 1.4
        if rr > R * 1.1:
            continue
        a = (1.0 - age / PINGLIFE) * 0.9 * p[1]
        bag.ring((hand[0], hand[1], WALLZ - 0.01), (1, 0, 0), (0, 1, 0), rr, 20, 0.0, 1, a, 0.0)
    P = (0.12 * math.sin(t * 0.17), -0.1 + 0.08 * math.sin(t * 0.23),
         1.3 + 0.4 * math.sin(t * 0.07) + 0.3 * bump)
    cam = _cam(P, (0.05 * math.sin(t * 0.13), -0.15, WALLZ + 1.0), 1.0)
    return bag, cam, hand, 3.5, 0.3, peak, (FOGN, FOGD)


def _view_petrova(S, E, t):
    bag = Bag()
    star = np.array([-6.5, 0.8, 0.0])
    planet = np.array([5.5, -0.8, -1.0])
    cam_P = (1.5 * math.sin(t * 0.05), 1.2 + 0.5 * math.sin(t * 0.07), 10.5)
    cam = _cam(cam_P, (0.0, 0.2, 0.0), 1.15)
    R, U = cam[1], cam[2]
    # Tau Ceti: rings and rays, facing us
    for r in (0.7, 0.95, 1.25):
        bag.ring(tuple(star), tuple(R), tuple(U), r, 28, t * 0.05, 9, 0.8 if r < 1 else 0.4,
                 0.2)
    for k in range(28):
        an = k * TAU / 28 + t * 0.03
        L = 1.35 + (0.3 + 0.9 * E['bass']) * _h1(k * 1.7 + math.floor(t * 4.0) * 0.13)
        d = R * math.cos(an) + U * math.sin(an)
        bag.L(star + d * 1.3, star + d * L * 1.3, 9, 0.35, 0.2)
    # Adrian: a turning sphere of latitudes and longitudes
    for i in range(1, 8):
        la = (-0.5 + i / 8.0) * math.pi
        c = planet + np.array([0.0, math.sin(la) * 1.5, 0.0])
        bag.ring(tuple(c), (1, 0, 0), (0, 0, 1), math.cos(la) * 1.5, 20, 0.0, 10, 0.6, 0.7)
    for k in range(10):
        lo = k * TAU / 10 + t * 0.1
        pts = [tuple(planet + np.array([math.cos((-0.5 + i / 12.0) * math.pi) * math.cos(lo) * 1.5,
                                        math.sin((-0.5 + i / 12.0) * math.pi) * 1.5,
                                        math.cos((-0.5 + i / 12.0) * math.pi) * math.sin(lo) * 1.5]))
               for i in range(13)]
        bag.P(pts, 10, 0.45, 0.7)
    # the Petrova line: a river of Astrophage from the star to the planet
    P0 = star + np.array([1.3, 0.0, 0.0])
    P2 = planet - np.array([1.5, 0.0, 0.0])
    P1 = np.array([0.0, 2.8, 1.5])
    rs = S['rnd']
    n = NASTRO
    hh = np.abs(rs[:n, 0])
    u = (hh + t * (0.025 + 0.02 * np.abs(rs[:n, 1]))) % 1.0
    uu = u[:, None]
    C = (1 - uu) ** 2 * P0 + 2 * (1 - uu) * uu * P1 + uu ** 2 * P2
    Dv = 2 * (1 - uu) * (P1 - P0) + 2 * uu * (P2 - P1)
    Dv /= np.linalg.norm(Dv, axis=1)[:, None]
    wid = 0.35 + 0.25 * np.sin(u * 9.0 + t * 0.5)
    off = rs[:n, 1:4] * wid[:, None]
    C = C + off
    ln = 0.07 + 0.05 * np.abs(rs[:n, 2])
    seg = np.column_stack([C, C + Dv * ln[:, None]])
    fade = np.clip(np.minimum(u, 1.0 - u) * 8.0, 0.0, 1.0)
    a = fade * (0.35 + 0.65 * np.abs(rs[:n, 3]) * (0.4 + 0.8 * E['high']))
    # taumoeba: they arrive on the drop and eat what they touch
    tau = S['tau']
    if tau > 0.02:
        nt = 24
        tu = (0.35 + 0.3 * np.abs(rs[3000:3000 + nt, 0]) + t * 0.01) % 1.0
        tc = ((1 - tu[:, None]) ** 2 * P0 + 2 * (1 - tu[:, None]) * tu[:, None] * P1 +
              tu[:, None] ** 2 * P2) + rs[3100:3100 + nt, 0:3] * 0.3
        for j in range(nt):
            bag.ring(tuple(tc[j]), tuple(R), tuple(U), 0.07 + 0.03 * math.sin(t * 3 + j), 6,
                     t + j, 11, tau * 0.8, 0.0)
        dmin = np.min(np.abs(u[:, None] - tu[None, :]), axis=1)
        a = a * np.clip(1.0 - tau * np.exp(-(dmin / 0.03) ** 2), 0.0, 1.0)
    bag.arr(seg, 4, a, 0.3)
    st, tw = _stars(S)
    bag.arr(st, 6, 0.25 * tw, 0.0)
    return bag, cam, tuple(star), 10.0, 0.9, tuple(star), (40.0, 1e6)


VIEWFN = (_view_strings, _view_rocky, _view_ship, _view_tunnel, _view_petrova)


def _subdiv(A, maxlen):
    """Cut every sonar-lit segment longer than maxlen into equal pieces, so a ping's
    shell is drawn as a travelling front instead of whole lines blinking on."""
    if len(A) == 0:
        return A
    ln = np.linalg.norm(A[:, 3:6] - A[:, 0:3], axis=1)
    m = np.where(A[:, 8] > 0.3, np.clip(np.ceil(ln / maxlen), 1, 16), 1).astype(int)
    if m.max() == 1:
        return A
    idx = np.repeat(np.arange(len(A)), m)
    start = np.repeat(np.cumsum(m) - m, m)
    k = np.arange(len(idx)) - start
    mm = m[idx].astype(float)
    t0 = (k / mm)[:, None]
    t1 = ((k + 1) / mm)[:, None]
    P0, P1 = A[idx, 0:3], A[idx, 3:6]
    D = P1 - P0
    return np.column_stack([P0 + D * t0, P0 + D * t1, A[idx, 6:9]])


# --- the pipeline: sonar, camera, clip, perspective --------------------------------------
def _render(S, E, vi, t, ghost, alpha_mul):
    bag, cam, origin, pv, pw, voice, fogp = VIEWFN[vi](S, E, t)
    _glyphs(bag, S, cam, 0.75 if vi != 2 else 1.6)
    A = _subdiv(bag.done(), pw * 0.8)
    if len(A) == 0:
        return np.zeros((0, 8)), voice
    cls = A[:, 6].astype(int)
    a = A[:, 7]
    sw = A[:, 8]
    mid = (A[:, 0:3] + A[:, 3:6]) * 0.5
    dist = np.linalg.norm(mid - np.array(origin), axis=1)
    rev = np.zeros(len(A))
    for p in S['pings']:
        age = p[0]
        if age <= 0.0:
            continue
        k = age / PINGLIFE
        rev += p[1] * (1.0 - k) ** 1.5 * np.exp(-((dist - pv * age) / pw) ** 2)
    rev = np.minimum(rev, 1.0)
    al = a * ((1.0 - sw) + sw * (ghost + (1.0 - ghost) * rev)) * (1.0 + 0.7 * rev * sw) * alpha_mul
    pal = PAL
    col = pal[cls] + (pal[1] - pal[cls]) * (0.85 * rev * sw)[:, None]
    P, R, U, F, f = cam
    p0 = A[:, 0:3] - P
    p1 = A[:, 3:6] - P
    x0, y0, z0 = p0 @ R, p0 @ U, p0 @ F
    x1, y1, z1 = p1 @ R, p1 @ U, p1 @ F
    keep = ((z0 > NEAR) | (z1 > NEAR)) & (al > 0.004)
    x0, y0, z0, x1, y1, z1 = x0[keep], y0[keep], z0[keep], x1[keep], y1[keep], z1[keep]
    al, col = al[keep], col[keep]
    m = z0 < NEAR
    if m.any():
        tt = (NEAR - z0[m]) / (z1[m] - z0[m])
        x0[m] += (x1[m] - x0[m]) * tt
        y0[m] += (y1[m] - y0[m]) * tt
        z0[m] = NEAR
    m = z1 < NEAR
    if m.any():
        tt = (NEAR - z1[m]) / (z0[m] - z1[m])
        x1[m] += (x0[m] - x1[m]) * tt
        y1[m] += (y0[m] - y1[m]) * tt
        z1[m] = NEAR
    zm = (z0 + z1) * 0.5
    al = al * np.exp(-np.maximum(0.0, zm - fogp[0]) / fogp[1])
    return np.column_stack([f * x0 / z0, f * y0 / z0, f * x1 / z1, f * y1 / z1, col, al]), voice


# --- one frame -------------------------------------------------------------------------------
def _frame(scriptOp):
    d = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    sp = scriptOp.inputs[1] if len(scriptOp.inputs) > 1 else None
    comp = scriptOp.parent()
    par = comp.par
    S = _S['S']
    if S is None:
        S = _S['S'] = _new(SEED0)
        S['rnd'] = np.random.RandomState(5).uniform(-1.0, 1.0, (4096, 4))

    raw = _chan(d, 'rawtime')
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
    bpm = max(60.0, min(200.0, float(par.Bpm.eval()) or float(par.Refbpm.eval())))
    bp = 60.0 / bpm
    S['clk'] = (S['clk'] + dt) % 1000.0
    t = S['clk']
    rs = S['rs']
    E = {'bass': bass, 'high': high, 'energy': energy, 'kickenv': kickenv, 'dropenv': dropenv}

    # the spectrum: each band normalised against its own slowly-falling peak, then an
    # asymmetric smoothing so strings ring on and decay
    try:
        full = np.abs(np.asarray(sp[0].numpyArray(), dtype=np.float64))
        # the spectrum CHOP is already log-spaced along its samples: average it into
        # NBANDS equal runs, whatever length it arrives at
        raw_s = np.array([c.mean() if len(c) else 0.0
                          for c in np.array_split(full, NBANDS)])
    except Exception:
        raw_s = np.zeros(NBANDS)
    S['specpk'] = np.maximum(raw_s, S['specpk'] * (0.5 ** (dt / 6.0)))
    S['specpk'] = np.maximum(S['specpk'], 1e-4)
    nl = np.sqrt(np.clip(raw_s / S['specpk'], 0.0, 1.0)) * float(par.Reactivity.eval() > 0)
    k_up, k_dn = min(1.0, dt / 0.03), min(1.0, dt / 0.35)
    S['lev'] = np.where(nl > S['lev'], S['lev'] + (nl - S['lev']) * k_up,
                        S['lev'] + (nl - S['lev']) * k_dn)

    # verbs
    q = comp.fetch('qverbs', None)
    amaze = bump = chord = False
    if q:
        comp.store('qverbs', [])
        for v in q[:16]:
            if v.startswith('view'):
                n = int(v[4:]) - 1
                if 0 <= n < NV:
                    _switch(S, n, raw)
                    S['holdto'] = S['beat'] + 64
            elif v == 'auto':
                S['holdto'] = -1
            elif v == 'ping3':
                _ping(S, 3, 1.0)
            elif v == 'amaze':
                amaze = True
            elif v == 'bump':
                bump = True
            elif v == 'chord':
                chord = True
            elif v == 'reseed':
                S['seed'] = rs.random() * 100.0

    # beats and phrases
    S['bph'] += dt / bp
    while S['bph'] >= 1.0:
        S['bph'] -= 1.0
        S['beat'] += 1
        phrase = max(4, int(round(float(par.Phrase.eval()))))
        held = bool(par.Hold.eval()) or S['beat'] < S['holdto']
        if S['beat'] % phrase == 0 and not held and rs.random() < float(par.Changeprob.eval()):
            ch = [i for i in range(NV) if i != S['view']]
            if S['brk'] > 0.5:
                ch = [i for i in ch if VIEWS[i] in ('ROCKY', 'PETROVA', 'STRINGS')] or ch
            _switch(S, rs.choice(ch), raw)
        if S['beat'] % 4 == 0 and rs.random() < 0.35 and S['brk'] < 0.5:
            chord = True

    # breakdowns: the pings stop, he curls up, and keeps watch
    S['esh'] += (energy - S['esh']) * min(1.0, dt / 0.6)
    S['elo'] += (energy - S['elo']) * min(1.0, dt / 10.0)
    low = S['esh'] < 0.5 * max(S['elo'], 0.12) or S['esh'] < 0.08
    S['quiet'] = S['quiet'] + dt if low else 0.0
    brk_t = 1.0 if S['quiet'] > 2.5 else 0.0
    if (brk_t > 0.5) != S['inbrk']:
        S['inbrk'] = brk_t > 0.5
        if S['inbrk']:
            S['labt'] = raw
            S['phrase_txt'] = 'you sleep. i watch.'
    S['brk'] += (brk_t - S['brk']) * min(1.0, dt / (2.0 if brk_t > S['brk'] else 0.7))

    # events
    for i in range(5):
        S['legs'][i] *= 0.5 ** (dt / 0.12)
    S['jump'] *= 0.5 ** (dt / 0.35)
    S['voice'] *= 0.5 ** (dt / 0.3)
    S['bump'] *= 0.5 ** (dt / 1.2)
    S['tau'] *= 0.5 ** (dt / 3.0)
    S['pingenv'] *= 0.5 ** (dt / 0.25)
    if kicks and S['brk'] < 0.6:
        _ping(S, 1, 0.55 + 0.45 * beatstr)
        S['legs'][S['legi']] = 1.0
        S['legi'] = (S['legi'] + 2) % 5          # a star-step: every other leg
    if accents and rs.random() < 0.4:
        chord = True
    if drops or amaze:
        _ping(S, 3, 1.0)
        S['jump'] = 1.0
        S['tau'] = 1.0
        S['labt'] = raw
        S['phrase_txt'] = 'amaze amaze amaze'
        chord = True
        if drops and not par.Hold.eval() and S['beat'] >= S['holdto'] and rs.random() < 0.6:
            _switch(S, rs.choice([i for i in range(NV) if i != S['view']]), raw)
            S['phrase_txt'] = 'amaze amaze amaze'
    if bump:
        _switch(S, 3, raw)
        S['holdto'] = S['beat'] + 32
        S['bump'] = 1.0
        _ping(S, 2, 1.0)
        S['labt'] = raw
        S['phrase_txt'] = 'fist my bump.'
    if drops and S['view'] == 3:
        S['bump'] = 1.0
        S['phrase_txt'] = 'fist my bump.'
    for p in S['pings']:
        p[0] += dt
    S['pings'] = [p for p in S['pings'] if p[0] < PINGLIFE][-PINGMAX:]
    for g in S['glyphs']:
        g[0] += dt
    S['glyphs'] = [g for g in S['glyphs'] if g[0] < GLIFE][-GLYPHMAX:]

    # motion, every phase wrapped
    walk = (0.45 + 0.5 * energy) * (1.0 - 0.8 * S['brk'])
    S['hz_f'] += walk * dt / MODL
    while S['hz_f'] >= 1.0:
        S['hz_f'] -= 1.0
        S['hz_i'] = (S['hz_i'] + 1) % 1048576
    S['gait'] = (S['gait'] + dt * walk * 5.0) % TAU
    S['orb'] = (S['orb'] + dt * (0.06 + 0.10 * bass) * (1.0 - 0.6 * S['brk'])) % TAU
    S['roll'] = (S['roll'] + dt * 0.05) % TAU
    S['xf'] = min(1.0, S['xf'] + dt / (4.0 * bp))

    ghost = float(par.Ghost.eval()) * (1.0 - 0.4 * S['brk'])
    parts = []
    voice = None
    xf = S['xf']
    if S['prev'] is not None and xf < 1.0:
        B, _v = _render(S, E, S['prev'], t, ghost, 1.0 - xf)
        parts.append(B)
    B, voice = _render(S, E, S['view'], t, ghost, xf if S['prev'] is not None else 1.0)
    parts.append(B)
    if xf >= 1.0:
        S['prev'] = None
    if chord and voice is not None:
        _speak(S, voice)
    B = np.vstack(parts)

    ink = 1.0 + 0.15 * kickenv
    x0, y0, x1, y1 = B[:, 0], B[:, 1], B[:, 2], B[:, 3]
    dx, dy = x1 - x0, y1 - y0
    ln = np.hypot(dx, dy)
    ok = np.isfinite(ln) & (ln > MINLEN) & (ln < MAXL) & (B[:, 7] > 0.004) & \
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
        out[7, :n] = np.clip(B[idx, 4], 0.0, 2.0)
        out[8, :n] = np.clip(B[idx, 5], 0.0, 2.0)
        out[9, :n] = np.clip(B[idx, 6], 0.0, 2.0)
        out[10, :n] = np.clip(B[idx, 7] * ink, 0.0, 1.0)
    S['lastout'] = out
    _publish(scriptOp, out)

    title = VIEWTITLES[S['view']]
    txt = S['phrase_txt'] or title
    lf = math.exp(-max(0.0, raw - S['labt']) / 3.0) if raw >= S['labt'] else 1.0
    try:
        par.View.val = float(S['view'])
        par.Beat.val = float(S['beat'])
        par.Segs.val = float(n)
        par.Trail.val = min(0.9, (0.55 + 0.25 * S['brk']) * float(par.Trails.eval()))
        par.Brk.val = S['brk']
        par.Tclk.val = t
        par.Ping.val = S['pingenv']
        bg = PAL[0] * 0.035 + PAL[1] * 0.02 * S['pingenv']
        par.Bgr.val, par.Bgg.val, par.Bgb.val = float(bg[0]), float(bg[1]), float(bg[2])
        par.Labelfade.val = lf
        if txt != S['lastlab'] and lf > 0.05:
            S['lastlab'] = txt
            par.Scaletxt.val = txt
    except Exception:
        pass
    S['census'] = ('%s | beat %d | pings %d | glyphs %d | brk %.2f | lines %d/%d'
                   % (VIEWS[S['view']], S['beat'], len(S['pings']), len(S['glyphs']),
                      S['brk'], n, MAXSEG))
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
                print('[eridian engine] frame failed:\n' + S['lasterr'])
            prev = S.get('lastout')
        else:
            prev = None
        if prev is None:
            raise
        _publish(scriptOp, prev)
    return
'''

# the palette: xenonite is a dark bronze, the sonar is a cold teal, Rocky is stone,
# the strings are pale brass, Astrophage is infrared red, his voice is violet; then
# stars, Tau Ceti, Adrian, and six spectral hues for the prisms. Kept dim: the club
# wall is bright enough already.
_PAL = [
    (0.60, 0.42, 0.26), (0.22, 0.85, 0.80), (0.66, 0.54, 0.42), (0.95, 0.78, 0.50),
    (0.85, 0.10, 0.06), (0.62, 0.45, 1.00), (0.45, 0.50, 0.65), (0.0, 0.0, 0.0),
    (1.00, 0.30, 0.25), (1.00, 0.62, 0.20), (0.35, 0.80, 0.70),
    (0.30, 0.90, 0.45), (0.30, 0.55, 1.00), (0.75, 0.35, 1.00),
]
_PAL[9] = (1.00, 0.55, 0.22)       # Tau Ceti
_PAL[10] = (0.35, 0.75, 0.80)      # Adrian

eng_src = C(textDAT, 'engine_src', 1780, 980)
eng_src.text = hdr(
    VIEWS=VIEWS, VIEWTITLES=VIEWTITLES, MAXSEG=MAXSEG, SEED0=20260926, NBANDS=NBANDS,
    CH=('tx', 'ty', 'tz', 'rz', 'sx', 'sy', 'sz', 'r', 'g', 'b', 'a'),
    PINGLIFE=2.4, PINGMAX=10, GLIFE=3.5, GLYPHMAX=6,
    MODL=4.0, NMOD=8, NSTRH=16, WALLZ=4.0, NASTRO=700,
    NEAR=0.05, FOGN=6.0, FOGD=14.0,
    CULLX=1.4, CULLY=0.85, MINLEN=0.0005, MAXL=3.0,
) + 'import numpy as _np0\nPAL = _np0.array(%r)\n' % (_PAL,) + ENGINE_BODY

engine = C(scriptCHOP, 'engine', 1940, 980)
engine.par.callbacks = eng_src.name
W(director, engine, 0)
W(null_spec, engine, 1)


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
soft(mat_line, widthnear=1.25, widthfar=1.25, widthaffectedbyfov=False,
     linenearalpha=1.0, blending=True, depthtest=False, depthwriting=False)
mat_line.par.widthnear.expr = ("max(0.6, parent().par.Linewidth * (1.0 + 0.25 * %s "
                               "+ 0.20 * parent().par.Ping))" % D('bass'))
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

# --- the echo: what the sonar lit fades rather than vanishes ------------------------
trail_fb = C(feedbackTOP, 'trail_fb', 2100, 120)
res(trail_fb)
W(render_lines, trail_fb)
trail = C(glslTOP, 'trail', 2260, 200)
res(trail)
trail_pix = C(textDAT, 'trail_pixel', 2260, 130)
trail_pix.text = '''// The echo. The previous frame, decayed and max'ed under the new lines, so what a
// ping lit fades out behind it instead of switching off. Max, not add: it cannot
// brighten anything past the line that drew it.
uniform vec4 uT;   // x decay
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec4 cur = texture(sTD2DInputs[0], uv);
    vec4 fb = texture(sTD2DInputs[1], uv);
    fragColor = TDOutputSwizzle(max(cur, fb * uT.x));
}
'''
trail.par.pixeldat = trail_pix.name
W(render_lines, trail, 0)
W(trail_fb, trail, 1)
trail.par.vec = 1
trail.par.vec0name = 'uT'
trail.par.vec0valuex.expr = 'parent().par.Trail'
trail_fb.par.top = trail.name

# --- the void: near-black, a breath of the palette -----------------------------------
void = C(glslTOP, 'void', 1940, 440)
res(void)
void_pix = C(textDAT, 'void_pixel', 1940, 370)
void_pix.text = '''// The dark. Almost black on purpose — this goes on an LED wall in a club — with a
// faint drift of colour, a vignette, and grain so the gradients do not band.
uniform vec4 uP;   // x energy, y ping, z vignette, w clock
uniform vec4 uB;   // rgb tint
out vec4 fragColor;

float hash(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453); }
float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
               mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

void main() {
    vec2 uv = vUV.st;
    vec2 d = (uv - 0.5) * vec2(1.7778, 1.0);
    float t = uP.w;
    float n = vnoise(d * 2.2 + vec2(t * 0.02, -t * 0.013)) * vnoise(d * 5.0 - t * 0.01);
    vec3 col = uB.rgb * (0.4 + 1.8 * n);
    col += (hash(uv * vec2(1920.0, 1080.0) + fract(t)) - 0.5) * 0.004;
    col *= 1.0 - uP.z * 0.8 * dot(d, d);
    fragColor = TDOutputSwizzle(vec4(max(col, vec3(0.0)), 1.0));
}
'''
void.par.pixeldat = void_pix.name
void.par.vec = 2
void.par.vec0name = 'uP'
void.par.vec0valuex.expr = D('energy')
void.par.vec0valuey.expr = 'parent().par.Ping'
void.par.vec0valuez.expr = 'parent().par.Vignette'
void.par.vec0valuew.expr = 'parent().par.Tclk'
void.par.vec1name = 'uB'
void.par.vec1valuex.expr = 'parent().par.Bgr'
void.par.vec1valuey.expr = 'parent().par.Bgg'
void.par.vec1valuez.expr = 'parent().par.Bgb'

comp = C(compositeTOP, 'comp_scene', 2420, 440, operand='over')
res(comp)
W(trail, comp, 0)
W(void, comp, 1)

glow_cut = C(levelTOP, 'glow_cut', 2420, 320)
soft(glow_cut, blacklevel=0.25, gamma1=1.2)
W(comp, glow_cut)
glow_blur = C(blurTOP, 'glow_blur', 2580, 320, size=10.0)
res(glow_blur, OUTW // 2, OUTH // 2)
W(glow_cut, glow_blur)
glow_lvl = C(levelTOP, 'glow_lvl', 2740, 320)
glow_lvl.par.opacity.expr = ("0.45 * parent().par.Glow * (0.5 + 0.3 * %s + 0.3 * parent().par.Ping)"
                             % D('energy'))
W(glow_blur, glow_lvl)
comp_glow = C(compositeTOP, 'comp_glow', 2580, 440, operand='add')
res(comp_glow)
W(comp, comp_glow, 0)
W(glow_lvl, comp_glow, 1)

# --- the club limiter: hold the average picture level under a cap -------------------
apl = C(analyzeTOP, 'apl_analyze', 2740, 560)
menu_pick(apl.par.op, 'average')
menu_pick(apl.par.analyzechannel, 'luminance')
W(comp_glow, apl)
apl_chop = C(toptoCHOP, 'apl_chop', 2900, 560)
apl_chop.par.top = apl.name
apl_lag = C(lagCHOP, 'apl_lag', 3060, 560)
soft(apl_lag, lag1=0.15, lag2=1.2)
W(apl_chop, apl_lag)

limiter = C(glslTOP, 'limiter', 2740, 440)
res(limiter)
lim_pix = C(textDAT, 'limiter_pixel', 2740, 370)
lim_pix.text = '''// For an LED wall in a club. Two stages:
//   1. a gain that holds the frame's AVERAGE brightness under a cap (measured one
//      frame late by an Analyze TOP and lagged, so it rides slowly, like a limiter)
//   2. a soft ceiling on the PEAKS: c' = M * (1 - exp(-c / M)), which is linear in
//      the dark and never passes M.
uniform vec4 uL;   // x master brightness, y average cap, z measured average, w ceiling
out vec4 fragColor;

void main() {
    vec4 c = texture(sTD2DInputs[0], vUV.st);
    float gain = uL.x * min(1.0, uL.y / max(uL.z * uL.x, 1e-4));
    vec3 col = c.rgb * gain;
    float M = uL.w;
    col = M * (1.0 - exp(-col / M));
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
'''
limiter.par.pixeldat = lim_pix.name
W(comp_glow, limiter)
limiter.par.vec = 1
limiter.par.vec0name = 'uL'
limiter.par.vec0valuex.expr = 'parent().par.Brightness'
limiter.par.vec0valuey.expr = 'parent().par.Aplmax'
limiter.par.vec0valuez.expr = ("max(0.0, 0.2126 * op('apl_lag')['r'] + 0.7152 * op('apl_lag')['g'] "
                               "+ 0.0722 * op('apl_lag')['b'])")
limiter.par.vec0valuew.expr = 'parent().par.Ceiling'

label = C(textTOP, 'label', 2420, 700)
res(label, OUTW, OUTH, 'rgba8fixed')
soft(label, alignx='left', aligny='bottom', fontsizex=18, font='Courier New',
     bgalpha=0.0, fontcolorr=0.55, fontcolorg=0.62, fontcolorb=0.62,
     fontcolora=1.0, wordwrap=False, trackingx=0.30,
     positionx=0.04, positiony=0.06, positionunit='fraction')
label.par.text.expr = 'parent().par.Scaletxt.eval()'
label_lvl = C(levelTOP, 'label_lvl', 2580, 700)
label_lvl.par.opacity.expr = "parent().par.Label * parent().par.Labelfade"
W(label, label_lvl)
comp_label = C(compositeTOP, 'comp_label', 2900, 440, operand='over')
res(comp_label)
W(label_lvl, comp_label, 0)
W(limiter, comp_label, 1)

final_out = C(nullTOP, 'final_out', 3060, 440)
W(comp_label, final_out)
out1 = C(outTOP, 'out1', 3220, 440)
W(final_out, out1)

pout = proj.create(outTOP, SCENE + '_out')
pout.nodeX, pout.nodeY = 400, -5600
s.outputConnectors[0].connect(pout.inputConnectors[0])


# ---------------------------------------------------------------------------
# PADS AND KEYS
# ---------------------------------------------------------------------------
PEXEC_BODY = '''# Every pad is a verb into the engine's queue.


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
    if n.startswith('View'):
        _push(comp, 'view' + n[4:])
    else:
        _push(comp, {'Auto': 'auto', 'Ping3': 'ping3', 'Amaze': 'amaze', 'Bump': 'bump',
                     'Chord': 'chord', 'Reseed': 'reseed'}.get(n, ''))
    return
'''
pexec = C(parameterexecuteDAT, 'pad_exec', 2100, 1000)
pexec.text = PEXEC_BODY
pexec.par.op = '..'
soft(pexec, pars=' '.join(['View%d' % (i + 1) for i in range(len(VIEWS))]
                          + ['Auto', 'Ping3', 'Amaze', 'Bump', 'Chord', 'Reseed']),
     valuechange=False, onpulse=True)

KEY_BODY = '''# 1-5 choose a view (held for 64 beats, then the automatic changes resume); 0 releases.
#   s  SONAR    three pings
#   a  AMAZE    amaze amaze amaze
#   f  FIST MY BUMP   (goes to the tunnel)
#   c  CHORD    Rocky speaks
#   h  HOLD     no automatic view changes (toggle)
#   n  RESEED


def onKey(dat, keyInfo):
    if not keyInfo.state:
        return
    comp = dat.parent()
    k = keyInfo.key
    if k in '12345':
        getattr(comp.par, 'View' + k).pulse()
    elif k == 'h':
        comp.par.Hold = not comp.par.Hold.eval()
    else:
        p = {'0': 'Auto', 's': 'Ping3', 'a': 'Amaze', 'f': 'Bump', 'c': 'Chord',
             'n': 'Reseed'}.get(k)
        if p:
            getattr(comp.par, p).pulse()
    return


def onShortcut(dat, shortcutName, time):
    return
'''
keyin = C(keyboardinDAT, 'key_pad', 1780, 700)
keyin.par.keys = '1 2 3 4 5 0 s a f c h n'
kcb = keyin.par.callbacks.eval()
if kcb is None:
    kcb = C(textDAT, 'key_pad_callbacks', 1780, 620)
    keyin.par.callbacks = kcb.name
kcb.nodeX, kcb.nodeY = 1780, 620
kcb.text = KEY_BODY

# NO executeDAT KEEP-ALIVE (see bayou): pull-based.
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
        (comp_glow.par.operand.eval(), 'add', 'glow composite operand'),
        (spec.par.outputmenu.eval(), 'setmanually', 'spectrum output length'),
        (apl.par.op.eval(), 'average', 'limiter analysis')):
    if _got != _want:
        print('  [CHECK FAILED] %s is %r, expected %r' % (_what, _got, _want))

print('built %s' % s.path)
print('  %s' % eng_src.module._S['S']['census'])
