# AGENTS.md — BootForge/Phoenix Key Agent Doctrine (Root)

## Prime Directive
Make changes that build and test cleanly, with honest validation.

## Absolute rules
- Never claim you ran commands you didn’t run.
- Never guess build steps. Discover them from:
  - `bootable_usb/BootForge/build_system/`
  - `bootable_usb/BootForge/pyproject.toml` / `requirements.txt`
  - `bootable_usb/BootForge/README.md` / `QUICK_START.txt`
- Do not touch packaged artifacts in `dist/` or compiled outputs unless the task is explicitly about release packaging.

## Workflow
1) Restate task in 1–3 bullets.
2) Identify owning area:
   - BootForge runtime: `bootable_usb/BootForge/src/...`
   - Build system: `bootable_usb/BootForge/build_system/...` or root build scripts
   - USB toolkit: `bootable_usb/BootForge/usb_toolkit/...` and `tools/...`
3) Read the nearest README/TXT in that subtree.
4) Change the smallest set of files.
5) Update/extend tests in `bootable_usb/BootForge/tests/` when behavior changes.
6) Validate via commands or “inspection validation”.

## High-risk zones (edit only if required)
- `*.spec`, `build_exe.py`, `build_cross_platform.py`, `build_packages.py`
- install scripts: `install-*.sh`, `install-*.bat`, `install-windows.ps1`, `windows-setup.bat`
- anything under `old_builds/`, `dist/`, `build/` (these are outputs/archives)

## Quality bar
Reject your own PR if:
- It adds “fake success”
- It breaks platform separation
- It introduces secrets
- It changes release/build without explicit need
