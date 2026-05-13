# Phoenix Agent Audit Model

All system-altering events must be recorded in the immutable audit log.

## Audit Entry Schema
Each entry must contain:
- `timestamp`: ISO 8601 UTC.
- `actor_id`: Entity that performed the action.
- `device_identity`: The hardware target.
- `action`: The canonical operation name (e.g., `disk.format`).
- `outcome`: `success` | `failed` | `aborted`.
- `evidence_hash`: SHA-256 hash of the `ReportBundle`.
- `details`: JSON blob containing parameters and non-sensitive results.

## Retention Policy
Audit logs are stored in the database but must be periodically exported to signed `ReportBundles` for long-term archiving.
- **Integrity**: Audit logs are read-only to the standard UI. Modification requires `owner` role via the direct database bridge (Rust-gated).
