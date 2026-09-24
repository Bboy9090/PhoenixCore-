# Windows Recovery Repair Gates — 2026-09-17

Branch: `convergence/windows-recovery-forge-macos-v2`
PR: #150

## Evidence chain

The Windows recovery lane now requires the following ordered evidence before repair execution can even be designed:

1. Source identity
   - SHA-256 for regular files.
   - Bounded manifest SHA-256 for directories.
   - Symlink sources rejected.
   - Source mutation during planning invalidates the plan.

2. Source physical-disk resolution
   - Windows drive-letter source resolves to a concrete `\\.\PHYSICALDRIVE<n>`.
   - Source and target must be proven distinct.
   - Collision proof is fail-closed.

3. Target evidence
   - Exact physical-drive target.
   - Stable target identity SHA-256.
   - Capacity evidence.
   - System/boot disk blocking.
   - External/removable proof.
   - Fresh identity recheck remains mandatory before write.

4. EFI / BCD / WinRE state
   - Read-only EFI System Partition inventory.
   - Secure Boot state capture when available.
   - `bcdedit /enum all` evidence with content hashes.
   - `reagentc /info` evidence with content hashes.
   - No EFI, BCD, WinRE, partition, or firmware mutation.

5. Rollback manifest and bundle
   - Manifest binds source identity, target identity, partition layout, and boot-state snapshot.
   - Rollback bundle persists partition-layout evidence and EFI inventory.
   - BCD store is exported to a local backup artifact.
   - WinRE image is copied and hashed only when already reachable through a normal filesystem path.
   - The tool never auto-mounts the EFI System Partition or privileged GLOBALROOT recovery locations.
   - Any missing rollback artifact keeps repair locked.

6. Recovery readiness
   - Validates source identity, target evidence, boot-state hash, rollback bundle hash, source/target collision proof, and capacity.
   - A passing result allows only checkpointed repair planning.
   - `destructive_restore_unlocked` remains false.

7. Checkpointed repair plan
   - Supported plan classes:
     - `bcd_repair`
     - `winre_relink`
     - `efi_boot_files_repair`
   - Every plan requires:
     - fresh source identity recheck,
     - fresh target identity recheck,
     - fresh boot-state capture and comparison,
     - rollback bundle revalidation,
     - repair-specific compatibility verification,
     - explicit repair authorization.
   - `execution_enabled` is false.
   - `destructive_restore_unlocked` is false.

## Current safety boundary

These additions do not execute BCDBoot, BCDEdit mutations, REAgentC mutations, firmware writes, partition changes, EFI mounting, formatting, raw disk writes, or a full restore.

The existing sacrificial media writer remains a separate path with its own authorization and fresh-target gates.

## Next gate

Before any repair executor is enabled:

- exact-head CI must be green,
- rollback-bundle artifact persistence must pass focused tests,
- recovery-readiness tests must pass,
- repair-plan tests must pass,
- repair executor must use an allowlisted operation contract,
- every mutation must create a pre-operation checkpoint and post-operation verification receipt,
- destructive restore remains separately locked.
