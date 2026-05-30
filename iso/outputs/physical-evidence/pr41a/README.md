# PR41A Physical Validation Evidence

This directory stores real physical boot evidence for Phoenix OS.

## Artifact Under Test

- `iso/outputs/bwos-home.iso`
- SHA256: `463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686`

## Required Evidence Per Completed Slot

- `photo_01_boot_menu.*`
- `photo_02_grub.*`
- `photo_03_desktop.*` for PASS
- `photo_fail_01.*` and `failure_notes.txt` for failure
- `uname-a.txt` if desktop reached
- `proc-cmdline.txt` if desktop reached
- `lsblk.txt` if desktop reached
- `journalctl-tail-200.txt` if desktop reached
- `app-launch-results.txt` if desktop reached

No evidence file should be fabricated. Empty folders mean the physical attempt has not been completed.
