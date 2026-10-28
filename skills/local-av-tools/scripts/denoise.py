"""Remove background noise (fan, AC, traffic, room hum, keyboard) from speech with DeepFilterNet 3 (MIT/Apache-2.0).
Runs on the CPU in real time, so it never fights the GPU. Works on audio or video files.

  python -I denoise.py talk.mp4            -> talk_clean.mp4 (video copied, audio cleaned)
  ... take.wav                       -> take_clean.wav
  ... talk.mp4 --strength 18         keep some room sound (dB of reduction; default = full)
  ... talk.mp4 --pf                  extra post-filter for very noisy rooms

Tip: run this before captions (transcribe-local) and before using a recording as a voice-clone reference.
Needs the DeepFilterNet binary (deep-filter) from https://github.com/Rikorose/DeepFilterNet/releases on PATH, or DEEPFILTER_EXE.
"""
import argparse, os, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import av_common as av  # noqa: E402

av.utf8_stdout()
DF = Path(os.environ.get("DEEPFILTER_EXE", "deep-filter"))
AUDIO_EXT = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--strength", type=float, default=100, help="max noise reduction in dB (100 = full, 12-24 = gentle)")
    ap.add_argument("--pf", action="store_true", help="post-filter: stronger on very noisy audio")
    ap.add_argument("--stereo", action="store_true", help="keep two channels (default: mono, as voice usually is)")
    a = ap.parse_args()

    for inp in a.inputs:
        src = Path(inp)
        t0 = time.time()
        info = av.probe(src)
        if not info["has_audio"]:
            print(f"{src.name}: no audio track, skipped"); continue
        is_video = info["w"] is not None and src.suffix.lower() not in AUDIO_EXT
        out = Path(a.out) if a.out and len(a.inputs) == 1 else src.with_name(f"{src.stem}_clean{src.suffix if is_video else '.wav'}")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            raw = tmp / "voice.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "2" if a.stereo else "1", "-ar", "48000",
                            "-c:a", "pcm_s16le", str(raw)], check=True)
            cmd = [str(DF), "-D", "-a", str(a.strength), "-o", str(tmp / "out"), str(raw)]
            if a.pf:
                cmd.insert(1, "--pf")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            clean = tmp / "out" / "voice.wav"
            if is_video:
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-i", str(clean), "-map", "0:v", "-map", "1:a",
                                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)], check=True)
            else:
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clean), str(out)], check=True)
        print(f"{src.name}: {info['duration']:.0f}s cleaned in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
