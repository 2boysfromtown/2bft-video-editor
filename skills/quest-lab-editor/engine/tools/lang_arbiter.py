"""For each source window: language-ID probabilities (en vs hi) + transcripts in hi and en mode. Arbiter for 'translated caption' doubts."""
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
# the project's 16 kHz audio: QL_AUDIO16K, else work/audio16k.wav in the current project folder (was hardcoded to the 25 Oct job)
_a16 = os.environ.get('QL_AUDIO16K') or os.path.join(os.getcwd(), 'work', 'audio16k.wav')
if not os.path.exists(_a16): sys.exit(f'no 16 kHz audio at {_a16} - run from the project folder or set QL_AUDIO16K')
print('audio:', _a16, file=sys.stderr)
audio, sr = sf.read(_a16, dtype='float32')
for arg in sys.argv[1:]:
    tag, a, b = arg.split(':'); a, b = float(a), float(b)
    seg = audio[int((a - .1) * sr): int((b + .1) * sr)]
    lang, p, allp = m.detect_language(seg)
    d = dict(allp); en, hi = d.get('en', 0), d.get('hi', 0) + d.get('ur', 0)
    t_hi = ' '.join(s.text for s in m.transcribe(seg, language='hi', beam_size=5, vad_filter=False, condition_on_previous_text=False)[0]).strip()
    t_en = ' '.join(s.text for s in m.transcribe(seg, language='en', beam_size=5, vad_filter=False, condition_on_previous_text=False)[0]).strip()
    verdict = 'EN' if en > .6 else 'HI' if hi > .6 else 'MIX'
    print(f'{verdict:3s} {tag:14s} {a:8.2f}-{b:7.2f}  en {en:.2f} hi {hi:.2f} | hi: {t_hi[:70]} | en: {t_en[:80]}', flush=True)
