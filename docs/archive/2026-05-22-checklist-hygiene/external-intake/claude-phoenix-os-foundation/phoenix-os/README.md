# Phoenix OS

**Repair-first. Creator-ready. Recovery-proven.**

Phoenix OS is a Linux-based operating system built for technicians, creators, and power users who need a reliable platform for system repair, disk recovery, hardware diagnostics, and professional creative work. Built on a Debian/Ubuntu LTS base with KDE Plasma and a curated toolkit of repair and recovery applications.

---

## Vision

Most operating systems are designed for the install-and-forget user. Phoenix OS is built for the person who shows up when things go wrong — the repair technician, the sysadmin, the creator who needs their machine back yesterday. It ships with the tools, the trust model, and the workflow integrations that professional users actually need.

Phoenix OS is also the native environment for **BootForge** tooling and the **Phoenix Key** hardware ecosystem — enabling one-boot repair sessions, client system imaging, and hardware diagnostics from a single trusted device.

---

## Status

**Phase:** MVP Foundation (pre-alpha)
**Base:** Ubuntu 24.04 LTS (Noble Numbat)
**Desktop:** KDE Plasma 6
**Installer:** Calamares

---

## Quick Start (Build the Live ISO)

### Prerequisites

Run on an Ubuntu 22.04 or 24.04 LTS host (bare metal or VM, not WSL):

```bash
sudo apt update
sudo apt install -y live-build calamares calamares-settings-ubuntu \
    debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin \
    mtools dosfstools isolinux syslinux-common git curl
```

### Clone and Build

```bash
git clone https://github.com/your-org/phoenix-os.git
cd phoenix-os

# Verify host environment
./scripts/verify-host.sh

# Build the ISO (takes 15–40 minutes depending on host speed)
sudo ./scripts/build-iso.sh
```

The resulting ISO will be written to `output/phoenix-os-<version>-amd64.iso`.

### Test the ISO

```bash
# Quick smoke test (requires KVM/QEMU)
./tests/smoke/test-boot.sh output/phoenix-os-*.iso
```

---

## Repository Layout

```
phoenix-os/
├── docs/               # Architecture, build system, branding, security docs
├── branding/           # Visual identity assets (wallpapers, splash, icons)
├── live-build/         # lb (live-build) configuration, hooks, package lists
├── installer/          # Calamares installer configuration
├── packages/           # Custom .deb package definitions
├── apps/               # Source code for custom Phoenix OS applications
├── scripts/            # Build, clean, verification, and packaging scripts
└── tests/              # Smoke tests and ISO validation
```

See [`docs/architecture.md`](docs/architecture.md) for full system design.

---

## Core Applications

| App | Purpose | Status |
|-----|---------|--------|
| Phoenix Welcome | First-boot onboarding and system overview | Placeholder |
| Phoenix Control Center | Unified repair, diagnostics, and settings hub | In development |
| Phoenix Recovery | Guided data rescue and disk repair workflows | In development |
| BootForge Launcher | BootForge session management and Phoenix Key integration | Placeholder |

---

## Safety Model

Phoenix OS ships with strong guardrails for disk operations:

- **No automatic disk targeting** — destructive operations never auto-select a disk
- **Confirmation gates** — all format/wipe/write operations require explicit user confirmation with device path verification
- **Read-only live default** — the live session does not automount internal disks as writable
- **Audit log** — disk tool actions are logged to `/var/log/phoenix/disk-ops.log`

See [`docs/security-model.md`](docs/security-model.md) for the full safety policy.

---

## Contributing

See `ROADMAP.md` for the current development plan. The project is in MVP foundation phase — contributions to build system stability, package curation, and application development are the highest priority.

---

## License

Phoenix OS configuration, scripts, and custom application code are released under the **MIT License** unless otherwise noted. Upstream components (Debian/Ubuntu packages, KDE Plasma, Calamares) retain their respective licenses.
