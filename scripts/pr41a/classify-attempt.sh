#!/bin/sh
set -eu

cat <<'RULES'
PR41A classification helper

Use exactly one:

PHYSICAL_BOOT_PASS
  Desktop reached and photo_03_desktop plus guest evidence exists.

PHYSICAL_BOOT_PARTIAL
  Boot reached display manager or desktop boundary, but full desktop evidence/app evidence is incomplete.

PHYSICAL_BOOT_FAIL_NO_PICKER
  Firmware did not list the USB/Ventoy boot option.

PHYSICAL_BOOT_FAIL_BOOTLOADER
  Boot option appeared, but GRUB/bootloader failed or hung.

PHYSICAL_BOOT_FAIL_KERNEL
  GRUB started kernel, but kernel/initramfs failed.

PHYSICAL_BOOT_FAIL_DESKTOP
  Kernel/init reached, but SDDM/Plasma desktop failed.

PHYSICAL_BOOT_UNTESTED
  No physical attempt was executed.
RULES
