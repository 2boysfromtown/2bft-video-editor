---
name: local-av-tools
description: Offline sound and picture clean-up tools for video editing, run on your own PC with small open models - remove mic noise (DeepFilterNet), split a song or soundtrack into vocals, drums, bass and music stems (Demucs), make a karaoke track by taking the singing out (BS-RoFormer), find every cut in a video (TransNetV2), track face, body, hands, smiles and blinks (MediaPipe), label who speaks when (pyannote), smooth motion or slow motion by frame interpolation (RIFE / FILM) and remove a background without a green screen (BiRefNet). Use when the user says clean up the audio, remove background noise, fan or hum, separate vocals, take the music out from under my voice, instrumental, karaoke, remove the singing, find the cuts, how many shots, pacing of this reel, who is speaking, speaker labels, smooth this to 60 fps, slow motion, remove background, cut me out, transparent webcam, or no green screen.
---

# Local AV tools

Eight scripts that do the clean-up jobs an edit keeps needing, offline. Each one streams frames or audio through ffmpeg, so any length works, and writes a new file next to the input (the source is never touched). Setup per tool: `references/setup.md`.

## Which tool

| Job | Command (from `scripts/`) | Model | Licence | Measured on our PC (RTX 5070 Ti) |
|---|---|---|---|---|
| Remove mic noise: fan, AC, traffic, hum, keyboard | `python -I denoise.py talk.mp4 [--strength 18] [--pf]` | DeepFilterNet 3 (CPU) | MIT / Apache-2.0 | 30 s cleaned in 2 s |
| Split into vocals / drums / bass / other | `python -I stems.py song.mp3 [--two] [--fast]` | Demucs v4 htdemucs_ft | MIT | 4 stems of 30 s in 25 s; `--two --fast` 5 s |
| Karaoke: take the singing out | `python -I karaoke.py song.mp3 [--keep-backing] [--video] [--mp3]` | BS-RoFormer / Mel-RoFormer Karaoke | wrapper MIT; **weights have no stated licence: personal use** | 5 min song in 55 s; Whisper heard 72 words in the original, 1 in the karaoke track |
| Find every cut, shot lengths, contact sheet | `python -I shots.py reel.mp4 [--sheet] [--split]` | TransNetV2 | MIT | 7.3 min edit: 62 shots in 22 s, every cut matched |
| Face / body / hands, smiles, blinks, 9:16 reframe | `python -I track.py talk.mp4 [--reframe --aspect 9:16] [--pose --hands --overlay] [--crop x,y,w,h]` | MediaPipe landmarkers (CPU) | Apache-2.0 | 12 s 720p: face 100 %, hands 44 %, 25 fps |
| Who speaks when, speaker-labelled captions | `python -I diarize.py call.mp4 [--speakers 2] [--srt captions.srt]` | pyannote speaker-diarization-community-1 | CC-BY-4.0 (credit pyannote) | needs a free Hugging Face terms click first |
| Smooth motion or slow motion | `<ComfyUI python> -I interpolate.py clip.mp4 [--x 2] [--fps 60] [--slowmo --x 4] [--model film]` | RIFE 4.26 / FILM | MIT / Apache-2.0 | 5 s 24 -> 48 fps in 13 s; 3 s 1080p60 4x slow-mo in 15 s |
| Remove the background, no green screen | `<ComfyUI python> -I cutout.py webcam.mp4 [--as mov/webm/green/matte] [--bg img or #hex] [--crop x,y,w,h]` | BiRefNet | MIT | 464x448 webcam crop at 6 fps, ProRes 4444 with alpha + audio |

## Where each one fits in an edit

- **Before transcribing:** `denoise.py` on any noisy recording. Whisper reads clean audio better, and the cleaned voice is what you mix.
- **Music under a voice:** a stream with music bleeding under the talk -> `stems.py stream.mp4 --two` gives `vocals.wav` + `music.wav`; mix the voice back over licensed music instead. Beat-driven edits: the `drums` stem gives clean transients to snap cuts to (`editor-os/scripts/editgrid.py`).
- **Lyric videos and covers:** `karaoke.py --video` keeps the picture and swaps in the instrumental. Use it only for personal or practice videos: the weights carry no licence, and the song itself is still copyrighted.
- **Studying a reference reel:** `shots.py ref.mp4 --sheet` gives cuts per minute and shot lengths; compare them with `editor-os` pacing targets.
- **Reframing:** `2bft-video-editor/scripts/reframe.py` (YuNet) is the main face-tracked reframe. Use `track.py --reframe` when you also want expressions (smile and mouth-open moments for punch-ins, laughs and energy shake), or body and hand tracking for gestures. Expressions need the face over ~200 px tall: use `--crop` on a webcam box.
- **Podcasts, calls, two-person streams:** `diarize.py --srt` puts speaker names on caption lines; cut to whoever is talking or drop one person's lines.
- **Frame rates:** `interpolate.py` takes a 24 fps AI clip or a 30 fps phone shot to 60, or makes slow motion. It holds the frame at hard cuts instead of blending two shots (`--cut 0` turns that off).
- **Talking head over graphics:** `cutout.py --as mov` gives ProRes 4444 with alpha to drop over anything in DaVinci Resolve, Premiere or ffmpeg; `--as webm` for Remotion/Chrome; `--as green` for editors that only key.

## Rules

- Never overwrite the source. Every script writes `<name>_<tool>` next to the input.
- Listen to cleaned audio and look at cutouts before using them: DeepFilterNet at full strength can make a voice sound thin (try `--strength 18`), and fine hair or fast hands can flicker in a cutout (`--smooth 0.3`).
- Out of memory with plenty of GPU memory free means **system** memory ran out (big apps like a game engine open). Close them and rerun.
- Credit pyannote if diarized output is published. Treat karaoke output as personal use.

## Related

Sound decisions (what to clean, how loud, ducking): `video-sound-and-music`. Where to get music and SFX: `asset-library`. Commands for cuts and mixes: `ffmpeg-edit-toolkit`. DaVinci Resolve hand-off and its free add-ons: `references/davinci-resolve.md`.
