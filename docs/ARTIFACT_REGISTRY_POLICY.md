# Artifact Registry Policy

## Purpose

The BWOS / Blue Phoenix OS artifact registry makes boot artifacts traceable, testable, and hard to confuse with older build products.

Quality rule:

> A boot artifact without provenance and test status is only a file, not a release.

## Scope

The registry covers every `.iso` and `.img` found in:

- `iso/outputs`
- `os/phoenix-os/build`

The scanner records both locations because build output copies and release output copies can exist at the same time. Duplicate files are recorded by checksum; they are not deleted by PR38.

## Source Of Truth

The source of truth is:

- Policy: `docs/ARTIFACT_REGISTRY_POLICY.md`
- PR record: `docs/release/PR38_MULTI_EDITION_ARTIFACT_REGISTRY.md`
- Boot matrix record: `docs/release/PR39_VM_BOOT_MATRIX.md`
- Human table: `iso/ARTIFACTS.md`
- VM matrix table: `iso/BOOT_MATRIX.md`
- Machine registry: `iso/outputs/manifest.json`
- Boot matrix data: `iso/outputs/vm-boot-matrix.json`
- Scanner: `iso/scripts/scan-artifacts.sh`
- Boot checklist: `iso/scripts/vm-boot-checklist.sh`
- Validator: `iso/scripts/validate-artifacts.sh`

`iso/outputs/manifest.json` is generated data. Do not hand-edit it unless the scanner is broken and the manual edit is documented in the PR record.

## Required Metadata

Each artifact entry must record:

- Edition ID
- Display name
- Artifact filename
- Path
- Architecture
- Size in bytes
- SHA256
- Build timestamp, when available
- Source commit context
- Edition manifest path
- Edition manifest SHA256, when available
- Build mode
- Boot status
- App validation status
- Safety validation status

The current scanner uses filesystem mtime as the build timestamp source because the existing boot artifacts do not embed a trusted build timestamp. Source commit is recorded as the Git `HEAD` at scan time and is marked `git_head_at_scan_not_embedded`; it is provenance context, not proof that the artifact was built from that exact tree.

## Status Fields

Allowed status values:

- `built`
- `checksum_verified`
- `vm_boot_untested`
- `vm_boot_pass`
- `vm_boot_fail`
- `usb_boot_untested`
- `usb_boot_pass`
- `usb_boot_fail`
- `release_blocked`
- `release_candidate`

Allowed VM boot classifications:

- `BOOT_PASS_DESKTOP`
- `BOOT_PASS_BOOTLOADER_ONLY`
- `BOOT_FAIL_KERNEL`
- `BOOT_FAIL_INITRAMFS`
- `BOOT_FAIL_DISPLAY`
- `NOT_TESTED`
- `BLOCKED_BY_VM_TOOLING`

## Release Readiness Rules

- Do not claim boot success unless VM or hardware boot was explicitly tested and recorded.
- Do not mark an edition `release_candidate` while VM boot, USB boot, app validation, or safety validation is untested.
- Do not treat structural boot preflight as VM boot success.
- Do not treat `BOOT_PASS_BOOTLOADER_ONLY` as desktop readiness.
- Do not treat `BOOT_PASS_DESKTOP` as release readiness without app and safety validation.
- Do not delete or replace an ISO without preserving registry history in docs or Git history.
- Do not silently overwrite canonical metadata. Regenerate the manifest and review the diff.
- Duplicate artifacts are warnings until intentionally archived or removed by a documented cleanup PR.

## Registry Commands

Generate machine registry:

```bash
bash iso/scripts/scan-artifacts.sh --json > iso/outputs/manifest.json
```

Generate human table:

```bash
bash iso/scripts/scan-artifacts.sh --markdown > iso/ARTIFACTS.md
```

Generate boot matrix:

```bash
bash iso/scripts/vm-boot-checklist.sh --markdown > iso/BOOT_MATRIX.md
```

Validate registry:

```bash
bash iso/scripts/validate-artifacts.sh
```

## Promotion Gate

A boot artifact can move from `release_blocked` to `release_candidate` only after:

- Current ISO exists exactly once in `iso/outputs`.
- SHA256 matches registry metadata.
- Edition manifest hash is recorded.
- VM boot status is `vm_boot_pass`.
- USB boot status is `usb_boot_pass`, or the PR explicitly scopes the candidate to VM-only.
- App validation is recorded as pass for the edition scope.
- Safety validation is recorded as pass.
- Known duplicate or legacy artifacts are archived or documented.
