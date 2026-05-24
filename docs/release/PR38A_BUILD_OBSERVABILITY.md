# PR38A Build Observability + Pipeline Telemetry

## Goal

Add structured observability to the BWOS / Blue Phoenix OS build pipeline so long-running edition builds are measurable, debuggable, and trustworthy.

## What PR38A Adds

- canonical build phase model
- structured event logging
- build heartbeats
- current-phase tracking
- phase timing records
- build summary JSON and Markdown
- safe build watch tooling
- explicit failure classification

## Non-Goals

- no fake progress
- no fake ETA
- no simulated success
- no destructive host operations
- no rewriting artifact outcomes

## Why This Matters

The platform now builds multiple editions, multiple architectures, and multiple artifact formats. When a build takes a long time, the output needs to explain itself truthfully instead of forcing humans to interpret terminal noise.

## Active Phase Model

The pipeline now uses a canonical sequence that maps observed live-build stages into:

- preflight
- manifest_resolution
- overlay_staging
- package_resolution
- debootstrap
- chroot_install
- package_configuration
- branding_hooks
- initramfs_generation
- filesystem_assembly
- iso_or_img_assembly
- checksum_generation
- artifact_registration
- cleanup
- completed
- failed

## Apple Silicon Emulation Guidance

Under Apple Silicon emulation, Debian live-build phases can be slow without being broken.

Expected slow areas include:

- package metadata refresh
- package installation
- initramfs generation
- squashfs assembly

The new telemetry does not hide that cost. It labels it.

## Next PR

PR39 should remain the VM boot matrix, but it should now consume the build telemetry so VM validation is tied to trustworthy artifacts rather than ambiguous files.

