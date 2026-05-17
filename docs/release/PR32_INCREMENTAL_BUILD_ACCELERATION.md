# PR32 Phoenix OS Incremental Build Acceleration

This document details the advanced, deep build optimizations implemented in the **PR32 Incremental Build Acceleration Framework**.

---

## ⚡ 1. Local APT Cache and Proxy Support

Repeating mirror package downloads is a major bottleneck in containerized live-build environments. We have introduced native support for local caching proxies like `apt-cacher-ng`.

### **How to Set Up `apt-cacher-ng` on Host:**
1. Install it via Homebrew on macOS:
   ```bash
   brew install apt-cacher-ng
   brew services start apt-cacher-ng
   ```
2. By default, it runs on `http://localhost:3142`.
3. To trigger the OCI builder to pipe all package transactions through this local cache:
   ```bash
   export PHOENIX_APT_PROXY="http://172.17.0.1:3142"  # Docker gateway IP
   bash os/phoenix-os/container/build-container.sh --mode dev-minimal
   ```
4. If `PHOENIX_APT_PROXY` is empty or not set, `live-build` defaults safely to direct network mirror mirror queries.

---

## 🚀 2. Granular Build Profiles

We have expanded the build modes into granular, logically isolated package profiles:

| Profile Mode | Base List | Recovery List | KDE Standard | Desktop Core | Intended Use Case |
|---|---|---|---|---|---|
| **`dev-minimal`** | ✅ | ❌ | ❌ | ✅ (`plasma-desktop`) | Hyper-fast dev boot/UI testing |
| **`desktop`** | ✅ | ❌ | ✅ | ✅ (`kde-standard`) | Full desktop framework testing |
| **`recovery`** | ✅ | ✅ | ✅ | ✅ (`kde-standard`) | Complete cyber-recovery toolset |
| **`release`** | ✅ | ✅ | ✅ | ✅ (`kde-standard`) | Full amd64 production release |

---

## 💾 3. Prebuilt Package Staging Injection

Custom utilities developed within the workspace (like the **Phoenix Control Center** Tauri bundle or custom agents) can now be injected into the live image without being pulled from public network mirrors.

* **Target Directory:** [os/phoenix-os/build/packages/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/build/packages/)
* **Automated Injection:** The script [package-cache.sh](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/scripts/package-cache.sh) automatically scans this directory for any `.deb` packages and stages them under `/config/packages.chroot/` in the chroot building workspace. They are natively installed during the chroot assembly stage.

---

## 🔄 4. Deep Incremental Stages & Clean Modes

Instead of rebuilding the target chroot completely from scratch (which wipes out bootstrap stages), we now support **granular Clean Modes**:

```bash
# 1. Hyper-Fast Recompilation (Skips clean entirely, compiles overlays in under 30 seconds!)
bash os/phoenix-os/container/build-container.sh --mode dev-minimal --clean=none

# 2. Binary-Stage Clean (Preserves chroot and bootstrap, rebuilds binary squashfs/ISO payload)
bash os/phoenix-os/container/build-container.sh --mode dev-minimal --clean=stage

# 3. Full Purge Clean (Wipes chroot, caches, and rebuilds everything from ground zero)
bash os/phoenix-os/container/build-container.sh --mode dev-minimal --clean=all
```

### **Safety Guide for Clean Modes:**

* **`--clean=none`:** Safe when only modifying files in `config/includes.chroot/` (e.g. `colors.css`, `metadata.json`, scripts, static configuration files) or editing branding overlays. Do NOT use if adding/removing packages.
* **`--clean=stage`:** Safe when updating package list profiles or config headers. Re-generates the squashfs filesystem dynamically while preserving cached debootstrap stages.
* **`--clean=all`:** Mandatory when editing core hooks, changing base architecture targets, or preparing a production release artifact.

---

## 🩺 5. Safe Overlay Auditing & Planner

The utility [refresh-overlays.sh](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/scripts/refresh-overlays.sh) now acts as a comprehensive, safe, read-only pre-flight overlay validator. It parses staged JSON assets, confirms CSS layout tokens, checks executable script parameters, and charts the squashfs-bypass repack strategy.
