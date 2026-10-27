"""Track his face inside the webcam rect for the whole recording, so every webcam crop can follow him when he leans, stands or moves.

usage (any python with OpenCV >= 4.8, which has FaceDetectorYN, plus numpy and scipy):  [--to SECONDS] limits the run (tests)
  <python with opencv> -I tools\\face_track.py <video> <out.json> [--cam x,y,w,h] [--fps 10]
  --cam defaults to source.json "cam" when run from the project folder.
Model: face_detection_yunet_2023mar.onnx from the OpenCV model zoo (MIT). Download it yourself and point QL_YUNET at it.
Output (source pixels): fps, cam, cx, cy (face box centre), ey (eye line), fw (face width), med_cx/med_ey (his usual seated position),
hit (fraction of samples with a face). build.py turns the DEVIATION from the usual position into a per-frame offset of each webcam crop,
so the hand-made crop presets keep their composition when he sits normally and only move when he moves.
Smoothing ("camera operator", not a jittery tracker): fill gaps <= 2 s, median-5 against false hits, Gaussian 0.25 s,
a 10 px deadzone hold, Gaussian 0.3 s again. Cuts are handled by the renderer (each shot reads the track at its own source times).
"""
import json, os, subprocess, sys
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter1d, median_filter
MODEL = os.environ.get('QL_YUNET', os.path.join('models', 'face_detection_yunet_2023mar.onnx'))


def main():
    a = sys.argv[1:]
    vid, out = a[0], a[1]
    fps = float(a[a.index('--fps') + 1]) if '--fps' in a else 10.0
    to = ['-t', a[a.index('--to') + 1]] if '--to' in a else []
    if '--cam' in a:
        cam = [int(v) for v in a[a.index('--cam') + 1].split(',')]
    else:
        cam = json.load(open('source.json'))['cam']
    x0, y0, w, h = cam
    det = cv2.FaceDetectorYN.create(MODEL, '', (w, h), 0.6, 0.3, 5)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', vid], capture_output=True, text=True).stdout)
    if to: dur = min(dur, float(to[1]))
    n = w * h * 3
    cx, cy, ey, fw = [], [], [], []

    def read_exact(f, k):
        buf = bytearray()
        while len(buf) < k:
            c = f.read(k - len(buf))
            if not c: break
            buf += c
        return bytes(buf)
    # decode in 60 s chunks: a one-off byte slip in a 15-minute pipe rolled every later frame vertically (seen 27 Oct) -
    # chunks bound any slip, and each chunk must deliver exactly its frame count
    CH = 60.0; s0 = 0.0
    while s0 < dur - 1e-3:
        span = min(CH, dur - s0); want = int(round(span * fps))
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{s0:.3f}', '-t', f'{span:.3f}', '-i', vid,
                              '-vf', f'fps={fps},crop={w}:{h}:{x0}:{y0},format=bgr24', '-frames:v', str(want), '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
        got = 0
        while got < want:
            b = read_exact(p.stdout, n)
            if len(b) < n: break
            img = np.frombuffer(b, np.uint8).reshape(h, w, 3); got += 1
            _, faces = det.detect(img)
            if faces is not None and len(faces):
                f = max(faces, key=lambda r: r[14] * r[2] * r[3])       # most confident, largest (posters have smaller faces)
                bx, by, bw, bh = f[:4]; rex, rey, lex, ley = f[4:8]
                cx.append(x0 + bx + bw / 2); cy.append(y0 + by + bh / 2); ey.append(y0 + (rey + ley) / 2); fw.append(float(bw))
            else:
                cx.append(np.nan); cy.append(np.nan); ey.append(np.nan); fw.append(np.nan)
        p.stdout.close(); p.wait()
        for _ in range(want - got):            # keep the time base exact even if a chunk came up short
            cx.append(np.nan); cy.append(np.nan); ey.append(np.nan); fw.append(np.nan)
        s0 += span
    arr = {k: np.array(v, float) for k, v in dict(cx=cx, cy=cy, ey=ey, fw=fw).items()}
    raw_ey = [None if np.isnan(x) else round(float(x), 1) for x in arr['ey']]
    N = len(cx); hit = float(np.mean(~np.isnan(arr['cx']))) if N else 0
    t = np.arange(N) / fps
    for k, v in arr.items():
        good = ~np.isnan(v)
        if good.sum() < 2: continue
        filled = np.interp(t, t[good], v[good])
        # gaps longer than 2 s: hold the last good value instead of sliding across the gap
        last = None; run = 0
        for i in range(N):
            if good[i]: last = filled[i]; run = 0
            else:
                run += 1
                if run > 2 * fps and last is not None: filled[i] = last
        v = median_filter(filled, size=5, mode='nearest')
        v = gaussian_filter1d(v, .25 * fps, mode='nearest')
        if k in ('cx', 'cy', 'ey'):          # deadzone hold, then ease
            held = v.copy(); cur = v[0]
            for i in range(N):
                if abs(v[i] - cur) > 10: cur = v[i] - np.sign(v[i] - cur) * 10
                held[i] = cur
            v = gaussian_filter1d(held, .3 * fps, mode='nearest')
        arr[k] = v
    res = dict(fps=fps, cam=cam, n=N, hit=round(hit, 3), med_cx=float(np.median(arr['cx'])), med_ey=float(np.median(arr['ey'])),
               med_fw=float(np.median(arr['fw'])), raw_ey=raw_ey, **{k: [round(float(x), 1) for x in v] for k, v in arr.items()})
    json.dump(res, open(out, 'w'))
    dev = np.array(res['ey']) - res['med_ey']
    print(f"{out}: {N} samples @ {fps} fps, face found {hit:.0%}, usual eye line y {res['med_ey']:.0f}, x {res['med_cx']:.0f}; "
          f"eye line moves {dev.min():+.0f}..{dev.max():+.0f} px; |dev| > 60 px for {np.mean(np.abs(dev) > 60):.0%} of the time")


if __name__ == '__main__':
    main()
