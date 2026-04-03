#!/bin/bash
# Phoenix Core - Bootable Kiosk Launcher
# This script is intended to run as an autostart in the bootable system.

echo "=== Phoenix Core Kiosk Launcher ==="

# 1. Start Phoenix Backend
echo "Starting Phoenix Backend..."
# Assume backend is at /tools/backend or integrated into the python enviroment
cd /tools/backend || exit 1
python3 main.py &
BACKEND_PID=$!

# 2. Wait for backend to be ready
echo "Waiting for backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo "Backend is ready!"
        break
    fi
    sleep 1
done

# 3. Launch Kiosk Browser
# Try Chromium first, then Firefox
echo "Launching Phoenix UI..."
if command -v chromium-browser > /dev/null; then
    chromium-browser --kiosk http://localhost:8000 --no-first-run --simulate-outdated-no-au
elif command -v google-chrome > /dev/null; then
    google-chrome --kiosk http://localhost:8000 --no-first-run
elif command -v firefox > /dev/null; then
    firefox --new-window http://localhost:8000
else
    echo "No browser found! Please install chromium or firefox."
fi

# Cleanup on exit
kill $BACKEND_PID
