# Phoenix Platform Migration Roadmap

## Purpose

PR 3 establishes the canonical Phoenix Platform map without relocating active source.

This roadmap exists so later PRs can migrate source deliberately instead of creating another set of duplicate apps, services, and recovery tools.

## Canonical Targets

| Future target | Role |
| --- | --- |
| `apps/phoenix-control-center/` | Main Phoenix OS desktop shell: Tauri, React, TypeScript, Tailwind, Rust commands, Phoenix Agent bridge. |
| `apps/phoenix-welcome/` | First-run onboarding for Phoenix OS daily-driver setup. |
| `apps/bootforge/` | Deployment, imaging, USB creation, diagnostics, BootCamp, OCLP, and repair workflows. |
| `apps/phoenix-key/` | Rescue and provisioning mode integrated with Phoenix OS and BootForge. |
| `apps/mobile/` | Canonical Expo React Native companion app. |
| `apps/web/` | Future Next.js public web, docs, downloads, and support surfaces. |
| `services/phoenix-agent/` | Local backend bridge and system service. Rust-first, FastAPI transitional. |
| `crates/` | Rust system layer, safety gates, imaging primitives, workflow engine, reports, and host adapters. |
| `os/phoenix-os/` | Debian/Ubuntu KDE Plasma OS image, installer, branding, package lists, and build scripts. |
| `scripts/` | Repo-level automation only. OS build scripts move under `os/phoenix-os/scripts/` later. |
| `tests/` | Cross-cutting tests for apps, services, crates, workflows, and OS validation. |
| `archive/` | Reviewed historical material that should be preserved outside active source paths. |

## Current Systems

| Current system | Current path | Future target | PR 3 status |
| --- | --- | --- | --- |
| Root Expo app | `app/`, `App.tsx`, `index.tsx`, root package files | `apps/phoenix-control-center/` or `apps/mobile/` after product split | Not migrated |
| Secondary mobile app | `mobile/` | `apps/mobile/` | Not migrated |
| Duplicate mobile app | `phoenix-core-mobile/` | `apps/mobile/` or `archive/legacy-mobile/` after comparison | Not migrated |
| Active BootForge desktop app | `desktop/` | `apps/bootforge/` | Not migrated |
| BootForge reference USB source | `legacy/bootable_usb/BootForge/` | `apps/bootforge/` or `archive/legacy-builds/` after comparison | Not migrated |
| Rust CLI | `apps/cli/` | Keep under `apps/cli/` until ownership is decided | Not migrated |
| Rust crates | `crates/` | Already near canonical location | Not migrated |
| FastAPI backend | `backend/` | `services/phoenix-agent/` | Not migrated |
| Python and TypeScript server stack | `server/`, `server/_core/` | `services/phoenix-agent/` or app-specific APIs | Not migrated |
| Existing API client bridge | `services/api.ts` | `services/phoenix-agent/` client or generated SDK | Not migrated |
| Vite recovery GUI | `website/recovery-gui/` | `apps/web/` or archive after product decision | Not migrated |
| Website server | `website/web_server.py` | `apps/web/` or `services/phoenix-agent/` after ownership decision | Not migrated |
| Standalone dashboard | `usb_creation_dashboard.html` | `apps/web/`, `apps/bootforge/`, or archive | Not migrated |
| Phoenix Key concept docs | `docs/phoenix_key_legendary_blueprint.md` | `apps/phoenix-key/` planning input | Not migrated |
| Legacy scripts and build experiments | `legacy/`, `legacy/build_system/`, `legacy/scripts/` | `archive/`, `scripts/`, or `os/phoenix-os/scripts/` after review | Not migrated |

## Migration Order

1. Keep PR 3 scaffold-only and land the map.
2. Add ownership labels and module boundaries for every current app, service, crate, and legacy subsystem.
3. Compare root Expo, `mobile/`, and `phoenix-core-mobile/`; choose the canonical mobile/control-center split.
4. Define the Phoenix Agent API contract before moving backend implementations.
5. Stabilize Rust workspace contracts for `core`, `safety`, `imaging`, `workflow-engine`, `report`, and host crates.
6. Move BootForge source in a small PR after comparing `desktop/` with `legacy/bootable_usb/BootForge/`.
7. Create Phoenix Control Center Tauri shell after the Agent and Rust command boundaries are explicit.
8. Add Phoenix Welcome as a thin first-run app once OS package and installer assumptions are documented.
9. Start `os/phoenix-os/` package lists and live-build configuration after the daily-driver app stack is named.
10. Archive legacy systems only after unique source and docs have been extracted.

## Risk Areas

- Duplicate app stacks can hide feature loss if moved in bulk.
- Backend duplication can create two incompatible API contracts.
- BootForge and OCLP workflows contain valuable repair logic that must not be discarded as legacy noise.
- Generated mobile/native payloads must not return to Git.
- Stale root docs and workflows still point to missing or old entrypoints.
- Rust crate contracts still need repair before they can be treated as stable platform APIs.
- CI currently masks failures in places and should not be trusted as proof of correctness.
- Phoenix OS direction can drift toward recovery-only, generic gaming distro, or enterprise dashboard unless the manifesto remains the source of truth.

## Systems Not Yet Migrated

PR 3 does not migrate:

- Root Expo app source.
- `mobile/` or `phoenix-core-mobile/`.
- `desktop/` BootForge source.
- `legacy/bootable_usb/BootForge/`.
- `backend/`, `server/`, or `services/api.ts`.
- `website/` or `usb_creation_dashboard.html`.
- Rust crates.
- OS build scripts, package lists, installer config, or branding assets.

## PR 4 Recommendation

PR 4 should be a source ownership and boundary PR.

Recommended scope:

- Add `OWNERSHIP.md` or focused subsystem READMEs for active current paths.
- Label each current system as active, transitional, reference, archive candidate, or generated-forbidden.
- Document the exact migration decision for root Expo vs `mobile/` vs `phoenix-core-mobile/`.
- Document the Phoenix Agent API surface before moving backend code.
- Avoid moving implementation files until tests and ownership labels are in place.
