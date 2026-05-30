#!/bin/sh
set -eu

usage() {
  cat <<'USAGE'
Usage:
  scripts/pr41a/ventoy-copy-iso-macos.sh --volume /Volumes/Ventoy [--iso iso/outputs/bwos-home.iso]

Purpose:
  Copy the Phoenix ISO onto an existing Ventoy partition without destroying the Ventoy drive.

Safety:
  - This does NOT raw-image the disk.
  - This writes only one ISO file to the mounted Ventoy volume.
  - Refuses to run if the target is not under /Volumes.
  - Verifies copied SHA256 after copy.

If macOS mounted the Ventoy NTFS volume read-only, this script will fail. In that case use a Linux machine, Windows, or an NTFS write driver.
USAGE
}

ISO_PATH="iso/outputs/bwos-home.iso"
VOLUME=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --iso)
      ISO_PATH="${2:?missing ISO path}"
      shift 2
      ;;
    --volume)
      VOLUME="${2:?missing volume path}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'ERROR: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$VOLUME" ]; then
  printf 'ERROR: --volume is required, for example --volume /Volumes/Ventoy\n' >&2
  usage >&2
  exit 2
fi

case "$VOLUME" in
  /Volumes/*) ;;
  *)
    printf 'ERROR: refusing target outside /Volumes: %s\n' "$VOLUME" >&2
    exit 2
    ;;
esac

if [ ! -f "$ISO_PATH" ]; then
  printf 'ERROR: ISO not found: %s\n' "$ISO_PATH" >&2
  exit 1
fi
if [ ! -d "$VOLUME" ]; then
  printf 'ERROR: volume not mounted: %s\n' "$VOLUME" >&2
  exit 1
fi
if [ ! -w "$VOLUME" ]; then
  printf 'ERROR: volume is not writable: %s\n' "$VOLUME" >&2
  printf 'macOS often mounts NTFS read-only. Use Linux/Windows or an NTFS write driver.\n' >&2
  exit 1
fi

ISO_BASENAME="$(basename "$ISO_PATH")"
DEST="$VOLUME/$ISO_BASENAME"
SRC_HASH="$(shasum -a 256 "$ISO_PATH" | awk '{print $1}')"

printf 'Source ISO: %s\n' "$ISO_PATH"
printf 'Source SHA256: %s\n' "$SRC_HASH"
printf 'Target Ventoy volume: %s\n' "$VOLUME"
printf 'Destination: %s\n' "$DEST"
printf '\nType exactly COPY_TO_VENTOY to copy the ISO: '
IFS= read -r CONFIRM
if [ "$CONFIRM" != "COPY_TO_VENTOY" ]; then
  printf 'Aborted.\n'
  exit 3
fi

cp -f "$ISO_PATH" "$DEST"
sync
DST_HASH="$(shasum -a 256 "$DEST" | awk '{print $1}')"
printf 'Copied SHA256: %s\n' "$DST_HASH"
if [ "$SRC_HASH" != "$DST_HASH" ]; then
  printf 'ERROR: copied hash mismatch. Do not boot this copy.\n' >&2
  exit 1
fi
printf 'Copy verified. Boot this ISO from the Ventoy menu: %s\n' "$ISO_BASENAME"
