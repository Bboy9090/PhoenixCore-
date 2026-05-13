#!/bin/bash
# Phoenix OS Build Agent Health Check (Linux/macOS Host)

echo "=== Phoenix OS Build Agent: Shell Environment Check ==="

SUCCESS=true

# 1. Check Docker/Podman
if command -v docker &> /dev/null; then
    echo "[OK] Docker found: $(docker --version)"
elif command -v podman &> /dev/null; then
    echo "[OK] Podman found: $(podman --version)"
else
    echo "[FAIL] No container engine found (Docker/Podman)."
    SUCCESS=false
fi

# 2. Check Compose
if docker compose version &> /dev/null; then
    echo "[OK] Docker Compose found."
else
    echo "[FAIL] Docker Compose not found."
    SUCCESS=false
fi

# 3. Check Privileged Mode
if [ "$SUCCESS" = true ]; then
    echo "Checking Privileged Container Support..."
    if docker run --rm --privileged debian:bookworm-slim echo "SUCCESS" &> /dev/null; then
        echo "[OK] Privileged mode verified."
    else
        echo "[FAIL] Privileged mode denied."
        SUCCESS=false
    fi
fi

echo "---------------------------------------"
if [ "$SUCCESS" = true ]; then
    echo "STATUS: Local Build Agent is READY."
else
    echo "STATUS: Local Build Agent is NOT READY."
    echo "Refer to docs/LOCAL_BUILD_AGENT.md for setup instructions."
fi
