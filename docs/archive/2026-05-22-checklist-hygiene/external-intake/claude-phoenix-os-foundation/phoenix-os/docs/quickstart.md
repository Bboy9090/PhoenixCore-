# Phoenix OS — Quick Start

Get from a fresh Ubuntu 24.04 LTS machine to a built ISO in the shortest path possible.

---

## Prerequisites: 5 minutes

```bash
sudo apt update && sudo apt install -y \
  live-build debootstrap squashfs-tools xorriso \
  grub-pc-bin grub-efi-amd64-bin mtools dosfstools \
  isolinux git curl dpkg-dev fakeroot imagemagick
```

You need:
- Ubuntu 22.04 or 24.04 LTS (not WSL)
- 35 GB free disk space
- 8 GB RAM
- Internet connection

---

## Option A — Full developer setup (first-time)

```bash
git clone https://github.com/your-org/phoenix-os.git
cd phoenix-os
./scripts/setup-dev.sh     # Installs Rust, Node, Tauri CLI, all deps (~10 min)
```

---

## Option B — ISO build only (no app development)

```bash
git clone https://github.com/your-org/phoenix-os.git
cd phoenix-os

# Comment out the custom apps package list (not compiled yet)
sed -i 's/^phoenix-/# phoenix-/' live-build/package-lists/080-phoenix-apps.list.chroot

# Build
sudo ./scripts/build-iso.sh
```

---

## Build times

| Machine | Cold build | Warm build |
|---------|-----------|------------|
| 8-core, 32GB RAM, SSD | ~18 min | ~9 min |
| 4-core, 16GB RAM, SSD | ~35 min | ~18 min |
| 4-core, 8GB RAM, HDD  | ~55 min | ~28 min |

---

## Test the ISO

```bash
# QEMU smoke test (requires kvm)
./tests/smoke/test-boot.sh output/phoenix-os-*.iso

# Full ISO structure validation
./tests/iso-validation/validate-iso.sh output/phoenix-os-*.iso
```

---

## Work on an app (no ISO build needed)

### Phoenix Control Center frontend only
```bash
cd apps/phoenix-control-center
npm install
npm run dev          # http://localhost:5173 — hot reload
```

### Phoenix Control Center with Rust backend
```bash
cd apps/phoenix-control-center
cargo tauri dev      # Launches desktop app with hot reload
```

### Phoenix Recovery
```bash
cd apps/phoenix-recovery
npm install
npm run dev          # http://localhost:5174
```

---

## Add a package to the ISO

1. Find the package name: `apt-cache search <keyword>` on Ubuntu 24.04
2. Add it to the appropriate list in `live-build/package-lists/`
3. Rebuild: `sudo ./scripts/build-iso.sh`

One package per line. Use section comments. See existing lists for style.

---

## Common build failures

| Error | Fix |
|-------|-----|
| `lb: command not found` | `sudo apt install live-build` |
| `debootstrap: not found` | `sudo apt install debootstrap` |
| `No space left on device` | Need 35 GB free; run `sudo ./scripts/clean.sh --all` first |
| Package not found in noble | Wrong package name; check with `apt-cache search` on Ubuntu 24.04 |
| ISO smaller than 800 MB | Build failed early; check `output/lb-build-*.log` |
| QEMU test times out | KVM may be unavailable; add `QEMU_KVM=""` override or test on bare metal |

---

## Where things live

```
scripts/build-iso.sh          ← Start here for ISO builds
live-build/package-lists/     ← Add/remove packages
live-build/hooks/live/        ← Scripts run inside the chroot
installer/calamares-config/   ← Installer settings
apps/phoenix-control-center/  ← Main desktop app (Tauri + React)
apps/phoenix-recovery/        ← Recovery app (Tauri + React)
docs/                         ← Architecture, security, branding
```

---

## Getting help

- Read the error output in `output/lb-build-<timestamp>.log`
- Check `docs/build-system.md` for detailed build instructions
- File an issue with the log attached
