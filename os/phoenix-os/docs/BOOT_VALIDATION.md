# Phoenix OS Boot Validation Strategy

This document outlines the protocol for validating Phoenix OS ISO images across various environments.

## 1. Validation Layers

### Layer 1: Static Analysis (Host)
- **Checksum**: Validate SHA256 against build output.
- **Header**: Verify ISO9660 and MBR/GPT signature.
- **Peeking**: Use `strings` or `7z` to verify existence of `/EFI`, `/boot/grub`, and `/live/filesystem.squashfs`.

### Layer 2: Virtualized Simulation (QEMU/UTM)
- **BIOS Mode**: Standard QEMU run.
- **UEFI Mode**: QEMU with OVMF firmware.
- **Targets**:
    - Boot to GRUB menu.
    - Load kernel/initrd.
    - Mount squashfs (Live Session).
    - Graphical session (KDE Plasma).

### Layer 3: Physical USB (Controlled)
- **Verification**: Write via `dd` or `Etcher` (non-destructive to host).
- **Target Hardware**: Intel/AMD x86_64 laptops.
- **Success Criteria**: Detectable in Boot Menu, loads kernel.

## 2. VM Test Plan

### QEMU (Recommended for CLI)
```bash
qemu-system-x86_64 -m 2G -cdrom os/phoenix-os/build/live-image-amd64.hybrid.iso -boot d
```

### UTM (macOS Apple Silicon)
- **Configuration**: Emulated (x86_64) or Virtual (if ARM64 target).
- **Display**: virtio-gpu-pci.
- **Network**: Shared Network.

## 3. Truth-First Boot Log

| Date | ISO SHA256 | Target | Result |
|------|------------|--------|--------|
| 2026-05-13 | ac412be... | Static | PASS (EFI, Squashfs confirmed) |
| 2026-05-18 | bwos-home  | QEMU   | PASS (Headless UEFI Boot, Captured Framebuffer) |

## 4. Known Blockers
- **Secure Boot**: Currently unsupported. Must be disabled in UEFI settings.
- **Display Drivers**: Early boot may use VESA/GOP; KDE requires proper acceleration.
