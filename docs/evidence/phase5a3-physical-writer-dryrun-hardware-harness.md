# Phase 5A-3: Physical USB Writer Dry-Run Hardware Lab Harness

## Purpose
Phase 5A-3 implements a dry-run physical hardware lab writer harness. This harness replicates the exact control path of the future physical writer without performing any physical disk mutations or writes. It checks permissions, verifies target identity lock state, performs drift comparisons, designs structured request/result models, integrates into the existing safety contract ledger, and provides CLI/Dashboard controls.

Physical USB writing remains strictly blocked.

## Files Changed
- `real_writer_interface.py`
- `usb_creator.py`
- `dashboard/vite.config.js`
- `dashboard/src/App.jsx`
- `tests/test_physical_writer_dryrun_harness.py`
- `docs/evidence/phase5a3-physical-writer-dryrun-hardware-harness.md`

## Permission Status Design
The elevation check uses schema:
```text
bootforge.hardware_lab_permission_status.v1
```
It evaluates running_as_admin_or_root. If false, elevation is blocked and elevation is requested.

## Dry-run Physical Writer Request Design
The request uses schema:
```text
bootforge.physical_writer_dryrun_request.v1
```
It bundles target parameters (drive, stable ID, identity hash), source image parameters (path, SHA256, size), lock ID, readiness gate ID, session ID, and ledger configuration.

## Dry-run Physical Writer Result Design
The result uses schema:
```text
bootforge.physical_writer_dryrun_result.v1
```
It forces:
- `dry_run_only: true`
- `physical_write_allowed: false`
- `physical_write_attempted: false`
- `bytes_written: 0`
- Calculated chunk plans based on image size.

## Adapter Behavior
`PhysicalDryRunWriterAdapter` executes mock calculations. It does not open raw devices or make destructive OS system calls.
OS-specific physical writer adapters (`WindowsPhysicalWriterAdapter`, `MacPhysicalWriterAdapter`, `LinuxPhysicalWriterAdapter`) remain blocked.

## CLI Behavior
Added flags:
- `--physical-writer-dryrun`
- `--hardware-lab-permission-status`
- `--export-physical-dryrun-json`
- `--export-physical-dryrun-markdown`
- `--mock-hardware-preflight` (test-only flag)

In normal CLI mode, if real preflight, identity lock, readiness, or target connection scanning evidence is missing, the command returns a blocked result. Generating mock target parameters is strictly gated behind the `--mock-hardware-preflight` flag or unit tests.

## Dashboard Behavior
The dashboard exposes the **Physical Writer Dry-Run Harness** panel. It allows running checks and viewing permissions.
Required statement:
```text
Physical writer dry-run only. No physical USB bytes are written, and the dashboard cannot start a real USB write.
```

## Evidence Export Behavior
Provides JSON and Markdown export helpers with path validations rejecting empty paths, system directories, UNC/device namespace paths, target drive roots, and overwrites.

## Ledger Integration
Integrates with the writer safety contract ledger, producing audit-safe and append-only evidence.

## Test Results
All backend unit tests passed:
```text
198/198 OK
```

## Dashboard Build Result
```text
Vite build completed successfully
```

## Danger Scan Summary
- UI label scans: No forbidden write labels found.
- Call-site scans: Only allowed hits found (docs, tests, comments, safety statements).

## Safety Assertion
- Physical USB writing remains strictly blocked.
- Zero physical bytes are written to any USB drive in this phase.
- The dashboard is read-only and cannot trigger or start a real physical USB write.
- Destructive capabilities still completely absent: partition editing, disk formatting, filesystem creation (mkfs), mount automation, unmount automation, diskpart script running, dd execution, and raw device write access.
