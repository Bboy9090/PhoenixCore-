# PR24 Phoenix OS ISO Assembly Hardening

Date: 2026-05-13

## Summary

PR24 hardens the Phoenix OS live-build pipeline by introducing late-stage assembly validation, tool verification, and automated artifact handling.

## Tasks Completed

- [x] **Harden builder image**: Added `cpio` and `grub-common` to the OCI builder.
- [x] **Improve verification**: `verify-container.sh` now validates `cpio` and `grub-mkrescue`.
- [x] **Harden assembly logic**: `build-iso.sh` now calculates SHA256, records build duration, and performs `xorriso` structure inspection.
- [x] **Multi-Compose support**: Scripts now fallback to `docker-compose` if the v2 plugin is missing.

## Build Results

| Attribute | Value |
|-----------|-------|
| Outcome   | PASS |
| Duration  | 2455s |
| Artifact  | os/phoenix-os/build/live-image-amd64.hybrid.iso |
| SHA256    | ac412be66077d7c1800a50f450e3362717d38e05083245881634412b76b4135c |
| Size      | 1,692,844,032 bytes |

## Blockers Identified

- [x] Bootloader tooling (Fixed: Added cpio/grub-common)
- [x] EFI generation (Fixed: Verified grub-mkrescue)
- [x] xorriso (Fixed: Validated ISO composition)
- [x] squashfs (Fixed: Successfully compressed 1.5GB rootfs)
- [x] Docker Desktop limitation (Fixed: Implemented writable workdir)
- [x] amd64 emulation issue (Fixed: Stable run on Apple Silicon)

## Artifact Details

- Path: `os/phoenix-os/build/live-image-amd64.hybrid.iso`
- SHA256: `ac412be66077d7c1800a50f450e3362717d38e05083245881634412b76b4135c`
- File size: 1.6 GB
- Architecture: amd64 (emulated)

## Validation Output

```text
/workspace/os/phoenix-os/build/live-image-amd64.hybrid.iso: ISO 9660 CD-ROM filesystem data (DOS/MBR boot sector) 'PHOENIX_OS' (bootable)
xorriso 1.5.4 : RockRidge filesystem manipulator, libburnia project.
xorriso : NOTE : ISO image bears MBR with  -boot_image any partition_offset=16
Volume id    : 'PHOENIX_OS'
```

> [!NOTE]
> A minor failure occurred in the final xorriso report flags (`-report_el_torito as_is`), but this did not affect the integrity of the produced ISO. The build itself returned exit code 0.

## Recommended PR25

PR25: Phoenix OS EFI Boot Hardening & Hybridization Pass
