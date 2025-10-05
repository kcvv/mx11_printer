"""
preview_dithers.py - Generate preview images for all dithering methods on test.png and cat.jpg
"""
from PIL import Image, ImageDraw, ImageFont
import os
from image_convert import preprocess_image

def label_image(img, label, width):
    # Add a label above the image
    font_path = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arial.ttf')
    try:
        font = ImageFont.truetype(font_path, 18)
    except Exception:
        font = ImageFont.load_default()
    label_height = 24
    labeled = Image.new('L', (width, img.height + label_height), color=255)
    draw = ImageDraw.Draw(labeled)
    draw.text((5, 2), label, font=font, fill=0)
    labeled.paste(img, (0, label_height))
    return labeled

def make_preview_grid(img_path, width, dithers, out_path):
    previews = []
    for dither in dithers:
        img = preprocess_image(img_path, width=width, dither=dither)
        labeled = label_image(img, dither, width)
        previews.append(labeled)
    # Stack vertically
    total_height = sum(im.height for im in previews)
    grid = Image.new('L', (width, total_height), color=255)
    y = 0
    for im in previews:
        grid.paste(im, (0, y))
        y += im.height
    grid.save(out_path)
    print(f"Saved preview: {out_path}")

def main():
    width = 384
    dithers = [
        'floyd-steinberg', 'none', 'manual', 'bayer', 'atkinson',
        'burkes', 'stucki', 'jarvis', 'sierra', 'random'
    ]
    for fname in ['cat1.jpg', 'buddha.jpg']:
        if os.path.exists(fname):
            out_path = f"preview_{os.path.splitext(fname)[0]}.png"
            make_preview_grid(fname, width, dithers, out_path)
        else:
            print(f"File not found: {fname}")

if __name__ == "__main__":
    main()
