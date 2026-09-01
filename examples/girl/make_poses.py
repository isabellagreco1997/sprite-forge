"""Worked example: from a screenshot to a clean sprite, a new standing pose, an idle loop, a shy walk cycle,
and a clip of her back inside her own game screen.

Run from the repo root:  python examples/girl/make_poses.py
Outputs go to examples/girl/out/
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from PIL import Image
import numpy as np
from spriteforge import (Sprite, extract, paint_out, clean, idle_loop, eyes_mask, lower_eyes, light_mask,
                         PROFILE_LEG, PROFILE_LEG_FAR, WALK_POSES, walk_cycle, export, showcase)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
SHOT = os.path.join(HERE, "screenshot.png")

# ---------- 1. cut her out and snap to the native grid (the source is AI "pixel-look", no real grid)
cut = extract(SHOT, region=(530, 185, 790, 470), thresh=20)      # region wide enough that the horn isn't on the edge
origin = cut.info["origin"]
sprite_img, grid = clean(cut, colors=24)
sprite_img.save(f"{OUT}/girl_1x.png")
print("grid", grid, "sprite", sprite_img.size)
jump = Sprite.load(f"{OUT}/girl_1x.png")
open(f"{OUT}/girl_dump.txt", "w").write(jump.dump())   # read this before editing anything

# ---------- 2. new pose: standing. keep head/hair/horn/dress; erase arms + legs by exact ranges from the dump
# colours we paint with are registered by RGB (dump symbols are per-sprite and change if the grid phase moves)
ARM = {'O': (11, 3, 11), 'S': (254, 227, 199), 'D': (235, 167, 144), 'A': (220, 141, 131),
       'G': (204, 38, 42), 'H': (175, 23, 33), 'K': (136, 17, 29), 'B': (48, 5, 16)}
st = jump.copy(); st.add_colours(ARM)
for y, (x0, x1) in {18: (30, 33), 19: (30, 34), 20: (29, 35), 21: (28, 34), 22: (27, 34), 23: (26, 33),
                    25: (23, 28), 26: (24, 27)}.items():
    st.erase(y, x0, x1)                                            # raised arm
st.erase(24, 24, 27); st.erase(24, 30, 30)
st.erase(24, 9, 12); st.erase(25, 1, 11); st.erase(26, 0, 11); st.erase(27, 1, 7); st.erase(28, 4, 7); st.erase(29, 6, 6)  # back arm
st.erase(33, 24, 26)
for y in (34, 35, 36): st.erase(y, 22, 31)                        # front thigh
for y in range(32, 37): st.erase(y, 8, 9)                          # stray hair-shadow dots
st.erase_rows(37, 49)                                              # both legs

# hanging arms: O outline, S/D/A skin, G/H/K glove reds, B cuff (registered above by RGB)
for y, (x0, s) in {25: (11, 'ODD'), 26: (11, 'OSDO'), 27: (11, 'OSDO'), 28: (11, 'OSDO'), 29: (11, 'OSDO'), 30: (11, 'ODDO'),
                   31: (11, 'ODDO'), 32: (11, 'BBBB'), 33: (11, 'OGGO'), 34: (11, 'OGHO'), 35: (11, 'OKHO'), 36: (11, '.OO.'),
                   }.items():
    st.paint(y, x0, s)
for y, (x0, s) in {26: (22, 'DDO'), 27: (22, 'ODAO'), 28: (22, 'ODAO'), 29: (22, 'ODAO'), 30: (22, 'ODAO'), 31: (22, 'ODDO'),
                   32: (22, 'BBBB'), 33: (22, 'OGGO'), 34: (22, 'OGHO'), 35: (22, 'OKHO'), 36: (22, '.OO.')}.items():
    st.paint(y, x0, s)
# legs: three-quarter view like her torso. She faces right, so her LEFT leg is nearest the camera: it goes on
# screen-left (hip 14), drawn last and full size. The right leg is behind on screen-right (hip 17), narrower.
PROFILE_LEG_FAR.draw(st, 17, WALK_POSES['STAND']); PROFILE_LEG.draw(st, 14, WALK_POSES['STAND'])
st.save(f"{OUT}/girl_stand_1x.png"); st.save(f"{OUT}/girl_stand_8x.png", scale=8)

# ---------- 3. idle loops (whole body; hair + hem lag; blink). masks by colour + region, never by cutting parts
def masks(sp):
    hair = light_mask(sp) & sp.box(0, 12, 16, 25)                                    # trailing strands
    red = sp.where(lambda r, g, b: (r > 140) & (g < 100) & (b < 100))
    hem = (red | light_mask(sp)) & sp.box(9, 21, 35, 36)
    eyes = eyes_mask(sp, 18, 27, 12, 15)
    return hair, hem, eyes
hair, hem, eyes = masks(jump)
float_frames = idle_loop(jump, n=12, mode="float", amp=2, hair=hair, hem=hem, eyes=eyes, blink_at=8)
hair, hem, eyes = masks(st)
stand_frames = idle_loop(st, n=16, mode="stand", hair=hair, hem=hem, eyes=eyes, blink_at=11, feet_row=44)
export.gif(float_frames, f"{OUT}/girl_float.gif", ms=90); export.spritesheet(float_frames, f"{OUT}/girl_float_sheet.png")
export.gif(stand_frames, f"{OUT}/girl_stand_idle.gif", ms=110); export.spritesheet(stand_frames, f"{OUT}/girl_stand_idle_sheet.png")

# ---------- 4. shy walk: hands clasped in front, eyes lowered, legs drawn fresh per frame (3px stride)
upper = st.copy(); upper.add_colours(ARM); upper.erase_rows(37, 49)
upper.erase_rect(25, 36, 11, 14); upper.erase_rect(26, 36, 22, 25)          # take the hanging arms off
upper.restore_from(jump, 30, 36, 11, 14); upper.restore_from(jump, 30, 33, 22, 23)   # skirt under them = source pixels
for y, (x0, s) in {26: (22, 'DDO'), 27: (21, 'ODAO'), 28: (21, 'ODAO'), 29: (20, 'ODAO'), 30: (20, 'ODAO'), 31: (19, 'ODDO'),
                   32: (18, 'BBBB'), 33: (18, 'OGGO'), 34: (18, 'OGHO'), 35: (18, 'OKHO'), 36: (18, '.OO.')}.items():
    upper.paint(y, x0, s)
for y, (x0, s) in {25: (11, 'ODD'), 26: (11, 'OSDO'), 27: (12, 'OSDO'), 28: (12, 'OSDO'), 29: (13, 'OSDO'), 30: (13, 'ODDO'),
                   31: (14, 'ODDO'), 32: (14, 'BBBB'), 33: (14, 'OGGO'), 34: (14, 'OGHO'), 35: (14, 'OKHO'), 36: (14, '.OO.')}.items():
    upper.paint(y, x0, s)
upper = lower_eyes(upper, eyes_mask(upper, 18, 27, 12, 15))
walk_frames = walk_cycle(upper, PROFILE_LEG, far_x=17, near_x=14, hair=light_mask(upper) & upper.box(0, 12, 16, 26), sink_rows=37)
export.gif(walk_frames, f"{OUT}/girl_walk.gif", ms=111); export.spritesheet(walk_frames, f"{OUT}/girl_walk_sheet.png")
export.gif(walk_frames, f"{OUT}/girl_walk_clear.gif", ms=111, bg=None)          # true colours, transparent background
export.gif(stand_frames, f"{OUT}/girl_stand_idle_clear.gif", ms=110, bg=None)

# ---------- 5. back into her own screen: paint her out, then idle → walk → idle along the floor, no skating
bg = paint_out(SHOT, cut, origin, bg=(23, 10, 30)).resize((1920, 1080), Image.LANCZOS)
frames_dir = f"{OUT}/frames"
n = showcase.render_walk(bg, stand_frames, walk_frames, feet_row=50 + 2, floor_y=int(556 * 1.5), x0=560, x1=1180,
                         scale=8, walk_fps=9, stride_px=3, out_dir=frames_dir)
try:
    showcase.to_mp4(frames_dir, f"{OUT}/girl_walking.mp4"); print("mp4 written")
except Exception as e:
    print("ffmpeg not available, frames left in", frames_dir, e)
print("done →", OUT)
