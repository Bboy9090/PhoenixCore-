# EDITION SYNTHESIS PLAN (Phase 4)

This document outlines the implementation strategy for Phase 4: Edition Synthesis.

## 1. Goal
Successfully transition from a single-ISO model to a multi-edition platform where branding and package selection are decoupled from the core OS logic.

## 2. Implementation Phases

### A. Manifest Consolidation (Current)
- Standardize all `edition.yaml` files.
- Create supporting assets (`colors.css`, `branding.md`, `package-profile.txt`).
- Implement shell-based validation scripts to ensure platform integrity.

### B. Theming Injection
- Update the `bwos-core` logic to read `edition.yaml` during runtime initialization.
- Map `theme.colors` to the Control Center's CSS variables.
- Dynamically load the logo and tagline from the edition profile.

### C. Build Pipeline Integration
- Update `scripts/build-edition.sh` to pass edition metadata to the Debian `live-build` environment.
- Use the `package-profile.txt` to populate the `chroot` environment during synthesis.

## 3. Success Metrics
- [ ] All 4 primary editions pass validation.
- [ ] `list-editions.sh` correctly identifies the platform hierarchy.
- [ ] Safety gates remain closed even in "Industrial" or "Premium" editions.
