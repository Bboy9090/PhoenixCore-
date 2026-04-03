#!/bin/bash
# BootForge USB Launcher for Linux
echo "🚀 Starting BootForge from USB..."
cd "$(dirname "$0")/BootForge"

# Check for Python
if command -v python3 &> /dev/null; then
    echo "✅ Python 3 found"
    python3 main.py --gui
elif command -v python &> /dev/null; then
    echo "✅ Python found"
    python main.py --gui
else
    echo "❌ Python not found. Please install Python 3."
    echo "Run: sudo apt install python3 python3-pip"
    read -p "Press enter to exit..."
fi
