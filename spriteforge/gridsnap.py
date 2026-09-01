"""Find the native pixel grid of a (possibly fake) pixel-art image and snap it to a clean 1x sprite.

AI-generated pixel art has no grid: cells are ~5.4 px, blurred, JPEG-noisy. We brute-force the cell size and
phase that make every cell as uniform as possible, take the median colour per cell, then quantise the palette.
The result is usually SHARPER than the source.
"""
from __future__ import annotations
from PIL import Image
import numpy as np


def _fit(rgb, alpha, s, ox, oy):
    H, W = alpha.shape
    xs = ((np.arange(W) - ox) // s).astype(int)
    ys = ((np.arange(H) - oy) // s).astype(int)
    cid = ys[:, None] * 100000 + xs[None, :]
    ids, cols = cid[alpha], rgb[alpha]
    uniq, inv = np.unique(ids, return_inverse=True)
    cnt = np.bincount(inv)
    var = np.zeros(len(uniq))
    for c in range(3):
        sm = np.bincount(inv, cols[:, c]); sq = np.bincount(inv, cols[:, c] ** 2)
        var += sq / cnt - (sm / cnt) ** 2
    return (var * cnt).sum() / cnt.sum()


def detect_grid(rgba: Image.Image, sizes=None, step: float = 0.5):
    """Cell size + phase of the native grid.

    Within-cell variance always drops as cells get smaller, so the raw minimum is useless (it picks the smallest
    size). The true cell shows up as a sharp DIP against its neighbours instead — we score each size by the
    prominence of that dip and take the most prominent one, then refine the phase at that size."""
    a = np.array(rgba.convert("RGBA")).astype(float)
    alpha = a[..., 3] > 0
    rgb = a[..., :3]
    sizes = np.round(np.arange(3.0, 12.01, 0.1), 1) if sizes is None else np.array(sizes, float)
    best_phase = {}
    curve = []
    for s in sizes:
        best = None
        for ox in np.arange(0, s, step):
            for oy in np.arange(0, s, step):
                sc = _fit(rgb, alpha, s, ox, oy)
                if best is None or sc < best[0]:
                    best = (sc, ox, oy)
        curve.append(best[0]); best_phase[s] = (best[1], best[2])
    curve = np.array(curve)
    if len(sizes) == 1:
        s = float(sizes[0]); ox, oy = best_phase[sizes[0]]
        return s, ox, oy
    prom = np.zeros(len(sizes))
    for i, s in enumerate(sizes):
        nb = [j for j in range(len(sizes)) if 0.15 < abs(sizes[j] - s) <= 0.5]
        if nb:
            prom[i] = 1 - curve[i] / curve[nb].mean()
    i = int(np.argmax(prom))
    s = float(sizes[i]); ox, oy = best_phase[sizes[i]]
    # refine phase at quarter-pixel
    best = None
    for dx in np.arange(-0.5, 0.51, 0.25):
        for dy in np.arange(-0.5, 0.51, 0.25):
            sc = _fit(rgb, alpha, s, (ox + dx) % s, (oy + dy) % s)
            if best is None or sc < best[0]:
                best = (sc, (ox + dx) % s, (oy + dy) % s)
    return s, float(best[1]), float(best[2])


def snap(rgba: Image.Image, cell: float, ox: float, oy: float, min_cover: float = 0.5) -> Image.Image:
    a = np.array(rgba.convert("RGBA")).astype(float)
    alpha = a[..., 3] > 0
    rgb = a[..., :3]
    H, W = alpha.shape
    xs = ((np.arange(W) - ox) // cell).astype(int)
    ys = ((np.arange(H) - oy) // cell).astype(int)
    gw, gh = xs.max() + 1, ys.max() + 1
    out = np.zeros((gh, gw, 4), np.uint8)
    for gy in range(gh):
        rows = ys == gy
        for gx in range(gw):
            m = rows[:, None] & (xs == gx)[None, :]
            n_all = m.sum()
            if n_all == 0:
                continue
            n_a = (m & alpha).sum()
            if n_a / n_all < min_cover:
                continue
            out[gy, gx, :3] = np.median(rgb[m & alpha], axis=0)
            out[gy, gx, 3] = 255
    solid = out[..., 3] > 0
    yy, xx = np.where(solid)
    return Image.fromarray(out[yy.min():yy.max() + 1, xx.min():xx.max() + 1])


def quantize(rgba: Image.Image, colors: int = 24) -> Image.Image:
    arr = np.array(rgba.convert("RGBA"))
    rgb = Image.fromarray(arr[..., :3]).quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    out = np.dstack([np.array(rgb), arr[..., 3]])
    out[out[..., 3] == 0] = 0
    return Image.fromarray(out)


def clean(rgba: Image.Image, colors: int = 24, cell: float | None = None):
    """detect → snap → quantise. Returns (sprite_1x, (cell, ox, oy))."""
    if cell is None:
        cell, ox, oy = detect_grid(rgba)
    else:
        _, ox, oy = detect_grid(rgba, sizes=[cell])
    return quantize(snap(rgba, cell, ox, oy), colors), (cell, ox, oy)
