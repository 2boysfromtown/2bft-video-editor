"""Remove a KNOWN track (you have its file) from the stream audio where it plays under speech - echo-cancellation style.
Use for third-party music/video that played on his screen under his voice (Content ID risk), when the original file is on disk.

usage: unmix_ref.py <stream48k.wav> <ref.wav|mp4> <offset_s> <learn_a> <learn_b> <fix_a> <fix_b> <out.wav>
  offset_s          stream time where ref second 0 plays (from tools/sync_clip.py)
  learn_a..learn_b  a stretch where ONLY the ref plays (no voice) - used to learn the exact delay and the playback EQ
  fix_a..fix_b      the stretch to clean; written into a copy of the stream audio (out.wav), 50 ms crossfades at both ends
Prints the attenuation of the ref measured on the learning stretch. Then point source.json "audio48k" at out.wav.
Method: sample-accurate delay by cross-correlation, per-frequency complex transfer H = <Y X*>/<|X|^2> (STFT), Y - H X,
then a gentle magnitude floor for the residual. Linear and conservative: if attenuation < 12 dB, don't rely on it.
"""
import subprocess, sys, tempfile, os
import numpy as np, soundfile as sf
from scipy.signal import stft, istft, correlate
sys.stdout.reconfigure(encoding='utf-8')
SR = 48000


def load_ref(p):
    if p.lower().endswith('.wav'):
        x, sr = sf.read(p, dtype='float32', always_2d=True)
        if sr == SR: return x
    t = os.path.join(tempfile.mkdtemp(), 'r.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', p, '-vn', '-ac', '2', '-ar', str(SR), t], check=True)
    return sf.read(t, dtype='float32', always_2d=True)[0]


def main():
    st, refp, off, la, lb, fa, fb, out = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:8]), sys.argv[8]
    Y, sr = sf.read(st, dtype='float32', always_2d=True)
    assert sr == SR, 'stream must be 48 kHz'
    R = load_ref(refp)
    # 1) exact delay on the learning stretch (mono, +-60 ms search)
    a, b = int(la * SR), int(lb * SR)
    y = Y[a:b].mean(1); r0 = int((la - off) * SR)
    pad = int(.06 * SR)
    x = R[max(0, r0 - pad): r0 + (b - a) + pad].mean(1)
    c = correlate(x, y, mode='valid', method='fft')
    lag = int(np.argmax(np.abs(c))) - pad  # ref sample index of stream sample a = r0 + lag
    off2 = off - lag / SR
    print(f'delay refined: offset {off:.4f} -> {off2:.5f} s ({lag / SR * 1000:+.1f} ms)')

    def ref_at(s0, n):
        i0 = int(round((s0 / SR - off2) * SR)); seg = np.zeros((n, 2), np.float32)
        lo, hi = max(0, i0), min(len(R), i0 + n)
        if hi > lo: seg[lo - i0:hi - i0] = R[lo:hi]
        return seg
    nper = 2048
    out_audio = Y.copy()
    for ch in range(2):
        yl = Y[a:b, ch]; xl = ref_at(a, b - a)[:, ch]
        _, _, Yf = stft(yl, SR, nperseg=nper); _, _, Xf = stft(xl, SR, nperseg=nper)
        H = (Yf * np.conj(Xf)).sum(1) / ((np.abs(Xf) ** 2).sum(1) + 1e-9)
        # attenuation on the learning stretch
        Vf = Yf - H[:, None] * Xf
        before = 10 * np.log10((np.abs(Yf) ** 2).sum() + 1e-12); after = 10 * np.log10((np.abs(Vf) ** 2).sum() + 1e-12)
        print(f'ch{ch}: ref attenuation on the learning stretch {before - after:.1f} dB')
        # clean the fix window (+-0.25 s context for the STFT)
        A, B = int((fa - .25) * SR), int((fb + .25) * SR)
        _, _, Yw = stft(Y[A:B, ch], SR, nperseg=nper); _, _, Xw = stft(ref_at(A, B - A)[:, ch], SR, nperseg=nper)
        E = H[:, None] * Xw
        V = Yw - E
        mag = np.maximum(np.abs(V) - .5 * np.abs(E), .12 * np.abs(Yw))  # gentle residual floor
        V = mag * np.exp(1j * np.angle(V))
        _, v = istft(V, SR, nperseg=nper)
        v = v[:B - A].astype(np.float32)
        i0, i1 = int(fa * SR) - A, int(fb * SR) - A
        fade = int(.05 * SR)
        w = np.ones(i1 - i0, np.float32); w[:fade] = np.linspace(0, 1, fade); w[-fade:] = np.linspace(1, 0, fade)
        seg = Y[int(fa * SR):int(fb * SR), ch]
        out_audio[int(fa * SR):int(fb * SR), ch] = seg * (1 - w) + v[i0:i1] * w
    sf.write(out, out_audio, SR, subtype='PCM_24')
    print('written', out)


if __name__ == '__main__':
    main()
