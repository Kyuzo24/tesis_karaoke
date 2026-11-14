"""Render the existing UI brand mark as a multi-size Windows icon."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
size = 1024
canvas = Image.new('RGBA', (size, size))
draw = ImageDraw.Draw(canvas)
draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=195, fill='#f1c55b')
font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 420)
box = draw.textbbox((0, 0), 'K', font=font)
draw.text(((size - box[2] + box[0]) / 2 - box[0],
           (size - box[3] + box[1]) / 2 - box[1]), 'K', font=font, fill='#18140b')
canvas.save(root / 'ui_live/icon.ico', bitmap_format='bmp',
            sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
