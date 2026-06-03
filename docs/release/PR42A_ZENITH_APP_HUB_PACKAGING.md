# PR42A: Zenith App Hub Debian Packaging

## Overview
This document outlines the pipeline for pre-compiling the Zenith App Hub into a native Debian (`.deb`) package for integration into the Phoenix OS SquashFS.

## Pipeline Configuration
- **Source Path:** `apps/native-app-hub`
- **Build Command:** `pnpm tauri build --bundles deb`
- **Expected `.deb` Output Path:** `apps/native-app-hub/src-tauri/target/release/bundle/deb/`
- **Staged `packages.chroot` Path:** `os/phoenix-os/live-build/config/packages.chroot/tauri-app_0.1.0_amd64.deb`

## Local Validation
The wrapper script (`scripts/build-zenith-app-hub-deb.sh`) was executed locally to validate the build environment.

**Validation Command:**
```sh
bash -n scripts/build-zenith-app-hub-deb.sh
./scripts/build-zenith-app-hub-deb.sh
```

## Known Blockers ❌
The local host build **failed** due to a missing cross-compilation toolchain. 

When executing the Tauri bundler on the host machine (macOS / Darwin), Tauri can only output native targets for that operating system (`[possible values: ios, app, dmg]`). It rejects `--bundles deb` because the Linux ABI and Debian packaging dependencies (like `dpkg`) are missing from the macOS host environment.

**Exact Missing Dependency / Toolchain:**
To successfully bundle the `.deb` file on a macOS host, we must either:
1. Wrap the build script inside a Docker container (e.g., using an `ubuntu:bullseye` image with Rust and Node installed).
2. Install a Rust cross-compilation toolchain like `cargo-zigbuild` along with `dpkg` and Linux GTK libraries via Homebrew/MacPorts (which is highly error-prone).

**Conclusion:** The packaging script is structurally correct, but cannot succeed natively on the current macOS host. A containerized builder or CI/CD Linux runner is required to produce the `.deb`.
