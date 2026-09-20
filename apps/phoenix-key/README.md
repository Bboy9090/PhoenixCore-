# Phoenix Key

Phoenix Key is PhoenixCore's guarded desktop recovery-media writer. It preserves the **Reignite · Rebuild · Reboot** product identity while enforcing the repository boundary:

- `libbootforge` detects connected USB peripherals and phone service modes.
- PhoenixCore identifies removable media, produces verified plans, and writes only to live-proven safe external devices.
- Phoenix Key presents both engines through one desktop interface.

Browser mode never fabricates hardware and cannot write. Physical writing requires the Windows Tauri desktop runtime, an elevated process, Python 3, an exact `PHYSICALDRIVE<n>` target, and every backend safety gate below.

## Write safety contract

Phoenix Key permits writing only when all of these conditions pass:

- Windows reports the target bus as USB, SD, or MMC.
- The target is neither the boot disk nor the system disk.
- A stable serial number or unique device identifier exists.
- The source image exists, is nonempty, and fits within the target capacity.
- A fresh target identity matches the identity-bound authorization phrase.
- The operator explicitly acknowledges complete data destruction.
- The writer receives its private execution unlock from the desktop backend.
- A second live identity scan passes immediately before raw access.
- The writer caps output at the exact image size and performs full SHA-256 readback verification.

Failures remain blocked. Phoenix Key never selects a target automatically, accepts a generic filesystem path for raw writing, formats or repartitions a disk, or silently changes a blocked device into an eligible device.

## Windows Recovery Forge

Recovery Forge is a separate Recovery Center workflow for Windows backup/recovery analysis. It does **not** reuse the removable-media writer's destructive authorization.

Current Recovery Forge capabilities are read-only or evidence-only:

- inspect Windows recovery sources and bind their SHA-256 / manifest identity
- inspect package trust and exact Windows image/index metadata
- prove source/target physical separation
- bind target snapshot and stable hardware identities
- create a non-executable restore rollback contract
- verify a separate physical rollback destination
- capture read-only GPT rollback artifacts
- locate the same target after Windows `PHYSICALDRIVE<n>` re-enumeration
- reject stale target authorization and hardware substitution
- capture external-target EFI/BCD/WinRE metadata only from partitions already accessible to Windows
- record preserve-vs-explicit-discard target-data intent
- create a checksummed Recovery Evidence Bundle v2
- persist a read-only recovery session state
- export sanitized recovery diagnostics

Recovery Forge does not currently:

- erase or repartition a restore target
- apply a Windows system image
- write EFI/BCD/WinRE
- destructively inject drivers
- mount or assign inaccessible target partitions
- persist destructive authorization
- automatically resume destructive work
- expose a restore executor

A complete evidence bundle still reports `restore_executable: false`. Real hardware rollback/re-enumeration evidence is a separate validation campaign and is not replaced by fixture tests.

See:

- `docs/evidence/WINDOWS_RECOVERY_FORGE_CONVERGENCE_V2.md`
- `docs/evidence/WINDOWS_RECOVERY_FORGE_HARDENING_MATRIX.md`

## Development

```bash
npm ci
npm run check:boundaries
npm run test:artifact-receipt
npm run build
npm run desktop:dev
```

The native build requires Rust, Tauri v1 prerequisites, Python 3, and platform USB dependencies. `libbootforge` is pinned to the proven BootForge commit recorded in `src-tauri/Cargo.toml`.

## Installer artifact evidence

The `Phoenix Key Desktop` workflow builds Windows MSI and NSIS installers and emits:

```text
phoenix-key.source-artifact.json
phoenix-key.source-artifact.json.sha256
```

The receipt records the exact PhoenixCore commit, product version, target architecture, package formats, installer sizes and SHA-256 values, Authenticode state, pinned `libbootforge` commit, safety boundary, workflow identity, and lifecycle-test status.

Current workflow outputs are classified as:

```text
verified-build-output-not-packaged
write-enabled-unsigned-release-candidate
release_eligible: false
```

A successful compiler run does not promote an installer to public production. Promotion requires retained passing receipts for installation, launch, update, rollback, uninstall, a sacrificial-device write/readback, and a named-machine boot test, followed by code signing and signature verification. ARCWYRE packaging must consume the machine-readable receipt rather than infer status from an installer filename or a commit title.

A producer receipt is accepted only when the focused receipt test, frontend boundary check, installer build, unsigned-state check, repository verification, governance, artifact, application-reality, boot-matrix, and release gates all pass on the same source head.
