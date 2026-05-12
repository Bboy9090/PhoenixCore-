# Phoenix Contracts

This directory defines platform contracts before source migration.

PR6 is contract and scaffold only. It does not move backend, server, crate, app, or legacy code, and it does not make dangerous system operations executable.

## Contract Set

- `phoenix-agent-api.md` - Phoenix Agent HTTP API boundary.
- `safety-gates.md` - safety ownership, preview, and policy rules.
- `device-model.md` - explicit device identity model.
- `operation-lifecycle.md` - preview, execute placeholder, status, report, and log lifecycle.
- `error-model.md` - stable error envelope and status code rules.

## Implementation Source Of Truth

The contract is the target boundary for later migration from:

- `backend/`
- `server/`
- `services/api.ts`
- `desktop/`
- `crates/`
- `legacy/`

Until implementation PRs wire a real service, these contracts are non-executable design artifacts.

## Hard Rule

UI apps may request operations only. Phoenix Agent owns policy checks. Rust crates own low-level safety logic. Destructive operations must require preview first, system disks are protected by default, and device identity must be explicit.
