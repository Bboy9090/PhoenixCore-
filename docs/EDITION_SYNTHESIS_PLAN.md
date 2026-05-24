# EDITION SYNTHESIS PLAN (Phase 4)

This document outlines the implementation strategy for Phase 4: Edition Synthesis.

## 1. Goal
Successfully transition from a single-ISO model to a multi-edition platform where branding and package selection are decoupled from the core OS logic.

## 2. Implementation Phases

### A. Manifest Consolidation (Complete)
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
- [x] All primary editions pass validation.
- [x] `list-editions.sh` correctly identifies the platform hierarchy.
- [x] Safety gates remain closed even in technician or premium editions.

## 4. Verification

Verified on 2026-05-22:

```bash
bash scripts/validate-editions.sh
bash scripts/list-editions.sh
```

Result:

- `validate-editions.sh`: all nine edition manifests valid.
- `list-editions.sh`: all edition IDs, display names, taglines, and target ISOs listed.
