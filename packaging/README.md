# Command Control Center - Packaging Guide

This directory contains packaging configurations and instructions for distributing Command across different platforms.

## Overview

Command Control Center supports multiple packaging formats tailored to each platform:

- **Windows**: MSIX packages for Microsoft Store and enterprise deployment
- **macOS**: .app bundles with optional code signing and notarization
- **Linux**: .deb, .rpm, and AppImage formats
- **Blue Phoenix OS**: Native BWOS package format

## Windows Packaging (MSIX)

### Prerequisites

- Windows 10 SDK (version 1809 or later)
- Visual Studio 2019+ or MSBuild tools
- Code signing certificate (for production releases)
- Windows App Certification Kit (optional, for Store submission)

### Package Manifest

The MSIX package manifest is located at `packaging/windows/AppxManifest.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">

  <Identity
    Name="BobbysWorldwideOS.CommandControlCenter"
    Publisher="CN=Bobby's Worldwide OS"
    Version="1.0.0.0"
    ProcessorArchitecture="x64" />

  <Properties>
    <DisplayName>Command Control Center</DisplayName>
    <PublisherDisplayName>Bobby's Worldwide OS</PublisherDisplayName>
    <Logo>Assets\AppIcon.png</Logo>
    <Description>System monitoring and control center for Bobby's Worldwide OS</Description>
  </Properties>

  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.22621.0" />
  </Dependencies>

  <Resources>
    <Resource Language="en-us" />
  </Resources>

  <Applications>
    <Application Id="Command" Executable="Command.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements
        DisplayName="Command"
        Description="Command Control Center"
        BackgroundColor="transparent"
        Square150x150Logo="Assets\AppIcon.png"
        Square44x44Logo="Assets\AppIcon.png">
        <uap:DefaultTile Wide310x150Logo="Assets\WideTile.png" />
      </uap:VisualElements>
    </Application>
  </Applications>

  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
</Package>
```

### Building MSIX

```powershell
# 1. Build the application
cargo build --release -p phoenix-core
python -m PyInstaller --onefile --name=Command main.py

# 2. Prepare package layout
mkdir packaging\windows\build
copy dist\Command.exe packaging\windows\build\
copy -r assets packaging\windows\build\

# 3. Create MSIX package
makeappx pack /d packaging\windows\build /p Command_1.0.0_x64.msix

# 4. Sign package (production only)
signtool sign /fd SHA256 /f Certificate.pfx /p <password> Command_1.0.0_x64.msix
```

### Testing MSIX

```powershell
# Install locally for testing
Add-AppxPackage Command_1.0.0_x64.msix

# Validate package
Windows App Certification Kit
```

### Store Submission

1. Create app listing at [Microsoft Partner Center](https://partner.microsoft.com/dashboard)
2. Upload MSIX package
3. Configure pricing and availability
4. Submit for certification

### Enterprise Deployment

For enterprise deployments via Intune or SCCM:

```powershell
# Deploy via Intune
# 1. Upload .msix to Microsoft Endpoint Manager
# 2. Configure deployment settings
# 3. Assign to device groups

# Deploy via SCCM
# 1. Create application in SCCM
# 2. Add deployment type (MSIX)
# 3. Configure detection rules
# 4. Deploy to collections
```

## macOS Packaging (.app)

### Prerequisites

- Xcode Command Line Tools
- Apple Developer Account (for code signing)
- Developer ID certificate (for distribution outside Mac App Store)

### Building .app Bundle

```bash
# 1. Build Rust components
cargo build --release -p phoenix-core

# 2. Build Python executable
pyinstaller --windowed --name=Command main.py

# 3. Create .app structure
mkdir -p "Command.app/Contents/MacOS"
mkdir -p "Command.app/Contents/Resources"

# 4. Copy executable
cp dist/Command "Command.app/Contents/MacOS/"

# 5. Create Info.plist
cat > "Command.app/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Command</string>
    <key>CFBundleIdentifier</key>
    <string>com.bobbysworld.command</string>
    <key>CFBundleName</key>
    <string>Command</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2026 Bobby's Worldwide OS</string>
</dict>
</plist>
EOF

# 6. Code sign (production)
codesign --deep --force --verify --verbose --sign "Developer ID Application: Bobby's Worldwide OS" Command.app

# 7. Notarize (for macOS 10.15+)
xcrun notarytool submit Command.app --apple-id your@email.com --team-id TEAMID --password "app-password"
```

### Creating DMG Installer

```bash
# Create DMG with Applications symlink
hdiutil create -volname "Command Installer" -srcfolder Command.app -ov -format UDZO Command-1.0.0.dmg
```

## Linux Packaging

### Debian/Ubuntu (.deb)

```bash
# 1. Create package structure
mkdir -p packaging/linux/deb/command_1.0.0/DEBIAN
mkdir -p packaging/linux/deb/command_1.0.0/usr/bin
mkdir -p packaging/linux/deb/command_1.0.0/usr/share/applications
mkdir -p packaging/linux/deb/command_1.0.0/usr/share/icons

# 2. Create control file
cat > packaging/linux/deb/command_1.0.0/DEBIAN/control <<'EOF'
Package: command
Version: 1.0.0
Architecture: amd64
Maintainer: Bobby's Worldwide OS <contact@bobbysworld.com>
Depends: python3 (>= 3.10), python3-pyqt6
Description: Command Control Center
 System monitoring and control center for Bobby's Worldwide OS
EOF

# 3. Copy files
cp dist/Command packaging/linux/deb/command_1.0.0/usr/bin/command
chmod +x packaging/linux/deb/command_1.0.0/usr/bin/command

# 4. Create .desktop file
cat > packaging/linux/deb/command_1.0.0/usr/share/applications/command.desktop <<'EOF'
[Desktop Entry]
Name=Command
Exec=/usr/bin/command
Icon=command
Type=Application
Categories=System;Utility;
EOF

# 5. Build package
dpkg-deb --build packaging/linux/deb/command_1.0.0
```

### Fedora/RHEL (.rpm)

```bash
# 1. Create RPM spec file
cat > packaging/linux/rpm/command.spec <<'EOF'
Name:           command
Version:        1.0.0
Release:        1%{?dist}
Summary:        Command Control Center
License:        MIT
URL:            https://github.com/Bboy9090/PhoenixCore-
Requires:       python3 >= 3.10

%description
System monitoring and control center for Bobby's Worldwide OS

%install
mkdir -p %{buildroot}/usr/bin
cp dist/Command %{buildroot}/usr/bin/command

%files
/usr/bin/command

%changelog
* Fri May 23 2026 Bobby's Worldwide OS
- Initial release
EOF

# 2. Build RPM
rpmbuild -ba packaging/linux/rpm/command.spec
```

### AppImage

```bash
# 1. Download AppImage tools
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# 2. Create AppDir structure
mkdir -p Command.AppDir/usr/bin
mkdir -p Command.AppDir/usr/share/applications
mkdir -p Command.AppDir/usr/share/icons

# 3. Copy files
cp dist/Command Command.AppDir/usr/bin/
cp assets/command-icon.png Command.AppDir/command.png
cp packaging/linux/command.desktop Command.AppDir/

# 4. Create AppRun script
cat > Command.AppDir/AppRun <<'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/Command" "$@"
EOF
chmod +x Command.AppDir/AppRun

# 5. Build AppImage
./appimagetool-x86_64.AppImage Command.AppDir Command-1.0.0-x86_64.AppImage
```

## Blue Phoenix OS Native Package

### Package Format

Blue Phoenix OS uses edition manifests and app metadata:

```bash
# 1. Ensure app.metadata.json is present
cp app.metadata.json packaging/bwos/

# 2. Create BWOS package descriptor
cat > packaging/bwos/package.yaml <<'EOF'
package_id: com.bobbysworld.command
name: Command
version: 1.0.0
edition_compatibility:
  - arcwyre
  - thunder-god
  - forge
  - blue-phoenix
install_location: /opt/bwos/apps/command
binaries:
  - src: dist/Command
    dest: bin/command
resources:
  - src: assets/
    dest: share/
metadata:
  - src: app.metadata.json
    dest: metadata/
EOF

# 3. Build BWOS package
bwos-package build packaging/bwos/package.yaml
```

## Continuous Integration

### GitHub Actions Workflow

Example workflow for automated packaging:

```yaml
name: Package

on:
  release:
    types: [created]

jobs:
  windows-msix:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build MSIX
        run: |
          cargo build --release
          python -m PyInstaller --onefile --name=Command main.py
          makeappx pack /d packaging/windows/build /p Command.msix
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: command-windows-msix
          path: Command.msix

  macos-dmg:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build DMG
        run: |
          cargo build --release
          pyinstaller --windowed --name=Command main.py
          # Create .app and DMG (steps above)
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: command-macos-dmg
          path: Command.dmg

  linux-packages:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build .deb and AppImage
        run: |
          cargo build --release
          pyinstaller --onefile --name=Command main.py
          # Create packages (steps above)
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: command-linux-packages
          path: |
            command_1.0.0_amd64.deb
            Command-1.0.0-x86_64.AppImage
```

## Distribution Channels

### Official Channels

- **Microsoft Store**: For Windows users
- **Mac App Store**: For macOS users (requires additional review)
- **GitHub Releases**: Cross-platform releases
- **BWOS Package Repository**: Native Blue Phoenix OS packages

### Third-Party Channels

- **Homebrew** (macOS/Linux): `brew install command`
- **Chocolatey** (Windows): `choco install command`
- **Snap** (Linux): `snap install command`
- **Flatpak** (Linux): `flatpak install command`

## Version Management

### Version Numbering

Follow SemVer: `MAJOR.MINOR.PATCH`

- Update version in:
  - `app.metadata.json`
  - `Cargo.toml`
  - `package.json`
  - Platform manifests (AppxManifest.xml, Info.plist, etc.)

### Release Process

1. Update version numbers across all files
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.0.0`
4. Build packages for all platforms
5. Sign packages (production)
6. Test installations on clean systems
7. Upload to distribution channels
8. Publish release notes

## Troubleshooting

### Windows MSIX Issues

- **Error: Package validation failed**: Check AppxManifest.xml syntax
- **Error: App won't install**: Verify certificate trust chain
- **Error: App crashes on launch**: Check dependencies are included

### macOS Notarization Issues

- **Error: Notarization failed**: Ensure hardened runtime is enabled
- **Error: App won't open**: Check Gatekeeper settings
- **Error: Entitlements invalid**: Verify entitlements.plist

### Linux Package Issues

- **Error: Dependencies not found**: Check control file/spec file deps
- **Error: Permission denied**: Verify executable permissions
- **Error: Icon not showing**: Check .desktop file and icon paths

## Support

For packaging questions or issues:
- GitHub Issues: https://github.com/Bboy9090/PhoenixCore-/issues
- Documentation: https://github.com/Bboy9090/PhoenixCore-/tree/main/docs
