# Phoenix Core (Unified)

Phoenix Core is a professional, cross-platform OS deployment system. This repository contains the **Rust core engine**, the **BootForge desktop app** (PyQt6), **HTTP APIs**, **mobile clients**, and **legacy reference** trees in one modular layout.

**Authoritative architecture and integration audit:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/AUDIT_PLATFORM_INTEGRATION.md`](docs/AUDIT_PLATFORM_INTEGRATION.md), [`docs/AUDIT_SECOND_PASS_STRUCTURE.md`](docs/AUDIT_SECOND_PASS_STRUCTURE.md).

**Authority hierarchy (enforced):** [`docs/AUTHORITY_MODEL.md`](docs/AUTHORITY_MODEL.md) · **Safety:** [`docs/SAFETY_MODEL.md`](docs/SAFETY_MODEL.md) · **Capabilities:** [`docs/CAPABILITY_MATRIX.md`](docs/CAPABILITY_MATRIX.md) · **Path status:** [`docs/REPO_STATUS_MAP.md`](docs/REPO_STATUS_MAP.md) · **Lockdown Plus:** [`docs/LOCKDOWN_PLUS_REPORT.md`](docs/LOCKDOWN_PLUS_REPORT.md) · **Stabilization:** [`docs/STABILIZATION_PHASE_REPORT.md`](docs/STABILIZATION_PHASE_REPORT.md) · **Backend deploy:** [`docs/BACKEND_DEPLOYMENT.md`](docs/BACKEND_DEPLOYMENT.md) · **Audit log:** [`docs/AUDIT_LOG.md`](docs/AUDIT_LOG.md) · **CI truth:** [`docs/TRUTH_ENFORCEMENT.md`](docs/TRUTH_ENFORCEMENT.md) · **Import boundaries:** [`docs/IMPORT_BOUNDARIES.md`](docs/IMPORT_BOUNDARIES.md) · **Root template barrier:** [`CONFIG_ROOT_TEMPLATE.md`](CONFIG_ROOT_TEMPLATE.md) · **Final cleanup:** [`docs/FINAL_CLEANUP_REPORT.md`](docs/FINAL_CLEANUP_REPORT.md).

**Which binary to run:** [`docs/CANONICAL_RUNTIME.md`](docs/CANONICAL_RUNTIME.md).

**Chrome OS recovery (download automation):** [`docs/CHROMEOS_RECOVERY.md`](docs/CHROMEOS_RECOVERY.md) · CLI: `python3 scripts/chromeos_recovery_download.py --help`

> **Non-core template:** The Expo / pnpm / tRPC workspace lives under **[`experimental/root-app-template/`](experimental/root-app-template/)** (not at repo root). For Phoenix mobile + USB remote control, use **`phoenix-core-mobile/`** with **`backend/`** FastAPI. See **[`ROOT_APP_TEMPLATE.redirect.md`](ROOT_APP_TEMPLATE.redirect.md)**.

---

## Unified architecture (at a glance)

| Module | Role |
|--------|------|
| [`crates/`](crates/) + [`apps/cli/`](apps/cli/) | **Phoenix Core engine** — device graph, safety, workflows (`phoenix-cli`). Long-term source of truth for low-level operations. |
| [`desktop/`](desktop/) | **BootForge** — PyQt6 GUI and Python engine under `desktop/src/` (USB recipes, safety validator, platform providers). Entry: `python main.py` at repo root. |
| [`backend/`](backend/) | **FastAPI** — REST for device scan, recipes, build jobs (orchestration for operators and mobile). |
| [`website/`](website/) | Flask demo / landing; optional recovery GUI build output under `website/recovery-gui/`. |
| [`phoenix-core-mobile/`](phoenix-core-mobile/) | Expo app — planning and remote status against the HTTP API. |
| [`mobile/`](mobile/) | **Deprecated** — use [`phoenix-core-mobile/`](phoenix-core-mobile/). |
| [`legacy/`](legacy/) | Archived toolkits and experiments — do not extend; port changes into `desktop/` or `crates/`. |
| [`experimental/root-app-template/`](experimental/root-app-template/) | **Non-core** Expo + pnpm + tRPC template (includes deprecated Flask `server/api.py`). |

---

## Features (Wave 8)

- **Universal USB creation**: Windows, Linux, macOS installers.
- **OCLP integration**: Unsupported Macs via OpenCore Legacy Patcher (`third_party/OpenCore-Legacy-Patcher` when checked out).
- **Phoenix Core Engine (Rust)**: Device graph, safety gates, imaging primitives, workflows.
- **BootForge (PyQt6)**: Wizard workflow and profiles via `desktop/`.

## Quick start

```bash
pip install -r requirements.txt
# Installs phoenix-safety from ./packages/phoenix_safety (shared SafetyValidator)

# BootForge GUI (repo root delegates to desktop/main.py)
python3 main.py --gui

# CLI
python3 main.py --help

# FastAPI backend (mobile / remote operators — install backend deps first)
pip install -r backend/requirements.txt
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
```

`GET /api/health` includes **`capabilities.destructive_usb_write_native`** (true on Linux with `dd`/`parted`). On other OSes, destructive USB steps may be limited — use BootForge on the desktop path for full parity.

**Rust CLI (supported crates on Linux — see `AGENTS.md`):**

```bash
cargo build -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 \
  -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim
```

## Repository map

```text
.
├── apps/cli/              # phoenix-cli
├── backend/               # FastAPI (devices, recipes, build jobs)
├── crates/                # Rust workspace (core, safety, hosts, imaging, …)
├── desktop/               # BootForge: main.py, src/ (engine + GUI)
├── packages/phoenix_safety/  # Shared SafetyValidator (pip install -e)
├── docs/                  # Architecture, contracts, audits
├── experimental/          # Non-core template: root-app-template/ (Expo+pnpm)
├── legacy/                # Quarantined / reference only
├── mobile/                # React Native (parallel to phoenix-core-mobile)
├── phoenix-core-mobile/   # Expo app (canonical mobile)
├── tests/                 # Python tests (imports desktop/src as `src`)
├── website/               # Flask web demo, recovery-gui assets
├── main.py                # Root entry → desktop/main.py
└── third_party/           # OCLP submodule (optional)
```

## License

- **Phoenix Core** – MIT License.
- **OpenCore Legacy Patcher** – BSD 2‑Clause.
