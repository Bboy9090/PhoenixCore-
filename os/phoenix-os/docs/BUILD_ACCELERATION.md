# Phoenix OS Build Acceleration Guide

This guide details the advanced incremental build mechanisms, cache options, and local APT caching architectures.

---

## 🚀 Accelerating Your Iteration Cycle

To achieve ultra-fast compile times, configure the builder to skip debootstrap and caching cycles:

### **1. Hyper-Fast Overlay Tweaking (< 30 seconds)**
If you are only editing custom theme colors (`colors.css`), app settings (`metadata.json`), static shell scripts, or visual branding files, reuse the compiled chroot entirely without cleaning:
```bash
bash os/phoenix-os/container/build-container.sh --mode dev-minimal --clean=none
```

### **2. Re-generating Systems Safe & Fast (< 3 minutes)**
If you are changing packages but want to reuse cached chroot setups:
```bash
bash os/phoenix-os/container/build-container.sh --mode dev-minimal --clean=stage
```

---

## ⚡ Setup Local APT Proxy Cache

Running a local `apt-cacher-ng` proxy service will cut package download times on subsequent rebuilds to practically zero.

```bash
# 1. Start apt-cacher-ng on host (macOS Homebrew)
brew install apt-cacher-ng
brew services start apt-cacher-ng

# 2. Tell the builder to pipe apt through it
export PHOENIX_APT_PROXY="http://172.17.0.1:3142"
bash os/phoenix-os/container/build-container.sh --mode dev-minimal
```

---

## 💾 Staging Prebuilt Packages (.deb)

To stage custom Tauri apps, control centers, or binary services directly inside your chroot without setting up a private APT repo:

1. Place your compiled `.deb` files in:
   [os/phoenix-os/build/packages/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/build/packages/)
2. Run the caching manager to stage them:
   ```bash
   bash os/phoenix-os/scripts/package-cache.sh
   ```
3. Trigger the build wrapper:
   ```bash
   bash os/phoenix-os/container/build-container.sh --mode dev-minimal
   ```
   The `.deb` files will be automatically staged and installed in your live image natively!
