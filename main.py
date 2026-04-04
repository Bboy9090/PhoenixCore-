#!/usr/bin/env python3
"""
Repository root entry point for BootForge (PyQt6 GUI / CLI).

Implementation lives under `desktop/`; this file exists so `python main.py`
matches README and CI expectations without duplicating logic.
"""
from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parent / "desktop" / "main.py"),
        run_name="__main__",
    )
