# Phoenix OS Release Checklist

This checklist must be completed before any ISO is published externally. Sign off each item with initials and date.

---

## Build Verification

- [ ] ISO built from clean state (`./scripts/clean.sh` run first)
- [ ] ISO built on reference build host (Ubuntu 24.04 LTS, clean VM)
- [ ] Build completed without errors or warnings in `lb build` output
- [ ] ISO file size is within expected range (2.5 GB – 5 GB for standard)
- [ ] SHA256 checksum generated and saved to `output/SHA256SUMS`
- [ ] GPG signature applied: `output/SHA256SUMS.gpg`

**Signed off by:** __________ **Date:** __________

---

## Boot Validation

- [ ] ISO boots in QEMU (BIOS mode)
- [ ] ISO boots in QEMU (UEFI mode via OVMF)
- [ ] ISO boots on physical hardware (x86_64, Intel)
- [ ] ISO boots on physical hardware (x86_64, AMD)
- [ ] Live session reaches KDE Plasma desktop without errors
- [ ] Plymouth boot animation displays correctly
- [ ] SDDM login screen displays Phoenix branding
- [ ] Auto-login to live session works (no password prompt in live mode)

**Signed off by:** __________ **Date:** __________

---

## Core Functionality

- [ ] Network: wired (Ethernet) connects automatically
- [ ] Network: Wi-Fi device detected, NetworkManager applet works
- [ ] Disk tools: GParted launches, lists disks correctly
- [ ] Disk tools: no internal disk auto-mounted as writable
- [ ] File manager: Dolphin launches, can browse filesystem
- [ ] Terminal: Konsole launches
- [ ] Phoenix Welcome: launches on first boot, renders correctly
- [ ] Phoenix Control Center: launches, shows system info
- [ ] Flatpak: `flatpak list` runs, Flathub configured

**Signed off by:** __________ **Date:** __________

---

## Installer (Calamares)

- [ ] Calamares launches from desktop shortcut
- [ ] Locale/timezone/keyboard pages render and accept input
- [ ] Disk partitioning page lists available disks
- [ ] Disk partitioning: does NOT pre-select any disk automatically
- [ ] Installation completes to VM disk without errors
- [ ] Installed system boots correctly (BIOS)
- [ ] Installed system boots correctly (UEFI)
- [ ] GRUB bootloader installed and shows Phoenix branding
- [ ] Post-install: Phoenix Welcome launches on first login

**Signed off by:** __________ **Date:** __________

---

## Safety and Security

- [ ] Live session: internal disk partitions not auto-mounted writable
- [ ] Disk operation tools: destructive actions require confirmation dialog
- [ ] Disk audit log: `/var/log/phoenix/disk-ops.log` created on first disk op
- [ ] No root password set in live session by default (sudo only)
- [ ] SSH server NOT enabled by default in live session
- [ ] Firewall (ufw): enabled with default deny-incoming policy

**Signed off by:** __________ **Date:** __________

---

## Branding

- [ ] Desktop wallpaper: Phoenix OS branded, not upstream default
- [ ] KDE Plasma color scheme: Phoenix palette applied
- [ ] Application menu: shows "Phoenix OS" in about/system info
- [ ] GRUB menu: shows Phoenix OS branding, not "Ubuntu" or "Debian"
- [ ] Plymouth: Phoenix splash, not Ubuntu/Debian spinner
- [ ] SDDM: Phoenix login theme, hostname shows as `phoenix`

**Signed off by:** __________ **Date:** __________

---

## Automated Tests

- [ ] `./tests/smoke/test-boot.sh` passes
- [ ] `./tests/iso-validation/validate-iso.sh` passes all checks
- [ ] No regressions from previous release (if applicable)

**Signed off by:** __________ **Date:** __________

---

## Documentation

- [ ] README.md version number updated
- [ ] CHANGELOG.md entry written for this release
- [ ] Known issues documented (if any)
- [ ] Build instructions verified on clean host

**Signed off by:** __________ **Date:** __________

---

## Release Artifacts

- [ ] `phoenix-os-<version>-amd64.iso` uploaded to release host
- [ ] `SHA256SUMS` published alongside ISO
- [ ] `SHA256SUMS.gpg` published alongside ISO
- [ ] Release notes published (GitHub Releases or equivalent)
- [ ] Download page updated

**Final release approval by:** __________ **Date:** __________
