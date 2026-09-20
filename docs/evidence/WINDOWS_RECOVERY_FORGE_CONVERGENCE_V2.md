# Windows Recovery Forge Convergence V2

## Canonical lane

- Repository: `Bboy9090/PhoenixCore-`
- Base: `main`
- Base SHA at branch creation: `b9cc058419dd6711d6eff3d9ff1a84256cd3803f`
- Working branch: `convergence/windows-recovery-forge-macos-v2`
- Draft PR: #150
- Last fully verified software checkpoint before this documentation refresh:
  `d78e2a90854f133d771d993b40d63b1429f55a07`
- Exact-head verification at that checkpoint: **24/24 GitHub Actions workflows successful**

The earlier `convergence/windows-recovery-forge-macos` branch was based on older lineage and is not the canonical implementation lane. Divergent historical branches are donor/evidence lanes only; they are never wholesale-merged over current `main`.

## Product boundary

Recovery Forge is a guarded recovery-analysis and evidence system. It is not a Windows restore executor.

The current Recovery Center may:

- inspect and classify Windows recovery sources
- bind source content identity
- inspect Windows image metadata and architecture
- validate package trust
- analyze a proposed target
- bind target snapshot and stable hardware identities
- create a non-executable rollback contract
- verify a physically separate rollback destination
- capture read-only GPT rollback artifacts
- locate the same physical target after Windows re-enumeration
- emit checksum-verifiable re-enumeration receipts
- capture already-accessible external-target EFI/BCD/WinRE metadata without mounting or assigning partitions
- record the target data-preservation decision
- construct a checksummed Recovery Evidence Bundle v2
- derive and persist a read-only Recovery Session State
- export sanitized diagnostics evidence

The current Recovery Center may **not**:

- erase or repartition the restore target
- apply a Windows system image
- write EFI files
- modify BCD
- modify WinRE
- inject drivers destructively
- change Secure Boot keys
- mount or assign an inaccessible target partition merely to satisfy an evidence gate
- persist destructive authorization
- automatically resume destructive work
- unlock restore execution

Every new recovery receipt continues to report `system_mutations_performed: false`. Evidence completion and restore execution are intentionally separate concepts.

## Source identity and trust

`source_identity.rs` binds planning to the exact source:

- files use SHA-256 identity
- directories use a bounded deterministic manifest
- symlinks/reparse-style unsafe traversal is rejected
- a changed source requires reanalysis
- planning embeds the source identity
- fresh source verification must match the planned identity before later gates may pass

Supported recovery-source inspection includes:

- ISO
- WIM / ESD
- complete split-WIM sets
- VHD / VHDX
- WindowsImageBackup structures
- WinRE trees
- extracted Windows installation media

Filename extension alone is not accepted when an internal format signature can be checked.

## Target identity model

Phoenix Key intentionally separates two identities:

1. **Snapshot identity** — binds the exact enumeration/path/topology observed for the current authorization window.
2. **Stable hardware identity** — binds serial/unique ID/bus/capacity evidence so the same physical device can be recognized after Windows renumbers `PHYSICALDRIVE<n>`.

Consequences:

- exact snapshot + stable match may continue read-only planning
- same stable hardware with a changed snapshot/path is classified as re-enumeration
- stale snapshot authorization is rejected
- full target safety analysis must run again after re-enumeration
- a different stable hardware identity is classified as substitution and blocks the session
- ambiguous stable-ID discovery never auto-selects a device

## Restore rollback contract

`restore_rollback_contract.rs` creates
`phoenix_key.restore_target_rollback_contract.v1`.

It binds:

- source identity SHA-256
- target snapshot identity SHA-256
- target stable identity SHA-256
- target size
- required rollback artifacts
- separate-physical-device destination requirement
- fresh target revalidation requirement

Required evidence includes:

- target partition-table backup
- target partition manifest
- target boot-metadata backup if present
- target data-preservation receipt or explicit discard decision
- artifact checksums

The contract always keeps:

- `restore_unlock_ready: false`
- `restore_unlock_scope: []`
- `apply_system_image` blocked
- `system_mutations_performed: false`

## Read-only GPT rollback capture

`capture_windows_restore_rollback.py` captures, from the exact Windows target:

- protective MBR
- primary GPT header
- primary partition entries
- backup partition entries
- backup GPT header
- partition manifest
- artifact SHA-256 values
- a checksum-verifiable capture receipt

It validates GPT header CRCs, partition-array CRCs, primary/backup cross-references, target identity, rollback contract binding, and separate-destination identity before producing evidence.

The target remains read-only:

- `target_bytes_written: 0`
- `target_write_attempted: false`
- `restore_unlock_ready: false`

Fixture proof is not treated as physical-hardware proof.

## Re-enumeration evidence

Recovery Forge now supports a complete read-only re-enumeration workflow:

1. Freeze target snapshot + stable identities.
2. Enumerate current Windows disks.
3. Locate the unique disk whose stable identity matches.
4. Compare current evidence with the frozen baseline.
5. Persist a checksum-verifiable receipt.
6. Reject stale snapshot authorization.
7. Require full target reanalysis before further planning.

The session model treats any receipt with `reanalysis_required: true` as incomplete hardware evidence even when the stable hardware matches.

## Target boot-metadata backup

`capture_windows_restore_target_boot_metadata.py` is scoped to an external restore target, not the current Windows boot/system disk.

It may copy metadata only from partitions Windows already exposes. It does not:

- assign a drive letter
- mount an inaccessible EFI/Recovery partition
- write to the target
- change BCD/WinRE/EFI state

If an EFI or Windows Recovery partition exists but is not already accessible, the boot-metadata requirement remains unresolved instead of being silently marked complete.

The capture is bound to:

- fresh target snapshot identity
- stable hardware identity
- rollback contract SHA-256
- prior read-only GPT rollback receipt

## Data-preservation gate

`data_preservation.rs` separates intent from execution.

Modes:

- `preserve_existing_data` — remains unresolved until a real target-data backup receipt exists
- `explicit_discard` — resolves only when the exact acknowledgement
  `I ACCEPT DATA LOSS ON THIS TARGET` is supplied

Even a resolved explicit-discard receipt keeps:

- `restore_unlock_ready: false`
- `system_mutations_performed: false`

The acknowledgement is bound to the exact target stable identity and rollback contract.

## Recovery Evidence Bundle v2

`recovery_evidence_bundle.rs` creates one checksummed evidence record over the current recovery session.

It records component presence, schema, digest, and trust for:

- identity-bound recovery plan
- fresh source verification
- package trust
- Windows image metadata
- target safety
- fresh target verification
- rollback contract
- hardware preflight
- rollback destination verification
- GPT rollback capture
- re-enumeration receipt
- data-preservation receipt
- boot-metadata receipt

The bundle distinguishes:

- `software_chain_complete`
- `hardware_chain_complete`

It always keeps `restore_executable: false`.

A stale re-enumeration receipt or substitution can never satisfy the hardware chain.

## Durable read-only recovery session

`recovery_session.rs` derives a resumable phase from the verified evidence bundle.

Representative phases include:

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

Session persistence is local and checksum-bound.

It explicitly records:

- `automatic_destructive_resume_allowed: false`
- `restore_executable: false`
- `system_mutations_performed: false`
- destructive authorization is **not** persisted

Hardware substitution blocks even read-only resume until the intended target is selected again.

## Sanitized diagnostics export

`recovery_diagnostics.rs` exports a checksum-bound support package while redacting sensitive local values such as:

- paths
- serial numbers
- unique IDs
- raw command stdout/stderr
- command arguments
- provider file IDs
- typed destructive acknowledgements

Identity hashes, safety verdicts, bundle state, and session state remain available for diagnosis.

Diagnostics never contain destructive authorization and never make restore executable.

## Google Drive recovery acquisition

The branch includes read-only Google Drive acquisition support with:

- system-browser Picker flow
- `drive.file`-scoped selection
- PKCE/state protections
- resumable ranged download
- cancellation at safe chunk boundaries
- local staging
- provider size/hash checks where available
- local SHA-256 identity lock
- cloud original preserved

A downloaded payload is not automatically considered recovery-ready; it enters the same local source-analysis and identity pipeline as any other source.

## CI safety contract

`.github/workflows/windows-recovery-forge.yml` gates:

- Recovery Center TypeScript/Vite build
- full Phoenix Key binary unit tests
- recovery probe unit tests
- recovery probe build
- clippy
- destructive-command boundary scan
- stable-target locator fixtures
- GPT rollback capture fixtures
- external-target boot-metadata fixtures

The recovery core runs on:

- Windows
- macOS
- Ubuntu

At verified head
`d78e2a90854f133d771d993b40d63b1429f55a07`,
all 24 PR workflows were successful, including:

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
- repository/governance/release/artifact/application-reality/boot-matrix gates

## What remains before destructive restore work can be designed

The remaining blocker is real hardware evidence, not another software-only fixture.

Required physical observations include:

1. Connect a sacrificial Windows-visible target.
2. Capture the exact `\\.\PHYSICALDRIVE<n>` snapshot + stable identity.
3. Verify a rollback folder on a different physical device.
4. Run the read-only GPT rollback capture and confirm target writes remain zero.
5. Physically unplug/replug/re-enumerate the target.
6. Prove the stable hardware identity survives and stale snapshot authorization is rejected.
7. Substitute a different sacrificial disk and prove stable-identity mismatch is rejected.
8. Capture external-target boot metadata where already accessible.
9. Resolve the data-preservation requirement with a real backup receipt or an explicit user discard decision.

No restore executor should be introduced on this PR.

## Merge-readiness status

Software state at the verified checkpoint is clean and fully green.

PR #150 should remain draft until its documentation refresh itself is revalidated on exact-head CI and the project decides whether software-only convergence is intended to merge before the separate physical-hardware campaign.

Merging PR #150 must not be interpreted as authorization to implement or enable destructive Windows restore.
