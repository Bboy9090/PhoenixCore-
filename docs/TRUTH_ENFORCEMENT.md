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

## pytest

`tests/test_lockdown_plus.py` covers:

- `start_build` rejects non-dry when `destructive_usb_write_native` is false (mocked).
- `scan_usb_devices(removable_only=True)` filters.
- Audit `append_record` creates a JSONL line.
- `phoenix_safety` import / `SafetyValidator` smoke.

CI runs the script after **`pip install -r requirements.txt`** (installs editable `phoenix_safety`).
