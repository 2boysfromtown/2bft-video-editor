"""Original, copyright-free music beds and sound effects, synthesised with numpy.

Used by clipkit.py and build_react_short.py. Nothing here is sampled from any song or
sound library, so the output is safe to publish.

CLI:
  python synth_audio.py out.wav groove|bounce [seconds]       music bed
  python synth_audio.py out.wav whoosh|hit|pop|ding|boing|riser|airhorn
"""
from __future__ import annotations

import wave

import numpy as np

SR = 48000
RNG = np.random.default_rng(7)


def _t(n):
    return np.arange(int(n)) / SR


def _lp(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def _hp_noise(n, amount=1.0):
    w = RNG.standard_normal(int(n))
    return np.diff(w, prepend=0.0) * amount


def write_wav(path, stereo):
    pk = np.max(np.abs(stereo)) or 1.0
    data = (np.clip(stereo / max(pk, 1.0), -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


# ---------------------------------------------------------------- drum + tone voices
def kick(n=0.35):
    t = _t(n * SR)
    f = 48 + 110 * np.exp(-t * 32)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) + 0.25 * np.exp(-t * 400) * RNG.standard_normal(len(t))


def snare(n=0.3):
    t = _t(n * SR)
    return 0.55 * RNG.standard_normal(len(t)) * np.exp(-t * 17) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 24)


def hat(n=0.08, open_=False):
    t = _t((0.28 if open_ else n) * SR)
    return _hp_noise(len(t), 0.5) * np.exp(-t * (14 if open_ else 62)) * 0.45


def tone(freq, n, decay=4.0, harm=(1.0, 0.45, 0.2, 0.08)):
    t = _t(n * SR)
    out = np.zeros_like(t)
    for k, h in enumerate(harm, 1):
        out += h * np.sin(2 * np.pi * freq * k * t)
    return out * np.exp(-t * decay)


def tri(freq, n, decay=2.5):
    t = _t(n * SR)
    return (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * freq * t)) * np.exp(-t * decay)


def _place(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name):
    n, o = name[:-1], int(name[-1])
    sharp = 1 if n.endswith("#") else 0
    return 12 * (o + 1) + NOTE[n[0]] + sharp


def hz(name):
    return 440.0 * 2 ** ((midi(name) - 69) / 12)


# ---------------------------------------------------------------- music beds
def music(style: str, dur: float, bpm: float | None = None) -> np.ndarray:
    """Returns stereo float array, about -18 dBFS peak-ish, loop-friendly length = dur."""
    n = int(dur * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    if style == "groove":  # laid-back boom-bap, minor key
        bpm = bpm or 90
        beat = 60 / bpm
        step = beat / 4
        chords = [("A2", ["A3", "C4", "E4", "G4"]), ("F2", ["F3", "A3", "C4", "E4"]),
                  ("C3", ["C4", "E4", "G4", "B4"]), ("G2", ["G3", "B3", "D4", "F4"])]
        bars = int(dur / (beat * 4)) + 2
        kicks = {0, 6, 10}
        snares = {4, 12}
        for b in range(bars):
            root, notes = chords[b % 4]
            t0 = b * beat * 4
            for s in range(16):
                at = t0 + s * step + (step * 0.18 if s % 2 else 0)  # swing
                if s in kicks:
                    _place(L, kick(), at, 0.9); _place(R, kick(), at, 0.9)
                if s in snares:
                    _place(L, snare(), at, 0.75); _place(R, snare(), at, 0.75)
                if s % 2 == 0:
                    g = 0.5 if s % 4 else 0.8
                    _place(L, hat(), at, g); _place(R, hat(), at + 0.004, g)
            _place(L, tri(hz(root), beat * 3.6, 1.6), t0, 0.9); _place(R, tri(hz(root), beat * 3.6, 1.6), t0, 0.9)
            for k, nt in enumerate(notes):
                for hit in (0, 2.5):
                    _place(L, tone(hz(nt), 1.2, 3.2) * 0.16, t0 + hit * beat + k * 0.012)
                    _place(R, tone(hz(nt), 1.2, 3.2) * 0.16, t0 + hit * beat + k * 0.012 + 0.006)
    elif style == "bounce":  # playful, staccato, major pentatonic
        bpm = bpm or 112
        beat = 60 / bpm
        step = beat / 2
        melody = ["C5", "E5", "G5", "E5", "A5", "G5", "E5", "D5", "C5", "D5", "E5", "G5", "E5", "D5", "C5", "A4"]
        bass = ["C3", "C3", "F3", "G3"]
        bars = int(dur / (beat * 4)) + 2
        for b in range(bars):
            t0 = b * beat * 4
            for s in range(8):
                at = t0 + s * step
                if s in (0, 5):
                    _place(L, kick(), at, 0.85); _place(R, kick(), at, 0.85)
                if s in (2, 6):
                    _place(L, snare(0.2), at, 0.6); _place(R, snare(0.2), at, 0.6)
                _place(L, hat(), at, 0.35); _place(R, hat(), at, 0.35)
                nt = melody[(b * 8 + s) % len(melody)]
                _place(L, tone(hz(nt), 0.35, 11, (1.0, 0.3, 0.1)) * 0.28, at)
                _place(R, tone(hz(nt), 0.35, 11, (1.0, 0.3, 0.1)) * 0.28, at + 0.005)
            _place(L, tri(hz(bass[b % 4]), beat * 1.6, 2.2), t0, 0.8); _place(R, tri(hz(bass[b % 4]), beat * 1.6, 2.2), t0, 0.8)
            _place(L, tri(hz(bass[b % 4]), beat * 1.6, 2.2), t0 + beat * 2, 0.8); _place(R, tri(hz(bass[b % 4]), beat * 1.6, 2.2), t0 + beat * 2, 0.8)
    else:
        raise ValueError(style)
    st = np.stack([_lp(L, 8000), _lp(R, 8000)], axis=1)
    pk = np.max(np.abs(st)) or 1
    return st / pk * 0.5


# ---------------------------------------------------------------- sound effects
def sfx(kind: str, dur: float | None = None) -> np.ndarray:
    """Mono array."""
    if kind == "whoosh":
        d = dur or 0.65
        n = int(d * SR)
        t = _t(n)
        noise = RNG.standard_normal(n)
        out = np.zeros(n)
        a = 0.0
        for i in range(n):  # sweeping low-pass: 250 Hz -> 6 kHz
            fc = 250 + 5750 * (i / n) ** 2
            k = np.exp(-2 * np.pi * fc / SR)
            a = (1 - k) * noise[i] + k * a
            out[i] = a
        env = np.sin(np.pi * (t / d) ** 0.8) ** 2
        low = _lp(RNG.standard_normal(n), 220) * 6 * env  # low layer for weight
        return (out * env * 1.6 + low * 0.5)
    if kind == "hit":
        t = _t(0.9 * SR)
        f = 52 + 80 * np.exp(-t * 28)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5)
        crack = RNG.standard_normal(len(t)) * np.exp(-t * 60) * 0.35
        air = _lp(RNG.standard_normal(len(t)), 2500) * np.exp(-t * 7) * 0.25
        return body + crack + air
    if kind == "pop":
        t = _t(0.1 * SR)
        f = 600 + 1500 * (t / 0.1)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38) * 0.8
    if kind == "ding":
        t = _t(1.4 * SR)
        return (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 1976 * t) + 0.25 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 3.2) * 0.45
    if kind == "boing":
        t = _t(0.55 * SR)
        f = 220 + 260 * np.exp(-t * 5) * (1 + 0.8 * np.sin(2 * np.pi * 9 * t))
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5.5) * 0.7
    if kind == "riser":
        d = dur or 1.6
        n = int(d * SR)
        t = _t(n)
        f = 180 + 1700 * (t / d) ** 2
        tone_ = np.sin(2 * np.pi * np.cumsum(f) / SR)
        nz = _lp(RNG.standard_normal(n), 3500)
        env = (t / d) ** 1.6
        return (0.45 * tone_ + 0.8 * nz) * env * 0.7
    if kind == "airhorn":
        d = dur or 0.9
        t = _t(d * SR)
        sig = np.zeros_like(t)
        for f in (466.0, 554.4, 698.5):
            for dt in (0.997, 1.003):
                ph = (f * dt * t) % 1.0
                sig += (2 * ph - 1)
        env = np.minimum(1, t / 0.02) * np.exp(-np.maximum(0, t - d * 0.65) * 9)
        return _lp(sig, 5000) * env * 0.16
    raise ValueError(kind)


def sfx_track(events, dur: float) -> np.ndarray:
    """events: [(time_seconds, kind, gain)] -> stereo array of length dur."""
    n = int(dur * SR)
    buf = np.zeros(n)
    for t, kind, gain in events:
        s = sfx(kind)
        _place(buf, s, max(0.0, t), gain)
    pk = np.max(np.abs(buf)) or 1
    buf = buf / max(pk, 1.0)
    return np.stack([buf, buf], axis=1)


if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    kind = sys.argv[2]
    if kind in ("groove", "bounce"):
        write_wav(out, music(kind, float(sys.argv[3]) if len(sys.argv) > 3 else 20))
    else:
        s = sfx(kind)
        write_wav(out, np.stack([s, s], axis=1))
    print(out)
