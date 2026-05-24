#!/usr/bin/env bash
# Install/update Ventoy on a target disk and sync Phoenix boot artifacts.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISO_DIR="$REPO_ROOT/iso/outputs"
VENTOY_DIR="/Users/bj90-m1/ventoy-source/VentoyMac"
VENTOY_BIN="$VENTOY_DIR/ventoy"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/ventoy-sync-isos.sh --disk /dev/diskX [--mode install|update] [--skip-ventoy]

Options:
  --disk         Target removable disk (example: /dev/disk10)
  --mode         Ventoy mode: install (default) or update
  --skip-ventoy  Do not run Ventoy install/update; only copy boot artifacts to partition 1

Notes:
  - install mode erases target disk content.
  - This script copies all *.iso and *.img files from iso/outputs to the Ventoy data partition.
EOF
}

TARGET_DISK=""
MODE="install"
SKIP_VENTOY="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --disk)
      TARGET_DISK="${2:-}"
      shift 2
      ;;
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --skip-ventoy)
      SKIP_VENTOY="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$TARGET_DISK" ]]; then
  echo "Missing required --disk argument." >&2
  usage
  exit 1
fi

if [[ "$MODE" != "install" && "$MODE" != "update" ]]; then
  echo "Invalid --mode value: $MODE (expected install or update)." >&2
  exit 1
fi

if [[ ! -d "$ISO_DIR" ]]; then
  echo "ISO output directory not found: $ISO_DIR" >&2
  exit 1
fi

shopt -s nullglob
artifacts=("$ISO_DIR"/*.iso "$ISO_DIR"/*.img)
shopt -u nullglob
if [[ ${#artifacts[@]} -eq 0 ]]; then
  echo "No boot artifacts found in $ISO_DIR" >&2
  exit 1
fi

if ! diskutil info "$TARGET_DISK" >/dev/null 2>&1; then
  echo "Disk not found: $TARGET_DISK" >&2
  exit 1
fi

if [[ "$SKIP_VENTOY" == "false" ]]; then
  if [[ ! -x "$VENTOY_BIN" ]]; then
    echo "Ventoy binary not found or not executable: $VENTOY_BIN" >&2
    exit 1
  fi

  echo "Running Ventoy $MODE on $TARGET_DISK ..."
  # VentoyMac handles privilege escalation via native auth dialog.
  "$VENTOY_BIN" "$MODE" "$TARGET_DISK"
fi

PART1="${TARGET_DISK}s1"
echo "Mounting Ventoy data partition: $PART1"
diskutil mount "$PART1" >/dev/null 2>&1 || true

MOUNT_POINT="$(diskutil info "$PART1" | awk -F': *' '/Mount Point/ {print $2}')"
if [[ -z "$MOUNT_POINT" || "$MOUNT_POINT" == "Not applicable (not mounted)" ]]; then
  echo "Failed to mount Ventoy data partition on $PART1" >&2
  exit 1
fi

echo "Ventoy data partition mounted at: $MOUNT_POINT"
for artifact in "${artifacts[@]}"; do
  echo "Copying $(basename "$artifact") ..."
  cp -f "$artifact" "$MOUNT_POINT/"
done

sync
echo "Done. Synced ${#artifacts[@]} boot artifacts to $MOUNT_POINT"
echo "You can now eject with: diskutil eject $TARGET_DISK"
