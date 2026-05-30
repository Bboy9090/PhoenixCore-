#!/usr/bin/env bash
# build-deb.sh - Debian Binary Package Compiler for Home Aurelia Theme Pack
set -euo pipefail

# Colors for terminal logging
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================================="
echo "⚡ Home Aurelia Theme Pack: Debian Package Compiler ⚡"
echo -e "==========================================================${NC}"

# 1. Staging Setup
STAGING_DIR="deb-staging"
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}/DEBIAN"

# Determine size of files
if du -s --exclude="deb-staging" .. >/dev/null 2>&1; then
    SIZE_KB=$(du -s --exclude="deb-staging" .. | cut -f1)
else
    SIZE_KB=$(du -s .. | cut -f1)
fi

# 2. Generate Debian Control File
cat > "${STAGING_DIR}/DEBIAN/control" <<EOF
Package: home-aurelia-theme-pack
Version: 1.0.0
Section: misc
Priority: optional
Architecture: all
Essential: no
Installed-Size: ${SIZE_KB}
Maintainer: Google DeepMind team <antigravity-dev@google.com>
Depends: bash, sddm, plymouth, grub-common, kvantum
Description: Home Aurelia Linux Theme Pack
 A comprehensive operating system identity package for KDE/Plasma.
 Includes custom wallpaper suites, Plymouth animation sequences,
 SDDM logins, Kvantum control structures, Aurorae border textures,
 color scheme registries, cursor pointers, Obsidian terminal profiles,
 and a local browser start page representing the four legacies.
EOF

# 3. Generate Post-Install Actions Script
cat > "${STAGING_DIR}/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
    echo "=========================================================="
    echo "🎉 Home Aurelia Theme Pack installed successfully!"
    echo "💡 To hot-apply this theme to your active KDE/Plasma session,"
    echo "   run: /usr/share/home-aurelia-theme-pack/apply-theme.sh"
    echo "=========================================================="
fi
exit 0
EOF
chmod 755 "${STAGING_DIR}/DEBIAN/postinst"

# 4. Copy Staged Resources into Debian Root Directories
echo -e "${BLUE}[INFO] Structuring package filesystem...${NC}"

# Color schemes
mkdir -p "${STAGING_DIR}/usr/share/color-schemes"
cp ../06-Color-Schemes/*.colors "${STAGING_DIR}/usr/share/color-schemes/"

# Kvantum
mkdir -p "${STAGING_DIR}/usr/share/Kvantum"
cp -R ../07-Kvantum/HomeAurelia "${STAGING_DIR}/usr/share/Kvantum/"

# Aurorae
mkdir -p "${STAGING_DIR}/usr/share/aurorae/themes"
cp -R ../08-Window-Decorations/Aurorae/HomeAurelia "${STAGING_DIR}/usr/share/aurorae/themes/"

# Icons & Cursors
mkdir -p "${STAGING_DIR}/usr/share/icons/home-aurelia"
cp -R ../09-Icons/* "${STAGING_DIR}/usr/share/icons/home-aurelia/"
mkdir -p "${STAGING_DIR}/usr/share/icons/home-aurelia-cursors"
cp -R ../10-Cursors/* "${STAGING_DIR}/usr/share/icons/home-aurelia-cursors/"

# Sound scheme
mkdir -p "${STAGING_DIR}/usr/share/sounds/home-aurelia"
cp -R ../13-Sounds/* "${STAGING_DIR}/usr/share/sounds/home-aurelia/"

# Plymouth boot theme
mkdir -p "${STAGING_DIR}/usr/share/plymouth/themes/home-aurelia"
cp -R ../04-Plymouth/home-aurelia/* "${STAGING_DIR}/usr/share/plymouth/themes/home-aurelia/"

# SDDM login theme
mkdir -p "${STAGING_DIR}/usr/share/sddm/themes/HomeAurelia"
cp -R ../11-SDDM-Login/HomeAurelia/* "${STAGING_DIR}/usr/share/sddm/themes/HomeAurelia/"

# GRUB boot themes
mkdir -p "${STAGING_DIR}/boot/grub/themes/HomeAurelia"
cp -R ../12-GRUB/HomeAurelia/* "${STAGING_DIR}/boot/grub/themes/HomeAurelia/"

# Konsole terminal
mkdir -p "${STAGING_DIR}/usr/share/konsole"
cp ../17-Terminal/*.colorscheme "${STAGING_DIR}/usr/share/konsole/"

# Browser Welcome Startpage
mkdir -p "${STAGING_DIR}/usr/share/browser-startpage"
cp -R ../18-Browser-Startpage/* "${STAGING_DIR}/usr/share/browser-startpage/"

# Source directories & scripts
mkdir -p "${STAGING_DIR}/usr/share/home-aurelia-theme-pack"
cp ../install.sh ../uninstall.sh ../apply-theme.sh ../build-package.sh "${STAGING_DIR}/usr/share/home-aurelia-theme-pack/"
cp -R ../01-Style-Guide "${STAGING_DIR}/usr/share/home-aurelia-theme-pack/"

# Wallpapers
mkdir -p "${STAGING_DIR}/usr/share/wallpapers"
cp -R ../02-Wallpapers/* "${STAGING_DIR}/usr/share/wallpapers/"

# 5. Build the Debian binary package
OUTPUT_PACKAGE="../../home-aurelia-theme-pack_1.0.0_all.deb"
echo -e "${BLUE}[INFO] Compiling .deb package via dpkg-deb...${NC}"
if command -v dpkg-deb >/dev/null 2>&1; then
    dpkg-deb --build "${STAGING_DIR}" "${OUTPUT_PACKAGE}"
    echo -e "${GREEN}=========================================================="
    echo "🎉 Debian Binary Package Compiled Successfully!"
    echo "📦 Package: ${OUTPUT_PACKAGE}"
    echo "⚖️  Size: $(du -sh "${OUTPUT_PACKAGE}" | cut -f1)"
    echo -e "==========================================================${NC}"
else
    echo -e "${YELLOW}[WARN] dpkg-deb command is not installed on this host."
    echo -e "       Simulated building complete. Folder structure staged successfully at: ${STAGING_DIR}${NC}"
fi

exit 0
