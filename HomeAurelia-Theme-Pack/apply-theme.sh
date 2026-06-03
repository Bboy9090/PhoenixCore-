#!/usr/bin/env bash
# apply-theme.sh - Active Plasma Theme Applier for Home Aurelia Linux Theme Pack
set -euo pipefail

# Colors for terminal logging
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================================="
echo "⚡ Home Aurelia Theme Pack: Active Plasma Applier ⚡"
echo -e "==========================================================${NC}"

# Usage information
usage() {
    echo -e "Usage: $0 [variant]"
    echo -e "Available variants:"
    echo -e "  ${GREEN}HomeAurelia${NC}           - Flagship gold-accented deep navy workstation colors"
    echo -e "  ${GREEN}HomeAurelia-Arcwyre${NC}   - Aggressive storm-rebellion red-blue colors"
    echo -e "  ${GREEN}HomeAurelia-Thundergod${NC} - Clean white/blue/gold heroic colors"
    echo -e "  ${GREEN}HomeAurelia-Native${NC}     - Ancestral ascension blue-red ultimate colors"
    echo ""
    echo -e "If no variant is specified, it defaults to ${BLUE}HomeAurelia${NC}."
    exit 1
}

# 1. Parse Arguments
VARIANT="HomeAurelia"
if [ $# -ge 1 ]; then
    case "$1" in
        HomeAurelia|HomeAurelia-Arcwyre|HomeAurelia-Thundergod|HomeAurelia-Native)
            VARIANT="$1"
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            echo -e "${RED}[ERROR] Invalid variant: '$1'${NC}"
            usage
            ;;
    esac
fi

echo -e "${BLUE}[INFO] Applying active theme variant: ${GREEN}${VARIANT}${NC}..."

# 2. Paths Configuration
HOME_DIR="${HOME}"
USER_WALLPAPER_DIR="$HOME_DIR/.local/share/wallpapers"
CONFIG_FILE="$HOME_DIR/.config/plasma-org.kde.plasma.desktop-appletsrc"

# Determine wallpaper image name based on variant
WALLPAPER_FILE=""
case "${VARIANT}" in
    HomeAurelia)
        WALLPAPER_FILE="FHD/ha_wallpaper_home_aurelia_main_1920x1080.png"
        ;;
    HomeAurelia-Arcwyre)
        WALLPAPER_FILE="FHD/ha_wallpaper_arcwyre_1920x1080.png"
        ;;
    HomeAurelia-Thundergod)
        WALLPAPER_FILE="FHD/ha_wallpaper_thundergod_1920x1080.png"
        ;;
    HomeAurelia-Native)
        WALLPAPER_FILE="FHD/ha_wallpaper_native_1920x1080.png"
        ;;
esac

WALLPAPER_PATH="${USER_WALLPAPER_DIR}/${WALLPAPER_FILE}"
WALLPAPER_URI="file://${WALLPAPER_PATH}"

# Determine Dynamic Theme Names
if [[ "$VARIANT" == "HomeAurelia" ]]; then
    ICON_THEME="home-aurelia"
    KVANTUM_THEME="HomeAurelia"
    AURORAE_THEME="HomeAurelia"
else
    # Extract suffix and lowercase (e.g. HomeAurelia-Arcwyre -> home-aurelia-arcwyre)
    SUFFIX="${VARIANT#HomeAurelia-}"
    ICON_THEME="home-aurelia-${SUFFIX,,}"
    KVANTUM_THEME="${VARIANT}"
    AURORAE_THEME="${VARIANT}"
fi
CURSOR_THEME="${ICON_THEME}-cursors"

# 3. Apply KDE Color Scheme
echo -e "${BLUE}[INFO] Setting color scheme to: ${GREEN}${VARIANT}${NC}..."
if command -v plasma-apply-colorscheme >/dev/null 2>&1; then
    plasma-apply-colorscheme "${VARIANT}" || true
else
    # Fallback to direct kwriteconfig updates
    for kwriteconfig in kwriteconfig6 kwriteconfig5; do
        if command -v "${kwriteconfig}" >/dev/null 2>&1; then
            "${kwriteconfig}" --file kdeglobals --group General --key ColorScheme "${VARIANT}" || true
        fi
    done
fi

# 4. Apply Icon Theme
echo -e "${BLUE}[INFO] Setting icon theme to: ${GREEN}${ICON_THEME}${NC}..."
for kwriteconfig in kwriteconfig6 kwriteconfig5; do
    if command -v "${kwriteconfig}" >/dev/null 2>&1; then
        "${kwriteconfig}" --file kdeglobals --group Icons --key Theme "${ICON_THEME}" || true
    fi
done

# 5. Apply Cursor Theme
echo -e "${BLUE}[INFO] Setting cursor theme to: ${GREEN}${CURSOR_THEME}${NC}..."
if command -v plasma-apply-cursortheme >/dev/null 2>&1; then
    plasma-apply-cursortheme "${CURSOR_THEME}" || true
else
    for kwriteconfig in kwriteconfig6 kwriteconfig5; do
        if command -v "${kwriteconfig}" >/dev/null 2>&1; then
            "${kwriteconfig}" --file kcminputrc --group Mouse --key cursorTheme "${CURSOR_THEME}" || true
        fi
    done
fi

# 6. Apply Window Decoration Theme
echo -e "${BLUE}[INFO] Setting window decoration theme to: ${GREEN}${AURORAE_THEME}${NC}..."
for kwriteconfig in kwriteconfig6 kwriteconfig5; do
    if command -v "${kwriteconfig}" >/dev/null 2>&1; then
        "${kwriteconfig}" --file kwinrc --group org.kde.kdecoration2 --key library "org.kde.aurorae" || true
        "${kwriteconfig}" --file kwinrc --group org.kde.kdecoration2 --key theme "${AURORAE_THEME}" || true
    fi
done

# 7. Apply Kvantum Widget Style Config
echo -e "${BLUE}[INFO] Setting Kvantum widget style to: ${GREEN}${KVANTUM_THEME}${NC}..."
mkdir -p "$HOME_DIR/.config/Kvantum"
cat > "$HOME_DIR/.config/Kvantum/kvantum.kvconfig" <<EOF
[General]
theme=${KVANTUM_THEME}
EOF

# 8. Apply Wallpaper
if [ -f "${WALLPAPER_PATH}" ]; then
    echo -e "${BLUE}[INFO] Setting wallpaper to: ${GREEN}${WALLPAPER_PATH}${NC}..."
    if command -v plasma-apply-wallpaperimage >/dev/null 2>&1; then
        plasma-apply-wallpaperimage "${WALLPAPER_PATH}" >/dev/null 2>&1 || true
    fi

    # Fallback to direct appletsrc configuration write
    for kwriteconfig in kwriteconfig6 kwriteconfig5; do
        if command -v "${kwriteconfig}" >/dev/null 2>&1; then
            for containment in 1 2 3 4 5 6; do
                "${kwriteconfig}" --file "${CONFIG_FILE}" --group "Containments" --group "${containment}" --group "Wallpaper" --group "org.kde.image" --group "General" --key "Image" "${WALLPAPER_URI}" >/dev/null 2>&1 || true
                "${kwriteconfig}" --file "${CONFIG_FILE}" --group "Containments" --group "${containment}" --key "wallpaperplugin" "org.kde.image" >/dev/null 2>&1 || true
            done
        fi
    done
else
    echo -e "${YELLOW}[WARN] Wallpaper file not found at: ${WALLPAPER_PATH}. Please run ./install.sh first.${NC}"
fi

# 9. Trigger Config Refresh via DBus
echo -e "${BLUE}[INFO] Notifying desktop shell to reload configurations...${NC}"
qdbus org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true
qdbus org.kde.keyboard /Layouts org.kde.KeyboardLayouts.reloadConfig >/dev/null 2>&1 || true

echo -e "${GREEN}=========================================================="
echo "🎉 Theme '${VARIANT}' Applied Successfully!"
echo "💡 Note: You may need to log out and log back in, or restart"
echo "   plasmashell (kquitapp5 plasmashell && kstart5 plasmashell)"
echo "   for all visual changes to propagate across running apps."
echo -e "==========================================================${NC}"
exit 0
