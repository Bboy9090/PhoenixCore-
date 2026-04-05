# Root Expo / pnpm / tRPC template (non-core)

This directory holds the **Manus-style** template that previously cluttered the repository root. It is **not** Phoenix Core USB, BootForge, or `phoenix-core-mobile/`.

## Run

```bash
cd experimental/root-app-template
pnpm install
pnpm dev
```

## Contents

- `package.json`, `pnpm-lock.yaml` — Node workspace
- `server/` — tRPC / Express template (`server/_core/`)
- `app/`, `components/`, etc. — Expo Router app shell
- `drizzle/` — DB template

## Product apps (canonical)

| Use | Path |
|-----|------|
| Phoenix mobile + USB remote | `phoenix-core-mobile/` + `backend/` FastAPI |
| BootForge desktop | `desktop/` + root `main.py` |
| Shared safety | `packages/phoenix_safety/` |

See **`../../ROOT_APP_TEMPLATE.redirect.md`** and **`../../docs/REPO_STATUS_MAP.md`**.
