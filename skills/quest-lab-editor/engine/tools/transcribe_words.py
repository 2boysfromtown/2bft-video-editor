"""Transcribe a wav with faster-whisper, keeping word timings. Writes JSON + a readable txt.
usage: transcribe_words.py <in.wav> <out_base> [hi|en|auto] [--glossary "Claude, Unreal, ..."] [--hallu 2]"""
import json, os, sys, time, glob
from pathlib import Path

# torch ships the CUDA/cuDNN DLLs ctranslate2 needs
try:
    import torch  # noqa
    lib = Path(torch.__file__).parent / "lib"
    os.add_dll_directory(str(lib))
    os.environ["PATH"] = str(lib) + os.pathsep + os.environ["PATH"]
except Exception as e:
    print("torch dll path:", e, file=sys.stderr)

from faster_whisper import WhisperModel

args = [a for a in sys.argv[1:]]
opt = {}
for k in ("--glossary", "--hallu"):          # optional; defaults keep the 25 Oct behaviour
    if k in args:
        i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
wav, out = args[0], args[1]
lang = args[2] if len(args) > 2 and args[2] != "auto" else None
# --glossary "Claude, Unreal, Meld, ComfyUI, <your show name>": names Whisper should spell this way (faster-whisper hotwords)
# --hallu 2: skip silent gaps > 2 s when a hallucination is suspected (needs word timestamps; good for streams with long waits)
extra = {}
if "--glossary" in opt: extra["hotwords"] = opt["--glossary"]
if "--hallu" in opt: extra["hallucination_silence_threshold"] = float(opt["--hallu"])
hub = Path.home() / ".cache" / "huggingface" / "hub"
model_dir = sorted(glob.glob(str(hub / "models--mobiuslabsgmbh--faster-whisper-large-v3-turbo" / "snapshots" / "*")))[0]

t0 = time.time()
try:
    model = WhisperModel(model_dir, device="cuda", compute_type="float16")
    dev = "cuda"
except Exception as e:
    print("cuda failed, using cpu:", e, file=sys.stderr)
    model = WhisperModel(model_dir, device="cpu", compute_type="int8")
    dev = "cpu"

segs, info = model.transcribe(wav, language=lang, word_timestamps=True, vad_filter=True,
                              vad_parameters=dict(min_silence_duration_ms=400),
                              beam_size=5, condition_on_previous_text=False, **extra)
print(f"device={dev} lang={info.language} p={info.language_probability:.2f} dur={info.duration:.0f}s", file=sys.stderr)
res = {"language": info.language, "duration": info.duration, "segments": []}
with open(out + ".txt", "w", encoding="utf-8") as f:
    for s in segs:
        words = [{"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)} for w in (s.words or [])]
        res["segments"].append({"s": round(s.start, 3), "e": round(s.end, 3), "t": s.text.strip(),
                                "lp": round(s.avg_logprob, 3), "ns": round(s.no_speech_prob, 3), "words": words})
        m, sec = divmod(int(s.start), 60)
        f.write(f"[{m:02d}:{sec:02d}] {s.text.strip()}\n"); f.flush()
        print(f"[{m:02d}:{sec:02d}] {s.text.strip()[:80]}", file=sys.stderr)
with open(out + ".json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False)
print(f"done in {time.time()-t0:.0f}s", file=sys.stderr)
