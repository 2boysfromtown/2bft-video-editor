"""Re-transcribe short windows with word timings, in a chosen language - for stretches where the long-file transcript is garbage.
usage: window_words.py <lang hi|en|auto> a:b [a:b ...]      (seconds; run from the project folder or set QL_AUDIO16K)
Prints words@absolute_time per window. Whisper word edges still run early (~100-300 ms): set cut points from the waveform.
"""
import os, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
try:
    import torch; lib = os.path.join(os.path.dirname(torch.__file__), 'lib'); os.add_dll_directory(lib); os.environ['PATH'] = lib + os.pathsep + os.environ['PATH']
except Exception: pass
import soundfile as sf
from faster_whisper import WhisperModel
from pathlib import Path
md = sorted(glob.glob(str(Path.home() / '.cache/huggingface/hub/models--mobiuslabsgmbh--faster-whisper-large-v3-turbo/snapshots/*')))[0]
m = WhisperModel(md, device='cuda', compute_type='float16')
_a16 = os.environ.get('QL_AUDIO16K') or os.path.join(os.getcwd(), 'work', 'audio16k.wav')
audio, sr = sf.read(_a16, dtype='float32')
lang = None if sys.argv[1] == 'auto' else sys.argv[1]
for w in sys.argv[2:]:
    a, b = map(float, w.split(':'))
    seg = audio[int(a * sr): int(b * sr)]
    segs, info = m.transcribe(seg, language=lang, beam_size=5, vad_filter=False, condition_on_previous_text=False, word_timestamps=True)
    out = []
    for s in segs:
        for x in s.words or []:
            out.append(f"{x.word.strip()}@{a + x.start:.2f}")
    print(f'== {a:.2f}-{b:.2f} [{info.language}]', ' '.join(out))
