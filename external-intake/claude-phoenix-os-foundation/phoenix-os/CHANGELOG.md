# Phoenix OS — Changelog

All notable changes to Phoenix OS are documented in this file.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
Phoenix OS versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased] — v0.1.0-alpha

### Added
- Complete repository foundation: directory structure, documentation, build system
- `live-build` configuration for Ubuntu 24.04 LTS (Noble Numbat) base
- KDE Plasma 6 as primary desktop environment
- 9 curated package lists: base, KDE, repair tools, disk tools, network tools, recovery tools, firmware, Flatpak, Phoenix apps
- 5 live-build hooks: user config, KDE session, disk safety policy, firewall, Flatpak
- Calamares installer configuration: settings, branding, partition safety, users, welcome
- Safety-first disk policy: udev rules blocking internal disk auto-mount in live session
- Polkit rules for privileged disk tool access
- Phoenix theme package: KDE color scheme (Phoenix Dark), SDDM login theme, Plymouth boot splash
- Phoenix tools package: udev rules, polkit policy, `phoenix-sysinfo` CLI report tool
- Phoenix welcome package: first-boot shell stub (kdialog-based)
- Phoenix Control Center: Tauri 2 + Rust backend (system, disk, network, thermal commands)
- Phoenix Control Center: React + TypeScript frontend (Dashboard, Disks, System, Network, Repair views)
- Phoenix Recovery: Tauri 2 skeleton with safety confirmation gate module
- BootForge Launcher: Phoenix Key USB detection, session read/write module
- Build scripts: `build-iso.sh`, `clean.sh`, `verify-host.sh`, `package-debs.sh`
- Test suite: `test-boot.sh` (QEMU smoke test), `validate-iso.sh` (ISO structure validation)
- GitHub Actions CI: validate, Rust build, React build, full ISO build on tag
- Full documentation: architecture, build system, branding, security model, hardware support

### Architecture Decisions
- Base: Ubuntu 24.04 LTS chosen over Debian for broader hardware driver support and HWE kernel access
- Desktop: KDE Plasma 6 chosen for customizability depth and professional tool integration
- App framework: Tauri 2 + Rust chosen for minimal binary size, memory safety, and native performance
- Disk safety model: explicit user confirmation with typed device path for all destructive operations
- Flatpak: apps not pre-installed in ISO (keeps image manageable); configured repo only

### Known Issues (Phase 0)
- Custom `.deb` packages are stubs; `080-phoenix-apps.list.chroot` must be commented out for first ISO build
- Tauri app frontends lack icons directory (`apps/*/icons/`) — will fail `cargo tauri build` without placeholder PNGs
- Plymouth PNG assets (logo, ember particle) not yet created — splash falls back to text
- ARM64 build not tested (structure ready, untested)
- `phoenix-control-center` disk command returns empty list (lsblk JSON parser is a Phase 1 TODO)

---

## Release Numbering

| Version | Milestone |
|---------|-----------|
| 0.1.x   | Phase 0 — Repository foundation |
| 0.2.x   | Phase 1 — First bootable alpha ISO |
| 0.5.x   | Phase 2 — Developer preview |
| 0.9.x   | Phase 3 — Public beta |
| 1.0.0   | Phase 4 — Stable release |
