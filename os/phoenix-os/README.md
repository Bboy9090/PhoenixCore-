# Phoenix OS Build Skeleton

This directory contains the reproducible build foundation for **Phoenix OS**, a KDE Plasma + Wayland-first operating system designed for the Phoenix Platform.

## Directory Structure
- `build/`: Temporary build artifacts and live-build chroot.
- `config/`: Configuration files for the `live-build` engine.
- `packages/`: Declarative package manifests (Base, KDE, Phoenix).
- `scripts/`: Build and verification orchestration.
- `branding/`: Naming, themes, and asset placeholders.
- `overlays/`: Filesystem overlays for the target image.
- `docs/`: Architecture and integration documentation.

## Getting Started
To initialize the build environment:
```bash
./scripts/build-iso.sh
```

To verify the skeleton integrity:
```bash
./scripts/verify-build.sh
```

## Safety Doctrine
This build system is strictly **non-destructive**. It generates immutable live images and does not include any installer logic capable of formatting system disks without explicit Phoenix Agent authorization.
