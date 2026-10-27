"""Tile frames into labelled contact sheets. usage: contact_sheet.py <frames_dir> <out_prefix> <step_seconds> [cols] [rows] [offset]"""
import sys, glob, os
from PIL import Image, ImageDraw, ImageFont

src, out, step = sys.argv[1], sys.argv[2], float(sys.argv[3])
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 5
rows = int(sys.argv[5]) if len(sys.argv) > 5 else 4
offset = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
files = sorted(glob.glob(os.path.join(src, "*.jpg")))
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
except Exception:
    font = ImageFont.load_default()
per = cols * rows
w0, h0 = Image.open(files[0]).size
for k in range(0, len(files), per):
    sheet = Image.new("RGB", (cols * w0, rows * h0), "black")
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files[k:k + per]):
        im = Image.open(f)
        x, y = (i % cols) * w0, (i // cols) * h0
        sheet.paste(im, (x, y))
        t = offset + (k + i) * step
        lab = f"{int(t//60):02d}:{t%60:04.1f}" if step < 1 else f"{int(t//60):02d}:{int(t%60):02d}"
        d.rectangle([x, y, x + 92, y + 28], fill="black")
        d.text((x + 4, y + 2), lab, fill="yellow", font=font)
    sheet.save(f"{out}_{k//per:02d}.jpg", quality=80)
print("sheets:", (len(files) + per - 1) // per)
