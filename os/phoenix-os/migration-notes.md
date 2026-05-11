# Phoenix OS Migration Notes

Current source and concept candidates:

- OS direction: `docs/vision/phoenix-os-manifesto.md`.
- Platform map: `docs/audits/2026-05-11-phoenix-platform-map.md`.
- Recovery and deployment logic: `desktop/`, `legacy/bootable_usb/BootForge/`, and `crates/`.
- Existing scripts and build experiments under `legacy/build_system/` and `legacy/scripts/`.

Migration rule:

Start with reproducible OS configuration, package lists, and installer docs before adding release automation. Do not turn Phoenix OS into a recovery-only image or a generic gaming remix.

Not migrated in PR 3:

- live-build config.
- Calamares modules.
- package lists.
- ISO build scripts.
