# 0002: Phoenix Control Center Canonical Stack

Status: Accepted

Date: 2026-05-11

## Decision

Phoenix Control Center must use:

- Tauri,
- React,
- TypeScript,
- Tailwind,
- Rust command/system layer,
- Phoenix Agent bridge for system operations.

Expo/React Native belongs to Phoenix Mobile, not Phoenix Control Center.

## Rationale

Phoenix Control Center is the daily-driver desktop shell for Phoenix OS. It needs native desktop integration, reliable system API boundaries, and a privileged-operation model that can route through Phoenix Agent and Rust safety gates.

Tauri gives Phoenix Control Center a desktop-native shell while keeping the React/TypeScript/Tailwind UI direction. Rust gives the system layer a stronger safety and packaging foundation than ad hoc UI-owned scripts.

## Boundary

Phoenix Control Center may present:

- device status,
- app setup,
- creator/streaming/gaming readiness,
- update status,
- recovery entrypoints,
- BootForge and Phoenix Key workflows.

Phoenix Control Center must not directly perform:

- disk formatting,
- imaging,
- bootloader writes,
- driver installation,
- OCLP patching,
- recovery repair operations,
- OS update or package mutation.

Dangerous operations must go:

```text
Phoenix Control Center -> Phoenix Agent -> Rust safety gates / workflow engine -> host adapter
```

## Consequences

- Existing Expo app code can inform product flows and UX, but it is not desktop Control Center source.
- `apps/phoenix-control-center/` remains a scaffold until a Tauri shell PR creates the canonical implementation.
- Future PRs should avoid copying generated Expo or Manus runtime code into Control Center.
