# Assemble scenes/fathom/build.py from fathom_template.py + verbatim blocks of
# scenes/homestead/build.py. Run from anywhere:  python3 scenes/fathom/gen_fathom.py
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HS = open(os.path.join(HERE, '..', 'homestead', 'build.py'), encoding='utf-8').read()
T = open(os.path.join(HERE, 'fathom_template.py'), encoding='utf-8').read()

out = []
for line in T.split('\n'):
    m = re.match(r'^\s*(#|//)@INCLUDE (.*)$', line)
    if not m:
        out.append(line)
        continue
    a, b = m.group(2).split('|||')
    a, b = a.replace('\\n', '\n'), b.replace('\\n', '\n')
    assert HS.count(a) == 1, a
    ia = HS.index(a)
    ib = HS.index(b, ia + len(a))
    cm = m.group(1)
    out.append('%s ---- BEGIN HOMESTEAD (verbatim) ----' % cm)
    out.append(HS[ia:ib].rstrip('\n'))
    out.append('%s ---- END HOMESTEAD ----' % cm)
src = '\n'.join(out)

# the man learns to swim: three poses added to homestead's _man, in place
anchor = "    elif pose == 'switch':"
assert src.count(anchor) == 1
src = src.replace(anchor, """    elif pose == 'swim':                                # (fathom) a stroke on the kick
        F = (2.95 - 1.70 * strike, 0.30 - 0.25 * strike)
        B = (2.85 - 1.40 * strike, 0.25)
    elif pose == 'dive':                                # (fathom) arms over his head
        F = (3.05, 0.05)
        B = (2.95, 0.08)
    elif pose == 'tread':                               # (fathom) sculling, head up
        F = (1.25 + 0.35 * math.sin(t * 3.0), 0.45)
        B = (1.15 - 0.35 * math.sin(t * 3.0), 0.45)
""" + anchor)

open(os.path.join(HERE, 'build.py'), 'w', encoding='utf-8').write(src)
compile(src, 'build.py', 'exec')
print('ok', src.count('\n'), 'lines')
