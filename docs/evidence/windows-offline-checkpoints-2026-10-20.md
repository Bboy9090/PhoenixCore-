# Offline Windows application checkpoint qualification

Baseline: `a3384d98934ef9fe591455246953c0dabc651ff0` on the ARCWYRE Drive convergence branch.

The offline WIM application helper now persists an operation UUID, source path and SHA-256, selected index, workspace, phase, status, and an integrity hash in `operation-state.json`. Checkpoints precede source snapshotting, metadata inspection, native application, and file readback. Completion records the applied manifest hash while explicitly leaving boot and Windows To Go unresolved. Caught failures retain their phase and error. No checkpoint authorizes resume.

Updates use an exclusive pending file, file flush/fsync, and atomic replacement. POSIX directory entries are also fsynced. Windows directory/power-loss durability is not qualified. A retained pending file blocks another update rather than silently overwriting ambiguous state. The unkeyed SHA-256 detects accidental record changes; it is not a signature or authentication guarantee.

The shared DISM runner checks cancellation before launch and after exit, reaps a cancelled child, retains a flushed transcript, and reports the exit code without describing all operations as WIM splitting.

## Verified in the local Linux environment

- 212 Windows-related tests passed, including 33 focused preparation/application tests.
- A real Python subprocess was terminated and reaped by the shared runner.
- A real child failed with exit code 7; its diagnostic remained in the transcript.
- A subprocess exited abruptly with code 23 during mocked image application. Its source snapshot and hashed `image_application` checkpoint survived, with no success or resume claim.
- Simulated atomic-replace failure preserved the previous checkpoint and retained pending evidence.
- Frontend TypeScript/Vite build, repository boundary check, and artifact-receipt test passed.
- Locked frontend npm audit reported zero vulnerabilities.
- Twelve JSON/Markdown evidence exporters now use exclusive creation. A competing-create regression exercises every exporter and preserves the competing sentinel file. Existing overwrite and same-target rejection checks passed; the fail-closed registry suite also passed.

## Explicitly unresolved

All registered remote computers were offline at inspection. This run did not execute native DISM, Rust/Tauri compilation, physical disk provisioning, Windows To Go, USB readback, or a hardware/VM boot. The product parity audit still reports 17 blocked feature families. Full legacy unittest discovery remains red (seven failures and fourteen errors before this change), including foreign Windows-path fixtures on Linux, Windows-only ctypes mocks, and tests expecting the invalid tool registry to verify. Registry rejection remains intact.

No physical disk was opened or changed. This evidence does not establish release readiness.

## Installer file-readback follow-up

`verify_windows_installer_readback.py` now exposes a read-only CLI for comparing a prepared source manifest with an independently mounted readback directory. It rejects source/destination overlap, changed/missing/extra files, unprepared source layouts, cancellation, and source changes during inspection. The selected fallback EFI file must have matching x64/ARM64/x86 PE headers, an EFI-application subsystem, a bounded section table, and an entry point backed by executable file bytes. Headers are inspected without executing the binary.

Nine new portable regression tests passed; the Windows-related suite now passes 221 tests locally. These use synthetic PE/WIM fixtures, not a Microsoft image or firmware execution. This component is available as a CLI, not yet wired into a physical writer or the desktop UI. Its receipt explicitly leaves native disk identity, partition layout, BCD, signature/Secure Boot trust, and actual boot unverified. No Windows-native or physical-media gate is promoted.
