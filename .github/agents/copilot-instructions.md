# BootForge / Phoenix Key — Copilot Instructions (Repository-Wide)

## What this repository contains (high-level)
This repo mixes:
- BootForge product source + bootable USB toolkit (Python) under `bootable_usb/BootForge/`
- Build/packaging utilities at repo root (`build_cross_platform.py`, `build_packages.py`, `bootforge-standalone.py`, `*.spec`, `install-*.bat/.sh/.ps1`)
- Assets/branding under `assets/`, `branding/`
- Agent prompt files under `.github/agents/`
- Historical/archived build artifacts in `old_builds/`, `old_installers/`, and dist folders

Primary product: BootForge Python app + USB toolkit (bootable installer builder + diagnostics + patch pipeline).

## Non-negotiables
- Never fabricate “command succeeded”, test results, CI results, device detection, patch success, or build artifacts.
- Never return “success” unless the actual side-effect occurred.
- Never add secrets or real credentials. Only modify `.env.example`-style files.
- Do not add bypass/exploit or lock-circumvention logic. If asked, propose lawful diagnostic/restore alternatives.

## Where to make changes (do not wander)
If the task is about BootForge behavior, start here:
- `bootable_usb/BootForge/src/`
  - `core/` (core logic)
  - `cli/` (CLI entry)
  - `gui/` (GUI)
  - `imaging/` (imaging pipeline)
  - `installers/` (installer logic)
  - `recovery/` (recovery workflows)
  - `plugins/` (plugin system)
  - `network/proto/` (protobuf)
  - `utils/` (shared utilities)
- Tests live in: `bootable_usb/BootForge/tests/`

If the task is about building binaries/installers, look here:
- Root scripts: `build_cross_platform.py`, `build_packages.py`, `bootforge-standalone.py`
- BootForge build system: `bootable_usb/BootForge/build_system/`
- Specs: `BootForge.spec`, `BootForge-*.spec`, and `bootable_usb/BootForge/build_system/specs/`

If the task is about USB toolkit artifacts, look here:
- `bootable_usb/BootForge/usb_toolkit/` and `bootable_usb/BootForge/tools/`

## How to build / test (rule)
Do NOT guess commands.
- Prefer reading and using:
  - `bootable_usb/BootForge/pyproject.toml`
  - `bootable_usb/BootForge/requirements.txt` and `uv.lock` (if used)
  - `bootable_usb/BootForge/build_system/*.py`
  - `bootable_usb/BootForge/QUICK_START.txt`, `README.md`, `WINDOWS-README.txt`
  - Any CI workflow under `.github/workflows/` (if present in repo)

If execution is not possible, validate by inspection:
- Read the build_system scripts that generate EXE/PKG/USB zips
- Read the tests and ensure your change aligns with existing fixtures and expectations

## PR discipline
- Keep diffs minimal.
- Update tests for logic changes.
- Update docs only when user-facing behavior changes.
- PR description must include:
  - What changed + why
  - Validation (commands run OR “validation by inspection” listing scripts/tests read)
  - Risk/rollback notes

## Code quality standards (BootForge)
- Prefer explicit errors over silent failures.
- OS-specific logic must be guarded (Windows vs macOS vs Linux).
- Avoid hardcoded paths; use pathlib and platform-safe handling.
- Logging must be informative and must not leak secrets.
