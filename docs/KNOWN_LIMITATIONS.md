# Known Limitations

This file records current limitations of the PhoenixCore foundation. It is intentionally stricter than historical plans or feature checklists.

## Trust and registry validation

- `validate_tool_against_registry()` currently returns success when no registry object is available.
- This is fail-open behavior and blocks any production trust claim.
- The repository contains a direct Python Ed25519 implementation that requires independent review and replacement or validation against a maintained cryptographic library before release promotion.
- A registered URL and SHA-256 value do not by themselves prove upstream publisher identity or package signing.

## Device discovery

- Windows discovery currently enumerates logical removable/CD-ROM volumes rather than proving an immutable whole-disk identity.
- Linux discovery relies on `lsblk` output and removable flags; it does not yet retain a complete hardware identity receipt.
- macOS discovery uses `diskutil` and broad removable/external fields; edge cases require named-hardware tests.
- Scanner output does not by itself authorize planning or mutation.

## Rescue structure creation

- `create_rescue_usb_structure()` creates directories and a README on an existing mounted path.
- It does not partition, format, image, install a bootloader, write firmware, or prove bootability.
- The supplied path is not yet bound to a prior immutable target-identity receipt.
- Dry-run mode proves only that the planning code completed without writing.

## External tool retrieval

- The OCLP retrieval path depends on GitHub release metadata and current registry values.
- Network behavior is mocked in unit tests; the tests do not prove current upstream availability, publisher signature validity, or redistribution rights.
- The current domain-string check is not a complete URL-origin or redirect security policy.

## Dashboard

- A successful Vite build proves compilation, not live-device integration.
- Browser previews may contain fixture or sample data and must label it clearly.
- Accessibility, responsive behavior, performance budgets, and complete failure states are not yet evidenced.

## Repository state

- The repository is unusually large and may contain duplicate assets, generated output, recovered prototypes, and historical planning material.
- A canonical supported source tree has not yet been declared.
- Root-level dependency, build, test, security, release, and support policies remain incomplete.

## Unsupported claims

PhoenixCore does not currently claim:

- production readiness
- general hardware compatibility
- physical disk-write safety
- bootable-media creation
- firmware flashing
- account, activation, carrier, bootloader, or security bypass
- hardware validation across Windows, macOS, or Linux
- independent security review
- reproducible release artifacts

These limitations remain active until machine evidence and reviewed documentation explicitly replace them.
