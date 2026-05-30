#!/usr/bin/env bash
# uninstall.sh - Master Uninstaller for Home Aurelia Linux Theme Pack
set -euo pipefail

# Colors for terminal logging
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}=========================================================="
echo "⚡ Home Aurelia Theme Pack: Master Uninstaller Engine ⚡"
echo -e "==========================================================${NC}"

# User Paths
HOME_DIR="${HOME}"
USER_ICONS_DIR="$HOME_DIR/.local/share/icons"
USER_COLORS_DIR="$HOME_DIR/.local/share/color-schemes"
USER_AURORAE_DIR="$HOME_DIR/.local/share/aurorae/themes"
USER_KVANTUM_DIR="$HOME_DIR/.config/Kvantum"
USER_SOUNDS_DIR="$HOME_DIR/.local/share/sounds"
USER_KONSOLE_DIR="$HOME_DIR/.local/share/konsole"

echo -e "${BLUE}[INFO] Purging user-level KDE desktop styles...${NC}"

# Color schemes
rm -f "$USER_COLORS_DIR"/HomeAurelia*.colors
echo "🗑️  Removed colors from: ~/.local/share/color-schemes/"

# Kvantum
rm -rf "$USER_KVANTUM_DIR/HomeAurelia"
echo "🗑️  Removed Kvantum config from: ~/.config/Kvantum/"

# Aurorae window decorations
rm -rf "$USER_AURORAE_DIR/HomeAurelia"
echo "🗑️  Removed Aurorae borders from: ~/.local/share/aurorae/themes/"

# Icons & Cursors
rm -rf "$USER_ICONS_DIR/home-aurelia"
rm -rf "$USER_ICONS_DIR/home-aurelia-cursors"
echo "🗑️  Removed icon & cursor directories from: ~/.local/share/icons/"

# Sounds
rm -rf "$USER_SOUNDS_DIR/home-aurelia"
echo "🗑️  Removed sound theme from: ~/.local/share/sounds/"

# Terminal Konsole colorschemes
rm -f "$USER_KONSOLE_DIR"/home-aurelia*.colorscheme
echo "🗑️  Removed Konsole profiles from: ~/.local/share/konsole/"

# Root integrations
if [ "$(id -u)" -eq 0 ]; then
    echo -e "${BLUE}[INFO] Root permissions detected. Cleaning system boot directories...${NC}"
    
    # SDDM Login screen
    rm -rf /usr/share/sddm/themes/HomeAurelia
    echo "🗑️  Removed SDDM theme from: /usr/share/sddm/themes/"

    # Plymouth boot screen
    rm -rf /usr/share/plymouth/themes/home-aurelia
    echo "🗑️  Removed Plymouth theme from: /usr/share/plymouth/themes/"

    # GRUB boot menu theme
    rm -rf /boot/grub/themes/HomeAurelia
    echo "🗑️  Removed GRUB theme from: /boot/grub/themes/"
else
    echo -e "${YELLOW}[WARN] Installer is running without root. System boot themes left untouched."
    echo -e "       To clean SDDM, Plymouth, and GRUB: Rerun this script with sudo: sudo ./uninstall.sh${NC}"
fi

echo -e "${GREEN}=========================================================="
echo "🎉 Home Aurelia Theme Pack Purged Successfully!"
echo -e "==========================================================${NC}"
exit 0
