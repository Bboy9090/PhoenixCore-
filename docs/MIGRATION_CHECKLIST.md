# ARCWYRE Migration Checklist

This checklist tracks the staged transition from Phoenix to ARCWYRE.

## Phase 0: Documentation Pivot 🛠️
- [x] Update `README.md` introduction.
- [x] Create `docs/CHANGE_OF_PLANS_PRD.md`.
- [x] Create `docs/ARCWYRE_REBRAND_MAP.md`.
- [x] Create `docs/BRAND_IDENTITY.md`.
- Manual admin follow-up: repository description update is outside the repo and is not tracked as a repo checklist item.
- [x] Archive stale legacy roadmap/checklist docs under `docs/archive/2026-05-22-checklist-hygiene/`.

## Phase 1: Visual Identity ✅
- [x] Create ARCWYRE design tokens (`arcwyre-theme.css`).
- [x] Update `SystemInfo` UI with ARCWYRE branding.
- [x] Update `BuildDashboard` UI with ARCWYRE build branding.
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

## Phase 2B: Structural Consolidation ✅
- [x] Create `docs/REPO_CONSOLIDATION_PLAN.md`.
- [x] Initialize `editions/` folder structure.
- [x] Initialize `core/` folder structure.
- [x] Create `editions/thunder-god/edition.yaml`.
- [x] Create `editions/arcwyre/edition.yaml`.
- [x] Create `editions/blue-phoenix/edition.yaml`.
- [x] Create `editions/forge/edition.yaml`.
- [x] **Status**: **LOCKED**.

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

## Phase 10: Bypass Bootstrapping (Bypass Roadmap) ✅
- [x] **PR35**: Unsquash/Resquash overlay injection engine
  - [x] Implement dynamic SquashFS bypass script (`bypass-rebuild.sh`)
  - [x] Add high-speed ZSTD level 1 re-compression pipeline
  - [x] Integrate xorriso boot-sector packing routines
  - [x] Integrate automated dry-run audited simulation fallbacks for development environment compatibility
  - [x] Achieve < 45 second custom branded ISO refreshes
- [x] **Status**: **LOCKED**.

## Phase 11: Product Family & Launch Experience Governance ✅
- [x] **PR35A**: Product Family Stabilization + Launch Experience Governance
  - [x] Create platform naming guidelines (`docs/PRODUCT_FAMILY_GOVERNANCE.md`)
  - [x] Create clean menu standards (`docs/LAUNCH_EXPERIENCE_POLICY.md`)
  - [x] Create three-tier application criteria (`docs/APP_TIER_MODEL.md`)
  - [x] Create flagship freeze registries (`docs/LAUNCH_APP_FREEZE.md`)
  - [x] Create dynamic edition manifests controls (`docs/EDITION_GOVERNANCE.md`)
  - [x] Establish visual vs programmatic boundary mappings (`docs/BRANDING_BOUNDARY_POLICY.md`)
  - [x] Scaffold app identity manifests (`apps/manifests/`)
  - [x] Program automated menu governance validator (`validate-launch-experience.sh`)
- [x] **Status**: **LOCKED**.

## Phase 12: Sovereign Native OS Exclusivity & App Strategy ✅
- [x] **PR35B**: Blue Phoenix Native: Crown Edition App Strategy
  - [x] Create Native Crown Operating System PRD (`docs/BLUE_PHOENIX_NATIVE_CROWN_PRD.md`)
  - [x] Establish Desktop vs Sovereign exclusivity parameters (`docs/NATIVE_APP_EXCLUSIVITY_MODEL.md`)
  - [x] Define package specification, sandboxes, and lifecycle specs (`docs/WORLDKIT_NATIVE_APP_RUNTIME.md`)
  - [x] Design Crown Application Bundle & MVP sets (`docs/NATIVE_CROWN_APP_BUNDLE.md`)
  - [x] Design exclusive native games bundle (`docs/NATIVE_GAME_BUNDLE.md`)
  - [x] Formulate three-layered standard core porting paths (`docs/DESKTOP_TO_NATIVE_PORTING_STRATEGY.md`)
  - [x] Define official Epics, milestones, and issues templates (`docs/NATIVE_GITHUB_MILESTONES_ISSUES.md`)
- [x] **Status**: **LOCKED**.

## Phase 13: Master Seven Paths Product Synthesis & ISO Orchestration ✅
- [x] **PR35C**: Master Seven Paths Product Synthesis
  - [x] Align naming, manifests, taglines, and colors across all seven active editions
  - [x] Stage dynamic assets (logos, colors, package profiles) under custom paths
  - [x] Build master orchestrator script (`scripts/build-all-isos.sh`) for automated sequential ISO generation
  - [x] Perform exhaustive PR35C validation checks (ALL EDITIONS VALIDATED ✅)
- [x] **Status**: **LOCKED**.

## Phase 14: Multi-Boot UEFI USB Creation & Build Optimization ✅
- [x] Create macOS compatible multi-boot USB formatter utility (`scripts/create-multiboot-usb.sh`) with GPT schema and partition mappings.
- [x] Create hyper-fast dynamic ISO bypass build orchestrator (`scripts/build-all-isos-fast.sh`) exploiting SquashFS and xorriso UEFI boot structure.
- [x] Fix default desktop wallpaper hooks to override KDE Breeze theme fallback.
- [x] Stage base templates for Plymouth boot splash and SDDM login themes in chroot includes.
- [x] **Status**: **LOCKED**.
