"""
Durable audit: JSONL append-only log + SQLite index for queries.

Env:
  PHOENIX_AUDIT_DIR — directory for JSONL + SQLite (default: ~/.phoenix_core/audit)
  PHOENIX_AUDIT_MAX_BYTES — rotate active JSONL when size exceeds this (default 5_000_000)
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

AUDIT_SCHEMA_VERSION = "1.1.0"


def _audit_dir() -> Path:
    raw = os.environ.get("PHOENIX_AUDIT_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.home() / ".phoenix_core" / "audit"


def _max_bytes() -> int:
    try:
        return int(os.environ.get("PHOENIX_AUDIT_MAX_BYTES", "5000000"))
    except ValueError:
        return 5_000_000


def _current_log_path() -> Path:
    d = _audit_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / "destructive_jobs.jsonl"


def _db_path() -> Path:
    return _audit_dir() / "audit_index.sqlite3"


def _rotate_if_needed(path: Path) -> Path:
    if not path.exists():
        return path
    if path.stat().st_size < _max_bytes():
        return path
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    rotated = path.with_name(f"destructive_jobs_{stamp}_{uuid.uuid4().hex[:8]}.jsonl")
    path.rename(rotated)
    return path


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            record_id TEXT PRIMARY KEY,
            written_at TEXT NOT NULL,
            event TEXT,
            job_id TEXT,
            recipe_id TEXT,
            target_device_path TEXT,
            failure_stage TEXT,
            rollback_available INTEGER,
            payload TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_job ON audit_events(job_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_device ON audit_events(target_device_path)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_written ON audit_events(written_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_events(event)")
    conn.commit()


def _index_append(rec: Dict[str, Any]) -> None:
    """Mirror JSONL record into SQLite (best-effort)."""
    db = _db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    try:
        _ensure_schema(conn)
        payload = json.dumps(rec, ensure_ascii=False)
        conn.execute(
            """
            INSERT OR REPLACE INTO audit_events
            (record_id, written_at, event, job_id, recipe_id, target_device_path,
             failure_stage, rollback_available, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rec.get("record_id", ""),
                rec.get("written_at", ""),
                rec.get("event"),
                rec.get("job_id"),
                rec.get("recipe_id"),
                rec.get("target_device_path"),
                rec.get("failure_stage"),
                1 if rec.get("rollback_available") is True else 0,
                payload,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def append_record(record: Dict[str, Any]) -> None:
    """Append one JSON object as a line (JSONL) and index in SQLite."""
    path = _rotate_if_needed(_current_log_path())
    rec = {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "record_id": f"aud-{uuid.uuid4().hex[:12]}",
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **record,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    try:
        _index_append(rec)
    except sqlite3.Error:
        # JSONL remains source of truth; index can be rebuilt
        pass


def read_recent(limit: int = 100) -> List[Dict[str, Any]]:
    """Last N lines of active JSONL (legacy / export-friendly)."""
    path = _current_log_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out: List[Dict[str, Any]] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def query_audit(
    *,
    job_id: Optional[str] = None,
    target_device_path: Optional[str] = None,
    event: Optional[str] = None,
    since_iso: Optional[str] = None,
    until_iso: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Query indexed audit events. Returns full records (parsed payload) newest first.
    If SQLite is missing or empty, returns [] (use rebuild_audit_index_from_jsonl).
    """
    db = _db_path()
    if not db.exists():
        return []

    conn = sqlite3.connect(str(db))
    try:
        _ensure_schema(conn)
        q = "SELECT payload FROM audit_events WHERE 1=1"
        params: List[Any] = []
        if job_id:
            q += " AND job_id = ?"
            params.append(job_id)
        if target_device_path:
            q += " AND target_device_path = ?"
            params.append(target_device_path)
        if event:
            q += " AND event = ?"
            params.append(event)
        if since_iso:
            q += " AND written_at >= ?"
            params.append(since_iso)
        if until_iso:
            q += " AND written_at <= ?"
            params.append(until_iso)
        q += " ORDER BY written_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        out: List[Dict[str, Any]] = []
        for (payload,) in rows:
            try:
                out.append(json.loads(payload))
            except json.JSONDecodeError:
                continue
        return out
    finally:
        conn.close()


def rebuild_audit_index_from_jsonl() -> int:
    """
    Scan PHOENIX_AUDIT_DIR for destructive_jobs*.jsonl and repopulate SQLite.
    Returns number of rows inserted/updated.
    """
    d = _audit_dir()
    if not d.is_dir():
        return 0
    files = sorted(d.glob("destructive_jobs*.jsonl"))
    count = 0
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "record_id" not in rec:
                continue
            try:
                _index_append(rec)
                count += 1
            except sqlite3.Error:
                continue
    return count


def export_jsonl_path() -> Path:
    return _current_log_path()


def audit_summary_for_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    """
    One row per job_id (latest event) for operator dashboards.
    """
    db = _db_path()
    if not db.exists():
        return []

    conn = sqlite3.connect(str(db))
    try:
        _ensure_schema(conn)
        rows = conn.execute(
            """
            SELECT job_id, MAX(written_at) AS w
            FROM audit_events
            WHERE job_id IS NOT NULL AND job_id != ''
            GROUP BY job_id
            ORDER BY w DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for jid, _ in rows:
            evs = query_audit(job_id=jid, limit=20)
            if evs:
                latest = evs[0]
                out.append(
                    {
                        "job_id": jid,
                        "last_written_at": latest.get("written_at"),
                        "last_event": latest.get("event"),
                        "recipe_id": latest.get("recipe_id"),
                        "target_device_path": latest.get("target_device_path"),
                        "failure_stage": latest.get("failure_stage"),
                        "rollback_available": latest.get("rollback_available", False),
                    }
                )
        return out
    finally:
        conn.close()
