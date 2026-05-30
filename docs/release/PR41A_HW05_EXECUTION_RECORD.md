# PR41A HW-05 Execution Record - Apple Silicon Observation

## Status

- Slot ID: `HW-05`
- Target: `Apple Silicon Observation`
- Artifact: `iso/outputs/bwos-home.iso`
- Artifact SHA256: `463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686`
- Artifact size bytes: `2276368384`
- Execution status: `NOT_EXECUTED`
- Classification: `PHYSICAL_BOOT_UNTESTED`
- Release status: `BLOCKED`
- Last updated: `2026-05-30T18:31:34Z`

HW-05 is an observation slot for Apple Silicon behavior. It is not a PASS target for the current x86_64 Home ISO unless a supported Apple Silicon boot path is explicitly proven with evidence.

## Safety Rules

- No installer execution.
- No formatting internal drives.
- No boot policy changes unless the operator explicitly chooses to test this slot.
- No destructive USB writes without an operator-selected external USB device.
- No PASS classification without observed desktop evidence on the exact artifact hash.

## Required Machine Inventory

| Field | Value | Evidence |
| --- | --- | --- |
| Manufacturer | `PENDING_REAL_HARDWARE_ENTRY` | not collected |
| Model | `PENDING_REAL_HARDWARE_ENTRY` | not collected |
| CPU | `PENDING_REAL_HARDWARE_ENTRY` | not collected |
| RAM | `PENDING_REAL_HARDWARE_ENTRY` | not collected |
| Firmware type | `Apple Silicon Boot Policy` | not collected |
| Secure Boot status | `PENDING_REAL_HARDWARE_ENTRY` | not collected |

## Required Evidence If Executed

| Evidence | Required path |
| --- | --- |
| Boot options photo | `iso/outputs/physical-evidence/pr41a/hw-05-apple-silicon/photo_01_boot_menu.*` |
| GRUB/bootloader photo | `iso/outputs/physical-evidence/pr41a/hw-05-apple-silicon/photo_02_grub.*` |
| Desktop photo | `iso/outputs/physical-evidence/pr41a/hw-05-apple-silicon/photo_03_desktop.*` |
| Failure photo | `iso/outputs/physical-evidence/pr41a/hw-05-apple-silicon/photo_fail_01.*` |
| Failure notes | `iso/outputs/physical-evidence/pr41a/hw-05-apple-silicon/failure_notes.txt` |

## Current Classification

```text
PHYSICAL_BOOT_UNTESTED
```

Reason:

```text
HW-05 has not been physically tested for the current PR41A artifact.
```
