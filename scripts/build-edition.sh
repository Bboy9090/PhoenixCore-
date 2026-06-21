#!/bin/bash
# build-edition.sh - Synthesize a BWOS edition ISO

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PHOENIX_OS_ARTIFACT_DIR:-$REPO_ROOT/os/phoenix-os/build}"
EDITION_ID=""
STAGE_ONLY=false
CLEAN_STAGING=false
BUILDER_MODE="release"
BUILDER_ARCH=""
BUILDER_CLEAN_MODE="stage"
BUILDER_NO_CACHE=false
LOGGER_SCRIPT="$REPO_ROOT/os/phoenix-os/scripts/build-logger.sh"
HEARTBEAT_SCRIPT="$REPO_ROOT/os/phoenix-os/scripts/build-heartbeat.sh"
HEARTBEAT_PID=""
BUILD_TELEMETRY_INITIALIZED=false
BUILD_BUILD_ID=""
BUILD_TELEMETRY_DIR=""
BUILD_FINAL_ARTIFACT=""
BUILD_FINAL_SHA256=""
BUILD_FINAL_SIZE=""
BUILD_SOURCE_COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"

# Transient staging roots (kept out of tracked live-build config/)
STAGING_ROOT="$REPO_ROOT/os/phoenix-os/cache/edition-staging"
STAGING_LB_CONFIG_DIR="$STAGING_ROOT/live-build-config"
STAGING_CHROOT="$STAGING_LB_CONFIG_DIR/includes.chroot/etc/bwos/edition"
PACKAGE_LIST_DIR="$STAGING_LB_CONFIG_DIR/package-lists"
STAGED_PKG_LIST="$PACKAGE_LIST_DIR/edition.list.chroot"
STAGED_PKG_SOURCE="$STAGING_CHROOT/package-profile.source.txt"
STAGED_PKG_INSTALLED="$STAGING_CHROOT/package-profile.installed.txt"
STAGED_PKG_BLOCKED="$STAGING_CHROOT/package-profile.blocked.txt"
STAGING_WALLPAPER_PATH="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/images/desktop-base/desktop-background.png"

function stop_build_heartbeat() {
    if [ -n "$HEARTBEAT_PID" ]; then
        kill "$HEARTBEAT_PID" 2>/dev/null || true
        wait "$HEARTBEAT_PID" 2>/dev/null || true
        HEARTBEAT_PID=""
    fi
}

function finalize_build_telemetry() {
    local exit_code="$1"

    stop_build_heartbeat

    if [ "$BUILD_TELEMETRY_INITIALIZED" != true ]; then
        return 0
    fi

    if [ ! -f "${PHOENIX_BUILD_SUMMARY_JSON:-}" ] && [ -f "$LOGGER_SCRIPT" ]; then
        # The inner build should usually finalize the summary, but if it didn't
        # we emit a truthful wrapper-level summary here.
        if [ "$exit_code" -eq 0 ]; then
            phoenix_build_logger_finalize "completed" "" "$BUILD_FINAL_ARTIFACT" "$BUILD_FINAL_SHA256" "$BUILD_FINAL_SIZE"
        else
            if [ -z "${PHOENIX_BUILD_FAILURE_CLASS:-}" ]; then
                phoenix_build_logger_error "Wrapper exited before a summary was produced." "${PHOENIX_BUILD_CURRENT_PHASE:-unknown}" "wrapper_script_failure"
            fi
            phoenix_build_logger_finalize "failed" "${PHOENIX_BUILD_FAILURE_CLASS:-wrapper_script_failure}" "$BUILD_FINAL_ARTIFACT" "$BUILD_FINAL_SHA256" "$BUILD_FINAL_SIZE"
        fi
    fi
}

function start_build_heartbeat() {
    if [ "$BUILD_TELEMETRY_INITIALIZED" != true ]; then
        return 0
    fi
    if [ ! -f "$HEARTBEAT_SCRIPT" ]; then
        return 0
    fi

    (
        while true; do
            "$HEARTBEAT_SCRIPT" \
                --state-file "$PHOENIX_BUILD_STATE_JSON" \
                --container-project "${PHOENIX_OS_COMPOSE_PROJECT:-phoenix-os-oci}" \
                --container-service "${PHOENIX_OS_BUILDER_SERVICE:-builder}" \
                1>>"$PHOENIX_BUILD_EVENT_LOG" \
                2>>"$PHOENIX_BUILD_HUMAN_LOG" || true
            sleep 60
        done
    ) &
    HEARTBEAT_PID="$!"
}

trap 'finalize_build_telemetry $?' EXIT

function clean_staging() {
    echo "🧹 Cleaning transient edition staging cache..."
    rm -rf "$STAGING_ROOT"
    echo "✅ Transient staging cache clean."
}

function map_package_alias() {
    local pkg="$1"
    case "$pkg" in
        ddrescue) echo "gddrescue" ;;
        memtest86-plus) echo "memtest86+" ;;
        clonezilla-cli) echo "clonezilla" ;;
        wireshark-cli) echo "tshark" ;;
        ghidra-headless) echo "binwalk" ;;
        badblocks) echo "e2fsprogs" ;;
        *) echo "$pkg" ;;
    esac
}

function is_blocked_package() {
    local pkg="$1"
    shift
    local blocked
    for blocked in "$@"; do
        if [ "$pkg" = "$blocked" ]; then
            return 0
        fi
    done
    return 1
}

function sanitize_package_profile() {
    local source_file="$1"
    local target_file="$2"
    local blocked_file="$3"
    echo "🧹 Sanitizing package profile: $(basename "$source_file")"
    local temp_file="${target_file}.tmp"
    local normalized_file="${target_file}.normalized"
    # Blocked packages that cause build failures or represent internal placeholders.
    local blocked_pkgs=(
        "bless" "libglib2.0-cil" "libglade2.0-cil" "libgtk2.0-cil" "mono-runtime" "mono-common"
        "bwos-core" "bootforge" "bootforge-pro" "arcwyre-control-center" "forensic-toolset"
        "legacy-utility-set" "original-phoenix-wallpapers" "classic-sound-scheme"
        "hardware-burn-in-tools" "mass-deployment-scripts"
    )
    local raw_pkg mapped_pkg

    # 1) Strip comments/whitespace
    # 2) Remap known aliases to Debian bullseye package names
    # 3) Remove blocked/internal package placeholders
    # 4) De-duplicate while preserving first appearance order
    grep -v '^[[:space:]]*#' "$source_file" | sed 's/[[:space:]]*#.*//' | sed 's/[[:space:]]*$//' | grep -v '^[[:space:]]*$' > "$temp_file" || true

    : > "$normalized_file"
    : > "$blocked_file"
    while IFS= read -r raw_pkg; do
        mapped_pkg="$(map_package_alias "$raw_pkg")"

        if [ "$mapped_pkg" != "$raw_pkg" ]; then
            echo "↪️  Remapped package '$raw_pkg' -> '$mapped_pkg'"
        fi

        if is_blocked_package "$mapped_pkg" "${blocked_pkgs[@]}"; then
            echo "⚠️  WARNING: Removing internal/blocked package '$raw_pkg' from $(basename "$source_file")."
            echo "$raw_pkg" >> "$blocked_file"
            continue
        fi

        echo "$mapped_pkg" >> "$normalized_file"
    done < "$temp_file"

    mkdir -p "$(dirname "$target_file")"
    awk '!seen[$0]++' "$normalized_file" > "$target_file"
    rm -f "$temp_file" "$normalized_file"
}

function manifest_value() {
    local key="$1"
    local file="$2"
    sed -n "s/^[[:space:]]*${key}:[[:space:]]*//p" "$file" | sed 's/^"//;s/"$//' | head -n 1
}

function profile_value() {
    local profile="$1"
    local key="$2"
    local file="$3"
    # Match from profile entry key at 2 spaces indentation to next non-empty entry at 2 spaces indentation
    sed -n "/^[[:space:]]\{2\}${profile}:/,/^[[:space:]]\{2\}[a-zA-Z0-9_-]\{1,\}:/ { /^[[:space:]]\{4\}${key}:/p; }" "$file" | sed "s/^[[:space:]]*${key}:[[:space:]]*//;s/^\"//;s/\"$//" | head -n 1
}


function manifest_color() {
    local key="$1"
    local file="$2"
    awk -v k="$key" '
        $1 ~ ("^" k ":") {
            if (match($0, /#[0-9A-Fa-f]{6}/)) {
                print substr($0, RSTART, RLENGTH)
                exit
            }
        }
    ' "$file"
}

function normalize_color() {
    local raw="${1:-}"
    local fallback="${2:-#3B82F6}"
    raw="$(echo "$raw" | tr -d '[:space:]')"
    if [[ "$raw" =~ ^#[0-9A-Fa-f]{6}$ ]]; then
        echo "$raw"
    else
        echo "$fallback"
    fi
}

function hex_to_rgb_floats() {
    local hex="$1"
    python3 - "$hex" <<'PY'
import sys
h = sys.argv[1].strip().lstrip("#")
r = int(h[0:2], 16) / 255.0
g = int(h[2:4], 16) / 255.0
b = int(h[4:6], 16) / 255.0
print(f"{r:.3f} {g:.3f} {b:.3f}")
PY
}

function scale_hex_color() {
    local hex="$1"
    local factor="$2"
    python3 - "$hex" "$factor" <<'PY'
import sys
h = sys.argv[1].strip().lstrip("#")
f = float(sys.argv[2])
r = max(0, min(255, round(int(h[0:2], 16) * f)))
g = max(0, min(255, round(int(h[2:4], 16) * f)))
b = max(0, min(255, round(int(h[4:6], 16) * f)))
print(f"#{r:02X}{g:02X}{b:02X}")
PY
}

function make_solid_png() {
    local out_path="$1"
    local hex="$2"
    local alpha="${3:-255}"
    python3 - "$out_path" "$hex" "$alpha" <<'PY'
import binascii
import struct
import sys
import zlib

out_path, color_hex, alpha = sys.argv[1], sys.argv[2].lstrip("#"), int(sys.argv[3])
r = int(color_hex[0:2], 16)
g = int(color_hex[2:4], 16)
b = int(color_hex[4:6], 16)

def chunk(chunk_type, data):
    return (
        struct.pack("!I", len(data))
        + chunk_type
        + data
        + struct.pack("!I", binascii.crc32(chunk_type + data) & 0xFFFFFFFF)
    )

# RGBA pixel with filter byte 0
raw = bytes([0, r, g, b, alpha])
ihdr = struct.pack("!IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
png = (
    b"\x89PNG\r\n\x1a\n"
    + chunk(b"IHDR", ihdr)
    + chunk(b"IDAT", zlib.compress(raw, 9))
    + chunk(b"IEND", b"")
)

with open(out_path, "wb") as f:
    f.write(png)
PY
}

function escape_qml_string() {
    local value="$1"
    python3 - "$value" <<'PY'
import json
import sys
print(json.dumps(sys.argv[1])[1:-1])
PY
}

function derive_arch_from_target() {
    local target="$1"
    if [[ "$target" =~ ^live-image-([A-Za-z0-9_+-]+)$ ]]; then
        echo "${BASH_REMATCH[1]}"
        return
    fi
    echo ""
}

function default_linux_flavour_for_arch() {
    local arch="$1"
    case "$arch" in
        amd64) echo "amd64" ;;
        arm64) echo "arm64" ;;
        i386) echo "686" ;;
        *) echo "amd64" ;;
    esac
}

# Parse arguments
BUILD_PROFILE=""
DRY_RUN=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --stage-only) STAGE_ONLY=true ;;
        --clean-staging) CLEAN_STAGING=true ;;
        --builder-mode=*) BUILDER_MODE="${1#*=}" ;;
        --builder-arch=*) BUILDER_ARCH="${1#*=}" ;;
        --builder-clean=*) BUILDER_CLEAN_MODE="${1#*=}" ;;
        --builder-no-cache) BUILDER_NO_CACHE=true ;;
        --profile=*) BUILD_PROFILE="${1#*=}" ;;
        --profile) BUILD_PROFILE="$2"; shift ;;
        --dry-run) DRY_RUN=true ;;
        -*) echo "Unknown option: $1"; exit 1 ;;
        *) EDITION_ID="$1" ;;
    esac
    shift
done

if [ "$CLEAN_STAGING" = true ]; then
    clean_staging
    exit 0
fi

if [ -z "$EDITION_ID" ]; then
    echo "Usage: ./build-edition.sh <edition-id> [--stage-only] [--clean-staging] [--builder-mode=<mode>] [--builder-arch=<arch>] [--builder-clean=<none|stage|all>] [--builder-no-cache]"
    exit 1
fi

EDITION_DIR="$REPO_ROOT/editions/$EDITION_ID"

if [ ! -d "$EDITION_DIR" ]; then
    echo "❌ Error: Edition '$EDITION_ID' not found in $REPO_ROOT/editions/"
    exit 1
fi

# 1. Validate
"$REPO_ROOT/scripts/validate-editions.sh" | grep "Checking $EDITION_ID"

# 2. Extract Metadata
manifest="$EDITION_DIR/edition.yaml"
display_name=$(manifest_value display_name "$manifest")
tagline=$(manifest_value tagline "$manifest")
iso_name=$(manifest_value iso_name "$manifest")
build_target=$(manifest_value target "$manifest")
manifest_arch=$(manifest_value architecture "$manifest")
manifest_linux_flavour=$(manifest_value linux_flavour "$manifest")
manifest_bootloader=$(manifest_value bootloader "$manifest")
wallpaper_name=$(manifest_value wallpaper "$manifest")
logo_name=$(manifest_value logo "$manifest")
splash_name=$(manifest_value splash "$manifest")
login_background_name=$(manifest_value login_background "$manifest")
primary_color=$(normalize_color "$(manifest_color primary "$manifest")" "#3B82F6")
secondary_color=$(normalize_color "$(manifest_color secondary "$manifest")" "#64748B")
background_color=$(normalize_color "$(manifest_color background "$manifest")" "#070B16")
surface_color=$(normalize_color "$(manifest_color surface "$manifest")" "#111827")
text_color=$(normalize_color "$(manifest_color text "$manifest")" "#E5E7EB")

# Determine Asset Theme Names
icon_theme=$(manifest_value icon_theme "$manifest")
if [ -z "$icon_theme" ]; then
    if [ "$EDITION_ID" == "home" ]; then
        icon_theme="home-aurelia"
    else
        icon_theme="home-aurelia-${EDITION_ID}"
    fi
fi

cursor_theme=$(manifest_value cursor_theme "$manifest")
if [ -z "$cursor_theme" ]; then
    cursor_theme="${icon_theme}-cursors"
fi

kvantum_theme=$(manifest_value kvantum_theme "$manifest")
if [ -z "$kvantum_theme" ]; then
    if [ "$EDITION_ID" == "home" ]; then
        kvantum_theme="HomeAurelia"
    else
        kvantum_theme="HomeAurelia-$(echo $EDITION_ID | awk -F'-' '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1' | tr -d ' ')"
    fi
fi

aurorae_theme=$(manifest_value aurorae_theme "$manifest")
if [ -z "$aurorae_theme" ]; then
    aurorae_theme="$kvantum_theme"
fi

# Determine Color Scheme Name
color_scheme=$(manifest_value color_scheme "$manifest")
if [ -z "$color_scheme" ]; then
    if [ "$EDITION_ID" == "home" ]; then
        color_scheme="HomeAurelia-Aurelia"
    else
        # Match variant logic from apply-theme.sh
        color_scheme="HomeAurelia-${display_name%%:*}"
        # If display_name is "Arcwyre: Thundergod Edition", taking everything before ":" -> "Arcwyre" -> "HomeAurelia-Arcwyre"
        # But we actually want "HomeAurelia-Thundergod" for Thundergod edition.
        # It's better to just use EDITION_ID converted to CamelCase, or we can use the folder name logic.
        color_scheme="HomeAurelia-$(echo $EDITION_ID | awk -F'-' '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1' | tr -d ' ')"
    fi
fi

# Apply profile overrides if --profile is specified
if [ -n "$BUILD_PROFILE" ]; then
    profiles_yaml="$REPO_ROOT/editions/profiles.yaml"
    if [ -f "$profiles_yaml" ]; then
        profile_name=$(profile_value "$BUILD_PROFILE" "name" "$profiles_yaml")
        if [ -n "$profile_name" ]; then
            echo "🚀 Applying target profile overrides: $profile_name ($BUILD_PROFILE)"
            profile_arch=$(profile_value "$BUILD_PROFILE" "arch" "$profiles_yaml")
            profile_bootloader=$(profile_value "$BUILD_PROFILE" "bootloader" "$profiles_yaml")
            profile_iso_name=$(profile_value "$BUILD_PROFILE" "iso_name" "$profiles_yaml")
            profile_parent_edition=$(profile_value "$BUILD_PROFILE" "parent_edition" "$profiles_yaml")
            profile_custom_path=$(profile_value "$BUILD_PROFILE" "profile_path" "$profiles_yaml")
            
            if [ -n "$profile_arch" ]; then
                manifest_arch="$profile_arch"
            fi
            if [ -n "$profile_bootloader" ]; then
                manifest_bootloader="$profile_bootloader"
            fi
            if [ -n "$profile_iso_name" ]; then
                iso_name="$profile_iso_name"
            fi
            if [ -n "$profile_parent_edition" ] && [ "$profile_parent_edition" != "$EDITION_ID" ]; then
                echo "❌ Error: Profile '$BUILD_PROFILE' is designed for parent edition '$profile_parent_edition', but you requested '$EDITION_ID'"
                exit 1
            fi
        else
            echo "❌ Error: Target profile '$BUILD_PROFILE' not found in $profiles_yaml"
            exit 1
        fi
    else
        echo "⚠️ Warning: profiles.yaml not found at $profiles_yaml"
    fi
fi

resolved_arch="$manifest_arch"
if [ -z "$resolved_arch" ]; then
    resolved_arch="$(derive_arch_from_target "$build_target")"
fi
if [ -z "$resolved_arch" ]; then
    resolved_arch="amd64"
fi

resolved_linux_flavour="$manifest_linux_flavour"
if [ -z "$resolved_linux_flavour" ]; then
    resolved_linux_flavour="$(default_linux_flavour_for_arch "$resolved_arch")"
fi

resolved_bootloader="${manifest_bootloader:-grub-efi}"

if [ -n "$BUILDER_ARCH" ]; then
    resolved_arch="$BUILDER_ARCH"
    # If user explicitly overrides arch, keep linux flavour coherent unless explicitly set.
    if [ -z "$manifest_linux_flavour" ]; then
        resolved_linux_flavour="$(default_linux_flavour_for_arch "$resolved_arch")"
    fi
fi

if [ -n "$wallpaper_name" ] && [ ! -f "$EDITION_DIR/$wallpaper_name" ]; then
    echo "❌ Error: Wallpaper path in manifest does not exist: $wallpaper_name"
    exit 1
fi

if [ -n "$logo_name" ] && [ ! -f "$EDITION_DIR/$logo_name" ]; then
    echo "❌ Error: Logo path in manifest does not exist: $logo_name"
    exit 1
fi

if [ -n "$splash_name" ] && [ ! -f "$EDITION_DIR/$splash_name" ]; then
    echo "❌ Error: Splash path in manifest does not exist: $splash_name"
    exit 1
fi

if [ -n "$login_background_name" ] && [ ! -f "$EDITION_DIR/$login_background_name" ]; then
    echo "❌ Error: Login background path in manifest does not exist: $login_background_name"
    exit 1
fi

echo "🔨 Selected Edition: $display_name"
echo "   Tagline: \"$tagline\""
echo "   Target artifact: $iso_name"
echo "   Target Arch: $resolved_arch"
echo "   Linux Flavour: $resolved_linux_flavour"
echo "   Bootloader: $resolved_bootloader"
echo ""

if [ -f "$LOGGER_SCRIPT" ]; then
    # Build telemetry is only initialized once the manifest has been resolved.
    BUILD_BUILD_ID="$(date -u +%Y%m%dT%H%M%SZ)-${EDITION_ID}-${resolved_arch}"
    BUILD_TELEMETRY_DIR="$BUILD_DIR/telemetry/$BUILD_BUILD_ID"
    # shellcheck source=/dev/null
    source "$LOGGER_SCRIPT"
    phoenix_build_logger_init \
        "$BUILD_TELEMETRY_DIR" \
        "$BUILD_BUILD_ID" \
        "$EDITION_ID" \
        "$display_name" \
        "$resolved_arch" \
        "$iso_name" \
        "$BUILDER_MODE" \
        "$manifest" \
        "$BUILD_SOURCE_COMMIT"
    BUILD_TELEMETRY_INITIALIZED=true
    export PHOENIX_BUILD_ID="$BUILD_BUILD_ID"
    export PHOENIX_BUILD_EDITION_ID="$EDITION_ID"
    export PHOENIX_BUILD_EDITION_NAME="$display_name"
    export PHOENIX_BUILD_ARCHITECTURE="$resolved_arch"
    export PHOENIX_BUILD_ARTIFACT_TARGET="$iso_name"
    export PHOENIX_BUILD_MODE="$BUILDER_MODE"
    export PHOENIX_BUILD_MANIFEST_PATH="$manifest"
    export PHOENIX_BUILD_SOURCE_COMMIT="$BUILD_SOURCE_COMMIT"
    export PHOENIX_BUILD_TELEMETRY_DIR="$BUILD_TELEMETRY_DIR"
    export PHOENIX_BUILD_STATE_JSON="$BUILD_TELEMETRY_DIR/build-state.json"
    export PHOENIX_BUILD_EVENT_LOG="$BUILD_TELEMETRY_DIR/build-events.jsonl"
    export PHOENIX_BUILD_HUMAN_LOG="$BUILD_TELEMETRY_DIR/build.log"
    export PHOENIX_BUILD_PHASE_TIMINGS="$BUILD_TELEMETRY_DIR/phase-timings.tsv"
    export PHOENIX_BUILD_WARNINGS_LOG="$BUILD_TELEMETRY_DIR/warnings.log"
    export PHOENIX_BUILD_FAILURES_LOG="$BUILD_TELEMETRY_DIR/failures.log"
    export PHOENIX_BUILD_SUMMARY_JSON="$BUILD_DIR/build-summary.json"
    export PHOENIX_BUILD_SUMMARY_MD="$BUILD_DIR/build-summary.md"
    export PHOENIX_BUILD_TELEMETRY_DIR_CONTAINER="/workspace/os/phoenix-os/build/telemetry/$BUILD_BUILD_ID"
    export PHOENIX_BUILD_STATE_JSON_CONTAINER="$PHOENIX_BUILD_TELEMETRY_DIR_CONTAINER/build-state.json"
    export PHOENIX_BUILD_EVENT_LOG_CONTAINER="$PHOENIX_BUILD_TELEMETRY_DIR_CONTAINER/build-events.jsonl"
    export PHOENIX_BUILD_HUMAN_LOG_CONTAINER="$PHOENIX_BUILD_TELEMETRY_DIR_CONTAINER/build.log"
    export PHOENIX_BUILD_PHASE_TIMINGS_CONTAINER="$PHOENIX_BUILD_TELEMETRY_DIR_CONTAINER/phase-timings.tsv"
    export PHOENIX_BUILD_WARNINGS_LOG_CONTAINER="$PHOENIX_BUILD_TELEMETRY_DIR_CONTAINER/warnings.log"
    export PHOENIX_BUILD_FAILURES_LOG_CONTAINER="$PHOENIX_BUILD_TELEMETRY_DIR_CONTAINER/failures.log"
    export PHOENIX_BUILD_SUMMARY_JSON_CONTAINER="/workspace/os/phoenix-os/build/build-summary.json"
    export PHOENIX_BUILD_SUMMARY_MD_CONTAINER="/workspace/os/phoenix-os/build/build-summary.md"
    phoenix_build_logger_phase_start "manifest_resolution" "Manifest resolved and build target selected."
else
    echo "[WARN] Telemetry helper not found; build will proceed without structured telemetry."
fi

# 3. Stage Edition Assets in transient live-build overlay
if [ "$BUILD_TELEMETRY_INITIALIZED" = true ]; then
    phoenix_build_logger_phase_start "overlay_staging" "Staging edition assets and branding overlays."
fi
echo "📦 Staging edition assets..."
clean_staging
mkdir -p "$STAGING_CHROOT"
mkdir -p "$PACKAGE_LIST_DIR"

if [ -n "${profile_custom_path:-}" ] && [ -d "$REPO_ROOT/$profile_custom_path" ]; then
    echo "⚙️  Detected profile overlay path: $profile_custom_path"

    # 1. Package lists
    if [ -f "$REPO_ROOT/$profile_custom_path/package-lists/base-packages.txt" ]; then
        cp "$REPO_ROOT/$profile_custom_path/package-lists/base-packages.txt" "$STAGED_PKG_SOURCE"
        sanitize_package_profile "$REPO_ROOT/$profile_custom_path/package-lists/base-packages.txt" "$STAGED_PKG_LIST" "$STAGED_PKG_BLOCKED"
        cp "$STAGED_PKG_LIST" "$STAGED_PKG_INSTALLED"
    else
        cp "$EDITION_DIR/package-profile.txt" "$STAGED_PKG_SOURCE"
        sanitize_package_profile "$EDITION_DIR/package-profile.txt" "$STAGED_PKG_LIST" "$STAGED_PKG_BLOCKED"
        cp "$STAGED_PKG_LIST" "$STAGED_PKG_INSTALLED"
    fi

    installed_pkg_count="$(wc -l < "$STAGED_PKG_INSTALLED" | tr -d '[:space:]')"
    blocked_pkg_count="$(wc -l < "$STAGED_PKG_BLOCKED" | tr -d '[:space:]')"

    if [ -f "$EDITION_DIR/colors.css" ]; then
        cp "$EDITION_DIR/colors.css" "$STAGING_CHROOT/colors.css"
    else
        echo "body { background: $background_color; color: $text_color; }" > "$STAGING_CHROOT/colors.css"
    fi
else
    cp "$EDITION_DIR/package-profile.txt" "$STAGED_PKG_SOURCE"
    sanitize_package_profile "$EDITION_DIR/package-profile.txt" "$STAGED_PKG_LIST" "$STAGED_PKG_BLOCKED"
    cp "$STAGED_PKG_LIST" "$STAGED_PKG_INSTALLED"

    installed_pkg_count="$(wc -l < "$STAGED_PKG_INSTALLED" | tr -d '[:space:]')"
    blocked_pkg_count="$(wc -l < "$STAGED_PKG_BLOCKED" | tr -d '[:space:]')"

    cp "$EDITION_DIR/colors.css" "$STAGING_CHROOT/colors.css"
fi

# Stage custom wallpaper if defined
if [ -n "$wallpaper_name" ]; then
    echo "🖼️  Staging custom wallpaper: $wallpaper_name"
    mkdir -p "$(dirname "$STAGING_WALLPAPER_PATH")"
    cp "$EDITION_DIR/$wallpaper_name" "$STAGING_WALLPAPER_PATH"
else
    echo "⚠️  WARNING: No wallpaper entry found in manifest."
fi

# Stage branding templates used by Plymouth, SDDM, and GRUB.
plymouth_theme_root="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/plymouth/themes"
sddm_theme_root="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/sddm/themes"
grub_theme_root="$STAGING_LB_CONFIG_DIR/includes.binary/boot/grub/themes"
plymouth_theme_dir="$plymouth_theme_root/phoenix"
sddm_theme_dir="$sddm_theme_root/phoenix"
grub_theme_dir="$grub_theme_root/phoenix"

mkdir -p "$plymouth_theme_root" "$sddm_theme_root" "$grub_theme_root"
rm -rf "$plymouth_theme_dir" "$sddm_theme_dir" "$grub_theme_dir"

cp -R "$REPO_ROOT/os/phoenix-os/branding/plymouth/phoenix" "$plymouth_theme_root/"
cp -R "$REPO_ROOT/os/phoenix-os/branding/sddm/phoenix" "$sddm_theme_root/"
cp -R "$REPO_ROOT/os/phoenix-os/branding/grub/phoenix" "$grub_theme_root/"

# Stage custom logo if defined (overrides Plymouth boot splash and SDDM login screen assets)
if [ -n "$logo_name" ]; then
    echo "🎨 Staging custom logo and full branding templates: $logo_name"
    logo_path="$EDITION_DIR/$logo_name"
    logo_mime="$(file -b --mime-type "$logo_path" 2>/dev/null || true)"

    case "$logo_mime" in
        image/svg+xml)
            cp "$logo_path" "$plymouth_theme_dir/phoenix-logo-boot.svg"
            cp "$logo_path" "$sddm_theme_dir/logo.svg"
            rm -f "$plymouth_theme_dir/phoenix-logo-boot.png" "$sddm_theme_dir/logo.png"
            ;;
        image/*)
            cp "$logo_path" "$plymouth_theme_dir/phoenix-logo-boot.png"
            cp "$logo_path" "$sddm_theme_dir/logo.png"
            rm -f "$plymouth_theme_dir/phoenix-logo-boot.svg" "$sddm_theme_dir/logo.svg"
            ;;
        *)
            echo "❌ Error: Unsupported logo MIME type '$logo_mime' for $logo_name"
            exit 1
            ;;
    esac
else
    echo "⚠️  WARNING: No logo entry found in manifest."
fi

splash_source_path=""
if [ -n "$splash_name" ] && [ -f "$EDITION_DIR/$splash_name" ]; then
    splash_source_path="$EDITION_DIR/$splash_name"
elif [ -n "$wallpaper_name" ] && [ -f "$EDITION_DIR/$wallpaper_name" ]; then
    splash_source_path="$EDITION_DIR/$wallpaper_name"
fi

login_background_path=""
if [ -n "$login_background_name" ] && [ -f "$EDITION_DIR/$login_background_name" ]; then
    login_background_path="$EDITION_DIR/$login_background_name"
elif [ -n "$splash_source_path" ]; then
    login_background_path="$splash_source_path"
elif [ -n "$wallpaper_name" ] && [ -f "$EDITION_DIR/$wallpaper_name" ]; then
    login_background_path="$EDITION_DIR/$wallpaper_name"
fi

# Stage per-edition splash background used by both boot (Plymouth) and login (SDDM).
if [ -f "$EDITION_DIR/plymouth_splash.png" ]; then
    cp "$EDITION_DIR/plymouth_splash.png" "$plymouth_theme_dir/splash-background.png"
elif [ -n "$splash_source_path" ]; then
    cp "$splash_source_path" "$plymouth_theme_dir/splash-background.png"
else
    make_solid_png "$plymouth_theme_dir/splash-background.png" "$background_color" 255
fi

if [ -f "$EDITION_DIR/sddm_splash.png" ]; then
    cp "$EDITION_DIR/sddm_splash.png" "$sddm_theme_dir/background.png"
elif [ -n "$login_background_path" ]; then
    cp "$login_background_path" "$sddm_theme_dir/background.png"
else
    make_solid_png "$sddm_theme_dir/background.png" "$background_color" 255
fi

read -r bg_top_r bg_top_g bg_top_b <<< "$(hex_to_rgb_floats "$background_color")"
read -r bg_bot_r bg_bot_g bg_bot_b <<< "$(hex_to_rgb_floats "$surface_color")"
progress_fill_color="$primary_color"
progress_bg_color="$(scale_hex_color "$secondary_color" 0.45)"
edition_name_qml="$(escape_qml_string "$display_name")"
edition_tagline_qml="$(escape_qml_string "$tagline")"

make_solid_png "$plymouth_theme_dir/progress-fill.png" "$progress_fill_color" 255
make_solid_png "$plymouth_theme_dir/progress-bg.png" "$progress_bg_color" 210

python3 - "$plymouth_theme_dir/phoenix.script" "$bg_top_r" "$bg_top_g" "$bg_top_b" "$bg_bot_r" "$bg_bot_g" "$bg_bot_b" <<'PY'
import sys

path = sys.argv[1]
bg_top_r, bg_top_g, bg_top_b = sys.argv[2], sys.argv[3], sys.argv[4]
bg_bot_r, bg_bot_g, bg_bot_b = sys.argv[5], sys.argv[6], sys.argv[7]
text = open(path, "r", encoding="utf-8").read()
replacements = {
    "__BG_TOP_R__": bg_top_r,
    "__BG_TOP_G__": bg_top_g,
    "__BG_TOP_B__": bg_top_b,
    "__BG_BOT_R__": bg_bot_r,
    "__BG_BOT_G__": bg_bot_g,
    "__BG_BOT_B__": bg_bot_b,
}
for key, value in replacements.items():
    text = text.replace(key, value)
open(path, "w", encoding="utf-8").write(text)
PY

python3 - "$sddm_theme_dir/Main.qml" "$edition_name_qml" "$edition_tagline_qml" "$primary_color" "$secondary_color" "$background_color" "$surface_color" "$text_color" <<'PY'
import sys

path = sys.argv[1]
edition_name, edition_tagline = sys.argv[2], sys.argv[3]
primary, secondary, background, surface, text_color = sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8]
text = open(path, "r", encoding="utf-8").read()
replacements = {
    "__EDITION_NAME__": edition_name,
    "__EDITION_TAGLINE__": edition_tagline,
    "__COLOR_PRIMARY__": primary,
    "__COLOR_SECONDARY__": secondary,
    "__COLOR_BACKGROUND__": background,
    "__COLOR_SURFACE__": surface,
    "__COLOR_TEXT__": text_color,
    "__WALLPAPER_IMAGE__": "background.png",
}
for key, value in replacements.items():
    text = text.replace(key, value)
open(path, "w", encoding="utf-8").write(text)
PY

# Stage per-edition GRUB wallpaper background.
if [ -f "$EDITION_DIR/grub_splash.png" ]; then
    cp "$EDITION_DIR/grub_splash.png" "$grub_theme_dir/background.png"
elif [ -n "$splash_source_path" ]; then
    cp "$splash_source_path" "$grub_theme_dir/background.png"
elif [ -n "$wallpaper_name" ] && [ -f "$EDITION_DIR/$wallpaper_name" ]; then
    cp "$EDITION_DIR/$wallpaper_name" "$grub_theme_dir/background.png"
fi

# Dynamically patch GRUB theme.txt with edition-specific styles and colorways
python3 - "$grub_theme_dir/theme.txt" "$display_name" "$tagline" "$primary_color" "$secondary_color" "$background_color" "$surface_color" "$text_color" <<'PY'
import sys

path = sys.argv[1]
edition_name, edition_tagline = sys.argv[2], sys.argv[3]
primary, secondary, background, surface, text_color = sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8]
text = open(path, "r", encoding="utf-8").read()
replacements = {
    "__EDITION_NAME__": edition_name,
    "__EDITION_TAGLINE__": edition_tagline,
    "__COLOR_PRIMARY__": primary,
    "__COLOR_SECONDARY__": secondary,
    "__COLOR_BACKGROUND__": background,
    "__COLOR_SURFACE__": surface,
    "__COLOR_TEXT__": text_color,
}
for key, value in replacements.items():
    text = text.replace(key, value)
open(path, "w", encoding="utf-8").write(text)
PY



cat <<EOF > "$STAGING_CHROOT/metadata.json"
{
  "id": "$EDITION_ID",
  "display_name": "$display_name",
  "tagline": "$tagline",
  "package_profile": {
    "source": "package-profile.source.txt",
    "installed": "package-profile.installed.txt",
    "blocked": "package-profile.blocked.txt",
    "installed_count": $installed_pkg_count,
    "blocked_count": $blocked_pkg_count
  },
  "theme": {
    "primary": "$primary_color",
    "secondary": "$secondary_color",
    "background": "$background_color",
    "surface": "$surface_color",
    "text": "$text_color"
  }
}
EOF

echo "✅ Assets staged in: $STAGING_CHROOT"
echo "✅ Package list staged: $STAGED_PKG_LIST"
# STAGE HOMEAURELIA ASSETS DIRECTLY
if [ -n "${profile_custom_path:-}" ] && [ -d "$REPO_ROOT/$profile_custom_path" ]; then
    echo "🎨 Staging Arc Flex profile overlays directly..."

    # Copy includes.chroot contents if any
    if [ -d "$REPO_ROOT/$profile_custom_path/includes.chroot" ]; then
        cp -R "$REPO_ROOT/$profile_custom_path/includes.chroot/"* "$STAGING_LB_CONFIG_DIR/includes.chroot/" 2>/dev/null || true
    fi

    # Copy branding assets
    if [ -d "$REPO_ROOT/$profile_custom_path/branding" ]; then
        mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/pixmaps/"
        cp -R "$REPO_ROOT/$profile_custom_path/branding/"* "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/pixmaps/" 2>/dev/null || true
    fi

    # Copy disabled services policy
    if [ -f "$REPO_ROOT/$profile_custom_path/base/disabled-services.txt" ]; then
        mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/etc/systemd/system/"
        cp "$REPO_ROOT/$profile_custom_path/base/disabled-services.txt" "$STAGING_LB_CONFIG_DIR/includes.chroot/etc/systemd/system/disabled-services.txt"
    fi

    # Copy modes
    if [ -d "$REPO_ROOT/$profile_custom_path/modes" ]; then
        mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/etc/arcwyre/modes/"
        cp -R "$REPO_ROOT/$profile_custom_path/modes/"* "$STAGING_LB_CONFIG_DIR/includes.chroot/etc/arcwyre/modes/" 2>/dev/null || true
    fi
else
    echo "🎨  Injecting HomeAurelia theme packages directly into chroot..."
    mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/plasma/look-and-feel/"
    mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/color-schemes/"
    mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/Kvantum/"
    mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/icons/"
    mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/aurorae/themes/"

    cp -R "$REPO_ROOT/HomeAurelia-Theme-Pack/05-KDE-Plasma-Theme/"* "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/plasma/look-and-feel/" 2>/dev/null || true
    cp -R "$REPO_ROOT/HomeAurelia-Theme-Pack/06-Color-Schemes/"* "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/color-schemes/" 2>/dev/null || true
    cp -R "$REPO_ROOT/HomeAurelia-Theme-Pack/07-Kvantum/"* "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/Kvantum/" 2>/dev/null || true
    mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/icons/$icon_theme/"
    cp -R "$REPO_ROOT/HomeAurelia-Theme-Pack/09-Icons/"* "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/icons/$icon_theme/" 2>/dev/null || true
    cp -R "$REPO_ROOT/HomeAurelia-Theme-Pack/10-Cursors/"* "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/icons/" 2>/dev/null || true
    cp -R "$REPO_ROOT/HomeAurelia-Theme-Pack/08-Window-Decorations/"* "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/aurorae/themes/" 2>/dev/null || true

    # OVERWRITE KDE DEFAULT WALLPAPER (Breeze / Next) TO GUARANTEE ZENITH WALLPAPER
    if [ -n "$wallpaper_name" ] && [ -f "$EDITION_DIR/$wallpaper_name" ]; then
        echo "🖼️  Hard-overriding KDE default Next wallpaper..."
        NEXT_WP_DIR="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/wallpapers/Next/contents/images"
        mkdir -p "$NEXT_WP_DIR"
        cp "$EDITION_DIR/$wallpaper_name" "$NEXT_WP_DIR/1024x768.png"
        cp "$EDITION_DIR/$wallpaper_name" "$NEXT_WP_DIR/1920x1080.png"
        cp "$EDITION_DIR/$wallpaper_name" "$NEXT_WP_DIR/2560x1440.png"
        cp "$EDITION_DIR/$wallpaper_name" "$NEXT_WP_DIR/3840x2160.png"
    fi
fi

# -----------------------------------------------------------------------------
# EXTENDED CUSTOM UI ARTWORK INJECTION
# -----------------------------------------------------------------------------
if [ -d "$EDITION_DIR/custom_art" ]; then
    echo "🎨 Processing extended custom artwork..."
    
    # 1. Start Menu (Kickoff) Icon
    if [ -f "$EDITION_DIR/custom_art/start_menu.png" ]; then
        echo "🌠 Injecting custom Start Menu icon..."
        cp "$EDITION_DIR/custom_art/start_menu.png" "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/icons/$icon_theme/places/start-here-kde.png" 2>/dev/null || true
        cp "$EDITION_DIR/custom_art/start_menu.png" "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/icons/$icon_theme/places/start-here-kde.svg" 2>/dev/null || true
        cp "$EDITION_DIR/custom_art/start_menu.png" "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/icons/scalable/places/start-here-kde.svg" 2>/dev/null || true
    fi

    # 2. Default User Avatar
    if [ -f "$EDITION_DIR/custom_art/avatar.png" ]; then
        echo "👤 Injecting custom Default Avatar..."
        mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/etc/skel"
        cp "$EDITION_DIR/custom_art/avatar.png" "$STAGING_LB_CONFIG_DIR/includes.chroot/etc/skel/.face.icon"
        mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/sddm/faces"
        cp "$EDITION_DIR/custom_art/avatar.png" "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/sddm/faces/default.face.icon"
    fi

    # 3. KSplash Loading Screen Background
    if [ -f "$EDITION_DIR/custom_art/ksplash_bg.png" ]; then
        echo "🌊 Injecting custom KSplash Background..."
        KSPLASH_DIR="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/plasma/look-and-feel/$color_scheme/contents/splash/images"
        mkdir -p "$KSPLASH_DIR"
        cp "$EDITION_DIR/custom_art/ksplash_bg.png" "$KSPLASH_DIR/background.png"
        mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/plasma/look-and-feel/HomeAurelia-Aurelia/contents/splash/images"
        cp "$EDITION_DIR/custom_art/ksplash_bg.png" "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/plasma/look-and-feel/HomeAurelia-Aurelia/contents/splash/images/background.png" 2>/dev/null || true
    fi

    # 4. Fastfetch Terminal Logo
    if [ -f "$EDITION_DIR/custom_art/fastfetch_logo.png" ]; then
        echo "🚀 Injecting custom Fastfetch Logo..."
        mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/pixmaps"
        cp "$EDITION_DIR/custom_art/fastfetch_logo.png" "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/pixmaps/phoenix-fastfetch.png"
        mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/etc/fastfetch"
        cat <<'EOF' > "$STAGING_LB_CONFIG_DIR/includes.chroot/etc/fastfetch/config.jsonc"
{
  "logo": {
    "source": "/usr/share/pixmaps/phoenix-fastfetch.png",
    "type": "kitty",
    "width": 30,
    "height": 15
  },
  "modules": [
    "title", "separator", "os", "host", "kernel", "uptime", "packages", "shell", "display", "de", "wm", "theme", "icons", "terminal", "cpu", "gpu", "memory", "disk", "battery", "poweradapter", "locale", "break", "colors"
  ]
}
EOF
    fi

    # 5. Calamares Installer Slideshow Art
    echo "📦 Injecting Calamares Installer Art..."
    CALAMARES_BRANDING="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/calamares/branding/phoenix"
    mkdir -p "$CALAMARES_BRANDING"
    if ls "$EDITION_DIR/custom_art/calamares_"*.png 1> /dev/null 2>&1; then
        cp "$EDITION_DIR/custom_art/calamares_"*.png "$CALAMARES_BRANDING/"
    fi

    # 6. About System Logo
    if [ -f "$EDITION_DIR/custom_art/about_logo.png" ]; then
        echo "🛡️  Injecting custom About System Logo..."
        mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/pixmaps"
        cp "$EDITION_DIR/custom_art/about_logo.png" "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/pixmaps/phoenix-logo.png"
        mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/kf5/infocenter"
        cp "$EDITION_DIR/custom_art/about_logo.png" "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/kf5/infocenter/logo.png" 2>/dev/null || true
    fi
fi
# -----------------------------------------------------------------------------
# CUSTOM SYSTEM ICONS INJECTION
# -----------------------------------------------------------------------------
if [ -d "$EDITION_DIR/custom_icons" ]; then
    echo "🗂️  Injecting custom variant-aware system icons..."
    for custom_icon in "$EDITION_DIR/custom_icons"/*.png; do
        [ -e "$custom_icon" ] || continue
        icon_basename="$(basename "$custom_icon")"
        icon_name_no_ext="${icon_basename%.*}"
        
        # Find all locations of this icon in the active theme
        if [ -d "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/icons/$icon_theme" ]; then
            find "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/icons/$icon_theme" -type f -name "${icon_name_no_ext}.*" | while read -r target_file; do
                target_dir="$(dirname "$target_file")"
                # Remove the generic icon (svg or png)
                rm -f "$target_file"
                # Inject the custom PNG
                cp "$custom_icon" "$target_dir/$icon_basename"
            done
        fi
        
        # Fallback injection to hicolor to guarantee visibility
        mkdir -p "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/icons/hicolor/scalable/apps"
        cp "$custom_icon" "$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/icons/hicolor/scalable/apps/$icon_basename"
    done
fi
# -----------------------------------------------------------------------------
# CUSTOM SOUNDS INJECTION
# -----------------------------------------------------------------------------
if [ -d "$EDITION_DIR/custom_sounds" ]; then
    echo "🔊 Injecting custom edition sound pack..."
    SOUNDS_DIR="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/sounds/phoenix"
    mkdir -p "$SOUNDS_DIR/stereo"
    cat <<EOF > "$SOUNDS_DIR/index.theme"
[Sound Theme]
Name=Phoenix
Directories=stereo

[stereo]
OutputProfile=stereo
EOF
    cp "$EDITION_DIR/custom_sounds"/*.ogg "$SOUNDS_DIR/stereo/" 2>/dev/null || true
    cp "$EDITION_DIR/custom_sounds"/*.wav "$SOUNDS_DIR/stereo/" 2>/dev/null || true
fi
# -----------------------------------------------------------------------------

echo "✅ Transient overlay ready: $STAGING_LB_CONFIG_DIR"

# Stage KDE User Skeleton Configurations
echo "⚙️  Staging dynamic KDE configuration skeleton..."
SKEL_CONFIG_DIR="$STAGING_LB_CONFIG_DIR/includes.chroot/etc/skel/.config"
mkdir -p "$SKEL_CONFIG_DIR"
mkdir -p "$SKEL_CONFIG_DIR/Kvantum"

cat <<EOF > "$SKEL_CONFIG_DIR/kdeglobals"
[General]
ColorScheme=$color_scheme

[Icons]
Theme=$icon_theme

[KDE]
widgetStyle=Breeze

[Sounds]
Theme=phoenix
EOF

cat <<EOF > "$SKEL_CONFIG_DIR/kcminputrc"
[Mouse]
cursorTheme=$cursor_theme
EOF

cat <<EOF > "$SKEL_CONFIG_DIR/kwinrc"
[org.kde.kdecoration2]
library=org.kde.aurorae
theme=$aurorae_theme
EOF

cat <<EOF > "$SKEL_CONFIG_DIR/Kvantum/kvantum.kvconfig"
[General]
theme=$kvantum_theme
EOF

if [ "$BUILD_TELEMETRY_INITIALIZED" = true ]; then
    phoenix_build_logger_phase_start "package_resolution" "Edition package graph resolved and staged."
fi

if [ "$DRY_RUN" = true ]; then
    echo "=== ARCWYRE FLEX DRY RUN REPORT ==="
    echo "Edition: $EDITION_ID"
    echo "Profile: ${BUILD_PROFILE:-none}"
    echo "Output ISO: $iso_name"
    echo "Target Arch: $resolved_arch"
    echo "Linux Flavour: $resolved_linux_flavour"
    echo "Bootloader: $resolved_bootloader"
    echo "Package List Source: $STAGED_PKG_SOURCE"
    echo "Active Packages Count: $installed_pkg_count"
    echo "Staging Config Directory: $STAGING_LB_CONFIG_DIR"
    if [ -n "${profile_custom_path:-}" ]; then
        echo "Overlays Source Path: $profile_custom_path"
        echo "Disabled Services Policy: $profile_custom_path/base/disabled-services.txt"
        echo "Branding Icon: $profile_custom_path/branding/arcwyre-flex.svg"
        echo "XFCE Configuration: $profile_custom_path/includes.chroot/etc/skel/.config/xfce4/panel/xfce4-panel.xml"
        echo "Target Modes Staged: $(ls -m "$REPO_ROOT/$profile_custom_path/modes" 2>/dev/null || echo 'none')"
        echo "Hooks Detected (NOT WIRED): $(ls -m "$REPO_ROOT/$profile_custom_path/hooks" 2>/dev/null || echo 'none')"
    fi
    echo "=== DRY RUN COMPLETE ==="
    exit 0
fi

if [ "$STAGE_ONLY" = true ]; then
    echo "⏹️ Stage-only mode complete. Exiting."
    exit 0
fi

# 4. Check Docker Availability
echo "🔍 Checking Docker Synthesis Engine..."
DOCKER_AVAILABLE=false
if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        DOCKER_AVAILABLE=true
        echo "✅ Docker daemon is reachable."
    else
        echo "⚠️ Docker daemon is not reachable. (Ensure Docker Desktop is running)"
    fi
else
    echo "⚠️ Docker command not found."
fi

# 5. Trigger Synthesis Engine
if [ "$DOCKER_AVAILABLE" = true ]; then
    BUILDER_SCRIPT="$REPO_ROOT/os/phoenix-os/container/build-container.sh"
    echo "🚀 Launching Synthesis Engine (OCI Builder)..."
    start_build_heartbeat
    if [ -f "$BUILDER_SCRIPT" ]; then
        BUILDER_ARGS=(
            --mode "$BUILDER_MODE"
            --arch "$resolved_arch"
            --linux-flavour "$resolved_linux_flavour"
            --bootloader "$resolved_bootloader"
            "--clean=$BUILDER_CLEAN_MODE"
        )
        if [ "$BUILDER_NO_CACHE" = true ]; then
            BUILDER_ARGS+=(--no-cache)
        fi

        if bash "$BUILDER_SCRIPT" "${BUILDER_ARGS[@]}"; then
            echo "✅ Synthesis Complete."
            BUILD_OUT_DIR="$REPO_ROOT/os/phoenix-os/build"
            FINAL_ISO="$BUILD_OUT_DIR/$iso_name"
            TARGET_PREFIX="$build_target"
            if [ -z "$TARGET_PREFIX" ]; then
                TARGET_PREFIX="live-image-$resolved_arch"
            fi

            CANDIDATE_ARTIFACTS=(
                "$BUILD_OUT_DIR/$TARGET_PREFIX.hybrid.iso"
                "$BUILD_OUT_DIR/live-image-$resolved_arch.hybrid.iso"
                "$BUILD_OUT_DIR/$TARGET_PREFIX.iso"
                "$BUILD_OUT_DIR/live-image-$resolved_arch.iso"
                "$BUILD_OUT_DIR/$TARGET_PREFIX.img"
                "$BUILD_OUT_DIR/live-image-$resolved_arch.img"
            )

            GENERATED_ISO=""
            for candidate in "${CANDIDATE_ARTIFACTS[@]}"; do
                if [ -f "$candidate" ]; then
                    GENERATED_ISO="$candidate"
                    break
                fi
            done

            if [ -z "$GENERATED_ISO" ]; then
                GENERATED_ISO="$(find "$BUILD_OUT_DIR" -maxdepth 1 -type f \( -name '*.iso' -o -name '*.img' \) -print | head -n 1 || true)"
            fi

            if [ -n "$GENERATED_ISO" ] && [ "$GENERATED_ISO" != "$FINAL_ISO" ]; then
                cp "$GENERATED_ISO" "$FINAL_ISO"
            fi

            if [ -f "$FINAL_ISO" ]; then
                echo "✨ Produced Edition artifact: $FINAL_ISO"
                echo "📥 Applying surgical boot patch for Trixie..."
                if [ -f "$REPO_ROOT/os/phoenix-os/scripts/patch_grub_trixie.sh" ]; then
                    bash "$REPO_ROOT/os/phoenix-os/scripts/patch_grub_trixie.sh" "$FINAL_ISO" || echo "⚠️  Warning: GRUB patch failed."
                else
                    echo "⚠️  Warning: patch_grub_trixie.sh not found."
                fi
            else
                echo "⚠️  Warning: Could not resolve final artifact for $EDITION_ID."
            fi
        else
            echo "❌ Synthesis Engine failed."
            # We don't auto-clean here to allow debugging, but we warn the user
            echo "💡 Staging area remains active. Run './scripts/build-edition.sh --clean-staging' to restore original lists."
            exit 1
        fi
    else
        echo "❌ Error: build-container.sh not found."
        exit 1
    fi
else
    echo "❌ Error: Cannot proceed with ISO build (Docker unavailable)."
    echo "💡 You can use --stage-only to verify the staging files manually."
    exit 1
fi
