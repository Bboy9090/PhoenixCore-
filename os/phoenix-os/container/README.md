# Phoenix OS Containerized Builder

This directory contains the OCI-compliant build environment for Phoenix OS.

## Files
- `Dockerfile`: The Debian-based build image definition.
- `docker-compose.yml`: Runtime configuration for volume mapping and privileges.
- `build-container.sh`: Wrapper to build the image and run the ISO pipeline.
- `verify-container.sh`: Wrapper to verify the skeleton inside the container.

## Quick Start
From the project root:
```bash
bash os/phoenix-os/container/verify-container.sh
```

## Requirements
Requires **Docker Desktop** (or Podman) with **Privileged Mode** support.
