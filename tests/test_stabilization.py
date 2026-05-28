"""Stabilization: audit JSONL + SQLite index integrity tests.

Scope: backend/core/audit_store only. All tests use tempfile isolation and
PHOENIX_AUDIT_DIR env so they never touch the real ~/.phoenix_core/audit dir.

Out of scope here (deferred — require backend chain not on this branch):
- core.usb_builder.start_build
- core.platform_guard.DestructiveOperationNotSupported
- phoenix_safety package
- core.device_scanner / core.safety_schema
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


# ---------------------------------------------------------------------------
# Audit store: JSONL append + SQLite index
# ---------------------------------------------------------------------------

def test_audit_append_indexes_sqlite():
    """append_record() must write JSONL line AND create indexed SQLite entry."""
    from core import audit_store

    with tempfile.TemporaryDirectory() as td:
        os.environ["PHOENIX_AUDIT_DIR"] = td
        audit_store.append_record({"event": "test_index", "job_id": "job-abc"})
        db = Path(td) / "audit_index.sqlite3"
        assert db.exists(), "SQLite index must be created on first append"
        # WAL is the default journal mode for concurrent read safety.
        assert audit_store._sqlite_journal_mode() == "wal"
        rows = audit_store.query_audit(job_id="job-abc", limit=5)
        assert len(rows) == 1
        assert rows[0]["event"] == "test_index"
    os.environ.pop("PHOENIX_AUDIT_DIR", None)


def test_audit_append_creates_jsonl_line():
    """Each append must produce a well-formed JSONL record with schema version."""
    from core import audit_store

    with tempfile.TemporaryDirectory() as td:
        os.environ["PHOENIX_AUDIT_DIR"] = td
        audit_store.append_record({"event": "test_jsonl", "job_id": "j1"})
        p = audit_store.export_jsonl_path()
        assert p.exists()
        line = p.read_text(encoding="utf-8").strip()
        rec = json.loads(line)
        assert rec["event"] == "test_jsonl"
        assert rec["audit_schema_version"] == audit_store.AUDIT_SCHEMA_VERSION
        assert "record_id" in rec
        assert "written_at" in rec
    os.environ.pop("PHOENIX_AUDIT_DIR", None)


def test_rebuild_index_from_jsonl():
    """rebuild_audit_index_from_jsonl() must ingest manually written JSONL records."""
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


def test_query_audit_auto_rebuilds_from_jsonl_only():
    """JSONL without prior SQLite: query_audit must trigger ensure_audit_index."""
    from core import audit_store

    with tempfile.TemporaryDirectory() as td:
        os.environ["PHOENIX_AUDIT_DIR"] = td
        p = Path(td) / "destructive_jobs.jsonl"
        rec = {
            "audit_schema_version": "1.1.0",
            "record_id": "aud-onlyjsonl",
            "written_at": "2026-02-01T12:00:00Z",
            "event": "preflight",
            "job_id": "job-xyz",
            "recipe_id": "recovery",
            "target_device_path": "/dev/sdz",
        }
        p.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        assert not (Path(td) / "audit_index.sqlite3").exists()
        rows = audit_store.query_audit(job_id="job-xyz", limit=5)
        assert len(rows) == 1
        assert rows[0]["record_id"] == "aud-onlyjsonl"
    os.environ.pop("PHOENIX_AUDIT_DIR", None)


def test_ensure_audit_index_rebuilds_when_jsonl_newer_than_db():
    """ensure_audit_index() must detect stale SQLite and rebuild from JSONL."""
    from core import audit_store

    with tempfile.TemporaryDirectory() as td:
        os.environ["PHOENIX_AUDIT_DIR"] = td
        d = Path(td)
        p = d / "destructive_jobs.jsonl"
        p.write_text(
            json.dumps({
                "audit_schema_version": "1.1.0",
                "record_id": "aud-old",
                "written_at": "2026-01-01T00:00:00Z",
                "event": "preflight",
                "job_id": "j1",
            }) + "\n",
            encoding="utf-8",
        )
        audit_store.rebuild_audit_index_from_jsonl()
        db = d / "audit_index.sqlite3"
        assert db.exists()
        # Make DB appear older than JSONL
        old = db.stat().st_mtime - 10
        os.utime(db, (old, old))
        p.write_text(
            p.read_text(encoding="utf-8") +
            json.dumps({
                "audit_schema_version": "1.1.0",
                "record_id": "aud-newer",
                "written_at": "2026-03-01T00:00:00Z",
                "event": "job_failed",
                "job_id": "j2",
            }) + "\n",
            encoding="utf-8",
        )
        info = audit_store.ensure_audit_index()
        assert info.get("action") == "rebuilt"
        rows = audit_store.query_audit(job_id="j2", limit=5)
        assert len(rows) >= 1
    os.environ.pop("PHOENIX_AUDIT_DIR", None)


# ---------------------------------------------------------------------------
# Skipped: backend chain not yet recovered on this branch
# ---------------------------------------------------------------------------

@pytest.mark.skip(
    reason="Requires backend/core/usb_builder + core/platform_guard chain — "
    "deferred until backend layer is recovered (Phase 3 extension)."
)
def test_start_build_rejection_writes_audit():
    """Placeholder: start_build() rejection must emit job_rejected audit record."""
    pass
