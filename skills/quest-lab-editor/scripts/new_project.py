"""Start a QUEST LAB edit project from a recording.

usage: python -I new_project.py "<recording.mp4>" "<project folder, keep it short e.g. <short path>\\job>" [--lang hi|en|auto] [--no-transcribe] [--no-facetrack]

Does: copy the engine (+ fonts, + Windows Bahnschrift) -> probe -> extract audio (16 k mono for Whisper/energy, 48 k stereo for the mix)
-> transcribe with word timings (GPU) -> energy map -> face track -> one frame every 10 s into labelled contact sheets -> write source.json.
Then: read every sheet and the transcript, confirm the layout rects in source.json, write EDIT-PLAN.md, write plans/, run render.py.
"""
import json, os, shutil, subprocess, sys
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(SKILL, 'engine')
PY_EDIT = os.environ.get('QL_PY_EDIT', sys.executable)   # venv with numpy/scipy/soundfile/Pillow
PY_ML = os.environ.get('QL_PY_ML', sys.executable)       # venv with faster-whisper, librosa, torch (CUDA build)

def run(cmd, **kw):
    print('>', ' '.join(str(c) for c in cmd[:4]), '...', flush=True); subprocess.run(cmd, check=True, **kw)

def main():
    if len(sys.argv) < 3 or '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__); return
    args = [a for a in sys.argv[1:] if not a.startswith('--') and a not in ('hi', 'en', 'auto')]
    src, proj = os.path.abspath(args[0]), os.path.abspath(args[1])
    lang = sys.argv[sys.argv.index('--lang') + 1] if '--lang' in sys.argv else 'hi'
    os.makedirs(proj, exist_ok=True)
    for d in ('plans', 'edits', 'cache/frames', 'cache/clips', 'assets', 'audio', 'out', 'review/stills', 'music', 'work/frames10', 'work/sheets', 'sfx_lib', 'tools', 'fonts'):
        os.makedirs(os.path.join(proj, d), exist_ok=True)
    for f in os.listdir(ENGINE):
        p = os.path.join(ENGINE, f)
        if os.path.isfile(p): shutil.copy(p, proj)
    for sub in ('tools', 'fonts'):
        for f in os.listdir(os.path.join(ENGINE, sub)): shutil.copy(os.path.join(ENGINE, sub, f), os.path.join(proj, sub))
    shutil.copytree(os.path.join(ENGINE, 'harness'), os.path.join(proj, 'harness'), dirs_exist_ok=True)   # render.mjs + lib/boot2d.js
    if not os.path.exists(os.path.join(proj, 'fonts', 'bahnschrift.ttf')) and os.path.exists(r'C:\Windows\Fonts\bahnschrift.ttf'):
        shutil.copy(r'C:\Windows\Fonts\bahnschrift.ttf', os.path.join(proj, 'fonts'))
    W = os.path.join(proj, 'work')
    a16, a48 = os.path.join(W, 'audio16k.wav'), os.path.join(W, 'audio48k.wav')
    run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '1', '-ar', '16000', a16])
    run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '2', '-ar', '48000', a48])
    words = os.path.join(W, 'transcript')
    if '--no-transcribe' not in sys.argv:
        run([PY_ML, '-I', os.path.join(proj, 'tools', 'transcribe_words.py'), a16, words, lang])
    run([PY_ML, '-I', os.path.join(proj, 'tools', 'energy.py'), src, a16, words + '.json', os.path.join(W, 'energy.json')])
    run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', 'fps=1/10,scale=480:-2', '-q:v', '4', os.path.join(W, 'frames10', 'f_%04d.jpg')])
    run([PY_EDIT, '-I', os.path.join(proj, 'tools', 'contact_sheet.py'), os.path.join(W, 'frames10'), os.path.join(W, 'sheets', 's10'), '10', '5', '4'])
    cfg = dict(video=src, audio48k=a48, energy=os.path.join(W, 'energy.json'), words=words + '.json',
               screen=[48, 125, 1412, 794], cam=[1474, 156, 388, 765], face=[1490, 330, 356, 356],
               layout_note='DEFAULTS from one example stream scene - measure a full-size frame of yours and correct these')
    # face tracking: every webcam crop follows his eyes (OpenCV YuNet; set QL_PY_CV and QL_YUNET)
    py_cv = os.environ.get('QL_PY_CV', sys.executable); yunet = os.environ.get('QL_YUNET', 'models/face_detection_yunet_2023mar.onnx')   # python with opencv + the YuNet ONNX model
    if os.path.exists(py_cv) and os.path.exists(yunet) and '--no-facetrack' not in sys.argv:
        ft = os.path.join(W, 'facetrack.json')
        run([py_cv, '-I', os.path.join(proj, 'tools', 'face_track.py'), src, ft, '--cam', ','.join(map(str, cfg['cam']))])
        cfg['facetrack'] = ft
    else:
        print('face tracking skipped (no QL_PY_CV python / QL_YUNET model) - webcam crops stay static')
    json.dump(cfg, open(os.path.join(proj, 'source.json'), 'w'), indent=2)
    # music pack: one line in <skill>/music_pack_path.txt = the folder of music YOU have the rights to (scanned with tools/music_scan.py)
    pack = os.path.join(SKILL, 'music_pack_path.txt')
    if os.path.exists(pack):
        mdir = open(pack).read().strip()
        if os.path.exists(os.path.join(mdir, 'scan.json')): shutil.copy(os.path.join(mdir, 'scan.json'), os.path.join(proj, 'music', 'scan.json'))
    print('\nproject ready:', proj)
    print('next: read work/sheets/*.jpg and work/transcript.txt, confirm source.json rects, write EDIT-PLAN.md, then plans/ and render.py')

if __name__ == '__main__':
    main()
