# phoenix-safety

**Canonical** device and patch safety validation for Phoenix Core.

- Consumed by **BootForge** (`desktop/`) via `src.core.safety_validator` shim.
- Consumed by **FastAPI** (`backend/`) via `phoenix_safety.safety_validator`.

Install (editable, from repo root):

```bash
pip install -e packages/phoenix_safety
```

Or rely on root `requirements.txt` which includes `-e packages/phoenix_safety`.
