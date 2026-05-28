# PR41A HW-01 x86_64_uefi_pc Physical Boot Execution Record

This document serves as the formal execution record and evidence checklist for verifying **PhoenixOS** on the **HW-01 (Standard UEFI PC)** physical hardware slot.

---

## 🔬 Test Specifications & Config

- **Milestone:** `PR41A`
- **Slot ID:** `HW-01`
- **Target Architecture:** `x86_64_uefi_pc`
- **Required Image Checksum:** `f113419abc4ad8c343cedb00a667e64fd13076f3c2ed87e658b63dea8059806d`
- **Boot Validation Type:** `Read-Only Boot (No Installer / No disk writes)`

---

## 📋 Operator Verification Checklist

| Check / Step | Status | Notes |
| :--- | :---: | :--- |
| Confirm ISO SHA-256 matches exact target checksum | [ ] | |
| Identify USB device block address safely (`diskutil list` / `lsblk`) | [ ] | |
| Write image to USB stick via raw block address (`dd`) | [ ] | |
| Place USB in target x86_64 host system slot | [ ] | |
| Enter BIOS / UEFI Settings (ensure Secure Boot is Disabled) | [ ] | |
| Capture BIOS Settings screen | [ ] | |
| Boot system to Boot Picker Menu | [ ] | |
| Capture Boot Picker Menu showing "PhoenixOS Boot" option | [ ] | |
| Boot system and capture initial PhoenixOS Loading Screen | [ ] | |
| Reached SDDM Graphical Desktop environment | [ ] | |
| Extract boot parameters and terminal command outputs | [ ] | |

---

## 📁 Evidence Package Placeholders

*Complete this section during live execution. Archive all media files under `iso/outputs/physical-evidence/pr41a/hw-01-x86_64_uefi_pc/`.*

- **Host Device Model:** `[Enter Model, e.g., Dell OptiPlex 7070]`
- **CPU Family / Count:** `[Enter CPU info]`
- **Total Installed RAM:** `[Enter RAM info, e.g., 16 GB]`
- **Firmware Boot Mode:** `UEFI`
- **Secure Boot State:** `Disabled`
- **USB Physical Device Used:** `[Enter USB brand/model, e.g., SanDisk Ultra 32GB]`
- **USB VID / PID:** `[Enter USB Hex IDs if available]`
- **Boot Picker Photo Path:** `iso/outputs/physical-evidence/pr41a/hw-01-x86_64_uefi_pc/boot_picker.jpg`
- **Phoenix Boot Screen Photo Path:** `iso/outputs/physical-evidence/pr41a/hw-01-x86_64_uefi_pc/boot_screen.jpg`
- **BIOS Settings Photo Path:** `iso/outputs/physical-evidence/pr41a/hw-01-x86_64_uefi_pc/bios_settings.jpg`
- **Desktop Reached (Yes/No):** `No (Untested)`
- **Kernel Command Line:**
  ```text
  [Paste output of cat /proc/cmdline here once booted]
  ```
- **dmesg Excerpt Path:** `iso/outputs/physical-evidence/pr41a/hw-01-x86_64_uefi_pc/dmesg_excerpt.txt`
- **lsblk Console Output Path:** `iso/outputs/physical-evidence/pr41a/hw-01-x86_64_uefi_pc/lsblk_output.txt`
- **Failure Analysis Photo Path:** `iso/outputs/physical-evidence/pr41a/hw-01-x86_64_uefi_pc/failure_screen.jpg`

---

## 📈 Final Evaluation

- **Status Classification:** `PHYSICAL_BOOT_UNTESTED`

*Record initialized by Release Engineering on 2026-05-28.*
