# BWOS Build Observability Model

## Purpose

BWOS builds are long-running and phase-heavy. The build system must report what it is doing without fabricating progress, ETA, or completion.

This model makes builds measurable and debuggable while preserving the truthful UI doctrine:

- report observed phases only
- distinguish slow from stalled
- record warnings and failures explicitly
- generate machine-readable summaries at the end of a build

## Canonical Phases

| Phase | Meaning |
| --- | --- |
| `preflight` | Build environment checks, manifest validation, and build ID initialization. |
| `manifest_resolution` | Edition manifest parsed and target architecture resolved. |
| `overlay_staging` | Edition assets, wallpapers, logos, and branding overlays are staged. |
| `package_resolution` | Package lists and package provenance are resolved and staged. |
| `debootstrap` | Base filesystem bootstrap and live-build bootstrap work. |
| `chroot_install` | Package installation inside the live-build chroot. |
| `package_configuration` | Package hooks, config generation, and chroot package setup. |
| `branding_hooks` | Plymouth, SDDM, wallpaper, and edition-specific visual hooks. |
| `initramfs_generation` | Kernel image and initramfs rebuild work. |
| `filesystem_assembly` | Squashfs or rootfs assembly. |
| `iso_or_img_assembly` | ISO or dd-image assembly. |
| `checksum_generation` | SHA256 and other artifact checksums. |
| `artifact_registration` | Artifact registry entry and canonical artifact naming. |
| `cleanup` | Cache cleanup, workspace cleanup, and final teardown. |
| `completed` | Build reached a truthful final success state. |
| `failed` | Build terminated with a classified failure. |

## Telemetry Outputs

Each build should emit:

- human-readable build log
- JSONL event stream
- heartbeat snapshots
- phase timing records
- build summary JSON
- build summary Markdown

### Human Log

The human log is for the person watching the build. It should mirror actual build activity without inventing completion, speed, or ETA.

### JSONL Event Stream

Each event is one JSON object per line. Events should include:

- timestamp
- build id
- edition id
- edition name
- architecture
- artifact target
- phase
- event type
- level
- message
- optional structured details

## Heartbeats

Heartbeats are a liveness signal, not a progress claim.

They should report:

- edition
- architecture
- current phase
- elapsed time
- last successful phase
- container status if available

Heartbeats must not invent:

- percent complete
- ETA
- boot success
- artifact success

## Slow vs Stalled

### Slow

A build is slow when:

- the active phase is known
- the build process is still alive
- logs continue to advance, even if slowly
- the container remains reachable

### Stalled

A build is stalled when:

- the active phase has not changed for an abnormal amount of time
- the process tree is still present, but no meaningful output arrives
- heartbeats continue, but the phase remains unchanged for too long

Stalled does not mean failed. It means humans should inspect the live state before assuming failure.

## Apple Silicon Notes

Running amd64 or i386 live-build work under Apple Silicon emulation can be much slower than native host builds.

Expected slow phases on Apple Silicon emulation:

- `package_resolution`
- `chroot_install`
- `filesystem_assembly`
- `iso_or_img_assembly`

This is normal. The presence of long-running package activity is not a failure.

## Failure Classification

If a build fails, classify it truthfully:

- `network_failure`
- `package_resolution_failure`
- `apt_lock_failure`
- `branding_failure`
- `overlay_failure`
- `artifact_missing`
- `initramfs_failure`
- `iso_assembly_failure`
- `wrapper_script_failure`
- `timeout`
- `unknown_failure`

## Summary Files

The final summary should record:

- edition
- artifact path
- SHA256
- size
- build duration
- phase timings
- warnings
- failures
- final status

## Operational Guidance

- Do not treat a live container as success.
- Do not treat a quiet terminal as a failure.
- Do not call a build complete until the artifact exists and the summary says it is complete.
- Use the watch script to see the current phase without mutating state.

