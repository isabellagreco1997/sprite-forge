"""Pixel knight: procedurally painted 32x40 sprite with idle + walk cycles.
Outputs: spritesheet (1x, 8x), idle.gif, walk.gif, per-frame PNGs for the showcase."""
from PIL import Image, ImageDraw
import os, math

W, H = 32, 40
P = {  # palette
    'K': (18, 18, 28),      # outline
    'S': (143, 155, 179),   # steel
    's': (91, 100, 120),    # steel dark
    'H': (216, 223, 239),   # steel highlight
    'R': (200, 40, 60),     # red cloth / plume
    'r': (138, 24, 38),     # red dark
    'G': (224, 176, 64),    # gold
    'g': (154, 116, 32),    # gold dark
    'B': (107, 74, 42),     # leather
    'V': (10, 10, 16),      # visor black
    'E': (255, 70, 70),     # eye glow
    'e': (170, 30, 40),     # eye glow dim
    'W': (245, 245, 250),   # glint
}

class Canvas:
    def __init__(self):
        self.px = {}
    def put(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.px[(x, y)] = c
    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)
    def outline(self):
        filled = set(self.px)
        for (x, y) in list(filled):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n not in filled and 0 <= n[0] < W and 0 <= n[1] < H:
                    self.px[n] = 'K'
    def image(self):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        for (x, y), c in self.px.items():
            im.putpixel((x, y), P[c] + (255,))
        return im

def draw_knight(bob=0, plume=0, legL=(0, 0), legR=(0, 0), armR=0, glint=None, eye='E', shield_dy=0):
    """bob: whole body y offset. plume: sway (-1..1). legL/legR: (dx, dy) foot offsets.
    armR: sword arm y offset. glint: y of blade glint pixel or None."""
    c = Canvas()
    b = bob
    # ---- legs (drawn first, behind torso)
    for (lx, (dx, dy)) in ((12, legL), (17, legR)):
        c.rect(lx + dx, 27 + b, lx + 2 + dx, 34 + b - max(0, -dy), 'S')   # upper/lower leg
        c.rect(lx + dx, 30 + b, lx + 2 + dx, 30 + b, 's')                   # knee joint
        c.rect(lx - 1 + dx, 35 + b + dy, lx + 3 + dx, 36 + b + dy, 's')   # boot
        c.put(lx + 3 + dx, 36 + b + dy, 'K')
    # ---- torso
    c.rect(12, 15 + b, 19, 25 + b, 'S')
    c.rect(12, 15 + b, 12, 25 + b, 'H')          # chest highlight column
    c.rect(19, 15 + b, 19, 25 + b, 's')
    # tabard: red with gold cross
    c.rect(14, 17 + b, 17, 24 + b, 'R')
    c.rect(14, 24 + b, 17, 24 + b, 'r')
    c.rect(15, 18 + b, 16, 23 + b, 'G')
    c.rect(14, 20 + b, 17, 20 + b, 'G')
    # belt
    c.rect(12, 25 + b, 19, 26 + b, 'B')
    c.rect(15, 25 + b, 16, 26 + b, 'G')
    # gorget / neck
    c.rect(13, 14 + b, 18, 14 + b, 's')
    # ---- pauldrons
    for x0 in (8, 20):
        c.rect(x0, 15 + b, x0 + 3, 18 + b, 'S')
        c.rect(x0, 15 + b, x0 + 3, 15 + b, 'G')
        c.put(x0 + (0 if x0 == 8 else 3), 18 + b, 's')
    # ---- left arm + shield
    c.rect(9, 19 + b, 11, 23 + b, 's')
    sd = shield_dy
    # heater shield rows: (y, x0, x1)
    shield_rows = [(18, 4, 10), (19, 4, 10), (20, 4, 10), (21, 4, 10), (22, 4, 10), (23, 4, 10), (24, 5, 9), (25, 5, 9), (26, 6, 8), (27, 7, 7)]
    for (y, x0, x1) in shield_rows:
        c.rect(x0, y + b + sd, x1, y + b + sd, 'S')
    for (y, x0, x1) in shield_rows:                  # gold rim
        c.put(x0, y + b + sd, 'G'); c.put(x1, y + b + sd, 'G')
    c.rect(4, 18 + b + sd, 10, 18 + b + sd, 'G')
    c.rect(6, 20 + b + sd, 8, 24 + b + sd, 'R')      # emblem
    c.rect(7, 19 + b + sd, 7, 25 + b + sd, 'R')
    c.put(7, 21 + b + sd, 'G')
    # ---- right arm + sword
    a = armR
    c.rect(20, 19 + b + a, 22, 23 + b + a, 's')
    c.rect(21, 23 + b + a, 23, 24 + b + a, 'B')      # gauntlet grip
    # sword (blade held vertical, up)
    c.rect(22, 4 + b + a, 23, 21 + b + a, 'S')
    c.rect(22, 4 + b + a, 22, 21 + b + a, 'H')       # edge highlight
    c.put(22, 3 + b + a, 'H'); c.put(23, 3 + b + a, 'S')   # tip
    c.rect(20, 22 + b + a, 25, 22 + b + a, 'G')      # crossguard
    c.put(20, 22 + b + a, 'g'); c.put(25, 22 + b + a, 'g')
    c.rect(22, 25 + b + a, 23, 26 + b + a, 'B')      # grip below hand
    c.rect(22, 27 + b + a, 23, 27 + b + a, 'G')      # pommel
    if glint is not None:
        c.put(22, glint + b + a, 'W'); c.put(23, glint + b + a, 'W')
    # ---- helmet
    c.rect(11, 5 + b, 20, 13 + b, 'S')
    c.rect(12, 4 + b, 19, 4 + b, 'S')
    c.rect(13, 3 + b, 18, 3 + b, 'S')
    c.rect(12, 5 + b, 13, 6 + b, 'H'); c.put(14, 4 + b, 'H')   # highlight
    c.rect(19, 5 + b, 20, 13 + b, 's')
    c.rect(11, 12 + b, 20, 13 + b, 's')
    c.rect(12, 9 + b, 19, 10 + b, 'V')                # visor slit
    c.rect(11, 9 + b, 11, 10 + b, 's'); c.rect(20, 9 + b, 20, 10 + b, 's')
    c.rect(15, 11 + b, 16, 13 + b, 's')               # ventail line
    c.put(14, 9 + b, eye); c.put(17, 9 + b, eye)      # eyes
    # ---- plume (sways)
    base = [(16, 2), (17, 2), (16, 1), (17, 1), (15, 0), (16, 0)]
    for i, (x, y) in enumerate(base):
        sway = plume if i >= 2 else 0
        sway2 = plume * 2 if i >= 4 else sway
        c.put(x + (sway2 if i >= 4 else sway), y + b, 'R' if i % 2 == 0 else 'r')
    c.put(15 + plume * 2, 0 + b, 'r')
    c.outline()
    return c.image()

# ---------- animation frames
IDLE = [
    dict(bob=0, plume=0,  glint=None, eye='E'),
    dict(bob=0, plume=1,  glint=6,    eye='E'),
    dict(bob=1, plume=1,  glint=12,   eye='e', armR=1, shield_dy=1),
    dict(bob=1, plume=0,  glint=18,   eye='E', armR=1, shield_dy=1),
    dict(bob=0, plume=-1, glint=None, eye='E'),
    dict(bob=0, plume=-1, glint=None, eye='E'),
]
WALK = [  # contact, lift, pass, lift (mirrored)
    dict(bob=0, plume=0,  legL=(-1, 0),  legR=(1, 0)),
    dict(bob=1, plume=1,  legL=(0, -1),  legR=(1, 0),  armR=1, shield_dy=1),
    dict(bob=1, plume=1,  legL=(1, 0),   legR=(0, 0),  armR=1, shield_dy=1),
    dict(bob=0, plume=0,  legL=(1, 0),   legR=(-1, 0)),
    dict(bob=1, plume=-1, legL=(1, 0),   legR=(0, -1), armR=1, shield_dy=1),
    dict(bob=1, plume=-1, legL=(0, 0),   legR=(-1, 0), armR=1, shield_dy=1),
]

def up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)

def main(out):
    os.makedirs(out, exist_ok=True)
    idle = [draw_knight(**f) for f in IDLE]
    walk = [draw_knight(**f) for f in WALK]
    # spritesheet 1x and 8x
    sheet = Image.new('RGBA', (W * max(len(idle), len(walk)), H * 2), (0, 0, 0, 0))
    for i, im in enumerate(idle): sheet.paste(im, (i * W, 0))
    for i, im in enumerate(walk): sheet.paste(im, (i * W, H))
    sheet.save(f'{out}/knight_spritesheet_1x.png')
    up(sheet, 8).save(f'{out}/knight_spritesheet_8x.png')
    up(idle[0], 16).save(f'{out}/knight_still_16x.png')
    # gifs on transparent → gif needs a bg; use dark bg
    def gif(frames, name, ms):
        bg = (20, 18, 26)
        fr = []
        for im in frames:
            big = up(im, 12)
            base = Image.new('RGBA', big.size, bg + (255,))
            base.alpha_composite(big)
            fr.append(base.convert('P', palette=Image.ADAPTIVE, colors=32))
        fr[0].save(f'{out}/{name}', save_all=True, append_images=fr[1:], duration=ms, loop=0, disposal=2)
    gif(idle, 'knight_idle.gif', 140)
    gif(walk, 'knight_walk.gif', 110)
    # frame pngs for showcase
    os.makedirs(f'{out}/frames', exist_ok=True)
    for i, im in enumerate(idle): im.save(f'{out}/frames/idle_{i}.png')
    for i, im in enumerate(walk): im.save(f'{out}/frames/walk_{i}.png')
    print('idle', len(idle), 'walk', len(walk))

if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out'))
