"""Print transcript words with source times in a range.  usage: words.py <transcript.json> <from mm:ss> <to mm:ss> [--seg]"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
def ts(x):
    if ':' in x: m, s = x.split(':'); return int(m) * 60 + float(s)
    return float(x)
T = json.load(open(sys.argv[1], encoding='utf-8')); a, b = ts(sys.argv[2]), ts(sys.argv[3])
for seg in T['segments']:
    if seg['e'] < a or seg['s'] > b: continue
    if '--seg' in sys.argv:
        print(f"[{seg['s']:.2f}-{seg['e']:.2f}] {seg['t']}"); continue
    line = ' '.join(f"{w['w'].strip()}@{w['s']:.2f}" for w in seg['words'] if a <= w['s'] <= b)
    if line: print(line)
