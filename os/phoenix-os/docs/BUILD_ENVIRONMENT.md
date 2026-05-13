# Phoenix OS Build Environment Requirements

This document specifies the environment required to successfully build the Phoenix OS ISO.

## Supported Host Environments
1. **Debian 12 (Bookworm)**: Recommended (Native).
2. **Ubuntu 22.04/24.04**: Supported.
3. **OCI Container**: Supported via `--privileged` Docker/Podman run.

## Required Packages
```bash
sudo apt-get update
sudo apt-get install -y \
    live-build \
    debian-archive-keyring \
    curl \
    git \
    make
```

## Command Sequence (Native Linux)
```bash
# 1. Clone repository
git clone https://github.com/phoenix-platform/phoenix-core-enterprise

# 2. Enter OS directory
cd os/phoenix-os

# 3. Verify skeleton
sudo bash scripts/verify-build.sh

# 4. Run build
sudo bash scripts/build-iso.sh
```

## Expected Output
- **Path**: `os/phoenix-os/build/live-image-amd64.hybrid.iso`
- **Size**: ~1.2GB - 1.8GB
- **Checksum**: `SHA256SUMS` generated in build directory.

## Known Limitations
- **Windows/macOS**: Cannot build native ISO directly; must use OCI container.
- **Network**: Internet access required to fetch packages during chroot phase.
- **Disk Space**: At least 20GB of free space recommended for chroot and temporary squashfs layers.
