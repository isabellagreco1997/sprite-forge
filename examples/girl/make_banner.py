"""Compose the README pipeline banner from the example outputs: one designed image, consistent sprite scale,
numbered panels, arrows. Run after make_poses.py:  python examples/girl/make_banner.py"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out")
BG, PANEL, LINE, FG, SUB, ACC = (0, 0, 0), (0, 0, 0), (255, 255, 255), (255, 255, 255), (170, 170, 170), (255, 0, 0)   # undertale box


def font(size, bold=False):
    """monospace, like the game's text box. Menlo (index 1 = bold) → DejaVu Sans Mono → Consolas → default."""
    cands = [("/System/Library/Fonts/Menlo.ttc", 1 if bold else 0),
             ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 0),
             ("C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf", 0)]
    for path, idx in cands:
        try:
            return ImageFont.truetype(path, size, index=idx)
        except OSError:
            continue
    return ImageFont.load_default()


F_NUM, F_TITLE, F_SUB = font(26, True), font(26, True), font(17)
SCALE = 7                          # every sprite in the banner is drawn at the same scale


def nearest(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def fit(im, w, h):
    k = min(w / im.width, h / im.height)
    return im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)


def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur); cur = w_
    return lines + [cur]


def panel(canvas, x, y, w, h, num, title, sub, image, image_h):
    d = ImageDraw.Draw(canvas)
    d.rectangle([x, y, x + w, y + h], fill=PANEL, outline=LINE, width=5)
    # image area
    ix, iy, iw, ih = x + 20, y + 20, w - 40, image_h
    im = image if image.width <= iw and image.height <= ih else fit(image, iw, ih)
    canvas.alpha_composite(im.convert("RGBA"), (ix + (iw - im.width) // 2, iy + (ih - im.height) // 2))
    # captions
    ty = iy + ih + 18
    heart(canvas, x + 24, ty + 6)                                  # the soul, as the menu cursor
    d.text((x + 56, ty), f"{num}. {title.upper()}", font=F_TITLE, fill=FG)
    ty += 42
    for line in wrap(d, "* " + sub, F_SUB, w - 44):
        d.text((x + 24, ty), line, font=F_SUB, fill=SUB); ty += 23


def heart(canvas, x, y, k=3):
    """8-bit red soul, 7x6 pixels at scale k."""
    rows = ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"]
    d = ImageDraw.Draw(canvas)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == "1":
                d.rectangle([x + i * k, y + j * k, x + i * k + k - 1, y + j * k + k - 1], fill=ACC)


def arrow(canvas, x, y):
    d = ImageDraw.Draw(canvas)
    d.line([(x, y), (x + 26, y)], fill=SUB, width=4)
    d.polygon([(x + 26, y - 9), (x + 40, y), (x + 26, y + 9)], fill=SUB)


W, H = 1800, 1220
c = Image.new("RGBA", (W, H), BG + (255,))
src = Image.open(f"{OUT}/../screenshot.png").convert("RGBA")
jump = nearest(Image.open(f"{OUT}/girl_1x.png").convert("RGBA"), SCALE)
parts = Image.open(f"{OUT}/girl_parts_8x.png").convert("RGBA")
parts = nearest(parts.resize((parts.width // 8, parts.height // 8), Image.NEAREST), SCALE)
stand = nearest(Image.open(f"{OUT}/girl_stand_1x.png").convert("RGBA"), SCALE)
dump = Image.open(f"{OUT}/girl_dump.png").convert("RGBA")
sheet = nearest(Image.open(f"{OUT}/girl_walk_sheet.png").convert("RGBA"), 3)

# row 1: source → extracted → parts map → new pose
y1, h1, img_h = 30, 640, 420
panel(c, 30, y1, 640, h1, 1, "Source", "an ai-generated “pixel art” screenshot. jpeg noise, no real pixel grid, girl mid-jump.", src, img_h)
arrow(c, 685, y1 + img_h // 2 + 20)
xs = [740, 1080, 1470]
panel(c, xs[0], y1, 290, h1, 2, "Extracted", "cut out and snapped to her real 5.4 px grid. a clean 41×50 sprite, 24 colours.", jump, img_h)
arrow(c, 1035, y1 + img_h // 2 + 20)
panel(c, xs[1], y1, 340, h1, 3, "Parts map", "horn, arms, legs, head, torso. so the re-pose erases exactly the right pixels.", parts, img_h)
arrow(c, 1425, y1 + img_h // 2 + 20)
panel(c, xs[2], y1, 300, h1, 4, "New pose", "standing, in her own palette. head, hair and dress untouched. legs in her 3/4 view.", stand, img_h)

# row 2: dump | spritesheet
y2, h2, img_h2 = 700, 490, 330
panel(c, 30, y2, 870, h2, 5, "Dump", "the sprite as an ascii map, one char per pixel. every edit is planned here. no guessing.", dump, img_h2)
panel(c, 930, y2, 840, h2, 6, "Walk spritesheet", "six frames drawn fresh: contact → recoil → pass, each leg. hands clasped, eyes down, hair a frame late. speed comes from the stride, so no skating.", sheet, img_h2)

c.convert("RGB").save(f"{OUT}/pipeline.png", optimize=True)
print("banner", c.size, "→", f"{OUT}/pipeline.png")
