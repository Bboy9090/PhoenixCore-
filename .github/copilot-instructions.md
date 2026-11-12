# Copilot Command Guide

## Bootstrap
- **Python:** `pip install -r requirements.txt`【F:README.md】
- **OCLP (optional):** `git submodule update --init third_party/OpenCore-Legacy-Patcher`【F:docs/oclp_integration.md】
- **Rust:** Install Rust (`>=1.94` via `rustup`).
- **Node (BobFWTools Tauri):** `cd bobbys-workshop && npm install`【F:bobbys-workshop/README.md】

## Build
- **macOS Native Studio (Universal 2, macOS 12.0+ Owner & Store Editions):** `rm -rf /tmp/swift-module-cache && cd bobbys-workshop && ./build_app.sh`【F:bobbys-workshop/build_app.sh】
- **Rust BootForge USB CLI:** `cd bobbys-workshop/libs/bootforgeusb && cargo build --release --bin bootforgeusb`【F:bobbys-workshop/libs/bootforgeusb/Cargo.toml】
- **Rust (Phoenix Core compilable crates):** `cargo build -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim`【F:AGENTS.md】
- **Python (recommended):** `python src/installers/build_installer.py`
- **Python (BootForge PyInstaller):** `python -m PyInstaller --onefile --windowed --name BootForge --add-data src:src --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.QtGui --hidden-import requests --hidden-import psutil --hidden-import cryptography --hidden-import yaml --hidden-import click --hidden-import colorama main.py`【F:build_system/simple_build.py†L19-L36】

## Test
- **Rust (Phoenix Core compilable crates):** `cargo test -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim`【F:AGENTS.md】
- **Rust (BootForge USB):** `cd bobbys-workshop/libs/bootforgeusb && cargo test`【F:bobbys-workshop/README.md】
- **BobFWTools Vitest Suite:** `cd bobbys-workshop && npm run bobfw:test`【F:bobbys-workshop/README.md】
- **Python:** `python3 -m pytest tests/`【F:AGENTS.md】

## Lint & Format
- **Rust clippy:** `cargo clippy -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim`【F:AGENTS.md】
- **Rust format check:** `cargo fmt --check`【F:AGENTS.md】
- **Swift typecheck (macOS 12.0+):** `cd bobbys-workshop && swiftc -typecheck -target x86_64-apple-macos12.0 -parse-as-library Sources/DeviceMasterRegistry.swift Sources/ServicingEngine.swift Sources/MainViews.swift Sources/AppMain.swift`【F:bobbys-workshop/build_app.sh】

## Package
- **macOS Owner & Store Bundles:** `rm -rf /tmp/swift-module-cache && cd bobbys-workshop && ./build_app.sh`【F:bobbys-workshop/build_app.sh】
- **Linux AppDir & udev Bundle:** `./store_packaging/linux/build_linux_package.sh`【F:store_packaging/linux/build_linux_package.sh】
- **Windows / macOS Tauri Bundles:** `cd bobbys-workshop && npm run tauri:build:windows` / `npm run tauri:build:macos`【F:bobbys-workshop/README.md】
- **Python USB Toolkit:** `python build_system/build_all.py`【F:build_system/build_all.py†L11-L47】
