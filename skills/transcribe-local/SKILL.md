---
name: transcribe-local
description: Transcribe a local audio or video file (mp3, wav, m4a, mp4, mkv, webm...) to timestamped text with offline Whisper (faster-whisper) - no API key, no upload. Use when the user asks to transcribe, caption, or get the spoken text of a file, or when an edit needs word or sentence timestamps (cutting by transcript, captions, kinetic type).
---

# Transcribe Local

Runs `faster-whisper` (Whisper large-v3-turbo, int8 on CPU by default) on your own machine. Audio never leaves it.

## Setup (one time)

```
pip install faster-whisper
```

ffmpeg must be on PATH. The first run downloads the model once (`large-v3-turbo`, about 1.6 GB; pass `--model small` for a small, faster one). If you already have a faster-whisper model in the Hugging Face cache, or the Codex desktop app's bundled faster-whisper runtime under `~/.cache/codex-runtimes`, the script reuses it and nothing is installed.

## Run it

```
python scripts/transcribe_local.py "<audio-or-video-file>" [--start T] [--end T] [--language en] [--model NAME_OR_DIR] [--out notes.txt]
```

- Output is `[MM:SS] text` lines on stdout (progress goes to stderr).
- `--start` / `--end` accept `SS`, `MM:SS` or `HH:MM:SS`; timestamps stay absolute.
- Language is auto-detected; pass `--language xx` to force it.
- `--device cuda` is opt-in and untested here; the default CPU path is the verified one.
- Speed on CPU is several times faster than real time. For a very long file, confirm with the user first, or transcribe a section.
- For word-level timestamps (karaoke captions) use `talking-head-polish/scripts/word_times.py`.

## Limits

- Whisper can hallucinate on silence or music and mishears names and mixed-language speech; flag doubtful stretches instead of smoothing them over, and proofread captions against the audio.
- Romanised Tanglish or Hinglish is not transcribed well without a prompt (see `word_times.py --prompts`).
- No speaker labels.
