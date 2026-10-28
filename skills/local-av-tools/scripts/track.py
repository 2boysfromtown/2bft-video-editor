"""Track face, body and hands in a video with Google MediaPipe (Apache-2.0), on the CPU (leaves the GPU free).

  python -I track.py talk.mp4
      -> talk_track.json: per frame face box + expressions (smile, mouth open, blink), and a summary
         (face found %, smile moments). Expressions are reliable when the face is big in frame (>~200 px tall);
         on a small webcam box inside a busy layout use --crop on the webcam region.
  ... talk.mp4 --reframe              16:9 -> 9:16 crop that follows the face (smooth camera)  -> talk_9x16.mp4
  ... talk.mp4 --reframe --aspect 4:5 (or 1:1)
  ... talk.mp4 --pose --hands --overlay   also body + hand landmarks, drawn on a preview -> talk_overlay.mp4
  ... --crop x,y,w,h                  track inside a region only (e.g. the webcam box of a stream layout)
  ... --start 60 --seconds 30

Expressions come from the face model's blendshapes (0-1): smile = mouthSmileLeft/Right, mouth_open = jawOpen,
blink = eyeBlinkLeft/Right. Use them to find laughs/reactions, punch-ins, or energy for camera shake.
"""
import argparse, json, os, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import mediapipe as mp  # noqa: E402
from mediapipe.tasks.python import BaseOptions, vision  # noqa: E402
import av_common as av  # noqa: E402

av.utf8_stdout()
MODELS = Path(os.environ.get("MEDIAPIPE_MODELS", os.path.join("models", "mediapipe")))  # face_landmarker.task, pose_landmarker_full.task, hand_landmarker.task
POSE_EDGES = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (24, 26), (26, 28),
              (0, 11), (0, 12)]
HAND_EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14),
              (14, 15), (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]


def spans(flags, fps, min_len=0.3):
    out, start = [], None
    for i, f in enumerate(list(flags) + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            if (i - start) / fps >= min_len:
                out.append([round(start / fps, 2), round(i / fps, 2)])
            start = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--pose", action="store_true")
    ap.add_argument("--hands", action="store_true")
    ap.add_argument("--no-face", action="store_true")
    ap.add_argument("--faces", type=int, default=1, help="max faces to track")
    ap.add_argument("--overlay", action="store_true", help="write a preview with landmarks drawn")
    ap.add_argument("--reframe", action="store_true", help="write a crop that follows the face")
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--follow", type=float, default=0.6, help="camera smoothing in seconds (higher = calmer)")
    ap.add_argument("--crop", help="x,y,w,h region")
    ap.add_argument("--start", type=float)
    ap.add_argument("--seconds", type=float)
    ap.add_argument("--detect-width", type=int, default=640, help="frames are shrunk to this width for tracking")
    a = ap.parse_args()

    src = Path(a.video)
    info = av.probe(src)
    W, H, fps = info["w"], info["h"], info["fps"]
    cx0 = cy0 = 0
    if a.crop:
        cx0, cy0, W, H = map(int, a.crop.split(","))

    def frames(size=None):
        it = av.read_frames(src, info["w"], info["h"], a.start, a.seconds)
        for f in it:
            f = f[cy0:cy0 + H, cx0:cx0 + W] if a.crop else f
            yield cv2.resize(f, size, interpolation=cv2.INTER_AREA) if size else f

    dw = min(a.detect_width, W)
    dh = int(round(H * dw / W / 2) * 2)
    run = vision.RunningMode.VIDEO
    face = None if a.no_face else vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODELS / "face_landmarker.task")), running_mode=run,
        num_faces=a.faces, output_face_blendshapes=True))
    pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODELS / "pose_landmarker_full.task")), running_mode=run)) if a.pose else None
    hands = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODELS / "hand_landmarker.task")), running_mode=run, num_hands=2)) if a.hands else None

    t0 = time.time()
    track = []
    for i, f in enumerate(frames((dw, dh))):
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(f))
        ms = int(i * 1000 / fps)
        rec = {"t": round(i / fps, 3)}
        if face:
            r = face.detect_for_video(img, ms)
            fl = []
            for k, lm in enumerate(r.face_landmarks):
                xs, ys = [p.x for p in lm], [p.y for p in lm]
                bs = {c.category_name: c.score for c in r.face_blendshapes[k]} if r.face_blendshapes else {}
                fl.append({"box": [round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4)],
                           "smile": round((bs.get("mouthSmileLeft", 0) + bs.get("mouthSmileRight", 0)) / 2, 3),
                           "mouth_open": round(bs.get("jawOpen", 0), 3),
                           "blink": round((bs.get("eyeBlinkLeft", 0) + bs.get("eyeBlinkRight", 0)) / 2, 3),
                           "pts": [[round(lm[j].x, 4), round(lm[j].y, 4)] for j in range(0, len(lm), 12)] if a.overlay else None})
            fl.sort(key=lambda d: -(d["box"][2] - d["box"][0]) * (d["box"][3] - d["box"][1]))
            rec["faces"] = fl
        if pose:
            r = pose.detect_for_video(img, ms)
            rec["pose"] = [[round(p.x, 4), round(p.y, 4), round(p.visibility, 2)] for p in r.pose_landmarks[0]] if r.pose_landmarks else None
        if hands:
            r = hands.detect_for_video(img, ms)
            rec["hands"] = [{"side": r.handedness[k][0].category_name, "pts": [[round(p.x, 4), round(p.y, 4)] for p in lm]}
                            for k, lm in enumerate(r.hand_landmarks)]
        track.append(rec)
        if (i + 1) % 300 == 0:
            print(f"  {i + 1} frames, {(i + 1) / (time.time() - t0):.0f} fps", flush=True)
    n = len(track)

    summary = {"frames": n, "fps": fps, "seconds": round(n / fps, 2)}
    if face:
        has = np.array([bool(r["faces"]) for r in track])
        smile = np.array([r["faces"][0]["smile"] if r["faces"] else 0 for r in track])
        summary.update(face_found_pct=round(100 * has.mean(), 1), smile_moments=spans(smile > 0.55, fps, 0.4))
    if pose:
        summary["pose_found_pct"] = round(100 * np.mean([r["pose"] is not None for r in track]), 1)
    if hands:
        summary["hands_visible_pct"] = round(100 * np.mean([bool(r["hands"]) for r in track]), 1)
    out_json = src.with_name(f"{src.stem}_track.json")
    out_json.write_text(json.dumps({"video": str(src), "crop": a.crop, "start": a.start, "summary": summary, "frames": track}),
                        encoding="utf-8")
    print(f"tracked {n} frames in {time.time() - t0:.0f}s -> {out_json}")
    print(json.dumps(summary))

    if a.reframe and face:
        aw, ah = map(float, a.aspect.split(":"))
        ch = H if W / H >= aw / ah else int(W * ah / aw)
        cw = int(round(ch * aw / ah / 2) * 2); ch = int(ch // 2 * 2)
        xs = np.array([(r["faces"][0]["box"][0] + r["faces"][0]["box"][2]) / 2 * W if r["faces"] else np.nan for r in track])
        ys = np.array([(r["faces"][0]["box"][1] + r["faces"][0]["box"][3]) / 2 * H if r["faces"] else np.nan for r in track])
        for arr, full in ((xs, W), (ys, H)):  # fill gaps by holding the last known position
            if np.all(np.isnan(arr)):
                arr[:] = full / 2
            idx = np.where(~np.isnan(arr), np.arange(len(arr)), 0)
            np.maximum.accumulate(idx, out=idx)
            arr[:] = arr[idx]
            arr[np.isnan(arr)] = np.nanmean(arr)
        sig = max(1.0, a.follow * fps)
        k = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2); k /= k.sum()
        sx = np.convolve(np.pad(xs, len(k) // 2, mode="edge"), k, "valid")[:n]
        sy = np.convolve(np.pad(ys, len(k) // 2, mode="edge"), k, "valid")[:n]
        x0 = np.clip(sx - cw / 2, 0, W - cw).astype(int)
        y0 = np.clip(sy - ch * 0.42, 0, H - ch).astype(int)  # face a little above centre
        out = src.with_name(f"{src.stem}_{a.aspect.replace(':', 'x')}.mp4")
        wr = av.video_writer(out, cw, ch, info["fps_str"], audio_from=src if info["has_audio"] else None,
                             audio_start=a.start, audio_seconds=a.seconds)
        for i, f in enumerate(frames()):
            if i >= n:
                break
            wr.stdin.write(np.ascontiguousarray(f[y0[i]:y0[i] + ch, x0[i]:x0[i] + cw]).tobytes())
        wr.stdin.close(); wr.wait()
        print(f"reframed {cw}x{ch} -> {out}")

    if a.overlay:
        out = src.with_name(f"{src.stem}_overlay.mp4")
        wr = av.video_writer(out, W, H, info["fps_str"], audio_from=src if info["has_audio"] else None,
                             audio_start=a.start, audio_seconds=a.seconds)
        P = lambda p: (int(p[0] * W), int(p[1] * H))  # noqa: E731
        for i, f in enumerate(frames()):
            if i >= n:
                break
            f = f.copy(); r = track[i]
            for fc in r.get("faces") or []:
                b = fc["box"]
                cv2.rectangle(f, P(b[:2]), P(b[2:]), (0, 255, 120), 2)
                for p in fc["pts"] or []:
                    cv2.circle(f, P(p), 1, (0, 255, 120), -1)
                cv2.putText(f, f"smile {fc['smile']:.2f}  mouth {fc['mouth_open']:.2f}", (P(b[:2])[0], max(15, P(b[:2])[1] - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 120), 1, cv2.LINE_AA)
            if r.get("pose"):
                for s, e in POSE_EDGES:
                    if r["pose"][s][2] > 0.5 and r["pose"][e][2] > 0.5:
                        cv2.line(f, P(r["pose"][s]), P(r["pose"][e]), (255, 180, 0), 2, cv2.LINE_AA)
            for hd in r.get("hands") or []:
                for s, e in HAND_EDGES:
                    cv2.line(f, P(hd["pts"][s]), P(hd["pts"][e]), (255, 60, 200), 2, cv2.LINE_AA)
            wr.stdin.write(np.ascontiguousarray(f).tobytes())
        wr.stdin.close(); wr.wait()
        print(f"overlay -> {out}")


if __name__ == "__main__":
    main()
