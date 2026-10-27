#!/usr/bin/env python3
"""Beat-grid maths, cut snapping and reading-time for edits. Pure standard library.

  editgrid.py beats --bpm 120 --fps 30 [--bars 8] [--offset 0]
      Table of bar.beat, time in s and frame number; says whether the beat is
      a whole number of frames.

  editgrid.py snap  --bpm 120 --fps 30 [--grid half] [--offset 0] T1 T2 ...
      Snap times (s) to the nearest grid line; shows the shift in ms.
      --grid: bar | beat | half | quarter

  editgrid.py read "text" [--spoken 2.4]
      Minimum on-screen hold for a caption: letters/15 + 1.5 s (Latin),
      characters/4.5 + 1.5 s (CJK), Indic scripts counted like Latin +20 %.
      Never below 1.8 s, and never below spoken + 0.6 s when --spoken is given.
"""
import argparse
import sys
import unicodedata


def step(bpm, grid):
    beat = 60.0 / bpm
    return {"bar": beat * 4, "beat": beat, "half": beat / 2, "quarter": beat / 4}[grid]


def cmd_beats(a):
    beat = 60.0 / a.bpm
    fpb = a.fps * beat
    whole = abs(fpb - round(fpb)) < 1e-6
    print(f"{a.bpm:g} BPM  beat {beat:.4f} s = {fpb:.3f} frames at {a.fps:g} fps "
          f"({'whole number of frames' if whole else 'NOT a whole number of frames'})")
    print(f"bar {beat*4:.4f} s   half-beat {beat/2:.4f} s   sixteenth {beat/4:.4f} s")
    if not whole:
        good = [b for b in (60, 72, 80, 90, 96, 100, 108, 112.5, 120, 125, 135, 144, 150, 160)
                if abs(a.fps * 60 / b - round(a.fps * 60 / b)) < 1e-6]
        print(f"tempos with whole-frame beats at {a.fps:g} fps: {', '.join(f'{g:g}' for g in good)}")
    print()
    print(f"{'bar.beat':>8} {'time_s':>9} {'frame':>7}")
    for bar in range(a.bars):
        for b in range(4):
            t = a.offset + (bar * 4 + b) * beat
            print(f"{bar+1:>5}.{b+1:<2} {t:9.3f} {int(round(t*a.fps)):7d}")


def cmd_snap(a):
    s = step(a.bpm, a.grid)
    print(f"grid {a.grid} = {s*1000:.1f} ms at {a.bpm:g} BPM, offset {a.offset:g} s, {a.fps:g} fps")
    print(f"{'input_s':>9} {'snapped_s':>10} {'shift_ms':>9} {'frame':>7}  position")
    beat = 60.0 / a.bpm
    for t in a.times:
        k = round((t - a.offset) / s)
        sn = a.offset + k * s
        pos = (sn - a.offset) / beat
        bar, rem = divmod(pos, 4)
        print(f"{t:9.3f} {sn:10.3f} {(sn - t)*1000:+9.1f} {int(round(sn*a.fps)):7d}  "
              f"bar {int(bar)+1} beat {rem+1:g}")


def classify(ch):
    if ch.isspace():
        return None
    cat = unicodedata.category(ch)
    if cat[0] in "PSZC":
        return None
    o = ord(ch)
    if (0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or 0x3040 <= o <= 0x30FF
            or 0xAC00 <= o <= 0xD7AF or 0xF900 <= o <= 0xFAFF):
        return "cjk"
    if 0x0900 <= o <= 0x097F or 0x0B80 <= o <= 0x0BFF or 0x0C00 <= o <= 0x0DFF:
        return "indic"
    return "latin"


def cmd_read(a):
    counts = {"cjk": 0, "indic": 0, "latin": 0}
    for ch in a.text:
        c = classify(ch)
        if c:
            counts[c] += 1
    hold = counts["cjk"] / 4.5 + counts["latin"] / 15 + counts["indic"] / 15 * 1.2 + 1.5
    floor = 1.8
    if a.spoken:
        floor = max(floor, a.spoken + 0.6)
    final = max(hold, floor)
    print(f"characters: latin {counts['latin']}, cjk {counts['cjk']}, indic {counts['indic']}")
    print(f"reading time {hold:.2f} s   floor {floor:.2f} s   hold at least {final:.2f} s")
    words = len(a.text.split())
    if counts["latin"] and words > 8:
        print(f"note: {words} words; caption-first captions work best at 6-8 words per line, split if longer")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("beats")
    b.add_argument("--bpm", type=float, required=True)
    b.add_argument("--fps", type=float, default=30)
    b.add_argument("--bars", type=int, default=8)
    b.add_argument("--offset", type=float, default=0.0)
    b.set_defaults(fn=cmd_beats)

    s = sub.add_parser("snap")
    s.add_argument("--bpm", type=float, required=True)
    s.add_argument("--fps", type=float, default=30)
    s.add_argument("--grid", choices=["bar", "beat", "half", "quarter"], default="half")
    s.add_argument("--offset", type=float, default=0.0)
    s.add_argument("times", type=float, nargs="+")
    s.set_defaults(fn=cmd_snap)

    r = sub.add_parser("read")
    r.add_argument("text")
    r.add_argument("--spoken", type=float, help="length of the spoken line in s")
    r.set_defaults(fn=cmd_read)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
