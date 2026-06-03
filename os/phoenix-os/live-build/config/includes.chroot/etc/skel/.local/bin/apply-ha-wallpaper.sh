#!/bin/bash
# Apply HomeAurelia wallpaper on first boot

WALLPAPER="$HOME/.local/share/wallpapers/FHD/ha_wallpaper_home_aurelia_main_1920x1080.png"
if [ -f "$WALLPAPER" ]; then
    # Wait for Plasma to fully initialize
    sleep 5
    if command -v plasma-apply-wallpaperimage >/dev/null 2>&1; then
        plasma-apply-wallpaperimage "$WALLPAPER"
    fi
fi

# Remove this script so it only runs once
rm -f "$0"
rm -f "$HOME/.config/autostart/apply-ha-wallpaper.desktop"
