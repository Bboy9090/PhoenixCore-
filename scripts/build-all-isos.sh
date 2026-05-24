#!/bin/bash
# scripts/build-all-isos.sh - Orchestrate compilation of active BWOS product edition ISOs
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$REPO_ROOT/iso/outputs"
mkdir -p "$OUTPUT_DIR"

STANDARD_EDITIONS=("home" "blue-phoenix" "arcwyre" "thunder-god")
AVAILABLE_EDITIONS=()
while IFS= read -r edition_dir; do
    edition_id="$(basename "$edition_dir")"
    edition_manifest="$REPO_ROOT/editions/$edition_id/edition.yaml"
    if grep -Eq '^[[:space:]]*archived:[[:space:]]*true([[:space:]]|$)' "$edition_manifest" 2>/dev/null; then
        continue
    fi
    AVAILABLE_EDITIONS+=("$edition_id")
done < <(find "$REPO_ROOT/editions" -mindepth 1 -maxdepth 1 -type d | sort)

TARGET_EDITIONS=()
for ed in "${STANDARD_EDITIONS[@]}"; do
    if [ -d "$REPO_ROOT/editions/$ed" ]; then
        TARGET_EDITIONS+=("$ed")
    fi
done

RESUME_FROM=""
SKIP_EXISTING=false
BUILDER_CLEAN_MODE="stage" # none, stage, all
BUILDER_NO_CACHE=false
FAIL_FAST=false
LIST_ONLY=false

usage() {
    cat <<'EOF'
Usage: ./scripts/build-all-isos.sh [options]

Options:
  --editions=<csv>       Build only these editions (e.g. home,blue-phoenix,arcwyre)
  --resume-from=<id>     Build from this edition onward
  --skip-existing        Skip edition if iso/outputs/<iso_name> already exists
  --clean-mode=<mode>    Builder clean mode: none|stage|all (default: stage)
  --no-cache             Disable APT package cache reuse
  --fail-fast            Stop at first failed edition
  --list-editions        Print known edition ids and exit
  -h, --help             Show this help

Examples:
  ./scripts/build-all-isos.sh --resume-from=home --skip-existing
  ./scripts/build-all-isos.sh --editions=home,blue-phoenix --clean-mode=stage
  ./scripts/build-all-isos.sh --editions=home --clean-mode=none
EOF
}

trim() {
    local s="$1"
    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"
    printf '%s' "$s"
}

edition_exists() {
    local id="$1"
    local e
    for e in "${AVAILABLE_EDITIONS[@]}"; do
        if [ "$e" = "$id" ]; then
            return 0
        fi
    done
    return 1
}

manifest_iso_name() {
    local edition="$1"
    local manifest="$REPO_ROOT/editions/$edition/edition.yaml"
    sed -n 's/^[[:space:]]*iso_name:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//' | head -n 1
}

parse_editions_csv() {
    local csv="$1"
    local raw item
    IFS=',' read -r -a raw <<< "$csv"
    TARGET_EDITIONS=()

    for item in "${raw[@]}"; do
        item="$(trim "$item")"
        [ -z "$item" ] && continue
        if ! edition_exists "$item"; then
            echo "❌ Unknown edition in --editions: $item"
            exit 1
        fi
        TARGET_EDITIONS+=("$item")
    done

    if [ "${#TARGET_EDITIONS[@]}" -eq 0 ]; then
        echo "❌ --editions resolved to an empty set."
        exit 1
    fi
}

apply_resume_filter() {
    local id="$1"
    local filtered=()
    local found=false
    local item

    for item in "${TARGET_EDITIONS[@]}"; do
        if [ "$item" = "$id" ]; then
            found=true
        fi
        if [ "$found" = true ]; then
            filtered+=("$item")
        fi
    done

    if [ "$found" = false ]; then
        echo "❌ --resume-from edition '$id' is not in the selected build list."
        exit 1
    fi

    TARGET_EDITIONS=("${filtered[@]}")
}

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --editions=*)
            parse_editions_csv "${1#*=}"
            ;;
        --resume-from=*)
            RESUME_FROM="${1#*=}"
            ;;
        --skip-existing)
            SKIP_EXISTING=true
            ;;
        --clean-mode=*)
            BUILDER_CLEAN_MODE="${1#*=}"
            ;;
        --no-cache)
            BUILDER_NO_CACHE=true
            ;;
        --fail-fast)
            FAIL_FAST=true
            ;;
        --list-editions)
            LIST_ONLY=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
    shift
done

if [ "$LIST_ONLY" = true ]; then
    printf "%s\n" "${AVAILABLE_EDITIONS[@]}"
    exit 0
fi

if [[ ! "$BUILDER_CLEAN_MODE" =~ ^(none|stage|all)$ ]]; then
    echo "❌ Invalid --clean-mode: $BUILDER_CLEAN_MODE (allowed: none|stage|all)"
    exit 1
fi

if [ -n "$RESUME_FROM" ]; then
    if ! edition_exists "$RESUME_FROM"; then
        echo "❌ Unknown --resume-from edition: $RESUME_FROM"
        exit 1
    fi
    apply_resume_filter "$RESUME_FROM"
fi

echo "=========================================================="
echo "🔥 Blue Phoenix OS: Product Family Master ISO Builder"
echo "=========================================================="
echo "Selected editions:"
for ed in "${TARGET_EDITIONS[@]}"; do
    echo "  - $ed"
done
echo "Builder clean mode: $BUILDER_CLEAN_MODE"
echo "Skip existing: $SKIP_EXISTING"
echo "Use package cache: $([ "$BUILDER_NO_CACHE" = true ] && echo "no" || echo "yes")"
echo "=========================================================="
echo ""

if [ "$BUILDER_CLEAN_MODE" = "none" ]; then
    echo "⚠️ WARNING: --clean-mode=none is fastest but may carry previous chroot state."
    echo "   Use stage/all for deterministic release artifacts."
    echo ""
fi

# Check Docker
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "✅ Docker engine detected and reachable."
else
    echo "⚠️  WARNING: Docker daemon is not reachable in this shell context."
    echo "   Ensure Docker Desktop is running and you have necessary permissions."
    echo ""
fi

# Confirm with user if interactive
if [ -t 0 ]; then
    read -p "🚀 Press [ENTER] to begin compilation, or Ctrl+C to cancel..."
fi

SUCCESS_COUNT=0
SALVAGED_COUNT=0
SKIPPED_COUNT=0
FAILED_EDITIONS=()

for ed in "${TARGET_EDITIONS[@]}"; do
    echo ""
    echo "----------------------------------------------------------"
    echo "🔨 [BUILDING EDITION: $ed]"
    echo "----------------------------------------------------------"

    manifest="$REPO_ROOT/editions/$ed/edition.yaml"
    iso_name="$(manifest_iso_name "$ed")"
    out_iso="$OUTPUT_DIR/$iso_name"

    if [ "$SKIP_EXISTING" = true ] && [ -s "$out_iso" ]; then
        echo "⏭️  SKIP: Output already exists: $out_iso"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        continue
    fi

    build_cmd=(
        bash "$REPO_ROOT/scripts/build-edition.sh" "$ed"
        "--builder-clean=$BUILDER_CLEAN_MODE"
    )
    if [ "$BUILDER_NO_CACHE" = true ]; then
        build_cmd+=(--builder-no-cache)
    fi

    if "${build_cmd[@]}"; then
        echo "✅ SUCCESS: Staged and synthesized ISO for $ed."

        synth_iso="$REPO_ROOT/os/phoenix-os/build/$iso_name"
        if [ -f "$synth_iso" ]; then
            echo "📦 Archiving final ISO to: $out_iso"
            cp "$synth_iso" "$out_iso"
        fi
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        synth_iso="$REPO_ROOT/os/phoenix-os/build/$iso_name"
        if [ -f "$synth_iso" ]; then
            echo "⚠️  BUILD EXITED NON-ZERO, BUT ISO EXISTS for $ed."
            echo "📦 Salvaging produced ISO to: $out_iso"
            cp "$synth_iso" "$out_iso"
            SALVAGED_COUNT=$((SALVAGED_COUNT + 1))
        else
            echo "❌ FAILURE: Failed to compile ISO for $ed."
            FAILED_EDITIONS+=("$ed")
            if [ "$FAIL_FAST" = true ]; then
                echo "⛔ Fail-fast enabled. Stopping build loop."
                break
            fi
        fi
    fi
done

echo ""
echo "=========================================================="
echo "🏁 Master Compilation Suite Finished"
echo "=========================================================="
echo "🎉 Successful builds: $SUCCESS_COUNT / ${#TARGET_EDITIONS[@]}"
echo "🛟 Salvaged builds: $SALVAGED_COUNT / ${#TARGET_EDITIONS[@]}"
echo "⏭️ Skipped builds: $SKIPPED_COUNT / ${#TARGET_EDITIONS[@]}"

if [ ${#FAILED_EDITIONS[@]} -gt 0 ]; then
    echo "❌ Failed editions: ${FAILED_EDITIONS[*]}"
    exit 1
else
    echo "✨ Selected editions synthesized and archived successfully in:"
    echo "   $OUTPUT_DIR"
    exit 0
fi
