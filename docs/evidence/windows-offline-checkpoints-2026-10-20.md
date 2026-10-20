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

## Native binding development follow-up

`verify_windows_installer_target.py` wraps file readback with fresh native mount/disk/volume queries before and after verification. It requires an exact local volume root, canonical physical target, reviewed stable identity, explicit partition number, healthy external disk with serial and unique identifiers, GPT, one FAT32 ESP and optionally one nonoverlapping 16 MiB MSR. It rejects invalid partition bounds/alignment, wrong mount identities, source/target collisions, and changed disk/partition/source/volume observations. Native commands are read-only; the volume query has a 30-second timeout. Cancellation is available through the CLI cancel file; existing disk/source queries still have their inherited latency limits.

Ten mocked-native regressions passed; 231 Windows-related tests pass locally. No Windows provider query ran in this qualification. The receipt uses observation-match fields and explicitly leaves a continuous volume lease, physical media certification, and boot unproven. Before/after matching cannot rule out a target swap and restoration between queries. The physical writer and desktop UI are not yet connected to this helper. This is development evidence, not a passed hardware gate.

## Independent review and macOS compilation

Independent review reproduced two rejection gaps. PE sections could extend beyond `SizeOfImage`, overlap headers, or overlap each other. Source collision checking could accept an inconsistent native source record naming the target disk with a different stable hash. Both now fail closed; fixtures declare coherent header bounds and regressions cover malformed extents, overlapping sections, absent source targets and conflicting source disk numbers. The updated local Windows-related suite passes 233 tests.

On the connected Intel Mac, an isolated checkout at `d4754ff35bd7e898a9f282e1d3c665b71e357826` passed 231 Python tests, frontend build, boundary and artifact-receipt checks, and npm audit reported zero vulnerabilities. Rust 1.98.1 `cargo check` passed against the pinned BootForge revision, and `cargo test --locked` passed all 156 tests. This is macOS compilation/testing, not Windows compilation, a signed app build, runtime qualification, or a physical-media test. The latest Python review fixes were not part of that original Mac checkout.

The previously absent app `Cargo.lock` was generated by that native compile and copied byte-for-byte; SHA-256 `09250b09af49cdceb3472178bd5f7eb40d6ed10d228875da25b51691a39207f1`. It pins dependency resolution for subsequent locked builds. No signing or store submission occurred.
