# PR39C GRUB Autohandoff + Desktop Reachability

**Status:** complete
**Date:** 2026-05-23

## Goal

Prove that the active Home ISO can:

- leave GRUB unattended
- reach kernel and initramfs visibly
- start the display manager
- auto-login into the live Plasma session
- reach a confirmed desktop session

## Current Diagnosis

PR39B proved the image was not missing payloads:

- GRUB appears
- manual Enter advances the guest
- kernel reaches serial output
- initramfs reaches the boot path
- serial reaches `BWOS_BOOT_SUCCESS_GRAPHICAL_REACHED`
- serial reaches `debian login:`

The remaining issue is boot handoff and desktop confirmation, not missing kernel or initramfs content.

## Outcome

The rebuilt Home ISO now reaches a visibly confirmed live Plasma desktop in QEMU.

Observed evidence:

- `iso/outputs/vm-boot-evidence/home/20260523T150945Z/desktop.png`
- `iso/outputs/vm-boot-evidence/home/20260523T150945Z/serial.log`

Observed stage state:

- boot menu reached
- unattended handoff reached
- kernel reached
- initramfs reached
- display manager reached
- desktop reached
- clean shutdown not yet verified

Current boot matrix classification:

- `BOOT_PASS_DESKTOP`
- `failure_point: shutdown`
- `clean_shutdown_verified: false`

## Changes Applied

- Added an explicit GRUB default entry and timeout in:
  - `os/phoenix-os/live-build/config/includes.binary/boot/grub/grub.cfg`
- Kept the verbose debug menu entry in place.
- Tightened SDDM autologin to the explicit Plasma session token:
  - `Session=plasma.desktop`
  - `DefaultSession=plasma.desktop`
- Preserved the desktop heartbeat autostart marker for later confirmation.

## Validation Criteria

This PR is only complete when the rebuilt Home ISO shows:

- unattended GRUB handoff without manual input
- kernel reached
- initramfs reached
- display manager reached
- desktop reached or truthfully blocked with a specific reason
- clean shutdown recorded when it is actually verified, otherwise left false and documented

## Notes

- The debug GRUB entry remains until the normal boot path is proven stable.
- No release candidate status is implied by this change.
- The visible desktop was confirmed with a host screen capture of the QEMU guest window.
