# Known Limitations

This file records current PhoenixCore limitations. It is intentionally stricter than historical plans, screenshots, generated completion prose, and commit titles.

## Trust and registry validation

- Missing registry evidence now fails closed and cannot approve a tool.
- Missing detached signatures, invalid signatures, malformed JSON, unknown tool IDs, URL mismatches, and checksum mismatches must reject approval.
- The committed `tool_registry.json` / `.sig` pair currently fails verification under the configured trust anchor, so registered external-tool approval is unavailable.
- Issue #136 owns the trust-root, manifest-byte, signer-provenance, and independent-verifier investigation.
- The repository contains a direct Python Ed25519 implementation that still requires independent review or migration to a maintained cryptographic library before release promotion.
- URL and SHA-256 validation do not independently prove publisher identity, upstream code signing, or redistribution rights.

## Device discovery

- Windows discovery does not yet prove immutable identity for every USB bridge and enclosure.
- Linux discovery relies on `lsblk` and platform-reported fields.
- macOS discovery relies on `diskutil` and platform-reported removable/external fields.
- Scanner output does not authorize mutation by itself.
- Device identity must be rescanned immediately before any physical operation.

## Physical-drive evidence

- Real drive access is permitted through the explicit sacrificial-drive test lane tracked in issue #135.
- Unknown, internal, fixed, boot, system, busy, identity-mismatched, or ambiguous targets remain blocked.
- A complete write claim requires exact image identity, bounded byte count, durable receipts, and full read-back SHA-256 verification.
- CI and mocked tests cannot produce hardware validation.
- The previously reported bootable SSD black-screen result is `hardware-attempted`, not `hardware-validated`.

## Rescue and media creation

- `create_rescue_usb_structure()` creates directories and a README on an existing mounted path.
- It does not partition, format, install a bootloader, write an image, or prove bootability.
- PhoenixCore’s historical simulated ISO assembler does not create a real ISO and must not be used as production evidence.
- Real ARCWYRE edition ISOs belong to the native repository build pipeline.

## Phoenix Key

- Windows MSI and NSIS preview installers have source, checksum, install, launch, uninstall, and cleanup evidence.
- They are unsigned.
- Update and rollback have not been proven.
- ARCWYRE embedding and native runtime compatibility have not been proven.
- Phoenix Key remains a verified unsigned preview with partial lifecycle evidence, not a release artifact.

## PhoenixCore Desktop and Mobile

- The current dashboard is a Vite browser application, not a verified desktop package.
- A desktop runtime, installer, lifecycle receipt, update path, rollback path, and ARCWYRE package remain open.
- PhoenixCore Mobile’s complete phone-to-desktop-to-USB handoff is not yet proven end to end.

## External tool retrieval

- External-tool retrieval is currently blocked by the unavailable trusted registry path.
- Network paths are mostly mocked in unit tests.
- Current tests do not prove upstream availability, publisher signature validity, license compliance, or redistribution rights.
- Redirect and origin policy require further hardening.

## Repository state

- The repository remains large and contains historical plans, generated output, recovered prototypes, and overlapping implementations.
- A complete asset/history cleanup has not been performed.
- Not every product idea in the repository is part of the supported surface.

## Unsupported claims

PhoenixCore does not currently claim:

- production readiness
- general hardware compatibility
- universally safe physical disk writing
- completed bootable-media creation
- completed Windows, Linux, macOS, or ARCWYRE installation workflows
- firmware flashing
- activation, FRP, MDM, credential, ownership, or anti-theft bypass
- a functioning trusted external-tool registry
- independent security review
- reproducible production artifacts
- release-candidate status

These limitations remain active until reviewed machine evidence explicitly replaces them.
