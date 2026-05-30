#!/usr/bin/env bash
# build-package.sh - Packaging and Syntax Audit Engine for Home Aurelia Linux Theme Pack
set -euo pipefail

# Colors for terminal logging
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================================="
echo "⚡ Home Aurelia Theme Pack: Release Builder Engine ⚡"
echo -e "==========================================================${NC}"

# 1. Self-Diagnosis and Syntax Check
echo -e "${BLUE}[INFO] Auditing shell script syntax integrity...${NC}"
SCRIPTS=("install.sh" "uninstall.sh" "apply-theme.sh" "build-package.sh")
for script in "${SCRIPTS[@]}"; do
    if [ -f "${script}" ]; then
        echo -n "   - Checking syntax of '${script}'... "
        bash -n "${script}"
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}[ERROR] Required script '${script}' is missing!${NC}"
        exit 1
    fi
done

# 2. Folder Structure Verification
echo -e "${BLUE}[INFO] Validating folder layout...${NC}"
REQUIRED_DIRS=(
    "01-Style-Guide"
    "02-Wallpapers"
    "03-Splash-Screens"
    "04-Plymouth"
    "06-Color-Schemes"
    "07-Kvantum"
    "08-Window-Decorations"
    "09-Icons"
    "10-Cursors"
    "11-SDDM-Login"
    "12-GRUB"
    "13-Sounds"
    "14-Branding"
    "17-Terminal"
    "18-Browser-Startpage"
)

MISSING_DIR=0
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "${dir}" ]; then
        echo -e "${RED}[ERROR] Required directory '${dir}' is missing!${NC}"
        MISSING_DIR=1
    fi
done

if [ ${MISSING_DIR} -ne 0 ]; then
    echo -e "${RED}[FATAL] Directory structure validation failed. Aborting compilation.${NC}"
    exit 1
else
    echo -e "✅ Directory structure validated: ${GREEN}OK${NC}"
fi

# 3. Create Package Archive
VERSION="v1.0.0"
OUTPUT_FILE="../HomeAurelia-Theme-Pack-${VERSION}.zip"
echo -e "${BLUE}[INFO] Compiling release archive: ${GREEN}${OUTPUT_FILE}${NC}..."

# We compress everything, excluding common developer noise
zip -r -q "${OUTPUT_FILE}" . \
    -x "*.git*" \
    -x "*.gemini*" \
    -x "*.DS_Store*" \
    -x "node_modules*" \
    -x "build*" \
    -x "out*"

if [ -f "${OUTPUT_FILE}" ]; then
    SIZE_KB=$(du -k "${OUTPUT_FILE}" | cut -f1)
    echo -e "${GREEN}=========================================================="
    echo "🎉 Release Archive Compiled Successfully!"
    echo "📦 Package: ${OUTPUT_FILE}"
    echo "⚖️  Size: ${SIZE_KB} KB"
    echo -e "==========================================================${NC}"
else
    echo -e "${RED}[ERROR] Failed to compile release archive!${NC}"
    exit 1
fi

exit 0
