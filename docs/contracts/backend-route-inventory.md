# Backend Route Inventory

PR7 maps existing backend, server, API, and client surfaces to the Phoenix Agent contract without moving implementation files.

This is an inventory, not a migration. All current source files remain in place.

## Audit Commands

Commands used for this route inventory:

```powershell
git grep -n -E "@(app|router)\.(get|post|put|delete|websocket)|app\.route|Blueprint\(|APIRouter\(" HEAD -- backend server website phoenix-core-mobile/lib/api legacy/"Integrate Backend and USB Features in Phoenix Core App"
git grep -n -E "client\.(get|post|put|delete)|fetch\(|axios\.|/api/|/health|/usb" HEAD -- services mobile phoenix-core-mobile
git show HEAD:server/openapi.yaml
git show HEAD:server/_core/index.ts
git show HEAD:server/_core/oauth.ts
git show HEAD:server/_core/systemRouter.ts
git show HEAD:server/routers.ts
```

## Safety Levels

| Level | Meaning |
| --- | --- |
| `read-only` | Reads health, status, metadata, catalogs, or device summaries. |
| `preview` | Performs validation, recipe planning, compatibility checks, or dry-run style preparation. |
| `destructive` | Can write media, erase or modify devices, install drivers, cancel active work, or alter system state. |
| `privileged` | Requires elevated policy or authorization even if the current implementation is mocked or read-heavy. |
| `unknown` | Purpose or runtime behavior needs source review before migration. |

## Inventory Summary

| Surface | Current role | PR7 disposition |
| --- | --- | --- |
| `backend/main.py` | Primary FastAPI recovery, USB, OCLP, diagnostics, device, and system API. | Harvest into Phoenix Agent and BootForge contracts. |
| `legacy/Integrate Backend and USB Features in Phoenix Core App/main.py` | Legacy copy of the `backend/main.py` style API. | Archive reference only; do not migrate separately. |
| `server/main.py` | FastAPI industrial backend with BootCamp/admin routers and USB build task runner. | Harvest BootForge and Agent ideas; block direct execution until Agent safety gates exist. |
| `server/api.py` and `server/api_modern.py` | Duplicate Flask-era USB/hardware/safety APIs. | Compare against Agent contract; likely archive one after migration. |
| `server/api_fastapi.py` | Separate FastAPI BootCamp/admin API. | Harvest BootCamp status and driver concepts; avoid duplicate Agent surface. |
| `server/routers/*.py` | FastAPI routers for BootCamp and admin. | BootCamp routes map through Agent operation lifecycle; admin routes are not Agent core. |
| `server/bootcamp/api.py` and `server/admin/*.py` | Flask blueprints for BootCamp and admin dashboards. | Reference for BootForge and admin/reporting; privileged routes require policy review. |
| `server/_core/*.ts` and `server/routers.ts` | Express/tRPC/OAuth generated app backend. | Generated/transitional web/mobile auth surface; not Phoenix Agent core. |
| `server/openapi.yaml` | Legacy documented OpenAPI surface for USB/hardware/safety/build APIs. | Treat as reference documentation, not canonical Agent contract. |
| `website/web_server.py` | Flask marketing/download/install web server with lightweight API endpoints. | Phoenix Web owner; only checksum/catalog ideas may be harvested. |
| `phoenix-core-mobile/lib/api/*.py` | Mobile-era FastAPI route prototypes for USB creation and multi-device management. | Feature harvest candidate; remote command and bulk operation routes require strict Agent policy if revived. |
| `services/api.ts`, `mobile/src/services/api.ts`, `phoenix-core-mobile/lib/api*.ts` | Existing TypeScript clients for old backend shapes. | Transitional clients; future calls should use the Phoenix Agent SDK. |

## Backend FastAPI Surface

`legacy/Integrate Backend and USB Features in Phoenix Core App/main.py` mirrors the same route family as `backend/main.py`. It is listed as a legacy source in each row so the migration does not duplicate that implementation.

| Current path | Current file | Current purpose | Future contract target | Migration status | Safety | Owner | Risks before migration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET /` | `backend/main.py`; legacy copy | Root API metadata. | `GET /health` | Harvest | `read-only` | Phoenix Agent | Duplicate health shapes across backends. |
| `GET /api/health` | `backend/main.py`; legacy copy | Backend health, uptime, platform, feature flags. | `GET /health`; `GET /system/summary` | Harvest | `read-only` | Phoenix Agent | Response shape differs from Agent contract. |
| `GET /api/devices` | `backend/main.py`; legacy copy | Scan USB/removable devices. | `GET /devices`; `GET /devices/removable` | Harvest | `read-only` | Phoenix Agent | Must normalize identity, system disk flag, and fingerprint. |
| `GET /api/devices/{device_id}` | `backend/main.py`; legacy copy | Look up a device by path or id. | Future `GET /devices/{device_id}` extension; `DeviceRef` | Harvest | `read-only` | Phoenix Agent | Path-based identity is unsafe without stable fingerprint validation. |
| `POST /api/devices/refresh` | `backend/main.py`; legacy copy | Force a fresh device scan. | `GET /devices` with scan semantics or future rescan endpoint | Harvest | `read-only` | Phoenix Agent | Rescan should not mutate device policy state. |
| `GET /api/hardware` | `backend/main.py`; legacy copy | Full hardware profile. | `GET /system/summary` | Harvest | `read-only` | Phoenix Agent | Needs schema reduction and privacy review. |
| `GET /api/hardware/profiles` | `backend/main.py`; legacy copy | Known target hardware profiles and OCLP profiles. | `operation_type=oclp.evaluate`; future catalog endpoint | Harvest | `read-only` | BootForge | Static profile data can drift from OCLP source. |
| `GET /api/system/metrics` | `backend/main.py`; legacy copy | CPU, memory, disk, network, temperature metrics. | `GET /system/summary`; future metrics extension | Harvest | `read-only` | Phoenix Agent | Metrics may expose sensitive host data. |
| `GET /api/system/usb-activity` | `backend/main.py`; legacy copy | USB activity monitor. | `GET /devices`; future event stream | Harvest | `read-only` | Phoenix Agent | Needs event model and privacy boundaries. |
| `GET /api/system/info` | `backend/main.py`; legacy copy | Host OS, platform, boot time, Python details. | `GET /system/summary` | Harvest | `read-only` | Phoenix Agent | Current response leaks runtime details not every UI needs. |
| `GET /api/recipes` | `backend/main.py`; legacy copy | List USB deployment recipes. | `POST /operations/preview`; operation catalog | Harvest | `read-only` | BootForge | Recipe schema is not the Agent operation schema. |
| `GET /api/recipes/{recipe_id}` | `backend/main.py`; legacy copy | Fetch one USB deployment recipe. | `POST /operations/preview`; operation catalog | Harvest | `read-only` | BootForge | Recipe ids must map to stable operation types. |
| `POST /api/safety-check` | `backend/main.py`; legacy copy | Validate device and recipe before USB creation. | `POST /safety/evaluate`; `POST /operations/preview` | Harvest | `preview` | Phoenix Agent | Current confirmation token is not a complete authorization model. |
| `POST /api/build/start` | `backend/main.py`; legacy copy | Start USB build job. | `POST /operations/execute` placeholder only | Block until Agent safety exists | `destructive` | BootForge | Must require preview, token freshness, device fingerprint, and Rust gates. |
| `GET /api/build/{job_id}/progress` | `backend/main.py`; legacy copy | Get USB build progress. | `GET /operations/{operation_id}` | Harvest | `read-only` | Phoenix Agent | Job ids need correlation with preview ids and audit ids. |
| `POST /api/build/{job_id}/cancel` | `backend/main.py`; legacy copy | Cancel an in-progress build. | Future cancel operation extension | Defer | `privileged` | Phoenix Agent | Cancel semantics need idempotency and audit logging. |
| `GET /api/build/jobs/list` | `backend/main.py`; legacy copy | List active/completed USB build jobs. | `GET /operations/{operation_id}` plus future operation list | Defer | `read-only` | Phoenix Agent | Operation history schema not designed yet. |
| `GET /api/oclp/models` | `backend/main.py`; legacy copy | List OCLP-compatible Mac models. | `operation_type=oclp.evaluate`; future catalog endpoint | Harvest | `read-only` | BootForge | Third-party OCLP versioning must be explicit. |
| `GET /api/oclp/check/{model}` | `backend/main.py`; legacy copy | Check OCLP compatibility for a model. | `POST /operations/preview` with `oclp.evaluate` | Harvest | `preview` | BootForge | Model id must be validated against pinned OCLP source. |
| `GET /api/oclp/macos-versions` | `backend/main.py`; legacy copy | List supported macOS versions for OCLP. | `operation_type=oclp.evaluate`; future catalog endpoint | Harvest | `read-only` | BootForge | macOS support matrix may drift. |
| `GET /api/oclp/detect` | `backend/main.py`; legacy copy | Detect current Mac model and compatibility. | `GET /system/summary`; `POST /operations/preview` | Harvest | `read-only` | Phoenix Agent | Host model detection is platform-specific and may need elevated APIs. |
| `GET /api/images` | `backend/main.py`; legacy copy | List local ISO/IMG files and downloadable images. | `operation_type=media.verify_image`; future image catalog | Harvest | `read-only` | BootForge | Scanning home/download paths exposes user file metadata. |
| `GET /api/images/{image_id}` | `backend/main.py`; legacy copy | Fetch one image entry. | `operation_type=media.verify_image`; future image catalog | Harvest | `read-only` | BootForge | Image identity should use path/hash, not only display id. |
| `GET /api/workflows` | `backend/main.py`; legacy copy | List workflow templates. | Operation catalog; workflow-engine crate | Harvest | `read-only` | BootForge | Workflow ids overlap with recipe ids and need canonical naming. |
| `POST /api/workflows/run` | `backend/main.py`; legacy copy | Run a full workflow, defaulting to dry run but capable of starting builds. | `POST /operations/preview`; `POST /operations/execute` placeholder only | Block until Agent safety exists | `destructive` | BootForge | Must not allow UI-triggered direct disk writes. |
| `GET /api/diagnostics` | `backend/main.py`; legacy copy | Run diagnostics and tool availability checks. | `POST /reports/bundle`; `GET /logs/export` | Harvest | `privileged` | Phoenix Agent | Diagnostics may expose paths, installed tools, and environment details. |

## Server FastAPI Surface

| Current path | Current file | Current purpose | Future contract target | Migration status | Safety | Owner | Risks before migration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET /api/v1/health` | `server/main.py` | FastAPI service health. | `GET /health` | Harvest | `read-only` | Phoenix Agent | Version and status fields differ. |
| `POST /api/v1/hardware/detect` | `server/main.py` | Detect Mac hardware with BootCamp detector. | `GET /system/summary`; `POST /operations/preview` for BootCamp prep | Harvest | `read-only` | Phoenix Agent | Mac-only detector must be host-gated. |
| `GET /api/v1/usb/devices` | `server/main.py` | List removable drives with size filtering. | `GET /devices/removable` | Harvest | `read-only` | Phoenix Agent | Query flags must not include system drives by default. |
| `POST /api/v1/recipe/build` | `server/main.py` | Create a USB recipe plan. | `POST /operations/preview` | Harvest | `preview` | BootForge | Recipe model differs from operation preview model. |
| `POST /api/v1/usb/build` | `server/main.py` | Start background USB build by shelling to Phoenix CLI. | `POST /operations/execute` placeholder only | Block until Agent safety exists | `destructive` | BootForge | Builds a shell command from request-derived data; must move behind Rust gates and idempotency. |
| `GET /api/v1/usb/build/{build_id}/status` | `server/main.py` | Return active build progress. | `GET /operations/{operation_id}` | Harvest | `read-only` | Phoenix Agent | In-memory build state must become durable operation state. |

## Flask USB API Duplicates

`server/api.py` and `server/api_modern.py` define the same route family with near-identical responsibilities.

| Current path | Current file | Current purpose | Future contract target | Migration status | Safety | Owner | Risks before migration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET /api/v1/health` | `server/api.py`; `server/api_modern.py` | Flask service health. | `GET /health` | Compare then archive duplicate | `read-only` | Phoenix Agent | Duplicate with `server/main.py`. |
| `POST /api/v1/hardware/detect` | `server/api.py`; `server/api_modern.py` | Hardware detection. | `GET /system/summary` | Compare then harvest | `read-only` | Phoenix Agent | Multiple incompatible hardware response shapes. |
| `GET /api/v1/usb/devices` | `server/api.py`; `server/api_modern.py` | USB device list. | `GET /devices/removable` | Compare then harvest | `read-only` | Phoenix Agent | Device identity must be normalized. |
| `POST /api/v1/recipe/build` | `server/api.py`; `server/api_modern.py` | Build recipe definition. | `POST /operations/preview` | Compare then harvest | `preview` | BootForge | Preview must not imply execution permission. |
| `GET /api/v1/recipe/<recipe_id>/export` | `server/api.py`; `server/api_modern.py` | Export recipe data. | Operation catalog; future export endpoint | Defer | `read-only` | BootForge | Export format is not canonical. |
| `POST /api/v1/usb/build` | `server/api.py`; `server/api_modern.py` | Start USB build. | `POST /operations/execute` placeholder only | Block until Agent safety exists | `destructive` | BootForge | Direct build entrypoint conflicts with Agent lifecycle. |
| `GET /api/v1/usb/build/<build_id>/status` | `server/api.py`; `server/api_modern.py` | Read USB build status. | `GET /operations/{operation_id}` | Harvest | `read-only` | Phoenix Agent | Build ids need correlation and durable state. |
| `POST /api/v1/safety/validate` | `server/api.py`; `server/api_modern.py` | Validate safety for a build. | `POST /safety/evaluate`; `POST /operations/preview` | Harvest | `preview` | Phoenix Agent | Safety response must align with gate names and evidence. |

## BootCamp And Admin APIs

| Current path | Current file | Current purpose | Future contract target | Migration status | Safety | Owner | Risks before migration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET /` | `server/api_fastapi.py` | FastAPI root metadata. | `GET /health` | Reference/harmonize | `read-only` | Phoenix Agent | Duplicate root shape. |
| `GET /api/v1/health` | `server/api_fastapi.py` | FastAPI BootCamp/admin service health. | `GET /health` | Reference/harmonize | `read-only` | Phoenix Agent | Duplicate health shape. |
| `GET /api/v1/bootcamp/health` | `server/routers/bootcamp.py`; `server/bootcamp/api.py` | BootCamp service health. | `GET /health` capability flag | Harvest | `read-only` | BootForge | Duplicate Flask and FastAPI routes. |
| `GET /api/v1/bootcamp/detect-mac` | `server/api_fastapi.py` | Detect Mac system for BootCamp. | `GET /system/summary`; `POST /operations/preview` with `bootcamp.prepare_drivers` | Harvest | `read-only` | BootForge | Uses GET for host detection and differs from POST router/blueprint shape. |
| `POST /api/v1/bootcamp/detect-mac` | `server/routers/bootcamp.py`; `server/bootcamp/api.py` | Detect Mac system and driver compatibility. | `GET /system/summary`; `POST /operations/preview` with `bootcamp.prepare_drivers` | Harvest | `preview` | BootForge | Platform-gated and privacy-sensitive serial/model data. |
| `GET /api/v1/bootcamp/drivers/{mac_id}` | `server/api_fastapi.py` | Return driver package metadata by Mac id. | `POST /operations/preview` with `bootcamp.prepare_drivers`; future driver catalog | Harvest | `read-only` | BootForge | Uses Mac id path while other route uses package id. |
| `GET /api/v1/bootcamp/drivers/{package_id}` | `server/routers/bootcamp.py`; `server/bootcamp/api.py` | Return BootCamp driver package metadata. | `POST /operations/preview` with `bootcamp.prepare_drivers`; future driver catalog | Harvest | `read-only` | BootForge | Driver package provenance must be verified. |
| `GET /api/v1/bootcamp/models` | `server/routers/bootcamp.py`; `server/bootcamp/api.py` | List supported Mac models. | Future driver catalog; `bootcamp.prepare_drivers` preview input | Harvest | `read-only` | BootForge | Driver database freshness and ownership unclear. |
| `GET /api/v1/bootcamp/models/{model_id}` | `server/bootcamp/api.py` | Return one Mac model record. | Future driver catalog | Harvest | `read-only` | BootForge | Response shape must match future catalog. |
| `GET /api/v1/bootcamp/compatibility/{mac_model}` | `server/bootcamp/api.py` | Check BootCamp compatibility. | `POST /operations/preview` with `bootcamp.prepare_drivers` | Harvest | `preview` | BootForge | Compatibility must be versioned with driver database. |
| `POST /api/v1/bootcamp/install` | `server/routers/bootcamp.py`; `server/api_fastapi.py`; `server/bootcamp/api.py` | Start BootCamp driver installation. | `POST /operations/execute` placeholder only | Block until Agent safety exists | `destructive` | BootForge | Driver installation mutates host state and requires explicit authorization. |
| `GET /api/v1/bootcamp/installation/{installation_id}` | `server/api_fastapi.py` | Installation status. | `GET /operations/{operation_id}` | Harvest | `read-only` | Phoenix Agent | Installation state model differs from Agent operation state. |
| `GET /api/v1/bootcamp/install/{installation_id}` | `server/bootcamp/api.py` | Installation status. | `GET /operations/{operation_id}` | Harvest | `read-only` | Phoenix Agent | Duplicate status path. |
| `POST /api/v1/bootcamp/install/{installation_id}/cancel` | `server/bootcamp/api.py` | Cancel BootCamp installation. | Future cancel operation extension | Defer | `privileged` | Phoenix Agent | Cancel must be audited and idempotent. |
| `GET /ws/installation/{installation_id}` | `server/api_fastapi.py` | WebSocket installation progress. | Future operation event stream | Defer | `read-only` | Phoenix Agent | No canonical Agent event stream exists yet. |
| `POST /api/admin/auth/login` | `server/routers/admin.py`; `server/admin/auth.py` | Admin login. | Not Phoenix Agent core | Defer | `privileged` | Web | Auth model is generated/transitional and not local Agent policy. |
| `GET /api/admin/auth/verify` | `server/admin/auth.py` | Verify admin auth token. | Not Phoenix Agent core | Defer | `privileged` | Web | Token model should not be reused blindly. |
| `POST /api/admin/auth/refresh` | `server/admin/auth.py` | Refresh admin auth token. | Not Phoenix Agent core | Defer | `privileged` | Web | Token model should not be reused blindly. |
| `POST /api/admin/auth/logout` | `server/admin/auth.py` | Admin logout. | Not Phoenix Agent core | Defer | `privileged` | Web | Session ownership unclear. |
| `GET /api/admin/health` | `server/routers/admin.py` | Admin health. | Not Phoenix Agent core | Defer | `privileged` | Web | Admin namespace conflicts with Agent local service concept. |
| `GET /api/admin/metrics/installations` | `server/routers/admin.py` | Installation metrics. | `POST /reports/bundle` or future analytics | Defer | `privileged` | Web | Mock/admin metrics should not define core contract. |
| `GET /api/admin/installations` | `server/routers/admin.py` | List installations. | Future operation history | Defer | `privileged` | Web | Needs role model and data retention rules. |
| `GET /api/v1/admin/dashboard` | `server/api_fastapi.py` | Admin dashboard summary. | Not Phoenix Agent core | Defer | `privileged` | Web | Admin dashboard is not Control Center system API. |
| `GET /api/v1/admin/installations` | `server/api_fastapi.py` | Admin installation list. | Future operation history | Defer | `privileged` | Web | Duplicate admin model. |
| `GET /admin/health` | `server/admin/dashboard.py` | Flask admin health. | Not Phoenix Agent core | Defer | `privileged` | Web | Separate prefix and auth decorator. |
| `GET /admin/metrics/installations` | `server/admin/dashboard.py` | Installation metrics. | Future reports/analytics | Defer | `privileged` | Web | Mock data and role model need review. |
| `GET /admin/metrics/system` | `server/admin/dashboard.py` | Admin system metrics. | Future reports/analytics | Defer | `privileged` | Web | May expose sensitive service metrics. |
| `GET /admin/installations` | `server/admin/dashboard.py` | List installations. | Future operation history | Defer | `privileged` | Web | Duplicate with `/api/admin/installations`. |
| `GET /admin/installations/<installation_id>` | `server/admin/dashboard.py` | Installation details. | `GET /operations/{operation_id}` or future report | Defer | `privileged` | Web | Mock shape differs from Agent operations. |
| `GET /admin/backups` | `server/admin/dashboard.py` | List driver backups. | Future report/backup catalog | Defer | `privileged` | Web | Backup deletion policy not defined. |
| `GET /admin/drivers/updates` | `server/admin/dashboard.py` | List driver database updates. | Future driver catalog audit | Defer | `privileged` | Web | Driver update provenance not defined. |
| `POST /admin/drivers/update` | `server/admin/dashboard.py` | Apply driver database update. | Future privileged maintenance operation | Defer | `destructive` | BootForge | Mutates driver database and requires signed update policy. |
| `POST /admin/installations/<installation_id>/cancel` | `server/admin/dashboard.py` | Cancel active installation. | Future cancel operation extension | Defer | `privileged` | Phoenix Agent | Needs audit and idempotency. |
| `POST /admin/backups/<backup_id>/delete` | `server/admin/dashboard.py` | Delete backup. | Future privileged maintenance operation | Defer | `destructive` | Web | Destructive data deletion policy not defined. |
| `GET /admin/audit-log` | `server/admin/dashboard.py` | Read admin audit log. | `POST /reports/bundle`; future audit API | Defer | `privileged` | Web | Audit retention and redaction model missing. |

## Express And tRPC Surface

| Current path | Current file | Current purpose | Future contract target | Migration status | Safety | Owner | Risks before migration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET /api/health` | `server/_core/index.ts` | Node/Express health route. | `GET /health` only if Node service remains | Defer | `read-only` | Web | Generated stack conflicts with Agent service identity. |
| `/api/trpc` | `server/_core/index.ts`; `server/routers.ts` | tRPC mount for generated app routers. | Not Phoenix Agent core | Defer | `unknown` | Web | Procedure-level auth and generated conventions do not match Agent contract. |
| `system.health` | `server/_core/systemRouter.ts` | tRPC public health procedure. | `GET /health` only if retained | Defer | `read-only` | Web | tRPC contract should not drive Agent API. |
| `system.notifyOwner` | `server/_core/systemRouter.ts` | tRPC admin notification mutation. | Not Phoenix Agent core | Defer | `privileged` | Web | Generated notification path with external side effects. |
| `auth.me` | `server/routers.ts` | tRPC current user. | Not Phoenix Agent core | Defer | `read-only` | Web | Web auth user is separate from local Agent authorization. |
| `auth.logout` | `server/routers.ts` | tRPC logout mutation. | Not Phoenix Agent core | Defer | `privileged` | Web | Session ownership unclear. |
| `GET /api/oauth/callback` | `server/_core/oauth.ts` | OAuth callback and frontend redirect. | Not Phoenix Agent core | Defer | `privileged` | Web | Generated OAuth path should not become local Agent auth. |
| `GET /api/oauth/mobile` | `server/_core/oauth.ts` | OAuth mobile exchange. | Not Phoenix Agent core | Defer | `privileged` | Mobile | Generated mobile auth path should remain outside Agent disk policy. |
| `POST /api/auth/logout` | `server/_core/oauth.ts` | Express auth logout. | Not Phoenix Agent core | Defer | `privileged` | Web | Duplicate logout with tRPC and Flask admin. |
| `GET /api/auth/me` | `server/_core/oauth.ts` | Express current authenticated user. | Not Phoenix Agent core | Defer | `read-only` | Web | Cloud/app user differs from local system authorization. |
| `POST /api/auth/session` | `server/_core/oauth.ts` | Convert bearer token to session cookie. | Not Phoenix Agent core | Defer | `privileged` | Web | Cookie/session mechanics not relevant to local Agent safety. |

## Legacy Server OpenAPI Documentation Surface

`server/openapi.yaml` documents a route family that overlaps with the Flask and FastAPI USB backends. PR7 treats it as historical API documentation, not the canonical future contract.

| Current path | Current file | Current purpose | Future contract target | Migration status | Safety | Owner | Risks before migration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET /health` | `server/openapi.yaml` | Documented health check. | `GET /health` | Reference only | `read-only` | Phoenix Agent | Path omits `/api/v1` used by several implementations. |
| `POST /hardware/detect` | `server/openapi.yaml` | Documented hardware detection. | `GET /system/summary` | Reference only | `read-only` | Phoenix Agent | Schema must be reconciled with implementation routes. |
| `GET /usb/devices` | `server/openapi.yaml` | Documented USB list. | `GET /devices/removable` | Reference only | `read-only` | Phoenix Agent | Device identity schema is not Agent-ready. |
| `GET /usb/devices/{device_id}` | `server/openapi.yaml` | Documented USB device detail. | Future `GET /devices/{device_id}` extension | Reference only | `read-only` | Phoenix Agent | Path-only device id is not safe enough. |
| `POST /recipe/build` | `server/openapi.yaml` | Documented recipe build. | `POST /operations/preview` | Reference only | `preview` | BootForge | Recipe build must not imply execution. |
| `POST /recipe/validate` | `server/openapi.yaml` | Documented recipe validation. | `POST /operations/preview`; `POST /safety/evaluate` | Reference only | `preview` | BootForge | Validation/gate naming differs from Agent safety model. |
| `POST /safety/check` | `server/openapi.yaml` | Documented safety check. | `POST /safety/evaluate` | Reference only | `preview` | Phoenix Agent | Safety response must carry gate evidence. |
| `POST /usb/build` | `server/openapi.yaml` | Documented USB build start. | `POST /operations/execute` placeholder only | Reference only; blocked | `destructive` | BootForge | Direct build route conflicts with preview-first lifecycle. |
| `GET /usb/build/{build_id}/status` | `server/openapi.yaml` | Documented build status. | `GET /operations/{operation_id}` | Reference only | `read-only` | Phoenix Agent | Build status schema is not Agent operation state. |
| `POST /usb/build/{build_id}/cancel` | `server/openapi.yaml` | Documented build cancel. | Future cancel operation extension | Reference only | `privileged` | Phoenix Agent | Cancel semantics need idempotency and audit. |
| `GET /ws/build/{build_id}` | `server/openapi.yaml` | Documented WebSocket build progress. | Future operation event stream | Reference only | `read-only` | Phoenix Agent | Agent event stream is not designed yet. |

## Website Flask Surface

| Current path | Current file | Current purpose | Future contract target | Migration status | Safety | Owner | Risks before migration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET /` | `website/web_server.py` | Website home/download page. | Phoenix Web | Keep outside Agent | `read-only` | Web | Not a local Agent surface. |
| `GET /download/<platform>-<arch>` | `website/web_server.py` | Platform download endpoint. | Phoenix Web downloads | Keep outside Agent | `read-only` | Web | Download integrity must stay signed/checksummed. |
| `GET /download/linux` | `website/web_server.py` | Linux download endpoint. | Phoenix Web downloads | Keep outside Agent | `read-only` | Web | Download versioning unclear. |
| `GET /download/linux-auto` | `website/web_server.py` | Auto Linux download endpoint. | Phoenix Web downloads | Keep outside Agent | `read-only` | Web | Auto selection rules need product ownership. |
| `GET /download/usb-package` | `website/web_server.py` | USB package download. | Phoenix Web downloads; BootForge package reference | Keep outside Agent | `read-only` | Web | Package signing and checksum policy needed. |
| `GET /cli-demo` | `website/web_server.py` | CLI demo page. | Phoenix Web demo | Keep outside Agent | `read-only` | Web | Demo should not imply production CLI contract. |
| `GET /checksum/<filename>` | `website/web_server.py` | Return checksum metadata. | Phoenix Web downloads; `media.verify_image` concept | Harvest concept | `read-only` | Web | Must use signed manifests later. |
| `GET /verify/<filename>` | `website/web_server.py` | Verify file metadata/checksum. | Phoenix Web downloads; `media.verify_image` concept | Harvest concept | `read-only` | Web | Verification semantics need hash/source trust model. |
| `GET /health` | `website/web_server.py` | Website health. | Phoenix Web health | Keep outside Agent | `read-only` | Web | Duplicate with API health names. |
| `GET /api` | `website/web_server.py` | Website API metadata. | Phoenix Web docs | Keep outside Agent | `read-only` | Web | Not Phoenix Agent API root. |
| `GET /api/health` | `website/web_server.py` | Website API health. | Phoenix Web health | Keep outside Agent | `read-only` | Web | Do not confuse with Agent `GET /health`. |
| `GET /api/recipes` | `website/web_server.py` | Recipe metadata for website/demo. | BootForge catalog reference | Harvest concept | `read-only` | Web | Recipe schema may duplicate BootForge recipes. |
| `GET /api/usb-toolkit` | `website/web_server.py` | USB toolkit metadata for website/demo. | BootForge catalog reference | Harvest concept | `read-only` | Web | Should not become execution API. |
| `GET /download/bootable-usb` | `website/web_server.py` | Bootable USB download. | Phoenix Web downloads | Keep outside Agent | `read-only` | Web | Package signing required later. |
| `GET /install` | `website/web_server.py` | Installation page. | Phoenix Web docs | Keep outside Agent | `read-only` | Web | Documentation only. |
| `GET /install/linux` | `website/web_server.py` | Linux install page. | Phoenix Web docs | Keep outside Agent | `read-only` | Web | Documentation only. |
| `GET /install/macos` | `website/web_server.py` | macOS install page. | Phoenix Web docs | Keep outside Agent | `read-only` | Web | Documentation only. |
| `GET /install/windows` | `website/web_server.py` | Windows install page. | Phoenix Web docs | Keep outside Agent | `read-only` | Web | Documentation only. |

## Mobile Prototype API Route Modules

| Current path | Current file | Current purpose | Future contract target | Migration status | Safety | Owner | Risks before migration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `POST /api/devices/register` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Register remote managed device. | Future fleet/service contract, not PR7 Agent core | Defer | `privileged` | Mobile | Remote management identity and trust model missing. |
| `GET /api/devices/registered` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | List registered remote devices. | Future fleet/service contract | Defer | `read-only` | Mobile | Local storage only; no auth model. |
| `GET /api/devices/{device_id}` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Get registered remote device. | Future fleet/service contract | Defer | `read-only` | Mobile | Conflicts with local storage device path. |
| `POST /api/devices/{device_id}/unregister` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Remove remote managed device. | Future fleet/service contract | Defer | `privileged` | Mobile | Device ownership and audit model missing. |
| `POST /api/devices/{device_id}/status` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Update remote device status. | Future fleet/service contract | Defer | `privileged` | Mobile | Status spoofing risk without auth. |
| `POST /api/groups/create` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Create device group. | Future fleet/service contract | Defer | `privileged` | Mobile | Fleet grouping is outside local Agent PR7 scope. |
| `GET /api/groups` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | List groups. | Future fleet/service contract | Defer | `read-only` | Mobile | No canonical fleet model. |
| `GET /api/groups/{group_id}` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Get group. | Future fleet/service contract | Defer | `read-only` | Mobile | No canonical fleet model. |
| `POST /api/groups/{group_id}/add-device` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Add device to group. | Future fleet/service contract | Defer | `privileged` | Mobile | Authorization missing. |
| `POST /api/groups/{group_id}/remove-device` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Remove device from group. | Future fleet/service contract | Defer | `privileged` | Mobile | Authorization missing. |
| `POST /api/bulk-operation` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Start bulk remote operation. | Future operations contract after Agent safety model expands | Block | `destructive` | Phoenix Agent | Includes reboot/shutdown and must never bypass policy gates. |
| `GET /api/bulk-operation/{operation_id}` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Read bulk operation status. | Future operation status | Defer | `read-only` | Phoenix Agent | Operation identity model differs from PR7 Agent. |
| `GET /api/dashboard/summary` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Fleet dashboard summary. | Future fleet/service contract | Defer | `read-only` | Mobile | Not Phoenix Agent local system summary. |
| `POST /api/devices/{device_id}/remote-command` | `phoenix-core-mobile/lib/api/multi_device_routes.py` | Send remote command to managed device. | Future privileged operation contract only | Block | `destructive` | Phoenix Agent | Remote command execution is high-risk and lacks trust boundaries. |
| `GET /api/recipes` | `phoenix-core-mobile/lib/api/usb_creation_routes.py` | USB creation recipe list. | Operation catalog; `POST /operations/preview` | Harvest | `read-only` | BootForge | Duplicate recipe model. |
| `GET /api/recipes/{recipe_id}` | `phoenix-core-mobile/lib/api/usb_creation_routes.py` | USB creation recipe detail. | Operation catalog; `POST /operations/preview` | Harvest | `read-only` | BootForge | Duplicate recipe model. |
| `POST /api/safety-check` | `phoenix-core-mobile/lib/api/usb_creation_routes.py` | USB safety validation. | `POST /safety/evaluate` | Harvest | `preview` | Phoenix Agent | Gate model must be normalized. |
| `POST /api/build/start` | `phoenix-core-mobile/lib/api/usb_creation_routes.py` | Start USB build. | `POST /operations/execute` placeholder only | Block until Agent safety exists | `destructive` | BootForge | Must not execute from mobile prototype route. |
| `GET /api/build/{job_id}/progress` | `phoenix-core-mobile/lib/api/usb_creation_routes.py` | Build progress. | `GET /operations/{operation_id}` | Harvest | `read-only` | Phoenix Agent | Job model duplicate. |
| `POST /api/build/{job_id}/cancel` | `phoenix-core-mobile/lib/api/usb_creation_routes.py` | Cancel build. | Future cancel operation extension | Defer | `privileged` | Phoenix Agent | Cancel policy missing. |
| `GET /api/build/jobs` | `phoenix-core-mobile/lib/api/usb_creation_routes.py` | List jobs. | Future operation list | Defer | `read-only` | Phoenix Agent | Operation list not in PR7 core contract. |
| `GET /api/build/{job_id}` | `phoenix-core-mobile/lib/api/usb_creation_routes.py` | Build detail. | `GET /operations/{operation_id}` | Harvest | `read-only` | Phoenix Agent | Duplicate job model. |

## TypeScript Client Surfaces

| Client surface | Expected paths | Future target | Migration status | Risks before migration |
| --- | --- | --- | --- | --- |
| `services/api.ts` | `GET /`, `GET /api/health`, `GET /api/devices`, `POST /api/devices/refresh`, `GET /api/hardware`, `GET /api/system/*`, `GET /api/recipes`, `POST /api/safety-check`, `POST /api/build/start`, `GET /api/oclp/*`, `GET /api/images`, `GET /api/workflows`, `POST /api/workflows/run`, `GET /api/diagnostics` | Replace or wrap with `services/phoenix-agent/sdk/typescript/phoenix-agent-client.ts` | Transitional SDK candidate | Calls direct build/workflow endpoints that must become preview/execute lifecycle calls. |
| `mobile/src/services/api.ts` | Same route family as `services/api.ts` | Phoenix Mobile should use typed Agent SDK or a remote-safe bridge | Transitional SDK candidate | Mobile must not directly format, image, partition, flash, or mutate boot/system state. |
| `phoenix-core-mobile/lib/api.ts` | `GET /health`, `GET /api/health`, `GET /api/recipes`, `GET /api/usb-toolkit` | Phoenix Web/Mobile reference only unless manually migrated | Archive or feature harvest | Mismatched base paths and lightweight demo semantics. |
| `phoenix-core-mobile/lib/api/phoenix-enterprise-client.ts` | `GET /health`, `GET /status`, `GET /storage/devices*`, `POST /storage/devices/{id}/mount`, `POST /storage/devices/{id}/unmount`, `POST /storage/devices/{id}/erase`, `GET /system/*`, `GET /hardware`, `GET /recipes`, `POST /safety-check`, `POST /build/start`, `GET /build/*`, `WS /api/ws` | Harvest read models; destructive methods must map to Agent preview and safety gates before any execution | Feature harvest candidate | Mount, unmount, erase, and WebSocket operation models are outside PR7 Agent contract and high-risk. |

## Contract Consequences

- UI apps may request operations only.
- Phoenix Agent owns policy and authorization checks.
- Rust crates own low-level safety logic.
- Destructive operations must require preview first.
- System disks are protected by default.
- Device identity must be explicit before action.
- No UI app may directly format, image, partition, flash, install drivers, patch boot state, or modify system state.
