# Automated truth enforcement

## Script

From repo root:

```bash
bash scripts/ci_truth_enforcement.sh
```

## What it checks

1. **`SAFETY_SCHEMA_VERSION`** in `backend/core/safety_schema.py` remains **`1.0.0`** unless intentionally bumped (with docs).
2. **`docs/CAPABILITY_MATRIX.md`** mentions **`destructive_usb_write_native`** (aligned with `GET /api/health`).
3. **Canonical Python trees** (`desktop/`, `backend/`, `packages/`, `tests/`) do not reference **`legacy/bootable_usb`** in imports/paths.
4. No **`mobile.`** Python imports in those trees.
5. **`packages/phoenix_safety/phoenix_safety/safety_validator.py`** exists.
6. **`python3 -c "from phoenix_safety.safety_validator import SafetyValidator"`** succeeds (requires **`pip install -r requirements.txt`** first in CI).
7. **`python3 scripts/check_import_boundaries.py`** — AST scan: no imports of **`legacy`**, **`experimental`**, or **`server`** from **`backend/`**, **`desktop/`**, **`packages/`**, **`tests/`** (see **`docs/IMPORT_BOUNDARIES.md`**).

## pytest

- `tests/test_lockdown_plus.py` — capability block, removable filter, schema, audit JSONL.
- `tests/test_stabilization.py` — SQLite index, rebuild from JSONL, rejection audit row.

CI runs **`pip install -r requirements.txt`** then **`pytest`** then **`scripts/ci_truth_enforcement.sh`**.
