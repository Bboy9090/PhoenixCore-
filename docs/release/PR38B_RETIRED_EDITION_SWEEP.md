# PR38B Retired Edition Reference Sweep

**Status:** PASS
**Date:** 2026-05-23

## Active Edition List

- `home`
- `thunder-god`
- `blue-phoenix` / Aurelia
- `arcwyre`
- `native` research-only

## Retired Edition List

- `forge`
- `revival`
- `resilient`

## What Changed

- Active-surface docs were rewritten to remove exact-word retired edition references.
- Generator and validator behavior continues to filter archived editions out of active registry and boot-matrix outputs.
- Active ISO artifact outputs remain limited to the constrained edition set.

## Files Changed

- `docs/CHANGE_OF_PLANS_PRD.md`
- `docs/ARCWYRE_REBRAND_MAP.md`
- `docs/ARCWYRE_PLATFORM_ARCHITECTURE.md`
- `docs/ARCWYRE_NATIVE_PRD.md`
- `docs/ARCWYRE_PHASE_2_AUDIT.md`
- `docs/BRAND_IDENTITY.md`
- `docs/phoenix_brand/phoenix_forge.md`
- `docs/phoenix_key_legendary_blueprint.md`
- `docs/phoenix_docs/index.md`
- `docs/phoenix_docs/linux_rescue_playbook.md`
- `docs/phoenix_docs/windows_driver_inject.md`
- `docs/phoenix_docs/phoenix_emergency_manual.md`
- `docs/ownership/active-systems.md`
- `docs/ownership/preserve-do-not-touch.md`
- `docs/audits/2026-05-11-repo-inventory.md`
- `docs/audits/2026-05-11-phoenix-platform-map.md`
- `docs/MIGRATION_CHECKLIST.md`
- `scripts/build-all-isos.sh`
- `scripts/create-multiboot-usb.sh`
- `iso/scripts/scan-artifacts.sh`
- `iso/scripts/validate-artifacts.sh`
- `iso/scripts/vm-boot-checklist.sh`
- `iso/outputs/manifest.json`
- `iso/ARTIFACTS.md`
- `iso/BOOT_MATRIX.md`
- `iso/outputs/vm-boot-matrix.json`

## Generator Changes

- `scripts/build-all-isos.sh` now skips editions whose manifests are marked `archived: true`.
- `scripts/create-multiboot-usb.sh` now emits only active boot artifacts and active menu entries.
- `iso/scripts/scan-artifacts.sh` now filters archived editions out of the generated registry output.
- `iso/scripts/vm-boot-checklist.sh` now filters archived editions out of the active boot matrix.

## Validator Changes

- `iso/scripts/validate-artifacts.sh` now treats archived editions as non-active and excludes them from active artifact validation.
- Active registry outputs were regenerated and verified:
  - `iso/outputs/manifest.json`
  - `iso/ARTIFACTS.md`
  - `iso/outputs/vm-boot-matrix.json`
  - `iso/BOOT_MATRIX.md`

## Reference Counts

- Active-surface exact-word hits for `Forge`: `0`
- Active-surface exact-word hits for `Revival`: `0`
- Active-surface exact-word hits for `Resilient`: `0`
- Archived-manifest exact-word hits preserved in `editions/forge/*`: `4`
- Archived-manifest exact-word hits preserved in `editions/revival/*`: `4`
- Archived-manifest exact-word hits preserved in `editions/resilient/*`: `4`

## Intentionally Preserved References

- `editions/forge/edition.yaml`, `editions/revival/edition.yaml`, and `editions/resilient/edition.yaml` remain in the tree as archived concepts.
- Each archived edition manifest contains `archived: true`.
- Historical release reports and migration notes may still mention retired concepts when documenting the transition.

## References Removed From Active Surface

- Standalone `Forge` references in active ARCWYRE docs were replaced with build, recovery, assembly, or deployment language.
- Standalone `Revival` and `Resilient` references were already confined to archived edition manifests.
- Active output files no longer contain retired edition names.

## Validation Commands

- `bash -n` on all existing changed shell scripts from the current diff
- `git diff --check`
- `rg -n -w "Forge" docs scripts os iso README.md server services backend --glob '!docs/archive/**' --glob '!docs/release/**'`
- `rg -n -w "Revival|Resilient" docs scripts os iso README.md server services backend --glob '!docs/archive/**' --glob '!docs/release/**'`
- `rg -n -w "Forge|Revival|Resilient" iso/outputs/manifest.json iso/ARTIFACTS.md iso/BOOT_MATRIX.md iso/outputs/vm-boot-matrix.json`

## Remaining Risks

- Historical release reports can still mention retired concepts by design.
- Archived edition folders remain present and must continue to be filtered by every active registry or matrix generator.
- Any future edition-metadata generator that stops checking `archived: true` would reintroduce retired concepts into active outputs.
