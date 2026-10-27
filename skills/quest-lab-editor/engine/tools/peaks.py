import json, sys
E = json.load(open(sys.argv[1]))
n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
ev = sorted(E['events'], key=lambda e: -e['peak'])
print('time      tier    peak  loud  pitch move word')
for e in ev[:n]:
    t = e['t']
    print(f"{int(t // 60):02d}:{t % 60:05.2f}  {e['tier']:7s} {e['peak']:.2f}  {e['loud']:+.1f}  {e['pitch']:+.1f}  {e['move']:+.1f}  {e['word']:.1f}")
