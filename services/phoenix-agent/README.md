# Phoenix Agent

Phoenix Agent is the future backend bridge and local system service for Phoenix Platform.

Canonical direction:

- Rust-first for privileged, safety-sensitive, or OS-facing operations.
- FastAPI transitional code is acceptable while contracts are being consolidated.
- Apps should call Phoenix Agent instead of reaching directly into scattered scripts.
- Agent APIs should expose device state, diagnostics, imaging workflows, reports, update state, and safe execution gates.

No source is migrated here in PR 3.
