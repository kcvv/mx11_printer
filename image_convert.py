"""
image_convert.py - Image and text conversion utilities for MX11 printer

This module provides functions to:
- Convert text to a printable image (with word wrapping, font selection, etc.)
- Convert and preprocess images for the printer (binarization, dithering, resizing, etc.)

All functions are designed to output a PIL Image ready for mx11.py.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import logging
import numpy as np

def text_to_image(text_content, width=384, font_name='arial.ttf', font_size=20):
    """
    Converts a string of text into a black and white PIL Image, with word wrapping.
    """
    # Find font path (Windows)
    font_path = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', font_name)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        logging.warning(f"Could not load font '{font_name}' at '{font_path}': {e}. Using default font.")
        font = ImageFont.load_default()

    # Word wrap using font.getbbox for width measurement
    lines = []
    for paragraph in text_content.split('\n'):
        words = paragraph.split(' ')
        line = ''
        for word in words:
            test_line = line + (' ' if line else '') + word
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0] if bbox else 0
            if w > width and line:
                lines.append(line)
                line = word
            else:
                line = test_line
        if line:
            lines.append(line)

    # Estimate image height
    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    img_height = line_height * len(lines)
    image = Image.new('L', (width, img_height), color=255)
    draw = ImageDraw.Draw(image)
    y_text = 0
    for line in lines:
        draw.text((0, y_text), line, font=font, fill=0)
        y_text += line_height
    return image

# Placeholder for future image conversion functions (binarization, dithering, etc.)


from PIL import ImageEnhance

def _bayer_dither(img, matrix_size=8):
    """Ordered/Bayer dithering using a threshold matrix."""
    bayer_matrix = np.array([
        [0, 48, 12, 60, 3, 51, 15, 63],
        [32, 16, 44, 28, 35, 19, 47, 31],
        [8, 56, 4, 52, 11, 59, 7, 55],
        [40, 24, 36, 20, 43, 27, 39, 23],
        [2, 50, 14, 62, 1, 49, 13, 61],
        [34, 18, 46, 30, 33, 17, 45, 29],
        [10, 58, 6, 54, 9, 57, 5, 53],
        [42, 26, 38, 22, 41, 25, 37, 21],
    ])
    img_np = np.array(img, dtype=np.uint8)
    h, w = img_np.shape
    out = np.zeros((h, w), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            threshold = bayer_matrix[y % matrix_size, x % matrix_size]
            out[y, x] = 255 if img_np[y, x] > (threshold * 4) else 0
    return Image.fromarray(out, mode='L').convert('1')

def _atkinson_dither(img):
    img_np = np.array(img, dtype=np.float32)
    h, w = img_np.shape
    for y in range(h):
        for x in range(w):
            old = img_np[y, x]
            new = 255 if old > 127 else 0
            err = old - new
            img_np[y, x] = new
            for dx, dy in [(1,0),(2,0),(-1,1),(0,1),(1,1),(0,2)]:
                if 0 <= x+dx < w and 0 <= y+dy < h:
                    img_np[y+dy, x+dx] += err * 1/8
    return Image.fromarray(img_np.clip(0,255).astype(np.uint8), mode='L').convert('1')

def _burkes_dither(img):
    img_np = np.array(img, dtype=np.float32)
    h, w = img_np.shape
    for y in range(h):
        for x in range(w):
            old = img_np[y, x]
            new = 255 if old > 127 else 0
            err = old - new
            img_np[y, x] = new
            for dx, dy, factor in [
                (1,0,8/32),(2,0,4/32),(-2,1,2/32),(-1,1,4/32),(0,1,8/32),(1,1,4/32),(2,1,2/32)
            ]:
                if 0 <= x+dx < w and 0 <= y+dy < h:
                    img_np[y+dy, x+dx] += err * factor
    return Image.fromarray(img_np.clip(0,255).astype(np.uint8), mode='L').convert('1')

def _stucki_dither(img):
    img_np = np.array(img, dtype=np.float32)
    h, w = img_np.shape
    for y in range(h):
        for x in range(w):
            old = img_np[y, x]
            new = 255 if old > 127 else 0
            err = old - new
            img_np[y, x] = new
            for dx, dy, factor in [
                (1,0,8/42),(2,0,4/42),(-2,1,2/42),(-1,1,4/42),(0,1,8/42),(1,1,4/42),(2,1,2/42),
                (-2,2,1/42),(-1,2,2/42),(0,2,4/42),(1,2,2/42),(2,2,1/42)
            ]:
                if 0 <= x+dx < w and 0 <= y+dy < h:
                    img_np[y+dy, x+dx] += err * factor
    return Image.fromarray(img_np.clip(0,255).astype(np.uint8), mode='L').convert('1')

def _jarvis_judice_ninke_dither(img):
    img_np = np.array(img, dtype=np.float32)
    h, w = img_np.shape
    for y in range(h):
        for x in range(w):
            old = img_np[y, x]
            new = 255 if old > 127 else 0
            err = old - new
            img_np[y, x] = new
            for dx, dy, factor in [
                (1,0,7/48),(2,0,5/48),(-2,1,3/48),(-1,1,5/48),(0,1,7/48),(1,1,5/48),(2,1,3/48),
                (-2,2,1/48),(-1,2,3/48),(0,2,5/48),(1,2,3/48),(2,2,1/48)
            ]:
                if 0 <= x+dx < w and 0 <= y+dy < h:
                    img_np[y+dy, x+dx] += err * factor
    return Image.fromarray(img_np.clip(0,255).astype(np.uint8), mode='L').convert('1')

def _sierra_dither(img):
    img_np = np.array(img, dtype=np.float32)
    h, w = img_np.shape
    for y in range(h):
        for x in range(w):
            old = img_np[y, x]
            new = 255 if old > 127 else 0
            err = old - new
            img_np[y, x] = new
            for dx, dy, factor in [
                (1,0,5/32),(2,0,3/32),(-2,1,2/32),(-1,1,4/32),(0,1,5/32),(1,1,4/32),(2,1,2/32),
                (-1,2,2/32),(0,2,3/32),(1,2,2/32)
            ]:
                if 0 <= x+dx < w and 0 <= y+dy < h:
                    img_np[y+dy, x+dx] += err * factor
    return Image.fromarray(img_np.clip(0,255).astype(np.uint8), mode='L').convert('1')

def _random_dither(img):
    img_np = np.array(img, dtype=np.uint8)
    noise = np.random.randint(-64, 64, img_np.shape)
    img_np = np.clip(img_np + noise, 0, 255)
    return Image.fromarray(np.where(img_np > 127, 255, 0).astype(np.uint8), mode='L').convert('1')

def preprocess_image(
    image_path,
    width=384,
    dither='floyd-steinberg',
    threshold=128,
    contrast=1.0,
    brightness=1.0,
    rotate=0
):
    """
    Loads and preprocesses an image for the printer (resize, grayscale, enhance, binarize, dither).
    Returns a PIL Image.
    Params:
        dither: 'none', 'floyd-steinberg', or 'default' (alias for 'floyd-steinberg')
        threshold: 0-255, for manual thresholding
        contrast: float, 1.0 = no change
        brightness: float, 1.0 = no change
        rotate: degrees to rotate (e.g., 90, 180)
    """
    img = Image.open(image_path).convert('L')
    if rotate:
        img = img.rotate(rotate, expand=True)
    new_height = int(img.height * width / img.width)
    img = img.resize((width, new_height), Image.LANCZOS)
    # Enhance contrast/brightness
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    # Dithering and binarization
    dither = dither.lower() if isinstance(dither, str) else dither
    if dither in ('floyd-steinberg', 'default'):
        img = img.convert('1', dither=Image.FLOYDSTEINBERG)
    elif dither == 'none':
        img = img.convert('1', dither=Image.NONE)
    elif dither == 'manual':
        img = img.point(lambda x: 255 if x > threshold else 0, '1')
    elif dither == 'bayer' or dither == 'ordered':
        img = _bayer_dither(img)
    elif dither == 'atkinson':
        img = _atkinson_dither(img)
    elif dither == 'burkes':
        img = _burkes_dither(img)
    elif dither == 'stucki':
        img = _stucki_dither(img)
    elif dither == 'jarvis' or dither == 'jarvis-judice-ninke':
        img = _jarvis_judice_ninke_dither(img)
    elif dither == 'sierra':
        img = _sierra_dither(img)
    elif dither == 'random':
        img = _random_dither(img)
    else:
        img = img.convert('1', dither=Image.FLOYDSTEINBERG)
    return img
