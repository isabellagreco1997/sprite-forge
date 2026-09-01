"""Whole-body motion for small sprites. The rule: never slide body parts past each other — a one-pixel seam on a
50-pixel character reads as a cut. Move the whole body, then add secondary motion only where it physically
happens (hair strands, a skirt hem, a cape tip, a blink), filling any vacated pixel from the row above.
"""
from __future__ import annotations
import math
import numpy as np
from .canvas import Sprite


def light_mask(sp: Sprite, lo: int = 165):
    return sp.where(lambda r, g, b: (r > lo) & (g > lo) & (b > lo))


def hue_mask(sp: Sprite, pred):
    return sp.where(pred)


def eyes_mask(sp: Sprite, x0, x1, y0, y1):
    """Iris + pupil pixels inside a box: anything bluish/purplish or very dark."""
    box = sp.box(x0, x1, y0, y1)
    return box & sp.where(lambda r, g, b: (b > r + 20) | ((r < 90) & (g < 90) & (b < 110)))


def blink(sp: Sprite, eyes: np.ndarray, lid_rows: int = 2, face_rgb=(241, 225, 206)) -> Sprite:
    """Lid comes down over the top `lid_rows` rows of the eye mask; the lash row stays. Subtle, never a wipe."""
    out = sp.copy()
    ys, xs = np.where(eyes)
    if len(ys) == 0:
        return out
    top = ys.min()
    for y, x in zip(ys, xs):
        if y < top + lid_rows:
            out.a[y, x, :3] = face_rgb
            out.a[y, x, 3] = 255
    return out


def lower_eyes(sp: Sprite, eyes: np.ndarray, face_rgb=(241, 225, 206)) -> Sprite:
    """Half-lidded look (top eye row only) — reads as shy / looking down."""
    return blink(sp, eyes, lid_rows=1, face_rgb=face_rgb)


def idle_loop(sp: Sprite, n: int = 12, mode: str = "float", amp: int = 2, hair: np.ndarray | None = None,
              hem: np.ndarray | None = None, eyes: np.ndarray | None = None, blink_at: int | None = None,
              feet_row: int | None = None, pad=(3, 4)) -> list[Sprite]:
    """
    mode='float': whole sprite rises/falls on a sine (airborne characters).
    mode='stand': feet planted; the upper body sinks `1` row for a third of the loop (rows above `feet_row`
                  shift down, a uniform shin row absorbs it).
    hair/hem: masks that lag one beat behind the body (max 1 px).
    """
    frames = []
    for i in range(n):
        ph = i / n * 2 * math.pi
        if mode == "float":
            body = round(-amp * math.sin(ph))
            lag = round(-amp * math.sin(ph - 0.9))
        else:
            body = 1 if math.sin(ph) < -0.3 else 0
            lag = 1 if math.sin(ph - 1.0) < -0.3 else 0
        d = int(np.clip(lag - body, -1, 1))
        f = sp
        if hair is not None:
            f = f.shift_region(hair, dy=d)
        if hem is not None:
            f = f.shift_region(hem, dy=d)
        if mode == "stand" and body:
            assert feet_row is not None, "stand mode needs feet_row (first row that must stay planted)"
            f = f.squash(feet_row, 1)
        if eyes is not None and blink_at is not None and i == blink_at:
            f = blink(f, eyes)
        f = f.offset(0, body if mode == "float" else 0, pad=pad)
        frames.append(f)
    return frames


def slip_factor(ground_px_per_s: float, stride_px: float, steps_per_cycle: int, cycle_s: float) -> float:
    """1.0 = feet planted. >1 = the character skates (moves further than the feet step). Fix the SPEED, not the art."""
    return ground_px_per_s / (steps_per_cycle * stride_px / cycle_s)


def ground_speed(stride_px: float, steps_per_cycle: int, cycle_s: float, scale: int = 1) -> float:
    """The only ground speed that doesn't slide, in screen px/s."""
    return scale * steps_per_cycle * stride_px / cycle_s
