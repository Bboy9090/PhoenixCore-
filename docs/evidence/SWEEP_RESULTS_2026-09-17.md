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


---

## Sweep 11–18 convergence update

Current convergence lane:
- branch: `convergence/windows-recovery-forge-macos-v2`
- PR: #150 remains draft
- current recorded source head at this update: `37a3e6e245e3479b876e36c24d62c2110a152818`
- release/execution claim: NOT MADE; exact-head CI still required

### Sweep 11 — Hostile source fixtures

Implemented:
- structural WIM/VHD/VHDX/ISO guards
- malformed WindowsImageBackup payload blocking
- incomplete split-WIM blocking
- hostile source guard enforced at the desktop Recovery Center boundary

Result: PASS for current hostile structural fixture set; additional real-image corpus testing remains useful.

### Sweep 12 — Source integrity and stale-plan invalidation

Implemented:
- full SHA-256 for file sources
- bounded, content-hashed directory manifests
- symlink refusal
- source identity captured before and after plan generation
- changed source invalidates planning
- desktop Recovery Center now returns the identity-bound plan

Result: PASS in source logic; destructive execution still requires a fresh identity recheck.

### Sweep 13 — Target collision, capacity, and topology

Implemented:
- live source physical-disk resolution
- source != target proof inside the destructive writer itself
- target capacity and stable identity gates
- current boot/system disk blocking
- APFS/HFS+/CoreStorage/Apple Boot GPT type detection in Windows drive evidence
- Apple-partition targets are blocked from the destructive writer candidate set
- Recovery Center target scan/selection is read-only and never assumes Disk 0

Result: PASS for current contract coverage; full partition-conflict policy remains intentionally conservative.

### Sweep 14 — Intel Mac exact model and Boot Camp package

Implemented:
- Apple Silicon hard-block from traditional Boot Camp
- exact Intel Mac model identifier requirement
- Boot Camp package content manifest hashing
- Authenticode inspection for signed package members on Windows
- exact-model evidence must actually appear in package evidence; merely labeling a generic package with a model no longer verifies it
- Intel Mac restore-design gate binds generic restore evidence + exact Mac model + exact driver package

Result: PASS for fail-closed model/package binding. Vendor-download provenance can be strengthened further when direct Apple package acquisition is implemented.

### Sweep 15 — EFI / BCD / WinRE evidence

Implemented:
- read-only EFI System Partition inventory
- Secure Boot observation
- `bcdedit /enum all` evidence
- `reagentc /info` evidence
- hashed boot-state snapshot
- evidence-driven boot-chain vs WinRE vs partition/full-restore assessment
- no boot repair command is executable from this planner

Important correction:
- online BCD/WinRE evidence is now allowed to bind only to the current Windows boot/system disk. It cannot be falsely attached to an arbitrary external restore target.

Result: PASS for online boot-repair evidence modeling.

### Sweep 16 — Rollback evidence

Implemented:
- rollback manifest bound to source identity, target identity, partition evidence, and boot-state hash
- BCD export backup
- EFI file backup only when the EFI partition is already accessible; the tool does not mount it merely to satisfy the gate
- ReAgent.xml / WinRE backup when accessible
- repair remains locked when required artifacts are absent
- corrected an unsafe condition where EFI inventory alone could have been treated as sufficient backup
- rollback bundle hashes and source/target bindings are verified before readiness

Result: PASS for fail-closed boot-repair rollback packaging. Full-disk restore rollback still requires a separate content-preservation contract before any full restore executor can exist.

### Sweep 17 — Interruption / unplug behavior

Implemented:
- short writes become explicit interruption failures
- target unplug/write/flush/fsync/read-back failures are classified by stage
- failure receipts record bytes written/read back
- interrupted writes are non-resumable
- restart requires fresh source and target identities
- successful writes still require full read-back SHA-256 verification

Result: PASS for current raw-writer interruption contract.

### Sweep 18 — Cloud / Google Drive staging foundation

Implemented provider-agnostic staging core:
- cloud original opened read-only
- provider file ID/name/size retained
- resumable `.partial` local staging
- partial prefix is re-hashed against the source before resume
- provider size mismatch fails before staging
- provider MD5 can prove transfer integrity
- trusted SHA-256 is separately required before the staged payload becomes recovery-eligible
- cloud original is never modified by the staging helper
- dedicated Windows/Linux CI workflow added

Current limitation:
- this is the safe staging layer, not yet Google OAuth/browse/download transport. A Drive connector/API must materialize the binary payload and metadata before this layer can verify it.

Result: PARTIAL by design; safe resumable staging exists, provider acquisition remains.

### Cross-evidence binding correction

A critical composability defect was fixed in restore readiness:
- package trust SHA must match the source identity SHA
- image metadata path must match the identity-bound source
- target safety source size must match the source identity size
- rollback bundle source identity must match the source
- rollback bundle target identity must match the selected target
- Windows edition must be identified
- architecture compatibility must pass

This prevents individually valid receipts from different sources or targets being mixed into a false green restore decision.

### Windows image metadata correction

Microsoft DISM documentation requires index 1 for VHD/VHDX/FFU detailed image inspection. The metadata inspector now uses index 1 directly for those formats instead of first issuing an unindexed probe.

### CI state at this update

The branch has been moving rapidly, so earlier workflow runs were repeatedly superseded/cancelled by concurrency. No release-ready claim is recorded. The exact current head must complete:
- Windows Recovery Forge
- Windows Drive Evidence
- Windows Sacrificial Writer
- Windows Image Metadata
- Boot Camp Driver Manifest
- Recovery Package Trust
- Cloud Recovery Staging
- Phoenix Key Desktop
- Phoenix Key Windows Lifecycle
- repository/governance/artifact/release gates

Agent lesson:
- evidence receipts are only meaningful when they are cryptographically/logically bound to the same source and target. Valid individual receipts must never be composable across unrelated recovery sessions.
