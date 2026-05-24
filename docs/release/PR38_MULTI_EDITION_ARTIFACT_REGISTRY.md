# PR38: Multi-Edition ISO Artifact Registry

Date: 2026-05-22

## Goal

Create a formal artifact registry for every generated BWOS / Blue Phoenix OS edition ISO so builds are traceable, testable, and not confused with older artifacts.

## Implemented

- Added artifact policy: `docs/ARTIFACT_REGISTRY_POLICY.md`
- Added generated human registry: `iso/ARTIFACTS.md`
- Added generated machine registry: `iso/outputs/manifest.json`
- Added scanner: `iso/scripts/scan-artifacts.sh`
- Added validator: `iso/scripts/validate-artifacts.sh`
- Added app roadmap note: `docs/BLUE_PHOENIX_APP_ROADMAP.md`
- Added app shipping waves note: `docs/APP_SHIPPING_WAVES.md`

## Editions Checked

| Edition | Current ISO | Manifest |
|---|---|---|
| Blue Phoenix Home | `iso/outputs/bwos-home.iso` | `editions/home/edition.yaml` |
| Blue Phoenix Aurelia | `iso/outputs/bwos-aurelia.iso` | `editions/blue-phoenix/edition.yaml` |
| ARCWYRE | `iso/outputs/bwos-arcwyre.iso` | `editions/arcwyre/edition.yaml` |
| Thunder God | `iso/outputs/bwos-thunder-god.iso` | `editions/thunder-god/edition.yaml` |

Architecture-specific variants such as `home-arm64`, `home-legacy-i386`, and `thunder-god-arm64` are compatibility build targets, not standalone editions.

Retired concept names are archived under `docs/archive/retired-editions/` and are excluded from the active registry surface.

## Artifact Findings

The scanner now limits the active registry surface to active editions and their live build copies.

Legacy build aliases and retired concept names are preserved in archive docs, but they are no longer emitted into the active registry.

## Validation Result

Command:

```bash
bash iso/scripts/validate-artifacts.sh
```

Result:

- Errors: 0
- Warnings: 21

Warning classes:

- ISO files exist outside `iso/outputs`.
- Duplicate artifact checksums exist between `iso/outputs` and `os/phoenix-os/build`.
- `phoenix-os-release-amd64.iso` has an unknown edition ID.
- VM boot status remains untested.
- USB boot status remains untested.
- App validation has not been recorded.
- Safety validation has not been recorded.
- Artifacts are release-blocked until validation is recorded.

## Truth-First Status

PR38 does not claim boot success.

Structural preflight exists for several images, but structural preflight is not VM boot success and not USB boot success. Every artifact remains `release_blocked` until boot, app, and safety validation are recorded.

## Commands Run

```bash
bash -n iso/scripts/scan-artifacts.sh
bash -n iso/scripts/validate-artifacts.sh
bash iso/scripts/scan-artifacts.sh --json > iso/outputs/manifest.json
bash iso/scripts/scan-artifacts.sh --markdown > iso/ARTIFACTS.md
bash iso/scripts/validate-artifacts.sh
```

## Recommended PR39

PR39 should be: Multi-Edition Boot/App/Safety Validation Promotion Gate.

Required PR39 work:

- Add per-edition VM boot test records.
- Add per-edition USB boot test records where hardware is available.
- Add app validation status per edition.
- Add safety validation status per edition.
- Decide whether `phoenix-os-release-amd64.iso` should be archived, renamed, or retained as a documented legacy alias.
- Embed build provenance into future ISOs so source commit is artifact-native instead of scan-context-only.
