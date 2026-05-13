#!/usr/bin/env bash

set -u
set -o pipefail

runtime="auto"
check_privileged=0

usage() {
  cat <<'USAGE'
Usage: check-build-agent.sh [--runtime docker|podman] [--check-privileged]

Non-destructive preflight checks for Phoenix OS OCI build readiness.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --runtime)
      if [[ $# -lt 2 ]]; then
        echo "[FAIL] --runtime requires a value: docker|podman"
        usage
        exit 2
      fi
      runtime="$2"
      if [[ "$runtime" != "docker" && "$runtime" != "podman" && "$runtime" != "auto" ]]; then
        echo "[FAIL] Invalid runtime '$runtime'. Expected docker or podman."
        usage
        exit 2
      fi
      shift 2
      ;;
    --check-privileged)
      check_privileged=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] Unknown argument: $1"
      usage
      exit 2
      ;;
  esac
done

failures=0
warnings=0

pass() { echo "[PASS] $1"; }
warn() { echo "[WARN] $1"; warnings=$((warnings + 1)); }
fail() { echo "[FAIL] $1"; failures=$((failures + 1)); }
info() { echo "[INFO] $1"; }

os_name="$(uname -s 2>/dev/null || echo unknown)"
case "$os_name" in
  Linux|Darwin)
    pass "Host OS detected: $os_name"
    ;;
  *)
    warn "Host OS is $os_name. This script supports Linux/macOS checks."
    ;;
esac

if [[ "$runtime" == "auto" ]]; then
  if command -v docker >/dev/null 2>&1; then
    runtime="docker"
  elif command -v podman >/dev/null 2>&1; then
    runtime="podman"
  else
    runtime="none"
  fi
fi

if [[ "$runtime" == "none" ]]; then
  fail "Neither docker nor podman was found in PATH."
else
  if ! command -v "$runtime" >/dev/null 2>&1; then
    fail "Requested runtime '$runtime' is not in PATH."
    runtime="none"
  fi
fi

if [[ "$runtime" != "none" ]]; then
  if "$runtime" --version >/dev/null 2>&1; then
    version="$($runtime --version 2>/dev/null | head -n 1)"
    pass "Runtime available: $version"
  else
    fail "Unable to execute '$runtime --version'."
  fi
fi

if [[ "$runtime" == "docker" ]]; then
  if docker info >/dev/null 2>&1; then
    pass "Docker daemon is reachable."
  else
    fail "Docker daemon is not reachable. Start Docker Desktop/service."
  fi

  if docker compose version >/dev/null 2>&1; then
    compose_version="$(docker compose version 2>/dev/null | head -n 1)"
    pass "Compose plugin available: $compose_version"
  else
    warn "'docker compose' is unavailable. Install/enable Docker Compose v2 plugin."
  fi
fi

if [[ "$runtime" == "podman" ]]; then
  if podman info >/dev/null 2>&1; then
    pass "Podman service is reachable."
  else
    fail "Podman is installed but 'podman info' failed."
  fi

  if podman compose version >/dev/null 2>&1; then
    compose_version="$(podman compose version 2>/dev/null | head -n 1)"
    pass "Podman compose provider available: $compose_version"
  elif command -v podman-compose >/dev/null 2>&1; then
    compose_version="$(podman-compose --version 2>/dev/null | head -n 1)"
    pass "podman-compose available: $compose_version"
  else
    warn "No compose provider detected for Podman ('podman compose' or 'podman-compose')."
  fi
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$script_dir/verify-container.sh" ]]; then
  pass "Found helper: os/phoenix-os/scripts/verify-container.sh"
else
  warn "Missing helper: os/phoenix-os/scripts/verify-container.sh"
fi

if [[ -f "$script_dir/build-container.sh" ]]; then
  pass "Found helper: os/phoenix-os/scripts/build-container.sh"
else
  warn "Missing helper: os/phoenix-os/scripts/build-container.sh"
fi

if [[ "$check_privileged" -eq 1 && "$runtime" != "none" ]]; then
  info "Running disposable privileged container probe (image: alpine:3.20)."
  if "$runtime" run --rm --privileged --pull=missing alpine:3.20 true >/dev/null 2>&1; then
    pass "Privileged container run succeeded for runtime '$runtime'."
  else
    fail "Privileged container run failed for runtime '$runtime'."
  fi
else
  info "Privileged container probe skipped. Use --check-privileged to enable."
fi

if [[ "$failures" -gt 0 ]]; then
  echo
  echo "Build-agent preflight FAILED ($failures failures, $warnings warnings)."
  exit 1
fi

echo
echo "Build-agent preflight PASSED (0 failures, $warnings warnings)."
exit 0
