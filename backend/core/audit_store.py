"""
Durable file-backed audit log for destructive USB job preflight and outcomes.

Env:
  PHOENIX_AUDIT_DIR — directory for JSONL files (default: ~/.phoenix_core/audit)
  PHOENIX_AUDIT_MAX_BYTES — rotate when current file exceeds this (default 5_000_000)
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

AUDIT_SCHEMA_VERSION = "1.0.0"


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


def _rotate_if_needed(path: Path) -> Path:
    if not path.exists():
        return path
    if path.stat().st_size < _max_bytes():
        return path
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    rotated = path.with_name(f"destructive_jobs_{stamp}_{uuid.uuid4().hex[:8]}.jsonl")
    path.rename(rotated)
    return path


def append_record(record: Dict[str, Any]) -> None:
    """Append one JSON object as a line (JSONL)."""
    path = _rotate_if_needed(_current_log_path())
    rec = {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "record_id": f"aud-{uuid.uuid4().hex[:12]}",
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **record,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_recent(limit: int = 100) -> List[Dict[str, Any]]:
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


def export_jsonl_path() -> Path:
    return _current_log_path()
