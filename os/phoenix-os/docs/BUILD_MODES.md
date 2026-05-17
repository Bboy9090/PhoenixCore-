# Phoenix OS Build Modes and Architectures

This document details the build mode selection and architecture support configured for the dynamic OCI synthesis engine.

---

## ⚡ Command Line Options

The build wrapper script `/os/phoenix-os/container/build-container.sh` supports the following dynamic flags:

| Flag | Options | Default | Description |
|---|---|---|---|
| `--mode` | `fast`, `full`, `release-hardened` | `release-hardened` | Selects package list profiles (Minimal vs Full KDE vs Release). |
| `--arch` | `amd64`, `arm64` | `amd64` (default) / `arm64` (auto on M1) | Sets target instruction set architecture. |
| `--clean` | *None* | *None* | Wipes working directory and persistent APT package caches. |
| `--no-cache` | *None* | *None* | Bypasses persistent apt package caches, forcing fresh downloads. |
| `--verify-only` | *None* | *None* | Runs pre-flight verification checks without initiating build. |

---

## 💻 Apple Silicon (M1/M2/M3) Best Practices

To accelerate your local development cycles:

```bash
# 1. Native ARM64 Speed Build (Minimal desktop, builds in ~3 mins)
bash os/phoenix-os/container/build-container.sh --mode fast --arch arm64

# 2. Native ARM64 Full Build (Full recovery tools, builds in ~8 mins)
bash os/phoenix-os/container/build-container.sh --mode full --arch arm64

# 3. Target Release Candidate Build (Full emulation, builds in ~15 mins)
bash os/phoenix-os/container/build-container.sh --mode release-hardened --arch amd64
```

---

## 🧪 Cache Management

To clear the persistent APT chroot cache and temporary workspaces back to a clean state:

```bash
bash os/phoenix-os/container/build-container.sh --clean
```
