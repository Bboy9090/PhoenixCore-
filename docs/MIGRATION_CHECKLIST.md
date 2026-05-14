# ARCWYRE Migration Checklist

This checklist tracks the staged transition from Phoenix to ARCWYRE.

## Phase 0: Documentation Pivot 🛠️
- [x] Update `README.md` introduction.
- [x] Create `docs/CHANGE_OF_PLANS_PRD.md`.
- [x] Create `docs/ARCWYRE_REBRAND_MAP.md`.
- [x] Create `docs/BRAND_IDENTITY.md`.
- [ ] Update repository description (Manual step for Admin).
- [ ] Add deprecation notices to legacy `docs/` files.

## Phase 1: Visual Identity ⏳
- [ ] Draft new ARCWYRE logo assets.
- [ ] Update `phoenix-control-center` color tokens in CSS/Tailwind.
- [ ] Replace legacy logo placeholders in frontend components.
- [ ] Remove all mascot-related references.

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
