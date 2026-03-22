/**
 * PhoenixCore Mobile – configuration
 * API base URL for the BootForge web server (web_server.py).
 *
 * On device/simulator:
 * - iOS Simulator: use http://localhost:5000
 * - Android Emulator: use http://10.0.2.2:5000
 * - Physical device on same WiFi: use your computer's LAN IP, e.g. http://192.168.1.x:5000
 *
 * Set EXPO_PUBLIC_API_URL in .env or .env.local to override.
 */
export const API_BASE_URL =
  (typeof process !== 'undefined' &&
    process.env?.EXPO_PUBLIC_API_URL) ||
  'http://localhost:5000';
