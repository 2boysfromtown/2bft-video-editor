#!/usr/bin/env python3
"""Generate placeholder sound effects with ffmpeg (no sample library needed).

Usage:
  python make_sfx.py <kind> <output.wav> [--dur SECONDS]

kinds:
  whoosh   band-passed pink noise with a swell and tail (transitions, movement)
  riser    rising sine sweep that builds (before a reveal)
  hit      low impact with a fast decay (on a punchline or title)
  pop      short high blip (UI element appearing)
  tick     very short click (typing, counters)

These are stand-ins for rough cuts. For the final mix prefer real licensed or
recorded sounds, and layer several (see video-sound-and-music).
"""
from __future__ import annotations

import argparse
import subprocess

RECIPES = {
    "whoosh": lambda d: (
        f"anoisesrc=d={d}:c=pink:r=48000:a=0.8",
        f"bandpass=f=1800:width_type=h:width=2500,"
        f"afade=t=in:st=0:d={d * 0.43:.3f}:curve=qsin,afade=t=out:st={d * 0.43:.3f}:d={d * 0.57:.3f}:curve=qsin,"
        "aformat=channel_layouts=stereo",
    ),
    "riser": lambda d: (
        f"aevalsrc='0.4*sin(2*PI*(300*t+700*t*t/2))*(t/{d})':d={d}:s=48000",
        "aformat=channel_layouts=stereo",
    ),
    "hit": lambda d: (
        f"aevalsrc='0.9*sin(2*PI*55*t)*exp(-4*t)+0.3*sin(2*PI*110*t)*exp(-7*t)':d={d}:s=48000",
        "aformat=channel_layouts=stereo",
    ),
    "pop": lambda d: (
        f"aevalsrc='0.6*sin(2*PI*(900+1400*t)*t)*exp(-30*t)':d={d}:s=48000",
        "aformat=channel_layouts=stereo",
    ),
    "tick": lambda d: (
        f"aevalsrc='0.5*sin(2*PI*2400*t)*exp(-120*t)':d={d}:s=48000",
        "aformat=channel_layouts=stereo",
    ),
}
DEFAULT_DUR = {"whoosh": 0.7, "riser": 2.0, "hit": 1.0, "pop": 0.15, "tick": 0.05}


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a placeholder SFX with ffmpeg.")
    ap.add_argument("kind", choices=sorted(RECIPES))
    ap.add_argument("output")
    ap.add_argument("--dur", type=float, default=None)
    args = ap.parse_args()

    dur = args.dur or DEFAULT_DUR[args.kind]
    source, filt = RECIPES[args.kind](dur)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", source, "-af", filt, args.output]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"ffmpeg failed: {result.stderr.strip()}")
    print(f"wrote {args.output} ({dur}s {args.kind})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
