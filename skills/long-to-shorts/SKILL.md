---
name: long-to-shorts
description: Turn a long recording (screen capture with face cams, a podcast, a call, a stream of your own) into ready-to-post vertical 1080x1920 Shorts/Reels/TikToks - pick the best moments from the transcript, cut the dead air, lay out hook, content pane, face cams, captions and CTA, add synthesised music and sound effects, render with ffmpeg. Use when the user wants Shorts or Reels cut from a long video, "clip the best parts", or a vertical version with captions and a hook.
---

# Long recording to Shorts

Claude reads the transcript, picks the moments, writes a plan, and these scripts do the cutting and rendering. Everything is driven by JSON; times are SOURCE seconds. Only use footage of people who agreed to appear.

## Needs

ffmpeg on PATH, Python 3.9+, `pip install numpy pillow`. Fonts: it uses Segoe UI / Impact / Arial / DejaVu if found; set `CLIPKIT_FONTS=/path/to/fonts` or `"fonts_dir"` in the spec to use your own. Music and effects are synthesised by `synth_audio.py` (no samples, no copyright).

## Workflow

1. **Transcribe** the long file with `transcribe-local`. Read it all.
2. **Pick 30-60 s moments** that stand alone: a hook in the first line, a payoff, no needed context. Prefer a surprising claim, a number, a funny reaction, a clear how-to step.
3. **Find the layout** in the source: pull a frame (`ffmpeg -ss T -i in.mp4 -frames:v 1 f.png`), look at it, and note pixel rects for the content area and each face cam.
4. **Write `plan.json`** (format in the docstring of `scripts/make_shorts_spec.py`): per clip a name, hook (a question or claim, under 8 words), `ranges` ([start, end, rect_name, tight]), captions (short lines timed to the audio), a few `sfx` on the punchline, a `cta`.
5. **Generate specs**: `python -I scripts/make_shorts_spec.py plan.json` splits each talk range at its pauses (dead air removed) and writes one spec per Short into `_specs/`.
6. **Render**: `python -I scripts/build_react_short.py _specs/short_<name>.json --out out/` (face-cam layout, `"cams"` in the plan) or `scripts/clipkit.py` for the two-pane layout (`top`/`bottom` keys, see its docstring). You get `<name>.mp4` (1080x1920, H.264, -14 LUFS) and `<name>.srt`.
7. **Check**: pull frames across the Short and look at them, transcribe the output, proofread every caption, say which sounds are synthesised placeholders. A person must watch and listen before posting: the agent cannot hear the audio or judge whether a joke lands.

## Spec features

Hook box sliding in, progress bar, caption pill on the seam, zoom punch-ins (`zooms`), time-lapse ranges (speed > 1, muted), blurred panes for people who must not be recognisable (`"blur": true`), whooshes on jumps, side-chain ducked music, CTA, watermark.

## Tools in `scripts/`

| File | Role |
|---|---|
| `make_shorts_spec.py` | plan.json -> one spec per Short, auto-tightening the talk |
| `build_react_short.py` | face-cam + content pane layout renderer |
| `clipkit.py` | two-pane layout renderer and the shared toolkit (captions, hook, timeline) |
| `synth_audio.py` | numpy-synthesised music beds (`groove`, `bounce`) and effects (`whoosh hit pop ding boing riser airhorn`) |

A runnable example on synthetic footage is in `examples/04-shorts-from-a-long-recording` of this repo.
