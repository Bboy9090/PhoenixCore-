# Legacy Materials (to remove or quarantine)

This repository is being reshaped into **phoenix-core**. The following areas are **legacy or transitional** — do not treat them as the primary place for new features:

## Legacy / quarantine areas

- `legacy/` — old BootForge copies, bootcamp, and experiments (including `legacy/bootable_usb/BootForge/`, which duplicates `desktop/src/`).
- `server/` — Flask API that assumes a sibling `PhoenixCore-` checkout; use `backend/` (FastAPI) for new HTTP work.
- `dist/`, `build/` — generated artifacts (never commit).
- Root-level `archive/`, old `assets/` trees if present — verify before use.

## Canonical (not legacy) in the current tree

- **`desktop/src/`** — active BootForge Python engine (GUI, safety, providers). Tests add `desktop/` to `sys.path` so imports use `src.*`.
- **`crates/`** — Rust phoenix-core engine and CLI.
- **`backend/`** — FastAPI orchestration service.

## Policy

Long-term direction: **Rust under `crates/`** owns low-level disk and imaging primitives; Python layers should become thinner orchestration. Until parity exists, BootForge may shell out to system tools — document any destructive path in operator-facing docs.
