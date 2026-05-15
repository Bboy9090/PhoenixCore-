# Phoenix OS Live-Boot Testing Guide

This document provides exact instructions for performing constrained smoke tests on the Phoenix OS ISO.

## Prerequisites
- QEMU (recommended) or UTM (macOS).
- The latest Phoenix OS ISO.
- `sha256sum` utility.

## 1. Pre-Flight Check
Always verify the ISO integrity before attempting to boot.
```bash
sha256sum live-image-amd64.hybrid.iso
# Compare with the hash in the release notes.
```

## 2. QEMU Test (Headless/CLI)
Use the following command to test bootability in a safe, virtualized environment.
```bash
qemu-system-x86_64 \
  -m 4G \
  -cdrom live-image-amd64.hybrid.iso \
  -boot d \
  -display default,show-cursor=on \
  -device virtio-vga-gl \
  -cpu host \
  -accel hvf
```
*Note: Remove `-accel hvf` if not on macOS.*

## 3. UTM Configuration (Apple Silicon / M1)
To test the x86_64 ISO on Apple Silicon, follow these steps:
1. **Create New VM**: Select **Emulate** -> **Other**.
2. **Boot Image**: Select the `live-image-amd64.hybrid.iso`.
3. **Hardware**: 
   - **System**: `x86_64` (Standard PC Q35 + ICH9).
   - **RAM**: 4096 MB.
   - **CPU**: `Haswell-v4` or `Default` (Ensure x86_64 emulation is active).
4. **Display**: Set to `virtio-ramfb` or `virtio-vga` for best compatibility with KDE.
5. **Network**: Shared Network.
6. **Drives**: Verify the ISO is mounted as a CD/DVD drive (USB or IDE).

## 4. Manual Checklist
| Task | Expected Result |
| :--- | :--- |
| **Boot Menu** | GRUB appears with Phoenix branding |
| **Splash Screen** | Plymouth shows the animated logo |
| **Desktop** | Reaches the desktop session within 60s |
| **Control Center** | Launches and displays hardware info |
| **Disk Safety** | Internal disks are not auto-mounted |
| **Mutation Gate** | `sudo gparted` requires authentication |

## 4. Safety Constraints
- **DO NOT** use physical USB drives for the first pass of a new hardening layer.
- **DO NOT** select "Install to Disk" from the boot menu.
- **DO NOT** run any script that asks for a target device unless it is a virtual disk created for testing.

## 5. Reporting Failures
If the boot fails, record the last visible log line or take a screenshot of the kernel panic/error message. common failure points:
- `initramfs` unable to find the squashfs (usually an ISO mounting issue).
- GPU driver context loss (KDE/Wayland incompatibility in VM).
- Polkit permission loops.
