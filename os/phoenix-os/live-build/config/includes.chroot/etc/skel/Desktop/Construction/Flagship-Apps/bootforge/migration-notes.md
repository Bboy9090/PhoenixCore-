# BootForge Migration Notes

Current source candidates:

- Active PyQt/CLI workflows: `desktop/`.
- Reference USB toolkit source: `legacy/bootable_usb/BootForge/`.
- Rust CLI entrypoint: `apps/cli/`.
- Rust imaging and safety crates: `crates/imaging/`, `crates/safety/`, `crates/workflow-engine/`, `crates/report/`, and host crates.
- Recovery workflows: `desktop/src/recovery/`.

Migration rule:

Move BootForge only after identifying which `desktop/` and `legacy/bootable_usb/BootForge/` files are active, duplicate, generated, or reference-only. Preserve PyQt workflow logic until replacement workflows exist.

Not migrated in PR 3:

- PyQt windows and widgets.
- Disk, OCLP, BootCamp, imaging, recovery, and USB logic.
- Installer/build scripts.
