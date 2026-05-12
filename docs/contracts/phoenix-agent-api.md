# Phoenix Agent API Contract

Phoenix Agent is the local API bridge for Phoenix Platform apps.

This contract defines the first stable surface for Phoenix Control Center, Phoenix Mobile, BootForge, and Phoenix Key. It is intentionally conservative: operation execution is present only as a placeholder contract and must not be wired to destructive behavior until safety gates and tests exist.

PR7 maps existing `backend/`, `server/`, website, mobile prototype, and TypeScript client surfaces to this contract. See `backend-route-inventory.md` for the current route inventory and `agent-route-mapping.md` for the migration target decisions.

## Consumers

- Phoenix Control Center calls Phoenix Agent for system state, devices, previews, operations, logs, and report bundles.
- Phoenix Mobile calls Phoenix Agent through a typed client or remote-safe bridge.
- BootForge and Phoenix Key use the same operation lifecycle instead of inventing separate destructive execution paths.
- Phoenix Web may call non-privileged status or documentation APIs only.

## Endpoints

| Method | Path | Purpose | Implementation status |
| --- | --- | --- | --- |
| `GET` | `/health` | Check Agent availability and version. | Contract only |
| `GET` | `/system/summary` | Read host OS, hardware summary, service state, and capability flags. | Contract only |
| `GET` | `/devices` | List known storage devices with explicit identity. | Contract only |
| `GET` | `/devices/removable` | List removable non-system candidate devices. | Contract only |
| `POST` | `/safety/evaluate` | Evaluate policy and low-level safety gates. | Contract only |
| `POST` | `/operations/preview` | Create a non-destructive operation preview. | Contract only |
| `POST` | `/operations/execute` | Placeholder for future execution after preview. | Placeholder only |
| `GET` | `/operations/{operation_id}` | Read operation status. | Contract only |
| `GET` | `/logs/export` | Placeholder for log export. | Placeholder only |
| `POST` | `/reports/bundle` | Placeholder for report bundle creation. | Placeholder only |

## Operation Families

Initial operation families:

- `media.create_boot_usb`
- `media.verify_image`
- `disk.inspect`
- `disk.repair_preview`
- `bootcamp.prepare_drivers`
- `oclp.evaluate`
- `phoenix_key.prepare_rescue`
- `report.collect_diagnostics`

Only non-destructive previews are allowed until implementation PRs add safety-backed execution.

## Migration Notes

Existing code that may migrate later:

- `backend/main.py` and `backend/` route logic.
- `server/main.py`, `server/api_fastapi.py`, `server/api.py`, `server/api_modern.py`, `server/bootcamp/*`, `server/admin/*`, and `server/routers/*`.
- `services/api.ts`, `mobile/src/services/api.ts`, and `phoenix-core-mobile/lib/api*.ts`, after reconciling types with this contract.
- `desktop/src/core/*`, `desktop/src/recovery/*`, and `desktop/src/imaging/*` workflows.
- `crates/safety`, `crates/imaging`, `crates/workflow-engine`, `crates/report`, and host crates.

Existing code that should not become Phoenix Agent core without a separate decision:

- `server/_core/oauth.ts` and generated Express/tRPC auth routes.
- `website/web_server.py` download, install, and demo routes.
- `server/admin/*` dashboard/auth routes, except possible future report or operation-history concepts.
- `phoenix-core-mobile/lib/api/multi_device_routes.py` remote command and bulk operation routes until a fleet trust model exists.

Not implemented in PR6:

- no running Phoenix Agent service,
- no disk writes,
- no imaging,
- no driver installation,
- no OCLP patching,
- no bootloader mutation,
- no report bundle generation,
- no log export implementation.
