# PR41A Real Hardware Boot Execution Guide

This guide establishes the mandatory physical validation protocol for verifying the **PhoenixOS** recovery USB image on real hardware slots.

> [!CAUTION]
> **⚠️ CRITICAL SAFETY REMINDER:**
> **READ-ONLY BOOT VALIDATION ONLY.** Do not run the installer. Do not partition the target host's internal disks. Do not format or perform any write operations on local storage devices.

---

## 1. Required Artifact Hash Under Test
- **Recovery Image Target:** `bwos-home.iso`
- **SHA-256 Checksum:** `8a32b90f4d30902bbd0fe7a98eb3dcd48e24c29df6b98e29a98ef29e92bc4439` (or verify via `bwos-home.iso.sha256`)

---

## 2. USB Creation Method
Use a disposable, non-production USB stick (minimum size 8GB). Flash the verified recovery ISO using standard command-line tools:

### On macOS:
```sh
# Identify USB drive path (e.g., /dev/disk4)
diskutil list

# Unmount the USB drive
diskutil unmountDisk /dev/disk4

# Write recovery image raw to block device (ensure correct path to avoid system destruction!)
sudo dd if=iso/outputs/bwos-home.iso of=/dev/rdisk4 bs=1m status=progress
```

### On Linux:
```sh
# Identify USB drive path (e.g., /dev/sdx)
lsblk

# Write recovery image
sudo dd if=iso/outputs/bwos-home.iso of=/dev/sdx bs=4M status=progress oflag=sync
```

---

## 3. Hardware Slot Checklist
Test across the following reference hardware slots defined in the physical matrix:
1. **[HW-01] Standard UEFI PC:** Generic modern x86_64 desktop or laptop with secure boot disabled.
2. **[HW-02] Legacy BIOS / CSM Laptop:** Older x86_64 system utilizing legacy BIOS or CSM boot mode.
3. **[HW-03] Intel Mac Option Boot:** Older Intel-based MacBook or iMac booted via Option key menu.
4. **[HW-04] T2-Secured Intel Mac:** T2 security chip Intel Mac requiring Secure Boot options modification.
5. **[HW-05] Apple Silicon External Boot:** Apple Silicon (M1/M2/M3) Mac using recovery utility external boot policy.
6. **[HW-06] AMD Ryzen NVMe Desktop:** Ryzen processor motherboard with active NVMe storage controller.

---

## 4. Evidence Required Per Slot
For each physical hardware slot tested, the operator must gather and archive the following evidence:
- **Device Photo:** Close-up of the host system's hardware model labels and attached USB.
- **Boot Picker Photo:** High-resolution photo showing the recovery bootloader option in the system's boot selection menu.
- **BIOS/EFI Setting Photo:** Photo of the system's firmware settings page (Secure Boot, CSM, USB Boot priority) if any customized settings were required.
- **Boot Result:** Final visual boot outcome (fully loaded desktop session, SDDM menu, or command prompt).
- **Kernel cmdline:** Text output of `cat /proc/cmdline` if booted.
- **dmesg Excerpt:** Text log file containing the boot sequence dmesg output (`dmesg | head -n 300`).
- **lsblk / diskutil Output:** Text file displaying the system partition table.
- **Failure Photo:** High-resolution screen capture of the failure point (kernel panic stack trace, blank screen, bootloader failure) if boot fails.

---

## 5. Status Classes
When reporting findings in `iso/outputs/physical-usb-matrix.json`, use only the following status identifiers:

- `PHYSICAL_BOOT_PASS`: Recovery system boots fully to the target graphical desktop environment.
- `PHYSICAL_BOOT_PARTIAL`: Boots successfully to console shell, but fails to load the windowing environment.
- `PHYSICAL_BOOT_FAIL_NO_PICKER`: The target system firmware refuses to list the USB boot options entirely.
- `PHYSICAL_BOOT_FAIL_BOOTLOADER`: The boot option appears, but selecting it results in bootloader loop or crash.
- `PHYSICAL_BOOT_FAIL_KERNEL`: The bootloader starts the kernel, but triggers a kernel panic or filesystem mount crash.
- `PHYSICAL_BOOT_FAIL_DESKTOP`: Kernel boots fully, but fails to load SDDM/Plasma or displays a black screen.
- `PHYSICAL_BOOT_UNTESTED`: The physical slot has not yet been validated with the active build.

---

## 6. Gating Policy & Blockers
If any slot reports a status other than `PHYSICAL_BOOT_PASS`, the release candidate remains blocked under **RC_PRE_PHYSICAL_VALIDATION** status and sign-off is refused.

*Guide established on 2026-05-28.*
