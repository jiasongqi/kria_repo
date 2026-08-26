# Desktop pet art prompt templates

Use **English** prompts for image models. Always request **transparent background only (no checkerboard)**. Generate **style previews first**, let the user pick, then mass-export action frames with `reference_image_paths`.

## Workflow

```
1. Style lottery (V1–V6-like) → assets/previews/
2. User picks 1–2 looks
3. Per look: idle_0/1, walk_0/1, click_0/1 (+ optional polish frames)
4. Copy raw → assets/source/ → run process_chosen_frames.py
```

## Shared locks (every prompt)

Append or keep these constraints:

- Full body centered, 1:1 canvas
- Big head chibi / Q-version (~60–70% head)
- Same identity across frames (hair, face, outfit)
- Transparent background ONLY — no checkerboard baked into RGB
- Clean edges; no watermark / no text
- White sneakers OK (matte pipeline must keep them)

Avoid: purple-on-white AI cliché, cream+terracotta default, newspaper layout vibes, Live2D-looking faces unless requested.

## A. Style preview — sticker (V2-like)

```
Cute chibi desktop pet, Q-version young East Asian man.
Style: soft moe anime sticker, clean thin outlines, glossy eyes, polished sticker sheet look.
Outfit: black thick sunglasses, light blue thin-stripe shirt, blue-and-white patterned scarf, silver chain, white sneakers.
Standing idle front view, full body centered, transparent background only (no checkerboard).
Adorable cool-but-cute expression, soft blush. No text, no watermark.
```

## B. Style preview — plush / vinyl toy (V6-like)

```
Ultra cute Chinese desktop-pet mascot, plush vinyl toy feeling.
Extremely round soft head, tiny stubby body and limbs, very thick rounded outlines, soft 3D kawaii shading.
Same young man Q-version: black sunglasses, light blue stripe shirt, blue-white scarf, silver chain, white sneakers.
Standing idle front view, full body, transparent background only (no checkerboard). Soft smile. No text.
```

## C. Style preview — scholar variant (optional)

```
Cute chibi desktop pet, Q-version handsome young East Asian man.
Style: [sticker | plush vinyl] consistent with chosen look.
Outfit: thin gold rectangular glasses, black blazer, white tiny-stripe shirt, black necktie, fluffy black hair with soft side bangs, white sneakers.
Idle front view, full body, transparent background only. Gentle cool-but-cute expression. No text.
```

## D. Action frames (always pass reference image)

Replace `{STYLE}` with `sticker art style` or `plush vinyl toy style`.

### Idle

```
Same character as reference, identical {STYLE} and outfit.
Transparent background only (no checkerboard). Full body centered.
Standing idle facing camera, soft gentle smile, slight subtle breath / tiny head bob.
Clean edges. Do not change proportions or clothes.
```

### Walk

```
Same character as reference, identical {STYLE} and outfit.
Transparent background only. Full body.
Walking pose with [left|right] leg forward, arms slightly swung.
CRITICAL: clean white sneakers — NO black blobs, NO dark triangles near shoes, clean feet cutout.
Keep same height and head size as reference.
```

### Click / reaction

```
Same character as reference, identical {STYLE} and outfit.
Transparent background only. Full body.
Cute click reaction: [push sunglasses / wink / heart hands / slight lean].
Keep silhouette readable at small size (~144px). Same proportions as reference.
```

## E. Naming convention

```
assets/source/
  sticker_idle_0.png  sticker_idle_1.png
  sticker_walk_0.png  sticker_walk_1.png
  sticker_click_0.png sticker_click_1.png
  plush_idle_0.png    ...
assets/previews/v2_*.png  # user pick only
```

Wire stems in `tools/process_chosen_frames.py` `MAP`.

## F. Consistency tips

- One reference per skin; never mix V2 pose onto V6 shading mid-batch
- Prefer **small pose deltas** between idle_0 and idle_1 (pipeline often uses one key + bob)
- If walk feet look dirty: regenerate walk with the CRITICAL sneakers line, then re-matte
- Reject frames with baked checkerboard — re-gen or matte will fail QC
