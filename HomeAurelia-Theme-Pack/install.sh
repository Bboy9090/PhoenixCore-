#!/usr/bin/env bash
# install.sh - Master Installer for Home Aurelia Linux Theme Pack
set -euo pipefail

# Colors for terminal logging
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================================="
echo "⚡ Home Aurelia Theme Pack: Master Installer Engine ⚡"
echo -e "==========================================================${NC}"

# 1. Environment & Path Setup
HOME_DIR="${HOME}"
USER_ICONS_DIR="$HOME_DIR/.local/share/icons"
USER_PLASMA_DIR="$HOME_DIR/.local/share/plasma/desktoptheme"
USER_COLORS_DIR="$HOME_DIR/.local/share/color-schemes"
USER_AURORAE_DIR="$HOME_DIR/.local/share/aurorae/themes"
USER_KVANTUM_DIR="$HOME_DIR/.config/Kvantum"
USER_WALLPAPER_DIR="$HOME_DIR/.local/share/wallpapers"
USER_SOUNDS_DIR="$HOME_DIR/.local/share/sounds"
USER_KONSOLE_DIR="$HOME_DIR/.local/share/konsole"

# Ensure user directories exist
mkdir -p "$USER_ICONS_DIR" "$USER_PLASMA_DIR" "$USER_COLORS_DIR" \
         "$USER_AURORAE_DIR" "$USER_KVANTUM_DIR" "$USER_WALLPAPER_DIR" \
         "$USER_SOUNDS_DIR" "$USER_KONSOLE_DIR"

# 2. Local User Staging
echo -e "${BLUE}[INFO] Installing user-level KDE desktop styles...${NC}"

# Color schemes
if [ -d "06-Color-Schemes" ]; then
    cp -R 06-Color-Schemes/*.colors "$USER_COLORS_DIR/"
    echo "✅ Colors installed to: ~/.local/share/color-schemes/"
fi

# Kvantum widget style config
if [ -d "07-Kvantum" ]; then
    cp -R 07-Kvantum/HomeAurelia "$USER_KVANTUM_DIR/"
    echo "✅ Kvantum widgets installed to: ~/.config/Kvantum/"
fi

# Aurorae Window Decorations
if [ -d "08-Window-Decorations/Aurorae" ]; then
    cp -R 08-Window-Decorations/Aurorae/HomeAurelia "$USER_AURORAE_DIR/"
    echo "✅ Aurorae window borders installed to: ~/.local/share/aurorae/themes/"
fi

# Icon theme index
if [ -d "09-Icons" ]; then
    cp -R 09-Icons "$USER_ICONS_DIR/home-aurelia/"
    echo "✅ Icon indices installed to: ~/.local/share/icons/home-aurelia/"
fi

# Cursors theme index
if [ -d "10-Cursors" ]; then
    cp -R 10-Cursors "$USER_ICONS_DIR/home-aurelia-cursors/"
    echo "✅ Cursor indices installed to: ~/.local/share/icons/home-aurelia-cursors/"
fi

# Sounds theme index
if [ -d "13-Sounds" ]; then
    cp -R 13-Sounds "$USER_SOUNDS_DIR/home-aurelia/"
    echo "✅ Ambient sound theme installed to: ~/.local/share/sounds/home-aurelia/"
fi

# Terminal colorscheme profile
if [ -d "17-Terminal" ]; then
    cp -R 17-Terminal/*.colorscheme "$USER_KONSOLE_DIR/"
    echo "✅ Konsole profiles installed to: ~/.local/share/konsole/"
fi

# Wallpapers
if [ -d "02-Wallpapers" ]; then
    cp -R 02-Wallpapers/* "$USER_WALLPAPER_DIR/"
    echo "✅ Wallpapers installed to: ~/.local/share/wallpapers/"
fi

# 3. System-Level Integration (SDDM, Plymouth, GRUB require root)
if [ "$(id -u)" -eq 0 ]; then
    echo -e "${BLUE}[INFO] Root permissions detected. Staging system-level files...${NC}"
    
    # SDDM Login screen
    if [ -d "11-SDDM-Login/HomeAurelia" ]; then
        mkdir -p /usr/share/sddm/themes
        cp -R 11-SDDM-Login/HomeAurelia /usr/share/sddm/themes/
        echo "✅ SDDM theme installed to: /usr/share/sddm/themes/HomeAurelia"
    fi

    # Plymouth boot screen
    if [ -d "04-Plymouth/home-aurelia" ]; then
        mkdir -p /usr/share/plymouth/themes
        cp -R 04-Plymouth/home-aurelia /usr/share/plymouth/themes/
        echo "✅ Plymouth theme installed to: /usr/share/plymouth/themes/home-aurelia"
    fi

    # GRUB boot menu theme
    if [ -d "12-GRUB/HomeAurelia" ]; then
        mkdir -p /boot/grub/themes
        cp -R 12-GRUB/HomeAurelia /boot/grub/themes/
        echo "✅ GRUB theme installed to: /boot/grub/themes/HomeAurelia"
    fi
else
    echo -e "${YELLOW}[WARN] Installer is running without root. Skipping system-level boot themes."
    echo -e "       To install SDDM, Plymouth, and GRUB: Rerun this script with sudo: sudo ./install.sh${NC}"
fi

echo -e "${GREEN}=========================================================="
echo "🎉 Home Aurelia Theme Pack Staging Complete!"
echo "💡 To apply colors, run: ./apply-theme.sh"
echo -e "==========================================================${NC}"
exit 0
