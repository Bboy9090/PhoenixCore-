# Phoenix Agent

Phoenix Agent is the future backend bridge and local system service for Phoenix Platform.

PR8 gives the Agent a safe TypeScript mock skeleton. It is non-destructive by design: it returns mock system/device data, creates preview-only operation responses, and rejects commits for dangerous operations.

## Purpose

- Provide one typed local API boundary for Phoenix Control Center, Phoenix Mobile, BootForge, and Phoenix Key.
- Keep UI apps out of direct disk, USB, driver, boot, OCLP, workflow, and remote-command execution.
- Prove the Phoenix Agent contract shape before migrating existing `backend/`, `server/`, `desktop/`, `crates/`, or legacy implementation code.

## Non-Destructive Status

This service does not:

- write USB media,
- erase disks,
- mount or unmount disks,
- install BootCamp drivers,
- run OCLP patching,
- execute workflows,
- execute remote commands,
- mutate real devices,
- migrate existing backend routes.

All device data is mock data from `src/mock/mock-devices.ts`.

## Endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| `GET` | `/health` | Returns Phoenix Agent mock health. |
| `GET` | `/v1/system/status` | Returns mock OS/platform/Agent status. |
| `GET` | `/v1/devices` | Returns mock devices only. |
| `GET` | `/v1/devices/:id` | Returns mock device detail or `404`. |
| `GET` | `/v1/operations/catalog` | Returns a safe static operation catalog. |
| `POST` | `/v1/operations/preview` | Returns a preview object only. |
| `POST` | `/v1/operations/commit` | Rejects commits with a blocked response. |
| `GET` | `/v1/safety/policy` | Returns the preview-first policy. |
| `GET` | `/v1/safety/blocked-operations` | Returns blocked destructive operations. |

Compatibility aliases also exist for a few PR6 contract paths, including `/system/summary`, `/devices`, `/devices/removable`, `/operations/preview`, and `/operations/execute`.

## Blocked Operations

PR8 blocks:

- `usb.build`
- `usb.erase`
- `disk.erase`
- `disk.mount`
- `disk.unmount`
- `bootcamp.install`
- `oclp.patch`
- `workflow.run`
- `remote.command`
- `bulk.operation`
- `firmware.flash`
- `restore.write`

Every blocked commit response includes:

- `operationId`
- `blocked: true`
- `reason`
- `requiredFutureGates`
- `safeNextStep`

## Future Gates

Execution remains blocked until future PRs provide:

- policy approval,
- Rust safety gate,
- device fingerprint,
- preview freshness,
- audit log,
- dry-run verification,
- explicit user confirmation,
- test coverage.

## How To Run

Install dependencies from this folder:

```powershell
npm install
```

Start the mock service:

```powershell
npm run build
node dist/src/index.js
```

By default it listens on `http://127.0.0.1:7788`. Override with `PHOENIX_AGENT_PORT`.

## How To Test

```powershell
npm run typecheck
npm test
```

The tests start the mock server on an ephemeral local port. They do not write disks, call system tools, or execute dangerous operations.

## Contract Artifacts

- `contracts/openapi.yaml` documents the existing PR6 contract and PR8 `/v1` mock endpoints.
- `contracts/operation-catalog.json` records operation families, blocked operations, and required future gates.
- `sdk/typescript/` remains the typed client boundary for apps.
- `../../docs/contracts/backend-route-inventory.md` records the current route inventory.
- `../../docs/contracts/agent-route-mapping.md` records migration target mapping.

## Intentionally Not Implemented

PR8 does not wire real device scanning, imaging, BootCamp, OCLP, workflow execution, log export, report bundles, auth, persistence, Rust crate bindings, or migration from legacy backend routes.
