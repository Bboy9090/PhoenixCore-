# Active Systems Ownership

This document labels current systems in place. Migration status in PR4 is "not moved" for every system.

## 1. Root Expo App

- Current purpose: primary React Native/Expo application surface with builder, wizard, dashboard, knowledge, admin, OAuth, and USB-oriented routes.
- Current entrypoint: `index.tsx`, `App.tsx`, `app/_layout.tsx`, routes under `app/`, root `package.json`.
- Future target: split decision between `apps/phoenix-control-center/` and `apps/mobile/`.
- Migration status: active, not moved.
- Preserve: route behavior, API assumptions, app config, NativeWind/Tailwind styling setup, admin and OAuth flows.
- Archive: duplicate or stale screens only after comparison with `mobile/` and `phoenix-core-mobile/`.
- Must not duplicate: a fourth mobile/control-center app tree.
- Known risks: current root app may mix desktop-control-center and mobile-companion concepts.
- Required tests before movement: `pnpm test`, `pnpm build`, route smoke tests, API client contract checks.
- Dependencies: Expo, React Native, NativeWind/Tailwind, root package locks and app config.
- Owner role: unresolved between Control Center and Mobile.

## 2. `mobile/`

- Current purpose: secondary mobile app with dashboard, build, devices, settings, API client, and theme utilities.
- Current entrypoint: `mobile/index.tsx`, `mobile/src/App.tsx`, `mobile/package.json`.
- Future target: `apps/mobile/`.
- Migration status: active/reference, not moved.
- Preserve: screens, API client behavior, theme utilities, package manifest.
- Archive: duplicate screens after canonical mobile app selection.
- Must not duplicate: another mobile API client if root Expo already owns it.
- Known risks: overlaps with root Expo app and `phoenix-core-mobile/`.
- Required tests before movement: mobile app install/build smoke test and API client tests.
- Dependencies: Expo/React Native package set in `mobile/package.json`.
- Owner role: Mobile.

## 3. `phoenix-core-mobile/`

- Current purpose: duplicate or experimental Expo app with tabs for builder, devices, knowledge, monitor, USB create, wizard, OAuth, and API clients.
- Current entrypoint: `phoenix-core-mobile/app/_layout.tsx`, `phoenix-core-mobile/app/(tabs)/index.tsx`, `phoenix-core-mobile/package.json`.
- Future target: `apps/mobile/` or `archive/legacy-mobile/` after comparison.
- Migration status: active/reference, not moved.
- Preserve: unique screens, API clients, enterprise client concepts, USB route ideas, config.
- Archive: superseded route copies and generated/native payload assumptions.
- Must not duplicate: generated Android/iOS folders or a separate Phoenix mobile namespace.
- Known risks: duplicated app stack and generated native artifact drift.
- Required tests before movement: route comparison, API client comparison, Expo build smoke test.
- Dependencies: Expo app config, package lock, local API client modules.
- Owner role: Mobile with possible Archive outcome.

## 4. `desktop/`

- Current purpose: active BootForge desktop/PyQt, CLI, imaging, recovery, OCLP, provider, diagnostics, plugin, and safety workflow source.
- Current entrypoint: `desktop/main.py`, `desktop/src/cli/cli_interface.py`, `desktop/src/cli/recovery_cli.py`, `desktop/pyproject.toml`.
- Future target: `apps/bootforge/`, with shared operations moving behind Phoenix Agent and Core Crates later.
- Migration status: active, not moved.
- Preserve: PyQt workflows, USB builder, disk manager, imaging, recovery, OCLP, BootCamp/driver-adjacent logic, safety validator, plugins, provider logic.
- Archive: old installer/build wrappers only after confirming replacement source exists.
- Must not duplicate: disk, bootloader, imaging, or OCLP execution paths outside Phoenix Agent/safety gates.
- Known risks: UI and destructive operations are currently close together.
- Required tests before movement: `PYTHONPATH=desktop:desktop/src python -m pytest tests/`, workflow fixtures, disk-operation dry-run tests.
- Dependencies: PyQt, Python requirements, OS tools, OCLP references, platform-specific disk utilities.
- Owner role: BootForge, with Phoenix Key and Phoenix Agent integration.

## 5. `backend/`

- Current purpose: FastAPI-style backend for hardware, USB, OCLP, monitoring, schemas, and device services.
- Current entrypoint: `backend/main.py`.
- Future target: `services/phoenix-agent/`.
- Migration status: active/transitional, not moved.
- Preserve: hardware profiler, device scanner, OCLP integration, USB builder, schemas, monitoring concepts.
- Archive: duplicate routes only after Phoenix Agent contract exists.
- Must not duplicate: server routes that conflict with `server/` without a contract decision.
- Known risks: overlaps with `server/` and may expose privileged operations without final safety boundary.
- Required tests before movement: FastAPI route smoke tests, schema compatibility tests, hardware/USB mock tests.
- Dependencies: Python requirements, FastAPI stack, hardware and USB libraries.
- Owner role: Phoenix Agent.

## 6. `server/`

- Current purpose: mixed Python and TypeScript server stack with API routes, BootCamp services, admin, notifications, monitoring, OpenAPI, and `_core` helpers.
- Current entrypoint: `server/main.py`, `server/api_fastapi.py`, `server/_core/index.ts`, `server/routers.ts`.
- Future target: `services/phoenix-agent/` for local system APIs; Web or Control Center only for app-facing clients.
- Migration status: active/transitional, not moved.
- Preserve: BootCamp driver tooling, API schemas, OpenAPI, admin auth concepts, notification and monitoring integrations.
- Archive: stale or duplicate web/server wrappers after route ownership is resolved.
- Must not duplicate: Phoenix Agent API surface or BootCamp workflow engines.
- Known risks: language and framework split can create incompatible API contracts.
- Required tests before movement: Python API tests, TypeScript route checks, OpenAPI diff, BootCamp route fixtures.
- Dependencies: Python requirements, TypeScript server helpers, OpenAPI schema, driver database.
- Owner role: Phoenix Agent, with BootForge ownership for BootCamp workflows.

## 7. `website/`

- Current purpose: recovery GUI, web server, Vercel marker, and web experiment docs.
- Current entrypoint: `website/recovery-gui/src/main.tsx`, `website/recovery-gui/package.json`, `website/web_server.py`.
- Future target: `apps/web/` or Archive after product decision.
- Migration status: active/reference, not moved.
- Preserve: unique recovery GUI UX, hero/assets, package config, web server ideas.
- Archive: recovery-only public web positioning if it conflicts with Phoenix OS daily-driver doctrine.
- Must not duplicate: Control Center UI or Phoenix Agent APIs.
- Known risks: can reinforce recovery-only product drift.
- Required tests before movement: web build, route smoke tests, asset checks.
- Dependencies: Vite/React stack, Python web server.
- Owner role: Web with possible Archive outcome.

## 8. `legacy/`

- Current purpose: historical source, integration experiments, BootForge USB reference source, old installers, build scripts, bootable USB material, BootCamp notes, and mobile integration copies.
- Current entrypoint: varies; notable entries include `legacy/bootable_usb/BootForge/main.py`, `legacy/create_recovery_usb.py`, and `legacy/build_system/build_all.py`.
- Future target: Archive by default, with selected BootForge, Phoenix Key, Mobile, Phoenix OS, or Phoenix Agent extraction.
- Migration status: reference, not moved.
- Preserve: unique BootForge workflows, OCLP logic, installer scripts, recovery scripts, Phoenix Key clues, build-system lessons.
- Archive: duplicate integration copies and obsolete installers after extraction.
- Must not duplicate: old source into active apps without ownership.
- Known risks: valuable source and obsolete generated material are mixed.
- Required tests before movement: file comparison against active `desktop/`, extraction notes, no-source-loss review.
- Dependencies: Python scripts, shell/batch scripts, PyInstaller specs, BootForge assets.
- Owner role: Archive, with extraction by BootForge, Phoenix Key, Mobile, Phoenix OS, or Phoenix Agent.

## 9. `crates/`

- Current purpose: Rust system layer for core orchestration, safety, imaging, workflow engine, reports, host adapters, bootloader, WIM, content, plugin SDK, and legacy patcher concepts.
- Current entrypoint: root `Cargo.toml`, crate `Cargo.toml` files, `crates/*/src/lib.rs`.
- Future target: `crates/` remains canonical.
- Migration status: active, not moved.
- Preserve: safety gates, imaging primitives, device/host abstractions, workflow engine concepts, report bundle work.
- Archive: obsolete crates only after API replacement and test coverage exist.
- Must not duplicate: Rust safety logic in UI apps or ad hoc Python wrappers.
- Known risks: cross-crate contract drift.
- Required tests before movement: `cargo build --workspace`, `cargo test --workspace`, crate contract tests.
- Dependencies: Rust workspace, platform host APIs, report/imaging dependencies.
- Owner role: Core Crates.

## 10. `apps/cli`

- Current purpose: Rust CLI entrypoint for invoking Phoenix/BootForge/core workflows.
- Current entrypoint: `apps/cli/src/main.rs`, `apps/cli/Cargo.toml`.
- Future target: remains under `apps/cli/` until CLI product ownership is decided.
- Migration status: active, not moved.
- Preserve: CLI command semantics and Rust integration points.
- Archive: none until replacement CLI exists.
- Must not duplicate: a second CLI in scripts or desktop wrappers without ownership.
- Known risks: may depend on unstable crate contracts.
- Required tests before movement: CLI build, command smoke tests, workspace tests.
- Dependencies: Rust workspace crates.
- Owner role: BootForge and Core Crates.

## 11. BootCamp

- Current purpose: BootCamp driver detection, installation, USB management, and recovery support.
- Current entrypoint: `server/bootcamp/api.py`, `server/routers/bootcamp.py`, `legacy/bootcamp/README.md`.
- Future target: BootForge workflows exposed through Phoenix Agent.
- Migration status: active/reference, not moved.
- Preserve: driver database, Mac detection, installer service, recovery logic, progress websocket.
- Archive: old docs only after current workflow ownership is documented.
- Must not duplicate: driver database or install state machines across apps.
- Known risks: driver installation can become destructive or host-specific.
- Required tests before movement: driver database validation, mocked install flow, API route tests.
- Dependencies: BootCamp driver database, server routes, platform detection.
- Owner role: BootForge with Phoenix Agent execution boundary.

## 12. `bootable_usb/`

- Current purpose: top-level Phoenix/BootForge/Phoenix Key branding assets and bootable USB material.
- Current entrypoint: no executable entrypoint found at top level; related source entrypoint exists at `legacy/bootable_usb/BootForge/main.py`.
- Future target: `apps/bootforge/`, `apps/phoenix-key/`, and `os/phoenix-os/branding/` after ownership split.
- Migration status: reference/assets, not moved.
- Preserve: Phoenix-era marks, Phoenix Key tokens, wordmarks, and boot media clues.
- Archive: stale or duplicate USB payloads after brand/source extraction.
- Must not duplicate: Phoenix Key branding or BootForge media layout in multiple active locations.
- Known risks: assets can drift from canonical Phoenix OS branding.
- Required tests before movement: asset inventory, brand token comparison, boot media manifest review.
- Dependencies: SVG/CSS/JSON brand assets.
- Owner role: BootForge, Phoenix Key, and Phoenix OS.

## 13. `legacy/usb_toolkit/`

- Current purpose: historical USB toolkit launchers, sync config, rebuild tool, and packaged executable payload.
- Current entrypoint: `legacy/usb_toolkit/Launch-BootForge-*.sh/.bat/.command`, `legacy/usb_toolkit/tools/rebuild_usb.py`.
- Future target: Archive by default; extract unique BootForge media logic if needed.
- Migration status: reference/risk, not moved.
- Preserve: launcher scripts, sync layout ideas, rebuild script if unique.
- Archive: packaged executable output and stale toolkit packaging after review.
- Must not duplicate: old executable payloads or generated toolkit output.
- Known risks: `legacy/usb_toolkit/executables/BootForge` is a tracked packaged binary-style payload and should be reviewed in a cleanup PR, not executed blindly.
- Required tests before movement: compare with active BootForge launch/build paths, checksum any retained binary, dry-run rebuild script.
- Dependencies: shell/batch launchers, local executable payload, sync config.
- Owner role: Archive with possible BootForge extraction.

## 14. `third_party/OpenCore-Legacy-Patcher`

- Current purpose: external OCLP reference/integration point.
- Current entrypoint: no repo-owned app entrypoint; integration code uses `desktop/src/oclp_launcher.py`, `desktop/src/core/oclp_*`, and `desktop/src/gui/oclp_wizard.py`.
- Future target: remain an external third-party reference with BootForge integration mediated by Phoenix Agent and safety gates.
- Migration status: reference, not moved.
- Preserve: upstream provenance, version/pin metadata, integration assumptions, safety controller behavior.
- Archive: never archive upstream dependency casually; replace only with explicit vendor policy.
- Must not duplicate: patched third-party source without a vendor/update policy.
- Known risks: upstream drift, licensing, patch safety, platform-specific behavior.
- Required tests before movement: OCLP pipeline tests, launcher dry-run, safety controller tests, upstream version audit.
- Dependencies: OCLP upstream, desktop OCLP integration modules.
- Owner role: BootForge with Core Crates safety support.
