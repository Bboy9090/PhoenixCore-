# ARCWYRE Migration Checklist

This checklist tracks the staged transition from Phoenix to ARCWYRE.

## Phase 0: Documentation Pivot 🛠️
- [x] Update `README.md` introduction.
- [x] Create `docs/CHANGE_OF_PLANS_PRD.md`.
- [x] Create `docs/ARCWYRE_REBRAND_MAP.md`.
- [x] Create `docs/BRAND_IDENTITY.md`.
- [ ] Update repository description (Manual step for Admin).
- [ ] Add deprecation notices to legacy `docs/` files.

## Phase 1: Visual Identity ✅
- [x] Create ARCWYRE design tokens (`arcwyre-theme.css`).
- [x] Update `SystemInfo` UI with ARCWYRE branding.
- [x] Update `BuildDashboard` UI with ARCWYRE Forge branding.
- [x] Update `BuildProgressCard` UI with ARCWYRE branding.
- [x] Replace legacy "Phoenix" display labels with "ARCWYRE" in UI.
- [x] Add `ArcwyreLogo` SVG component.
- [x] Update `BRAND_IDENTITY.md` with UI token guidance.
- [x] Remove legacy mascot references from UI components.

## Phase 1A: Integration & Wiring ✅
- [x] Create `apps/phoenix-control-center` entry points (`main.tsx`, `App.tsx`, `index.html`).
- [x] Import `arcwyre-theme.css` into global styles.
- [x] Resolve broken `screen-container` imports with web-compatible version.
- [x] Fix broken `SkeletonCard` imports in `BuildDashboard`.
- [x] Integrate `ArcwyreLogo` into header and dashboard.

## Phase 1B: Dependency Containment ✅
- [x] Remove missing nonessential dependencies (`recharts`, `lucide-react`, `zustand`, `@tauri-apps/api`).
- [x] Replace `lucide-react` with standalone `Icons.tsx` (plain SVG).
- [x] Replace `recharts` with custom CSS/SVG charts in `BuildDashboard` and `BuildProgressCard`.
- [x] Replace `zustand` with custom hook-based state management in `store/`.
- [x] Create `lib/bridge.ts` for safe Tauri interaction and mock fallbacks.
- [x] Verify build stability (PASSED).
    - **TypeScript**: Verified (unrelated pre-existing `@types/node` issues noted).
    - **Vite Build**: PASSED (Offline production build successful).
    - **Status**: **LOCKED**.

## Phase 2: Architecture & Roadmap Alignment ✅
- [x] Create `docs/ARCWYRE_PLATFORM_ARCHITECTURE.md`.
- [x] Create `docs/ARCWYRE_OS_DESKTOP_ROADMAP.md`.
- [x] Create `docs/ARCWYRE_NATIVE_PRD.md`.
- [x] Create `docs/ARCWYRE_SYSTEM_BOUNDARIES.md`.
- [x] Create `docs/ARCWYRE_PHASE_2_AUDIT.md`.
- [x] Define "Bobby’s Worldwide OS" (BWOS) as the Master Platform.
- [x] Create `docs/PLATFORM_EDITION_MODEL.md`.
- [x] Create `docs/BWOS_MASTER_PLATFORM_PRD.md`.
- [x] Create `docs/EDITION_MANIFEST_SPEC.md`.
- [x] **Status**: **LOCKED**.

## Phase 2B: Structural Consolidation ⏳
- [ ] Create `docs/REPO_CONSOLIDATION_PLAN.md`.
- [ ] Initialize `editions/` folder structure.
- [ ] Initialize `core/` folder structure.
- [ ] Create `editions/thunder-god/edition.yaml`.
- [ ] Create `editions/arcwyre/edition.yaml`.
- [ ] Create `editions/blue-phoenix/edition.yaml`.
- [ ] Create `editions/forge/edition.yaml`.

## Phase 3: Core Integration ✅
- [x] Port Python recovery logic to Rust Agent.
- [x] Implement "Sacred Minimal" communication protocol.
- [x] Standardize Core Crates in `core/shared`. (Build repaired for sysinfo 0.29.11)

## Phase 4: Edition Synthesis ✅
- [x] Standardize `edition.yaml` manifests.
- [x] Create core edition assets (`colors.css`, `branding.md`).
- [x] Implement `validate-editions.sh` and `list-editions.sh`.
- [x] Implement dynamic staging in `build-edition.sh`.
- [x] **Status**: **LOCKED**.

## Phase 5: Dynamic ISO Edition Synthesis ✅
- [x] Phase 5A: Hardened Staging Bridge (Non-destructive)
- [x] Phase 5B: Bullseye Package Mapping (Verified)
- [x] Phase 5C: Nightclub Synthesis Engine (LOCKED)
- [x] Successfully produce edition-specific ISOs (e.g., `bwos-thunder-god.iso`).
- [x] Verify dynamic package/theme injection in live environment.
- [x] **Status**: **LOCKED**.

## Phase 6: Controlled Atmosphere Testing ⏳
- [x] **PR28B**: Hook Stabilization + Successful Hardened ISO Completion
- [x] **PR29**: VM visual confirmation (Verify KDE/Wayland and ARCWYRE branding in hypervisor)
- [x] **PR30**: Read-only USB boot (Verify on bare-metal without internal drive modification)

## Phase 7: Build Acceleration & Native Emulation ✅
- [x] **PR31**: Build Acceleration Framework
  - [x] Add Build Modes (`fast`, `full`, `release-hardened`)
  - [x] Create package profiles (fast, full, recovery, branding lists)
  - [x] Integrate persistent package caching (`os/phoenix-os/cache/`)
  - [x] Native ARM64 build target configuration on Apple Silicon
  - [x] Add OCI host wrapper orchestration parameters
  - [x] Document and script future overlay-only refresh plan (`refresh-overlays.sh`)
- [x] **PR32**: Incremental Build Acceleration
  - [x] Local APT cache support via `PHOENIX_APT_PROXY`
  - [x] Granular build profiles (`dev-minimal`, `desktop`, `recovery`, `release`)
  - [x] Prebuilt package cache support (`package-cache.sh`)
  - [x] Incremental stages preservation with advanced Clean Modes (`--clean=none`, `--clean=stage`, `--clean=all`)
  - [x] Overlay validation and dry-run planner prototype (`refresh-overlays.sh`)
- [x] **Status**: **LOCKED**.

## Phase 8: App Reality Audit & Launch Validation ✅
- [x] **PR33**: App Reality Audit + Launch App Validation
  - [x] Create app release standard (`docs/APP_RELEASE_STANDARD.md`)
  - [x] Create launch app inventory (`docs/LAUNCH_APP_INVENTORY.md`)
  - [x] Inject core proven apps into `dev-minimal` fast profile (`fast.list.chroot`)
  - [x] Program automated pre-flight apps validation script (`validate-launch-apps.sh`)
  - [x] Perform exhaustive PR33 release reality audit and gap report
- [x] **Status**: **LOCKED**.

## Phase 9: Governed Application Execution ✅
- [x] **PR34**: Governed Application Execution + Safe Elevation Framework
  - [x] Create governed execution policies (`docs/GOVERNED_EXECUTION_MODEL.md`, `docs/SAFE_ELEVATION_POLICY.md`, `docs/OPERATION_STATE_MACHINE.md`)
  - [x] Create scoped pkexec Polkit actions (`policies/org.aurelia.phoenix.policy`)
  - [x] Scaffold audited SMART helper script (`policies/phoenix-smart-helper.sh`)
  - [x] Establish truthful UI diagnostics policy (`docs/TRUTHFUL_UI_POLICY.md`)
  - [x] Define secure cryptographically signed governance log schema (`docs/AUDIT_LOG_MODEL.md`)
  - [x] Program automated governance rules validator (`validate-governance.sh`)
- [x] **Status**: **LOCKED**.

## Phase 10: Bypass Bootstrapping (Bypass Roadmap) ⏳
- [ ] **PR35**: Unsquash/Resquash overlay injection engine
- [ ] Achieve < 45 second custom branded ISO refreshes

