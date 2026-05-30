#!/bin/sh
set -eu

usage() {
  cat <<'USAGE'
Usage:
  scripts/pr41a/raw-image-usb-macos.sh --disk diskN [--iso iso/outputs/bwos-home.iso]

Purpose:
  Raw-image the Phoenix ISO to a disposable external USB device.

DANGER:
  This destroys the selected disk's partition table and all data on it.
  Do NOT use this on a Ventoy drive unless you intend to erase Ventoy.

Safety gates:
  - Refuses internal disks.
  - Requires diskutil to report external physical.
  - Requires typed confirmation: WRITE /dev/diskN
USAGE
}

ISO_PATH="iso/outputs/bwos-home.iso"
DISK=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --iso)
      ISO_PATH="${2:?missing ISO path}"
      shift 2
      ;;
    --disk)
      DISK="${2:?missing disk id}"
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

if [ -z "$DISK" ]; then
  printf 'ERROR: --disk is required, for example --disk disk6\n' >&2
  usage >&2
  exit 2
fi
case "$DISK" in
  disk[0-9]*) ;;
  /dev/disk[0-9]*) DISK="$(basename "$DISK")" ;;
  *) printf 'ERROR: invalid disk id: %s\n' "$DISK" >&2; exit 2 ;;
esac

if [ ! -f "$ISO_PATH" ]; then
  printf 'ERROR: ISO not found: %s\n' "$ISO_PATH" >&2
  exit 1
fi

INFO="$(diskutil info "$DISK")"
printf '%s\n' "$INFO"
printf '%s\n' "$INFO" | grep -q 'Device Location: *External' || {
  printf 'ERROR: refusing non-external disk: /dev/%s\n' "$DISK" >&2
  exit 1
}
printf '%s\n' "$INFO" | grep -q 'Whole: *Yes' || {
  printf 'ERROR: refusing non-whole disk: /dev/%s\n' "$DISK" >&2
  exit 1
}

SRC_HASH="$(shasum -a 256 "$ISO_PATH" | awk '{print $1}')"
printf '\nISO: %s\nSHA256: %s\nTarget: /dev/%s\n' "$ISO_PATH" "$SRC_HASH" "$DISK"
printf '\nThis will erase /dev/%s. Type exactly WRITE /dev/%s to continue: ' "$DISK" "$DISK"
IFS= read -r CONFIRM
if [ "$CONFIRM" != "WRITE /dev/$DISK" ]; then
  printf 'Aborted.\n'
  exit 3
fi

diskutil unmountDisk "/dev/$DISK"
sudo dd if="$ISO_PATH" of="/dev/r$DISK" bs=1m status=progress
sync
printf 'Raw image write complete. Ejecting /dev/%s.\n' "$DISK"
diskutil eject "/dev/$DISK" || true
