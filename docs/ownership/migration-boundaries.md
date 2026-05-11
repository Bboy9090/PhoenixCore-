# Migration Boundaries

PR4 defines boundaries only. No source moves are approved by this document alone.

## Global Rules

- Move one subsystem at a time.
- Preserve current entrypoints until replacement entrypoints are tested.
- Do not rewrite imports across the repo as part of a documentation or scaffold PR.
- Do not delete source because it appears old.
- Archive before deleting when source value is uncertain.
- Generated dependencies, caches, build outputs, and packaged artifacts remain forbidden in active source.

## Dangerous Operations Boundary

UI apps must not directly perform destructive disk or system operations.

This applies to:

- disk formatting,
- partitioning,
- bootloader writes,
- imaging and restore,
- driver installation,
- BootCamp operations,
- OCLP patching,
- repair workflows,
- privilege elevation,
- package or OS update operations.

Required path:

```text
UI app -> Phoenix Agent -> Rust safety gates / reviewed workflow engine -> host adapter or system tool
```

The UI may request, confirm, and display operation state. Execution belongs behind Phoenix Agent and safety gates.

## Canonical Naming Rule

Use these names exactly:

- Phoenix Platform
- Phoenix OS
- Phoenix Control Center
- Phoenix Agent
- BootForge
- Phoenix Key

Do not introduce competing names such as Phoenix Desktop, Phoenix Recovery OS, BootForge OS, Phoenix Toolkit, or Phoenix Repair Center without an explicit doctrine update.

## Movement Gate

Before moving implementation files, the PR must state:

- source owner,
- destination owner,
- entrypoint before and after,
- tests to run,
- rollback plan,
- files intentionally left behind,
- files intentionally archived.

## Archive Gate

Before archiving source, the PR must state:

- why the source is not active,
- whether equivalent source exists elsewhere,
- what unique behavior or docs were preserved,
- whether any generated artifacts are being excluded.
