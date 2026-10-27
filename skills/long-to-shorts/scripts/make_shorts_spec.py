"""make_shorts_spec.py <plan.json> [--out DIR]

Turns a Shorts plan (written by Claude after reading the transcript of a long recording)
into one spec file per Short for build_react_short.py or clipkit.py.

What it adds on top of the plan: every talk range marked "tight" is split at its pauses
(ffmpeg silencedetect), so dead air between sentences is cut out automatically, and the
shared settings (src, rects, cams, music...) are copied into each clip.

plan.json:
{
  "src": "long_recording.mp4",            # relative to the plan file, or absolute
  "builder": "react",                      # "react" (build_react_short.py) or "panes" (clipkit.py)
  "rects": {"screen": {"rect": [x, y, w, h], "mode": "cover"}},
  "cams": [{"rect": [x, y, w, h], "label": "HOST"}],
  "music": {"style": "bounce", "bpm": 104, "gain_db": -14},
  "silence": {"min": 0.9, "pad": 0.22, "noise": -38},
  "clips": [
    {"name": "01_best_moment", "hook": "...", "ranges": [[120.0, 165.5, "screen", true]],
     "captions": [[121.0, 124.5, "..."]], "sfx": [{"t": 130.2, "kind": "hit"}], "cta": "..."}
  ]
}
A range is [src_start, src_end, rect_name, tight]; tight defaults to true.
Proofread every caption against the audio before posting.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def tighten(src, a, b, dmin=0.9, pad=0.22, noise=-38):
    """Split [a, b] into the stretches that are not silence (pauses >= dmin seconds removed)."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(a), "-t", str(b - a), "-i", src, "-vn",
                          "-af", f"silencedetect=noise={noise}dB:d={dmin}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) + a for x in re.findall(r"silence_start:\s*(-?[\d.]+)", log)]
    en = [float(x) + a for x in re.findall(r"silence_end:\s*(-?[\d.]+)", log)]
    keep, cur = [], a
    for i, s in enumerate(st):
        e = en[i] if i < len(en) else b
        if s - a > 0.05 and s + pad > cur:
            keep.append((cur, min(b, s + pad)))
        cur = max(cur, e - pad)
    if cur < b:
        keep.append((cur, b))
    return [(round(x, 2), round(y, 2)) for x, y in keep if y - x >= 0.3]  # short words like "and" survive


def main():
    args = sys.argv[1:]
    out = None
    if "--out" in args:
        i = args.index("--out")
        out = Path(args[i + 1])
        args = args[:i] + args[i + 2:]
    if not args:
        raise SystemExit(__doc__)
    plan_path = Path(args[0]).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    src = Path(plan["src"])
    src = str(src if src.is_absolute() else (plan_path.parent / src).resolve())
    out = (out or plan_path.parent / "_specs").resolve()
    out.mkdir(parents=True, exist_ok=True)
    sil = plan.get("silence", {})
    shared = {k: v for k, v in plan.items() if k not in ("clips", "src", "silence", "builder")}

    for c in plan["clips"]:
        ranges = []
        for r in c["ranges"]:
            a, b, rect = float(r[0]), float(r[1]), r[2] if len(r) > 2 else "main"
            tight = r[3] if len(r) > 3 else True
            pieces = tighten(src, a, b, sil.get("min", 0.9), sil.get("pad", 0.22), sil.get("noise", -38)) if tight else [(a, b)]
            ranges += [[s, e, 1.0, rect] for s, e in pieces]
        spec = {**shared, **c, "src": src, "ranges": ranges, "work": str(out.parent / "_work")}
        spec.setdefault("cut_whoosh_gap", 3.0)
        path = out / f"short_{c['name']}.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
        before = sum(float(r[1]) - float(r[0]) for r in c["ranges"])
        after = sum(e - s for s, e, _, _ in ranges)
        print(f"{c['name']:40} {before:6.1f}s -> {after:6.1f}s  {len(ranges)} ranges  {path.name}")


if __name__ == "__main__":
    main()
