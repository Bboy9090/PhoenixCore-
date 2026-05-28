# PR41A — Forensic Evidence Capture Sheet Template

This template must be filled out in full by the operator for **every single physical boot validation attempt** made under the **PR41A Physical USB Boot Matrix**. 

> [!IMPORTANT]
> **SYSTEM PRINCIPLE: No green check without evidence.**
> This sheet represents the absolute forensic audit record. Do not omit any parameter. 

---

## 1. Run Metadata
* **Slot ID**: [e.g., HW-01 / x86_64_uefi_pc]
* **Operator Name**: [Full Name or Agent Handle]
* **Execution Timestamp**: [YYYY-MM-DDTHH:MM:SSZ (UTC)]
* **Booted Edition**: [e.g., Home Aurelia]
* **Artifact ISO Path**: [e.g., iso/releases/pr40-known-good/bwos-home.iso]
* **Artifact Hash (SHA256)**: [Must match the validation anchor: `463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686`]

---

## 2. Host USB & Target Controller Specs
* **Physical USB Drive Model**: [e.g., SanDisk Ultra USB 3.0 32GB]
* **USB Vendor ID / Product ID (VID:PID)**: [e.g., `0781:5581` - obtain via `lsusb` on Linux or `system_profiler SPUSBDataType` on Mac]
* **USB Partition Layout**: [e.g., GPT (GUID Partition Table) or MBR (Master Boot Record)]
* **USB Filesystem Format**: [e.g., FAT32 or exFAT System Partition]
* **Target System Port Used**: [e.g., Rear Native Panel USB 3.0 / Front Panel Hub / Type-C Direct Port]

---

## 3. Motherboard & Firmware Environment
* **Target Machine Model**: [e.g., Lenovo ThinkPad T420]
* **Processor (CPU) / Arch**: [e.g., Intel Core i5-2520M x86_64]
* **Installed RAM**: [e.g., 8 GB DDR3]
* **Motherboard Firmware Vendor / Version**: [e.g., Lenovo v1.52 (83ET82WW)]
* **Firmware Boot Mode**: [UEFI Class 3 / UEFI with CSM / Legacy BIOS Only / Apple EFI]
* **Secure Boot State**: [Enabled / Disabled / Unsupported]
* **Target Boot Option Hotkey**: [e.g., Held Option Key at chime / Pressed F12 at splash]

---

## 4. Boot Evidence & Outputs
* **Boot Picker Photo Reference**: [Path to captured photograph of the motherboard's boot selector displaying the USB drive: `evidence/media/...`]
* **Bootloader Rendered Output**: [Describe syslinux/grub loading screen behavior: Success / Hang / Graphical Glitch]
* **Boot Command Line (`/proc/cmdline`)**:
  ```txt
  # Paste complete guest-side kernel command line
  ```
* **Early Dmesg / ACPI Boot Excerpt**:
  ```txt
  # Paste critical early hardware/ACPI initialization console logs
  ```
* **Host Block Map Output (`lsblk` or `diskutil list`)**:
  ```txt
  # Paste target partition layout from guest context
  ```
* **Serial Telemetry Capture File**: [Link to captured raw output log from serial port if wired: `evidence/serial-HW-XX.log`]

---

## 5. Validation Outcome & Audit
* **Boot Classification**: [Choose one of: `PHYSICAL_BOOT_PASS` | `PHYSICAL_BOOT_PARTIAL` | `PHYSICAL_BOOT_FAIL_NO_PICKER` | `PHYSICAL_BOOT_FAIL_BOOTLOADER` | `PHYSICAL_BOOT_FAIL_KERNEL` | `PHYSICAL_BOOT_FAIL_DESKTOP` | `PHYSICAL_BOOT_UNSUPPORTED`]
* **Observed Anomalies**: [Detail any hardware drop-outs, graphics stutter, display resolution mismatch, thermal throttling, or system freezes]
* **Recovery Notes / Interventions**: [Detail if manual BIOS configuration tweaks, port swaps, or firmware overrides were necessary to force bootloader execution]
* **Audit Signature (Operator)**:

---

### Verification Checklist (Operator Verification)
- [ ] USB block write completed and verified via hash check.
- [ ] Motherboard Secure Boot state explicitly verified.
- [ ] External boot permissions validated in Startup Security Utility (if Mac T2).
- [ ] Serial capture terminal active and recording at `115200 8N1` (if applicable).
- [ ] Read-only boot rules strictly observed (NO local OS writes executed).
- [ ] System reports gathered and archived under evidence directories.
