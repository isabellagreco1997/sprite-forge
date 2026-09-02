"""Compose the README pipeline banner from the example outputs: one designed image, consistent sprite scale,
numbered panels, arrows. Run after make_poses.py:  python examples/girl/make_banner.py"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out")
BG, PANEL, LINE, FG, SUB, ACC = (17, 15, 24), (28, 25, 38), (48, 44, 62), (240, 238, 245), (160, 155, 175), (255, 92, 108)


def font(size, bold=False):
    for cand in (["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"] if bold
                 else ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]):
        try:
            return ImageFont.truetype(cand, size)
        except OSError:
            continue
    return ImageFont.load_default()


F_NUM, F_TITLE, F_SUB = font(30, True), font(26, True), font(18)
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
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=PANEL, outline=LINE, width=2)
    # image area
    ix, iy, iw, ih = x + 20, y + 20, w - 40, image_h
    im = image if image.width <= iw and image.height <= ih else fit(image, iw, ih)
    canvas.alpha_composite(im.convert("RGBA"), (ix + (iw - im.width) // 2, iy + (ih - im.height) // 2))
    # captions
    ty = iy + ih + 18
    d.text((x + 22, ty), f"{num}", font=F_NUM, fill=ACC)
    d.text((x + 22 + d.textlength(f"{num}", font=F_NUM) + 12, ty + 3), title, font=F_TITLE, fill=FG)
    ty += 44
    for line in wrap(d, sub, F_SUB, w - 44):
        d.text((x + 22, ty), line, font=F_SUB, fill=SUB); ty += 24


def arrow(canvas, x, y):
    d = ImageDraw.Draw(canvas)
    d.line([(x, y), (x + 26, y)], fill=SUB, width=4)
    d.polygon([(x + 26, y - 9), (x + 40, y), (x + 26, y + 9)], fill=SUB)


W, H = 1800, 1180
c = Image.new("RGBA", (W, H), BG + (255,))
src = Image.open(f"{OUT}/../screenshot.png").convert("RGBA")
jump = nearest(Image.open(f"{OUT}/girl_1x.png").convert("RGBA"), SCALE)
parts = Image.open(f"{OUT}/girl_parts_8x.png").convert("RGBA")
parts = nearest(parts.resize((parts.width // 8, parts.height // 8), Image.NEAREST), SCALE)
stand = nearest(Image.open(f"{OUT}/girl_stand_1x.png").convert("RGBA"), SCALE)
dump = Image.open(f"{OUT}/girl_dump.png").convert("RGBA")
sheet = nearest(Image.open(f"{OUT}/girl_walk_sheet.png").convert("RGBA"), 3)

# row 1: source → extracted → parts map → new pose
y1, h1, img_h = 30, 600, 420
panel(c, 30, y1, 640, h1, 1, "Source", "An AI-generated “pixel art” screenshot: JPEG noise, no real pixel grid, character mid-jump.", src, img_h)
arrow(c, 685, y1 + img_h // 2 + 20)
xs = [740, 1080, 1470]
panel(c, xs[0], y1, 290, h1, 2, "Extracted", "Cut out and snapped to her native 5.4 px grid: a clean 41×50 sprite, 24 colours.", jump, img_h)
arrow(c, 1035, y1 + img_h // 2 + 20)
panel(c, xs[1], y1, 340, h1, 3, "Parts map", "Horn, arms, legs, head, torso labelled by polygon, so the re-pose erases exactly the right pixels.", parts, img_h)
arrow(c, 1425, y1 + img_h // 2 + 20)
panel(c, xs[2], y1, 300, h1, 4, "New pose", "Standing idle in her own palette. Head, hair and dress untouched; legs in her three-quarter view.", stand, img_h)

# row 2: dump | spritesheet
y2, h2, img_h2 = 660, 490, 330
panel(c, 30, y2, 870, h2, 5, "Dump", "The sprite as a palette-indexed ASCII map. Every edit is planned here, row and column exact, never guessed.", dump, img_h2)
panel(c, 930, y2, 840, h2, 6, "Walk spritesheet", "Six frames drawn fresh: contact → recoil → pass for each leg. Hands clasped, eyes down, hair a frame behind. Ground speed derived from the stride, so no skating.", sheet, img_h2)

c.convert("RGB").save(f"{OUT}/pipeline.png", optimize=True)
print("banner", c.size, "→", f"{OUT}/pipeline.png")
