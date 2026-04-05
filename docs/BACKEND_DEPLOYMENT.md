# Backend-only deployment (FastAPI)

The API requires **`phoenix-safety`** on `PYTHONPATH` or installed in the environment. It does **not** need BootForge GUI (PyQt6) for safety validation.

## Minimal install (from full clone)

From the **repository root** (so relative paths resolve):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ./packages/phoenix_safety
pip install -r backend/requirements.txt
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
```

`backend/requirements.txt` references **`../packages/phoenix_safety`** (path relative to the requirements file location) for a **non-editable** install from source.

## Wheel-based install (no full monorepo on server)

On a build machine inside the repo:

```bash
./scripts/build_phoenix_safety_wheel.sh
```

Copy `packages/phoenix_safety/dist/phoenix_safety-*.whl` to the server, then:

```bash
pip install phoenix_safety-1.1.0-py3-none-any.whl
pip install fastapi "uvicorn[standard]" pydantic psutil
```

Pin versions to match your `backend/requirements.txt` for FastAPI stack.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `PHOENIX_AUDIT_DIR` | Audit JSONL + SQLite directory |
| `PHOENIX_REPO_ROOT` | Repo root for `phoenix_paths` (optional) |

## Verification

```bash
python3 -c "from phoenix_safety.safety_validator import SafetyValidator; print('ok')"
```

## Ownership

**Package:** `packages/phoenix_safety/` — version in `pyproject.toml`.  
**API safety schema:** `backend/core/safety_schema.py` (`SAFETY_SCHEMA_VERSION`) documents HTTP payload shape; keep in sync when changing token or field semantics.
