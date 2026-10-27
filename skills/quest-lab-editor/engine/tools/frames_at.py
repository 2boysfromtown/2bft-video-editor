"""Tile frames of a finished video at given output times. usage: frames_at.py <video> <out.jpg> <tile_w> <cols> t1,t2,..."""
import subprocess, sys, os, tempfile
from PIL import Image, ImageDraw
v, out, w, cols = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); ts = [float(x) for x in sys.argv[5].split(',')]
tmp = tempfile.mkdtemp(); ims = []
for i, t in enumerate(ts):
    p = os.path.join(tmp, f'{i}.jpg'); subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', v, '-frames:v', '1', '-vf', f'scale={w}:-2', p], check=True)
    im = Image.open(p).convert('RGB'); ImageDraw.Draw(im).rectangle([0, 0, 70, 18], fill='black'); ImageDraw.Draw(im).text((3, 3), f'{t:.1f}', fill='yellow'); ims.append(im)
h = ims[0].height; rows = (len(ims) + cols - 1) // cols; s = Image.new('RGB', (cols * w, rows * h))
for i, im in enumerate(ims): s.paste(im, ((i % cols) * w, (i // cols) * h))
s.save(out, quality=85); print(out, s.size)
