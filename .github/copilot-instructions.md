# Copilot Command Guide

## Bootstrap
- `pip install -r requirements.txt`【F:README.md†L43-L53】

## Build
- **Recommended:** `python src/installers/build_installer.py`【F:README.md†L170-L174】
- `pyinstaller --onefile --name=PhoenixKey main.py`【F:README.md†L170-L177】
- `python -m PyInstaller --onefile --windowed --name BootForge --add-data src:src --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.QtGui --hidden-import requests --hidden-import psutil --hidden-import cryptography --hidden-import yaml --hidden-import click --hidden-import colorama main.py` (use `;` instead of `:` in `--add-data` on Windows)【F:build_system/simple_build.py†L19-L36】

## Test
- `python -m pytest tests/`【F:README.md†L179-L183】
- `python -m pytest tests/ --cov=src`【F:README.md†L183-L186】

## Lint
- No lint commands are documented in the reviewed files.

## Package
- `python build_system/build_all.py` (ensures PyInstaller is installed, builds the platform executable, and generates the USB toolkit)【F:build_system/build_all.py†L11-L47】
