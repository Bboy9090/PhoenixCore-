#!/bin/bash
# -------------------------------------------------------------
# Home Aurelia FLAGSHIP FULL-THEME UNINSTALLER
# -------------------------------------------------------------
echo "🧹 Uninstalling Home Aurelia Flagship Theme Ecosystem..."

SHARE_DEST="/usr/share"
USER_DEST="$HOME/.local/share"

sudo rm -rf "$SHARE_DEST/icons/home-aurelia" "$USER_DEST/icons/home-aurelia"
sudo rm -rf "$SHARE_DEST/icons/home-aurelia-cursors" "$USER_DEST/icons/home-aurelia-cursors"
sudo rm -rf "$SHARE_DEST/sounds/home-aurelia" "$USER_DEST/sounds/home-aurelia"

for ed in Aurelia Arcwyre Thundergod Native; do
    sudo rm -rf "$SHARE_DEST/aurorae/themes/HomeAurelia-$ed" "$USER_DEST/aurorae/themes/HomeAurelia-$ed"
    sudo rm -f "$SHARE_DEST/color-schemes/HomeAurelia-$ed.colors" "$USER_DEST/color-schemes/HomeAurelia-$ed.colors"
    sudo rm -rf "$SHARE_DEST/Kvantum/HomeAurelia-$ed" "$USER_DEST/Kvantum/HomeAurelia-$ed"
    sudo rm -rf "$SHARE_DEST/plymouth/themes/home-aurelia-$ed"
done

echo "✨ SUCCESS: Clean uninstall completed!"
