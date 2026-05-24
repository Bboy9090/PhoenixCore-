# PR39: Multi-Edition VM Boot Matrix

Date: 2026-05-22

## Goal

Test every generated BWOS / Blue Phoenix OS edition ISO in a virtual machine and record the exact boot stage reached without claiming more than was observed.

## Scope

- VM test only
- No physical USB testing
- No installer execution
- No formatting, partitioning, disk repair, or host-disk passthrough
- No USB passthrough
- No release-candidate promotion until validation is complete

## Editions Covered

- Blue Phoenix Home
- Blue Phoenix Aurelia
- ARCWYRE
- Thunder God
- Compatibility variants such as `home-legacy-i386` and `thunder-god-arm64` are recorded as build-target artifacts when present.
- `Blue Phoenix Native` is a research-only branch and is not part of the Linux VM boot matrix.
- Retired concept names Revival, Forge, and Resilient are archived and are not part of the active boot matrix.

## Boot Stage Classifications

Allowed VM boot classifications:

- `BOOT_PASS_DESKTOP`
- `BOOT_PASS_BOOTLOADER_ONLY`
- `BOOT_FAIL_KERNEL`
- `BOOT_FAIL_INITRAMFS`
- `BOOT_FAIL_DISPLAY`
- `NOT_TESTED`
- `BLOCKED_BY_VM_TOOLING`

Interpretation:

- `BOOT_PASS_BOOTLOADER_ONLY` means the VM reached the bootloader/menu, but not the kernel.
- `BOOT_PASS_DESKTOP` means the VM reached the desktop-session marker.
- `BOOT_PASS_DESKTOP` is not release-ready by itself.
- `NOT_TESTED` means no VM stage record exists yet.
- `BLOCKED_BY_VM_TOOLING` means the machine could not run the test harness with the available VM stack.

## Required VM Settings

Preferred settings for each ISO:

- x86_64 / amd64 VM target
- 4096 MB RAM minimum
- 2 CPU cores minimum
- EFI enabled first
- Secure Boot disabled
- ISO attached read-only
- No host disk passthrough
- No USB passthrough

## Generated Sources

The generated source of truth for this PR is:

- `iso/outputs/vm-boot-matrix.json`
- `iso/BOOT_MATRIX.md`
- `iso/outputs/manifest.json`
- `iso/ARTIFACTS.md`

The scanner and validator remain the source of truth for the registry; this PR adds the VM-stage record that those tools consume.

## Truth Rule

Boot success only means the exact stage reached and documented.

That means:

- bootloader visibility is not desktop success
- kernel visibility is not desktop success
- initramfs visibility is not desktop success
- display manager visibility is not desktop success
- desktop visibility still does not imply release readiness without app and safety validation

## Promotion Rule

PR39 records boot reality. It does not promote release candidates.

Release candidate status remains blocked until the artifact registry, VM boot matrix, app validation, and safety validation are all complete and consistent.

## Implementation Notes

The boot matrix is produced by `iso/scripts/vm-boot-checklist.sh` and merged into the registry by `iso/scripts/scan-artifacts.sh`. Validation is enforced by `iso/scripts/validate-artifacts.sh`.
