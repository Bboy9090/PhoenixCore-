#!/usr/bin/env bash
# scripts/customize-ventoy-theme.sh - Ventoy Boot Menu Visual Customizer
set -euo pipefail

# Colors for terminal logging
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================================="
echo "⚡ Ventoy Boot Menu Customizer: Home Aurelia Edition ⚡"
echo -e "==========================================================${NC}"

# 1. Environment & Target Discovery
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THEME_SRC_DIR="$REPO_ROOT/os/phoenix-os/branding/grub/phoenix"
DEFAULT_VOLUME="/Volumes/Ventoy"
TARGET_VOLUME=""

usage() {
    echo -e "Usage: $0 [options]"
    echo -e "Options:"
    echo -e "  --volume <path>   Path to the mounted Ventoy partition (default: /Volumes/Ventoy)"
    echo -e "  -h, --help        Show this help message"
    echo ""
    echo -e "If --volume is not provided, it will automatically search for mounted volumes named:"
    echo -e "  ${GREEN}/Volumes/Ventoy${NC} or ${GREEN}/Volumes/AURELIA${NC}"
    exit 1
}

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        --volume)
            TARGET_VOLUME="${2:-}"
            shift 2
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            echo -e "${RED}[ERROR] Unknown argument: '$1'${NC}"
            usage
            ;;
    esac
done

# Auto-detect if no volume specified
if [ -z "${TARGET_VOLUME}" ]; then
    if [ -d "/Volumes/Ventoy" ]; then
        TARGET_VOLUME="/Volumes/Ventoy"
    elif [ -d "/Volumes/AURELIA" ]; then
        TARGET_VOLUME="/Volumes/AURELIA"
    else
        echo -e "${YELLOW}[WARN] Could not find default mounted volumes under /Volumes/Ventoy or /Volumes/AURELIA.${NC}"
        echo -e "Please plug in your Ventoy USB drive or specify the path manually with --volume."
        echo ""
        df -h
        exit 1
    fi
fi

if [ ! -d "${TARGET_VOLUME}" ]; then
    echo -e "${RED}[ERROR] Specified Ventoy volume path does not exist: ${TARGET_VOLUME}${NC}"
    exit 1
fi

echo -e "${BLUE}[INFO] Target volume detected: ${GREEN}${TARGET_VOLUME}${NC}"

# 2. Stage Ventoy Directories
VENTOY_CONF_DIR="${TARGET_VOLUME}/ventoy"
VENTOY_THEME_DIR="${VENTOY_CONF_DIR}/theme"

echo -e "${BLUE}[INFO] Creating Ventoy configuration directory structure...${NC}"
mkdir -p "${VENTOY_THEME_DIR}"

# 3. Copy & Patch Theme Assets
echo -e "${BLUE}[INFO] Copying premium theme assets to Ventoy...${NC}"
cp -f "${THEME_SRC_DIR}/background.png" "${VENTOY_THEME_DIR}/background.png"

# Patch theme.txt template
THEME_TXT_TEMPLATE="${THEME_SRC_DIR}/theme.txt"
THEME_TXT_DEST="${VENTOY_THEME_DIR}/theme.txt"

if [ -f "${THEME_TXT_TEMPLATE}" ]; then
    echo -e "${BLUE}[INFO] Compiling crash-proof Home Aurelia GRUB theme...${NC}"
    cat > "${THEME_TXT_DEST}" <<'EOF_THEME'
# theme.txt - Safe Home Aurelia GRUB Boot Loader Theme (Solid Color / Font-Safe)
desktop-color: "#05070D"
title-color: "#D4AF37"
title-text: "Phoenix OS: Aurelia Multi-Boot"
title-font: "unicode 16"

+ boot_menu {
  left            = 20%
  top             = 25%
  width           = 60%
  height          = 50%
  item_color      = "#8A929E"
  item_font       = "unicode 12"
  selected_item_color = "#D4AF37"
  selected_item_font  = "unicode 12"
  item_height     = 32
  item_padding    = 10
  item_spacing    = 6
  scrollbar       = true
  scrollbar_width = 6
  scrollbar_color = "#101827"
  scrollbar_thumb_color = "#D4AF37"
}

+ progress_bar {
  id         = "__timeout__"
  left       = 20%
  top        = 78%
  width      = 60%
  height     = 4
  fg_color   = "#D4AF37"
  bg_color   = "#101827"
  border_color = "#101827"
}

+ label {
  id         = "__timeout__"
  left       = 20%
  top        = 81%
  width      = 60%
  height     = 20
  color      = "#8A929E"
  font       = "unicode 10"
  align      = "center"
  text       = "Initializing recovery kernel in %d seconds..."
}

+ label {
  left       = 20%
  top        = 90%
  width      = 60%
  height     = 20
  color      = "#D4AF37"
  font       = "unicode 10"
  align      = "center"
  text       = "Four Legacies. One Throne."
}
EOF_THEME
    echo "✅ Theme text compiled successfully (Solid Color & Font-Safe mode)."
else
    echo -e "${RED}[ERROR] GRUB theme template not found at: ${THEME_TXT_TEMPLATE}${NC}"
    exit 1
fi

# 4. Generate ventoy.json configuration file
echo -e "${BLUE}[INFO] Generating ventoy.json config file...${NC}"
cat > "${VENTOY_CONF_DIR}/ventoy.json" <<EOF
{
    "control": [
        { "VTO_MENU_STYLE": "1" },
        { "VTO_COLOR_THEME": "dark" }
    ],
    "theme": {
        "file": "/ventoy/theme/theme.txt",
        "select_font_color": "#D4AF37"
    }
}
EOF

sync

echo -e "${GREEN}=========================================================="
echo "🎉 Ventoy Premium Theme Applied Successfully!"
echo "🔌 Safe to eject your drive now."
echo "💡 When booting, your Ventoy menu will load with the custom"
echo "   Royal Gold and Electric Blue Home Aurelia branding!"
echo -e "==========================================================${NC}"
exit 0
