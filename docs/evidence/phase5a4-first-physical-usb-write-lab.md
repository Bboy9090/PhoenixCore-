# Phase 5A-4: First Physical USB Write Lab

## Summary

Phase 5A-4 introduces the **Physical USB Write Lab** — a CLI-only, lab-only, sacrificial-test-drive-only framework for executing a gated physical USB write on a removable external drive.

**No physical USB bytes are written in this phase.** The adapter validates all 27 safety gates, but the actual write path returns `physical_writer_not_safely_implemented`. This establishes the complete gate validation pipeline without executing destructive I/O.

---

## Safety Architecture

### 27 Required Gates

| # | Gate | Description |
|---|------|-------------|
| 1 | Environment unlock | `BOOTFORGE_ENABLE_PHYSICAL_USB_WRITE=I_ACCEPT_SACRIFICIAL_USB_WRITE_RISK` |
| 2 | Admin/root | Must be running with elevated privileges |
| 3 | Target from scan | Target drive must come from hardware scan evidence |
| 4 | Target has stable ID | Stable hardware identifier required |
| 5 | Target has identity hash | Identity hash from prior lock required |
| 6 | Target is removable/external | Only removable external drives allowed |
| 7 | Target is not fixed/internal | Fixed and internal drives permanently blocked |
| 8 | Target is not system drive | System drives permanently blocked |
| 9 | Identity lock exists | A prior identity lock must be referenced |
| 10 | Latest re-scan matches lock | Re-scan must confirm locked identity |
| 11 | No identity drift | Hash comparison must show zero drift |
| 12 | Image exists | ISO/image file path required |
| 13 | Image SHA256 exists | Image hash required for verification |
| 14 | Image size exists | Image size in bytes required (>0) |
| 15 | Write plan exists | A validated write plan must precede |
| 16 | Audit passed | Plan audit must have passed |
| 17 | Mock simulation passed | Mock writer simulation required |
| 18 | Hardware preflight passed | Hardware preflight must have passed |
| 19 | Physical dry-run exists | A completed dry-run result is required |
| 20 | Physical dry-run wrote zero bytes | Dry-run must confirm zero bytes written |
| 21 | Readiness gate passed | Final destructive readiness gate required |
| 22 | Ledger path exists and safe | Ledger path must exist and not target system dirs |
| 23 | Evidence export path safe | Export paths must not target system dirs |
| 24 | Typed confirmations match | All three typed phrases must match exactly |
| 25 | User requested physical USB write lab | Explicit `--physical-usb-write-lab` flag required |
| 26 | Adapter supports platform | Platform must be `win32` (macOS/Linux blocked) |
| 27 | Target path maps to scanned/locked target | Target must trace back to scan + lock chain |

### Three Typed Confirmations

1. `"I UNDERSTAND THIS WILL OVERWRITE THE SELECTED PHYSICAL USB DRIVE"`
2. `"I CONFIRM THIS IS A SACRIFICIAL REMOVABLE TEST USB DRIVE"`
3. `"I ACCEPT FULL RESPONSIBILITY FOR THIS TEST USB WRITE"`

### Dashboard Restrictions

- Dashboard is **read-only** for physical write status
- No write trigger button exists
- Allowed label: "View Physical USB Write Lab Status"
- Message displayed: "Physical USB write lab mode is CLI-only. The dashboard cannot start a physical USB write."

---

## What Was Implemented

### `real_writer_interface.py` — Part 7

- `build_physical_usb_write_lab_request()` — schema v1 request builder
- `build_physical_usb_write_lab_result()` — schema v1 result builder
- `build_physical_usb_write_lab_verification()` — schema v1 verification builder
- `validate_physical_usb_write_lab_gates()` — validates all 27 gates
- `PhysicalUSBWriteLabAdapter` — adapter that validates gates, always returns blocked
- `build_physical_usb_write_lab_status()` — read-only status for dashboard
- `validate_physical_usb_write_lab_export_path()` — safe path validation
- `export_physical_usb_write_lab_json()` — JSON evidence export
- `generate_physical_usb_write_lab_markdown()` — Markdown report generator
- `export_physical_usb_write_lab_markdown()` — Markdown evidence export

### `usb_creator.py` — CLI Arguments

- `--physical-usb-write-lab` — Execute physical write lab mode
- `--physical-usb-write-lab-status` — Print read-only status JSON
- `--export-physical-write-json` — Export result as JSON
- `--export-physical-write-markdown` — Export result as Markdown
- `--final-irreversible-acknowledgement` — Third typed confirmation
- `--physical-write-chunk-size` — Chunk size in bytes
- `--physical-write-max-bytes` — Maximum bytes cap
- `--require-dryrun-result` — Path to required dry-run JSON
- `--require-preflight-result` — Path to required preflight JSON
- `--require-identity-lock` — Path to required identity lock JSON

### `dashboard/vite.config.js`

- Added `/api/write/physical-usb-write-lab-status` GET route (read-only)

### `dashboard/src/App.jsx`

- Added read-only "Physical USB Write Lab Status" panel
- Button label: "View Physical USB Write Lab Status"
- Displays: platform, write implemented, write allowed, CLI-only, dashboard blocked, env unlock, admin/root, next action, block reasons
- No write trigger button

---

## What Is NOT Implemented

- No physical USB bytes are written
- No raw device I/O
- No formatting, partitioning, mounting, or unmounting
- No dd, diskpart, or mkfs calls
- No dashboard write trigger
- No consumer write mode
- macOS and Linux physical writes remain blocked

---

## Absolutely Forbidden (Verified Not Present)

- No `Write USB`, `Burn USB`, `Flash USB`, `Start Write`, `Format USB`, `Erase Drive`, `Arm Writer`, `Execute Write`, `Destructive Write`, `Write Now` labels
- No diskpart, dd, mkfs, mount, unmount, format automation
- No writes to fixed/internal/system drives
- No writes without identity lock
- No writes without typed confirmation
- No writes without environment unlock
- No writes from the dashboard
- No auto-selected target writes
- No hidden writes

---

## Test Coverage

Test file: `tests/test_physical_usb_write_lab.py`

30 tests covering:
- Schema version assertions (request, result, verification)
- Constant value assertions (env var, typed confirmations)
- All 27 gate validations (individual block reason tests)
- Adapter behavior (blocked, not-safely-implemented, zero bytes)
- Status endpoint (always blocked, CLI-only, required gates list)
- Export path validation (empty, UNC, system dirs, wrong extensions, overwrite)
- JSON and Markdown export (success and failure paths)
- Chunk calculation (exact division, rounding, zero size)
- Safety assertion presence in generated markdown

---

## Schema Versions

| Schema | Version |
|--------|---------|
| `bootforge.physical_usb_write_lab_request` | v1 |
| `bootforge.physical_usb_write_lab_result` | v1 |
| `bootforge.physical_usb_write_lab_verification` | v1 |
| `bootforge.physical_usb_write_lab_status` | v1 |
