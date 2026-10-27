#!/usr/bin/env python3
"""Measure the pacing of an edit from its cut times.

Cut times come from one of:
  --video FILE      detect cuts with ffmpeg scene detection (needs ffmpeg/ffprobe)
  --cuts 1.5,3,4.2  a comma/space separated list of cut times in seconds
  --edl FILE        text/CSV file; first column of every non-comment line is a cut time (s)

Reports cuts, cuts per minute (overall and per window), shot-length stats,
flat stretches with no cut, the tempo trend, the hook check, and with --bpm
how well the cuts sit on the beat grid. Pure standard library.

Examples:
  python -I pacing_report.py --video edits/reel_v1.mp4
  python -I pacing_report.py --cuts 0.5,1,1.5,2,4,8,9 --duration 12 --bpm 120
"""
import argparse
import json
import re
import statistics
import subprocess
import sys


def out(*a):
    print(*a)


def probe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        sys.exit("ffprobe could not read the duration of " + path)


def detect_cuts(path, threshold):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vf",
           f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return sorted(float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr))


def load_edl(path):
    times = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            first = re.split(r"[,\s;]+", line)[0]
            try:
                times.append(float(first))
            except ValueError:
                continue  # header row
    return sorted(times)


def parse_list(s):
    return sorted(float(x) for x in re.split(r"[,\s;]+", s.strip()) if x)


def grid_step(bpm, grid):
    beat = 60.0 / bpm
    return {"bar": beat * 4, "beat": beat, "half": beat / 2,
            "quarter": beat / 4}[grid]


def build(args):
    if args.video:
        dur = args.duration or probe_duration(args.video)
        cuts = detect_cuts(args.video, args.scene)
    elif args.edl:
        cuts = load_edl(args.edl)
        dur = args.duration or (max(cuts) if cuts else 0)
    elif args.cuts:
        cuts = parse_list(args.cuts)
        dur = args.duration or (max(cuts) if cuts else 0)
    else:
        sys.exit("give --video, --cuts or --edl")
    cuts = [c for c in cuts if 0.05 < c < dur - 0.05]
    # drop detector duplicates closer than 3 frames at 30 fps
    clean = []
    for c in cuts:
        if not clean or c - clean[-1] >= 0.1:
            clean.append(c)
    return clean, dur


def analyse(cuts, dur, args):
    bounds = [0.0] + cuts + [dur]
    shots = [b - a for a, b in zip(bounds, bounds[1:])]
    res = {"duration_s": round(dur, 2), "cuts": len(cuts),
           "cpm_overall": round(len(cuts) / dur * 60, 1) if dur else 0}

    res["shot_length_s"] = {
        "min": round(min(shots), 2), "median": round(statistics.median(shots), 2),
        "mean": round(statistics.mean(shots), 2), "max": round(max(shots), 2)}

    # per-window CPM
    w = args.window or (5.0 if dur <= 60 else 10.0 if dur <= 300 else 30.0)
    args.window = w
    wins = []
    t = 0.0
    while t < dur - 1e-6:
        end = min(t + w, dur)
        n = sum(1 for c in cuts if t <= c < end)
        span = end - t
        wins.append({"from": round(t, 1), "to": round(end, 1), "cuts": n,
                     "cpm": round(n / span * 60, 1)})
        t += w
    res["windows"] = wins

    cpms = [x["cpm"] for x in wins if (x["to"] - x["from"]) >= w * 0.6]
    notes = []
    if len(cpms) >= 3:
        mean = statistics.mean(cpms)
        sd = statistics.pstdev(cpms)
        cv = sd / mean if mean else 0
        k = max(1, len(cpms) // 3)
        head, tail = statistics.mean(cpms[:k]), statistics.mean(cpms[-k:])
        if cv < 0.25:
            trend = "flat: one even speed"
            notes.append("Tempo barely varies. Plan one acceleration or brake and one breath.")
        elif tail > head * 1.4:
            trend = "accelerating"
        elif head > tail * 1.4:
            trend = "decelerating"
        else:
            trend = "wave: fast and slow stretches"
        res["tempo"] = {"trend": trend, "cpm_mean": round(mean, 1),
                        "cpm_variation": round(cv, 2),
                        "cpm_start": round(head, 1), "cpm_end": round(tail, 1)}
    else:
        res["tempo"] = {"trend": "too short to judge (need 3+ full windows; try a smaller --window)"}

    # flat stretches
    flat = []
    for a, b in zip(bounds, bounds[1:]):
        if b - a > args.flat:
            flat.append({"from": round(a, 2), "to": round(b, 2), "length_s": round(b - a, 2)})
    res["no_cut_longer_than_%gs" % args.flat] = flat
    if flat:
        notes.append(f"{len(flat)} stretch(es) with no cut over {args.flat:g}s: fine only if something "
                     "moves (counter, push, drawn line, source camera) or it is a planned reading hold.")

    # hook
    first = cuts[0] if cuts else dur
    in3 = sum(1 for c in cuts if c <= 3.0)
    res["hook"] = {"first_cut_s": round(first, 2), "cuts_in_first_3s": in3}
    if first > 3.0:
        notes.append(f"First cut at {first:.1f}s. Check that the opening is an event, not a slow reveal.")

    # very short shots
    tiny = [round(s, 3) for s in shots if s < 0.1]
    if tiny:
        notes.append(f"{len(tiny)} shot(s) under 0.1s (3 frames at 30fps): likely detector noise or flashes.")

    # grid
    if args.bpm:
        step = grid_step(args.bpm, args.grid)
        tol = args.tol / 1000.0
        errs = []
        for c in cuts:
            k = round((c - args.offset) / step)
            snapped = args.offset + k * step
            errs.append((c, (c - snapped) * 1000.0))
        on = [e for e in errs if abs(e[1]) <= args.tol]
        worst = sorted(errs, key=lambda e: -abs(e[1]))[:5]
        res["grid"] = {
            "bpm": args.bpm, "grid": args.grid, "offset_s": args.offset,
            "tolerance_ms": args.tol,
            "on_grid": f"{len(on)}/{len(errs)}",
            "on_grid_pct": round(100 * len(on) / len(errs), 1) if errs else 0,
            "worst": [{"t": round(c, 3), "error_ms": round(e, 1)} for c, e in worst]}
        if errs and len(on) / len(errs) < 0.8:
            notes.append("Fewer than 80% of cuts sit on the grid. Wrong BPM/offset, or snap them with editgrid.py snap.")

    res["notes"] = notes
    return res


def show(res, args):
    out(f"Duration {res['duration_s']} s   cuts {res['cuts']}   overall {res['cpm_overall']} CPM")
    s = res["shot_length_s"]
    out(f"Shot length  min {s['min']}  median {s['median']}  mean {s['mean']}  max {s['max']} s")
    t = res["tempo"]
    out(f"Tempo        {t['trend']}" + (
        f"  (window CPM mean {t['cpm_mean']}, variation {t['cpm_variation']}, "
        f"start {t['cpm_start']} -> end {t['cpm_end']})" if 'cpm_mean' in t else ""))
    h = res["hook"]
    out(f"Hook         first cut {h['first_cut_s']} s, {h['cuts_in_first_3s']} cut(s) in first 3 s")
    out("")
    out(f"CPM by {args.window:g}-second window:")
    peak = max([w["cpm"] for w in res["windows"]] + [1])
    for w in res["windows"]:
        bar = "#" * int(round(30 * w["cpm"] / peak))
        part = "  (partial)" if (w["to"] - w["from"]) < args.window * 0.6 else ""
        out(f"  {w['from']:7.1f}-{w['to']:<7.1f} {w['cuts']:3d} cuts {w['cpm']:6.1f} CPM  {bar}{part}")
    key = [k for k in res if k.startswith("no_cut")][0]
    if res[key]:
        out("")
        out(f"Stretches with no cut over {args.flat:g} s:")
        for f in res[key]:
            out(f"  {f['from']:.1f} -> {f['to']:.1f}  ({f['length_s']} s)")
    if "grid" in res:
        g = res["grid"]
        out("")
        out(f"Grid {g['bpm']} BPM, {g['grid']} subdivision, offset {g['offset_s']} s, "
            f"tolerance {g['tolerance_ms']} ms: {g['on_grid']} on grid ({g['on_grid_pct']} %)")
        for w in g["worst"]:
            out(f"  worst: {w['t']} s off by {w['error_ms']:+} ms")
    if res["notes"]:
        out("")
        out("Observations:")
        for n in res["notes"]:
            out("  - " + n)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--video")
    p.add_argument("--cuts")
    p.add_argument("--edl")
    p.add_argument("--duration", type=float, help="total length in s (required for --cuts if the last shot matters)")
    p.add_argument("--scene", type=float, default=0.3, help="scene-detect threshold 0-1 (default 0.3; lower finds more cuts)")
    p.add_argument("--window", type=float, default=None,
                   help="CPM window in s (default: 5 s up to 60 s long, 10 s up to 5 min, else 30 s)")
    p.add_argument("--flat", type=float, default=4.0, help="flag shots longer than this many s (default 4)")
    p.add_argument("--bpm", type=float, help="check cuts against a beat grid")
    p.add_argument("--grid", choices=["bar", "beat", "half", "quarter"], default="half")
    p.add_argument("--offset", type=float, default=0.0, help="time of beat 0 in s (default 0)")
    p.add_argument("--tol", type=float, default=40.0, help="grid tolerance in ms (default 40)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    cuts, dur = build(args)
    if dur <= 0:
        sys.exit("duration is 0: pass --duration")
    res = analyse(cuts, dur, args)
    if args.json:
        res["cut_times"] = [round(c, 3) for c in cuts]
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        show(res, args)


if __name__ == "__main__":
    main()
