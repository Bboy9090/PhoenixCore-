# Arcwyre Product Definition

This document establishes the official product architecture and deployment boundaries for **Arcwyre** within the **PhoenixCore** platform. It consolidates the product definition to prevent architectural drift and defines how the lightweight "Arc Flex" profile maps directly into the core Arcwyre product mission.

---

## 1. The PhoenixCore Product Matrix

PhoenixCore is the platform architecture. It contains four targeted operating systems, each serving a distinct hardware tier and user profile:

```
PhoenixCore (Platform)
├── Blue Phoenix Native  →  Native OS / Kernel Track (from-scratch kernel)
├── Home Aurelia         →  Full Desktop Experience (modern hardware, rich visuals, KDE-based)
├── Thunder God          →  Power User & Creator Experience (heavy multitasking, workstation specs)
└── Arcwyre              →  Lightweight, Recovery & Everyday OS (low resource, XFCE-based)
    └── Deployment Profiles:
        ├── Flex         →  Lightweight desktop for old laptops/Chromebooks
        ├── Repair       →  Technician tool system and diagnostics
        ├── Live USB     →  File rescue and temporary systems
        ├── Kiosk        →  Locked-down appliance shell
        └── Power        →  Developer / system operator environment
```

---

## 2. Defining Arcwyre & Arc Flex

> **Architectural Law**: Arc Flex is **not** a separate operating system product. It is the lightweight deployment profile of Arcwyre.

Arcwyre exists to rescue weak, outdated, or constrained hardware and return it to functional everyday usage. 

### Target Hardware Environment
- **Minimum Specs**: 2 GB RAM (with Lite Mode), 16 GB storage (e.g., Chromebook eMMC), x86_64 or arm64 architecture.
- **Typical Hardware**: Legacy laptops, education Chromebooks, repair lab utility USBs, low-resource virtual machines.

### The Arcwyre Flex Profile Footprint
To satisfy the target environment, the **Flex** profile strips away resource-heavy graphics and services:
- **Desktop Environment**: XFCE (no compositor effects, flat layouts, single panel at the bottom).
- **Web Appliance Target**: Primary interface optimized for web apps and offline utilities (Firefox ESR).
- **Zero-Downloads Flagship App Suite**: All essential recovery and configuration tools must run offline from the local image.

---

## 3. Core Component Layout (Arcwyre Flex)

| Component | Profile Deployment Mapping |
| :--- | :--- |
| **Window Manager** | `xfwm4` (compositing, animations, and shadows disabled) |
| **Web Browser** | Firefox ESR (standardized, low memory profile) |
| **System Utilities** | Thunar (Files), Mousepad (Text), Ristretto (Images), GNOME Calculator |
| **Offline App Suite** | Recovery Center, Device Inspector, BootForge, Maintenance Tools, Web App Center |
| **Startpage** | Offline browser home page for web app launcher configuration |

---

## 4. Staging and Packaging Plan

All configuration files, service rules, and script packages corresponding to Arcwyre profiles are isolated from other editions and stored under:
[os/phoenix-os/profiles/arc-flex/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/profiles/arc-flex/)

### Profile Maps
- `profiles/arc-flex/package-lists/base-packages.txt` → Lightweight Debian base + XFCE core.
- `profiles/arc-flex/base/disabled-services.txt` → Boot daemon exclusions (Tracker, Preload, Evolution, Zeitgeist disabled).
- `profiles/arc-flex/includes.chroot/` → XFCE configurations, panel XMLs, and offline launcher configurations.
- `profiles/arc-flex/modes/` → Execution parameters (simple, repair, kiosk, power, live-usb).

---

## 5. Architectural Alignment Status

**Status**: `ARCWYRE_ARCH_LOCKED`

This definition officially halts the bifurcation of the lightweight product track, aligning the Arc Flex profile directly under the main Arcwyre product directory.
