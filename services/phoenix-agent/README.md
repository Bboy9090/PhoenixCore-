# Phoenix Agent

Phoenix Agent is the future backend bridge and local system service for Phoenix Platform.

Canonical direction:

- Rust-first for privileged, safety-sensitive, or OS-facing operations.
- FastAPI transitional code is acceptable while contracts are being consolidated.
- Apps should call Phoenix Agent instead of reaching directly into scattered scripts.
- Agent APIs should expose device state, diagnostics, imaging workflows, reports, update state, and safe execution gates.

PR6 adds the first contract boundary, and PR7 maps current backend/API surfaces to it:

- `contracts/openapi.yaml` - HTTP API contract.
- `contracts/operation-catalog.json` - preview-first operation catalog.
- `sdk/typescript/` - safe TypeScript client boundary for apps.
- `../../docs/contracts/backend-route-inventory.md` - current route inventory.
- `../../docs/contracts/agent-route-mapping.md` - migration target mapping.

This scaffold is intentionally non-executable. It does not wire destructive operations, move backend code, or replace `backend/`, `server/`, `desktop/`, `crates/`, or legacy source.

## Safety Rule

UI apps may request operations only. Phoenix Agent owns policy checks, and Rust crates own low-level safety logic. Destructive operations must require preview first.
