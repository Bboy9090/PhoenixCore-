# Windows Recovery Forge Convergence V2

## Canonical lane

- Repository: `Bboy9090/PhoenixCore-`
- Base: `main`
- Base SHA at branch creation: `b9cc058419dd6711d6eff3d9ff1a84256cd3803f`
- Working branch: `convergence/windows-recovery-forge-macos-v2`
- Draft PR: #150

The earlier `convergence/windows-recovery-forge-macos` branch was discovered to be based on the older `coderabbitai/utg/2e0b4db` lineage. It is not the canonical implementation lane.

## Branch reconciliation

The older Phoenix Key integration and Windows lifecycle branches are already ancestors of current `main`.

`agent/phoenix-key-safe-device-write-3.2` is divergent from current `main` (six commits ahead and three commits behind at audit time). It is therefore treated as a donor/evidence lane, not a wholesale merge target. Current `main` already contains typed device-family/mode filtering, Windows target normalization, write preparation evidence, explicit authorization, and the guarded sacrificial writer path.

## Recovery core added in this lane

`apps/phoenix-key/src-tauri/src/windows_recovery.rs` provides non-destructive backup inspection and recovery planning.

Current verified design constraints:

- WIM is identified using the `MSWIM` signature rather than extension alone.
- VHDX uses the `vhdxfile` signature.
- legacy VHD checks the `conectix` footer.
- ISO checks the ISO9660 `CD001` volume descriptor.
- extracted Windows trees are inspected for `boot.wim`, `install.wim`, `install.esd`, split WIMs, WinRE, EFI, BCD, and `setup.exe`.
- extension-only FFU/SWM matches are not accepted as restore-ready.
- Apple Silicon blocks traditional Boot Camp planning.
- every current recovery plan is dry-run-only and reports `destructive_actions_performed: false`.

`apps/phoenix-key/src-tauri/src/bin/windows_recovery_probe.rs` exposes JSON inspection/planning for fixture and CI testing without attaching the recovery core to the physical writer.

## CI safety gate

`.github/workflows/windows-recovery-forge.yml` runs the recovery probe on Ubuntu, macOS, and Windows and separately scans the recovery core for direct destructive writer APIs/commands.

The destructive-boundary job has passed on the initial implementation. The first functional job failure was formatting-only because `cargo fmt --all` crossed into pre-existing Phoenix Key formatting. The workflow has been narrowed so functional compiler/tests/clippy can surface independently; formatting cleanup remains a separate required task before final merge.

## Google Drive recovery-source reconnaissance

The connected Drive exposes this hierarchy:

`WindowsImageBackup/`
`  bj-90-PC/`
`    Catalog/`
`    Backup 2025-02-13 104757/`

At reconnaissance time, direct reads of the `Catalog` and `Backup 2025-02-13 104757` folders returned no visible child files through the connector. Searches for `Winre.wim` and `.vhdx` did not expose binary payloads. Therefore the hierarchy is a confirmed recovery-source lead, but it is NOT yet counted as a validated recovery fixture until actual image files become visible/downloadable.

The original Drive data remains untouched.

## Next gates

1. Make recovery-core tests/build/clippy green on Ubuntu, macOS, and Windows.
2. Format only the new recovery sources without mass-editing legacy files.
3. Compare the six divergent safe-device-write commits against current main feature by feature.
4. Add read-only Tauri commands for backup inspection/recovery planning.
5. Add a Google Drive source adapter only after real binary-file metadata/download paths are validated.
6. Build the macOS distribution split: sandboxed App Store analysis edition vs direct notarized Recovery edition for privileged operations.
7. Do not mark PR #150 ready until evidence gates pass.
