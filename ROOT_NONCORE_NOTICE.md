# Non-core paths at repository root

**Phoenix Core product** code lives primarily under:

- `desktop/`, `backend/`, `packages/phoenix_safety/`, `phoenix-core-mobile/`, `crates/`, `apps/cli/`, `website/`, `tests/`, `docs/`

**At this root you may also see:**

- **`package.json`** — Expo / Node / tRPC **template workspace** (pnpm). It is **not** the same app as `phoenix-core-mobile/`. Prefer the Expo app under `phoenix-core-mobile/` for Phoenix mobile + USB remote control.
- **`server/`** — Legacy Flask + template server code; **deprecated** for Phoenix USB API (`backend/` is canonical).

See **`experimental/README.md`** and **`docs/REPO_STATUS_MAP.md`**.
