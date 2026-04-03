#!/bin/bash
echo "Starting BootForge..."
cd "$(dirname "$0")/executables"
if [ -d "BootForge.app" ]; then
    open "BootForge.app"
else
    echo "BootForge.app not found!"
    read -p "Press enter to continue..."
fi
