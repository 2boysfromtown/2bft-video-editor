import json, sys
sys.stdout.reconfigure(encoding='utf-8')
E = json.load(open(sys.argv[1], encoding='utf-8'))
print('00:00 Cold open')
for g in sorted([g for g in E['gfx'] if g['type'] == 'level'], key=lambda g: g['t']):
    t = max(0, g['t']); title = g['title'].replace(' / ', ' ').replace('/', ' ').title()
    print(f"{int(t // 60):02d}:{int(t % 60):02d} {g.get('kicker') or ('Level ' + g['num'])} — {title}")
print(f"(duration {E['dur']:.1f}s)")
