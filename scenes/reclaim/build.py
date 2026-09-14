# Reclaim — nature takes a brick wall back.
#
# One continuous story, not a loop of stages. A photographed brick wall is edge-traced
# to its mortar outlines. A crack opens, an L-System plant pushes through it, grows,
# blooms and draws bees — and then a second plant cracks its own brick and does the
# same, then a third, then a fourth, until the wall is a garden. Each plant's scene
# takes `Scenelen` seconds (60 by default), so the whole arc runs about four minutes
# before it loops.
#
# Keys 1-9 are *checkpoints*, not freeze-frames: pressing one seeks the story to that
# moment and playback carries on from there.
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
GENMAX = 5.0                      # L-System generations at full growth
MAXSITES = 46 * 8                 # hard cap on flower sites (all plants combined)
MAXBEES = 80
MAXLEAVES = 26 * 8                # hard cap on leaves (all plants combined)

# Master clock period. The clock timer free-runs and cycles on this, and
# cycles_plus_fraction * CLOCKLEN is a monotonic seconds counter that the story time
# is measured against. Independent of Scenelen so retiming the show never jumps it.
CLOCKLEN = 60.0

# Checkpoints, in multiples of Scenelen. Pressing one SEEKS the story there and lets
# it keep running — these are chapter marks, not freeze-frames.
CHECKPOINTS = [
    ('start',  ' 1 - Bare Wall',      0.00),
    ('crack',  ' 2 - First Crack',    0.02),
    ('grow',   ' 3 - Sprout & Grow',  0.14),
    ('bloom',  ' 4 - First Bloom',    0.50),
    ('bees',   ' 5 - Bees Arrive',    0.66),
    ('spread', ' 6 - Spreading',      1.00),
    ('half',   ' 7 - Half the Wall',  2.00),
    ('last',   ' 8 - Last Plants',    3.00),
    ('garden', ' 9 - Full Garden',    4.65),   # into the held ending
]

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
# Heights are deliberately uneven so the garden does not read as a row of pickets.
PLANTS = [
    (-0.86, -0.34, 0.66, 3),
    (-0.62, -0.50, 0.52, 11),
    (-0.34, -0.22, 0.74, 27),
    (-0.06, -0.50, 0.50, 41),
    (0.20, -0.30, 0.66, 59),
    (0.46, -0.52, 0.46, 73),
    (0.70, -0.24, 0.60, 89),
    (0.93, -0.45, 0.44, 101),
]

# Plants do not wait for each other. Plant i's scene opens STAGGER scene-lengths after
# plant i-1, so growth overlaps and the wall is continuously in motion instead of
# taking eight full minutes to fill.
STAGGER = 0.5

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
    ('Scenelen',   'Seconds per Plant', 60.0, 10.0, 180.0),
    ('Refbpm',     'Reference BPM',    120.0, 60.0, 200.0),
    ('Beatdrive',  'Beat Drive',         1.0, 0.0, 1.0),
    ('Photomix',   'Wall Photo Mix',    0.62, 0.0, 1.0),
    ('Linebright', 'Brick Line Bright', 1.0, 0.0, 3.0),
    ('Crackamt',   'Crack Amount',      1.0, 0.0, 2.0),
    ('Moss',       'Moss on the Wall',  1.0, 0.0, 2.0),
    ('Flowersize', 'Flower Size',       1.0, 0.2, 3.0),
    ('Leafsize',   'Leaf Size',         1.0, 0.0, 3.0),
    ('Beecount',   'Bee Count',        26.0, 0.0, float(MAXBEES)),
    ('Beespeed',   'Bee Speed',         1.0, 0.0, 3.0),
    ('Glow',       'Glow',              0.55, 0.0, 3.0),
    ('Vignette',   'Vignette',          0.9, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

# --- checkpoints -----------------------------------------------------------
# Timeoffset is the story's playhead: showtime = monotonic clock - Timeoffset.
# Seeking is just a subtraction, which is why a checkpoint resumes playing instead
# of freezing — nothing is paused, the playhead simply moves.
pg.appendFloat('Timeoffset', label='Time Offset (s)')
s.par.Timeoffset.normMin, s.par.Timeoffset.normMax = -600.0, 600.0
s.par.Timeoffset.default = 0.0

pg.appendFloat('Bpm', label='Detected BPM')
s.par.Bpm.normMin, s.par.Bpm.normMax = 0.0, 200.0
s.par.Bpm.readOnly = True

pg.appendFloat('Showtime', label='Story Time (s)')
s.par.Showtime.normMin, s.par.Showtime.normMax = 0.0, 300.0
s.par.Showtime.readOnly = True

for cp, label, _mult in CHECKPOINTS:
    pg.appendPulse('Go' + cp, label=label)
pg.appendPulse('Nextcp', label='Next Checkpoint')
pg.appendPulse('Prevcp', label='Previous Checkpoint')
pg.appendPulse('Restart', label=' 0 - Restart Story')

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
# MASTER CLOCK — one timerCHOP, free-running, cycling forever, never seeked.
# cycles_plus_fraction is monotonic, so it gives a continuous seconds counter that
# does not depend on the project timeline range. The story's playhead is this minus
# Timeoffset, so seeking never touches the clock itself.
# ---------------------------------------------------------------------------
timer = C(timerCHOP, 'clock', 0, 1000, lengthunits='seconds', length=CLOCKLEN,
          cycle=True, cyclelimit=False, play=True,
          outfraction=True, outcycle=True, outcycleplusfraction=True)


# ---------------------------------------------------------------------------
# TEMPO — the story runs on musical time, not wall time
# ---------------------------------------------------------------------------
tempo_src = C(textDAT, 'tempo_src', 1780, 1240)
tempo_src.text = '''# Beat detector and tempo estimator. The story advances on musical time, not wall
# time, so a 140bpm track pushes the plants up noticeably faster than a 90bpm one.
#
# Onset detection is done here rather than with a trigger CHOP so the refractory
# period and the adaptive threshold are explicit and tunable. The level is compared
# against its own slow EMA, which makes the detector indifferent to how hot the
# source is - the same reason patterns.md recommends envelope-divide normalisation.
REF_FLOOR = 0.25       # slowest the story may crawl when the music goes quiet
REF_CEIL = 2.50
REFRACTORY = 0.30      # seconds; caps detection at 200bpm and kills double-hits
SILENCE = 2.5          # seconds without a beat before we decide the music stopped

_state = {'prev': 0.0, 'fluxavg': 0.0, 'last_t': 0.0, 'last_beat': -99.0,
          'intervals': [], 'factor': 1.0, 'seen': False, 'hist': []}


def onCook(scriptOp):
    src = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    clk = scriptOp.inputs[1] if len(scriptOp.inputs) > 1 else None
    par = scriptOp.parent().par
    st = _state

    # Peak over the whole time slice, not sample 0: at 60fps a frame carries several
    # samples and a kick transient can land on any of them.
    level = 0.0
    try:
        level = max(abs(v) for v in src.chan(0).vals)
    except Exception:
        pass
    try:
        now = float(clk['cycles_plus_fraction'][0]) * %.4f
    except Exception:
        now = st['last_t']

    dt = max(0.0, now - st['last_t'])
    st['last_t'] = now

    # Positive spectral flux, not a level ratio. Comparing the slice peak against an
    # EMA of the slice peak does not work: the envelope is already smooth, so the
    # baseline sits at roughly the same height as the signal (measured: baseline 0.77
    # against a signal maxing at 0.54) and the ratio never clears a threshold. The
    # RISE is what marks an onset, and it is naturally independent of how loud the
    # track is.
    flux = max(0.0, level - st['prev'])
    st['prev'] = level
    a = min(1.0, dt / 0.6) if dt > 0 else 0.0
    st['fluxavg'] += (flux - st['fluxavg']) * a
    ratio = flux / max(st['fluxavg'], 1e-5)

    # small ring buffer so the detector can be tuned against real numbers
    st['hist'].append((round(level, 4), round(flux, 5), round(st['fluxavg'], 5)))
    del st['hist'][:-150]

    beat = 0.0
    if flux > max(st['fluxavg'] * 1.9, 0.004):
        if now - st['last_beat'] > REFRACTORY:
            iv = now - st['last_beat']
            if 0.32 < iv < 1.30:           # 46..187bpm; ignore gaps outside that
                # A MEDIAN of recent intervals, not an EMA: one spurious onset
                # halves an EMA and drags the whole tempo with it, while the median
                # simply ignores it.
                st['intervals'].append(iv)
                del st['intervals'][:-24]
            st['last_beat'] = now
            st['seen'] = True
            beat = 1.0

    # The DOMINANT CLUSTER, not the median. Spurious onsets do not scatter evenly -
    # they pile up at their own interval, so the collected set is bimodal and a median
    # lands in the empty gap between the two humps. Measured on the test track:
    #   [0.35 0.35 0.367 0.367 0.367 0.383 0.40 0.417 0.483 x6 0.65]
    # -> median 0.417 = 144bpm (wrong), dominant cluster 0.483 = 124bpm (right).
    ivs = st['intervals']
    period = 0.5
    if ivs:
        best_n = 0
        for c in ivs:
            near = [v for v in ivs if abs(v - c) <= c * 0.09]
            if len(near) > best_n:
                best_n = len(near)
                period = sum(near) / len(near)
    bpm = 60.0 / max(period, 1e-3)
    bpm = min(200.0, max(50.0, bpm))

    # Before the first beat has ever been heard, sit at 1.0 rather than the silence
    # floor: the detector needs a few seconds of audio to acquire, and dropping to
    # 0.25x meanwhile made the show crawl every time the scene was (re)built.
    quiet = st['seen'] and now - st['last_beat'] > SILENCE
    if not st['seen']:
        target = 1.0
    else:
        target = REF_FLOOR if quiet else bpm / max(1.0, float(par.Refbpm.eval()))
    target = min(REF_CEIL, max(REF_FLOOR, target))
    # ease toward the target so a missed beat cannot jolt the whole story
    st['factor'] += (target - st['factor']) * min(1.0, dt * 1.5)

    drive = float(par.Beatdrive.eval())
    factor = 1.0 + (st['factor'] - 1.0) * drive

    scriptOp.clear()
    chans = [scriptOp.appendChan(n) for n in ('factor', 'bpm', 'beat', 'ratio')]
    scriptOp.numSamples = 1
    for c, v in zip(chans, (factor, bpm if (st['seen'] and not quiet) else 0.0,
                            beat, ratio)):
        c[0] = v
    try:
        par.Bpm.val = bpm if (st['seen'] and not quiet) else 0.0
    except Exception:
        pass
    return
''' % CLOCKLEN

tempo = C(scriptCHOP, 'tempo', 1940, 1240)
tempo.par.callbacks = tempo_src.path
# The 700Hz "bass" band is too wide to count beats with - it carries the bassline
# and the body of the snare as well as the kick, and detection off it read 175bpm on
# a ~125bpm track. This is a dedicated kick band, and it feeds nothing else.
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

# ---------------------------------------------------------------------------
# DIRECTOR — the whole show's state in one 1-sample CHOP.
# ---------------------------------------------------------------------------
dir_src = C(textDAT, 'director_src', 1780, 1120)
dir_src.text = '''# Director: turns one monotonic clock + the audio bands into every envelope the
# scene needs. There is no cycling stage machine here - the whole show is a single
# playhead, `show`, measured in seconds since the wall was bare. Each plant owns a
# `scenelen`-long window of it and simply holds its finished state afterwards.
import math

NPLANTS = %d
CLOCKLEN = %.4f
STAGGER = %.4f     # scene-lengths between one plant's start and the next
TAIL = 0.30        # extra scene-lengths of held full garden at the end


# Musical time is integrated here rather than with a speed CHOP: the CHOP's
# accumulator did not survive being cooked on demand (it read 0.18s after a minute
# of running), and dt is derived from the wall clock so cooking this script twice in
# one frame adds nothing the second time.
_clock = {'last_raw': None, 'musical': 0.0}


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
    mus = scriptOp.inputs[2] if len(scriptOp.inputs) > 2 else None
    par = scriptOp.parent().par

    # Wall seconds. Bee orbits and plant sway run off this so they stay smooth and
    # physical even if the tempo estimate wobbles.
    raw = chan(tmr, 'cycles_plus_fraction', 0.0) * CLOCKLEN
    # Musical seconds: the integral of the tempo factor, so it runs fast on a quick
    # track and slow on a mellow one. Monotonic, which is what lets a seek stay a
    # plain subtraction.
    factor = chan(mus, 'factor', 1.0)
    if _clock['last_raw'] is None:
        _clock['last_raw'] = raw
    dt = raw - _clock['last_raw']
    if dt < 0.0:
        dt = 0.0
    _clock['last_raw'] = raw
    _clock['musical'] += dt * factor
    musical = _clock['musical']

    scenelen = max(1.0, float(par.Scenelen.eval()))
    storyend = scenelen * ((NPLANTS - 1) * STAGGER + 1.0 + TAIL)
    # Clamped, NOT wrapped: the garden is the end of the story and it stays on screen
    # until someone seeks back to an earlier checkpoint and lets it grow again.
    show = min(storyend, max(0.0, musical - float(par.Timeoffset.eval())))

    bass = chan(aud, 'bass', 0.0)
    high = chan(aud, 'high', 0.0)
    energy = chan(aud, 'energy', 0.0)

    out = {'rawtime': raw, 'musical': musical, 'show': show, 'ctime': raw,
           'tempofactor': factor,
           'scene': float(int(show / scenelen)),
           'done': 1.0 if show >= storyend - 1e-3 else 0.0,
           'bass': bass, 'high': high, 'energy': energy}

    # Bass makes whatever is currently growing surge; it never runs backwards.
    surge = 1.0 + 0.45 * bass

    for i in range(NPLANTS):
        p = (show - i * scenelen * STAGGER) / scenelen   # <0 not yet, 0..1 its scene
        if p < 0.0:
            crack = grow = bloom = bee = 0.0
        elif p <= 1.0:
            crack = env(p, 0.02, 0.22)
            grow = min(1.0, env(p, 0.12, 0.62) * surge)
            bloom = env(p, 0.52, 0.80)
            bee = env(p, 0.68, 0.95)
        else:
            crack = grow = bloom = bee = 1.0
        # The plant COMP rotates by this, and the flower and bee instancers rotate
        # their anchors by the same angle about the same base. Publishing it once is
        # the only way those stay in agreement - flowers used to carry an unrelated
        # horizontal wiggle of their own and visibly slid off the stems.
        out['sway%%d' %% i] = (2.6 * math.sin(raw * (0.31 + 0.04 * i) + i * 2.1)
                              * (0.5 + min(1.0, energy)) * (1.0 if grow > 0.0 else 0.0))
        out['crack%%d' %% i] = crack
        out['grow%%d' %% i] = grow
        out['bloom%%d' %% i] = bloom
        out['bee%%d' %% i] = bee
        # Every later scene keeps adding flowers to the plants already standing.
        out['dens%%d' %% i] = min(1.0, 0.62 + 0.16 * max(0.0, p - 1.0))

    # How full the garden is overall, 0..1 - drives bee count and glow.
    out['fullness'] = min(1.0, show / max(1e-6, storyend - scenelen * TAIL))

    scriptOp.clear()
    keys = sorted(out.keys())
    chans = [scriptOp.appendChan(k) for k in keys]
    scriptOp.numSamples = 1
    for c, k in zip(chans, keys):
        c[0] = out[k]

    # Mirrored onto a read-only par so the playhead is visible while performing.
    try:
        par.Showtime.val = show
    except Exception:
        pass
    return
''' % (len(PLANTS), CLOCKLEN, STAGGER)

director = C(scriptCHOP, 'director', 1940, 1120)
director.par.callbacks = dir_src.path
W(timer, director, 0)
W(null_audio, director, 1)
W(tempo, director, 2)


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
UNIFORM_SEEDS
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

    SEED_ARRAY
    float crack = 0.0;   // thin fracture lines
    float rim = 0.0;     // dust glowing on the breaking edge
    float hole = 0.0;    // bricks actually gone
    float moss = 0.0;    // green creeping out from every break

    for (int i = 0; i < NSEEDS; i++) {
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
        // moss spreads much further than the fracture itself
        moss = max(moss, (1.0 - smoothstep(R * 0.5, R * 3.2, d)) * sd.w);
    }

    float amt = uParams.y;
    crack = clamp(crack * amt, 0.0, 1.0);
    rim = clamp(rim * amt, 0.0, 1.0);
    hole = clamp(hole * amt, 0.0, 1.0);

    // Mostly a dark void where the brick has gone, with warm light bleeding along the
    // fracture edge. Weighted the other way it reads as lava rather than a broken wall.
    vec3 col = wall.rgb * (1.0 - 0.88 * crack);
    col = mix(col, vec3(0.010, 0.008, 0.010), max(crack * 0.78, hole * 0.94));
    col += vec3(1.00, 0.50, 0.18) * crack * (0.11 + 0.30 * uParams.z);
    col += vec3(1.00, 0.74, 0.40) * rim * (0.34 + 0.65 * uParams.z);

    // Moss: patchy green growing out of every break, thickening as the garden fills.
    // Broken up by its own noise so it reads as growth on the brick rather than a
    // green wash, and it settles into the mortar (the darker pixels) first.
    float mossN = fbm(p * 22.0);
    float mortar = 1.0 - smoothstep(0.05, 0.30, dot(wall.rgb, vec3(0.33)));
    float mossAmt = clamp(moss * uGrade.y, 0.0, 1.0)
                  * smoothstep(0.30, 0.72, mossN)
                  * (0.45 + 0.55 * mortar);
    vec3 mossCol = vec3(0.16, 0.34, 0.12) + 0.5 * wall.rgb * vec3(0.3, 0.9, 0.3);
    col = mix(col, mossCol, mossAmt * 0.80);

    vec2 q = uv - 0.5;
    col *= clamp(1.0 - uGrade.x * dot(q, q) * 1.6, 0.0, 1.0);

    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
'''
# The seed uniforms are generated so the shader always matches len(PLANTS) - adding
# a plant must never mean hand-editing GLSL.
_n = len(PLANTS)
crack_code = crack_code.replace(
    'UNIFORM_SEEDS',
    '\n'.join('uniform vec4 uSeed%d;' % i for i in range(_n))
    + '   // xy seed in uv space, z growth radius, w active')
crack_code = crack_code.replace(
    'SEED_ARRAY',
    'vec4 seeds[%d] = vec4[%d](%s);'
    % (_n, _n, ', '.join('uSeed%d' % i for i in range(_n))))
crack_code = crack_code.replace('NSEEDS', str(_n))

crack_dat = C(textDAT, 'wall_crack_pixel', 1460, 620)
crack_dat.text = crack_code
crack_src.par.pixeldat = crack_dat.path

# Uniforms via the Vectors page — the Constants page is broken on this build
# (MACHINE.md), and packing into vec4s is safe everywhere.
crack_src.par.vec = len(PLANTS) + 2
for i, (px, py, _h, seed) in enumerate(PLANTS):
    setattr(crack_src.par, 'vec%dname' % i, 'uSeed%d' % i)
    # world -> uv
    getattr(crack_src.par, 'vec%dvaluex' % i).val = 0.5 + px / ORTHOW
    getattr(crack_src.par, 'vec%dvaluey' % i).val = 0.5 + py / ORTHOH
    getattr(crack_src.par, 'vec%dvaluez' % i).expr = (
        "0.02 + 0.19 * %s" % D('crack%d' % i))
    getattr(crack_src.par, 'vec%dvaluew' % i).expr = (
        "1.0 if %s > 0.001 else 0.0" % D('crack%d' % i))

_pv = len(PLANTS)
setattr(crack_src.par, 'vec%dname' % _pv, 'uParams')
getattr(crack_src.par, 'vec%dvaluex' % _pv).expr = D('ctime')
getattr(crack_src.par, 'vec%dvaluey' % _pv).expr = "parent().par.Crackamt"
getattr(crack_src.par, 'vec%dvaluez' % _pv).expr = D('bass')
getattr(crack_src.par, 'vec%dvaluew' % _pv).val = ASPECT

setattr(crack_src.par, 'vec%dname' % (_pv + 1), 'uGrade')
getattr(crack_src.par, 'vec%dvaluex' % (_pv + 1)).expr = "parent().par.Vignette"
# moss creeps out from every crack as the garden fills
getattr(crack_src.par, 'vec%dvaluey' % (_pv + 1)).expr = (
    "parent().par.Moss * %s" % D('fullness'))

# ---------------------------------------------------------------------------
# PLANTS — one L-System per plant, generations animated 0 -> GENMAX
# ---------------------------------------------------------------------------
rules = C(textDAT, 'plant_rules', 0, 100)
# Classic bushy plant (Prusinkiewicz & Lindenmayer, fig 1.24d). Note the Rules DAT
# wants NO space after ':' or '=' — with one it silently produces zero geometry.
# A spray, not a shrub. Measured by what fraction of branch tips land in the top
# third of the plant - i.e. how much it reads as a bunch rather than a bush:
#   A=F[+A]F[-A]A      (the old shrub)  0.18  - flowers scattered all over
#   A=FF[+A][-A]                        0.52
#   A=F[++A][--A]A     (this one)       0.84  - stems fan up and bloom in a crown
# The FFFF premise is the bare stem rising out of the crack before it fans.
# The /(137) roll is the golden angle, the same divergence real phyllotaxis uses.
# Without it every branch stays in one plane and the crown is a flat cut-out:
# measured depth (z extent / height) 0.11 flat vs 0.54 with the roll, and it bunches
# the tips slightly better too (topfrac 0.84 -> 0.86).
rules.text = "premise:FFFFA\nA=/(137)F[++A][--A]~(9)A\n"

# Tubes, not a wireframe skeleton: flat constant-width lines read as a wire mesh no
# matter what colour they are, while lit tapered tubes read as stems. 12k points at
# Gens 6 costs ~0.9ms to cook, so it is well inside budget.
stem_mat = C(phongMAT, 'mat_stem', 0, -60)
soft(stem_mat, diffr=0.28, diffg=0.56, diffb=0.22,
     ambr=0.10, ambg=0.19, ambb=0.08,
     specr=0.18, specg=0.24, specb=0.13, shininess=16.0)
# A small, clamped warm-up as the track gets loud - unclamped it drove the bush neon.
if hasattr(stem_mat.par, 'diffr'):
    stem_mat.par.diffr.expr = "0.26 + 0.08 * min(1.0, %s)" % D('energy')
    stem_mat.par.diffg.expr = "0.52 + 0.14 * min(1.0, %s)" % D('energy')

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
           angleinit=16.0, stepinit=0.1, stepscale=0.99, anglescale=0.84,
           randscale=0.30, randseed=seed, contangl=True, contlength=True,
           # 81 long stems converge at the crown, so they merge into a solid canopy
           # far sooner than 729 lacy branchlets did: measured silhouette coverage
           # 0.05 -> 0.8%, 0.08 -> 1.8%, 0.16 -> 4.0% (solid green mushroom).
           contwidth=True, thickinit=0.075, thickscale=0.88,
           rows=3, cols=6, smooth=0.4)
    ls.par.rules = rules.path
    ls.par.generations.expr = "%.2f * %s" % (GENMAX, D('grow%d' % i))

    # A second, static copy at full growth: flower sites are read off this, so they
    # stay put while the animated one grows. Constant params -> cooks once.
    lsf = C(lsystemSOP, 'plant%d_full' % i, 170, y - 80, type='skel',
            angleinit=16.0, stepinit=0.1, stepscale=0.99, anglescale=0.84,
            randscale=0.30, randseed=seed, contangl=True, contlength=True,
            generations=GENMAX)
    lsf.par.rules = rules.path
    lsf.cook(force=True)
    ys_ = [pt.P[1] for pt in lsf.points] or [0.0, 1.0]
    span = max(1e-6, max(ys_) - min(ys_))
    scl = height / span

    # A finished plant must stop re-cooking: its `generations` expression reads the
    # director, which cooks every frame, so the SOP is dirtied every frame even when
    # the value has not moved. A Switch SOP only cooks its selected input, so once
    # the plant is grown the animated L-System is not evaluated at all. With four
    # plants that is the difference between ~4ms and ~1ms of L-System per frame.
    lsg = C(lsystemSOP, 'plant%d_grown' % i, 170, y - 160, type='tube',
            angleinit=16.0, stepinit=0.1, stepscale=0.99, anglescale=0.84,
            randscale=0.30, randseed=seed, contangl=True, contlength=True,
            contwidth=True, thickinit=0.075, thickscale=0.88,
            rows=3, cols=6, smooth=0.4, generations=GENMAX)
    lsg.par.rules = rules.path

    swi = C(switchSOP, 'plant%d_switch' % i, 340, y - 80)
    W(ls, swi, 0)
    W(lsg, swi, 1)
    swi.par.input.expr = "1 if %s >= 0.999 else 0" % D('grow%d' % i)

    geo = C(geometryCOMP, 'plant%d_geo' % i, 340, y, tx=px, ty=py, tz=0.0)
    # The premise (FFFF) is drawn even at generations 0, so a plant that has not
    # started yet would still show a bare stem standing on the bare wall. Scaling the
    # whole COMP up over the first few percent of growth both hides it beforehand and
    # reads as the stem pushing up out of the crack.
    emerge = "min(1.0, %s / 0.06)" % D('grow%d' % i)
    for axis in ('sx', 'sy', 'sz'):
        getattr(geo.par, axis).expr = "%.6f * %s" % (scl, emerge)
    geo.par.material = stem_mat.path
    # A slow sway that leans with the music, shared with the flowers and bees.
    geo.par.rz.expr = D('sway%d' % i)
    ins = geo.op('torus1')
    if ins:
        ins.destroy()
    sel = geo.create(inSOP, 'in_stem') if False else None
    # Pull the L-System in with a Select SOP so the geometry lives outside the COMP.
    sel = geo.create(selectSOP, 'stem')
    sel.par.sop = swi.path
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
sites_src.text = '''# Flower anchors: the TRUE branch tips of each fully grown L-System, in world space.
#
# A tip is a node with exactly ONE segment touching it - not "the last vertex of a
# prim". Measured on one plant: 82 real tips (degree 1, heights 0.71-1.00 of the
# plant) against 41 prim end-points of which exactly ONE was a real tip, the rest
# being interior junctions at heights 0.55-0.88. Using prim ends put every flower in
# the middle of the crown with the outer stems left bare.
#
# Depends only on the static *_full SOPs, so it cooks when the plant definition
# changes and then stops.
PLANTS = %r
MAXSITES = %d


def _key(P):
    return (round(P[0], 4), round(P[1], 4), round(P[2], 4))


def onCook(scriptOp):
    pts = []
    budget = max(1, MAXSITES // max(1, len(PLANTS)))
    for pid, (px, py, scl, seed) in enumerate(PLANTS):
        sop = op('plant%%d_full' %% pid)
        if sop is None:
            continue

        nbr = {}
        for prim in sop.prims:
            for i in range(len(prim) - 1):
                ka = _key(prim[i].point.P)
                kb = _key(prim[i + 1].point.P)
                if ka == kb:
                    continue
                nbr.setdefault(ka, []).append(kb)
                nbr.setdefault(kb, []).append(ka)
        if not nbr:
            continue

        ys = [k[1] for k in nbr]
        lo, hi = min(ys), max(ys)
        span = max(1e-6, hi - lo)

        # The root is degree 1 as well, so drop anything still down at the base.
        tips = [k for k, v in nbr.items()
                if len(v) == 1 and (k[1] - lo) / span > 0.15]
        tips.sort(key=lambda k: -k[1])

        for j, k in enumerate(tips[:budget]):
            nb = nbr[k][0]
            dx, dy = k[0] - nb[0], k[1] - nb[1]
            dl = (dx * dx + dy * dy) ** 0.5 or 1.0
            r = ((j * 2654435761) %% 10007) / 10007.0
            pts.append((px + k[0] * scl, py + k[1] * scl, k[2] * scl,
                        r, float(pid), scl, dx / dl, dy / dl))

    scriptOp.clear()
    names = ['tx', 'ty', 'tz', 'rnd', 'pid', 'pscl', 'ux', 'uy']
    chans = [scriptOp.appendChan(n) for n in names]
    scriptOp.numSamples = max(1, len(pts))
    if not pts:
        for c in chans:
            c[0] = 0.0
        return
    for j, pt in enumerate(pts):
        for c, v in zip(chans, pt):
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
finst_src.text = '''# Per-flower transform + colour, one numpy pass per frame.
import numpy as np

NPLANTS = %d
BASES = %r
PSCLREF = %.5f     # the tallest plant's geometry scale


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
    pscl = np.array(sites['pscl'].vals, dtype=np.float32) / PSCLREF
    ux = np.array(sites['ux'].vals, dtype=np.float32)
    uy = np.array(sites['uy'].vals, dtype=np.float32)
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
    swaydeg = np.zeros(n, dtype=np.float32)
    basex = np.zeros(n, dtype=np.float32)
    basey = np.zeros(n, dtype=np.float32)
    for i in range(NPLANTS):
        m = (pid == i)
        if not m.any():
            continue
        bloom[m] = dc('bloom%%d' %% i)
        dens[m] = dc('dens%%d' %% i)
        swaydeg[m] = dc('sway%%d' %% i)
        basex[m] = BASES[i][0]
        basey[m] = BASES[i][1]

    # Push the bloom out ALONG its branch so its base meets the tip and the head sits
    # beyond it, instead of the quad straddling the tip and burying half the flower in
    # the foliage. Done before the sway rotation so the offset rotates with it.
    reach = (0.042 + 0.030 * np.mod(rnd * 3.7, 1.0)) \
        * float(par.Flowersize.eval()) * (0.55 + 0.45 * pscl) * 0.55
    tx = tx + ux * reach
    ty = ty + uy * reach

    # Rotate each flower about its own plant's base by exactly the angle the plant
    # COMP is rotating by, so blossom stays welded to the stem tip it grew on.
    ang = np.radians(swaydeg)
    ca, sa = np.cos(ang), np.sin(ang)
    dx, dy = tx - basex, ty - basey
    tx = basex + dx * ca - dy * sa
    ty = basey + dx * sa + dy * ca

    # Each flower opens at its own moment inside the bloom window, and only the
    # fraction of sites allowed by this plant's density ever opens at all.
    delay = np.mod(rnd * 7.13, 1.0)
    local = np.clip((bloom - delay * 0.55) / 0.45, 0.0, 1.0)
    local = local * local * (3.0 - 2.0 * local)
    allowed = (rnd < dens).astype(np.float32)

    # A bud is just an unopened flower: once the stem carrying it has grown, show it
    # small and green, then let it swell and take on its colour as it opens. Cheaper
    # and better looking than a separate bud instancer, and it means the crown is
    # never bare while the plant waits for its bloom window.
    budded = np.zeros(n, dtype=np.float32)
    for i in range(NPLANTS):
        m = (pid == i)
        if m.any():
            budded[m] = dc('grow%%d' %% i)
    budded = np.clip((budded - 0.45) / 0.55, 0.0, 1.0) * allowed
    openness = np.maximum(local, 0.0)

    # overshoot then settle - flowers pop rather than fade in
    pop = 1.0 + 0.35 * np.sin(np.clip(local, 0.0, 1.0) * np.pi) * (1.0 - local)
    # blooms scale with their plant too, so a small plant is not all flower
    head = (0.042 + 0.030 * np.mod(rnd * 3.7, 1.0)) * size * (0.55 + 0.45 * pscl)
    # a third of full size as a bud, swelling to full as it opens
    scale = budded * (0.32 + 0.68 * openness) * pop * head
    scale = scale * (1.0 + 0.16 * bass)

    # a small per-flower nod on top of the plant's sway, so they are not rigid
    nod = 0.004 * np.sin(t * 1.3 + rnd * 12.0) * local
    rot = (np.mod(rnd * 360.0, 360.0) + swaydeg
           + 8.0 * np.sin(t * 0.7 + rnd * 5.0))

    # Cream / butter / coral / rose - warm hues that sit with the brick rather than
    # fighting it. Only the top of the range goes properly pink.
    h = np.mod(rnd * 2.7, 1.0)
    cr = 1.00 - 0.06 * h
    cg = 0.86 - 0.46 * h + 0.08 * energy
    cb = 0.58 - 0.16 * h + 0.12 * np.mod(rnd * 5.1, 1.0)
    lift = (0.80 + 0.20 * min(1.0, energy))
    # green while closed, its own colour once open
    cr = cr * openness + 0.34 * (1.0 - openness)
    cg = cg * openness + 0.52 * (1.0 - openness)
    cb = cb * openness + 0.24 * (1.0 - openness)

    scriptOp.numSamples = n
    # ortho camera: a constant z only changes occlusion, never screen position.
    # In front of the leaves, which are in front of the stems.
    data = [tx + nod, ty, np.full(n, 0.45, dtype=np.float32),
            scale, scale, scale, rot,
            cr * lift, cg * lift, cb * lift]
    for c, v in zip(chans, data):
        c.vals = np.asarray(v, dtype=np.float32).tolist()
    return
''' % (len(PLANTS), [(pl[0], pl[1]) for pl in PLANTS], max(plant_scales))

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
BASES = %r


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
    bass = dc('bass')
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
    # the flowers are swaying, so the points the bees orbit have to sway with them
    for i in range(NPLANTS):
        m = (pid == i)
        if not m.any():
            continue
        a = np.radians(dc('sway%%d' %% i))
        bx0, by0 = BASES[i]
        dx, dy = ftx[m] - bx0, fty[m] - by0
        ftx[m] = bx0 + dx * np.cos(a) - dy * np.sin(a)
        fty[m] = by0 + dx * np.sin(a) + dy * np.cos(a)

    idx = np.arange(nb)
    # Spread the bees EVENLY over the whole live-site list. The old fixed stride of 7
    # only walked `7 * nb` entries into it, and since sites are ordered by plant that
    # meant the later plants never got a single bee: measured at 8 plants, picks ran
    # index 3..178 of 230 live sites and the per-plant tally was [7,6,7,6,0,0,0,0].
    pos = (idx + 0.5) * len(live) / float(max(1, nb))
    pick = live[np.clip(pos.astype(np.int32), 0, len(live) - 1)]
    ax = ftx[pick]
    ay = fty[pick]
    apid = pid[pick]

    r1 = np.mod(np.sin(idx * 12.9898) * 43758.5453, 1.0)
    r2 = np.mod(np.sin(idx * 78.233) * 12345.6789, 1.0)
    r3 = np.mod(np.sin(idx * 39.425) * 24634.6345, 1.0)

    # Rhythmic, not frantic. Three things were making the swarm read as jitter:
    # per-bee rates spread over 2.5x, the treble band multiplying the orbital SPEED,
    # and wobble at non-integer harmonics (1.3 / 2.7 / 3.1) that never resolved.
    # Now every bee shares one orbital rate with only a slight spread, the beat
    # breathes the orbit radius instead of the speed, and the wobble sits on exact
    # 2x and 0.5x harmonics so it repeats with the orbit.
    TAU = 6.283185307179586
    rate = float(par.Beespeed.eval()) * 1.05 * (0.94 + 0.12 * r1)
    ang = t * rate + r2 * TAU

    breathe = 1.0 + 0.18 * bass
    rad = (0.070 + 0.045 * r3) * breathe

    ox = np.cos(ang) * rad
    oy = np.sin(ang) * rad * 0.62            # flattened ellipse, same frequency
    ox = ox + 0.010 * np.sin(ang * 2.0 + r3 * TAU)
    oy = oy + 0.008 * np.cos(ang * 2.0 + r2 * TAU)
    oy = oy + 0.013 * np.sin(ang * 0.5 + r1 * TAU)   # slow hover, half the orbit

    arrive = beeenv[np.clip(apid, 0, NPLANTS - 1)]
    arrive = np.clip((arrive - r1 * 0.35) / 0.65, 0.0, 1.0)
    arrive = arrive * arrive * (3.0 - 2.0 * arrive)

    # fly in from just off the sides
    entry_x = np.where(r2 > 0.5, 1.35, -1.35)
    entry_y = ay + (r3 - 0.5) * 0.5
    bx = entry_x + (ax + ox - entry_x) * arrive
    by = entry_y + (ay + oy - entry_y) * arrive

    sz = arrive * (0.026 + 0.014 * r3)
    # heading from the ellipse tangent, so the bee tilts into its travel direction
    rz = np.degrees(np.arctan2(np.cos(ang) * 0.62, -np.sin(ang)))

    scriptOp.numSamples = nb
    # in front of everything - they are flying around the plant, not inside it
    data = [bx, by, np.full(nb, 0.60, dtype=np.float32), sz, sz, sz, rz]
    for c, v in zip(chans, data):
        c.vals = np.asarray(v, dtype=np.float32).tolist()
    return
''' % (len(PLANTS), MAXBEES, [(pl[0], pl[1]) for pl in PLANTS])

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
    vec3 bodycol = mix(vec3(0.88, 0.64, 0.16), vec3(0.09, 0.06, 0.04), stripe * 0.92);

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

# Sprite quads come from a GRID SOP, not rectangleSOP + textureSOP.
# rectangleSOP's own `texture` toggle produces no uv attribute at all on this build,
# and a Texture SOP in 'rowcol' mode on a single 4-vertex polygon produces garbage:
# measured uv = (1.0,0.5) (1.333,0.5) (0.667,0.5) (1.0,0.5) — v pinned at 0.5, u
# running outside 0..1, so every sprite was drawing one horizontal slice of its
# texture stretched across the quad. gridSOP at rows=2 cols=2 with texture='rowcol'
# gives the expected (0,0) (1,0) (0,1) (1,1).
flower_quad = C(gridSOP, 'flower_quad', 1300, 40, rows=2, cols=2,
                sizex=1.0, sizey=1.0, texture='rowcol')
bee_quad = C(gridSOP, 'bee_quad', 1300, -120, rows=2, cols=2,
             sizex=1.0, sizey=0.62, texture='rowcol')

mat_flower = C(constantMAT, 'mat_flower', 1300, 110)
mat_flower.par.colormap = flower_tex.path
# depthtest ON, depthwriting OFF is the textbook transparent-surface setup, and it is
# what actually puts the blossom in front. depthtest=False does NOT mean "draw on
# top" - it means the fragment ignores its own (correct, nearer) depth, and under the
# render TOP's order-independent transparency the stems then won.
soft(mat_flower, alpha=1.0, blending=True, depthtest=True, depthwriting=False)

mat_bee = C(constantMAT, 'mat_bee', 1300, -50)
mat_bee.par.colormap = bee_tex.path
soft(mat_bee, alpha=1.0, blending=True, depthtest=True, depthwriting=False)

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
# LEAVES — instanced along the stems, unfurling as growth passes them
# ---------------------------------------------------------------------------
leaf_sites_src = C(textDAT, 'leaf_sites_src', 500, -240)
leaf_sites_src.text = '''# Leaf anchors: interior points along the stems, with the local stem direction so a
# leaf can sit ON its stem rather than floating near it. Reads the static full-growth
# skeleton, so this cooks when the plant definition changes and then stops.
PLANTS = %r
MAXLEAVES = %d


def onCook(scriptOp):
    pts = []
    budget = max(1, MAXLEAVES // max(1, len(PLANTS)))
    for pid, (px, py, scl, seed) in enumerate(PLANTS):
        sop = op('plant%%d_full' %% pid)
        if sop is None:
            continue
        cand = []
        for prim in sop.prims:
            n = len(prim)
            if n < 3:
                continue
            for k in range(0, n - 1):
                a = prim[k].point.P
                b = prim[k + 1].point.P
                dx, dy = b[0] - a[0], b[1] - a[1]
                # Sample ALONG each segment, not just at its vertices. The bare stem
                # below the crown is only four long segments, so vertex-only
                # candidates leave most height bands empty and the leaves all end up
                # in the flower head again.
                for u in (0.18, 0.42, 0.66, 0.90):
                    cand.append((a[0] + dx * u, a[1] + (b[1] - a[1]) * u,
                                 a[2] + (b[2] - a[2]) * u, dx, dy))
        if not cand:
            continue
        ys = [c[1] for c in cand]
        lo, hi = min(ys), max(ys)
        span = max(1e-6, hi - lo)

        # Spread the leaves evenly by HEIGHT, not evenly through the candidate list.
        # Branching multiplies segments towards the crown, so most candidates live up
        # there and sampling the list evenly piles every leaf into the flower head,
        # leaving the stems bare. Bucketing by height band puts leaves up the stem
        # the way a real plant carries them.
        top = 0.78
        chosen = []
        for b in range(budget):
            h0 = lo + span * top * (b / float(budget))
            h1 = lo + span * top * ((b + 1) / float(budget))
            band = [c for c in cand if h0 <= c[1] < h1]
            if band:
                chosen.append((b, band[(b * 7919) %% len(band)]))

        for k, c in chosen:
            ex, ey, ez, dx, dy = c
            import math as _m
            ang = _m.degrees(_m.atan2(dy, dx))
            r = ((k * 2654435761) %% 10007) / 10007.0
            # Strict alternation at a fixed angle marches up the stem as a regular
            # chevron. Letting the per-leaf random break the alternation and widen
            # the angle, with a slight downward droop, reads as foliage instead.
            side = 1.0 if ((k %% 2 == 0) != (r > 0.72)) else -1.0
            pts.append((px + ex * scl, py + ey * scl, ez * scl,
                        ang + side * (32.0 + 58.0 * r) - 10.0, r, float(pid),
                        (ey - lo) / span, scl))

    scriptOp.clear()
    names = ['tx', 'ty', 'tz', 'rz', 'rnd', 'pid', 'hgt', 'pscl']
    chans = [scriptOp.appendChan(n) for n in names]
    scriptOp.numSamples = max(1, len(pts))
    if not pts:
        for c in chans:
            c[0] = 0.0
        return
    for j, pt in enumerate(pts):
        for c, v in zip(chans, pt):
            c[j] = v
    return
''' % (
    [(PLANTS[i][0], PLANTS[i][1], plant_scales[i], PLANTS[i][3])
     for i in range(len(PLANTS))], MAXLEAVES)

leaf_sites = C(scriptCHOP, 'leaf_sites', 660, -240)
leaf_sites.par.callbacks = leaf_sites_src.path

leaf_inst_src = C(textDAT, 'leaf_inst_src', 820, -240)
leaf_inst_src.text = '''# Leaves unfurl as the stem that carries them grows past them, and rotate with the
# plant's sway exactly like the flowers do.
import numpy as np

NPLANTS = %d
BASES = %r
PSCLREF = %.5f     # the tallest plant's geometry scale


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

    def dc(name, default=0.0):
        try:
            return float(d[name][0])
        except Exception:
            return default

    n = sites.numSamples
    tx = np.array(sites['tx'].vals, dtype=np.float32)
    ty = np.array(sites['ty'].vals, dtype=np.float32)
    tz = np.array(sites['tz'].vals, dtype=np.float32)
    rz = np.array(sites['rz'].vals, dtype=np.float32)
    rnd = np.array(sites['rnd'].vals, dtype=np.float32)
    hgt = np.array(sites['hgt'].vals, dtype=np.float32)
    pscl = np.array(sites['pscl'].vals, dtype=np.float32) / PSCLREF
    pid = np.array(sites['pid'].vals, dtype=np.float32).astype(np.int32)

    grow = np.zeros(n, dtype=np.float32)
    swaydeg = np.zeros(n, dtype=np.float32)
    basex = np.zeros(n, dtype=np.float32)
    basey = np.zeros(n, dtype=np.float32)
    for i in range(NPLANTS):
        m = (pid == i)
        if not m.any():
            continue
        grow[m] = dc('grow%%d' %% i)
        swaydeg[m] = dc('sway%%d' %% i)
        basex[m] = BASES[i][0]
        basey[m] = BASES[i][1]

    t = dc('ctime')
    energy = dc('energy')

    # A leaf opens only once growth has reached its height on the stem.
    local = np.clip((grow - hgt * 0.85) / 0.18, 0.0, 1.0)
    local = local * local * (3.0 - 2.0 * local)

    ang = np.radians(swaydeg)
    ca, sa = np.cos(ang), np.sin(ang)
    dx, dy = tx - basex, ty - basey
    tx = basex + dx * ca - dy * sa
    ty = basey + dx * sa + dy * ca

    # lower leaves are older, so they are larger; the newest near the crown are small
    # Leaf size follows the plant it grows on. Fixed world-size leaves made the
    # short plants read as stacked green chevrons rather than foliage.
    size = ((0.030 + 0.038 * (1.0 - hgt)) + 0.030 * rnd) * local * pscl \
        * float(par.Leafsize.eval())
    flutter = 7.0 * np.sin(t * 1.1 + rnd * 9.0) * local
    rot = rz + swaydeg + flutter

    shade = 0.80 + 0.45 * rnd
    lift = 0.95 + 0.25 * min(1.0, energy)
    cr = 0.30 * shade * lift
    cg = 0.62 * shade * lift
    cb = 0.24 * shade * lift

    # The camera is ORTHOGRAPHIC, so translating in z does not move anything on
    # screen - it only decides what occludes what. The stems are a 3D spray spanning
    # z -0.20..+0.21, so leaves and blossom sitting at their own tip's z had half the
    # plant drawing in front of them. Parking each layer at a fixed depth in front of
    # the stems is free and fixes it outright.
    scriptOp.numSamples = n
    data = [tx, ty, np.full(n, 0.30, dtype=np.float32),
            size, size, size, rot, cr, cg, cb]
    for c, v in zip(chans, data):
        c.vals = np.asarray(v, dtype=np.float32).tolist()
    return
''' % (
    len(PLANTS), [(pl[0], pl[1]) for pl in PLANTS], max(plant_scales))

leaf_inst = C(scriptCHOP, 'leaf_inst', 980, -240)
leaf_inst.par.callbacks = leaf_inst_src.path
W(leaf_sites, leaf_inst, 0)
W(director, leaf_inst, 1)

leaf_tex = C(glslTOP, 'leaf_tex', 1140, -240)
res(leaf_tex, 128, 128)
leaf_dat = C(textDAT, 'leaf_tex_pixel', 1140, -310)
leaf_dat.text = '''// A pointed leaf, attached at u=0 and tapering to a tip at u=1. The quad is offset so
// u=0 sits on the stem, which means the leaf pivots at its base like a real one
// instead of spinning about its middle.
out vec4 fragColor;

void main() {
    float t = clamp(vUV.s, 0.0, 1.0);             // 0 at the stem, 1 at the tip
    float y = vUV.t * 2.0 - 1.0;                  // -1..1 across the blade

    // broad a third of the way along, drawn to a point at the tip
    float w = 0.46 * pow(max(sin(3.14159265 * pow(t, 0.80)), 0.0), 1.15);
    float d = abs(y) - w;
    float m = 1.0 - smoothstep(-0.02, 0.02, d);

    float across = abs(y) / max(w, 1e-3);         // 0 on the midrib, 1 at the edge
    float rib = 1.0 - smoothstep(0.0, 0.12, abs(y));
    // chevron veins running out from the midrib toward the tip
    float veins = 0.5 + 0.5 * sin((t * 9.0 - abs(y) * 5.0) * 3.14159265);

    vec3 deep = vec3(0.15, 0.30, 0.12);
    vec3 pale = vec3(0.42, 0.66, 0.28);
    vec3 col = mix(pale, deep, smoothstep(0.15, 1.0, across));
    col *= 0.93 + 0.07 * veins;
    col = mix(col, pale * 1.15, rib * 0.40);
    col *= 0.85 + 0.25 * (1.0 - t);               // slightly darker toward the tip

    fragColor = TDOutputSwizzle(vec4(col * m, m));
}
'''
leaf_tex.par.pixeldat = leaf_dat.path

# tx = 0.5 puts the quad's near edge on the origin, so an instanced leaf hangs off
# its stem point rather than being centred on it. UVs come from the grid's rows and
# columns, so shifting the geometry does not disturb them.
leaf_quad = C(gridSOP, 'leaf_quad', 1300, -240, rows=2, cols=2,
              sizex=1.0, sizey=0.52, tx=0.5, texture='rowcol')

mat_leaf = C(constantMAT, 'mat_leaf', 1300, -180)
mat_leaf.par.colormap = leaf_tex.path
soft(mat_leaf, alpha=1.0, blending=True, depthtest=True, depthwriting=False)

leaves = C(geometryCOMP, 'leaves', 1460, -240)
lq = leaves.op('torus1')
if lq:
    lq.destroy()
lsel = leaves.create(selectSOP, 'quad')
lsel.par.sop = leaf_quad.path
lsel.render = True
lsel.display = True
leaves.par.material = mat_leaf.path
leaves.par.instancing = True
leaves.par.instanceop = leaf_inst.path
for _p, _v in (('instancetx', 'tx'), ('instancety', 'ty'), ('instancetz', 'tz'),
               ('instancesx', 'sx'), ('instancesy', 'sy'), ('instancesz', 'sz'),
               ('instancerz', 'rz')):
    soft(leaves, **{_p: _v})
soft(leaves, instancecolormode='multiply', instancer='cr',
     instanceg='cg', instanceb='cb')

# ---------------------------------------------------------------------------
# RENDER + COMPOSITE
# ---------------------------------------------------------------------------
cam = C(cameraCOMP, 'cam', 1620, -60, projection='ortho', tz=4.0)
soft(cam, orthowidth=ORTHOW, near=0.1, far=20.0)

# THREE passes, not one. Inside a single render TOP the blossom kept losing to the
# stems no matter what: depth ordering did not decide it (flowers parked at z=3.0,
# right against the camera, still drew behind stems at z<=0.2), and neither
# transparency mode changed it. Compositing separate passes in 2D is unconditional -
# what is in front is simply whatever is composited last.
def R(name, geo, x, y):
    o = C(renderTOP, name, x, y)
    res(o)
    o.par.camera = cam.path
    o.par.geometry = geo
    o.par.lights = 'light_sun light_fill'
    o.par.bgcolora = 0.0
    soft(o, antialias='msaa4x', transparency='sortedblending')
    return o


render = R('render_plants',
           ' '.join('plant%d_geo' % i for i in range(len(PLANTS))) + ' leaves',
           1780, -60)
render_bloom = R('render_bloom', 'flowers', 1780, 60)
render_bees = R('render_bees', 'bees', 1780, 180)

# wall <- plants <- blossom <- bees, each strictly over the last
comp_pl = C(compositeTOP, 'comp_plants', 1940, 180, operand='over')
res(comp_pl)
W(render, comp_pl, 0)   # top layer first for compositeTOP 'over'
W(crack_src, comp_pl, 1)

comp_bl = C(compositeTOP, 'comp_bloom', 1940, 240, operand='over')
res(comp_bl)
W(render_bloom, comp_bl, 0)
W(comp_pl, comp_bl, 1)

comp = C(compositeTOP, 'comp_scene', 1940, 300, operand='over')
res(comp)
W(render_bees, comp, 0)
W(comp_bl, comp, 1)

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
pexec = C(parameterexecuteDAT, 'checkpoint_exec', 1940, 1000)
pexec.text = '''# Checkpoints are SEEKS, not freeze-frames. showtime = monotonic clock - Timeoffset,
# so jumping to time T is just Timeoffset = clock_now - T; nothing pauses, and the
# story carries on playing from wherever it lands.
CHECKPOINTS = %r


def _seek(comp, seconds):
    # Seeking is a subtraction on the playhead, never a transport command - which is
    # why the story carries on playing from wherever it lands. Measured against
    # MUSICAL time, so a checkpoint means the same place in the story at any tempo.
    d = comp.op('director')
    mus = float(d['musical'][0]) if d is not None and d.numChans else 0.0
    comp.par.Timeoffset = mus - seconds


def _current_index(comp):
    scenelen = max(1.0, float(comp.par.Scenelen.eval()))
    d = comp.op('director')
    show = float(d['show'][0]) if d is not None and d.numChans else 0.0
    here = show / scenelen
    idx = 0
    for i, (_n, _l, mult) in enumerate(CHECKPOINTS):
        if mult <= here + 1e-4:
            idx = i
    return idx


def onPulse(par):
    comp = par.owner
    n = par.name
    scenelen = max(1.0, float(comp.par.Scenelen.eval()))
    names = [c[0] for c in CHECKPOINTS]

    if n == 'Restart':
        _seek(comp, 0.0)
    elif n == 'Nextcp':
        _seek(comp, CHECKPOINTS[(_current_index(comp) + 1) %% len(CHECKPOINTS)][2]
              * scenelen)
    elif n == 'Prevcp':
        _seek(comp, CHECKPOINTS[(_current_index(comp) - 1) %% len(CHECKPOINTS)][2]
              * scenelen)
    elif n.startswith('Go'):
        want = n[2:].lower()
        if want in names:
            _seek(comp, CHECKPOINTS[names.index(want)][2] * scenelen)
    return
''' % (CHECKPOINTS,)
pexec.par.op = s.path
soft(pexec, pars='Restart Nextcp Prevcp ' + ' '.join('Go' + cp[0]
                                                     for cp in CHECKPOINTS),
     valuechange=False, onpulse=True)

# --- keyboard: 1-9 seek to a checkpoint, 0 restarts the story ----------------
keyin = C(keyboardinDAT, 'key_checkpoint', 1780, 880)
keyin.par.keys = ' '.join(str(d) for d in range(10))
# TD auto-docks a <name>_callbacks Text DAT when the op is created; reuse it.
kcb = keyin.par.callbacks.eval()
if kcb is None:
    kcb = C(textDAT, 'key_checkpoint_callbacks', 1780, 800)
    keyin.par.callbacks = kcb.path
kcb.nodeX, kcb.nodeY = 1780, 800
kcb.text = '''# 1-9 seek to a checkpoint and let the story keep playing; 0 restarts from a bare
# wall. These are chapter marks in one continuous four-minute arc, not stages.
CHECKPOINTS = %r


def onKey(dat, keyInfo):
    if not keyInfo.state:          # key-up; act once, on the press
        return
    comp = dat.parent()
    k = keyInfo.key
    if k == '0':
        comp.par.Restart.pulse()
    elif k in '123456789':
        i = int(k) - 1
        if i < len(CHECKPOINTS):
            getattr(comp.par, 'Go' + CHECKPOINTS[i][0]).pulse()
    return


def onShortcut(dat, shortcutName, time):
    return
''' % (CHECKPOINTS,)

frame_exec = C(executeDAT, 'frame_exec', 2100, 1000)
frame_exec.text = '''# TD only cooks what something is pulling on. With the scene's output not on screen,
# nothing pulls the director, so the story clock and the beat detector simply stop -
# measured: cookFrame stuck at 246 while the project was on frame 374990. Cooking the
# director once per frame keeps musical time and tempo detection running regardless of
# what is being displayed, and costs one CHOP cook.


def onFrameStart(frame):
    d = op('director')
    if d is not None:
        d.cook()
    return
'''
soft(frame_exec, framestart=True)

s.par.display = True
s.par.opviewer = final_out.path

timer.par.initialize.pulse()
timer.par.start.pulse()
# Start the story at the bare wall rather than wherever TD's uptime happens to sit.
director.cook(force=True)
try:
    s.par.Timeoffset = float(director['musical'][0])
except Exception:
    s.par.Timeoffset = 0.0

print('built %s' % s.path)
print('  wall photo: %s' % (wall_path or 'NOT FOUND'))
print('  plants: %d   scene length: %.0fs   full story: %.0fs'
      % (len(PLANTS), s.par.Scenelen.eval(),
         s.par.Scenelen.eval() * ((len(PLANTS) - 1) * STAGGER + 1.3)))
print('  checkpoints: %s' % ', '.join('%d=%s' % (i + 1, cp[0])
                                      for i, cp in enumerate(CHECKPOINTS)))
print('  director chans: %s' % [c.name for c in director.chans()])
print('  flower sites: %d   leaf sites: %d' % (sites.numSamples,
                                                 leaf_sites.numSamples))
