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

## Phase 3: Core Integration 🛑
- [ ] Port Python recovery logic to Rust Agent.
- [ ] Implement "Sacred Minimal" communication protocol.
- [ ] Standardize Core Crates in `core/shared`.

## Phase 4: Edition Synthesis 🛑
- [ ] Implement Edition Builder scripts.
- [ ] Implement UI Theme-Switcher (Manifest-based).
- [ ] Verify ISO creation for multiple editions.
