#!/usr/bin/env bash
# Build a wheel for phoenix-safety (upload to internal PyPI or install offline).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/packages/phoenix_safety"
python3 -m pip install --upgrade build >/dev/null 2>&1 || pip install build
python3 -m build --wheel
echo "Wheel output under packages/phoenix_safety/dist/"
ls -la dist/
