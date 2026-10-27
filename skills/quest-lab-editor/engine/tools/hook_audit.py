"""Where does each Short's top text sit? Lists hook / top-anchored gfx with their pixel band (1080x1920)."""
import glob, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
# usage: hook_audit.py <project folder> [<project folder> ...]   (reads each one's edits/s*.json)
for proj in sys.argv[1:] or ['.']:
    for f in sorted(glob.glob(os.path.join(proj, 'edits', 's[01]*.json'))):
        if f.endswith('.audio.json'): continue
        E = json.load(open(f, encoding='utf-8')); name = os.path.basename(f)[:-5]
        if E['h'] != 1920: continue
        for g in E['gfx']:
            if g['type'] == 'hook':
                size = g.get('size', 64); y = g.get('y', 230); n = len(g['lines'])
                top = y - size * .9; bot = y + (n - 1) * size * 1.22 + size * .25
                print(f"{name:16s} {proj}  hook y={y:4} size={size:3} lines={n}  band {top:5.0f}-{bot:5.0f}  t {g['t0']:.1f}-{g['t1']:.1f}  {' / '.join(g['lines'])}")
