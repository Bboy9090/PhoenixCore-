# Rust Workspace Status - 2026-05-12

## Scope

This file records the Rust workspace status for the PhoenixCore PR10 Rust API Drift Repair Pass.

The requested PR9 status document was not present in the current checkout, so PR10 reconstructs the current status from direct workspace inspection and fresh `cargo check` runs.

## Workspace Packages

The workspace now includes the 15 discovered Rust packages:

- `phoenix-cli`
- `phoenix-core`
- `phoenix-host-windows`
- `phoenix-imaging`
- `phoenix-safety`
- `phoenix-bootloader-core`
- `phoenix-content`
- `phoenix-fs-fat32`
- `phoenix-host-linux`
- `phoenix-host-macos`
- `phoenix-legacy-patcher`
- `phoenix-report`
- `bootforge-plugin-sdk`
- `phoenix-wim`
- `phoenix-workflow-engine`

## PR10 Rust API Drift Repair

### Commands Run

```powershell
cargo check -p phoenix-content
cargo check -p phoenix-legacy-patcher
cargo check -p phoenix-workflow-engine
cargo check -p phoenix-cli
cargo check --workspace
```

Earlier in the pass, targeted checks were also run for:

```powershell
cargo check -p phoenix-host-linux
cargo check -p phoenix-host-macos
cargo check -p phoenix-report
```

### Errors Fixed

- Added all discovered Rust packages to the root workspace so `cargo check --workspace` reflects the real Rust surface.
- Fixed `phoenix-host-windows` dependency drift around the `windows` crate feature set.
- Restored the `phoenix-host-windows::format` and `phoenix-host-windows::space` module boundary for Windows and non-Windows builds.
- Repaired Windows API type drift in `phoenix-host-windows` format and disk-space helpers.
- Bridged `phoenix-core` device graph drift by keeping legacy fields while adding the newer host, partition, workflow, and timestamp fields expected by host/report/workflow crates.
- Added the missing `sha2` dependency used by `phoenix-core`.
- Repaired `phoenix-host-linux` and `phoenix-host-macos` construction of `DeviceGraph`, `Disk`, `Partition`, and `Volume` values.
- Added missing `serde` support for `phoenix-report` and derived `Debug`/`Clone` for `ReportPaths`.
- Fixed `phoenix-content` ISO mount parsing and Windows VHD feature gates.
- Fixed `phoenix-legacy-patcher` dependency drift and `plist::Dictionary` API usage.
- Added the missing imaging API surface expected by `phoenix-workflow-engine`.
- Fixed `phoenix-workflow-engine` dependency drift, free-space helper collision, report-base parsing, and non-macOS helper boundaries.

### Crates Newly Passing

The priority repair crates now pass under the checked workspace:

- `phoenix-host-linux`
- `phoenix-host-macos`
- `phoenix-report`
- `phoenix-cli`
- `phoenix-workflow-engine`
- `phoenix-legacy-patcher`
- `phoenix-content`

The full workspace also passes `cargo check --workspace` on this Windows checkout.

### Crates Still Failing

None under:

```powershell
cargo check --workspace
```

### Exact Remaining Errors

No compiler errors remain in the verified workspace check.

Remaining warning classes:

- unused imports in `phoenix-core`, `phoenix-cli`, `phoenix-host-macos`, `phoenix-wim`, and `phoenix-workflow-engine`
- unused variables and unreachable statements caused by platform-gated workflow bodies on Windows
- unused `Result` returns from Windows handle cleanup paths in `phoenix-host-windows` and `phoenix-wim`
- duplicate/unreachable workflow match arms in `phoenix-workflow-engine`

### Failure Classification

- Current build status: pass for `cargo check --workspace`
- Remaining issues: warning debt, platform-specific runtime verification gaps, and test coverage gaps
- Not verified in PR10: Linux/macOS native checks, destructive workflow execution, runtime USB/disk behavior, or full `cargo test --workspace`

## Recommended PR11

PR11 should be a Rust warning and test-hardening pass:

- fix unused import/variable warning debt without suppressing real issues
- remove duplicate/unreachable workflow match arms
- handle Windows cleanup return values explicitly
- add non-destructive unit tests around device graph compatibility, report bundle paths, operation parsing, and imaging chunk planning
- run `cargo test --workspace` after the warning cleanup
