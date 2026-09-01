"""Composite animated sprites back onto a scene and render an mp4 (needs ffmpeg on PATH).

Two rules baked in:
  * ground speed is derived from the stride — the character never skates
  * the sprite's sole row is placed ON the floor line you give; measure that line in the source image
"""
from __future__ import annotations
import os
import subprocess
from PIL import Image
from .canvas import Sprite
from .motion import ground_speed


def _img(f):
    return f.image() if isinstance(f, Sprite) else f


def _up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def render_walk(background: Image.Image, idle_frames, walk_frames, *, feet_row: int, floor_y: int, x0: int, x1: int,
                scale: int = 8, walk_fps: float = 9, stride_px: int = 3, idle_fps: float = 9, lead_in: float = 2.0,
                tail: float = 2.0, fps: int = 30, out_dir: str = "frames") -> int:
    """idle at x0, walk to x1 at slip-free speed, idle. Writes JPEG frames; returns frame count."""
    os.makedirs(out_dir, exist_ok=True)
    idle = [_up(_img(f), scale) for f in idle_frames]
    walk = [_up(_img(f), scale) for f in walk_frames]
    feet = feet_row * scale
    cycle_s = len(walk) / walk_fps
    speed = ground_speed(stride_px, 2, cycle_s, scale)
    walk_s = (x1 - x0) / speed
    total = lead_in + walk_s + tail
    n = int(total * fps)
    for i in range(n):
        t = i / fps
        if t < lead_in:
            spr, x = idle[int(t * idle_fps) % len(idle)], x0
        elif t < lead_in + walk_s:
            spr, x = walk[int((t - lead_in) * walk_fps) % len(walk)], x0 + (t - lead_in) * speed
        else:
            spr, x = idle[int(t * idle_fps) % len(idle)], x1
        im = background.copy()
        im.paste(spr, (int(x), floor_y - feet), spr)
        im.save(f"{out_dir}/f{i:05d}.jpg", quality=93)
    return n


def render_idle(background: Image.Image, idle_frames, *, feet_row: int, floor_y: int, x: int, scale: int = 8,
                idle_fps: float = 9, seconds: float = 6.0, fps: int = 30, out_dir: str = "frames") -> int:
    os.makedirs(out_dir, exist_ok=True)
    idle = [_up(_img(f), scale) for f in idle_frames]
    n = int(seconds * fps)
    for i in range(n):
        spr = idle[int(i / fps * idle_fps) % len(idle)]
        im = background.copy()
        im.paste(spr, (x, floor_y - feet_row * scale), spr)
        im.save(f"{out_dir}/f{i:05d}.jpg", quality=93)
    return n


def to_mp4(frames_dir: str, out: str, fps: int = 30):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(fps), "-i", f"{frames_dir}/f%05d.jpg",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
                    "-movflags", "+faststart", out], check=True)
    return out
