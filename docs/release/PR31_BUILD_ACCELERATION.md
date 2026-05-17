# PR31 Phoenix OS Build Acceleration Framework

This document outlines the **PR31 Build Acceleration Framework** designed to optimize, customize, and significantly speed up the Phoenix OS ISO synthesis pipeline on developer environments (specifically Apple Silicon Macs) without weakening the hardened release path.

---

## 🚀 Build Mode Matrix

We now support three high-level build modes mapped against target architectures:

| Mode | Target Arch | Package Set | Intended Use | Expected Build Time (Native) |
|---|---|---|---|---|
| **`fast`** | `arm64` / `amd64` | Minimal Plasma Desktop + SDDM/Plymouth Themes | Quick dev boot checks, theme tweaks, UI layout testing | **~3-5 minutes** (with cache) |
| **`full`** | `arm64` / `amd64` | Standard KDE + Full Recovery Tools + Overlays | Complete features validation, full toolchain tests | **~8-12 minutes** (with cache) |
| **`release-hardened`** | `amd64` (default) | Standard KDE + Full Recovery Tools + Validation | Official production audits and physical deployments | **~15-20 minutes** |

---

## ⚡ Speed & Acceleration Impact

The core bottlenecks of the legacy build pipeline were:
1. **Emulated CPU Overhead:** Running an `amd64` live-build container under Apple Silicon translation was slow.
2. **Fresh Package Downloads:** Download and extraction of 1,000+ packages on every fresh docker container run.

### Acceleration Solutions:
* **Native ARM64 Compilation:** Using `linux/arm64` platform on M1/M2/M3 chips completely removes the CPU translation layer, delivering **5x speed improvements** on debootstrap, chroot operations, and squashfs packing.
* **Persistent Package Cache:** A bind-mounted host-to-container directory (`os/phoenix-os/cache/packages.chroot`) caches downloaded `.deb` packages. Subsequent builds skip network downloads entirely.
* **Lightweight Desktop Profile:** Selecting `fast` mode replaces the bulky `kde-standard` suite with a lean `plasma-desktop` core, reducing package install counts by **50%**.

---

## 🛠️ Persistent Cache Behavior

* **Default State:** The APT cache is **active by default**. It dynamically populates `os/phoenix-os/cache/packages.chroot` on the host side.
* **Non-Polluting:** The cached `.deb` files are staged purely inside the working cache area during bootstrap and are completely excluded from the final SquashFS/ISO payload. The target ISO remains strictly pristine.
* **Disabling Cache:** Run with `--no-cache` to force a completely fresh download from scratch (required for final pre-release validation).
* **Cleaning Cache:** Run with `--clean` to sweep both the temporary build workspace and host-side caches.

---

## 🍎 Apple Silicon Recommendations

For local development on an M1/M2/M3 Mac:
1. **Always default to `--mode fast --arch arm64`** during active iteration. The build will run natively at max CPU efficiency and compile under 5 minutes.
2. **Use `--mode full --arch arm64`** to verify recovery overlays.
3. **Use `--mode release-hardened --arch amd64`** strictly for the final release candidate build before production deployment.

---

## ⚠️ Known Limitations
* **iMac/Intel boot of ARM64 ISOs:** ARM64 builds are purely for hypervisor (UTM) or native ARM64 device testing. They will not boot on your Intel 2015 iMac.
* **Emulated amd64 builds on Apple Silicon:** Building `amd64` on Apple Silicon is fully supported but will naturally run slower due to Docker's internal QEMU translation. This is expected and is why cache preservation is vital!
