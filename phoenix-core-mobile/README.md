# PhoenixCore Mobile

Expo (React Native) app for PhoenixCore: wizard, builder, and knowledge flows.

## Quick Start

```bash
npm install
npx expo start
```

## Run on Your Phone (Expo Go)

1. Install [Expo Go](https://expo.dev/go) on your device
2. Make sure phone and computer are on the same Wi‑Fi
3. Scan the QR code from the terminal
4. If not on same network, use: `npx expo start --tunnel`

## Connect to Local Backend

To talk to the BootForge web server:

```bash
EXPO_PUBLIC_API_URL=http://YOUR_LAN_IP:5000 npx expo start
```

Find your LAN IP: `ifconfig` (macOS/Linux) or `ipconfig` (Windows).

## Routes

- **/** – Home
- **/wizard** – USB wizard flow
- **/builder** – USB builder
- **/knowledge** – Knowledge base
- **/dev/theme-lab** – Theme development
- **/oauth/callback** – OAuth redirect handler
