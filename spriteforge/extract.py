"""Cut a character out of a screenshot.

Works on real pixel art and on AI-generated "pixel-look" images (JPEG noise, no true grid) alike:
    1. colour-distance mask against the background colour (auto: median of the region's border)
    2. keep the largest connected component + any component that sits inside its bounding box (hair strands,
       a detached horn, a glove) — never the whole thresholded mess
    3. close small gaps and fill holes so dark outline pixels that matched the background are recovered

Gotcha learned the hard way: never drop components that touch the crop edge — if the crop is tight, the horn
touches the top edge and the whole body goes with it. Widen the region instead.
"""
from __future__ import annotations
from PIL import Image
import numpy as np
from scipy import ndimage


def auto_bg(rgb: np.ndarray) -> np.ndarray:
    border = np.concatenate([rgb[:6].reshape(-1, 3), rgb[-6:].reshape(-1, 3), rgb[:, :6].reshape(-1, 3), rgb[:, -6:].reshape(-1, 3)])
    return np.median(border, axis=0)


def extract(image: str | Image.Image, region: tuple[int, int, int, int] | None = None, bg=None,
            thresh: float = 20, min_component: int = 12, margin: int = 6, pad: int = 2) -> Image.Image:
    """Return an RGBA crop of the character. region = (x0, y0, x1, y1) in image pixels; default = whole image."""
    im = Image.open(image).convert("RGB") if isinstance(image, str) else image.convert("RGB")
    a = np.array(im).astype(float)
    x0, y0, x1, y1 = region or (0, 0, im.width, im.height)
    reg = a[y0:y1, x0:x1]
    bgc = np.array(bg, float) if bg is not None else auto_bg(reg)
    d = np.sqrt(((reg - bgc) ** 2).sum(-1))
    mask = d > thresh
    lab, n = ndimage.label(mask)
    if n == 0:
        raise ValueError("nothing found above the background threshold")
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    big = int(np.argmax(sizes)) + 1
    ys, xs = np.where(lab == big)
    bx0, by0, bx1, by1 = xs.min() - margin, ys.min() - margin, xs.max() + margin, ys.max() + margin
    keep = np.zeros_like(mask)
    for i, s in enumerate(sizes, 1):
        if s < min_component:
            continue
        yy, xx = np.where(lab == i)
        if xx.min() >= bx0 and xx.max() <= bx1 and yy.min() >= by0 and yy.max() <= by1:
            keep |= lab == i
    keep = ndimage.binary_closing(keep, iterations=2)
    keep = ndimage.binary_fill_holes(keep)
    # a detached blob far from the body (a star, a coin) that still fell inside the box: keep only what is
    # connected after closing, i.e. the largest component of `keep`
    lab2, n2 = ndimage.label(keep)
    if n2 > 1:
        sizes2 = ndimage.sum(keep, lab2, range(1, n2 + 1))
        keep = lab2 == (int(np.argmax(sizes2)) + 1)
    ys, xs = np.where(keep)
    out = np.zeros((reg.shape[0], reg.shape[1], 4), np.uint8)
    out[..., :3] = reg.astype(np.uint8)
    out[..., 3] = keep * 255
    crop = Image.fromarray(out).crop((max(0, xs.min() - pad), max(0, ys.min() - pad), xs.max() + pad + 1, ys.max() + pad + 1))
    crop.info["origin"] = (x0 + max(0, xs.min() - pad), y0 + max(0, ys.min() - pad))
    return crop


def paint_out(image: str | Image.Image, cut: Image.Image, origin: tuple[int, int], bg, dilate: int = 5) -> Image.Image:
    """Remove the character from the source (fill its silhouette with the background colour) so the
    animated sprite can be composited back over its own scene."""
    im = Image.open(image).convert("RGB") if isinstance(image, str) else image.convert("RGB")
    arr = np.array(im)
    m = np.zeros(arr.shape[:2], bool)
    ox, oy = origin
    cm = np.array(cut)[..., 3] > 0
    m[oy:oy + cm.shape[0], ox:ox + cm.shape[1]] = cm
    m = ndimage.binary_dilation(m, iterations=dilate)
    arr[m] = bg
    return Image.fromarray(arr)
