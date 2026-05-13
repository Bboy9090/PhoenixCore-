# PR22 OCI Script Restore

Date: 2026-05-13

## Summary

PR22 restores the Phoenix OS OCI container orchestration path needed before truthful ISO verification/build execution can resume.

## Files Added

- `os/phoenix-os/container/Dockerfile`
- `os/phoenix-os/container/docker-compose.yml`
- `os/phoenix-os/container/verify-container.sh`
- `os/phoenix-os/container/build-container.sh`
- `os/phoenix-os/scripts/verify-build.sh`
- `os/phoenix-os/scripts/build-iso.sh`
- `os/phoenix-os/docs/OCI_BUILD_ENVIRONMENT.md`
- `docs/release/PR22_OCI_SCRIPT_RESTORE.md`

## Safety Boundaries

- No host device mounts.
- No disk formatting.
- No installer logic.
- No package manager replacement.
- Repository root is mounted read-only.
- Artifacts are written only under `os/phoenix-os/build/`.
- `build-container.sh` reports ISO path/checksum only when a real `.iso` exists.

## Verification Commands

```bash
bash -n os/phoenix-os/container/verify-container.sh
bash -n os/phoenix-os/container/build-container.sh
bash os/phoenix-os/container/verify-container.sh
```

Observed result on the PR22 macOS Docker Desktop host:

- `verify-container.sh` passed.
- required tools were present inside the builder: `lb`, `debootstrap`, `xorriso`, `mksquashfs`.
- `build-container.sh` exited `1` truthfully because no real live-build configuration exists yet.

## Expected Current Build State

`verify-container.sh` should pass on a host with Docker/Compose and privileged container support.

`build-container.sh` is expected to fail truthfully until real live-build configuration is added under `os/phoenix-os/live-build/`.

## Next Recommended PR

PR23: Phoenix OS live-build configuration foundation

Recommended scope:

- add minimal real live-build config under `os/phoenix-os/live-build/`
- define package list ingestion from `os/phoenix-os/package-lists/`
- run `build-container.sh`
- publish real build logs, ISO path, and SHA256 only if the ISO exists
