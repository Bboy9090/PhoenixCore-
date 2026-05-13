# Phoenix OS — Build System

## Overview

Phoenix OS uses **live-build** (`lb`), Debian's official live system construction toolkit, to produce bootable ISO images. The build system is designed to run on Ubuntu 22.04 LTS or 24.04 LTS and produces a hybrid ISO that boots from both USB (via `dd` or Etcher) and DVD.

---

## Host Requirements

### Operating System

- Ubuntu 22.04 LTS or 24.04 LTS (bare metal or VM)
- **Not supported:** WSL, macOS, Fedora/RHEL hosts (different debootstrap behavior)
- Minimum 8 GB RAM (16 GB recommended)
- Minimum 40 GB free disk space for build workspace
- Internet connection for package downloads (first build ~3–8 GB download)

### Required Packages

```bash
sudo apt update
sudo apt install -y \
    live-build \
    debootstrap \
    squashfs-tools \
    xorriso \
    grub-pc-bin \
    grub-efi-amd64-bin \
    grub-efi-amd64-signed \
    shim-signed \
    mtools \
    dosfstools \
    isolinux \
    syslinux-common \
    syslinux-efi \
    memtest86+ \
    git \
    curl \
    wget \
    dpkg-dev \
    devscripts \
    debhelper
```

Run `./scripts/verify-host.sh` to check all requirements before building.

---

## Build Directory Structure

```
live-build/
├── config/                   # lb configuration files
│   ├── bootstrap             # Debootstrap settings
│   ├── chroot                # Chroot environment settings
│   ├── binary                # ISO assembly settings
│   └── common                # Shared settings
├── package-lists/            # Package list files (.list.chroot)
│   ├── 000-base.list.chroot
│   ├── 010-kde-plasma.list.chroot
│   ├── 020-repair-tools.list.chroot
│   ├── 030-disk-tools.list.chroot
│   ├── 040-network-tools.list.chroot
│   ├── 050-recovery-tools.list.chroot
│   ├── 060-firmware.list.chroot
│   ├── 070-flatpak.list.chroot
│   └── 080-phoenix-apps.list.chroot
├── hooks/                    # Scripts run during build phases
│   ├── live/                 # Hooks for live environment
│   └── normal/               # Hooks for installed system
└── includes.chroot/          # Files overlaid onto the chroot filesystem
    ├── etc/
    │   ├── skel/             # Default user home directory files
    │   ├── apt/              # APT configuration
    │   └── default/          # System defaults
    └── usr/
        ├── share/applications/  # Desktop entries
        ├── share/pixmaps/       # Icons
        └── local/bin/           # Phoenix utility scripts
```

---

## Building the ISO

### Step 1: Verify Host

```bash
cd phoenix-os
./scripts/verify-host.sh
```

This checks for required packages, disk space, and network connectivity. Fix any reported issues before proceeding.

### Step 2: Run the Build

```bash
sudo ./scripts/build-iso.sh
```

This script runs the full live-build pipeline. Expected duration:
- First build (cold cache): 25–60 minutes
- Subsequent builds (warm cache): 15–30 minutes

### Step 3: Output

On success, the ISO is written to:

```
output/phoenix-os-<version>-amd64.iso
output/SHA256SUMS
```

### Step 4: Test

```bash
# QEMU test (requires kvm or qemu-system-x86_64)
./tests/smoke/test-boot.sh output/phoenix-os-*.iso

# Full ISO validation
./tests/iso-validation/validate-iso.sh output/phoenix-os-*.iso
```

---

## Build Options

The build script accepts environment variables:

```bash
# Build for a specific architecture (default: amd64)
ARCH=arm64 sudo ./scripts/build-iso.sh

# Set a custom version string (default: reads from VERSION file)
PHOENIX_VERSION=1.0.0-beta sudo ./scripts/build-iso.sh

# Keep build workspace after completion (useful for debugging)
KEEP_BUILD=1 sudo ./scripts/build-iso.sh

# Verbose live-build output
LB_VERBOSE=1 sudo ./scripts/build-iso.sh
```

---

## Incremental Builds

live-build supports partial rebuilds. After a full build, you can re-run specific stages:

```bash
# Redo only the binary (ISO assembly) stage — fast, useful for branding changes
sudo lb binary

# Redo chroot + binary (re-installs packages, runs hooks)
sudo lb chroot && sudo lb binary

# Full clean rebuild
sudo ./scripts/clean.sh && sudo ./scripts/build-iso.sh
```

**Warning:** Running `lb chroot` after `lb bootstrap` is faster than a full rebuild but uses the cached debootstrap. If you change the Ubuntu base version or mirror, run a full clean.

---

## Package Cache

live-build caches downloaded .deb files in `.build/cache/packages/`. This cache persists across `./scripts/clean.sh` runs. To also clear the package cache:

```bash
sudo ./scripts/clean.sh --all
```

---

## Hooks

Hooks are shell scripts executed at specific points in the build:

| Hook type | When it runs | Use for |
|-----------|-------------|---------|
| `chroot` hooks in `hooks/live/` | Inside the chroot, after packages | Configuration, symlinks, user creation |
| `binary` hooks in `hooks/normal/` | After chroot, before ISO assembly | ISO metadata, GRUB customization |

Hook filenames must follow the pattern `NNN-description.hook.chroot` or `NNN-description.hook.binary` (NNN = three-digit order number).

---

## Custom Package Integration

To include locally-built .deb packages in the ISO:

1. Build the package: `./scripts/package-debs.sh packages/phoenix-control-center`
2. The script copies the .deb to `live-build/config/packages.chroot/`
3. Re-run the build; live-build installs local packages before pulling from apt

---

## Troubleshooting

### Build fails at debootstrap stage
- Check internet connectivity
- Try a different Ubuntu mirror: edit `live-build/config/common` → `LB_MIRROR_BOOTSTRAP`

### "No space left on device" during lb build
- The build workspace needs ~25 GB minimum. Clean up or use a larger disk.

### Package not found during chroot install
- Verify the package name against `apt-cache search <name>` on a running Ubuntu 24.04 system
- Check if the package requires a non-standard PPA (add PPA setup to a hook)

### ISO doesn't boot in UEFI mode
- Ensure `grub-efi-amd64-signed` and `shim-signed` are installed on the build host
- Verify EFI binaries are present: `ls build/binary/EFI/`

### Live session fails to start X/Wayland
- Check `lb config` → display server settings
- Review `/var/log/sddm.log` in the running live session
