#!/bin/bash
# list-editions.sh - List all available BWOS editions and metadata

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDITIONS_DIR="$REPO_ROOT/editions"

echo "Bobby’s Worldwide OS: Available Editions"
echo "========================================"

for dir in "$EDITIONS_DIR"/*/; do
    [ -d "$dir" ] || continue
    manifest="$dir/edition.yaml"
    
    [ -f "$manifest" ] || continue
    if grep -Eq '^[[:space:]]*status:[[:space:]]*archived[[:space:]]*$' "$manifest"; then
        continue
    fi
    
    id=$(sed -n 's/^[[:space:]]*id:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')
    display_name=$(sed -n 's/^[[:space:]]*display_name:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')
    tagline=$(sed -n 's/^[[:space:]]*tagline:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')
    iso_name=$(sed -n 's/^[[:space:]]*iso_name:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')

    printf "[%s] %s\n" "$id" "$display_name"
    printf "  Tagline: %s\n" "$tagline"
    if [ -n "$iso_name" ]; then
        printf "  Target ISO: %s\n" "$iso_name"
    fi
    echo ""
done
