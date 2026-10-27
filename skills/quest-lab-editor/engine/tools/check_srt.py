"""Check (and optionally fix) SRT files against Netflix timed-text timing rules, adapted for Roman Hinglish.

usage: check_srt.py <video_duration_s> <file.srt ...> [--cuts video.cuts.txt] [--fps 30] [--fix]
  --cuts  cut times from qa_detect.py --strips, for shot-change timing
  --fix   writes <name>.fixed.srt: closes 3-14-frame gaps to 2 frames, snaps in/out times to nearby cuts, stretches too-short cues
Rules (references/review-qa.md §3):
  structure   numbering, overlaps, empty cues, cue after the video ends
  LINE-LENGTH > 42 chars · LINE-COUNT > 2 · one-liner split in two (FYI) · top line much longer than bottom (FYI, prefer bottom-heavy)
  LINE-BREAK  2nd line starting with a postposition / auxiliary (ne ko se mein pe par ka ki ke hai tha raha gaya diya ...)
  DURATION    < 5/6 s (25 frames) or > 7 s
  CPS         > 20 characters/s (Latin-script adult rate; Roman Hinglish is longer than Devanagari, so not Netflix's 22)
  GAP         gaps between cues are either 2 frames or >= 0.5 s - never 3-14 frames (flicker)
  SHOT        in-time 1-15 frames before a cut -> move onto the cut; out-time within 15 frames of a cut -> 2 frames before it
  REPEAT      the same word twice in a row (FYI: time to audio, write once, unless the repetition is the joke)
"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
STRAND = {'ne', 'ko', 'se', 'mein', 'me', 'pe', 'par', 'ka', 'ki', 'ke', 'hai', 'hain', 'tha', 'thi', 'the', 'raha', 'rahi', 'rahe',
          'gaya', 'gayi', 'gaye', 'diya', 'liya', 'karna', 'kiya', 'hoga', 'hogi', 'wala', 'wali', 'wale'}


def ts(x):
    h, m, r = x.split(':'); s, ms = r.split(','); return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def fmt(t):
    t = max(0, t); ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def main():
    a = sys.argv[1:]
    vdur = float(a[0])
    fps = float(a[a.index('--fps') + 1]) if '--fps' in a else 30.0
    cuts = [float(x) for x in open(a[a.index('--cuts') + 1]).read().split()] if '--cuts' in a else []
    fix = '--fix' in a
    files = [x for x in a[1:] if x.lower().endswith('.srt')]
    F = 1 / fps
    for p in files:
        blocks = [b for b in re.split(r'\r?\n\r?\n', open(p, encoding='utf-8-sig').read().strip()) if b.strip()]
        cues, probs = [], []
        for i, b in enumerate(blocks, 1):
            ln = b.splitlines()
            if ln[0].strip() != str(i): probs.append(('BLOCKER', i, 'numbering'))
            s, e = [ts(x.strip()) for x in ln[1].split('-->')]
            cues.append([s, e, ln[2:]])
        for i, (s, e, lines) in enumerate(cues, 1):
            text = ' '.join(lines); n = len(text); d = e - s
            if e <= s: probs.append(('BLOCKER', i, 'empty cue'))
            if e > vdur + .05: probs.append(('BLOCKER', i, 'ends after the video'))
            if i > 1 and s < cues[i - 2][1] - 1e-3: probs.append(('BLOCKER', i, 'overlaps the previous cue'))
            if any(len(t) > 42 for t in lines): probs.append(('ISSUE', i, f'LINE-LENGTH {max(len(t) for t in lines)} > 42'))
            if len(lines) > 2: probs.append(('ISSUE', i, f'LINE-COUNT {len(lines)}'))
            if len(lines) == 2:
                if n <= 42: probs.append(('FYI', i, 'LINE-COUNT fits on one line'))
                if len(lines[0]) > len(lines[1]) + 8: probs.append(('FYI', i, 'top-heavy (prefer a shorter top line)'))
                w2 = re.sub(r'[^\w]', ' ', lines[1].lower()).split()
                if w2 and w2[0] in STRAND: probs.append(('ISSUE', i, f'LINE-BREAK line 2 starts with "{w2[0]}" (keep it with its noun/verb)'))
                if len(lines[0].split()) <= 2 and len(lines[1]) > 25: probs.append(('FYI', i, 'LINE-BREAK 1-2 words alone on the top line'))
            if d < 25 / 30 - 1e-3: probs.append(('ISSUE', i, f'DURATION-SHORT {d:.2f}s < 0.83s'))
            if d > 7.0: probs.append(('ISSUE', i, f'DURATION-LONG {d:.2f}s > 7s'))
            if d > 0 and n / d > 20: probs.append(('ISSUE', i, f'CPS {n / d:.1f} > 20'))
            ws = re.sub(r'[^\w\s]', ' ', text.lower()).split()
            for x, y in zip(ws, ws[1:]):
                if x == y and len(x) > 1: probs.append(('FYI', i, f'REPEAT "{x} {x}"')); break
            if i < len(cues):
                g = cues[i][0] - e
                if 2.5 * F < g < .5 - 1e-3 and not any(e - F * .5 <= c <= cues[i][0] + F * .5 for c in cuts):   # a cut inside the gap: the shot rule wins
                    probs.append(('ISSUE', i, f'GAP {g * fps:.0f} frames to next cue (make it 2 frames or >= 0.5 s)'))
            for c in cuts:
                if F * .5 < c - s <= 15 * F: probs.append(('ISSUE', i, f'SHOT in-time {round((c - s) * fps)} frames before the cut at {c:.2f}s - start on the cut'))
                if abs(e - c) <= 15 * F and abs(e - (c - 2 * F)) > F * .6 and s < c - 2 * F: probs.append(('ISSUE', i, f'SHOT out-time {round((e - c) * fps):+d} frames from the cut at {c:.2f}s - end 2 frames before it'))
        rank = {'BLOCKER': 0, 'ISSUE': 1, 'FYI': 2}
        probs.sort(key=lambda x: (rank[x[0]], x[1]))
        cnt = {k: sum(1 for x in probs if x[0] == k) for k in rank}
        print(f"{p.split(chr(92))[-1]}: {len(cues)} cues, {sum(e - s for s, e, _ in cues):.0f}s captioned, last ends {cues[-1][1]:.2f}s - "
              f"{cnt['BLOCKER']} blocker, {cnt['ISSUE']} issue, {cnt['FYI']} fyi")
        for sev, i, msg in probs[:60]:
            print(f'  {sev:7s} cue {i:3d} {fmt(cues[i - 1][0])}  {msg}')
        if len(probs) > 60: print(f'  ... {len(probs) - 60} more')
        if fix:
            out = [list(c) for c in cues]
            for k, c in enumerate(out):
                s, e = c[0], c[1]
                nxt = out[k + 1][0] if k + 1 < len(out) else vdur
                for cut in cuts:
                    if F * .5 < cut - s <= 15 * F and (k == 0 or out[k - 1][1] <= cut - 2 * F): s = cut
                    # snap the out-time to 2 frames before a nearby cut - unless that leaves the cue too short to read
                    if abs(e - cut) <= 15 * F and s < cut - 15 * F and (cut - 2 * F) - s >= 25 / 30: e = cut - 2 * F
                if e - s < 25 / 30: e = min(s + 25 / 30, nxt - 2 * F)
                g = nxt - e
                # close a flicker gap only when no cut lies inside it (shot changes win over the gap rule)
                if 2.5 * F < g < .5 and not any(e - F * .5 <= cut <= nxt + F * .5 for cut in cuts): e = nxt - 2 * F
                c[0], c[1] = s, e
            fp = re.sub(r'\.srt$', '.fixed.srt', p, flags=re.I)
            with open(fp, 'w', encoding='utf-8') as fh:
                for k, (s, e, lines) in enumerate(out, 1):
                    fh.write(f'{k}\n{fmt(s)} --> {fmt(e)}\n' + '\n'.join(lines) + '\n\n')
            print(f'  fixed -> {fp} (re-run the check on it; line breaks and CPS are not auto-fixed)')


if __name__ == '__main__':
    main()
