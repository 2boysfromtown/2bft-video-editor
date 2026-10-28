"""Remove the background from images or video with BiRefNet (MIT) - no green screen needed. Streams, so any length works.

Runs with ComfyUI's Python (uses ComfyUI's built-in BiRefNet code and ComfyUI\\models\\background_removal\\birefnet.safetensors).
ComfyUI does not need to be running.

  <ComfyUI python> -I cutout.py photo.jpg      -> photo_cutout.png (transparent)
  ... webcam.mp4                    -> webcam_cutout.mov  (ProRes 4444 with alpha: drop on top of anything in DaVinci/Premiere/ffmpeg)
  ... webcam.mp4 --as webm          -> .webm VP9 with alpha (small; Chrome/Remotion play it with transparency)
  ... webcam.mp4 --as green         -> .mp4 on pure green (for editors that only take keyable footage)
  ... webcam.mp4 --as matte         -> .mp4 black/white mask only
  ... webcam.mp4 --bg beach.jpg     -> .mp4 composited over an image or colour (--bg "#101820")
  ... --start 30 --seconds 5   --smooth 0.3 (steadier edges on video; higher = steadier but laggier)
  ... --crop x,y,w,h                cut a region first, e.g. the webcam box of a stream layout
"""
import argparse, os, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMFY = Path(os.environ.get("COMFYUI_DIR", "ComfyUI"))  # the ComfyUI folder (holds comfy/ and models/)
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(COMFY))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import av_common as av  # noqa: E402
import comfy.bg_removal_model  # noqa: E402

av.utf8_stdout()
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def parse_bg(bg, w, h):
    if not bg:
        return None
    if bg.startswith("#"):
        c = bg.lstrip("#")
        return np.broadcast_to(np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.float32), (h, w, 3))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", bg, "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--as", dest="fmt", choices=["mov", "webm", "green", "matte"], default="mov")
    ap.add_argument("--bg", help="image file or #rrggbb to composite over (video -> mp4)")
    ap.add_argument("--start", type=float)
    ap.add_argument("--seconds", type=float)
    ap.add_argument("--smooth", type=float, default=0.0, help="0-0.8 temporal smoothing of the mask on video")
    ap.add_argument("--crop", help="x,y,w,h region to cut out first")
    ap.add_argument("--batch", type=int, default=4)
    a = ap.parse_args()

    bg_model = comfy.bg_removal_model.load(str(COMFY / "models" / "background_removal" / "birefnet.safetensors"))
    # Run the network on the GPU directly (ComfyUI's memory manager offloads it to the CPU when memory is tight,
    # which made it ~4x slower). If the GPU is short on memory, wait and retry, then fall back to ComfyUI's path.
    net = bg_model.model.to("cuda").eval()
    import comfy.clip_model as cm

    def run_direct(t):
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
            pv = cm.clip_preprocess(t.to("cuda"), size=bg_model.image_size, mean=bg_model.image_mean, std=bg_model.image_std, crop=False)
            out = net(pixel_values=pv)
            out = torch.nn.functional.interpolate(out.float(), size=t.shape[1:3], mode="bicubic")
            return out.sigmoid().squeeze(1).clamp_(0, 1).cpu().numpy()

    def masks(frames):  # list of HxWx3 uint8 -> (n,H,W) float 0-1
        t = torch.from_numpy(np.stack(frames)).float().div_(255)
        for attempt in range(6):
            try:
                return np.concatenate([run_direct(t[i:i + 1]) for i in range(len(t))])
            except torch.OutOfMemoryError:
                torch.cuda.empty_cache()
                time.sleep(2)
        print("  GPU memory is tight: using ComfyUI's slower offloading path for this batch", flush=True)
        with torch.inference_mode():
            return bg_model.encode_image(t).float().clamp_(0, 1).cpu().numpy()

    for inp in a.inputs:
        src = Path(inp)
        t0 = time.time()
        if src.suffix.lower() in IMG_EXT:
            info = av.probe(src)
            fr = next(av.read_frames(src, info["w"], info["h"]))
            m = masks([fr])[0]
            out = Path(a.out) if a.out and len(a.inputs) == 1 else src.with_name(f"{src.stem}_cutout.png")
            rgba = np.dstack([fr, (m * 255).round().astype(np.uint8)])
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{fr.shape[1]}x{fr.shape[0]}",
                            "-i", "-", "-frames:v", "1", str(out)], input=rgba.tobytes(), check=True)
            print(f"{src.name} -> {out} ({time.time() - t0:.1f}s)")
            continue

        info = av.probe(src)
        W, H = info["w"], info["h"]
        frames_iter = av.read_frames(src, W, H, a.start, a.seconds)
        if a.crop:
            x, y, cw, ch = map(int, a.crop.split(","))
            frames_iter = (f[y:y + ch, x:x + cw] for f in frames_iter)
            W, H = cw, ch
        bg = parse_bg(a.bg, W, H)
        fmt = "bg" if bg is not None else a.fmt
        ext = {"mov": ".mov", "webm": ".webm", "green": ".mp4", "matte": ".mp4", "bg": ".mp4"}[fmt]
        out = Path(a.out) if a.out and len(a.inputs) == 1 else src.with_name(f"{src.stem}_cutout{ext}")
        if fmt == "green":
            bg = np.broadcast_to(np.array([0, 255, 0], np.float32), (H, W, 3))
        enc = {"mov": "prores4444", "webm": "vp9alpha"}.get(fmt, "h264")
        pix = "rgba" if fmt in ("mov", "webm") else "rgb24"
        writer = av.video_writer(out, W, H, info["fps_str"], pix_in=pix, fmt=enc, audio_from=src if info["has_audio"] else None,
                                 audio_start=a.start, audio_seconds=a.seconds)
        prev, n, buf = None, 0, []

        def flush(buf):
            nonlocal prev, n
            for fr, m in zip(buf, masks(buf)):
                if a.smooth > 0 and prev is not None:
                    m = a.smooth * prev + (1 - a.smooth) * m
                prev = m
                if fmt in ("mov", "webm"):
                    o = np.dstack([fr, (m * 255).round().astype(np.uint8)])
                elif fmt == "matte":
                    o = np.repeat((m * 255).round().astype(np.uint8)[..., None], 3, 2)
                else:
                    o = (fr * m[..., None] + bg * (1 - m[..., None])).round().astype(np.uint8)
                writer.stdin.write(np.ascontiguousarray(o).tobytes())
                n += 1
            if n and n % 100 < len(buf):
                print(f"  {n} frames, {n / (time.time() - t0):.1f} fps", flush=True)

        for fr in frames_iter:
            buf.append(np.ascontiguousarray(fr))
            if len(buf) == a.batch:
                flush(buf); buf = []
        if buf:
            flush(buf)
        writer.stdin.close(); writer.wait()
        print(f"{src.name}: {n} frames in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
