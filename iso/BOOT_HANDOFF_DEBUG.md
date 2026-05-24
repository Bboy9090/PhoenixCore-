# Boot Handoff Debug

Target:
- `bwos-home.iso`
- SHA256: `64228d469c5509bc54224d3b09a16ca74281a9b830cc7b92df23e6999600f844`

What the ISO contains:
- `/boot/grub/grub.cfg`
- `/boot/grub/efi.img`
- `/live/vmlinuz-5.10.0-43-amd64`
- `/live/initrd.img-5.10.0-43-amd64`
- `/live/filesystem.squashfs`
- `/boot.catalog`

What happened in QEMU:
- GRUB banner appeared.
- Manual `Enter` advanced the guest.
- Serial output then showed `BWOS_BOOT_SUCCESS_GRAPHICAL_REACHED`.
- The guest reached `Debian GNU/Linux 11 debian ttyS0`.
- The guest stopped at `debian login:`.

Interpretation:
- The Home ISO is not missing the live kernel or initramfs payload.
- The visible problem is that unattended VM boots stall at GRUB because the menu has no timeout.
- Quiet/splash hides the handoff details unless a debug path is used.

Temporary debug overlay:
- `os/phoenix-os/live-build/config/includes.binary/boot/grub/grub.cfg`
- Adds a verbose debug entry and keeps the normal live entry.

Evidence:
- `iso/outputs/vm-boot-evidence/home/20260523T131431Z/console.log`
- `iso/outputs/vm-boot-evidence/home/20260523T131431Z/serial.log`
- `iso/outputs/vm-boot-evidence/home/20260523T131431Z/meta.json`

Status:
- `boot_menu_reached`: true
- `kernel_reached`: true
- `initramfs_reached`: true
- `display_manager_reached`: true
- `desktop_reached`: false
- `clean_shutdown_verified`: false
- `classification`: `BOOT_FAIL_DISPLAY`
