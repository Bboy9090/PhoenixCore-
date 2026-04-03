#!/bin/bash
echo "Starting BootForge..."
cd "$(dirname "$0")/executables"
if [ -f "BootForge" ]; then
    ./BootForge
else
    echo "BootForge executable not found!"
    read -p "Press enter to continue..."
fi
