# Phase 5B-3: Read-Only Hardware Evidence Bundle

**Date**: 2026-06-25
**Branch**: `phase5b3/read-only-hardware-evidence-bundle`
**Base**: `usb-creator-foundation-lock` @ `27ddc571`
**Tag**: `phase5b3-read-only-hardware-evidence-bundle`

## What Was Added

A CLI-driven read-only evidence bundle that composes scanner, identity-lock, preflight, and dry-run evidence into a single exportable payload. No physical writing. No destructive operations.

### CLI Flags
- `--export-hardware-evidence-bundle` — Export evidence bundle (JSON to stdout)
- `--hardware-evidence-target <drive>` — Target drive for evidence collection
- `--hardware-evidence-label <label>` — Human label
- `--hardware-evidence-redact-serials` — Redact device serials
- `--hardware-evidence-include-full-scan` — Include full scan payload
- `--hardware-evidence-json <path>` — Export JSON to file
- `--hardware-evidence-markdown <path>` — Export Markdown to file

## Files Changed

| File | Change |
|------|--------|
| `real_writer_interface.py` | Added `build_hardware_evidence_bundle()`, `generate_hardware_evidence_markdown()`, `validate_hardware_evidence_export_path()`, `export_hardware_evidence_json()`, `export_hardware_evidence_markdown()` |
| `usb_creator.py` | Added CLI flags and dispatch for evidence bundle |
| `tests/test_hardware_evidence_bundle.py` | **NEW** — 25 tests across 10 test classes |
| `docs/evidence/phase5b3-read-only-hardware-evidence-bundle.md` | This evidence document |

## Behavior

### Scanner Evidence
- Uses `device_scanner.scan_devices()` via `get_normalized_scan()` — no duplicate scanner logic
- Includes scan summary with schema, scan_id, device_count, detection_source, warnings
- Scanner failure degrades into evidence warning, does not crash

### Target Resolution
- No target → `resolution_reason: no_target_selected`, blocked
- Target not found → `resolution_reason: target_not_found`, blocked
- Ambiguous target (multiple matches) → `resolution_reason: ambiguous_target`, blocked
- Fixed/internal/system target → `resolution_reason: fixed_internal_or_system_target`, blocked, not eligible
- Low confidence → blocked, not eligible, block reason added
- Valid removable high-confidence → eligible but `physical_write_allowed: false`

### Identity Preview
- Identity lock preview composed from `build_removable_target_identity_lock()`
- Rescan preview composed from `rescan_and_compare_target_identity()`
- Identity hash is deterministic and stable for same scan evidence

### Preflight Preview
- Preflight preview composed from `build_physical_writer_preflight_result()`
- `physical_writer_allowed: false` always

### Dry-Run Preview
- `dry_run_only: true`, `physical_write_allowed: false`, `physical_write_attempted: false`, `bytes_written: 0`
- Identity drift detection included

### Serial Redaction
- `--hardware-evidence-redact-serials` replaces serial with `REDACTED`
- `stable_id` replaced with truncated SHA-256 hash (16 chars)
- Redaction applied to top-level fields AND nested previews (identity lock, preflight)
- Identity hash preserved (already derived evidence)
- No raw serial leaks in JSON or Markdown output when redaction is enabled

### JSON Export
- Valid JSON with `bootforge.hardware_evidence_bundle.v1` schema
- Includes all evidence fields, previews, safety assertions

### Markdown Export
- Human-readable with sections for target, scanner, identity, preflight, dry-run, safety
- Includes safety contract block asserting no physical writing

## Tests

### New: `tests/test_hardware_evidence_bundle.py` — 25 tests, 10 classes
All passing:
- Schema is `bootforge.hardware_evidence_bundle.v1`
- `physical_write_allowed: false`
- `physical_write_attempted: false`
- `bytes_written: 0`
- `dashboard_write_available: false`
- No target → blocked bundle
- Ambiguous target → blocked bundle
- Fixed/internal/system → blocked, not eligible
- Removable high-confidence → eligible but not write-allowed
- Target not found → blocked
- Low confidence blocks eligibility
- Identity hash stable for same evidence
- Identity drift detected when scan changes
- Serial redaction removes raw serial from JSON
- Serial redaction removes raw serial from Markdown
- Stable ID hashed when redacted
- JSON export valid
- Markdown export includes safety contract
- Scanner failure degrades into warning
- Identity lock, preflight, dryrun previews present
- Dashboard has no forbidden labels
- No destructive call sites in bundle code
- CLI returns valid JSON

### Regression
- **Baseline** (usb-creator-foundation-lock): 260 passed, 32 failed
- **Phase 5B-3**: 325 passed, 32 failed
- Failure set: **identical** (diff is empty)
- New failures introduced: **none**

## Dashboard
- **Dashboard unchanged** — no files modified
- Dashboard builds cleanly (verified in Phase 5B-2)

## Danger Scan
- **Clean** — all hits are read-only references (comments, mount-point reads, volume info queries)
- No destructive command paths added

## UI Label Scan
- **Clean** — no forbidden labels found in dashboard

## Safety Assertions
- **No physical writing added** in this phase
- **No dashboard write trigger added** in this phase
- `physical_write_allowed: false` in every evidence bundle
- `physical_write_attempted: false` in every evidence bundle
- `bytes_written: 0` in every evidence bundle
- `dashboard_write_available: false` in every evidence bundle
