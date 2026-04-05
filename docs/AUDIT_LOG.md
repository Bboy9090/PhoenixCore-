# Durable audit log (destructive jobs)

## Storage model

1. **JSONL** — append-only source of truth: **`destructive_jobs.jsonl`** (and rotated siblings).
2. **SQLite index** — **`audit_index.sqlite3`** in the same directory for **`GET /api/audit/query`** and summaries.

**Auto-recovery:** On API **startup** (`lifespan`) and before **indexed** reads (`query_audit`, `audit_summary_for_jobs`), **`ensure_audit_index()`** runs: if any **`destructive_jobs*.jsonl`** is newer than the DB, or the DB is missing/corrupt, the index is **rebuilt from JSONL**. You can still call **`POST /api/audit/rebuild-index`** manually.

## Location

- Default: **`~/.phoenix_core/audit/`**
- Override: **`PHOENIX_AUDIT_DIR`**
- Rotation: when active JSONL exceeds **`PHOENIX_AUDIT_MAX_BYTES`** (default `5000000`), it is renamed and a new file is started.

## Schema (`audit_schema_version`)

Current line schema version: **1.1.0** (adds index alongside JSONL; fields unchanged from 1.0.0).

| Field | Meaning |
|-------|---------|
| `record_id` | Unique id for the line |
| `written_at` | UTC ISO8601 when appended |
| `event` | `preflight` \| `job_complete` \| `job_failed` \| `job_rejected` \| `test` |
| `job_id` | Build job id (if assigned) |
| `recipe_id` | Recipe |
| `target_device_path` | Block device path |
| `validation` | Preflight: safety subset |
| `host_capabilities` | `platform_caps()` at preflight |
| `failure_stage` | Stage string when failed |
| `rollback_available` | Always **false** for honesty |
| `recovery` | Guidance on failure |
| `reason` | For `job_rejected` |

## API (operator review)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/audit/jobs/recent?limit=` | Tail of **active** JSONL only |
| `GET /api/audit/query?job_id=&target_device_path=&event=&since=&until=&limit=` | Indexed query |
| `GET /api/audit/jobs/summary?limit=` | Latest row per **job_id** |
| `POST /api/audit/rebuild-index` | Rebuild SQLite from JSONL |
| `GET /api/audit/export/path` | Paths to JSONL + SQLite |

### Examples

```bash
curl -s "http://127.0.0.1:8000/api/audit/jobs/summary?limit=20"
curl -s "http://127.0.0.1:8000/api/audit/query?job_id=<uuid>&limit=50"
```

## Retention

Archive rotated JSONL and optionally the SQLite file per policy. Phoenix does not auto-delete rotated JSONL.

## Mobile / remote operators

Use the same HTTP endpoints against the **host** running the API. See **`phoenix-core-mobile/README.md`** (audit helpers on the client).
