"""FastAPI backend safety validation (demo device gate)."""

import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


@pytest.fixture
def clear_demo_env():
    os.environ.pop("PHX_ALLOW_DEMO_DEVICE", None)
    yield
    os.environ.pop("PHX_ALLOW_DEMO_DEVICE", None)


def test_validate_safety_blocks_unknown_device_without_demo(clear_demo_env):
    from core.usb_builder import validate_safety

    r = validate_safety("/dev/phoenix_nonexistent_test_device", "recovery")
    assert r["safe_to_proceed"] is False
    assert r["device_info"] is None
    assert any("not found" in e.lower() or "not visible" in e.lower() for e in r["errors"])


def test_validate_safety_allows_demo_device_when_env_set():
    os.environ["PHX_ALLOW_DEMO_DEVICE"] = "1"
    try:
        from core.usb_builder import validate_safety

        r = validate_safety("/dev/phoenix_nonexistent_test_device", "recovery")
        assert r["device_info"] is not None
        assert r["device_info"].get("id") == "demo"
    finally:
        os.environ.pop("PHX_ALLOW_DEMO_DEVICE", None)
