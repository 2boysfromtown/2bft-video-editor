"""Energy map of a talking-head recording -> per-frame energy curve + shake events.

Signals (all per output frame at --fps):
  loud   short-term voice loudness (dB) vs a rolling 30 s baseline   (shouting, emphasis)
  pitch  F0 vs a rolling baseline (semitones)                      (excitement raises pitch)
  flux   spectral flux / onset strength                            (bursts, laughs, claps)
  move   webcam motion: mean abs frame difference in the cam crop   (gestures, leaning in)
  words  exclamation words from the transcript (let's go, oh my god, wow, bhai, yes ...)
energy = weighted sum of robust z-scores, smoothed; events = peaks above thresholds -> tiers rumble/shake/impact.

usage: python energy.py <video> <wav16k> <transcript.json> <out.json> [--cam x,y,w,h] [--fps 30]
"""
import argparse, json, subprocess, sys
import numpy as np, soundfile as sf, librosa
from scipy.ndimage import uniform_filter1d, median_filter, maximum_filter1d
from scipy.signal import find_peaks

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('wav'); ap.add_argument('words'); ap.add_argument('out')
ap.add_argument('--cam', default='1474,156,388,765'); ap.add_argument('--fps', type=float, default=30.0)
A = ap.parse_args()
FPS = A.fps

# ---------- audio ----------
y, sr = sf.read(A.wav, dtype='float32'); assert sr == 16000
hop = int(round(sr / FPS * 1))           # one hop per output frame (533 at 30 fps)
n_fr = int(len(y) / hop)
rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=hop, center=True)[0][:n_fr]
loud = 20 * np.log10(rms + 1e-6)
print('rms done', n_fr, file=sys.stderr)
# pitch with yin on voiced range, hop matched
f0 = librosa.yin(y, fmin=70, fmax=400, sr=sr, frame_length=1024, hop_length=hop)[:n_fr]
voiced = loud > np.percentile(loud, 45)
semi = 12 * np.log2(np.maximum(f0, 1) / 100.0)
semi[~voiced] = np.nan
print('pitch done', file=sys.stderr)
S = np.abs(librosa.stft(y, n_fft=1024, hop_length=hop))[:, :n_fr]
flux = np.r_[0, np.sqrt((np.maximum(np.diff(np.log1p(S), axis=1), 0) ** 2).sum(0))]
del S

def rolling_z(x, win_s=30, floor=1.0):
    """robust z vs a rolling median; NaN frames (unvoiced) are excluded from the baseline and get z=0"""
    x = np.asarray(x, float); ok = ~np.isnan(x)
    if ok.sum() < 10: return np.zeros_like(x)
    idx = np.flatnonzero(ok); v = x[ok]
    w = max(5, int(win_s * FPS * ok.mean()))
    med_v = median_filter(v, size=w, mode='nearest')
    mad_v = median_filter(np.abs(v - med_v), size=w, mode='nearest') * 1.4826
    med = np.interp(np.arange(len(x)), idx, med_v); mad = np.maximum(np.interp(np.arange(len(x)), idx, mad_v), floor)
    z = (np.where(ok, x, med) - med) / mad
    z[~ok] = 0
    return np.clip(z, -4, 6)

z_loud = rolling_z(loud, floor=2.0)        # dB
z_pitch = rolling_z(semi, floor=1.0)       # semitones
z_flux = rolling_z(flux, floor=float(np.median(flux)) * .25 + 1e-6)

# ---------- webcam motion ----------
cx, cy, cw, ch = map(int, A.cam.split(','))
W2, H2 = 64, 126
cmd = ['ffmpeg', '-v', 'error', '-i', A.video, '-vf', f'fps={FPS},crop={cw}:{ch}:{cx}:{cy},scale={W2}:{H2},format=gray', '-f', 'rawvideo', '-']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 7)
fs = W2 * H2; prev = None; mv = []
while True:
    b = p.stdout.read(fs * 300)
    if not b: break
    arr = np.frombuffer(b, np.uint8)[: (len(b) // fs) * fs].reshape(-1, H2, W2).astype(np.float32)
    for f in arr:
        f = f - f.mean()                    # drop global brightness / light-colour changes
        mv.append(0.0 if prev is None else float(np.abs(f - prev).mean())); prev = f
p.wait()
move = np.array(mv)
print('motion done', len(move), file=sys.stderr)
n = min(n_fr, len(move))
z_loud, z_pitch, z_flux, move, loud = z_loud[:n], z_pitch[:n], z_flux[:n], move[:n], loud[:n]
z_move = rolling_z(uniform_filter1d(move, 5), floor=float(np.median(move)) * .3 + 1e-3)
z_move = np.minimum(z_move, 4.0)           # leaving the chair is not energy

# ---------- exclamation words ----------
EXC = {
    3.0: ["let's go", 'lets go', 'oh my god', 'omg', 'wow', 'crazy', 'insane', 'boom', 'yes yes', 'beautiful',
          'लेट्स गो', 'लेस्गो', 'लेट्स', 'ओ माय गॉड', 'माय गॉड', 'वाओ', 'ब्यूटिफुल', 'बढ़िया', 'क्रेज़ी'],
    1.5: ['bhai', 'yaar', 'yes', 'wait', 'what', 'kya', 'dekho', 'see', 'oh', 'arre', 'haha',
          'भाई', 'यार', 'देखो', 'अरे', 'वाह', 'हाहा'],
}
word_sig = np.zeros(n)
W = json.load(open(A.words, encoding='utf-8'))
for seg in W['segments']:
    t = seg['t'].lower()
    ws = seg.get('words') or []
    for wgt, keys in EXC.items():
        for k in keys:
            if k in t:
                # put the bump on the word that starts the phrase, else the segment start
                at = seg['s']
                for w in ws:
                    if k.split()[0] in w['w'].lower(): at = w['s']; break
                i = int(at * FPS)
                if 0 <= i < n: word_sig[i] = max(word_sig[i], wgt)
word_sig = uniform_filter1d(maximum_filter1d(word_sig, int(.6 * FPS)), int(.3 * FPS)) * 1.0

# ---------- combine ----------
speech = (loud > np.percentile(loud, 35)).astype(float)
speech = maximum_filter1d(speech, int(.5 * FPS))
energy = (0.38 * np.clip(z_loud, -2, 6) + 0.22 * np.clip(z_pitch, -2, 6) + 0.12 * np.clip(z_flux, -2, 6)
          + 0.20 * np.clip(z_move, -2, 6)) * speech + 0.35 * word_sig
energy = uniform_filter1d(energy, int(.25 * FPS))
# normalise: 0 = calm talking, 1 = clearly energetic, 2+ = peak
lo, hi = np.percentile(energy, 50), np.percentile(energy, 97)
e01 = np.clip((energy - lo) / (hi - lo + 1e-6), 0, 3)

# ---------- events ----------
events = []
pk, pr = find_peaks(e01, height=0.85, distance=int(1.2 * FPS), prominence=0.35)
for i, h in zip(pk, pr['peak_heights']):
    tier = 'impact' if h >= 1.9 else 'shake' if h >= 1.2 else 'rumble'
    # attack starts where energy first crossed 60% of the peak before it
    j = i
    while j > 0 and e01[j] > 0.6 * h and i - j < 1.5 * FPS: j -= 1
    k = i
    while k < n - 1 and e01[k] > 0.6 * h and k - i < 3 * FPS: k += 1
    events.append(dict(t=round(i / FPS, 3), t0=round(j / FPS, 3), t1=round(k / FPS, 3), peak=round(float(h), 2), tier=tier,
                       loud=round(float(z_loud[i]), 2), pitch=round(float(z_pitch[i]), 2), move=round(float(z_move[i]), 2), word=round(float(word_sig[i]), 2)))

out = dict(fps=FPS, n=int(n), energy=[round(float(v), 3) for v in e01], events=events,
           note='energy: 0 calm, 1 energetic, 2+ peak (relative to this recording)')
json.dump(out, open(A.out, 'w'))
tiers = {t: sum(1 for e in events if e['tier'] == t) for t in ('rumble', 'shake', 'impact')}
print(f'frames {n}, events {len(events)} {tiers}, share >1: {np.mean(e01 > 1) * 100:.1f}%', file=sys.stderr)
