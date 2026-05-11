# Preserve And Do Not Touch List

These areas contain source or product knowledge that must not be casually deleted, rewritten, or folded into new scaffolds.

## Preserve Until Replacement Exists

- `desktop/` PyQt, CLI, imaging, recovery, OCLP, safety, provider, and plugin logic.
- `legacy/bootable_usb/BootForge/` reference BootForge source.
- `backend/` hardware, USB, OCLP, monitoring, and schema source.
- `server/bootcamp/` BootCamp driver and recovery tooling.
- `crates/` safety, imaging, report, workflow, host, bootloader, WIM, content, and plugin SDK crates.
- `docs/phoenix_key_legendary_blueprint.md`.
- `bootable_usb/BootForge/assets/` Phoenix Forge and Phoenix Key brand assets.
- `third_party/OpenCore-Legacy-Patcher` provenance and integration assumptions.
- Root Expo routes and mobile app screens until a canonical app split is approved.

## Handle With Extra Review

- Any code that formats disks, writes bootloaders, images drives, repairs filesystems, installs drivers, patches macOS, or changes boot media.
- Any OCLP integration code.
- Any BootCamp driver installation or recovery flow.
- Any Phoenix Key or bootable USB material.
- Any Rust safety gate or workflow engine code.

## Archive Candidates, Not Delete Candidates

- `legacy/Integrate Backend and USB Features in Phoenix Core App/`
- `legacy/archive/`
- `legacy/build_system/`
- `legacy/usb_toolkit/`
- duplicated mobile app surfaces after comparison,
- stale deployment docs after replacement docs exist.

## Forbidden Casual Changes

- Do not make UI apps execute destructive operations directly.
- Do not duplicate disk/imaging logic into React, Expo, or web code.
- Do not vendor or patch third-party OCLP code without a vendor policy.
- Do not reintroduce `node_modules`, generated native mobile folders, build outputs, or packaged binaries as active source.
