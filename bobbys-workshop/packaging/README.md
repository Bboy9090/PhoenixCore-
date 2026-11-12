# Packaging Guide

## BobFWTools Studio (Bobby's Workshop — Phoenix Forge v5.0.0)

**Purpose:** Guide for packaging BobFWTools Studio across **macOS (12.0 Monterey+ Universal 2)**, **Windows 10/11 (MSI/NSIS/MSIX/WinGet)**, **Linux (AppDir/DEB/RPM/Snap/Flatpak + udev)**, and **Blue Phoenix OS**.

**Last Updated:** 2026-11-12

---

## Table of Contents

1. [Overview](#overview)
2. [Windows Packaging (MSI/NSIS)](#windows-packaging-msinsis)
3. [MSIX Packaging](#msix-packaging)
4. [Blue Phoenix OS Integration](#blue-phoenix-os-integration)
5. [Troubleshooting](#troubleshooting)

---

## Overview

BobFWTools Studio supports multiple packaging formats for different distribution channels:

| Format | Platform | Use Case | Distribution |
|--------|----------|----------|--------------|
| **Native `.app` + `.zip`** | macOS 12.0+ (`arm64` + `x86_64`) | Owner Standalone & Mac App Store (`-DSTORE_EDITION`) | `./build_app.sh` (`/Applications/BobFWTools.app` & `dist/`) |
| **MSI** | Windows 10 (1809+) / 11 | Enterprise deployment | Direct download, SCCM, WinGet (`BobbyBlanco.BobFWToolsStudio.yaml`) |
| **NSIS** | Windows 10 / 11 | Standard user installation | Direct download (`npm run tauri:build:windows`) |
| **MSIX** | Windows 10 / 11 | Microsoft Store | `store_packaging/windows/AppxManifest.xml` (`usb` + `serialcommunication`) |
| **DMG / App** | macOS 12.0+ | Tauri cross-platform bundle | `npm run tauri:build:macos` |
| **AppDir / AppImage** | Linux (`x86_64` / `aarch64`) | Portable Linux bundle + `udev` rules | `store_packaging/linux/build_linux_package.sh` |
| **DEB / RPM / Snap / Flatpak** | Debian / Ubuntu / Fedora / Flathub | Linux software stores | `snapcraft.yaml` & `com.bobbyblanco.bobfwtools.metainfo.xml` |

This document covers **macOS**, **Windows (MSI/NSIS/MSIX)**, **Linux (`udev` + Store packages)**, and **Blue Phoenix OS** integration.

---

## Windows Packaging (MSI/NSIS)

### Prerequisites

- Node.js 20+
- Rust 1.75+ (for Tauri)
- Windows 10+ (for building Windows installers)
- Visual Studio Build Tools 2019+

### Build MSI Installer

MSI installers are ideal for enterprise deployment and support:
- Silent installation
- Centralized deployment via SCCM/Group Policy
- Custom installation paths
- Repair and uninstall via Windows Programs & Features

**Build Command:**
```bash
npm run tauri:build:windows
```

**Output:**
```
src-tauri/target/release/bundle/msi/Bobby's Workshop_5.0.0_x64_en-US.msi
```

**Configuration:**

MSI settings are in `src-tauri/tauri.conf.json`:

```json
{
  "bundle": {
    "targets": ["msi"],
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": ""
    }
  }
}
```

**MSI Features:**
- Default install path: `C:\Program Files\Bobby's Workshop`
- Start menu shortcut created automatically
- Desktop shortcut (optional, user choice)
- Add to PATH (optional)
- Embedded Node.js workshop API server
- Bundled Python runtime for FastAPI backend

### Build NSIS Installer

NSIS installers provide a user-friendly installation wizard:
- Custom install wizard UI
- User-selectable components
- Desktop and Start Menu shortcuts
- Uninstaller included

**Build Command:**
```bash
npm run tauri:build:windows
```

Tauri builds both MSI and NSIS by default when `targets: ["msi", "nsis"]` is configured.

**Output:**
```
src-tauri/target/release/bundle/nsis/Bobby's Workshop_5.0.0_x64-setup.exe
```

**NSIS Configuration:**

Advanced NSIS settings in `src-tauri/tauri.nsis.conf.json`:

```json
{
  "license": "LICENSE",
  "languages": ["English"],
  "installerIcon": "icons/icon.ico",
  "installMode": "perMachine"
}
```

**NSIS Features:**
- Custom installer icon
- License agreement display
- Component selection (core app, shortcuts, PATH)
- Modern UI with progress bar
- Silent install support: `/S` flag

### Code Signing (Optional)

For production releases, code signing is recommended:

**Certificate Setup:**
1. Obtain code signing certificate from trusted CA
2. Install certificate in Windows Certificate Store
3. Note certificate thumbprint

**Configure Tauri:**

In `src-tauri/tauri.conf.json`:

```json
{
  "bundle": {
    "windows": {
      "certificateThumbprint": "YOUR_CERT_THUMBPRINT",
      "digestAlgorithm": "sha256",
      "timestampUrl": "http://timestamp.digicert.com"
    }
  }
}
```

**Sign After Build:**

If not using Tauri's built-in signing:

```powershell
signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a "Bobby's Workshop_5.0.0_x64-setup.exe"
```

### Testing Windows Installers

**Test Checklist:**
- [ ] Clean Windows 10 VM installation succeeds
- [ ] Clean Windows 11 VM installation succeeds
- [ ] Application launches after install
- [ ] Start menu shortcut works
- [ ] Desktop shortcut works (if selected)
- [ ] Uninstaller removes all files
- [ ] Uninstaller removes registry keys
- [ ] Reinstall works after uninstall
- [ ] Silent install works: `setup.exe /S`
- [ ] Windows Defender does not flag installer

---

## MSIX Packaging

MSIX is the modern Windows app package format for Microsoft Store distribution.

### Prerequisites

- Windows 10 SDK (10.0.19041.0+)
- Windows App Certification Kit
- Developer account (for Store submission)

### Build MSIX Package

**Current Status:** Tauri's MSIX support is limited. Use manual packaging for now.

**Alternative: Manual MSIX Creation**

1. **Install MSIX Packaging Tool**
   ```powershell
   winget install Microsoft.MSIXPackagingTool
   ```

2. **Create MSIX from MSI**
   - Open MSIX Packaging Tool
   - Select "Application package"
   - Choose MSI installer as source
   - Follow wizard to generate MSIX

3. **Sign MSIX**
   ```powershell
   signtool sign /fd SHA256 /a /f MyCertificate.pfx "Bobby's Workshop_5.0.0.msix"
   ```

### MSIX Configuration

**Package Manifest (AppxManifest.xml):**

```xml
<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10">
  <Identity Name="com.bobbysworld.workshop"
            Publisher="CN=BobbyWorldPublisher"
            Version="5.0.0.0" />
  <Properties>
    <DisplayName>Bobby's Workshop</DisplayName>
    <PublisherDisplayName>Bobby's World</PublisherDisplayName>
    <Logo>Assets\StoreLogo.png</Logo>
    <Description>Professional device repair, diagnostics, and recovery dashboard</Description>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.19041.0" MaxVersionTested="10.0.22000.0" />
  </Dependencies>
  <Resources>
    <Resource Language="en-us" />
  </Resources>
  <Applications>
    <Application Id="Workshop" Executable="Bobby's Workshop.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="Bobby's Workshop"
                          Square150x150Logo="Assets\Square150x150Logo.png"
                          Square44x44Logo="Assets\Square44x44Logo.png"
                          Description="Rise from the Ashes. Every Device Reborn."
                          BackgroundColor="transparent">
        <uap:DefaultTile Wide310x150Logo="Assets\Wide310x150Logo.png" />
      </uap:VisualElements>
    </Application>
  </Applications>
  <Capabilities>
    <Capability Name="internetClient" />
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
</Package>
```

### MSIX Validation

**Windows App Certification Kit:**

```powershell
"C:\Program Files (x86)\Windows Kits\10\App Certification Kit\appcert.exe" test -appxpackagepath "Bobby's Workshop_5.0.0.msix" -reportoutputpath "certification_report.xml"
```

**Validation Checklist:**
- [ ] Package installs via App Installer
- [ ] Application launches from Start menu
- [ ] No certification failures
- [ ] Privacy policy URL set (required for Store)
- [ ] Age rating appropriate (ESRB E for Everyone)
- [ ] App capabilities justified
- [ ] No prohibited content

---

## Blue Phoenix OS Integration

**Blue Phoenix OS** is Bobby's custom Android-based operating system for repair shops.

### Package ID

Bobby's Workshop uses a consistent package ID across platforms:

```
com.bobbysworld.workshop
```

This ID is configured in:
- `app.metadata.json`: `"id": "com.bobbysworld.workshop"`
- `src-tauri/tauri.conf.json`: `"identifier": "com.phoenixforge.app"` (to be updated)
- `package.json`: `"name": "phoenix-forge"` (legacy name)

**Recommendation:** Update Tauri identifier to match:
```json
{
  "identifier": "com.bobbysworld.workshop"
}
```

### Blue Phoenix OS App Integration

Workshop can be bundled with Blue Phoenix OS as a system app.

**Integration Methods:**

1. **Pre-installed System App**
   - Workshop included in `/system/app/` or `/system/priv-app/`
   - Auto-installed on first boot
   - Cannot be uninstalled by user
   - Recommended for repair shop devices

2. **Bundled User App**
   - Workshop included in `/data/app/`
   - Installed via package manager
   - Can be updated independently
   - Recommended for general distribution

3. **OTA Update Bundle**
   - Workshop delivered via OTA update
   - Installed when Blue Phoenix OS updates
   - Version managed by OS update system

### Blue Phoenix OS Manifest

**AndroidManifest.xml (for Android packaging):**

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
          package="com.bobbysworld.workshop">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.USB_PERMISSION" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />

    <application
        android:name=".WorkshopApplication"
        android:label="Bobby's Workshop"
        android:icon="@mipmap/ic_launcher"
        android:theme="@style/AppTheme">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

### Blue Phoenix OS API Integration

Workshop can integrate with Blue Phoenix OS APIs:

**Device Detection:**
```javascript
// Use Blue Phoenix OS device manager
const devices = await BluePhoenixxOS.DeviceManager.getConnectedDevices();
```

**System Diagnostics:**
```javascript
// Run Blue Phoenix OS system diagnostics
const diagnostics = await BluePhoenixxOS.Diagnostics.runSystemCheck();
```

**Repair History:**
```javascript
// Access Blue Phoenix OS repair history
const history = await BluePhoenixxOS.RepairLog.getHistory();
```

### Distribution on Blue Phoenix OS

**APK Build (Future):**

Workshop is currently a desktop app (Tauri). For Blue Phoenix OS, consider:

1. **WebView Wrapper** - Wrap Workshop UI in Android WebView
2. **React Native Port** - Port Workshop to React Native
3. **Progressive Web App** - Run Workshop as PWA in browser

**Recommended:** WebView wrapper for quick Blue Phoenix OS integration.

---

## Installer Customization

### Custom Branding

**Icons:**
- Windows: `src-tauri/icons/icon.ico` (256x256)
- macOS: `src-tauri/icons/icon.icns` (1024x1024)
- Linux: `src-tauri/icons/icon.png` (512x512)

**Splash Screen:**

Add splash screen in Tauri config:

```json
{
  "app": {
    "withGlobalTauri": true,
    "windows": [{
      "title": "Bobby's Workshop",
      "splashScreen": {
        "imageUrl": "assets/splash.png",
        "backgroundColor": "#0A0A12"
      }
    }]
  }
}
```

### Install Location

**Default Paths:**
- Windows: `C:\Program Files\Bobby's Workshop`
- macOS: `/Applications/Bobby's Workshop.app`
- Linux: `/opt/bobbys-workshop` or `~/.local/share/bobbys-workshop`

**Custom Path (Windows MSI):**

Allow user to choose install directory via MSI UI.

### Bundled Dependencies

Workshop bundles:
- Node.js workshop API server (`src-tauri/resources/server`)
- Python FastAPI backend (`src-tauri/resources/python`)
- Core workflow definitions (`src-tauri/resources/runtime`)

**Bundle Size:**
- Windows: ~150 MB (with Node.js + Python)
- macOS: ~140 MB
- Linux: ~130 MB

---

## Troubleshooting

### Build Fails on Windows

**Error:** `npm run tauri:build` fails with Rust compilation errors

**Solution:**
1. Install Visual Studio Build Tools 2019+
2. Install Rust: `winget install Rustlang.Rust.MSVC`
3. Restart terminal
4. Run `cargo clean` in `src-tauri/`
5. Retry build

### MSI Install Fails

**Error:** "This installation package cannot be opened."

**Solution:**
- Ensure MSI is not corrupted (verify checksum)
- Run installer as Administrator
- Check Windows Installer service is running:
  ```powershell
  Get-Service msiserver
  ```

### MSIX Signature Invalid

**Error:** "App package signature is invalid"

**Solution:**
- Re-sign MSIX with valid certificate
- Ensure certificate is trusted on target machine
- For testing, enable Developer Mode in Windows Settings

### Blue Phoenix OS Integration Issues

**Error:** Workshop not detected as system app

**Solution:**
- Verify package ID matches: `com.bobbysworld.workshop`
- Check app is in correct directory: `/system/priv-app/Workshop/`
- Ensure permissions granted in AndroidManifest.xml
- Reboot Blue Phoenix OS after installation

---

## Next Steps

### Short Term (MVP)

- [x] MSI and NSIS installers working
- [x] Code signing setup documented
- [ ] MSIX packaging tested
- [ ] Blue Phoenix OS package ID aligned

### Long Term (Future)

- [ ] Microsoft Store submission (MSIX)
- [ ] Windows ARM build support
- [ ] Blue Phoenix OS native integration
- [ ] Android/APK build for mobile devices

---

## Appendix: Build Scripts

### Complete Windows Build

```bash
# Install dependencies
npm install

# Install workshop server dependencies
npm run workshop:server:install

# Build frontend
npm run build

# Prepare bundle (platform-specific resources)
npm run prepare:bundle

# Bundle FastAPI backend
npm run bundle:fastapi

# Build Tauri Windows installers (MSI + NSIS)
cargo tauri build --target x86_64-pc-windows-msvc
```

### Verify Build Artifacts

```powershell
# Check MSI exists
Test-Path "src-tauri/target/release/bundle/msi/Bobby's Workshop_5.0.0_x64_en-US.msi"

# Check NSIS exists
Test-Path "src-tauri/target/release/bundle/nsis/Bobby's Workshop_5.0.0_x64-setup.exe"

# Get file sizes
Get-ChildItem "src-tauri/target/release/bundle" -Recurse | Select-Object Name, Length
```

---

**Document Owner:** Bobby's Workshop Team
**Review Cycle:** Per release
**Next Review:** Before v5.0.0 release

> For packaging issues or questions, open an issue: https://github.com/Bboy9090/Bobbys-Workshop-/issues
