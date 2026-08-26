---
name: windows-q-desktop-pet
description: >-
  Build a Windows Q-version (chibi) desktop pet from 0 to 1 with PyQt6:
  AI art prompt templates (sticker/plush), matting white clothes safely,
  idle/walk/click animations, click VFX, speech bubbles, low-CPU timers,
  multi-monitor bounds, single-instance launch, and PyInstaller packaging.
  Use when creating or fixing a Windows desktop pet, 桌面萌宠, shimeji-like
  pet, transparent always-on-top mascot, PNG sprite matting, GenerateImage
  prompts for pets, or DesktopPet.exe build.
---

# Windows Q 版桌面萌宠（0→1）

Reference implementation: `D:\desktop-pet` (Python + PyQt6).

## Goal

Ship a **frameless, transparent, always-on-top** Windows pet that:

- Uses **Q-version / chibi** sprites (not Live2D)
- Supports **skin switch**, **drag**, **walk/idle/click**, **speech bubble**, **click VFX**
- Stays **low CPU** (throttled FPS + sleep)
- Survives **multi-monitor** drag without jumping back to primary
- Defaults to **single instance**

## 0→1 checklist

Copy and track:

```
Progress:
- [ ] 1. Requirements + skin brief
- [ ] 2. Project scaffold (PyQt6)
- [ ] 3. Style lottery + action frames (prompt templates)
- [ ] 4. Matte pipeline (safe for white shoes/pants)
- [ ] 5. Normalize frames (same height, feet baseline)
- [ ] 6. State machine (idle/walk/click/sleep)
- [ ] 7. Interactions (drag, bubble, VFX, menu)
- [ ] 8. Low-CPU + multi-monitor + single-instance
- [ ] 9. Launch without console + smoke test
- [ ] 10. PyInstaller onedir ship (build.ps1)
```

## Step 1 — Requirements

Ask once, then lock:

| Item | Default in this project |
|------|-------------------------|
| Platform | Windows desktop resident |
| Style | Q 版可爱风；两套皮肤可右键切换 |
| Motion | idle / walk / click / sleep |
| Extra | bubble + hearts / yuanbao VFX |
| CPU | idle ~8–12 FPS; sleep after ~60s |

Do **not** start with geometric Pillow stick figures if user wants cute — generate AI chibi + process, or use artist PNGs.

## Step 2 — Scaffold

```
desktop-pet/
  main.py
  pet/
    config.py
    window.py          # transparent topmost + offscreen buffer
    state_machine.py   # idle/walk/click/sleep
    renderer.py        # frames + mirror cache
    bubbles.py         # separate Tool bubble window
    effects.py         # separate VFX overlay
  assets/
    source/            # raw generated PNGs
    <skin>/{idle,walk,click}/frame_XX.png
  tools/
    process_chosen_frames.py
    generate_assets.py   # optional procedural fallback
  启动萌宠.bat           # pythonw, no console
  requirements.txt
```

Stack: **Python 3.11+ / PyQt6 / Pillow**. Prefer PyQt6 over Electron for low CPU.

## Step 3 — Art sources + prompt templates

Per skin, need at least:

- `idle_0`, `idle_1` (optional second pose)
- `walk_0`, `walk_1`
- `click_0`, `click_1`

Full copy-paste prompts (sticker / plush / scholar + action frames):  
see [reference-prompts.md](reference-prompts.md).

Short rules:

- Style lottery first → user picks → then frames with `reference_image_paths`
- Transparent background ONLY — no checkerboard in RGB
- Full body, consistent outfit/identity; white sneakers OK
- Walk prompts must forbid black foot blobs / dark triangles near shoes

## Step 4 — Matting (critical)

**Never** unbounded “grow into all whiteish pixels from character” — that claims the whole white background → **opaque square white frame**.

Correct approach (see [reference-matting.md](reference-matting.md)):

1. Mark **strong content** (chromatic / dark)
2. White connected components:
   - touch image border → **background**
   - enclosed → **keep** (shoes / pants)
3. Optional: claim near-white fringe only within ~10px of strong content
4. Flood-erase bg from corners through white/checker
5. Foot cleanup:
   - strip only **charcoal fringe touching transparency**
   - do **not** delete dark shoe soles
   - fill only **well-enclosed** holes (no aggressive morph expand into crotch gaps)

Validate:

```python
# corners must be fully transparent
assert all(px[x, y][3] == 0 for x,y in corners)
# QC feet on magenta bg — no white square, shoes solid
```

## Step 5 — Frame normalize + animation

After matte:

1. Trim → scale to **shared height** → pin **feet to baseline** on fixed canvas (e.g. 160×160)
2. Export 6–8 frames per action
3. Animation rules that avoid “zoom pulse” / ghosting:
   - **Idle**: single silhouette + vertical bob only (do not hard-cut between differently scaled AI poses)
   - **Walk**: alternate same-height poses; no `Image.blend` dissolve (ghost trails)
   - **Click**: hold then cut to reaction pose
4. Do polish **after** downscale for speed

## Step 6 — Runtime architecture

See [reference-architecture.md](reference-architecture.md).

Minimum behaviors:

| State | Behavior |
|-------|----------|
| idle | low FPS loop; face cursor with hysteresis |
| walk | move on **current monitor** work area; mid-path random turns; prefer away from nearer edge |
| click | random effect: glasses frames / hearts / yuanbao; matching bubble text |
| sleep | stop anim timers after idle timeout; wake on near cursor / click |

**Walk pitfall**: if pet docks at primary **right** edge and bounds use `primaryScreen()` only, it always bounces left and/or jumps monitors. Use `QGuiApplication.screenAt(center)` / `widget.screen()`.

## Step 7 — Interactions

- **Drag**: left drag; click = release without drag (4px threshold)
- **Bubble**: separate always-on-top Tool window; **always above head** (consistent); prewarm at startup
- **VFX**: separate overlay; particles on **side lanes** so they do not cover bubble; `bubble.raise_()` after spawn
- **Menu**: skins, always-on-top, quiet mode, quit
- **First-click hitch**: prewarm bubble + effect HWNDs with opacity 0 / hidden after `show()+repaint()`

## Step 8 — Hardening

Low CPU:

- Idle/walk ~10 FPS; cursor sample ~250ms
- Sleep ~60s without input
- `BELOW_NORMAL` process priority on Windows
- Offscreen `QImage` ARGB32_Premultiplied → `CompositionMode_Source` full-window blit (kills translucent ghosting)

Single instance:

- `QLockFile` in temp (e.g. `desktop-pet-qver.lock`)
- Second launch exits 0
- Optional `--multi` escape hatch

Launch:

- `pythonw main.py` or `启动萌宠.bat` (no CMD tether)
- Closing CMD must not be required

## Step 9 — Smoke test

1. No white square around pet
2. Shoes intact on walk frames
3. Walks both left and right; survives secondary monitor
4. Click cycles glasses / hearts / yuanbao; bubble stays above head
5. Second launch does not spawn duplicate
6. Right-click → exit works

## Step 10 — Package (PyInstaller)

See [reference-packaging.md](reference-packaging.md).

```powershell
powershell -ExecutionPolicy Bypass -File tools\build.ps1
# → dist\DesktopPet\DesktopPet.exe  (ship whole folder, windowed/onedir)
```

Must `--add-data "assets;assets"` on Windows; `console=False`. Re-matte before rebuild after art changes. Frozen builds must not call `process_chosen_frames.py`.

## Do / Don't

**Do**

- Separate Tool windows for bubble and VFX
- Current-monitor bounds for walk
- Height-normalize all keys of a skin
- Prewarm layered windows
- Prompt with reference image for every action frame
- Ship onedir `dist\DesktopPet\` folder

**Don't**

- `Image.blend` between dissimilar AI poses for “smoothness”
- Matte by growing into all whites unbounded
- Clamp walk to `primaryScreen()` only
- Put VFX paint only inside pet transparent HWND (often invisible)
- Rely on console `python main.py` for end users
- Bake checkerboard into source art
- Distribute only the `.exe` without sibling datas (onedir)

## Reference project map

| Path | Role |
|------|------|
| `pet/window.py` | Topmost transparent pet + buffer clear |
| `pet/state_machine.py` | States, random walk turns, click effects |
| `pet/bubbles.py` | Animated speech bubble |
| `pet/effects.py` | Hearts / yuanbao overlay |
| `pet/renderer.py` | Frame cache + horizontal mirror |
| `tools/process_chosen_frames.py` | Matte + normalize + export frames |
| `tools/build.ps1` | PyInstaller windowed onedir build |
| `DesktopPet.spec` | Frozen Analysis / COLLECT |
| `main.py` | Assets ensure + lock + `pythonw` entry |

## Additional resources

- Art / GenerateImage prompts: [reference-prompts.md](reference-prompts.md)
- Matting details and failure modes: [reference-matting.md](reference-matting.md)
- Module responsibilities and signals: [reference-architecture.md](reference-architecture.md)
- PyInstaller ship checklist: [reference-packaging.md](reference-packaging.md)
