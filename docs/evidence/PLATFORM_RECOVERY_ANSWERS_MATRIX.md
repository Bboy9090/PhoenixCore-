# Phoenix Key Platform Recovery Answers Matrix

Status: active hardening layer on `convergence/windows-recovery-forge-macos-v2`.

Purpose: give Phoenix Key a broad, evidence-backed answer engine for firmware, boot, and OS recovery without turning recovery into credential, ownership, enrollment, Verified Boot, Secure Boot, or signature bypass.

## Core rule

Phoenix Key may diagnose, explain, verify, stage, repair, and recover supported systems. It must not defeat security controls whose purpose is to establish ownership, authorization, boot trust, or enterprise policy.

## Coverage implemented

### HP BIOS / firmware

Recognized scenarios:
- failed BIOS update / suspected BIOS corruption
- black/blank screen with power present
- blink/beep-code evidence collection
- HP Sure Start present vs not present
- firmware/admin password or access-control problem

Supported route:
- exact product/model/System Board ID evidence
- exact official HP BIOS package matching
- HP automatic recovery
- HP-documented manual/USB recovery only for systems where HP supports it
- Sure Start automatic recovery / HP-supported service path
- post-recovery BIOS version and boot-result evidence

Blocked route:
- password bypass/master-password generation
- cross-flashing another model's firmware
- unverified BIOS images
- SPI modification intended to remove ownership/security data
- disabling verification simply to force an image

Important distinction:
HP Sure Start systems are not treated as ordinary manual BIOS-recovery machines. Phoenix Key must route them through Sure Start/HP-supported recovery instead of forcing a manual recovery method.

### ChromeOS / Chromebook

Recognized scenarios:
- `ChromeOS is missing or damaged`
- boot loop / serious OS corruption
- Recovery Mode
- Verified Boot / developer-path questions
- enterprise/school-managed device
- enrollment / forced re-enrollment scenarios
- custom-firmware or "shim" requests

Supported route:
- less-invasive diagnostics first when the OS still boots
- official ChromeOS Recovery Mode
- supported internet recovery where the device provides it
- official model/board-matched recovery media
- supported owner-controlled Developer Mode/debugging path where appropriate
- recovery back to normal Verified Boot state
- administrator route for enterprise/school policy

Blocked route:
- enterprise-enrollment bypass
- forced re-enrollment defeat
- Verified Boot bypass shim
- patched recovery image intended to suppress ownership/policy checks
- firmware patch whose purpose is to evade management

Data rule:
Full ChromeOS recovery is treated as destructive to local device data unless evidence for that specific path proves otherwise. Phoenix Key must warn before staging or executing it.

### UEFI Secure Boot / shim / signed bootloader

Recognized scenarios:
- shim signature failure
- bootloader signature rejection
- Secure Boot trust-chain failure
- EFI boot entry or boot-file damage

Supported route:
- inspect UEFI/legacy mode
- inspect Secure Boot state
- inventory EFI System Partition and boot entries
- identify exact failing shim/bootloader
- restore vendor/distribution-signed boot components
- repair EFI boot entries without weakening the trust chain
- owner-authorized firmware policy changes only when specifically required

Blocked route:
- signature-check bypass payloads
- patched shim designed to execute untrusted code
- silently disabling Secure Boot as a generic fix
- replacing platform keys without ownership-backed recovery evidence

## Machine-checkable implementation

Backend module:
`apps/phoenix-key/src-tauri/src/platform_recovery.rs`

Diagnostic entrypoint:
`cargo run --example windows_recovery_probe -- answer <platform> <scenario>`

Current automated tests prove:
1. HP Sure Start does not receive a non-Sure-Start manual-recovery route.
2. HP BIOS-password scenarios explicitly block bypass behavior.
3. Managed Chromebook scenarios explicitly block enrollment bypass.
4. ChromeOS missing/damaged routes to official recovery and carries a destructive-data warning.
5. Secure Boot/shim failure routes to signed-component repair and blocks signature-bypass behavior.

Recovery Forge CI now includes this module in:
- Windows recovery unit tests
- Windows recovery example build
- Clippy with warnings denied
- destructive-boundary scanning

## Vendor-source basis

The implementation is intentionally conservative and follows these vendor/platform principles:
- HP BIOS Recovery documentation distinguishes HP Sure Start systems from manual BIOS recovery paths.
- Google Chromebook recovery documentation treats recovery as OS reinstallation and warns that local data is erased.
- ChromiumOS Verified Boot and Firmware Boot/Recovery documentation describe recovery as restoring a verified boot chain.
- Managed-device ownership/enrollment remains an administrator policy boundary rather than a repair target.

## Next expansion set

Add evidence-backed answer families for:
- Dell BIOS recovery
- Lenovo BIOS/UEFI recovery
- ASUS/Acer firmware recovery
- Microsoft Surface UEFI/recovery images
- Windows BitLocker/WinRE boot recovery that preserves key/ownership controls
- Linux GRUB/systemd-boot signed recovery
- Android Fastboot/Recovery/ADB states without FRP bypass
- Apple DFU/revive/restore without Activation Lock bypass
- NVMe/SATA/USB storage diagnostics
- TPM/Secure Boot reset decision tree with owner authorization
- BCD/EFI/WinRE repair recommendation engine

Every new family must include:
- evidence to collect
- supported recovery actions
- blocked security-bypass actions
- destructive-data warning when applicable
- tests proving both the supported path and the security boundary
