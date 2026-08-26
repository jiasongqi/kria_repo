# Desktop pet matting reference

## Failure modes seen in production

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Opaque **square white frame** | Unbounded grow into all whiteish pixels claimed entire white BG | White CC: border-touching = BG; enclosed = keep |
| White sneakers become holes | Corner flood through white ate shoes (often via white outline bridge) | Keep enclosed white CCs; limited near-content fringe only |
| Black wedge on shoe / pants cuff | AI fringe or leftover matte charcoal | Remove only charcoal **touching transparency**; inpaint with bright neighbors |
| Shoe looks hollow after “cleanup” | Deleted dark sole or morph-close filled gaps then looked broken | Never morph-expand foot crotch; keep soles; only enclosed hole fill |
| Zoom pulse while animating | Alternating AI keys with different cropped heights | Force shared target height + feet baseline; idle = one key + bob |
| Ghost / smear on action change | `Image.blend` dissolve + translucent HWND residue | Hard cuts / bob only; offscreen buffer + `CompositionMode_Source` blit |

## Recommended pipeline order

1. `remove_background` (border-aware white CC)
2. `trim`
3. `normalize_height` to shared `TARGET_H`
4. `clean_foot_artifacts` (fringe only)
5. `fill_foot_holes` (n≥5–6 opaque neighbors)
6. `place_on_canvas` feet-pinned
7. Expand idle/walk/click frame sequences **without** alpha dissolve between dissimilar poses

## QC commands

```python
from PIL import Image

im = Image.open("assets/plush/idle/frame_00.png").convert("RGBA")
w, h = im.size
px = im.load()
corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
assert all(c[3] == 0 for c in corners), corners

# Magenta composite reveals holes
bg = Image.new("RGBA", im.size, (255, 0, 255, 255))
Image.alpha_composite(bg, im).save("qc_magenta.png")
```

## White clothing algorithm (summary)

```
strong = chromatic or dark pixels
white_cc = connected whiteish regions
keep = strong ∪ {white_cc that do NOT touch image border}
protect = dilate(keep, small)
bg = flood from borders through white/checker while avoiding protect
alpha = 0 on bg
```

## Foot cleanup rules

- **Strip**: `r,g,b < ~45`, component size small, **and** touches `alpha < 25`
- **Keep**: dark soles inside shoe that do not touch empty bg
- **Fill holes**: transparent pixel with ≥5–6 opaque neighbors → average neighbor color
- **Avoid**: `MaxFilter` morph close on whole foot band (creates dark wedges between legs)
