#!/usr/bin/env bash
# Emit a truthful build heartbeat from the current telemetry state.
#
# stdout: JSONL heartbeat event
# stderr: human-readable heartbeat line

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/build-logger.sh"

STATE_FILE=""
CONTAINER_PROJECT="${PHOENIX_OS_COMPOSE_PROJECT:-phoenix-os-oci}"
CONTAINER_SERVICE="${PHOENIX_OS_BUILDER_SERVICE:-builder}"

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
        --container-project=*)
            CONTAINER_PROJECT="${1#*=}"
            shift
            ;;
        --container-project)
            CONTAINER_PROJECT="${2:-}"
            shift 2
            ;;
        --container-service=*)
            CONTAINER_SERVICE="${1#*=}"
            shift
            ;;
        --container-service)
            CONTAINER_SERVICE="${2:-}"
            shift 2
            ;;
        --help|-h)
            cat <<'EOF'
Usage: build-heartbeat.sh --state-file <path> [--container-project <name>] [--container-service <name>]

Outputs a JSONL heartbeat to stdout and a human-readable line to stderr.
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

if [[ -z "$STATE_FILE" ]]; then
    STATE_FILE="${PHOENIX_BUILD_STATE_JSON:-}"
fi

if [[ -z "$STATE_FILE" || ! -f "$STATE_FILE" ]]; then
    exit 0
fi

heartbeat_json="$(
python3 - "$STATE_FILE" "$CONTAINER_PROJECT" "$CONTAINER_SERVICE" <<'PY'
import datetime as dt
import json
import os
import subprocess
import sys

state_path, project, service = sys.argv[1:4]
with open(state_path, "r", encoding="utf-8") as handle:
    state = json.load(handle)

def parse_iso(value):
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))

def now_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

current = now_iso()
start_time = parse_iso(state.get("PHOENIX_BUILD_START_TIME", ""))
elapsed = None
if start_time is not None:
    elapsed = max(0, int((dt.datetime.now(dt.timezone.utc) - start_time).total_seconds()))

container_status = "unavailable"
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
    status_line = result.stdout.strip().splitlines()
    if status_line:
        container_status = status_line[0]
except Exception:
    container_status = "unavailable"

heartbeat_count = int(state.get("PHOENIX_BUILD_HEARTBEAT_COUNT", 0) or 0) + 1
state["PHOENIX_BUILD_HEARTBEAT_COUNT"] = heartbeat_count
state["PHOENIX_BUILD_LAST_HEARTBEAT_AT"] = current
state["PHOENIX_BUILD_UPDATED_AT"] = current
tmp_path = f"{state_path}.tmp"
with open(tmp_path, "w", encoding="utf-8") as handle:
    json.dump(state, handle, indent=2, sort_keys=True)
    handle.write("\n")
os.replace(tmp_path, state_path)

payload = {
    "timestamp": current,
    "event_type": "heartbeat",
    "build_id": state.get("PHOENIX_BUILD_ID", ""),
    "edition_id": state.get("PHOENIX_BUILD_EDITION_ID", ""),
    "edition_name": state.get("PHOENIX_BUILD_EDITION_NAME", ""),
    "architecture": state.get("PHOENIX_BUILD_ARCHITECTURE", ""),
    "artifact_target": state.get("PHOENIX_BUILD_ARTIFACT_TARGET", ""),
    "current_phase": state.get("PHOENIX_BUILD_CURRENT_PHASE", ""),
    "last_successful_phase": state.get("PHOENIX_BUILD_LAST_SUCCESSFUL_PHASE", ""),
    "elapsed_seconds": elapsed,
    "status": state.get("PHOENIX_BUILD_STATUS", "running"),
    "container_status": container_status,
    "warning_count": int(state.get("PHOENIX_BUILD_WARNING_COUNT", 0) or 0),
    "failure_count": int(state.get("PHOENIX_BUILD_FAILURE_COUNT", 0) or 0),
    "heartbeat_count": heartbeat_count,
}

human = (
    f"[{current}] heartbeat edition={payload['edition_id']} "
    f"arch={payload['architecture']} phase={payload['current_phase']} "
    f"elapsed={payload['elapsed_seconds']}s "
    f"last_ok={payload['last_successful_phase'] or 'none'} "
    f"container={container_status}"
)

print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
print(human, file=sys.stderr)
PY
)"

printf '%s\n' "$heartbeat_json"
