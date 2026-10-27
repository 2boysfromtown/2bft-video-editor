#!/usr/bin/env python3
"""Word-level timestamps for karaoke captions, optionally steered by the script you know was said.

  python word_times.py <audio-or-video> [--prompts prompts.json] [--language en] [--model DIR_OR_NAME] [--out words.json]

Without --prompts it transcribes the whole file with word timestamps.
With --prompts (a JSON list of {"start": s, "end": s, "text": "what was said"}), each window is
transcribed with that text as Whisper's initial prompt. This is how mixed-language speech
(Tanglish, Hinglish) written in the Latin alphabet gets usable word timings: Whisper follows
the spelling in the prompt instead of guessing a script.
Output: [{"w": word, "s": start, "e": end}] in source seconds. Nudge starts to loudness onsets
by eye if a word lights up early. Needs faster-whisper (pip install faster-whisper) and ffmpeg.
"""
import argparse
import glob
import json
import os
import subprocess

import numpy as np
from faster_whisper import WhisperModel


def load(src):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def pick_model(explicit):
    if explicit:
        return explicit, os.path.isdir(explicit)
    hub = os.path.join(os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface")), "hub")
    c = [p for p in glob.glob(hub + "/models--*faster-whisper*/snapshots/*") if os.path.exists(p + "/model.bin")]
    c.sort(key=lambda p: (0 if "turbo" in p else 1, p))
    return (c[0], True) if c else ("large-v3-turbo", False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("--prompts")
    ap.add_argument("--language")
    ap.add_argument("--model")
    ap.add_argument("--out")
    a = ap.parse_args()
    audio = load(a.media)
    ref, local = pick_model(a.model)
    m = WhisperModel(ref, device="cpu", compute_type="int8", local_files_only=local)
    windows = json.load(open(a.prompts, encoding="utf-8")) if a.prompts else [{"start": 0.0, "end": len(audio) / 16000, "text": None}]
    words = []
    for win in windows:
        st, en = float(win["start"]), float(win["end"])
        segs, _ = m.transcribe(audio[int(st * 16000):int(en * 16000)], language=a.language, initial_prompt=win.get("text"),
                               word_timestamps=True, beam_size=5, condition_on_previous_text=False)
        for s in segs:
            for w in s.words:
                words.append({"w": w.word.strip(), "s": round(st + w.start, 2), "e": round(st + w.end, 2)})
    text = json.dumps(words, ensure_ascii=False, indent=0)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    for w in words:
        print(f'{w["s"]:7.2f} {w["e"]:7.2f}  {w["w"]}')


if __name__ == "__main__":
    main()
