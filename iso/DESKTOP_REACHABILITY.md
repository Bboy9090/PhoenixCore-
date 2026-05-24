# Desktop Reachability

This document records whether the current Home ISO reaches an actual live desktop session.

## Current Target

- Edition: `home`
- Artifact: `bwos-home.iso`
- Architecture: `amd64`

## Observed Goal

The build must do more than reach a graphical target or a login prompt. The desktop is only considered reachable when the live Plasma session is visibly confirmed in VM testing.

## Required Signals

- GRUB auto-advances without manual input
- kernel output is observed
- initramfs output is observed
- display manager starts
- live Plasma session loads
- desktop is visually confirmed

## Truth Rules

- `graphical_target_reached_serial_only` means the system reached a graphical target on serial, but the desktop was not visually confirmed.
- `display_manager_login_only` means SDDM/login appeared, but no desktop session was confirmed.
- `desktop_not_confirmed` means the build reached the live session path, but the desktop was not observed.
- `qemu_graphics_limitation` means the VM graphics path prevented reliable visual confirmation.
- `sddm_failure` means the display manager failed before session handoff.
- `plasma_session_failure` means SDDM started but the Plasma session failed to launch.

## Current Status

Confirmed on the rebuilt Home ISO.

Observed evidence:

- `iso/outputs/vm-boot-evidence/home/20260523T150945Z/desktop.png`
- `iso/outputs/vm-boot-evidence/home/20260523T150945Z/serial.log`

Observed result:

- visible live Plasma desktop reached in QEMU
- `clean_shutdown_verified` remains `false` for this pass
- boot matrix classification: `BOOT_PASS_DESKTOP`
