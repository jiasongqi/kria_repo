# Desktop pet PyInstaller packaging

Reference: `D:\desktop-pet` — onedir, windowed (`console=False`).

## Prefer

```powershell
cd D:\desktop-pet
python -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File tools\build.ps1
```

`tools\build.ps1` ensures frames exist, then:

```powershell
python -m PyInstaller --noconfirm --windowed --name DesktopPet `
  --add-data "assets;assets" `
  main.py
```

Output: `dist\DesktopPet\DesktopPet.exe` (+ `_internal\` / datas beside it).

Windows `--add-data` separator is **`;`** (`assets;assets`). On macOS/Linux use `:`.

## Spec file

Project keeps `DesktopPet.spec`:

- `datas=[('assets', 'assets')]`
- `console=False` (no black CMD)
- `exclude_binaries=True` + `COLLECT` → **onedir** (more reliable for Qt + many PNGs than onefile)

Rebuild from spec:

```powershell
python -m PyInstaller --noconfirm DesktopPet.spec
```

## Frozen asset path

`main.py` / `pet.config` must resolve assets when `sys.frozen`:

- Prefer `Path(sys._MEIPASS) / "assets"` if using onefile, **or**
- Onedir: assets next to exe via `--add-data` → often `Path(sys.executable).parent / "assets"` depending on layout

If assets missing when frozen, exit with a clear message (do not try to run `process_chosen_frames.py` inside the package).

## Checklist before ship

1. Run `tools\process_chosen_frames.py` so `assets/<skin>/{idle,walk,click}/` are current
2. Smoke-test with `pythonw main.py` (skins, click VFX, multi-monitor walk)
3. Build; copy whole `dist\DesktopPet\` folder (not only the `.exe`)
4. Launch `DesktopPet.exe` from Explorer — no console; single-instance lock still works
5. Optional: shortcut to exe; do not ship `build\` or `.spec` as required runtime

## Do / Don't

**Do**

- `--windowed` / `console=False` for end users
- Bundle entire `assets` tree
- Ship **onedir** folder for PyQt6 pets

**Don't**

- Expect users to keep a CMD open (`python main.py`)
- Use onefile blindly if Qt plugins / PNG load fail — fall back to onedir
- Forget to re-run matte pipeline after art changes before rebuild
- Commit huge `dist\` / `build\` unless the team wants binaries in git

## Dev vs ship launch

| Audience | Command |
|----------|---------|
| Dev | `python main.py` |
| Daily use | `启动萌宠.bat` → `pythonw` |
| Distribute | `dist\DesktopPet\DesktopPet.exe` |
| Multi pets | `DesktopPet.exe --multi` (if argv forwarded) |
