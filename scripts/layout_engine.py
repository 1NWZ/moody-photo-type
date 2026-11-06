"""Measured text blocks for three reference-inspired layout families."""
from PIL import Image, ImageDraw, ImageFont, ImageChops

# role: (normalized box, min/max font ratio, default ratio, default leading)
PRESETS = {
    'vertical': {'main': ([.175,.20,.65,.60], (.085,.095), .09, 1.24)},
    'split': {
        'title': ([.15,.13,.70,.16], (.10,.16), .13, 1.05),
        'body': ([.20,.70,.60,.23], (.045,.075), .06, 1.10),
        'top_left': ([.04,.025,.25,.055], (.018,.035), .025, 1.1),
        'top_right': ([.71,.025,.25,.055], (.018,.035), .025, 1.1),
        'bottom_left': ([.04,.93,.25,.045], (.018,.035), .025, 1.1),
        'bottom_right': ([.71,.93,.25,.045], (.018,.035), .025, 1.1),
    },
    'micro': {
        'left': ([.25,.46,.12,.08], (.010,.016), .012, 1.12),
        'main': ([.40,.46,.25,.08], (.010,.016), .012, 1.12),
        'right': ([.68,.46,.12,.08], (.010,.016), .012, 1.12),
    },
}
REQUIRED = {'vertical': {'main'}, 'split': {'title','body'}, 'micro': {'main'}}


def render_blocks(size, font_path, layout_id, blocks):
    """Return full-canvas ink mask and per-block measured bounds; never shrink text."""
    if layout_id not in PRESETS or not isinstance(blocks, list) or not blocks:
        raise ValueError('Provide a known layout and a nonempty block list')
    w,h = size
    canvas = Image.new('L', size, 0)
    records, used = [], set()
    for block in blocks:
        role = block['role']
        if role not in PRESETS[layout_id] or role in used:
            raise ValueError('Unknown or repeated text role')
        used.add(role)
        box, limits, default_ratio, default_leading = PRESETS[layout_id][role]
        ratio = float(block.get('font_ratio', default_ratio))
        leading = float(block.get('line_spacing', default_leading))
        if not limits[0] <= ratio <= limits[1] or not 1 <= leading <= 1.30:
            raise ValueError('Text size or leading outside layout limits')
        if layout_id == 'vertical' and not 1.18 <= leading <= 1.30:
            raise ValueError('Vertical leading must be 1.18–1.30')
        lines = block['lines']
        if not isinstance(lines,list) or not lines or not all(isinstance(s,str) and s.strip() and '\n' not in s for s in lines):
            raise ValueError('Provide nonempty explicit single-line strings')
        px = max(1,round(w*ratio))
        font = ImageFont.truetype(str(font_path),px)
        bounds = [font.getbbox(s) for s in lines]
        step = round(px*leading)
        # Use a common baseline offset to preserve ascenders and descenders.
        top = min(b[1] for b in bounds)
        iw = max(b[2]-b[0] for b in bounds)
        ih = max(i*step+b[3]-top for i,b in enumerate(bounds))
        if iw <= 0 or ih <= 0 or iw > box[2]*w+1 or ih > box[3]*h+1:
            raise ValueError(f'{layout_id}/{role}: text does not fit; rewrite or rebreak lines')
        ink = Image.new('L',(iw+4,ih+4),0)
        draw = ImageDraw.Draw(ink)
        align = 'left' if layout_id == 'micro' or role.endswith('left') else 'right' if role.endswith('right') else 'center'
        for i,(line,b) in enumerate(zip(lines,bounds)):
            dx = 0 if align == 'left' else iw-(b[2]-b[0]) if align == 'right' else (iw-(b[2]-b[0]))/2
            draw.text((round(dx)-b[0]+2,i*step-top+2),line,font=font,fill=255)
        ink = ink.crop(ink.getbbox())
        x = box[0]*w if align=='left' else (box[0]+box[2])*w-ink.width if align=='right' else (box[0]+box[2]/2)*w-ink.width/2
        y = box[1]*h if layout_id=='micro' else (box[1]+box[3]/2)*h-ink.height/2
        x,y = round(x),round(y)
        if layout_id=='vertical' and (ink.width < .35*w-1 or ink.height < .30*h-1):
            raise ValueError('Vertical text group is too small; rewrite within the fixed font range')
        layer = Image.new('L',size,0); layer.paste(ink,(x,y))
        canvas = ImageChops.lighter(canvas,layer)
        records.append({'role':role,'lines':lines,'font_size':px,'box':box,'text_bounds_before_occlusion':[x,y,x+ink.width,y+ink.height]})
    if not REQUIRED[layout_id] <= used:
        raise ValueError('Missing required layout roles')
    return canvas, records
