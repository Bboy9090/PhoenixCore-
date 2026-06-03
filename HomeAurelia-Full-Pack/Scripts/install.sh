#!/bin/bash
# -------------------------------------------------------------
# Home Aurelia FLAGSHIP FULL-THEME INSTALLER
# Designed by Bobby Bboy9090
# -------------------------------------------------------------
echo "🚀 Installing Home Aurelia Flagship Theme Ecosystem..."

SHARE_DEST="/usr/share"
USER_DEST="$HOME/.local/share"

# Copy core shared directories
echo "📦 Staging Shared Core Components..."
sudo cp -R Core/HomeAurelia-Icons "$SHARE_DEST/icons/home-aurelia" 2>/dev/null || cp -R Core/HomeAurelia-Icons "$USER_DEST/icons/home-aurelia"
sudo cp -R Core/HomeAurelia-Cursors "$SHARE_DEST/icons/home-aurelia-cursors" 2>/dev/null || cp -R Core/HomeAurelia-Cursors "$USER_DEST/icons/home-aurelia-cursors"
sudo cp -R Core/HomeAurelia-Sounds "$SHARE_DEST/sounds/home-aurelia" 2>/dev/null || cp -R Core/HomeAurelia-Sounds "$USER_DEST/sounds/home-aurelia"
sudo cp -R Core/HomeAurelia-Fonts/* "/usr/share/fonts/truetype/" 2>/dev/null || cp -R Core/HomeAurelia-Fonts/* "$HOME/.local/share/fonts/"

echo "🎨 Copying Theme Editions..."
for ed in Aurelia Arcwyre Thundergod Native; do
    echo "   -> Copying $ed Theme files..."
    # Aurorae window decorations
    sudo cp -R Editions/$ed/Aurorae-Window-Decoration "$SHARE_DEST/aurorae/themes/HomeAurelia-$ed" 2>/dev/null || cp -R Editions/$ed/Aurorae-Window-Decoration "$USER_DEST/aurorae/themes/HomeAurelia-$ed"
    # KDE Color Schemes
    sudo cp Editions/$ed/Color-Scheme/*.colors "$SHARE_DEST/color-schemes/" 2>/dev/null || cp Editions/$ed/Color-Scheme/*.colors "$USER_DEST/color-schemes/"
    # Kvantum Themes
    sudo cp -R Editions/$ed/Kvantum/* "$SHARE_DEST/Kvantum/" 2>/dev/null || cp -R Editions/$ed/Kvantum/* "$USER_DEST/Kvantum/"
    # Plymouth Theme variants
    sudo cp -R Editions/$ed/Plymouth "$SHARE_DEST/plymouth/themes/home-aurelia-$ed" 2>/dev/null
done

echo "✨ SUCCESS: Flagship Home Aurelia Full Theme Pack successfully installed!"
