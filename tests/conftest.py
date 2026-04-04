"""Pytest configuration for BootForge tests."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESKTOP = ROOT / "desktop"

# Tests import `src.*` (BootForge engine under desktop/src).
if str(DESKTOP) not in sys.path:
    sys.path.insert(0, str(DESKTOP))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
