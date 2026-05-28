# PHYSICAL_USB_BOOT_MATRIX.md — Active Hardware Validation Registry

This document records the official physical USB boot matrix testing status for the active **Home Aurelia** and matching builds.

> [!CAUTION]
> **CRITICAL OPERATOR SAFETY NOTE:**
> * Physical boot testing is strictly a **read-only boot validation** exercise.
> * **DO NOT** run the installer on target physical machines.
> * **DO NOT** format internal drives or execute partition tables overrides.
> * **DO NOT** write to host target disks or perform any destructive actions.
> * This phase is restricted to **USB boot verification only**.

---

## 1. Summary Registry Table
| Slot ID | Slot Key | Physical Hardware Class | Active Status | Release Blocking | Verified Evidence Logs |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **HW-01** | `x86_64_uefi_pc` | Standard UEFI PC | `PHYSICAL_BOOT_NOT_TESTED` | `true` | None (Pending test run) |
| **HW-02** | `x86_64_legacy_bios_pc` | Legacy BIOS / CSM Laptop | `PHYSICAL_BOOT_NOT_TESTED` | `true` | None (Pending test run) |
| **HW-03** | `intel_mac_option_boot` | Intel Mac Option Boot | `PHYSICAL_BOOT_NOT_TESTED` | `true` | None (Pending test run) |
| **HW-04** | `t2_mac_external_boot` | T2-Secured Intel Mac | `PHYSICAL_BOOT_NOT_TESTED` | `true` | None (Pending test run) |
| **HW-05** | `apple_silicon_external_boot_observation` | M1/M2/M3 Guest Observation | `PHYSICAL_BOOT_NOT_TESTED` | `true` | None (Pending test run) |
| **HW-06** | `ryzen_nvme_desktop` | AMD Ryzen NVMe Desktop | `PHYSICAL_BOOT_NOT_TESTED` | `true` | None (Pending test run) |

---

## 2. Boot Status Classes Reference
* `PHYSICAL_BOOT_NOT_TESTED`
* `PHYSICAL_BOOT_PASS`
* `PHYSICAL_BOOT_PARTIAL`
* `PHYSICAL_BOOT_FAIL_NO_PICKER`
* `PHYSICAL_BOOT_FAIL_BOOTLOADER`
* `PHYSICAL_BOOT_FAIL_KERNEL`
* `PHYSICAL_BOOT_FAIL_DESKTOP`
* `PHYSICAL_BOOT_UNSUPPORTED`

---

## 3. Detailed Hardware Validation Criteria
Every passing slot is strictly required to contain the following verified parameters under [docs/release/PR41A_PHYSICAL_USB_BOOT_MATRIX.md](file:///Users/bj90-m1/PhoenixCore-/docs/release/PR41A_PHYSICAL_USB_BOOT_MATRIX.md):
- **Device model name**
- **Firmware settings** (Secure boot on/off)
- **USB controller profile**
- **Kernel cmdline capture**
- **Dmesg boot excerpt**
- **Partition table representation (`lsblk` or `diskutil`)**
- **System boot logs**

---

**Lead Release Architect**: `Antigravity AI Agent`  
*Current Schema Version:* `1.0.0`
