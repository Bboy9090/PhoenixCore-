# Phoenix Agent Migration Notes

Current source candidates:

- FastAPI backend: `backend/main.py` and `backend/`.
- Python and TypeScript server stack: `server/main.py`, `server/api_fastapi.py`, `server/_core/index.ts`, and related routers.
- Existing API client bridge: `services/api.ts`.
- Rust safety/workflow/report/device primitives: `crates/`.
- BootForge operational workflows: `desktop/src/core/`, `desktop/src/recovery/`, and `desktop/src/imaging/`.

Migration rule:

Define the Phoenix Agent contract before moving implementations. Do not merge every backend into one service until route ownership, privilege boundaries, and safety gates are clear.

Not migrated in PR 3:

- FastAPI routes.
- TypeScript server routes.
- Device and USB workflows.
- Rust service bindings.
