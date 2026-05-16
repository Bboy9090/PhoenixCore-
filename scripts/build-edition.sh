#!/bin/bash
# build-edition.sh - Synthesize a BWOS edition ISO

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDITION_ID=$1

if [ -z "$EDITION_ID" ]; then
    echo "Usage: ./build-edition.sh <edition-id>"
    exit 1
fi

EDITION_DIR="$REPO_ROOT/editions/$EDITION_ID"

if [ ! -d "$EDITION_DIR" ]; then
    echo "❌ Error: Edition '$EDITION_ID' not found in $REPO_ROOT/editions/"
    exit 1
fi

# 1. Validate
"$REPO_ROOT/scripts/validate-editions.sh" | grep "Checking $EDITION_ID"

manifest="$EDITION_DIR/edition.yaml"
display_name=$(sed -n 's/^[[:space:]]*display_name:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')
tagline=$(sed -n 's/^[[:space:]]*tagline:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')
iso_name=$(sed -n 's/^[[:space:]]*iso_name:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')

echo "🔨 Preparing Synthesis for: $display_name"
echo "   \"$tagline\""
echo ""

# 3. Fail gracefully (Builder not yet implemented in Phase 4)
echo "🔍 Checking for Synthesis Engine..."
if [ ! -d "$REPO_ROOT/os/phoenix-os" ]; then
    echo "❌ Error: OS Build Source not found at os/phoenix-os"
    exit 1
fi

echo "⚠️ Synthesis Engine: os/phoenix-os found, but dynamic edition injection is pending Phase 5."
echo "❌ Error: Dynamic synthesis of '$iso_name' is not yet operational."
echo "   Please use legacy build scripts for Phoenix OS until Phase 4 synthesis is verified."

exit 1
