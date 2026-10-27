"""Print SRT cues around given SOURCE times, via the edit timeline. usage: srt_at_src.py <edit.json> <file.srt> t1 t2 ..."""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
E = json.load(open(sys.argv[1]))
def ts(x): h, m, r = x.split(':'); s, ms = r.split(','); return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
cues = []
for b in re.split(r'\r?\n\r?\n', open(sys.argv[2], encoding='utf-8-sig').read().strip()):
    ln = b.splitlines(); a, z = [ts(x.strip()) for x in ln[1].split('-->')]; cues.append((a, z, ' / '.join(ln[2:])))
for st in map(float, sys.argv[3:]):
    outs = [s['t0'] + (st - s['src0']) / s['speed'] for s in E['shots'] if not s['freeze'] and s['speed'] and s['src0'] <= st <= s['src0'] + (s['t1'] - s['t0']) * s['speed']]
    for o in outs:
        near = [c for c in cues if c[1] > o - .3 and c[0] < o + 3.0]
        print(f'src {st:8.2f} -> out {o:7.2f}:  ' + '  ||  '.join(f'[{c[0]:.1f}] {c[2]}' for c in near))
