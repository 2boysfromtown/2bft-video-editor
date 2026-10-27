---
name: ffmpeg-edit-toolkit
description: Do the actual cutting, mixing and exporting with ffmpeg - remove silences and dead air (automatic jump cuts), trim, join, punch-in zooms, speed ramps, J-cuts and L-cuts, dissolves, timed overlays, burned-in captions, placing sound effects, ducking music under a voice, voice cleanup, loudness normalising and delivery encodes. Includes tested recipes and two scripts (remove_silence.py, make_sfx.py). Use when asked to cut, tighten, trim, join, speed up, add music or sound effects, normalise audio, or export a video, or whenever another editing skill needs a command to carry out its plan.
---

# ffmpeg edit toolkit

The hands for the editing skills. `edit-video` decides what to do; the craft skills say why; this one has the commands that do it. Every recipe in `references/recipes.md` was run on ffmpeg 9.0.2 and the results checked, not just parsed.

## Ground rules

- **Never overwrite the source.** Write every result to a new file in an `edits/` folder next to it (`name_v1.mp4`, `name_v2.mp4`).
- **Probe before cutting:** `ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height,r_frame_rate -of compact in.mp4`
- **Re-encode once.** Stream copy (`-c copy`) is only for rough trims on keyframes. Do all filtering in one pass, then one final encode.
- **Check the result, don't assume it.** After each render: ffprobe the duration (does it equal what the plan says?), pull 2-3 frames with `-ss T -frames:v 1` and look at them, and for audio changes measure with `volumedetect` or `loudnorm ... print_format=json`.
- **Long files:** over ~30 minutes, say what the render will take and ask before starting.

## Windows / PowerShell notes

- Put filtergraphs in double quotes and use single quotes inside for expressions: `-filter_complex "[0:a]volume='clip(t/3,0,1)':eval=frame[a]"`. Avoid `$` inside the graph.
- Very long graphs (many cuts) overflow the command line. This ffmpeg no longer has `-filter_complex_script`; write the graph to a file and use `-/filter_complex graph.txt`.
- Needs `ffmpeg` and `ffprobe` on PATH and Python 3.9+ (standard library only). A terminal opened before installing ffmpeg may need restarting.

## Scripts

Run with `python -I <script>`.

| Script | What it does |
|---|---|
| `scripts/remove_silence.py in out` | Detects pauses and cuts them out, keeping a small pad so words aren't clipped. Prints original vs kept length and cuts per minute. `--dry-run` shows the keep-list first. Tune `--noise` (-35 dB default; use -30 in noisy rooms, -45 if it cuts too much) and `--min-silence` (0.4 s default; raise to keep natural breathing room). Works on video or audio. |
| `scripts/make_sfx.py kind out.wav` | Generates placeholder `whoosh`, `riser`, `hit`, `pop`, `tick` sounds so a rough cut has sound before real assets are chosen. Replace with real sounds for the final mix. |

For transcript-driven cuts (remove a sentence, cut a filler word): run `transcribe-local`, pick the time ranges from its `[MM:SS]` lines, then build the keep-list as trim/concat (recipe "Cut list").

## Recipes

See `references/recipes.md`: inspect, trim, cut list, dead air, punch-in zoom, speed ramp and slow-mo, J-cut and L-cut, dissolve and fade, timed overlay, burned-in captions, voice chain, music EQ pocket and ducking, reverb tail, reversed riser, panning, placing and synthesising sound effects, mixing onto video, loudness, and delivery encodes.

For vertical Shorts use `long-to-shorts`. For code-built graphics use Remotion or GSAP (and their Claude skills, if installed).
