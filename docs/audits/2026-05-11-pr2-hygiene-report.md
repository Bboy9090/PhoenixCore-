# PhoenixCore PR 2 Hygiene Report - 2026-05-11

## Scope

PR 2 is repo hygiene and quarantine only.

This PR does not restructure app architecture, rewrite features, or move BootForge/Phoenix Key/PyQt source logic. It removes generated dependency/build artifacts from active tracking, strengthens repo hygiene files, and records archive policy for the next phase.

## Files Removed From Tracking

Total generated/artifact paths removed from Git tracking: 46,416.

Top-level removal summary:

| Top-level path | Removed paths |
| --- | ---: |
| `mobile/` | 46,248 |
| `legacy/` | 84 |
| `phoenix-core-mobile/` | 64 |
| `server/` | 16 |
| `desktop/` | 2 |
| `phoenix-core-mobile.zip` | 1 |
| `phoenix-core-mobile7.zip` | 1 |

Removed categories:

| Category | Removed paths |
| --- | ---: |
| `node_modules` dependency files | 46,246 |
| Expo cache files | 2 |
| Build/dist/target paths | 12,909 |
| Python cache directories | 16 |
| Python compiled files | 16 |
| PyInstaller artifacts | 6 |
| Generated archives | 10 |
| Generated native mobile files | 64 |

Category counts overlap where generated dependency trees contain nested build/dist paths.

## Files Kept

Important source and product material intentionally kept:

- BootForge PyQt/CLI/core/recovery/plugin source in `desktop/`.
- BootForge reference source in `legacy/bootable_usb/BootForge/` outside generated installer output.
- Legacy scripts in `legacy/scripts/`, `legacy/archive/`, and `legacy/create_recovery_usb.py`.
- Rust crates in `crates/`.
- Backend source in `backend/` and `server/`.
- Root Expo app source.
- Mobile source in `mobile/` excluding generated dependencies and Expo cache.
- `phoenix-core-mobile/` source/config files excluding generated native Android/iOS projects.
- Brand assets, Phoenix Key docs, and PR 1 audit/doctrine docs.

## Files Archived

No source files were moved into archive in PR 2.

Useful old project material remains in place until PR 3 creates the Phoenix Platform scaffold and can move source with clearer ownership. See `docs/archive-manifest.md`.

Archive scaffolding created for later quarantine work:

- `archive/`
- `archive/generated/`
- `archive/legacy-builds/`
- `archive/legacy-mobile/`

Each archive directory contains only a `.gitkeep` placeholder.

## Hygiene Files Added Or Strengthened

- `.gitignore`
  - Added global dependency/build/cache rules for `node_modules`, `.expo`, `dist`, `build`, `target`, `__pycache__`, compiled Python files, PyInstaller outputs, generated archives, native generated mobile projects, logs, reports, secrets, IDE files, and OS junk.
- `.gitattributes`
  - Added line-ending normalization and binary classification for common source, docs, assets, archives, and packaged binaries.
- `.editorconfig`
  - Added baseline UTF-8, LF, indentation, final-newline, and whitespace conventions.
- `docs/archive-manifest.md`
  - Added keep/remove/archive policy and PR 3 archive candidates.

## Clone And Checkout Risk Reduction

Before PR 2, a normal Windows checkout failed because tracked `mobile/node_modules` paths exceeded Windows filename limits.

After PR 2 cleanup:

- Remaining tracked generated-path spot-check count: 0.
- Remaining tracked paths longer than 240 characters: 0.
- Longest remaining tracked path length: 153 characters.
- Tracked file count after staged removals and archive scaffolding: 667.

Sparse checkout should no longer be required solely to avoid the previous generated dependency long-path failure.

## Remaining Blockers

- App stacks remain duplicated: root Expo app, `mobile/`, and `phoenix-core-mobile/`.
- Backend stacks remain duplicated: `backend/`, `server/`, `server/_core/`, and `website/web_server.py`.
- Root README, Dockerfile, and release workflows still reference stale entrypoints.
- Rust workspace membership and cross-crate contracts are still inconsistent.
- CI still masks failures with `|| true` in several places.
- Useful legacy source still needs owner-by-owner migration into Phoenix Platform.

## PR 3 Recommendation

Create the Phoenix Platform scaffold without rewriting product logic:

```text
phoenix-platform/
|-- apps/
|-- services/
|-- crates/
|-- os/
|-- docs/
|-- scripts/
|-- tests/
|-- archive/
`-- README.md
```

Then move active source in reviewable groups:

- `desktop/` toward `apps/bootforge/`.
- Rust crates toward `crates/`.
- Backend/agent candidates toward `services/phoenix-agent/`.
- Root app source toward `apps/phoenix-control-center/` planning input.
- Useful legacy source toward `archive/` only after comparing with active source.

Do not repair every build in PR 3. The goal should be source ownership and path clarity first.

## Verification Commands

```powershell
git status
git diff --stat
git diff --cached --stat

git ls-files |
  Select-String -Pattern '(^|/)(node_modules|dist|build|target|__pycache__|\.expo)(/|$)|\.(pyc|pyo|toc|pkg|pyz|zip)$|(^|/)android/|(^|/)ios/' |
  Measure-Object

git check-ignore -v --no-index -- mobile/node_modules/react-native/sdks/hermesc/win64-bin/icudt64.dll
git check-ignore -v --no-index -- legacy/dist/BootForge
git check-ignore -v --no-index -- legacy/build/BootForge/Analysis-00.toc
git check-ignore -v --no-index -- server/__pycache__/main.cpython-314.pyc
git check-ignore -v --no-index -- desktop/src/installers/dist/bootforge-standalone.py
git check-ignore -v --no-index -- phoenix-core-mobile/android/app/build.gradle
git check-ignore -v --no-index -- phoenix-core-mobile/ios/Podfile
git check-ignore -v --no-index -- phoenix-core-mobile.zip
git check-ignore -v --no-index -- desktop/tauri-app/src-tauri/src/drives/files.zip
git check-ignore -v --no-index -- target/debug/phoenix-cli.exe

git ls-files |
  Where-Object { $_.Length -gt 240 } |
  Sort-Object Length -Descending
```
