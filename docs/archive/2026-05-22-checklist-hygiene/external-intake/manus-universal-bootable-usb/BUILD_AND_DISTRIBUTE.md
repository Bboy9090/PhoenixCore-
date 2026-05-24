# PhoenixDrive Desktop App — Build & Distribution Guide

## Overview

This guide explains how to build standalone executables for Windows, macOS, and Linux, and distribute them to users.

## Prerequisites

- **Python 3.9+** installed
- **PyInstaller** — `pip install pyinstaller`
- **Platform-specific tools**:
  - **Windows**: NSIS installer (optional)
  - **macOS**: Xcode Command Line Tools
  - **Linux**: dpkg, AppImage tools

## Building for Your Platform

### Windows Build

#### 1.1 Install Dependencies

```bash
cd /home/ubuntu/phoenix-drive-desktop
pip install -r requirements.txt
pip install pyinstaller nuitka
```

#### 1.2 Build Executable

```bash
# Using PyInstaller
pyinstaller phoenix-drive.spec

# Or using Nuitka (faster)
python -m nuitka --onefile --windows-icon=assets/icon.ico main.py
```

#### 1.3 Create Installer (Optional)

```bash
# Install NSIS
# Download from https://nsis.sourceforge.io/

# Create installer
makensis installer.nsi
```

#### 1.4 Output

- **Executable**: `dist/phoenix-drive.exe`
- **Installer**: `dist/PhoenixDrive-Setup.exe`

### macOS Build

#### 2.1 Install Dependencies

```bash
cd /home/ubuntu/phoenix-drive-desktop
pip install -r requirements.txt
pip install pyinstaller
```

#### 2.2 Build App Bundle

```bash
pyinstaller phoenix-drive.spec
```

#### 2.3 Create DMG (Disk Image)

```bash
# Create DMG
hdiutil create -volname "PhoenixDrive" \
  -srcfolder dist/phoenix-drive.app \
  -ov -format UDZO dist/PhoenixDrive.dmg

# Verify
hdiutil verify dist/PhoenixDrive.dmg
```

#### 2.4 Code Signing (Optional but Recommended)

```bash
# Sign app
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application" \
  dist/phoenix-drive.app

# Verify signature
codesign -v dist/phoenix-drive.app
```

#### 2.5 Notarization (Required for Distribution)

```bash
# Create notarization request
xcrun altool --notarize-app \
  --file dist/PhoenixDrive.dmg \
  --primary-bundle-id com.phoenixdrive.app \
  --username your-apple-id@icloud.com \
  --password your-app-specific-password

# Check status
xcrun altool --notarization-history 0 \
  --username your-apple-id@icloud.com \
  --password your-app-specific-password
```

#### 2.6 Output

- **App Bundle**: `dist/phoenix-drive.app`
- **DMG**: `dist/PhoenixDrive.dmg`

### Linux Build

#### 3.1 Install Dependencies

```bash
cd /home/ubuntu/phoenix-drive-desktop
pip install -r requirements.txt
pip install pyinstaller
```

#### 3.2 Build Executable

```bash
pyinstaller phoenix-drive.spec
```

#### 3.3 Create AppImage

```bash
# Install appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Create AppImage
./appimagetool-x86_64.AppImage dist/phoenix-drive PhoenixDrive.AppImage
```

#### 3.4 Create DEB Package (Optional)

```bash
# Create debian package structure
mkdir -p debian/DEBIAN
mkdir -p debian/usr/bin
mkdir -p debian/usr/share/applications
mkdir -p debian/usr/share/pixmaps

# Copy executable
cp dist/phoenix-drive debian/usr/bin/

# Create control file
cat > debian/DEBIAN/control << EOF
Package: phoenixdrive
Version: 1.0.0
Architecture: amd64
Maintainer: PhoenixDrive Team <team@phoenixdrive.com>
Description: Boot Camp driver installer and USB builder
 PhoenixDrive automatically detects your Mac model and provides
 the correct Windows drivers with automated installation.
EOF

# Build DEB
dpkg-deb --build debian phoenixdrive_1.0.0_amd64.deb
```

#### 3.5 Output

- **Executable**: `dist/phoenix-drive`
- **AppImage**: `PhoenixDrive.AppImage`
- **DEB Package**: `phoenixdrive_1.0.0_amd64.deb`

## Distribution

### GitHub Releases

#### 4.1 Create Release

```bash
# Create tag
git tag v1.0.0
git push origin v1.0.0

# Create release on GitHub
gh release create v1.0.0 \
  dist/phoenix-drive.exe \
  dist/PhoenixDrive.dmg \
  dist/PhoenixDrive.AppImage \
  --title "PhoenixDrive v1.0.0" \
  --notes "Initial release"
```

#### 4.2 Upload Artifacts

```bash
# Upload to release
gh release upload v1.0.0 dist/phoenix-drive.exe
gh release upload v1.0.0 dist/PhoenixDrive.dmg
gh release upload v1.0.0 dist/PhoenixDrive.AppImage
```

### Website Distribution

Create a download page with links to:
- Windows: `https://github.com/your-org/phoenixdrive/releases/download/v1.0.0/phoenix-drive.exe`
- macOS: `https://github.com/your-org/phoenixdrive/releases/download/v1.0.0/PhoenixDrive.dmg`
- Linux: `https://github.com/your-org/phoenixdrive/releases/download/v1.0.0/PhoenixDrive.AppImage`

### Auto-Update System

#### 5.1 Create Update Manifest

```json
{
  "version": "1.0.0",
  "windows": {
    "url": "https://github.com/your-org/phoenixdrive/releases/download/v1.0.0/phoenix-drive.exe",
    "sha256": "abc123..."
  },
  "macos": {
    "url": "https://github.com/your-org/phoenixdrive/releases/download/v1.0.0/PhoenixDrive.dmg",
    "sha256": "def456..."
  },
  "linux": {
    "url": "https://github.com/your-org/phoenixdrive/releases/download/v1.0.0/PhoenixDrive.AppImage",
    "sha256": "ghi789..."
  }
}
```

#### 5.2 Host Manifest

```bash
# Upload to S3 or GitHub Pages
aws s3 cp update-manifest.json s3://your-bucket/updates/manifest.json

# Or commit to GitHub
git add update-manifest.json
git commit -m "Update manifest for v1.0.0"
git push
```

## Signing & Verification

### Generate Checksums

```bash
# macOS
shasum -a 256 dist/PhoenixDrive.dmg > dist/PhoenixDrive.dmg.sha256

# Linux
sha256sum dist/PhoenixDrive.AppImage > dist/PhoenixDrive.AppImage.sha256

# Windows
certutil -hashfile dist/phoenix-drive.exe SHA256 > dist/phoenix-drive.exe.sha256
```

### Verify Downloads

Users can verify integrity:

```bash
# macOS
shasum -a 256 -c PhoenixDrive.dmg.sha256

# Linux
sha256sum -c PhoenixDrive.AppImage.sha256

# Windows
certutil -hashfile phoenix-drive.exe SHA256
```

## Troubleshooting

### Build Fails

```bash
# Clean build
rm -rf build dist

# Rebuild with verbose output
pyinstaller --debug=all phoenix-drive.spec
```

### Missing Dependencies

```bash
# Check dependencies
ldd dist/phoenix-drive  # Linux
otool -L dist/phoenix-drive.app/Contents/MacOS/phoenix-drive  # macOS
```

### Code Signing Issues (macOS)

```bash
# List available certificates
security find-identity -v -p codesigning

# Remove signature
codesign --remove-signature dist/phoenix-drive.app
```

## Checklist

- [ ] All dependencies installed
- [ ] Code tested locally
- [ ] Executable builds successfully
- [ ] Installer creates properly
- [ ] Code signed (macOS)
- [ ] Notarized (macOS)
- [ ] Checksums generated
- [ ] Release created on GitHub
- [ ] Artifacts uploaded
- [ ] Download page updated
- [ ] Update manifest deployed
- [ ] Tested on clean system

## Support

For issues:
- **PyInstaller Docs**: [pyinstaller.org](https://pyinstaller.org)
- **NSIS Docs**: [nsis.sourceforge.io](https://nsis.sourceforge.io)
- **AppImage Docs**: [appimage.org](https://appimage.org)

---

**Last Updated**: April 2026  
**Version**: 1.0  
**Author**: Manus AI
