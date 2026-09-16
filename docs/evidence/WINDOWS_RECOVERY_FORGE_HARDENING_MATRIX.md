# Windows Recovery Forge — Hardening Matrix

Status: active convergence work on `convergence/windows-recovery-forge-macos-v2`.

## Product rule

Recovery Forge must be understandable before it is powerful. Analysis and planning are read-only. No destructive restore path may become reachable until its source, host, target, rollback, identity, and explicit-authorization gates have independent evidence.

## User journey

1. **Choose source** — local file/folder first; cloud sources are staged locally before analysis.
2. **Understand what Phoenix Key found** — plain-language type, confidence, warnings, and what is missing.
3. **Understand this computer** — Intel Mac, Apple Silicon Mac, Windows, or analysis-only host.
4. **Choose an outcome** — repair existing Windows, restore an exact system image, create recovery media, create clean install media, or inspect/export only.
5. **Review dry-run** — source, target, partitions, capacity, boot mode, drivers, rollback data, and exact changes.
6. **Authorize separately** — destructive execution remains a distinct phase and must re-enumerate the target immediately before writing.
7. **Verify and report** — checksums/readback, boot/recovery validation, receipts, and recovery/rollback instructions.

## Source coverage

| Source | Detection | User-facing result | Restore state |
| --- | --- | --- | --- |
| Windows ISO | ISO9660 signature | Windows disc image detected; inspect contents before use | Plan only |
| WIM / ESD | MSWIM signature | Windows image payload verified | Plan only |
| Split WIM / SWM | Complete-set validation pending | Explain that every segment is required | Blocked until complete |
| VHD | `conectix` footer | Legacy virtual disk image verified | Plan only |
| VHDX | `vhdxfile` signature | Virtual disk image verified | Plan only |
| WindowsImageBackup | Backup structure + VHD/VHDX payload | Windows system-image backup detected | Plan only |
| Incomplete WindowsImageBackup | Backup metadata without VHD/VHDX | Explain missing payload/download | Blocked |
| WinRE tree | Winre.wim / recovery layout | Windows recovery environment detected, not a full OS backup | Repair planning only |
| Extracted installer tree | Sources image + setup/boot evidence | Extracted Windows media detected | Media/repair planning |
| FFU | Signature validation not yet implemented | Extension alone is insufficient | Blocked |
| Unknown file/folder | No supported evidence | Explain supported choices | Blocked |

## Host routing

| Host | Allowed route | Explicit block |
| --- | --- | --- |
| Intel Mac | Analyze; plan Boot Camp repair/restore after exact-model and partition checks | No automatic internal write |
| Apple Silicon Mac | Analyze; Windows ARM media/VHDX/VM recovery planning | Traditional Boot Camp creation/restore is blocked |
| Windows | Analyze and plan native recovery workflows | Destructive execution still separately gated |
| Linux/other | Analyze, validate, export plans/media where supported | Machine-specific internal restore blocked without supported target workflow |

## Mandatory source gates

- File/directory exists and is readable.
- Format is identified from internal evidence, not filename alone where a signature exists.
- Source is non-empty.
- Integrity hash/manifest is captured before execution work.
- Windows architecture and edition are identified when possible.
- Multi-file sets are complete.
- Windows system-image backups expose their actual VHD/VHDX payloads before restore planning.
- Source remains immutable during target preparation; a changed source invalidates the plan.

## Mandatory target gates

- Fresh device enumeration.
- Canonical target identity.
- Source and target cannot resolve to the same physical device.
- System/internal/boot disk protection by default.
- Capacity and required free-space validation.
- Existing GPT/MBR and partition manifest captured before changes.
- EFI/UEFI/legacy boot compatibility determined.
- Exact Intel Mac model identified before Boot Camp restore.
- Correct Boot Camp driver package matched to model and Windows version before driver injection.
- Fresh identity recheck immediately before the first write.

## Rollback and evidence gates

Before an internal restore is ever enabled, capture:

- disk identifier and stable identity
- complete partition table / GPT metadata
- partition GUIDs and filesystem identifiers
- EFI directory inventory where readable
- Windows BCD metadata where readable
- WinRE configuration where readable
- source hash and source-analysis receipt
- intended-operation manifest
- app/source commit
- timestamps and target capacity

Every execution must emit a durable receipt. A failed operation must preserve enough evidence to explain what completed and what did not.

## UX requirements

The default screen must never lead with raw JSON, drive GUIDs, or recovery jargon. Show:

- **What we found**
- **How confident we are**
- **What you can safely do next**
- **What is blocked and why**
- **What will happen to your data**

Advanced technical evidence may be shown behind an explicit details control.

Dangerous buttons must use verb + consequence language, for example `Erase USB and create recovery media`, not vague labels such as `Continue`.

The product must distinguish these jobs instead of collapsing them into one Restore button:

- Repair Windows boot/recovery
- Restore my exact old Windows installation
- Create Windows recovery media
- Create a clean Windows installer
- Inspect/export my backup without changing disks

## Failure-state requirements

For every error, Phoenix Key should answer three questions:

1. What failed?
2. Was anything changed?
3. What should I do next?

Cancellation before the first write must be guaranteed non-destructive. Cancellation after execution begins must produce an interrupted-operation receipt rather than pretending rollback automatically succeeded.

## Google Drive / cloud-source rule

Cloud data must never be restored directly from a transient stream. Stage the selected backup locally or to a verified external workspace, support resumable transfer, verify size/hash after transfer, preserve the cloud original, and analyze the staged copy. If a cloud connector exposes only folder metadata and not the VHD/VHDX payload, report the source as incomplete rather than enabling restore.

## Release gates

Recovery Forge does not leave draft status until all applicable items are evidenced:

- Linux/macOS/Windows recovery probe tests green
- destructive-boundary scan green
- malformed/empty/truncated fixtures rejected
- WindowsImageBackup complete/incomplete fixtures tested
- Apple Silicon Boot Camp block tested
- Intel Mac route tested without internal writes
- source=target rejection tested
- unplug/replug target identity change tested in the guarded writer lane
- insufficient capacity tested
- interrupted transfer and interrupted write receipts tested
- UI keyboard/focus/readability pass
- first-run copy understandable without specialist terminology
- advanced details separated from the default workflow
- signed/notarized desktop build evidence for release edition

## Current known limitation

The connected Google Drive hierarchy includes a real `WindowsImageBackup/bj-90-PC/Backup 2025-02-13 104757` path, but the available Drive connector has not exposed the underlying binary system-image payload. That backup must remain analysis-incomplete until the actual VHD/VHDX files can be read or staged. No repository code should claim otherwise.
