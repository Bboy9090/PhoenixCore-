# Phoenix Key

Phoenix Key is PhoenixCore's desktop recovery and media-planning application. It preserves the **Reignite · Rebuild · Reboot** product identity while enforcing the repository boundary:

- `libbootforge` detects connected USB peripherals and phone service modes.
- PhoenixCore identifies removable media and produces verified, non-destructive build plans.
- Phoenix Key presents both engines through one desktop interface.

This migration phase does not expose physical media writing. Browser mode never fabricates hardware; live results require the Tauri desktop runtime.

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
unsigned-preview
release_eligible: false
```

A successful compiler run does not promote an installer to production. Promotion requires retained passing receipts for installation, launch, update, rollback, and uninstall, followed by code signing and signature verification. ARCWYRE packaging must consume the machine-readable receipt rather than infer status from an installer filename or a commit title.

A producer receipt is accepted only when the focused receipt test, frontend boundary check, installer build, unsigned-state check, repository verification, governance, artifact, application-reality, boot-matrix, and release gates all pass on the same source head.
