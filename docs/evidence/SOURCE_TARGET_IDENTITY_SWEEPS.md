# Phoenix Key — Source + Target Identity Sweeps

Date: 2026-09-19
Branch: `convergence/windows-recovery-forge-macos-v2`
PR: #150

## Sweep 12 — Source identity and stale-plan invalidation

Implemented in `apps/phoenix-key/src-tauri/src/source_identity.rs`.

Claims now enforced by code:
- regular-file recovery sources receive a full streaming SHA-256
- directory recovery sources receive a bounded, sorted manifest digest over relative path, size, modification time, and each file's SHA-256
- symbolic-link sources and symbolic-link directory members are rejected
- directory manifests are bounded to 1024 files and depth 8; exceeding the bound marks the identity incomplete and blocks an identity-bound plan
- a recovery plan captures identity before planning and again immediately after planning
- if the source changes during planning, plan creation fails closed
- the emitted plan carries `source_identity` plus `source_identity_gate = recheck_immediately_before_any_mutation`
- an independent verification function marks digest mismatch as `reanalysis_required=true`

Automated tests:
- file identity changes when source bytes change
- directory manifest changes when a member changes
- stale expected digest requires re-analysis
- an identity-bound recovery plan contains source identity evidence

Probe commands:
- `identity <path>`
- `verify <path> <expected-sha256>`
- `plan <path>` now emits an identity-bound plan

Safety result:
A plan is no longer considered portable across source mutations. A later mutation boundary must re-check the recorded digest before execution.

## Sweep 13 — Target collision / capacity / identity contract

Implemented in `apps/phoenix-key/src-tauri/src/target_safety.rs`.

Claims now enforced by code:
- existing drive-evidence `write_candidate` block reasons are preserved
- boot disks are blocked
- system disks are blocked
- target identity must be a valid 64-character SHA-256
- target capacity must exist and be at least the source size
- source physical device and target physical device must be proven distinct
- missing source physical-device proof fails closed
- same physical source/target device fails closed

Automated tests:
- distinct sufficiently sized target passes the contract
- source/target physical-device collision is blocked
- insufficient target capacity is blocked
- unproven source device is blocked
- existing boot/system-disk blocks remain intact

Probe command:
- `target-check <evidence-json> <source-size-bytes> <source-physical-target|unknown>`

## Existing writer protections retained

The Windows sacrificial writer already performs fresh target re-enumeration immediately before write, checks the stable identity hash and capacity against the evidence lock, blocks boot/system disks, requires an exact authorization phrase, caps bytes written to the source image length, and verifies the full write by SHA-256 read-back.

The new target contract sits before that writer. It does not weaken or replace the writer's own fresh pre-write target checks.

## Subsequent closure

The convergence branch now also contains:
- automatic Windows source-path to physical-disk resolution through `resolve_windows_source_disk.py`
- source/target collision enforcement in the sacrificial writer
- writer authorization bound to target identity, target capacity, and the source SHA-256
- an immediate pre-raw-open source recheck covering byte length, SHA-256, source physical device, and source/target distinction
- a second fresh target identity/capacity scan immediately before raw-device open
- persisted prewrite source/target recheck evidence in success and interruption receipts
- Windows boot-state capture plus rollback-manifest/bundle persistence for EFI/BCD/WinRE evidence
- non-resumable interruption receipts, a simulated unplug-after-first-write test, and explicit ENOSPC failure-receipt coverage

The source-SHA authorization/recheck and ENOSPC receipt changes added on 2026-09-19 remain subject to exact-head CI before they can be treated as verified.

## Still required before destructive recovery unlock

- exact-head CI success for the newest source-bound writer changes
- real sacrificial-hardware unplug/replug identity-change evidence
- explicit ENOSPC/short-capacity failure-receipt coverage at the execution boundary
- Google Drive OAuth/Picker integration and verified acquisition-to-identity-lock handoff
- signed/notarized desktop release evidence and final release review

Result: SOURCE/TARGET IDENTITY CONTRACT IMPLEMENTED AND EXECUTION BOUNDARY HARDENED; destructive recovery remains gated.
