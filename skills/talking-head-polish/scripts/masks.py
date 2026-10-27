#!/usr/bin/env python3
"""Person masks for the stretches of a video where text should go BEHIND the speaker.

  python masks.py <video> <out_dir> "3.3-6.3,15.3-25.2" [--model u2net_human_seg] [--scale 0.5]

Writes one grayscale PNG per frame, named by the frame index in the source video
(00000.png ...), at half resolution by default (cutout.py scales them back up).
Uses rembg (pip install rembg onnxruntime); the model downloads once on first use.
"""
import argparse
import json
import os
import subprocess

from PIL import Image
from rembg import new_session, remove


def probe(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "json", src], capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(num) / float(den)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out_dir")
    ap.add_argument("ranges", help="comma-separated start-end seconds, e.g. 3.3-6.3,15.3-25.2")
    ap.add_argument("--model", default="u2net_human_seg")
    ap.add_argument("--scale", type=float, default=0.5)
    a = ap.parse_args()

    vw, vh, fps = probe(a.video)
    w, h = int(vw * a.scale) // 2 * 2, int(vh * a.scale) // 2 * 2
    os.makedirs(a.out_dir, exist_ok=True)
    sess = new_session(a.model)
    for r in a.ranges.split(","):
        st, en = map(float, r.split("-"))
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{st}", "-i", a.video, "-t", f"{en - st}",
                              "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        i = 0
        while True:
            b = p.stdout.read(w * h * 3)
            if len(b) < w * h * 3:
                break
            im = Image.frombuffer("RGB", (w, h), b)
            m = remove(im, session=sess, only_mask=True, post_process_mask=False)
            m.save(os.path.join(a.out_dir, f"{round(st * fps) + i:05d}.png"))
            i += 1
        print(f"{st}-{en}s: {i} masks", flush=True)


if __name__ == "__main__":
    main()
