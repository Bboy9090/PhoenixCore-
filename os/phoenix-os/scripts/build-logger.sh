#!/usr/bin/env bash
# Shared build telemetry helpers for BWOS / Blue Phoenix OS.
#
# This file is intended to be sourced by build orchestration scripts.
# It records structured build events, phase transitions, warnings,
# failures, and final summaries without faking progress or status.

set -euo pipefail

phoenix_build_logger_now_iso() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

phoenix_build_logger_state_set() {
    local key="$1"
    local value="$2"

    if [ -z "${PHOENIX_BUILD_STATE_JSON:-}" ]; then
        return 0
    fi

    python3 - "$PHOENIX_BUILD_STATE_JSON" "$key" "$value" <<'PY'
import json
import os
import sys

state_path, key, raw_value = sys.argv[1:4]

try:
    value = json.loads(raw_value)
except Exception:
    value = raw_value

state = {}
if os.path.exists(state_path):
    with open(state_path, "r", encoding="utf-8") as handle:
        try:
            state = json.load(handle)
        except Exception:
            state = {}

state[key] = value
tmp_path = f"{state_path}.tmp"
with open(tmp_path, "w", encoding="utf-8") as handle:
    json.dump(state, handle, indent=2, sort_keys=True)
    handle.write("\n")
os.replace(tmp_path, state_path)
PY
}

phoenix_build_logger_state_get() {
    local key="$1"

    if [ -z "${PHOENIX_BUILD_STATE_JSON:-}" ] || [ ! -f "$PHOENIX_BUILD_STATE_JSON" ]; then
        return 1
    fi

    python3 - "$PHOENIX_BUILD_STATE_JSON" "$key" <<'PY'
import json
import os
import sys

state_path, key = sys.argv[1:3]
with open(state_path, "r", encoding="utf-8") as handle:
    state = json.load(handle)
value = state.get(key, "")
if value is None:
    value = ""
if isinstance(value, (dict, list)):
    print(json.dumps(value, sort_keys=True))
else:
    print(value)
PY
}

phoenix_build_logger_state_sync_shell() {
    if [ -z "${PHOENIX_BUILD_STATE_JSON:-}" ] || [ ! -f "$PHOENIX_BUILD_STATE_JSON" ]; then
        return 0
    fi

    eval "$(
        python3 - "$PHOENIX_BUILD_STATE_JSON" <<'PY'
import json
import os
import shlex
import sys

state_path = sys.argv[1]
with open(state_path, "r", encoding="utf-8") as handle:
    state = json.load(handle)

keys = [
    "PHOENIX_BUILD_ID",
    "PHOENIX_BUILD_EDITION_ID",
    "PHOENIX_BUILD_EDITION_NAME",
    "PHOENIX_BUILD_ARCHITECTURE",
    "PHOENIX_BUILD_ARTIFACT_TARGET",
    "PHOENIX_BUILD_MODE",
    "PHOENIX_BUILD_MANIFEST_PATH",
    "PHOENIX_BUILD_SOURCE_COMMIT",
    "PHOENIX_BUILD_TELEMETRY_DIR",
    "PHOENIX_BUILD_STATUS",
    "PHOENIX_BUILD_FAILURE_CLASS",
    "PHOENIX_BUILD_CURRENT_PHASE",
    "PHOENIX_BUILD_PHASE_STARTED_AT",
    "PHOENIX_BUILD_LAST_SUCCESSFUL_PHASE",
    "PHOENIX_BUILD_START_TIME",
    "PHOENIX_BUILD_UPDATED_AT",
    "PHOENIX_BUILD_LAST_WARNING",
    "PHOENIX_BUILD_LAST_ERROR",
    "PHOENIX_BUILD_WARNING_COUNT",
    "PHOENIX_BUILD_FAILURE_COUNT",
    "PHOENIX_BUILD_HEARTBEAT_COUNT",
    "PHOENIX_BUILD_LAST_HEARTBEAT_AT",
    "PHOENIX_BUILD_ARTIFACT_PATH",
    "PHOENIX_BUILD_ARTIFACT_SHA256",
    "PHOENIX_BUILD_ARTIFACT_SIZE_BYTES",
    "PHOENIX_BUILD_SUMMARY_GENERATED_AT",
]

for key in keys:
    value = state.get(key, "")
    if value is None:
        value = ""
    print(f"export {key}={shlex.quote(str(value))}")
PY
    )"
}

phoenix_build_logger_phase_close() {
    local phase_status="${1:-completed}"
    local end_iso
    end_iso="$(phoenix_build_logger_now_iso)"

    if [ -z "${PHOENIX_BUILD_STATE_JSON:-}" ] || [ ! -f "$PHOENIX_BUILD_STATE_JSON" ]; then
        return 0
    fi

    python3 - "$PHOENIX_BUILD_STATE_JSON" "$PHOENIX_BUILD_PHASE_TIMINGS" "$phase_status" "$end_iso" <<'PY'
import datetime as dt
import json
import os
import sys

state_path, timings_path, phase_status, end_iso = sys.argv[1:5]

with open(state_path, "r", encoding="utf-8") as handle:
    state = json.load(handle)

phase = state.get("PHOENIX_BUILD_CURRENT_PHASE", "")
phase_started_at = state.get("PHOENIX_BUILD_PHASE_STARTED_AT", "")
if not phase or not phase_started_at:
    state["PHOENIX_BUILD_UPDATED_AT"] = end_iso
    tmp_path = f"{state_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp_path, state_path)
    sys.exit(0)

def parse_iso(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))

started = parse_iso(phase_started_at)
ended = parse_iso(end_iso)
duration = max(0, int((ended - started).total_seconds()))

os.makedirs(os.path.dirname(timings_path), exist_ok=True)
with open(timings_path, "a", encoding="utf-8") as handle:
    handle.write(f"{phase}\t{phase_started_at}\t{end_iso}\t{duration}\t{phase_status}\n")

if phase_status == "completed":
    state["PHOENIX_BUILD_LAST_SUCCESSFUL_PHASE"] = phase

state["PHOENIX_BUILD_UPDATED_AT"] = end_iso
tmp_path = f"{state_path}.tmp"
with open(tmp_path, "w", encoding="utf-8") as handle:
    json.dump(state, handle, indent=2, sort_keys=True)
    handle.write("\n")
os.replace(tmp_path, state_path)
PY

    if [ "$phase_status" = "completed" ]; then
        PHOENIX_BUILD_LAST_SUCCESSFUL_PHASE="$(
            python3 - "$PHOENIX_BUILD_STATE_JSON" <<'PY'
import json
import os
import sys

path = sys.argv[1]
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    print(state.get("PHOENIX_BUILD_LAST_SUCCESSFUL_PHASE", ""))
PY
        )"
    fi
    PHOENIX_BUILD_UPDATED_AT="$end_iso"
}

phoenix_build_logger_event() {
    local event_type="$1"
    local level="$2"
    local phase="$3"
    local message="$4"
    local details_json="${5:-null}"
    local timestamp
    timestamp="$(phoenix_build_logger_now_iso)"

    if [ -z "${PHOENIX_BUILD_EVENT_LOG:-}" ] || [ -z "${PHOENIX_BUILD_HUMAN_LOG:-}" ]; then
        return 0
    fi

    python3 - \
        "$PHOENIX_BUILD_EVENT_LOG" \
        "$PHOENIX_BUILD_HUMAN_LOG" \
        "$timestamp" \
        "${PHOENIX_BUILD_ID:-}" \
        "${PHOENIX_BUILD_EDITION_ID:-}" \
        "${PHOENIX_BUILD_EDITION_NAME:-}" \
        "${PHOENIX_BUILD_ARCHITECTURE:-}" \
        "${PHOENIX_BUILD_ARTIFACT_TARGET:-}" \
        "$event_type" \
        "$level" \
        "$phase" \
        "$message" \
        "$details_json" <<'PY'
import datetime as dt
import json
import os
import sys

event_path, human_path, timestamp, build_id, edition_id, edition_name, architecture, artifact_target, event_type, level, phase, message, details_raw = sys.argv[1:14]

try:
    details = json.loads(details_raw)
except Exception:
    details = details_raw

payload = {
    "timestamp": timestamp,
    "build_id": build_id,
    "edition_id": edition_id,
    "edition_name": edition_name,
    "architecture": architecture,
    "artifact_target": artifact_target,
    "event_type": event_type,
    "level": level,
    "phase": phase,
    "message": message,
    "details": details,
}

os.makedirs(os.path.dirname(event_path), exist_ok=True)
with open(event_path, "a", encoding="utf-8") as event_handle:
    event_handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
with open(human_path, "a", encoding="utf-8") as human_handle:
    human_handle.write(f"[{timestamp}] [{level}] [{phase}] {message}\n")
PY
}

phoenix_build_logger_warning() {
    local message="$1"
    local phase="${2:-${PHOENIX_BUILD_CURRENT_PHASE:-unknown}}"
    local timestamp
    timestamp="$(phoenix_build_logger_now_iso)"

    phoenix_build_logger_event "warning" "warn" "$phase" "$message"
    phoenix_build_logger_state_set "PHOENIX_BUILD_LAST_WARNING" "$message"
    phoenix_build_logger_state_set "PHOENIX_BUILD_WARNING_COUNT" "$(
        python3 - "$PHOENIX_BUILD_STATE_JSON" <<'PY'
import json
import os
import sys

path = sys.argv[1]
state = {}
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as handle:
        state = json.load(handle)
count = int(state.get("PHOENIX_BUILD_WARNING_COUNT", 0) or 0) + 1
print(count)
PY
    )"
    PHOENIX_BUILD_LAST_WARNING="$message"
    PHOENIX_BUILD_WARNING_COUNT="$(( ${PHOENIX_BUILD_WARNING_COUNT:-0} + 1 ))"
    if [ -n "${PHOENIX_BUILD_WARNINGS_LOG:-}" ]; then
        printf '%s\t[%s] %s\n' "$timestamp" "$phase" "$message" >>"$PHOENIX_BUILD_WARNINGS_LOG"
    fi
}

phoenix_build_logger_error() {
    local message="$1"
    local phase="${2:-${PHOENIX_BUILD_CURRENT_PHASE:-unknown}}"
    local failure_class="${3:-unknown_failure}"
    local timestamp
    timestamp="$(phoenix_build_logger_now_iso)"

    phoenix_build_logger_event "error" "error" "$phase" "$message" "{\"failure_class\":\"$failure_class\"}"
    phoenix_build_logger_state_set "PHOENIX_BUILD_LAST_ERROR" "$message"
    phoenix_build_logger_state_set "PHOENIX_BUILD_FAILURE_CLASS" "$failure_class"
    phoenix_build_logger_state_set "PHOENIX_BUILD_FAILURE_COUNT" "$(
        python3 - "$PHOENIX_BUILD_STATE_JSON" <<'PY'
import json
import os
import sys

path = sys.argv[1]
state = {}
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as handle:
        state = json.load(handle)
count = int(state.get("PHOENIX_BUILD_FAILURE_COUNT", 0) or 0) + 1
print(count)
PY
    )"
    PHOENIX_BUILD_LAST_ERROR="$message"
    PHOENIX_BUILD_FAILURE_CLASS="$failure_class"
    PHOENIX_BUILD_FAILURE_COUNT="$(( ${PHOENIX_BUILD_FAILURE_COUNT:-0} + 1 ))"
    if [ -n "${PHOENIX_BUILD_FAILURES_LOG:-}" ]; then
        printf '%s\t[%s] %s\t%s\n' "$timestamp" "$phase" "$failure_class" "$message" >>"$PHOENIX_BUILD_FAILURES_LOG"
    fi
}

phoenix_build_logger_artifact_event() {
    local event_name="$1"
    local message="$2"
    local details_json="${3:-null}"
    local phase="${4:-artifact_registration}"
    phoenix_build_logger_event "artifact" "info" "$phase" "$message" "$details_json"
    if [ "$event_name" = "artifact created" ] || [ "$event_name" = "artifact_copied" ]; then
        phoenix_build_logger_state_set "PHOENIX_BUILD_ARTIFACT_PATH" "$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("path",""))' "$details_json" 2>/dev/null || true)"
    fi
}

phoenix_build_logger_detect_phase_from_line() {
    local line="$1"
    case "$line" in
        *"lb bootstrap"*|*"bootstrap_debian"*) echo "debootstrap" ;;
        *"lb chroot_install-packages"*) echo "chroot_install" ;;
        *"lb chroot_package-lists"*) echo "package_resolution" ;;
        *"lb chroot_hooks"*) echo "package_configuration" ;;
        *"lb chroot_hacks"*) echo "initramfs_generation" ;;
        *"lb binary_rootfs"*) echo "filesystem_assembly" ;;
        *"lb binary_iso"*) echo "iso_or_img_assembly" ;;
        *"lb binary_checksums"*) echo "checksum_generation" ;;
        *"lb chroot_archives"*) echo "cleanup" ;;
        *"lb chroot_apt"*) echo "cleanup" ;;
        *"P: Preparing squashfs image"*|*"mksquashfs"*) echo "filesystem_assembly" ;;
        *"update-initramfs"*) echo "initramfs_generation" ;;
        *"Converting phoenix-logo-boot.svg"*|*"Setting Plymouth theme to phoenix"*|*"Configuring SDDM theme to phoenix"*|*"Configuring custom desktop wallpaper"*|*"bwos-heartbeat.service"*) echo "branding_hooks" ;;
        *"Installer stage completed"*) echo "cleanup" ;;
        *) return 1 ;;
    esac
}

phoenix_build_logger_classify_failure_line() {
    local line="$1"
    local phase="${2:-${PHOENIX_BUILD_CURRENT_PHASE:-unknown}}"

    case "$line" in
        *"Could not resolve"*|*"Temporary failure resolving"*|*"Network is unreachable"*|*"Connection timed out"*|*"Failed to fetch"*|*"TLS handshake timeout"*|*"no route to host"*)
            echo "network_failure"
            return 0
            ;;
        *"Unable to locate package"*|*"Package has no installation candidate"*|*"E: Couldn't find any package"*|*"dependency problems"*|*"unmet dependencies"*)
            echo "package_resolution_failure"
            return 0
            ;;
        *"Could not get lock"*|*"is another process using it"*|*"dpkg frontend lock"*|*"Unable to lock the administration directory"*)
            echo "apt_lock_failure"
            return 0
            ;;
        *"update-initramfs"*|*"initramfs"*|*"dracut"*|*"mkinitramfs"*)
            echo "initramfs_failure"
            return 0
            ;;
        *"xorriso"*|*"binary_iso"*|*"mksquashfs"*|*"squashfs"*|*"iso generation"*)
            echo "iso_assembly_failure"
            return 0
            ;;
        *"Failed to copy artifact"*|*"Artifact missing"*)
            echo "artifact_missing"
            return 0
            ;;
        *"Plymouth"*|*"SDDM"*|*"wallpaper"*|*"logo"*|*"branding"*|*"theme"*)
            echo "branding_failure"
            return 0
            ;;
        *"overlay"*|*"staging"*|*"edition overlay"*|*"package-profile"*)
            echo "overlay_failure"
            return 0
            ;;
        *"timed out"*|*"timeout"*)
            echo "timeout"
            return 0
            ;;
    esac

    case "$phase" in
        branding_hooks) echo "branding_failure" ;;
        overlay_staging) echo "overlay_failure" ;;
        package_resolution|chroot_install|package_configuration) echo "package_resolution_failure" ;;
        initramfs_generation) echo "initramfs_failure" ;;
        filesystem_assembly|iso_or_img_assembly|checksum_generation) echo "iso_assembly_failure" ;;
        artifact_registration) echo "artifact_missing" ;;
        *) echo "unknown_failure" ;;
    esac
}

phoenix_build_logger_observe_line() {
    local line="$1"
    local detected_phase=""

    if [[ "$line" =~ (^|[[:space:]])([Ww]:|WARNING|warning) ]]; then
        phoenix_build_logger_warning "$line" "${PHOENIX_BUILD_CURRENT_PHASE:-unknown}"
    fi

    if [[ "$line" =~ (\[FAIL\]|(^|[[:space:]])ERROR($|[[:space:]])|(^|[[:space:]])Error:) ]]; then
        local failure_class
        failure_class="$(phoenix_build_logger_classify_failure_line "$line" "${PHOENIX_BUILD_CURRENT_PHASE:-unknown}")"
        phoenix_build_logger_error "$line" "${PHOENIX_BUILD_CURRENT_PHASE:-unknown}" "$failure_class"
    fi

    if detected_phase="$(phoenix_build_logger_detect_phase_from_line "$line" 2>/dev/null)"; then
        if [ -n "$detected_phase" ] && [ "$detected_phase" != "${PHOENIX_BUILD_CURRENT_PHASE:-}" ]; then
            phoenix_build_logger_phase_start "$detected_phase" "$line"
        fi
    fi
}

phoenix_build_logger_phase_start() {
    local phase="$1"
    local message="${2:-phase started}"
    local timestamp
    timestamp="$(phoenix_build_logger_now_iso)"

    if [ -n "${PHOENIX_BUILD_CURRENT_PHASE:-}" ] && [ "$PHOENIX_BUILD_CURRENT_PHASE" != "$phase" ]; then
        phoenix_build_logger_phase_close "completed"
    fi

    phoenix_build_logger_state_set "PHOENIX_BUILD_CURRENT_PHASE" "$phase"
    phoenix_build_logger_state_set "PHOENIX_BUILD_PHASE_STARTED_AT" "$timestamp"
    phoenix_build_logger_state_set "PHOENIX_BUILD_UPDATED_AT" "$timestamp"
    PHOENIX_BUILD_CURRENT_PHASE="$phase"
    PHOENIX_BUILD_PHASE_STARTED_AT="$timestamp"
    PHOENIX_BUILD_UPDATED_AT="$timestamp"
    phoenix_build_logger_event "phase_start" "info" "$phase" "$message"
}

phoenix_build_logger_phase_complete() {
    local phase="${1:-${PHOENIX_BUILD_CURRENT_PHASE:-}}"
    local phase_status="${2:-completed}"
    local message="${3:-phase completed}"
    local timestamp
    timestamp="$(phoenix_build_logger_now_iso)"

    if [ -z "$phase" ]; then
        return 0
    fi

    phoenix_build_logger_phase_close "$phase_status"
    phoenix_build_logger_state_set "PHOENIX_BUILD_CURRENT_PHASE" "$phase_status"
    phoenix_build_logger_state_set "PHOENIX_BUILD_PHASE_STARTED_AT" "$timestamp"
    phoenix_build_logger_state_set "PHOENIX_BUILD_UPDATED_AT" "$timestamp"
    PHOENIX_BUILD_CURRENT_PHASE="$phase_status"
    PHOENIX_BUILD_PHASE_STARTED_AT="$timestamp"
    PHOENIX_BUILD_UPDATED_AT="$timestamp"
    phoenix_build_logger_event "phase_end" "info" "$phase" "$message"
}

phoenix_build_logger_finalize() {
    local final_status="${1:-completed}"
    local failure_class="${2:-}"
    local artifact_path="${3:-}"
    local artifact_sha256="${4:-}"
    local artifact_size_bytes="${5:-}"
    local timestamp
    timestamp="$(phoenix_build_logger_now_iso)"

    if [ -n "${PHOENIX_BUILD_CURRENT_PHASE:-}" ] && [ "$PHOENIX_BUILD_CURRENT_PHASE" != "$final_status" ]; then
        phoenix_build_logger_phase_close "$final_status"
    fi

    phoenix_build_logger_state_set "PHOENIX_BUILD_STATUS" "$final_status"
    phoenix_build_logger_state_set "PHOENIX_BUILD_FAILURE_CLASS" "$failure_class"
    phoenix_build_logger_state_set "PHOENIX_BUILD_CURRENT_PHASE" "$final_status"
    phoenix_build_logger_state_set "PHOENIX_BUILD_UPDATED_AT" "$timestamp"
    phoenix_build_logger_state_set "PHOENIX_BUILD_SUMMARY_GENERATED_AT" "$timestamp"
    PHOENIX_BUILD_STATUS="$final_status"
    PHOENIX_BUILD_FAILURE_CLASS="$failure_class"
    PHOENIX_BUILD_CURRENT_PHASE="$final_status"
    PHOENIX_BUILD_UPDATED_AT="$timestamp"
    PHOENIX_BUILD_SUMMARY_GENERATED_AT="$timestamp"

    if [ -n "$artifact_path" ]; then
        phoenix_build_logger_state_set "PHOENIX_BUILD_ARTIFACT_PATH" "$artifact_path"
        PHOENIX_BUILD_ARTIFACT_PATH="$artifact_path"
    fi
    if [ -n "$artifact_sha256" ]; then
        phoenix_build_logger_state_set "PHOENIX_BUILD_ARTIFACT_SHA256" "$artifact_sha256"
        PHOENIX_BUILD_ARTIFACT_SHA256="$artifact_sha256"
    fi
    if [ -n "$artifact_size_bytes" ]; then
        phoenix_build_logger_state_set "PHOENIX_BUILD_ARTIFACT_SIZE_BYTES" "$artifact_size_bytes"
        PHOENIX_BUILD_ARTIFACT_SIZE_BYTES="$artifact_size_bytes"
    fi

    phoenix_build_logger_generate_summary
}

phoenix_build_logger_generate_summary() {
    if [ -z "${PHOENIX_BUILD_STATE_JSON:-}" ] || [ ! -f "$PHOENIX_BUILD_STATE_JSON" ]; then
        return 0
    fi

    python3 - \
        "$PHOENIX_BUILD_STATE_JSON" \
        "${PHOENIX_BUILD_PHASE_TIMINGS:-}" \
        "${PHOENIX_BUILD_WARNINGS_LOG:-}" \
        "${PHOENIX_BUILD_FAILURES_LOG:-}" \
        "${PHOENIX_BUILD_SUMMARY_JSON:-}" \
        "${PHOENIX_BUILD_SUMMARY_MD:-}" <<'PY'
import datetime as dt
import json
import os
import pathlib
import sys

state_path, timings_path, warnings_path, failures_path, summary_json_path, summary_md_path = sys.argv[1:7]

with open(state_path, "r", encoding="utf-8") as handle:
    state = json.load(handle)

def parse_iso(value):
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))

def seconds_between(start, end):
    if not start or not end:
        return None
    return max(0, int((parse_iso(end) - parse_iso(start)).total_seconds()))

phase_timings = []
if timings_path and os.path.exists(timings_path):
    with open(timings_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            phase, started_at, ended_at, duration_seconds, status = line.split("\t")
            phase_timings.append({
                "phase": phase,
                "started_at": started_at,
                "ended_at": ended_at,
                "duration_seconds": int(duration_seconds),
                "status": status,
            })

warnings = []
if warnings_path and os.path.exists(warnings_path):
    with open(warnings_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.rstrip("\n")
            if raw_line:
                warnings.append(raw_line)

failures = []
if failures_path and os.path.exists(failures_path):
    with open(failures_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.rstrip("\n")
            if raw_line:
                failures.append(raw_line)

start_time = parse_iso(state.get("PHOENIX_BUILD_START_TIME", ""))
updated_at = parse_iso(state.get("PHOENIX_BUILD_UPDATED_AT", ""))
elapsed_seconds = None
if start_time and updated_at:
    elapsed_seconds = max(0, int((updated_at - start_time).total_seconds()))

summary = {
    "build_id": state.get("PHOENIX_BUILD_ID", ""),
    "edition_id": state.get("PHOENIX_BUILD_EDITION_ID", ""),
    "edition_name": state.get("PHOENIX_BUILD_EDITION_NAME", ""),
    "architecture": state.get("PHOENIX_BUILD_ARCHITECTURE", ""),
    "artifact_target": state.get("PHOENIX_BUILD_ARTIFACT_TARGET", ""),
    "manifest_path": state.get("PHOENIX_BUILD_MANIFEST_PATH", ""),
    "source_commit": state.get("PHOENIX_BUILD_SOURCE_COMMIT", ""),
    "mode": state.get("PHOENIX_BUILD_MODE", ""),
    "telemetry_dir": state.get("PHOENIX_BUILD_TELEMETRY_DIR", ""),
    "status": state.get("PHOENIX_BUILD_STATUS", "running"),
    "failure_class": state.get("PHOENIX_BUILD_FAILURE_CLASS", ""),
    "current_phase": state.get("PHOENIX_BUILD_CURRENT_PHASE", ""),
    "last_successful_phase": state.get("PHOENIX_BUILD_LAST_SUCCESSFUL_PHASE", ""),
    "start_time": state.get("PHOENIX_BUILD_START_TIME", ""),
    "updated_at": state.get("PHOENIX_BUILD_UPDATED_AT", ""),
    "elapsed_seconds": elapsed_seconds,
    "warning_count": int(state.get("PHOENIX_BUILD_WARNING_COUNT", 0) or 0),
    "failure_count": int(state.get("PHOENIX_BUILD_FAILURE_COUNT", 0) or 0),
    "heartbeat_count": int(state.get("PHOENIX_BUILD_HEARTBEAT_COUNT", 0) or 0),
    "latest_warning": state.get("PHOENIX_BUILD_LAST_WARNING", ""),
    "latest_error": state.get("PHOENIX_BUILD_LAST_ERROR", ""),
    "artifact": {
        "path": state.get("PHOENIX_BUILD_ARTIFACT_PATH", ""),
        "sha256": state.get("PHOENIX_BUILD_ARTIFACT_SHA256", ""),
        "size_bytes": int(state.get("PHOENIX_BUILD_ARTIFACT_SIZE_BYTES", 0) or 0),
    },
    "phase_timings": phase_timings,
    "warnings": warnings,
    "failures": failures,
}

summary_dir = os.path.dirname(summary_json_path)
os.makedirs(summary_dir, exist_ok=True)
with open(summary_json_path, "w", encoding="utf-8") as handle:
    json.dump(summary, handle, indent=2, sort_keys=True)
    handle.write("\n")

def human_duration(seconds):
    if seconds is None:
        return "unknown"
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {sec}s"
    if minutes:
        return f"{minutes}m {sec}s"
    return f"{sec}s"

lines = []
lines.append("# BWOS Build Summary")
lines.append("")
lines.append(f"- Build ID: `{summary['build_id']}`")
lines.append(f"- Edition: `{summary['edition_name']}` (`{summary['edition_id']}`)")
lines.append(f"- Architecture: `{summary['architecture']}`")
lines.append(f"- Artifact target: `{summary['artifact_target']}`")
lines.append(f"- Manifest path: `{summary['manifest_path']}`")
lines.append(f"- Source commit: `{summary['source_commit']}`")
lines.append(f"- Mode: `{summary['mode']}`")
lines.append(f"- Final status: `{summary['status']}`")
lines.append(f"- Failure class: `{summary['failure_class'] or 'none'}`")
lines.append(f"- Current phase: `{summary['current_phase']}`")
lines.append(f"- Last successful phase: `{summary['last_successful_phase']}`")
lines.append(f"- Build duration: `{human_duration(summary['elapsed_seconds'])}`")
lines.append(f"- Artifact path: `{summary['artifact']['path'] or 'unresolved'}`")
lines.append(f"- SHA256: `{summary['artifact']['sha256'] or 'unresolved'}`")
lines.append(f"- Size bytes: `{summary['artifact']['size_bytes']}`")
lines.append(f"- Warnings: `{summary['warning_count']}`")
lines.append(f"- Failures: `{summary['failure_count']}`")
lines.append("")
lines.append("## Phase Timings")
lines.append("")
lines.append("| Phase | Start | End | Duration | Status |")
lines.append("| --- | --- | --- | ---: | --- |")
for phase in phase_timings:
    lines.append(
        f"| {phase['phase']} | {phase['started_at']} | {phase['ended_at']} | {phase['duration_seconds']}s | {phase['status']} |"
    )
if not phase_timings:
    lines.append("| _none recorded_ |  |  |  |  |")

lines.append("")
lines.append("## Warnings")
lines.append("")
if warnings:
    for warning in warnings:
        lines.append(f"- {warning}")
else:
    lines.append("- None recorded.")

lines.append("")
lines.append("## Failures")
lines.append("")
if failures:
    for failure in failures:
        lines.append(f"- {failure}")
else:
    lines.append("- None recorded.")

with open(summary_md_path, "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines) + "\n")
PY
}

phoenix_build_logger_init() {
    local telemetry_dir="$1"
    local build_id="$2"
    local edition_id="$3"
    local edition_name="$4"
    local architecture="$5"
    local artifact_target="$6"
    local mode="$7"
    local manifest_path="$8"
    local source_commit="$9"

    mkdir -p "$telemetry_dir"

    PHOENIX_BUILD_TELEMETRY_DIR="$telemetry_dir"
    PHOENIX_BUILD_STATE_JSON="$telemetry_dir/build-state.json"
    PHOENIX_BUILD_EVENT_LOG="$telemetry_dir/build-events.jsonl"
    PHOENIX_BUILD_HUMAN_LOG="$telemetry_dir/build.log"
    PHOENIX_BUILD_PHASE_TIMINGS="$telemetry_dir/phase-timings.tsv"
    PHOENIX_BUILD_WARNINGS_LOG="$telemetry_dir/warnings.log"
    PHOENIX_BUILD_FAILURES_LOG="$telemetry_dir/failures.log"
    PHOENIX_BUILD_SUMMARY_JSON="${PHOENIX_BUILD_SUMMARY_JSON:-$telemetry_dir/build-summary.json}"
    PHOENIX_BUILD_SUMMARY_MD="${PHOENIX_BUILD_SUMMARY_MD:-$telemetry_dir/build-summary.md}"

    export PHOENIX_BUILD_TELEMETRY_DIR
    export PHOENIX_BUILD_STATE_JSON
    export PHOENIX_BUILD_EVENT_LOG
    export PHOENIX_BUILD_HUMAN_LOG
    export PHOENIX_BUILD_PHASE_TIMINGS
    export PHOENIX_BUILD_WARNINGS_LOG
    export PHOENIX_BUILD_FAILURES_LOG
    export PHOENIX_BUILD_SUMMARY_JSON
    export PHOENIX_BUILD_SUMMARY_MD

    local now
    now="$(phoenix_build_logger_now_iso)"

    python3 - \
        "$PHOENIX_BUILD_STATE_JSON" \
        "$build_id" \
        "$edition_id" \
        "$edition_name" \
        "$architecture" \
        "$artifact_target" \
        "$mode" \
        "$manifest_path" \
        "$source_commit" \
        "$telemetry_dir" \
        "$now" <<'PY'
import json
import os
import sys

(
    state_path,
    build_id,
    edition_id,
    edition_name,
    architecture,
    artifact_target,
    mode,
    manifest_path,
    source_commit,
    telemetry_dir,
    now,
) = sys.argv[1:12]

state = {
    "PHOENIX_BUILD_ID": build_id,
    "PHOENIX_BUILD_EDITION_ID": edition_id,
    "PHOENIX_BUILD_EDITION_NAME": edition_name,
    "PHOENIX_BUILD_ARCHITECTURE": architecture,
    "PHOENIX_BUILD_ARTIFACT_TARGET": artifact_target,
    "PHOENIX_BUILD_MODE": mode,
    "PHOENIX_BUILD_MANIFEST_PATH": manifest_path,
    "PHOENIX_BUILD_SOURCE_COMMIT": source_commit,
    "PHOENIX_BUILD_TELEMETRY_DIR": telemetry_dir,
    "PHOENIX_BUILD_STATUS": "running",
    "PHOENIX_BUILD_FAILURE_CLASS": "",
    "PHOENIX_BUILD_CURRENT_PHASE": "preflight",
    "PHOENIX_BUILD_PHASE_STARTED_AT": now,
    "PHOENIX_BUILD_LAST_SUCCESSFUL_PHASE": "",
    "PHOENIX_BUILD_START_TIME": now,
    "PHOENIX_BUILD_UPDATED_AT": now,
    "PHOENIX_BUILD_LAST_WARNING": "",
    "PHOENIX_BUILD_LAST_ERROR": "",
    "PHOENIX_BUILD_WARNING_COUNT": 0,
    "PHOENIX_BUILD_FAILURE_COUNT": 0,
    "PHOENIX_BUILD_HEARTBEAT_COUNT": 0,
    "PHOENIX_BUILD_LAST_HEARTBEAT_AT": "",
    "PHOENIX_BUILD_ARTIFACT_PATH": "",
    "PHOENIX_BUILD_ARTIFACT_SHA256": "",
    "PHOENIX_BUILD_ARTIFACT_SIZE_BYTES": 0,
    "PHOENIX_BUILD_SUMMARY_GENERATED_AT": "",
}

tmp_path = f"{state_path}.tmp"
with open(tmp_path, "w", encoding="utf-8") as handle:
    json.dump(state, handle, indent=2, sort_keys=True)
    handle.write("\n")
os.replace(tmp_path, state_path)
PY

    : >"$PHOENIX_BUILD_EVENT_LOG"
    : >"$PHOENIX_BUILD_HUMAN_LOG"
    : >"$PHOENIX_BUILD_PHASE_TIMINGS"
    : >"$PHOENIX_BUILD_WARNINGS_LOG"
    : >"$PHOENIX_BUILD_FAILURES_LOG"

    phoenix_build_logger_state_sync_shell
}
