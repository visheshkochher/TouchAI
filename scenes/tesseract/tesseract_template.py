# Tesseract — a camera travelling through the inside of a four-dimensional lattice,
# for a long techno set. Amon Tobin's ISAM by way of the tesseract in Interstellar.
#
# THE WORLD IS THE TESSERACT. As in Interstellar, the lattice has no outside: rooms
# repeat in every direction, the camera flies down it, and threads of light — world
# lines — stream along the direction of travel with packets of information running
# down them. A hypercube turns in four dimensions around the camera, and its
# timelines are extruded behind it: every vertex trails its own past orientations,
# which is what slit-scan does to time.
#
# ISAM IS THE SURFACE. The faces of the lattice cells light up from inside, amber
# panels and circuit-board traces, Tetris-stacked; the palette can go to Tron cyan
# or an engine-room red; a drop tears the frame with glitch, and the whole corridor
# FOLDS: the lattice itself is embedded in four dimensions and rotated through w.
#
# BUILT FOR A LONG SET. Six programs (corridor, hypercube, stack, stargate,
# bookshelf, fold) are sets of parameters, not scenes: every parameter morphs over
# two beats, so a change is a transformation of the one world, never a cut. The
# program is re-chosen at random on phrase boundaries, always on a drop, and the
# palette with it; small things flip every eight beats; a breakdown is detected and
# the world slows and thins around the turning hypercube until the kick returns.
#
# EVERYTHING IS A LINE. One instanced unit segment, fed by one numpy engine; the
# 3D and the 4D are done in Python and projected there. No particles.
#
# BUILT TO RUN ALL NIGHT: Script CHOP channels are built once and then only written;
# every list is capped and aged; every phase wraps (the camera position is an
# integer cell counter modulo 2^20 plus a fraction); shaders get a wrapped clock.
#
# Idempotent: destroys and recreates /project1/tesseract and its project-level Out
# TOP, and touches nothing else. No media files.
#     code = open('scenes/tesseract/build.py', encoding='utf-8').read()
#     g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
#
# GENERATED: this file is tesseract_template.py + verbatim blocks of
# scenes/homestead/build.py (BEGIN/END HOMESTEAD), assembled by gen_tesseract.py.

import math
import os

SCENE = 'tesseract'
OUTW, OUTH = 1280, 720
ASPECT = OUTW / OUTH
ORTHOW = 2.0
ORTHOH = ORTHOW / ASPECT
CLOCKLEN = 60.0
STORYDEF = 600.0          # the director needs a story length; this piece has no story
MAXSEG = 14000

# name, parameters, palettes it may choose from
PROGS = [
    ('CORRIDOR', dict(spd=0.90, hol=0.0, xl=1.0, yl=1.0, zl=1.0, occ=0.92, lit=0.22,
                      tes=0.06, hyp=0.0, strd=0.35, weave=0.0, pk=0.5, fold=0.12,
                      roll=0.04, sway=0.25, trl=0.45, scr=0.0, fog=5.5,
                      pw0=0.6, pw1=0.4, pw2=0.0), ('AMBER', 'TRON', 'BONE')),
    ('HYPERCUBE', dict(spd=0.35, hol=1.0, xl=0.6, yl=0.6, zl=0.6, occ=0.55, lit=0.06,
                       tes=0.12, hyp=1.0, strd=0.25, weave=0.0, pk=0.4, fold=0.22,
                       roll=0.12, sway=0.15, trl=0.60, scr=0.0, fog=4.5,
                       pw0=1.0, pw1=0.0, pw2=0.0), ('BONE', 'TRON', 'SEPIA')),
    ('STACK', dict(spd=0.45, hol=1.0, xl=1.0, yl=1.0, zl=0.8, occ=0.60, lit=0.65,
                   tes=0.0, hyp=0.0, strd=0.15, weave=0.0, pk=0.3, fold=0.06,
                   roll=0.0, sway=0.5, trl=0.35, scr=0.2, fog=5.0,
                   pw0=0.5, pw1=0.5, pw2=0.0), ('AMBER', 'ALERT', 'CIRCUIT')),
    ('STARGATE', dict(spd=2.40, hol=1.0, xl=0.12, yl=0.12, zl=1.0, occ=0.85, lit=0.12,
                      tes=0.0, hyp=0.0, strd=1.0, weave=0.0, pk=1.0, fold=0.08,
                      roll=0.30, sway=0.1, trl=0.88, scr=0.0, fog=8.0,
                      pw0=0.0, pw1=1.0, pw2=0.0), ('TRON', 'BONE', 'ALERT')),
    ('BOOKSHELF', dict(spd=0.55, hol=1.0, xl=0.8, yl=0.8, zl=0.9, occ=0.85, lit=0.4,
                       tes=0.03, hyp=0.0, strd=0.5, weave=0.6, pk=0.6, fold=0.16,
                       roll=0.02, sway=0.2, trl=0.50, scr=0.45, fog=4.5,
                       pw0=0.0, pw1=0.0, pw2=1.0), ('SEPIA',)),
    ('FOLD', dict(spd=0.80, hol=1.0, xl=0.8, yl=0.8, zl=0.8, occ=0.75, lit=0.25,
                  tes=0.2, hyp=0.5, strd=0.5, weave=0.3, pk=0.6, fold=0.85,
                  roll=0.08, sway=0.3, trl=0.65, scr=0.1, fog=6.0,
                  pw0=0.4, pw1=0.4, pw2=0.2), ('CIRCUIT', 'TRON', 'AMBER', 'BONE')),
]
# lattice, lit panels, threads, tesseracts, hot highlights, background
PALETTES = {
    'AMBER':   ((0.42, 0.52, 0.70), (1.00, 0.60, 0.20), (1.00, 0.85, 0.60),
                (0.75, 0.85, 1.00), (1.00, 0.90, 0.75), (0.020, 0.018, 0.030)),
    'SEPIA':   ((0.80, 0.60, 0.36), (1.00, 0.80, 0.45), (1.00, 0.93, 0.78),
                (0.60, 0.75, 0.95), (1.00, 0.95, 0.85), (0.030, 0.020, 0.012)),
    'TRON':    ((0.15, 0.75, 1.00), (1.00, 0.25, 0.75), (0.60, 1.00, 1.00),
                (1.00, 0.50, 0.90), (0.80, 1.00, 1.00), (0.005, 0.012, 0.030)),
    'ALERT':   ((0.85, 0.12, 0.08), (1.00, 0.55, 0.15), (1.00, 0.90, 0.85),
                (1.00, 0.30, 0.25), (1.00, 1.00, 1.00), (0.028, 0.004, 0.004)),
    'BONE':    ((0.80, 0.80, 0.84), (0.62, 0.45, 1.00), (1.00, 1.00, 1.00),
                (0.70, 0.60, 1.00), (1.00, 1.00, 1.00), (0.012, 0.010, 0.022)),
    'CIRCUIT': ((0.45, 0.30, 0.85), (0.35, 1.00, 0.55), (0.80, 1.00, 0.85),
                (0.55, 1.00, 0.75), (0.90, 1.00, 0.90), (0.010, 0.006, 0.022)),
}
PALNAMES = ('AMBER', 'SEPIA', 'TRON', 'ALERT', 'BONE', 'CIRCUIT')

proj = op('/project1')
for stale in (SCENE, SCENE + '_out'):
    o = proj.op(stale)
    if o:
        o.destroy()

s = proj.create(containerCOMP, SCENE)
s.nodeX, s.nodeY = 0, -5000
s.par.w, s.par.h = OUTW, OUTH


#@INCLUDE def C(type_, name, x, y, **params):|||# ---------------------------------------------------------------------------\n# PERFORMANCE SURFACE


# ---------------------------------------------------------------------------
# PERFORMANCE SURFACE
# ---------------------------------------------------------------------------
pg = s.appendCustomPage('Tesseract')
pg.appendMenu('Audiosrc', label='Audio Source')
s.par.Audiosrc.menuNames = ['device', 'file']
s.par.Audiosrc.menuLabels = ['Audio Device In', 'Audio File In (test)']
s.par.Audiosrc = 'file'

for nm, label, val, lo, hi in [
    ('Reactivity', 'Reactivity',          1.0, 0.0, 3.0),
    ('Devgain',    'Device In Gain',      6.0, 1.0, 30.0),
    ('Storylen',   'Clock Length (s)', STORYDEF, 60.0, 2400.0),
    ('Refbpm',     'Reference BPM',     128.0, 60.0, 200.0),
    ('Beatdrive',  'Beat Drive',          1.0, 0.0, 1.0),
    ('Timeoffset', 'Time Offset (s)',     0.0, -600.0, 3000.0),
    ('Speed',      'Travel Speed',        1.0, 0.0, 3.0),
    ('Changeprob', 'Program Change Chance per Phrase', 0.55, 0.0, 1.0),
    ('Phrase',     'Phrase Length (beats)', 32.0, 8.0, 128.0),
    ('Linewidth',  'Line Width (px)',     1.3, 0.5, 4.0),
    ('Ink',        'Brightness of Lines', 1.0, 0.0, 2.0),
    ('Glow',       'Glow',                1.0, 0.0, 3.0),
    ('Trails',     'Trails',              1.0, 0.0, 1.3),
    ('Glitchamt',  'Glitch',              1.0, 0.0, 2.0),
    ('Foldamt',    'Fold (4D)',           1.0, 0.0, 2.0),
    ('Label',      'Program Readout',     0.7, 0.0, 1.0),
    ('Vignette',   'Vignette',            0.8, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

_RO = [('Bpm', 0, 200), ('Showt', 0, 2400), ('Program', 0, len(PROGS)),
       ('Beat', 0, 1e9), ('Segs', 0, MAXSEG), ('Trail', 0, 1), ('Zoomtr', 0.9, 1.2),
       ('Scrape', 0, 1), ('Scrapea', 0, 7), ('Trot', -1, 1), ('Glitch', 0, 2),
       ('Gseed', 0, 1000), ('Flash', 0, 1), ('Bgr', 0, 1), ('Bgg', 0, 1), ('Bgb', 0, 1),
       ('Brk', 0, 1), ('Tclk', 0, 1000), ('Labelfade', 0, 1), ('Cellsps', 0, 50),
       ('Bassm', 0, 1), ('Highm', 0, 1), ('Energym', 0, 1)]
for _mn, _lo, _hi in _RO:
    pg.appendFloat(_mn, label=_mn)
    _p = getattr(s.par, _mn)
    _p.normMin, _p.normMax = _lo, _hi
    _p.readOnly = True

pg.appendToggle('Loop', label='Loop the Clock')
s.par.Loop.default = True
s.par.Loop.val = True
pg.appendToggle('Hold', label='H - HOLD THE PROGRAM (no automatic changes)')
s.par.Hold.val = False
pg.appendToggle('Reverse', label='R - REVERSE THE TRAVEL')
s.par.Reverse.val = False
pg.appendStr('Scaletxt', label='Readout')
s.par.Scaletxt.readOnly = True
s.par.Scaletxt.val = ''

for i, (nm, _pp, _pl) in enumerate(PROGS):
    pg.appendPulse('Prog%d' % (i + 1), label='%d - %s' % (i + 1, nm))
pg.appendPulse('Auto', label='0 - AUTOMATIC (release a held or forced program)')
pg.appendPulse('Foldnow', label='F - FOLD (rotate the lattice through w)')
pg.appendPulse('Glitchnow', label='G - GLITCH')
pg.appendPulse('Pulsenow', label='P - PULSE (a shockwave down the lattice)')
pg.appendPulse('Palette', label='C - NEXT PALETTE')
pg.appendPulse('Newprog', label='N - NEW (random program, new lattice)')

# ---------------------------------------------------------------------------
# AUDIO FRONT END, CLOCK, TEMPO — verbatim from homestead
# ---------------------------------------------------------------------------
#@INCLUDE adev = C(audiodeviceinCHOP|||# ---------------------------------------------------------------------------\n# DIRECTOR

# ---------------------------------------------------------------------------
# DIRECTOR — verbatim from homestead. It supplies the envelopes and the event
# counters; its playhead is unused (this piece has no story). Its verb queue is
# unused too: this scene's verbs go to the engine through 'qverbs'.
# ---------------------------------------------------------------------------
#@INCLUDE DIRECTOR_BODY = '''|||def D(ch):


def D(ch):
    return "(op('director')['%s'] or 0)" % ch


# ---------------------------------------------------------------------------
# THE ENGINE — the lattice, its lit faces, the threads, the hypercubes, the fold
# ---------------------------------------------------------------------------
ENGINE_BODY = r'''# Everything is a line segment. The world is built every frame, but only the window
# of it around the camera, and always as whole numpy arrays:
#
#   the lattice   lines at every half-integer x and y, and every integer z, in a
#                 window 2NX x 2NY cells across and NZ cells deep. The camera sits
#                 in the middle of the cross-section and moves along +z; its position
#                 is an integer cell counter plus a fraction, so the window is
#                 recomputed from nothing each frame and nothing accumulates.
#   the faces     the walls, floor and ceiling of the channel the camera flies down.
#                 Some light up from inside, in one of five patterns.
#   the threads   world lines along z (and, in the bookshelf, along x), plucked by
#                 the kick, with packets of light running down them.
#   the cubes     small tesseracts in some cells, and one big one around the camera,
#                 all turning in four dimensions.
#
# Then one pipeline for all of it: camera-relative -> view rotation -> THE FOLD (a
# rotation through w, then a w-perspective) -> near clip -> perspective -> glitch.
import math
import random
import numpy as np

_S = {'S': None}
_PUB = {'built': False}
TAU = 2.0 * math.pi
NPROG = len(PROGS)
PNAMES = [p[0] for p in PROGS]
PKEYS = sorted(PROGS[0][1].keys())


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


# --- the tesseract ------------------------------------------------------------------
TV = np.array([[a, b, c, d] for a in (-1.0, 1.0) for b in (-1.0, 1.0)
               for c in (-1.0, 1.0) for d in (-1.0, 1.0)])
TEI = np.array([(i, j) for i in range(16) for j in range(i + 1, 16)
                if int(np.sum(TV[i] != TV[j])) == 1])          # 32 edges


def _tess(ang):
    """16 vertices rotated in the xw, yw, zw and xy planes, then projected from 4D
    to 3D by a w-perspective: the inner cube is the far side in w."""
    V = TV.copy()
    for a, b, th in ((0, 3, ang[0]), (1, 3, ang[1]), (2, 3, ang[2]), (0, 1, ang[3])):
        c, s_ = math.cos(th), math.sin(th)
        va, vb = V[:, a].copy(), V[:, b].copy()
        V[:, a] = va * c - vb * s_
        V[:, b] = va * s_ + vb * c
    k = TD4 / (TD4 - V[:, 3])
    return V[:, :3] * k[:, None]


# --- face patterns, in face coordinates (u along z, v across), [0, 1]^2 --------------
def _pat_panel():
    out = []
    for m in (0.04, 0.16, 0.29, 0.40):
        out += [(m, m, 1 - m, m), (1 - m, m, 1 - m, 1 - m), (1 - m, 1 - m, m, 1 - m),
                (m, 1 - m, m, m)]
    return out


def _pat_circuit(seed):
    rs = random.Random(seed)
    out = [(0.04, 0.04, 0.96, 0.04), (0.96, 0.04, 0.96, 0.96), (0.96, 0.96, 0.04, 0.96),
           (0.04, 0.96, 0.04, 0.04)]
    for _ in range(4):
        x, y = rs.choice((0.04, 0.96)), rs.uniform(0.15, 0.85)
        pts = [(x, y)]
        for k in range(3):
            if k % 2 == 0:
                x = rs.uniform(0.2, 0.8)
            else:
                y = rs.uniform(0.2, 0.8)
            pts.append((x, y))
        for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
            out.append((a, b, c, d))
        cx, cy = pts[-1]
        out += [(cx - 0.03, cy - 0.03, cx + 0.03, cy - 0.03), (cx + 0.03, cy - 0.03, cx + 0.03, cy + 0.03),
                (cx + 0.03, cy + 0.03, cx - 0.03, cy + 0.03), (cx - 0.03, cy + 0.03, cx - 0.03, cy - 0.03)]
    return out


def _pat_books():
    rs = random.Random(7)
    out = [(0.02, 0.04, 0.98, 0.04), (0.02, 0.50, 0.98, 0.50), (0.02, 0.96, 0.98, 0.96)]
    for lo in (0.04, 0.50):
        u = 0.05
        while u < 0.95:
            h = rs.uniform(0.22, 0.42)
            out.append((u, lo, u, lo + h))
            u += rs.uniform(0.035, 0.075)
    return out


PATS = [np.array(_pat_panel()), np.array(_pat_circuit(1)), np.array(_pat_circuit(2)),
        np.array(_pat_circuit(3)), np.array(_pat_books())]


# --- state ----------------------------------------------------------------------------
def _new(seed):
    rs = random.Random(seed)
    S = {
        'rs': rs, 'seed': rs.random() * 1000.0, 'last': {}, 'lastraw': None,
        'cz_i': 0, 'cz_f': 0.0, 'ph1': 0.0, 'ph2': 0.3, 'fph': 0.0, 'roll': 0.0,
        'rolldir': 1.0, 'fplane': 2, 'fdir': 1.0, 'foldenv': 0.0,
        'ta': [0.0, 0.7, 1.3, 0.2], 'ha': [0.3, 0.0, 0.9, 0.0],
        'bph': 0.0, 'beat': 0, 'prog': 0, 'pal': 'AMBER', 'holdto': -1,
        'P': dict(PROGS[0][1]), 'T': dict(PROGS[0][1]),
        'pal_c': np.array(PALETTES['AMBER'], dtype=np.float64),
        'pulses': [], 'gl': 0.0, 'gseed': 0.0, 'gtick': 0, 'surge': 0.0, 'flash': 0.0,
        'pluck': 0.0, 'inbrk': False, 'esh': 0.0, 'elo': 0.3, 'quiet': 0.0, 'brk': 0.0,
        'scra': 0.0, 'clk': 0.0, 'labt': -99.0, 'labtxt': '', 'lastlab': '',
        'errs': 0, 'lastout': None, 'census': '',
    }
    return S


def _switch(S, n, raw, why=''):
    S['prog'] = n
    S['T'] = dict(PROGS[n][1])
    S['pal'] = S['rs'].choice(PROGS[n][2])
    S['labt'] = raw


def _on_beat(S, par, raw):
    b = S['beat']
    rs = S['rs']
    if b % 8 == 0:                       # small things flip every eight beats
        if rs.random() < 0.30:
            S['fplane'] = rs.choice((0, 1, 2))
        if rs.random() < 0.25:
            S['rolldir'] = -S['rolldir']
        if rs.random() < 0.35:
            S['scra'] = rs.uniform(0.0, TAU)
    phrase = max(4, int(round(float(par.Phrase.eval()))))
    held = bool(par.Hold.eval()) or b < S['holdto']
    if b % phrase == 0 and not held and rs.random() < float(par.Changeprob.eval()):
        choices = [i for i in range(NPROG) if i != S['prog']]
        if S['brk'] > 0.5:                # in a breakdown, prefer the quiet ones
            choices = [i for i in choices if PNAMES[i] in ('HYPERCUBE', 'BOOKSHELF', 'FOLD')] or choices
        _switch(S, rs.choice(choices), raw)


# --- the world, as arrays ----------------------------------------------------------------
def _fogv(z, fog):
    return (np.exp(-np.maximum(0.0, z - 1.0) / max(fog, 0.5)) *
            np.clip((NZ - z) / 3.0, 0.0, 1.0) * np.clip((z + 0.6), 0.0, 1.0))


def _lattice(S, P, out):
    xs = np.arange(-NX, NX) + 0.5
    ys = np.arange(-NY, NY) + 0.5
    ks = np.arange(-1, NZ + 1)
    zr = ks - S['cz_f']
    kab = ((S['cz_i'] + ks) % 4096).astype(np.float64)
    sd = S['seed']
    hol = P['hol']
    # z-lines
    X, Y, K = np.meshgrid(xs, ys, np.arange(len(ks) - 1), indexing='ij')
    X, Y, K = X.ravel(), Y.ravel(), K.ravel()
    zl = np.column_stack([X, Y, zr[K], X, Y, zr[K + 1]])
    idz = X * 13.1 + Y * 7.7 + kab[K] * 1.618 + sd
    # x-lines
    I, Y2, K2 = np.meshgrid(np.arange(len(xs) - 1), ys, np.arange(len(ks)), indexing='ij')
    I, Y2, K2 = I.ravel(), Y2.ravel(), K2.ravel()
    xl = np.column_stack([xs[I], Y2, zr[K2], xs[I + 1], Y2, zr[K2]])
    idx = xs[I] * 3.3 + Y2 * 11.9 + kab[K2] * 2.71 + sd + 100.3
    # y-lines
    X3, J, K3 = np.meshgrid(xs, np.arange(len(ys) - 1), np.arange(len(ks)), indexing='ij')
    X3, J, K3 = X3.ravel(), J.ravel(), K3.ravel()
    yl = np.column_stack([X3, ys[J], zr[K3], X3, ys[J + 1], zr[K3]])
    idy = X3 * 5.9 + ys[J] * 17.3 + kab[K3] * 3.14 + sd + 200.7
    A = np.vstack([zl, xl, yl])
    ids = np.concatenate([idz, idx, idy])
    dirw = np.concatenate([np.full(len(zl), P['zl']), np.full(len(xl), P['xl']),
                           np.full(len(yl), P['yl'])])
    mx = (A[:, 0] + A[:, 3]) * 0.5
    my = (A[:, 1] + A[:, 4]) * 0.5
    mz = (A[:, 2] + A[:, 5]) * 0.5
    al = np.clip((P['occ'] - _hs(ids)) * 6.0, 0.0, 1.0) * dirw
    hy = min(hol, 1.0)
    inside = (np.abs(mx) < hol + 0.49) & (np.abs(my) < hy + 0.49)
    al = np.where(inside, al * _cl(1.0 - (hol - 0.25) * 3.0), al)
    al *= _fogv(mz, P['fog'])
    hot = np.zeros(len(A))
    for p in S['pulses']:
        front = p[0] * PV
        hot += p[1] * (1.0 - p[0] / PLIFE) * np.exp(-((mz - front) / 0.6) ** 2)
    keep = al > 0.004
    out.append((A[keep], al[keep] * 0.55, 0, hot[keep]))


def _faces(S, P, E, out):
    H = int(round(P['hol']))
    Hy = min(H, 1)
    ks = np.arange(0, NZ)
    zr = ks - S['cz_f']
    kab = ((S['cz_i'] + ks) % 4096).astype(np.float64)
    ycell = np.arange(-NY, NY - 1) + 0.5
    xcell = np.arange(-NX, NX - 1) + 0.5
    O, E1, E2, FID = [], [], [], []
    for sg in (-1.0, 1.0):
        Y, K = np.meshgrid(ycell, np.arange(len(ks)), indexing='ij')
        Y, K = Y.ravel(), K.ravel()
        n = len(Y)
        O.append(np.column_stack([np.full(n, sg * (H + 0.5)), Y, zr[K]]))
        E1.append(np.tile([0.0, 0.0, 1.0], (n, 1)))
        E2.append(np.tile([0.0, 1.0, 0.0], (n, 1)))
        FID.append(sg * 31.7 + Y * 5.3 + kab[K] * 1.93)
        X, K = np.meshgrid(xcell, np.arange(len(ks)), indexing='ij')
        X, K = X.ravel(), K.ravel()
        n = len(X)
        O.append(np.column_stack([X, np.full(n, sg * (Hy + 0.5)), zr[K]]))
        E1.append(np.tile([0.0, 0.0, 1.0], (n, 1)))
        E2.append(np.tile([1.0, 0.0, 0.0], (n, 1)))
        FID.append(sg * 57.1 + X * 8.9 + kab[K] * 2.37 + 500.0)
    O, E1, E2, FID = np.vstack(O), np.vstack(E1), np.vstack(E2), np.concatenate(FID)
    FID = FID + S['seed']
    step = float(S['beat'] // 2)
    h = _hs(FID + step * 7.13)
    lit = min(1.0, P['lit'] + 0.35 * S['brk'])
    on = np.clip((lit - h) * 6.0, 0.0, 1.0)
    flick = np.where(_hs(FID * 1.7 + step) < 0.5, E['kickenv'], 0.35 + 0.3 * E['bass'])
    zmid = O[:, 2] + 0.5
    a = on * (0.30 + 0.55 * flick + 0.2 * E['high']) * _fogv(zmid, P['fog'])
    m = a > 0.01
    if not m.any():
        return
    O, E1, E2, a, FID = O[m], E1[m], E2[m], a[m], FID[m]
    # which pattern: panel, one of three circuits, or books
    hp = _hs(FID * 1.37)
    w0, w1, w2 = P['pw0'], P['pw1'], P['pw2']
    tot = max(1e-6, w0 + w1 + w2)
    c0, c1 = w0 / tot, (w0 + w1) / tot
    pid = np.where(hp < c0, 0, np.where(hp < c1, 1 + (_hs(FID * 2.9) * 3).astype(int), 4))
    for p in range(5):
        mm = pid == p
        if not mm.any():
            continue
        T = PATS[p]
        o, e1, e2 = O[mm][:, None, :], E1[mm][:, None, :], E2[mm][:, None, :]
        p0 = o + T[None, :, 0:1] * e1 + T[None, :, 1:2] * e2
        p1 = o + T[None, :, 2:3] * e1 + T[None, :, 3:4] * e2
        seg = np.concatenate([p0, p1], axis=2).reshape(-1, 6)
        aa = np.repeat(a[mm], len(T))
        out.append((seg, aa, 1, np.full(len(seg), 0.15 * E['kickenv'])))


def _threads(S, P, E, t, out):
    ns = NSTR
    i = np.arange(ns, dtype=np.float64)
    sd = S['seed']
    vis = np.clip((P['strd'] - _hs(i * 0.917 + sd)) * 5.0, 0.0, 1.0)
    m = vis > 0.01
    if m.any():
        ii = i[m]
        vv = vis[m]
        bx = (_hs(ii * 1.31 + sd) * 2.0 - 1.0) * (NX - 0.6)
        by = (_hs(ii * 2.17 + sd) * 2.0 - 1.0) * (NY - 0.6)
        zp = np.linspace(-0.5, NZ, NPTS)
        wz = zp[None, :] + S['cz_f'] + float(S['cz_i'] % 4096)
        ph = _hs(ii * 3.7)[:, None] * TAU
        amp = 0.03 + 0.14 * E['bass'] + 0.22 * S['pluck']
        dx = amp * np.sin(wz * 0.9 + t * 1.3 + ph) + 0.05 * np.sin(wz * 0.23 + ph)
        dy = amp * 0.7 * np.cos(wz * 1.1 - t * 0.9 + ph)
        X = bx[:, None] + dx
        Y = by[:, None] + dy
        Z = np.broadcast_to(zp[None, :], X.shape)
        seg = np.stack([X[:, :-1], Y[:, :-1], Z[:, :-1], X[:, 1:], Y[:, 1:], Z[:, 1:]],
                       axis=2).reshape(-1, 6)
        zm = (seg[:, 2] + seg[:, 5]) * 0.5
        aa = np.repeat(vv, NPTS - 1) * _fogv(zm, P['fog'] * 1.4) * (0.45 + 0.35 * E['high'])
        out.append((seg, aa, 2, np.zeros(len(seg))))
        # packets of light, running down each thread toward the camera
        npk = 3
        pk = P['pk'] * (0.35 + 0.65 * E['high'])
        if pk > 0.02:
            j = np.arange(npk, dtype=np.float64)
            spd = 0.35 + 0.5 * _hs(ii * 4.1)[:, None]
            u = (t * spd * 0.25 + _hs(ii[:, None] * 5.3 + j[None, :] * 0.37)) % 1.0
            zz = (NZ * (1.0 - u)).ravel()
            show = (_hs(ii[:, None] * 6.1 + j[None, :] * 1.9) < pk).ravel()
            xx = np.repeat(bx, npk)
            yy = np.repeat(by, npk)
            wzz = zz + S['cz_f'] + float(S['cz_i'] % 4096)
            phr = np.repeat(ph[:, 0], npk)
            xx = xx + amp * np.sin(wzz * 0.9 + t * 1.3 + phr) + 0.05 * np.sin(wzz * 0.23 + phr)
            yy = yy + amp * 0.7 * np.cos(wzz * 1.1 - t * 0.9 + phr)
            seg = np.column_stack([xx, yy, zz, xx, yy, zz + 0.45])[show]
            aa = (np.repeat(vv, npk) * _fogv(zz, P['fog'] * 1.4))[show] * pk
            out.append((seg, aa, 4, np.full(len(seg), 0.4)))
    # the bookshelf's weave: threads across x, at fixed places in the world
    if P['weave'] > 0.02:
        ks = np.arange(0, NZ)
        kab = ((S['cz_i'] + ks) % 4096).astype(np.float64)
        rows = []
        for r in range(2):
            hsel = _hs(kab * 1.77 + r * 9.1 + sd)
            mm = hsel < P['weave'] * 0.6
            if not mm.any():
                continue
            kk = ks[mm]
            yv = (_hs(kab[mm] * 2.3 + r) * 2.0 - 1.0) * (NY - 0.7)
            zv = kk - S['cz_f'] + _hs(kab[mm] * 3.1 + r)
            xp = np.linspace(-NX + 0.5, NX - 0.5, 15)
            vib = (0.03 + 0.18 * S['pluck']) * np.sin(xp[None, :] * 2.1 + t * 3.0 + kk[:, None])
            Y = yv[:, None] + vib
            X = np.broadcast_to(xp[None, :], Y.shape)
            Z = np.broadcast_to(zv[:, None], Y.shape)
            seg = np.stack([X[:, :-1], Y[:, :-1], Z[:, :-1], X[:, 1:], Y[:, 1:], Z[:, 1:]],
                           axis=2).reshape(-1, 6)
            aa = np.repeat(_fogv(zv, P['fog']), 14) * 0.6 * min(1.0, P['weave'])
            rows.append((seg, aa))
        for seg, aa in rows:
            out.append((seg, aa, 2, np.zeros(len(seg))))


def _cubes(S, P, E, t, out):
    # small ones, in cells
    if P['tes'] > 0.01:
        xc = np.arange(-NX, NX - 1) + 1.0
        yc = np.arange(-NY, NY - 1) + 1.0
        ks = np.arange(0, NZ)
        X, Y, K = np.meshgrid(xc, yc, ks, indexing='ij')
        X, Y, K = X.ravel(), Y.ravel(), K.ravel()
        kab = ((S['cz_i'] + K) % 4096).astype(np.float64)
        on = np.clip((P['tes'] - _hs(X * 4.1 + Y * 9.7 + kab * 1.13 + S['seed'] + 300.0)) * 6.0,
                     0.0, 1.0)
        hol = P['hol']
        path = (np.abs(X) < max(hol, 0.0) + 0.5) & (np.abs(Y) < min(hol, 1.0) + 0.5)
        on = np.where(path, 0.0, on)
        Z = K - S['cz_f'] + 0.5
        a = on * _fogv(Z, P['fog'])
        m = a > 0.01
        if m.any():
            V = _tess(S['ta']) * TSC
            Ed = V[TEI]                                              # (32, 2, 3)
            C = np.column_stack([X[m], Y[m], Z[m]])
            seg = (C[:, None, None, :] + Ed[None]).reshape(-1, 6)
            out.append((seg, np.repeat(a[m], 32) * 0.9, 3,
                        np.full(len(seg), 0.25 * E['kickenv'])))
    # the big one, around the camera, with its timelines extruded behind it
    hyp = min(1.0, P['hyp'] + 0.9 * S['brk'])
    if hyp > 0.01:
        c = np.array([0.0, 0.0, HZ])
        V0 = _tess(S['ha']) * HSC
        Ed = V0[TEI]
        seg = (c[None, None, :] + Ed).reshape(-1, 6)
        out.append((seg, np.full(len(seg), hyp), 3, np.full(len(seg), 0.3 * E['kickenv'])))
        prev = V0
        rows = []
        for k in range(1, TRN + 1):
            ang = [S['ha'][q] - k * TRDA * (1.0 + q * 0.3) for q in range(4)]
            Vk = _tess(ang) * HSC
            Vk = Vk + np.array([0.0, 0.0, k * TRDZ])
            Vp = prev + (np.array([0.0, 0.0, (k - 1) * TRDZ]) if k > 1 else 0.0)
            rows.append((np.column_stack([Vp, Vk]) + np.concatenate([c, c])[None, :],
                         hyp * 0.55 * (1.0 - k / (TRN + 1.0)) ** 1.4))
            prev = _tess(ang) * HSC
        for sg, aa in rows:
            out.append((sg, np.full(len(sg), aa), 2, np.zeros(len(sg))))


# --- the pipeline -----------------------------------------------------------------------
def _pipeline(S, P, E, parts, t, par):
    if not parts:
        return np.zeros((0, 8))
    A = np.vstack([p[0] for p in parts])
    al = np.concatenate([p[1] for p in parts])
    cls = np.concatenate([np.full(len(p[0]), p[2], dtype=int) for p in parts])
    hot = np.concatenate([p[3] for p in parts])
    # the camera: a weave and a roll, and the channel is centred on it
    camx = 0.30 * P['sway'] * math.sin(TAU * S['ph1'])
    camy = 0.18 * P['sway'] * math.sin(TAU * S['ph2'])
    yaw = 0.10 * P['sway'] * math.cos(TAU * S['ph1']) + 0.03 * E['kickenv'] * math.sin(t * 17.0)
    pitch = 0.06 * P['sway'] * math.cos(TAU * S['ph2'])
    roll = S['roll']
    out = []
    for a0 in (0, 3):
        x = A[:, a0] - camx
        y = A[:, a0 + 1] - camy
        z = A[:, a0 + 2]
        cy, sy = math.cos(yaw), math.sin(yaw)
        x, z = x * cy - z * sy, x * sy + z * cy
        cp, sp = math.cos(pitch), math.sin(pitch)
        y, z = y * cp - z * sp, y * sp + z * cp
        cr, sr = math.cos(roll), math.sin(roll)
        x, y = x * cr - y * sr, x * sr + y * cr
        # THE FOLD: embed in 4D with a small w bulge, rotate through w, project back
        th = S['fth']
        if abs(th) > 1e-4 or S['bulge'] > 1e-4:
            q = [x / FS, y / FS, z / FS]
            w0 = S['bulge'] * np.sin(z * 0.55 + t * 0.3)
            pl = S['fplane']
            c_, s_ = math.cos(th), math.sin(th)
            qa = q[pl]
            q[pl] = qa * c_ - w0 * s_
            w = qa * s_ + w0 * c_
            k = FD / np.maximum(FD - w, 0.35)
            x, y, z = q[0] * FS * k, q[1] * FS * k, q[2] * FS
        out.append((x, y, z))
    (x0, y0, z0), (x1, y1, z1) = out
    keep = ((z0 > NEAR) | (z1 > NEAR)) & (al > 0.004)
    x0, y0, z0, x1, y1, z1 = x0[keep], y0[keep], z0[keep], x1[keep], y1[keep], z1[keep]
    al, cls, hot = al[keep], cls[keep], hot[keep]
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
    f = FOCAL * (1.0 + 0.07 * E['kickenv'])
    pal = S['pal_c']
    col = pal[cls] + np.clip(hot, 0.0, 2.0)[:, None] * pal[4][None, :] * 0.9
    B = np.column_stack([f * x0 / z0, f * y0 / z0, f * x1 / z1, f * y1 / z1, col, al])
    # GLITCH: horizontal bands torn sideways, and a red/cyan echo
    G = S['gl'] * float(par.Glitchamt.eval())
    if G > 0.02 and len(B):
        ym = (B[:, 1] + B[:, 3]) * 0.5
        band = np.floor(ym * (10.0 + 30.0 * _h1(S['gseed'])) + S['gseed'])
        hb = _hs(band * 3.1 + S['gseed'])
        on = _hs(band * 7.7 + S['gseed'] * 1.3) < 0.2 + 0.5 * min(G, 1.0)
        sh = (hb - 0.5) * 0.45 * G * on
        B[:, 0] += sh
        B[:, 2] += sh
        e = _hs(np.arange(len(B)) * 0.37 + S['gseed']) < 0.35 * min(G, 1.0)
        if e.any():
            R = B[e].copy()
            Cc = B[e].copy()
            R[:, [0, 2]] += 0.012 * G
            Cc[:, [0, 2]] -= 0.012 * G
            R[:, 4:7] = (1.0, 0.1, 0.15)
            Cc[:, 4:7] = (0.1, 0.9, 1.0)
            R[:, 7] *= 0.5
            Cc[:, 7] *= 0.5
            B = np.vstack([B, R, Cc])
    return B


# --- one frame ----------------------------------------------------------------------------
def _frame(scriptOp):
    d = scriptOp.inputs[0] if scriptOp.inputs else None
    comp = scriptOp.parent()
    par = comp.par
    S = _S['S']
    if S is None:
        S = _S['S'] = _new(SEED0)

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
    bpm = float(par.Bpm.eval()) or float(par.Refbpm.eval())
    bpm = max(60.0, min(200.0, bpm))
    bp = 60.0 / bpm
    S['clk'] = (S['clk'] + dt) % 1000.0
    t = S['clk']
    rs = S['rs']
    E = {'bass': bass, 'high': high, 'energy': energy, 'kickenv': kickenv,
         'dropenv': dropenv}

    # verbs from the keys and pads
    fold = glitch = pulse = False
    q = comp.fetch('qverbs', None)
    if q:
        comp.store('qverbs', [])
        for v in q[:16]:
            if v.startswith('prog'):
                n = int(v[4:]) - 1
                if 0 <= n < NPROG:
                    _switch(S, n, raw)
                    S['holdto'] = S['beat'] + 64
            elif v == 'auto':
                S['holdto'] = -1
            elif v == 'fold':
                fold = True
            elif v == 'glitch':
                glitch = True
            elif v == 'pulse':
                pulse = True
            elif v == 'palette':
                S['pal'] = PALNAMES[(PALNAMES.index(S['pal']) + 1) % len(PALNAMES)]
                S['labt'] = raw
            elif v == 'new':
                S['seed'] = rs.random() * 1000.0
                _switch(S, rs.choice([i for i in range(NPROG) if i != S['prog']]), raw)
                glitch = True

    # the beat clock, and what happens on it
    S['bph'] += dt / bp
    while S['bph'] >= 1.0:
        S['bph'] -= 1.0
        S['beat'] += 1
        _on_beat(S, par, raw)

    # breakdowns: the energy falls well under its own recent level and stays there
    S['esh'] += (energy - S['esh']) * min(1.0, dt / 0.6)
    S['elo'] += (energy - S['elo']) * min(1.0, dt / 10.0)
    low = S['esh'] < 0.5 * max(S['elo'], 0.12) or S['esh'] < 0.08
    S['quiet'] = S['quiet'] + dt if low else 0.0
    brk_t = 1.0 if S['quiet'] > 2.5 else 0.0
    if (brk_t > 0.5) != S['inbrk']:        # entering or leaving one shows the readout
        S['inbrk'] = brk_t > 0.5
        S['labt'] = raw
    S['brk'] += (brk_t - S['brk']) * min(1.0, dt / (2.0 if brk_t > S['brk'] else 0.7))

    # events
    S['gl'] *= 0.5 ** (dt / 0.30)
    S['surge'] *= 0.5 ** (dt / 1.2)
    S['flash'] *= 0.5 ** (dt / 0.25)
    S['foldenv'] *= 0.5 ** (dt / 1.8)
    S['pluck'] *= 0.5 ** (dt / 0.35)
    if kicks or pulse:
        S['pulses'].append([0.0, 0.8 + 0.8 * beatstr if not pulse else 1.6])
        S['pluck'] = max(S['pluck'], 0.4 + 0.6 * beatstr)
        for k in range(4):
            S['ta'][k] = (S['ta'][k] + 0.18 * (1.0 + k * 0.3)) % TAU
    if accents and rs.random() < 0.15 * float(par.Glitchamt.eval()):
        S['gl'] = max(S['gl'], 0.35)
    if drops or fold:
        S['foldenv'] = 1.0
        S['fdir'] = rs.choice((-1.0, 1.0))
        S['fplane'] = rs.choice((0, 1, 2))
    if drops or glitch:
        S['gl'] = 1.0
        S['flash'] = 1.0
    if drops:
        S['surge'] = 1.0
        S['seed'] = rs.random() * 1000.0
        S['pulses'].append([0.0, 2.2])
        if not par.Hold.eval() and S['beat'] >= S['holdto'] and rs.random() < 0.75:
            _switch(S, rs.choice([i for i in range(NPROG) if i != S['prog']]), raw)
    for p in S['pulses']:
        p[0] += dt
    S['pulses'] = [p for p in S['pulses'] if p[0] < PLIFE][-PULSEMAX:]
    S['gtick'] = (S['gtick'] + 1) % 1000
    if S['gtick'] % 3 == 0:
        S['gseed'] = rs.random() * 997.0

    # the program morphs, two beats at a time
    P, T = S['P'], S['T']
    k = min(1.0, dt / (2.0 * bp))
    for key in PKEYS:
        P[key] += (T[key] - P[key]) * k
    S['pal_c'] += (np.array(PALETTES[S['pal']]) - S['pal_c']) * k

    # travel, and every phase wrapped
    cells = (P['spd'] * (bpm / 60.0) * 0.5 * (0.55 + 0.6 * energy) * (1.0 + 1.3 * S['surge'])
             * (1.0 - 0.75 * S['brk']) * float(par.Speed.eval()))
    sgn = -1.0 if par.Reverse.eval() else 1.0
    S['cz_f'] += cells * dt * sgn
    while S['cz_f'] >= 1.0:
        S['cz_f'] -= 1.0
        S['cz_i'] = (S['cz_i'] + 1) % 1048576
    while S['cz_f'] < 0.0:
        S['cz_f'] += 1.0
        S['cz_i'] = (S['cz_i'] - 1) % 1048576
    S['ph1'] = (S['ph1'] + dt / (16.0 * bp)) % 1.0
    S['ph2'] = (S['ph2'] + dt / (22.0 * bp)) % 1.0
    S['fph'] = (S['fph'] + dt / (32.0 * bp)) % 1.0
    S['roll'] = (S['roll'] + dt * P['roll'] * S['rolldir'] * (0.6 + bass) * 0.8) % TAU
    spin = 0.35 + 1.4 * bass + 0.8 * S['surge']
    for kk, rate in enumerate((0.31, 0.23, 0.17, 0.05)):
        S['ta'][kk] = (S['ta'][kk] + dt * rate * spin * 1.6) % TAU
        S['ha'][kk] = (S['ha'][kk] + dt * rate * (0.45 + 0.9 * bass + 0.4 * S['brk'])) % TAU
    famt = float(par.Foldamt.eval())
    S['fth'] = famt * (P['fold'] * 0.55 * math.sin(TAU * S['fph'])
                       + S['foldenv'] * 1.25 * S['fdir'])
    S['bulge'] = famt * (0.12 + 0.3 * P['fold']) * (0.5 + bass)

    parts = []
    _cubes(S, P, E, t, parts)
    _faces(S, P, E, parts)
    _threads(S, P, E, t, parts)
    _lattice(S, P, parts)
    B = _pipeline(S, P, E, parts, t, par)

    ink = float(par.Ink.eval()) * (1.0 + 0.5 * S['flash'] + 0.2 * kickenv)
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
        out[7, :n] = np.clip(B[idx, 4], 0.0, 4.0)
        out[8, :n] = np.clip(B[idx, 5], 0.0, 4.0)
        out[9, :n] = np.clip(B[idx, 6], 0.0, 4.0)
        out[10, :n] = np.clip(B[idx, 7] * ink, 0.0, 1.0)
    S['lastout'] = out
    _publish(scriptOp, out)

    txt = '%02d  %s\n%s   %d BPM%s' % (S['prog'] + 1, PNAMES[S['prog']], S['pal'], int(round(bpm)),
                                       '   [breakdown]' if S['inbrk'] else '')
    lf = math.exp(-max(0.0, raw - S['labt']) / 2.5) if raw >= S['labt'] else 1.0
    try:
        par.Program.val = float(S['prog'])
        par.Beat.val = float(S['beat'])
        par.Segs.val = float(n)
        par.Trail.val = min(0.93, (P['trl'] + 0.25 * S['surge'] + 0.2 * S['brk'])
                            * float(par.Trails.eval()))
        par.Zoomtr.val = 1.0 + 0.004 + 0.010 * min(3.0, cells * 0.25)
        par.Scrape.val = P['scr']
        par.Scrapea.val = S['scra']
        par.Trot.val = P['roll'] * S['rolldir'] * 0.01
        par.Glitch.val = S['gl'] * float(par.Glitchamt.eval())
        par.Gseed.val = S['gseed']
        par.Flash.val = S['flash']
        bg = S['pal_c'][5]
        par.Bgr.val, par.Bgg.val, par.Bgb.val = float(bg[0]), float(bg[1]), float(bg[2])
        par.Brk.val = S['brk']
        par.Tclk.val = t
        par.Cellsps.val = cells
        par.Labelfade.val = lf
        if txt != S['lastlab'] and lf > 0.05:
            S['lastlab'] = txt
            par.Scaletxt.val = txt
    except Exception:
        pass
    S['census'] = ('%s/%s | beat %d | cells/s %.2f | brk %.2f | fold %.2f | lines %d/%d'
                   % (PNAMES[S['prog']], S['pal'], S['beat'], cells, S['brk'], S['fth'], n,
                      MAXSEG))
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
                print('[tesseract engine] frame failed:\n' + S['lasterr'])
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
    PROGS=PROGS, PALETTES=PALETTES, PALNAMES=PALNAMES, MAXSEG=MAXSEG, SEED0=20260926,
    CH=('tx', 'ty', 'tz', 'rz', 'sx', 'sy', 'sz', 'r', 'g', 'b', 'a'),
    # the window of the lattice around the camera, in cells
    NX=4, NY=3, NZ=18,
    # the threads
    NSTR=40, NPTS=26,
    # kick shockwaves: speed (cells/s), life (s), cap
    PV=14.0, PLIFE=1.35, PULSEMAX=8,
    # tesseracts: the w-perspective distance, small-cube scale, the big one's scale
    # and distance ahead, and its extruded timelines
    TD4=2.4, TSC=0.20, HSC=1.25, HZ=3.2, TRN=7, TRDA=0.10, TRDZ=0.55,
    # the fold: the 4D scale and the w-perspective distance
    FS=5.0, FD=2.2,
    FOCAL=1.0, NEAR=0.05,
    CULLX=1.4, CULLY=0.85, MINLEN=0.0005, MAXL=3.0,
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
soft(mat_line, widthnear=1.3, widthfar=1.3, widthaffectedbyfov=False,
     linenearalpha=1.0, blending=True, depthtest=False, depthwriting=False)
mat_line.par.widthnear.expr = ("max(0.6, parent().par.Linewidth * (1.0 + 0.35 * %s "
                               "+ 0.30 * %s + 0.4 * parent().par.Flash))"
                               % (D('bass'), D('kickenv')))
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

# --- trails: travel streaks out of the vanishing point, or Richter's scrape ----------
trail_fb = C(feedbackTOP, 'trail_fb', 2100, 120)
res(trail_fb)
W(render_lines, trail_fb)
trail = C(glslTOP, 'trail', 2260, 200)
res(trail)
trail_pix = C(textDAT, 'trail_pixel', 2260, 130)
trail_pix.text = '''// Slit-scan by feedback. The previous frame is pulled outward from the vanishing
// point (zoom > 1), turned with the roll, and dragged sideways by the scrape; then
// decayed and max'ed under the new lines — max, not add, so it can never wash out.
uniform vec4 uT;   // x decay, y zoom, z scrape, w aspect
uniform vec4 uU;   // x turn, y scrape angle
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec4 cur = texture(sTD2DInputs[0], uv);
    vec2 p = (uv - 0.5) * vec2(uT.w, 1.0);
    float c = cos(uU.x), s = sin(uU.x);
    p = mat2(c, -s, s, c) * p / uT.y;
    p -= vec2(cos(uU.y), sin(uU.y)) * uT.z * 0.006;
    vec4 fb = texture(sTD2DInputs[1], p / vec2(uT.w, 1.0) + 0.5);
    fragColor = TDOutputSwizzle(max(cur, fb * uT.x));
}
'''
trail.par.pixeldat = trail_pix.name
W(render_lines, trail, 0)
W(trail_fb, trail, 1)
trail.par.vec = 2
trail.par.vec0name = 'uT'
trail.par.vec0valuex.expr = 'parent().par.Trail'
trail.par.vec0valuey.expr = 'parent().par.Zoomtr'
trail.par.vec0valuez.expr = 'parent().par.Scrape'
trail.par.vec0valuew = ASPECT
trail.par.vec1name = 'uU'
trail.par.vec1valuex.expr = 'parent().par.Trot'
trail.par.vec1valuey.expr = 'parent().par.Scrapea'
trail_fb.par.top = trail.name

# --- the void: deep space behind the lattice -----------------------------------------
void = C(glslTOP, 'void', 1940, 440)
res(void)
void_pix = C(textDAT, 'void_pixel', 1940, 370)
void_pix.text = '''// Behind the lattice: a dim nebula in the palette's background colour, a glow at
// the vanishing point that the kick and the breakdown feed, grain and a vignette.
uniform vec4 uP;   // x energy, y kickenv, z vignette, w clock (wrapped)
uniform vec4 uB;   // rgb background, w breakdown
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
    for (int i = 0; i < 5; i++) { s += a * vnoise(p); p = p * 2.07 + 5.1; a *= 0.5; }
    return s;
}

void main() {
    vec2 uv = vUV.st;
    vec2 d = (uv - 0.5) * vec2(1.7778, 1.0);
    float t = uP.w;
    float r = length(d);
    // the nebula turns slowly around the vanishing point
    float a = atan(d.y, d.x);
    vec2 q = vec2(a * 1.2 + t * 0.01, log(r + 0.05) * 1.6 - t * 0.05);
    float n = fbm(q * 2.0) * fbm(d * 3.0 + t * 0.02);
    vec3 col = uB.rgb * (0.5 + 3.2 * n);
    col += uB.rgb * (6.0 + 10.0 * uB.w) * exp(-r * r * (18.0 - 10.0 * uB.w))
           * (0.35 + 0.6 * uP.x + 0.7 * uP.y);
    col += (hash(uv * vec2(1920.0, 1080.0) + fract(t)) - 0.5) * 0.006;
    col *= 1.0 - uP.z * 0.8 * dot(d, d);
    fragColor = TDOutputSwizzle(vec4(max(col, vec3(0.0)), 1.0));
}
'''
void.par.pixeldat = void_pix.name
void.par.vec = 2
void.par.vec0name = 'uP'
void.par.vec0valuex.expr = D('energy')
void.par.vec0valuey.expr = D('kickenv')
void.par.vec0valuez.expr = 'parent().par.Vignette'
void.par.vec0valuew.expr = 'parent().par.Tclk'
void.par.vec1name = 'uB'
void.par.vec1valuex.expr = 'parent().par.Bgr'
void.par.vec1valuey.expr = 'parent().par.Bgg'
void.par.vec1valuez.expr = 'parent().par.Bgb'
void.par.vec1valuew.expr = 'parent().par.Brk'

comp = C(compositeTOP, 'comp_scene', 2420, 440, operand='over')
res(comp)
W(trail, comp, 0)
W(void, comp, 1)

glow_cut = C(levelTOP, 'glow_cut', 2420, 320)
soft(glow_cut, blacklevel=0.20, gamma1=1.20)
W(comp, glow_cut)
glow_blur = C(blurTOP, 'glow_blur', 2580, 320, size=12.0)
res(glow_blur, OUTW // 2, OUTH // 2)
glow_blur.par.size.expr = "10.0 + 18.0 * %s" % D('dropenv')
W(glow_cut, glow_blur)
glow_lvl = C(levelTOP, 'glow_lvl', 2740, 320)
glow_lvl.par.opacity.expr = (
    "0.55 * parent().par.Glow * (0.45 + 0.30 * %s + 0.35 * %s + 0.5 * %s "
    "+ 0.6 * parent().par.Flash)" % (D('energy'), D('kickenv'), D('dropenv')))
W(glow_blur, glow_lvl)
comp_glow = C(compositeTOP, 'comp_glow', 2580, 440, operand='add')
res(comp_glow)
W(comp, comp_glow, 0)
W(glow_lvl, comp_glow, 1)

# --- glitch: torn bands, displaced blocks, colour split ------------------------------
glitch = C(glslTOP, 'glitch', 2740, 440)
res(glitch)
glitch_pix = C(textDAT, 'glitch_pixel', 2740, 370)
glitch_pix.text = '''// Rip it to shreds (ISAM's word for it). Horizontal bands torn sideways, a few
// blocks dropped out of line, a colour split that the kick also nudges, and scan
// lines. With no glitch it is a faint colour split and nothing else.
uniform vec4 uG;   // x amount, y seed, z kickenv, w unused
out vec4 fragColor;

float h(float n) { return fract(sin(n * 91.345) * 47453.5453); }

void main() {
    vec2 uv = vUV.st;
    float g = uG.x;
    vec2 u = uv;
    if (g > 0.002) {
        float rows = 16.0 + floor(h(uG.y) * 64.0);
        float band = floor(uv.y * rows);
        float on = step(h(band * 1.7 + uG.y * 13.1), g * 0.5);
        u.x += (h(band * 3.3 + uG.y) - 0.5) * 0.22 * g * on;
        float cb = floor(uv.x * 12.0);
        float onb = step(h(cb * 5.1 + band * 0.7 + uG.y * 3.0), g * 0.10);
        u.y += onb * (h(cb + uG.y) - 0.5) * 0.08 * g;
    }
    float ca = 0.0003 + 0.010 * g + 0.0010 * uG.z;
    float r = texture(sTD2DInputs[0], u + vec2(ca, 0.0)).r;
    vec4 c = texture(sTD2DInputs[0], u);
    float b = texture(sTD2DInputs[0], u - vec2(ca, 0.0)).b;
    vec3 col = vec3(r, c.g, b);
    col *= 1.0 - 0.10 * g * step(0.5, fract(uv.y * 240.0));
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
'''
glitch.par.pixeldat = glitch_pix.name
W(comp_glow, glitch)
glitch.par.vec = 1
glitch.par.vec0name = 'uG'
glitch.par.vec0valuex.expr = 'parent().par.Glitch'
glitch.par.vec0valuey.expr = 'parent().par.Gseed'
glitch.par.vec0valuez.expr = D('kickenv')

label = C(textTOP, 'label', 2420, 620)
res(label, OUTW, OUTH, 'rgba8fixed')
soft(label, alignx='left', aligny='top', fontsizex=17, font='Courier New',
     bgalpha=0.0, fontcolorr=0.92, fontcolorg=0.92, fontcolorb=0.96,
     fontcolora=1.0, wordwrap=False, trackingx=0.25,
     positionx=0.035, positiony=-0.06, positionunit='fraction')
label.par.text.expr = 'parent().par.Scaletxt.eval()'
label_lvl = C(levelTOP, 'label_lvl', 2580, 620)
label_lvl.par.opacity.expr = "parent().par.Label * parent().par.Labelfade"
W(label, label_lvl)
comp_label = C(compositeTOP, 'comp_label', 2900, 440, operand='over')
res(comp_label)
W(label_lvl, comp_label, 0)
W(glitch, comp_label, 1)

grade = C(levelTOP, 'grade', 3060, 440)
soft(grade, gamma1=0.95, contrast=1.06, blacklevel=0.0)
grade.par.brightness1.expr = '1.0 + 0.35 * parent().par.Flash'
soft(grade, clamp=True, clamplow2=0.0, clamphigh2=4.0)
W(comp_label, grade)

final_out = C(nullTOP, 'final_out', 3220, 440)
W(grade, final_out)
out1 = C(outTOP, 'out1', 3380, 440)
W(final_out, out1)

pout = proj.create(outTOP, SCENE + '_out')
pout.nodeX, pout.nodeY = 400, -5000
s.outputConnectors[0].connect(pout.inputConnectors[0])


# ---------------------------------------------------------------------------
# PADS AND KEYS
# ---------------------------------------------------------------------------
PEXEC_BODY = '''# Every pad is a verb into the engine's queue; nothing seeks, because this piece has
# no story — it has a program, and the verbs change it or throw something into it.


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
    if n.startswith('Prog'):
        _push(comp, 'prog' + n[4:])
    elif n == 'Auto':
        _push(comp, 'auto')
    elif n == 'Foldnow':
        _push(comp, 'fold')
    elif n == 'Glitchnow':
        _push(comp, 'glitch')
    elif n == 'Pulsenow':
        _push(comp, 'pulse')
    elif n == 'Palette':
        _push(comp, 'palette')
    elif n == 'Newprog':
        _push(comp, 'new')
    return
'''
pexec = C(parameterexecuteDAT, 'pad_exec', 2100, 1000)
pexec.text = PEXEC_BODY
pexec.par.op = '..'
soft(pexec, pars=' '.join(['Prog%d' % (i + 1) for i in range(len(PROGS))]
                          + ['Auto', 'Foldnow', 'Glitchnow', 'Pulsenow', 'Palette', 'Newprog']),
     valuechange=False, onpulse=True)

KEY_BODY = '''# 1-6 force a program (held for 64 beats, then the automatic changes resume);
# 0 releases it now.
#   f  FOLD     rotate the whole lattice through the fourth dimension
#   g  GLITCH   tear the frame
#   p  PULSE    a shockwave down the lattice
#   c  PALETTE  the next palette
#   n  NEW      a random program and a new lattice
#   h  HOLD     stop the automatic program changes (toggle)
#   r  REVERSE  fly the other way (toggle)


def onKey(dat, keyInfo):
    if not keyInfo.state:
        return
    comp = dat.parent()
    k = keyInfo.key
    if k in '123456':
        p = getattr(comp.par, 'Prog' + k, None)
        if p is not None:
            p.pulse()
    elif k == '0':
        comp.par.Auto.pulse()
    elif k == 'f':
        comp.par.Foldnow.pulse()
    elif k == 'g':
        comp.par.Glitchnow.pulse()
    elif k == 'p':
        comp.par.Pulsenow.pulse()
    elif k == 'c':
        comp.par.Palette.pulse()
    elif k == 'n':
        comp.par.Newprog.pulse()
    elif k == 'h':
        comp.par.Hold = not comp.par.Hold.eval()
    elif k == 'r':
        comp.par.Reverse = not comp.par.Reverse.eval()
    return


def onShortcut(dat, shortcutName, time):
    return
'''
keyin = C(keyboardinDAT, 'key_pad', 1780, 700)
keyin.par.keys = '1 2 3 4 5 6 0 f g p c n h r'
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
        (comp_glow.par.operand.eval(), 'add', 'glow composite operand')):
    if _got != _want:
        print('  [CHECK FAILED] %s is %r, expected %r' % (_what, _got, _want))

print('built %s' % s.path)
print('  %s' % eng_src.module._S['S']['census'])
