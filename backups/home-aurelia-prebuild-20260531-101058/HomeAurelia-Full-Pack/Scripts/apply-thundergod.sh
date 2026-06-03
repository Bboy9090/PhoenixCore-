#!/bin/bash
# -------------------------------------------------------------
# Apply Selector — Home Aurelia Thundergod Edition
# -------------------------------------------------------------
echo "👑 Applying Home Aurelia Thundergod Edition..."

# Edit KDE config files via kwriteconfig5 or standard writes
if command -v kwriteconfig5 &>/dev/null; then
    kwriteconfig5 --file kdeglobals --group General --key ColorScheme "HomeAurelia-Thundergod"
    kwriteconfig5 --file kdeglobals --group General --key ActiveElementColorScheme "HomeAurelia-Thundergod"
    kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key theme "HomeAurelia-Thundergod"
    kwriteconfig5 --file plasmarc --group Theme --key name "home-aurelia-thundergod"
    # Refresh config
    qdbus org.kde.KWin /KWin reconfigure 2>/dev/null
    echo "✨ Applied Thundergod Theme configurations successfully!"
else
    echo "⚠️ KDE configuration tool not found. Staging system parameters only."
fi
