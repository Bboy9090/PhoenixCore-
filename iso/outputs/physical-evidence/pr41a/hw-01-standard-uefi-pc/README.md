# PR41A HW-01 Physical Evidence Folder

Slot: `HW-01 Standard UEFI PC`
Artifact: `iso/outputs/bwos-home.iso`
SHA256: `463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686`

This folder is intentionally evidence-empty until a real physical boot attempt is performed.

Required files after execution:

- `photo_01_boot_menu.*`
- `photo_02_grub.*`
- `photo_03_desktop.*`
- `photo_fail_01.*` if failed
- `failure_notes.txt` if failed
- `uname-a.txt` if desktop reached
- `proc-cmdline.txt` if desktop reached
- `lsblk.txt` if desktop reached
- `journalctl-tail-200.txt` if desktop reached
- `app-launch-results.txt` if desktop reached

Do not record `PHYSICAL_BOOT_PASS` unless `photo_03_desktop.*` and guest command outputs exist.
