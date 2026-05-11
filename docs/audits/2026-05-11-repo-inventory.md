# PhoenixCore Repo Inventory - 2026-05-11

## Audit Target

- Repository: `Bboy9090/PhoenixCore-`
- Branch: `main`
- Commit: `9fc1758a702b459d8d9b89175ccea1ed521ed1d2`
- Commit date: `2026-05-11T19:09:31Z`
- PR 1 scope: documentation-only audit and classification. No source moves, no file deletion, no generated cleanup, and no formatting rewrites.

## Repo Scale Snapshot

| Measure | Value |
| --- | ---: |
| Git tree entries | 53,774 |
| Blob entries | 47,070 |
| GitHub repository size | about 546 MB |
| Artifact candidate entries | 46,352 |
| Exact duplicate content groups, excluding `node_modules`, `legacy/build`, and `legacy/dist` | 91 |

Largest top-level areas by entry count and blob size:

| Path | Entries | Blob size |
| --- | ---: | ---: |
| `mobile/` | 52,722 | 413.32 MB |
| `legacy/` | 273 | 349.87 MB |
| `phoenix-core-mobile/` | 136 | 0.77 MB |
| `desktop/` | 113 | 1.73 MB |
| `server/` | 80 | 0.55 MB |
| `crates/` | 67 | 0.19 MB |
| `docs/` | 47 | 0.08 MB |
| `assets/` | 31 | 6.04 MB |
| `app/` | 27 | 0.23 MB |
| `website/` | 27 | 0.23 MB |

## Active Source Classification

### Rust Core And CLI

Active or near-active Rust source lives in:

- `Cargo.toml`
- `apps/cli/`
- `crates/core/`
- `crates/safety/`
- `crates/imaging/`
- `crates/host-windows/`
- `crates/host-linux/`
- `crates/host-macos/`
- `crates/report/`
- `crates/workflow-engine/`
- `crates/content/`
- `crates/fs-fat32/`
- `crates/wim/`
- `crates/bootloader-core/`
- `crates/legacy-patcher/`
- `crates/plugin-sdk/`

Current root workspace membership only includes:

- `crates/core`
- `crates/host-windows`
- `crates/imaging`
- `crates/safety`
- `apps/cli`

Several Rust crates are present but not part of the root workspace. This matters because `ci-windows.yml` runs `cargo build --workspace`, while `ci.yml` and `deploy.yml` attempt to build packages that are not declared as workspace members.

### BootForge Desktop Python

The strongest host-side recovery and deployment app is under `desktop/`:

- `desktop/main.py`
- `desktop/src/cli/`
- `desktop/src/core/`
- `desktop/src/gui/`
- `desktop/src/imaging/`
- `desktop/src/installers/`
- `desktop/src/network/proto/`
- `desktop/src/plugins/`
- `desktop/src/recovery/`
- `desktop/src/utils/`

This area contains the PyQt GUI, CLI, OCLP integration, disk manager, OS image manager, patch pipeline, safety validator, USB builder, provider model, report/doc builder, and recovery helpers. It should be preserved and migrated deliberately, not erased.

### Python Backends And Services

There are two competing backend families:

- `backend/`: FastAPI service around USB device discovery, hardware profiling, OCLP compatibility, system metrics, and USB builds.
- `server/`: mixed Python FastAPI/Flask-style service files plus TypeScript `server/_core/` Express/TRPC runtime.

The future Phoenix Agent should consolidate these into one service boundary instead of keeping multiple API stacks active.

### Root Expo / React Native App

The root app stack includes:

- `package.json`
- `app.config.ts`
- `app/`
- `components/`
- `hooks/`
- `lib/`
- `constants/`
- `server/_core/`
- `__tests__/`
- `tests/*.test.ts`

This is the richest current React/TypeScript app surface. It includes Expo Router routes, USB builder flows, device wizard flows, knowledge base, admin routes, OAuth callback handling, persistence tests, catalog tests, and API hooks.

### Mobile Copies

There are two additional mobile app copies:

- `mobile/`: React Native / Expo app plus checked-in `node_modules`.
- `phoenix-core-mobile/`: generated Expo project with Android and iOS native folders.

These should be treated as duplicate systems until a canonical app stack is chosen and migrated.

### Website / Demo UI

Website and web demo surfaces:

- `website/web_server.py`: Flask BootForge download/demo server.
- `website/recovery-gui/`: Vite React demo app.
- `usb_creation_dashboard.html`: standalone dashboard artifact or prototype.

These are useful as product-reference material, but they should not remain scattered as independent production entrypoints.

### Tests

Current tests include:

- Python: `tests/test_core.py`, `tests/test_critical_fixes.py`, `tests/test_hardware_detection.py`, `tests/test_oclp_pipeline.py`, `tests/test_win_patch_engine.py`, and related files.
- TypeScript/Vitest: `__tests__/catalog.test.ts`, `__tests__/hooks.test.ts`, `__tests__/persistence.test.ts`, `tests/e2e-integration.test.ts`, `tests/integration.test.ts`, `tests/auth.logout.test.ts`.

Several Python tests import a root `src/` package that is not present in the current tree. They likely need `desktop/src` path fixes or package migration.

### Assets And Brand

Current useful assets:

- `assets/brand/phoenix-forge/`
- `assets/logo/`
- `assets/icons/`
- `assets/images/`
- `docs/phoenix_brand/`
- `docs/phoenix_key_legendary_blueprint.md`

Generated image duplicates also exist in `attached_assets/generated_images/` and `legacy/bootable_usb/BootForge/assets/icons/`.

## Duplicate Systems

### App Stack Duplication

| System | Current paths | Classification |
| --- | --- | --- |
| Root Expo app | `app/`, `components/`, `hooks/`, `lib/`, `server/_core/`, `package.json` | Candidate canonical planning input for Phoenix Control Center and mobile/web |
| Older mobile app | `mobile/`, `screens/`, `services/`, `utils/` | Duplicate, includes generated dependency tree |
| Generated native mobile app | `phoenix-core-mobile/` | Duplicate/generated native project, useful as reference |

Exact duplicate examples:

- `mobile/src/services/api.ts`, `services/api.ts`, and legacy `api.ts`
- `mobile/src/screens/BuildScreen.tsx`, `screens/BuildScreen.tsx`, and legacy `BuildScreen.tsx`
- `mobile/src/screens/DashboardScreen.tsx`, `screens/DashboardScreen.tsx`, and legacy `DashboardScreen.tsx`
- `mobile/src/screens/DevicesScreen.tsx`, `screens/DevicesScreen.tsx`, and legacy `DevicesScreen.tsx`
- `mobile/src/screens/SettingsScreen.tsx`, `screens/SettingsScreen.tsx`, and legacy `SettingsScreen.tsx`
- `mobile/src/utils/theme.ts`, `utils/theme.ts`, and legacy `theme.ts`

### Backend Duplication

| System | Current paths | Classification |
| --- | --- | --- |
| FastAPI hardware/USB backend | `backend/main.py`, `backend/core/`, `backend/models/` | Candidate Phoenix Agent input |
| Industrial Python backend | `server/main.py`, `server/api_fastapi.py`, `server/api.py`, `server/bootcamp/`, `server/admin/` | Candidate Phoenix Agent input |
| TypeScript local API bridge | `server/_core/`, `server/routers.ts`, `server/storage.ts`, `server/db.ts` | App-support runtime, not OS agent yet |
| Flask web demo | `website/web_server.py` | Product/demo reference, not canonical backend |

### BootForge Duplication

`desktop/` and `legacy/bootable_usb/BootForge/` contain many exact or near-exact duplicates. Examples include:

- `desktop/src/gui/modern_theme.py`
- `desktop/src/gui/os_image_manager_qt.py`
- `desktop/src/gui/log_viewer.py`
- `desktop/src/gui/status_widget.py`
- `desktop/src/gui/stepper_header.py`
- `desktop/src/gui/os_image_widget.py`
- `desktop/src/gui/oclp_wizard.py`
- `desktop/src/gui/usb_recipe_manager.py`
- `desktop/src/core/real_time_monitor.py`
- `desktop/src/core/safety_validator.py`
- `desktop/src/core/providers/linux_provider.py`
- `desktop/src/core/providers/windows_provider.py`
- `desktop/src/core/system_monitor.py`
- `desktop/src/core/vendor_database.py`

`desktop/` should be treated as the active source and `legacy/bootable_usb/BootForge/` as archive/reference unless a later diff proves otherwise.

### Asset Duplication

Exact duplicate asset examples:

- `assets/icons/hero_banner.png`
- `attached_assets/generated_images/BootForge_Hero_Banner_60f12ffc.png`
- `legacy/bootable_usb/BootForge/assets/icons/hero_banner.png`
- `assets/icons/BootForge_App_Icon_1685d1e8.png`
- `attached_assets/generated_images/BootForge_App_Icon_1685d1e8.png`
- `legacy/bootable_usb/BootForge/assets/icons/BootForge_App_Icon_1685d1e8.png`
- `assets/icons/Toolbar_Icons_Set_db533bcc.png`
- `attached_assets/generated_images/Toolbar_Icons_Set_db533bcc.png`
- `legacy/bootable_usb/BootForge/assets/icons/Toolbar_Icons_Set_db533bcc.png`

## Build Artifacts And Generated Files Tracked

These should not remain active source:

- `mobile/node_modules/`: dominates the repository and caused Windows checkout failures due long paths.
- `mobile/.expo/`: generated Expo metadata.
- `legacy/build/`: PyInstaller build output.
- `legacy/dist/`: release output, packaged executables, archives, and staged complete bundles.
- `legacy/usb_toolkit/executables/BootForge`: packaged binary.
- `phoenix-core-mobile.zip` and `phoenix-core-mobile7.zip`: duplicate archive files.
- `desktop/src/installers/dist/bootforge-standalone.py`: generated installer output.
- `desktop/tauri-app/src-tauri/src/drives/files.zip`: embedded/generated zip.
- `server/__pycache__/`, `server/**/__pycache__/`, and `.pyc` files.
- PyInstaller files such as `.toc`, `.pkg`, `.pyz`, and generated `xref-*.html`.
- Generated native app folders under `phoenix-core-mobile/android/` and `phoenix-core-mobile/ios/`, especially the checked-in `debug.keystore`.

Largest tracked file examples:

| Size | Path |
| ---: | --- |
| 64.67 MB | `legacy/usb_toolkit/executables/BootForge` |
| 64.67 MB | `legacy/dist/BootForge` |
| 64.67 MB | `legacy/dist/BootForge-USB-Toolkit/executables/BootForge` |
| 64.61 MB | `legacy/build/BootForge/BootForge.pkg` |
| 64.03 MB | `legacy/dist/BootForge-USB-Toolkit.zip` |
| 26.26 MB | `mobile/node_modules/react-native/sdks/hermesc/win64-bin/icudt64.dll` |
| 22.07 MB | `mobile/node_modules/jsc-android/dist/org/webkit/android-jsc-intl/r250231/android-jsc-intl-r250231.aar` |
| 8.69 MB | `mobile/node_modules/typescript/lib/typescript.js` |
| 1.81 MB | `phoenix-core-mobile.zip` |
| 1.81 MB | `phoenix-core-mobile7.zip` |

## Legacy Worth Preserving

Preserve, archive, and mine these for Phoenix OS and Phoenix Key:

- BootForge PyQt UX and wizard flow in `desktop/src/gui/`.
- BootForge CLI and recovery CLI in `desktop/src/cli/`.
- OCLP pipeline and safety controller in `desktop/src/core/`.
- Hardware profiles and vendor database in `desktop/src/core/`.
- Patch pipeline, provider model, and safety validator in `desktop/src/core/`.
- OS image manager, USB builder, and Win patch engine in `desktop/src/core/`.
- BootCamp and driver tooling in `server/bootcamp/` and `BOOTCAMP_*` docs.
- Rust crates for safety gates, device graph, imaging, reports, WIM, bootloader validation, host providers, and workflow definitions.
- Phoenix Key blueprint in `docs/phoenix_key_legendary_blueprint.md`.
- Brand assets in `assets/brand/`, `assets/logo/`, and `docs/phoenix_brand/`.

## Broken Or Outdated Docs

- `README.md` references root `main.py` and `src/`, but current active Python source appears under `desktop/`.
- `README.md` presents PhoenixCore as unified recovery/deployment, not Phoenix OS as an everyday OS plus recovery superpowers.
- `docs/VISION.md` and `docs/ROADMAP.md` explicitly scope the product as recovery-first/recovery-only V1. This conflicts with the Phoenix OS mission.
- `LEGACY.md` labels areas like `desktop/` and `assets/` as legacy, but those areas contain important active source and brand material.
- Heroku and deployment docs are likely stale relative to the current mixed FastAPI, Flask, Express, Expo, and Rust layout.
- `DESKTOP_CONSUMER_APP.md` and `MOBILE_ENTERPRISE_INTEGRATION.md` are useful product references, but they describe transitional app/backend architecture rather than the future Phoenix Platform architecture.

## Missing Dependencies And Config Issues

- Rust workspace membership is incomplete relative to existing crates and CI package names.
- Some Rust crates use incompatible contracts. For example, `host-linux`, `host-macos`, `report`, and `workflow-engine` reference `DeviceGraph` fields or types that do not match `crates/core/src/lib.rs`.
- Python tests import root `src` even though the present source root is `desktop/src`.
- Dockerfile copies `web_server.py`, `src/`, and `dist/` from the repository root, but these paths do not exist as root active files.
- `docker-compose.yml` configures PostgreSQL, while `drizzle.config.ts` is set to MySQL.
- Root package manager state is mixed: `package.json` declares `pnpm@9.12.0`, but both `package-lock.json` and `pnpm-lock.yaml` are tracked.
- `phoenix-core-mobile/` contains generated Android/iOS native folders and a debug keystore, but its role is not defined.

## Safety And Security Risks

- Tracked generated dependency trees and binaries make review difficult and create supply-chain ambiguity.
- `phoenix-core-mobile/android/app/debug.keystore` is checked in. Debug keys are common in generated apps but should not be treated as production credentials.
- `docker-compose.yml` includes development database credentials and `SECRET_KEY=dev-secret-key-change-in-production`.
- Several API services use broad CORS defaults such as `allow_origins=["*"]`.
- CI workflows use `|| true` around critical build/test operations, which can hide broken builds.
- Disk imaging, formatting, OCLP, BootCamp, and driver injection functionality is inherently high-risk and needs a single safety policy surface before productization.

## Best Current Architecture Pieces

Keep and elevate these into Phoenix Platform:

- Rust device graph model and host provider direction.
- Rust safety gates and confirmation-token pattern.
- Read-only imaging/hash primitives and report bundle generation.
- Workflow engine concept for auditable recovery/deployment flows.
- BootForge PyQt wizard experience and CLI commands.
- OCLP integration and macOS-specific safety workflows.
- BootCamp/driver detection and provisioning work.
- Phoenix Key blueprint and offline rescue/provisioning story.
- Brand assets and Phoenix Forge visual identity.

## PR 1 Archive Policy

PR 1 does not archive or delete anything. Later cleanup should follow this order:

1. Move useful old work into `archive/` with a manifest.
2. Remove only obvious generated junk after the inventory is reviewed.
3. Keep active source and product-reference docs until their replacements exist.
4. Do not erase recovery/BootForge/Phoenix Key work while pivoting toward daily-driver Phoenix OS.

## Audit Commands Used

```powershell
git clone --no-checkout https://github.com/Bboy9090/PhoenixCore-.git PhoenixCore-sparse
git sparse-checkout init --cone
git sparse-checkout set docs
git checkout main
git rev-parse HEAD

$r = Invoke-RestMethod -Uri 'https://api.github.com/repos/Bboy9090/PhoenixCore-/git/trees/main?recursive=1'
[pscustomobject]@{ truncated=$r.truncated; count=$r.tree.Count } | Format-List

$repo = Invoke-RestMethod -Uri 'https://api.github.com/repos/Bboy9090/PhoenixCore-'
[pscustomobject]@{
  full_name=$repo.full_name
  default_branch=$repo.default_branch
  size_kb=$repo.size
  pushed_at=$repo.pushed_at
  updated_at=$repo.updated_at
} | Format-List

$tree = git ls-tree -r -t --long HEAD
# Parsed type, sha, size, path, top-level directory, and extension from git ls-tree output.
# Grouped by top-level directory for counts and blob sizes.

$tree = git ls-tree -r --long HEAD
# Parsed blobs, selected files larger than 1 MB, and counted artifact candidates using generated-output path and extension patterns.

$tree = git ls-tree -r --long HEAD
# Grouped blobs by SHA to identify exact duplicate content groups, excluding node_modules, legacy/build, and legacy/dist.
```

## Checkout Note

A normal Windows checkout attempted with:

```powershell
git clone https://github.com/Bboy9090/PhoenixCore-.git PhoenixCore-
```

failed during checkout because tracked `mobile/node_modules` paths exceed Windows filename limits. The sparse checkout was used for PR 1 to avoid mutating source while still auditing the complete Git tree.
