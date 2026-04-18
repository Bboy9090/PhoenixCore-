"""
Tests for backend/core/platform_caps.py (new in this PR).

Covers: _executable_available(), destructive_usb_write_native(), platform_caps().
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest import mock

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


class TestExecutableAvailable:
    def test_finds_existing_executable_via_shutil_which(self):
        from core.platform_caps import _executable_available
        with mock.patch("shutil.which", return_value="/usr/bin/ls"):
            assert _executable_available("ls") is True

    def test_returns_false_when_not_found_anywhere(self):
        from core.platform_caps import _executable_available
        with mock.patch("shutil.which", return_value=None):
            with mock.patch("os.path.isfile", return_value=False):
                assert _executable_available("nonexistent_binary_xyz") is False

    def test_falls_back_to_manual_path_check(self):
        """shutil.which returns None but binary exists at /usr/bin/<name>."""
        from core.platform_caps import _executable_available

        def fake_isfile(p):
            return p == "/usr/bin/mybin"

        def fake_access(p, mode):
            return p == "/usr/bin/mybin"

        with mock.patch("shutil.which", return_value=None):
            with mock.patch("os.path.isfile", side_effect=fake_isfile):
                with mock.patch("os.access", side_effect=fake_access):
                    assert _executable_available("mybin") is True

    def test_file_not_executable_returns_false(self):
        """File exists but is not executable."""
        from core.platform_caps import _executable_available

        with mock.patch("shutil.which", return_value=None):
            with mock.patch("os.path.isfile", return_value=True):
                with mock.patch("os.access", return_value=False):
                    assert _executable_available("notexec") is False


class TestDestructiveUsbWriteNative:
    def test_false_on_non_linux(self):
        from core import platform_caps as pc
        with mock.patch("platform.system", return_value="Darwin"):
            assert pc.destructive_usb_write_native() is False

    def test_false_on_windows(self):
        from core import platform_caps as pc
        with mock.patch("platform.system", return_value="Windows"):
            assert pc.destructive_usb_write_native() is False

    def test_false_on_linux_when_dd_missing(self):
        from core import platform_caps as pc
        with mock.patch("platform.system", return_value="Linux"):
            with mock.patch("core.platform_caps._executable_available", side_effect=lambda n: n != "dd"):
                assert pc.destructive_usb_write_native() is False

    def test_false_on_linux_when_parted_missing(self):
        from core import platform_caps as pc
        with mock.patch("platform.system", return_value="Linux"):
            with mock.patch("core.platform_caps._executable_available", side_effect=lambda n: n != "parted"):
                assert pc.destructive_usb_write_native() is False

    def test_true_on_linux_with_dd_and_parted(self):
        from core import platform_caps as pc
        with mock.patch("platform.system", return_value="Linux"):
            with mock.patch("core.platform_caps._executable_available", return_value=True):
                assert pc.destructive_usb_write_native() is True

    def test_case_insensitive_linux_check(self):
        """platform.system() may return 'linux' (lowercase) on some systems."""
        from core import platform_caps as pc
        with mock.patch("platform.system", return_value="linux"):
            with mock.patch("core.platform_caps._executable_available", return_value=True):
                assert pc.destructive_usb_write_native() is True


class TestPlatformCaps:
    def test_returns_dict_with_required_keys(self):
        from core.platform_caps import platform_caps
        result = platform_caps()
        assert isinstance(result, dict)
        assert "host_os" in result
        assert "destructive_usb_write_native" in result
        assert "notes" in result

    def test_host_os_is_lowercase(self):
        from core.platform_caps import platform_caps
        with mock.patch("platform.system", return_value="Linux"):
            result = platform_caps()
        assert result["host_os"] == "linux"

    def test_destructive_flag_matches_helper(self):
        from core import platform_caps as pc
        with mock.patch("platform.system", return_value="Linux"):
            with mock.patch("core.platform_caps._executable_available", return_value=True):
                result = pc.platform_caps()
        assert result["destructive_usb_write_native"] is True

    def test_notes_field_is_string(self):
        from core.platform_caps import platform_caps
        result = platform_caps()
        assert isinstance(result["notes"], str)
        assert len(result["notes"]) > 0

    def test_non_linux_destructive_is_false(self):
        from core import platform_caps as pc
        with mock.patch("platform.system", return_value="Darwin"):
            result = pc.platform_caps()
        assert result["destructive_usb_write_native"] is False
        assert result["host_os"] == "darwin"