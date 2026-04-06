import os
import sys
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
DESKTOP = ROOT / "desktop"
BACKEND = ROOT / "backend"
if str(DESKTOP) not in sys.path:
    sys.path.insert(0, str(DESKTOP))
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_mvp_check_blocks_non_removable_and_writes_audit():
    from src.core import mvp_check

    with tempfile.TemporaryDirectory() as td:
        os.environ["PHOENIX_AUDIT_DIR"] = td
        r = mvp_check.run_headless_mvp_check(
            recipe_name="Custom Payload Deployment",
            target_device="/dev/nvme0n1",
            target_is_removable=False,
            dry_run=True,
            write_audit=True,
        )
        assert r.checklist["safety_module_imports_cleanly"] is True  # imports + engine init OK
        assert r.checklist["non_removable_target_is_blocked"] is True
        assert r.checklist["audit_record_exists"] is True

        # Confirm at least one audit record exists in canonical audit store.
        from core import audit_store

        rows = audit_store.query_audit(event="bootforge_mvp_check", limit=10)
        assert len(rows) >= 1

    os.environ.pop("PHOENIX_AUDIT_DIR", None)


def test_mvp_check_allows_removable_in_dry_run_and_writes_audit():
    from src.core import mvp_check

    with tempfile.TemporaryDirectory() as td:
        os.environ["PHOENIX_AUDIT_DIR"] = td
        r = mvp_check.run_headless_mvp_check(
            recipe_name="Custom Payload Deployment",
            target_device="/dev/sdz",
            target_is_removable=True,
            dry_run=True,
            write_audit=True,
        )
        assert r.checklist["safety_module_imports_cleanly"] is True
        # In the "removable" case, we should not prove the non-removable block path.
        assert r.checklist["non_removable_target_is_blocked"] is False
        assert r.details["selected_recipe"] == "Custom Payload Deployment"
        assert r.checklist["build_starts"] is True
        assert r.checklist["audit_record_exists"] is True

    os.environ.pop("PHOENIX_AUDIT_DIR", None)

