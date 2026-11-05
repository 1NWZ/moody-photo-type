#!/usr/bin/env python3
"""Rasterize visually verified normalized person contours to a soft foreground mask."""
import argparse,json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter

def build_mask(plan, output):
    width,height=plan['size']
    if not all(isinstance(v,int) and 1<=v<=6000 for v in (width,height)):
        raise ValueError('size must contain positive pixel dimensions <= 6000')
    mask=Image.new('L',(width*4,height*4),0)
    draw=ImageDraw.Draw(mask)
    for polygon in plan['polygons']:
        if len(polygon)<3 or not all(len(p)==2 and all(isinstance(v,(float,int)) and math.isfinite(v) and 0<=v<=1 for v in p) for p in polygon):
            raise ValueError('Each polygon needs >=3 normalized [x,y] points')
        draw.polygon([(round(x*width*4),round(y*height*4)) for x,y in polygon],fill=255)
    mask=mask.resize((width,height),Image.Resampling.LANCZOS)
    mask=mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.35))
    if output.exists():raise ValueError('Mask output already exists')
    mask.save(output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('contours',type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();build_mask(json.loads(a.contours.read_text()),a.output)
