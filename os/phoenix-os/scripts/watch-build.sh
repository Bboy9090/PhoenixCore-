#!/usr/bin/env bash
# Safely report the active BWOS build status without mutating the workspace.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/build-logger.sh"

STATE_FILE=""
FOLLOW=true
INTERVAL_SECONDS=5

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --state-file=*)
            STATE_FILE="${1#*=}"
            shift
            ;;
        --state-file)
            STATE_FILE="${2:-}"
            shift 2
            ;;
        --once)
            FOLLOW=false
            shift
            ;;
        --interval=*)
            INTERVAL_SECONDS="${1#*=}"
            shift
            ;;
        --interval)
            INTERVAL_SECONDS="${2:-5}"
            shift 2
            ;;
        --help|-h)
            cat <<'EOF'
Usage: watch-build.sh [--state-file <path>] [--once] [--interval <seconds>]

Prints the current build snapshot from build telemetry.
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

find_latest_state_file() {
    local build_root="${PHOENIX_OS_ARTIFACT_DIR:-$SCRIPT_DIR/../build}"
    find "$build_root/telemetry" -name build-state.json -type f 2>/dev/null | sort | tail -n 1
}

if [[ -z "$STATE_FILE" ]]; then
    STATE_FILE="$(find_latest_state_file || true)"
fi

render_snapshot() {
    local path="$1"
    if [[ -z "$path" || ! -f "$path" ]]; then
        echo "No build telemetry state file found."
        return 0
    fi

    python3 - "$path" <<'PY'
import datetime as dt
import json
import os
import subprocess
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as handle:
    state = json.load(handle)

def parse_iso(value):
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))

def docker_status(project, service):
    if not shutil.which("docker"):
        return "unavailable"
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                f"label=com.docker.compose.project={project}",
                "--filter",
                f"label=com.docker.compose.service={service}",
                "--format",
                "{{.Status}}",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return "unavailable"
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return lines[0] if lines else "unavailable"

import shutil

start = parse_iso(state.get("PHOENIX_BUILD_START_TIME", ""))
updated_at = parse_iso(state.get("PHOENIX_BUILD_UPDATED_AT", ""))
last_heartbeat = parse_iso(state.get("PHOENIX_BUILD_LAST_HEARTBEAT_AT", ""))
now = dt.datetime.now(dt.timezone.utc)
elapsed = None
if start:
    elapsed = max(0, int((now - start).total_seconds()))
current_phase = state.get("PHOENIX_BUILD_CURRENT_PHASE", "")
last_ok = state.get("PHOENIX_BUILD_LAST_SUCCESSFUL_PHASE", "")
heartbeat_count = int(state.get("PHOENIX_BUILD_HEARTBEAT_COUNT", 0) or 0)
status = state.get("PHOENIX_BUILD_STATUS", "running")

container_status = docker_status(
    os.environ.get("PHOENIX_OS_COMPOSE_PROJECT", "phoenix-os-oci"),
    os.environ.get("PHOENIX_OS_BUILDER_SERVICE", "builder"),
)

last_activity = updated_at or last_heartbeat or start
stale_seconds = None
if last_activity:
    stale_seconds = max(0, int((now - last_activity).total_seconds()))

if status in ("completed", "failed"):
    stall_hint = "not applicable"
elif stale_seconds is None:
    stall_hint = "unknown"
elif stale_seconds >= 180:
    stall_hint = f"possible stall ({stale_seconds}s since last state update)"
else:
    stall_hint = f"active ({stale_seconds}s since last state update)"

warnings = []
warnings_path = os.path.join(os.path.dirname(path), "warnings.log")
if os.path.exists(warnings_path):
    with open(warnings_path, "r", encoding="utf-8") as handle:
        warnings = [line.rstrip("\n") for line in handle if line.strip()]

print(f"Build ID: {state.get('PHOENIX_BUILD_ID', '')}")
print(f"Edition: {state.get('PHOENIX_BUILD_EDITION_NAME', '')} ({state.get('PHOENIX_BUILD_EDITION_ID', '')})")
print(f"Architecture: {state.get('PHOENIX_BUILD_ARCHITECTURE', '')}")
print(f"Artifact target: {state.get('PHOENIX_BUILD_ARTIFACT_TARGET', '')}")
print(f"Status: {status}")
print(f"Current phase: {current_phase}")
print(f"Last successful phase: {last_ok or 'none'}")
print(f"Elapsed: {elapsed if elapsed is not None else 'unknown'}s")
print(f"Warnings: {state.get('PHOENIX_BUILD_WARNING_COUNT', 0)}")
print(f"Failures: {state.get('PHOENIX_BUILD_FAILURE_COUNT', 0)}")
print(f"Heartbeats: {heartbeat_count}")
print(f"Container status: {container_status}")
print(f"Stall hint: {stall_hint}")
if state.get("PHOENIX_BUILD_LAST_WARNING"):
    print(f"Latest warning: {state.get('PHOENIX_BUILD_LAST_WARNING')}")
if state.get("PHOENIX_BUILD_LAST_ERROR"):
    print(f"Latest error: {state.get('PHOENIX_BUILD_LAST_ERROR')}")
if warnings:
    print("Recent warnings:")
    for warning in warnings[-5:]:
        print(f"  - {warning}")
PY
}

if [[ "$FOLLOW" == false ]]; then
    render_snapshot "$STATE_FILE"
    exit 0
fi

while true; do
    printf '\033[2J\033[H'
    render_snapshot "$STATE_FILE"
    sleep "$INTERVAL_SECONDS"
done
