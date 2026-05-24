# PhoenixDrive Desktop App — Build Quick Start

Build standalone executables for your platform in 5 minutes.

## Prerequisites

- Python 3.8+
- Git
- Platform-specific tools (see below)

## Step 1: Install Dependencies

```bash
cd /home/ubuntu/phoenix-drive-desktop
pip install -r requirements.txt
```

## Step 2: Make Build Script Executable

```bash
chmod +x build-all-platforms.sh
```

## Step 3: Run Build Script

### Option A: Build for Current Platform (Recommended)

```bash
./build-all-platforms.sh
```

This automatically detects your OS and builds the appropriate installer.

### Option B: Build for Specific Platform

**Windows (from Windows machine):**
```bash
python -m PyInstaller phoenix-drive.spec
```

**macOS (from Mac):**
```bash
python -m PyInstaller phoenix-drive.spec
```

**Linux (from Linux):**
```bash
python -m PyInstaller phoenix-drive.spec
```

## Step 4: Find Your Installer

Built files are in the `releases/` directory:

| Platform | File |
|----------|------|
| Windows | `releases/phoenix-drive.exe` or `releases/PhoenixDrive-Setup.exe` |
| macOS | `releases/PhoenixDrive.dmg` |
| Linux | `releases/PhoenixDrive.AppImage` or `releases/phoenixdrive_1.0.0_amd64.deb` |

## Step 5: Verify Checksums

```bash
cd releases/
sha256sum -c *.sha256
```

All checksums should show "OK".

## Step 6: Test the Installer

### Windows
Double-click `PhoenixDrive-Setup.exe` and follow the installer.

### macOS
1. Double-click `PhoenixDrive.dmg`
2. Drag `phoenix-drive.app` to Applications folder
3. Launch from Applications

### Linux
**AppImage:**
```bash
chmod +x PhoenixDrive.AppImage
./PhoenixDrive.AppImage
```

**DEB Package:**
```bash
sudo dpkg -i phoenixdrive_1.0.0_amd64.deb
phoenix-drive
```

## Step 7: Distribute

### GitHub Releases
```bash
gh release create v1.0.0 releases/* --title "PhoenixDrive v1.0.0"
```

### Manual Distribution
Upload `releases/` files to your website or cloud storage.

## Troubleshooting

### PyInstaller Not Found
```bash
pip install pyinstaller
```

### Permission Denied
```bash
chmod +x build-all-platforms.sh
```

### Build Fails
Check logs:
```bash
./build-all-platforms.sh 2>&1 | tee build.log
```

### Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

## Build Output Structure

```
releases/
├── phoenix-drive              # Linux executable
├── phoenix-drive.exe          # Windows executable
├── phoenix-drive.sha256       # Linux checksum
├── phoenix-drive.exe.sha256   # Windows checksum
├── PhoenixDrive.dmg           # macOS disk image
├── PhoenixDrive.dmg.sha256    # macOS checksum
├── PhoenixDrive.AppImage      # Linux AppImage
├── PhoenixDrive.AppImage.sha256 # AppImage checksum
├── phoenixdrive_1.0.0_amd64.deb # Linux DEB package
└── RELEASE_NOTES.md           # Release notes
```

## Next Steps

1. **Test on Clean System** — Install on a fresh machine to verify everything works
2. **Create GitHub Release** — Upload files to GitHub Releases
3. **Update Website** — Add download links
4. **Announce Release** — Tell users about the new version

---
**Time to Build:** ~5 minutes
**Output Size:** ~100-150 MB per platform
