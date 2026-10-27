import json, sys
E = json.load(open(sys.argv[1]))
print('  '.join(f"{i}:{s['t0']:.1f}{(s['layout'] or '?')[:4]}" for i, s in enumerate(E['shots'])))
