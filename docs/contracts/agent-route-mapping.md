# Agent Route Mapping

PR7 maps existing route families to the Phoenix Agent contract. It does not move files, rewrite routes, or make any dangerous operation executable.

## Canonical Phoenix Agent Routes

| Phoenix Agent route | Purpose | Existing route families that feed it |
| --- | --- | --- |
| `GET /health` | Agent availability, version, implementation status, capabilities. | `GET /`, `GET /api/health`, `GET /api/v1/health`, website health routes, Express `/api/health`, tRPC `system.health`. |
| `GET /system/summary` | Host OS, hardware summary, capability flags, safety policy summary. | `GET /api/hardware`, `GET /api/system/info`, `GET /api/system/metrics`, `POST /api/v1/hardware/detect`, BootCamp Mac detection. |
| `GET /devices` | Known storage devices with explicit identity. | `GET /api/devices`, `GET /api/devices/{device_id}`, `POST /api/devices/refresh`, storage device client paths. |
| `GET /devices/removable` | Removable non-system candidates. | `GET /api/v1/usb/devices`, `GET /storage/devices/usb`, `backend/core/device_scanner.py`, BootCamp USB manager helpers. |
| `POST /safety/evaluate` | Policy and low-level gate evaluation. | `POST /api/safety-check`, `POST /api/v1/safety/validate`, safety portions of recipe/build routes. |
| `POST /operations/preview` | Non-destructive operation preview. | Recipe build/validate, OCLP compatibility checks, BootCamp detect/compatibility, image verification, workflow dry-run, disk repair previews. |
| `POST /operations/execute` | Placeholder for future execution after preview. | USB build, BootCamp install, workflow run, erase/mount/unmount client methods, remote command prototypes. |
| `GET /operations/{operation_id}` | Operation status. | Build progress/status, installation status, bulk-operation status, admin installation detail, WebSocket progress concepts. |
| `GET /logs/export` | Placeholder for future log export. | Admin audit-log, diagnostics logs, build/installation logs. |
| `POST /reports/bundle` | Placeholder for future report bundle. | Diagnostics, admin dashboard metrics, installation summaries, report crate concepts. |

## Route Family Decisions

| Existing family | Representative files | Future Agent target | Decision | Safety note |
| --- | --- | --- | --- | --- |
| Health and metadata | `backend/main.py`, `server/main.py`, `server/api.py`, `server/_core/index.ts`, `website/web_server.py` | `GET /health` | Consolidate later into one Agent health shape. | Read-only; avoid letting website health define Agent readiness. |
| Hardware/system summary | `backend/main.py`, `server/main.py`, `server/api.py`, BootCamp detectors | `GET /system/summary` | Harvest detection code after schema alignment. | Read-only but privacy-sensitive; serial numbers and hostnames need redaction rules. |
| Device listing | `backend/core/device_scanner.py`, `server/bootcamp/usb_manager.py`, mobile enterprise client storage paths | `GET /devices`; `GET /devices/removable` | Normalize around `Device` and `DeviceRef`. | System disks protected by default; path-only ids are not sufficient. |
| Safety validation | `backend/core/usb_builder.py`, `server/api.py`, `phoenix-core-mobile/lib/api/usb_creation_routes.py` | `POST /safety/evaluate`; `POST /operations/preview` | Preserve safety ideas, but move policy ownership to Agent and low-level gates to Rust. | Safety tokens must include preview freshness, device fingerprint, and audit context. |
| USB build and imaging | `backend/main.py`, `server/main.py`, `server/api.py`, mobile USB routes | `POST /operations/preview`; `POST /operations/execute` placeholder; `GET /operations/{operation_id}` | Block execution until Agent, Rust safety gates, and tests exist. | Destructive; UI must never call disk write helpers directly. |
| Recipes and workflows | `backend/main.py`, `server/api.py`, `phoenix-core-mobile/lib/api/usb_creation_routes.py` | Operation catalog; workflow-engine crate; `POST /operations/preview` | Harvest planning concepts and recipe data. | Recipes cannot grant execution permission. |
| OCLP | `backend/core/oclp_integration.py`, `desktop/src/core/oclp_*`, `server/bootcamp` compatibility helpers | `operation_type=oclp.evaluate` | Keep as BootForge capability behind Agent previews. | Third-party version, model detection, and patch side effects must be explicit. |
| BootCamp drivers | `server/bootcamp/*`, `server/routers/bootcamp.py`, `legacy/bootcamp` | `operation_type=bootcamp.prepare_drivers` | Keep BootForge ownership; route execution through Agent lifecycle. | Driver install/update mutates host state and requires signed package policy. |
| Diagnostics and reports | `backend/main.py`, admin dashboard/audit routes, `crates/report` | `GET /logs/export`; `POST /reports/bundle` | Harvest into report bundle model. | Redaction and retention rules required before implementation. |
| Admin dashboards | `server/routers/admin.py`, `server/admin/*.py`, `server/api_fastapi.py` | Mostly outside Agent; possible future reports/operation history | Defer; do not let admin prototypes define local Agent auth. | Privileged auth/session model is unresolved. |
| Express/tRPC/OAuth | `server/_core/index.ts`, `server/_core/oauth.ts`, `server/routers.ts` | Not Phoenix Agent core | Treat as Web/Mobile generated transitional stack. | App/cloud identity is separate from local destructive-operation authorization. |
| Legacy server OpenAPI docs | `server/openapi.yaml` | Reference only; superseded by `services/phoenix-agent/contracts/openapi.yaml` | Use as comparison input, not source of truth. | Several paths omit `/api/v1` and do not express preview-first safety. |
| Website/download routes | `website/web_server.py` | Phoenix Web; possible checksum/image verification references | Keep outside Agent. | Downloads require signing/checksum policy, not Agent route migration. |
| Multi-device remote management | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Future fleet/service contract, not PR7 Agent core | Feature harvest only. | Remote command and bulk operations are high-risk and blocked. |

## Operation Type Mapping

| Operation type | Existing sources | Allowed PR7 behavior | Future owner |
| --- | --- | --- | --- |
| `media.create_boot_usb` | `/api/build/start`, `/api/v1/usb/build`, `/api/workflows/run`, `/build/start` client methods | Preview contract only; execution placeholder only. | BootForge through Phoenix Agent |
| `media.verify_image` | `/api/images`, `/api/images/{image_id}`, website checksum/verify routes | Read-only catalog and verification concepts only. | BootForge |
| `disk.inspect` | `/api/devices`, `/api/v1/usb/devices`, `/storage/devices*` client paths | Read-only listing only. | Phoenix Agent |
| `disk.repair_preview` | Legacy recovery and disk repair concepts | Preview contract only. | BootForge |
| `bootcamp.prepare_drivers` | `/api/v1/bootcamp/*`, driver database and installer modules | Preview contract only; install blocked. | BootForge |
| `oclp.evaluate` | `/api/oclp/*`, BootCamp/Mac compatibility helpers, OCLP desktop modules | Read-only evaluation and preview only. | BootForge |
| `phoenix_key.prepare_rescue` | Recovery USB workflows and Phoenix Key blueprint references | Preview contract only. | Phoenix Key |
| `report.collect_diagnostics` | `/api/diagnostics`, admin audit/metrics, `crates/report` | Report placeholder only. | Phoenix Agent |

## Explicit Non-Migration Decisions

- `server/_core/oauth.ts` routes are not Phoenix Agent auth.
- `server/routers.ts` tRPC procedures are not the canonical Agent API.
- `website/web_server.py` API routes are Phoenix Web/demo/download surfaces, not the local Agent.
- `phoenix-core-mobile/lib/api/multi_device_routes.py` remote-command and bulk-operation routes are blocked until a future fleet trust model exists.
- `services/api.ts` and `mobile/src/services/api.ts` are transitional clients. They should be replaced or wrapped by the typed Phoenix Agent SDK instead of expanded.

## Migration Readiness Checklist

Before any route implementation migrates into `services/phoenix-agent`, PRs must prove:

- the route maps to one canonical Agent contract endpoint or a documented future extension,
- destructive operations use preview before execute,
- device identity includes `device_id`, `identity_fingerprint`, and stable path evidence,
- system disks are blocked by default,
- Rust safety gates are called for low-level risk checks,
- audit/report hooks exist for privileged operations,
- UI apps call the SDK and do not invoke disk/system helpers directly,
- tests cover read-only, preview, blocked, and placeholder paths.
