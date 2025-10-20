"""
preview_dithers.py - Generate preview images for all dithering methods.
"""
from PIL import Image, ImageDraw, ImageFont
import os
import argparse
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
    parser = argparse.ArgumentParser(description='Generate preview images for all dithering methods.')
    parser.add_argument('image_path', type=str, help='Path to the input image file.')
    parser.add_argument('-o', '--output', type=str, default=None, help='Optional output file path.')
    args = parser.parse_args()

    width = 384
    dithers = [
        'floyd-steinberg', 'none', 'manual', 'bayer', 'atkinson',
        'burkes', 'stucki', 'jarvis', 'sierra', 'random'
    ]

    if os.path.exists(args.image_path):
        if args.output:
            out_path = args.output
        else:
            out_path = f"preview_{os.path.splitext(os.path.basename(args.image_path))[0]}.png"
        make_preview_grid(args.image_path, width, dithers, out_path)
    else:
        print(f"File not found: {args.image_path}")

if __name__ == "__main__":
    main()