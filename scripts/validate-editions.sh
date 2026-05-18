#!/bin/bash
# validate-editions.sh - Verify all BWOS editions comply with platform rules

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDITIONS_DIR="$REPO_ROOT/editions"

manifest_value() {
    local key="$1"
    local file="$2"
    sed -n "s/^[[:space:]]*${key}:[[:space:]]*//p" "$file" | sed 's/^"//;s/"$//' | head -n 1
}

echo "🔍 Validating Bobby’s Worldwide OS Editions..."
echo "============================================"

EXIT_CODE=0

for dir in "$EDITIONS_DIR"/*/; do
    [ -d "$dir" ] || continue
    edition_id=$(basename "$dir")
    manifest="$dir/edition.yaml"
    
    echo -n "Checking $edition_id... "
    
    if [ ! -f "$manifest" ]; then
        echo "❌ MISSING edition.yaml"
        EXIT_CODE=1
        continue
    fi

    # Basic Field Validation (Shell only, no YAML parser)
    if ! grep -q "^id: $edition_id" "$manifest"; then
        echo "❌ ID mismatch in manifest"
        EXIT_CODE=1
        continue
    fi

    if ! grep -q "inherits_core_safety_rules: true" "$manifest"; then
        echo "❌ SAFETY VIOLATION: Must inherit core safety rules"
        EXIT_CODE=1
        continue
    fi

    if ! grep -q "allow_destructive_disk_ops_by_default: false" "$manifest"; then
        echo "❌ SAFETY VIOLATION: Destructive ops must be disabled by default"
        EXIT_CODE=1
        continue
    fi

    # Verify Assets
    for asset in "colors.css" "branding.md" "package-profile.txt"; do
        if [ ! -f "$dir/$asset" ]; then
            echo "❌ MISSING ASSET: $asset"
            EXIT_CODE=1
            continue 2
        fi
    done

    logo_path="$(manifest_value logo "$manifest")"
    wallpaper_path="$(manifest_value wallpaper "$manifest")"

    if [ -z "$logo_path" ]; then
        echo "❌ MISSING BRANDING FIELD: logo"
        EXIT_CODE=1
        continue
    fi

    if [ -z "$wallpaper_path" ]; then
        echo "❌ MISSING BRANDING FIELD: wallpaper"
        EXIT_CODE=1
        continue
    fi

    for visual in "$logo_path" "$wallpaper_path"; do
        resolved_path="$dir/$visual"
        if [ ! -f "$resolved_path" ]; then
            echo "❌ MISSING BRANDING ASSET: $visual"
            EXIT_CODE=1
            continue 2
        fi

        mime_type="$(file -b --mime-type "$resolved_path" 2>/dev/null || true)"
        if ! echo "$mime_type" | grep -q '^image/'; then
            echo "❌ INVALID BRANDING ASSET (not an image): $visual ($mime_type)"
            EXIT_CODE=1
            continue 2
        fi
    done

    echo "✅ VALID"
done

echo "============================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "🎉 All editions passed validation."
else
    echo "⚠️ Validation failed."
fi

exit $EXIT_CODE
