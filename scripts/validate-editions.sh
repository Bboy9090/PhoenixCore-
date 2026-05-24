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
    splash_path="$(manifest_value splash "$manifest")"
    login_background_path="$(manifest_value login_background "$manifest")"
    build_arch="$(manifest_value architecture "$manifest")"

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

    # Optional advanced branding fields
    for optional_visual in "$splash_path" "$login_background_path"; do
        if [ -z "$optional_visual" ]; then
            continue
        fi
        resolved_path="$dir/$optional_visual"
        if [ ! -f "$resolved_path" ]; then
            echo "❌ MISSING OPTIONAL BRANDING ASSET: $optional_visual"
            EXIT_CODE=1
            continue 2
        fi

        mime_type="$(file -b --mime-type "$resolved_path" 2>/dev/null || true)"
        if ! echo "$mime_type" | grep -q '^image/'; then
            echo "❌ INVALID OPTIONAL BRANDING ASSET (not an image): $optional_visual ($mime_type)"
            EXIT_CODE=1
            continue 2
        fi
    done

    if [ -n "$build_arch" ]; then
        case "$build_arch" in
            amd64|arm64|i386) ;;
            *)
                echo "❌ INVALID BUILD ARCHITECTURE: $build_arch (allowed: amd64, arm64, i386)"
                EXIT_CODE=1
                continue
                ;;
        esac
    fi

    echo "✅ VALID"
done

echo "============================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "🎉 All editions passed validation."
else
    echo "⚠️ Validation failed."
fi

exit $EXIT_CODE
