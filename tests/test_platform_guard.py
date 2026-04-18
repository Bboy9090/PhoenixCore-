"""
Tests for backend/core/platform_guard.py (new in this PR).

Covers: DestructiveOperationNotSupported, require_destructive_usb_native(),
explain_block().
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


class TestDestructiveOperationNotSupported:
    def test_is_runtime_error_subclass(self):
        from core.platform_guard import DestructiveOperationNotSupported
        assert issubclass(DestructiveOperationNotSupported, RuntimeError)

    def test_can_be_raised_and_caught(self):
        from core.platform_guard import DestructiveOperationNotSupported
        with pytest.raises(DestructiveOperationNotSupported) as exc_info:
            raise DestructiveOperationNotSupported("test message")
        assert "test message" in str(exc_info.value)

    def test_is_also_exception(self):
        from core.platform_guard import DestructiveOperationNotSupported
        assert issubclass(DestructiveOperationNotSupported, Exception)


class TestRequireDestructiveUsbNative:
    def test_dry_run_always_passes(self):
        """dry_run=True skips platform check entirely."""
        from core.platform_guard import require_destructive_usb_native
        # Even with native=False, dry_run=True should not raise
        with mock.patch("core.platform_guard.destructive_usb_write_native", return_value=False):
            # Should not raise
            require_destructive_usb_native(dry_run=True)

    def test_raises_when_native_unavailable_and_not_dry_run(self):
        from core.platform_guard import require_destructive_usb_native, DestructiveOperationNotSupported
        with mock.patch("core.platform_guard.destructive_usb_write_native", return_value=False):
            with pytest.raises(DestructiveOperationNotSupported):
                require_destructive_usb_native(dry_run=False)

    def test_passes_when_native_available_and_not_dry_run(self):
        from core.platform_guard import require_destructive_usb_native
        with mock.patch("core.platform_guard.destructive_usb_write_native", return_value=True):
            # Should not raise
            require_destructive_usb_native(dry_run=False)

    def test_error_message_mentions_dd_and_parted(self):
        """Error message should guide the user to install dd/parted or use dry_run."""
        from core.platform_guard import require_destructive_usb_native, DestructiveOperationNotSupported
        with mock.patch("core.platform_guard.destructive_usb_write_native", return_value=False):
            with pytest.raises(DestructiveOperationNotSupported) as exc_info:
                require_destructive_usb_native(dry_run=False)
        msg = str(exc_info.value)
        assert "dd" in msg or "parted" in msg or "dry_run" in msg

    def test_dry_run_true_with_native_available_still_passes(self):
        """When native is available, dry_run=True is also fine."""
        from core.platform_guard import require_destructive_usb_native
        with mock.patch("core.platform_guard.destructive_usb_write_native", return_value=True):
            require_destructive_usb_native(dry_run=True)

    def test_only_dry_run_keyword_allowed(self):
        """dry_run must be a keyword argument."""
        from core.platform_guard import require_destructive_usb_native
        with pytest.raises(TypeError):
            require_destructive_usb_native(True)  # positional arg not allowed


class TestExplainBlock:
    def test_returns_string(self):
        from core.platform_guard import explain_block
        result = explain_block()
        assert isinstance(result, str)

    def test_mentions_destructive_usb_write_native(self):
        from core.platform_guard import explain_block
        result = explain_block()
        assert "destructive_usb_write_native" in result

    def test_mentions_health_endpoint(self):
        from core.platform_guard import explain_block
        result = explain_block()
        assert "/api/health" in result or "health" in result.lower()

    def test_non_empty(self):
        from core.platform_guard import explain_block
        assert len(explain_block()) > 10