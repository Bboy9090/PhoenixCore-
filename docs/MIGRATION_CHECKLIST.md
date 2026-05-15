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

## Phase 2: Architecture & Roadmap ⏳
- [ ] Create `docs/ARCWYRE_PLATFORM_ARCHITECTURE.md`.
- [ ] Create `docs/ARCWYRE_OS_DESKTOP_ROADMAP.md`.
- [ ] Update `docs/ARCHITECTURE.md` (Transitional).
- [ ] Align PR28/PR29 reports with ARCWYRE naming.

## Phase 3: Code Audit 🛑
- [ ] Search for "Phoenix" in `apps/`.
- [ ] Search for "Phoenix" in `crates/`.
- [ ] Search for "Phoenix" in `os/`.
- [ ] Search for "Phoenix" in build scripts (`.sh`, `Makefile`).
- [ ] Classify references:
    - Safe to rename (UI labels, comments).
    - Risky (Package IDs, internal module names).

## Phase 4: Implementation 🛑
- [ ] Rename safe UI strings.
- [ ] Update build-time environment variables.
- [ ] Update ISO volume labels and metadata.
- [ ] Update binary names (e.g., `phoenix-cli` -> `arcwyre-cli`).

## Phase 5: Verification 🛑
- [ ] Verify build pass (`cargo build`).
- [ ] Verify UI render.
- [ ] Verify ISO creation pass.
- [ ] Final "Truth-First" audit of naming consistency.
