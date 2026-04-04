# Phoenix Core (Unified)

Phoenix Core is a professional, cross-platform OS deployment system. This repository contains both the **modern cloud-ready architecture** and the **original desktop tools** in a unified, modular structure.

---

## 🚀 Unified Architecture

The repository is organized into primary modules that coexist and interact:

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
