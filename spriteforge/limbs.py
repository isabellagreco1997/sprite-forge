"""A tiny DSL for drawing limbs in poses, so a walk cycle is *drawn* per frame instead of cut-and-flipped.

A Limb is a stack of row strings (palette symbols, '.' transparent) plus foot/hand variants. A Pose is a per-row
x offset list (so the limb can angle forward/back and bend) plus which rows to skip (a lifted foot shortens the
leg) and which foot variant to use. Draw the FAR limb first, the NEAR limb over it.

The default PROFILE_LEG is a three-quarter-view leg (character facing screen-right). Match the view angle of
the body you attach it to: a 3/4 torso needs overlapping profile legs, not two front-view legs side by side.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from .canvas import Sprite


@dataclass
class Limb:
    start_row: int                     # sprite row of the first limb row (the hip / shoulder)
    rows: dict[int, str]               # row -> string, keyed by absolute sprite row
    feet: dict[str, dict[int, str]]    # variant name -> {row: string}, rows are relative (0 = first foot row)
    palette: dict[str, tuple] = field(default_factory=dict)

    def draw(self, sp: Sprite, anchor_x: int, pose: "Pose"):
        """Paint the limb. The limb's own palette overrides the sprite's symbols while drawing, then is restored,
        so a limb definition is portable between sprites whose dump symbols differ."""
        saved = dict(sp.pal)
        sp.pal.update(self.palette)
        try:
            self._draw(sp, anchor_x, pose)
        finally:
            sp.pal = saved

    def _draw(self, sp: Sprite, anchor_x: int, pose: "Pose"):
        y = self.start_row
        keys = sorted(self.rows)
        for src_y in keys:
            if src_y in pose.skip:
                continue
            off = pose.off[src_y - self.start_row]
            sp.paint(y, anchor_x + off, self.rows[src_y])
            y += 1
        foot = self.feet[pose.foot]
        for j, r in enumerate(sorted(foot)):
            off = pose.off[min(len(pose.off) - 1, y + j - self.start_row)]
            sp.paint(y + j, anchor_x + off, foot[r])


@dataclass
class Pose:
    off: list[int]
    foot: str = "flat"
    skip: tuple = ()


# ---------- default: three-quarter profile leg, hip at column 0, light side (3) faces front (screen right)
LEG_PALETTE = {'0': (136, 17, 29), '1': (204, 38, 42), '5': (175, 23, 33), '2': (11, 3, 11), 'i': (11, 0, 7),
               'h': (50, 28, 54), '3': (254, 227, 199), 'd': (235, 167, 144), '4': (220, 141, 131),
               'k': (232, 187, 159), 'c': (169, 106, 115), '8': (253, 252, 232), 'l': (250, 241, 228),
               '9': (200, 188, 179), '7': (253, 253, 244), 'g': (189, 173, 173)}

PROFILE_LEG = Limb(
    start_row=37,
    rows={37: '2cdd42', 38: '2d3342', 39: '2d3342', 40: '2kdd42',           # thigh, knee
          41: '.2d342', 42: '.2d342', 43: '.2d342', 44: '.2d342',           # shin, ankle
          45: '.2l892', 46: '.27892'},                                      # sock, sock fold
    feet={'flat':   {0: '2h1152.', 1: '2h50052', 2: 'iiiiiii'},             # heel left, toe right
          'heelup': {0: '2h11...', 1: '.2h55..', 2: '..2005.', 3: '...iii.'},  # trailing foot, toe on the ground
          'lift':   {0: '2h115..', 1: '.2h505.', 2: '..2ii..'}},            # swinging foot, off the ground
    palette=LEG_PALETTE,
)

# per-row x offsets for the 13 leg rows (37..49). contact → recoil → pass, then the other leg.
WALK_POSES = {
    'STAND': Pose([0] * 13),
    'FWD':   Pose([0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]),
    'FWD2':  Pose([0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2]),
    'BACK':  Pose([0, 0, -1, -1, -2, -2, -3, -3, -3, -4, -4, -4, -4], foot='heelup', skip=(43,)),
    'BACK2': Pose([0, 0, 0, -1, -1, -1, -2, -2, -2, -3, -3, -3, -3], foot='heelup', skip=(43,)),
    'PASS':  Pose([0, 0, 0, 1, 1, 0, -1, -1, -1, -1, -1, -1, -1], foot='lift', skip=(42, 43)),
    'PLANT': Pose([0] * 9 + [1] * 4),
}

# (near pose, far pose, body sinks?, hair lags?)  — 6 frames, 3px stride
WALK_SEQUENCE = [('FWD', 'BACK', True, False), ('FWD2', 'BACK2', True, False), ('PLANT', 'PASS', False, True),
                 ('BACK', 'FWD', True, False), ('BACK2', 'FWD2', True, False), ('PASS', 'PLANT', False, True)]
WALK_STRIDE = 3


def walk_cycle(upper: Sprite, limb: Limb, far_x: int, near_x: int, poses=WALK_POSES, sequence=WALK_SEQUENCE,
               hair=None, sink_rows: int | None = None, pad=(3, 2)) -> list[Sprite]:
    """upper = the body with the legs erased. Legs are painted fresh per frame."""
    frames = []
    for near, far, bob, lag in sequence:
        f = upper.copy()
        limb.draw(f, far_x, poses[far])
        limb.draw(f, near_x, poses[near])
        if bob and sink_rows:
            f = f.squash(sink_rows, 1)
        if lag and hair is not None:
            f = f.shift_region(hair, dy=1)
        frames.append(f.offset(0, 0, pad=pad))
    return frames
