# Phase 4C-2: Contract CLI + Dashboard Read-Only Contract Preview

**Branch:** `phase4c2/contract-cli-dashboard-preview`  
**Base commit:** `b25ee1c6` (Merge PR #112 — Phase 4C-1)  
**Date:** 2026-06-21  
**Tag:** `phase4c2-contract-cli-dashboard-preview-lock`

---

## 1. Phase Purpose

Phase 4C-2 exposes the writer safety contract (`bootforge.writer_safety_contract.v1`) for
read-only visibility through the CLI and the dashboard UI. It does **not** expand the
contract's power: the cage is shown, the tiger gets no door handle.

No real writer is introduced. No destructive operations exist.
`real_writer_implemented` remains `false`. `destructive_operations_enabled` remains `false`.

---

## 2. Files Changed

| File | Type | Change |
|---|---|---|
| `writer_safety_contract.py` | MODIFIED | Added `build_contract_preview_payload()` bridge function; updated `_cli_validate_writer_contract()` to consume full preview args |
| `usb_creator.py` | MODIFIED | Wired `--validate-writer-contract`, `--audit-passed`, `--simulation-passed`, `--typed-confirmation`, `--destructive-acknowledgement` CLI flags |
| `dashboard/vite.config.js` | MODIFIED | Added `GET /api/write/contract` bridge route |
| `dashboard/src/App.jsx` | MODIFIED | Added `contractData` state, `fetchContractPreview()` async function, and Writer Safety Contract Preview panel |
| `tests/test_writer_safety_contract_preview.py` | NEW | 10 test objectives, 17 test methods |
| `docs/evidence/phase4c2-contract-cli-dashboard-preview.md` | NEW | This evidence document |

No existing test files were modified. `usb_creator.py` changes are additive only.

---

## 3. CLI Behavior

### New flag: `--validate-writer-contract`

```bash
python usb_creator.py --validate-writer-contract
python usb_creator.py --validate-writer-contract --target-drive E:\ --image ubuntu.iso
python usb_creator.py --validate-writer-contract --target-drive E:\ --image ubuntu.iso --audit-passed --simulation-passed
```

**What it does:**
- Delegates immediately to `writer_safety_contract._cli_validate_writer_contract(args)`
- Calls `build_contract_preview_payload()` with the supplied args
- Prints the full contract JSON to stdout
- Returns exit code 0 always (blocked contracts are not errors)

**What it does NOT do:**
- Does not open, read, write, mount, unmount, or query any drive
- Does not call diskpart, dd, WriteFile, or any raw-device API
- Does not perform any destructive action
- Does not change any system state

### New companion flags

| Flag | Type | Purpose |
|---|---|---|
| `--audit-passed` | boolean | Reports audit gate as passed in the preview |
| `--simulation-passed` | boolean | Reports simulation gate as passed in the preview |
| `--typed-confirmation` | string | Future gate display only — no effect on blocking |
| `--destructive-acknowledgement` | string | Future gate display only — no effect on blocking |

---

## 4. Dashboard API Endpoint

### `GET /api/write/contract`

Implemented in `dashboard/vite.config.js` as a bridge route, following the same
pattern as all existing bridge routes.

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `drive` | string | Candidate target drive path |
| `image` | string | Candidate image file path |
| `auditPassed` | `"true"` / omit | Whether audit gate should be reported as passed |
| `simulationPassed` | `"true"` / omit | Whether simulation gate should be reported as passed |

**Response schema:** `bootforge.writer_safety_contract.v1`

**Invariants:**
- `real_writer_implemented: false` — always
- `destructive_operations_enabled: false` — always
- `blocked: true` — always (Phase 4C-2 lock)
- On any error: safe blocked fallback payload is returned, not an unhandled exception

**What the endpoint does NOT do:**
- Does not write, format, partition, mount, or unmount any drive
- Does not call diskpart, dd, or any raw-device API
- Does not expose any write-enabling path

---

## 5. Dashboard UI Panel

### Panel title: **Writer Safety Contract Preview**

Location: Below the Mock Writer Simulator panel, above the terminal console.

**Button:** `Preview Writer Safety Contract` (id: `btn-preview-writer-safety-contract`)

**Panel displays:**
- Schema badge (`bootforge.writer_safety_contract.v1`)
- Phase badge
- Blocked status pill (⛔ BLOCKED / ✓ UNBLOCKED)
- `real_writer_implemented: false` — green card
- `destructive_operations_enabled: false` — green card
- Gate results table (all 11 required gates with PASS / PENDING status)
- Identity hashes (device + image, if present)
- Block reasons list
- Warnings list
- Next required action
- Contract ID + timestamp

**Required safety copy (always visible):**
> "Read-only safety contract preview. No USB write, format, partition, mount,
> unmount, raw disk access, or destructive operation is available."

**Forbidden labels confirmed absent:**
- Write USB ✗ not present
- Burn USB ✗ not present
- Flash USB ✗ not present
- Start Write ✗ not present
- Format USB ✗ not present
- Erase Drive ✗ not present
- Arm Writer ✗ not present
- Execute Write ✗ not present
- Destructive Write ✗ not present
- Write Now ✗ not present

---

## 6. Safety Statement

```text
real_writer_implemented        = false  (hard-coded, immutable)
destructive_operations_enabled = false  (hard-coded, immutable)
blocked                        = true   (always — at minimum by the 4C lock)

No write to any drive.
No format.
No partition changes.
No mount or unmount operations.
No raw disk access.
No diskpart.
No dd.
No WriteFile / CreateFile on block devices.
No subprocess calls to disk utilities.
No real write button.
No arm writer button.
```

The `build_contract_preview_payload()` function builds identity structures from
path strings only. It does not stat, open, or read any file unless checking whether
an image path exists (size_bytes field) — and even then it only calls `Path.stat()`,
not any write or device API.

---

## 7. Test Results

**Command:**
```bat
python -m unittest tests/test_usb_creator.py tests/test_image_inspection.py ^
  tests/test_drive_safety.py tests/test_write_plan.py tests/test_plan_audit.py ^
  tests/test_plan_export.py tests/test_mock_writer.py ^
  tests/test_writer_safety_contract.py tests/test_writer_safety_contract_preview.py
```

**Result:**
```text
Ran 91 tests in 1.382s

OK
```

**Dashboard build:**
```text
vite v8.0.14 building for production...
✓ 1738 modules transformed.
dist/index.html       0.67 kB │ gzip:  0.41 kB
dist/assets/*.css     7.78 kB │ gzip:  2.19 kB
dist/assets/*.js    252.00 kB │ gzip: 73.19 kB
✓ built in 2.49s
```

### Test objectives satisfied

| # | Objective | Status |
|---|---|---|
| 1 | Preview returns schema `bootforge.writer_safety_contract.v1` | ✅ |
| 2 | `real_writer_implemented` remains `false` | ✅ |
| 3 | `destructive_operations_enabled` remains `false` | ✅ |
| 4 | Preview with missing drive is blocked | ✅ |
| 5 | Preview with missing image is blocked | ✅ |
| 6 | Fully valid mock preview still does not enable writing | ✅ |
| 7 | Payload is JSON serializable (round-trip verified) | ✅ |
| 8 | Forbidden destructive labels not in executable Python source (AST-verified) | ✅ |
| 9 | CLI preview does not require or perform destructive actions | ✅ |
| 10 | Repeated preview with same inputs is deterministic | ✅ |

---

## 8. Explicit Safety Declarations

### No real writer exists

> Neither `writer_safety_contract.py`, `usb_creator.py`, `vite.config.js`,
> nor `App.jsx` contains any code that opens a device handle, calls `WriteFile`,
> invokes `diskpart` or `dd`, accesses `/dev/` paths, or performs any byte-level
> write to any block device. All four files build, fetch, and display JSON payloads only.

### Destructive operations remain disabled

> `destructive_operations_enabled` is hard-coded to `False` inside
> `build_writer_safety_contract()` and is not a parameter, not a keyword argument,
> and not overridable from the CLI or the dashboard API.

### Forbidden capabilities still absent

- USB writing: **absent**
- Drive formatting: **absent**
- Partition editing: **absent**
- Mount automation: **absent**
- Unmount automation: **absent**
- Raw disk access: **absent**
- diskpart invocation: **absent**
- dd invocation: **absent**
- Bootloader writing: **absent**
- Real write button: **absent**
- Arm writer button: **absent**

---

## 9. Phase 4C-2 Exit Criteria Status

| EC | Criterion | Status |
|---|---|---|
| EC1 | Contract preview available through safe CLI path | ✅ Done |
| EC2 | Dashboard API endpoint returns blocked contract | ✅ Done |
| EC3 | Dashboard UI shows contract read-only panel | ✅ Done |
| EC4 | Required safety copy present in UI | ✅ Done |
| EC5 | Forbidden UI labels absent | ✅ Confirmed |
| EC6 | 91 tests passing, 0 regressions | ✅ Confirmed |
| EC7 | Dashboard build clean | ✅ Confirmed |
| EC8 | No real writer introduced | ✅ Confirmed |
