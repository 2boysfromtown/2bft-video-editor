"""Karaoke maker: take the singing out of any song (audio or video file) on the GPU.

  APY karaoke.py song.mp3                    -> song_karaoke\\karaoke.wav (no vocals) + vocals.wav
  APY karaoke.py song.mp3 --keep-backing     lead singer removed, backing vocals / chorus kept (like a studio karaoke track)
  APY karaoke.py "music video.mp4" --video   also writes song_karaoke\\karaoke.mp4 (same picture, singing removed)
  APY karaoke.py a.mp3 b.m4a C:\\Songs\\      several files or a whole folder at once
  APY karaoke.py song.mp3 --mp3              also writes 320 kbps MP3 copies
  APY karaoke.py song.mp3 --start 60 --seconds 30   only part of the file (quick test)

  APY = python -I <skills>/local-av-tools/scripts/

Models (downloaded on first use into KARAOKE_MODELS, default ./models/audio-separator, run through python-audio-separator).
The weights are community-trained with no stated licence: treat the output as personal use.
  default         BS-RoFormer viperx 1297   - removes all vocals (instrumental SDR 16.5, vocals 11.8)
  --keep-backing  Mel-RoFormer Karaoke gabox - removes only the lead vocal (instrumental SDR 16.4)
  --model <file>  any other model from `audio-separator --list_models`
"""
import argparse, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import av_common as av  # noqa: E402

av.utf8_stdout()
MODEL_DIR = Path(os.environ.get("KARAOKE_MODELS", os.path.join("models", "audio-separator")))
FULL = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
LEAD = "mel_band_roformer_karaoke_gabox.ckpt"
MEDIA = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wma", ".aiff", ".aif",
         ".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v"}


def collect(inputs):
    files = []
    for p in map(Path, inputs):
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.suffix.lower() in MEDIA and not f.stem.endswith("_karaoke"))
        elif p.exists():
            files.append(p)
        else:
            print(f"skip (not found): {p}")
    return files


def stem_of(path):
    """'x_(Instrumental)_model.wav' -> 'instrumental'."""
    name = Path(path).name
    if "(" in name and ")" in name:
        return name[name.index("(") + 1:name.index(")")].lower()
    return Path(path).stem.lower()


def main():
    ap = argparse.ArgumentParser(description="Remove vocals from songs for karaoke.")
    ap.add_argument("inputs", nargs="+", help="audio/video files or folders")
    ap.add_argument("--keep-backing", action="store_true", help="remove only the lead vocal, keep backing vocals")
    ap.add_argument("--model", help="override the model file")
    ap.add_argument("--video", action="store_true", help="for video inputs, also write karaoke.mp4 with the new audio")
    ap.add_argument("--mp3", action="store_true", help="also write MP3 copies")
    ap.add_argument("--out", help="output folder (default <name>_karaoke next to each input)")
    ap.add_argument("--start", type=float)
    ap.add_argument("--seconds", type=float)
    a = ap.parse_args()

    files = collect(a.inputs)
    if not files:
        sys.exit("no input files")
    model = a.model or (LEAD if a.keep_backing else FULL)
    voc_name = "lead_vocals" if a.keep_backing else "vocals"

    from audio_separator.separator import Separator  # slow import, after argument checks
    import logging
    work = Path(tempfile.mkdtemp(prefix="karaoke_", dir=os.environ.get("TEMP")))
    sep = Separator(log_level=logging.WARNING, model_file_dir=str(MODEL_DIR), output_dir=str(work),
                    output_format="WAV", use_autocast=True)
    t0 = time.time()
    sep.load_model(model)
    print(f"model {model} loaded in {time.time() - t0:.0f}s", flush=True)

    try:
        for src in files:
            t1 = time.time()
            out = Path(a.out) / f"{src.stem}_karaoke" if a.out and len(files) > 1 else \
                Path(a.out) if a.out else src.with_name(f"{src.stem}_karaoke")
            out.mkdir(parents=True, exist_ok=True)
            # Decode anything (video, m4a, opus...) to a clean 44.1 kHz stereo WAV first.
            tmp_in = work / "input.wav"
            cmd = ["ffmpeg", "-v", "error", "-y"]
            if a.start:
                cmd += ["-ss", str(a.start)]
            cmd += ["-i", str(src)]
            if a.seconds:
                cmd += ["-t", str(a.seconds)]
            r = subprocess.run(cmd + ["-vn", "-ac", "2", "-ar", "44100", "-c:a", "pcm_f32le", str(tmp_in)],
                               capture_output=True, text=True)
            if r.returncode or not tmp_in.exists():
                print(f"skip {src.name}: no audio track ({r.stderr.strip()[:200]})")
                continue
            info = av.probe(src)
            print(f"{src.name}: {av.probe(tmp_in)['duration']:.0f}s of audio", flush=True)

            results = sep.separate(str(tmp_in))
            vocals_key = {"vocals", "karaoke", "lead", "lead vocals", "lead_vocals"}
            for f in results:
                f = work / Path(f).name if not Path(f).is_absolute() else Path(f)
                s = stem_of(f)
                target = out / (f"{voc_name}.wav" if s in vocals_key else "karaoke.wav")
                shutil.move(str(f), target)
            tmp_in.unlink(missing_ok=True)

            made = ["karaoke.wav", f"{voc_name}.wav"]
            if a.mp3:
                for n in list(made):
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out / n), "-c:a", "libmp3lame", "-b:a", "320k",
                                    str(out / n.replace(".wav", ".mp3"))], check=True)
                made += [n.replace(".wav", ".mp3") for n in made]
            if a.video and info["w"]:
                cmd = ["ffmpeg", "-v", "error", "-y"]
                if a.start:
                    cmd += ["-ss", str(a.start)]
                cmd += ["-i", str(src)]
                if a.seconds:
                    cmd += ["-t", str(a.seconds)]
                cmd += ["-i", str(out / "karaoke.wav"), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", str(out / "karaoke.mp4")]
                subprocess.run(cmd, check=True)
                made.append("karaoke.mp4")
            print(f"  done in {time.time() - t1:.0f}s -> {out}  ({', '.join(made)})", flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
