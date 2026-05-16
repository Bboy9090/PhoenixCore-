# ARCWYRE OS / Phoenix OS Live-Boot Testing Guide

This document provides exact instructions for performing constrained smoke tests on the hardened system ISO.

## ⚠️ Safety Mandatory Rules

*   **NO INSTALLATION**: Do not execute any "Install" or "Installer" flows.
*   **READ-ONLY MODE**: Internal disks must remain unmounted or mounted as read-only.
*   **NO DATA MUTATION**: Do not perform partitioning, formatting, erasing, or disk repair.
*   **LIVE ENVIRONMENT ONLY**: All testing must be conducted in the live session (`live/`) without persistent storage.

## 1. Pre-Flight Check
Always verify the ISO integrity before attempting to boot.
```bash
sha256sum os/phoenix-os/build/live-image-amd64.hybrid.iso
# Compare with the hash in the release report (PR27).
```

## 2. QEMU Test (macOS/Linux)
```bash
qemu-system-x86_64 \
  -m 4G \
  -cdrom os/phoenix-os/build/live-image-amd64.hybrid.iso \
  -boot d \
  -display default,show-cursor=on \
  -device virtio-vga-gl \
  -cpu Haswell-v4 \
  -accel hvf # Remove -accel hvf if not on macOS
```

## 3. UTM Configuration (Apple Silicon)
1. **Create New VM**: Select **Emulate** -> **Other**.
2. **Boot Image**: Select the `live-image-amd64.hybrid.iso`.
3. **Hardware**: 
   - **Architecture**: `x86_64`.
   - **RAM**: 4096 MB.
   - **CPU Cores**: 2.
4. **Display**: Set to `virtio-ramfb` or `virtio-vga`.
5. **Drives**: Ensure the ISO is the primary boot device.

## 4. VirtualBox Configuration
1. **Name**: `ARCWYRE_SMOKE_TEST`.
2. **Type**: Linux / Debian (64-bit).
3. **Memory**: 4096 MB.
4. **Graphics**: VMSVGA (Enable 3D Acceleration).
5. **Storage**: Mount ISO in the Optical Drive.
6. **System**: Enable EFI (Special OSes only).

## 5. Boot Stage Checklist
| Stage | Requirement | Status |
| :--- | :--- | :--- |
| **1. Bootloader** | GRUB appears with ARCWYRE/Phoenix branding | [ ] |
| **2. Kernel/Init** | Kernel initializes and pivots to live-filesystem | [ ] |
| **3. Splash** | Plymouth animated splash is visible | [ ] |
| **4. Desktop** | Reaches the KDE Plasma / Sacred Minimal session | [ ] |
| **5. Shutdown** | Clean power-off without hangs | [ ] |

## 6. Reporting Failures
Record the exact error message or screenshot if:
- `initramfs` fails to find the squashfs.
- The display manager (SDDM) fails to start.
- The system hangs at "Reached target Graphical Interface".
