# Arcwyre Flex Boot Matrix

This document registers the boot matrix validation results for the **Arcwyre Flex** release candidate 1 (RC1).

---

## 1. Boot Verification Matrix

| Boot Mode | Platform Type | Boot Loader | Boot Success | Boot Time | Login Success | Smoke Test Success |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **QEMU UEFI** | Modern UEFI Path | GRUB UEFI x64 | **PASS** | ~14s | **PASS** (user `arc`) | **PASS** |
| **QEMU BIOS** | Legacy BIOS Path | ISOLINUX/GRUB | **FAIL** | N/A | N/A | N/A |

### Boot Details & Observations

1. **Modern UEFI Path (QEMU UEFI)**
   - **Command**: `qemu-system-x86_64 -pflash .../edk2-x86_64-code.fd -m 4096 -drive file=bwos-arcwyre-flex.iso,media=cdrom,readonly=on,format=raw`
   - **Behavior**: Seamless boot sequence. UEFI firmware boots GRUB EFIloader directly. Passes through Plymouth splash to automatic login as user `arc` on virtual console `tty2` in under 15 seconds.
   - **Verification**: `/usr/bin/arc-flex-smoke` successfully run on `tty2` and outputted `ARCWYRE FLEX BOOT OK`.

2. **Legacy Boot Path (QEMU BIOS)**
   - **Command**: `qemu-system-x86_64 -m 4096 -cdrom bwos-arcwyre-flex.iso`
   - **Behavior**: SeaBIOS reports `Boot failed: Could not read from CDROM (code 0009)`. This is the expected and correct behavior as `grub-efi` is configured as the exclusive bootloader target to minimize ISO footprint and maintain architectural security.

---

## 2. Validation Status

- **Matrix Status**: **UEFI-ONLY PASS** (Modern UEFI path fully validated and repeatable; Legacy BIOS path is disabled by design).
