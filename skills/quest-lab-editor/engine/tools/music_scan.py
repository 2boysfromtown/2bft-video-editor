"""Scan music tracks: convert to 48 kHz wav, report duration, BPM, first downbeat, and drop candidates (biggest loudness jumps).
usage: music_scan.py <music_dir> <out_json>"""
import json, os, sys, subprocess
import numpy as np, librosa
from scipy.ndimage import uniform_filter1d
sys.stdout.reconfigure(encoding='utf-8')
root, out = sys.argv[1], sys.argv[2]
res = {}
for slug in sorted(os.listdir(root)):
    d = os.path.join(root, slug)
    if not os.path.isdir(d): continue
    mp3 = next((os.path.join(d, f) for f in os.listdir(d) if f.endswith('.mp3')), None)
    if not mp3: continue
    wav = os.path.join(d, slug + '.wav')
    if not os.path.exists(wav):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ac', '2', '-ar', '48000', wav], check=True)
    y, sr = librosa.load(mp3, sr=22050, mono=True)
    dur = len(y) / sr
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
    tempo = float(np.atleast_1d(tempo)[0])
    rms = librosa.feature.rms(y=y, hop_length=512)[0]; t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
    db = 20 * np.log10(rms + 1e-6); sm = uniform_filter1d(db, 43)          # ~1 s smoothing
    lag = 86                                                                # ~2 s before vs after
    jump = np.r_[np.zeros(lag), sm[lag:] - sm[:-lag]]
    cands = []
    for i in np.argsort(-jump):
        tt = float(t[i]) - 1.0
        if tt < 3 or tt > dur - 5: continue
        if all(abs(tt - c[0]) > 8 for c in cands): cands.append((round(tt, 2), round(float(jump[i]), 1)))
        if len(cands) >= 4: break
    # snap drops to the nearest beat
    bt = np.array(beats)
    drops = [(float(bt[np.argmin(np.abs(bt - c[0]))]) if len(bt) else c[0], c[1]) for c in cands]
    loud = [round(float(np.mean(db[(t >= a) & (t < a + 10)])), 1) for a in range(0, int(dur), 10)]
    res[slug] = dict(wav=wav, dur=round(dur, 2), bpm=round(tempo, 1), first_beat=round(float(bt[0]), 3) if len(bt) else 0,
                     drops=[(round(a, 2), j) for a, j in drops], loud_by_10s=loud)
    print(f"{slug:18s} {dur:6.1f}s  {tempo:6.1f} bpm  first beat {res[slug]['first_beat']:.2f}  drops {res[slug]['drops']}")
json.dump(res, open(out, 'w'), indent=1)
