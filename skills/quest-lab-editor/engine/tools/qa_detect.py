"""Automatic pre-delivery QC for finished exports. One decode per file; prints findings with a severity and a QC code.

usage: qa_detect.py <video.mp4> [more.mp4 ...] [--strips <dir>] [--expect SECONDS] [--short]

Severities: BLOCKER (fix before upload) · ISSUE (fix unless it is intended) · FYI (creative intent / for the ear).
Codes follow the MovieLabs QC vocabulary so notes read the same everywhere.
Checks:
  BLACK-FRAMES        blackdetect d>=0.1 s (FYI if it is the planned 2-frame blackout, ISSUE if longer than 0.5 s)
  DUPLICATE-FRAMES    freezedetect >= 2 s of identical frames (a stalled render / missing-frame fallback)
  DROPOUTS            silencedetect -50 dB >= 2 s in the final mix
  LOUDNESS            integrated -14 LUFS +-1, true peak <= -1.0 dBTP, max short-term <= -9 LUFS (EBU R128 s1 idea: +5 LU over target)
  OUT-OF-PHASE        mono fold-down loses > 3 dB vs stereo (phones sum to mono)
  EMPTY-FIRST-FRAME   frame 0 nearly flat (a Short counts a view on frame 0: it must be the hook)
  FLASH               WCAG 2.3.1 general-flash test approximated on a 64x36 luminance grid: > 3 flashes in any 1 s over > 25 % of the frame
  RED-FLASH           same with saturated red (R/(R+G+B) >= 0.8)
  STATIC              > 8 s (Short: > 4 s) with almost no change on screen
  DURATION-MISMATCH   --expect given and the file differs by > 0.1 s
  SPEC                1080p, yuv420p, bt709 tv range, 48 kHz stereo AAC, faststart
--strips <dir> writes <dir>/<name>_cuts.jpg (never into a delivery folder): every detected cut at -0.2 s / -1 frame / cut / +0.2 s (look for flash frames, half words,
captions hidden by overlays) and <dir>/<name>.cuts.txt (cut times, used by check_srt.py --cuts).
Ideas: HotClip (AGPL, ideas only), HyperFrames review.md (Apache-2.0), MovieLabs QC vocabulary, W3C WCAG 2.2 2.3.1, EBU R128 s1.
"""
import json, os, re, subprocess, sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
GW, GH = 64, 36


def probe(f):
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', f], capture_output=True, text=True).stdout)
    v = next(s for s in j['streams'] if s['codec_type'] == 'video')
    a = next((s for s in j['streams'] if s['codec_type'] == 'audio'), None)
    num, den = v['r_frame_rate'].split('/')
    return j, v, a, float(num) / float(den)


def lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def frames(f, fps):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f, '-vf', f'scale={GW}:{GH}:flags=area,format=rgb24', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    n = GW * GH * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(GH, GW, 3).astype(np.float32)
    p.wait()


def main():
    args = sys.argv[1:]
    strips = args[args.index('--strips') + 1] if '--strips' in args else None
    short_mode = '--short' in args
    expect = float(args[args.index('--expect') + 1]) if '--expect' in args else None
    files = [a for a in args if a.lower().endswith(('.mp4', '.mov', '.mkv')) and a != strips]
    worst = 0
    for f in files:
        out = []

        def add(sev, code, msg):
            out.append((sev, code, msg))
        j, v, a, fps = probe(f)
        dur = float(j['format']['duration'])
        vertical = int(v['height']) > int(v['width'])
        short = short_mode or vertical
        # ---- spec
        spec = []
        if (int(v['width']), int(v['height'])) not in ((1920, 1080), (1080, 1920)):
            spec.append(f"{v['width']}x{v['height']}")
        if v.get('pix_fmt') != 'yuv420p':
            spec.append(f"pix_fmt {v.get('pix_fmt')}")
        if v.get('color_range') not in (None, 'tv') or v.get('color_primaries') not in (None, 'bt709'):
            spec.append(f"colour {v.get('color_range')}/{v.get('color_primaries')}")
        if a is None:
            spec.append('no audio')
        else:
            if a.get('sample_rate') != '48000': spec.append(f"audio {a.get('sample_rate')} Hz")
            if a.get('channels') != 2: spec.append(f"{a.get('channels')} ch")
            br = int(a.get('bit_rate', 0) or 0)
            if br and br < 300000: add('FYI', 'SPEC', f'audio {br // 1000} kbps (YouTube recommends 384 kbps stereo AAC-LC)')
        with open(f, 'rb') as fh:
            head = fh.read(4096)
        if b'moov' not in head[:4096] and b'mdat' in head[:4096]:
            spec.append('moov atom not at front (no faststart)')
        if spec:
            add('ISSUE', 'SPEC', ', '.join(spec))
        if expect is not None and abs(dur - expect) > .1:
            add('BLOCKER', 'DURATION-MISMATCH', f'{dur:.2f}s vs plan {expect:.2f}s')
        # ---- one decode for black / freeze / silence / loudness
        r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f, '-vf', 'blackdetect=d=0.1:pix_th=0.10,freezedetect=n=-60dB:d=2',
                            '-af', 'silencedetect=noise=-50dB:d=2,ebur128=peak=true', '-f', 'null', '-'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
        small = []
        for s, e, d in re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)', r):
            s, e, d = float(s), float(e), float(d)
            edge = s < .05 or e > dur - .05
            sev = 'BLOCKER' if (s < .05 and short) else ('ISSUE' if d > .5 or edge else 'FYI')
            if sev == 'FYI':
                small.append(s); continue
            add(sev, 'BLACK-FRAMES', f'{s:.2f}-{e:.2f}s ({d:.2f}s)' + (' at the very start' if s < .05 else ''))
        if small:
            add('ISSUE' if len(small) > 3 else 'FYI', 'BLACK-FRAMES', f'{len(small)} short black runs (<= 0.5 s) at ' + ', '.join(f'{x:.2f}' for x in small[:8]) + (' ...' if len(small) > 8 else '') + ' - planned blackouts?')
        fz = re.findall(r'freeze_start: ([\d.]+)', r); fe = re.findall(r'freeze_end: ([\d.]+)', r)
        for i, s in enumerate(fz):
            e = float(fe[i]) if i < len(fe) else dur
            add('ISSUE', 'DUPLICATE-FRAMES', f'{float(s):.2f}-{e:.2f}s frozen ({e - float(s):.1f}s) - intended hold? else a stalled frame')
        ss = re.findall(r'silence_start: ([\d.]+)', r); se = re.findall(r'silence_end: ([\d.]+)', r)
        for i, s in enumerate(ss):
            e = float(se[i]) if i < len(se) else dur
            add('ISSUE', 'DROPOUTS', f'{float(s):.2f}-{e:.2f}s below -50 dB')
        I = re.findall(r'I:\s+(-?[\d.]+) LUFS', r); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)
        S = [float(x) for x in re.findall(r'S:\s*(-?[\d.]+)', r) if float(x) > -70]
        Iv = float(I[-1]) if I else None; TPv = float(TP[-1]) if TP else None; Smax = max(S) if S else None
        if Iv is not None and abs(Iv + 14) > 1: add('ISSUE', 'LOUDNESS', f'integrated {Iv:.1f} LUFS (target -14)')
        if TPv is not None and TPv > -1.0: add('BLOCKER', 'CLIPPING', f'true peak {TPv:.1f} dBTP (max -1.0)')
        if Smax is not None and Iv is not None and Smax > Iv + 5: add('ISSUE', 'LEVEL-SHIFT', f'max short-term {Smax:.1f} LUFS is {Smax - Iv:.1f} LU over integrated (keep <= +5): a boom/drop jumps out')
        # ---- mono fold
        if a is not None and a.get('channels') == 2:
            m = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f, '-vn', '-af', 'pan=mono|c0=0.5*c0+0.5*c1,ebur128', '-f', 'null', '-'],
                               capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
            Im = re.findall(r'I:\s+(-?[\d.]+) LUFS', m)
            if Im and Iv is not None:
                # identical L/R (mono voice) folds to stereo - 3.01 LU -> drop 0; fully uncorrelated stereo -> drop ~3; phase trouble -> more
                drop = Iv - float(Im[-1]) - 3.01
                if drop > 4.5: add('ISSUE', 'OUT-OF-PHASE', f'mono fold loses {drop:.1f} dB more than a mono voice would - check stereo wideners / phase')
        # ---- frame scan: first frame, flashes, static stretches, cuts
        prevY = prevR = None
        trans, rtrans, diffs, cuts = [], [], [], []
        first_std = None
        for i, fr in enumerate(frames(f, fps)):
            R, G, B = lin(fr[..., 0]), lin(fr[..., 1]), lin(fr[..., 2])
            Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
            sat_red = (fr[..., 0] / (fr.sum(-1) + 1e-6)) >= 0.8
            if i == 0:
                first_std = float(fr.std())
            if prevY is not None:
                d = Y - prevY
                dark = np.minimum(Y, prevY) < 0.80
                up = ((d >= .10) & dark).mean(); dn = ((d <= -.10) & dark).mean()
                if up > .25: trans.append((i, 1))
                elif dn > .25: trans.append((i, -1))
                rr = (sat_red ^ prevR).mean()
                if rr > .25: rtrans.append(i)
                diffs.append(float(np.abs(fr - prevF).mean()))
            prevY, prevR, prevF = Y, sat_red, fr
        if first_std is not None and first_std < 6:
            add('BLOCKER' if short else 'ISSUE', 'EMPTY-FIRST-FRAME', f'frame 0 is nearly flat (std {first_std:.1f}) - frame 0 must show the hook')

        def flash_windows(ev, label, code):
            # a flash = a pair of opposing transitions; fail when > 3 flashes (> 6 transitions) inside any 1 s window
            idx = [e[0] if isinstance(e, tuple) else e for e in ev]
            win = int(round(fps)); bad = []
            for k in range(len(idx)):
                cnt = sum(1 for x in idx[k:] if x - idx[k] < win)
                if cnt > 6:
                    bad.append(idx[k] / fps)
            if bad:
                add('BLOCKER', code, f'{label}: > 3 flashes/s over > 25 % of frame near ' + ', '.join(f'{t:.1f}s' for t in sorted(set(round(b, 1) for b in bad))[:6]))
        flash_windows(trans, 'general flash', 'FLASH')
        flash_windows(rtrans, 'saturated red', 'RED-FLASH')
        if diffs:
            dd = np.array(diffs)
            # cuts: big frame difference that is a local peak
            thr = max(12.0, np.percentile(dd, 99) * .6)
            # a cut is the strongest frame change within +-8 frames (animated transitions fire on several frames in a row)
            for i in range(1, len(dd) - 1):
                lo, hi = max(0, i - 8), min(len(dd), i + 9)
                if dd[i] > thr and dd[i] >= dd[lo:hi].max():
                    cuts.append((i + 1) / fps)
            # static stretches
            lim = 4 if short else 8
            run0 = None
            for i, x in enumerate(np.append(dd, 99)):
                if x < 0.6:
                    run0 = i if run0 is None else run0
                else:
                    if run0 is not None and (i - run0) / fps > lim:
                        add('ISSUE', 'STATIC', f'{run0 / fps:.1f}-{i / fps:.1f}s almost nothing changes ({(i - run0) / fps:.1f}s) - add a reveal, a push-in or cut it')
                    run0 = None
        # ---- report
        sev_rank = {'BLOCKER': 2, 'ISSUE': 1, 'FYI': 0}
        out.sort(key=lambda x: -sev_rank[x[0]])
        worst = max([worst] + [sev_rank[o[0]] for o in out])
        print(f"\n{os.path.basename(f)}  {dur:.2f}s  {v['width']}x{v['height']} {fps:.2f}fps  {Iv if Iv is not None else '?'} LUFS  TP {TPv if TPv is not None else '?'}  "
              f"maxS {Smax if Smax is not None else '?'}  cuts {len(cuts)}  ({len(cuts) / max(dur / 60, 1e-6):.0f}/min)")
        if not out:
            print('  clean')
        for sev, code, msg in out:
            print(f'  {sev:7s} {code:18s} {msg}')
        if strips:
            os.makedirs(strips, exist_ok=True)
            base = os.path.join(strips, os.path.splitext(os.path.basename(f))[0])
            with open(base + '.cuts.txt', 'w') as fh:
                fh.write('\n'.join(f'{c:.3f}' for c in cuts))
            make_strips(f, cuts, fps, base + '_cuts.jpg')
    sys.exit(2 if worst == 2 else 0)


def make_strips(f, cuts, fps, out_jpg, w=240, max_cuts=48):
    from PIL import Image, ImageDraw
    cuts = cuts[:max_cuts]
    if not cuts:
        return
    probe_h = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip().split(',')
    if int(probe_h[1]) > int(probe_h[0]):
        w = 150  # vertical: keep the sheet short enough to read
    want = []
    for c in cuts:
        n = int(round(c * fps))
        want += [max(0, n - int(.2 * fps)), max(0, n - 1), n, n + int(.2 * fps)]
    uniq = sorted(set(want))
    ims = {}
    h = int(round(int(probe_h[1]) * w / int(probe_h[0]) / 2) * 2)
    sz = w * h * 3
    # batches of 40 frames: one select expression for 190+ frames broke ffmpeg's parser on a 7-minute video (27 Oct)
    for b0 in range(0, len(uniq), 40):
        batch = uniq[b0:b0 + 40]
        expr = '+'.join(f'eq(n\\,{k})' for k in batch)
        p = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-vf', f"select='{expr}',scale={w}:-2,format=rgb24", '-fps_mode', 'passthrough', '-f', 'rawvideo', '-'], capture_output=True)
        if not p.stdout:
            print('  strips: ffmpeg gave no frames -', p.stderr.decode(errors='replace')[:300]); return
        for i, k in enumerate(batch):
            b = p.stdout[i * sz:(i + 1) * sz]
            if len(b) == sz:
                ims[k] = Image.frombytes('RGB', (w, h), b)
    sheet = Image.new('RGB', (4 * w, len(cuts) * (h + 2)), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for r, c in enumerate(cuts):
        n = int(round(c * fps))
        for col, k in enumerate([max(0, n - int(.2 * fps)), max(0, n - 1), n, n + int(.2 * fps)]):
            if k in ims:
                sheet.paste(ims[k], (col * w, r * (h + 2)))
        d.rectangle([0, r * (h + 2), 64, r * (h + 2) + 14], fill='black'); d.text((3, r * (h + 2) + 2), f'{c:.2f}s', fill='yellow')
    sheet.save(out_jpg, quality=82)
    print(f'  strips: {out_jpg} ({len(cuts)} cuts; columns -0.2s, -1f, cut, +0.2s)')


if __name__ == '__main__':
    main()
