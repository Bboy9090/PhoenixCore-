# Ownership Risk Register

| ID | Risk | Affected systems | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R1 | Root Expo, `mobile/`, and `phoenix-core-mobile/` overlap. | Root Expo app, `mobile/`, `phoenix-core-mobile/` | Feature loss or another duplicate app if moved too quickly. | Compare routes and API clients before selecting canonical Mobile and Control Center inputs. |
| R2 | Backend ownership is split. | `backend/`, `server/`, `services/api.ts` | Conflicting Phoenix Agent API contracts. | Define Agent contract before moving routes. |
| R3 | UI and destructive operations are too close. | `desktop/`, root app, mobile apps, website | Unsafe operation execution from UI. | Enforce UI -> Phoenix Agent -> Rust safety gates. |
| R4 | BootForge and OCLP source may be mistaken for legacy-only code. | `desktop/`, `legacy/bootable_usb/BootForge/`, OCLP files | Loss of high-value repair workflows. | Preserve until replacement workflows and tests exist. |
| R5 | BootCamp logic spans server and legacy docs. | `server/bootcamp/`, `legacy/bootcamp/` | Driver workflow drift. | Assign BootForge owner with Phoenix Agent execution boundary. |
| R6 | Generated or packaged payloads may return. | `legacy/usb_toolkit/`, mobile apps, build outputs | Checkout instability, binary drift, security risk. | Keep PR2 hygiene rules; review `legacy/usb_toolkit/executables/BootForge` separately. |
| R7 | Rust crate contracts are not stable enough for app migration. | `crates/`, `apps/cli` | Broken builds or duplicated safety logic. | Repair crate contracts before relying on them as platform APIs. |
| R8 | Phoenix OS product direction drifts. | `os/`, apps, docs, website | Recovery-only, gaming-only, or enterprise-only product drift. | Treat the manifesto and canonical names as binding until explicitly updated. |
| R9 | Third-party OCLP provenance becomes unclear. | `third_party/OpenCore-Legacy-Patcher`, OCLP integration files | Licensing, update, and safety risk. | Document vendor policy and upstream version before changing integration. |
| R10 | Archive work can hide source movement. | `legacy/`, archive paths | Source loss under "cleanup" label. | Archive moves must be small, documented, and linked to extraction notes. |

## Unresolved Ownership Conflicts

- Root Expo app target: Control Center, Mobile, or split.
- `website/recovery-gui/` target: Web, BootForge UI reference, or Archive.
- `services/api.ts` target: Phoenix Agent client, generated SDK, or transitional app-local client.
- `legacy/usb_toolkit/` handling: Archive vs BootForge extraction, especially the tracked executable payload.
- Phoenix Key implementation boundary: BootForge mode, OS boot profile, or standalone app shell.
