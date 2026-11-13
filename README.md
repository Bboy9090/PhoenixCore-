# Phoenix Core & BobFWTools Studio (Bobby's Workshop v5.0.0)

Phoenix Core is a cross-platform mobile hardware diagnostics, USB descriptor telemetry, OS deployment, and firmware servicing platform spanning **macOS (12.0 Monterey through Tahoe)**, **Windows (10/11)**, and **Linux**.

---

## 🚀 Primary Workbenches & Modules

- **[`bobbys-workshop/`](bobbys-workshop/)**: **BobFWTools Studio (Bobby's Workshop)** — Native macOS Universal 2 (`arm64` + `x86_64`) SwiftUI/AppKit Studio + cross-platform Tauri v2/Rust desktop suite powered by `bootforgeusb`.
- **[`store_packaging/`](store_packaging/)**: Official Store & Distribution manifests for **Mac App Store / Notarized DMG** (`macos/`), **Microsoft Store MSIX & WinGet** (`windows/`), and **Linux AppDir / Snap / Flatpak / udev** (`linux/`).
- **[`backend/`](backend/)**: Central FastAPI hardware discovery and imaging orchestration service.
- **[`src/`](src/)**: Python CLI & PyQt6 desktop recovery/imaging engine.
- **[`crates/`](crates/)**: Rust workspace crates (`phoenix-core`, `phoenix-safety`, `phoenix-fs-fat32`, `phoenix-host-linux`, `phoenix-host-macos`, `phoenix-bootloader-core`, `phoenix-wim`).

---

## 🛠️ Key Capabilities (v5.0.0)

- **Zero-Simulation Truth Boundary**: All device identities, serials, CPIDs/BDIDs, battery health telemetry, and firmware URLs come strictly from live USB hardware descriptors, `irecovery`/`libimobiledevice`, `adb`/`fastboot`, Samsung `AT+DEVCONINFO`, and live Apple IPSW.me APIs — never mocked or fabricated.
- **150+ Apple Devices Mapped**: Full `CPID` + `BDID` hardware matrix from iPhone 2G through iPhone 16 Pro Max / iPhone 16e, iPad (1st Gen through iPad Pro M4, iPad Air M3, iPad A16, iPad mini A17 Pro), and iPod touch (5th–7th Gen) across Normal, Recovery (`05ac:1281`), and DFU (`05ac:1227`) modes.
- **20+ Android OEMs & Bare-Metal Bootloaders**: Deep USB interface descriptor inspection (`ff/42/01` ADB, `ff/42/03` Fastboot, `06/01/01` MTP/PTP, `02/02` CDC ACM) supporting Samsung (`04e8`), Google Pixel (`18d1`), Motorola (`22b8`), Xiaomi/POCO (`2717`), OnePlus/OPPO/Realme (`22d9`/`2a70`), Nothing (`2b4c`), Sony (`0fce`), ASUS (`0b05`), LG (`1004`), HTC (`0bb4`), Huawei/Honor (`12d1`), ZTE/RedMagic (`19d2`), Lenovo (`17ef`), TCL / Alcatel / T-Mobile REVVL (`1bbb`), Fairphone (`2ae5`), Qualcomm EDL 9008 (`05c6`), MediaTek BROM/Preloader (`0e8d`), and Unisoc/Spreadtrum FDL (`1782`).
- **Broad OS Compatibility**:
  - **macOS**: Universal 2 (`arm64` + `x86_64`) native app supporting **macOS 12.0 Monterey and newer** (`LSMinimumSystemVersion = 12.0`).
  - **Windows**: Windows 10 (1809+) & Windows 11 (`x64`) via MSI, NSIS, WinGet, and Microsoft Store MSIX (`AppxManifest.xml` with `usb` and `serialcommunication` capabilities).
  - **Linux**: Universal `AppDir`/tarball, Debian `.deb`, RPM, Flatpak/AppStream (`com.bobbyblanco.bobfwtools.metainfo.xml`), Snap (`snapcraft.yaml`), and `99-bobfwtools-devices.rules` `udev` rules.

---

## ⚡ Quick Start & Build Commands

### 1. Native macOS Studio (`BobFWTools.app` — macOS 12.0+)
```bash
# Build Universal 2 (x86_64 + arm64) Owner & Store Submission bundles
rm -rf /tmp/swift-module-cache && cd bobbys-workshop && ./build_app.sh

# Launch installed app
open /Applications/BobFWTools.app
```
Outputs:
- Installed Runtime: `/Applications/BobFWTools.app`
- Owner Standalone Archive: `bobbys-workshop/dist/Owner-Private-Only/BobFWTools-Owner-Private-macOS.zip`
- Mac App Store Submission Archive (`-DSTORE_EDITION`): `bobbys-workshop/dist/Store-Submission/BobFWTools-Store-Submission-macOS.zip`

### 2. Native Rust `bootforgeusb` CLI Scanner
```bash
cd bobbys-workshop/libs/bootforgeusb
cargo build --release --bin bootforgeusb
./target/release/bootforgeusb scan
```

### 3. Cross-Platform Tauri Desktop Build (Windows / Linux / macOS)
```bash
cd bobbys-workshop
npm install
npm run bobfw:test
npm run tauri:build:windows   # Windows MSI + NSIS
npm run tauri:build:macos     # macOS Universal
```

### 4. Linux Package & `udev` Hardware Rules Installation
```bash
# Build Linux Universal AppDir bundle
./store_packaging/linux/build_linux_package.sh

# Install udev rules for non-root USB/Fastboot/EDL/BROM/Recovery access
sudo cp store_packaging/linux/99-bobfwtools-devices.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### 5. Python CLI / GUI & Rust Core Workspace
```bash
# Python CLI & Tests
python3 main.py --help
python3 -m pytest tests/

# Rust Phoenix Core Crates
cargo build -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim
cargo test -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim
```

---

## 📄 License

- **Phoenix Core & BobFWTools Studio** — Licensed under the MIT License (© 2026 Bobby Blanco — Bobby's Workshop).
- **OpenCore Legacy Patcher** — BSD 2-Clause.
