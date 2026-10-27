"""clipkit.py <spec.json> [--out DIR]

Builds one vertical 1080x1920 Short from a long side-by-side recording (a video call,
a podcast with two cameras, a screen plus a webcam...). It is also the shared toolkit
(caption, hook and tag images, the source-to-output Timeline) used by build_react_short.py.

Layout: progress bar on top, hook title, TOP pane, BOTTOM pane, caption pill on the seam
between them, a call-to-action near the end, optional watermark. Everything is driven by
the spec; times in the spec are SOURCE seconds.

Spec keys (see examples/04-shorts-from-a-long-recording for a working one):
  name, src                     output name, source video
  top / bottom                  {"rect": [x, y, w, h], "focus": [fx, fy], "blur": false, "label": ""}
                                rect = the area of the source frame shown in that pane
  ranges                        [[src_start, src_end, speed], ...]  speed > 1 = silent time-lapse
  captions                      [[src_start, src_end, "text"], ...]
  hook, hook_secs               big title at the start
  cta, cta_secs                 call to action at the end
  zooms                         [{"pane": "top"|"bottom", "t0": s, "t1": s, "amount": 0.15}]
  sfx                           [{"t": src_s | "out": out_s, "kind": "hit|pop|whoosh|ding|boing|riser|airhorn", "gain": 0.6}]
  music                         {"style": "groove"|"bounce", "bpm": 90, "gain_db": -9}  (synthesised, copyright-free)
  cut_whoosh, cut_whoosh_gap    whoosh on every jump of more than N source seconds
  watermark, accent             optional text; accent colour as 0xRRGGBB
  fonts_dir                     optional folder with .ttf files to prefer

Needs: ffmpeg on PATH, Python 3.9+ with numpy and Pillow.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import synth_audio as sa  # noqa: E402

W, H = 1080, 1920
PANE_W, PANE_H = 1080, 818
Y_TOP, Y_BOTTOM = 200, 1024
FPS = 30
ACCENT = "0xa855f7"

# ------------------------------------------------------------------ fonts (any OS)
FONT_DIRS = [Path(os.environ["CLIPKIT_FONTS"])] if os.environ.get("CLIPKIT_FONTS") else []
FONT_DIRS += [Path("C:/Windows/Fonts"), Path("/Library/Fonts"), Path("/System/Library/Fonts"),
              Path("/System/Library/Fonts/Supplemental"), Path.home() / ".fonts",
              Path("/usr/share/fonts/truetype/dejavu"), Path("/usr/share/fonts/TTF"), Path("/usr/share/fonts")]
FONT_CHOICES = {
    "bold": ["segoeuib.ttf", "Arial Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"],
    "display": ["impact.ttf", "Impact.ttf", "segoeuib.ttf", "Arial Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"],
    "tag": ["bahnschrift.ttf", "segoeui.ttf", "Arial.ttf", "arial.ttf", "DejaVuSans.ttf"],
    "emoji": ["seguiemj.ttf"],  # colour emoji at any size; elsewhere emoji fall back to the text font
}
_cache: dict = {}


def set_fonts_dir(path: str | None):
    if path:
        FONT_DIRS.insert(0, Path(path))
        _cache.clear()


def _font(role, size):
    key = (role, size)
    if key in _cache:
        return _cache[key]
    for name in FONT_CHOICES[role]:
        for d in FONT_DIRS:
            p = d / name
            if p.exists():
                _cache[key] = ImageFont.truetype(str(p), size)
                return _cache[key]
    _cache[key] = None if role == "emoji" else ImageFont.load_default(size)
    return _cache[key]


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise SystemExit(f"command failed: {' '.join(map(str, cmd[:6]))} ...\n{r.stderr[-1800:]}")
    return r


# ------------------------------------------------------------------ images
def _is_emoji(ch):
    o = ord(ch)
    return o >= 0x1F000 or 0x2600 <= o <= 0x27BF or 0x2300 <= o <= 0x23FF or 0x2B00 <= o <= 0x2BFF or o in (0xFE0F, 0x200D)


FALLBACK_CHARS = "\u20b9"   # display fonts often lack the rupee sign; draw it with the bold font


def _glyph_font(ch, f_text):
    return _font("bold", int(f_text.size)) if ch in FALLBACK_CHARS else f_text


def _pick(ch, f_text, f_emoji):
    if _is_emoji(ch):
        return f_emoji or f_text, f_emoji is not None
    return _glyph_font(ch, f_text), False


def _text_width(draw, text, f_text, f_emoji):
    return sum(draw.textlength(ch, font=_pick(ch, f_text, f_emoji)[0]) for ch in text if ch != "\ufe0f")


def _draw_mixed(img, xy, text, f_text, f_emoji, fill, stroke=0, stroke_fill=(0, 0, 0, 255)):
    d = ImageDraw.Draw(img)
    x, y = xy
    for ch in text:
        if ch == "\ufe0f":
            continue
        f, colour = _pick(ch, f_text, f_emoji)
        if colour:
            d.text((x, y + 4), ch, font=f, embedded_color=True)
        else:
            d.text((x, y), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += d.textlength(ch, font=f)


def _wrap(draw, text, f_text, f_emoji, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if _text_width(draw, trial, f_text, f_emoji) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def caption_png(text, path):
    f_text, f_emoji = _font("bold", 54), _font("emoji", 48)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines = _wrap(probe, text, f_text, f_emoji, 800)
    lh = 68
    tw = max(_text_width(probe, ln, f_text, f_emoji) for ln in lines)
    box_w, box_h = int(tw + 90), int(len(lines) * lh + 36)
    img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, box_w - 1, box_h - 1), radius=26, fill=(14, 11, 26, 226))
    d.rounded_rectangle((0, 0, 11, box_h - 1), radius=6, fill=(255, 200, 0, 255))
    for i, ln in enumerate(lines):
        lw = _text_width(d, ln, f_text, f_emoji)
        _draw_mixed(img, (22 + (box_w - 22 - lw) / 2, 16 + i * lh), ln, f_text, f_emoji, (255, 255, 255, 255))
    img.save(path)
    return img.size


def hook_png(text, path, accent=ACCENT):
    f_text, f_emoji = _font("display", 66), _font("emoji", 56)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines = _wrap(probe, text.upper(), f_text, f_emoji, 880)
    lh = 78
    tw = max(_text_width(probe, ln, f_text, f_emoji) for ln in lines)
    box_w, box_h = int(tw + 70), int(len(lines) * lh + 30)
    img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rgb = tuple(int(accent[i:i + 2], 16) for i in (2, 4, 6))
    d.rounded_rectangle((0, 0, box_w - 1, box_h - 1), radius=28, fill=(*rgb, 238))
    for i, ln in enumerate(lines):
        lw = _text_width(d, ln, f_text, f_emoji)
        _draw_mixed(img, ((box_w - lw) / 2, 10 + i * lh), ln, f_text, f_emoji, (255, 255, 255, 255), stroke=3, stroke_fill=(30, 10, 60, 255))
    img.save(path)
    return img.size


def tag_png(text, path, size=30, alpha=190):
    f = _font("tag", size)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    w = int(probe.textlength(text, font=f)) + 28
    img = Image.new("RGBA", (w, size + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((14, 8), text, font=f, fill=(255, 255, 255, alpha))
    img.save(path)
    return img.size


# ------------------------------------------------------------------ timeline mapping
class Timeline:
    """ranges: [(src_start, src_end, speed)]; maps SOURCE seconds to OUTPUT seconds."""

    def __init__(self, ranges):
        self.ranges, self.offsets, acc = ranges, [], 0.0
        for s, e, sp in ranges:
            self.offsets.append(acc)
            acc += (e - s) / sp
        self.total = acc

    def _inside(self, t):
        for (s, e, sp), o in zip(self.ranges, self.offsets):
            if s <= t <= e:
                return o + (t - s) / sp
        return None

    def start(self, t):
        hit = self._inside(t)          # ranges may be out of source order (e.g. a trailer)
        if hit is not None:
            return hit
        for (s, e, sp), o in zip(self.ranges, self.offsets):
            if t <= e:
                return o + max(0.0, t - s) / sp
        return self.total

    def end(self, t):
        hit = self._inside(t)
        if hit is not None:
            return hit
        last = 0.0
        for (s, e, sp), o in zip(self.ranges, self.offsets):
            if t >= e:
                last = o + (e - s) / sp
            elif t >= s:
                return o + (t - s) / sp
            else:
                return last
        return last


def fmt_srt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"


# ------------------------------------------------------------------ two-pane builder
def build(spec_path: str, out_dir: str | None):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8-sig"))
    set_fonts_dir(spec.get("fonts_dir"))
    accent = spec.get("accent", ACCENT)
    name = spec["name"]
    src = spec["src"]
    out_dir = Path(out_dir or Path(spec_path).parent.parent)
    work = Path(spec.get("work", out_dir / "_work")) / name
    work.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    panes = {"top": spec["top"], "bottom": spec["bottom"]}

    ranges = [(float(r[0]), float(r[1]), float(r[2]) if len(r) > 2 else 1.0) for r in spec["ranges"]]
    tl = Timeline(ranges)
    D = tl.total
    a0 = max(0.0, min(r[0] for r in ranges) - 1.0)
    a1 = max(r[1] for r in ranges) + 1.0
    seg = work / "seg.mp4"
    stamp_file = work / "seg.json"
    want = {"src": src, "a0": round(a0, 3), "a1": round(a1, 3)}
    if seg.exists() and stamp_file.exists() and json.loads(stamp_file.read_text()) == want:
        print(f"[{name}] reusing working segment {a0:.1f}-{a1:.1f}s")
    else:
        print(f"[{name}] extracting working segment {a0:.1f}-{a1:.1f}s ...")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a0:.3f}", "-t", f"{a1 - a0:.3f}", "-i", src,
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", str(seg)])
        stamp_file.write_text(json.dumps(want))

    rel = [(s - a0, e - a0, sp) for s, e, sp in ranges]
    parts, vl = [], []
    for i, (s, e, sp) in enumerate(rel):
        ln = (e - s) / sp
        parts.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=(PTS-STARTPTS)/{sp:.4f}[v{i}]")
        if sp == 1.0:
            parts.append(f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.01,afade=t=out:st={ln - 0.01:.3f}:d=0.01[a{i}]")
        else:  # time-lapse: keep the video, drop the (sped-up) sound
            parts.append(f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,atempo={sp:.4f},volume=0[a{i}]")
        vl.append(f"[v{i}][a{i}]")
    parts.append("".join(vl) + f"concat=n={len(rel)}:v=1:a=1[vc][ac]")

    # ---- zoom expressions per pane (output time)
    zooms = {"top": [], "bottom": []}
    alias = {"them": "top", "me": "bottom"}
    for z in spec.get("zooms", []):
        t0, t1 = tl.start(z["t0"]), tl.end(z["t1"])
        zooms[alias.get(z["pane"], z["pane"])].append((t0, t1, z.get("amount", 0.15)))

    def zoom_expr(pane):
        zs = zooms[pane]
        if not zs:
            return None
        r = 0.22
        terms = [f"{a}*clip((t-{t0:.3f})/{r},0,1)*(1-clip((t-{max(t0 + r, t1 - r):.3f})/{r},0,1))" for t0, t1, a in zs]
        return "1+" + "+".join(terms)

    def pane_graph(label, pane, out):
        cfg = panes[pane]
        x, y, w, h = cfg["rect"]
        ze = zoom_expr(pane)
        base = f"[{label}]crop={w}:{h}:{x}:{y}"
        blur = f",gblur=sigma={spec.get('blur_sigma', 28)}:steps=2" if cfg.get("blur") else ""
        if ze:
            cx, cy = cfg.get("focus", [0.5, 0.5])
            return (f"{base},scale=w='trunc({PANE_W}*({ze})/2)*2':h=-2:eval=frame,"
                    # crop's iw/ih keep the first frame's size, so derive the scaled size from the zoom itself
                    f"crop={PANE_W}:{PANE_H}:x='({PANE_W}*({ze})-{PANE_W})*{cx}':"
                    f"y='({PANE_W}*({ze})*{h}/{w}-{PANE_H})*{cy}'{blur}[{out}]")
        return f"{base},scale={PANE_W}:{PANE_H}{blur}[{out}]"

    parts.append("[vc]split=2[s0][s1]")
    parts.append(pane_graph("s0", "top", "pt"))
    parts.append(pane_graph("s1", "bottom", "pm"))
    parts.append(f"color=c=0x0b0716:s={W}x{H}:r={FPS}:d={D:.3f}[bg]")
    parts.append(f"[bg][pt]overlay=0:{Y_TOP}[b1]")
    parts.append(f"[b1][pm]overlay=0:{Y_BOTTOM}[b2]")
    parts.append(f"[b2]drawbox=x=0:y={Y_TOP}:w={W}:h={PANE_H}:color={accent}@0.9:t=5,"
                 f"drawbox=x=0:y={Y_BOTTOM}:w={W}:h={PANE_H}:color={accent}@0.9:t=5,"
                 f"drawbox=x=48:y=40:w=984:h=10:color=white@0.22:t=fill[b3]")
    parts.append(f"color=c={accent}:s=984x10:r={FPS}:d={D:.3f},scale=w='max(2,984*t/{D:.3f})':h=10:eval=frame[pb]")
    parts.append("[b3][pb]overlay=48:40[b4]")

    # ---- image overlays (inputs after 0: seg)
    inputs, cur = [], "b4"
    idx = 1

    def add_overlay(png, enable, x, y, nxt):
        nonlocal idx, cur
        inputs.extend(["-loop", "1", "-framerate", str(FPS), "-i", str(png)])
        parts.append(f"[{idx}:v]format=rgba[im{idx}]")
        parts.append(f"[{cur}][im{idx}]overlay=x='{x}':y='{y}':enable='{enable}':format=auto[{nxt}]")
        cur = nxt
        idx += 1

    srt = []
    for k, (cs, ce, text) in enumerate(spec.get("captions", [])):
        s_o, e_o = tl.start(cs), tl.end(ce)
        if e_o - s_o < 0.25:
            continue
        png = work / f"cap_{k:02d}.png"
        cw, chh = caption_png(text, png)
        seam = Y_TOP + PANE_H + 3
        add_overlay(png, f"between(t,{s_o:.3f},{e_o:.3f})", f"({W}-w)/2",
                    f"{seam - chh // 2}+14*pow(1-clip((t-{s_o:.3f})/0.14,0,1),2)", f"c{k}")
        srt.append((s_o, e_o, text))

    if spec.get("hook"):
        png = work / "hook.png"
        hw, hh = hook_png(spec["hook"], png, accent)
        hs, he = 0.05, spec.get("hook_secs", 3.4)
        add_overlay(png, f"between(t,{hs},{he})", f"({W}-w)/2",
                    f"62-({hh}+80)*pow(1-clip((t-{hs})/0.38,0,1),3)-({hh}+80)*clip((t-{he - 0.3})/0.3,0,1)", "hook")

    if spec.get("cta"):
        png = work / "cta.png"
        cw, chh = caption_png(spec["cta"], png)
        ts = max(0.0, D - spec.get("cta_secs", 2.0))
        add_overlay(png, f"gte(t,{ts:.3f})", f"({W}-w)/2",
                    f"{Y_BOTTOM + PANE_H - chh - 40}+20*pow(1-clip((t-{ts:.3f})/0.2,0,1),2)", "cta")

    for pane, y in (("top", Y_TOP), ("bottom", Y_BOTTOM)):
        label = panes[pane].get("label") or ("FACE BLURRED" if panes[pane].get("blur") else "")
        if label:
            png = work / f"label_{pane}.png"
            tag_png(label, png, size=26, alpha=230)
            add_overlay(png, "1", "24", f"{y + 14}", f"lab_{pane}")

    if spec.get("watermark"):
        wm = work / "wm.png"
        tag_png(spec["watermark"], wm)
        add_overlay(wm, "1", f"({W}-w)/2", "1856", "wm")
    parts.append(f"[{cur}]format=yuv420p[vout]")

    # ---- audio stems
    sfx_events = []
    for ev in spec.get("sfx", []):
        t = ev["out"] if "out" in ev else tl.start(ev["t"])
        sfx_events.append((t, ev["kind"], ev.get("gain", 0.6)))
    if spec.get("cut_whoosh"):  # a whoosh on every jump to a different moment
        for i in range(1, len(ranges)):
            if ranges[i][0] - ranges[i - 1][1] > spec.get("cut_whoosh_gap", 3.0):
                sfx_events.append((max(0.0, tl.offsets[i] - 0.12), "whoosh", 0.3))
    if spec.get("hook"):
        sfx_events.append((0.05, "pop", 0.35))
    sa.write_wav(work / "sfx.wav", sa.sfx_track(sfx_events, D))
    m = spec.get("music", {"style": "groove", "bpm": 90, "gain_db": -9})
    sa.write_wav(work / "music.wav", sa.music(m["style"], D + 2, m.get("bpm")))
    inputs.extend(["-i", str(work / "music.wav"), "-i", str(work / "sfx.wav")])
    mi, si = idx, idx + 1
    gain = m.get("gain_db", -9)
    parts.append("[ac]highpass=f=70,afftdn=nr=8:nf=-35,acompressor=threshold=-27dB:ratio=3.5:attack=6:release=100:makeup=7,"
                 "alimiter=limit=0.9[voice]")
    parts.append("[voice]asplit=2[v1][v2]")
    parts.append(f"[{mi}:a]atrim=0:{D:.3f},asetpts=PTS-STARTPTS,volume={gain}dB,afade=t=in:st=0:d=0.4,"
                 f"afade=t=out:st={max(0.0, D - 1.2):.3f}:d=1.2[mus]")
    parts.append("[mus][v1]sidechaincompress=threshold=0.05:ratio=3:attack=25:release=500[md]")
    parts.append(f"[{si}:a]atrim=0:{D:.3f},asetpts=PTS-STARTPTS,volume=-3dB[fx]")
    parts.append("[v2][md][fx]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

    graph = work / "graph.txt"
    graph.write_text(";\n".join(parts), encoding="utf-8")
    final = out_dir / f"{name}.mp4"
    print(f"[{name}] rendering {D:.1f}s -> {final.name} ...")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(seg), *inputs,
           "-/filter_complex", str(graph), "-map", "[vout]", "-map", "[aout]", "-t", f"{D:.3f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(final)]
    run(cmd)

    (out_dir / f"{name}.srt").write_text(
        "\n".join(f"{n}\n{fmt_srt(s)} --> {fmt_srt(e)}\n{t}\n" for n, (s, e, t) in enumerate(srt, 1)), encoding="utf-8")
    print(f"[{name}] done: {final}")
    return final, D


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
