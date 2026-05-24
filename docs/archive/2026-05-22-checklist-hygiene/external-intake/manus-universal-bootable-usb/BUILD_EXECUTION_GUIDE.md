# PhoenixDrive Desktop App — Build Execution Guide

Complete step-by-step guide to build and package the desktop application for all platforms.

## Overview

This guide covers building PhoenixDrive desktop app for Windows, macOS, and Linux with proper code signing, installers, and distribution packages.

## Prerequisites

### All Platforms
- Python 3.8 or higher
- pip (Python package manager)
- Git
- 2GB free disk space
- Internet connection

### Windows-Specific
- Visual C++ Build Tools (for PyInstaller)
- NSIS (Nullsoft Scriptable Install System) for installer
- Administrator privileges

### macOS-Specific
- Xcode Command Line Tools: `xcode-select --install`
- Apple Developer Account (for code signing)
- 5GB free disk space

### Linux-Specific
- Build essentials: `sudo apt-get install build-essential python3-dev`
- AppImage tools: `sudo apt-get install appimage-kit`
- DEB tools: `sudo apt-get install dpkg`

## Phase 1: Environment Setup

### Step 1.1: Clone Repository

```bash
cd /home/ubuntu
git clone https://github.com/Bboy9090/PhoenixCore-.git
cd phoenix-drive-desktop
```

### Step 1.2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 1.3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Verify installations:
```bash
pip list | grep -E "PyInstaller|PyQt6|opencv"
```

### Step 1.4: Install Platform-Specific Tools

**Windows:**
```bash
# Install NSIS
# Download from: https://nsis.sourceforge.io/Download
# Or use chocolatey:
choco install nsis
```

**macOS:**
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Optional: Install code signing certificate
# Visit: https://developer.apple.com/account/
```

**Linux:**
```bash
# Install AppImage and DEB tools
sudo apt-get update
sudo apt-get install -y appimage-kit dpkg

# For Ubuntu/Debian
sudo apt-get install -y python3-dev build-essential
```

## Phase 2: Build Preparation

### Step 2.1: Verify Project Structure

```bash
ls -la
```

Should show:
```
main.py
phoenix-drive.spec
build.sh
build-all-platforms.sh
requirements.txt
src/
assets/
installer.nsi
README.md
```

### Step 2.2: Check Assets

```bash
ls -la assets/
```

Should contain:
- `icon.png` (Linux/Windows)
- `icon.ico` (Windows)
- `icon.icns` (macOS)

### Step 2.3: Update Version Numbers

Edit `phoenix-drive.spec`:
```python
version = '1.0.0'  # Update to current version
```

Edit `installer.nsi`:
```nsis
!define VERSION "1.0.0"  # Update to current version
```

## Phase 3: Build for Current Platform

### Option A: Automated Build (Recommended)

```bash
chmod +x build-all-platforms.sh
./build-all-platforms.sh
```

This automatically:
1. Detects your platform
2. Installs dependencies
3. Builds the executable
4. Creates platform-specific installer
5. Generates checksums
6. Creates release package

### Option B: Manual Build

#### Windows Build

```bash
# Activate virtual environment
venv\Scripts\activate

# Run PyInstaller
pyinstaller --onefile ^
  --windowed ^
  --icon=assets/icon.ico ^
  --name=phoenix-drive ^
  --add-data "assets;assets" ^
  --add-data "src;src" ^
  main.py

# Create installer (requires NSIS)
makensis installer.nsi

# Generate checksum
certutil -hashfile dist\phoenix-drive.exe SHA256 > dist\phoenix-drive.exe.sha256
```

#### macOS Build

```bash
# Activate virtual environment
source venv/bin/activate

# Run PyInstaller
pyinstaller --onefile \
  --windowed \
  --icon=assets/icon.icns \
  --name=phoenix-drive \
  --add-data "assets:assets" \
  --add-data "src:src" \
  --osx-bundle-identifier=com.phoenixdrive.app \
  main.py

# Create DMG
hdiutil create -volname "PhoenixDrive" \
  -srcfolder dist/phoenix-drive.app \
  -ov -format UDZO dist/PhoenixDrive.dmg

# Optional: Code sign
codesign --deep --force --verify --verbose \
  --sign "-" dist/phoenix-drive.app

# Generate checksums
shasum -a 256 dist/PhoenixDrive.dmg > dist/PhoenixDrive.dmg.sha256
```

#### Linux Build

```bash
# Activate virtual environment
source venv/bin/activate

# Run PyInstaller
pyinstaller --onefile \
  --icon=assets/icon.png \
  --name=phoenix-drive \
  --add-data "assets:assets" \
  --add-data "src:src" \
  main.py

# Create AppImage
appimagetool dist/phoenix-drive dist/PhoenixDrive.AppImage

# Create DEB package
mkdir -p debian/DEBIAN debian/usr/bin debian/usr/share/applications
cp dist/phoenix-drive debian/usr/bin/

cat > debian/DEBIAN/control << EOF
Package: phoenixdrive
Version: 1.0.0
Architecture: amd64
Maintainer: PhoenixDrive Team <team@phoenixdrive.com>
Description: Boot Camp driver installer and USB builder
EOF

dpkg-deb --build debian dist/phoenixdrive_1.0.0_amd64.deb

# Generate checksums
sha256sum dist/phoenix-drive > dist/phoenix-drive.sha256
sha256sum dist/PhoenixDrive.AppImage > dist/PhoenixDrive.AppImage.sha256
```

## Phase 4: Verify Build Output

### Step 4.1: Check Build Directory

```bash
ls -lh dist/
```

Should show:
- Executable file (50-150 MB)
- Installer file (if applicable)
- Checksum files (.sha256)

### Step 4.2: Verify Checksums

```bash
cd dist/
sha256sum -c *.sha256
```

All should show "OK".

### Step 4.3: Test Executable

**Windows:**
```bash
dist\phoenix-drive.exe --version
```

**macOS:**
```bash
dist/phoenix-drive.app/Contents/MacOS/phoenix-drive --version
```

**Linux:**
```bash
dist/phoenix-drive --version
```

### Step 4.4: Test Installer

**Windows:**
```bash
# Run installer
dist\PhoenixDrive-Setup.exe
# Follow prompts
```

**macOS:**
```bash
# Mount DMG
hdiutil mount dist/PhoenixDrive.dmg
# Drag app to Applications
```

**Linux (AppImage):**
```bash
chmod +x dist/PhoenixDrive.AppImage
dist/PhoenixDrive.AppImage
```

**Linux (DEB):**
```bash
sudo dpkg -i dist/phoenixdrive_1.0.0_amd64.deb
phoenix-drive
```

## Phase 5: Create Release Package

### Step 5.1: Organize Release Files

```bash
mkdir -p releases/v1.0.0
cp dist/* releases/v1.0.0/
```

### Step 5.2: Create Release Notes

```bash
cat > releases/v1.0.0/RELEASE_NOTES.md << EOF
# PhoenixDrive v1.0.0

## What's New
- Automated Mac model detection
- Boot Camp driver installation
- Real-time progress tracking
- WebSocket integration
- Email notifications

## Downloads
- Windows: phoenix-drive.exe
- macOS: PhoenixDrive.dmg
- Linux: PhoenixDrive.AppImage

## Installation
1. Download for your platform
2. Run installer
3. Follow on-screen instructions

## Verification
sha256sum -c *.sha256

## Support
https://github.com/Bboy9090/PhoenixCore-
EOF
```

### Step 5.3: Create GitHub Release

```bash
# Install GitHub CLI if needed
# https://cli.github.com/

cd releases/v1.0.0

# Create release
gh release create v1.0.0 \
  --title "PhoenixDrive v1.0.0" \
  --notes-file RELEASE_NOTES.md \
  phoenix-drive.exe \
  PhoenixDrive.dmg \
  PhoenixDrive.AppImage \
  phoenixdrive_1.0.0_amd64.deb \
  *.sha256
```

## Phase 6: Distribution

### Option 1: GitHub Releases (Recommended)

Files are automatically available at:
```
https://github.com/Bboy9090/PhoenixCore-/releases/tag/v1.0.0
```

### Option 2: Website Download Page

Create download page with:
- Platform-specific download links
- Checksum verification instructions
- Installation guides
- System requirements

### Option 3: Package Managers

**Windows (Chocolatey):**
```bash
# Create package and submit to Chocolatey
```

**macOS (Homebrew):**
```bash
# Create tap and submit to Homebrew
```

**Linux (Snap):**
```bash
# Create snap package
snap pack .
```

## Troubleshooting

### PyInstaller Errors

**"Module not found"**
```bash
pip install -r requirements.txt --upgrade
```

**"Icon file not found"**
```bash
ls -la assets/
# Verify icon files exist
```

### Build Fails on Startup

```bash
# Run in debug mode
python main.py
```

Check for import errors or missing dependencies.

### Installer Creation Fails

**Windows (NSIS):**
```bash
# Verify NSIS is installed
makensis /version
```

**macOS (DMG):**
```bash
# Check disk space
df -h
```

### Code Signing Issues (macOS)

```bash
# List available certificates
security find-identity -v -p codesigning

# Sign manually
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application" dist/phoenix-drive.app
```

## Performance Optimization

### Reduce Executable Size

```bash
# Use UPX compression (optional)
pip install upx
pyinstaller --upx-dir=/path/to/upx main.py
```

### Faster Build Times

```bash
# Use --onedir instead of --onefile (faster, but larger)
pyinstaller --onedir main.py
```

## Security Considerations

1. **Code Signing** — Sign executables to prevent warnings
2. **Checksums** — Always provide SHA256 checksums
3. **HTTPS** — Host downloads over HTTPS only
4. **Virus Scanning** — Scan builds with VirusTotal
5. **Dependencies** — Keep dependencies updated

## Build Checklist

- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Version numbers updated
- [ ] Assets present and correct
- [ ] Build completes without errors
- [ ] Executable runs successfully
- [ ] Installer works on clean system
- [ ] Checksums verified
- [ ] Release notes created
- [ ] GitHub release published
- [ ] Download links working
- [ ] Documentation updated

## Next Steps

1. **Test on Clean System** — Install on fresh machine
2. **Gather Feedback** — Ask users to test
3. **Monitor Issues** — Track bug reports
4. **Plan Updates** — Schedule next release
5. **Automate Builds** — Set up CI/CD pipeline

## Useful Commands Reference

| Command | Purpose |
|---------|---------|
| `python3 -m venv venv` | Create virtual environment |
| `source venv/bin/activate` | Activate virtual environment |
| `pip install -r requirements.txt` | Install dependencies |
| `pyinstaller main.py` | Build executable |
| `sha256sum file` | Generate checksum |
| `gh release create` | Create GitHub release |

---
**Build Time:** 5-15 minutes per platform
**Output Size:** 100-150 MB per platform
**Supported Platforms:** Windows 10+, macOS 10.13+, Linux (Ubuntu 18.04+)
