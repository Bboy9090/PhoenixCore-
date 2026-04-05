# phoenix-safety

**Canonical** device and patch safety validation for Phoenix Core (single implementation; BootForge and FastAPI both depend on this package).

**Version:** see `pyproject.toml` (`project.version`). Bump **minor** for compatible behavior/schema tweaks; **major** for breaking API changes (coordinate with `SAFETY_SCHEMA_VERSION` in `backend/core/safety_schema.py`).

## Install options

### From monorepo directory (no editable; recommended for backend-only hosts)

From repository root:

```bash
pip install ./packages/phoenix_safety
# In requirements.txt use: ./packages/phoenix_safety
```

Or from `backend/` using the requirements file (paths are relative to `backend/requirements.txt`):

```bash
pip install -r backend/requirements.txt
```

### Editable (developers)

```bash
pip install -e ./packages/phoenix_safety
```

### Wheel (CI, air-gapped, internal mirror)

```bash
./scripts/build_phoenix_safety_wheel.sh
pip install dist/phoenix_safety-*.whl
```

### Internal index

Build the wheel, upload to your private PyPI, then:

```bash
pip install "phoenix-safety==1.1.0" --index-url https://your-index/simple/
```

See **`docs/BACKEND_DEPLOYMENT.md`** for backend-only deployment.
