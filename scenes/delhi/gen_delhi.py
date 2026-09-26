# Assemble scenes/delhi/build.py from delhi_template.py + verbatim blocks of
# scenes/homestead/build.py. Run from anywhere:  python3 scenes/delhi/gen_delhi.py
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HS = open(os.path.join(HERE, '..', 'homestead', 'build.py'), encoding='utf-8').read()
T = open(os.path.join(HERE, 'delhi_template.py'), encoding='utf-8').read()

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

open(os.path.join(HERE, 'build.py'), 'w', encoding='utf-8').write(src)
compile(src, 'build.py', 'exec')
print('ok', src.count('\n'), 'lines')
