#!/bin/bash
# -------------------------------------------------------------
# Apply Selector — Home Aurelia Native Edition
# -------------------------------------------------------------
echo "👑 Applying Home Aurelia Native Edition..."

# Edit KDE config files via kwriteconfig5 or standard writes
if command -v kwriteconfig5 &>/dev/null; then
    kwriteconfig5 --file kdeglobals --group General --key ColorScheme "HomeAurelia-Native"
    kwriteconfig5 --file kdeglobals --group General --key ActiveElementColorScheme "HomeAurelia-Native"
    kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key theme "HomeAurelia-Native"
    kwriteconfig5 --file plasmarc --group Theme --key name "home-aurelia-native"
    # Refresh config
    qdbus org.kde.KWin /KWin reconfigure 2>/dev/null
    echo "✨ Applied Native Theme configurations successfully!"
else
    echo "⚠️ KDE configuration tool not found. Staging system parameters only."
fi
