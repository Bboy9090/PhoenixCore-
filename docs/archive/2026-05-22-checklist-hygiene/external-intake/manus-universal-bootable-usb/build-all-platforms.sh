#!/bin/bash

# PhoenixDrive Desktop App — Automated Build Script for All Platforms
# Builds standalone executables for Windows, macOS, and Linux

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERSION="1.0.0"
BUILD_DIR="dist"
RELEASE_DIR="releases"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PhoenixDrive Desktop App - Build Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check Prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo -e "${YELLOW}! Installing PyInstaller...${NC}"
    pip install pyinstaller
fi

echo -e "${GREEN}✓ Python 3 found${NC}"
echo -e "${GREEN}✓ PyInstaller available${NC}"

# Step 2: Clean Previous Builds
echo ""
echo -e "${YELLOW}Step 2: Cleaning previous builds...${NC}"

rm -rf build dist *.spec __pycache__
mkdir -p "$BUILD_DIR" "$RELEASE_DIR"

echo -e "${GREEN}✓ Clean complete${NC}"

# Step 3: Install Dependencies
echo ""
echo -e "${YELLOW}Step 3: Installing dependencies...${NC}"

pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 4: Detect Platform
echo ""
echo -e "${YELLOW}Step 4: Detecting platform...${NC}"

PLATFORM=$(uname -s)
case "$PLATFORM" in
    Linux*)
        echo -e "${GREEN}✓ Detected: Linux${NC}"
        BUILD_LINUX=true
        ;;
    Darwin*)
        echo -e "${GREEN}✓ Detected: macOS${NC}"
        BUILD_MACOS=true
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo -e "${GREEN}✓ Detected: Windows${NC}"
        BUILD_WINDOWS=true
        ;;
    *)
        echo -e "${YELLOW}! Unknown platform: $PLATFORM${NC}"
        ;;
esac

# Step 5: Build for Current Platform
echo ""
echo -e "${YELLOW}Step 5: Building for current platform...${NC}"

if [ "$BUILD_WINDOWS" = true ]; then
    echo -e "${BLUE}Building Windows executable...${NC}"
    
    pyinstaller --onefile \
        --windowed \
        --icon=assets/icon.ico \
        --name=phoenix-drive \
        --add-data "assets:assets" \
        --add-data "src:src" \
        main.py
    
    # Create installer
    if command -v makensis &> /dev/null; then
        echo -e "Creating Windows installer..."
        makensis installer.nsi
        echo -e "${GREEN}✓ Installer created: $BUILD_DIR/PhoenixDrive-Setup.exe${NC}"
    fi
    
    echo -e "${GREEN}✓ Windows build complete${NC}"
    echo -e "  Executable: $BUILD_DIR/phoenix-drive.exe"
    
    # Generate checksum
    certutil -hashfile "$BUILD_DIR/phoenix-drive.exe" SHA256 > "$BUILD_DIR/phoenix-drive.exe.sha256"
    echo -e "  Checksum: $BUILD_DIR/phoenix-drive.exe.sha256"

elif [ "$BUILD_MACOS" = true ]; then
    echo -e "${BLUE}Building macOS app bundle...${NC}"
    
    pyinstaller --onefile \
        --windowed \
        --icon=assets/icon.icns \
        --name=phoenix-drive \
        --add-data "assets:assets" \
        --add-data "src:src" \
        --osx-bundle-identifier=com.phoenixdrive.app \
        main.py
    
    # Create DMG
    echo -e "Creating macOS disk image..."
    hdiutil create -volname "PhoenixDrive" \
        -srcfolder "$BUILD_DIR/phoenix-drive.app" \
        -ov -format UDZO "$BUILD_DIR/PhoenixDrive.dmg"
    
    # Code signing (optional)
    if command -v codesign &> /dev/null; then
        echo -e "Signing application..."
        codesign --deep --force --verify --verbose \
            --sign "-" "$BUILD_DIR/phoenix-drive.app" 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ macOS build complete${NC}"
    echo -e "  App Bundle: $BUILD_DIR/phoenix-drive.app"
    echo -e "  DMG: $BUILD_DIR/PhoenixDrive.dmg"
    
    # Generate checksums
    shasum -a 256 "$BUILD_DIR/PhoenixDrive.dmg" > "$BUILD_DIR/PhoenixDrive.dmg.sha256"
    echo -e "  Checksums: $BUILD_DIR/PhoenixDrive.dmg.sha256"

elif [ "$BUILD_LINUX" = true ]; then
    echo -e "${BLUE}Building Linux executable...${NC}"
    
    pyinstaller --onefile \
        --icon=assets/icon.png \
        --name=phoenix-drive \
        --add-data "assets:assets" \
        --add-data "src:src" \
        main.py
    
    # Create AppImage
    if command -v appimagetool &> /dev/null; then
        echo -e "Creating AppImage..."
        appimagetool "$BUILD_DIR/phoenix-drive" "$BUILD_DIR/PhoenixDrive.AppImage"
        echo -e "${GREEN}✓ AppImage created: $BUILD_DIR/PhoenixDrive.AppImage${NC}"
    fi
    
    # Create DEB package
    echo -e "Creating DEB package..."
    mkdir -p debian/DEBIAN debian/usr/bin debian/usr/share/applications debian/usr/share/pixmaps
    cp "$BUILD_DIR/phoenix-drive" debian/usr/bin/
    
    cat > debian/DEBIAN/control << EOF
Package: phoenixdrive
Version: $VERSION
Architecture: amd64
Maintainer: PhoenixDrive Team <team@phoenixdrive.com>
Description: Boot Camp driver installer and USB builder
 PhoenixDrive automatically detects your Mac model and provides
 the correct Windows drivers with automated installation.
EOF
    
    dpkg-deb --build debian "$BUILD_DIR/phoenixdrive_${VERSION}_amd64.deb"
    rm -rf debian
    
    echo -e "${GREEN}✓ Linux build complete${NC}"
    echo -e "  Executable: $BUILD_DIR/phoenix-drive"
    echo -e "  AppImage: $BUILD_DIR/PhoenixDrive.AppImage"
    echo -e "  DEB Package: $BUILD_DIR/phoenixdrive_${VERSION}_amd64.deb"
    
    # Generate checksums
    sha256sum "$BUILD_DIR/phoenix-drive" > "$BUILD_DIR/phoenix-drive.sha256"
    sha256sum "$BUILD_DIR/PhoenixDrive.AppImage" > "$BUILD_DIR/PhoenixDrive.AppImage.sha256"
    echo -e "  Checksums: $BUILD_DIR/*.sha256"
fi

# Step 6: Create Release Package
echo ""
echo -e "${YELLOW}Step 6: Creating release package...${NC}"

# Copy to releases directory
cp -r "$BUILD_DIR"/* "$RELEASE_DIR/"

echo -e "${GREEN}✓ Release package created in $RELEASE_DIR/${NC}"

# Step 7: Generate Release Notes
echo ""
echo -e "${YELLOW}Step 7: Generating release notes...${NC}"

cat > "$RELEASE_DIR/RELEASE_NOTES.md" << EOF
# PhoenixDrive v$VERSION Release Notes

## What's New
- Automated Mac model detection
- Boot Camp driver installation
- Real-time progress tracking
- WebSocket integration with mobile app
- Email notifications

## Downloads
- **Windows**: phoenix-drive.exe
- **macOS**: PhoenixDrive.dmg
- **Linux**: PhoenixDrive.AppImage or phoenixdrive_${VERSION}_amd64.deb

## Installation
1. Download the appropriate installer for your platform
2. Run the installer
3. Follow the on-screen instructions
4. Connect to your mobile app for driver installation

## Verification
All downloads include SHA256 checksums for verification:
\`\`\`bash
sha256sum -c phoenix-drive.sha256
\`\`\`

## Support
For issues or questions, visit: https://github.com/your-org/phoenixdrive

---
Released: $(date)
EOF

echo -e "${GREEN}✓ Release notes created${NC}"

# Step 8: Display Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Build Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Version: $VERSION${NC}"
echo -e "${GREEN}✓ Platform: $PLATFORM${NC}"
echo -e "${GREEN}✓ Output Directory: $RELEASE_DIR${NC}"
echo ""
echo -e "${YELLOW}Files created:${NC}"
ls -lh "$RELEASE_DIR"/ | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Test the application on a clean system"
echo -e "2. Verify checksums: sha256sum -c $RELEASE_DIR/*.sha256"
echo -e "3. Create GitHub release with these files"
echo -e "4. Update download page with release links"
echo -e "5. Announce release to users"
echo ""
echo -e "${GREEN}Build completed successfully!${NC}"
