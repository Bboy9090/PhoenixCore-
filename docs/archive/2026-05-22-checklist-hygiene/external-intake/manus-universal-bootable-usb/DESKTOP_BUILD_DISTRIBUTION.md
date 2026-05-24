# Desktop App Build & Distribution Guide

**Status:** Production Ready  
**Last Updated:** May 5, 2026  
**Version:** 2.0.0

---

## Overview

This guide covers building Bobby's PhoenixDrive desktop application for Windows, macOS, and Linux, and distributing it via GitHub Releases.

**What We're Building:**
- Windows EXE + NSIS Installer
- macOS APP Bundle + DMG
- Linux AppImage + DEB Package
- Auto-update system
- GitHub Releases distribution

---

## Prerequisites

### All Platforms
- Python 3.11+
- PyInstaller 6.0+
- Git
- GitHub account

### Windows
- Windows 10/11
- Visual C++ Build Tools
- NSIS (Nullsoft Scriptable Install System)
- Code signing certificate (optional)

### macOS
- macOS 11+
- Xcode Command Line Tools
- Apple Developer Account ($99/year)
- Code signing certificate
- Notarization credentials

### Linux
- Ubuntu 20.04+ / Debian 11+
- AppImage tools
- DEB packaging tools
- dpkg-dev

---

## Step 1: Prepare Build Environment

### 1.1 Install PyInstaller

```bash
pip install pyinstaller==6.0.0
```

### 1.2 Install Platform-Specific Tools

**Windows:**
```bash
# Install NSIS
# Download from: https://nsis.sourceforge.io/

# Or via Chocolatey
choco install nsis
```

**macOS:**
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install create-dmg
brew install create-dmg
```

**Linux:**
```bash
# Install AppImage tools
sudo apt-get install appimage-builder

# Install DEB tools
sudo apt-get install dpkg-dev
```

### 1.3 Verify Installation

```bash
pyinstaller --version
```

---

## Step 2: Build Windows Executable

### 2.1 Create PyInstaller Spec

```bash
cd phoenix-drive-desktop
pyinstaller --name "PhoenixDrive" \
  --onefile \
  --windowed \
  --icon assets/images/icon.ico \
  --add-data "assets:assets" \
  --add-data "src:src" \
  main_enhanced.py
```

### 2.2 Build Executable

```bash
pyinstaller phoenix-drive.spec
```

Output: `dist/PhoenixDrive.exe`

### 2.3 Create NSIS Installer

Use `installer.nsi` to create installer:

```bash
makensis installer.nsi
```

Output: `dist/PhoenixDrive-Setup-2.0.0.exe`

### 2.4 Sign Executable (Optional)

```bash
signtool sign /f certificate.pfx /p password \
  /t http://timestamp.authority.com \
  dist/PhoenixDrive.exe
```

---

## Step 3: Build macOS App Bundle

### 3.1 Create PyInstaller Spec for macOS

```bash
pyinstaller --name "PhoenixDrive" \
  --onefile \
  --windowed \
  --icon assets/images/icon.icns \
  --add-data "assets:assets" \
  --add-data "src:src" \
  --osx-bundle-identifier "com.phoenixdrive.app" \
  main_enhanced.py
```

### 3.2 Build App Bundle

```bash
pyinstaller phoenix-drive-macos.spec
```

Output: `dist/PhoenixDrive.app`

### 3.3 Code Sign App Bundle

```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application" \
  dist/PhoenixDrive.app
```

### 3.4 Create DMG

```bash
create-dmg \
  --volname "PhoenixDrive" \
  --volicon "assets/images/icon.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "PhoenixDrive.app" 200 190 \
  --hide-extension "PhoenixDrive.app" \
  --app-drop-link 600 190 \
  dist/PhoenixDrive-2.0.0.dmg \
  dist/PhoenixDrive.app
```

### 3.5 Notarize DMG (Required for macOS 10.15+)

```bash
# Upload for notarization
xcrun altool --notarize-app \
  --file dist/PhoenixDrive-2.0.0.dmg \
  --primary-bundle-id com.phoenixdrive.app \
  -u your-apple-id@apple.com \
  -p your-app-password

# Check status
xcrun altool --notarization-info <REQUEST-ID> \
  -u your-apple-id@apple.com \
  -p your-app-password

# Staple notarization
xcrun stapler staple dist/PhoenixDrive-2.0.0.dmg
```

---

## Step 4: Build Linux Packages

### 4.1 Create PyInstaller Spec for Linux

```bash
pyinstaller --name "PhoenixDrive" \
  --onefile \
  --windowed \
  --icon assets/images/icon.png \
  --add-data "assets:assets" \
  --add-data "src:src" \
  main_enhanced.py
```

### 4.2 Build Executable

```bash
pyinstaller phoenix-drive-linux.spec
```

### 4.3 Create AppImage

Create `AppImageBuilder.yml`:

```yaml
version: 1
AppDir:
  path: dist/AppDir
  app_info:
    id: com.phoenixdrive.app
    name: PhoenixDrive
    icon: assets/images/icon.png
    version: 2.0.0
    exec: PhoenixDrive
  files:
    dist/PhoenixDrive: ./
    assets: ./assets
AppImage:
  file_name: PhoenixDrive-2.0.0.AppImage
  update-information: gh-releases-zsync|Bboy9090|PhoenixCore-|latest|PhoenixDrive-*.AppImage.zsync
```

Build:

```bash
appimage-builder --recipe AppImageBuilder.yml
```

### 4.4 Create DEB Package

Create `debian/control`:

```
Package: phoenixdrive
Version: 2.0.0
Architecture: amd64
Maintainer: Bobby <bobby@phoenixdrive.app>
Description: Universal OS Deployment Tool
Homepage: https://phoenixdrive.app
```

Build:

```bash
mkdir -p debian/phoenixdrive/usr/bin
mkdir -p debian/phoenixdrive/usr/share/applications
mkdir -p debian/phoenixdrive/usr/share/pixmaps

cp dist/PhoenixDrive debian/phoenixdrive/usr/bin/
cp assets/images/icon.png debian/phoenixdrive/usr/share/pixmaps/phoenixdrive.png
cp phoenixdrive.desktop debian/phoenixdrive/usr/share/applications/

dpkg-deb --build debian/phoenixdrive
mv debian/phoenixdrive.deb dist/phoenixdrive_2.0.0_amd64.deb
```

---

## Step 5: Generate Checksums

```bash
cd dist

# Windows
sha256sum PhoenixDrive-Setup-2.0.0.exe > PhoenixDrive-Setup-2.0.0.exe.sha256

# macOS
sha256sum PhoenixDrive-2.0.0.dmg > PhoenixDrive-2.0.0.dmg.sha256

# Linux
sha256sum PhoenixDrive-2.0.0.AppImage > PhoenixDrive-2.0.0.AppImage.sha256
sha256sum phoenixdrive_2.0.0_amd64.deb > phoenixdrive_2.0.0_amd64.deb.sha256
```

---

## Step 6: Create GitHub Release

### 6.1 Create Release

```bash
gh release create v2.0.0 \
  --title "PhoenixDrive 2.0.0" \
  --notes "Release notes here"
```

### 6.2 Upload Artifacts

```bash
# Windows
gh release upload v2.0.0 dist/PhoenixDrive-Setup-2.0.0.exe
gh release upload v2.0.0 dist/PhoenixDrive-Setup-2.0.0.exe.sha256

# macOS
gh release upload v2.0.0 dist/PhoenixDrive-2.0.0.dmg
gh release upload v2.0.0 dist/PhoenixDrive-2.0.0.dmg.sha256

# Linux
gh release upload v2.0.0 dist/PhoenixDrive-2.0.0.AppImage
gh release upload v2.0.0 dist/PhoenixDrive-2.0.0.AppImage.sha256
gh release upload v2.0.0 dist/phoenixdrive_2.0.0_amd64.deb
gh release upload v2.0.0 dist/phoenixdrive_2.0.0_amd64.deb.sha256
```

---

## Step 7: Set Up Auto-Update

### 7.1 Create Update Checker

```python
import requests
import json
from packaging import version

def check_for_updates(current_version):
    """Check for new version on GitHub."""
    try:
        response = requests.get(
            "https://api.github.com/repos/Bboy9090/PhoenixCore-/releases/latest"
        )
        latest = response.json()
        latest_version = latest['tag_name'].lstrip('v')
        
        if version.parse(latest_version) > version.parse(current_version):
            return {
                'available': True,
                'version': latest_version,
                'url': latest['html_url'],
                'notes': latest['body']
            }
        return {'available': False}
    except Exception as e:
        logger.error(f"Update check failed: {e}")
        return {'available': False}
```

### 7.2 Download and Install Update

```python
def download_and_install_update(url, current_exe):
    """Download and install update."""
    import tempfile
    import subprocess
    
    # Download
    response = requests.get(url, stream=True)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp_path = tmp.name
    
    # Verify checksum
    if not verify_checksum(tmp_path):
        raise Exception("Checksum verification failed")
    
    # Install
    if sys.platform == 'win32':
        subprocess.Popen([tmp_path, '/S'])  # NSIS silent install
    elif sys.platform == 'darwin':
        subprocess.run(['open', tmp_path])
    else:
        subprocess.run(['chmod', '+x', tmp_path])
        subprocess.Popen([tmp_path])
```

---

## Step 8: Testing

### 8.1 Test Windows Installer

1. Download `PhoenixDrive-Setup-2.0.0.exe`
2. Run installer
3. Verify installation in Program Files
4. Launch application
5. Test all features
6. Uninstall and verify cleanup

### 8.2 Test macOS DMG

1. Download `PhoenixDrive-2.0.0.dmg`
2. Mount DMG
3. Drag PhoenixDrive.app to Applications
4. Launch from Applications
5. Verify code signature: `codesign -v dist/PhoenixDrive.app`
6. Test all features

### 8.3 Test Linux Packages

**AppImage:**
```bash
chmod +x PhoenixDrive-2.0.0.AppImage
./PhoenixDrive-2.0.0.AppImage
```

**DEB:**
```bash
sudo dpkg -i phoenixdrive_2.0.0_amd64.deb
phoenixdrive
```

### 8.4 Verify Checksums

```bash
sha256sum -c PhoenixDrive-Setup-2.0.0.exe.sha256
sha256sum -c PhoenixDrive-2.0.0.dmg.sha256
sha256sum -c PhoenixDrive-2.0.0.AppImage.sha256
sha256sum -c phoenixdrive_2.0.0_amd64.deb.sha256
```

---

## Distribution Channels

### 1. GitHub Releases
- Primary distribution channel
- Automatic update checking
- All platforms in one place

### 2. Website Download
Add to phoenixdrive.app:
```html
<a href="https://github.com/Bboy9090/PhoenixCore-/releases/download/v2.0.0/PhoenixDrive-Setup-2.0.0.exe">
  Download for Windows
</a>
```

### 3. Package Managers

**Windows (Chocolatey):**
```bash
choco install phoenixdrive
```

**macOS (Homebrew):**
```bash
brew install phoenixdrive
```

**Linux (APT):**
```bash
sudo apt-add-repository ppa:phoenixdrive/stable
sudo apt-get install phoenixdrive
```

---

## Troubleshooting

### Issue: PyInstaller Build Fails

**Solution:**
```bash
# Clear cache
rm -rf build dist *.spec

# Rebuild with verbose output
pyinstaller --debug=all main_enhanced.py
```

### Issue: Code Signing Fails on macOS

**Solution:**
```bash
# Check available certificates
security find-identity -v -p codesigning

# Use correct certificate
codesign -s "Developer ID Application: Your Name (TEAM_ID)" app.app
```

### Issue: Notarization Fails

**Solution:**
```bash
# Check notarization status
xcrun altool --notarization-info <REQUEST_ID> \
  -u your-apple-id@apple.com \
  -p your-app-password

# View detailed logs
xcrun altool --notarization-info <REQUEST_ID> \
  -u your-apple-id@apple.com \
  -p your-app-password --verbose
```

### Issue: AppImage Won't Run

**Solution:**
```bash
# Check dependencies
ldd PhoenixDrive-2.0.0.AppImage

# Run with debug
./PhoenixDrive-2.0.0.AppImage --verbose
```

---

## Build Checklist

- [ ] All dependencies installed
- [ ] Code compiled without errors
- [ ] All tests passing
- [ ] Version number updated
- [ ] Changelog updated
- [ ] Windows EXE created and signed
- [ ] Windows installer created
- [ ] macOS app bundle created and signed
- [ ] macOS DMG created and notarized
- [ ] Linux AppImage created
- [ ] Linux DEB package created
- [ ] All checksums generated
- [ ] GitHub release created
- [ ] All artifacts uploaded
- [ ] Update checker tested
- [ ] Installation tested on each platform
- [ ] Uninstallation tested
- [ ] Auto-update tested

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Startup time | < 2 seconds |
| Memory usage | < 100 MB |
| Disk space | < 150 MB |
| Build time | < 5 minutes |
| Download size | < 50 MB |

---

## Next Steps

1. Build installers for all platforms
2. Test on multiple machines
3. Create GitHub releases
4. Set up auto-update system
5. Announce release
6. Monitor for issues
7. Plan next release

---

**Status:** ✅ Ready for Production

For questions or issues, contact: support@phoenixdrive.app
