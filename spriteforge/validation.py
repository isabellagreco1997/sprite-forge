"""Measure frame integrity without inventing animation poses or repairing the art."""
from __future__ import annotations
import numpy as np
from scipy import ndimage
from .canvas import Sprite


def _rgba(frame):
    a = frame.a if isinstance(frame, Sprite) else np.asarray(frame)
    if a.ndim != 3 or a.shape[2] != 4:
        raise ValueError("Frames must be RGBA images, arrays, or Sprite objects")
    return a


def _colors(a):
    return {tuple(int(v) for v in p) for p in a[a[..., 3] > 0, :3]}


def frame_report(reference, frames, allowed_change=None):
    """Report detailed-art issues relative to a registered reference frame.

    allowed_change is a Boolean HxW mask including the *destination* extent of
    animated parts. A zero outside-mask count proves stationary parts are intact.
    Reports do not declare artistic quality or automatically erase small effects.
    """
    ref = _rgba(reference)
    h, w = ref.shape[:2]
    allowed = None if allowed_change is None else np.asarray(allowed_change, dtype=bool)
    if allowed is not None and allowed.shape != (h, w):
        raise ValueError("allowed_change must match the reference height and width")
    palette = _colors(ref)
    border = np.zeros((h, w), dtype=bool)
    border[[0, -1], :] = True
    border[:, [0, -1]] = True
    reports = []
    for index, frame in enumerate(frames):
        a = _rgba(frame)
        result = {"frame": index, "size_matches": a.shape == ref.shape}
        if not result["size_matches"]:
            result["size"] = [int(a.shape[1]), int(a.shape[0])]
            reports.append(result)
            continue
        # RGB differences in fully transparent pixels are not visible art changes.
        visible = (a[..., 3] > 0) | (ref[..., 3] > 0)
        changed = np.any(a != ref, axis=2) & visible
        ys, xs = np.where(changed)
        solid = a[..., 3] > 0
        labels, _ = ndimage.label(solid)
        sizes = np.bincount(labels.ravel())
        sizes[0] = 0
        isolated = solid & (sizes[labels] <= 2)
        result.update({
            "changed_pixels": int(changed.sum()),
            "changed_bbox": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else None,
            "outside_mask_pixels": int((changed & ~allowed).sum()) if allowed is not None else None,
            "new_colors": [list(c) for c in sorted(_colors(a) - palette)],
            "partial_alpha_pixels": int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum()),
            "new_border_pixels": int((solid & border & (ref[..., 3] == 0)).sum()),
            "isolated_pixels": [[int(x), int(y)] for y, x in np.argwhere(isolated)],
        })
        reports.append(result)
    return reports
