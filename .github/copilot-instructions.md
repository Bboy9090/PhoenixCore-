# Copilot Command Guide

## Bootstrap
- **Python:** `pip install -r requirements.txt`【F:README.md†L43-L53】
- **Rust:** Install Rust (e.g. rustup); no separate bootstrap step for Phoenix Core crates.

## Build
- **Rust (Phoenix Core CLI):** `cargo build --workspace`【F:.github/workflows/ci-windows.yml】
- **Rust release binary:** `cargo build --workspace --release` (output: `target/release/phoenix-cli` or `phoenix-cli.exe` on Windows)
- **Python (recommended):** `python src/installers/build_installer.py`【F:README.md†L170-L174】
- **Python:** `pyinstaller --onefile --name=PhoenixKey main.py`【F:README.md†L170-L177】
- **Python (BootForge):** `python -m PyInstaller --onefile --windowed --name BootForge --add-data src:src --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.QtGui --hidden-import requests --hidden-import psutil --hidden-import cryptography --hidden-import yaml --hidden-import click --hidden-import colorama main.py` (use `;` instead of `:` in `--add-data` on Windows)【F:build_system/simple_build.py†L19-L36】

## Test
- **Rust:** `cargo test --workspace`【F:.github/workflows/ci-windows.yml】
- **Python:** `python -m pytest tests/`【F:README.md†L179-L183】
- **Python (with coverage):** `python -m pytest tests/ --cov=src`【F:README.md†L183-L186】

## Lint
- No lint commands are documented in the reviewed files.

## Package
- `python build_system/build_all.py` (ensures PyInstaller is installed, builds the platform executable, and generates the USB toolkit)【F:build_system/build_all.py†L11-L47】
