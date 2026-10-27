"""Grab frames at given source times and tile them with time labels.
usage: grab.py <video> <out.jpg> <width> <cols> t1 t2 ...   (times in seconds or mm:ss)"""
import sys, subprocess, os, tempfile
from PIL import Image, ImageDraw, ImageFont
video, out, w, cols = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
def ts(x):
    if ':' in x: m, s = x.split(':'); return int(m) * 60 + float(s)
    return float(x)
times = [ts(x) for x in sys.argv[5:]]
tmp = tempfile.mkdtemp(); ims = []
for i, t in enumerate(times):
    p = os.path.join(tmp, f'{i}.jpg')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', video, '-frames:v', '1', '-vf', f'scale={w}:-2', '-q:v', '3', p], check=True)
    ims.append(Image.open(p).convert('RGB'))
h = ims[0].height; rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * h)); d = ImageDraw.Draw(sheet)
try: f = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', max(14, w // 28))
except Exception: f = ImageFont.load_default()
for i, (im, t) in enumerate(zip(ims, times)):
    x, y = (i % cols) * w, (i // cols) * h; sheet.paste(im, (x, y))
    lab = f'{int(t // 60):02d}:{t % 60:05.2f}'; d.rectangle([x, y, x + w // 6, y + w // 22], fill='black'); d.text((x + 4, y + 2), lab, fill='yellow', font=f)
sheet.save(out, quality=82); print(out, sheet.size)
