# Phoenix Agent Migration Notes

Current source candidates:

- FastAPI backend: `backend/main.py` and `backend/`.
- Python and TypeScript server stack: `server/main.py`, `server/api_fastapi.py`, `server/api.py`, `server/api_modern.py`, `server/_core/index.ts`, `server/bootcamp/*`, `server/admin/*`, and related routers.
- Existing API client bridges: `services/api.ts`, `mobile/src/services/api.ts`, and `phoenix-core-mobile/lib/api*.ts`.
- Rust safety/workflow/report/device primitives: `crates/`.
- BootForge operational workflows: `desktop/src/core/`, `desktop/src/recovery/`, and `desktop/src/imaging/`.

Migration rule:

Define the Phoenix Agent contract before moving implementations. Do not merge every backend into one service until route ownership, privilege boundaries, and safety gates are clear.

PR6 contract additions:

- `contracts/openapi.yaml` defines health, system summary, devices, removable drives, operation preview, operation execute placeholder, operation status, log export placeholder, report bundle placeholder, and safety evaluation.
- `contracts/operation-catalog.json` records operation families and safety requirements.
- `sdk/typescript/phoenix-agent-client.ts` defines typed request and response models and safe client methods.

PR7 route mapping additions:

- `../../docs/contracts/backend-route-inventory.md` records existing backend, server, website, mobile prototype, and API client surfaces.
- `../../docs/contracts/agent-route-mapping.md` maps current route families to Phoenix Agent endpoints and operation types.
- `contracts/openapi.yaml` and `contracts/operation-catalog.json` now reference the PR7 mapping documents.

Migration guidance:

- `services/api.ts` may migrate only after it is reconciled with this contract as a typed Phoenix Agent client or generated SDK.
- `backend/` and `server/` routes should not be merged blindly; first map each route to a Phoenix Agent endpoint, app-local concern, or archive candidate.
- Express/tRPC/OAuth and website download routes are not Phoenix Agent core unless a later decision record says otherwise.
- BootForge and Phoenix Key should use the same preview-first operation lifecycle instead of maintaining separate execution flows.
- Rust crates should become the safety and host-adapter implementation layer behind the Agent, not UI-owned imports.

Not migrated yet:

- FastAPI routes.
- TypeScript server routes.
- Device and USB workflows.
- Rust service bindings.
- BootForge execution workflows.
- Phoenix Key rescue workflows.
- Report bundle generation.
- Log export implementation.
