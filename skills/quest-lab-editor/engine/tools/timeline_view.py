"""One picture of a source range for a cut decision: a filmstrip, the waveform with the silence threshold, and the words on a time axis.
Use it only at decision points (an ambiguous pause, which retake to keep, exactly where to cut) - not for scanning.

usage: timeline_view.py <video> <audio.wav> <transcript.json|-> <from mm:ss> <to mm:ss> <out.png> [--frames 8] [--rect x,y,w,h]
  --rect crops the filmstrip to a source rect (e.g. the webcam 1474,156,388,765) so faces and mouths are readable.
Idea from browser-use/video-use (MIT): text first, pictures only where a decision needs them.
"""
import json, os, subprocess, sys, tempfile
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding='utf-8')


def ts(x):
    if ':' in x:
        m, s = x.split(':'); return int(m) * 60 + float(s)
    return float(x)


def font(sz):
    for p in (r'C:\Windows\Fonts\Nirmala.ttc', r'C:\Windows\Fonts\arial.ttf'):  # Nirmala UI covers Devanagari + Latin
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def main():
    a = sys.argv[1:]
    vid, wav, tj, t0, t1, out = a[0], a[1], a[2], ts(a[3]), ts(a[4]), a[5]
    nf = int(a[a.index('--frames') + 1]) if '--frames' in a else 8
    rect = [int(v) for v in a[a.index('--rect') + 1].split(',')] if '--rect' in a else None
    W = 1600; fw = W // nf
    tmp = tempfile.mkdtemp()
    strip = []
    for i in range(nf):
        t = t0 + (t1 - t0) * (i + .5) / nf
        p = os.path.join(tmp, f'{i}.png')
        vf = (f'crop={rect[2]}:{rect[3]}:{rect[0]}:{rect[1]},' if rect else '') + f'scale={fw}:-2'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', vid, '-frames:v', '1', '-vf', vf, p], check=True)
        strip.append((t, Image.open(p).convert('RGB')))
    fh = max(im.height for _, im in strip)
    WH, AX = 220, 120
    img = Image.new('RGB', (W, fh + WH + AX + 30), (16, 18, 24))
    d = ImageDraw.Draw(img); f12, f14 = font(12), font(14)
    X = lambda t: int((t - t0) / (t1 - t0) * W)
    for i, (t, im) in enumerate(strip):
        img.paste(im, (i * fw, 0)); d.text((i * fw + 4, 4), f'{t:.2f}', fill='yellow', font=f12)
    with sf.SoundFile(wav) as f:
        sr = f.samplerate; f.seek(int(t0 * sr)); x = f.read(int((t1 - t0) * sr), dtype='float32', always_2d=True).mean(1)
    hop = max(1, len(x) // W)
    env = np.array([np.abs(x[i * hop:(i + 1) * hop]).max() if len(x[i * hop:(i + 1) * hop]) else 0 for i in range(W)])
    rms = np.array([np.sqrt(np.mean(x[i:i + int(.03 * sr)] ** 2) + 1e-12) for i in range(0, max(1, len(x) - int(.03 * sr)), int(.01 * sr))])
    db = 20 * np.log10(rms + 1e-9)
    blocks = [20 * np.log10(np.sqrt(np.mean(rms[i:i + 50] ** 2)) + 1e-9) for i in range(0, max(1, len(rms) - 50), 10)]
    blocks = np.array(blocks); live = blocks[blocks > -65]
    F = float(np.percentile(live if len(live) > 20 else blocks, 10)); thr = F + 6
    y0 = fh + 10; mid = y0 + WH // 2
    # silence shading (below F + 6 dB)
    for i, v in enumerate(db):
        if v < thr:
            xx = X(t0 + i * .01)
            d.line([xx, y0, xx, y0 + WH], fill=(40, 44, 58))
    peak = max(env.max(), 1e-4)
    for i, v in enumerate(env):
        hgt = int(v / peak * (WH // 2 - 4))
        d.line([i, mid - hgt, i, mid + hgt], fill=(66, 130, 240))
    d.text((4, y0 + 2), f'floor {F:.0f} dB · grey = below {thr:.0f} dB (cuttable silence)', fill=(170, 170, 170), font=f12)
    # time axis
    ya = y0 + WH + 4
    step = .5 if t1 - t0 <= 12 else (1 if t1 - t0 <= 30 else 5)
    t = np.ceil(t0 / step) * step
    while t <= t1:
        d.line([X(t), ya, X(t), ya + 6], fill='white'); d.text((X(t) + 2, ya + 6), f'{t:.1f}', fill=(200, 200, 200), font=f12); t += step
    # words
    if tj != '-':
        T = json.load(open(tj, encoding='utf-8')); row = 0; lastx = -999
        for seg in T['segments']:
            for w in seg.get('words') or []:
                if t0 <= w['s'] <= t1:
                    x0, x1 = X(w['s']), X(min(w['e'], t1))
                    row = row + 1 if x0 < lastx + 4 else 0
                    yy = ya + 26 + (row % 4) * 22
                    col = (255, 210, 63) if w['e'] - w['s'] > 1.0 else ((255, 74, 61) if w.get('p', 1) < .35 else (18, 234, 187))
                    d.rectangle([x0, yy, max(x0 + 2, x1), yy + 3], fill=col)
                    d.text((x0, yy + 4), w['w'].strip(), fill=col, font=f14)
                    lastx = x0 + int(d.textlength(w['w'].strip(), font=f14))
        d.text((W - 520, fh + WH + AX + 12), 'mint = word · yellow = stretched > 1 s (hidden pause) · red = low confidence', fill=(150, 150, 150), font=f12)
    img.save(out)
    print(out, img.size)


if __name__ == '__main__':
    main()
