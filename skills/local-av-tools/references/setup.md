# Setup for local-av-tools

Tested on Windows 11, Python 3.12, PyTorch 2.14 with CUDA 13 and an RTX 5070 Ti (16 GB). Most tools also run on the CPU, just slower. All need `ffmpeg` and `ffprobe` on PATH.

Keep these in their own virtual environment so their PyTorch pins don't fight your other tools:

```bash
python -m venv av-env
av-env\Scripts\activate          # Linux/macOS: source av-env/bin/activate
pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cu130   # or the CPU wheels
pip install numpy soundfile opencv-python
```

| Script | Install | Model files | Setting |
|---|---|---|---|
| `denoise.py` | the `deep-filter` binary from the [DeepFilterNet releases](https://github.com/Rikorose/DeepFilterNet/releases) (no Python package needed) | bundled in the binary | put it on PATH or set `DEEPFILTER_EXE` |
| `stems.py` | `pip install demucs` (tested 4.1.0) | downloaded from Hugging Face on first run (htdemucs_ft 321 MB, htdemucs 81 MB) | `HF_HUB_CACHE` to choose where weights go |
| `karaoke.py` | `pip install "audio-separator[gpu]" audioread` (tested 0.47.1; keep `audioread` installed, newer librosa dropped it) | downloaded on first run (BS-RoFormer 639 MB, Mel-RoFormer Karaoke 913 MB) | `KARAOKE_MODELS` (default `./models/audio-separator`) |
| `shots.py` | `pip install transnetv2-pytorch` (tested 1.0.5) | bundled | none |
| `track.py` | `pip install mediapipe` (tested 1.1.1) | `face_landmarker.task`, `pose_landmarker_full.task`, `hand_landmarker.task` from the [MediaPipe models page](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker#models) | `MEDIAPIPE_MODELS` (default `./models/mediapipe`) |
| `diarize.py` | `pip install pyannote.audio` (tested 4.0.7) | accept the terms at [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1), log in with `hf auth login`, then `hf download pyannote/speaker-diarization-community-1 --local-dir models/pyannote-community-1` | `PYANNOTE_MODEL` |
| `interpolate.py` | a recent [ComfyUI](https://github.com/comfyanonymous/ComfyUI) install (portable build is easiest); run the script with ComfyUI's own Python | `rife_v4.26.safetensors` and/or `film_net_fp16.safetensors` in `ComfyUI/models/frame_interpolation` | `COMFYUI_DIR` (the folder that holds `comfy/` and `models/`) |
| `cutout.py` | same ComfyUI install | `birefnet.safetensors` in `ComfyUI/models/background_removal` | `COMFYUI_DIR` |

`interpolate.py` and `cutout.py` import ComfyUI's built-in RIFE, FILM and BiRefNet code, so ComfyUI does not need to be running; on the portable build the Python is `ComfyUI_windows_portable\python_embeded\python.exe`.

Run every script with `python -I` (isolated mode). Each script adds its own folder to `sys.path` so it can import `av_common.py`.

## Licences in one place

- Commercial-safe: DeepFilterNet (MIT/Apache-2.0), Demucs (MIT), TransNetV2 (MIT), MediaPipe (Apache-2.0), RIFE (MIT), FILM (Apache-2.0), BiRefNet (MIT).
- pyannote community-1: CC-BY-4.0. Credit "pyannote.audio" when you publish its output.
- Karaoke weights (BS-RoFormer viperx, Mel-RoFormer Karaoke gabox): community-trained, no stated licence. python-audio-separator itself is MIT. Personal use only.
