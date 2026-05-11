# Phoenix Platform Map - 2026-05-11

## Direction

PhoenixCore should become Phoenix Platform: the foundation for Phoenix OS as an everyday desktop operating system with recovery, deployment, diagnostics, BootForge, and Phoenix Key as flagship advantages.

Locked PR 1 assumptions:

- Phoenix OS default desktop target: KDE Plasma.
- COSMIC is deferred until the KDE foundation is stable.
- Phoenix Control Center direction: Tauri desktop shell, React + TypeScript frontend, Tailwind styling, Rust system layer, Phoenix Agent API bridge.
- PR 1 is documentation-only. No source moves, deletion, generated cleanup, formatter runs, or code rewrites.

## Proposed Monorepo Layout

```text
phoenix-platform/
├── apps/
│   ├── phoenix-control-center/
│   ├── bootforge/
│   ├── phoenix-key/
│   ├── phoenix-welcome/
│   ├── mobile/
│   └── web/
├── services/
│   └── phoenix-agent/
├── crates/
│   ├── core/
│   ├── safety/
│   ├── imaging/
│   ├── workflow-engine/
│   ├── report/
│   ├── host-windows/
│   ├── host-macos/
│   └── host-linux/
├── os/
│   └── phoenix-os/
│       ├── live-build/
│       ├── calamares/
│       ├── packages/
│       ├── branding/
│       ├── package-lists/
│       └── scripts/
├── docs/
├── scripts/
├── tests/
├── archive/
└── README.md
```

## Source-To-Target Mapping

| Current source | Future target | Classification |
| --- | --- | --- |
| `app/`, `components/`, `hooks/`, `lib/`, `constants/`, root `package.json` | `phoenix-platform/apps/phoenix-control-center/` and `phoenix-platform/apps/mobile/` planning input | Keep as active UI source/reference until Tauri shell exists |
| `desktop/` | `phoenix-platform/apps/bootforge/` | Keep, then migrate deliberately; this is the strongest current BootForge host app |
| `desktop/tauri-app/src-tauri/` | `phoenix-platform/apps/phoenix-control-center/src-tauri/` reference | Preserve as Tauri/Rust drive-enumeration experiment, but clean embedded zip/file nesting first |
| `backend/` | `phoenix-platform/services/phoenix-agent/` input | Merge into one agent API |
| `server/main.py`, `server/api_fastapi.py`, `server/bootcamp/`, `server/admin/` | `phoenix-platform/services/phoenix-agent/` input | Merge BootCamp/admin/progress concepts into one agent API |
| `server/_core/` | `phoenix-platform/apps/phoenix-control-center/` dev bridge or archive | Do not treat as OS agent |
| `crates/core` | `phoenix-platform/crates/core` | Keep and repair contracts |
| `crates/safety` | `phoenix-platform/crates/safety` | Keep as safety policy foundation |
| `crates/imaging` | `phoenix-platform/crates/imaging` | Keep and expand read/write verification primitives |
| `crates/workflow-engine` | `phoenix-platform/crates/workflow-engine` | Keep concept, repair contracts |
| `crates/report` | `phoenix-platform/crates/report` | Keep, repair field drift with core |
| `crates/host-windows` | `phoenix-platform/crates/host-windows` | Keep, replace placeholders with real provider implementation |
| `crates/host-macos` | `phoenix-platform/crates/host-macos` | Keep, repair field drift with core |
| `crates/host-linux` | `phoenix-platform/crates/host-linux` | Keep, repair field drift with core |
| `crates/content`, `crates/wim`, `crates/fs-fat32`, `crates/bootloader-core`, `crates/legacy-patcher` | `phoenix-platform/crates/` or archive depending on contract repair | Keep as candidate platform crates |
| `docs/` | `phoenix-platform/docs/` | Rewrite around Phoenix OS daily-driver identity |
| `assets/brand/`, `assets/logo/`, `docs/phoenix_brand/` | `phoenix-platform/os/phoenix-os/branding/` and app assets | Preserve |
| `docs/phoenix_key_legendary_blueprint.md` | `phoenix-platform/apps/phoenix-key/` docs and product spec | Preserve and productize |
| `website/recovery-gui/`, `website/web_server.py`, `usb_creation_dashboard.html` | `phoenix-platform/apps/web/` or `archive/` | Reference/demo material |
| `mobile/`, `screens/`, `services/`, `utils/` | Archive after merging unique code into canonical app | Duplicate |
| `phoenix-core-mobile/` | Archive after extracting any unique mobile/native settings | Generated duplicate |
| `legacy/bootable_usb/BootForge/` | `phoenix-platform/archive/bootforge-usb-reference/` | Archive/reference, not active source |
| `legacy/build`, `legacy/dist`, `legacy/usb_toolkit/executables` | Delete generated artifacts in cleanup PR after review | Generated output |

## Phoenix OS Daily-Driver Foundation

The OS foundation should be explicit, not implied by recovery tooling.

Minimum target for the first Phoenix OS foundation:

- KDE Plasma desktop session as default.
- Calamares installer integration.
- Browser support through package lists and first-run defaults.
- Flatpak and graphical app store support.
- Streaming/media readiness with OBS, codecs policy, audio stack plan, and GPU acceleration checklist.
- Gaming readiness path with Steam, Proton/Wine, controller support, and GPU driver documentation.
- LibreOffice/productivity package set.
- Bluetooth, Wi-Fi, printer, and scanner support plan.
- Phoenix Welcome first-run app.
- Phoenix Control Center as the main settings, recovery, diagnostics, and BootForge hub.

This should live under `phoenix-platform/os/phoenix-os/` with:

- `live-build/` for image generation.
- `calamares/` for installer branding and modules.
- `packages/` for Phoenix-owned packages and metadata.
- `branding/` for Plymouth, SDDM, wallpapers, icons, and app branding.
- `package-lists/` for daily-driver, creator, streaming, gaming, and recovery package sets.
- `scripts/` for reproducible image build helpers.

## Recovery And Forge Foundation

Phoenix OS must keep recovery as a superpower:

- BootForge USB creation remains a flagship app under `apps/bootforge/`.
- Phoenix Key becomes the rescue/provisioning mode under `apps/phoenix-key/`.
- Imaging, disk repair, driver injection, BootCamp, OCLP, device graph, audit report generation, and workflow engine move toward Rust-backed contracts.
- Destructive operations must flow through shared safety gates and auditable reports.
- Phoenix Agent should provide the privileged bridge between UI apps and system operations.

## Recommended PR Sequence After PR 1

### PR 2 - Cleanup Quarantine

- Remove tracked generated dependency trees and generated binaries after review.
- Add missing ignore rules for `node_modules`, `.expo`, `__pycache__`, `.pyc`, `build`, `dist`, PyInstaller artifacts, native generated mobile outputs, report bundles, and archives.
- Move useful legacy source to `archive/` with a manifest.
- Do not change app behavior.

### PR 3 - Monorepo Scaffold

- Create `phoenix-platform/` skeleton.
- Move active source into the new layout with compatibility notes.
- Keep old entrypoints as shims only where needed.
- Update README to state Phoenix OS identity: everyday OS plus creator, streaming, gaming, recovery, BootForge, and Phoenix Key.

### PR 4 - Rust Contract Repair

- Expand root workspace to include real platform crates.
- Repair `DeviceGraph`, `HostInfo`, disk/partition/volume contracts across `core`, `report`, `host-linux`, `host-macos`, `host-windows`, and `workflow-engine`.
- Make `cargo build --workspace` and `cargo test --workspace` meaningful and non-optional.

### PR 5 - Phoenix Agent

- Consolidate `backend/` and `server/` Python capabilities into `services/phoenix-agent/`.
- Define one API contract for device graph, USB creation, imaging, recovery, BootCamp, OCLP, reports, and workflow progress.
- Remove broad CORS defaults and dev-only secrets from production paths.

### PR 6 - Phoenix Control Center

- Create Tauri shell with React + TypeScript + Tailwind.
- Use Rust commands and Phoenix Agent API for privileged operations.
- Start with dashboard, device graph, reports, BootForge launch surface, recovery workflows, and settings.

### PR 7 - Phoenix OS KDE Foundation

- Add `os/phoenix-os/live-build/` and `os/phoenix-os/calamares/`.
- Add package lists for daily desktop, creators/streaming, gaming readiness, productivity, hardware support, recovery, and BootForge/Phoenix Key.
- Add Phoenix Welcome first-run app plan and packaging route.

## Archive Policy

- Preserve useful old work before deleting generated junk.
- Delete only obvious generated output after it is documented in PR 1 and reviewed in PR 2.
- Keep BootForge, Phoenix Key, OCLP, driver, imaging, and workflow assets unless there is a replacement.
- Do not bury product vision in scattered historical docs. Move conflicting docs to `archive/` once replacement docs exist.

## Risks To Carry Forward

- Full checkout currently fails on Windows unless long paths or sparse checkout are used.
- Rust crates have contract drift and incomplete workspace membership.
- App stacks are duplicated and will fight each other unless one canonical stack is chosen.
- Backends are duplicated and expose broad dev defaults.
- Current docs still describe a recovery-only product, conflicting with Phoenix OS daily-driver identity.
- CI uses failure-masking patterns and must become trustworthy before release automation means anything.

## Audit Commands Used

```powershell
git rev-parse HEAD

git ls-tree -r -t --long HEAD |
  Select-String -Pattern 'tauri|src-tauri|package\.json|tailwind|vite|tsconfig|Cargo\.toml' |
  Select-String -Pattern 'node_modules' -NotMatch |
  Select-Object -First 80

git show HEAD:docs/VISION.md | Select-Object -First 100
git show HEAD:docs/ROADMAP.md | Select-Object -First 100
git show HEAD:docs/ARCHITECTURE.md | Select-Object -First 100
git show HEAD:docs/phoenix_key_legendary_blueprint.md | Select-Object -First 100
git show HEAD:DESKTOP_CONSUMER_APP.md | Select-Object -First 100
git show HEAD:MOBILE_ENTERPRISE_INTEGRATION.md | Select-Object -First 100
```
