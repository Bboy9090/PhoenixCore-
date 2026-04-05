# Canonical runtime paths (operator-facing)

Use this when deciding **which command to run** or **which HTTP server is authoritative**.

**Normative authority hierarchy:** [`AUTHORITY_MODEL.md`](AUTHORITY_MODEL.md).

## Primary paths

1. **BootForge (desktop GUI/CLI)** — `python3 main.py` from repo root (delegates to `desktop/main.py`).  
   Full wizard, `desktop/src/` engine, richest safety and imaging integration on the **local machine**.

2. **Phoenix Core API (FastAPI)** — from repo root: install `backend/requirements.txt`, then  
   `cd backend && uvicorn main:app --host 0.0.0.0 --port 8000`.  
   REST for devices, recipes, safety check, build jobs. **Required** for `phoenix-core-mobile/` USB flows. Runs on the **host that has the USB drive**.

3. **Rust CLI** — `cargo build` / run `phoenix-cli` for the crates listed in `AGENTS.md`.  
   Low-level workflows and contracts; **not** automatically invoked by BootForge or FastAPI today.

## Non-authoritative / other products

- **`website/web_server.py`** — marketing / demo Flask (port 5000 typical).
- **`server/api.py`** — legacy Flask API; **deprecated** in favor of `backend/`.
- **Root `package.json` + `server/_core/`** — separate Expo/Node template; **not** `phoenix-core-mobile/`.
- **`legacy/`** — quarantined reference copies.

See **`docs/AUDIT_SECOND_PASS_STRUCTURE.md`** for drift, build truth, and debt.
