"""
Repository-root resolution for the FastAPI backend.

Avoids hard-coded machine paths so diagnostics and OCLP discovery work on any
checkout (CI, developer laptops, cloud agents).
"""
from __future__ import annotations

import os
from pathlib import Path

_ENV_ROOT = "PHOENIX_REPO_ROOT"


def repo_root() -> Path:
    """
    Absolute path to the Phoenix Core repository root (directory containing
    `crates/`, `backend/`, `desktop/`, etc.).
    """
    env = os.environ.get(_ENV_ROOT)
    if env:
        p = Path(env).expanduser().resolve()
        if p.is_dir():
            return p
    # backend/core/phoenix_paths.py -> parents[2] == repo root
    here = Path(__file__).resolve()
    return here.parents[2]


def oclp_submodule_path() -> Path:
    """OpenCore-Legacy-Patcher location when present as a git submodule."""
    return repo_root() / "third_party" / "OpenCore-Legacy-Patcher"


def recovery_gui_dist() -> Path:
    """Built recovery GUI assets (optional)."""
    return repo_root() / "website" / "recovery-gui" / "dist"


def legacy_boot_kiosk_script() -> Path:
    """Optional kiosk launcher copied onto recovery media."""
    return repo_root() / "legacy" / "scripts" / "boot-kiosk.sh"
