#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

FORMAT="json"
EDITION_FILTER=()
ARTIFACT_FILTER=()
TIMEOUT_SECONDS="900"
ATTEMPT_LABEL=""
SESSION_PROFILE=""
FROM_EXISTING="false"
SHUTDOWN_PROBE="false"

usage() {
  cat <<'USAGE'
Usage: iso/scripts/vm-boot-checklist.sh [--json|--markdown] [--root PATH] [--timeout SECONDS] [--edition ID] [--artifact-path PATH] [--session-profile wayland|x11] [--shutdown-probe] [--from-existing]

Boot-tests each current BWOS / Blue Phoenix OS edition ISO in QEMU and records
the exact stage reached without claiming more than was observed.

Outputs:
  --json       Print the machine-readable VM boot matrix JSON (default)
  --markdown   Print the human-readable boot matrix table
  --from-existing
               Regenerate matrix outputs from existing evidence without launching QEMU
  --artifact-path PATH
               Boot-test or render matrix data for one exact ISO/IMG artifact path
  --shutdown-probe
               Select the VM-only shutdown probe GRUB entry
USAGE
}

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
    --timeout)
      TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    --edition)
      EDITION_FILTER+=("$2")
      shift 2
      ;;
    --artifact-path)
      ARTIFACT_FILTER+=("$2")
      shift 2
      ;;
    --attempt-label)
      ATTEMPT_LABEL="$2"
      shift 2
      ;;
    --session-profile)
      SESSION_PROFILE="$2"
      case "$SESSION_PROFILE" in
        wayland|x11) ;;
        *)
          echo "Invalid --session-profile: $SESSION_PROFILE" >&2
          exit 2
          ;;
      esac
      shift 2
      ;;
    --from-existing)
      FROM_EXISTING="true"
      shift
      ;;
    --shutdown-probe)
      SHUTDOWN_PROBE="true"
      shift
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

export ROOT FORMAT TIMEOUT_SECONDS
export ATTEMPT_LABEL SESSION_PROFILE FROM_EXISTING SHUTDOWN_PROBE
if [ "${#ARTIFACT_FILTER[@]}" -gt 0 ]; then
  export ARTIFACT_FILTER_CSV="$(IFS=,; echo "${ARTIFACT_FILTER[*]}")"
else
  export ARTIFACT_FILTER_CSV=""
fi
if [ "${#EDITION_FILTER[@]}" -gt 0 ]; then
  export EDITION_FILTER_CSV="$(IFS=,; echo "${EDITION_FILTER[*]}")"
else
  export EDITION_FILTER_CSV=""
fi

exec python3 - <<'PY'
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(os.environ["ROOT"]).resolve()
FORMAT = os.environ["FORMAT"]
TIMEOUT_SECONDS = int(os.environ["TIMEOUT_SECONDS"])
FILTER = [item for item in os.environ.get("EDITION_FILTER_CSV", "").split(",") if item]
ARTIFACT_FILTER = [item for item in os.environ.get("ARTIFACT_FILTER_CSV", "").split(",") if item]
ATTEMPT_LABEL = os.environ.get("ATTEMPT_LABEL", "")
SESSION_PROFILE = os.environ.get("SESSION_PROFILE", "")
FROM_EXISTING = os.environ.get("FROM_EXISTING", "false") == "true"
SHUTDOWN_PROBE = os.environ.get("SHUTDOWN_PROBE", "false") == "true"

ISO_DIR = ROOT / "iso" / "outputs"
BUILD_DIR = ROOT / "os" / "phoenix-os" / "build"
BUILD_SUMMARY_JSON = BUILD_DIR / "build-summary.json"
BUILD_SUMMARY_MD = BUILD_DIR / "build-summary.md"
BOOT_MATRIX_JSON = ISO_DIR / "vm-boot-matrix.json"
BOOT_MATRIX_MD = ROOT / "iso" / "BOOT_MATRIX.md"
BOOT_REPEATABILITY_MD = ROOT / "iso" / "BOOT_REPEATABILITY.md"
EDITION_ORDER = [
    "home",
    "blue-phoenix",
    "arcwyre",
    "thunder-god",
    "home-arm64",
    "thunder-god-arm64",
    "home-legacy-i386",
]

GRUB_MENU_RE = re.compile(r"(?i)\bwelcome to grub\b|\bgnu grub\b|\bgrub\b")
KERNEL_RE = re.compile(r"(?i)\blinux version\b|\bkernel command line\b|\befi stub: booting linux kernel\b")
INITRAMFS_RE = re.compile(r"(?i)\binitramfs\b|\bbusybox\b|\bbegin: running /scripts\b|\bloading, please wait\b")
DISPLAY_MANAGER_MARKER = "BWOS_BOOT_SUCCESS_GRAPHICAL_REACHED"
DESKTOP_MARKER = "BWOS_DESKTOP_SESSION_STARTED"
SHUTDOWN_MARKER = "BWOS_SHUTDOWN_TELEMETRY_STARTED"
WALLPAPER_MARKER = "BWOS_WALLPAPER_APPLIED"
PRESENTATION_LOCK_MARKER = "BWOS_PRESENTATION_LOCK_ACTIVE"
SDDM_AUTLOGIN_MARKER = "BWOS_SDDM_AUTOLOGIN_CONFIGURED"
SESSION_LAUNCH_MARKER = "BWOS_SESSION_LAUNCH_ATTEMPTED"
WAYLAND_ATTEMPT_MARKER = "BWOS_WAYLAND_SESSION_ATTEMPTED"
X11_ATTEMPT_MARKER = "BWOS_X11_SESSION_ATTEMPTED"
KWIN_STARTED_MARKER = "BWOS_KWIN_STARTED"
PLASMASHELL_STARTED_MARKER = "BWOS_PLASMASHELL_STARTED"
USER_PROVISIONING_OK_MARKER = "BWOS_USER_PROVISIONING_OK"
USER_PROVISIONING_FAIL_MARKER = "BWOS_USER_PROVISIONING_FAIL"
SESSION_CONFIG_FAIL_MARKER = "BWOS_SESSION_CONFIG_FAIL"
KERNEL_CMDLINE_RE = re.compile(r"BWOS_KERNEL_CMDLINE\s+(.*)")
SELECTED_SESSION_RE = re.compile(r"BWOS_SELECTED_SESSION_FILE=([^\s]+)")
SESSION_ENV_RE = re.compile(r"BWOS_SESSION_ENV\s+.*?\bXDG_SESSION_TYPE=([^\s]+)")
SDDM_ACTUAL_SESSION_RE = re.compile(r'Session\s+"(?:/usr/share/(?:x)?sessions/)?([^"/\s]+\.desktop)"\s+selected')
LOGINCTL_SESSION_TYPE_RE = re.compile(r"BWOS_LOGINCTL_SHOW\s+Type=([^\s]+)")
PROCESS_MARKERS = {
    "kwin_x11": "BWOS_PROC_KWIN_X11_STARTED",
    "kwin_wayland": "BWOS_PROC_KWIN_WAYLAND_STARTED",
    "plasmashell": "BWOS_PROC_PLASMASHELL_STARTED",
    "ksmserver": "BWOS_PROC_KSMSERVER_STARTED",
    "startplasma_x11": "BWOS_PROC_STARTPLASMA_X11_STARTED",
    "startplasma_wayland": "BWOS_PROC_STARTPLASMA_WAYLAND_STARTED",
    "dbus_daemon": "BWOS_PROC_DBUS_DAEMON_STARTED",
    "dbus_broker": "BWOS_PROC_DBUS_BROKER_STARTED",
    "systemd_user": "BWOS_PROC_SYSTEMD_USER_STARTED",
}
SESSION_DETERMINISM_GOAL = 3
PR39E_PREFIX = "PR39E-"
PR39F_PREFIX = "PR39F-"
PR39I_PREFIX = "PR39I-"
ATTEMPT_STRENGTH = {
    "NOT_TESTED": 0,
    "BLOCKED_BY_VM_TOOLING": 0,
    "BOOT_FAIL_KERNEL": 1,
    "BOOT_FAIL_INITRAMFS": 2,
    "BOOT_FAIL_DISPLAY": 3,
    "BOOT_PASS_BOOTLOADER_ONLY": 4,
    "BOOT_PASS_DESKTOP": 5,
}

QEMU_X86_64 = next(
    (item for item in [shutil.which("qemu-system-x86_64"), "/opt/homebrew/bin/qemu-system-x86_64"] if item and Path(item).exists()),
    None,
)
QEMU_I386 = next(
    (item for item in [shutil.which("qemu-system-i386"), "/opt/homebrew/bin/qemu-system-i386"] if item and Path(item).exists()),
    None,
)
QEMU_AARCH64 = next(
    (item for item in [shutil.which("qemu-system-aarch64"), "/opt/homebrew/bin/qemu-system-aarch64"] if item and Path(item).exists()),
    None,
)

QEMU_SHARE_DIRS = sorted(Path("/opt/homebrew/Cellar/qemu").glob("*/share/qemu"), reverse=True)
OVMF_X86_64_CODE_CANDIDATES = []
OVMF_X86_64_VARS_CANDIDATES = []
OVMF_I386_CODE_CANDIDATES = []
OVMF_I386_VARS_CANDIDATES = []
OVMF_AARCH64_CODE_CANDIDATES = []
OVMF_AARCH64_VARS_CANDIDATES = []
for share_dir in QEMU_SHARE_DIRS:
    OVMF_X86_64_CODE_CANDIDATES.extend([
        share_dir / "edk2-x86_64-code.fd",
        share_dir / "edk2-x86_64-secure-code.fd",
    ])
    OVMF_X86_64_VARS_CANDIDATES.extend([
        share_dir / "edk2-i386-vars.fd",
        share_dir / "edk2-x86_64-vars.fd",
    ])
    OVMF_I386_CODE_CANDIDATES.extend([
        share_dir / "edk2-i386-code.fd",
        share_dir / "edk2-i386-secure-code.fd",
    ])
    OVMF_I386_VARS_CANDIDATES.extend([
        share_dir / "edk2-i386-vars.fd",
    ])
    OVMF_AARCH64_CODE_CANDIDATES.extend([
        share_dir / "edk2-aarch64-code.fd",
    ])
    OVMF_AARCH64_VARS_CANDIDATES.extend([
        share_dir / "edk2-arm-vars.fd",
    ])

def first_existing(paths: list[str | Path]) -> str | None:
    for item in paths:
        candidate = Path(item)
        if candidate.exists():
            return str(candidate)
    return None

OVMF_X86_64_CODE = first_existing(OVMF_X86_64_CODE_CANDIDATES)
OVMF_X86_64_VARS = first_existing(OVMF_X86_64_VARS_CANDIDATES)
OVMF_I386_CODE = first_existing(OVMF_I386_CODE_CANDIDATES)
OVMF_I386_VARS = first_existing(OVMF_I386_VARS_CANDIDATES)
OVMF_AARCH64_CODE = first_existing(OVMF_AARCH64_CODE_CANDIDATES)
OVMF_AARCH64_VARS = first_existing(OVMF_AARCH64_VARS_CANDIDATES)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
      for chunk in iter(lambda: f.read(1024 * 1024), b""):
        h.update(chunk)
    return h.hexdigest()

def size_file(path: Path) -> int:
    return path.stat().st_size

def mtime_file(path: Path) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(path.stat().st_mtime))

def edition_from_filename(name: str) -> str:
    mapping = {
        "bwos-home.iso": "home",
        "bwos-home.img": "home",
        "bwos-aurelia.iso": "blue-phoenix",
        "bwos-aurelia.img": "blue-phoenix",
        "bwos-arcwyre.iso": "arcwyre",
        "bwos-arcwyre.img": "arcwyre",
        "bwos-thunder-god.iso": "thunder-god",
        "bwos-thunder-god.img": "thunder-god",
        "bwos-thunder-god-arm64.iso": "thunder-god-arm64",
        "bwos-thunder-god-arm64.img": "thunder-god-arm64",
        "bwos-home-arm64.iso": "home-arm64",
        "bwos-home-arm64.img": "home-arm64",
        "bwos-home-legacy-i386.iso": "home-legacy-i386",
        "bwos-home-legacy-i386.img": "home-legacy-i386",
    }
    return mapping.get(name, "unknown")

def yaml_scalar(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$")
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pattern.match(line)
        if m:
            value = m.group(1).strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            return value
    return ""

def edition_is_archived(manifest: Path) -> bool:
    value = yaml_scalar(manifest, "archived")
    return value.lower() == "true"

def yaml_architecture(path: Path) -> str:
    architecture = yaml_scalar(path, "architecture")
    if architecture:
        return architecture
    target = yaml_scalar(path, "target")
    if "amd64" in target:
        return "amd64"
    if "arm64" in target:
        return "arm64"
    if "i386" in target:
        return "i386"
    return "unknown"

def yaml_build_mode(path: Path) -> str:
    target = yaml_scalar(path, "target")
    return target or "unknown"

def artifact_format_from_filename(name: str) -> str:
    if name.endswith(".iso"):
        return "iso"
    if name.endswith(".img"):
        return "dd-image"
    return "unknown"

def build_summary_path() -> str:
    return "os/phoenix-os/build/build-summary.json"

def build_summary_status() -> str:
    return "present" if BUILD_SUMMARY_JSON.exists() else "not_recorded"

def build_status_from_summary() -> str:
    if not BUILD_SUMMARY_JSON.exists():
        return "not_recorded"
    try:
        data = json.loads(BUILD_SUMMARY_JSON.read_text(encoding="utf-8"))
    except Exception:
        return "unknown"
    status = str(data.get("status", "") or data.get("final_status", "") or "").strip()
    return status or "unknown"

def telemetry_status_from_summary() -> str:
    return "recorded" if BUILD_SUMMARY_JSON.exists() else "not_recorded"

def vm_tool_audit() -> dict:
    def version_of(cmd: str) -> str:
        path = shutil.which(cmd)
        if not path:
            return ""
        try:
            result = subprocess.run([path, "--version"], check=False, capture_output=True, text=True)
            line = (result.stdout or result.stderr).strip().splitlines()[0] if (result.stdout or result.stderr) else ""
            return line or "available"
        except Exception:
            return "available"

    return {
        "virtualbox": {
            "available": bool(shutil.which("VBoxManage") or shutil.which("virtualbox")),
            "version": version_of("VBoxManage") or version_of("virtualbox"),
            "limitations": "Apple Silicon builds are not the primary path for x86_64/i386 boot automation; use for arm64 guests only when explicitly needed.",
        },
        "utm": {
            "available": (Path("/Applications/UTM.app").exists() or Path("/Applications/UTM.app/Contents").exists()),
            "version": "4.7.5" if Path("/Applications/UTM.app").exists() else "",
            "limitations": "No native CLI automation is wired into this repository; use manually if needed.",
        },
        "qemu": {
            "available": bool(QEMU_X86_64 or QEMU_I386 or QEMU_AARCH64),
            "version": version_of("qemu-system-x86_64") or version_of("qemu-system-i386") or version_of("qemu-system-aarch64"),
            "limitations": "x86 guests run under TCG on Apple Silicon and are slow; arm64 is supported only when the matching firmware is present.",
        },
    }

def artifact_path_rel(iso: Path) -> str:
    return str(iso.relative_to(ROOT))

def artifact_metadata(iso: Path) -> dict:
    edition_id = edition_from_filename(iso.name)
    manifest = ROOT / "editions" / edition_id / "edition.yaml"
    display_name = yaml_scalar(manifest, "display_name") or edition_id
    artifact_format = artifact_format_from_filename(iso.name)
    arch = yaml_architecture(manifest)
    build_mode = yaml_build_mode(manifest)
    if not arch or arch == "unknown":
        if "i386" in iso.name:
            arch = "i386"
        elif "arm64" in iso.name:
            arch = "arm64"
        elif "amd64" in iso.name or "x86_64" in iso.name:
            arch = "amd64"
    return {
        "edition_id": edition_id,
        "display_name": display_name,
        "iso_filename": iso.name,
        "path": artifact_path_rel(iso),
        "artifact_format": artifact_format,
        "sha256": sha256_file(iso),
        "size_bytes": size_file(iso),
        "mtime": mtime_file(iso),
        "manifest_path": str(manifest.relative_to(ROOT)) if manifest.exists() else "",
        "manifest_hash": sha256_file(manifest) if manifest.exists() else "",
        "arch": arch or "unknown",
        "build_mode": build_mode or "unknown",
    }

def vm_boot_classification(menu: bool, kernel: bool, initramfs: bool, display: bool, desktop: bool, tooling_blocked: bool) -> tuple[str, str]:
    if tooling_blocked:
        return "BLOCKED_BY_VM_TOOLING", "vm_tooling"
    if desktop:
        return "BOOT_PASS_DESKTOP", ""
    if display:
        return "BOOT_FAIL_DISPLAY", "desktop"
    if initramfs:
        return "BOOT_FAIL_DISPLAY", "display"
    if kernel:
        return "BOOT_FAIL_INITRAMFS", "initramfs"
    if menu:
        return "BOOT_PASS_BOOTLOADER_ONLY", "kernel"
    return "BOOT_FAIL_KERNEL", "bootloader"

def vm_plan_for_artifact(meta: dict) -> dict:
    arch = meta.get("arch", "unknown")
    artifact_format = meta.get("artifact_format", "unknown")

    if arch == "arm64":
        if not (QEMU_AARCH64 and OVMF_AARCH64_CODE and OVMF_AARCH64_VARS):
            return {
                "tooling_blocked": True,
                "vm_tool": "qemu-system-aarch64",
                "efi_enabled": True,
                "secure_boot_state": "disabled",
                "ram_mb": 4096,
                "cpu_cores": 2,
                "disk_attached": "none",
                "vm_notes": "aarch64 QEMU firmware unavailable",
                "mode": "arm64-uefi",
            }
        return {
            "tooling_blocked": False,
            "vm_tool": "qemu-system-aarch64",
            "efi_enabled": True,
            "secure_boot_state": "disabled",
            "ram_mb": 4096,
            "cpu_cores": 2,
            "disk_attached": "none",
            "vm_notes": "ARM64 UEFI boot",
            "mode": "arm64-uefi",
        }

    if arch == "i386" or artifact_format == "dd-image":
        if not QEMU_I386:
            return {
                "tooling_blocked": True,
                "vm_tool": "qemu-system-i386",
                "efi_enabled": False,
                "secure_boot_state": "disabled",
                "ram_mb": 4096,
                "cpu_cores": 2,
                "disk_attached": "raw-image",
                "vm_notes": "qemu-system-i386 unavailable",
                "mode": "i386-legacy-bios",
            }
        return {
            "tooling_blocked": False,
            "vm_tool": "qemu-system-i386",
            "efi_enabled": False,
            "secure_boot_state": "disabled",
            "ram_mb": 4096,
            "cpu_cores": 2,
            "disk_attached": "raw-image",
            "vm_notes": "Legacy BIOS raw-image boot",
            "mode": "i386-legacy-bios",
        }

    if not (QEMU_X86_64 and OVMF_X86_64_CODE and OVMF_X86_64_VARS):
        return {
            "tooling_blocked": True,
            "vm_tool": "qemu-system-x86_64",
            "efi_enabled": True,
            "secure_boot_state": "disabled",
            "ram_mb": 4096,
            "cpu_cores": 2,
            "disk_attached": "none",
            "vm_notes": "x86_64 QEMU firmware unavailable",
            "mode": "x86_64-uefi",
        }

    return {
        "tooling_blocked": False,
        "vm_tool": "qemu-system-x86_64",
        "efi_enabled": True,
        "secure_boot_state": "disabled",
        "ram_mb": 4096,
        "cpu_cores": 2,
        "disk_attached": "none",
        "vm_notes": "x86_64 UEFI boot",
        "mode": "x86_64-uefi",
    }

def vm_status_from_classification(classification: str) -> str:
    if classification in {"BOOT_PASS_DESKTOP", "BOOT_PASS_BOOTLOADER_ONLY"}:
        return "vm_boot_pass"
    if classification in {"BOOT_FAIL_KERNEL", "BOOT_FAIL_INITRAMFS", "BOOT_FAIL_DISPLAY"}:
        return "vm_boot_fail"
    return "vm_boot_untested"

def strength_score(classification: str, shutdown_verified: bool) -> int:
    return ATTEMPT_STRENGTH.get(classification, 0) * 2 + (1 if shutdown_verified else 0)

def extract_timestamp_from_text(value: str) -> str:
    match = re.search(r"(\d{8}T\d{6}Z)", value or "")
    return match.group(1) if match else ""

def canonical_attempt_id(row: dict) -> str:
    timestamp = str(row.get("boot_timestamp", "") or "")
    if not timestamp:
        timestamp = extract_timestamp_from_text(str(row.get("boot_log_path", "")))
    if not timestamp:
        timestamp = extract_timestamp_from_text(str(row.get("serial_log_path", "")))
    if not timestamp:
        timestamp = row.get("sha256", "")[:12] or "unknown"
    return f"canonical-{timestamp}"

def build_vm_settings(row: dict) -> dict:
    return {
        "vm_tool": row.get("vm_tool", ""),
        "efi_enabled": row.get("efi_enabled", False),
        "secure_boot_state": row.get("secure_boot_state", "disabled"),
        "ram_mb": row.get("ram_mb", 0),
        "cpu_cores": row.get("cpu_cores", 0),
        "disk_attached": row.get("disk_attached", "none"),
    }

def summarize_attempt(attempt: dict) -> str:
    stage = str(attempt.get("result_stage", "NOT_TESTED"))
    shutdown = "clean shutdown" if attempt.get("clean_shutdown_verified") else "shutdown not verified"
    return f"{stage} ({shutdown})"

def attempt_from_row(row: dict, attempt_label: str = "canonical", canonical_update: bool = True) -> dict:
    boot_timestamp = str(row.get("boot_timestamp", "") or "")
    if not boot_timestamp:
        boot_timestamp = extract_timestamp_from_text(str(row.get("boot_log_path", "")))
    if not boot_timestamp:
        boot_timestamp = extract_timestamp_from_text(str(row.get("serial_log_path", "")))
    if not boot_timestamp:
        boot_timestamp = ""
    return {
        "attempt_label": attempt_label,
        "attempt_timestamp": boot_timestamp,
        "artifact_hash": row.get("sha256", ""),
        "artifact_path": row.get("path", ""),
        "artifact_format": row.get("artifact_format", "unknown"),
        "vm_tool": row.get("vm_tool", ""),
        "vm_settings": build_vm_settings(row),
        "result_stage": row.get("classification", "NOT_TESTED"),
        "boot_menu_reached": bool(row.get("boot_menu_reached", False)),
        "kernel_reached": bool(row.get("kernel_reached", False)),
        "initramfs_reached": bool(row.get("initramfs_reached", False)),
        "display_manager_reached": bool(row.get("display_manager_reached", False)),
        "desktop_reached": bool(row.get("desktop_reached", False)),
        "desktop_marker_reached": bool(row.get("desktop_marker_reached", False)),
        "wallpaper_marker_reached": bool(row.get("wallpaper_marker_reached", False)),
        "presentation_lock_reached": bool(row.get("presentation_lock_reached", False)),
        "shutdown_marker_reached": bool(row.get("shutdown_marker_reached", False)),
        "clean_shutdown_verified": bool(row.get("clean_shutdown_verified", False)),
        "session_profile": str(row.get("session_profile", "") or ""),
        "selected_session_file": str(row.get("selected_session_file", "") or ""),
        "actual_session_type": str(row.get("actual_session_type", "") or ""),
        "actual_sddm_session_file": str(row.get("actual_sddm_session_file", "") or ""),
        "shutdown_probe": bool(row.get("shutdown_probe", False)),
        "session_launch_attempted": bool(row.get("session_launch_attempted", False)),
        "wayland_session_attempted": bool(row.get("wayland_session_attempted", False)),
        "x11_session_attempted": bool(row.get("x11_session_attempted", False)),
        "kwin_started": bool(row.get("kwin_started", False)),
        "plasmashell_started": bool(row.get("plasmashell_started", False)),
        "sddm_autologin_configured": bool(row.get("sddm_autologin_configured", False)),
        "user_provisioning_ok": row.get("user_provisioning_ok", None),
        "session_config_failure": bool(row.get("session_config_failure", False)),
        "process_observations": dict(row.get("process_observations", {}) or {}),
        "session_probe_classification": str(row.get("session_probe_classification", "") or ""),
        "session_logs_path": str(row.get("session_logs_path", "") or ""),
        "screenshot_path": str(row.get("screenshot_path", "") or ""),
        "serial_log_path": str(row.get("serial_log_path", "") or ""),
        "console_log_path": str(row.get("boot_log_path", "") or ""),
        "reason_aborted": str(row.get("reason_aborted", "") or row.get("failure_point", "") or ""),
        "shutdown_method": str(row.get("shutdown_method", "") or ""),
        "canonical_update": bool(canonical_update),
        "attempt_note": str(row.get("attempt_note", "") or ""),
    }

def choose_canonical(existing_row: dict | None, incoming_row: dict | None) -> dict | None:
    if existing_row is None:
        return incoming_row
    if incoming_row is None:
        return existing_row
    existing_strength = strength_score(str(existing_row.get("classification", "NOT_TESTED")), bool(existing_row.get("clean_shutdown_verified", False)))
    incoming_strength = strength_score(str(incoming_row.get("classification", "NOT_TESTED")), bool(incoming_row.get("clean_shutdown_verified", False)))
    if incoming_strength > existing_strength:
        return incoming_row
    return existing_row

def canonical_attempt_from_attempts(attempts: list[dict]) -> dict:
    valid_attempts = [dict(item) for item in attempts if isinstance(item, dict)]
    if not valid_attempts:
        return {}

    def key(attempt: dict) -> tuple[int, int, str]:
        return (
            strength_score(str(attempt.get("result_stage", "NOT_TESTED")), bool(attempt.get("clean_shutdown_verified", False))),
            1 if bool(attempt.get("canonical_update", False)) else 0,
            str(attempt.get("attempt_timestamp", "")),
        )

    return max(valid_attempts, key=key)

def apply_canonical_attempt_evidence(row: dict, attempts: list[dict], summary: dict) -> dict:
    canonical_attempt = canonical_attempt_from_attempts(attempts)
    if not canonical_attempt:
        return row
    row["classification"] = str(canonical_attempt.get("result_stage", row.get("classification", "NOT_TESTED")))
    row["boot_menu_reached"] = bool(canonical_attempt.get("boot_menu_reached", row.get("boot_menu_reached", False)))
    row["kernel_reached"] = bool(canonical_attempt.get("kernel_reached", row.get("kernel_reached", False)))
    row["initramfs_reached"] = bool(canonical_attempt.get("initramfs_reached", row.get("initramfs_reached", False)))
    row["display_manager_reached"] = bool(canonical_attempt.get("display_manager_reached", row.get("display_manager_reached", False)))
    row["desktop_reached"] = bool(canonical_attempt.get("desktop_reached", row.get("desktop_reached", False)))
    row["failure_point"] = str(canonical_attempt.get("reason_aborted", row.get("failure_point", "")) or row.get("failure_point", ""))
    row["boot_log_path"] = str(canonical_attempt.get("console_log_path", row.get("boot_log_path", "")) or "")
    row["serial_log_path"] = str(canonical_attempt.get("serial_log_path", row.get("serial_log_path", "")) or "")
    row["session_logs_path"] = str(canonical_attempt.get("session_logs_path", row.get("session_logs_path", "")) or "")
    row["session_profile"] = str(canonical_attempt.get("session_profile", row.get("session_profile", "")) or "")
    row["selected_session_file"] = str(canonical_attempt.get("selected_session_file", row.get("selected_session_file", "")) or "")
    row["process_observations"] = dict(canonical_attempt.get("process_observations", row.get("process_observations", {})) or {})
    row["desktop_marker_reached"] = bool(canonical_attempt.get("desktop_marker_reached", False))
    row["wallpaper_marker_reached"] = bool(canonical_attempt.get("wallpaper_marker_reached", False))
    row["presentation_lock_reached"] = bool(canonical_attempt.get("presentation_lock_reached", False))
    row["shutdown_marker_reached"] = bool(canonical_attempt.get("shutdown_marker_reached", False))
    row["clean_shutdown_verified"] = bool(canonical_attempt.get("clean_shutdown_verified", False))
    row["kernel_cmdline"] = str(canonical_attempt.get("kernel_cmdline", "") or row.get("kernel_cmdline", "") or "")
    row["shutdown_probe_cmdline_confirmed"] = any(bool(attempt.get("shutdown_probe_cmdline_confirmed", False)) for attempt in attempts)
    row["desktop_marker_attempt_count"] = summary["desktop_marker_attempt_count"]
    row["wallpaper_marker_attempt_count"] = summary["wallpaper_marker_attempt_count"]
    row["presentation_lock_attempt_count"] = summary.get("presentation_lock_attempt_count", 0)
    row["shutdown_marker_attempt_count"] = summary["shutdown_marker_attempt_count"]
    row["clean_shutdown_attempt_count"] = summary["clean_shutdown_attempt_count"]
    row["desktop_shutdown_same_attempt"] = summary["desktop_shutdown_same_attempt"]
    row["desktop_wallpaper_shutdown_same_attempt"] = summary["desktop_wallpaper_shutdown_same_attempt"]
    row["clean_shutdown_after_desktop"] = summary["clean_shutdown_after_desktop"]
    return row

def summarize_boot_attempts(attempts: list[dict]) -> dict:
    attempts = [dict(item) for item in attempts if isinstance(item, dict)]
    if not attempts:
        return {
            "attempt_count": 0,
            "desktop_repeatable": False,
            "shutdown_clean": False,
            "repeatability_risk": False,
            "shutdown_method": "",
            "desktop_marker_attempt_count": 0,
            "wallpaper_marker_attempt_count": 0,
            "presentation_lock_attempt_count": 0,
            "shutdown_marker_attempt_count": 0,
            "clean_shutdown_attempt_count": 0,
            "desktop_shutdown_same_attempt": False,
            "desktop_wallpaper_shutdown_same_attempt": False,
            "clean_shutdown_after_desktop": False,
        }

    classifications = {str(a.get("result_stage", "NOT_TESTED")) for a in attempts}
    strengths = {strength_score(str(a.get("result_stage", "NOT_TESTED")), bool(a.get("clean_shutdown_verified", False))) for a in attempts}
    desktop_repeatable = all(bool(a.get("desktop_reached", False)) for a in attempts) and any(bool(a.get("desktop_reached", False)) for a in attempts)
    shutdown_clean = any(bool(a.get("clean_shutdown_verified", False)) for a in attempts)
    desktop_marker_count = sum(bool(a.get("desktop_marker_reached", False)) for a in attempts)
    wallpaper_marker_count = sum(bool(a.get("wallpaper_marker_reached", False)) for a in attempts)
    presentation_lock_count = sum(bool(a.get("presentation_lock_reached", False)) for a in attempts)
    shutdown_marker_count = sum(bool(a.get("shutdown_marker_reached", False)) for a in attempts)
    clean_shutdown_count = sum(bool(a.get("clean_shutdown_verified", False)) for a in attempts)
    desktop_shutdown_same_attempt = any(
        bool(a.get("desktop_marker_reached", False)) and bool(a.get("shutdown_marker_reached", False))
        for a in attempts
    )
    desktop_wallpaper_shutdown_same_attempt = any(
        bool(a.get("desktop_marker_reached", False))
        and bool(a.get("wallpaper_marker_reached", False))
        and bool(a.get("shutdown_marker_reached", False))
        for a in attempts
    )
    clean_shutdown_after_desktop = any(
        bool(a.get("desktop_marker_reached", False)) and bool(a.get("clean_shutdown_verified", False))
        for a in attempts
    )
    repeatability_risk = len(strengths) > 1 or len(classifications) > 1
    shutdown_method = ""
    if shutdown_clean:
        for a in attempts:
            if bool(a.get("clean_shutdown_verified", False)):
                shutdown_method = str(a.get("shutdown_method", "") or "")
                if shutdown_method:
                    break
    if not shutdown_method and any(str(a.get("shutdown_method", "")) for a in attempts):
        shutdown_method = next(str(a.get("shutdown_method", "")) for a in attempts if str(a.get("shutdown_method", "")))
    return {
        "attempt_count": len(attempts),
        "desktop_repeatable": desktop_repeatable,
        "shutdown_clean": shutdown_clean,
        "repeatability_risk": repeatability_risk,
        "shutdown_method": shutdown_method,
        "desktop_marker_attempt_count": desktop_marker_count,
        "wallpaper_marker_attempt_count": wallpaper_marker_count,
        "presentation_lock_attempt_count": presentation_lock_count,
        "shutdown_marker_attempt_count": shutdown_marker_count,
        "clean_shutdown_attempt_count": clean_shutdown_count,
        "desktop_shutdown_same_attempt": desktop_shutdown_same_attempt,
        "desktop_wallpaper_shutdown_same_attempt": desktop_wallpaper_shutdown_same_attempt,
        "clean_shutdown_after_desktop": clean_shutdown_after_desktop,
    }

def summarize_session_attempts(attempts: list[dict]) -> dict:
    attempts = [
        dict(item)
        for item in attempts
        if isinstance(item, dict)
        and (
            str(item.get("attempt_label", "")).startswith(PR39E_PREFIX)
            or str(item.get("attempt_label", "")).startswith(PR39F_PREFIX)
            or str(item.get("attempt_label", "")).startswith(PR39I_PREFIX)
        )
    ]
    if not attempts:
        return {
            "attempt_count": 0,
            "desktop_marker_count": 0,
            "wallpaper_marker_count": 0,
            "presentation_lock_count": 0,
            "shutdown_marker_count": 0,
            "session_determinism_class": "NOT_RUN",
            "repeatability_risk": False,
            "shutdown_clean": False,
        }

    desktop_marker_count = sum(bool(a.get("desktop_marker_reached", False)) for a in attempts)
    wallpaper_marker_count = sum(bool(a.get("wallpaper_marker_reached", False)) for a in attempts)
    presentation_lock_count = sum(bool(a.get("presentation_lock_reached", False)) for a in attempts)
    shutdown_marker_count = sum(bool(a.get("shutdown_marker_reached", False)) for a in attempts)
    shutdown_clean = any(bool(a.get("clean_shutdown_verified", False)) for a in attempts)
    classifications = {str(a.get("result_stage", "NOT_TESTED")) for a in attempts}
    repeatability_risk = len(classifications) > 1 or len(attempts) != SESSION_DETERMINISM_GOAL
    marker_floor = min(desktop_marker_count, wallpaper_marker_count)
    if marker_floor == 0:
        session_class = "FAIL"
    elif desktop_marker_count == SESSION_DETERMINISM_GOAL and wallpaper_marker_count == SESSION_DETERMINISM_GOAL:
        session_class = "PASS"
    else:
        session_class = "PARTIAL"
    return {
        "attempt_count": len(attempts),
        "desktop_marker_count": desktop_marker_count,
        "wallpaper_marker_count": wallpaper_marker_count,
        "presentation_lock_count": presentation_lock_count,
        "shutdown_marker_count": shutdown_marker_count,
        "session_determinism_class": session_class,
        "repeatability_risk": repeatability_risk,
        "shutdown_clean": shutdown_clean,
    }

def normalize_row(row: dict) -> dict:
    normalized = dict(row)
    filename = str(normalized.get("iso_filename", ""))
    if not filename:
        return normalized

    edition_id = str(normalized.get("edition_id", edition_from_filename(filename)))
    rel_path = str(normalized.get("path", ""))
    if not rel_path:
        output_candidate = ISO_DIR / filename
        build_candidate = BUILD_DIR / filename
        if output_candidate.exists():
            rel_path = str(output_candidate.relative_to(ROOT))
        elif build_candidate.exists():
            rel_path = str(build_candidate.relative_to(ROOT))
        else:
            rel_path = f"iso/outputs/{filename}"

    file_path = ROOT / rel_path
    if normalized.get("size_bytes") in (None, "") and file_path.exists():
        normalized["size_bytes"] = size_file(file_path)
    normalized["edition_id"] = edition_id
    normalized["path"] = rel_path
    normalized["artifact_format"] = normalized.get("artifact_format") or artifact_format_from_filename(filename)
    normalized["build_summary_path"] = normalized.get("build_summary_path") or build_summary_path()
    normalized["build_status"] = normalized.get("build_status") or build_status_from_summary()
    normalized["telemetry_status"] = normalized.get("telemetry_status") or telemetry_status_from_summary()
    normalized["vm_notes"] = normalized.get("vm_notes", "")
    normalized["boot_timestamp"] = normalized.get("boot_timestamp", "")
    normalized["shutdown_method"] = normalized.get("shutdown_method", "")
    normalized["desktop_repeatable"] = bool(normalized.get("desktop_repeatable", False))
    normalized["repeatability_risk"] = bool(normalized.get("repeatability_risk", False))
    normalized["desktop_marker_reached"] = bool(normalized.get("desktop_marker_reached", False))
    normalized["wallpaper_marker_reached"] = bool(normalized.get("wallpaper_marker_reached", False))
    normalized["presentation_lock_reached"] = bool(normalized.get("presentation_lock_reached", False))
    normalized["shutdown_marker_reached"] = bool(normalized.get("shutdown_marker_reached", False))
    normalized["desktop_marker_attempt_count"] = int(normalized.get("desktop_marker_attempt_count", 0) or 0)
    normalized["wallpaper_marker_attempt_count"] = int(normalized.get("wallpaper_marker_attempt_count", 0) or 0)
    normalized["presentation_lock_attempt_count"] = int(normalized.get("presentation_lock_attempt_count", 0) or 0)
    normalized["shutdown_marker_attempt_count"] = int(normalized.get("shutdown_marker_attempt_count", 0) or 0)
    normalized["clean_shutdown_attempt_count"] = int(normalized.get("clean_shutdown_attempt_count", 0) or 0)
    normalized["desktop_shutdown_same_attempt"] = bool(normalized.get("desktop_shutdown_same_attempt", False))
    normalized["desktop_wallpaper_shutdown_same_attempt"] = bool(normalized.get("desktop_wallpaper_shutdown_same_attempt", False))
    normalized["clean_shutdown_after_desktop"] = bool(normalized.get("clean_shutdown_after_desktop", False))
    if bool(normalized.get("desktop_reached", False)) or normalized["desktop_marker_reached"]:
        normalized["display_manager_reached"] = True
    if bool(normalized.get("display_manager_reached", False)):
        normalized["boot_menu_reached"] = True
        normalized["kernel_reached"] = True
        normalized["initramfs_reached"] = True
    normalized["session_determinism_class"] = str(normalized.get("session_determinism_class", "NOT_RUN") or "NOT_RUN")
    normalized["session_attempt_count"] = int(normalized.get("session_attempt_count", 0) or 0)
    normalized["session_desktop_marker_count"] = int(normalized.get("session_desktop_marker_count", 0) or 0)
    normalized["session_wallpaper_marker_count"] = int(normalized.get("session_wallpaper_marker_count", 0) or 0)
    normalized["session_presentation_lock_count"] = int(normalized.get("session_presentation_lock_count", 0) or 0)
    normalized["session_shutdown_marker_count"] = int(normalized.get("session_shutdown_marker_count", 0) or 0)
    normalized["session_repeatability_risk"] = bool(normalized.get("session_repeatability_risk", False))
    normalized["session_profile"] = str(normalized.get("session_profile", "") or "")
    normalized["selected_session_file"] = str(normalized.get("selected_session_file", "") or "")
    normalized["actual_session_type"] = str(normalized.get("actual_session_type", "") or "")
    normalized["actual_sddm_session_file"] = str(normalized.get("actual_sddm_session_file", "") or "")
    normalized["kernel_cmdline"] = str(normalized.get("kernel_cmdline", "") or "")
    normalized["shutdown_probe_cmdline_confirmed"] = bool(normalized.get("shutdown_probe_cmdline_confirmed", False))
    normalized["shutdown_probe"] = bool(normalized.get("shutdown_probe", False))
    normalized["session_launch_attempted"] = bool(normalized.get("session_launch_attempted", False))
    normalized["wayland_session_attempted"] = bool(normalized.get("wayland_session_attempted", False))
    normalized["x11_session_attempted"] = bool(normalized.get("x11_session_attempted", False))
    normalized["kwin_started"] = bool(normalized.get("kwin_started", False))
    normalized["plasmashell_started"] = bool(normalized.get("plasmashell_started", False))
    normalized["sddm_autologin_configured"] = bool(normalized.get("sddm_autologin_configured", False))
    normalized["user_provisioning_ok"] = normalized.get("user_provisioning_ok", None)
    normalized["session_config_failure"] = bool(normalized.get("session_config_failure", False))
    normalized["process_observations"] = dict(normalized.get("process_observations", {}) or {})
    normalized["session_probe_classification"] = str(normalized.get("session_probe_classification", "NOT_RUN") or "NOT_RUN")
    normalized["session_logs_path"] = str(normalized.get("session_logs_path", "") or "")
    normalized["boot_attempts"] = normalized.get("boot_attempts") if isinstance(normalized.get("boot_attempts"), list) else []
    normalized["attempt_count"] = int(normalized.get("attempt_count", len(normalized["boot_attempts"])))
    return normalized

def qmp_send(qmp_path: Path, command: dict, timeout: float = 10.0) -> dict | None:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect(str(qmp_path))
    greeting = sock.recv(4096)
    _ = greeting
    sock.sendall(json.dumps({"execute": "qmp_capabilities"}).encode("utf-8") + b"\n")
    _ = sock.recv(4096)
    sock.sendall(json.dumps(command).encode("utf-8") + b"\n")
    data = sock.recv(4096)
    sock.close()
    try:
        return json.loads(data.decode("utf-8").splitlines()[-1])
    except Exception:
        return None

def qmp_send_key(qmp_path: Path, key: str) -> None:
    qmp_send(qmp_path, {"execute": "send-key", "arguments": {"keys": [{"type": "qcode", "data": key}]}})

def qmp_send_down_and_enter(qmp_path: Path, down_count: int) -> None:
    for _ in range(down_count):
        qmp_send_key(qmp_path, "down")
        time.sleep(0.15)
    qmp_send_key(qmp_path, "ret")

def qmp_send_hotkey_and_enter(qmp_path: Path, hotkey: str) -> None:
    qmp_send_key(qmp_path, hotkey)
    time.sleep(0.2)
    qmp_send_key(qmp_path, "ret")

def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")

def selected_session_from_text(text: str) -> str:
    match = SELECTED_SESSION_RE.search(text)
    return match.group(1) if match else ""

def actual_session_type_from_text(text: str) -> str:
    matches = SESSION_ENV_RE.findall(text)
    if matches:
        return matches[-1]
    loginctl_matches = LOGINCTL_SESSION_TYPE_RE.findall(text)
    return loginctl_matches[-1] if loginctl_matches else ""

def actual_sddm_session_from_text(text: str) -> str:
    matches = SDDM_ACTUAL_SESSION_RE.findall(text)
    return matches[-1] if matches else ""

def kernel_cmdline_from_text(text: str) -> str:
    matches = KERNEL_CMDLINE_RE.findall(text)
    return matches[-1].strip() if matches else ""

def attempt_reached_actual_session(attempt: dict, session_type: str) -> bool:
    actual_type = str(attempt.get("actual_session_type", "") or "").lower()
    actual_sddm = str(attempt.get("actual_sddm_session_file", "") or "").lower()
    selected = str(attempt.get("selected_session_file", "") or "").lower()
    if session_type == "wayland":
        return actual_type == "wayland" or actual_sddm == "plasmawayland.desktop"
    if session_type == "x11":
        return actual_type == "x11" or actual_sddm == "plasma.desktop" or selected == "plasma.desktop"
    return False

def enrich_attempt_from_logs(attempt: dict) -> dict:
    enriched = dict(attempt)
    log_path = str(enriched.get("session_logs_path", "") or "")
    text = ""
    if log_path:
        text = read_text(ROOT / log_path)
        if not str(enriched.get("actual_session_type", "") or ""):
            enriched["actual_session_type"] = actual_session_type_from_text(text)
        if not str(enriched.get("actual_sddm_session_file", "") or ""):
            enriched["actual_sddm_session_file"] = actual_sddm_session_from_text(text)
    serial_path = str(enriched.get("serial_log_path", "") or "")
    if serial_path:
        text = f"{text}\n{read_text(ROOT / serial_path)}"
    if str(enriched.get("session_profile", "")) in {"wayland", "x11"}:
        enriched["session_probe_classification"] = session_probe_classification([enriched])
    if not dict(enriched.get("process_observations", {}) or {}):
        enriched["process_observations"] = {
            name: marker in text
            for name, marker in PROCESS_MARKERS.items()
        }
    if not str(enriched.get("kernel_cmdline", "") or ""):
        if serial_path:
            enriched["kernel_cmdline"] = kernel_cmdline_from_text(read_text(ROOT / serial_path))
    enriched["shutdown_probe_cmdline_confirmed"] = "bwos.shutdown_probe=1" in str(enriched.get("kernel_cmdline", ""))
    # A systemd-shutdown hook can fire when QEMU is terminated after a failed
    # desktop attempt. Preserve clean shutdown evidence, but do not count a
    # forced-kill marker as a valid guest shutdown marker.
    if str(enriched.get("shutdown_method", "")) == "forced kill" and not bool(enriched.get("clean_shutdown_verified", False)):
        enriched["shutdown_marker_reached"] = False
    return enriched

def session_probe_classification(profile_attempts: list[dict]) -> str:
    attempts = [item for item in profile_attempts if isinstance(item, dict)]
    if not attempts:
        return "NOT_RUN"
    if any(item.get("user_provisioning_ok") is False for item in attempts):
        return "USER_PROVISIONING_FAIL"
    if any(item.get("session_config_failure") for item in attempts):
        return "SESSION_CONFIG_FAIL"
    if all(not item.get("display_manager_reached") for item in attempts):
        return "DISPLAY_MANAGER_FAIL"

    wayland_attempts = [item for item in attempts if item.get("session_profile") == "wayland"]
    x11_attempts = [item for item in attempts if item.get("session_profile") == "x11"]
    wayland_pass = any(
        item.get("desktop_marker_reached") and attempt_reached_actual_session(item, "wayland")
        for item in wayland_attempts
    )
    x11_pass = any(
        item.get("desktop_marker_reached") and attempt_reached_actual_session(item, "x11")
        for item in x11_attempts
    )
    implicit_x11_pass = any(
        item.get("desktop_marker_reached") and attempt_reached_actual_session(item, "x11")
        for item in wayland_attempts
    )

    if wayland_pass:
        return "WAYLAND_PASS"
    if x11_pass:
        return "WAYLAND_FAIL_X11_PASS"
    if wayland_attempts and (x11_pass or implicit_x11_pass):
        return "WAYLAND_FAIL_X11_PASS"
    if wayland_attempts and x11_attempts:
        return "BOTH_FAIL"
    if any(item.get("session_launch_attempted") for item in attempts):
        return "MARKER_HOOK_FAIL"
    return "MARKER_HOOK_FAIL"

def write_session_extract(serial_path: Path, output_path: Path) -> str:
    text = read_text(serial_path)
    interesting = []
    patterns = re.compile(r"BWOS_|sddm|plasma|kwin|ksmserver|startplasma|wayland|x11|xorg|pam|dbus|loginctl|XDG_RUNTIME_DIR|DISPLAY|WAYLAND_DISPLAY|DBUS_SESSION_BUS_ADDRESS", re.IGNORECASE)
    for line in text.splitlines():
        if patterns.search(line):
            interesting.append(line)
    output_path.write_text("\n".join(interesting[-500:]) + ("\n" if interesting else ""), encoding="utf-8")
    return str(output_path.relative_to(ROOT))

def render_markdown(rows: list[dict], generated_at: str, audit: dict) -> str:
    lines = [
        "# VM Boot Matrix",
        "",
        f"Generated: {generated_at}",
        "",
        "VM policy: EFI on, Secure Boot off, 4096 MB RAM minimum, 2 CPU cores minimum, and no host disk or USB passthrough.",
        "",
        "## VM Tool Audit",
        "",
        "| Tool | Availability | Version | Limitations |",
        "|---|---|---|---|",
    ]
    for tool_name in ("virtualbox", "utm", "qemu"):
        tool = audit.get(tool_name, {})
        availability = "available" if tool.get("available") else "unavailable"
        lines.append(
            f"| {tool_name} | {availability} | {tool.get('version', '')} | {tool.get('limitations', '')} |"
        )

    lines.extend([
        "",
        "| Edition ID | Artifact Filename | Path | Format | Size Bytes | SHA256 | Build Summary | Build Status | Telemetry | VM Tool | EFI | Secure Boot | RAM | CPU | Disk | Attempts | Desktop Repeatable | Repeatability Risk | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Desktop+Shutdown Same Attempt | Desktop+Wallpaper+Shutdown Same Attempt | Desktop Marker Attempts | Wallpaper Marker Attempts | Presentation Lock Attempts | Shutdown Marker Attempts | Clean Shutdown Attempts | Session Class | Session Probe | Session Desktop Marker Count | Session Wallpaper Marker Count | Session Presentation Lock Count | Shutdown Clean | Shutdown Method | Boot Menu | Kernel | Initramfs | Display Manager | Desktop | Class | Failure Point |",
        "|---|---|---|---|---:|---|---|---|---|---|---|---|---:|---:|---|---:|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|---|---|---|---|---|---|---|",
    ])
    for row in rows:
        lines.append(
            "| {edition_id} | {iso_filename} | `{path}` | {artifact_format} | {size_bytes} | `{sha256}` | `{build_summary_path}` | {build_status} | {telemetry_status} | {vm_tool} | {efi_enabled} | {secure_boot_state} | {ram_mb} | {cpu_cores} | {disk_attached} | {attempt_count} | {desktop_repeatable} | {repeatability_risk} | {desktop_marker_reached} | {wallpaper_marker_reached} | {presentation_lock_reached} | {shutdown_marker_reached} | {desktop_shutdown_same_attempt} | {desktop_wallpaper_shutdown_same_attempt} | {desktop_marker_attempt_count} | {wallpaper_marker_attempt_count} | {presentation_lock_attempt_count} | {shutdown_marker_attempt_count} | {clean_shutdown_attempt_count} | {session_determinism_class} | {session_probe_classification} | {session_desktop_marker_count} | {session_wallpaper_marker_count} | {session_presentation_lock_count} | {clean_shutdown_verified} | {shutdown_method} | {boot_menu_reached} | {kernel_reached} | {initramfs_reached} | {display_manager_reached} | {desktop_reached} | {classification} | {failure_point} |".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"

def render_repeatability(rows: list[dict], generated_at: str) -> str:
    lines = [
        "# Boot Repeatability",
        "",
        f"Generated: {generated_at}",
        "",
        "This file records attempt-level evidence. Canonical boot status is only allowed to improve when a stronger attempt is observed.",
        "",
    ]
    for row in rows:
        lines.extend([
            f"## {row['edition_id']} - {row['iso_filename']}",
            "",
            f"- SHA256: `{row['sha256']}`",
            f"- Canonical class: `{row['classification']}`",
            f"- Desktop repeatable: `{row.get('desktop_repeatable', False)}`",
            f"- Shutdown clean: `{row.get('clean_shutdown_verified', False)}`",
            f"- Shutdown method: `{row.get('shutdown_method', '') or 'n/a'}`",
            f"- Repeatability risk: `{row.get('repeatability_risk', False)}`",
            f"- Desktop + shutdown same attempt: `{row.get('desktop_shutdown_same_attempt', False)}`",
            f"- Desktop + wallpaper + shutdown same attempt: `{row.get('desktop_wallpaper_shutdown_same_attempt', False)}`",
            f"- Desktop marker attempts: `{row.get('desktop_marker_attempt_count', 0)}`",
            f"- Wallpaper marker attempts: `{row.get('wallpaper_marker_attempt_count', 0)}`",
            f"- Presentation lock attempts: `{row.get('presentation_lock_attempt_count', 0)}`",
            f"- Shutdown marker attempts: `{row.get('shutdown_marker_attempt_count', 0)}`",
            f"- Clean shutdown attempts: `{row.get('clean_shutdown_attempt_count', 0)}`",
            f"- Session determinism class: `{row.get('session_determinism_class', 'NOT_RUN')}`",
            f"- Session desktop markers: `{row.get('session_desktop_marker_count', 0)}` / `{SESSION_DETERMINISM_GOAL}`",
            f"- Session wallpaper markers: `{row.get('session_wallpaper_marker_count', 0)}` / `{SESSION_DETERMINISM_GOAL}`",
            f"- Session presentation lock markers: `{row.get('session_presentation_lock_count', 0)}` / `{SESSION_DETERMINISM_GOAL}`",
            f"- Wallpaper marker reached: `{row.get('wallpaper_marker_reached', False)}`",
            f"- Session shutdown markers: `{row.get('session_shutdown_marker_count', 0)}`",
            "",
            "| Attempt | Timestamp | Result Stage | Desktop | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Clean Shutdown | Canonical Update | Screenshot | Reason/Note | Console Log | Serial Log |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ])
        for attempt in row.get("boot_attempts", []) or []:
            lines.append(
                "| {attempt_label} | {attempt_timestamp} | {result_stage} | {desktop_reached} | {desktop_marker_reached} | {wallpaper_marker_reached} | {presentation_lock_reached} | {shutdown_marker_reached} | {clean_shutdown_verified} | {canonical_update} | {screenshot_path} | {reason} | {console_log} | {serial_log} |".format(
                    attempt_label=attempt.get("attempt_label", ""),
                    attempt_timestamp=attempt.get("attempt_timestamp", ""),
                    result_stage=attempt.get("result_stage", ""),
                    desktop_reached=attempt.get("desktop_reached", False),
                    desktop_marker_reached=attempt.get("desktop_marker_reached", False),
                    wallpaper_marker_reached=attempt.get("wallpaper_marker_reached", False),
                    presentation_lock_reached=attempt.get("presentation_lock_reached", False),
                    shutdown_marker_reached=attempt.get("shutdown_marker_reached", False),
                    clean_shutdown_verified=attempt.get("clean_shutdown_verified", False),
                    canonical_update=attempt.get("canonical_update", False),
                    screenshot_path=attempt.get("screenshot_path", ""),
                    reason=(attempt.get("reason_aborted", "") or attempt.get("attempt_note", "") or "").replace("|", "\\|"),
                    console_log=attempt.get("console_log_path", ""),
                    serial_log=attempt.get("serial_log_path", ""),
                )
            )
        session_attempts = [
            attempt
            for attempt in (row.get("boot_attempts", []) or [])
            if str(attempt.get("attempt_label", "")).startswith(PR39E_PREFIX)
            or str(attempt.get("attempt_label", "")).startswith(PR39F_PREFIX)
            or str(attempt.get("attempt_label", "")).startswith(PR39I_PREFIX)
        ]
        if session_attempts:
            lines.extend([
                "",
                "### PR39E/PR39F/PR39I Session Determinism Attempts",
                "",
                "| Attempt | Timestamp | Requested Profile | Selected Session | Actual Type | Actual SDDM Session | Shutdown Probe Cmdline | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Shutdown | Probe Class | Session Logs | Console Log | Serial Log | Reason/Note |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
            ])
            for attempt in session_attempts:
                lines.append(
                    "| {attempt_label} | {attempt_timestamp} | {session_profile} | {selected_session_file} | {actual_session_type} | {actual_sddm_session_file} | {shutdown_probe_cmdline_confirmed} | {desktop_marker_reached} | {wallpaper_marker_reached} | {presentation_lock_reached} | {shutdown_marker_reached} | {clean_shutdown_verified} | {session_probe_classification} | {session_logs} | {console_log} | {serial_log} | {reason} |".format(
                        attempt_label=attempt.get("attempt_label", ""),
                        attempt_timestamp=attempt.get("attempt_timestamp", ""),
                        session_profile=attempt.get("session_profile", ""),
                        selected_session_file=attempt.get("selected_session_file", ""),
                        actual_session_type=attempt.get("actual_session_type", ""),
                        actual_sddm_session_file=attempt.get("actual_sddm_session_file", ""),
                        shutdown_probe_cmdline_confirmed=attempt.get("shutdown_probe_cmdline_confirmed", False),
                        desktop_marker_reached=attempt.get("desktop_marker_reached", False),
                        wallpaper_marker_reached=attempt.get("wallpaper_marker_reached", False),
                        presentation_lock_reached=attempt.get("presentation_lock_reached", False),
                        shutdown_marker_reached=attempt.get("shutdown_marker_reached", False),
                        clean_shutdown_verified=attempt.get("clean_shutdown_verified", False),
                        session_probe_classification=attempt.get("session_probe_classification", ""),
                        session_logs=attempt.get("session_logs_path", ""),
                        console_log=attempt.get("console_log_path", ""),
                        serial_log=attempt.get("serial_log_path", ""),
                        reason=(attempt.get("reason_aborted", "") or attempt.get("attempt_note", "") or "").replace("|", "\\|"),
                    )
                )
        lines.append("")
    return "\n".join(lines) + "\n"

def render_boot_log_excerpt(row: dict) -> str:
    failure = row["failure_point"] or "none"
    return (
        f"{row['edition_id']}: {row['classification']} ({failure})\n"
        f"  ISO: {row['iso_filename']}\n"
        f"  Menu: {row['boot_menu_reached']} | Kernel: {row['kernel_reached']} | Initramfs: {row['initramfs_reached']} | "
        f"Display: {row['display_manager_reached']} | Desktop: {row['desktop_reached']} | Shutdown: {row['clean_shutdown_verified']}\n"
    )

def list_target_isos() -> list[Path]:
    if ARTIFACT_FILTER:
        targets: list[Path] = []
        for item in ARTIFACT_FILTER:
            artifact = Path(item)
            if not artifact.is_absolute():
                artifact = ROOT / artifact
            artifact = artifact.resolve()
            if not artifact.exists():
                raise SystemExit(f"Artifact path does not exist: {artifact}")
            edition_id = edition_from_filename(artifact.name)
            if edition_id == "unknown":
                raise SystemExit(f"Cannot infer edition from artifact path: {artifact}")
            manifest = ROOT / "editions" / edition_id / "edition.yaml"
            if not manifest.exists() or edition_is_archived(manifest):
                raise SystemExit(f"Artifact is not an active edition target: {artifact}")
            targets.append(artifact)
        return targets

    candidates = sorted(
        list(BUILD_DIR.glob("bwos-*.iso"))
        + list(BUILD_DIR.glob("bwos-*.img"))
        + list(ISO_DIR.glob("bwos-*.iso"))
        + list(ISO_DIR.glob("bwos-*.img"))
    )
    targets: list[Path] = []
    for iso in candidates:
        if not iso.exists():
            continue
        edition_id = edition_from_filename(iso.name)
        if edition_id == "unknown":
            continue
        manifest = ROOT / "editions" / edition_id / "edition.yaml"
        if not manifest.exists() or edition_is_archived(manifest):
            continue
        targets.append(iso)
    if FILTER:
        wanted = set(FILTER)
        filtered = []
        for iso in targets:
            if iso.stem in wanted or edition_from_filename(iso.name) in wanted:
                filtered.append(iso)
        return filtered
    return [item for item in sorted(
        targets,
        key=lambda item: (
            {edition: index for index, edition in enumerate(EDITION_ORDER)}.get(edition_from_filename(item.name), len(EDITION_ORDER)),
            edition_from_filename(item.name),
            0 if item.is_relative_to(ISO_DIR) else 1,
            str(item.name),
        ),
    )]

def main() -> int:
    rows: list[dict] = []
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    attempt_label = ATTEMPT_LABEL or generated_at

    if FROM_EXISTING:
        evidence_attempts = load_evidence_attempts()
        rows = []
        for iso in list_target_isos():
            meta = artifact_metadata(iso)
            plan = vm_plan_for_artifact(meta)
            attempts = evidence_attempts.get((meta["edition_id"], meta["sha256"]), [])
            rows.append(row_from_artifact_and_evidence(meta, plan, attempts, generated_at))
        merged_rows = write_outputs(rows, generated_at)
        if FORMAT == "markdown":
            print(render_markdown(merged_rows, generated_at, vm_tool_audit()), end="")
        else:
            print(json.dumps({"generated_at": generated_at, "vm_tool_audit": vm_tool_audit(), "artifacts": merged_rows}, indent=2))
        return 0

    existing_index = {
        (str(row.get("edition_id", "")), str(row.get("sha256", ""))): row
        for row in load_existing_rows()
    }
    for iso in list_target_isos():
        meta = artifact_metadata(iso)
        plan = vm_plan_for_artifact(meta)
        edition_id = meta["edition_id"]
        display_name = meta["display_name"]
        sha = meta["sha256"]
        artifact_format = meta["artifact_format"]
        summary_path = build_summary_path()
        summary_status = build_summary_status()
        telemetry_status = telemetry_status_from_summary()
        existing_row = existing_index.get((edition_id, sha))

        if plan["tooling_blocked"]:
            attempt = {
                "attempt_label": attempt_label,
                "attempt_timestamp": generated_at,
                "artifact_hash": sha,
                "artifact_path": meta["path"],
                "artifact_format": artifact_format,
                "vm_tool": plan["vm_tool"],
                "vm_settings": build_vm_settings({
                    "vm_tool": plan["vm_tool"],
                    "efi_enabled": plan["efi_enabled"],
                    "secure_boot_state": plan["secure_boot_state"],
                    "ram_mb": plan["ram_mb"],
                    "cpu_cores": plan["cpu_cores"],
                    "disk_attached": plan["disk_attached"],
                }),
                "result_stage": "BLOCKED_BY_VM_TOOLING",
                "boot_menu_reached": False,
                "kernel_reached": False,
                "initramfs_reached": False,
                "display_manager_reached": False,
                "desktop_reached": False,
                "desktop_marker_reached": False,
                "shutdown_marker_reached": False,
                "clean_shutdown_verified": False,
                "screenshot_path": "",
                "serial_log_path": "",
                "console_log_path": "",
                "reason_aborted": "vm_tooling",
                "shutdown_method": "",
                "canonical_update": existing_row is None,
                "attempt_note": plan["vm_notes"],
            }
            row = {
                "edition_id": edition_id,
                "display_name": display_name,
                "iso_filename": meta["iso_filename"],
                "path": meta["path"],
                "artifact_format": artifact_format,
                "size_bytes": meta["size_bytes"],
                "sha256": sha,
                "build_summary_path": summary_path,
                "build_status": build_status_from_summary(),
                "telemetry_status": telemetry_status,
                "vm_tool": plan["vm_tool"],
                "efi_enabled": plan["efi_enabled"],
                "secure_boot_state": plan["secure_boot_state"],
                "ram_mb": plan["ram_mb"],
                "cpu_cores": plan["cpu_cores"],
                "disk_attached": plan["disk_attached"],
                "boot_menu_reached": False,
                "kernel_reached": False,
                "initramfs_reached": False,
                "display_manager_reached": False,
                "desktop_reached": False,
                "clean_shutdown_verified": False,
                "classification": "BLOCKED_BY_VM_TOOLING",
                "failure_point": "vm_tooling",
                "boot_log_path": "",
                "serial_log_path": "",
                "vm_notes": plan["vm_notes"],
                "boot_timestamp": generated_at,
                "boot_attempts": [attempt],
                "attempt_count": 1,
                "desktop_repeatable": False,
                "repeatability_risk": False,
                "desktop_marker_reached": False,
                "shutdown_marker_reached": False,
                "session_determinism_class": "NOT_RUN",
                "session_attempt_count": 0,
                "session_desktop_marker_count": 0,
                "session_shutdown_marker_count": 0,
                "session_repeatability_risk": False,
                "shutdown_method": "",
            }
            attempt["canonical_update"] = choose_canonical(existing_row, row) is row
            rows.append(normalize_row(row))
            continue

        tempdir = Path(tempfile.mkdtemp(prefix=f"bwos-vm-{edition_id}-"))
        boot_target = tempdir / iso.name
        console_log = tempdir / "console.log"
        serial_log = tempdir / "serial.log"
        qmp_socket = tempdir / "qmp.sock"
        ovmf_vars = tempdir / "ovmf-vars.fd"
        shutil.copy2(iso, boot_target)
        if plan["mode"] == "x86_64-uefi":
            shutil.copy2(OVMF_X86_64_VARS, ovmf_vars)
        elif plan["mode"] == "arm64-uefi":
            shutil.copy2(OVMF_AARCH64_VARS, ovmf_vars)
        elif plan["mode"] == "i386-legacy-bios":
            pass

        if plan["mode"] == "x86_64-uefi":
            cmd = [
                QEMU_X86_64,
                "-machine", "q35,accel=tcg",
                "-m", "4096",
                "-smp", "2",
                "-cpu", "qemu64",
                "-nographic",
                "-boot", "d",
                "-cdrom", str(boot_target),
                "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_X86_64_CODE}",
                "-drive", f"if=pflash,format=raw,file={ovmf_vars}",
                "-serial", f"file:{serial_log}",
                "-qmp", f"unix:{qmp_socket},server,nowait",
                "-monitor", "none",
                "-no-reboot",
                "-net", "none",
            ]
        elif plan["mode"] == "arm64-uefi":
            cmd = [
                QEMU_AARCH64,
                "-machine", "virt,accel=tcg",
                "-cpu", "cortex-a57",
                "-m", "4096",
                "-smp", "2",
                "-nographic",
                "-boot", "d",
                "-cdrom", str(boot_target),
                "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_AARCH64_CODE}",
                "-drive", f"if=pflash,format=raw,file={ovmf_vars}",
                "-serial", f"file:{serial_log}",
                "-qmp", f"unix:{qmp_socket},server,nowait",
                "-monitor", "none",
                "-no-reboot",
                "-net", "none",
            ]
        else:
            cmd = [
                QEMU_I386,
                "-machine", "pc,accel=tcg",
                "-m", "4096",
                "-smp", "2",
                "-nographic",
                "-boot", "c",
                "-drive", f"file={boot_target},format=raw,if=ide",
                "-serial", f"file:{serial_log}",
                "-qmp", f"unix:{qmp_socket},server,nowait",
                "-monitor", "none",
                "-no-reboot",
                "-net", "none",
            ]

        console_f = console_log.open("wb")
        proc = subprocess.Popen(cmd, stdout=console_f, stderr=subprocess.STDOUT)

        menu = False
        kernel = False
        initramfs = False
        display = False
        desktop = False
        desktop_marker = False
        wallpaper_marker = False
        presentation_lock = False
        shutdown_marker = False
        sddm_autologin_configured = False
        session_launch_attempted = False
        wayland_session_attempted = False
        x11_session_attempted = False
        kwin_started = False
        plasmashell_started = False
        user_provisioning_ok = None
        session_config_failure = False
        selected_session_file = ""
        actual_session_type = ""
        actual_sddm_session_file = ""
        kernel_cmdline = ""
        shutdown = False
        shutdown_requested = False
        failure_point = ""
        qmp_powered = False
        qemu_exited_normally = False
        forced_termination = False
        boot_profile_selected = False
        requested_session_profile = SESSION_PROFILE
        shutdown_probe_requested = SHUTDOWN_PROBE

        start = time.time()
        deadline = start + TIMEOUT_SECONDS
        shutdown_deadline = None

        try:
            while time.time() < deadline:
                console_text = read_text(console_log)
                serial_text = read_text(serial_log)

                if not menu and (GRUB_MENU_RE.search(console_text) or GRUB_MENU_RE.search(serial_text)):
                    menu = True
                if menu and (requested_session_profile == "x11" or shutdown_probe_requested) and not boot_profile_selected:
                    try:
                        qmp_send_hotkey_and_enter(qmp_socket, "s" if shutdown_probe_requested else "x")
                        boot_profile_selected = True
                    except Exception:
                        boot_profile_selected = True
                if not kernel and KERNEL_RE.search(serial_text):
                    kernel = True
                if not initramfs and INITRAMFS_RE.search(serial_text):
                    initramfs = True
                if not display and DISPLAY_MANAGER_MARKER in serial_text:
                    display = True
                if not desktop_marker and DESKTOP_MARKER in serial_text:
                    desktop_marker = True
                    desktop = True
                if not wallpaper_marker and WALLPAPER_MARKER in serial_text:
                    wallpaper_marker = True
                if not presentation_lock and PRESENTATION_LOCK_MARKER in serial_text:
                    presentation_lock = True
                if not shutdown_marker and SHUTDOWN_MARKER in serial_text:
                    shutdown_marker = True
                if not sddm_autologin_configured and SDDM_AUTLOGIN_MARKER in serial_text:
                    sddm_autologin_configured = True
                if not session_launch_attempted and SESSION_LAUNCH_MARKER in serial_text:
                    session_launch_attempted = True
                if not wayland_session_attempted and WAYLAND_ATTEMPT_MARKER in serial_text:
                    wayland_session_attempted = True
                if not x11_session_attempted and X11_ATTEMPT_MARKER in serial_text:
                    x11_session_attempted = True
                if not kwin_started and KWIN_STARTED_MARKER in serial_text:
                    kwin_started = True
                if not plasmashell_started and PLASMASHELL_STARTED_MARKER in serial_text:
                    plasmashell_started = True
                if user_provisioning_ok is None and USER_PROVISIONING_OK_MARKER in serial_text:
                    user_provisioning_ok = True
                if user_provisioning_ok is None and USER_PROVISIONING_FAIL_MARKER in serial_text:
                    user_provisioning_ok = False
                if not session_config_failure and SESSION_CONFIG_FAIL_MARKER in serial_text:
                    session_config_failure = True
                if not selected_session_file:
                    selected_session_file = selected_session_from_text(serial_text)
                parsed_session_type = actual_session_type_from_text(serial_text)
                if parsed_session_type:
                    actual_session_type = parsed_session_type
                parsed_sddm_session = actual_sddm_session_from_text(serial_text)
                if parsed_sddm_session:
                    actual_sddm_session_file = parsed_sddm_session
                parsed_cmdline = kernel_cmdline_from_text(serial_text)
                if parsed_cmdline:
                    kernel_cmdline = parsed_cmdline

                if desktop and not shutdown_requested and not shutdown_probe_requested:
                    try:
                        qmp_send(qmp_socket, {"execute": "system_powerdown"})
                        shutdown_requested = True
                        shutdown_deadline = time.time() + 120
                        qmp_powered = True
                    except Exception:
                        shutdown_requested = True
                        shutdown_deadline = time.time() + 5
                elif desktop and shutdown_probe_requested and not shutdown_requested:
                    shutdown_requested = True
                    shutdown_deadline = time.time() + 180

                if shutdown_requested and proc.poll() is not None:
                    shutdown = True
                    qemu_exited_normally = True
                    break

                if proc.poll() is not None:
                    qemu_exited_normally = True
                    break

                if shutdown_requested and shutdown_deadline is not None and time.time() > shutdown_deadline:
                    break

                time.sleep(2)
        finally:
            if proc.poll() is None:
                forced_termination = True
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)
            console_f.close()

        shutdown = bool(shutdown and shutdown_marker)
        effective_shutdown_marker = bool(shutdown_marker and shutdown_requested)

        classification, inferred_failure = vm_boot_classification(
            menu, kernel, initramfs, display, desktop, False
        )
        aborted_reason = ""
        shutdown_method = ""
        if failure_point == "":
            failure_point = inferred_failure
        if classification == "BOOT_PASS_DESKTOP" and not shutdown:
            failure_point = "shutdown"
        if classification == "BOOT_PASS_DESKTOP" and shutdown:
            shutdown_method = "ACPI power button"
        elif shutdown_requested and not shutdown:
            shutdown_method = "forced kill"
            aborted_reason = "timeout"
        elif failure_point:
            shutdown_method = "forced kill" if not shutdown else shutdown_method
            aborted_reason = failure_point
        else:
            shutdown_method = "forced kill" if not shutdown else shutdown_method

        evidence_dir = ISO_DIR / "vm-boot-evidence" / edition_id / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        evidence_dir.mkdir(parents=True, exist_ok=True)
        saved_console = evidence_dir / "console.log"
        saved_serial = evidence_dir / "serial.log"
        saved_qmp = evidence_dir / "qmp.sock"
        saved_attempt = evidence_dir / "attempt.json"
        saved_session_logs = evidence_dir / "session.log"
        shutil.move(str(console_log), saved_console)
        if serial_log.exists():
            shutil.move(str(serial_log), saved_serial)
            session_logs_path = write_session_extract(saved_serial, saved_session_logs)
        else:
            session_logs_path = ""
        if qmp_socket.exists():
            shutil.move(str(qmp_socket), saved_qmp)

        saved_serial_text = read_text(saved_serial) if saved_serial.exists() else ""
        process_observations = {
            name: marker in saved_serial_text
            for name, marker in PROCESS_MARKERS.items()
        }
        attempt_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        attempt = {
            "attempt_label": attempt_label,
            "attempt_timestamp": attempt_timestamp,
            "artifact_hash": sha,
            "artifact_path": meta["path"],
            "artifact_format": artifact_format,
            "session_profile": requested_session_profile,
            "selected_session_file": selected_session_file,
            "actual_session_type": actual_session_type,
            "actual_sddm_session_file": actual_sddm_session_file,
            "kernel_cmdline": kernel_cmdline,
            "shutdown_probe_cmdline_confirmed": "bwos.shutdown_probe=1" in kernel_cmdline,
            "shutdown_probe": shutdown_probe_requested,
            "acpi_powerdown_requested": shutdown_requested and not shutdown_probe_requested,
            "qmp_powerdown_sent": qmp_powered,
            "qemu_exited_normally": qemu_exited_normally,
            "forced_termination": forced_termination,
            "vm_tool": plan["vm_tool"],
            "vm_settings": build_vm_settings(plan),
            "result_stage": classification,
            "boot_menu_reached": menu,
            "kernel_reached": kernel,
            "initramfs_reached": initramfs,
            "display_manager_reached": display,
            "desktop_reached": desktop,
            "desktop_marker_reached": desktop_marker,
            "wallpaper_marker_reached": wallpaper_marker,
            "presentation_lock_reached": presentation_lock,
            "shutdown_marker_reached": effective_shutdown_marker,
            "sddm_autologin_configured": sddm_autologin_configured,
            "session_launch_attempted": session_launch_attempted,
            "wayland_session_attempted": wayland_session_attempted,
            "x11_session_attempted": x11_session_attempted,
            "kwin_started": kwin_started,
            "plasmashell_started": plasmashell_started,
            "user_provisioning_ok": user_provisioning_ok,
            "session_config_failure": session_config_failure,
            "process_observations": process_observations,
            "session_probe_classification": session_probe_classification([{
                "session_profile": requested_session_profile,
                "display_manager_reached": display,
                "desktop_marker_reached": desktop_marker,
                "actual_session_type": actual_session_type,
                "actual_sddm_session_file": actual_sddm_session_file,
                "selected_session_file": selected_session_file,
                "session_launch_attempted": session_launch_attempted,
                "user_provisioning_ok": user_provisioning_ok,
                "session_config_failure": session_config_failure,
            }]),
            "clean_shutdown_verified": shutdown,
            "screenshot_path": "",
            "session_logs_path": session_logs_path,
            "serial_log_path": str(saved_serial.relative_to(ROOT)) if saved_serial.exists() else "",
            "console_log_path": str(saved_console.relative_to(ROOT)),
            "reason_aborted": aborted_reason,
            "shutdown_method": shutdown_method,
            "canonical_update": False,
            "attempt_note": (plan["vm_notes"] + ("; shutdown probe requested" if shutdown_probe_requested else "") + ("; ACPI powerdown sent" if qmp_powered else "")).strip("; "),
        }
        saved_attempt.write_text(json.dumps(attempt, indent=2) + "\n", encoding="utf-8")

        row = {
            "edition_id": edition_id,
            "display_name": display_name,
            "iso_filename": meta["iso_filename"],
            "path": meta["path"],
            "artifact_format": artifact_format,
            "size_bytes": meta["size_bytes"],
            "sha256": sha,
            "build_summary_path": summary_path,
            "build_status": summary_status if summary_path else "not_recorded",
            "telemetry_status": telemetry_status,
            "vm_tool": plan["vm_tool"],
            "efi_enabled": plan["efi_enabled"],
            "secure_boot_state": plan["secure_boot_state"],
            "ram_mb": plan["ram_mb"],
            "cpu_cores": plan["cpu_cores"],
            "disk_attached": plan["disk_attached"],
            "boot_menu_reached": menu,
            "kernel_reached": kernel,
            "initramfs_reached": initramfs,
            "display_manager_reached": display,
            "desktop_reached": desktop,
            "desktop_marker_reached": desktop_marker,
            "wallpaper_marker_reached": wallpaper_marker,
            "presentation_lock_reached": presentation_lock,
            "shutdown_marker_reached": effective_shutdown_marker,
            "sddm_autologin_configured": sddm_autologin_configured,
            "session_launch_attempted": session_launch_attempted,
            "wayland_session_attempted": wayland_session_attempted,
            "x11_session_attempted": x11_session_attempted,
            "kwin_started": kwin_started,
            "plasmashell_started": plasmashell_started,
            "user_provisioning_ok": user_provisioning_ok,
            "session_config_failure": session_config_failure,
            "process_observations": process_observations,
            "session_profile": requested_session_profile,
            "selected_session_file": selected_session_file,
            "actual_session_type": actual_session_type,
            "actual_sddm_session_file": actual_sddm_session_file,
            "kernel_cmdline": kernel_cmdline,
            "shutdown_probe_cmdline_confirmed": "bwos.shutdown_probe=1" in kernel_cmdline,
            "shutdown_probe": shutdown_probe_requested,
            "acpi_powerdown_requested": shutdown_requested and not shutdown_probe_requested,
            "qmp_powerdown_sent": qmp_powered,
            "qemu_exited_normally": qemu_exited_normally,
            "forced_termination": forced_termination,
            "session_probe_classification": attempt["session_probe_classification"],
            "session_logs_path": session_logs_path,
            "clean_shutdown_verified": shutdown,
            "classification": classification,
            "failure_point": failure_point or None,
            "boot_log_path": str(saved_console.relative_to(ROOT)),
            "serial_log_path": str(saved_serial.relative_to(ROOT)) if saved_serial.exists() else "",
            "vm_notes": (plan["vm_notes"] + ("; shutdown probe requested" if shutdown_probe_requested else "") + ("; ACPI powerdown sent" if qmp_powered else "")).strip("; "),
            "boot_timestamp": attempt_timestamp,
            "boot_attempts": [attempt],
            "attempt_count": 1,
            "desktop_repeatable": False,
            "repeatability_risk": False,
            "desktop_marker_reached": desktop_marker,
            "wallpaper_marker_reached": wallpaper_marker,
            "presentation_lock_reached": presentation_lock,
            "shutdown_marker_reached": effective_shutdown_marker,
            "session_determinism_class": "NOT_RUN",
            "session_attempt_count": 0,
            "session_desktop_marker_count": 0,
            "session_wallpaper_marker_count": 0,
            "session_presentation_lock_count": 0,
            "session_shutdown_marker_count": 0,
            "session_repeatability_risk": False,
            "shutdown_method": shutdown_method,
        }
        attempt["canonical_update"] = choose_canonical(existing_row, row) is row
        saved_attempt.write_text(json.dumps(attempt, indent=2) + "\n", encoding="utf-8")
        rows.append(normalize_row(row))

    write_outputs(rows, generated_at)
    if FORMAT == "markdown":
        print(render_markdown(rows, generated_at, vm_tool_audit()), end="")
    else:
        print(json.dumps({"generated_at": generated_at, "vm_tool_audit": vm_tool_audit(), "artifacts": rows}, indent=2))
    return 0

def write_outputs(rows: list[dict], generated_at: str) -> list[dict]:
    existing_rows = {
        (str(row.get("edition_id", "")), str(row.get("sha256", ""))): row
        for row in load_existing_rows()
    }
    incoming_rows = {
        (str(row.get("edition_id", "")), str(row.get("sha256", ""))): row
        for row in rows
    }
    merged_rows = []
    for key in sorted(set(existing_rows) | set(incoming_rows), key=lambda item: (
        {edition: index for index, edition in enumerate(EDITION_ORDER)}.get(str(item[0]), len(EDITION_ORDER)),
        str(item[0]),
        str(item[1]),
    )):
        merged_row = merge_rows(existing_rows.get(key), incoming_rows.get(key))
        if merged_row is not None:
            merged_rows.append(merged_row)
    merged_rows = sort_rows(merged_rows)
    audit = vm_tool_audit()
    BOOT_MATRIX_JSON.write_text(
        json.dumps({"generated_at": generated_at, "vm_tool_audit": audit, "artifacts": merged_rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    BOOT_MATRIX_MD.write_text(render_markdown(merged_rows, generated_at, audit), encoding="utf-8")
    BOOT_REPEATABILITY_MD.write_text(render_repeatability(merged_rows, generated_at), encoding="utf-8")
    return merged_rows

def load_existing_rows() -> list[dict]:
    if not BOOT_MATRIX_JSON.exists():
        return []
    try:
        data = json.loads(BOOT_MATRIX_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []
    artifacts = data.get("artifacts", [])
    if not isinstance(artifacts, list):
        return []
    filtered = []
    for row in artifacts:
        if not isinstance(row, dict):
            continue
        edition_id = str(row.get("edition_id", "unknown"))
        if edition_id == "unknown":
            continue
        manifest = ROOT / "editions" / edition_id / "edition.yaml"
        if manifest.exists() and edition_is_archived(manifest):
            continue
        filtered.append(normalize_row(row))
    return filtered

def sort_rows(rows: list[dict]) -> list[dict]:
    order = {edition_id: index for index, edition_id in enumerate(EDITION_ORDER)}

    def key(row: dict) -> tuple[int, str, str]:
        edition_id = str(row.get("edition_id", "unknown"))
        return (
            order.get(edition_id, len(order)),
            edition_id,
            str(row.get("iso_filename", "")),
            str(row.get("sha256", "")),
        )

    return sorted(rows, key=key)

def row_attempts(row: dict) -> list[dict]:
    attempts = row.get("boot_attempts")
    if isinstance(attempts, list) and attempts:
        return [dict(item) for item in attempts if isinstance(item, dict)]
    return [attempt_from_row(row, attempt_label=canonical_attempt_id(row), canonical_update=True)]

def dedupe_attempts(attempts: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for attempt in attempts:
        if not isinstance(attempt, dict):
            continue
        key = (
            str(attempt.get("attempt_label", "")),
            str(attempt.get("attempt_timestamp", "")),
            str(attempt.get("artifact_hash", "")),
            str(attempt.get("result_stage", "")),
            str(attempt.get("console_log_path", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(enrich_attempt_from_logs(attempt))
    return result

def load_evidence_attempts() -> dict[tuple[str, str], list[dict]]:
    grouped: dict[tuple[str, str], list[dict]] = {}
    evidence_root = ISO_DIR / "vm-boot-evidence"
    if not evidence_root.exists():
        return grouped
    for attempt_path in sorted(evidence_root.glob("*/*/attempt.json")):
        try:
            attempt = json.loads(attempt_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(attempt, dict):
            continue
        edition_id = attempt_path.parent.parent.name
        artifact_hash = str(attempt.get("artifact_hash", "") or "")
        if not edition_id or not artifact_hash:
            continue
        grouped.setdefault((edition_id, artifact_hash), []).append(attempt)
    return grouped

def not_tested_row(meta: dict, plan: dict, generated_at: str) -> dict:
    return normalize_row({
        "edition_id": meta["edition_id"],
        "display_name": meta["display_name"],
        "iso_filename": meta["iso_filename"],
        "path": meta["path"],
        "artifact_format": meta["artifact_format"],
        "size_bytes": meta["size_bytes"],
        "sha256": meta["sha256"],
        "build_summary_path": build_summary_path(),
        "build_status": build_status_from_summary(),
        "telemetry_status": telemetry_status_from_summary(),
        "vm_tool": plan["vm_tool"],
        "efi_enabled": plan["efi_enabled"],
        "secure_boot_state": plan["secure_boot_state"],
        "ram_mb": plan["ram_mb"],
        "cpu_cores": plan["cpu_cores"],
        "disk_attached": plan["disk_attached"],
        "boot_menu_reached": False,
        "kernel_reached": False,
        "initramfs_reached": False,
        "display_manager_reached": False,
        "desktop_reached": False,
        "desktop_marker_reached": False,
        "wallpaper_marker_reached": False,
        "presentation_lock_reached": False,
        "shutdown_marker_reached": False,
        "sddm_autologin_configured": False,
        "session_launch_attempted": False,
        "wayland_session_attempted": False,
        "x11_session_attempted": False,
        "kwin_started": False,
        "plasmashell_started": False,
        "user_provisioning_ok": None,
        "session_config_failure": False,
        "session_profile": "",
        "selected_session_file": "",
        "actual_session_type": "",
        "actual_sddm_session_file": "",
        "kernel_cmdline": "",
        "shutdown_probe_cmdline_confirmed": False,
        "shutdown_probe": False,
        "session_probe_classification": "NOT_RUN",
        "session_logs_path": "",
        "clean_shutdown_verified": False,
        "classification": "BLOCKED_BY_VM_TOOLING" if plan["tooling_blocked"] else "NOT_TESTED",
        "failure_point": "vm_tooling" if plan["tooling_blocked"] else "",
        "boot_log_path": "",
        "serial_log_path": "",
        "vm_notes": plan["vm_notes"],
        "boot_timestamp": generated_at,
        "boot_attempts": [],
        "attempt_count": 0,
        "desktop_repeatable": False,
        "repeatability_risk": False,
        "session_determinism_class": "NOT_RUN",
        "session_attempt_count": 0,
        "session_desktop_marker_count": 0,
        "session_wallpaper_marker_count": 0,
        "session_presentation_lock_count": 0,
        "session_shutdown_marker_count": 0,
        "session_repeatability_risk": False,
        "shutdown_method": "",
        "desktop_marker_attempt_count": 0,
        "wallpaper_marker_attempt_count": 0,
        "presentation_lock_attempt_count": 0,
        "shutdown_marker_attempt_count": 0,
        "clean_shutdown_attempt_count": 0,
        "desktop_shutdown_same_attempt": False,
        "desktop_wallpaper_shutdown_same_attempt": False,
        "clean_shutdown_after_desktop": False,
    })

def row_from_artifact_and_evidence(meta: dict, plan: dict, attempts: list[dict], generated_at: str) -> dict:
    row = not_tested_row(meta, plan, generated_at)
    clean_attempts = dedupe_attempts(attempts)
    if not clean_attempts:
        return row
    summary = summarize_boot_attempts(clean_attempts)
    session_summary = summarize_session_attempts(clean_attempts)
    row["boot_attempts"] = clean_attempts
    row["attempt_count"] = summary["attempt_count"]
    row["desktop_repeatable"] = summary["desktop_repeatable"]
    row["repeatability_risk"] = summary["repeatability_risk"]
    row["shutdown_method"] = summary["shutdown_method"]
    row = apply_canonical_attempt_evidence(row, clean_attempts, summary)
    row["session_determinism_class"] = session_summary["session_determinism_class"]
    row["session_attempt_count"] = session_summary["attempt_count"]
    row["session_desktop_marker_count"] = session_summary["desktop_marker_count"]
    row["session_wallpaper_marker_count"] = session_summary["wallpaper_marker_count"]
    row["session_presentation_lock_count"] = session_summary.get("presentation_lock_count", 0)
    row["session_shutdown_marker_count"] = session_summary["shutdown_marker_count"]
    row["session_repeatability_risk"] = session_summary["repeatability_risk"]
    profile_attempts = [
        attempt for attempt in clean_attempts
        if str(attempt.get("attempt_label", "")).startswith(PR39F_PREFIX)
        or str(attempt.get("attempt_label", "")).startswith(PR39I_PREFIX)
        or str(attempt.get("session_profile", "")) in {"wayland", "x11"}
    ]
    row["session_probe_classification"] = session_probe_classification(profile_attempts)
    row["session_launch_attempted"] = any(bool(a.get("session_launch_attempted", False)) for a in clean_attempts)
    row["wayland_session_attempted"] = any(bool(a.get("wayland_session_attempted", False)) for a in clean_attempts)
    row["x11_session_attempted"] = any(bool(a.get("x11_session_attempted", False)) for a in clean_attempts)
    row["kwin_started"] = any(bool(a.get("kwin_started", False)) for a in clean_attempts)
    row["plasmashell_started"] = any(bool(a.get("plasmashell_started", False)) for a in clean_attempts)
    row["sddm_autologin_configured"] = any(bool(a.get("sddm_autologin_configured", False)) for a in clean_attempts)
    row["session_config_failure"] = any(bool(a.get("session_config_failure", False)) for a in clean_attempts)
    row["shutdown_probe_cmdline_confirmed"] = any(bool(a.get("shutdown_probe_cmdline_confirmed", False)) for a in clean_attempts)
    row["boot_timestamp"] = clean_attempts[-1].get("attempt_timestamp", generated_at)
    return normalize_row(row)

def attempt_sort_key(attempt: dict) -> tuple[int, str, str]:
    return (
        0,
        str(attempt.get("attempt_timestamp", "")),
        str(attempt.get("attempt_label", "")),
    )

def merge_rows(existing: dict | None, incoming: dict | None) -> dict | None:
    if existing is None and incoming is None:
        return None
    if existing is None:
        merged = dict(incoming)
        merged["boot_attempts"] = dedupe_attempts(row_attempts(incoming))
        summary = summarize_boot_attempts(merged["boot_attempts"])
        merged.update(summary)
        merged = apply_canonical_attempt_evidence(merged, merged["boot_attempts"], summary)
        merged["attempt_count"] = len(merged["boot_attempts"])
        merged["boot_timestamp"] = merged.get("boot_timestamp") or merged["boot_attempts"][-1].get("attempt_timestamp", "")
        return normalize_row(merged)
    if incoming is None:
        merged = dict(existing)
        merged["boot_attempts"] = dedupe_attempts(row_attempts(existing))
        summary = summarize_boot_attempts(merged["boot_attempts"])
        merged.update(summary)
        merged = apply_canonical_attempt_evidence(merged, merged["boot_attempts"], summary)
        merged["attempt_count"] = len(merged["boot_attempts"])
        merged["boot_timestamp"] = merged.get("boot_timestamp") or merged["boot_attempts"][-1].get("attempt_timestamp", "")
        return normalize_row(merged)

    existing_attempts = row_attempts(existing)
    incoming_attempts = row_attempts(incoming)
    all_attempts = dedupe_attempts(existing_attempts + incoming_attempts)
    all_attempts = sorted(all_attempts, key=attempt_sort_key)
    canonical = choose_canonical(existing, incoming)
    merged = dict(canonical or incoming or existing)
    summary = summarize_boot_attempts(all_attempts)
    session_summary = summarize_session_attempts(all_attempts)
    merged["boot_attempts"] = all_attempts
    merged["attempt_count"] = summary["attempt_count"]
    merged["desktop_repeatable"] = summary["desktop_repeatable"]
    merged["repeatability_risk"] = summary["repeatability_risk"]
    merged["shutdown_method"] = summary["shutdown_method"]
    merged = apply_canonical_attempt_evidence(merged, all_attempts, summary)
    merged["session_determinism_class"] = session_summary["session_determinism_class"]
    merged["session_attempt_count"] = session_summary["attempt_count"]
    merged["session_desktop_marker_count"] = session_summary["desktop_marker_count"]
    merged["session_wallpaper_marker_count"] = session_summary["wallpaper_marker_count"]
    merged["session_presentation_lock_count"] = session_summary.get("presentation_lock_count", 0)
    merged["session_shutdown_marker_count"] = session_summary["shutdown_marker_count"]
    merged["session_repeatability_risk"] = session_summary["repeatability_risk"]
    profile_attempts = [
        attempt
        for attempt in all_attempts
        if str(attempt.get("attempt_label", "")).startswith(PR39F_PREFIX)
        or str(attempt.get("attempt_label", "")).startswith(PR39I_PREFIX)
        or str(attempt.get("session_profile", "")) in {"wayland", "x11"}
    ]
    merged["session_probe_classification"] = session_probe_classification(profile_attempts)
    merged["session_launch_attempted"] = any(bool(a.get("session_launch_attempted", False)) for a in all_attempts)
    merged["wayland_session_attempted"] = any(bool(a.get("wayland_session_attempted", False)) for a in all_attempts)
    merged["x11_session_attempted"] = any(bool(a.get("x11_session_attempted", False)) for a in all_attempts)
    merged["actual_session_type"] = next(
        (str(a.get("actual_session_type", "")) for a in reversed(all_attempts) if str(a.get("actual_session_type", ""))),
        str(merged.get("actual_session_type", "") or ""),
    )
    merged["actual_sddm_session_file"] = next(
        (str(a.get("actual_sddm_session_file", "")) for a in reversed(all_attempts) if str(a.get("actual_sddm_session_file", ""))),
        str(merged.get("actual_sddm_session_file", "") or ""),
    )
    merged["kernel_cmdline"] = next(
        (str(a.get("kernel_cmdline", "")) for a in reversed(all_attempts) if str(a.get("kernel_cmdline", ""))),
        str(merged.get("kernel_cmdline", "") or ""),
    )
    merged["shutdown_probe_cmdline_confirmed"] = any(bool(a.get("shutdown_probe_cmdline_confirmed", False)) for a in all_attempts)
    merged["kwin_started"] = any(bool(a.get("kwin_started", False)) for a in all_attempts)
    merged["plasmashell_started"] = any(bool(a.get("plasmashell_started", False)) for a in all_attempts)
    merged["sddm_autologin_configured"] = any(bool(a.get("sddm_autologin_configured", False)) for a in all_attempts)
    merged["session_config_failure"] = any(bool(a.get("session_config_failure", False)) for a in all_attempts)
    user_values = [a.get("user_provisioning_ok") for a in all_attempts if a.get("user_provisioning_ok") is not None]
    merged["user_provisioning_ok"] = all(bool(value) for value in user_values) if user_values else None
    merged["boot_timestamp"] = (
        merged.get("boot_timestamp")
        or extract_timestamp_from_text(str(merged.get("boot_log_path", "")))
        or extract_timestamp_from_text(str(merged.get("serial_log_path", "")))
        or (all_attempts[-1].get("attempt_timestamp", "") if all_attempts else "")
    )
    if merged.get("classification") == "BOOT_PASS_DESKTOP" and not merged.get("clean_shutdown_verified"):
        merged["failure_point"] = merged.get("failure_point") or "shutdown"
    if merged.get("classification") != "BOOT_PASS_DESKTOP" and summary["shutdown_clean"]:
        merged["clean_shutdown_verified"] = True
    return normalize_row(merged)

if __name__ == "__main__":
    raise SystemExit(main())
PY
