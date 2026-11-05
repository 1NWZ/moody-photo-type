"""Deterministic restrained dark-tone preset; RGB sRGB inputs, no generative edits."""
import math
from PIL import ImageEnhance, ImageFilter, ImageStat

DEFAULTS = {'strength': 0.7, 'darkening': 0.22, 'saturation': 1.08,
            'light': 0.05, 'detail': 0.12}
LIMITS = {'strength': (0,1), 'darkening': (0,0.5), 'saturation': (0.8,1.25),
          'light': (0,0.15), 'detail': (0,0.3)}


def grade(image, config):
    config = dict(config)
    mode = config.pop('mode', 'fixed')
    if mode not in ('fixed', 'none'):
        raise ValueError('grade.mode must be fixed or none')
    if set(config) - set(DEFAULTS):
        raise ValueError('Unknown grade parameters: '+str(set(config)-set(DEFAULTS)))
    params = {**DEFAULTS, **config}
    for name, value in params.items():
        lo, hi = LIMITS[name]
        if not isinstance(value,(float,int)) or not math.isfinite(value) or not lo <= value <= hi:
            raise ValueError(f'grade.{name} must be within {lo}..{hi}')
    if mode == 'none':
        return image.copy(), {'mode':'none'}
    gray = image.convert('L')
    median = ImageStat.Stat(gray).median[0] / 255
    # Already dark images receive almost no additional darkening.
    exposure_weight = max(0.0, min(1.0, (median-0.12)/0.38))
    exponent = 1 + params['darkening']*exposure_weight
    tone = [round(255*(i/255)**exponent) for i in range(256)]
    result = image.point(tone*3)
    result = ImageEnhance.Color(result).enhance(params['saturation'])
    # Smooth, bounded lift follows existing luminance, never invents a light source.
    light_lut = [min(255,round(i+255*params['light']*4*(i/255)**2*(1-i/255))) for i in range(256)]
    result = result.point(light_lut*3)
    sharpened = result.filter(ImageFilter.UnsharpMask(radius=1.2,percent=60,threshold=3))
    from PIL import Image
    result = Image.blend(result, sharpened, params['detail'])
    result = Image.blend(image, result, params['strength'])
    return result, {'mode':'fixed', **params, 'input_median':round(median,6),
                    'effective_gamma':round(exponent,6), 'preset_version':'1.0'}
