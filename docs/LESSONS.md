# Lessons, in the order they were learned

Each entry is a critique from the artist, what was actually wrong, and the rule that came out of it.

| # | critique | what was actually wrong | rule |
|---|---|---|---|
| 1 | *"the run looks wrong"* | legs were cut out and mirrored; boots pointed backwards every other stride, thighs detached from hips, skirt pixels rode along with the legs | draw animation frames; a cut-out puppet can't run |
| 2 | *"you are cutting her in half instead of being creative with how she should move"* | idle loop offset head/torso/arms/legs by 1 px against each other → visible seams | move the whole body; secondary motion only where it happens (hair lag, hem, blink); fill vacated pixels |
| 3 | *"you did not keep the same amount of detail from her original legs"* | redrawn legs were flat tubes with one highlight | match the original's shading density: knee, calf, ankle, sock fold, heel |
| 4 | *"something weird happening to her eyes"* | blink wiped the iris to skin and drew a jagged lash | lids over the top 1–2 eye rows only, lash row untouched |
| 5 | *"observe her original shape of her legs, they are not completely straight"* | straight-line contour | measure widths row by row: thigh 5 → knee 4 → calf 4 → ankle 2 |
| 6 | *"make her legs closer together / no gap"* | stance too wide for a shy character | share one outline column between the legs |
| 7 | *"when she is walking is still a bit off, not sure what"* | ground speed 3× what the feet covered (skating) + two pass frames identical to standing (a hold) | slip factor = 1.0; contact → recoil → pass with the swing foot lifted |
| 8 | *"her body is turned to the right and her legs are like she is standing looking ahead"* | 3/4 torso on front-view legs | view angle first: overlapping profile legs, far leg behind |
| 9 | (self-caught) she hovered above the platform and a sole speck survived the paint-out | floor measured from the wrong edge; dilation too small | measure floor/platform tops from the source image; inspect the painted-out scene |
| 10 | (self-caught) red stripes past the hem after removing arms | repainted the skirt under the arms by guess | restore what was underneath from the source pixels |
| 11 | (self-caught) render chain hung | `ffmpeg` without `-y` waits on an overwrite prompt | always `-y` |
| 12 | *"her right leg is bigger than her left; if she looks right, the left leg should be in front and bigger, the right smaller, hidden by the leg in front"* | near/far legs were swapped: the far leg was drawn on the camera side | the camera-side leg is near: screen-left when facing right, drawn last, full width; far leg narrower and behind |
