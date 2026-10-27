"""Pack a word-level transcript into a short phrase-per-line markdown file the editor can read in one go.

usage: packed_transcript.py <transcript.json> <out.md> [--gap 0.5] [--from mm:ss] [--to mm:ss]

A new line starts at every pause >= --gap seconds. Each line: [start-end] text.
Marks (so cut decisions don't trust bad timings):
  word~      the word lasts > 1.0 s - a pause or retake is hidden inside it; never cut on its edges
  (?word)    low confidence (p < 0.35)
  {HALLU?}   a segment that looks like Whisper filling silence (no-speech prob > 0.6 or a stock phrase)
  ...N.Ns    pause length before the line when >= 1.5 s
Idea from browser-use/video-use (MIT): reason over packed text, fetch pictures only at decision points.
"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

STOCK = re.compile(r'^(thank you\.?|thanks for watching\.?|subscribe\.?|you|bye\.?)$', re.I)


def ts(x):
    if ':' in x:
        m, s = x.split(':'); return int(m) * 60 + float(s)
    return float(x)


def mmss(t):
    m, s = divmod(t, 60); return f'{int(m):02d}:{s:04.1f}'


def main():
    a = sys.argv[1:]
    src, out = a[0], a[1]
    gap = float(a[a.index('--gap') + 1]) if '--gap' in a else 0.5
    t_from = ts(a[a.index('--from') + 1]) if '--from' in a else 0
    t_to = ts(a[a.index('--to') + 1]) if '--to' in a else 1e9
    T = json.load(open(src, encoding='utf-8'))
    lines, cur, last_end, prev_seg = [], None, None, None
    n_words = n_stretch = n_hallu = 0
    for seg in T['segments']:
        if seg['e'] < t_from or seg['s'] > t_to:
            continue
        hallu = seg.get('ns', 0) > 0.6 or bool(STOCK.match(seg['t'].strip())) or (prev_seg and seg['t'].strip() == prev_seg)
        prev_seg = seg['t'].strip()
        for i, w in enumerate(seg.get('words') or []):
            if not (t_from <= w['s'] <= t_to):
                continue
            txt = w['w'].strip()
            if not txt:
                continue
            n_words += 1
            if w['e'] - w['s'] > 1.0:
                txt += '~'; n_stretch += 1
            if w.get('p', 1) < 0.35:
                txt = f'(?{txt})'
            pause = (w['s'] - last_end) if last_end is not None else 0
            long_line = cur is not None and ((w['s'] - cur['s'] > 8 and pause >= .2) or w['s'] - cur['s'] > 15)
            if cur is None or pause >= gap or long_line:
                if cur:
                    lines.append(cur)
                cur = dict(s=w['s'], e=w['e'], words=[], pause=pause, hallu=False)
            cur['words'].append(txt); cur['e'] = w['e']
            if hallu and i == 0:
                cur['hallu'] = True; n_hallu += 1
            last_end = w['e']
    if cur:
        lines.append(cur)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(f'# Packed transcript - {src}\n')
        f.write(f'{len(lines)} phrases, {n_words} words, gap {gap}s. Marks: word~ stretched (>1 s, hidden pause/retake) x{n_stretch} | (?word) low confidence | {{HALLU?}} possible filler-over-silence x{n_hallu} | ...N.Ns pause before.\n')
        f.write('This is a map, not the words: Hinglish stretches may be silently translated - verify exact wording with lang_arbiter.py before captioning.\n\n')
        for L in lines:
            pre = f'...{L["pause"]:.1f}s ' if L['pause'] >= 1.5 else ''
            tag = '{HALLU?} ' if L['hallu'] else ''
            f.write(f'[{mmss(L["s"])}-{mmss(L["e"])}] {pre}{tag}{" ".join(L["words"])}\n')
    print(f'{out}: {len(lines)} phrases, {n_words} words, {n_stretch} stretched, {n_hallu} suspect segments')


if __name__ == '__main__':
    main()
