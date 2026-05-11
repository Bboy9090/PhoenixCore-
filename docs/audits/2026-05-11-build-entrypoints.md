# PhoenixCore Build Entrypoint Audit - 2026-05-11

## Audit Target

- Repository: `Bboy9090/PhoenixCore-`
- Branch: `main`
- Commit: `9fc1758a702b459d8d9b89175ccea1ed521ed1d2`
- PR 1 scope: document current entrypoints and blockers only. No build fixes are made in this PR.

## Current Entrypoints

| Area | Entrypoint | Command or path | Current status |
| --- | --- | --- | --- |
| Root Expo app | `package.json` | `pnpm dev`, `pnpm test`, `pnpm build`, `pnpm check`, `pnpm lint` | Active-looking, but depends on root app/server layout and package install state |
| Root web/mobile routes | `app/` | Expo Router via `expo-router/entry` | Active-looking app shell |
| Root TypeScript API bridge | `server/_core/index.ts` | `pnpm dev:server`, `pnpm build`, `pnpm start` | Active-looking Express/TRPC bridge |
| Rust CLI | `apps/cli/src/main.rs` | `cargo run -p phoenix-cli -- <command>` | Active-looking CLI, but workspace membership is incomplete |
| Rust workspace | `Cargo.toml` | `cargo build --workspace`, `cargo test --workspace` | Partial workspace only |
| BootForge desktop | `desktop/main.py` | `python desktop/main.py --gui`, `python desktop/main.py --help` | Most coherent desktop host app |
| BootForge Python package config | `desktop/pyproject.toml`, `desktop/requirements.txt` | `pip install -r desktop/requirements.txt` | Active-looking, but not wired into root README commands |
| Phoenix Core backend | `backend/main.py` | `uvicorn backend.main:app` or `python backend/main.py` style launch | Active-looking FastAPI service |
| Industrial backend | `server/main.py` | `uvicorn server.main:socket_app` style launch | Competing FastAPI service |
| FastAPI alternate backend | `server/api_fastapi.py` | `uvicorn server.api_fastapi:app` style launch | Competing API implementation |
| Website demo | `website/web_server.py` | `python website/web_server.py` | Product/demo server, not canonical platform backend |
| Recovery GUI demo | `website/recovery-gui/` | `npm install`, `npm run dev`, `npm run build` | Vite React demo app |
| Legacy USB toolkit build | `legacy/create_recovery_usb.py` | `python3 legacy/create_recovery_usb.py --yes` | Used by deploy workflow, but writes under legacy output paths |
| Mobile copy | `mobile/package.json` | `npm start`, `npm run android`, `npm run ios`, `npm run web` | Duplicate mobile app, includes checked-in dependencies |
| Generated mobile copy | `phoenix-core-mobile/package.json` | `npm start`, `npm run android`, `npm run ios`, `npm run web` | Generated native project/reference copy |

## Root Package Scripts

From root `package.json`:

| Script | Command | Notes |
| --- | --- | --- |
| `dev` | `concurrently -k "pnpm dev:server" "pnpm dev:metro"` | Runs TypeScript API bridge and Expo web together |
| `dev:server` | `cross-env NODE_ENV=development tsx watch server/_core/index.ts` | Starts Express/TRPC bridge |
| `dev:metro` | `cross-env EXPO_USE_METRO_WORKSPACE_ROOT=1 npx expo start --web --port ${EXPO_PORT:-8081}` | Starts Expo web |
| `build` | `esbuild server/_core/index.ts --platform=node --packages=external --bundle --format=esm --outdir=dist` | Builds only the server bridge, not Phoenix OS or BootForge |
| `start` | `NODE_ENV=production node dist/index.js` | Starts bundled server bridge |
| `check` | `tsc --noEmit` | TypeScript check |
| `lint` | `expo lint` | Expo lint |
| `format` | `prettier --write .` | Mutating command, not used in PR 1 |
| `test` | `vitest run` | TypeScript tests |
| `db:push` | `drizzle-kit generate && drizzle-kit migrate` | Mutating database migration generation/application |
| `android` | `expo start --android` | Expo native target |
| `ios` | `expo start --ios` | Expo native target |
| `qr` | `node scripts/generate_qr.mjs` | QR helper |

## Rust Entrypoints

Root `Cargo.toml` currently declares only:

```toml
[workspace]
members = [
    "crates/core",
    "crates/host-windows",
    "crates/imaging",
    "crates/safety",
    "apps/cli",
]
resolver = "2"
```

But additional crates exist and are referenced by code or workflows:

- `crates/bootloader-core`
- `crates/content`
- `crates/fs-fat32`
- `crates/host-linux`
- `crates/host-macos`
- `crates/legacy-patcher`
- `crates/plugin-sdk`
- `crates/report`
- `crates/wim`
- `crates/workflow-engine`

`apps/cli/src/main.rs` exposes commands for device graph generation, report creation, read-only disk hashing, safety token generation, preflight, and JSON job execution. This is a valuable core interface, but it currently imports only `phoenix-host-windows` for device graph construction, so cross-platform CLI behavior is not yet unified.

## Broken Or Stale Entrypoints

| Path | Problem |
| --- | --- |
| `README.md` | Quick Start says `python main.py --gui` and `python main.py --help`, but root `main.py` is absent. Current file is `desktop/main.py`. |
| `README.md` | Repository map references root `src/`, but current active Python source is under `desktop/src/`. |
| `Dockerfile` | Copies `web_server.py`, `src/`, and `dist/` from repo root. Those are not active root paths. |
| `.github/workflows/release.yml` | Builds `pyinstaller --noconfirm --onefile --name BootForge main.py`, but root `main.py` is absent. |
| `tests/test_core.py` | Adds root `src` to `sys.path` and imports `src.core.*`, but root `src/` is absent. |
| `tests/simple_pipeline_test.py` and `tests/test_oclp_pipeline.py` | Path insertion points to `tests/src` or root `src` patterns instead of `desktop/src`. |
| `.github/workflows/deploy.yml` | Builds release assets from legacy paths and uses `legacy/create_recovery_usb.py --yes`. This may still be useful, but it does not represent Phoenix Platform. |
| `docker-compose.yml` and `drizzle.config.ts` | Compose config uses PostgreSQL, Drizzle is configured for MySQL. |
| `server/requirements.txt` | Includes both Flask and FastAPI dependencies plus `asyncio`, which is a stdlib module and should not be a package dependency. |

## CI And Release Risks

Current workflow risk areas:

- `.github/workflows/ci.yml` runs Rust build/test commands with `|| true`, so failures can pass silently.
- `.github/workflows/deploy.yml` loops through Rust packages with `cargo build -p $p --release || true`, masking missing workspace packages or compile errors.
- `.github/workflows/python-app.yml` runs `pytest || exit 0`, making test failure non-blocking.
- `.github/workflows/release.yml` points PyInstaller at missing root `main.py`.
- `.github/workflows/deploy.yml` publishes from `phoenix-core-mobile/dist/`, but the future canonical UI direction is Tauri desktop plus React/TypeScript/Tailwind and Phoenix Agent.
- Windows checkout can fail on tracked long paths in `mobile/node_modules`, blocking standard developer and CI flows unless long paths or sparse checkout are used.

## Expected Commands For Future Verification

These are the expected commands to repair toward in later PRs. PR 1 does not claim they currently pass.

```bash
cargo build --workspace
cargo test --workspace
pnpm test
pnpm build
PYTHONPATH=desktop:desktop/src python -m pytest tests/
```

Known blockers before claiming success:

- Full checkout reliability on Windows because of `mobile/node_modules` long paths.
- Root Python entrypoint mismatch: `main.py` and `src/` are missing at root.
- Rust workspace membership and cross-crate contracts are inconsistent.
- Python tests need package path normalization.
- Root Node dependency install state must be normalized to one package manager.
- Backend service ownership must be reduced to one Phoenix Agent API surface.

## Current Recommendation

Do not attempt to make all entrypoints pass in one PR. Use this order:

1. PR 2: quarantine generated artifacts and fix ignore rules.
2. PR 3: create the `phoenix-platform/` scaffold and move code without behavior changes.
3. PR 4: repair Rust workspace membership and core contracts.
4. PR 5: consolidate backend service code into `services/phoenix-agent`.
5. PR 6: introduce Phoenix Control Center as a Tauri + React/TypeScript/Tailwind shell.
6. PR 7: add KDE Plasma live-build and Calamares Phoenix OS foundation.

## Audit Commands Used

```powershell
git show HEAD:package.json | Select-Object -First 80
git show HEAD:Cargo.toml
git show HEAD:requirements.txt | Select-Object -First 80

git show HEAD:.github/workflows/ci.yml | Select-Object -First 120
git show HEAD:.github/workflows/deploy.yml | Select-Object -First 120
git show HEAD:.github/workflows/release.yml | Select-Object -First 120

git ls-tree -r -t --long HEAD |
  Select-String -Pattern 'tauri|src-tauri|package\.json|tailwind|vite|tsconfig|Cargo\.toml' |
  Select-String -Pattern 'node_modules' -NotMatch |
  Select-Object -First 80
```
