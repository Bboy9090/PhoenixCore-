# PhoenixCore Archive Manifest

## Purpose

This manifest records the PR 2 hygiene decision: remove obvious generated dependency/build artifacts from active tracking while preserving useful legacy source for later migration.

PR 2 does not restructure application architecture, rewrite features, or move BootForge/Phoenix Key logic. It only cleans generated files from the tracked tree and strengthens repository hygiene.

## Source Of Truth

- `docs/audits/2026-05-11-repo-inventory.md`
- `docs/audits/2026-05-11-build-entrypoints.md`
- `docs/audits/2026-05-11-phoenix-platform-map.md`
- `docs/vision/phoenix-os-manifesto.md`

## Removed From Active Tracking

Generated dependency and build artifacts removed from Git tracking:

- `mobile/node_modules/`
- `mobile/.expo/`
- `legacy/build/`
- `legacy/dist/`
- `desktop/src/installers/dist/`
- `legacy/bootable_usb/BootForge/src/installers/dist/`
- `server/**/__pycache__/`
- `*.pyc`
- `*.pyo`
- `*.toc`
- `*.pkg`
- `*.pyz`
- `*.zip`
- `*.tgz`
- `*.tar.gz`
- `desktop/tauri-app/src-tauri/src/drives/files.zip`
- `legacy/Integrate Backend and USB Features in Phoenix Core App/phoenix_core_complete.zip`
- `phoenix-core-mobile.zip`
- `phoenix-core-mobile7.zip`
- `phoenix-core-mobile/android/`
- `phoenix-core-mobile/ios/`

These files are deleted from the repository history going forward, not archived as active source. Their useful source equivalents are already present elsewhere in the tree or can be rebuilt from source and package manifests.

## Kept In Place

Useful legacy and active source intentionally kept:

- `desktop/` BootForge PyQt, CLI, recovery, OCLP, imaging, provider, safety, and plugin source.
- `legacy/bootable_usb/BootForge/` source files outside generated installer output.
- `legacy/archive/` old build/install scripts.
- `legacy/scripts/` install and security scripts.
- `legacy/create_recovery_usb.py`.
- `backend/` FastAPI hardware, USB, OCLP, and monitoring source.
- `server/` BootCamp, admin, FastAPI, Flask-style, and TypeScript bridge source.
- `crates/` Rust core, safety, imaging, workflow, report, host, bootloader, WIM, content, and plugin source.
- Root Expo/React Native app source.
- `mobile/` source files excluding generated dependencies and Expo cache.
- `phoenix-core-mobile/` source/config files excluding generated native Android/iOS projects.
- `assets/`, `attached_assets/`, and `docs/phoenix_brand/` brand/reference assets.
- `docs/phoenix_key_legendary_blueprint.md`.

## Archived In PR 2

No useful source was moved into a new archive location in PR 2.

Reason: PR 1 identified conflicting systems, but the safe next move is to remove generated junk first. PR 3 should create the Phoenix Platform scaffold and then move or archive source with clearer ownership.

PR 2 creates archive scaffolding only:

- `archive/`
- `archive/generated/`
- `archive/legacy-builds/`
- `archive/legacy-mobile/`

These directories are intentionally empty except for `.gitkeep` placeholders. They reserve reviewable destinations for later quarantine work without pretending generated artifacts are source.

Intended use:

- `archive/generated/` is for generated material that must be preserved temporarily for inspection.
- `archive/legacy-builds/` is for historical build/package payloads with source value that should not remain active.
- `archive/legacy-mobile/` is for old generated/native mobile project material after unique source/config has been extracted.

## Archive Candidates For PR 3

Candidates to move after the Phoenix Platform scaffold exists:

- `legacy/bootable_usb/BootForge/` to `archive/bootforge-usb-reference/`, after comparing with active `desktop/`.
- `legacy/Integrate Backend and USB Features in Phoenix Core App/` to an integration-reference archive, after extracting any unique docs or source.
- `phoenix-core-mobile/` to a generated-mobile-reference archive, after extracting any unique Expo/native configuration.
- `website/recovery-gui/` and `usb_creation_dashboard.html` to a web-demo archive or `apps/web/`, depending on product direction.
- Stale Heroku/deployment docs to a historical docs archive after replacement deployment docs exist.

## Rules For Future Archive Work

- Preserve useful old work before deleting it.
- Delete only generated dependencies, caches, build outputs, packaged binaries, and generated archives without source value.
- Do not remove BootForge, Phoenix Key, OCLP, BootCamp, imaging, safety, workflow, or report logic until a replacement exists.
- Keep archive moves reviewable and grouped by subsystem.
- Update this manifest whenever source is moved into or out of archive.

## Windows Checkout Risk

The primary Windows checkout blocker was tracked `mobile/node_modules/`, especially deeply nested React Native debugger/frontend paths. Removing generated dependency trees from Git tracking should make a normal checkout possible without sparse checkout or long-path workarounds.

If long-path checkout failures remain after PR 2, the next check should inspect tracked paths with:

```powershell
git ls-files | Where-Object { $_.Length -gt 240 } | Sort-Object Length -Descending
```
