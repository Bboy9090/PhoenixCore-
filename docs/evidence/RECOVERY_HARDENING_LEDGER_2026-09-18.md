# Phoenix Key Recovery Forge — Evidence Ledger — 2026-09-18

Branch: `convergence/windows-recovery-forge-macos-v2`  
PR: #150  
Status: DRAFT / ACTIVE HARDENING  
Rule: implementation is not a PASS until exact-head CI completes.

## Sweep 12 — Source identity binding

Implemented:
- file SHA-256 identity
- bounded directory-manifest SHA-256
- source size / modified time / canonical path evidence
- symlink refusal
- before/after identity comparison while planning
- stale identity verification returns reanalysis required
- desktop Recovery Center uses the same identity-bound planner as the probe
- pre-mutation gate explicitly requires a fresh identity recheck

Primary files:
- `apps/phoenix-key/src-tauri/src/source_identity.rs`
- `apps/phoenix-key/src-tauri/src/recovery_center.rs`
- `apps/phoenix-key/src-tauri/examples/windows_recovery_probe.rs`

Status: IMPLEMENTED / exact-head CI pending.

## Sweep 13 — Target identity and source-target collision

Implemented:
- read-only Windows source-path to `PHYSICALDRIVE<n>` resolution
- source != target physical-device proof
- target capacity proof
- existing boot/system/external/stable-ID gates preserved
- same-device collision check exists in planning contract
- same-device collision check also executes inside the destructive writer immediately before eligibility is granted

Primary files:
- `apps/phoenix-key/src-tauri/src/target_safety.rs`
- `scripts/hardware/resolve_windows_source_disk.py`
- `scripts/hardware/write_windows_sacrificial_drive.py`
- `tests/test_windows_source_disk_resolution.py`
- `tests/test_windows_sacrificial_writer.py`

Status: IMPLEMENTED / exact-head CI pending.

## Sweeps 14–16 — EFI / BCD / WinRE evidence and rollback

Implemented read-only boot-state capture:
- EFI System Partition inventory
- Secure Boot state query
- `bcdedit /enum all`
- `reagentc /info`
- command-output hashes
- boot-state snapshot SHA-256
- no EFI/BCD/WinRE/partition writes

Rollback manifest binds:
- source identity
- target identity / capacity / topology
- boot-state snapshot
- required backup artifacts
- fresh source/target pre-mutation rechecks

Canonical rollback bundle:
- verifies snapshot and rollback-manifest digests
- BCD export backup
- actual EFI file-tree backup only when the ESP is already directly accessible
- ReAgent.xml backup
- WinRE image backup only when directly accessible
- refuses symlink backup sources
- hashes all persisted rollback artifacts
- repair unlock remains false if any required artifact is missing
- even a complete repair bundle never authorizes repartitioning, full image application, or Secure Boot key changes

Primary files:
- `scripts/hardware/capture_windows_boot_state.py`
- `scripts/hardware/persist_windows_rollback_bundle.py`
- `tests/test_windows_boot_state.py`
- `tests/test_windows_rollback_bundle.py`
- `.github/workflows/windows-drive-evidence.yml`

Status: IMPLEMENTED / exact-head CI pending.

## Sweep 16b — Boot repair decision contract

Implemented evidence-driven routing:
- BCD failure + ESP present -> boot-chain repair assessment
- WinRE failure + BCD healthy -> WinRE repair assessment
- missing ESP + verified restore source -> partition/full-restore assessment
- missing ESP without verified source -> blocked
- healthy evidence -> no invented repair

The contract remains:
- `executable=false`
- `system_mutations_performed=false`

Primary file:
- `apps/phoenix-key/src-tauri/src/boot_repair_contract.rs`

Status: IMPLEMENTED / exact-head CI pending.

## Sweep 17 — Interruption / unplug / partial write

Writer hardening implemented:
- target seek/write/flush/fsync/readback failures become explicit interruption errors
- partial byte counts recorded
- short writes fail
- readback failures fail
- hash mismatch fails
- deterministic failure receipt persisted
- interrupted write classification is never success
- resume is explicitly disabled
- restart requires fresh source identity
- restart requires fresh target identity

Tested by a simulated unplug after the first successful chunk.

Primary files:
- `scripts/hardware/write_windows_sacrificial_drive.py`
- `tests/test_windows_sacrificial_writer.py`

Status: IMPLEMENTED / exact-head CI pending.

## Sweep 18 — Intel Mac / Boot Camp compatibility

Implemented:
- Apple Silicon hard-blocked from traditional Boot Camp
- Intel Mac route requires exact model identity
- Windows source architecture must be x64 for traditional Intel Boot Camp route
- no automatic partition mutation
- no unverified driver injection
- Boot Camp support-software evidence required
- driver-package verification remains separate from host routing

Primary file:
- `apps/phoenix-key/src-tauri/src/mac_bootcamp_compat.rs`

Status: IMPLEMENTED / exact-head CI pending.

## Sweep 18b — Boot Camp driver-package manifest

Implemented:
- exact Mac model binding
- deterministic whole-package SHA-256 manifest
- per-file SHA-256
- symlink rejection
- Authenticode evidence for Windows driver/binary extensions
- missing expected manifest hash blocks verification
- invalid signatures block verification
- non-Windows signature inspection remains pending rather than fabricated

Primary files:
- `scripts/hardware/inspect_bootcamp_driver_package.py`
- `tests/test_bootcamp_driver_package.py`
- `.github/workflows/bootcamp-driver-manifest.yml`

Status: IMPLEMENTED / exact-head CI pending.

## Sweep 19 — Recovery package trust

Implemented:
- SHA-256 verification for recovery images/packages
- Authenticode inspection for signed Windows binaries/drivers
- optional expected signer-subject match
- unsupported package types blocked
- valid-but-blocked inspections return structured JSON instead of becoming generic process failures

Primary files:
- `scripts/hardware/inspect_recovery_package_trust.py`
- `tests/test_recovery_package_trust.py`
- `.github/workflows/recovery-package-trust.yml`

Status: IMPLEMENTED / exact-head CI pending.

## Sweep 20 — Windows image architecture / edition / exact index

Implemented:
- DISM read-only `/Get-ImageInfo`
- enumerates image indexes
- detailed per-index metadata
- architecture normalization
- edition ID capture
- multi-index media requires explicit selection
- architecture mismatch blocks eligibility
- ISO is not mounted automatically
- split WIM sets require contiguous `install.swm`, `install2.swm`, … segments before DISM metadata inspection; missing/gapped sets fail closed

Primary files:
- `scripts/hardware/inspect_windows_image_metadata.py`
- `tests/test_windows_image_metadata.py`
- `.github/workflows/windows-image-metadata.yml`

Status: IMPLEMENTED / exact-head CI pending.

## Sweep 21 — Restore-readiness convergence contract

A single non-executable contract now requires all of:
1. complete source identity
2. trusted package hash/signature evidence
3. exact Windows image index selection
4. architecture compatibility
5. safe distinct target identity
6. complete rollback bundle
7. non-destructive planning state

Even when all gates pass:
- `executable=false`

This means passing the contract only proves the evidence set is coherent enough to design a later executor; it does not authorize restoration.

Primary file:
- `apps/phoenix-key/src-tauri/src/restore_readiness.rs`

Status: IMPLEMENTED / exact-head CI pending.

## Recovery Center UX integration

The desktop Recovery Center now displays:
- source SHA-256 identity
- source identity completeness / recheck rule
- expected SHA-256 input
- package trust result and block reasons
- image-index input
- target architecture
- Windows edition/name/architecture
- explicit image-selection and compatibility blockers

Primary file:
- `apps/phoenix-key/src/RecoveryCenter.tsx`

Status: IMPLEMENTED / UI build pending on exact head.

## Current safety boundary

Still disabled:
- destructive Windows restore
- EFI file writes
- BCD modification
- WinRE modification
- repartitioning
- system-image application
- Secure Boot key changes
- firmware-security bypass
- BIOS password bypass
- ChromeOS enrollment / Verified Boot bypass
- BitLocker cracking
- Android FRP bypass
- Apple Activation Lock bypass

The pre-existing sacrificial removable-media writer remains separate and retains its authorization, target-identity, capacity, removable-device, source-target collision, byte-cap, and readback verification gates.

## CI state at ledger creation

GitHub Actions is congested. Multiple older heads were cancelled by concurrency before starting because newer branch commits superseded them. That is not test evidence.

Exact current tip must complete:
- Windows Recovery Forge
- Phoenix Key Desktop
- Phoenix Key Windows Lifecycle
- Windows Drive Evidence
- Windows Sacrificial Writer
- Recovery Package Trust
- Windows Image Metadata
- Boot Camp Driver Manifest
- Verify Repository
- PhoenixCore Foundation
- Release Gate
- Validate Governance
- Validate Boot Matrix
- Validate Artifacts
- App Reality Matrix
- Launch Boundary Audit

No PASS is claimed here until exact-tip results are collected.


## Sweep 22 — Recovery Center accessibility hardening

Implemented:
- live status updates are atomic for assistive technology
- expected-hash field disables autocorrect/spellcheck and has explicit help text
- technical-evidence disclosure exposes expanded/collapsed state
- technical evidence has a stable controlled region and keyboard focus target
- existing visible focus and reduced-motion handling preserved

Primary files:
- `apps/phoenix-key/src/RecoveryCenter.tsx`
- `apps/phoenix-key/src/recovery-center.css`

Status: IMPLEMENTED / exact-head CI pending.
