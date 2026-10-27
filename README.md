<p align="center"><img src="media/cover.png" alt="2BFT Video Editor: face-tracked 9:16 reframe and editing skills for Claude Code" width="100%"></p>

# 2BFT Video Editor: Claude Code video editing skills with face-tracked auto reframe

**2BFT Video Editor is an open-source pack of 12 Claude Code skills that edits talking-head, webcam and live-stream footage into YouTube videos and 9:16 Shorts, with face-tracked auto reframe.** It runs on your own PC, free, MIT licensed.

**A video editor for Claude Code that keeps your face in frame.** Hand Claude a raw recording and it reframes it to 9:16 with a crop that follows your face, then cuts the pauses, adds energy-reactive shake, captions, sound effects and music, and masters to -14 LUFS. Twelve skills, one install, runs on your own PC.

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) ![Claude Code skills](https://img.shields.io/badge/Claude%20Code-skills-8A2BE2) ![Face tracking](https://img.shields.io/badge/face%20tracking-OpenCV%20YuNet-yellow) ![ffmpeg](https://img.shields.io/badge/runs%20on-ffmpeg-black) ![Offline](https://img.shields.io/badge/runs-offline-orange)

<p align="center"><img src="media/demo.gif" alt="static crop vs face-tracked crop" width="420"></p>

*Left: a fixed crop loses the speaker when he stands and leans. Right: `reframe.py` follows the face. Real webcam footage from one of our streams, not staged. Full-quality video: [`media/demo.mp4`](media/demo.mp4).*

## Install in 1 minute

```bash
npx skills add 2boysfromtown/2bft-video-editor --global --agent claude-code
```

Or as a Claude Code plugin:

```bash
claude plugin marketplace add 2boysfromtown/2bft-video-editor
claude plugin install 2bft-video-editor@2bft
```

Then the Python side:

```bash
pip install numpy "opencv-python>=4.8"
```

Download the face model `face_detection_yunet_2023mar.onnx` from the [OpenCV model zoo](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) and point `REFRAME_YUNET` at it. You need ffmpeg on PATH. Then tell Claude:

> Reframe this to a vertical Short that follows my face: `C:\videos\stream.mp4`

## Auto reframe to 9:16 with face tracking (try it without Claude)

```bash
python -I skills/2bft-video-editor/scripts/reframe.py in.mp4 out_9x16.mp4                      # whole frame -> 9:16
python -I skills/2bft-video-editor/scripts/reframe.py stream.mp4 cam.mp4 --region 1476,154,384,768 --zoom 1.7   # just the webcam box, closer
python -I skills/2bft-video-editor/scripts/reframe.py in.mp4 compare.mp4 --compare --dur 20    # static vs tracked, side by side
```

## Results (measured, not estimated)

| Test | Result |
|---|---|
| Face found in a 20 s webcam clip with two face posters on the wall | 100 % of 200 samples |
| 5 s of 1080p to a 1080x1920 face-tracked Short, with audio | 5.7 s on CPU |
| 20 s side-by-side comparison render | 8.1 s on CPU |
| A 68-minute two-person stream edited with this pack | a 38-minute YouTube cut at -14.0 LUFS plus 13 Shorts |

Worked example: [`examples/face-reframe`](examples/face-reframe).

## What's in the pack

**Face tracking first**
- **`2bft-video-editor`** (start here): the entry skill and `reframe.py`. Face-tracked reframe to 9:16, 4:5 or 1:1, with a "camera operator" smoothing chain (gap fill, median, Gaussian, deadzone) so the crop moves like a person, not a jittery tracker. Picks the real face over posters and photos.
- **`quest-lab-editor`**: our full stream-to-video engine. Webcam crops that follow the face, energy-reactive camera shake measured from voice and movement, quest HUD graphics, kinetic Hinglish or English captions, SFX and echo by rule, music cut to drops, pause tightening from the measured noise floor, Netflix-style subtitle checks and automatic pre-delivery QC (black, frozen, silent, loudness, flash safety).

**Editing craft**
- **`editor-os`**: eight edit styles, pacing targets in cuts per minute, a sound cue-sheet method, `pacing_report.py`.
- **`edit-video`**: intake, look, plan, rough cut, pacing, sound, export, QA.
- **`video-editing-craft`**, **`comedy-editing-timing`**, **`video-sound-and-music`**, **`motion-graphics-for-video`**: the decisions behind good cuts, jokes, mixes and graphics.
- **`ffmpeg-edit-toolkit`**: tested ffmpeg recipes plus `remove_silence.py` (automatic jump cuts) and `make_sfx.py`.
- **`transcribe-local`**: offline Whisper transcripts with timestamps.
- **`long-to-shorts`**: long recording to captioned 1080x1920 Shorts with hook and CTA.
- **`talking-head-polish`**: text behind the speaker and karaoke captions.

## How it works

```
recording ──► transcribe (offline Whisper) ──► face track (YuNet, 10 fps) ──► smooth (gap fill → median → Gaussian → deadzone → Gaussian)
                                                                                         │
            plan (hook, beats, style) ◄── contact sheets + energy map ◄──────────────────┘
                     │
                     ▼
   cut → tighten pauses → reframe 9:16 on the face → captions → SFX + music → energy shake → -14 LUFS → QC
```

## How it compares

| | 2BFT Video Editor | Cloud auto-clip apps (e.g. Opus Clip) | Editor apps with auto reframe (e.g. CapCut, Premiere Pro) |
|---|---|---|---|
| Face-tracked 9:16 reframe | Yes | Yes | Yes |
| Runs inside Claude Code, driven by plain-English requests | Yes | No | No |
| Your footage stays on your PC | Yes | No (uploaded) | Depends on the app |
| Open source, you can change the rules | Yes (MIT) | No | No |
| Price | Free | Free tier, then paid | Free tier or paid |
| Polished drag-and-drop interface | No (you talk to Claude) | Yes | Yes |

Pick an app if you want buttons. Pick this if you already use Claude Code, want the edit to run on your own machine, and want to change how it cuts.

## FAQ

**What is the best Claude Code skill for video editing?**
For talking-head, webcam and stream footage, this pack: one install gives Claude a full workflow (watch, transcribe, plan, cut, reframe, captions, sound, QC) plus face-tracked auto reframe. For animation and motion graphics built in code, also look at Remotion's own skills.

**How do I auto reframe a 16:9 video to 9:16 with face tracking for free?**
`python -I skills/2bft-video-editor/scripts/reframe.py in.mp4 out.mp4`. It finds the face with OpenCV's YuNet model and moves the crop smoothly to keep it in frame. Add `--region` to reframe only a webcam box.

**Does it work offline?**
Yes. Face tracking, transcription (faster-whisper) and rendering all run locally. Nothing is uploaded.

**Do I need a GPU?**
No for reframing (it ran on CPU in our tests). Transcription and the full stream engine are faster on an NVIDIA GPU.

**Does it handle Hindi, Hinglish or Tamil?**
Yes. Transcription and captions handle Hindi and Hinglish (Roman script captions) as well as English; Tanglish (Tamil in Roman letters) karaoke captions are in `talking-head-polish`.

**Can it edit a whole live stream into a YouTube video and Shorts?**
Yes, that is what `quest-lab-editor` does: one long screen + webcam recording into a chaptered YouTube cut and a set of captioned Shorts.

## Limits (read this)

- **Claude can't hear or watch playback.** It reads frames and transcripts and measures faces, levels and loudness. Whether a moment lands needs a human to watch.
- **Resolution:** a small webcam box blown up to 1080x1920 goes soft past about 2.5x. Record the webcam larger if you plan to reframe it.
- If the face is lost (turned away, backlit), the crop holds its last position and the script prints the hit rate so you can check those stretches.
- `quest-lab-editor`'s renderer needs Node 18+ and Chrome or Edge, and its transcription is fastest on an NVIDIA GPU. No music ships with the pack: use tracks you have the rights to.

## Requirements

Python 3.10+, ffmpeg, `pip install -r requirements.txt` (only `numpy` and `opencv-python` are needed for face tracking). Tested on Windows 11 with an RTX 5070 Ti; reframing runs on CPU.

## Credits

- Face detection: [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) (MIT) via OpenCV.
- Edit style grammars in `editor-os` are distilled from the [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) directing library (MIT).
- Ideas merged into `quest-lab-editor` (rewritten, not copied) are listed with their licences in `skills/quest-lab-editor/references/sources-merged.md`.
- Editing craft sources (Inside The Edit, Daniel Thrasher, Roger Nygard and others) are credited at the bottom of each `SKILL.md`; see also our earlier pack [claude-cuts](https://github.com/2boysfromtown/claude-cuts).
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT), [ffmpeg](https://ffmpeg.org). Fonts in `quest-lab-editor/engine/fonts` are under the SIL Open Font License (licence files included).

## Want the lessons behind it?

The full lessons, failure logs and project files for this and our other workflows are in the **Claude + Magic Skills** course vault at [2bft.in](https://2bft.in).

---

Built by **[2BFT, Two Boys From Town](https://2bft.in)**, a free AI school from Vaniyambadi, Tamil Nadu. Follow [@navaratan.ai](https://instagram.com/navaratan.ai) for more tools like this.
