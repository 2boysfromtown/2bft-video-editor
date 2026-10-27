"""edits/<name>.audio.json -> audio/<name>_mix.wav  (48 kHz stereo; loudness set to -14 LUFS at mux)

Buses
  voice   stream voice cut per shot (12 ms fades), high-pass 80 Hz, gentle presence lift, slow leveller + light compression
  media   original audio of inserted outputs (Leela episodes, reels) when a shot asks for it
  fx      echo throws (delay taps, darker each repeat, ping-pong) and reverb throws (synthetic hall) on chosen words / lines
  sfx     the cue list (sfx.py kit or sfx_lib/ samples), gains in dB relative to the voice's speaking level
  music   track cues (files in music/) or the synth bed, ducked under speech, cut dead on 'stop'
usage: python mix.py <name>
"""
import json, os, sys
import numpy as np, soundfile as sf
from scipy.ndimage import uniform_filter1d, maximum_filter1d
from scipy.signal import butter, sosfilt, fftconvolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx as K
import score as S

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(ROOT, 'source.json')))
SR = 48000
UNDER_VOICE_DB, GAP_DB = -20.0, -10.0
def db(x): return 10 ** (x / 20)
def sos(kind, f, o=2): return butter(o, f, kind, fs=SR, output='sos')

def fade(seg, n=576):
    n = min(n, len(seg) // 2)
    if n > 0: r = np.linspace(0, 1, n, dtype=np.float32)[:, None]; seg[:n] *= r; seg[-n:] *= r[::-1]
    return seg

def level_voice(v):
    mono = v.mean(1); e = np.sqrt(uniform_filter1d(mono ** 2, int(.4 * SR)) + 1e-12)
    act = e[e > np.percentile(e, 60)]; target = np.median(act) if len(act) else .05
    g = np.clip(target / e, db(-6), db(8)); g[e < target * db(-24)] = 1.0
    g = uniform_filter1d(g, int(.25 * SR)); v = v * g[:, None]
    pk = maximum_filter1d(np.abs(v).max(1), int(.01 * SR)); pk = uniform_filter1d(pk, int(.02 * SR))
    thr = np.percentile(pk[pk > 1e-4], 88) if (pk > 1e-4).any() else .3
    cg = np.where(pk > thr, (thr + (pk - thr) / 3.5) / np.maximum(pk, 1e-9), 1.0)
    return v * cg[:, None]

def eq_voice(v):
    v = sosfilt(sos('high', 80, 2), v, axis=0)
    pres = sosfilt(sos('band', [2500, 5500], 2), v, axis=0)       # +~3 dB presence
    low = sosfilt(sos('low', 220, 2), v, axis=0)                   # slight warmth
    return v + .35 * pres + .12 * low

def echo_throw(src, a, b, delay=.3, fb=.45, taps=4, wet=.75):
    """repeats of src[a:b] at delay*k, each darker and quieter, ping-pong"""
    seg = src[a:b].mean(1)
    seg = fade(seg[:, None].copy(), 240)[:, 0]
    out = np.zeros((len(seg) + int(delay * SR * (taps + 1)), 2), np.float32)
    for k in range(1, taps + 1):
        x = sosfilt(sos('low', max(1200, 6000 / k), 2), sosfilt(sos('high', 250 + 80 * k, 2), seg))
        s = int(delay * SR * k); g = wet * fb ** (k - 1)
        pan = -.6 if k % 2 else .6
        out[s:s + len(x), 0] += x * g * np.cos((pan + 1) * np.pi / 4) * 1.414
        out[s:s + len(x), 1] += x * g * np.sin((pan + 1) * np.pi / 4) * 1.414
    return out

_IR = None
def hall_ir(decay=2.2):
    global _IR
    if _IR is None:
        n = int(decay * SR); tt = np.arange(n) / SR; rngs = np.random.default_rng(11)
        ir = np.stack([rngs.standard_normal(n), rngs.standard_normal(n)], 1) * np.exp(-tt / (decay / 6.9))[:, None]
        ir = sosfilt(sos('low', 5000, 2), ir, axis=0); ir[:int(.02 * SR)] = 0
        _IR = (ir / np.sqrt((ir ** 2).sum(0))).astype(np.float32)
    return _IR

def load_track(path):
    x, sr = sf.read(path, dtype='float32', always_2d=True)
    if x.shape[1] == 1: x = np.repeat(x, 2, 1)
    if sr != SR:
        import librosa
        x = np.stack([librosa.resample(x[:, c], orig_sr=sr, target_sr=SR) for c in range(2)], 1)
    return x

def main(name, clean=False):
    A = json.load(open(os.path.join(ROOT, 'edits', name + '.audio.json')))
    if clean: A['music_gain'] = 0.0
    dur = A['dur']; N = int(round(dur * SR)) + SR // 10
    srcf = sf.SoundFile(CFG['audio48k']); assert srcf.samplerate == SR   # read only the segments we use (the full file is 1+ GB as float32)
    def src_seg(i0, n):
        srcf.seek(max(0, i0)); x = srcf.read(n, dtype='float32', always_2d=True)
        return x if x.shape[1] == 2 else np.repeat(x, 2, 1)
    voice = np.zeros((N, 2), np.float32); media = np.zeros((N, 2), np.float32); mcache = {}
    for s in A['shots']:
        a, b = int(round(s['t0'] * SR)), int(round(s['t1'] * SR)); n = b - a
        if n <= 0: continue
        if s.get('media'):   # an inserted output plays with its own audio
            key = s['media'].split(':', 1)[1]; wav = A['clips'].get(key)
            if wav:
                if wav not in mcache: mcache[wav] = load_track(wav)
                i0 = int(round(s.get('clip0', 0) * SR)); seg = mcache[wav][i0:i0 + n].copy()
                if len(seg) < n: seg = np.pad(seg, ((0, n - len(seg)), (0, 0)))
                media[a:b] += fade(seg) * s.get('mvol', 1.0)
        if s['freeze'] or s.get('mute'): continue
        sp = s['speed']
        if sp == 1:
            i0 = int(round(s['src0'] * SR)); seg = src_seg(i0, n)
        else: continue   # sped-up stretches carry sfx / music, not chipmunk voice
        if len(seg) < n: seg = np.pad(seg, ((0, n - len(seg)), (0, 0)))
        voice[a:b] += fade(seg) * s.get('vol', 1.0)
    voice = level_voice(eq_voice(voice))
    bleeps = []
    for e in A.get('fx', []):   # telephone colour and bleeps rewrite the voice itself
        a, b = int(round(e['t0'] * SR)), int(round(e['t1'] * SR))
        if b <= a: continue
        if e['kind'] == 'tel':
            seg = voice[a:b]
            for _ in range(2): seg = sosfilt(sos('high', 300, 2), seg, axis=0); seg = sosfilt(sos('low', 3400, 2), seg, axis=0)
            seg = seg + .5 * sosfilt(sos('band', [1100, 1900], 2), seg, axis=0)
            seg = np.round(seg * 512) / 512
            voice[a:b] = fade(seg * 1.6, 240)
        elif e['kind'] == 'bleep':
            voice[a:b] *= 0; bleeps.append((e['t0'], e['t1'] - e['t0']))
        elif e['kind'] == 'mute':
            n = min(480, (b - a) // 2); voice[a:a + n] *= np.linspace(1, 0, n)[:, None]; voice[a + n:b] *= 0
    ve = np.sqrt(uniform_filter1d(voice.mean(1) ** 2, int(.12 * SR)) + 1e-12)
    vact = np.median(ve[ve > np.percentile(ve, 55)]) if (ve > 0).any() else .05
    # fx: echo / reverb throws (taken from the processed voice so they match)
    fxb = np.zeros((N + SR * 3, 2), np.float32)
    for e in A.get('fx', []):
        a, b = int(round(e['t0'] * SR)), int(round(e['t1'] * SR))
        if b <= a: continue
        if e['kind'] == 'echo':
            x = echo_throw(voice, a, b, e.get('delay', .3), e.get('fb', .45), e.get('taps', 4), e.get('wet', .75))
            fxb[a:a + len(x)] += x[:len(fxb) - a]
        else:
            seg = voice[a:b].copy(); wet = fftconvolve(seg, hall_ir(), axes=0)[:len(seg) + SR * 2] * e.get('wet', .35) * 3
            fxb[a:a + len(wet)] += wet[:len(fxb) - a].astype(np.float32)
    fxb = fxb[:N]
    # speaking envelope for ducking
    speaking = (ve > vact * db(-14)).astype(np.float32); speaking = maximum_filter1d(speaking, int(.35 * SR))
    if np.abs(media).max() > 0:
        me = np.sqrt(uniform_filter1d(media.mean(1) ** 2, int(.12 * SR)) + 1e-12)
        act = me[me > 1e-4]                                   # only where the clip actually plays (it may be < 10 % of the film)
        mr = np.median(act[act >= np.percentile(act, 50)]) if len(act) else 1.0
        media *= min(8.0, (vact * 1.05) / max(mr, 1e-4))     # match the voice level, never more than +18 dB
        speaking = np.maximum(speaking, (me > mr * db(-18)).astype(np.float32))
    sm = uniform_filter1d(speaking, int(.18 * SR))
    # music: cues are either a file track (dict(file=..., at=offset_s, gain=dB)) or a synth state
    mus = np.zeros((N, 2), np.float32); synth_secs = []
    cues = A['music']
    for i, m in enumerate(cues):
        t0 = m['t']; t1 = cues[i + 1]['t'] if i + 1 < len(cues) else dur + 1
        a, b = int(t0 * SR), min(N, int(t1 * SR))
        if m.get('file'):
            x = load_track(m['file']); off = int(m.get('at', 0) * SR); seg = x[off:off + (b - a)]
            if len(seg) < b - a:   # loop the track if the section is longer
                reps = int(np.ceil((b - a) / max(1, len(x) - off))) + 1; seg = np.concatenate([x[off:]] * reps)[:b - a]
            seg = seg.copy(); fl = int(m.get('fade_in', .02) * SR); seg[:fl] *= np.linspace(0, 1, fl)[:, None]
            fo = int(m.get('fade_out', .04) * SR); seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
            mus[a:b] += seg * db(m.get('gain', 0))
        elif m['state'] not in ('stop',):
            synth_secs.append(dict(t0=t0, t1=t1, state=m['state']))
    if synth_secs:
        sy = S.build(dur + .1, synth_secs)[:N]; sy = np.pad(sy, ((0, max(0, N - len(sy))), (0, 0)))
        mus += sy
    for m in cues:   # tape stop: the music brakes to a halt in the 0.35 s before a 'stop' cue marked tape=True
        if m.get('tape'):
            T = int(m['t'] * SR); L = int(m.get('tape_len', .35) * SR); a = max(0, T - L)
            src_seg = mus[a:T + L].copy(); rr_ = (1 - np.arange(T - a) / max(1, T - a)) ** 2; pos = np.cumsum(rr_)
            pos = np.clip(pos, 0, len(src_seg) - 1).astype(int); mus[a:T] = src_seg[pos] * np.linspace(1, .3, T - a)[:, None]
    m_rms = np.sqrt(np.mean(mus[np.abs(mus).max(1) > 1e-4] ** 2)) if (np.abs(mus) > 1e-4).any() else 1
    base = vact / max(m_rms, 1e-6) * A.get('music_gain', 1.0)
    duck = db(GAP_DB) * (1 - sm) + db(UNDER_VOICE_DB) * sm
    for s in A['shots']:
        if s.get('duck') is not None:
            a, b = int(s['t0'] * SR), int(s['t1'] * SR); duck[a:b] = np.minimum(duck[a:b], db(s['duck']))
    music = mus * (base * duck)[:, None]
    # per-cue check: music is normalised across ALL cues, so one loud drop can bury a gentle bed (found 27 Oct on S02: 32 dB under).
    # Report each file cue's level under the voice while he talks; target 18-24 dB (captions-sfx-voicefx.md §2). Fix with the cue's gain.
    if not clean:
        for i, m in enumerate(cues):
            if not m.get('file'): continue
            a = int(m['t'] * SR); b = min(N, int((cues[i + 1]['t'] if i + 1 < len(cues) else dur) * SR))
            talk = (sm[a:b] > .5) & (np.abs(voice[a:b]).max(1) > 1e-3)   # his voice only (not clip audio / muted shots)
            if talk.sum() < SR * .5: continue
            v_r = np.sqrt(np.mean(voice[a:b][talk] ** 2)) + 1e-9; m_r = np.sqrt(np.mean(music[a:b][talk] ** 2)) + 1e-9
            under = 20 * np.log10(v_r / m_r)
            flag = '' if 17 <= under <= 25 else ('  <- too quiet: raise this cue\'s gain by ~%.0f dB' % (under - 21) if under > 25 else '  <- too loud under speech: lower gain by ~%.0f dB' % (21 - under))
            print(f"music cue {os.path.basename(m['file'])} @ {m['t']:.2f}s: {under:.1f} dB under the voice while he talks{flag}")
    # sfx
    fol = np.zeros((N + SR * 3, 2), np.float32)
    for e in A['sfx']:
        try: x = K.get(e['name'], e.get('dur'))
        except KeyError: print('unknown sfx', e['name']); continue
        at = e['t'] - (len(x) / SR * .55 if e['name'] in ('whoosh', 'whoosh_s') else 0) - (len(x) / SR if e['name'] == 'riser' else 0)
        S.add(fol, x.astype(np.float32), max(0, at), vact * 2.2 * db(e.get('gain', -12)), pan=e.get('pan', 0))
    for t0, d in bleeps:
        tt = np.arange(int(d * SR)) / SR; x = np.sin(2 * np.pi * 1000 * tt) * .25 * np.minimum(1, np.minimum(tt, d - tt) / .005)
        S.add(fol, x.astype(np.float32), t0, vact * 2.2)
    fol = fol[:N]
    buses = dict(voice=voice, media=media, fx=fxb, music=music, sfx=fol)
    bad = {k: float(np.abs(np.nan_to_num(v, nan=9e9)).max()) for k, v in buses.items()}
    if max(bad.values()) > 4:   # a bus exploded (NaN or runaway gain) -> say where instead of silently scaling the whole film down
        for k, v in buses.items():
            if bad[k] > 4:
                i = int(np.argmax(np.abs(np.nan_to_num(v, nan=9e9)).max(1))); print(f'WARNING bus {k} peak {bad[k]:.1f} at {i / SR:.2f}s — clipped to ±1')
                np.clip(np.nan_to_num(v, nan=0.0), -1, 1, out=v)
    mix = voice + media + fxb + music + fol
    mix[:int(.025 * SR)] *= np.linspace(0, 1, int(.025 * SR))[:, None]
    tail = int(.25 * SR); mix[-tail:] *= np.linspace(1, 0, tail)[:, None]
    pk = np.abs(mix).max()
    if pk > .98: mix *= .98 / pk
    mix = mix[:int(round(dur * SR))]
    os.makedirs(os.path.join(ROOT, 'audio'), exist_ok=True)
    out = os.path.join(ROOT, 'audio', name + ('_mix_clean.wav' if clean else '_mix.wav')); sf.write(out, mix, SR, subtype='PCM_24')
    print(f'{out}: {dur:.2f}s, peak {pk:.2f}, voice act {20 * np.log10(vact):.1f} dBFS, {len(A["sfx"])} sfx, {len(A.get("fx", []))} voice fx')

if __name__ == '__main__':
    main(sys.argv[1], clean='--clean' in sys.argv)
