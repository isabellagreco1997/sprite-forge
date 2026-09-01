---
name: sprite-forge
description: Turn any pixel-art image (real or AI-generated) into clean game sprites, new poses and animations (idle, walk) that keep the character consistent. Use when asked to extract a character from a screenshot, make a sprite, re-pose a sprite, animate a pixel character, build a walk/idle cycle, or put an animated sprite back into its scene.
---

# sprite-forge — playbook

Tools live in `spriteforge/` (Python: Pillow, numpy, scipy; ffmpeg for mp4). Read this whole file before touching pixels. Every rule below was paid for with a wrong render.

## 0. Order of checks (do them in THIS order)

1. **View angle** — is the body front-on, 3/4, or profile? Every part you draw must match. A 3/4 torso gets overlapping profile legs (far leg behind, near leg in front), never two front-view legs side by side.
   **Depth:** the leg on the camera side is the near one. Facing screen-right she shows her left side, so her *left* leg is near: it sits on screen-left, is drawn last and full size, and its boot overlaps the far leg. The far leg is one column narrower, without highlight, partly hidden. Get this backwards and the character looks like she's standing on the wrong leg.
2. **Silhouette** — measure the original's contour row by row (widths and offsets) before redrawing a part. A leg is thigh → knee (narrower) → calf → ankle (2px), not a straight tube.
3. **Shading** — match the original's density: same palette, same number of tones, knee/heel/fold marks. Never simplify.
4. **Timing** — slip factor, holds, bounce. Numbers first, eyes second.

## 1. Extract

```
spriteforge extract screenshot.png cut.png --region x0 y0 x1 y1
```
* Region must be **wider than the character**. A horn touching the crop edge once deleted the whole body.
* Keeps the largest component + components inside its bbox (strands, gloves). Stars/coins nearby are dropped.
* Read the result at 4–8x before going on.

## 2. Snap to the native grid

```
spriteforge snap cut.png sprite_1x.png --colors 24
```
* AI "pixel art" has no grid. `detect_grid` brute-forces cell size + phase minimising within-cell variance; per-cell median; palette quantise. Output is sharper than the source.
* Sanity: the 1x sprite should be ~30–60 px tall for a typical platformer character.

## 3. Read before you edit

```
spriteforge dump sprite_1x.png > dump.txt
```
Palette-indexed ASCII map, one char per pixel, columns numbered. **Every edit is planned on this map** — exact rows, exact columns, exact palette symbols. `Sprite.paint(y, x0, "2d342")` uses the same symbols the dump printed.

## 4. New pose (re-posing an existing sprite)

* Build a **parts map** first (`parts.segment` with polygons planned on the dump; colour filters keep skirt-red out of leg polygons). Look at `parts.preview` before erasing anything — it shows whether a strand, a frill or a glove landed in the wrong part.

* Keep everything that doesn't move **pixel-for-pixel** (head, hair, torso, costume). That's what keeps the character consistent.
* Erase limbs by exact ranges from the dump. Then **restore what was underneath from the source sprite** (`restore_from`) — never repaint the skirt/torso under a removed arm by guess.
* Draw the new limb with the limb DSL (`Limb`, `Pose`) or `paint()` rows, in the original palette, at the original shading density, matching the view angle (rule 0).
* Stray pixels: after erasing, dump again and hunt for orphan dots next to where the limb was.
* Verify against the source side by side at 12x before animating.

## 5. Idle / breathing (whole body, no seams)

* **Never offset body parts against each other.** A 1px seam on a 50px sprite reads as the character cut in half.
* Move the **whole body** (`offset`) or sink the upper body onto planted feet (`squash` — the absorbed row must be a uniform column, e.g. a shin).
* Secondary motion only where physics puts it: trailing hair strands (lag 1 px, one beat behind), skirt hem/cape tip (flare on the way down), a blink. Masks are picked by **colour + region**, not by cutting.
* `shift_region` fills vacated pixels from the row above — no holes.
* Blink = lids over the top 1–2 eye rows for one frame, lash row untouched. Wiping the iris to skin looks like a glitch.
* 12–16 frames, 90–120 ms. Blink once per loop at most.

## 6. Walk cycle (drawn, not flipped)

* Cut-and-flip legs are not animation: boots point backwards on alternate strides, thighs detach from hips, skirt pixels ride along. Draw the legs **fresh per frame** with `Limb.draw` and per-row offsets.
* 6 frames per cycle: **contact** (body low, front foot flat, back heel peeling) → **recoil** (still low) → **pass** (body high, swing foot bent and lifted under the body), then mirror for the other leg. Never leave the pass frames identical to standing — that's a hold that reads as a stutter.
* **Hair/cloth lag is measured in absolute position.** Body height per frame [1,1,0,…] → hair one frame late [0,1,1,…] → relative shift [-1,0,+1]. Shifting the hair only on the pass frame cancels the body's motion exactly and the hair looks glued on. Check the hair's absolute row across the frames, not its offset from the body.
* Personality lives in the walk: stride length (2–3 px = shy shuffle, 5–6 = march), what the hands do (clasped in front / swinging / in pockets), eye line (`lower_eyes` for shy), hair lag, bounce height.
* **Slip factor** before anything else: `ground_speed = steps_per_cycle × stride / cycle_seconds`. If the showcase moves the character faster than that, they skate. `motion.slip_factor` must be 1.0.

## 7. Back into the scene

* `paint_out` fills the character's silhouette with the background colour (dilate 5) so the animated sprite can be composited over its own screen. Then dump/inspect for leftover sole/outline specks and fill them.
* Measure the floor / platform top **from the source image** (in source pixels × display scale) and put the sole row exactly on it. Hovering 8 px above a platform is instantly visible.
* Don't let the character walk through raised platforms or leave the play window. Path them.
* Verify the final mp4 with a contact sheet (`ffmpeg -vf fps=1,tile=...`), not the pipeline.

## 8. Process rules

* `ffmpeg -y` always; without it a chained render hangs on an overwrite prompt.
* One critique = one rule. Log it here.
* When the user says "something is off but I'm not sure what", **measure** (slip factor, frame diffs, silhouette widths) before guessing.
