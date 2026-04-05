# Copilot Command Guide

Commands below match **`AGENTS.md`** and the verified layout: BootForge lives under **`desktop/`** (root **`main.py`** delegates to **`desktop/main.py`**). Rust: prefer building **individual crates** on Linux (full workspace may fail; see `AGENTS.md`).

**Authority / safety:** `docs/AUTHORITY_MODEL.md`, `docs/SAFETY_MODEL.md`, `docs/CAPABILITY_MATRIX.md`.

## Bootstrap

- **Python (BootForge + tests):** `pip install -r requirements.txt` (installs **`phoenix-safety` from `./packages/phoenix_safety`**)
- **Python (FastAPI backend only):** `pip install -r backend/requirements.txt` (includes phoenix-safety)
- **OCLP (optional):** `git submodule update --init third_party/OpenCore-Legacy-Patcher` (see `docs/oclp_integration.md`)
- **Rust:** Install Rust (e.g. rustup); stable >= 1.94 for edition 2024 dependencies.

## Build

- **Rust (supported crates, Linux):**  
  `cargo build -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim`
- **Rust release (same packages):** add `--release`.
- **BootForge (PyInstaller example):** run from repo root with `desktop` as cwd so `src` resolves:  
  `cd desktop && python -m PyInstaller --onefile --windowed --name BootForge --add-data src:src --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.QtGui --hidden-import requests --hidden-import psutil --hidden-import cryptography --hidden-import yaml --hidden-import click --hidden-import colorama main.py`  
  On Windows use `;` instead of `:` in `--add-data`.

## Test

- **Python:** `python3 -m pytest tests/`
- **Rust (supported crates):**  
  `cargo test -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim`

## Lint

- **Rust:** `cargo clippy` with the same `-p` list as build.  
- **Rust format:** `cargo fmt --check`

## Run (dev)

- **BootForge GUI:** `python3 main.py --gui`
- **BootForge CLI:** `python3 main.py --help`
- **FastAPI backend:** `pip install -r backend/requirements.txt && cd backend && uvicorn main:app --host 0.0.0.0 --port 8000`
- **Flask web demo:** `python3 website/web_server.py`

## Package

- If `build_system/build_all.py` exists in your checkout, it may orchestrate installers; prefer scripts checked into the repo over guessed invocations.
