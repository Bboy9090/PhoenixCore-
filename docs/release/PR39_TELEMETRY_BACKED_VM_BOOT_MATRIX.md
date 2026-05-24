# PR39 Telemetry-Backed VM Boot Matrix

PR39 ties boot evidence to artifact hashes and build telemetry instead of naming or assumption.

## Source of truth

- `iso/outputs/manifest.json`
- `iso/outputs/vm-boot-matrix.json`
- `iso/BOOT_MATRIX.md`
- `os/phoenix-os/build/build-summary.json` when present

## VM tool audit

| Tool | Availability | Version | Limitations |
|---|---|---|---|
| VirtualBox | available | `7.2.6r172322` | Apple Silicon builds are not the primary path for x86_64/i386 boot automation; use for arm64 guests only when explicitly needed. |
| UTM | available | `4.7.5` | No native CLI automation is wired into this repository; use manually if needed. |
| QEMU | available | `QEMU emulator version 11.0.0` | x86 guests run under TCG on Apple Silicon and are slow; arm64 is supported only when the matching firmware is present. |

## Current observed boot states

The matrix is conservative. A status only records what was actually observed.

| Artifact | SHA256 prefix | VM result | Observed stage |
|---|---|---|---|
| `bwos-home.iso` | `64228d469c55` | `BOOT_PASS_BOOTLOADER_ONLY` | GRUB reached, kernel not observed |
| `bwos-aurelia.iso` | `6dcc401780d2` | `BOOT_PASS_BOOTLOADER_ONLY` | GRUB reached, kernel not observed |
| `bwos-arcwyre.iso` | `3ba79189b563` | `BOOT_PASS_BOOTLOADER_ONLY` | GRUB reached, kernel not observed |
| `bwos-thunder-god.iso` | `4ea3fa9cfa92` | `BOOT_PASS_BOOTLOADER_ONLY` | GRUB reached, kernel not observed |
| `bwos-home-legacy-i386.img` | `70b8efd70b5a` | `BOOT_FAIL_KERNEL` | SeaBIOS reported no bootable device |

## What this means

- Bootability is tracked per artifact hash, not per edition label.
- A rebuilt ISO must be revalidated if the checksum changes.
- `release_candidate` remains blocked until a pass state is backed by stage evidence.
- Current registry state is truthful but not release-ready.
- Retired concept artifacts are excluded from the active boot matrix and preserved only in archive history.

## Notes

- The legacy i386 build artifacts share bytes across multiple filenames. That is why the validator still emits format-mismatch warnings for the ambiguous `unknown` entries.
- No physical USB boot testing has been done yet in this PR.
- No installer or partitioning actions were executed in VM tests.
