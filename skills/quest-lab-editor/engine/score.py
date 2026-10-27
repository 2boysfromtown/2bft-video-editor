"""Synthesised score + foley for the stream edits (numpy only, 48 kHz stereo).

Palette (caption-first / broadcast mode): 120 BPM pulse - kick, off-beat hats, clap on 2 and 4,
eighth-note pluck bass, marimba ostinato, short synth-brass stabs on big moments, riser + impact.
Key A major, one chord per bar (2 s): A - E - F#m - D.

build(dur, sections, bpm) -> (N,2) float32
  sections: list of dicts {t0, t1, state} with state in
    full   - whole kit + bass + marimba            (montage, titles, no talk)
    groove - hats + bass + marimba, soft kick     (under talk)
    light  - marimba + soft bass only              (under dense talk)
    pad    - one held chord, no rhythm             (breath / reflective)
    stop   - silence                               (before a turn)
  Bar grid is global (bar 0 at t=0) so sections stay on beat.
"""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(2026)


def t_(d): return np.arange(int(round(d * SR))) / SR
def env(d, tau): return np.exp(-t_(d) / tau)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def noise(d): return rng.standard_normal(int(round(d * SR)))
def norm(x, p=1.0):
    m = np.abs(x).max()
    return x * (p / m) if m > 0 else x
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, x, at, gain=1.0, pan=0.0):
    s = int(round(at * SR))
    if s >= len(buf) or s + len(x) <= 0: return
    if s < 0: x = x[-s:]; s = 0
    e = min(len(buf), s + len(x)); l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[s:e, 0] += x[:e - s] * gain * l * 1.414
    buf[s:e, 1] += x[:e - s] * gain * r * 1.414


# ---------- instruments ----------
def kick(v=1.0):
    d = .4; tt = t_(d); f = 48 + 90 * np.exp(-tt / .035)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, .16) + hp(noise(d), 3000) * env(d, .003) * .25
    return norm(x) * v

def hat(v=1.0, open_=False):
    d = .25 if open_ else .06
    return norm(hp(noise(d), 7500, 3) * env(d, .07 if open_ else .014)) * v

def clap(v=1.0):
    d = .25; x = np.zeros(int(d * SR))
    for k, o in enumerate([0, .009, .019]):
        b = bp(noise(d), 900, 3800) * env(d, .006 if k < 2 else .055); s = int(o * SR); x[s:] += b[:len(x) - s]
    return norm(x) * v

def marimba(m, v=1.0):
    d = 1.0; tt = t_(d); f = hz(m)
    x = np.sin(2 * np.pi * f * tt) * env(d, .32) + .35 * np.sin(2 * np.pi * f * 3.93 * tt) * env(d, .05) \
        + .12 * np.sin(2 * np.pi * f * 9.2 * tt) * env(d, .012)
    x += bp(noise(d), 1500, 5000) * env(d, .002) * .15
    a = min(len(x), 48); x[:a] *= np.linspace(0, 1, a)
    return norm(x) * v

def pluck_bass(m, d=.24, v=1.0):
    tt = t_(d + .08); f = hz(m)
    x = np.sin(2 * np.pi * f * tt) + .45 * np.sin(2 * np.pi * 2 * f * tt) + .18 * np.sin(2 * np.pi * 3 * f * tt)
    e = np.minimum(1, tt / .004) * np.exp(-tt / .18) * np.clip((d + .08 - tt) / .08, 0, 1)
    return norm(np.tanh(1.6 * x) * e) * v

def saw(f, d):
    tt = t_(d); out = np.zeros_like(tt)
    for det in (-.08, 0, .07):
        out += 2 * ((tt * f * (1 + det / 100 * 6)) % 1) - 1
    return out / 3

def stab(ms, v=1.0, d=.45):
    tt = t_(d); x = sum(saw(hz(m), d) for m in ms)
    # filter envelope: open then close
    y = np.zeros_like(x); seg = 480
    for i in range(0, len(x), seg):
        fc = 600 + 4200 * np.exp(-i / SR / .09)
        y[i:i + seg] = lp(x[max(0, i - 4000):i + seg], fc)[-len(x[i:i + seg]):]
    e = np.minimum(1, tt / .006) * np.exp(-tt / .22)
    return norm(y * e) * v

def pad(ms, d, v=1.0):
    tt = t_(d); x = sum(saw(hz(m), d) for m in ms)
    x = lp(x, 1100, 2); e = np.minimum(1, tt / .6) * np.minimum(1, (d - tt) / .8).clip(0, 1)
    return norm(x * e) * v

def riser(d=1.6, v=1.0):
    tt = t_(d); n = noise(d); y = np.zeros_like(n); seg = 480
    for i in range(0, len(n), seg):
        f = 400 + 7000 * (i / len(n)) ** 2
        y[i:i + seg] = bp(n[max(0, i - 3000):i + seg], f * .7, min(f * 1.4, 20000))[-len(n[i:i + seg]):]
    tone = np.sin(2 * np.pi * np.cumsum(220 * 2 ** (2 * tt / d)) / SR) * .25
    return norm((y + tone) * (tt / d) ** 2) * v

def impact(v=1.0):
    d = 2.2; tt = t_(d)
    sub = np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-tt / .05)) / SR) * env(d, .45)
    cym = hp(noise(d), 4000, 2) * env(d, .7) * .35
    body = lp(noise(d), 500) * env(d, .08) * .7
    return norm(sub + cym + body) * v

# ---------- foley for graphics ----------
def whoosh(d=.32, v=1.0):
    n = noise(d); tt = t_(d); out = np.zeros_like(n)
    for i in range(0, len(n), 480):
        hi_ = min(len(n), i + 480); f = 500 + 3000 * np.sin(np.pi * i / len(n))
        out[i:hi_] = bp(n[max(0, i - 2000):hi_], f * .7, f * 1.35)[-(hi_ - i):]
    return norm(out * np.sin(np.pi * tt / d) ** 2) * v

def click(v=1.0, pitch=1.0):
    d = .05; tt = t_(d)
    x = hp(noise(d), 2500) * env(d, .0015) + .6 * np.sin(2 * np.pi * 2900 * pitch * tt) * env(d, .01) \
        + .4 * np.sin(2 * np.pi * 190 * pitch * tt) * env(d, .01)
    return norm(x) * v

def thump(v=1.0, f=65):
    d = .35; tt = t_(d)
    return norm(np.sin(2 * np.pi * f * tt * (1 - .3 * tt)) * env(d, .07) + lp(noise(d), 300) * env(d, .02) * .5) * v

def slam(v=1.0):
    a = click(1, .8); b = thump(1, 70); n = max(len(a), len(b)); x = np.zeros(n); x[:len(a)] += a * .7; x[:len(b)] += b
    return norm(x) * v

def pop(v=1.0):
    d = .14; tt = t_(d); f = 500 + 1500 * tt / d
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, .04)) * v

def ding(v=1.0):
    d = 1.4; tt = t_(d)
    x = sum(a * np.sin(2 * np.pi * f * tt) * env(d, tau) for f, a, tau in [(1318, 1, .5), (2637, .45, .3), (3951, .25, .18), (1976, .2, .45)])
    return norm(x) * v

def shutter(v=1.0):
    a = click(1, 1.4); b = click(.8, 1.1); x = np.zeros(int(.12 * SR)); x[:len(a)] += a; s = int(.06 * SR); x[s:s + len(b)] += b[:len(x) - s]
    return norm(x + hp(noise(.12), 3000) * env(.12, .02) * .3) * v

def tick(v=1.0):
    return click(v, 1.6) * .7

def tape_rewind(d=.6, v=1.0):
    tt = t_(d); f = 900 + 1800 * tt / d
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * .3 + bp(noise(d), 1500, 6000) * .5
    return norm(x * np.sin(np.pi * tt / d) ** .5) * v

def keys(d=1.0, v=1.0):
    """keyboard typing burst"""
    x = np.zeros(int(d * SR)); t = 0.0
    while t < d - .05:
        c = click(.5 + rng.random() * .5, .7 + rng.random() * .5); s = int(t * SR); x[s:s + len(c)] += c[:len(x) - s]
        t += .06 + rng.random() * .09
    return norm(x) * v

FOLEY = dict(whoosh=whoosh, click=click, thump=thump, slam=slam, pop=pop, ding=ding, shutter=shutter, tick=tick,
             rewind=tape_rewind, keys=keys, riser=riser, impact=impact)


# ---------- score ----------
CHORDS = [  # (root midi for bass, chord tones for marimba/stab) A - E - F#m - D
    (45, [57, 61, 64, 69, 73, 76]),
    (40, [56, 59, 64, 68, 71, 76]),
    (42, [57, 61, 66, 69, 73, 78]),
    (38, [57, 62, 66, 69, 74, 78]),
]
OSTINATO = [0, 2, 4, 2, 5, 2, 4, 3]   # index into chord tones, eighth notes


def state_at(sections, t):
    for s in sections:
        if s['t0'] <= t < s['t1']:
            return s['state']
    return 'stop'


def build(dur, sections, bpm=120, hits=()):
    """hits: list of (t, kind) kind in stab|impact|riser_to (riser ends at t)"""
    beat = 60 / bpm; bar = 4 * beat; e8 = beat / 2
    out = np.zeros((int(dur * SR) + SR, 2), np.float32)
    nb = int(dur / bar) + 1
    for b in range(nb):
        root, tones = CHORDS[b % 4]
        for k in range(8):           # eighths
            t = b * bar + k * e8
            st = state_at(sections, t)
            if st in ('stop', 'pad'): continue
            # marimba ostinato
            gm = {'full': .30, 'groove': .26, 'light': .22}[st]
            add(out, marimba(tones[OSTINATO[k]], 1.0), t, gm * (1.0 if k % 2 == 0 else .8), pan=-.25 + .5 * (k % 2))
            # bass on eighths (light: quarters only, soft)
            if st != 'light' or k % 2 == 0:
                gb = {'full': .5, 'groove': .42, 'light': .3}[st]
                add(out, lp(pluck_bass(root + (12 if k in (3, 7) else 0), .22), 900), t, gb)
            # hats on the off-beats
            if st in ('full', 'groove') and k % 2 == 1:
                add(out, hat(1), t, .16 if st == 'full' else .1, pan=.3)
            # kick / clap
            if st == 'full':
                if k % 2 == 0: add(out, kick(1), t, .62)
                if k in (2, 6): add(out, clap(1), t, .28, pan=-.1)
            elif st == 'groove' and k in (0, 4):
                add(out, kick(1), t, .38)
        # pad bars
        tb = b * bar
        if state_at(sections, tb) == 'pad':
            add(out, pad([tones[0] - 12, tones[1] - 12, tones[2] - 12, tones[3]], bar + .6), tb, .22)
    for t, kind in hits:
        if kind == 'stab':
            add(out, stab([m - 12 for m in CHORDS[int(t / bar) % 4][1][:3]] + [CHORDS[int(t / bar) % 4][1][3]], 1), t, .45)
        elif kind == 'impact':
            add(out, impact(1), t, .8)
        elif kind == 'riser_to':
            r = riser(1.6, 1); add(out, r, t - len(r) / SR, .35)
    # bus: gentle saturation + room-ish stereo widen
    out = np.tanh(out * 1.2) / 1.2
    return out[:int(dur * SR)]
