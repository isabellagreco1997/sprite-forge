"""Sprite: a tiny RGBA pixel canvas with the editing primitives that make hand-pixel work precise.

The workflow this enables:
    1. `sprite.dump()` prints the sprite as a palette-indexed ASCII map (one char per pixel).
    2. You read the map, decide exact rows/columns to change.
    3. `sprite.erase(...)` / `sprite.paint(y, x, "2d342")` using the SAME symbols the dump printed.
Nothing is guessed: every pixel you write is a colour the sprite already has (or one you add by name).
"""
from __future__ import annotations
from collections import Counter
from PIL import Image
import numpy as np

SYMBOLS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


class Sprite:
    def __init__(self, arr: np.ndarray, palette: dict[str, tuple] | None = None):
        assert arr.ndim == 3 and arr.shape[2] == 4, "Sprite needs an RGBA array"
        self.a = arr.astype(np.uint8).copy()
        self.pal: dict[str, tuple] = dict(palette) if palette else {}
        if not self.pal:
            self.rebuild_palette()

    # ---------- io
    @classmethod
    def load(cls, path: str) -> "Sprite":
        return cls(np.array(Image.open(path).convert("RGBA")))

    def save(self, path: str, scale: int = 1):
        im = self.image()
        if scale > 1:
            im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        im.save(path)

    def image(self) -> Image.Image:
        return Image.fromarray(self.a)

    def copy(self) -> "Sprite":
        return Sprite(self.a.copy(), self.pal)

    @property
    def size(self):
        return self.a.shape[1], self.a.shape[0]

    # ---------- palette / dump
    def rebuild_palette(self):
        """Symbols are assigned by frequency: '0' is the most common colour."""
        H, W = self.a.shape[:2]
        cnt = Counter(tuple(int(v) for v in self.a[y, x, :3]) for y in range(H) for x in range(W) if self.a[y, x, 3])
        self.pal = {SYMBOLS[i]: c for i, (c, _) in enumerate(cnt.most_common()) if i < len(SYMBOLS)}
        return self.pal

    def symbol_of(self, rgb) -> str:
        rgb = tuple(int(v) for v in rgb)
        for k, v in self.pal.items():
            if tuple(v) == rgb:
                return k
        return "?"

    def add_colour(self, symbol: str, rgb: tuple):
        """Register a named colour. Dump symbols are assigned per sprite by frequency, so scripts that must be
        re-runnable should paint with colours they register themselves (uppercase letters are never auto-assigned
        before 36 colours are in use, so they are safe names)."""
        self.pal[symbol] = tuple(int(v) for v in rgb)

    def add_colours(self, mapping: dict):
        for k, v in mapping.items():
            self.add_colour(k, v)

    def dump(self, with_palette: bool = True) -> str:
        H, W = self.a.shape[:2]
        lines = []
        if with_palette:
            cnt = Counter(tuple(int(v) for v in self.a[y, x, :3]) for y in range(H) for x in range(W) if self.a[y, x, 3])
            for k, v in self.pal.items():
                lines.append(f"{k} {v}  x{cnt.get(tuple(v), 0)}")
            lines.append("")
        lines.append("    " + "".join(str(x % 10) for x in range(W)))
        for y in range(H):
            row = "".join(self.symbol_of(self.a[y, x, :3]) if self.a[y, x, 3] else "." for x in range(W))
            lines.append(f"{y:3d} {row}")
        return "\n".join(lines)

    # ---------- editing
    def erase(self, y: int, x0: int, x1: int):
        """Clear pixels on row y from x0..x1 inclusive."""
        self.a[y, max(0, x0):x1 + 1] = 0

    def erase_rect(self, y0: int, y1: int, x0: int, x1: int):
        self.a[y0:y1 + 1, x0:x1 + 1] = 0

    def erase_rows(self, y0: int, y1: int):
        self.a[y0:y1 + 1, :] = 0

    def paint(self, y: int, x0: int, s: str):
        """Write a row string starting at x0. '.' = leave untouched, ' ' = clear, any other char = palette symbol."""
        H, W = self.a.shape[:2]
        for i, ch in enumerate(s):
            x = x0 + i
            if ch == "." or not (0 <= x < W and 0 <= y < H):
                continue
            if ch == " ":
                self.a[y, x] = 0
                continue
            if ch not in self.pal:
                raise KeyError(f"'{ch}' is not in the palette; add it with add_colour()")
            self.a[y, x, :3] = self.pal[ch]
            self.a[y, x, 3] = 255

    def restore_from(self, source: "Sprite", y0: int, y1: int, x0: int, x1: int):
        """Copy a rectangle back from another sprite (e.g. the untouched original). Use this instead of guessing
        what was underneath a limb you removed."""
        self.a[y0:y1 + 1, x0:x1 + 1] = source.a[y0:y1 + 1, x0:x1 + 1]

    # ---------- masks
    def solid(self) -> np.ndarray:
        return self.a[..., 3] > 0

    def where(self, pred) -> np.ndarray:
        """Boolean mask from a predicate on (r, g, b) int arrays, restricted to solid pixels."""
        r, g, b = (self.a[..., i].astype(int) for i in range(3))
        return self.solid() & pred(r, g, b)

    def box(self, x0: int, x1: int, y0: int, y1: int) -> np.ndarray:
        H, W = self.a.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]
        return (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)

    # ---------- whole-body / secondary motion helpers (no seams)
    def shift_region(self, mask: np.ndarray, dy: int = 0, dx: int = 0, fill: bool = True) -> "Sprite":
        """Move the masked pixels by (dx, dy). When moving down, pixels vacated at the top are filled from the
        row above (a stretch) so no hole opens. Returns a new Sprite."""
        out = self.copy()
        if dx == 0 and dy == 0:
            return out
        H, W = self.a.shape[:2]
        ys, xs = np.where(mask)
        out.a[ys, xs] = 0
        for y, x in zip(ys, xs):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W:
                out.a[ny, nx] = self.a[y, x]
        if fill and dy > 0:
            for y, x in zip(ys, xs):
                if out.a[y, x, 3] == 0 and y > 0 and out.a[y - 1, x, 3] > 0:
                    out.a[y, x] = out.a[y - 1, x]
        return out

    def squash(self, rows_end: int, down: int = 1) -> "Sprite":
        """Sink rows [0, rows_end) by `down` pixels onto what's below (e.g. a body sinking onto planted feet).
        The rows just below rows_end are overwritten; pick rows_end where the columns are uniform (a shin)."""
        out = self.copy()
        out.a[down:rows_end + down] = self.a[0:rows_end]
        out.a[0:down] = 0
        return out

    def offset(self, dx: int, dy: int, pad: tuple[int, int] = (0, 0)) -> "Sprite":
        """Whole-sprite translation onto a padded canvas (pad = (x, y) each side)."""
        H, W = self.a.shape[:2]
        px, py = pad
        c = np.zeros((H + 2 * py, W + 2 * px, 4), np.uint8)
        y0, x0 = py + dy, px + dx
        c[y0:y0 + H, x0:x0 + W] = self.a
        return Sprite(c, self.pal)
