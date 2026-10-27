"""One command per film: build -> mix -> GPU render in chunks -> concat -> two-pass loudnorm mux (-14 LUFS, -1.5 dBTP) -> out/<name>.mp4

usage: python render.py plans/<name>.py [--chunk 2400] [--jobs 2] [--stills 1.0,5.0] [--no-video] [--clean]

GPU encoder slots: consumer NVIDIA cards allow ~8 NVENC sessions and extra encodes HANG (not fail). Every chunk takes a
machine-wide slot (lock files in QL_SLOTS_DIR, default %TEMP%\\questlab_render_slots, QL_MAX_ENCODES default 4) and has a
per-chunk timeout with retries. Chunks already rendered from the same timeline are reused (marker = hash of the edit JSON).
"""
import hashlib, json, os, re, subprocess, sys, runpy, tempfile, time
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.abspath(__file__)); os.chdir(ROOT)
PY = sys.executable
RENDER = os.environ.get('QL_RENDER', os.path.join(ROOT, 'harness', 'render.mjs'))   # headless-Chrome frame renderer, copied with the engine
SLOTS = os.environ.get('QL_SLOTS_DIR', os.path.join(tempfile.gettempdir(), 'questlab_render_slots'))
MAX_ENC = int(os.environ.get('QL_MAX_ENCODES', '4'))
os.makedirs(SLOTS, exist_ok=True)

def run(cmd, timeout=None, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout, **kw)
    if r.returncode: print(r.stdout[-2000:], r.stderr[-2000:]); raise RuntimeError(f'failed ({r.returncode}): {" ".join(map(str, cmd[:3]))}')
    return r

def acquire():
    while True:
        for i in range(MAX_ENC):
            p = os.path.join(SLOTS, f'slot{i}.lock')
            try:
                if os.path.exists(p) and time.time() - os.path.getmtime(p) > 20 * 60: os.remove(p)   # stale (crashed holder)
                fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.write(fd, f'{os.getpid()} {ROOT}'.encode()); os.close(fd); return p
            except (FileExistsError, PermissionError): continue
        time.sleep(2)

def kill_tree(pid):
    subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], capture_output=True)

def render_chunk(cmd, timeout_s):
    slot = acquire()
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        try:
            out, _ = p.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            kill_tree(p.pid); p.communicate(); return False, 'timeout'
        return p.returncode == 0, out[-1500:]
    finally:
        try: os.remove(slot)
        except OSError: pass

def main():
    plan = sys.argv[1]; args = sys.argv[2:]
    chunk = int(args[args.index('--chunk') + 1]) if '--chunk' in args else 2400
    jobs = int(args[args.index('--jobs') + 1]) if '--jobs' in args else 2
    P = runpy.run_path(plan)['PLAN']; name = P['name']
    print(run([PY, '-I', 'build.py', plan]).stdout.strip(), flush=True)
    print(run([PY, '-I', 'mix.py', name]).stdout.strip(), flush=True)
    E = json.load(open(f'edits/{name}.json')); W, H, frames = E['w'], E['h'], int(round(E['dur'] * 30))
    mounts = ['--mount=/frames=cache/frames', '--mount=/clips=cache/clips']
    if '--stills' in args:
        st = args[args.index('--stills') + 1]
        run(['node', RENDER, f'--page=film.html?edit=edits/{name}.json', '--mode=stills', f'--stills={st}', f'--w={W}', f'--h={H}', '--fps=30', '--flip=0', f'--tag={name}', '--out=review/stills', '--timeout=5'] + mounts)
        print('stills ->', os.path.join(ROOT, 'review', 'stills'))
    if '--no-video' in args: return
    os.makedirs('out/parts', exist_ok=True)
    ehash = hashlib.md5(open(f'edits/{name}.json', 'rb').read()).hexdigest()[:12]
    parts = [(i, s, min(chunk, frames - s)) for i, s in enumerate(range(0, frames, chunk))]
    def one(p):
        i, s, n = p; out = f'out/parts/{name}_{i:03d}.mp4'; mark = out + '.done'; key = f'{ehash} {s} {n} {W}x{H}'
        if os.path.exists(out) and os.path.getsize(out) > 0 and os.path.exists(mark) and open(mark).read() == key:
            print(f'  part {i + 1}/{len(parts)} reused', flush=True); return out
        cmd = ['node', RENDER, f'--page=film.html?edit=edits/{name}.json', '--mode=video', f'--w={W}', f'--h={H}', '--fps=30', f'--start={s}', f'--frames={n}',
               '--flip=0', '--cq=19', f'--out={out}', '--timeout=30'] + mounts
        limit = 120 + n / 6.0          # generous: ~6 fps worst case + startup
        for attempt in range(3):
            ok, log = render_chunk(cmd, limit)
            if ok and os.path.exists(out) and os.path.getsize(out) > 0:
                open(mark, 'w').write(key); print(f'  part {i + 1}/{len(parts)} done', flush=True); return out
            print(f'  part {i + 1}/{len(parts)} attempt {attempt + 1} failed: {log.strip()[-300:]}', flush=True)
        raise RuntimeError(f'part {i} failed 3 times')
    with ThreadPoolExecutor(jobs) as ex: outs = list(ex.map(one, parts))
    lst = f'out/parts/{name}_list.txt'
    open(lst, 'w').write(''.join(f"file '{os.path.abspath(o)}'\n" for o in outs))
    vid = f'out/parts/{name}_v.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', vid])
    variants = [(f'audio/{name}_mix.wav', f'out/{name}.mp4')]
    if '--clean' in args or P.get('clean'):
        run([PY, '-I', 'mix.py', name, '--clean']); variants.append((f'audio/{name}_mix_clean.wav', f'out/{name}_clean.mp4'))
    for wav, final in variants:
        m = run(['ffmpeg', '-hide_banner', '-nostats', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-']).stderr
        j = json.loads(m[m.rindex('{'):m.rindex('}') + 1])
        ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
              f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
        # linear loudnorm can't hold the ceiling when it adds a lot of gain -> brick-wall limiter at -1.5 dBFS after it
        run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', ln + ',aresample=48000,alimiter=limit=0.84:level=false:attack=3:release=60',
             '-c:a', 'aac', '-b:a', '384k', '-ar', '48000', '-movflags', '+faststart', '-shortest', final])
        m2 = run(['ffmpeg', '-hide_banner', '-nostats', '-i', final, '-af', 'ebur128=peak=true', '-f', 'null', '-']).stderr
        I = re.findall(r'I:\s+(-?[\d.]+) LUFS', m2); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', m2)
        print(f'DONE {final}  {E["dur"]:.1f}s  {I[-1] if I else "?"} LUFS  TP {TP[-1] if TP else "?"} dBFS', flush=True)

if __name__ == '__main__':
    try: main()
    except RuntimeError as e: raise SystemExit(str(e))
