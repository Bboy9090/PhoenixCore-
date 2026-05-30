#!/bin/sh
set -eu

ISO_PATH="${1:-iso/outputs/bwos-home.iso}"

printf '== PR41A macOS host preflight ==\n'
printf 'Working directory: %s\n' "$(pwd)"
printf '\n== ISO ==\n'
if [ ! -f "$ISO_PATH" ]; then
  printf 'ERROR: ISO not found: %s\n' "$ISO_PATH" >&2
  exit 1
fi
ls -lh "$ISO_PATH"
shasum -a 256 "$ISO_PATH"

printf '\n== External physical disks ==\n'
diskutil list external physical || true

printf '\n== All disks ==\n'
diskutil list

printf '\n== USB devices ==\n'
system_profiler SPUSBDataType || true

printf '\nNext step for Ventoy: run scripts/pr41a/ventoy-copy-iso-macos.sh after confirming the Ventoy volume mount path.\n'
