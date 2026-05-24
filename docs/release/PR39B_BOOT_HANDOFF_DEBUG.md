# PR39B Boot Handoff Debug Pass

**Status:** PASS
**Date:** 2026-05-23

## Scope

- Active target: `home`
- Artifact: `iso/outputs/bwos-home.iso`
- SHA256: `64228d469c5509bc54224d3b09a16ca74281a9b830cc7b92df23e6999600f844`
- VM: `qemu-system-x86_64`
- EFI: enabled
- Secure Boot: disabled

## What Was Verified In The ISO

- `/boot/grub/grub.cfg`
- `/boot/grub/efi.img`
- `/live/vmlinuz-5.10.0-43-amd64`
- `/live/initrd.img-5.10.0-43-amd64`
- `/live/filesystem.squashfs`
- `/boot.catalog`

## GRUB Findings

- The active Home ISO does contain valid live boot paths.
- The menu entry points at existing kernel and initrd paths.
- The live entry includes `boot=live`, `findiso=${iso_path}`, `quiet`, `splash`, and serial console settings.
- The generated GRUB menu had no timeout, so unattended QEMU testing stayed at the GRUB banner until input was sent.

## Runtime Probe Result

Manual `Enter` on the GRUB menu advanced the guest to:

- `BWOS_BOOT_SUCCESS_GRAPHICAL_REACHED`
- `Debian GNU/Linux 11 debian ttyS0`
- `debian login:`

Observed stage summary:

- bootloader reached: yes
- kernel reached: yes, inferred from later userspace/graphical target evidence
- initramfs reached: yes, inferred from later userspace/graphical target evidence
- live media found: yes
- display manager reached: yes
- desktop reached: no
- clean shutdown verified: no

## Why It Looked Like A GRUB-Only Failure

- The ISO was not actually missing the kernel or initramfs payload.
- The VM test path was missing GRUB automation and was also booting a quiet/splash configuration.
- That combination hid the kernel handoff from the serial log until the menu was advanced manually.

## Temporary Debug Change

- Added a temporary debug GRUB overlay at:
  - `os/phoenix-os/live-build/config/includes.binary/boot/grub/grub.cfg`
- The debug entry keeps the normal live entry and adds a verbose path with:
  - `console=ttyS0`
  - `console=tty0`
  - `loglevel=7`
  - `debug`
  - `systemd.log_level=debug`
  - `rd.debug`

## Evidence Paths

- Boot matrix row: [iso/outputs/vm-boot-matrix.json](/Users/bj90-m1/PhoenixCore-/iso/outputs/vm-boot-matrix.json)
- Boot log: `iso/outputs/vm-boot-evidence/home/20260523T131431Z/console.log`
- Serial log: `iso/outputs/vm-boot-evidence/home/20260523T131431Z/serial.log`
- Probe metadata: `iso/outputs/vm-boot-evidence/home/20260523T131431Z/meta.json`

## Validation

- `bash -n iso/scripts/validate-boot-matrix.sh`
- `bash -n iso/scripts/validate-artifacts.sh`
- `bash iso/scripts/validate-boot-matrix.sh`
- `bash iso/scripts/validate-artifacts.sh`
- `git diff --check`

## Conclusion

The Home ISO is not a GRUB-only artifact. The blocker is boot observability and unattended handoff, not a missing kernel or initrd payload.
