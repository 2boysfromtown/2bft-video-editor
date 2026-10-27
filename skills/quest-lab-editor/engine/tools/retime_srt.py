"""Re-time an SRT made for an old cut onto a new cut of the same plan: map each cue through source time.
usage: retime_srt.py <old_edit.json> <new_edit.json> <in.srt> <out.srt>"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
old, new = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
def to_src(E, t):
    for s in E['shots']:
        if s['t0'] <= t < s['t1'] + 1e-6:
            if s['freeze'] or not s['speed']: return None
            return s['src0'] + (t - s['t0']) * s['speed']
    return None
def to_out(E, st):
    for s in E['shots']:
        if s['freeze'] or not s['speed']: continue
        a = s['src0']; b = a + (s['t1'] - s['t0']) * s['speed']
        if a - 1e-3 <= st <= b + 1e-3: return s['t0'] + (st - a) / s['speed']
    return None
def ts(x): h, m, r = x.split(':'); s, ms = r.split(','); return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
def fmt(t): t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = int(t % 60); ms = int(round((t - int(t)) * 1000)); ms = min(ms, 999); return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
blocks = re.split(r'\r?\n\r?\n', open(sys.argv[3], encoding='utf-8').read().strip())
out, dropped = [], []
for b in blocks:
    lines = b.splitlines(); a, z = [ts(x.strip()) for x in lines[1].split('-->')]
    # map start/end; a cue that falls inside removed material is dropped, one that straddles the cut is trimmed
    sa, sz = to_src(old, a), to_src(old, z - .001)
    na = to_out(new, sa) if sa is not None else None
    nz = to_out(new, sz) if sz is not None else None
    if na is None and nz is None: dropped.append((a, z, ' / '.join(lines[2:]))); continue
    if na is None or nz is None or nz <= na:
        # straddles the cut: keep the surviving side
        if na is None: na = nz - min(1.5, z - a)
        if nz is None or nz <= na: nz = na + min(1.5, z - a)
    out.append((na, nz + .001, lines[2:]))
out.sort(key=lambda c: c[0])
for i in range(1, len(out)):   # no overlaps after re-timing
    if out[i][0] < out[i - 1][1]: out[i - 1] = (out[i - 1][0], out[i][0] - .02, out[i - 1][2])
with open(sys.argv[4], 'w', encoding='utf-8', newline='\n') as f:
    for i, (a, z, txt) in enumerate(out, 1): f.write(f"{i}\n{fmt(a)} --> {fmt(z)}\n" + '\n'.join(txt) + '\n\n')
print(f'{len(blocks)} cues in, {len(out)} out, dropped {len(dropped)}:'); [print(f'  {a:.2f}-{z:.2f}  {t}') for a, z, t in dropped]
