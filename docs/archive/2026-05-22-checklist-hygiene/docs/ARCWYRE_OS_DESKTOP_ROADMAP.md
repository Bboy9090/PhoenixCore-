# ARCWYRE OS Desktop Roadmap

This roadmap outlines the milestones for the **ARCWYRE OS Desktop** (Linux-based) branch.

## 🟢 Milestone 1: Visual Foundation (Current)
- [x] Establish ARCWYRE visual identity (colors, typography, logo).
- [x] Stabilize Control Center offline build (Zero-dependency UI).
- [x] Integrate ARCWYRE branding into Forge Dashboard.
- [x] Finalize platform architecture alignment.

## 🟡 Milestone 2: Control Center MVP
- [ ] Implement local-first data caching in Control Center.
- [ ] Connect Control Center to ARCWYRE Agent (Local WebSocket/Bridge).
- [ ] Build hardware discovery dashboard (CPU, Disk, Memory status).
- [ ] Integrate BootForge imaging triggers from UI.
- [ ] Implement StormGrid diagnostic visualization.

## 🟡 Milestone 3: Forge Mode (Recovery Environment)
- [ ] Design minimal "Forge Mode" Linux environment (Live-build).
- [ ] Autostart Control Center in fullscreen mode.
- [ ] Lock down system permissions (Immutable rootfs).
- [ ] Implement "One-Click Resurrection" imaging profile.
- [ ] Add network-less diagnostics for air-gapped recovery.

## 🔵 Milestone 4: Distribution & Deployment
- [ ] Finalize ARCWYRE OS ISO build scripts (Live-build/Custom).
- [ ] Implement ARCWYRE OS Installer (Calamares-based or Custom).
- [ ] Build "Cold Fuse" system imaging for local disks.
- [ ] Public Beta release (Community testing).

## 🔵 Milestone 5: Visual Polish & Ecosystem
- [ ] Custom KDE Plasma "Sacred Minimal" theme integration.
- [ ] ARCWYRE Key hardware binding implementation.
- [ ] ARCWYRE Agent privilege escalation security audit.
- [ ] Ecosystem launch (App store/Recovery package repository).

---

## Release-Readiness Checklist
- [ ] 100% Offline build verification.
- [ ] Safety gate validation (Zero data-loss policy).
- [ ] Hardware compatibility audit (Broad x86_64 support).
- [ ] Recovery spine performance verification.
- [ ] Documentation alignment (Internal Phoenix codenames audited).
