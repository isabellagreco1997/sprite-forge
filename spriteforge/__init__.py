"""sprite-forge: turn any pixel-art image into clean sprites, new poses and animations."""
from .canvas import Sprite
from .extract import extract, paint_out
from .gridsnap import detect_grid, snap, quantize, clean
from .motion import idle_loop, blink, lower_eyes, eyes_mask, light_mask, slip_factor, ground_speed
from .limbs import Limb, Pose, PROFILE_LEG, PROFILE_LEG_FAR, WALK_POSES, WALK_SEQUENCE, WALK_STRIDE, walk_cycle
from . import export, showcase, parts

__all__ = ["Sprite", "extract", "paint_out", "detect_grid", "snap", "quantize", "clean", "idle_loop", "blink",
           "lower_eyes", "eyes_mask", "light_mask", "slip_factor", "ground_speed", "Limb", "Pose", "PROFILE_LEG", "PROFILE_LEG_FAR",
           "WALK_POSES", "WALK_SEQUENCE", "WALK_STRIDE", "walk_cycle", "export", "showcase", "parts"]
