# PR41A — Physical Device Ledger & Hardware Inventory

This ledger catalogs the exact hardware specifications, boot hotkeys, firmware configurations, and known quirks of the target physical devices designated for **PR41A Physical USB Boot Matrix** validation. 

Before physical validation begins, the operator must align the target devices to the baseline profiles cataloged here.

---

## Hardware Inventory & Profiles

### Slot HW-01: `x86_64_uefi_pc` (Standard UEFI PC)
* **Device Model**: Intel NUC8i5BEH (Bean Canyon)
* **CPU / Arch**: Intel Core i5-8259U (x86_64)
* **RAM**: 16 GB DDR4-2400 (Dual Channel)
* **Storage Type**: WD Blue 500GB SATA M.2 SSD
* **Firmware Version**: Intel Visual BIOS `BECFL357.86A` (v0095)
* **BIOS/UEFI Mode**: UEFI Mode Only (Legacy Boot disabled)
* **USB Controller Type**: Intel Corporation Cannon Point-LP USB 3.1 xHCI Controller
* **Secure Boot State**: Enabled (Custom signed keys imported, KEK/db active)
* **Boot Hotkeys**: Press `F10` at visual BIOS splash to trigger the boot selection menu.
* **Known Quirks**: 
  * Intel Visual BIOS sometimes ignores USB 3.1 drives formatted with standard GPT labels if the drive partition is not marked with the `boot` attribute.
  * Secure boot key enforcement requires standard UEFI shim loaders to avoid `Security Violation` warnings on boot init.
* **Photo Reference**: `iso/outputs/app-launch-evidence/hardware/hw-01-nuc.jpg` (Pending Capture)

---

### Slot HW-02: `x86_64_legacy_bios_pc` (Legacy BIOS / CSM Laptop)
* **Device Model**: Lenovo ThinkPad T420 (4177-CTO)
* **CPU / Arch**: Intel Core i5-2520M (Sandy Bridge x86_64)
* **RAM**: 8 GB DDR3-1333
* **Storage Type**: Crucial MX500 250GB 2.5-inch SATA SSD
* **Firmware Version**: Lenovo BIOS `83ET82WW (1.52)`
* **BIOS/UEFI Mode**: Legacy / CSM Only (UEFI boot explicitly disabled in BIOS startup)
* **USB Controller Type**: Intel 6 Series/C200 Series Chipset Family USB Enhanced Host Controller (EHCI)
* **Secure Boot State**: Unsupported (Legacy BIOS)
* **Boot Hotkeys**: Press `F12` during Lenovo splash screen to launch the Boot Device Menu.
* **Known Quirks**:
  * Sandy Bridge mobile platforms will hang with a blinking cursor at boot if the USB partition sector size is not explicitly 512 bytes.
  * USB EHCI handoff can occasionally drop connection if power saving (USB Suspend) is enabled during early kernel stages.
* **Photo Reference**: `iso/outputs/app-launch-evidence/hardware/hw-02-t420.jpg` (Pending Capture)

---

### Slot HW-03: `intel_mac_option_boot` (Intel Mac Option Key Boot)
* **Device Model**: Apple MacBook Air 11-inch (A1370 - Mid 2011)
* **CPU / Arch**: Intel Core 2 Duo L9400 (Penryn x86_64)
* **RAM**: 4 GB DDR3-1066 (Onboard)
* **Storage Type**: Apple Proprietary 128GB Flash Storage
* **Firmware Version**: MacBookAir4,1 EFI Boot ROM (`MBA41.88Z.0084.B00.1112161643`)
* **BIOS/UEFI Mode**: Apple EFI (Hybrid GPT/MBR fallback enabled)
* **USB Controller Type**: NVIDIA MCP89 USB 2.0 EHCI Controller
* **Secure Boot State**: Unsupported (Pre-T2 chip)
* **Boot Hotkeys**: Hold down the `Option (Alt)` key immediately after hearing the Apple startup chime.
* **Known Quirks**:
  * NVIDIA MCP89 EHCI controller enforces strict FAT32 layout for USB drives to display in the Apple EFI Boot Selector. If formatted in exFAT, the drive is invisible to the picker.
  * L9400 CPU lacks standard SSE4.2 virtualization primitives; the graphical installer must not attempt to trigger VM hypervisors locally.
* **Photo Reference**: `iso/outputs/app-launch-evidence/hardware/hw-03-a1370.jpg` (Pending Capture)

---

### Slot HW-04: `t2_mac_external_boot` (T2-Secured Intel Mac)
* **Device Model**: Apple MacBook Pro 15-inch (A1990 - Late 2018)
* **CPU / Arch**: Intel Core i7-8850H (Coffee Lake x86_64)
* **RAM**: 16 GB DDR4-2400 (Onboard)
* **Storage Type**: Apple Onboard PCIe NVMe SSD
* **Firmware Version**: Apple T2 Secure Boot ROM (`19.16.16067.0.0,0`)
* **BIOS/UEFI Mode**: Apple EFI + Secure Boot
* **USB Controller Type**: Intel Cannon Lake USB 3.1 Gen 2 xHCI Controller
* **Secure Boot State**: Enabled / Medium Security (Allowed External Boot)
* **Boot Hotkeys**: 
  1. Hold down `Command (Cmd) + R` at startup to boot into macOS Recovery.
  2. Launch **Startup Security Utility** and check:
     * *Secure Boot:* `Medium Security` or `No Security`.
     * *Allowed Boot Media:* `Allow booting from external or removable media`.
  3. Restart and hold down `Option (Alt)` to load the Apple Boot Manager.
* **Known Quirks**:
  * If Startup Security Utility is left at "Full Security" or "Disallow External Boot," the T2 chip will display a red padlock error screen stating: "Security settings do not allow this Mac to use an external startup disk."
  * Intel Gen 2 USB controllers require standard Type-C to Type-A adapters to have strict physical ground pin contact to avoid sudden drop-outs.
* **Photo Reference**: `iso/outputs/app-launch-evidence/hardware/hw-04-t2mbp.jpg` (Pending Capture)

---

### Slot HW-05: `apple_silicon_external_boot_observation` (ARM64 Hypervisor Observation)
* **Device Model**: Apple Mac mini M1 (A2348 - Late 2020)
* **CPU / Arch**: Apple M1 (8-core ARM64 system-on-chip)
* **RAM**: 16 GB LPDDR4X Unified Memory
* **Storage Type**: Apple Onboard PCIe NVMe SSD
* **Firmware Version**: Apple iBoot `8422.141.2`
* **BIOS/UEFI Mode**: ARM64 Boot ROM / Emulated x86_64 Guest (via UTM/QEMU TCG)
* **USB Controller Type**: Apple Thunderbolt / USB4 xHCI Controller
* **Secure Boot State**: System Integrity Protection (SIP) enabled / Standard Apple Security
* **Boot Hotkeys**: Hold down the Power Button at startup to load the Apple Boot Options screen.
* **Known Quirks**:
  * Emulating an x86_64 Live OS on ARM64 Apple Silicon requires using QEMU TCG translation mode (implemented via UTM). Performance is slow, but useful for testing x86 UEFI compatibility in a sandboxed guest environment.
  * Direct USB pass-through must route the raw physical USB-A controller to the virtual machine guest to verify raw sector blocks.
* **Photo Reference**: `iso/outputs/app-launch-evidence/hardware/hw-05-m1mini.jpg` (Pending Capture)

---

### Slot HW-06: `ryzen_nvme_desktop` (AMD Ryzen Desktop with NVMe Target)
* **Device Model**: Custom Desktop System (ASUS ROG Strix X570-E Gaming)
* **CPU / Arch**: AMD Ryzen 9 5900X (x86_64)
* **RAM**: 32 GB DDR4-3600 (Dual Channel)
* **Storage Type**: Samsung 980 Pro 1TB PCIe Gen 4 NVMe M.2 SSD
* **Firmware Version**: ASUS UEFI BIOS `Version 5003`
* **BIOS/UEFI Mode**: UEFI Class 3 (Secure Boot Off)
* **USB Controller Type**: AMD X570 USB 3.2 Gen 2 xHCI Controller / ASMedia eXtensible Host Controller
* **Secure Boot State**: Disabled (User custom override)
* **Boot Hotkeys**: Press `F8` at ASUS ROG splash to launch the UEFI Boot Selection screen.
* **Known Quirks**:
  * AMD X570 chipsets occasionally reset USB controllers during IOMMU initialization if `IOMMU` is set to "Enabled" rather than "Auto" in BIOS.
  * NVMe write target will be ignored by safety checking unless it is flagged as external physical (which it is not, so it must be protected under internal system disk checks).
* **Photo Reference**: `iso/outputs/app-launch-evidence/hardware/hw-06-ryzen.jpg` (Pending Capture)

---

**Lead Hardware Registry Officer**: `Antigravity AI Agent`  
*Current Schema Version:* `1.0.0`
