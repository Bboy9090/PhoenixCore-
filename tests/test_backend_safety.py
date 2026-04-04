"""FastAPI backend safety validation."""

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_validate_safety_blocks_unknown_device():
    from core.usb_builder import validate_safety

    r = validate_safety("/dev/phoenix_nonexistent_test_device", "recovery")
    assert r["safe_to_proceed"] is False
    assert r["device_info"] is None
    assert any("not found" in e.lower() or "not visible" in e.lower() for e in r["errors"])
