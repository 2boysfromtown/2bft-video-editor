"""Shared ffmpeg helpers for the local-av-tools scripts (stdlib + numpy only).

Scripts run with -I (isolated), which drops the script folder from sys.path, so each script does
sys.path.insert(0, <this folder>) before `import av_common`.
"""
import json, subprocess, sys
from fractions import Fraction
import numpy as np


def utf8_stdout():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def probe(path):
    """-> dict(w, h, fps (float), fps_str ("30000/1001"), duration, has_audio, nb_frames (estimate))."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    has_audio = any(s["codec_type"] == "audio" for s in d["streams"])
    dur = float(d["format"].get("duration", 0) or 0)
    info = {"has_audio": has_audio, "duration": dur, "w": None, "h": None, "fps": None, "fps_str": None, "nb_frames": 0}
    if v:
        fps_str = v.get("avg_frame_rate") or v.get("r_frame_rate")
        if not fps_str or fps_str.startswith("0"):
            fps_str = v.get("r_frame_rate", "30/1")
        fps = float(Fraction(fps_str))
        w, h = int(v["width"]), int(v["height"])
        rot = 0
        for sd in v.get("side_data_list", []) or []:
            if "rotation" in sd:
                rot = abs(int(sd["rotation"]))
        if rot in (90, 270):
            w, h = h, w
        info.update(w=w, h=h, fps=fps, fps_str=fps_str, nb_frames=int(round(dur * fps)))
    return info


def read_frames(path, w, h, start=None, seconds=None, pix="rgb24", size=None):
    """Yield frames as HxWxC uint8 arrays. size=(w2, h2) scales on the way out."""
    ch = 4 if pix == "rgba" else (1 if pix == "gray" else 3)
    cmd = ["ffmpeg", "-v", "error"]
    if start:
        cmd += ["-ss", str(start)]
    cmd += ["-i", str(path)]
    if seconds:
        cmd += ["-t", str(seconds)]
    if size:
        cmd += ["-vf", f"scale={size[0]}:{size[1]}:flags=area"]
        w, h = size
    cmd += ["-f", "rawvideo", "-pix_fmt", pix, "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = w * h * ch
    try:
        while True:
            buf = p.stdout.read(n)
            if len(buf) < n:
                break
            arr = np.frombuffer(bytearray(buf), np.uint8)
            yield arr.reshape(h, w, ch) if ch > 1 else arr.reshape(h, w)
    finally:
        p.stdout.close()
        p.wait()


def video_writer(out, w, h, fps_str, pix_in="rgb24", fmt="h264", audio_from=None, audio_start=None, audio_seconds=None):
    """Open an ffmpeg process that takes raw frames on stdin. fmt: h264 | prores4444 (alpha) | vp9alpha | gray.
    audio_from: copy (re-encode) that file's audio track into the output."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", pix_in, "-s", f"{w}x{h}", "-r", str(fps_str), "-i", "-"]
    if audio_from:
        if audio_start:
            cmd += ["-ss", str(audio_start)]
        if audio_seconds:
            cmd += ["-t", str(audio_seconds)]
        cmd += ["-i", str(audio_from), "-map", "0:v", "-map", "1:a?", "-shortest"]
    if fmt == "h264":
        cmd += ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "18", "-b:v", "0", "-pix_fmt", "yuv420p"]
    elif fmt == "prores4444":
        cmd += ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-vendor", "apl0"]
    elif fmt == "vp9alpha":
        cmd += ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "24", "-row-mt", "1", "-auto-alt-ref", "0"]
    if audio_from:
        cmd += ["-c:a", "pcm_s16le" if fmt == "prores4444" else ("libopus" if fmt == "vp9alpha" else "aac"), "-b:a", "192k"]
    if fmt == "h264":
        cmd += ["-movflags", "+faststart"]
    cmd += [str(out)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def read_audio(path, sr, channels):
    """-> float32 array shaped (channels, samples)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", str(channels), "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, channels).T.copy()
