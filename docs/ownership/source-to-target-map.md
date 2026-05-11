# Source To Target Map

This map names future homes without moving source in PR4.

| Current source | Current status | Future target | Owner role | Movement rule |
| --- | --- | --- | --- | --- |
| `app/`, `App.tsx`, `index.tsx` | Active | `apps/phoenix-control-center/` or `apps/mobile/` | Control Center or Mobile | Decide product split before movement. |
| `mobile/` | Active/reference | `apps/mobile/` | Mobile | Compare with root Expo and `phoenix-core-mobile/`. |
| `phoenix-core-mobile/` | Active/reference | `apps/mobile/` or `archive/legacy-mobile/` | Mobile or Archive | Extract unique source before archiving. |
| `desktop/` | Active | `apps/bootforge/` | BootForge | Preserve PyQt workflows and operation logic. |
| `backend/` | Transitional active | `services/phoenix-agent/` | Phoenix Agent | Define API contract first. |
| `server/` | Transitional active | `services/phoenix-agent/` | Phoenix Agent | Resolve Python/TypeScript route ownership first. |
| `website/` | Reference/active | `apps/web/` or archive | Web or Archive | Decide public web vs historical demo. |
| `legacy/` | Reference | `archive/` with selective extraction | Archive | Compare before archiving or deleting. |
| `crates/` | Active | `crates/` | Core Crates | Keep canonical, repair contracts later. |
| `apps/cli/` | Active | `apps/cli/` | BootForge/Core Crates | Keep until CLI ownership is clearer. |
| `server/bootcamp/`, `legacy/bootcamp/` | Active/reference | BootForge through Phoenix Agent | BootForge/Phoenix Agent | Preserve driver database and flow semantics. |
| `bootable_usb/`, `legacy/bootable_usb/` | Reference/assets/source | `apps/bootforge/`, `apps/phoenix-key/`, `os/phoenix-os/branding/`, archive | BootForge/Phoenix Key/Phoenix OS/Archive | Split assets, source, and payloads separately. |
| `legacy/usb_toolkit/` | Reference/risk | `archive/legacy-builds/` or BootForge extraction | Archive/BootForge | Review packaged executable payload separately. |
| `third_party/OpenCore-Legacy-Patcher` | Third-party reference | Third-party reference plus BootForge integration | BootForge/Core Crates | Maintain provenance and update policy. |

## Unresolved Target Decisions

- Root Expo app may be Control Center prototype, Mobile prototype, or both.
- `website/recovery-gui/` may become Phoenix Web content, BootForge support UI, or archive.
- `services/api.ts` may become a Phoenix Agent client, a generated SDK, or app-local transitional code.
- BootCamp ownership spans BootForge workflows and Phoenix Agent execution.
- Phoenix Key source boundaries depend on BootForge and OS boot media decisions.
