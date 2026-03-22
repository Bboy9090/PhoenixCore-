"""Facade for the cold-fuse imaging engine."""
from __future__ import annotations
from typing import Dict, Any
from ..imaging.cold_fuse import cold_fuse_clone as _clone


def cold_fuse_clone(src: str, dst: str, dry_run: bool = False) -> Dict[str, Any]:
    return _clone(src, dst, dry_run=dry_run)
