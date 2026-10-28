"""Split any song or video soundtrack into stems with Demucs v4 (Meta, MIT): vocals / drums / bass / other.

  python -I stems.py song.mp3            -> song_stems\\vocals.wav drums.wav bass.wav other.wav
  ... stream.mp4 --two               -> vocals.wav + music.wav (everything except the voice)
  ... song.mp3 --fast                htdemucs (about 4x faster, slightly less clean); default is htdemucs_ft (best)
  ... --start 60 --seconds 30        only part of the file

Uses: pull the music out from under your voice in a stream, make an a-cappella or instrumental for a lyric video,
or lift a beat so cuts and captions can land on the drums.
"""
import argparse, os, subprocess, sys, time
from pathlib import Path

# Demucs 4.1 downloads its weights from Hugging Face on first use (set HF_HUB_CACHE to choose where they go).
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402
from demucs.apply import apply_model  # noqa: E402
from demucs.pretrained import get_model  # noqa: E402
import av_common as av  # noqa: E402

av.utf8_stdout()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out", help="output folder (default <name>_stems next to the input)")
    ap.add_argument("--two", action="store_true", help="vocals + music only")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--start", type=float)
    ap.add_argument("--seconds", type=float)
    a = ap.parse_args()

    src = Path(a.input)
    out = Path(a.out) if a.out else src.with_name(f"{src.stem}_stems")
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    model = get_model("htdemucs" if a.fast else "htdemucs_ft")
    model.eval()
    sr = model.samplerate

    cmd = ["ffmpeg", "-v", "error"]
    if a.start:
        cmd += ["-ss", str(a.start)]
    cmd += ["-i", str(src)]
    if a.seconds:
        cmd += ["-t", str(a.seconds)]
    raw = subprocess.run(cmd + ["-vn", "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    wav = torch.from_numpy(np.frombuffer(raw, np.float32).reshape(-1, 2).T.copy())
    print(f"{src.name}: {wav.shape[1] / sr:.0f}s of audio, model {'htdemucs' if a.fast else 'htdemucs_ft'}", flush=True)

    ref = wav.mean(0)
    mean, std = ref.mean(), ref.std() + 1e-8
    with torch.inference_mode():
        stems = apply_model(model, ((wav - mean) / std)[None], device="cuda", shifts=1, split=True, overlap=0.25,
                            progress=True)[0]
    stems = stems * std + mean
    names = list(model.sources)
    if a.two:
        v = names.index("vocals")
        groups = {"vocals": stems[v], "music": sum(stems[i] for i in range(len(names)) if i != v)}
    else:
        groups = dict(zip(names, stems))
    for name, s in groups.items():
        sf.write(str(out / f"{name}.wav"), s.T.numpy(), sr, subtype="PCM_16")
    print(f"done in {time.time() - t0:.0f}s -> {out}  ({', '.join(f'{n}.wav' for n in groups)})")


if __name__ == "__main__":
    main()
