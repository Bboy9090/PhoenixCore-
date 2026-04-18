"""
Tests for the new removable_only / include_all parameters added to
scan_usb_devices() in backend/core/device_scanner.py (changed in this PR).

Also covers the new `filter` key returned in the result dict.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest import mock

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# psutil may not be installed in the minimal CI env; provide a stub so that
# device_scanner.py (which imports psutil at module level) can be imported.
if "psutil" not in sys.modules:
    _psutil_stub = types.ModuleType("psutil")
    _psutil_stub.disk_partitions = lambda all=False: []  # type: ignore
    sys.modules["psutil"] = _psutil_stub


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_device(path: str, removable: bool, is_system_disk: bool = False) -> dict:
    return {
        "id": path.lstrip("/").replace("/", "_"),
        "path": path,
        "name": f"Device {path}",
        "friendly_name": f"Drive at {path}",
        "size_bytes": 32 * 1024 ** 3,
        "size_gb": 32.0,
        "removable": removable,
        "is_system_disk": is_system_disk,
        "risk_level": "low",
    }


def _scan_patches(devices: list):
    """Return a list of context managers patching all OS-level scan helpers."""
    return [
        mock.patch("core.device_scanner._scan_linux", return_value=devices),
        mock.patch("core.device_scanner._scan_macos", return_value=devices),
        mock.patch("core.device_scanner._scan_windows", return_value=devices),
        mock.patch("core.device_scanner._scan_generic", return_value=devices),
    ]


class _MultiPatch:
    """Enter several patches as a group."""
    def __init__(self, patches):
        self._patches = patches

    def __enter__(self):
        for p in self._patches:
            p.start()
        return self

    def __exit__(self, *args):
        for p in reversed(self._patches):
            p.stop()


def _mock_scan(devices: list) -> _MultiPatch:
    return _MultiPatch(_scan_patches(devices))


# ---------------------------------------------------------------------------
# Default behaviour (backward compat)
# ---------------------------------------------------------------------------

class TestDefaultBehaviour:
    def test_returns_all_devices_by_default(self):
        from core.device_scanner import scan_usb_devices
        devices = [_make_device("/dev/sda", False), _make_device("/dev/sdb", True)]
        with _mock_scan(devices):
            result = scan_usb_devices()
        assert result["total"] == 2

    def test_filter_key_present_in_result(self):
        from core.device_scanner import scan_usb_devices
        with _mock_scan([]):
            result = scan_usb_devices()
        assert "filter" in result

    def test_filter_defaults(self):
        from core.device_scanner import scan_usb_devices
        with _mock_scan([]):
            result = scan_usb_devices()
        assert result["filter"]["removable_only"] is False
        assert result["filter"]["include_all"] is False

    def test_result_has_devices_key(self):
        from core.device_scanner import scan_usb_devices
        with _mock_scan([]):
            result = scan_usb_devices()
        assert "devices" in result

    def test_result_has_timestamp(self):
        from core.device_scanner import scan_usb_devices
        with _mock_scan([]):
            result = scan_usb_devices()
        assert "timestamp" in result

    def test_result_has_host_os(self):
        from core.device_scanner import scan_usb_devices
        with _mock_scan([]):
            result = scan_usb_devices()
        assert "host_os" in result
        assert isinstance(result["host_os"], str)


# ---------------------------------------------------------------------------
# removable_only=True
# ---------------------------------------------------------------------------

class TestRemovableOnly:
    def test_filters_out_non_removable(self):
        from core.device_scanner import scan_usb_devices
        devices = [
            _make_device("/dev/sda", removable=False),
            _make_device("/dev/sdb", removable=True),
            _make_device("/dev/sdc", removable=True),
        ]
        with _mock_scan(devices):
            result = scan_usb_devices(removable_only=True)
        paths = [d["path"] for d in result["devices"]]
        assert "/dev/sdb" in paths
        assert "/dev/sdc" in paths
        assert "/dev/sda" not in paths

    def test_total_matches_filtered_count(self):
        from core.device_scanner import scan_usb_devices
        devices = [
            _make_device("/dev/sda", removable=False),
            _make_device("/dev/sdb", removable=True),
        ]
        with _mock_scan(devices):
            result = scan_usb_devices(removable_only=True)
        assert result["total"] == 1
        assert len(result["devices"]) == 1

    def test_filter_key_reflects_params(self):
        from core.device_scanner import scan_usb_devices
        with _mock_scan([]):
            result = scan_usb_devices(removable_only=True)
        assert result["filter"]["removable_only"] is True
        assert result["filter"]["include_all"] is False

    def test_empty_result_when_no_removable_devices(self):
        from core.device_scanner import scan_usb_devices
        devices = [
            _make_device("/dev/sda", removable=False),
            _make_device("/dev/nvme0n1", removable=False),
        ]
        with _mock_scan(devices):
            result = scan_usb_devices(removable_only=True)
        assert result["devices"] == []
        assert result["total"] == 0

    def test_all_devices_returned_when_all_removable(self):
        from core.device_scanner import scan_usb_devices
        devices = [_make_device(f"/dev/sd{c}", removable=True) for c in "abc"]
        with _mock_scan(devices):
            result = scan_usb_devices(removable_only=True)
        assert result["total"] == 3


# ---------------------------------------------------------------------------
# include_all=True overrides removable_only
# ---------------------------------------------------------------------------

class TestIncludeAll:
    def test_include_all_overrides_removable_only(self):
        """include_all=True with removable_only=True should return all devices."""
        from core.device_scanner import scan_usb_devices
        devices = [
            _make_device("/dev/sda", removable=False),
            _make_device("/dev/sdb", removable=True),
        ]
        with _mock_scan(devices):
            result = scan_usb_devices(removable_only=True, include_all=True)
        assert result["total"] == 2

    def test_filter_key_reflects_both_params(self):
        from core.device_scanner import scan_usb_devices
        with _mock_scan([]):
            result = scan_usb_devices(removable_only=True, include_all=True)
        assert result["filter"]["removable_only"] is True
        assert result["filter"]["include_all"] is True

    def test_include_all_without_removable_only_still_returns_all(self):
        from core.device_scanner import scan_usb_devices
        devices = [
            _make_device("/dev/sda", removable=False),
            _make_device("/dev/sdb", removable=True),
        ]
        with _mock_scan(devices):
            result = scan_usb_devices(include_all=True)
        assert result["total"] == 2


# ---------------------------------------------------------------------------
# Device with removable=None / missing key (edge case)
# ---------------------------------------------------------------------------

class TestRemovableEdgeCases:
    def test_device_with_removable_none_excluded_when_removable_only(self):
        """d.get('removable') is True must be strictly True (not None or False)."""
        from core.device_scanner import scan_usb_devices
        dev = _make_device("/dev/sdb", removable=False)
        dev["removable"] = None  # ambiguous
        with _mock_scan([dev]):
            result = scan_usb_devices(removable_only=True)
        assert result["total"] == 0

    def test_device_missing_removable_key_excluded_when_removable_only(self):
        from core.device_scanner import scan_usb_devices
        dev = _make_device("/dev/sdb", removable=False)
        del dev["removable"]  # key absent
        with _mock_scan([dev]):
            result = scan_usb_devices(removable_only=True)
        assert result["total"] == 0

    def test_scan_time_ms_is_numeric(self):
        from core.device_scanner import scan_usb_devices
        with _mock_scan([]):
            result = scan_usb_devices()
        assert isinstance(result["scan_time_ms"], (int, float))
        assert result["scan_time_ms"] >= 0

    def test_non_removable_included_without_filter(self):
        """Backward compat: non-removable devices appear when removable_only=False."""
        from core.device_scanner import scan_usb_devices
        devices = [_make_device("/dev/sda", removable=False)]
        with _mock_scan(devices):
            result = scan_usb_devices(removable_only=False)
        assert result["total"] == 1