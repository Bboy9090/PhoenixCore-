# Bobby’s Worldwide OS (BWOS)

Bobby’s Worldwide OS is a sovereign, high-integrity operating-system platform designed for machine recovery, system repair, and creator-owned computing. It is the parent ecosystem for a family of specialized Editions.

## 🌟 The Edition Model
BWOS follows a "One Platform, Many Faces" strategy. All editions share the same hardened core, safety gates, and recovery spine, but provide tailored visual identities and package presets:

- **Thunder God Edition**: The heroic, electric desktop experience.
- **ARCWYRE Edition**: The sleek, modern cyber-recovery suite.
- **Forge Edition**: The industrial technician's toolset.
- **Blue Phoenix Edition**: The classic legacy UI and brand experience.
- **Native Preview**: The sovereign, from-scratch kernel development track.

*"Phoenix" and "ARCWYRE" remain as internal codenames and specialized public editions within the BWOS ecosystem.*

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

### Prerequisites

- **Python 3.10+** (for Python-based tools)
- **Rust 1.94+** (for core libraries)
- **Node.js 18+** with pnpm (for frontend apps)

### Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Rust workspace (optional, for development)
cargo build -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32

# Frontend dependencies (optional)
pnpm install
```

### Run the Application

```bash
# Python CLI
python main.py --help

# Python GUI
python main.py --gui

# Control Center (React)
cd apps/phoenix-control-center && pnpm run dev
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

## 🏗️ Build

### Rust Libraries

```bash
# Build compilable crates
cargo build -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 \
            -p phoenix-host-linux -p phoenix-host-macos \
            -p phoenix-bootloader-core -p phoenix-wim

# Release build
cargo build --release -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32
```

### Frontend Applications

```bash
# Control Center (Vite + React)
cd apps/phoenix-control-center
pnpm run build

# Output: dist/ directory with static assets
```

### Python Tools

```bash
# Build installer (recommended)
python src/installers/build_installer.py

# Or build with PyInstaller directly
pyinstaller --onefile --name=PhoenixKey main.py
```

## 🧪 Test

### Run Tests

```bash
# Python tests
python -m pytest tests/

# Python tests with coverage
python -m pytest tests/ --cov=src

# Rust tests (compilable crates only)
cargo test -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 \
           -p phoenix-bootloader-core -p phoenix-wim
```

### Lint & Format

```bash
# Rust lint
cargo clippy -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32

# Rust format check
cargo fmt --check
```

## 📦 Package

```bash
# Build all (ensures dependencies, builds executable, generates USB toolkit)
python build_system/build_all.py
```

For detailed packaging instructions, see [packaging/README.md](packaging/README.md).

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
├── apps/             # Application layer (Control Center, Welcome, etc.)
├── editions/         # Edition manifests (ARCWYRE, Thunder God, Forge, Blue Phoenix)
├── scripts/          # Build and validation scripts
└── third_party/      # OCLP Submodule
```

## 📄 License

- **Phoenix Core** – Licensed under the MIT License.
- **OpenCore Legacy Patcher** – BSD 2‑Clause.
