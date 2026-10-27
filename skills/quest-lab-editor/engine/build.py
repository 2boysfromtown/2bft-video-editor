"""QUEST LAB build: plan (source times) -> edits/<name>.json (render timeline + energy camera) + edits/<name>.audio.json + frame cache.

usage: python build.py plans/<name>.py [--no-frames]

PLAN = dict(name, size '16x9'|'9x16', shots=[...], gfx=[...], music=[...], assets={name: path}, clips={name: dict(path, size, wav)})
Shot keys
  in, out             source seconds  (or freeze=t, dur=d for a held frame)
  layout              16x9: screen | stage | face | loot | versus | full      9x16: v_split | v_face | v_screen | v_loot | v_output | v_cam
  rect, rect1         source crop of the screen (rect1 = end of a push; ease io|out|punch|lin)
  cam                 'card' (default) | 'bubble' | None — how the webcam sits on screen layouts
  media / media2      'img:<asset>' | 'clip:<name>' for loot / versus layouts (clip0 = start second in the clip)
  bg                  'blue' | 'ink' | 'blur'
  speed, vol, fx{flash,freeze,freezeColor,rewind,whip,glitch}
  shake               energy-camera multiplier (default 1 on face/stage layouts, .6 elsewhere, 0 = locked)
  punch               [(src_t, 'zoom'|'shake'|'impact', strength)]  — manual hits on top of the measured energy
  caps                [(src_t, "words {mint} {!red} {$yellow} *shake* ^big / newline", {end, y, size, dx})]
  gfx                 [dict(type=..., at=src_t | dt=local, dur=..., ...)]
  sfx                 [(src_t | ('dt', x), name, gain_db)]
  echo                [(src_t0, src_t1, dict(delay=.32, fb=.45, taps=4))]   — echo throw on a word / phrase
  verb                [(src_t0, src_t1, wet)]                                  — reverb on a reflective line
  music               music state from this shot on ('drop' | 'groove' | 'light' | 'stop' | 'pad' | track cue)
Global gfx use output-time markers: numbers (negative = from the end), 'start', 'end', ('shot', i[, 'end']).
"""
import json, math, os, re, subprocess, sys, runpy
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(ROOT, 'source.json')))
SRC = CFG['video']; FPS = 30
SCR, CAM, FACE = CFG['screen'], CFG['cam'], CFG['face']
# v_face framing presets (PLAN key 'vface'). 'high' puts the face high so chest captions at y ~1200 never cover it (default);
# 'classic' is the first framing (used by S06-S15 of the 25 Oct stream). punch = the 1.18x jump-cut crop with the same face centre.
VFACE = {'high': dict(camd=[60, 250, 960, 1150], camrect=[1474, 426, 388, 465], punch=[1504, 461, 329, 394]),
         'classic': dict(camd=[60, 270, 960, 1300], camrect=[1474, 262, 388, 525], punch=[1504, 310, 329, 445])}
VF = VFACE['high']
SRC_DUR = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', SRC], capture_output=True, text=True).stdout.strip() or 1e9)
ENERGY = json.load(open(CFG['energy']))
EN = np.array(ENERGY['energy'], dtype=np.float32); EV = ENERGY['events']
WORDS = json.load(open(CFG['words'], encoding='utf-8'))
CLIPS = {}
FACE_LAYOUTS = {'face', 'stage', 'v_face', 'v_split'}

# ---------------------------------------------------------------- layouts
def card(s0, d, **kw):
    p = dict(s0=s0, d=d, r=kw.pop('r', 22), outline=kw.pop('outline', 6), shadow=kw.pop('shadow', 12)); p.update(kw); return p

CAM_GRADE = {}   # webcam-only grade (PLAN or source.json 'cam_grade'): contrast, bright, grade (CSS filter string); screen panes stay untouched


# face tracking (tools/face_track.py -> source.json "facetrack"): every webcam crop follows his eyes, frame by frame
FT = None
if CFG.get('facetrack') and os.path.exists(CFG['facetrack']):
    FT = json.load(open(CFG['facetrack']))


def face_offsets(p, src0, sp, dur, frz, ref_ey, step=1 / 15):
    """Per-output-time [loc, dx, dy] for a webcam pane. Keeps the crop's designed composition at his usual eye line (ref_ey),
    with the eyes held between 30 % and 50 % of the crop height, and the crop always inside the webcam rect."""
    cam, fps, EY, CX = FT['cam'], FT['fps'], FT['ey'], FT['cx']
    rects = [p['s0']] + ([p['s1']] if p.get('s1') else [])
    r = rects[0]
    fy = min(.50, max(.30, (ref_ey - r[1]) / r[3]))
    lo_x = max(cam[0] - q[0] for q in rects); hi_x = min(cam[0] + cam[2] - (q[0] + q[2]) for q in rects)
    lo_y = max(cam[1] - q[1] for q in rects); hi_y = min(cam[1] + cam[3] - (q[1] + q[3]) for q in rects)
    out = []
    for i in range(int(dur / step) + 2):
        loc = i * step; src = src0 if frz else src0 + loc * sp
        j = src * fps; j0 = int(max(0, min(len(EY) - 2, math.floor(j)))); f = min(1.0, max(0.0, j - j0))
        e = EY[j0] * (1 - f) + EY[j0 + 1] * f; c = CX[j0] * (1 - f) + CX[j0 + 1] * f
        dx = c - (r[0] + r[2] / 2); dy = e - (r[1] + fy * r[3])
        dx = 0.0 if lo_x > hi_x else min(max(dx, lo_x), hi_x)
        dy = 0.0 if lo_y > hi_y else min(max(dy, lo_y), hi_y)
        out.append([round(loc, 3), round(dx, 1), round(dy, 1)])
    return out


def cam_pane(s, d, **kw):
    default = kw.pop('camrect', CAM)
    g = {k: v for k, v in CAM_GRADE.items() if k in ('contrast', 'bright', 'grade')}
    if s.get('cam') == 'bubble':
        return dict(s0=s.get('facerect', FACE), d=d, round=True, outline=6, shadow=10, trackable=True, **g, **kw)
    return card(s.get('camrect', default), d, trackable=True, **g, **kw)

def media_pane(m, d, s, **kw):
    if m.startswith('img:'): p = card(s.get('mrect') or ([0, 0] + list(s.get('msize', [1920, 1080]))), d, src=m, **kw)   # mrect = source crop of the still
    else:
        c = m.split(':', 1)[1]; cw, ch = CLIPS[c]['size']
        p = card(s.get('mrect', [0, 0, cw, ch]), d, src=m, clip0=s.get('clip0', 0.0), **kw)
    if s.get('mrect1'): p['s1'] = s['mrect1']
    return p

def panes_16x9(s):
    L = s.get('layout', 'stage'); rect = s.get('rect', SCR); r1 = s.get('rect1'); ease = s.get('ease', 'io')
    scr = lambda d, **kw: dict(s0=rect, s1=r1, ease=ease, d=d, **kw)
    P = []
    if L == 'screen':                       # screen fills the frame (4 % overscan so shake never shows an edge), cam as sticker
        P.append(scr([-40, -23, 2000, 1126], r=0))
        c = s.get('cam', 'card')
        if c == 'card': P.append(cam_pane(s, [1610, 438, 270, 532], tilt=2, r=18, outline=5, shadow=9, **({'in': s['camin']} if s.get('camin') else {})))
        elif c == 'bubble': P.append(cam_pane(s, [1600, 760, 280, 280]))
    elif L == 'stage':                      # screen card + tall cam card on the blue world
        P.append(scr([52, 150, 1330, 748], r=20, outline=6, shadow=12, tilt=s.get('tilt', -0.8)))
        P.append(cam_pane(s, [1426, 92, 446, 880], tilt=1.6, r=22))
    elif L == 'face':                       # cam is the show; right side for slams / a small screen card
        P.append(cam_pane(s, [120, 36, 540, 1010], camrect=s.get('camrect', [1474, 200, 388, 726]), tilt=-1.5, r=24, outline=7, shadow=14))
        if s.get('side', 'screen') == 'screen': P.append(scr([760, 250, 1080, 608], r=18, outline=6, shadow=12, tilt=1.2))
    elif L == 'loot':                       # an output, big, from the original file; cam reacts at the side
        m = s['media']; d = s.get('md', [56, 92, 1360, 765] if not s.get('tall') else [300, 42, 556, 988])
        P.append(media_pane(m, d, s, r=18, outline=7, shadow=14, tilt=s.get('tilt', -0.6)))
        if s.get('cam', 'card'): P.append(cam_pane(s, s.get('camd', [1480, 150, 400, 788] if not s.get('tall') else [930, 150, 420, 828]), tilt=2, r=20))
    elif L == 'tallscreen':                 # a vertical video playing on the screen share, as a tall card; cam reacts beside it
        P.append(scr(s.get('md', [300, 42, 556, 988]), r=18, outline=7, shadow=14, tilt=s.get('tilt', -0.6)))
        if s.get('cam', 'card'): P.append(cam_pane(s, s.get('camd', [930, 150, 420, 828]), tilt=2, r=20))
    elif L == 'versus':
        P.append(media_pane(s['media'], [48, 236, 900, 506], s, r=16, outline=6, shadow=12, tilt=-1.2))
        s2 = dict(s, mrect=s.get('mrect2'), mrect1=None, msize=s.get('msize2', s.get('msize', [1920, 1080])))
        P.append(media_pane(s['media2'], [972, 236, 900, 506], s2, r=16, outline=6, shadow=12, tilt=1.2))
    elif L == 'full':
        P.append(dict(s0=s.get('rect', [0, 0, 1920, 1080]), s1=r1, ease=ease, d=[-40, -23, 2000, 1126], r=0))
    else: raise SystemExit('unknown 16x9 layout ' + L)
    return P

def panes_9x16(s):
    L = s.get('layout', 'v_split'); rect = s.get('rect', [430, 125, 860, 794]); r1 = s.get('rect1'); ease = s.get('ease', 'io')
    scr = lambda d, **kw: dict(s0=rect, s1=r1, ease=ease, d=d, **kw)
    P = []
    # safe box for both Shorts and Reels: x 65-850, y 288-1248 (captions ~y 900-1240, hook ~y 300-600, right 230 px of the lower half is buttons)
    if L == 'v_split':                      # proof on top, face below, captions on the seam
        P.append(scr([40, 300, 1000, 600], r=20, outline=6, shadow=12, tilt=-1))
        P.append(cam_pane(s, s.get('camd', [110, 945, 860, 720]), camrect=s.get('camrect', [1474, 410, 388, 325]), tilt=1.5, r=22))
    elif L == 'v_face':                     # face is the shot; captions over the chest
        P.append(cam_pane(s, s.get('camd', VF['camd']), camrect=s.get('camrect', VF['camrect']), tilt=-1, r=26, outline=7, shadow=14))
    elif L == 'v_screen':                   # one screen region tall, face bubble
        P.append(scr([40, 290, 1000, 900], r=20, outline=6, shadow=12, tilt=-0.8))
        if s.get('cam', 'bubble'): P.append(cam_pane(dict(s, cam='bubble'), s.get('camd', [60, 1010, 300, 300])))
    elif L == 'v_loot':                     # an output (16:9 still/clip) big, face card below
        P.append(media_pane(s['media'], s.get('md', [30, 300, 1020, 574]), s, r=18, outline=6, shadow=12, tilt=-1.2))
        if s.get('cam', 'card'): P.append(cam_pane(s, s.get('camd', [110, 945, 860, 720]), camrect=s.get('camrect', [1474, 410, 388, 325]), tilt=1.5, r=22))
    elif L == 'v_tall':                     # a vertical video playing on the screen share (player 530,125 447x795), shown tall; face bubble top-right
        P.append(dict(s0=s.get('rect', [530, 125, 447, 795]), s1=r1, ease=ease, d=s.get('sd', [170, 270, 740, 1316]), r=20, outline=6, shadow=12, tilt=-0.8))
        if s.get('cam', 'bubble'): P.append(cam_pane(dict(s, cam='bubble'), s.get('camd', [770, 230, 270, 270])))
    elif L == 'v_full':                     # a vertical region of the stream (an episode playing on screen) fills the frame, optional face bubble
        P.append(scr([-20, -36, 1120, 1992], r=0))
        if s.get('cam'): P.append(cam_pane(dict(s, cam='bubble'), s.get('camd', [60, 990, 300, 300])))
    elif L == 'v_versus':                   # two outputs stacked: reference (top) vs result (bottom)
        P.append(media_pane(s['media'], s.get('md', [40, 330, 1000, 600]), s, r=16, outline=6, shadow=12, tilt=-1.2))
        s2 = dict(s, mrect=s.get('mrect2'), mrect1=s.get('mrect2_1'), msize=s.get('msize2', s.get('msize', [1920, 1080])))
        P.append(media_pane(s['media2'], s.get('md2', [40, 990, 1000, 600]), s2, r=16, outline=6, shadow=12, tilt=1.2))
    elif L == 'v_cam':                      # portrait phone footage: the camera itself fills the frame, face-tracked (camrect = source crop)
        P.append(cam_pane(s, s.get('camd', [-8, -14, 1096, 1948]), camrect=s.get('camrect', CAM), r=0, outline=0, shadow=0))
    elif L == 'v_output':                   # a 9:16 output full frame (Leela episodes), face bubble
        P.append(media_pane(s['media'], [-20, -36, 1120, 1992], s, r=0, outline=0, shadow=0))
        if s.get('cam'): P.append(cam_pane(dict(s, cam='bubble'), s.get('camd', [60, 990, 300, 300])))
    else: raise SystemExit('unknown 9x16 layout ' + L)
    return P

# ---------------------------------------------------------------- captions
TOK = re.compile(r'(\{[^}]*\}|[^\s{]+)')
def parse_words(text):
    words = []; br = False
    for ln_i, line in enumerate(text.split(' / ')):
        for tk in TOK.findall(line.replace('^{', '{^').replace('*{', '{*')):
            w = dict(tx=tk)
            if tk.startswith('{') and tk.endswith('}'):
                if tk[1:2] == '^': w0 = dict(big=True); tk = '{' + tk[2:]
                elif tk[1:2] == '*': w0 = dict(shake=True); tk = '{' + tk[2:]
                else: w0 = {}
                inner = tk[1:-1]; key = 'mint'
                if inner.startswith('!'): key, inner = 'red', inner[1:]
                elif inner.startswith('$'): key, inner = 'yellow', inner[1:]
                elif inner.startswith('~'): key, inner = 'blue', inner[1:]
                elif inner.startswith('=#') and ':' in inner: key, inner = inner[1:inner.index(':')], inner[inner.index(':') + 1:]   # {=#RRGGBB:word}
                w = dict(tx=inner, key=key, **w0)
            else:
                if tk.startswith('^'): w['big'] = True; tk = tk[1:]
                if tk.startswith('*') and tk.endswith('*') and len(tk) > 2: w['shake'] = True; tk = tk[1:-1]
                if tk.startswith('~~') and tk.endswith('~~') and len(tk) > 4: w['strike'] = True; tk = tk[2:-2]
                if tk.startswith('_') and tk.endswith('_') and len(tk) > 2: w['under'] = True; tk = tk[1:-1]
                w['tx'] = tk
            if br: w['br'] = True; br = False
            words.append(w)
        br = True
    return words

def speech_span(a, b):
    """last word end inside [a, b] from the transcript (source time)"""
    last = a
    for seg in WORDS['segments']:
        if seg['e'] < a or seg['s'] > b: continue
        for w in seg.get('words') or []:
            if a <= w['s'] < b: last = max(last, min(w['e'], b))
    return last

# ---------------------------------------------------------------- energy camera
def noise1(t, seed, freqs):
    return sum(a * math.sin(2 * math.pi * f * t + 6.2831 * ((seed * 7.13 + i * 3.7) % 1)) for i, (f, a) in enumerate(freqs)) / sum(a for _, a in freqs)

def camera_track(shots_out, P, total, unit):
    n = int(round(total * FPS)) + 1
    cam = np.zeros((n, 7), np.float32); cam[:, 3] = 1.0     # dx, dy, rot, zoom, rgb px, flash, hold (hit-stop seconds)
    # impacts allowed: the strongest measured peaks inside shots that permit shake (max_impacts per video)
    hits = []
    for si, (sh, s) in enumerate(shots_out):
        mul = s.get('shake', 1.0 if s.get('layout') in FACE_LAYOUTS else .6)
        if sh['freeze'] or mul <= 0 or sh['speed'] != 1: continue
        a, b = sh['src0'], sh['src0'] + (sh['t1'] - sh['t0'])
        for e in EV:
            if a + .15 <= e['t'] <= b - .1 and e['tier'] != 'rumble':
                hits.append(dict(out=sh['t0'] + (e['t'] - a), peak=e['peak'], tier=e['tier'], mul=mul, src=e['t']))
        for pt in s.get('punch', []):
            st, kind = pt[0], pt[1]; strength = pt[2] if len(pt) > 2 else 1.0
            if a <= st <= b: hits.append(dict(out=sh['t0'] + (st - a), peak=3.0 if kind == 'impact' else 1.6, tier=kind, mul=strength, src=st, manual=True))
    max_imp = P.get('max_impacts', 2)
    auto_imp = sorted([h for h in hits if h['tier'] == 'impact' and not h.get('manual')], key=lambda h: -h['peak'])
    for h in auto_imp[max_imp:]: h['tier'] = 'shake'
    # cooldown: no two shake/impact hits within 3 s (manual hits win, then the stronger peak)
    hits.sort(key=lambda h: (not h.get('manual'), -h['peak']))
    kept = []
    for h in hits:
        if h['tier'] in ('shake', 'impact') and any(abs(h['out'] - k['out']) < 3.0 and k['tier'] in ('shake', 'impact') for k in kept): continue
        kept.append(h)
    hits = sorted(kept, key=lambda h: h['out'])
    # hum: only where the energy stays high for ~1.5 s (sustained hype), face layouts only
    from scipy.ndimage import minimum_filter1d
    ENs = minimum_filter1d(EN, 45)
    for si, (sh, s) in enumerate(shots_out):
        mul = s.get('shake', 1.0 if s.get('layout') in FACE_LAYOUTS else .6)
        if sh['freeze'] or mul <= 0 or s.get('layout') not in FACE_LAYOUTS: continue
        f0, f1 = int(round(sh['t0'] * FPS)), int(round(sh['t1'] * FPS))
        for f in range(f0, min(f1, n)):
            t = f / FPS; st = sh['src0'] + (t - sh['t0']) * sh['speed']
            e = float(ENs[min(len(ENs) - 1, max(0, int(round(st * 30))))])
            r = max(0.0, min(4.0, (e - .8) * 6.0)) * mul
            if r > 0:
                cam[f, 0] += r * noise1(t, 1, [(1.3, 1), (2.4, .6), (4.1, .25)])
                cam[f, 1] += r * noise1(t, 2, [(1.1, 1), (2.7, .5), (3.9, .25)])
                cam[f, 2] += r * .05 * noise1(t, 3, [(.9, 1), (1.7, .5)])
    # shakes and impacts (sound gets a cue for each impact)
    cues = []
    for h in hits:
        tier, f0 = h['tier'], int(round(h['out'] * FPS))
        if tier == 'zoom':
            for f in range(max(0, f0 - 1), min(n, f0 + int(.7 * FPS))):
                lt = (f - f0) / FPS; k = (1 - math.exp(-max(lt, 0) / .03)) * math.exp(-max(lt - .05, 0) / .5) if lt >= 0 else 0
                cam[f, 3] += .09 * h['mul'] * k
            cues.append(dict(t=h['out'], name='punch', gain=-12)); continue
        amp = (30 if tier == 'impact' else 9 + 7 * min(1, max(0, (h['peak'] - 1.2) / .7))) * h['mul']
        tau = .32 if tier == 'impact' else .22
        stop = 3 if tier == 'impact' else 0                       # hit-stop: hold the impact frame 3 frames, then shake
        for f in range(f0, min(n, f0 + stop)): cam[f, 6] = (f - f0) / FPS
        for f in range(max(0, f0 - 1), min(n, f0 + int(1.2 * FPS))):
            lt = (f - f0 - stop) / FPS
            if lt < 0: continue
            env = min(1, lt / .04) * math.exp(-lt / tau)
            cam[f, 0] += amp * env * noise1(lt, h['src'], [(11, 1), (17, .5), (7, .4)])
            cam[f, 1] += amp * env * noise1(lt, h['src'] + 5, [(13, 1), (19, .45), (8, .4)])
            cam[f, 2] += amp * .045 * env * noise1(lt, h['src'] + 9, [(9, 1), (14, .5)])
            if tier == 'impact':
                cam[f, 3] += .10 * h['mul'] * min(1, lt / .05) * math.exp(-max(0, lt - .06) / .45)
                if lt < 3 / FPS: cam[f, 4] = 7 * h['mul']
                if lt < 1.5 / FPS: cam[f, 5] = .22
        if tier == 'impact': cues.append(dict(t=h['out'], name='impact', gain=-10))
        elif h.get('manual'): cues.append(dict(t=h['out'], name='hit', gain=-14))
    # budget: visible shake (> 3 px) at most 5 % of a long video, 10 % of a Short
    cap = P.get('shake_budget', .05 if total > 120 else .10)
    mag = np.hypot(cam[:, 0], cam[:, 1]); share = float((mag > 3).mean())
    if share > cap:
        k = cap / share; cam[:, :3] *= k ** .5
    cam[:, :2] *= unit
    stats = dict(shake_share=round(float((np.hypot(cam[:, 0], cam[:, 1]) > 3 * unit).mean()) * 100, 1),
                 impacts=sum(1 for h in hits if h['tier'] == 'impact'), shakes=sum(1 for h in hits if h['tier'] == 'shake'))
    return [[round(float(v), 2) for v in row] for row in cam], cues, stats

# ---------------------------------------------------------------- build
def build(plan_path, frames=True):
    P = runpy.run_path(plan_path)['PLAN']
    name, size = P['name'], P.get('size', '16x9'); W, H = (1920, 1080) if size == '16x9' else (1080, 1920)
    unit = W / 1920 if size == '16x9' else W / 1080
    panes = panes_16x9 if size == '16x9' else panes_9x16
    CLIPS.update(P.get('clips', {}))
    shots, caps, gfx, sfx, music, need, clip_need, fxa = [], [], [], [], [], set(), {}, []
    pairs = []
    t = 0.0
    prev_layout, alt = None, False
    global VF, CAM_GRADE
    VF = VFACE[P.get('vface', 'high')]
    CAM_GRADE = dict(P.get('cam_grade', CFG.get('cam_grade')) or {})
    PUNCH = {'face': [1504, 276, 329, 615], 'v_face': VF['punch']}   # ~1.18x tighter, same aspect, same face centre
    for i, s in enumerate(P['shots']):
        # jump cuts between two shots of the same face layout alternate between normal and punched-in framing
        L = s.get('layout')
        if L in PUNCH and L == prev_layout and P.get('auto_punch', True) and 'camrect' not in s and 'freeze' not in s:
            alt = not alt
        elif 'freeze' not in s:
            alt = False
        prev_layout = L
        if alt: s = dict(s, camrect=PUNCH[L])
        frz = 'freeze' in s
        if not frz and s['out'] > SRC_DUR - .05: raise SystemExit(f"shot {i} ends at {s['out']}s, past the end of the source ({SRC_DUR:.2f}s)")
        src0 = s['freeze'] if frz else s['in']; sp = s.get('speed', 1.0)
        dur = s['dur'] if frz else (s['out'] - s['in']) / abs(sp)
        dur = round(dur * FPS) / FPS
        pn = panes(s)
        if FT and P.get('face_track', True) and s.get('track', True):   # webcam crops follow his face (tools/face_track.py)
            for p_ in pn:
                if p_.get('trackable') and p_.get('src') in (None, 'frame'):
                    p_['trk'] = face_offsets(p_, src0, sp, dur, frz, P.get('face_ref_ey', FT['med_ey']))
        if s.get('main_hold') is not None:   # freeze the first (screen) pane on one source frame while the cam keeps playing
            pn[0]['hold'] = s['main_hold']; need.add(max(1, int(math.floor(s['main_hold'] * FPS + .5))))
        bg = s.get('bg', 'blue'); bg = dict(type=bg) if isinstance(bg, str) else bg
        if bg.get('type') == 'blur' and 'rect' not in bg: bg['rect'] = SCR
        fx = dict(s.get('fx', {}))
        if frz: fx.setdefault('freeze', True)
        sh = dict(t0=round(t, 4), t1=round(t + dur, 4), src0=src0, speed=0 if frz else sp, freeze=frz, panes=pn, fx=fx, bg=bg, layout=s.get('layout'))
        shots.append(sh); pairs.append((sh, s))
        uses_frame = any((p.get('src') or 'frame') == 'frame' for p in pn) or bg.get('type') == 'blur'
        nfr = int(round(dur * FPS))
        for f in range(nfr + 3):            # a little past the end: float rounding can put one more frame inside the shot
            st = src0 if frz else src0 + (f / FPS) * sp
            if uses_frame and st * FPS < SRC_DUR * FPS - 1: need.add(max(1, int(math.floor(st * FPS + .5))))
        for p in pn:
            src = p.get('src') or 'frame'
            if src.startswith('clip:'):
                c = src[5:]; c0 = p.get('clip0', 0.0)
                for f in range(nfr + 3): clip_need.setdefault(c, set()).add(max(1, int(math.floor((c0 + f / FPS) * FPS + .5))))
        def ot(src_t, _t=t, _src0=src0, _sp=sp, _frz=frz):
            if isinstance(src_t, tuple): return _t + src_t[1]
            return _t if _frz else _t + (src_t - _src0) / _sp
        # captions
        cl = s.get('caps', [])
        for j, c in enumerate(cl):
            ct, text = c[0], c[1]; opt = c[2] if len(c) > 2 else {}
            t0 = max(t, ot(ct))
            end = opt.get('end')
            if end is not None: t1 = ot(end)
            elif j + 1 < len(cl): t1 = ot(cl[j + 1][0])
            else: t1 = t + dur
            t1 = min(t + dur, t1)
            words = parse_words(text)
            # Shorts: words appear across the spoken span (karaoke build). Long-form: a fast cascade so the line reads as one slam.
            reveal = opt.get('reveal', P.get('cap_reveal', 'speech' if size == '9x16' else 'fast'))
            if reveal == 'speech' and not isinstance(ct, tuple) and not frz:
                se = speech_span(ct, ct + (t1 - t0) * sp)
                span = max(.12 * (len(words) - 1), min((se - ct) / sp * .85, (t1 - t0) * .7))
            else: span = .07 * (len(words) - 1)
            for k, w in enumerate(words): w['t'] = round(t0 + (span * k / max(1, len(words) - 1) if len(words) > 1 else 0), 4)
            cap = dict(t0=round(t0, 4), t1=round(t1, 4), words=words)
            for kk in ('y', 'size', 'dx', 'align', 'x', 'maxW'):
                if kk in opt: cap[kk] = opt[kk]
            caps.append(cap)
            for w in words:
                if w.get('key'): sfx.append(dict(t=w['t'], name='pop', gain=-22 if w['key'] == 'mint' else -20))
        for g in s.get('gfx', []):
            g = dict(g)   # timing: dt (seconds into the shot) | src (source second) | at as a number (source second); a list 'at' is a position
            if 'dt' in g: g0 = t + g.pop('dt')
            elif 'src' in g: g0 = ot(g.pop('src'))
            elif isinstance(g.get('at'), (int, float)): g0 = ot(g.pop('at'))
            else: g0 = t
            d = g.pop('dur', None); g['t0'] = round(g0, 4); g['t1'] = round(g0 + d if d else t + dur, 4)
            if g['type'] == 'level': g['t'] = g['t0']
            if g['type'] in ('level', 'endcard', 'black'): g.setdefault('layer', 'top')
            for st in g.get('steps', []):
                if 'at_src' in st: st['at'] = round(ot(st.pop('at_src')), 4)
                if 'from_src' in st: st['from'] = round(ot(st.pop('from_src')), 4)
            gfx.append(g); auto_sfx(g, sfx)
        for e in s.get('sfx', []):
            at, nm = e[0], e[1]; gain = e[2] if len(e) > 2 else -12
            sfx.append(dict(t=ot(at), name=nm, gain=gain))
        for e in s.get('echo', []):
            fxa.append(dict(kind='echo', t0=ot(e[0]), t1=ot(e[1]), src0=e[0], src1=e[1], **(e[2] if len(e) > 2 else {})))
        for e in s.get('verb', []):
            fxa.append(dict(kind='verb', t0=ot(e[0]), t1=ot(e[1]), wet=e[2] if len(e) > 2 else .35))
        for e in s.get('tel', []):
            fxa.append(dict(kind='tel', t0=ot(e[0]), t1=ot(e[1])))
        for e in s.get('bleep', []):
            fxa.append(dict(kind='bleep', t0=ot(e[0]), t1=ot(e[1])))
        for e in s.get('silence', []):      # mute the voice inside a shot (picture keeps running), no bleep tone
            fxa.append(dict(kind='mute', t0=ot(e[0]), t1=ot(e[1])))
        if s.get('music'):
            mm = s['music']; music.append(dict(t=t, state=mm) if isinstance(mm, str) else dict(t=t + mm[2].get('dt', 0) if len(mm) > 2 else t, state=mm[0], **(mm[1] if len(mm) > 1 and isinstance(mm[1], dict) else {})))
        if frz and not fx.get('nosfx'): sfx.append(dict(t=t - (.15 if fx.get('freezeColor') == 'red' else 0), name='scratch' if fx.get('freezeColor') == 'red' else 'shutter', gain=-10))
        if fx.get('whip'): sfx.append(dict(t=t, name='whoosh', gain=-12))
        if fx.get('glitch'): sfx.append(dict(t=t, name='glitch', gain=-14))
        if fx.get('flash'): sfx.append(dict(t=t, name='hit', gain=-12))
        t += dur
    total = round(t, 4)

    def mark(m):
        if isinstance(m, (int, float)): return m if m >= 0 else total + m
        if m == 'start': return 0.0
        if m == 'end': return total
        if isinstance(m, (list, tuple)) and m[0] == 'shot':
            s = shots[m[1]]; return s['t1'] if len(m) > 2 and m[2] == 'end' else s['t0']
        if isinstance(m, (list, tuple)) and m[0] == 'src':   # first output time showing source second m[1]
            for s in shots:
                if not s['freeze'] and s['speed'] > 0 and s['src0'] <= m[1] <= s['src0'] + (s['t1'] - s['t0']) * s['speed']:
                    return round(s['t0'] + (m[1] - s['src0']) / s['speed'], 4)
            raise SystemExit('source time %.2f is not in the cut' % m[1])
        raise SystemExit('bad marker %r' % (m,))
    for g in P.get('gfx', []):
        g = dict(g)
        if 't' in g: g['t'] = mark(g['t'])
        g['t0'] = mark(g.get('t0', g.get('t', 0))); g['t1'] = mark(g.get('t1', 'end'))
        if g['type'] == 'level': g.setdefault('t', g['t0']); g['t0'] = g['t'] - .3; g['t1'] = g['t'] + g.get('hold', 1.25) + .35
        if g['type'] in ('level', 'endcard', 'black'): g.setdefault('layer', 'top')   # full-frame cards sit above captions
        gfx.append(g); auto_sfx(g, sfx)
    for m in P.get('music', []):
        music.append(dict(t=mark(m[0]) + (m[2].get('dt', 0) if len(m) > 2 else 0), state=m[1], **{k: v for k, v in (m[2] if len(m) > 2 else {}).items() if k != 'dt'}))
    music.sort(key=lambda m: m['t'])
    # resolve track cues: track=<slug> -> file; hit=<out time> lines the track's drop up with that moment
    scan = json.load(open(os.path.join(ROOT, 'music', 'scan.json'))) if os.path.exists(os.path.join(ROOT, 'music', 'scan.json')) else {}
    for m in music:
        if m.get('track'):
            info = scan[m['track']]; m['file'] = info['wav']
            if 'hit' in m:
                hit = mark(m.pop('hit'))
                drop = m.pop('drop_t', info['drops'][m.pop('drop', 0)][0])
                m['at'] = round(drop - (hit - m['t']), 3)
                if m['at'] < 0: print(f"warning: {m['track']} would need to start {-m['at']:.2f}s before its cue; starting at 0"); m['at'] = 0.0
    for e in P.get('sfx', []): sfx.append(dict(t=mark(e[0]) + (e[3] if len(e) > 3 else 0), name=e[1], gain=e[2] if len(e) > 2 else -12))

    cam, cues, stats = camera_track(pairs, P, total, unit)
    sfx += cues
    assets = {k: '/assets/' + os.path.basename(v) for k, v in P.get('assets', {}).items()}
    edit = dict(name=name, w=W, h=H, fps=FPS, dur=total, shots=shots, caps=caps, gfx=gfx, cam=cam, assets=assets,
                fadeIn=P.get('fadeIn', 0), fadeOut=P.get('fadeOut', 0))
    if P.get('capBox'): edit['capBox'] = P['capBox']
    os.makedirs(os.path.join(ROOT, 'edits'), exist_ok=True)
    json.dump(edit, open(os.path.join(ROOT, 'edits', name + '.json'), 'w'), separators=(',', ':'))
    audio = dict(name=name, dur=total,
                 shots=[dict(t0=sh['t0'], t1=sh['t1'], src0=sh['src0'], speed=sh['speed'], freeze=sh['freeze'], vol=s.get('vol', 1.0), duck=s.get('duck'),
                             media=s.get('media') if s.get('media_audio') else None, clip0=s.get('clip0', 0.0), mvol=s.get('mvol', 1.0), mute=s.get('mute', False))
                        for sh, s in pairs],
                 sfx=sorted(sfx, key=lambda e: e['t']), music=music, fx=fxa, music_gain=P.get('music_gain', 1.0),
                 clips={k: v.get('wav') for k, v in CLIPS.items()})
    json.dump(audio, open(os.path.join(ROOT, 'edits', name + '.audio.json'), 'w'), indent=0)
    # copy assets next to the page
    for k, v in P.get('assets', {}).items():
        dst = os.path.join(ROOT, 'assets', os.path.basename(v))
        if not os.path.exists(dst):
            import shutil; shutil.copy(v, dst)
    print(f'{name}: {len(shots)} shots, {total:.2f}s ({int(total // 60)}:{total % 60:05.2f}), {len(caps)} captions, {len(gfx)} gfx, '
          f'{len(need)} source frames, shake {stats}')
    if frames:
        extract(sorted(need))
        for c, nd in clip_need.items():
            # never ask for frames past the clip's own end (the +3-frame safety margin broke on a clip as long as its shot);
            # the renderer falls back to the nearest frame, so a shot slightly longer than its clip holds the last frame
            cdur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', CLIPS[c]['path']],
                                        capture_output=True, text=True).stdout or 0)
            last = max(1, int(cdur * FPS) - 1) if cdur else None
            extract(sorted(n for n in nd if last is None or n <= last), CLIPS[c]['path'], os.path.join(ROOT, 'cache', 'clips', c))
        for c in clip_need:
            wav = CLIPS[c].get('wav')
            if wav and not os.path.exists(wav):
                subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', CLIPS[c]['path'], '-vn', '-ac', '2', '-ar', '48000', '-c:a', 'pcm_f32le', wav], check=True)
    return edit

def auto_sfx(g, sfx):
    t0 = g['t0']; ty = g['type']
    if ty == 'level': t = g.get('t', t0); sfx += [dict(t=t - .3, name='whoosh', gain=-8), dict(t=t + .02, name='slam', gain=-9)]
    elif ty == 'quest': sfx += [dict(t=t0, name='whoosh_s', gain=-18)] + [dict(t=s['at'], name='fail' if s.get('state') == 'fail' else 'ding', gain=-14 if s.get('state') == 'fail' else -16) for s in g.get('steps', []) if s.get('at') is not None]
    elif ty == 'stamp': sfx.append(dict(t=t0, name='stamp', gain=-8))
    elif ty == 'meter': sfx.append(dict(t=t0 + .3, name='ticks', gain=-20, dur=g.get('roll', .8)))
    elif ty == 'chip' or ty == 'label': sfx.append(dict(t=t0, name='pop', gain=-20))
    elif ty == 'lower3': sfx.append(dict(t=t0, name='whoosh_s', gain=-16))
    elif ty == 'circle': sfx.append(dict(t=t0, name='marker', gain=-18))
    elif ty == 'arrow': sfx.append(dict(t=t0, name='whoosh_s', gain=-20))
    elif ty == 'typecard': sfx += [dict(t=t0, name='pop', gain=-16), dict(t=t0 + .35, name='typing', gain=-20, dur=min(g['t1'] - t0 - .4, len(g['text']) / g.get('cps', 45)))]
    elif ty == 'vs': sfx.append(dict(t=t0, name='slam', gain=-10))
    elif ty == 'endcard': sfx += [dict(t=t0 + .1, name='impact', gain=-10)]
    elif ty == 'hook': sfx.append(dict(t=t0, name='pop', gain=-18))

def extract(need, src=SRC, out=None):
    out = out or os.path.join(ROOT, 'cache', 'frames'); os.makedirs(out, exist_ok=True)
    have = set(int(f[:-4]) for f in os.listdir(out) if f.endswith('.jpg'))
    miss = [n for n in need if n not in have]
    if not miss: print('frames: all cached'); return
    runs, a = [], miss[0]; b = a
    for n in miss[1:]:
        if n <= b + 15: b = n
        else: runs.append((a, b)); a = b = n
    runs.append((a, b))
    print(f'frames: extracting {len(miss)} in {len(runs)} runs')
    for a, b in runs:
        ss = a / FPS; cnt = b - a + 1
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-ss', f'{ss:.4f}', '-i', src, '-vf', 'fps=30', '-frames:v', str(cnt),
               '-q:v', '2', '-start_number', str(a), os.path.join(out, '%d.jpg')]
        subprocess.run(cmd, check=True)

if __name__ == '__main__':
    build(sys.argv[1], frames='--no-frames' not in sys.argv)
