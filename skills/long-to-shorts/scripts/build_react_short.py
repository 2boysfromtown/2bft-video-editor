"""build_react_short.py <spec.json> [--out DIR]

Vertical 1080x1920 "reaction" Short from a long screen recording that has face cams in it:
  hook box | content pane (any part of the screen) | caption on the seam |
  one or two face cams side by side | CTA | optional site tag and watermark | progress bar on top.

Spec times are SOURCE seconds. Each range may carry its own content rect:
  "ranges": [[start, end, speed, rect_name], ...]
  "rects": {"reel": {"rect": [x, y, w, h], "mode": "fit"}, "chat": {"rect": [...], "mode": "cover"}}
  "cams":  [{"rect": [x, y, w, h], "label": "HOST"}, {"rect": [...], "label": "GUEST"}]
mode "cover" fills the pane (crops to its aspect); "fit" shows the whole rect over a blurred fill
(use it for vertical videos shown on screen).

Optional: "broll": {"start": src_s, "rect": name}  the content pane plays other footage (consumed
in order from start) while the cams and the audio stay on the talk ranges.
Other keys (hook, captions, cta, sfx, music, watermark, site_text, accent) work as in clipkit.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import clipkit as ck  # noqa: E402
import synth_audio as sa  # noqa: E402

W, H, FPS = 1080, 1920, 30
CY, CH = 170, 1060               # content pane y, height
CAM_Y, CAM_H = 1252, 405


def probe_size(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
    w, h = out.split(",")[:2]
    return int(w), int(h)


def fit_to_aspect(x, y, w, h, aspect, fw, fh):
    """Grow rect (centered) to the target aspect, clamped to the fw x fh frame."""
    cx, cy = x + w / 2, y + h / 2
    if w / h > aspect:
        h = w / aspect
    else:
        w = h * aspect
    w, h = min(w, fw), min(h, fh)
    x = min(max(0, cx - w / 2), fw - w)
    y = min(max(0, cy - h / 2), fh - h)
    return int(x) // 2 * 2, int(y) // 2 * 2, int(w) // 2 * 2, int(h) // 2 * 2


def build(spec_path, out_dir=None):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8-sig"))
    ck.set_fonts_dir(spec.get("fonts_dir"))
    accent = spec.get("accent", ck.ACCENT)
    name, src = spec["name"], spec["src"]
    out_dir = Path(out_dir or Path(spec_path).parent.parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    work = Path(spec.get("work", out_dir / "_work")) / name
    work.mkdir(parents=True, exist_ok=True)
    FW, FH = probe_size(src)

    cams = spec.get("cams", [])
    if not 1 <= len(cams) <= 2:
        raise SystemExit("spec 'cams' needs one or two entries: [{'rect': [x, y, w, h], 'label': '...'}]")
    cam_w = W // 2                         # 540x405 per cam; one cam is centred
    cam_x0 = (W - cam_w * len(cams)) // 2
    cam_rects = [fit_to_aspect(*c["rect"], cam_w / CAM_H, FW, FH) for c in cams]

    rects = spec["rects"]
    ranges = []
    for r in spec["ranges"]:
        ranges.append((float(r[0]), float(r[1]), float(r[2]) if len(r) > 2 else 1.0, r[3] if len(r) > 3 else spec.get("default_rect", "main")))
    tl = ck.Timeline([(s, e, sp) for s, e, sp, _ in ranges])
    D = tl.total

    # one fast-seeked input per range (ranges may jump around a long recording, in any order),
    # so ffmpeg never has to hold frames from one part of the file while it waits for another
    inputs, pre = [], []
    for s, e, sp, _ in ranges:
        p = min(1.0, s)
        pre.append(p)
        inputs += ["-ss", f"{s - p:.3f}", "-t", f"{e - s + p + 0.5:.3f}", "-i", src]
    n_in = len(ranges)

    br = spec.get("broll")
    if br:
        inputs += ["-ss", f"{br['start']:.3f}", "-t", f"{D + 2:.3f}", "-i", src]

    n_split = 2 + len(cams)
    parts, joins = [], []
    for i, (s, e, sp, rn) in enumerate(ranges):
        s0, e0 = pre[i], pre[i] + (e - s)
        ln = (e - s) / sp
        cam_labels = "".join(f"[r{i}c{k}]" for k in range(len(cams)))
        if br:
            rn = br.get("rect", rn)
            bo = tl.offsets[i]
            parts.append(f"[{n_in}:v]trim=start={bo:.3f}:end={bo + ln:.3f},setpts=PTS-STARTPTS,split=2[r{i}a][r{i}b]")
            parts.append(f"[{i}:v]trim=start={s0:.3f}:end={e0:.3f},setpts=(PTS-STARTPTS)/{sp:.4f},split={len(cams)}{cam_labels}"
                         if len(cams) > 1 else
                         f"[{i}:v]trim=start={s0:.3f}:end={e0:.3f},setpts=(PTS-STARTPTS)/{sp:.4f}{cam_labels}")
        else:
            parts.append(f"[{i}:v]trim=start={s0:.3f}:end={e0:.3f},setpts=(PTS-STARTPTS)/{sp:.4f},split={n_split}[r{i}a][r{i}b]{cam_labels}")
        rx, ry, rw, rh = rects[rn]["rect"]
        mode = rects[rn].get("mode", "cover")
        if mode == "fit":
            # fill: the rect itself scaled to cover the pane, blurred and dimmed
            parts.append(f"[r{i}a]crop={rw}:{rh}:{rx}:{ry},scale=w='if(gt(a,{W}/{CH}),-2,{W})':h='if(gt(a,{W}/{CH}),{CH},-2)',"
                         f"crop={W}:{CH},gblur=sigma=36,eq=brightness=-0.18[bg{i}]")
            parts.append(f"[r{i}b]crop={rw}:{rh}:{rx}:{ry},scale=w='if(gt(a,{W}/{CH}),{W},-2)':h='if(gt(a,{W}/{CH}),-2,{CH})'[fg{i}]")
            parts.append(f"[bg{i}][fg{i}]overlay=(W-w)/2:(H-h)/2[ct{i}]")
        else:
            fx, fy, fw, fh = fit_to_aspect(rx, ry, rw, rh, W / CH, FW, FH)
            parts.append(f"[r{i}a]crop={fw}:{fh}:{fx}:{fy},scale={W}:{CH}[ct{i}]")
            parts.append(f"[r{i}b]nullsink")
        parts.append(f"color=c=0x0b0716:s={W}x{H}:r={FPS}:d={ln:.3f}[cv{i}]")
        parts.append(f"[cv{i}][ct{i}]overlay=0:{CY}[k{i}_0]")
        for k, (cx, cy, cw, chh) in enumerate(cam_rects):
            parts.append(f"[r{i}c{k}]crop={cw}:{chh}:{cx}:{cy},scale={cam_w}:{CAM_H}[ca{i}_{k}]")
            last = k == len(cam_rects) - 1
            parts.append(f"[k{i}_{k}][ca{i}_{k}]overlay={cam_x0 + k * cam_w}:{CAM_Y}{':shortest=1' if last else ''}[{'comp' + str(i) if last else f'k{i}_{k + 1}'}]")
        if sp == 1.0:
            parts.append(f"[{i}:a]atrim=start={s0:.3f}:end={e0:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.01,afade=t=out:st={ln - 0.01:.3f}:d=0.01[a{i}]")
        else:
            parts.append(f"[{i}:a]atrim=start={s0:.3f}:end={e0:.3f},asetpts=PTS-STARTPTS,atempo={sp:.4f},volume=0[a{i}]")
        joins.append(f"[comp{i}][a{i}]")
    parts.append("".join(joins) + f"concat=n={len(ranges)}:v=1:a=1[vc][ac]")

    # frames, progress bar
    boxes = f"drawbox=x=0:y={CY}:w={W}:h={CH}:color={accent}@0.9:t=5"
    for k in range(len(cams)):
        boxes += f",drawbox=x={cam_x0 + k * cam_w}:y={CAM_Y}:w={cam_w}:h={CAM_H}:color={accent}@0.9:t=4"
    parts.append(f"[vc]{boxes},drawbox=x=48:y=40:w=984:h=10:color=white@0.22:t=fill[b0]")
    parts.append(f"color=c={accent}:s=984x10:r={FPS}:d={D:.3f},scale=w='max(2,984*t/{D:.3f})':h=10:eval=frame[pb]")
    parts.append("[b0][pb]overlay=48:40[b1]")

    cur, idx = "b1", n_in + (1 if br else 0)

    def add(png, enable, x, y, nxt):
        nonlocal idx, cur
        inputs.extend(["-loop", "1", "-framerate", str(FPS), "-i", str(png)])
        parts.append(f"[{idx}:v]format=rgba[im{idx}]")
        parts.append(f"[{cur}][im{idx}]overlay=x='{x}':y='{y}':enable='{enable}':format=auto[{nxt}]")
        cur, idx = nxt, idx + 1

    for k, cam in enumerate(cams):
        if cam.get("label"):
            png = work / f"name_{k}.png"
            ck.tag_png(cam["label"], png, size=26, alpha=235)
            add(png, "1", f"{cam_x0 + k * cam_w + 14}", f"{CAM_Y + CAM_H - 50}", f"nm{k}")

    srt = []
    seam = CY + CH + 1
    for k, (cs, ce, text) in enumerate(spec.get("captions", [])):
        s_o, e_o = tl.start(cs), tl.end(ce)
        if e_o - s_o < 0.25:
            continue
        png = work / f"cap_{k:02d}.png"
        cw, chh = ck.caption_png(text, png)
        add(png, f"between(t,{s_o:.3f},{e_o:.3f})", f"({W}-w)/2",
            f"{seam - chh // 2}+14*pow(1-clip((t-{s_o:.3f})/0.14,0,1),2)", f"c{k}")
        srt.append((s_o, e_o, text))

    if spec.get("hook"):
        png = work / "hook.png"
        hw, hh = ck.hook_png(spec["hook"], png, accent)
        he = spec.get("hook_secs", 3.6)
        add(png, f"between(t,0.05,{he})", f"({W}-w)/2",
            f"66-({hh}+90)*pow(1-clip((t-0.05)/0.38,0,1),3)-({hh}+90)*clip((t-{he - 0.3})/0.3,0,1)", "hook")

    if spec.get("cta"):
        png = work / "cta.png"
        cw, chh = ck.caption_png(spec["cta"], png)
        ts = max(0.0, D - spec.get("cta_secs", 3.0))
        add(png, f"gte(t,{ts:.3f})", f"({W}-w)/2", f"{CAM_Y + CAM_H + 40}+20*pow(1-clip((t-{ts:.3f})/0.2,0,1),2)", "cta")  # under the cams

    if spec.get("site_text"):
        png = work / "site.png"
        ck.tag_png(spec["site_text"], png, size=34, alpha=230)
        add(png, "1", f"({W}-w)/2", f"{CAM_Y + CAM_H + (170 if spec.get('cta') else 26)}", "site")

    if spec.get("watermark"):
        wm = work / "wm.png"
        ck.tag_png(spec["watermark"], wm)
        add(wm, "1", f"({W}-w)/2", "1856", "wm")
    parts.append(f"[{cur}]format=yuv420p[vout]")

    # audio: voice + ducked music + effects
    ev = [((e["out"] if "out" in e else tl.start(e["t"])), e["kind"], e.get("gain", 0.6)) for e in spec.get("sfx", [])]
    if spec.get("hook"):
        ev.append((0.05, "pop", 0.35))
    for i in range(1, len(ranges)):
        if ranges[i][0] - ranges[i - 1][1] > spec.get("cut_whoosh_gap", 3.0):
            ev.append((max(0.0, tl.offsets[i] - 0.12), "whoosh", 0.3))
    sa.write_wav(work / "sfx.wav", sa.sfx_track(ev, D))
    m = spec.get("music", {"style": "groove", "bpm": 90, "gain_db": -12})
    sa.write_wav(work / "music.wav", sa.music(m["style"], D + 2, m.get("bpm")))
    inputs += ["-i", str(work / "music.wav"), "-i", str(work / "sfx.wav")]
    mi, si = idx, idx + 1
    parts.append("[ac]highpass=f=70,afftdn=nr=6:nf=-38,acompressor=threshold=-27dB:ratio=3.5:attack=6:release=100:makeup=7,alimiter=limit=0.9[voice]")
    parts.append("[voice]asplit=2[v1][v2]")
    parts.append(f"[{mi}:a]atrim=0:{D:.3f},asetpts=PTS-STARTPTS,volume={m.get('gain_db', -12)}dB,afade=t=in:st=0:d=0.4,afade=t=out:st={max(0.0, D - 1.2):.3f}:d=1.2[mus]")
    parts.append("[mus][v1]sidechaincompress=threshold=0.05:ratio=3:attack=25:release=500[md]")
    parts.append(f"[{si}:a]atrim=0:{D:.3f},asetpts=PTS-STARTPTS,volume=-3dB[fx]")
    parts.append("[v2][md][fx]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

    graph = work / "graph.txt"
    graph.write_text(";\n".join(parts), encoding="utf-8")
    final = out_dir / f"{name}.mp4"
    print(f"[{name}] rendering {D:.1f}s ...")
    ck.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs, "-/filter_complex", str(graph),
            "-map", "[vout]", "-map", "[aout]", "-t", f"{D:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(final)])
    (out_dir / f"{name}.srt").write_text("\n".join(f"{n}\n{ck.fmt_srt(s)} --> {ck.fmt_srt(e)}\n{t}\n" for n, (s, e, t) in enumerate(srt, 1)), encoding="utf-8")
    print(f"[{name}] done: {final} ({D:.1f}s)")
    return final


if __name__ == "__main__":
    args = sys.argv[1:]
    out = None
    if "--out" in args:
        i = args.index("--out")
        out = args[i + 1]
        args = args[:i] + args[i + 2:]
    if not args:
        raise SystemExit(__doc__)
    build(args[0], out)
