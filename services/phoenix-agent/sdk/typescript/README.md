# Phoenix Agent TypeScript SDK

This SDK is a typed boundary for Phoenix Control Center, Phoenix Mobile, BootForge UI, and Phoenix Key UI.

PR6 provides request and response models plus safe client methods. PR7 maps the existing `services/api.ts`, `mobile/src/services/api.ts`, and `phoenix-core-mobile/lib/api*.ts` client surfaces to this SDK boundary.

It does not execute destructive operations.

## Usage Direction

Apps should call Phoenix Agent through this SDK or a generated equivalent:

```text
UI app -> Phoenix Agent SDK -> Phoenix Agent -> Rust safety gates
```

## Placeholder Methods

The execute, log export, and report bundle methods return `not_implemented` placeholder responses by default. They are intentionally not wired to destructive behavior in PR6.

## Future Wiring

TODO:

- replace hand-written client with generated SDK if OpenAPI generation becomes the standard,
- reconcile `services/api.ts`, `mobile/src/services/api.ts`, and `phoenix-core-mobile/lib/api.ts` with this SDK,
- keep legacy direct build, erase, mount, unmount, workflow-run, and remote-command calls behind Agent preview and safety-gate methods,
- add auth/session handling when Phoenix Agent authentication is designed,
- add integration tests against a real Phoenix Agent service.
