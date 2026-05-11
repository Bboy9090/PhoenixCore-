# PhoenixCore Ownership Map

PR4 labels the current source systems before any implementation files move.

This directory is documentation only. It does not change behavior, rewrite imports, delete files, or migrate source into the Phoenix Platform scaffold.

## Canonical Names

These names are canonical and should not be forked into competing labels:

- Phoenix Platform - the whole monorepo ecosystem.
- Phoenix OS - the daily-driver operating system.
- Phoenix Control Center - the main desktop shell.
- Phoenix Agent - the local backend bridge and system service.
- BootForge - the deployment, imaging, diagnostics, and repair layer.
- Phoenix Key - the rescue and provisioning mode.

## Hard Boundary

UI apps must not directly perform destructive disk, bootloader, imaging, repair, driver, or system operations.

Dangerous operations must go through Phoenix Agent and Rust safety gates. UI layers may request operations, display state, and render confirmations, but they must not own destructive execution.

## Owner Roles

Every system should resolve to one of these owner roles before movement:

- Control Center
- Phoenix Agent
- BootForge
- Phoenix Key
- Phoenix OS
- Mobile
- Web
- Archive
- Core Crates

## Documents

- `active-systems.md` - current systems, entrypoints, owners, preservation rules, risks, and tests.
- `migration-boundaries.md` - movement rules and forbidden shortcuts.
- `source-to-target-map.md` - current path to Phoenix Platform destination map.
- `preserve-do-not-touch.md` - source that must not be deleted or casually rewritten.
- `dependency-boundaries.md` - allowed dependency directions and dangerous operation boundaries.
- `testing-obligations.md` - required tests before moving each system.
- `risk-register.md` - open ownership and migration risks.
