"""Audit: English-looking speech captions over audio that is actually Hindi (Whisper sometimes translates Hindi->English).
For every caption chunk in the plans, transcribe its own short source window in Hindi mode and measure how much is Devanagari.
usage: caption_audit.py <out.tsv> <plan.py> [<plan.py> ...]"""
import os, re, sys, runpy, glob, json
sys.stdout.reconfigure(encoding='utf-8')
try:
    import torch; lib = os.path.join(os.path.dirname(torch.__file__), 'lib'); os.add_dll_directory(lib); os.environ['PATH'] = lib + os.pathsep + os.environ['PATH']
except Exception: pass
import numpy as np, soundfile as sf
from faster_whisper import WhisperModel
from pathlib import Path
md = sorted(glob.glob(str(Path.home() / '.cache/huggingface/hub/models--mobiuslabsgmbh--faster-whisper-large-v3-turbo/snapshots/*')))[0]
model = WhisperModel(md, device='cuda', compute_type='float16')
# the project's 16 kHz audio: QL_AUDIO16K, else work/audio16k.wav in the current project folder (was hardcoded to the 25 Oct job)
_a16 = os.environ.get('QL_AUDIO16K') or os.path.join(os.getcwd(), 'work', 'audio16k.wav')
if not os.path.exists(_a16): sys.exit(f'no 16 kHz audio at {_a16} - run from the project folder or set QL_AUDIO16K')
print('audio:', _a16, file=sys.stderr)
audio, sr = sf.read(_a16, dtype='float32')
EN = set("i i'm i'll i've don't it it's is the a an to you my me we they people will can what how very so but with for are was in on not be do this that have has had and of just like no yes see let's go".split())
HI = set("hai hain nahi nahin ka ki ke ko se mein main toh to kya kuch bhai yaar raha rahi rahe karna karo kar banaya banaye bana diya liya mere mera meri aap hum ye yeh wo woh aur bhi tha thi hoon ho liye lagta laga dekho sab apna apni kaise kyun isne usne phir abhi hi na aaj kal koi maine humne karke wala wali wale".split())
def plain(t): return re.sub(r'[{}^*~!$/]|=#\w+:', ' ', t).lower()
rows = []
for plan in sys.argv[2:]:
    P = runpy.run_path(plan)['PLAN']
    for s in P['shots']:
        if 'in' not in s: continue
        caps = s.get('caps', [])
        for k, c in enumerate(caps):
            if isinstance(c[0], tuple): continue
            text = c[1]; toks = re.findall(r"[a-z']+", plain(text))
            en, hi = sum(t in EN for t in toks), sum(t in HI for t in toks)
            lo = int(os.environ.get('CA_MIN_EN', '2')); hi_max = int(os.environ.get('CA_MAX_EN', '99'))
            if not (lo <= en <= hi_max and hi == 0): continue          # only English-looking captions
            a = c[0]; b = caps[k + 1][0] if k + 1 < len(caps) and not isinstance(caps[k + 1][0], tuple) else s['out']
            b = min(max(b, a + 1.0), s['out'], a + 6.0)
            seg = audio[int((a - .15) * sr): int((b + .25) * sr)]
            out = ' '.join(x.text for x in model.transcribe(seg, language='hi', beam_size=5, vad_filter=False, condition_on_previous_text=False)[0]).strip()
            letters = [ch for ch in out if ch.isalpha()]
            dev = sum('\u0900' <= ch <= '\u097f' for ch in letters) / max(1, len(letters))
            rows.append((os.path.basename(plan), a, text, round(dev, 2), out))
            print(f"{'FLAG ' if dev >= .5 else 'ok   '} {os.path.basename(plan):16s} {a:8.2f}  dev {dev:.2f}  cap: {text[:48]:48s}  heard: {out[:70]}", flush=True)
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    for r in rows: f.write('\t'.join(map(str, r)) + '\n')
print('flagged', sum(r[3] >= .5 for r in rows), 'of', len(rows), 'English-looking captions')
