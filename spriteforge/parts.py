"""Parts map: label which pixels belong to which body part, so a re-pose erases exactly the right ones.

Parts are polygons in sprite coordinates (plan them on the dump), assigned in priority order (first wins).
`segment` returns one boolean mask per part; `preview` paints them in flat colours over black so you can check
the split at a glance (the "weird coloured" picture). Nothing here moves pixels — it's a planning tool.
"""
from __future__ import annotations
from PIL import Image, ImageDraw
import numpy as np
from .canvas import Sprite

COLOURS = [(255, 0, 0), (0, 200, 255), (0, 120, 255), (255, 200, 0), (255, 120, 0), (200, 0, 255), (0, 220, 80),
           (255, 0, 200), (120, 255, 255), (255, 255, 120)]


def segment(sp: Sprite, parts: dict[str, list[tuple[int, int]]], colour_filter=None) -> dict[str, np.ndarray]:
    """parts: {name: polygon}. Optional colour_filter(name, r, g, b) -> bool mask to keep out e.g. skirt-red from a
    leg polygon. Priority = dict order; each pixel goes to the first part whose polygon contains it."""
    W, H = sp.size
    solid = sp.solid()
    taken = np.zeros((H, W), bool)
    masks = {}
    r, g, b = (sp.a[..., i].astype(int) for i in range(3))
    for name, poly in parts.items():
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        mask = (np.array(m) > 0) & solid & ~taken
        if colour_filter is not None:
            mask &= colour_filter(name, r, g, b)
        masks[name] = mask
        taken |= mask
    masks["_rest"] = solid & ~taken
    return masks


def preview(sp: Sprite, masks: dict[str, np.ndarray], scale: int = 8, side_by_side: bool = True) -> Image.Image:
    W, H = sp.size
    seg = np.zeros((H, W, 4), np.uint8)
    for i, (name, m) in enumerate(masks.items()):
        c = (90, 90, 90) if name == "_rest" else COLOURS[i % len(COLOURS)]
        seg[m] = c + (255,)
    out = Image.new("RGBA", (W * 2 if side_by_side else W, H), (0, 0, 0, 255))
    if side_by_side:
        out.alpha_composite(sp.image(), (0, 0))
    out.alpha_composite(Image.fromarray(seg), (W if side_by_side else 0, 0))
    return out.resize((out.width * scale, out.height * scale), Image.NEAREST)


def erase_parts(sp: Sprite, masks: dict[str, np.ndarray], names) -> Sprite:
    out = sp.copy()
    for n in names:
        out.a[masks[n]] = 0
    return out
