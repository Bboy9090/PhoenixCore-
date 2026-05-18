#!/bin/bash
# scripts/verify-edition-visuals.sh - Validate staged boot/login visual wiring for all active editions.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACTIVE_EDITIONS=("home" "revival" "resilient" "blue-phoenix" "forge" "arcwyre" "thunder-god")

STAGING_LB_CONFIG_DIR="$REPO_ROOT/os/phoenix-os/cache/edition-staging/live-build-config"
PLYMOUTH_THEME_DIR="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/plymouth/themes/phoenix"
SDDM_THEME_DIR="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/sddm/themes/phoenix"
WALLPAPER_PATH="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/images/desktop-base/desktop-background.png"
EDITION_META="$STAGING_LB_CONFIG_DIR/includes.chroot/etc/bwos/edition/metadata.json"

cleanup() {
    bash "$REPO_ROOT/scripts/build-edition.sh" --clean-staging >/dev/null 2>&1 || true
}
trap cleanup EXIT

manifest_value() {
    local key="$1"
    local file="$2"
    sed -n "s/^[[:space:]]*${key}:[[:space:]]*//p" "$file" | sed 's/^"//;s/"$//' | head -n 1
}

escape_qml() {
    local value="$1"
    python3 - "$value" <<'PY'
import json
import sys
print(json.dumps(sys.argv[1])[1:-1])
PY
}

echo "=========================================================="
echo "🧪 Blue Phoenix Edition Visual Verification"
echo "=========================================================="

for edition in "${ACTIVE_EDITIONS[@]}"; do
    manifest="$REPO_ROOT/editions/$edition/edition.yaml"
    display_name="$(manifest_value display_name "$manifest")"
    tagline="$(manifest_value tagline "$manifest")"
    display_name_qml="$(escape_qml "$display_name")"
    tagline_qml="$(escape_qml "$tagline")"
    logo_rel="$(manifest_value logo "$manifest")"
    wallpaper_rel="$(manifest_value wallpaper "$manifest")"

    echo ""
    echo "----------------------------------------------------------"
    echo "Checking edition: $edition"
    echo "Display Name: $display_name"
    echo "----------------------------------------------------------"

    bash "$REPO_ROOT/scripts/build-edition.sh" "$edition" --stage-only >/tmp/bwos_stage_${edition}.log 2>&1

    test -f "$PLYMOUTH_THEME_DIR/phoenix.script"
    test -f "$PLYMOUTH_THEME_DIR/progress-bg.png"
    test -f "$PLYMOUTH_THEME_DIR/progress-fill.png"
    test -f "$SDDM_THEME_DIR/Main.qml"
    test -f "$WALLPAPER_PATH"
    test -f "$EDITION_META"

    if rg -q "__EDITION_NAME__|__EDITION_TAGLINE__|__COLOR_PRIMARY__" "$SDDM_THEME_DIR/Main.qml"; then
        echo "❌ Placeholder leak in SDDM template for $edition"
        exit 1
    fi

    if rg -q "__BG_TOP_R__|__BG_BOT_R__" "$PLYMOUTH_THEME_DIR/phoenix.script"; then
        echo "❌ Placeholder leak in Plymouth template for $edition"
        exit 1
    fi

    if ! grep -Fq "$display_name_qml" "$SDDM_THEME_DIR/Main.qml"; then
        echo "❌ Edition display name missing in SDDM theme for $edition"
        exit 1
    fi

    if ! grep -Fq "$tagline_qml" "$SDDM_THEME_DIR/Main.qml"; then
        echo "❌ Edition tagline missing in SDDM theme for $edition"
        exit 1
    fi

    logo_mime="$(file -b --mime-type "$PLYMOUTH_THEME_DIR/phoenix-logo-boot.png" 2>/dev/null || true)"
    wallpaper_mime="$(file -b --mime-type "$WALLPAPER_PATH" 2>/dev/null || true)"

    echo "✅ Logo staged: $logo_rel ($logo_mime)"
    echo "✅ Wallpaper staged: $wallpaper_rel ($wallpaper_mime)"
    echo "✅ Progress assets present and template placeholders resolved"
done

echo ""
echo "=========================================================="
echo "✅ All active editions passed visual staging verification"
echo "=========================================================="
