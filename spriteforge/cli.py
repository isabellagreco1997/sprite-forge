"""spriteforge CLI

  spriteforge extract  screenshot.png out.png [--region x0 y0 x1 y1] [--thresh 20]
  spriteforge snap     cut.png sprite_1x.png [--colors 24] [--cell 5.4]
  spriteforge dump     sprite_1x.png                       # palette-indexed ASCII map
  spriteforge scale    sprite_1x.png out.png --k 8
  spriteforge gif      frames_dir out.gif [--ms 110] [--scale 8]
  spriteforge sheet    frames_dir out.png [--scale 1]
"""
from __future__ import annotations
import argparse
import glob
import os
from PIL import Image
from .extract import extract as _extract
from . import gridsnap, export
from .canvas import Sprite


def main(argv=None):
    p = argparse.ArgumentParser(prog="spriteforge")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("extract"); a.add_argument("image"); a.add_argument("out")
    a.add_argument("--region", nargs=4, type=int); a.add_argument("--thresh", type=float, default=20)
    a.add_argument("--bg", nargs=3, type=int)

    s = sub.add_parser("snap"); s.add_argument("cut"); s.add_argument("out")
    s.add_argument("--colors", type=int, default=24); s.add_argument("--cell", type=float)

    d = sub.add_parser("dump"); d.add_argument("sprite")

    sc = sub.add_parser("scale"); sc.add_argument("sprite"); sc.add_argument("out"); sc.add_argument("--k", type=int, default=8)

    g = sub.add_parser("gif"); g.add_argument("frames_dir"); g.add_argument("out")
    g.add_argument("--ms", type=int, default=110); g.add_argument("--scale", type=int, default=8)

    sh = sub.add_parser("sheet"); sh.add_argument("frames_dir"); sh.add_argument("out"); sh.add_argument("--scale", type=int, default=1)

    args = p.parse_args(argv)
    if args.cmd == "extract":
        cut = _extract(args.image, tuple(args.region) if args.region else None, bg=args.bg, thresh=args.thresh)
        cut.save(args.out)
        print(f"saved {args.out} {cut.size} origin={cut.info.get('origin')}")
    elif args.cmd == "snap":
        sp, grid = gridsnap.clean(Image.open(args.cut), colors=args.colors, cell=args.cell)
        sp.save(args.out)
        print(f"saved {args.out} {sp.size} grid cell={grid[0]:.2f} offset=({grid[1]:.1f},{grid[2]:.1f})")
    elif args.cmd == "dump":
        print(Sprite.load(args.sprite).dump())
    elif args.cmd == "scale":
        Sprite.load(args.sprite).save(args.out, scale=args.k)
    elif args.cmd in ("gif", "sheet"):
        frames = [Image.open(f).convert("RGBA") for f in sorted(glob.glob(os.path.join(args.frames_dir, "*.png")))]
        if args.cmd == "gif":
            export.gif(frames, args.out, ms=args.ms, scale=args.scale)
        else:
            export.spritesheet(frames, args.out, scale=args.scale)
        print(f"saved {args.out} ({len(frames)} frames)")


if __name__ == "__main__":
    main()
