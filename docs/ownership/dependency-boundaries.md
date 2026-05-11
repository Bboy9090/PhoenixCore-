# Dependency Boundaries

Phoenix Platform should move toward explicit dependency direction instead of cross-calling scattered scripts.

## Allowed Direction

```text
Apps -> Phoenix Agent -> Core Crates / reviewed workflows -> host adapters / system tools
```

Apps include Phoenix Control Center, Phoenix Welcome, BootForge UI, Phoenix Key UI, Mobile, and Web.

## App Boundaries

- Apps may render UI, collect user intent, display status, and call stable APIs.
- Apps must not format disks, write bootloaders, image drives, patch systems, install drivers, or run privileged repair scripts directly.
- Apps should not import backend internals or Rust crate internals directly.

## Phoenix Agent Boundaries

- Phoenix Agent owns local API contracts for system state and operations.
- Phoenix Agent may coordinate Python transitional code and Rust-first implementations.
- Phoenix Agent must enforce authentication, confirmation, audit logging, dry-run behavior, and safety gate calls for dangerous workflows.

## Core Crates Boundaries

- `crates/safety` owns safety decisions and validation.
- `crates/imaging` owns imaging primitives.
- `crates/workflow-engine` owns workflow orchestration concepts.
- `crates/report` owns audit/report bundle output.
- host crates own platform-specific adapters.

## BootForge Boundaries

- BootForge owns deployment, imaging, USB creation, diagnostics, repair, BootCamp, and OCLP workflows.
- BootForge UI must still route destructive execution through Phoenix Agent and safety gates.

## Phoenix Key Boundaries

- Phoenix Key owns rescue/provisioning mode.
- Phoenix Key should reuse BootForge workflows and Phoenix Agent execution paths rather than creating a separate recovery stack.

## Web And Mobile Boundaries

- Web should not become a privileged local operations surface.
- Mobile should be a companion and remote-friendly app, not a local destructive execution engine.
- Both may call APIs but must respect Phoenix Agent and safety boundaries.

## Third-Party Boundaries

- `third_party/OpenCore-Legacy-Patcher` must remain traceable to upstream.
- Any OCLP integration must document upstream version, patch policy, license implications, and safety tests.
