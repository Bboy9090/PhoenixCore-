# Bobby’s Worldwide OS (BWOS)

Bobby’s Worldwide OS is a sovereign, high-integrity operating-system platform designed for machine recovery, system repair, and creator-owned computing. It is the parent ecosystem for a family of specialized Editions.

## 🌟 The Edition Model
BWOS follows a "One Platform, Many Faces" strategy. All editions share the same hardened core, safety gates, and recovery spine, but provide tailored visual identities and package presets:

- **Home Edition**: Consumer-focused daily desktop.
- **Aurelia Edition (`blue-phoenix`)**: Premium creator profile.
- **ARCWYRE Edition**: Cyber-recovery professional profile.
- **Thunder God Edition**: High-power performance profile.
- **Native**: Research-only sovereign track, intentionally excluded from the live-build Linux ISO matrix.

Architecture-specific build targets such as `home-arm64`, `home-legacy-i386`, and `thunder-god-arm64` are compatibility variants, not separate editions.

Archived concept history lives under `docs/archive/retired-editions/` and must not be treated as active branches.

---

## 🏗️ Project Status

- **Phase 0: Documentation Pivot**: ✅ Locked
- **Phase 1: Visual Identity Foundation**: ✅ Locked
- **Phase 1A/B: Offline Build Stabilization**: ✅ Locked
- **Phase 2: Architecture Alignment**: ✅ Locked (BWOS Master Platform)
- **Phase 2B: Structural Consolidation**: 🏗️ In Progress

### Build Verification (Control Center)
The ARCWYRE Control Center frontend has been verified to build in an offline, air-gapped environment.
- **Last Verified**: 2026-05-14
- **Verification Command**: `cd apps/phoenix-control-center && ../../node_modules/.bin/vite build`
- **Result**: `dist/` successfully generated with zero external runtime dependencies.

---

## 🚀 Platform Architecture

The platform is organized into primary modules designed for machine resurrection:

- **[`backend/`](file:///Users/bj90-m1/Documents/GitHub/PhoenixCore-/backend)**: **Central FastAPI Service**. The primary API for hardware discovery and USB imaging.
- **[`mobile/`](file:///Users/bj90-m1/Documents/GitHub/PhoenixCore-/mobile)**: **React Native / Expo App**. Modern mobile client for managing Phoenix Core.
- **[`src/`](file:///Users/bj90-m1/Documents/GitHub/PhoenixCore-/src)**: **Refactored Core Engine**. The new "Wave 8" deployment logic, diagnostics, and recovery tools.
- **[`website/`](file:///Users/bj90-m1/Documents/GitHub/PhoenixCore-/website)**: **Flask Web Demo**. A web interface for downloads and cloud-based diagnostics.

---

## 🛠️ Features (Wave 8)

- **Universal USB creation**: Windows, Linux, macOS installers.
- **OCLP integration**: Boot unsupported Macs on newer macOS via embedded OpenCore Legacy Patcher.
- **Target & Kext config**: Select Mac model, kexts (Graphics, Audio, WiFi/Bluetooth, USB), and OpenCore settings.
- **Phoenix Core Engine**: Rust-based device graph, safety gates, and imaging primitives.
- **PyQt6 GUI**: Modern wizard workflow and one-click profiles.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run GUI
python main.py --gui

# Or CLI
python main.py --help
```

## 📄 Components

### 1. Modern API & Mobile
- **Backend (FastAPI)**: Real-time device orchestration.
- **Mobile (Expo)**: Remote management and status monitoring.

### 2. High-Performance Core (Rust)
- The low-level engine that powers all the above.
- **Rust Workspace**: `cargo build --workspace`

### 3. Recovery & Imaging
- Integrated disk probing, OS identification, and Cold Fuse imaging.

## 📁 Repository Map

```text
.
├── backend/          # Central FastAPI Backend
├── mobile/           # React Native Mobile App
├── src/              # Refactored Core Engine (Wave 8)
│   ├── gui/         # PyQt6 GUI & Wizards
│   ├── recovery/    # Disk probing & OS identification
│   └── imaging/     # Cold Fuse imaging pipeline
├── website/          # Flask Web Server / Vercel
├── crates/           # Rust Imaging & Safety Libraries
├── legacy/           # Original toolkits & scripts
└── third_party/      # OCLP Submodule
```

## 📄 License

- **Phoenix Core** – Licensed under the MIT License.
- **OpenCore Legacy Patcher** – BSD 2‑Clause.
