# Windows Recovery Forge — Sweep Results — 2026-09-17

Branch: `convergence/windows-recovery-forge-macos-v2`
PR: #150
Purpose: preserve exact parallel-sweep findings, fixes, evidence, and carry-forward work for the reusable Agent Sweep Blueprint.

## Parallel Lane A — Recovery Forge integrated CI repair

Starting symptom:
- Windows Recovery Forge matrix failed on Ubuntu, macOS, and Windows.
- Recovery UI build was also previously failing.

Defect A1 — Tauri native dialog feature mismatch
- `tauri.conf.json` allowed native open dialogs.
- Rust `tauri` dependency did not enable the matching `dialog-open` feature.
- Result: Rust recovery jobs failed before product behavior could be trusted.

Fix:
- enabled `dialog-open` in `apps/phoenix-key/src-tauri/Cargo.toml`.

Defect A2 — TypeScript target incompatibility
- Recovery Center UI used `String.replaceAll` against a TypeScript/JS target that did not guarantee that API.
- Result: guided Recovery Center UI build failed.

Fix:
- replaced the incompatible usage with target-compatible string handling.

Defect A3 — Clippy false-negative in diagnostic probe build
Observed evidence from workflow run 35165399938:
- 9/9 recovery tests passed.
- recovery probe built successfully.
- Recovery Center UI build passed.
- destructive-boundary job passed.
- Clippy alone failed because `recovery_center.rs` functions were imported by the standalone probe only for tests and appeared unused in the normal probe binary.

Root cause:
- `#[path = "../recovery_center.rs"] mod recovery_center;` was unconditional in `windows_recovery_probe.rs`.
- `cargo clippy --bin windows_recovery_probe -- -D warnings` correctly promoted those dead-code warnings to errors.

Fix:
- gate the Recovery Center module import under `#[cfg(test)]` so tests still compile the application boundary without production probe Clippy seeing test-only functions as dead code.

Commit:
- `c1adeb66e96822b8724cfc5ea0a9a6d2b692156d`

Safety impact:
- none; no warning policy was weakened and `-D warnings` remains intact.

Status:
- FIXED; fresh integrated CI pending on the later combined head.

Agent lesson:
- when tests/build pass but Clippy fails, inspect whether the lint is identifying real production debt or a test-compilation topology artifact. Fix module topology; do not suppress global lint strictness.

---

## Parallel Lane B — Windows installer lifecycle repair

Starting symptom:
- `Phoenix Key Windows Lifecycle` failed for both MSI and NSIS clean-runner lifecycle jobs.

Evidence from run 35165399954:
- lifecycle input build job passed.
- source artifact receipt generator passed.
- installed smoke receipt contract unit test passed.
- MSI/NSIS lifecycle inputs built successfully.
- MSI installation itself returned exit code 0.
- post-install smoke failed because expected `Phoenix Key.exe` did not exist.
- the installer artifact was named `windows_recovery_probe_3.2.0_x64_en-US.msi`.

Root cause:
- adding the standalone `windows_recovery_probe` binary made the Tauri/Cargo package ambiguous for bundling.
- the lifecycle build packaged the diagnostic probe instead of the Phoenix Key desktop executable.
- this was a packaging target-selection defect, not a smoke-test defect.

Fix B1 — explicit default desktop binary
`apps/phoenix-key/src-tauri/Cargo.toml` now declares:
- `default-run = "phoenix-key"`
- explicit `[[bin]]` entry for `phoenix-key` → `src/main.rs`

Fix B2 — isolate the diagnostic probe from release packaging
- explicit `[[bin]]` entry for `windows_recovery_probe`
- probe now requires feature `recovery-probe`
- feature is disabled by default

Fix B3 — make Recovery Forge CI opt into the probe
`.github/workflows/windows-recovery-forge.yml` now runs:
- `cargo test --features recovery-probe --bin windows_recovery_probe`
- `cargo build --features recovery-probe --bin windows_recovery_probe`
- `cargo clippy --features recovery-probe --bin windows_recovery_probe -- -D warnings`

This preserves diagnostic coverage while making it impossible for normal Tauri packaging to select the probe as the desktop application.

Commits:
- `172b618b63d7f7eecc5f795be824a4be92ea5be3`
- `28fe85eaf6d94736a8ecc8931b8542427293d0cb`

Safety impact:
- positive; diagnostic/testing binaries are now structurally separated from release payload selection.

Release impact:
- expected Phoenix Key installer payload should again be the actual desktop application instead of the probe.

Status:
- FIXED IN SOURCE; clean-runner MSI/NSIS evidence pending on head `28fe85eaf6d94736a8ecc8931b8542427293d0cb`.

Agent lesson:
- every auxiliary binary added to a desktop package must have an explicit release-packaging policy. Diagnostic/test executables should be feature-gated or packaged separately so release tooling cannot select them accidentally.

---

## Parallel CI state on head 28fe85eaf6d94736a8ecc8931b8542427293d0cb

At first poll:
- Windows Recovery Forge: queued
- Phoenix Key Windows Lifecycle: queued
- Phoenix Key Desktop: queued
- PhoenixCore Foundation: queued
- Windows Sacrificial Writer: queued
- Windows Drive Evidence: queued
- Release Gate / Governance / Repository / Boot Matrix / Artifact checks: queued or starting

No final pass claim is recorded until those jobs complete.

---

## Next active sweeps running in parallel

### Lane C — Hostile source fixtures
Targets:
- empty/zero-byte Windows image candidates
- truncated WIM/VHDX/VHD/ISO signatures
- random files with Windows extensions
- incomplete split WIM/SWM sets
- malformed WindowsImageBackup trees
- WindowsImageBackup payload files whose internal format does not match VHD/VHDX
- scan-depth/entry-limit behavior
- source mutation between analysis and planning

Exit criterion:
No malformed or incomplete source may become a high-confidence executable restore candidate.

### Lane D — Source integrity binding
Targets:
- file SHA-256 identity
- multi-file/directory manifest identity
- source size and modification evidence
- plan bound to source identity
- stale plan invalidation after source change

Exit criterion:
A plan cannot be reused after the material source changes.

### Lane E — Target-safety contract
Targets:
- source == target proof
- capacity checks
- stable physical-device identity
- internal/system-disk blocking
- unplug/replug identity changes
- partition topology evidence

Exit criterion:
No stale or ambiguous target can reach executable state.

---

## Reusable blueprint upgrades learned from this cycle

1. Test binaries must have an explicit packaging policy.
2. Product CI, packaging CI, and lifecycle CI are separate proof layers.
3. Successful installer exit code does not prove the correct application was installed.
4. Installed-binary identity must be asserted as part of release lifecycle testing.
5. Lint failures should be classified before suppressions are added.
6. Parallel agents should work on independent evidence lanes, not edit the same file concurrently.
7. Every red gate must be converted into a named root cause before the next architectural change.
