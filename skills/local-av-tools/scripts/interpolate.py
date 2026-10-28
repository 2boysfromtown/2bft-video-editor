"""Smooth motion / slow motion with RIFE 4.26 (MIT) or FILM (Apache-2.0), streamed so any length works.

Runs with ComfyUI's Python (uses ComfyUI's built-in RIFE/FILM code and the model files in
ComfyUI\\models\\frame_interpolation). ComfyUI does not need to be running.

  <ComfyUI python> -I interpolate.py clip.mp4
      -> clip_x2.mp4  (twice the frames: 24 -> 48 fps, 30 -> 60 fps; same length, audio kept)
  ... --x 3              24 fps WAN clip -> 72 fps; or --fps 60 picks the multiplier for you (then resamples to exactly 60)
  ... --slowmo --x 4     4x slow motion (keeps the source fps, drops audio)
  ... --model film       FILM: slower, better on big motion; RIFE is the default
  ... --start 10 --seconds 5

Hard cuts are detected and not blended (the frame is held instead), so edited footage is safe.
"""
import argparse, os, math, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMFY = Path(os.environ.get("COMFYUI_DIR", "ComfyUI"))  # the ComfyUI folder (holds comfy/ and models/)
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(COMFY))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
import av_common as av  # noqa: E402
import comfy.utils  # noqa: E402
from comfy_extras.frame_interpolation_models.ifnet import IFNet, detect_rife_config  # noqa: E402
from comfy_extras.frame_interpolation_models.film_net import FILMNet  # noqa: E402

av.utf8_stdout()
MODELS = {"rife": "rife_v4.26.safetensors", "film": "film_net_fp16.safetensors"}


def load(name):
    sd = comfy.utils.load_torch_file(str(COMFY / "models" / "frame_interpolation" / MODELS[name]), safe_load=True)
    if "extract.extract_sublevels.convs.0.0.conv.weight" in sd:
        m = FILMNet()
    else:  # same key clean-up as ComfyUI's FrameInterpolationModelLoader
        sd = comfy.utils.state_dict_prefix_replace(sd, {"module.": "", "flownet.": ""})
        km = {k: f"blocks.{i}.{k[len(f'block{i}.'):]}" for k in sd for i in range(5) if k.startswith(f"block{i}.")}
        sd = {km.get(k, k): v for k, v in sd.items() if not k.startswith(("teacher.", "caltime."))}
        head_ch, channels = detect_rife_config(sd)
        m = IFNet(head_ch=head_ch, channels=channels)
    m.load_state_dict(sd)
    return m.eval().to("cuda", torch.float16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out")
    ap.add_argument("--x", type=int, default=2, help="frame multiplier (2-16)")
    ap.add_argument("--fps", type=float, help="target fps, e.g. 60 (overrides --x)")
    ap.add_argument("--slowmo", action="store_true", help="keep source fps -> slow motion, no audio")
    ap.add_argument("--model", choices=list(MODELS), default="rife")
    ap.add_argument("--start", type=float)
    ap.add_argument("--seconds", type=float)
    ap.add_argument("--cut", type=float, default=0.18, help="scene-cut threshold (mean frame difference, 0-1); 0 disables")
    a = ap.parse_args()

    src = Path(a.video)
    info = av.probe(src)
    W, H, fps = info["w"], info["h"], info["fps"]
    x = max(2, math.ceil(a.fps / fps)) if a.fps else a.x
    out_fps = fps if a.slowmo else fps * x
    out = Path(a.out) if a.out else src.with_name(f"{src.stem}_{'slowmo' if a.slowmo else 'x'}{x}.mp4")
    print(f"{src.name}: {W}x{H} @ {fps:.3f} fps -> x{x} with {a.model.upper()} -> {out_fps:.3f} fps{' (slow motion)' if a.slowmo else ''}")

    model = load(a.model)
    film = isinstance(model, FILMNet)
    align = 64
    pH, pW = math.ceil(H / align) * align, math.ceil(W / align) * align
    ts = [i / x for i in range(1, x)]
    ts_t = torch.tensor(ts, device="cuda", dtype=torch.float16).view(-1, 1, 1, 1).expand(-1, 1, pH, pW)

    resample = bool(a.fps) and not a.slowmo and abs(out_fps - a.fps) > 0.01  # then resample to the exact target
    enc_out = out.with_suffix(".tmp.mp4") if resample else out
    writer = av.video_writer(enc_out, W, H, f"{out_fps:.6f}", audio_from=None if a.slowmo else src,
                             audio_start=a.start, audio_seconds=a.seconds)

    def to_t(fr):
        t = torch.from_numpy(fr).to("cuda").permute(2, 0, 1)[None].half().div_(255)
        return F.pad(t, (0, pW - W, 0, pH - H), mode="reflect") if (pW != W or pH != H) else t

    def emit(t):  # t: (n,3,pH,pW) on GPU
        arr = (t[:, :, :H, :W].clamp(0, 1).mul(255).round().byte().permute(0, 2, 3, 1).contiguous().cpu().numpy())
        writer.stdin.write(arr.tobytes())

    t0, n, cuts = time.time(), 0, 0
    prev = prev_feat = None
    with torch.inference_mode():
        for fr in av.read_frames(src, W, H, a.start, a.seconds):
            cur = to_t(fr)
            if prev is not None:
                diff = F.avg_pool2d(cur - prev, 8).abs().mean().item() if a.cut > 0 else 0
                if diff > a.cut:  # hard cut: hold the old frame instead of blending two shots
                    emit(prev.expand(len(ts), -1, -1, -1)); cuts += 1
                    prev_feat = None
                else:
                    f0 = prev_feat if prev_feat is not None else model.extract_features(prev)
                    f1 = model.extract_features(cur)
                    cache = {"img0": f0, "img1": f1}
                    if film:
                        mids = model.forward_multi_timestep(prev, cur, ts, cache=cache)
                    else:
                        mids = model(prev.expand(len(ts), -1, -1, -1), cur.expand(len(ts), -1, -1, -1), timestep=ts_t, cache=cache)
                    emit(mids)
                    prev_feat = f1
            emit(cur)
            prev, n = cur, n + 1
            if n % 100 == 0:
                print(f"  {n} frames, {n / (time.time() - t0):.1f} fps", flush=True)
    writer.stdin.close(); writer.wait()

    if resample:
        import subprocess
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(enc_out), "-vf", f"fps={a.fps}", "-c:v", "h264_nvenc", "-preset", "p5",
                        "-cq", "18", "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)], check=True)
        enc_out.unlink()
    print(f"done: {n} source frames in {time.time() - t0:.0f}s, {cuts} cut(s) held -> {out}")


if __name__ == "__main__":
    main()
