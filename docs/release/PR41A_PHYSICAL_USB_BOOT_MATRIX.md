# PR41A — Physical USB Boot Matrix Validation Checklist

This document serves as the formal operator checklist and registry for **PR41A Physical USB Boot Matrix** validation. 

> [!CAUTION]
> **CRITICAL OPERATOR SAFETY NOTE:**
> * Physical boot testing is strictly a **read-only boot validation** exercise.
> * **DO NOT** run the installer on target physical machines.
> * **DO NOT** format internal drives or execute partition tables overrides.
> * **DO NOT** write to host target disks or perform any destructive actions.
> * This phase is restricted to **USB boot verification only**.

---

## 1. System Philosophy & Rules
* **No green check without evidence.** Any status change from `PHYSICAL_BOOT_NOT_TESTED` to a passing or partial state *must* have the corresponding hardware log evidence paths entered into this matrix.
* **Release Blocking Status**: All hardware slots are initialized as **release-blocking**. Successful clearance of the RC gate requires a verified boot pass on at least 3 distinct slots (including at least one legacy Mac and one UEFI PC).

---

## 2. Boot Status Classifications
Every hardware slot must be evaluated and categorized under one of the following official status classes:

* `PHYSICAL_BOOT_NOT_TESTED`: Initial state. No verification attempts made.
* `PHYSICAL_BOOT_PASS`: Complete boot cycle. Successful boot-menu loading, kernel loading, DM initialization, Plasma desktop reached, and clean ACPI shutdown verified.
* `PHYSICAL_BOOT_PARTIAL`: Boot successfully reached the display manager or desktop but experienced stability issues, driver failures, or shutdown problems.
* `PHYSICAL_BOOT_FAIL_NO_PICKER`: The drive was not discovered or listed by the motherboard's native boot selection menu/picker.
* `PHYSICAL_BOOT_FAIL_BOOTLOADER`: The drive was selected, but the GRUB/Syslinux bootloader crashed, hung, or failed to render.
* `PHYSICAL_BOOT_FAIL_KERNEL`: GRUB successfully chainloaded, but the Linux kernel panicked, hung during early init, or failed to mount the squashfs root.
* `PHYSICAL_BOOT_FAIL_DESKTOP`: Kernel booted successfully, but the X11 display manager failed, or the Plasma desktop session failed to load/stabilize.
* `PHYSICAL_BOOT_UNSUPPORTED`: Hardware platform determined to be structurally incompatible (e.g., non-emulated arch boundaries).

---

## 3. Physical Hardware Slots & Checklist

### Slot 1: `x86_64_uefi_pc` (Standard UEFI PC)
* **Status**: `PHYSICAL_BOOT_NOT_TESTED`
* **Release Gate Blocking**: `true`
* **Validation Checklist & Evidence Parameters**:
  * [ ] **Device Model**: (e.g., Intel NUC8i5BEH)
  * [ ] **Firmware Mode**: UEFI (Secure Boot state)
  * [ ] **USB Controller Type**: (e.g., Intel xHCI)
  * [ ] **Boot Picker Photo/Screenshot**: (Link to captured media)
  * [ ] **Kernel Cmdline**: `/proc/cmdline` contents
  * [ ] **Dmesg Boot Excerpt**: (Early hardware init logs)
  * [ ] **lsblk/diskutil Output**: (Partition enumeration verification)
  * [ ] **Serial/Console Log**: (Telemetry dump link)
  * [ ] **Result Classification**: `PHYSICAL_BOOT_NOT_TESTED`
  * [ ] **Operator Notes**:

---

### Slot 2: `x86_64_legacy_bios_pc` (Legacy BIOS / CSM Laptop)
* **Status**: `PHYSICAL_BOOT_NOT_TESTED`
* **Release Gate Blocking**: `true`
* **Validation Checklist & Evidence Parameters**:
  * [ ] **Device Model**: (e.g., ThinkPad T420)
  * [ ] **Firmware Mode**: Legacy BIOS / CSM
  * [ ] **USB Controller Type**: (e.g., USB 2.0 Native EHCI)
  * [ ] **Boot Picker Photo/Screenshot**: (Link to captured media)
  * [ ] **Kernel Cmdline**: `/proc/cmdline` contents
  * [ ] **Dmesg Boot Excerpt**: (Early BIOS/ACPI init logs)
  * [ ] **lsblk/diskutil Output**: (MBR/GPT partition tables)
  * [ ] **Serial/Console Log**: (Console recording link)
  * [ ] **Result Classification**: `PHYSICAL_BOOT_NOT_TESTED`
  * [ ] **Operator Notes**:

---

### Slot 3: `intel_mac_option_boot` (Intel Mac Option Key Boot)
* **Status**: `PHYSICAL_BOOT_NOT_TESTED`
* **Release Gate Blocking**: `true`
* **Validation Checklist & Evidence Parameters**:
  * [ ] **Device Model**: (e.g., MacBook Air A1370)
  * [ ] **Firmware Mode**: Apple EFI (Legacy Hybrid MBR/GPT)
  * [ ] **USB Controller Type**: (e.g., Apple USB 2.0 EHCI)
  * [ ] **Boot Picker Photo/Screenshot**: (Link to Apple Boot Options Screen photo)
  * [ ] **Kernel Cmdline**: `/proc/cmdline` contents
  * [ ] **Dmesg Boot Excerpt**: (Apple hardware discovery logs)
  * [ ] **lsblk/diskutil Output**: (EFI System Partition details)
  * [ ] **Serial/Console Log**: (Serial logging output link)
  * [ ] **Result Classification**: `PHYSICAL_BOOT_NOT_TESTED`
  * [ ] **Operator Notes**:

---

### Slot 4: `t2_mac_external_boot` (T2-Secured Intel Mac)
* **Status**: `PHYSICAL_BOOT_NOT_TESTED`
* **Release Gate Blocking**: `true`
* **Validation Checklist & Evidence Parameters**:
  * [ ] **Device Model**: (e.g., MacBook Pro 15-inch 2018)
  * [ ] **Firmware Mode**: Apple EFI + T2 Security (Allowed External Boot)
  * [ ] **USB Controller Type**: (e.g., Thunderbolt 3 USB-C xHCI)
  * [ ] **Boot Picker Photo/Screenshot**: (Link to boot picker photo)
  * [ ] **Kernel Cmdline**: `/proc/cmdline` contents
  * [ ] **Dmesg Boot Excerpt**: (T2 security controller communication logs)
  * [ ] **lsblk/diskutil Output**: (Partition verification)
  * [ ] **Serial/Console Log**: (Console capture link)
  * [ ] **Result Classification**: `PHYSICAL_BOOT_NOT_TESTED`
  * [ ] **Operator Notes**:

---

### Slot 5: `apple_silicon_external_boot_observation` (ARM64 Hypervisor Observation)
* **Status**: `PHYSICAL_BOOT_NOT_TESTED`
* **Release Gate Blocking**: `true`
* **Validation Checklist & Evidence Parameters**:
  * [ ] **Device Model**: (e.g., Mac mini M1 2020)
  * [ ] **Firmware Mode**: Apple Silicon Boot ROM / Emulated x86_64 Guest
  * [ ] **USB Controller Type**: (e.g., Apple Type-C USB4)
  * [ ] **Boot Picker Photo/Screenshot**: (Link to boot manager capture)
  * [ ] **Kernel Cmdline**: `/proc/cmdline` contents if emulated
  * [ ] **Dmesg Boot Excerpt**: (Hypervisor virtual block logs)
  * [ ] **lsblk/diskutil Output**: (Disk util status)
  * [ ] **Serial/Console Log**: (Hypervisor console log link)
  * [ ] **Result Classification**: `PHYSICAL_BOOT_NOT_TESTED`
  * [ ] **Operator Notes**:

---

### Slot 6: `ryzen_nvme_desktop` (AMD Ryzen Desktop with NVMe Target)
* **Status**: `PHYSICAL_BOOT_NOT_TESTED`
* **Release Gate Blocking**: `true`
* **Validation Checklist & Evidence Parameters**:
  * [ ] **Device Model**: (e.g., AMD Ryzen 9 5900X Custom System)
  * [ ] **Firmware Mode**: UEFI Class 3 (Secure Boot Off)
  * [ ] **USB Controller Type**: (e.g., AMD X570 xHCI / USB 3.2 Gen 2)
  * [ ] **Boot Picker Photo/Screenshot**: (Link to UEFI boot menu)
  * [ ] **Kernel Cmdline**: `/proc/cmdline` contents
  * [ ] **Dmesg Boot Excerpt**: (NVMe controller init + storage logs)
  * [ ] **lsblk/diskutil Output**: (Host partition layouts)
  * [ ] **Serial/Console Log**: (Console telemetry link)
  * [ ] **Result Classification**: `PHYSICAL_BOOT_NOT_TESTED`
  * [ ] **Operator Notes**:

---

**Lead Release Architect**: `Antigravity AI Agent`  
*Current Schema Version:* `1.0.0`
