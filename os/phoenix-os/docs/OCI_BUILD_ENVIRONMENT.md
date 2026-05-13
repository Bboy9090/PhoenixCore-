# Phoenix OS OCI Build Environment

The Phoenix OS OCI build environment runs Debian live-build tooling inside a Docker Compose managed builder. It is intended for Windows/WSL2, native Linux, macOS Docker Desktop, and remote Linux build VMs.

## Scope

PR22 restores container orchestration only. It does not claim ISO generation.

Allowed behavior:

- Build a Debian-based OCI builder image.
- Verify required build tools inside the container.
- Run non-destructive Phoenix OS build skeleton checks.
- Write build artifacts only under `os/phoenix-os/build/`.

Disallowed behavior:

- Host disk formatting.
- Installer execution.
- Host device passthrough mounts.
- Package manager replacement.
- ISO success claims unless a real `.iso` exists.

## Files

- `os/phoenix-os/container/Dockerfile`
- `os/phoenix-os/container/docker-compose.yml`
- `os/phoenix-os/container/verify-container.sh`
- `os/phoenix-os/container/build-container.sh`
- `os/phoenix-os/scripts/verify-build.sh`
- `os/phoenix-os/scripts/build-iso.sh`

## Runtime Requirements

- Docker with Compose v2 (`docker compose version`)
- Privileged container support for live-build mount/chroot operations
- macOS Apple Silicon hosts must support `linux/amd64` container emulation

The Compose service defaults to:

```text
PHOENIX_OS_PLATFORM=linux/amd64
```

Override only when the build target is intentionally changed:

```bash
PHOENIX_OS_PLATFORM=linux/amd64 bash os/phoenix-os/container/verify-container.sh
```

## Verification

From the repository root:

```bash
bash os/phoenix-os/container/verify-container.sh
```

The verifier builds the builder image if needed and checks:

```bash
lb --version
debootstrap --version
xorriso -version
mksquashfs -version
```

It then runs:

```bash
bash os/phoenix-os/scripts/verify-build.sh
```

inside the container.

## Build Attempt

From the repository root:

```bash
bash os/phoenix-os/container/build-container.sh
```

The build wrapper first calls `verify-container.sh`, then runs:

```bash
bash os/phoenix-os/scripts/build-iso.sh
```

inside the container.

`build-iso.sh` refuses to run live-build unless real live-build configuration exists under `os/phoenix-os/live-build/`. If an ISO is produced, `build-container.sh` reports its path and SHA256 checksum. If no ISO exists, it exits with failure.

## Mounts

The builder uses only these bind mounts:

- repository root mounted read-only at `/workspace`
- `os/phoenix-os/build/` mounted read-write at `/workspace/os/phoenix-os/build`

No host block devices are mounted.

## Cleanup

Remove the builder image and Compose resources with normal Docker commands if needed:

```bash
docker compose -f os/phoenix-os/container/docker-compose.yml --project-directory os/phoenix-os/container --project-name phoenix-os-oci down
```

This does not remove `os/phoenix-os/build/`.
