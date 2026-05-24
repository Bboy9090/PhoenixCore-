#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST="$ROOT/iso/outputs/manifest.json"
BOOT_MATRIX="$ROOT/iso/outputs/vm-boot-matrix.json"

errors=0
warnings=0

error() {
  printf 'ERROR: %s\n' "$*" >&2
  errors=$((errors + 1))
}

warn() {
  printf 'WARN: %s\n' "$*" >&2
  warnings=$((warnings + 1))
}

info() {
  printf 'INFO: %s\n' "$*"
}

if [ ! -f "$MANIFEST" ]; then
  error "Missing registry manifest: $MANIFEST"
fi

if [ ! -f "$BOOT_MATRIX" ]; then
  error "Missing VM boot matrix: $BOOT_MATRIX"
fi

if [ "$errors" -gt 0 ]; then
  printf '\nBoot matrix validation summary: %s error(s), %s warning(s)\n' "$errors" "$warnings" >&2
  exit 1
fi

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

python3 - "$MANIFEST" "$BOOT_MATRIX" "$ROOT" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
matrix_path = Path(sys.argv[2])
root = Path(sys.argv[3])

def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)

def strength_score(classification: str, shutdown_verified: bool) -> int:
    strength = {
        "NOT_TESTED": 0,
        "BLOCKED_BY_VM_TOOLING": 0,
        "BOOT_FAIL_KERNEL": 1,
        "BOOT_FAIL_INITRAMFS": 2,
        "BOOT_FAIL_DISPLAY": 3,
        "BOOT_PASS_BOOTLOADER_ONLY": 4,
        "BOOT_PASS_DESKTOP": 5,
    }.get(classification, 0)
    return strength * 2 + (1 if shutdown_verified else 0)

def summarize_attempts(attempts):
    attempts = [item for item in attempts if isinstance(item, dict)]
    strengths = {strength_score(str(a.get("result_stage", "NOT_TESTED")), as_bool(a.get("clean_shutdown_verified"))) for a in attempts}
    classifications = {str(a.get("result_stage", "NOT_TESTED")) for a in attempts}
    desktop_repeatable = bool(attempts) and all(as_bool(a.get("desktop_reached")) for a in attempts)
    shutdown_clean = any(as_bool(a.get("clean_shutdown_verified")) for a in attempts)
    repeatability_risk = len(strengths) > 1 or len(classifications) > 1
    return {
        "attempt_count": len(attempts),
        "desktop_repeatable": desktop_repeatable,
        "shutdown_clean": shutdown_clean,
        "repeatability_risk": repeatability_risk,
        "max_strength": max(strengths) if strengths else 0,
    }

manifest = load_json(manifest_path)
matrix = load_json(matrix_path)

manifest_artifacts = manifest.get("artifacts", [])
matrix_artifacts = matrix.get("artifacts", [])

matrix_by_sha = {}
matrix_by_key = {}
for row in matrix_artifacts:
    if not isinstance(row, dict):
        continue
    sha = str(row.get("sha256", ""))
    edition_id = str(row.get("edition_id", ""))
    matrix_by_sha.setdefault(sha, []).append(row)
    matrix_by_key[(edition_id, sha)] = row

errors = 0
warnings = 0

def error(msg):
    nonlocal_errors[0] += 1
    print(f"ERROR: {msg}", file=sys.stderr)

def warn(msg):
    nonlocal_warnings[0] += 1
    print(f"WARN: {msg}", file=sys.stderr)

nonlocal_errors = [0]
nonlocal_warnings = [0]

if "vm_tool_audit" not in matrix:
    warn("VM tool audit block is missing from vm-boot-matrix.json")

for artifact in manifest_artifacts:
    if not isinstance(artifact, dict):
        continue

    edition_id = str(artifact.get("edition_id", "unknown"))
    path = str(artifact.get("path", ""))
    sha = str(artifact.get("sha256", ""))
    size_bytes = int(artifact.get("size_bytes", 0) or 0)
    artifact_format = str(artifact.get("artifact_format", "unknown"))
    status = artifact.get("status", [])
    status = status if isinstance(status, list) else []
    release_candidate = "release_candidate" in status
    release_blocked = "release_blocked" in status

    file_path = root / path
    if not file_path.exists():
        error(f"Missing artifact file for {edition_id}: {path}")
        continue

    current_sha = file_sha(file_path)
    if current_sha != sha:
        error(f"Checksum mismatch for {edition_id}: registry={sha} file={current_sha}")

    if int(file_path.stat().st_size) != size_bytes:
        error(f"Size mismatch for {edition_id}: registry={size_bytes} file={file_path.stat().st_size}")

    boot_rows = matrix_by_sha.get(sha, [])
    if not boot_rows:
        error(f"Missing VM boot status for {edition_id} ({path})")
        continue

    boot_row = matrix_by_key.get((edition_id, sha), boot_rows[0])
    if not boot_row:
        error(f"Unable to resolve VM boot row for {edition_id} ({sha})")
        continue

    boot_format = str(boot_row.get("artifact_format", "unknown"))
    boot_path = str(boot_row.get("path", ""))
    boot_size = int(boot_row.get("size_bytes", 0) or 0)
    summary_path = str(artifact.get("build_summary_path", "") or boot_row.get("build_summary_path", ""))
    build_status = str(artifact.get("build_status", "") or boot_row.get("build_status", ""))
    telemetry_status = str(artifact.get("telemetry_status", "") or boot_row.get("telemetry_status", ""))
    classification = str(boot_row.get("classification", "NOT_TESTED"))
    menu = as_bool(boot_row.get("boot_menu_reached"))
    kernel = as_bool(boot_row.get("kernel_reached"))
    initramfs = as_bool(boot_row.get("initramfs_reached"))
    display = as_bool(boot_row.get("display_manager_reached"))
    desktop = as_bool(boot_row.get("desktop_reached"))
    shutdown = as_bool(boot_row.get("clean_shutdown_verified"))
    failure_point = str(boot_row.get("failure_point", "") or "")
    attempts = boot_row.get("boot_attempts", [])
    attempts = attempts if isinstance(attempts, list) else []
    attempt_summary = summarize_attempts(attempts)
    canonical_strength = strength_score(classification, shutdown)

    if boot_format != artifact_format:
        warn(f"Format mismatch for {edition_id}: registry={artifact_format} boot={boot_format}")

    if boot_size and boot_size != size_bytes:
        warn(f"Boot matrix size mismatch for {edition_id}: registry={size_bytes} boot={boot_size}")

    if summary_path:
        if telemetry_status == "recorded" and not (root / summary_path).exists():
            error(f"Recorded telemetry missing summary file for {edition_id}: {summary_path}")
        if build_status == "not_recorded" and telemetry_status == "recorded":
            error(f"Telemetry status inconsistent with build status for {edition_id}")
    else:
        error(f"Missing build summary path for {edition_id}")

    if classification == "BOOT_PASS_DESKTOP":
        if not (menu and kernel and initramfs and display and desktop and shutdown):
            if not (menu and kernel and initramfs and display and desktop):
                error(f"Desktop pass lacks full stage evidence for {edition_id}")
            elif not shutdown:
                warn(f"Desktop pass reached without clean shutdown verification for {edition_id}")
    elif classification == "BOOT_PASS_BOOTLOADER_ONLY":
        if not menu or any([kernel, initramfs, display, desktop, shutdown]):
            error(f"Bootloader-only classification is inconsistent for {edition_id}")
    elif classification == "BOOT_FAIL_KERNEL":
        if menu:
            error(f"Kernel failure should not report boot menu reached for {edition_id}")
    elif classification == "BOOT_FAIL_INITRAMFS":
        if not menu or not kernel or initramfs:
            error(f"Initramfs failure stage evidence is inconsistent for {edition_id}")
    elif classification == "BOOT_FAIL_DISPLAY":
        if not menu or not kernel or not initramfs or not display or desktop:
            error(f"Display failure stage evidence is inconsistent for {edition_id}")
    elif classification in {"NOT_TESTED", "BLOCKED_BY_VM_TOOLING"}:
        if release_candidate:
            error(f"Untested artifact cannot be release candidate: {edition_id}")
    else:
        warn(f"Unknown boot classification for {edition_id}: {classification}")

    if release_candidate and classification not in {"BOOT_PASS_DESKTOP", "BOOT_PASS_BOOTLOADER_ONLY"}:
        error(f"Release candidate requires a boot pass classification: {edition_id}")

    if release_blocked and classification == "BOOT_PASS_DESKTOP":
        warn(f"Artifact is boot-pass but still release-blocked: {edition_id}")

    if classification not in {"NOT_TESTED", "BLOCKED_BY_VM_TOOLING"} and not boot_path:
        error(f"Boot matrix row is missing artifact path for {edition_id}")

    if failure_point == "not_tested" and classification not in {"NOT_TESTED", "BLOCKED_BY_VM_TOOLING"}:
        warn(f"Failure point not recorded for {edition_id}")

    # Monotonic stage sanity: later stages imply earlier stages.
    if kernel and not menu:
        error(f"Kernel reached without boot menu for {edition_id}")
    if initramfs and not kernel:
        error(f"Initramfs reached without kernel for {edition_id}")
    if display and not initramfs:
        error(f"Display manager reached without initramfs for {edition_id}")
    if desktop and not display:
        error(f"Desktop reached without display manager for {edition_id}")
    if shutdown and not desktop:
        error(f"Shutdown verified without desktop for {edition_id}")

    if classification == "BOOT_PASS_BOOTLOADER_ONLY" and failure_point not in {"kernel", "bootloader"}:
        warn(f"Bootloader-only failure point should be kernel/bootloader for {edition_id}: {failure_point}")

    if attempts:
        if int(boot_row.get("attempt_count", 0) or 0) != attempt_summary["attempt_count"]:
            error(f"Attempt count mismatch for {edition_id}")
        if as_bool(boot_row.get("desktop_repeatable")) != attempt_summary["desktop_repeatable"]:
            error(f"Desktop repeatability summary mismatch for {edition_id}")
        if as_bool(boot_row.get("repeatability_risk")) != attempt_summary["repeatability_risk"]:
            error(f"Repeatability risk summary mismatch for {edition_id}")
        if as_bool(boot_row.get("clean_shutdown_verified")) != attempt_summary["shutdown_clean"]:
            error(f"Shutdown summary mismatch for {edition_id}")
        if canonical_strength < attempt_summary["max_strength"]:
            error(f"Canonical boot row is weaker than at least one attempt for {edition_id}")
        if attempt_summary["repeatability_risk"] and not as_bool(boot_row.get("repeatability_risk")):
            error(f"Contradictory attempts must set repeatability_risk=true for {edition_id}")
        if attempt_summary["shutdown_clean"] and not as_bool(boot_row.get("clean_shutdown_verified")):
            error(f"Clean shutdown evidence exists but canonical row is not marked clean for {edition_id}")

        session_attempts = [a for a in attempts if str(a.get("attempt_label", "")).startswith("PR39E-")]
        if session_attempts:
            session_count = len(session_attempts)
            desktop_marker_count = sum(as_bool(a.get("desktop_marker_reached")) for a in session_attempts)
            shutdown_marker_count = sum(as_bool(a.get("shutdown_marker_reached")) for a in session_attempts)
            session_class = str(boot_row.get("session_determinism_class", "NOT_RUN"))
            session_attempt_count = int(boot_row.get("session_attempt_count", 0) or 0)
            session_desktop_marker_count = int(boot_row.get("session_desktop_marker_count", 0) or 0)
            session_shutdown_marker_count = int(boot_row.get("session_shutdown_marker_count", 0) or 0)
            session_repeatability_risk = as_bool(boot_row.get("session_repeatability_risk"))

            if session_attempt_count != session_count:
                error(f"Session attempt count mismatch for {edition_id}")
            if session_desktop_marker_count != desktop_marker_count:
                error(f"Session desktop-marker count mismatch for {edition_id}")
            if session_shutdown_marker_count != shutdown_marker_count:
                error(f"Session shutdown-marker count mismatch for {edition_id}")

            if session_class not in {"PASS", "PARTIAL", "FAIL", "NOT_RUN"}:
                error(f"Unexpected session determinism class for {edition_id}: {session_class}")
            elif session_class == "PASS" and desktop_marker_count != 3:
                error(f"Session determinism PASS requires 3/3 desktop markers for {edition_id}")
            elif session_class == "PARTIAL" and desktop_marker_count not in {1, 2}:
                error(f"Session determinism PARTIAL requires 1-2 desktop markers for {edition_id}")
            elif session_class == "FAIL" and desktop_marker_count != 0:
                error(f"Session determinism FAIL requires 0 desktop markers for {edition_id}")

            if session_class in {"PASS", "PARTIAL", "FAIL"} and session_attempt_count != 3:
                warn(f"Session determinism for {edition_id} is based on {session_attempt_count}/3 attempts")

            if session_class == "PASS" and session_repeatability_risk:
                error(f"Session determinism PASS cannot carry repeatability risk for {edition_id}")
            if session_class == "PASS" and shutdown_marker_count == 0:
                error(f"Session determinism PASS requires shutdown marker evidence for {edition_id}")
            if any(as_bool(a.get("clean_shutdown_verified")) for a in session_attempts) and shutdown_marker_count == 0:
                error(f"Session clean shutdown evidence exists without a shutdown marker for {edition_id}")

summary = f"Boot matrix validation summary: {nonlocal_errors[0]} error(s), {nonlocal_warnings[0]} warning(s)"
print(summary)
if nonlocal_errors[0]:
    sys.exit(1)
PY
