# PR41A HW-01 Execution Record - Standard UEFI PC

## Status

- Slot ID: `HW-01`
- Target: `Standard UEFI PC`
- Artifact: `iso/outputs/bwos-home.iso`
- Artifact SHA256: `463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686`
- Artifact size bytes: `2276368384`
- Execution status: `NOT_EXECUTED`
- Classification: `PHYSICAL_BOOT_UNTESTED`
- Release status: `BLOCKED`
- Last updated: `2026-05-30T18:31:34Z`

No physical boot PASS, PARTIAL, or FAIL status is recorded for HW-01 in this update. Real hardware evidence is still required.

## Safety Rules

- No installer execution.
- No formatting internal drives.
- No partitioning internal drives.
- No repair tools.
- No destructive USB writes without explicit operator-selected external USB device.
- No PASS classification without desktop evidence.

## Step 1 - Target Machine Inventory

Required evidence before test execution:

| Field | Value | Evidence |
| --- | --- | --- |
| Manufacturer | `PENDING_REAL_HARDWARE_ENTRY` | not collected |
| Model | `PENDING_REAL_HARDWARE_ENTRY` | not collected |
| CPU | `PENDING_REAL_HARDWARE_ENTRY` | not collected |
| RAM | `PENDING_REAL_HARDWARE_ENTRY` | not collected |
| Firmware type | `PENDING_REAL_HARDWARE_ENTRY` | not collected |
| Secure Boot status | `PENDING_REAL_HARDWARE_ENTRY` | not collected |

## Step 2 - Phoenix USB Creation

Source image:

```text
iso/outputs/bwos-home.iso
```

Verified source hash:

```text
463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686  iso/outputs/bwos-home.iso
```

USB media status:

| Field | Value |
| --- | --- |
| USB make/model | `NOT_SELECTED` |
| USB capacity | `NOT_SELECTED` |
| USB device node | `NOT_SELECTED` |
| USB write performed | `NO` |
| Reason | No explicit external USB device was available/selected for destructive imaging. |

Read-only host inventory on this Mac showed internal APFS disks and disk images only; no external USB mass-storage device was selected for imaging.

## Step 3 - Boot Attempt

No physical HW-01 boot attempt was executed in this session.

Required evidence paths once executed:

| Evidence | Required path |
| --- | --- |
| Boot menu photo | `iso/outputs/physical-evidence/pr41a/hw-01-standard-uefi-pc/photo_01_boot_menu.*` |
| GRUB photo | `iso/outputs/physical-evidence/pr41a/hw-01-standard-uefi-pc/photo_02_grub.*` |
| Desktop photo | `iso/outputs/physical-evidence/pr41a/hw-01-standard-uefi-pc/photo_03_desktop.*` |
| Failure photo | `iso/outputs/physical-evidence/pr41a/hw-01-standard-uefi-pc/photo_fail_01.*` |
| Failure notes | `iso/outputs/physical-evidence/pr41a/hw-01-standard-uefi-pc/failure_notes.txt` |

## Step 4 - Guest Evidence If Desktop Loads

These commands must be collected from the live session only after the desktop is reached:

```sh
uname -a
cat /proc/cmdline
lsblk
journalctl -b | tail -200
```

Application smoke tests required:

| App | Result | Evidence |
| --- | --- | --- |
| Firefox | `NOT_TESTED` | no physical boot |
| Dolphin | `NOT_TESTED` | no physical boot |
| Konsole | `NOT_TESTED` | no physical boot |

## Step 5 - Classification

Current classification:

```text
PHYSICAL_BOOT_UNTESTED
```

Reason:

```text
No external USB device was selected and no HW-01 physical boot evidence was collected.
```

Allowed future classifications:

- `PHYSICAL_BOOT_PASS`
- `PHYSICAL_BOOT_PARTIAL`
- `PHYSICAL_BOOT_FAIL_NO_PICKER`
- `PHYSICAL_BOOT_FAIL_BOOTLOADER`
- `PHYSICAL_BOOT_FAIL_KERNEL`
- `PHYSICAL_BOOT_FAIL_DESKTOP`

## Blockers

- External USB target must be selected by the operator before imaging.
- HW-01 hardware inventory must be recorded from the actual machine.
- Boot menu, GRUB, and desktop/failure photos are required before status can change.

## Recommended Next Hardware Target

Do not advance to HW-06 until HW-01 has one completed attempt package or the operator explicitly marks HW-01 unavailable. If HW-01 is unavailable, proceed to `HW-06 Ryzen Desktop` using the same evidence rules.
