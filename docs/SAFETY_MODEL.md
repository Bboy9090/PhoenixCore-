# Safety model (lockdown)

## Canonical authority

**BootForge `SafetyValidator`** (`desktop/src/core/safety_validator.py`) is the **canonical safety authority** for device-target decisions when its code is importable from the API process.

The FastAPI layer loads it via **`backend/core/safety_bridge.py`** (adds `desktop/` to `sys.path` and imports `src.core.safety_validator`).

## API response schema

`POST /api/safety-check` returns **`backend/core/safety_schema.py`** payload:

- `schema_version` — `"1.0.0"`
- `safe_to_proceed` — whether a confirmation token may be issued
- `risk_level` — `low` | `medium` | `high` | `critical`
- `warnings`, `errors`
- `confirmation_token` — present only if `safe_to_proceed`
- `device_info` — scanner snapshot
- `device_risk` — `SafetyValidator` output (paths, removable, `overall_risk`, `risk_factors`, …)
- `validator_source` — `bootforge_safety_validator` when loaded
- `capability_notes` — e.g. missing native write

## Policy highlights

1. **Non-removable targets:** USB creation via API **requires** OS-reported `removable` on the scanned device (`require_removable=True` default). Internal disks are **rejected** for token issuance.
2. **Validator BLOCKED / DANGEROUS:** No token; operator must use **BootForge desktop** or fix the target.
3. **Validator unavailable:** No token until `desktop/` deps (e.g. PyQt6 for imports that pull Qt) are installed — install from repo root `requirements.txt` for full parity.

## Rollback

**There is no automatic disk rollback** after partial `dd`/format. Jobs report `rollback_available: false` and log explicit failure stages. See **`docs/AUTHORITY_MODEL.md`**.
