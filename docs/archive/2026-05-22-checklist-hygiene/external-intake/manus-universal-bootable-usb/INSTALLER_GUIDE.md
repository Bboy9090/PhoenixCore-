# Bobby's PhoenixDrive Desktop App - Installer Guide

Complete guide for building and distributing standalone installers for Windows, macOS, and Linux.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Building Executables](#building-executables)
3. [Creating Installers](#creating-installers)
4. [Distribution](#distribution)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Python 3.8+
- PyInstaller
- Platform-specific tools (see below)

### Install Dependencies

```bash
# Install PyInstaller
pip3 install PyInstaller

# Install other dependencies
pip3 install -r requirements.txt
```

### Build Executable

```bash
# Make build script executable (Linux/macOS)
chmod +x build.sh

# Run build script
./build.sh
```

The executable will be in the `dist/` directory.

---

## Building Executables

### Windows

#### Prerequisites

- Windows 10 or later
- Python 3.8+
- PyInstaller

#### Build Steps

```bash
# Install dependencies
pip install -r requirements.txt
pip install PyInstaller

# Build executable
pyinstaller --onefile --windowed --icon=src/ui/icons/app.ico phoenix-drive.spec

# Output: dist/PhoenixDrive.exe
```

#### Create Windows Installer

**Option 1: NSIS (Recommended)**

1. Install NSIS from [nsis.sourceforge.io](https://nsis.sourceforge.io/)
2. Run:

```bash
makensis installer.nsi
```

Output: `dist/PhoenixDrive-1.0.0-installer.exe`

**Option 2: WiX Toolset**

1. Install WiX from [wixtoolset.org](https://wixtoolset.org/)
2. Create `phoenix-drive.wxs` configuration
3. Build:

```bash
candle phoenix-drive.wxs
light -out PhoenixDrive-installer.msi phoenix-drive.wixobj
```

### macOS

#### Prerequisites

- macOS 10.13+
- Python 3.8+
- PyInstaller
- Xcode Command Line Tools

#### Build Steps

```bash
# Install dependencies
pip3 install -r requirements.txt
pip3 install PyInstaller

# Build app bundle
pyinstaller --onefile --windowed --icon=src/ui/icons/app.icns phoenix-drive.spec

# Output: dist/PhoenixDrive.app
```

#### Create macOS Installer

**Option 1: DMG (Recommended)**

```bash
# Create DMG
hdiutil create -volname "PhoenixDrive" \
    -srcfolder dist/PhoenixDrive.app \
    -ov -format UDZO dist/PhoenixDrive-1.0.0.dmg
```

**Option 2: PKG Installer**

```bash
# Create package
productbuild --component dist/PhoenixDrive.app /Applications \
    --sign "Developer ID Installer" \
    dist/PhoenixDrive-1.0.0.pkg
```

### Linux

#### Prerequisites

- Linux (Ubuntu 18.04+, Fedora 30+, etc.)
- Python 3.8+
- PyInstaller
- Build tools: `build-essential`, `python3-dev`

#### Build Steps

```bash
# Install dependencies
sudo apt-get install build-essential python3-dev  # Ubuntu/Debian
sudo dnf install gcc python3-devel                # Fedora

pip3 install -r requirements.txt
pip3 install PyInstaller

# Build executable
pyinstaller --onefile --windowed phoenix-drive.spec

# Output: dist/PhoenixDrive
```

#### Create Linux Installer

**Option 1: AppImage (Recommended)**

```bash
# Install appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Create AppImage
./appimagetool-x86_64.AppImage dist/PhoenixDrive PhoenixDrive-1.0.0-x86_64.AppImage
```

**Option 2: Snap Package**

```bash
# Install snapcraft
sudo snap install snapcraft --classic

# Create snapcraft.yaml
snapcraft

# Output: phoenix-drive_1.0.0_amd64.snap
```

**Option 3: DEB Package (Debian/Ubuntu)**

```bash
# Create package structure
mkdir -p debian/DEBIAN
mkdir -p debian/usr/bin
mkdir -p debian/usr/share/applications

# Copy executable
cp dist/PhoenixDrive debian/usr/bin/

# Create control file
cat > debian/DEBIAN/control << EOF
Package: phoenix-drive
Version: 1.0.0
Architecture: amd64
Maintainer: Bobby <bobby@phoenixdrive.com>
Description: Bobby's PhoenixDrive - Create bootable USB drives
EOF

# Build DEB
dpkg-deb --build debian phoenix-drive_1.0.0_amd64.deb
```

---

## Creating Installers

### Automated Build Script

The `build.sh` script automates the entire process:

```bash
./build.sh
```

This script:
1. Checks prerequisites
2. Detects platform
3. Cleans previous builds
4. Builds executable
5. Creates distribution package
6. Generates archive

### Manual Build Steps

#### Step 1: Build Executable

```bash
pyinstaller --onefile --windowed phoenix-drive.spec
```

#### Step 2: Create Installer

**Windows:**
```bash
makensis installer.nsi
```

**macOS:**
```bash
hdiutil create -volname "PhoenixDrive" -srcfolder dist/PhoenixDrive.app -ov -format UDZO dist/PhoenixDrive-1.0.0.dmg
```

**Linux:**
```bash
./appimagetool-x86_64.AppImage dist/PhoenixDrive PhoenixDrive-1.0.0-x86_64.AppImage
```

#### Step 3: Test Installer

- Install on clean system
- Verify all features work
- Check shortcuts and menus
- Test uninstall

---

## Distribution

### Release on GitHub

1. Create GitHub release
2. Upload installers:
   - `PhoenixDrive-1.0.0-installer.exe` (Windows)
   - `PhoenixDrive-1.0.0.dmg` (macOS)
   - `PhoenixDrive-1.0.0-x86_64.AppImage` (Linux)

### Create Download Page

```html
<h2>Download Bobby's PhoenixDrive</h2>

<h3>Windows</h3>
<a href="PhoenixDrive-1.0.0-installer.exe">
  Download Installer (50 MB)
</a>

<h3>macOS</h3>
<a href="PhoenixDrive-1.0.0.dmg">
  Download DMG (60 MB)
</a>

<h3>Linux</h3>
<a href="PhoenixDrive-1.0.0-x86_64.AppImage">
  Download AppImage (55 MB)
</a>
```

### Update Checker

Implement auto-update in app:

```python
def check_for_updates():
    """Check for new version"""
    response = requests.get(
        'https://api.github.com/repos/Bboy9090/PhoenixCore-/releases/latest'
    )
    latest = response.json()['tag_name']
    
    if latest > CURRENT_VERSION:
        show_update_dialog(latest)
```

---

## Troubleshooting

### PyInstaller Issues

**Missing modules:**
```bash
# Add hidden imports to spec file
hiddenimports = ['module_name']
```

**Large executable size:**
```bash
# Use UPX compression
pyinstaller --upx-dir=/path/to/upx phoenix-drive.spec
```

### Windows Installer Issues

**NSIS not found:**
```bash
# Add NSIS to PATH or specify full path
"C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
```

**Code signing errors:**
```bash
# Sign executable
signtool sign /f certificate.pfx /p password dist\PhoenixDrive.exe
```

### macOS Installer Issues

**Gatekeeper warning:**
```bash
# Sign app
codesign --deep --force --verify --verbose --sign "Developer ID Application" dist/PhoenixDrive.app
```

**Notarization required:**
```bash
# Submit for notarization
xcrun altool --notarize-app -f dist/PhoenixDrive-1.0.0.dmg \
    -t osx -u apple_id@example.com -p app_password
```

### Linux Installer Issues

**AppImage permissions:**
```bash
chmod +x PhoenixDrive-1.0.0-x86_64.AppImage
```

**Missing dependencies:**
```bash
# Check dependencies
ldd dist/PhoenixDrive
```

---

## Advanced Configuration

### Code Signing

**Windows:**
```bash
# Create certificate
makecert -sv MyKey.pvk -n "CN=PhoenixDrive" MyKey.cer

# Sign executable
signtool sign /f MyKey.pfx dist\PhoenixDrive.exe
```

**macOS:**
```bash
# Sign app
codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: Bobby" \
    dist/PhoenixDrive.app
```

### Auto-Update

Implement in-app update checking:

```python
class UpdateChecker:
    def __init__(self):
        self.current_version = "1.0.0"
        self.update_url = "https://api.github.com/repos/Bboy9090/PhoenixCore-/releases/latest"
    
    def check_for_updates(self):
        """Check for new version"""
        response = requests.get(self.update_url)
        latest = response.json()['tag_name'].lstrip('v')
        
        if self.compare_versions(latest, self.current_version) > 0:
            return True, latest
        return False, None
    
    def compare_versions(self, v1, v2):
        """Compare semantic versions"""
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        for a, b in zip(v1_parts, v2_parts):
            if a > b:
                return 1
            elif a < b:
                return -1
        return 0
```

---

## References

- **PyInstaller:** https://pyinstaller.readthedocs.io/
- **NSIS:** https://nsis.sourceforge.io/
- **WiX Toolset:** https://wixtoolset.org/
- **AppImage:** https://appimage.org/
- **Snapcraft:** https://snapcraft.io/

---

**Last Updated:** April 2, 2026
**Version:** 1.0.0
