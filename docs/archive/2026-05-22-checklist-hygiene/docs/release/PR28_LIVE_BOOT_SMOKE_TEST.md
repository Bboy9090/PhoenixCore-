# PR28 Phoenix OS Constrained Live-Boot Smoke Test Plan

Date: 2026-05-14

## Goal
Validate whether the PR27 hardened ISO can boot into a live session without performing installer, disk repair, partitioning, formatting, erase, or mutation workflows.

## Artifact Under Test
- **ISO**: `os/phoenix-os/build/live-image-amd64.hybrid.iso`
- **SHA256**: `456bd6cca3bcd20b3f3a54183aeb31ac3e38b21525b07519ed3d98473cbaee16`
- **Size**: 2,623,733,760 bytes
- **Build Duration**: 6,284s

## Safety Rules (Non-Negotiable)
- **NO INSTALLER**: Do not launch Calamares or any installation wizard.
- **NO MUTATION**: Do not format, partition, or erase any disks.
- **NO REPAIR**: Do not run `fsck`, `testdisk` (repair mode), or `gparted`.
- **READ-ONLY**: Internal disks must not be mounted read-write.
- **CONSTRAINED**: Live session only.

## Test Stages

### Stage A: ISO Integrity Verification
- [ ] Verify SHA256 checksum matches the reference (`456bd6cc...`).
- [ ] Inspect ISO structure using `xorriso` to ensure EFI/GRUB paths are valid.
*Status: READY (Synchronized with PR27 Audit)*

### Stage B: VM Boot Test (Preferred)
- [ ] Launch the ISO in QEMU/UTM.
- [ ] Allocate 4GB RAM and 2 CPU cores.
- [ ] Ensure no physical disks are passed through to the VM.

### Stage C: Boot Menu Validation
- [x] Verify the Phoenix OS custom GRUB menu appears.
- [ ] Check if "Live Session" is the default entry.
*Status: PARTIAL (User reported "Debian GRUB" and "Yellow screen" — custom branding bypassed)*

### Stage D: Live Session Startup
- [x] Monitor kernel boot logs for errors.
- [x] Confirm SDDM (Login Manager) or auto-login reaches the desktop.
*Status: SUCCESS (Reaches login/lock screen, but branding is incorrect)*

### Stage E: Branding Check
- [ ] Confirm Plymouth boot splash displays the Phoenix logo.
- [ ] Verify desktop wallpaper and icon themes match the "Sacred Minimal" aesthetic.
*Status: FAIL (User reported purple Monterey-style background and incorrect lock screen; no Phoenix logo seen)*

### Stage F: Read-only Hardware Inventory
- [ ] Run `lsblk` and `blkid` to verify internal disks are detected but not mounted.
- [ ] Verify system information in the Phoenix Control Center.

### Stage G: Polkit Denial Check
- [ ] Attempt to run a mutation tool (e.g., `gparted`) as a non-privileged user.
- [ ] Verify that Polkit correctly denies the action or requires a password that is NOT the live user password.

### Stage H: Clean Shutdown
- [ ] Perform a software-initiated shutdown.
- [ ] Verify the system exits cleanly without filesystem corruption messages.

## Manual Checklist
- [ ] Verify checksum before boot.
- [ ] Boot ISO read-only.
- [ ] **DO NOT** launch Calamares.
- [ ] **DO NOT** run GParted/Partition Manager.
- [ ] Verify internal disk mutation tools are denied (Polkit).
- [ ] Verify Phoenix marker files exist (e.g., `/etc/phoenix-version`).
- [ ] Verify live session can shut down cleanly.

## Hardware Boot Go/No-Go
*Current Status: PENDING*

- **VM (QEMU/UTM)**: Waiting for first smoke test.
- **Physical (USB)**: NOT RECOMMENDED until Stage D is passed in VM.

## Recommended PR29
**PR29: Live Session App Validation & Forensic Tool Audit.**
Verify the functionality of the integrated recovery tools in the live environment without modifying disk state.
