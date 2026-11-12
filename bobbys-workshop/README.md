# BobFWTools Studio — Bobby's Workshop (Phoenix Forge v5.0.0)

BobFWTools Studio is a local-first, cross-platform mobile hardware diagnostics, USB descriptor telemetry, and firmware servicing workbench for **macOS (12.0 Monterey+)**, **Windows (10/11)**, and **Linux**.

---

## 🏛️ Architecture & Editions

1. **Native macOS Studio (`Sources/*.swift` + `build_app.sh`)**:
   - Compiled as a **Universal 2 (`arm64` + `x86_64`)** native AppKit/SwiftUI application supporting **macOS 12.0 Monterey and newer**.
   - **Owner Standalone Edition**: Full hardware servicing, direct serial/modem/USB/Fastboot/Heimdall/libimobiledevice execution, installed to `/Applications/BobFWTools.app`.
   - **Public Store Submission Edition (`-DSTORE_EDITION`)**: Strict Mac App Store sandbox (`entitlements.store.plist`), bundled helper tools (`entitlements.helper.plist`), `PrivacyInfo.xcprivacy`, and Store-compliant UI strings.
2. **Native Rust `bootforgeusb` USB Engine (`libs/bootforgeusb`)**:
   - Inspects USB device descriptors AND active USB configuration interface descriptors (`ff/42/01` ADB, `ff/42/03` Fastboot, `06/01/01` MTP/PTP, `02/02` CDC ACM) via `rusb`/`libusb`.
   - Distinguishes internal Mac host USB controllers (`apple-host-internal`) from external Apple iOS/iPadOS devices (`Normal`, `Recovery 05ac:1281`, `DFU 05ac:1227`, `WTF 05ac:1222`).
3. **Cross-Platform Tauri v2 + Rust + React Workbench (`src-tauri/` + `src/`)**:
   - Targets **Windows 10/11 (`msi`, `nsis`, Microsoft Store `MSIX`)**, **Linux (`deb`, `rpm`, `appimage`, `Snap`, `Flatpak`)**, and **macOS (`app`, `dmg`)**.

---

## 🔒 Strict Zero-Simulation Truth Boundary

1. **No synthetic or fallback devices**: Never fabricates device models, serial numbers, battery percentages, or firmware URLs.
2. **Live hardware verification**: Every command (`irecovery`, `idevicediagnostics`, `cfgutil`, `adb`, `fastboot`, `heimdall`) verifies process exit status and real USB bus presence before reporting success.
3. **Cross-platform IPSW safety guard**: Refuses to flash an `iPhone*` IPSW onto an `iPad*` target (or vice-versa).

---

## 📱 Supported Hardware Matrix

- **Apple (`05ac`)**: 150+ models mapped by `ProductType` and `CPID`+`BDID` — iPhone 2G through iPhone 16 Pro Max & iPhone 16e, iPad (1st Gen through iPad Pro M4 11"/13", iPad Air M3, iPad A16, iPad mini A17 Pro), and iPod touch (5th–7th Gen).
- **Android OEMs & Silicon Boot Modes**:
  - Samsung (`04e8`), Google Pixel (`18d1`), Motorola (`22b8`), Xiaomi/Redmi/POCO (`2717`), OnePlus/OPPO/Realme (`22d9`/`2a70`), Nothing (`2b4c`), Sony (`0fce`), ASUS (`0b05`), LG (`1004`), HTC (`0bb4`), Huawei/Honor (`12d1`), ZTE/Nubia/RedMagic (`19d2`), Lenovo (`17ef`), TCL / Alcatel / T-Mobile REVVL (`1bbb`), Fairphone (`2ae5`).
  - Silicon Recovery/BootROM: Qualcomm EDL 9008 (`05c6`), MediaTek BROM/Preloader (`0e8d`), Unisoc/Spreadtrum FDL (`1782`).

---

## 🛠️ Build & Verification Commands

### macOS Native Universal 2 Studio (macOS 12.0+)
```bash
rm -rf /tmp/swift-module-cache && ./build_app.sh
```
Produces:
- `/Applications/BobFWTools.app`
- `dist/Owner-Private-Only/BobFWTools-Owner-Private-macOS.zip`
- `dist/Store-Submission/BobFWTools-Store-Submission-macOS.zip`

### Rust `bootforgeusb` Engine
```bash
cd libs/bootforgeusb
cargo test
cargo build --release --bin bootforgeusb
```

### Cross-Platform Tauri / Node Qualification
```bash
npm install
npm run verify:reality
npm run bobfw:check
npm run bobfw:test
npm run tauri:build:macos
npm run tauri:build:windows
```

### Store Packaging Assets (`store_packaging/`)
- `store_packaging/macos/AppIcon.icns` — Multi-resolution macOS icon (`16x16` to `512x512@2x`)
- `Resources/AppIcon_1024.png` & `Resources/SplashHero.png` — Studio launch splash & hero assets
- `store_packaging/windows/AppxManifest.xml` & `BobbyBlanco.BobFWToolsStudio.yaml` — Microsoft Store MSIX & WinGet manifests
- `store_packaging/linux/99-bobfwtools-devices.rules`, `snapcraft.yaml`, `com.bobbyblanco.bobfwtools.metainfo.xml`, `build_linux_package.sh` — Linux store & `udev` packaging
