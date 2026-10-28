---
name: 2bft-video-editor
description: The 2BFT video editor for Claude Code - turns raw talking-head, webcam, screen-recording or live-stream footage into finished YouTube videos and vertical Shorts/Reels, with face tracking first - auto-reframe 16:9 to 9:16 so the crop follows the speaker's face, webcam crops that follow the face, energy-reactive camera shake measured from voice and movement, pause and filler tightening measured from the audio, captions, sound effects and music sourced with their licences (including trending songs), offline noise removal, stem splitting and background removal, music ducking, -14 LUFS masters and automatic QC. Use when the user says edit this video, make Shorts or Reels from this, reframe to vertical, follow my face, auto reframe, face tracking, keep me in frame, make it punchy, add captions or shake, cut the pauses, or hands over a recording and wants it finished.
---

# 2BFT video editor

The entry point for the whole pack. It decides the order of work and calls the right tool or skill. Face tracking comes first because every vertical deliverable depends on it: if the face drifts out of the crop, nothing else matters.

## What this pack can and can't do

- **Can:** track faces (OpenCV YuNet), reframe any video to 9:16 / 4:5 / 1:1 with a smooth face-following crop, measure voice and movement energy, transcribe offline with word timings, cut pauses by measured noise floor, render captions, graphics, SFX and music, master to -14 LUFS, and run automatic QC.
- **Can't:** hear or watch playback, or feel whether a joke lands. Make the measurable decisions, then ask the user to watch and listen.
- **Must not:** overwrite the source, invent numbers or quotes, bake commercial songs into an export, or show strangers who did not agree to be filmed (blur them).

## Priority 1: face tracking and reframing

### Auto-reframe (horizontal to vertical, face-following)

```
python -I skills/2bft-video-editor/scripts/reframe.py in.mp4 out_9x16.mp4
python -I skills/2bft-video-editor/scripts/reframe.py stream.mp4 cam_9x16.mp4 --region 1476,154,384,768 --zoom 1.7
python -I skills/2bft-video-editor/scripts/reframe.py in.mp4 compare.mp4 --compare --dur 20     # static vs tracked, side by side
```

- `--region x,y,w,h` limits tracking and cropping to one part of the frame (the webcam box of a stream layout). Measure it from one frame: `ffmpeg -ss 60 -i in.mp4 -frames:v 1 frame.png`, then check your crop with `-vf crop=w:h:x:y`.
- `--zoom` 1.0 is the widest crop of that aspect; 1.5-1.8 is a close-up. Above about 2.5x of the source pixels the picture goes soft: say so rather than push further.
- `--eyes 0.40` puts the eye line a little above centre (talking-head convention). Use 0.35 for more headroom, 0.45 for tight close-ups.
- `--track-json` saves the smoothed track so other tools (captions that avoid the face, punch-ins) can reuse it.
- Always look at the result: pull frames at the moments the person moves most (`--compare` makes this obvious). The script prints the share of samples where a face was found; under about 80 % means a bad region, backlight or a turned head, so check those stretches.

How the "camera operator" behaves: detect at 10 fps, keep the most confident and largest face (posters and photos on the wall are smaller and lose), fill gaps up to 2 s, median filter against false hits, Gaussian smoothing, a deadzone so the crop holds still until the face really moves, then a second smoothing pass. Tune in `SMOOTH` at the top of the script.

### Webcam crops that follow the face inside a full edit

For stream layouts (screen + webcam), `quest-lab-editor` runs `engine/tools/face_track.py` on the webcam box during project setup; its `build.py` turns the face's deviation from the usual seated position into a per-frame offset, so hand-made crops keep their composition and only move when the person moves.

### More picture tools

- Smile, mouth-open and blink moments (for punch-ins and laughs), body and hand tracking: `local-av-tools/scripts/track.py`.
- Cut the speaker out with no green screen (ProRes 4444 alpha or WebM): `local-av-tools/scripts/cutout.py`.
- Smooth 24/30 fps footage to 60, or slow motion: `local-av-tools/scripts/interpolate.py`.
- Hand-off to a DaVinci Resolve timeline through Blackmagic's MCP, plus free add-ons: `local-av-tools/references/davinci-resolve.md`.

### Setup for face tracking

- Python with `numpy` and `opencv-python>=4.8` (`pip install numpy opencv-python`).
- The YuNet model `face_detection_yunet_2023mar.onnx` from the OpenCV model zoo (MIT): download it once, then set `REFRAME_YUNET` (for `reframe.py`) and `QL_YUNET` (for `quest-lab-editor`) to its path, or put it in `./models/`.
- ffmpeg and ffprobe on PATH.

## Priority 2: energy, pace and sound

| Job | Tool |
|---|---|
| Energy map (voice loudness + movement) driving camera rumble, shake and impacts, with budgets | `quest-lab-editor/engine/tools/energy.py`, rules in `quest-lab-editor/references/energy-shake.md` |
| Tighten pauses from the measured noise floor (gap table per format; fillers and retakes listed, never auto-cut) | `quest-lab-editor/engine/tools/pauses.py`, `quest-lab-editor/references/cutting.md` |
| Quick automatic jump cuts on any file | `ffmpeg-edit-toolkit/scripts/remove_silence.py` |
| Pacing numbers (cuts per minute, flat stretches, hook timing, beat-grid fit) | `editor-os/scripts/pacing_report.py` |
| Sound effects by rule, echo throws, music cut to drops, ducking, -14 LUFS | `quest-lab-editor/references/captions-sfx-voicefx.md`, `video-sound-and-music` |
| Find music, SFX, meme sounds, trending songs (India + global charts), B-roll, fonts, with licence and credit recorded | `asset-library` (`find_assets.py`, `trending.py`, `fetch_asset.py`; ask before every download) |
| Clean the voice (fan, hum, traffic) before transcribing and mixing | `local-av-tools/scripts/denoise.py` |
| Pull music out from under a voice, or split a song into stems for beat cuts | `local-av-tools/scripts/stems.py` (`--two` = voice + music) |
| Instrumental / karaoke version (personal use only) | `local-av-tools/scripts/karaoke.py` |
| Who speaks when (podcasts, two-person streams) and speaker-labelled captions | `local-av-tools/scripts/diarize.py` |
| Cuts per minute of a reference reel, contact sheet of every shot | `local-av-tools/scripts/shots.py --sheet` |

## Priority 3: words on screen

- Offline transcript with word timings: `transcribe-local`, or `quest-lab-editor/engine/tools/transcribe_words.py` (Hindi/Hinglish/English, glossary, hallucination filter).
- Shorts captions in short chunks, edited for meaning (deletions fine, additions never). Long-form: only a handful of key-line slams.
- Text behind the speaker and karaoke captions: `talking-head-polish`.
- Subtitle timing check (Netflix-style gaps, durations, reading speed): `quest-lab-editor/engine/tools/check_srt.py`.

## The order of work

1. **Watch:** probe, transcribe, contact sheets every 10 s, read all of it. Map the layout (where the face and screen sit).
2. **Track:** run face tracking on every region a face appears in; check the hit rate and the stretches where it drops.
3. **Plan:** pick the moments (hook in the first 3 seconds), write a one-screen plan per deliverable (`editor-os` styles, `quest-lab-editor/templates/director-pass.md`).
4. **Cut:** story first on the transcript, then pause tightening.
5. **Picture:** reframe to the delivery aspect with the face track; punch-ins on peaks (max about 1.2x on top of an already-enlarged webcam).
6. **Words, then sound, then energy** as in the tables above.
7. **QC:** `quest-lab-editor/engine/tools/qa_detect.py` (black/frozen/silent stretches, loudness, flashes), frames at the biggest movements, `check_srt.py` on every SRT. Then ask a human to watch and listen.
8. **Report:** what changed, the numbers (length before/after, face hit rate, LUFS), what is a placeholder, what a human must still check.

## Skills in this pack

`2bft-video-editor` (this) · `quest-lab-editor` (the full stream-to-video engine and house style) · `asset-library` (where to get music, SFX, memes, trending songs, B-roll, fonts) · `local-av-tools` (denoise, stems, karaoke, cutout, slow-mo, shot and speaker detection) · `editor-os` · `edit-video` · `video-editing-craft` · `comedy-editing-timing` · `video-sound-and-music` · `motion-graphics-for-video` · `ffmpeg-edit-toolkit` · `transcribe-local` · `long-to-shorts` · `talking-head-polish`
