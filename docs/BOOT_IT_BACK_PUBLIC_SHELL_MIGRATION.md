# Boot It Back — Public Shell Migration

## Public identity
**Boot It Back**

This migration changes the customer-facing desktop/install identity only.

## Preserved compatibility surfaces
The following remain unchanged:

- repository: `Bboy9090/PhoenixCore-`
- internal package/app ID: `phoenixcore-desktop`
- Tauri identifier: `com.bobbysworld.phoenixcore.desktop`
- `PHOENIXCORE_*` environment variables
- PhoenixCore evidence/schema identifiers
- BootForge crate/library names
- existing audit receipt schema versions
- repair/session persisted identifiers

PhoenixCore remains the internal orchestration and device-intelligence layer. BootForge remains an internal low-level engine.

## User-facing scope
Boot It Back owns computer-only workflows:

- boot diagnosis and recovery
- OS installation/reinstallation planning
- BIOS/UEFI-aware recovery guidance
- disks, partitions, imaging and removable media
- multiboot/recovery-media handoff to Phoenix Key
- repair-session evidence and safe execution planning

Phone/tablet workflows belong to **BobFWTools**.

## Release gate
This public rename is qualified only when the existing desktop build, installer lifecycle, rollback, dashboard build, and safety/evidence tests pass under the new installer display name.
