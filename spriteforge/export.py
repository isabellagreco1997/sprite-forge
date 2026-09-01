"""Export helpers: upscaled PNG, spritesheet, GIF, contact sheet."""
from __future__ import annotations
from PIL import Image
from .canvas import Sprite


def up(im: Image.Image, k: int) -> Image.Image:
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def _img(f):
    return f.image() if isinstance(f, Sprite) else f


def spritesheet(frames, path: str, scale: int = 1, bg=None) -> Image.Image:
    ims = [_img(f) for f in frames]
    w, h = ims[0].size
    sheet = Image.new("RGBA", (w * len(ims), h), (0, 0, 0, 0) if bg is None else tuple(bg) + (255,))
    for i, im in enumerate(ims):
        sheet.alpha_composite(im, (i * w, 0))
    sheet = up(sheet, scale) if scale > 1 else sheet
    sheet.save(path)
    return sheet


def gif(frames, path: str, ms: int = 110, scale: int = 8, bg=(30, 20, 40), colors: int = 64):
    """bg=None → transparent background with the sprite's true colours (index 255 reserved for transparency)."""
    out = []
    for f in frames:
        im = _img(f)
        if bg is None:
            big = up(im, scale)
            alpha = big.split()[3]
            pim = big.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255)
            pim.paste(255, Image.eval(alpha, lambda a: 255 if a <= 128 else 0))
            pim.info["transparency"] = 255
            out.append(pim)
        else:
            base = Image.new("RGBA", im.size, tuple(bg) + (255,))
            base.alpha_composite(im)
            out.append(up(base, scale).convert("P", palette=Image.ADAPTIVE, colors=colors))
    kw = dict(save_all=True, append_images=out[1:], duration=ms, loop=0)
    if bg is None:
        kw.update(transparency=255, disposal=2)
    out[0].save(path, **kw)


def png(frame, path: str, scale: int = 8):
    up(_img(frame), scale).save(path)


def contact_sheet(paths: list[str], out: str, cols: int = 4, width: int = 480):
    ims = [Image.open(p) for p in paths]
    k = width / ims[0].width
    w, h = int(ims[0].width * k), int(ims[0].height * k)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), (0, 0, 0))
    for i, im in enumerate(ims):
        sheet.paste(im.convert("RGB").resize((w, h)), ((i % cols) * w, (i // cols) * h))
    sheet.save(out)
    return sheet
