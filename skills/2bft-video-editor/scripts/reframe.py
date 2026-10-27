"""reframe.py - face-tracked auto reframe. Turns any video (or one region of it, such as the webcam box of a
stream layout) into a vertical 9:16 (or any aspect) video whose crop follows the speaker's face like a camera
operator: smooth, with a deadzone, never jittery.

usage:
  python -I reframe.py <in.mp4> <out.mp4> [--region x,y,w,h] [--aspect 9:16] [--zoom 1.0]
                       [--size 1080x1920] [--start S] [--dur S] [--track-fps 10] [--eyes 0.40]
                       [--compare] [--track-json track.json] [--no-audio]

  --region    part of the source frame to work in (source pixels). Default: the whole frame.
  --aspect    output aspect, default 9:16.
  --zoom      1.0 = the largest crop of that aspect that fits the region; 1.5 = a 1.5x closer shot.
  --eyes      where the eye line sits in the output, as a fraction of the height (0.40 = a little above centre).
  --compare   write a side-by-side: a static centre crop on the left, the face-tracked crop on the right.
  --track-json  also save the smoothed face track (source pixels) for other tools.

Needs: ffmpeg/ffprobe on PATH; Python with numpy and OpenCV >= 4.8 (cv2.FaceDetectorYN).
Face model: face_detection_yunet_2023mar.onnx from the OpenCV model zoo (MIT). Point REFRAME_YUNET (or
--model) at it; by default it looks in ./models/.

How the camera moves (all numbers are starting values, change them in SMOOTH below):
  detect at --track-fps -> keep the most confident, largest face -> fill gaps up to 2 s -> median of 5 against
  false hits -> Gaussian 0.25 s -> deadzone (the crop holds still until the face moves more than 4% of the
  crop width) -> Gaussian 0.3 s. If no face is ever found, the crop stays centred.
"""
import json, os, subprocess, sys
import numpy as np
import cv2

SMOOTH = dict(fill_gap_s=2.0, median=5, sigma1_s=0.25, deadzone=0.04, sigma2_s=0.30)


def arg(a, name, default=None, cast=str):
    return cast(a[a.index(name) + 1]) if name in a else default


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height,r_frame_rate:format=duration', '-of', 'json', path],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out); s = j['streams'][0]
    num, den = s['r_frame_rate'].split('/')
    return int(s['width']), int(s['height']), float(num) / float(den), float(j['format']['duration'])


def has_audio(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index',
                          '-of', 'csv=p=0', path], capture_output=True, text=True).stdout
    return bool(out.strip())


def read_exact(f, k):
    buf = bytearray()
    while len(buf) < k:
        c = f.read(k - len(buf))
        if not c:
            break
        buf += c
    return bytes(buf)


def frames(path, start, dur, region, fps=None):
    """Yield BGR frames of the region. Decodes in 60 s chunks so a byte slip can never roll later frames."""
    x, y, w, h = region
    n = w * h * 3
    t, end = start, start + dur
    while t < end - 1e-3:
        span = min(60.0, end - t)
        vf = (f'fps={fps},' if fps else '') + f'crop={w}:{h}:{x}:{y},format=bgr24'
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-t', f'{span:.3f}', '-i', path,
                              '-vf', vf, '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
        while True:
            b = read_exact(p.stdout, n)
            if len(b) < n:
                break
            yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
        p.wait()
        t += span


def gauss(v, sigma):
    if sigma <= 0 or len(v) < 3:
        return v
    r = int(3 * sigma) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    return np.convolve(np.pad(v, r, mode='edge'), k, mode='valid')


def median(v, size):
    if len(v) < size:
        return v
    r = size // 2
    p = np.pad(v, r, mode='edge')
    return np.array([np.median(p[i:i + size]) for i in range(len(v))])


def fill(v, max_gap):
    """Linear fill of NaN gaps up to max_gap samples; longer gaps hold the last good value."""
    v = v.copy(); ok = ~np.isnan(v)
    if not ok.any():
        return None
    idx = np.arange(len(v))
    v[~ok] = np.interp(idx[~ok], idx[ok], v[ok])
    return v


def deadzone(v, dz):
    out = v.copy(); hold = v[0]
    for i, x in enumerate(v):
        if abs(x - hold) > dz:
            hold = x - np.sign(x - hold) * dz
        out[i] = hold
    return out


def track(path, start, dur, region, tfps, model):
    x0, y0, w, h = region
    det = cv2.FaceDetectorYN.create(model, '', (w, h), 0.6, 0.3, 5)
    cx, ey, fw = [], [], []
    for img in frames(path, start, dur, region, fps=tfps):
        _, faces = det.detect(img)
        if faces is not None and len(faces):
            f = max(faces, key=lambda r: r[14] * r[2] * r[3])   # confident and large beats a poster face
            bx, by, bw, bh = f[:4]
            cx.append(bx + bw / 2); ey.append((f[5] + f[7]) / 2); fw.append(float(bw))
        else:
            cx.append(np.nan); ey.append(np.nan); fw.append(np.nan)
    cx, ey, fw = map(lambda a: np.array(a, float), (cx, ey, fw))
    hit = float(np.mean(~np.isnan(cx))) if len(cx) else 0.0
    return cx, ey, fw, hit


def smooth(v, tfps, dz_px):
    v = fill(v, SMOOTH['fill_gap_s'] * tfps)
    if v is None:
        return None
    v = median(v, SMOOTH['median'])
    v = gauss(v, SMOOTH['sigma1_s'] * tfps)
    v = deadzone(v, dz_px)
    return gauss(v, SMOOTH['sigma2_s'] * tfps)


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] in ('-h', '--help'):
        print(__doc__); return
    src, out = a[0], a[1]
    W, H, fps, total = probe(src)
    region = [int(v) for v in arg(a, '--region', f'0,0,{W},{H}').split(',')]
    aw, ah = [float(v) for v in arg(a, '--aspect', '9:16').split(':')]
    zoom = arg(a, '--zoom', 1.0, float)
    ow, oh = [int(v) for v in arg(a, '--size', '1080x1920').split('x')]
    start = arg(a, '--start', 0.0, float)
    dur = arg(a, '--dur', total - start, float)
    tfps = arg(a, '--track-fps', 10.0, float)
    eyes = arg(a, '--eyes', 0.40, float)
    model = arg(a, '--model', os.environ.get('REFRAME_YUNET', os.path.join('models', 'face_detection_yunet_2023mar.onnx')))
    if not os.path.exists(model):
        sys.exit(f'face model not found: {model}  (download face_detection_yunet_2023mar.onnx, set REFRAME_YUNET)')

    rx, ry, rw, rh = region
    ch = min(rh, rw * ah / aw) / zoom            # crop size inside the region
    cw = ch * aw / ah
    cw, ch = int(round(cw)) // 2 * 2, int(round(ch)) // 2 * 2

    cx, ey, fw, hit = track(src, start, dur, region, tfps, model)
    print(f'face found in {hit * 100:.0f}% of {len(cx)} samples', file=sys.stderr)
    sx = smooth(cx, tfps, SMOOTH['deadzone'] * cw)
    sy = smooth(ey, tfps, SMOOTH['deadzone'] * cw)
    if sx is None:
        print('no face found: crop stays centred', file=sys.stderr)
        sx = np.full(max(len(cx), 1), rw / 2); sy = np.full(max(len(cx), 1), rh * 0.4)
    tt = np.arange(len(sx)) / tfps

    if '--track-json' in a:
        json.dump({'fps': tfps, 'start': start, 'region': region, 'hit': hit,
                   'cx': [round(float(v) + rx, 1) for v in sx], 'ey': [round(float(v) + ry, 1) for v in sy]},
                  open(arg(a, '--track-json'), 'w'))

    compare = '--compare' in a
    fw_out = ow * 2 if compare else ow
    audio = has_audio(src) and '--no-audio' not in a
    enc = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{fw_out}x{oh}',
           '-r', f'{fps:.6f}', '-i', '-']
    if audio:
        enc += ['-ss', f'{start:.3f}', '-t', f'{dur:.3f}', '-i', src, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k']
    enc += ['-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-color_range', 'tv',
            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', '-shortest', out]
    p = subprocess.Popen(enc, stdin=subprocess.PIPE)

    static_x, static_y = (rw - cw) / 2, (rh - ch) / 2
    n = 0
    for img in frames(src, start, dur, region):
        t = n / fps
        fx = float(np.interp(t, tt, sx)); fy = float(np.interp(t, tt, sy))
        x = int(round(np.clip(fx - cw / 2, 0, rw - cw)))
        y = int(round(np.clip(fy - eyes * ch, 0, rh - ch)))
        crop = cv2.resize(img[y:y + ch, x:x + cw], (ow, oh), interpolation=cv2.INTER_LANCZOS4)
        if compare:
            sxp, syp = int(static_x), int(static_y)
            left = cv2.resize(img[syp:syp + ch, sxp:sxp + cw], (ow, oh), interpolation=cv2.INTER_LANCZOS4)
            crop = np.hstack([left, crop])
        p.stdin.write(crop.tobytes()); n += 1
    p.stdin.close(); p.wait()
    print(f'wrote {out}: {n} frames, crop {cw}x{ch} of region {rw}x{rh}, zoom {zoom}', file=sys.stderr)


if __name__ == '__main__':
    main()
