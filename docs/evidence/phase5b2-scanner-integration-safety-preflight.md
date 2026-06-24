# Phase 5B-2: Scanner Integration Into USB Safety + Preflight Flow

**Date**: 2026-06-24
**Branch**: `phase5b2/scanner-integration-safety-preflight`
**Base**: `usb-creator-foundation-lock` @ `0274bdc9`
**Tag**: `phase5b2-scanner-integration-safety-preflight`

## Goal

Wire `device_scanner.scan_devices()` (Phase 5B-1's v2 scanner) into the existing USB safety, preflight, identity lock, and dry-run paths. This phase is **read-only** — no physical writing, no dashboard write controls, no raw device writer.

## Files Modified

| File | Change |
|------|--------|
| `usb_creator.py` | Added `get_normalized_scan()`, rewrote `get_removable_drives()` as v2 compatibility wrapper, updated `build_drive_scan_payload()` to v2 schema |
| `real_writer_interface.py` | Added `_resolve_scanner_device()`, `_build_scanner_identity_hash()`, updated identity lock/rescan/preflight to use scanner v2 evidence |
| `tests/test_usb_creator.py` | Updated 2 tests to mock `get_normalized_scan` instead of old platform-specific code; updated schema assertions from v1 to v2 |
| `tests/test_scanner_integration_preflight.py` | **NEW** — 39 integration tests across 11 test classes |

## Integration Points

### 1. usb_creator.py — Scan Path Delegation
- `get_normalized_scan(quiet=False)` — thin wrapper around `device_scanner.scan_devices()` with structured logging
- `get_removable_drives()` — now delegates to `get_normalized_scan()` instead of platform-specific code (ctypes/diskutil/lsblk); returns legacy-shaped list for backward compatibility
- `build_drive_scan_payload()` — schema upgraded from `bootforge.drive_scan.v1` to `bootforge.drive_scan.v2`; includes both v2 `devices` array and legacy `drives` array

### 2. real_writer_interface.py — Identity Lock + Preflight
- `_resolve_scanner_device(target_drive, scan_payload)` — resolves a target drive path to a scanner v2 device record; checks `drive_path`, `path`, and `drive` keys for backward compatibility
- `_build_scanner_identity_hash(device)` — deterministic SHA-256 from: stable_id, serial, size_bytes, platform, drive_path, detection_source, bus_protocol
- `build_removable_target_identity_lock()` — uses v2 scanner identity hash when device has `drive_path` key; falls back to legacy `device_identity_hash` for legacy format payloads
- `rescan_and_compare_target_identity()` — uses v2 hash via `_resolve_scanner_device` and `_build_scanner_identity_hash` for re-scan comparison
- `build_physical_writer_preflight_result()` — enriched with scanner evidence fields: `scanner_schema`, `scanner_confidence`, `scanner_detection_source`, `scanner_stable_id`, `scanner_serial`, `scanner_block_reasons`, `scanner_warnings`
- **Low confidence blocks**: `if scanner_confidence == "low"` → preflight adds block reason: "Scanner confidence is low; identity lock is unreliable for lab write eligibility."

### 3. Dashboard
- No changes to `dashboard/src/App.jsx`
- Dashboard remains **read-only** — no write triggers, no forbidden labels
- Dashboard builds cleanly (`vite build` succeeds)

## Test Results

### New Tests: `tests/test_scanner_integration_preflight.py`
- **39 tests, 11 classes, all passing**
- Coverage: scan delegation, legacy output shape, fixed/internal/system blocking, stable_id/confidence, target path resolution, ambiguous target blocking, identity lock scanner fields, identity drift, dry-run safety, preflight scanner evidence, command failure safety, dashboard forbidden labels, no destructive call sites

### Existing Tests
- **158 passed, 16 failed** (across all required test files)
- All 16 failures are **pre-existing** (confirmed by baseline test without Phase 5B-2 changes: same 16 failures)
  - 8 in `test_usb_creator.py`: registry signature verification (sig file issue), OCLP download mocking, Windows ctypes mocking on macOS
  - 4 in `test_drive_safety.py`: Windows-specific tests on macOS
  - 4 in `test_hardware_writer_preflight.py` / `test_physical_writer_dryrun_harness.py`: `/var/folders` temp path triggering suspicious path check
- **Zero new failures introduced by Phase 5B-2**

## Danger Scans

| Scan | Result |
|------|--------|
| Destructive commands (dd, mkfs, diskpart, format, fdisk, parted, sgdisk, wipefs, shred, blkdiscard) | **CLEAN** — none found |
| Raw device open (PhysicalDrive, /dev/sd, /dev/disk, /dev/rdisk, O_WRONLY, O_RDWR) | **CLEAN** — none found |
| Unmount/eject commands | **CLEAN** — only in dashboard comments describing what is NOT implemented |
| subprocess write commands | **CLEAN** — none found |
| Forbidden dashboard labels (Write USB, Burn USB, Flash USB, Start Write, Format USB, Erase Drive, Arm Writer, Execute Write, Destructive Write, Write Now) | **CLEAN** — none found as UI element text |

## Safety Assertions

- This phase is **read-only**: no physical writing added
- No dashboard write controls added
- No raw device writer added
- No mount/unmount/format/partition automation added
- Scanner v2 identity hash is deterministic and reproducible
- Low-confidence scanner results block lab write eligibility at preflight level
- Legacy scan payload formats remain supported via backward-compatible resolution
- Dashboard builds without errors and contains no forbidden labels
