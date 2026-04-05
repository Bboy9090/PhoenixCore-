"""Lockdown Plus: capability blocking, removable filter, audit, shared safety."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
REPO = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_phoenix_safety_import_and_validator():
    from phoenix_safety.safety_validator import SafetyValidator, SafetyLevel

    v = SafetyValidator(SafetyLevel.STANDARD)
    dr = v.validate_device_safety("/dev/nonexistent_phoenix_test_999")
    assert dr.overall_risk.value == "blocked"


def test_scan_usb_devices_removable_only_filters():
    from core.device_scanner import scan_usb_devices

    full = scan_usb_devices(removable_only=False)
    only = scan_usb_devices(removable_only=True)
    assert only["total"] <= full["total"]
    assert only["filter"]["removable_only"] is True
    for d in only["devices"]:
        assert d.get("removable") is True


def test_audit_append_creates_jsonl_line():
    from core import audit_store

    with tempfile.TemporaryDirectory() as td:
        os.environ["PHOENIX_AUDIT_DIR"] = td
        audit_store.append_record({"event": "test", "job_id": "j1"})
        p = audit_store.export_jsonl_path()
        assert p.exists()
        line = p.read_text(encoding="utf-8").strip()
        rec = json.loads(line)
        assert rec["event"] == "test"
        assert rec["audit_schema_version"] == audit_store.AUDIT_SCHEMA_VERSION
    os.environ.pop("PHOENIX_AUDIT_DIR", None)


def test_start_build_blocked_when_native_false():
    from core.usb_builder import start_build

    with tempfile.TemporaryDirectory() as td:
        os.environ["PHOENIX_AUDIT_DIR"] = td
        with patch("core.usb_builder.require_destructive_usb_native") as m:
            from core.platform_guard import DestructiveOperationNotSupported

            m.side_effect = DestructiveOperationNotSupported("no native")
            r = start_build(
                {
                    "recipe_id": "recovery",
                    "target_device_path": "/dev/sdz",
                    "dry_run": False,
                    "confirmation_token": "PHX-test",
                }
            )
            assert r["status"] == "failed"
            assert r["job_id"] == ""
    os.environ.pop("PHOENIX_AUDIT_DIR", None)


def test_safety_schema_version_constant():
    from core import safety_schema

    assert safety_schema.SAFETY_SCHEMA_VERSION == "1.0.0"
