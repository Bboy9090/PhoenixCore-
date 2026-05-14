# CHANGE OF PLANS PRD: ARCWYRE OS Pivot

**Status:** Active / Authoritative
**Date:** 2026-05-14
**Subject:** Brand Transition and Platform Direction Pivot

## 1. Executive Summary
This document codifies the strategic pivot from the "Phoenix" public branding to **ARCWYRE OS**. The project architecture remains intact, but the public identity is being restructured to better reflect a recovery-first, machine-repair, and creator-owned computing platform.

## 2. Reason for Change
The name "Phoenix" is overcrowded in the operating system and software landscape, leading to brand confusion and reduced discoverability. **ARCWYRE** (Arc + Wire) is a more distinctive, powerful, and repair-focused brand that aligns with our core mission: "Boot the broken. Rewire the future."

## 3. What Is Not Changing
- **Core Architecture:** The underlying Rust engine, FastAPI orchestration, and React clients remain the foundation.
- **BootForge:** The existing imaging and provisioning engine remains a critical tool inside the ARCWYRE ecosystem.
- **Safety-First Design:** The commitment to non-destructive hardware interaction and "Truth-First" auditing remains unchanged.
- **Dual Track Strategy:** We maintain both the Linux-based Desktop track and the from-scratch Native OS track.

## 4. What Is Changing
- **Public Name:** Phoenix OS is now ARCWYRE OS.
- **Visual Identity:** Transitioning from "fire" motifs to "electric arcs, dark storm, and forged silver" aesthetics.
- **Roadmap Terminology:** Projects are now organized under the ARCWYRE platform.
- **Documentation:** All public-facing documentation will pivot to ARCWYRE immediately.

## 5. New Product Architecture

| Old Name | New Name | Description |
| :--- | :--- | :--- |
| Phoenix OS | **ARCWYRE OS** | The overall platform umbrella. |
| Phoenix OS Desktop | **ARCWYRE OS Desktop** | The Linux-based public shipping edition. |
| Phoenix Native | **ARCWYRE Native** | The from-scratch sovereign OS branch. |
| Phoenix Kernel | **ARCWYRE Kernel** | The custom sovereign kernel. |
| Phoenix Core | **ARCWYRE Core** | The cross-platform management engine. |
| Phoenix Agent | **ARCWYRE Agent** | The hardware-side execution daemon. |
| Phoenix Control Center | **ARCWYRE Control Center** | The primary dashboard and UI. |
| Phoenix Key | **ARCWYRE Key** | The secure, bootable hardware token. |
| Phoenix Forge | **ARCWYRE Forge** | The assembly and build environment. |
| - | **ArcWatch** | New subsystem for diagnostics and audit logging. |
| - | **StormGrid** | New subsystem for package management and app hub. |

## 6. Repository Impact: PhoenixCore-
This repository becomes the **Transitional Platform Repo**. Its focus is:
- ARCWYRE Control Center and UX development.
- ARCWYRE Agent and API orchestration.
- Linux-based ARCWYRE OS Desktop assembly.
- Cross-platform shared libraries (Rust crates).

## 7. Migration Phases

### Phase 0: Documentation Pivot (Immediate)
- Update README.
- Deploy Rebrand Map and Brand Identity docs.
- Add deprecation notices for Phoenix branding.

### Phase 1: Visual Identity Pivot
- Define ARCWYRE brand palette (Electric Cyan, Forged Silver).
- Remove legacy third-party inspired mascot concepts.
- Update UI mockups with "Dark Storm" aesthetic.

### Phase 2: Platform Docs Pivot
- Rename architecture docs.
- Finalize ARCWYRE OS Desktop Roadmap.
- Update system diagrams.

### Phase 3: Code-Level Rename Audit (Staged)
- Search/classify Phoenix references.
- Rename UI text and safe identifiers.
- classification: [DOCS, UI_TEXT, PACKAGE_NAME, IMPORT, INTERNAL_MODULE, BUILD_CRITICAL].

### Phase 4: Build & Safety Verification
- Run full test suite.
- Confirm no broken imports or build-critical failures.

## 8. Risks & Mitigations
- **Broken Imports:** Mitigated by staged renaming; internal modules may retain "Phoenix" codenames in Phase 3.
- **Terminology Confusion:** Mitigated by the authoritative `ARCWYRE_REBRAND_MAP.md`.
- **Scope Creep:** Focusing on documentation and branding first to ensure stability.

## 9. Final Founder Directive
ARCWYRE is the new public identity for a repair-first operating-system platform. We are building the tools to "Boot the broken" and the sovereign foundation to "Rewire the future."
