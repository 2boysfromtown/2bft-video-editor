"""Find pauses to tighten, unworded voice (fillers, breaths, laughs), stretched words and retakes in a source range,
and propose keep-ranges you can paste into a plan as shots.  Rules: references/cutting.md.

usage: pauses.py <audio.wav> <transcript.json> <from mm:ss> <to mm:ss> [--mode aggressive|balanced|gentle] [--min-save 0.2] [--json out.json]

- Silence threshold comes from the footage: noise floor F = 10th pct of 0.5 s RMS, speech S = 90th pct, threshold F + 6 dB.
  If S - F < 8 dB the audio can't separate speech from silence (music under voice) and cuts fall back to word timings.
- Real gap edges come from energy, not Whisper (Whisper word edges run ~100-300 ms early and swallow pauses).
- Gap table (gap -> length kept):   < .25 s | .25-1 s | 1-3 s | > 3 s
    aggressive (Shorts)               keep  |  0.10   |  0.20 | 0.20
    balanced   (long-form)            keep  |  0.30   |  0.80 | 0.50
    gentle     (emotional/moral)      keep  |  0.50   |  1.50 | 1.00
  Of the kept gap, at most 0.10 s goes before the next word, the rest after the last word (voices decay; onsets are sharp).
- A cut is a visible jump: it is skipped unless it saves >= --min-save (0.2 s aggressive, 0.3 s otherwise), and no kept piece may be < 0.4 s.
- Never auto-cut: unworded voice inside a gap (could be a laugh or a beat), stretched words, retakes. They are listed for you to decide.
Ideas from louisedesadeleer/cut-video (MIT) and WyattBlue/auto-editor (Unlicense), re-derived for this engine.
"""
import json, re, sys
import numpy as np
import soundfile as sf
sys.stdout.reconfigure(encoding='utf-8')

TABLE = {'aggressive': (.10, .20, .20), 'balanced': (.30, .80, .50), 'gentle': (.50, 1.50, 1.00)}


def ts(x):
    if ':' in x:
        m, s = x.split(':'); return int(m) * 60 + float(s)
    return float(x)


def norm(w):
    return re.sub(r"[^\w']+", '', w.lower())


def main():
    a = sys.argv[1:]
    wav, tjson, t0, t1 = a[0], a[1], ts(a[2]), ts(a[3])
    mode = a[a.index('--mode') + 1] if '--mode' in a else 'aggressive'
    # a cut is a visible jump: skip it unless it saves at least this much, and never leave a kept sliver shorter than MIN_KEEP
    min_save = float(a[a.index('--min-save') + 1]) if '--min-save' in a else (.20 if mode == 'aggressive' else .30)
    MIN_KEEP = .40
    jout = a[a.index('--json') + 1] if '--json' in a else None
    with sf.SoundFile(wav) as f:
        sr = f.samplerate
        f.seek(int(max(0, t0 - .5) * sr)); x = f.read(int((t1 - t0 + 1.0) * sr), dtype='float32', always_2d=True).mean(1)
    base = max(0, t0 - .5)
    hop = int(.01 * sr); win = int(.03 * sr)
    n = max(1, (len(x) - win) // hop)
    rms = np.array([np.sqrt(np.mean(x[i * hop:i * hop + win] ** 2) + 1e-12) for i in range(n)])
    db = 20 * np.log10(rms + 1e-9)
    w50 = 50
    blocks = np.array([20 * np.log10(np.sqrt(np.mean(rms[i:i + w50] ** 2)) + 1e-9) for i in range(0, max(1, n - w50), 10)])
    live = blocks[blocks > -65]  # ignore digital silence (muted mic, scene with no audio) or the floor collapses
    F, S = float(np.percentile(live if len(live) > 20 else blocks, 10)), float(np.percentile(blocks, 90))
    thr = F + 6
    energy_ok = (S - F) >= 8
    tt = base + np.arange(n) * .01 + .015
    loud = db > thr
    # ignore loud blips < 80 ms (mouse clicks, lip smacks, breaths in a stare) - auto-editor's --smooth idea
    i = 0
    while i < len(loud):
        if loud[i]:
            j = i
            while j < len(loud) and loud[j]:
                j += 1
            if j - i < 8:
                loud[i:j] = False
            i = j
        else:
            i += 1

    def silent_run(g0, g1):
        """Longest below-threshold run inside [g0, g1] (seconds), from energy."""
        i0, i1 = np.searchsorted(tt, g0), np.searchsorted(tt, g1)
        best, cur_s, best_span = 0, None, None
        for i in range(i0, i1):
            if not loud[i]:
                cur_s = i if cur_s is None else cur_s
                if (i - cur_s + 1) > best:
                    best, best_span = i - cur_s + 1, (tt[cur_s] - .005, tt[i] + .005)
            else:
                cur_s = None
        return best_span

    words = []
    T = json.load(open(tjson, encoding='utf-8'))
    for seg in T['segments']:
        for w in seg.get('words') or []:
            if t0 <= w['s'] <= t1 and w['w'].strip():
                words.append(dict(w=w['w'].strip(), s=w['s'], e=w['e'], p=w.get('p', 1)))
    if not words:
        print('no words in range'); return
    k1, k2, k3 = TABLE[mode]  # kept length for gaps of .25-1 s, 1-3 s, > 3 s
    cuts, unworded, stretched = [], [], []
    for w in words:
        if w['e'] - w['s'] > 1.0:
            stretched.append(w)
    for a_, b_ in zip(words, words[1:]):
        g = b_['s'] - a_['e']
        # widen the search: Whisper ends early and starts early
        span = silent_run(a_['e'] - .15, b_['s'] + .10) if energy_ok else (a_['e'], b_['s'])
        if span is None:
            continue
        s0, s1 = span
        real = s1 - s0
        if energy_ok and g > .15:
            # voice inside the Whisper gap that is not a word: filler / breath / laugh / unheard word
            i0, i1 = np.searchsorted(tt, a_['e'] + .05), np.searchsorted(tt, b_['s'] - .05)
            if i1 > i0:
                seg = loud[i0:i1]
                voiced = seg.sum() * .01
                if voiced >= .15:
                    peak = db[i0:i1].max()
                    kind = ('long + loud: laugh / reaction? protect' if voiced > .6 and peak > S else
                            'long: aside or unheard words? listen' if voiced > .6 else
                            'short: filler / breath?')
                    unworded.append(dict(s=round(a_['e'], 2), e=round(b_['s'], 2), voiced=round(voiced, 2), kind=kind,
                                         after=a_['w'], before=b_['w']))
        if real < .25:
            continue
        keep = k1 if real <= 1 else (k2 if real <= 3 else k3)
        if keep >= real - .02:
            continue
        head = min(.10, keep * .4); tail = keep - head
        if real - keep < min_save:
            continue
        if cuts and (s0 + tail) - cuts[-1]['cut_to'] < MIN_KEEP:
            continue
        cuts.append(dict(cut_from=round(s0 + tail, 3), cut_to=round(s1 - head, 3), gap=round(real, 2), keep=keep,
                         after=a_['w'], before=b_['w']))
    # silences hidden INSIDE stretched words (Whisper glued a pause onto a word) - found 27 Oct on S02: a 4.4 s stare inside "same"
    if energy_ok:
        for w in stretched:
            span = silent_run(w['s'], w['e'])
            if span is None or span[1] - span[0] < 1.0:
                continue
            s0, s1 = span; real = s1 - s0
            keep = k1 if real <= 1 else (k2 if real <= 3 else k3)
            head = min(.10, keep * .4); tail = keep - head
            if real - keep >= min_save:
                cuts.append(dict(cut_from=round(s0 + tail, 3), cut_to=round(s1 - head, 3), gap=round(real, 2), keep=keep,
                                 after=f"(inside stretched '{w['w']}')", before='- verify with timeline_view'))
        cuts.sort(key=lambda c: c['cut_from'])
        merged = []
        for c in cuts:  # drop overlaps and slivers created by the extra cuts
            if merged and (c['cut_from'] < merged[-1]['cut_to'] + MIN_KEEP):
                if c['gap'] > merged[-1]['gap']: merged[-1] = c
                continue
            merged.append(c)
        cuts = merged
    # retakes: phrases split at >= .5 s pauses, compare openings
    phrases, cur = [], [words[0]]
    for a_, b_ in zip(words, words[1:]):
        if b_['s'] - a_['e'] >= .5:
            phrases.append(cur); cur = []
        cur.append(b_)
    phrases.append(cur)

    def grams(p, k=3):
        t = [norm(w['w']) for w in p[:8]]
        return {tuple(t[i:i + k]) for i in range(max(0, len(t) - k + 1))}
    retakes = []
    for i, p in enumerate(phrases):
        gi, oi = grams(p), [norm(w['w']) for w in p[:3]]
        for q in phrases[i + 1:]:
            if q[0]['s'] - p[0]['s'] > 60:
                break
            gq, oq = grams(q), [norm(w['w']) for w in q[:3]]
            jac = len(gi & gq) / max(1, len(gi | gq))
            if (len(oi) == 3 and oi == oq) or jac > .7:
                kind = 'false start' if q[0]['s'] - p[-1]['e'] < 3 else 'retake'
                retakes.append(dict(kind=kind, first=(round(p[0]['s'], 2), round(p[-1]['e'], 2), ' '.join(w['w'] for w in p[:8])),
                                    later=(round(q[0]['s'], 2), round(q[-1]['e'], 2), ' '.join(w['w'] for w in q[:8]))))
                break
    # keep ranges
    start = words[0]['s'] - .05; end = words[-1]['e'] + .20
    keeps, s = [], start
    for c in cuts:
        if c['cut_from'] > s:
            keeps.append([round(s, 2), round(c['cut_from'], 2)])
        s = c['cut_to']
    keeps.append([round(s, 2), round(end, 2)])
    lens = [b - a for a, b in keeps]
    kept = sum(lens); total = end - start
    med = float(np.median(lens)) if lens else 0
    print(f'range {t0:.2f}-{t1:.2f}  mode {mode}  floor {F:.1f} dB  speech {S:.1f} dB  threshold {thr:.1f} dB' +
          ('' if energy_ok else '  !! S-F < 8 dB: energy cannot separate speech (music/noise under voice) - gaps from word timings only'))
    print(f'pauses tightened: {len(cuts)}  kept {kept:.1f}s of {total:.1f}s (-{max(0, 100 * (1 - kept / total)):.0f}%)  segments {len(keeps)}  median {med:.2f}s' +
          ('  !! over-cut (median < 0.7 s): merge or switch to balanced' if med < .7 and len(keeps) > 3 else '') +
          ('  (median > 2 s: fine for long-form, loose for a Short)' if med > 2 and mode == 'aggressive' else ''))
    for c in cuts:
        print(f"  cut {c['cut_from']:.2f}-{c['cut_to']:.2f}  gap {c['gap']:.2f}s -> {c['keep']:.2f}s   …{c['after']} | {c['before']}…")
    if unworded:
        print('UNWORDED VOICE in gaps (not cut - listen, then decide; laughs and beats stay):')
        for u in unworded:
            print(f"  {u['s']:.2f}-{u['e']:.2f}  {u['voiced']:.2f}s voiced  {u['kind']}   after '{u['after']}' before '{u['before']}'")
    if stretched:
        print('STRETCHED WORDS (> 1 s - hidden pause/retake; never cut on their edges):')
        for w in stretched:
            print(f"  {w['s']:.2f}-{w['e']:.2f}  '{w['w']}'  {w['e'] - w['s']:.2f}s")
    if retakes:
        print('RETAKE CANDIDATES (default: keep the later take unless it is flubbed):')
        for r in retakes:
            print(f"  {r['kind']}: {r['first'][0]:.2f}-{r['first'][1]:.2f} \"{r['first'][2]}\"  ->  {r['later'][0]:.2f}-{r['later'][1]:.2f} \"{r['later'][2]}\"")
    print('PLAN SHOTS:')
    for k in keeps:
        print(f"  {{'in': {k[0]:.2f}, 'out': {k[1]:.2f}}},")
    if jout:
        json.dump(dict(range=[t0, t1], mode=mode, floor=F, speech=S, threshold=thr, energy_ok=bool(energy_ok), cuts=cuts, keeps=keeps,
                       unworded=unworded, stretched=stretched, retakes=retakes), open(jout, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
