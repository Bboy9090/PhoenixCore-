#!/bin/bash
echo "===================================================="
echo "⚡ ZENITH TIER: COMPILING VOLUMETRIC UI ENGINE ⚡"
echo "===================================================="
echo ""
echo "Installing Rust Compiler..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

echo ""
echo "Installing Node.js Engine..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt-get install -y nodejs

echo ""
echo "Installing Graphics Libraries for Glass UI..."
sudo apt update
sudo apt install -y libwebkit2gtk-4.0-dev build-essential curl wget file libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev

echo ""
echo "Compiling React/Tauri Architecture..."
cd /opt/native-app-hub
npm install
npm run tauri dev
