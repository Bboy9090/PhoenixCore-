# PR41A HW-05 Apple Silicon External Boot Execution Record

This document serves as the formal execution record and evidence checklist for verifying **PhoenixOS** on the **HW-05 (Apple Silicon External Boot Observation)** physical hardware slot.

---

## 🔬 Test Specifications & Config

- **Milestone:** `PR41A`
- **Slot ID:** `HW-05`
- **Target Architecture:** `arm64` (Apple Silicon M1/M2/M3)
- **Target Flagship Edition:** `thunder-god-arm64`
- **Target Image File:** `bwos-thunder-god-arm64.iso`
- **Required Image Checksum:** `b3a2305cbfedfebc8fc4821e1d5804216aca25f66d907b45943038426b270ef0`
- **Boot Validation Type:** `Read-Only Boot (No Installer / No disk writes)`

---

## 📋 Operator Verification Checklist

| Check / Step | Status | Notes |
| :--- | :---: | :--- |
| Ensure native ARM64 OCI container is configured and ready | [ ] | |
| Identify M1 host hardware parameters | [ ] | |
| Place target Apple Silicon Mac in recovery / permissive boot mode | [ ] | |
| Set Boot Security Policy to "Permissive Security" or "Reduced Security" | [ ] | |
| Identify USB device block address safely (`diskutil list`) | [ ] | |
| Write ARM64 image to USB stick via raw block address (`dd`) | [ ] | |
| Place USB in target M1 Silicon host port | [ ] | |
| Boot system to Boot Picker Menu via long-pressing Power Button | [ ] | |
| Capture Boot Picker Menu showing "PhoenixOS Boot" / "EFI Boot" option | [ ] | |
| Boot system and capture initial PhoenixOS Loading Screen | [ ] | |
| Reached SDDM Graphical Desktop environment | [ ] | |
| Extract boot parameters and terminal command outputs | [ ] | |

---

## 📁 Evidence Package Placeholders

*Complete this section during live execution. Archive all media files under `iso/outputs/physical-evidence/pr41a/hw-05-apple_silicon/`.*

- **Host Device Model:** `[Enter Model, e.g., MacBook Air M1 2020]`
- **CPU Family / Count:** `Apple M1 (8 Cores)`
- **Total Installed RAM:** `[Enter RAM info, e.g., 8 GB / 16 GB]`
- **Firmware Boot Mode:** `iBoot / Apple Silicon Boot Rom`
- **Secure Boot State:** `Permissive / Reduced Security`
- **USB Physical Device Used:** `[Enter USB brand/model, e.g., SanDisk Ultra 32GB]`
- **USB VID / PID:** `[Enter USB Hex IDs if available]`
- **Boot Picker Photo Path:** `iso/outputs/physical-evidence/pr41a/hw-05-apple_silicon/boot_picker.jpg`
- **Phoenix Boot Screen Photo Path:** `iso/outputs/physical-evidence/pr41a/hw-05-apple_silicon/boot_screen.jpg`
- **BIOS Settings Photo Path:** `iso/outputs/physical-evidence/pr41a/hw-05-apple_silicon/boot_policy_settings.jpg`
- **Desktop Reached (Yes/No):** `No (Untested)`
- **Kernel Command Line:**
  ```text
  [Paste output of cat /proc/cmdline here once booted]
  ```
- **dmesg Excerpt Path:** `iso/outputs/physical-evidence/pr41a/hw-05-apple_silicon/dmesg_excerpt.txt`
- **lsblk Console Output Path:** `iso/outputs/physical-evidence/pr41a/hw-05-apple_silicon/diskutil_output.txt`
- **Failure Analysis Photo Path:** `iso/outputs/physical-evidence/pr41a/hw-05-apple_silicon/failure_screen.jpg`

---

## 📈 Final Evaluation

- **Status Classification:** `PHYSICAL_BOOT_UNTESTED`

*Record initialized by Release Engineering on 2026-05-28.*
