# Phoenix Key Recovery Forge — Evidence Ledger — 2026-09-18

Branch: `convergence/windows-recovery-forge-macos-v2`  
PR: #150  
Status: DRAFT PR / SOFTWARE CONVERGENCE VERIFIED  
Rule: implementation is not a PASS until exact-head CI completes.

> Historical sweep entries below retain the status recorded when they were written. The current verification record at the end of this ledger supersedes earlier "exact-head CI pending" notes.

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


## Sweep 23 — Restore rollback contract + software hardware-preflight boundary

Implemented:

- canonical full-restore rollback contract
- source identity binding
- target snapshot identity binding
- target stable hardware identity binding
- target capacity binding
- separate-physical-device rollback destination requirement
- explicit required artifact list
- `apply_system_image` always blocked
- `restore_unlock_ready=false`
- software-only hardware preflight proving whether evidence collection may begin

Primary files:

- `apps/phoenix-key/src-tauri/src/restore_rollback_contract.rs`
- `apps/phoenix-key/src-tauri/src/restore_preflight.rs`

Status: IMPLEMENTED / CI-GATED.

## Sweep 24 — Separate rollback destination + read-only GPT capture

Implemented:

- rollback destination physical-device resolution
- stable-identity proof that destination is not the target
- fresh target revalidation
- protective MBR capture
- primary/backup GPT headers
- primary/backup partition arrays
- GPT/header CRC validation
- partition-array CRC validation
- primary/backup cross-reference validation
- partition manifest
- artifact hashes
- rollback-contract binding
- zero target-write receipt
- capture output only to a separate rollback folder

Primary files:

- `apps/phoenix-key/src-tauri/src/rollback_destination.rs`
- `scripts/hardware/capture_windows_restore_rollback.py`
- `tests/test_windows_restore_rollback_capture.py`

Status: IMPLEMENTED / FIXTURE-VERIFIED / REAL-HARDWARE PROOF STILL REQUIRED.

## Sweep 25 — Stable target re-enumeration proof

Implemented:

- durable checksum-verifiable re-enumeration receipt
- stable hardware identity locator across `PHYSICALDRIVE<n>` renumbering
- exact snapshot mismatch classification
- stale authorization rejection
- hardware substitution detection
- ambiguous stable-ID match blocking
- local persisted receipt
- Recovery Center reconnect workflow

Primary files:

- `apps/phoenix-key/src-tauri/src/target_reenumeration.rs`
- `scripts/hardware/find_windows_drive_by_stable_identity.py`
- `tests/test_windows_stable_target_locator.py`
- `apps/phoenix-key/src/RecoveryCenter.tsx`

Status: IMPLEMENTED / FIXTURE-VERIFIED / REAL UNPLUG-REPLUG PROOF STILL REQUIRED.

## Sweep 26 — External-target boot metadata + data-preservation decision

Implemented:

External target boot metadata:

- fresh target identity recheck before capture
- partition inventory
- EFI tree capture only when already accessible
- BCD files where already accessible
- WinRE image/config where already accessible
- no partition mount/assignment
- inaccessible EFI/Recovery partitions remain unresolved
- zero target writes

Data-preservation decision:

- preserve mode requires real backup receipt
- explicit discard requires exact acknowledgement
- receipt bound to target stable identity
- receipt bound to rollback contract
- never unlocks restore

Primary files:

- `scripts/hardware/capture_windows_restore_target_boot_metadata.py`
- `tests/test_windows_restore_target_boot_metadata.py`
- `apps/phoenix-key/src-tauri/src/data_preservation.rs`

Status: IMPLEMENTED / CI-GATED / REAL-HARDWARE CAPTURE STILL REQUIRED.

## Sweep 27 — Recovery Evidence Bundle v2 + durable session state

Implemented:

Evidence bundle:

- one checksum-bound record for all current evidence classes
- per-component presence / schema / digest / trust
- separate software-chain and hardware-chain completeness
- explicit outstanding requirements
- stale re-enumeration rejected as hardware-complete
- hardware substitution rejected
- `restore_executable=false`

Persistent session:

- deterministic read-only resume phase
- target-reanalysis-required override
- hardware-substitution-blocked override
- local collision-safe persistence
- destructive authorization never persisted
- automatic destructive resume disabled
- restore executable remains false

Primary files:

- `apps/phoenix-key/src-tauri/src/recovery_evidence_bundle.rs`
- `apps/phoenix-key/src-tauri/src/recovery_session.rs`

Status: IMPLEMENTED / CI-GATED.

## Sweep 28 — Sanitized recovery diagnostics

Implemented:

- checksum-bound diagnostics export
- component bundle + session state included
- sensitive paths redacted
- hardware serial/unique ID redacted
- provider file IDs redacted
- raw command stdout/stderr/arguments redacted
- typed destructive acknowledgement redacted
- destructive authorization never included
- restore executable remains false
- local collision-safe persistence

Primary files:

- `apps/phoenix-key/src-tauri/src/recovery_diagnostics.rs`
- `apps/phoenix-key/src/RecoveryCenter.tsx`

Status: IMPLEMENTED / CI-GATED.

## Verified software checkpoint — 2026-09-20

Exact head:

`d78e2a90854f133d771d993b40d63b1429f55a07`

Result:

**24 / 24 GitHub Actions workflows successful.**

This included:

- Windows Recovery Forge
- Verify Repository
- Phoenix Key Desktop
- Phoenix Key Windows Lifecycle
- Phoenix Key Signed Windows Release
- Phoenix Key macOS Signed Release
- Phoenix Key Mac App Store
- Phoenix Key Microsoft Store
- Windows Drive Evidence
- Windows Sacrificial Writer
- Recovery Package Trust
- Windows Image Metadata
- Windows FAT32 Media Plan
- Boot Camp Driver Manifest
- Cloud Recovery Staging
- Validate Governance
- Validate Artifacts
- Validate Boot Matrix
- Release Gate
- App Reality Matrix
- Launch Boundary Audit
- PhoenixCore Foundation
- PhoenixCore Android Store Release
- PhoenixCore Mobile APK Candidate

The documentation-refresh commits after this checkpoint require their own exact-head CI pass. They do not invalidate the verified software checkpoint, but they are not considered merge-ready until the refreshed head is green.

## Current remaining blocker

The remaining Recovery Forge blocker is physical Windows hardware evidence:

- sacrificial target observation
- separate physical rollback destination
- real read-only GPT capture with zero target writes
- physical unplug/replug/re-enumeration
- stable identity continuity
- stale snapshot rejection
- hardware-substitution rejection
- real external-target boot metadata behavior
- real target-data backup receipt if preserve mode is chosen

No fixture may be promoted to hardware proof.

## Restore executor boundary

No full Windows restore executor exists in Recovery Center.

Any future restore executor requires a separate architecture gate and implementation lane. It must not be inferred from this PR, from the sacrificial removable-media writer, or from evidence-chain completeness.
