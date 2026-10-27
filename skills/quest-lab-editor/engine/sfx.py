"""QUEST LAB sound kit — synthesised SFX (numpy, 48 kHz mono). Placeholders until licensed/CC0 samples are dropped into sfx_lib/.
If sfx_lib/<name>.wav exists it is used instead of the synth (so real samples upgrade the whole kit without code changes).
"""
import os
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt
from score import SR, t_, env, lp, hp, bp, noise, norm, whoosh, click, thump, slam, pop, ding, shutter, tick, tape_rewind, keys, riser, impact

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sfx_lib')
rng = np.random.default_rng(7)

def whoosh_s(v=1.0): return whoosh(.2, v)

def stamp(v=1.0):
    d = .45; tt = t_(d)
    body = np.sin(2 * np.pi * np.cumsum(90 + 120 * np.exp(-tt / .02)) / SR) * env(d, .09)
    slap = bp(noise(d), 800, 5000) * env(d, .012) * .9
    return norm(body + slap) * v

def fail(v=1.0):   # two-tone descending buzzer (game "wrong")
    out = []
    for f, d in ((311, .16), (233, .32)):
        tt = t_(d); sq = np.sign(np.sin(2 * np.pi * f * tt)) * .5 + np.sin(2 * np.pi * f * tt) * .5
        out.append(lp(sq, 2500) * np.minimum(1, tt / .005) * np.clip((d - tt) / .03, 0, 1))
    return norm(np.concatenate(out)) * v

def scratch(v=1.0):   # record scratch: fast pitch-bent noise + tone, back and forth
    d = .42; tt = t_(d); ph = np.sin(2 * np.pi * 7.5 * tt) * np.exp(-tt / .25)
    f = 900 + 700 * ph
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * .35
    n = bp(noise(d), 600, 4000) * (.6 + .4 * np.abs(ph))
    return norm((tone + n) * np.minimum(1, tt / .01) * np.clip((d - tt) / .06, 0, 1)) * v

def glitch(v=1.0):
    d = .25; x = np.zeros(int(d * SR))
    for k in range(7):
        s = int(rng.random() * (len(x) - 2400)); L = int((.008 + rng.random() * .025) * SR)
        seg = np.sign(np.sin(2 * np.pi * (300 + rng.random() * 3000) * t_(L / SR))) * .6 + noise(L / SR) * .4
        x[s:s + L] += seg[:len(x) - s]
    return norm(hp(x, 200)) * v

def typing(v=1.0, dur=1.0): return keys(max(.2, dur), v)

def marker(v=1.0):   # marker squeak for drawn circles
    d = .38; tt = t_(d); f = 2200 + 500 * np.sin(2 * np.pi * 3 * tt)
    x = bp(noise(d), 1800, 5200) * (.5 + .5 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.sin(np.pi * tt / d) ** .7
    return norm(x) * v

def hit(v=1.0):   # bass hit with pitch drop (boom)
    d = 1.1; tt = t_(d)
    x = np.sin(2 * np.pi * np.cumsum(38 + 110 * np.exp(-tt / .045)) / SR) * env(d, .28) + lp(noise(d), 400) * env(d, .03) * .5
    return norm(np.tanh(x * 1.6)) * v

def punch(v=1.0):   # short thump for a zoom punch
    d = .3; tt = t_(d)
    return norm(np.sin(2 * np.pi * np.cumsum(60 + 160 * np.exp(-tt / .02)) / SR) * env(d, .07) + hp(noise(d), 2500) * env(d, .004) * .3) * v

def ticks(v=1.0, dur=.8):
    x = np.zeros(int((dur + .1) * SR)); t = 0.0
    while t < dur: c = tick(1); s = int(t * SR); x[s:s + len(c)] += c[:len(x) - s]; t += .045
    return norm(x) * v

def levelup(v=1.0):   # bright 4-note arpeggio
    out = np.zeros(int(.9 * SR))
    for i, m in enumerate((72, 76, 79, 84)):
        f = 440 * 2 ** ((m - 69) / 12); d = .5; tt = t_(d)
        x = (np.sin(2 * np.pi * f * tt) + .3 * np.sin(2 * np.pi * 2 * f * tt)) * env(d, .16)
        s = int(i * .07 * SR); out[s:s + len(x)] += x[:len(out) - s]
    return norm(out) * v

def sparkle(v=1.0):
    out = np.zeros(int(1.0 * SR))
    for i in range(9):
        f = 2000 + rng.random() * 4000; d = .3; tt = t_(d); x = np.sin(2 * np.pi * f * tt) * env(d, .06)
        s = int(i * .05 * SR); out[s:s + len(x)] += x[:len(out) - s] * (1 - i / 12)
    return norm(out) * v

def boom(v=1.0):   # sub drop for big reveals
    d = 2.0; tt = t_(d)
    x = np.sin(2 * np.pi * np.cumsum(30 + 70 * np.exp(-tt / .12)) / SR) * env(d, .7)
    return norm(np.tanh(1.4 * x) + lp(noise(d), 200) * env(d, .05) * .4) * v

def riser2(v=1.0, dur=1.6): return riser(dur, v)

def ding2(v=1.0): return ding(v)

SYNTH = dict(whoosh=whoosh, whoosh_s=whoosh_s, click=click, thump=thump, slam=slam, pop=pop, ding=ding2, shutter=shutter, tick=tick,
             rewind=tape_rewind, typing=typing, keys=keys, riser=riser2, impact=impact, stamp=stamp, fail=fail, scratch=scratch,
             glitch=glitch, marker=marker, hit=hit, punch=punch, ticks=ticks, levelup=levelup, sparkle=sparkle, boom=boom)

_cache = {}
def get(name, dur=None):
    p = os.path.join(LIB, name + '.wav')
    if os.path.exists(p):
        if p not in _cache:
            x, sr = sf.read(p, dtype='float32', always_2d=True); x = x.mean(1)
            if sr != SR:
                import librosa  # noqa
                x = librosa.resample(x, orig_sr=sr, target_sr=SR)
            _cache[p] = norm(x)
        x = _cache[p]
        if dur and len(x) > dur * SR: x = x[:int(dur * SR)] * np.r_[np.ones(int(dur * SR) - 480), np.linspace(1, 0, 480)]
        return x
    fn = SYNTH.get(name)
    if fn is None: raise KeyError(name)
    return fn(1.0, dur) if (dur and name in ('typing', 'ticks', 'riser')) else fn(1.0)
