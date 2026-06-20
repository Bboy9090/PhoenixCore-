# Phase 4B: Real Writer Architecture Gate

**Document type:** Architecture design — no implementation  
**Branch:** `phase4b/real-writer-architecture-gate`  
**Base commit:** `1cec3ff2` (Merge PR #110 — Phase 4A)  
**Date:** 2026-06-20  
**Status:** Design only. No real writer exists. No destructive code exists.

---

## 1. Phase 4B Purpose

Phase 4B is a **design and gate-definition phase only**.

Its sole purpose is to specify every safety constraint, state transition, identity lock, confirmation requirement, failure model, and audit obligation that must exist **before any real writer implementation is permitted to begin** in Phase 4C or later.

### What this phase does

- Defines the threat model for a real USB write operation.
- Defines the state machine a future writer must follow.
- Defines the confirmation gate a user must pass before any write is armed.
- Defines device identity and image identity lock schemas.
- Defines boundary rules that permanently block a write if any gate fails.
- Defines the failure and recovery model.
- Defines the audit log schema for a future write session.
- Defines exact UX safety language for the future writer screen.
- Defines what must be true before Phase 4C is allowed to begin.

### What this phase does NOT do

**No real writer is implemented in this phase.**  
No destructive code is added. No diskpart, dd, raw device handles, WriteFile, format, partition, mount, unmount, or any byte-level write to any block device is introduced. This document is a blueprint. The construction crew has not been hired yet.

---

## 2. Threat Model

A USB image writer is a rare class of software where a single incorrect operation can irreversibly destroy user data. Every threat below must be addressed before a write engine is permitted to exist.

### 2.1 Wrong target drive selected

**Threat:** The user selects a drive path that refers to a different physical device than they intended — for example, a secondary internal SSD, a NAS mount, or a network drive appearing as a local volume.

**Required mitigations:**
- Drive eligibility check must classify the drive as removable/external before any gate can pass.
- Device identity lock must be established at scan time and re-verified immediately before arming.
- User must type the exact drive path and label during confirmation — no dropdown selection alone is sufficient.

### 2.2 OS / system drive selected

**Threat:** The user selects `C:\`, `/`, or any volume flagged as the active OS boot partition.

**Required mitigations:**
- `is_system_drive` flag must be checked and must be `false` before any planning step proceeds.
- System drive detection must be performed at the OS level (Win32 GetSystemDirectory, macOS `diskutil info`, Linux `/proc/mounts`), not inferred from drive letter alone.
- Any positive `is_system_drive` result is a permanent block for that session — no override, no confirmation bypass.

### 2.3 Removable drive identity changing between scan and write

**Threat:** A USB drive is scanned for eligibility, then removed and replaced with a different drive (or the same drive repositioned to a different port) before the write begins. The writer would then target the wrong device.

**Required mitigations:**
- Device identity hash must be computed at scan time.
- A fresh rescan must be performed immediately before the writer is armed (`armed_pending_confirmation` state).
- Identity hash must match between the original scan and the pre-arm rescan. Any mismatch aborts and requires full re-scan from idle.

### 2.4 Drive removed and reinserted during arming window

**Threat:** Drive is physically unplugged and replugged between confirmation and write start, potentially receiving a new device handle or drive letter assignment.

**Required mitigations:**
- Confirmation token is invalidated immediately if any drive rescan event is detected before write start.
- Write is blocked if drive presence cannot be re-confirmed with matching identity hash.
- Platform-level device change notification must be monitored during the arming window.

### 2.5 Drive letter reassignment

**Threat:** On Windows, another drive may claim the same letter (e.g., `E:\`) between scan and write if the original drive is briefly disconnected.

**Required mitigations:**
- Identity lock must include volume serial number and hardware identifier, not drive letter alone.
- Pre-write rescan must re-resolve the drive letter to confirm it still maps to the original hardware identifier.
- Drive-letter-only path resolution is forbidden in the writer.

### 2.6 Image file modified after audit

**Threat:** The OS image file (ISO/IMG) is modified by another process between the audit step and the write step. The writer would then write an unaudited, possibly corrupt or tampered image.

**Required mitigations:**
- Image SHA256 is computed and locked at audit time.
- SHA256 must be recomputed immediately before write arm and compared to the locked value.
- Any mismatch aborts and requires full re-inspection from idle.
- Image file modification timestamp is also recorded and checked.

### 2.7 User misunderstanding the destructive action

**Threat:** The user clicks through a confirmation dialog without understanding that the target drive will be completely overwritten and all data destroyed.

**Required mitigations:**
- User must type the target drive path exactly — no pre-filled value, no copy-paste helper.
- User must type an exact destructive acknowledgement phrase.
- Warning screen must use unambiguous language (see Section 11).
- Countdown timer must be visible before the final arm button becomes active.
- No "quick confirm" or "remember this" option may exist.

### 2.8 App crash during write

**Threat:** The application process is killed, crashes, or is force-quit while a write is in progress. The drive is left in a partially written, non-bootable state.

**Required mitigations:**
- Write session audit trail must be flushed to disk at each chunk boundary, not only at completion.
- Crash recovery must detect incomplete sessions on next launch and present a `recovery_required` state to the user.
- The audit log must record `bytes_written` at each checkpoint so the extent of a partial write is known.

### 2.9 Partial write failure

**Threat:** The write engine completes some chunks but fails partway through due to a drive error, write-protection flag, or OS error. The drive is left in an indeterminate state.

**Required mitigations:**
- Each chunk write is followed by a read-back verification step (future implementation).
- On any chunk failure the writer transitions to `failed` state immediately — no retry loop that could further corrupt the drive.
- Audit log records the last successful chunk index.

### 2.10 Power loss during write

**Threat:** Host machine loses power or the user's laptop battery dies during an active write.

**Required mitigations:**
- Write session checkpoint file is written to host disk at each chunk so that on restart the application can detect an incomplete write and show `recovery_required`.
- The drive is assumed corrupted after power loss — no auto-resume, no silent retry.

### 2.11 Platform differences (Windows / macOS / Linux)

**Threat:** Raw device write semantics differ significantly across platforms. A write path that works safely on macOS may silently corrupt data on Windows, or vice versa.

**Required mitigations:**
- Platform-specific write paths must be implemented and tested separately (see Section 8).
- No cross-platform abstraction layer may hide the underlying device access method.
- Platform detection must occur at session start. Unsupported platform transitions to `failed` before any write gate opens.

### 2.12 Malicious path or symlink edge cases

**Threat:** A crafted symlink, junction point, or path traversal could cause the writer to target a different device than the path string suggests. On Windows, paths like `\\.\PhysicalDrive0` could be passed in place of a drive letter.

**Required mitigations:**
- All drive paths must be resolved to their canonical real path before eligibility check.
- Paths beginning with `\\.\`, `/dev/`, or any raw device prefix must be rejected unless they have been explicitly resolved and classified as removable by the eligibility layer.
- Symlinks and junction points must be detected and rejected or resolved before any identity lock is established.
- Path length and character set must be validated before use.

---

## 3. Writer State Machine

The following states define the complete lifecycle of a future write session. No state beyond `simulation_passed` is implemented in Phase 4B or earlier.

```
idle
  │
  ▼
image_selected
  │  (image inspection passes)
  ▼
drive_selected
  │  (drive eligibility passes)
  ▼
safety_scanned
  │  (drive safety check passes — not system, not fixed, not oversized)
  ▼
plan_generated
  │  (dry-run write plan generated — Phase 3A)
  ▼
audit_passed
  │  (plan audit validation passes — Phase 3B)
  ▼
simulation_passed
  │  (null-device mock writer completes without error — Phase 4A)
  ▼
armed_pending_confirmation
  │  (fresh device rescan performed, identity hash re-verified,
  │   image hash re-verified, confirmation UI presented)
  ▼
final_confirmation_required
  │  (user must type drive path, acknowledgement phrase,
  │   confirm image hash, confirm capacity, confirm destruction)
  ▼
writing_locked          ← FUTURE IMPLEMENTATION ONLY. Does not exist yet.
  │  (all gates passed, confirmation token valid, write engine armed)
  ▼
writing_in_progress     ← FUTURE IMPLEMENTATION ONLY. Does not exist yet.
  │  (chunked write executing, checkpoints flushing, progress emitting)
  ▼
verify_written_image    ← FUTURE IMPLEMENTATION ONLY. Does not exist yet.
  │  (post-write SHA256 verification of written data)
  ▼
completed
  │  (write and verification successful, audit log sealed)
  │
  ├── failed            (any gate failure, write error, or verification mismatch)
  ├── cancelled         (user cancelled before or during write)
  └── recovery_required (crash or power loss detected — incomplete write on disk)
```

### State transition rules

- Any state may transition to `failed` or `cancelled` at any point.
- `recovery_required` may only be entered from `writing_in_progress` via crash detection.
- `armed_pending_confirmation` may only be entered after `simulation_passed`.
- `writing_locked` may only be entered after all gates in `final_confirmation_required` pass.
- **`writing_in_progress` does not exist in this codebase. It is future design only.**
- No state may skip `audit_passed` or `simulation_passed` to reach `writing_locked`.

---

## 4. Confirmation Gate Design

The confirmation gate is the last human checkpoint before a write is physically armed. It must be impossible to accidentally pass.

### Required confirmation steps (all mandatory, in order)

1. **Type the target drive path exactly.**  
   The user must type the full drive path (e.g., `E:\` on Windows, `/dev/disk4` on macOS) into a text input field with no pre-filled value, no autocomplete, and no copy-paste shortcut from the UI.  
   The typed value must match the scanned drive path exactly, case-normalized per platform.

2. **Type the destructive acknowledgement phrase.**  
   The user must type the exact string: `I understand all data on this drive will be destroyed`  
   The phrase must be matched exactly. Partial matches, case-insensitive matches, or whitespace-trimmed matches are not accepted.

3. **Confirm the image SHA256.**  
   The full SHA256 of the image file must be displayed. The user must check a checkbox explicitly acknowledging they have verified the hash. No auto-check, no default-checked state.

4. **Confirm the target drive capacity.**  
   The total capacity of the drive in GB (e.g., `32.0 GB`) must be displayed. The user must type this value exactly into a separate confirmation field.

5. **Confirm all data will be destroyed.**  
   A separate explicit checkbox: `I confirm that all data currently on this drive will be permanently destroyed and cannot be recovered.` This may not be pre-checked.

6. **Observe the countdown.**  
   After all five steps above are satisfied, a countdown timer (minimum 10 seconds) counts down visibly before the arm button becomes active. The countdown resets if any input field is modified.

### Confirmation token properties

- A confirmation token is generated only after all six steps above complete.
- The token includes a HMAC of: drive identity hash + image identity hash + confirmation timestamp + acknowledgement phrase hash.
- Token expires after 60 seconds.
- Token is single-use — it is consumed when the write engine is armed.
- Token is invalidated immediately if:
  - A drive change event is detected on the system.
  - The drive rescan returns a different identity hash.
  - The image file modification timestamp changes.
  - The image SHA256 changes.
  - The application window loses focus (configurable — recommended for Phase 4C).

---

## 5. Device Identity Lock Design

A device identity lock is a snapshot of all stable identifying characteristics of a target drive, taken at safety scan time. It must be re-verified immediately before write arm.

### Identity lock fields

| Field | Description |
|---|---|
| `root_path` | Canonical resolved path to drive root (e.g., `E:\`, `/dev/disk4s1`) |
| `volume_label` | OS-reported volume name |
| `filesystem` | Filesystem type (e.g., `FAT32`, `exFAT`, `NTFS`, `HFS+`) |
| `total_capacity_bytes` | Total capacity in bytes (not GB — exact integer) |
| `removable_classification` | `removable` \| `external` \| `fixed` \| `unknown` |
| `is_system_drive` | Boolean — must be `false` for any gate to pass |
| `hardware_id` | OS-level hardware identifier (see platform notes below) |
| `volume_serial` | OS-reported volume serial number |
| `stable_os_id` | Platform-specific stable device identifier (see below) |
| `scan_timestamp` | ISO 8601 UTC timestamp of when the identity was captured |
| `identity_hash` | SHA256 of the canonical concatenation of all above fields |

### Platform-specific stable ID sources

| Platform | Stable ID source |
|---|---|
| Windows | `DeviceIoControl` IOCTL_STORAGE_QUERY_PROPERTY → StorageDeviceProperty → SerialNumberOffset; or WMI `Win32_DiskDrive.SerialNumber` |
| macOS | `diskutil info` → `IORegistryEntryName` + `VolumeUUID` + `DiskUUID` |
| Linux | `/dev/disk/by-id/` symlink target; or `udevadm info` `ID_SERIAL` attribute |

### Rescan requirement

The identity lock must be **re-established by a fresh scan** immediately before transitioning to `armed_pending_confirmation`. The fresh scan result is compared field-by-field to the original lock. Any field mismatch blocks the transition and resets to `idle`.

---

## 6. Image Identity Lock Design

An image identity lock is a snapshot of all identifying properties of the OS image file, taken at inspection/audit time. It must be re-verified immediately before write arm.

### Identity lock fields

| Field | Description |
|---|---|
| `image_path` | Absolute canonical path to the image file |
| `filename` | Basename of the image file |
| `extension` | File extension (`.iso`, `.img`, `.dmg`, `.bin`, `.raw`) |
| `size_bytes` | File size in bytes at inspection time |
| `sha256` | SHA256 hash of the complete file |
| `modified_timestamp` | OS-reported file modification timestamp at inspection time |
| `audit_timestamp` | ISO 8601 UTC timestamp of when the inspection was run |
| `image_identity_hash` | SHA256 of the canonical concatenation of all above fields |

### Invalidation rules

The image identity lock is invalidated and requires full re-inspection if:
- The file modification timestamp changes.
- The file size changes.
- The SHA256 recomputed immediately before write arm does not match the locked value.
- The file is renamed, moved, or deleted.
- The audit timestamp is older than a configurable threshold (recommended: 60 minutes).

---

## 7. Real Writer Boundary Rules

The following rules are **permanently blocking**. No configuration option, command-line flag, or user confirmation may override them. They are to be enforced in code as pre-conditions checked before any write-engine code path is reachable.

| Rule | Condition | Effect if violated |
|---|---|---|
| R1 | `audit_passed` must be `true` | Abort — transition to `failed` |
| R2 | `simulation_passed` must be `true` | Abort — transition to `failed` |
| R3 | Fresh device rescan must have occurred within 30 seconds | Abort — require rescan |
| R4 | Final typed confirmation must be valid and unexpired | Abort — require re-confirmation |
| R5 | `is_system_drive` must be `false` | Permanent block for this session |
| R6 | `removable_classification` must be `removable` or `external` | Permanent block |
| R7 | Device identity hash must match between scan and pre-arm rescan | Abort — reset to idle |
| R8 | Image SHA256 must match between audit and pre-arm recheck | Abort — reset to idle |
| R9 | Target must not be classified as `fixed` or `internal` | Permanent block |
| R10 | Total capacity must not exceed platform-specific safety ceiling (e.g., 256 GB) | Permanent block |
| R11 | Target path must not resolve to the OS root partition | Permanent block |
| R12 | Confirmation token must not be reused | Abort — require new confirmation |
| R13 | Confirmation token must not be expired | Abort — require new confirmation |
| R14 | Platform must be a supported write target (Windows / macOS / Linux) | Abort — unsupported platform |

---

## 8. Platform-Specific Writer Plan (Design Only)

**No code is written in this section.** These are design targets only, describing how a future real write engine would be implemented per platform. None of this exists.

### 8.1 Windows (future)

- Device path format: `\\.\PhysicalDriveN` resolved from drive letter via `CreateFile` with `GENERIC_WRITE` + `FILE_FLAG_NO_BUFFERING`.
- Requires Administrator elevation. Elevation must be requested and granted before any write path is accessible.
- Write loop: `WriteFile` in chunk-aligned blocks (512-byte or 4096-byte sector alignment required).
- Drive must be dismounted before raw write (`FSCTL_LOCK_VOLUME`, `FSCTL_DISMOUNT_VOLUME`).
- Post-write: `FSCTL_UNLOCK_VOLUME`, then hash verification pass via `ReadFile`.
- Error handling: `GetLastError()` captured at each `WriteFile` call — any non-zero result transitions to `failed`.

### 8.2 macOS (future)

- Device path format: `/dev/rdiskN` (raw disk, not `/dev/diskN`) for performance.
- Requires root or explicit user authorization via `AuthorizationCreate` / `SMJobBless` or a privileged helper tool.
- Unmount required before write: `diskutil unmountDisk /dev/diskN`.
- Write loop: `dd`-equivalent via direct `write()` syscall or Python `os.write()` in 1 MB chunks, not via subprocess `dd`.
- Post-write: SHA256 of `/dev/rdiskN` output compared to image SHA256.
- Error handling: `errno` captured at each `write()` call.

### 8.3 Linux (future)

- Device path format: `/dev/sdX` or `/dev/mmcblkX` resolved from device enumeration.
- Requires root or `CAP_SYS_RAWIO` capability.
- Unmount required: `umount` for all mounted partitions on the device.
- Write loop: direct `write()` syscall in sector-aligned chunks.
- Post-write: SHA256 of raw device read-back compared to image SHA256.
- Kernel block device flush required: `fsync()` + `ioctl(BLKFLSBUF)` after write.
- Error handling: `errno` at each syscall.

### Platform gate

Before entering any platform-specific write path, the platform must be explicitly detected and matched against a supported list. Any unsupported platform (e.g., FreeBSD, Cygwin, WSL running as the write host) transitions immediately to `failed`.

---

## 9. Failure and Recovery Model

### 9.1 Pre-write failure

Cause: Any gate check fails before `writing_locked` is reached.  
Effect: Session transitions to `failed`. Drive is not modified. Audit log records the failed gate and reason. No recovery action required on the drive.

### 9.2 Write interrupted (mid-write error)

Cause: `WriteFile` / `write()` returns an error mid-session.  
Effect: Session transitions to `failed`. Drive is in a partially written state. Audit log records: last successful chunk index, bytes written, error code, timestamp.  
User action required: Drive must be reformatted before reuse. Application presents `recovery_required` screen with explicit statement that the drive is in an indeterminate state.

### 9.3 Verification failure

Cause: Post-write SHA256 of written data does not match image SHA256.  
Effect: Session transitions to `failed`. Audit log records expected hash vs. actual hash.  
User action required: Write must be repeated from scratch after drive reformat. Application warns that the current drive state may be partially corrupt.

### 9.4 Cancelled before write

Cause: User cancels at any state before `writing_locked`.  
Effect: Session transitions to `cancelled`. Drive is not modified. Audit log records cancellation point and timestamp.

### 9.5 Cancelled during write (future)

Cause: User initiates cancel while `writing_in_progress`.  
Effect: Write is halted at the next safe chunk boundary. Session transitions to `cancelled`. Drive is in a partially written state and must be treated identically to an interrupted write. Audit log records bytes written at cancel point.

### 9.6 Drive disconnect during write (future)

Cause: Physical drive removal event detected while `writing_in_progress`.  
Effect: Session transitions to `failed` immediately. OS-level write error is expected to follow. Audit log records disconnect event timestamp and bytes written at last checkpoint.

### 9.7 App crash

Cause: Application process exits unexpectedly (SIGKILL, force quit, Windows task-kill).  
Effect: Checkpoint file on host disk records the last confirmed write state. On next application launch, checkpoint file is detected and session is presented as `recovery_required`. User is informed the drive was being written and is now in an indeterminate state.

### 9.8 Audit trail preservation

Regardless of outcome, the following must survive any failure mode:
- Audit log file written to host disk with session ID as filename.
- Checkpoint file (JSON) updated at each chunk boundary.
- Both files must be written with `fsync()` / `FlushFileBuffers()` after each update, not buffered.
- Audit log is never deleted by the application, only by explicit user action.

### 9.9 Recovery evidence bundle

On `recovery_required` or `failed` state, the application must offer to export a recovery evidence bundle containing:
- Session audit log.
- Device identity lock snapshot.
- Image identity lock snapshot.
- Checkpoint file.
- Platform information.
- Failure reason and error codes.

This bundle extends the evidence export model from Phase 3C.

---

## 10. Audit Log Schema Proposal

The following JSON schema defines the audit record for a future write session. No write session exists yet. This is a forward-design specification.

```json
{
  "schema": "bootforge.write_session_audit.v1",
  "writer_session_id": "<uuid4>",
  "plan_id": "<bootforge-plan-xxxxxxxx>",
  "plan_hash": "<sha256>",
  "device_identity_hash": "<sha256>",
  "image_identity_hash": "<sha256>",
  "confirmation_token_hash": "<sha256-of-confirmation-token>",
  "platform": "win32 | darwin | linux",
  "start_time": "<ISO8601-UTC>",
  "end_time": "<ISO8601-UTC | null>",
  "status": "completed | failed | cancelled | recovery_required",
  "bytes_expected": 0,
  "bytes_written": 0,
  "last_checkpoint_chunk": 0,
  "chunk_size": 1048576,
  "chunks_total": 0,
  "chunks_completed": 0,
  "verification_result": "passed | failed | skipped | null",
  "verification_sha256_expected": "<sha256 | null>",
  "verification_sha256_actual": "<sha256 | null>",
  "failure_reason": "<string | null>",
  "failure_error_code": "<platform-error-code | null>",
  "destructive_operation_declared": true,
  "user_acknowledgement_record": {
    "drive_path_typed": "<string>",
    "acknowledgement_phrase_hash": "<sha256-of-typed-phrase>",
    "image_hash_confirmed": true,
    "capacity_confirmed": true,
    "destruction_confirmed": true,
    "confirmation_timestamp": "<ISO8601-UTC>",
    "token_expiry_timestamp": "<ISO8601-UTC>"
  },
  "gates_passed": {
    "audit_passed": true,
    "simulation_passed": true,
    "device_rescan_fresh": true,
    "identity_hash_matched": true,
    "image_hash_matched": true,
    "confirmation_valid": true,
    "is_not_system_drive": true,
    "is_removable": true,
    "capacity_within_ceiling": true
  }
}
```

### Schema version policy

The schema version string (`bootforge.write_session_audit.v1`) must be incremented if any field is added, removed, or changes type. Audit logs from older schema versions must remain readable by the application but are not required to be writable.

---

## 11. UX Safety Copy

The following text must appear on the future writer confirmation screen, verbatim. No summarization, no softening, no abbreviation.

### Primary warning header
```
⚠ PERMANENT DATA DESTRUCTION WARNING
```

### Warning body
```
You are about to write an operating system image to the following device:

  Drive:     [DRIVE LABEL] ([DRIVE PATH])
  Capacity:  [TOTAL GB] GB
  Image:     [IMAGE FILENAME]
  SHA256:    [IMAGE SHA256]

THIS ACTION WILL PERMANENTLY AND IRREVERSIBLY DESTROY ALL DATA ON THE
TARGET DRIVE. THIS CANNOT BE UNDONE. NO BACKUP WILL BE CREATED
AUTOMATICALLY. ONCE THE WRITE BEGINS, YOUR DATA IS GONE.

Do not proceed if you are not certain this is the correct drive.
Do not proceed if you have not verified the SHA256 hash of the image.
Do not proceed if this drive contains data you have not backed up.
```

### Typed confirmation fields

```
To confirm, type the drive path exactly:
[ text input — no pre-fill ]

Type the following phrase exactly:
"I understand all data on this drive will be destroyed"
[ text input — no pre-fill ]

Verify the image SHA256:
[ SHA256 displayed ] [ ✓ I have verified this hash — checkbox, unchecked by default ]

Confirm drive capacity:
[ type the capacity in GB, e.g. "32.0 GB" — text input ]

[ ✓ I confirm that all data currently on this drive will be permanently
  destroyed and cannot be recovered. — checkbox, unchecked by default ]
```

### Countdown notice
```
All confirmations satisfied. Write arm available in [N] seconds.
Do not unplug the drive.
```

### Final arm button label
```
ARM WRITE — IRREVERSIBLE
```
*(button is disabled until countdown completes and all fields are valid)*

### Post-write screen (success)
```
Write complete.
[DRIVE PATH] has been written with [IMAGE FILENAME].
Verification: PASSED (SHA256 confirmed)
Session ID: [SESSION ID]
Audit log saved to: [PATH]
```

### Post-write screen (failure)
```
Write FAILED.
[DRIVE PATH] is in an indeterminate state. Do not use this drive until
it has been reformatted.

Failure reason: [REASON]
Bytes written:  [N] of [TOTAL]
Session ID:     [SESSION ID]
Recovery evidence bundle: [ Export Bundle ]
```

---

## 12. Explicit Non-Goals for Phase 4B

The following capabilities are explicitly **out of scope** for Phase 4B and all prior phases. They do not exist in the codebase and must not be introduced without a separate architecture gate and explicit user approval.

| Non-goal | Status |
|---|---|
| Real writer implementation | ❌ Not implemented — future Phase 4C+ |
| Destructive writes to any block device | ❌ Blocked permanently until Phase 4C |
| `diskpart` integration (Windows) | ❌ Not implemented |
| `dd` subprocess integration | ❌ Not implemented |
| Raw device handle opening (`\\.\PhysicalDriveN`, `/dev/rdiskN`) | ❌ Not implemented |
| Formatting / filesystem creation | ❌ Not implemented |
| Partition table creation or modification | ❌ Not implemented |
| Mount / unmount automation | ❌ Not implemented |
| Bootloader writing (GRUB, rEFInd, syslinux, Windows BCD) | ❌ Not implemented |
| Post-write partition resizing | ❌ Not implemented |
| Drive erase / secure wipe | ❌ Not implemented |

---

## 13. Phase 4B Exit Criteria

Phase 4C (Real Writer Implementation) may not begin until **all** of the following are true:

| Exit criterion | Required state |
|---|---|
| EC1 | This architecture document is committed, tagged, and reviewed. |
| EC2 | The threat model in Section 2 has been reviewed and no unaddressed threat remains. |
| EC3 | The state machine in Section 3 has been reviewed and all transitions are agreed upon. |
| EC4 | The confirmation gate in Section 4 has been reviewed and the minimum steps are agreed upon. |
| EC5 | The device identity lock schema in Section 5 is agreed upon for the target platform. |
| EC6 | The image identity lock schema in Section 6 is agreed upon. |
| EC7 | All boundary rules in Section 7 are agreed upon and none have been relaxed without explicit documented justification. |
| EC8 | The platform-specific write paths in Section 8 have been selected and the implementation approach for each supported platform is agreed upon. |
| EC9 | The failure and recovery model in Section 9 is agreed upon. |
| EC10 | The audit log schema in Section 10 is agreed upon. |
| EC11 | The UX safety copy in Section 11 has been reviewed and no wording changes that reduce user clarity are accepted. |
| EC12 | A new branch `phase4c/real-writer-implementation` is created from `usb-creator-foundation-lock` only after all above criteria are met. |
| EC13 | The user explicitly confirms Phase 4C may begin in writing (in the project conversation). |

### What does NOT satisfy the exit criteria

- "We tested it and it worked" — without architecture review complete.
- "The mock writer already handles this" — Phase 4A is simulation only and establishes no precedent for the real writer's safety properties.
- Any partial implementation of a real write path sneaked into a documentation branch. If code that opens a device handle, calls WriteFile, or invokes diskpart/dd is found on any branch before Phase 4C is explicitly authorized, it is to be reverted and treated as a safety incident.

---

*End of Phase 4B: Real Writer Architecture Gate*  
*No real writer exists. No destructive capability exists. This document is a design specification only.*
