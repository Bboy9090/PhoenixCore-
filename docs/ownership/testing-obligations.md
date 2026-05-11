# Testing Obligations Before Movement

PR4 does not run or change product tests. This file defines what later movement PRs must prove.

| System | Required tests before moving |
| --- | --- |
| Root Expo app | `pnpm test`, `pnpm build`, route smoke tests, API client contract checks. |
| `mobile/` | install/build smoke test, screen navigation smoke test, API client tests. |
| `phoenix-core-mobile/` | Expo route comparison, build smoke test, API client diff against root app and `mobile/`. |
| `desktop/` | `PYTHONPATH=desktop:desktop/src python -m pytest tests/`, BootForge workflow dry-runs, disk-operation mocks. |
| `backend/` | FastAPI route smoke tests, schema compatibility, hardware/USB/OCLP mocks. |
| `server/` | Python route tests, TypeScript route checks, OpenAPI diff, BootCamp fixture tests. |
| `website/` | web build, route smoke test, asset path check. |
| `legacy/` | source comparison against active systems, extraction notes, no-source-loss review. |
| `crates/` | `cargo build --workspace`, `cargo test --workspace`, cross-crate contract tests. |
| `apps/cli` | CLI build, command smoke tests, workspace tests. |
| BootCamp | driver database validation, mocked install/recovery flow, API route tests. |
| `bootable_usb/` | asset inventory, boot media manifest review, brand token comparison. |
| `legacy/usb_toolkit/` | compare launchers and rebuild tool with active BootForge, dry-run rebuild script, binary payload review. |
| `third_party/OCLP` | OCLP pipeline tests, launcher dry-run, safety controller tests, upstream version audit. |

## Dangerous Workflow Test Requirements

Any PR moving destructive workflows must include:

- dry-run mode,
- mocked device tests,
- confirmation boundary tests,
- audit/report output tests,
- failure and rollback behavior,
- platform-specific host adapter checks.

## Documentation Test Requirements

Movement PRs must update:

- `docs/migration-roadmap.md`,
- `docs/archive-manifest.md` if anything is archived,
- this ownership map if owner roles or entrypoints change.
