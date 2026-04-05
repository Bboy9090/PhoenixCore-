"""Smoke: import boundary script exits 0 on clean tree."""

import subprocess
import sys
from pathlib import Path


def test_check_import_boundaries_zero_exit():
    repo = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, str(repo / "scripts" / "check_import_boundaries.py")],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
