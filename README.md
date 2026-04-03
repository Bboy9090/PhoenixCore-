# Phoenix Core (Unified)

Phoenix Core is a professional, cross-platform OS deployment system. This repository contains both the **modern cloud-ready architecture** and the **original desktop tools** in a unified, modular structure.

## 🚀 Unified Architecture

The repository is organized into four primary modules that can coexist and interact:

- **[`backend/`](file:///Users/bj90-m1/Documents/GitHub/PhoenixCore-/backend)**: **Central FastAPI Service**. The primary API for hardware discovery and USB imaging.
- **[`mobile/`](file:///Users/bj90-m1/Documents/GitHub/PhoenixCore-/mobile)**: **React Native / Expo App**. Modern mobile client for managing Phoenix Core.
- **[`desktop/`](file:///Users/bj90-m1/Documents/GitHub/PhoenixCore-/desktop)**: **Original PyQt6 Desktop App**. The native Python application for local use.
- **[`website/`](file:///Users/bj90-m1/Documents/GitHub/PhoenixCore-/website)**: **Flask Web Demo**. A web interface for downloads and cloud-based diagnostics.

---

## 🛠️ Components

### 1. Modern API & Mobile
The future of Phoenix Core, built for mobility and cloud integration.
- **Backend**: `cd backend && pip install -r requirements.txt && python main.py`
- **Mobile**: `cd mobile && npm install && npm start`

### 2. Native Desktop Tools
The original heavy-duty Python tools for local system imaging.
- **GUI**: `cd desktop && python main.py --gui`
- **CLI**: `python desktop/main.py --help`

### 3. Web Service
The public-facing demo and download portal.
- **Server**: `cd website && python web_server.py`

### 4. High-Performance Core (Rust)
The low-level engine that powers all the above.
- **Rust Workspace**: `cargo build --workspace`

---

## 📁 Repository Map

```text
.
├── backend/          # NEW: FastAPI Backend
├── mobile/           # NEW: React Native Mobile App
├── desktop/          # ORIGINAL: PyQt6 Desktop GUI & Logic
├── website/          # ORIGINAL: Flask Web Server / Vercel
├── crates/           # CORE: Rust Imaging & Safety Libraries
├── apps/             # CORE: Rust CLI & Desktop entry points
├── legacy/           # ARCHIVE: Original toolkits, scripts, and build artifacts
├── docs/             # DOCUMENTATION: New & Legacy manuals
└── third_party/      # OCLP: OpenCore Legacy Patcher subtree
```

## 📄 License

- **Phoenix Core** – Licensed under the MIT License.
- **OpenCore Legacy Patcher** – BSD 2‑Clause.
