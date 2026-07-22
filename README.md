# PhoenixCore

**Device intelligence, diagnostics, recovery planning, and evidence orchestration for Bobby’s Workshop.**

PhoenixCore helps an authorized owner or technician understand a connected device, identify its current mode and supported capabilities, and produce a cautious recovery plan before any mutation is considered.

## Current maturity

**Status: prototype with tested read-only and dry-run foundations.**

This repository contains working code and tests, but it is not yet a production device-repair platform. It does not currently carry a general hardware-support, physical-write, firmware-flashing, bypass, or production-readiness claim.

## Supported foundation

The clearest currently testable path is the Python USB/rescue-planning module plus the React dashboard:

- cross-platform removable-device enumeration
- SHA-256 file identity calculation
- signed tool-registry loading and tamper rejection
- registered tool URL and checksum comparison
- dry-run rescue-directory planning
- non-destructive directory-structure creation on an explicitly supplied mounted path
- dashboard development, lint, and production build commands

The active fan-favorite foundation issue is [#125](https://github.com/Bboy9090/PhoenixCore-/issues/125).

## Important safety blocker

`usb_creator.validate_tool_against_registry()` currently returns success when the registry loader returns no registry. That is a **fail-open behavior** and is not accepted as a production security boundary.

Until it is corrected and regression-tested:

- do not treat registry validation as authoritative when the manifest is unavailable
- do not use this code to approve downloads or physical device mutation
- do not describe the tool supply chain as fully fail-closed

The portfolio standard requires missing, invalid, ambiguous, or unsupported trust evidence to block approval.

## Quick start

### Python foundation

Requirements:

- Python 3.11 or newer
- platform utilities used by the selected read-only scanner, such as `lsblk` on Linux or `diskutil` on macOS

Run the test suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

List detected removable devices without mutation:

```bash
python usb_creator.py --list
```

Simulate the rescue-directory plan without writing files:

```bash
python usb_creator.py --create /path/to/mounted/target --dry-run
```

The non-dry-run `--create` path creates folders and a text README on the supplied mounted target. It is not a disk imager, partitioner, formatter, bootloader installer, or firmware writer.

### Dashboard

Requirements:

- Node.js compatible with the locked Vite toolchain
- npm

```bash
cd dashboard
npm ci
npm run lint
npm run build
npm run dev
```

Browser data must be labeled as live, fixture, or sample data. A successful frontend render is not hardware validation.

## Product boundaries

PhoenixCore owns:

- device identity and mode interpretation
- read-only diagnostics
- capability and limitation analysis
- recovery-plan generation
- evidence and receipt orchestration
- cross-device coordination contracts

PhoenixCore does not own:

- the ARCWYRE Native kernel or operating system
- BootForge’s reusable low-level USB primitives
- Phoenix Key’s end-user boot-media experience
- Bobby’s Workshop’s complete technician workspace
- hidden bypass, lock removal, unauthorized access, or unsupported destructive actions

See [`docs/PRODUCT_BOUNDARIES.md`](docs/PRODUCT_BOUNDARIES.md).

## Repository truth rules

1. A feature is supported only when the documented command, test, and evidence exist.
2. Fixture or sample data is never presented as live hardware data.
3. Dry-run success is not a physical-write receipt.
4. QEMU or mocked tests are not hardware validation.
5. Missing trust, identity, permission, or target evidence fails closed.
6. Historical plans and recovered prototypes do not override current machine evidence.

## Quality gates

The foundation workflow is intended to verify:

- Python compilation
- Python unit tests
- dashboard locked dependency installation
- dashboard lint
- dashboard production build
- explicit detection of the current fail-open registry blocker

A passing foundation workflow proves only those gates. It does not prove production readiness or hardware support.

## Documentation

- [Product boundaries](docs/PRODUCT_BOUNDARIES.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [Fan-favorite foundation issue](https://github.com/Bboy9090/PhoenixCore-/issues/125)
- [Portfolio program](https://github.com/Bboy9090/Bboy9090/issues/4)

## Security

Do not report sensitive device data, credentials, private keys, account tokens, personal identifiers, or proprietary firmware in public issues. Security-sensitive reports should include the smallest reproducible description and omit user data.

A dedicated security policy and supported disclosure channel remain part of the foundation issue before release promotion.

## License and third-party tools

Third-party recovery utilities retain their own licenses, support boundaries, trademarks, and distribution rules. A registry entry or integration plan does not transfer ownership, certify safety, or grant redistribution rights.

PhoenixCore must preserve source provenance and verify every external artifact through the strongest supported upstream mechanism before use.
