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

## Connect to the Phoenix Core API (required for USB flows)

The app drives the **FastAPI** backend on the computer that has the USB drive (`backend/main.py`, default port **8000**). The phone does not write to USB directly.

```bash
# On the host machine (same Wi‑Fi as the phone):
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

# On your dev machine when starting Expo:
EXPO_PUBLIC_API_URL=http://YOUR_LAN_IP:8000 npx expo start
```

Find your LAN IP: `ifconfig` (macOS/Linux) or `ipconfig` (Windows).

## Audit / destructive job history (host)

After a failed or completed USB job, review durable records on the **host**:

- `GET /api/audit/jobs/summary?limit=20` — one line per job id  
- `GET /api/audit/query?job_id=<uuid>` — full timeline for one job  
- `POST /api/audit/rebuild-index` — if SQLite index is empty but JSONL exists  

The TypeScript client exposes `phoenixClient.getAuditJobsSummary()`, `queryAudit()`, `rebuildAuditIndex()`. See **`docs/AUDIT_LOG.md`**.

**Recovery:** There is **no automatic rollback**. Treat the stick as suspect after a mid-write failure; re-image from BootForge on the desktop if unsure.

## Routes

- **/** – Home
- **/wizard** – USB wizard flow
- **/builder** – USB builder
- **/knowledge** – Knowledge base
- **/dev/theme-lab** – Theme development
- **/oauth/callback** – OAuth redirect handler
