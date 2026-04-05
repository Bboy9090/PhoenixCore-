#!/usr/bin/env bash
# Truth enforcement for Lockdown Plus (run in CI after checkout).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== safety schema version stable =="
SCHEMA_VER=$(grep -E '^SAFETY_SCHEMA_VERSION' backend/core/safety_schema.py | head -1)
echo "$SCHEMA_VER"
if ! echo "$SCHEMA_VER" | grep -q '1.0.0'; then
  echo "FAIL: bump SAFETY_SCHEMA_VERSION only with intentional contract change + doc update"
  exit 1
fi

echo "== capability matrix mentions destructive_usb_write_native =="
if ! grep -q 'destructive_usb_write_native' docs/CAPABILITY_MATRIX.md; then
  echo "FAIL: CAPABILITY_MATRIX must document API capability flag"
  exit 1
fi

echo "== canonical code must not import legacy/bootable_usb =="
if grep -r -E 'legacy/bootable_usb|legacy\.bootable_usb' --include='*.py' desktop backend packages tests 2>/dev/null | grep -q .; then
  grep -r -E 'legacy/bootable_usb|legacy\.bootable_usb' --include='*.py' desktop backend packages tests || true
  echo "FAIL: canonical trees must not reference legacy/bootable_usb"
  exit 1
fi

echo "== canonical code must not import from mobile/ app tree =="
if grep -r -E '(from|import)[[:space:]]+mobile\.' --include='*.py' desktop backend packages tests 2>/dev/null | grep -q .; then
  echo "FAIL: unexpected import from mobile package"
  exit 1
fi

echo "== phoenix_safety package present =="
test -f packages/phoenix_safety/phoenix_safety/safety_validator.py

echo "== phoenix_safety importable in environment =="
python3 -c "from phoenix_safety.safety_validator import SafetyValidator; assert SafetyValidator is not None"

echo "== backend must not import server.* or legacy package =="
if grep -r -E '^[[:space:]]*(from|import)[[:space:]]+server\.' --include='*.py' backend packages 2>/dev/null | grep -q .; then
  echo "FAIL: backend/packages must not import server.*"
  exit 1
fi
if grep -r -E '^[[:space:]]*(from|import)[[:space:]]+legacy(\.| |$)' --include='*.py' backend packages desktop tests 2>/dev/null | grep -q .; then
  echo "FAIL: canonical code must not import legacy as top-level package"
  exit 1
fi

echo "OK: truth enforcement passed"
