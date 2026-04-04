/**
 * PhoenixCore Mobile — API base URL for the Phoenix Core **FastAPI** backend
 * (`backend/main.py`, default port **8000**). USB creation runs on that machine.
 *
 * - iOS Simulator: `http://127.0.0.1:8000`
 * - Android Emulator: `http://10.0.2.2:8000`
 * - Physical phone on same Wi‑Fi: your computer's LAN IP, e.g. `http://192.168.1.x:8000`
 *
 * Set `EXPO_PUBLIC_API_URL` in `.env` / EAS secrets for production builds.
 */
export const API_BASE_URL =
  (typeof process !== 'undefined' &&
    process.env?.EXPO_PUBLIC_API_URL) ||
  'http://127.0.0.1:8000';
