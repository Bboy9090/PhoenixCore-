# PR42B: Zenith App Hub Linux Container Builder

## Overview
Because the Phoenix OS build environment runs on a macOS (Darwin) host, natively bundling Linux Debian packages (`.deb`) via Tauri is fundamentally blocked by the host OS ABI and missing Linux tools (e.g., `dpkg-dev`, `patchelf`). 

To resolve this without altering the host environment, we introduced a Docker-based containerized build pipeline.

## Implementation Details
- **Wrapper Script:** `scripts/build-zenith-app-hub-deb-container.sh`
- **Internal Script Executed:** `scripts/build-zenith-app-hub-deb.sh`
- **Container Environment:** `ubuntu:22.04` (forced `--platform linux/amd64` for x86_64 Debian targeting)
- **Volume Mount:** `$REPO_ROOT:/workspace`
- **Toolchain Injected:**
  - Rust & Cargo
  - Node.js & pnpm
  - Linux GTK3, WebKit2GTK, Ayatana Indicators (Tauri requirements)
  - `dpkg-dev`, `patchelf`, `build-essential`

## Process
1. The wrapper script initializes a pristine Linux container.
2. It installs all essential Tauri cross-compilation and Debian packaging dependencies.
3. It mounts the PhoenixCore repository and executes the original `build-zenith-app-hub-deb.sh` script within the Linux context.
4. The `.deb` package is produced locally.
5. Due to the volume mount, the resulting `.deb` is natively staged back to the macOS host at `os/phoenix-os/live-build/config/packages.chroot/`.

## Local Validation Run
The containerized builder has been executed on the host. If a `.deb` was successfully produced, the output of `dpkg-deb --info` will be logged as evidence of success. 

**Note:** No ISO rebuild has been executed, and no physical hardware validation statuses have been changed.
