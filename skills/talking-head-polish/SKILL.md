---
name: talking-head-polish
description: Polish a vertical talking-head reel - put text or a darkened background BEHIND the speaker with a person mask (rembg), and add Whisper-timed karaoke captions where the spoken word lights up, including mixed-language speech like Tanglish or Hinglish. Use when the user wants text behind a person, depth-style titles, word-by-word highlighted captions, or Hindi/Tamil/English captions timed to the voice.
---

# Talking-head polish

Two techniques that make a phone-shot talking head look produced. The scripts do the machine work; the graphics layer (text, counters, captions) is built in Remotion or similar and composited by you.

## Needs

ffmpeg with libvpx-vp9, Python 3.9+, `pip install rembg onnxruntime pillow numpy faster-whisper`. rembg downloads its model on first use.

## 1. Text behind the speaker

1. Find the time ranges where text should sit behind the person (only those: masks are slow).
2. `python -I scripts/masks.py talk.mp4 work/mask "3.3-6.3,15.3-25.2"` writes a person mask PNG per frame (default model `u2net_human_seg`, half resolution).
3. `python -I scripts/cutout.py talk.mp4 work/mask work/cutout.webm` builds a transparent cut-out of the speaker (VP9 alpha), empty outside the masked ranges.
4. Layer order in your graphics tool: the original video at the bottom, your text above it, the cut-out on top. The text now passes behind the person. Darkening the background works the same way (dim layer between video and cut-out).
5. Check frames at the edges of each range: hair and hands are where masks fail; shorten a range rather than ship a flickering edge.

## 2. Word-timed karaoke captions

1. Extract word times: `python -I scripts/word_times.py talk.mp4 --out words.json`.
2. For mixed-language speech written in the Latin alphabet (Tanglish, Hinglish), Whisper guesses wrong scripts and spellings. Write down what was actually said, split it into windows and pass them: `--prompts prompts.json` where each item is `{"start": s, "end": e, "text": "what was said"}`. Each window is transcribed with that text as the initial prompt, which keeps spelling and gives usable word times.
3. Chunk the words into 1-3 word captions, highlight the active word (a colour change from its start until the next word starts), uppercase, one line, shrink long words.
4. Nudge starts to the loudness onsets by eye: Whisper word starts can run early. Render, pull frames on the word boundaries, and proofread against the audio.

## Limits

- Masks are per frame, not temporally smoothed beyond a small blur; busy backgrounds and fast hands can flicker.
- Whisper word times are approximate. The agent cannot hear: a person must watch the captions against the audio.
- The shipped scripts were smoke-tested end to end on a synthetic clip (no person in it, so the masks are empty); there is no real-footage example in this repo because the source video is not ours to redistribute.
