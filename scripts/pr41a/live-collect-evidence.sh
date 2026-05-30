#!/bin/sh
set -eu

OUT="${1:-/tmp/pr41a-live-evidence}"
mkdir -p "$OUT"

run_capture() {
  name="$1"
  shift
  printf 'Collecting %s...\n' "$name"
  ( "$@" ) > "$OUT/$name" 2>&1 || true
}

run_capture uname-a.txt uname -a
run_capture proc-cmdline.txt cat /proc/cmdline
run_capture lsblk.txt lsblk
run_capture journalctl-tail-200.txt sh -c 'journalctl -b | tail -200'

APP_RESULTS="$OUT/app-launch-results.txt"
: > "$APP_RESULTS"
for app in firefox-esr firefox dolphin konsole; do
  if command -v "$app" >/dev/null 2>&1; then
    printf '%s: PRESENT\n' "$app" >> "$APP_RESULTS"
  else
    printf '%s: MISSING\n' "$app" >> "$APP_RESULTS"
  fi
done

cat > "$OUT/README.txt" <<README
PR41A live evidence collected at: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Files:
- uname-a.txt
- proc-cmdline.txt
- lsblk.txt
- journalctl-tail-200.txt
- app-launch-results.txt

Manual app validation still required:
- Open Firefox and confirm it launches.
- Open Dolphin and confirm it launches.
- Open Konsole and confirm it launches.
README

printf 'Evidence bundle written to %s\n' "$OUT"
