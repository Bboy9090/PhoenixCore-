# Safety model (lockdown +)

## Canonical authority

**Single implementation:** `packages/phoenix_safety/phoenix_safety/safety_validator.py` (install **`pip install -e packages/phoenix_safety`**, included from root `requirements.txt`).

- **BootForge** imports it through **`desktop/src/core/safety_validator.py`** (thin re-export).
- **FastAPI** imports it through **`backend/core/safety_bridge.py`** → `phoenix_safety.safety_validator`.

## API response schema

`POST /api/safety-check` returns **`backend/core/safety_schema.py`** payload:

- `schema_version` — `"1.0.0"`
- `safe_to_proceed` — whether a confirmation token may be issued
- `risk_level` — `low` | `medium` | `high` | `critical`
- `warnings`, `errors`
- `confirmation_token` — present only if `safe_to_proceed`
- `device_info` — scanner snapshot
- `device_risk` — `SafetyValidator` output (paths, removable, `overall_risk`, `risk_factors`, …)
- `validator_source` — `phoenix_safety`
- `capability_notes` — e.g. missing native write

## Policy highlights

1. **Non-removable targets:** USB creation via API **requires** OS-reported `removable` on the scanned device (`require_removable=True` default). Internal disks are **rejected** for token issuance.
2. **Validator BLOCKED / DANGEROUS:** No token; operator must use **BootForge desktop** or fix the target.
3. **Package missing:** No token until **`phoenix-safety`** is installed (`pip install -e packages/phoenix_safety`).

## Rollback

**There is no automatic disk rollback** after partial `dd`/format. Jobs report `rollback_available: false` and log explicit failure stages. See **`docs/AUTHORITY_MODEL.md`**.
