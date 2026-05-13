# Phoenix OS OCI Build Environment

This document defines the containerized environment used to build Phoenix OS independently of the host operating system.

## Overview
The OCI (Open Container Initiative) build model ensures that the complex dependencies of `live-build` are encapsulated in a reproducible Debian-based image. This allows developers on Windows, macOS, and Linux to generate the same ISO artifacts.

## Supported Hosts
- **Docker Desktop**: (Windows/macOS/Linux)
- **Podman**: (Linux/macOS)
- **Native Docker**: (Linux)

## Prerequisites
- Docker or Podman installed.
- **Privileged Mode**: The container must run with `--privileged` flags (or `privileged: true` in compose) to allow the `lb` engine to perform loopback mounts and chroot operations.

## Usage Sequence
1. **Initialize Environment**:
   ```bash
   ./os/phoenix-os/container/verify-container.sh
   ```

2. **Run ISO Build**:
   ```bash
   ./os/phoenix-os/container/build-container.sh
   ```

## Security Considerations
- **Privileged Execution**: Use only in trusted environments. Privileged containers have access to host hardware and kernel features required for ISO generation.
- **Volume Mapping**: The container mounts the entire project root to allow the build process to access package manifests and scripts.

## Troubleshooting
- **Mount Failures**: Ensure your Docker host allows privileged containers. On Windows, ensure Docker is using the WSL2 backend.
- **Performance**: Building a live image involves heavy I/O. Use a fast SSD for the project workspace.
