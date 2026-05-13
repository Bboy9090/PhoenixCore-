#!/bin/bash

# Bobby's PhoenixDrive Desktop App - Build Script
# Creates standalone executables for Windows, macOS, and Linux

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="PhoenixDrive"
APP_VERSION="1.0.0"
BUILD_DIR="dist"
SPEC_FILE="phoenix-drive.spec"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Bobby's PhoenixDrive - Build Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}Installing PyInstaller...${NC}"
    pip3 install PyInstaller
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Determine platform
PLATFORM=$(uname -s)
case "$PLATFORM" in
    Linux*)
        PLATFORM="Linux"
        OUTPUT_NAME="${APP_NAME}-${APP_VERSION}-linux-x86_64"
        ;;
    Darwin*)
        PLATFORM="macOS"
        OUTPUT_NAME="${APP_NAME}-${APP_VERSION}-macos-universal"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        PLATFORM="Windows"
        OUTPUT_NAME="${APP_NAME}-${APP_VERSION}-windows-x86_64"
        ;;
    *)
        echo -e "${RED}Unsupported platform: $PLATFORM${NC}"
        exit 1
        ;;
esac

echo -e "${BLUE}Building for: $PLATFORM${NC}"
echo ""

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.egg-info/
echo -e "${GREEN}✓ Cleaned${NC}"
echo ""

# Build executable
echo -e "${YELLOW}Building executable...${NC}"
echo -e "${BLUE}This may take a few minutes...${NC}"
echo ""

pyinstaller \
    --onefile \
    --windowed \
    --name="$APP_NAME" \
    --version-file=version.txt 2>/dev/null || true \
    --icon=src/ui/icons/app.ico 2>/dev/null || true \
    "$SPEC_FILE"

if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build completed${NC}"
echo ""

# Create distribution package
echo -e "${YELLOW}Creating distribution package...${NC}"

if [ ! -d "$BUILD_DIR" ]; then
    mkdir -p "$BUILD_DIR"
fi

# Copy executable to dist
if [ "$PLATFORM" = "macOS" ]; then
    # macOS app bundle
    cp -r "dist/$APP_NAME.app" "$BUILD_DIR/"
    PACKAGE_PATH="$BUILD_DIR/$APP_NAME.app"
elif [ "$PLATFORM" = "Windows" ]; then
    # Windows executable
    cp "dist/$APP_NAME.exe" "$BUILD_DIR/"
    PACKAGE_PATH="$BUILD_DIR/$APP_NAME.exe"
else
    # Linux executable
    cp "dist/$APP_NAME" "$BUILD_DIR/"
    PACKAGE_PATH="$BUILD_DIR/$APP_NAME"
fi

echo -e "${GREEN}✓ Distribution package created${NC}"
echo ""

# Create archive
echo -e "${YELLOW}Creating archive...${NC}"

if [ "$PLATFORM" = "macOS" ]; then
    # Create DMG for macOS
    cd "$BUILD_DIR"
    hdiutil create -volname "$APP_NAME" -srcfolder . -ov -format UDZO "$OUTPUT_NAME.dmg" 2>/dev/null || \
    tar -czf "$OUTPUT_NAME.tar.gz" "$APP_NAME.app"
    cd ..
elif [ "$PLATFORM" = "Windows" ]; then
    # Create ZIP for Windows
    cd "$BUILD_DIR"
    zip -r "$OUTPUT_NAME.zip" "$APP_NAME.exe" 2>/dev/null || \
    tar -czf "$OUTPUT_NAME.tar.gz" "$APP_NAME.exe"
    cd ..
else
    # Create TAR.GZ for Linux
    cd "$BUILD_DIR"
    tar -czf "$OUTPUT_NAME.tar.gz" "$APP_NAME"
    cd ..
fi

echo -e "${GREEN}✓ Archive created${NC}"
echo ""

# Display results
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Build Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Platform:     ${GREEN}$PLATFORM${NC}"
echo -e "App Name:     ${GREEN}$APP_NAME${NC}"
echo -e "Version:      ${GREEN}$APP_VERSION${NC}"
echo -e "Output Dir:   ${GREEN}$BUILD_DIR${NC}"
echo ""

# List artifacts
echo -e "${YELLOW}Build Artifacts:${NC}"
ls -lh "$BUILD_DIR"/ 2>/dev/null | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Test the executable on your system"
echo "2. Create installer (optional)"
echo "3. Upload to release page"
echo "4. Share with users"
echo ""

echo -e "${GREEN}Build complete! 🎉${NC}"
