#!/usr/bin/env python3
"""Apply a fixed photo grade and typeset model-planned captions in a reproducible batch."""
import argparse
import json
import math
import re
import random
import secrets
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageChops
from grade_photo import grade
from layout_engine import PRESETS, render_blocks


def resolve(base, value):
    p = Path(value).expanduser()
    return p if p.is_absolute() else base / p


def render(manifest, output):
    base = manifest.parent
    data = json.loads(manifest.read_text(encoding='utf-8'))
    items = data['items']
    seed = data.get('layout_seed', secrets.randbits(32))
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError('layout_seed must be an integer')
    rng = random.Random(seed)
    previous_layout = None
    planned = {}
    if not items:
        raise ValueError('items must not be empty')
    font_path = resolve(base, data['font'])
    if not font_path.is_file():
        raise ValueError('Provide an existing font file that covers every caption character')
    width = int(data.get('width', 1080))
    ratio = float(data.get('font_ratio', 0.09))
    leading = float(data.get('line_spacing', 1.24))
    if not 320 <= width <= 6000 or not 0.04 <= ratio <= 0.16 or not 1 <= leading <= 2:
        raise ValueError('Invalid width, font_ratio or line_spacing')
    # Preflight all files and layout before creating any outputs.
    prepared, seen = [], set()
    shared_size = round(width * ratio)
    for item in items:
        key = str(item['id'])
        if not re.fullmatch(r'[A-Za-z0-9_-]+', key) or key in seen:
            raise ValueError('Each id must be unique and contain only A-Z a-z 0-9 _ -')
        seen.add(key)
        if 'layouts' in item:
            variants = item['layouts']
            if not isinstance(variants, dict) or not variants or set(variants)-set(PRESETS):
                raise ValueError(f'{key}: invalid layout candidates')
            eligible = list(variants)
            if len(eligible)>1 and previous_layout in eligible:
                eligible.remove(previous_layout)
            chosen = rng.choice(sorted(eligible))
            previous_layout = chosen
            planned[key] = (chosen, variants[chosen])
            lines = []
        else:
            lines = item['lines']
        if not isinstance(lines, list) or not all(isinstance(s, str) and s.strip() and '\n' not in s for s in lines):
            raise ValueError(f'{key}: lines must be a list of single-line strings (empty means no text)')
        box = item.get('box', [0.14, 0.18, 0.72, 0.64])
        if len(box) != 4 or not all(isinstance(v, (float, int)) and math.isfinite(v) for v in box):
            raise ValueError(f'{key}: box must contain four finite numbers')
        x, y, bw, bh = box
        if min(x, y) < 0 or min(bw, bh) <= 0 or x + bw > 1 or y + bh > 1:
            raise ValueError(f'{key}: box outside canvas')
        if abs(x+bw/2-0.5) > 1e-6 or abs(y+bh/2-0.5) > 1e-6:
            raise ValueError(f'{key}: text box must be centered on the canvas')
        with Image.open(resolve(base, item['image'])) as src:
            im = ImageOps.exif_transpose(src).convert('RGB')
        crop = item.get('crop')
        if crop is not None:
            if len(crop) != 4 or not all(isinstance(v,(float,int)) and math.isfinite(v) for v in crop):
                raise ValueError(f'{key}: crop must be four finite numbers')
            left, top, right, bottom = crop
            if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
                raise ValueError(f'{key}: invalid crop coordinates')
            pixels = (round(left*im.width), round(top*im.height), round(right*im.width), round(bottom*im.height))
            if pixels[2] <= pixels[0] or pixels[3] <= pixels[1]:
                raise ValueError(f'{key}: crop is smaller than one pixel')
            im = im.crop(pixels)
        height = round(im.height * width / im.width)
        im = im.resize((width, height), Image.Resampling.LANCZOS)
        im, grade_info = grade(im, {**data.get('grade', {}), **item.get('grade', {})})
        foreground = None
        if item.get('foreground_mask'):
            with Image.open(resolve(base, item['foreground_mask'])) as mask:
                foreground = mask.convert('L')
            if foreground.size != im.size:
                raise ValueError(f'{key}: foreground mask must match the final canvas dimensions')
        if key in planned:
            if foreground is None:
                raise ValueError(f'{key}: a subject mask is required for reference layouts')
            chosen, blocks = planned[key]
            text_mask, block_records = render_blocks(im.size, font_path, chosen, blocks)
            planned[key] = (chosen, text_mask, block_records)
            prepared.append((key, im, lines, box, grade_info, crop, foreground))
            continue
        size = shared_size
        while size >= round(width * 0.06):
            font = ImageFont.truetype(str(font_path), size)
            bounds = [font.getbbox(s) for s in lines]
            step = round(size * leading)
            block_height = (len(lines) - 1) * step + max((b[3]-b[1] for b in bounds), default=0)
            if max((b[2]-b[0] for b in bounds), default=0) <= bw*width and block_height <= bh*height:
                break
            size -= 1
        else:
            raise ValueError(f'{key}: text does not fit; shorten caption or enlarge box')
        prepared.append((key, im, lines, box, grade_info, crop, foreground))
        shared_size = min(shared_size, size)
    if output.exists():
        raise ValueError('Output directory already exists; choose a new directory to preserve prior work')
    output.mkdir(parents=True)
    (output/'graded').mkdir()
    results, thumbs = [], []
    for key, im, lines, box, grade_info, crop, foreground in prepared:
        im.save(output/'graded'/f'{key}.png')
        w, h = im.size
        block_records = None
        chosen = None
        if key in planned:
            chosen, centered, block_records = planned[key]
        else:
            font = ImageFont.truetype(str(font_path), shared_size)
            bounds = [font.getbbox(s) for s in lines]
            step = round(shared_size * leading)
            block_height = (len(lines)-1)*step + max((b[3]-b[1] for b in bounds), default=0)
            text_mask = Image.new('L', (w, h), 0)
            draw = ImageDraw.Draw(text_mask)
            for i, (line, bound) in enumerate(zip(lines, bounds)):
                left = w/2 - (bound[2]-bound[0])/2 - bound[0]
                draw.text((round(left), i*step-bound[1]), line, font=font, fill=255)
            ink_box = text_mask.getbbox()
            centered = Image.new('L', (w,h), 0)
            if ink_box:
                ink = text_mask.crop(ink_box)
                centered.paste(ink, (round((w-ink.width)/2), round((h-ink.height)/2)))
        centered_bounds = centered.getbbox()
        hidden_pixels = 0
        if foreground is not None:
            overlap = ImageChops.multiply(centered, foreground)
            hidden_pixels = sum(overlap.histogram()[1:])
            centered = ImageChops.multiply(centered, ImageOps.invert(foreground))
        im = Image.composite(Image.new('RGB',im.size,'white'), im, centered)
        filename = f'{key}.jpg'
        im.save(output / filename, quality=95, subsampling=0)
        results.append({'id': key, 'file': filename, 'lines': lines, 'box': box,
                        'size': [w,h], 'font_size': shared_size if chosen is None else None,
                        'layout_id': chosen, 'blocks': block_records, 'grade': grade_info, 'crop': crop,
                        'graded_file': f'graded/{key}.png', 'text_bounds_before_occlusion':centered_bounds,
                        'foreground_mask_applied':foreground is not None,'occluded_text_pixels':hidden_pixels})
        thumb = im.copy()
        thumb.thumbnail((270,360), Image.Resampling.LANCZOS)
        thumbs.append((key, thumb))
    cols = min(3, len(thumbs))
    sheet = Image.new('RGB', (cols*294, math.ceil(len(thumbs)/cols)*402), '#EAE7E1')
    draw = ImageDraw.Draw(sheet)
    label_font = ImageFont.truetype(str(font_path), 16)
    for i, (key, thumb) in enumerate(thumbs):
        ox, oy = (i%cols)*294, (i//cols)*402
        sheet.paste(thumb, (ox+12+(270-thumb.width)//2, oy+12+(360-thumb.height)//2))
        # IDs may be long; keep previews legible without overflowing cells.
        label = key if len(key) <= 22 else key[:19]+'...'
        draw.text((ox+12,oy+376), label, font=label_font, fill='#222222')
    sheet.save(output/'contact-sheet.jpg', quality=92)
    (output/'layout.json').write_text(json.dumps({'layout_seed':seed,'items':results},ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(output/'finals.zip','w',zipfile.ZIP_DEFLATED) as bundle:
        for p in sorted(output.iterdir()):
            if p.suffix in ('.jpg','.json'):
                bundle.write(p,p.name)
    return {'count':len(results), 'font_size':shared_size, 'output':str(output)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(render(args.manifest.resolve(), args.output.resolve()),ensure_ascii=False))
