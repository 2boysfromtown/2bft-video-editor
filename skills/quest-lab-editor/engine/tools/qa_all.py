"""Measure every exported mp4 (duration, size, LUFS, true peak, video stream) and build 1-fps contact sheets for the given names."""
import glob, os, re, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
EXP = os.environ.get('QL_EXPORTS', 'exports')   # folder of finished mp4s (run from the project folder)
for f in sorted(glob.glob(os.path.join(EXP, '**', '*.mp4'), recursive=True)):
    d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=width,height,codec_name', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.split()
    m = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
    I = re.findall(r'I:\s+(-?[\d.]+) LUFS', m); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', m)
    print(f"{os.path.basename(f):34s} {float(d[-1]):6.1f}s  {os.path.getsize(f)/2**20:6.1f} MB  {I[-1] if I else '?':>6} LUFS  TP {TP[-1] if TP else '?':>5}  {' '.join(d[:-1])}")
names = sys.argv[1:]
for n in names:
    out = os.path.join('work', f'qa_{n}', 'f'); os.makedirs(out, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(EXP, 'shorts', n + '.mp4'), '-vf', 'fps=1,scale=216:-2', '-q:v', '5', os.path.join(out, 'f_%03d.jpg')], check=True)
    subprocess.run([sys.executable, '-I', os.path.join('tools', 'contact_sheet.py'), out, os.path.join('work', f'qa_{n}', 'sheet'), '1', '12', '5'], check=True)
