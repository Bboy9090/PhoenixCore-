# Phoenix OS — Hardware Support

## Overview

Phoenix OS targets professional repair and recovery scenarios. Hardware support prioritizes breadth (technicians work on all kinds of machines) and reliability (a repair OS that fails to boot is useless). The Ubuntu 24.04 LTS HWE kernel provides the broadest hardware support baseline.

---

## Certified x86_64 Hardware Categories

### Storage Controllers
| Type | Support Level | Notes |
|------|--------------|-------|
| SATA AHCI | ✅ Full | All modern SATA controllers |
| NVMe (PCIe) | ✅ Full | Requires kernel 4.4+, covered by HWE |
| USB Mass Storage | ✅ Full | Required for USB boot and key storage |
| SD/MMC | ✅ Full | Via mmc-core |
| RAID (LSI/Broadcom) | ✅ Full | mpt3sas, megaraid_sas modules |
| RAID (Intel RST) | ⚠️ Partial | Software RAID via dmraid; hardware RST needs proprietary driver |
| NVMe RAID (AMD) | ⚠️ Partial | May require manual configuration |

### Networking
| Type | Support Level | Notes |
|------|--------------|-------|
| Intel Ethernet (e1000e, igb, ixgbe) | ✅ Full | All modern Intel NICs |
| Realtek Ethernet | ✅ Full | r8169 covers most Realtek |
| Broadcom Ethernet | ✅ Full | bnx2, tg3 |
| Intel Wi-Fi (iwlwifi) | ✅ Full | Requires firmware-iwlwifi |
| Realtek Wi-Fi (RTL88xx) | ✅ Full | Requires rtl8xxxu or vendor firmware |
| Broadcom Wi-Fi | ⚠️ Partial | b43 open-source or wl proprietary (included) |
| MediaTek Wi-Fi | ✅ Full | mt76 family |
| Qualcomm Wi-Fi | ✅ Full | ath10k, ath11k with firmware |

### Graphics
| Type | Support Level | Notes |
|------|--------------|-------|
| Intel integrated (Gen 8+) | ✅ Full | i915 driver, good Wayland support |
| AMD (RDNA1, RDNA2, RDNA3) | ✅ Full | amdgpu, excellent open-source |
| AMD (older GCN) | ✅ Full | amdgpu or radeon |
| NVIDIA (Turing+) | ⚠️ Partial | nouveau for boot; nvidia proprietary in ISO for repair |
| NVIDIA (older) | ⚠️ Partial | nouveau; install proprietary post-boot if needed |

Note: Phoenix OS is not a gaming platform. Graphics support needs to be sufficient for KDE Plasma. We ship `nouveau` and `nvidia-driver-535` (open kernel module variant) in the ISO.

### Input Devices
| Type | Support Level | Notes |
|------|--------------|-------|
| PS/2 keyboard/mouse | ✅ Full | |
| USB HID (keyboard, mouse) | ✅ Full | |
| Touchpad (Synaptics, libinput) | ✅ Full | |
| Touchscreen | ✅ Full | evdev, libinput |

---

## Firmware Packages

The following firmware packages are included in the ISO:

```
linux-firmware              # Mega-package: covers most devices
firmware-linux-free         # GPL-compatible firmware
intel-microcode             # Intel CPU microcode updates
amd64-microcode             # AMD CPU microcode updates
fwupd                       # Firmware update daemon (for post-install updates)
```

Additionally, for Wi-Fi cards that need supplementary firmware:
```
firmware-iwlwifi            # Intel Wi-Fi firmware
firmware-atheros            # Qualcomm/Atheros Wi-Fi
firmware-realtek            # Realtek Wi-Fi and Ethernet
firmware-brcm80211          # Broadcom Wi-Fi
```

---

## ARM64 Hardware (Planned — Phase 2)

### Raspberry Pi 4 / 5

- Kernel: `linux-image-raspi` or upstream kernel with RPi patches
- GPU: VideoCore VI / VideoCore VII (Broadcom; requires proprietary firmware blob)
- Storage: SD card, USB 3, NVMe via PCIe (RPi 5)
- Networking: Built-in Ethernet, Wi-Fi (Broadcom; requires firmware)
- Display: HDMI via VC4 DRM driver

### Apple Silicon (M-series) via Asahi Linux

- Requires Asahi Linux kernel and firmware packages
- Boot process: m1n1 + U-Boot + GRUB
- Not a Phase 1 target; tracked in ROADMAP

### Ampere Altra Workstations

- Standard ARM64 UEFI boot
- Network: Broadcom/Marvell; all mainline supported
- Target: repair shop workstation running Phoenix OS as primary OS

---

## USB Boot Compatibility

Phoenix OS ISO is built as a **hybrid image** (using `xorriso --isohybrid`), meaning it can be written directly to a USB drive with `dd` or Etcher and will boot on:

- UEFI systems (x86_64): via EFI partition with GRUB
- Legacy BIOS systems: via MBR + isolinux
- UEFI Secure Boot: **Not enforced in MVP** — disable Secure Boot in firmware settings

### Writing the ISO to USB

```bash
# Linux (dd method — verified, no data loss risk if /dev/sdX is correctly identified)
sudo dd if=phoenix-os-1.0-amd64.iso of=/dev/sdX bs=4M status=progress oflag=sync

# Balena Etcher (GUI, cross-platform) — recommended for less experienced users
# Ventoy — supported (ISO can be placed on a Ventoy drive)
```

---

## S.M.A.R.T. and Diagnostics Support

Phoenix OS ships `smartmontools` which supports:

- All ATA/SATA drives via `smartctl -a /dev/sdX`
- NVMe drives via `smartctl -a /dev/nvmeXn1`
- USB-attached drives via `-d sat,auto` or `-d usb` options

S.M.A.R.T. data is surfaced in Phoenix Control Center's disk health panel.

---

## Known Limitations

1. **NVIDIA proprietary driver:** The ISO includes the open kernel module variant (`nvidia-driver-535-open`). For older NVIDIA cards requiring legacy drivers (390.x), users must install manually after boot.

2. **Realtek RTL8852BE Wi-Fi:** Some newer Realtek chips require an out-of-tree kernel module. A build hook installs the DKMS package where available.

3. **Apple T2 Security Chip:** MacBooks with T2 require special boot configuration. T2Linux project patches are tracked but not included in MVP.

4. **USB 3.x hubs with embedded NVMe:** Some USB dock configurations present NVMe as USB; S.M.A.R.T. passthrough may not work without explicit `-d` flag.

---

## Reporting Hardware Issues

Hardware compatibility issues should be filed in the project issue tracker with:

- `lspci -vvv` output
- `lsusb` output
- `dmesg` output (filtered for relevant device)
- `inxi -Faz` output
- Description of the failure (no boot, device not detected, etc.)
