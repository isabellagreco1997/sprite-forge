# Detailed pixel art and title-screen animation

A title portrait may be 100–200 logical pixels tall and use 64–128 colors. Do not force it into the 30–60px platformer example. Measure the visible pixel scale of the surrounding art, choose one logical stage, and preserve the original silhouette, view angle, palette relationships and shading density. Inspect eyes, hands, horns and costume details after grid snapping.

## Art correction comes before motion

1. Inspect the alpha channel, not a checkerboard preview. An RGB image containing a checkerboard is not transparent. Inspect over both a dark and a light matte.
2. Clean detached edge noise, preserving intentional sparks and highlights. Do not blindly remove all small components.
3. Match the displayed pixel grid across layers. A shared source resolution does not guarantee equal displayed pixels if one layer is independently resized.
4. Make a registered static composition and inspect it at native scale and nearest-neighbor enlargement. Do not use motion to disguise inconsistent art.

## Author actual keyframes

When the request is for newly designed frames, do not substitute whole-image transforms, palette cycling alone, or a region-warp function. Those are effects, not a substitute for the requested drawing.

- Dump the base sprite and inspect a color-coded parts map before editing. Record exact rows, columns, original palette symbols, stationary anchors and the destination extent of each moving part.
- Draw key poses as explicit pixel rows or saved PNGs: for example, relaxed lock, left-curving lock, transition, right-curving lock and return. Redesign contours and their internal shading together.
- Keep the stationary body and costume pixel-identical. Include the vacated area in the parts plan; restore it from known source pixels, not a guessed color.
- On a flame, redraw the outer contour, hot core and shadow band together. Register every frame at the wick.
- A detailed blink needs a close-up study of the original eye. Start with one or two upper interior rows, retain the lash contour and avoid wiping the entire iris with flat skin. Check the blink in motion before increasing closure.
- Store the drawn keyframes separately from the timeline. Holds, repeats and playback code may assemble them; they must not silently generate new shapes by shifting source regions.
- Use a return pose that matches the opening pose. Inspect the wrap from the final frame to the first, not only the middle of the loop.

The existing `idle_loop` remains useful for a simple breathing effect when that is what was requested. It should not be described as freshly drawn character animation.

## Registration and timing

Use identical canvas dimensions and a fixed origin. Do not independently crop and resize every frame to fit: changing hair or flame bounds will make the body jitter. A common union crop is safe when every frame retains the same crop origin.

Plan key poses first, then in-betweens and holds. Start around 8–12 fps for subtle title-screen motion and inspect the actual loop; a large count of duplicated or automatically modified frames does not prove animation quality. Different subjects can have different cycles and blink timings.

Generated contact sheets need particular care: inspect every cell for clipping, inconsistent scale, costume drift and shifted body anchors. Reject a clipped cell instead of stretching it or inventing its missing pixels during packing.

## Palette-safe editing and validation

`Sprite.dump()` supports up to 256 colors using one glyph per pixel. The first 62 symbols are unchanged; extended palettes use punctuation followed by Unicode glyphs. Save maps as UTF-8. Space clears and dot preserves a pixel. Do not reuse a palette symbol for a new named color without checking for a collision. More than 256 colors raises an explicit error instead of silently dropping colors.

```python
from spriteforge import Sprite, frame_report

reference = Sprite.load("idle-00.png")
frames = [Sprite.load(f"idle-{i:02d}.png") for i in range(8)]
# Boolean HxW mask covering both original and destination positions of moving parts.
reports = frame_report(reference, frames, allowed_change=animation_mask)
assert all(r["size_matches"] for r in reports)
assert all(r["outside_mask_pixels"] == 0 for r in reports)
```

The report measures visible changes, changes outside the planned mask, new colors, partial alpha, new pixels on canvas edges, and isolated pixels. A spark can legitimately appear in the isolated-pixel list, so interpret the coordinates against the parts map. Reports do not establish artistic quality. Review enlarged contact sheets, a loop at native size, and the integrated game scene; verify pause/reduced-motion behavior as well.
