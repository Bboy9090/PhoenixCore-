#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: iso/scripts/scan-artifacts.sh [--json|--markdown] [--root PATH]

Scans BWOS / Blue Phoenix boot artifacts without modifying them.

Outputs:
  --json      Machine-readable artifact registry JSON (default)
  --markdown  Markdown artifact table
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FORMAT="json"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --json)
      FORMAT="json"
      shift
      ;;
    --markdown)
      FORMAT="markdown"
      shift
      ;;
    --root)
      ROOT="$(cd "$2" && pwd)"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

cd "$ROOT"

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/	/\\t/g'
}

json_string() {
  printf '"%s"' "$(json_escape "$1")"
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

size_file() {
  stat -f '%z' "$1" 2>/dev/null || stat -c '%s' "$1"
}

mtime_file() {
  stat -f '%Sm' -t '%Y-%m-%dT%H:%M:%S%z' "$1" 2>/dev/null || stat -c '%y' "$1"
}

yaml_value() {
  local file="$1"
  local key="$2"

  [ -f "$file" ] || return 0
  awk -v key="$key" '
    $0 ~ "^[[:space:]]*" key ":" {
      sub("^[[:space:]]*" key ":[[:space:]]*", "")
      sub(/[[:space:]]+#.*$/, "")
      gsub(/^"/, "")
      gsub(/"$/, "")
      gsub(/^\047/, "")
      gsub(/\047$/, "")
      print
      exit
    }
  ' "$file"
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

edition_from_filename() {
  case "$1" in
    bwos-home.iso) echo "home" ;;
    bwos-aurelia.iso) echo "blue-phoenix" ;;
    bwos-arcwyre.iso) echo "arcwyre" ;;
    bwos-thunder-god.iso) echo "thunder-god" ;;
    bwos-thunder-god-arm64.iso) echo "thunder-god-arm64" ;;
    bwos-home-arm64.iso) echo "home-arm64" ;;
    bwos-home-legacy-i386.iso) echo "home-legacy-i386" ;;
    bwos-home-legacy-i386.img) echo "home-legacy-i386" ;;
    *) echo "unknown" ;;
  esac
}

artifact_format_from_filename() {
  case "$1" in
    *.iso) echo "iso" ;;
    *.img) echo "dd-image" ;;
    *) echo "unknown" ;;
  esac
}

architecture_from_manifest() {
  local manifest="$1"
  local arch target

  arch="$(yaml_value "$manifest" "architecture")"
  if [ -n "$arch" ]; then
    echo "$arch"
    return
  fi

  target="$(yaml_value "$manifest" "target")"
  case "$target" in
    *amd64*) echo "amd64" ;;
    *arm64*) echo "arm64" ;;
    *i386*) echo "i386" ;;
    *) echo "unknown" ;;
  esac
}

build_mode_from_manifest() {
  local manifest="$1"
  local target

  target="$(yaml_value "$manifest" "target")"
  if [ -n "$target" ]; then
    echo "$target"
  else
    echo "unknown"
  fi
}

preflight_status() {
  local filename="$1"
  local preflight="iso/outputs/BOOT-PREFLIGHT-2026-05-19-v2.txt"

  if [ ! -f "$preflight" ]; then
    echo "not_run"
    return
  fi

  if awk -v file="[$filename]" '
    $0 == file { in_file = 1; next }
    /^\[/ { in_file = 0 }
    in_file && /RESULT[[:space:]]+PASS/ { found = 1 }
    END { exit found ? 0 : 1 }
  ' "$preflight"; then
    echo "boot_structure_preflight_pass"
  else
    echo "not_run"
  fi
}

artifact_paths=()
for dir in "iso/outputs" "os/phoenix-os/build"; do
  if [ -d "$dir" ]; then
    while IFS= read -r path; do
      artifact_paths+=("$path")
    done < <(find "$dir" -maxdepth 1 -type f \( -name '*.iso' -o -name '*.img' \) -print | sort)
  fi
done

source_commit="unknown"
source_commit_source="unavailable"
source_tree_dirty="null"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  source_commit="$(git rev-parse HEAD)"
  source_commit_source="git_head_at_scan_not_embedded"
  if [ -n "$(git status --porcelain)" ]; then
    source_tree_dirty="true"
  else
    source_tree_dirty="false"
  fi
fi

generated_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

artifact_path=()
artifact_filename=()
artifact_size=()
artifact_sha=()
artifact_mtime=()
artifact_edition=()
artifact_display=()
artifact_manifest=()
artifact_manifest_hash=()
artifact_arch=()
artifact_build_mode=()
artifact_formats=()
artifact_preflight=()
artifact_vm_tool=()
artifact_vm_efi=()
artifact_vm_secure_boot=()
artifact_vm_ram=()
artifact_vm_cpu=()
artifact_vm_disk=()
artifact_vm_boot_menu=()
artifact_vm_kernel=()
artifact_vm_initramfs=()
artifact_vm_display=()
artifact_vm_desktop=()
artifact_vm_desktop_marker=()
artifact_vm_shutdown_marker=()
artifact_vm_session_class=()
artifact_vm_session_probe_class=()
artifact_vm_session_attempt_count=()
artifact_vm_session_desktop_marker_count=()
artifact_vm_session_shutdown_marker_count=()
artifact_vm_session_repeatability_risk=()
artifact_vm_shutdown=()
artifact_vm_classification=()
artifact_vm_failure_point=()
artifact_vm_boot_log=()
artifact_vm_serial_log=()
artifact_vm_artifact_path=()
artifact_vm_artifact_format=()
artifact_vm_artifact_size=()
artifact_vm_build_summary_path=()
artifact_vm_build_status=()
artifact_vm_telemetry_status=()

vm_tool_version() {
  local tool="$1"
  if command -v "$tool" >/dev/null 2>&1; then
    "$tool" --version 2>/dev/null | head -n 1
  else
    echo ""
  fi
}

vm_tool_available() {
  local tool="$1"
  if command -v "$tool" >/dev/null 2>&1; then
    echo "true"
  else
    echo "false"
  fi
}

vm_tool_audit_json() {
  local vbox_available utm_available qemu_available
  local vbox_version utm_version qemu_version

  vbox_available="$(vm_tool_available VBoxManage)"
  if [ "$vbox_available" = "false" ]; then
    vbox_available="$(vm_tool_available virtualbox)"
  fi
  vbox_version="$(vm_tool_version VBoxManage)"
  if [ -z "$vbox_version" ]; then
    vbox_version="$(vm_tool_version virtualbox)"
  fi

  if [ -d /Applications/UTM.app ]; then
    utm_available="true"
    utm_version="$(defaults read /Applications/UTM.app/Contents/Info CFBundleShortVersionString 2>/dev/null || true)"
  else
    utm_available="false"
    utm_version=""
  fi

  qemu_available="false"
  qemu_version=""
  for tool in qemu-system-x86_64 qemu-system-i386 qemu-system-aarch64; do
    if command -v "$tool" >/dev/null 2>&1; then
      qemu_available="true"
      qemu_version="$(vm_tool_version "$tool")"
      break
    fi
  done

  cat <<EOF
  "vm_tool_audit": {
    "virtualbox": {
      "available": $vbox_available,
      "version": "$(json_escape "$vbox_version")",
      "limitations": "Apple Silicon builds are not the primary path for x86_64/i386 boot automation; use for arm64 guests only when explicitly needed."
    },
    "utm": {
      "available": $utm_available,
      "version": "$(json_escape "$utm_version")",
      "limitations": "No native CLI automation is wired into this repository; use manually if needed."
    },
    "qemu": {
      "available": $qemu_available,
      "version": "$(json_escape "$qemu_version")",
      "limitations": "x86 guests run under TCG on Apple Silicon and are slow; arm64 is supported only when the matching firmware is present."
    }
  },
EOF
}

boot_matrix_file="iso/outputs/vm-boot-matrix.json"
boot_matrix_tsv=""
if [ -f "$boot_matrix_file" ]; then
  boot_matrix_tsv="$(mktemp)"
  python3 - "$boot_matrix_file" > "$boot_matrix_tsv" <<'PY'
import json
import sys

path = sys.argv[1]
data = json.load(open(path, encoding="utf-8"))
def txt(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)

for item in data.get("artifacts", []):
    print("\t".join([
        txt(item.get("edition_id")),
        txt(item.get("sha256")),
        txt(item.get("classification")),
        txt(item.get("path")),
        txt(item.get("artifact_format")),
        txt(item.get("size_bytes")),
        txt(item.get("vm_tool")),
        txt(item.get("efi_enabled")),
        txt(item.get("secure_boot_state")),
        txt(item.get("ram_mb")),
        txt(item.get("cpu_cores")),
        txt(item.get("disk_attached")),
        txt(item.get("boot_menu_reached")),
        txt(item.get("kernel_reached")),
        txt(item.get("initramfs_reached")),
        txt(item.get("display_manager_reached")),
        txt(item.get("desktop_reached")),
        txt(item.get("desktop_marker_reached")),
        txt(item.get("shutdown_marker_reached")),
        txt(item.get("session_determinism_class")),
        txt(item.get("session_attempt_count")),
        txt(item.get("session_desktop_marker_count")),
        txt(item.get("session_shutdown_marker_count")),
        txt(item.get("session_repeatability_risk")),
        txt(item.get("clean_shutdown_verified")),
        txt(item.get("failure_point")),
        txt(item.get("boot_log_path")),
        txt(item.get("serial_log_path")),
        txt(item.get("build_summary_path")),
        txt(item.get("build_status")),
        txt(item.get("telemetry_status")),
        txt(item.get("session_probe_classification")),
    ]))
PY
fi

cleanup_tmp() {
  if [ -n "${boot_matrix_tsv:-}" ] && [ -f "$boot_matrix_tsv" ]; then
    rm -f "$boot_matrix_tsv"
  fi
}
trap cleanup_tmp EXIT

boot_matrix_lookup() {
  local edition="$1"
  local sha="$2"
  local field="$3"

  if [ -z "$boot_matrix_tsv" ] || [ ! -f "$boot_matrix_tsv" ]; then
    return 0
  fi

  awk -F'\t' -v edition="$edition" -v sha="$sha" -v field="$field" '
    $2 == sha { print $field; found = 1; exit }
    $1 == edition { if (!found && edition_match == "") edition_match = $field }
    END { if (!found && edition_match != "") print edition_match }
  ' "$boot_matrix_tsv"
}

for path in "${artifact_paths[@]}"; do
  filename="$(basename "$path")"
  edition_id="$(edition_from_filename "$filename")"
  manifest=""
  display_name="Unknown edition"
  manifest_hash=""
  arch="unknown"
  build_mode="unknown"
  current_format="$(artifact_format_from_filename "$filename")"

  if [ "$edition_id" = "unknown" ]; then
    continue
  fi

  manifest="editions/$edition_id/edition.yaml"
  if [ ! -f "$manifest" ] || edition_is_archived "$manifest"; then
    continue
  fi

  display_name="$(yaml_value "$manifest" "display_name")"
  [ -n "$display_name" ] || display_name="$edition_id"
  manifest_hash="$(sha256_file "$manifest")"
  arch="$(architecture_from_manifest "$manifest")"
  build_mode="$(build_mode_from_manifest "$manifest")"

  artifact_path+=("$path")
  artifact_filename+=("$filename")
  current_size="$(size_file "$path")"
  current_sha="$(sha256_file "$path")"
  artifact_size+=("$current_size")
  artifact_sha+=("$current_sha")
  artifact_mtime+=("$(mtime_file "$path")")
  artifact_edition+=("$edition_id")
  artifact_display+=("$display_name")
  artifact_manifest+=("$manifest")
  artifact_manifest_hash+=("$manifest_hash")
  artifact_arch+=("$arch")
  artifact_build_mode+=("$build_mode")
  artifact_formats+=("$current_format")
  artifact_preflight+=("$(preflight_status "$filename")")

  vm_classification="$(boot_matrix_lookup "$edition_id" "$current_sha" 3)"
  vm_path="$(boot_matrix_lookup "$edition_id" "$current_sha" 4)"
  vm_format="$(boot_matrix_lookup "$edition_id" "$current_sha" 5)"
  vm_size="$(boot_matrix_lookup "$edition_id" "$current_sha" 6)"
  vm_tool="$(boot_matrix_lookup "$edition_id" "$current_sha" 7)"
  vm_efi="$(boot_matrix_lookup "$edition_id" "$current_sha" 8)"
  vm_secure_boot="$(boot_matrix_lookup "$edition_id" "$current_sha" 9)"
  vm_ram="$(boot_matrix_lookup "$edition_id" "$current_sha" 10)"
  vm_cpu="$(boot_matrix_lookup "$edition_id" "$current_sha" 11)"
  vm_disk="$(boot_matrix_lookup "$edition_id" "$current_sha" 12)"
  vm_menu="$(boot_matrix_lookup "$edition_id" "$current_sha" 13)"
  vm_kernel="$(boot_matrix_lookup "$edition_id" "$current_sha" 14)"
  vm_initramfs="$(boot_matrix_lookup "$edition_id" "$current_sha" 15)"
  vm_display="$(boot_matrix_lookup "$edition_id" "$current_sha" 16)"
  vm_desktop="$(boot_matrix_lookup "$edition_id" "$current_sha" 17)"
  vm_desktop_marker="$(boot_matrix_lookup "$edition_id" "$current_sha" 18)"
  vm_shutdown_marker="$(boot_matrix_lookup "$edition_id" "$current_sha" 19)"
  vm_session_class="$(boot_matrix_lookup "$edition_id" "$current_sha" 20)"
  vm_session_attempt_count="$(boot_matrix_lookup "$edition_id" "$current_sha" 21)"
  vm_session_desktop_marker_count="$(boot_matrix_lookup "$edition_id" "$current_sha" 22)"
  vm_session_shutdown_marker_count="$(boot_matrix_lookup "$edition_id" "$current_sha" 23)"
  vm_session_repeatability_risk="$(boot_matrix_lookup "$edition_id" "$current_sha" 24)"
  vm_shutdown="$(boot_matrix_lookup "$edition_id" "$current_sha" 25)"
  vm_failure_point="$(boot_matrix_lookup "$edition_id" "$current_sha" 26)"
  vm_boot_log="$(boot_matrix_lookup "$edition_id" "$current_sha" 27)"
  vm_serial_log="$(boot_matrix_lookup "$edition_id" "$current_sha" 28)"
  vm_build_summary_path="$(boot_matrix_lookup "$edition_id" "$current_sha" 29)"
  vm_build_status="$(boot_matrix_lookup "$edition_id" "$current_sha" 30)"
  vm_telemetry_status="$(boot_matrix_lookup "$edition_id" "$current_sha" 31)"
  vm_session_probe_class="$(boot_matrix_lookup "$edition_id" "$current_sha" 32)"

  [ -n "$vm_classification" ] || vm_classification="NOT_TESTED"
  [ -n "$vm_path" ] || vm_path="$path"
  [ -n "$vm_format" ] || vm_format="$current_format"
  [ -n "$vm_size" ] || vm_size="$current_size"
  [ -n "$vm_tool" ] || vm_tool="qemu-system-x86_64"
  [ -n "$vm_efi" ] || vm_efi="true"
  [ -n "$vm_secure_boot" ] || vm_secure_boot="disabled"
  [ -n "$vm_ram" ] || vm_ram="4096"
  [ -n "$vm_cpu" ] || vm_cpu="2"
  [ -n "$vm_disk" ] || vm_disk="none"
  [ -n "$vm_menu" ] || vm_menu="false"
  [ -n "$vm_kernel" ] || vm_kernel="false"
  [ -n "$vm_initramfs" ] || vm_initramfs="false"
  [ -n "$vm_display" ] || vm_display="false"
  [ -n "$vm_desktop" ] || vm_desktop="false"
  [ -n "$vm_desktop_marker" ] || vm_desktop_marker="false"
  [ -n "$vm_shutdown_marker" ] || vm_shutdown_marker="false"
  [ -n "$vm_session_class" ] || vm_session_class="NOT_RUN"
  [ -n "$vm_session_attempt_count" ] || vm_session_attempt_count="0"
  [ -n "$vm_session_desktop_marker_count" ] || vm_session_desktop_marker_count="0"
  [ -n "$vm_session_shutdown_marker_count" ] || vm_session_shutdown_marker_count="0"
  [ -n "$vm_session_repeatability_risk" ] || vm_session_repeatability_risk="false"
  [ -n "$vm_shutdown" ] || vm_shutdown="false"
  [ -n "$vm_failure_point" ] || vm_failure_point="not_tested"
  [ -n "$vm_boot_log" ] || vm_boot_log=""
  [ -n "$vm_serial_log" ] || vm_serial_log=""
  [ -n "$vm_build_summary_path" ] || vm_build_summary_path="os/phoenix-os/build/build-summary.json"
  [ -n "$vm_build_status" ] || vm_build_status="not_recorded"
  [ -n "$vm_telemetry_status" ] || vm_telemetry_status="not_recorded"
  [ -n "$vm_session_probe_class" ] || vm_session_probe_class="NOT_RUN"

  artifact_vm_tool+=("$vm_tool")
  artifact_vm_efi+=("$vm_efi")
  artifact_vm_secure_boot+=("$vm_secure_boot")
  artifact_vm_ram+=("$vm_ram")
  artifact_vm_cpu+=("$vm_cpu")
  artifact_vm_disk+=("$vm_disk")
  artifact_vm_boot_menu+=("$vm_menu")
  artifact_vm_kernel+=("$vm_kernel")
  artifact_vm_initramfs+=("$vm_initramfs")
  artifact_vm_display+=("$vm_display")
  artifact_vm_desktop+=("$vm_desktop")
  artifact_vm_desktop_marker+=("$vm_desktop_marker")
  artifact_vm_shutdown_marker+=("$vm_shutdown_marker")
  artifact_vm_session_class+=("$vm_session_class")
  artifact_vm_session_probe_class+=("$vm_session_probe_class")
  artifact_vm_session_attempt_count+=("$vm_session_attempt_count")
  artifact_vm_session_desktop_marker_count+=("$vm_session_desktop_marker_count")
  artifact_vm_session_shutdown_marker_count+=("$vm_session_shutdown_marker_count")
  artifact_vm_session_repeatability_risk+=("$vm_session_repeatability_risk")
  artifact_vm_shutdown+=("$vm_shutdown")
  artifact_vm_classification+=("$vm_classification")
  artifact_vm_failure_point+=("$vm_failure_point")
  artifact_vm_boot_log+=("$vm_boot_log")
  artifact_vm_serial_log+=("$vm_serial_log")
  artifact_vm_artifact_path+=("$vm_path")
  artifact_vm_artifact_format+=("$vm_format")
  artifact_vm_artifact_size+=("$vm_size")
  artifact_vm_build_summary_path+=("$vm_build_summary_path")
  artifact_vm_build_status+=("$vm_build_status")
  artifact_vm_telemetry_status+=("$vm_telemetry_status")
done

duplicate_count_for_index() {
  local idx="$1"
  local count=0
  local sha="${artifact_sha[$idx]}"
  local i

  for i in "${!artifact_sha[@]}"; do
    if [ "${artifact_sha[$i]}" = "$sha" ]; then
      count=$((count + 1))
    fi
  done
  echo "$count"
}

duplicate_paths_json_for_index() {
  local idx="$1"
  local sha="${artifact_sha[$idx]}"
  local first=1
  local i

  printf '['
  for i in "${!artifact_sha[@]}"; do
    if [ "$i" != "$idx" ] && [ "${artifact_sha[$i]}" = "$sha" ]; then
      if [ "$first" -eq 0 ]; then
        printf ', '
      fi
      json_string "${artifact_path[$i]}"
      first=0
    fi
  done
  printf ']'
}

artifact_role_for_path() {
  case "$1" in
    iso/outputs/*) echo "registry_output" ;;
    os/phoenix-os/build/*) echo "build_output" ;;
    *) echo "unknown" ;;
  esac
}

vm_status_for_classification() {
  case "$1" in
    BOOT_PASS_DESKTOP|BOOT_PASS_BOOTLOADER_ONLY) echo "vm_boot_pass" ;;
    BOOT_FAIL_KERNEL|BOOT_FAIL_INITRAMFS|BOOT_FAIL_DISPLAY) echo "vm_boot_fail" ;;
    BLOCKED_BY_VM_TOOLING|NOT_TESTED|*) echo "vm_boot_untested" ;;
  esac
}

if [ "$FORMAT" = "markdown" ]; then
  cat <<EOF
# Boot Artifact Registry

Generated: $generated_at

Source commit: \`$source_commit\` ($source_commit_source)

Status policy: Artifact existence is not release readiness. VM and USB boot remain untested until recorded by explicit validation.

  | Edition ID | Display Name | Artifact | Format | Path | Arch | Size Bytes | SHA256 | Build Timestamp | Build Summary | Build Status | Telemetry | Role | VM Class | Menu | Kernel | Initramfs | Display | Desktop | Desktop Marker | Shutdown Marker | Session Class | Session Probe | Session Marks | Shutdown | USB | App | Safety | Duplicate Count |
  |---|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|
EOF
  for i in "${!artifact_path[@]}"; do
    printf '| %s | %s | %s | %s | `%s` | %s | %s | `%s` | %s | `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |\n' \
      "${artifact_edition[$i]}" \
      "${artifact_display[$i]}" \
      "${artifact_filename[$i]}" \
      "${artifact_formats[$i]}" \
      "${artifact_path[$i]}" \
      "${artifact_arch[$i]}" \
      "${artifact_size[$i]}" \
      "${artifact_sha[$i]}" \
      "${artifact_mtime[$i]}" \
      "${artifact_vm_build_summary_path[$i]}" \
      "${artifact_vm_build_status[$i]}" \
      "${artifact_vm_telemetry_status[$i]}" \
      "$(artifact_role_for_path "${artifact_path[$i]}")" \
      "${artifact_vm_classification[$i]}" \
      "${artifact_vm_boot_menu[$i]}" \
      "${artifact_vm_kernel[$i]}" \
      "${artifact_vm_initramfs[$i]}" \
      "${artifact_vm_display[$i]}" \
      "${artifact_vm_desktop[$i]}" \
      "${artifact_vm_desktop_marker[$i]}" \
      "${artifact_vm_shutdown_marker[$i]}" \
      "${artifact_vm_session_class[$i]}" \
      "${artifact_vm_session_probe_class[$i]}" \
      "${artifact_vm_session_desktop_marker_count[$i]}" \
      "${artifact_vm_shutdown[$i]}" \
      "usb_boot_untested" \
      "not_run" \
      "not_run" \
      "$(duplicate_count_for_index "$i")"
  done
  exit 0
fi

cat <<EOF
{
  "schema_version": 1,
  "registry_name": "BWOS / Blue Phoenix OS Multi-Edition Boot Artifact Registry",
  "generated_at": "$(json_escape "$generated_at")",
  "source_commit": "$(json_escape "$source_commit")",
  "source_commit_source": "$(json_escape "$source_commit_source")",
  "source_tree_dirty": $source_tree_dirty,
  "quality_rule": "An artifact without provenance and test status is only a file, not a release.",
$(vm_tool_audit_json)
  "status_fields": [
    "built",
    "checksum_verified",
    "vm_boot_untested",
    "vm_boot_pass",
    "vm_boot_fail",
    "usb_boot_untested",
    "usb_boot_pass",
    "usb_boot_fail",
    "release_blocked",
    "release_candidate"
  ],
  "artifacts": [
EOF

for i in "${!artifact_path[@]}"; do
  if [ "$i" -gt 0 ]; then
    printf ',\n'
  fi

  duplicate_count="$(duplicate_count_for_index "$i")"
  vm_status="$(vm_status_for_classification "${artifact_vm_classification[$i]}")"
  cat <<EOF
    {
      "edition_id": "$(json_escape "${artifact_edition[$i]}")",
      "display_name": "$(json_escape "${artifact_display[$i]}")",
      "iso_filename": "$(json_escape "${artifact_filename[$i]}")",
      "path": "$(json_escape "${artifact_path[$i]}")",
      "artifact_role": "$(json_escape "$(artifact_role_for_path "${artifact_path[$i]}")")",
      "artifact_format": "$(json_escape "${artifact_formats[$i]}")",
      "architecture": "$(json_escape "${artifact_arch[$i]}")",
      "size_bytes": ${artifact_size[$i]},
      "sha256": "$(json_escape "${artifact_sha[$i]}")",
      "build_timestamp": "$(json_escape "${artifact_mtime[$i]}")",
      "build_timestamp_source": "filesystem_mtime",
      "source_commit": "$(json_escape "$source_commit")",
      "source_commit_source": "$(json_escape "$source_commit_source")",
      "edition_manifest_path": "$(json_escape "${artifact_manifest[$i]}")",
      "edition_manifest_sha256": "$(json_escape "${artifact_manifest_hash[$i]}")",
      "build_mode": "$(json_escape "${artifact_build_mode[$i]}")",
      "build_summary_path": "$(json_escape "${artifact_vm_build_summary_path[$i]}")",
      "build_status": "$(json_escape "${artifact_vm_build_status[$i]}")",
      "telemetry_status": "$(json_escape "${artifact_vm_telemetry_status[$i]}")",
      "status": [
        "built",
        "checksum_verified",
        "${vm_status}",
        "usb_boot_untested",
        "release_blocked"
      ],
      "boot_status": {
        "vm": "${vm_status}",
        "usb": "usb_boot_untested",
        "structure_preflight": "$(json_escape "${artifact_preflight[$i]}")"
      },
      "vm_boot_matrix": {
        "classification": "$(json_escape "${artifact_vm_classification[$i]}")",
        "artifact_path": "$(json_escape "${artifact_vm_artifact_path[$i]}")",
        "artifact_format": "$(json_escape "${artifact_vm_artifact_format[$i]}")",
        "artifact_size_bytes": ${artifact_vm_artifact_size[$i]},
        "build_summary_path": "$(json_escape "${artifact_vm_build_summary_path[$i]}")",
        "build_status": "$(json_escape "${artifact_vm_build_status[$i]}")",
        "telemetry_status": "$(json_escape "${artifact_vm_telemetry_status[$i]}")",
        "vm_tool": "$(json_escape "${artifact_vm_tool[$i]}")",
        "efi_enabled": $(json_escape "${artifact_vm_efi[$i]}"),
        "secure_boot_state": "$(json_escape "${artifact_vm_secure_boot[$i]}")",
        "ram_mb": $(json_escape "${artifact_vm_ram[$i]}"),
        "cpu_cores": $(json_escape "${artifact_vm_cpu[$i]}"),
        "disk_attached": "$(json_escape "${artifact_vm_disk[$i]}")",
        "boot_menu_reached": $(json_escape "${artifact_vm_boot_menu[$i]}"),
        "kernel_reached": $(json_escape "${artifact_vm_kernel[$i]}"),
        "initramfs_reached": $(json_escape "${artifact_vm_initramfs[$i]}"),
        "display_manager_reached": $(json_escape "${artifact_vm_display[$i]}"),
        "desktop_reached": $(json_escape "${artifact_vm_desktop[$i]}"),
        "desktop_marker_reached": $(json_escape "${artifact_vm_desktop_marker[$i]}"),
        "shutdown_marker_reached": $(json_escape "${artifact_vm_shutdown_marker[$i]}"),
        "session_determinism_class": "$(json_escape "${artifact_vm_session_class[$i]}")",
        "session_probe_classification": "$(json_escape "${artifact_vm_session_probe_class[$i]}")",
        "session_attempt_count": $(json_escape "${artifact_vm_session_attempt_count[$i]}"),
        "session_desktop_marker_count": $(json_escape "${artifact_vm_session_desktop_marker_count[$i]}"),
        "session_shutdown_marker_count": $(json_escape "${artifact_vm_session_shutdown_marker_count[$i]}"),
        "session_repeatability_risk": $(json_escape "${artifact_vm_session_repeatability_risk[$i]}"),
        "clean_shutdown_verified": $(json_escape "${artifact_vm_shutdown[$i]}"),
        "failure_point": "$(json_escape "${artifact_vm_failure_point[$i]}")",
        "boot_log_path": "$(json_escape "${artifact_vm_boot_log[$i]}")",
        "serial_log_path": "$(json_escape "${artifact_vm_serial_log[$i]}")"
      },
      "app_validation_status": "not_run",
      "safety_validation_status": "not_run",
      "release_readiness": "release_blocked",
      "duplicate_count": $duplicate_count,
      "duplicate_paths": $(duplicate_paths_json_for_index "$i")
    }
EOF
done

cat <<'EOF'
  ]
}
EOF
