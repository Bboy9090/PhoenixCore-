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
| `requirements.txt` (root) | **Canonical** | BootForge + web deps + `./packages/phoenix_safety` |
| `packages/phoenix_safety/` | **Canonical** | Shared `SafetyValidator` — single implementation |
| `backend/requirements.txt` | **Canonical** | FastAPI runtime + `../packages/phoenix_safety` |
| `experimental/root-app-template/` | **Experimental / template** | Expo + pnpm + tRPC + `server/` (includes deprecated Flask `server/api.py`) |
| `experimental/` | **Isolation** | Pointer + `root-app-template/README.md` |
| `CONFIG_ROOT_TEMPLATE.md` | **Tombstone** | Template moved off root |
| `ROOT_APP_TEMPLATE.redirect.md` | **Redirect** | How to run the template |
| `mobile/` | **Deprecated** | Use `phoenix-core-mobile/` |
| `legacy/` | **Archive** | No feature work; reference only |
| `legacy/bootable_usb/BootForge/` | **Archive (duplicate)** | Do not sync with `desktop/` |

## Migration (final cleanup)

- **Removed from repo root:** `package.json`, `pnpm-lock.yaml`, `app/`, `server/`, and related Expo/tRPC files → **`experimental/root-app-template/`**.
- **If you had scripts** assuming root `pnpm dev`, run from **`experimental/root-app-template/`** instead.
- **Legacy Flask** `server/api.py` now only exists under the template tree; **canonical API** is **`backend/main.py`**.
