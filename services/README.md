# Phoenix Services

`services/` is the future home for long-running Phoenix Platform services and API bridges.

The first canonical service target is `phoenix-agent/`, which will become the local bridge between user-facing apps and system-level Rust/Python capabilities.

Existing service-like code remains in place for now:

- `backend/`
- `server/`
- `server/_core/`
- `website/web_server.py`
- `services/api.ts`

No service source is migrated in PR 3.
