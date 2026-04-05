# Repository path status map (lockdown)

Hard labels for humans and tooling. **Canonical** = ship and patch here first.

| Path | Status | Notes |
|------|--------|------|
| `desktop/` | **Canonical** | BootForge; final local execution authority |
| `backend/` | **Canonical** | FastAPI; remote/mobile orchestration |
| `crates/`, `apps/cli/` | **Canonical (primitives)** | Rust; use where explicitly wired |
| `phoenix-core-mobile/` | **Canonical** | Expo app for FastAPI |
| `tests/` | **Canonical** | Python tests |
| `docs/` | **Canonical** | Architecture + audits |
| `website/` | **Canonical (non-core)** | Flask demo / marketing |
| `main.py` (root) | **Canonical** | Entry → `desktop/main.py` |
| `requirements.txt` (root) | **Canonical** | BootForge + web deps |
| `backend/requirements.txt` | **Canonical** | FastAPI runtime |
| `server/api.py` (Flask) | **Deprecated** | Use `backend/`; path fixed to `desktop/src` |
| `server/_core/`, root `package.json` | **Experimental / template** | Separate Expo+Node stack; not Phoenix USB core |
| `mobile/` | **Deprecated** | Use `phoenix-core-mobile/` |
| `legacy/` | **Archive** | No feature work; reference only |
| `legacy/bootable_usb/BootForge/` | **Archive (duplicate)** | Do not sync with `desktop/` |
