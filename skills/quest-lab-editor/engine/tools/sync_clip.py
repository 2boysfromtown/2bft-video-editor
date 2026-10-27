"""Find where an inserted clip plays inside the stream: per-window cross-correlation of 16 kHz audio.
usage: sync_clip.py <stream16k.wav> <clip.mp4> <from_s> <to_s> [win_s=6]"""
import sys, subprocess, numpy as np, soundfile as sf
from scipy.signal import fftconvolve
st, clip, a, b = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]); win = float(sys.argv[5]) if len(sys.argv) > 5 else 6.0
x, sr = sf.read(st, dtype='float32', start=int(a * 16000), stop=int(b * 16000))
c = subprocess.run(['ffmpeg', '-v', 'error', '-i', clip, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout
y = np.frombuffer(c, np.float32)
def nz(v): v = v - v.mean(); return v / (np.sqrt((v ** 2).sum()) + 1e-9)
for w0 in np.arange(0, (b - a) - win, win):
    seg = nz(x[int(w0 * 16000): int((w0 + win) * 16000)])
    cc = fftconvolve(y, seg[::-1], mode='valid')
    # normalise by local energy of y
    cs = np.r_[0, np.cumsum(y.astype(np.float64) ** 2)]; e = np.sqrt(cs[len(seg):] - cs[:-len(seg)]) + 1e-9
    r = cc / e; i = int(np.argmax(r))
    print(f'stream {a + w0:7.2f}s -> clip {i / 16000:6.2f}s  corr {r[i]:.2f}  offset {a + w0 - i / 16000:7.2f}')
