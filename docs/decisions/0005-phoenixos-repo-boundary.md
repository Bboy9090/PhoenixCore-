# 0005: PhoenixOS Repository Boundary

Status: Accepted

Date: 2026-05-12

## Decision

Phoenix OS remains inside PhoenixCore under:

```text
os/phoenix-os/
```

Phoenix OS may become a separate repository later, but not during the current platform stabilization, ownership, and contract-building phases.

## Why Phoenix OS Stays In PhoenixCore For Now

Phoenix OS is not ready to split because its core dependencies are still being defined inside PhoenixCore:

- Phoenix Agent API contracts are new and not yet implemented.
- Rust crate boundaries are not yet stable enough to package as external platform dependencies.
- Phoenix Control Center is still a scaffold, not a working shell.
- BootForge and Phoenix Key boundaries are documented but not migrated.
- OS package lists, live-build config, Calamares config, branding, and ISO scripts are still scaffolds.
- No successful Phoenix OS ISO build exists yet.

Keeping `os/phoenix-os/` in PhoenixCore lets the team evolve the operating-system integration beside the platform logic it will consume.

## Why Early Repo Splitting Is Dangerous

Splitting Phoenix OS too early would create avoidable platform debt:

- duplicated contracts between PhoenixCore and PhoenixOS,
- unstable boundaries between Agent, crates, apps, and OS integration,
- dependency drift between source logic and packaged OS components,
- fragmented ownership across multiple repos before the product shape is stable,
- duplicated tooling for builds, scripts, SDKs, and release checks,
- broken package assumptions because real package dependency flow does not exist yet.

An early split would make PhoenixOS look independent before it can actually consume PhoenixCore as packaged, versioned platform components.

## Future Split Conditions

PhoenixOS may become its own repository only after all of these are true:

- Phoenix Agent contract is stable and implemented enough for app and OS consumers.
- Rust crate boundaries are stable and packageable.
- Phoenix Control Center shell exists in canonical Tauri + React + TypeScript + Tailwind + Rust form.
- BootForge boundaries are documented and its active workflows are mapped to Agent and crate ownership.
- OS build and package pipeline exists under `os/phoenix-os/`.
- First Phoenix OS ISO builds succeed reproducibly.
- Package dependency flow is real: PhoenixOS consumes packaged PhoenixCore components instead of copying source logic.

Until those conditions are met, PhoenixOS remains part of PhoenixCore.

## Canonical Ownership

PhoenixCore owns:

- platform logic,
- services,
- safety,
- SDKs,
- tooling,
- device intelligence,
- Phoenix Control Center,
- BootForge,
- Phoenix Key.

PhoenixOS owns:

- distro integration,
- live-build,
- Calamares,
- KDE branding,
- package lists,
- ISO builds,
- release engineering,
- system integration.

## Package Relationship

PhoenixOS consumes packaged PhoenixCore components.

It must not duplicate PhoenixCore source logic for:

- Phoenix Agent,
- Rust safety gates,
- SDKs,
- device graph/intelligence,
- BootForge workflows,
- Phoenix Key rescue/provisioning logic,
- Control Center application code.

The intended relationship is:

```text
PhoenixCore source -> packaged platform components -> PhoenixOS image integration
```

PhoenixOS should integrate and configure packages. PhoenixCore should remain the source of platform behavior.

## Future Repository Candidates

Potential future repositories:

- `PhoenixOS`
- `PhoenixMobile`
- `PhoenixWeb`

Even if those repos are created later, PhoenixCore remains the platform brain: contracts, services, SDKs, safety, device intelligence, BootForge, Phoenix Key, and shared platform logic stay governed here unless a later decision record explicitly changes that.

## Non-Goals

PR6A does not:

- move OS files,
- split repositories,
- create package builds,
- create ISO builds,
- rewrite app architecture,
- move source out of PhoenixCore,
- change runtime behavior.
