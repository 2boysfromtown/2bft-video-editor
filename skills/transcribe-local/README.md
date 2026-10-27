# transcribe-local

Offline speech-to-text for the editing skills, built on [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

**Honest about where it gets its runtime.** The script needs `faster-whisper`. It looks for it in this order:

1. the Python you run it with: `pip install faster-whisper` (the plain, supported route);
2. an existing faster-whisper install bundled with the Codex desktop app (`~/.cache/codex-runtimes/*/dependencies/python`), which it reuses if you happen to have that app. Nothing is installed or modified;
3. otherwise it stops and tells you to run `pip install faster-whisper`.

The model is the best faster-whisper model already in your Hugging Face cache, else `large-v3-turbo` downloaded once (about 1.6 GB). Everything after that runs offline.

```
pip install faster-whisper
python scripts/transcribe_local.py talk.mp4 --language en
```
