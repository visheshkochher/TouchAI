# Assemble scenes/voyage/build.py from voyage_template.py + verbatim blocks of
# scenes/homestead/build.py. Run from anywhere:  python3 scenes/voyage/gen_voyage.py
import os
import re
HERE = os.path.dirname(os.path.abspath(__file__))
HS = open(os.path.join(HERE, '..', 'homestead', 'build.py'), encoding='utf-8').read()
T = open(os.path.join(HERE, 'voyage_template.py'), encoding='utf-8').read()
out = []
for line in T.split('\n'):
    m = re.match(r'^\s*(#|//)@INCLUDE (.*)$', line)
    if not m:
        out.append(line); continue
    a, b = m.group(2).split('|||')
    a, b = a.replace('\\n', '\n'), b.replace('\\n', '\n')
    ia = HS.index(a)
    ib = HS.index(b, ia + len(a))
    assert HS.count(a) == 1, a
    block = HS[ia:ib].rstrip('\n')
    cm = m.group(1)
    out.append('%s ---- BEGIN HOMESTEAD (verbatim) ----' % cm)
    out.append(block)
    out.append('%s ---- END HOMESTEAD ----' % cm)
src = '\n'.join(out)
# the homestead sky dissolves into space as he climbs: one line, before the hills
anchor = '    // far range, deep in aerial perspective'
assert src.count(anchor) == 1
src = src.replace(anchor, '    // (voyage) the sky dissolves into space as he climbs\n    col = mix(col, gSpace, gSF);\n' + anchor)
for a, b in (("    vec2 sp = vec2(sunx, FARY + SUNY0 + sunh * SUNYK);",
              "    vec2 sp = vec2(sunx, FARY + SUNY0 + sunh * SUNYK + gAlt);"),
             ("    vec2 mp = MOONP;", "    vec2 mp = MOONP + vec2(0.0, gAlt);"),
             ("    float topfrac = (w.y - CAMY) / (OH * 0.5);",
              "    float topfrac = (w.y - gAlt - CAMY) / (OH * 0.5);")):
    assert src.count(a) == 1, a
    src = src.replace(a, b + '   // (voyage) pinned to the altitude')
import os
open(os.path.join(HERE, 'build.py'), 'w', encoding='utf-8').write(src)
compile(src, 'build.py', 'exec')
print('ok', src.count('\n'), 'lines')
