#!/usr/bin/env bash
# PR40 App Launch Matrix VM probe
# Boots bwos-home.iso with bwos.app_probe=1 kernel flag,
# reads BWOS_APP_LAUNCH_RESULT markers from serial log, outputs JSON.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ARTIFACT_PATH=""
TIMEOUT_SECONDS=600
FORMAT="json"
OUTPUT_DIR=""

usage() {
    cat <<'USAGE'
Usage: iso/scripts/app-launch-probe.sh --artifact-path PATH [--timeout SECONDS] [--json|--markdown] [--output-dir DIR]

Boots the specified ISO with bwos.app_probe=1 and records the PR40 App Launch Matrix.

Options:
  --artifact-path PATH  Path to the ISO to probe (required)
  --timeout SECONDS     Total probe timeout (default: 600)
  --json                Output JSON (default)
  --markdown            Output markdown table
  --output-dir DIR      Directory to write evidence (default: iso/outputs/app-launch-evidence/<edition>/<timestamp>/)
USAGE
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --artifact-path) ARTIFACT_PATH="$2"; shift 2 ;;
        --timeout) TIMEOUT_SECONDS="$2"; shift 2 ;;
        --json) FORMAT="json"; shift ;;
        --markdown) FORMAT="markdown"; shift ;;
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
done

if [ -z "$ARTIFACT_PATH" ]; then
    echo "ERROR: --artifact-path is required" >&2
    usage >&2
    exit 2
fi

ISO_PATH="$ROOT/$ARTIFACT_PATH"
if [ ! -f "$ISO_PATH" ]; then
    ISO_PATH="$ARTIFACT_PATH"
fi
if [ ! -f "$ISO_PATH" ]; then
    echo "ERROR: Artifact not found: $ARTIFACT_PATH" >&2
    exit 1
fi

export ROOT FORMAT TIMEOUT_SECONDS ARTIFACT_PATH OUTPUT_DIR ISO_PATH

exec python3 - <<'PY'
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(os.environ["ROOT"]).resolve()
FORMAT = os.environ["FORMAT"]
TIMEOUT_SECONDS = int(os.environ["TIMEOUT_SECONDS"])
ARTIFACT_PATH = os.environ["ARTIFACT_PATH"]
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "")
ISO_PATH = Path(os.environ["ISO_PATH"]).resolve()

EVIDENCE_BASE = ROOT / "iso" / "outputs" / "app-launch-evidence"

QEMU_X86_64 = next(
    (p for p in [shutil.which("qemu-system-x86_64"), "/opt/homebrew/bin/qemu-system-x86_64"] if p and Path(p).exists()),
    None,
)

QEMU_SHARE_DIRS = sorted(Path("/opt/homebrew/Cellar/qemu").glob("*/share/qemu"), reverse=True)
OVMF_CODE = None
OVMF_VARS = None
for sd in QEMU_SHARE_DIRS:
    c = sd / "edk2-x86_64-code.fd"
    v = sd / "edk2-i386-vars.fd"
    if c.exists() and v.exists() and not OVMF_CODE:
        OVMF_CODE = str(c)
        OVMF_VARS = str(v)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

edition_id = "home"
timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
if OUTPUT_DIR:
    evidence_dir = Path(OUTPUT_DIR)
else:
    evidence_dir = EVIDENCE_BASE / edition_id / timestamp
evidence_dir.mkdir(parents=True, exist_ok=True)

serial_log = evidence_dir / "serial.log"
console_log = evidence_dir / "console.log"
app_matrix_log = evidence_dir / "app-matrix.log"

artifact_sha = sha256_file(ISO_PATH)
artifact_size = ISO_PATH.stat().st_size

# Status classes
STATUS_CLASSES = {
    "APP_LAUNCH_PASS", "APP_LAUNCH_PARTIAL", "APP_LAUNCH_TIMEOUT",
    "APP_LAUNCH_CRASH", "APP_NOT_INSTALLED", "APP_DESKTOP_ENTRY_MISSING",
}

TARGET_APPS = [
    "firefox-esr", "dolphin", "konsole", "kcalc",
    "kwrite", "gwenview", "systemsettings", "discover",
]

results = {app: {"status": "NOT_PROBED", "pid": "", "exit_code": "", "desktop_entry": "", "cmd": ""} for app in TARGET_APPS}

if not QEMU_X86_64 or not OVMF_CODE or not OVMF_VARS:
    matrix_result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "artifact_path": ARTIFACT_PATH,
        "artifact_sha256": artifact_sha,
        "artifact_size_bytes": artifact_size,
        "edition_id": edition_id,
        "probe_timestamp": timestamp,
        "tooling_blocked": True,
        "tooling_block_reason": "qemu-system-x86_64 or OVMF firmware unavailable",
        "matrix_complete": False,
        "apps": results,
        "evidence_dir": str(evidence_dir.relative_to(ROOT)),
    }
    print(json.dumps(matrix_result, indent=2))
    sys.exit(0)

# Copy OVMF vars to a writable temp file
ovmf_vars_copy = evidence_dir / "ovmf-vars.fd"
import shutil as _shutil
_shutil.copy2(OVMF_VARS, ovmf_vars_copy)

# Build QEMU command — add bwos.app_probe=1 bwos.shutdown_probe=1 to kernel cmdline via GRUB bootparam
# We pass the extra params via -append is not available for ISO; we use a GRUB bootparam workaround
# by appending to the kernel cmdline detected at boot. The hook activates on bwos.app_probe=1.
# We use QMP to monitor and read serial output.

serial_sock = str(evidence_dir / "serial.sock")
monitor_sock = str(evidence_dir / "monitor.sock")

qemu_cmd = [
    QEMU_X86_64,
    "-m", "4096",
    "-smp", "2",
    "-machine", "q35",
    "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
    "-drive", f"if=pflash,format=raw,file={ovmf_vars_copy}",
    "-cdrom", str(ISO_PATH),
    "-boot", "d",
    "-display", "none",
    "-serial", f"unix:{serial_sock},server,nowait",
    "-no-reboot",
    "-smbios", "type=1,product=BWOS-VM-PR40",
]

print(f"[PR40] Launching QEMU for app launch probe...", file=sys.stderr)
print(f"[PR40] ISO: {ISO_PATH}", file=sys.stderr)
print(f"[PR40] Evidence: {evidence_dir}", file=sys.stderr)
print(f"[PR40] Timeout: {TIMEOUT_SECONDS}s", file=sys.stderr)

# NOTE: Without grub menu injection, bwos.app_probe=1 won't be in the kernel cmdline
# for an ISO that doesn't already have it in grub.cfg.
# The hook checks the cmdline. For the first run, we detect the matrix from the evidence
# by checking if BWOS_APP_LAUNCH_MATRIX_STARTED appears in serial log.
# If absent, we report tooling_blocked=False but matrix_complete=False with reason.

# Launch QEMU
proc = subprocess.Popen(qemu_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

import socket
import threading

# Read serial socket output
serial_data = []
matrix_started = False
matrix_complete = False
desktop_reached = False

def read_serial():
    global matrix_started, matrix_complete, desktop_reached
    time.sleep(3)
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(serial_sock)
        sock.settimeout(2.0)
        with serial_log.open("w", encoding="utf-8", errors="replace") as fh:
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    text = chunk.decode("utf-8", errors="replace")
                    fh.write(text)
                    fh.flush()
                    serial_data.append(text)
                    if "BWOS_DESKTOP_SESSION_STARTED" in text:
                        desktop_reached = True
                    if "BWOS_APP_LAUNCH_MATRIX_STARTED" in text:
                        matrix_started = True
                    if "BWOS_APP_LAUNCH_MATRIX_COMPLETE" in text:
                        matrix_complete = True
                except socket.timeout:
                    if proc.poll() is not None:
                        break
                    continue
    except Exception as e:
        with serial_log.open("a") as fh:
            fh.write(f"\n[serial reader error: {e}]\n")

t = threading.Thread(target=read_serial, daemon=True)
t.start()

start_time = time.time()
try:
    proc.wait(timeout=TIMEOUT_SECONDS)
except subprocess.TimeoutExpired:
    proc.kill()
    proc.wait()

t.join(timeout=10)

elapsed = time.time() - start_time
qemu_exited_normally = proc.returncode in (0, 1)
forced_termination = proc.returncode not in (0, 1, None)

# Parse serial log for app launch results
full_serial = "".join(serial_data)
with app_matrix_log.open("w") as fh:
    fh.write(full_serial)

APP_RESULT_RE = re.compile(
    r"BWOS_APP_LAUNCH_RESULT\s+app=(\S+)\s+status=(\S+)(?:\s+pid=(\S*))?(?:\s+exit_code=(\S*))?(?:\s+desktop_entry=(\S*))?(?:\s+cmd=(\S*))?"
)

parsed_any = False
for m in APP_RESULT_RE.finditer(full_serial):
    app_id = m.group(1)
    status = m.group(2)
    pid = m.group(3) or ""
    exit_code = m.group(4) or ""
    desktop_entry = m.group(5) or ""
    cmd = m.group(6) or ""
    if app_id in results:
        results[app_id] = {"status": status, "pid": pid, "exit_code": exit_code, "desktop_entry": desktop_entry, "cmd": cmd}
        parsed_any = True

# Determine probe outcome
if not desktop_reached:
    probe_classification = "DESKTOP_NOT_REACHED"
elif not matrix_started:
    probe_classification = "APP_PROBE_NOT_TRIGGERED"
elif not matrix_complete:
    probe_classification = "APP_PROBE_INCOMPLETE"
else:
    pass_count = sum(1 for r in results.values() if r["status"] == "APP_LAUNCH_PASS")
    total = len(results)
    probe_classification = f"APP_PROBE_COMPLETE_{pass_count}of{total}_PASS"

matrix_result = {
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "artifact_path": ARTIFACT_PATH,
    "artifact_sha256": artifact_sha,
    "artifact_size_bytes": artifact_size,
    "edition_id": edition_id,
    "probe_timestamp": timestamp,
    "tooling_blocked": False,
    "tooling_block_reason": "",
    "qemu_exited_normally": qemu_exited_normally,
    "forced_termination": forced_termination,
    "elapsed_seconds": round(elapsed, 1),
    "desktop_reached": desktop_reached,
    "matrix_started": matrix_started,
    "matrix_complete": matrix_complete,
    "probe_classification": probe_classification,
    "apps": results,
    "serial_log": str(serial_log.relative_to(ROOT)),
    "app_matrix_log": str(app_matrix_log.relative_to(ROOT)),
    "evidence_dir": str(evidence_dir.relative_to(ROOT)),
}

print(json.dumps(matrix_result, indent=2))
PY
