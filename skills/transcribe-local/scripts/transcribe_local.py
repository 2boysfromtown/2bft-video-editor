#!/usr/bin/env python3
"""Transcribe an audio/video file locally with faster-whisper (offline Whisper).

Prints "[MM:SS] text" lines. Audio never leaves the machine.

Where faster-whisper comes from, in this order:
  1. the Python running this script (`pip install faster-whisper`);
  2. an existing faster-whisper install that the Codex desktop app ships under
     ~/.cache/codex-runtimes (reused if present, nothing is installed);
  3. otherwise it stops and tells you to `pip install faster-whisper`.

Which model, in this order:
  --model DIR_OR_NAME, then $TRANSCRIBE_MODEL, then the best faster-whisper
  model already in the Hugging Face cache (~/.cache/huggingface/hub), then
  "large-v3-turbo" (downloaded once, about 1.6 GB).

Usage:
  python transcribe_local.py <media-file> [--start T] [--end T] [--language en]
                             [--model DIR_OR_NAME] [--device cpu|cuda] [--out FILE]
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


HOME = Path.home()
REEXEC_FLAG = "TRANSCRIBE_LOCAL_REEXEC"
DEFAULT_MODEL = "large-v3-turbo"


def codex_python() -> str | None:
    """Python bundled with the Codex desktop app's runtime, if it is installed."""
    base = HOME / ".cache" / "codex-runtimes" / "*" / "dependencies" / "python"
    hits: list[str] = []
    for pattern in ("python.exe", "bin/python3", "python3"):
        hits += glob.glob(str(base / pattern))
    hits.sort(key=os.path.getmtime, reverse=True)
    return hits[0] if hits else None


try:
    import numpy as np
    from faster_whisper import WhisperModel
except ImportError:
    py = codex_python()
    if not py or os.environ.get(REEXEC_FLAG):
        raise SystemExit(
            "faster-whisper is not installed for this Python. Install it with:\n"
            "    pip install faster-whisper\n"
            "(If the Codex desktop app is installed, its bundled faster-whisper under "
            "~/.cache/codex-runtimes is reused automatically; none was found.)"
        )
    env = dict(os.environ, **{REEXEC_FLAG: "1"})
    raise SystemExit(subprocess.run([py, "-B", __file__, *sys.argv[1:]], env=env).returncode)


def find_model(explicit: str | None) -> tuple[str, bool]:
    """Return (model directory or name, local_files_only)."""
    chosen = explicit or os.environ.get("TRANSCRIBE_MODEL")
    if chosen:
        return chosen, os.path.isdir(chosen)
    hub = Path(os.environ.get("HF_HOME", HOME / ".cache" / "huggingface")) / "hub"
    snaps = [
        p for p in glob.glob(str(hub / "models--*faster-whisper*" / "snapshots" / "*"))
        if os.path.exists(os.path.join(p, "model.bin"))
    ]
    if not snaps:
        print(f"[transcribe] no cached model found; downloading '{DEFAULT_MODEL}' once "
              "(use --model small for a faster, smaller one)", file=sys.stderr)
        return DEFAULT_MODEL, False

    def rank(path: str) -> tuple[int, str]:
        name = path.lower()
        return (0 if "turbo" in name else 1 if "large" in name else 2, name)

    return min(snaps, key=rank), True


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    bundled = glob.glob(str(HOME / ".cache" / "codex-runtimes" / "*" / "dependencies" / "bin" / "ffmpeg*"))
    if bundled:
        return bundled[0]
    raise SystemExit("ffmpeg not found on PATH.")


def parse_time(value: str | None) -> float | None:
    if not value:
        return None
    try:
        seconds = 0.0
        for part in value.split(":"):
            seconds = seconds * 60 + float(part)
        return seconds
    except ValueError:
        raise SystemExit(f"Cannot parse time {value!r} (expected SS, MM:SS or HH:MM:SS)")


def load_audio(src: str, start: float | None, end: float | None) -> "np.ndarray":
    """Decode to 16 kHz mono float32 with ffmpeg (avoids PyAV container quirks)."""
    cmd = [find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    if end is not None:
        cmd += ["-t", f"{max(0.0, end - (start or 0.0)):.3f}"]
    with tempfile.TemporaryDirectory(prefix="transcribe-") as tmp:
        wav_path = os.path.join(tmp, "audio.wav")
        cmd += ["-i", src, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not os.path.exists(wav_path):
            raise SystemExit(f"ffmpeg could not read audio from {src}: {result.stderr.strip()}")
        with wave.open(wav_path, "rb") as w:
            frames = w.readframes(w.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


def stamp(seconds: float) -> str:
    total = int(seconds)
    return f"[{total // 60:02d}:{total % 60:02d}]"


def main() -> int:
    ap = argparse.ArgumentParser(description="Offline Whisper transcription with faster-whisper.")
    ap.add_argument("media", help="Audio or video file")
    ap.add_argument("--start", help="Range start (SS, MM:SS or HH:MM:SS)")
    ap.add_argument("--end", help="Range end (SS, MM:SS or HH:MM:SS)")
    ap.add_argument("--language", help="Language code, e.g. en (default: auto-detect)")
    ap.add_argument("--model", help=f"Model directory or name (default: best cached, else {DEFAULT_MODEL})")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Default cpu (int8)")
    ap.add_argument("--out", help="Also write the transcript to this file")
    args = ap.parse_args()

    media = Path(args.media).expanduser().resolve()
    if not media.exists():
        raise SystemExit(f"File not found: {media}")

    start, end = parse_time(args.start), parse_time(args.end)
    offset = start or 0.0
    model_ref, local_only = find_model(args.model)
    compute_type = "int8" if args.device == "cpu" else "float16"

    print(f"[transcribe] model: {model_ref}", file=sys.stderr)
    print(f"[transcribe] decoding audio from {media.name}...", file=sys.stderr)
    audio = load_audio(str(media), start, end)
    if audio.size == 0:
        raise SystemExit("No audio samples decoded - the file may have no audio track.")

    model = WhisperModel(model_ref, device=args.device, compute_type=compute_type, local_files_only=local_only)
    print(f"[transcribe] transcribing {audio.size / 16000:.1f}s of audio on {args.device}...", file=sys.stderr)

    def run(vad: bool):
        segments, info = model.transcribe(audio, beam_size=5, language=args.language, vad_filter=vad)
        return list(segments), info

    try:
        segments, info = run(vad=True)
    except Exception as exc:  # VAD needs onnxruntime; fall back rather than fail the whole run
        print(f"[transcribe] VAD unavailable ({exc}); retrying without it", file=sys.stderr)
        segments, info = run(vad=False)

    print(f"[transcribe] language: {info.language} (p={info.language_probability:.2f})", file=sys.stderr)
    lines = [f"{stamp(offset + seg.start)} {seg.text.strip()}" for seg in segments if seg.text.strip()]
    text = "\n".join(lines)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
