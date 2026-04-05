# Durable audit log (destructive jobs)

## Location

- Default: **`~/.phoenix_core/audit/destructive_jobs.jsonl`**
- Override: **`PHOENIX_AUDIT_DIR`** (directory; file name remains `destructive_jobs.jsonl`)
- Rotation: when file exceeds **`PHOENIX_AUDIT_MAX_BYTES`** (default `5000000`), it is renamed with a UTC timestamp and a new file is started.

## Schema (`audit_schema_version` **1.0.0**)

Each line is one JSON object. Common fields:

| Field | Meaning |
|-------|---------|
| `record_id` | Unique id for the line |
| `written_at` | UTC ISO8601 when appended |
| `event` | `preflight` \| `job_complete` \| `job_failed` \| `job_rejected` |
| `job_id` | Build job id (if assigned) |
| `recipe_id` | Recipe |
| `target_device_path` | Block device path |
| `validation` | Preflight: full safety payload subset |
| `host_capabilities` | Output of `platform_caps()` at preflight |
| `failure_stage` | Stage string when failed |
| `rollback_available` | Always **false** (honest) |
| `recovery` | Guidance text on failure |

## API

- **`GET /api/audit/jobs/recent?limit=100`** — recent records
- **`GET /api/audit/export/path`** — path to active JSONL for copy/archival

## Retention

Operators should **archive or truncate** JSONL files according to policy. The server does not delete old rotated files automatically.
