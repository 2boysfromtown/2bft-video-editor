#!/usr/bin/env python3
"""Cut dead air out of a talking video or audio file (automatic jump cuts).

Detects silences with ffmpeg's silencedetect, keeps the voiced stretches plus a
small pad on each side so words are not clipped, and joins them with hard cuts.

Usage:
  python remove_silence.py <input> <output> [--noise -35] [--min-silence 0.4]
                           [--pad 0.08] [--dry-run]

  --noise        silence threshold in dB (default -35; raise toward -30 for noisy rooms)
  --min-silence  only gaps at least this long (seconds) are removed (default 0.4)
  --pad          seconds of room kept around speech so words are not clipped (default 0.08)
  --dry-run      print the keep-list and stats without rendering

Output container follows the extension: .mp4/.mov re-encode H.264 + AAC, .wav/.m4a/.mp3 audio only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def probe(path: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
         "-of", "json", path],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise SystemExit(f"ffprobe failed: {out.stderr.strip()}")
    data = json.loads(out.stdout or "{}")
    kinds = {s.get("codec_type") for s in data.get("streams", [])}
    return {"duration": float(data["format"]["duration"]), "has_video": "video" in kinds, "has_audio": "audio" in kinds}


def detect_silence(path: str, noise_db: float, min_silence: float) -> list[tuple[float, float]]:
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn",
           "-af", f"silencedetect=noise={noise_db}dB:d={min_silence}", "-f", "null", "-"]
    log = subprocess.run(cmd, capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*(-?[\d.]+)", log)]
    spans = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None  # file may end inside a silence
        spans.append((max(0.0, s), e))
    return spans  # e is None for a trailing silence


def keep_segments(duration: float, silences, pad: float) -> list[tuple[float, float]]:
    keeps, cursor = [], 0.0
    for s, e in silences:
        end_keep = min(duration, s + pad)
        if s > 0.05 and end_keep > cursor:  # a silence at the very start leaves nothing to keep before it
            keeps.append((cursor, end_keep))
        cursor = duration if e is None else max(cursor, e - pad)
    if cursor < duration:
        keeps.append((cursor, duration))
    merged: list[list[float]] = []
    for a, b in keeps:  # merge overlaps created by padding
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged if b - a > 0.05]


def build_graph(segs, has_video: bool, has_audio: bool) -> tuple[str, list[str]]:
    parts, labels = [], []
    for i, (a, b) in enumerate(segs):
        if has_video:
            parts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]")
            labels.append(f"[v{i}]")
        if has_audio:
            parts.append(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}]")
            labels.append(f"[a{i}]")
    v, a = (1 if has_video else 0), (1 if has_audio else 0)
    outs = ("[v]" if has_video else "") + ("[a]" if has_audio else "")
    parts.append("".join(labels) + f"concat=n={len(segs)}:v={v}:a={a}{outs}")
    maps = []
    if has_video:
        maps += ["-map", "[v]"]
    if has_audio:
        maps += ["-map", "[a]"]
    return ";\n".join(parts), maps


def main() -> int:
    ap = argparse.ArgumentParser(description="Remove dead air from a video or audio file.")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--noise", type=float, default=-35.0)
    ap.add_argument("--min-silence", type=float, default=0.4)
    ap.add_argument("--pad", type=float, default=0.08)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = str(Path(args.input).expanduser().resolve())
    info = probe(src)
    if not info["has_audio"]:
        raise SystemExit("Input has no audio stream - nothing to detect silence in.")

    silences = detect_silence(src, args.noise, args.min_silence)
    segs = keep_segments(info["duration"], silences, args.pad)
    if not segs:
        raise SystemExit("Everything was classified as silence - lower --noise (e.g. -45).")

    kept = sum(b - a for a, b in segs)
    cuts = len(segs) - 1
    minutes = kept / 60 if kept else 1
    print(f"original {info['duration']:.1f}s -> kept {kept:.1f}s "
          f"({info['duration'] - kept:.1f}s removed), {len(segs)} segments, "
          f"{cuts} cuts = {cuts / minutes:.1f} cuts/min", file=sys.stderr)
    if args.dry_run:
        for a, b in segs:
            print(f"keep {a:8.2f} -> {b:8.2f}")
        return 0

    graph, maps = build_graph(segs, info["has_video"], True)
    out = Path(args.output).expanduser().resolve()
    is_video_out = info["has_video"] and out.suffix.lower() in {".mp4", ".mov", ".mkv", ".m4v"}
    if info["has_video"] and not is_video_out:
        graph, maps = build_graph(segs, False, True)  # audio-only output requested

    tail = list(maps)
    if is_video_out:
        tail += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
    tail.append(str(out))
    base = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src]

    # Short graphs go inline. Long ones (many cuts) would overflow the Windows command line,
    # so write them to a file; the option for that was renamed in ffmpeg 7 (-/filter_complex).
    attempts = [base + ["-filter_complex", graph] + tail]
    if len(graph) > 20000:
        attempts = []
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(graph)
        script = f.name
    attempts += [base + ["-/filter_complex", script] + tail,
                 base + ["-filter_complex_script", script] + tail]
    result = None
    for cmd in attempts:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            break
        if "Unrecognized option" not in result.stderr and "Option not found" not in result.stderr:
            break
    Path(script).unlink(missing_ok=True)
    if result is None or result.returncode != 0:
        raise SystemExit(f"ffmpeg failed: {result.stderr.strip() if result else 'no attempt ran'}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
