"""Stabilization: audit index, phoenix_safety path install assumption."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_audit_append_indexes_sqlite():
    from core import audit_store

    with tempfile.TemporaryDirectory() as td:
        os.environ["PHOENIX_AUDIT_DIR"] = td
        audit_store.append_record({"event": "test_index", "job_id": "job-abc"})
        db = Path(td) / "audit_index.sqlite3"
        assert db.exists()
        rows = audit_store.query_audit(job_id="job-abc", limit=5)
        assert len(rows) == 1
        assert rows[0]["event"] == "test_index"
    os.environ.pop("PHOENIX_AUDIT_DIR", None)


def test_rebuild_index_from_jsonl():
    from core import audit_store

    with tempfile.TemporaryDirectory() as td:
        os.environ["PHOENIX_AUDIT_DIR"] = td
        p = Path(td) / "destructive_jobs.jsonl"
        rec = {
            "audit_schema_version": "1.1.0",
            "record_id": "aud-manual1",
            "written_at": "2026-01-01T00:00:00Z",
            "event": "job_rejected",
            "job_id": "",
            "recipe_id": "recovery",
        }
        p.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        n = audit_store.rebuild_audit_index_from_jsonl()
        assert n >= 1
        rows = audit_store.query_audit(event="job_rejected", limit=10)
        assert any(r.get("record_id") == "aud-manual1" for r in rows)
    os.environ.pop("PHOENIX_AUDIT_DIR", None)


def test_start_build_rejection_writes_audit():
    from core.usb_builder import start_build

    with tempfile.TemporaryDirectory() as td:
        os.environ["PHOENIX_AUDIT_DIR"] = td
        with patch("core.usb_builder.require_destructive_usb_native") as m:
            from core.platform_guard import DestructiveOperationNotSupported

            m.side_effect = DestructiveOperationNotSupported("blocked")
            start_build(
                {
                    "recipe_id": "recovery",
                    "target_device_path": "/dev/null",
                    "dry_run": False,
                    "confirmation_token": "PHX-x",
                }
            )
        from core import audit_store

        rows = audit_store.query_audit(event="job_rejected", limit=5)
        assert any(r.get("reason") == "destructive_usb_write_native_false" for r in rows)
    os.environ.pop("PHOENIX_AUDIT_DIR", None)
