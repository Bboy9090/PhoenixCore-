# PhoenixCore

**Device intelligence, diagnostics, recovery planning, USB orchestration, and evidence coordination for Bobby’s Workshop, established 2026.**

PhoenixCore helps an authorized owner or technician identify a connected device, understand its current mode and supported capabilities, prepare a cautious recovery or installation plan, and hand that plan to Phoenix USB Creator and ARCWYRE Live through versioned contracts.

## Current maturity

**Status: integrated prototype with tested read-only, dry-run, artifact-receipt, and Windows installer lifecycle foundations.**

The repository contains working code and retained CI evidence. It is not yet a generally supported repair platform, boot-media factory, firmware service, or production release.

## Locked ecosystem position

- **Phoenix Prime Kernel** owns the shared native kernel.
- **ARCWYRE Native** is the lightweight repair-first native edition.
- **ARCWYRE Eternum** is the performance, creator, developer, and future gaming edition.
- **ARCWYRE Live** is the live repair and deployment environment.
- **PhoenixCore Mobile/Desktop** diagnose, plan, coordinate, and retain case evidence.
- **Phoenix USB Creator / Phoenix Key** prepare approved media and record write evidence.

PhoenixCore does not own the kernel and must not duplicate the native OS source tree.

## Supported foundation

The current tested surface includes:

- normalized read-only device and removable-drive payloads
- SHA-256 file and image identity
- fail-closed tool-registry rejection when trust evidence is unavailable
- missing, unsigned, invalid, malformed, and tampered registry rejection tests
- dry-run rescue and media planning
- guarded Windows Phoenix Key MSI/NSIS builds
- deterministic artifact receipts
- clean-runner Windows install, launch, uninstall, and cleanup receipts
- React dashboard locked install, lint, and production build

The committed tool-registry manifest/signature pair currently fails verification under the configured trust anchor. Registered-tool URL and checksum approval therefore remain unavailable and blocked under issue #136. The system denies approval rather than bypassing trust.

## Quick start

### Python foundation

```bash
python -m compileall -q usb_creator.py device_scanner.py tests/test_foundation_surface.py tests/test_registry_fail_closed.py
python -m unittest discover -s tests -p "test_foundation_surface.py" -v
python -m unittest discover -s tests -p "test_registry_fail_closed.py" -v
python usb_creator.py --list
python usb_creator.py --create /path/to/mounted/target --dry-run
```

The non-dry-run mounted-path structure command creates folders and a README. It is not a disk imager, partitioner, formatter, bootloader installer, or proof of bootability.

### Dashboard

```bash
cd dashboard
npm ci
npm run lint
npm run build
npm run dev
```

Browser data must be labeled as live, fixture, or sample. A successful frontend render is not hardware validation.

## Hardware evidence ladder

Real drive evidence is allowed through an explicit gated sequence:

1. read-only whole-drive identity receipt
2. exclusive-handle or busy-state proof with zero writes
3. explicit sacrificial-drive authorization
4. image and target identity revalidation
5. bounded write with pre/post receipts
6. complete read-back SHA-256 verification
7. boot receipt with machine, firmware, Secure Boot, display, and serial markers

Unknown, internal, boot, system, identity-mismatched, or non-authorized targets must fail closed. The dedicated hardware wave is tracked in issue #135.

## Product boundaries

PhoenixCore owns device interpretation, diagnostics, compatibility decisions, recovery planning, repair-session contracts, and evidence orchestration. BootForge owns reusable low-level discovery and guarded media primitives. Phoenix Key owns the user-facing media workflow. ARCWYRE owns native boot, kernel, userspace, live repair execution, and native evidence.

See [`docs/PRODUCT_BOUNDARIES.md`](docs/PRODUCT_BOUNDARIES.md).

## Truth rules

1. A feature is supported only when its code path, tests, caller integration, and evidence are identified.
2. Fixture or sample data is never represented as live hardware data.
3. Dry-run success is not physical-write evidence.
4. QEMU success is not hardware validation.
5. Missing trust, identity, permission, target, or provenance evidence fails closed.
6. A commit title such as `v1.0.0-PROD` is not production proof.
7. A preview installer is not an ARCWYRE-packaged application.

## Current non-claims

PhoenixCore does not currently claim:

- general hardware compatibility
- universally safe physical disk writing
- completed Windows, Linux, macOS, or ARCWYRE installation workflows
- firmware flashing
- ownership, activation, FRP, MDM, credential, or anti-theft bypass
- independently reviewed cryptography
- a functioning trusted external-tool registry
- reproducible production releases
- release-candidate status

## Documentation

- [Product boundaries](docs/PRODUCT_BOUNDARIES.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [Foundation issue #125](https://github.com/Bboy9090/PhoenixCore-/issues/125)
- [PhoenixCore Desktop packaging issue #131](https://github.com/Bboy9090/PhoenixCore-/issues/131)
- [Phoenix Key lifecycle issue #132](https://github.com/Bboy9090/PhoenixCore-/issues/132)
- [Hardware validation issue #135](https://github.com/Bboy9090/PhoenixCore-/issues/135)
- [Tool-registry trust issue #136](https://github.com/Bboy9090/PhoenixCore-/issues/136)

## Security

Never place credentials, private keys, account tokens, personal device identifiers, proprietary firmware, or user data in public receipts. Destructive actions require an explicit target, preview, authorization, backup warning, TruthLog entry, and result receipt.
