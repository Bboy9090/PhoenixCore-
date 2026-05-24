#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

MANIFEST="iso/outputs/manifest.json"
BOOT_MATRIX="iso/outputs/vm-boot-matrix.json"

EXPECTED_FILES=(
  "bwos-home.iso"
  "bwos-aurelia.iso"
  "bwos-arcwyre.iso"
  "bwos-thunder-god.iso"
)

errors=0
warnings=0
boot_matrix_tsv=""

error() {
  echo "ERROR: $*" >&2
  errors=$((errors + 1))
}

warn() {
  echo "WARN: $*" >&2
  warnings=$((warnings + 1))
}

info() {
  echo "INFO: $*"
}

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    echo "No SHA256 tool found: need shasum or sha256sum" >&2
    exit 1
  fi
}

edition_is_archived() {
  local manifest="$1"

  [ -f "$manifest" ] || return 1
  if awk '
    /^[[:space:]]*archived:[[:space:]]*true([[:space:]]|$)/ { found = 1 }
    END { exit found ? 0 : 1 }
  ' "$manifest"; then
    return 0
  fi
  return 1
}

all_artifact_paths() {
  for dir in "iso/outputs" "os/phoenix-os/build"; do
    if [ -d "$dir" ]; then
      find "$dir" -maxdepth 1 -type f \( -name '*.iso' -o -name '*.img' \) -print
    fi
  done | sort
}

if [ ! -f "$MANIFEST" ]; then
  error "Missing generated registry: $MANIFEST"
else
  info "Using registry: $MANIFEST"
fi

if [ -f "$BOOT_MATRIX" ]; then
  boot_matrix_tsv="$(mktemp)"
  python3 - "$BOOT_MATRIX" > "$boot_matrix_tsv" <<'PY'
import json
import sys

def txt(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)

data = json.load(open(sys.argv[1], encoding="utf-8"))
for item in data.get("artifacts", []):
    print("\t".join([
        txt(item.get("edition_id")),
        txt(item.get("sha256")),
        txt(item.get("classification")),
        txt(item.get("boot_menu_reached")),
        txt(item.get("kernel_reached")),
        txt(item.get("initramfs_reached")),
        txt(item.get("display_manager_reached")),
        txt(item.get("desktop_reached")),
        txt(item.get("clean_shutdown_verified")),
        txt(item.get("failure_point")),
    ]))
PY
else
  warn "Missing VM boot matrix data file: $BOOT_MATRIX"
fi

cleanup_boot_matrix() {
  if [ -n "${boot_matrix_tsv:-}" ] && [ -f "$boot_matrix_tsv" ]; then
    rm -f "$boot_matrix_tsv"
  fi
}
trap cleanup_boot_matrix EXIT

boot_matrix_lookup() {
  local edition="$1"
  local sha="$2"
  local field="$3"

  if [ -z "$boot_matrix_tsv" ] || [ ! -f "$boot_matrix_tsv" ]; then
    return 0
  fi

  awk -F'\t' -v edition="$edition" -v sha="$sha" -v field="$field" '
    $1 == edition && $2 == sha { print $field; exit }
  ' "$boot_matrix_tsv"
}

for filename in "${EXPECTED_FILES[@]}"; do
  count="$(find iso/outputs -maxdepth 1 -type f -name "$filename" -print 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$count" -ne 1 ]; then
    error "Expected exactly one current artifact in iso/outputs for $filename, found $count"
  else
    info "Current artifact present: iso/outputs/$filename"
    case "$filename" in
      bwos-home.iso) edition_id="home" ;;
      bwos-aurelia.iso) edition_id="blue-phoenix" ;;
      bwos-arcwyre.iso) edition_id="arcwyre" ;;
      bwos-thunder-god.iso) edition_id="thunder-god" ;;
      *) edition_id="unknown" ;;
    esac
    sha="$(sha256_file "iso/outputs/$filename")"
    classification="$(boot_matrix_lookup "$edition_id" "$sha" 3)"
    boot_menu="$(boot_matrix_lookup "$edition_id" "$sha" 4)"
    kernel="$(boot_matrix_lookup "$edition_id" "$sha" 5)"
    initramfs="$(boot_matrix_lookup "$edition_id" "$sha" 6)"
    display="$(boot_matrix_lookup "$edition_id" "$sha" 7)"
    desktop="$(boot_matrix_lookup "$edition_id" "$sha" 8)"
    shutdown="$(boot_matrix_lookup "$edition_id" "$sha" 9)"

    if [ -z "$classification" ]; then
      error "Missing VM boot status for $filename"
    else
      info "Boot classification for $filename: $classification"
      case "$classification" in
        NOT_TESTED|BLOCKED_BY_VM_TOOLING)
          warn "Boot matrix for $filename is not yet a boot pass/fail record"
          ;;
      esac
    fi

    if [ -n "$classification" ] && [ "$classification" != "NOT_TESTED" ] && [ "$classification" != "BLOCKED_BY_VM_TOOLING" ]; then
      if [ -z "$boot_menu" ] || [ -z "$kernel" ] || [ -z "$initramfs" ] || [ -z "$display" ] || [ -z "$desktop" ] || [ -z "$shutdown" ]; then
        warn "Incomplete boot stage booleans for $filename"
      fi
    fi
  fi
done

tmp_checksums="$(mktemp)"
trap 'rm -f "$tmp_checksums"' EXIT

while IFS= read -r path; do
  [ -n "$path" ] || continue
  sha="$(sha256_file "$path")"
  filename="$(basename "$path")"
  case "$filename" in
    bwos-home.iso) edition_id="home" ;;
    bwos-aurelia.iso) edition_id="blue-phoenix" ;;
    bwos-arcwyre.iso) edition_id="arcwyre" ;;
    bwos-thunder-god.iso) edition_id="thunder-god" ;;
    bwos-home-legacy-i386.img) edition_id="home-legacy-i386" ;;
    bwos-home-arm64.iso) edition_id="home-arm64" ;;
    bwos-thunder-god-arm64.iso) edition_id="thunder-god-arm64" ;;
    *) edition_id="unknown" ;;
  esac

  if [ "$edition_id" = "unknown" ]; then
    warn "Legacy artifact preserved outside active registry: $path"
    continue
  fi

  manifest_path="editions/$edition_id/edition.yaml"
  if edition_is_archived "$manifest_path"; then
    warn "Archived artifact preserved outside active registry: $path"
    continue
  fi

  printf '%s %s\n' "$sha" "$path" >> "$tmp_checksums"

  if [ -f "$MANIFEST" ]; then
    if ! grep -Fq "\"path\": \"$path\"" "$MANIFEST"; then
      error "Missing metadata for $path"
    fi
    if ! grep -Fq "\"sha256\": \"$sha\"" "$MANIFEST"; then
      error "Checksum mismatch or missing checksum metadata for $path"
    fi
  fi

  case "$path" in
    iso/outputs/*) ;;
    *) warn "Artifact outside registry output directory: $path" ;;
  esac
done < <(all_artifact_paths)

while IFS= read -r duplicate_sha; do
  [ -n "$duplicate_sha" ] || continue
  paths="$(awk -v sha="$duplicate_sha" '$1 == sha { $1=""; sub(/^ /, ""); print }' "$tmp_checksums" | paste -sd ';' -)"
  warn "Duplicate artifact checksum $duplicate_sha: $paths"
done < <(awk '{print $1}' "$tmp_checksums" | sort | uniq -d)

if [ -f "$MANIFEST" ]; then
  if grep -Fq '"edition_id": "unknown"' "$MANIFEST"; then
    warn "Registry contains artifact(s) with unknown edition id"
  fi
  if grep -Fq '"vm_boot_matrix"' "$MANIFEST"; then
    info "VM boot matrix fields present in registry"
  else
    warn "VM boot matrix fields are not present in the registry yet"
  fi
  if grep -Fq '"vm": "vm_boot_untested"' "$MANIFEST"; then
    warn "VM boot status is untested for one or more artifacts"
  fi
  if grep -Fq '"usb": "usb_boot_untested"' "$MANIFEST"; then
    warn "USB boot status is untested for one or more artifacts"
  fi
  if grep -Fq '"app_validation_status": "not_run"' "$MANIFEST"; then
    warn "App validation has not been recorded for one or more artifacts"
  fi
  if grep -Fq '"safety_validation_status": "not_run"' "$MANIFEST"; then
    warn "Safety validation has not been recorded for one or more artifacts"
  fi
  if grep -Fq '"release_readiness": "release_blocked"' "$MANIFEST"; then
    warn "One or more artifacts are release-blocked until validation is recorded"
  fi
fi

echo
echo "Artifact validation summary: $errors error(s), $warnings warning(s)"

if [ "$errors" -gt 0 ]; then
  exit 1
fi
