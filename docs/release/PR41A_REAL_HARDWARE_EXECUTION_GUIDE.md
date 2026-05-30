# PR41A Real Hardware Validation Execution Guide

## Objective

Collect real physical boot evidence for Phoenix OS using the current Home ISO.

This is read-only validation. It is not an install test.

## Artifact Under Test

- ISO path: `iso/outputs/bwos-home.iso`
- SHA256: `463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686`
- Size bytes: `2276368384`

Verify before writing any removable USB:

```sh
shasum -a 256 iso/outputs/bwos-home.iso
```

## Safety Rules

- Do not run the installer.
- Do not format internal drives.
- Do not partition internal drives.
- Do not run disk repair tools.
- Do not write to host disks.
- Do not classify PASS without desktop evidence.
- Stop after completing the first hardware slot unless explicitly instructed to continue.

## Target Order

1. `HW-01` Standard UEFI PC
2. `HW-06` Ryzen Desktop
3. `HW-03` Intel Mac
4. `HW-04` T2 Mac
5. `HW-05` Apple Silicon Observation

`HW-02` legacy BIOS remains a deferred slot and is not part of the current PR41A target order.

## Step 1 - Record Target Machine

For the active slot, record:

- Manufacturer
- Model
- CPU
- RAM
- Firmware type: UEFI, BIOS, Apple EFI, or Apple Silicon Boot Policy
- Secure Boot status

Do not use example hardware profiles as evidence.

## Step 2 - Create Phoenix USB

Only image a clearly identified external removable USB device.

Required record:

- USB make/model
- USB capacity
- USB device path
- ISO SHA256

macOS read-only discovery:

```sh
diskutil list
system_profiler SPUSBDataType
```

macOS destructive write, only after the operator confirms the external USB disk identifier:

```sh
diskutil unmountDisk /dev/diskN
sudo dd if=iso/outputs/bwos-home.iso of=/dev/rdiskN bs=1m status=progress
sync
```

Linux read-only discovery:

```sh
lsblk -o NAME,MODEL,SIZE,TRAN,TYPE,MOUNTPOINTS
```

Linux destructive write, only after the operator confirms the external USB device:

```sh
sudo dd if=iso/outputs/bwos-home.iso of=/dev/sdX bs=4M status=progress oflag=sync
sync
```

## Step 3 - Attempt Boot

Capture:

- `photo_01_boot_menu`
- `photo_02_grub`
- `photo_03_desktop`

If failed, capture:

- `photo_fail_01`
- `failure_notes.txt`

## Step 4 - If Desktop Loads

Collect these from the live session:

```sh
uname -a
cat /proc/cmdline
lsblk
journalctl -b | tail -200
```

Launch and record:

- Firefox
- Dolphin
- Konsole

## Step 5 - Classification

Allowed classifications:

- `PHYSICAL_BOOT_PASS`: Desktop reached with evidence.
- `PHYSICAL_BOOT_PARTIAL`: Boot progressed but did not fully satisfy desktop evidence.
- `PHYSICAL_BOOT_FAIL_NO_PICKER`: Firmware did not list the USB.
- `PHYSICAL_BOOT_FAIL_BOOTLOADER`: USB selected but GRUB/bootloader failed.
- `PHYSICAL_BOOT_FAIL_KERNEL`: Kernel failed after bootloader handoff.
- `PHYSICAL_BOOT_FAIL_DESKTOP`: Kernel/init reached but desktop failed.
- `PHYSICAL_BOOT_UNTESTED`: No physical attempt executed yet.

## Current HW-01 State

`HW-01` remains `PHYSICAL_BOOT_UNTESTED`. No USB image write or physical boot attempt was executed in this update.
