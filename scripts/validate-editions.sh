#!/bin/bash
# validate-editions.sh - Verify all BWOS editions comply with platform rules

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDITIONS_DIR="$REPO_ROOT/editions"

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

    echo "✅ VALID"
done

echo "============================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "🎉 All editions passed validation."
else
    echo "⚠️ Validation failed."
fi

exit $EXIT_CODE
