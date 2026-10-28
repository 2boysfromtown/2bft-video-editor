"""Who speaks when: split a recording into speaker turns with pyannote speaker-diarization-community-1 (CC-BY-4.0).

  python -I diarize.py call.mp4
      -> call_speakers.json + call_speakers.rttm, and prints talk time per speaker and the turns
  ... call.mp4 --speakers 2          if you know how many people talk (more accurate)
  ... call.mp4 --srt call.srt        label each caption line with its speaker -> call_speakers.srt
                                     (make the .srt with transcribe-local first)
  ... --start 60 --seconds 300

Uses: label who says what in podcasts/calls/streams with guests, cut to whoever is speaking,
or drop everything one person said. Credit: pyannote.audio (CC-BY-4.0) if the output is published.
"""
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from pyannote.audio import Pipeline  # noqa: E402
import av_common as av  # noqa: E402

av.utf8_stdout()
MODEL = Path(os.environ.get("PYANNOTE_MODEL", os.path.join("models", "pyannote-community-1")))


def srt_time(s):
    h, m = divmod(int(s), 3600); m, sec = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{sec:02d},{int(round((s - int(s)) * 1000)):03d}"


def parse_srt(text):
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().splitlines()
        tl = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if tl is None:
            continue
        a, b = [x.strip().replace(",", ".") for x in lines[tl].split("-->")]
        sec = lambda t: sum(float(p) * f for p, f in zip(t.split(":"), (3600, 60, 1)))  # noqa: E731
        out.append((sec(a), sec(b), "\n".join(lines[tl + 1:])))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--speakers", type=int)
    ap.add_argument("--min", type=int)
    ap.add_argument("--max", type=int)
    ap.add_argument("--srt")
    ap.add_argument("--start", type=float)
    ap.add_argument("--seconds", type=float)
    a = ap.parse_args()

    if not (MODEL / "config.yaml").exists():
        sys.exit(f"Model missing in {MODEL}. Accept the terms at https://huggingface.co/pyannote/speaker-diarization-community-1, "
                 f"then: hf download pyannote/speaker-diarization-community-1 --local-dir {MODEL}")
    src = Path(a.input)
    t0 = time.time()
    pipe = Pipeline.from_pretrained(str(MODEL))
    pipe.to(torch.device("cuda"))

    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(a.start)] if a.start else []) + ["-i", str(src)]
    cmd += (["-t", str(a.seconds)] if a.seconds else []) + ["-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"]
    wav = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).copy()
    kw = {k: v for k, v in (("num_speakers", a.speakers), ("min_speakers", a.min), ("max_speakers", a.max)) if v}
    res = pipe({"waveform": torch.from_numpy(wav)[None], "sample_rate": 16000}, **kw)
    ann = getattr(res, "exclusive_speaker_diarization", None) or getattr(res, "speaker_diarization", res)

    # friendlier labels: SPEAKER_00 -> A, B, C ... in order of first appearance
    turns = [(seg.start, seg.end, spk) for seg, _, spk in ann.itertracks(yield_label=True)]
    names = {}
    for _, _, spk in sorted(turns):
        names.setdefault(spk, chr(ord("A") + len(names)))
    turns = [{"start": round(s, 2), "end": round(e, 2), "speaker": names[k]} for s, e, k in sorted(turns)]
    total = {}
    for t in turns:
        total[t["speaker"]] = total.get(t["speaker"], 0) + t["end"] - t["start"]

    base = src.with_name(f"{src.stem}_speakers")
    Path(f"{base}.json").write_text(json.dumps({"input": str(src), "start": a.start, "turns": turns,
                                                "talk_seconds": {k: round(v, 1) for k, v in total.items()}}, indent=1), encoding="utf-8")
    with open(f"{base}.rttm", "w", encoding="utf-8") as f:
        for t in turns:
            f.write(f"SPEAKER {src.stem} 1 {t['start']:.3f} {t['end'] - t['start']:.3f} <NA> <NA> {t['speaker']} <NA> <NA>\n")
    dur = len(wav) / 16000
    print(f"{src.name}: {dur:.0f}s, {len(names)} speaker(s), {len(turns)} turns  [{time.time() - t0:.0f}s]")
    for k, v in sorted(total.items(), key=lambda x: -x[1]):
        print(f"  speaker {k}: {v:.0f}s ({100 * v / dur:.0f}%)")
    for t in turns[:30]:
        print(f"  {t['start']:8.2f} - {t['end']:8.2f}  {t['speaker']}")
    if len(turns) > 30:
        print(f"  ... {len(turns) - 30} more in {base}.json")

    if a.srt:
        out = []
        for i, (s, e, txt) in enumerate(parse_srt(Path(a.srt).read_text(encoding="utf-8")), 1):
            ov = {}
            for t in turns:
                o = min(e, t["end"]) - max(s, t["start"])
                if o > 0:
                    ov[t["speaker"]] = ov.get(t["speaker"], 0) + o
            who = max(ov, key=ov.get) if ov else "?"
            out.append(f"{i}\n{srt_time(s)} --> {srt_time(e)}\n[{who}] {txt}\n")
        Path(f"{base}.srt").write_text("\n".join(out), encoding="utf-8")
        print("labelled captions ->", f"{base}.srt")


if __name__ == "__main__":
    main()
