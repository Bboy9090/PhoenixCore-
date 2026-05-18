#!/bin/bash
# scripts/build-all-isos-fast.sh - Hyper-Fast Multi-Edition Synthesis using OCI Bypass Rebuild (PR35)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$REPO_ROOT/iso/outputs"
mkdir -p "$OUTPUT_DIR"

ACTIVE_EDITIONS=("home" "revival" "resilient" "blue-phoenix" "forge" "arcwyre" "thunder-god")
BASE_EDITION="home"

echo "=========================================================="
echo "⚡ Blue Phoenix OS: Hyper-Fast Master ISO Synthesizer ⚡"
echo "=========================================================="
echo "Using PR35 Bypass Rebuild Engine to package all editions"
echo "in under 3 minutes total!"
echo "⚠️  Fast mode reuses the base initramfs for non-base editions."
echo "   For edition-specific Plymouth boot splash/progress branding, use build-all-isos.sh."
echo "=========================================================="
echo ""

# 1. Ensure Docker is running
if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    echo "❌ Error: Docker daemon is not reachable. (Ensure Docker Desktop is running)"
    exit 1
fi

BUILD_OUT_DIR="$REPO_ROOT/os/phoenix-os/build"
BASE_ISO_PATH="$BUILD_OUT_DIR/bwos-${BASE_EDITION}.iso"

# 2. Check if the Base ISO exists, if not build it first
if [ ! -f "$BASE_ISO_PATH" ]; then
    echo "⚠️  Base ISO for '$BASE_EDITION' not found. Performing initial bootstrap build..."
    echo "   (This first run will bootstrap the cache. Subsequent builds will be instant.)"
    echo ""
    bash "$REPO_ROOT/scripts/build-edition.sh" "$BASE_EDITION"
fi

if [ ! -f "$BASE_ISO_PATH" ]; then
    echo "❌ Error: Failed to locate or generate the base ISO."
    exit 1
fi

echo "✅ Base ISO verified at: $BASE_ISO_PATH"
echo ""

SUCCESS_COUNT=0
FAILED_EDITIONS=()

# Copy Base ISO directly to final outputs
echo "📦 Archiving base edition '$BASE_EDITION'..."
cp "$BASE_ISO_PATH" "$OUTPUT_DIR/bwos-${BASE_EDITION}.iso"
SUCCESS_COUNT=$((SUCCESS_COUNT + 1))

# 3. Fast-synthesize all other editions using bypass-rebuild.sh inside the OCI container
for ed in "${ACTIVE_EDITIONS[@]}"; do
    if [ "$ed" = "$BASE_EDITION" ]; then
        continue
    fi
    
    echo ""
    echo "----------------------------------------------------------"
    echo "⚡ [FAST SYNTHESIZING EDITION: $ed]"
    echo "----------------------------------------------------------"
    
    # We run bypass-rebuild.sh inside the pre-built container to avoid local macOS dependencies
    # Map the host paths appropriately so they align with the OCI workspace mount
    # In-container mount points:
    # - Workspace: /workspace (corresponds to REPO_ROOT)
    # - Output ISO: /workspace/os/phoenix-os/build/bwos-ed.iso
    
    docker compose \
        -f "$REPO_ROOT/os/phoenix-os/container/docker-compose.yml" \
        --project-directory "$REPO_ROOT/os/phoenix-os/container" \
        --project-name "phoenix-os-oci" \
        run --rm builder bash -lc "
            set -euo pipefail
            bash /workspace/os/phoenix-os/scripts/bypass-rebuild.sh \
                --edition $ed \
                --base-iso /workspace/os/phoenix-os/build/bwos-${BASE_EDITION}.iso
        "
        
    SYNTH_ISO="$REPO_ROOT/os/phoenix-os/build/bwos-$ed.iso"
    if [ -f "$SYNTH_ISO" ]; then
        echo "✅ SUCCESS: Synthesized $ed ISO."
        echo "📦 Archiving final ISO to: $OUTPUT_DIR/bwos-$ed.iso"
        cp "$SYNTH_ISO" "$OUTPUT_DIR/bwos-$ed.iso"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "❌ FAILURE: Failed to synthesize $ed ISO."
        FAILED_EDITIONS+=("$ed")
    fi
done

echo ""
echo "=========================================================="
echo "🏁 Fast Synthesis Suite Finished"
echo "=========================================================="
echo "🎉 Successful builds: $SUCCESS_COUNT / ${#ACTIVE_EDITIONS[@]}"

if [ ${#FAILED_EDITIONS[@]} -gt 0 ]; then
    echo "❌ Failed editions: ${FAILED_EDITIONS[*]}"
    exit 1
else
    echo "✨ All Seven Paths OS editions synthesized and archived successfully in:"
    echo "   $OUTPUT_DIR"
    exit 0
fi
