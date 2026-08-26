# Desktop pet architecture reference

## Process / windows

```
main.py
  ├─ QLockFile single-instance (unless --multi)
  ├─ QApplication
  └─ PetWindow (frameless, Tool, translucent, topmost)
        ├─ SpeechBubble  (separate Tool HWND)
        └─ EffectOverlay (separate Tool HWND, mouse-transparent)
```

Why separate HWNDs for bubble/VFX:

- Painting particles inside the pet’s per-pixel-alpha window often **does not show**
- First `show()` of a layered Tool window is slow → **prewarm** at startup

## Rendering

Each `paintEvent` on `PetWindow`:

1. Clear offscreen `QImage(Format_ARGB32_Premultiplied)` with `fill(0)`
2. Draw current sprite (and not VFX)
3. Blit to widget with `CompositionMode_Source` (full replace — kills DWM ghost trails)

Mirror: cache left/right `QPixmap` lists; PyQt6 has no `QPixmap.mirrored` — use `QImage.mirrored` then `QPixmap.fromImage`.

## State machine signals

| Signal | Payload | Consumer |
|--------|---------|----------|
| `state_changed` | `idle/walk/click/sleep` | switch sprite action |
| `frame_tick` | — | advance frame |
| `walk_step` | `dx, dy` | move on current monitor |
| `request_bubble` | text | bubble above head |
| `click_effect` | `glasses/hearts/yuanbao` | overlay VFX |
| `facing_hint` | bool right | mirror |

## Click effects

- `glasses` → play `click` frames
- `hearts` / `yuanbao` → keep `idle` pose + overlay particles on **side lanes**
- Always `bubble.raise_()` after VFX so text stays readable
- Bubble placement: **always center above head** (do not jump left/right by effect)

## Walk / multi-monitor

```python
screen = QGuiApplication.screenAt(frameGeometry().center()) or widget.screen()
geo = screen.availableGeometry()
```

Start direction: if nearer left edge → prefer right, and vice versa (pet often docks bottom-right).

Mid-walk: random turn timer + optional small `dy` + occasional faster step.

## Config knobs (`pet/config.py`)

- `IDLE_FPS` / `WALK_FPS` / `CLICK_FPS`
- `WALK_MOVE_MS`, `WALK_SPEED`, turn / duration ranges
- `SLEEP_AFTER_MS`, `CURSOR_SAMPLE_MS`
- `BUBBLES_BY_EFFECT`, `CLICK_EFFECT_WEIGHTS`
- `SKINS`, `SKIN_LABELS`

## Launch

- End users: `启动萌宠.bat` → `pythonw` (no console)
- Dev: `python main.py`
- Multi: `pythonw main.py --multi`
