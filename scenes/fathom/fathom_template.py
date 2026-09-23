# Fathom — the man from `homestead` puts a glass jar over his head, ties his lantern
# to his waist, and dives off his own riverbank: down through the sunlit shallows, a
# kelp forest, a coral garden, the twilight zone where the jellyfish drift, past a
# whale, into the abyss and down to the hot vents on the sea floor — and a burst of
# bubbles carries him back up to surface by his house at golden hour.
#
# THE VIEW IS A CROSS-SECTION, side-on like homestead: the water surface is one
# line, the bank drops away beneath it, and the camera follows him down while the
# world scrolls past (as in bayou). Everything he meets is a flat cel with a hard
# shadow side and a bold outline — the same primitive, and the same man, as homestead.
#
# THE REALISM IS IN THE WATER. The water column, light shafts, caustics, marine snow,
# the sea bed and the distant rock silhouettes are painted in one shader, and the
# water ABSORBS COLOUR WITH DEPTH: every cel is lit by an ambient that loses red
# first, then green, until the abyss is black. His lantern is the only warm light
# down there, and it gives back the true colours of whatever it falls on.
#
# AUDIO IS IN THE PACE AND THE LIFE. Tempo is the story clock; his swim strokes land
# on the kick; jellyfish pulse and tube worms snap back into their tubes on the
# kick; bass sways the kelp and the anemones; highs make the bioluminescence
# twinkle; energy is the current (marine snow, the schools); a drop sends a flash of
# fish past him.
#
# BUILT TO RUN ALL NIGHT (see the skill's long-run audit): the story loops through
# black, every integrated phase resets at the seam, every list is hard-capped, and
# Script CHOP channels are built once and then only written.
#
# Idempotent: destroys and recreates /project1/fathom and its project-level Out TOP,
# and touches nothing else. No media files.
#     code = open('scenes/fathom/build.py', encoding='utf-8').read()
#     g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
#
# GENERATED: this file is fathom_template.py + verbatim blocks of
# scenes/homestead/build.py (BEGIN/END HOMESTEAD), assembled by gen_fathom.py.

import math
import os

SCENE = 'fathom'
OUTW, OUTH = 1280, 720
ASPECT = OUTW / OUTH
ORTHOW = 1.80
ORTHOH = ORTHOW / ASPECT
CAMX, CAMY = 0.0, 0.0            # the camera moves; these are only the render COMP's rest
CLOCKLEN = 60.0

STORYDEF = 330.0
MAXSEG = 12000

MANSC = 0.270
BANKY = 0.068                    # the top of his bank
BANKCAM = (-0.28, 0.13)          # where the camera sits on the bank

# The sea bed, as a table of (x, y) in world units, shared by the shader and the
# engine (both use the same smooth interpolation and the same small bumps). The
# path he swims sits a little above it — except where the shelf drops away into
# open water, which is the point of the twilight and whale chapters.
FLOOR_X = (-3.0, -0.12, 0.00, 0.10, 0.35, 0.90, 3.10, 6.60, 10.10, 11.00, 13.00,
           16.00, 18.50, 19.10, 22.10, 23.50, 25.00, 30.0)
FLOOR_Y = (BANKY, BANKY, 0.063, -0.050, -0.450, -0.800, -1.100, -1.700, -2.250,
           -3.200, -4.700, -5.600, -6.900, -6.850, -6.850, -6.900, -7.400, -7.500)
# his swim, chapter by chapter (f, x, y of his hip)
PATH_F = (0.100, 0.200, 0.320, 0.440, 0.550, 0.660, 0.770, 0.870, 0.950)
PATH_X = (0.900, 3.100, 6.600, 10.100, 13.100, 16.100, 19.100, 22.100, 24.800)
PATH_Y = (-0.450, -0.750, -1.300, -1.850, -3.100, -3.900, -5.700, -6.580, -1.200)

CHECKPOINTS = [
    ('bank',     ' 1 - The Edge of the Water', 0.000),
    ('shallows', ' 2 - Into the River',        0.100),
    ('kelp',     ' 3 - The Kelp Forest',       0.200),
    ('reef',     ' 4 - The Coral Garden',      0.320),
    ('twilight', ' 5 - The Twilight Zone',     0.440),
    ('whale',    ' 6 - The Whale',             0.550),
    ('abyss',    ' 7 - The Abyss',             0.660),
    ('vents',    ' 8 - The Deep Vents',        0.770),
    ('light',    ' 9 - Back to the Light',     0.870),
]
# the sun over the river: a dim morning when he dives, golden hour when he climbs out
GSUN_F = (0.00, 0.50, 0.93, 1.00)
GSUN_H = (0.30, 0.30, 0.14, 0.10)
# the homestead palette's dim-daylight ambient, by sun height (see homestead)
AMB_H = (-0.60, -0.20, 0.00, 0.15, 0.40, 0.90)
AMB_R = (0.130, 0.260, 0.600, 0.700, 0.700, 0.690)
AMB_G = (0.160, 0.260, 0.440, 0.560, 0.640, 0.650)
AMB_B = (0.300, 0.440, 0.420, 0.440, 0.540, 0.560)
# how water eats light, per channel, per world unit of depth (red goes first)
ABSORB = (0.62, 0.26, 0.16)
DIMDEPTH = 0.26

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
    WARM=(1.000, 0.680, 0.380),
    GLASS=(0.780, 0.920, 0.960), COPPER=(0.720, 0.420, 0.220),
    KELP=(0.520, 0.470, 0.200), KELPLT=(0.680, 0.620, 0.300),
    BUBBLE=(0.820, 0.940, 1.000), BIO=(0.550, 1.000, 0.880),
)

proj = op('/project1')
for stale in (SCENE, SCENE + '_out'):
    o = proj.op(stale)
    if o:
        o.destroy()

s = proj.create(containerCOMP, SCENE)
s.nodeX, s.nodeY = 0, -3200
s.par.w, s.par.h = OUTW, OUTH


#@INCLUDE def C(type_, name, x, y, **params):|||# ---------------------------------------------------------------------------\n# PERFORMANCE SURFACE


# ---------------------------------------------------------------------------
# PERFORMANCE SURFACE
# ---------------------------------------------------------------------------
pg = s.appendCustomPage('Fathom')
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
    ('Paceaudio',  'Energy Drives Current', 1.0, 0.0, 3.0),
    ('Sway',       'Plant Sway',          1.0, 0.0, 3.0),
    ('Brightness', 'Brightness',          1.0, 0.2, 2.0),
    ('Ink',        'Brightness of Art',   1.0, 0.0, 2.0),
    ('Glow',       'Glow',                1.0, 0.0, 3.0),
    ('Label',      'Chapter Readout',     1.0, 0.0, 2.0),
    ('Vignette',   'Vignette',            0.75, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

_RO = [('Bpm', 0, 200), ('Showt', 0, 2400), ('Chapter', 0, len(CHECKPOINTS)),
       ('Camx', -9, 99), ('Camy', -99, 9), ('Current', 0, 1e6), ('Gsun', -1, 1),
       ('Burst', 0, 1), ('Lant', 0, 1), ('Lx', -99, 99), ('Ly', -99, 99),
       ('Vent', 0, 1), ('Fade', 0, 1), ('Loops', 0, 1e6), ('Depth', -1, 99),
       ('Rejects', 0, 1e6), ('Segs', 0, MAXSEG), ('Labelfade', 0, 1),
       ('Bassm', 0, 1), ('Highm', 0, 1), ('Energym', 0, 1)]
for _mn, _lo, _hi in _RO:
    pg.appendFloat(_mn, label=_mn)
    _p = getattr(s.par, _mn)
    _p.normMin, _p.normMax = _lo, _hi
    _p.readOnly = True
s.par.Fade.val = 1.0
s.par.Camx.val, s.par.Camy.val = BANKCAM

pg.appendToggle('Loop', label='Loop the Story')
s.par.Loop.default = True
s.par.Loop.val = True
pg.appendStr('Scaletxt', label='Chapter Text')
s.par.Scaletxt.readOnly = True
s.par.Scaletxt.val = ''

pg.appendPulse('Bubbles', label='B - BUBBLES (a burst from his helmet)')
pg.appendPulse('Reseed', label='N - RESEED (a new sea)')
pg.appendPulse('Restart', label='0 - RESTART')
pg.appendPulse('Nextcp', label='next chapter')
pg.appendPulse('Prevcp', label='previous chapter')
for cp, label, _f in CHECKPOINTS:
    pg.appendPulse('Go' + cp, label=label)

# ---------------------------------------------------------------------------
# AUDIO FRONT END, CLOCK, TEMPO — verbatim from homestead
# ---------------------------------------------------------------------------
#@INCLUDE adev = C(audiodeviceinCHOP|||# ---------------------------------------------------------------------------\n# DIRECTOR

# ---------------------------------------------------------------------------
# DIRECTOR — verbatim from homestead (its 'gust' verb is our bubble burst)
# ---------------------------------------------------------------------------
#@INCLUDE DIRECTOR_BODY = '''|||def D(ch):


def D(ch):
    return "(op('director')['%s'] or 0)" % ch


# ---------------------------------------------------------------------------
# THE ENGINE
# ---------------------------------------------------------------------------
ENGINE_BODY = r'''# Everything that lives or is built is emitted from here as ONE primitive (see
# homestead): rows of (x0, y0, x1, y1, r, g, b, a, z, fl, w, wl), in WORLD units —
# the camera is subtracted at the very end. The first half is homestead's engine,
# verbatim: the primitives, the man, his house, the tree. The second half is the dive.
import math
import random
import numpy as np

#@INCLUDE _S = {'S': None}|||# --- the wild: grass
#@INCLUDE def _slabs(ry):|||def _gen_fireflies(rs):


# ===================================================================================
# THE DIVE
# ===================================================================================
def _tab(f, F, V):
    return float(np.interp(f, F, V))


def _sinterp(x, X, Y):
    """Smooth (smoothstep) interpolation through a table — the shader does the same."""
    if x <= X[0]:
        return Y[0]
    if x >= X[-1]:
        return Y[-1]
    for i in range(len(X) - 1):
        if X[i] <= x < X[i + 1]:
            q = (x - X[i]) / (X[i + 1] - X[i])
            q = q * q * (3.0 - 2.0 * q)
            return Y[i] + (Y[i + 1] - Y[i]) * q
    return Y[-1]


def floor_y(x):
    bump = (0.030 * math.sin(x * 2.3) + 0.018 * math.sin(x * 5.7 + 1.3)
            + 0.008 * math.sin(x * 13.1 + 0.7)) * _cl(x / 0.4)
    return _sinterp(x, FLOOR_X, FLOOR_Y) + bump


def _rot(pts, cx, cy, a):
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca)
            for (x, y) in pts]


# --- the flora: generated once in world coordinates, swayed per frame ------------
# Every row carries a sway weight (how far up its plant it sits) and a phase, so the
# whole sea bed sways as one vectorised operation.
def _gen_flora(rs):
    rows, wt, ph, tips = [], [], [], []

    def add(tmp, w, p):
        rows.extend(tmp)
        wt.extend([w] * len(tmp) if not isinstance(w, list) else w)
        ph.extend([p] * len(tmp))

    def zf(y):
        return 0.30 + 0.02 * rs.random()

    # --- the bank: grass on top, reeds at the edge, his house, the tree --------
    for k in range(70):
        x = rs.uniform(-1.9, -0.03)
        tmp = []
        for j in range(rs.randint(3, 5)):
            h = rs.uniform(0.03, 0.07)
            a = rs.uniform(-0.4, 0.4)
            c = _mul((0.36, 0.44, 0.18), rs.uniform(0.8, 1.15))
            _seg(tmp, x, BANKY, x + math.sin(a) * h, BANKY + math.cos(a) * h, c, 1.0,
                 0.34 + 0.001 * j, 0.0045)
        add(tmp, 0.6, rs.uniform(0, 6.28))
    for k in range(9):
        x = rs.uniform(-0.10, 0.20)
        y0 = floor_y(x)
        h = rs.uniform(0.10, 0.22)
        tmp = []
        _seg(tmp, x, y0, x + 0.01, y0 + h, (0.33, 0.40, 0.18), 1.0, 0.33, 0.0045)
        if rs.random() < 0.6:
            _limb(tmp, x + 0.008, y0 + h * 0.78, x + 0.01, y0 + h * 0.97, 0.010,
                  (0.38, 0.24, 0.13), None, 1.0, 0.331, 1.0, LWO * 0.5)
        add(tmp, 0.7, rs.uniform(0, 6.28))

    # --- the shallows: sea grass and pebbles --------------------------------------
    for k in range(80):
        x = rs.uniform(0.2, 3.3)
        y0 = floor_y(x)
        tmp = []
        for j in range(3):
            h = rs.uniform(0.06, 0.20)
            a = rs.uniform(-0.25, 0.25)
            _seg(tmp, x + 0.006 * j, y0, x + 0.006 * j + math.sin(a) * h,
                 y0 + math.cos(a) * h, _mul((0.30, 0.52, 0.26), rs.uniform(0.8, 1.2)),
                 1.0, 0.30 + 0.001 * j, 0.006)
        add(tmp, 1.0, rs.uniform(0, 6.28))
    for k in range(40):
        x = rs.uniform(0.3, 6.0)
        y0 = floor_y(x)
        r = rs.uniform(0.010, 0.030)
        tmp = []
        _shape(tmp, _ell(x, y0 + r * 0.4, r, r * 0.6, 12), _mul((0.55, 0.52, 0.46),
               rs.uniform(0.7, 1.1)), 1.0, 0.36, (0.70, 0.68, 0.60), 1.0, LWO * 0.5)
        add(tmp, 0.0, 0.0)

    # --- the kelp forest: tall stalks with blades, swaying from the root --------
    for k in range(28):
        x = rs.uniform(3.0, 6.9)
        y0 = floor_y(x)
        h = rs.uniform(0.70, 1.35)
        p = rs.uniform(0, 6.28)
        front = rs.random() < 0.18
        z = 0.80 if front else 0.28 + 0.03 * rs.random()
        n = 12
        tone = _mul(KELP, rs.uniform(0.8, 1.1))
        for i in range(n):
            q0, q1 = i / float(n), (i + 1) / float(n)
            xa = x + 0.03 * math.sin(q0 * 5.0 + p)
            xb = x + 0.03 * math.sin(q1 * 5.0 + p)
            tmp = []
            _limb(tmp, xa, y0 + h * q0, xb, y0 + h * q1, 0.014, tone, None, 1.0, z, 1.0,
                  LWO * 0.5)
            if i % 2 == 1:
                side = 1.0 if (i // 2) % 2 else -1.0
                bl = 0.07 + 0.05 * rs.random()
                _shape(tmp, _ell(xb + side * bl * 0.5, y0 + h * q1 + 0.02, bl * 0.55,
                                 0.018, 10, side * 0.6), tone, 1.0, z + 0.0005, KELPLT,
                       1.0, LWO * 0.5, slabs=7)
            add(tmp, q1 ** 1.2, p)
        # a float bladder at the crown
        tmp = []
        _shape(tmp, _ell(x + 0.03 * math.sin(5.0 + p), y0 + h + 0.015, 0.016, 0.020, 10),
               KELPLT, 1.0, z + 0.001, None, 1.0, LWO * 0.5)
        add(tmp, 1.0, p)

    # --- the coral garden --------------------------------------------------------
    coral_cols = ((0.86, 0.52, 0.60), (0.92, 0.66, 0.40), (0.62, 0.52, 0.86),
                  (0.95, 0.80, 0.46), (0.52, 0.80, 0.72))
    for k in range(58):
        x = rs.uniform(6.3, 10.4)
        y0 = floor_y(x) - 0.01
        kind = rs.randint(0, 4)
        col = coral_cols[rs.randint(0, 4)]
        s = rs.uniform(0.13, 0.28)
        z = 0.31 + 0.03 * rs.random()
        tmp = []
        if kind == 0:                                   # fan coral
            def br(x0, y0_, ang, ln, lv):
                x1, y1 = x0 + math.cos(ang) * ln, y0_ + math.sin(ang) * ln
                _seg(tmp, x0, y0_, x1, y1, col, 1.0, z, 0.006 - 0.001 * lv)
                if lv < 3:
                    for da in (-0.35, 0.35):
                        br(x1, y1, ang + da + rs.uniform(-0.1, 0.1), ln * 0.72, lv + 1)
            br(x, y0, 1.5708, s * 0.6, 0)
            add(tmp, 0.35, rs.uniform(0, 6.28))
        elif kind == 1:                                 # brain coral
            _shape(tmp, _ell(x, y0 + s * 0.25, s * 0.55, s * 0.40, 18), col, 1.0, z,
                   _mix(col, (1, 1, 1), 0.3), 1.0, slabs=10)
            for j in range(5):
                yy = y0 + s * (0.12 + 0.08 * j)
                _seg(tmp, x - s * 0.35, yy, x + s * 0.35, yy + 0.01 * math.sin(j),
                     _mul(col, 0.7), 1.0, z + 0.0006, 0.004)
            add(tmp, 0.0, 0.0)
        elif kind == 2:                                 # tube sponges
            for j in range(3):
                xx = x + (j - 1) * s * 0.28
                hh = s * rs.uniform(0.8, 1.5)
                _limb(tmp, xx, y0, xx, y0 + hh, s * 0.22, col, _mix(col, (1, 1, 1), 0.3),
                      1.0, z + 0.001 * j, 1.0)
                _fill(tmp, _ell(xx, y0 + hh, s * 0.09, s * 0.04, 10), _mul(col, 0.45), 1.0,
                      z + 0.001 * j + 0.0005, 3)
            add(tmp, 0.10, rs.uniform(0, 6.28))
        elif kind == 3:                                 # staghorn
            def st(x0, y0_, ang, ln, lv):
                x1, y1 = x0 + math.cos(ang) * ln, y0_ + math.sin(ang) * ln
                _limb(tmp, x0, y0_, x1, y1, 0.016 - 0.004 * lv, col, None, 1.0, z, 1.0,
                      LWO * 0.5)
                if lv < 2:
                    for da in (-0.5, 0.45):
                        st(x1, y1, ang + da, ln * 0.75, lv + 1)
            st(x, y0, 1.5708 + rs.uniform(-0.2, 0.2), s * 0.55, 0)
            add(tmp, 0.15, rs.uniform(0, 6.28))
        else:                                           # anemone
            _limb(tmp, x, y0, x, y0 + s * 0.30, s * 0.30, _mul(col, 0.8), None, 1.0, z,
                  1.0)
            w = []
            for j in range(11):
                a = 1.5708 + (j - 5) * 0.20
                tl = s * 0.45
                _limb(tmp, x + (j - 5) * s * 0.025, y0 + s * 0.30,
                      x + math.cos(a) * tl, y0 + s * 0.30 + math.sin(a) * tl,
                      s * 0.05, col, None, 1.0, z + 0.001, 1.0, LWO * 0.4)
            add(tmp, 0.8, rs.uniform(0, 6.28))
            tips.append(('anemone', x, y0 + s * 0.45))
    for k in range(8):                                  # starfish
        x = rs.uniform(6.5, 10.0)
        y0 = floor_y(x)
        tmp = []
        for j in range(5):
            a = j * 1.2566 + 0.3
            _limb(tmp, x, y0 + 0.012, x + math.cos(a) * 0.028, y0 + 0.012 + math.sin(a) * 0.014,
                  0.010, (0.92, 0.46, 0.30), None, 1.0, 0.37, 1.0, LWO * 0.5)
        add(tmp, 0.0, 0.0)

    # --- the slope into the dark: sea whips -------------------------------------
    for k in range(22):
        x = rs.uniform(10.2, 16.2)
        y0 = floor_y(x)
        h = rs.uniform(0.25, 0.60)
        tmp = []
        pts = [(x + 0.04 * math.sin(i * 0.9), y0 + h * i / 6.0) for i in range(7)]
        _path(tmp, pts, (0.70, 0.40, 0.46), 1.0, 0.30, 0.006)
        add(tmp, 0.9, rs.uniform(0, 6.28))

    # --- the abyssal plain: glass sponges and glowing sea pens -------------------
    for k in range(10):
        x = rs.uniform(16.2, 19.5)
        y0 = floor_y(x)
        s = rs.uniform(0.10, 0.18)
        tmp = []
        _path(tmp, [(x - s * 0.20, y0), (x - s * 0.32, y0 + s * 0.6), (x - s * 0.22, y0 + s * 1.2),
                    (x + s * 0.22, y0 + s * 1.2), (x + s * 0.32, y0 + s * 0.6), (x + s * 0.20, y0)],
              (0.80, 0.86, 0.90), 0.85, 0.30, 0.005)
        for j in range(4):
            yy = y0 + s * 0.25 * (j + 0.5)
            _seg(tmp, x - s * 0.28, yy, x + s * 0.28, yy, (0.80, 0.86, 0.90), 0.45, 0.30, 0.003)
        add(tmp, 0.05, 0.0)
    for k in range(12):
        x = rs.uniform(16.0, 23.0)
        y0 = floor_y(x)
        h = rs.uniform(0.10, 0.22)
        tmp = []
        CUR['fl'] = 1.0
        _seg(tmp, x, y0, x, y0 + h, (0.30, 0.70, 0.55), 0.8, 0.31, 0.006)
        for j in range(6):
            yy = y0 + h * (0.35 + 0.1 * j)
            for sgn in (-1, 1):
                _seg(tmp, x, yy, x + sgn * 0.03, yy + 0.02, BIO, 0.55, 0.311, 0.004)
        CUR['fl'] = 0.0
        add(tmp, 0.5, rs.uniform(0, 6.28))

    # --- the vents: chimneys, tube worms, mussels ---------------------------------
    for (x, h) in ((19.6, 0.55), (20.4, 0.80), (21.5, 0.45), (22.6, 0.70)):
        y0 = floor_y(x)
        tmp = []
        pts = [(x - 0.12, y0), (x + 0.12, y0), (x + 0.07, y0 + h * 0.4),
               (x + 0.045, y0 + h), (x - 0.045, y0 + h), (x - 0.08, y0 + h * 0.4)]
        _shape(tmp, pts, (0.20, 0.19, 0.20), 1.0, 0.33, (0.32, 0.30, 0.30), 1.0,
               slabs=24)
        CUR['fl'] = 1.0
        for j in range(4):                              # hot cracks
            yy = y0 + h * rs.uniform(0.1, 0.8)
            _seg(tmp, x - 0.02, yy, x + 0.015, yy + 0.03, (1.0, 0.45, 0.15), 0.8, 0.332,
                 0.004)
        CUR['fl'] = 0.0
        add(tmp, 0.0, 0.0)
        tips.append(('chimney', x, y0 + h))
    for k in range(9):
        cx = rs.uniform(19.2, 23.0)
        y0 = floor_y(cx)
        tmp = []
        for j in range(rs.randint(5, 9)):
            x = cx + rs.uniform(-0.09, 0.09)
            h = rs.uniform(0.12, 0.30)
            _limb(tmp, x, y0, x + rs.uniform(-0.02, 0.02), y0 + h, 0.016,
                  (0.88, 0.86, 0.80), None, 1.0, 0.34 + 0.001 * j, 1.0, LWO * 0.5)
            tips.append(('worm', x, y0 + h))
        for j in range(6):
            x = cx + rs.uniform(-0.15, 0.15)
            _shape(tmp, _ell(x, y0 + 0.01, 0.018, 0.010, 10), (0.20, 0.22, 0.30), 1.0,
                   0.345, None, 1.0, LWO * 0.4)
        add(tmp, 0.1, rs.uniform(0, 6.28))

    # sorted by x once, so each frame takes only the slice near the camera with a
    # binary search instead of testing every plant on the sea bed
    A = np.array(rows, dtype=np.float64)
    xs = (A[:, 0] + A[:, 2]) * 0.5
    o = np.argsort(xs, kind='stable')
    return dict(A=A[o], w=np.array(wt)[o], ph=np.array(ph)[o], xs=xs[o], tips=tips)


def _gen_home(rs, canopy):
    """His house and the tree, homestead's own generators, set on the bank."""
    H = _gen_house()
    A = H['A'][H['st'] <= 3].copy()
    k, ax, ay = 0.80, (HX0 + HX1) * 0.5, GYH
    for cx_, cy_ in ((0, 1), (2, 3)):
        A[:, cx_] = -0.78 + (A[:, cx_] - ax) * k
        A[:, cy_] = BANKY + (A[:, cy_] - ay) * k
    A[:, 10] *= k
    A[:, 8] = 0.25 + (A[:, 8] - 0.30) * 0.2
    A[:, 11] = 99.0
    T = _gen_tree(rs, canopy)
    TA = T['A'][T['w'] >= 0.0].copy()
    dx, dy = -1.55 - TREEX, BANKY + 0.31
    TA[:, [0, 2]] += dx
    TA[:, [1, 3]] += dy
    TA[:, 8] = 0.26 + (TA[:, 8] - 0.30) * 0.1
    return np.concatenate([A, TA], axis=0)


# --- the fauna -----------------------------------------------------------------
def _fish(out, x, y, s, ang, body, belly, tph, z, a=1.0, bands=None, fl=0.0):
    flip = -1.0 if math.cos(ang) < 0.0 else 1.0
    ca, sa = math.cos(ang), math.sin(ang)

    def R(u, v):
        v *= flip
        return (x + u * ca - v * sa, y + u * sa + v * ca)

    CUR['fl'] = fl
    wag = 0.12 * s * math.sin(tph)
    # A fish is ~20 px on screen: one fat stroke for the body (outline, colour, lit
    # stripe) and a two-slab tail read the same as a filled polygon at a tenth of the
    # cost — a school of thirty filled polygons was 5 ms a frame.
    _fill(out, [R(-0.38 * s, 0.0), R(-0.68 * s, 0.22 * s + wag), R(-0.68 * s, -0.22 * s + wag)],
          body, a, z - 0.0003, 2)
    n0, t0 = R(0.44 * s, 0.0), R(-0.36 * s, 0.0)
    _limb(out, t0[0], t0[1], n0[0], n0[1], 0.32 * s, body, belly, a, z, 1.0, LWT * 0.6)
    if bands:
        for u in bands:
            p0, p1 = R(u * s, 0.17 * s), R(u * s, -0.15 * s)
            _seg(out, p0[0], p0[1], p1[0], p1[1], (0.97, 0.95, 0.92), a, z + 0.0004, 0.07 * s)
    e = R(0.30 * s, 0.05 * s)
    _rect(out, e[0], e[1], 0.06 * s, 0.06 * s, INK, a, z + 0.0006)
    CUR['fl'] = 0.0


def _school(out, S, key, cx, cy, n, s, body, belly, t, cur, z, spread=0.25,
            bands=None, alpha=1.0):
    """A school circling a moving centre; each fish faces its own direction of travel."""
    rs = random.Random(key)
    for i in range(n):
        r = spread * (0.35 + 0.65 * rs.random())
        w = (0.55 + 0.35 * rs.random()) * (1.0 + 0.8 * cur) * (1 if i % 3 else -1)
        p0 = rs.uniform(0, 6.28)
        a = p0 + t * w
        x = cx + math.cos(a) * r * 1.6
        y = cy + math.sin(a) * r * 0.55 + 0.03 * math.sin(t * 1.3 + i)
        vx, vy = -math.sin(a) * r * 1.6 * w, math.cos(a) * r * 0.55 * w
        ang = math.atan2(vy, vx)
        _fish(out, x, y, s * (0.8 + 0.4 * rs.random()), ang, body, belly,
              t * 9.0 + i, z + 0.0005 * (i % 7), alpha, bands)


def _jelly(out, x, y, s, pulse, t, ph, col, z):
    w = s * (1.0 + 0.28 * pulse)
    h = s * (0.78 - 0.22 * pulse)
    dome = [(x + w * math.cos(a), y + h * math.sin(a)) for a in
            [i * math.pi / 14.0 for i in range(15)]]
    CUR['fl'] = 1.0                                     # they make their own light
    _fill(out, dome, _mul(col, 0.85), 0.55, z, 12)
    _fill(out, [(x + w * 0.6 * math.cos(a), y + h * 0.55 * math.sin(a)) for a in
                [i * math.pi / 10.0 for i in range(11)]], _mix(col, (1, 1, 1), 0.3), 0.35,
          z + 0.0002, 6)
    _path(out, dome, _mix(col, (1, 1, 1), 0.4), 0.55, z + 0.0004, 0.004)
    _seg(out, x - w, y, x + w, y, _mix(col, BIO, 0.5), 0.60, z + 0.0005, 0.004)
    CUR['fl'] = 0.0
    for k in range(6):
        x0 = x - w * 0.8 + w * 1.6 * k / 5.0
        pts = [(x0 + 0.018 * s * 6 * math.sin(t * 2.0 + k + ph + j * 0.9) * (j / 6.0),
                y - s * 2.6 * j / 6.0) for j in range(7)]
        _path(out, pts, _mul(col, 0.85), 0.60, z - 0.0005, 0.0042)
    for k in (-1, 1):
        pts = [(x + k * w * 0.2 + 0.02 * s * 5 * math.sin(t * 1.5 + j + k), y - s * 1.6 * j / 5.0)
               for j in range(6)]
        _path(out, pts, _mul(col, 0.75), 0.55, z - 0.0004, 0.010 * s * 10)
    CUR['fl'] = 0.0


def _whale(out, x, y, s, t, z):
    """A humpback, side on, swimming left."""
    dark, light = (0.42, 0.50, 0.62), (0.82, 0.86, 0.92)
    fl = 0.10 * math.sin(t * 0.7)
    # flukes
    tx, ty = x + 1.25 * s, y + 0.06 * s + fl * s
    for sgn in (-1, 1):
        _shape(out, [(tx - 0.05 * s, ty), (tx + 0.28 * s, ty + sgn * 0.20 * s + fl * s),
                     (tx + 0.18 * s, ty + sgn * 0.04 * s)], dark, 1.0, z - 0.002,
               None, 1.0)
    _limb(out, x + 0.75 * s, y + 0.02 * s, tx, ty, 0.15 * s, dark, None, 1.0, z - 0.001, 1.0)
    body = [(x - 1.00 * s, y + 0.02 * s), (x - 0.80 * s, y + 0.22 * s), (x - 0.20 * s, y + 0.31 * s),
            (x + 0.50 * s, y + 0.20 * s), (x + 0.85 * s, y + 0.06 * s), (x + 0.80 * s, y - 0.07 * s),
            (x + 0.30 * s, y - 0.24 * s), (x - 0.50 * s, y - 0.28 * s), (x - 0.92 * s, y - 0.12 * s)]
    _shape(out, body, dark, 1.0, z, _mix(dark, light, 0.25), 1.0, slabs=30)
    belly = [(x - 0.90 * s, y - 0.08 * s), (x - 0.50 * s, y - 0.20 * s), (x + 0.30 * s, y - 0.17 * s),
             (x + 0.10 * s, y - 0.07 * s), (x - 0.60 * s, y - 0.03 * s)]
    _fill(out, belly, light, 1.0, z + 0.0005, 12)
    for j in range(6):                                  # throat grooves
        yy = y - 0.09 * s - 0.018 * s * j
        _seg(out, x - 0.85 * s + 0.03 * s * j, yy, x - 0.25 * s, yy + 0.01 * s,
             _mul(light, 0.75), 1.0, z + 0.0008, 0.006 * s)
    fa = 0.25 * math.sin(t * 0.5)                       # the long pectoral fin
    _limb(out, x - 0.42 * s, y - 0.10 * s, x - 0.05 * s + 0.1 * s * fa, y - 0.52 * s + fa * s * 0.3,
          0.09 * s, dark, light, 1.0, z + 0.001, 1.0)
    for j in range(5):                                  # tubercles on the head
        _fill(out, _ell(x - 0.92 * s + 0.07 * s * j, y + 0.06 * s + 0.02 * s * (j % 2), 0.012 * s,
                        0.012 * s, 8), _mul(dark, 0.7), 1.0, z + 0.0009, 2)
    _fill(out, _ell(x - 0.64 * s, y - 0.02 * s, 0.020 * s, 0.016 * s, 10), INK, 1.0, z + 0.0012, 3)
    _rect(out, x - 0.645 * s, y - 0.015 * s, 0.008 * s, 0.008 * s, (0.9, 0.9, 0.9), 1.0, z + 0.0013)


def _turtle(out, x, y, s, t, z):
    shell, scute, skin = (0.40, 0.34, 0.20), (0.56, 0.46, 0.26), (0.46, 0.52, 0.36)
    fa = math.sin(t * 2.2)
    _shape(out, [(x + 0.03 * s, y - 0.01 * s), (x + 0.06 * s, y - 0.03 * s),
                 (x - 0.04 * s + 0.04 * s * fa, y - 0.12 * s - 0.03 * s * fa)], skin, 1.0,
           z - 0.001, None, 1.0)
    _shape(out, [(x - 0.08 * s, y - 0.02 * s), (x - 0.05 * s, y - 0.04 * s),
                 (x - 0.15 * s, y - 0.07 * s)], skin, 1.0, z - 0.001, None, 1.0)
    _shape(out, _ell(x, y, 0.13 * s, 0.075 * s, 16), shell, 1.0, z, scute, 1.0)
    for j in range(3):
        cx = x - 0.07 * s + 0.07 * s * j
        _path(out, _ell(cx, y + 0.02 * s, 0.03 * s, 0.025 * s, 6), _mul(shell, 0.6), 1.0,
              z + 0.0005, 0.004 * s, close=True)
    _shape(out, _ell(x + 0.16 * s, y + 0.005 * s, 0.045 * s, 0.032 * s, 12), skin, 1.0, z + 0.0002,
           None, 1.0)
    _rect(out, x + 0.18 * s, y + 0.012 * s, 0.010 * s, 0.010 * s, INK, 1.0, z + 0.0006)
    _shape(out, [(x + 0.05 * s, y - 0.02 * s), (x + 0.09 * s, y - 0.04 * s),
                 (x + 0.01 * s - 0.05 * s * fa, y - 0.14 * s + 0.04 * s * fa)], skin, 1.0,
           z + 0.001, None, 1.0)


def _angler(out, x, y, s, t, high, z):
    body = (0.20, 0.17, 0.22)
    _shape(out, _ell(x, y, 0.11 * s, 0.09 * s, 16), body, 1.0, z, _mul(body, 1.5), 1.0)
    _shape(out, [(x - 0.10 * s, y), (x - 0.19 * s, y + 0.06 * s), (x - 0.19 * s, y - 0.06 * s)],
           body, 1.0, z - 0.0005, None, 1.0)
    _seg(out, x + 0.03 * s, y - 0.03 * s, x + 0.11 * s, y - 0.01 * s, INK, 1.0, z + 0.0006, 0.010 * s)
    for j in range(5):
        xx = x + 0.035 * s + 0.017 * s * j
        _fill(out, [(xx, y - 0.028 * s + 0.003 * s * j), (xx + 0.008 * s, y - 0.028 * s + 0.003 * s * j),
                    (xx + 0.004 * s, y - 0.005 * s)], (0.92, 0.92, 0.86), 1.0, z + 0.0008, 2)
    _rect(out, x + 0.05 * s, y + 0.035 * s, 0.018 * s, 0.018 * s, (0.75, 0.80, 0.70), 1.0, z + 0.0007)
    rod = [(x + 0.02 * s, y + 0.085 * s), (x + 0.09 * s, y + 0.17 * s), (x + 0.17 * s, y + 0.15 * s)]
    _path(out, rod, _mul(body, 1.6), 1.0, z + 0.0004, 0.006 * s)
    fl = 0.65 + 0.35 * math.sin(t * (6.0 + 10.0 * high)) * math.sin(t * 2.3)
    CUR['fl'] = 1.0
    lx, ly = rod[-1][0], rod[-1][1] - 0.015 * s
    _fill(out, _ell(lx, ly, 0.050 * s, 0.050 * s, 20), BIO, 0.22 * fl, z + 0.001, 16)
    _fill(out, _ell(lx, ly, 0.026 * s, 0.026 * s, 16), BIO, 0.40 * fl, z + 0.0011, 10)
    _fill(out, _ell(lx, ly, 0.012 * s, 0.012 * s, 12), (0.85, 1.0, 0.95), fl, z + 0.0012, 6)
    CUR['fl'] = 0.0


def _comb(out, x, y, s, t, high, z):
    _fill(out, _ell(x, y, 0.05 * s, 0.08 * s, 14), (0.70, 0.80, 0.90), 0.20, z, 8)
    _path(out, _ell(x, y, 0.05 * s, 0.08 * s, 14), (0.80, 0.90, 1.0), 0.35, z + 0.0003, 0.003,
          close=True)
    CUR['fl'] = 1.0
    for k in range(6):
        a = -0.8 + 1.6 * k / 5.0
        for j in range(5):
            v = -0.8 + 1.6 * j / 4.0
            hue = (k / 6.0 + j * 0.08 + t * 0.6 * (1.0 + high)) % 1.0
            c = (0.5 + 0.5 * math.cos(6.283 * hue), 0.5 + 0.5 * math.cos(6.283 * (hue - 0.33)),
                 0.5 + 0.5 * math.cos(6.283 * (hue - 0.67)))
            _rect(out, x + a * 0.04 * s * math.cos(v * 1.2), y + v * 0.07 * s, 0.005 * s, 0.005 * s,
                  c, 0.85, z + 0.0006)
    CUR['fl'] = 0.0


def _dumbo(out, x, y, s, t, z):
    col, lt = (0.88, 0.58, 0.56), (0.98, 0.76, 0.70)
    fa = 0.5 * math.sin(t * 3.0)
    for sgn in (-1, 1):
        _shape(out, _ell(x + sgn * 0.075 * s, y + 0.045 * s, 0.045 * s, 0.022 * s, 12, sgn * (0.5 + fa)),
               col, 1.0, z - 0.0005, lt, 1.0)
    _shape(out, [(x - 0.07 * s, y - 0.02 * s), (x + 0.07 * s, y - 0.02 * s), (x + 0.10 * s, y - 0.10 * s),
                 (x, y - 0.12 * s), (x - 0.10 * s, y - 0.10 * s)], col, 1.0, z - 0.0003, None, 1.0)
    _shape(out, _ell(x, y + 0.03 * s, 0.065 * s, 0.07 * s, 16), col, 1.0, z, lt, 1.0)
    for sgn in (-1, 1):
        _rect(out, x + sgn * 0.025 * s, y + 0.01 * s, 0.014 * s, 0.018 * s, INK, 1.0, z + 0.0006)


def _crab(out, x, y, s, t, z):
    col = (0.86, 0.36, 0.22)
    for k in range(3):
        for sgn in (-1, 1):
            a = 0.3 * math.sin(t * 8.0 + k + sgn)
            _seg(out, x + sgn * 0.02 * s, y + 0.01 * s, x + sgn * (0.05 * s + 0.01 * k * s),
                 y - 0.012 * s + 0.004 * s * a, col, 1.0, z - 0.0005, 0.005 * s)
    _shape(out, _ell(x, y + 0.018 * s, 0.035 * s, 0.020 * s, 12), col, 1.0, z, _mix(col, (1, 1, 1), 0.3),
           1.0, LWO * 0.6)
    for sgn in (-1, 1):
        _shape(out, _ell(x + sgn * 0.05 * s, y + 0.035 * s, 0.014 * s, 0.010 * s, 10), col, 1.0,
               z + 0.0003, None, 1.0, LWO * 0.5)


def _bubble(out, x, y, r, a, z):
    CUR['fl'] = 1.0
    _path(out, _ell(x, y, r, r, 10), BUBBLE, 0.55 * a, z, max(0.002, r * 0.22), close=True)
    _rect(out, x - r * 0.35, y + r * 0.35, r * 0.35, r * 0.35, (1, 1, 1), 0.8 * a, z + 0.0002)
    CUR['fl'] = 0.0


# --- him: position, pose and angle, from the story alone ----------------------------
def _path_at(f):
    return _sinterp(f, PATH_F, PATH_X), _sinterp(f, PATH_F, PATH_Y)


def _man_state(f):
    """(hip x, hip y, rotation, pose, face, jar-in-hand, helmet on)"""
    stand_y = BANKY + 0.47 * MANSC
    if f < 0.062:
        pose = 'look' if f < 0.028 else 'stand'
        return (-0.06, stand_y, 0.0, pose, 1.0, f < 0.042, f >= 0.042)
    if f < 0.086:                                       # the dive: up, over, in
        q = (f - 0.062) / 0.024
        x = -0.06 + 0.52 * q
        y = stand_y + (-0.30 - stand_y) * q ** 1.7 + 0.18 * math.sin(math.pi * q) * (1 - 0.3 * q)
        return (x, y, -2.30 * _ss(0.0, 0.8, q), 'dive', 1.0, False, True)
    if f < 0.100:
        q = _ss(0.086, 0.100, f)
        x0, y0 = 0.46, -0.30
        x1, y1 = _path_at(0.100)
        return (x0 + (x1 - x0) * q, y0 + (y1 - y0) * q, -2.30 + 0.9 * q, 'swim', 1.0, False, True)
    if f < 0.9505:
        x, y = _path_at(f)
        xa, ya = _path_at(f - 0.004)
        xb, yb = _path_at(f + 0.004)
        slope = math.atan2(yb - ya, max(1e-6, xb - xa))
        return (x, y, -1.5708 + slope, 'swim', 1.0, False, True)
    if f < 0.966:                                       # home: up to the surface
        q = _ss(0.9505, 0.966, f)
        return (0.95 - 0.45 * q, -0.62 + 0.62 * q - 0.12 * MANSC, -0.35 * (1 - q), 'tread',
                -1.0, False, True)
    if f < 0.976:                                       # swim to the bank
        q = _ss(0.966, 0.976, f)
        return (0.50 - 0.36 * q, -0.12 * MANSC, 0.0, 'tread', -1.0, False, True)
    if f < 0.986:                                       # climb out
        q = _ss(0.976, 0.986, f)
        return (0.14 - 0.20 * q, -0.12 * MANSC + (stand_y + 0.12 * MANSC) * q, 0.0,
                'stand', -1.0, False, True)
    return (-0.06, stand_y, 0.0, 'look', 1.0, f > 0.990, f <= 0.990)


# --- state -------------------------------------------------------------------------
def _new(seed):
    rs = random.Random(seed)
    canopy = [(TREEX + rs.uniform(-0.20, 0.26), rs.uniform(0.18, 0.52),
               rs.uniform(0.07, 0.13), rs.random()) for _ in range(16)]
    return {
        'seed': seed, 'rng': rs, 'canopy': canopy, 'flora': None, 'home': None,
        'cur': 0.0, 'ph': 0.0, 'lastf': None, 'lastt': None, 'lasty': None, 'loops': 0,
        'bubbles': [], 'drops': [], 'smoke': [], 'darts': [], 'pz': None,
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


def _frame(scriptOp):
    d = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    comp = scriptOp.parent()
    par = comp.par
    first = _S['S'] is None
    if first:
        _S['S'] = _new(SEED0)
    S = _S['S']
    if S['flora'] is None:
        S['flora'] = _gen_flora(S['rng'])
        S['home'] = _gen_home(S['rng'], S['canopy'])

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
    kickenv = ch('kickenv')
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
        S['flora'] = _gen_flora(S['rng'])
        S['home'] = _gen_home(S['rng'], S['canopy'])
    rs = S['rng']
    nkick = _delta(S, d, 'kickcnt')
    ndrop = _delta(S, d, 'dropcnt')
    nburst = _delta(S, d, 'gustcnt')

    slen = _sane(ch('storylen', STORYDEF), STORYDEF, 1.0, 1.0e5)
    f = _sane(ch('show', 0.0) / slen, 0.0, 0.0, 1.0)
    # THE LOOP SEAM (and any seek): phases and particle lists go back to empty
    if S['lastf'] is not None and (f < S['lastf'] - 0.5 or abs(f - S['lastf']) > 0.02):
        S['cur'] = 0.0
        S['bubbles'], S['drops'], S['smoke'], S['darts'] = [], [], [], []
        S['lasty'] = None
        if f < S['lastf'] - 0.5:
            S['loops'] += 1
    S['lastf'] = f
    loop = bool(par.Loop.eval())
    fade = (_ss(0.0, 0.010, f) * (1.0 - _ss(0.990, 1.0, f))) if loop else 1.0
    pace = float(par.Paceaudio.eval())
    sway = float(par.Sway.eval())
    # the CURRENT is where energy goes: an integrated phase that drives the schools,
    # the marine snow and the plants' sway speed. Reset at the seam.
    S['cur'] += dt * (0.35 + 0.65 * energy * pace)
    cur = S['cur']

    # --- him ---------------------------------------------------------------------
    hx, hy, rot, pose, face, jar, helmet = _man_state(f)
    gsun = _tab(f, GSUN_F, GSUN_H)
    burst = _ss(0.936, 0.950, f) * (1.0 - _ss(0.950, 0.962, f))
    swim = pose in ('swim', 'dive', 'tread')
    S['ph'] = (S['ph'] + dt * (1.6 if swim else 0.0) * (1.0 + 0.5 * energy)) % 1.0
    strike = kickenv ** 0.6 if pose == 'swim' else 0.0
    rr = []
    CUR['wl'], CUR['fl'] = 99.0, 0.0
    gx, gy = hx, hy - 0.47 * MANSC
    _man(rr, gx, gy, MANSC, face, pose, S['ph'], 0.55 if swim else 0.0, strike, t, 1.0,
         None, 0.012 * kickenv if pose in ('stand', 'look') else 0.0, 0.0,
         zover=0.60)
    R = np.array(rr, dtype=np.float64)
    if abs(rot) > 1e-4:
        ca, sa = math.cos(rot), math.sin(rot)
        for c0, c1 in ((0, 1), (2, 3)):
            X, Y = R[:, c0] - hx, R[:, c1] - hy
            R[:, c0] = hx + X * ca - Y * sa
            R[:, c1] = hy + X * sa + Y * ca
    ca, sa = math.cos(rot), math.sin(rot)

    def body(u, v):                                     # a point on him, rotated with him
        lx, ly = u * MANSC * face, (v - 0.47) * MANSC
        return (hx + lx * ca - ly * sa, hy + lx * sa + ly * ca)

    out = []
    # the glass jar he wears as a helmet, with a copper collar
    hc = body(0.04, 0.905)
    if helmet:
        hr = 0.135 * MANSC
        _fill(out, _ell(hc[0], hc[1], hr, hr, 20), GLASS, 0.16, 0.615, 10)
        CUR['fl'] = 1.0
        _path(out, _ell(hc[0], hc[1], hr, hr, 20), GLASS, 0.55, 0.616, 0.0035, close=True)
        arc = [(hc[0] + hr * 0.78 * math.cos(a), hc[1] + hr * 0.78 * math.sin(a))
               for a in (1.9, 2.2, 2.5, 2.8)]
        _path(out, arc, (1.0, 1.0, 1.0), 0.65, 0.617, 0.004)
        CUR['fl'] = 0.0
        c0, c1 = body(-0.09, 0.80), body(0.12, 0.80)
        _limb(out, c0[0], c0[1], c1[0], c1[1], 0.035 * MANSC, COPPER, None, 1.0, 0.614, 1.0)
    if jar:
        jx, jy = body(0.16, 0.44)
        _fill(out, _ell(jx, jy, 0.10 * MANSC, 0.12 * MANSC, 16), GLASS, 0.18, 0.62, 8)
        _path(out, _ell(jx, jy, 0.10 * MANSC, 0.12 * MANSC, 16), GLASS, 0.6, 0.621, 0.003,
              close=True)
    # his lantern, tied to his waist on a cord, trailing behind him
    D = -hy
    lant = _ss(1.2, 1.8, D) * (1.0 - burst)
    back = -1.0 if face > 0 else 1.0
    hip = body(0.0, 0.47)
    lpx = hip[0] + back * 0.10 + 0.012 * math.sin(t * 1.3)
    lpy = hip[1] - (0.13 if not swim else 0.06) + 0.010 * math.sin(t * 1.7)
    _seg(out, hip[0], hip[1], lpx, lpy + 0.025, INK, 1.0, 0.59, 0.003)
    lampv = lant * (0.84 + 0.10 * kickenv + 0.06 * math.sin(t * 5.3))
    CUR['fl'] = 1.0
    if lampv > 0.01:
        _fill(out, _ell(lpx, lpy, 0.045, 0.045, 16), _mul(WARM, 1.25), 0.40 * lampv, 0.588, 8)
    _fill(out, _ell(lpx, lpy, 0.013, 0.017, 12), _mix((0.55, 0.52, 0.45), (1.25, 1.1, 0.85),
                                                        lampv), 1.0, 0.590, 5)
    CUR['fl'] = 0.0
    _path(out, [(lpx - 0.018, lpy - 0.024), (lpx + 0.018, lpy - 0.024), (lpx + 0.018, lpy + 0.024),
                (lpx - 0.018, lpy + 0.024)], INK, 1.0, 0.591, 0.0032, close=True)

    # bubbles from the jar: a puff on the kick while he is under
    if hy < -0.05 and helmet and nkick:
        for _ in range(2):
            S['bubbles'].append([hc[0] + rs.uniform(-0.01, 0.01), hc[1] + 0.03,
                                 rs.uniform(0.006, 0.014), rs.random(), t])
    if nburst:
        for _ in range(25):
            S['bubbles'].append([hc[0] + rs.uniform(-0.1, 0.1), hc[1] + rs.uniform(-0.1, 0.05),
                                 rs.uniform(0.006, 0.02), rs.random(), t])
    # the bubble curtain that carries him home
    if burst > 0.05:
        cx0, cy0 = hx + 0.20, hy
        for _ in range(int(14 * burst)):
            S['bubbles'].append([cx0 + rs.uniform(-1.0, 1.0), cy0 + rs.uniform(-0.6, 0.5),
                                 rs.uniform(0.008, 0.035), rs.random(), t])
    del S['bubbles'][:-NBUBBLE]
    live = []
    for b in S['bubbles']:
        b[1] += dt * (0.16 + 3.0 * b[2])
        b[0] += dt * 0.03 * math.sin(t * 3.0 + b[3] * 6.0)
        if b[1] > -0.004 or t - b[4] > 8.0:
            continue
        live.append(b)
        _bubble(out, b[0], b[1], b[2], 1.0, 0.70)
    S['bubbles'] = live

    # splashes where he breaks the surface, in and out
    if S['lasty'] is not None and (S['lasty'] > 0.0) != (hy > 0.0) and abs(hy) < 0.3:
        for _ in range(16):
            S['drops'].append([hx + rs.uniform(-0.04, 0.04), 0.0, rs.uniform(-0.35, 0.35),
                               rs.uniform(0.25, 0.65), t])
    S['lasty'] = hy
    del S['drops'][:-NDROPS]
    live = []
    for dr in S['drops']:
        a = t - dr[4]
        y = dr[1] + dr[3] * a - 1.6 * a * a
        if y < -0.01 and a > 0.1:
            continue
        live.append(dr)
        _rect(out, dr[0] + dr[2] * a, y, 0.008, 0.012, BUBBLE, 0.8, 0.72)
    S['drops'] = live

    # --- the life of each zone, near the camera ----------------------------------
    camx = hx + 0.22
    camy = hy + 0.04
    kb = _ss(0.066, 0.102, f) * (1.0 - _ss(0.962, 0.980, f))
    camx = BANKCAM[0] + (camx - BANKCAM[0]) * kb
    camy = BANKCAM[1] + (camy - BANKCAM[1]) * kb

    def near(x, m=1.4):
        return abs(x - camx) < m

    if near(1.8, 1.6):
        _school(out, S, 101, 1.9 + 0.2 * math.sin(cur * 0.2), -0.60, 14, 0.030,
                (0.62, 0.64, 0.58), (0.86, 0.86, 0.80), cur, 0.2, 0.52, 0.22)
    if near(4.8, 1.7):
        _school(out, S, 202, 4.9 + 0.4 * math.sin(cur * 0.15), -0.95, 24, 0.034,
                (0.55, 0.62, 0.70), (0.85, 0.88, 0.92), cur, 0.35, 0.55, 0.30)
    if near(8.3, 1.8):
        _school(out, S, 303, 8.0, -1.62, 10, 0.040, (0.95, 0.80, 0.25), (1.0, 0.92, 0.55),
                cur, 0.3, 0.50, 0.25)
        _school(out, S, 304, 9.2, -1.75, 8, 0.040, (0.35, 0.50, 0.90), (0.60, 0.72, 1.0),
                cur, 0.25, 0.51, 0.20)
        for (tp, ax, ay) in S['flora']['tips']:
            if tp == 'anemone' and 7.8 < ax < 8.8:
                _school(out, S, int(ax * 100), ax, ay + 0.03, 2, 0.032, (0.98, 0.50, 0.15),
                        (1.0, 0.70, 0.35), cur * 1.4, 0.2, 0.53, 0.05, bands=(0.18, -0.05, -0.30))
                break
        tq = _cl((f - 0.330) / 0.110)
        if 0.0 < tq < 1.0:
            _turtle(out, 6.9 + 3.6 * tq, -1.12 - 0.25 * tq + 0.03 * math.sin(t), 1.05, t, 0.50)
    if near(12.0, 2.2):
        for i, (jx, jy, js, jp) in enumerate(((10.9, -2.25, 0.07, 0.0), (11.5, -2.70, 0.05, 1.3),
                                              (12.1, -2.35, 0.09, 2.1), (12.6, -3.00, 0.06, 0.7),
                                              (13.0, -2.55, 0.05, 3.1), (11.9, -3.25, 0.08, 1.9),
                                              (13.4, -3.40, 0.06, 2.6))):
            # the bell pulses on the kick, and each pulse lifts it a little
            yy = jy + 0.05 * math.sin(cur * 0.3 + jp) + 0.012 * kickenv
            col = ((0.92, 0.66, 0.84), (0.70, 0.74, 0.98), (0.98, 0.78, 0.60))[i % 3]
            _jelly(out, jx, yy, js, kickenv, t, jp, col, 0.50 + 0.01 * i)
    if 0.545 < f < 0.668:
        wq = (f - 0.545) / 0.123
        # placed against the camera so it always crosses the frame: in from the right,
        # slowly past behind him, out on the left
        _whale(out, camx + 2.0 - 4.2 * wq, camy - 0.08 + 0.06 * math.sin(t * 0.3), 0.85, t,
               0.40)
    if near(17.8, 2.0):
        _angler(out, 18.25 + 0.05 * math.sin(t * 0.4), -4.93 + 0.03 * math.sin(t * 0.7), 1.0,
                t, high, 0.55)
        for (cx_, cy_) in ((16.9, -4.55), (18.3, -5.40), (18.9, -4.95)):
            _comb(out, cx_, cy_ + 0.04 * math.sin(t * 0.5 + cx_), 1.4, t, high, 0.50)
    if near(21.0, 2.0):
        _dumbo(out, 21.35 + 0.1 * math.sin(t * 0.25), -6.42 + 0.05 * math.sin(t * 1.1), 0.85, t,
               0.52)
        for (cx_, ph_) in ((19.9, 0.0), (21.2, 1.7), (22.4, 3.1)):
            x = cx_ + 0.15 * math.sin(t * 0.6 + ph_)
            _crab(out, x, floor_y(x), 1.2, t, 0.40)
        # tube worm plumes snap back into their tubes on the kick
        pl = 1.0 - 0.75 * kickenv
        for (tp, ax, ay) in S['flora']['tips']:
            if tp == 'worm' and near(ax, 1.5):
                # plain strokes, not outlined limbs: sixty worms x five plumes of
                # outlined limbs was the most expensive thing in the scene
                for j in range(4):
                    a = 1.5708 + (j - 1.5) * 0.40 + 0.1 * math.sin(t * 2.0 + ax * 9.0)
                    _seg(out, ax, ay, ax + math.cos(a) * 0.035 * pl, ay + math.sin(a) * 0.035 * pl,
                         (0.90, 0.20, 0.18), 1.0, 0.345, 0.008)
            elif tp == 'chimney' and near(ax, 1.5) and rs.random() < 0.25:
                if len(S['smoke']) < NSMOKE:
                    S['smoke'].append([ax + rs.uniform(-0.02, 0.02), ay, t, rs.random()])
    live = []
    for sm in S['smoke']:
        a = t - sm[2]
        if a > 4.0:
            continue
        live.append(sm)
        r = 0.015 + 0.025 * a
        _fill(out, _ell(sm[0] + 0.03 * a * math.sin(sm[3] * 6 + a), sm[1] + 0.09 * a, r, r * 0.85, 10),
              (0.12, 0.11, 0.12), 0.45 * (1.0 - a / 4.0), 0.325, 3)
    S['smoke'] = live
    # a drop sends a flash of fish darting past him
    if ndrop and len(S['darts']) < 2 and hy < -0.2:
        S['darts'].append([t, rs.uniform(-0.2, 0.2), rs.random()])
    live = []
    for dd in S['darts']:
        a = (t - dd[0]) / 1.6
        if a > 1.0:
            continue
        live.append(dd)
        cx_ = camx + 1.3 - 2.8 * a
        _school(out, S, int(dd[2] * 1000), cx_, camy + dd[1], 12, 0.028, (0.78, 0.82, 0.86),
                (0.95, 0.96, 0.98), t * 2.0, 0.15, 0.75, 0.12)
    S['darts'] = live

    # --- the static sea bed and the home bank, culled and swayed -----------------
    Fl = S['flora']
    i0, i1 = np.searchsorted(Fl['xs'], (camx - 1.35, camx + 1.35))
    m = slice(int(i0), int(i1))
    FA = Fl['A'][m].copy()
    swy = (0.012 + 0.020 * bass * sway) * np.sin(cur * 0.9 + Fl['ph'][m]
                                                   + FA[:, 1] * 1.3) * Fl['w'][m]
    FA[:, 0] += swy
    FA[:, 2] += swy * 1.15
    parts = [R, FA]
    if out:
        parts.append(np.array(out, dtype=np.float64))
    if camx < 1.6:
        parts.append(S['home'])
    A = np.concatenate(parts, axis=0)

    # --- light every cel by the water above it -----------------------------------
    # Water eats red first, then green: the ambient at a row is the surface light
    # attenuated per channel by its own depth. His lantern gives the true colours
    # back to whatever it is near, which is the only warm thing down there.
    my_ = (A[:, 1] + A[:, 3]) * 0.5
    mx_ = (A[:, 0] + A[:, 2]) * 0.5
    Dr = np.maximum(-my_, 0.0)
    surf = np.array([_tab(gsun, AMB_H, AMB_R), _tab(gsun, AMB_H, AMB_G),
                     _tab(gsun, AMB_H, AMB_B)])
    ab = np.array(ABSORB)
    L = surf[None, :] * np.exp(-np.outer(Dr, ab)) * np.exp(-Dr * DIMDEPTH)[:, None]
    L = np.maximum(L, np.array([0.010, 0.016, 0.030])[None, :])
    L = np.where((my_ < 0.0)[:, None], L * 0.95 + np.array([0.02, 0.05, 0.06]) * (Dr < 1.5)[:, None],
                 surf[None, :])
    dd = (mx_ - lpx) ** 2 + ((my_ - lpy) * 1.1) ** 2
    L += np.outer(lampv * 0.85 / (1.0 + dd * 22.0), np.array(WARM))
    vent = _ss(19.0, 19.6, camx) * (1.0 - _ss(23.2, 23.8, camx))
    if vent > 0.0:
        L += np.outer(vent * 0.10 / (1.0 + np.abs(my_ + 6.8) * 6.0), np.array((1.0, 0.45, 0.2)))
    lit = A[:, 9] < 0.5
    ink = float(par.Ink.eval())
    A[lit, 4:7] = A[lit, 4:7] * L[lit] * ink

    # --- to the camera, cull, order, publish -------------------------------------
    A[:, [0, 2]] -= camx
    A[:, [1, 3]] -= camy
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
    vals = dict(Chapter=cp, Segs=n, Camx=camx, Camy=camy, Current=cur, Gsun=gsun,
                Burst=burst, Lant=lampv, Lx=lpx, Ly=lpy, Vent=vent, Fade=fade,
                Loops=S['loops'], Depth=D, Rejects=S.get('rejects', 0), Labelfade=lf)
    try:
        for k3, v in vals.items():
            getattr(par, k3).val = _sane(v, 0.0)
        txt = CHECKPOINTS[cp][1].strip()
        if par.Scaletxt.eval() != txt:
            par.Scaletxt.val = txt
    except Exception:
        pass
    S['census'] = ('f %.3f | pose %s | at (%.2f, %.2f) | quads %d/%d | bubbles %d | '
                   'loops %d | rejects %d' % (f, pose, hx, hy, n, MAXSEG, len(S['bubbles']),
                                              S['loops'], S.get('rejects', 0)))
    return


def _publish(scriptOp, outc):
    # NEVER clear() AND RE-APPEND CHANNELS EVERY FRAME: it leaks native memory inside
    # TouchDesigner (see the skill's debugging.md). Build once, then only write.
    # (numChans cannot be read inside a cook, so "built" is tracked here.)
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
                print('[fathom engine] frame failed:\n' + S['lasterr'])
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
    CHECKPOINTS=CHECKPOINTS, MAXSEG=MAXSEG, SEED0=20260925,
    CH=('tx', 'ty', 'tz', 'rz', 'sx', 'sy', 'sz', 'r', 'g', 'b', 'a'),
    # homestead's geography, for its verbatim house and tree generators
    FARY=0.020, SHOREY=-0.125, SHOREX=0.160, BANKK=0.600, BANKH=0.440,
    GYH=-0.265, FLOORY=-0.195, WALLTOP=0.012, HX0=-0.640, HX1=-0.205, MANGY=-0.330,
    WX=0.530, WY=-0.205, WR=0.092, WWL=-0.270, BULB=(-0.188, -0.030),
    GARDEN=(-0.115, 0.235, -0.505, -0.365), ROWS=(-0.385, -0.430, -0.475),
    TREEX=-0.905, CLR0=-0.760, CLR1=0.300,
    MANSC=MANSC, BANKY=BANKY, BANKCAM=BANKCAM,
    FLOOR_X=FLOOR_X, FLOOR_Y=FLOOR_Y, PATH_F=PATH_F, PATH_X=PATH_X, PATH_Y=PATH_Y,
    GSUN_F=GSUN_F, GSUN_H=GSUN_H, AMB_H=AMB_H, AMB_R=AMB_R, AMB_G=AMB_G, AMB_B=AMB_B,
    ABSORB=ABSORB, DIMDEPTH=DIMDEPTH, STORYDEF=STORYDEF,
    LWO=0.0046, LWT=0.0032, HS=1.30,
    NBUBBLE=260, NDROPS=40, NSMOKE=30,
    CULLX=1.10, CULLY=0.66, MINLEN=0.0004, MAXW=0.80, MAXL=3.00,
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
#@INCLUDE SHAPE_BODY = '''# ONE UNIT QUAD|||def _g3(c):


def _g3(c):
    return 'vec3(%.4f, %.4f, %.4f)' % c


def _garr(v):
    return 'float[%d](%s)' % (len(v), ', '.join('%.5f' % x for x in v))


world = C(glslTOP, 'world', 2260, 200)
res(world)
world_pix = C(textDAT, 'world_pixel', 2260, 120)
world_pix.text = ('''// THE PAINTED WATER. Above the surface: homestead's sky, hills and jungle
// (verbatim), his bank and the river's far surface. Below it: the water column,
// coloured by depth and dimming to black; light shafts and the bright underside of
// the surface near the top; caustics dancing on a shallow bed; marine snow drifting
// in the current; distant rock silhouettes; and, in the abyss, bioluminescent
// sparks that twinkle with the highs. His lantern scatters warm light through the
// water around him.
//
// Every scalar arrives on the Vectors page and goes through san() first.
uniform vec4 uA;   // x story time, y cam x, z cam y, w current (integrated)
uniform vec4 uB;   // x bass, y high, z kick, w loop fade
uniform vec4 uC;   // x vignette, y brightness, z glow, w label fade
uniform vec4 uD;   // x sun height, y bubble burst, z lantern, w vent glow
uniform vec4 uL;   // x lantern x, y lantern y (world)
out vec4 fragColor;

const float OW = ''' + repr(ORTHOW) + ''';
const float OH = ''' + repr(ORTHOH) + ''';
const float FARY = 0.035;          // the far bank's horizon, just above the surface
const float CAMX = 0.0;
const float CAMY = 0.0;
const float SHOREY = -0.125;
const float SHOREX = 0.160;
const float BANKK = 0.600;
const float BANKH = 0.440;
const vec2 BULB = vec2(-0.93, 0.05);
const vec3 WARM = ''' + _g3(PAL['WARM']) + ''';
const float SUNY0 = 0.085;
const float SUNYK = 0.27;
const vec2 MOONP = vec2(0.46, 0.36);
const float BANKY = ''' + repr(BANKY) + ''';
const float FX[''' + str(len(FLOOR_X)) + '''] = ''' + _garr(FLOOR_X) + ''';
const float FY[''' + str(len(FLOOR_Y)) + '''] = ''' + _garr(FLOOR_Y) + ''';

//@INCLUDE float san(float v|||float sheet(vec2 uv

// ================================================================================
// THE WATER
// ================================================================================
float floorY(float x) {
    float y = FY[0];
    if (x >= FX[''' + str(len(FLOOR_X) - 1) + ''']) {
        y = FY[''' + str(len(FLOOR_Y) - 1) + '''];
    } else {
        for (int i = 0; i < ''' + str(len(FLOOR_X) - 1) + '''; i++) {
            if (x >= FX[i] && x < FX[i + 1]) {
                float q = (x - FX[i]) / (FX[i + 1] - FX[i]);
                q = q * q * (3.0 - 2.0 * q);
                y = mix(FY[i], FY[i + 1], q);
            }
        }
    }
    float bump = 0.030 * sin(x * 2.3) + 0.018 * sin(x * 5.7 + 1.3) + 0.008 * sin(x * 13.1 + 0.7);
    return y + bump * clamp(x / 0.4, 0.0, 1.0);
}

float surfY(float x, float t) {
    return 0.004 * sin(x * 14.0 - t * 1.4) + 0.003 * sin(x * 31.0 + t * 2.1);
}

vec3 waterColour(float D) {
    vec3 c = mix(vec3(0.20, 0.40, 0.42), vec3(0.06, 0.18, 0.30), smoothstep(0.0, 1.6, D));
    c = mix(c, vec3(0.018, 0.055, 0.12), smoothstep(1.4, 3.6, D));
    c = mix(c, vec3(0.004, 0.008, 0.022), smoothstep(3.6, 6.0, D));
    return c;
}

void main() {
    vec2 uv = vUV.st;
    float t     = san(uA.x, 0.0, 1.0e6, 0.0);
    vec2 cam    = vec2(san(uA.y, -10.0, 100.0, 0.0), san(uA.z, -100.0, 10.0, 0.0));
    float cur   = san(uA.w, 0.0, 1.0e5, 0.0);
    float bass  = san(uB.x, 0.0, 2.0, 0.0);
    float high  = san(uB.y, 0.0, 2.0, 0.0);
    float kick  = pow(san(uB.z, 0.0, 1.0, 0.0), 0.7);
    float fade  = san(uB.w, 0.0, 1.0, 1.0);
    float vign  = san(uC.x, 0.0, 2.0, 0.75);
    float brite = san(uC.y, 0.2, 4.0, 1.0);
    float glowa = san(uC.z, 0.0, 4.0, 0.4);
    float labf  = san(uC.w, 0.0, 1.0, 0.0);
    float gsun  = san(uD.x, -1.0, 1.0, 0.3);
    float burst = san(uD.y, 0.0, 1.0, 0.0);
    float lant  = san(uD.z, 0.0, 2.0, 0.0);
    float vent  = san(uD.w, 0.0, 1.0, 0.0);
    vec2 lp     = vec2(san(uL.x, -100.0, 100.0, 0.0), san(uL.y, -100.0, 100.0, 0.0));

    vec2 w = vec2((uv.x - 0.5) * OW, (uv.y - 0.5) * OH) + cam;
    vec3 amb = ambient(gsun);
    float daylum = dot(amb, vec3(0.33)) * 1.4;
    float fy = floorY(w.x);
    float sy = surfY(w.x, t);
    float D = max(-w.y, 0.0);
    vec3 col;

    if (w.y > sy) {
        if (w.y < fy) {
            // --- his bank, above the water ------------------------------------------
            float e = fy - w.y;
            float n = fbm(w * vec2(14.0, 30.0));
            vec3 grass = mix(vec3(0.20, 0.26, 0.10), vec3(0.36, 0.40, 0.17), n);
            vec3 earth = vec3(0.34, 0.24, 0.15) * (0.8 + 0.3 * fbm3(w * 40.0));
            col = mix(grass, earth, smoothstep(0.010, 0.030, e)) * amb;
        } else if (w.y < FARY) {
            // --- the river's surface, running away to the far bank -------------------
            float q = (w.y - sy) / max(FARY - sy, 1e-4);
            vec3 refl = skyHor(gsun) * 0.8;
            col = mix(refl * (0.75 + 0.25 * fbm3(vec2(w.x * 30.0 - t * 0.3, q * 40.0))),
                      vec3(0.12, 0.20, 0.22) * amb, 0.35 * (1.0 - q));
        } else {
            col = above(w, gsun, VP_X_SUN(w), t * 0.004, t, high, 0.0, false, kick);
        }
    } else if (w.y < fy) {
        // --- the sea bed ------------------------------------------------------------
        float e = fy - w.y;
        vec3 sand = mix(vec3(0.60, 0.54, 0.40), vec3(0.34, 0.35, 0.40), smoothstep(1.0, 4.5, D));
        sand *= 0.78 + 0.35 * fbm(w * vec2(9.0, 22.0));
        sand = mix(sand, sand * 0.45, smoothstep(0.02, 0.35, e));
        vec3 lightD = exp(-D * vec3(0.62, 0.26, 0.16)) * exp(-D * 0.26);
        col = sand * (amb * lightD * 1.1 + vec3(0.010, 0.016, 0.030));
        // caustics on a shallow bed
        if (D < 3.0) {
            vec2 cp = w * vec2(7.0, 11.0) + vec2(t * 0.15, t * 0.09);
            float c = abs(sin(fbm3(cp) * 11.0)) * abs(sin(fbm3(cp * 1.3 + 4.0) * 9.0));
            c = pow(1.0 - c, 7.0);
            col += vec3(0.55, 0.75, 0.70) * c * 0.45 * exp(-D * 0.9) * smoothstep(0.12, 0.0, e) * daylum;
        }
        col += vec3(1.0, 0.42, 0.16) * vent * 0.20 * exp(-e * 8.0) * (0.8 + 0.2 * sin(t * 3.0 + w.x * 20.0));
    } else {
        // --- the water column -------------------------------------------------------
        col = waterColour(D) * (0.40 + 0.60 * daylum);
        // brighter toward the surface, as it is from below
        col += vec3(0.30, 0.50, 0.50) * exp(-(sy - w.y) * 18.0) * 0.35 * daylum;
        // light shafts, slanting down from the surface
        if (D < 3.2) {
            float rx = w.x + w.y * 0.35;
            float r = fbm3(vec2(rx * 3.2 + t * 0.03, t * 0.04));
            r = pow(smoothstep(0.50, 0.92, r), 2.0);
            col += vec3(0.30, 0.50, 0.50) * r * 0.40 * exp(-D * 0.85) * daylum;
        }
        // distant rocks, a hazy silhouette behind everything (parallax 0.55)
        float bx = cam.x + (w.x - cam.x) * 0.55 + 7.3;
        float by = floorY(bx) * 0.55 + cam.y * 0.45 + 0.30 + 0.06 * fbm3(vec2(bx * 2.0, 3.0));
        if (w.y < by) col = mix(col, col * 0.55 + waterColour(D + 0.8) * 0.15, 0.55);
        // marine snow, drifting in the current
        vec2 sp = w * 34.0 + vec2(cur * 1.4, t * 0.25);
        vec2 si = floor(sp);
        float sh = hash21(si);
        vec2 sf = fract(sp) - 0.5 - (vec2(hash21(si + 3.0), hash21(si + 7.0)) - 0.5) * 0.6;
        col += vec3(0.55, 0.62, 0.66) * step(0.93, sh) * exp(-dot(sf, sf) / 0.004) * 0.22
               * (0.35 + 0.65 * smoothstep(1.0, 3.0, D));
        // bioluminescence in the dark, twinkling with the highs
        if (D > 3.8) {
            vec2 bp = w * 22.0 + vec2(cur * 0.6, 0.0);
            vec2 bi = floor(bp);
            float bh = hash21(bi + 17.0);
            vec2 bf = fract(bp) - 0.5;
            float tw = 0.5 + 0.5 * sin(t * (2.0 + 5.0 * bh) * (0.6 + 1.2 * high) + bh * 40.0);
            col += mix(vec3(0.30, 0.95, 0.85), vec3(0.50, 0.60, 1.0), bh) * step(0.975, bh)
                   * exp(-dot(bf, bf) / 0.006) * tw * 0.9 * smoothstep(3.8, 5.0, D);
        }
    }
    // his lantern, scattering warm light through the water
    if (w.y < 0.0) {
        float dl = length((w - lp) * vec2(1.0, 1.1));
        col += WARM * lant * (0.20 * exp(-dl * 7.0) + 0.06 * exp(-dl * 2.0));
    }
    // the curtain of bubbles that carries him home
    if (burst > 0.001) {
        float b = fbm(w * 9.0 + vec2(0.0, -t * 1.5));
        col = mix(col, vec3(0.70, 0.88, 0.92) * (0.75 + 0.35 * b), burst * 0.92);
    }

    // --- the cels, and their glow ----------------------------------------------------
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

    // --- grade (homestead's) ---------------------------------------------------------
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
        outc = vec3(0.01, 0.03, 0.05) * fade;
    }
    fragColor = TDOutputSwizzle(vec4(outc, 1.0));
}
''').replace('VP_X_SUN(w)', '(cam.x + 0.30)')
world.par.pixeldat = world_pix.name
W(render_cels, world, 0)
W(glow_blur, world, 1)

_U = [('uA', ('Showt', 'Camx', 'Camy', 'Current')),
      ('uB', (D('bass'), D('high'), D('kickenv'), 'Fade')),
      ('uC', ('Vignette', 'Brightness', None, 'Labelfade')),
      ('uD', ('Gsun', 'Burst', 'Lant', 'Vent')),
      ('uL', ('Lx', 'Ly', None, None))]
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
# glow is what EMITS: the lantern, the lure, the comb jellies, the bubbles
world.par.vec2valuez.expr = 'parent().par.Glow * 0.50'

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
pout.nodeX, pout.nodeY = 400, -3200
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
    if n == 'Bubbles':
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
soft(pexec, pars='Bubbles Reseed Restart Nextcp Prevcp '
     + ' '.join('Go' + cp[0] for cp in CHECKPOINTS),
     valuechange=False, onpulse=True)

KEY_BODY = '''# 1-9 walk the dive to a chapter; 0 starts it again.
#   b  BUBBLES — a burst from his helmet
#   n  RESEED  — a new sea


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
    elif k == 'b':
        comp.par.Bubbles.pulse()
    elif k == 'n':
        comp.par.Reseed.pulse()
    return


def onShortcut(dat, shortcutName, time):
    return
'''

keyin = C(keyboardinDAT, 'key_pad', 1780, 700)
keyin.par.keys = '1 2 3 4 5 6 7 8 9 0 b n'
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
print('  keys: 1-9 chapters | 0 restart | b bubbles | n reseed')
