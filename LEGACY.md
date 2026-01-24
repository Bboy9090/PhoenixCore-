# Legacy Materials (to remove or quarantine)

This repository is being reshaped into **phoenix-core**. The following
directories/files are legacy and will be removed or moved to a donor repo:

## Legacy areas
- `src/` (Python runtime + GUI)
- `tests/` (Python tests)
- `bootable_usb/` (legacy toolkit)
- `dist/` (generated artifacts)
- `build/` (generated artifacts)
- `archive/` (legacy build scripts)
- `assets/` + `desktop/` (branding + legacy)
- `main.py`, `pyproject.toml`, `requirements.txt`, `uv.lock`

## Policy
No external tools are required at runtime for Phoenix Core. Anything that
depends on shelling out or bundled executables is considered legacy until
it is reimplemented in Rust under `crates/`.
