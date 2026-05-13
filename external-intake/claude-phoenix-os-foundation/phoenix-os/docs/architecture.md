# Phoenix OS — System Architecture

## Overview

Phoenix OS is a live-build-based Linux distribution derived from Ubuntu 24.04 LTS (Noble Numbat). It targets x86_64 as its primary architecture with an ARM64-ready build structure. The distribution is packaged as a bootable ISO image suitable for USB deployment, live session use, and full disk installation via Calamares.

---

## Layer Model

```
┌─────────────────────────────────────────────────────┐
│                  Phoenix Applications                │
│  Control Center │ Recovery │ Welcome │ BootForge     │
├─────────────────────────────────────────────────────┤
│                   KDE Plasma 6                       │
│         (Shell, Dolphin, Konsole, KDE Apps)         │
├─────────────────────────────────────────────────────┤
│              Repair & Diagnostics Layer              │
│  GParted │ TestDisk │ Clonezilla │ smartmontools     │
│  fsck │ ddrescue │ photorec │ chntpw │ fwupd         │
├─────────────────────────────────────────────────────┤
│              Ubuntu 24.04 LTS Base                   │
│         (packages, apt, systemd, udev)               │
├─────────────────────────────────────────────────────┤
│         Linux Kernel (Ubuntu HWE series)             │
├─────────────────────────────────────────────────────┤
│           Hardware / Virtualization Layer            │
│       x86_64 (primary) │ ARM64 (planned)            │
└─────────────────────────────────────────────────────┘
```

---

## Base System

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Base distro | Ubuntu 24.04 LTS | Long-term support, wide hardware driver coverage, strong apt ecosystem |
| Init system | systemd | Standard, well-supported, required by Ubuntu base |
| Kernel | linux-image-generic-hwe-24.04 | HWE kernel for broadest new hardware support |
| Package manager | APT + dpkg | Native to Ubuntu base |
| Supplementary format | Flatpak + Flathub | Application sandboxing, creator tools availability |
| Build system | live-build (lb) | Debian's official live system creation tool, proven, scriptable |

---

## Desktop Environment

**KDE Plasma 6** is the primary and only officially supported desktop for Phoenix OS. The rationale:

- Best-in-class customizability — Phoenix theme integration is deep and maintainable
- Native disk and file management tools (Dolphin, KDE Partition Manager)
- Strong Wayland support with X11 fallback for legacy tool compatibility
- Professional-grade panel and widget system for repair technician workflows
- KDE Connect for mobile device integration in recovery scenarios

The live session auto-logs in as user `phoenix` with a pre-configured KDE profile.

---

## Boot Architecture

```
BIOS/UEFI firmware
       │
       ▼
GRUB 2 bootloader (EFI + BIOS compatible)
       │
       ├── Live session (default, RAM-based squashfs)
       ├── Install Phoenix OS (launches Calamares)
       ├── Memory test (memtest86+)
       └── Boot from first hard disk
       │
       ▼
Linux kernel + initrd
       │
       ▼
Plymouth boot splash (Phoenix flame)
       │
       ▼
systemd → SDDM login manager → KDE Plasma session
```

**Live session persistence:** Supported via `persistence` kernel parameter when a labeled USB partition is present. This enables repair technicians to carry a persistent tool configuration across sessions.

---

## Storage Layout (Installed System)

Default Calamares partition scheme (single-disk automatic):

```
/dev/sdX
├── /dev/sdX1   512 MB    EFI System Partition (FAT32)  [UEFI only]
├── /dev/sdX2   1 GB      /boot (ext4)
├── /dev/sdX3   [remainder] LVM Physical Volume
│   └── phoenix-vg
│       ├── root-lv    20 GB min    /        (ext4)
│       ├── home-lv    [remainder]  /home    (ext4)
│       └── swap-lv    [RAM size]   swap
```

LVM is used to enable future snapshot support for system recovery points.

---

## Application Architecture

### Phoenix Control Center

A unified dashboard for repair, diagnostics, and system configuration.

- **Framework:** Tauri 2 (Rust backend + React/TypeScript frontend)
- **Backend:** Rust process managing system calls, disk enumeration, S.M.A.R.T. queries
- **Frontend:** React + shadcn/ui, styled with Phoenix design system
- **IPC:** Tauri command API (typed, audited)
- **Privilege model:** Runs as user, invokes specific privileged helpers via polkit

### Phoenix Recovery

Guided workflow application for data rescue and system repair.

- **Framework:** Tauri 2
- **Integrations:** ddrescue, TestDisk/PhotoRec, fsck wrappers, ntfs-3g
- **Safety model:** All destructive operations gated by confirmation modal with device path display
- **Logging:** All operations logged to `/var/log/phoenix/recovery-<session>.log`

### Phoenix Welcome

First-boot onboarding and system overview.

- **Framework:** Qt6 / KDE Kirigami (native KDE integration)
- **Behavior:** Auto-launches on first KDE session, suppressed after first-run flag is set

### BootForge Launcher

Integration point for Phoenix Key hardware and BootForge session management.

- **Framework:** Tauri 2
- **Detection:** Monitors udev for Phoenix Key VID/PID insertion event
- **Functions:** Mount key, read/write session data, launch repair workflows

---

## Security Model

See [`security-model.md`](security-model.md) for full details. Key principles:

1. Live session user (`phoenix`) has no password; sudo requires explicit invocation
2. SSH daemon is disabled by default in live session
3. Internal disk partitions are not auto-mounted writable
4. All disk tool GUIs enforce confirmation before destructive actions
5. Flatpak apps run in sandboxed environment

---

## Build System

See [`build-system.md`](build-system.md) for full build instructions.

The build pipeline is:

```
scripts/verify-host.sh → scripts/build-iso.sh → output/phoenix-os-<ver>-amd64.iso
```

Under the hood, `build-iso.sh` orchestrates:
1. `lb config` — configures the live-build environment
2. `lb build` — bootstraps Ubuntu base, installs packages, runs hooks, assembles ISO
3. Post-build: checksum generation, optional GPG signing

---

## ARM64 Readiness

The repository structure is ARM64-ready:

- Package lists use architecture-agnostic package names where possible
- Build scripts accept an `ARCH` environment variable (`amd64` or `arm64`)
- ARM64-specific kernel and firmware packages are noted in package lists as `# ARM64:`
- Calamares configuration is architecture-agnostic

ARM64 target hardware (planned): Raspberry Pi 4/5, Ampere Altra workstations, Apple Silicon via Asahi.
