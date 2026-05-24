#!/usr/bin/env bash
# Phoenix OS ISO build entrypoint for the OCI builder.
#
# Part of PR32 Incremental Build Acceleration.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="${PHOENIX_OS_ARTIFACT_DIR:-$PHOENIX_OS_DIR/build}"
LIVE_BUILD_DIR="$PHOENIX_OS_DIR/live-build"
BUILD_WORK_DIR="/home/phoenix-builder/build-workspace"
EDITION_STAGING_DIR="${PHOENIX_EDITION_STAGING_DIR:-/workspace/os/phoenix-os/cache/edition-staging/live-build-config}"
LOGGER_SCRIPT="${PHOENIX_BUILD_LOGGER_SCRIPT:-$SCRIPT_DIR/build-logger.sh}"

# Default parameters
MODE="release"
ARCH="amd64"
LINUX_FLAVOUR=""
BOOTLOADER="grub-efi"
CLEAN_MODE="stage" # Options: none, stage, all
NO_CACHE=false
TELEMETRY_ENABLED=false
BUILD_TELEMETRY_FINALIZED=false
BUILD_FINAL_ARTIFACT=""
BUILD_FINAL_SHA256=""
BUILD_FINAL_SIZE=""

# Support both --clean (legacy boolean) and --clean=mode (PR32 syntax)
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --arch)
      ARCH="$2"
      shift 2
      ;;
    --linux-flavour)
      LINUX_FLAVOUR="$2"
      shift 2
      ;;
    --bootloader)
      BOOTLOADER="$2"
      shift 2
      ;;
    --clean=*)
      CLEAN_MODE="${1#*=}"
      shift
      ;;
    --clean)
      CLEAN_MODE="all"
      shift
      ;;
    --no-cache)
      NO_CACHE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$LINUX_FLAVOUR" ]]; then
  case "$ARCH" in
    amd64) LINUX_FLAVOUR="amd64" ;;
    arm64) LINUX_FLAVOUR="arm64" ;;
    i386) LINUX_FLAVOUR="686" ;;
    *)
      echo "[FAIL] Unsupported architecture: $ARCH"
      exit 1
      ;;
  esac
fi

if [[ -n "${PHOENIX_BUILD_STATE_JSON:-}" && -f "$LOGGER_SCRIPT" ]]; then
  # shellcheck source=/dev/null
  source "$LOGGER_SCRIPT"
  phoenix_build_logger_state_sync_shell
  TELEMETRY_ENABLED=true
fi

function finalize_build_telemetry() {
  local exit_code="$1"

  if [[ "$TELEMETRY_ENABLED" != true || "$BUILD_TELEMETRY_FINALIZED" == true ]]; then
    return 0
  fi

  if [[ "$exit_code" -eq 0 ]]; then
    if [[ ! -f "${PHOENIX_BUILD_SUMMARY_JSON:-}" ]]; then
      phoenix_build_logger_finalize "completed" "" "$BUILD_FINAL_ARTIFACT" "$BUILD_FINAL_SHA256" "$BUILD_FINAL_SIZE"
    fi
  else
    if [[ -z "${PHOENIX_BUILD_FAILURE_CLASS:-}" ]]; then
      phoenix_build_logger_error "Build exited before summary generation." "${PHOENIX_BUILD_CURRENT_PHASE:-unknown}" "wrapper_script_failure"
    fi
    phoenix_build_logger_finalize "failed" "${PHOENIX_BUILD_FAILURE_CLASS:-wrapper_script_failure}" "$BUILD_FINAL_ARTIFACT" "$BUILD_FINAL_SHA256" "$BUILD_FINAL_SIZE"
  fi

  BUILD_TELEMETRY_FINALIZED=true
}

trap 'finalize_build_telemetry $?' EXIT

echo "=== Phoenix OS ISO Build Entrypoint ==="
echo "[INFO] Phoenix OS directory: $PHOENIX_OS_DIR"
echo "[INFO] Artifact directory: $BUILD_DIR"
echo "[INFO] Mode: $MODE"
echo "[INFO] Arch: $ARCH"
echo "[INFO] Linux Flavour: $LINUX_FLAVOUR"
echo "[INFO] Bootloader: $BOOTLOADER"
echo "[INFO] Clean Mode: $CLEAN_MODE"
echo "[INFO] No-Cache: $NO_CACHE"

# Check APT proxy setup
PROXY_STATUS="Not Used"
APT_PROXY_ARGS=()
if [[ -n "${PHOENIX_APT_PROXY:-}" ]]; then
  echo "[INFO] APT proxy specified: $PHOENIX_APT_PROXY"
  APT_PROXY_ARGS+=(--apt-http-proxy "$PHOENIX_APT_PROXY")
  PROXY_STATUS="$PHOENIX_APT_PROXY"
else
  echo "[INFO] No APT proxy specified. Using direct connection."
fi

if [[ "$BUILD_DIR" != "$PHOENIX_OS_DIR/build" ]]; then
  echo "[FAIL] Refusing to write artifacts outside os/phoenix-os/build."
  exit 1
fi

mkdir -p "$BUILD_DIR"

if ! command -v lb >/dev/null 2>&1; then
  echo "[FAIL] live-build command 'lb' is unavailable in the container."
  exit 1
fi

if [[ ! -d "$LIVE_BUILD_DIR/config" && ! -f "$LIVE_BUILD_DIR/auto/config" ]]; then
  echo "[FAIL] No live-build configuration exists yet under $LIVE_BUILD_DIR."
  exit 1
fi

# Clean chroot and staging directories back to ground zero if 'all' is requested
if [[ "$CLEAN_MODE" == "all" ]]; then
  echo "[INFO] Performing clean rebuild path..."
  sudo rm -rf "$BUILD_WORK_DIR"
  sudo rm -rf /workspace/os/phoenix-os/cache/*
  echo "[OK] Clean complete."
  exit 0
fi

echo "[INFO] Preparing build workspace..."
# Incremental chroot and cache preservation strategy
if [[ ! -d "$BUILD_WORK_DIR" ]]; then
  echo "[INFO] Initializing new build workspace..."
  mkdir -p "$BUILD_WORK_DIR"
  rsync -a "$LIVE_BUILD_DIR/" "$BUILD_WORK_DIR/"
else
  echo "[INFO] Reusing existing build workspace for incremental compile..."
  # Sync configs/hooks/lists but preserve existing chroot/cache
  rsync -a --exclude=chroot --exclude=cache "$LIVE_BUILD_DIR/" "$BUILD_WORK_DIR/"
fi

# 1A. Reset transient edition overlay files in the workspace to prevent stale carry-over.
rm -rf "$BUILD_WORK_DIR/config/includes.chroot/etc/bwos/edition"
rm -rf "$BUILD_WORK_DIR/config/includes.chroot/usr/share/plymouth/themes/phoenix"
rm -rf "$BUILD_WORK_DIR/config/includes.chroot/usr/share/sddm/themes/phoenix"

# 1B. Apply staged edition overlay (if present).
if [[ -d "$EDITION_STAGING_DIR" ]]; then
  echo "[INFO] Applying staged edition overlay from: $EDITION_STAGING_DIR"
  rsync -a "$EDITION_STAGING_DIR/" "$BUILD_WORK_DIR/config/"
else
  echo "[INFO] No staged edition overlay detected. Building with baseline visuals."
fi

# 2. Package List Staging Mode-Driven
echo "[INFO] Staging package list profile for mode: $MODE..."
PKG_DEST_DIR="$BUILD_WORK_DIR/config/package-lists"

# Remove default package lists to prevent duplication/override
rm -f "$PKG_DEST_DIR"/phoenix-hardened.list.chroot
rm -f "$PKG_DEST_DIR"/phoenix.list.chroot

PROFILE_DIR="$BUILD_WORK_DIR/config/package-lists/profiles"

if [[ ! -d "$PROFILE_DIR" ]]; then
  echo "[FAIL] Profile directory does not exist: $PROFILE_DIR"
  exit 1
fi

# Map profiles and support legacy values compatibly
if [[ "$MODE" == "dev-minimal" || "$MODE" == "fast" ]]; then
  cat "$PROFILE_DIR/fast.list.chroot" "$PROFILE_DIR/branding-tools.list.chroot" > "$PKG_DEST_DIR/phoenix.list.chroot"
elif [[ "$MODE" == "desktop" ]]; then
  cat "$PROFILE_DIR/fast.list.chroot" "$PROFILE_DIR/full.list.chroot" "$PROFILE_DIR/branding-tools.list.chroot" > "$PKG_DEST_DIR/phoenix.list.chroot"
elif [[ "$MODE" == "recovery" || "$MODE" == "release" || "$MODE" == "full" || "$MODE" == "release-hardened" ]]; then
  cat "$PROFILE_DIR/fast.list.chroot" "$PROFILE_DIR/full.list.chroot" "$PROFILE_DIR/recovery-tools.list.chroot" "$PROFILE_DIR/branding-tools.list.chroot" > "$PKG_DEST_DIR/phoenix.list.chroot"
else
  echo "[FAIL] Unsupported build mode: $MODE"
  exit 1
fi

if [[ "$ARCH" == "arm64" ]]; then
  if grep -qx 'memtest86+' "$PKG_DEST_DIR/phoenix.list.chroot"; then
    echo "[INFO] Removing memtest86+ from arm64 package list (package unavailable on arm64)."
    grep -vx 'memtest86+' "$PKG_DEST_DIR/phoenix.list.chroot" > "$PKG_DEST_DIR/phoenix.list.chroot.tmp"
    mv "$PKG_DEST_DIR/phoenix.list.chroot.tmp" "$PKG_DEST_DIR/phoenix.list.chroot"
  fi
fi

echo "[INFO] Staging branding assets and safety rules..."
# Ensure directories exist
PLYMOUTH_THEME_DIR="$BUILD_WORK_DIR/config/includes.chroot/usr/share/plymouth/themes/phoenix"
SDDM_THEME_DIR="$BUILD_WORK_DIR/config/includes.chroot/usr/share/sddm/themes/phoenix"
mkdir -p "$PLYMOUTH_THEME_DIR" "$SDDM_THEME_DIR"

# Copy baseline themes only for missing files so staged edition overrides are preserved.
if [ -d "$PHOENIX_OS_DIR/branding/plymouth/phoenix" ]; then
    rsync -a --ignore-existing "$PHOENIX_OS_DIR/branding/plymouth/phoenix/" "$PLYMOUTH_THEME_DIR/"
fi

if [ -d "$PHOENIX_OS_DIR/branding/sddm/phoenix" ]; then
    rsync -a --ignore-existing "$PHOENIX_OS_DIR/branding/sddm/phoenix/" "$SDDM_THEME_DIR/"
fi

# Restore package cache if present and enabled
if [[ "$NO_CACHE" == "false" ]]; then
  echo "[INFO] Checking for persistent APT package cache..."
  mkdir -p "$BUILD_WORK_DIR/cache/packages.chroot"
  if [[ -d "/workspace/os/phoenix-os/cache/packages.chroot" ]]; then
    # Copy deb files safely
    find /workspace/os/phoenix-os/cache/packages.chroot/ -maxdepth 1 -name "*.deb" -exec cp -p {} "$BUILD_WORK_DIR/cache/packages.chroot/" \; 2>/dev/null || true
    echo "[OK] Staged persistent package cache."
  fi
fi

# Sync custom prebuilt .deb packages from build/packages/ if present
PREBUILT_PKG_SRC="/workspace/os/phoenix-os/build/packages"
PREBUILT_PKG_DEST="$BUILD_WORK_DIR/config/packages.chroot"
mkdir -p "$PREBUILT_PKG_DEST"
if [[ -d "$PREBUILT_PKG_SRC" ]]; then
  mapfile -t prebuilt_debs < <(find "$PREBUILT_PKG_SRC" -maxdepth 1 -name "*.deb" -print 2>/dev/null || true)
  if [[ "${#prebuilt_debs[@]}" -gt 0 ]]; then
    echo "[INFO] Injecting ${#prebuilt_debs[@]} prebuilt custom .deb packages..."
    find "$PREBUILT_PKG_SRC/" -maxdepth 1 -name "*.deb" -exec cp -p {} "$PREBUILT_PKG_DEST/" \;
  fi
fi

echo "[INFO] Running live-build from $BUILD_WORK_DIR."
START_TIME=$(date +%s)
(
  cd "$BUILD_WORK_DIR"
  
  # Run safe cleaning operations inside the workspace
  if [[ "$CLEAN_MODE" == "stage" ]]; then
    echo "[INFO] Running default lb clean (preserves chroot/bootstrap stages)..."
    sudo lb clean
  elif [[ "$CLEAN_MODE" == "none" ]]; then
    echo "[INFO] Skipping workspace clean for hyper-fast incremental recompilation..."
  fi

  # Run lb config to ensure everything is initialized for the target architecture
  export PHOENIX_LIVE_ARCHITECTURE="$ARCH"
  export PHOENIX_LIVE_LINUX_FLAVOUR="$LINUX_FLAVOUR"
  export PHOENIX_LIVE_BOOTLOADER="$BOOTLOADER"
  lb_config_args=(
    config
    --architecture "$ARCH"
    --linux-flavours "$LINUX_FLAVOUR"
    --bootloader "$BOOTLOADER"
    --apt-options "--yes -oAcquire::Retries=8 -oAcquire::http::Timeout=30 -oAcquire::https::Timeout=30"
  )
  if [[ "${#APT_PROXY_ARGS[@]}" -gt 0 ]]; then
    lb_config_args+=("${APT_PROXY_ARGS[@]}")
  fi
  lb "${lb_config_args[@]}"

  if [[ "$TELEMETRY_ENABLED" == true ]]; then
    phoenix_build_logger_phase_start "debootstrap" "Live-build bootstrap and package assembly started."
  fi

  trace_live_build() {
    set +e
    sudo lb build 2>&1 | while IFS= read -r line; do
      printf '%s\n' "$line"
      if [[ "$TELEMETRY_ENABLED" == true ]]; then
        phoenix_build_logger_observe_line "$line"
      fi
    done
    local lb_status="${PIPESTATUS[0]}"
    set -e
    return "$lb_status"
  }

  trace_live_build
)
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

mapfile -t built_isos < <(find "$BUILD_WORK_DIR" -maxdepth 1 -type f \( -name "*.iso" -o -name "*.img" \) -print | sort)
if [[ "${#built_isos[@]}" -eq 0 ]]; then
  echo "[FAIL] live-build completed without producing an ISO."
  if [[ "$TELEMETRY_ENABLED" == true ]]; then
    phoenix_build_logger_error "live-build completed without producing an artifact." "${PHOENIX_BUILD_CURRENT_PHASE:-unknown}" "artifact_missing"
  fi
  exit 1
fi

CANONICAL_ARTIFACT_TARGET="${PHOENIX_BUILD_ARTIFACT_TARGET:-}"
PRIMARY_SOURCE_ARTIFACT="${built_isos[0]}"
if [[ -n "$CANONICAL_ARTIFACT_TARGET" ]]; then
  for candidate in "${built_isos[@]}"; do
    if [[ "$(basename "$candidate")" == "$CANONICAL_ARTIFACT_TARGET" ]]; then
      PRIMARY_SOURCE_ARTIFACT="$candidate"
      break
    fi
  done
fi

for iso in "${built_isos[@]}"; do
  ISO_NAME=$(basename "$iso")
  
  # Standard name or custom architecture name
  DEST="$BUILD_DIR/$ISO_NAME"
  cp "$iso" "$DEST"
  CANONICAL_DEST="$DEST"
  if [[ -n "$CANONICAL_ARTIFACT_TARGET" ]]; then
    CANONICAL_DEST="$BUILD_DIR/$CANONICAL_ARTIFACT_TARGET"
  fi
  
  # Also create a mode/arch friendly named link/file for easy user discovery
  ARTIFACT_EXT="${ISO_NAME##*.}"
  if [[ -z "$ARTIFACT_EXT" || "$ARTIFACT_EXT" == "$ISO_NAME" ]]; then
    ARTIFACT_EXT="iso"
  fi
  FRIENDLY_NAME="phoenix-os-${MODE}-${ARCH}.${ARTIFACT_EXT}"
  if [[ "$BUILD_DIR/$FRIENDLY_NAME" != "$DEST" ]]; then
    cp "$iso" "$BUILD_DIR/$FRIENDLY_NAME"
  fi
  if [[ "$iso" == "$PRIMARY_SOURCE_ARTIFACT" ]]; then
    if [[ "$CANONICAL_DEST" != "$DEST" ]]; then
      cp "$iso" "$CANONICAL_DEST"
    fi
    BUILD_FINAL_ARTIFACT="$CANONICAL_DEST"
  fi
  
  if [[ -f "$DEST" ]]; then
    SIZE=$(stat -c%s "$DEST" 2>/dev/null || stat -f%z "$DEST")
    SHA256=$(sha256sum "$DEST" | awk '{print $1}' 2>/dev/null || shasum -a 256 "$DEST" | awk '{print $1}')
    
    echo "[OK] Artifact: $ISO_NAME"
    echo "[OK] Friendly Name: $FRIENDLY_NAME"
    echo "[OK] Path: $DEST"
    echo "[OK] Size: $SIZE bytes"
    echo "[OK] SHA256: $SHA256"
    echo "[OK] Build Duration: ${DURATION}s"
    echo "[OK] APT Cache Proxy: $PROXY_STATUS"

    if [[ "$iso" == "$PRIMARY_SOURCE_ARTIFACT" ]]; then
      BUILD_FINAL_SHA256="$SHA256"
      BUILD_FINAL_SIZE="$SIZE"
    fi

    if [[ "$TELEMETRY_ENABLED" == true ]]; then
      phoenix_build_logger_event "artifact" "info" "artifact_registration" "Artifact copied to canonical destination." "{\"source\":\"$iso\",\"path\":\"$DEST\",\"friendly_name\":\"$FRIENDLY_NAME\"}"
      if [[ "$iso" == "$PRIMARY_SOURCE_ARTIFACT" ]]; then
        phoenix_build_logger_phase_start "checksum_generation" "Generating canonical artifact checksum."
        phoenix_build_logger_event "artifact" "info" "checksum_generation" "Artifact checksum generated." "{\"path\":\"$CANONICAL_DEST\",\"sha256\":\"$SHA256\",\"size_bytes\":$SIZE}"
        phoenix_build_logger_phase_start "artifact_registration" "Artifact registered in build output."
        phoenix_build_logger_event "artifact" "info" "artifact_registration" "Artifact registered and ready for registry update." "{\"path\":\"$CANONICAL_DEST\"}"
      fi
    fi
    
    # Save back new packages to persistent cache if caching is active
    if [[ "$NO_CACHE" == "false" ]]; then
      echo "[INFO] Preserving downloaded packages to persistent APT cache..."
      mkdir -p "/workspace/os/phoenix-os/cache/packages.chroot"
      find "$BUILD_WORK_DIR/cache/packages.chroot/" -maxdepth 1 -name "*.deb" -exec cp -p {} "/workspace/os/phoenix-os/cache/packages.chroot/" \; 2>/dev/null || true
    fi
    
    # Non-destructive validation
    echo "[INFO] Validating artifact structure..."
    file "$DEST"
    if command -v xorriso >/dev/null 2>&1; then
      xorriso -indev "$DEST" -report_el_torito plain -report_system_area plain
    fi
  else
    echo "[FAIL] Failed to copy artifact to $DEST"
    exit 1
  fi
done

if [[ "$TELEMETRY_ENABLED" == true ]]; then
  phoenix_build_logger_phase_start "cleanup" "Final cleanup and telemetry summary generation."
  phoenix_build_logger_finalize "completed" "" "$BUILD_FINAL_ARTIFACT" "$BUILD_FINAL_SHA256" "$BUILD_FINAL_SIZE"
  BUILD_TELEMETRY_FINALIZED=true
fi

echo "=== Phoenix OS Artifact Build Entrypoint Complete ==="
