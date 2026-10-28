"""Find every cut (shot change, including fades and dissolves) in a video with TransNetV2 (MIT).

  python -I shots.py reel.mp4
      -> reel_shots.json + reel_shots.csv  (shot number, start/end time, length) and prints the pacing
  ... reel.mp4 --sheet               also a contact sheet (first frame of every shot) -> reel_shots.jpg
  ... reel.mp4 --split               also cut every shot into its own mp4 -> reel_shots\\shot_001.mp4 ...
  ... --threshold 0.5                lower = more cuts found (default 0.5)

Uses: study the pacing of a reference reel (cuts per minute, shot lengths), chop a long edit or a
downloaded clip into shots, or find scene boundaries before frame interpolation or reframing.
"""
import argparse, csv, json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from transnetv2_pytorch import TransNetV2  # noqa: E402
import av_common as av  # noqa: E402

av.utf8_stdout()


def ts(t):
    return f"{int(t // 60):02d}:{t % 60:06.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--split", action="store_true")
    a = ap.parse_args()

    src = Path(a.video)
    info = av.probe(src)
    fps = info["fps"]
    t0 = time.time()
    model = TransNetV2(device="cuda" if torch.cuda.is_available() else "cpu")
    model.eval()
    frames = np.stack(list(av.read_frames(src, info["w"], info["h"], size=(48, 27))))
    with torch.inference_mode():
        single, _ = model.predict_frames(torch.from_numpy(frames).to(model.device), quiet=True)
    scenes = model.predictions_to_scenes(single.float().numpy(), threshold=a.threshold)
    shots = [{"shot": i + 1, "start": round(s / fps, 3), "end": round((e + 1) / fps, 3), "start_frame": int(s), "end_frame": int(e),
              "length": round((e + 1 - s) / fps, 3)} for i, (s, e) in enumerate(scenes)]

    base = src.with_name(f"{src.stem}_shots")
    Path(f"{base}.json").write_text(json.dumps({"video": str(src), "fps": fps, "shots": shots}, indent=1), encoding="utf-8")
    with open(f"{base}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(shots[0])); w.writeheader(); w.writerows(shots)

    lens = np.array([s["length"] for s in shots])
    dur = len(frames) / fps
    print(f"{src.name}: {len(shots)} shots in {dur:.1f}s ({len(shots) / dur * 60:.0f} cuts/min), "
          f"shot length median {np.median(lens):.2f}s, shortest {lens.min():.2f}s, longest {lens.max():.2f}s  [{time.time() - t0:.0f}s]")
    for s in shots[:40]:
        print(f"  {s['shot']:3d}  {ts(s['start'])} -> {ts(s['end'])}  {s['length']:6.2f}s")
    if len(shots) > 40:
        print(f"  ... {len(shots) - 40} more in {base}.csv")

    if a.sheet:
        cols = 6
        sel = "+".join(f"eq(n\\,{s['start_frame']})" for s in shots[:96])
        rows = (min(len(shots), 96) + cols - 1) // cols
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf",
                        f"select='{sel}',scale=320:-2,drawtext=fontfile='C\\:/Windows/Fonts/arialbd.ttf':text='%{{eif\\:n+1\\:d}}':x=6:y=6:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6,tile={cols}x{rows}",
                        "-frames:v", "1", "-fps_mode", "vfr", f"{base}.jpg"], check=False)
        print("sheet ->", f"{base}.jpg")
    if a.split:
        d = Path(base); d.mkdir(exist_ok=True)
        for s in shots:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["start"]), "-i", str(src), "-t", str(s["length"]),
                            "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "19", "-c:a", "aac", str(d / f"shot_{s['shot']:03d}.mp4")], check=True)
        print(f"split {len(shots)} shots -> {d}")


if __name__ == "__main__":
    main()
