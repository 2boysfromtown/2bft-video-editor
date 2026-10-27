#!/usr/bin/env python3
"""Transparent cut-out of the speaker (VP9 + alpha WebM) from the masks made by masks.py.

  python cutout.py <video> <mask_dir> <out.webm>

Frames without a mask come out fully transparent, so the cut-out only covers the
stretches you masked. Put it on top of your text layer to make text sit behind the person.
Needs ffmpeg with libvpx-vp9, numpy and Pillow.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter


def probe(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "json", src], capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    return int(s["width"]), int(s["height"]), s["r_frame_rate"]


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    src, maskdir, out = sys.argv[1:4]
    W, H, rate = probe(src)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", rate, "-i", "-",
                            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "18", "-b:v", "0", "-deadline", "good",
                            "-cpu-used", "5", "-row-mt", "1", "-auto-alt-ref", "0", out], stdin=subprocess.PIPE)
    empty = np.zeros((H, W, 4), np.uint8).tobytes()
    i = 0
    while True:
        b = dec.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        mp = os.path.join(maskdir, f"{i:05d}.png")
        if os.path.exists(mp):
            m = Image.open(mp).convert("L").resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))
            a = np.asarray(m, np.float32) / 255
            a = np.clip((a - 0.18) / 0.64, 0, 1)          # firm up the edge, drop the soft halo
            rgb = np.frombuffer(b, np.uint8).reshape(H, W, 3)
            enc.stdin.write(np.dstack([rgb, (a * 255).astype(np.uint8)]).tobytes())
        else:
            enc.stdin.write(empty)
        i += 1
    enc.stdin.close()
    enc.wait()
    print("frames", i)


if __name__ == "__main__":
    main()
