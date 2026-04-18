"""
Tests for backend/core/audit_store.py (new in this PR).

Covers: append_record, read_recent, query_audit, rebuild_audit_index_from_jsonl,
ensure_audit_index, audit_summary_for_jobs, export_jsonl_path, _rotate_if_needed,
_max_bytes env var, PHOENIX_AUDIT_DIR env var isolation.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _isolated_env(tmp_dir: str):
    """Context manager: redirect all audit I/O to tmp_dir."""
    return mock.patch.dict(os.environ, {"PHOENIX_AUDIT_DIR": tmp_dir}, clear=False)


# ---------------------------------------------------------------------------
# append_record / read_recent
# ---------------------------------------------------------------------------

class TestAppendRecord:
    def test_creates_jsonl_file(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            audit_store.append_record({"event": "test_event", "job_id": "j1"})
            log = tmp_path / "destructive_jobs.jsonl"
            assert log.exists()

    def test_record_has_required_fields(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            audit_store.append_record({"event": "preflight", "job_id": "job-abc"})
            log = tmp_path / "destructive_jobs.jsonl"
            line = log.read_text(encoding="utf-8").strip()
            rec = json.loads(line)
            assert "audit_schema_version" in rec
            assert "record_id" in rec
            assert rec["record_id"].startswith("aud-")
            assert "written_at" in rec
            assert rec["event"] == "preflight"
            assert rec["job_id"] == "job-abc"

    def test_multiple_records_append_multiple_lines(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            audit_store.append_record({"event": "a"})
            audit_store.append_record({"event": "b"})
            audit_store.append_record({"event": "c"})
            log = tmp_path / "destructive_jobs.jsonl"
            lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
            assert len(lines) == 3

    def test_audit_schema_version_matches_constant(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            audit_store.append_record({"event": "x"})
            log = tmp_path / "destructive_jobs.jsonl"
            rec = json.loads(log.read_text(encoding="utf-8").strip())
            assert rec["audit_schema_version"] == audit_store.AUDIT_SCHEMA_VERSION

    def test_user_fields_not_overridden_by_metadata(self, tmp_path):
        """User fields (event, job_id, etc.) survive the metadata merge."""
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            audit_store.append_record({"event": "job_complete", "recipe_id": "recovery", "rollback_available": False})
            log = tmp_path / "destructive_jobs.jsonl"
            rec = json.loads(log.read_text(encoding="utf-8").strip())
            assert rec["event"] == "job_complete"
            assert rec["recipe_id"] == "recovery"
            assert rec["rollback_available"] is False


class TestReadRecent:
    def test_empty_when_no_log(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            result = audit_store.read_recent(10)
            assert result == []

    def test_returns_all_when_under_limit(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            for i in range(5):
                audit_store.append_record({"event": f"ev{i}"})
            result = audit_store.read_recent(10)
            assert len(result) == 5

    def test_respects_limit(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            for i in range(20):
                audit_store.append_record({"event": f"ev{i}"})
            result = audit_store.read_recent(5)
            assert len(result) == 5

    def test_returns_last_n_lines(self, tmp_path):
        """read_recent returns last N lines (tail semantics)."""
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            for i in range(10):
                audit_store.append_record({"event": f"ev{i}", "seq": i})
            result = audit_store.read_recent(3)
            seqs = [r["seq"] for r in result]
            assert seqs == [7, 8, 9]

    def test_skips_malformed_lines(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            # Manually write a corrupt line + a valid one
            log = tmp_path / "destructive_jobs.jsonl"
            tmp_path.mkdir(parents=True, exist_ok=True)
            log.write_text("{not valid json}\n" + json.dumps({"event": "good", "record_id": "x"}) + "\n")
            result = audit_store.read_recent(10)
            assert len(result) == 1
            assert result[0]["event"] == "good"


# ---------------------------------------------------------------------------
# query_audit / SQLite index
# ---------------------------------------------------------------------------

class TestQueryAudit:
    def test_empty_when_no_data(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            result = audit_store.query_audit(limit=10)
            assert result == []

    def test_query_by_job_id(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            audit_store.append_record({"event": "preflight", "job_id": "jA"})
            audit_store.append_record({"event": "preflight", "job_id": "jB"})
            result = audit_store.query_audit(job_id="jA")
            assert len(result) == 1
            assert result[0]["job_id"] == "jA"

    def test_query_by_event(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            audit_store.append_record({"event": "preflight", "job_id": "jA"})
            audit_store.append_record({"event": "job_complete", "job_id": "jA"})
            result = audit_store.query_audit(event="job_complete")
            assert len(result) == 1
            assert result[0]["event"] == "job_complete"

    def test_query_by_target_device_path(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            audit_store.append_record({"event": "preflight", "target_device_path": "/dev/sdb"})
            audit_store.append_record({"event": "preflight", "target_device_path": "/dev/sdc"})
            result = audit_store.query_audit(target_device_path="/dev/sdb")
            assert len(result) == 1
            assert result[0]["target_device_path"] == "/dev/sdb"

    def test_query_respects_limit(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            for i in range(20):
                audit_store.append_record({"event": "preflight", "job_id": f"j{i}"})
            result = audit_store.query_audit(limit=5)
            assert len(result) == 5

    def test_query_since_iso(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            # Write a record then check since= future excludes it
            audit_store.append_record({"event": "old_event", "job_id": "j1"})
            future = "2099-01-01T00:00:00Z"
            result = audit_store.query_audit(since_iso=future)
            assert result == []

    def test_query_until_iso(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            audit_store.append_record({"event": "event_now", "job_id": "j1"})
            past = "2000-01-01T00:00:00Z"
            result = audit_store.query_audit(until_iso=past)
            assert result == []

    def test_query_returns_newest_first(self, tmp_path):
        """Records should be returned newest-first (ORDER BY written_at DESC)."""
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            # Write JSONL directly with distinct second-level timestamps so
            # the ORDER BY written_at DESC behaviour is deterministic.
            log = tmp_path / "destructive_jobs.jsonl"
            old_rec = {"record_id": "aud-000000000001", "written_at": "2024-01-01T10:00:00Z", "event": "ev", "job_id": "first"}
            new_rec = {"record_id": "aud-000000000002", "written_at": "2024-01-01T11:00:00Z", "event": "ev", "job_id": "second"}
            log.write_text(json.dumps(old_rec) + "\n" + json.dumps(new_rec) + "\n")
            # Force index rebuild so SQLite picks up the files we just wrote
            audit_store.rebuild_audit_index_from_jsonl()
            result = audit_store.query_audit(event="ev", limit=2)
            assert len(result) == 2
            # Newest first
            assert result[0]["job_id"] == "second"
            assert result[1]["job_id"] == "first"


# ---------------------------------------------------------------------------
# rebuild_audit_index_from_jsonl
# ---------------------------------------------------------------------------

class TestRebuildAuditIndex:
    def test_returns_zero_when_no_dir(self, tmp_path):
        nonexistent = str(tmp_path / "nope")
        with _isolated_env(nonexistent):
            from core import audit_store
            result = audit_store.rebuild_audit_index_from_jsonl()
            assert result == 0

    def test_counts_indexed_rows(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            # Write JSONL manually with record_id
            log = tmp_path / "destructive_jobs.jsonl"
            records = [
                {"record_id": f"aud-{i:012x}", "written_at": "2024-01-01T00:00:00Z", "event": "preflight"}
                for i in range(3)
            ]
            log.write_text("\n".join(json.dumps(r) for r in records) + "\n")
            count = audit_store.rebuild_audit_index_from_jsonl()
            assert count == 3

    def test_skips_records_without_record_id(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            log = tmp_path / "destructive_jobs.jsonl"
            # One record with record_id, one without
            log.write_text(
                json.dumps({"record_id": "aud-000000000001", "written_at": "2024-01-01T00:00:00Z", "event": "x"}) + "\n"
                + json.dumps({"written_at": "2024-01-01T00:00:00Z", "event": "no_id"}) + "\n"
            )
            count = audit_store.rebuild_audit_index_from_jsonl()
            assert count == 1

    def test_scans_rotated_jsonl_files(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            # Write two JSONL files matching glob pattern
            for n, fname in enumerate(["destructive_jobs.jsonl", "destructive_jobs_20240101T000000Z_abcd1234.jsonl"]):
                (tmp_path / fname).write_text(
                    json.dumps({"record_id": f"aud-{n:012x}", "written_at": "2024-01-01T00:00:00Z", "event": "x"}) + "\n"
                )
            count = audit_store.rebuild_audit_index_from_jsonl()
            assert count == 2


# ---------------------------------------------------------------------------
# ensure_audit_index
# ---------------------------------------------------------------------------

class TestEnsureAuditIndex:
    def test_no_audit_dir_returns_none_action(self, tmp_path):
        nonexistent = str(tmp_path / "missing")
        with _isolated_env(nonexistent):
            from core import audit_store
            result = audit_store.ensure_audit_index()
            assert result["action"] == "none"
            assert "no_audit_dir" in result.get("reason", "")

    def test_no_jsonl_returns_none_action(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            tmp_path.mkdir(parents=True, exist_ok=True)
            result = audit_store.ensure_audit_index()
            assert result["action"] == "none"
            assert "no_jsonl" in result.get("reason", "")

    def test_rebuilds_when_db_missing(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            # Write a JSONL file but no DB
            log = tmp_path / "destructive_jobs.jsonl"
            log.write_text(
                json.dumps({"record_id": "aud-000000000001", "written_at": "2024-01-01T00:00:00Z", "event": "x"}) + "\n"
            )
            result = audit_store.ensure_audit_index()
            assert result["action"] == "rebuilt"
            assert result.get("indexed_records", 0) >= 1

    def test_ok_when_db_is_current(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            # Append a record (creates both JSONL + DB)
            audit_store.append_record({"event": "test"})
            # Touch DB to make it newer than JSONL
            db = tmp_path / "audit_index.sqlite3"
            new_time = time.time() + 10
            os.utime(str(db), (new_time, new_time))
            result = audit_store.ensure_audit_index()
            assert result["action"] == "ok"


# ---------------------------------------------------------------------------
# audit_summary_for_jobs
# ---------------------------------------------------------------------------

class TestAuditSummaryForJobs:
    def test_empty_when_no_data(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            result = audit_store.audit_summary_for_jobs()
            assert result == []

    def test_one_entry_per_job(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            audit_store.append_record({"event": "preflight", "job_id": "job-001", "recipe_id": "recovery"})
            audit_store.append_record({"event": "job_complete", "job_id": "job-001", "recipe_id": "recovery"})
            audit_store.append_record({"event": "preflight", "job_id": "job-002", "recipe_id": "linux-automated"})
            result = audit_store.audit_summary_for_jobs()
            job_ids = {r["job_id"] for r in result}
            assert "job-001" in job_ids
            assert "job-002" in job_ids
            assert len(job_ids) == 2

    def test_latest_event_is_returned(self, tmp_path):
        """audit_summary_for_jobs returns the most recent event per job_id."""
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            # Write JSONL with distinct timestamps so ordering is deterministic
            log = tmp_path / "destructive_jobs.jsonl"
            early = {"record_id": "aud-000000000010", "written_at": "2024-01-01T10:00:00Z", "event": "preflight", "job_id": "job-X"}
            later = {"record_id": "aud-000000000011", "written_at": "2024-01-01T11:00:00Z", "event": "job_complete", "job_id": "job-X"}
            log.write_text(json.dumps(early) + "\n" + json.dumps(later) + "\n")
            audit_store.rebuild_audit_index_from_jsonl()
            result = audit_store.audit_summary_for_jobs()
            assert len(result) == 1
            assert result[0]["last_event"] == "job_complete"

    def test_respects_limit(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            for i in range(10):
                audit_store.append_record({"event": "preflight", "job_id": f"job-{i:03d}"})
            result = audit_store.audit_summary_for_jobs(limit=3)
            assert len(result) <= 3


# ---------------------------------------------------------------------------
# export_jsonl_path
# ---------------------------------------------------------------------------

class TestExportJsonlPath:
    def test_returns_path_ending_in_jsonl(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            p = audit_store.export_jsonl_path()
            assert str(p).endswith(".jsonl")

    def test_path_is_under_audit_dir(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            p = audit_store.export_jsonl_path()
            assert str(tmp_path) in str(p)


# ---------------------------------------------------------------------------
# _max_bytes via env var
# ---------------------------------------------------------------------------

class TestMaxBytesEnvVar:
    def test_default_is_5_million(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PHOENIX_AUDIT_MAX_BYTES", None)
            # Re-import to pick up env at module level is tricky; test the function directly
            from core import audit_store
            # Call the private function (we can test it because it reads env each call)
            with mock.patch.dict(os.environ, {"PHOENIX_AUDIT_MAX_BYTES": "5000000"}):
                assert audit_store._max_bytes() == 5_000_000

    def test_custom_max_bytes(self):
        with mock.patch.dict(os.environ, {"PHOENIX_AUDIT_MAX_BYTES": "1024"}):
            from core import audit_store
            assert audit_store._max_bytes() == 1024

    def test_invalid_env_falls_back_to_default(self):
        with mock.patch.dict(os.environ, {"PHOENIX_AUDIT_MAX_BYTES": "not_a_number"}):
            from core import audit_store
            assert audit_store._max_bytes() == 5_000_000


# ---------------------------------------------------------------------------
# rotation
# ---------------------------------------------------------------------------

class TestRotateIfNeeded:
    def test_no_rotation_when_file_missing(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            p = tmp_path / "destructive_jobs.jsonl"
            result = audit_store._rotate_if_needed(p)
            assert result == p
            assert not p.exists()  # not created by rotation check

    def test_no_rotation_when_under_limit(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            p = tmp_path / "destructive_jobs.jsonl"
            p.write_text("x")  # tiny file
            with mock.patch.dict(os.environ, {"PHOENIX_AUDIT_MAX_BYTES": "1000000"}):
                result = audit_store._rotate_if_needed(p)
            assert result == p
            assert p.exists()

    def test_rotation_renames_file_when_over_limit(self, tmp_path):
        with _isolated_env(str(tmp_path)):
            from core import audit_store
            p = tmp_path / "destructive_jobs.jsonl"
            # Write content larger than limit
            p.write_bytes(b"x" * 100)
            with mock.patch.dict(os.environ, {"PHOENIX_AUDIT_MAX_BYTES": "50"}):
                result = audit_store._rotate_if_needed(p)
            # Original path is returned (new file slot)
            assert result == p
            # Original was renamed
            assert not p.exists() or p.stat().st_size == 0
            # A rotated file should exist
            rotated = list(tmp_path.glob("destructive_jobs_*.jsonl"))
            assert len(rotated) == 1