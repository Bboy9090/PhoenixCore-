"""Tests for BootForge MVP headless check harness.

Scope: validates run_headless_mvp_check() block/allow logic using fake
DiskManager + SafetyValidator stubs inside mvp_check itself.

audit_store is NOT tested here — that requires backend/core/audit_store
which lives in Phase 3 (audit hardening). write_audit=False throughout.
"""

import os
import sys
from pathlib import Path

# Add desktop/ to path so 'src.core.*' resolves — matches project test pattern.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "desktop"))


def test_mvp_check_blocks_non_removable():
    """Non-removable target must be classified as blocked and set the flag."""
    from src.core import mvp_check

    r = mvp_check.run_headless_mvp_check(
        recipe_name="Custom Payload Deployment",
        target_device="/dev/nvme0n1",
        target_is_removable=False,
        dry_run=True,
        write_audit=False,
    )
    assert r.checklist["safety_module_imports_cleanly"] is True
    assert r.checklist["non_removable_target_is_blocked"] is True
    # Without audit_store, audit_record_exists is False — that is expected and honest.
    assert r.checklist["audit_record_exists"] is False


def test_mvp_check_allows_removable_dry_run():
    """Removable target should pass safety gate and reach build_starts=True."""
    from src.core import mvp_check

    r = mvp_check.run_headless_mvp_check(
        recipe_name="Custom Payload Deployment",
        target_device="/dev/sdz",
        target_is_removable=True,
        dry_run=True,
        write_audit=False,
    )
    assert r.checklist["safety_module_imports_cleanly"] is True
    assert r.checklist["non_removable_target_is_blocked"] is False
    assert r.details["selected_recipe"] == "Custom Payload Deployment"
    assert r.checklist["build_starts"] is True
    assert r.checklist["audit_record_exists"] is False


def test_mvp_check_result_serializable():
    """to_dict() must return a plain dict with no unserializable types."""
    import json
    from src.core import mvp_check

    r = mvp_check.run_headless_mvp_check(
        recipe_name="Custom Payload Deployment",
        target_device="/dev/sdz",
        target_is_removable=True,
        dry_run=True,
        write_audit=False,
    )
    d = r.to_dict()
    # Must be JSON-serializable (no Enum values leaking out).
    json.dumps(d)
    assert isinstance(d["ok"], bool)
    assert isinstance(d["checklist"], dict)
    assert isinstance(d["details"], dict)
