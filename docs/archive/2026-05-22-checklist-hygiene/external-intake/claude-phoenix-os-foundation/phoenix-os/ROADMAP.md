# Phoenix OS Roadmap

This document tracks the development milestones for Phoenix OS from MVP foundation to public release.

---

## Phase 0 — Repository Foundation (Current)

**Goal:** Establish a real, buildable project structure that can grow into a shippable OS.

- [x] Repository structure and documentation
- [x] live-build configuration skeleton
- [x] Package lists: KDE Plasma, repair tools, recovery utilities
- [x] Calamares installer configuration skeleton
- [x] Branding placeholders (wallpaper, boot splash, SDDM theme, icons)
- [x] Build scripts: `build-iso.sh`, `clean.sh`, `verify-host.sh`, `package-debs.sh`
- [x] Safety-first disk tooling rules and guardrails
- [x] Custom app skeletons: Control Center, Recovery, Welcome, BootForge Launcher
- [x] Smoke test and ISO validation framework
- [ ] First successful bootable ISO build
- [ ] CI pipeline: GitHub Actions build-on-push

---

## Phase 1 — Bootable Alpha ISO

**Goal:** A live ISO that boots to KDE Plasma with Phoenix branding and core repair tools.

- [ ] Complete live-build config validation
- [ ] Plymouth boot splash (Phoenix flame animation)
- [ ] SDDM login screen with Phoenix theme
- [ ] KDE Plasma 6 with Phoenix color scheme and wallpaper
- [ ] All Phase 0 package lists verified installable
- [ ] Phoenix Welcome app: functional GTK/Qt window
- [ ] BootForge Launcher stub: detects Phoenix Key USB presence
- [ ] First internal ISO test: boots in QEMU, network up, tools launch
- [ ] Calamares installs to disk in VM without errors
- [ ] Firmware detection: `fwupd`, `linux-firmware` package list validated

**Target:** Internal build milestone

---

## Phase 2 — Developer Preview

**Goal:** A shareable ISO for trusted testers, with real recovery and repair workflows.

- [ ] Phoenix Control Center v0.1: disk info, S.M.A.R.T. data, network status
- [ ] Phoenix Recovery v0.1: guided fsck, NTFS repair, photo/document rescue
- [ ] BootForge integration: Phoenix Key read/write, session log export
- [ ] ARM64 build target: Raspberry Pi 4/5, Apple Silicon (UTM)
- [ ] Secure Boot signing pipeline (Shim + MOK)
- [ ] Custom kernel config (minimal + repair-optimized)
- [ ] .deb packaging for all custom apps
- [ ] Flatpak support: enabled, curated repo list
- [ ] System locale and language pack support
- [ ] Accessibility: screen reader, high-contrast theme
- [ ] Persistent live session support (USB install with overlay)

**Target:** Limited external release

---

## Phase 3 — Public Beta

**Goal:** A polished, installable OS that professionals can trust on client machines.

- [ ] Phoenix Control Center v1.0: full diagnostics suite
- [ ] Phoenix Recovery v1.0: imaging (dd/clonezilla integration), RAID recovery
- [ ] Phoenix Key hardware SDK: public API for third-party tool integration
- [ ] OEM image variant: stripped-down for repair shop deployment
- [ ] Update system: APT + Phoenix-managed channel
- [ ] Telemetry opt-in: anonymous crash and hardware reporting
- [ ] Signed ISO with published SHA256/GPG verification
- [ ] Documentation site: docs.phoenix-os.io
- [ ] Community: Discord, forum, issue tracker

**Target:** Public beta release

---

## Phase 4 — v1.0 Stable

**Goal:** A production-ready OS that ships on Phoenix Key hardware.

- [ ] LTS support commitment (3 years minimum)
- [ ] Certified hardware list
- [ ] Phoenix Key hardware bundle: OS pre-loaded
- [ ] Enterprise licensing for repair organizations
- [ ] Automated ISO testing pipeline (hardware-in-the-loop)
- [ ] Localization: EN, ES, FR, DE, PT, ZH
- [ ] FIPS compliance review (for government/defense adjacent customers)

---

## Backlog / Future Exploration

- AI-assisted diagnostics (local inference, no cloud dependency)
- Phoenix OS Server variant (headless recovery server)
- Mobile companion app (iOS/Android) for remote session monitoring
- Hardware compatibility database (crowdsourced)
- Plugin system for Phoenix Control Center
