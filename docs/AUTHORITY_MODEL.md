# Authority model (enforced)

This document is **normative** for Phoenix Core. Code and APIs should align with it.

## Hierarchy (highest authority first)

### 1. BootForge desktop — final execution authority (local destructive)

- **Path:** `desktop/` — `python3 main.py` → PyQt6 + `desktop/src/`.
- **Authority:** The **only** supported path where the operator may perform **full** destructive local workflows (USB imaging, recovery actions) with the **richest** safety UX and platform integrations.
- **Rule:** If FastAPI and BootForge disagree, **BootForge wins** for what is *allowed in production on a given machine*; FastAPI must not claim capabilities the host OS cannot deliver.

### 2. FastAPI backend — orchestration and remote API

- **Path:** `backend/main.py`.
- **Authority:** **Orchestration, validation surface, and remote/mobile control** against the **host** that runs the server.
- **Rule:** Destructive jobs are **blocked** unless:
  - host **platform capabilities** allow native write (`destructive_usb_write_native`), **or** `dry_run=true`;
  - **canonical safety schema** passes (delegates to **`phoenix_safety`** `SafetyValidator` via `backend/core/safety_bridge.py`);
  - valid **confirmation token** from `/api/safety-check`.
- **Not authoritative for:** Implies **no disk rollback** after partial writes — see `docs/SAFETY_MODEL.md`.

### 3. Rust engine — primitive authority (explicit wiring only)

- **Path:** `crates/`, `apps/cli/` (`phoenix-cli`).
- **Authority:** **Primitives and contracts** (`docs/core-contracts.md`) **only where invoked** by tooling or future integration.
- **Rule:** Rust is **not** the single runtime for USB builds today; do not document it as replacing BootForge/FastAPI until wired end-to-end.

## Non-authoritative (do not treat as product core)

| Area | Status |
|------|--------|
| `website/web_server.py` | Marketing / demo |
| `experimental/root-app-template/server/api.py` (Flask) | **Deprecated** — use `backend/`; kept only inside template tree |
| `experimental/root-app-template/` | **Experimental / template** — not Phoenix USB product |
| `legacy/` | **Archive** |
| `mobile/` (root RN tree) | **Deprecated** — use `phoenix-core-mobile/` |

See **`docs/REPO_STATUS_MAP.md`**.
