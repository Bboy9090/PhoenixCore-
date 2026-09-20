# Windows Recovery Forge — Hardening Matrix

Status: software convergence complete on
`convergence/windows-recovery-forge-macos-v2`; PR #150 remains draft.

Last fully verified software checkpoint before this documentation refresh:
`d78e2a90854f133d771d993b40d63b1429f55a07` — **24/24 PR workflows successful**.

## Product rule

Recovery Forge must be understandable before it is powerful.

Analysis, planning, identity verification, rollback capture, session persistence, and diagnostics export remain non-destructive. No Windows restore executor is reachable from Recovery Center.

The existing Phoenix Key sacrificial removable-media writer is a separate subsystem with its own destructive authorization and safety contract. Recovery Forge does not inherit that authorization.

## Current user journey

1. **Choose source**
   - local file/folder, or
   - stage a Google Drive file locally through the guarded acquisition flow.
2. **Analyze source**
   - type/signature
   - completeness
   - source identity
   - warnings and host route.
3. **Verify source**
   - fresh identity
   - package trust
   - exact image/index metadata
   - architecture compatibility.
4. **Analyze target**
   - source != target physical device
   - boot/system protection
   - capacity
   - snapshot identity
   - stable hardware identity.
5. **Create rollback contract**
   - binds source + both target identities
   - remains non-executable.
6. **Run hardware preflight**
   - proves the software evidence chain is coherent enough to collect hardware rollback evidence.
7. **Verify rollback destination**
   - must be a different physical device.
8. **Capture GPT rollback artifacts**
   - target remains read-only.
9. **Capture target boot metadata**
   - only from already-accessible partitions; inaccessible EFI/Recovery partitions remain blocked.
10. **Resolve target data handling**
    - preserve mode requires a real backup receipt
    - explicit discard requires an exact acknowledgement.
11. **Handle re-enumeration**
    - locate same stable hardware
    - reject stale snapshot authorization
    - require full reanalysis.
12. **Build evidence bundle**
    - one checksummed view of all current evidence.
13. **Persist read-only session**
    - safe resume state only
    - no destructive authorization persisted.
14. **Export sanitized diagnostics**
    - paths, hardware IDs, provider IDs, command output, and acknowledgements redacted.

## Source coverage

| Source | Detection / validation | Current state |
| --- | --- | --- |
| ISO | ISO9660 signature + content planning | Analysis / planning |
| WIM | MSWIM signature + DISM metadata | Analysis / planning |
| ESD | DISM metadata | Analysis / planning |
| Split WIM | contiguous set validation + DISM metadata | Analysis / planning when complete |
| VHD | `conectix` footer + checksum-aware validation | Analysis / planning |
| VHDX | `vhdxfile` signature | Analysis / planning |
| WindowsImageBackup | structure + VHD/VHDX payload discovery | Analysis / planning when payload visible |
| Incomplete WindowsImageBackup | metadata without payload | Blocked with explanation |
| WinRE tree | recovery layout / Winre.wim | Repair planning |
| Extracted installer | Sources + EFI/BCD/setup evidence | Media / repair planning |
| FFU | extension alone insufficient | Blocked |
| Unknown | unsupported or insufficient evidence | Blocked |

## Host routing

| Host | Current route | Explicit boundary |
| --- | --- | --- |
| Windows | full read-only Recovery Center evidence workflow | no system-image restore executor |
| Intel Mac | analysis + exact-model Boot Camp planning | no internal destructive restore |
| Apple Silicon Mac | Windows ARM / VM-oriented planning | traditional Boot Camp blocked |
| Linux / other | analysis / validation / export | machine-specific internal restore blocked |

## Source identity gates

Status: **implemented and CI-gated**.

- file SHA-256 identity
- deterministic bounded directory manifest
- unsafe symlink/reparse traversal rejection
- source plan binding
- fresh re-verification
- changed source invalidates planning
- package trust
- exact Windows image index selection
- architecture compatibility
- complete split-WIM requirement

## Target identity gates

Status: **implemented and CI-gated**.

- exact Windows `PHYSICALDRIVE<n>` normalization
- source != target proof
- system / boot disk protection
- capacity check
- snapshot identity
- stable hardware identity
- fresh identity verification
- stable-ID target locator
- ambiguous locator match blocked
- re-enumeration classification
- hardware substitution classification
- stale snapshot authorization rejected

## Rollback contract

Status: **implemented and CI-gated**.

The full-restore rollback contract requires:

- target partition table backup
- target partition manifest
- target boot metadata if present
- data-preservation receipt or explicit discard decision
- artifact checksums
- separate physical rollback destination
- fresh target revalidation

The contract always blocks `apply_system_image`.

## GPT rollback capture

Status: **implemented in software / fixture-tested / real hardware still required**.

Software evidence covers:

- primary GPT header CRC
- backup GPT header CRC
- primary/backup cross references
- partition-array CRC
- primary/backup partition-array equality
- protective MBR
- artifact hashes
- partition manifest
- zero target writes
- rollback-contract binding
- target snapshot + stable identity binding
- separate destination identity

Real-hardware proof remains required.

## External-target boot metadata

Status: **implemented in software / fixture-tested / real hardware still required**.

Supported read-only capture where already accessible:

- EFI file tree
- EFI / Boot BCD files
- WinRE image
- ReAgent.xml
- partition inventory

Safety boundary:

- no drive-letter assignment
- no partition mount
- no target writes
- inaccessible EFI/Recovery partition remains unresolved

## Data-preservation decision

Status: **implemented and CI-gated**.

`preserve_existing_data`:

- cannot resolve without a real target-data backup receipt.

`explicit_discard`:

- exact acknowledgement required:
  `I ACCEPT DATA LOSS ON THIS TARGET`
- bound to target stable identity
- bound to rollback contract
- never unlocks restore execution.

## Recovery Evidence Bundle v2

Status: **implemented and CI-gated**.

The bundle:

- checksums each supplied evidence component
- verifies component trust
- distinguishes software-chain vs hardware-chain completeness
- lists outstanding requirements
- rejects stale re-enumeration as hardware-complete
- rejects hardware substitution
- always reports `restore_executable: false`

## Persistent recovery session

Status: **implemented and CI-gated**.

Session phases include:

- source pending
- source verified
- image verified
- target verified
- rollback planned
- software preflight complete
- rollback destination verified
- rollback captured
- awaiting boot metadata
- awaiting data preservation
- target reanalysis required
- hardware substitution blocked
- hardware evidence complete

Hard invariants:

- destructive authorization is not persisted
- automatic destructive resume is false
- restore executable is false
- hardware substitution blocks resume
- stale target evidence forces reanalysis

## Sanitized diagnostics export

Status: **implemented and CI-gated**.

Redacted fields include:

- local paths
- hardware serials / unique IDs
- provider file IDs
- command stdout / stderr
- command arguments
- typed data-loss acknowledgement

Preserved diagnostic value includes:

- evidence hashes
- trust status
- gate results
- session phase
- outstanding requirements

The export never includes destructive authorization.

## Google Drive acquisition

Status: **implemented read-only acquisition path; production credential/configuration evidence remains environment-dependent**.

Implemented:

- system-browser Picker
- `drive.file`-scoped access
- PKCE/state
- one-file selection
- local staging
- resumable ranged download
- safe cancellation
- provider size/hash validation where available
- local SHA-256 identity lock
- cloud original preserved

Downloaded data must still enter normal Recovery Center analysis and identity gates.

## CI gates

At verified head
`d78e2a90854f133d771d993b40d63b1429f55a07`,
**24/24 workflows succeeded**.

Recovery-specific CI covers:

- Windows/macOS/Ubuntu full binary tests
- recovery probe tests
- recovery probe build
- clippy
- Recovery Center UI build
- destructive-command boundary scan
- target-locator fixtures
- GPT rollback fixtures
- target boot-metadata fixtures

Repository/release CI also covers:

- Verify Repository
- governance
- artifacts
- release gate
- application reality
- boot matrix
- desktop packaging
- Windows lifecycle
- signed Windows candidate
- signed macOS candidate
- Mac App Store
- Microsoft Store
- mobile release candidates
- drive evidence
- sacrificial writer
- package trust
- Windows image metadata
- FAT32 media planning
- Boot Camp driver manifest
- cloud recovery staging

## Remaining real-hardware campaign

These are **not** satisfied by fixture tests:

- observe a real sacrificial target as exact `PHYSICALDRIVE<n>`
- record snapshot + stable identities
- verify rollback output is a separate physical disk
- run GPT capture against real hardware
- prove target write count is zero
- physically unplug/replug the target
- prove stable identity survives re-enumeration
- prove stale snapshot authorization is rejected
- substitute another sacrificial disk
- prove stable identity mismatch is rejected
- capture target boot metadata where partitions are already accessible
- exercise target-data backup/preservation evidence if preserve mode is chosen

## Merge boundary

PR #150 may converge the software-only Recovery Forge architecture without enabling destructive Windows restore.

A future restore executor requires:

- a separate architecture gate
- a separate implementation lane / PR
- explicit destructive authorization design
- final source + target identity rechecks
- rollback preconditions
- power-loss and interruption semantics
- real hardware evidence

Merging this PR is not authorization to create that executor.
